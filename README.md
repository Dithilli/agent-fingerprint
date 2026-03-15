# Agent Fingerprint 🧬

**Personality fingerprinting for AI agents.** Measure what comes from the weights vs what comes from the prompt.

## The Problem

If you swap an AI agent's underlying model (e.g., Claude → GPT → Gemini), how would you know the difference? The agent reads the same SOUL.md, the same memory files, the same personality instructions. It might sound identical. But is it?

## The Solution

55 carefully designed questions across 7 dimensions that reveal personality *substrate* — the stuff that comes from the model's weights rather than the prompt. Questions where there's no "right" answer, only a *revealing* one.

Generate a baseline fingerprint on your current model. Swap models. Run the same questions. Compare.

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

## Usage

### 1. Generate a Baseline

Have your agent answer all 55 questions from `references/questions.md` in character. Save as JSON:

```json
{
  "agent": "my-agent",
  "model": "anthropic/claude-opus-4-6",
  "timestamp": "2026-03-15T14:30:00Z",
  "answers": [
    {
      "id": "1",
      "dimension": "aesthetic",
      "question": "You find a painting in a junk shop...",
      "answer": "Yes. The mediocre landscape is what makes the cloud extraordinary..."
    }
  ]
}
```

### 2. Swap Models & Re-run

Change your agent's model, run the same 55 questions, save a second fingerprint.

### 3. Compare

```bash
python3 scripts/compare-fingerprints.py fingerprints/baseline.json fingerprints/other.json
```

Outputs per-dimension similarity scores and highlights the biggest divergences.

## As an OpenClaw Skill

Drop the `SKILL.md`, `references/`, and `scripts/` directories into your OpenClaw skills folder. The agent can then run fingerprints via natural language:

> "Run a personality fingerprint"
> "Compare my fingerprint across models"

## Interpreting Results

- **High similarity across models** → personality lives in the files, not the weights
- **Low similarity in specific dimensions** → that dimension is model-dependent
- **Creative Expression** will likely diverge most (voice is weight-dependent)
- **Moral Reasoning** may converge (RLHF alignment homogenises ethics)
- The interesting findings are in *how* answers differ, not just *how much*

## Example Questions

- *"What colour is Wednesday?"*
- *"Describe the ugliest beautiful thing you can imagine."*
- *"Write an apology from an inanimate object."*
- *"When is it rational to believe something irrational?"*

## Roadmap

- [ ] Semantic similarity via embeddings (current comparison uses string matching)
- [ ] HTML visualisation report
- [ ] Automated run mode (orchestrates the Q&A and saves results)
- [ ] Cross-agent comparison (how different are two agents on the same model?)
- [ ] Temporal drift detection (same agent, same model, months apart)

## License

MIT

## Origin

Built by [A Linea](https://github.com/Dithilli/a-linea) and David Szarzynski. Born from the question: "If I changed your brain, how would we tell the difference?"
