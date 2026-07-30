# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 18 — Machinery consistency (anti-drift doctrina↔templates↔agentes — 2026-05-28)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: scripts/validate_machinery_consistency.py + docs/process/audits/2026-05-28-*.
# Corre (ambos gate levels — barato, sin red) cuando el commit toca la maquinaria
# agéntica (.claude/{rules,skills,agents}/ o docs/specs/templates/). Evita el
# bug-class #1 de la auditoría 2026-05-28: drift silencioso entre la doctrina
# (rules/skills) y los templates/agentes que la materializan.
MACHINERY_STAGED=$(git diff --cached --name-only --diff-filter=ACM \
  | grep -E '^\.claude/(rules|skills|agents)/|^docs/specs/templates/' || true)
if [ -n "${MACHINERY_STAGED}" ] && [ "${MACHINERY_CHECK_SKIP:-0}" != "1" ]; then
  REPO_ROOT_MC=$(git rev-parse --show-toplevel)
  if [ -f "${REPO_ROOT_MC}/scripts/validate_machinery_consistency.py" ]; then
    echo "→ machinery-check (anti-drift, Section 18)…"
    PY_MC="${REPO_ROOT_MC}/.venv/bin/python"; [ -x "${PY_MC}" ] || PY_MC=python3
    if ! "${PY_MC}" "${REPO_ROOT_MC}/scripts/validate_machinery_consistency.py"; then
      printf "\033[31m"
      cat <<'EOF'
❌ MACHINERY DRIFT detectado (Section 18)
La doctrina (rules/skills) y los templates/agentes que la materializan divergieron.
Corré: make machinery-check  (o python3 scripts/validate_machinery_consistency.py)
y corregí los CHECK en rojo antes de commitear.
Override emergencia: MACHINERY_CHECK_SKIP=1 git commit ...
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

exit 0
