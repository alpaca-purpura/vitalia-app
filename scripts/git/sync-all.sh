#!/usr/bin/env bash
set -uo pipefail   # NO -e: seguir aunque un worktree haga STOP
# sync-all.sh — "poné al día a las demás": corre sync-from-main en CADA worktree wip/*.
# FF-safe: sync-from-main hace FF/merge-only + STOP-on-dirty → nunca pierde WIP.
# Doctrina: docs/process/harness-backlog.md HB-86.
#
# Usage:
#   scripts/git/sync-all.sh            # integra main en cada wip/*
#   scripts/git/sync-all.sh --check    # solo reporta cuánto está atrás cada uno

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC="${SCRIPT_DIR}/sync-from-main.sh"
CHECK=0; [[ "${1:-}" == "--check" ]] && CHECK=1
SYNC_ARGS=(--quiet); [[ ${CHECK} -eq 1 ]] && SYNC_ARGS=(--check --quiet)

printf '%-26s %-16s %s\n' "WORKTREE" "BRANCH" "RESULT"
git worktree list --porcelain | awk '/^worktree /{p=$2} /^branch /{print p" "$2}' | while read -r path ref; do
  br="${ref#refs/heads/}"
  case "${br}" in wip/*) ;; *) continue ;; esac
  out="$(cd "${path}" && bash "${SYNC}" "${SYNC_ARGS[@]}" 2>&1)"; rc=$?
  if [[ ${CHECK} -eq 1 ]]; then
    res="$(echo "${out}" | grep -iE 'behind|ahead|up-to-date' | head -1)"
    [[ -z "${res}" ]] && res="✓ up-to-date"
  else
    case ${rc} in
      0) res="✓ synced / up-to-date" ;;
      1) res="⚠ STOP — resolvé en ${path} (corré sync-from-main ahí)" ;;
      *) res="✗ error rc=${rc}" ;;
    esac
  fi
  printf '%-26s %-16s %s\n' "$(basename "${path}")" "${br}" "${res}"
done
