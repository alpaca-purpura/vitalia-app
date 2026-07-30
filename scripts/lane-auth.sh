#!/usr/bin/env bash
# lane-auth.sh — seed a Chrome DevTools MCP lane profile with a real Clerk session (HB-89).
#
# ROOT CAUSE: the Chrome DevTools MCP launches Chrome against a persistent per-lane profile
#   ~/.cache/chrome-devtools-mcp/luana-${brand}-${LUANA_LANE:-solo}
# That profile is never signed into Clerk → authenticated writes (POST/PATCH) the lane's MCP
# attempts redirect to /sign-in. The Playwright e2e harness produces an authed Clerk session
# (vitalia/frontend/e2e/setup/clerk.setup.ts → playwright/.clerk/user.json storageState) but
# that's a DIFFERENT cookie jar. This script bridges the gap: it drives a headless Playwright
# persistent context against the MCP's profile dir, runs the SAME @clerk/testing ticket signIn,
# and closes — the persistent context flushes cookies to disk natively. The MCP then opens that
# profile already signed in.
#
# RAM NOTE (host-infra, out of scope for this script): when running a live-verify, prefer a
# single-brand FE to avoid OOM — `make dev-active BRAND=<brand>` stops the other brands' FE.
#
# Usage:  bash scripts/lane-auth.sh <vitalia|nicolify|comunify> [--force]
#   LUANA_LANE selects the lane profile (default "solo"). Re-seeds if the profile marker is
#   >4h old; --force re-seeds unconditionally.
set -euo pipefail

# ── arg parse ────────────────────────────────────────────────────────────────
BRAND="${1:-}"
FORCE=0
shift || true
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) echo "lane-auth: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

case "$BRAND" in
  vitalia|nicolify|comunify) ;;
  "")
    echo "Uso: bash scripts/lane-auth.sh <vitalia|nicolify|comunify> [--force]" >&2
    exit 2 ;;
  *)
    echo "lane-auth: brand inválida '$BRAND' (esperado: vitalia|nicolify|comunify)" >&2
    exit 2 ;;
esac

WS="$(git rev-parse --show-toplevel)"
LANE="${LUANA_LANE:-solo}"
PROFILE="$HOME/.cache/chrome-devtools-mcp/luana-${BRAND}-${LANE}"
FE_DIR="${WS}/${BRAND}/frontend"
ENV_FILE="${WS}/${BRAND}/.env.dev"
MARKER="${PROFILE}/.lane-auth.ok"
FRESH_WINDOW_S=$((4 * 60 * 60))

echo "[lane-auth] brand=${BRAND} lane=${LANE}"
echo "[lane-auth] profile=${PROFILE}"

# ── freshness gate (4h mtime on the marker) ──────────────────────────────────
if [ "$FORCE" -eq 0 ] && [ -f "$MARKER" ]; then
  now="$(date +%s)"
  mtime="$(stat -c %Y "$MARKER" 2>/dev/null || echo 0)"
  age=$((now - mtime))
  if [ "$age" -lt "$FRESH_WINDOW_S" ]; then
    echo "[lane-auth] profile seeded ${age}s ago (<4h) — skipping. Use --force to re-seed."
    exit 0
  fi
fi

# ── env load ─────────────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "lane-auth: missing ${ENV_FILE} (gitignored per-worktree)." >&2
  echo "           Copy ${BRAND}/.env.dev.template → ${BRAND}/.env.dev and fill the E2E_CLERK_* + CLERK_SECRET_KEY vars." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

# Default E2E_BASE_URL per brand if not provided by .env.dev.
if [ -z "${E2E_BASE_URL:-}" ]; then
  case "$BRAND" in
    vitalia)  E2E_BASE_URL="http://localhost:3002" ;;
    nicolify) E2E_BASE_URL="http://localhost:3001" ;;
    comunify) E2E_BASE_URL="http://localhost:3003" ;;
  esac
  export E2E_BASE_URL
fi

# Validate the vars the .mjs requires.
missing=0
for v in E2E_CLERK_USER_EMAIL CLERK_SECRET_KEY NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY; do
  if [ -z "${!v:-}" ]; then
    echo "lane-auth: ${v} not set in ${ENV_FILE}" >&2
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1

# ── lock guard: the MCP must not hold the profile while we seed ──────────────
# Chrome writes SingletonLock (and friends) inside the profile when running. If the lane's
# MCP Chrome is open against this profile, launchPersistentContext would race / corrupt it.
for lock in "${PROFILE}/SingletonLock" "${PROFILE}/SingletonCookie" "${PROFILE}/SingletonSocket"; do
  if [ -e "$lock" ]; then
    echo "lane-auth: profile lock present (${lock##*/}) — a Chrome is using this profile." >&2
    echo "           Close the lane's MCP Chrome first, or unset LUANA_LANE, then re-run." >&2
    exit 1
  fi
done

# ── playwright binary resolution ─────────────────────────────────────────────
if [ ! -d "${FE_DIR}/node_modules/@playwright/test" ] || [ ! -d "${FE_DIR}/node_modules/@clerk/testing" ]; then
  echo "lane-auth: ${BRAND}/frontend deps not installed (@playwright/test + @clerk/testing)." >&2
  echo "           Run 'pnpm install' first (the live-verify stack needs FE deps anyway)." >&2
  exit 1
fi

# ── seed ─────────────────────────────────────────────────────────────────────
# Run node with cwd = ${brand}/frontend so @playwright/test + @clerk/testing resolve from
# the brand FE node_modules. Point at the absolute .mjs path under scripts/.
echo "[lane-auth] seeding Clerk session into the lane profile (headless)…"
( cd "$FE_DIR" && \
  LANE_PROFILE_DIR="$PROFILE" \
  E2E_BASE_URL="$E2E_BASE_URL" \
    node "${WS}/scripts/lane-auth.mjs" )

echo "[lane-auth] done. Lane profile ${BRAND}-${LANE} now carries a Clerk session."
