#!/usr/bin/env python3
"""Negative tests for the rebuild checks (assemble_r5.py, check_rebuild.py): they must FAIL when the base or the committed tree is tampered with.
usage: python3 -I -B test_rebuild_checks.py <r4-draft dir> <r5-draft dir>   (needs a git checkout: the real trees are copied into temp dirs)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
R4, R5 = os.path.abspath(sys.argv.pop(1)), os.path.abspath(sys.argv.pop(1))
PY = [sys.executable, "-I", "-B"]


def sh(args):
    return subprocess.run(PY + args, capture_output=True, text=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.r4 = os.path.join(self.tmp, "r4")
        shutil.copytree(R4, self.r4, ignore=shutil.ignore_patterns("__pycache__"))
        self.out = os.path.join(self.tmp, "out")

    def assemble(self, base=None):
        return sh([os.path.join(HERE, "assemble_r5.py"), base or self.r4, self.out])


class AssemblerRejectsATamperedBase(Base):
    def test_clean_base_assembles_and_matches_the_committed_tree(self):
        r = self.assemble()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        c = sh([os.path.join(HERE, "check_rebuild.py"), "check", self.out, R5])
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)

    def test_modified_file(self):
        with open(os.path.join(self.r4, "src", "dliq_journal_verify_v2.py"), "a") as f:
            f.write("\n# tampered\n")
        r = self.assemble()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hash mismatch", r.stdout + r.stderr)

    def test_extra_file(self):
        with open(os.path.join(self.r4, "src", "extra.py"), "w") as f:
            f.write("x = 1\n")
        r = self.assemble()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("extra", r.stdout + r.stderr)

    def test_missing_file(self):
        os.remove(os.path.join(self.r4, "src", "fixtures", "messages.jsonl"))
        self.assertNotEqual(self.assemble().returncode, 0)

    def test_symlink(self):
        os.symlink("dliq_journal_v2.py", os.path.join(self.r4, "src", "link.py"))
        r = self.assemble()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("symlink", r.stdout + r.stderr)

    def test_manifest_replaced(self):
        with open(os.path.join(self.r4, "MANIFEST.sha256"), "a") as f:
            f.write("\n")
        r = self.assemble()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pinned", r.stdout + r.stderr)

    def test_existing_output_directory_is_refused(self):
        os.makedirs(self.out)
        self.assertNotEqual(self.assemble().returncode, 0)


class CheckerRejectsATamperedCommittedTree(Base):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.assemble().returncode, 0)
        self.r5 = os.path.join(self.tmp, "r5")
        shutil.copytree(R5, self.r5, ignore=shutil.ignore_patterns("__pycache__"))

    def check(self):
        return sh([os.path.join(HERE, "check_rebuild.py"), "check", self.out, self.r5])

    def test_baseline(self):
        self.assertEqual(self.check().returncode, 0)

    def test_committed_output_file_modified_with_manifest_updated(self):
        with open(os.path.join(self.r5, "src", "dliq_journal_verify_v2.py"), "a") as f:
            f.write("\n# tampered after assembly\n")
        sh([os.path.join(HERE, "check_rebuild.py"), "write-tree", self.r5])         # the tree manifest is regenerated, so only the REBUILD comparison can catch it
        r = self.check()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("differs from the rebuilt one", r.stdout)

    def test_committed_file_modified_without_manifest_update(self):
        with open(os.path.join(self.r5, "README.md"), "a") as f:
            f.write("x\n")
        self.assertNotEqual(self.check().returncode, 0)

    def test_log_file_modified_without_manifest_update(self):
        with open(os.path.join(self.r5, "logs", "env.txt"), "a") as f:          # not a rebuilt output: only the tree manifest can catch this
            f.write("tampered\n")
        r = self.check()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("MANIFEST.sha256 hash mismatch", r.stdout)

    def test_extra_committed_file(self):
        with open(os.path.join(self.r5, "src", "extra.py"), "w") as f:
            f.write("x\n")
        sh([os.path.join(HERE, "check_rebuild.py"), "write-tree", self.r5])
        r = self.check()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("neither a rebuilt output", r.stdout)

    def test_missing_committed_output(self):
        os.remove(os.path.join(self.r5, "src", "dliq_msg_contract_v1.py"))
        sh([os.path.join(HERE, "check_rebuild.py"), "write-tree", self.r5])
        r = self.check()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing from the committed tree", r.stdout)

    def test_assembled_manifest_tampered(self):
        # the checker reads patches/ASSEMBLED_MANIFEST.sha256 next to itself: use a private copy of the patches directory
        patches = os.path.join(self.tmp, "patches_copy")
        shutil.copytree(HERE, patches, ignore=shutil.ignore_patterns("__pycache__"))
        path = os.path.join(patches, "ASSEMBLED_MANIFEST.sha256")
        with open(path) as f:
            lines = f.read().splitlines()
        lines[0] = "0" * 64 + lines[0][64:]
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        r = sh([os.path.join(patches, "check_rebuild.py"), "check", self.out, self.r5])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("differs from ASSEMBLED_MANIFEST", r.stdout)

    def test_symlink_in_committed_tree(self):
        os.symlink("README.md", os.path.join(self.r5, "link.md"))
        self.assertNotEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
