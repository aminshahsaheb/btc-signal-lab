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
    ('attempts=a.connect_attempts, connect_timeout=a.connect_timeout, **extra)', 'attempts=1, connect_timeout=a.connect_timeout, **extra)'),
    ('attempts=a.connect_attempts, connect_timeout=a.connect_timeout, **extra)', 'attempts=a.connect_attempts, connect_timeout=15, **extra)'),
    ('    c = WsClient(host, port, path, tls, connect_timeout=connect_timeout, ctx=ctx)', '    c = WsClient(host, port, path, tls, ctx=ctx)'),
    ('        plan = plan[1:]', '        pass'),
    ('run_with_retries(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host', 'run_with_retries(label, path, want, budget, writer, seconds, 1, wait, sleep, log, host=host'),
    ('run_with_retries(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host', 'run_with_retries(label, path, want, budget, writer, seconds, attempts, 0, sleep, log, host=host'),
    ('run_watch(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host', 'run_watch(label, path, want, budget, writer, seconds, 1, wait, sleep, log, host=host'),
    ('run_watch(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host', 'run_watch(label, path, want, budget, writer, seconds, attempts, 0, sleep, log, host=host'),
    ('            self._drop()', '            pass'),
    ('        sock, self.sock = self.sock, None', '        sock = self.sock'),
    ('a.also_all_market, a.skip_kline_raw, a.watch_btc_minutes, a.watch_stop_after)', 'a.also_all_market, False, a.watch_btc_minutes, a.watch_stop_after)'),
    ('a.also_all_market, a.skip_kline_raw, a.watch_btc_minutes, a.watch_stop_after)', 'a.also_all_market, a.skip_kline_raw, 0, a.watch_stop_after)'),
    ('a.also_all_market, a.skip_kline_raw, a.watch_btc_minutes, a.watch_stop_after)', 'a.also_all_market, a.skip_kline_raw, a.watch_btc_minutes, 1)'),
    # --- watch mode
    ('        if got >= need or budget.left["force"] <= 0:\n            return results, "frames_complete"', '        if budget.left["force"] <= 0:\n            return results, "frames_complete"'),
    ('        if got >= need or budget.left["force"] <= 0:\n            return results, "frames_complete"', '        if got >= need:\n            return results, "frames_complete"'),
    ('        if remaining <= 0.5:', '        if False:'),
    ('        if len(results) >= max_connections:', '        if False:'),
    ('        if dead >= max_dead:', '        if False:'),
    ('        dead = 0 if opened(r) else dead + 1', '        dead = dead + 1'),
    ('        dead = 0 if opened(r) else dead + 1', '        dead = 0'),
    ('        got += r["got"]["force"]', '        got += 0'),
    ('        if got < need and budget.left["force"] > 0:\n            sleep(pause)', '        if True:\n            sleep(pause)'),
    ('        if got < need and budget.left["force"] > 0:\n            sleep(pause)', '        if got < need:\n            sleep(pause)'),
    ('        if got < need and budget.left["force"] > 0:\n            sleep(pause)', '        if budget.left["force"] > 0:\n            sleep(pause)'),
    ('min(remaining, MAX_SECONDS_HARD)', 'MAX_SECONDS_HARD'),
    ('{"force": need - got, "kline": 0}', '{"force": need, "kline": 0}'),
    ('    end = clock() + total_seconds', '    end = clock()'),
    ('"%s#%d" % (label, k)', 'label'),
    ('"force_frames": sum(r["got"]["force"] for r in results)', '"force_frames": 0'),
    ('            plan = []\n', '            pass\n'),
    ('    extra = {"watch": {}} if a.watch_btc_minutes else {}', '    extra = {}'),
    ('    extra = {"watch": {}} if a.watch_btc_minutes else {}', '    extra = {"watch": {}}'),
    ('    if not (0 <= a.watch_btc_minutes <= MAX_WATCH_MIN_HARD):', '    if False:'),
    ('    if not (1 <= a.watch_stop_after <= a.max_force):', '    if False:'),
    ('    if a.watch_btc_minutes and (a.also_all_market or a.also_legacy or a.skip_kline_raw):', '    if False:'),
    ('"force": min(stop_after, max_force)}, watch_minutes * 60)', '"force": stop_after}, watch_minutes * 60)'),
    ('"force": min(stop_after, max_force)}, watch_minutes * 60)', '"force": min(stop_after, max_force)}, watch_minutes)'),
    ('        return 0 if any(opened(c) for c in summary["connections"]) else 1', '        return 0'),
    ('        if w["force_frames"] == 0:', '        if False:'),
    ('    if w:\n        print("Watch ended', '    if False:\n        print("Watch ended'),
    ('WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 300', 'WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 1200, 300'),
    ('WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 300', 'WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 3000'),
    ('WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 300', 'WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 0.0, 3, 120, 300'),
    ('WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 300', 'WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 30, 120, 300'),
    # --- output and flow
    ('"sha256": hashlib.sha256(payload).hexdigest()', '"sha256": hashlib.sha256(b"").hexdigest()'),
    ('"raw_b64": base64.b64encode(payload).decode()', '"raw_b64": base64.b64encode(payload[1:]).decode()'),
    ('    os.makedirs(out_dir)  ', '    os.makedirs(out_dir, exist_ok=True)  '),
    ('os.path.join(out_dir, "capture.jsonl"), "x"', 'os.path.join(out_dir, "capture.jsonl"), "w"'),
    ('os.path.join(out_dir, "summary.json"), "x"', 'os.path.join(out_dir, "summary.json"), "w"'),
    ('            if idx == 0 and not opened(r):', '            if False:'),
    ('            if idx == 0 and not opened(r):', '            if idx == 0 and r["outcome"] != "complete":'),
    ('    return r.get("http") is not None and r["http"].get("status") == 101', '    return r.get("http") is not None'),
    ('    return r.get("http") is not None and r["http"].get("status") == 101', '    return True'),
    ('    ended_early = [c["label"] for c in summary["connections"] if c["outcome"] != "complete"]', '    ended_early = []'),
    ('        summary["frames_recorded"] = n["i"]', '        summary["frames_recorded"] = 0'),
    ('    if not a.i_approve_format_only_dryrun:', '    if False:'),
    ('    if os.path.exists(a.out_dir):', '    if False:'),
    ('    if not (1 <= a.max_force <= MAX_FORCE_HARD):', '    if False:'),
    ('    if not (1 <= a.max_kline <= MAX_KLINE_HARD):', '    if False:'),
    ('    if not (10 <= a.seconds <= MAX_SECONDS_HARD):', '    if False:'),
    ('    summary = run_all(plan, Budget(a.max_force, MAX_KLINE_HARD), a.out_dir, attempts=', '    summary = run_all(plan, Budget(1000, 1000), a.out_dir, attempts='),
    ('    if first and not opened(first):', '    if False:'),
    ('        print("The first connection could not be opened', '        print("done: The first connection could not be opened'),
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
