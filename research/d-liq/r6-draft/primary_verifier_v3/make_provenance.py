"""Regenerates the two provenance diffs of the primary verifier: the r5 files it was DERIVED from against the files of this package.

usage:  python3 -I -B make_provenance.py            writes PROVENANCE_verify.diff and PROVENANCE_msg_contract.diff next to this file
        python3 -I -B make_provenance.py --check    exits 1 if a committed diff is not what the current files produce
The diffs are the answer to GPT's condition (2026-11-12, Q4) that the code derived from r5 is documented and the r6-specific logic isolated: every line of
the primary verifier that is not r5 code is visible in them, and the new module r6_rules.py (no r5 counterpart) holds all r6-specific rules.
"""
import difflib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R5 = HERE.parent.parent / "r5-draft" / "src"
PAIRS = (
    ("PROVENANCE_verify.diff", "dliq_journal_verify_v2.py", "dliq_journal_verify_v3.py"),
    ("PROVENANCE_msg_contract.diff", "dliq_msg_contract_v1.py", "dliq_msg_contract_v3.py"),
)


def render(old_name, new_name):
    old = (R5 / old_name).read_text(encoding="utf-8").splitlines(keepends=True)
    new = (HERE / new_name).read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(old, new, fromfile="r5-draft/src/" + old_name, tofile="r6-draft/primary_verifier_v3/" + new_name, n=2))


def main(argv):
    check = "--check" in argv
    bad = 0
    for out_name, old_name, new_name in PAIRS:
        text = render(old_name, new_name)
        target = HERE / out_name
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                print("STALE: %s" % out_name)
                bad += 1
        else:
            target.write_text(text, encoding="utf-8")
            print("wrote %s (%d lines)" % (out_name, text.count("\n")))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
