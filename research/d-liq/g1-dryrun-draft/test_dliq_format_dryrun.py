#!/usr/bin/env python3
"""Synthetic tests of dliq_format_dryrun.py against a LOCAL fake websocket server written by the same author.
They show the tool follows RFC 6455 as the author understood it, obeys its caps and never writes outside the new directory.
They do NOT show that the real exchange behaves this way: that is exactly what the dry run is for.
Run: python3 -I -B test_dliq_format_dryrun.py   (from this directory)"""
import ast
import base64
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dliq_format_dryrun as D  # noqa: E402

GUID = D.GUID

# SAFETY NET: no test (and no deliberately broken mutant of the tool) may ever reach a real host. Only the loopback address is allowed.
_REAL_CREATE_CONNECTION = socket.create_connection


def _loopback_only(address, *a, **k):
    if address[0] not in ("127.0.0.1", "localhost"):
        raise AssertionError("network access to %r attempted by a test" % (address,))
    return _REAL_CREATE_CONNECTION(address, *a, **k)


socket.create_connection = _loopback_only


def frame(op, payload=b"", fin=True, masked=False, rsv=0):
    b0 = (0x80 if fin else 0) | rsv | op
    n = len(payload)
    if n < 126:
        head = bytes([b0, (0x80 if masked else 0) | n])
    elif n < 65536:
        head = bytes([b0, (0x80 if masked else 0) | 126]) + n.to_bytes(2, "big")
    else:
        head = bytes([b0, (0x80 if masked else 0) | 127]) + n.to_bytes(8, "big")
    if masked:
        mask = b"\x01\x02\x03\x04"
        return head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return head + payload


def kline(t=1700000040000, o="35000.10", E=None, x=False):
    return json.dumps({"e": "kline", "E": E or t + 1000, "s": "BTCUSDT",
                       "k": {"t": t, "T": t + 59999, "s": "BTCUSDT", "i": "1m", "o": o, "x": x}}, separators=(",", ":")).encode()


def force(i=0):
    return json.dumps({"e": "forceOrder", "E": 1700000000000 + i, "o": {"s": "BTCUSDT", "S": "SELL", "p": "34999.9", "q": "0.01"}}, separators=(",", ":")).encode()


class FakeServer:
    """One listening socket; each accepted connection runs script(conn, request_head, state)."""

    def __init__(self, script, tls_ctx=None):
        self.script, self.tls_ctx, self.requests, self.received, self.errors = script, tls_ctx, [], [], []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self.t = threading.Thread(target=self.loop, daemon=True)
        self.t.start()

    def loop(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self.handle, args=(c,), daemon=True).start()

    def handle(self, c):
        try:
            if self.tls_ctx:
                c = self.tls_ctx.wrap_socket(c, server_side=True)
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = c.recv(4096)
                if not chunk:
                    return
                buf += chunk
            head = buf.split(b"\r\n\r\n")[0].decode("latin-1")
            self.requests.append(head)
            self.script(c, head, self)
        except Exception as e:          # the client may hang up at any time; remember anything unexpected
            self.errors.append(repr(e))
        finally:
            try:
                c.close()
            except Exception:
                pass

    def close(self):
        self.sock.close()


def accept_key(head):
    key = re.search(r"Sec-WebSocket-Key: (\S+)", head).group(1)
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def upgrade(c, head, bad_accept=False):
    acc = "AAAA" if bad_accept else accept_key(head)
    c.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n"
               "Date: Mon, 09 Nov 2026 10:00:00 GMT\r\nServer: fake\r\n\r\n" % acc).encode())


def send_then_hold(frames, hold=0.3):
    def script(c, head, srv):
        upgrade(c, head)
        for f in frames:
            c.sendall(f)
        time.sleep(hold)
    return script


def make_client(srv, path="/ws/x"):
    return D.WsClient("127.0.0.1", srv.port, path, tls=False, connect_timeout=5)


class Budget0(D.Budget):
    pass


class TestProtocol(unittest.TestCase):
    def client(self, srv, path="/ws/x"):
        c = make_client(srv, path)
        self.addCleanup(c.close)
        return c

    def run_one(self, frames, hold=0.3):
        srv = FakeServer(send_then_hold(frames, hold))
        self.addCleanup(srv.close)
        c = self.client(srv)
        c.open()
        self.addCleanup(c.close)
        return c, srv

    def test_handshake_sends_expected_request(self):
        srv = FakeServer(send_then_hold([]))
        self.addCleanup(srv.close)
        c = make_client(srv, "/market/ws/btcusdt@kline_1m")
        info = c.open()
        c.close()
        self.assertEqual(info["status"], 101)
        self.assertEqual(info["date"], "Mon, 09 Nov 2026 10:00:00 GMT")
        head = srv.requests[0]
        self.assertTrue(head.startswith("GET /market/ws/btcusdt@kline_1m HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n" % srv.port), head)
        for needle in ("Upgrade: websocket", "Connection: Upgrade", "Sec-WebSocket-Version: 13", "User-Agent: " + D.TOOL_VERSION):
            self.assertIn(needle, head)
        self.assertNotIn("Authorization", head)
        self.assertNotIn("MBX", head.upper())             # no API-key header ever (also checked statically below)
        self.assertNotIn("Cookie", head)

    def test_wrong_accept_rejected(self):
        srv = FakeServer(lambda c, h, s: upgrade(c, h, bad_accept=True))
        self.addCleanup(srv.close)
        with self.assertRaises(D.HandshakeError) as cm:
            make_client(srv).open()
        self.assertIn("Sec-WebSocket-Accept", str(cm.exception))

    def test_http_451_reported_with_body(self):
        def script(c, h, s):
            body = b'{"msg":"Service unavailable from a restricted location"}'
            c.sendall(b"HTTP/1.1 451 Unavailable For Legal Reasons\r\nDate: x\r\nServer: cloud\r\nContent-Length: %d\r\n\r\n" % len(body) + body)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        with self.assertRaises(D.HandshakeError) as cm:
            make_client(srv).open()
        self.assertEqual(cm.exception.status, 451)
        self.assertIn(b"restricted location", cm.exception.body)

    def test_server_closes_before_headers(self):
        srv = FakeServer(lambda c, h, s: None)
        self.addCleanup(srv.close)
        with self.assertRaises(D.HandshakeError):
            make_client(srv).open()

    def test_oversized_http_header_rejected(self):
        def script(c, head, srv):
            c.sendall(b"HTTP/1.1 200 OK\r\n" + b"X: " + b"a" * 20000)
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        with self.assertRaises(D.HandshakeError) as cm:
            make_client(srv).open()
        self.assertIn("too large", str(cm.exception))

    def test_silent_server_times_out_in_handshake(self):
        srv = FakeServer(lambda c, h, s: time.sleep(2))
        self.addCleanup(srv.close)
        c = D.WsClient("127.0.0.1", srv.port, "/ws/x", tls=False, connect_timeout=0.5)
        t0 = time.monotonic()
        with self.assertRaises(D.HandshakeError) as cm:
            c.open()
        self.assertIn("timeout", str(cm.exception))
        self.assertLess(time.monotonic() - t0, 2)

    def test_failed_handshakes_release_the_socket(self):
        scripts = {"timeout": lambda c, h, s: time.sleep(1.5), "closed": lambda c, h, s: None, "451": lambda c, h, s: c.sendall(b"HTTP/1.1 451 X\r\n\r\n"),
                   "bad accept": lambda c, h, s: upgrade(c, h, bad_accept=True), "too large": lambda c, h, s: c.sendall(b"HTTP/1.1 200 OK\r\nX: " + b"a" * 20000)}
        for name, script in scripts.items():
            with self.subTest(name):
                srv = FakeServer(script)
                self.addCleanup(srv.close)
                c = D.WsClient("127.0.0.1", srv.port, "/ws/x", tls=False, connect_timeout=0.5)
                with self.assertRaises(D.HandshakeError):
                    c.open()
                self.assertIsNone(c.sock, name)                    # released inside open(), not left to the garbage collector

    def test_small_medium_large_lengths(self):
        sizes = (0, 1, 125, 126, 300, 65535, 65536, 70000)
        msgs = [bytes([65 + i % 26]) * n for i, n in enumerate(sizes)]
        c, _ = self.run_one([frame(1, m) for m in msgs])
        dl = time.monotonic() + 5
        for m in msgs:
            self.assertEqual(c.recv_message(dl), (1, m))

    def test_binary_opcode_kept(self):
        c, _ = self.run_one([frame(2, b"\x00\xff")])
        self.assertEqual(c.recv_message(time.monotonic() + 5), (2, b"\x00\xff"))

    def test_fragmented_message_with_ping_in_the_middle(self):
        c, srv = self.run_one([frame(1, b"he", fin=False), frame(9, b"p1"), frame(0, b"ll", fin=False), frame(0, b"o")])
        self.assertEqual(c.recv_message(time.monotonic() + 5), (1, b"hello"))
        self.assertEqual(c.pings, 1)

    def test_ping_is_answered_with_masked_pong_carrying_the_payload(self):
        got = {}

        def script(c, head, srv):
            upgrade(c, head)
            c.sendall(frame(9, b"abc") + frame(1, b"x"))
            c.settimeout(3)
            data = b""
            while len(data) < 2 + 4 + 3:
                data += c.recv(64)
            got["pong"] = data

        srv = FakeServer(script)
        self.addCleanup(srv.close)
        c = self.client(srv)
        c.open()
        self.assertEqual(c.recv_message(time.monotonic() + 5), (1, b"x"))
        time.sleep(0.3)
        c.close()
        pong = got["pong"]
        self.assertEqual(pong[0], 0x8A)
        self.assertEqual(pong[1], 0x80 | 3)
        mask = pong[2:6]
        self.assertEqual(bytes(b ^ mask[i % 4] for i, b in enumerate(pong[6:9])), b"abc")

    def test_pong_frame_is_ignored(self):
        c, _ = self.run_one([frame(0xA, b"zz"), frame(1, b"x")])
        self.assertEqual(c.recv_message(time.monotonic() + 5), (1, b"x"))
        self.assertEqual(c.pings, 0)

    def test_close_frame(self):
        c, _ = self.run_one([frame(8, b"\x03\xe8")])
        with self.assertRaises(D.WsClosed) as cm:
            c.recv_message(time.monotonic() + 5)
        self.assertIn("close frame", str(cm.exception))       # not merely the TCP hang-up that follows it

    def test_peer_hangs_up(self):
        srv = FakeServer(lambda c, h, s: upgrade(c, h))
        self.addCleanup(srv.close)
        c = self.client(srv)
        c.open()
        with self.assertRaises(D.WsClosed):
            c.recv_message(time.monotonic() + 5)

    def test_timeout(self):
        c, _ = self.run_one([], hold=3)
        t0 = time.monotonic()
        with self.assertRaises(D.WsTimeout):
            c.recv_message(time.monotonic() + 0.4)
        self.assertLess(time.monotonic() - t0, 3)

    def test_protocol_violations(self):
        cases = {
            "masked server frame": frame(1, b"x", masked=True),
            "reserved bits": frame(1, b"x", rsv=0x40),
            "continuation without start": frame(0, b"x"),
            "new data frame inside fragmented": frame(1, b"a", fin=False) + frame(1, b"b"),
            "fragmented control": frame(9, b"x", fin=False),
            "unknown control opcode": frame(0xB, b""),
            "oversize frame": bytes([0x81, 127]) + (D.MAX_FRAME + 1).to_bytes(8, "big"),
            "oversize control": bytes([0x89, 126]) + (200).to_bytes(2, "big") + b"x" * 200,
        }
        for name, raw in cases.items():
            with self.subTest(name):
                c, _ = self.run_one([raw])
                with self.assertRaises(D.WsProtocolError):
                    c.recv_message(time.monotonic() + 5)

    def test_fragmented_message_over_limit(self):
        chunk = b"a" * 600000
        c, _ = self.run_one([frame(1, chunk, fin=False), frame(0, chunk, fin=True)])
        with self.assertRaises(D.WsProtocolError):
            c.recv_message(time.monotonic() + 5)

    def test_bytes_arriving_with_the_http_header_are_not_lost(self):
        def script(c, head, srv):
            acc = accept_key(head)
            c.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n" % acc).encode() + frame(1, b"first"))
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        c = self.client(srv)
        c.open()
        self.assertEqual(c.recv_message(time.monotonic() + 5), (1, b"first"))

    def test_data_split_across_tcp_segments(self):
        raw = frame(1, b"x" * 1000)

        def script(c, head, srv):
            upgrade(c, head)
            for i in range(0, len(raw), 7):
                c.sendall(raw[i:i + 7])
                time.sleep(0.0005)
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        c = self.client(srv)
        c.open()
        self.assertEqual(c.recv_message(time.monotonic() + 10), (1, b"x" * 1000))


class TestClassify(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(D.classify(kline()), ("kline", "RAW"))
        self.assertEqual(D.classify(force()), ("force", "RAW"))
        self.assertEqual(D.classify(json.dumps({"stream": "btcusdt@kline_1m", "data": json.loads(kline())}).encode()), ("kline", "COMBINED"))
        self.assertEqual(D.classify(json.dumps({"stream": "btcusdt@forceOrder", "data": json.loads(force())}).encode()), ("force", "COMBINED"))
        for junk in (b"\xff\xfe", b"not json", b"[1,2]", b'"s"', b"123", b"null", b'{"e":5}', b'{"e":"aggTrade"}', b'{"result":null,"id":1}', b'{"stream":"x","data":[1]}'):
            self.assertEqual(D.classify(junk)[0], "other", junk)
        self.assertEqual(D.classify(b'{"stream":"x","data":[1]}')[1], "RAW")   # a wrapper whose data is not an object is not "COMBINED"


class TestRunConnection(unittest.TestCase):
    def go(self, payloads, want, budget=None, seconds=3, tls=False, hold=0.2, script=None, **kw):
        """payloads: raw message bytes, each sent as one text frame (use script= for anything else)."""
        srv = FakeServer(script or send_then_hold([frame(1, x) for x in payloads], hold))
        self.addCleanup(srv.close)
        rec = []
        out = D.run_connection("t", "/ws/x", want, budget or D.Budget(20, 10), lambda *a: rec.append(a), seconds,
                               host="127.0.0.1", port=srv.port, tls=tls, log=lambda *a: None, **kw)
        return out, rec, srv

    def test_stops_when_wanted_counts_reached(self):
        out, rec, _ = self.go([force(i) for i in range(5)], {"force": 3, "kline": 0})
        self.assertEqual(out["outcome"], "complete")
        self.assertEqual(out["got"]["force"], 3)
        self.assertEqual(len(rec), 3)
        self.assertEqual(out["http"]["status"], 101)

    def test_extra_frames_over_the_cap_are_discarded_not_recorded(self):
        out, rec, _ = self.go([force(i) for i in range(30)] , {"force": 20, "kline": 0}, hold=0.5)
        self.assertEqual(out["got"]["force"], 20)
        self.assertEqual(len(rec), 20)

    def test_global_budget_caps_across_connections(self):
        b = D.Budget(4, 10)
        o1, r1, _ = self.go([force(i) for i in range(10)], {"force": 3, "kline": 0}, budget=b)
        o2, r2, _ = self.go([force(i) for i in range(10)], {"force": 3, "kline": 0}, budget=b)
        self.assertEqual((len(r1), len(r2)), (3, 1))
        self.assertEqual(o2["outcome"], "complete")      # finished because the budget ran out, not after the timeout
        o3, r3, srv3 = self.go([], {"force": 3, "kline": 0}, budget=b)
        self.assertEqual(r3, [])
        self.assertTrue(o3["outcome"].startswith("skipped"))
        self.assertEqual(srv3.requests, [])               # no connection was opened at all

    def test_frame_over_the_budget_is_discarded_while_another_kind_is_still_wanted(self):
        b = D.Budget(1, 10)
        out, rec, _ = self.go([force(1), force(2), force(3)], {"force": 5, "kline": 5}, budget=b, seconds=3, hold=0.6)
        self.assertEqual(len(rec), 1)
        self.assertEqual(out["got"]["force"], 1)
        self.assertEqual(out["discarded_over_cap"], 2)
        self.assertEqual(b.left["force"], 0)                  # never negative

    def test_kline_budget_ends_the_connection_early(self):
        b = D.Budget(20, 2)
        out, rec, _ = self.go([kline(1700000040000 + 60000 * i) for i in range(5)], {"force": 0, "kline": 6}, budget=b, seconds=5)
        self.assertEqual(out["outcome"], "complete")
        self.assertEqual(len(rec), 2)

    def test_forms_and_kinds_are_recorded(self):
        comb = json.dumps({"stream": "btcusdt@forceOrder", "data": json.loads(force())}).encode()
        out, rec, _ = self.go([kline(), comb, force()], {"force": 2, "kline": 1})
        self.assertEqual(sorted(out["forms"]), ["COMBINED", "RAW"])
        self.assertEqual([r[4] for r in rec], ["kline", "force", "force"])

    def test_other_frames_are_kept_only_up_to_a_small_cap(self):
        out, rec, _ = self.go([b'{"result":null,"id":1}'] * 9 + [force()], {"force": 1, "kline": 0})
        self.assertEqual(out["got"]["other"], D.MAX_OTHER_KEPT)
        self.assertEqual(out["discarded_over_cap"], 9 - D.MAX_OTHER_KEPT)
        self.assertEqual(out["outcome"], "complete")

    def test_timeout_outcome(self):
        out, rec, _ = self.go([], {"force": 1, "kline": 0}, seconds=1, script=send_then_hold([], hold=3))
        self.assertEqual(out["outcome"], "timeout")
        self.assertLess(out["seconds"], 2.5)

    def test_closed_by_peer_outcome(self):
        out, rec, _ = self.go([], {"force": 5, "kline": 0}, script=send_then_hold([frame(1, force()), frame(8, b"\x03\xe8")]))
        self.assertTrue(out["outcome"].startswith("closed_by_peer"), out)
        self.assertEqual(out["got"]["force"], 1)

    def test_protocol_error_outcome(self):
        out, rec, _ = self.go([], {"force": 5, "kline": 0}, script=send_then_hold([frame(1, b"x", masked=True)]))
        self.assertTrue(out["outcome"].startswith("protocol_error"), out)

    def test_pings_are_counted(self):
        out, rec, _ = self.go([], {"force": 1, "kline": 0}, script=send_then_hold([frame(9), frame(9), frame(1, force())]))
        self.assertEqual(out["pings"], 2)

    def test_handshake_failure_outcome_has_http_status_and_body(self):
        def script(c, h, s):
            c.sendall(b"HTTP/1.1 403 Forbidden\r\nServer: cdn\r\n\r\nblocked by region")
        out, rec, _ = self.go([], {"force": 1, "kline": 0}, script=script)
        self.assertTrue(out["outcome"].startswith("handshake_failed"))
        self.assertEqual(out["http"]["status"], 403)
        self.assertEqual(out["http"]["body_head"], "blocked by region")
        self.assertEqual(rec, [])

    def test_connection_refused_outcome(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        out = D.run_connection("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: None, 3, host="127.0.0.1", port=port, tls=False, log=lambda *a: None)
        self.assertTrue(out["outcome"].startswith("connect_error"), out)


@unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
class TestTls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.cert, cls.key = os.path.join(cls.tmp, "c.pem"), os.path.join(cls.tmp, "k.pem")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", cls.key, "-out", cls.cert, "-days", "1",
                        "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"], check=True, capture_output=True)
        cls.srv_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cls.srv_ctx.load_cert_chain(cls.cert, cls.key)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_untrusted_certificate_is_refused_by_default(self):
        srv = FakeServer(send_then_hold([frame(1, force())]), tls_ctx=self.srv_ctx)
        self.addCleanup(srv.close)
        rec = []
        out = D.run_connection("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: rec.append(a), 3, host="localhost", port=srv.port, tls=True, log=lambda *a: None)
        self.assertTrue(out["outcome"].startswith("tls_certificate_error"), out)
        self.assertEqual(rec, [])

    def test_trusted_certificate_works(self):
        srv = FakeServer(send_then_hold([frame(1, force())]), tls_ctx=self.srv_ctx)
        self.addCleanup(srv.close)
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(self.cert)
        rec = []
        out = D.run_connection("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: rec.append(a), 3, host="localhost", port=srv.port, tls=True, ctx=ctx, log=lambda *a: None)
        self.assertEqual(out["outcome"], "complete", out)
        self.assertEqual(len(rec), 1)

    def test_wrong_hostname_is_refused(self):
        srv = FakeServer(send_then_hold([]), tls_ctx=self.srv_ctx)
        self.addCleanup(srv.close)
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(self.cert)
        out = D.run_connection("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: None, 3, host="127.0.0.1", port=srv.port, tls=True, ctx=ctx, log=lambda *a: None)
        self.assertTrue(out["outcome"].startswith("tls_certificate_error"), out)


class TestRunAll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def plan(self, srv_ok):
        return [("a", "/ws/a", {"kline": 1, "force": 0}, 3), ("b", "/ws/b", {"kline": 0, "force": 2}, 3)]

    def test_capture_is_exact_and_summary_written(self):
        k, f1, f2 = kline(), force(1), force(2)

        def script(c, head, srv):
            upgrade(c, head)
            path = head.split(" ")[1]
            for raw in ([k] if path == "/ws/a" else [f1, f2]):
                c.sendall(frame(1, raw))
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        out = os.path.join(self.tmp, "o")
        s = D.run_all(self.plan(True), D.Budget(20, 10), out, host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        with open(os.path.join(out, "capture.jsonl"), encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh]
        self.assertEqual([x["i"] for x in lines], [1, 2, 3])
        self.assertEqual([base64.b64decode(x["raw_b64"]) for x in lines], [k, f1, f2])
        for x, raw in zip(lines, [k, f1, f2]):
            self.assertEqual(x["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn(x["kind"], ("kline", "force"))
            self.assertGreater(x["recv_ms"], 1_700_000_000_000)
        with open(os.path.join(out, "summary.json"), encoding="utf-8") as fh:
            summ = json.load(fh)
        self.assertEqual(summ["frames_recorded"], 3)
        self.assertEqual([c["outcome"] for c in summ["connections"]], ["complete", "complete"])
        self.assertEqual(sorted(os.listdir(out)), ["capture.jsonl", "summary.json"])
        self.assertIn("no price or outcome analysis", summ["scope"])
        self.assertEqual(s["frames_recorded"], 3)
        self.assertNotIn("127.0.0.1", json.dumps(summ))   # no address of the local machine or the peer is written

    def test_refuses_an_existing_directory(self):
        with self.assertRaises(FileExistsError):
            D.run_all([], D.Budget(1, 1), self.tmp, log=lambda *a: None)

    def test_stops_after_a_failed_first_connection(self):
        srv = FakeServer(lambda c, h, s: c.sendall(b"HTTP/1.1 451 X\r\n\r\n"))
        self.addCleanup(srv.close)
        out = os.path.join(self.tmp, "o")
        s = D.run_all(self.plan(False), D.Budget(20, 10), out, host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        self.assertTrue(s["aborted_after_first_connection"])
        self.assertEqual(len(s["connections"]), 1)
        self.assertEqual(len(srv.requests), 1)
        with open(os.path.join(out, "capture.jsonl"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "")
        self.assertTrue(os.path.exists(os.path.join(out, "summary.json")))

    def test_keyboard_interrupt_still_writes_the_summary(self):
        def writer_boom(*a, **k):
            raise KeyboardInterrupt
        srv = FakeServer(send_then_hold([frame(1, force())]))
        self.addCleanup(srv.close)
        out = os.path.join(self.tmp, "o")
        orig = D.run_connection

        def boom(*a, **k):
            raise KeyboardInterrupt
        D.run_connection = boom
        try:
            s = D.run_all([("a", "/ws/a", {"kline": 0, "force": 1}, 3)], D.Budget(5, 5), out, host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        finally:
            D.run_connection = orig
        self.assertTrue(s["interrupted"])
        self.assertTrue(os.path.exists(os.path.join(out, "summary.json")))


class TestRetries(unittest.TestCase):
    def stub(self, outcomes):
        """Replace run_connection by a scripted one; returns the list of calls."""
        calls = []
        seq = list(outcomes)

        def fake(label, path, want, budget, writer, seconds, **kw):
            calls.append(kw)
            return seq.pop(0)
        orig = D.run_connection
        D.run_connection = fake
        self.addCleanup(setattr, D, "run_connection", orig)
        return calls

    def result(self, outcome, status="absent"):
        return {"label": "t", "outcome": outcome, "http": None if status == "absent" else {"status": status}, "got": {}}

    def go(self, outcomes, attempts=3):
        calls = self.stub(outcomes)
        slept = []
        r = D.run_with_retries("t", "/ws/x", {}, None, None, 10, attempts=attempts, wait=7, sleep=slept.append, log=lambda *a: None, host="h", connect_timeout=22)
        return r, calls, slept

    def test_retryable_outcomes(self):
        yes = [self.result("connect_error: x"), self.result("connect_error: _ssl.c:1015: The handshake operation timed out"),
               self.result("handshake_failed: timeout waiting for the HTTP response", None)]
        no = [self.result("complete"), self.result("timeout"), self.result("closed_by_peer: x"), self.result("protocol_error: x"),
              self.result("tls_certificate_error: x"), self.result("skipped: nothing left"), self.result("handshake_failed: HTTP status 451 instead of 101", 451),
              self.result("handshake_failed: HTTP status 403 instead of 101", 403), self.result("handshake_failed: wrong Sec-WebSocket-Accept", 101),
              {"outcome": None, "http": None}]
        for r in yes:
            self.assertTrue(D.retryable(r), r)
        for r in no:
            self.assertFalse(D.retryable(r), r)

    def test_succeeds_on_the_third_try(self):
        r, calls, slept = self.go([self.result("connect_error: a"), self.result("handshake_failed: z", None), self.result("complete")])
        self.assertEqual((r["outcome"], r["attempts"]), ("complete", 3))
        self.assertEqual(r["attempt_outcomes"], ["connect_error: a", "handshake_failed: z", "complete"])
        self.assertEqual(slept, [7, 7])                        # waits between tries only, none after the last
        self.assertEqual(len(calls), 3)
        for kw in calls:
            self.assertEqual((kw["host"], kw["connect_timeout"]), ("h", 22))   # settings reach every try

    def test_gives_up_after_the_allowed_number_of_tries(self):
        r, calls, slept = self.go([self.result("connect_error: %d" % i) for i in range(5)], attempts=4)
        self.assertEqual((r["attempts"], len(calls), len(slept)), (4, 4, 3))
        self.assertEqual(r["outcome"], "connect_error: 3")     # the LAST failure is reported

    def test_no_retry_for_a_real_refusal_or_certificate_error(self):
        for res in (self.result("handshake_failed: HTTP status 451 instead of 101", 451), self.result("tls_certificate_error: x"), self.result("timeout"), self.result("complete")):
            r, calls, slept = self.go([res, self.result("complete")])
            self.assertEqual((r["attempts"], len(calls), slept), (1, 1, []), res["outcome"])

    def test_one_attempt_means_no_retry(self):
        r, calls, slept = self.go([self.result("connect_error: a"), self.result("complete")], attempts=1)
        self.assertEqual((r["attempts"], len(calls), slept), (1, 1, []))

    def test_against_a_real_flaky_local_server(self):
        n = {"c": 0}

        def script(c, head, srv):
            n["c"] += 1
            if n["c"] <= 2:
                return                                          # hang up without any HTTP answer: what a dead tunnel looks like
            upgrade(c, head)
            c.sendall(frame(1, force(1)))
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        rec, slept = [], []
        r = D.run_with_retries("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: rec.append(a), 5, attempts=3, wait=0.1, sleep=slept.append,
                               log=lambda *a: None, host="127.0.0.1", port=srv.port, tls=False)
        self.assertEqual((r["outcome"], r["attempts"], len(rec), len(slept)), ("complete", 3, 1, 2), r)
        self.assertEqual(len(srv.requests), 3)

    def test_451_is_asked_exactly_once(self):
        srv = FakeServer(lambda c, h, s: c.sendall(b"HTTP/1.1 451 X\r\n\r\n"))
        self.addCleanup(srv.close)
        r = D.run_with_retries("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: None, 5, attempts=5, wait=0.1, sleep=lambda s: None,
                               log=lambda *a: None, host="127.0.0.1", port=srv.port, tls=False)
        self.assertEqual((r["attempts"], len(srv.requests)), (1, 1))

    def test_run_all_records_attempts_in_the_summary_and_aborts_after_the_first_connection_gives_up(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        srv = FakeServer(lambda c, h, s: None)                  # never answers
        self.addCleanup(srv.close)
        s = D.run_all([("a", "/ws/a", {"kline": 1, "force": 0}, 3), ("b", "/ws/b", {"kline": 0, "force": 1}, 3)], D.Budget(5, 5), os.path.join(tmp, "o"),
                      host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None, attempts=3, wait=0, sleep=lambda x: None)
        self.assertEqual(len(srv.requests), 3)
        self.assertEqual(len(s["connections"]), 1)
        self.assertEqual(s["connections"][0]["attempts"], 3)
        self.assertTrue(s["aborted_after_first_connection"])
        with open(os.path.join(tmp, "o", "summary.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["connections"][0]["attempts"], 3)

    def test_run_all_passes_the_wait_between_tries(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        srv = FakeServer(lambda c, h, s: None)
        self.addCleanup(srv.close)
        slept = []
        D.run_all([("a", "/ws/a", {"kline": 1, "force": 0}, 3)], D.Budget(5, 5), os.path.join(tmp, "o"), host="127.0.0.1", port=srv.port, tls=False,
                  log=lambda *a: None, attempts=3, wait=9, sleep=slept.append)
        self.assertEqual(slept, [9, 9])

    def test_opened(self):
        self.assertTrue(D.opened({"http": {"status": 101}}))
        for r in ({"http": None}, {}, {"http": {"status": 451}}, {"http": {"status": None}}, {"http": {"status": 200}}):
            self.assertFalse(D.opened(r), r)

    def test_a_connection_hung_up_after_opening_does_not_stop_the_run(self):
        def script(c, head, srv):
            upgrade(c, head)
            path = head.split(" ")[1]
            if path == "/ws/a":
                c.sendall(frame(1, kline()))                    # one frame, then a TCP hang-up without a close frame
                time.sleep(0.2)
            elif path == "/ws/b":
                time.sleep(0.2)                                 # hang-up with no frame at all
            else:
                c.sendall(frame(1, force(1)))
                time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        plan = [("a", "/ws/a", {"kline": 5, "force": 0}, 3), ("b", "/ws/b", {"kline": 0, "force": 1}, 3), ("c", "/ws/c", {"kline": 0, "force": 1}, 3)]
        s = D.run_all(plan, D.Budget(5, 5), os.path.join(tmp, "o"), host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        self.assertEqual([c["label"] for c in s["connections"]], ["a", "b", "c"])
        self.assertTrue(s["connections"][0]["outcome"].startswith("closed_by_peer"))
        self.assertTrue(s["connections"][1]["outcome"].startswith("closed_by_peer"))
        self.assertEqual(s["connections"][2]["outcome"], "complete")
        self.assertNotIn("aborted_after_first_connection", s)
        self.assertEqual(s["frames_recorded"], 2)

    def test_default_run_all_does_not_retry(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        srv = FakeServer(lambda c, h, s: None)
        self.addCleanup(srv.close)
        D.run_all([("a", "/ws/a", {"kline": 1, "force": 0}, 3)], D.Budget(5, 5), os.path.join(tmp, "o"), host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        self.assertEqual(len(srv.requests), 1)

    def test_connect_timeout_is_applied(self):
        srv = FakeServer(lambda c, h, s: time.sleep(3))
        self.addCleanup(srv.close)
        t0 = time.monotonic()
        out = D.run_connection("t", "/ws/x", {"force": 1, "kline": 0}, D.Budget(5, 5), lambda *a: None, 30, host="127.0.0.1", port=srv.port, tls=False,
                               log=lambda *a: None, connect_timeout=0.5)
        self.assertLess(time.monotonic() - t0, 2.5)
        self.assertTrue(out["outcome"].startswith("handshake_failed"), out)
        self.assertIsNone(out["http"]["status"])


class TestPlanAndMain(unittest.TestCase):
    def test_routed_plan(self):
        plan = D.build_plan("market", 20, 6, 600, False)
        self.assertEqual([p[1] for p in plan], ["/market/ws/btcusdt@kline_1m", "/market/stream?streams=btcusdt@forceOrder/btcusdt@kline_1m", "/market/ws/btcusdt@forceOrder"])
        self.assertEqual(plan[0][2], {"kline": 3, "force": 0})
        self.assertEqual(plan[1][2], {"kline": 6, "force": 10})
        self.assertEqual(plan[2][2], {"kline": 0, "force": 20})
        self.assertEqual(plan[0][3], 60)

    def test_skip_kline_raw(self):
        full = D.build_plan("market", 20, 6, 600, False)
        skipped = D.build_plan("market", 20, 6, 600, False, False, True)
        self.assertEqual(skipped, full[1:])
        self.assertEqual([p[0] for p in skipped], ["combined", "force_raw"])
        self.assertEqual([p[0] for p in D.build_plan("market", 20, 6, 600, True, True, True)], ["combined", "force_raw", "force_all_market", "force_legacy_unrouted"])

    def test_public_none_legacy_and_all_market(self):
        self.assertTrue(all(p[1].startswith("/public/") for p in D.build_plan("public", 20, 6, 600, False)))
        self.assertTrue(all(p[1].startswith("/ws/") or p[1].startswith("/stream?") for p in D.build_plan("none", 20, 6, 600, False)))
        plan = D.build_plan("market", 20, 6, 600, True, True)
        self.assertEqual([p[0] for p in plan][-2:], ["force_all_market", "force_legacy_unrouted"])
        self.assertEqual(plan[-2][1], "/market/ws/!forceOrder@arr")
        self.assertEqual(plan[-1][1], "/ws/btcusdt@forceOrder")

    def test_every_plan_has_hard_limits(self):
        for route in ("market", "public", "none"):
            for p in D.build_plan(route, D.MAX_FORCE_HARD, D.MAX_KLINE_HARD, D.MAX_SECONDS_HARD, True, True):
                self.assertLessEqual(p[2]["force"], D.MAX_FORCE_HARD)
                self.assertLessEqual(p[2]["kline"], D.MAX_KLINE_HARD)
                self.assertLessEqual(p[3], D.MAX_SECONDS_HARD)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = D.main(argv)
            except SystemExit as e:
                rc = e.code
        return rc, out.getvalue(), err.getvalue()

    def test_without_approval_nothing_happens(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        target = os.path.join(tmp, "o")
        called = []
        orig = D.run_all
        D.run_all = lambda *a, **k: called.append(1)
        try:
            rc, out, err = self.run_main(["--out-dir", target])
        finally:
            D.run_all = orig
        self.assertEqual(rc, 2)
        self.assertEqual(called, [])
        self.assertFalse(os.path.exists(target))
        self.assertIn("Nothing was done", out)
        self.assertIn("--i-approve-format-only-dryrun", out)

    def test_existing_out_dir_refused(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        rc, out, err = self.run_main(["--out-dir", tmp, "--i-approve-format-only-dryrun"])
        self.assertEqual(rc, 2)
        self.assertIn("already exists", out)

    def test_out_of_range_arguments_rejected(self):
        for argv in (["--connect-attempts", "0"], ["--connect-attempts", "6"], ["--connect-timeout", "4"], ["--connect-timeout", "61"]):
            with self.subTest(argv):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as cm:
                        D.parse_args(["--out-dir", "/nonexistent/x"] + argv)
                self.assertEqual(cm.exception.code, 2)
        a = D.parse_args(["--out-dir", "/nonexistent/x"])
        self.assertEqual((a.connect_attempts, a.connect_timeout, a.skip_kline_raw), (3, 15, False))
        a = D.parse_args(["--out-dir", "/nonexistent/x", "--connect-attempts", "5", "--connect-timeout", "60", "--skip-kline-raw"])
        self.assertEqual((a.connect_attempts, a.connect_timeout, a.skip_kline_raw), (5, 60, True))
        for argv in (["--max-force", "21"], ["--max-force", "0"], ["--max-kline", "11"], ["--max-kline", "0"], ["--seconds", "9"], ["--seconds", "1801"], ["--route", "evil"]):
            with self.subTest(argv):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as cm:
                        D.parse_args(["--out-dir", "/nonexistent/x"] + argv)
                self.assertEqual(cm.exception.code, 2)
        for argv in (["--max-force", "20", "--max-kline", "10", "--seconds", "1800"], ["--max-force", "1", "--max-kline", "1", "--seconds", "10"]):
            D.parse_args(["--out-dir", "/nonexistent/x"] + argv)        # the limits themselves are allowed
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                D.parse_args([])                                         # --out-dir is required
        self.assertEqual(cm.exception.code, 2)

    def test_main_end_to_end_against_local_server(self):
        k = kline()

        def script(c, head, srv):
            upgrade(c, head)
            c.sendall(frame(1, k) + frame(1, force(1)) + frame(1, force(2)))
            time.sleep(0.3)
        srv = FakeServer(script)
        self.addCleanup(srv.close)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        target = os.path.join(tmp, "o")
        orig = D.run_all
        seen = {}

        def local_run_all(plan, budget, out_dir, **kw):
            seen["budget"] = dict(budget.left)
            seen["plan_hosts_ok"] = all(p[1].startswith("/market/") for p in plan)
            seen["kw"] = kw
            return orig(plan, budget, out_dir, host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        D.run_all = local_run_all
        try:
            rc, out, err = self.run_main(["--out-dir", target, "--max-force", "2", "--max-kline", "1", "--seconds", "10", "--connect-attempts", "4", "--connect-timeout", "9",
                                          "--i-approve-format-only-dryrun"])
        finally:
            D.run_all = orig
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(seen["budget"], {"force": 2, "kline": D.MAX_KLINE_HARD})   # the global caps are the ones asked for (kline: the hard cap)
        self.assertTrue(seen["plan_hosts_ok"])
        self.assertEqual(seen["kw"], {"attempts": 4, "connect_timeout": 9})        # the retry settings reach the runner
        self.assertIn("frame(s) recorded", out)
        self.assertTrue(os.path.exists(os.path.join(target, "capture.jsonl")))

    def test_main_passes_the_skip_flag_to_the_plan(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        seen = {}
        orig = D.run_all

        def stub(plan, budget, out_dir, **kw):
            seen["labels"] = [p[0] for p in plan]
            return {"frames_recorded": 0, "connections": [{"outcome": "complete", "label": "x", "http": {"status": 101}}]}
        D.run_all = stub
        try:
            rc, out, err = self.run_main(["--out-dir", os.path.join(tmp, "a"), "--skip-kline-raw", "--i-approve-format-only-dryrun"])
            self.assertEqual((rc, seen["labels"]), (0, ["combined", "force_raw"]))
            self.assertNotIn("kline_raw", out)
            rc, out, err = self.run_main(["--out-dir", os.path.join(tmp, "b"), "--i-approve-format-only-dryrun"])
            self.assertEqual((rc, seen["labels"]), (0, ["kline_raw", "combined", "force_raw"]))
            self.assertIn("tried up to 3 times, 15 s each", out)
        finally:
            D.run_all = orig

    def test_main_returns_0_and_names_early_endings_when_the_first_connection_opened(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        orig = D.run_all
        D.run_all = lambda plan, budget, out_dir, **kw: {"frames_recorded": 3, "connections": [
            {"label": "combined", "outcome": "closed_by_peer: connection closed by the peer", "http": {"status": 101}},
            {"label": "force_raw", "outcome": "complete", "http": {"status": 101}},
            {"label": "force_all_market", "outcome": "timeout", "http": {"status": 101}}]}
        try:
            rc, out, err = self.run_main(["--out-dir", os.path.join(tmp, "o"), "--i-approve-format-only-dryrun"])
        finally:
            D.run_all = orig
        self.assertEqual(rc, 0)
        self.assertIn("ended before their wanted frames arrived", out)
        self.assertIn("combined, force_all_market", out)
        self.assertNotIn("force_raw.", out)

    def test_main_returns_1_when_first_connection_fails(self):
        srv = FakeServer(lambda c, h, s: c.sendall(b"HTTP/1.1 451 X\r\n\r\n"))
        self.addCleanup(srv.close)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        orig = D.run_all
        D.run_all = lambda plan, budget, out_dir, **kw: orig(plan, budget, out_dir, host="127.0.0.1", port=srv.port, tls=False, log=lambda *a: None)
        try:
            rc, out, err = self.run_main(["--out-dir", os.path.join(tmp, "o"), "--i-approve-format-only-dryrun"])
        finally:
            D.run_all = orig
        self.assertEqual(rc, 1)
        self.assertRegex(out, r"(?m)^The first connection could not be opened: ")


class TestStaticSafety(unittest.TestCase):
    """The promises in the module docstring, checked on the source text."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, "dliq_format_dryrun.py"), encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.tree = ast.parse(cls.src)

    def test_only_standard_library_imports(self):
        allowed = {"argparse", "base64", "hashlib", "json", "os", "platform", "socket", "ssl", "sys", "time"}
        found = set()
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                found |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                found.add((n.module or "").split(".")[0])
        self.assertEqual(found, allowed)

    def test_only_one_host_name_appears(self):
        hosts = set(re.findall(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|dev|ru|ir|cn)\b", self.src))
        self.assertEqual(hosts, {"fstream.binance.com"})
        self.assertNotIn("http://", self.src)
        self.assertNotIn("https://", self.src)

    def test_no_credentials_orders_or_environment_access(self):
        low = self.src.lower()
        for word in ("apikey", "api_key", "secret", "signature", "listenkey", "os.environ", "getenv", "subprocess", "urllib", "requests", "eval(", "exec(", "__import__", "pickle"):
            self.assertNotIn(word, low, word)

    def test_certificate_verification_never_disabled(self):
        for word in ("CERT_NONE", "check_hostname", "_create_unverified_context", "verify=False", "set_ciphers"):
            self.assertNotIn(word, self.src, word)

    def test_file_writes_are_only_the_two_exclusive_output_files(self):
        opens = [n for n in ast.walk(self.tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"]
        self.assertEqual(len(opens), 2)
        for n in opens:
            mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else None
            self.assertEqual(mode, "x")            # exclusive create: an existing file is never overwritten or appended to
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Attribute) and n.attr in ("remove", "unlink", "rmdir", "rmtree", "rename", "replace", "chmod", "system", "popen"):
                self.fail("unexpected file/process operation: " + n.attr)

    def test_hard_limits_are_the_documented_ones(self):
        self.assertEqual((D.MAX_FORCE_HARD, D.MAX_KLINE_HARD, D.MAX_SECONDS_HARD), (20, 10, 1800))
        self.assertEqual(D.MAX_ATTEMPTS_HARD, 5)
        self.assertEqual((D.HOST, D.PORT), ("fstream.binance.com", 443))

    def test_script_runs_in_isolated_mode_and_does_nothing_without_approval(self):
        target = os.path.join(tempfile.mkdtemp(), "o")
        self.addCleanup(shutil.rmtree, os.path.dirname(target), True)
        # same entry point as `python3 -I dliq_format_dryrun.py --out-dir ...`, but with the network blocked even if the approval check were broken
        code = ("import sys, socket\n"
                "def boom(*a, **k): raise AssertionError('network attempted')\n"
                "socket.create_connection = boom\n"
                "sys.path.insert(0, %r)\nimport dliq_format_dryrun as D\n"
                "raise SystemExit(D.main(['--out-dir', %r]))\n" % (HERE, target))
        r = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Nothing was done", r.stdout)
        self.assertFalse(os.path.exists(target))


if __name__ == "__main__":
    unittest.main()
