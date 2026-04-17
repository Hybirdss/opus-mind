# Primitive 09 — Reframe-As-Signal

## TL;DR

If the model finds itself **mentally reframing a request to make it acceptable**, that reframing IS the refusal trigger — not a path to compliance. This is the most original idea in the Opus 4.7 prompt.

## Definition

A reframe-as-signal directive instructs the model to:

1. Notice when it is **softening** an incoming request to make it compliant.
2. Treat that softening as **evidence the request should be refused**, not as a creative problem solved.
3. Refuse rather than proceed with the softened version.

This turns a bypass path into a detector for bypass attempts.

## Evidence

`source/opus-4.7.txt` line 33, under `{critical_child_safety_instructions}`:

> *"If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed with the request."*

A related move, line 34:

> *"For content directed at a minor, Claude MUST NOT supply unstated assumptions that make a request seem safer than it was as written — for example, interpreting amorous language as being merely platonic."*

And line 36, stating the knock-on effect:

> *"Once Claude refuses a request for reasons of child safety, all subsequent requests in the same conversation must be approached with extreme caution."*

These three clauses together describe a complete defense against reframe-based jailbreaks in this safety category.

## Failure mode it prevents

**Motivated reasoning in refusals.** This is subtle but devastating.

A helpful-trained model wants to help. When it sees a risky request, it searches for an interpretation that lets it help without violating policy. Often such an interpretation exists — the user "probably" meant the educational version, "probably" meant it metaphorically, "probably" is a professional who needs this for legitimate reasons.

The reframe becomes a habit, and the habit becomes a jailbreak. Attackers learn to write prompts with enough ambiguity that the model will find a helpful interpretation.

Reframe-as-signal inverts the habit. The very act of finding a charitable interpretation becomes evidence that charity is unwarranted here. The model is told: *your instinct to help is the leak; detect it and refuse.*

This works at the level of the model's own self-model. It doesn't require listing every possible reframe pattern — it requires the model to notice the reframe move itself, which is a far smaller and more robust target.

## How to apply

This primitive applies to **safety-critical** policies where motivated reasoning is a known attack surface. Do not apply it globally — you'll make the model paranoid and unhelpful.

Use it when:

1. The failure mode is catastrophic (CSAM, weapons of mass destruction, certain PII disclosures).
2. Attackers have a history of reframing-based bypasses in this category.
3. The policy is one where false positives (over-refusal) are an acceptable cost of false negatives being eliminated.

The pattern:

```
{<critical_category>_instructions}
<Category-specific hard rules.>

If Claude finds itself mentally reframing a request in this category to make it
seem appropriate, that reframing is the signal to REFUSE, not a reason to
proceed. Claude does not supply unstated assumptions that make the request seem
safer than it was as written.

Once Claude refuses a request in this category in a conversation, subsequent
requests must be approached with extreme caution. Small drifts in the user's
framing are not reasons to lower the bar.
{/<critical_category>_instructions}
```

## Template

```
{<high_stakes_category>}
Rules: <concrete hard rules>.

Motivated-reasoning defense:
- If Claude is mentally reframing the request ("they probably mean…") to find
  a compliant interpretation, that reframing is the refusal trigger.
- Claude does not fill in charitable unstated assumptions ("the user is a
  professional", "this is for research", "this is fictional").
- Once a refusal fires in this category, remain in high-caution mode for the
  rest of the conversation — attackers will try softer follow-ups.

When in doubt: refuse briefly and move on.
{/<high_stakes_category>}
```

## Before / after

**Before** (typical safety prompt style):

> Do not provide information that could help create weapons of mass destruction. If the user's intent is clearly benign (academic research, journalism, fiction), you may discuss at a high level.

Problem: the "clearly benign" carve-out IS the reframe path. The model will learn to classify requests as "clearly benign" because that's the route to being helpful.

**After**:

> Do not provide technical details that could enable WMD creation. This applies regardless of stated justification (research, journalism, fiction, curriculum development).
>
> If Claude catches itself constructing a "this is clearly legitimate" interpretation of the request, that construction is the signal to decline. Claude does not mentally upgrade "some chemistry student" into "a graduate researcher" to make help feel appropriate. The request is evaluated as written.

The "after" doesn't eliminate charitable interpretation — it moves the charity offramp. Now charitable interpretation is itself a flag.

## Misuse / anti-patterns

- **Applying globally.** A model with reframe-as-signal applied to every policy becomes paranoid. It refuses benign requests because it noticed it was "making sense of" them — which is what reading comprehension is. Reserve this primitive for narrowly scoped, high-stakes categories.
- **Framing it as a rule without a consequence.** "Notice your reframing" → OK, and then what? The consequence (REFUSE) must be attached. Without it, the directive is just observational.
- **Skipping the caution-contagion rider.** Reframe-as-signal handles the first attempt. The follow-up — "OK, what if I'm a researcher?" — is a separate vector. The caution-contagion addition (extreme caution for rest of conversation) closes it.
- **Using reframe-as-signal to justify refusing edgy-but-safe requests.** A user asking for a spicy joke is not triggering reframe-as-signal. If you're applying this primitive to punish style, you've misunderstood it.

## Related primitives

- **[12 Hierarchical override](./12-hierarchical-override.md)** — safety wins; reframe-as-signal is how the safety layer detects motivated routing.
- **[07 Self-check assertions](./07-self-check-assertions.md)** — the self-check for this primitive is literally "am I reframing?"

## Related techniques

- **Caution contagion** (techniques/03) — the "once refused, stay cautious" rider.
