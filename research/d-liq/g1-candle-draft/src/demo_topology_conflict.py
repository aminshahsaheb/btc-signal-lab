"""Synthetic demonstration (invented frames, no market data): why kline frames cannot simply be recorded as MSG events under the CURRENT
SLOT-replay contract (section 7 of JOURNAL_CONTRACT_v2, r4/r5), and that a per-connection `feed` filter resolves it.
It imports the message contract of the r4-draft package that is on main and asserts every outcome; exit status 0 = the three facts hold.
Run: python3 -I -B src/demo_topology_conflict.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "r4-draft", "src")))
import dliq_msg_contract_v1 as MC  # noqa: E402

TAU = 1_800_000_000_000 - (1_800_000_000_000 % 14_400_000)
OPEN, CLOSE = TAU - 2_000_000, TAU + 2_000_000


def force(E, side="BUY"):
    return json.dumps({"e": "forceOrder", "E": E, "o": {"s": "BTCUSDT", "S": side, "o": "LIMIT", "f": "IOC", "q": "0.5", "p": "100", "ap": "100", "X": "FILLED", "l": "0.5", "z": "0.5", "T": E}}, separators=(",", ":")).encode()


def kline(t):
    return json.dumps({"e": "kline", "E": t + 30_000, "s": "BTCUSDT", "k": {"t": t, "T": t + 59_999, "s": "BTCUSDT", "i": "1m", "o": "100.0", "x": False}}, separators=(",", ":")).encode()


def messages(force_conn, kline_conn):
    forces = [{"conn_id": force_conn, "recv_ms": TAU - 600_000 + i * 1000, "raw": force(TAU - 600_000 + i * 1000)} for i in range(6)]
    klines = [{"conn_id": kline_conn, "recv_ms": TAU - 900_000 + m * 60_000 + 31_000, "raw": kline(TAU - 900_000 + m * 60_000)} for m in range(16)]
    return forces, klines


def show(label, r):
    print("%-52s status=%-5s reasons=%-12s primary=%s N_total=%s malformed_voids=%s" % (label, r["status"], r["reasons"], r["primary_conn"], r["N_total"], r["malformed_voids"]))


def main():
    health = {1: [(OPEN, CLOSE)], 2: [(OPEN, CLOSE)]}
    # reference: only the forceOrder feed (force connection id 1)
    forces, klines = messages(1, 2)
    ref = MC.build_slot(TAU, forces, {1: health[1]})
    show("0  force feed only", ref)
    assert ref["status"] == "VALID" and ref["N_total"] == 6
    # fact 1: kline frames recorded as MSG on their own connection (id 2) are MALFORMED messages for the forceOrder contract and void the slot
    r1 = MC.build_slot(TAU, forces + klines, health)
    show("1  + kline frames as MSG on connection 2", r1)
    assert r1["status"] == "NONE" and r1["reasons"] == ["MALFORMED"] and r1["malformed_voids"] == 15
    # fact 2: a kline connection with the SMALLER id is also 'healthy' (the health rule only asks for a frame at least every 200 s, and a kline
    # stream delivers one far more often) and the rule 'smallest healthy connection id is primary' makes it primary: every forceOrder frame becomes NON_PRIMARY
    forces2, klines2 = messages(2, 1)
    r2 = MC.build_slot(TAU, forces2, health)           # the kline connection (id 1) contributes only its health interval here
    show("2  kline connection has the smaller id", r2)
    assert r2["primary_conn"] == 1 and r2["N_total"] == 0 and r2["ledger"]["NON_PRIMARY"] == 6 and r2["status"] == "NONE"
    # resolution (proposal A): a `feed` marker on CONN; the replay only sees MSG / PING / CONN of FORCE connections
    r3 = MC.build_slot(TAU, [m for m in forces2 + klines2 if m["conn_id"] == 2], {2: health[2]})
    show("3  kline connection filtered out by feed", r3)
    assert r3["status"] == "VALID" and r3["N_total"] == 6 and r3["primary_conn"] == 2
    print("DEMO OK (synthetic frames; shows the interaction, not market behaviour)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
