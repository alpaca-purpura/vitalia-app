# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 17 — checkpoint.md frontmatter: NO duplicate top-level keys (cement 2026-05-28)
# ─────────────────────────────────────────────────────────────────────────────
# Causa raíz del bug "la story no aparece en el board": una key top-level repetida
# en el frontmatter (ej. `phase:` dos veces) rompe el parse YAML → el cockpit no
# puede leer el checkpoint (cae a state=idea o lo descarta).
#
# Disciplina (SSoT docs/process/checkpoint-protocol.md § Frontmatter edit discipline):
# al editar checkpoint.md se ACTUALIZA la key existente en la cabecera, NUNCA se
# appendea una nueva. Este gate bloquea el commit si detecta keys duplicadas.
# Override emergencia: CHECKPOINT_DUPKEY_SKIP=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────
if [ "${CHECKPOINT_DUPKEY_SKIP:-0}" != "1" ]; then
  DUP_CKPTS=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null \
    | grep -E '/checkpoint\.md$' || true)
  if [ -n "$DUP_CKPTS" ]; then
    DUPKEY_FOUND=0
    while IFS= read -r cp_file; do
      [[ -z "$cp_file" || ! -f "$cp_file" ]] && continue
      DUPS=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm==1 && /^[A-Za-z_][A-Za-z0-9_]*:/ {
          k=$0; sub(/:.*/, "", k)
          if (seen[k]++) print k
        }
        fm>=2 { exit }
      ' "$cp_file" | sort -u)
      if [ -n "$DUPS" ]; then
        DUPKEY_FOUND=1
        printf "\033[31m"
        cat <<EOF

─────────────────────────────────────────────────────────────
CHECKPOINT FRONTMATTER · KEY DUPLICADA (cement 2026-05-28)

File: $cp_file
Keys duplicadas: $(echo "$DUPS" | tr '\n' ' ')

Una key top-level repetida rompe el parse YAML → el cockpit no puede
leer el checkpoint (cae a state=idea o lo descarta del board).

FIX: actualiza la key EXISTENTE en la cabecera, no agregues una nueva.
     (caso típico: 'outcome:'/'phase:' legacy viejos + el nuevo encima)

Override emergencia: CHECKPOINT_DUPKEY_SKIP=1 git commit ...
SSoT: docs/process/checkpoint-protocol.md § Frontmatter edit discipline
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
      fi
    done <<< "$DUP_CKPTS"
    # NO usar `[ ... ] && exit 1` como último statement: bajo `source` + set -e
    # del dispatcher, el `[` fallando (caso sin dups) devuelve rc=1 → aborta
    # el commit SIN mensaje (bug cazado 2026-06-09 en el squash-merge a main).
    if [ "$DUPKEY_FOUND" = "1" ]; then
      exit 1
    fi
  fi
fi

