"""Build the two packages of the independent-verifier handoff (GPT, 2026-11-15, decisions C and D) from the pinned sources.

usage:  python3 -I -B make_handoff.py --vectors DIR --contract FILE --out OUTDIR [--spec-dir DIR] [--zip] [--no-check-pins]

--vectors   the directory `vectors` of PR #40 at the pinned commit (46 vector directories and EXPECT_DERIVED.json)
--contract  the file JOURNAL_CONTRACT_v3.md of PR #39 at the pinned commit
--spec-dir  the directory that holds the three specification documents of the r3 package that the contract points to (07_MESSAGE_CONTRACT_v1.md, protocol_r3_section4_fa.md, protocol_r3_appendixB_params.md);
            each is checked against its pinned SHA-256 and copied verbatim into `spec/`. They are NOT in this repository (decision D-SPEC-1 of the owner is open), so without --spec-dir the build is PARTIAL: it holds
            `spec/PARTIAL_BUILD_DO_NOT_HAND_OVER.txt` instead, has its own pinned digest, and is not the package to hand to an author. Only the build with --spec-dir is.
--out       an empty or new directory; it receives
              dliq_r6_handoff_inputs/    the BLIND package for the author: contract, interface, harness, journals, input.json (anchor, journal_id, verify_time_ms), the capability-boundary input B01
              dliq_r6_handoff_expected/  the SEALED package: expected outputs (the twelve report keys of 8.2) and their provenance
            and, with --zip, the same two directories as deterministic .zip files (stored, sorted, fixed timestamps).
Removed from what the author sees: the fields r6_only, r5_only_extra, cases, contract_refs, title and description of every expect.json, and the descriptive part of every vector directory name (only
the short id, V01 ... V28c, remains). Nothing of the oracle, the vector generator, QUESTIONS.md, the PROVENANCE files or any verifier source is copied.
The two packages get SEPARATE digests: sha256 of the lines `<sha256>  ./<path>` of all files, sorted by byte order of the path (= `cd <package> && find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`).
Unless --no-check-pins is given, the sources and the resulting digests must equal HANDOFF_PINS.json. The build is deterministic: the same sources give the same bytes.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = "dliq_r6_handoff_inputs"
EXPECTED = "dliq_r6_handoff_expected"
KEYS = ("verdict", "findings", "hard", "soft", "n_events", "head_hex", "slots", "missing", "outcomes", "candles", "replayed", "analysis_eligible")
FROM_EXPECT = ("verdict", "findings", "hard", "soft", "slots", "missing", "candles", "replayed", "analysis_eligible")
DERIVED_KEYS = ("n_events", "head_hex", "outcomes")
INPUT_KEYS = ("journal_id", "verify_time_ms", "anchor")
REMOVED = ("r6_only", "r5_only_extra", "cases", "contract_refs", "title", "description")
BOUNDARY_ID = "B01"
BOUNDARY_T = 1785600000000


def jdump(obj):
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode("ascii")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def tree_digest(root):
    """(digest, file count) of a directory by the definition in the module docstring."""
    names = []
    for base, _dirs, files in os.walk(root):
        for f in files:
            names.append("./" + os.path.relpath(os.path.join(base, f), root).replace(os.sep, "/"))
    lines = []
    for n in sorted(names, key=lambda x: x.encode("utf-8")):
        with open(os.path.join(root, n[2:]), "rb") as fh:
            lines.append("%s  %s\n" % (sha256_bytes(fh.read()), n))
    return sha256_bytes("".join(lines).encode("utf-8")), len(names)


def vector_set_digest(vdir):
    """The digest of the vector set as PR #40 defines it: lines `<sha256>  vectors/<path>`."""
    names = []
    for base, _dirs, files in os.walk(vdir):
        for f in files:
            names.append("vectors/" + os.path.relpath(os.path.join(base, f), vdir).replace(os.sep, "/"))
    lines = []
    for n in sorted(names, key=lambda x: x.encode("utf-8")):
        with open(os.path.join(vdir, n[len("vectors/"):]), "rb") as fh:
            lines.append("%s  %s\n" % (sha256_bytes(fh.read()), n))
    return sha256_bytes("".join(lines).encode("utf-8")), len(names)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def boundary_journal():
    """B01: one CANDLE event that is valid per 2.1 (every listed field, msg_seq included). It tests only the capability boundary."""
    ev = {"t": "CANDLE", "seq": 1, "rec_ms": BOUNDARY_T, "open_time_ms": BOUNDARY_T, "open": "60000", "recv_ms": BOUNDARY_T, "raw_b64": "e30=", "sha256": sha256_bytes(b"{}"), "msg_seq": 1}
    return (json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def short_id(dirname):
    m = re.match(r"^(V[0-9]+[a-z]?)(_|$)", dirname)
    if not m:
        raise ValueError("not a vector directory name: %r" % dirname)
    return m.group(1)


def build(vectors, contract, out, pins=None, spec_dir=None):
    """Writes the two package directories under `out`. Returns {"inputs": (digest, files), "expected": (digest, files), "partial": bool}."""
    vectors, contract, out = Path(vectors), Path(contract), Path(out)
    if pins:
        got = vector_set_digest(vectors)
        want = (pins["vectors"]["digest"], pins["vectors"]["files"])
        if got != want:
            raise SystemExit("the vector set is not the pinned one: digest/files %s, expected %s" % (got, want))
        if sha256_bytes(contract.read_bytes()) != pins["contract"]["sha256"]:
            raise SystemExit("the contract file is not the pinned one")
    derived = json.loads((vectors / "EXPECT_DERIVED.json").read_text(encoding="utf-8"))["vectors"]
    names = sorted(d for d in os.listdir(vectors) if (vectors / d).is_dir())
    ids = [short_id(n) for n in names]
    if len(set(ids)) != len(ids) or set(derived) != set(ids):
        raise SystemExit("vector ids and EXPECT_DERIVED.json do not match")
    if pins and len(names) != pins["vectors"]["count"]:
        raise SystemExit("the number of vectors is not the pinned one")
    if out.exists() and any(out.iterdir()):
        raise SystemExit("--out must be empty or new")
    pin_info = pins or json.loads((HERE / "HANDOFF_PINS.json").read_text(encoding="utf-8"))
    inp, exp = out / INPUTS, out / EXPECTED
    for name in ("README_FOR_AUTHOR.md", "INTERFACE.md", "run_inputs.py"):
        write(inp / name, (HERE / "author_src" / name).read_bytes())
    write(inp / "contract" / "JOURNAL_CONTRACT_v3.md", contract.read_bytes())
    spec = pin_info["spec"]
    if spec_dir is not None:
        spec_dir = Path(spec_dir)
        lines = []
        for name in sorted(spec["files"]):
            if not (spec_dir / name).is_file():
                raise SystemExit("the specification document %s is missing in %s" % (name, spec_dir))
            data = (spec_dir / name).read_bytes()
            if sha256_bytes(data) != spec["files"][name]:
                raise SystemExit("the specification document %s is not the pinned one" % name)
            write(inp / "spec" / name, data)
            lines.append("%s  %s\n" % (spec["files"][name], name))
        write(inp / "spec" / "SPEC_PINS.txt", ("sha256 of each file in this directory, verbatim copies:\n%s\norigin: %s\n" % ("".join(lines), spec["origin"])).encode("ascii"))
    else:
        write(inp / "spec" / "PARTIAL_BUILD_DO_NOT_HAND_OVER.txt", b"This package was built WITHOUT the specification documents. It is not the package to hand to an author.\n")
    c = pin_info["contract"]
    write(inp / "CONTRACT_PIN.txt", ("contract: pull request #%d, commit %s\npath: %s\nsha256 of the file: %s\n" % (c["pr"], c["commit"], c["path"], c["sha256"])).encode("ascii"))
    write(exp / "README_SEALED.md", (HERE / "sealed_src" / "README_SEALED.md").read_bytes())
    v = pin_info["vectors"]
    write(exp / "SOURCE_PINS.txt", ("expected outputs of the vectors of pull request #%d, commit %s\nvector set: %d vectors, %d files, digest %s\nthe nine keys verdict, findings, hard, soft, slots, missing, candles, replayed, analysis_eligible: expect.json of each vector;\n"
                                    "the three keys n_events, head_hex, outcomes: vectors/EXPECT_DERIVED.json (oracle of the same author)\nboundary input %s: written by make_handoff.py, expectation {\"unsupported_journal\": true}\n"
                                    % (v["pr"], v["commit"], v["count"], v["files"], v["digest"], BOUNDARY_ID)).encode("ascii"))
    for name, vid in zip(names, ids):
        spec = json.loads((vectors / name / "expect.json").read_text(encoding="utf-8"))
        write(inp / "inputs" / vid / "journal.jsonl", (vectors / name / "journal.jsonl").read_bytes())
        write(inp / "inputs" / vid / "input.json", jdump({k: spec[k] for k in INPUT_KEYS}))
        expected = {k: spec[k] for k in FROM_EXPECT}
        if set(derived[vid]) != set(DERIVED_KEYS):
            raise SystemExit("EXPECT_DERIVED.json: %s has the keys %s" % (vid, sorted(derived[vid])))
        expected.update({k: derived[vid][k] for k in DERIVED_KEYS})
        assert tuple(sorted(expected)) == tuple(sorted(KEYS))
        write(exp / "expected" / (vid + ".json"), jdump(expected))
    write(inp / "boundary" / BOUNDARY_ID / "journal.jsonl", boundary_journal())
    write(inp / "boundary" / BOUNDARY_ID / "input.json", jdump({"journal_id": "boundary-" + BOUNDARY_ID, "verify_time_ms": BOUNDARY_T, "anchor": []}))
    write(exp / "expected" / (BOUNDARY_ID + ".json"), jdump({"unsupported_journal": True}))
    return {"inputs": tree_digest(inp), "expected": tree_digest(exp), "partial": spec_dir is None}


def write_zip(directory, zip_path):
    """A deterministic archive: stored (not compressed), sorted by byte order, fixed timestamps and permissions, the directory name as the top level."""
    directory = Path(directory)
    entries = []
    for base, _dirs, files in os.walk(directory):
        for f in files:
            entries.append(os.path.relpath(os.path.join(base, f), directory).replace(os.sep, "/"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
        for rel in sorted(entries, key=lambda x: x.encode("utf-8")):
            info = zipfile.ZipInfo(directory.name + "/" + rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (directory / rel).read_bytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec-dir")
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--no-check-pins", action="store_true")
    args = ap.parse_args(argv)
    pins = json.loads((HERE / "HANDOFF_PINS.json").read_text(encoding="utf-8"))
    result = build(args.vectors, args.contract, args.out, None if args.no_check_pins else pins, args.spec_dir)
    problems = 0
    if result["partial"]:
        print("PARTIAL PACKAGE (no --spec-dir): this is NOT the package to hand to an author")
    for key, pin_key, label in (("inputs", "input_package_partial" if result["partial"] else "input_package", "input package (blind%s)" % (", PARTIAL" if result["partial"] else "")),
                                ("expected", "expected_package", "expected package (sealed)")):
        digest, files = result[key]
        print("%s: %d files, digest %s" % (label, files, digest))
        want = pins[pin_key]
        if not args.no_check_pins and (digest, files) != (want["digest"], want["files"]):
            print("  PIN MISMATCH: HANDOFF_PINS.json says %d files, digest %s" % (want["files"], want["digest"]))
            problems += 1
    if args.zip:
        for name in (INPUTS, EXPECTED):
            zp = Path(args.out) / (name + ".zip")
            write_zip(Path(args.out) / name, zp)
            print("%s: sha256 %s" % (zp.name, sha256_bytes(zp.read_bytes())))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
