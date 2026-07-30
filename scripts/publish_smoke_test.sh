#!/bin/bash
# Smoke test against published luana-platform packages in GitHub Packages registry.
# Usage: bash scripts/publish_smoke_test.sh [VERSION]
# Requires: uv, node, npm, GH_PACKAGES_TOKEN or GITHUB_TOKEN env var

set -euo pipefail

VERSION="${1:-0.1.0}"
SMOKE_DIR=$(mktemp -d -t luana-smoke-XXXXXX)

cleanup() { rm -rf "${SMOKE_DIR}"; }
trap cleanup EXIT

echo "=== Smoke test against published v${VERSION} in ${SMOKE_DIR} ==="

# --- Python smoke ---
cd "${SMOKE_DIR}"
cat > pyproject.toml <<EOF_PY
[project]
name = "smoke-test"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
    "luana-core-platform==${VERSION}",
    "luana-core-extension-sdk==${VERSION}",
]

[[tool.uv.index]]
name = "github"
url = "https://pypi.pkg.github.com/alpacapurpura/simple/"
default = false
EOF_PY

# Configure auth
TOKEN="${UV_PUBLISH_TOKEN:-${GH_PACKAGES_TOKEN:-${GITHUB_TOKEN:-}}}"
if [ -z "${TOKEN}" ]; then
  echo "::error::No auth token found. Set GH_PACKAGES_TOKEN or GITHUB_TOKEN."
  echo "::error::See docs/process/release-procedure-v0.1.0.md §Token-setup for setup instructions."
  exit 1
fi
echo "machine pypi.pkg.github.com login alpacapurpura password ${TOKEN}" > "${HOME}/.netrc.smoke"
chmod 600 "${HOME}/.netrc.smoke"

echo ""
echo "--- Python smoke: installing luana-core-platform + luana-core-extension-sdk ---"
NETRC="${HOME}/.netrc.smoke" uv sync 2>&1 | tail -5

echo "--- Python smoke: verifying imports ---"
NETRC="${HOME}/.netrc.smoke" uv run python -c "
from luana_core_platform import __version__
assert __version__ == '${VERSION}', f'got {__version__}'
print(f'luana-core-platform=={VERSION} installed OK')
"

NETRC="${HOME}/.netrc.smoke" uv run python -c "
from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext
r = ExtensionPointRegistry()
methods = ['offer_preset_pack_register', 'brand_voice_seed_register', 'sales_agent_tool_register']
assert all(hasattr(r, m) for m in methods), [m for m in methods if not hasattr(r, m)]
print(f'luana-core-extension-sdk=={VERSION} installed OK — 3 critical EPs callable')
"

rm -f "${HOME}/.netrc.smoke"

# --- TypeScript smoke ---
echo ""
echo "--- TypeScript smoke: installing @luana/extension-sdk ---"
mkdir -p "${SMOKE_DIR}/ts-smoke"
cd "${SMOKE_DIR}/ts-smoke"

cat > .npmrc <<EOF_NPM
@luana:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN:-${TOKEN}}
EOF_NPM
chmod 600 .npmrc

cat > package.json <<EOF_PKG
{"name": "smoke-test-ts", "version": "0.0.0", "dependencies": {"@luana/extension-sdk": "${VERSION}"}}
EOF_PKG

npm install --no-save 2>&1 | tail -5

node -e "
const sdk = require('@luana/extension-sdk');
if (Object.keys(sdk).length === 0) {
  console.error('::error::SDK empty — @luana/extension-sdk exports nothing');
  process.exit(1);
}
console.log('@luana/extension-sdk@${VERSION} installed OK — exports: ' + Object.keys(sdk).join(', '));
"

echo ""
echo "=== SMOKE TEST GREEN — v${VERSION} consumable from published registry ==="
