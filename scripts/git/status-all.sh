#!/usr/bin/env bash
set -euo pipefail
# status-all.sh — Dashboard del repo único (simplificado 2026-07-31 · retiro worktrees)
#
# Reporta: branch, tree status (dirty/clean + untracked), last commit,
# y containers Docker vitalia activos.
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

REPO_ROOT="$(git rev-parse --show-toplevel)"
BRANCH="$(git branch --show-current 2>/dev/null || echo '<detached>')"

# Tree status
if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
  untracked="$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "$untracked" -gt 0 ]]; then
    STATUS="${C_YELLOW}clean+${untracked}u${C_RESET}"
  else
    STATUS="${C_GREEN}clean${C_RESET}"
  fi
else
  modified="$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')"
  staged="$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
  STATUS="${C_RED}$((modified + staged)) modif${C_RESET}"
fi

LAST="$(git log -1 --format='%h %cr' 2>/dev/null || echo '—')"
AHEAD_BEHIND="$(git rev-list --left-right --count "origin/${BRANCH}...HEAD" 2>/dev/null | awk '{print "behind "$1" / ahead "$2}' || echo '—')"

echo "Repo:    ${REPO_ROOT}"
echo "Branch:  ${BRANCH}"
echo "Status:  ${STATUS}"
echo "Last:    ${LAST}"
echo "Remote:  ${AHEAD_BEHIND}"

# Docker containers vitalia
if command -v docker &>/dev/null; then
  CONTAINERS="$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E '^luana-(dev-)?vitalia' || true)"
  if [[ -n "$CONTAINERS" ]]; then
    echo "Docker:  ${C_CYAN}vitalia ✓${C_RESET}"
    echo "$CONTAINERS" | sed 's/^/         /'
  else
    echo "Docker:  — (make dev-vitalia para levantar)"
  fi
fi

echo ""
echo "${C_DIM}Tip: status modif >0 → pushear pronto (M11: nunca >30 min sin push)${C_RESET}"
