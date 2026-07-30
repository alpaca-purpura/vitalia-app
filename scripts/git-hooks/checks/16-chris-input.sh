# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 16 — chris-input.md consistency (R4 brand-docs-schema, cement 2026-05-27)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: .claude/rules/sistema-docs-schema.md § R4
#
# Si el commit toca {brand}/docs/product/stories/{id}/checkpoint.md y el state
# está en {idea, refining, refined, ready, developing, developed, reviewing},
# debe existir chris-input.md en el mismo directorio. chris-input.md nace con
# la idea (R4 v3 cement 2026-05-28) — es el buzón de inputs de Chris desde el
# día cero.
#
# Override:
#   * frontmatter del checkpoint.md: `# chris-input-skip: razón` (advisory log)
#   * env: CHRIS_INPUT_SKIP=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────

if [ "${CHRIS_INPUT_SKIP:-0}" != "1" ]; then
  STAGED_CHECKPOINTS=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/docs/product/stories/[^/]+/checkpoint\.md$' \
    || true)

  if [ -n "$STAGED_CHECKPOINTS" ]; then
    while IFS= read -r cp_file; do
      [[ -z "$cp_file" ]] && continue
      [[ ! -f "$cp_file" ]] && continue

      # Honor magic comment escape in checkpoint frontmatter
      if grep -qE '^\s*#\s*chris-input-skip([: \t]|$)' "$cp_file"; then
        continue
      fi

      # Extract state field via grep (frontmatter line: `state: <value>`).
      # Tolerates trailing inline comments (# ...).
      STATE_RAW=$(grep -E '^state:[[:space:]]+' "$cp_file" | head -1 \
        | sed -E 's/^state:[[:space:]]+//' \
        | sed -E 's/[[:space:]]*#.*$//' \
        | tr -d '"' | tr -d "'" | xargs)

      case "$STATE_RAW" in
        idea|refining|refined|ready|developing|developed|reviewing)
          STORY_DIR=$(dirname "$cp_file")
          CHRIS_INPUT="$STORY_DIR/chris-input.md"
          if [ ! -f "$CHRIS_INPUT" ]; then
            printf "\033[31m"
            cat <<EOF

─────────────────────────────────────────────────────────────
CHRIS-INPUT.MD MISSING (R4 brand-docs-schema, cement 2026-05-27)

File:  $cp_file
State: $STATE_RAW
Story dir: $STORY_DIR

Story en state '$STATE_RAW' requiere chris-input.md presente.

Crear con:
  cp docs/specs/templates/00-chris-input-template.md $CHRIS_INPUT

Si el template no existe aún, crear un chris-input.md mínimo:
  - file: $CHRIS_INPUT
  - contiene: ratificaciones Chris + decisiones humanas + scope confirmations

Override (advisory, audit escruta):
  * En checkpoint frontmatter agregar: # chris-input-skip: razón
  * Emergency env: CHRIS_INPUT_SKIP=1 git commit ...

SSoT: .claude/rules/sistema-docs-schema.md § R4
─────────────────────────────────────────────────────────────
EOF
            printf "\033[0m"
            exit 1
          fi
          ;;
        *)
          # states {done, parked, dropped} — no chris-input.md required
          # (idea ahora SÍ lo requiere — nace con la idea, R4 v3 cement 2026-05-28)
          ;;
      esac
    done <<< "$STAGED_CHECKPOINTS"
  fi
fi

