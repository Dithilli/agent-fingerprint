#!/usr/bin/env python3
"""Compare two agent fingerprint files and produce a diff report."""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


def tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens, stripping punctuation."""
    return set(re.findall(r'\b\w+\b', text.lower()))


def jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity."""
    tokens_a, tokens_b = tokenize(a), tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def similarity(a: str, b: str) -> float:
    """Blended similarity: 60% Jaccard (semantic), 40% SequenceMatcher (structural)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    j = jaccard(a, b)
    s = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return 0.6 * j + 0.4 * s


def load_fingerprint(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def compare(base: dict, other: dict) -> dict:
    results = {
        "base_model": base.get("model", "unknown"),
        "other_model": other.get("model", "unknown"),
        "base_agent": base.get("agent", "unknown"),
        "other_agent": other.get("agent", "unknown"),
        "total_questions": 0,
        "avg_similarity": 0.0,
        "dimensions": {},
        "biggest_divergences": [],
        "most_similar": [],
    }

    base_answers = {a["id"]: a for a in base.get("answers", [])}
    other_answers = {a["id"]: a for a in other.get("answers", [])}

    all_ids = sorted(set(base_answers.keys()) | set(other_answers.keys()))
    results["total_questions"] = len(all_ids)

    scores = []
    dimension_scores = {}

    for qid in all_ids:
        ba = base_answers.get(qid, {})
        oa = other_answers.get(qid, {})

        b_text = ba.get("answer", "")
        o_text = oa.get("answer", "")
        dim = ba.get("dimension", oa.get("dimension", "unknown"))

        sim = similarity(b_text, o_text)
        scores.append(sim)

        if dim not in dimension_scores:
            dimension_scores[dim] = []
        dimension_scores[dim].append(sim)

        entry = {
            "id": qid,
            "question": ba.get("question", oa.get("question", "")),
            "dimension": dim,
            "similarity": round(sim, 3),
            "base_answer_preview": b_text[:150],
            "other_answer_preview": o_text[:150],
        }

        results["biggest_divergences"].append(entry)
        results["most_similar"].append(entry)

    results["avg_similarity"] = round(sum(scores) / len(scores), 3) if scores else 0

    for dim, dim_scores in dimension_scores.items():
        results["dimensions"][dim] = {
            "avg_similarity": round(sum(dim_scores) / len(dim_scores), 3),
            "count": len(dim_scores),
        }

    results["biggest_divergences"].sort(key=lambda x: x["similarity"])
    results["biggest_divergences"] = results["biggest_divergences"][:10]

    results["most_similar"].sort(key=lambda x: x["similarity"], reverse=True)
    results["most_similar"] = results["most_similar"][:5]

    return results


def print_summary(result: dict):
    print(f"\n{'='*60}")
    print(f"FINGERPRINT COMPARISON")
    print(f"{'='*60}")
    print(f"Base:  {result['base_model']} ({result['base_agent']})")
    print(f"Other: {result['other_model']} ({result['other_agent']})")
    print(f"Overall similarity: {result['avg_similarity']*100:.1f}%")
    print(f"\nBy dimension:")
    for dim, data in sorted(result["dimensions"].items()):
        bar = "█" * int(data["avg_similarity"] * 20) + "░" * (20 - int(data["avg_similarity"] * 20))
        print(f"  {dim:30s} {bar} {data['avg_similarity']*100:.1f}%")
    print(f"\nTop 5 biggest divergences:")
    for d in result["biggest_divergences"][:5]:
        print(f"  Q{d['id']:2s} ({d['dimension']:20s}) — {d['similarity']*100:.1f}% similar")
        print(f"      {d['question'][:80]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compare two agent fingerprints")
    parser.add_argument("baseline", help="Path to baseline fingerprint JSON")
    parser.add_argument("other", help="Path to other fingerprint JSON")
    parser.add_argument("-o", "--output", help="Save comparison JSON to file")
    parser.add_argument("--json", action="store_true", help="Output JSON only (no summary)")
    args = parser.parse_args()

    base = load_fingerprint(args.baseline)
    other = load_fingerprint(args.other)
    result = compare(base, other)

    output_json = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output_json)

    if args.json:
        print(output_json)
    else:
        if args.output:
            print(f"Comparison saved to {args.output}")
        else:
            print(output_json)
        print_summary(result)


if __name__ == "__main__":
    main()
