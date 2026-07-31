#!/usr/bin/env bash
set -uo pipefail
# cloudflared-setup.sh — Provisión NO-INTERACTIVA del Cloudflare Tunnel de dev de
# una marca, vía la Cloudflare REST API (curl). Deja la credencial gitignored que
# el container `{brand}_cloudflared_dev` (locally-managed) monta.
#
# SSoT: .claude/rules/definition-of-done-live-verify.md § "Provisión del túnel"
#
# Usage:
#   scripts/cloudflared-setup.sh vitalia [--recreate]
#
# ✅ NO-INTERACTIVO — usa un API token de cuenta (cfat_) en lugar de login browser.
#    NO requiere el binario cloudflared en el host (el container docker corre el túnel).
#
# Credenciales API (gitignored, una por marca):
#   {brand}/deploy/cloudflared/.credentials/cf-api.env
#     CLOUDFLARE_API_TOKEN=cfat_...        (account-scoped: Tunnel:Edit + DNS:Edit)
#     CLOUDFLARE_ACCOUNT_ID=...
#     CLOUDFLARE_ZONE=...                  (ej. vitalialat.com)
#   (fallback: lee las mismas keys de {brand}/.env.dev)
#
# Qué hace (IDEMPOTENTE · no-destructivo por default):
#   1. Carga API token + account + zone (cf-api.env o .env.dev).
#   2. Verifica acceso a la cuenta (read-only).
#   3. Resuelve el tunnel: por id de dev-config.yml o por nombre `dev-{brand}`.
#        - EXISTE  → reusa (NO recrea). Si falta la credencial local, avisa cómo obtenerla.
#        - NO existe → crea locally-managed con secret nuevo + escribe la credencial JSON.
#   4. Asegura el CNAME {hostname} → {tunnel_id}.cfargotunnel.com (proxied; idempotente).
#   5. Resuelve placeholder <TUNNEL_ID> en dev-config.yml si aplica.
#   --recreate: borra el tunnel existente y crea uno nuevo (DESTRUCTIVO, explícito).

WS="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BRAND="${1:?Usage: cloudflared-setup.sh vitalia [--recreate]}"
RECREATE=0; [[ "${2:-}" == "--recreate" ]] && RECREATE=1

CF_DIR="${WS}/${BRAND}/deploy/cloudflared"
CF_CONFIG="${CF_DIR}/dev-config.yml"
CF_CREDS_DIR="${CF_DIR}/.credentials"
CF_CREDS="${CF_CREDS_DIR}/dev-tunnel.json"
CF_API_ENV="${CF_CREDS_DIR}/cf-api.env"
ENV_DEV="${WS}/${BRAND}/.env.dev"

err() { echo "✗ $*" >&2; }
die() { err "$*"; exit 1; }

[[ -f "${CF_CONFIG}" ]] || die "No existe ${CF_CONFIG} (creá la config del tunnel primero — mirá vitalia/deploy/cloudflared/dev-config.yml)."
command -v curl &>/dev/null || die "curl no encontrado."
command -v python3 &>/dev/null || die "python3 no encontrado (para parsear JSON)."

# ── 1. Cargar API creds (cf-api.env preferido; fallback .env.dev) ─────────────
# (inline en el scope principal — NO en $(...) o el source no exporta al padre)
CREDS_SRC=""
if [[ -f "${CF_API_ENV}" ]]; then CREDS_SRC="${CF_API_ENV}";
elif [[ -f "${ENV_DEV}" ]] && grep -q '^CLOUDFLARE_API_TOKEN=' "${ENV_DEV}"; then CREDS_SRC="${ENV_DEV}"; fi
[[ -n "${CREDS_SRC}" ]] || die "No encuentro CLOUDFLARE_API_TOKEN en ${CF_API_ENV} ni ${ENV_DEV}.
  Dejá un cf-api.env (gitignored) con CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_ZONE."
# shellcheck disable=SC1090
set -a; source <(grep -E '^CLOUDFLARE_' "${CREDS_SRC}"); set +a
: "${CLOUDFLARE_API_TOKEN:?falta CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?falta CLOUDFLARE_ACCOUNT_ID}"
: "${CLOUDFLARE_ZONE:?falta CLOUDFLARE_ZONE}"

HOSTNAME="$(grep -oE 'hostname:[[:space:]]*dev-app[^[:space:]]+' "${CF_CONFIG}" | head -1 | sed -E 's/hostname:[[:space:]]*//')"
CFG_TUNNEL_ID="$(grep -oE '^tunnel:[[:space:]]*[^[:space:]]+' "${CF_CONFIG}" | head -1 | sed -E 's/^tunnel:[[:space:]]*//')"
TUNNEL_NAME="dev-${BRAND}"

echo "── cloudflared-setup (no-interactive) :: ${BRAND} ─────────────────────────"
echo "  creds:    ${CREDS_SRC/#${WS}\//} (gitignored)"
echo "  hostname: ${HOSTNAME:-<no encontrado>}"
echo "  zona:     ${CLOUDFLARE_ZONE}"
echo "  tunnel:   nombre=${TUNNEL_NAME} · id-config=${CFG_TUNNEL_ID:-<none>}"
echo
[[ -n "${HOSTNAME}" ]] || die "No pude leer 'hostname:' de dev-config.yml."

API="https://api.cloudflare.com/client/v4"
cf() { curl -sS --max-time 25 -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H "Content-Type: application/json" "$@"; }
jq_py() { python3 -c "import sys,json;d=json.load(sys.stdin);$1" 2>/dev/null; }

# ── 2. Verificar acceso a la cuenta (read-only) ──────────────────────────────
echo "▸ 1/5 — verificar acceso a la cuenta …"
ACCT_CHECK="$(cf "${API}/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel?per_page=1")"
echo "${ACCT_CHECK}" | jq_py 'sys.exit(0 if d.get("success") else 1)' || die "El API token no tiene acceso a cfd_tunnel en la cuenta (scope Tunnel:Edit?). Resp: $(echo "${ACCT_CHECK}" | head -c160)"
echo "  ✓ token válido (account-scoped)"

# ── 3. Resolver tunnel (reusar existente · crear si falta · --recreate borra) ─
echo
echo "▸ 2/5 — resolver tunnel '${TUNNEL_NAME}' …"
LIST="$(cf "${API}/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel?is_deleted=false&name=${TUNNEL_NAME}")"
TUNNEL_ID="$(echo "${LIST}" | jq_py 'r=d.get("result") or [];print(r[0]["id"] if r else "")')"
# fallback: por id de la config si el nombre no matchea
if [[ -z "${TUNNEL_ID}" && -n "${CFG_TUNNEL_ID}" && "${CFG_TUNNEL_ID}" != "<TUNNEL_ID>" ]]; then
  INFO="$(cf "${API}/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel/${CFG_TUNNEL_ID}")"
  echo "${INFO}" | jq_py 'sys.exit(0 if d.get("success") else 1)' && TUNNEL_ID="${CFG_TUNNEL_ID}"
fi

if [[ -n "${TUNNEL_ID}" && "${RECREATE}" -eq 1 ]]; then
  echo "  ⚠ --recreate: borrando tunnel ${TUNNEL_ID} …"
  cf -X DELETE "${API}/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}" >/dev/null
  TUNNEL_ID=""
fi

NEW_TUNNEL=0
if [[ -n "${TUNNEL_ID}" ]]; then
  echo "  ✓ Ya existe: ${TUNNEL_ID} (reuso, NO recreo)"
else
  echo "  ▸ Creando tunnel locally-managed nuevo …"
  SECRET="$(openssl rand -base64 32 2>/dev/null)" || die "openssl no disponible para generar el secret."
  CREATE="$(cf -X POST "${API}/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel" \
    --data "$(python3 -c "import json,sys;print(json.dumps({'name':'${TUNNEL_NAME}','config_src':'local','tunnel_secret':'${SECRET}'}))")")"
  TUNNEL_ID="$(echo "${CREATE}" | jq_py 'print((d.get("result") or {}).get("id",""))')"
  [[ -n "${TUNNEL_ID}" ]] || die "create falló: $(echo "${CREATE}" | head -c200)"
  NEW_TUNNEL=1
  echo "  ✓ Creado: ${TUNNEL_ID}"
  # Escribir credencial JSON (locally-managed) — gitignored
  mkdir -p "${CF_CREDS_DIR}"
  python3 -c "import json;print(json.dumps({'AccountTag':'${CLOUDFLARE_ACCOUNT_ID}','TunnelID':'${TUNNEL_ID}','TunnelSecret':'${SECRET}'}))" > "${CF_CREDS}"
  chmod 600 "${CF_CREDS}"
  echo "  ✓ Credencial escrita: ${CF_CREDS/#${WS}\//} (gitignored)"
fi

# ── 4. DNS CNAME idempotente ─────────────────────────────────────────────────
echo
echo "▸ 3/5 — DNS CNAME ${HOSTNAME} → ${TUNNEL_ID}.cfargotunnel.com …"
ZID="$(cf "${API}/zones?name=${CLOUDFLARE_ZONE}" | jq_py 'r=d.get("result") or [];print(r[0]["id"] if r else "")')"
[[ -n "${ZID}" ]] || die "No encontré la zona ${CLOUDFLARE_ZONE} (scope Zone:Read/DNS:Edit?)."
REC="$(cf "${API}/zones/${ZID}/dns_records?type=CNAME&name=${HOSTNAME}")"
REC_ID="$(echo "${REC}" | jq_py 'r=d.get("result") or [];print(r[0]["id"] if r else "")')"
DNS_BODY="$(python3 -c "print(__import__('json').dumps({'type':'CNAME','name':'${HOSTNAME}','content':'${TUNNEL_ID}.cfargotunnel.com','proxied':True,'ttl':1}))")"
if [[ -n "${REC_ID}" ]]; then
  cf -X PUT "${API}/zones/${ZID}/dns_records/${REC_ID}" --data "${DNS_BODY}" | jq_py 'sys.exit(0 if d.get("success") else 1)' \
    && echo "  ✓ CNAME actualizado (idempotente)" || echo "  ⚠ update CNAME devolvió error (revisá scope DNS:Edit)."
else
  cf -X POST "${API}/zones/${ZID}/dns_records" --data "${DNS_BODY}" | jq_py 'sys.exit(0 if d.get("success") else 1)' \
    && echo "  ✓ CNAME creado" || echo "  ⚠ create CNAME devolvió error."
fi

# ── 5. Resolver placeholder + chequear credencial local ──────────────────────
echo
echo "▸ 4/5 — sincronizar tunnel id en dev-config.yml …"
if grep -q '<TUNNEL_ID>' "${CF_CONFIG}"; then
  sed -i "s/<TUNNEL_ID>/${TUNNEL_ID}/g" "${CF_CONFIG}"
  echo "  ✓ Placeholder reemplazado por ${TUNNEL_ID} (revisá diff + commiteá dev-config.yml)."
else
  echo "  ✓ dev-config.yml ya tiene id concreto."
fi

echo
echo "▸ 5/5 — credencial local para el container locally-managed …"
if [[ -f "${CF_CREDS}" ]]; then
  echo "  ✓ ${CF_CREDS/#${WS}\//} presente"
elif [[ "${NEW_TUNNEL}" -eq 0 ]]; then
  echo "  ⚠ Tunnel EXISTE pero NO hay credencial local en este worktree:"
  echo "      ${CF_CREDS/#${WS}\//}"
  echo "    El secret de un tunnel existente NO se recupera vía API. Opciones:"
  echo "      a) Copiala del worktree donde se creó (ej. ~/Proyectos/luana-platform/${BRAND}/deploy/cloudflared/.credentials/dev-tunnel.json)."
  echo "      b) Recreá el tunnel: scripts/cloudflared-setup.sh ${BRAND} --recreate (DESTRUCTIVO: cambia el id)."
fi

echo
echo "═══════════════════════════════════════════════════════════════════════"
echo "  Tunnel de ${BRAND} listo (id ${TUNNEL_ID}). Próximo paso:"
echo "    make dev-app-${BRAND}        # levanta stack + tunnel + verifica"
echo "  Credencial + cf-api.env gitignored — NUNCA commitear."
echo "═══════════════════════════════════════════════════════════════════════"
