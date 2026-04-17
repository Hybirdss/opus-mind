#!/usr/bin/env bash
# opus-mind critic — multi-stage audit loop.
#
# Pipeline:
#   1. audit   → score the prompt, record verdict + failing invariants
#   2. plan    → list missing required primitives for this domain
#   3. fix     → inject deterministic skeletons for everything fix --add knows
#   4. audit   → re-score; report the delta
#   5. crosscheck prompt emit → let the surrounding LLM apply the semantic review
#
# Never calls an API. The crosscheck step ends with a prompt the caller
# pastes into Claude / ChatGPT / Cursor. When opus-mind is invoked from
# inside a Claude Code session, Claude reads the emitted prompt and
# applies it right there in chat — that's the product.
#
# Usage:
#   opus-mind critic <path>              # full loop, applies fixes, emits crosscheck
#   opus-mind critic <path> --dry-run    # audits + plans only, writes nothing
#   opus-mind critic <path> --no-fix     # audit + plan + crosscheck (no fix step)
#   opus-mind critic <path> --json       # structured summary for CI consumers

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${PYTHON:-python3}"

usage() {
    sed -n '2,22p' "$0" | sed 's/^# //;s/^#//'
}

# -- arg parsing ------------------------------------------------------------

dry_run=0
no_fix=0
json_out=0
path=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run)  dry_run=1; shift ;;
        --no-fix)   no_fix=1;  shift ;;
        --json)     json_out=1; shift ;;
        -h|--help)  usage; exit 0 ;;
        -*)         echo "unknown flag: $1" >&2; exit 2 ;;
        *)          path="$1"; shift ;;
    esac
done

if [ -z "$path" ]; then
    echo "error: path required" >&2
    usage >&2
    exit 2
fi

if [ ! -f "$path" ]; then
    echo "error: $path not found" >&2
    exit 2
fi

# -- phase 1: audit (pre) ---------------------------------------------------

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

pre_json="$tmp_dir/pre.json"
"$py" "$here/audit.py" --json "$path" > "$pre_json" || true

pre_score=$("$py" -c "import json; print(json.load(open('$pre_json'))['structural_health'])")
pre_verdict=$("$py" -c "import json; print(json.load(open('$pre_json'))['verdict'])")

if [ "$json_out" -eq 0 ]; then
    echo "[1/5] audit (before)"
    echo "      score:   $pre_score"
    echo "      verdict: $pre_verdict"
    echo ""
fi

# -- phase 2: plan ----------------------------------------------------------

plan_json="$tmp_dir/plan.json"
"$py" "$here/plan.py" --json "$path" > "$plan_json" || true

missing_keys=$("$py" -c "
import json
d = json.load(open('$plan_json'))
mapping = {
    'I2_no_rule_conflicts': 'ladder',
    'I3_motivated_reasoning': 'reframe-guard',
    'I6_failure_modes_explicit': 'consequences',
    'I8_default_exception': 'defaults',
    'I9_self_check': 'self-check',
    'I10_tier_labels': 'tier-labels',
    'I11_hierarchical_override': 'tier-labels',
}
adds = []
for inv in d.get('missing_required', []):
    key = mapping.get(inv)
    if key and key not in adds:
        adds.append(key)
print(','.join(adds))
")

if [ "$json_out" -eq 0 ]; then
    echo "[2/5] plan — missing required primitives translate to --add keys:"
    if [ -n "$missing_keys" ]; then
        echo "      $missing_keys"
    else
        echo "      (nothing to add — required primitives all present)"
    fi
    echo ""
fi

# -- phase 3: fix -----------------------------------------------------------

fix_applied=0
if [ "$dry_run" -eq 0 ] && [ "$no_fix" -eq 0 ] && [ -n "$missing_keys" ]; then
    "$py" "$here/fix.py" "$path" --add "$missing_keys" --apply \
        >"$tmp_dir/fix.log" 2>&1 || true
    fix_applied=1
    if [ "$json_out" -eq 0 ]; then
        echo "[3/5] fix — injected skeletons for: $missing_keys"
        echo "      (review <FIXME> markers in $path before commit)"
        echo ""
    fi
elif [ "$json_out" -eq 0 ]; then
    if [ "$dry_run" -eq 1 ]; then
        echo "[3/5] fix — skipped (--dry-run)"
    elif [ "$no_fix" -eq 1 ]; then
        echo "[3/5] fix — skipped (--no-fix)"
    else
        echo "[3/5] fix — no changes to apply"
    fi
    echo ""
fi

# -- phase 4: audit (post) --------------------------------------------------

post_json="$tmp_dir/post.json"
"$py" "$here/audit.py" --json "$path" > "$post_json" || true

post_score=$("$py" -c "import json; print(json.load(open('$post_json'))['structural_health'])")
post_verdict=$("$py" -c "import json; print(json.load(open('$post_json'))['verdict'])")

if [ "$json_out" -eq 0 ]; then
    echo "[4/5] audit (after)"
    echo "      score:   $post_score   (was $pre_score)"
    echo "      verdict: $post_verdict  (was $pre_verdict)"
    echo ""
fi

# -- phase 5: crosscheck prompt emit ----------------------------------------

if [ "$json_out" -eq 0 ]; then
    echo "[5/5] crosscheck prompt — semantic review the regex cannot do."
    echo "      Paste the block below into any LLM, OR — if you're in a"
    echo "      Claude Code session — let Claude read it and reply."
    echo ""
    echo "=========================================================="
    "$py" "$here/audit.py" --crosscheck "$path"
    echo "=========================================================="
fi

# -- JSON summary (CI-friendly) ---------------------------------------------

if [ "$json_out" -eq 1 ]; then
    "$py" -c "
import json
pre = json.load(open('$pre_json'))
post = json.load(open('$post_json'))
plan = json.load(open('$plan_json'))
print(json.dumps({
    'path': '$path',
    'pre':  {'score': pre['structural_health'], 'verdict': pre['verdict']},
    'post': {'score': post['structural_health'], 'verdict': post['verdict']},
    'fix_applied': bool($fix_applied),
    'added_keys': '$missing_keys',
    'placeholder_count': post.get('placeholder_count', 0),
    'still_failing': [k for k, v in post['pass'].items() if not v],
}, indent=2))
"
fi

# Exit code mirrors the final audit: 0 on verdict GOOD, 1 otherwise.
if [ "$post_verdict" = "GOOD" ]; then
    exit 0
else
    exit 1
fi
