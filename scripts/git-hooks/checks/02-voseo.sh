# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 2. Voseo regex check on added lines only
# ─────────────────────────────────────────────────────────────────

# Glosario sourced from .claude/rules/spanish-text.md
VOSEO_REGEX='\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|dejalo|poné|ponelo|usá|usalo|hacé|hacelo|elegí|elegilo|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|subí|bajá|abrí|volvé|andá|cambiá|cambialo|ofrecés|cobrás|ejecutás|acompañás|activás|desactivás|linkeá|despublicala|reactivá|cancelala|validá|considerá|formulala|marcá|referís|atendés|integrás|listá|probá|mostrá|compartí|contá|explicá|fijate|acordate)\b'

VOSEO_HITS=""

if [ -n "${ALL_TEXT_STAGED}" ]; then
  while IFS= read -r FILE; do
    [ -z "${FILE}" ] && continue

    # Voseo neutro aplica SOLO a interfaces de usuario (web UI / agentic output).
    # NUNCA al harness interno (.claude/), docs, tooling (tools/, scripts/), ni
    # tests. (Chris 2026-06-01: el voseo solo molesta cuando se mete en lo interno.)
    case "${FILE}" in
      .claude/*|docs/*|scripts/*|tools/*|\
      */tests/*|*/__tests__/*|*/e2e/*|*.test.*|*test_*.py)
        continue
        ;;
    esac

    # Per spanish-text.md exception: sales_agent voice output respects tenant
    # voice (puede ser voseo si AR). Skip personality compiler / specialist
    # prompt templates that LLM consumes as voice instructions.
    # Also skip goldens/ directory: golden transcripts may contain voseo when
    # dialect_code=es-AR (Story D D10 + sales_agent voice exception). Path-based
    # exclusion avoids per-file magic comment proliferation (05-guidelines.md).
    case "${FILE}" in
      */modules/sales_agent/*personality*|\
      */modules/sales_agent/*specialist*|\
      */modules/sales_agent/*.j2|\
      */modules/sales_agent/*system_instruction*|\
      */modules/sales_agent/agent_identity*|\
      */tests/modules/sales_agent/*goldens*|\
      */agentic_evals/sales_agent/goldens/*)
        continue
        ;;
    esac

    # Per spanish-text.md exception: skill SKILL.md / rules/*.md / process docs
    # may quote voseo glosario or example wrong-then-right pairs. Honor magic
    # comment in any of these forms (R25 flexible regex 2026-05-05 + TS fix 2026-05-26):
    #   # voseo-allowed                     (Python/shell comment, no reason)
    #   # voseo-allowed: optional reason    (Python/shell comment, with reason)
    #   # voseo-allowed — optional reason   (any unicode separator + reason)
    #   // voseo-allowed                    (TypeScript/JS comment, no reason)
    #   // voseo-allowed: optional reason   (TypeScript/JS comment, with reason)
    #   <!-- voseo-allowed -->              (Markdown/HTML/JSX, no reason)
    #   <!-- voseo-allowed: optional -->    (Markdown/HTML/JSX, with reason inside)
    #   <!-- voseo-allowed — reason -->     (any unicode separator + reason)
    #
    # Regex strategy: avoid unicode chars in character classes (locale issues
    # with multi-byte chars in POSIX ERE). Use `[^>]*` for MD and end-of-line
    # tolerance for Py/TS. Both anchored at literal `voseo-allowed`.
    # Supports: # voseo-allowed (Python/shell), // voseo-allowed (TypeScript/JS),
    #           <!-- voseo-allowed --> (HTML/Markdown/JSX)
    if grep -qE '((#|//)\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)' "${FILE}" 2>/dev/null; then
      continue
    fi

    # Examine ONLY added lines in this commit (-U0 zero context)
    HITS=$(git diff --cached -U0 -- "${FILE}" 2>/dev/null \
      | grep -E '^\+' \
      | grep -vE '^\+\+\+' \
      | grep -niE "${VOSEO_REGEX}" \
      || true)

    if [ -n "${HITS}" ]; then
      VOSEO_HITS+="${FILE}:"$'\n'"${HITS}"$'\n\n'
    fi
  done <<< "${ALL_TEXT_STAGED}"
fi

if [ -n "${VOSEO_HITS}" ]; then
  printf "\033[31m"
  cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: voseo detected in staged changes.

EOF
  printf "%s" "${VOSEO_HITS}"
  cat <<EOF
─────────────────────────────────────────────────────────────
Per .claude/rules/spanish-text.md: tuteo (tú) only on user-facing
strings. Convert + re-stage.

Glosario voseo→neutro: see .claude/rules/spanish-text.md table.

Common conversions:
  vos     → tú          sos     → eres        tenés   → tienes
  podés   → puedes      mirá    → mira        dejá    → deja
  poné    → pon         hacé    → haz         elegí   → elige
  agregá  → agrega      configurá → configura  revisá  → revisa

Exception: modules/sales_agent/ voice templates (already excluded).
If false positive, mark file:
  # voseo-allowed: <reason>           (Python/shell comment)
  // voseo-allowed: <reason>          (TypeScript/JS comment)
  <!-- voseo-allowed: <reason> -->    (Markdown/HTML)

NEVER use --no-verify (.claude/rules/git-safety.md prohibits).
─────────────────────────────────────────────────────────────
EOF
  printf "\033[0m"
  exit 1
fi

