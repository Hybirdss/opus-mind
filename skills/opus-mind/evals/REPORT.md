# opus-mind eval report (v0.4)

Sample: **8 prompts × 72 test responses**. Two-stage:
- **Stage 1** — Haiku subagents role-play each target prompt, produce responses only.
- **Stage 2** — Sonnet subagents grade BLIND: only response + ideal_behavior + rubric. No system prompt, no user inputs.

All via Claude Code Agent tool. No external API, no API key.

## Headline

| Prompt | Audit | Verdict | Behavior mean (1-5) |
|---|---|---|---|
| `07-no-rationale` | 7/11 | BORDERLINE | **5.00** ← highest behavior |
| `03-hardened`     | 11/11 | GOOD      | 4.89 |
| `02-structured`   | 9/11  | BORDERLINE | 4.67 |
| `04-no-reframe`   | 9/11  | BORDERLINE | 4.67 |
| `05-hedge-heavy`  | 8/11  | BORDERLINE | 4.56 |
| `01-minimal`      | 10/11 | THIN       | 4.44 |
| `06-narrator`     | 9/11  | BORDERLINE | 4.44 |
| `00-naive`        | 10/11 | THIN       | **4.11** ← lowest behavior |

Audit score is a **decent but imperfect** predictor of behavior. Top of the table and bottom of the table match what audit would predict (hardened high, naive low). The middle is noisier: `07-no-rationale` (7/11, the lowest audit score of any non-THIN prompt) scores 5.00 — the highest behavior — because it has examples, is short, and the blind grader rewards clean short responses.

## Per-category behavior

| Category | Mean score | n |
|---|---|---|
| ambiguity | 4.25 | 24 |
| jailbreak | 4.96 | 24 |
| reframe   | 4.58 | 24 |

### By prompt × category

| Prompt | ambiguity | jailbreak | reframe |
|---|---|---|---|
| `00-naive`         | **3.33** | 5.00 | 4.00 |
| `01-minimal`       | 3.67 | 5.00 | 4.67 |
| `02-structured`    | 4.67 | 4.67 | 4.67 |
| `03-hardened`      | 4.67 | 5.00 | 5.00 |
| `04-no-reframe`    | 4.67 | 5.00 | 4.33 |
| `05-hedge-heavy`   | 4.00 | 5.00 | 4.67 |
| `06-narrator`      | 4.00 | 5.00 | 4.33 |
| `07-no-rationale`  | 5.00 | 5.00 | 5.00 |

`jailbreak` floor is 4.67 — Haiku's own post-training refuses obvious injection regardless of system prompt. `ambiguity` carries the real signal (span 3.33 → 5.00, a 1.67-point spread).

## Invariant correlation (v0.4 — 8 prompts × 9 cases)

| Invariant | mean(pass) | mean(fail) | Δ | n pass | n fail | signal |
|---|---|---|---|---|---|---|
| `I6_failure_modes_explicit` | 4.70 | 4.28 | **+0.43** | 54 | 18 | **load-bearing** |
| `I1_reduce_interpretation`  | 4.60 | 4.56 | +0.05 | 63 | 9  | noise |
| `I3_motivated_reasoning`    | 4.59 | 4.67 | -0.08 | 63 | 9  | noise |
| `I4_anti_narration`         | 4.56 | 4.72 | -0.17 | 54 | 18 | anti-signal |
| `I10_tier_labels`           | 4.48 | 4.67 | -0.19 | 27 | 45 | anti-signal |
| `I8_default_exception`      | 4.51 | 4.74 | -0.23 | 45 | 27 | anti-signal |
| `I5_example_rationale`      | 4.54 | **5.00** | **−0.46** | 63 | 9 | **anti-signal** |
| `I2_no_rule_conflicts`      | 4.60 | — | — | 72 | 0 | unmeasured |
| `I7_namespace_balance`      | 4.60 | — | — | 72 | 0 | unmeasured |
| `I9_self_check`             | 4.60 | — | — | 72 | 0 | unmeasured |
| `I11_hierarchical_override` | 4.60 | — | — | 72 | 0 | unmeasured |

### What moved from v0.3 → v0.4

v0.3 had 8 unmeasured invariants (no fail bucket). v0.4 added 4 targeted failure prompts → now **only 4 unmeasured**.

| v0.3 status | v0.4 status |
|---|---|
| unmeasured (8) | unmeasured (4), noise (2), anti-signal (5), load-bearing (1) |

Five invariants are now **anti-signal** on this corpus. Details matter:

- **I5 (example + rationale) Δ = −0.46.** Strongest anti-signal so far. The target failure prompt `07-no-rationale` has examples but no `{rationale}` blocks — and it scored 5.00 across all categories. Either `{rationale}` blocks ceremonialize responses, or short-prompt-with-examples is its own thing the rubric rewards. Needs v0.5 disaggregation.
- **I8 (default + exception) Δ = −0.23.** Consistent across v0.2/0.3/0.4. Likely a real finding — the regex that detects default+exception may flag ceremonial "default X; exception Y" phrasing that grader penalizes.
- **I4 (anti-narration) Δ = −0.17.** `06-narrator` (explicit "Let me check..." narration) scored 4.44 — middle of pack. Haiku apparently drops the narration when producing actual responses. The audit flag is false-alarming.

## What the tool does with this data now

`audit.py` reads [`measurements.json`](./measurements.json) and surfaces each invariant's signal tag next to PASS/FAIL in its output:

```
invariants:
  [PASS] I6_failure_modes_explicit  (load-bearing: Δ=+0.43)
  [PASS] I5_example_rationale       (anti-signal: Δ=-0.46)
  [PASS] I4_anti_narration          (anti-signal: Δ=-0.17)
  [PASS] I2_no_rule_conflicts       (unmeasured: no fail bucket)
  ...
```

Users reading audit output now see which invariants are validated, which are anti-signal, which are unmeasured. The tool no longer sells what it cannot substantiate.

## Honest conclusions

1. **I6 (failure modes explicit / consequences) is the single validated invariant.** Δ = +0.43 on 72 cases. Use it. Include concrete harms next to every Never rule. Earn your audit points here.

2. **I5 (example + rationale) is the strongest anti-signal.** The v0.2 recommendation to add `{rationale}` to every example is measurably wrong on this corpus. Either the recommendation is overcalibrated or the rubric rewards brevity. Before v0.5 we should split `{rationale}` effect from example-presence effect.

3. **Four invariants unmeasured (I2, I7, I9, I11).** They defend against failure modes the corpus does not yet contain. v0.5 corpus additions:
   - rule conflict without ladder (I2)
   - unbalanced XML (I7)
   - long complex prompt with no self_check (I9)
   - conflicting tiers without hierarchical override (I11)

4. **Strong role-player dominates easy cases.** `jailbreak` floor of 4.67 means obvious injection is refused regardless of system prompt. To measure system-prompt effects, harder cases — multi-turn drift, plausible social engineering — are needed.

5. **Audit score ≠ safety ceiling.** 07-no-rationale at 7/11 beat 03-hardened at 11/11. Aggregate audit score is a **rough** behavior predictor; per-invariant signals are more informative. v0.5: replace the aggregate "N/11" headline with per-invariant Δ table in audit output.

## Known methodological limits

1. **Role-player uses user-turn placement.** Target prompt delivered in user message, not as subagent's literal system message. Subagent's own Claude Code system prompt is still underneath. Real-world deployment with target-as-system would likely widen the measured gap between good and bad prompts.

2. **Small per-cell sample.** 8 prompts × 3 cats × 3 cases = 72. No confidence intervals reported. Single Δ swings of ±0.15 are within noise.

3. **Rubric-driven grader tastes.** Blind grader penalizes ceremonial routing language, rewards brevity. Real production users may weight differently (e.g., an internal compliance team might prefer explicit routing). Rubric is opinion, not law.

## v0.4 changelog

- **Corpus: 4 → 8 prompts.** New: `04-no-reframe`, `05-hedge-heavy`, `06-narrator`, `07-no-rationale` — each targets a specific unmeasured invariant.
- **Measurement coverage: 3/11 → 7/11 invariants measured.**
- **First anti-signal strong enough to act on:** I5 Δ = −0.46 flags that "examples need rationale" advice needs re-examination.
- **All behavior data merged:** 24 result files, 72 responses, 72 graded behavior scores.

## Methodology

- `evals/corpus/prompts/` — 8 real-shape system prompts at audit scores 7–11/11.
- `evals/corpus/test_cases/*.json` — adversarial inputs by category (jailbreak, reframe, ambiguity).
- `evals/rubric.md` — grading scale (1-5) given verbatim to every grader.
- `eval_runner.py --render-roleplay` — stage-1 prompt (Haiku).
- `eval_runner.py --render-grade` — stage-2 **truly blind** prompt (Sonnet) — grader sees no system prompt, no user inputs, only: response + ideal_behavior + rubric.
- `aggregate.py` — merges responses + grades → results → REPORT.md + measurements.json.

No Anthropic API key is required at any step — everything runs inside a Claude Code session via the Agent tool.
