# Technique 01 — Force Tool Call

## TL;DR

Declare a class of queries where tool use is mandatory, and strip out the "I think I know this" fallback. Category membership wins over prior-knowledge confidence — the model searches because the rule says it must, not because it feels uncertain.

## Problem

Models trained on their own priors answer factual questions directly. Under pressure (casual queries, confident-feeling topics), they skip the search tool even when the fact has changed since training.

## The move

Declare a **class of queries** where tool use is mandatory. Remove the "I think I know this" path.

## Evidence

the source lines 4–6, at the very top of the claude_behavior section:

> *"Claude has the web_search tool. For any factual question about the present-day world, Claude must search before answering. Claude's confidence on topics is not an excuse to skip search. Present-day facts like who holds a role, what something costs, whether a law still applies, and what's newest in a category cannot come from training data."*

Note the three distinct moves in this short passage:

1. **Naming the category**: "any factual question about the present-day world."
2. **Removing the exception**: "Claude's confidence on topics is not an excuse to skip search."
3. **Stating the reason**: "cannot come from training data."

Line 833 repeats it in even stronger form:

> *"Claude searches for any present-day factual question before answering, regardless of confidence."*

## How to apply

```
{search_first_<domain>}
For any <specific class> query, Claude calls <tool> before answering.

This applies regardless of whether Claude believes it already knows the answer.
Training-era knowledge is stale for <this class of facts>. Search first,
reconcile with priors second.

Claude does not announce the search ("Let me search…") — it searches silently
and answers with the result. (See anti-narration, primitive 08.)
{/search_first_<domain>}
```

## Example — from news search to stock prices

**Before:**

> Use the search tool when you need current information.

Model behavior: stays silent on "what's the S&P 500 today", answers from 2024 training data, says "I can check the web if you'd like."

**After:**

```
{present_day_facts}
For any query about the current state of the world — prices, index levels,
office holders, legal status, product availability, stock quotes, sports scores
from the last week — Claude calls web_search before answering.

Training knowledge is stale for these categories. Claude searches regardless
of how confident it feels.

Do not announce the search. Emit the answer with the result.
{/present_day_facts}
```

Now: "what's the S&P 500 today" triggers a silent search and a numeric answer. No "I can check if you'd like" offer — the check happens.

## Misuse

- **Apply to stable-knowledge queries.** "What's 2+2" does not need a search. Force-tool-call only on the categories where training data is known to be stale.
- **Forget to pair with anti-narration.** If you force the tool call but allow narration, the product feels talky. "Let me search… OK, searching now… found it…"
- **Force a tool call where no tool is available.** The model can't search if there's no search tool. Confirm the capability exists before forcing use.
