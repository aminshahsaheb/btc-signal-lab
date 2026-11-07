#!/usr/bin/env python3
"""Self-tests for the repository guards: they must FAIL on known-bad inputs, not only pass on the real tree.

Covers scripts/check_docs.py (R1-R5), scripts/check_mirrors.py and scripts/check_dliq_strict.sh.
Run: python3 -I scripts/test_guards.py      (stdlib only; no network; no git needed)
A pass proves the guards catch the listed defects. It does not validate research claims or trading performance.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_docs  # noqa: E402
import check_mirrors  # noqa: E402

STRICT = HERE / "check_dliq_strict.sh"

README = "## Repository layout\n\n```text\n└── docs/\n```\n"
INDEX = "| `README.md` | LIVING | x |\n| `A.md` | LIVING | x |\n"


class Tree:
    """A throw-away repository tree: write files, then run a guard on an explicit file list."""

    def __init__(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.files: list[str] = []

    def put(self, rel: str, text: str | bytes = "") -> "Tree":
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
        if rel not in self.files:
            self.files.append(rel)
        return self

    def docs(self, a_md: str, extra: dict[str, str] | None = None, index: str = INDEX, readme: str = README) -> list[str]:
        self.put("README.md", readme).put("docs/INDEX.md", index).put("A.md", a_md).put("docs/B.md", "b\n")
        for rel, text in (extra or {}).items():
            self.put(rel, text)
        errors, _ = check_docs.run(self.dir, self.files)
        return errors

    def close(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


class DocsGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.t = Tree()
        self.addCleanup(self.t.close)
        self.idx = INDEX + "| `docs/B.md` | LIVING | x |\n"

    def run_docs(self, a_md: str, **kw: object) -> list[str]:
        return self.t.docs(a_md, index=kw.pop("index", self.idx), **kw)  # type: ignore[arg-type]

    def broken(self, errors: list[str], needle: str) -> bool:
        return any(e.startswith("R1") and needle in e for e in errors)

    def test_baseline_passes(self) -> None:
        self.assertEqual(self.run_docs("see [b](docs/B.md) and [ext](https://x.y) and [top](#a) and [m](mailto:a@b.c)\n"), [])

    def test_inline_broken(self) -> None:
        self.assertTrue(self.broken(self.run_docs("[x](missing-inline.md)\n"), "missing-inline.md"))

    def test_image_broken(self) -> None:
        self.assertTrue(self.broken(self.run_docs("![alt](missing-img.png)\n"), "missing-img.png"))

    def test_reference_definition_broken(self) -> None:
        self.assertTrue(self.broken(self.run_docs("[x][r1]\n\n[r1]: missing-reference.md\n"), "missing-reference.md"))

    def test_reference_definition_good(self) -> None:
        self.assertEqual(self.run_docs("[x][r1] and [r1][] \n\n[r1]: docs/B.md\n"), [])

    def test_reference_undefined_label(self) -> None:
        self.assertTrue(self.broken(self.run_docs("[x][nope]\n"), "undefined link reference [nope]"))

    def test_reference_label_is_case_and_space_insensitive(self) -> None:
        self.assertEqual(self.run_docs("[x][My  Ref]\n\n[my ref]: docs/B.md\n"), [])

    def test_html_href_and_src_broken(self) -> None:
        for html in ('<a href="missing-html.md">x</a>', "<a href='missing-html.md'>x</a>", "<a href=missing-html.md>x</a>", '<img src="missing-html.md">'):
            with self.subTest(html=html):
                t = Tree()
                try:
                    self.assertTrue(self.broken(t.docs(html + "\n", index=self.idx), "missing-html.md"))
                finally:
                    t.close()

    def test_html_good_and_external(self) -> None:
        self.assertEqual(self.run_docs('<a href="docs/B.md">x</a> <a href="https://x.y">y</a>\n'), [])

    def test_angle_destination_with_space(self) -> None:
        self.assertTrue(self.broken(self.run_docs("[x](<missing angle.md>)\n"), "missing angle.md"))
        t = Tree()
        try:
            self.assertEqual(t.docs("[x](<docs/with space.md>)\n", extra={"docs/with space.md": "x\n"}, index=self.idx + "| `docs/with space.md` | LIVING | x |\n"), [])
        finally:
            t.close()

    def test_parentheses_in_destination(self) -> None:
        errors = self.run_docs("[x](missing(1).md)\n")
        self.assertTrue(self.broken(errors, "missing(1).md"), errors)
        t = Tree()
        try:
            self.assertEqual(t.docs("[x](docs/a(1).md)\n", extra={"docs/a(1).md": "x\n"}, index=self.idx + "| `docs/a(1).md` | LIVING | x |\n"), [])
        finally:
            t.close()

    def test_title_after_destination(self) -> None:
        self.assertTrue(self.broken(self.run_docs('[x](missing-t.md "a title")\n'), "missing-t.md"))
        self.assertEqual(self.run_docs('[x](docs/B.md "a title") [y](docs/B.md \'t\')\n'), [])

    def test_percent_encoding_and_fragment_and_query(self) -> None:
        t = Tree()
        try:
            self.assertEqual(t.docs("[x](docs/a%20b.md#sec) [y](docs/a%20b.md?raw=1)\n", extra={"docs/a b.md": "x\n"}, index=self.idx + "| `docs/a b.md` | LIVING | x |\n"), [])
        finally:
            t.close()

    def test_root_relative_and_directory_links(self) -> None:
        self.assertEqual(self.run_docs("[x](/docs/B.md) [d](docs/) [r](.)\n"), [])
        self.assertTrue(self.broken(self.run_docs("[x](/docs/nope.md)\n"), "/docs/nope.md"))

    def test_link_escaping_the_repository(self) -> None:
        errors = self.run_docs("[x](../../etc/passwd)\n")
        self.assertTrue(any("escapes the repository" in e for e in errors), errors)

    def test_code_is_ignored(self) -> None:
        text = "```\n[x](missing-fence.md)\n```\n~~~\n[x](missing-tilde.md)\n~~~\n`[x](missing-span.md)`\n"
        self.assertEqual(self.run_docs(text), [])

    def test_unclosed_fence_is_a_failure(self) -> None:
        errors = self.run_docs("```\n[x](missing.md)\n")
        self.assertTrue(any("unclosed code fence" in e for e in errors), errors)

    def test_shortcut_reference_is_not_checked(self) -> None:
        # documented limitation: "[label]" alone is not treated as a link
        self.assertEqual(self.run_docs("- [x] done and [P] parameter\n"), [])

    def test_index_rules(self) -> None:
        t = Tree()
        try:
            errors = t.docs("a\n", index=INDEX)  # docs/B.md is not listed
            self.assertTrue(any(e.startswith("R2 not listed") and "docs/B.md" in e for e in errors), errors)
        finally:
            t.close()
        errors = self.run_docs("a\n", index=self.idx + "| `docs/ghost.md` | LIVING | x |\n")
        self.assertTrue(any(e.startswith("R2") and "ghost.md" in e for e in errors), errors)
        errors = self.run_docs("a\n", index=self.idx + "| `docs/B.md` | LIVING | dup |\n")
        self.assertTrue(any("duplicate row" in e for e in errors), errors)
        errors = self.run_docs("a\n", index=INDEX + "| `docs/B.md` | WEIRD | x |\n")
        self.assertTrue(any("unknown class" in e for e in errors), errors)

    def test_historical_banner(self) -> None:
        idx = INDEX + "| `docs/B.md` | HISTORICAL | x |\n"
        t = Tree()
        try:
            errors = t.docs("a\n", index=idx)
            self.assertTrue(any(e.startswith("R3") for e in errors), errors)
        finally:
            t.close()
        t = Tree()
        try:
            t.put("README.md", README).put("docs/INDEX.md", idx).put("A.md", "a\n").put("docs/B.md", "> HISTORICAL record\nb\n")
            self.assertEqual(check_docs.run(t.dir, t.files)[0], [])
        finally:
            t.close()

    def test_living_document_must_not_claim_private(self) -> None:
        for claim in ("Visibility: Private", "Keep the repository private", "The repository is private", "Do not make the repository public"):
            with self.subTest(claim=claim):
                errors = self.run_docs(claim + "\n")
                self.assertTrue(any(e.startswith("R4") for e in errors), errors)

    def test_readme_layout(self) -> None:
        errors = self.run_docs("a\n", extra={"scripts/x.py": "x\n"})
        self.assertTrue(any(e.startswith("R5") and "scripts/" in e for e in errors), errors)
        t = Tree()
        try:
            errors = t.docs("a\n", index=self.idx, readme="## Repository layout\n\n```text\n├── docs/\n└── ghost/\n```\n")
            self.assertTrue(any(e.startswith("R5") and "ghost/" in e for e in errors), errors)
        finally:
            t.close()


class MirrorGuard(unittest.TestCase):
    PAIRS = [("specs/a.md", "research/forward-journal/a.md")]

    def setUp(self) -> None:
        self.t = Tree()
        self.addCleanup(self.t.close)
        self.t.put("specs/a.md", "same\n").put("research/forward-journal/a.md", "same\n")

    def run_guard(self) -> list[str]:
        return check_mirrors.run(self.t.dir, self.t.files, self.PAIRS)[0]

    def test_baseline_and_trailing_newline(self) -> None:
        self.assertEqual(self.run_guard(), [])
        self.t.put("research/forward-journal/a.md", "same")
        self.assertEqual(self.run_guard(), [])

    def test_drift_and_missing(self) -> None:
        self.t.put("research/forward-journal/a.md", "different\n")
        self.assertTrue(any("mirror drift" in e for e in self.run_guard()))
        (self.t.dir / "specs/a.md").unlink()
        self.assertTrue(any("missing canonical" in e for e in self.run_guard()))

    def test_unregistered_files_in_mirror_trees(self) -> None:
        for path in ("research/forward-journal/new.md", "pine/new.pine", "research/d-liq/notes.md"):
            with self.subTest(path=path):
                self.t.put(path, "x\n")
                self.assertTrue(any(path in e for e in self.run_guard()))
                self.t.files.remove(path)

    def test_files_starting_with_r_are_not_exempt(self) -> None:
        # GPT audit E2: the old prefix "research/d-liq/r" exempted anything that begins with the letter r.
        for path in ("research/d-liq/rogue-file.md", "research/d-liq/r4x/a.md", "research/d-liq/r-draft/a.md", "research/d-liq/r4-draft", "research/d-liq/rogue/r4-draft/a.md", "research/d-liq/r4-draft-evil/a.md"):
            with self.subTest(path=path):
                self.t.put(path, "x\n")
                self.assertTrue(any(path in e for e in self.run_guard()), path)
                self.t.files.remove(path)

    def test_work_packages_are_exempt(self) -> None:
        for path in ("research/d-liq/r4-draft/src/x.py", "research/d-liq/r5-draft/README.md", "research/d-liq/r12-draft/a/b/c.md"):
            with self.subTest(path=path):
                self.t.put(path, "x\n")
                self.assertEqual(self.run_guard(), [])
                self.t.files.remove(path)


@unittest.skipIf(shutil.which("bash") is None, "bash not available")
class StrictRunner(unittest.TestCase):
    """check_dliq_strict.sh must fail when the old wiring would have passed (GPT audit E3)."""

    MUT_OK = "for i in range({n}):\n    print('KILLED  mutant', i)\n"
    DIFF_OK = "print('journals compared: {n}, disagreements: {d}')\n"

    def make(self, mut_v: str | None = None, mut_b: str | None = None, diff: str | None = None) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "patches").mkdir()
        (d / "builder").mkdir()
        (d / "src").mkdir()
        (d / "indep_verifier").mkdir()
        (d / "patches/mutation_check_verifiers.py").write_text(mut_v if mut_v is not None else self.MUT_OK.format(n=9))
        (d / "patches/mutation_check_builder.py").write_text(mut_b if mut_b is not None else self.MUT_OK.format(n=6))
        (d / "src/diff_test_verifiers.py").write_text(diff if diff is not None else self.DIFF_OK.format(n=1105, d=0))
        return d

    def go(self, pkg: Path, expect: str = "15", n: str = "1000", seeds: tuple[str, ...] = ("11",)) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(STRICT), str(pkg), expect, n, *seeds], capture_output=True, text=True)

    def test_all_good_passes(self) -> None:
        r = self.go(self.make())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_crashing_mutation_script_fails(self) -> None:
        # exits non-zero and prints no SURVIVED: the old `;`-joined subshell reported success
        r = self.go(self.make(mut_v="import sys\nfor i in range(9):\n    print('KILLED m')\nsys.exit(3)\n"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_missing_mutation_script_fails(self) -> None:
        d = self.make()
        (d / "patches/mutation_check_builder.py").unlink()
        self.assertNotEqual(self.go(d).returncode, 0)

    def test_survivor_fails(self) -> None:
        r = self.go(self.make(mut_b="for i in range(5):\n    print('KILLED m')\nprint('SURVIVED m6')\n"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_wrong_killed_count_fails(self) -> None:
        self.assertNotEqual(self.go(self.make(), expect="16").returncode, 0)
        self.assertNotEqual(self.go(self.make(), expect="14").returncode, 0)

    def test_differential_exit_status_fails(self) -> None:
        r = self.go(self.make(diff=self.DIFF_OK.format(n=1105, d=0) + "import sys\nsys.exit(1)\n"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_differential_disagreement_fails(self) -> None:
        self.assertNotEqual(self.go(self.make(diff=self.DIFF_OK.format(n=1105, d=2))).returncode, 0)

    def test_differential_missing_or_short_corpus_fails(self) -> None:
        self.assertNotEqual(self.go(self.make(diff="print('nothing')\n")).returncode, 0)
        self.assertNotEqual(self.go(self.make(diff=self.DIFF_OK.format(n=10, d=0)), n="1000").returncode, 0)

    def test_differential_crash_before_summary_fails(self) -> None:
        self.assertNotEqual(self.go(self.make(diff="raise SystemExit('boom')\n")).returncode, 0)

    def test_every_seed_is_checked(self) -> None:
        r = self.go(self.make(diff="import sys\nseed = sys.argv[-1]\nprint('journals compared: 2000, disagreements: %d' % (1 if seed == '13' else 0))\n"), n="1000", seeds=("11", "12", "13", "14"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_original_package_is_never_mutated(self) -> None:
        marker = "import sys, pathlib\npathlib.Path(sys.argv[1], 'MUTATED').write_text('x')\nprint('KILLED a')\n"
        d = self.make(mut_v=marker + "print('KILLED b')\n" * 8)
        self.go(d)
        self.assertFalse((d / "MUTATED").exists())

    def test_bad_arguments(self) -> None:
        d = self.make()
        self.assertEqual(self.go(d, expect="x").returncode, 2)
        self.assertNotEqual(subprocess.run(["bash", str(STRICT), str(d)], capture_output=True, text=True).returncode, 0)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    unittest.main(verbosity=1)
