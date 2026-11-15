#!/usr/bin/env python3
"""Generator of the r6 conformance vectors (journal contract v3, revision r6-draft; contract section 10, cases 1-27).

  python3 -I -B make_vectors.py            # (re)write vectors/<id>/journal.jsonl and vectors/<id>/expect.json
  python3 -I -B make_vectors.py --check    # regenerate in memory and compare with the committed files (no write)

WHAT THIS IS. Every vector is a small journal (canonical JSON lines, hash-chained from the v3 genesis only where a checkpoint needs a chain) and an
expectation written BY HAND in this file: the findings, their `where` (the physical line numbers come from the tags of the construction, not from any
checker) and the SLOT fields (derived from the counts of the construction: 5 BUY messages of weight 60000 each, so sumW_BUY = 60000 * N). The expectation is
then compared with (1) the oracle oracle_r6.py for the rules that are NEW in r6 and (2) the existing r5 verifier for everything else (check_vectors.py).
All three are by the same author as the contract text. This is NOT independent evidence; it is a set of inputs and expected outputs that an independent
implementation can be run against.

Layout of the journals: one connection per slot, opened 1_000_000 ms before tau, a PING every 200_000 ms from tau-800_000 to tau (so the connection is
healthy over V(tau) = [tau-960_000, tau+10_000] and is the smallest healthy id of its slot), five BUY messages (E = tau-700_000+100_000*i, recv_ms = E+1000)
and the SLOT written at rec_ms = tau+10_000. verify_time_ms is tau_1+10_000 for every vector, so every SLOT is PENDING (no checkpoint, no deadline finding).
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "vectors"
GRID = 14_400_000
TAU0 = GRID * 124_000                      # 1_785_600_000_000, on the 4 h grid
V3 = b"DLIQ-JOURNAL-v3-GENESIS"
V2 = b"DLIQ-JOURNAL-v2-GENESIS"
LEDGER_KEYS = ("MALFORMED", "NO_PRIMARY", "NON_PRIMARY", "OUT_OF_WINDOW", "LATE", "INELIGIBLE", "COUNTED")
ABSENT = object()

# contract 8.1 (hand copy; the checker has its own copy)
HARD = {"BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP", "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER",
        "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
        "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE",
        "SLOT_MISMATCH", "SLOT_EARLY_WRITE", "REPLAY_NOT_RUN", "CONN_FEED_CONFLICT", "MSG_CONN_UNKNOWN", "FORCE_MSG_STRUCTURE", "CANDLE_LINK",
        "CANDLE_PARSE", "CANDLE_FIELD_MISMATCH", "CANDLE_LAG_UNSET"}
SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED", "FORCE_UNKNOWN_KEY"}
R6_NAMES = {"CONN_FEED_CONFLICT", "MSG_CONN_UNKNOWN", "FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY", "CANDLE_LAG_UNSET"}


def canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def raw_json(obj):
    return json.dumps(obj, separators=(",", ":")).encode("ascii")


def chain(genesis, lines):
    heads = [hashlib.sha256(genesis).digest()]
    for line in lines:
        heads.append(hashlib.sha256(heads[-1] + line).digest())
    return heads


def frame(E, *, s="BTCUSDT", ps="BTCUSDT", st=1, top=None, o_extra=None):
    """An unwrapped forceOrder frame (compact JSON, exchange key order). ps / st may be ABSENT; `top` adds top-level keys; `o_extra` adds keys inside `o`."""
    o = {} if s is ABSENT else {"s": s}
    o.update({"S": "BUY", "o": "LIMIT", "f": "IOC", "q": "1", "p": "60000", "ap": "60000", "X": "FILLED", "l": "1", "z": "1", "T": E - 1000})
    if ps is not ABSENT:
        o["ps"] = ps
    if st is not ABSENT:
        o["st"] = st
    if o_extra:
        o.update(o_extra)
    m = {"e": "forceOrder", "E": E}
    if top:
        m.update(top)
    m["o"] = o
    return raw_json(m)


def kline_frame(E, t0):
    return raw_json({"e": "kline", "E": E, "s": "BTCUSDT", "k": {"t": t0, "T": t0 + 59_999, "s": "BTCUSDT", "i": "1m", "o": "60000", "x": False}})


def msg_ev(conn, recv, raw):
    return {"t": "MSG", "rec_ms": recv, "conn_id": conn, "recv_ms": recv, "raw_b64": base64.b64encode(raw).decode("ascii"), "sha256": hashlib.sha256(raw).hexdigest()}


_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def raw_ev(conn, recv, text, intended):
    """A MSG event whose raw_b64 TEXT is given exactly as written (it may be UNDECODABLE under contract 2.2). `sha256` is the hash of the bytes the text was meant to carry
    (for a non-canonical text: of its permissive decoding, which gives the same bytes), so that a decoder that is more permissive than 2.2 finds a matching hash."""
    return {"t": "MSG", "rec_ms": recv, "conn_id": conn, "recv_ms": recv, "raw_b64": text, "sha256": hashlib.sha256(intended).hexdigest()}


def bad_char(raw, at=8):
    """An invalid alphabet character inside the text ('!'); a permissive decoder drops it and gets the intended bytes."""
    t = b64(raw)
    return t[:at] + "!" + t[at:]


def trailing_newline(raw):
    return b64(raw) + "\n"


def embedded_space(raw, at=12):
    t = b64(raw)
    return t[:at] + " " + t[at:]


def stripped_padding(raw):
    t = b64(raw)
    assert t.endswith("=")
    return t.rstrip("=")


def extra_padding(raw):
    """One '=' too many; a permissive decoder ignores it."""
    return b64(raw) + "="


def truncated(raw):
    return b64(raw)[:-3]


def non_canonical(raw, bit):
    """The same bytes, but the last data character carries a NON-ZERO trailing bit (`bit`: one of the spare bits of that character; the canonical text has zeros there). The frame length must
    leave spare bits (padding '=': two spare bits, 0x01 and 0x02; padding '==': four, 0x01 to 0x08). `validate=True` alone accepts the result."""
    t = b64(raw)
    pad = len(t) - len(t.rstrip("="))
    assert pad in (1, 2), "the frame length leaves no spare bits"
    assert bit in ((1, 2) if pad == 1 else (1, 2, 4, 8))
    i = len(t) - pad - 1
    c = _ALPHA.index(t[i])
    assert c & (3 if pad == 1 else 15) == 0, "the canonical text has zero trailing bits"
    out = t[:i] + _ALPHA[c | bit] + t[i + 1:]
    assert base64.b64decode(out, validate=True) == raw and out != t
    return out


def conn_ev(conn, ev, ms, feed="FORCE"):
    e = {"t": "CONN", "rec_ms": ms, "conn_id": conn, "ev": ev, "ms": ms}
    if feed is not ABSENT:
        e["feed"] = feed
    return e


def ping_ev(conn, ms):
    return {"t": "PING", "rec_ms": ms, "conn_id": conn, "ms": ms}


def slot_ev(tau, *, primary, ledger, status="VALID", reasons=(), voids=0):
    """Hand-derived SLOT event. All messages weigh 60000 (z=1, ap=60000) and are BUY, so N_BUY = N_total = ledger COUNTED, sumW_BUY = 60000 * N_BUY,
    sumW_SELL = "0", X_sn = "1.0" (exact decimal 1, repr of the float) when N_total > 0; side = 1 when VALID else 0; n_messages = sum of the ledger."""
    led = {k: 0 for k in LEDGER_KEYS}
    led.update(ledger)
    n = led["COUNTED"]
    return {"t": "SLOT", "rec_ms": tau + 10_000, "tau_ms": tau, "status": status, "reasons": list(reasons), "primary_conn": primary, "N_total": n,
            "N_BUY": n, "N_SELL": 0, "side": 1 if status == "VALID" else 0, "malformed_voids": voids, "n_messages": sum(led.values()),
            "sumW_BUY": str(60000 * n), "sumW_SELL": "0", "X_sn": "1.0" if n > 0 else None, "ledger": led}


class J:
    """A journal under construction. `tag` maps a name to the 1-based physical line of an event (used for the hand-written `where`)."""

    def __init__(self):
        self.events, self.tag, self.taus = [], {}, []

    def add(self, ev, tag=None, seq_off=0):
        ev = dict(ev)
        ev["seq"] = len(self.events) + 1 + seq_off
        self.events.append(ev)
        if tag:
            assert tag not in self.tag, tag
            self.tag[tag] = len(self.events)
        return len(self.events)

    def slot(self, tau, tag=None, **kw):
        self.taus.append(tau)
        return self.add(slot_ev(tau, **kw), tag=tag)

    def lines(self):
        return [canon(e) for e in self.events]

    def data(self):
        return b"".join(l + b"\n" for l in self.lines())


def block(j, tau, conn, *, plain=False, extras=(), quiet=(), feed="FORCE", n_normal=5):
    """The events that precede the SLOT of `tau`: the open, the pings, the five normal messages of connection `conn`, plus `extras` (dicts with conn, E, raw, tag,
    optional recv and seq_off) and `quiet` connections ((conn_id, ms before tau at which it opens), no frames of their own). Sorted by time."""
    evs = [(tau - 1_000_000, 0, conn_ev(conn, "open", tau - 1_000_000, feed), "open%d" % conn, 0)]
    for dt in (800_000, 600_000, 400_000, 200_000, 0):
        evs.append((tau - dt, 1, ping_ev(conn, tau - dt), None, 0))
    for i in range(n_normal):
        E = tau - 700_000 + 100_000 * i
        evs.append((E + 1000, 2, msg_ev(conn, E + 1000, frame(E, ps=ABSENT, st=ABSENT) if plain else frame(E)), None, 0))
    for c, before in quiet:
        evs.append((tau - before, 0, conn_ev(c, "open", tau - before), "open%d" % c, 0))
    for x in extras:
        recv = x["recv"] if "recv" in x else x["E"] + 1000
        evs.append((recv, 2, x["ev"] if "ev" in x else msg_ev(x["conn"], recv, x["raw"]), x.get("tag"), x.get("seq_off", 0)))
    for _, _, ev, tag, off in sorted(evs, key=lambda e: (e[0], e[1])):
        j.add(ev, tag=tag, seq_off=off)


def F(name, where, detail=None):
    return [name, where, detail]


def finish(vid, slug, title, cases, refs, desc, j, findings, *, checkpoint=False, anchor=(), extra_r6_only=(), r5_only_extra=(), verify_time_ms=None, outcomes=None):
    base = [F("CANDLE_LAG_UNSET", 0)] + ([] if checkpoint else [F("NO_CHECKPOINT", 0)])
    allf = sorted(base + list(findings), key=lambda f: (f[1], f[0]))
    hard = sorted({f[0] for f in allf if f[0] in HARD})
    soft = sorted({f[0] for f in allf if f[0] in SOFT})
    verdict = "FAIL" if any(h not in ("REPLAY_NOT_RUN", "CANDLE_LAG_UNSET") for h in hard) else "INCOMPLETE"       # contract 8.2; CANDLE_LAG_UNSET is always present
    r6_only = sorted([f[0], f[1]] for f in allf if f[0] in R6_NAMES) + [list(x) for x in extra_r6_only]
    vt = TAU0 + 10_000 if verify_time_ms is None else verify_time_ms
    expect = {"id": vid, "title": title, "cases": sorted(cases), "contract_refs": list(refs), "description": desc, "journal_id": "vec-" + vid,
              "verify_time_ms": vt, "anchor": list(anchor), "findings": allf, "r6_only": sorted(r6_only), "r5_only_extra": [list(x) for x in r5_only_extra],
              "verdict": verdict, "hard": hard, "soft": soft, "replayed": True, "analysis_eligible": False,
              "slots": {str(t): "OK" if checkpoint else "PENDING" for t in j.taus}, "missing": [], "candles": {}}
    # report keys that do not depend on the findings (contract 8.2): n_events = number of parsed lines, head_hex = h_N under the v3 genesis (3.2), outcomes = {tau_ms: COVERED | UNCOVERED}
    # (6.4), written by hand per vector (empty when the journal has no OUTCOME). They are stored apart from expect.json, in vectors/EXPECT_DERIVED.json (see write_all).
    derived = {"n_events": len(j.events), "head_hex": chain(V3, j.lines())[-1].hex(), "outcomes": dict(outcomes or {})}
    return {"dir": "%s_%s" % (vid, slug), "journal": j.data(), "expect": expect, "derived": derived}


def add_checkpoint(j, k, time_ms, index, tag):
    """Append a CHECKPOINT for the first k lines of `j`, chained from the v3 genesis, with the matching anchor entry (returned as the first value; the second is the line)."""
    hx = chain(V3, j.lines())[k].hex()
    rc = {"anchor_id": "vec-anchor", "index": index, "seq": k, "head": hx, "time_ms": time_ms, "time_resolution_ms": 1000, "time_uncertainty_ms": 500}
    line = j.add({"t": "CHECKPOINT", "rec_ms": time_ms, "anchored_seq": k, "anchored_head": hx, "receipt": rc}, tag=tag)
    return rc, line


# ---------------------------------------------------------------------------------------------------------------------------------------------------------
def anomaly(reason, E, conn=1, tag="anom"):
    """One structurally anomalous forceOrder message of the given 7.5a reason (and nothing else wrong with it)."""
    kw = {"st_top_level": dict(top={"st": 2}), "ps_type": dict(ps=1), "ps_no_s": dict(s=ABSENT, ps="BTCUSDT"), "ps_ne_s": dict(ps="ETHUSDT"), "st_type": dict(st="1"), "st_ne_1": dict(st=2)}[reason]
    return {"conn": conn, "E": E, "raw": frame(E, **kw), "tag": tag}


def build():
    vs = []
    t1 = TAU0
    t2 = TAU0 + GRID
    t3 = TAU0 + 2 * GRID

    def one_slot_anomaly(vid, slug, reason, cases, refs):
        j = J()
        block(j, t1, 1, extras=[anomaly(reason, t1 - 350_000)])
        j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
        return finish(vid, slug, "one %s message inside the window of the only SLOT" % reason, cases, refs,
                      "A forceOrder message with exactly one anomaly (%s), recorded before the SLOT, on the primary FORCE connection. It is MALFORMED for the replay "
                      "(slot NONE, reason MALFORMED, one void) and gets ONE hard FORCE_MSG_STRUCTURE with the physical line number." % reason,
                      j, [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=%s" % reason)])

    # V01 control: all messages carry the valid optional fields ps and st like the one real frame (case 10, last part)
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    vs.append(finish("V01", "control", "control: five valid messages with o.ps == o.s and o.st == 1", [10, 13], ["2.3", "7.5a", "7.7", "8.2"],
                     "One FORCE connection, five valid BUY messages (each carrying o.ps equal to o.s and o.st equal to 1, like the one real frame), one VALID slot. "
                     "No FORCE finding. CANDLE_LAG_UNSET is present, so the verdict is INCOMPLETE and never PASS.", j, []))

    # case 1 and 9: each of the five reasons, before the SLOT, inside its window
    for letter, reason in zip("abcdef", ("st_top_level", "ps_type", "ps_ne_s", "st_type", "st_ne_1", "ps_no_s")):
        vs.append(one_slot_anomaly("V02" + letter, reason, reason, [1, 9] + ([20] if reason == "ps_no_s" else []), ["7.5a", "7.5d", "7.7b", "7.7e"]))

    # GPT 2026-11-12 (condition of his answer to Q1): an o.s that is not a string differs from o.ps. o.ps = "5" and o.s = 5 would be EQUAL if the two were compared as strings.
    j = J()
    block(j, t1, 1, extras=[{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, s=5, ps="5"), "tag": "anom"}])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V02g", "ps_ne_s_nonstring_s", "one ps_ne_s message whose o.s is not a string", [1, 9], ["7.5a", "7.5d", "7.7b", "7.7e"],
                     "A forceOrder message with o.ps = \"5\" (a string) and o.s = 5 (a number): `o` has a key s, so the reason is ps_ne_s, not ps_no_s, and an o.s that is not a string differs (7.5a). "
                     "Compared as strings the two would be equal, so a reading that coerces o.s to a string reports nothing. The message is also MALFORMED in the replay (symbol): slot NONE, one void; "
                     "ONE hard FORCE_MSG_STRUCTURE with the physical line number.", j, [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=ps_ne_s")]))

    # case 2: between two slots
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    block(j, t2, 2, extras=[{"conn": 2, "E": t2 - 350_000, "raw": frame(t2 - 350_000, st=None), "tag": "anom"}])
    j.slot(t2, primary=2, ledger={"MALFORMED": 1, "NON_PRIMARY": 5, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V03", "between_slots", "an anomalous message recorded between two SLOTs", [2], ["7.5d", "7.7d"],
                     "Slot 1 is clean and VALID. The anomalous message (o.st is JSON null: st_type) is recorded after slot 1 and before slot 2, on connection 2. "
                     "Slot 1 is not affected (its replay only sees earlier lines). Slot 2 is NONE (MALFORMED, one void); the five messages of connection 1 are NON_PRIMARY in its ledger. "
                     "One FORCE_MSG_STRUCTURE.", j, [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=2 reason=st_type")]))

    # case 3: after the last SLOT, and in a journal without a SLOT
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    j.add(msg_ev(1, t1 + 20_000, anomaly("ps_ne_s", t1 + 19_000)["raw"]), tag="anom")
    vs.append(finish("V04a", "after_last_slot", "an anomalous message after the last SLOT", [3], ["7.7d", "7.7e"],
                     "The message is recorded after the only SLOT: no replay contains it, the slot stays VALID, no slot is created for it, and the run-level pass still reports "
                     "exactly one FORCE_MSG_STRUCTURE (ps_ne_s). Verdict FAIL.", j, [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=ps_ne_s")]))
    j = J()
    j.add(conn_ev(1, "open", t1 - 1_000_000), tag="open1")
    j.add(ping_ev(1, t1 - 800_000))
    j.add(msg_ev(1, t1 - 699_000, frame(t1 - 700_000)))
    j.add(msg_ev(1, t1 - 599_000, anomaly("ps_type", t1 - 600_000)["raw"]), tag="anom")
    j.add(msg_ev(1, t1 - 499_000, frame(t1 - 500_000)))
    vs.append(finish("V04b", "no_slot", "an anomalous message in a journal without any SLOT", [3], ["7.7a", "7.7d"],
                     "No SLOT event at all: the replay is vacuous (replayed true, nothing compared) but the run-level pass still reports exactly one FORCE_MSG_STRUCTURE. "
                     "Verdict FAIL, `slots` empty.", j, [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=ps_type")]))

    # case 4: non-primary FORCE connection
    j = J()
    block(j, t1, 1, extras=[anomaly("st_ne_1", t1 - 350_000, conn=2)], quiet=[(2, 1_000_000)])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V05a", "nonprimary_in_window", "an anomalous message on a non-primary FORCE connection, inside V(tau)", [4], ["7.5b", "7.5d", "7.7b"],
                     "Connection 2 is a FORCE connection that is not healthy (no frames of its own), so connection 1 is primary. The anomalous message of connection 2 is MALFORMED "
                     "before the primary-connection label applies, and it lies in V(tau): slot NONE (MALFORMED, one void). One FORCE_MSG_STRUCTURE with conn_id=2.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=2 reason=st_ne_1")]))
    far = t1 - 5_000_000
    j = J()
    block(j, t1, 1, extras=[{"conn": 2, "E": far, "raw": frame(far, st=2), "tag": "anom"}], quiet=[(2, 6_000_000)])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5})
    vs.append(finish("V05b", "nonprimary_outside_V", "an anomalous message on a non-primary connection, outside V(tau)", [4], ["7.5d", "7.7b", "7.7e"],
                     "Same as V05a, but the message (E and recv_ms) lies far before V(tau): it is counted in the ledger as MALFORMED but voids nothing, so the SLOT is VALID. "
                     "The run-level finding is present all the same and the verdict is FAIL: a VALID slot in a failed journal.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=2 reason=st_ne_1")]))

    # case 5 and 18, and the last part of case 11: KLINE connection with a SMALLER id
    j = J()
    j.add(conn_ev(0, "open", t1 - 1_000_000, "KLINE"), tag="open0")
    for dt in (800_000, 600_000, 400_000, 200_000, 0):
        j.add(ping_ev(0, t1 - dt))
    for i in range(16):
        E = t1 - 800_000 + 50_000 * i
        j.add(msg_ev(0, E + 500, kline_frame(E, t1 - 900_000 + 60_000 * (i // 2 + 1))))
    j.add(msg_ev(0, t1 - 100_000, b"this is not json"), tag="kline_garbage")
    j.add(msg_ev(0, t1 - 90_000, frame(t1 - 91_000, top={"st": 1}, ps=1)), tag="kline_anom")
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    vs.append(finish("V06", "kline_smaller_id", "a KLINE connection with a smaller id, sixteen kline frames, a garbage frame and an anomalous frame", [5, 11, 18], ["2.3d", "7.2", "7.5b", "7.5c", "7.5d", "7.7a"],
                     "Connection 0 is a KLINE connection with the smallest id and its own pings (it WOULD be the primary connection if its events were replay inputs: the failure of the G-1 "
                     "demo_topology_conflict). It carries sixteen kline frames (MALFORMED as forceOrder frames), a frame that is not JSON, and a frame with a top-level st and o.ps = 1. "
                     "None of it is a replay input: the SLOT is identical to the SLOT of V01 (primary 1, ledger COUNTED 5, n_messages 5, no void) and there is no FORCE finding.", j, []))

    # case 6: several unknown keys in one message
    j = J()
    ex = {"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, top={"extra1": 5, "aa": "x", "ps": "BTCUSDT"}, o_extra={"zz": 1}), "tag": "unk"}
    block(j, t1, 1, extras=[ex])
    j.slot(t1, primary=1, ledger={"COUNTED": 6})
    vs.append(finish("V07", "unknown_keys", "one message with several unknown keys", [6], ["7.5a", "7.7c"],
                     "One valid message with top-level keys extra1, aa and ps (a top-level ps is an unknown key) and o.zz. ONE soft FORCE_UNKNOWN_KEY with one entry per occurrence, "
                     "the key inside o written o.zz, sorted by code point: aa,extra1,o.zz,ps; no hard finding from 7.7, no void, the slot counts the message (N_total 6). Verdict INCOMPLETE only because of CANDLE_LAG_UNSET.",
                     j, [F("FORCE_UNKNOWN_KEY", j.tag["unk"], "conn_id=1 keys=aa,extra1,o.zz,ps")]))

    # case 7: boolean st and numeric ps
    j = J()
    block(j, t1, 1, extras=[{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, st=True), "tag": "bool"},
                            {"conn": 1, "E": t1 - 340_000, "raw": frame(t1 - 340_000, ps=1), "tag": "num"}])
    j.slot(t1, primary=1, ledger={"MALFORMED": 2, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=2)
    vs.append(finish("V08", "bool_and_number", "o.st = true and o.ps = 1", [7], ["7.5a"],
                     "A boolean is not the integer 1 (st_type) and a number is not a string (ps_type): two messages, two findings, two voids.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["bool"], "conn_id=1 reason=st_type"), F("FORCE_MSG_STRUCTURE", j.tag["num"], "conn_id=1 reason=ps_type")]))

    # case 8 and 9: many slots replay the same anomalous message
    j = J()
    block(j, t1, 1, extras=[anomaly("st_top_level", t1 - 350_000, conn=1)])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    block(j, t2, 2)
    j.slot(t2, primary=2, ledger={"MALFORMED": 1, "NON_PRIMARY": 5, "COUNTED": 5})
    block(j, t3, 3)
    j.slot(t3, primary=3, ledger={"MALFORMED": 1, "NON_PRIMARY": 10, "COUNTED": 5})
    vs.append(finish("V09", "many_slots", "one anomalous message replayed by three SLOTs", [8, 9], ["7.5d", "7.7d", "7.7e"],
                     "The anomalous message lies in the window of slot 1 (NONE, MALFORMED). Slots 2 and 3 replay it again (ledger MALFORMED 1, void 0 because it is outside their V) "
                     "and are VALID; later healthy messages do not clear the finding. ONE FORCE_MSG_STRUCTURE.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=st_top_level")]))

    # case 10
    j = J()
    block(j, t1, 1, extras=[{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, top={"ps": "BTCUSDT"}), "tag": "tps"}])
    j.slot(t1, primary=1, ledger={"COUNTED": 6})
    vs.append(finish("V10a", "top_level_ps", "a top-level ps (no st): soft finding only", [10], ["7.5a", "7.7c"],
                     "A top-level ps is an unknown key: one soft FORCE_UNKNOWN_KEY (keys=ps); the message is not MALFORMED and the slot counts it.", j,
                     [F("FORCE_UNKNOWN_KEY", j.tag["tps"], "conn_id=1 keys=ps")]))
    j = J()
    block(j, t1, 1, extras=[{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, top={"st": 1}), "tag": "tst"}])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V10b", "top_level_st_1", "a top-level st = 1: hard, reason st_top_level", [10], ["7.5a", "7.7b"],
                     "A top-level st is forbidden whatever its value (the r5 rule accepted st = 1; r6 does not): MALFORMED in the replay and one hard FORCE_MSG_STRUCTURE.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["tst"], "conn_id=1 reason=st_top_level")]))
    j = J()
    block(j, t1, 1, plain=True)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    vs.append(finish("V10c", "ps_st_absent", "o.ps and o.st absent: no finding", [10], ["7.5a"],
                     "No message carries o.ps or o.st: both are optional, their absence is not an error. No FORCE finding.", j, []))

    # case 11: feed
    for letter, slug, feed, title in (("a", "feed_missing", ABSENT, "a CONN event without feed"), ("b", "feed_other", "OTHER", "a CONN event with feed OTHER"),
                                      ("c", "feed_lowercase", "force", "a CONN event with feed force (case matters)")):
        j = J()
        j.add(conn_ev(1, "open", t1 - 1_000_000, feed), tag="bad")
        j.add(ping_ev(1, t1 - 800_000))
        j.add(msg_ev(1, t1 - 699_000, frame(t1 - 700_000)), tag="msg")
        vs.append(finish("V12" + letter, slug, title + " is BAD_EVENT", [11], ["2.1", "2.3a", "2.3c"],
                         "The only `open` event of connection 1 is BAD_EVENT (feed missing or not FORCE / KLINE), so the connection has no valid open event and its message is "
                         "MSG_CONN_UNKNOWN. No SLOT in this journal (r5 would treat the CONN event as valid, so the replay of r5 and r6 differ by design here).", j,
                         [F("BAD_EVENT", j.tag["bad"]), F("MSG_CONN_UNKNOWN", j.tag["msg"])], extra_r6_only=[("BAD_EVENT", j.tag["bad"])]))
    j = J()
    j.add(conn_ev(1, "open", t1 - 1_000_000, "FORCE"))
    j.add(conn_ev(2, "open", t1 - 1_000_000, "KLINE"))
    j.add(msg_ev(1, t1 - 699_000, frame(t1 - 700_000)))
    j.add(conn_ev(1, "close", t1 - 500_000, "KLINE"), tag="c1")
    j.add(conn_ev(2, "open", t1 - 400_000, "FORCE"), tag="c2")
    j.add(conn_ev(1, "close", t1 - 300_000, "OTHER"), tag="bad")
    vs.append(finish("V12d", "feed_conflict", "a later CONN event names another feed", [11], ["2.1", "2.3a", "2.3b"],
                     "Connection 1 opens as FORCE (its feed) and is later closed with feed KLINE; connection 2 opens as KLINE and is reopened with feed FORCE. One CONN_FEED_CONFLICT per "
                     "conflicting event, where = the CONN line. A last CONN event with feed OTHER is BAD_EVENT and, being invalid, is excluded from the conflict rule (no CONN_FEED_CONFLICT for it).",
                     j, [F("CONN_FEED_CONFLICT", j.tag["c1"]), F("CONN_FEED_CONFLICT", j.tag["c2"]), F("BAD_EVENT", j.tag["bad"])], extra_r6_only=[("BAD_EVENT", j.tag["bad"])]))
    # case 16
    j = J()
    j.add(msg_ev(1, t1 - 900_000, frame(t1 - 901_000)), tag="early")
    j.add(conn_ev(1, "open", t1 - 800_000, "FORCE"))
    j.add(msg_ev(1, t1 - 699_000, frame(t1 - 700_000)))
    j.add(msg_ev(9, t1 - 698_000, anomaly("ps_type", t1 - 699_000, conn=9)["raw"]), tag="never")
    vs.append(finish("V12e", "msg_before_open", "a MSG recorded before the first valid open, and a MSG of a connection that never opens", [11, 16], ["2.3c", "7.7a"],
                     "Line 1 is a MSG of connection 1 recorded BEFORE connection 1 opens (line 2): MSG_CONN_UNKNOWN, although the connection is opened later. The MSG on line 3 is fine. "
                     "The MSG of connection 9 (never opened, so it has no feed) is MSG_CONN_UNKNOWN too, and, being treated as a FORCE message (2.3c, the conservative reading), "
                     "its ps_type anomaly is also reported by 7.7.", j,
                     [F("MSG_CONN_UNKNOWN", j.tag["early"]), F("MSG_CONN_UNKNOWN", j.tag["never"]), F("FORCE_MSG_STRUCTURE", j.tag["never"], "conn_id=9 reason=ps_type")]))

    # case 19: the same unknown name at both levels
    j = J()
    ex = {"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, top={"zz": 1, "o.zz": 3}, o_extra={"zz": 2}), "tag": "both"}
    block(j, t1, 1, extras=[ex])
    j.slot(t1, primary=1, ledger={"COUNTED": 6})
    vs.append(finish("V23", "unknown_both_levels", "the same unknown key name at both levels", [19], ["7.5a", "7.7c"],
                     "Top-level zz, o.zz and a top-level key that is literally named o.zz: ONE soft FORCE_UNKNOWN_KEY with three entries, o.zz,o.zz,zz (one entry per occurrence, location-qualified, "
                     "no de-duplication even when two written entries coincide, sorted by code point of the written string). The message is valid and counted.", j, [F("FORCE_UNKNOWN_KEY", j.tag["both"], "conn_id=1 keys=o.zz,o.zz,zz")]))

    # case 22: o is not an object
    j = J()
    e1, e2, e3 = t1 - 350_000, t1 - 340_000, t1 - 330_000
    r1 = b'{"e":"forceOrder","E":%d,"o":"not an object"}' % e1
    r2 = b'{"e":"forceOrder","E":%d,"st":1,"o":null}' % e2
    r3 = b'{"e":"forceOrder","E":%d,"o":5}' % e3
    block(j, t1, 1, extras=[{"conn": 1, "E": e1, "raw": r1, "tag": "str"}, {"conn": 1, "E": e2, "raw": r2, "tag": "null"}, {"conn": 1, "E": e3, "raw": r3, "tag": "num"}])
    j.slot(t1, primary=1, ledger={"MALFORMED": 3, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=3)
    vs.append(finish("V21", "o_not_object", "o is not an object", [22], ["7.5a", "7.7b"],
                     "m1: o is a string, m2: o is null and the top level has st = 1, m3: o is the number 5. All three are MALFORMED in the replay (three voids). m1 and m3 get NO FORCE finding (no ps/st "
                     "reason looks inside a non-object o); m2 still gets st_top_level, which looks at the top-level object only.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["null"], "conn_id=1 reason=st_top_level")]))

    # case 21: the feed applies from the first valid open on
    far = t1 - 2_000_000
    j = J()
    j.add(conn_ev(0, "close", far - 1000, "FORCE"), tag="preclose")
    j.add(msg_ev(0, far + 1000, anomaly("ps_type", far, conn=0)["raw"]), tag="pre")
    j.add(conn_ev(0, "open", t1 - 1_000_000, "KLINE"), tag="open0")
    for dt in (800_000, 600_000, 400_000, 200_000, 0):
        j.add(ping_ev(0, t1 - dt))
    for i in range(3):
        E = t1 - 700_000 + 100_000 * i
        j.add(msg_ev(0, E + 500, kline_frame(E, t1 - 900_000)))
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5})
    vs.append(finish("V12f", "feed_from_first_open", "a MSG recorded before the first open of a connection that later opens as KLINE", [11, 21], ["2.3a", "2.3c", "7.2", "7.7a"],
                     "Line 1 is a CONN close of connection 0 naming feed FORCE, recorded before its first valid open (no feed yet, so no CONN_FEED_CONFLICT). Line 2 is a MSG (ps_type anomaly, far outside V(tau)) of "
                     "connection 0, recorded BEFORE connection 0 opens as KLINE (line 3). The feed applies from the first valid open on, so the message "
                     "has no feed: MSG_CONN_UNKNOWN; it is treated as a FORCE message, so it is a replay input (ledger MALFORMED, no void: outside V) and its anomaly is reported by 7.7. The frames of "
                     "connection 0 recorded after its open are KLINE frames and change nothing.", j,
                     [F("MSG_CONN_UNKNOWN", j.tag["pre"]), F("FORCE_MSG_STRUCTURE", j.tag["pre"], "conn_id=0 reason=ps_type")]))

    # case 12: genesis
    for letter, slug, genesis, title in (("a", "genesis_v2", V2, "a journal chained from the v2 genesis"), ("b", "genesis_v3", V3, "the same journal chained from the v3 genesis")):
        j = J()
        block(j, t1, 1)
        k = j.slot(t1, primary=1, ledger={"COUNTED": 5})
        hx = chain(genesis, j.lines())[k].hex()
        rc = {"anchor_id": "vec-anchor", "index": 1, "seq": k, "head": hx, "time_ms": t1 + 20_000, "time_resolution_ms": 1000, "time_uncertainty_ms": 500}
        cp = j.add({"t": "CHECKPOINT", "rec_ms": t1 + 20_000, "anchored_seq": k, "anchored_head": hx, "receipt": rc}, tag="cp")
        want = [F("HEAD_MISMATCH", cp)] if letter == "a" else []
        vs.append(finish("V13" + letter, slug, title, [12], ["3.2", "3.3", "4.2b"],
                         "One slot and one checkpoint whose anchored_head (and the anchor entry) was computed over the %s genesis. Under r6 (v3 genesis) the v2-chained journal fails with "
                         "HEAD_MISMATCH at the checkpoint line; the v3-chained journal has no finding but CANDLE_LAG_UNSET (r5 reports the opposite for each: the genesis differs)." % ("v2" if letter == "a" else "v3"),
                         j, want, checkpoint=True, anchor=[rc],
                         extra_r6_only=[("HEAD_MISMATCH", cp)] if letter == "a" else [], r5_only_extra=[("HEAD_MISMATCH", cp)] if letter == "b" else []))

    # case 14: physical line number, not seq
    j = J()
    block(j, t1, 1, extras=[dict(anomaly("ps_type", t1 - 350_000), seq_off=100)])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V14", "seq_gap_line", "where is the physical line number, not seq", [14], ["3.1", "7.7b", "8.4"],
                     "The anomalous MSG carries seq = line + 100: SEQ_GAP is reported at its line, and FORCE_MSG_STRUCTURE carries the same physical line number (not the seq value).",
                     j, [F("SEQ_GAP", j.tag["anom"]), F("FORCE_MSG_STRUCTURE", j.tag["anom"], "conn_id=1 reason=ps_type")]))

    # case 15: wrong symbol and o.st = 2
    j = J()
    block(j, t1, 1, extras=[{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, s="ETHUSDT", ps=ABSENT, st=2), "tag": "sym"}])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=1)
    vs.append(finish("V15", "symbol_and_st2", "wrong symbol AND o.st = 2", [15], ["7.5a", "7.7b"],
                     "MALFORMED for the symbol in the replay (slot NONE) and still FORCE_MSG_STRUCTURE with reason st_ne_1: the run-level check is independent of the classification order.",
                     j, [F("FORCE_MSG_STRUCTURE", j.tag["sym"], "conn_id=1 reason=st_ne_1")]))

    # case 17: the decided limit
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    j.add(msg_ev(1, t1 + 20_000, frame(t1 + 19_000, s="ETHUSDT", ps=ABSENT, st=ABSENT)), tag="sym")
    vs.append(finish("V17", "limit_wrong_symbol_after_last_slot", "the decided limit: a wrong-symbol message after the last SLOT", [17], ["7.7a", "9"],
                     "A FORCE message MALFORMED for a non-ps/st reason and recorded after the last SLOT is reported by NO rule (contract section 9). The vector documents the limit; "
                     "it must not be 'fixed' without a new decision.", j, []))

    # my own addition: several anomalies in one message -> the first reason only; plus the float 1.0
    j = J()
    ex = [{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, top={"st": 1}, ps=1, st=2), "tag": "m1"},
          {"conn": 1, "E": t1 - 340_000, "raw": frame(t1 - 340_000, ps="ETHUSDT", st="x"), "tag": "m2"},
          {"conn": 1, "E": t1 - 330_000, "raw": frame(t1 - 330_000, ps=5, st=True), "tag": "m3"},
          {"conn": 1, "E": t1 - 320_000, "raw": frame(t1 - 320_000, st=True), "tag": "m4"},
          {"conn": 1, "E": t1 - 310_000, "raw": frame(t1 - 310_000).replace(b'"st":1', b'"st":1.0'), "tag": "m5"}]
    assert b'"st":1.0' in ex[4]["raw"]
    block(j, t1, 1, extras=ex)
    j.slot(t1, primary=1, ledger={"MALFORMED": 5, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=5)
    vs.append(finish("V19", "first_reason_only", "several anomalies in one message: the first reason only", [], ["7.5a", "7.7b"],
                     "m1: top-level st, o.ps = 1 and o.st = 2 -> st_top_level; m2: o.ps != o.s and o.st = 'x' -> ps_ne_s; m3: o.ps = 5 and o.st = true -> ps_type; m4: o.st = true -> st_type; "
                     "m5: o.st = 1.0 (a number with a fraction is not the integer 1) -> st_type. One finding per message.", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["m1"], "conn_id=1 reason=st_top_level"), F("FORCE_MSG_STRUCTURE", j.tag["m2"], "conn_id=1 reason=ps_ne_s"),
                      F("FORCE_MSG_STRUCTURE", j.tag["m3"], "conn_id=1 reason=ps_type"), F("FORCE_MSG_STRUCTURE", j.tag["m4"], "conn_id=1 reason=st_type"),
                      F("FORCE_MSG_STRUCTURE", j.tag["m5"], "conn_id=1 reason=st_type")]))

    # GPT 2026-11-12 (condition of his answer to Q1): the order of the six reasons is deterministic; ps_no_s comes before the st reasons
    j = J()
    ex = [{"conn": 1, "E": t1 - 350_000, "raw": frame(t1 - 350_000, s=ABSENT, ps="BTCUSDT", st=2), "tag": "m1"},
          {"conn": 1, "E": t1 - 340_000, "raw": frame(t1 - 340_000, s=ABSENT, ps="BTCUSDT", st="1"), "tag": "m2"}]
    block(j, t1, 1, extras=ex)
    j.slot(t1, primary=1, ledger={"MALFORMED": 2, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=2)
    vs.append(finish("V19b", "ps_no_s_before_st", "ps_no_s takes precedence over the st reasons", [20], ["7.5a", "7.7b"],
                     "m1: o.ps = 'BTCUSDT', no o.s, o.st = 2 -> ps_no_s (not st_ne_1); m2: o.ps = 'BTCUSDT', no o.s, o.st = '1' -> ps_no_s (not st_type). One finding per message; "
                     "the order is st_top_level, ps_type, ps_no_s, ps_ne_s, st_type, st_ne_1 (7.5a).", j,
                     [F("FORCE_MSG_STRUCTURE", j.tag["m1"], "conn_id=1 reason=ps_no_s"), F("FORCE_MSG_STRUCTURE", j.tag["m2"], "conn_id=1 reason=ps_no_s")]))

    # my own addition: unparsable frames are not a structural anomaly (7.7a)
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    dup = b'{"e":"forceOrder","e":"forceOrder","E":%d,"o":{"s":"BTCUSDT","st":2}}' % (t1 + 19_000)
    for i, raw in enumerate((b"not json", dup, b'{"E":NaN,"st":2}', b"\xff\xfe\xfd", b'["st"]')):
        j.add(msg_ev(1, t1 + 20_000 + i, raw))
    vs.append(finish("V20", "unparsable_not_structural", "unparsable frames produce no FORCE finding", [], ["7.7a"],
                     "After the last SLOT: a frame that is not JSON, one with a duplicate key, one with NaN, one that is not UTF-8, a JSON array. None is a 'structurally anomalous object' (7.7a): no finding.",
                     j, []))

    # ---- revision 2026-11-14 (GPT's red-team review of the primary verifier, PR #41): cases 23 to 27 of the amended contract text (PR #39, 53a7a3a). New directories only; V01 to V23 are unchanged.
    def undecodable(vid, slug, title, msgs, desc):
        """One SLOT whose V contains every message of `msgs` ((tag, text, intended_raw)); each is UNDECODABLE (2.2): RAW_HASH_MISMATCH, MALFORMED in the replay, one void each,
        and nothing else (no FORCE finding, whatever the intended bytes would have said)."""
        j = J()
        ex = []
        for i, (tag, text, intended) in enumerate(msgs):
            E = t1 - 350_000 + 10_000 * i                         # the E inside every intended frame is this one (checked by the generator below)
            assert b'"E":%d,' % E in intended
            ex.append({"conn": 1, "E": E, "recv": E + 1000, "ev": raw_ev(1, E + 1000, text, intended), "tag": tag})
        block(j, t1, 1, extras=ex)
        n = len(msgs)
        j.slot(t1, primary=1, ledger={"MALFORMED": n, "COUNTED": 5}, status="NONE", reasons=["MALFORMED"], voids=n)
        return finish(vid, slug, title, [23] if vid.startswith("V24") else [24], ["2.1", "2.2", "7.2", "7.5a", "7.5d", "7.7a"], desc, j, [F("RAW_HASH_MISMATCH", j.tag[t]) for t, _, _ in msgs])

    E0 = t1 - 350_000
    valid_full = frame(E0)                                    # a perfectly valid BUY frame (o.ps, o.st present); 190 bytes: its base64 ends in '==' (4 spare bits)
    vs.append(undecodable("V24a", "bad_alphabet_char", "an invalid alphabet character inside raw_b64 of a valid BUY frame",
                          [("m", bad_char(valid_full), valid_full)],
                          "The text of raw_b64 is the base64 of a valid BUY frame with one '!' inserted; sha256 is the hash of the valid frame. A permissive decoder skips the '!', gets the valid frame, finds the hash "
                          "matching and COUNTS the message (slot VALID, six messages). Under 2.2 the text is UNDECODABLE: RAW_HASH_MISMATCH at the line, the message is a replay input with no bytes, "
                          "MALFORMED (ledger MALFORMED 1, one void): slot NONE; no other finding."))
    ps_type_frame = frame(E0 + 10_000, ps=1)                  # 182 bytes: base64 ends in '=' (2 spare bits)
    unk_frame = frame(E0 + 20_000, o_extra={"zz": 1})         # 197 bytes: base64 ends in '='
    unk_b = frame(E0 + 10_000, o_extra={"zz": 1})
    vs.append(undecodable("V24b", "whitespace", "whitespace inside or at the end of raw_b64",
                          [("m1", trailing_newline(frame(E0, ps=1)), frame(E0, ps=1)), ("m2", embedded_space(unk_b), unk_b)],
                          "m1: the base64 of a frame with o.ps = 1 (a ps_type anomaly) followed by a newline; m2: the base64 of a valid frame with an unknown key (o.zz) with one space inside. "
                          "A permissive decoder ignores the whitespace, the hashes match, and it would report FORCE_MSG_STRUCTURE (m1) and FORCE_UNKNOWN_KEY (m2). Under 2.2 both are UNDECODABLE: "
                          "two RAW_HASH_MISMATCH, two MALFORMED messages (two voids), slot NONE, and NO FORCE finding (7.7a: there is no content to check)."))
    full_b = frame(E0)
    vs.append(undecodable("V24c", "padding_and_length", "wrong padding and a length that is not a multiple of 4",
                          [("m1", stripped_padding(full_b), full_b), ("m2", extra_padding(ps_type_frame), ps_type_frame), ("m3", truncated(unk_frame), unk_frame)],
                          "m1: the padding '==' is missing; m2: one '=' too many after the correct padding of a frame with a ps_type anomaly (a permissive decoder ignores it); m3: the last three characters "
                          "of the text are cut off. All three are UNDECODABLE (2.2): three RAW_HASH_MISMATCH, three voids, slot NONE, no FORCE finding, no crash (a decoder may raise an error on m1 and m3)."))
    nc_full = frame(E0)
    vs.append(undecodable("V25a", "non_canonical_two_pad", "non-canonical trailing bits, padding '=='",
                          [("m", non_canonical(nc_full, 8), nc_full)],
                          "The text of a valid BUY frame (190 bytes, padding '==') whose last data character is changed so that the highest of its four spare bits (0x08) is not zero. It still decodes (even with "
                          "validate=True) to exactly the valid frame, and sha256 is that frame's hash, so a decoder that only validates the alphabet counts the message. Under 2.2 the text is not the standard "
                          "encoding of its own bytes: UNDECODABLE, RAW_HASH_MISMATCH, MALFORMED, one void, slot NONE."))
    nc_unk = frame(E0, o_extra={"zz": 1})
    vs.append(undecodable("V25b", "non_canonical_one_pad", "non-canonical trailing bits, padding '=' (a valid frame with an unknown key)",
                          [("m", non_canonical(nc_unk, 2), nc_unk)],
                          "The same for a 197-byte valid frame with an unknown key o.zz (padding '=', two spare bits; the higher one, 0x02, is set: an implementation that looks only at the lowest trailing bit accepts it). A decoder that only validates the alphabet counts the message AND reports "
                          "FORCE_UNKNOWN_KEY. Under 2.2: UNDECODABLE, RAW_HASH_MISMATCH, MALFORMED, one void, slot NONE, no FORCE finding."))

    # case 25: undecodable outside V of the slot, and after the last slot
    far = t1 - 5_000_000
    far_frame = frame(far)
    after_frame = frame(t1 + 19_000)
    j = J()
    block(j, t1, 1, extras=[{"conn": 2, "E": far, "recv": far + 1000, "ev": raw_ev(2, far + 1000, bad_char(far_frame), far_frame), "tag": "far"}], quiet=[(2, 6_000_000)])
    j.slot(t1, primary=1, ledger={"MALFORMED": 1, "COUNTED": 5})
    j.add(raw_ev(1, t1 + 20_000, bad_char(after_frame), after_frame), tag="after")
    vs.append(finish("V26", "undecodable_outside_V", "an undecodable message outside V(tau) and one after the last SLOT", [25], ["2.2", "7.2", "7.5c", "7.5d"],
                     "m1 (connection 2, far before V(tau)) and m2 (after the only SLOT) are valid BUY frames with an invalid character in raw_b64 and the hash of the valid frame. Both are RAW_HASH_MISMATCH. "
                     "m1 is a replay input of the SLOT with no bytes: it is counted in n_messages (6) and as MALFORMED in the ledger and, being outside V, voids nothing: the SLOT is VALID. "
                     "m2 is replayed by no SLOT and changes nothing. No FORCE finding. A permissive decoder would label m1 differently in the ledger (it is a valid frame of a non-primary connection).",
                     j, [F("RAW_HASH_MISMATCH", j.tag["far"]), F("RAW_HASH_MISMATCH", j.tag["after"])]))

    # case 26: a CANDLE event without msg_seq. It says nothing about CANDLE support: no VALID CANDLE event is in any vector.
    t0c = t1 - 900_000
    craw = kline_frame(t0c + 60_000, t0c)
    j = J()
    block(j, t1, 1)
    j.slot(t1, primary=1, ledger={"COUNTED": 5})
    j.add({"t": "CANDLE", "rec_ms": t1 + 30_000, "open_time_ms": t0c, "open": "60000", "recv_ms": t0c + 60_500, "raw_b64": b64(craw), "sha256": hashlib.sha256(craw).hexdigest()}, tag="candle")
    vs.append(finish("V27", "candle_without_msg_seq", "a CANDLE event without msg_seq is BAD_EVENT", [26], ["2.1", "6.5"],
                     "A CANDLE event with every required field of 2.1 except msg_seq (open_time_ms, open, recv_ms, raw_b64 and a matching sha256 are all valid): BAD_EVENT at its line, and no valid CANDLE exists "
                     "(`candles` is {}). THIS VECTOR SAYS NOTHING ABOUT THE CANDLE RULES 6.2 TO 6.9 and does not ask a verifier to implement them: no vector of this package contains a VALID CANDLE event, "
                     "and a verifier that lacks the CANDLE rules must give no verdict for a journal that has one (case 26). The r5 verifier has no msg_seq and sees a valid CANDLE here: the r6 finding is r6-only.",
                     j, [F("BAD_EVENT", j.tag["candle"])], extra_r6_only=[("BAD_EVENT", j.tag["candle"])]))

    # case 27: OUTCOME with L unset
    def outcome_vector(vid, slug, title, status, covered, desc):
        j = J()
        block(j, t1, 1)
        k = j.slot(t1, primary=1, ledger={"COUNTED": 5})
        rc1, c1 = add_checkpoint(j, k, t1 + 20_000, 1, "cp1")
        entry = t1 + 300_000                                     # tau + 5 min (6.1)
        exit_ = entry + 14_400_000                               # entry + 4 h
        out = {"t": "OUTCOME", "rec_ms": exit_ + 70_000, "tau_ms": t1, "status": status}
        if status == "EVAL":
            out.update({"entry_open_ms": entry, "exit_open_ms": exit_, "entry_price": "60000", "exit_price": "60000", "r_bps": "0.0"})     # ln(60000/60000) = 0
        jo = j.add(out, tag="out")
        anchors, extra, findings = [rc1], [("HEAD_MISMATCH", c1)], []
        if status == "EVAL":
            findings += [F("OUTCOME_UNLINKED", jo, "endpoint=entry"), F("OUTCOME_UNLINKED", jo, "endpoint=exit")]
        if covered:
            rc2, c2 = add_checkpoint(j, jo, exit_ + 80_000, 2, "cp2")
            anchors.append(rc2)
            extra.append(("HEAD_MISMATCH", c2))
        else:
            findings += [F("OUTCOME_UNCOVERED", t1), F("TAIL_UNANCHORED", c1 + 1)]
        return finish(vid, slug, title, [27], ["6.4", "6.8", "6.9", "8.4"], desc, j, findings, checkpoint=True, anchor=anchors, r5_only_extra=extra,
                      outcomes={str(t1): "COVERED" if covered else "UNCOVERED"})

    vs.append(outcome_vector("V28a", "eval_outcome_l_unset", "an EVAL outcome with L unset: two OUTCOME_UNLINKED, entry first, then exit", "EVAL", True,
                             "One VALID SLOT, the checkpoint that covers it, an OUTCOME with status EVAL for it (entry_open_ms = tau + 5 min, exit_open_ms = entry + 4 h, equal prices, r_bps 0.0: timing and r_bps are "
                             "correct) and the checkpoint that covers the OUTCOME (`outcomes` COVERED). No CANDLE exists and L is unset (6.8), so no minute is USABLE: exactly two OUTCOME_UNLINKED at the OUTCOME "
                             "line, in the order entry, then exit; their details begin `endpoint=entry` and `endpoint=exit` (the rest of a detail is not compared, so expect.json holds that prefix); no other OUTCOME finding. "
                             "(r5 reports HEAD_MISMATCH at every checkpoint of this journal: its genesis string differs.)"))
    vs.append(outcome_vector("V28b", "no_price_outcome_l_unset", "the same OUTCOME with status NO_PRICE: no finding", "NO_PRICE", True,
                             "The same journal as V28a with an OUTCOME of status NO_PRICE: it references no candle, so it gets no OUTCOME_UNLINKED, and nothing else is reported except the "
                             "always-present CANDLE_LAG_UNSET (`outcomes` COVERED). The verdict is INCOMPLETE, never PASS."))
    vs.append(outcome_vector("V28c", "eval_outcome_uncovered", "an EVAL outcome without a covering checkpoint: UNCOVERED", "EVAL", False,
                             "As V28a, but the journal ends with the OUTCOME: no checkpoint covers it (`outcomes` UNCOVERED, soft OUTCOME_UNCOVERED with `where` = tau_ms, informational TAIL_UNANCHORED at the "
                             "OUTCOME line) next to the two OUTCOME_UNLINKED findings, which do not depend on coverage."))
    return vs


DERIVED = "EXPECT_DERIVED.json"
DERIVED_NOTE = ("Report keys of contract 8.2 that do not depend on the findings, for every vector: n_events (number of parsed lines), head_hex (h_N under the v3 genesis, 3.2) and "
                "outcomes ({tau_ms: COVERED | UNCOVERED}, 6.4). Kept here, not in expect.json, so that the vector directories of the earlier revisions stay byte-identical.")


def derived_text(vs):
    return json.dumps({"note": DERIVED_NOTE, "vectors": {v["expect"]["id"]: v["derived"] for v in vs}}, indent=1, sort_keys=True) + "\n"


def write_all(vs, root):
    root.mkdir(parents=True, exist_ok=True)
    for v in vs:
        d = root / v["dir"]
        d.mkdir(exist_ok=True)
        (d / "journal.jsonl").write_bytes(v["journal"])
        (d / "expect.json").write_text(json.dumps(v["expect"], indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (root / DERIVED).write_text(derived_text(vs), encoding="utf-8")


def main(argv):
    vs = build()
    if "--check" in argv:
        bad = []
        for v in vs:
            d = OUT / v["dir"]
            if not (d / "journal.jsonl").exists() or (d / "journal.jsonl").read_bytes() != v["journal"]:
                bad.append(v["dir"] + "/journal.jsonl")
            want = json.dumps(v["expect"], indent=1, sort_keys=True) + "\n"
            if not (d / "expect.json").exists() or (d / "expect.json").read_text(encoding="utf-8") != want:
                bad.append(v["dir"] + "/expect.json")
        if not (OUT / DERIVED).exists() or (OUT / DERIVED).read_text(encoding="utf-8") != derived_text(vs):
            bad.append(DERIVED)
        extra = sorted(p.name for p in OUT.iterdir() if p.is_dir() and p.name not in {v["dir"] for v in vs}) if OUT.exists() else []
        if bad or extra:
            print("STALE or missing:", bad, "unexpected directories:", extra)
            return 1
        print("vectors are current: %d" % len(vs))
        return 0
    write_all(vs, OUT)
    print("wrote %d vectors" % len(vs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
