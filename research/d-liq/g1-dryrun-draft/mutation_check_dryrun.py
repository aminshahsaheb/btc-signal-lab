"""Deliberate-bug (mutation) check of dliq_format_dryrun.py against test_dliq_format_dryrun.py.
Usage: python3 -I -B mutation_check_dryrun.py <package-dir>      (the package is COPIED first; the argument is never modified)
Every mutant must be KILLED (the test suite fails). A mutation pattern that does not occur exactly once is an error (stale mutant), never a pass.
Exit status 0 only if every mutant was killed. Synthetic check of the draft tool; not research evidence."""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = "dliq_format_dryrun.py"
TESTS = "test_dliq_format_dryrun.py"
MUTANTS = [
    # --- websocket client
    ('        if headers.get("sec-websocket-accept") != want:', '        if False:'),
    ('        if status != 101:', '        if False:'),
    ('        if len(buf) > 16384:', '        if False:'),
    ('            if rsv:\n', '            if False:\n'),
    ('            if b1 & 0x80:\n', '            if False:\n'),
    ('            if ln > MAX_FRAME:', '            if False:'),
    ('                if not fin or ln > 125:', '                if False:'),
    ('                    self._send(0xA, payload)', '                    pass'),
    ('                    self._send(0xA, payload)', '                    self._send(0xA, b"")'),
    ('                    self.pings += 1\n', '                    pass\n'),
    ('                if len(frag) > MAX_MESSAGE:', '                if False:'),
    ('                if frag_op is None:\n', '                if False:\n'),
    ('                if frag_op is not None:\n', '                if False:\n'),
    ('        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))', '        masked = payload'),
    ('0x80 | len(payload)', 'len(payload)'),
    ('bytes([0x80 | opcode,', 'bytes([opcode,'),
    ('                ctx = self.ctx or ssl.create_default_context()', '                ctx = self.ctx or ssl._create_unverified_context()'),
    ('                raise WsClosed("close frame received")', '                continue'),
    ('        self._pending = bytearray(rest)', '        self._pending = bytearray()'),
    # --- classification and caps
    ('        form, d = "COMBINED", d["data"]', '        form, d = "RAW", d["data"]'),
    ('{"forceOrder": "force", "kline": "kline"}', '{"forceOrder": "force", "kline": "force"}'),
    ('                if s["got"][kind] >= want.get(kind, 0) or budget.left[kind] <= 0:', '                if s["got"][kind] >= want.get(kind, 0):'),
    ('                budget.left[kind] -= 1', '                pass'),
    ('            elif s["got"]["other"] >= MAX_OTHER_KEPT:', '            elif False:'),
    ('            if all(s["got"][k] >= want.get(k, 0) or budget.left[k] <= 0 for k in ("force", "kline")):', '            if all(s["got"][k] >= want.get(k, 0) for k in ("force", "kline")):'),
    ('    if all(want.get(k, 0) <= 0 or budget.left[k] <= 0 for k in ("force", "kline")):', '    if False:'),
    ('MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 10, 1800', 'MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 200, 10, 1800'),
    ('MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 10, 1800', 'MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 100, 1800'),
    ('MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 10, 1800', 'MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 10, 18000'),
    # --- retries, connect timeout, skip option, socket release
    ('        if k == attempts or not retryable(r):', '        if k == attempts:'),
    ('        if k == attempts or not retryable(r):', '        if not retryable(r):'),
    ('    if o.startswith("connect_error"):\n        return True', '    if False:\n        return True'),
    ('    return o.startswith("handshake_failed") and r["http"] is not None and r["http"].get("status") is None', '    return o.startswith("handshake_failed")'),
    ('    return o.startswith("handshake_failed") and r["http"] is not None and r["http"].get("status") is None', '    return False'),
    ('    for k in range(1, attempts + 1):', '    for k in range(1, attempts):'),
    ('        sleep(wait)', '        pass'),
    ('    r["attempts"] = len(outcomes)', '    r["attempts"] = 1'),
    ('    r["attempt_outcomes"] = outcomes', '    r["attempt_outcomes"] = []'),
    ('    if not (1 <= a.connect_attempts <= MAX_ATTEMPTS_HARD):', '    if False:'),
    ('    if not (5 <= a.connect_timeout <= 60):', '    if False:'),
    ('MAX_ATTEMPTS_HARD, RETRY_WAIT_S = 5, 5.0', 'MAX_ATTEMPTS_HARD, RETRY_WAIT_S = 50, 5.0'),
    ('attempts=a.connect_attempts, connect_timeout=a.connect_timeout)', 'attempts=1, connect_timeout=a.connect_timeout)'),
    ('attempts=a.connect_attempts, connect_timeout=a.connect_timeout)', 'attempts=a.connect_attempts, connect_timeout=15)'),
    ('    c = WsClient(host, port, path, tls, connect_timeout=connect_timeout, ctx=ctx)', '    c = WsClient(host, port, path, tls, ctx=ctx)'),
    ('        plan = plan[1:]', '        pass'),
    ('seconds, attempts, wait, sleep, log, host=host', 'seconds, 1, wait, sleep, log, host=host'),
    ('seconds, attempts, wait, sleep, log, host=host', 'seconds, attempts, 0, sleep, log, host=host'),
    ('            self._drop()', '            pass'),
    ('        sock, self.sock = self.sock, None', '        sock = self.sock'),
    ('build_plan(a.route, a.max_force, a.max_kline, a.seconds, a.also_legacy, a.also_all_market, a.skip_kline_raw)', 'build_plan(a.route, a.max_force, a.max_kline, a.seconds, a.also_legacy, a.also_all_market, False)'),
    # --- output and flow
    ('"sha256": hashlib.sha256(payload).hexdigest()', '"sha256": hashlib.sha256(b"").hexdigest()'),
    ('"raw_b64": base64.b64encode(payload).decode()', '"raw_b64": base64.b64encode(payload[1:]).decode()'),
    ('    os.makedirs(out_dir)  ', '    os.makedirs(out_dir, exist_ok=True)  '),
    ('os.path.join(out_dir, "capture.jsonl"), "x"', 'os.path.join(out_dir, "capture.jsonl"), "w"'),
    ('os.path.join(out_dir, "summary.json"), "x"', 'os.path.join(out_dir, "summary.json"), "w"'),
    ('            if idx == 0 and r["outcome"] != "complete":', '            if False:'),
    ('        summary["frames_recorded"] = n["i"]', '        summary["frames_recorded"] = 0'),
    ('    if not a.i_approve_format_only_dryrun:', '    if False:'),
    ('    if os.path.exists(a.out_dir):', '    if False:'),
    ('    if not (1 <= a.max_force <= MAX_FORCE_HARD):', '    if False:'),
    ('    if not (1 <= a.max_kline <= MAX_KLINE_HARD):', '    if False:'),
    ('    if not (10 <= a.seconds <= MAX_SECONDS_HARD):', '    if False:'),
    ('    summary = run_all(plan, Budget(a.max_force, MAX_KLINE_HARD), a.out_dir, attempts=', '    summary = run_all(plan, Budget(1000, 1000), a.out_dir, attempts='),
    ('    if first and first["outcome"] != "complete":', '    if False:'),
    ('        print("The first connection did not complete', '        print("done: The first connection did not complete'),
    ('    pre = "" if route == "none" else "/" + route', '    pre = "/market"'),
    ('("kline_raw", "%s/ws/btcusdt@kline_1m" % pre, {"kline": min(3, max_kline), "force": 0}, min(60, seconds))', '("kline_raw", "%s/ws/btcusdt@kline_1m" % pre, {"kline": 30, "force": 0}, min(60, seconds))'),
    ('"%s/stream?streams=btcusdt@forceOrder/btcusdt@kline_1m" % pre, {"kline": max_kline, "force": max_force // 2}, seconds)', '"%s/stream?streams=btcusdt@forceOrder/btcusdt@kline_1m" % pre, {"kline": max_kline, "force": max_force}, seconds)'),
]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    work = tempfile.mkdtemp()
    try:
        pkg = os.path.join(work, "pkg")
        shutil.copytree(sys.argv[1], pkg, ignore=shutil.ignore_patterns("__pycache__", "logs"))
        path = os.path.join(pkg, SRC)
        with open(path, encoding="utf-8") as fh:
            orig = fh.read()
        base = subprocess.run([sys.executable, "-I", "-B", TESTS], cwd=pkg, capture_output=True, text=True, timeout=300)
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
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(orig.replace(a, b))
            try:
                r = subprocess.run([sys.executable, "-I", "-B", TESTS], cwd=pkg, capture_output=True, text=True, timeout=120)
                killed = r.returncode != 0
            except subprocess.TimeoutExpired:
                killed = True                       # a mutant that hangs the suite is detected too
            label = "%s => %s" % (a[:60].strip().replace("\n", "\\n"), b[:50].strip().replace("\n", "\\n"))
            print(("KILLED   " if killed else "SURVIVED ") + label)
            bad += 0 if killed else 1
        print("mutants: %d, problems: %d" % (len(MUTANTS), bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
