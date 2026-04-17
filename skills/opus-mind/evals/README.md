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
│   ├── prompts/              system prompts at varied audit scores
│   └── test_cases/           adversarial inputs grouped by failure mode
├── tasks_roleplay/           stage-1 subagent prompts (Haiku role-players)
├── responses/                stage-1 outputs (responses only, no grades)
├── tasks_grade/              stage-2 blind-grader prompts (Sonnet)
├── grades/                   stage-2 outputs (scores + reasons)
├── results/                  merged responses + grades (final)
├── audits/                   per-prompt audit.py --json dumps
├── rubric.md                 grading scale (1-5), given verbatim to graders
├── eval_runner.py            task-list + prompt renderers
│                             (--render-roleplay / --render-grade)
├── aggregate.py              merge two stages → REPORT.md
└── REPORT.md                 latest measured numbers + honest interpretation
```

## Run it

Inside a Claude Code session, the opus-mind skill's Flow D handles
the full pipeline. v0.2 splits the work across two subagent stages
to remove self-grading bias.

```bash
SKILL=skills/opus-mind

# 1. audit each corpus prompt + render stage-1 tasks
opus-mind eval audit-corpus
opus-mind eval prepare-tasks

# 2. STAGE 1 — role-play (Haiku subagent per task, parallel)
#    each writes evals/responses/<task_id>.json

# 3. STAGE 2 — blind grade
#    render grade prompts from the responses
for f in "$SKILL/evals/responses"/*.json; do
  tid=$(basename "$f" .json)
  opus-mind eval render-grade "$tid" "$f" \
    > "$SKILL/evals/tasks_grade/${tid}.md"
done
#    Sonnet subagent per task, parallel
#    each writes evals/grades/<task_id>.json

# 4. aggregate (merges responses + grades → results → REPORT.md)
opus-mind eval aggregate
```

The grader does NOT see the system prompt that produced the response
— this is what makes the grading blind.

Running from Claude Code: ask the skill to "run the eval harness",
it handles stages 1-3 via parallel subagents. Stage 4 runs as a
bash step.

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
