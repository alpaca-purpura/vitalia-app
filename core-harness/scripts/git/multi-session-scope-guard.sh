#!/usr/bin/env bash
# multi-session-scope-guard.sh — HB-31 sweep guard.
#
# Cement 2026-06-04 (Chris): el paralelo de varias sesiones sobre el MISMO hub está
# PERMITIDO (aceleramos). Lo que se prohíbe es la contaminación cross-sesión: una
# sesión que barre los archivos de OTRA (típico de `git add -A/-u/.`). Este guard
# bloquea un commit cuyo set staged toca el scope EXCLUSIVO de ≥2 sesiones VIVAS
# distintas (cada sesión commitea SOLO su scope por pathspec).
#
# Scope exclusivo de un lock vivo (.session-locks/{bucket}.lock · línea
# `PID SKILL TS STORY LANE BUCKET`):
#   - story-folder:  */docs/product/stories/{STORY}/*
#   - module code:   */backend/src/modules/*/{MODULE}/*   (para buckets code:{module})
# Archivos fuera de todo scope exclusivo (shared, harness, lockfiles) = neutros.
#
# Diseño defensivo: FAIL-OPEN ante cualquier error interno (nunca bloquea por un bug
# propio). Override intencional: MULTI_SESSION_ACK=1. Solo actúa con ≥2 locks VIVOS.
#
# Exit: 0 = OK (proceder) · 1 = BLOCK (sweep cross-sesión detectado).

set -uo pipefail

[ "${MULTI_SESSION_ACK:-0}" = "1" ] && exit 0

WT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
LOCK_DIR="${WT}/.session-locks"
[ -d "${LOCK_DIR}" ] || exit 0

# --- Recolectar locks VIVOS (PID con kill -0) + su scope exclusivo ---
# Arrays paralelos: labels[i] = id legible · cada lock aporta sus globs de scope.
declare -a LOCK_LABELS=()
declare -a LOCK_STORIES=()
declare -a LOCK_MODULES=()
live_count=0
for lf in "${LOCK_DIR}"/*.lock; do
  [ -f "$lf" ] || continue
  read -r pid skill ts story lane bucket < "$lf" 2>/dev/null || continue
  [ -n "${pid:-}" ] || continue
  case "$pid" in (*[!0-9]*|'') continue;; esac
  kill -0 "$pid" 2>/dev/null || continue   # stale/dead → ignorar
  live_count=$((live_count + 1))
  LOCK_LABELS+=("${story:-?}/${bucket:-?}/pid${pid}")
  LOCK_STORIES+=("${story:-}")
  mod="${bucket#code:}"
  [ "${mod}" = "${bucket:-}" ] && mod=""   # bucket sin code: → sin módulo
  LOCK_MODULES+=("${mod}")
done

[ "${live_count}" -lt 2 ] && exit 0   # paralelo solo importa con ≥2 sesiones vivas

STAGED="$(git diff --cached --name-only --diff-filter=ACMRD 2>/dev/null)" || exit 0
[ -n "${STAGED}" ] || exit 0

# --- ¿Cuántos locks vivos DISTINTOS toca el set staged? ---
declare -A HIT=()
n="${#LOCK_LABELS[@]}"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  i=0
  while [ "$i" -lt "$n" ]; do
    st="${LOCK_STORIES[$i]}"; md="${LOCK_MODULES[$i]}"; lbl="${LOCK_LABELS[$i]}"
    if [ -n "$st" ] && [ "$st" != "-" ]; then
      case "/$f" in (*"/docs/product/stories/${st}/"*) HIT["$lbl"]=1;; esac
    fi
    if [ -n "$md" ]; then
      case "/$f" in (*"/backend/src/modules/"*"/${md}/"*) HIT["$lbl"]=1;; esac
    fi
    i=$((i + 1))
  done
done <<< "${STAGED}"

if [ "${#HIT[@]}" -ge 2 ]; then
  echo ""
  echo "─────────────────────────────────────────────────────────────"
  echo "PRE-COMMIT BLOCKED — multi-session sweep guard (HB-31, cement 2026-06-04)"
  echo ""
  echo "Este commit stagea archivos del scope EXCLUSIVO de ${#HIT[@]} sesiones VIVAS distintas:"
  for l in "${!HIT[@]}"; do echo "  • ${l}"; done
  echo ""
  echo "El paralelo en el mismo hub está PERMITIDO, pero cada sesión commitea SOLO su"
  echo "scope por pathspec exacto — NUNCA 'git add -A/-u/.'. Sacá del stage lo ajeno:"
  echo "  git restore --staged <archivos-de-otra-sesión>"
  echo ""
  echo "Override (solo si es un commit cross-sesión intencional + ratificado):"
  echo "  MULTI_SESSION_ACK=1 git commit ..."
  echo "─────────────────────────────────────────────────────────────"
  exit 1
fi
exit 0
