"""SANITY mutants of the primary verifier: a check that run_vectors.py (and the unit tests) are not vacuous. THIS IS NOT the mutation / differential suite of GPT's step 6.

Each mutant breaks ONE rule of the verifier in a temporary COPY of the package (this directory is never modified). Two detectors are run on every mutant:
(v) run_vectors.py on the given vectors (must report problems), (t) the unit tests of test_primary_v3.py, all classes except GuardTests (must fail; GuardTests
compare the files with the provenance diffs and would fail on every mutant, so they say nothing). The unmutated copy must pass both first.
The output says which detector killed the mutant. A mutant killed by (t) only names a rule the vectors do not pin: information for the vector author.
A mutant that survives both is printed and makes the exit status 1 (a rule nobody checks, or a mutant that changes nothing observable).
The mutants are chosen by the author of the verifier and of the vectors; a green run says "these breakages are noticed", not "every breakage is noticed".

usage:  python3 -I -B sanity_mutants.py --vectors DIR [--expect-digest HEX] [--require-derived]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COPY = ("dliq_journal_verify_v3.py", "dliq_msg_contract_v3.py", "r6_rules.py", "run_vectors.py", "make_provenance.py", "test_primary_v3.py")
TEST_CLASSES = ("StructureReasonTests", "UnknownKeyTests", "FeedTests", "RunLevelTests", "ScopeTests", "ReportKeyTests", "RunnerTests")
RULES, VERIFY, MSGC, RUNNER = "r6_rules.py", "dliq_journal_verify_v3.py", "dliq_msg_contract_v3.py", "run_vectors.py"

MUTANTS = (
    # (label, file, exact old text (must occur once), new text)
    ("genesis is the v2 string", RULES, 'GENESIS_V3 = b"DLIQ-JOURNAL-v3-GENESIS"', 'GENESIS_V3 = b"DLIQ-JOURNAL-v2-GENESIS"'),
    ("feed 'KLINE' not accepted", RULES, 'FEEDS = ("FORCE", "KLINE")', 'FEEDS = ("FORCE",)'),
    ("st_top_level never applies", RULES, '("st_top_level", "st" in msg)', '("st_top_level", False)'),
    ("ps_type never applies", RULES, '("ps_type", o is not None and "ps" in o and not isinstance(ps, str))', '("ps_type", False)'),
    ("ps_no_s never applies", RULES, '("ps_no_s", ps_is_string and "s" not in o)', '("ps_no_s", False)'),
    ("ps_ne_s compares str(ps) with str(s)", RULES, 'ps != o["s"])', 'str(ps) != str(o["s"]))'),
    ("a boolean counts as a JSON integer", RULES, "return isinstance(x, int) and not isinstance(x, bool)", "return isinstance(x, int)"),
    ("st_ne_1 never applies", RULES, '("st_ne_1", o is not None and "st" in o and is_json_integer(o["st"]) and o["st"] != 1)', '("st_ne_1", False)'),
    ("reasons examined in reverse order", RULES, "for name, applies in tests:", "for name, applies in reversed(tests):"),
    ("duplicate keys accepted", RULES, "object_pairs_hook=_no_duplicates, ", ""),
    ("NaN / Infinity accepted", RULES, ", parse_constant=_no_constants", ""),
    ("unknown keys de-duplicated", RULES, "return sorted(entries)", "return sorted(set(entries))"),
    ("unknown keys not sorted", RULES, "return sorted(entries)", "return entries"),
    ("o.l is an unknown key", RULES, '"X", "l", "z"', '"X", "z"'),
    ("KLINE messages are examined", RULES, 'if ev["t"] != "MSG" or is_kline_event(opens, ev["conn_id"], line):', 'if ev["t"] != "MSG":'),
    ("a feed applies retroactively", RULES, "if found is not None and found[0] <= line:", "if found is not None:"),
    ("a conflict is also found before the first open", RULES, 'line > found[0] and ev["feed"] != found[1]', 'ev["feed"] != found[1]'),
    ("MSG_CONN_UNKNOWN only for a connection never opened", RULES, "if found is None or found[0] > line:", "if found is None:"),
    ("FORCE_MSG_STRUCTURE not reported", RULES, 'out.append(["FORCE_MSG_STRUCTURE", line,', 'out.append(["FORCE_MSG_STRUCTURE_X", line,'),
    ("where is the seq field, not the physical line", RULES, 'out.append(["FORCE_MSG_STRUCTURE", line,', 'out.append(["FORCE_MSG_STRUCTURE", ev["seq"],'),
    ("detail text reordered", RULES, '"conn_id=%d reason=%s" % (ev["conn_id"], reason)', '"reason=%s conn_id=%d" % (reason, ev["conn_id"])'),
    ("only the first unknown key is reported", RULES, '",".join(keys))', 'keys[0])'),
    ("undecodable base64 stops the verifier", RULES, "        raw = base64.b64decode(text, validate=True)\n    except Exception:\n        return None", "        raw = base64.b64decode(text, validate=True)\n    except ZeroDivisionError:\n        return None"),
    ("verdict: only REPLAY_NOT_RUN is INCOMPLETE", VERIFY, "any(h not in INCOMPLETE_CLASS for h in hard)", 'any(h != "REPLAY_NOT_RUN" for h in hard)'),
    ("CANDLE_LAG_UNSET not reported", VERIFY, 'F(["CANDLE_LAG_UNSET", 0, "L is unset (6.8); no CANDLE minute is USABLE"])', "pass"),
    ("CONN event without feed is valid", VERIFY, ' and g("feed") in R6.FEEDS', ""),
    ("CANDLE without msg_seq is valid", VERIFY, "\n                and _isint(g(\"msg_seq\")))", ")"),
    ("KLINE events enter the replay", VERIFY, 'if t in ("MSG", "PING", "CONN") and R6.is_kline_event(', 'if False and R6.is_kline_event('),
    ("run-level findings dropped", VERIFY, "for f in R6.run_level_findings(valid, opens_by_conn):", "for f in []:"),
    ("feed findings dropped", VERIFY, "for f in R6.feed_findings(valid, opens_by_conn):", "for f in []:"),
    ("one OUTCOME_UNLINKED instead of two", VERIFY, '(("entry_open_ms", "entry"), ("exit_open_ms", "exit")):', '(("entry_open_ms", "entry"),):'),
    ("OUTCOME_UNLINKED endpoints not told apart", VERIFY, '("exit_open_ms", "exit")', '("exit_open_ms", "entry")'),
    ("undecodable base64 becomes empty bytes", VERIFY, '"raw": R6.decode_raw(e)})', '"raw": R6.decode_raw(e) or b""})'),
    ("undecodable MSG dropped from the replay", VERIFY, 'msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": R6.decode_raw(e)})',
     'R6.decode_raw(e) is not None and msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": R6.decode_raw(e)})'),
    ("undecodable base64 has no explicit class", MSGC, 'if raw is None:\n        out["reason"] = "undecodable_base64"', 'if False:\n        out["reason"] = "undecodable_base64"'),
    ("candles reported as USABLE", VERIFY, '"candles": {},', '"candles": {1: "USABLE"},'),
    ("FORCE_UNKNOWN_KEY is hard", VERIFY, '"OUTCOME_UNCOVERED", "FORCE_UNKNOWN_KEY"}', '"OUTCOME_UNCOVERED"}'),
    ("message contract keeps the r5 st rule", MSGC, "reason = R6.structure_reason(msg)", "reason = None"),
    # GPT's blocking finding of 2026-11-14: strict CANONICAL base64 everywhere (a permissive decoder gave 'e!30=' the bytes '{}')
    # (Removing `validate=True` from decode_raw is an EQUIVALENT mutant and is not listed: the canonical comparison that follows already rejects every text a permissive decoder would
    # skip characters of, because the re-encoding of the decoded bytes can never contain them. `validate=True` stays as a second, independent guard; test_the_only_base64_decoder_...
    # requires it, and "the canonical form is not required" below shows that the comparison is the part that matters.)
    ("base64 trailing bits not checked (the canonical form is not required)", RULES, 'return raw if base64.b64encode(raw).decode("ascii") == text else None', "return raw"),
    ("the replay decodes permissively", VERIFY, 'msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": R6.decode_raw(e)})',
     'msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": R6.decode_raw(e) or R6.base64.b64decode(e["raw_b64"])})'),
    # the report keys of 8.2 that the runner compares since 2026-11-14
    ("n_events is off by one", VERIFY, '"n_events": N, "head_hex"', '"n_events": N + 1, "head_hex"'),
    ("head_hex is the head before the last line", VERIFY, '"head_hex": heads[-1].hex()', '"head_hex": heads[-2].hex()'),
    ("an uncovered outcome is reported COVERED", VERIFY, 'outcomes[tau] = "UNCOVERED"', 'outcomes[tau] = "COVERED"'),
    # the runner itself (killed by its negative unit tests: a runner that compares less finds fewer problems on the vectors)
    ("the runner does not compare outcomes", RUNNER, 'if {str(k): v for k, v in report["outcomes"].items()} != derived["outcomes"]:', "if False:"),
    ("the runner does not compare n_events", RUNNER, 'for key in ("n_events", "head_hex"):', 'for key in ("head_hex",):'),
    ("the runner does not compare head_hex", RUNNER, 'for key in ("n_events", "head_hex"):', 'for key in ("n_events",):'),
    ("the runner does not compare the endpoint of OUTCOME_UNLINKED", RUNNER, "return (name, where, m.group(0) if m else detail)", "return (name, where, None)"),
    ("the runner does not check the order of the two OUTCOME_UNLINKED findings", RUNNER, 'if unlinked_order(report["findings"]) != unlinked_order(expect["findings"]):', "if False:"),
    ("--require-derived does not fail on a missing file", RUNNER, "if derived is None and args.require_derived:", "if False:"),
)


def _run(cmd, workdir):
    done = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=300, env={"PATH": os.environ.get("PATH", "")})
    return done.returncode, done.stdout + done.stderr


def run_runner(workdir, vectors, expect_digest, require_derived=False):
    cmd = [sys.executable, "-I", "-B", os.path.join(workdir, "run_vectors.py"), "--vectors", vectors]
    if expect_digest:
        cmd += ["--expect-digest", expect_digest]
    if require_derived:
        cmd += ["--require-derived"]
    return _run(cmd, workdir)


def run_tests(workdir):
    return _run([sys.executable, "-I", "-B", os.path.join(workdir, "test_primary_v3.py"), *TEST_CLASSES], workdir)


def fresh_copy(base):
    work = tempfile.mkdtemp(dir=base)
    for name in COPY:
        shutil.copy(HERE / name, os.path.join(work, name))
    return work


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", required=True)
    ap.add_argument("--expect-digest")
    ap.add_argument("--require-derived", action="store_true", help="the vectors carry EXPECT_DERIVED.json (vector revision 7bb06f0 on): the runner of every copy must compare it")
    args = ap.parse_args(argv)
    vectors = os.path.abspath(args.vectors)
    survived = []
    with tempfile.TemporaryDirectory() as base:
        work0 = fresh_copy(base)
        code, out = run_runner(work0, vectors, args.expect_digest, args.require_derived)
        code_t, out_t = run_tests(work0)
        if code != 0 or code_t != 0:
            print("BASELINE FAILS: the unmutated copy does not pass; mutants are meaningless\n" + out + out_t)
            return 1
        print("baseline: unmutated copy passes the vectors and the unit tests")
        for label, name, old, new in MUTANTS:
            work = fresh_copy(base)
            path = os.path.join(work, name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            if text.count(old) != 1:
                print("INVALID  %-52s (old text occurs %d times in %s)" % (label, text.count(old), name))
                survived.append(label + " [invalid]")
                continue
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, new))
            killers = []
            if run_runner(work, vectors, args.expect_digest, args.require_derived)[0] != 0:
                killers.append("vectors")
            if run_tests(work)[0] != 0:
                killers.append("tests")
            if not killers:
                print("SURVIVED %s" % label)
                survived.append(label)
            else:
                print("KILLED   %-52s by %s" % (label, "+".join(killers)))
    print("mutants: %d, survived/invalid: %d" % (len(MUTANTS), len(survived)))
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
