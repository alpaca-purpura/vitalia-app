#!/usr/bin/env bash
set -euo pipefail
# dev-lock-check.sh — Guard contra worktree-mismatch del dev-stack (mec. F)
# SSoT: docs/process/parallel-sessions-protocol.md § D5
#
# El proyecto compose se llama `luana-dev` (compartido por TODOS los worktrees).
# `make dev-{brand}` bindea el monorepo al CWD donde se corre → si una sesión
# lo lanza desde otro worktree, RECREA los containers apuntando a ESE worktree,
# en silencio. El último que lanza gana → tu código no se deploya y no hay señal.
#
# Este guard compara el worktree que el stack corriendo bindea vs el worktree
# actual — para AMBOS servicios (backend + frontend). Bloquea si:
#   • el backend sirve OTRO worktree, o
#   • el frontend sirve OTRO worktree, o
#   • FE y BE quedaron bindeados a worktrees DISTINTOS (binding MIXTO, HB-87):
#     el stack sirve código mezclado (ej. FE=luana-vitalia + BE=main stale) →
#     500 silencioso en endpoints DB que /health no toca.
#
# Usage:
#   scripts/dev-lock-check.sh <brand>     # pre-condición de make dev-{brand}
#   scripts/dev-lock-check.sh --which     # tabla read-only: qué worktree sirve cada marca (FE+BE)
#   scripts/dev-lock-check.sh --self-check
#
# Escape: FORCE_REBIND=1 make dev-{brand}   (rebindea ambos servicios a este worktree)
# Fail-OPEN si docker no está disponible.

BRANDS="vitalia"

_mount_src() {  # echo el worktree root que el BACKEND bindea en /workspace ('' si no hay stack)
  docker inspect "luana-dev-${1}_backend_dev-1" \
    --format '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo ''
}

_fe_root() {  # echo el worktree root que el FRONTEND bindea ('' si no hay stack FE)
  # FE monta `./core:/app/core` → Source = <root>/core → root = dirname.
  local src
  src="$(docker inspect "luana-dev-${1}_frontend_dev-1" \
    --format '{{range .Mounts}}{{if eq .Destination "/app/core"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo '')"
  if [[ -n "${src}" ]]; then dirname "${src}"; return; fi
  # fallback: `./{brand}/frontend:/app/{brand}/frontend` → strip /{brand}/frontend
  src="$(docker inspect "luana-dev-${1}_frontend_dev-1" \
    --format "{{range .Mounts}}{{if eq .Destination \"/app/${1}/frontend\"}}{{.Source}}{{end}}{{end}}" 2>/dev/null || echo '')"
  [[ -n "${src}" ]] && echo "${src%/${1}/frontend}" || echo ''
}

_decide_rebind() {  # pura: BLOCK|OK  (bound, current, force) — un servicio vs cwd
  local bound="$1" current="$2" force="$3"
  [[ "${force}" == "1" ]] && { echo OK; return; }
  [[ -z "${bound}" ]] && { echo OK; return; }          # no hay servicio corriendo
  [[ "${bound}" == "${current}" ]] && { echo OK; return; }
  echo BLOCK
}

_decide_pair() {  # pura: COHERENT|MIXED  (be_root, fe_root) — los dos servicios entre sí
  local be="$1" fe="$2"
  [[ -z "${be}" || -z "${fe}" ]] && { echo COHERENT; return; }  # falta un lado → no afirmar mixto
  [[ "${be}" == "${fe}" ]] && { echo COHERENT; return; }
  echo MIXED
}

# ── self-check ────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--self-check" ]]; then
  assert() { [[ "$1" == "$2" ]] || { echo "FAIL: got '$1' want '$2'"; exit 1; }; }
  assert "$(_decide_rebind ''     /a       0)" OK     # no stack → permitir
  assert "$(_decide_rebind /a     /a       0)" OK     # mismo worktree → permitir
  assert "$(_decide_rebind /main  /vitalia 0)" BLOCK  # mismatch → bloquear
  assert "$(_decide_rebind /main  /vitalia 1)" OK     # FORCE_REBIND override
  assert "$(_decide_pair   /a     /a)"         COHERENT  # FE==BE
  assert "$(_decide_pair   /main  /vitalia)"   MIXED     # FE≠BE → binding mixto (HB-87)
  assert "$(_decide_pair   ''     /vitalia)"   COHERENT  # falta BE → no afirmar mixto
  assert "$(_decide_pair   /main  '')"         COHERENT  # falta FE → no afirmar mixto
  echo "✓ dev-lock-check self-check passed"
  exit 0
fi

# ── dev-which: vista read-only de todos los stacks (FE + BE + coherencia) ──────
if [[ "${1:-}" == "--which" ]]; then
  command -v docker &>/dev/null || { echo "(dev-which: docker not available)"; exit 0; }
  current="$(git rev-parse --show-toplevel 2>/dev/null || echo '?')"
  echo "cwd worktree: ${current}"
  printf '%-10s %-42s %-42s %s\n' "BRAND" "BACKEND (/workspace)" "FRONTEND (/app/core)" "COHERENCIA"
  for b in ${BRANDS}; do
    be="$(_mount_src "${b}")"; fe="$(_fe_root "${b}")"
    be_d="${be:-(no stack)}"; fe_d="${fe:-(no stack)}"
    note=""
    if [[ "$(_decide_pair "${be}" "${fe}")" == "MIXED" ]]; then
      note="⚠ MIXTO — FE y BE sirven directorios DISTINTOS (HB-87)"
    elif [[ -n "${be}" && "${be}" != "${current}" ]]; then
      note="⚠ no es este repo (${current})"
    fi
    printf '%-10s %-42s %-42s %s\n' "${b}" "${be_d}" "${fe_d}" "${note}"
  done
  exit 0
fi

# ── pre-condición de make dev-{brand} ─────────────────────────────────────────
BRAND="${1:?Usage: dev-lock-check.sh BRAND}"

if ! command -v docker &>/dev/null; then
  echo "  (dev-lock-check: docker not available, skip)"
  exit 0
fi

CURRENT="$(git rev-parse --show-toplevel 2>/dev/null || echo '')"
BE="$(_mount_src "${BRAND}")"
FE="$(_fe_root "${BRAND}")"
FORCE="${FORCE_REBIND:-0}"

be_verdict="$(_decide_rebind "${BE}" "${CURRENT}" "${FORCE}")"
fe_verdict="$(_decide_rebind "${FE}" "${CURRENT}" "${FORCE}")"

if [[ "${be_verdict}" == "BLOCK" || "${fe_verdict}" == "BLOCK" ]]; then
  be_flag=""; fe_flag=""
  [[ "${be_verdict}" == "BLOCK" ]] && be_flag="  ← OTRO worktree"
  [[ "${fe_verdict}" == "BLOCK" ]] && fe_flag="  ← OTRO worktree"
  mixed=""
  [[ "$(_decide_pair "${BE}" "${FE}")" == "MIXED" ]] && \
    mixed="
  ⚠ BINDING MIXTO (HB-87): FE y BE sirven worktrees DISTINTOS → el stack sirve
    código mezclado (ej. BE main stale → 500 en endpoints DB que /health no toca)."
  cat <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DEV-LOCK STOP — el stack de '${BRAND}' sirve OTRO worktree
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Backend  bindea:  ${BE:-(no stack)}${be_flag}
  Frontend bindea:  ${FE:-(no stack)}${fe_flag}
  Vos estás en:     ${CURRENT}
${mixed}

  El proyecto compose 'luana-dev' es ÚNICO cross-worktree. Si recreás
  el stack desde acá, REBINDEA los containers a este worktree.

  Opciones:
    • Editá donde el stack ya apunta (cd al worktree de arriba)
    • O rebindeá AMBOS servicios a ESTE worktree a propósito:
          FORCE_REBIND=1 make dev-${BRAND}
    • Ver todos los stacks:             make dev-which

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
  exit 1
fi

# Notas informativas (no bloquean)
if [[ "${FORCE}" == "1" && ( -n "${BE}" || -n "${FE}" ) ]]; then
  echo "  ⚠ FORCE_REBIND: rebindeando stack de ${BRAND} (BE:${BE:-—} FE:${FE:-—}) → ${CURRENT}"
elif [[ -n "${BE}" && "${BE}" == "${CURRENT}" ]]; then
  echo "  (dev-lock-check: stack de ${BRAND} ya bindea este worktree — recrear es seguro)"
fi
exit 0
