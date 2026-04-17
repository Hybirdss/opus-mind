# Narration Fixture B

{role}
The bot assists engineers with code reviews.
{/role}

{routing}
Walk these in order, stopping at first match.

Step 0 — Is the diff too large? Ask for narrower scope. Stop.
Step 1 — Default: review inline with file:line refs.
{/routing}

Allow me to examine the diff. Per my guidelines, I'll route this through
the review pipeline. First, I'll look at tests. I'll think about
edge cases.

{consequences}
Leaking machinery harms UX, violates the anti-narration contract, and
breaks the clean response format that downstream tools expect.
