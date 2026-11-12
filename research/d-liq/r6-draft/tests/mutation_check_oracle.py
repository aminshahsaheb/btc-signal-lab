#!/usr/bin/env python3
"""Deliberate-bug check of the r6 oracle against the r6 vectors.

  python3 -I -B mutation_check_oracle.py            # run from research/d-liq/r6-draft/tests

Each mutant is a one-place text change of oracle_r6.py (a deliberately wrong reading of the contract text). A mutant is KILLED when the oracle built from it
disagrees with the expected findings of at least one vector (or crashes). The point is to show that the vectors can tell the written rules from plausible wrong
readings; it does not show that the rules are right. A pattern that no longer occurs exactly once is STALE and fails the run.
A mutant may be marked "expected to survive" (the last field) when it changes behaviour on which the contract text is silent (an open question in the README); if a vector ever
decides it, the run fails until the list is updated, so that a question cannot be settled by accident. Since GPT's answers of 2026-11-12 no mutant is marked.
"""
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_vectors as CV          # noqa: E402

SRC = (HERE / "oracle_r6.py").read_text(encoding="utf-8")

MUTANTS = [
    # structure reasons (7.5a, 7.7b)
    ("top-level st check removed", '    if "st" in obj:\n        return "st_top_level"', '    if False:\n        return "st_top_level"', False),
    ("top-level st only looked at when o is an object", '    if "st" in obj:', '    if "st" in obj and isinstance(obj.get("o"), dict):', False),
    ("every o is treated as an object", '    if isinstance(o, dict):\n        if "ps" in o:', '    if True:\n        if "ps" in o:', False),
    ("ps_type check removed", 'if not isinstance(o["ps"], str):', 'if False:', False),
    ("ps_no_s check removed", 'if "s" not in o:\n                return "ps_no_s"', 'if False:\n                return "ps_no_s"', False),
    ("ps_no_s reported as ps_ne_s", 'return "ps_no_s"', 'return "ps_ne_s"', False),
    ("ps_ne_s evaluated before ps_no_s",
     '            if "s" not in o:\n                return "ps_no_s"\n            if o["ps"] != o["s"]:\n                return "ps_ne_s"',
     '            if o["ps"] != o.get("s"):\n                return "ps_ne_s"\n            if "s" not in o:\n                return "ps_no_s"', False),
    ("ps_ne_s check removed", 'if o["ps"] != o["s"]:', 'if False:', False),
    ("st_type check removed", 'if not _is_int(o["st"]):', 'if False:', False),
    ("st_ne_1 check removed", 'if o["st"] != 1:', 'if False:', False),
    ("a boolean counts as the integer", 'return isinstance(x, int) and not isinstance(x, bool)', 'return isinstance(x, int)', False),
    ("ps_ne_s evaluated before ps_type",
     '            if not isinstance(o["ps"], str):\n                return "ps_type"\n            if "s" not in o:',
     '            if o["ps"] != o.get("s"):\n                return "ps_ne_s"\n            if not isinstance(o["ps"], str):\n                return "ps_type"\n            if "s" not in o:', False),
    ("st_ne_1 evaluated before st_type",
     '            if not _is_int(o["st"]):\n                return "st_type"\n            if o["st"] != 1:\n                return "st_ne_1"',
     '            if o["st"] != 1:\n                return "st_ne_1"\n            if not _is_int(o["st"]):\n                return "st_type"', False),
    ("st_type evaluated before ps_type", '        if "ps" in o:\n            if not isinstance(o["ps"], str):',
     '        if "st" in o and not _is_int(o["st"]):\n            return "st_type"\n        if "ps" in o:\n            if not isinstance(o["ps"], str):', False),
    ("ps_type evaluated before the top-level st", '    if "st" in obj:\n        return "st_top_level"\n    o = obj.get("o")',
     '    o = obj.get("o")\n    if isinstance(o, dict) and "ps" in o and not isinstance(o["ps"], str):\n        return "ps_type"\n    if "st" in obj:\n        return "st_top_level"', False),
    ("a non-string o.s is compared as a string", 'if o["ps"] != o["s"]:', 'if o["ps"] != str(o["s"]):', False),
    ("ps_no_s evaluated after the st reasons",
     '            if "s" not in o:\n                return "ps_no_s"\n            if o["ps"] != o["s"]:\n                return "ps_ne_s"\n        if "st" in o:\n            if not _is_int(o["st"]):\n                return "st_type"\n            if o["st"] != 1:\n                return "st_ne_1"\n',
     '            if "s" in o and o["ps"] != o["s"]:\n                return "ps_ne_s"\n        if "st" in o:\n            if not _is_int(o["st"]):\n                return "st_type"\n            if o["st"] != 1:\n                return "st_ne_1"\n        if "ps" in o and "s" not in o:\n            return "ps_no_s"\n', False),
    ("a reason label is wrong", 'return "st_type"', 'return "st_ne_1"', False),
    # parsing (7.7a)
    ("duplicate keys accepted", 'object_pairs_hook=_no_dups, ', '', False),
    ("NaN accepted", ', parse_constant=_bad_const', '', False),
    ("a JSON array is treated as an object", 'return obj if isinstance(obj, dict) else None', 'return obj', False),
    # unknown keys (7.5a, 7.7c)
    ("top-level st counted as an unknown key", 'names = [k for k in obj if k not in TOP_KNOWN and k != "st"]', 'names = [k for k in obj if k not in TOP_KNOWN]', False),
    ("a top-level ps counted as known", 'TOP_KNOWN = ("e", "E", "o")', 'TOP_KNOWN = ("e", "E", "o", "ps")', False),
    ("E not a known top-level key", 'TOP_KNOWN = ("e", "E", "o")', 'TOP_KNOWN = ("e", "o")', False),
    ("o.ps not a known key", '"T", "ps", "st")', '"T", "st")', False),
    ("o.st not a known key", '"T", "ps", "st")', '"T", "ps")', False),
    ("unknown keys inside o ignored", '    if isinstance(o, dict):\n        names += ["o." + k for k in o if k not in O_KNOWN]', '    if False:\n        names += ["o." + k for k in o if k not in O_KNOWN]', False),
    ("the location prefix o. is dropped", '["o." + k for k in o if k not in O_KNOWN]', '[k for k in o if k not in O_KNOWN]', False),
    ("unknown keys are not sorted", 'return sorted(names)', 'return names', False),
    ("unknown keys are de-duplicated", 'return sorted(names)', 'return sorted(set(names))', False),
    ("detail joins the keys with a semicolon", '",".join(keys)', '";".join(keys)', False),
    ("detail upper-cases the reason", '% (c, reason)])', '% (c, reason.upper())])', False),
    ("where is seq, not the physical line", 'out.append(["FORCE_MSG_STRUCTURE", n,', 'out.append(["FORCE_MSG_STRUCTURE", ev["seq"],', False),
    # feed (2.1, 2.3)
    ("a KLINE connection is examined", 'if feed == "KLINE":', 'if False:', False),
    ("a message without a feed is not examined", 'if feed == "KLINE":', 'if feed != "FORCE":', False),
    ("feed missing is accepted", 'if ev.get("feed") not in FEEDS:', 'if "feed" not in ev:', False),
    ("a CONN with a bad feed is still used", '            out.append(["BAD_EVENT", n, ""])\n            continue', '            out.append(["BAD_EVENT", n, ""])\n            ev = dict(ev, feed="FORCE")', False),
    ("the last open decides the feed", 'if ev["ev"] == "open" and ev["conn_id"] not in first_open:', 'if ev["ev"] == "open":', False),
    ("CONN_FEED_CONFLICT only for close events", 'if n in valid_conn and ev["conn_id"] in first_open',
     'if n in valid_conn and ev["ev"] == "close" and ev["conn_id"] in first_open', False),
    ("CONN_FEED_CONFLICT also for BAD_EVENT CONN events", 'if n in valid_conn and ev["conn_id"] in first_open and first_open[ev["conn_id"]][0] < n and ev["feed"] != first_open[ev["conn_id"]][1]:',
     'if ev.get("t") == "CONN" and ev["conn_id"] in first_open and first_open[ev["conn_id"]][0] < n and ev.get("feed") != first_open[ev["conn_id"]][1]:', False),
    ("CONN_FEED_CONFLICT also for events before the first open", 'first_open[ev["conn_id"]][0] < n and ev["feed"]', 'ev["feed"]', False),
    ("a message before the first open is accepted", 'if feed is None:', 'if False:', False),
    ("the feed is taken from the whole file (retroactive)", 'if c in first_open and first_open[c][0] < n else None', 'if c in first_open else None', False),
    # genesis, checkpoint, L (3.2, 4.2b, 6.8)
    ("genesis is the v2 string", 'GENESIS_V3 = b"DLIQ-JOURNAL-v3-GENESIS"', 'GENESIS_V3 = b"DLIQ-JOURNAL-v2-GENESIS"', False),
    ("head comparison inverted", 'heads[k].hex() != ev["anchored_head"]', 'heads[k].hex() == ev["anchored_head"]', False),
    ("CANDLE_LAG_UNSET not reported", 'out.append(["CANDLE_LAG_UNSET", 0, ""])', 'pass', False),
    # (since 2026-11-12 no mutant is expected to survive; the mechanism for a deliberately surviving mutant, the last field, is kept for future open questions)
]


def build_oracle(src):
    mod = types.ModuleType("oracle_mut")
    exec(compile(src, "oracle_mut", "exec"), mod.__dict__)
    return mod


def killed_by(mod, vs):
    """Names of the vectors on which the mutated oracle disagrees with the expectation (an exception counts as a disagreement)."""
    out = []
    for v in vs:
        ex = v["expect"]
        want = sorted([f[0], f[1], f[2] if f[0] in CV.DETAIL_NAMES else ""] for f in ex["findings"] if f[0] in CV.ORACLE_NAMES)
        try:
            got = sorted([f[0], f[1], f[2] if f[0] in CV.DETAIL_NAMES else ""] for f in mod.findings(v["data"]))
        except Exception:
            out.append(v["dir"])
            continue
        if got != want:
            out.append(v["dir"])
    return out


def main():
    vs = CV.load(HERE / "vectors")
    problems, n = 0, 0
    # the unmutated oracle must pass
    base = killed_by(build_oracle(SRC), vs)
    if base:
        print("PROBLEM unmutated oracle disagrees on", base)
        problems += 1
    for name, old, new, survives in MUTANTS:
        n += 1
        if SRC.count(old) != 1:
            print("STALE  %s (pattern occurs %d times)" % (name, SRC.count(old)))
            problems += 1
            continue
        k = killed_by(build_oracle(SRC.replace(old, new)), vs)
        if survives and not k:
            print("SURVIVED (expected, undecided)  %s" % name)
        elif survives:
            print("PROBLEM  %s: expected to survive but %s decide it now" % (name, k))
            problems += 1
        elif k:
            print("KILLED  %s  by %s" % (name, ",".join(x.split("_")[0] for x in k[:6])))
        else:
            print("SURVIVED  %s" % name)
            problems += 1
    print("mutants: %d, problems: %d" % (n, problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
