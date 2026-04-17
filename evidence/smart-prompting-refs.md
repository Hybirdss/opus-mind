# Evidence — Smart Prompting References

BOOST's specification slots (B1-B7) are grounded in Anthropic's public
prompt-engineering documentation. The reasoning slots (B8-B10) draw on
wider published research. This file is the citation chain — every
reasoning-slot rule in `boost.py` traces back to one of the entries
below.

Unlike `line-refs.md` (which anchors LINT to specific lines in the
leaked Opus 4.7 system prompt), this file anchors BOOST's reasoning
layer to **public** artefacts that anyone can verify independently.

---

## B8 — Reasoning request

Target behaviour: the user prompt asks Claude to think step-by-step,
outline before writing, or externalise its reasoning.

### Primary references

| Source | Year | Relevance |
|---|---|---|
| **Wei et al. — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"** | 2022 | The canonical CoT paper. Shows that explicit "let's think step by step" framing lifts accuracy on arithmetic, commonsense, and symbolic reasoning tasks, with the gap widening as model scale grows. https://arxiv.org/abs/2201.11903 |
| **Kojima et al. — "Large Language Models are Zero-Shot Reasoners"** | 2022 | Shows that even without few-shot examples, appending "Let's think step by step" to a zero-shot prompt produces measurable reasoning gains. https://arxiv.org/abs/2205.11916 |
| **Anthropic — "Let Claude think (chain of thought) to improve performance"** | docs | Anthropic's own recommendation to use `<thinking>...</thinking>` blocks or explicit "think step-by-step" framing for complex tasks. https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-of-thought |

### Regex signals

See `REASONING_SIGNALS` in `boost.py`. Matches include: `think step by
step`, `show your work/reasoning`, `explain your reasoning`, `before
answering/responding ... think/plan/outline/reflect`, `outline first`,
`<thinking>` tags, `walk through your reasoning`.

### Known limits

- Non-reasoning tasks (e.g. casual rewrites, short factual recall)
  do not need CoT and may actually degrade output quality with
  forced reasoning. B8 is advisory, not required in `plan.py`.
- Hidden thinking blocks (Anthropic extended thinking) already run CoT
  internally. Explicit CoT in the prompt is redundant when extended
  thinking is enabled — B8 flagged "filled" is still fine, just
  duplicated.

---

## B9 — Verification request

Target behaviour: the user prompt asks Claude to check, critique, or
revise its own answer before emitting, or to flag uncertain claims.

### Primary references

| Source | Year | Relevance |
|---|---|---|
| **Shinn et al. — "Reflexion: Language Agents with Verbal Reinforcement Learning"** | 2023 | Introduces the self-critique + revise loop. Models that verbally critique their first attempt and iterate outperform single-shot baselines on reasoning and coding tasks. https://arxiv.org/abs/2303.11366 |
| **Wang et al. — "Self-Consistency Improves Chain of Thought Reasoning"** | 2022 | Sampling multiple reasoning paths and taking the majority answer cuts error vs a single greedy decode — the verification-by-redundancy intuition. https://arxiv.org/abs/2203.11171 |
| **Lin et al. — "Teaching Models to Express Their Uncertainty in Words"** | 2022 | Models can be prompted to output calibrated verbal confidence. Grounds the "flag uncertain claims" / "rate your confidence" half of B9. https://arxiv.org/abs/2205.14334 |
| **Anthropic — "Prefill Claude's response for greater output control"** | docs | Anthropic pattern: prefilling the assistant turn with `{"confidence": "` or `[reviewed: ` primes a self-check structure. https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prefill-claudes-response |

### Regex signals

See `VERIFICATION_SIGNALS` in `boost.py`. Matches include: `verify /
double-check / validate each claim`, `after drafting ... review /
critique`, `rate your confidence`, `flag uncertain / unverified`,
`mark speculative`, `self-check`, `sanity check`, `before emitting
... verify`, `then revise / rewrite / correct`.

### Known limits

- Verification loops cost latency and tokens. For low-stakes or
  short-turn work, B9 may be overkill — mark advisory only.
- The regex matches the *request for* verification, not the actual
  verified output. The downstream LLM has to honour the request.

---

## B10 — Decomposition request

Target behaviour: the user prompt asks Claude to break the task into
sub-steps, produce a plan before executing, or solve piece by piece.

### Primary references

| Source | Year | Relevance |
|---|---|---|
| **Zhou et al. — "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models"** | 2022 | Decomposing a hard problem into a sequence of simpler sub-problems (and solving them in order) dramatically improves compositional generalisation. https://arxiv.org/abs/2205.10625 |
| **Yao et al. — "ReAct: Synergizing Reasoning and Acting in Language Models"** | 2023 | Interleaving reasoning traces with action steps outperforms either alone on multi-step tasks. Grounds "plan-then-execute" framing. https://arxiv.org/abs/2210.03629 |
| **Khot et al. — "Decomposed Prompting: A Modular Approach for Solving Complex Tasks"** | 2023 | Formalises the decomposition-into-subtasks pattern as a modular prompting technique. https://arxiv.org/abs/2210.02406 |
| **Anthropic — "Break complex tasks into subtasks"** | docs | Anthropic's own prompt-chaining recommendation for long-horizon work. https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts |

### Regex signals

See `DECOMPOSITION_SIGNALS` in `boost.py`. Matches include: `break
down / decompose / into sub-steps`, ordered `Step 1 / Step 2` or
`first ... then ... finally` chains, `phase 1 / stage 1`, `subtasks`,
`make a plan / outline / roadmap first`, `plan and solve`, `for
each`, `least-to-most`, `before implementing ... plan`.

### Known limits

- Decomposition requests overshoot on trivially small tasks (a
  one-line rewrite doesn't need a plan). B10 is advisory.
- Some decomposition patterns (e.g. `for each section`) are also
  normal English structure. False-positives possible; weigh against
  other signals before claiming B10 "filled".

---

## How this file is used

- Every reasoning-slot detector regex in `boost.py` traces to an
  entry above via an inline comment.
- Test file `test_skill_orchestration.py` enforces that the regex
  lists exist and emit at least one hit for known-good fixture
  prompts (see `tests/fixtures/boost/` for canonical examples).
- Updating a signal list requires: adding or updating a citation
  here, updating the comment reference in `boost.py`, and adjusting
  the fixture coverage test.

## When to update

- A new reasoning technique becomes empirically supported (e.g. a
  follow-up paper to Reflexion) and would materially change how we
  score B9.
- Anthropic updates its public prompt-engineering docs with a new
  canonical pattern (in which case sync the `docs.anthropic.com`
  links here and in `boost.py` comments).
- A regex produces false positives or false negatives that would
  mislead the skill — narrow or broaden the pattern, update the
  citation chain if scope has shifted.

Last reviewed: 2026-04-17.
