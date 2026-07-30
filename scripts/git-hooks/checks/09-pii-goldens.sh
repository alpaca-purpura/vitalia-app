# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 9. PII scan on staged goldens YAMLs (Story D — synthetic-first ground truth)
# (refactor 2026-05-15 post multibrand reorg — per-brand goldens dirs)
# Gate: FULL only (wip/* branches skip — PII scan is a final-commit quality gate)
# ─────────────────────────────────────────────────────────────────
# Activates si hay YAMLs staged en:
#   - backend/tests/agentic_evals/sales_agent/goldens/          (legacy)
#   - {brand}/backend/tests/agentic_evals/sales_agent/goldens/  (per-brand)
#
# Para cada path detectado se invoca scan_goldens_pii.py contra el
# directorio completo correspondiente.
#
# Strict block — NO whitelist (spec D10). Synthetic-first invariant:
# all PII in goldens is a bug, no legitimate exceptions.
#
# Scanner path: scripts/scan_goldens_pii.py (workspace, multibrand — HB-18 2026-06-01).
# Legacy fallback: backend/scripts/scan_goldens_pii.py. Si ninguno existe → warning + skip.
#
# Scanner exit codes: 0=clean, 1=PII detected, 2=error.
# Bypass: NEVER use --no-verify.

if [ "${GATE_LEVEL}" = "full" ]; then

STAGED_GOLDEN_YAMLS=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '^([a-z][a-z0-9_-]*/)?backend/tests/agentic_evals/sales_agent/goldens/.*\.yaml$' \
  || true)

if [ -n "${STAGED_GOLDEN_YAMLS}" ]; then
  # Prefer root venv (uv workspace), fallback legacy backend venv
  if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/.venv/bin/python"
  elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/backend/.venv/bin/python"
  else
    VENV_PY=""
  fi

  # Resolver scanner: scripts/ (workspace, multibrand HB-18) primero, legacy fallback.
  if [ -f "${REPO_ROOT}/scripts/scan_goldens_pii.py" ]; then
    GOLDEN_SCANNER_PY="${REPO_ROOT}/scripts/scan_goldens_pii.py"
  elif [ -f "${REPO_ROOT}/backend/scripts/scan_goldens_pii.py" ]; then
    GOLDEN_SCANNER_PY="${REPO_ROOT}/backend/scripts/scan_goldens_pii.py"
  else
    GOLDEN_SCANNER_PY=""
  fi

  if [ -z "${VENV_PY}" ]; then
    printf "\033[33m"
    echo "WARNING: venv not found (.venv ni backend/.venv) — skipping PII goldens scan (Section 9)."
    printf "\033[0m"
  elif [ -z "${GOLDEN_SCANNER_PY}" ]; then
    printf "\033[33m"
    echo "WARNING: scan_goldens_pii.py not found en scripts/ ni backend/scripts/ — skipping (Section 9)."
    printf "\033[0m"
  else
    # Derivar dirs a scanear desde paths staged (uno por brand + legacy raíz).
    GOLDENS_DIRS_TO_SCAN=$(echo "${STAGED_GOLDEN_YAMLS}" \
      | sed -E 's|(.*backend/tests/agentic_evals/sales_agent/goldens)/.*|\1|' \
      | sort -u)

    GOLDEN_SCAN_FAILED=0
    GOLDEN_ERROR_OUTPUT=""
    while IFS= read -r GOLDENS_DIR; do
      [ -z "${GOLDENS_DIR}" ] && continue
      if [ ! -d "${REPO_ROOT}/${GOLDENS_DIR}" ]; then
        continue
      fi
      if ! "${VENV_PY}" "${GOLDEN_SCANNER_PY}" "${REPO_ROOT}/${GOLDENS_DIR}" 2>/tmp/pii-goldens-err.txt; then
        GOLDEN_SCAN_FAILED=1
        GOLDEN_ERROR_OUTPUT+="── ${GOLDENS_DIR}/ ──"$'\n'
        GOLDEN_ERROR_OUTPUT+="$(cat /tmp/pii-goldens-err.txt 2>/dev/null || true)"$'\n\n'
      fi
    done <<< "${GOLDENS_DIRS_TO_SCAN}"

    if [ "${GOLDEN_SCAN_FAILED}" -eq 1 ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: PII detected in goldens/ — strict block (multibrand).
─────────────────────────────────────────────────────────────
Synthetic-first invariant: zero PII en golden YAMLs (spec D10).
NO whitelist disponible para goldens.

Dirs scanned:
${GOLDENS_DIRS_TO_SCAN}

Errors:
${GOLDEN_ERROR_OUTPUT}

Resolución:
  1. Reemplaza PII real con equivalentes sintéticos (nombres como
     "Cliente Ejemplo", teléfono "+99 0 1234 5678", email "usuario@example.com").
  2. O elimina el golden y regénéralo con generate_golden_candidates.py
     (path scoped a {brand}/backend/scripts/ o root backend/scripts/ según
     dónde viva el script para esa brand).

NEVER use --no-verify (.claude/rules/git-safety.md prohibits).
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

fi  # end GATE_LEVEL=full guard (section 9)

