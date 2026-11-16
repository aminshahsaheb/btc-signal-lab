"""Run a verifier module of journal contract v3 on every input of this package and record the outputs (stage 1 of the handoff).

usage:  python3 -I -B run_inputs.py --module PATH/TO/verifier.py --inputs . --out OUTDIR

--inputs is the root of this package (the directory that holds `inputs/` and `boundary/`). The module must define
    verify(path, anchor, journal_id, verify_time_ms) -> dict       (contract 8.2; see INTERFACE.md)
    class UnsupportedJournal(Exception)                            (the capability boundary, see INTERFACE.md)
For each input directory <id> this writes OUTDIR/outputs/<id>.json and finally OUTDIR/OUTPUT_RECORD.json (the sha256 of this harness, of every .py file in the
directory of the module, of every output file, and the digest of the outputs). The harness uses no clock and no network, and it does not look at any expected output.
It calls verify with exactly four positional arguments and with nothing else; a module that needs an option must default it.
An output file is one of:
    the report (a JSON object with the keys of 8.2),
    {"unsupported_journal": true}                 when verify raised an exception whose class is named UnsupportedJournal,
    {"error": "<ExceptionClass>: <message>"}      for any other exception, or for a return value that is not a JSON-serializable dict.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys


class Anchor:
    """The anchor object of contract 4.1, built from the `anchor` list of an input.json."""

    def __init__(self, entries):
        self.entries = {e["index"]: e for e in entries}

    def get(self, journal_id, index):
        """The entry (a dict) whose `index` equals `index`, else None. `journal_id` is ignored: one anchor serves one journal."""
        return self.entries.get(index)

    def latest(self, journal_id):
        """The largest `index` among the entries, 0 if there are none."""
        return max(self.entries) if self.entries else 0


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def digest_of(named):
    """sha256 of the lines `<sha256>  ./<name>\\n` over {name: sha256}, sorted by the BYTES of the name (= `find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`)."""
    lines = "".join("%s  ./%s\n" % (named[n], n) for n in sorted(named, key=lambda x: x.encode("utf-8")))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def load_module(path):
    path = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(path))          # siblings of the module (isolated mode does not add them)
    spec = importlib.util.spec_from_file_location("verifier_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def input_dirs(root):
    found = []
    for group in ("inputs", "boundary"):
        base = os.path.join(root, group)
        if os.path.isdir(base):
            for name in sorted(os.listdir(base), key=lambda x: x.encode("utf-8")):
                if os.path.isfile(os.path.join(base, name, "journal.jsonl")):
                    found.append((name, os.path.join(base, name)))
    return found


def run_one(mod, directory):
    with open(os.path.join(directory, "input.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    try:
        report = mod.verify(os.path.join(directory, "journal.jsonl"), Anchor(spec["anchor"]), spec["journal_id"], spec["verify_time_ms"])
        if not isinstance(report, dict):
            return {"error": "TypeError: verify returned %s, not a dict" % type(report).__name__}
        return json.loads(json.dumps(report, sort_keys=True))
    except Exception as exc:                                       # noqa: BLE001 - every failure is recorded, none is hidden
        if type(exc).__name__ == "UnsupportedJournal":
            return {"unsupported_journal": True}
        return {"error": "%s: %s" % (type(exc).__name__, exc)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--module", required=True)
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    mod = load_module(args.module)
    dirs = input_dirs(args.inputs)
    if not dirs:
        print("NO INPUTS FOUND under %s" % args.inputs)
        return 1
    outdir = os.path.join(args.out, "outputs")
    os.makedirs(outdir, exist_ok=True)
    out_hashes = {}
    for name, directory in dirs:
        result = run_one(mod, directory)
        path = os.path.join(outdir, name + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(result, sort_keys=True, indent=1) + "\n")
        out_hashes[name + ".json"] = sha256_file(path)
        kind = "report" if "verdict" in result else ("unsupported_journal" if "unsupported_journal" in result else ("ERROR" if "error" in result else "other"))
        print("%-6s %s" % (name, kind))
    mdir = os.path.dirname(os.path.abspath(args.module))
    record = {
        "harness_sha256": sha256_file(os.path.abspath(__file__)),
        "module": os.path.basename(args.module),
        "code_files_sha256": {n: sha256_file(os.path.join(mdir, n)) for n in sorted(os.listdir(mdir)) if n.endswith(".py")},
        "python": sys.version.split()[0],
        "inputs": len(dirs),
        "outputs_sha256": out_hashes,
        "outputs_digest": digest_of(out_hashes),
    }
    with open(os.path.join(args.out, "OUTPUT_RECORD.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, sort_keys=True, indent=1) + "\n")
    print("inputs: %d" % len(dirs))
    print("outputs digest: %s" % record["outputs_digest"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
