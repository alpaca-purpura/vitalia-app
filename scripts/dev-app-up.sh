#!/usr/bin/env bash
set -uo pipefail
# dev-app-up.sh — Levanta el stack dev de una marca + (si hay credenciales) el
# Cloudflare Tunnel, y VERIFICA que la app responde, dejando todo listo para la
# verificación live (Definition of Done — Critical Rule #37).
#
# SSoT: .claude/rules/definition-of-done-live-verify.md
#       vitalia/docs/domains/dev-app/live-verification.md (runbook)
#
# Usage:
#   scripts/dev-app-up.sh [brand]     # brand opcional; se infiere del worktree
#   make dev-app-vitalia              # wrapper
#
# Comportamiento (IDEMPOTENTE):
#   1. Levanta backend+frontend de la marca (reusa `make dev-{brand}`).
#   2. Espera health del backend (/health) y reachability del frontend.
#   3. Si existe la credencial del tunnel → levanta cloudflared + verifica el
#      dominio público dev-app.{brand}*. Si NO existe → FALLBACK a localhost
#      (verificación válida; falta solo el dominio público — ver rule).
#   4. Imprime URL + usuario de prueba + de dónde salen las credenciales.
#
# NO es deploy a cloud: el "entorno dev" = cloudflared tunnel locally-managed
# que expone el stack local. GitHub Actions sigue deferred.

WS="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ── 1. Resolver brand (single-brand standalone: default vitalia) ─────────────
BRAND="${1:-vitalia}"

# ── 2. Puertos ───────────────────────────────────────────────────────────────
case "${BRAND}" in
  vitalia)  BE_PORT=8002; FE_PORT=3002 ;;
  *) echo "✗ Marca desconocida: ${BRAND} (single-brand: vitalia)" >&2; exit 2 ;;
esac

CF_CONFIG="${WS}/${BRAND}/deploy/cloudflared/dev-config.yml"
CF_CREDS="${WS}/${BRAND}/deploy/cloudflared/.credentials/dev-tunnel.json"

# Hostname público: se parsea del dev-config.yml (vitalialat.com).
HOSTNAME=""
if [[ -f "${CF_CONFIG}" ]]; then
  HOSTNAME="$(grep -oE 'hostname:[[:space:]]*dev-app[^[:space:]]+' "${CF_CONFIG}" | head -1 | sed -E 's/hostname:[[:space:]]*//')"
fi

echo "── dev-app-up :: ${BRAND} ──────────────────────────────────────────────"
echo "  worktree: ${WS}"
echo "  puertos:  backend :${BE_PORT}  ·  frontend :${FE_PORT}"
[[ -n "${HOSTNAME}" ]] && echo "  dominio:  https://${HOSTNAME}"

if ! command -v docker &>/dev/null; then
  echo "✗ docker no disponible — no puedo levantar el stack." >&2
  exit 1
fi

# ── 3. Levantar stack (idempotente; reusa el target make canónico) ───────────
echo
echo "▸ Levantando stack (make dev-${BRAND}) …"
if ! make -C "${WS}" "dev-${BRAND}"; then
  echo "✗ make dev-${BRAND} falló — revisá docker." >&2
  exit 1
fi

# ── helper: poll de un endpoint hasta que responda (o timeout) ───────────────
wait_http() {  # $1=url  $2=label  $3=max_intentos
  local url="$1" label="$2" max="${3:-30}" i=1 code
  while (( i <= max )); do
    code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 4 "${url}" 2>/dev/null || true)"
    if [[ -n "${code}" && "${code}" != "000" ]]; then
      echo "  ✓ ${label} responde (HTTP ${code}) tras ${i} intento(s)"
      return 0
    fi
    sleep 2; ((i++))
  done
  echo "  ✗ ${label} no respondió tras ${max} intentos (${url})"
  return 1
}

echo
echo "▸ Esperando readiness del stack …"
BE_OK=0; FE_OK=0
wait_http "http://127.0.0.1:${BE_PORT}/health" "backend /health" 40 && BE_OK=1
# Next dev compila on-demand; el primer hit puede tardar — más intentos.
wait_http "http://127.0.0.1:${FE_PORT}/" "frontend raíz" 60 && FE_OK=1

if [[ "${BE_OK}" -ne 1 || "${FE_OK}" -ne 1 ]]; then
  echo
  echo "✗ El stack no quedó listo (backend=${BE_OK} frontend=${FE_OK})." >&2
  echo "  Diagnóstico: docker logs luana-dev-${BRAND}_backend_dev-1 --tail 60" >&2
  exit 1
fi

# ── 4. Tunnel: solo si hay credencial; si no, fallback localhost ─────────────
PUBLIC_OK=0
URL="http://127.0.0.1:${FE_PORT}"
if [[ -n "${HOSTNAME}" && -f "${CF_CREDS}" ]]; then
  echo
  echo "▸ Levantando Cloudflare Tunnel (make dev-${BRAND}-tunnel) …"
  if make -C "${WS}" "dev-${BRAND}-tunnel"; then
    if wait_http "https://${HOSTNAME}/" "dominio público" 30; then
      PUBLIC_OK=1
      URL="https://${HOSTNAME}"
    else
      echo "  ⚠ El tunnel se levantó pero el dominio no respondió aún."
      echo "    Logs: docker logs luana-dev-${BRAND}_cloudflared_dev-1 --tail 30"
    fi
  else
    echo "  ⚠ make dev-${BRAND}-tunnel falló — sigo con fallback localhost."
  fi
else
  echo
  echo "▸ Tunnel OMITIDO — sin credencial en:"
  echo "    ${CF_CREDS}"
  echo "  FALLBACK localhost (verificación VÁLIDA per rule #37; falta solo el"
  echo "  dominio público + JWT Clerk del dominio real). Para el dominio público:"
  echo "    scripts/cloudflared-setup.sh ${BRAND}   # requiere login Cloudflare (Chris)"
fi

# ── 5. Resumen + credenciales de prueba ──────────────────────────────────────
ENV_FILE="${WS}/${BRAND}/.env.dev"
echo
echo "═══════════════════════════════════════════════════════════════════════"
echo "  dev-app LISTO para verificación live — ${BRAND}"
echo "  URL:     ${URL}"
[[ "${PUBLIC_OK}" -eq 1 ]] && echo "  modo:    DOMINIO PÚBLICO (Clerk real)" \
                           || echo "  modo:    LOCALHOST (fallback — documentar en dod_evidence)"
if [[ "${BRAND}" == "vitalia" ]]; then
  echo "  usuario: dr.demo@vitalialat.com (owner tenant Sanaré)"
fi
if [[ -f "${ENV_FILE}" ]]; then
  found="$(grep -oE '^(DEV_APP_TEST_PASSWORD|DEV_APP_TEST_EMAIL|CLERK_TESTING_TOKEN_[A-Z]+)' "${ENV_FILE}" 2>/dev/null | paste -sd' ' -)"
  [[ -n "${found}" ]] && echo "  creds:   en ${BRAND}/.env.dev → ${found}" \
                      || echo "  creds:   ${BRAND}/.env.dev no tiene DEV_APP_TEST_* (ver rule #37)"
else
  echo "  creds:   ${BRAND}/.env.dev ausente"
fi
echo "  verificá: Chrome DevTools MCP (live) + Playwright autenticado (golden)"
echo "  SSoT:    .claude/rules/definition-of-done-live-verify.md"
echo "═══════════════════════════════════════════════════════════════════════"
