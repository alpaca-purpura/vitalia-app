#!/usr/bin/env bash
set -euo pipefail
# push-wip.sh — T-push pre-push sync check + push portable (mec. L logic + opencode/manual)
# SSoT model: docs/process/parallel-sessions-protocol.md § D10 (T-push)
#
# Usage:
#   scripts/git/push-wip.sh                      # push current branch
#   scripts/git/push-wip.sh wip/vitalia-X        # push specific branch
#   scripts/git/push-wip.sh --check-only         # solo check, no push (Claude PreToolUse use case)
#
# Behavior:
#   1. Verify current branch is wip/* or hotfix/* or exp/* (not main)
#   2. Fetch origin main
#   3. Check if origin/main moved (count commits behind)
#   4. Advisory if behind (label CORE si delta toca core/luana-core-*/)
#   5. Push current branch (NOT main — per regla M5 nunca push main directo desde wip)
#
# Does NOT block push. Advisory only. Regla M5 sigue: si remoto rechaza non-fast-forward → STOP.

BRANCH_ARG="${1:-}"
CHECK_ONLY=false

if [[ "${BRANCH_ARG}" = "--check-only" ]]; then
  CHECK_ONLY=true
  BRANCH_ARG=""
fi

CURRENT="$(git branch --show-current)"
TARGET="${BRANCH_ARG:-${CURRENT}}"

# Validate target is wip/* | hotfix/* | exp/* — NUNCA main from this script
case "${TARGET}" in
  wip/*|hotfix/*|exp/*) ;;
  main)
    echo "::error::push-wip.sh NUNCA pushea main directamente. Squash-merge desde principal vía /pm-{brand}."
    exit 1
    ;;
  *)
    echo "::error::target '${TARGET}' no es wip/*, hotfix/* o exp/*"
    exit 1
    ;;
esac

# Fetch origin main
echo "→ Fetching origin main..."
git fetch origin main --quiet

# Behind analysis
BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"

if [[ "${BEHIND}" -gt 0 ]]; then
  CORE_TOUCHED="$(git diff HEAD..origin/main --name-only 2>/dev/null | grep -cE '^core/luana-core-[^/]+/src/' || echo 0)"
  DEPS_TOUCHED="$(git diff HEAD..origin/main --name-only 2>/dev/null | grep -cE 'core/luana-core-[^/]+/(pyproject\.toml|package\.json)$' || echo 0)"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  PUSH BLOCKED (v2 sync KISS cementado 2026-05-18) — rama behind main"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Estado: ${BEHIND} commits behind origin/main"
  if [[ "${CORE_TOUCHED}" -gt 0 ]]; then
    echo "  ⚠ ${CORE_TOUCHED} archivos en core/luana-core-*/src/ cambiaron"
  fi
  if [[ "${DEPS_TOUCHED}" -gt 0 ]]; then
    echo "  ⚠ deps changed → considerá 'uv sync' (Python) o 'pnpm install' (TS)"
  fi
  echo ""
  echo "Acción requerida ANTES de push (regla v2 D10):"
  echo "  git fetch origin main && git merge origin/main"
  echo ""
  echo "Override (emergencias documentadas):"
  echo "  PUSH_WIP_SKIP_SYNC=1 scripts/git/push-wip.sh ${TARGET}"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ "${PUSH_WIP_SKIP_SYNC:-0}" != "1" ]]; then
    exit 1
  fi
  echo ""
  echo "  ⚠ Override PUSH_WIP_SKIP_SYNC=1 — proceeding pero riesgo conflict a tu cargo"
  echo ""
fi

if $CHECK_ONLY; then
  exit 0
fi

# Push
echo "→ Pushing ${TARGET} to origin..."
if git push origin "${TARGET}"; then
  SHA="$(git rev-parse HEAD)"
  echo "✓ pushed ${TARGET} @ ${SHA:0:7}"
  exit 0
else
  echo ""
  echo "::error::push rejected (likely non-fast-forward)"
  echo "  STOP — regla M5 prohíbe git pull. Acciones posibles:"
  echo "  1. git fetch origin main && git merge origin/main (mergear cambios upstream a tu wip)"
  echo "  2. escalate a Chris si el rechazo es inesperado"
  exit 2
fi
