#!/usr/bin/env bash
set -euo pipefail

PROMPTS_DIR="documentation/prompts"
OUT_DIRS=(
  ".cursor/commands"
  ".opencode/commands"
  ".claude/commands"
  ".codex/prompts"
)

# Ensures prompt files exist
shopt -s nullglob
PROMPTS=( "$PROMPTS_DIR"/*.md )
if (( ${#PROMPTS[@]} == 0 )); then
  echo "No prompts found in '$PROMPTS_DIR/*.md'"
  exit 1
fi

# Creates output directories
for dir in "${OUT_DIRS[@]}"; do
  mkdir -p "$dir"
done

# Function: try symlink; fallback to copy
link_or_copy() {
  local src="$1"
  local dest="$2"

  # Relative path from destination to source (repo root)
  # destination is in .cursor/commands or .opencode/commands (2 levels)
  local rel_src="../../$src"

  # Remove old file (or symlink) to avoid conflicts
  rm -f "$dest"

  # Try symlink (Linux/macOS/Git Bash). If it fails, copy.
  if ln -s "$rel_src" "$dest" 2>/dev/null; then
    echo "linked:  $dest -> $rel_src"
  else
    # Fallback: copy file content
    {
      echo "<!-- Auto-generated from $src (symlink not available) -->"
      echo
      cat "$src"
    } > "$dest"
    echo "copied:  $dest <- $src"
  fi
}

for src in "${PROMPTS[@]}"; do
  filename="$(basename "$src")"
  name="${filename%.md}"

  # Remove trailing "-prompt" (if present)
  if [[ "$name" == *-prompt ]]; then
    name="${name%-prompt}"
  fi

  for dir in "${OUT_DIRS[@]}"; do
    dest="$dir/$name.md"
    link_or_copy "$src" "$dest"
  done
done
