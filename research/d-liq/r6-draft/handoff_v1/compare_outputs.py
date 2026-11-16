"""Stage 2 of the handoff: compare the recorded outputs of a verifier with the sealed expected outputs.

usage:  python3 -I -B compare_outputs.py --expected DIR --outputs DIR

--expected is the directory `expected/` of the sealed package, --outputs the directory `outputs/` written by run_inputs.py. Exit status 0 only if every id has an output, no
output is unexpected, and every output agrees with its expectation under the rules of INTERFACE.md section 6 (repeated here, they are the rules the author was given):
- an expectation {"unsupported_journal": true} is met only by exactly that output (no verdict: fail closed);
- otherwise the output must be a report with the twelve keys of contract 8.2 (extra keys are ignored), and:
  verdict, replayed, analysis_eligible, n_events, head_hex: equal;   hard, soft: equal lists (the contract says sorted);
  missing: equal as sorted lists (the contract does not fix the order);   slots, outcomes, candles: equal as dicts (JSON keys are decimal strings);
  findings: equal as multisets of (name, where) plus, for FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY the exact detail string (7.7b, 7.7c) and for OUTCOME_UNLINKED the endpoint (the detail
  BEGINS `endpoint=entry` or `endpoint=exit`, 6.9); the OUTCOME_UNLINKED findings must come in the order they are listed in the expectation (entry, then exit, per OUTCOME);
  every finding must be [name (string), where (integer), detail (string)].
NOT compared (diagnostic only): every other detail string, the relative order of findings other than OUTCOME_UNLINKED, extra keys.
A pass means agreement with expectations that one author derived with the contract text and the verifier; it is not independent evidence by itself.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

KEYS = ("verdict", "findings", "hard", "soft", "n_events", "head_hex", "slots", "missing", "outcomes", "candles", "replayed", "analysis_eligible")
DETAIL_NAMES = ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY")
ENDPOINT = re.compile(r"endpoint=(entry|exit)(?![A-Za-z0-9_])")
UNSUPPORTED = {"unsupported_journal": True}


def finding_key(name, where, detail):
    if name in DETAIL_NAMES:
        return (name, where, detail)
    if name == "OUTCOME_UNLINKED":
        m = ENDPOINT.match(detail if isinstance(detail, str) else "")
        return (name, where, m.group(0) if m else detail)
    return (name, where, None)


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def well_formed(findings):
    problems = []
    if not isinstance(findings, list):
        return ["findings is not a list"]
    for f in findings:
        if not (isinstance(f, list) and len(f) == 3 and isinstance(f[0], str) and _int(f[1]) and isinstance(f[2], str)):
            problems.append("finding %r is not [name (string), where (integer), detail (string)]" % (f,))
    return problems


def describe(got):
    if "error" in got and len(got) == 1:
        return "an error (%s)" % got["error"]
    if got == UNSUPPORTED:
        return "UnsupportedJournal"
    return "a report" if "verdict" in got else "something else"


def compare(got, want):
    """Problems (a list of strings, empty = agreement) of one output `got` against one expectation `want` (both parsed JSON)."""
    if want == UNSUPPORTED:
        return [] if got == UNSUPPORTED else ["expected UnsupportedJournal and NO verdict (fail closed), got %s" % describe(got)]
    if not isinstance(got, dict) or "verdict" not in got:
        return ["expected a report, got %s" % (describe(got) if isinstance(got, dict) else "something that is not a JSON object")]
    problems = []
    missing_keys = [k for k in KEYS if k not in got]
    if missing_keys:
        return ["the report lacks the keys %s" % missing_keys]
    for key in ("verdict", "replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft"):
        if got[key] != want[key]:
            problems.append("%s: got %r, expected %r" % (key, got[key], want[key]))
    try:
        if sorted(got["missing"]) != sorted(want["missing"]):
            problems.append("missing: got %r, expected %r" % (got["missing"], want["missing"]))
    except TypeError:
        problems.append("missing: not a list of integers: %r" % (got["missing"],))
    for key in ("slots", "outcomes", "candles"):
        if not isinstance(got[key], dict) or {str(k): v for k, v in got[key].items()} != want[key]:
            problems.append("%s: got %r, expected %r" % (key, got[key], want[key]))
    bad = well_formed(got["findings"])
    if bad:
        return problems + bad
    have = Counter(finding_key(*f) for f in got["findings"])
    need = Counter(finding_key(*f) for f in want["findings"])
    for key in sorted((have - need).elements(), key=repr):
        problems.append("unexpected finding %r" % (key,))
    for key in sorted((need - have).elements(), key=repr):
        problems.append("missing finding %r" % (key,))
    order_got = [finding_key(*f)[1:] for f in got["findings"] if f[0] == "OUTCOME_UNLINKED"]
    order_want = [finding_key(*f)[1:] for f in want["findings"] if f[0] == "OUTCOME_UNLINKED"]
    if order_got != order_want:
        problems.append("OUTCOME_UNLINKED order: got %r, expected %r" % (order_got, order_want))
    return problems


def ids_in(directory):
    return sorted((n[:-5] for n in os.listdir(directory) if n.endswith(".json")), key=lambda x: x.encode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--expected", required=True)
    ap.add_argument("--outputs", required=True)
    args = ap.parse_args(argv)
    want_ids, got_ids = ids_in(args.expected), ids_in(args.outputs)
    problems = 0
    if not want_ids:
        print("NO EXPECTED OUTPUTS FOUND")
        problems += 1
    for i in sorted(set(got_ids) - set(want_ids)):
        print("FAIL %s: an output with no expectation" % i)
        problems += 1
    for i in want_ids:
        if i not in got_ids:
            print("FAIL %s: no output" % i)
            problems += 1
            continue
        with open(os.path.join(args.expected, i + ".json"), encoding="utf-8") as fh:
            want = json.load(fh)
        with open(os.path.join(args.outputs, i + ".json"), encoding="utf-8") as fh:
            got = json.load(fh)
        found = compare(got, want)
        if found:
            print("FAIL %s" % i)
            for line in found:
                print("   " + line)
            problems += 1
        else:
            print("OK   %s" % i)
    print("compared: %d of %d expectations" % (len([i for i in want_ids if i in got_ids]), len(want_ids)))
    print("problems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
