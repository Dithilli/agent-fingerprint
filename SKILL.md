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
