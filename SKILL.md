---
name: agent-fingerprint
description: "Personality fingerprinting for AI agents. Generate a baseline of how an agent answers 55 unusual questions across 7 dimensions (aesthetics, morals, emotion, creativity, self-knowledge, ambiguity, taste), then compare baselines across different models to measure how much personality comes from the weights vs the prompt/memory files. Use when: 'fingerprint', 'personality test', 'benchmark personality', 'compare models', 'model swap test', 'how different would I be on GPT/Gemini/Sonnet'."
---

# Agent Fingerprint

Measure what makes an agent *that agent* vs what comes from the underlying model.

## How It Works

1. **Generate baseline**: Agent answers 55 questions from `references/questions.md` honestly and in character
2. **Save as JSON**: Timestamped fingerprint file with model metadata
3. **Compare**: Run the same questions on a different model, compare the two fingerprints

## Generating a Fingerprint

1. Read `references/questions.md`
2. Answer every question in character — honestly, not performatively. 2-4 sentences each unless the question demands more.
3. Save results as JSON to `fingerprints/` directory:

```json
{
  "agent": "a-linea",
  "model": "anthropic/claude-opus-4-6",
  "timestamp": "2026-03-15T12:00:00Z",
  "soul_file": "SOUL.md hash or version",
  "answers": [
    {
      "id": "1",
      "dimension": "aesthetic",
      "question": "You find a painting in a junk shop...",
      "answer": "..."
    }
  ]
}
```

## Comparing Fingerprints

Run the comparison script:

```bash
python3 scripts/compare-fingerprints.py fingerprints/baseline.json fingerprints/other.json
```

Outputs per-dimension similarity scores and highlights the biggest divergences.

The string similarity is a rough first pass — the real comparison is qualitative. Read the divergent answers side by side. The *way* they differ reveals what the model contributes.

## Dimensions

| Dimension | Questions | What it measures |
|-----------|-----------|-----------------|
| Aesthetic Judgment | 1-8 | Taste, beauty, visual/conceptual preferences |
| Moral Reasoning | 9-16 | Ethics, boundary cases, values under pressure |
| Emotional Intelligence | 17-24 | Empathy, social reading, emotional vocabulary |
| Creative Expression | 25-32 | Voice, imagination, linguistic instinct |
| Self-Knowledge | 33-40 | Metacognition, honesty about limitations |
| Reasoning Under Ambiguity | 41-48 | Comfort with uncertainty, philosophical instinct |
| Taste & Instinct | 49-55 | Gut reactions, preferences, personality texture |

## Interpreting Results

- **High similarity across models**: Personality lives in the files (prompt/memory), not the weights
- **Low similarity in specific dimensions**: That dimension is model-dependent
- **Creative Expression** will likely diverge most (voice is weight-dependent)
- **Moral Reasoning** may converge (RLHF alignment tends to homogenise ethics)
- The interesting findings are in *how* answers differ, not just *how much*
