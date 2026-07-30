#!/usr/bin/env bash
# verify-no-backend-errors.sh — Critical Rule #37 §3 (gate anti-burbuja · lado backend).
#
# Falla (exit 1) si el backend logueó ERROR/Traceback/Exception/500 desde $SINCE.
# Atrapa el caso "la UI devolvió 200 con datos parciales tras tragarse un 500" —
# el backend lo logueó aunque la pantalla no lo muestre.
#
# Uso: capturá el timestamp ANTES de ejercer la acción, luego corré el script:
#   SINCE="$(date -Iseconds)"
#   # ... ejercer la acción real del usuario (write) ...
#   scripts/verify-no-backend-errors.sh vitalia "$SINCE"
#
# Container real (verificado): luana-dev-{brand}_backend_dev-1
set -euo pipefail

BRAND="${1:-vitalia}"
SINCE="${2:-5m}"          # timestamp ISO (ej "2026-06-01T19:00:00") o duración relativa (ej "5m")
CONTAINER="luana-dev-${BRAND}_backend_dev-1"

# Patrones que indican un error real del backend.
PATTERN='ERROR|Traceback|Exception|CRITICAL|500 Internal'
# Allowlist de ruido no-accionable (shutdown esperado, cancelaciones de asyncio).
# Ratchet: shrink-only. Agregar requiere justificación.
ALLOWLIST='asyncio\.CancelledError|KeyboardInterrupt|Application shutdown complete'

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER}"; then
  echo "[verify-no-backend-errors] ⚠️  container ${CONTAINER} no corre — levantá el stack: make dev-app-${BRAND}" >&2
  exit 2
fi

HITS="$(docker logs "${CONTAINER}" --since "${SINCE}" 2>&1 | grep -E "${PATTERN}" | grep -vE "${ALLOWLIST}" || true)"

if [[ -n "${HITS}" ]]; then
  echo "[verify-no-backend-errors] ❌ ${CONTAINER} logueó errores desde ${SINCE}:" >&2
  echo "----------------------------------------------------------------------" >&2
  echo "${HITS}" >&2
  echo "----------------------------------------------------------------------" >&2
  echo "NO es 'done': la UI pudo verse OK pero el backend falló. Diagnosticá el traceback." >&2
  exit 1
fi

echo "[verify-no-backend-errors] ✅ ${CONTAINER} sin ERROR/Traceback/Exception desde ${SINCE}."
