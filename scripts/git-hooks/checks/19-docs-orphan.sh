# shellcheck shell=bash
# Check 19 — docs-orphan ADVISORY (DOCS-SWEEP gate anti-recontaminación · 2026-06-10).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, set -euo pipefail).
# DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
#
# Un .md NUEVO (staged A) bajo root docs/ que (a) cae FUERA de los homes
# declarados y (b) no tiene inbound-ref en superficies vivas → ADVISORY ruidoso
# (NUNCA bloquea — no frenar a Chris escribiendo; el barrido periódico
# `make docs-graph` lo caza). SSoT: scripts/scan_docs_graph.py + INVENTORY del
# sweep en legacy/2026-06-10-docs-sweep/.
#
# Regla durable (learning 2026-06-09-sourced-check-andlist-errexit): NUNCA
# `[ cond ] && acción` como último statement de un path alcanzable — usar if.
if [ "${DOCS_ORPHAN_SKIP:-0}" != "1" ]; then
  DOCS_ORPHAN_HOMES='^docs/(learnings|process|architecture|specs|portfolio|promotion-protocol|core-modules|rules-detail)/'
  NEW_ROOT_DOCS=$(git diff --cached --name-only --diff-filter=A 2>/dev/null \
    | grep -E '^docs/.*\.md$' || true)
  if [ -n "$NEW_ROOT_DOCS" ]; then
    while IFS= read -r nd; do
      if [ -z "$nd" ]; then
        continue
      fi
      if echo "$nd" | grep -qE "$DOCS_ORPHAN_HOMES"; then
        continue  # home declarado → OK silencioso
      fi
      ND_BASE=$(basename "$nd")
      ND_HITS=$(grep -rl --exclude-dir=__pycache__ --exclude-dir=node_modules \
        -e "$nd" -e "$ND_BASE" \
        "${REPO_ROOT}/.claude" "${REPO_ROOT}/scripts" \
        "${REPO_ROOT}/tools/luana-cockpit-go" "${REPO_ROOT}/Makefile" \
        "${REPO_ROOT}/CLAUDE.md" "${REPO_ROOT}/AGENTS.md" 2>/dev/null | head -1 || true)
      if [ -z "$ND_HITS" ]; then
        printf "\033[33m"
        cat <<EOF
─────────────────────────────────────────────────────────────
⚠ DOCS-ORPHAN ADVISORY (no bloquea · DOCS-SWEEP 2026-06-10)

  $nd

.md nuevo bajo root docs/ FUERA de los homes declarados (learnings/process/
architecture/specs/portfolio/promotion-protocol/core-modules/rules-detail)
y SIN inbound-ref en superficies vivas → nacería huérfano.

Opciones: (a) moverlo a un home declarado · (b) citarlo desde su consumidor
(skill/rule/script/doc vivo) · (c) seguir igual — el barrido periódico
\`make docs-graph\` lo va a reportar. Silenciar: DOCS_ORPHAN_SKIP=1
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
      fi
    done <<< "$NEW_ROOT_DOCS"
  fi
fi
