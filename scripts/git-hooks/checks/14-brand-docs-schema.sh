# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 14 — Brand docs schema R1 enforcement (cement 2026-05-19)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: .claude/rules/sistema-docs-schema.md § R1
#
# Bloquea staging de archivos .md sueltos en {brand}/docs/ raíz.
# {brand}/docs/ solo permite sub-dirs canónicos: product/, archive/,
# learnings/, architecture/, domains/.
#
# Contenido ad-hoc debe ir a sub-dir apropiado:
#   ADR              → {brand}/docs/architecture/ADR-{brand}-{NNN}-{slug}.md
#   Process doc      → {brand}/docs/domains/{component}.md
#   Learning         → {brand}/docs/learnings/{date}-{slug}.md
#   Release (fase)   → {brand}/docs/product/releases/{FN}.yaml
#
# Override: BRAND_DOCS_SCHEMA_SKIP=1 (emergencias documentadas, auditor escruta)
# ─────────────────────────────────────────────────────────────────────────────

if [ "${BRAND_DOCS_SCHEMA_SKIP:-0}" != "1" ]; then
  STAGED_R1=$(git diff --cached --name-only 2>/dev/null)
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    # Detectar {brand}/docs/X.md (un solo nivel después de docs/)
    if [[ "$f" =~ ^(vitalia)/docs/[^/]+\.md$ ]]; then
      BRAND_R1="${BASH_REMATCH[1]}"
      FILE_NAME=$(basename "$f")
      printf "\033[31m"
      cat <<EOF

─────────────────────────────────────────────────────────────
BRAND DOCS SCHEMA VIOLATION (R1): MD suelto en {brand}/docs/ raíz

File:    $f
Brand:   $BRAND_R1
Schema:  .claude/rules/sistema-docs-schema.md § R1

${BRAND_R1}/docs/ raíz NO permite archivos .md sueltos. Solo sub-dirs:
  - ${BRAND_R1}/docs/product/   (stories, capabilities, modules, releases)
  - ${BRAND_R1}/docs/archive/   (stories done immutable snapshot)
  - ${BRAND_R1}/docs/learnings/ (insights brand-local)
  - ${BRAND_R1}/docs/architecture/ (ADRs locales brand)
  - ${BRAND_R1}/docs/domains/   (tools/workflows registrados via Extension SDK)

Reubicar '${FILE_NAME}' al sub-dir apropiado según contenido:
  - ¿ADR/decisión arquitectónica? → ${BRAND_R1}/docs/architecture/ADR-${BRAND_R1}-NNN-{slug}.md
  - ¿Procedimiento operacional?    → ${BRAND_R1}/docs/domains/{component}.md
  - ¿Learning/insight histórico?   → ${BRAND_R1}/docs/learnings/{date}-{slug}.md
  - ¿Spec de feature?              → ${BRAND_R1}/docs/product/stories/{story-id}/01-spec.md
  - ¿Release/fase?                 → ${BRAND_R1}/docs/product/releases/{FN}.yaml
  - ¿Handoff cross-session?        → dentro de la story relevante

Override (emergencias documentadas): BRAND_DOCS_SCHEMA_SKIP=1 git commit ...
SSoT: .claude/rules/sistema-docs-schema.md
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  done <<< "$STAGED_R1"
fi

