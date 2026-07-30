#!/usr/bin/env bash
set -euo pipefail
# new-session.sh — Crea worktree + branch + manifest + symlink venv per modelo cementado 2026-05-18
# SSoT del modelo: docs/process/parallel-sessions-protocol.md (D1-D14) + ADR-005
#
# Usage:
#   scripts/git/new-session.sh BRAND TYPE [SLUG] [LANE]
#
# Args:
#   BRAND    brand activa: vitalia | nicolify | comunify | lupulo
#            o pseudo-brand: core (D12 — lifts engine) | protocol (cross-cutting harness/modelo)
#   TYPE     worktree type per BRAND:
#              brand activa:
#                canonical  → ~/Proyectos/luana-{brand}/                       branch wip/{brand}-{slug}
#                story      → ~/Proyectos/luana-{brand}-{slug}/                branch wip/{brand}-{slug}[-{lane}]
#                hotfix     → ~/Proyectos/luana-{brand}-hotfix-{slug}/         branch hotfix/{brand}-{slug}
#                exp        → ~/Proyectos/luana-{brand}-exp-{slug}/            branch exp/{brand}-{slug}
#              core:
#                lift       → ~/Proyectos/luana-core-{slug}/                   branch wip/core-{slug}
#              protocol:    (cross-cutting: .claude/**, docs/{process,architecture,specs}/**, scripts/**, Makefile)
#                work       → ~/Proyectos/luana-protocol-{slug}/               branch wip/protocol-{slug}
#   SLUG     identificador story-id/slug-corto. Solo [a-z0-9-], lowercase, max 40 chars
#            Con TYPE=story, SLUG === story-id (story-closure-gate convention 2026-05-18).
#   LANE     opcional, solo con TYPE=story: be|fe|tests|docs (libre, recomendado)
#
# Exit codes:
#   0  Worktree creado exitosamente
#   1  Error args / brand|type desconocido / slug invalido / branch existe / dir existe
#   2  Error git operation (fetch/worktree add)
#
# Produces:
#   - Branch nacida de origin/main fresco (NO de HEAD actual)
#   - Worktree fisico
#   - Symlink ${worktree}/.venv → ~/Proyectos/luana-platform/.venv/
#   - Manifest ${worktree}/.session.yaml con identidad estatica
#   - Copia best-effort de .env.dev.template por brand (no aplica para BRAND=core)
#
# Examples:
#   scripts/git/new-session.sh vitalia canonical bootstrap
#   scripts/git/new-session.sh vitalia story vitalia-copilot-tools-impl
#   scripts/git/new-session.sh vitalia story vitalia-copilot-tools-impl fe
#   scripts/git/new-session.sh comunify hotfix kb-broken
#   scripts/git/new-session.sh core lift extract-callback-handler

BRAND="${1:?Usage: new-session.sh BRAND TYPE [SLUG] [LANE] — see header}"
TYPE="${2:?Usage: new-session.sh BRAND TYPE [SLUG] [LANE]}"
SLUG="${3:-}"
LANE="${4:-}"

# Validate BRAND (mantener lista en sync con docs/portfolio/PORTFOLIO.md)
# 'core' es pseudo-brand reservado para lifts engine (D12).
# 'protocol' es pseudo-brand para cambios cross-cutting al modelo/harness (scope-gate wip/protocol-*).
case "${BRAND}" in
  vitalia|nicolify|comunify|lupulo|core|protocol) ;;
  *)
    echo "::error::Unknown brand '${BRAND}'. Allowed: vitalia, nicolify, comunify, lupulo, core, protocol"
    exit 1
    ;;
esac

# Validate TYPE per BRAND
case "${BRAND}" in
  core)
    case "${TYPE}" in
      lift) ;;
      *)
        echo "::error::With BRAND=core only TYPE=lift allowed (got TYPE=${TYPE})"
        exit 1
        ;;
    esac
    ;;
  protocol)
    case "${TYPE}" in
      work) ;;
      *)
        echo "::error::With BRAND=protocol only TYPE=work allowed (got TYPE=${TYPE})"
        exit 1
        ;;
    esac
    ;;
  *)
    case "${TYPE}" in
      canonical|story|hotfix|exp) ;;
      *)
        echo "::error::Unknown type '${TYPE}' for brand '${BRAND}'. Allowed: canonical, story, hotfix, exp"
        exit 1
        ;;
    esac
    ;;
esac

# SLUG required for all types
if [[ -z "${SLUG}" ]]; then
  echo "::error::SLUG required for type '${TYPE}'"
  exit 1
fi

# Validate SLUG: only [a-z0-9-], lowercase, max 40 chars
if [[ ! "${SLUG}" =~ ^[a-z0-9-]+$ ]]; then
  echo "::error::Invalid slug '${SLUG}' — only [a-z0-9-] allowed (lowercase, no underscores)"
  exit 1
fi
if [[ ${#SLUG} -gt 40 ]]; then
  echo "::error::Slug too long (${#SLUG} chars, max 40)"
  exit 1
fi

# story-closure-gate convention (post 2026-05-18): cuando TYPE=story, SLUG debe ser
# story-id existente en {BRAND}/docs/product/stories/ con state ∈ {idea, refining, refined, ready}
# (no developing/developed/reviewing — esos ya tienen worktree).
if [[ "${TYPE}" = "story" ]] && [[ "${BRAND}" != "core" ]]; then
  STORY_CHECKPOINT="${BRAND}/docs/product/stories/${SLUG}/checkpoint.md"
  if [[ -f "${STORY_CHECKPOINT}" ]]; then
    STORY_STATE=$(grep -E "^state:" "${STORY_CHECKPOINT}" | head -1 | awk '{print $2}' || echo "")
    if [[ "${STORY_STATE}" =~ ^(developing|developed|reviewing|done)$ ]]; then
      echo "::error::Story ${SLUG} state=${STORY_STATE} — ya tiene worktree o esta cerrada."
      echo "  Si querés retomar: cd al worktree existente."
      echo "  Si state=done: la story esta cerrada, crear nueva."
      echo "  SSoT: .claude/rules/story-closure-gate.md (Layer 4)"
      exit 2
    fi
  fi
  # Si no existe checkpoint, OK — story se creará. /pm-{brand} bootstrap escribirá checkpoint.
fi

# LANE only valid with story type
if [[ -n "${LANE}" ]]; then
  if [[ "${TYPE}" != "story" ]]; then
    echo "::error::LANE only valid with TYPE=story (got TYPE=${TYPE})"
    exit 1
  fi
  if [[ ! "${LANE}" =~ ^[a-z0-9-]+$ ]]; then
    echo "::error::Invalid lane '${LANE}' — only [a-z0-9-] allowed"
    exit 1
  fi
fi

# Workspace root detection
WS_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${WS_ROOT}" ]] || [[ ! -d "${WS_ROOT}/.git" ]]; then
  echo "::error::Not in a git repo. Run from inside ~/Proyectos/luana-platform/"
  exit 1
fi
# Resolve PRINCIPAL = root path of the main worktree (where .git is a directory, not file)
PRINCIPAL="$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')"
if [[ ! -d "${PRINCIPAL}/.git" ]]; then
  echo "::error::Could not detect principal worktree (expected .git as directory)"
  exit 1
fi
WORKTREE_PARENT="$(dirname "${PRINCIPAL}")"

# Override for tests
if [[ -n "${WORKTREE_PARENT_OVERRIDE:-}" ]]; then
  WORKTREE_PARENT="${WORKTREE_PARENT_OVERRIDE}"
fi

# Compute branch name + worktree dir per BRAND + TYPE
if [[ "${BRAND}" = "core" ]]; then
  # D12 — lift core
  BRANCH="wip/core-${SLUG}"
  WORKTREE_DIR="${WORKTREE_PARENT}/luana-core-${SLUG}"
  WORKTREE_TYPE="ephemeral"
elif [[ "${BRAND}" = "protocol" ]]; then
  # cross-cutting harness/modelo — scope-gate enforces wip/protocol-* solo toca modelo
  BRANCH="wip/protocol-${SLUG}"
  WORKTREE_DIR="${WORKTREE_PARENT}/luana-protocol-${SLUG}"
  WORKTREE_TYPE="ephemeral"
else
  case "${TYPE}" in
    canonical)
      # v2 cementado 2026-05-18: canónico = wip/{brand} ESTABLE (NO rota story-by-story).
      # SLUG es ignorado para canónico. Si already exists → refuse + advise.
      BRANCH="wip/${BRAND}"
      WORKTREE_DIR="${WORKTREE_PARENT}/luana-${BRAND}"
      WORKTREE_TYPE="canonical"
      if [[ -n "${SLUG}" ]] && [[ "${SLUG}" != "${BRAND}" ]]; then
        echo "⚠ TYPE=canonical: SLUG '${SLUG}' ignored (v2 modelo: canónico siempre wip/${BRAND})"
      fi
      SLUG="${BRAND}"
      ;;
    story)
      # v2 cementado 2026-05-18: worktree story SOLO por pedido EXPLÍCITO del user.
      # Skills (PM/dev-team/auditor) NO crean story worktrees automático.
      # Para confirmar intención humana: requiere --explicit-user-request flag.
      if [[ "${EXPLICIT_USER_REQUEST:-0}" != "1" ]]; then
        echo "::error::TYPE=story requiere EXPLICIT_USER_REQUEST=1 (v2 modelo, evita auto-creates)"
        echo "  Pedido del user esperado: 'creá worktree story para X' antes de invocar."
        echo "  Usage: EXPLICIT_USER_REQUEST=1 scripts/git/new-session.sh ${BRAND} story ${SLUG}"
        exit 1
      fi
      if [[ -n "${LANE}" ]]; then
        BRANCH="wip/${BRAND}-${SLUG}-${LANE}"
        WORKTREE_DIR="${WORKTREE_PARENT}/luana-${BRAND}-${SLUG}-${LANE}"
      else
        BRANCH="wip/${BRAND}-${SLUG}"
        WORKTREE_DIR="${WORKTREE_PARENT}/luana-${BRAND}-${SLUG}"
      fi
      WORKTREE_TYPE="ephemeral"
      ;;
    hotfix)
      BRANCH="hotfix/${BRAND}-${SLUG}"
      WORKTREE_DIR="${WORKTREE_PARENT}/luana-${BRAND}-hotfix-${SLUG}"
      WORKTREE_TYPE="ephemeral"
      ;;
    exp)
      BRANCH="exp/${BRAND}-${SLUG}"
      WORKTREE_DIR="${WORKTREE_PARENT}/luana-${BRAND}-exp-${SLUG}"
      WORKTREE_TYPE="ephemeral"
      ;;
  esac
fi

# Pre-flight checks
if git rev-parse --verify "${BRANCH}" &>/dev/null; then
  echo "::error::Branch ${BRANCH} already exists locally. Pick a different slug or cleanup first"
  exit 1
fi
if [[ -e "${WORKTREE_DIR}" ]]; then
  echo "::error::Directory ${WORKTREE_DIR} already exists. Remove it first or pick a different slug"
  exit 1
fi

# Fetch origin/main fresh (the branch is born from origin/main, NOT from current HEAD)
echo "→ Fetching origin/main fresh..."
if ! git -C "${PRINCIPAL}" fetch origin main 2>&1; then
  echo "::error::git fetch origin main failed"
  exit 2
fi
ORIGIN_MAIN_SHA="$(git -C "${PRINCIPAL}" rev-parse origin/main)"

# Create worktree at origin/main HEAD with new branch
echo "→ Creating worktree ${WORKTREE_DIR} on branch ${BRANCH} from origin/main (${ORIGIN_MAIN_SHA:0:7})..."
if ! git -C "${PRINCIPAL}" worktree add -b "${BRANCH}" "${WORKTREE_DIR}" "${ORIGIN_MAIN_SHA}" 2>&1; then
  echo "::error::git worktree add failed"
  exit 2
fi

# Create symlink to shared .venv (if principal has one)
if [[ -d "${PRINCIPAL}/.venv" ]]; then
  echo "→ Creating symlink ${WORKTREE_DIR}/.venv → ${PRINCIPAL}/.venv"
  ln -sfn "${PRINCIPAL}/.venv" "${WORKTREE_DIR}/.venv"
else
  echo "⚠ ${PRINCIPAL}/.venv does not exist — run 'uv sync' in principal first then re-symlink manually"
fi

# Generate .session.yaml manifest
MANIFEST="${WORKTREE_DIR}/.session.yaml"
echo "→ Writing manifest ${MANIFEST}"
cat > "${MANIFEST}" <<EOF
# Manifest auto-generado por new-session.sh ($(date -u +%Y-%m-%dT%H:%M:%SZ))
# SSoT: docs/process/parallel-sessions-protocol.md § D8 + D13
# Este archivo NO se versiona (debe estar gitignored).
brand: ${BRAND}
worktree_type: ${WORKTREE_TYPE}
story_id: ${SLUG}
lane: ${LANE:-}
tickets: []
created_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
created_by_skill: chris-manual
parent_branch: origin/main
parent_sha: ${ORIGIN_MAIN_SHA}
branch: ${BRANCH}
notes: ""
# last_sync auto-actualizado por T1/T2 hooks (D10):
last_sync:
  fetched_at: ${origin_main_sha:+null}
  origin_main_sha: ${ORIGIN_MAIN_SHA}
  result: nothing
  commits_pulled: 0
  core_touched: false
EOF

# Add .session.yaml to local exclude (per-worktree gitignore, not committed)
# Note: .git/info/exclude is shared across worktrees, so we add it once if not present.
EXCLUDE_FILE="${PRINCIPAL}/.git/info/exclude"
if ! grep -qxF "/.session.yaml" "${EXCLUDE_FILE}" 2>/dev/null; then
  echo "/.session.yaml" >> "${EXCLUDE_FILE}"
  echo "→ Added /.session.yaml to ${EXCLUDE_FILE}"
fi

# Copy .env.dev.template per brand (best-effort) — solo brands reales (no 'core'/'protocol')
if [[ "${BRAND}" != "core" ]] && [[ "${BRAND}" != "protocol" ]]; then
  template="${WORKTREE_DIR}/${BRAND}/.env.dev.template"
  if [[ -f "${template}" ]]; then
    dest="${WORKTREE_DIR}/${BRAND}/.env.dev"
    if [[ ! -e "${dest}" ]]; then
      cp "${template}" "${dest}"
      echo "→ Copied ${BRAND}/.env.dev.template → ${BRAND}/.env.dev"
    fi
  fi
fi

# Final report
echo ""
echo "✓ Worktree ready"
echo "  Path:      ${WORKTREE_DIR}"
echo "  Branch:    ${BRANCH}"
echo "  Type:      ${WORKTREE_TYPE}"
echo "  Born from: origin/main @ ${ORIGIN_MAIN_SHA:0:7}"
echo "  Manifest:  .session.yaml created"
echo "  Venv:      symlinked from principal (if available)"
echo ""
echo "Next steps:"
echo "  1. cd ${WORKTREE_DIR}"
echo "  2. Open Warp tab (Cmd+T) and cd to the new path"
echo "  3. Run 'claude' (or 'opencode') in that tab"
echo "  4. Push at least every 30 min: git push origin ${BRANCH} (safety net M11)"
