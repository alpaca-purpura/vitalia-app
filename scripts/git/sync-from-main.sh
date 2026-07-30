#!/usr/bin/env bash
set -euo pipefail
# sync-from-main.sh — Sync KISS activo (v2 cementado 2026-05-18)
# SSoT: docs/process/parallel-sessions-protocol.md § D10-v2
#
# Garantiza que el worktree actual está al día con origin/main.
# Acción graduada según estado:
#
#   tree clean + FF puro          → auto-FF silencioso
#   tree clean + merge real OK    → auto MERGE silencioso + 1 línea
#   tree clean + merge real CONF  → STOP + lista archivos + sugerir resolver
#   tree dirty + FF puro          → auto-FF (no toca WIP)
#   tree dirty + merge real       → STOP + "commit/stash tu WIP primero"
#   already up-to-date            → silencioso
#
# Usage:
#   scripts/git/sync-from-main.sh                # ejecuta en cwd
#   scripts/git/sync-from-main.sh --check        # solo reporta estado (no integra)
#   scripts/git/sync-from-main.sh --quiet        # silent si OK
#
# Exit codes:
#   0  Synced exitoso (o ya estaba al día)
#   1  Conflict detectado / tree dirty + merge real (acción del user requerida)
#   2  Error git operation
#   3  Banned branch (main / release/*)

MODE="execute"
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --check) MODE="check" ;;
    --quiet) QUIET=1 ;;
    --help|-h)
      sed -n '1,30p' "$0"
      exit 0
      ;;
    *)
      echo "::error::Unknown arg: $arg (try --help)"
      exit 2
      ;;
  esac
done

# Workspace detection
WORKTREE="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${WORKTREE}" ]]; then
  echo "::error::Not in a git repo"
  exit 2
fi
cd "${WORKTREE}"

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || echo '')"
if [[ -z "${CURRENT_BRANCH}" ]]; then
  echo "::error::Detached HEAD — checkout a branch first"
  exit 3
fi

# Banned: no sync from main on main itself or release/*
case "${CURRENT_BRANCH}" in
  main|release/*)
    echo "::error::sync-from-main NOT applicable on branch ${CURRENT_BRANCH}"
    echo "  This script is for wip/* branches only."
    exit 3
    ;;
esac

# Fetch fresh
[[ ${QUIET} -eq 0 ]] && echo "→ Fetching origin/main..."
if ! git fetch origin main 2>&1 | grep -v "^$"; then
  echo "::error::git fetch origin main failed"
  exit 2
fi

# Diagnostic
LOCAL_SHA="$(git rev-parse HEAD)"
MAIN_SHA="$(git rev-parse origin/main)"
MERGE_BASE="$(git merge-base HEAD origin/main)"

# Behind/ahead counts
BEHIND_COUNT="$(git rev-list --count HEAD..origin/main)"
AHEAD_COUNT="$(git rev-list --count origin/main..HEAD)"

# Tree dirty? = SOLO archivos tracked modificados. Los untracked (cruft tipo
# tools/, .clone/) NO bloquean un merge — git los preserva → no deben frenar el sync.
TREE_DIRTY=0
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  TREE_DIRTY=1
fi

# Core touched by incoming commits?
CORE_TOUCHED=0
if [[ ${BEHIND_COUNT} -gt 0 ]]; then
  if git diff --name-only HEAD..origin/main | grep -qE '^core/luana-core-[^/]+/src/' 2>/dev/null; then
    CORE_TOUCHED=1
  fi
fi

# Already up-to-date case
if [[ ${BEHIND_COUNT} -eq 0 ]]; then
  [[ ${QUIET} -eq 0 ]] && echo "✓ ${CURRENT_BRANCH} already up-to-date with origin/main"
  exit 0
fi

# Format summary line
SUMMARY="${BEHIND_COUNT} commits behind origin/main"
[[ ${AHEAD_COUNT} -gt 0 ]] && SUMMARY="${SUMMARY}, ${AHEAD_COUNT} ahead"
[[ ${CORE_TOUCHED} -eq 1 ]] && SUMMARY="${SUMMARY} (CORE TOUCHED)"

# Check-only mode
if [[ "${MODE}" = "check" ]]; then
  echo "${SUMMARY}"
  echo "tree:    $([[ ${TREE_DIRTY} -eq 1 ]] && echo 'dirty' || echo 'clean')"
  echo "ff-puro: $([[ ${AHEAD_COUNT} -eq 0 ]] && echo 'yes' || echo 'no (merge real needed)')"
  exit 0
fi

# Determine action per state matrix (D10-v2)
FF_POSSIBLE=0
[[ ${AHEAD_COUNT} -eq 0 ]] && FF_POSSIBLE=1

# Case 1: FF puro (clean or dirty — FF no toca working tree files modificados)
if [[ ${FF_POSSIBLE} -eq 1 ]]; then
  if git merge --ff-only origin/main >/dev/null 2>&1; then
    [[ ${QUIET} -eq 0 ]] && echo "↑ Auto-FF synced ${BEHIND_COUNT} commits from origin/main"
    [[ ${CORE_TOUCHED} -eq 1 ]] && echo "  ⚠ CORE touched — verify nothing broke"
    exit 0
  else
    echo "::error::ff-only merge failed unexpectedly"
    exit 2
  fi
fi

# Case 2: merge real needed (AHEAD > 0)
# Sub-case 2a: tree dirty + merge real → STOP
if [[ ${TREE_DIRTY} -eq 1 ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  SYNC STOP — tree dirty + merge real needed"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Estado: ${SUMMARY}"
  echo ""
  echo "Tree dirty — files modified sin commit:"
  git status --short | head -10
  echo ""
  echo "Acciones recomendadas (elegir UNA):"
  echo "  1. git add <files> && git commit -m 'wip: ...' && scripts/git/sync-from-main.sh"
  echo "  2. git stash && scripts/git/sync-from-main.sh && git stash pop"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi

# Sub-case 2b: tree clean + merge real → attempt merge
[[ ${QUIET} -eq 0 ]] && echo "→ Merging origin/main into ${CURRENT_BRANCH} (real merge, ${SUMMARY})..."
if git merge origin/main --no-edit 2>&1 | tail -5; then
  # Merge OK = sin archivos unmerged (untracked no cuenta — ver TREE_DIRTY arriba)
  if [[ -z "$(git ls-files -u 2>/dev/null)" ]]; then
    [[ ${QUIET} -eq 0 ]] && echo "✓ Auto-merge OK"
    [[ ${CORE_TOUCHED} -eq 1 ]] && echo "  ⚠ CORE touched — verify nothing broke"
    exit 0
  fi
fi

# Sub-case 2c: conflict detected
if [[ -n "$(git ls-files -u 2>/dev/null)" ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  SYNC STOP — merge conflict en ${CURRENT_BRANCH} vs origin/main"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Conflicted files:"
  git diff --name-only --diff-filter=U | head -20
  echo ""
  echo "Acciones:"
  echo "  1. Resolver conflicts manualmente (editar files + git add)"
  echo "  2. git commit (completa merge commit)"
  echo "  3. O abortar: git merge --abort"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi

echo "::error::unexpected state after merge attempt"
exit 2
