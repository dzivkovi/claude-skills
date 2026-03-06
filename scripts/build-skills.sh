#!/usr/bin/env bash
# build-skills.sh
# Packages each skill in skills/ into a .skill file in releases/.
# Produces two files per skill: a versioned build and a -latest alias.
#
# Usage:
#   ./scripts/build-skills.sh              # build all skills
#   ./scripts/build-skills.sh branded-docx # build one skill by name

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/..")" && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
RELEASES_DIR="$REPO_ROOT/releases"

mkdir -p "$RELEASES_DIR"

TARGET="${1:-}"   # optional: specific skill name

built=0
skipped=0

for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_dir")"

  # Filter to requested skill if argument provided
  if [ -n "$TARGET" ] && [ "$skill_name" != "$TARGET" ]; then
    continue
  fi

  skill_md="$skill_dir/SKILL.md"
  if [ ! -f "$skill_md" ]; then
    echo "  skip: $skill_name (no SKILL.md)"
    skipped=$((skipped + 1))
    continue
  fi

  # Extract version from YAML frontmatter (version: x.y.z)
  version="$(grep -m1 '^version:' "$skill_md" | sed 's/version:[[:space:]]*//' | tr -d '"' || true)"
  if [ -z "$version" ]; then
    echo "  skip: $skill_name (no version: field in SKILL.md frontmatter)"
    skipped=$((skipped + 1))
    continue
  fi

  versioned_file="$RELEASES_DIR/${skill_name}-v${version}.skill"
  latest_file="$RELEASES_DIR/${skill_name}-latest.skill"

  # Pack into a temp location then move (avoids partial writes)
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT

  cp -r "$skill_dir" "$tmp_dir/$skill_name"
  (cd "$tmp_dir" && zip -r "$versioned_file" "$skill_name/" \
    --exclude "*/.DS_Store" \
    --exclude "*/__pycache__/*" \
    --exclude "*/*.pyc" \
    -q)

  cp "$versioned_file" "$latest_file"
  rm -rf "$tmp_dir"
  trap - EXIT

  size="$(du -sh "$versioned_file" | cut -f1)"
  echo "  built: ${skill_name}-v${version}.skill  (${size})"
  echo "         ${skill_name}-latest.skill updated"
  built=$((built + 1))
done

echo ""
if [ "$built" -eq 0 ] && [ "$skipped" -eq 0 ]; then
  echo "No skills found in $SKILLS_DIR"
  exit 1
fi

echo "Done: $built built, $skipped skipped -> $RELEASES_DIR"
