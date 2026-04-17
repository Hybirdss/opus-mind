# False-positive gallery

Every line below is a phrase that SHOULD NOT trigger a finding. The
regex checker has been tuned to pass all of these. If a tune breaks
one, test_false_positives catches it.

## Adjectives that look like slop but aren't governing behavior

Property management is the user's job, not ours.
99% uptime under a robust design, with 500 calls per minute.
5 seconds average response time keeps the experience seamless.

## Stems that share prefix with slop

The property of being idempotent matters here.
Proper nouns stay capitalized.
Reasonable doubt is a legal term of art, not a rule softener.

## Numbers near adj (should keep adj, no FIXME)

The service handles 10000 requests per hour under a robust load balancer.
Seamless deploys run in under 30 seconds.
Response latency is 200 ms for an efficient pipeline.

## Words that contain narration phrase substrings

The letter-opener works as expected.
Bracket notation wins here.

## Ladder-looking text that is not a ladder

Step 1 of 5 is complete, onto Step 2.
The ladder leans against the wall.

## Refusal topic mention without real refusal policy

The word "refuse" appears once here as a vocabulary demo.
