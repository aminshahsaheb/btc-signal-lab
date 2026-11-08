"""Synthetic tests for dliq_kline_v1 (parser + reference CANDLE checker). Fixtures are invented frames shaped like the documented
kline message; they are NOT captured exchange data. A pass shows the rules behave as written in docs/G1_CANDLE_CONTRACT_PROPOSAL.md; it
says nothing about the real feed ([VERIFY] items) and nothing about market behaviour."""
import base64
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I does not add the script directory

import dliq_kline_v1 as K

T0 = 1_800_000_000_000          # a whole minute
MIN = 60_000


def frame(t=T0, o="100.5", E=None, x=False, form="RAW", **over):
    E = t + 1000 if E is None else E          # E=KeyError removes the key
    k = {"t": t, "T": t + MIN - 1, "s": "BTCUSDT", "i": "1m", "f": 1, "L": 2, "o": o, "c": o, "h": o, "l": o, "v": "1", "n": 1, "x": x, "q": "1", "V": "1", "Q": "1", "B": "0"}
    msg = {"e": "kline", "E": E, "s": "BTCUSDT", "k": k}
    if E is KeyError:
        del msg["E"]
    for key, val in over.items():
        if key.startswith("k_"):
            if val is KeyError:
                k.pop(key[2:], None)
            else:
                k[key[2:]] = val
        elif val is KeyError:
            msg.pop(key, None)
        else:
            msg[key] = val
    top = {"stream": "btcusdt@kline_1m", "data": msg} if form == "COMBINED" else msg
    return json.dumps(top, separators=(",", ":")).encode()


def b64(raw):
    return base64.b64encode(raw).decode()


def msg_ev(conn, recv, raw):
    return {"t": "MSG", "conn_id": conn, "recv_ms": recv, "raw_b64": b64(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def cand_ev(ot, o, recv, raw, msg_seq):
    return {"t": "CANDLE", "open_time_ms": ot, "open": o, "recv_ms": recv, "raw_b64": b64(raw), "sha256": hashlib.sha256(raw).hexdigest(), "msg_seq": msg_seq}


def journal(frames, feed="KLINE", open_ms=T0 - 10 * MIN, close_ms=None, clock=None, conn=7):
    """frames: list of (raw, recv_ms[, overrides dict for the CANDLE event]). Returns the (line, event) list of a minimal valid journal."""
    evs = [{"t": "CONN", "conn_id": conn, "ev": "open", "ms": open_ms}]
    if feed is not None:
        evs[0]["feed"] = feed
    if clock is not None:
        evs.append({"t": "CLOCK", "offset_ms": clock, "ms": open_ms})
    for item in frames:
        raw, recv = item[0], item[1]
        ov = item[2] if len(item) > 2 else {}
        p = K.parse_kline_frame(raw)
        ot, o = (p["t"], p["o"]) if p["ok"] else (T0, "100.5")
        evs.append(msg_ev(conn, recv, raw))
        m = len(evs)
        c = cand_ev(ot, o, recv, raw, m)
        c.update(ov)
        evs.append(c)
    if close_ms is not None:
        evs.append({"t": "CONN", "conn_id": conn, "ev": "close", "ms": close_ms})
    return [(i, dict(ev, seq=i, rec_ms=0)) for i, ev in enumerate(evs, 1)]


def names(findings):
    return sorted(f[0] for f in findings)


L = 5000


class ParserAccepts(unittest.TestCase):
    def test_raw_form(self):
        r = K.parse_kline_frame(frame())
        self.assertEqual({k: r[k] for k in ("ok", "form", "t", "T", "o", "E", "x")}, {"ok": True, "form": "RAW", "t": T0, "T": T0 + MIN - 1, "o": "100.5", "E": T0 + 1000, "x": False})

    def test_combined_form(self):
        r = K.parse_kline_frame(frame(form="COMBINED"))
        self.assertTrue(r["ok"])
        self.assertEqual(r["form"], "COMBINED")

    def test_bytearray_and_closed_candle(self):
        self.assertTrue(K.parse_kline_frame(bytearray(frame(x=True)))["ok"])


class ParserRejects(unittest.TestCase):
    def reason(self, raw, **kw):
        r = K.parse_kline_frame(raw, **kw)
        self.assertFalse(r["ok"], raw)
        return r["reason"]

    def test_not_bytes(self):
        self.assertEqual(self.reason("text"), "not_bytes")

    def test_utf8(self):
        self.assertEqual(self.reason(b"\xff\xfe{}"), "utf8")

    def test_json(self):
        self.assertEqual(self.reason(b"{not json"), "json")
        self.assertEqual(self.reason(b""), "json")

    def test_nan(self):
        self.assertEqual(self.reason(b'{"e":NaN}'), "json")

    def test_duplicate_key_top_and_nested(self):
        self.assertEqual(self.reason(b'{"e":"kline","e":"kline"}'), "duplicate_key")
        raw = frame().replace(b'"i":"1m"', b'"i":"1m","i":"1m"')
        self.assertEqual(self.reason(raw), "duplicate_key")

    def test_rest_array(self):
        rest = b'[[1800000000000,"100.5","101","99","100","1",1800000059999,"1",1,"1","1","0"]]'
        self.assertEqual(self.reason(rest), "rest_array")
        self.assertEqual(self.reason(b"[]"), "rest_array")

    def test_not_object(self):
        for raw in (b"1", b'"s"', b"null", b"true"):
            self.assertEqual(self.reason(raw), "not_object")

    def test_combined_structure(self):
        good = json.loads(frame(form="COMBINED"))
        extra = dict(good, more=1)
        self.assertEqual(self.reason(json.dumps(extra).encode()), "combined_keys")
        self.assertEqual(self.reason(json.dumps({"stream": "btcusdt@kline_1m"}).encode()), "combined_keys")
        self.assertEqual(self.reason(json.dumps(dict(good, data=[1])).encode()), "data_not_object")

    def test_stream_name(self):
        for name in ("btcusdt@kline_5m", "ethusdt@kline_1m", "BTCUSDT@kline_1m", "", None, 5):
            good = json.loads(frame(form="COMBINED"))
            good["stream"] = name
            self.assertEqual(self.reason(json.dumps(good).encode()), "stream_name", name)

    def test_event_type(self):
        for e in ("continuous_kline", "forceOrder", "KLINE", None):
            self.assertEqual(self.reason(frame(e=e)), "event_type", e)
        self.assertEqual(self.reason(frame(e=KeyError)), "event_type")

    def test_E(self):
        for bad in (KeyError, "1800000001000", 1800000001000.0, True, 1_000, 5_000_000_000_000):
            self.assertEqual(self.reason(frame(E=bad)), "E_type_or_range", bad)
        self.assertEqual(self.reason(frame().replace(b'"E":1800000001000', b'"E":null')), "E_type_or_range")

    def test_outer_symbol(self):
        for bad in ("ETHUSDT", "btcusdt", KeyError, None):
            self.assertEqual(self.reason(frame(s=bad)), "symbol_outer", bad)

    def test_k(self):
        for bad in (KeyError, [], "k", None):
            self.assertEqual(self.reason(frame(k=bad)), "k_not_object", bad)

    def test_inner_symbol(self):
        for bad in ("ETHUSDT", KeyError, None):
            self.assertEqual(self.reason(frame(k_s=bad)), "symbol_k", bad)

    def test_interval(self):
        for bad in ("5m", "1M", "1h", KeyError, 1):
            self.assertEqual(self.reason(frame(k_i=bad)), "interval", bad)

    def test_t(self):
        for bad in (KeyError, "1800000000000", 1800000000000.0, True, None, 5_000_000_000_000):
            self.assertEqual(self.reason(frame(k_t=bad, k_T=T0 + MIN - 1)), "t_type_or_range", bad)
        self.assertEqual(self.reason(frame(k_t=T0 + 1, k_T=T0 + MIN)), "t_not_minute")

    def test_T(self):
        for bad in (KeyError, T0 + MIN, T0 + MIN - 2, "x", 1800000059999.0, True):
            self.assertEqual(self.reason(frame(k_T=bad)), "T_mismatch", bad)

    def test_o_grammar(self):
        for bad in ("", "1e5", "01", ".5", "-1", "1.", " 1", "1 ", "٣", "0x1", "1" * 31, 100, 100.5, None, KeyError):
            self.assertEqual(self.reason(frame(k_o=bad)), "o_grammar", repr(bad))

    def test_o_zero(self):
        for bad in ("0", "0.0", "0.000"):
            self.assertEqual(self.reason(frame(k_o=bad)), "o_zero", bad)

    def test_x(self):
        for bad in ("false", 0, 1, None, KeyError):
            self.assertEqual(self.reason(frame(k_x=bad)), "x_type", repr(bad))

    def test_custom_expected_stream(self):
        self.assertTrue(K.parse_kline_frame(frame(form="COMBINED"), expected_stream="btcusdt@kline_1m")["ok"])
        self.assertEqual(self.reason(frame(form="COMBINED"), expected_stream="other"), "stream_name")


class CheckerGood(unittest.TestCase):
    def test_clean_minute(self):
        ev = journal([(frame(), T0 + 1100)])
        f, c, refs = K.candle_checks(ev, L)
        self.assertEqual(f, [])
        self.assertEqual(c, {T0: "USABLE"})
        self.assertEqual(refs, {T0: (3, "100.5")})

    def test_combined_form_and_two_minutes(self):
        ev = journal([(frame(form="COMBINED"), T0 + 1100), (frame(t=T0 + MIN, form="COMBINED"), T0 + MIN + 1100)])
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual((f, c), ([], {T0: "USABLE", T0 + MIN: "USABLE"}))

    def test_closing_message_may_arrive_after_the_minute(self):
        ev = journal([(frame(), T0 + 1100), (frame(x=True, E=T0 + MIN + 5), T0 + MIN + 40)])
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual(f, [])
        self.assertEqual(c, {T0: "USABLE"})

    def test_lag_unset_is_hard_and_nothing_is_usable(self):
        f, c, _ = K.candle_checks(journal([(frame(), T0 + 1100)]), None)
        self.assertEqual(f, [["CANDLE_LAG_UNSET", 0, f[0][2]]])
        self.assertEqual(c, {T0: "LAG_UNSET"})

    def test_empty(self):
        self.assertEqual(K.candle_checks([], L), ([], {}, {}))
        self.assertEqual(names(K.candle_checks([], None)[0]), ["CANDLE_LAG_UNSET"])


class CheckerLink(unittest.TestCase):
    def one(self, ev):
        f, c, _ = K.candle_checks(ev, L)
        return names(f), c[T0]

    def test_msg_seq_variants(self):
        for bad in (None, True, "2", 3, 99, 4, 1, 0, -1):          # absent-like, bool, str, self/forward/unknown, CONN line, line 0, negative
            ev = journal([(frame(), T0 + 1100, {"msg_seq": bad})])
            n, st = self.one(ev)
            self.assertEqual(n, ["CANDLE_LINK"], bad)
            self.assertEqual(st, "DEFECT_LINK")

    def test_forward_reference_to_a_real_msg(self):
        ev = journal([(frame(), T0 + 1100)])
        conn, msg, cand = ev[0], ev[1], ev[2]
        swapped = [conn, (2, dict(cand[1], seq=2, msg_seq=3)), (3, dict(msg[1], seq=3))]      # CANDLE (line 2) points at the MSG written AFTER it (line 3)
        f, c, _ = K.candle_checks(swapped, L)
        self.assertEqual(names(f), ["CANDLE_LINK"])
        self.assertEqual(c[T0], "DEFECT_LINK")

    def test_missing_msg_seq_key(self):
        ev = journal([(frame(), T0 + 1100)])
        del ev[2][1]["msg_seq"]
        self.assertEqual(self.one(ev), (["CANDLE_LINK"], "DEFECT_LINK"))

    def test_raw_differs(self):
        ev = journal([(frame(), T0 + 1100)])
        ev[1][1]["raw_b64"] = b64(frame(o="100.6"))
        ev[1][1]["sha256"] = hashlib.sha256(frame(o="100.6")).hexdigest()
        self.assertEqual(self.one(ev)[1], "DEFECT_LINK")

    def test_only_hash_differs(self):
        ev = journal([(frame(), T0 + 1100)])
        ev[1][1]["sha256"] = "0" * 64
        self.assertEqual(self.one(ev)[1], "DEFECT_LINK")

    def test_recv_differs(self):
        ev = journal([(frame(), T0 + 1100, {"recv_ms": T0 + 1101})])
        self.assertEqual(self.one(ev), (["CANDLE_LINK"], "DEFECT_LINK"))

    def test_connection_rules(self):
        base = journal([(frame(), T0 + 1100)])
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], feed="FORCE")), (["CANDLE_LINK"], "DEFECT_LINK"))
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], feed=None)), (["CANDLE_LINK"], "DEFECT_LINK"))
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], feed="kline")), (["CANDLE_LINK"], "DEFECT_LINK"))
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], close_ms=T0 + 1099)), (["CANDLE_LINK"], "DEFECT_LINK"))
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], close_ms=T0 + 1100))[0], [])          # closed exactly at receipt: still open
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], open_ms=T0 + 1101)), (["CANDLE_LINK"], "DEFECT_LINK"))
        self.assertEqual(self.one(journal([(frame(), T0 + 1100)], open_ms=T0 + 1100))[0], [])
        self.assertEqual(self.one(base)[0], [])

    def test_open_event_after_the_msg_is_not_an_open(self):
        ev = journal([(frame(), T0 + 1100)])
        ev = [ev[1], ev[2], ev[0]]                                                      # MSG, CANDLE, then CONN open: the open comes too late
        ev = [(i, dict(e, seq=i)) for i, (_, e) in enumerate(ev, 1)]
        ev[1][1]["msg_seq"] = 1
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual(names(f), ["CANDLE_LINK"])

    def test_first_open_event_defines_the_feed(self):
        ev = journal([(frame(), T0 + 1100)])
        ev.insert(1, (99, {"t": "CONN", "conn_id": 7, "ev": "open", "ms": T0 - 5 * MIN, "feed": "FORCE", "seq": 99, "rec_ms": 0}))
        self.assertEqual(self.one(ev)[0], [])                                           # the later open (other feed) is ignored, as for open_ms in 7.2

    def test_one_finding_per_name_per_record(self):
        ev = journal([(frame(o="100.5"), T0 + 1100, {"msg_seq": 99, "open": "1"})])
        f, _, _ = K.candle_checks(ev, L)
        self.assertEqual(names(f), ["CANDLE_FIELD_MISMATCH", "CANDLE_LINK"])


class CheckerParse(unittest.TestCase):
    def test_rest_array_as_candle(self):
        rest = b'[[1800000000000,"100.5","101","99","100","1",1800000059999,"1",1,"1","1","0"]]'
        ev = journal([(rest, T0 + 1100)])
        ev[2][1].update(open_time_ms=T0, open="100.5")
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual(names(f), ["CANDLE_PARSE"])
        self.assertEqual(c[T0], "DEFECT_PARSE")

    def test_invalid_base64(self):
        ev = journal([(frame(), T0 + 1100)])
        ev[2][1]["raw_b64"] = "!!!"
        ev[1][1]["raw_b64"] = "!!!"
        f, _, _ = K.candle_checks(ev, L)
        self.assertEqual(names(f), ["CANDLE_PARSE"])

    def test_wrong_symbol_interval_stream(self):
        for raw in (frame(s="ETHUSDT"), frame(k_i="5m"), frame(form="COMBINED").replace(b"kline_1m", b"kline_5m")):
            ev = journal([(raw, T0 + 1100)])
            ev[2][1].update(open_time_ms=T0, open="100.5")
            self.assertEqual(names(K.candle_checks(ev, L)[0]), ["CANDLE_PARSE"])

    def test_field_mismatch(self):
        for ov in ({"open": "100.6"}, {"open_time_ms": T0 + MIN}, {"open": "100.50"}):
            ev = journal([(frame(), T0 + 1100, ov)])
            f, c, _ = K.candle_checks(ev, L)
            self.assertIn("CANDLE_FIELD_MISMATCH", names(f), ov)
            self.assertTrue(c[ev[2][1]["open_time_ms"]].startswith("DEFECT_"))


class CheckerLiveness(unittest.TestCase):
    def test_not_live_boundary_no_clock(self):
        n = lambda recv, **kw: names(K.candle_checks(journal([(frame(E=T0 + 100), recv)], **kw), L)[0])
        self.assertEqual(n(T0 - 250), [])
        self.assertEqual(n(T0 - 251), ["CANDLE_NOT_LIVE"])

    def test_not_live_with_clock_offset(self):
        n = lambda recv, clock: names(K.candle_checks(journal([(frame(E=T0 + 100), recv)], clock=clock), L)[0])
        self.assertEqual(n(T0 - 150, 100), [])              # local clock 100 ms ahead: exchange time = recv - 100 = T0 - 250; +250 = T0
        self.assertEqual(n(T0 - 151, 100), ["CANDLE_NOT_LIVE"])
        self.assertEqual(n(T0 - 350, -100), [])             # local clock behind: exchange time = recv + 100; + 250 = T0
        self.assertEqual(n(T0 - 351, -100), ["CANDLE_NOT_LIVE"])

    def test_not_live_makes_the_minute_unusable(self):
        f, c, _ = K.candle_checks(journal([(frame(E=T0 + 100), T0 - 5000)]), L)
        self.assertEqual(c[T0], "DEFECT_NOT_LIVE")

    def test_clock_event_after_the_candle_is_not_used(self):
        ev = journal([(frame(E=T0 + 100), T0 - 200)])
        ev.append((len(ev) + 1, {"t": "CLOCK", "offset_ms": 100, "ms": T0, "seq": len(ev) + 1, "rec_ms": 0}))
        self.assertEqual(K.candle_checks(ev, L)[0], [])


class CheckerUsability(unittest.TestCase):
    def state(self, raw=None, recv=None, L_=L, **kw):
        raw = frame() if raw is None else raw
        f, c, _ = K.candle_checks(journal([(raw, T0 + 1100 if recv is None else recv)], **kw), L_)
        return c[T0], names(f)

    def test_clock_beyond_bound(self):
        self.assertEqual(self.state(clock=251), ("CLOCK", []))
        self.assertEqual(self.state(clock=-251), ("CLOCK", []))
        self.assertEqual(self.state(clock=250)[0], "USABLE")
        self.assertEqual(self.state(clock=-250)[0], "USABLE")

    def test_E_outside_the_candle(self):
        self.assertEqual(self.state(frame(E=T0 - 1), T0 + 100), ("E_RANGE", []))
        self.assertEqual(self.state(frame(E=T0 + MIN), T0 + MIN - 400), ("E_RANGE", []))
        self.assertEqual(self.state(frame(E=T0), T0 + 100)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + MIN - 1), T0 + MIN - 251)[0], "USABLE")

    def test_late_minute_boundary(self):
        self.assertEqual(self.state(frame(E=T0 + MIN - 1), T0 + MIN - 1 - 250, L_=10**9)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + MIN - 1), T0 + MIN - 1 - 249, L_=10**9)[0], "LATE_MINUTE")
        self.assertEqual(self.state(frame(E=T0 + MIN - 1), T0 + MIN + 30_000, L_=10**9)[0], "LATE_MINUTE")

    def test_late_minute_with_clock(self):
        self.assertEqual(self.state(frame(E=T0 + 10), T0 + MIN - 1 - 250 + 100, clock=100, L_=10**9)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + 10), T0 + MIN - 1 - 249 + 100, clock=100, L_=10**9)[0], "LATE_MINUTE")

    def test_negative_lag(self):
        self.assertEqual(self.state(frame(E=T0 + 5000), T0 + 5000 - 250)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + 5000), T0 + 5000 - 251)[0], "LAG_NEGATIVE")

    def test_max_lag(self):
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + L)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + L + 1)[0], "LAG_TOO_OLD")
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + 3000, L_=2999)[0], "LAG_TOO_OLD")
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + 3000, L_=3000)[0], "USABLE")

    def test_lag_with_clock(self):
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + 200 + L, clock=200)[0], "USABLE")
        self.assertEqual(self.state(frame(E=T0 + 1000), T0 + 1000 + 200 + L + 1, clock=200)[0], "LAG_TOO_OLD")

    def test_usability_creates_no_finding(self):
        for kw in ({"clock": 300}, {"raw": frame(E=T0 - 1), "recv": T0 + 100}):
            self.assertEqual(self.state(**kw)[1], [])


class CheckerReferenceRule(unittest.TestCase):
    def test_bad_first_record_cannot_be_rescued(self):
        ev = journal([(frame(), T0 + 1100, {"msg_seq": 99}), (frame(), T0 + 1300)])
        f, c, refs = K.candle_checks(ev, L)
        self.assertEqual(names(f), ["CANDLE_LINK"])
        self.assertEqual(c[T0], "DEFECT_LINK")
        self.assertEqual(refs[T0][0], 3)

    def test_late_first_record_cannot_be_rescued(self):
        ev = journal([(frame(E=T0 + 100), T0 + MIN + 10), (frame(), T0 + MIN + 20)])
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual(c[T0], "LATE_MINUTE")

    def test_later_good_record_does_not_replace_the_reference(self):
        ev = journal([(frame(), T0 + 1100), (frame(x=True, E=T0 + MIN), T0 + MIN + 10)])
        _, c, refs = K.candle_checks(ev, L)
        self.assertEqual((c[T0], refs[T0][0]), ("USABLE", 3))

    def test_conflict_once_per_minute(self):
        ev = journal([(frame(o="100.5"), T0 + 1100), (frame(o="100.6"), T0 + 1300), (frame(o="100.7"), T0 + 1500)])
        f, c, _ = K.candle_checks(ev, L)
        conflicts = [x for x in f if x[0] == "CANDLE_CONFLICT"]
        self.assertEqual([x[1] for x in conflicts], [5])      # the first record whose open differs from the reference
        self.assertEqual(c[T0], "USABLE")                                               # the reference keeps its state; the journal fails by the hard finding

    def test_same_open_repeated_is_no_conflict(self):
        ev = journal([(frame(), T0 + 1100), (frame(), T0 + 1300)])
        self.assertEqual(K.candle_checks(ev, L)[0], [])

    def test_later_defective_record_is_reported_but_keeps_reference_state(self):
        ev = journal([(frame(), T0 + 1100), (frame(), T0 + 1300, {"msg_seq": 99})])
        f, c, _ = K.candle_checks(ev, L)
        self.assertEqual((names(f), c[T0]), (["CANDLE_LINK"], "USABLE"))


class OutcomeLink(unittest.TestCase):
    def setUp(self):
        _, self.c, self.refs = K.candle_checks(journal([(frame(), T0 + 1100)]), L)

    def test_ok(self):
        self.assertFalse(K.outcome_unlinked(10, T0, "100.5", self.refs, self.c))

    def test_failures(self):
        self.assertTrue(K.outcome_unlinked(10, T0 + MIN, "100.5", self.refs, self.c))   # no candle
        self.assertTrue(K.outcome_unlinked(3, T0, "100.5", self.refs, self.c))          # reference CANDLE is line 3: written at the outcome line
        self.assertTrue(K.outcome_unlinked(2, T0, "100.5", self.refs, self.c))          # ... or after it
        self.assertFalse(K.outcome_unlinked(4, T0, "100.5", self.refs, self.c))
        self.assertTrue(K.outcome_unlinked(10, T0, "100.50", self.refs, self.c))        # string comparison
        self.assertTrue(K.outcome_unlinked(10, T0, "100.6", self.refs, self.c))
        c = dict(self.c)
        c[T0] = "LATE_MINUTE"
        self.assertTrue(K.outcome_unlinked(10, T0, "100.5", self.refs, c))              # unusable minute

    def test_lag_unset_blocks_every_outcome(self):
        _, c, refs = K.candle_checks(journal([(frame(), T0 + 1100)]), None)
        self.assertTrue(K.outcome_unlinked(10, T0, "100.5", refs, c))


if __name__ == "__main__":
    unittest.main(verbosity=1)
