# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 5c. Code-to-cap index regen advisory (cement 2026-05-28 · Fase A)
# ─────────────────────────────────────────────────────────────────
# Re-genera `{brand}/docs/product/capabilities/_code-index.json` cuando
# archivos de código (.py / .ts / .tsx) son staged. Output gitignored R3 v2.
#
# Behavior:
#   Advisory (never blocks): regenera índice silenciosamente. Si detecta
#   archivos NUEVOS sin header `# cap:` / `// cap:`, imprime warning
#   con paths sugeridos.
#
# Override:
#   * env: CODE_INDEX_SKIP=1 git commit ...
#
# SSoT: docs/process/capability-protocol.md § Sección 12 v3.2 (Fase A)
#       .claude/rules/anti-duplication-refining.md
# ─────────────────────────────────────────────────────────────────

if [ "${CODE_INDEX_SKIP:-0}" != "1" ]; then

  # Detect staged code files (per-brand backend/frontend/src)
  CODE_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/(backend|frontend)/src/.*\.(py|ts|tsx)$' \
    || true)

  if [ -n "${CODE_STAGED}" ]; then
    # Derive brand(s) from staged paths
    BRANDS_CODE=$(echo "${CODE_STAGED}" | cut -d/ -f1 | sort -u)

    INDEX_SCRIPT="${REPO_ROOT}/scripts/generate_code_to_cap_index.py"
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      VENV_CODE="${REPO_ROOT}/.venv/bin/python"
    elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
      VENV_CODE="${REPO_ROOT}/backend/.venv/bin/python"
    else
      VENV_CODE=""
    fi

    if [ -n "${VENV_CODE}" ] && [ -f "${INDEX_SCRIPT}" ]; then
      while IFS= read -r B_CODE; do
        [ -z "${B_CODE}" ] && continue

        # Regen silently (output gitignored)
        CODE_OUT=$("${VENV_CODE}" "${INDEX_SCRIPT}" --brand "${B_CODE}" 2>&1 || true)

        # Parse no_header count from output
        NO_HEADER_COUNT=$(echo "${CODE_OUT}" | grep -oE 'no_header=[0-9]+' | head -1 | sed 's/no_header=//')

        if [ -n "${NO_HEADER_COUNT}" ] && [ "${NO_HEADER_COUNT}" -gt 0 ]; then
          # Get list of files without header from JSON
          INDEX_JSON="${REPO_ROOT}/${B_CODE}/docs/product/capabilities/_code-index.json"
          if [ -f "${INDEX_JSON}" ]; then
            NO_HEADER_FILES=$("${VENV_CODE}" -c "
import json
d = json.load(open('${INDEX_JSON}'))
# Only show NEWLY staged files without header
import sys
staged = set('''${CODE_STAGED}'''.strip().split('\n'))
new_orphans = [f for f in d.get('no_header', []) if f in staged]
for f in new_orphans[:5]:
    print(f'    {f}')
" 2>/dev/null || true)

            if [ -n "${NO_HEADER_FILES}" ]; then
              printf "\033[33m"
              echo ""
              echo "[5c] Code-index advisory · ${B_CODE} (non-blocking)"
              echo "  ${NO_HEADER_COUNT} archivos sin header \`# cap:\` / \`// cap:\`:"
              echo "${NO_HEADER_FILES}"
              echo ""
              echo "  Agregá header al archivo (2 líneas) per docs/process/capability-protocol.md § 12:"
              echo "    Python: # cap: {module}.{slug}"
              echo "            # story-origin: TBD"
              echo "    TS/TSX: // cap: {module}.{slug}"
              echo "            // story-origin: TBD"
              echo "  Special markers: __orphan__ · __shared__ · __skip__"
              printf "\033[0m"
            fi
          fi
        fi
      done <<< "${BRANDS_CODE}"
    fi
  fi

fi  # end CODE_INDEX_SKIP guard (section 5c)

