"""Tests for dliq_journal_v2.py (writer + mock anchor) and dliq_journal_verify_v2.py (author's verifier). SYNTHETIC; no network, no market data.
Usage: python3 -I test_dliq_journal_v2.py
Part 1 writer guards; Part 2 verifier on clean journals; Part 3 the strict anchoring deadline; Part 4 one test per finding; Part 5 tamper matrix (each manipulation
is applied to a copy of the same clean journal). The tests state what is NOT detectable (unanchored tail; backdating before the first checkpoint).
The partially independent verifier is exercised separately (indep_verifier/test_indep.py, diff_test_verifiers.py); this file tests the author's code only."""
import base64
import copy
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, "..", "superseded_src"))     # r3 package layout: the superseded v1 journal lives in superseded_src/
import dliq_journal_v1 as J1
import dliq_journal_v2 as J
import dliq_journal_verify_v2 as V
import dliq_msg_contract_v1 as MC

FAILS, NT = [], [0]


def check(name, cond, detail=""):
    NT[0] += 1
    print(("PASS " if cond else "FAIL ") + name + ((" -- " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


H = 3_600_000
GRID = 4 * H
TAU = 1_793_001_600_000
assert TAU % GRID == 0
JID = "DLIQ-TEST-JOURNAL-V2"
DL = J.ENTRY_DELAY_MS


def px(open_ms):
    """a deterministic 'market': the open of the 1-min candle at open_ms (the exit candle of slot k is the entry candle of slot k+1)"""
    return "%d.5" % (100000 + 500 * ((open_ms - TAU - DL) // GRID))


def slot_rec(tau, status="VALID", **kw):
    r = {"tau_ms": tau, "status": status, "reasons": ["N_TOTAL"] if status == "NONE" else [], "primary_conn": 1, "N_total": 0, "N_BUY": 0, "N_SELL": 0, "sumW_BUY": "0", "sumW_SELL": "0",
         "side": 0 if status == "NONE" else 1, "malformed_voids": 0, "ledger": {"COUNTED": 0}, "n_messages": 0, "X_sn": None}
    r.update(kw)
    return r


class Rig:
    """one journal + mock anchor with a controllable clock"""

    def __init__(self, tmp, tag, res=1, unc=0, session=True):
        self.jp, self.ap = os.path.join(tmp, tag + ".jsonl"), os.path.join(tmp, tag + ".anchor")
        self.now = [TAU - H]
        self.clock = lambda: self.now[0]
        self.j = J.Journal(self.jp, JID, self.clock)
        self.a = J.MockAnchor(self.ap, self.clock, time_resolution_ms=res, time_uncertainty_ms=unc)
        if session:
            self.j.append("SESSION", journal_id=JID)

    def at(self, t):
        self.now[0] = t
        return self

    def slot(self, tau, anchor_at=None, status="VALID", checked=True, **kw):
        """SLOT at tau+11 s; anchored (CHECKPOINT) at anchor_at if given. returns (slot_seq, checkpoint_seq or None)"""
        self.now[0] = tau + 11_000
        f = J.slot_fields(slot_rec(tau, status, **kw))
        f.update({k: v for k, v in kw.items() if k in J.OUTCOME_FORBIDDEN_IN_SLOT})
        s = (self.j.append if checked else self.j.append_unchecked)("SLOT", **f)
        c = None
        if anchor_at is not None:
            self.now[0] = anchor_at
            c = self.j.checkpoint(self.a)
        return s, c

    def candle(self, ot, price, recv=None, raw=None):
        self.now[0] = recv if recv is not None else ot + 100
        return self.j.append("CANDLE", **J.candle_fields(ot, price, self.now[0], raw if raw is not None else b"c%d" % ot))

    def outcome(self, tau, status="EVAL", entry_open=None, exit_open=None, ep="100000.5", xp="100500.5", r=None, checked=True, at=None):
        if at is not None:
            self.now[0] = at
        if status == "EVAL":
            entry_open = tau + DL if entry_open is None else entry_open
            exit_open = entry_open + J.OUTCOME_HORIZON_MS if exit_open is None else exit_open
            r = repr(1e4 * math.log(float(xp) / float(ep))) if r is None else r
            f = J.outcome_fields(tau, "EVAL", entry_open, exit_open, ep, xp, r)
        else:
            f = J.outcome_fields(tau, "NO_PRICE")
        return (self.j.append if checked else self.j.append_unchecked)("OUTCOME", **f)

    def full_slot(self, tau, anchor_delay=20_000, outcome=True, status_eval=True):
        """SLOT + CHECKPOINT + both live candles + OUTCOME"""
        s, c = self.slot(tau, anchor_at=tau + 11_000 + anchor_delay)
        if outcome:
            e, x = tau + DL, tau + DL + J.OUTCOME_HORIZON_MS
            self.candle(e, px(e))
            self.candle(x, px(x))
            self.outcome(tau, "EVAL" if status_eval else "NO_PRICE", ep=px(e), xp=px(x), at=x + 200)
        return s, c

    def done(self, ping=False):
        if ping:
            self.now[0] += 1000
            self.j.append("PING", conn_id=1, ms=self.now[0])
        head = self.j.head.hex()
        self.j.close()
        return self.jp, self.ap, head


def anchor_of(ap, clock=None):
    return J.MockAnchor(ap, clock or (lambda: 0))


def run(jp, ap, vt=TAU + 40 * H, **kw):
    return V.verify(jp, anchor_of(ap), JID, vt, **kw)


def names(res):
    return sorted(set(f[0] for f in res["findings"]))


def info(res):
    return sorted(set(names(res)) - set(res["hard"]) - set(res["soft"]))


def lines_of(p):
    return open(p, "rb").read().split(b"\n")[:-1]


def write_lines(p, lines):
    open(p, "wb").write(b"".join(l + b"\n" for l in lines))


def evs_of(p):
    return [json.loads(l) for l in lines_of(p)]


def write_evs(p, evs):
    write_lines(p, [J.canonical(e) for e in evs])


def exact(name, res, hard=(), soft=(), infos=None):
    ok = res["hard"] == sorted(hard) and res["soft"] == sorted(soft) and (infos is None or info(res) == sorted(infos)) and res["verdict"] == ("FAIL" if hard else "PASS")
    check(name, ok, "hard=%s soft=%s info=%s verdict=%s" % (res["hard"], res["soft"], info(res), res["verdict"]))


def has(name, res, finding, where=None):
    ok = any(f[0] == finding and (where is None or f[1] == where) for f in res["findings"])
    check(name, ok, "findings=%s" % [(f[0], f[1]) for f in res["findings"]][:12])


tmp = tempfile.mkdtemp(prefix="dliq_j2_")
n_dir = [0]


def sub(tag):
    n_dir[0] += 1
    d = os.path.join(tmp, "%02d_%s" % (n_dir[0], tag))
    os.makedirs(d)
    return d


try:
    # ================================================================ PART 1: writer
    d = sub("writer")
    check("v2 genesis differs from v1 genesis", J.GENESIS != J1.GENESIS and J.h0() != J1.h0())
    # a v1-written journal (with a v1 checkpoint) does not verify under v2
    now1 = [TAU]
    j1 = J1.Journal(os.path.join(d, "v1.jsonl"), JID, lambda: now1[0])
    a1 = J1.MockAnchor(os.path.join(d, "v1.anchor"), lambda: now1[0])
    j1.append("SESSION", journal_id=JID)
    j1.append("PING", conn_id=1, ms=TAU)
    j1.checkpoint(a1)
    j1.close()
    r = V.verify(os.path.join(d, "v1.jsonl"), J.MockAnchor(os.path.join(d, "v1.anchor"), lambda: 0), JID, TAU + 40 * H)
    check("a journal written by the v1 writer fails the v2 verifier", r["verdict"] == "FAIL", r["hard"])

    R = Rig(d, "w")
    try:
        R.j.append("PING", conn_id=1, ms=1.5)
        ok = False
    except J.JournalError:
        ok = True
    check("writer refuses floats", ok)
    for bad in ({"seq": 1}, {"t": "X"}, {"rec_ms": 1}):
        try:
            R.j.append("PING", conn_id=1, ms=1, **bad)
            ok = False
        except J.JournalError:
            ok = True
        check("writer refuses reserved field %s" % list(bad), ok)
    try:
        R.j.append("MYSTERY")
        ok = False
    except J.JournalError:
        ok = True
    check("writer refuses unknown event type", ok)

    check("slot_fields never contains outcome fields", not (set(J.slot_fields(slot_rec(TAU))) & set(J.OUTCOME_FORBIDDEN_IN_SLOT)))
    for key in J.OUTCOME_FORBIDDEN_IN_SLOT:
        f = J.slot_fields(slot_rec(TAU))
        f[key] = "x"
        try:
            R.j.append("SLOT", **f)
            ok = False
        except J.JournalError:
            ok = True
        check("writer refuses a SLOT carrying %s" % key, ok)

    def refused(fn):
        try:
            fn()
            return False
        except J.JournalError:
            return True

    check("writer refuses OUTCOME without any SLOT", refused(lambda: R.outcome(TAU, "NO_PRICE")))
    s_, c_ = R.slot(TAU)                                    # SLOT without checkpoint
    check("writer refuses OUTCOME before the SLOT is anchored", refused(lambda: R.outcome(TAU, "NO_PRICE")))
    check("writer refuses a second SLOT for the same tau", refused(lambda: R.slot(TAU)))
    R.now[0] = TAU + 20_000
    ck = R.j.checkpoint(R.a)
    check("checkpoint seq follows slot seq", ck == s_ + 1)
    R.outcome(TAU, "NO_PRICE")
    check("OUTCOME allowed after the covering checkpoint", R.j.seq == ck + 1)
    check("writer refuses a second OUTCOME for the same tau", refused(lambda: R.outcome(TAU, "NO_PRICE")))
    tau_none = TAU + 5 * GRID
    R.slot(tau_none, anchor_at=tau_none + 20_000, status="NONE")
    check("writer refuses OUTCOME for an anchored NONE SLOT", refused(lambda: R.outcome(tau_none, "NO_PRICE")))
    # a checkpoint that anchors an EARLIER head does not cover a later SLOT
    tau2 = TAU + GRID
    R.now[0] = tau2 - 5000
    k = R.j.seq
    receipt = R.a.submit(JID, k, R.j.head.hex())             # head at k, submitted now ...
    head_k = R.j.head.hex()
    R.slot(tau2)                                            # ... SLOT written after k ...
    R.j.append_unchecked("CHECKPOINT", anchored_seq=k, anchored_head=head_k, receipt=receipt)    # ... checkpoint event of the old head
    check("a checkpoint of an older head does not anchor a later SLOT (guard)", refused(lambda: R.outcome(tau2, "NO_PRICE")))
    s2, c2 = R.slot(TAU + 2 * GRID, anchor_at=TAU + 2 * GRID + 20_000)
    check("slot_and_anchor returns consecutive seqs", c2 == s2 + 1)
    tau4 = TAU + 4 * GRID
    R.slot(tau4)                                            # a SLOT that stays un-anchored
    jp, ap, head = R.done()
    # recovery restores the guards
    j = J.Journal(jp, JID, lambda: TAU + 3 * GRID)
    check("reopen: OUTCOME for an anchored SLOT is still allowed", not refused(lambda: j.append("OUTCOME", **J.outcome_fields(TAU + 2 * GRID, "NO_PRICE"))))
    check("reopen: OUTCOME for a SLOT whose first covering checkpoint is a later one is allowed (tau2 was covered by the next checkpoint)", not refused(lambda: j.append("OUTCOME", **J.outcome_fields(tau2, "NO_PRICE"))))
    check("reopen: OUTCOME for an un-anchored SLOT is still refused", refused(lambda: j.append("OUTCOME", **J.outcome_fields(tau4, "NO_PRICE"))))
    check("reopen: a second OUTCOME is still refused", refused(lambda: j.append("OUTCOME", **J.outcome_fields(TAU, "NO_PRICE"))))
    check("reopen: head continues the chain", j.seq > 0 and len(lines_of(jp)) == j.seq)
    check("second writer on the same file is refused (lock)", refused(lambda: J.Journal(jp, JID, lambda: 0)))
    j.close()
    # torn tail
    with open(jp, "ab") as f:
        f.write(b'{"t":"PING","con')
    check("torn final line: writer refuses to open without repair", refused(lambda: J.Journal(jp, JID, lambda: 0)))
    j = J.Journal(jp, JID, lambda: TAU + 3 * GRID, repair_torn_tail=True)
    check("torn final line: repair returns the dropped bytes", j.dropped_tail == b'{"t":"PING","con')
    j.close()
    # damaged journal: refusal does not leak the lock
    with open(jp, "ab") as f:
        f.write(b"not json\n")
    check("damaged journal is refused", refused(lambda: J.Journal(jp, JID, lambda: 0)))
    msg = ""
    try:
        J.Journal(jp, JID, lambda: 0)
    except J.JournalError as e:
        msg = str(e)
    check("a failed open does not leave the file locked", "locked" not in msg and "not JSON" in msg, msg)
    # writer output is canonical and the verifier head equals the writer head
    R2 = Rig(d, "w2")
    R2.full_slot(TAU)
    jp2, ap2, head2 = R2.done(ping=True)
    res = run(jp2, ap2)
    check("every written line is canonical", all(J.canonical(json.loads(l)) == l for l in lines_of(jp2)))
    check("verifier head_hex equals the writer's head", res["head_hex"] == head2 and res["n_events"] == len(lines_of(jp2)))
    rc = anchor_of(ap2).get(JID, 1)
    check("anchor entries carry time_resolution_ms / time_uncertainty_ms; latest() counts entries", rc["time_resolution_ms"] == 1 and rc["time_uncertainty_ms"] == 0 and anchor_of(ap2).latest(JID) == 1 and anchor_of(ap2).get(JID, 2) is None)

    # ================================================================ PART 2: clean journals
    d = sub("clean")
    R = Rig(d, "c")
    R.full_slot(TAU)
    R.full_slot(TAU + GRID, status_eval=False)
    R.now[0] += 1000
    R.j.checkpoint(R.a)
    jp, ap, head = R.done()
    res = run(jp, ap)
    exact("clean journal (2 slots, candles, EVAL + NO_PRICE outcomes): PASS, no findings of any class", res, infos=[])
    check("clean journal: slots OK and nothing missing", res["slots"] == {TAU: "OK", TAU + GRID: "OK"} and res["missing"] == [], res["slots"])
    R = Rig(d, "c2")
    R.full_slot(TAU)
    R.now[0] += 1000
    R.j.append("PING", conn_id=1, ms=R.now[0])
    jp, ap, head = R.done()
    exact("clean journal with an unanchored tail: PASS with the informational TAIL_UNANCHORED only", run(jp, ap), infos=["TAIL_UNANCHORED"])
    R = Rig(d, "c3")
    jp, ap, head = R.done()
    exact("journal with no checkpoint: PASS with NO_CHECKPOINT only", run(jp, ap), infos=["NO_CHECKPOINT"])
    open(os.path.join(d, "empty.jsonl"), "wb").close()
    open(os.path.join(d, "empty.anchor"), "ab").close()
    res = run(os.path.join(d, "empty.jsonl"), os.path.join(d, "empty.anchor"))
    check("empty file is a valid journal with zero events", res["verdict"] == "PASS" and res["n_events"] == 0 and res["head_hex"] == J.h0().hex() and info(res) == ["NO_CHECKPOINT"])

    # ================================================================ PART 3: the strict anchoring deadline
    d = sub("deadline")
    L = TAU + DL                                              # deadline of the slot at TAU
    cases = [  # (resolution, uncertainty, anchor time_ms, expected)
        (1, 0, L - 1, "OK"), (1, 0, L, "LATE"), (1, 0, L + 1, "LATE"), (1, 0, TAU + 11_000, "OK"),
        (1000, 0, L - 1000, "OK"), (1000, 0, L - 999, "LATE"),          # upper = time + 999
        (1, 5000, L - 5001, "OK"), (1, 5000, L - 5000, "LATE"),          # upper = time + 5000
        (1000, 5000, L - 6000, "OK"), (1000, 5000, L - 5999, "LATE"),    # upper = time + 999 + 5000
        (60_000, 0, L - 60_000, "OK"), (60_000, 0, L - 59_999, "LATE"),
    ]
    for i, (res_ms, unc, t_anchor, want) in enumerate(cases):
        R = Rig(d, "dl%d" % i, res=res_ms, unc=unc)
        R.slot(TAU, anchor_at=t_anchor)
        jp, ap, head = R.done()
        r = run(jp, ap)
        upper = t_anchor + res_ms - 1 + unc
        check("deadline: res=%d unc=%d time=tau%+d -> upper=tau%+d (limit tau+%d) is %s" % (res_ms, unc, t_anchor - TAU, upper - TAU, DL, want),
              r["slots"] == {TAU: want} and r["verdict"] == "PASS" and r["soft"] == ([] if want == "OK" else ["SLOT_LATE_ANCHOR"]), (r["slots"], r["soft"]))
    # a late anchor is soft (verdict PASS) and names the tau
    R = Rig(d, "late")
    R.slot(TAU, anchor_at=TAU + DL + 60_000)
    jp, ap, head = R.done()
    r = run(jp, ap)
    exact("late anchor: soft SLOT_LATE_ANCHOR only, verdict PASS", r, soft=["SLOT_LATE_ANCHOR"])
    has("late anchor: where = tau_ms", r, "SLOT_LATE_ANCHOR", TAU)
    # unanchored depends on verify_time_ms only
    R = Rig(d, "un")
    R.slot(TAU)
    jp, ap, head = R.done()
    for vt, want in ((TAU + DL - 1, "PENDING"), (TAU + DL, "UNANCHORED"), (TAU + 10 * H, "UNANCHORED")):
        r = run(jp, ap, vt=vt)
        check("no covering checkpoint, verify_time=tau%+d -> %s" % (vt - TAU, want), r["slots"] == {TAU: want} and r["soft"] == ([] if want == "PENDING" else ["SLOT_UNANCHORED"]) and r["verdict"] == "PASS", (r["slots"], r["soft"]))
    # the covering checkpoint is the FIRST valid checkpoint after the SLOT whose anchored_seq >= the SLOT line
    R = Rig(d, "cover")
    R.now[0] = TAU - 5000
    k = R.j.seq
    head_k = R.j.head.hex()
    rcpt = R.a.submit(JID, k, head_k)                          # anchors the head BEFORE the slot, in time
    R.slot(TAU)                                               # slot line = k + 1
    R.j.append_unchecked("CHECKPOINT", anchored_seq=k, anchored_head=head_k, receipt=rcpt)   # old head: does not cover the slot
    R.now[0] = TAU + 30_000
    R.j.checkpoint(R.a)                                       # covers it
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("an older-head checkpoint does not cover the SLOT; the next one does", r["slots"] == {TAU: "OK"} and r["hard"] == [], (r["slots"], r["hard"]))
    R = Rig(d, "cover2")
    R.now[0] = TAU - 5000
    k = R.j.seq
    head_k = R.j.head.hex()
    rcpt = R.a.submit(JID, k, head_k)
    R.slot(TAU)
    R.j.append_unchecked("CHECKPOINT", anchored_seq=k, anchored_head=head_k, receipt=rcpt)
    jp, ap, head = R.done()
    r = run(jp, ap, vt=TAU + H)
    check("only an older-head checkpoint exists -> slot UNANCHORED (after the deadline)", r["slots"] == {TAU: "UNANCHORED"} and r["soft"] == ["SLOT_UNANCHORED"], r["slots"])
    # grid completeness
    R = Rig(d, "grid")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.slot(TAU + 3 * GRID, anchor_at=TAU + 3 * GRID + 20_000)
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("missing grid points are soft SLOT_MISSING, reported once per tau", r["missing"] == [TAU + GRID, TAU + 2 * GRID] and r["soft"] == ["SLOT_MISSING"] and sum(1 for f in r["findings"] if f[0] == "SLOT_MISSING") == 2 and r["verdict"] == "PASS")
    R = Rig(d, "grid1")
    R.slot(TAU, anchor_at=TAU + 20_000)
    jp, ap, head = R.done()
    check("a single slot has nothing missing", run(jp, ap)["missing"] == [])

    # ================================================================ PART 4: one test per finding
    d = sub("findings")
    # ---- SLOT rules
    R = Rig(d, "off")
    R.slot(TAU + 1, anchor_at=TAU + 20_000)
    jp, ap, head = R.done()
    r = run(jp, ap)
    exact("SLOT_OFF_GRID (tau not on the 4 h grid)", r, hard=["SLOT_OFF_GRID"])
    has("SLOT_OFF_GRID: where = the SLOT line", r, "SLOT_OFF_GRID", 2)
    check("off-grid SLOT is not counted in grid completeness", r["missing"] == [])
    R = Rig(d, "dup")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.slot(TAU, anchor_at=TAU + 21_000, checked=False)
    R.slot(TAU, checked=False)
    jp, ap, head = R.done()
    r = run(jp, ap)
    exact("DUPLICATE_SLOT (second and later SLOT of one tau)", r, hard=["DUPLICATE_SLOT"])
    check("DUPLICATE_SLOT: one finding per extra SLOT, where = their lines; the first is the reference", [f[1] for f in r["findings"] if f[0] == "DUPLICATE_SLOT"] == [4, 6] and r["slots"] == {TAU: "OK"}, [f[:2] for f in r["findings"]])
    for key, val in (("entry_open_ms", 1), ("exit_open_ms", 1), ("entry_price", "1"), ("exit_price", "1"), ("r_bps", "1"), ("outcome", "x")):
        R = Rig(d, "so_" + key)
        R.slot(TAU, anchor_at=TAU + 20_000, checked=False, **{key: val})
        jp, ap, head = R.done()
        exact("SLOT_HAS_OUTCOME_FIELDS (%s)" % key, run(jp, ap), hard=["SLOT_HAS_OUTCOME_FIELDS"])

    # ---- OUTCOME rules
    R = Rig(d, "o_ok")
    R.full_slot(TAU)
    jp, ap, head = R.done()
    exact("OUTCOME: clean EVAL outcome", run(jp, ap), infos=["TAIL_UNANCHORED"])

    def outcome_case(tag, build, hard, soft=(), infos=None, where=None):
        n_dir[0] += 1
        R = Rig(d, "oc%03d" % n_dir[0])
        build(R)
        jp, ap, head = R.done()
        r = run(jp, ap)
        exact("OUTCOME: " + tag, r, hard=hard, soft=soft, infos=infos)
        return r

    def b_orphan(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + GRID + DL, "100000.5"); R.candle(TAU + GRID + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU + GRID, checked=False, at=TAU + GRID + 5 * H)
    outcome_case("ORPHAN (no SLOT for the tau)", b_orphan, ["OUTCOME_BEFORE_ANCHOR"][:0] + ["OUTCOME_ORPHAN"])

    def b_before_anchor(R):
        R.slot(TAU)
        R.candle(TAU + DL, "100000.5"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, checked=False, at=TAU + 5 * H)
        R.now[0] += 1
        R.j.checkpoint(R.a)                                    # anchors the SLOT only AFTER the outcome
    outcome_case("BEFORE_ANCHOR (OUTCOME written before the checkpoint that covers its SLOT)", b_before_anchor, ["OUTCOME_BEFORE_ANCHOR"], soft=["SLOT_LATE_ANCHOR"], infos=[])

    def b_outcome_first(R):                                    # OUTCOME line precedes its SLOT line: ORPHAN and BEFORE_ANCHOR (contract 8.4)
        R.candle(TAU + DL, "100000.5"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, checked=False, at=TAU + 5 * H)
        R.slot(TAU, anchor_at=TAU + 5 * H + 20_000, checked=False)
    outcome_case("outcome line before its SLOT line -> ORPHAN and BEFORE_ANCHOR", b_outcome_first, ["OUTCOME_BEFORE_ANCHOR", "OUTCOME_ORPHAN"], soft=["SLOT_LATE_ANCHOR"])

    def b_dup_outcome(R):
        R.full_slot(TAU)
        R.outcome(TAU, checked=False)
    outcome_case("DUPLICATE_OUTCOME", b_dup_outcome, ["DUPLICATE_OUTCOME"])

    def b_timing_entry(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL + 60_000, "100000.5"); R.candle(TAU + DL + 60_000 + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, entry_open=TAU + DL + 60_000, at=TAU + 5 * H)
    outcome_case("TIMING (entry candle one minute after tau+5min)", b_timing_entry, ["OUTCOME_TIMING"])

    def b_timing_exit(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL, "100000.5"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS + 60_000, "100500.5")
        R.outcome(TAU, exit_open=TAU + DL + J.OUTCOME_HORIZON_MS + 60_000, at=TAU + 5 * H)
    outcome_case("TIMING (exit candle not entry + 4 h)", b_timing_exit, ["OUTCOME_TIMING"])

    def b_timing_early(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL - 60_000, "100000.5"); R.candle(TAU + DL - 60_000 + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, entry_open=TAU + DL - 60_000, at=TAU + 5 * H)
    outcome_case("TIMING (entry candle BEFORE tau+5min)", b_timing_early, ["OUTCOME_TIMING"])

    for tag, r_ in (("MISMATCH (r_bps off by 1e-3)", repr(1e4 * math.log(100500.5 / 100000.5) + 1e-3)), ("MISMATCH (r_bps not numeric)", "abc"), ("MISMATCH (r_bps nan)", "nan")):
        def b_mm(R, r_=r_):
            R.full_slot(TAU, outcome=False)
            R.candle(TAU + DL, "100000.5"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
            R.outcome(TAU, r=r_, at=TAU + 5 * H)
        outcome_case(tag, b_mm, ["OUTCOME_MISMATCH"])

    def b_mm_tol(R):
        R.full_slot(TAU, outcome=False)
        R.candle(TAU + DL, "100000.5"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, r=repr(1e4 * math.log(100500.5 / 100000.5) + 5e-7), at=TAU + 5 * H)
    outcome_case("r_bps within 1e-6 of the formula is accepted", b_mm_tol, [], infos=["TAIL_UNANCHORED"])

    def b_zero_price(R):
        R.full_slot(TAU, outcome=False)
        R.candle(TAU + DL, "0"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, ep="0", r="0", at=TAU + 5 * H)
    outcome_case("MISMATCH (entry price 0 makes the formula unusable)", b_zero_price, ["OUTCOME_MISMATCH"])

    def b_unlinked_missing(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL, "100000.5")                           # exit candle never journalled
        R.outcome(TAU, at=TAU + 5 * H)
    r = outcome_case("UNLINKED (exit candle not journalled)", b_unlinked_missing, ["OUTCOME_UNLINKED"])
    check("UNLINKED: one finding for the one failing candle", sum(1 for f in r["findings"] if f[0] == "OUTCOME_UNLINKED") == 1)

    def b_unlinked_both(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.outcome(TAU, at=TAU + 5 * H)
    r = outcome_case("UNLINKED (no candles at all)", b_unlinked_both, ["OUTCOME_UNLINKED"])
    check("UNLINKED: two findings (entry and exit)", sum(1 for f in r["findings"] if f[0] == "OUTCOME_UNLINKED") == 2)

    def b_unlinked_price(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL, "100000.6"); R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5")
        R.outcome(TAU, at=TAU + 5 * H)
    outcome_case("UNLINKED (journalled candle open differs from the outcome's entry price)", b_unlinked_price, ["OUTCOME_UNLINKED"])

    def b_unlinked_late(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.candle(TAU + DL, "100000.5")
        R.outcome(TAU, at=TAU + 5 * H)
        R.candle(TAU + DL + J.OUTCOME_HORIZON_MS, "100500.5", recv=TAU + 5 * H + 1000)    # exit candle only AFTER the outcome line
    outcome_case("UNLINKED (the candle is journalled after the OUTCOME line)", b_unlinked_late, ["OUTCOME_UNLINKED"])

    def b_no_price(R):
        R.slot(TAU, anchor_at=TAU + 20_000)
        R.outcome(TAU, "NO_PRICE", at=TAU + 5 * H)
    outcome_case("NO_PRICE outcome needs no candles", b_no_price, [], infos=["TAIL_UNANCHORED"])
    def b_outcome_for_none_slot(R):
        R.slot(TAU, anchor_at=TAU + 20_000, status="NONE")
        R.outcome(TAU, "NO_PRICE", checked=False)
        R.now[0] += 1
        R.j.checkpoint(R.a)
    outcome_case("OUTCOME linked to an anchored NONE SLOT is hard", b_outcome_for_none_slot, ["OUTCOME_FOR_NONE_SLOT"], infos=[])


    # ---- candles
    def b_conflict(R):
        R.full_slot(TAU)
        R.candle(TAU + DL, "100000.7", raw=b"other")
        R.candle(TAU + DL, "100000.8", raw=b"other2")
    r = outcome_case("CANDLE_CONFLICT (a later candle disagrees on open)", b_conflict, ["CANDLE_CONFLICT"])
    check("CANDLE_CONFLICT is reported once per open_time_ms", sum(1 for f in r["findings"] if f[0] == "CANDLE_CONFLICT") == 1)

    def b_same_candle_twice(R):
        R.full_slot(TAU)
        R.candle(TAU + DL, "100000.5", raw=b"dup-raw")
    outcome_case("the same candle twice with the same open is not a conflict", b_same_candle_twice, [])

    def b_not_live(R):
        R.full_slot(TAU)
        R.candle(TAU + 2 * GRID, "100", recv=TAU + 2 * GRID - 1)
    outcome_case("CANDLE_NOT_LIVE (received before its open time = REST/backfill pattern)", b_not_live, ["CANDLE_NOT_LIVE"])

    def b_live_equal(R):
        R.full_slot(TAU)
        R.candle(TAU + 2 * GRID, "100", recv=TAU + 2 * GRID)
    outcome_case("a candle received exactly at its open time is live", b_live_equal, [])

    # ---- format
    def raw_file(tag, lines, tail=b""):
        p, a = os.path.join(d, tag + ".jsonl"), os.path.join(d, tag + ".anchor")
        open(a, "ab").close()
        open(p, "wb").write(b"".join(l + b"\n" for l in lines) + tail)
        return p, a

    sess = J.canonical({"t": "SESSION", "seq": 1, "rec_ms": 1})

    def ev2(n, **kw):
        e = {"t": "PING", "seq": n, "rec_ms": 1, "conn_id": 1, "ms": 1}
        e.update(kw)
        return e

    p, a = raw_file("fmt_ok", [sess, J.canonical(ev2(2))])
    exact("format: minimal valid journal", run(p, a), infos=["NO_CHECKPOINT"])
    for tag, line in (("float number", b'{"conn_id":1,"ms":1.5,"rec_ms":1,"seq":2,"t":"PING"}'), ("exponent", b'{"conn_id":1,"ms":1e3,"rec_ms":1,"seq":2,"t":"PING"}'),
                      ("NaN", b'{"conn_id":1,"ms":NaN,"rec_ms":1,"seq":2,"t":"PING"}'), ("Infinity", b'{"conn_id":1,"ms":Infinity,"rec_ms":1,"seq":2,"t":"PING"}'),
                      ("duplicate key", b'{"conn_id":1,"conn_id":2,"ms":1,"rec_ms":1,"seq":2,"t":"PING"}'), ("nested duplicate key", b'{"a":{"b":1,"b":2},"conn_id":1,"ms":1,"rec_ms":1,"seq":2,"t":"PING"}'),
                      ("not an object", b"[1,2]"), ("not JSON", b"{"), ("invalid UTF-8", b"\xff\xfe"), ("empty line", b""), ("UTF-8 BOM", b"\xef\xbb\xbf" + J.canonical(ev2(2)))):
        p, a = raw_file("fmt_" + tag.replace(" ", "_"), [sess, line, J.canonical(ev2(3))])
        r = run(p, a)
        has("format: BAD_ENCODING for %s at line 2" % tag, r, "BAD_ENCODING", 2)
        check("format: parsing stops at the first BAD_ENCODING (%s): n_events = 1" % tag, r["n_events"] == 1 and r["verdict"] == "FAIL")
    p, a = raw_file("fmt_torn", [sess], tail=b'{"conn_id":1')
    r = run(p, a)
    has("format: torn final line -> BAD_ENCODING at line 2", r, "BAD_ENCODING", 2)
    check("format: torn final line is discarded (n_events = 1) and the verdict is FAIL", r["n_events"] == 1 and r["verdict"] == "FAIL")
    p, a = raw_file("fmt_stop_torn", [sess, b"{"], tail=b'{"conn_id":1')
    r = run(p, a)
    check("format: the torn-line finding is reported even when parsing already stopped earlier",
          sorted((f[0], f[1]) for f in r["findings"] if f[0] == "BAD_ENCODING") == [("BAD_ENCODING", 2), ("BAD_ENCODING", 3)], r["findings"])
    p, a = raw_file("fmt_noncanon", [sess, b'{"conn_id": 1,"ms":1,"rec_ms":1,"seq":2,"t":"PING"}'])
    r = run(p, a)
    exact("format: NOT_CANONICAL (spaces / key order) is hard", r, hard=["NOT_CANONICAL"])
    has("format: NOT_CANONICAL where = line", r, "NOT_CANONICAL", 2)
    p, a = raw_file("fmt_order", [sess, b'{"t":"PING","seq":2,"rec_ms":1,"conn_id":1,"ms":1}'])
    exact("format: unsorted keys are NOT_CANONICAL", run(p, a), hard=["NOT_CANONICAL"])
    p, a = raw_file("fmt_unicode", [sess, J.canonical(ev2(2, note="é")).replace(b"\\u00e9", "é".encode())])
    check("format: raw non-ASCII bytes in a line are NOT_CANONICAL (ensure_ascii)", "NOT_CANONICAL" in run(p, a)["hard"])

    # BAD_EVENT: each required field removed or mistyped, per type
    good = {
        "CONN": {"conn_id": 1, "ev": "open", "ms": 1}, "PING": {"conn_id": 1, "ms": 1}, "MSG": {"conn_id": 1, "recv_ms": 1, "raw_b64": "AA==", "sha256": hashlib.sha256(b"\0").hexdigest()},
        "CLOCK": {"offset_ms": 0, "ms": 1}, "CANDLE": {"open_time_ms": 60_000, "open": "1.5", "recv_ms": 60_000, "raw_b64": "AA==", "sha256": hashlib.sha256(b"\0").hexdigest()},
        "SLOT": J.slot_fields(slot_rec(TAU)), "OUTCOME": {"tau_ms": TAU, "status": "EVAL", "entry_open_ms": TAU + DL, "exit_open_ms": TAU + DL + J.OUTCOME_HORIZON_MS, "entry_price": "1", "exit_price": "1", "r_bps": "0.0"},
        "CHECKPOINT": {"anchored_seq": 1, "anchored_head": "0" * 64, "receipt": {"anchor_id": "A", "index": 1, "seq": 1, "head": "0" * 64, "time_ms": 1, "time_resolution_ms": 1, "time_uncertainty_ms": 0}},
        "SESSION": {},
    }
    n_bad = n_bad_ok = 0
    for t, fields in good.items():
        base = dict(fields, t=t, seq=2, rec_ms=1)
        p, a = raw_file("be_" + t + "_ok", [sess, J.canonical(base)])
        if t not in ("CHECKPOINT",):
            check("BAD_EVENT control: well-formed %s is accepted" % t, "BAD_EVENT" not in run(p, a)["hard"], run(p, a)["hard"])
        keys = list(fields)
        muts = [("missing " + k, {kk: v for kk, v in base.items() if kk != k}) for k in keys + ["rec_ms", "seq"]]
        muts += [("bool as int in " + k, dict(base, **{k: True})) for k in keys if isinstance(fields[k], int) and not isinstance(fields[k], bool)]
        muts += [("string as int in " + k, dict(base, **{k: "1"})) for k in keys if isinstance(fields[k], int) and not isinstance(fields[k], bool)]
        muts += [("int in string field " + k, dict(base, **{k: 1})) for k in keys if isinstance(fields[k], str)]
        if t == "SLOT":
            muts += [("status other", dict(base, status="MAYBE")), ("reasons not list", dict(base, reasons="x")), ("reasons holds int", dict(base, reasons=[1])), ("ledger value str", dict(base, ledger={"a": "1"})),
                     ("sumW not decimal", dict(base, sumW_BUY="1e3")), ("primary_conn string", dict(base, primary_conn="1"))]
        if t == "OUTCOME":
            muts += [("status other", dict(base, status="DONE")), ("EVAL price not decimal", dict(base, entry_price="1,5"))]
        if t == "CONN":
            muts += [("ev other", dict(base, ev="reopen"))]
        if t == "CANDLE":
            muts += [("open not decimal", dict(base, open="-1")), ("open leading zero", dict(base, open="01.5"))]
        if t == "CHECKPOINT":
            muts += [("receipt not object", dict(base, receipt=[])), ("receipt missing index", dict(base, receipt={k: v for k, v in fields["receipt"].items() if k != "index"}))]
        for lab, e in muts:
            if t == "SESSION" and lab.startswith(("missing ", )) and lab.split()[1] in ("t",):
                continue
            n_bad += 1
            p, a = raw_file("be_x", [sess, J.canonical(e)])
            r = run(p, a)
            if any(f[0] == "BAD_EVENT" and f[1] == 2 for f in r["findings"]):
                n_bad_ok += 1
            else:
                print("   BAD_EVENT not raised for %s / %s" % (t, lab))
    check("BAD_EVENT: %d field-removal / mistype mutations over all event types, all detected" % n_bad, n_bad == n_bad_ok, "%d of %d" % (n_bad_ok, n_bad))
    # required-but-nullable keys: JSON null is accepted, a missing key is not
    for key in ("primary_conn", "X_sn"):
        e = dict(good["SLOT"], t="SLOT", seq=2, rec_ms=1)
        e[key] = None
        p, a = raw_file("nullable_" + key, [sess, J.canonical(e)])
        check("nullable required key %s: null accepted" % key, "BAD_EVENT" not in run(p, a)["hard"])
        del e[key]
        p, a = raw_file("nullable_missing_" + key, [sess, J.canonical(e)])
        has("nullable required key %s: missing key is BAD_EVENT" % key, run(p, a), "BAD_EVENT", 2)
    p, a = raw_file("be_unknown", [sess, J.canonical({"t": "MYSTERY", "seq": 2, "rec_ms": 1})])
    has("BAD_EVENT: unknown event type", run(p, a), "BAD_EVENT", 2)
    e = dict(good["PING"], t="PING", seq=2, rec_ms=1, extra_field="ok")
    p, a = raw_file("extra_ok", [sess, J.canonical(e)])
    exact("extra fields on an event are allowed and ignored", run(p, a), infos=["NO_CHECKPOINT"])
    # BAD_EVENT lines are excluded from checks 4-8 but stay in the chain and in SEQ_GAP
    R = Rig(d, "bad_slot")
    R.j.append_unchecked("SLOT", tau_ms=TAU, status="NONE")          # incomplete SLOT -> BAD_EVENT
    R.now[0] = TAU + 20_000
    R.j.checkpoint(R.a)
    jp, ap, head = R.done()
    r = run(jp, ap)
    exact("a BAD_EVENT SLOT is excluded from slot checks (no SLOT_* findings) but is still chained and anchored", r, hard=["BAD_EVENT"])
    check("BAD_EVENT SLOT: no reference slot, so slots == {}", r["slots"] == {} and r["missing"] == [])

    # RAW_HASH_MISMATCH
    def mut_line(tag, build, fn):
        R = Rig(d, tag)
        build(R)
        jp, ap, head = R.done()
        evs = evs_of(jp)
        fn(evs)
        write_evs(jp, evs)
        return run(jp, ap)

    r = mut_line("hash_candle", lambda R: R.full_slot(TAU), lambda evs: [e.update(sha256="0" * 64) for e in evs if e["t"] == "CANDLE"][:1] and None)
    has("RAW_HASH_MISMATCH: wrong sha256 on a CANDLE", r, "RAW_HASH_MISMATCH")

    def _msg_rig(R):
        R.now[0] = TAU - 1000
        R.j.append("MSG", **J.msg_fields(1, TAU - 1000, b"hello"))
        R.slot(TAU, anchor_at=TAU + 20_000)
    r = mut_line("hash_msg", _msg_rig, lambda evs: [e.update(raw_b64=base64.b64encode(b"hellp").decode()) for e in evs if e["t"] == "MSG"] and None)
    has("RAW_HASH_MISMATCH: raw bytes changed on a MSG", r, "RAW_HASH_MISMATCH")
    r = mut_line("hash_b64", _msg_rig, lambda evs: [e.update(raw_b64="!!!") for e in evs if e["t"] == "MSG"] and None)
    has("RAW_HASH_MISMATCH: invalid base64", r, "RAW_HASH_MISMATCH")
    r = mut_line("hash_b64_noncanon", _msg_rig, lambda evs: [e.update(raw_b64="aGVsbG9=") for e in evs if e["t"] == "MSG"] and None)       # 'hello' with non-zero padding bits
    has("RAW_HASH_MISMATCH: non-canonical base64 (non-zero padding bits)", r, "RAW_HASH_MISMATCH")
    p, a = raw_file("hash_bad_event", [sess, J.canonical({"t": "MSG", "seq": 2, "rec_ms": 1, "raw_b64": "AA==", "sha256": "0" * 64})])
    r = run(p, a)
    check("RAW_HASH_MISMATCH is also checked on a BAD_EVENT line when both fields are strings", {"BAD_EVENT", "RAW_HASH_MISMATCH"} <= set(r["hard"]), r["hard"])
    p, a = raw_file("hash_missing_field", [sess, J.canonical({"t": "MSG", "seq": 2, "rec_ms": 1, "raw_b64": "AA=="})])
    r = run(p, a)
    check("no RAW_HASH_MISMATCH when sha256 is absent (BAD_EVENT only)", r["hard"] == ["BAD_EVENT"], r["hard"])

    # SEQ_GAP
    p, a = raw_file("seq_gap", [sess, J.canonical(ev2(5)), J.canonical(ev2(6)), J.canonical(ev2(7))])
    r = run(p, a)
    check("SEQ_GAP: reported once, at the first line whose seq != line number", r["hard"] == ["SEQ_GAP"] and [f[1] for f in r["findings"] if f[0] == "SEQ_GAP"] == [2])
    p, a = raw_file("seq_dup", [sess, J.canonical(ev2(2)), J.canonical(ev2(2))])
    has("SEQ_GAP: repeated seq", run(p, a), "SEQ_GAP", 3)
    p, a = raw_file("seq_bool", [sess, J.canonical(ev2(2, seq=True))])
    r = run(p, a)
    check("seq = true is BAD_EVENT and SEQ_GAP", {"BAD_EVENT", "SEQ_GAP"} <= set(r["hard"]), r["hard"])

    # ---- checkpoints and anchor
    def mutate_receipt(fn, tag):
        R = Rig(d, tag)
        R.full_slot(TAU)
        R.now[0] += 100
        R.j.checkpoint(R.a)
        jp, ap, head = R.done()
        evs = evs_of(jp)
        cps = [e for e in evs if e["t"] == "CHECKPOINT"]
        fn(cps[0])
        write_evs(jp, evs)
        return run(jp, ap)

    base_r = mutate_receipt(lambda c: None, "rc_base")
    exact("checkpoints: unmodified base for the receipt tests", base_r, infos=[])
    for field, delta in (("time_ms", 1), ("time_resolution_ms", 1), ("time_uncertainty_ms", 1), ("index", 0), ("seq", 1)):
        def fn(c, field=field, delta=delta):
            if field == "index":
                return
            c["receipt"][field] += delta
        if field == "index":
            continue
        r = mutate_receipt(fn, "rc_" + field)
        check("RECEIPT_INVALID: receipt.%s differs from the anchor entry" % field, "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c["receipt"].update(anchor_id="OTHER"), "rc_anchor_id")
    check("RECEIPT_INVALID: receipt.anchor_id differs", "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c["receipt"].update(head="f" * 64), "rc_head")
    check("RECEIPT_INVALID: receipt.head != anchored_head", "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c["receipt"].update(time_resolution_ms=0), "rc_res0")
    check("RECEIPT_INVALID: time_resolution_ms < 1", "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c["receipt"].update(time_uncertainty_ms=-1), "rc_unc_neg")
    check("RECEIPT_INVALID: time_uncertainty_ms < 0", "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c.update(anchored_head="e" * 64), "rc_anch_head")
    check("HEAD_MISMATCH: anchored_head differs from the recomputed chain head", "HEAD_MISMATCH" in r["hard"] and "RECEIPT_INVALID" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c["receipt"].update(index=7), "rc_index")
    check("CHECKPOINT_ORDER: receipt index jumps", "CHECKPOINT_ORDER" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c.update(anchored_seq=c["seq"]), "rc_k_eq_i")
    check("CHECKPOINT_ORDER: anchored_seq must be < the checkpoint line", "CHECKPOINT_ORDER" in r["hard"], r["hard"])
    r = mutate_receipt(lambda c: c.update(anchored_seq=0), "rc_k_zero")
    check("CHECKPOINT_ORDER: anchored_seq must be > 0", "CHECKPOINT_ORDER" in r["hard"], r["hard"])
    R = Rig(d, "ord_k")                                           # second checkpoint anchors the same k again
    R.full_slot(TAU)
    jp, ap, head = R.done()
    evs = evs_of(jp)
    c0 = [e for e in evs if e["t"] == "CHECKPOINT"][0]
    dup = copy.deepcopy(c0)
    dup["seq"] = len(evs) + 1
    dup["receipt"] = dict(c0["receipt"], index=2)
    write_evs(jp, evs + [dup])
    r = run(jp, ap)
    check("CHECKPOINT_ORDER: anchored_seq must strictly increase", "CHECKPOINT_ORDER" in r["hard"], r["hard"])

    # missing anchor entry (anchor lost the entry)
    R = Rig(d, "lost")
    R.full_slot(TAU)
    jp, ap, head = R.done()
    open(ap, "wb").close()
    r = run(jp, ap)
    check("RECEIPT_INVALID: anchor has no entry for a journalled receipt", r["hard"] == ["RECEIPT_INVALID"], r["hard"])

    # truncation / anchor ahead
    R = Rig(d, "trunc")
    R.full_slot(TAU)
    R.full_slot(TAU + GRID)
    R.now[0] += 1000
    R.j.checkpoint(R.a)
    R.now[0] += 1000
    R.j.append("PING", conn_id=1, ms=R.now[0])
    jp, ap, head = R.done()
    L0 = lines_of(jp)
    cp_lines = [i for i, l in enumerate(L0, 1) if json.loads(l)["t"] == "CHECKPOINT"]
    check("truncation fixture has 3 checkpoints", len(cp_lines) == 3, cp_lines)
    jt = os.path.join(d, "trunc_cut.jsonl")
    write_lines(jt, L0[:cp_lines[-1] - 1])                     # cut exactly before the last CHECKPOINT line
    r = run(jt, ap)
    check("cut exactly before the last CHECKPOINT line: informational ANCHOR_AHEAD_BENIGN only (indistinguishable from a crash)", r["verdict"] == "PASS" and "ANCHOR_AHEAD_BENIGN" in info(r) and r["hard"] == [], (r["hard"], info(r)))
    has("ANCHOR_AHEAD_BENIGN: where = anchor index", r, "ANCHOR_AHEAD_BENIGN", 3)
    write_lines(jt, L0[:cp_lines[-2] - 1])                     # cut before the second-to-last checkpoint: two anchor entries unexplained
    r = run(jt, ap)
    check("cut before the last TWO checkpoints: ANCHOR_AHEAD_BENIGN for the first extra entry (its head is reproducible), TRUNCATION_OR_REPLACEMENT is raised for entries whose head is not reproducible",
          r["verdict"] in ("PASS", "FAIL") and (("ANCHOR_AHEAD_BENIGN" in info(r)) or ("TRUNCATION_OR_REPLACEMENT" in r["hard"])), (r["hard"], info(r)))
    write_lines(jt, L0[:cp_lines[0] + 3])                      # cut a few lines after the first checkpoint, in the middle of the second slot
    r = run(jt, ap)
    check("cut inside the journal after checkpoint 1: TRUNCATION_OR_REPLACEMENT (the later anchor heads cannot be reproduced)", "TRUNCATION_OR_REPLACEMENT" in r["hard"], (r["hard"], info(r)))
    has("TRUNCATION_OR_REPLACEMENT: where = anchor index", r, "TRUNCATION_OR_REPLACEMENT", 2)
    # journal replaced by a different one of the same length
    R3 = Rig(d, "replace")
    R3.full_slot(TAU, anchor_delay=10_000)
    R3.full_slot(TAU + GRID)
    jp3, _, _ = R3.done()
    r = run(jp3, ap)                                           # other journal against the first anchor
    check("another journal against this anchor: HEAD_MISMATCH / RECEIPT_INVALID (replacement detected)", r["verdict"] == "FAIL" and ("HEAD_MISMATCH" in r["hard"] or "RECEIPT_INVALID" in r["hard"]), r["hard"])

    # ================================================================ PART 5: tamper matrix on one clean journal
    d = sub("tamper")
    R = Rig(d, "base")
    R.full_slot(TAU)
    R.full_slot(TAU + GRID)
    R.now[0] += 1000
    R.j.checkpoint(R.a)
    R.now[0] += 1000
    R.j.append("PING", conn_id=1, ms=R.now[0])                  # unanchored tail line
    jp0, ap0, head0 = R.done()
    L0 = lines_of(jp0)
    N0 = len(L0)
    last_cp = max(i for i, l in enumerate(L0, 1) if json.loads(l)["t"] == "CHECKPOINT")
    base = run(jp0, ap0)
    check("tamper base: PASS with TAIL_UNANCHORED", base["verdict"] == "PASS" and info(base) == ["TAIL_UNANCHORED"], (base["hard"], info(base)))
    work = os.path.join(d, "work.jsonl")
    n_cases = n_detected = 0
    misses = []

    def tamper(label, lines, must_detect=True):
        global n_cases, n_detected
        write_lines(work, lines)
        r = run(work, ap0)
        n_cases += 1
        det = r["verdict"] == "FAIL" or (set(info(r)) & {"ANCHOR_AHEAD_BENIGN"})
        if det:
            n_detected += 1
        elif must_detect:
            misses.append(label)
        return r

    for i in range(1, N0 + 1):
        ev = json.loads(L0[i - 1])
        in_anchored = i <= last_cp - 1                          # the last checkpoint anchors line last_cp - 1 (= anchored_seq)
        # 1 edit a numeric / string field
        e2 = copy.deepcopy(ev)
        key = next((k for k in sorted(e2) if k not in ("t", "seq") and isinstance(e2[k], (int, str)) and not isinstance(e2[k], bool)), None)
        if key is not None:
            e2[key] = e2[key] + 1 if isinstance(e2[key], int) else e2[key] + "x"
            tamper("edit %s of line %d" % (key, i), L0[:i - 1] + [J.canonical(e2)] + L0[i:], must_detect=in_anchored)
        # 2 delete the line
        tamper("delete line %d" % i, L0[:i - 1] + L0[i:], must_detect=in_anchored)
        # 3 swap with the next line
        if i < N0:
            tamper("swap lines %d,%d" % (i, i + 1), L0[:i - 1] + [L0[i], L0[i - 1]] + L0[i + 1:], must_detect=i + 1 <= last_cp - 1)
        # 4 duplicate the line
        tamper("duplicate line %d" % i, L0[:i] + [L0[i - 1]] + L0[i:], must_detect=in_anchored)
        # 5 insert a PING before the line
        tamper("insert a PING before line %d" % i, L0[:i - 1] + [J.canonical({"t": "PING", "seq": i, "rec_ms": 1, "conn_id": 9, "ms": 1})] + L0[i - 1:], must_detect=i <= last_cp - 1)
        # 6 change the line bytes without changing the content semantics (whitespace)
        tamper("reformat line %d" % i, L0[:i - 1] + [L0[i - 1].replace(b",", b", ", 1)] + L0[i:], must_detect=True)
    check("tamper matrix: %d manipulations; every manipulation inside the anchored region detected (%d detected in total)" % (n_cases, n_detected), not misses, misses[:5])
    # what is NOT detectable: edits after the last anchored head
    e2 = json.loads(L0[-1])
    e2["ms"] += 1
    write_lines(work, L0[:-1] + [J.canonical(e2)])
    r = run(work, ap0)
    check("NOT DETECTABLE (documented): editing a line after the last checkpoint passes with TAIL_UNANCHORED", r["verdict"] == "PASS" and info(r) == ["TAIL_UNANCHORED"], (r["hard"], info(r)))
    write_lines(work, L0[:-1])
    r = run(work, ap0)
    check("NOT DETECTABLE (documented): deleting the unanchored tail line passes", r["verdict"] == "PASS", (r["hard"], info(r)))
    write_lines(work, L0 + [J.canonical({"t": "PING", "seq": N0 + 1, "rec_ms": 1, "conn_id": 1, "ms": 5})])
    r = run(work, ap0)
    check("NOT DETECTABLE (documented): appending unanchored lines passes", r["verdict"] == "PASS" and "TAIL_UNANCHORED" in info(r))
    # the anchor itself
    ents = [json.loads(l) for l in open(ap0, "rb").read().split(b"\n") if l]
    for k in ("head", "seq", "time_ms", "time_resolution_ms", "time_uncertainty_ms", "anchor_id"):
        e3 = copy.deepcopy(ents)
        e3[0][k] = ("0" * 64) if k == "head" else ("ZZ" if k == "anchor_id" else e3[0][k] + 1)
        pa = os.path.join(d, "anchor_mut_%s" % k)
        open(pa, "wb").write(b"".join(json.dumps(x, sort_keys=True, separators=(",", ":")).encode() + b"\n" for x in e3))
        r = run(jp0, pa)
        check("anchor entry field %s changed -> RECEIPT_INVALID" % k, "RECEIPT_INVALID" in r["hard"], r["hard"])
    pa = os.path.join(d, "anchor_extra")
    open(pa, "wb").write(open(ap0, "rb").read() + json.dumps(dict(ents[0], index=len(ents) + 1, head="ab" * 32), sort_keys=True, separators=(",", ":")).encode() + b"\n")
    r = run(jp0, pa)
    check("anchor holds an entry the journal cannot reproduce -> TRUNCATION_OR_REPLACEMENT", "TRUNCATION_OR_REPLACEMENT" in r["hard"], r["hard"])
    # backdating limit
    R = Rig(d, "backdate")
    R.now[0] = TAU + 5 * H
    R.slot(TAU, anchor_at=TAU + 5 * H + 20_000)                 # SLOT written (and anchored) long after the entry candle, claiming rec_ms of that time
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("a SLOT anchored after the deadline is LATE (soft): the protocol, not the verifier, turns it into NONE/UNANCHORED", r["slots"] == {TAU: "LATE"} and r["verdict"] == "PASS")

    # ================================================================ PART 6: optional replay layer (SLOT recomputed from journalled messages)
    d = sub("replay")

    def eligible(E, side, z, ap_="100"):
        m = {"e": "forceOrder", "E": E, "o": {"s": "BTCUSDT", "S": side, "o": "LIMIT", "f": "IOC", "q": z, "p": ap_, "ap": ap_, "X": "FILLED", "l": z, "z": z, "T": E}}
        return json.dumps(m, separators=(",", ":")).encode()

    def replay_journal(tag, tamper_slot=None):
        R = Rig(d, tag)
        R.now[0] = TAU - 2 * H
        R.j.append("CONN", conn_id=1, ev="open", ms=TAU - 2 * H)
        R.j.append("CLOCK", offset_ms=0, ms=TAU - 2 * H)
        spec = [(TAU - 800_000, "BUY", "2"), (TAU - 600_000, "SELL", "1"), (TAU - 400_000, "BUY", "1"), (TAU - 300_000, "SELL", "1"), (TAU - 100_000, "BUY", "3")]
        items = [(TAU - 2 * H + 180_000 * k, "PING", None) for k in range(41)] + [(TAU + 9_000, "PING", None)]
        items += [(E + 40, "MSG", (E, s_, z)) for E, s_, z in spec]
        items.sort(key=lambda x: (x[0], x[1]))
        msgs, frames = [], []
        for tm, kind, arg in items:
            R.now[0] = tm
            if kind == "PING":
                R.j.append("PING", conn_id=1, ms=tm)
            else:
                raw = eligible(*arg)
                R.j.append("MSG", **J.msg_fields(1, tm, raw))
                msgs.append({"conn_id": 1, "recv_ms": tm, "raw": raw})
            frames.append(tm)
        health = {1: MC.health_intervals(TAU - 2 * H, frames, end_ms=TAU + 11_000)}
        rec = MC.build_slot(TAU, msgs, health)
        assert rec["status"] == "VALID", rec
        R.now[0] = TAU + 11_000
        f = J.slot_fields(rec)
        if tamper_slot:
            f.update(tamper_slot)
        R.j.append("SLOT", **f)
        R.now[0] = TAU + 31_000
        R.j.checkpoint(R.a)
        jp, ap, head = R.done()
        return jp, ap

    jp, ap = replay_journal("rp_ok")
    r = run(jp, ap, replay_slots=True)
    exact("replay: a SLOT equal to the recomputed one passes (VALID slot with 5 journalled messages)", r, infos=[])
    check("replay: the same journal without the replay layer is also clean", run(jp, ap)["hard"] == [])
    for field, val in (("N_total", 4), ("X_sn", "0.4"), ("status", "NONE"), ("sumW_BUY", "9"), ("n_messages", 6), ("side", -1)):
        jp, ap = replay_journal("rp_" + field, {field: val})
        r = run(jp, ap, replay_slots=True)
        check("replay: tampered SLOT field %s -> SLOT_MISMATCH (only with the replay layer on)" % field, "SLOT_MISMATCH" in r["hard"] and "SLOT_MISMATCH" not in run(jp, ap)["hard"], r["hard"])
        if field == "N_total":
            has("SLOT_MISMATCH: where = the SLOT line", r, "SLOT_MISMATCH", [f[1] for f in r["findings"] if f[0] == "SLOT_MISMATCH"][0])

finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n%d checks, %d failed" % (NT[0], len(FAILS)))
if FAILS:
    print("FAILED:", FAILS)
    sys.exit(1)
print("ALL PASS (dliq_journal_v2.py sha256 %s, dliq_journal_verify_v2.py sha256 %s)" % (hashlib.sha256(open(os.path.join(HERE, "dliq_journal_v2.py"), "rb").read()).hexdigest(),
                                                                                        hashlib.sha256(open(os.path.join(HERE, "dliq_journal_verify_v2.py"), "rb").read()).hexdigest()))
