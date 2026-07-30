#!/bin/bash
# Rollback a partial publish to GitHub Packages registry.
# Usage: bash scripts/rollback_partial_publish.sh VERSION
# Requires: gh CLI authenticated with write:packages scope

set -euo pipefail

VERSION="${1:?Usage: rollback_partial_publish.sh VERSION (e.g., 0.1.0)}"

echo "Rolling back partial publish of v${VERSION}"
echo "WARNING: this deletes published packages from GH Packages registry."
echo "This action is IRREVERSIBLE. Ensure VERSION=${VERSION} is correct."
read -r -p "Proceed? [yes/no]: " CONFIRM
[ "${CONFIRM}" = "yes" ] || { echo "Aborted."; exit 0; }

# Verify gh CLI is authenticated
gh auth status || { echo "::error::Run 'gh auth login --scopes write:packages' first."; exit 1; }

echo ""
echo "=== Deleting Python packages ==="
for pkg in luana-core-platform luana-core-llm luana-core-channels \
           luana-core-idempotency luana-core-observability luana-core-events \
           luana-core-extraction luana-core-compliance luana-core-billing \
           luana-core-iam luana-core-tenant-profile luana-core-tenant-domains \
           luana-core-commercial-calendar luana-core-social-proof luana-core-assets \
           luana-core-crm luana-core-analytics-engine luana-core-landing \
           luana-core-connections luana-core-brand-studio luana-core-offer-studio \
           luana-core-copilot luana-core-sales-agent luana-core-campaigns \
           luana-core-extension-sdk; do
  VERSIONS=$(gh api "/orgs/alpacapurpura/packages/pypi/${pkg}/versions" \
    --jq ".[] | select(.name == \"${VERSION}\") | .id" 2>/dev/null || echo "")
  for vid in ${VERSIONS}; do
    if gh api -X DELETE "/orgs/alpacapurpura/packages/pypi/${pkg}/versions/${vid}" 2>/dev/null; then
      echo "  Deleted ${pkg}@${VERSION} (id=${vid})"
    else
      echo "  ::warning:: Failed to delete ${pkg}@${VERSION} — may already be deleted or not published"
    fi
  done
  if [ -z "${VERSIONS}" ]; then
    echo "  Not found: ${pkg}@${VERSION} (may not have been published)"
  fi
done

echo ""
echo "=== Deleting TypeScript packages ==="
for pkg in api-client design-tokens extension-sdk format hooks schemas ui-kit; do
  VERSIONS=$(gh api "/orgs/alpacapurpura/packages/npm/${pkg}/versions" \
    --jq ".[] | select(.name == \"${VERSION}\") | .id" 2>/dev/null || echo "")
  for vid in ${VERSIONS}; do
    if gh api -X DELETE "/orgs/alpacapurpura/packages/npm/${pkg}/versions/${vid}" 2>/dev/null; then
      echo "  Deleted @luana/${pkg}@${VERSION} (id=${vid})"
    else
      echo "  ::warning:: Failed to delete @luana/${pkg}@${VERSION}"
    fi
  done
  if [ -z "${VERSIONS}" ]; then
    echo "  Not found: @luana/${pkg}@${VERSION} (may not have been published)"
  fi
done

echo ""
echo "=== Rollback complete ==="
echo "Next steps:"
echo "  1. Delete the git tag locally: git tag -d v${VERSION}"
echo "  2. Delete the git tag remotely: git push origin --delete v${VERSION}"
echo "  3. Fix the issue that caused partial publish"
echo "  4. Re-tag and release: git tag v${VERSION} && git push origin v${VERSION}"
