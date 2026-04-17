# Tier-1 Slop Fixture

{role}
The bot helps users delve into their data and utilize every feature.
It leverages machine learning to facilitate deep insights. This is a
holistic platform that encompasses every need.
{/role}

{routing}
Walk these steps in order, stopping at the first match.

Step 0 — Is the request unsafe? Refuse. Stop.
Step 1 — Did the user paste a CSV? Parse it. Stop.
Step 2 — Default: answer inline.
{/routing}

{consequences}
Skipping the schema check harms downstream analyses and breaks the
spreadsheet parser's contract with its callers.
{/consequences}
