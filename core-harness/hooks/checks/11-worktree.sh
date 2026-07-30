# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# Section 11 — Worktree D11 enforcement (added 2026-05-18 ADR-005 worktree-policy)
# Block direct commit to main unless squash-merge/merge in progress.
# Pre-commit no puede leer commit message (eso es commit-msg hook);
# usamos signal git-native: .git/SQUASH_MSG | .git/MERGE_MSG.
# ─────────────────────────────────────────────────────────────────
if [[ "${GATE_LEVEL:-light}" = "full" ]]; then
  CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || echo '')"
  if [[ "${CURRENT_BRANCH}" = "main" ]]; then
    GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || echo '.git')"
    if [[ -f "${GIT_DIR}/SQUASH_MSG" ]] || [[ -f "${GIT_DIR}/MERGE_MSG" ]]; then
      :  # OK — squash-merge o merge en progreso (/pm-{sistema} territory)
    elif [[ -n "${HARNESS_ALLOW_MAIN_COMMIT:-}" ]]; then
      :  # OK — bypass explícito (meta-commits del worktree-protocol)
    else
      printf "\033[31m"
      cat <<'EOF'

─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: commit directo a 'main' (ADR-005 D11).

main solo recibe squash-merges desde branches wip/* via
/pm-{sistema} al cerrar story state=done. Commits directos a
main están prohibidos.

Acciones:
  1. Si esto es WIP: crear worktree wip/* primero:
     scripts/git/new-session.sh <sistema> <type> <slug>
  2. Si esto es squash-merge: el flow correcto es
     `git merge --squash wip/<branch>` + `git commit` —
     pre-commit detecta .git/SQUASH_MSG automáticamente.
  3. Si esto es meta-commit del protocolo:
     HARNESS_ALLOW_MAIN_COMMIT=1 git commit -m "..."

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

