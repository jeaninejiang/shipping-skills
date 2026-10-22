#!/usr/bin/env bash
# Copy these skills into a project, in the layout your agent expects.
#
#   ./install.sh /path/to/project              # asks which tool
#   ./install.sh /path/to/project --claude     # or name it
#   ./install.sh /path/to/project --cursor
#   ./install.sh /path/to/project --agents
#
# Copies only; never deletes. Existing files are left alone unless you
# confirm an overwrite, because your own AGENTS.md is more valuable than
# anything this script has to add to it.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"
TOOL="${2:-}"

if [[ -z "$TARGET" ]]; then
  echo "usage: ./install.sh /path/to/project [--claude|--cursor|--agents]" >&2
  exit 1
fi

if [[ ! -d "$TARGET" ]]; then
  echo "error: $TARGET is not a directory" >&2
  exit 1
fi

if [[ -z "$TOOL" ]]; then
  echo "Which agent reads this project?"
  echo "  1) Claude Code      → .claude/skills/"
  echo "  2) Cursor           → .cursor/rules/"
  echo "  3) Codex / AGENTS.md → skills/ + AGENTS.md"
  read -rp "choice [1-3]: " choice
  case "$choice" in
    1) TOOL=--claude ;;
    2) TOOL=--cursor ;;
    3) TOOL=--agents ;;
    *) echo "error: pick 1, 2 or 3" >&2; exit 1 ;;
  esac
fi

# Let people take a subset. A skill for a stack you aren't using is
# noise in every conversation, so this is the common case, not an edge.
echo
echo "Available skills:"
mapfile -t ALL < <(cd "$HERE/skills" && ls -d */ | tr -d /)
for i in "${!ALL[@]}"; do echo "  $((i+1))) ${ALL[$i]}"; done
read -rp "install which? [numbers, or Enter for all]: " pick

SKILLS=()
if [[ -z "${pick// }" ]]; then
  SKILLS=("${ALL[@]}")
else
  for n in $pick; do
    idx=$((n-1))
    [[ -n "${ALL[$idx]:-}" ]] && SKILLS+=("${ALL[$idx]}")
  done
fi
[[ ${#SKILLS[@]} -eq 0 ]] && { echo "nothing selected" >&2; exit 1; }

copy_skills() {  # $1 = destination dir
  mkdir -p "$1"
  for s in "${SKILLS[@]}"; do
    if [[ -e "$1/$s" ]]; then
      read -rp "  $s already exists in $1 — overwrite? [y/N] " yn
      [[ "$yn" =~ ^[Yy]$ ]] || { echo "  skipped $s"; continue; }
      rm -rf "${1:?}/$s"
    fi
    cp -r "$HERE/skills/$s" "$1/$s"
    echo "  + $s"
  done
}

echo
case "$TOOL" in
  --claude)
    echo "Installing into $TARGET/.claude/skills/"
    copy_skills "$TARGET/.claude/skills"
    ;;

  --cursor)
    echo "Installing into $TARGET/.cursor/rules/"
    copy_skills "$TARGET/.cursor/rules"
    for s in "${SKILLS[@]}"; do
      cp "$HERE/.cursor/rules/$s.mdc" "$TARGET/.cursor/rules/$s.mdc"
    done
    echo "  + rule files pointing at each SKILL.md"
    ;;

  --agents)
    echo "Installing into $TARGET/skills/"
    copy_skills "$TARGET/skills"
    if [[ -f "$TARGET/AGENTS.md" ]]; then
      echo
      echo "  $TARGET/AGENTS.md already exists — not touching it."
      echo "  Add the 'When to read what' table from this repo's AGENTS.md."
    else
      cp "$HERE/AGENTS.md" "$TARGET/AGENTS.md"
      echo "  + AGENTS.md"
    fi
    ;;

  *)
    echo "error: unknown option $TOOL" >&2
    exit 1
    ;;
esac

echo
echo "Done. Start with app-flow-design — fill its flow spec template"
echo "before writing code, and let the gates shape your schema."
