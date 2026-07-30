#!/usr/bin/env bash
# code-health.sh — Code maintainability gate (BE + FE), baseline-aware ratchet.
#
# SSoT: docs/process/code-health-gate.md · Origen: HB-61 (2026-06-08).
# Cierra el gap "tools declaradas pero nunca cableadas" (jscpd/knip/madge FE 3/8 · BE sin dead-code).
#
#   BE (Python): jscpd dup + vulture dead-code + interrogate docstrings (+ pip-audit env-wide, once)
#   FE (TS/JS):  fallow dead-code (baseline ratchet) + fallow dupes (threshold)
#
# Filosofía: thresholds que HOY pasan = HARD gate; dead-code (vulture/fallow) = baseline shrink-only
# (no rompe day-1 sobre un codebase legacy; bloquea SÓLO findings NUEVOS). Mismo patrón que el
# ratchet de arch-fitness (KNOWN_* allowlists). NUNCA reportar verde sin correr (anti false-green).
#
# Uso:
#   scripts/quality/code-health.sh <brand> [be|fe|all] [--update-baseline]
#   make code-health BRAND=vitalia            # all
#   make code-health BRAND=vitalia SURFACE=fe
#
# Tools vía npx pinned (sin churn de lockfile). Promote a root devDeps si se quiere offline.
set -uo pipefail

WS="$(git rev-parse --show-toplevel)"
BRAND="${1:-}"
SURFACE="${2:-all}"          # be | fe | all
UPDATE_BASELINE=0
[ "${3:-}" = "--update-baseline" ] && UPDATE_BASELINE=1

if [ -z "$BRAND" ]; then
  echo "usage: code-health.sh <brand> [be|fe|all] [--update-baseline]" >&2
  exit 2
fi

PY="${WS}/.venv/bin"
BASE_DIR="${WS}/scripts/quality/baselines"
mkdir -p "$BASE_DIR"
JSCPD_VER="4.0.9"
FALLOW_VER="2.89.0"

# thresholds (HARD) — calibrados sobre el estado real 2026-06-08
JSCPD_MAX=5            # % dup BE (vitalia hoy 2.85%)
INTERROGATE_MIN=80     # % docstrings (vitalia hoy 90.9%)
FALLOW_DUP_MAX=8       # % dup FE src (e2e/.next excluidos vía .fallowrc.jsonc)

FAIL=0
note() { printf '%s\n' "$*"; }

# shrink-only count ratchet: falla si current > baseline; aprieta baseline si bajó.
ratchet_count() {
  local name="$1" file="$2" cur="$3" base
  if [ ! -f "$file" ] || [ "$UPDATE_BASELINE" = 1 ]; then
    printf '%s\n' "$cur" > "$file"
    note "  [baseline] ${name} = ${cur} (recorded)"
    return
  fi
  base="$(tr -dc '0-9' < "$file")"; [ -z "$base" ] && base=0
  if [ "$cur" -gt "$base" ]; then
    note "  ✗ ${name}: ${cur} > baseline ${base} — findings NUEVOS (arreglá o justificá + --update-baseline)"
    FAIL=1
  elif [ "$cur" -lt "$base" ]; then
    printf '%s\n' "$cur" > "$file"
    note "  ✓ ${name}: ${cur} (baseline apretado ${base}→${cur})"
  else
    note "  ✓ ${name}: ${cur} ≤ baseline ${base}"
  fi
}

run_be() {
  local b="$1"
  local src="${WS}/${b}/backend/src"
  [ -d "$src" ] || { note "── BE ${b}: (sin backend/src — skip)"; return; }
  note "── BE ${b} ──"

  # jscpd duplication (threshold HARD)
  if npx --yes "jscpd@${JSCPD_VER}" "$src" --threshold "$JSCPD_MAX" --reporters consoleFull \
        >/tmp/ch-jscpd-${b}.log 2>&1; then
    note "  ✓ jscpd dup ≤ ${JSCPD_MAX}%  ($(grep -oiE '[0-9.]+% +duplicated' /tmp/ch-jscpd-${b}.log | tail -1))"
  else
    note "  ✗ jscpd dup > ${JSCPD_MAX}%"; grep -oiE 'Found .*duplicated lines.*' /tmp/ch-jscpd-${b}.log | tail -1; FAIL=1
  fi

  # vulture dead-code (baseline ratchet)
  local vcount
  vcount="$("${PY}/vulture" "$src" --min-confidence 80 2>/dev/null | wc -l | tr -d ' ')"
  ratchet_count "vulture-deadcode" "${BASE_DIR}/${b}-be-vulture.count" "$vcount"

  # interrogate docstrings (threshold HARD)
  if "${PY}/interrogate" "$src" --fail-under "$INTERROGATE_MIN" -q >/dev/null 2>&1; then
    note "  ✓ interrogate docstrings ≥ ${INTERROGATE_MIN}%"
  else
    note "  ✗ interrogate docstrings < ${INTERROGATE_MIN}%"; FAIL=1
  fi
}

run_fe() {
  local b="$1"
  local fe="${WS}/${b}/frontend"
  [ -d "${fe}/src" ] || { note "── FE ${b}: (sin frontend/src — skip)"; return; }
  note "── FE ${b} ──"
  local bl="${BASE_DIR}/${b}-fe-deadcode.json"

  pushd "$fe" >/dev/null || return
    # dead-code: baseline ratchet (bloquea NUEVOS unused vs baseline)
    if [ ! -f "$bl" ] || [ "$UPDATE_BASELINE" = 1 ]; then
      npx --yes "fallow@${FALLOW_VER}" dead-code --save-baseline "$bl" >/dev/null 2>&1 || true
      if [ -s "$bl" ]; then note "  [baseline] fallow dead-code → $(basename "$bl") (recorded)"
      else note "  ⚠ fallow dead-code baseline NO se escribió"; FAIL=1; fi
    else
      if npx --yes "fallow@${FALLOW_VER}" dead-code --baseline "$bl" --fail-on-issues >/tmp/ch-fallow-dc-${b}.log 2>&1; then
        note "  ✓ fallow dead-code: sin findings nuevos vs baseline"
      else
        note "  ✗ fallow dead-code: findings NUEVOS vs baseline"; tail -3 /tmp/ch-fallow-dc-${b}.log; FAIL=1
      fi
    fi
    # dupes: threshold HARD sobre src (e2e/.next excluidos por .fallowrc.jsonc)
    if npx --yes "fallow@${FALLOW_VER}" dupes --threshold "$FALLOW_DUP_MAX" --ignore-imports >/tmp/ch-fallow-dup-${b}.log 2>&1; then
      note "  ✓ fallow dupes ≤ ${FALLOW_DUP_MAX}%  ($(grep -oE '\([0-9.]+%\) duplicated' /tmp/ch-fallow-dup-${b}.log | tail -1))"
    else
      note "  ✗ fallow dupes > ${FALLOW_DUP_MAX}%"; grep -oE 'duplicated across.*' /tmp/ch-fallow-dup-${b}.log | tail -1; FAIL=1
    fi
  popd >/dev/null || true
}

audit_once() {
  note "── pip-audit (env-wide, --skip-editable) ──"
  local ignore_file="${BASE_DIR}/pip-audit-ignore.txt"
  local args=(--skip-editable --progress-spinner off)
  local known=0
  if [ -f "$ignore_file" ]; then
    while IFS= read -r id; do
      id="${id%%#*}"; id="$(printf '%s' "$id" | tr -d '[:space:]')"
      [ -z "$id" ] && continue
      args+=(--ignore-vuln "$id"); known=$((known+1))
    done < "$ignore_file"
  fi
  if "${PY}/pip-audit" "${args[@]}" >/tmp/ch-pipaudit.log 2>&1; then
    note "  ✓ pip-audit: sin vulnerabilidades NUEVAS (${known} pre-existentes en allowlist — deuda, ver pip-audit-ignore.txt)"
  else
    note "  ✗ pip-audit: vulnerabilidad NUEVA (fuera del allowlist)"; grep -iE 'GHSA|PYSEC|CVE-' /tmp/ch-pipaudit.log | head; FAIL=1
  fi
}

note "═══ code-health · brand=${BRAND} · surface=${SURFACE}$([ "$UPDATE_BASELINE" = 1 ] && echo ' · UPDATE-BASELINE') ═══"
case "$SURFACE" in
  be)  run_be "$BRAND"; audit_once ;;
  fe)  run_fe "$BRAND" ;;
  all) run_be "$BRAND"; run_fe "$BRAND"; audit_once ;;
  *)   echo "surface inválida: $SURFACE (be|fe|all)" >&2; exit 2 ;;
esac

if [ "$FAIL" = 0 ]; then
  note "═══ code-health: PASS ═══"; exit 0
else
  note "═══ code-health: FAIL ═══"; exit 1
fi
