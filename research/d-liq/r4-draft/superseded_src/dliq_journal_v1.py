"""D-LIQ evidence journal -- WRITER and MOCK ANCHOR (spec r2 Appendix A). Python 3 standard library only. DRAFT, not locked.

Format  (A.2): one event per line; canonical JSON = UTF-8/ASCII, keys sorted, separators (",",":"), integers only for numbers
               (floats are REFUSED, so there is no float-repr ambiguity), decimals travel as strings, "\\n" ends every line.
Chain   (A.3): h_0 = SHA-256(GENESIS);  h_n = SHA-256(h_{n-1} || line_n)   where h are the raw 32 bytes and line_n are the canonical
               bytes of event n WITHOUT the trailing "\\n".  Hashes are derived, not stored in the file.
Events  (A.1): SESSION CONN PING MSG CLOCK CANDLE SLOT OUTCOME CHECKPOINT  (OUTCOME is an addition, see P1-J3 in the audit notes:
               r2 A.1 puts entry/exit candle ids inside SLOT, which would force a signal record to be written after the outcome).
Anchor  (A.4): CHECKPOINT(anchored_seq=k, anchored_head=h_k, receipt) is itself a chain event.  The head h_k is sent to an external
               append-only service BEFORE the CHECKPOINT event is written.  MockAnchor below is a local stand-in with the interface a real
               target must provide; it proves the verifier logic, NOT the independence of any real target (OPEN-14).

Writer guarantees: single writer (flock), fsync per event, contiguous seq, refuses non-canonical input, refuses to open a journal whose
existing content does not parse (no silent repair; a torn final line must be handled explicitly with repair_torn_tail=True, which is
logged by returning the dropped bytes to the caller).
"""
import base64
import fcntl
import hashlib
import json
import os

GENESIS = b"DLIQ-JOURNAL-v1-GENESIS"
EVENT_TYPES = ("SESSION", "CONN", "PING", "MSG", "CLOCK", "CANDLE", "SLOT", "OUTCOME", "CHECKPOINT")


class JournalError(Exception):
    pass


def h0():
    return hashlib.sha256(GENESIS).digest()


def _reject_float(o):
    if isinstance(o, float):
        raise JournalError("float refused in canonical event: %r" % (o,))
    if isinstance(o, dict):
        for k, v in o.items():
            if not isinstance(k, str):
                raise JournalError("non-string key")
            _reject_float(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            _reject_float(v)
    elif not (o is None or isinstance(o, (str, int, bool))):
        raise JournalError("unsupported type %s" % type(o).__name__)


def canonical(ev):
    """canonical bytes of one event (no newline)."""
    _reject_float(ev)
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def chain_step(prev, line):
    return hashlib.sha256(prev + line).digest()


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def msg_fields(conn_id, recv_ms, raw):
    return {"conn_id": conn_id, "recv_ms": recv_ms, "raw_b64": b64(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def slot_fields(rec):
    """build_slot() record -> canonical-safe SLOT fields (floats become repr strings)."""
    f = {k: rec[k] for k in ("tau_ms", "status", "reasons", "primary_conn", "N_total", "N_BUY", "N_SELL", "sumW_BUY", "sumW_SELL",
                             "side", "malformed_voids", "ledger", "n_messages")}
    f["X_sn"] = None if rec["X_sn"] is None else repr(rec["X_sn"])
    return f


class Journal:
    def __init__(self, path, journal_id, clock, repair_torn_tail=False):
        self.path, self.journal_id, self.clock = path, journal_id, clock
        self.dropped_tail = b""
        self._fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self._fd)
            raise JournalError("journal is locked by another writer")
        try:
            self._recover(path, repair_torn_tail)
        except BaseException:
            self.close()            # a failed open must not leave the file locked (found by test_dliq_journal_v1)
            raise

    def _recover(self, path, repair_torn_tail):
        data = open(path, "rb").read()
        self.seq, self.head = 0, h0()
        if data:
            if not data.endswith(b"\n"):
                cut = data.rfind(b"\n") + 1
                if not repair_torn_tail:
                    raise JournalError("torn final line; reopen with repair_torn_tail=True after inspecting it")
                self.dropped_tail = data[cut:]
                os.ftruncate(self._fd, cut)
                data = data[:cut]
            for i, line in enumerate(data.split(b"\n")[:-1], 1):
                try:
                    ev = json.loads(line)
                except Exception:
                    raise JournalError("line %d is not JSON; refusing to append to a damaged journal" % i)
                if canonical(ev) != line or ev.get("seq") != i:
                    raise JournalError("line %d is not canonical / not sequential; refusing to append" % i)
                self.head = chain_step(self.head, line)
                self.seq = i

    def append(self, etype, **fields):
        if etype not in EVENT_TYPES:
            raise JournalError("unknown event type " + etype)
        if "seq" in fields or "t" in fields or "rec_ms" in fields:
            raise JournalError("reserved field name")
        ev = dict(fields)
        ev.update({"t": etype, "seq": self.seq + 1, "rec_ms": int(self.clock())})
        line = canonical(ev)
        os.write(self._fd, line + b"\n")
        os.fsync(self._fd)
        self.seq += 1
        self.head = chain_step(self.head, line)
        return self.seq

    def checkpoint(self, anchor):
        """Send the CURRENT head to the anchor, then record the receipt as a CHECKPOINT event (which extends the chain)."""
        k, head_hex = self.seq, self.head.hex()
        receipt = anchor.submit(self.journal_id, k, head_hex)
        return self.append("CHECKPOINT", anchored_seq=k, anchored_head=head_hex, receipt=receipt)

    def close(self):
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)


class MockAnchor:
    """Local stand-in for an external append-only, time-stamping service (e.g. a transparency log / public repository / notary).
    Required interface for any real target:
        submit(journal_id, seq, head_hex) -> receipt dict (ints/strings only) containing at least anchor_id, index, time_ms, head, seq
        get(journal_id, index)            -> the stored entry or None           (independent lookup)
        latest(journal_id)                -> highest stored index or 0           (used to detect truncation of checkpoints)
    This mock keeps its entries in its OWN file with its own hash chain, so that deleting/editing the journal cannot touch it."""

    def __init__(self, path, clock, anchor_id="MOCK-ANCHOR-1"):
        self.path, self.clock, self.anchor_id = path, clock, anchor_id
        open(path, "ab").close()

    def _entries(self):
        return [json.loads(l) for l in open(self.path, "rb").read().split(b"\n") if l]

    def submit(self, journal_id, seq, head_hex):
        es = self._entries()
        idx = 1 + sum(1 for e in es if e["journal_id"] == journal_id)
        prev = es[-1]["entry_hash"] if es else "0" * 64
        e = {"anchor_id": self.anchor_id, "journal_id": journal_id, "index": idx, "seq": seq, "head": head_hex, "time_ms": int(self.clock())}
        e["entry_hash"] = hashlib.sha256((prev + json.dumps(e, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
        with open(self.path, "ab") as f:
            f.write(json.dumps(e, sort_keys=True, separators=(",", ":")).encode() + b"\n")
            f.flush()
            os.fsync(f.fileno())
        return {k: e[k] for k in ("anchor_id", "index", "seq", "head", "time_ms")}

    def get(self, journal_id, index):
        for e in self._entries():
            if e["journal_id"] == journal_id and e["index"] == index:
                return e
        return None

    def latest(self, journal_id):
        return sum(1 for e in self._entries() if e["journal_id"] == journal_id)
