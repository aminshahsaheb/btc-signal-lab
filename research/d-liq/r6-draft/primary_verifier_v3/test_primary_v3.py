"""Unit tests of the primary verifier v3 (journal contract v3, r6 text of PR #39 at 53a7a3a; history: first written against 8969b65, which 53a7a3a amends). SYNTHETIC; written by the author of the verifier: NOT independent.

Self-contained: the journals are built here, not read from the conformance vectors (those are run by run_vectors.py against a pinned commit of PR #40).
Several tests are NEGATIVE: they must make the checking machinery fail, otherwise a green run would mean nothing.
Run:  python3 -I -B test_primary_v3.py
"""
import ast
import base64
import contextlib
import hashlib
import io
import json
import math
import itertools
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dliq_journal_verify_v3 as V      # noqa: E402
import dliq_msg_contract_v3 as MC       # noqa: E402
import make_provenance as MP            # noqa: E402
import r6_rules as R6                   # noqa: E402
import run_vectors as RV                # noqa: E402

TAU = 14_400_000 * 124_000
ABSENT = object()


def canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def frame(E, s="BTCUSDT", ps=ABSENT, st=ABSENT, top=None, o_extra=None, o=ABSENT):
    """A forceOrder frame as bytes (compact JSON); None / ABSENT / extra keys let a test build every anomaly of 7.5a."""
    inner = {"S": "BUY", "o": "LIMIT", "f": "IOC", "q": "1", "p": "60000", "ap": "60000", "X": "FILLED", "l": "1", "z": "1", "T": E - 1000}
    if s is not ABSENT:
        inner["s"] = s
    if ps is not ABSENT:
        inner["ps"] = ps
    if st is not ABSENT:
        inner["st"] = st
    inner.update(o_extra or {})
    msg = {"e": "forceOrder", "E": E, "o": inner if o is ABSENT else o}
    msg.update(top or {})
    return json.dumps(msg, separators=(",", ":")).encode("utf-8")


class Journal:
    def __init__(self):
        self.events = []

    def add(self, ev, seq=None):
        line = len(self.events) + 1
        ev = dict(ev)
        ev["seq"] = line if seq is None else seq
        self.events.append(ev)
        return line

    def msg(self, conn, raw, recv_ms, seq=None):
        return self.add({"t": "MSG", "rec_ms": recv_ms, "conn_id": conn, "recv_ms": recv_ms, "raw_b64": base64.b64encode(raw).decode("ascii"),
                         "sha256": hashlib.sha256(raw).hexdigest()}, seq=seq)

    def conn(self, conn, kind, ms, feed="FORCE"):
        ev = {"t": "CONN", "rec_ms": ms, "conn_id": conn, "ev": kind, "ms": ms}
        if feed is not None:
            ev["feed"] = feed
        return self.add(ev)

    def ping(self, conn, ms):
        return self.add({"t": "PING", "rec_ms": ms, "conn_id": conn, "ms": ms})

    def slot(self, n_messages=5, malformed=0, voids=0):
        status = "NONE" if voids else "VALID"
        return self.add({"t": "SLOT", "rec_ms": TAU + 10_000, "tau_ms": TAU, "status": status, "reasons": ["MALFORMED"] if voids else [],
                         "primary_conn": 1, "N_total": 5, "N_BUY": 5, "N_SELL": 0, "side": 0 if voids else 1, "malformed_voids": voids, "n_messages": n_messages,
                         "sumW_BUY": "300000", "sumW_SELL": "0", "X_sn": "1.0",
                         "ledger": {"MALFORMED": malformed, "NO_PRIMARY": 0, "NON_PRIMARY": 0, "OUT_OF_WINDOW": 0, "LATE": 0, "INELIGIBLE": 0, "COUNTED": 5}})

    def write(self, directory, name="journal.jsonl"):
        path = os.path.join(directory, name)
        with open(path, "wb") as fh:
            for ev in self.events:
                fh.write(canon(ev) + b"\n")
        return path


def control(extra=(), malformed=0, voids=0, after_slot=(), kline_first=False, bad_b64=(), trap=()):
    """One FORCE connection (id 1) healthy over V(tau), five BUY messages (weight 60000 each), the SLOT at tau + 10 s, then `after_slot` frames.
    `extra` = frames (bytes) recorded before the SLOT, placed inside V and the feature window.
    `bad_b64` = recv_ms of MSG events whose raw_b64 is not decodable base64 (recorded before the SLOT); the journalled SLOT counts each as MALFORMED and,
    when its recv_ms lies in V(tau) = [tau - 16 min, tau + 10 s], as a malformed void.
    `trap` = (recv_ms, text, intended_bytes) of MSG events whose raw_b64 TEXT is not strict canonical base64 but which a permissive decoder reads as `intended_bytes` (whose sha256 is
    recorded): the same accounting as `bad_b64`. This is the case of GPT's blocking finding of 2026-11-14; `bad_b64` ('abc', incorrect padding) fails in every decoder and does not test it."""
    j = Journal()
    t0 = TAU - 1_000_000
    if kline_first:
        j.conn(0, "open", t0, feed="KLINE")
        for k in range(1, 6):
            j.ping(0, t0 + 200_000 * k)
        j.msg(0, b'{"e":"kline","note":"not a forceOrder frame"}', TAU - 500_000)
        j.msg(0, b"\xff\xfe not even utf-8", TAU - 400_000)
    j.conn(1, "open", t0)
    for i in range(5):
        E = TAU - 700_000 + 100_000 * i
        j.msg(1, frame(E), E + 1000)
    lines = [j.msg(1, raw, TAU - 340_000) for raw in extra]
    lines += [j.add({"t": "MSG", "rec_ms": ms, "conn_id": 1, "recv_ms": ms, "raw_b64": "abc", "sha256": "0" * 64}) for ms in bad_b64]
    lines += [j.add({"t": "MSG", "rec_ms": ms, "conn_id": 1, "recv_ms": ms, "raw_b64": text, "sha256": hashlib.sha256(raw).hexdigest()}) for ms, text, raw in trap]
    for k in range(1, 6):
        j.ping(1, t0 + 200_000 * k)
    undecodable = list(bad_b64) + [ms for ms, _, _ in trap]
    bad_void = sum(1 for ms in undecodable if TAU - 960_000 <= ms <= TAU + 10_000)
    slot_line = j.slot(n_messages=5 + len(extra) + len(undecodable), malformed=(malformed or len(extra)) + len(undecodable),
                       voids=(voids if voids else len(extra)) + bad_void)
    after = [j.msg(1, raw, TAU + 50_000) for raw in after_slot]
    return j, lines, slot_line, after


def run(journal, directory, replay=True, verify_time=TAU + 10_000, anchors=()):
    path = journal.write(directory)
    return V.verify(path, RV.MockAnchor(list(anchors)), "jid", verify_time, replay_slots=replay)


def chain_head(events, n=None):
    """h_n of the first n events (all when None) under the v3 genesis (3.2), computed here and not by the verifier."""
    h = hashlib.sha256(b"DLIQ-JOURNAL-v3-GENESIS").digest()
    for ev in events[:n]:
        h = hashlib.sha256(h + canon(ev)).digest()
    return h.hex()


def checkpoint(j, k, index, time_ms):
    """Append a CHECKPOINT that anchors the first k events; returns the receipt (the anchor entry the journal's anchor must hold)."""
    hx = chain_head(j.events, k)
    rc = {"anchor_id": "a", "index": index, "seq": k, "head": hx, "time_ms": time_ms, "time_resolution_ms": 1000, "time_uncertainty_ms": 500}
    j.add({"t": "CHECKPOINT", "rec_ms": time_ms, "anchored_seq": k, "anchored_head": hx, "receipt": rc})
    return rc


_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def non_canonical(raw, bit):
    """The same bytes with a non-zero trailing bit in the last data character (validate=True alone accepts the text)."""
    t = b64(raw)
    pad = len(t) - len(t.rstrip("="))
    i = len(t) - pad - 1
    c = _ALPHA.index(t[i])
    assert pad in (1, 2) and c & (3 if pad == 1 else 15) == 0 and bit < (4 if pad == 1 else 16)
    out = t[:i] + _ALPHA[c | bit] + t[i + 1:]
    assert base64.b64decode(out, validate=True) == raw and out != t
    return out


def trap_cases(E):
    """(label, text, intended bytes): each text is NOT strict canonical base64, yet a permissive decoder reads it as the intended valid BUY frame (and the recorded sha256 is that frame's)."""
    two_pad = frame(E, ps="BTCUSDT", st=1)                          # 190 bytes: base64 ends in '=='
    one_pad = frame(E, st=1, o_extra={"zz": 1})                     # 182 bytes: base64 ends in '=' (and an unknown key, which a permissive decoder would report)
    assert len(two_pad) % 3 == 1 and len(one_pad) % 3 == 2
    f = two_pad
    t = b64(f)
    return [("invalid character", t[:8] + "!" + t[8:], f), ("trailing newline", t + "\n", f), ("embedded space", t[:12] + " " + t[12:], f), ("leading space", " " + t, f),
            ("one '=' too many", b64(one_pad) + "=", one_pad), ("non-canonical, padding ==", non_canonical(two_pad, 8), two_pad), ("non-canonical, padding =", non_canonical(one_pad, 2), one_pad)]


def named(report, name):
    return [f for f in report["findings"] if f[0] == name]


class StructureReasonTests(unittest.TestCase):
    def reason(self, text):
        return R6.structure_reason(R6.parse_strict_object(text.encode("utf-8")))

    def test_six_reasons_one_example_each_and_the_clean_frames(self):
        table = [
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT"}}', None),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","ps":"BTCUSDT","st":1}}', None),
            ('{"e":"forceOrder","E":1,"st":1,"o":{"s":"BTCUSDT"}}', "st_top_level"),
            ('{"e":"forceOrder","E":1,"st":"x","o":{"s":"BTCUSDT"}}', "st_top_level"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","ps":5}}', "ps_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","ps":null}}', "ps_type"),
            ('{"e":"forceOrder","E":1,"o":{"ps":"BTCUSDT"}}', "ps_no_s"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","ps":"ETHUSDT"}}', "ps_ne_s"),
            ('{"e":"forceOrder","E":1,"o":{"s":5,"ps":"5"}}', "ps_ne_s"),            # an o.s that is not a string differs, also when str(5) == "5"
            ('{"e":"forceOrder","E":1,"o":{"s":null,"ps":"BTCUSDT"}}', "ps_ne_s"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":true}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":1.0}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":1e0}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":"1"}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":null}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":[1]}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":{}}}', "st_type"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":2}}', "st_ne_1"),
            ('{"e":"forceOrder","E":1,"o":{"s":"BTCUSDT","st":0}}', "st_ne_1"),
        ]
        for text, want in table:
            with self.subTest(text=text):
                self.assertEqual(self.reason(text), want)

    def test_the_order_of_the_reasons_is_fixed(self):
        table = [
            ('{"st":1,"o":{"ps":5,"st":2}}', "st_top_level"),
            ('{"o":{"s":"BTCUSDT","ps":5,"st":true}}', "ps_type"),
            ('{"o":{"ps":"BTCUSDT","st":2}}', "ps_no_s"),                 # ps_no_s before st_ne_1
            ('{"o":{"ps":"BTCUSDT","st":"1"}}', "ps_no_s"),               # ps_no_s before st_type
            ('{"o":{"s":"ETHUSDT","ps":"BTCUSDT","st":"x"}}', "ps_ne_s"),
            ('{"o":{"s":"BTCUSDT","st":"x"}}', "st_type"),
        ]
        for text, want in table:
            with self.subTest(text=text):
                self.assertEqual(self.reason(text), want)

    def test_o_missing_or_not_an_object_gives_no_ps_or_st_reason_but_the_top_level_st_is_checked(self):
        for text, want in [('{"e":"forceOrder"}', None), ('{"o":"x"}', None), ('{"o":null}', None), ('{"o":5}', None), ('{"o":[1]}', None),
                           ('{"st":1,"o":"x"}', "st_top_level"), ('{"st":2}', "st_top_level")]:
            with self.subTest(text=text):
                self.assertEqual(self.reason(text), want)

    def test_strict_parsing_rejects_what_7_7a_says(self):
        for raw in (b"\xff\xfe", b'{"a":1,"a":2}', b'{"o":{"x":1,"x":2}}', b'{"a":NaN}', b'{"a":Infinity}', b"[1]", b"5", b'"s"', b"", b'{"a":'):
            with self.subTest(raw=raw):
                self.assertIsNone(R6.parse_strict_object(raw))
        self.assertEqual(R6.parse_strict_object(b'{"a":1.5}'), {"a": 1.5})
        self.assertIsNone(R6.parse_strict_object(None))


class UnknownKeyTests(unittest.TestCase):
    def entries(self, text):
        return R6.unknown_key_entries(R6.parse_strict_object(text.encode("utf-8")))

    def test_one_entry_per_occurrence_sorted_by_code_point_nothing_dropped(self):
        self.assertEqual(self.entries('{"e":1,"E":1,"o":{"s":"x"}}'), [])
        self.assertEqual(self.entries('{"zz":1,"o":{"zz":2}}'), ["o.zz", "zz"])
        self.assertEqual(self.entries('{"o.zz":1,"o":{"zz":2}}'), ["o.zz", "o.zz"])           # a top-level key literally named o.zz: two equal entries, not one
        self.assertEqual(self.entries('{"b":1,"A":1,"o":{"c":1,"a":1,"ps":"x"}}'), ["A", "b", "o.a", "o.c"])
        self.assertEqual(self.entries('{"ps":"x","o":{}}'), ["ps"])                           # a top-level ps is unknown (soft)
        self.assertEqual(self.entries('{"st":1,"o":{}}'), [])                                 # a top-level st is the hard case, not an unknown key
        self.assertEqual(self.entries('{"o":"x","k":1}'), ["k"])


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_control_journal_has_exactly_the_expected_findings(self):
        j, _, slot_line, _ = control()
        r = run(j, self.tmp.name)
        self.assertEqual(sorted(f[0] for f in r["findings"]), ["CANDLE_LAG_UNSET", "NO_CHECKPOINT"])
        self.assertEqual(r["verdict"], "INCOMPLETE")
        self.assertFalse(r["analysis_eligible"])
        self.assertTrue(r["replayed"])
        self.assertEqual(r["slots"], {TAU: "PENDING"})
        self.assertEqual(r["candles"], {})

    def test_the_chain_starts_from_the_v3_genesis(self):
        j, _, _, _ = control()
        path = j.write(self.tmp.name)
        h = hashlib.sha256(b"DLIQ-JOURNAL-v3-GENESIS").digest()
        h2 = hashlib.sha256(b"DLIQ-JOURNAL-v2-GENESIS").digest()
        for ev in j.events:
            h = hashlib.sha256(h + canon(ev)).digest()
            h2 = hashlib.sha256(h2 + canon(ev)).digest()
        r = V.verify(path, RV.MockAnchor([]), "jid", TAU + 10_000)
        self.assertEqual(r["head_hex"], h.hex())
        self.assertNotEqual(r["head_hex"], h2.hex())

    def test_conn_without_feed_or_with_another_value_is_bad_event_and_not_an_open(self):
        for feed in (None, "OTHER", "force", 5):
            with self.subTest(feed=feed):
                j = Journal()
                j.conn(1, "open", TAU - 1_000_000, feed=feed)
                if feed is not None:
                    j.events[0]["feed"] = feed
                E = TAU - 500_000
                m = j.msg(1, frame(E), E + 1000)
                r = V.verify(j.write(self.tmp.name), RV.MockAnchor([]), "jid", TAU)
                self.assertEqual([f[1] for f in named(r, "BAD_EVENT")], [1])
                self.assertEqual([f[1] for f in named(r, "MSG_CONN_UNKNOWN")], [m])
                self.assertEqual(named(r, "CONN_FEED_CONFLICT"), [])

    def test_conflict_only_for_a_valid_conn_after_the_first_open(self):
        j, _, _, _ = control()
        # a close recorded BEFORE the first open of connection 5 names KLINE: no feed yet, no conflict; the open names FORCE; a later close names KLINE: conflict
        j2 = Journal()
        j2.conn(5, "close", TAU - 2_000_000, feed="KLINE")
        j2.conn(5, "open", TAU - 1_000_000, feed="FORCE")
        late = j2.conn(5, "close", TAU - 900_000, feed="KLINE")
        same = j2.conn(5, "close", TAU - 800_000, feed="FORCE")
        r = V.verify(j2.write(self.tmp.name), RV.MockAnchor([]), "jid", TAU)
        self.assertEqual([f[1] for f in named(r, "CONN_FEED_CONFLICT")], [late])
        self.assertNotIn(same, [f[1] for f in named(r, "CONN_FEED_CONFLICT")])
        self.assertEqual(r["verdict"], "FAIL")

    def test_a_message_before_the_first_open_is_unknown_and_still_examined_as_force(self):
        j = Journal()
        bad = j.msg(3, frame(TAU - 5_000_000, ps=5), TAU - 5_000_000)          # ps_type anomaly, far outside V
        j.conn(3, "open", TAU - 1_000_000, feed="KLINE")
        r = V.verify(j.write(self.tmp.name), RV.MockAnchor([]), "jid", TAU)
        self.assertEqual([f[1] for f in named(r, "MSG_CONN_UNKNOWN")], [bad])
        self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_MSG_STRUCTURE")], [(bad, "conn_id=3 reason=ps_type")])
        self.assertEqual(r["verdict"], "FAIL")

    def test_a_kline_connection_changes_no_slot_field_and_is_not_examined(self):
        j, _, _, _ = control(kline_first=True)        # connection 0 (smaller id than 1) is KLINE, healthy over V, and sends junk and a non-forceOrder frame
        r = run(j, self.tmp.name)
        self.assertEqual(sorted(f[0] for f in r["findings"]), ["CANDLE_LAG_UNSET", "NO_CHECKPOINT"])       # no SLOT_MISMATCH, no FORCE_*, no MSG_CONN_UNKNOWN
        self.assertEqual(r["verdict"], "INCOMPLETE")

    def test_the_kline_skip_is_what_keeps_the_slot_unchanged(self):
        # the same journal with connection 0 as FORCE: now it is primary (smallest healthy id) and the journalled slot no longer matches
        j, _, _, _ = control(kline_first=True)
        j.events[0]["feed"] = "FORCE"
        r = run(j, self.tmp.name)
        self.assertTrue(named(r, "SLOT_MISMATCH"))


class RunLevelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_each_reason_one_finding_physical_line_exact_detail(self):
        frames = {
            "st_top_level": frame(TAU - 340_000, top={"st": 1}),
            "ps_type": frame(TAU - 340_000, ps=7),
            "ps_no_s": frame(TAU - 340_000, s=ABSENT, ps="BTCUSDT"),
            "ps_ne_s": frame(TAU - 340_000, ps="ETHUSDT"),
            "st_type": frame(TAU - 340_000, st="1"),
            "st_ne_1": frame(TAU - 340_000, st=2),
        }
        for reason, raw in frames.items():
            with self.subTest(reason=reason):
                j, lines, _, _ = control(extra=[raw])
                r = run(j, self.tmp.name)
                self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_MSG_STRUCTURE")], [(lines[0], "conn_id=1 reason=" + reason)])
                self.assertEqual(r["verdict"], "FAIL")
                self.assertEqual(named(r, "SLOT_MISMATCH"), [])           # the message voids its slot (NONE, MALFORMED) and the journalled slot says so

    def test_where_is_the_physical_line_not_the_seq_field(self):
        j = Journal()
        j.conn(1, "open", TAU - 1_000_000)
        line = j.msg(1, frame(TAU - 340_000, ps=7), TAU - 340_000, seq=500)
        r = V.verify(j.write(self.tmp.name), RV.MockAnchor([]), "jid", TAU)
        self.assertEqual([f[1] for f in named(r, "SEQ_GAP")], [line])
        self.assertEqual([f[1] for f in named(r, "FORCE_MSG_STRUCTURE")], [line])

    def test_messages_after_the_last_slot_and_in_a_journal_without_slot_are_examined(self):
        j, _, _, after = control(after_slot=[frame(TAU + 20_000, ps=7), frame(TAU + 21_000, s="ETHUSDT")])
        r = run(j, self.tmp.name)
        self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_MSG_STRUCTURE")], [(after[0], "conn_id=1 reason=ps_type")])      # the wrong symbol is no structural reason
        j2 = Journal()
        j2.conn(1, "open", TAU - 1_000_000)
        line = j2.msg(1, frame(TAU, st=3), TAU)
        r2 = V.verify(j2.write(self.tmp.name), RV.MockAnchor([]), "jid", TAU)
        self.assertEqual([f[1] for f in named(r2, "FORCE_MSG_STRUCTURE")], [line])

    def test_the_check_is_independent_of_other_malformed_reasons(self):
        j, lines, _, _ = control(extra=[frame(TAU - 340_000, s="ETHUSDT", st=2)])          # wrong symbol AND st != 1
        r = run(j, self.tmp.name)
        self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_MSG_STRUCTURE")], [(lines[0], "conn_id=1 reason=st_ne_1")])

    def test_unparsable_frames_are_not_a_structural_anomaly(self):
        j, _, _, _ = control(extra=[b"\xff\xfe", b'{"o":{"s":"BTCUSDT","s":"BTCUSDT"}}', b"[1]", b'{"st":NaN}'])
        r = run(j, self.tmp.name)
        self.assertEqual(named(r, "FORCE_MSG_STRUCTURE"), [])
        self.assertEqual(named(r, "FORCE_UNKNOWN_KEY"), [])

    def test_unknown_keys_are_soft_one_finding_per_message(self):
        j, _, _, after = control(after_slot=[frame(TAU + 20_000, top={"zz": 1}, o_extra={"zz": 2, "aa": 3})])      # after the slot: the slot itself stays as journalled
        r = run(j, self.tmp.name)
        self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_UNKNOWN_KEY")], [(after[0], "conn_id=1 keys=o.aa,o.zz,zz")])
        self.assertEqual(r["soft"], ["FORCE_UNKNOWN_KEY"])
        self.assertEqual(r["verdict"], "INCOMPLETE")                       # soft only: no FAIL; INCOMPLETE because L is unset

    def test_top_level_ps_is_soft_only_and_top_level_st_is_hard(self):
        j, _, _, after = control(after_slot=[frame(TAU + 20_000, top={"ps": "BTCUSDT"})])
        r = run(j, self.tmp.name)
        self.assertEqual(named(r, "FORCE_MSG_STRUCTURE"), [])
        self.assertEqual([(f[1], f[2]) for f in named(r, "FORCE_UNKNOWN_KEY")], [(after[0], "conn_id=1 keys=ps")])
        self.assertEqual(r["verdict"], "INCOMPLETE")

    # GPT's decision of 2026-11-14 on Q1 (undecodable base64): RAW_HASH_MISMATCH; the MSG stays a replay candidate; explicit MALFORMED; an affected SLOT is voided;
    # no JSON structural check on content that does not exist; no invented bytes; no crash.
    def test_q1_decode_helper_and_explicit_malformed_class(self):
        self.assertIsNone(R6.decode_raw({"raw_b64": "abc"}))               # incorrect padding
        self.assertIsNone(R6.decode_raw({}))
        self.assertEqual(R6.decode_raw({"raw_b64": "e30="}), b"{}")
        self.assertEqual(R6.decode_raw({"raw_b64": ""}), b"")              # the empty text is valid base64 of the empty byte string (and is not "undecodable")
        c = MC.classify(None)
        self.assertEqual((c["class"], c["reason"]), ("MALFORMED", "undecodable_base64"))
        self.assertNotEqual(MC.classify(b"")["reason"], "undecodable_base64")       # empty bytes are a different, ordinary parse failure

    def test_q1_undecodable_msg_in_v_voids_the_slot_and_is_hard_reported(self):
        j, lines, _, _ = control(bad_b64=[TAU - 340_000])
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "RAW_HASH_MISMATCH")], [lines[0]])
        self.assertEqual(named(r, "SLOT_MISMATCH"), [])          # the replay voided the slot exactly as journalled: status NONE, reason MALFORMED, one void, ledger MALFORMED 1
        self.assertEqual(named(r, "FORCE_MSG_STRUCTURE") + named(r, "FORCE_UNKNOWN_KEY"), [])      # no JSON structural check on nonexistent content
        self.assertEqual(r["verdict"], "FAIL")
        self.assertTrue(r["replayed"])

    def test_q1_the_voided_slot_is_what_the_journal_must_say(self):
        j, lines, slot_line, _ = control(bad_b64=[TAU - 340_000])
        slot = j.events[slot_line - 1]
        slot.update({"status": "VALID", "reasons": [], "malformed_voids": 0, "side": 1})
        slot["ledger"] = dict(slot["ledger"], MALFORMED=0)
        slot["n_messages"] = 6
        r = run(j, self.tmp.name)
        self.assertEqual(len(named(r, "SLOT_MISMATCH")), 1)           # a journal that claims a VALID slot despite the undecodable MSG in V is caught by the replay

    def test_q1_undecodable_msg_outside_v_is_malformed_in_the_ledger_but_voids_nothing(self):
        j, lines, _, _ = control(bad_b64=[TAU - 980_000])             # before V(tau) = [tau - 960_000, tau + 10_000]
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "RAW_HASH_MISMATCH")], [lines[0]])
        self.assertEqual(named(r, "SLOT_MISMATCH"), [])
        self.assertEqual(r["slots"], {TAU: "PENDING"})

    def test_q1_the_message_stays_a_replay_candidate_with_no_invented_bytes(self):
        j, _, _, _ = control(bad_b64=[TAU - 340_000])
        seen = []
        real = MC.build_slot

        def spy(tau, messages, health, clock_offset_ms=0):
            seen.append([m["raw"] for m in messages])
            return real(tau, messages, health, clock_offset_ms=clock_offset_ms)

        with mock.patch.object(MC, "build_slot", spy):
            run(j, self.tmp.name)
        self.assertEqual(len(seen), 1)
        self.assertEqual(len(seen[0]), 6)                             # five good frames and the undecodable one: not dropped
        self.assertEqual(sum(1 for raw in seen[0] if raw is None), 1)
        self.assertNotIn(b"", seen[0])                                # and no empty bytes were made up for it

    # GPT's BLOCKING finding of 2026-11-14 against de41160: the replay decoded permissively ('e!30=' gave b'{}') while the hash check was strict. Strict canonical decoding everywhere.
    def test_q1_strict_canonical_decoding_table(self):
        for text in ("e!30=", "e30=\n", "e3 0=", " e30=", "e30= ", "e3\n0=", "e31=", "e30==", "e30", "=e30", "e30=x", "\u00e9AAA", "e30=\x00", "AAB=", "AB==", "AAA=\n"):
            with self.subTest(text=text):
                self.assertIsNone(R6.decode_raw({"raw_b64": text}))
        for value in (None, 5, b"e30=", ["e30="]):
            with self.subTest(value=value):
                self.assertIsNone(R6.decode_raw({"raw_b64": value}))
        for text, raw in (("e30=", b"{}"), ("", b""), ("AAAA", b"\0\0\0"), ("AA==", b"\0"), ("AAA=", b"\0\0")):
            with self.subTest(text=text):
                self.assertEqual(R6.decode_raw({"raw_b64": text}), raw)

    def test_q1_the_strict_decoder_agrees_with_a_hand_written_grammar_on_every_short_string(self):
        """A second method for the same rule (2.2): RFC 4648 section 4 grammar plus zero trailing bits, written here from the text. Exhaustive over all strings of length 0 to 6 over a
        small alphabet that has a canonical and a non-canonical last character, padding, an invalid character and whitespace."""
        grammar = re.compile(r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")

        def reference(t):
            if grammar.fullmatch(t) is None:
                return None
            if t.endswith("==") and _ALPHA.index(t[-3]) & 0x0F:
                return None
            if t.endswith("=") and not t.endswith("==") and _ALPHA.index(t[-2]) & 0x03:
                return None
            return base64.b64decode(t)
        n = 0
        for k in range(7):
            for tup in itertools.product("AQRY=!\n", repeat=k):
                t = "".join(tup)
                self.assertEqual(R6.decode_raw({"raw_b64": t}), reference(t), repr(t))
                n += 1
        self.assertGreater(n, 100_000)

    def test_q1_trap_texts_are_undecodable_and_cannot_enter_the_buy_sell_count(self):
        """Every trap text is read by a PERMISSIVE decoder as a valid BUY frame whose hash matches. Here each is RAW_HASH_MISMATCH, MALFORMED in the replay (never counted as BUY or SELL),
        voids the slot, and gets no structural finding; a journal that claims the message was counted is caught."""
        cases = trap_cases(TAU - 340_000)
        self.assertEqual(len(cases), 7)
        for label, text, intended in cases:
            with self.subTest(label):
                self.assertEqual(base64.b64decode(text), intended)                      # it really is a trap: the permissive decoding is the valid frame
                self.assertIsNone(R6.decode_raw({"raw_b64": text}))
                results = []
                real = MC.build_slot

                def spy(tau, messages, health, clock_offset_ms=0):
                    rec = real(tau, messages, health, clock_offset_ms=clock_offset_ms)
                    results.append((rec, [m["raw"] for m in messages]))
                    return rec

                j, lines, slot_line, _ = control(trap=[(TAU - 340_000, text, intended)])
                with mock.patch.object(MC, "build_slot", spy):
                    r = run(j, self.tmp.name)
                self.assertEqual([f[1] for f in named(r, "RAW_HASH_MISMATCH")], [lines[0]])
                self.assertEqual(named(r, "SLOT_MISMATCH"), [])
                self.assertEqual(named(r, "FORCE_MSG_STRUCTURE") + named(r, "FORCE_UNKNOWN_KEY"), [])
                self.assertEqual(r["verdict"], "FAIL")
                rec, raws = results[0]
                self.assertEqual((rec["N_total"], rec["N_BUY"], rec["N_SELL"]), (5, 5, 0))           # the sixth message is in neither count
                self.assertEqual((rec["ledger"]["MALFORMED"], rec["ledger"]["COUNTED"], rec["n_messages"]), (1, 5, 6))
                self.assertEqual((rec["status"], rec["malformed_voids"]), ("NONE", 1))
                self.assertEqual(sum(1 for raw in raws if raw is None), 1)                              # it stayed a replay candidate, with no bytes
                self.assertEqual(rec["sumW_BUY"], "300000")                                             # five weights of 60000, not six
                claim = j.events[slot_line - 1]                                                          # a journal that says "VALID, six BUY messages" is wrong
                claim.update({"status": "VALID", "reasons": [], "side": 1, "malformed_voids": 0, "N_total": 6, "N_BUY": 6, "sumW_BUY": "360000"})
                claim["ledger"] = dict(claim["ledger"], MALFORMED=0, COUNTED=6)
                self.assertEqual(len(named(run(j, self.tmp.name), "SLOT_MISMATCH")), 1)

    def test_q1_a_trap_text_outside_v_is_malformed_in_the_ledger_and_voids_nothing(self):
        label, text, intended = trap_cases(TAU - 980_000)[0]
        j, lines, _, _ = control(trap=[(TAU - 980_000, text, intended)])
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "RAW_HASH_MISMATCH")], [lines[0]])
        self.assertEqual(named(r, "SLOT_MISMATCH"), [])
        self.assertEqual(r["slots"], {TAU: "PENDING"})

    def test_q1_a_trap_text_after_the_last_slot_changes_nothing_but_the_hash_finding(self):
        label, text, intended = trap_cases(TAU + 50_000)[0]
        j, _, _, _ = control()
        line = j.add({"t": "MSG", "rec_ms": TAU + 50_000, "conn_id": 1, "recv_ms": TAU + 50_000, "raw_b64": text, "sha256": hashlib.sha256(intended).hexdigest()})
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "RAW_HASH_MISMATCH")], [line])
        self.assertEqual(named(r, "SLOT_MISMATCH") + named(r, "FORCE_MSG_STRUCTURE") + named(r, "FORCE_UNKNOWN_KEY"), [])

    def test_the_run_level_pass_does_not_depend_on_the_replay_switch(self):
        j, lines, _, _ = control(extra=[frame(TAU - 340_000, ps=7)])
        for flag in (False, None, 0, 1, "yes"):
            with self.subTest(flag=flag):
                r = run(j, self.tmp.name, replay=flag)
                self.assertEqual([f[1] for f in named(r, "FORCE_MSG_STRUCTURE")], [lines[0]])
                self.assertFalse(r["replayed"])
                self.assertEqual(len(named(r, "REPLAY_NOT_RUN")), 1)
                self.assertEqual(r["verdict"], "FAIL")
        j2, _, _, _ = control()
        r2 = run(j2, self.tmp.name, replay=False)
        self.assertEqual(r2["verdict"], "INCOMPLETE")
        self.assertFalse(r2["analysis_eligible"])


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def candle(self, **override):
        ev = {"t": "CANDLE", "rec_ms": TAU, "open_time_ms": TAU, "open": "60000", "recv_ms": TAU, "raw_b64": "e30=", "sha256": hashlib.sha256(b"{}").hexdigest(), "msg_seq": 1}
        ev.update(override)
        return ev

    def test_a_valid_candle_event_is_refused_not_given_a_verdict(self):
        j, _, _, _ = control()
        j.add(self.candle())
        with self.assertRaises(V.UnsupportedJournal):
            run(j, self.tmp.name)

    def test_a_candle_event_without_msg_seq_is_bad_event_and_does_not_raise(self):
        j, _, _, _ = control()
        ev = self.candle()
        del ev["msg_seq"]
        line = j.add(ev)
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "BAD_EVENT")], [line])

    def test_cand_lag_unset_on_every_journal_so_never_pass(self):
        empty = os.path.join(self.tmp.name, "empty.jsonl")
        open(empty, "wb").close()
        r = V.verify(empty, RV.MockAnchor([]), "jid", 0)
        self.assertEqual(named(r, "CANDLE_LAG_UNSET"), [["CANDLE_LAG_UNSET", 0, "L is unset (6.8); no CANDLE minute is USABLE"]])
        self.assertEqual(r["verdict"], "INCOMPLETE")
        self.assertFalse(r["analysis_eligible"])

    def test_an_eval_outcome_has_two_unlinked_findings_a_no_price_outcome_none(self):
        j, _, slot_line, _ = control()
        entry, exit_ = TAU + 300_000, TAU + 300_000 + 14_400_000
        calc = repr(10000.0 * math.log(101.0 / 100.0))
        j.add({"t": "OUTCOME", "rec_ms": exit_ + 60_000, "tau_ms": TAU, "status": "EVAL", "entry_open_ms": entry, "exit_open_ms": exit_, "entry_price": "100", "exit_price": "101", "r_bps": calc})
        r = run(j, self.tmp.name)
        self.assertEqual([f[1] for f in named(r, "OUTCOME_UNLINKED")], [len(j.events)] * 2)
        details = [f[2] for f in named(r, "OUTCOME_UNLINKED")]
        self.assertEqual(len(set(details)), 2)                          # GPT, 2026-11-14, Q4: the two findings are distinguishable
        self.assertTrue(details[0].startswith("endpoint=entry: ") and str(entry) in details[0], details[0])
        self.assertTrue(details[1].startswith("endpoint=exit: ") and str(exit_) in details[1], details[1])
        self.assertEqual(named(r, "OUTCOME_MISMATCH"), [])
        j2, _, _, _ = control()
        j2.add({"t": "OUTCOME", "rec_ms": exit_ + 60_000, "tau_ms": TAU, "status": "NO_PRICE"})
        self.assertEqual(named(run(j2, self.tmp.name), "OUTCOME_UNLINKED"), [])


class ReportKeyTests(unittest.TestCase):
    """The report keys of contract 8.2 that the runner now compares for every vector: n_events, head_hex (3.2) and outcomes (6.4). Expected values are computed in this file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def eval_outcome(self):
        entry, exit_ = TAU + 300_000, TAU + 300_000 + 14_400_000
        return {"t": "OUTCOME", "rec_ms": exit_ + 60_000, "tau_ms": TAU, "status": "EVAL", "entry_open_ms": entry, "exit_open_ms": exit_, "entry_price": "100", "exit_price": "100", "r_bps": "0.0"}

    def test_n_events_and_head_hex(self):
        j, _, _, _ = control()
        r = run(j, self.tmp.name)
        self.assertEqual(r["n_events"], len(j.events))
        self.assertEqual(r["head_hex"], chain_head(j.events))
        self.assertEqual(r["outcomes"], {})

    def test_head_hex_covers_every_parsed_line_including_a_bad_event(self):
        j, _, _, _ = control()
        j.add({"t": "CANDLE", "rec_ms": TAU, "open_time_ms": TAU})            # BAD_EVENT: not valid, but it takes part in the chain (3.2)
        r = run(j, self.tmp.name)
        self.assertEqual(r["n_events"], len(j.events))
        self.assertEqual(r["head_hex"], chain_head(j.events))

    def test_outcomes_uncovered_then_covered(self):
        j, _, slot_line, _ = control()
        rc1 = checkpoint(j, slot_line, 1, TAU + 20_000)
        out_line = j.add(self.eval_outcome())
        r = run(j, self.tmp.name, anchors=[rc1])
        self.assertEqual(r["outcomes"], {TAU: "UNCOVERED"})
        self.assertEqual([f[1] for f in named(r, "OUTCOME_UNCOVERED")], [TAU])
        rc2 = checkpoint(j, out_line, 2, TAU + 15_000_000)
        r = run(j, self.tmp.name, anchors=[rc1, rc2])
        self.assertEqual(r["outcomes"], {TAU: "COVERED"})
        self.assertEqual(named(r, "OUTCOME_UNCOVERED"), [])
        self.assertEqual(r["n_events"], len(j.events))
        self.assertEqual(r["head_hex"], chain_head(j.events))
        self.assertEqual([f[1] for f in named(r, "OUTCOME_UNLINKED")], [out_line, out_line])       # L is unset: unlinked whether or not it is covered

    def test_a_second_outcome_for_the_same_tau_is_not_entered(self):
        j, _, slot_line, _ = control()
        rc1 = checkpoint(j, slot_line, 1, TAU + 20_000)
        first = j.add(self.eval_outcome())
        rc2 = checkpoint(j, first, 2, TAU + 15_000_000)
        j.add(dict(self.eval_outcome(), rec_ms=TAU + 16_000_000))
        r = run(j, self.tmp.name, anchors=[rc1, rc2])
        self.assertEqual(r["outcomes"], {TAU: "COVERED"})                    # the reference OUTCOME is the first one; the duplicate is a hard finding, not an entry
        self.assertEqual(len(named(r, "DUPLICATE_OUTCOME")), 1)


class RunnerTests(unittest.TestCase):
    """NEGATIVE tests of run_vectors.py: the runner must fail on a wrong expectation, a wrong digest, a wrong count, a missing file and an empty directory."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vdir = os.path.join(self.tmp.name, "vectors")
        os.makedirs(os.path.join(self.vdir, "T01"))
        j, _, _, _ = control()
        j.write(os.path.join(self.vdir, "T01"))
        self.journal = j
        self.expect = {"id": "T01", "journal_id": "t01", "verify_time_ms": TAU + 10_000, "anchor": [],
                       "verdict": "INCOMPLETE", "hard": ["CANDLE_LAG_UNSET"], "soft": [], "missing": [], "replayed": True, "analysis_eligible": False,
                       "slots": {str(TAU): "PENDING"}, "candles": {},
                       "findings": [["CANDLE_LAG_UNSET", 0, None], ["NO_CHECKPOINT", 0, None]]}
        self.write_expect(self.expect)

    def write_expect(self, expect):
        with open(os.path.join(self.vdir, "T01", "expect.json"), "w", encoding="utf-8") as fh:
            json.dump(expect, fh)

    def main(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = RV.main(["--vectors", self.vdir, *extra])
        return code, out.getvalue()

    def test_passes_on_a_correct_expectation(self):
        code, out = self.main()
        self.assertEqual(code, 0, out)
        self.assertIn("problems: 0", out)

    def test_fails_on_every_kind_of_wrong_expectation(self):
        mutations = [
            ("verdict", lambda e: e.update(verdict="PASS")),
            ("hard", lambda e: e.update(hard=[])),
            ("soft", lambda e: e.update(soft=["FORCE_UNKNOWN_KEY"])),
            ("slots", lambda e: e.update(slots={str(TAU): "OK"})),
            ("missing", lambda e: e.update(missing=[TAU])),
            ("replayed", lambda e: e.update(replayed=False)),
            ("eligible", lambda e: e.update(analysis_eligible=True)),
            ("candles", lambda e: e.update(candles={"1": "USABLE"})),
            ("extra expected finding", lambda e: e["findings"].append(["FORCE_MSG_STRUCTURE", 3, "conn_id=1 reason=ps_type"])),
            ("missing expected finding", lambda e: e["findings"].pop()),
            ("where", lambda e: e["findings"].__setitem__(1, ["NO_CHECKPOINT", 1, None])),
        ]
        for label, mutate in mutations:
            with self.subTest(label):
                expect = json.loads(json.dumps(self.expect))
                mutate(expect)
                self.write_expect(expect)
                code, out = self.main()
                self.assertEqual(code, 1, out)
                self.assertIn("FAIL T01", out)
        self.write_expect(self.expect)

    def test_the_detail_of_a_force_finding_is_compared_exactly(self):
        j, lines, _, _ = control(extra=[frame(TAU - 340_000, ps=7)])
        j.write(os.path.join(self.vdir, "T01"))
        expect = json.loads(json.dumps(self.expect))
        expect.update(verdict="FAIL", hard=["CANDLE_LAG_UNSET", "FORCE_MSG_STRUCTURE"])
        expect["findings"].append(["FORCE_MSG_STRUCTURE", lines[0], "conn_id=1 reason=ps_type"])
        self.write_expect(expect)
        self.assertEqual(self.main()[0], 0)
        expect["findings"][-1][2] = "conn_id=1 reason=ps_ne_s"
        self.write_expect(expect)
        self.assertEqual(self.main()[0], 1)

    # --- the three report keys of 8.2 that were not compared before GPT's review of 2026-11-14: n_events, head_hex, outcomes; and the endpoint of OUTCOME_UNLINKED
    def pair(self):
        """A (report, expect, derived) triple that agrees: an EVAL outcome with its two OUTCOME_UNLINKED findings, covered."""
        report = {"verdict": "FAIL", "findings": [["CANDLE_LAG_UNSET", 0, "L is unset"], ["OUTCOME_UNLINKED", 14, "endpoint=entry: no USABLE reference CANDLE for open_time_ms 1"],
                                                  ["OUTCOME_UNLINKED", 14, "endpoint=exit: no USABLE reference CANDLE for open_time_ms 2"]],
                  "hard": ["CANDLE_LAG_UNSET", "OUTCOME_UNLINKED"], "soft": [], "n_events": 15, "head_hex": "ab" * 32, "slots": {TAU: "OK"}, "missing": [],
                  "outcomes": {TAU: "COVERED"}, "candles": {}, "replayed": True, "analysis_eligible": False}
        expect = {"verdict": "FAIL", "findings": [["CANDLE_LAG_UNSET", 0, None], ["OUTCOME_UNLINKED", 14, "endpoint=entry"], ["OUTCOME_UNLINKED", 14, "endpoint=exit"]],
                  "hard": ["CANDLE_LAG_UNSET", "OUTCOME_UNLINKED"], "soft": [], "slots": {str(TAU): "OK"}, "missing": [], "candles": {}, "replayed": True, "analysis_eligible": False}
        derived = {"n_events": 15, "head_hex": "ab" * 32, "outcomes": {str(TAU): "COVERED"}}
        return report, expect, derived

    def test_compare_is_clean_on_a_matching_triple_and_ignores_diagnostic_text(self):
        report, expect, derived = self.pair()
        self.assertEqual(RV.compare(report, expect, derived), [])
        report["findings"][0][2] = "another diagnostic text"                                   # free text of an ordinary finding is not compared
        report["findings"][1][2] = "endpoint=entry"                                            # the prefix alone is enough
        report["findings"][2][2] = "endpoint=exit and anything after it"
        self.assertEqual(RV.compare(report, expect, derived), [])

    def test_compare_examines_all_twelve_report_keys_of_8_2(self):
        keys = ("verdict", "findings", "hard", "soft", "n_events", "head_hex", "slots", "missing", "outcomes", "candles", "replayed", "analysis_eligible")
        report, expect, derived = self.pair()
        self.assertEqual(sorted(report), sorted(keys))
        mutations = {"verdict": "PASS", "findings": report["findings"] + [["SLOT_MISMATCH", 3, "x"]], "hard": [], "soft": ["FORCE_UNKNOWN_KEY"], "n_events": 16, "head_hex": "cd" * 32,
                     "slots": {TAU: "LATE"}, "missing": [TAU], "outcomes": {TAU: "UNCOVERED"}, "candles": {1: "USABLE"}, "replayed": False, "analysis_eligible": True}
        self.assertEqual(sorted(mutations), sorted(keys))
        for key, value in mutations.items():
            with self.subTest(key):
                bad = dict(report)
                bad[key] = value
                self.assertNotEqual(RV.compare(bad, expect, derived), [], key)

    def test_the_endpoint_of_outcome_unlinked_and_the_order_of_the_two_findings_are_compared(self):
        report, expect, derived = self.pair()
        for label, details in (("swapped", ["endpoint=exit: x", "endpoint=entry: x"]), ("both entry", ["endpoint=entry: x", "endpoint=entry: x"]),
                               ("no endpoint", ["no USABLE reference CANDLE", "no USABLE reference CANDLE"]), ("prefix glued to a word", ["endpoint=entryX", "endpoint=exit"]),
                               ("endpoint in the middle", ["x endpoint=entry", "endpoint=exit"])):
            with self.subTest(label):
                bad = json.loads(json.dumps(report))
                bad["findings"][1][2], bad["findings"][2][2] = details
                self.assertNotEqual(RV.compare(bad, expect, derived), [])
        reordered = json.loads(json.dumps(report))
        reordered["findings"][1], reordered["findings"][2] = reordered["findings"][2], reordered["findings"][1]       # the same multiset, the wrong order
        problems = RV.compare(reordered, expect, derived)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("OUTCOME_UNLINKED order", problems[0])
        moved = json.loads(json.dumps(report))
        moved["findings"].insert(0, moved["findings"].pop(0))                                                           # other findings may come in any order
        self.assertEqual(RV.compare(moved, expect, derived), [])
        report["findings"][1][1] = 15                                                                                    # the line of the finding is compared too
        self.assertNotEqual(RV.compare(report, expect, derived), [])

    def test_without_a_derived_entry_the_three_keys_are_not_compared(self):
        report, expect, derived = self.pair()
        report.update(n_events=999, head_hex="00" * 32, outcomes={})
        self.assertEqual(RV.compare(report, expect), [])                      # the older pins have no EXPECT_DERIVED.json: main() says "NOT COMPARED"
        self.assertEqual(len(RV.compare(report, expect, derived)), 3)

    def write_derived(self, vectors):
        with open(os.path.join(self.vdir, "EXPECT_DERIVED.json"), "w", encoding="utf-8") as fh:
            json.dump({"note": "test", "vectors": vectors}, fh)

    def test_the_runner_reads_the_derived_file_compares_it_and_says_what_it_did_not_compare(self):
        good = {"n_events": len(self.journal.events), "head_hex": chain_head(self.journal.events), "outcomes": {}}
        code, out = self.main()
        self.assertEqual(code, 0, out)
        self.assertIn("NOT COMPARED for 1 of 1 vectors", out)
        code, out = self.main("--require-derived")
        self.assertEqual(code, 1)
        self.assertIn("DERIVED FILE MISSING", out)
        self.write_derived({"T01": good})
        code, out = self.main("--require-derived")
        self.assertEqual(code, 0, out)
        self.assertIn("compared for 1 of 1 vectors", out)
        self.assertNotIn("NOT COMPARED", out)
        for label, vectors in (("n_events", {"T01": dict(good, n_events=good["n_events"] + 1)}), ("head_hex", {"T01": dict(good, head_hex="0" * 64)}),
                               ("outcomes", {"T01": dict(good, outcomes={str(TAU): "COVERED"})}), ("a key is missing", {"T01": {"n_events": good["n_events"], "head_hex": good["head_hex"]}}),
                               ("an extra key", {"T01": dict(good, more=1)}), ("another vector id", {"T01": good, "T02": good}), ("the vector is not named", {"T99": good}), ("empty", {})):
            with self.subTest(label):
                self.write_derived(vectors)
                code, out = self.main()
                self.assertEqual(code, 1, out)

    def test_fails_on_wrong_digest_count_missing_file_empty_dir_and_a_crashing_journal(self):
        self.assertEqual(self.main("--expect-digest", "0" * 64)[0], 1)
        self.assertEqual(self.main("--expect-count", "2")[0], 1)
        self.assertEqual(self.main("--expect-count", "1", "--expect-digest", RV.vector_set_digest(self.vdir)[0])[0], 0)
        os.remove(os.path.join(self.vdir, "T01", "expect.json"))
        self.assertEqual(self.main()[0], 1)
        self.write_expect(self.expect)
        with open(os.path.join(self.vdir, "T01", "journal.jsonl"), "ab") as fh:           # a journal with a valid CANDLE event: the verifier raises, the runner must fail
            fh.write(b"")
        j, _, _, _ = control()
        j.add({"t": "CANDLE", "rec_ms": TAU, "open_time_ms": TAU, "open": "1", "recv_ms": TAU, "raw_b64": "e30=", "sha256": hashlib.sha256(b"{}").hexdigest(), "msg_seq": 1})
        j.write(os.path.join(self.vdir, "T01"))
        code, out = self.main()
        self.assertEqual(code, 1)
        self.assertIn("UnsupportedJournal", out)
        empty = os.path.join(self.tmp.name, "empty")
        os.makedirs(empty)
        out2 = io.StringIO()
        with contextlib.redirect_stdout(out2):
            self.assertEqual(RV.main(["--vectors", empty]), 1)

    def test_the_digest_is_a_byte_order_sha256_of_the_sha256sum_lines(self):
        os.makedirs(os.path.join(self.vdir, "T01b"))
        for name, data in (("journal.jsonl", b"a\n"), ("expect.json", b"{}")):
            with open(os.path.join(self.vdir, "T01b", name), "wb") as fh:
                fh.write(data)
        lines = ""
        for rel in sorted(["T01/journal.jsonl", "T01/expect.json", "T01b/journal.jsonl", "T01b/expect.json"], key=lambda p: p.encode()):
            with open(os.path.join(self.vdir, rel), "rb") as fh:
                lines += "%s  vectors/%s\n" % (hashlib.sha256(fh.read()).hexdigest(), rel)
        self.assertEqual(RV.vector_set_digest(self.vdir)[0], hashlib.sha256(lines.encode()).hexdigest())


class GuardTests(unittest.TestCase):
    FILES = ("dliq_journal_verify_v3.py", "dliq_msg_contract_v3.py", "r6_rules.py")

    def imports(self, name):
        tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        return found

    def test_no_file_of_the_package_imports_the_oracle_or_the_vector_generator(self):
        for name in sorted(p.name for p in HERE.glob("*.py")):
            with self.subTest(name=name):
                bad = self.imports(name) & {"oracle_r6", "make_vectors", "check_vectors", "mutation_check_oracle", "test_r6_vectors"}
                self.assertEqual(bad, set())
        self.assertNotIn("oracle_r6", sys.modules)

    def test_the_verifier_uses_the_standard_library_only_without_clock_network_or_processes(self):
        allowed = {"base64", "hashlib", "json", "math", "os", "re", "sys", "decimal", "r6_rules", "dliq_msg_contract_v3"}
        for name in self.FILES:
            with self.subTest(name=name):
                self.assertEqual(self.imports(name) - allowed, set())

    def test_the_only_base64_decoder_is_the_strict_one_and_the_verifier_has_no_base64_of_its_own(self):
        """GPT's blocking finding of 2026-11-14: a permissive `base64.b64decode(text)` next to a strict one made the hash check and the replay disagree. The only decoding call of the
        package is the one in r6_rules.decode_raw, with validate=True; no other file of the verifier imports base64 or calls a decoder."""
        decoders = {"b64decode", "urlsafe_b64decode", "standard_b64decode", "decodebytes", "decodestring", "a2b_base64", "b32decode", "b16decode", "a85decode", "b85decode"}
        calls = {}
        for name in self.FILES + ("run_vectors.py", "make_provenance.py"):
            tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and (node.module or "") in ("base64", "binascii"):
                    self.fail("%s imports names from %s" % (name, node.module))
                if isinstance(node, ast.Call):
                    fn = node.func
                    called = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else None
                    if called in decoders:
                        calls.setdefault(name, []).append(node)
        self.assertEqual(sorted(calls), ["r6_rules.py"])
        self.assertEqual(len(calls["r6_rules.py"]), 1)
        node = calls["r6_rules.py"][0]
        self.assertEqual(node.func.attr, "b64decode")
        self.assertEqual([(k.arg, getattr(k.value, "value", None)) for k in node.keywords], [("validate", True)])
        self.assertNotIn("base64", self.imports("dliq_journal_verify_v3.py"))
        self.assertNotIn("base64", self.imports("dliq_msg_contract_v3.py"))

    def test_provenance_diffs_are_current(self):
        self.assertEqual(MP.main(["--check"]), 0)
        for out_name, old_name, new_name in MP.PAIRS:
            self.assertEqual((HERE / out_name).read_text(encoding="utf-8"), MP.render(old_name, new_name))

    def test_readme_lists_the_current_hashes_of_the_verifier_files(self):
        readme = (HERE / "README.md").read_text(encoding="utf-8")
        for name in self.FILES:
            with self.subTest(name=name):
                self.assertIn(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), readme)

    def test_stale_provenance_diff_is_detected(self):
        out_name = MP.PAIRS[0][0]
        target = HERE / out_name
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(original + "# stale\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MP.main(["--check"]), 1)
        finally:
            target.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=1)
