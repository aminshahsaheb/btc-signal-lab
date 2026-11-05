"""Tests for dliq_msg_contract_v1.py (spec r2 sections 4.1-4.5). SYNTHETIC FIXTURES ONLY; no socket, no market data.
Usage: python3 test_dliq_msg_contract_v1.py
Fixtures: fixtures/messages.jsonl (built by make_fixtures.py from the field list in Binance's public documentation;
          NOT recorded messages -- real raw samples are still OPEN-13 in the spec)."""
import base64
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dliq_msg_contract_v1 as M

FAILS = []
NTESTS = [0]


def check(name, cond, detail=""):
    NTESTS[0] += 1
    print(("PASS " if cond else "FAIL ") + name + ((" -- " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


H = 3_600_000
TAU = 1_793_001_600_000          # an arbitrary grid-aligned-looking instant in 2026 (ms); tests are relative to it
assert TAU % (4 * H) == 0


def msg_bytes(E, side="SELL", z="1", ap="100", X="FILLED", **top):
    m = {"e": "forceOrder", "E": E, "o": {"s": "BTCUSDT", "S": side, "o": "LIMIT", "f": "IOC", "q": z, "p": ap, "ap": ap,
                                           "X": X, "l": z, "z": z, "T": E}}
    m.update(top)
    return json.dumps(m, separators=(",", ":")).encode()


def M_(conn, recv, E, **kw):
    return {"conn_id": conn, "recv_ms": recv, "raw": msg_bytes(E, **kw)}


def healthy_all(conn=1):
    return {conn: [(TAU - 3 * H, TAU + H)]}


def five(conn=1, side="SELL", base_E=TAU - 600_000):
    return [M_(conn, base_E + i * 1000 + 50, base_E + i * 1000, side=side) for i in range(5)]


# ------------------------------------------------------------------------------------------ 1. fixtures ----
fx = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "messages.jsonl"))]
bad = []
for c in fx:
    r = M.classify(base64.b64decode(c["raw_b64"]))
    if r["class"] != c["expect_class"] or (c["expect_reason"] is not None and r["reason"] != c["expect_reason"]):
        bad.append((c["id"], c["expect_class"], c["expect_reason"], r["class"], r["reason"]))
check("fixtures: every fixture classified exactly as expected (class and reason)", not bad, "%d fixtures, mismatches=%r" % (len(fx), bad))
ids = [c["id"] for c in fx]
check("fixtures: ids are unique", len(ids) == len(set(ids)))
cnt = collections.Counter(c["expect_class"] for c in fx)
check("fixtures: all three classes are represented", set(cnt) == {"ELIGIBLE", "INELIGIBLE", "MALFORMED"}, str(dict(cnt)))

# ----------------------------------------------------------------------------- 2. classifier properties ----
r = M.classify(msg_bytes(TAU - 5, side="BUY", z="0.014", ap="98010.50"))
check("classify: eligible BUY returns exact Decimal values", r["class"] == "ELIGIBLE" and str(r["z"]) == "0.014" and str(r["ap"]) == "98010.50" and r["side"] == "BUY")
r = M.classify(msg_bytes(TAU - 5, z="0.1", ap="0.2"))
check("classify: weights use Decimal arithmetic, not float (0.1*0.2 == 0.02 exactly)", r["z"] * r["ap"] == M.Decimal("0.02"))
r = M.classify(b'{"e":"forceOrder","E":1793000000000.0,"o":{}}')
check("classify: E recorded only when it is an in-range JSON integer (float E -> E stays None)", r["E"] is None and r["class"] == "MALFORMED")
bad_t = msg_bytes(TAU - 5).replace(b'"T":%d' % (TAU - 5), b'"T":"x"')
r = M.classify(bad_t)
check("classify: malformed message with a valid E keeps E (used by section 4.3 for voiding)", r["class"] == "MALFORMED" and r["E"] == TAU - 5)
r = M.classify(b"\xff\xfe")
check("classify: invalid UTF-8 never raises", r["class"] == "MALFORMED" and r["reason"] == "utf8")
r = M.classify(b'{"e":"forceOrder"' + b"[" * 100000)
check("classify: deeply nested garbage does not raise (RecursionError is caught)", r["class"] == "MALFORMED")
check("classify: true/false are not integers for E (bool is not int)", M.classify(msg_bytes(TAU).replace(str(TAU).encode(), b"true", 1))["class"] == "MALFORMED")
check("classify: INELIGIBLE keeps E and X for the ledger", (lambda r: r["class"] == "INELIGIBLE" and r["E"] == TAU - 1 and r["X"] == "PARTIALLY_FILLED")(M.classify(msg_bytes(TAU - 1, X="PARTIALLY_FILLED"))))

# ------------------------------------------------------------------------------------ 3. health intervals ----
g = M.PARAMS["max_frame_gap_ms"]
check("health: no frames -> only open + max gap", M.health_intervals(1000, [], end_ms=10**9) == [(1000, 1000 + g)])
check("health: frames every 180 s form one run", M.health_intervals(0, [180_000, 360_000, 540_000], end_ms=10**9) == [(0, 540_000 + g)])
check("health: gap of exactly 200 s is still healthy", len(M.health_intervals(0, [g], end_ms=10**9)) == 1)
check("health: gap of 200 s + 1 ms breaks the run", M.health_intervals(0, [g + 1], end_ms=10**9) == [(0, g), (g + 1, g + 1 + g)])
check("health: close_ms caps the interval", M.health_intervals(0, [100_000], close_ms=150_000) == [(0, 150_000)])
check("health: frames after close are ignored", M.health_intervals(0, [100_000, 500_000], close_ms=150_000) == [(0, 150_000)])
check("health: frames before open are ignored", M.health_intervals(1000, [10, 500], end_ms=10**9) == [(1000, 1000 + g)])
check("health: unsorted frame times are handled", M.health_intervals(0, [360_000, 180_000], end_ms=10**9) == [(0, 360_000 + g)])
check("health: end_ms caps the open-ended interval", M.health_intervals(0, [100_000], end_ms=120_000) == [(0, 120_000)])

# ---------------------------------------------------------------------------------------- 4. slot building ----
s = M.build_slot(TAU, five(side="SELL"), healthy_all())
check("slot: 5 eligible SELL messages -> VALID, X_sn = -1, side -1", s["status"] == "VALID" and s["X_sn"] == -1.0 and s["side"] == -1 and s["N_total"] == 5, str(s["reasons"]))
s = M.build_slot(TAU, five(side="BUY"), healthy_all())
check("slot: 5 eligible BUY messages -> VALID, X_sn = +1, side +1", s["status"] == "VALID" and s["X_sn"] == 1.0 and s["side"] == 1)
s = M.build_slot(TAU, five()[:4], healthy_all())
check("slot: N_total = 4 -> NONE with reason N_TOTAL", s["status"] == "NONE" and s["reasons"] == ["N_TOTAL"] and s["N_total"] == 4)
s = M.build_slot(TAU, five()[:0], healthy_all())
check("slot: no messages at all -> NONE N_TOTAL (not VALID)", s["status"] == "NONE" and "N_TOTAL" in s["reasons"] and s["X_sn"] is None)

# half-open window [tau-900000, tau)
msgs = five()[:4] + [M_(1, TAU - 900_000 + 5, TAU - 900_000)]
check("slot: E = tau - 900000 is INSIDE the window (closed lower edge)", M.build_slot(TAU, msgs, healthy_all())["N_total"] == 5)
msgs = five()[:4] + [M_(1, TAU - 900_000 + 5, TAU - 900_001)]
s = M.build_slot(TAU, msgs, healthy_all())
check("slot: E = tau - 900001 is OUTSIDE the window", s["N_total"] == 4 and s["ledger"]["OUT_OF_WINDOW"] == 1)
msgs = five()[:4] + [M_(1, TAU + 5, TAU)]
s = M.build_slot(TAU, msgs, healthy_all())
check("slot: E = tau is OUTSIDE the window (open upper edge)", s["N_total"] == 4 and s["ledger"]["OUT_OF_WINDOW"] == 1)
msgs = five()[:4] + [M_(1, TAU - 1, TAU - 1)]
check("slot: E = tau - 1 is inside", M.build_slot(TAU, msgs, healthy_all())["N_total"] == 5)

# late rule
msgs = five()[:4] + [M_(1, TAU + 10_000, TAU - 1)]
check("slot: recv = tau + 10000 counts (late rule is <=)", M.build_slot(TAU, msgs, healthy_all())["N_total"] == 5)
msgs = five()[:4] + [M_(1, TAU + 10_001, TAU - 1)]
s = M.build_slot(TAU, msgs, healthy_all())
check("slot: recv = tau + 10001 is LATE and not counted", s["N_total"] == 4 and s["ledger"]["LATE"] == 1 and s["status"] == "NONE")

# MALFORMED voiding: V(tau) = [tau - 960000, tau + 10000]
junk = b"not json"
def with_junk(recv):
    return five() + [{"conn_id": 1, "recv_ms": recv, "raw": junk}]
for recv, expect_void in ((TAU - 960_000, True), (TAU - 960_001, False), (TAU, True), (TAU + 10_000, True), (TAU + 10_001, False)):
    s = M.build_slot(TAU, with_junk(recv), healthy_all())
    check("void: unparseable frame with recv = tau%+d %s the slot" % (recv - TAU, "voids" if expect_void else "does not void"),
          (s["status"] == "NONE" and "MALFORMED" in s["reasons"]) == expect_void and s["malformed_voids"] == int(expect_void))
bad_T = msg_bytes(TAU - 100).replace(b'"T":%d' % (TAU - 100), b'"T":"x"')
s = M.build_slot(TAU, five() + [{"conn_id": 1, "recv_ms": TAU - 5 * H, "raw": bad_T}], healthy_all())
check("void: malformed message with a valid E inside V voids even when recv_time is far outside V", s["status"] == "NONE" and "MALFORMED" in s["reasons"])
bad_E = msg_bytes(TAU - 100).replace(b'"E":%d' % (TAU - 100), b'"E":"x"')
s = M.build_slot(TAU, five() + [{"conn_id": 1, "recv_ms": TAU - 5 * H, "raw": bad_E}], healthy_all())
check("void: malformed message with NO valid E and recv outside V does not void", s["status"] == "VALID" and s["malformed_voids"] == 0)
s = M.build_slot(TAU, five() + [{"conn_id": 2, "recv_ms": TAU - 1000, "raw": junk}], {1: [(TAU - 3 * H, TAU + H)], 2: [(TAU - 3 * H, TAU + H)]})
check("void: a malformed frame on a STANDBY connection also voids (conservative by design; spec 4.3 is connection-independent)", s["status"] == "NONE" and "MALFORMED" in s["reasons"])
s = M.build_slot(TAU, five() + [M_(1, TAU - 2000, TAU - 2000, X="PARTIALLY_FILLED")], healthy_all())
check("void: INELIGIBLE messages never void a slot and are not counted", s["status"] == "VALID" and s["N_total"] == 5 and s["ledger"]["INELIGIBLE"] == 1)

# GAP and primary selection
s = M.build_slot(TAU, five(), {1: [(TAU - 3 * H, TAU + 9_999)]})
check("gap: healthy interval ending 1 ms before tau+L -> GAP", s["status"] == "NONE" and "GAP" in s["reasons"] and s["primary_conn"] is None)
s = M.build_slot(TAU, five(), {1: [(TAU - 960_000, TAU + 10_000)]})
check("gap: healthy interval exactly equal to V(tau) -> primary found", s["status"] == "VALID" and s["primary_conn"] == 1)
s = M.build_slot(TAU, five(), {1: [(TAU - 960_000 + 1, TAU + 10_000)]})
check("gap: healthy interval starting 1 ms after V(tau) starts -> GAP", "GAP" in s["reasons"])
s = M.build_slot(TAU, five(), {1: [(TAU - 3 * H, TAU - 100_000), (TAU - 90_000, TAU + H)]})
check("gap: V(tau) split across two healthy runs is NOT healthy (no stitching)", "GAP" in s["reasons"])
s = M.build_slot(TAU, five(conn=1) + five(conn=2), {1: [(TAU - 3 * H, TAU + H)], 2: [(TAU - 3 * H, TAU + H)]})
check("primary: lowest healthy id wins; the other connection's 5 messages are NON_PRIMARY, not merged", s["primary_conn"] == 1 and s["N_total"] == 5 and s["ledger"]["NON_PRIMARY"] == 5)
s = M.build_slot(TAU, five(conn=1) + five(conn=2), {1: [(TAU - 3 * H, TAU - 1000)], 2: [(TAU - 3 * H, TAU + H)]})
check("primary: connection 1 unhealthy over V -> falls back to connection 2", s["primary_conn"] == 2 and s["N_total"] == 5 and s["ledger"]["NON_PRIMARY"] == 5)
m1 = [M_(1, TAU - 500_000 + i * 10, TAU - 500_000 + i) for i in range(3)]
m2 = [M_(2, TAU - 400_000 + i * 10, TAU - 400_000 + i) for i in range(3)]
s = M.build_slot(TAU, m1 + m2, {1: [(TAU - 3 * H, TAU + H)], 2: [(TAU - 3 * H, TAU + H)]})
check("primary: 3 messages on each of two connections are NOT added up (no cross-connection merge) -> NONE N_TOTAL", s["status"] == "NONE" and s["N_total"] == 3)
s = M.build_slot(TAU, five(), {})
check("primary: no connection at all -> GAP and every eligible frame is NO_PRIMARY", "GAP" in s["reasons"] and s["ledger"]["NO_PRIMARY"] == 5 and "N_TOTAL" not in s["reasons"])

# clock
for off, expect in ((250, "VALID"), (-250, "VALID"), (251, "NONE"), (-251, "NONE")):
    s = M.build_slot(TAU, five(), healthy_all(), clock_offset_ms=off)
    check("clock: offset %+d ms -> %s" % (off, expect), s["status"] == expect and (("CLOCK" in s["reasons"]) == (expect == "NONE")))

# dedup: identical bytes on one connection are NOT collapsed
one = M_(1, TAU - 1000, TAU - 1000)
s = M.build_slot(TAU, [dict(one) for _ in range(5)], healthy_all())
check("dedup: five byte-identical frames on one connection are five deliveries (N_total = 5)", s["N_total"] == 5 and s["status"] == "VALID")

# weights / imbalance
msgs = [M_(1, TAU - 10_000 - i, TAU - 10_000 - i, side="BUY", z="3", ap="100") for i in range(3)] + \
       [M_(1, TAU - 5_000 - i, TAU - 5_000 - i, side="SELL", z="1", ap="100") for i in range(2)]
s = M.build_slot(TAU, msgs, healthy_all())
check("feature: X_sn = (900-200)/(900+200) with Decimal sums", s["status"] == "VALID" and abs(s["X_sn"] - 700 / 1100) < 1e-15 and s["sumW_BUY"] == "900" and s["sumW_SELL"] == "200")
msgs = [M_(1, TAU - 10_000 - i, TAU - 10_000 - i, side="BUY", z="1", ap="100") for i in range(3)] + \
       [M_(1, TAU - 5_000 - i, TAU - 5_000 - i, side="SELL", z="1.5", ap="100") for i in range(2)]
s = M.build_slot(TAU, msgs, healthy_all())
check("feature: exactly equal buy and sell notional -> NONE with reason ZERO", s["status"] == "NONE" and s["reasons"] == ["ZERO"] and s["X_sn"] == 0.0 and s["side"] == 0)
msgs = [M_(1, TAU - 10_000 - i, TAU - 10_000 - i, side="BUY", z="1", ap="100") for i in range(4)] + [M_(1, TAU - 3000, TAU - 3000, side="SELL", z="1000", ap="100")]
s = M.build_slot(TAU, msgs, healthy_all())
check("feature (documented weakness): one large order sets the sign (4 small BUY vs 1 huge SELL -> side -1)", s["side"] == -1 and s["N_BUY"] == 4 and s["N_SELL"] == 1)
big = "123456789012345678901234567890"
msgs = five()[:4] + [M_(1, TAU - 1000, TAU - 1000, side="BUY", z=big, ap="1")]
s = M.build_slot(TAU, msgs, healthy_all())
check("feature: 30-digit values are summed exactly (no float rounding in the sums)", s["sumW_BUY"] == big and s["sumW_SELL"] == "400")
check("feature: order of messages in the input does not change the result", M.build_slot(TAU, list(reversed(msgs)), healthy_all())["X_sn"] == s["X_sn"])

# ledger invariant (property test with an independent tiny generator)
x = [0x2545F4914F6CDD1D]
def rnd(n):
    x[0] ^= (x[0] << 13) & 0xFFFFFFFFFFFFFFFF
    x[0] ^= x[0] >> 7
    x[0] ^= (x[0] << 17) & 0xFFFFFFFFFFFFFFFF
    return x[0] % n
ok_all, nvalid, nnone = True, 0, 0
kinds = [lambda E: msg_bytes(E, side="BUY")] * 12 + [lambda E: msg_bytes(E, side="SELL")] * 12 + [lambda E: msg_bytes(E, X="NEW"),
         lambda E: msg_bytes(E, z="0"), lambda E: b"garbage", lambda E: msg_bytes(E).replace(b'"BTCUSDT"', b'"ETHUSDT"')]
# 24 of 28 kinds are eligible, 2 are INELIGIBLE, 2 are MALFORMED (about 7 percent), so that VALID slots occur as well as NONE slots
for t in range(500):
    n = 3 + rnd(30)
    msgs = []
    for _ in range(n):
        E = TAU - 1_100_000 + rnd(1_200_000)
        recv = E + rnd(30_000) - 2000
        msgs.append({"conn_id": 1 if rnd(4) else 2, "recv_ms": recv, "raw": kinds[rnd(len(kinds))](E)})
    hl = {1: [(TAU - 3 * H, TAU + H)]}
    if rnd(3) == 0:
        hl[2] = [(TAU - 3 * H, TAU + H)]
    if rnd(5) == 0:
        hl = {1: [(TAU - 3 * H, TAU - 500_000)]}
    s = M.build_slot(TAU, msgs, hl, clock_offset_ms=rnd(600) - 300)
    ok_all &= sum(s["ledger"].values()) == len(msgs) == s["n_messages"]
    ok_all &= (s["status"] == "VALID") == (not s["reasons"])
    ok_all &= s["N_total"] == s["N_BUY"] + s["N_SELL"] == s["ledger"]["COUNTED"]
    ok_all &= (s["status"] == "VALID") <= (s["N_total"] >= 5 and s["side"] in (-1, 1))
    nvalid += s["status"] == "VALID"
    nnone += s["status"] == "NONE"
check("ledger: 500 random message sets -- ledger sums to the message count, VALID <=> no reasons, counts consistent", ok_all, "VALID=%d NONE=%d" % (nvalid, nnone))
check("ledger: the random sets exercised both VALID and NONE slots", nvalid > 0 and nnone > 0)

print()
print("%d checks, %d failures" % (NTESTS[0], len(FAILS)))
if FAILS:
    print("FAILED: " + ", ".join(FAILS))
    sys.exit(1)
print("ALL PASS")
