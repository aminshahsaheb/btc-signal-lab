#!/usr/bin/env python3
"""Structural checks of the r6 contract TEXT (a text guard, not a verifier; it does not check any rule of the contract).

  python3 -I -B tools/check_contract_text.py            # run from research/d-liq/r6-draft
  python3 -I -B tools/check_contract_text.py --selftest # also prove that each check fails on a known-bad text

Checks:
  T1  contract/R5_TO_R6.diff equals the unified diff of the r5 text (../r5-draft/indep_verifier/JOURNAL_CONTRACT_v2.md) against contract/JOURNAL_CONTRACT_v3.md,
      so a reviewer can read exactly what r6 changed and cannot be shown a stale diff.
  T2  every finding name listed in section 8.1 is used in at least one rule outside 8.1, and every upper-case finding-like name used anywhere
      (prefixes CONN_, MSG_, FORCE_, CANDLE_, SLOT_, OUTCOME_, CHECKPOINT_, ANCHOR_, REPLAY_, DUPLICATE_, TAIL_, NO_CHECKPOINT) is listed in 8.1.
  T3  every section reference such as 6.8, 7.7b or 2.3c names an item that exists in the text (a numbered paragraph and, for a letter, a lettered sub-item of it).
  T4  the genesis string is the v3 string and the v2 string appears only as the documented r5 value.
A pass confirms the structure of the text only. It says nothing about whether the rules are right, implemented or tested.
"""
import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
R5 = HERE.parent / "r5-draft" / "indep_verifier" / "JOURNAL_CONTRACT_v2.md"
R6 = HERE / "contract" / "JOURNAL_CONTRACT_v3.md"
DIFF = HERE / "contract" / "R5_TO_R6.diff"
PREFIXES = ("CONN_", "MSG_", "FORCE_", "CANDLE_", "SLOT_", "OUTCOME_", "CHECKPOINT_", "ANCHOR_", "REPLAY_", "DUPLICATE_", "TAIL_", "NO_CHECKPOINT")
NAME = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")


def make_diff(r5_text: str, r6_text: str) -> str:
    return "".join(difflib.unified_diff(r5_text.splitlines(True), r6_text.splitlines(True),
                                        "r5-draft/indep_verifier/JOURNAL_CONTRACT_v2.md", "r6-draft/contract/JOURNAL_CONTRACT_v3.md", n=2))


def section_81(text: str) -> str:
    m = re.search(r"^8\.1 .*?(?=^8\.2 )", text, re.S | re.M)
    return m.group(0) if m else ""


def check_names(text: str) -> list:
    errors = []
    block = section_81(text)
    if not block:
        return ["T2: section 8.1 not found"]
    listed = {n for n in NAME.findall(block) if n.startswith(PREFIXES)}
    rest = text.replace(block, "")
    for n in sorted(listed):
        if n not in rest:
            errors.append(f"T2: {n} is listed in 8.1 but no rule outside 8.1 uses it")
    used = {n for n in NAME.findall(rest) if n.startswith(PREFIXES)}
    for n in sorted(used - listed):
        errors.append(f"T2: {n} is used in a rule but is not listed in 8.1")
    return errors


def defined_items(text: str):
    items = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^(\d{1,2}\.\d{1,2}) ", line)
        if m:
            cur = m.group(1)
            items.setdefault(cur, set())
            continue
        if re.match(r"^## ", line):
            cur = None
            continue
        m = re.match(r"^ {2,3}([a-z])\. ", line)
        if m and cur:
            items[cur].add(m.group(1))
    return items


def check_refs(text: str) -> list:
    errors = []
    items = defined_items(text)
    stripped = re.sub(r"`[^`\n]*`", "``", text)
    for m in re.finditer(r"(?<![\d.\w])(\d{1,2}\.\d{1,2})([a-z]?)(?![\d\w])", stripped):
        num, letter = m.group(1), m.group(2)
        if num not in items:
            errors.append(f"T3: reference to {num}{letter} but no paragraph {num} exists")
        elif letter and letter not in items[num]:
            errors.append(f"T3: reference to {num}{letter} but paragraph {num} has no sub-item {letter}")
    return errors


def check_genesis(text: str) -> list:
    errors = []
    if 'GENESIS = b"DLIQ-JOURNAL-v3-GENESIS"' not in text:
        errors.append("T4: the v3 genesis string is not defined in 3.2")
    for m in re.finditer(r"DLIQ-JOURNAL-v2-GENESIS", text):
        ctx = text[max(0, m.start() - 12):m.start()]
        if "r5: `" not in ctx:
            errors.append("T4: the v2 genesis string appears other than as the documented r5 value")
    return errors


def run(r5_text: str, r6_text: str, diff_text: str) -> list:
    errors = []
    if make_diff(r5_text, r6_text) != diff_text:
        errors.append("T1: contract/R5_TO_R6.diff is not the current diff of r5 against r6")
    return errors + check_names(r6_text) + check_refs(r6_text) + check_genesis(r6_text)


def main(argv) -> int:
    r5, r6, diff = (p.read_text(encoding="utf-8") for p in (R5, R6, DIFF))
    errors = run(r5, r6, diff)
    for e in errors:
        print("FAIL", e)
    if "--selftest" in argv:
        bad = {
            "T1 stale diff": (r5, r6, diff + " "),
            "T2 unused listed name": (r5, r6.replace("FORCE_UNKNOWN_KEY (r6; 7.7c)", "FORCE_UNKNOWN_KEY (r6; 7.7c), XX_NEVER_USED".replace("XX_", "CANDLE_")), diff),
            "T2 unlisted used name": (r5, r6.replace("one soft finding", "one soft finding CANDLE_INVENTED_NAME", 1), diff),
            "T3 dangling section": (r5, r6.replace("(7.7b)", "(7.9b)", 1), diff),
            "T3 dangling sub-item": (r5, r6.replace("(7.7b)", "(7.7q)", 1), diff),
            "T4 wrong genesis": (r5, r6.replace('b"DLIQ-JOURNAL-v3-GENESIS"', 'b"DLIQ-JOURNAL-v2-GENESIS"', 1), diff),
        }
        for label, (a, b, d) in bad.items():
            if b == r6 and d == diff:
                print("FAIL selftest input unchanged:", label)
                errors.append(label)
                continue
            got = run(a, b, d)
            if not got:
                print("FAIL selftest: the check did not catch:", label)
                errors.append(label)
            else:
                print("ok   selftest caught:", label)
    if errors:
        return 1
    print("CONTRACT TEXT CHECKS PASSED (structure only; not a verification of any rule)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
