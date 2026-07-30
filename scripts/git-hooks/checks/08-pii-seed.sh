# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 8. PII scan on staged eval seed YAMLs (origen T-2 eval-foundation-tenant-seed-data)
# (refactor 2026-05-15 post multibrand reorg — per-brand seed dirs)
# Gate: FULL only (wip/* branches skip — PII scan is a final-commit quality gate)
# ─────────────────────────────────────────────────────────────────
# Activates si hay YAML files staged en:
#   - backend/tests/fixtures/eval/tenants/            (legacy single-target)
#   - {brand}/backend/tests/fixtures/eval/tenants/    (per-brand)
#
# Para cada path detectado se invoca scan_seed_pii.py contra el directorio
# completo correspondiente (no solo el diff), para catch PII en archivos
# que cambiaron previamente clean.
#
# Scanner path: scripts/scan_seed_pii.py (workspace, multibrand — HB-18 2026-06-01).
# Legacy fallback: backend/scripts/scan_seed_pii.py. Si ninguno existe → warning + skip.
#
# Scanner exit codes: 0=clean, 1=PII detected, 2=error.
# Bypass: NEVER use --no-verify. Whitelist por brand:
#   {brand_or_root}/backend/tests/fixtures/eval/tenants/.eval-whitelist

if [ "${GATE_LEVEL}" = "full" ]; then

STAGED_SEED_YAMLS=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '^([a-z][a-z0-9_-]*/)?backend/tests/fixtures/eval/tenants/.*\.yaml$' \
  || true)

if [ -n "${STAGED_SEED_YAMLS}" ]; then
  # Prefer root venv (uv workspace), fallback legacy backend venv
  if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/.venv/bin/python"
  elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/backend/.venv/bin/python"
  else
    VENV_PY=""
  fi

  # Resolver scanner: scripts/ (workspace, multibrand HB-18) primero, legacy fallback.
  if [ -f "${REPO_ROOT}/scripts/scan_seed_pii.py" ]; then
    SCANNER_PY="${REPO_ROOT}/scripts/scan_seed_pii.py"
  elif [ -f "${REPO_ROOT}/backend/scripts/scan_seed_pii.py" ]; then
    SCANNER_PY="${REPO_ROOT}/backend/scripts/scan_seed_pii.py"
  else
    SCANNER_PY=""
  fi

  if [ -z "${VENV_PY}" ]; then
    printf "\033[33m"
    echo "WARNING: venv not found (.venv ni backend/.venv) — skipping PII scan (Section 8)."
    printf "\033[0m"
  elif [ -z "${SCANNER_PY}" ]; then
    printf "\033[33m"
    echo "WARNING: scan_seed_pii.py not found en scripts/ ni backend/scripts/ — skipping PII scan (Section 8)."
    printf "\033[0m"
  else
    # Derivar dirs a scanear desde paths staged (uno por brand + legacy raíz).
    SEED_DIRS_TO_SCAN=$(echo "${STAGED_SEED_YAMLS}" \
      | sed -E 's|(.*backend/tests/fixtures/eval/tenants)/.*|\1|' \
      | sort -u)

    SCAN_FAILED=0
    SCAN_ERROR_OUTPUT=""
    while IFS= read -r SEED_DIR; do
      [ -z "${SEED_DIR}" ] && continue
      if [ ! -d "${REPO_ROOT}/${SEED_DIR}" ]; then
        continue
      fi
      if ! "${VENV_PY}" "${SCANNER_PY}" "${REPO_ROOT}/${SEED_DIR}" 2>/tmp/pii-scan-err.txt; then
        SCAN_FAILED=1
        SCAN_ERROR_OUTPUT+="── ${SEED_DIR}/ ──"$'\n'
        SCAN_ERROR_OUTPUT+="$(cat /tmp/pii-scan-err.txt 2>/dev/null || true)"$'\n\n'
      fi
    done <<< "${SEED_DIRS_TO_SCAN}"

    if [ "${SCAN_FAILED}" -eq 1 ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: PII detected in seed/ — commit blocked (multibrand).
─────────────────────────────────────────────────────────────
Dirs scanned:
${SEED_DIRS_TO_SCAN}

Errors:
${SCAN_ERROR_OUTPUT}

Resolution:
  1. Replace real PII con synthetic equivalents (e.g., +99 0 1234 5678 for phones,
     user@example.com for emails, fake ID numbers).
  2. Si el flagged value es legitimate public reference, agregar a
     {brand_or_root}/backend/tests/fixtures/eval/tenants/.eval-whitelist
     con justificación.

NEVER use --no-verify (.claude/rules/git-safety.md prohibits).
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

fi  # end GATE_LEVEL=full guard (section 8)

