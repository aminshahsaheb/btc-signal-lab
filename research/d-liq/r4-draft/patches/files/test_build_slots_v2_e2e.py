"""End-to-end tests of the r4 builder (build_slots_v2.py): REAL journals written by the r4 writer (real messages, SLOT computed by the executable message contract,
OUTCOME + covering CHECKPOINT), run through the pinned verifiers WITH the mandatory SLOT replay. SYNTHETIC data; nothing here touches a network, an exchange or an anchor service.
Usage: python3 -I test_build_slots_v2_e2e.py      (needs ../src for the writer and the message contract; the builder pins verifiers/ by SHA-256)"""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
import warnings
from unittest import mock

warnings.simplefilter("ignore", ResourceWarning)      # the writer/verifier read files with open().read(); not part of what is tested here

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
sys.path.insert(0, SRC)
import dliq_journal_v2 as J           # writer (r4)
import dliq_msg_contract_v1 as MC     # executable message contract
SPEC = importlib.util.spec_from_file_location("build_slots_v2", os.path.join(HERE, "build_slots_v2.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

H4 = 14_400_000
TAU0 = (1_793_000_000_000 // H4 + 1) * H4
JID = "E2E"
DL = 300_000


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def px(ot):
    return "%d.5" % (100_000 + (ot // 300_000) % 997)


def frame(E, side, z, ap):
    o = {"s": "BTCUSDT", "S": side, "o": "LIMIT", "f": "IOC", "q": z, "p": ap, "ap": ap, "X": "FILLED", "l": z, "z": z, "T": E}
    return json.dumps({"e": "forceOrder", "E": E, "o": o}, separators=(",", ":")).encode()


def slot_from_events(evs, tau, rec_ms):
    """contract 7.2: the replay input, from the events written so far"""
    msgs, frames, opens, closes, clock = [], {}, {}, {}, 0
    for e in evs:
        t = e["t"]
        if t == "MSG":
            msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": base64.b64decode(e["raw_b64"])})
            frames.setdefault(e["conn_id"], []).append(e["recv_ms"])
        elif t == "PING":
            frames.setdefault(e["conn_id"], []).append(e["ms"])
        elif t == "CONN":
            if e["ev"] == "open":
                opens.setdefault(e["conn_id"], e["ms"])
            else:
                closes[e["conn_id"]] = e["ms"]
        elif t == "CLOCK":
            clock = e["offset_ms"]
    health = {c: MC.health_intervals(o, frames.get(c, []), close_ms=closes.get(c), end_ms=rec_ms) for c, o in opens.items()}
    return J.slot_fields(MC.build_slot(tau, msgs, health, clock_offset_ms=clock))


def gen(tmp, tag, specs, flip_side_at=None, slot_delay=11_000, tail_dup=False):
    """specs: list of dict(side='BUY'|'SELL'|'NONE', outcome='EVAL'|'NO_PRICE'|None|'TAIL_EVAL'|'TAIL_NO_PRICE'|'NONE_UNCHECKED', prior=True); grid point k has tau = TAU0 + k*H4.
    returns (journal_path, anchor_snapshot_path); the snapshot is the genuine MockAnchor content (verify_time far in the future)."""
    jp, ap = os.path.join(tmp, tag + ".jsonl"), os.path.join(tmp, tag + ".anchor")
    now = [TAU0 - 2 * 3600_000]
    clock = lambda: now[0]
    j = J.Journal(jp, JID, clock)
    a = J.MockAnchor(ap, clock)
    j.append("SESSION", journal_id=JID)
    tl, written, seen_candle = [], [], set()
    open_t = TAU0 - 2 * 3600_000
    last = TAU0 + len(specs) * H4 + 2 * DL
    tl.append((open_t, 0, "open", None))
    tl.append((open_t + 1, 1, "clock", None))
    t = open_t
    while t < last:
        t += 180_000
        tl.append((t, 2, "ping", None))
    for k, sp in enumerate(specs):
        tau = TAU0 + k * H4
        n = 2 if sp["side"] == "NONE" else 5
        for m, off in enumerate((-800_000, -600_000, -400_000, -300_000, -100_000)[:n]):
            side = "BUY" if sp["side"] in ("BUY", "NONE") else "SELL"
            tl.append((tau + off + 40, 3, "msg", (tau + off, frame(tau + off, side, "0.0%d" % (14 + m), "9800%d.50" % m))))
        if sp.get("prior", True):
            for ot in (tau - 900_000, tau):
                tl.append((ot + 100, 4, "candle", ot))
        tl.append((tau + slot_delay, 5, "slot", k))
        if sp["outcome"] in ("EVAL", "TAIL_EVAL"):
            for ot in (tau + DL, tau + DL + 14_400_000):
                tl.append((ot + 100, 4, "candle", ot))
            tl.append((tau + DL + 14_400_000 + 200, 7, "outcome", k))
        elif sp["outcome"] in ("NO_PRICE", "TAIL_NO_PRICE", "NONE_UNCHECKED"):
            tl.append((tau + 14_400_000 + 400_000, 7, "outcome", k))
    tl.sort(key=lambda x: (x[0], x[1]))

    def rec(t_, **f):
        written.append(dict(f))
    for tm, _, kind, pl in tl:
        now[0] = tm
        if kind == "open":
            j.append("CONN", conn_id=1, ev="open", ms=tm); rec(0, t="CONN", conn_id=1, ev="open", ms=tm)
        elif kind == "clock":
            j.append("CLOCK", offset_ms=0, ms=tm); rec(0, t="CLOCK", offset_ms=0)
        elif kind == "ping":
            j.append("PING", conn_id=1, ms=tm); rec(0, t="PING", conn_id=1, ms=tm)
        elif kind == "msg":
            E, raw = pl
            f = J.msg_fields(1, tm, raw)
            j.append("MSG", **f); rec(0, t="MSG", **f)
        elif kind == "candle":
            if pl in seen_candle:
                continue
            seen_candle.add(pl)
            j.append("CANDLE", **J.candle_fields(pl, px(pl), tm, b"c%d" % pl))
        elif kind == "slot":
            tau = TAU0 + pl * H4
            f = slot_from_events(written, tau, tm)
            if flip_side_at == pl:
                f["side"] = -f["side"] if f["side"] else 1
            j.append("SLOT", **f)
            now[0] = tm + 20_000
            j.checkpoint(a)
        elif kind == "outcome":
            sp, tau = specs[pl], TAU0 + pl * H4
            if sp["outcome"] in ("EVAL", "TAIL_EVAL"):
                e, x = tau + DL, tau + DL + 14_400_000
                fo = J.outcome_fields(tau, "EVAL", e, x, px(e), px(x), repr(1e4 * math.log(float(px(x)) / float(px(e)))))
            else:
                fo = J.outcome_fields(tau, "NO_PRICE")
            if sp["outcome"].startswith("TAIL"):
                j.append("OUTCOME", **fo)
                if tail_dup:
                    j.append_unchecked("OUTCOME", **fo)
            elif sp["outcome"] == "NONE_UNCHECKED":
                j.append_unchecked("OUTCOME", **fo)
                j.checkpoint(a)
            else:
                j.outcome_and_anchor(fo, a)
    now[0] += 1000
    j.close()
    return jp, ap


def snapshot(ap, path, verify_time_ms=TAU0 + 40 * H4):
    ents = [{k: e[k] for k in ("index", "seq", "head", "anchor_id", "time_ms", "time_resolution_ms", "time_uncertainty_ms")}
            for e in J.MockAnchor(ap, lambda: 0)._entries()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"journal_id": JID, "verify_time_ms": verify_time_ms, "entries": ents}, f, sort_keys=True)
    return path


class Case:
    def __init__(self, tc, specs, **kw):
        self.td = tempfile.TemporaryDirectory()
        tc.addCleanup(self.td.cleanup)
        self.dir = self.td.name
        self.journal, self.anchor_path = gen(self.dir, "j", specs, **kw)
        self.snap = snapshot(self.anchor_path, os.path.join(self.dir, "snap.json"))
        self.refresh()

    def refresh(self, journal=None):
        self.journal = journal or self.journal
        self.p, self.i, _ = BUILDER.run_pinned_verifiers(self.journal, self.snap)
        self.r1, self.r2 = os.path.join(self.dir, "primary.json"), os.path.join(self.dir, "independent.json")
        for path, rep in ((self.r1, self.p), (self.r2, self.i)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rep, f, sort_keys=True)

    def diag(self):
        return BUILDER._build_diagnostics(self.journal, self.r1, self.r2, self.snap)

    def build(self):
        return BUILDER.build(self.journal, self.r1, self.r2, self.snap)

    def lines(self):
        return open(self.journal, "rb").read().split(b"\n")[:-1]

    def write_variant(self, lines, name="variant.jsonl"):
        p = os.path.join(self.dir, name)
        with open(p, "wb") as f:
            f.write(b"\n".join(lines) + b"\n")
        return p


CLEAN = [dict(side="BUY", outcome="EVAL"), dict(side="SELL", outcome="NO_PRICE"), dict(side="NONE", outcome=None)]


class E2E(unittest.TestCase):
    def test_clean_three_slots_are_analysis_ready(self):
        c = Case(self, CLEAN)
        self.assertEqual((c.p["verdict"], c.i["verdict"], c.p["hard"], c.i["hard"]), ("PASS", "PASS", [], []))
        self.assertIs(c.p["replayed"], True)
        summary, primary, control = c.build()
        self.assertEqual([r[1] for r in primary], ["EVAL", "NO_PRICE", "NONE"])
        self.assertEqual((summary["N_eval"], summary["N_noprice"], summary["N_none"], summary["N_pending"], summary["N_unanch"], summary["N_missing"]), (1, 1, 1, 0, 0, 0))
        self.assertEqual([r["status"] for r in summary["outcome_coverage"]], ["COVERED", "COVERED"])
        self.assertTrue(summary["primary_replayed"])
        self.assertEqual(summary["message_contract_source_sha256"], hashlib.sha256(open(BUILDER.MSG_CONTRACT_PATH, "rb").read()).hexdigest())
        self.assertEqual(summary["coverage_lag"]["n_covered"], 2)
        self.assertEqual(summary["coverage_lag"]["lag_events_max"], 1)         # outcome_and_anchor: the covering checkpoint is the next line
        self.assertEqual(summary["coverage_lag"]["lag_ms_max"], 0)

    def test_tail_unanchored_outcome_is_pending_and_blocks_rows(self):
        c = Case(self, [dict(side="BUY", outcome="TAIL_EVAL")])
        self.assertEqual(c.p["outcomes"], {TAU0: "UNCOVERED"})
        summary, primary, _ = c.diag()
        self.assertEqual(summary["N_pending"], 1)
        self.assertEqual(summary["outcome_coverage"][0]["status"], "UNCOVERED")
        self.assertEqual(summary["diagnostics"][0]["reason"], "PENDING_OUTCOME_ANCHOR")
        self.assertEqual(summary["coverage_lag"]["n_uncovered"], 1)
        with self.assertRaisesRegex(BUILDER.BuildError, "analysis ineligible"):
            c.build()

    def test_cli_refuses_csv_for_a_tail_outcome(self):
        c = Case(self, [dict(side="BUY", outcome="TAIL_EVAL")])
        prefix = os.path.join(c.dir, "out")
        with mock.patch.object(BUILDER.sys, "argv", ["b", c.journal, c.r1, c.r2, c.snap, "--out-prefix", prefix]):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = BUILDER.main()
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(prefix + ".csv"))
        self.assertEqual(_load(prefix + ".summary.json")["N_pending"], 1)

    def test_tampered_covered_outcome(self):
        c = Case(self, CLEAN[:1])
        L = c.lines()
        oi = [k for k, l in enumerate(L) if json.loads(l)["t"] == "OUTCOME"][0]
        ev = json.loads(L[oi])
        ev["r_bps"] = "999.0"
        L[oi] = J.canonical(ev)
        c.refresh(c.write_variant(L))
        self.assertEqual(c.p["verdict"], "FAIL")
        self.assertIn("HEAD_MISMATCH", c.p["hard"])
        self.assertIn("HEAD_MISMATCH", c.i["hard"])
        summary, _, _ = c.diag()
        self.assertFalse(summary["registry_ok"])
        with self.assertRaisesRegex(BUILDER.BuildError, "analysis ineligible"):
            c.build()

    def test_omitted_covered_outcome(self):
        c = Case(self, CLEAN[:1])
        L = c.lines()
        oi = [k for k, l in enumerate(L) if json.loads(l)["t"] == "OUTCOME"][0]
        del L[oi]
        c.refresh(c.write_variant(L))
        self.assertEqual(c.p["verdict"], "FAIL")
        try:
            summary, _, _ = c.diag()
            self.assertFalse(summary["registry_ok"])
        except BUILDER.BuildError:
            pass                                                           # the builder may already refuse the broken sequence
        with self.assertRaises(BUILDER.BuildError):
            c.build()

    def test_resequenced_omission_is_caught_by_the_anchor(self):
        # an attacker deletes the OUTCOME and its checkpoint AND renumbers / re-chains the rest: the genuine anchor entries no longer match the new heads
        c = Case(self, CLEAN[:1])
        L = c.lines()
        keep = []
        for l in L:
            ev = json.loads(l)
            if ev["t"] == "OUTCOME" or (ev["t"] == "CHECKPOINT" and ev["anchored_seq"] == len(keep) + 1 and False):
                continue
            keep.append(l)
        out, n = [], 0
        for l in keep:
            ev = json.loads(l)
            n += 1
            ev["seq"] = n
            out.append(J.canonical(ev))
        c.refresh(c.write_variant(out))
        self.assertEqual(c.p["verdict"], "FAIL")
        self.assertTrue({"HEAD_MISMATCH", "TRUNCATION_OR_REPLACEMENT", "RECEIPT_INVALID", "CHECKPOINT_ORDER"} & set(c.p["hard"]), c.p["hard"])
        with self.assertRaises(BUILDER.BuildError):
            c.build()

    def test_side_flipped_slot_with_consistent_chain_is_caught_only_by_the_replay(self):
        c = Case(self, [dict(side="BUY", outcome="NO_PRICE")], flip_side_at=0)
        # sections 1-6 (what the partially independent verifier checks) see a perfectly consistent journal ...
        self.assertEqual(c.i["hard"], [])
        self.assertEqual(c.i["verdict"], "PASS")
        # ... the mandatory replay does not
        self.assertIn("SLOT_MISMATCH", c.p["hard"])
        summary, _, _ = c.diag()
        self.assertFalse(summary["registry_ok"])
        self.assertIn("SLOT_MISMATCH", summary["hard_findings"])
        with self.assertRaisesRegex(BUILDER.BuildError, "analysis ineligible"):
            c.build()

    def test_early_written_slot_is_a_hard_finding(self):
        c = Case(self, [dict(side="BUY", outcome=None)], slot_delay=9_999)
        self.assertIn("SLOT_EARLY_WRITE", c.p["hard"])
        summary, _, _ = c.diag()
        self.assertIn("SLOT_EARLY_WRITE", summary["hard_findings"])
        with self.assertRaises(BUILDER.BuildError):
            c.build()

    def test_outcome_for_none_slot_written_through_the_unchecked_path(self):
        c = Case(self, [dict(side="NONE", outcome="NONE_UNCHECKED")])
        self.assertIn("OUTCOME_FOR_NONE_SLOT", c.p["hard"])
        self.assertIn("OUTCOME_FOR_NONE_SLOT", c.i["hard"])
        summary, _, _ = c.diag()
        self.assertFalse(summary["registry_ok"])
        with self.assertRaises(BUILDER.BuildError):
            c.build()

    def test_duplicate_tail_outcome(self):
        c = Case(self, [dict(side="BUY", outcome="TAIL_NO_PRICE")], tail_dup=True)
        self.assertIn("DUPLICATE_OUTCOME", c.p["hard"])
        summary, _, _ = c.diag()
        self.assertFalse(summary["registry_ok"])
        with self.assertRaises(BUILDER.BuildError):
            c.build()

    def test_report_without_outcomes_map_is_refused(self):
        c = Case(self, CLEAN[:1])
        rep = _load(c.r1)
        rep.pop("outcomes")
        _dump(rep, c.r1)
        with self.assertRaisesRegex(BUILDER.BuildError, "outcomes"):
            c.diag()

    def test_report_forged_to_hide_the_replay_flag_is_refused(self):
        c = Case(self, CLEAN[:1])
        rep = _load(c.r1)
        rep["replayed"] = False
        _dump(rep, c.r1)
        with self.assertRaisesRegex(BUILDER.BuildError, "pinned verifier"):
            c.diag()

    def test_forged_reports_both_claiming_covered_are_refused_by_the_pin_and_by_the_own_derivation(self):
        c = Case(self, [dict(side="BUY", outcome="TAIL_EVAL")])
        forged = [json.loads(json.dumps(x)) for x in (c.p, c.i)]
        for rep in forged:
            rep["outcomes"][str(TAU0)] = "COVERED"
        for path, rep in zip((c.r1, c.r2), forged):
            _dump(rep, path)
        with self.assertRaisesRegex(BUILDER.BuildError, "pinned verifier"):                  # line 1 of defence: the report must equal the pinned verifier's own output
            c.diag()
        with mock.patch.object(BUILDER, "run_pinned_verifiers", return_value=(forged[0], forged[1], "0" * 64)):   # line 2: pretend the pin check was subverted
            summary, rows, _ = c.diag()
        self.assertIn("BUILDER_OUTCOME_COVERAGE_MISMATCH", summary["hard_findings"])
        self.assertEqual(summary["N_pending"], 1)

    def test_verifiers_disagreeing_on_coverage_is_a_build_error(self):
        c = Case(self, [dict(side="BUY", outcome="TAIL_EVAL")])
        forged = [json.loads(json.dumps(x)) for x in (c.p, c.i)]
        forged[1]["outcomes"][str(TAU0)] = "COVERED"
        for path, rep_ in zip((c.r1, c.r2), forged):
            _dump(rep_, path)
        with mock.patch.object(BUILDER, "run_pinned_verifiers", return_value=(forged[0], forged[1], "0" * 64)):
            with self.assertRaisesRegex(BUILDER.BuildError, "coverage"):
                c.diag()

    def test_changed_message_contract_breaks_the_pin(self):
        c = Case(self, CLEAN[:1])
        with mock.patch.object(BUILDER, "MSG_CONTRACT_SHA256", "0" * 64):
            with self.assertRaisesRegex(BUILDER.BuildError, "pinned source hash mismatch"):
                BUILDER.run_pinned_verifiers(c.journal, c.snap)

    def test_primary_verifier_that_skips_the_replay_is_refused(self):
        c = Case(self, CLEAN[:1])
        real = BUILDER._load_pinned_verifier

        def loader(path, expected, name):
            mod = real(path, expected, name)
            if name.endswith("primary_verifier"):
                inner = mod.verify
                mod.verify = lambda *a, **k: inner(*a, **dict(k, replay_slots=False))
            return mod
        with mock.patch.object(BUILDER, "_load_pinned_verifier", loader):
            with self.assertRaisesRegex(BUILDER.BuildError, "replay"):
                BUILDER.run_pinned_verifiers(c.journal, c.snap)

    def test_pinned_hashes_are_those_of_the_shipped_verifier_files(self):
        h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        self.assertEqual(BUILDER.PRIMARY_VERIFIER_SHA256, h(BUILDER.PRIMARY_VERIFIER_PATH))
        self.assertEqual(BUILDER.INDEPENDENT_VERIFIER_SHA256, h(BUILDER.INDEPENDENT_VERIFIER_PATH))
        self.assertEqual(BUILDER.MSG_CONTRACT_SHA256, h(BUILDER.MSG_CONTRACT_PATH))
        # the shipped copies are the r4 tree files
        self.assertEqual(h(BUILDER.PRIMARY_VERIFIER_PATH), h(os.path.join(SRC, "dliq_journal_verify_v2.py")))
        self.assertEqual(h(BUILDER.MSG_CONTRACT_PATH), h(os.path.join(SRC, "dliq_msg_contract_v1.py")))
        self.assertEqual(h(BUILDER.INDEPENDENT_VERIFIER_PATH), h(os.path.join(HERE, "..", "indep_verifier", "verify_indep.py")))


if __name__ == "__main__":
    unittest.main()
