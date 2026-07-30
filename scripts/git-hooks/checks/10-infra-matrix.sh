# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 10. INFRA-MATRIX auto-freshness (S-DOCKER-DEV-MULTIBRAND T-9 — 2026-05-15)
# (dynamic brand discovery wired 2026-05-15 post audit aislamiento brand)
# Gate: ALL branches (infra matrix freshness is always valuable)
# ─────────────────────────────────────────────────────────────────
# Si se edita cualquier {brand}/config/brand.yaml de las brands activas,
# regenerar INFRA-MATRIX.md y agregarlo al commit automaticamente.
#
# Patron "metadata-en-su-lugar + auto-gen index":
#   SSoT: {brand}/config/brand.yaml::infra
#   Index: docs/portfolio/INFRA-MATRIX.md (auto-generado)
#
# Sin este hook, un cambio de puerto en brand.yaml quedaria desincronizado
# con el INFRA-MATRIX.md hasta que alguien corriera make infra-matrix manualmente.
#
# Dynamic brand discovery: detecta brands del filesystem (dirs con
# config/brand.yaml). Escala automaticamente cuando se bootstrappean
# saasora/inmoflow/retailly/fixia/guestly/fitflow o cualquier brand futura
# sin requerir update manual del regex.

# Build pipe-separated brand list dinamicamente (vacio si no hay brands aun)
BRANDS_REGEX=$(find "${REPO_ROOT}" -maxdepth 3 -mindepth 3 -type f -path "${REPO_ROOT}/*/config/brand.yaml" 2>/dev/null \
  | sed -E "s|^${REPO_ROOT}/||; s|/config/brand\.yaml$||" \
  | sort -u \
  | paste -sd'|' -)

if [ -z "${BRANDS_REGEX}" ]; then
  # No brands bootstrappeadas todavia — skip Section 10 sin error
  CHANGED_BRAND_YAML=""
else
  CHANGED_BRAND_YAML=$(git diff --cached --name-only 2>/dev/null \
    | grep -E "^(${BRANDS_REGEX})/config/brand\.yaml\$" \
    || true)
fi

if [ -n "${CHANGED_BRAND_YAML}" ]; then
  echo "[pre-commit] brand.yaml editado — regenerando INFRA-MATRIX.md..."
  INFRA_SCRIPT="${REPO_ROOT}/scripts/generate_infra_matrix.py"
  VENV_PY_ROOT="${REPO_ROOT}/.venv/bin/python"

  if [ ! -f "${INFRA_SCRIPT}" ]; then
    printf "\033[33m"
    echo "WARNING: scripts/generate_infra_matrix.py not found — skipping INFRA-MATRIX regen."
    printf "\033[0m"
  elif [ ! -x "${VENV_PY_ROOT}" ]; then
    printf "\033[33m"
    echo "WARNING: .venv/bin/python not found — skipping INFRA-MATRIX regen (Section 10)."
    printf "\033[0m"
  else
    if "${VENV_PY_ROOT}" "${INFRA_SCRIPT}" 2>/tmp/infra-matrix-err.txt; then
      # NOTE 2026-05-20: INFRA-MATRIX.md es gitignored — regen sin auto-stage.
      echo "[pre-commit] INFRA-MATRIX.md regenerado localmente (gitignored, no incluido en commit). Vista: cat docs/portfolio/INFRA-MATRIX.md"
    else
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: generate_infra_matrix.py fallo (Section 10).
─────────────────────────────────────────────────────────────
$(cat /tmp/infra-matrix-err.txt 2>/dev/null || true)

Resolucion:
  .venv/bin/python scripts/generate_infra_matrix.py
  # Corrige el error y vuelve a git add + commit.

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

