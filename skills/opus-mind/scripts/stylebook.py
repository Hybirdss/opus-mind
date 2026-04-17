"""
stylebook.py — author's opinionated anti-slop word list.

    NOT GROUNDED IN OPUS 4.7.

These lists are the author's personal stylebook, imported from a private
`~/.claude/rules/conventions.md`. They are useful for engineers who share
the same taste, but they do not belong in the primary audit score — the
primary score is defined only by invariants traceable to the Opus 4.7
source (see `audit.py` docstring for line refs).

Opt-in via `audit.py --stylebook`. When used, violations surface under
the `stylebook` category (not I1–I6).

Design note:
    The Opus 4.7 source itself uses words from these lists — "multifaceted"
    (L68), "nuanced" (L130), "facilitates" (L32), "comprehensive" (L18).
    A rule that flags the source as non-compliant is not a rule derived
    from the source. Hence: opt-in, separate category, author-attributed.
"""

from __future__ import annotations

# Tier 1 verbs — inflection-tolerant (utilize → utilizes, utilized, utilizing).
SLOP_TIER1_STEM = [
    "delve", "utilize", "leverage", "facilitate", "encompass",
    "catalyze",
]

# Tier 1 exact — bare nouns and adjectives, no inflection needed.
SLOP_TIER1_EXACT = [
    "multifaceted", "tapestry", "testament", "paradigm", "synergy",
    "holistic", "nuanced", "realm", "landscape", "myriad", "plethora",
]

# Tier 2 verbs — inflection-tolerant.
SLOP_TIER2_STEM = [
    "streamline", "empower", "foster", "elevate", "resonate",
]

# Tier 2 exact — bare adjectives. Kept conservative: words like "proper"
# and "reasonable" were excluded because legitimate English uses (legal /
# philosophical) collide with the rule.
SLOP_TIER2_EXACT = [
    "robust", "comprehensive", "seamless", "cutting-edge", "innovative",
    "pivotal", "intricate", "cornerstone", "effective",
    "efficient", "appropriate", "optimal", "enhance",
]
