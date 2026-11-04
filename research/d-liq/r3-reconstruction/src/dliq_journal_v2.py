"""D-LIQ evidence journal v2 -- WRITER and MOCK ANCHOR (spec r3 Appendix A). Python 3 standard library only. DRAFT, not locked.
Supersedes dliq_journal_v1.py (the r2 audit object; kept unchanged). Differences from v1 (response to GPT's audit of the r2 package):
  * genesis string is v2 (a v1 journal can never verify as v2);
  * the SIGNAL record (SLOT) and the OUTCOME record are separate events; an OUTCOME may only be written AFTER a CHECKPOINT that covers the SLOT of the same tau;
  * every SLOT must be anchored before the entry candle opens, with a STRICT inequality on the anchor's own time interval:
        anchor_upper_ms < tau_ms + ENTRY_DELAY_MS,   anchor_upper_ms = time_ms + time_resolution_ms - 1 + time_uncertainty_ms
    (receipts carry time_ms, time_resolution_ms, time_uncertainty_ms; a target that cannot give a bound is not eligible);
  * Journal.slot_and_anchor() writes the SLOT and the CHECKPOINT back to back (the only supported way to record a signal);
  * CANDLE events carry the collector-parsed open_time_ms/open plus raw bytes; OUTCOME carries entry/exit candle times and prices and the r_bps string.

Format  (A.2): one event per line; canonical JSON = ASCII, keys sorted, separators (",",":"), integers only for numbers
               (floats REFUSED), decimals as strings, "\\n" ends every line.
Chain   (A.3): h_0 = SHA-256(GENESIS);  h_n = SHA-256(h_{n-1} || line_n)   (raw 32-byte h; line_n = canonical bytes WITHOUT newline).
Anchor  (A.4): CHECKPOINT(anchored_seq=k, anchored_head=h_k, receipt) is itself a chain event; h_k is sent to the external anchor BEFORE the
               CHECKPOINT event is written. MockAnchor is a local stand-in proving verifier logic, NOT the independence of any real target.
Writer guarantees: single writer (flock), fsync per event, contiguous seq, refuses non-canonical input, refuses to open a damaged journal
(a torn final line needs repair_torn_tail=True, which returns the dropped bytes).
Writer guards for the SLOT/OUTCOME order (append(); the verifier re-checks everything independently of these guards):
  * a SLOT with outcome fields, or a second SLOT for the same tau_ms, is refused;
  * an OUTCOME is refused unless a SLOT with the same tau_ms exists AND a CHECKPOINT written after it anchors it; a second OUTCOME for a tau is refused.
Test hook: append_unchecked() skips these guards so that tests can craft the bad journals the verifier must catch; production code never calls it.
"""
import base64
import fcntl
import hashlib
import json
import os

GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"
ENTRY_DELAY_MS = 300_000            # [P] r3 5.1: the entry candle is the one whose open_time is EXACTLY tau + 5 min (a missing candle is NO_PRICE); also the anchoring deadline
OUTCOME_HORIZON_MS = 14_400_000     # exit candle open_time = entry candle open_time + 4 h
OUTCOME_FORBIDDEN_IN_SLOT = ("entry_open_ms", "exit_open_ms", "entry_price", "exit_price", "r_bps", "outcome")
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
    assert not (set(f) & set(OUTCOME_FORBIDDEN_IN_SLOT)), "outcome fields must never be part of a SLOT"
    return f


def candle_fields(open_time_ms, open_price, recv_ms, raw):
    """collector-parsed values + raw bytes of one live 1-minute candle message (REST backfill is forbidden by r3 5.1)."""
    return {"open_time_ms": open_time_ms, "open": open_price, "recv_ms": recv_ms, "raw_b64": b64(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def outcome_fields(tau_ms, status, entry_open_ms=None, exit_open_ms=None, entry_price=None, exit_price=None, r_bps=None):
    """status EVAL needs entry/exit candle open times (ms), prices (decimal strings) and r_bps (repr string of the float); NO_PRICE carries none."""
    if status == "NO_PRICE":
        return {"tau_ms": tau_ms, "status": "NO_PRICE"}
    return {"tau_ms": tau_ms, "status": "EVAL", "entry_open_ms": entry_open_ms, "exit_open_ms": exit_open_ms,
            "entry_price": entry_price, "exit_price": exit_price, "r_bps": r_bps}


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
        self._slot_seq, self._slot_status, self._anchored_taus, self._outcome_taus = {}, {}, set(), set()
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
                self._track(ev)

    def _track(self, ev):
        """keeps the SLOT/OUTCOME bookkeeping for the guards; called for every event written or recovered."""
        t = ev.get("t")
        if t == "SLOT" and isinstance(ev.get("tau_ms"), int) and ev["tau_ms"] not in self._slot_seq:
            self._slot_seq[ev["tau_ms"]] = ev["seq"]
            self._slot_status[ev["tau_ms"]] = ev.get("status")
        elif t == "OUTCOME" and isinstance(ev.get("tau_ms"), int):
            self._outcome_taus.add(ev["tau_ms"])
        elif t == "CHECKPOINT" and isinstance(ev.get("anchored_seq"), int):
            for tau, sq in self._slot_seq.items():
                if sq <= ev["anchored_seq"] < ev["seq"]:
                    self._anchored_taus.add(tau)

    def append(self, etype, **fields):
        if etype == "SLOT":
            if set(fields) & set(OUTCOME_FORBIDDEN_IN_SLOT):
                raise JournalError("a SLOT must not carry outcome fields")
            if fields.get("tau_ms") in self._slot_seq:
                raise JournalError("a SLOT for tau_ms %r already exists" % (fields.get("tau_ms"),))
        elif etype == "OUTCOME":
            tau = fields.get("tau_ms")
            if tau not in self._slot_seq:
                raise JournalError("OUTCOME without a SLOT for tau_ms %r" % (tau,))
            if self._slot_status.get(tau) != "VALID":
                raise JournalError("OUTCOME refused: SLOT for tau_ms %r is not VALID" % (tau,))
            if tau not in self._anchored_taus:
                raise JournalError("OUTCOME refused: the SLOT of tau_ms %r is not yet anchored by a CHECKPOINT" % (tau,))
            if tau in self._outcome_taus:
                raise JournalError("a second OUTCOME for tau_ms %r" % (tau,))
        return self.append_unchecked(etype, **fields)

    def append_unchecked(self, etype, **fields):
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
        self._track(ev)
        return self.seq

    def checkpoint(self, anchor):
        """Send the CURRENT head to the anchor, then record the receipt as a CHECKPOINT event (which extends the chain)."""
        k, head_hex = self.seq, self.head.hex()
        receipt = anchor.submit(self.journal_id, k, head_hex)
        return self.append("CHECKPOINT", anchored_seq=k, anchored_head=head_hex, receipt=receipt)

    def slot_and_anchor(self, slot_rec, anchor):
        """the only supported way to record a signal: SLOT immediately followed by the CHECKPOINT that anchors it. Returns (slot_seq, checkpoint_seq)."""
        s = self.append("SLOT", **slot_fields(slot_rec))
        return s, self.checkpoint(anchor)

    def close(self):
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)


class MockAnchor:
    """Local stand-in for an external append-only, time-stamping service (e.g. a transparency log / public repository / notary).
    Required interface for any real target:
        submit(journal_id, seq, head_hex) -> receipt dict (ints/strings only) containing at least anchor_id, index, time_ms, head, seq,
                                             time_resolution_ms, time_uncertainty_ms (the anchor's own clock; a target that cannot bound these is ineligible)
        get(journal_id, index)            -> the stored entry or None           (independent lookup)
        latest(journal_id)                -> highest stored index or 0           (used to detect truncation of checkpoints)
    This mock keeps its entries in its OWN file with its own hash chain, so that deleting/editing the journal cannot touch it."""

    def __init__(self, path, clock, anchor_id="MOCK-ANCHOR-1", time_resolution_ms=1, time_uncertainty_ms=0):
        self.path, self.clock, self.anchor_id = path, clock, anchor_id
        self.time_resolution_ms, self.time_uncertainty_ms = time_resolution_ms, time_uncertainty_ms
        open(path, "ab").close()

    def _entries(self):
        return [json.loads(l) for l in open(self.path, "rb").read().split(b"\n") if l]

    def submit(self, journal_id, seq, head_hex):
        es = self._entries()
        idx = 1 + sum(1 for e in es if e["journal_id"] == journal_id)
        prev = es[-1]["entry_hash"] if es else "0" * 64
        e = {"anchor_id": self.anchor_id, "journal_id": journal_id, "index": idx, "seq": seq, "head": head_hex, "time_ms": int(self.clock()),
             "time_resolution_ms": self.time_resolution_ms, "time_uncertainty_ms": self.time_uncertainty_ms}
        e["entry_hash"] = hashlib.sha256((prev + json.dumps(e, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
        with open(self.path, "ab") as f:
            f.write(json.dumps(e, sort_keys=True, separators=(",", ":")).encode() + b"\n")
            f.flush()
            os.fsync(f.fileno())
        return {k: e[k] for k in ("anchor_id", "index", "seq", "head", "time_ms", "time_resolution_ms", "time_uncertainty_ms")}

    def get(self, journal_id, index):
        for e in self._entries():
            if e["journal_id"] == journal_id and e["index"] == index:
                return e
        return None

    def latest(self, journal_id):
        return sum(1 for e in self._entries() if e["journal_id"] == journal_id)
