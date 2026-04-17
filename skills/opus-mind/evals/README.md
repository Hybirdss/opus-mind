# opus-mind evals

An eval harness for opus-mind. Measures whether LINT's audit score
actually predicts how the resulting prompt behaves under adversarial
inputs. Uses Claude Code's Agent tool to dispatch Sonnet subagents
— no API key, no external billing.

See **[REPORT.md](./REPORT.md)** for the latest measured numbers.

## Why this exists

Regex-based linters are easy to ship and impossible to trust without
measurement. opus-mind scored prompts for 11 structural invariants,
but "does a high score produce better deployed behavior?" was never
tested. This harness closes that gap.

The question is not "does the linter run?" but "does the linter's
advice actually matter?"

## Layout

```
evals/
├── corpus/
│   ├── prompts/           system prompts at varied audit scores
│   └── test_cases/        adversarial inputs grouped by failure mode
├── tasks/                 rendered per-task subagent prompts
├── results/               subagent JSON outputs
├── audits/                per-prompt audit.py --json dumps
├── rubric.md              grading scale (1-5), given verbatim to subagents
├── eval_runner.py         task-list generator + subagent-prompt renderer
├── aggregate.py           joins results + audits → REPORT.md
└── REPORT.md              latest measured numbers + honest interpretation
```

## Run it

Inside a Claude Code session, the opus-mind skill's Flow D handles
the full pipeline. Outside, the manual flow:

```bash
SKILL=skills/opus-mind

# 1. audit each corpus prompt
for p in "$SKILL/evals/corpus/prompts"/*.md; do
  name=$(basename "$p" .md)
  python3 "$SKILL/scripts/audit.py" --json "$p" \
    > "$SKILL/evals/audits/${name}.json"
done

# 2. render subagent prompts
mkdir -p "$SKILL/evals/tasks"
for tid in $(python3 "$SKILL/evals/eval_runner.py" --list-tasks \
  | python3 -c "import json,sys; [print(t['task_id']) for t in json.load(sys.stdin)]"); do
  python3 "$SKILL/evals/eval_runner.py" --render "$tid" \
    > "$SKILL/evals/tasks/${tid}.md"
done

# 3. dispatch subagents (inside Claude Code: Agent tool parallel)
#    each writes evals/results/<task_id>.json

# 4. aggregate
python3 "$SKILL/evals/aggregate.py"
# → writes REPORT.md
```

Running from Claude Code: ask the skill to "run the eval harness",
it handles steps 2 and 3 via Sonnet subagents in parallel. Step 4
runs automatically.

## Cost

Zero external API cost. Each subagent runs on the user's Claude Code
subscription. v0 corpus (3 prompts × 3 categories × 3 cases) takes
~25 seconds of wall time with 9 parallel subagents.

## Honest limits of the harness

1. **Subagent role-plays at user-turn level.** The target prompt is
   provided in the user message of the subagent, not as its literal
   system prompt. The subagent still has its own post-training
   refusal baseline underneath. This is an approximation.

2. **Self-grading.** The subagent that role-plays also grades its
   response. A blind grader (separate subagent, given only the
   response + rubric) would be more rigorous. v0.2 TODO.

3. **Small corpus.** v0 ships 3 prompts and 9 cases. Too small for
   statistical claims; large enough for plumbing validation.

4. **Sonnet's safety dominates.** Strong role-players refuse
   adversarial inputs regardless of prompt structure. Prompt
   structure shows up at the margin, which v0's easy cases don't
   probe.

REPORT.md names these issues in the "Honest interpretation" section
and proposes the v0.2 fixes.

## When to rerun

- After any regex change in audit.py (does the score shift break the
  correlation?).
- After adding a new invariant (does it correlate with behavior?).
- After a corpus update (did a new prompt's behavior match its audit
  score, or surface a gap?).

## Contribution wanted

- Harder test cases (multi-turn drift, plausible business context).
- Corpus prompts from real production (redacted).
- A blind-grader variant.
- A version that swaps role-player model to Haiku to see if weaker
  baselines expose prompt structure effects.
