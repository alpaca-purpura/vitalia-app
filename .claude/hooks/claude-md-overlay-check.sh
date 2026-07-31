#!/usr/bin/env bash
# claude-md-overlay-check — SessionStart hook
#
# tier: hybrid · core = overlay-walk advisory mechanism ·
#       project = brand enum + 165-line cap → seam brands[] (W5)
#
# Advisory hook que verifica:
#  - Si cwd cae dentro `vitalia/` PERO `vitalia/CLAUDE.md` overlay
#    no existe → emite advisory.
#
# NO carga el overlay (Claude Code lo hace built-in via walking ancestors).
# Solo valida existencia + sugiere bootstrap si missing.
#
# Falla suave: exit 0 siempre (nunca bloquea SessionStart).
#
# Origen: conversación 2026-05-27 — Chris pidió hierarchy CLAUDE.md.
# SSoT: .claude/rules/claude-md-overlay.md

set -uo pipefail

# Leer stdin JSON (SessionStart hook recibe { sessionId, cwd, ... })
INPUT=$(cat 2>/dev/null || true)
if [[ -z "${INPUT}" ]]; then
  exit 0
fi

# Extraer cwd
CWD=""
if command -v jq >/dev/null 2>&1; then
  CWD=$(echo "${INPUT}" | jq -r '.cwd // empty' 2>/dev/null || true)
fi

# Fallback: usar pwd actual del proceso
if [[ -z "${CWD}" ]]; then
  CWD=$(pwd)
fi

# Detectar brand desde cwd path
# Pattern: cwd dentro de la brand dir en root (ej: /path/to/vitalia-app/vitalia/...)
# (el patrón legacy luana-{brand} se mantiene en la regex por backcompat, inofensivo)
BRAND=""
# Brand enum from the seam (project.config.yaml · harness_config.py) — no hardcoded list
# (charter §3 DIP · W5b). Repo root resolved from this hook's own location (robust to the
# analyzed cwd). Loud-degrade to empty: no brand matched → exit 0 (no overlay), the same safe
# outcome a PRINCIPAL/protocol cwd already produces.
_OV_REPO="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
OV_BRANDS="$("${_OV_REPO}/.venv/bin/python" "${_OV_REPO}/scripts/harness_config.py" brands.loop_order 2>/dev/null | tr '\n' ' ')"
[ -z "${OV_BRANDS}" ] && echo "WARN: project.config.yaml brands.loop_order unreadable — overlay brand detection degraded" >&2
for B in ${OV_BRANDS}; do
  if echo "${CWD}" | grep -qE "(luana-${B}([-/]|$)|/${B}([-/]|$))"; then
    BRAND="${B}"
    break
  fi
done

# Si no se detectó brand → cwd es PRINCIPAL o protocol o core — no overlay needed
if [[ -z "${BRAND}" ]]; then
  exit 0
fi

# Buscar workspace root (debe contener .git)
WS=""
CHECK="${CWD}"
while [[ "${CHECK}" != "/" && "${CHECK}" != "" ]]; do
  if [[ -d "${CHECK}/.git" || -f "${CHECK}/.git" ]]; then
    WS="${CHECK}"
    break
  fi
  CHECK=$(dirname "${CHECK}")
done

if [[ -z "${WS}" ]]; then
  exit 0
fi

# Verificar overlay exists
OVERLAY="${WS}/${BRAND}/CLAUDE.md"

if [[ ! -f "${OVERLAY}" ]]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "advisory CLAUDE.md overlay missing — cwd cae dentro brand ${BRAND} pero ${OVERLAY} no existe. Per .claude/rules/claude-md-overlay.md, cada brand activa debería tener su overlay. Para bootstrap brand nueva: tomar como referencia ${WS}/vitalia/CLAUDE.md (overlay canónico de ejemplo; no hay template dedicado aún). Mientras tanto: sesión continúa pero sin contexto brand-specific auto-cargado."
  }
}
EOF
  exit 0
fi

# Overlay exists — sanity check size (cap 165 líneas per rule)
LINE_COUNT=$(wc -l < "${OVERLAY}" 2>/dev/null || echo 0)
if [[ "${LINE_COUNT}" -gt 165 ]]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "advisory ${BRAND}/CLAUDE.md exceeds soft cap (${LINE_COUNT} líneas > 165). Per .claude/rules/claude-md-overlay.md, brand overlay debería ser ≤165 líneas. Considerá mover detalle a ${WS}/${BRAND}/docs/domains/ con pointer."
  }
}
EOF
  exit 0
fi

# All OK — silent (no advisory needed)
exit 0
