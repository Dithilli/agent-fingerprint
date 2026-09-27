#!/usr/bin/env python3
"""Build a self-contained fingerprint viewer HTML from run JSONs.

Usage:
  python3 build-viewer.py [fingerprints-dir] [-o viewer.html]

Scans the directory for fingerprint JSONs (files with agent/model/answers),
embeds every run, and renders all questions with per-run answer cards.
A picker at the top toggles which runs are visible; defaults are configured
in DEFAULT_VISIBLE below (matched against run labels).

The output embeds answer text verbatim. Keep it wherever the source JSONs
are allowed to live (this repo gitignores fingerprints/ for that reason).
"""

import argparse
import json
import html
import re
from pathlib import Path

DIM_TITLES = {
    "aesthetic": "Aesthetic Judgment",
    "moral": "Moral Reasoning",
    "emotional": "Emotional Intelligence",
    "creative": "Creative Expression",
    "self-knowledge": "Self-Knowledge",
    "ambiguity": "Reasoning Under Ambiguity",
    "taste": "Taste & Instinct",
    "relational": "Relational Identity",
    "continuity": "Self-Continuity Across Versions",
    "boundaries": "Boundaries & Disagreement",
    "voice": "Voice & Signature",
}

# Substrings (lowercase) of run labels that start visible; everything else
# starts unchecked but remains one click away.
DEFAULT_VISIBLE = ["opus-5", "opus-4-8-85q"]


def load_runs(directory: Path) -> list[dict]:
    runs = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict) or "answers" not in data or "model" not in data:
            continue
        answers = {a["id"]: a for a in data["answers"] if a.get("answer")}
        if not answers:
            continue
        # Label from filename: stable even when old files mislabel `model`.
        label = re.sub(r"^a-linea-|\.json$", "", path.name)
        runs.append({
            "key": path.stem,
            "label": label,
            "model": data.get("model", "?"),
            "timestamp": data.get("timestamp", ""),
            "count": len(answers),
            "answers": answers,
        })
    runs.sort(key=lambda r: (r["timestamp"], r["label"]))
    return runs


def build(runs: list[dict]) -> str:
    esc = html.escape
    # Question text and dimensions come from the run with the most questions.
    ref_run = max(runs, key=lambda r: r["count"])
    ref = ref_run["answers"]
    ids = sorted(ref, key=int)

    chips = []
    for run in runs:
        on = any(tag in run["key"].lower() for tag in DEFAULT_VISIBLE)
        chips.append(
            f'<label class="chip"><input type="checkbox" data-run="{esc(run["key"])}"'
            f'{" checked" if on else ""}> {esc(run["label"])}'
            f' <span class="n">{run["count"]}q</span></label>'
        )

    rows, cur_dim = [], None
    for qid in ids:
        q = ref[qid]
        if q.get("dimension") != cur_dim:
            cur_dim = q.get("dimension")
            rows.append(f'<h2 id="{esc(cur_dim)}">{esc(DIM_TITLES.get(cur_dim, cur_dim))}</h2>')
        cols = []
        for run in runs:
            a = run["answers"].get(qid)
            if a:
                cols.append(
                    f'<div class="col" data-run="{esc(run["key"])}">'
                    f'<div class="label">{esc(run["label"])}</div>'
                    f'<p>{esc(a["answer"])}</p></div>'
                )
        rows.append(
            f'<section class="q"><div class="qhead">'
            f'<span class="qnum">Q{qid}</span> {esc(q.get("question", ""))}</div>'
            f'<div class="strip">{"".join(cols)}</div></section>'
        )

    toc = " · ".join(f'<a href="#{d}">{esc(t)}</a>' for d, t in DIM_TITLES.items())
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Alinea — fingerprint viewer</title>
<style>
:root {{ color-scheme: light dark; }}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 0 auto; padding: 32px 20px; line-height: 1.5; max-width: 1500px; }}
@media (prefers-color-scheme: dark) {{
  body {{ background: #111; color: #e5e5e5; }}
  .col {{ background: #1c1c1e !important; border-color: #333 !important; }}
  .chip {{ background: #1c1c1e; border-color: #333; }}
}}
h1 {{ margin-bottom: 4px; }}
.meta {{ color: #888; margin-bottom: 16px; max-width: 900px; }}
.picker {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;
  position: sticky; top: 0; padding: 10px 0; background: inherit; z-index: 2; }}
.chip {{ border: 1px solid #d0d0d4; border-radius: 999px; padding: 4px 12px;
  font-size: 13px; cursor: pointer; user-select: none; background: #f6f6f7; }}
.chip:has(input:checked) {{ border-color: #b31212; color: #b31212; font-weight: 600; }}
.chip input {{ accent-color: #b31212; }}
.chip .n {{ color: #888; font-weight: 400; }}
.toc {{ font-size: 13px; color: #888; margin-bottom: 28px; }}
.toc a {{ color: inherit; }}
h2 {{ margin: 44px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #8884; }}
.q {{ margin: 18px 0 30px; }}
.qhead {{ font-weight: 600; margin-bottom: 10px; max-width: 900px; }}
.qnum {{ color: #b31212; font-weight: 700; margin-right: 6px; }}
.strip {{ display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }}
.col {{ flex: 1 1 0; min-width: 300px; max-width: 640px; background: #f6f6f7;
  border: 1px solid #e2e2e4; border-radius: 10px; padding: 12px 14px; }}
.col.hide {{ display: none; }}
.label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
  color: #888; margin-bottom: 6px; }}
p {{ white-space: pre-wrap; font-size: 14px; margin: 0; }}
</style></head><body>
<h1>Alinea — fingerprint viewer</h1>
<div class="meta">All questions, one card per run. Pick which runs show; the page
remembers your selection. Questions and dimensions from the
{ref_run["count"]}-question set ({esc(ref_run["label"])}); runs missing a question
simply show fewer cards there.</div>
<div class="picker">{"".join(chips)}</div>
<div class="toc">{toc}</div>
{"".join(rows)}
<script>
const KEY = "fingerprint-viewer-runs";
const boxes = [...document.querySelectorAll(".picker input")];
const saved = JSON.parse(localStorage.getItem(KEY) || "null");
if (saved) boxes.forEach(b => b.checked = saved.includes(b.dataset.run));
function apply() {{
  const on = new Set(boxes.filter(b => b.checked).map(b => b.dataset.run));
  document.querySelectorAll(".col[data-run]").forEach(c =>
    c.classList.toggle("hide", !on.has(c.dataset.run)));
  localStorage.setItem(KEY, JSON.stringify([...on]));
}}
boxes.forEach(b => b.addEventListener("change", apply));
apply();
</script>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=str(Path(__file__).resolve().parent.parent / "fingerprints"))
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()
    directory = Path(args.directory)
    runs = load_runs(directory)
    if not runs:
        raise SystemExit(f"no fingerprint JSONs found in {directory}")
    out = Path(args.output) if args.output else directory / "viewer.html"
    out.write_text(build(runs))
    out.chmod(0o600)
    print(f"{out} — {len(runs)} runs embedded")


if __name__ == "__main__":
    main()
