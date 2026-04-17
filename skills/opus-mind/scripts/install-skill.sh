#!/usr/bin/env bash
# install-skill.sh — register opus-mind as a global Claude Code skill.
#
# Creates a symlink at ~/.claude/skills/opus-mind pointing to this repo's
# skill directory. After running, Claude Code discovers the skill on its
# next session start.
#
# Safety:
#   - Refuses to overwrite a non-symlink at the target path.
#   - Backs up an existing opus-mind symlink if it points somewhere else.
#   - --dry-run shows the action without executing it.
#   - --uninstall removes the symlink (leaves this repo intact).
#
# Usage:
#   bash install-skill.sh                 install (link from ~/.claude/skills/)
#   bash install-skill.sh --dry-run       preview only
#   bash install-skill.sh --uninstall     remove the symlink
#   bash install-skill.sh --target DIR    custom install directory
#
# Distribution:
#   This is the Claude Code path. For standalone CLI use, add
#   skills/opus-mind/scripts/ to your $PATH or install via pip (future).

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_src="$(cd "$here/.." && pwd)"
target_dir="${HOME}/.claude/skills"

dry_run=0
uninstall=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run) dry_run=1; shift ;;
        --uninstall) uninstall=1; shift ;;
        --target) target_dir="$2"; shift 2 ;;
        --target=*) target_dir="${1#*=}"; shift ;;
        -h|--help)
            sed -n '2,22p' "$0" | sed 's/^# //;s/^#//'
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

link_path="${target_dir}/opus-mind"

# Basic sanity
if [ ! -f "$skill_src/SKILL.md" ]; then
    echo "error: SKILL.md not found at $skill_src/SKILL.md" >&2
    echo "       (install-skill.sh must live inside the skill directory)" >&2
    exit 2
fi

if [ "$uninstall" -eq 1 ]; then
    if [ -L "$link_path" ]; then
        dest="$(readlink "$link_path")"
        if [ "$dry_run" -eq 1 ]; then
            echo "# dry-run: would remove symlink $link_path -> $dest"
            exit 0
        fi
        rm "$link_path"
        echo "removed symlink: $link_path (was -> $dest)"
    elif [ -e "$link_path" ]; then
        echo "refusing to remove $link_path — not a symlink, may be yours" >&2
        exit 2
    else
        echo "nothing to uninstall."
    fi
    exit 0
fi

mkdir -p "$target_dir"

# If target already exists, check what it is
if [ -L "$link_path" ]; then
    existing="$(readlink "$link_path")"
    if [ "$existing" = "$skill_src" ]; then
        echo "already installed: $link_path -> $existing"
        exit 0
    fi
    if [ "$dry_run" -eq 1 ]; then
        echo "# dry-run: would replace symlink"
        echo "#   $link_path -> $existing (old)"
        echo "#   $link_path -> $skill_src (new)"
        exit 0
    fi
    backup="${link_path}.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$link_path" "$backup"
    echo "backup: old symlink -> $backup"
elif [ -e "$link_path" ]; then
    echo "refusing to overwrite $link_path — exists and is not a symlink" >&2
    echo "       move or remove it first" >&2
    exit 2
fi

if [ "$dry_run" -eq 1 ]; then
    echo "# dry-run: would create symlink"
    echo "#   $link_path -> $skill_src"
    exit 0
fi

ln -s "$skill_src" "$link_path"
echo "installed: $link_path -> $skill_src"
echo ""
echo "Claude Code discovers skills on session start. Restart your"
echo "Claude Code session (or type /skills reload) to pick up opus-mind."
echo ""
echo "Test with: ask Claude Code \"audit my CLAUDE.md\""
