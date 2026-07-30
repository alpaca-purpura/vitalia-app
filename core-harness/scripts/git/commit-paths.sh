#!/usr/bin/env bash
set -euo pipefail
# commit-paths.sh — commit SEGURO por pathspec en el hub único (ADR-009).
#
# Por qué existe: en el hub único N sesiones (= yo en N terminales) comparten el
# MISMO `.git/index`. Un `git add <x>` + `git commit` pelado commitea TODO lo staged,
# barriendo renames/cambios que otra sesión mía dejó staged (¡`git mv` auto-stagea!).
# Caso origen: commit cockpit 0072388f barrió los renames del lift SSR-store (2026-05-29).
#
# Este helper usa `git commit --only <paths>` → commitea EXCLUSIVAMENTE los paths dados,
# ignorando cualquier otra cosa en el índice. Imposible contaminar.
#
# Usage:
#   scripts/git/commit-paths.sh "<commit message>" <path1> [path2 ...]
#   SCOPE_GATE_SKIP=1 scripts/git/commit-paths.sh "<msg>" <paths...>   # cross-cutting (bootstrap)
#
# Notas:
#   - El mensaje va PRIMERO (puede ser multilínea via $'...' o "$(cat <<EOF ...)").
#   - Rechaza `.`, `-A`, `-u`, globs peligrosos y "sin paths".
#   - Pasa SCOPE_GATE_SKIP / cualquier env tal cual al hook (no lo toca).
#   - NO hace push (eso es decisión explícita aparte).

if [[ $# -lt 2 ]]; then
  echo "::error::Uso: commit-paths.sh \"<msg>\" <path1> [path2 ...]" >&2
  echo "  (commit por pathspec — nunca 'git add .' en el hub compartido)" >&2
  exit 2
fi

MSG="$1"
shift
PATHS=("$@")

# Guardrails: nada de comodines peligrosos como pathspec.
for p in "${PATHS[@]}"; do
  case "$p" in
    "."|"-A"|"-u"|"--all"|"*")
      echo "::error::pathspec prohibido: '$p'. Listá rutas EXACTAS (cero git add .)." >&2
      exit 2
      ;;
  esac
  if [[ ! -e "$p" ]]; then
    # Permitir paths borrados (rename/delete) — git los maneja; solo avisamos.
    echo "ℹ aviso: '$p' no existe en disco (¿delete/rename?). git lo resolverá si está tracked." >&2
  fi
done

echo "→ commit sobre ${#PATHS[@]} path(s) (resto del índice intacto):"
printf '   %s\n' "${PATHS[@]}"

# 1. Stagea EXACTAMENTE estos paths (nombres exactos · jamás `.`/`-A`). Esto cubre
#    archivos nuevos/untracked, que `--only` solo no levanta. No toca lo demás staged.
git add -- "${PATHS[@]}"

# 2. --only: commitea EXCLUSIVAMENTE estos paths, ignorando cualquier otra cosa que
#    haya en el índice compartido (renames de git mv de otra terminal mía, etc.).
git commit --only -m "$MSG" -- "${PATHS[@]}"

echo "✓ commit creado:"
git log --oneline -1
