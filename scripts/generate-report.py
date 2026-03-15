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
import importlib.util
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
