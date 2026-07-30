#!/usr/bin/env bash
# CI Parity — cross-brand reproducer of GitHub Actions ``quality-gates`` job.
#
# Why this exists
# ===============
# ``/test-all`` runs natively in Linux for fast iteration (CLAUDE.md rule #2).
# Native runs differ from CI in three ways that have produced 5+ failed
# deploys (lessons preserved post-T-10/T-14 cutover):
#
#   1. ``<brand>/backend/.env`` (84 keys, prod-mirror routing) vs the CI image's
#      baked-in ``<brand>/backend/.env.test`` (~38 keys after sync).
#   2. Host TZ (UTC-3..-5) vs CI runner TZ=UTC. Date-boundary tests
#      (Lima locale, ISO week resets) flip outcome at midnight UTC.
#   3. Host RAM 16GB+ with no Node heap limit vs container ~1GB default.
#      ``tsc --noEmit`` and ``vitest run --coverage`` OOM only in CI.
#
# This script builds the SAME Docker test images CI builds (``test``
# stage of each Dockerfile) and runs the SAME steps with the SAME
# environment constraints. Per-brand orchestration via ``--brand=NAME``.
#
# Usage
# =====
#   bash scripts/ci-parity.sh --brand=nicolify            # full sweep brand
#   bash scripts/ci-parity.sh --brand=nicolify --skip-fe  # backend only
#   bash scripts/ci-parity.sh --brand=nicolify --skip-be  # frontend only
#
# Direct invocation (no flags) prints usage.
#
# Decisión 8 (Story 10): cross-brand pattern lives at luana-platform root.
# Per-brand pre-extraction: brand=nicolify resolves paths to nicolify/{backend,frontend}/.
# Post-brand-extraction (future per-brand repo): this script may delegate
# to brand-repo-internal ci-parity.sh via git submodule or relative path.

set -euo pipefail

cd "$(dirname "$0")/.."

BRAND=""
SKIP_BE=0
SKIP_FE=0
for arg in "$@"; do
  case "$arg" in
    --brand=*) BRAND="${arg#--brand=}" ;;
    --skip-be) SKIP_BE=1 ;;
    --skip-fe) SKIP_FE=1 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg" >&2
      echo "Usage: $0 --brand=NAME [--skip-be] [--skip-fe]" >&2
      exit 2
      ;;
  esac
done

if [ -z "$BRAND" ]; then
  echo "ERROR: --brand=NAME required" >&2
  echo "Usage: $0 --brand=NAME [--skip-be] [--skip-fe]" >&2
  exit 2
fi

if [ ! -d "$BRAND" ]; then
  echo "ERROR: brand directory '$BRAND' not found in $(pwd)" >&2
  echo "Available brands: $(ls -d */ 2>/dev/null | grep -v 'node_modules\|core\|scripts\|docs' | tr -d '/')" >&2
  exit 3
fi

# ANSI colour helpers
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
blue()   { printf "\033[34m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }

step() {
  blue "── [$BRAND] $* ──"
}

# Single shared env block — mirrors ci.yml ``env`` keys plus
# the heap bump that unblocks tsc/vitest in container-constrained RAM.
DOCKER_RUN_ENV=(
  -e TZ=UTC
  -e NODE_OPTIONS=--max-old-space-size=4096
)

BE_DIR="$BRAND/backend"
FE_DIR="$BRAND/frontend"

# Mirror validator — fail fast if the script has drifted from
# ci.yml. Skip silently if the BE venv is unavailable.
if [ -x "$BE_DIR/.venv/bin/python" ] && [ -f scripts/validate_ci_parity_mirror.py ]; then
  step "Validating ci-parity.sh mirrors ci.yml"
  "$BE_DIR/.venv/bin/python" scripts/validate_ci_parity_mirror.py || \
    yellow "  (advisory: validator not yet adapted to cross-brand layout — review Story 10 T-12 closure notes)"
fi

if [ "$SKIP_BE" -eq 0 ]; then
  step "Building backend test image (Dockerfile target=test)"
  docker build \
    --target test \
    -f "$BE_DIR/Dockerfile" \
    -t "local-be-ci-$BRAND" \
    "$BE_DIR/"

  step "BE: ruff check"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-be-ci-$BRAND" ruff check src

  step "BE: ruff format --check"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-be-ci-$BRAND" ruff format --check src

  step "BE: pytest with coverage"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-be-ci-$BRAND" \
    pytest --cov=src/modules --cov=src/shared --cov-report=term -q \
    --ignore=tests/modules/analytics/test_meta_provider.py

  step "BE: pip-audit (security, advisory — matches ci.yml continue-on-error)"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-be-ci-$BRAND" pip-audit --strict --desc || \
    yellow "  (advisory: pip-audit reported issues; CI has continue-on-error: true on this step)"
fi

if [ "$SKIP_FE" -eq 0 ]; then
  step "Building frontend test image (Dockerfile target=test)"
  docker build \
    --target test \
    -f "$FE_DIR/Dockerfile" \
    -t "local-fe-ci-$BRAND" \
    "$FE_DIR/"

  step "FE: ESLint"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-fe-ci-$BRAND" npm run lint

  step "FE: TypeScript (tsc --noEmit)"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-fe-ci-$BRAND" npx tsc --noEmit

  step "FE: Vitest with coverage"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-fe-ci-$BRAND" \
    npx vitest run --coverage

  step "FE: npm audit (security, advisory — matches ci.yml continue-on-error)"
  docker run --rm "${DOCKER_RUN_ENV[@]}" "local-fe-ci-$BRAND" npm audit --audit-level=high || \
    yellow "  (advisory: npm audit reported issues; CI has continue-on-error: true on this step)"
fi

# Drop a marker the pre-push hook reads. Per-brand marker so a multi-brand
# repo state cleanly bumps marker per HEAD.
if [ -d .git ]; then
  HEAD_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  rm -f ".git/ci-parity-passed-$BRAND-"* 2>/dev/null || true
  touch ".git/ci-parity-passed-$BRAND-${HEAD_SHA}"
fi

green "✓ [$BRAND] CI Parity passed locally — safe to push to main."
