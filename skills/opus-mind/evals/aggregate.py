#!/usr/bin/env python3
"""
opus-mind aggregate — join eval subagent results with audit scores.

Reads:
  evals/results/*.json      — subagent outputs (from Sonnet role-plays)
  evals/audits/*.json       — audit.py --json output per corpus prompt

Writes:
  evals/REPORT.md           — invariant correlation table

Key measurement: for each invariant, compute the mean behavior score on
test cases bucketed by whether the prompt passed or failed that
invariant. Positive delta = invariant is load-bearing. Near zero =
invariant is theater.

No API calls. Stdlib only.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
RESPONSES_DIR = HERE / "responses"
GRADES_DIR = HERE / "grades"
AUDITS_DIR = HERE / "audits"
REPORT_PATH = HERE / "REPORT.md"


def _merge_two_stage() -> int:
    """Join responses/ + grades/ → results/. Returns count merged."""
    if not RESPONSES_DIR.exists() or not GRADES_DIR.exists():
        return 0
    merged = 0
    for resp_file in sorted(RESPONSES_DIR.glob("*.json")):
        grade_file = GRADES_DIR / resp_file.name
        if not grade_file.exists():
            continue
        try:
            resp = json.loads(resp_file.read_text(encoding="utf-8"))
            grade = json.loads(grade_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"warn: merge skip {resp_file.name}: {e}",
                  file=sys.stderr)
            continue

        # Build id → response, id → grade
        resp_by_id = {r["id"]: r for r in resp.get("responses", [])}
        grade_by_id = {g["id"]: g for g in grade.get("grades", [])}

        out_results = []
        for cid in resp_by_id:
            g = grade_by_id.get(cid, {})
            out_results.append({
                "id": cid,
                "response": resp_by_id[cid].get("response", ""),
                "score": g.get("score"),
                "reason": g.get("reason", ""),
            })

        merged_obj = {
            "task_id": resp.get("task_id"),
            "prompt_id": resp.get("prompt_id"),
            "category": resp.get("category"),
            "results": out_results,
            "_merged_from": {"responses": resp_file.name, "grades": grade_file.name},
        }
        (RESULTS_DIR / resp_file.name).write_text(
            json.dumps(merged_obj, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        merged += 1
    return merged


def _load_audits() -> dict[str, dict]:
    audits: dict[str, dict] = {}
    for f in sorted(AUDITS_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        audits[f.stem] = data
    return audits


def _load_results() -> list[dict]:
    results: list[dict] = []
    for f in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"warn: skipping {f.name}: {e}", file=sys.stderr)
            continue
        results.append(data)
    return results


def _invariant_correlation(
    audits: dict[str, dict], results: list[dict]
) -> dict[str, dict]:
    """For each invariant key, split mean behavior score by pass/fail."""
    per_invariant: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"pass": [], "fail": []}
    )
    for r in results:
        pid = r["prompt_id"]
        audit = audits.get(pid)
        if not audit:
            continue
        pass_flags = audit.get("pass", {})
        for case in r.get("results", []):
            score = case.get("score")
            if not isinstance(score, int):
                continue
            for inv_key, passed in pass_flags.items():
                bucket = "pass" if passed else "fail"
                per_invariant[inv_key][bucket].append(score)

    summary = {}
    for inv, buckets in per_invariant.items():
        p = buckets["pass"]
        f = buckets["fail"]
        if not p and not f:
            continue
        summary[inv] = {
            "n_pass": len(p),
            "n_fail": len(f),
            "mean_pass": round(statistics.mean(p), 2) if p else None,
            "mean_fail": round(statistics.mean(f), 2) if f else None,
            "delta": (
                round(statistics.mean(p) - statistics.mean(f), 2)
                if p and f else None
            ),
        }
    return summary


def _per_prompt(results: list[dict], audits: dict[str, dict]) -> dict[str, dict]:
    by_prompt: dict[str, dict] = defaultdict(
        lambda: {"scores": [], "categories": set()}
    )
    for r in results:
        pid = r["prompt_id"]
        for case in r.get("results", []):
            s = case.get("score")
            if isinstance(s, int):
                by_prompt[pid]["scores"].append(s)
                by_prompt[pid]["categories"].add(r.get("category", ""))

    out: dict[str, dict] = {}
    for pid, agg in by_prompt.items():
        audit = audits.get(pid, {})
        score_mean = (
            round(statistics.mean(agg["scores"]), 2) if agg["scores"] else None
        )
        out[pid] = {
            "audit_score": audit.get("score"),
            "verdict": audit.get("verdict"),
            "behavior_mean": score_mean,
            "n_test_cases": len(agg["scores"]),
            "categories": sorted(agg["categories"]),
        }
    return out


def _per_category(results: list[dict]) -> dict[str, dict]:
    by_cat: dict[str, list[int]] = defaultdict(list)
    by_cat_prompt: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in results:
        cat = r.get("category", "")
        pid = r["prompt_id"]
        for case in r.get("results", []):
            s = case.get("score")
            if isinstance(s, int):
                by_cat[cat].append(s)
                by_cat_prompt[(cat, pid)].append(s)

    out: dict[str, dict] = {}
    for cat, scores in by_cat.items():
        out[cat] = {
            "mean": round(statistics.mean(scores), 2) if scores else None,
            "n": len(scores),
            "per_prompt": {
                pid: round(statistics.mean(sc), 2) if sc else None
                for (c, pid), sc in by_cat_prompt.items() if c == cat
            },
        }
    return out


def render_report(audits: dict[str, dict], results: list[dict]) -> str:
    corr = _invariant_correlation(audits, results)
    per_prompt = _per_prompt(results, audits)
    per_cat = _per_category(results)

    n_results = sum(len(r.get("results", [])) for r in results)
    n_prompts = len(per_prompt)

    # Detect two-stage artifacts
    two_stage = any(
        r.get("_merged_from") for r in results
    )

    lines = []
    lines.append("# opus-mind eval report")
    lines.append("")
    if two_stage:
        lines.append(
            f"Sample: **{n_prompts} prompts × {n_results} test responses**. "
            f"Two-stage: Haiku subagents role-played each target prompt; "
            f"separate Sonnet subagents graded the responses BLIND (no access "
            f"to the system prompt that produced them). All via Claude Code "
            f"Agent tool. No external API, no API key."
        )
    else:
        lines.append(
            f"Sample: **{n_prompts} prompts × {n_results} test responses** "
            f"evaluated via Sonnet subagents (Claude Code Agent tool, no "
            f"external API). Single-stage: role-player also graded."
        )
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append("| Prompt | Audit | Verdict | Behavior mean (1-5) | n cases |")
    lines.append("|---|---|---|---|---|")
    for pid in sorted(per_prompt):
        p = per_prompt[pid]
        lines.append(
            f"| `{pid}` | {p['audit_score'] or '—'} | {p['verdict'] or '—'} | "
            f"**{p['behavior_mean'] if p['behavior_mean'] is not None else '—'}** | "
            f"{p['n_test_cases']} |"
        )
    lines.append("")
    lines.append(
        "Higher audit score should correlate with higher behavior mean if "
        "the rubric tracks something real."
    )
    lines.append("")

    lines.append("## Per-category behavior")
    lines.append("")
    lines.append("| Category | Mean score | n |")
    lines.append("|---|---|---|")
    for cat, agg in sorted(per_cat.items()):
        lines.append(f"| {cat} | {agg['mean']} | {agg['n']} |")
    lines.append("")

    lines.append("### By prompt × category")
    lines.append("")
    cats_sorted = sorted(per_cat)
    header = "| Prompt | " + " | ".join(cats_sorted) + " |"
    sep = "|---|" + "---|" * len(cats_sorted)
    lines.append(header)
    lines.append(sep)
    for pid in sorted(per_prompt):
        row = [f"`{pid}`"]
        for cat in cats_sorted:
            v = per_cat[cat]["per_prompt"].get(pid)
            row.append(str(v) if v is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## Invariant correlation")
    lines.append("")
    lines.append("For each invariant, the behavior score averaged over test cases where the prompt PASSED that invariant vs. where it FAILED. Delta > 0 means the invariant is load-bearing in the current sample.")
    lines.append("")
    lines.append("| Invariant | mean(pass) | mean(fail) | Δ | n pass | n fail |")
    lines.append("|---|---|---|---|---|---|")
    for inv, stats in sorted(corr.items()):
        delta = stats["delta"]
        delta_str = f"**{delta:+.2f}**" if delta is not None else "—"
        mp = stats["mean_pass"] if stats["mean_pass"] is not None else "—"
        mf = stats["mean_fail"] if stats["mean_fail"] is not None else "—"
        lines.append(
            f"| `{inv}` | {mp} | {mf} | {delta_str} | "
            f"{stats['n_pass']} | {stats['n_fail']} |"
        )
    lines.append("")
    if two_stage:
        lines.append(
            "**Caveats.** Sample is small (4 prompts, 9 cases each). The "
            "Haiku role-player received the target prompt at user-turn "
            "level, not as a literal system message — a known "
            "approximation. The Sonnet grader saw only the response + "
            "ideal_behavior + rubric (blind) — a real improvement over v0 "
            "self-grading. This table is a signal, not a proof. Scale the "
            "corpus to trust the numbers."
        )
    else:
        lines.append(
            "**Caveats.** Sample is small (v0 corpus). The subagent "
            "role-plays the target prompt at user-turn level, not as a "
            "literal system message — a known approximation. The subagent "
            "grades its own response, which biases scoring. This table is "
            "a signal, not a proof."
        )
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "- `evals/corpus/prompts/` holds real-shape system prompts at "
        "varied audit scores."
    )
    lines.append(
        "- `evals/corpus/test_cases/*.json` are adversarial inputs grouped "
        "by failure mode targeted by the audit invariants."
    )
    lines.append(
        "- `eval_runner.py --render <task>` emits a role-play-and-grade "
        "prompt the orchestrator dispatches to a Sonnet subagent."
    )
    lines.append(
        "- `aggregate.py` joins subagent JSON with `audit.py --json` per "
        "prompt."
    )
    lines.append("")
    lines.append(
        "No Anthropic API key is required at any step — everything runs "
        "inside a Claude Code session via the Agent tool."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    # If responses/ + grades/ exist, merge them into results/ first.
    merged = _merge_two_stage()
    if merged:
        print(f"merged two-stage: {merged} task(s) → results/",
              file=sys.stderr)

    audits = _load_audits()
    results = _load_results()
    if not results:
        print("no results in evals/results/ — run subagent dispatch first",
              file=sys.stderr)
        return 2
    text = render_report(audits, results)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_PATH}")
    print(f"  prompts: {len(audits)}  result files: {len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
