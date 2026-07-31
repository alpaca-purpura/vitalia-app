#!/usr/bin/env bash
set -euo pipefail
# promote-to-main.sh — Lift un commit COMPARTIDO (core/harness) a main via cherry-pick.
# Rechaza si el commit toca {brand}/** (eso NO es un cambio compartido — arrastraría
# WIP de marca a main). Doctrina: docs/process/harness-backlog.md HB-86.
#
# Por qué cherry-pick y NO squash-merge del branch: un wip/{brand} puede estar
# decenas de commits adelante con WIP de marca; squashear el branch entero
# entanglearía todo eso en main. Cherry-pick mueve SOLO el commit compartido.
#
# ★ Caveat: el cherry-pick es limpio SOLO si el commit compartido se hizo sobre
#   un base sincronizado con main. Si main avanzó tocando los MISMOS archivos
#   (típico: el log append-only `harness-backlog.md`), el cherry-pick da
#   falso-conflicto por mismatch de base → sincronizá tu wip con main ANTES
#   (git fetch origin main && git merge origin/main), o reconstruí a mano.
#
# Usage:
#   scripts/git/promote-to-main.sh <sha> [<sha2> ...]   # oldest-first si son varios
#   scripts/git/promote-to-main.sh --self-check

BRAND_DIRS="vitalia"
# Repo standalone single-brand (2026-07-31): solo vitalia.

_brand_path() {  # lee files de stdin; echo la 1ra ruta brand-scoped tocada ('' si shared-only)
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    local seg="${f%%/*}"
    case " ${BRAND_DIRS} " in *" ${seg} "*) echo "$f"; return ;; esac
  done
}

if [[ "${1:-}" == "--self-check" ]]; then
  assert() { [[ "$1" == "$2" ]] || { echo "FAIL: got '$1' want '$2'"; exit 1; }; }
  assert "$(printf 'core/x.py\nscripts/y.sh\nMakefile\n'        | _brand_path)" ""
  assert "$(printf 'core/x.py\nvitalia/backend/z.py\n'          | _brand_path)" "vitalia/backend/z.py"
  assert "$(printf 'docs/process/a.md\n'                        | _brand_path)" ""
  assert "$(printf 'vitalia/frontend/app/page.tsx\n'            | _brand_path)" "vitalia/frontend/app/page.tsx"
  echo "✓ promote-to-main self-check passed"
  exit 0
fi

SHAS=("$@")
[[ ${#SHAS[@]} -ge 1 ]] || { echo "Usage: promote-to-main.sh <sha> [<sha2> ...]"; exit 2; }

MAIN_WT="$(git worktree list --porcelain | awk '/^worktree /{p=$2} /^branch refs\/heads\/main$/{print p}')"
[[ -n "${MAIN_WT}" ]] || { echo "::error:: no hay worktree en branch main"; exit 2; }

# Guard 1: cada commit existe + es shared-only (cero {brand}/**)
for sha in "${SHAS[@]}"; do
  git cat-file -e "${sha}^{commit}" 2>/dev/null || { echo "::error:: commit inexistente: ${sha}"; exit 2; }
  bp="$(git diff-tree --no-commit-id --name-only -r "${sha}" | _brand_path)"
  [[ -z "${bp}" ]] || { echo "::error:: ${sha} toca ruta de marca (${bp}) → NO es compartido. Refuse."; exit 1; }
done

# Guard 2: main worktree sin cambios TRACKED (untracked OK)
if ! git -C "${MAIN_WT}" diff --quiet || ! git -C "${MAIN_WT}" diff --cached --quiet; then
  echo "::error:: el worktree main (${MAIN_WT}) tiene cambios tracked sin commitear — resolvé antes."
  exit 1
fi

echo "→ Promoviendo ${#SHAS[@]} commit(s) a main (worktree ${MAIN_WT})..."
git -C "${MAIN_WT}" fetch origin main --quiet
git -C "${MAIN_WT}" merge --ff-only origin/main --quiet 2>/dev/null || {
  echo "::error:: main local divergió de origin/main — resolvé manualmente."; exit 1; }

# El pre-commit gatea commits directos a main; el cherry-pick a main es intencional.
export LUANA_ALLOW_MAIN_COMMIT=1
if ! git -C "${MAIN_WT}" cherry-pick "${SHAS[@]}"; then
  echo "::error:: cherry-pick conflictó → abortando (no dejo main a medias)."
  git -C "${MAIN_WT}" cherry-pick --abort 2>/dev/null || true
  exit 1
fi

git -C "${MAIN_WT}" push origin main
echo "✓ main → $(git -C "${MAIN_WT}" rev-parse --short HEAD)."
