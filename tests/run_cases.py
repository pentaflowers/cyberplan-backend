"""Run every test case in tests/cases.json against the rule engine.

Usage: python tests/run_cases.py   (exit code 0 = all cases pass)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import AnswerError, evaluate, load_rules  # noqa: E402

_MISSING = object()


def get(obj, dotted):
    for part in dotted.split("."):
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return _MISSING
    return obj


def run(cases_path=ROOT / "tests" / "cases.json") -> list[str]:
    data = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    rules = load_rules()
    failures = []
    for case in data["cases"]:
        answers = {**data["base"], **case["answers"]}
        answers = {k: v for k, v in answers.items() if v is not None}
        when = case.get("evaluation_date", data["evaluation_date"])
        try:
            res = evaluate(answers, rules, when)
        except AnswerError as e:
            if "expect_error" in case and case["expect_error"] in str(e):
                continue
            failures.append(f"{case['id']}: unexpected error {e}")
            continue
        if "expect_error" in case:
            failures.append(f"{case['id']}: expected error '{case['expect_error']}' but got a result")
            continue
        for path, want in case["expect"].items():
            got = get(res, path)
            if got != want:
                failures.append(f"{case['id']} {path}: expected {want!r}, got {got!r}")
    return failures


def test_all_cases():  # pytest entry point
    assert run() == []


if __name__ == "__main__":
    f = run()
    n = len(json.loads((ROOT / "tests" / "cases.json").read_text())["cases"])
    print(f"{n - len({x.split()[0].rstrip(':') for x in f})}/{n} cases pass")
    for line in f:
        print("  FAIL", line)
    sys.exit(1 if f else 0)
