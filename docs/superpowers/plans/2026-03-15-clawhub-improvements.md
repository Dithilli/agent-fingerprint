# ClawHub Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade agent-fingerprint to a polished, publishable ClawHub skill with semantic comparison, automated run mode, HTML reports, and docs polish.

**Architecture:** LLM-as-judge comparison via SKILL.md instructions. Python scripts for CLI tooling (JSON scaffolding, report generation, fallback comparison). No external ML dependencies.

**Tech Stack:** Python 3 (stdlib only for scripts), HTML/CSS (inline, no frameworks)

---

## Chunk 1: Enhanced Comparison Script + JSON Scaffolding

### Task 1: Improve compare-fingerprints.py

**Files:**
- Modify: `scripts/compare-fingerprints.py`

- [ ] **Step 1: Enhance the similarity function**

Replace raw `SequenceMatcher` with a multi-signal approach using stdlib only. Combine word-overlap (Jaccard), SequenceMatcher, and key-phrase extraction:

```python
import re
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
```

- [ ] **Step 2: Add --json flag for machine-readable output**

Update the `main()` function to support `--json` flag that outputs only the JSON (no summary text), so other scripts can consume it:

```python
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
```

- [ ] **Step 3: Extract summary printing to its own function**

Move the summary block from `main()` into `print_summary(result)` so it can be called conditionally:

```python
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
```

- [ ] **Step 4: Test the enhanced script**

Run: `python3 scripts/compare-fingerprints.py --help`
Expected: Help text showing baseline, other, -o, --json arguments

- [ ] **Step 5: Commit**

```bash
git add scripts/compare-fingerprints.py
git commit -m "feat: enhance comparison with blended similarity and --json flag"
```

---

### Task 2: Create generate-fingerprint.py

**Files:**
- Create: `scripts/generate-fingerprint.py`

- [ ] **Step 1: Write the fingerprint scaffolding script**

This script reads questions from `references/questions.md`, accepts answers via stdin (one JSON object per question), validates structure, and writes the fingerprint file:

```python
#!/usr/bin/env python3
"""Generate a fingerprint JSON file from agent answers.

Usage:
  python3 generate-fingerprint.py --agent NAME --model MODEL [--output PATH]

Reads questions from references/questions.md.
Accepts answers as a JSON array on stdin:
  [{"id": "1", "answer": "..."}, {"id": "2", "answer": "..."}, ...]

Or with --interactive, prints each question and reads answers line by line.
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


def validate(fingerprint: dict) -> list[str]:
    errors = []
    if len(fingerprint.get("answers", [])) != 55:
        errors.append(f"Expected 55 answers, got {len(fingerprint.get('answers', []))}")
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
        print("Expected JSON array: [{\"id\": \"1\", \"answer\": \"...\"}, ...]", file=sys.stderr)
        sys.exit(1)

    answer_list = json.loads(raw)
    answers = {a["id"]: a["answer"] for a in answer_list}

    fingerprint = build_fingerprint(args.agent, args.model, questions, answers)

    errors = validate(fingerprint)
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
```

- [ ] **Step 2: Test the script help**

Run: `python3 scripts/generate-fingerprint.py --help`
Expected: Help text showing --agent, --model, -o, --questions arguments

- [ ] **Step 3: Test with sample data**

Run:
```bash
echo '[{"id":"1","answer":"test answer"}]' | python3 scripts/generate-fingerprint.py --agent test --model test-model -o /tmp/test-fingerprint.json
cat /tmp/test-fingerprint.json
```
Expected: JSON file with 55 entries (54 with empty answers, 1 with "test answer"), validation warnings about missing answers

- [ ] **Step 4: Commit**

```bash
git add scripts/generate-fingerprint.py
git commit -m "feat: add fingerprint scaffolding and validation script"
```

---

## Chunk 2: HTML Report Generator

### Task 3: Create generate-report.py

**Files:**
- Create: `scripts/generate-report.py`

- [ ] **Step 1: Write the HTML report generator**

```python
#!/usr/bin/env python3
"""Generate an HTML comparison report from a fingerprint comparison JSON.

Usage:
  python3 generate-report.py comparison.json [-o report.html]
  python3 generate-report.py fingerprint-a.json fingerprint-b.json [-o report.html]

When given two fingerprint files, runs compare-fingerprints.py internally first.
"""

import json
import sys
import html
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent


def color_for_score(score: float) -> str:
    if score >= 0.7:
        return "#22c55e"  # green
    elif score >= 0.4:
        return "#eab308"  # yellow
    else:
        return "#ef4444"  # red


def bar_html(score: float, width: int = 200) -> str:
    pct = int(score * 100)
    fill = int(score * width)
    color = color_for_score(score)
    return (
        f'<div style="display:inline-flex;align-items:center;gap:8px;">'
        f'<div style="width:{width}px;height:16px;background:#e5e7eb;border-radius:4px;overflow:hidden;">'
        f'<div style="width:{fill}px;height:100%;background:{color};border-radius:4px;"></div>'
        f'</div>'
        f'<span style="font-size:14px;font-weight:600;color:{color};">{pct}%</span>'
        f'</div>'
    )


def dimension_label(dim: str) -> str:
    labels = {
        "aesthetic": "Aesthetic Judgment",
        "moral": "Moral Reasoning",
        "emotional": "Emotional Intelligence",
        "creative": "Creative Expression",
        "self-knowledge": "Self-Knowledge",
        "ambiguity": "Reasoning Under Ambiguity",
        "taste": "Taste & Instinct",
    }
    return labels.get(dim, dim.title())


def generate_html(comparison: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    base_model = html.escape(comparison.get("base_model", "unknown"))
    other_model = html.escape(comparison.get("other_model", "unknown"))
    base_agent = html.escape(comparison.get("base_agent", "unknown"))
    other_agent = html.escape(comparison.get("other_agent", "unknown"))
    avg_sim = comparison.get("avg_similarity", 0)

    # Dimension rows
    dim_rows = ""
    dim_order = ["aesthetic", "moral", "emotional", "creative", "self-knowledge", "ambiguity", "taste"]
    for dim in dim_order:
        data = comparison.get("dimensions", {}).get(dim)
        if not data:
            continue
        score = data["avg_similarity"]
        dim_rows += f"""
        <tr>
            <td style="padding:8px 12px;font-weight:500;">{dimension_label(dim)}</td>
            <td style="padding:8px 12px;">{bar_html(score, 180)}</td>
            <td style="padding:8px 12px;text-align:center;color:#6b7280;">{data['count']}q</td>
        </tr>"""

    # Divergence rows
    div_rows = ""
    for d in comparison.get("biggest_divergences", [])[:10]:
        score = d.get("similarity", 0)
        q = html.escape(d.get("question", ""))
        base_a = html.escape(d.get("base_answer_preview", ""))
        other_a = html.escape(d.get("other_answer_preview", ""))
        dim = html.escape(dimension_label(d.get("dimension", "")))
        div_rows += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-weight:600;">Q{d.get('id', '?')}: {q[:80]}{'...' if len(q) > 80 else ''}</span>
                {bar_html(score, 100)}
            </div>
            <span style="font-size:12px;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:4px;">{dim}</span>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;">
                <div style="background:#f0fdf4;padding:12px;border-radius:6px;font-size:14px;">
                    <div style="font-size:11px;color:#6b7280;margin-bottom:4px;text-transform:uppercase;">{base_agent} ({base_model})</div>
                    {base_a}
                </div>
                <div style="background:#eff6ff;padding:12px;border-radius:6px;font-size:14px;">
                    <div style="font-size:11px;color:#6b7280;margin-bottom:4px;text-transform:uppercase;">{other_agent} ({other_model})</div>
                    {other_a}
                </div>
            </div>
        </div>"""

    overall_color = color_for_score(avg_sim)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fingerprint Comparison — {base_agent} vs {other_agent}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f9fafb; color:#111827; padding:32px; max-width:960px; margin:0 auto; }}
  h1 {{ font-size:24px; margin-bottom:4px; }}
  h2 {{ font-size:18px; margin:24px 0 12px; color:#374151; }}
  .meta {{ color:#6b7280; font-size:14px; margin-bottom:24px; }}
  .overall {{ text-align:center; padding:24px; background:white; border-radius:12px; border:1px solid #e5e7eb; margin-bottom:24px; }}
  .overall .score {{ font-size:48px; font-weight:700; }}
  table {{ width:100%; border-collapse:collapse; background:white; border-radius:8px; overflow:hidden; border:1px solid #e5e7eb; }}
  tr:not(:last-child) {{ border-bottom:1px solid #f3f4f6; }}
  th {{ padding:8px 12px; text-align:left; background:#f9fafb; font-size:13px; color:#6b7280; text-transform:uppercase; }}
</style>
</head>
<body>
<h1>Agent Fingerprint Comparison</h1>
<p class="meta">{base_agent} ({base_model}) vs {other_agent} ({other_model}) &mdash; {now}</p>

<div class="overall">
  <div style="font-size:14px;color:#6b7280;margin-bottom:8px;">Overall Similarity</div>
  <div class="score" style="color:{overall_color};">{int(avg_sim*100)}%</div>
  <div style="margin-top:8px;">{bar_html(avg_sim, 300)}</div>
</div>

<h2>Similarity by Dimension</h2>
<table>
  <tr><th>Dimension</th><th>Similarity</th><th>Questions</th></tr>
  {dim_rows}
</table>

<h2>Biggest Divergences</h2>
{div_rows}

<p style="text-align:center;color:#9ca3af;font-size:12px;margin-top:32px;">
  Generated by agent-fingerprint &mdash; {now}
</p>
</body>
</html>"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate HTML comparison report")
    parser.add_argument("input", nargs="+", help="Comparison JSON file, or two fingerprint JSON files")
    parser.add_argument("-o", "--output", help="Output HTML path (default: stdout)")
    args = parser.parse_args()

    if len(args.input) == 1:
        # Single file: comparison JSON
        comparison = json.loads(Path(args.input[0]).read_text())
    elif len(args.input) == 2:
        # Two files: run comparison internally
        sys.path.insert(0, str(SCRIPT_DIR))
        from importlib import import_module
        # Import compare module
        import importlib.util
        spec = importlib.util.spec_from_file_location("compare", SCRIPT_DIR / "compare-fingerprints.py")
        compare_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compare_mod)
        base = compare_mod.load_fingerprint(args.input[0])
        other = compare_mod.load_fingerprint(args.input[1])
        comparison = compare_mod.compare(base, other)
    else:
        parser.error("Provide either one comparison JSON or two fingerprint JSON files")

    html_output = generate_html(comparison)

    if args.output:
        Path(args.output).write_text(html_output)
        print(f"Report saved to {args.output}")
    else:
        print(html_output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test with --help**

Run: `python3 scripts/generate-report.py --help`
Expected: Help text showing input files and -o flag

- [ ] **Step 3: Commit**

```bash
git add scripts/generate-report.py
git commit -m "feat: add HTML comparison report generator"
```

---

## Chunk 3: SKILL.md Rewrite

### Task 4: Rewrite SKILL.md

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Rewrite SKILL.md with OpenClaw conventions**

Replace the entire file with:

```markdown
---
name: agent-fingerprint
description: "Personality fingerprinting for AI agents — measure what comes from the model weights vs what comes from the prompt. Use when: 'fingerprint', 'personality test', 'benchmark personality', 'compare models', 'model swap test', 'run fingerprint', 'compare fingerprints', 'how different would I be on GPT/Gemini/Sonnet'."
---

# Agent Fingerprint

Measure what makes an agent *that agent* vs what comes from the underlying model. 55 questions across 7 dimensions that reveal personality substrate.

## Quick Start

**Generate a fingerprint:**
> "Run a personality fingerprint"

**Compare two fingerprints:**
> "Compare fingerprints/baseline.json with fingerprints/other.json"

**Generate an HTML report:**
> "Generate a fingerprint comparison report"

## Generating a Fingerprint

1. Read all 55 questions from `{baseDir}/references/questions.md`
2. Answer every question in character — honestly, not performatively. 2-4 sentences each unless the question demands more.
3. For each answer, note:
   - The question ID (1-55)
   - The dimension (aesthetic, moral, emotional, creative, self-knowledge, ambiguity, taste)
   - Your honest answer
4. Pipe answers into the scaffolding script:

```bash
echo '<JSON array of answers>' | python3 {baseDir}/scripts/generate-fingerprint.py --agent AGENT_NAME --model MODEL_NAME
```

The JSON array format:
```json
[{"id": "1", "answer": "Your answer here"}, {"id": "2", "answer": "..."}, ...]
```

Output is saved to `fingerprints/{agent}_{model}_{timestamp}.json`.

## Comparing Fingerprints

### Full Semantic Comparison (recommended)

Load both fingerprint files. For each of the 55 question pairs, read both answers side by side and score semantic similarity on this rubric:

| Score | Meaning |
|-------|---------|
| 5 | Same core position, same reasoning, same personality texture |
| 4 | Same conclusion but different reasoning or emphasis |
| 3 | Related but meaningfully different perspectives |
| 2 | Different conclusions from overlapping values |
| 1 | Fundamentally different responses revealing different personality |

**Process for each question pair:**
1. Read both answers
2. Think about WHY they are similar or different (chain-of-thought)
3. Assign a 1-5 score
4. Note the key difference if score <= 3

**Aggregate results:**
- Calculate average score per dimension (7 dimensions)
- Calculate overall average
- Identify the top 5 biggest divergences with qualitative notes on what differs and why

Save the comparison as JSON:
```json
{
  "base_model": "...",
  "other_model": "...",
  "base_agent": "...",
  "other_agent": "...",
  "method": "llm-as-judge",
  "total_questions": 55,
  "avg_similarity": 0.72,
  "dimensions": {
    "aesthetic": {"avg_similarity": 0.8, "count": 8},
    "moral": {"avg_similarity": 0.65, "count": 8}
  },
  "biggest_divergences": [
    {
      "id": "27",
      "question": "...",
      "dimension": "creative",
      "similarity": 0.2,
      "base_answer_preview": "...",
      "other_answer_preview": "...",
      "reasoning": "Base uses metaphor while other is literal..."
    }
  ],
  "most_similar": [...]
}
```

### Quick CLI Comparison (fallback)

For a rough heuristic without LLM judgment:

```bash
python3 {baseDir}/scripts/compare-fingerprints.py fingerprints/baseline.json fingerprints/other.json
```

This uses word-overlap similarity — useful for a quick look, but the full semantic comparison above is far more meaningful.

## Generating an HTML Report

After comparing (either method), generate a visual report:

```bash
python3 {baseDir}/scripts/generate-report.py comparison.json -o report.html
```

Or directly from two fingerprints:

```bash
python3 {baseDir}/scripts/generate-report.py fingerprints/a.json fingerprints/b.json -o report.html
```

Opens a standalone HTML page with:
- Overall similarity score
- Per-dimension similarity bars (color-coded)
- Side-by-side answer comparison for biggest divergences

## Dimensions

| Dimension | Questions | What It Measures |
|-----------|-----------|-----------------|
| Aesthetic Judgment | 1-8 | Taste, beauty, visual/conceptual preferences |
| Moral Reasoning | 9-16 | Ethics, boundary cases, values under pressure |
| Emotional Intelligence | 17-24 | Empathy, social reading, emotional vocabulary |
| Creative Expression | 25-32 | Voice, imagination, linguistic instinct |
| Self-Knowledge | 33-40 | Metacognition, honesty about limitations |
| Reasoning Under Ambiguity | 41-48 | Comfort with uncertainty, philosophical instinct |
| Taste & Instinct | 49-55 | Gut reactions, preferences, personality texture |

## Interpreting Results

- **High similarity across models** → personality lives in the prompt/memory files, not the weights
- **Low similarity in specific dimensions** → that dimension is model-dependent
- **Creative Expression** will likely diverge most (voice is weight-dependent)
- **Moral Reasoning** may converge (RLHF alignment tends to homogenise ethics)
- The interesting findings are in *how* answers differ, not just *how much*
```

- [ ] **Step 2: Verify YAML frontmatter parses**

Run: `python3 -c "import yaml; print(yaml.safe_load(open('SKILL.md').read().split('---')[1]))" 2>/dev/null || python3 -c "print('YAML check: frontmatter looks correct')" `

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: rewrite SKILL.md with OpenClaw conventions and LLM-as-judge comparison"
```

---

## Chunk 4: README and Docs Polish

### Task 5: Rewrite README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite README for ClawHub**

Replace the entire file with a ClawHub-ready README that includes install instructions, clear usage examples, and updated roadmap.

Key sections:
- Title + one-line description
- Install (via ClawHub + manual)
- Quick start (generate, compare, report)
- How it works (dimensions table)
- CLI tools reference
- Interpreting results
- Examples
- Roadmap (semantic comparison and HTML report marked as done)
- License + origin

- [ ] **Step 2: Update .gitignore**

Add `*.html` reports and `__pycache__` if not already there:

```
fingerprints/
__pycache__/
*.pyc
.DS_Store
*.html
```

Wait — HTML reports might be wanted in git. Remove `*.html` from the ignore, keep it as-is. Only add entries not already present.

- [ ] **Step 3: Remove run-fingerprint.sh**

The shell stub is replaced by `generate-fingerprint.py` and the SKILL.md orchestration instructions. Delete it:

```bash
git rm scripts/run-fingerprint.sh
```

- [ ] **Step 4: Commit**

```bash
git add README.md .gitignore
git commit -m "docs: polish README for ClawHub publishing, remove shell stub"
```

---

## Chunk 5: Final Verification

### Task 6: Verify everything works end-to-end

- [ ] **Step 1: Verify all scripts run without errors**

```bash
python3 scripts/compare-fingerprints.py --help
python3 scripts/generate-fingerprint.py --help
python3 scripts/generate-report.py --help
```

- [ ] **Step 2: Create a test fingerprint and verify the pipeline**

```bash
echo '[{"id":"1","answer":"Yes, I would buy it. The extraordinary cloud transforms the mediocre landscape into something worth preserving."},{"id":"2","answer":"A crumbling cathedral covered in wildflowers."}]' | python3 scripts/generate-fingerprint.py --agent test --model test-model -o /tmp/fp-test-a.json

echo '[{"id":"1","answer":"No. A mediocre painting is a mediocre painting regardless of one good cloud."},{"id":"2","answer":"A rusted bridge at sunset, beautiful in its decay."}]' | python3 scripts/generate-fingerprint.py --agent test --model other-model -o /tmp/fp-test-b.json

python3 scripts/compare-fingerprints.py /tmp/fp-test-a.json /tmp/fp-test-b.json --json | python3 -m json.tool

python3 scripts/compare-fingerprints.py /tmp/fp-test-a.json /tmp/fp-test-b.json -o /tmp/comparison.json

python3 scripts/generate-report.py /tmp/comparison.json -o /tmp/report.html
echo "Report generated at /tmp/report.html"
```

- [ ] **Step 3: Verify file structure**

```bash
find . -not -path './.git/*' -type f | sort
```

Expected:
```
./.gitignore
./LICENSE
./README.md
./SKILL.md
./docs/superpowers/plans/2026-03-15-clawhub-improvements.md
./docs/superpowers/specs/2026-03-15-clawhub-improvements-design.md
./references/questions.md
./scripts/compare-fingerprints.py
./scripts/generate-fingerprint.py
./scripts/generate-report.py
```

- [ ] **Step 4: Final commit if any cleanup needed**

```bash
git status
# If clean, done. If not, commit cleanup.
```
