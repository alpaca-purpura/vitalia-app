#!/usr/bin/env bash
# learning-detect — UserPromptSubmit hook
#
# tier: hybrid · core = learning-capture trigger → additionalContext mechanism + doctrine ·
#       project = Spanish trigger phrases → seam locale (W5)
#
# Detecta el pattern de Chris pidiendo capturar aprendizaje + emite
# system-reminder al modelo autorizando ejecución del flow learning-capture
# (vs devolver handoff textual o ignorar).
#
# Trigger patterns reconocidos (case-insensitive):
#   - "aprendamos de esto"
#   - "esto es un aprendizaje"
#   - "capturá esto" / "capturalo"
#   - "/aprende"
#   - "anota esto para futuro"
#   - "esto hay que recordarlo"
#   - "esto no funcionó" (advisory weak — suggest pero no force)
#   - "ya nos pasó" (advisory weak)
#   - "ya nos pasó esto antes" (advisory weak)
#
# El hook recibe el prompt del usuario via stdin (JSON con campo "prompt"),
# escribe a stdout un objeto JSON con "additionalContext" cuando detecta el
# pattern. Si no detecta, exit 0 sin output (no-op).
#
# Falla suave: exit 0 siempre (nunca bloquea el prompt del usuario).
#
# Origen: conversación 2026-05-27 — Chris pidió sistema aprendizajes pointer-first.
# SSoT: .claude/rules/learning-capture.md

set -uo pipefail

# Leer stdin JSON
INPUT=$(cat 2>/dev/null || true)
if [[ -z "${INPUT}" ]]; then
  exit 0
fi

# Extraer prompt — tolerante a jq ausente
PROMPT=""
if command -v jq >/dev/null 2>&1; then
  PROMPT=$(echo "${INPUT}" | jq -r '.prompt // empty' 2>/dev/null || true)
else
  # fallback grep+sed (lossy si prompt contiene comillas escapadas)
  PROMPT=$(echo "${INPUT}" | sed -nE 's/.*"prompt"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' | head -1)
fi

if [[ -z "${PROMPT}" ]]; then
  exit 0
fi

# Patterns STRONG — Chris ratifica explícito (force capture flow)
STRONG_RE='(aprendamos de esto|esto es un aprendizaje|captur[áa](lo|r) esto|/aprende|anota esto para futuro|esto hay que recordarlo|hagamos un learning de esto|este aprendizaje)'

# Patterns WEAK — implícito, sugiere capture (Chris ratifica)
WEAK_RE='(esto no funcion[óo]|ya nos pas[óo]|esto ya pas[óo]|esto se repiti[óo]|misma cosa de la otra vez)'

STRONG_HIT=$(echo "${PROMPT}" | grep -oEi "${STRONG_RE}" | head -1 || true)
WEAK_HIT=$(echo "${PROMPT}" | grep -oEi "${WEAK_RE}" | head -1 || true)

if [[ -n "${STRONG_HIT}" ]]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "learning-capture flow authorized — Chris pidió explícitamente capturar aprendizaje (trigger: \"${STRONG_HIT}\"). Per .claude/rules/learning-capture.md § Trigger 1: (1) determiná tipo (técnico transversal | negocio per-brand | process | tooling), (2) determiná brand si business-specific (inferí del worktree actual + confirmá), (3) proponé slug kebab-case ≤60 chars, (4) escribí archivo en path canónico siguiendo template, (5) agregá pointer 1 línea a MEMORY.md, (6) confirmá ratificación. SI el aprendizaje no está claro aún (Chris dijo \"aprendamos\" sin contenido específico) → preguntá QUÉ es el aprendizaje antes de capturar. NO uses scripts/learning/capture.sh sin contenido ratificado."
  }
}
EOF
  exit 0
fi

if [[ -n "${WEAK_HIT}" ]]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "learning-capture suggestion (weak signal) — Chris citó \"${WEAK_HIT}\" que sugiere problema recurrente. Per .claude/rules/learning-capture.md § Trigger 2: considerá sugerir capturar como anti-pattern learning. NO captures sin ratificación explícita Chris — sólo proponé al cierre del turno: \"¿querés que capturemos esto como aprendizaje en {path canónico}?\". Si Chris dice sí → flow Trigger 1. Si Chris dice no → continuá sin captura."
  }
}
EOF
  exit 0
fi

# No-op si nada match
exit 0
