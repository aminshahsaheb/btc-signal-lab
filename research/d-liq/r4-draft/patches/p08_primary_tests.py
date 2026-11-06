"""r4 patch 08: primary suite PART 7 -- coverage, outcome_and_anchor, tamper/omit/tail, replay + SLOT_EARLY_WRITE. usage: python3 p08_primary_tests.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/src/test_dliq_journal_v2.py"
s = open(p, encoding="utf-8").read()
new = '''
    # ================================================================ PART 7 (r4): per-OUTCOME coverage, tamper / omit / tail, mandatory-replay findings
    d = sub("r4")

    def refused4(fn):
        try:
            fn()
            return False
        except J.JournalError:
            return True

    # 7.1 outcome_and_anchor
    R = Rig(d, "oa")
    s_, c_ = R.slot(TAU, anchor_at=TAU + 20_000)
    R.now[0] = TAU + 30_000
    o_, k_ = R.j.outcome_and_anchor(J.outcome_fields(TAU, "NO_PRICE"), R.a)
    check("outcome_and_anchor returns consecutive seqs (OUTCOME, covering CHECKPOINT)", k_ == o_ + 1, (o_, k_))
    seq_before = R.j.seq
    check("outcome_and_anchor refuses a second OUTCOME and writes nothing (no stray checkpoint)", refused4(lambda: R.j.outcome_and_anchor(J.outcome_fields(TAU, "NO_PRICE"), R.a)) and R.j.seq == seq_before)
    tn = TAU + GRID
    R.slot(tn, anchor_at=tn + 20_000, status="NONE")
    seq_before = R.j.seq
    check("outcome_and_anchor refuses an OUTCOME for a NONE slot and writes nothing", refused4(lambda: R.j.outcome_and_anchor(J.outcome_fields(tn, "NO_PRICE"), R.a)) and R.j.seq == seq_before)
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("verifier: reference OUTCOME recorded by outcome_and_anchor is COVERED, no OUTCOME_UNCOVERED, no TAIL_UNANCHORED",
          r["outcomes"] == {TAU: "COVERED"} and "OUTCOME_UNCOVERED" not in r["soft"] and "TAIL_UNANCHORED" not in info(r) and r["hard"] == [], (r["outcomes"], r["soft"], info(r), r["hard"]))

    # 7.2 tail outcome: UNCOVERED, soft finding, PASS; a later checkpoint covers it
    R = Rig(d, "tail")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.outcome(TAU, "NO_PRICE", at=TAU + 30_000, anchor=False)
    jp, ap, head = R.done()
    r = run(jp, ap)
    exact("tail OUTCOME (no checkpoint after it): soft OUTCOME_UNCOVERED only, verdict PASS", r, soft=["OUTCOME_UNCOVERED"], infos=["TAIL_UNANCHORED"])
    check("tail OUTCOME: outcomes map says UNCOVERED, where = tau_ms", r["outcomes"] == {TAU: "UNCOVERED"} and [f[1] for f in r["findings"] if f[0] == "OUTCOME_UNCOVERED"] == [TAU], r["outcomes"])
    R = Rig(d, "tail2")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.outcome(TAU, "NO_PRICE", at=TAU + 30_000, anchor=False)
    R.now[0] += 100
    R.j.checkpoint(R.a)                                      # a LATE checkpoint still covers it (no deadline in the verifier, OPEN-22)
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("late covering checkpoint: the OUTCOME is COVERED (no lag cap in the verifier)", r["outcomes"] == {TAU: "COVERED"} and r["soft"] == [], (r["outcomes"], r["soft"]))

    # 7.3 a checkpoint written AFTER the OUTCOME that anchors only an OLDER head does not cover it (anchored_seq >= outcome line is required)
    R = Rig(d, "pre")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.now[0] = TAU + 25_000
    k_old, head_old = R.j.seq, R.j.head.hex()
    receipt = R.a.submit(JID, k_old, head_old)                     # genuine receipt for the head BEFORE the outcome ...
    R.outcome(TAU, "NO_PRICE", at=TAU + 30_000, anchor=False)      # ... the OUTCOME ...
    R.j.append_unchecked("CHECKPOINT", anchored_seq=k_old, anchored_head=head_old, receipt=receipt)   # ... and a checkpoint line that only anchors the old head
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("a later checkpoint that anchors only an older head does not cover the OUTCOME (and is itself a valid checkpoint)", r["outcomes"] == {TAU: "UNCOVERED"} and r["hard"] == [], (r["outcomes"], r["hard"]))

    # 7.3b a forward-pointing checkpoint (a line BEFORE the outcome claiming anchored_seq >= the outcome line) must not cover it either
    R = Rig(d, "fwd")
    R.slot(TAU, anchor_at=TAU + 20_000)                            # lines 2, 3
    R.outcome(TAU, "NO_PRICE", at=TAU + 30_000, anchor=False)      # line 4
    R.now[0] += 100
    R.j.append("PING", conn_id=1, ms=R.now[0])                     # line 5
    jp, ap, head = R.done()
    L = lines_of(jp)
    ev = json.loads(L[2])
    ev["anchored_seq"] = 5
    L[2] = J.canonical(ev)
    jt = os.path.join(d, "fwd_cp.jsonl")
    write_lines(jt, L)
    r = run(jt, ap)
    check("forward-pointing checkpoint (line 3 claims anchored_seq 5): CHECKPOINT_ORDER hard, and it does not cover the OUTCOME at line 4", "CHECKPOINT_ORDER" in r["hard"] and r["outcomes"] == {TAU: "UNCOVERED"}, (r["hard"], r["outcomes"]))

    # 7.4 tamper / omit / tail for a covered EVAL outcome
    def eval_journal(tag, tail=False):
        R = Rig(d, tag)
        R.full_slot(TAU, outcome=False)
        e, x = TAU + DL, TAU + DL + J.OUTCOME_HORIZON_MS
        R.candle(e, px(e))
        R.candle(x, px(x))
        R.outcome(TAU, "EVAL", ep=px(e), xp=px(x), at=x + 200, anchor=not tail)
        jp, ap, head = R.done()
        return jp, ap

    jp, ap = eval_journal("ev_ok")
    r = run(jp, ap)
    exact("covered EVAL outcome: clean", r, infos=[])
    L = lines_of(jp)
    oi = [i for i, l in enumerate(L) if json.loads(l)["t"] == "OUTCOME"][0]
    ev = json.loads(L[oi])
    ev["r_bps"] = "999.0"
    L2 = list(L)
    L2[oi] = J.canonical(ev)
    jt = os.path.join(d, "ev_tamper.jsonl")
    write_lines(jt, L2)
    r = run(jt, ap)
    check("tampered covered OUTCOME: hard HEAD_MISMATCH (chain) and OUTCOME_MISMATCH", "HEAD_MISMATCH" in r["hard"] and "OUTCOME_MISMATCH" in r["hard"] and r["verdict"] == "FAIL", r["hard"])
    L3 = list(L)
    del L3[oi]
    jt = os.path.join(d, "ev_omit.jsonl")
    write_lines(jt, L3)
    r = run(jt, ap)
    check("omitted covered OUTCOME: FAIL (SEQ_GAP and/or HEAD_MISMATCH) and the tau is absent from `outcomes`", r["verdict"] == "FAIL" and bool({"SEQ_GAP", "HEAD_MISMATCH"} & set(r["hard"])) and TAU not in r["outcomes"], (r["hard"], r["outcomes"]))
    jp2, ap2 = eval_journal("ev_tail", tail=True)
    r = run(jp2, ap2)
    check("tail-unanchored EVAL outcome: no hard finding, but UNCOVERED + soft OUTCOME_UNCOVERED (consumer must refuse it)", r["hard"] == [] and r["outcomes"] == {TAU: "UNCOVERED"} and "OUTCOME_UNCOVERED" in r["soft"], (r["hard"], r["outcomes"]))
    L = lines_of(jp2)
    oi = [i for i, l in enumerate(L) if json.loads(l)["t"] == "OUTCOME"][0]
    ev = json.loads(L[oi])
    ev["exit_price"], ev["r_bps"] = "123456.5", repr(1e4 * math.log(123456.5 / float(ev["entry_price"])))
    L[oi] = J.canonical(ev)
    jt = os.path.join(d, "ev_tail_tamper.jsonl")
    write_lines(jt, L)
    r = run(jt, ap2)
    check("tampered tail OUTCOME: the chain cannot see it (documented limit 4.4), the unlinked price is a hard finding and the outcome is UNCOVERED", "OUTCOME_UNLINKED" in r["hard"] and r["outcomes"] == {TAU: "UNCOVERED"}, (r["hard"], r["outcomes"]))

    # 7.5 duplicate OUTCOME: only the reference outcome is entered
    R = Rig(d, "dup4")
    R.slot(TAU, anchor_at=TAU + 20_000)
    R.outcome(TAU, "NO_PRICE", at=TAU + 30_000)
    R.outcome(TAU, "NO_PRICE", checked=False, at=TAU + 40_000, anchor=False)      # duplicate in the unanchored tail
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("duplicate OUTCOME in the tail: DUPLICATE_OUTCOME hard; outcomes has ONE entry (the covered reference); no OUTCOME_UNCOVERED", r["hard"] == ["DUPLICATE_OUTCOME"] and r["outcomes"] == {TAU: "COVERED"} and "OUTCOME_UNCOVERED" not in r["soft"], (r["hard"], r["outcomes"], r["soft"]))

    # 7.6 OUTCOME for a NONE slot written through the unchecked path: hard, whatever its coverage
    R = Rig(d, "none4")
    R.slot(TAU, anchor_at=TAU + 20_000, status="NONE")
    R.outcome(TAU, "NO_PRICE", checked=False, at=TAU + 30_000)
    jp, ap, head = R.done()
    r = run(jp, ap)
    check("OUTCOME for an anchored NONE slot (unchecked path, covered): hard OUTCOME_FOR_NONE_SLOT, outcomes COVERED", r["hard"] == ["OUTCOME_FOR_NONE_SLOT"] and r["outcomes"] == {TAU: "COVERED"}, (r["hard"], r["outcomes"]))

    # 7.7 SLOT_EARLY_WRITE (replay layer): a SLOT recorded before tau + 10 s
    def replay_slot_journal(tag, slot_rec_ms):
        R = Rig(d, tag)
        R.now[0] = TAU - 2 * H
        R.j.append("CONN", conn_id=1, ev="open", ms=TAU - 2 * H)
        R.j.append("CLOCK", offset_ms=0, ms=TAU - 2 * H)
        frames = []
        for k in range(41):
            tm = TAU - 2 * H + 180_000 * k
            R.now[0] = tm
            R.j.append("PING", conn_id=1, ms=tm)
            frames.append(tm)
        R.now[0] = TAU + 5_000
        R.j.append("PING", conn_id=1, ms=TAU + 5_000)
        frames.append(TAU + 5_000)
        health = {1: MC.health_intervals(TAU - 2 * H, frames, end_ms=slot_rec_ms)}
        rec = MC.build_slot(TAU, [], health)
        R.now[0] = slot_rec_ms
        R.j.append("SLOT", **J.slot_fields(rec))
        R.now[0] = slot_rec_ms + 20_000
        R.j.checkpoint(R.a)
        jp, ap, head = R.done()
        return jp, ap, rec

    jp, ap, rec = replay_slot_journal("early", TAU + 9_999)
    r = run(jp, ap, replay_slots=True)
    check("SLOT_EARLY_WRITE: SLOT written at tau+9999 ms is flagged (hard) when the replay layer runs; the replay itself agrees (no SLOT_MISMATCH)",
          "SLOT_EARLY_WRITE" in r["hard"] and "SLOT_MISMATCH" not in r["hard"], (r["hard"], rec["status"], rec["reasons"]))
    has("SLOT_EARLY_WRITE: where = the SLOT line", r, "SLOT_EARLY_WRITE", [f[1] for f in r["findings"] if f[0] == "SLOT_EARLY_WRITE"][0])
    check("SLOT_EARLY_WRITE is not reported without the replay layer", "SLOT_EARLY_WRITE" not in run(jp, ap)["hard"])
    jp, ap, rec = replay_slot_journal("ontime", TAU + 10_000)
    r = run(jp, ap, replay_slots=True)
    check("SLOT written exactly at tau+10 s: no SLOT_EARLY_WRITE (boundary)", "SLOT_EARLY_WRITE" not in r["hard"] and r["hard"] == [], (r["hard"], rec["status"]))
'''
marker = "\nfinally:\n    shutil.rmtree(tmp, ignore_errors=True)"
assert s.count(marker) == 1
s = s.replace(marker, new + marker)
open(p, "w", encoding="utf-8").write(s)
print("ok")
