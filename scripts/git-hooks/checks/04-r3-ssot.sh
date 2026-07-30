# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 4. R3 SSoT freshness gate (origen C1 2026-05-05 R21) — MULTIBRAND-AWARE
# (refactor 2026-05-15 post multibrand reorg: cubre shared/ legacy +
# per-brand shared raro + engine packages core/luana-core-*)
# Gate: FULL only (wip/* branches skip — WIP files may not yet have SSoT entry)
# ─────────────────────────────────────────────────────────────────
# New file under shared cross-consumer surface MUST appear in the inventory
# tabla of .claude/rules/auditor-downstream-regression.md, OR carry magic
# comment `# downstream-regression-na: <reason>` within first 20 lines.
#
# Surfaces detectadas (multibrand):
#   - backend/src/shared/                       (legacy single-target backcompat)
#   - {brand}/backend/src/shared/               (per-brand shared raro)
#   - core/luana-core-*/src/luana_core_*/       (engine packages — afecta TODAS
#                                                las brands consumidoras)
#
# Lookup en tabla SSoT:
#   - Engine file core/luana-core-X/src/luana_core_X/Y/Z.py → lookup exact path
#     y dirname/
#   - Per-brand shared {brand}/backend/src/shared/Y.py → lookup shared/Y.py
#     (convención tabla strips brand prefix)
#   - Legacy backend/src/shared/Y.py → lookup shared/Y.py
#
# Detects status A (added) AND R (renamed-into).

if [ "${GATE_LEVEL}" = "full" ]; then

NEW_SHARED_FILES=$(git diff --cached --name-only --diff-filter=AR 2>/dev/null \
  | grep -E '^(backend/src/shared|[a-z][a-z0-9_-]*/backend/src/shared|core/luana-core-[a-z][a-z0-9-]*/src/luana_core_[a-z0-9_]+)/.+\.py$' \
  | grep -vE '(__pycache__/|\.venv/|migrations/versions/|tests/)' \
  || true)

if [ -n "${NEW_SHARED_FILES}" ]; then
  SSoT_TABLE="${REPO_ROOT}/.claude/rules/auditor-downstream-regression.md"
  MISSING_FILES=""

  if [ ! -f "${SSoT_TABLE}" ]; then
    printf "\033[33m"
    echo "─────────────────────────────────────────────────────────────"
    echo "WARNING: ${SSoT_TABLE} not found — skipping R3 SSoT freshness gate."
    echo "─────────────────────────────────────────────────────────────"
    printf "\033[0m"
  else
    while IFS= read -r FILE; do
      [ -z "${FILE}" ] && continue

      # Compute lookup paths según tipo de surface multibrand.
      # Engine packages (core/luana-core-X/src/luana_core_X/Y/Z.py) → lookup full path.
      # Per-brand shared ({brand}/backend/src/shared/Y.py) → strip prefix, lookup shared/Y.py.
      # Legacy (backend/src/shared/Y.py) → strip prefix, lookup shared/Y.py.
      case "${FILE}" in
        core/luana-core-*/src/luana_core_*/*)
          LOOKUP_PATH="${FILE}"
          ;;
        */backend/src/shared/*)
          # Strip up to and including 'backend/src/' (works for legacy y per-brand)
          LOOKUP_PATH="${FILE##*backend/src/}"
          ;;
        backend/src/shared/*)
          LOOKUP_PATH="${FILE#backend/src/}"
          ;;
        *)
          LOOKUP_PATH="${FILE}"
          ;;
      esac
      LOOKUP_DIR="$(dirname "${LOOKUP_PATH}")/"

      # Check tabla — either exact path OR parent directory listed
      # (e.g. `shared/billing/` covers all Py files under that dir).
      if grep -qF "\`${LOOKUP_PATH}\`" "${SSoT_TABLE}" 2>/dev/null; then
        continue
      fi
      if grep -qF "\`${LOOKUP_DIR}\`" "${SSoT_TABLE}" 2>/dev/null; then
        continue
      fi

      # Check magic-comment escape hatch in staged file content
      if git show ":${FILE}" 2>/dev/null | head -20 | grep -qE '#\s*downstream-regression-na:'; then
        continue
      fi

      MISSING_FILES+="  - ${FILE}"$'\n'
      MISSING_FILES+="    looked up: \`${LOOKUP_PATH}\` and \`${LOOKUP_DIR}\`"$'\n'
    done <<< "${NEW_SHARED_FILES}"

    if [ -n "${MISSING_FILES}" ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: R3 SSoT freshness gate (downstream-regression — multibrand)
─────────────────────────────────────────────────────────────
You're adding new file(s) under a shared cross-consumer surface that are
NOT listed in the downstream-regression SSoT tabla. Surfaces cubiertas:
  - backend/src/shared/ (legacy)
  - {brand}/backend/src/shared/ (per-brand shared raro)
  - core/luana-core-*/src/luana_core_*/ (engine — afecta TODAS las brands)

Auditors rely on that tabla to spawn cross-surface tests
(.claude/rules/auditor-downstream-regression.md caso D4 origen).

Files missing from tabla:
${MISSING_FILES}

Resolution (pick one):

A) Add a row to .claude/rules/auditor-downstream-regression.md tabla
   with downstream_test_targets enumerating which test paths consume
   this surface. Format:

   | \`shared/<your_path>.py\` | \`tests/...\`<br>\`tests/...\` | <reason — 1 line> |

B) Mark file as truly self-contained (no cross-consumers) by adding
   to first 20 lines:

   # downstream-regression-na: <one-line reason — e.g. "private helper
   #                          for shared/X internal use, no module imports">

   Justification scrutinized at audit time — false NA = REVERT.

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

fi  # end GATE_LEVEL=full guard (section 4)

