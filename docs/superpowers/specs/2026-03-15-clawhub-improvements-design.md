# ClawHub Improvements — Design Spec

## Goal

Upgrade agent-fingerprint from a rough prototype to a polished, publishable ClawHub skill with four improvements: LLM-as-judge semantic comparison, automated run mode, HTML report generation, and docs polish.

## Architecture

The skill is an OpenClaw SKILL.md with bundled scripts and references. The agent itself performs semantic comparison (LLM-as-judge) — no external ML libraries. Python scripts provide CLI tooling for report generation and lightweight fallback comparison.

## Improvement 1: Semantic Similarity — LLM-as-Judge

**Problem:** `compare-fingerprints.py` uses `SequenceMatcher` (character-level string matching). Two answers saying the same thing in different words score low.

**Solution:** The SKILL.md comparison section instructs the agent to:
1. Load both fingerprint JSON files
2. For each question pair, read both answers side by side
3. Score on a 1-5 rubric with chain-of-thought reasoning:
   - 5: Same core position, same reasoning, same personality texture
   - 4: Same conclusion but different reasoning or emphasis
   - 3: Related but meaningfully different perspectives
   - 2: Different conclusions from overlapping values
   - 1: Fundamentally different responses
4. Aggregate scores per dimension and overall
5. Highlight top divergences with qualitative analysis of WHY they differ
6. Save structured comparison JSON

The Python script (`compare-fingerprints.py`) stays as a quick CLI fallback with improved string matching, but is explicitly positioned as "rough heuristic — for real comparison, use the skill."

## Improvement 2: Automated Run Mode

**Problem:** The shell script (`run-fingerprint.sh`) just prints instructions. The agent has to manually read questions, answer them, and assemble JSON. Error-prone and tedious.

**Solution:** The SKILL.md orchestration section provides step-by-step instructions for the agent to:
1. Read `references/questions.md` and parse all 55 questions
2. Iterate through each question, answering in character (2-4 sentences)
3. Assemble answers into the fingerprint JSON schema
4. Validate the JSON structure (all 55 questions, correct dimension labels, required metadata)
5. Save to `fingerprints/{agent}_{model}_{timestamp}.json`

A Python helper script (`scripts/generate-fingerprint.py`) handles JSON scaffolding — takes answers as input, validates structure, writes the file. The agent calls this script rather than hand-assembling JSON.

## Improvement 3: HTML Report

**Problem:** Comparison output is terminal-only (JSON + bar charts). Hard to share or review side-by-side.

**Solution:** A Python script (`scripts/generate-report.py`) that:
1. Takes a comparison JSON file as input (output of the agent's LLM-as-judge comparison or the Python fallback)
2. Generates a standalone HTML file (no external dependencies, all CSS inline)
3. Shows:
   - Header with agent/model metadata
   - Overall similarity score
   - Per-dimension similarity bars (color-coded: green > 70%, yellow 40-70%, red < 40%)
   - Side-by-side answer comparison for each question
   - Divergence highlights (top 10 biggest differences)

## Improvement 4: Docs Polish

**Problem:** README and SKILL.md are functional but not ClawHub-ready. Missing trigger phrases, install instructions, progressive disclosure.

**Solution:**

**SKILL.md rewrite:**
- Proper trigger phrases in description field
- Progressive disclosure: overview → quick start → generate → compare → report
- `{baseDir}` references to bundled scripts
- LLM-as-judge rubric inline
- Rules/guardrails section

**README rewrite:**
- ClawHub install instructions (`clawhub install agent-fingerprint`)
- Proper usage examples with expected output
- Clear separation of "as a skill" vs "standalone CLI"
- Updated roadmap (mark completed items)

## File Structure

```
agent-fingerprint/
├── SKILL.md                          # Rewritten — OpenClaw conventions
├── README.md                         # Rewritten — ClawHub-ready
├── references/
│   └── questions.md                  # Unchanged
├── scripts/
│   ├── compare-fingerprints.py       # Enhanced — better string matching + JSON output for HTML
│   ├── generate-fingerprint.py       # New — JSON scaffolding/validation helper
│   └── generate-report.py           # New — HTML report generator
├── fingerprints/                     # .gitignored — user data
├── LICENSE                           # Unchanged
└── .gitignore                        # Updated
```

## Out of Scope

- Embedding-based comparison (the agent IS the semantic engine)
- Cross-agent comparison (future)
- Temporal drift detection (future)
- Web UI or server (reports are static HTML files)
