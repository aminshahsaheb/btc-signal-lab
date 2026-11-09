#!/usr/bin/env python3
"""Own tests for replay_indep.py.  Run:  cd out && python3 -I test_replay_indep.py

All expected values below were derived BY HAND from the written specifications
(JOURNAL_CONTRACT_v2_r4draft.md section 7 / 1-2, 07_MESSAGE_CONTRACT_v1.md, protocol
section 4, messages.jsonl labels); the derivation is in the comment above each case.
They were NOT produced by running replay_indep.py.

Tests whose name contains KNOWN_AMBIGUOUS encode a reading that the specification does
not force (see SPEC_NOTES.md); they pass under the reading chosen there.

HOW THE HAND-BUILT JOURNALS ARE CONSTRUCTED
    Every event gets seq = its line number, a dummy rec_ms, and (MSG) the true sha256.
    No hash chain / checkpoint / anchor is written: replay_indep.py does not verify them,
    it only applies the validity rule of 1.3 + 2.1 (see its module docstring).
    TAU = 124514 * 14_400_000 = 1_793_001_600_000 (on the 4 h grid, inside the E range).
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import replay_indep as R  # noqa: E402

SPEC_DIR = os.path.join(HERE, "..", "spec")

G = 14_400_000
TAU = 124514 * G
REC = TAU + 20_000
LK = ("MALFORMED", "NO_PRIMARY", "NON_PRIMARY", "OUT_OF_WINDOW", "LATE", "INELIGIBLE", "COUNTED")
FIELDS13 = ("status", "reasons", "primary_conn", "N_total", "N_BUY", "N_SELL", "sumW_BUY",
            "sumW_SELL", "side", "malformed_voids", "ledger", "n_messages", "X_sn")
LABEL_DIFFS = []          # informational: reason labels that differ from the fixture file


# ----------------------------------------------------------------------------- builders
def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def frame(E, S="BUY", z="1", ap="1", X="FILLED", T=None, top=None, drop_T=False):
    o = {"s": "BTCUSDT", "S": S, "o": "LIMIT", "f": "IOC", "q": "0.001", "p": "1", "ap": ap,
         "X": X, "l": z, "z": z, "T": (E if T is None else T)}
    if drop_T:
        del o["T"]
    d = {"e": "forceOrder", "E": E, "o": o}
    if top:
        d.update(top)
    return json.dumps(d, separators=(",", ":")).encode()


GARBAGE = b"{"            # not JSON -> MALFORMED, no readable E


def canon(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


def loose(d):
    return json.dumps(d).encode()          # default separators, insertion order (NOT canonical)


class J(object):
    """Hand-built journal.  Items are dicts (serialised at write time) or raw bytes."""

    def __init__(self):
        self.items = []

    def raw(self, b):
        self.items.append(b)
        return len(self.items)                         # 1-based line number

    def ev(self, d):
        d = dict(d)
        d.setdefault("seq", len(self.items) + 1)
        self.items.append(d)
        return len(self.items)

    def conn(self, cid, ev, ms):
        return self.ev({"t": "CONN", "conn_id": cid, "ev": ev, "ms": ms, "rec_ms": ms})

    def ping(self, cid, ms):
        return self.ev({"t": "PING", "conn_id": cid, "ms": ms, "rec_ms": ms})

    def msg(self, cid, recv, raw):
        return self.ev({"t": "MSG", "conn_id": cid, "recv_ms": recv, "raw_b64": b64(raw),
                        "sha256": sha(raw), "rec_ms": recv})

    def clock(self, off, ms=1):
        return self.ev({"t": "CLOCK", "offset_ms": off, "ms": ms, "rec_ms": ms})

    def slot(self, tau, rec, expected, **extra):
        d = {"t": "SLOT", "tau_ms": tau, "rec_ms": rec}
        d.update(expected)
        d.update(extra)
        return self.ev(d)

    def write(self, dirpath, name, ser=canon, eol=b""):
        data = b""
        for it in self.items:
            data += (it if isinstance(it, bytes) else ser(it)) + eol + b"\n"
        p = os.path.join(dirpath, name)
        with open(p, "wb") as fh:
            fh.write(data)
        return p


def exp(status="VALID", reasons=(), primary=1, buy=0, sell=0, sb="0", ss="0", side=0,
        voids=0, n=0, x=None, **led):
    ledger = dict.fromkeys(LK, 0)
    for k, v in led.items():
        assert k in ledger, k
        ledger[k] = v
    return {"status": status, "reasons": list(reasons), "primary_conn": primary,
            "N_total": buy + sell, "N_BUY": buy, "N_SELL": sell, "sumW_BUY": sb,
            "sumW_SELL": ss, "side": side, "malformed_voids": voids, "ledger": ledger,
            "n_messages": n, "X_sn": x}


def base_valid(n=5, **led):
    """five BUY messages z=1 ap=1 counted -> N=5, sumBUY 5, sumSELL 0, X=(5-0)/5=1.0, side 1"""
    led.setdefault("COUNTED", 5)
    return exp(buy=5, sb="5", side=1, n=n, x="1.0", **led)


def add_healthy(j, cid=1, tau=TAU, open_ms=None):
    """open at tau-1_000_000 (before V), a PING every 100_000 ms from tau-900_000 to tau."""
    j.conn(cid, "open", tau - 1_000_000 if open_ms is None else open_ms)
    t = tau - 900_000
    while t <= tau:
        j.ping(cid, t)
        t += 100_000


def add_std(j, cid=1, tau=TAU, n=5, side="BUY", z="1", ap="1"):
    """n eligible messages inside W, on time: E = tau-100_000-1000*i, recv = E+50."""
    for i in range(n):
        E = tau - 100_000 - 1000 * i
        j.msg(cid, E + 50, frame(E, S=side, z=z, ap=ap))


class Base(unittest.TestCase):
    _counter = 0

    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory(dir=HERE, prefix="_tmp_")
        cls.tmp = cls._td.name

    @classmethod
    def tearDownClass(cls):
        cls._td.cleanup()

    def write(self, j, **kw):
        Base._counter += 1
        return j.write(self.tmp, "j%06d.jsonl" % Base._counter, **kw)

    def assertReplay(self, j, expected, **kw):
        """replayed fields (and the journalled copy) equal the hand-derived `expected` list
        and check_journal reports no SLOT_MISMATCH."""
        p = self.write(j, **kw)
        res = R.replay_journal(p)
        self.assertEqual(len(res), len(expected))
        for r, e in zip(res, expected):
            self.assertEqual(r["fields"], e)
            self.assertEqual(r["journalled"], e)
        self.assertEqual([f for f in R.check_journal(p) if f[0] == "SLOT_MISMATCH"], [])
        return res, p


# ----------------------------------------------------------------------------- 1. fixtures
with open(os.path.join(SPEC_DIR, "messages.jsonl"), "rb") as _fh:
    FIX = [json.loads(line) for line in _fh if line.strip()]


class TestFixtures(unittest.TestCase):
    def test_fixture_file_inventory(self):
        # 07_MESSAGE_CONTRACT: 93 frames = 8 ELIGIBLE + 8 INELIGIBLE + 77 MALFORMED
        self.assertEqual(len(FIX), 93)
        cnt = {}
        for r in FIX:
            cnt[r["expect_class"]] = cnt.get(r["expect_class"], 0) + 1
        self.assertEqual(cnt, {"ELIGIBLE": 8, "INELIGIBLE": 8, "MALFORMED": 77})


def _make_fixture_test(rec):
    def t(self):
        raw = base64.b64decode(rec["raw_b64"])
        cls, reason = R.classify_frame(raw)
        self.assertEqual(cls, rec["expect_class"], "fixture %s" % rec["id"])
        if (reason or None) != (rec["expect_reason"] or None):
            LABEL_DIFFS.append((rec["id"], reason, rec["expect_reason"]))
    return t


for _i, _rec in enumerate(FIX):
    setattr(TestFixtures, "test_fixture_%03d_%s" % (_i, _rec["id"]), _make_fixture_test(_rec))


# ----------------------------------------------------------------------------- 2. classifier
class TestClassifier(unittest.TestCase):
    def cls(self, raw):
        return R.classify_frame(raw)[0]

    def test_baseline_eligible(self):
        self.assertEqual(self.cls(frame(TAU)), "ELIGIBLE")

    def test_st_must_be_json_integer_1(self):
        # 07: "`st` present and not integer 1" -> MALFORMED.  true/1.0/null/"1"/2 are not integer 1.
        base = json.loads(frame(TAU))
        for lit, want in (("1", "ELIGIBLE"), ("true", "MALFORMED"), ("1.0", "MALFORMED"),
                          ("null", "MALFORMED"), ('"1"', "MALFORMED"), ("2", "MALFORMED"),
                          ("1e0", "MALFORMED")):
            raw = frame(TAU)[:-1] + b',"st":' + lit.encode() + b"}"
            self.assertEqual(self.cls(raw), want, lit)
        del base

    def test_E_T_must_be_json_integers_in_range(self):
        # E, T JSON integer within [1_700_000_000_000, 4_102_444_800_000]
        ok = b"1793000000000"
        tmpl = (b'{"e":"forceOrder","E":%s,"o":{"s":"BTCUSDT","S":"BUY","o":"LIMIT","f":"IOC",'
                b'"q":"1","p":"1","ap":"1","X":"FILLED","l":"1","z":"1","T":%s}}')
        cases = [(ok, ok, "ELIGIBLE"),
                 (b"1700000000000", ok, "ELIGIBLE"), (b"1699999999999", ok, "MALFORMED"),
                 (b"4102444800000", ok, "ELIGIBLE"), (b"4102444800001", ok, "MALFORMED"),
                 (ok, b"1700000000000", "ELIGIBLE"), (ok, b"1699999999999", "MALFORMED"),
                 (ok, b"4102444800001", "MALFORMED"),
                 (b"true", ok, "MALFORMED"), (ok, b"true", "MALFORMED"),
                 (b"1793000000000.0", ok, "MALFORMED"), (ok, b"1793000000000.0", "MALFORMED"),
                 (b"1.793e12", ok, "MALFORMED"), (ok, b"1793E9", "MALFORMED"),
                 (b'"1793000000000"', ok, "MALFORMED"), (ok, b"null", "MALFORMED"),
                 (b"-1793000000000", ok, "MALFORMED"), (ok, b"[]", "MALFORMED")]
        for e, t, want in cases:
            self.assertEqual(self.cls(tmpl % (e, t)), want, (e, t))

    def test_decimal_grammar_whole_string_and_30_chars(self):
        # ^(0|[1-9][0-9]*)(\.[0-9]+)?$ ASCII only, whole string, <= 30 chars
        for s, want in (("1", "ELIGIBLE"), ("0.5", "ELIGIBLE"), ("10.250", "ELIGIBLE"),
                        ("1\n", "MALFORMED"), ("1 ", "MALFORMED"), (" 1", "MALFORMED"),
                        ("01", "MALFORMED"), ("00.1", "MALFORMED"), (".5", "MALFORMED"),
                        ("5.", "MALFORMED"), ("1e3", "MALFORMED"), ("-1", "MALFORMED"),
                        ("+1", "MALFORMED"), ("", "MALFORMED"), ("1,5", "MALFORMED"),
                        ("١", "MALFORMED"), ("1" * 30, "ELIGIBLE"), ("1" * 31, "MALFORMED"),
                        ("1." + "1" * 28, "ELIGIBLE"), ("1." + "1" * 29, "MALFORMED")):
            for key in ("q", "p", "ap", "l", "z"):
                raw = frame(TAU)
                d = json.loads(raw)
                d["o"][key] = s
                self.assertEqual(self.cls(json.dumps(d).encode()), want, (key, s))

    def test_ineligible_conditions(self):
        # X != "FILLED" (exact), z = 0, ap = 0 (numerically, so 0.000 too); q, p, l = 0 do not matter
        self.assertEqual(self.cls(frame(TAU, X="NEW")), "INELIGIBLE")
        self.assertEqual(self.cls(frame(TAU, X="filled")), "INELIGIBLE")
        self.assertEqual(self.cls(frame(TAU, z="0")), "INELIGIBLE")
        self.assertEqual(self.cls(frame(TAU, z="0.000")), "INELIGIBLE")
        self.assertEqual(self.cls(frame(TAU, ap="0.0")), "INELIGIBLE")
        self.assertEqual(self.cls(frame(TAU, X="NEW", z="0")), "INELIGIBLE")
        d = json.loads(frame(TAU))
        d["o"]["q"] = d["o"]["p"] = "0"
        d["o"]["l"] = "0.0"
        self.assertEqual(self.cls(json.dumps(d).encode()), "ELIGIBLE")

    def test_malformed_beats_ineligible(self):
        # MALFORMED is applied first (07 table order)
        d = json.loads(frame(TAU, X="NEW", z="0"))
        d["o"]["S"] = "buy"
        self.assertEqual(self.cls(json.dumps(d).encode()), "MALFORMED")

    def test_json_level_rejections(self):
        good = frame(TAU).decode()
        self.assertEqual(self.cls(("﻿" + good).encode()), "MALFORMED")        # BOM
        self.assertEqual(self.cls(b"\xff" + good.encode()), "MALFORMED")           # bad UTF-8
        self.assertEqual(self.cls(good.encode() + b" x"), "MALFORMED")             # trailing garbage
        self.assertEqual(self.cls(good.encode() + b" \n\t\r "), "ELIGIBLE")        # trailing whitespace ok
        self.assertEqual(self.cls(b"\x00" + good.encode()), "MALFORMED")           # NUL
        self.assertEqual(self.cls(b""), "MALFORMED")
        self.assertEqual(self.cls(b"null"), "MALFORMED")
        self.assertEqual(self.cls(b"[" + good.encode() + b"]"), "MALFORMED")
        # duplicate key at a nested level of an extra key
        self.assertEqual(self.cls(frame(TAU)[:-1] + b',"x":{"a":1,"a":2}}'), "MALFORMED")
        # duplicate key through an escape: "e" is "e"
        self.assertEqual(self.cls(frame(TAU)[:-1] + b',"\\u0065":"forceOrder"}'), "MALFORMED")
        # NaN / Infinity / -Infinity constants anywhere
        for c in (b"NaN", b"Infinity", b"-Infinity"):
            self.assertEqual(self.cls(frame(TAU)[:-1] + b',"x":' + c + b"}"), "MALFORMED")
        # a float token in an irrelevant extra key is still valid JSON for a FRAME (only E/T/st
        # are integer-typed): ELIGIBLE
        self.assertEqual(self.cls(frame(TAU)[:-1] + b',"x":1.5}'), "ELIGIBLE")
        # JSON escapes in keys are decoded: "e" instead of "e" is fine when not duplicated
        d = frame(TAU).decode().replace('"e":', '"\\u0065":', 1)
        self.assertEqual(self.cls(d.encode()), "ELIGIBLE")

    def test_deep_nesting_does_not_crash(self):
        raw = b"[" * 200000 + b"]" * 200000
        self.assertEqual(self.cls(raw), "MALFORMED")

    def test_KNOWN_AMBIGUOUS_extra_keys(self):
        # (a) extra non-string key inside `o` is tolerated (fixture valid_extra_key_in_o has x:1);
        #     the literal prose "o.* other than T not a string" could be read as rejecting it.
        d = json.loads(frame(TAU))
        d["o"]["x"] = 1
        self.assertEqual(self.cls(json.dumps(d).encode()), "ELIGIBLE")
        # (b) `st` is only looked at on the top level
        d = json.loads(frame(TAU))
        d["o"]["st"] = 2
        self.assertEqual(self.cls(json.dumps(d).encode()), "ELIGIBLE")

    def test_KNOWN_AMBIGUOUS_exotic_json(self):
        # 5000-digit integer in an irrelevant key: valid JSON, ELIGIBLE (Python 3.11+ int limit worked around)
        self.assertEqual(self.cls(frame(TAU)[:-1] + b',"x":' + b"9" * 5000 + b"}"), "ELIGIBLE")
        # lone surrogate escape in a string value: accepted by Python json, ELIGIBLE here
        self.assertEqual(self.cls(frame(TAU)[:-1] + b',"x":"\\ud800"}'), "ELIGIBLE")

    def test_valid_E_extraction_for_voids(self):
        # (class, reason, E_valid, ...)  E_valid is returned for MALFORMED frames with a parsable body
        c = R._classify(frame(TAU, drop_T=True))
        self.assertEqual((c[0], c[2]), ("MALFORMED", TAU))
        c = R._classify(frame(TAU) + b" x")
        self.assertEqual((c[0], c[2]), ("MALFORMED", None))
        c = R._classify(b'{"e":"forceOrder","E":"%d"}' % TAU)
        self.assertEqual((c[0], c[2]), ("MALFORMED", None))


# ----------------------------------------------------------------------------- 3. replay
class TestWindowAndLate(Base):
    def test_window_edges(self):
        # W = [tau-900000, tau): E=tau-900001 OUT, tau-900000 IN, tau-1 IN, tau OUT.
        # weights: m1 BUY 1*1000 (OUT), m2 SELL 1*3 (IN), m3 BUY 1*3 (IN), m4 SELL 1*1000 (OUT),
        # m5-7 BUY 2*1 (IN).   COUNTED=5 (BUY 4: 3+2+2+2 = 9; SELL 1: 3), X = (9-3)/12 = 0.5
        j = J()
        add_healthy(j)
        j.msg(1, TAU - 899_901, frame(TAU - 900_001, "BUY", "1", "1000"))
        j.msg(1, TAU - 899_900, frame(TAU - 900_000, "SELL", "1", "3"))
        j.msg(1, TAU + 99, frame(TAU - 1, "BUY", "1", "3"))
        j.msg(1, TAU + 100, frame(TAU, "SELL", "1", "1000"))
        for i in range(3):
            j.msg(1, TAU - 499_000 + i, frame(TAU - 500_000, "BUY", "2", "1"))
        e = exp(buy=4, sell=1, sb="9", ss="3", side=1, n=7, x="0.5", OUT_OF_WINDOW=2, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_late_edges(self):
        # recv <= tau+10000 counted; tau+10001 LATE.  An out-of-window late frame is OUT_OF_WINDOW
        # (priority), an in-window late INELIGIBLE frame is LATE (priority over INELIGIBLE).
        # counted: a + 4 std = 5 BUY, X = 5/5 = 1.0.  n = 1+1+1+4+1 = 8
        j = J()
        add_healthy(j)
        j.msg(1, TAU + 10_000, frame(TAU - 10, "BUY", "1", "1"))          # a COUNTED
        j.msg(1, TAU + 10_001, frame(TAU - 10, "SELL", "1", "7"))         # b LATE
        j.msg(1, TAU + 10_001, frame(TAU + 1, "BUY", "1", "9"))           # c OUT_OF_WINDOW
        for i in range(4):
            j.msg(1, TAU - 19, frame(TAU - 20, "BUY", "1", "1"))          # d COUNTED
        j.msg(1, TAU + 10_002, frame(TAU - 30, "BUY", "1", "1", X="NEW"))  # e LATE
        e = exp(buy=5, sb="5", side=1, n=8, x="1.0", LATE=2, OUT_OF_WINDOW=1, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_ineligible_not_counted_and_do_not_void(self):
        # 4 INELIGIBLE (X=NEW, z=0, ap=0.0, X=filled) + 5 COUNTED -> VALID, no void
        j = J()
        add_healthy(j)
        add_std(j)
        for k, raw in enumerate((frame(TAU - 7000, X="NEW"), frame(TAU - 7001, z="0"),
                                 frame(TAU - 7002, ap="0.0"), frame(TAU - 7003, X="filled"))):
            j.msg(1, TAU - 6000 + k, raw)
        e = base_valid(n=9, INELIGIBLE=4)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_frames_before_open_still_messages(self):
        # recv has no lower bound: a frame received before the open event is a message,
        # counted if E is in W; it is not a health point.  6 BUY counted -> sums "6", X 1.0
        j = J()
        add_healthy(j)
        add_std(j)
        j.msg(1, TAU - 5_000_000, frame(TAU - 200_000))
        e = exp(buy=6, sb="6", side=1, n=6, x="1.0", COUNTED=6)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])


def _void_case(kind, value, voids):
    def t(self):
        j = J()
        add_healthy(j)
        add_std(j)
        if kind == "recv":
            j.msg(9, value, GARBAGE)                                   # no readable E
        else:
            j.msg(9, TAU + 500_000, frame(value, drop_T=True))         # valid E, missing o.T
        if voids:
            e = exp(status="NONE", reasons=["MALFORMED"], buy=5, sb="5", side=0, voids=1, n=6,
                    x="1.0", MALFORMED=1, COUNTED=5)
        else:
            e = exp(buy=5, sb="5", side=1, voids=0, n=6, x="1.0", MALFORMED=1, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
    return t


class TestVoidEdges(Base):
    """V = [tau-960000, tau+10000] closed; MALFORMED on a connection WITHOUT open event (conn 9)
    voids too.  Expected: ledger MALFORMED=1 always; malformed_voids per edge."""
    pass


for _kind, _val, _v in (("recv", TAU - 960_001, 0), ("recv", TAU - 960_000, 1),
                        ("recv", TAU + 10_000, 1), ("recv", TAU + 10_001, 0),
                        ("E", TAU - 960_001, 0), ("E", TAU - 960_000, 1),
                        ("E", TAU + 10_000, 1), ("E", TAU + 10_001, 0)):
    setattr(TestVoidEdges, "test_void_%s_%s%d" % (_kind, "m" if _val < TAU else "p", abs(_val - TAU)),
            _void_case(_kind, _val, _v))


class TestVoidMisc(Base):
    def test_E_not_valid_means_only_recv_counts(self):
        # E as a JSON string (numerically inside V) is not a valid E: recv outside V -> no void
        j = J()
        add_healthy(j)
        add_std(j)
        raw = b'{"e":"forceOrder","E":"%d"}' % (TAU - 100)
        j.msg(9, TAU + 500_000, raw)
        e = base_valid(n=6, MALFORMED=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_malformed_with_valid_E_other_defect_voids(self):
        # event type wrong but E readable and inside V (E-only void): voids=1
        j = J()
        add_healthy(j)
        add_std(j)
        d = json.loads(frame(TAU - 5))
        d["e"] = "other"
        j.msg(9, TAU + 500_000, json.dumps(d).encode())
        e = exp(status="NONE", reasons=["MALFORMED"], buy=5, sb="5", side=0, voids=1, n=6,
                x="1.0", MALFORMED=1, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_KNOWN_AMBIGUOUS_no_E_when_body_does_not_parse(self):
        # duplicate key => whole frame is not JSON => no readable E => only recv (outside V) counts
        j = J()
        add_healthy(j)
        add_std(j)
        raw = frame(TAU - 5)[:-1] + b',"E":%d}' % (TAU - 5)
        j.msg(9, TAU + 500_000, raw)
        e = base_valid(n=6, MALFORMED=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_several_malformed_each_counted_once(self):
        # recv in V AND E in V is still ONE void per message: 3 malformed messages -> voids=3
        j = J()
        add_healthy(j)
        add_std(j)
        for k in range(3):
            j.msg(1, TAU - 50 + k, frame(TAU - 50, drop_T=True))
        e = exp(status="NONE", reasons=["MALFORMED"], buy=5, sb="5", side=0, voids=3, n=8,
                x="1.0", MALFORMED=3, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])


class TestHealth(Base):
    def gap_case(self, open_ms, pings, healthy, rec=REC, cid=1, extra=None):
        j = J()
        j.conn(cid, "open", open_ms)
        for t in pings:
            j.ping(cid, t)
        if extra:
            extra(j)
        e = (exp(status="NONE", reasons=["N_TOTAL"], primary=cid) if healthy
             else exp(status="NONE", reasons=["GAP"], primary=None))
        j.slot(TAU, rec, e)
        self.assertReplay(j, [e])

    def test_gap_exactly_200000_bridged(self):
        # open TAU-1_000_000, every step exactly 200_000 -> one run, healthy
        self.gap_case(TAU - 1_000_000, [TAU - 800_000, TAU - 600_000, TAU - 400_000,
                                        TAU - 200_000, TAU], True)

    def test_gap_200001_breaks(self):
        # one step of 200_001 -> two runs; run1 ends TAU-400000 (< V end), run2 starts inside V
        self.gap_case(TAU - 1_000_000, [TAU - 800_000, TAU - 600_000, TAU - 399_999,
                                        TAU - 200_000, TAU], False)

    def test_gap_200001_at_start(self):
        self.gap_case(TAU - 1_000_000, [TAU - 799_999, TAU - 700_000, TAU - 600_000, TAU - 400_000,
                                        TAU - 200_000, TAU], False)

    def test_run_must_reach_end_of_V_edge_ok(self):
        # last frame p=TAU-190000: p+200000 = TAU+10000 >= V end -> healthy
        self.gap_case(TAU - 1_000_000, [TAU - 810_000, TAU - 620_000, TAU - 430_000,
                                        TAU - 240_000, TAU - 190_000], True)

    def test_run_must_reach_end_of_V_edge_fail(self):
        # last frame p=TAU-190001: p+200000 = TAU+9999 < V end -> unhealthy
        self.gap_case(TAU - 1_000_000, [TAU - 810_000, TAU - 620_000, TAU - 430_000,
                                        TAU - 240_000, TAU - 190_001], False)

    def test_open_at_V_start_ok(self):
        pings = [TAU - 860_000 + 100_000 * k for k in range(9)]      # to TAU-60000
        self.gap_case(TAU - 960_000, pings, True)

    def test_open_after_V_start_fails(self):
        pings = [TAU - 860_000 + 100_000 * k for k in range(9)]
        self.gap_case(TAU - 959_999, pings, False)

    def test_open_without_any_frame_unhealthy(self):
        self.gap_case(TAU - 1_000_000, [], False)

    def test_runs_not_stitched_gap_inside_V(self):
        # open TAU-1_200_000, ping TAU-1_100_000, then a 300_000 gap, run 2 starts TAU-800_000 (inside V)
        pings = [TAU - 1_100_000] + [TAU - 800_000 + 100_000 * k for k in range(9)]
        self.gap_case(TAU - 1_200_000, pings, False)

    def test_KNOWN_AMBIGUOUS_gap_before_V_start_does_not_matter(self):
        # a >200000 gap BEFORE V; run 2 starts at TAU-1_000_000 <= V start and covers V -> healthy
        pings = [TAU - 1_300_000, TAU - 1_000_000] + [TAU - 900_000 + 100_000 * k for k in range(10)]
        self.gap_case(TAU - 1_400_000, pings, True)

    def test_KNOWN_AMBIGUOUS_gap_straddling_end_of_V(self):
        # rec = TAU+300000 so frames up to there are seen.  Frames: ..., TAU-100000, then TAU+150000
        # (gap 250000).  7.5b: run1 covers up to TAU+100000 >= V end -> healthy.
        pings = [TAU - 900_000 + 100_000 * k for k in range(9)] + [TAU + 150_000]
        self.gap_case(TAU - 1_000_000, pings, True, rec=TAU + 300_000)

    def test_frame_times_msg_and_ping_bridge_but_not_clock_or_close(self):
        # open TAU-1_000_000.  MSG frames at the same step also bridge:
        j = J()
        j.conn(1, "open", TAU - 1_000_000)
        for k, t in enumerate([TAU - 800_000, TAU - 600_000, TAU - 400_000, TAU - 200_000, TAU]):
            j.msg(1, t, frame(TAU - 100_000 - k))            # MSG frame times are frame times
        e = exp(buy=5, sb="5", side=1, n=5, x="1.0", COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        # CLOCK event in the middle of a 300000 gap does NOT bridge it; another connection's PING
        # does not either
        j = J()
        j.conn(1, "open", TAU - 1_000_000)
        j.ping(1, TAU - 700_000)
        j.clock(0, TAU - 550_000)
        j.ping(2, TAU - 550_000)
        j.ping(1, TAU - 400_000)
        for t in (TAU - 200_000, TAU):
            j.ping(1, t)
        e = exp(status="NONE", reasons=["GAP"], primary=None)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        # ... and with a PING of conn 1 in the gap it is bridged (steps 150000/150000/..)
        j = J()
        j.conn(1, "open", TAU - 1_000_000)
        for t in (TAU - 850_000, TAU - 700_000, TAU - 550_000, TAU - 400_000, TAU - 200_000, TAU):
            j.ping(1, t)
        e = exp(status="NONE", reasons=["N_TOTAL"], primary=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_frames_after_stop_ignored(self):
        # no close: stop = rec = TAU+20000.  A ping at TAU+500000 (after the SLOT's rec) must not
        # create a point; it also cannot help: healthy anyway thanks to p=TAU.
        self.gap_case(TAU - 1_000_000, [TAU - 900_000 + 100_000 * k for k in range(10)] + [TAU + 500_000],
                      True)


class TestConnections(Base):
    def test_two_conns_smallest_id_is_numeric(self):
        # conns 10 and 9, both healthy -> primary 9 (numeric order, not file/lexical order).
        # conn 10 has 3 SELL (NON_PRIMARY), conn 9 has 5 BUY counted.  n=8
        j = J()
        add_healthy(j, 10)
        add_healthy(j, 9)
        add_std(j, 10, n=3, side="SELL", ap="2")
        add_std(j, 9, n=5)
        e = exp(primary=9, buy=5, sb="5", side=1, n=8, x="1.0", NON_PRIMARY=3, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_smaller_id_unhealthy_larger_wins(self):
        # conn 9 opens at TAU-959999 (after V start) -> unhealthy; conn 10 healthy -> primary 10
        j = J()
        add_healthy(j, 9, open_ms=TAU - 959_999)
        add_healthy(j, 10)
        add_std(j, 9, n=3, side="SELL", ap="2")
        add_std(j, 10, n=5)
        e = exp(primary=10, buy=5, sb="5", side=1, n=8, x="1.0", NON_PRIMARY=3, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_connection_without_open_event_never_candidate(self):
        # conn 3 has frames/pings but no open; conn 4 healthy -> primary 4; sells on conn 4 count
        j = J()
        for t in range(TAU - 1_000_000, TAU + 1, 100_000):
            j.ping(3, t)
        add_std(j, 3, n=5)
        add_healthy(j, 4)
        add_std(j, 4, n=5, side="SELL")
        e = exp(primary=4, sell=5, ss="5", side=-1, n=10, x="-1.0", NON_PRIMARY=5, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_only_connection_without_open_gap(self):
        j = J()
        for t in range(TAU - 1_000_000, TAU + 1, 100_000):
            j.ping(3, t)
        add_std(j, 3, n=5)
        j.conn(3, "close", TAU + 5_000)
        e = exp(status="NONE", reasons=["GAP"], primary=None, n=5, NO_PRIMARY=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_close_before_end_of_V(self):
        # close at TAU+9999 -> stop < V end -> unhealthy (GAP); every message NO_PRIMARY
        j = J()
        add_healthy(j)
        j.conn(1, "close", TAU + 9_999)
        add_std(j)
        e = exp(status="NONE", reasons=["GAP"], primary=None, n=5, NO_PRIMARY=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_KNOWN_AMBIGUOUS_close_exactly_at_V_end_is_healthy(self):
        # 7.5b: stop = TAU+10000, min(p+200000, stop) = TAU+10000 >= TAU+10000 -> healthy;
        # the prose "no close/error" could be read as unhealthy.
        j = J()
        add_healthy(j)
        j.conn(1, "close", TAU + 10_000)
        add_std(j)
        e = base_valid()
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_close_inside_V_other_connection_primary(self):
        j = J()
        add_healthy(j, 1)
        add_healthy(j, 2)
        j.conn(1, "close", TAU - 500_000)
        add_std(j, 1)
        add_std(j, 2, side="SELL")
        e = exp(primary=2, sell=5, ss="5", side=-1, n=10, x="-1.0", NON_PRIMARY=5, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_first_open_wins_not_earliest_ms(self):
        # file order: open@TAU-500000 then open@TAU-1000000 -> FIRST (file order) is used -> unhealthy
        j = J()
        j.conn(1, "open", TAU - 500_000)
        j.conn(1, "open", TAU - 1_000_000)
        for t in range(TAU - 900_000, TAU + 1, 100_000):
            j.ping(1, t)
        e = exp(status="NONE", reasons=["GAP"], primary=None)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        # reversed order: first open at TAU-1000000, a later open (inside V) is ignored -> healthy
        j = J()
        j.conn(1, "open", TAU - 1_000_000)
        j.conn(1, "open", TAU - 500_000)
        for t in range(TAU - 900_000, TAU + 1, 100_000):
            j.ping(1, t)
        e = exp(status="NONE", reasons=["N_TOTAL"], primary=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_last_close_wins_not_latest_ms(self):
        # closes in file order [TAU+50000, TAU-500000]: LAST in file order = TAU-500000 -> unhealthy
        j = J()
        add_healthy(j)
        j.conn(1, "close", TAU + 50_000)
        j.conn(1, "close", TAU - 500_000)
        e = exp(status="NONE", reasons=["GAP"], primary=None)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        # [TAU-500000, TAU+50000]: LAST = TAU+50000 -> stop >= V end, frames cover -> healthy
        j = J()
        add_healthy(j)
        j.conn(1, "close", TAU - 500_000)
        j.conn(1, "close", TAU + 50_000)
        e = exp(status="NONE", reasons=["N_TOTAL"], primary=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_no_primary_ledger_and_reason_order(self):
        # conn 1 opens at TAU-500000 -> GAP.  5 BUY msgs -> NO_PRIMARY; garbage in V -> MALFORMED label
        # (priority over NO_PRIMARY) and void.  N_total=0 -> no N_TOTAL, X_sn null.
        j = J()
        add_healthy(j, open_ms=TAU - 500_000)
        add_std(j)
        j.msg(1, TAU + 5, GARBAGE)
        e = exp(status="NONE", reasons=["GAP", "MALFORMED"], primary=None, voids=1, n=6,
                MALFORMED=1, NO_PRIMARY=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        # same + CLOCK 251 (written before the SLOT): reasons order GAP, CLOCK, MALFORMED
        j = J()
        add_healthy(j, open_ms=TAU - 500_000)
        add_std(j)
        j.msg(1, TAU + 5, GARBAGE)
        j.clock(251)
        e = exp(status="NONE", reasons=["GAP", "CLOCK", "MALFORMED"], primary=None, voids=1, n=6,
                MALFORMED=1, NO_PRIMARY=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_full_ledger_priority(self):
        # conn 1 primary (smallest healthy), conn 2 healthy, conn 9 no open.
        # m1 garbage conn1 recv outside V      -> MALFORMED (no void)
        # m2 conn2 in window                   -> NON_PRIMARY ; m3 conn2 out of window -> NON_PRIMARY
        # m4 conn9 valid                       -> NON_PRIMARY
        # m5 conn1 E=TAU+5                     -> OUT_OF_WINDOW
        # m6 conn1 in window, recv TAU+10001   -> LATE
        # m7 conn1 X=NEW, m8 conn1 z=0         -> INELIGIBLE x2
        # 5 std BUY conn1                      -> COUNTED   total n = 13
        j = J()
        add_healthy(j, 1)
        add_healthy(j, 2)
        j.msg(1, TAU - 2_000_000, GARBAGE)
        j.msg(2, TAU - 4000, frame(TAU - 5000))
        j.msg(2, TAU - 3000, frame(TAU + 5))
        j.msg(9, TAU - 3000, frame(TAU - 5000))
        j.msg(1, TAU - 3000, frame(TAU + 5))
        j.msg(1, TAU + 10_001, frame(TAU - 5000))
        j.msg(1, TAU - 4900, frame(TAU - 5000, X="NEW"))
        j.msg(1, TAU - 4800, frame(TAU - 5000, z="0"))
        add_std(j, 1)
        e = exp(primary=1, buy=5, sb="5", side=1, n=13, x="1.0", MALFORMED=1, NON_PRIMARY=3,
                OUT_OF_WINDOW=1, LATE=1, INELIGIBLE=2, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])


class TestReasons(Base):
    def clock_case(self, offsets, want_clock):
        j = J()
        add_healthy(j)
        add_std(j)
        for o in offsets:
            j.clock(o)
        e = (exp(status="NONE", reasons=["CLOCK"], buy=5, sb="5", side=0, n=5, x="1.0", COUNTED=5)
             if want_clock else base_valid())
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_clock_250_vs_251(self):
        self.clock_case([250], False)
        self.clock_case([251], True)
        self.clock_case([-250], False)
        self.clock_case([-251], True)
        self.clock_case([], False)
        self.clock_case([0], False)

    def test_clock_last_event_wins(self):
        self.clock_case([500, 100], False)
        self.clock_case([100, 500], True)
        self.clock_case([-900, 0, 250], False)

    def test_clock_not_a_frame_time_see_health_tests(self):
        pass  # covered in TestHealth.test_frame_times_msg_and_ping_bridge_but_not_clock_or_close

    def test_n_total_4_vs_5(self):
        # 4 counted BUY -> N_TOTAL, status NONE, side 0, X_sn still journalled (4/4 = 1.0)
        j = J()
        add_healthy(j)
        add_std(j, n=4)
        e = exp(status="NONE", reasons=["N_TOTAL"], buy=4, sb="4", side=0, n=4, x="1.0", COUNTED=4)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])
        j = J()
        add_healthy(j)
        add_std(j, n=5)
        e = base_valid()
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_n_total_ignores_ineligible_late_out_of_window(self):
        j = J()
        add_healthy(j)
        add_std(j, n=4)
        j.msg(1, TAU - 6000, frame(TAU - 7000, X="NEW"))            # INELIGIBLE
        j.msg(1, TAU + 10_001, frame(TAU - 7001))                   # LATE
        j.msg(1, TAU - 5000, frame(TAU + 1))                        # OUT_OF_WINDOW
        e = exp(status="NONE", reasons=["N_TOTAL"], buy=4, sb="4", side=0, n=7, x="1.0",
                INELIGIBLE=1, LATE=1, OUT_OF_WINDOW=1, COUNTED=4)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_zero_with_enough_messages(self):
        # 3 BUY w=2 (z=1,ap=2) = 6, 2 SELL w=3 = 6 -> N=5, equal -> ZERO, X=(6-6)/12 = 0.0, side 0
        j = J()
        add_healthy(j)
        add_std(j, n=3, ap="2")
        for i in range(2):
            E = TAU - 200_000 - 1000 * i
            j.msg(1, E + 50, frame(E, "SELL", "1", "3"))
        e = exp(status="NONE", reasons=["ZERO"], buy=3, sell=2, sb="6", ss="6", side=0, n=5,
                x="0.0", COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_zero_is_numeric_equality_not_text(self):
        # BUY z=1.0 ap=2 x3 -> each 2.0 (one decimal) -> "6.0" ; SELL 3+3 -> "6"; numerically equal -> ZERO
        j = J()
        add_healthy(j)
        add_std(j, n=3, z="1.0", ap="2")
        for i in range(2):
            E = TAU - 200_000 - 1000 * i
            j.msg(1, E + 50, frame(E, "SELL", "1", "3"))
        e = exp(status="NONE", reasons=["ZERO"], buy=3, sell=2, sb="6.0", ss="6", side=0, n=5,
                x="0.0", COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_zero_suppressed_by_n_total(self):
        # 1 BUY w=2 and 1 SELL w=2: N=2 < 5 and equal -> reasons only ["N_TOTAL"], X=0.0
        j = J()
        add_healthy(j)
        add_std(j, n=1, ap="2")
        j.msg(1, TAU - 150_000, frame(TAU - 150_000, "SELL", "1", "2"))
        e = exp(status="NONE", reasons=["N_TOTAL"], buy=1, sell=1, sb="2", ss="2", side=0, n=2,
                x="0.0", COUNTED=2)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_n_total_zero_with_primary(self):
        # healthy primary, no messages: N_TOTAL (N_total=0<5), no ZERO, X_sn null, sums "0"
        j = J()
        add_healthy(j)
        e = exp(status="NONE", reasons=["N_TOTAL"], primary=1)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_reason_order_clock_malformed_ntotal(self):
        # 4 counted BUY, clock -251, malformed (garbage) at TAU-100 inside V (conn 1)
        j = J()
        add_healthy(j)
        add_std(j, n=4)
        j.msg(1, TAU - 100, GARBAGE)
        j.clock(-251)
        e = exp(status="NONE", reasons=["CLOCK", "MALFORMED", "N_TOTAL"], buy=4, sb="4", side=0,
                voids=1, n=5, x="1.0", MALFORMED=1, COUNTED=4)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_reason_order_clock_malformed_zero(self):
        j = J()
        add_healthy(j)
        add_std(j, n=3, ap="2")
        for i in range(2):
            E = TAU - 200_000 - 1000 * i
            j.msg(1, E + 50, frame(E, "SELL", "1", "3"))
        j.msg(1, TAU - 100, GARBAGE)
        j.clock(300)
        e = exp(status="NONE", reasons=["CLOCK", "MALFORMED", "ZERO"], buy=3, sell=2, sb="6",
                ss="6", side=0, voids=1, n=6, x="0.0", MALFORMED=1, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])


class TestDecimalsAndX(Base):
    def test_decimal_text_exponents_preserved(self):
        # BUY: 0.014*98010.50 = 1372.14700 (exp -5); 0.5*3 = 1.5 (exp -1); 1.25*2 = 2.50 (exp -2)
        #      sum exponent = min = -5 -> 1372.14700+1.50000+2.50000 = 1376.14700
        # SELL: 10*0.5 = 5.0 (exp -1); 2*1.250 = 2.500 (exp -3) -> 7.500
        # X = (1376.147-7.5)/(1376.147+7.5) = 1368647/1383647
        j = J()
        add_healthy(j)
        k = [0]

        def m(S, z, ap):
            E = TAU - 100_000 - 1000 * k[0]
            k[0] += 1
            j.msg(1, E + 50, frame(E, S, z, ap))
        m("BUY", "0.014", "98010.50")
        m("BUY", "0.5", "3")
        m("BUY", "1.25", "2")
        m("SELL", "10", "0.5")
        m("SELL", "2", "1.250")
        x = repr(1368647 / 1383647)
        e = exp(buy=3, sell=2, sb="1376.14700", ss="7.500", side=1, n=5, x=x, COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_exact_arithmetic_beyond_28_digits(self):
        # z has 30 digits, ap = 98010.50 -> exact product int(z)*9801050 with 2 decimals; plus four
        # 1*1 (exponent 0).  sum = (int(z)*9801050 + 4*100) with 2 decimals.  Only BUY -> X = 1.0
        z = "123456789012345678901234567890"
        s = str(int(z) * 9801050 + 400)
        want = s[:-2] + "." + s[-2:]
        self.assertGreater(len(s), 28)
        j = J()
        add_healthy(j)
        add_std(j, n=4)
        E = TAU - 300_000
        j.msg(1, E + 50, frame(E, "BUY", z, "98010.50"))
        e = exp(buy=5, sb=want, side=1, n=5, x="1.0", COUNTED=5)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def _xcase(self, buys, sells, want_x, sb, ss, side, status="VALID", reasons=()):
        j = J()
        add_healthy(j)
        k = 0
        for w in buys:
            E = TAU - 100_000 - 1000 * k
            k += 1
            z, ap = (w if isinstance(w, tuple) else ("1", str(w)))
            j.msg(1, E + 50, frame(E, "BUY", z, ap))
        for w in sells:
            E = TAU - 100_000 - 1000 * k
            k += 1
            z, ap = (w if isinstance(w, tuple) else ("1", str(w)))
            j.msg(1, E + 50, frame(E, "SELL", z, ap))
        e = exp(status=status, reasons=reasons, buy=len(buys), sell=len(sells), sb=sb, ss=ss,
                side=side, n=len(buys) + len(sells), x=want_x, COUNTED=len(buys) + len(sells))
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_xsn_repr_values(self):
        # (4-1)/5 = 0.6 ; (1-4)/5 = -0.6 ; (8-4)/12 = 1/3 ; (4-8)/12 = -1/3
        self._xcase([1, 1, 1, 1], [1], "0.6", "4", "1", 1)
        self._xcase([1], [1, 1, 1, 1], "-0.6", "1", "4", -1)
        self._xcase([2, 2, 2, 2], [4], "0.3333333333333333", "8", "4", 1)
        self._xcase([4], [2, 2, 2, 2], "-0.3333333333333333", "4", "8", -1)
        # all one side: 1.0 / -1.0
        self._xcase([1, 1, 1, 1, 1], [], "1.0", "5", "0", 1)
        self._xcase([], [1, 1, 1, 1, 1], "-1.0", "0", "5", -1)

    def test_xsn_repr_7_over_11(self):
        # BUY 3+2+2+2 = 9, SELL 2: X = 7/11; literal checked against exact integer division
        lit = "0.6363636363636364"
        self.assertEqual(float(lit), 7 / 11)
        self._xcase([3, 2, 2, 2], [2], lit, "9", "2", 1)

    def test_xsn_repr_exponent_form(self):
        # BUY 1e20,1,1,1 and SELL 1e20: X = 3/(2e20+3) ~ 1.5e-20 -> repr "1.5e-20"
        big = ("100000000000000000000", "1")
        self.assertEqual(float("1.5e-20"), Fraction(3, 2 * 10 ** 20 + 3).__float__())
        self._xcase([big, 1, 1, 1], [big], "1.5e-20", "100000000000000000003",
                    "100000000000000000000", 1)

    def test_xsn_journalled_when_none_status(self):
        # N_total=2 (<5): NONE/N_TOTAL, but X_sn present: (3-1)/(3+1) = 0.5
        self._xcase([3], [1], "0.5", "3", "1", 0, status="NONE", reasons=["N_TOTAL"])


class TestSlotsAndValidity(Base):
    def test_events_after_slot_ignored_and_duplicate_not_replayed(self):
        j = J()
        add_healthy(j)
        add_std(j)
        e = base_valid()
        j.slot(TAU, REC, e)
        # everything below is AFTER the SLOT line and must not influence it
        add_std(j, n=3)
        j.conn(1, "close", TAU - 500_000)
        j.clock(999)
        j.msg(1, TAU + 1, GARBAGE)
        j.slot(TAU, REC, exp(status="NONE", reasons=["GAP"], primary=None))   # duplicate: not compared
        res, p = self.assertReplay(j, [e])
        self.assertEqual(R.check_journal(p), [])

    def test_two_reference_slots_lines_and_accumulation(self):
        # SLOT1 at TAU (5 BUY in its window); SLOT2 at TAU+G (6 SELL w=2 in its window).
        # SLOT2 sees all 11 earlier messages: the 5 BUY are OUT_OF_WINDOW for it.
        # SLOT2: N_SELL 6, sumSELL 12, sumBUY 0, X=-1.0, side -1
        TAU2 = TAU + G
        j = J()
        add_healthy(j)
        add_std(j)
        e1 = base_valid()
        line1 = j.slot(TAU, REC, e1)
        t = TAU + 100_000
        while t <= TAU2:                                           # 144 pings
            j.ping(1, t)
            t += 100_000
        for i in range(6):
            E = TAU2 - 50_000 - 1000 * i
            j.msg(1, E + 50, frame(E, "SELL", "1", "2"))
        e2 = exp(sell=6, ss="12", side=-1, n=11, x="-1.0", OUT_OF_WINDOW=5, COUNTED=6)
        line2 = j.slot(TAU2, TAU2 + 20_000, e2)
        res, p = self.assertReplay(j, [e1, e2])
        self.assertEqual([(r["line"], r["tau_ms"], r["rec_ms"]) for r in res],
                         [(line1, TAU, REC), (line2, TAU2, TAU2 + 20_000)])
        self.assertEqual(line2 - line1, 144 + 6 + 1)

    def test_off_grid_slot_with_outcome_fields_is_still_replayed(self):
        # SLOT_OFF_GRID / SLOT_HAS_OUTCOME_FIELDS are not section-7 findings; the SLOT is a reference SLOT
        tau = TAU + 123
        j = J()
        add_healthy(j, tau=tau)
        add_std(j, tau=tau)
        e = base_valid()
        j.slot(tau, tau + 20_000, e, r_bps="1", entry_price="1")
        self.assertReplay(j, [e])

    def test_first_valid_slot_is_reference(self):
        # the second SLOT (same tau) has the right values, the first (reference) has wrong ones
        j = J()
        add_healthy(j)
        add_std(j)
        wrong = base_valid()
        wrong["side"] = -1
        l1 = j.slot(TAU, REC, wrong)
        j.slot(TAU, REC, base_valid())
        p = self.write(j)
        res = R.replay_journal(p)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["line"], l1)
        self.assertEqual(R.check_journal(p), [("SLOT_MISMATCH", l1, "side")])

    def _bad_slot_then_good(self, mutate):
        j = J()
        add_healthy(j)
        add_std(j)
        good = base_valid()
        bad = json.loads(json.dumps({"t": "SLOT", "tau_ms": TAU, "rec_ms": REC, **good}))
        mutate(bad)
        j.ev(bad)                                  # invalid (BAD_EVENT) -> not a reference SLOT
        lg = j.slot(TAU, REC, good)
        p = self.write(j)
        res = R.replay_journal(p)
        self.assertEqual([r["line"] for r in res], [lg])
        self.assertEqual(R.check_journal(p), [])

    def test_invalid_slot_events_are_not_slots(self):
        cases = {
            "status lowercase": lambda d: d.__setitem__("status", "valid"),
            "status int": lambda d: d.__setitem__("status", 1),
            "dec leading zero": lambda d: d.__setitem__("sumW_BUY", "05"),
            "dec exponent": lambda d: d.__setitem__("sumW_SELL", "1e3"),
            "dec int": lambda d: d.__setitem__("sumW_SELL", 0),
            "ledger bool": lambda d: d["ledger"].__setitem__("LATE", True),
            "ledger str": lambda d: d["ledger"].__setitem__("LATE", "0"),
            "ledger list": lambda d: d.__setitem__("ledger", []),
            "reasons int item": lambda d: d.__setitem__("reasons", [1]),
            "reasons string": lambda d: d.__setitem__("reasons", "GAP"),
            "primary str": lambda d: d.__setitem__("primary_conn", "1"),
            "primary bool": lambda d: d.__setitem__("primary_conn", True),
            "X_sn missing": lambda d: d.pop("X_sn"),
            "X_sn int": lambda d: d.__setitem__("X_sn", 1),
            "primary_conn missing": lambda d: d.pop("primary_conn"),
            "N_total bool": lambda d: d.__setitem__("N_total", True),
            "side str": lambda d: d.__setitem__("side", "1"),
            "tau missing": lambda d: d.pop("tau_ms"),
            "malformed_voids missing": lambda d: d.pop("malformed_voids"),
            "n_messages null": lambda d: d.__setitem__("n_messages", None),
            "seq missing": lambda d: d.pop("seq", None) or d.__setitem__("seq", None),
            "seq bool": lambda d: d.__setitem__("seq", True),
            "rec_ms bool": lambda d: d.__setitem__("rec_ms", True),
            "t lowercase": lambda d: d.__setitem__("t", "slot"),
        }
        for name, mut in cases.items():
            with self.subTest(name):
                self._bad_slot_then_good(mut)

    def test_valid_but_odd_slot_values_are_valid(self):
        # any int `side`, any strings in reasons / X_sn, extra fields: valid event -> replayed, mismatch reported
        j = J()
        add_healthy(j)
        add_std(j)
        odd = base_valid()
        odd["side"] = 5
        odd["reasons"] = ["WHATEVER"]
        odd["X_sn"] = "garbage"
        odd["extra"] = {"anything": [1, 2]}
        l = j.slot(TAU, REC, odd)
        p = self.write(j)
        self.assertEqual(R.check_journal(p), [("SLOT_MISMATCH", l, "X_sn,reasons,side,status")]
                         if False else R.check_journal(p))
        # status VALID matches; reasons/X_sn/side differ:
        self.assertEqual(R.check_journal(p), [("SLOT_MISMATCH", l, "X_sn,reasons,side")])

    def test_bad_event_other_types_are_excluded_from_replay_input(self):
        j = J()
        add_healthy(j)
        add_std(j)
        for k in range(1, 4):
            j.ping(0, TAU - 1_000_000 + 100_000 * k)
        # conn 0 would be the smallest healthy id if this (invalid) open event were accepted
        j.ev({"t": "CONN", "conn_id": 0, "ev": "OPEN", "ms": TAU - 1_000_000, "rec_ms": 1})
        for t in range(TAU - 600_000, TAU + 1, 100_000):
            j.ping(0, t)
        ok_raw = frame(TAU - 5000)
        base_msg = {"t": "MSG", "conn_id": 1, "recv_ms": TAU - 4000, "raw_b64": b64(ok_raw),
                    "sha256": sha(ok_raw), "rec_ms": 1}

        def variant(**ch):
            d = dict(base_msg)
            for k, v in ch.items():
                if v is KeyError:
                    d.pop(k, None)
                else:
                    d[k] = v
            return d
        j.ev(variant(conn_id=True))                  # bool conn_id
        j.ev(variant(sha256=KeyError))               # missing sha256
        j.ev(variant(recv_ms="5"))                   # string recv_ms
        j.ev(variant(seq=True))                      # bool seq
        j.ev(variant(rec_ms=KeyError))               # missing rec_ms
        j.ev(variant(t="msg"))                       # unknown type
        j.ev(variant(raw_b64=5))                     # raw_b64 not a string
        j.ev({"t": "CLOCK", "offset_ms": 999, "rec_ms": 1})                  # missing ms
        j.ev({"t": "CLOCK", "offset_ms": True, "ms": 1, "rec_ms": 1})        # bool offset
        j.ev({"t": "PING", "conn_id": "1", "ms": TAU, "rec_ms": 1})          # string conn_id
        j.ev({"t": "CONN", "conn_id": 1, "ev": "close", "rec_ms": 1})        # missing ms: close@? ignored
        e = base_valid()
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_seq_and_canonical_form_do_not_matter(self):
        # seq != line number (SEQ_GAP) and non-canonical text (NOT_CANONICAL, CRLF) are still valid events
        j = J()
        add_healthy(j)
        add_std(j)
        for it in j.items:
            it["seq"] = 999
        e = base_valid()
        j.slot(TAU, REC, e)
        j.items[-1]["seq"] = 12345
        res, p = self.assertReplay(j, [e], ser=loose, eol=b"\r")
        self.assertEqual(res[0]["line"], len(j.items))

    def test_hash_mismatch_does_not_exclude_msg(self):
        # a wrong sha256 is RAW_HASH_MISMATCH (not section 7); the decoded bytes are still used
        j = J()
        add_healthy(j)
        add_std(j, n=4)
        raw = frame(TAU - 9000)
        j.ev({"t": "MSG", "conn_id": 1, "recv_ms": TAU - 8000, "raw_b64": b64(raw),
              "sha256": "0" * 64, "rec_ms": 1})
        e = base_valid()
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_KNOWN_AMBIGUOUS_invalid_base64_msg_is_a_malformed_message(self):
        # raw_b64 not decodable: counted in n_messages, labelled MALFORMED; recv outside V -> no void
        j = J()
        add_healthy(j)
        add_std(j)
        j.ev({"t": "MSG", "conn_id": 1, "recv_ms": TAU - 2_000_000, "raw_b64": "!!!!",
              "sha256": "0" * 64, "rec_ms": 1})
        j.ev({"t": "MSG", "conn_id": 1, "recv_ms": TAU - 3_000_000, "raw_b64": "QUJD=",
              "sha256": "0" * 64, "rec_ms": 1})        # bad padding
        e = base_valid(n=7, MALFORMED=2)
        j.slot(TAU, REC, e)
        self.assertReplay(j, [e])

    def test_KNOWN_AMBIGUOUS_dec_with_trailing_newline_is_not_dec(self):
        # the contract regex written with `$` would (in Python re.match) accept "5\n"; whole-string match used
        self._bad_slot_then_good(lambda d: d.__setitem__("sumW_BUY", "5\n"))


class TestEarlyWriteAndMismatch(Base):
    def test_rec_tau_plus_9999_vs_10000(self):
        # rec = tau+9999: early write; no close -> stop = rec < V end -> GAP.  rec = tau+10000: not early, healthy.
        j = J()
        add_healthy(j)
        add_std(j)
        e = exp(status="NONE", reasons=["GAP"], primary=None, n=5, NO_PRIMARY=5)
        line = j.slot(TAU, TAU + 9_999, e)
        res, p = self.assertReplay(j, [e])
        self.assertTrue(res[0]["early_write"])
        self.assertEqual(R.check_journal(p), [("SLOT_EARLY_WRITE", line, "")])
        j = J()
        add_healthy(j)
        add_std(j)
        e = base_valid()
        j.slot(TAU, TAU + 10_000, e)
        res, p = self.assertReplay(j, [e])
        self.assertFalse(res[0]["early_write"])
        self.assertEqual(R.check_journal(p), [])

    def test_early_write_in_addition_to_mismatch(self):
        # journal says healthy/VALID, replay (rec=tau+9999, no close) says GAP.
        # differing fields (hand): N_BUY(0/5) N_total(0/5) X_sn(None/"1.0") ledger primary_conn
        # reasons side(0/1) status sumW_BUY("0"/"5");  same: N_SELL, malformed_voids, n_messages, sumW_SELL
        j = J()
        add_healthy(j)
        add_std(j)
        line = j.slot(TAU, TAU + 9_999, base_valid())
        p = self.write(j)
        self.assertEqual(R.check_journal(p), [
            ("SLOT_MISMATCH", line, "N_BUY,N_total,X_sn,ledger,primary_conn,reasons,side,status,sumW_BUY"),
            ("SLOT_EARLY_WRITE", line, "")])

    def test_KNOWN_AMBIGUOUS_early_slot_with_later_close_stop_is_close_ms(self):
        # 7.5b: stop = close_ms even when later than rec -> healthy although rec = tau+9999
        # (7.2 says the horizon of EVERY connection is rec).  Only EARLY_WRITE is reported.
        j = J()
        add_healthy(j)
        add_std(j)
        j.conn(1, "close", TAU + 50_000)
        e = base_valid()
        line = j.slot(TAU, TAU + 9_999, e)
        p = self.write(j)
        self.assertEqual(R.replay_journal(p)[0]["fields"], e)
        self.assertEqual(R.check_journal(p), [("SLOT_EARLY_WRITE", line, "")])

    def test_mismatch_detail_names_sorted(self):
        base = base_valid()
        j_cases = {
            "sumW_BUY": dict(base, sumW_BUY="5.0"),                       # text, not numeric, comparison
            "X_sn": dict(base, X_sn="1"),
            "primary_conn": dict(base, primary_conn=2),
            "side": dict(base, side=-1),
            "ledger": dict(base, ledger={k: v for k, v in base["ledger"].items() if k != "LATE"}),
            "reasons,status": dict(base, reasons=["N_TOTAL"], status="NONE"),
            "malformed_voids": dict(base, malformed_voids=1),
            "n_messages": dict(base, n_messages=6),
            "N_SELL": dict(base, N_SELL=1),
            "sumW_SELL": dict(base, sumW_SELL="0.0"),
            "N_BUY,N_total": dict(base, N_BUY=4, N_total=4),
        }
        for want, journalled in j_cases.items():
            with self.subTest(want):
                j = J()
                add_healthy(j)
                add_std(j)
                line = j.slot(TAU, REC, journalled)
                p = self.write(j)
                self.assertEqual(R.check_journal(p), [("SLOT_MISMATCH", line, want)])

    def test_mismatch_all_13_fields_sorted(self):
        j = J()
        add_healthy(j)
        add_std(j)
        wrong = {"status": "NONE", "reasons": ["X"], "primary_conn": None, "N_total": 9, "N_BUY": 9,
                 "N_SELL": 9, "sumW_BUY": "9", "sumW_SELL": "9", "side": 0, "malformed_voids": 9,
                 "ledger": {}, "n_messages": 9, "X_sn": None}
        line = j.slot(TAU, REC, wrong)
        p = self.write(j)
        self.assertEqual(R.check_journal(p), [(
            "SLOT_MISMATCH", line,
            "N_BUY,N_SELL,N_total,X_sn,ledger,malformed_voids,n_messages,primary_conn,reasons,"
            "side,status,sumW_BUY,sumW_SELL")])

    def test_reasons_order_matters(self):
        j = J()
        add_healthy(j)
        add_std(j)
        j.msg(1, TAU - 100, GARBAGE)
        j.clock(300)
        right = exp(status="NONE", reasons=["CLOCK", "MALFORMED"], buy=5, sb="5", side=0, voids=1,
                    n=6, x="1.0", MALFORMED=1, COUNTED=5)
        wrong = dict(right, reasons=["MALFORMED", "CLOCK"])
        j2 = J()
        j2.items = list(j.items)
        j.slot(TAU, REC, right)
        l2 = j2.slot(TAU, REC, wrong)
        self.assertEqual(R.check_journal(self.write(j)), [])
        self.assertEqual(R.check_journal(self.write(j2)), [("SLOT_MISMATCH", l2, "reasons")])

    def test_api_shape(self):
        j = J()
        add_healthy(j)
        add_std(j)
        e = base_valid()
        line = j.slot(TAU, REC, e)
        res = R.replay_journal(self.write(j))
        r = res[0]
        self.assertEqual(sorted(r), ["early_write", "fields", "journalled", "line", "rec_ms", "tau_ms"])
        self.assertEqual(sorted(r["fields"]), sorted(FIELDS13))
        self.assertEqual(sorted(r["journalled"]), sorted(FIELDS13))
        self.assertEqual((r["line"], r["tau_ms"], r["rec_ms"], r["early_write"]), (line, TAU, REC, False))
        self.assertIsInstance(r["fields"]["sumW_BUY"], str)
        self.assertIsInstance(r["fields"]["X_sn"], str)
        self.assertIs(type(r["fields"]["N_total"]), int)


class TestFileLevel(Base):
    def _journal_with_slot_then(self, tail_lines):
        j = J()
        add_healthy(j)
        add_std(j)
        e = base_valid()
        l1 = j.slot(TAU, REC, e)
        return j, l1, e

    def test_bad_encoding_stops_parsing(self):
        tau2 = TAU + G
        bad_lines = {
            "float token": b'{"t":"PING","conn_id":1,"ms":1.5,"rec_ms":1,"seq":99}',
            "exponent token": b'{"t":"PING","conn_id":1,"ms":1E5,"rec_ms":1,"seq":99}',
            "duplicate key": b'{"t":"PING","t":"PING","conn_id":1,"ms":1,"rec_ms":1,"seq":99}',
            "nested duplicate": b'{"t":"SESSION","seq":99,"rec_ms":1,"x":{"a":1,"a":2}}',
            "NaN": b'{"t":"SESSION","seq":99,"rec_ms":1,"x":NaN}',
            "Infinity": b'{"t":"SESSION","seq":99,"rec_ms":1,"x":-Infinity}',
            "invalid utf8": b'{"t":"SESSION","seq":99,"rec_ms":1,"x":"\xff"}',
            "empty line": b"",
            "array": b"[]",
            "scalar": b"5",
            "truncated": b'{"t":"SESSION","seq":99',
            "BOM": b"\xef\xbb\xbf" + canon({"t": "SESSION", "seq": 99, "rec_ms": 1}),
        }
        for name, bad in bad_lines.items():
            with self.subTest(name):
                j = J()
                add_healthy(j)
                add_std(j)
                e = base_valid()
                l1 = j.slot(TAU, REC, e)
                j.raw(bad)
                # a second SLOT after the bad line, fully valid, must be ignored
                j.slot(tau2, tau2 + 20_000, exp(status="NONE", reasons=["GAP"], primary=None, n=5,
                                                NO_PRIMARY=5))
                res = R.replay_journal(self.write(j))
                self.assertEqual([r["line"] for r in res], [l1])

    def test_bad_line_before_slot_hides_it(self):
        j = J()
        add_healthy(j)
        j.raw(b"[]")
        j.slot(TAU, REC, base_valid())
        self.assertEqual(R.replay_journal(self.write(j)), [])

    def test_string_values_that_look_like_floats_are_fine(self):
        # only NUMBER tokens are checked: "1.5" / "1e5" inside strings do not trigger BAD_ENCODING
        j = J()
        add_healthy(j)
        add_std(j)
        j.ev({"t": "SESSION", "rec_ms": 1, "note": "1.5e5 NaN Infinity"})
        j.slot(TAU, REC, base_valid())
        self.assertEqual(len(R.replay_journal(self.write(j))), 1)

    def test_partial_last_line_discarded_and_empty_file(self):
        j = J()
        add_healthy(j)
        add_std(j)
        l1 = j.slot(TAU, REC, base_valid())
        p = self.write(j)
        with open(p, "ab") as fh:           # SLOT line without terminating newline -> discarded
            tau2 = TAU + G
            j2 = J()
            j2.items = [None] * (l1)
            j2.slot(tau2, tau2 + 20_000, exp(status="NONE", reasons=["GAP"], primary=None, n=5,
                                             NO_PRIMARY=5))
            fh.write(canon(j2.items[-1]))
        self.assertEqual([r["line"] for r in R.replay_journal(p)], [l1])
        q = os.path.join(self.tmp, "empty.jsonl")
        open(q, "wb").close()
        self.assertEqual(R.replay_journal(q), [])
        self.assertEqual(R.check_journal(q), [])

    def test_journal_without_slots(self):
        j = J()
        add_healthy(j)
        add_std(j)
        self.assertEqual(R.check_journal(self.write(j)), [])

    def test_cli_prints_check_journal_as_json(self):
        j = J()
        add_healthy(j)
        add_std(j)
        line = j.slot(TAU, TAU + 9_999, base_valid())
        p = self.write(j)
        out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "replay_indep.py"), p],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        self.assertEqual(json.loads(out.stdout.decode()), [
            ["SLOT_MISMATCH", line, "N_BUY,N_total,X_sn,ledger,primary_conn,reasons,side,status,sumW_BUY"],
            ["SLOT_EARLY_WRITE", line, ""]])
        j = J()
        add_healthy(j)
        add_std(j)
        j.slot(TAU, REC, base_valid())
        out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "replay_indep.py"), self.write(j)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        self.assertEqual(json.loads(out.stdout.decode()), [])

    def test_KNOWN_AMBIGUOUS_finding_order_and_early_write_detail(self):
        # per SLOT in file order, SLOT_MISMATCH before SLOT_EARLY_WRITE; EARLY_WRITE detail is "" (unspecified)
        j = J()
        add_healthy(j)
        add_std(j)
        a = j.slot(TAU, TAU + 9_999, base_valid())
        tau2 = TAU + G
        b = j.slot(tau2, tau2 + 9_999, exp(status="NONE", reasons=["GAP"], primary=None, n=5, NO_PRIMARY=5))
        got = R.check_journal(self.write(j))
        self.assertEqual([(n, w) for n, w, _ in got],
                         [("SLOT_MISMATCH", a), ("SLOT_EARLY_WRITE", a), ("SLOT_EARLY_WRITE", b)])


class TestScale(Base):
    def test_moderate_size_runs(self):
        # 6000 messages, 40 slots: a smoke test for run time only (no value assertions beyond counts)
        import time
        j = J()
        add_healthy(j)
        t0 = time.time()
        for i in range(6000):
            E = TAU - 800_000 + (i % 700_000)
            j.msg(1, E + 50, frame(E, "BUY" if i % 2 else "SELL", "1", str(1 + i % 7)))
        for k in range(40):
            j.slot(TAU + k * G, TAU + k * G + 20_000, base_valid())
        res = R.replay_journal(self.write(j))
        self.assertEqual(len(res), 40)
        self.assertLess(time.time() - t0, 60)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    amb = []
    for t in unittest.defaultTestLoader.getTestCaseNames(TestClassifier):
        if "KNOWN_AMBIGUOUS" in t:
            amb.append("TestClassifier." + t)
    for cls in (TestVoidMisc, TestHealth, TestConnections, TestSlotsAndValidity,
                TestEarlyWriteAndMismatch, TestFileLevel):
        for t in unittest.defaultTestLoader.getTestCaseNames(cls):
            if "KNOWN_AMBIGUOUS" in t:
                amb.append(cls.__name__ + "." + t)
    print("tests run: %d, failures: %d, errors: %d" % (result.testsRun, len(result.failures),
                                                      len(result.errors)))
    print("KNOWN-AMBIGUOUS tests (pass under the reading chosen in SPEC_NOTES.md): %d" % len(amb))
    for a in amb:
        print("   ", a)
    print("fixture reason-label differences (informational, class is what is contractual): %d" %
          len(LABEL_DIFFS))
    for d in LABEL_DIFFS:
        print("   ", d)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
