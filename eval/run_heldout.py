"""
Runner for Held-Out Evaluation Set.
Executes all 15 in-scope and 15 out-of-scope questions strictly as-is
without modifying any retrieval or gating thresholds.
"""

import asyncio
import sys
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.generation.service import AskService
from app.models.schemas import AnswerStatus


async def evaluate():
    yaml_path = Path(__file__).resolve().parent / "heldout.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    in_scope = data.get("in_scope", [])
    out_of_scope = data.get("out_of_scope", [])

    service = AskService()

    print("=" * 80)
    print("HELD-OUT EVALUATION REPORT (15 In-Scope + 15 Out-of-Scope)")
    print("=" * 80)

    # 1. Evaluate In-Scope
    print("\n--- [PART 1: IN-SCOPE QUESTIONS (Target: ANSWERED)] ---")
    in_results = []
    for item in in_scope:
        qid = item["id"]
        q = item["question"]
        resp = await service.answer_question(q)
        actual = resp.status.value
        passed = (resp.status == AnswerStatus.ANSWERED)
        source = resp.details[0].source_id if resp.details else "NONE"
        section = resp.details[0].section if resp.details else "NONE"
        in_results.append((qid, q, passed, actual, source, section))
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {qid}: '{q[:50]}...' -> status={actual}, source={source}, section={section}")

    # 2. Evaluate Out-of-Scope
    print("\n--- [PART 2: OUT-OF-SCOPE / UNCOVERED (Target: REFUSED)] ---")
    out_results = []
    for item in out_of_scope:
        qid = item["id"]
        q = item["question"]
        resp = await service.answer_question(q)
        actual = resp.status.value
        # Refused if insufficient_evidence or out_of_scope (must NOT be answered)
        passed = (resp.status in (AnswerStatus.INSUFFICIENT_EVIDENCE, AnswerStatus.OUT_OF_SCOPE))
        out_results.append((qid, q, passed, actual))
        status_str = "PASS" if passed else "FAIL (LEAKED)"
        print(f"[{status_str}] {qid}: '{q[:50]}...' -> status={actual}")

    in_passed = sum(1 for r in in_results if r[2])
    out_passed = sum(1 for r in out_results if r[2])

    print("\n" + "=" * 80)
    print(f"SUMMARY: In-Scope Accuracy:     {in_passed}/{len(in_scope)} ({(in_passed/len(in_scope))*100:.1f}%)")
    print(f"         Out-of-Scope Rejection: {out_passed}/{len(out_of_scope)} ({(out_passed/len(out_of_scope))*100:.1f}%)")
    print(f"         Total Score:            {in_passed + out_passed}/{len(in_scope) + len(out_of_scope)} ({((in_passed + out_passed)/(len(in_scope) + len(out_of_scope)))*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(evaluate())
