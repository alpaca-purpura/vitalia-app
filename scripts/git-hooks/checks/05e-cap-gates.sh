# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 5e. cap-format gates G1-G6 HARD (HB-51 · enforcement determinístico)
# ─────────────────────────────────────────────────────────────────
# Bloquea el commit si un brand MADURO (vitalia · comunify) tiene deriva en los
# gates determinísticos de formato/estado de caps (G1 header-resuelve · G2 área-
# viva-tiene-cap · G3 cap-tiene-hogar · G4 paths-existen · G5 superseded-válido ·
# G6 map-coverage). nicolify/lupulo quedan ADVISORY (mid-rebuild / placeholder) —
# su deriva la muestra la sección 5d. Backfill hecho 2026-06-05 (cap-doctor 0).
#
# Trigger: code (.py/.ts/.tsx) O cap YAML O SYSTEM-MAP staged de un brand HARD.
# Override (audit): CAP_GATES_SKIP=1 git commit ...
# SSoT: docs/process/cap-deterministic-enforcement.md (Capa 4)
# ─────────────────────────────────────────────────────────────────

# HARD-cap-gate brands from the seam (project.config.yaml · brands.active where cap_gate=hard)
# — no hardcoded enum (charter §3 DIP · W5b). Adding a brand's gate policy = config, not code.
# Both the path pre-filter (regex) AND the per-brand gate check derive from this one set.
CAP_GATES_HARD_BRANDS="$("${REPO_ROOT}/.venv/bin/python" "${REPO_ROOT}/scripts/harness_config.py" brands.active slug --where cap_gate=hard 2>/dev/null | tr '\n' ' ')"
CAPG_HARD_RE="$(echo "${CAP_GATES_HARD_BRANDS}" | tr -s ' ' '|' | sed 's/^|//;s/|$//')"
[ -z "${CAPG_HARD_RE}" ] && echo "WARN: project.config.yaml HARD cap-gate brands unreadable — cap-gate enforcement skipped (advisory degrade)" >&2

if [ "${CAP_GATES_SKIP:-0}" != "1" ] && [ -n "${CAPG_HARD_RE}" ]; then
  CAPG_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep -E "^(${CAPG_HARD_RE})/(backend|frontend)/src/.*\.(py|ts|tsx)$|^(${CAPG_HARD_RE})/docs/product/capabilities/[^/]+/[^/]+\.yaml$|^(${CAPG_HARD_RE})/docs/architecture/SYSTEM-MAP\.yaml$" \
    || true)

  if [ -n "${CAPG_STAGED}" ]; then
    BRANDS_CAPG=$(echo "${CAPG_STAGED}" | cut -d/ -f1 | sort -u)
    CAPG_SCRIPT="${REPO_ROOT}/scripts/validate_code_cap_bidirectional.py"
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      VENV_CAPG="${REPO_ROOT}/.venv/bin/python"
    elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
      VENV_CAPG="${REPO_ROOT}/backend/.venv/bin/python"
    else
      VENV_CAPG=""
    fi

    if [ -n "${VENV_CAPG}" ] && [ -f "${CAPG_SCRIPT}" ]; then
      CAPG_FAILED=""
      while IFS= read -r B_CAPG; do
        [ -z "${B_CAPG}" ] && continue
        case " ${CAP_GATES_HARD_BRANDS} " in *" ${B_CAPG} "*) ;; *) continue ;; esac
        if ! "${VENV_CAPG}" "${CAPG_SCRIPT}" --brand "${B_CAPG}" --cap-gates-hard --strict >/dev/null 2>&1; then
          CAPG_FAILED="${CAPG_FAILED} ${B_CAPG}"
        fi
      done <<< "${BRANDS_CAPG}"

      if [ -n "${CAPG_FAILED}" ]; then
        printf "\033[31m"
        echo "─────────────────────────────────────────────────────────────"
        echo "COMMIT BLOCKED: cap-format gates G1-G6 HARD drift (HB-51)"
        echo "  Brands con deriva:${CAPG_FAILED}"
        echo ""
        echo "  Diagnóstico de un vistazo:"
        echo "    make cap-doctor BRAND=<brand>"
        echo "  Detalle:"
        echo "    python3 scripts/validate_code_cap_bidirectional.py --brand <brand> --cap-gates-hard --strict"
        echo ""
        echo "  Causas típicas: header \`# cap:\` → cap inexistente (G1) · caja live"
        echo "  vacía (G2) · path declarado inexistente (G4) · supersesión rota (G5)."
        echo "  Cap nueva → \`make new-cap\` (NUNCA hand-author el YAML)."
        echo ""
        echo "  Override emergencia (audit): CAP_GATES_SKIP=1 git commit ..."
        echo "─────────────────────────────────────────────────────────────"
        printf "\033[0m"
        exit 1
      fi
    fi
  fi
fi  # end CAP_GATES_SKIP guard (section 5e)

