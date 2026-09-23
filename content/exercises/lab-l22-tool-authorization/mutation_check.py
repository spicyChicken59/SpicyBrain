"""Re-run the nine deliberate mutations described in SOLUTIONS.md.

    python mutation_check.py

Each mutation replaces one rule in solutions/gate.py inside a temporary copy
of this package and runs run_tests.py there with the same interpreter; it is
caught when at least one test fails, and the failing test names are printed.
Nothing in this directory is modified and the temporary copy is deleted.
Standard library only.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LAB = Path(__file__).resolve().parent
MUTANTS = {
    "M1 extra properties accepted": ('if schema.get("additionalProperties", True) is False:', "if False:"),
    "M2 delegation as a union": ('if tool["permission"] not in self.application["delegated_scopes"]:', "if False:"),
    "M3 replay ignores the arguments": ('if stored["digest"] != args_digest:', "if False:"),
    "M4 approval never required": ('if policy == "always":\n            return True',
                                   'if policy == "always":\n            return False'),
    "M5 self-approval allowed": ('if approver == record["requester"]:', "if False:"),
    "M6 two extra attempts": ("for attempt in range(1, allowed + 1):", "for attempt in range(1, allowed + 3):"),
    "M7 missing user becomes a supervisor": ('if not session or not session.get("valid"):\n            return None',
                                             'if not session or not session.get("valid"):\n            return "sup-n1"'),
    "M8 audit keeps only successes": ("self._audit.append(dict(row))",
                                      'self._audit.append(dict(row)) if decision in ("allowed", "replayed") else None'),
    "M9 target ignores the key": ("if key is not None and slot in self.by_key:", "if False:"),
}


def main() -> int:
    missed = []
    for name, (old, new) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "lab"
            shutil.copytree(LAB, work, ignore=shutil.ignore_patterns("__pycache__"))
            target = work / "solutions" / "gate.py"
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: the original rule is not in solutions/gate.py exactly once")
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
