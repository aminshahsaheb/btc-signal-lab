"""Differential test: dliq_journal_verify_v2.verify (author's) versus verify_indep.verify (partially independent implementation based on JOURNAL_CONTRACT_v2.md).
SYNTHETIC journals only. Usage: python3 -I diff_test_verifiers.py <indep_dir> [n_mutants] [seed]
Corpus = hand-built clean journals (several slot counts, anchor timing around the strict boundary, outcomes with candles) + random mutations of them
(JSON-level and byte-level) + mutations of the anchor store. For every journal both verifiers run; compared fields: verdict, hard, soft, head_hex, n_events, slots, missing,
and the multiset of (name, where) for hard+soft findings. Every disagreement is written to the report with a minimal description so it can be traced to a contract ambiguity or a bug."""
import collections
import copy
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
indep_dir = os.path.abspath(sys.argv[1])
sys.path.insert(1, indep_dir)
N_MUT = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 20261101
import dliq_journal_v2 as J
import dliq_journal_verify_v2 as V
import verify_indep as I

H = 3_600_000
TAU = 1_793_001_600_000
JID = "DIFF-TEST"
assert TAU % J.ENTRY_DELAY_MS == 0 and TAU % (4 * H) == 0


def slot_rec(tau, status="VALID"):
    return {"tau_ms": tau, "status": status, "reasons": ["N_TOTAL"] if status == "NONE" else [], "primary_conn": 1, "N_total": 0, "N_BUY": 0, "N_SELL": 0,
            "sumW_BUY": "0", "sumW_SELL": "0", "side": 0 if status == "NONE" else 1, "malformed_voids": 0, "ledger": {"COUNTED": 0}, "n_messages": 0, "X_sn": None}


def build(tmp, tag, nslots=2, anchor_delay=20_000, res=1, unc=0, outcomes=True, skip_slot=None, outcome_before_anchor=False, late_outcome_status="EVAL", invalid_none_outcome=False):
    jp, ap = os.path.join(tmp, tag + ".jsonl"), os.path.join(tmp, tag + ".anchor")
    now = [TAU - 3600_000]
    clock = lambda: now[0]
    jr, an = J.Journal(jp, JID, clock), J.MockAnchor(ap, clock, time_resolution_ms=res, time_uncertainty_ms=unc)
    jr.append("SESSION", journal_id=JID)
    jr.append("CONN", conn_id=1, ev="open", ms=TAU - 3600_000)
    taus = [TAU + s * 4 * H for s in range(nslots)]
    for s, tau in enumerate(taus):
        if skip_slot is not None and s == skip_slot:
            continue
        now[0] = tau + 11_000
        slot_status = "NONE" if invalid_none_outcome else "VALID"
        jr.append("SLOT", **J.slot_fields(dict(slot_rec(tau, status=slot_status), X_sn=None)))
        now[0] = tau + 11_000 + anchor_delay
        jr.checkpoint(an)
        if outcomes:
            entry, exit_ = tau + J.ENTRY_DELAY_MS, tau + J.ENTRY_DELAY_MS + J.OUTCOME_HORIZON_MS
            now[0] = entry + 100
            jr.append("CANDLE", **J.candle_fields(entry, "100000.5", entry + 100, b"entry-%d" % tau))
            now[0] = exit_ + 100
            jr.append("CANDLE", **J.candle_fields(exit_, "101000.25", exit_ + 100, b"exit-%d" % tau))
            now[0] = exit_ + 200
            if s % 2 == 0:
                import math
                r = 1e4 * math.log(101000.25 / 100000.5)
                outcome_fields = J.outcome_fields(tau, "EVAL", entry, exit_, "100000.5", "101000.25", repr(r))
            else:
                outcome_fields = J.outcome_fields(tau, "NO_PRICE")
            if invalid_none_outcome:
                jr.append_unchecked("OUTCOME", **outcome_fields)
            else:
                jr.append("OUTCOME", **outcome_fields)
    now[0] += 5000
    jr.append("PING", conn_id=1, ms=now[0])
    jr.close()
    return jp, ap


class Snap:
    """read-only snapshot of a MockAnchor file so that mutated anchors can be evaluated without touching the original."""
    def __init__(self, path, entries=None):
        self.entries = entries if entries is not None else [json.loads(l) for l in open(path, "rb").read().split(b"\n") if l]

    def get(self, jid, idx):
        for e in self.entries:
            if e["journal_id"] == jid and e["index"] == idx:
                return e
        return None

    def latest(self, jid):
        return sum(1 for e in self.entries if e["journal_id"] == jid)


def norm(res):
    f = collections.Counter((x[0], x[1]) for x in res["findings"] if x[0] in (set(res["hard"]) | set(res["soft"])))
    return {"verdict": res["verdict"], "hard": list(res["hard"]), "soft": list(res["soft"]), "head": res["head_hex"], "n": res["n_events"],
            "slots": {str(k): v for k, v in dict(res["slots"]).items()}, "missing": sorted(res["missing"]), "where": sorted(f.items(), key=lambda kv: str(kv[0]))}


def run_both(path, snap, vt):
    a = norm(V.verify(path, snap, JID, vt, replay_slots=False))
    try:
        b = norm(I.verify(path, snap, JID, vt))
    except Exception as e:                               # a crash is a disagreement too
        b = {"crash": repr(e)}
    return a, b


def lines_of(p):
    return open(p, "rb").read().split(b"\n")[:-1]


def dump(evs):
    return [json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() for e in evs]


def write(p, lines):
    open(p, "wb").write(b"".join(l + b"\n" for l in lines))


def mutate(rng, jp, out, snap):
    """apply 1-3 random operations; returns (description, snapshot_entries or None)."""
    L = lines_of(jp)
    desc = []
    entries = copy.deepcopy(snap.entries)
    for _ in range(rng.choice((1, 1, 2, 3))):
        op = rng.choice(["del", "dup", "swap", "edit_int", "edit_str", "del_key", "add_key", "noncanon", "renumber", "trunc_bytes", "garbage", "anchor_edit", "anchor_drop",
                         "anchor_add", "bool_int", "float_int", "empty_file", "shuffle_receipt", "change_t", "dup_key"])
        if not L and op not in ("garbage", "anchor_add"):
            continue
        i = rng.randrange(len(L)) if L else 0
        try:
            ev = json.loads(L[i]) if L else {}
            if not isinstance(ev, dict):
                ev = {}
        except Exception:
            ev = {}
        if op == "del":
            del L[i]
        elif op == "dup":
            L.insert(i, L[i])
        elif op == "swap" and len(L) > 1:
            j = rng.randrange(len(L))
            L[i], L[j] = L[j], L[i]
        elif op == "edit_int":
            ks = [k for k, v in ev.items() if isinstance(v, int) and not isinstance(v, bool)]
            if ks:
                k = rng.choice(ks)
                ev[k] += rng.choice((-1, 1, -300_000, 300_000, 14_400_000, -14_400_000, 0 if False else 7))
                L[i] = dump([ev])[0]
        elif op == "edit_str":
            ks = [k for k, v in ev.items() if isinstance(v, str)]
            if ks:
                k = rng.choice(ks)
                s = ev[k]
                ev[k] = (s[:-1] + ("0" if s[-1:] != "0" else "1")) if s else "x"
                L[i] = dump([ev])[0]
        elif op == "del_key":
            ks = [k for k in ev if k not in ("t",)]
            if ks:
                del ev[rng.choice(ks)]
                L[i] = dump([ev])[0]
        elif op == "add_key":
            ev[rng.choice(["r_bps", "entry_price", "outcome", "zzz", "exit_open_ms"])] = rng.choice(["1", 1])
            L[i] = dump([ev])[0]
        elif op == "noncanon":
            L[i] = L[i].replace(b",", b", ", 1)
        elif op == "renumber":
            evs = []
            for k, l in enumerate(L, 1):
                try:
                    e = json.loads(l)
                    e["seq"] = k
                    evs.append(e)
                except Exception:
                    evs.append(None)
            L = [dump([e])[0] if e is not None else l for e, l in zip(evs, L)]
        elif op == "trunc_bytes":
            data = b"".join(l + b"\n" for l in L)
            if len(data) < 2:
                continue
            cut = rng.randrange(1, len(data))
            data = data[:cut]
            L = data.split(b"\n")
            if L and L[-1] == b"":
                L = L[:-1]
            else:
                out_bytes = data
                open(out, "wb").write(out_bytes)
                desc.append("trunc_bytes@%d(no-newline-end)" % cut)
                return ";".join(desc), entries if entries != snap.entries else None
        elif op == "garbage":
            L.insert(rng.randrange(len(L) + 1), rng.choice([b"{", b"[]", b"null", b'{"a":1.5}', b'{"a":NaN}', b'{"t":"PING","t":"PING"}', b"\xff\xfe", b'{"t":"MYSTERY","seq":1,"rec_ms":1}', b""]))
        elif op == "anchor_edit" and entries:
            e = rng.choice(entries)
            k = rng.choice(["head", "seq", "time_ms", "time_resolution_ms", "time_uncertainty_ms", "anchor_id"])
            e[k] = ("0" * 64) if k == "head" else ("ZZ" if k == "anchor_id" else e[k] + rng.choice((1, -1, 300_000)))
        elif op == "anchor_drop" and entries:
            del entries[rng.randrange(len(entries))]
        elif op == "anchor_add":
            entries.append({"anchor_id": "MOCK-ANCHOR-1", "journal_id": JID, "index": len(entries) + 1, "seq": rng.randrange(1, 40), "head": "ab" * 32,
                            "time_ms": TAU, "time_resolution_ms": 1, "time_uncertainty_ms": 0, "entry_hash": "00"})
        elif op == "bool_int":
            ks = [k for k, v in ev.items() if isinstance(v, int) and not isinstance(v, bool)]
            if ks:
                ev[rng.choice(ks)] = rng.choice([True, False])
                L[i] = dump([ev])[0]
        elif op == "float_int":
            L[i] = L[i].replace(b'"seq":%d' % ev.get("seq", -1), b'"seq":%d.0' % ev.get("seq", -1), 1) if "seq" in ev else L[i]
        elif op == "empty_file":
            L = []
        elif op == "shuffle_receipt" and ev.get("t") == "CHECKPOINT":
            rc = ev.get("receipt")
            if isinstance(rc, dict) and isinstance(rc.get("index"), int):
                rc["index"] = rc["index"] + rng.choice((-1, 1, 5))
                L[i] = dump([ev])[0]
        elif op == "change_t":
            ev["t"] = rng.choice(["SLOT", "OUTCOME", "CANDLE", "PING", "CHECKPOINT", "SESSION", "NOPE"])
            L[i] = dump([ev])[0]
        elif op == "dup_key":
            L[i] = L[i][:-1] + b',"seq":' + str(rng.randrange(1, 9)).encode() + b"}"
        desc.append(op + "@%d" % i)
    write(out, L)
    return ";".join(desc), entries if entries != snap.entries else None


def main():
    rng = random.Random(SEED)
    tmp = tempfile.mkdtemp(prefix="difftest_")
    report = []
    n_total = n_diff = 0
    cats = collections.Counter()
    cover = collections.Counter()
    try:
        bases = []
        # hand-built corpus around the strict boundary: anchor_upper = slot_time(11 s) + delay + res - 1 + unc  versus  300 s
        for delay, res, unc, label in ((20_000, 1, 0, "early"), (288_999, 1, 0, "upper=tau+299999"), (289_000, 1, 0, "upper=tau+300000(equal)"), (289_001, 1, 0, "late"),
                                       (289_000, 1000, 0, "res1000 equal+999"), (278_000, 1000, 0, "res1000 ok?"), (200_000, 1, 99_000, "unc 99s"), (200_000, 1, 90_000, "unc 90s")):
            for ns in (1, 2, 3):
                bases.append(build(tmp, "b%d_%s_%d" % (len(bases), label.replace(" ", "_"), ns), nslots=ns, anchor_delay=delay, res=res, unc=unc))
        bases.append(build(tmp, "nooutcome", nslots=2, outcomes=False))
        bases.append(build(tmp, "outcome_for_none_slot", nslots=1, outcomes=True, invalid_none_outcome=True))
        bases.append(build(tmp, "skip_middle", nslots=3, skip_slot=1))
        bases.append(build(tmp, "skip_first", nslots=3, skip_slot=0))
        for jp, ap in bases:
            snap = Snap(ap)
            for vt in (TAU, TAU + 400_000, TAU + 40 * H):
                a, b = run_both(jp, snap, vt)
                n_total += 1
                if a != b:
                    n_diff += 1
                    report.append(("BASE " + os.path.basename(jp) + " vt=%d" % vt, a, b))
        for m in range(N_MUT):
            jp, ap = bases[rng.randrange(len(bases))]
            snap = Snap(ap)
            out = os.path.join(tmp, "m.jsonl")
            desc, ents = mutate(rng, jp, out, snap)
            sn = Snap(None, ents) if ents is not None else snap
            vt = rng.choice((TAU, TAU + 400_000, TAU + 40 * H))
            a, b = run_both(out, sn, vt)
            n_total += 1
            for nm in set(a.get("hard", [])) | set(a.get("soft", [])):
                cover[nm] += 1
            if a != b:
                n_diff += 1
                report.append(("MUT %s base=%s vt=%d" % (desc, os.path.basename(jp), vt), a, b))
                keep = os.path.join(HERE, "diff_cases")
                os.makedirs(keep, exist_ok=True)
                shutil.copy(out, os.path.join(keep, "case_%03d.jsonl" % len(report)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("journals compared: %d, disagreements: %d" % (n_total, n_diff))
    allnames = sorted(V.HARD | V.SOFT)
    print("finding coverage (journals in which the author verifier reported the name):", {k: cover[k] for k in allnames})
    print("never exercised:", [k for k in allnames if not cover[k]])
    # classify disagreements by the symmetric difference of hard/soft names
    for desc, a, b in report:
        if "crash" in b:
            cats["indep crashed"] += 1
            continue
        diffs = []
        for k in ("verdict", "head", "n", "slots", "missing"):
            if a[k] != b[k]:
                diffs.append(k)
        sa, sb = set(a["hard"]) | set(a["soft"]), set(b["hard"]) | set(b["soft"])
        if sa != sb:
            diffs.append("names:+author=%s,+indep=%s" % (sorted(sa - sb), sorted(sb - sa)))
        elif a["where"] != b["where"]:
            diffs.append("where")
        cats[" | ".join(diffs) or "other"] += 1
    print("\ndisagreement classes:")
    for k, v in cats.most_common():
        print("%5d  %s" % (v, k))
    wc = collections.Counter()
    for desc, a, b in report:
        if "crash" in b or set(a["hard"]) | set(a["soft"]) != set(b["hard"]) | set(b["soft"]):
            continue
        wa, wb = collections.Counter(dict(a["where"])), collections.Counter(dict(b["where"]))
        for k in set(wa) | set(wb):
            if wa[k] != wb[k]:
                wc[k[0]] += 1
    print("\nwhere-only differences by finding name:", dict(wc))
    print("\nfirst examples per class:")
    shown = set()
    for desc, a, b in report:
        if "crash" in b:
            key = "crash"
        else:
            sa, sb = set(a["hard"]) | set(a["soft"]), set(b["hard"]) | set(b["soft"])
            key = (tuple(sorted(sa - sb)), tuple(sorted(sb - sa)), a["verdict"] != b["verdict"], a["slots"] != b["slots"], a["missing"] != b["missing"], a["where"] != b["where"] and sa == sb)
        if key in shown:
            continue
        shown.add(key)
        print("\n---", desc)
        if "crash" in b:
            print("indep:", b["crash"])
            continue
        print("author hard=%s soft=%s slots=%s missing=%s" % (a["hard"], a["soft"], a["slots"], a["missing"]))
        print("indep  hard=%s soft=%s slots=%s missing=%s" % (b["hard"], b["soft"], b["slots"], b["missing"]))
        if a["where"] != b["where"]:
            wa, wb = dict((tuple(map(str, k)), v) for k, v in a["where"]), dict((tuple(map(str, k)), v) for k, v in b["where"])
            print("   only author:", {k: v for k, v in wa.items() if wb.get(k) != v})
            print("   only indep :", {k: v for k, v in wb.items() if wa.get(k) != v})
    return n_diff


if __name__ == "__main__":
    main()
