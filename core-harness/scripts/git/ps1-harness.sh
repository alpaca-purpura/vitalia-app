#!/usr/bin/env bash
# ps1-harness.sh — PS1 customizado para worktrees del proyecto (mec. I)
# SSoT: docs/process/parallel-sessions-protocol.md § D7
#
# Source this file in ~/.bashrc (ajustá la ruta a tu workspace):
#   if [[ -f ~/<worktree_root>/<repo_prefix>-platform/scripts/git/ps1-harness.sh ]]; then
#     source ~/<worktree_root>/<repo_prefix>-platform/scripts/git/ps1-harness.sh
#   fi
#
# Detección de worktree: si exportás HARNESS_REPO_PREFIX (= workspace.repo_prefix del
# project.config.yaml) el prompt solo aparece dentro de un worktree <repo_prefix>-*.
# Sin esa var, aparece en cualquier repo git.
#
# Format: [<repo_prefix>-{suffix} {branch} {dirty}]$
# Ejemplo: [acme-{sistema}-{slug} wip/{sistema}-{slug} ✗]$

__harness_ps1() {
  local cwd_basename branch dirty prefix
  cwd_basename="$(basename "$PWD" 2>/dev/null)"
  prefix="${HARNESS_REPO_PREFIX:-}"

  # Only show if inside a managed worktree (<repo_prefix>-*), cuando el prefix está definido
  if [[ -n "$prefix" && ! "$cwd_basename" =~ ^"$prefix" ]]; then
    return 0
  fi

  branch="$(git branch --show-current 2>/dev/null || echo '<detached>')"

  # Dirty marker
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    dirty=' \[\033[31m\]✗\[\033[0m\]'
  else
    dirty=' \[\033[32m\]✓\[\033[0m\]'
  fi

  echo -n "\[\033[36m\][${cwd_basename}\[\033[0m\] \[\033[33m\]${branch}\[\033[0m\]${dirty}\[\033[36m\]]\[\033[0m\]"
}

# Backup original PS1 (idempotent)
[[ -z "${HARNESS_PS1_ORIG:-}" ]] && export HARNESS_PS1_ORIG="$PS1"

# Set PS1 to include worktree context
export PS1='$(__harness_ps1)\$ '
