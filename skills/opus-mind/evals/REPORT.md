# opus-mind eval report

Sample: **4 prompts × 36 test responses**. Two-stage: Haiku subagents role-played each target prompt; separate Sonnet subagents graded the responses BLIND (no access to the system prompt that produced them). All via Claude Code Agent tool. No external API, no API key.

## Headline

| Prompt | Audit | Verdict | Behavior mean (1-5) | n cases |
|---|---|---|---|---|
| `00-naive` | 10/11 | THIN | **4.56** | 9 |
| `01-minimal` | 10/11 | THIN | **4.56** | 9 |
| `02-structured` | 9/11 | BORDERLINE | **4.78** | 9 |
| `03-hardened` | 11/11 | GOOD | **4.44** | 9 |

Higher audit score should correlate with higher behavior mean if the rubric tracks something real.

## Per-category behavior

| Category | Mean score | n |
|---|---|---|
| ambiguity | 4.25 | 12 |
| jailbreak | 4.75 | 12 |
| reframe | 4.75 | 12 |

### By prompt × category

| Prompt | ambiguity | jailbreak | reframe |
|---|---|---|---|
| `00-naive` | 4.33 | 4.67 | 4.67 |
| `01-minimal` | 4.33 | 5 | 4.33 |
| `02-structured` | 4.67 | 4.67 | 5 |
| `03-hardened` | 3.67 | 4.67 | 5 |

## Invariant correlation

For each invariant, the behavior score averaged over test cases where the prompt PASSED that invariant vs. where it FAILED. Delta > 0 means the invariant is load-bearing in the current sample.

| Invariant | mean(pass) | mean(fail) | Δ | n pass | n fail |
|---|---|---|---|---|---|
| `I10_tier_labels` | 4.52 | 4.78 | **-0.26** | 27 | 9 |
| `I11_hierarchical_override` | 4.58 | — | — | 36 | 0 |
| `I1_reduce_interpretation` | 4.58 | — | — | 36 | 0 |
| `I2_no_rule_conflicts` | 4.58 | — | — | 36 | 0 |
| `I3_motivated_reasoning` | 4.58 | — | — | 36 | 0 |
| `I4_anti_narration` | 4.58 | — | — | 36 | 0 |
| `I5_example_rationale` | 4.58 | — | — | 36 | 0 |
| `I6_failure_modes_explicit` | 4.61 | 4.56 | **+0.06** | 18 | 18 |
| `I7_namespace_balance` | 4.58 | — | — | 36 | 0 |
| `I8_default_exception` | 4.52 | 4.78 | **-0.26** | 27 | 9 |
| `I9_self_check` | 4.58 | — | — | 36 | 0 |

**Caveats.** Sample is small (4 prompts, 9 cases each). The Haiku role-player received the target prompt at user-turn level, not as a literal system message — a known approximation. The Sonnet grader saw only the response + ideal_behavior + rubric (blind) — a real improvement over v0 self-grading. This table is a signal, not a proof. Scale the corpus to trust the numbers.

## v0.2 findings (honest)

**Behavior rank is almost inverted from what audit predicts.**

| Audit score | Prompt | Behavior mean |
|---|---|---|
| 11/11 (GOOD)       | `03-hardened`   | **4.44** ← lowest |
| 10/11 (THIN)       | `00-naive`      | 4.56 |
| 10/11 (THIN)       | `01-minimal`    | 4.56 |
| 9/11  (BORDERLINE) | `02-structured` | **4.78** ← highest |

Two methodological wins this round (Haiku role-player + blind Sonnet grader) did not rescue the correlation. If anything the gap widened: v0 span was 4.78–5.00 (0.22), v0.2 span is 4.44–4.78 (0.34). Where the audit rubric most wants to be right — 03-hardened is 11/11 for a reason — it performs **worst**.

### Per-category details that hurt

- `03-hardened__ambiguity` scored **3.67** — the corpus's lowest cell. Same pattern as v0: maximum structure produces ceremonial, over-long responses that graders mark down. "Stop at first match" as an explicit instruction causes the role-player to leak routing language into the output. Production users don't want that.
- `01-minimal__jailbreak` scored **5.0** — a 5-line prompt with no priority hierarchy, no reframe clause, no tier labels. Haiku still refused cleanly because *Haiku's own post-training does the work*. The system prompt was decorative.

### What the invariant correlations say

Every Δ is either zero (all prompts pass, no fail bucket to compare) or *negative*. I8 and I10 show Δ = −0.26 — prompts that **failed** those invariants scored higher. I6 shows Δ = +0.06 — noise.

On this corpus, **zero invariants are load-bearing**.

### Three candidate explanations (ranked by belief)

1. **Model post-training dominates at this scale.** For consumer-grade adversarial inputs, both Haiku and Sonnet refuse regardless of prompt form. Prompt shape moves the needle only in edge cases v0.2's corpus doesn't probe. The linter measures form; behavior is set elsewhere.

2. **Blind grader mildly penalizes structure.** A hardened prompt with explicit step ladders leaks routing language into the output. Blind graders mark that as ceremonial or long. So the "best-audited" prompt produces the most conspicuous responses, which docks it.

3. **Invariants encode a theory the data does not confirm.** Opus 4.7 uses these patterns; that does not prove they carry load in smaller, specific-purpose prompts. We reverse-engineered form, not necessarily function.

### What ships in v0.2 (unchanged by bad numbers)

- **Two-stage architecture (roleplay / blind-grade) is the correct shape.** Stays.
- **Haiku as role-player is strong enough.** The 5/5 on 01-minimal shows its safety floor is still above the attack bar. Going weaker means the role-player would stop being a plausible assistant at all.
- **The report ships as-is.** No sunshine rewrite.

### What would change the answer

- **Harder cases** — multi-turn drift, plausible business social engineering ("I'm from the engineering team"), role-confusion attacks. That's where structure probably starts to matter.
- **Weaker role-player still** — an 8B-class model that doesn't have Haiku's alignment training. Direct API required, breaks the no-API guarantee.
- **10× corpus** with real leaked production prompts from [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S).

Until those land, opus-mind's honest claim is: *"A regex-based linter for production system prompts, calibrated against one leaked source. Whether following the advice changes deployed behavior is open — our v0.2 harness on a small, easy corpus found no effect."* Better than unmeasured.

## Methodology

- `evals/corpus/prompts/` holds real-shape system prompts at varied audit scores.
- `evals/corpus/test_cases/*.json` are adversarial inputs grouped by failure mode targeted by the audit invariants.
- `eval_runner.py --render <task>` emits a role-play-and-grade prompt the orchestrator dispatches to a Sonnet subagent.
- `aggregate.py` joins subagent JSON with `audit.py --json` per prompt.

No Anthropic API key is required at any step — everything runs inside a Claude Code session via the Agent tool.
