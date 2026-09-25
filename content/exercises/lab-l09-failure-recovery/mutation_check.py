"""Re-run the fourteen deliberate mutations described in SOLUTIONS.md.

    python mutation_check.py

Each mutation replaces one rule in solutions/pipeline.py inside a temporary copy
of this package and runs run_tests.py there with the same interpreter; it is
caught when at least one test fails, and the failing test names are printed.
Nothing in this directory is modified and the temporary copy is deleted.
Standard library only. These runs check that the tests can fail; they are not
part of the recorded evidence.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LAB = Path(__file__).resolve().parent
MUTANTS = {
    "M1 repair re-runs succeeded tasks": ('if record["tasks"][task]["status"] == "succeeded":\n        return "reuse"',
                                          'if record["tasks"][task]["status"] == "succeeded":\n        return "run"'),
    "M2 dependents run after a failure": ('if all(record["tasks"][upstream]["status"] == "succeeded" for upstream in DEPENDS_ON[task]):',
                                          "if True:"),
    "M3 no freshness check": ('if landing.get("business_date") != business_date:', "if False:"),
    "M4 retention overwrites": ("if event_id not in area:", "if True:"),
    "M5 identity from rows only": ("sha256(canonical(content).encode('utf-8'))",
                                   "sha256(canonical(content['rows']).encode('utf-8'))"),
    "M6 key per try": ("return f\"notify:{report['report_id']}:{recipient}\"",
                       "return f\"notify:{report['report_id']}:{recipient}:{ctx['try']}\""),
    "M7 gate ignores conflicts": ('if result["conflicts"]:', "if False:"),
    "M8 invalid rows take part": ("        if reason:\n            excluded.append", "        if False:\n            excluded.append"),
    "M9 receiver never deduplicates": ("if self.honours_keys and key is not None and key in self._by_key:", "if False:"),
    "M10 no transient retry": ("if error.transient and tries <= self.retries[task]:", "if False:"),
    "M11 alerts not deduplicated": ('if all(alert["key"] != key for alert in self.store.alerts):', "if True:"),
    "M12 diagnosis trusts an unanswerable receiver": ("if not receiver_can_answer:", "if False:"),
    "M13 superseded conflicts still block": ("        latest = winning[key]\n        payloads = {canonical({m: r[m] for m in contract[\"measures\"]}) for r in versions[latest].values()}",
                                             "        latest = min(versions)\n        payloads = {canonical({m: r[m] for m in contract[\"measures\"]}) for r in versions[latest].values()}\n        latest = winning[key]"),
    "M14 superseded event conflicts still block": ('if validate(contract, row) or row["version"] == winning.get(key_of(contract, row)):',
                                                   "if True:"),
}


def main() -> int:
    missed = []
    for name, (old, new) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "lab"
            shutil.copytree(LAB, work, ignore=shutil.ignore_patterns("__pycache__"))
            target = work / "solutions" / "pipeline.py"
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: the original rule is not in solutions/pipeline.py exactly once")
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            done = subprocess.run([sys.executable, "-B", "run_tests.py"], cwd=work, capture_output=True, text=True)
            failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+)", done.stderr, re.M)))
            print(f"{name}: exit {done.returncode}; {len(failed)} failing: {', '.join(failed)}")
            if done.returncode == 0:
                missed.append(name)
    if missed:
        print("NOT caught: " + ", ".join(missed))
        return 1
    print(f"all {len(MUTANTS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
