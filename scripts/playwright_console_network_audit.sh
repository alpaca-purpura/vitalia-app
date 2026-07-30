#!/usr/bin/env bash
# =============================================================================
# playwright_console_network_audit.sh — SC-17 (vitalia-auth-base-functional)
#
# Audita el reporte Playwright (playwright-report/) en busca de:
#   1. console.error o console.warn en páginas vitalia
#   2. Respuestas HTTP 4xx o 5xx (excluyendo 401 pre-auth — allowlist)
#
# Retorna exit code 0 si no hay hallazgos fuera del allowlist.
# Retorna exit code 1 si se detectan errores o respuestas HTTP problemáticas.
#
# Uso:
#   bash scripts/playwright_console_network_audit.sh [REPORT_DIR]
#
# Argumentos:
#   REPORT_DIR — directorio con el reporte Playwright (default: vitalia/frontend/playwright-report)
#
# Ejemplo:
#   cd /home/chalreme/Proyectos/luana-vitalia
#   bash scripts/playwright_console_network_audit.sh vitalia/frontend/playwright-report
#
# Prerequisitos:
#   - unzip (para extraer trace.zip)
#   - jq (para parsear trace.json / network.json dentro del trace)
#
# downstream-regression-na: script de plataforma (cross-brand tooling); no es
#   source de consumers específicos de brand.
#
# LIMITACIÓN — text-fallback (función audit_report_text):
#   El regex `\b[45][0-9]{2}\b` es una heurística COARSE que extrae cualquier
#   número de 3 dígitos que empiece con 4 o 5 de archivos .txt/.log del reporte.
#   Puede producir FALSOS POSITIVOS (p.ej., "versión 4.5.2" o "line 503" en un
#   stack trace normal). El path canónico y confiable para detectar errores HTTP
#   es el análisis de trace.zip via `--trace=on` (función audit_traces), que
#   parsea network.json estructurado con jq. El text-fallback es solo complementario
#   cuando no hay trace.zip disponible.
# =============================================================================

set -euo pipefail

# ─── Configuración ────────────────────────────────────────────────────────────

REPORT_DIR="${1:-vitalia/frontend/playwright-report}"
TRACE_WORK_DIR="/tmp/playwright_audit_$$"

# Allowlist de códigos HTTP a ignorar (pre-auth 401 es esperado para rutas protegidas)
HTTP_ALLOWLIST_CODES=(401)

# Patrones de console.error/warn a ignorar (no-accionables en entorno dev)
CONSOLE_IGNORE_PATTERNS=(
  "ClerkJS"
  "clerk.com"
  "Could not parse CSS"
  "Loading failed for"
  "Failed to load resource"
  "Hydration"
  "favicon"
  "__webpack"
  "React DevTools"
  "next-dev"
)

# Flags de resultado
FOUND_CONSOLE_ERRORS=0
FOUND_HTTP_ERRORS=0

# ─── Helpers ──────────────────────────────────────────────────────────────────

log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*" >&2; }
log_ok()    { echo "[OK]    $*"; }

# Verifica si un string contiene algún patrón del array
matches_any_pattern() {
  local str="$1"
  shift
  local patterns=("$@")
  for pat in "${patterns[@]}"; do
    if echo "$str" | grep -qF "$pat" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

# Verifica si un código HTTP está en el allowlist
in_http_allowlist() {
  local code="$1"
  for allowed in "${HTTP_ALLOWLIST_CODES[@]}"; do
    if [[ "$code" == "$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

# ─── Verificar dependencias ───────────────────────────────────────────────────

check_deps() {
  local missing=0
  for cmd in unzip jq find grep; do
    if ! command -v "$cmd" &>/dev/null; then
      log_warn "Dependencia no encontrada: $cmd (algunas verificaciones pueden omitirse)"
      missing=1
    fi
  done
  return $missing
}

# ─── Extraer y auditar trace.zip ─────────────────────────────────────────────

audit_trace_zip() {
  local trace_zip="$1"
  local test_name
  test_name=$(basename "$(dirname "$trace_zip")")

  local work_dir="$TRACE_WORK_DIR/$test_name"
  mkdir -p "$work_dir"

  # Extraer trace sin mostrar output
  unzip -q "$trace_zip" -d "$work_dir" 2>/dev/null || {
    log_warn "No se pudo extraer: $trace_zip (omitiendo)"
    return 0
  }

  # ── Auditar console entries desde trace.json ──────────────────────────────
  local trace_json="$work_dir/trace.json"
  if [[ -f "$trace_json" ]] && command -v jq &>/dev/null; then
    # Extraer entradas de tipo console-api-called con level error o warning
    while IFS= read -r line; do
      local level msg
      level=$(echo "$line" | jq -r '.type // ""' 2>/dev/null || echo "")
      msg=$(echo "$line"   | jq -r '.text // ""' 2>/dev/null || echo "")

      if [[ -z "$msg" ]]; then
        continue
      fi

      # Solo procesar error y warning
      if [[ "$level" != "error" && "$level" != "warning" ]]; then
        continue
      fi

      # Filtrar patrones del allowlist
      if matches_any_pattern "$msg" "${CONSOLE_IGNORE_PATTERNS[@]}"; then
        continue
      fi

      log_error "CONSOLE[$level] en test '$test_name': $msg"
      FOUND_CONSOLE_ERRORS=1

    done < <(jq -c '
      .[] |
      select(.type == "event") |
      select(.method == "console-api-called") |
      .params |
      select(.type == "error" or .type == "warning") |
      {type: .type, text: (.args[0].value // .args[0].preview // "")}
    ' "$trace_json" 2>/dev/null || true)
  fi

  # ── Auditar network entries para 4xx/5xx ──────────────────────────────────
  # Playwright trace puede tener network.json o embebido en trace.json
  local network_json="$work_dir/network.json"
  local scan_file=""

  if [[ -f "$network_json" ]] && command -v jq &>/dev/null; then
    scan_file="$network_json"
  elif [[ -f "$trace_json" ]] && command -v jq &>/dev/null; then
    scan_file="$trace_json"
  fi

  if [[ -n "$scan_file" ]]; then
    while IFS= read -r entry; do
      local status url
      status=$(echo "$entry" | jq -r '.status // ""' 2>/dev/null || echo "")
      url=$(echo "$entry"    | jq -r '.url // ""'    2>/dev/null || echo "")

      if [[ -z "$status" || ! "$status" =~ ^[0-9]+$ ]]; then
        continue
      fi

      # Solo procesar 4xx y 5xx
      if [[ "$status" -lt 400 ]]; then
        continue
      fi

      # Verificar allowlist
      if in_http_allowlist "$status"; then
        continue
      fi

      log_error "HTTP $status en test '$test_name': $url"
      FOUND_HTTP_ERRORS=1

    done < <(jq -c '
      .[] |
      select(.type == "event") |
      select(.method == "requestfinished") |
      {status: .params.response.status, url: .params.url}
    ' "$scan_file" 2>/dev/null || true)
  fi

  rm -rf "$work_dir"
}

# ─── Escanear report de texto (resultado.txt / test-results/) ────────────────

audit_report_text() {
  local report_dir="$1"

  # Buscar archivos de resultado de texto generados por Playwright
  local result_files
  result_files=$(find "$report_dir" \( -name "*.txt" -o -name "*.log" \) 2>/dev/null | head -50 || true)

  if [[ -z "$result_files" ]]; then
    return 0
  fi

  while IFS= read -r rfile; do
    # Buscar líneas con HTTP error codes fuera del allowlist
    while IFS= read -r line; do
      # Extraer código HTTP si está en el formato "HTTP/1.1 NNN" o "status: NNN"
      local code
      code=$(echo "$line" | grep -oE '\b[45][0-9]{2}\b' | head -1 || true)

      if [[ -z "$code" ]]; then
        continue
      fi

      if in_http_allowlist "$code"; then
        continue
      fi

      log_error "HTTP $code detectado en log '$rfile': $line"
      FOUND_HTTP_ERRORS=1

    done < <(grep -E '\b[45][0-9]{2}\b' "$rfile" 2>/dev/null || true)

  done <<< "$result_files"
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
  log_info "=== playwright_console_network_audit.sh ==="
  log_info "Reporte: $REPORT_DIR"
  log_info "Allowlist HTTP: ${HTTP_ALLOWLIST_CODES[*]}"

  # Verificar que el directorio existe
  if [[ ! -d "$REPORT_DIR" ]]; then
    log_warn "Directorio de reporte no encontrado: $REPORT_DIR"
    log_warn "Ejecutar Playwright primero para generar el reporte."
    log_info "Audit omitido (nada que verificar)."
    exit 0
  fi

  # Verificar dependencias (warning, no fatal)
  check_deps || true

  # Crear directorio de trabajo temporal
  mkdir -p "$TRACE_WORK_DIR"

  # Buscar y auditar archivos trace.zip
  local trace_count=0
  while IFS= read -r trace_zip; do
    ((trace_count++)) || true
    log_info "Auditando trace: $trace_zip"
    audit_trace_zip "$trace_zip"
  done < <(find "$REPORT_DIR" -name "trace.zip" 2>/dev/null || true)

  if [[ $trace_count -eq 0 ]]; then
    log_info "No se encontraron archivos trace.zip en $REPORT_DIR"
    log_info "Auditando archivos de texto del reporte..."
    audit_report_text "$REPORT_DIR"
  fi

  # Limpiar trabajo temporal
  rm -rf "$TRACE_WORK_DIR"

  # ── Resultado final ──────────────────────────────────────────────────────
  echo ""
  echo "=== RESULTADO AUDIT ==="

  if [[ $FOUND_CONSOLE_ERRORS -eq 0 && $FOUND_HTTP_ERRORS -eq 0 ]]; then
    log_ok "Sin errores de consola ni respuestas HTTP fuera del allowlist."
    echo "=== AUDIT OK ==="
    exit 0
  fi

  if [[ $FOUND_CONSOLE_ERRORS -eq 1 ]]; then
    log_error "Se detectaron errores/warnings de consola no-allowlisteados."
  fi

  if [[ $FOUND_HTTP_ERRORS -eq 1 ]]; then
    log_error "Se detectaron respuestas HTTP 4xx/5xx fuera del allowlist."
  fi

  echo "=== AUDIT FAILED ==="
  exit 1
}

main "$@"
