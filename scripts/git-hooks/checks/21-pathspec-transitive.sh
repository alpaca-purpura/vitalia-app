# shellcheck shell=bash
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL,
# STAGED_*, set -euo pipefail). DO NOT add a shebang or 'set -e'; 'exit 1' aborta el commit.
# ─────────────────────────────────────────────────────────────────────────────
# Section 21 — pathspec transitive-dep guard (HB-36)
# ─────────────────────────────────────────────────────────────────────────────
# El repo prohíbe `git add -A/.`; cada commit stagea rutas explícitas. Si un .ts/.tsx
# staged importa un archivo LOCAL que NO está en el commit (untracked o modified-unstaged),
# el snapshot del commit no compila aunque el disco sí (rompe en CI / otro worktree tras
# merge). Origen: adrian-embudo (T-FE-2 omitió types/embudo-schema.ts). Corre en light+full
# (el bug pega en commits wip/*). Override: PATHSPEC_TRANSITIVE_SKIP=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────
if [ "${PATHSPEC_TRANSITIVE_SKIP:-0}" != "1" ]; then
  PT_STAGED_TS=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep -E '\.(ts|tsx)$' || true)
  if [ -n "$PT_STAGED_TS" ]; then
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      PT_PY="${REPO_ROOT}/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
      PT_PY="python3"
    else
      PT_PY=""
      echo "WARNING: python no encontrado — skipping pathspec-transitive (Section 21)." >&2
    fi
    if [ -n "$PT_PY" ]; then
      if ! PT_OUT=$("$PT_PY" "${REPO_ROOT}/scripts/check_pathspec_transitive.py" 2>&1); then
        printf "\033[31m"
        cat <<EOF

─────────────────────────────────────────────────────────────
PATHSPEC · DEP TRANSITIVA NO COMMITEADA (HB-36)

$PT_OUT

Un archivo .ts/.tsx staged importa un archivo LOCAL que NO está en este
commit (untracked o modified-unstaged). El commit aislado no compilará
aunque el disco sí (rompe en CI / otro worktree tras el merge).

FIX: agregá la(s) dep(s) al MISMO commit por pathspec (git add <ruta>),
o committeá la dep primero. NO uses git add -A.

Override emergencia: PATHSPEC_TRANSITIVE_SKIP=1 git commit ...
SSoT: docs/process/harness-backlog.md HB-36
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
        exit 1
      fi
    fi
  fi
fi
