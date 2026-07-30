#!/usr/bin/env bash
# dod-evidence-gate.sh — Layer 6 de Critical Rule #37 (definition-of-done-live-verify.md).
#
# Cement 2026-06-04 (Chris). Backstop MECÁNICO (git hook) del live-verify: hasta hoy el
# gate vivía SOLO a nivel-skill (dev-team Step 4.6 / auditor / pm REFUSE) = conductual,
# saltable si un agente ignora el skill. Este hook bloquea, da igual el agente.
#
# Qué hace: si un commit STAGEA una TRANSICIÓN de checkpoint a `state: developed|done`
# para una story funcional, exige que el checkpoint traiga evidencia live real:
#   dod_live_verified: true   +   dod_evidence: con ≥1 `action:`.
# Story técnica pura → exenta vía `dod_live_verified_skip_reason: <razón>`.
#
# Límite honesto: es PRESENCE-enforcement (que el bloque EXISTA), NO puede forzar que
# la evidencia sea VERDADERA — eso lo dan el chris_verify.signoff humano + el auditor que ejerce
# el write live. Sube el costo de saltarlo en silencio; no mata la mentira deliberada.
#
# Solo dispara sobre la TRANSICIÓN (línea `+state: developed|done` en el diff staged) →
# no molesta re-edits de checkpoints legacy ya en ese estado.
#
# FAIL-OPEN ante error propio (nunca bloquea por un bug suyo). Override ratificado:
# DOD_GATE_ACK=1. Exit: 0 OK · 1 BLOCK.

set -uo pipefail

[ "${DOD_GATE_ACK:-0}" = "1" ] && exit 0
WT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "${WT}" || exit 0

CPS="$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '/docs/product/stories/[^/]+/checkpoint\.md$' || true)"
[ -n "${CPS}" ] || exit 0

violations=""
while IFS= read -r cp; do
  [ -n "${cp}" ] || continue
  # ¿La transición a developed|done está en las líneas AÑADIDAS de este commit?
  added_state="$(git diff --cached -U0 -- "${cp}" 2>/dev/null \
    | grep -E '^\+[[:space:]]*state:[[:space:]]*(developed|done)\b' || true)"
  [ -n "${added_state}" ] || continue
  content="$(git show ":${cp}" 2>/dev/null || true)"
  [ -n "${content}" ] || continue
  # Exención técnica explícita
  if printf '%s\n' "${content}" | grep -qE '^[[:space:]]*dod_live_verified_skip_reason:[[:space:]]*[^[:space:]]'; then
    continue
  fi
  has_flag="$(printf '%s\n' "${content}" | grep -E '^[[:space:]]*dod_live_verified:[[:space:]]*true\b' || true)"
  has_ev="$(printf '%s\n' "${content}" | awk '/^[[:space:]]*dod_evidence:/{f=1; next} f && /action:/{print; exit}' || true)"
  if [ -z "${has_flag}" ] || [ -z "${has_ev}" ]; then
    violations="${violations}
  • ${cp} → state:developed|done SIN dod_live_verified:true + dod_evidence(action)"
  fi
done <<< "${CPS}"

if [ -n "${violations}" ]; then
  echo ""
  echo "─────────────────────────────────────────────────────────────"
  echo "PRE-COMMIT BLOCKED — DoD live-verify gate (Layer 6 · Critical Rule #37)"
  echo "${violations}"
  echo ""
  echo "Una story funcional NO pasa a developed/done sin evidencia live REAL:"
  echo "  dod_live_verified: true"
  echo "  dod_evidence:"
  echo "    - action: <write real ejercido — POST/PATCH/PUT/DELETE>"
  echo "      observed: <efecto: fila DB / persistencia al recargar>"
  echo "      backend_log: <2xx + sin Traceback>"
  echo "GET 200 / e2e mockeado NO cuentan. Ejercé la acción real en el entorno live de la marca."
  echo "Story técnica pura → agregá  dod_live_verified_skip_reason: <razón>"
  echo "Override ratificado: DOD_GATE_ACK=1 git commit ..."
  echo "Ref: .claude/rules/definition-of-done-live-verify.md (Layer 6)"
  echo "─────────────────────────────────────────────────────────────"
  exit 1
fi
exit 0
