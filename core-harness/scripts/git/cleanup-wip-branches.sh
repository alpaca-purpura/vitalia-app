#!/usr/bin/env bash
# cleanup-wip-branches.sh — List and optionally delete stale wip/* branches
#
# Called by .github/workflows/cleanup-wip.yml (cron weekly + workflow_dispatch).
# Also usable locally for dry-run preview.
#
# Environment variables:
#   DRY_RUN         — 'true' (default) or 'false'. When true: list only, no delete.
#   MAX_AGE_DAYS    — Age threshold in days (default: 30). Branches with no commits
#                     in the last MAX_AGE_DAYS days are cleanup candidates.
#   GH_TOKEN        — GitHub token with branch delete scope (set by workflow).
#   GITHUB_REPOSITORY — owner/repo (set by workflow, e.g. org/{workspace.repo_prefix}-platform).
#
# Output:
#   Summary with N candidates, M preserved, K deleted.
#   Exit 0 always (cleanup failure is non-fatal — cron will retry next week).
#
# Safety invariants:
#   1. NEVER touches main or release/* branches — explicit guard on every delete.
#   2. Default dry_run=true — first run is always safe.
#   3. Only processes refs/remotes/origin/wip/** pattern.

set -euo pipefail

DRY_RUN="${DRY_RUN:-true}"
MAX_AGE_DAYS="${MAX_AGE_DAYS:-30}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"

NOW=$(date +%s)
MAX_AGE_SECONDS=$((MAX_AGE_DAYS * 86400))

CANDIDATES=()
PRESERVED=()
DELETED=()
ERRORS=()

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WIP Branch Cleanup — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Mode: $([ "${DRY_RUN}" = 'true' ] && echo 'DRY RUN (no deletions)' || echo 'DELETE MODE')"
echo "Threshold: branches with last commit older than ${MAX_AGE_DAYS} days"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Fetch latest remote refs (needed to see all remote wip/* branches)
git fetch --prune origin 2>/dev/null || echo "Warning: git fetch failed — working with cached refs"

# List all remote wip/* branches with their last committer date (Unix timestamp)
# Format: <unix_timestamp> <branch_short_name>
while IFS=' ' read -r LAST_COMMIT_UNIX BRANCH_SHORT; do
  [ -z "${BRANCH_SHORT}" ] && continue

  # Strip 'origin/' prefix to get the actual branch name
  BRANCH="${BRANCH_SHORT#origin/}"

  # Safety guard: NEVER touch main or release/* — belt AND suspenders.
  # The for-each-ref pattern already filters to wip/**, but we double-check.
  case "${BRANCH}" in
    main | release/*)
      echo "SKIP (protected): ${BRANCH}"
      continue
      ;;
    wip/*)
      # Expected — proceed with age check
      ;;
    *)
      # Unexpected branch in wip/** pattern — skip safely
      echo "SKIP (unexpected): ${BRANCH}"
      continue
      ;;
  esac

  AGE_SECONDS=$((NOW - LAST_COMMIT_UNIX))
  AGE_DAYS=$((AGE_SECONDS / 86400))

  if [ "${AGE_SECONDS}" -gt "${MAX_AGE_SECONDS}" ]; then
    CANDIDATES+=("${BRANCH} (last commit: ${AGE_DAYS} days ago)")
    echo "CANDIDATE: ${BRANCH} — last commit ${AGE_DAYS} days ago (threshold: ${MAX_AGE_DAYS}d)"

    if [ "${DRY_RUN}" = "false" ]; then
      # Delete via gh api (works with GITHUB_TOKEN)
      if [ -n "${GITHUB_REPOSITORY}" ] && [ -n "${GH_TOKEN:-}" ]; then
        if gh api "repos/${GITHUB_REPOSITORY}/git/refs/heads/${BRANCH}" \
            -X DELETE 2>/dev/null; then
          DELETED+=("${BRANCH}")
          echo "  → DELETED: ${BRANCH}"
        else
          ERRORS+=("${BRANCH}")
          echo "  → ERROR deleting: ${BRANCH}"
        fi
      else
        echo "  → SKIP delete: GITHUB_REPOSITORY or GH_TOKEN not set"
      fi
    fi
  else
    PRESERVED+=("${BRANCH} (last commit: ${AGE_DAYS} days ago)")
    echo "PRESERVE: ${BRANCH} — last commit ${AGE_DAYS} days ago (recent)"
  fi

done < <(
  git for-each-ref \
    'refs/remotes/origin/wip/**' \
    --format='%(committerdate:unix) %(refname:short)' \
    --sort=committerdate \
    2>/dev/null || true
)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "  Candidates (>=${MAX_AGE_DAYS}d without commits): ${#CANDIDATES[@]}"
echo "  Preserved  (<${MAX_AGE_DAYS}d, active):          ${#PRESERVED[@]}"
echo "  Deleted:                                  ${#DELETED[@]}"
if [ "${#ERRORS[@]}" -gt 0 ]; then
  echo "  Errors:                                   ${#ERRORS[@]}"
fi
if [ "${DRY_RUN}" = "true" ] && [ "${#CANDIDATES[@]}" -gt 0 ]; then
  echo ""
  echo "  To delete candidates, run with dry_run=false via workflow_dispatch."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Always exit 0 — cleanup is non-fatal (cron retries weekly)
exit 0
