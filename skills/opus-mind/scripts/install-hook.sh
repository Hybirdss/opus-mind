#!/usr/bin/env bash
# opus-mind install-hook.sh — install a git pre-commit hook that runs
# audit.py on any staged prompt file and blocks commits below threshold.
#
# Safety:
# - Existing pre-commit hook is backed up to pre-commit.backup-<timestamp>.
# - --dry-run prints the hook content without installing.
# - --uninstall restores the most recent backup (or deletes the opus-mind hook
#   if none exists).
# - --threshold N sets the block threshold (1-6, default 5).
#
# Usage:
#   bash install-hook.sh                      install (threshold 5)
#   bash install-hook.sh --threshold 6        strict 6/6 gate
#   bash install-hook.sh --dry-run            preview only
#   bash install-hook.sh --uninstall          remove, restore backup if any

set -euo pipefail

threshold=5
dry_run=0
uninstall=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --threshold) threshold="$2"; shift 2 ;;
        --threshold=*) threshold="${1#*=}"; shift ;;
        --dry-run) dry_run=1; shift ;;
        --uninstall) uninstall=1; shift ;;
        -h|--help)
            sed -n '2,19p' "$0" | sed 's/^# //;s/^#//'
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if ! [[ "$threshold" =~ ^[1-6]$ ]]; then
    echo "error: --threshold must be 1-6, got $threshold" >&2
    exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
audit_script="$here/audit.py"
registry_path=""

git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$git_root" ]; then
    echo "error: not inside a git repo" >&2
    exit 2
fi

if [ -f "$git_root/.opus-mind.json" ]; then
    registry_path="$git_root/.opus-mind.json"
fi

hook_path="$git_root/.git/hooks/pre-commit"

if [ "$uninstall" -eq 1 ]; then
    latest_backup=$(ls -1t "$git_root/.git/hooks/pre-commit.backup-"* 2>/dev/null | head -n1 || true)
    if [ -n "$latest_backup" ]; then
        mv "$latest_backup" "$hook_path"
        echo "restored: $latest_backup -> $hook_path"
    elif [ -f "$hook_path" ]; then
        if grep -q "Installed by opus-mind" "$hook_path" 2>/dev/null; then
            rm "$hook_path"
            echo "removed: $hook_path (was opus-mind hook)"
        else
            echo "refusing to remove $hook_path — not installed by opus-mind"
            exit 2
        fi
    else
        echo "nothing to uninstall."
    fi
    exit 0
fi

if [ ! -f "$audit_script" ]; then
    echo "error: audit.py not found at $audit_script" >&2
    exit 2
fi

generated_hook=$(cat <<EOF
#!/usr/bin/env bash
# Installed by opus-mind install-hook.sh. Threshold: $threshold / 6.
# Uninstall: bash $here/install-hook.sh --uninstall
# Bypass for one commit: git commit --no-verify
set -euo pipefail

AUDIT="$audit_script"
REGISTRY="$registry_path"
THRESHOLD=$threshold

# Build file list: either from .opus-mind.json prompts[] or from a default
# pattern regex matching staged files.
if [ -n "\$REGISTRY" ] && [ -f "\$REGISTRY" ]; then
    registered=\$(python3 -c '
import json, sys
try:
    d = json.load(open("'"\$REGISTRY"'"))
    for p in d.get("prompts", []):
        print(p["path"])
except Exception as e:
    sys.exit(0)
' 2>/dev/null || true)
else
    registered=""
fi

mapfile -t staged < <(git diff --cached --name-only --diff-filter=AM || true)
files=()
for f in "\${staged[@]}"; do
    [ -f "\$f" ] || continue
    # Match against registered paths
    if [ -n "\$registered" ] && echo "\$registered" | grep -qxF "\$f"; then
        files+=("\$f")
        continue
    fi
    # Fallback pattern match
    if echo "\$f" | grep -Eq '(^|/)(CLAUDE|AGENTS|GEMINI|SKILL)\.md\$|(^|/)\.cursorrules\$|system-prompt.*\.md\$|^prompts/'; then
        files+=("\$f")
    fi
done

[ \${#files[@]} -eq 0 ] && exit 0

fail=0
for f in "\${files[@]}"; do
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
)

if [ "$dry_run" -eq 1 ]; then
    echo "# dry-run preview: $hook_path"
    echo "$generated_hook"
    exit 0
fi

if [ -f "$hook_path" ]; then
    if grep -q "Installed by opus-mind" "$hook_path" 2>/dev/null; then
        echo "note: overwriting existing opus-mind hook"
    else
        stamp=$(date +%Y%m%d-%H%M%S)
        backup="$hook_path.backup-$stamp"
        mv "$hook_path" "$backup"
        echo "backup: existing hook -> $backup"
    fi
fi

printf "%s\n" "$generated_hook" > "$hook_path"
chmod +x "$hook_path"
echo "installed: $hook_path"
echo "threshold: $threshold / 6"
echo "registry:  ${registry_path:-<none, pattern fallback>}"
echo "uninstall: bash $here/install-hook.sh --uninstall"
