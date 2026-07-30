#!/usr/bin/env bash
set -euo pipefail
# status-all.sh — Dashboard cross-worktree (mec. H)
# SSoT: docs/process/parallel-sessions-protocol.md § D7 + D13
#
# Output enriquece `git worktree list` con:
# - branch
# - dirty/clean status
# - last commit SHA + relative age
# - story-id from .session.yaml manifest
# - Docker activo per brand (containers luana-{brand}-*)
#
# Usage:
#   scripts/git/status-all.sh
#
# No args. Read-only.

# Color codes (ASCII fallback if no tty)
if [[ -t 1 ]]; then
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
  C_CYAN=$'\033[36m'
  C_DIM=$'\033[2m'
  C_RESET=$'\033[0m'
else
  C_GREEN=""; C_YELLOW=""; C_RED=""; C_CYAN=""; C_DIM=""; C_RESET=""
fi

# Compute Docker activity per brand (one shot)
declare -A DOCKER_BY_BRAND
if command -v docker &>/dev/null; then
  while IFS= read -r container; do
    [[ -z "$container" ]] && continue
    # Soportar 2 naming conventions: luana-{brand}-{service}-dev y luana-dev-{brand}_{service}_dev-N
    if [[ "$container" =~ ^luana-dev-([a-z]+)_ ]]; then
      brand="${BASH_REMATCH[1]}"
      # Skip "luana" prefix (postgres compartido se llama luana-dev-luana_postgres)
      [[ "$brand" = "luana" ]] && continue
      DOCKER_BY_BRAND["$brand"]=1
    elif [[ "$container" =~ ^luana-([a-z]+)- ]]; then
      brand="${BASH_REMATCH[1]}"
      DOCKER_BY_BRAND["$brand"]=1
    fi
  done < <(docker ps --format '{{.Names}}' 2>/dev/null)
fi

# Header
printf "%-50s %-45s %-12s %-18s %-25s %s\n" \
  "WORKTREE" "BRANCH" "STATUS" "LAST COMMIT" "STORY" "DOCKER"
printf "%-50s %-45s %-12s %-18s %-25s %s\n" \
  "$(printf '%.0s-' {1..50})" "$(printf '%.0s-' {1..45})" "$(printf '%.0s-' {1..12})" \
  "$(printf '%.0s-' {1..18})" "$(printf '%.0s-' {1..25})" "$(printf '%.0s-' {1..6})"

# Iterate worktrees
git worktree list --porcelain | awk '
  /^worktree / {path=$2}
  /^HEAD / {sha=$2}
  /^branch / {branch=$2; print path"|"sha"|"branch}
  /^bare/ {next}
' | while IFS='|' read -r path sha branch; do
  [[ -z "$path" ]] && continue

  basename="$(basename "$path")"
  branch_short="${branch#refs/heads/}"

  # Tree status
  if git -C "$path" diff --quiet 2>/dev/null && git -C "$path" diff --cached --quiet 2>/dev/null; then
    untracked="$(git -C "$path" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$untracked" -gt 0 ]]; then
      status="${C_YELLOW}clean+u${C_RESET}"
    else
      status="${C_GREEN}clean${C_RESET}"
    fi
  else
    modified="$(git -C "$path" diff --name-only 2>/dev/null | wc -l | tr -d ' ')"
    staged="$(git -C "$path" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
    total=$((modified + staged))
    status="${C_RED}${total} modif${C_RESET}"
  fi

  # Last commit (relative time)
  last="$(git -C "$path" log -1 --format='%h %cr' 2>/dev/null || echo '—')"

  # Story-id from manifest
  manifest="$path/.session.yaml"
  story="—"
  if [[ -f "$manifest" ]]; then
    story_raw="$(grep -E '^story_id: ' "$manifest" 2>/dev/null | head -1 | sed 's/^story_id: //')"
    lane="$(grep -E '^lane: ' "$manifest" 2>/dev/null | head -1 | sed 's/^lane: //')"
    [[ -n "$story_raw" ]] && story="$story_raw"
    [[ -n "$lane" && "$lane" != "" ]] && story="$story/$lane"
  fi

  # Docker
  docker_status="—"
  if [[ "$basename" =~ ^luana-([a-z]+) ]]; then
    brand_from_path="${BASH_REMATCH[1]}"
    if [[ -n "${DOCKER_BY_BRAND[$brand_from_path]:-}" ]]; then
      docker_status="${C_CYAN}${brand_from_path} ✓${C_RESET}"
    fi
  fi

  printf "%-50s %-45s %-12s %-18s %-25s %s\n" \
    "$basename" "$branch_short" "$status" "$last" "$story" "$docker_status"
done

# Footer
echo ""
echo "${C_DIM}Tips:${C_RESET}"
echo "  - Worktree status modif >0: pushear pronto (M11)"
echo "  - Docker activo en >1 brand simultáneo: OK; >1 stack misma brand: D5 violation"
echo "  - story=— : worktree sin manifest, regenerar con scripts/git/regenerate-manifest.sh"
