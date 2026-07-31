#!/usr/bin/env bash
set -uo pipefail
# e2e-preflight.sh — Chequeo previo a correr Playwright E2E de una marca.
# Verifica que el stack esté arriba y que existan los insumos de auth Clerk,
# ANTES de gastar tiempo en `npx playwright test`.
#
# SSoT: .claude/rules/e2e-testing.md · skill playwright-expert
#
# Usage:
#   scripts/e2e-preflight.sh [brand]   # brand opcional; se infiere del worktree
#
# Exit codes:
#   0 = READY (stack arriba; warnings soft no bloquean)
#   1 = BLOQUEADO (stack abajo) — levantá `make dev-{brand}` primero

WS="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Single-brand standalone: default = vitalia
BRAND="${1:-vitalia}"

case "${BRAND}" in
  vitalia)  BE_PORT=8002; FE_PORT=3002 ;;
  *) echo "✗ Marca desconocida: ${BRAND} (single-brand: vitalia)" >&2; exit 2 ;;
esac

echo "── e2e-preflight :: ${BRAND} ──────────────────────────────────────────"
echo "  frontend :${FE_PORT}  ·  backend :${BE_PORT}"

WARN=0; BLOCK=0

http_code() {  # $1=url → imprime código o vacío
  curl -fsS -o /dev/null -w '%{http_code}' --max-time 4 "$1" 2>/dev/null || true
}

# ── 1. Frontend arriba (bloqueante) ──────────────────────────────────────────
fe="$(http_code "http://127.0.0.1:${FE_PORT}/")"
if [[ -n "${fe}" && "${fe}" != "000" ]]; then
  echo "  ✓ frontend responde (HTTP ${fe})"
else
  echo "  ✗ frontend NO responde en :${FE_PORT} → levantá: make dev-${BRAND}"
  BLOCK=1
fi

# ── 2. Backend health (bloqueante) ───────────────────────────────────────────
be="$(http_code "http://127.0.0.1:${BE_PORT}/health")"
if [[ -n "${be}" && "${be}" != "000" ]]; then
  echo "  ✓ backend /health responde (HTTP ${be})"
else
  echo "  ✗ backend NO responde en :${BE_PORT}/health → levantá: make dev-${BRAND}"
  BLOCK=1
fi

# ── 3. Clerk testing token (soft warn) ───────────────────────────────────────
ENV_FILE="${WS}/${BRAND}/.env.dev"
BRAND_UP="$(echo "${BRAND}" | tr '[:lower:]' '[:upper:]')"
if [[ -f "${ENV_FILE}" ]] && grep -qE "^CLERK_TESTING_TOKEN_${BRAND_UP}" "${ENV_FILE}"; then
  echo "  ✓ CLERK_TESTING_TOKEN_${BRAND_UP} presente en .env.dev"
else
  echo "  ⚠ CLERK_TESTING_TOKEN_${BRAND_UP} ausente → el auth de Clerk en tests puede fallar (Bot traffic)."
  WARN=1
fi

# ── 4. Storage state de Clerk (soft warn — se regenera en primer auth) ───────
CLERK_STATE="${WS}/${BRAND}/frontend/playwright/.clerk/user.json"
if [[ -f "${CLERK_STATE}" ]]; then
  echo "  ✓ storageState Clerk presente"
else
  echo "  ⚠ storageState Clerk ausente (${BRAND}/frontend/playwright/.clerk/user.json) → se crea en el primer login. Si falla: npm run test:e2e:fresh"
  WARN=1
fi

# ── 5. playwright.config presente (soft) ─────────────────────────────────────
if [[ -f "${WS}/${BRAND}/frontend/playwright.config.ts" ]]; then
  echo "  ✓ playwright.config.ts presente"
else
  echo "  ⚠ ${BRAND}/frontend/playwright.config.ts no encontrado"
  WARN=1
fi

echo "───────────────────────────────────────────────────────────────────────"
if [[ "${BLOCK}" -eq 1 ]]; then
  echo "✗ BLOQUEADO: el stack no está arriba. Corré 'make dev-${BRAND}' y reintentá."
  exit 1
fi
if [[ "${WARN}" -eq 1 ]]; then
  echo "✓ READY (con warnings soft — revisá arriba). Correr:"
else
  echo "✓ READY. Correr:"
fi
echo "    cd ${BRAND}/frontend && E2E_BASE_URL=http://localhost:${FE_PORT} npx playwright test --project=smoke"
echo "  ℹ si specs TARDÍOS (autosave) throttlean en suites largas → es el session-token TTL 60s de Clerk (no es bug):"
echo "    .claude/skills/playwright-expert/references/clerk-auth-deep-dive.md § HB-28 (dashboard-only · mitigación retries=1 ya aceptada)"
exit 0
