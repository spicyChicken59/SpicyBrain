"""Re-run the fourteen deliberate mutations described in the lab walkthrough.

    python mutation_check.py

Each mutation replaces one line of solutions/parser.py in a temporary copy of
this package and runs run_tests.py there with the same interpreter; it is
caught when at least one test fails, and the failing test names are printed.
Nothing in this directory is modified. Standard library only.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LAB = Path(__file__).resolve().parent
MUTANTS = {
 "M1 int() without regex": ('if isinstance(value, str) and INTEGER_TEXT.match(value.strip()):\n        return int(value.strip())', 'if isinstance(value, str):\n        return int(value.strip())'),
 "M2 null reported as missing": ('return None, ("null_" + name', 'return None, ("missing_" + name'),
 "M3 cross-field always": ('if not reasons and typed["defective_units"]', 'if typed["defective_units"] is not None and typed["inspected_units"] is not None and typed["defective_units"]'),
 "M4 keep last duplicate": ('elif record is not group[0]:', 'elif record is not group[-1]:'),
 "M5 no assert": ('assert len(accepted) + len(rejected) == raw_count, "every record is accepted or rejected exactly once"', 'pass'),
 "M6 basicConfig at import": ('log = logging.getLogger("cinderline.parsing")', 'logging.basicConfig(level=logging.WARNING)\nlog = logging.getLogger("cinderline.parsing")'),
 "M7 zero rate 0.0": ('if inspected_units == 0:\n        return None', 'if inspected_units == 0:\n        return 0.0'),
 "M8 Decimal(float)": ('result = Decimal(str(value))', 'result = Decimal(value)'),
 "M9 date without regex": ('if not isinstance(value, str) or not ISO_DATE_TEXT.match(value.strip()):', 'if not isinstance(value, str):'),
 "M10 rejected loses raw": ('rejected.append({"source": source, "position": position, "raw": raw, "reasons": reasons})', 'rejected.append({"source": source, "position": position, "raw": {}, "reasons": reasons})'),
 "M11 info not warning": ('log.warning("rejected %s position %d: %s", source, position', 'log.info("rejected %s position %d: %s", source, position'),
 "M12 bool accepted": ('if type(value) is int:', 'if isinstance(value, int):'),
 "M14 broad except": ('    except ValueError:\n        return None, "malformed_" + name', '    except Exception:\n        return None, "malformed_" + name'),
 "M13 blank not missing": ('if name not in raw or is_blank(raw[name]):', 'if name not in raw:'),
}


def main() -> int:
    missed = []
    for name, (old, new) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "lab"
            shutil.copytree(LAB, work, ignore=shutil.ignore_patterns("__pycache__"))
            target = work / "solutions" / "parser.py"
            text = target.read_text()
            if old not in text:
                raise SystemExit(f"{name}: the original line is not in solutions/parser.py")
            target.write_text(text.replace(old, new, 1))
            done = subprocess.run([sys.executable, "run_tests.py"], cwd=work, capture_output=True, text=True)
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
