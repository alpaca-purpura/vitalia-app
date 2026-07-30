# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 5d. Bidirectional validator advisory (cement 2026-05-28 · Fase B)
# ─────────────────────────────────────────────────────────────────
# Runs `validate_code_cap_bidirectional.py --brand {brand}` cuando archivos
# de código (.py/.ts/.tsx) O cap YAMLs son staged. Output advisory only.
#
# HARD pre-push enforce vive en scripts/git-hooks/pre-push (Section 4d).
#
# Behavior:
#   Advisory (never blocks): regenera _bidirectional-validation.json silente.
#   Si detecta drift en cross_check_3 (scenario→e2e_test, HARD) o cross_check_4
#   (access roles ↔ PHI, advisory), imprime warning con caps afectados.
#
# Override:
#   * env: BIDIRECTIONAL_SKIP=1 git commit ...
#
# SSoT: docs/process/capability-protocol.md § Sección 13 (cement 2026-05-28)
# ─────────────────────────────────────────────────────────────────

if [ "${BIDIRECTIONAL_SKIP:-0}" != "1" ]; then

  # Trigger: any code file OR cap YAML staged
  BIDIR_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/(backend|frontend)/src/.*\.(py|ts|tsx)$|^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/docs/product/capabilities/[^/]+/[^/]+\.yaml$' \
    || true)

  if [ -n "${BIDIR_STAGED}" ]; then
    BRANDS_BIDIR=$(echo "${BIDIR_STAGED}" | cut -d/ -f1 | sort -u)

    BIDIR_SCRIPT="${REPO_ROOT}/scripts/validate_code_cap_bidirectional.py"
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      VENV_BIDIR="${REPO_ROOT}/.venv/bin/python"
    elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
      VENV_BIDIR="${REPO_ROOT}/backend/.venv/bin/python"
    else
      VENV_BIDIR=""
    fi

    if [ -n "${VENV_BIDIR}" ] && [ -f "${BIDIR_SCRIPT}" ]; then
      while IFS= read -r B_BIDIR; do
        [ -z "${B_BIDIR}" ] && continue

        BIDIR_OUT=$("${VENV_BIDIR}" "${BIDIR_SCRIPT}" --brand "${B_BIDIR}" 2>&1 || true)
        BIDIR_VERDICT=$(echo "${BIDIR_OUT}" | grep -oE 'Verdict: \w+' | head -1 | sed 's/Verdict: //')

        if [ "${BIDIR_VERDICT}" = "HARD_FAIL" ] || [ "${BIDIR_VERDICT}" = "SOFT_DRIFT" ]; then
          printf "\033[33m"
          echo ""
          echo "[5d] Bidirectional validator advisory · ${B_BIDIR} · verdict=${BIDIR_VERDICT}"
          echo "${BIDIR_OUT}" | grep -E "drift=|Drift" | head -5 | sed 's/^/  /'
          echo ""
          if [ "${BIDIR_VERDICT}" = "HARD_FAIL" ]; then
            echo "  ⚠ HARD checks failing (cross_check_3 scenario→e2e_test)"
            echo "  Pre-push hook bloqueará push a main/release/* si HARD persiste."
          fi
          echo "  Detalle: ${B_BIDIR}/docs/product/capabilities/_bidirectional-validation.json"
          printf "\033[0m"
        fi
      done <<< "${BRANDS_BIDIR}"
    fi
  fi

fi  # end BIDIRECTIONAL_SKIP guard (section 5d)

