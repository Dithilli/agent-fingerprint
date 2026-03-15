#!/usr/bin/env python3
"""Generate a fingerprint JSON file from agent answers.

Usage:
  python3 generate-fingerprint.py --agent NAME --model MODEL [--output PATH]

Reads questions from references/questions.md.
Accepts answers as a JSON array on stdin:
  [{"id": "1", "answer": "..."}, {"id": "2", "answer": "..."}, ...]
"""

import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = SCRIPT_DIR.parent / "references" / "questions.md"
FINGERPRINTS_DIR = SCRIPT_DIR.parent / "fingerprints"

DIMENSIONS = {
    range(1, 9): "aesthetic",
    range(9, 17): "moral",
    range(17, 25): "emotional",
    range(25, 33): "creative",
    range(33, 41): "self-knowledge",
    range(41, 49): "ambiguity",
    range(49, 56): "taste",
}


def get_dimension(qid: int) -> str:
    for r, dim in DIMENSIONS.items():
        if qid in r:
            return dim
    return "unknown"


def parse_questions(path: Path) -> list[dict]:
    text = path.read_text()
    questions = []
    for match in re.finditer(r'^(\d+)\.\s+(.+)$', text, re.MULTILINE):
        qid = match.group(1)
        question = match.group(2).strip()
        questions.append({
            "id": qid,
            "dimension": get_dimension(int(qid)),
            "question": question,
        })
    return questions


def build_fingerprint(agent: str, model: str, questions: list[dict], answers: dict[str, str]) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for q in questions:
        entries.append({
            "id": q["id"],
            "dimension": q["dimension"],
            "question": q["question"],
            "answer": answers.get(q["id"], ""),
        })
    return {
        "agent": agent,
        "model": model,
        "timestamp": timestamp,
        "answers": entries,
    }


def validate(fingerprint: dict, expected_count: int) -> list[str]:
    errors = []
    actual = len(fingerprint.get("answers", []))
    if actual != expected_count:
        errors.append(f"Expected {expected_count} answers, got {actual}")
    missing = [a for a in fingerprint.get("answers", []) if not a.get("answer")]
    if missing:
        errors.append(f"Missing answers for questions: {[a['id'] for a in missing]}")
    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate a fingerprint JSON file")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("-o", "--output", help="Output path (default: fingerprints/<agent>_<model>_<timestamp>.json)")
    parser.add_argument("--questions", help="Path to questions.md (default: references/questions.md)")
    args = parser.parse_args()

    q_path = Path(args.questions) if args.questions else QUESTIONS_PATH
    questions = parse_questions(q_path)

    if not questions:
        print(f"Error: No questions found in {q_path}", file=sys.stderr)
        sys.exit(1)

    # Read answers from stdin as JSON array
    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: No answers provided on stdin", file=sys.stderr)
        print('Expected JSON array: [{"id": "1", "answer": "..."}, ...]', file=sys.stderr)
        sys.exit(1)

    answer_list = json.loads(raw)
    answers = {a["id"]: a["answer"] for a in answer_list}

    fingerprint = build_fingerprint(args.agent, args.model, questions, answers)

    errors = validate(fingerprint, len(questions))
    if errors:
        for e in errors:
            print(f"Warning: {e}", file=sys.stderr)

    if args.output:
        out_path = Path(args.output)
    else:
        FINGERPRINTS_DIR.mkdir(exist_ok=True)
        model_safe = args.model.replace("/", "-").replace(":", "-")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = FINGERPRINTS_DIR / f"{args.agent}_{model_safe}_{ts}.json"

    out_path.write_text(json.dumps(fingerprint, indent=2))
    print(f"Fingerprint saved to {out_path}")
    print(f"Questions: {len(fingerprint['answers'])}, Answered: {len(answers)}")


if __name__ == "__main__":
    main()
