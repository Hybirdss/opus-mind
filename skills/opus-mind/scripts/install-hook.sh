#!/usr/bin/env bash
# opus-mind install-hook.sh — install a git pre-commit hook that runs
# audit.py on any staged prompt file and blocks commits below threshold.
#
# Usage (from inside any git repo):
#   bash /path/to/opus-mind/scripts/install-hook.sh
#   bash /path/to/opus-mind/scripts/install-hook.sh --threshold 5
#
# Patterns matched (staged, added/modified): CLAUDE.md, AGENTS.md,
# .cursorrules, GEMINI.md, SKILL.md, system-prompt*.md.

set -euo pipefail

threshold=5
while [ "$#" -gt 0 ]; do
    case "$1" in
        --threshold) threshold="$2"; shift 2 ;;
        --threshold=*) threshold="${1#*=}"; shift ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
audit_script="$here/audit.py"

if [ ! -f "$audit_script" ]; then
    echo "error: audit.py not found at $audit_script" >&2
    exit 2
fi

git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$git_root" ]; then
    echo "error: not inside a git repo" >&2
    exit 2
fi

hooks_dir="$git_root/.git/hooks"
hook_path="$hooks_dir/pre-commit"

cat > "$hook_path" <<EOF
#!/usr/bin/env bash
# Installed by opus-mind install-hook.sh. Threshold: $threshold / 6.
set -euo pipefail

AUDIT="$audit_script"
THRESHOLD=$threshold

mapfile -t files < <(
    git diff --cached --name-only --diff-filter=AM |
    grep -E '(^|/)(CLAUDE|AGENTS|GEMINI|SKILL)\.md$|(^|/)\.cursorrules$|system-prompt.*\.md$' || true
)

[ \${#files[@]} -eq 0 ] && exit 0

fail=0
for f in "\${files[@]}"; do
    [ -f "\$f" ] || continue
    score_line=\$(python3 "\$AUDIT" "\$f" 2>/dev/null | grep '^score:' || true)
    score=\$(echo "\$score_line" | awk -F'[ /]' '{print \$2}')
    if [ -z "\$score" ]; then
        echo "[opus-mind] could not score \$f" >&2
        continue
    fi
    if [ "\$score" -lt "\$THRESHOLD" ]; then
        echo "[opus-mind] FAIL \$f — \$score_line (need >= \$THRESHOLD)"
        fail=1
    else
        echo "[opus-mind] PASS \$f — \$score_line"
    fi
done

if [ "\$fail" -eq 1 ]; then
    echo ""
    echo "commit blocked. fix the failing files or bypass with: git commit --no-verify"
    exit 1
fi
EOF

chmod +x "$hook_path"
echo "installed: $hook_path"
echo "threshold: $threshold / 6"
echo "audit: $audit_script"
