"""Deliberate-bug (mutation) check of dliq_kline_v1 against src/test_dliq_kline_v1.py.
Usage: python3 -I -B mutation_check_kline.py <package-dir>      (the package is COPIED first; the argument is never modified)
Every mutant must be KILLED (the test suite fails). A mutation pattern that does not occur exactly once is an error (stale mutant), never a pass.
Exit status 0 only if every mutant was killed. Synthetic check of the draft checker; not research evidence."""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = "src/dliq_kline_v1.py"
MUTANTS = [
    # --- parser
    ('    if isinstance(top, list):\n        return _fail("rest_array")', '    if False:\n        return _fail("rest_array")'),
    ('        if set(top) != {"stream", "data"}:', '        if False:'),
    ('        if top["stream"] != expected_stream:', '        if False:'),
    ('    if msg.get("e") != "kline":', '    if False:'),
    ('    if not _is_int(E) or not (TS_MIN <= E <= TS_MAX):', '    if not _is_int(E):'),
    ('    if msg.get("s") != SYMBOL:', '    if False:'),
    ('    if k.get("s") != SYMBOL:', '    if False:'),
    ('    if k.get("i") != INTERVAL:', '    if False:'),
    ('    if t % MINUTE_MS != 0:', '    if False:'),
    ('    if not _is_int(T) or T != t + MINUTE_MS - 1:', '    if not _is_int(T) or T != t + MINUTE_MS:'),
    ('DEC_RE.fullmatch(o) is None', 'DEC_RE.match(o) is None'),
    ('len(o) > 30 or ', ''),
    ('    if Decimal(o) == 0:', '    if False:'),
    ('    if not isinstance(x, bool):', '    if False:'),
    # (dropping the bool exclusion of _is_int is an EQUIVALENT mutant: every use is followed by a range / equality check that rejects True)
    ('json.loads(text, object_pairs_hook=_no_dups, parse_constant=_bad_const)', 'json.loads(text, parse_constant=_bad_const)'),
    ('json.loads(text, object_pairs_hook=_no_dups, parse_constant=_bad_const)', 'json.loads(text, object_pairs_hook=_no_dups)'),
    ('decode("utf-8", errors="strict")', 'decode("utf-8", errors="ignore")'),
    ('    if not isinstance(top, dict):\n        return _fail("not_object")', '    if False:\n        return _fail("not_object")'),
    # --- link and connection rules
    ('        elif msg["raw_b64"] != ev["raw_b64"] or msg["sha256"] != ev["sha256"]:', '        elif False:'),
    ('        elif msg["raw_b64"] != ev["raw_b64"] or msg["sha256"] != ev["sha256"]:', '        elif msg["raw_b64"] != ev["raw_b64"]:'),
    ('        elif msg["recv_ms"] != ev["recv_ms"]:', '        elif False:'),
    ('or not (m < ln):', ':'),
    ('msg.get("t") != "MSG" or ', ''),
    ('            elif feeds.get(c) != "KLINE":', '            elif False:'),
    ('            if c not in opens or opens[c][0] >= m:', '            if c not in opens:'),
    ('not (opens[c][1] <= msg["recv_ms"] and (c not in closes or msg["recv_ms"] <= closes[c]))', 'not (c not in closes or msg["recv_ms"] <= closes[c])'),
    ('not (opens[c][1] <= msg["recv_ms"] and (c not in closes or msg["recv_ms"] <= closes[c]))', 'not (opens[c][1] <= msg["recv_ms"])'),
    ('not (opens[c][1] <= msg["recv_ms"] and (c not in closes or msg["recv_ms"] <= closes[c]))', 'not (opens[c][1] <= msg["recv_ms"] and (c not in closes or msg["recv_ms"] < closes[c]))'),
    ('        if ev["ev"] == "open" and c not in opens:', '        if ev["ev"] == "open":'),
    ('            closes[c] = ev["ms"]', '            pass'),
    # --- parse / field comparison / liveness
    ('        elif p["t"] != ot or p["o"] != declared_open:', '        elif p["t"] != ot:'),
    ('        elif p["t"] != ot or p["o"] != declared_open:', '        elif p["o"] != declared_open:'),
    ('        if ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS < ot:', '        if ev["recv_ms"] + CLOCK_UNCERTAINTY_MS < ot:'),
    ('        if ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS < ot:', '        if ev["recv_ms"] - off < ot:'),
    ('        if ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS < ot:', '        if ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS <= ot:'),
    ('            if ln < line:\n                off = o', '            if True:\n                off = o'),
    ('            bad = bad or "LINK"', '            pass'),
    ('            bad = bad or "PARSE"', '            pass'),
    ('            bad = bad or "NOT_LIVE"', '            pass'),
    # --- reference rule and conflict
    ('        if ot in ref_line:', '        if False:'),
    ('            if ref_open[ot] != declared_open and ot not in seen_conflict:', '            if ot not in seen_conflict:'),
    ('            if ref_open[ot] != declared_open and ot not in seen_conflict:', '            if ref_open[ot] != declared_open:'),
    # --- usability
    ('        if defect[ot]:', '        if False:'),
    ('        elif abs(off) > CLOCK_UNCERTAINTY_MS:', '        elif False:'),
    ('        elif abs(off) > CLOCK_UNCERTAINTY_MS:', '        elif abs(off) >= CLOCK_UNCERTAINTY_MS:'),
    ('        elif not (p["t"] <= p["E"] <= p["T"]):', '        elif False:'),
    ('        elif not (p["t"] <= p["E"] <= p["T"]):', '        elif not (p["t"] < p["E"] <= p["T"]):'),
    ('        elif not (p["t"] <= p["E"] <= p["T"]):', '        elif not (p["t"] <= p["E"] < p["T"]):'),
    ('        elif ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS > p["T"]:', '        elif False:'),
    ('        elif ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS > p["T"]:', '        elif ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS >= p["T"]:'),
    ('        elif ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS > p["T"]:', '        elif ev["recv_ms"] - off > p["T"]:'),
    ('        elif ev["recv_ms"] - off - p["E"] < -CLOCK_UNCERTAINTY_MS:', '        elif False:'),
    ('        elif ev["recv_ms"] - off - p["E"] < -CLOCK_UNCERTAINTY_MS:', '        elif ev["recv_ms"] - off - p["E"] <= -CLOCK_UNCERTAINTY_MS:'),
    ('        elif max_lag_ms is None:', '        elif False:'),
    ('        elif ev["recv_ms"] - off - p["E"] > max_lag_ms:', '        elif False:'),
    ('        elif ev["recv_ms"] - off - p["E"] > max_lag_ms:', '        elif ev["recv_ms"] - off - p["E"] >= max_lag_ms:'),
    ('        elif ev["recv_ms"] - off - p["E"] > max_lag_ms:', '        elif ev["recv_ms"] - p["E"] > max_lag_ms:'),
    ('    if max_lag_ms is None:\n        findings.append(["CANDLE_LAG_UNSET"', '    if False:\n        findings.append(["CANDLE_LAG_UNSET"'),
    # --- OUTCOME link
    ('    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price', '    return ref is None or ref[0] > outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price'),
    ('    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price', '    return ref is None or ref[0] >= outcome_line or ref[1] != price'),
    ('    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price', '    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE"'),
    ('    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price', '    return ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price'),
]


def main():
    if len(sys.argv) != 2 or not os.path.isfile(os.path.join(sys.argv[1], SRC)):
        print("usage: mutation_check_kline.py <package-dir>", file=sys.stderr)
        return 2
    work = tempfile.mkdtemp()
    try:
        pkg = os.path.join(work, "pkg")
        shutil.copytree(sys.argv[1], pkg, ignore=shutil.ignore_patterns("__pycache__", "logs"))
        path = os.path.join(pkg, SRC)
        orig = open(path, encoding="utf-8").read()
        base = subprocess.run([sys.executable, "-I", "-B", "src/test_dliq_kline_v1.py"], cwd=pkg, capture_output=True, text=True)
        if base.returncode != 0:
            print("FAIL: the unmutated suite does not pass")
            print(base.stderr[-600:])
            return 1
        bad = 0
        for a, b in MUTANTS:
            if orig.count(a) != 1:
                print("STALE   (pattern occurs %d times) %s" % (orig.count(a), a[:70].replace("\n", "\\n")))
                bad += 1
                continue
            open(path, "w", encoding="utf-8").write(orig.replace(a, b))
            r = subprocess.run([sys.executable, "-I", "-B", "src/test_dliq_kline_v1.py"], cwd=pkg, capture_output=True, text=True)
            label = "%s => %s" % (a[:60].replace("\n", "\\n"), b[:50].replace("\n", "\\n"))
            print(("KILLED   " if r.returncode else "SURVIVED ") + label)
            bad += 0 if r.returncode else 1
        print("mutants: %d, problems: %d" % (len(MUTANTS), bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
