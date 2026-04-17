# Hedges Fixture

{role}
The bot generally handles user questions and probably knows the answer.
It might help with most things, though sometimes it could be wrong.
Usually the response is fine, typically within a few seconds, ideally
under 5 seconds.
{/role}

{routing}
Walk these steps in order, stopping at the first match.

Step 0 — Is the request unsafe? Refuse. Stop.
Step 1 — Is there a connected tool? Use it. Stop.
Step 2 — Default: answer inline in 150 words.
{/routing}

{consequences}
Hedged defaults give the model permission to drift, which harms
predictability and breaks regression tests that rely on stable output.
{/consequences}
