#!/usr/bin/env bash
# Test: cleanup-session.sh Story-Closure-Gate (Layer 5) scope (fix 2026-06-16).
# El gate debe sweepear SOLO la marca propia del worktree — no bloquear por stories ajenas.
#
# Cómo: corre el script REAL con --force + GIT_PUSH_DRY_RUN=1 contra dirs construidos
# (no-git) bajo ~/Proyectos/luana-<arg>. Si el gate PASA, el script muere recién en
# `git worktree remove` (dir no es worktree real) → exit 1. Si BLOQUEA → exit 2.
# Assert: exit==2 ⇔ gate bloqueó.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${HERE}/../cleanup-session.sh"
WS_PARENT="$(dirname "$(git -C "${HERE}" rev-parse --show-toplevel)")"
FAILS=0

plant_story() {  # $1=worktree_dir $2=brand $3=story_state
  mkdir -p "$1/$2/docs/product/stories/fake-open"
  printf 'state: %s\n' "$3" > "$1/$2/docs/product/stories/fake-open/checkpoint.md"
}
manifest() { printf 'brand: %s\nworktree_type: ephemeral\n' "$2" > "$1/.session.yaml"; }

run_gate() {  # $1=arg → echoes exit code
  CLEANUP_SKIP_STORY_GATE=0 GIT_PUSH_DRY_RUN=1 bash "${SCRIPT}" --force "$1" >/dev/null 2>&1
  echo $?
}

assert_eq() {  # $1=label $2=got $3=want
  if [[ "$2" == "$3" ]]; then echo "  ✓ $1 (exit=$2)"; else echo "  ✗ $1 (exit=$2, want=$3)"; FAILS=$((FAILS+1)); fi
}

cleanup() { rm -rf "${WS_PARENT}/luana-core-gatetestaa" "${WS_PARENT}/luana-vitalia-gatetestbb" "${WS_PARENT}/luana-vitalia-gatetestcc"; }
trap cleanup EXIT
cleanup

echo "Test: cleanup-session story-gate scope"

# A — worktree CORE con story nicolify open (snapshot incidental) → gate NO bloquea
A="${WS_PARENT}/luana-core-gatetestaa"; mkdir -p "$A"; manifest "$A" core; plant_story "$A" nicolify reviewing
assert_eq "core worktree NO bloqueado por story nicolify ajena" "$(run_gate core-gatetestaa)" 1

# B — worktree VITALIA con story PROPIA vitalia open → gate SÍ bloquea (exit 2)
B="${WS_PARENT}/luana-vitalia-gatetestbb"; mkdir -p "$B"; manifest "$B" vitalia; plant_story "$B" vitalia developing
assert_eq "vitalia worktree bloqueado por su PROPIA story open" "$(run_gate vitalia-gatetestbb)" 2

# C — worktree VITALIA con story nicolify open pero NINGUNA vitalia → gate NO bloquea
C="${WS_PARENT}/luana-vitalia-gatetestcc"; mkdir -p "$C"; manifest "$C" vitalia; plant_story "$C" nicolify reviewing
assert_eq "vitalia worktree NO bloqueado por story nicolify ajena" "$(run_gate vitalia-gatetestcc)" 1

[[ $FAILS -eq 0 ]] && { echo "PASS"; exit 0; } || { echo "FAIL ($FAILS)"; exit 1; }
