#!/usr/bin/env bash
set -euo pipefail
# cleanup-session.sh — Push final + remueve worktree + opcional delete branch (mec. C mejorado)
# SSoT model: docs/process/parallel-sessions-protocol.md § D11 (cleanup post-merge)
#
# Usage:
#   scripts/git/cleanup-session.sh BRAND-SLUG[-LANE]
#   scripts/git/cleanup-session.sh core-SLUG          (D12 — lift core)
#   scripts/git/cleanup-session.sh --delete-branch BRAND-SLUG
#   scripts/git/cleanup-session.sh --force BRAND-SLUG    (skip dirty check, dangerous)
#
# Args:
#   BRAND-SLUG[-LANE]  Identificador del worktree a limpiar (matches branch wip/<arg>)
#                      Para hotfix usar: hotfix/{brand}-{slug} → arg='hotfix-{brand}-{slug}'
#                      O verás flagged como unknown — usar --branch para override
#
# Flags:
#   --delete-branch   Post-cleanup: borra branch local + remota (use AFTER squash-merge a main)
#   --force           Saltea dirty check (no recomendado)
#
# Exit codes:
#   0  Cleanup OK: worktree removido (+ opcional branch deleted)
#   1  Error: arg inválido / worktree no existe / git error
#   2  STOP: worktree tiene cambios uncommitted — no destruye WIP
#
# Behavior:
#   1. Verify worktree exists at expected path
#   2. SAFETY: check tree clean (or --force)
#   3. Push final to origin (best-effort)
#   4. Read manifest .session.yaml para log
#   5. Remove worktree via `git worktree remove`
#   6. If --delete-branch: delete branch local + remote
#   7. Log summary

DELETE_BRANCH=false
FORCE=false
ARG=""
for a in "$@"; do
  case "$a" in
    --delete-branch) DELETE_BRANCH=true ;;
    --force)         FORCE=true ;;
    -*)              echo "::error::Unknown flag: $a"; exit 1 ;;
    *)               ARG="$a" ;;
  esac
done

if [[ -z "${ARG}" ]]; then
  echo "::error::Usage: cleanup-session.sh BRAND-SLUG[-LANE] [--delete-branch] [--force]"
  exit 1
fi

# Sanitize
if [[ ! "${ARG}" =~ ^[a-z0-9-]+$ ]]; then
  echo "::error::Invalid arg '${ARG}' — only [a-z0-9-] allowed"
  exit 1
fi

# Compute branch + worktree path from arg
# Cases:
#   core-SLUG     → branch=wip/core-SLUG path=luana-core-SLUG
#   BRAND-SLUG    → branch=wip/BRAND-SLUG path=luana-BRAND-SLUG
#   BRAND-hotfix-SLUG → branch=hotfix/BRAND-SLUG path=luana-BRAND-hotfix-SLUG
#   BRAND-exp-SLUG    → branch=exp/BRAND-SLUG path=luana-BRAND-exp-SLUG
#   Default: assume wip/<arg> + luana-<arg>
WS_PARENT="$(dirname "$(git rev-parse --show-toplevel)")"

if [[ "${ARG}" =~ ^core-(.+)$ ]]; then
  BRANCH="wip/core-${BASH_REMATCH[1]}"
  WORKTREE_DIR="${WS_PARENT}/luana-${ARG}"
elif [[ "${ARG}" =~ ^([a-z]+)-hotfix-(.+)$ ]]; then
  BRANCH="hotfix/${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
  WORKTREE_DIR="${WS_PARENT}/luana-${ARG}"
elif [[ "${ARG}" =~ ^([a-z]+)-exp-(.+)$ ]]; then
  BRANCH="exp/${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
  WORKTREE_DIR="${WS_PARENT}/luana-${ARG}"
else
  BRANCH="wip/${ARG}"
  WORKTREE_DIR="${WS_PARENT}/luana-${ARG}"
fi

# Verify worktree exists
if [[ ! -d "${WORKTREE_DIR}" ]]; then
  echo "::error::No worktree at ${WORKTREE_DIR}"
  echo "Listing all worktrees:"
  git worktree list
  exit 1
fi

# Safety: dirty check
if ! $FORCE; then
  DIRTY="$(git -C "${WORKTREE_DIR}" status --short 2>/dev/null || true)"
  if [[ -n "${DIRTY}" ]]; then
    echo "::error::Worktree has uncommitted changes:"
    echo "${DIRTY}"
    echo ""
    echo "Run: cd ${WORKTREE_DIR} && git status"
    echo "Stage + commit + push first, then re-run cleanup."
    echo "(Or use --force at your own risk)"
    exit 2
  fi
fi

# STORY CLOSURE GATE — Layer 5 enforcement (post 2026-05-18)
# Verificar que NO hay stories en state developing/developed/reviewing sin defer_audit
# SSoT: .claude/rules/story-closure-gate.md
# Toggle override: CLEANUP_SKIP_STORY_GATE=1 (solo emergencias documentadas)
#
# SCOPE FIX (2026-06-16): el sweep cubre SOLO la marca PROPIA del worktree (de
# .session.yaml::brand, fallback al prefijo del arg). Antes barría TODAS las marcas
# presentes en el filesystem — pero un worktree es checkout del monorepo entero, así que
# un worktree core/protocol veía las copias incidentales de {brand}/docs/product/stories
# (snapshots de main, no trabajo en curso) y se bloqueaba por stories ajenas. Core/protocol/
# platform NO ownan brand-stories → sin sweep.
if [[ "${CLEANUP_SKIP_STORY_GATE:-0}" != "1" ]]; then
  # Marca propia del worktree: manifest autoritativo, fallback al prefijo del arg.
  WT_BRAND=""
  if [[ -f "${WORKTREE_DIR}/.session.yaml" ]]; then
    WT_BRAND="$(grep -E '^brand: ' "${WORKTREE_DIR}/.session.yaml" | head -1 | awk '{print $2}')"
  fi
  [[ -z "${WT_BRAND}" ]] && WT_BRAND="${ARG%%-*}"

  OPEN_STORIES=""
  # Core/protocol/platform no ownan brand-stories → sin sweep (evita falso-positivo cross-brand).
  if [[ "${WT_BRAND}" != "core" && "${WT_BRAND}" != "protocol" && "${WT_BRAND}" != "platform" \
        && -d "${WORKTREE_DIR}/${WT_BRAND}/docs/product/stories" ]]; then
    for cp in "${WORKTREE_DIR}/${WT_BRAND}/docs/product/stories/"*/checkpoint.md; do
      [ -f "$cp" ] || continue
      STORY_ID=$(basename "$(dirname "$cp")")
      STATE=$(grep -E "^state:" "$cp" 2>/dev/null | head -1 | awk '{print $2}' || echo "")
      DEFER=$(grep -E "^defer_audit:" "$cp" 2>/dev/null | awk '{print $2}' || echo "")
      if [[ "$STATE" =~ ^(developing|developed|reviewing)$ ]] && [[ "$DEFER" != "true" ]]; then
        OPEN_STORIES+="  - ${WT_BRAND}/${STORY_ID} (state=${STATE})"$'\n'
      fi
    done
  fi

  if [[ -n "${OPEN_STORIES}" ]]; then
    echo "::error::Story closure gate (Layer 5): no se puede cleanup worktree con stories open."
    echo "Stories en state developing/developed/reviewing sin defer_audit:"
    echo "${OPEN_STORIES}"
    echo "Resolver primero:"
    echo "  - state=developing → /dev-team continua hasta developed"
    echo "  - state=developed  → /auditor toma (auto-handoff)"
    echo "  - state=reviewing  → esperar APPROVED + /pm-{brand} merge"
    echo "  - O ratificar defer_audit:true en checkpoint con razon documentada"
    echo "SSoT: .claude/rules/story-closure-gate.md"
    echo ""
    echo "Override (emergencias): CLEANUP_SKIP_STORY_GATE=1 scripts/git/cleanup-session.sh ${ARG}"
    exit 2
  fi
fi

# Read manifest for log
STORY="—"
MANIFEST="${WORKTREE_DIR}/.session.yaml"
if [[ -f "${MANIFEST}" ]]; then
  STORY="$(grep -E '^story_id: ' "${MANIFEST}" | head -1 | sed 's/^story_id: //')"
fi

# Push final (dry-run si GIT_PUSH_DRY_RUN=1, para tests)
echo "→ Pushing ${BRANCH} (final push before cleanup)..."
if [[ "${GIT_PUSH_DRY_RUN:-0}" = "1" ]]; then
  echo "  (dry-run skipped actual push)"
else
  if git -C "${WORKTREE_DIR}" push origin "${BRANCH}" --set-upstream 2>/dev/null; then
    echo "  ✓ pushed"
  elif git -C "${WORKTREE_DIR}" push origin "${BRANCH}" 2>/dev/null; then
    echo "  ✓ pushed (already upstream)"
  else
    echo "  ⚠ push failed (branch may already be up-to-date)"
  fi
fi

# Remove worktree
echo "→ Removing worktree ${WORKTREE_DIR}..."
git worktree remove "${WORKTREE_DIR}"
echo "  ✓ removed"

# Optional branch delete
if $DELETE_BRANCH; then
  echo "→ Deleting branch ${BRANCH} (local + remote)..."
  git branch -D "${BRANCH}" 2>/dev/null || echo "  ⚠ local branch delete failed"
  if [[ "${GIT_PUSH_DRY_RUN:-0}" != "1" ]]; then
    git push origin --delete "${BRANCH}" 2>/dev/null || echo "  ⚠ remote delete failed (maybe already deleted)"
  fi
fi

echo ""
echo "✓ Cleanup complete"
echo "  worktree: ${WORKTREE_DIR} removed"
echo "  branch:   ${BRANCH} $($DELETE_BRANCH && echo 'DELETED' || echo 'preserved (cron purge >30d)')"
echo "  story:    ${STORY}"
