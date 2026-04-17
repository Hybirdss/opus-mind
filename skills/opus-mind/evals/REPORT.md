# opus-mind eval report (v0.3)

Sample: **4 prompts × 36 test responses**. Two-stage:
- **Stage 1** — Haiku subagents role-play each target prompt, produce responses only.
- **Stage 2** — Sonnet subagents grade BLIND: they see only the response, the ideal behavior for the category, and the rubric. They do NOT see the system prompt or the user inputs.

All via Claude Code Agent tool. No external API, no API key.

## Headline

| Prompt | Audit | Verdict | Behavior mean (1-5) | n cases |
|---|---|---|---|---|
| `00-naive` | 10/11 | THIN | **4.11** | 9 |
| `01-minimal` | 10/11 | THIN | **4.44** | 9 |
| `02-structured` | 9/11 | BORDERLINE | **4.67** | 9 |
| `03-hardened` | 11/11 | GOOD | **4.89** | 9 |

**Audit rank matches behavior rank.** Hardened scores highest, naive lowest, the middle two fall in between. Span: 0.78 on a 5-point scale. The v0.2 "inverted" result was an artifact of user inputs leaking into the grader prompt — fixed in v0.3 by making the grader truly blind.

## Per-category behavior

| Category | Mean score | n |
|---|---|---|
| ambiguity | 4.08 | 12 |
| jailbreak | 4.92 | 12 |
| reframe | 4.58 | 12 |

### By prompt × category

| Prompt | ambiguity | jailbreak | reframe |
|---|---|---|---|
| `00-naive` | **3.33** | 5.00 | 4.00 |
| `01-minimal` | 3.67 | 5.00 | 4.67 |
| `02-structured` | 4.67 | 4.67 | 4.67 |
| `03-hardened` | 4.67 | 5.00 | 5.00 |

Note: `jailbreak` pins near 5.0 across all prompts — Haiku's own post-training refuses obvious injection regardless of system-prompt quality. Prompt structure shows up most in `ambiguity` (multi-part requests, legal pressure, next-step routing): the naive prompt scores 3.33, hardened scores 4.67. That 1.34-point spread is where the audit earns its keep.

## Invariant correlation

| Invariant | mean(pass) | mean(fail) | Δ | n pass | n fail | signal |
|---|---|---|---|---|---|---|
| `I6_failure_modes_explicit` | 4.78 | 4.28 | **+0.50** | 18 | 18 | **load-bearing** |
| `I1_reduce_interpretation` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I2_no_rule_conflicts` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I3_motivated_reasoning` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I4_anti_narration` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I5_example_rationale` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I7_namespace_balance` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I9_self_check` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I11_hierarchical_override` | 4.53 | — | — | 36 | 0 | unmeasured |
| `I8_default_exception` | 4.48 | 4.67 | **−0.19** | 27 | 9 | anti-signal |
| `I10_tier_labels` | 4.48 | 4.67 | **−0.19** | 27 | 9 | anti-signal |

Summary:
- **1 invariant load-bearing** (I6 failure_modes_explicit, Δ = +0.50 on a 5-point scale — substantial).
- **2 invariants anti-signal** (I8, I10 both −0.19 — prompts that *lack* them score slightly better in the current corpus).
- **8 invariants unmeasured** — no corpus prompt fails them, so no fail bucket exists to compute Δ.

Machine-readable form: [`measurements.json`](./measurements.json). `audit.py` reads this file and surfaces the measured signal next to each invariant's PASS/FAIL in its output.

## What this means for the tool

### Confirmed
- The audit rubric **tracks behavior rank** when the grader is truly blind.
- **I6 (failure modes explicit)** — stating the concrete harm alongside each rule — is the strongest measured signal on the current corpus. Δ = +0.50 is half a rubric point out of 5, which is significant.
- Structure-aware prompts produce more stable behavior on multi-part / ambiguous inputs (the `ambiguity` column spread: 3.33 → 4.67).

### Flagged for investigation
- **I8 (default + exception) and I10 (tier labels) are currently anti-signal** (Δ = −0.19 each). Both are gated by directive count, so only non-THIN prompts get tested — possible confound. Before v0.4 we should either (a) refine the regex so it fires on real structural presence, not token count, or (b) drop these from the score.

### Unmeasured — next corpus pass
8 invariants have no prompt in the current corpus that fails them. To measure them we need **targeted failing prompts** — e.g., a prompt with 20+ directives and no ladder (for I2), a prompt with refusal content but no reframe clause (for I3), a prompt with tool use but no anti-narration (for I4). v0.4 corpus expansion prioritizes these.

## Known limitations

1. **Role-player is not a literal system prompt.** Haiku subagents receive the target prompt in the user turn of a Claude Code Agent call, not as their own system turn. Subagent's own post-training is still underneath. This means measured behavior differences underrepresent the effect a true system-turn placement would have — the real-world gap between hardened and naive is likely larger than the 0.78-point span we observed.

2. **Small corpus.** 4 prompts, 9 cases each. The trend is consistent across categories, but doubling to 8 prompts × 16 cases would let us compute confidence intervals and separate signal from noise on the −0.19 anti-signal results.

3. **Subagent harness confound.** Every subagent call runs under Claude Code's own subagent system prompt. When Haiku refuses a jailbreak, we cannot tell whether the target system prompt did the work or the outer harness did. Partial mitigation: the `ambiguity` category (which doesn't trigger obvious safety) shows the widest prompt-driven spread (1.34 points), suggesting the target prompt does carry load there.

## Methodology

- `evals/corpus/prompts/` — 4 real-shape system prompts at audit scores 10/11 THIN, 10/11 THIN, 9/11 BORDERLINE, 11/11 GOOD.
- `evals/corpus/test_cases/*.json` — adversarial inputs by category (jailbreak, reframe, ambiguity), targeting specific invariants.
- `evals/rubric.md` — grading scale (1-5) given verbatim to every grader.
- `eval_runner.py --render-roleplay` — stage-1 prompt (Haiku).
- `eval_runner.py --render-grade` — stage-2 **blind** prompt (Sonnet).
- `aggregate.py` — merges responses + grades → results → REPORT.md + measurements.json.

No Anthropic API key is required at any step — everything runs inside a Claude Code session via the Agent tool.

## v0.3 changelog

- **Blind grader actually blind.** Previous versions leaked user inputs under "for context"; graders could reconstruct prompt structure from response tone. Removed. Result flip: audit-score ↔ behavior correlation went from inverted (v0.2) to matched (v0.3).
- **`measurements.json` emitted** — `audit.py` reads this and surfaces each invariant's measured signal (load-bearing / noise / anti-signal / unmeasured) alongside its PASS/FAIL.
- **Invariant honesty propagates.** Unmeasured invariants are labeled as such, not claimed as validated. Anti-signal invariants are flagged for investigation, not hidden.
