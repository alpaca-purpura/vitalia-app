# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 7. Checkpoint state enum validator (v4 paradigma — Punto 4 2026-05-06)
# Gate: FULL only (wip/* branches skip — checkpoint may be in mid-transition
# during WIP commits)
# ─────────────────────────────────────────────────────────────────
# Staged checkpoint.md files MUST use v4 vocabulary (10 estados):
#   idea | refining | refined | ready | developing | developed |
#   reviewing | done | parked | dropped
#
# Legacy v3 states (validated/building/review) are coerced at runtime by
# generate_backlog.py LEGACY_STATE_MAP, but new commits should use v4
# vocabulary directly to avoid stale paradigm leak.
#
# Bypass: rare — magic comment `<!-- state-enum-na: <reason> -->` if needed
# (e.g., archive snapshots). Adding to active checkpoints requires Chris approval.

if [ "${GATE_LEVEL}" = "full" ]; then

# Multisistema: capturar checkpoints en docs/ raíz (platform/legacy) + per-sistema
# {sistema}/docs/product/stories/{story}/checkpoint.md. Validación v4 states es
# universal cross-sistema (mismo paradigma 10 estados).
CHECKPOINT_FILES_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
  | grep -E '^(docs/(product/stories/[^/]+/checkpoint\.md|projects/active/.+/checkpoint\.md)|[a-z][a-z0-9_-]*/docs/product/stories/[^/]+/checkpoint\.md)$' \
  || true)

if [ -n "${CHECKPOINT_FILES_STAGED}" ]; then
  V4_STATES_REGEX='^state:[[:space:]]*(idea|refining|refined|ready|developing|developed|reviewing|done|parked|dropped)\b'
  STATE_VIOLATIONS=""

  while IFS= read -r FILE; do
    [ -z "${FILE}" ] && continue
    [ ! -f "${FILE}" ] && continue
    # Bypass via magic comment
    if grep -qE '<!--[[:space:]]*state-enum-na' "${FILE}"; then
      continue
    fi
    # Legacy folder gets relaxed enforcement (coercion handles it)
    if echo "${FILE}" | grep -qE '^docs/projects/active/'; then
      continue
    fi
    # Extract state line(s) from staged content (use git show :file for staged)
    STAGED_CONTENT=$(git show ":${FILE}" 2>/dev/null || true)
    [ -z "${STAGED_CONTENT}" ] && continue
    STATE_LINE=$(echo "${STAGED_CONTENT}" | grep -m1 -E '^state:' || true)
    if [ -n "${STATE_LINE}" ]; then
      if ! echo "${STATE_LINE}" | grep -qE "${V4_STATES_REGEX}"; then
        STATE_VIOLATIONS="${STATE_VIOLATIONS}${FILE}: ${STATE_LINE}"$'\n'
      fi
    fi
  done <<< "${CHECKPOINT_FILES_STAGED}"

  if [ -n "${STATE_VIOLATIONS}" ]; then
    printf "\033[31m"
    cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: invalid checkpoint state(s) — v4 paradigma.

Staged checkpoint(s) use legacy or unknown state. Fix:

${STATE_VIOLATIONS}

V4 valid states (Punto 4 2026-05-06):
  idea | refining | refined | ready | developing | developed |
  reviewing | done | parked | dropped

Legacy → v4 mapping:
  validated → refining (drafts) | refined (ratified)
  building  → developing (active) | developed (validators GREEN)
  review    → reviewing

Per docs/process/pm-redesign-2026-05.md § Punto 4.

Bypass (rare): add <!-- state-enum-na: <reason> --> to checkpoint.md
NEVER use --no-verify (.claude/rules/git-safety.md).
─────────────────────────────────────────────────────────────
EOF
    printf "\033[0m"
    exit 1
  fi
fi

fi  # end GATE_LEVEL=full guard (section 7)

