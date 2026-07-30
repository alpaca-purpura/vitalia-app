#!/usr/bin/env bash
# vitalia/deploy/scripts/post_deploy_smoke.sh
# Post-deploy smoke verification para Vitalia en K8s.
#
# Verifica que el deploy esta funcionando correctamente ANTES de proceder a T-6.b LIVE.
# Ejecutar DESPUES de `kubectl apply` + `kubectl rollout restart`.
#
# Uso:
#   bash vitalia/deploy/scripts/post_deploy_smoke.sh
#
# Variables de entorno opcionales:
#   VITALIA_NAMESPACE    — namespace K8s (default: vitalia)
#   BACKEND_URL          — URL backend (default: https://dev-app.vitalialat.com)
#   ADMIN_URL            — URL admin Streamlit (default: https://vitalia-admin.vitalialat.com)
#   POD_TIMEOUT          — segundos espera pods Ready (default: 120)
#
# Exit codes:
#   0 — todos los checks pasaron
#   1 — uno o mas checks fallaron (ver output para detalle)
#
# Arch ref: vitalia-auth-base-functional T-5 · SC-17 K8s healthcheck + deploy verify

set -euo pipefail

# ── Configuracion ─────────────────────────────────────────────────────────────
NAMESPACE="${VITALIA_NAMESPACE:-vitalia}"
BACKEND_URL="${BACKEND_URL:-https://dev-app.vitalialat.com}"
ADMIN_URL="${ADMIN_URL:-https://vitalia-admin.vitalialat.com}"
POD_TIMEOUT="${POD_TIMEOUT:-120}"

# Colores para output (solo si terminal interactivo)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # Sin color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

FAILED=0

# ── Funciones helper ──────────────────────────────────────────────────────────

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FALLO]${NC} $1"
    FAILED=1
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# ── Check 1: Pods en namespace vitalia listos ─────────────────────────────────
log_info "Verificando pods en namespace '${NAMESPACE}'..."

if ! command -v kubectl &>/dev/null; then
    log_info "kubectl no encontrado — omitiendo verificacion de pods (entorno sin cluster local)"
else
    # Esperar hasta POD_TIMEOUT segundos a que todos los pods esten Ready
    ELAPSED=0
    ALL_READY=false
    while [ $ELAPSED -lt "$POD_TIMEOUT" ]; do
        NOT_READY=$(kubectl get pods -n "${NAMESPACE}" \
            --field-selector=status.phase!=Running \
            --no-headers 2>/dev/null | grep -v "Completed" | wc -l || echo "0")

        if [ "$NOT_READY" -eq 0 ]; then
            ALL_READY=true
            break
        fi

        log_info "  Pods aun iniciando (${ELAPSED}s / ${POD_TIMEOUT}s)..."
        sleep 10
        ELAPSED=$((ELAPSED + 10))
    done

    if [ "$ALL_READY" = "true" ]; then
        POD_LIST=$(kubectl get pods -n "${NAMESPACE}" --no-headers 2>/dev/null | awk '{print $1" "$3}' | tr '\n' ', ')
        log_ok "Pods listos en namespace '${NAMESPACE}': ${POD_LIST}"
    else
        PENDING_PODS=$(kubectl get pods -n "${NAMESPACE}" --no-headers 2>/dev/null | grep -v "Running\|Completed" || true)
        log_fail "Pods NO listos despues de ${POD_TIMEOUT}s:\n${PENDING_PODS}"
    fi
fi

# ── Check 2: /api/health → 200 JSON {status:"ok"} ───────────────────────────
log_info "Verificando backend health: ${BACKEND_URL}/api/health"

HTTP_STATUS=$(curl -fsS -o /tmp/vitalia_health_response.json \
    -w "%{http_code}" \
    --max-time 10 \
    "${BACKEND_URL}/api/health" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    # Verificar que la respuesta contiene status:ok
    if grep -q '"status"' /tmp/vitalia_health_response.json 2>/dev/null; then
        log_ok "/api/health → 200 OK (respuesta: $(cat /tmp/vitalia_health_response.json))"
    else
        log_fail "/api/health → 200 pero respuesta inesperada: $(cat /tmp/vitalia_health_response.json)"
    fi
else
    log_fail "/api/health → HTTP ${HTTP_STATUS} (esperado 200)"
fi

# ── Check 3: Admin /healthz → 200 (Streamlit nativo) ────────────────────────
log_info "Verificando admin health: ${ADMIN_URL}/healthz"

ADMIN_STATUS=$(curl -fsS -o /dev/null \
    -w "%{http_code}" \
    --max-time 10 \
    "${ADMIN_URL}/healthz" 2>/dev/null || echo "000")

if [ "$ADMIN_STATUS" = "200" ]; then
    log_ok "Admin /healthz → 200 OK (Streamlit activo en ${ADMIN_URL})"
else
    log_fail "Admin /healthz → HTTP ${ADMIN_STATUS} (esperado 200) — revisar deployment vitalia-admin"
fi

# ── Check 4: / → 307 redirect a /sign-in (Clerk middleware activo) ──────────
log_info "Verificando redirect auth: ${BACKEND_URL}/ → 307 /sign-in"

# --max-redirs 0 para NO seguir el redirect — queremos verificar el 307
ROOT_STATUS=$(curl -fsS -o /dev/null \
    -w "%{http_code}" \
    --max-time 10 \
    --max-redirs 0 \
    "${BACKEND_URL}/" 2>/dev/null || echo "000")

# Clerk middleware puede retornar 307 o 302 dependiendo de la configuracion
if [ "$ROOT_STATUS" = "307" ] || [ "$ROOT_STATUS" = "302" ]; then
    log_ok "/ → ${ROOT_STATUS} redirect (Clerk middleware activo)"
else
    log_fail "/ → HTTP ${ROOT_STATUS} (esperado 307 o 302 — verificar que el middleware Clerk esta activo)"
fi

# ── Check 5: /sign-in → 200 HTML con "Iniciar sesion" ───────────────────────
log_info "Verificando pagina sign-in: ${BACKEND_URL}/sign-in"

SIGNIN_BODY=$(curl -fsS \
    --max-time 15 \
    "${BACKEND_URL}/sign-in" 2>/dev/null || echo "")

SIGNIN_STATUS=$?

if [ -n "$SIGNIN_BODY" ]; then
    # Verificar que la pagina contiene el texto de la pagina de inicio de sesion
    if echo "$SIGNIN_BODY" | grep -qi "iniciar sesi"; then
        log_ok "/sign-in → 200 HTML contiene 'Iniciar sesion'"
    else
        log_fail "/sign-in → 200 pero no contiene 'Iniciar sesion' — verificar componente Clerk SignIn"
    fi
else
    log_fail "/sign-in → no respuesta o error (verificar que Next.js esta activo)"
fi

# ── Resumen final ────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}RESULTADO: TODOS LOS CHECKS PASARON — Deploy Vitalia verificado${NC}"
    echo "Proceder a T-6.b LIVE smoke (Playwright contra dev-app.vitalialat.com)."
else
    echo -e "${RED}RESULTADO: UNO O MAS CHECKS FALLARON — REVISAR ANTES DE PROCEDER${NC}"
    echo "No proceder a T-6.b hasta resolver los fallos listados arriba."
    echo ""
    echo "Recursos de debug:"
    echo "  kubectl logs deployment/vitalia-app -n ${NAMESPACE} --tail=50"
    echo "  kubectl logs deployment/vitalia-admin -n ${NAMESPACE} --tail=50"
    echo "  kubectl describe pods -n ${NAMESPACE}"
fi
echo "════════════════════════════════════════════════════════════"

exit "$FAILED"
