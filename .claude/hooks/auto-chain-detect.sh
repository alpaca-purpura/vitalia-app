#!/usr/bin/env bash
# auto-chain-detect — UserPromptSubmit hook
#
# tier: hybrid · core = prompt-intent → additionalContext chaining mechanism ·
#       project = brand enum + secondary-skill names → seam brands[] (W5)
#
# Detecta el pattern "user invoca PM skill + pide encadenar skill secundaria"
# (ej. /pm-vitalia con args que nombran /po-ux Y expresan intención) y emite
# additionalContext que autoriza al modelo a encadenar via Skill tool inline.
#
# TRIGGER ENDURECIDO (fix 2026-06-01 — anti-falso-positivo):
#   Para disparar se necesitan LOS TRES:
#     1. /pm-{brand} como slash-command-token (límite de palabra).
#     2. skill secundaria (/(po-ux|po|ux-agentico|architect|dev-team|auditor)\b).
#     3. AL MENOS UNO de:
#        (a) verbo de intención de encadenado cercano a la skill secundaria
#            (invocá|invoca|spawneá|spawnea|arrancá|arranca|encadená|encadena|
#             corré|corre|seguí con|seguí|pasá a|continuá con|llamá|llama), O
#        (b) >=2 slash-commands secundarios distintos en el mismo prompt
#            (cuando Chris nombra dos skills → intención inequívoca).
#   Sin señal de intención, la mención suelta de una skill NO dispara.
#
# ANTI-STALE (fix 2026-06-01):
#   El additionalContext emitido indica explícitamente que la autorización
#   aplica SOLO al prompt actual. Si Chris luego dice "avanzá / ratificado /
#   sí" sin volver a nombrar una skill secundaria, el modelo NO debe asumir
#   que la cadena sigue autorizada.
#
# JQ AUSENTE (conservador):
#   Si jq no está instalado el fallback sed es lossy (pierde comillas
#   escapadas). En ese caso preferimos NO disparar ante ambigüedad: solo
#   disparamos si la señal de intención es inequívoca (verbo + secundaria).
#   Emitimos warning a stderr (no bloquea el prompt).
#
# Origen: caso F1-S4 vitalia 2026-05-23 — estancamiento por handoff textual.
# Fix false-positive: 2026-06-01 — "avanzá, ratificado" disparaba cadena.
# SSoT: .claude/rules/pm-skill-chaining.md
#
# Falla suave: exit 0 siempre (nunca bloquea el prompt del usuario).

set -uo pipefail

# Leer stdin JSON
INPUT=$(cat 2>/dev/null || true)
if [[ -z "${INPUT}" ]]; then
  exit 0
fi

HAS_JQ=false
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=true
fi

# Extraer prompt
PROMPT=""
if $HAS_JQ; then
  PROMPT=$(echo "${INPUT}" | jq -r '.prompt // empty' 2>/dev/null || true)
else
  # fallback sed — lossy ante comillas escapadas; usamos con cautela
  echo "[auto-chain-detect] WARN: jq no disponible, fallback sed (conservador)" >&2
  PROMPT=$(echo "${INPUT}" | sed -nE 's/.*"prompt"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' | head -1)
fi

if [[ -z "${PROMPT}" ]]; then
  exit 0
fi

# --- Patrones ---
PM_RE='/pm-(vitalia|nicolify|comunify|lupulo|luana|saasora|inmoflow|retailly|fixia|guestly|fitflow)\b'
SEC_RE='/(po-ux|po|ux-agentico|architect|dev-team|auditor)\b'

# Verbo de intención de encadenado (debe aparecer en el prompt).
# Usamos \b al inicio para evitar que sufijos como "seguimos" matcheen "seguí".
# NOTA: grep -E no soporta \b en todos los sistemas; usamos alternativas con
# espacio/inicio para anclar: el verbo debe estar precedido por espacio, inicio
# de línea o puntuación — no ser parte de una palabra mayor (ej. "seguimos").
INTENT_RE='(^|[[:space:][:punct:]])(invoc[aá]|spawne[aá]|arranc[aá]|encaden[aá]|corr[eé]|segu[ií] con|pas[aá] a|continu[aá] con|llam[aá])([[:space:][:punct:]]|$)'

# --- Gate 1: ambas skills presentes ---
echo "${PROMPT}" | grep -qE "${PM_RE}" || exit 0
echo "${PROMPT}" | grep -qE "${SEC_RE}" || exit 0

PM_HIT=$(echo "${PROMPT}" | grep -oE "${PM_RE}" | head -1)
SEC_HIT=$(echo "${PROMPT}" | grep -oE "${SEC_RE}" | head -1)

# --- Gate 2: señal de intención ---
# (a) verbo de encadenado presente en el prompt
HAS_INTENT=false
echo "${PROMPT}" | grep -qiE "${INTENT_RE}" && HAS_INTENT=true

# (b) >=2 slash-commands secundarios distintos → intención inequívoca
SEC_COUNT=$(echo "${PROMPT}" | grep -oE "${SEC_RE}" | sort -u | wc -l)
[[ "${SEC_COUNT}" -ge 2 ]] && HAS_INTENT=true

if ! $HAS_INTENT; then
  # Sin señal de intención → mención suelta, NO disparar.
  # (Previene el caso "avanzá, ratificado" cuando el historial mencionó skills.)
  exit 0
fi

# Con jq ausente y solo un slash-command secundario sin verbo → conservador: no disparar.
# (HAS_INTENT ya requiere verbo en ese caso, pero SEC_COUNT<2 sin jq es ambiguo.)
if ! $HAS_JQ && [[ "${SEC_COUNT}" -lt 2 ]]; then
  echo "[auto-chain-detect] WARN: jq ausente + señal ambigua, no disparando para evitar falso-positivo" >&2
  exit 0
fi

SEC_NAME="${SEC_HIT#/}"

# --- Emitir additionalContext con cláusula anti-stale explícita ---
REMINDER="[auto-chain-detect] AUTORIZACIÓN TURNO ACTUAL ÚNICAMENTE — El usuario nombró ${PM_HIT} y ${SEC_HIT} con intención explícita de encadenar EN ESTE PROMPT. Per .claude/rules/pm-skill-chaining.md § Trigger 1: después de Step 0 GREEN + contexto cargado + validación WIP caps/deps/scope, encadená via Skill tool inline con { skill: \"${SEC_NAME}\", args: \"<brand> <story-id>\" }. NO devuelvas handoff textual. IMPORTANTE ANTI-STALE: esta autorización es para EL PROMPT ACTUAL SOLAMENTE. Si en un turno posterior Chris dice 'avanzá', 'ratificado', 'sí', 'dale', etc. sin volver a nombrar una skill secundaria, esta autorización NO aplica y NO debés encadenar automáticamente — esperá instrucción explícita."

if $HAS_JQ; then
  jq -nc --arg ctx "${REMINDER}" \
    '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
else
  CTX_ESC=$(echo "${REMINDER}" | sed 's/\\/\\\\/g; s/"/\\"/g')
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"${CTX_ESC}\"}}"
fi

exit 0
