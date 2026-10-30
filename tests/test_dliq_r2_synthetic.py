from __future__ import annotations

import hashlib
import json
import re
import unittest
from decimal import Decimal, InvalidOperation
from typing import Any

NUMERIC_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")


def decimal_field(value: Any, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not NUMERIC_RE.fullmatch(value):
        raise ValueError("invalid decimal grammar")
    try:
        out = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not out.is_finite() or (positive and out <= 0):
        raise ValueError("decimal outside allowed range")
    return out


def validate_force_order(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("e") != "forceOrder":
        raise ValueError("wrong event type")
    if not isinstance(payload.get("E"), int) or payload["E"] <= 0:
        raise ValueError("invalid event time")
    order = payload.get("o")
    if not isinstance(order, dict) or order.get("s") != "BTCUSDT":
        raise ValueError("wrong symbol or order object")
    if order.get("S") not in {"BUY", "SELL"}:
        raise ValueError("invalid side")
    if order.get("X") != "FILLED":
        raise ValueError("status not accepted")
    if not isinstance(order.get("T"), int) or order["T"] <= 0:
        raise ValueError("invalid order time")
    q = decimal_field(order.get("q"), positive=True)
    p = decimal_field(order.get("p"))
    ap = decimal_field(order.get("ap"), positive=True)
    last = decimal_field(order.get("l"), positive=True)
    z = decimal_field(order.get("z"), positive=True)
    if z > q or last > z:
        raise ValueError("quantity relationship invalid")
    return {"event_time": payload["E"], "side": order["S"], "weight": z * ap, "price": p}


def fingerprint(raw_payload: bytes) -> str:
    return hashlib.sha256(raw_payload).hexdigest()


def deduplicate_overlap(records: list[dict[str, Any]], overlap_pairs: set[frozenset[str]]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    seen: dict[tuple[frozenset[str], str], tuple[bytes, str]] = {}
    duplicates = 0
    for rec in sorted(records, key=lambda x: (x["recv_time"], x["connection_id"])):
        raw = rec["raw"]
        duplicate = False
        for pair in overlap_pairs:
            if rec["connection_id"] in pair:
                key = (pair, fingerprint(raw))
                prior = seen.get(key)
                if prior is not None and prior[0] == raw and prior[1] != rec["connection_id"]:
                    duplicate = True
                    break
                seen[key] = (raw, rec["connection_id"])
        if duplicate:
            duplicates += 1
        else:
            kept.append(rec)
    return kept, duplicates


def assemble_blocks(slots: list[dict[str, Any]], starts: list[int], block_len: int) -> list[dict[str, Any]]:
    if block_len <= 0 or block_len > len(slots):
        raise ValueError("invalid block length")
    if any(start < 0 or start > len(slots) - block_len for start in starts):
        raise ValueError("block start out of range")
    out: list[dict[str, Any]] = []
    for start in starts:
        out.extend(slots[start:start + block_len])
    return out[:len(slots)]


def theta(slots: list[dict[str, Any]]) -> float | None:
    plus = [x["return_bps"] for x in slots if x.get("signal") == "LONG" and x.get("return_bps") is not None]
    minus = [x["return_bps"] for x in slots if x.get("signal") == "SHORT" and x.get("return_bps") is not None]
    if not plus or not minus:
        return None
    return (sum(plus) / len(plus) - sum(minus) / len(minus)) / 2.0


def journal_entry(seq: int, prev_hash: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    preimage = f"DLIQ-JOURNAL-v1\n{seq}\n{prev_hash}\n{event_type}\n{canonical}".encode("utf-8")
    return {"seq": seq, "prev_hash": prev_hash, "event_type": event_type, "payload": payload,
            "entry_hash": hashlib.sha256(preimage).hexdigest()}


def verify_chain(entries: list[dict[str, Any]]) -> bool:
    prev = "0" * 64
    for expected_seq, entry in enumerate(entries, start=1):
        if entry["seq"] != expected_seq or entry["prev_hash"] != prev:
            return False
        expected = journal_entry(entry["seq"], entry["prev_hash"], entry["event_type"], entry["payload"])["entry_hash"]
        if expected != entry["entry_hash"]:
            return False
        prev = entry["entry_hash"]
    return True


def replicate_validity(invalid_count: int, total_count: int) -> bool:
    if total_count <= 0 or invalid_count < 0 or invalid_count > total_count:
        return False
    return invalid_count / total_count <= 0.01


def checkpoint_head(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {"head_seq": 0, "head_hash": "0" * 64}
    return {"head_seq": entries[-1]["seq"], "head_hash": entries[-1]["entry_hash"]}


def verify_anchored_chain(entries: list[dict[str, Any]], anchor: dict[str, Any]) -> bool:
    if not verify_chain(entries):
        return False
    seq = anchor["head_seq"]
    if seq == 0:
        return anchor["head_hash"] == "0" * 64
    return len(entries) >= seq and entries[seq - 1]["entry_hash"] == anchor["head_hash"]


def linear_quantile(values: list[float], q: float) -> float:
    if not values or not 0 <= q <= 1:
        raise ValueError("invalid quantile input")
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos); hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


class TestDliqR2Synthetic(unittest.TestCase):
    def valid_payload(self) -> dict[str, Any]:
        return {"e": "forceOrder", "E": 1_800_000_000_000,
                "o": {"s": "BTCUSDT", "S": "BUY", "X": "FILLED", "T": 1_800_000_000_000,
                      "q": "0.020", "p": "0", "ap": "65000.50", "l": "0.020", "z": "0.020"}}

    def test_valid_payload_and_snapshot_notional(self):
        out = validate_force_order(self.valid_payload())
        self.assertEqual(out["weight"], Decimal("1300.010000"))

    def test_rejects_non_filled_status(self):
        p = self.valid_payload(); p["o"]["X"] = "PARTIALLY_FILLED"
        with self.assertRaises(ValueError): validate_force_order(p)

    def test_rejects_bad_numeric_grammar(self):
        for value in ["NaN", "Infinity", "1e3", "-1", " 1", ""]:
            p = self.valid_payload(); p["o"]["ap"] = value
            with self.subTest(value=value), self.assertRaises(ValueError): validate_force_order(p)

    def test_rejects_quantity_inconsistency(self):
        p = self.valid_payload(); p["o"]["z"] = "0.03"
        with self.assertRaises(ValueError): validate_force_order(p)
        p = self.valid_payload(); p["o"]["l"] = "0.03"
        with self.assertRaises(ValueError): validate_force_order(p)

    def test_exact_raw_dedup_only_across_overlap(self):
        raw = json.dumps(self.valid_payload(), separators=(",", ":")).encode()
        other = json.dumps({**self.valid_payload(), "E": 1_800_000_000_001}, separators=(",", ":")).encode()
        records = [
            {"connection_id": "A", "recv_time": 1, "raw": raw},
            {"connection_id": "B", "recv_time": 2, "raw": raw},
            {"connection_id": "A", "recv_time": 3, "raw": other},
        ]
        kept, ndup = deduplicate_overlap(records, {frozenset({"A", "B"})})
        self.assertEqual(ndup, 1)
        self.assertEqual(len(kept), 2)

    def test_same_connection_repeated_payload_is_not_deduplicated(self):
        raw = b'{"e":"forceOrder","E":1}'
        records = [{"connection_id":"A","recv_time":1,"raw":raw},{"connection_id":"A","recv_time":2,"raw":raw}]
        kept, ndup = deduplicate_overlap(records, {frozenset({"A","B"})})
        self.assertEqual(ndup, 0); self.assertEqual(len(kept), 2)

    def test_different_payloads_are_not_deduplicated(self):
        a = b'{"e":"forceOrder","E":1}'
        b = b'{"E":1,"e":"forceOrder"}'
        records = [{"connection_id":"A","recv_time":1,"raw":a},{"connection_id":"B","recv_time":2,"raw":b}]
        kept, ndup = deduplicate_overlap(records, {frozenset({"A","B"})})
        self.assertEqual(ndup, 0); self.assertEqual(len(kept), 2)

    def test_full_grid_none_and_no_price_preserved(self):
        slots = [{"slot":i,"status":("VALID" if i in (1,5) else "NONE"),"return_bps":(3 if i==1 else -1 if i==5 else None)} for i in range(10)]
        sampled = assemble_blocks(slots, [0,4,6], 4)
        self.assertEqual(len(sampled), 10)
        self.assertEqual(sum(x["status"] == "NONE" for x in sampled), 8)
        self.assertEqual(sum(x["return_bps"] is None for x in sampled), 8)

    def test_bootstrap_blocks_never_wrap(self):
        slots = [{"slot":i} for i in range(10)]
        with self.assertRaises(ValueError): assemble_blocks(slots, [8], 4)

    def test_theta_uses_only_valid_non_none_returns(self):
        slots = [{"signal":"LONG","return_bps":20},{"signal":"LONG","return_bps":10},
                 {"signal":"SHORT","return_bps":-10},{"signal":"NONE","return_bps":999},
                 {"signal":"LONG","return_bps":None}]
        self.assertAlmostEqual(theta(slots), 12.5)

    def test_bootstrap_invalid_replicate_threshold(self):
        self.assertTrue(replicate_validity(100, 10000))
        self.assertFalse(replicate_validity(101, 10000))

    def test_quantile_linear_and_sample_se_inputs(self):
        self.assertAlmostEqual(linear_quantile([0.0, 10.0, 20.0, 30.0], 0.05), 1.5)

    def test_journal_checkpoint_and_tamper_or_truncation_detection(self):
        zero = "0" * 64
        e1 = journal_entry(1, zero, "GENESIS", {"spec":"r2"})
        e2 = journal_entry(2, e1["entry_hash"], "SLOT", {"slot":1,"status":"NONE"})
        anchor = checkpoint_head([e1,e2])
        e3 = journal_entry(3, e2["entry_hash"], "CHECKPOINT", anchor)
        self.assertEqual(anchor["head_seq"], 2)
        self.assertEqual(anchor["head_hash"], e2["entry_hash"])
        self.assertTrue(verify_anchored_chain([e1,e2,e3], anchor))
        tampered = [e1, {**e2, "payload":{"slot":1,"status":"VALID"}}, e3]
        self.assertFalse(verify_anchored_chain(tampered, anchor))
        self.assertFalse(verify_anchored_chain([e1], anchor))


if __name__ == "__main__":
    unittest.main(verbosity=2)
