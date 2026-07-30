# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 13 — Scope per branch enforcement (v2 cementado 2026-05-18)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: docs/process/worktree-protocol-v2-plan.md § CORE #4
#
# Bloquea staging de files que violan scope de la branch actual.
# Patterns:
#   wip/{brand}            → solo {brand}/** + raíz brand-agnostic
#   wip/{brand}-{story-id} → mismo que wip/{brand}
#   wip/protocol-*         → solo docs/process/, docs/architecture/, .claude/, scripts/
#   wip/core-*             → solo core/luana-core-*/
#   main                   → bloqueado por Section 11
#
# Override: SCOPE_GATE_SKIP=1 (emergencias documentadas, auditor escruta)

if [ "${SCOPE_GATE_SKIP:-0}" != "1" ]; then
  CURRENT_BRANCH_SCOPE=$(git branch --show-current 2>/dev/null || echo "")
  STAGED_SCOPE=$(git diff --cached --name-only 2>/dev/null)

  # Helper para reportar violación + exit
  scope_violation() {
    local file="$1"
    local reason="$2"
    local hint="$3"
    printf "\033[31m"
    cat <<EOF

─────────────────────────────────────────────────────────────
SCOPE GATE BLOCKED: $reason

File staged: $file
Branch:      $CURRENT_BRANCH_SCOPE

$hint

Override (emergencias): SCOPE_GATE_SKIP=1 git commit ...
SSoT: docs/process/worktree-protocol-v2-plan.md § CORE #4
─────────────────────────────────────────────────────────────
EOF
    printf "\033[0m"
    exit 1
  }

  # wip/{brand} or wip/{brand}-{story-id} pattern
  if [[ "$CURRENT_BRANCH_SCOPE" =~ ^wip/(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)(-.*)?$ ]]; then
    SCOPE_BRAND="${BASH_REMATCH[1]}"
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      # OK: brand propia
      [[ "$f" =~ ^${SCOPE_BRAND}/ ]] && continue
      # OK: raíz brand-agnostic
      [[ "$f" =~ ^(CLAUDE\.md|AGENTS\.md|README\.md|Makefile|pnpm-lock\.yaml|uv\.lock|pyproject\.toml|pnpm-workspace\.yaml|\.gitignore|\.env\.example)$ ]] && continue
      # OK: scripts brand-agnostic (no scripts/git/ que es transversal-modelo)
      [[ "$f" =~ ^scripts/ ]] && [[ ! "$f" =~ ^scripts/git/ ]] && [[ ! "$f" =~ ^scripts/git-hooks/ ]] && continue
      # OK: gitignored o untracked dirs (vendor/coverage/etc)
      [[ "$f" =~ /coverage/|/node_modules/|/\.venv/|/__pycache__/ ]] && continue

      # BLOCK: cross-brand
      if [[ "$f" =~ ^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/ ]]; then
        OTHER_BRAND="${BASH_REMATCH[1]}"
        scope_violation "$f" \
          "Cross-brand staging blocked (branch=$CURRENT_BRANCH_SCOPE expects only ${SCOPE_BRAND}/)" \
          "El archivo es de brand '${OTHER_BRAND}'. Cada brand mergea desde su propio wip/{brand}.
Acciones:
  1. Si es trabajo de ${OTHER_BRAND}: cambiar a worktree luana-${OTHER_BRAND}/
  2. Si confundiste branch: git restore --staged $f"
      fi
      # BLOCK: transversal modelo
      if [[ "$f" =~ ^(\.claude/(rules|skills)/|docs/(process|architecture)/|scripts/git/|scripts/git-hooks/) ]]; then
        scope_violation "$f" \
          "Transversal modelo staging blocked (branch=$CURRENT_BRANCH_SCOPE no toca modelo/protocolo)" \
          "El archivo es transversal al modelo (rules/skills/process/architecture/scripts git).
Acciones:
  1. Crear worktree dedicado: scripts/git/new-session.sh protocol work <slug>
  2. O abandonar el cambio si no era intencional: git restore --staged $f"
      fi
      # BLOCK: core engine
      if [[ "$f" =~ ^core/luana-core- ]]; then
        scope_violation "$f" \
          "Core engine staging blocked (branch=$CURRENT_BRANCH_SCOPE no toca core)" \
          "El archivo es del engine luana-core-*. Requiere promotion proposal.
Acciones:
  1. Crear worktree core: EXPLICIT_USER_REQUEST=1 scripts/git/new-session.sh core lift <slug>
  2. Crear promotion proposal en docs/promotion-protocol/proposals/"
      fi
    done <<< "$STAGED_SCOPE"
  fi

  # wip/protocol-* pattern → solo modelo
  if [[ "$CURRENT_BRANCH_SCOPE" =~ ^wip/protocol- ]]; then
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      # OK: paths de modelo/proceso/skills/scripts-git
      [[ "$f" =~ ^(\.claude/|docs/(process|architecture|specs)/|scripts/) ]] && continue
      [[ "$f" =~ ^(CLAUDE\.md|AGENTS\.md|README\.md|Makefile)$ ]] && continue

      # BLOCK: brand
      if [[ "$f" =~ ^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/ ]]; then
        scope_violation "$f" \
          "Brand staging blocked en wip/protocol-* (branch=$CURRENT_BRANCH_SCOPE solo toca modelo)" \
          "Acciones:
  1. Si es trabajo del modelo: el archivo no debería ser de brand. Reconsiderá.
  2. Si es trabajo de brand: cambiar a worktree de esa brand."
      fi
      # BLOCK: core engine
      if [[ "$f" =~ ^core/luana-core- ]]; then
        scope_violation "$f" \
          "Core engine staging blocked en wip/protocol-* (branch=$CURRENT_BRANCH_SCOPE solo toca modelo)" \
          "Crear worktree core dedicado o promotion proposal."
      fi
    done <<< "$STAGED_SCOPE"
  fi

  # wip/core-* pattern → solo core
  if [[ "$CURRENT_BRANCH_SCOPE" =~ ^wip/core- ]]; then
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      # OK: core engine
      [[ "$f" =~ ^core/luana-core- ]] && continue
      # OK: docs promotion + ADRs
      [[ "$f" =~ ^docs/(promotion-protocol|architecture|core-modules)/ ]] && continue
      # OK: raíz lockfiles si bump deps
      [[ "$f" =~ ^(uv\.lock|pnpm-lock\.yaml|pyproject\.toml|pnpm-workspace\.yaml)$ ]] && continue

      # BLOCK: brand
      if [[ "$f" =~ ^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/ ]]; then
        scope_violation "$f" \
          "Brand staging blocked en wip/core-* (branch=$CURRENT_BRANCH_SCOPE solo toca engine)" \
          "Lift core es independiente de brand. Si necesitás brand consumer changes,
hacer en wip/{brand} separado después del lift."
      fi
    done <<< "$STAGED_SCOPE"
  fi
fi

