#!/usr/bin/env bash
set -euo pipefail
# check-sync.sh — T1/T2 sync logic portable (mec. A logic + invoked manually for opencode)
# SSoT model: docs/process/parallel-sessions-protocol.md § D10 + D13
#
# Usage:
#   scripts/git/check-sync.sh                    # full check + actions per D10
#   scripts/git/check-sync.sh --detect-only      # solo detect worktree, print context, NO sync
#   scripts/git/check-sync.sh --silent           # output only if action needed
#
# Behavior:
#   - PRINCIPAL (luana-platform/ en main):
#       git fetch origin main && git merge --ff-only origin/main  (silent if OK, advisory if FF fails)
#   - CANÓNICO (luana-{brand}/ en wip/{brand}-*):
#       Tree clean + FF posible → AUTO FF + info line
#       Tree clean + merge real → advisory only
#       Tree dirty + core changed → banner LOUD
#       Tree dirty + non-core changes → advisory soft
#   - EFÍMERO (brand or core):
#       NO sync auto. Detection + output context only.
#   - UNKNOWN:
#       advisory + escalate
#
# Updates .session.yaml.last_sync block (if manifest exists).
# Exit codes:
#   0  OK (action taken or no action needed)
#   1  Error (cannot detect, fetch failed, ...)

DETECT_ONLY=false
SILENT=false
for arg in "$@"; do
  case "$arg" in
    --detect-only) DETECT_ONLY=true ;;
    --silent)      SILENT=true ;;
    *) echo "::error::Unknown arg: $arg"; exit 1 ;;
  esac
done

log() {
  $SILENT && return 0
  echo "$@"
}

# Detect cwd worktree type
CWD="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${CWD}" ]]; then
  echo "::error::not in git repo"
  exit 1
fi
BASENAME="$(basename "${CWD}")"

# Parse type
WORKTREE_TYPE=""
WORKTREE_BRAND=""
WORKTREE_SLUG=""
# Brand enum from the seam (project.config.yaml · harness_config.py) — no hardcoded list
# (charter §3 DIP · W5b 2026-06-09). Loud-degrade to empty if unreadable (the config ships
# with the kit; empty degrades brand-detection rather than asserting a stale enum).
KNOWN_BRANDS="$("${CWD}/.venv/bin/python" "${CWD}/scripts/harness_config.py" brands.loop_order 2>/dev/null | tr '\n' ' ')"
[ -z "${KNOWN_BRANDS}" ] && echo "WARN: project.config.yaml brands.loop_order unreadable — brand detection degraded" >&2

if [[ "${BASENAME}" = "luana-platform" ]]; then
  WORKTREE_TYPE="PRINCIPAL"
elif [[ "${BASENAME}" =~ ^luana-core-(.+)$ ]]; then
  WORKTREE_TYPE="EPHEMERAL_CORE"
  WORKTREE_BRAND="core"
  WORKTREE_SLUG="${BASH_REMATCH[1]}"
elif [[ "${BASENAME}" =~ ^luana-([a-z]+)$ ]]; then
  BRAND="${BASH_REMATCH[1]}"
  if echo " ${KNOWN_BRANDS} " | grep -q " ${BRAND} "; then
    WORKTREE_TYPE="CANONICAL"
    WORKTREE_BRAND="${BRAND}"
  else
    WORKTREE_TYPE="UNKNOWN"
  fi
elif [[ "${BASENAME}" =~ ^luana-([a-z]+)-(.+)$ ]]; then
  BRAND="${BASH_REMATCH[1]}"
  SLUG="${BASH_REMATCH[2]}"
  if echo " ${KNOWN_BRANDS} " | grep -q " ${BRAND} "; then
    WORKTREE_TYPE="EPHEMERAL_BRAND"
    WORKTREE_BRAND="${BRAND}"
    WORKTREE_SLUG="${SLUG}"
  else
    WORKTREE_TYPE="UNKNOWN"
  fi
else
  WORKTREE_TYPE="UNKNOWN"
fi

BRANCH="$(git branch --show-current 2>/dev/null || echo '<detached>')"

log "[step 0 worktree]"
log "  path:     ${CWD}"
log "  branch:   ${BRANCH}"
log "  type:     ${WORKTREE_TYPE}${WORKTREE_BRAND:+ ${WORKTREE_BRAND}}${WORKTREE_SLUG:+ ${WORKTREE_SLUG}}"

# Manifest
MANIFEST="${CWD}/.session.yaml"
if [[ -f "${MANIFEST}" ]]; then
  # Light parse — only what we need
  M_BRAND="$(grep -E '^brand: ' "${MANIFEST}" | head -1 | sed 's/^brand: //')"
  M_STORY="$(grep -E '^story_id: ' "${MANIFEST}" | head -1 | sed 's/^story_id: //')"
  M_LANE="$(grep -E '^lane: ' "${MANIFEST}" | head -1 | sed 's/^lane: //')"
  log "  manifest: brand=${M_BRAND} story=${M_STORY:-—} lane=${M_LANE:-—}"
  # Coherence check
  if [[ -n "${WORKTREE_BRAND}" && "${M_BRAND}" != "${WORKTREE_BRAND}" ]]; then
    log "  ⚠ COHERENCE: manifest brand=${M_BRAND} but path implies ${WORKTREE_BRAND}"
  fi
elif [[ "${WORKTREE_TYPE}" != "PRINCIPAL" && "${WORKTREE_TYPE}" != "UNKNOWN" ]]; then
  log "  manifest: ABSENT — regenerar con scripts/git/regenerate-manifest.sh (mec. M)"
fi

if $DETECT_ONLY; then
  log "[step 0 detect-only OK]"
  exit 0
fi

# Sync logic
if [[ "${WORKTREE_TYPE}" = "UNKNOWN" ]]; then
  log "  sync:     skipped (UNKNOWN type)"
  log "[step 0 advisory — escalate Chris]"
  exit 0
fi

# Fetch
if ! git fetch origin main --quiet 2>/dev/null; then
  log "  sync:     ✗ fetch origin main failed"
  exit 1
fi

ORIGIN_SHA="$(git rev-parse origin/main)"

# PRINCIPAL: FF only on main
if [[ "${WORKTREE_TYPE}" = "PRINCIPAL" ]]; then
  if git merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    BEHIND="$(git rev-list --count HEAD..origin/main)"
    if [[ "${BEHIND}" = "0" ]]; then
      log "  sync:     ✓ already up-to-date"
    else
      if git merge --ff-only origin/main --quiet 2>/dev/null; then
        log "  sync:     ↑ FF synced ${BEHIND} commits from origin/main"
      else
        log "  sync:     ✗ FF failed (uncommitted changes?)"
      fi
    fi
  else
    log "  sync:     ⚠ main has diverged — local commits not in origin/main (raro, escalate)"
  fi
  log "[step 0 OK]"
  exit 0
fi

# EPHEMERAL (brand or core): no sync auto, just info
if [[ "${WORKTREE_TYPE}" = "EPHEMERAL_BRAND" || "${WORKTREE_TYPE}" = "EPHEMERAL_CORE" ]]; then
  BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
  AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
  log "  sync:     ↑ ${BEHIND} behind, ↓ ${AHEAD} ahead origin/main (no auto-sync en efímeros)"
  log "[step 0 OK]"
  exit 0
fi

# CANONICAL: T1 logic per D10
if [[ "${WORKTREE_TYPE}" = "CANONICAL" ]]; then
  # Tree state
  if git diff --quiet && git diff --cached --quiet; then
    TREE_DIRTY=false
  else
    TREE_DIRTY=true
  fi

  BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
  AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"

  # Detect "touches core"
  CORE_TOUCHED=false
  if [[ "${BEHIND}" -gt 0 ]]; then
    CORE_CHANGES="$(git diff HEAD..origin/main --name-only 2>/dev/null | grep -E '^core/luana-core-[^/]+/src/' || true)"
    if [[ -n "${CORE_CHANGES}" ]]; then
      CORE_TOUCHED=true
    fi
  fi

  if [[ "${BEHIND}" = "0" ]]; then
    log "  sync:     ✓ already up-to-date with origin/main"
  elif ! $TREE_DIRTY && [[ "${AHEAD}" = "0" ]]; then
    # FF puro posible
    if git merge --ff-only origin/main --quiet 2>/dev/null; then
      core_label=""
      $CORE_TOUCHED && core_label=" (⚠ touches core)"
      log "  sync:     ↑ AUTO FF synced ${BEHIND} commits from origin/main${core_label}"
    else
      log "  sync:     ✗ FF unexpectedly failed"
    fi
  elif ! $TREE_DIRTY; then
    # Tree clean pero merge real (ahead > 0)
    log "  sync:     ↑ ${BEHIND} behind, ↓ ${AHEAD} ahead — merge required (advisory only)"
    log "            Mergeá cuando estés listo:"
    log "            $ git fetch origin main && git merge origin/main"
  elif $TREE_DIRTY && $CORE_TOUCHED; then
    # Tree dirty + core changed → LOUD
    log "  sync:     ${BEHIND} commits behind, tree dirty"
    log ""
    log "  ╔═══ CORE CHANGED while you worked ═══════════════╗"
    log "  ║ commits behind: ${BEHIND}                                ║"
    log "  ║ affected: core/luana-core-* (ver git diff)       ║"
    log "  ║ Recomendado: terminar WIP, push, mergear         ║"
    log "  ╚══════════════════════════════════════════════════╝"
  else
    # Tree dirty + non-core
    log "  sync:     ${BEHIND} commits behind, tree dirty — mergear cuando esté limpio"
  fi

  # Update .session.yaml.last_sync if manifest exists
  if [[ -f "${MANIFEST}" ]]; then
    NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    # Best-effort sed (no-op if section missing)
    sed -i.bak \
      -e "s|^  fetched_at: .*|  fetched_at: ${NOW}|" \
      -e "s|^  origin_main_sha: .*|  origin_main_sha: ${ORIGIN_SHA}|" \
      -e "s|^  commits_pulled: .*|  commits_pulled: ${BEHIND}|" \
      -e "s|^  core_touched: .*|  core_touched: ${CORE_TOUCHED}|" \
      "${MANIFEST}" 2>/dev/null && rm -f "${MANIFEST}.bak" 2>/dev/null
  fi

  log "[step 0 OK]"
  exit 0
fi

exit 0
