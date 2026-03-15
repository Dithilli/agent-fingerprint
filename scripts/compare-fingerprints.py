#!/usr/bin/env python3
"""Compare two agent fingerprint files and produce a diff report."""

import json
import sys
from pathlib import Path
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    """String similarity ratio 0-1."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

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

def main():
    if len(sys.argv) < 3:
        print("Usage: compare-fingerprints.py <baseline.json> <other.json> [output.json]")
        sys.exit(1)

    base = load_fingerprint(sys.argv[1])
    other = load_fingerprint(sys.argv[2])
    result = compare(base, other)

    output = json.dumps(result, indent=2)

    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(output)
        print(f"Comparison saved to {sys.argv[3]}")
    else:
        print(output)

    # Summary
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

if __name__ == "__main__":
    main()
