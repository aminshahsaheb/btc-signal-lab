# D-LIQ G-1 dry run — format-only capture tool (DRAFT)

STATUS: **DRAFT. Not run against the real exchange. Not reviewed. Nothing here is a result, a collector, a probe, T0 or an edge claim.** The tests below run against a fake local server written by the same author as the tool; they show that the code follows the websocket protocol as the author understood it, not that the exchange behaves that way. That is what the dry run is for.

## Why it exists
Every field name and stream shape in the G-1 CANDLE proposal and in the message contract is `[VERIFY]` (documentation or third-party clients only), and the endpoint path of the single-symbol `forceOrder` stream is unverified (ROADMAP 2F, OPEN-10 / OPEN-13). The collector host is undecided and the owner's own connection to the exchange is not available directly. This tool lets the owner look at the real wire format once, for free, from his own computer through a VPN, before any server is paid for. It records **at most 20 raw `forceOrder` frames and at most 10 `kline_1m` frames** of BTCUSDT and nothing else (hard limits in the code, enforced and tested).

## What it does and does not do
- Connects only to `fstream.binance.com:443` over TLS (certificate and host name are verified; there is no switch to turn that off). Public market-data streams only. No login, no API key, no order, no account, no cookie, no upload, no environment-variable access.
- Writes only into a NEW directory that must not exist yet, using exclusive-create file modes: `capture.jsonl` (one line per recorded frame: exact bytes as base64, SHA-256, local receive time in ms, connection label, route path) and `summary.json` (outcome of each connection, HTTP status and `Date` header of the handshake, counters, Python and platform string). It contains no IP address and no personal data.
- Does no price, outcome, liquidation-size or "edge" analysis. It only classifies a frame as `force` / `kline` / `other` to count and cap it; the raw bytes are what is stored.
- Stops by itself: hard caps on frames, on seconds per connection (default 600, maximum 1800), and a stop after the first connection if it fails for good. A connection that gets **no answer at all** from the network (dead VPN tunnel: TCP/TLS/HTTP timeout) is tried up to 3 times (`--connect-attempts`, hard limit 5, 5 s apart, `--connect-timeout` 5-60 s per try); a real refusal (HTTP 451/403), a certificate error or anything after the handshake is never retried. A failed try records nothing.
- Standard library only (Python 3.8+). Needs the flag `--i-approve-format-only-dryrun`; without it the tool prints the plan and exits without doing anything. Passing the flag is the owner's explicit approval that ROADMAP 2F requires, for exactly the capture printed in the plan.

## Plan it executes (default route `market`)
| # | label | path | records |
|---|---|---|---|
| 1 | `kline_raw` | `/market/ws/btcusdt@kline_1m` | up to 3 kline frames (60 s) |
| 2 | `combined` | `/market/stream?streams=btcusdt@forceOrder/btcusdt@kline_1m` | up to 6 kline and 10 forceOrder frames |
| 3 | `force_raw` | `/market/ws/btcusdt@forceOrder` | up to the remaining forceOrder budget (20 in total) |
Optional: `--skip-kline-raw` (drop row 1, e.g. when kline frames are already captured), `--also-all-market` (all-symbol liquidation stream, same message format, for when BTCUSDT is quiet), `--also-legacy` (the old unrouted `/ws/btcusdt@forceOrder` path for 60 s, diagnostic), `--route public` / `--route none` (other route prefixes if `/market` is refused).

## What the first real run showed (owner's computer, VPN, 2026-11-09 22:24Z, tool version 1, 3 kline frames; frames not committed)
Observed, from one connection and three frames only:
- `wss://fstream.binance.com/market/ws/btcusdt@kline_1m` answered HTTP 101 and delivered RAW-form kline messages (3 frames in 2.3 s). The response had a `Date` header and no `Server` header. The TLS chain was a normal DigiCert chain (GeoTrust TLS RSA CA G1 under DigiCert Global Root G2), so the VPN does not intercept TLS.
- Shape: outer keys `e, E, s, k`; keys of `k`: `t, T, s, i, f, L, o, c, h, l, v, n, x, q, V, Q, B`; `e = "kline"`, `s = "BTCUSDT"`, `k.i = "1m"`, `k.t` a multiple of 60000, `k.T = k.t + 59999`, `k.o` a decimal string, `k.x` a boolean, `E` between `k.t` and `k.T`. The whitespace is irregular (no space between the outer keys, ", " inside `k`), so raw bytes must be stored and never re-serialised. The G-1 parser `parse_kline_frame` accepts all three frames unchanged.
- `recv_ms - E` was -4192, -4168 and -4183 ms: the owner's laptop clock is about 4.2 s behind the exchange; the HTTP `Date` header (1 s resolution) agrees with `E`. Laptop receipt times therefore say nothing about latency, and the contract's 250 ms clock bound needs a real anchor on the collector host.
- Not yet observed: any `forceOrder` frame, the combined-stream shape, the all-market stream, the legacy unrouted path. TLS handshakes through the owner's VPN (a TUN client with fake-IP DNS) timed out intermittently, which is why version 2 retries.
- Setup notes: python.org Python on macOS needs "Install Certificates.command" once (otherwise `CERTIFICATE_VERIFY_FAILED ... self-signed certificate in certificate chain`).

## Findings from public documentation — all `[VERIFY]`, `forceOrder` still not checked on the wire
Read on 2026-11-09 from Binance's official WebSocket pages (summarised by a small model; treat as unverified):
1. USD-M futures streams are **routed**: `/public`, `/market`, `/private`, each with `/ws/<stream>` and `/stream?streams=...`; `forceOrder` and `kline` are `/market` streams. The old unrouted paths were announced to deliver Public data only and to be decommissioned after 2026-04-23. The Forward Journal r7 draft already locks `wss://fstream.binance.com/market/ws/btcusdt@kline_5m`; the contract text and ROADMAP still say the `forceOrder` path is unverified.
2. The server pings about every 3 minutes (pong required within 10 minutes), a connection lives 24 h. The replay health rule (section 7, "frame or ping gap <= 200 s") could therefore keep a connection on a **wrong or empty route** looking healthy while it delivers no `forceOrder` frame at all, and a slot could then read as "no liquidations". Whether this can happen, and what the legacy path delivers today, is exactly what rows 3 and `--also-legacy` show. Do not change the contract on this until real frames exist.
3. HTTP 451 / 403 for some locations (USA among them): the tool prints the status and the first bytes of the body.

## Run (summary; the owner gets the exact steps in the conversation)
```
python3 dliq_format_dryrun.py --out-dir ~/dliq_dryrun_1                                  # prints the plan, does nothing
python3 dliq_format_dryrun.py --out-dir ~/dliq_dryrun_1 --i-approve-format-only-dryrun   # runs it
```
Tool version 2 adds retries, `--connect-timeout` and `--skip-kline-raw`; the file hash to check is in the conversation, never trust a hash printed only in this README.
A system-wide VPN (not a browser-only extension) with an exit outside the USA must be on, because the Terminal does not use the browser's proxy. A run takes up to about 20 minutes (liquidations are bursty; zero `forceOrder` frames in 10 minutes is possible and is itself informative; then rerun with `--also-all-market`). On macOS with a python.org installation a `tls_certificate_error` usually means "Install Certificates.command" has not been run; do not work around it by disabling verification.

What to send back: `capture.jsonl` and `summary.json` of the run, the VPN exit country, and the local time. They are public market data. **They must not be committed to the repository** (ROADMAP rule: captured exchange frames need an owner decision first).

## What a good outcome would and would not mean
- It would settle: which routed path actually accepts the connection, whether `forceOrder` frames arrive on `/market/ws/btcusdt@forceOrder`, raw versus combined shape, the real field names for `E`, `o.*`, `k.t/T/o/x`, whether the legacy path still delivers data, and the HTTP status from the owner's VPN path.
- It would NOT settle: anything about latency, frame loss, 24 h stability, the 200 s health rule, `L` (decision B), a production host, a clock anchor, or any statistical property of liquidations. It is a handful of frames seen once from one network path.

## Files
`dliq_format_dryrun.py` (tool) · `test_dliq_format_dryrun.py` (68 synthetic tests against a loopback fake server; every test and every deliberately broken mutant is blocked from reaching a real host by a loopback-only guard) · `mutation_check_dryrun.py` (68 deliberate-bug mutants, all must be killed) · `MANIFEST.sha256`, `logs/`.
```
python3 -I -B test_dliq_format_dryrun.py
python3 -I -B mutation_check_dryrun.py .
sha256sum -c MANIFEST.sha256
```
## Not done / not claimed
No run against the exchange; TLS behaviour was tested only with a self-signed local certificate; macOS and Windows were not tested (Linux, Python 3.13 only); the reviewer is the author's own test suite, there is no independent review of the tool; the path list may be wrong (that is the question).
