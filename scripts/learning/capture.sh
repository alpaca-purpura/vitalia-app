#!/usr/bin/env bash
# scripts/learning/capture.sh — CLI helper for learning capture
#
# Captura un aprendizaje en path canónico + agrega pointer a MEMORY.md.
# Invocable directamente por Chris o por el modelo (autorizado via
# .claude/rules/learning-capture.md § Trigger 1).
#
# Usage:
#   ./scripts/learning/capture.sh \
#     --type {technical|business|process|tooling} \
#     --brand {vitalia|none} \
#     --slug "clerk-storage-state-freshness-gate" \
#     --title "Clerk storage state freshness gate" \
#     --hook "E2E auth Clerk requiere check freshness pre-test, retry+sanity, no cachear >5min" \
#     --tags "clerk,auth,freshness,storage-state,e2e" \
#     --content-file /tmp/learning-body.md
#
# Si --content-file no se provee → script abre $EDITOR para que Chris escriba.
#
# El path canónico se calcula según --type + --brand:
#   - technical → docs/learnings/{YYYY-MM-DD}-{slug}.md
#   - business + brand → {brand}/docs/learnings/{YYYY-MM-DD}-{slug}.md
#   - process → append a docs/process/learnings.md (no file separado)
#   - tooling → docs/learnings/tooling/{slug}.md (sin fecha en filename)
#
# Origen: conversación 2026-05-27 — sistema aprendizajes pointer-first.
# SSoT: .claude/rules/learning-capture.md

set -euo pipefail

# Defaults
TYPE=""
BRAND=""
SLUG=""
TITLE=""
HOOK=""
TAGS=""
CONTENT_FILE=""
WS=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

if [[ -z "${WS}" ]]; then
  echo "ERROR: no se detectó git workspace root" >&2
  exit 1
fi

# Memory path (per Claude Code convention)
MEMORY_FILE="${HOME}/.claude/projects/-home-chalreme-Proyectos-luana-platform/memory/MEMORY.md"

usage() {
  cat <<EOF
Usage: $0 --type {technical|business|process|tooling} --slug "kebab-slug" --title "Title" --hook "≤120 chars" [opts]

Required:
  --type TYPE          technical | business | process | tooling
  --slug SLUG          kebab-case ≤60 chars (sin date prefix — se agrega auto)
  --title TITLE        Title case, ej "Clerk storage state freshness gate"
  --hook HOOK          1 línea ≤120 chars que explica por qué importa al futuro Claude

Optional:
  --brand BRAND        vitalia (mandatory si type=business)
  --tags TAGS          comma-separated, 3-7 grep-friendly tags
  --content-file PATH  archivo .md con cuerpo. Si omitido → abre \$EDITOR.
  --dry-run            no escribe nada, sólo muestra el path target + pointer
  --help               muestra este mensaje

Examples:
  $0 --type technical --slug "clerk-storage-state-freshness-gate" \\
     --title "Clerk storage state freshness gate" \\
     --hook "E2E auth Clerk requiere check freshness pre-test, retry+sanity" \\
     --tags "clerk,auth,freshness,storage-state,e2e"

  $0 --type business --brand vitalia --slug "hipaa-lite-latam-marco" \\
     --title "Vitalia HIPAA-lite LatAm 6 países" \\
     --hook "Habeas Data CO + LFPDPPP MX + Ley 25.326 AR + LGPD BR + Ley 29733 PE + Ley 19.628 CL" \\
     --tags "vitalia,hipaa,compliance,latam,regulacion"
EOF
}

DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) TYPE="$2"; shift 2 ;;
    --brand) BRAND="$2"; shift 2 ;;
    --slug) SLUG="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --hook) HOOK="$2"; shift 2 ;;
    --tags) TAGS="$2"; shift 2 ;;
    --content-file) CONTENT_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: arg desconocido: $1" >&2; usage; exit 1 ;;
  esac
done

# Validate required
for VAR_NAME in TYPE SLUG TITLE HOOK; do
  if [[ -z "${!VAR_NAME}" ]]; then
    echo "ERROR: --$(echo $VAR_NAME | tr 'A-Z' 'a-z') es obligatorio" >&2
    usage
    exit 1
  fi
done

# Validate type
case "${TYPE}" in
  technical|business|process|tooling) ;;
  *) echo "ERROR: --type debe ser technical|business|process|tooling (recibido: ${TYPE})" >&2; exit 1 ;;
esac

# Validate slug format (kebab-case, ≤60 chars, alphanumeric+hyphen)
if ! echo "${SLUG}" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'; then
  echo "ERROR: --slug debe ser kebab-case (a-z 0-9 -), recibido: ${SLUG}" >&2
  exit 1
fi
if [[ ${#SLUG} -gt 60 ]]; then
  echo "ERROR: --slug ≤60 chars, recibido: ${#SLUG}" >&2
  exit 1
fi

# Validate hook length
if [[ ${#HOOK} -gt 120 ]]; then
  echo "ERROR: --hook ≤120 chars, recibido: ${#HOOK}" >&2
  exit 1
fi

# Validate brand if type=business
if [[ "${TYPE}" == "business" && -z "${BRAND}" ]]; then
  echo "ERROR: --brand obligatorio cuando --type=business" >&2
  exit 1
fi

if [[ -n "${BRAND}" && "${TYPE}" != "business" ]]; then
  echo "WARNING: --brand ignorado cuando --type=${TYPE}" >&2
  BRAND=""
fi

# Validate brand value
if [[ -n "${BRAND}" ]]; then
  case "${BRAND}" in
    vitalia) ;;
    *) echo "ERROR: --brand inválido: ${BRAND} (single-brand: vitalia)" >&2; exit 1 ;;
  esac
fi

# Calculate target path
DATE=$(date +%Y-%m-%d)
case "${TYPE}" in
  technical)
    TARGET="${WS}/docs/learnings/${DATE}-${SLUG}.md"
    ;;
  business)
    TARGET="${WS}/${BRAND}/docs/learnings/${DATE}-${SLUG}.md"
    ;;
  process)
    TARGET="${WS}/docs/process/learnings.md"
    APPEND_MODE="true"
    ;;
  tooling)
    TARGET="${WS}/docs/learnings/tooling/${SLUG}.md"
    ;;
esac

# Calculate relative path for MEMORY pointer
TARGET_REL=${TARGET#${WS}/}

# Dry run output
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "=== Dry run ==="
  echo "Target path: ${TARGET}"
  echo "MEMORY pointer: - [${TITLE}](${TARGET_REL}) — ${HOOK}"
  echo "Tags: ${TAGS}"
  exit 0
fi

# Get content
if [[ -n "${CONTENT_FILE}" ]]; then
  if [[ ! -f "${CONTENT_FILE}" ]]; then
    echo "ERROR: --content-file no existe: ${CONTENT_FILE}" >&2
    exit 1
  fi
  CONTENT=$(cat "${CONTENT_FILE}")
else
  # Open editor
  TMP_FILE=$(mktemp --suffix=.md)
  cat > "${TMP_FILE}" <<EOF
## Contexto

¿Qué situación generó el aprendizaje? (2-4 líneas, factual)

## Aprendizaje

La regla / pattern / anti-pattern verbatim.

## Aplicación práctica

- **Cuándo aplica:** triggers concretos
- **Cómo aplica:** acción específica
- **Cuándo NO aplica:** excepciones (si las hay)

## Ejemplo (opcional)

Snippet código / config / comando que ilustra.

## Referencias

- Links a spec/ADR/rule/memory relevantes
EOF
  ${EDITOR:-nano} "${TMP_FILE}"
  CONTENT=$(cat "${TMP_FILE}")
  rm -f "${TMP_FILE}"
fi

# Calculate brands_affected for frontmatter
BRANDS_AFFECTED="[]"
if [[ "${TYPE}" == "technical" || "${TYPE}" == "tooling" ]]; then
  BRANDS_AFFECTED="[vitalia]"
elif [[ "${TYPE}" == "business" ]]; then
  BRANDS_AFFECTED="[${BRAND}]"
fi

# Compose frontmatter
TAGS_YAML="[]"
if [[ -n "${TAGS}" ]]; then
  TAGS_YAML="[${TAGS}]"
fi

FRONTMATTER=$(cat <<EOF
---
title: "${TITLE}"
date: ${DATE}
type: ${TYPE}
brands_affected: ${BRANDS_AFFECTED}
${BRAND:+brand: ${BRAND}}
ratified_by: chris
tags: ${TAGS_YAML}
---

# ${TITLE}

EOF
)

# Write learning file
if [[ "${APPEND_MODE:-false}" == "true" ]]; then
  # Process learning — append a docs/process/learnings.md
  mkdir -p "$(dirname "${TARGET}")"
  if [[ ! -f "${TARGET}" ]]; then
    echo "# Process Learnings" > "${TARGET}"
    echo "" >> "${TARGET}"
  fi
  cat >> "${TARGET}" <<EOF

---

## ${DATE} — ${TITLE}

**Tags:** ${TAGS}

${CONTENT}
EOF
else
  # New file
  mkdir -p "$(dirname "${TARGET}")"
  if [[ -f "${TARGET}" ]]; then
    echo "ERROR: target ya existe: ${TARGET}" >&2
    exit 1
  fi
  {
    echo "${FRONTMATTER}"
    echo "${CONTENT}"
  } > "${TARGET}"
fi

echo "✓ Aprendizaje escrito: ${TARGET}"

# Append pointer to MEMORY.md
if [[ ! -f "${MEMORY_FILE}" ]]; then
  echo "WARNING: MEMORY.md no existe en ${MEMORY_FILE}. Creando..." >&2
  mkdir -p "$(dirname "${MEMORY_FILE}")"
  echo "# MEMORY index" > "${MEMORY_FILE}"
fi

POINTER="- [${TITLE}](${TARGET_REL}) — ${HOOK}"

# Determinar sección donde insertar (heuristic)
case "${TYPE}" in
  technical|tooling) SECTION_MARKER="## Cross-portfolio" ;;
  business) SECTION_MARKER="## " ;;  # buscar brand section o cross-portfolio
  process) SECTION_MARKER="## Process" ;;
esac

# Append simple al final si no se encuentra sección
if grep -qE "^${SECTION_MARKER}" "${MEMORY_FILE}"; then
  # Insertar después del marker
  TMP_MEM=$(mktemp)
  awk -v marker="${SECTION_MARKER}" -v pointer="${POINTER}" '
    {print}
    $0 ~ "^"marker && !done {
      print ""
      print pointer
      done=1
    }
  ' "${MEMORY_FILE}" > "${TMP_MEM}"
  mv "${TMP_MEM}" "${MEMORY_FILE}"
else
  echo "" >> "${MEMORY_FILE}"
  echo "${POINTER}" >> "${MEMORY_FILE}"
fi

echo "✓ MEMORY.md pointer agregado"
echo ""
echo "=== Próximos pasos ==="
echo "1. Revisa el contenido escrito: cat ${TARGET}"
echo "2. Si querés promover a rule (futura aplicación enforce-able): /pm-vitalia propone path .claude/rules/{slug}.md"
echo "3. Commit en mismo PR del trabajo que originó el learning"
