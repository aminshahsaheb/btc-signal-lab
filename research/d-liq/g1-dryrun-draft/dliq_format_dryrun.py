#!/usr/bin/env python3
"""D-LIQ format-only dry run (DRAFT, unreviewed). Captures at most 20 raw forceOrder frames and at most 10 kline frames of BTCUSDT from the public
Binance USD-M futures websocket, only to see the real message format, the working endpoint routes and the HTTP status of this network path.

What it does NOT do: no login, no API key, no order, no price/outcome analysis, no upload. It connects ONLY to fstream.binance.com:443, writes
only into a NEW local directory, and stops by itself (hard caps below). Python 3.8+ standard library only (own minimal websocket client).
It must be started with --i-approve-format-only-dryrun: passing that flag is the owner's explicit approval required by docs/ROADMAP.md (2F).
Usage:  python3 dliq_format_dryrun.py --out-dir ./dryrun_out --i-approve-format-only-dryrun
Output: <out-dir>/capture.jsonl (one line per recorded frame: exact bytes as base64 + sha256 + local receive time) and <out-dir>/summary.json.
The files contain public market data and no personal data (no IP address, no account). They are NOT to be committed to the repository."""
import argparse
import base64
import hashlib
import json
import os
import platform
import socket
import ssl
import sys
import time

TOOL_VERSION = "dliq-format-dryrun/4 (draft)"
HOST, PORT = "fstream.binance.com", 443        # the ONLY endpoint this tool ever connects to
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_FORCE_HARD, MAX_KLINE_HARD, MAX_SECONDS_HARD = 20, 10, 1800
WATCH_PAUSE_S, WATCH_MAX_DEAD, MAX_WATCH_MIN_HARD, MAX_WATCH_CONNECTIONS = 3.0, 3, 120, 300   # watch mode: bounded reconnecting
MAX_ATTEMPTS_HARD, RETRY_WAIT_S = 5, 5.0                      # a flaky VPN tunnel is retried a few times, never in a loop
MAX_FRAME, MAX_MESSAGE, MAX_OTHER_KEPT = 1 << 20, 1 << 20, 5


class HandshakeError(Exception):
    def __init__(self, msg, status=None, headers=None, body=b""):
        super().__init__(msg)
        self.status, self.headers, self.body = status, headers or {}, body


class WsClosed(Exception):
    pass


class WsTimeout(Exception):
    pass


class WsProtocolError(Exception):
    pass


class WsClient:
    """Minimal RFC 6455 client: handshake, text/binary messages (with fragmentation), ping -> pong, close."""

    def __init__(self, host, port, path, tls=True, connect_timeout=15.0, ctx=None):
        self.host, self.port, self.path, self.tls, self.connect_timeout = host, port, path, tls, connect_timeout
        self.ctx, self.sock, self.pings, self.info = ctx, None, 0, {}
        self._pending = bytearray()

    def open(self):
        raw = socket.create_connection((self.host, self.port), timeout=self.connect_timeout)
        try:
            if self.tls:
                ctx = self.ctx or ssl.create_default_context()        # certificate verification stays ON
                self.sock = ctx.wrap_socket(raw, server_hostname=self.host)
            else:
                self.sock = raw
        except Exception:
            raw.close()
            raise
        try:
            return self._handshake()
        except BaseException:
            self._drop()                                             # every failed handshake releases the socket (no WebSocket close frame: none was opened)
            raise

    def _drop(self):
        sock, self.sock = self.sock, None
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode()
        host_header = self.host if self.port in (80, 443) else "%s:%d" % (self.host, self.port)
        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
               "Sec-WebSocket-Version: 13\r\nUser-Agent: %s\r\n\r\n" % (self.path, host_header, key, TOOL_VERSION))
        self.sock.sendall(req.encode("ascii"))
        deadline = time.monotonic() + self.connect_timeout
        buf = bytearray()
        while b"\r\n\r\n" not in buf:
            if len(buf) > 16384:
                raise HandshakeError("HTTP response header too large")
            self.sock.settimeout(max(0.1, deadline - time.monotonic()))
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                raise HandshakeError("timeout waiting for the HTTP response")
            if not chunk:
                break
            buf += chunk
        head, _, rest = bytes(buf).partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        parts = lines[0].split(" ", 2)
        status = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        headers = {}
        for ln in lines[1:]:
            k, _, v = ln.partition(":")
            headers[k.strip().lower()] = v.strip()
        self.info = {"status": status, "date": headers.get("date"), "server": headers.get("server")}
        if status != 101:
            body = bytes(rest[:2048])
            raise HandshakeError("HTTP status %s instead of 101" % status, status, headers, body)
        want = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        if headers.get("sec-websocket-accept") != want:
            raise HandshakeError("wrong Sec-WebSocket-Accept", status, headers)
        self._pending = bytearray(rest)                              # bytes that arrived together with the header
        return self.info

    def _recv_exact(self, n, deadline):
        out = bytearray()
        while len(out) < n:
            if self._pending:
                take = bytes(self._pending[:n - len(out)])
                del self._pending[:len(take)]
                out += take
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise WsTimeout()
            self.sock.settimeout(min(remaining, 5.0))
            try:
                chunk = self.sock.recv(n - len(out))
            except (socket.timeout, ssl.SSLWantReadError):
                continue
            if not chunk:
                raise WsClosed("connection closed by the peer")
            out += chunk
        return bytes(out)

    def _send(self, opcode, payload=b""):
        if len(payload) > 125:
            raise WsProtocolError("control payload too long")
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes([0x80 | opcode, 0x80 | len(payload)]) + mask + masked)

    def recv_message(self, deadline):
        """Next data message as (opcode, payload). Control frames are handled here. Raises WsClosed / WsTimeout / WsProtocolError."""
        frag_op, frag = None, bytearray()
        while True:
            b0, b1 = self._recv_exact(2, deadline)
            fin, rsv, op = b0 & 0x80, b0 & 0x70, b0 & 0x0F
            if rsv:
                raise WsProtocolError("reserved bits set")
            if b1 & 0x80:
                raise WsProtocolError("server frame is masked")
            ln = b1 & 0x7F
            if ln == 126:
                ln = int.from_bytes(self._recv_exact(2, deadline), "big")
            elif ln == 127:
                ln = int.from_bytes(self._recv_exact(8, deadline), "big")
            if ln > MAX_FRAME:
                raise WsProtocolError("frame too large (%d bytes)" % ln)
            payload = self._recv_exact(ln, deadline)
            if op >= 8:
                if not fin or ln > 125:
                    raise WsProtocolError("bad control frame")
                if op == 8:
                    raise WsClosed("close frame received")
                if op == 9:
                    self.pings += 1
                    self._send(0xA, payload)
                elif op != 0xA:
                    raise WsProtocolError("unknown control opcode %d" % op)
                continue
            if op == 0:
                if frag_op is None:
                    raise WsProtocolError("continuation without a start")
                frag += payload
                if len(frag) > MAX_MESSAGE:
                    raise WsProtocolError("message too large")
                if fin:
                    return frag_op, bytes(frag)
            else:
                if frag_op is not None:
                    raise WsProtocolError("new data frame inside a fragmented message")
                if fin:
                    return op, payload
                frag_op, frag = op, bytearray(payload)

    def close(self):
        if self.sock is not None:
            try:
                self.sock.sendall(bytes([0x88, 0x80]) + os.urandom(4))
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


def classify(payload):
    """(kind, form): kind in force / kline / other; form RAW / COMBINED / None. Only used to count and cap; the raw bytes are what is stored."""
    try:
        d = json.loads(payload.decode("utf-8"))
    except Exception:
        return "other", None
    if not isinstance(d, dict):
        return "other", None
    form = "RAW"
    if "stream" in d and isinstance(d.get("data"), dict):
        form, d = "COMBINED", d["data"]
    e = d.get("e")
    return ({"forceOrder": "force", "kline": "kline"}.get(e, "other") if isinstance(e, str) else "other"), form


def now_ms():
    return time.time_ns() // 1_000_000


class Budget:
    """Global caps across all connections: forceOrder frames <= max_force, kline frames <= max_kline."""

    def __init__(self, max_force, max_kline):
        self.left = {"force": max_force, "kline": max_kline}


def run_connection(label, path, want, budget, writer, seconds, host=HOST, port=PORT, tls=True, ctx=None, log=print, connect_timeout=15.0):
    """Record frames from one connection until the wanted counts are reached, the time is up, or the connection ends. Returns a summary dict."""
    s = {"label": label, "path": path, "wanted": dict(want), "got": {"force": 0, "kline": 0, "other": 0}, "discarded_over_cap": 0,
         "forms": [], "outcome": None, "http": None, "pings": 0}
    t0 = time.monotonic()
    if all(want.get(k, 0) <= 0 or budget.left[k] <= 0 for k in ("force", "kline")):
        s["outcome"] = "skipped: nothing left to record within the global caps"
        return s
    c = WsClient(host, port, path, tls, connect_timeout=connect_timeout, ctx=ctx)
    try:
        s["http"] = c.open()
    except HandshakeError as e:
        s["outcome"] = "handshake_failed: %s" % e
        s["http"] = {"status": e.status, "date": e.headers.get("date"), "server": e.headers.get("server"), "body_head": e.body[:300].decode("latin-1")}
        return s
    except ssl.SSLCertVerificationError as e:
        s["outcome"] = "tls_certificate_error: %s (see README, macOS certificate note)" % e
        return s
    except OSError as e:
        s["outcome"] = "connect_error: %s" % e
        return s
    deadline = t0 + seconds
    try:
        while True:
            if all(s["got"][k] >= want.get(k, 0) or budget.left[k] <= 0 for k in ("force", "kline")):
                s["outcome"] = "complete"
                break
            try:
                op, payload = c.recv_message(deadline)
            except WsTimeout:
                s["outcome"] = "timeout"
                break
            except WsClosed as e:
                s["outcome"] = "closed_by_peer: %s" % e
                break
            except WsProtocolError as e:
                s["outcome"] = "protocol_error: %s" % e
                break
            t = now_ms()
            kind, form = classify(payload) if op == 1 else ("other", None)
            if kind in ("force", "kline"):
                if s["got"][kind] >= want.get(kind, 0) or budget.left[kind] <= 0:
                    s["discarded_over_cap"] += 1
                    continue
                budget.left[kind] -= 1
            elif s["got"]["other"] >= MAX_OTHER_KEPT:
                s["discarded_over_cap"] += 1
                continue
            s["got"][kind] += 1
            if form and form not in s["forms"]:
                s["forms"].append(form)
            writer(label, path, t, op, kind, form, payload)
            log("  %s: %s %d/%s" % (label, kind, s["got"][kind], want.get(kind, "-")))
    finally:
        s["pings"] = c.pings
        c.close()
        s["seconds"] = round(time.monotonic() - t0, 1)
    return s


def opened(r):
    """True if the websocket upgrade succeeded (HTTP 101), whatever happened afterwards."""
    return r.get("http") is not None and r["http"].get("status") == 101


def retryable(r):
    """True only when the connection could not be established at all: no TCP/TLS answer, or no HTTP answer to the upgrade request.
    A real HTTP status (403, 451 ...), a certificate error, a protocol error and anything after the handshake are never retried."""
    o = r["outcome"] or ""
    if o.startswith("connect_error"):
        return True
    return o.startswith("handshake_failed") and r["http"] is not None and r["http"].get("status") is None


def run_with_retries(label, path, want, budget, writer, seconds, attempts=1, wait=RETRY_WAIT_S, sleep=time.sleep, log=print, **kw):
    """run_connection, repeated (at most `attempts` times, `wait` seconds apart) while the failure is retryable. A failed attempt records no frame."""
    outcomes = []
    for k in range(1, attempts + 1):
        r = run_connection(label, path, want, budget, writer, seconds, log=log, **kw)
        outcomes.append(r["outcome"])
        if k == attempts or not retryable(r):
            break
        log("  attempt %d/%d failed (%s); trying again in %d s" % (k, attempts, r["outcome"], wait))
        sleep(wait)
    r["attempts"] = len(outcomes)
    r["attempt_outcomes"] = outcomes
    return r


def run_watch(label, path, want, budget, writer, total_seconds, attempts, wait, sleep, log, pause=WATCH_PAUSE_S, max_dead=WATCH_MAX_DEAD,
              max_connections=MAX_WATCH_CONNECTIONS, clock=time.monotonic, **kw):
    """Watch mode: keep ONE stream open for up to total_seconds, reconnecting `pause` seconds after every hang-up, until the wanted number of
    forceOrder frames has arrived, the global caps are used up, the time is over, too many connections were made, or `max_dead` rounds in a row
    could not even open a connection. Returns (results, why). Same host, same caps, same TLS checks as everything else in this tool."""
    end = clock() + total_seconds
    need, got, dead, results = want["force"], 0, 0, []
    while True:
        remaining = end - clock()
        if got >= need or budget.left["force"] <= 0:
            return results, "frames_complete"
        if remaining <= 0.5:
            return results, "time_over"
        if len(results) >= max_connections:
            return results, "too_many_connections"
        if dead >= max_dead:
            return results, "network_dead"
        k = len(results) + 1
        log("watch connection #%d (%d s of the watch left, %d/%d frame(s) so far)" % (k, remaining, got, need))
        r = run_with_retries("%s#%d" % (label, k), path, {"force": need - got, "kline": 0}, budget, writer, min(remaining, MAX_SECONDS_HARD), attempts, wait, sleep, log, **kw)
        results.append(r)
        got += r["got"]["force"]
        dead = 0 if opened(r) else dead + 1
        log("  -> %s" % r["outcome"])
        if got < need and budget.left["force"] > 0:
            sleep(pause)


def build_plan(route, max_force, max_kline, seconds, legacy, all_market=False, skip_kline_raw=False, watch_minutes=None, stop_after=1):
    pre = "" if route == "none" else "/" + route
    if watch_minutes:
        return [("btc_watch", "%s/ws/btcusdt@forceOrder" % pre, {"kline": 0, "force": min(stop_after, max_force)}, watch_minutes * 60)]
    plan = [
        ("kline_raw", "%s/ws/btcusdt@kline_1m" % pre, {"kline": min(3, max_kline), "force": 0}, min(60, seconds)),
        ("combined", "%s/stream?streams=btcusdt@forceOrder/btcusdt@kline_1m" % pre, {"kline": max_kline, "force": max_force // 2}, seconds),
        ("force_raw", "%s/ws/btcusdt@forceOrder" % pre, {"kline": 0, "force": max_force}, seconds),
    ]
    if skip_kline_raw:
        plan = plan[1:]
    if all_market:
        plan.append(("force_all_market", "%s/ws/!forceOrder@arr" % pre, {"kline": 0, "force": max_force}, seconds))
    if legacy:
        plan.append(("force_legacy_unrouted", "/ws/btcusdt@forceOrder", {"kline": 0, "force": max_force}, min(60, seconds)))
    return plan


def run_all(plan, budget, out_dir, host=HOST, port=PORT, tls=True, ctx=None, log=print, attempts=1, wait=RETRY_WAIT_S, sleep=time.sleep, connect_timeout=15.0, watch=None):
    os.makedirs(out_dir)                                              # fails if it exists: never overwrite an earlier capture
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    summary = {"tool": TOOL_VERSION, "python": sys.version.split()[0], "platform": platform.platform(), "started_utc": started,
               "scope": "format-only dry run; no price or outcome analysis was performed", "connections": [], "interrupted": False}
    n = {"i": 0}
    cap = open(os.path.join(out_dir, "capture.jsonl"), "x", encoding="utf-8")

    def writer(label, path, t, op, kind, form, payload):
        n["i"] += 1
        cap.write(json.dumps({"i": n["i"], "conn": label, "path": path, "recv_ms": t, "opcode": op, "kind": kind, "form": form,
                              "sha256": hashlib.sha256(payload).hexdigest(), "raw_b64": base64.b64encode(payload).decode()}, separators=(",", ":")) + "\n")
        cap.flush()

    try:
        if watch is not None:
            label, path, want, seconds = plan[0]
            results, why = run_watch(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host, port=port, tls=tls, ctx=ctx,
                                     connect_timeout=connect_timeout, **watch)
            summary["connections"].extend(results)
            summary["watch"] = {"stopped_because": why, "connections": len(results), "frames_wanted": want["force"], "seconds_allowed": seconds,
                                "force_frames": sum(r["got"]["force"] for r in results), "seconds_open": round(sum(r.get("seconds", 0) for r in results), 1)}
            plan = []
        for idx, (label, path, want, seconds) in enumerate(plan):
            log("connection %d/%d: %s%s" % (idx + 1, len(plan), label, path))
            r = run_with_retries(label, path, want, budget, writer, seconds, attempts, wait, sleep, log, host=host, port=port, tls=tls, ctx=ctx, connect_timeout=connect_timeout)
            summary["connections"].append(r)
            log("  -> %s" % r["outcome"])
            if idx == 0 and not opened(r):                            # a connection that opened and was hung up later is NOT a reason to stop
                summary["aborted_after_first_connection"] = True
                break
    except KeyboardInterrupt:
        summary["interrupted"] = True
    finally:
        cap.close()
        summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        summary["frames_recorded"] = n["i"]
        with open(os.path.join(out_dir, "summary.json"), "x", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1, sort_keys=True)
            fh.write("\n")
    return summary


def parse_args(argv):
    p = argparse.ArgumentParser(description="D-LIQ format-only dry run (see the module docstring).")
    p.add_argument("--out-dir", required=True, help="NEW directory for capture.jsonl and summary.json (must not exist)")
    p.add_argument("--route", choices=("market", "public", "none"), default="market", help="endpoint route prefix (default: market); 'none' = legacy unrouted path")
    p.add_argument("--max-force", type=int, default=MAX_FORCE_HARD, help="at most this many forceOrder frames in total (hard limit %d)" % MAX_FORCE_HARD)
    p.add_argument("--max-kline", type=int, default=6, help="at most this many kline frames in the combined stream (hard limit %d)" % MAX_KLINE_HARD)
    p.add_argument("--seconds", type=int, default=600, help="time limit per connection (hard limit %d)" % MAX_SECONDS_HARD)
    p.add_argument("--also-all-market", action="store_true", help="also listen to the all-market liquidation stream (any symbol; same message format; use when BTCUSDT is quiet)")
    p.add_argument("--skip-kline-raw", action="store_true", help="do not run the first (kline-only) connection, e.g. when kline frames were already captured")
    p.add_argument("--connect-attempts", type=int, default=3, help="tries per connection when the network gives NO answer at all (VPN hiccup); default 3, hard limit %d" % MAX_ATTEMPTS_HARD)
    p.add_argument("--connect-timeout", type=int, default=15, help="seconds to wait for TCP/TLS/HTTP upgrade per try (5-60, default 15)")
    p.add_argument("--watch-btc-minutes", type=int, default=0, help="WATCH MODE: keep /market/ws/btcusdt@forceOrder open for up to this many minutes (1-%d), reconnecting after every hang-up, until --watch-stop-after frames arrived" % MAX_WATCH_MIN_HARD)
    p.add_argument("--watch-stop-after", type=int, default=1, help="watch mode: stop after this many BTCUSDT forceOrder frames (default 1, at most --max-force)")
    p.add_argument("--also-legacy", action="store_true", help="also try the old unrouted /ws/ path for 60 s (diagnostic)")
    p.add_argument("--i-approve-format-only-dryrun", action="store_true", help="REQUIRED: the owner's explicit approval of exactly this capture")
    a = p.parse_args(argv)
    if not (1 <= a.max_force <= MAX_FORCE_HARD):
        p.error("--max-force must be between 1 and %d" % MAX_FORCE_HARD)
    if not (1 <= a.max_kline <= MAX_KLINE_HARD):
        p.error("--max-kline must be between 1 and %d" % MAX_KLINE_HARD)
    if not (1 <= a.connect_attempts <= MAX_ATTEMPTS_HARD):
        p.error("--connect-attempts must be between 1 and %d" % MAX_ATTEMPTS_HARD)
    if not (5 <= a.connect_timeout <= 60):
        p.error("--connect-timeout must be between 5 and 60")
    if not (10 <= a.seconds <= MAX_SECONDS_HARD):
        p.error("--seconds must be between 10 and %d" % MAX_SECONDS_HARD)
    if not (0 <= a.watch_btc_minutes <= MAX_WATCH_MIN_HARD):
        p.error("--watch-btc-minutes must be between 1 and %d (0 = off)" % MAX_WATCH_MIN_HARD)
    if not (1 <= a.watch_stop_after <= a.max_force):
        p.error("--watch-stop-after must be between 1 and --max-force")
    if a.watch_btc_minutes and (a.also_all_market or a.also_legacy or a.skip_kline_raw):
        p.error("watch mode watches the single BTCUSDT forceOrder stream only; do not combine it with --also-all-market, --also-legacy or --skip-kline-raw")
    return a


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    plan = build_plan(a.route, a.max_force, a.max_kline, a.seconds, a.also_legacy, a.also_all_market, a.skip_kline_raw, a.watch_btc_minutes, a.watch_stop_after)
    print("Plan (host %s only; no login, no key, no order, no analysis):" % HOST)
    for label, path, want, secs in plan:
        print("  %-22s wss://%s%s  wants %s, up to %d s" % (label, HOST, path, want, secs))
    print("  (a connection that gets no answer at all from the network is tried up to %d times, %d s each; a real refusal such as HTTP 451 is never retried)" % (a.connect_attempts, a.connect_timeout))
    if a.watch_btc_minutes:
        print("  WATCH MODE: reconnects after every hang-up for up to %d minutes, stops after %d BTCUSDT forceOrder frame(s) (never more than %d in total); no output between connections is normal"
              % (a.watch_btc_minutes, a.watch_stop_after, a.max_force))
    if not a.i_approve_format_only_dryrun:
        print("\nNothing was done. To run exactly this, add --i-approve-format-only-dryrun (your explicit approval).")
        return 2
    if os.path.exists(a.out_dir):
        print("FAIL: %s already exists; give a new directory." % a.out_dir)
        return 2
    extra = {"watch": {}} if a.watch_btc_minutes else {}
    summary = run_all(plan, Budget(a.max_force, MAX_KLINE_HARD), a.out_dir, attempts=a.connect_attempts, connect_timeout=a.connect_timeout, **extra)
    print("\nDone. %d frame(s) recorded in %s" % (summary["frames_recorded"], a.out_dir))
    w = summary.get("watch")
    if w:
        print("Watch ended (%s) after %d connection(s), %s s open: %d BTCUSDT forceOrder frame(s) recorded." % (w["stopped_because"], w["connections"], w["seconds_open"], w["force_frames"]))
        if w["force_frames"] == 0:
            print("No BTCUSDT forceOrder frame arrived: a quiet market, or the network path; see summary.json.")
        return 0 if any(opened(c) for c in summary["connections"]) else 1
    first = summary["connections"][0] if summary["connections"] else None
    if first and not opened(first):
        print("The first connection could not be opened: %s\nTry another VPN node or country (not the USA), or see the README." % first["outcome"])
        return 1
    ended_early = [c["label"] for c in summary["connections"] if c["outcome"] != "complete"]
    if ended_early:
        print("These connections ended before their wanted frames arrived (hang-up by the network or the exchange, or a quiet stream): %s. See summary.json." % ", ".join(ended_early))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
