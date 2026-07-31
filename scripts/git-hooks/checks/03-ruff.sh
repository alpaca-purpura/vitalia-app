# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 3. Ruff check + format on staged Python — MULTIBRAND-AWARE
# (refactor 2026-05-15 post multibrand reorg: cubre todos los workspace
# members — backend/ legacy + {brand}/backend/ + core/luana-core-*/.)
# ─────────────────────────────────────────────────────────────────
#
# Regex captura cualquier Python en workspace member backend o core:
#   - backend/                  (legacy single-target, mantenido por backcompat)
#   - {brand}/backend/          (vitalia)
#   - core/luana-core-{pkg}/    (26 packages engine compartido)
#
# Venv canónico: ${REPO_ROOT}/.venv/bin/ruff (uv workspace root, instala TODOS
# los members en editable mode — un solo venv compartido). Fallback al venv
# legacy backend/.venv/ si root venv ausente (compat con setups antiguos).
#
# Ruff auto-descubre el pyproject.toml correcto (cada workspace member tiene
# el suyo) subiendo directorios desde el archivo. No requiere pushd manual.

STAGED_BACKEND_PY_REPO=$(echo "${STAGED_PY}" \
  | grep -E '^(backend|[a-z][a-z0-9_-]*/backend|core/luana-core-[a-z][a-z0-9-]*)/' \
  || true)

if [ -n "${STAGED_BACKEND_PY_REPO}" ]; then
  # Resolver venv canónico
  if [ -x "${REPO_ROOT}/.venv/bin/ruff" ]; then
    RUFF="${REPO_ROOT}/.venv/bin/ruff"
  elif [ -x "${REPO_ROOT}/backend/.venv/bin/ruff" ]; then
    RUFF="${REPO_ROOT}/backend/.venv/bin/ruff"
    printf "\033[33m"
    echo "WARNING: usando legacy backend/.venv/bin/ruff — recomendado migrar a root .venv via 'uv sync'."
    printf "\033[0m"
  else
    RUFF=""
  fi

  if [ -z "${RUFF}" ]; then
    printf "\033[33m"
    echo "─────────────────────────────────────────────────────────────"
    echo "WARNING: ruff not found en .venv/bin/ ni backend/.venv/bin/ — skipping ruff checks."
    echo "  Run: uv sync   (instala todos los workspace members + dev deps en .venv root)"
    echo "─────────────────────────────────────────────────────────────"
    printf "\033[0m"
  else
    RUFF_FAIL_FILES=""
    FORMAT_FAIL_FILES=""

    # Ruff check + format on STAGED content (via `git show :file` stdin) — not
    # working tree, which may diverge if dev edited post-stage. Fixes pre-existing
    # silent-pass bug where pre-commit hook accepted broken staged content if
    # working tree was clean.
    #
    # Multibrand: cd al workspace root (no a backend/) — ruff auto-descubre el
    # pyproject.toml correcto desde --stdin-filename. Cada workspace member
    # (backend/, {brand}/backend/, core/luana-core-X/) tiene su propio
    # pyproject.toml con line-length=120 + reglas heredadas.
    pushd "${REPO_ROOT}" >/dev/null
    while IFS= read -r FILE; do
      [ -z "${FILE}" ] && continue

      # --stdin-filename con path relativo al REPO_ROOT permite a ruff
      # descubrir el pyproject.toml correcto del workspace member.
      if ! git -C "${REPO_ROOT}" show ":${FILE}" 2>/dev/null \
          | "${RUFF}" check --no-cache --quiet --stdin-filename "${FILE}" - >/dev/null 2>&1; then
        RUFF_FAIL_FILES+="${FILE} "
      fi

      if ! git -C "${REPO_ROOT}" show ":${FILE}" 2>/dev/null \
          | "${RUFF}" format --check --quiet --stdin-filename "${FILE}" - >/dev/null 2>&1; then
        FORMAT_FAIL_FILES+="${FILE} "
      fi
    done <<< "${STAGED_BACKEND_PY_REPO}"
    popd >/dev/null

    if [ -n "${RUFF_FAIL_FILES}" ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: ruff check failures on STAGED content (multibrand)
─────────────────────────────────────────────────────────────
Files with ruff violations in staged content:
${RUFF_FAIL_FILES}

Re-run con detalles (paths absolutos, ruff descubre pyproject.toml del workspace member):
  ${RUFF} check --no-cache ${RUFF_FAIL_FILES}

Fix:
  ${RUFF} check --fix ${RUFF_FAIL_FILES}

Después \`git add\` para re-stage. NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi

    if [ -n "${FORMAT_FAIL_FILES}" ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: ruff format violations on STAGED content (multibrand)
─────────────────────────────────────────────────────────────
Files con format violations en staged content:
${FORMAT_FAIL_FILES}

Fix:
  ${RUFF} format ${FORMAT_FAIL_FILES}

Después \`git add\` para re-stage. NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

