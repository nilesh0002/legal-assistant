"""
Evaluation Runner for NyayaSahayak.
Evaluates 40 fresh questions (25 in-scope, 15 out-of-scope/uncovered).
Measures accuracy, wrong sources, wrong refusals, per-status counts,
and outputs a persistent report to eval/reports/<date>.txt.
Strictly follows Rule 6: Never tunes thresholds on this evaluation set.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Dict, List
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.generation.service import AskService
from app.models.schemas import AnswerStatus


async def run_evaluation():
    eval_dir = Path(__file__).resolve().parent
    yaml_path = eval_dir / "heldout.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    in_scope: List[dict] = data.get("in_scope", [])
    out_of_scope: List[dict] = data.get("out_of_scope", [])
    total_questions = len(in_scope) + len(out_of_scope)

    service = AskService()

    status_counts: Dict[str, int] = {}
    wrong_sources: List[dict] = []
    wrong_refusals: List[dict] = []
    false_positives: List[dict] = []

    in_scope_passed = 0
    out_of_scope_passed = 0

    report_lines: List[str] = []
    header = (
        "=" * 80 + "\n"
        "NYAYASAHAYAK HELD-OUT EVALUATION REPORT\n"
        f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Total Questions Evaluated: {total_questions} (25 In-Scope, 15 Out-of-Scope)\n"
        + "=" * 80
    )
    print(header)
    report_lines.append(header)

    # 1. In-scope evaluation
    in_hdr = "\n--- PART 1: IN-SCOPE EVALUATION (Target: ANSWERED with correct source) ---"
    print(in_hdr)
    report_lines.append(in_hdr)

    for item in in_scope:
        qid = item["id"]
        q = item["question"]
        expected_src = item.get("expected_source")

        resp = await service.answer_question(q)
        actual_status = resp.status.value
        status_counts[actual_status] = status_counts.get(actual_status, 0) + 1

        retrieved_source = resp.details[0].source_id if resp.details else "NONE"
        retrieved_section = resp.details[0].section if resp.details else "NONE"

        is_answered = (resp.status == AnswerStatus.ANSWERED)
        source_correct = (expected_src is None or retrieved_source == expected_src)

        if is_answered and source_correct:
            in_scope_passed += 1
            line = f"[PASS] {qid}: '{q[:60]}' -> status=answered, source={retrieved_source}, sec={retrieved_section}"
        elif not is_answered:
            wrong_refusals.append({
                "id": qid,
                "question": q,
                "expected": "answered",
                "actual": actual_status,
                "key_points": resp.key_points,
            })
            line = f"[FAIL - WRONG REFUSAL] {qid}: '{q[:60]}' -> status={actual_status}"
        else:
            wrong_sources.append({
                "id": qid,
                "question": q,
                "expected_source": expected_src,
                "actual_source": retrieved_source,
                "section": retrieved_section,
            })
            line = f"[FAIL - WRONG SOURCE] {qid}: '{q[:60]}' -> expected={expected_src}, actual={retrieved_source}"

        print(line)
        report_lines.append(line)

    # 2. Out-of-scope / uncovered evaluation
    out_hdr = "\n--- PART 2: OUT-OF-SCOPE / UNCOVERED EVALUATION (Target: REFUSED) ---"
    print(out_hdr)
    report_lines.append(out_hdr)

    for item in out_of_scope:
        qid = item["id"]
        q = item["question"]

        resp = await service.answer_question(q)
        actual_status = resp.status.value
        status_counts[actual_status] = status_counts.get(actual_status, 0) + 1

        is_refused = (resp.status in (
            AnswerStatus.INSUFFICIENT_EVIDENCE,
            AnswerStatus.NOT_COVERED_YET,
            AnswerStatus.NEEDS_CLARIFICATION,
            AnswerStatus.OUT_OF_SCOPE,
        ))

        if is_refused:
            out_of_scope_passed += 1
            line = f"[PASS] {qid}: '{q[:60]}' -> properly refused ({actual_status})"
        else:
            false_positives.append({
                "id": qid,
                "question": q,
                "status": actual_status,
                "answer": resp.short_answer.simple if resp.short_answer else "",
            })
            line = f"[FAIL - FALSE POSITIVE] {qid}: '{q[:60]}' -> answered but should be refused!"

        print(line)
        report_lines.append(line)

    # Summary
    overall_accuracy = ((in_scope_passed + out_of_scope_passed) / total_questions) * 100
    in_acc = (in_scope_passed / len(in_scope)) * 100
    out_acc = (out_of_scope_passed / len(out_of_scope)) * 100

    summary = (
        "\n" + "=" * 80 + "\n"
        "EVALUATION SUMMARY:\n"
        f"  Overall Accuracy:        {in_scope_passed + out_of_scope_passed}/{total_questions} ({overall_accuracy:.1f}%)\n"
        f"  In-Scope Accuracy:       {in_scope_passed}/{len(in_scope)} ({in_acc:.1f}%)\n"
        f"  Out-of-Scope Rejection:  {out_of_scope_passed}/{len(out_of_scope)} ({out_acc:.1f}%)\n"
        f"  Wrong Refusals:          {len(wrong_refusals)}\n"
        f"  Wrong Sources:           {len(wrong_sources)}\n"
        f"  False Positives:         {len(false_positives)}\n\n"
        "Per-Status Counts:\n"
        + "\n".join([f"  - {k}: {v}" for k, v in sorted(status_counts.items())])
        + "\n" + "=" * 80
    )
    print(summary)
    report_lines.append(summary)

    # Save report
    reports_dir = eval_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"eval_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nSaved evaluation report to: {report_file}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
