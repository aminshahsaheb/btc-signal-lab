#!/usr/bin/env python3
"""Tests for verify_indep.py, built only from JOURNAL_CONTRACT_v2.md.

Contains its own minimal journal writer (class JW) and mock anchor (class Anchor).
Run:  python3 -I test_indep.py
"""
import base64
import hashlib
import inspect
import json
import math
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # -I removes the script directory from sys.path
import verify_indep  # noqa: E402

verify = verify_indep.verify

G = 14_400_000          # GRID_MS
D = 300_000             # ENTRY_DELAY_MS
H = 14_400_000          # HORIZON_MS
GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"
TAU0 = 1000 * G
JID = "J1"

ALL_81 = {
    "BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP", "HEAD_MISMATCH",
    "RECEIPT_INVALID", "CHECKPOINT_ORDER", "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID",
    "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
    "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED",
    "CANDLE_CONFLICT", "CANDLE_NOT_LIVE",
    "SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING",
    "NO_CHECKPOINT", "TAIL_UNANCHORED", "ANCHOR_AHEAD_BENIGN",
}  # SLOT_MISMATCH (section 7, optional replay layer) is intentionally not implemented/tested
SEEN = set()
_TMP = tempfile.mkdtemp(prefix="t_", dir=HERE)
_COUNTER = [0]


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


# ----------------------------------------------------------------------------------------
# Minimal writer and mock anchor (from the contract only)
# ----------------------------------------------------------------------------------------

def canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Anchor:
    """Mock anchor: entries are 1-indexed per journal_id."""

    def __init__(self):
        self.entries = {}

    def submit(self, jid, seq, head, time_ms, res=1, unc=0, anchor_id="A1"):
        lst = self.entries.setdefault(jid, [])
        e = {"anchor_id": anchor_id, "index": len(lst) + 1, "seq": seq, "head": head,
             "time_ms": time_ms, "time_resolution_ms": res, "time_uncertainty_ms": unc}
        lst.append(e)
        return dict(e)

    def get(self, jid, index):
        lst = self.entries.get(jid, [])
        if isinstance(index, int) and 1 <= index <= len(lst):
            return dict(lst[index - 1])
        return None

    def latest(self, jid):
        return len(self.entries.get(jid, []))


class HoleAnchor(Anchor):
    """Anchor whose get() returns None for the listed indexes although latest() counts them."""

    def __init__(self, holes):
        super().__init__()
        self.holes = set(holes)

    def get(self, jid, index):
        if index in self.holes:
            return None
        return super().get(jid, index)


class JW:
    def __init__(self, anchor, jid=JID):
        self.anchor = anchor
        self.jid = jid
        self.lines = []
        self._h = [hashlib.sha256(GENESIS).digest()]

    def raw(self, line):
        self.lines.append(line)
        self._h.append(hashlib.sha256(self._h[-1] + line).digest())
        return len(self.lines)

    def add(self, ev):
        ev = dict(ev)
        ev.setdefault("seq", len(self.lines) + 1)
        ev.setdefault("rec_ms", 5_000_000 + len(self.lines))
        return self.raw(canon(ev))

    def head_hex(self, k=None):
        k = len(self.lines) if k is None else k
        return self._h[k].hex()

    def ck(self, k=None, time_ms=1_000, res=1, unc=0, anchor_id="A1", ev_over=None,
           rc_over=None, anchor_over=None, drop=False, head=None):
        if k is None:
            k = len(self.lines)
        if head is None:
            head = self.head_hex(k) if 0 <= k <= len(self.lines) else "0" * 64
        rc = self.anchor.submit(self.jid, k, head, time_ms, res, unc, anchor_id)
        if anchor_over:
            self.anchor.entries[self.jid][-1].update(anchor_over)
        if drop:
            self.anchor.entries[self.jid].pop()
        rc = dict(rc)
        rc.update(rc_over or {})
        ev = {"t": "CHECKPOINT", "anchored_seq": k, "anchored_head": head, "receipt": rc}
        ev.update(ev_over or {})
        return self.add(ev)

    def bytes_(self, newline=True):
        if not self.lines:
            return b""
        return b"\n".join(self.lines) + (b"\n" if newline else b"")


def e_session():
    return {"t": "SESSION"}


def e_conn(cid=1, ev="open", ms=1000):
    return {"t": "CONN", "conn_id": cid, "ev": ev, "ms": ms}


def e_msg(raw=b"hello"):
    return {"t": "MSG", "conn_id": 1, "recv_ms": 10, "raw_b64": b64(raw), "sha256": sha(raw)}


def e_candle(open_time, open_="100.5", recv=None, raw=None):
    raw = raw if raw is not None else b"candle-%d-%s" % (open_time, open_.encode())
    return {"t": "CANDLE", "open_time_ms": open_time, "open": open_,
            "recv_ms": open_time + 5 if recv is None else recv,
            "raw_b64": b64(raw), "sha256": sha(raw)}


def e_slot(tau, **over):
    ev = {"t": "SLOT", "tau_ms": tau, "status": "VALID", "reasons": [], "primary_conn": 1,
          "N_total": 3, "N_BUY": 2, "N_SELL": 1, "side": 1, "malformed_voids": 0,
          "n_messages": 3, "sumW_BUY": "1.5", "sumW_SELL": "0.5", "X_sn": None,
          "ledger": {"x": 1}}
    ev.update(over)
    return ev


def rbps(entry, exit_):
    return "%.9f" % (10000.0 * math.log(float(exit_) / float(entry)))


def e_outcome(tau, entry="100.5", exit_="101.5", **over):
    ev = {"t": "OUTCOME", "tau_ms": tau, "status": "EVAL", "entry_open_ms": tau + D,
          "exit_open_ms": tau + D + H, "entry_price": entry, "exit_price": exit_,
          "r_bps": rbps(entry, exit_)}
    ev.update(over)
    return ev


def without(ev, *keys):
    ev = dict(ev)
    for k in keys:
        del ev[k]
    return ev


def mk():
    a = Anchor()
    return a, JW(a)


def run_raw(src, anchor, vt=0, newline=True, jid=JID):
    """src: JW or raw bytes.  Returns the RAW verify() result (r5: with the REPLAY_NOT_RUN markers) and records seen findings."""
    data = src.bytes_(newline) if isinstance(src, JW) else src
    _COUNTER[0] += 1
    path = os.path.join(_TMP, "j%05d.jsonl" % _COUNTER[0])
    with open(path, "wb") as fh:
        fh.write(data)
    res = verify(path, anchor, jid, vt)
    with open(path, "rb") as fh:
        assert fh.read() == data, "verifier modified the file"
    for f in res["findings"]:
        SEEN.add(f[0])
    assert res["verdict"] != "PASS" and res["replayed"] is False and res["analysis_eligible"] is False, res["verdict"]      # r5: this verifier has no replay
    return res


def sections_view(res):
    """r5: the result of sections 1-6 only (REPLAY_NOT_RUN and the markers removed; INCOMPLETE read as the old PASS), so the section-level assertions keep their meaning."""
    assert "REPLAY_NOT_RUN" in res["hard"] and [f[1] for f in res["findings"] if f[0] == "REPLAY_NOT_RUN"] == [0]
    out = dict(res)
    out["findings"] = [f for f in res["findings"] if f[0] != "REPLAY_NOT_RUN"]
    out["hard"] = [h for h in res["hard"] if h != "REPLAY_NOT_RUN"]
    out["verdict"] = "FAIL" if out["hard"] else "PASS"
    del out["replayed"], out["analysis_eligible"]
    return out


def run(src, anchor, vt=0, newline=True, jid=JID):
    return sections_view(run_raw(src, anchor, vt, newline, jid))


def names(res):
    return {f[0] for f in res["findings"]}


def wheres(res, name):
    return [f[1] for f in res["findings"] if f[0] == name]


def clean_journal():
    """Three SLOTs (taus TAU0, +G, +2G), each anchored in time, one OUTCOME. 13 lines."""
    a, jw = mk()
    jw.add(e_session())                                   # 1
    jw.add(e_conn())                                      # 2
    jw.add(e_msg())                                       # 3
    jw.add(e_slot(TAU0))                                  # 4
    jw.ck(time_ms=TAU0 + 1000)                            # 5  k=4
    jw.add(e_candle(TAU0 + D, "100.5"))                   # 6
    jw.add(e_candle(TAU0 + D + H, "101.5"))               # 7
    jw.add(e_outcome(TAU0))                               # 8
    jw.add(e_slot(TAU0 + G))                              # 9
    jw.add({"t": "PING", "conn_id": 1, "ms": 5})          # 10
    jw.ck(time_ms=TAU0 + G + 1000)                        # 11 k=10
    jw.add(e_slot(TAU0 + 2 * G))                          # 12
    jw.ck(time_ms=TAU0 + 2 * G + 1000)                    # 13 k=12
    return a, jw


# ----------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------

class TestCleanAndShape(unittest.TestCase):
    def test_clean_pass(self):
        a, jw = clean_journal()
        res = run(jw, a, vt=TAU0 + 2 * G + D + 1)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["findings"], [])
        self.assertEqual(res["hard"], [])
        self.assertEqual(res["soft"], [])
        self.assertEqual(res["n_events"], 13)
        self.assertEqual(res["head_hex"], jw.head_hex())
        self.assertEqual(res["slots"], {TAU0: "OK", TAU0 + G: "OK", TAU0 + 2 * G: "OK"})
        self.assertEqual(res["missing"], [])
        self.assertEqual(res["outcomes"], {TAU0: "COVERED"})
        self.assertEqual(sorted(res), sorted(["verdict", "findings", "hard", "soft", "n_events",
                                              "head_hex", "slots", "missing", "outcomes"]))

    def test_deterministic_and_clock_independent(self):
        a, jw = clean_journal()
        r1 = run(jw, a, vt=5)
        r2 = run(jw, a, vt=5)
        self.assertEqual(r1, r2)

    def test_empty_file(self):
        a = Anchor()
        res = run(b"", a)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["n_events"], 0)
        self.assertEqual(res["head_hex"], hashlib.sha256(GENESIS).hexdigest())
        self.assertEqual(names(res), {"NO_CHECKPOINT"})
        self.assertEqual((res["slots"], res["missing"], res["hard"], res["soft"]), ({}, [], [], []))

    def test_empty_file_with_anchor_entries_is_truncation(self):
        a = Anchor()
        a.submit(JID, 5, "ab" * 32, 10)
        res = run(b"", a)
        self.assertEqual(res["hard"], ["TRUNCATION_OR_REPLACEMENT"])

    def test_finding_shape(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0 + 1))
        res = run(jw, a)
        for f in res["findings"]:
            self.assertIsInstance(f, list)
            self.assertEqual(len(f), 3)
            self.assertIsInstance(f[0], str)
            self.assertIsInstance(f[1], int)
            self.assertIsInstance(f[2], str)
        self.assertEqual(res["hard"], sorted(set(res["hard"])))

    def test_extra_fields_ignored(self):
        a, jw = mk()
        jw.add(dict(e_session(), whatever={"a": [1, 2, {"b": None}]}))
        jw.add(dict(e_slot(TAU0), extra_field="x"))
        jw.ck(time_ms=TAU0 + 5)
        res = run(jw, a, vt=TAU0 + G)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["findings"], [])


class TestEncoding(unittest.TestCase):
    BAD = {
        "invalid_utf8": b"\xff\xfe",
        "invalid_utf8_in_string": b'{"a":"\xc3\x28"}',
        "surrogate_utf8": b'{"a":"\xed\xa0\x80"}',
        "overlong_utf8": b'{"a":"\xc0\xaf"}',
        "truncated_json": b"{",
        "array": b"[1,2]",
        "string": b'"abc"',
        "number": b"123",
        "null": b"null",
        "empty_line": b"",
        "trailing_garbage": b'{"t":"SESSION","seq":3,"rec_ms":1} x',
        "dup_key_top": b'{"rec_ms":1,"seq":3,"t":"SESSION","t":"SESSION"}',
        "dup_key_escaped": b'{"a":1,"\\u0061":2,"rec_ms":1,"seq":3,"t":"SESSION"}',
        "dup_key_nested": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":{"a":1,"a":2}}',
        "dup_key_in_list": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":[{"a":1,"a":2}]}',
        "nan": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":NaN}',
        "infinity": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":Infinity}',
        "neg_infinity": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":-Infinity}',
        "fraction": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":1.0}',
        "fraction_in_seq": b'{"rec_ms":1,"seq":3.0,"t":"SESSION"}',
        "exponent": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":1e3}',
        "exponent_upper": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":1E3}',
        "negative_fraction": b'{"rec_ms":1,"seq":3,"t":"SESSION","x":-0.5}',
        "leading_zero": b'{"rec_ms":01,"seq":3,"t":"SESSION"}',
        "single_quotes": b"{'t':'SESSION'}",
        "bom": b'\xef\xbb\xbf{"rec_ms":1,"seq":3,"t":"SESSION"}',
    }

    def test_each_bad_line_stops_parsing(self):
        for label, bad in self.BAD.items():
            with self.subTest(label):
                a, jw = mk()
                jw.add(e_session())               # 1
                jw.add(e_conn())                  # 2
                jw.raw(bad)                       # 3 -> BAD_ENCODING, parsing stops
                jw.add(e_slot(TAU0 + 1))          # 4 ignored: would be SLOT_OFF_GRID
                jw.add(e_outcome(TAU0))           # 5 ignored: would be OUTCOME_ORPHAN
                res = run(jw, a)
                self.assertEqual(res["hard"], ["BAD_ENCODING"], res["findings"])
                self.assertEqual(wheres(res, "BAD_ENCODING"), [3])
                self.assertEqual(res["n_events"], 2)
                self.assertEqual(res["head_hex"], jw.head_hex(2))
                self.assertEqual(res["verdict"], "FAIL")

    def test_findings_still_computed_on_the_prefix(self):
        a, jw = mk()
        jw.add(e_session())                       # 1
        jw.add(e_slot(TAU0))                      # 2 -> prefix has an unanchored slot
        jw.raw(b"{")                              # 3 bad
        jw.ck(k=2, time_ms=TAU0 + 5)              # 4 ignored (would cover the slot)
        res = run(jw, a, vt=TAU0 + D)             # deadline equality => UNANCHORED
        self.assertEqual(res["slots"], {TAU0: "UNANCHORED"})
        self.assertEqual(res["soft"], ["SLOT_UNANCHORED"])
        self.assertIn("NO_CHECKPOINT", names(res))
        # the anchor knows a checkpoint (k=2) that the cut journal no longer shows; the journal still reproduces h_2,
        # so contract 4.3 makes it the informational ANCHOR_AHEAD_BENIGN, NOT a hard TRUNCATION_OR_REPLACEMENT
        # (test expectation corrected by the integrator after the implementer was cut off by a usage limit; verify_indep.py unchanged)
        self.assertEqual(res["hard"], ["BAD_ENCODING"])
        self.assertIn("ANCHOR_AHEAD_BENIGN", names(res))

    def test_partial_last_line(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_conn())
        data = jw.bytes_() + b'{"rec_ms":5,"seq":3,"t":"SESS'
        res = run(data, a)
        self.assertEqual(res["hard"], ["BAD_ENCODING"])
        self.assertEqual(wheres(res, "BAD_ENCODING"), [3])
        self.assertEqual(res["n_events"], 2)
        self.assertEqual(res["head_hex"], jw.head_hex(2))

    def test_valid_last_line_without_newline_is_still_discarded(self):
        a, jw = mk()
        jw.add(e_session())
        res = run(jw, a, newline=False)
        self.assertEqual(res["hard"], ["BAD_ENCODING"])
        self.assertEqual(wheres(res, "BAD_ENCODING"), [1])
        self.assertEqual(res["n_events"], 0)
        self.assertEqual(res["head_hex"], hashlib.sha256(GENESIS).hexdigest())

    def test_partial_line_number_counts_newlines(self):
        a, jw = mk()
        for _ in range(4):
            jw.add(e_session())
        res = run(jw.bytes_() + b"xyz", a)
        self.assertEqual(wheres(res, "BAD_ENCODING"), [5])
        self.assertEqual(res["n_events"], 4)

    def test_single_newline_is_an_empty_line(self):
        res = run(b"\n", Anchor())
        self.assertEqual(res["hard"], ["BAD_ENCODING"])
        self.assertEqual(wheres(res, "BAD_ENCODING"), [1])
        self.assertEqual(res["n_events"], 0)

    def test_big_integers_are_fine(self):
        a, jw = mk()
        jw.add(dict(e_session(), big=10 ** 30, neg=-5))
        res = run(jw, a)
        self.assertEqual(res["hard"], [])


class TestCanonical(unittest.TestCase):
    CASES = {
        "spaces": b'{"t": "SESSION", "seq": 2, "rec_ms": 7}',
        "key_order": b'{"t":"SESSION","seq":2,"rec_ms":7}',
        "escaped_ascii": b'{"note":"\\u0041","rec_ms":7,"seq":2,"t":"SESSION"}',
        "minus_zero": b'{"rec_ms":-0,"seq":2,"t":"SESSION"}',
        "non_ascii_literal": '{"note":"é","rec_ms":7,"seq":2,"t":"SESSION"}'.encode("utf-8"),
        "trailing_cr": b'{"rec_ms":7,"seq":2,"t":"SESSION"}\r',
        "leading_space": b' {"rec_ms":7,"seq":2,"t":"SESSION"}',
        "lowercase_unicode_escape": b'{"note":"\\u00E9","rec_ms":7,"seq":2,"t":"SESSION"}',
        "escaped_slash": b'{"note":"a\\/b","rec_ms":7,"seq":2,"t":"SESSION"}',
    }

    def test_noncanonical_lines(self):
        for label, line in self.CASES.items():
            with self.subTest(label):
                a, jw = mk()
                jw.add(e_session())               # 1
                jw.raw(line)                      # 2 parsed, used as stored
                jw.add(e_session())               # 3
                jw.ck(k=3, time_ms=1)             # 4: chain over stored bytes => no HEAD_MISMATCH
                res = run(jw, a)
                self.assertEqual(res["hard"], ["NOT_CANONICAL"], res["findings"])
                self.assertEqual(wheres(res, "NOT_CANONICAL"), [2])
                self.assertEqual(res["n_events"], 4)
                self.assertEqual(res["head_hex"], jw.head_hex())

    def test_one_finding_per_line(self):
        a, jw = mk()
        jw.raw(b'{"t": "SESSION", "seq": 1, "rec_ms": 7}')
        jw.raw(b'{"t": "SESSION", "seq": 2, "rec_ms": 7}')
        jw.add(e_session())
        res = run(jw, a)
        self.assertEqual(wheres(res, "NOT_CANONICAL"), [1, 2])


class TestBadEvent(unittest.TestCase):
    def one_bad(self, ev, extra_hard=()):
        a, jw = mk()
        jw.add(e_session())
        jw.add(ev)
        jw.add(e_session())
        res = run(jw, a)
        self.assertEqual(wheres(res, "BAD_EVENT"), [2], res["findings"])
        self.assertEqual(res["hard"], sorted({"BAD_EVENT", *extra_hard}), res["findings"])
        self.assertEqual(res["n_events"], 3)
        self.assertEqual(res["head_hex"], jw.head_hex())  # BAD_EVENT lines are chained
        return res

    def test_bad_variants(self):
        good_slot = e_slot(TAU0)
        good_ev = e_outcome(TAU0)
        variants = {
            "unknown_t": {"t": "FOO"},
            "t_not_string": {"t": 5},
            "lowercase_t": {"t": "session"},
            "rec_ms_string": {"t": "SESSION", "rec_ms": "5"},
            "rec_ms_bool": {"t": "SESSION", "rec_ms": True},
            "rec_ms_null": {"t": "SESSION", "rec_ms": None},
            "conn_missing_id": without(e_conn(), "conn_id"),
            "conn_bad_ev": e_conn(ev="bounce"),
            "conn_id_bool": e_conn(cid=True),
            "ping_ms_string": {"t": "PING", "conn_id": 1, "ms": "5"},
            "msg_missing_sha": without(e_msg(), "sha256"),
            "msg_raw_not_string": dict(e_msg(), raw_b64=5),
            "clock_null": {"t": "CLOCK", "offset_ms": None, "ms": 1},
            "candle_leading_zero": e_candle(TAU0, "01"),
            "candle_trailing_dot": e_candle(TAU0, "1."),
            "candle_leading_dot": e_candle(TAU0, ".5"),
            "candle_negative": e_candle(TAU0, "-1"),
            "candle_open_number": dict(e_candle(TAU0), open=100),
            "candle_missing_recv": without(e_candle(TAU0), "recv_ms"),
            "slot_bad_status": e_slot(TAU0, status="MAYBE"),
            "slot_reasons_not_strings": e_slot(TAU0, reasons=[1]),
            "slot_reasons_not_list": e_slot(TAU0, reasons="x"),
            "slot_primary_string": e_slot(TAU0, primary_conn="x"),
            "slot_ledger_string_value": e_slot(TAU0, ledger={"a": "x"}),
            "slot_ledger_bool_value": e_slot(TAU0, ledger={"a": True}),
            "slot_ledger_not_object": e_slot(TAU0, ledger=[1]),
            "slot_sumw_number": e_slot(TAU0, sumW_BUY=1),
            "slot_sumw_bad_dec": e_slot(TAU0, sumW_SELL="1e5"),
            "slot_xsn_number": e_slot(TAU0, X_sn=5),
            "slot_missing_tau": without(good_slot, "tau_ms"),
            "slot_missing_n_messages": without(good_slot, "n_messages"),
            "outcome_bad_status": e_outcome(TAU0, status="WAT"),
            "outcome_eval_missing_rbps": without(good_ev, "r_bps"),
            "outcome_eval_rbps_number": e_outcome(TAU0, r_bps=5),
            "outcome_eval_price_number": e_outcome(TAU0, entry_price=100),
            "outcome_eval_missing_exit_open": without(good_ev, "exit_open_ms"),
            "checkpoint_seq_string": {"t": "CHECKPOINT", "anchored_seq": "3", "anchored_head": "a",
                                      "receipt": {}},
            "checkpoint_no_receipt": {"t": "CHECKPOINT", "anchored_seq": 1, "anchored_head": "a"},
            "checkpoint_receipt_missing_field": {
                "t": "CHECKPOINT", "anchored_seq": 1, "anchored_head": "a",
                "receipt": {"anchor_id": "x", "index": 1, "seq": 1, "head": "a", "time_ms": 1,
                            "time_resolution_ms": 1}},
            "checkpoint_receipt_index_string": {
                "t": "CHECKPOINT", "anchored_seq": 1, "anchored_head": "a",
                "receipt": {"anchor_id": "x", "index": "1", "seq": 1, "head": "a", "time_ms": 1,
                            "time_resolution_ms": 1, "time_uncertainty_ms": 0}},
        }
        for label, ev in variants.items():
            with self.subTest(label):
                self.one_bad(ev)

    def test_bad_seq_variants_also_gap(self):
        for label, ev in {"missing": {"t": "SESSION"}, "string": {"t": "SESSION", "seq": "2"},
                          "bool": {"t": "SESSION", "seq": True}}.items():
            with self.subTest(label):
                a, jw = mk()
                jw.add(e_session())
                jw.raw(canon(dict(ev, rec_ms=3)))
                res = run(jw, a)
                self.assertIn("BAD_EVENT", res["hard"])
                self.assertIn("SEQ_GAP", res["hard"])

    def test_valid_neighbours_of_bad_variants(self):
        # positive controls: these must NOT be BAD_EVENT
        a, jw = mk()
        jw.add(e_session())
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})
        jw.add(e_conn(ev="close"))
        jw.add(e_slot(TAU0, primary_conn=None, X_sn="abc", reasons=["a", "b"], ledger={}))
        jw.add(e_candle(TAU0, "0.5"))
        jw.add(e_candle(TAU0 + 1, "0"))
        jw.add(e_candle(TAU0 + 2, "10.25"))
        jw.add({"t": "CLOCK", "offset_ms": -5, "ms": 1})
        res = run(jw, a)
        self.assertNotIn("BAD_EVENT", names(res))

    def test_bad_event_excluded_from_checks(self):
        a, jw = mk()
        jw.add(e_session())                                      # 1
        jw.add(e_slot(TAU0 + 1, status="MAYBE"))                 # 2 BAD_EVENT slot (off grid)
        jw.add(e_candle(TAU0, "01", recv=TAU0 - 100))            # 3 BAD_EVENT candle (not live)
        jw.add(e_outcome(TAU0, status="WAT"))                    # 4 BAD_EVENT outcome (orphan)
        jw.add({"t": "CHECKPOINT", "anchored_seq": "3", "anchored_head": "x",
                "receipt": {}})                                  # 5 BAD_EVENT checkpoint
        a.submit(JID, 4, jw.head_hex(4), 10)                     # anchor knows an entry
        res = run(jw, a)
        self.assertEqual(res["hard"], ["BAD_EVENT"])
        self.assertEqual(wheres(res, "BAD_EVENT"), [2, 3, 4, 5])
        self.assertEqual(res["slots"], {})
        self.assertIn("NO_CHECKPOINT", names(res))               # M == 0: bad checkpoint ignored
        self.assertIn("ANCHOR_AHEAD_BENIGN", names(res))         # anchor index 1 > M, consistent

    def test_bad_event_inside_chain_does_not_break_checkpoints(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add({"t": "FOO"})
        jw.add(e_session())
        jw.ck(k=3, time_ms=5)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["BAD_EVENT"])


class TestRawHash(unittest.TestCase):
    def one(self, ev):
        a, jw = mk()
        jw.add(e_session())
        jw.add(ev)
        jw.add(e_session())
        res = run(jw, a)
        self.assertEqual(res["hard"], ["RAW_HASH_MISMATCH"], res["findings"])
        self.assertEqual(wheres(res, "RAW_HASH_MISMATCH"), [2])

    def test_bad_hash_variants(self):
        good = e_msg(b"abc")
        for label, ev in {
            "msg_wrong_sha": dict(good, sha256=sha(b"abd")),
            "msg_uppercase_sha": dict(good, sha256=sha(b"abc").upper()),
            "msg_invalid_base64_chars": dict(good, raw_b64="!!!!"),
            "msg_bad_padding": dict(good, raw_b64="YWJjZA="),
            "msg_missing_padding": dict(good, raw_b64="YWJjZA"),
            "msg_whitespace_in_base64": dict(good, raw_b64="YWJj\nZA=="),
            "msg_urlsafe_alphabet": dict(e_msg(b"\xfb\xff"), raw_b64="-_8="),
            "msg_non_ascii_base64": dict(good, raw_b64="YWJjé"),
            "candle_wrong_sha": dict(e_candle(TAU0), sha256="0" * 64),
            "candle_invalid_base64": dict(e_candle(TAU0), raw_b64="@@@"),
        }.items():
            with self.subTest(label):
                self.one(ev)

    def test_good_hashes(self):
        a, jw = mk()
        jw.add(e_msg(b""))
        jw.add(e_msg(b"\x00\xff" * 100))
        jw.add(e_candle(TAU0))
        res = run(jw, a)
        self.assertEqual(res["hard"], [])


class TestSeqGap(unittest.TestCase):
    def test_only_first_gap_reported(self):
        a, jw = mk()
        jw.add(e_session())                         # 1
        jw.add(e_session())                         # 2
        jw.add(dict(e_session(), seq=4))            # 3 gap
        jw.add(dict(e_session(), seq=9))            # 4 later mismatch: not reported again
        res = run(jw, a)
        self.assertEqual(res["hard"], ["SEQ_GAP"])
        self.assertEqual(wheres(res, "SEQ_GAP"), [3])
        self.assertEqual(res["n_events"], 4)

    def test_first_line_zero_based(self):
        a, jw = mk()
        jw.add(dict(e_session(), seq=0))
        jw.add(dict(e_session(), seq=1))
        res = run(jw, a)
        self.assertEqual(wheres(res, "SEQ_GAP"), [1])

    def test_duplicate_seq(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(dict(e_session(), seq=1))
        res = run(jw, a)
        self.assertEqual(wheres(res, "SEQ_GAP"), [2])


class TestCheckpointHeads(unittest.TestCase):
    def test_head_mismatch_single(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=3, head=jw.head_hex(2), time_ms=5)     # anchor and receipt agree with the wrong head
        res = run(jw, a)
        self.assertEqual(res["hard"], ["HEAD_MISMATCH"])
        self.assertEqual(wheres(res, "HEAD_MISMATCH"), [4])

    def test_head_uppercase_is_mismatch(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, head=jw.head_hex(2).upper(), time_ms=5)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["HEAD_MISMATCH"])

    def test_rewritten_history(self):
        a, jw = clean_journal()
        lines = list(jw.lines)
        lines[1] = canon(dict(e_conn(ms=1001), seq=2, rec_ms=5_000_001))   # line 2 replaced
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 2 * G + D + 1)
        self.assertEqual(res["hard"], ["HEAD_MISMATCH"])
        self.assertEqual(wheres(res, "HEAD_MISMATCH"), [5, 11, 13])
        self.assertNotEqual(res["head_hex"], jw.head_hex())

    def test_rewrite_after_last_checkpoint_is_not_detected(self):
        # section 9: events after the last anchored head are not authenticated
        a, jw = clean_journal()
        jw.add(e_session())
        lines = list(jw.lines)
        lines[-1] = canon(dict(e_session(), seq=14, rec_ms=1))
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 2 * G + D + 1)
        self.assertEqual(res["hard"], [])
        self.assertEqual(names(res), {"TAIL_UNANCHORED"})

    def test_k_beyond_n_has_no_head_check(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=99, time_ms=5)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CHECKPOINT_ORDER"])


class TestReceipt(unittest.TestCase):
    def base(self, **kw):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=1234, res=10, unc=7, anchor_id="AID", **kw)
        return run(jw, a)

    def test_ok(self):
        res = self.base()
        self.assertEqual(res["hard"], [])

    def test_variants(self):
        cases = {
            "entry_missing": dict(drop=True),
            "anchor_head": dict(anchor_over={"head": "0" * 64}),
            "anchor_seq": dict(anchor_over={"seq": 1}),
            "anchor_time_ms": dict(anchor_over={"time_ms": 1235}),
            "anchor_resolution": dict(anchor_over={"time_resolution_ms": 11}),
            "anchor_uncertainty": dict(anchor_over={"time_uncertainty_ms": 8}),
            "anchor_id": dict(anchor_over={"anchor_id": "OTHER"}),
            "receipt_head": dict(rc_over={"head": "f" * 64}),
            "receipt_seq": dict(rc_over={"seq": 1}),
            "receipt_time_ms": dict(rc_over={"time_ms": 1}),
            "receipt_resolution": dict(rc_over={"time_resolution_ms": 9}),
            "receipt_uncertainty": dict(rc_over={"time_uncertainty_ms": 6}),
            "receipt_anchor_id": dict(rc_over={"anchor_id": "OTHER"}),
        }
        for label, kw in cases.items():
            with self.subTest(label):
                res = self.base(**kw)
                self.assertEqual(res["hard"], ["RECEIPT_INVALID"], res["findings"])
                self.assertEqual(wheres(res, "RECEIPT_INVALID"), [3])

    def test_resolution_below_one(self):
        for res_ms in (0, -5):
            with self.subTest(res_ms):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_session())
                jw.ck(k=2, time_ms=5, res=res_ms, unc=0)   # anchor and receipt consistent
                r = run(jw, a)
                self.assertEqual(r["hard"], ["RECEIPT_INVALID"])

    def test_negative_uncertainty(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=5, res=1, unc=-1)
        r = run(jw, a)
        self.assertEqual(r["hard"], ["RECEIPT_INVALID"])

    def test_boundary_values_accepted(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=0, res=1, unc=0)
        self.assertEqual(run(jw, a)["hard"], [])

    def test_unknown_journal_id(self):
        a, jw = clean_journal()
        res = run(jw, a, vt=0, jid="OTHER")   # anchor knows nothing about this id
        self.assertIn("RECEIPT_INVALID", res["hard"])
        self.assertEqual(wheres(res, "RECEIPT_INVALID"), [5, 11, 13])


class TestCheckpointOrder(unittest.TestCase):
    def test_k_zero(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=0, time_ms=5)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CHECKPOINT_ORDER"])
        self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [3])

    def test_k_negative(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=-1, time_ms=5)
        self.assertEqual(run(jw, a)["hard"], ["CHECKPOINT_ORDER"])

    def test_k_equal_or_beyond_own_line(self):
        for k in (3, 4, 50):
            with self.subTest(k):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_session())
                jw.ck(k=k, time_ms=5)
                res = run(jw, a)
                self.assertIn("CHECKPOINT_ORDER", res["hard"])
                self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [3])

    def test_k_not_increasing(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=5)      # line 3
        jw.ck(k=2, time_ms=6)      # line 4: k <= prev_k
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CHECKPOINT_ORDER"])
        self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [4])

    def test_prev_k_is_running_maximum(self):
        a, jw = mk()
        for _ in range(5):
            jw.add(e_session())
        jw.ck(k=5, time_ms=5)      # line 6
        jw.ck(k=3, time_ms=6)      # line 7: 3 <= 5
        jw.ck(k=4, time_ms=7)      # line 8: 4 <= 5 (max), would pass if prev_k were just 3
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CHECKPOINT_ORDER"])
        self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [7, 8])

    def test_index_skips(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        a.submit(JID, 1, jw.head_hex(1), 3)   # entry 1 never appears in the journal
        jw.ck(k=2, time_ms=5)                 # receipt.index == 2, expected 1
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CHECKPOINT_ORDER"])
        self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [3])

    def test_index_repeats(self):
        a, jw = mk()
        for _ in range(3):
            jw.add(e_session())
        jw.ck(k=2, time_ms=5)                       # line 4, index 1
        jw.ck(k=3, time_ms=6, rc_over={"index": 1})  # line 5: index repeats (and no matching entry)
        res = run(jw, a)
        self.assertIn("CHECKPOINT_ORDER", res["hard"])
        self.assertEqual(wheres(res, "CHECKPOINT_ORDER"), [5])

    def test_well_ordered(self):
        a, jw = mk()
        for _ in range(3):
            jw.add(e_session())
        jw.ck(k=1, time_ms=5)
        jw.ck(k=2, time_ms=6)
        jw.ck(k=5, time_ms=7)
        self.assertEqual(run(jw, a)["hard"], [])


class TestAnchorAhead(unittest.TestCase):
    def test_benign_cut_before_last_checkpoint(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=5)                       # line 3
        jw.add(e_session())                         # line 4
        a.submit(JID, 4, jw.head_hex(4), 9)         # anchored, but CHECKPOINT line never written
        res = run(jw, a)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(names(res), {"ANCHOR_AHEAD_BENIGN", "TAIL_UNANCHORED"})
        self.assertEqual(res["hard"], [])

    def test_seq_equal_n_ok_n_plus_one_not(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        a.submit(JID, 2, jw.head_hex(2), 9)          # e.seq == N, matching head
        res = run(jw, a)
        self.assertEqual(res["hard"], [])
        self.assertIn("ANCHOR_AHEAD_BENIGN", names(res))
        a2, jw2 = mk()
        jw2.add(e_session())
        jw2.add(e_session())
        a2.submit(JID, 3, jw2.head_hex(2), 9)        # e.seq == N + 1
        self.assertEqual(run(jw2, a2)["hard"], ["TRUNCATION_OR_REPLACEMENT"])

    def test_head_differs(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        a.submit(JID, 2, jw.head_hex(1), 9)
        self.assertEqual(run(jw, a)["hard"], ["TRUNCATION_OR_REPLACEMENT"])

    def test_missing_entry(self):
        a = HoleAnchor({1})
        jw = JW(a)
        jw.add(e_session())
        a.submit(JID, 1, jw.head_hex(1), 9)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["TRUNCATION_OR_REPLACEMENT"])

    def test_real_truncation(self):
        a, jw = clean_journal()
        cut = jw.lines[:5]                         # keep up to and including checkpoint line 5
        res = run(b"\n".join(cut) + b"\n", a, vt=0)
        self.assertEqual(res["hard"], ["TRUNCATION_OR_REPLACEMENT"])
        self.assertEqual(len(wheres(res, "TRUNCATION_OR_REPLACEMENT")), 2)   # anchor indexes 2, 3

    def test_no_finding_for_entries_the_journal_owns(self):
        a, jw = clean_journal()
        res = run(jw, a, vt=TAU0 + 2 * G + D + 1)
        self.assertNotIn("TRUNCATION_OR_REPLACEMENT", names(res))
        self.assertNotIn("ANCHOR_AHEAD_BENIGN", names(res))


class TestInformational(unittest.TestCase):
    def test_no_checkpoint(self):
        a, jw = mk()
        jw.add(e_session())
        res = run(jw, a)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(names(res), {"NO_CHECKPOINT"})

    def test_tail_unanchored(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=5)
        jw.add(e_session())
        res = run(jw, a)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(names(res), {"TAIL_UNANCHORED"})

    def test_no_tail_when_checkpoint_is_last(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_session())
        jw.ck(k=2, time_ms=5)
        self.assertEqual(run(jw, a)["findings"], [])


class TestSlots(unittest.TestCase):
    def test_off_grid(self):
        for off in (1, G - 1, -1, 7):
            with self.subTest(off):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_slot(TAU0 + off))
                jw.ck(time_ms=TAU0 + 10)
                res = run(jw, a, vt=TAU0 + 2 * G)
                self.assertEqual(res["hard"], ["SLOT_OFF_GRID"])
                self.assertEqual(wheres(res, "SLOT_OFF_GRID"), [2])        # where = line (contract 8.2 table)
                self.assertEqual(res["missing"], [])

    def test_on_grid_negative_and_zero(self):
        a, jw = mk()
        jw.add(e_slot(0))
        jw.add(e_slot(-G))
        jw.ck(time_ms=-G)
        res = run(jw, a, vt=0)
        self.assertEqual(res["hard"], [])

    def test_outcome_fields_in_slot(self):
        for key in ("entry_open_ms", "exit_open_ms", "entry_price", "exit_price", "r_bps",
                    "outcome"):
            with self.subTest(key):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_slot(TAU0, **{key: "x"}))
                jw.ck(time_ms=TAU0 + 10)
                res = run(jw, a, vt=TAU0 + G)
                self.assertEqual(res["hard"], ["SLOT_HAS_OUTCOME_FIELDS"])
                self.assertEqual(wheres(res, "SLOT_HAS_OUTCOME_FIELDS"), [2])   # where = line

    def test_duplicate_slot_and_reference(self):
        a, jw = mk()
        jw.add(e_session())                         # 1
        jw.add(e_slot(TAU0))                        # 2 reference
        jw.ck(time_ms=TAU0 + 1000)                  # 3 covers line 2 in time
        jw.add(e_slot(TAU0, status="NONE"))         # 4 duplicate
        jw.add(e_slot(TAU0))                        # 5 duplicate
        jw.ck(time_ms=TAU0 + D + 10 ** 6)           # 6 late; would cover a reference at 4 or 5
        res = run(jw, a, vt=TAU0 + 2 * D)
        self.assertEqual(res["hard"], ["DUPLICATE_SLOT"])
        self.assertEqual(wheres(res, "DUPLICATE_SLOT"), [4, 5])         # where = line of each later SLOT
        self.assertEqual(res["slots"], {TAU0: "OK"})
        self.assertEqual(res["soft"], [])

    def test_bad_event_slot_is_not_a_duplicate(self):
        a, jw = mk()
        jw.add(e_slot(TAU0))
        jw.add(e_slot(TAU0, status="MAYBE"))
        jw.ck(time_ms=TAU0 + 1)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["BAD_EVENT"])


class TestDeadline(unittest.TestCase):
    def one(self, time_ms, res_ms=1, unc=0):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=time_ms, res=res_ms, unc=unc)
        return run(jw, a, vt=10 ** 15)

    def test_one_below_deadline_is_ok(self):
        res = self.one(TAU0 + D - 1)
        self.assertEqual(res["slots"], {TAU0: "OK"})
        self.assertEqual((res["soft"], res["findings"]), ([], []))

    def test_equal_to_deadline_is_late(self):
        res = self.one(TAU0 + D)
        self.assertEqual(res["slots"], {TAU0: "LATE"})
        self.assertEqual(res["soft"], ["SLOT_LATE_ANCHOR"])
        self.assertEqual(res["hard"], [])
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(wheres(res, "SLOT_LATE_ANCHOR"), [TAU0])

    def test_resolution_and_uncertainty_enter_upper_bound(self):
        # upper = time + res - 1 + unc
        self.assertEqual(self.one(TAU0 + D - 1500, 1000, 500)["slots"], {TAU0: "OK"})
        self.assertEqual(self.one(TAU0 + D - 1499, 1000, 500)["slots"], {TAU0: "LATE"})
        self.assertEqual(self.one(TAU0 + D - 1, 1, 0)["slots"], {TAU0: "OK"})
        self.assertEqual(self.one(TAU0 + D - 2, 1, 1)["slots"], {TAU0: "OK"})
        self.assertEqual(self.one(TAU0 + D - 1, 1, 1)["slots"], {TAU0: "LATE"})
        self.assertEqual(self.one(TAU0 + D - 1, 2, 0)["slots"], {TAU0: "LATE"})

    def test_first_covering_checkpoint_is_used(self):
        a, jw = mk()
        jw.add(e_session())                       # 1
        jw.add(e_slot(TAU0))                      # 2  (i = 2)
        jw.ck(k=1, time_ms=TAU0 + 5)              # 3  anchored_seq 1 < 2: does not cover
        jw.ck(k=3, time_ms=TAU0 + D + 99)         # 4  anchored_seq 3 >= 2: first covering, late
        jw.ck(k=4, time_ms=TAU0 + 5)              # 5  later checkpoint with early time: ignored
        res = run(jw, a, vt=0)
        self.assertEqual(res["hard"], [])
        self.assertEqual(res["slots"], {TAU0: "LATE"})

    def test_anchored_seq_equal_to_slot_line_covers(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))                      # line 2
        jw.ck(k=2, time_ms=TAU0 + 5)              # k == i
        self.assertEqual(run(jw, a)["slots"], {TAU0: "OK"})

    def test_checkpoint_before_slot_does_not_cover(self):
        a, jw = mk()
        jw.add(e_session())
        jw.ck(k=1, time_ms=TAU0)                  # line 2
        jw.add(e_slot(TAU0))                      # line 3
        res = run(jw, a, vt=TAU0 + D)
        self.assertEqual(res["slots"], {TAU0: "UNANCHORED"})

    def test_unanchored_pending_boundary(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        self.assertEqual(run(jw, a, vt=TAU0 + D - 1)["slots"], {TAU0: "PENDING"})
        self.assertEqual(run(jw, a, vt=TAU0 + D - 1)["soft"], [])
        res = run(jw, a, vt=TAU0 + D)
        self.assertEqual(res["slots"], {TAU0: "UNANCHORED"})
        self.assertEqual(res["soft"], ["SLOT_UNANCHORED"])
        self.assertEqual(wheres(res, "SLOT_UNANCHORED"), [TAU0])
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(run(jw, a, vt=10 ** 18)["slots"], {TAU0: "UNANCHORED"})

    def test_unanchored_with_tail_checkpoint_count(self):
        a, jw = clean_journal()
        jw.add(e_slot(TAU0 + 3 * G))              # line 14, no checkpoint afterwards
        res = run(jw, a, vt=TAU0 + 3 * G + D)
        self.assertEqual(res["slots"][TAU0 + 3 * G], "UNANCHORED")
        self.assertEqual(res["soft"], ["SLOT_UNANCHORED"])
        self.assertIn("TAIL_UNANCHORED", names(res))


class TestGrid(unittest.TestCase):
    def slots_journal(self, taus):
        a, jw = mk()
        jw.add(e_session())
        for t in taus:
            jw.add(e_slot(t))
        jw.ck(time_ms=0)
        return a, jw

    def test_missing_points(self):
        a, jw = self.slots_journal([TAU0, TAU0 + 3 * G])
        res = run(jw, a, vt=0)
        self.assertEqual(res["missing"], [TAU0 + G, TAU0 + 2 * G])
        self.assertEqual(res["soft"], ["SLOT_MISSING"])
        self.assertEqual(wheres(res, "SLOT_MISSING"), [TAU0 + G, TAU0 + 2 * G])
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(sorted(res["slots"]), [TAU0, TAU0 + 3 * G])

    def test_unsorted_slots_and_inclusive_tmax(self):
        a, jw = self.slots_journal([TAU0 + 2 * G, TAU0])
        res = run(jw, a, vt=0)
        self.assertEqual(res["missing"], [TAU0 + G])

    def test_off_grid_slots_ignored_for_range(self):
        a, jw = self.slots_journal([TAU0, TAU0 + G, TAU0 + 10 * G + 7, TAU0 - 5 * G + 3])
        res = run(jw, a, vt=0)
        self.assertEqual(res["missing"], [])
        self.assertEqual(res["hard"], ["SLOT_OFF_GRID"])

    def test_single_slot_no_missing(self):
        a, jw = self.slots_journal([TAU0])
        self.assertEqual(run(jw, a)["missing"], [])

    def test_no_slots(self):
        a, jw = self.slots_journal([])
        res = run(jw, a)
        self.assertEqual((res["slots"], res["missing"]), ({}, []))

    def test_duplicates_dont_hide_or_create_missing(self):
        a, jw = self.slots_journal([TAU0, TAU0, TAU0 + 2 * G])
        res = run(jw, a)
        self.assertEqual(res["missing"], [TAU0 + G])
        self.assertEqual(res["hard"], ["DUPLICATE_SLOT"])


class TestOutcomes(unittest.TestCase):
    def scn(self, outcomes, candles="both", ck_between=True, ck_k_offset=0, tail_ck=True,
            tau=TAU0, entry="100.5", exit_="101.5"):
        a, jw = mk()
        jw.add(e_session())                                    # 1
        i = jw.add(e_slot(tau))                                # 2
        if ck_between:
            jw.ck(k=i + ck_k_offset, time_ms=tau + 1000)       # 3
        if candles == "both":
            jw.add(e_candle(tau + D, entry))                   # 4
            jw.add(e_candle(tau + D + H, exit_))               # 5
        for ev in outcomes:
            jw.add(ev)                                         # 6...
        if tail_ck:
            jw.ck(time_ms=tau + 2000)
        return a, jw

    def go(self, outcomes, **kw):
        a, jw = self.scn(outcomes, **kw)
        return run(jw, a, vt=TAU0 + 10 * G)

    def test_eval_ok(self):
        res = self.go([e_outcome(TAU0)])
        self.assertEqual(res["findings"], [], res["findings"])
        self.assertEqual(res["verdict"], "PASS")

    def test_eval_ok_negative_return(self):
        res = self.go([e_outcome(TAU0, "101.5", "100.5")], entry="101.5", exit_="100.5")
        self.assertEqual(res["findings"], [])

    def test_no_price_has_no_further_checks(self):
        res = self.go([{"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"}], candles="none")
        self.assertEqual(res["findings"], [])

    def test_outcome_for_none_slot_is_hard(self):
        a, jw = mk()
        jw.add(e_session())
        i = jw.add(e_slot(TAU0, status="NONE", reasons=["N_TOTAL"], N_total=0,
                          N_BUY=0, N_SELL=0, side=0, sumW_BUY="0", sumW_SELL="0",
                          n_messages=0, X_sn=None))
        jw.ck(k=i, time_ms=TAU0 + 1000)
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})
        jw.ck(time_ms=TAU0 + 2000)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["hard"], ["OUTCOME_FOR_NONE_SLOT"])

    def test_no_price_still_checked_for_orphan_and_duplicate(self):
        res = self.go([{"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"},
                       {"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"},
                       {"t": "OUTCOME", "tau_ms": TAU0 + G, "status": "NO_PRICE"}], candles="none")
        self.assertEqual(res["hard"], ["DUPLICATE_OUTCOME", "OUTCOME_ORPHAN"])
        self.assertEqual(wheres(res, "DUPLICATE_OUTCOME"), [5])
        self.assertEqual(wheres(res, "OUTCOME_ORPHAN"), [6])

    def test_duplicate_outcome(self):
        res = self.go([e_outcome(TAU0), e_outcome(TAU0)])
        self.assertEqual(res["hard"], ["DUPLICATE_OUTCOME"])
        self.assertEqual(wheres(res, "DUPLICATE_OUTCOME"), [7])

    def test_orphan_no_slot(self):
        res = self.go([e_outcome(TAU0 + G)])
        self.assertIn("OUTCOME_ORPHAN", res["hard"])
        self.assertEqual(wheres(res, "OUTCOME_ORPHAN"), [6])
        self.assertNotIn("OUTCOME_BEFORE_ANCHOR", res["hard"])   # no reference SLOT exists at all

    def test_orphan_slot_after_outcome(self):
        a, jw = mk()
        jw.add(e_session())                                    # 1
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # 2
        jw.add(e_slot(TAU0))                                   # 3
        jw.ck(time_ms=TAU0 + 5)                                # 4
        res = run(jw, a)
        self.assertIn("OUTCOME_ORPHAN", res["hard"])
        self.assertEqual(wheres(res, "OUTCOME_ORPHAN"), [2])

    def test_before_anchor_no_checkpoint(self):
        res = self.go([e_outcome(TAU0)], ck_between=False)
        self.assertEqual(res["hard"], ["OUTCOME_BEFORE_ANCHOR"])
        self.assertEqual(wheres(res, "OUTCOME_BEFORE_ANCHOR"), [5])

    def test_before_anchor_checkpoint_does_not_reach_slot(self):
        res = self.go([e_outcome(TAU0)], ck_k_offset=-1)       # anchored_seq == i - 1
        self.assertEqual(res["hard"], ["OUTCOME_BEFORE_ANCHOR"])

    def test_before_anchor_checkpoint_only_after_outcome(self):
        # checkpoint comes after the outcome => not 'between'
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.add(e_candle(TAU0 + D))
        jw.add(e_candle(TAU0 + D + H, "101.5"))
        jw.add(e_outcome(TAU0))
        jw.ck(time_ms=TAU0 + 5)                                # covers the slot, but after outcome
        res = run(jw, a)
        self.assertEqual(res["hard"], ["OUTCOME_BEFORE_ANCHOR"])
        self.assertEqual(res["slots"], {TAU0: "OK"})

    def test_before_anchor_ok_when_k_equals_slot_line(self):
        res = self.go([e_outcome(TAU0)], ck_k_offset=0)
        self.assertEqual(res["hard"], [])

    def test_timing(self):
        for label, over in {
            "entry_plus_1": dict(entry_open_ms=TAU0 + D + 1, exit_open_ms=TAU0 + D + 1 + H),
            "entry_minus_1": dict(entry_open_ms=TAU0 + D - 1, exit_open_ms=TAU0 + D - 1 + H),
            "exit_off": dict(exit_open_ms=TAU0 + D + H + 60000),
            "exit_equal_entry": dict(exit_open_ms=TAU0 + D),
            "exit_correct_entry_wrong": dict(entry_open_ms=TAU0, exit_open_ms=TAU0 + D + H),
        }.items():
            with self.subTest(label):
                a, jw = self.scn([e_outcome(TAU0, **over)], candles="none")
                # provide candles for whatever open times the outcome names, to isolate TIMING
                lines_before = len(jw.lines)
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_slot(TAU0))
                jw.ck(time_ms=TAU0 + 1000)
                oo = e_outcome(TAU0, **over)
                jw.add(e_candle(oo["entry_open_ms"], "100.5"))
                if oo["exit_open_ms"] != oo["entry_open_ms"]:
                    jw.add(e_candle(oo["exit_open_ms"], "101.5"))
                else:
                    jw.add(e_candle(oo["exit_open_ms"] + 0, "100.5"))
                jw.add(oo)
                jw.ck(time_ms=TAU0 + 2000)
                res = run(jw, a, vt=0)
                if label == "exit_equal_entry":
                    # entry and exit share one CANDLE (open 100.5) so exit_price 101.5 is unlinked
                    self.assertIn("OUTCOME_TIMING", res["hard"])
                else:
                    self.assertEqual(res["hard"], ["OUTCOME_TIMING"], res["findings"])
                    self.assertEqual(wheres(res, "OUTCOME_TIMING"), [6])
                self.assertGreater(lines_before, 0)

    def test_mismatch_variants(self):
        good = rbps("100.5", "101.5")
        calc = 10000.0 * math.log(101.5 / 100.5)
        for label, rb in {
            "off_by_1e-3": "%.9f" % (calc + 1e-3),
            "off_by_2e-6": "%.9f" % (calc + 2e-6),
            "off_by_minus_2e-6": "%.9f" % (calc - 2e-6),
            "text": "abc",
            "empty": "",
            "nan": "nan",
            "inf": "inf",
            "whitespace": " 1 2 ",
            "wrong_sign": "%.9f" % -calc,
        }.items():
            with self.subTest(label):
                res = self.go([e_outcome(TAU0, r_bps=rb)])
                self.assertEqual(res["hard"], ["OUTCOME_MISMATCH"], res["findings"])
                self.assertEqual(wheres(res, "OUTCOME_MISMATCH"), [6])
        for label, rb in {"exact": good, "within_5e-7": "%.9f" % (calc + 5e-7),
                          "within_minus_5e-7": "%.9f" % (calc - 5e-7)}.items():
            with self.subTest(label):
                self.assertEqual(self.go([e_outcome(TAU0, r_bps=rb)])["hard"], [])

    def test_mismatch_zero_prices(self):
        for label, kw in {"entry_zero": dict(entry="0", exit_="1.5"),
                          "exit_zero": dict(entry="1.5", exit_="0"),
                          "both_zero": dict(entry="0", exit_="0")}.items():
            with self.subTest(label):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_slot(TAU0))
                jw.ck(time_ms=TAU0 + 1000)
                jw.add(e_candle(TAU0 + D, kw["entry"]))
                jw.add(e_candle(TAU0 + D + H, kw["exit_"]))
                jw.add(e_outcome(TAU0, kw["entry"], kw["exit_"], r_bps="0.0")
                       if False else
                       {"t": "OUTCOME", "tau_ms": TAU0, "status": "EVAL", "entry_open_ms": TAU0 + D,
                        "exit_open_ms": TAU0 + D + H, "entry_price": kw["entry"],
                        "exit_price": kw["exit_"], "r_bps": "0.0"})
                jw.ck(time_ms=TAU0 + 2000)
                res = run(jw, a)
                self.assertEqual(res["hard"], ["OUTCOME_MISMATCH"], res["findings"])

    def test_unlinked_variants(self):
        # (a) no candles at all -> both sides unlinked
        res = self.go([e_outcome(TAU0)], candles="none")
        self.assertEqual(res["hard"], ["OUTCOME_UNLINKED"])
        self.assertEqual(wheres(res, "OUTCOME_UNLINKED"), [4, 4])
        # (b) candle open differs only textually: string comparison
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=TAU0 + 1000)
        jw.add(e_candle(TAU0 + D, "100.50"))
        jw.add(e_candle(TAU0 + D + H, "101.5"))
        jw.add(e_outcome(TAU0))
        jw.ck(time_ms=TAU0 + 2000)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["OUTCOME_UNLINKED"])
        self.assertEqual(wheres(res, "OUTCOME_UNLINKED"), [6])
        # (c) candles exist but only after the outcome line
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=TAU0 + 1000)
        jw.add(e_outcome(TAU0))                                # 4
        jw.add(e_candle(TAU0 + D, "100.5"))
        jw.add(e_candle(TAU0 + D + H, "101.5"))
        jw.ck(time_ms=TAU0 + 2000)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["OUTCOME_UNLINKED"])
        # (d) only the exit candle missing
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=TAU0 + 1000)
        jw.add(e_candle(TAU0 + D, "100.5"))
        jw.add(e_outcome(TAU0))
        jw.ck(time_ms=TAU0 + 2000)
        res = run(jw, a)
        self.assertEqual(res["hard"], ["OUTCOME_UNLINKED"])
        self.assertEqual(len(wheres(res, "OUTCOME_UNLINKED")), 1)

    def test_first_candle_decides_link(self):
        for first, second, expect_unlinked in (("100.5", "100.6", False), ("100.6", "100.5", True)):
            with self.subTest(first=first):
                a, jw = mk()
                jw.add(e_session())
                jw.add(e_slot(TAU0))
                jw.ck(time_ms=TAU0 + 1000)
                jw.add(e_candle(TAU0 + D, first))
                jw.add(e_candle(TAU0 + D, second))
                jw.add(e_candle(TAU0 + D + H, "101.5"))
                jw.add(e_outcome(TAU0))
                jw.ck(time_ms=TAU0 + 2000)
                res = run(jw, a)
                want = ["CANDLE_CONFLICT"] + (["OUTCOME_UNLINKED"] if expect_unlinked else [])
                self.assertEqual(res["hard"], sorted(want), res["findings"])

    def test_candle_conflict_once_per_open_time(self):
        a, jw = mk()
        jw.add(e_candle(TAU0, "1"))
        jw.add(e_candle(TAU0, "2"))
        jw.add(e_candle(TAU0, "3"))
        jw.add(e_candle(TAU0, "1"))
        jw.add(e_candle(TAU0 + 1, "5"))
        jw.add(e_candle(TAU0 + 1, "5"))     # identical open: no conflict
        jw.add(e_candle(TAU0 + 2, "7"))
        jw.add(e_candle(TAU0 + 2, "8"))
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CANDLE_CONFLICT"])
        self.assertEqual(len(wheres(res, "CANDLE_CONFLICT")), 2)

    def test_candle_not_live_boundary(self):
        a, jw = mk()
        jw.add(e_candle(TAU0, "1", recv=TAU0 - 1))      # 1: not live
        jw.add(e_candle(TAU0 + 1, "1", recv=TAU0 + 1))  # 2: recv == open_time: fine
        jw.add(e_candle(TAU0 + 2, "1", recv=TAU0 + 3))  # 3: fine
        res = run(jw, a)
        self.assertEqual(res["hard"], ["CANDLE_NOT_LIVE"])
        self.assertEqual(wheres(res, "CANDLE_NOT_LIVE"), [1])

    def test_duplicate_outcome_still_gets_other_checks(self):
        res = self.go([e_outcome(TAU0), e_outcome(TAU0, r_bps="999")])
        self.assertEqual(res["hard"], ["DUPLICATE_OUTCOME", "OUTCOME_MISMATCH"])


def _canon_line(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


class TestOutcomeCoverageR4(unittest.TestCase):
    """r4 integrator-added tests (contract 6.4; GPT audit orders 1 and 4): the independent author's own suite did not contain them."""

    def build(self, final_ck, dup=False, eval_=False):
        a, jw = mk()
        jw.add(e_session())                                    # 1
        jw.add(e_slot(TAU0))                                   # 2
        jw.ck(time_ms=TAU0 + 5)                                # 3 covers the SLOT
        if eval_:
            jw.add(e_candle(TAU0 + D, "100.5"))                # 4
            jw.add(e_candle(TAU0 + D + H, "101.5"))            # 5
            jw.add(e_outcome(TAU0))                            # 6
        else:
            jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # 4
        if dup:
            jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})
        if final_ck:
            jw.ck(time_ms=TAU0 + 9)
        return a, jw

    def test_covered(self):
        a, jw = self.build(True)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual((res["verdict"], res["hard"], res["soft"], res["outcomes"]), ("PASS", [], [], {TAU0: "COVERED"}))

    def test_uncovered_tail(self):
        a, jw = self.build(False)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual((res["verdict"], res["hard"], res["soft"], res["outcomes"]), ("PASS", [], ["OUTCOME_UNCOVERED"], {TAU0: "UNCOVERED"}))
        self.assertEqual(wheres(res, "OUTCOME_UNCOVERED"), [TAU0])

    def test_duplicate_outcome_is_not_entered_twice(self):
        a, jw = self.build(True, dup=True)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["hard"], ["DUPLICATE_OUTCOME"])
        self.assertEqual(res["outcomes"], {TAU0: "COVERED"})
        self.assertEqual(sum(1 for f in res["findings"] if f[0] == "OUTCOME_UNCOVERED"), 0)

    def test_checkpoint_before_the_outcome_does_not_cover_it(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=TAU0 + 5)                                # line 3, anchored_seq 2
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # line 4
        jw.add({"t": "PING", "conn_id": 1, "ms": 1})           # line 5, no checkpoint after
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})

    def test_checkpoint_anchoring_an_older_head_does_not_cover_a_later_outcome(self):
        # a checkpoint line AFTER the outcome whose anchored_seq lies BEFORE the outcome line must not cover it (anchored_seq >= j is required)
        a, jw = mk()
        jw.add(e_session())                                    # 1
        jw.add(e_slot(TAU0))                                   # 2
        jw.ck(time_ms=TAU0 + 5)                                # 3 anchors 2
        k_old = 3
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # 4
        jw.ck(k=k_old, time_ms=TAU0 + 9)                       # 5 a valid, later checkpoint that anchors head 3 (< 4): it comes after the outcome but does not cover it
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["hard"], [])
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})

    def test_tampered_outcome_after_its_covering_checkpoint(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\n")[:-1]
        ev = json.loads(lines[5])                              # line 6, the EVAL OUTCOME
        self.assertEqual(ev["t"], "OUTCOME")
        ev["r_bps"] = "999.0"
        lines[5] = _canon_line(ev)
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("HEAD_MISMATCH", res["hard"])
        self.assertIn("OUTCOME_MISMATCH", res["hard"])

    def test_tampered_outcome_that_stays_arithmetically_consistent_is_still_caught_by_the_chain(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\n")[:-1]
        ev = json.loads(lines[5])
        ev["r_bps"] = repr(1e4 * math.log(101.5 / 100.5) + 0.0)   # unchanged value written back
        ev["status"] = "EVAL"
        # change the price pair consistently with a consistent r_bps: candles would no longer link, but the chain alone already differs
        ev["exit_price"], ev["r_bps"] = "102.5", repr(1e4 * math.log(102.5 / 100.5))
        lines[5] = _canon_line(ev)
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("HEAD_MISMATCH", res["hard"])

    def test_omitted_outcome(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\n")[:-1]
        del lines[5]                                           # drop the OUTCOME line; the later checkpoint still anchors the old head
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertTrue({"SEQ_GAP", "HEAD_MISMATCH"} & set(res["hard"]))
        self.assertNotIn(TAU0, res["outcomes"])

    def test_tail_outcome_can_be_replaced_without_a_hard_finding_but_is_flagged_uncovered(self):
        # documented limit 4.4: lines after the last checkpoint are not authenticated; r4 makes the consequence visible per OUTCOME
        a, jw = self.build(False, eval_=True)
        lines = jw.bytes_().split(b"\n")[:-1]
        ev = json.loads(lines[5])
        ev["exit_price"], ev["r_bps"] = "101.0", repr(1e4 * math.log(101.0 / 100.5))   # arithmetically consistent, but no candle has that open
        lines[5] = _canon_line(ev)
        res = run(b"\n".join(lines) + b"\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})
        self.assertIn("OUTCOME_UNCOVERED", res["soft"])


class ZA_ReplayMarkers(unittest.TestCase):
    """r5, contract 7.6: this verifier has no SLOT replay, so it must never look like a complete verification."""

    def test_clean_journal_is_incomplete_not_pass(self):
        a, jw = clean_journal()
        res = run_raw(jw, a, vt=TAU0 + 2 * G + D + 1)
        self.assertEqual(res["verdict"], "INCOMPLETE")
        self.assertEqual(res["hard"], ["REPLAY_NOT_RUN"])
        self.assertEqual([f[:2] for f in res["findings"]], [["REPLAY_NOT_RUN", 0]])
        self.assertIs(res["replayed"], False)
        self.assertIs(res["analysis_eligible"], False)
        self.assertEqual(res["soft"], [])

    def test_tampered_journal_is_fail_and_still_lists_replay_not_run(self):
        a, jw = clean_journal()
        lines = jw.bytes_().split(b"\n")[:-1]
        lines[3] = lines[3].replace(b'"N_total":3', b'"N_total":4')
        res = run_raw(b"\n".join(lines) + b"\n", a, vt=TAU0 + 2 * G + D + 1)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("REPLAY_NOT_RUN", res["hard"])
        self.assertGreater(len(res["hard"]), 1)
        self.assertIs(res["analysis_eligible"], False)

    def test_there_is_no_way_to_enable_a_replay(self):
        self.assertEqual(list(inspect.signature(verify).parameters), ["path", "anchor", "journal_id", "verify_time_ms"])

    def test_replay_not_run_is_a_hard_name(self):
        self.assertIn("REPLAY_NOT_RUN", verify_indep.HARD_NAMES)


class ZZ_Coverage(unittest.TestCase):
    def test_every_finding_name_was_observed(self):
        missing = sorted(ALL_81 - SEEN)
        self.assertEqual(missing, [], "finding names never produced by any test: %s" % missing)
        self.assertEqual(verify_indep.HARD_NAMES | verify_indep.SOFT_NAMES | verify_indep.INFO_NAMES
                         >= ALL_81, True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
