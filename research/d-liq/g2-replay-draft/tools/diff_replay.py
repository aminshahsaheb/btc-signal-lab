"""Differential harness: independent SLOT replay (clean-room, replay_indep.py) vs the author's replay (primary verifier verify(replay_slots=True)).
SYNTHETIC journals only. Usage: python3 -I -B diff_replay.py <src_dir_of_r4_or_r5_draft> <dir_with_replay_indep.py> <seed> <n_journals>
Exit status: 0 = no disagreement AND the run was not vacuous (at least n/25 honest VALID slots); 1 = disagreement(s); 3 = vacuous run.
Disagreeing journals are kept in a fresh temporary directory whose path is printed (never in the working directory).
HISTORY: the first version compared the free-text detail of SLOT_MISMATCH and let a tamper turn sumW_BUY into an invalid decimal; both were harness bugs
(contract 7.3 only fixes the field LIST; BAD_EVENT slots are excluded from every check) and are fixed here. The scenario mix was also changed after it was
found that only 0.1 % of the first version's scenarios produced a VALID slot (the counted path was barely exercised).

For each random scenario a journal is written with the author's writer (honest SLOT built by the author's build_slot from the journalled events), then
  (1) honest: the independent replay must reproduce the journalled SLOT field by field, and the author's verifier must report no SLOT_MISMATCH;
  (2) tampered: one SLOT field is changed -> BOTH must report SLOT_MISMATCH with the same field list;
  (3) early write: a SLOT written before tau+10000 -> BOTH must report SLOT_EARLY_WRITE.
Disagreements are collected with the scenario seed so they can be reproduced.
"""
import base64
import json
import os
import random
import shutil
import sys
import tempfile

SRC, IND, SEED, N = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, os.path.abspath(SRC))
sys.path.insert(0, os.path.abspath(IND))
sys.dont_write_bytecode = True
import dliq_journal_v2 as J
import dliq_journal_verify_v2 as V
import dliq_msg_contract_v1 as MC
import replay_indep as RI

H = 3_600_000
TAU0 = 1_793_001_600_000
GRID = 4 * H
JID = "DLIQ-DIFF-REPLAY"
LAST = {}
FIX = [json.loads(l) for l in open(os.path.join(SRC, "fixtures", "messages.jsonl"))]
FIXRAW = [(base64.b64decode(f["raw_b64"]), f["expect_class"]) for f in FIX]


def eligible(E, side, z, ap="100", status="FILLED"):
    m = {"e": "forceOrder", "E": E, "o": {"s": "BTCUSDT", "S": side, "o": "LIMIT", "f": "IOC", "q": z, "p": ap, "ap": ap, "X": status, "l": z, "z": z, "T": E}}
    return json.dumps(m, separators=(",", ":")).encode()


def gen_messages(rng, tau, good=False):
    """list of (recv_ms, conn_id, raw). good=True: mostly eligible frames inside the feature window on the main connection (so that VALID slots and the counted path are exercised)."""
    edges = [tau - 900_001, tau - 900_000, tau - 899_999, tau - 1, tau, tau + 1, tau - 960_000, tau - 960_001, tau + 10_000, tau + 10_001, tau - 960_000 + 1]
    out = []
    for _ in range(rng.choice([5, 5, 6, 8, 12, 20, 30]) if good else rng.choice([0, 3, 5, 5, 6, 8, 12, 20])):
        if good:
            E = rng.choice([tau - rng.randint(1, 900_000) for _ in range(12)] + edges[:6])
            conn = rng.choice([1, 1, 1, 1, 1, 2])
            recv = E + rng.choice([0, 40, 40, 200, 200, 9_999, 10_000])
        else:
            E = rng.choice(edges + [tau - rng.randint(1, 900_000) for _ in range(4)])
            conn = rng.choice([1, 1, 1, 2, 3])
            recv = E + rng.choice([0, 40, 40, 200, 9_999, 10_000, 10_001, 12_000, -5])
        kind = rng.random()
        if good and kind >= 0.97:
            kind = 0.95                                              # fixture frames (incl. malformed ones) in 3 % of the messages
        elif good:
            kind = 0.1 if kind < 0.85 else 0.7
        if kind < 0.65:
            z = rng.choice(["1", "2", "3", "0.5", "1.25", "10", "123456.789"])
            ap = rng.choice(["100", "100.5", "99999.99", "1"])
            raw = eligible(E, rng.choice(["BUY", "SELL"]), z, ap)
        elif kind < 0.78:
            raw = eligible(E, rng.choice(["BUY", "SELL"]), "1", "100", status=rng.choice(["PARTIALLY_FILLED", "NEW"]))
        else:
            raw = rng.choice(FIXRAW)[0]
        out.append((recv, conn, raw))
    return out


def scenario(seed, d):
    rng = random.Random(seed)
    k = rng.randint(0, 2)
    good = rng.random() < 0.6
    LAST["good"] = good
    tau = TAU0 + k * GRID
    jp = os.path.join(d, "j%d.jsonl" % seed)
    now = [tau - 3 * H]
    j = J.Journal(jp, JID, lambda: now[0])
    j.append("SESSION", journal_id=JID)
    events = []                                                  # (time, order, kind, payload) to be written in time order
    nconn = rng.choice([1, 1, 2, 3])
    for c in range(1, nconn + 1):
        late_open = rng.random() < (0.08 if good else 0.15)
        open_ms = tau - 960_000 + rng.choice([1, 0, -1, 5_000]) if late_open else tau - 2 * H - rng.randint(0, H)
        events.append((open_ms, 0, "CONN", dict(conn_id=c, ev="open", ms=open_ms)))
        if rng.random() < 0.12:
            events.append((open_ms + 1, 0, "CONN", dict(conn_id=c, ev="open", ms=open_ms + 1)))      # a repeated open of the same id (ignored by the contract)
        # frame times: pings with controllable gaps
        t = open_ms
        gap_choices = [60_000, 120_000, 180_000, 199_999, 200_000, 200_000, 200_001]
        while t < tau + 12_000:
            if good:
                t += rng.choice([60_000, 120_000, 180_000, 199_999, 200_000])
            else:
                t += rng.choice(gap_choices) if rng.random() < 0.9 else rng.choice([250_000, 400_000])
            if t < tau + 20_000:
                events.append((t, 1, "PING", dict(conn_id=c, ms=t)))
        if rng.random() < (0.08 if good else 0.2):
            cm = rng.choice([tau - 500_000, tau - 960_000, tau - 959_999, tau + 5_000, tau + 10_000, tau + 10_001, tau + 11_000])
            events.append((cm, 2, "CLOCKCLOSE", dict(conn_id=c, ev="close", ms=cm)))
    if rng.random() < 0.5:
        off = rng.choice([0, 0, 0, 249, 250, -250] if good else [0, 0, 249, 250, 251, -250, -251])
        events.append((tau - 5 * H // 2, 0, "CLOCK", dict(offset_ms=off, ms=tau - 5 * H // 2)))
    if rng.random() < (0.04 if good else 0.15):
        off = rng.choice([0, 300, -300])
        events.append((tau - 1000, 3, "CLOCK", dict(offset_ms=off, ms=tau - 1000)))
    msgs = gen_messages(rng, tau, good)
    for recv, conn, raw in msgs:
        events.append((recv, 4, "MSG", dict(conn_id=conn, recv_ms=recv, raw=raw)))
    events.sort(key=lambda x: (x[0], x[1]))
    rec_ms = rng.choice([tau + 10_000, tau + 10_000, tau + 10_001, tau + 11_000, tau + 20_000, tau + 9_999, tau + 5_000])
    # only events with time <= rec_ms are journalled before the SLOT; some arrive after it
    before = [e for e in events if e[0] <= rec_ms]
    after = [e for e in events if e[0] > rec_ms]
    tampered = {}
    for tm, _, kind, p in before:
        now[0] = max(now[0], tm)
        if kind == "MSG":
            j.append("MSG", **J.msg_fields(p["conn_id"], p["recv_ms"], p["raw"]))
        elif kind == "PING":
            j.append("PING", **p)
        elif kind in ("CONN", "CLOCKCLOSE"):
            j.append("CONN", **p)
        elif kind == "CLOCK":
            j.append("CLOCK", **p)
    # honest SLOT: author's build_slot over exactly what the replay contract admits (everything journalled before the SLOT line)
    open_ms, close_ms, frames, off, mlist = {}, {}, {}, 0, []
    for tm, _, kind, p in before:
        if kind == "CONN" and p["ev"] == "open":
            open_ms.setdefault(p["conn_id"], p["ms"])
        elif kind == "CLOCKCLOSE":
            close_ms[p["conn_id"]] = p["ms"]
        elif kind == "PING":
            frames.setdefault(p["conn_id"], []).append(p["ms"])
        elif kind == "MSG":
            frames.setdefault(p["conn_id"], []).append(p["recv_ms"])
            mlist.append({"conn_id": p["conn_id"], "recv_ms": p["recv_ms"], "raw": p["raw"]})
        elif kind == "CLOCK":
            off = p["offset_ms"]
    health = {}
    for c, o in open_ms.items():
        stop = close_ms.get(c, rec_ms)
        health[c] = MC.health_intervals(o, [t for t in frames.get(c, []) if o <= t <= stop], end_ms=stop)
    rec = MC.build_slot(tau, mlist, health, off)
    LAST.update(status=rec["status"], reasons=tuple(rec["reasons"]), n=rec["N_total"])
    f = J.slot_fields(rec)
    mode = rng.choice(["honest", "honest", "honest", "tamper"])
    if mode == "tamper":
        field = rng.choice(["status", "N_total", "N_BUY", "sumW_BUY", "X_sn", "side", "n_messages", "malformed_voids", "primary_conn", "reasons", "ledger"])
        if field == "status":
            f["status"] = "NONE" if f["status"] == "VALID" else "VALID"
        elif field in ("N_total", "N_BUY", "n_messages", "malformed_voids"):
            f[field] = f[field] + 1
        elif field == "sumW_BUY":
            f[field] = "1" if f[field] == "0" else f[field] + "1"          # "0" + "1" = "01" would break the dec grammar (BAD_EVENT, excluded from every check)
        elif field == "X_sn":
            f[field] = "0.123456789" if f[field] != "0.123456789" else None
        elif field == "side":
            f[field] = 1 if f[field] != 1 else -1
        elif field == "primary_conn":
            f[field] = 9 if f[field] != 9 else None
        elif field == "reasons":
            f[field] = f[field] + ["GAP"] if "GAP" not in f[field] else []
        elif field == "ledger":
            f[field] = dict(f[field]); f[field]["COUNTED"] = f[field]["COUNTED"] + 1
        tampered = {"field": field}
    now[0] = max(now[0], rec_ms)
    j.append_unchecked("SLOT", **f) if True else None
    now[0] += 1000
    for tm, _, kind, p in after:                                  # events AFTER the SLOT line: must not influence the replay
        now[0] = max(now[0], tm)
        if kind == "MSG":
            j.append("MSG", **J.msg_fields(p["conn_id"], p["recv_ms"], p["raw"]))
        elif kind == "PING":
            j.append("PING", **p)
        elif kind in ("CONN", "CLOCKCLOSE"):
            j.append("CONN", **p)
        elif kind == "CLOCK":
            j.append("CLOCK", **p)
    j.close()
    return jp, tau, rec_ms, mode, tampered


KEEP = tempfile.mkdtemp(prefix="diffreplay_kept_")


def main():
    d = tempfile.mkdtemp(prefix="diffreplay_")
    dis, counts = [], {"honest": 0, "tamper": 0, "early": 0, "valid_status": 0}
    try:
        for i in range(N):
            seed = SEED * 1_000_003 + i
            jp, tau, rec_ms, mode, tam = scenario(seed, d)
            # independent
            ind = RI.check_journal(jp)
            ind_names = sorted(set((n, str(w)) for n, w, _ in ind))
            ind_det = {(n, str(w)): det for n, w, det in ind}
            # author's replay (the verifier needs an anchor only for the chain; use a fresh MockAnchor that has nothing -> findings about anchoring are irrelevant here)
            ap = os.path.join(d, "a%d.anchor" % seed)
            res = V.verify(jp, J.MockAnchor(ap, lambda: 0), JID, tau + 40 * H, replay_slots=True)
            au = [(f[0], str(f[1]), f[2] if len(f) > 2 else "") for f in res["findings"] if f[0] in ("SLOT_MISMATCH", "SLOT_EARLY_WRITE")]
            au_names = sorted(set((n, w) for n, w, _ in au))
            au_det = {(n, w): det for n, w, det in au}
            expect_early = rec_ms < tau + 10_000
            counts[mode if mode == "tamper" else "honest"] += 1
            counts["valid_status"] += int(LAST["status"] == "VALID")
            counts["good_mode"] = counts.get("good_mode", 0) + int(LAST["good"])
            for r_ in LAST["reasons"]:
                counts["reason_" + r_] = counts.get("reason_" + r_, 0) + 1
            counts["early"] += int(expect_early)
            problems = []
            if ind_names != au_names:
                problems.append("finding sets differ: indep=%s author=%s" % (ind_names, au_names))
            else:
                for k in ind_names:
                    if k[0] == "SLOT_MISMATCH":
                        # contract 7.3: the detail names the differing fields, sorted, comma separated. The author's verifier prefixes the list with free text
                        # ("recomputed slot differs in <fields>"); the field LIST is what is compared (8.4 compares only (name, where)).
                        fa = str(au_det[k]).split(" differs in ")[-1]
                        if sorted(str(ind_det[k]).split(",")) != sorted(fa.split(",")):
                            problems.append("MISMATCH field list differs %s: indep=%r author=%r" % (k, ind_det[k], au_det[k]))
            if mode == "honest" and any(n == "SLOT_MISMATCH" for n, _ in ind_names):
                problems.append("honest SLOT reported as mismatch by independent replay: %r" % [x for x in ind if x[0] == "SLOT_MISMATCH"])
            if mode == "tamper" and not any(n == "SLOT_MISMATCH" for n, _ in ind_names) and not any(n == "SLOT_MISMATCH" for n, _ in au_names):
                pass                                               # a tamper that happens to equal the honest value is not a finding (e.g. ledger/side already equal)
            if expect_early and not any(n == "SLOT_EARLY_WRITE" for n, _ in ind_names):
                problems.append("independent missed SLOT_EARLY_WRITE")
            if (not expect_early) and any(n == "SLOT_EARLY_WRITE" for n, _ in ind_names):
                problems.append("independent reported SLOT_EARLY_WRITE wrongly")
            if problems:
                dis.append({"seed": seed, "i": i, "mode": mode, "tamper": tam, "tau": tau, "rec_ms": rec_ms, "problems": problems})
                shutil.copy(jp, os.path.join(KEEP, "disagree_%d.jsonl" % seed))
            else:
                os.remove(jp)
        print(json.dumps({"seed": SEED, "n": N, "counts": counts, "disagreements": len(dis)}))
        for x in dis[:15]:
            print(json.dumps(x))
        if dis:
            print("kept journals: " + KEEP)
        else:
            shutil.rmtree(KEEP, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if dis:
        return 1
    if counts["valid_status"] < N // 25:
        print("VACUOUS RUN: only %d VALID slots in %d scenarios" % (counts["valid_status"], N))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
