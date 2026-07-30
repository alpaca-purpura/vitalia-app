# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 5. R32 capability ↔ story status freshness (origen 2026-05-05) — MULTIBRAND
# (refactor 2026-05-15 post multibrand reorg, --brand flag wired 2026-05-15)
# Gate: FULL only (wip/* branches skip — capability reconciliation may
# produce false positives on in-progress stories)
# ─────────────────────────────────────────────────────────────────
# Capability YAML at {brand}/docs/product/capabilities/{m}/{c}.yaml (per-brand)
# o docs/product/capabilities/{m}/{c}.yaml (platform/legacy) carries derived
# fields (status, stories_live, stories_planned, stories_total) que MUST stay
# synced con stories referenced.
#
# Trigger: any staged change touching:
#   - docs/product/{capabilities,stories}/             (platform/legacy)
#   - {brand}/docs/product/{capabilities,stories}/     (per-brand)
#
# Action por trigger:
#   - Path raíz docs/product/... → reconciler sin flag (legacy/platform behavior).
#   - Path {brand}/docs/product/... → reconciler con `--brand {brand}` (multibrand).

if [ "${GATE_LEVEL}" = "full" ]; then

PRODUCT_TOUCHED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
  | grep -E '^(docs/product|[a-z][a-z0-9_-]*/docs/product)/(capabilities|stories)/' \
  || true)

if [ -n "${PRODUCT_TOUCHED}" ]; then
  RECONCILER="${REPO_ROOT}/scripts/reconcile_capabilities.py"
  # Prefer root venv (uv workspace), fallback legacy backend venv
  if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/.venv/bin/python"
  elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/backend/.venv/bin/python"
  else
    VENV_PY=""
  fi

  # Detectar si hay paths per-brand vs raíz para invocar correctamente.
  BRAND_PATHS_TOUCHED=$(echo "${PRODUCT_TOUCHED}" \
    | grep -E '^[a-z][a-z0-9_-]*/docs/product/' \
    | cut -d/ -f1 | sort -u || true)
  ROOT_PATHS_TOUCHED=$(echo "${PRODUCT_TOUCHED}" \
    | grep -E '^docs/product/' || true)

  if [ -n "${VENV_PY}" ] && [ -f "${RECONCILER}" ]; then
    # Caso 1: paths raíz docs/product/ → invocar reconciler legacy (sin --brand).
    if [ -n "${ROOT_PATHS_TOUCHED}" ]; then
      if ! "${VENV_PY}" "${RECONCILER}" --check >/tmp/reconcile-out.txt 2>&1; then
        printf "\033[31m"
        cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: R32 capability status drift (platform/legacy)
─────────────────────────────────────────────────────────────
You're staging changes under docs/product/{capabilities,stories}/ but the
capability YAML derived fields (status, stories_live, stories_planned,
stories_total) no longer match the referenced stories.

Drift detail:
$(cat /tmp/reconcile-out.txt)

Resolution:
  python scripts/reconcile_capabilities.py
  git add docs/product/capabilities/
  git commit ...

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
        exit 1
      fi
    fi

    # Caso 2: paths per-brand → invocar reconciler con --brand per cada brand.
    if [ -n "${BRAND_PATHS_TOUCHED}" ]; then
      while IFS= read -r BRAND; do
        [ -z "${BRAND}" ] && continue
        if ! "${VENV_PY}" "${RECONCILER}" --check --brand "${BRAND}" >/tmp/reconcile-${BRAND}.txt 2>&1; then
          printf "\033[31m"
          cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: R32 capability status drift (brand: ${BRAND})
─────────────────────────────────────────────────────────────
You're staging changes under ${BRAND}/docs/product/{capabilities,stories}/
but the capability YAML derived fields (status, stories_live,
stories_planned, stories_total) no longer match the referenced stories.

Drift detail:
$(cat /tmp/reconcile-${BRAND}.txt)

Resolution:
  python scripts/reconcile_capabilities.py --brand ${BRAND}
  git add ${BRAND}/docs/product/capabilities/
  git commit ...

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
          printf "\033[0m"
          exit 1
        fi
      done <<< "${BRAND_PATHS_TOUCHED}"
    fi
  else
    printf "\033[33m"
    echo "WARNING: skipping R32 reconciler — venv or script missing."
    printf "\033[0m"
  fi
fi

fi  # end GATE_LEVEL=full guard (section 5)

