#!/usr/bin/env bash
# check-skill-links.sh - detect skills that have silently drifted out of version control.
#
# WHY THIS EXISTS: a skill deployed to ~/.claude/skills/ can be either a JUNCTION into
# this repo (edits are version-controlled, one source of truth) or a plain COPY (edits
# are invisible to git and the two versions drift apart). Both look identical in the
# skill picker, and nothing warns you.
#
# That failed for real, twice, on 2026-09-19:
#   * markdown-to-epub was a copy. A cover-layout fix was written into the deployed
#     copy and never reached this repo. `git status` showed nothing, so the fix would
#     have been lost the next time the copy was refreshed.
#   * branded-docx was a copy that had gone stale in the OTHER direction: the deployed
#     version was 2.5.0 while this repo was at 2.7.0, so months of work (the Magma
#     brand theme, the font-fidelity fix) simply never reached the machine using it.
#     Client documents were being generated with a two-version-old skill.
#
# The rule this enforces: THIS REPO IS THE ONLY SOURCE OF TRUTH. Every deployed skill
# that exists here must be a junction into here. Never edit under ~/.claude/skills/.
#
# Usage:
#   bash scripts/check-skill-links.sh          # report
#   bash scripts/check-skill-links.sh --fix    # print the commands to fix each problem
#
# Exit codes: 0 = everything linked correctly; 1 = drift found.

set -uo pipefail

DEPLOY_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_DIR/skills"
FIX=false
[[ "${1:-}" == "--fix" ]] && FIX=true

[[ -d "$DEPLOY_DIR" ]] || { echo "deploy dir not found: $DEPLOY_DIR" >&2; exit 1; }
[[ -d "$SRC_DIR" ]]    || { echo "skills dir not found: $SRC_DIR" >&2; exit 1; }

problems=0
fixes=()

# A reparse point (junction or symlink) reads as a symlink to Git Bash, which is enough
# to tell "linked" from "plain copy". Checking that rather than shelling out to `dir /AL`
# keeps this working on macOS and Linux too.
is_linked() { [[ -L "$1" ]]; }

echo "source of truth: $SRC_DIR"
echo "deployed:        $DEPLOY_DIR"
echo

for src in "$SRC_DIR"/*/; do
  name="$(basename "$src")"
  dep="$DEPLOY_DIR/$name"

  if [[ ! -e "$dep" ]]; then
    echo "  [ absent  ] $name - in this repo, not deployed"
    continue
  fi

  if is_linked "$dep"; then
    if [[ -f "$dep/SKILL.md" ]]; then
      echo "  [ linked  ] $name"
    else
      echo "  [ BROKEN  ] $name - link exists but does not resolve"
      problems=$((problems + 1))
      fixes+=("# $name: link is broken, recreate it")
    fi
    continue
  fi

  # Plain copy: the drift case. Say which side is ahead, because that decides whether
  # junctioning is a free upgrade or would discard local edits.
  echo "  [ COPY !! ] $name - a plain directory, edits here are invisible to git"
  problems=$((problems + 1))
  if diff -rq --strip-trailing-cr "$src" "$dep" >/dev/null 2>&1; then
    echo "             identical to the repo; safe to junction now"
  else
    echo "             CONTENT DIFFERS from the repo. Diff before linking:"
    echo "             diff -rq --strip-trailing-cr '$src' '$dep'"
  fi
  fixes+=("mv '$dep' '$dep.pre-junction' && powershell -NoProfile -Command \"New-Item -ItemType Junction -Path '$(cygpath -m "$dep" 2>/dev/null || echo "$dep")' -Target '$(cygpath -m "$src" 2>/dev/null || echo "$src")' | Out-Null\"")
done

# Leftover rollback directories register as DUPLICATE skills in the picker, which is its
# own bug: the model may route to the stale one.
shopt -s nullglob
for stale in "$DEPLOY_DIR"/*.pre-junction; do
  echo "  [ STALE   ] $(basename "$stale") - leftover copy, registers as a duplicate skill"
  problems=$((problems + 1))
  fixes+=("rm -rf '$stale'")
done
shopt -u nullglob

echo
if [[ $problems -eq 0 ]]; then
  echo "OK: every skill in this repo is deployed as a junction."
  exit 0
fi

echo "$problems problem(s) found."
if $FIX; then
  echo
  echo "Suggested commands (review each before running; a junction makes THIS REPO win):"
  printf '%s\n' "${fixes[@]}"
else
  echo "Re-run with --fix to print the commands."
fi
exit 1
