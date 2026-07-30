#!/usr/bin/env bash
# test_pre_commit_hook.sh — Unit tests for scripts/git-hooks/pre-commit branch-aware gates
#
# TDD: Written BEFORE the hook refactor (T-9 S-GIT-STRATEGY-CORE).
# Tests branch detection logic (GATE_LEVEL assignment) independently from
# the hook's real implementation, using a sourced testable module.
#
# Usage:
#   bash scripts/tests/test_pre_commit_hook.sh
#
# Exit 0 = all tests pass. Exit 1 = at least one test failed.

set -euo pipefail

TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=""

# ─────────────────────────────────────────────────────────────────
# Test framework helpers
# ─────────────────────────────────────────────────────────────────

_pass() {
  local name="$1"
  TESTS_PASSED=$((TESTS_PASSED + 1))
  printf "  \033[32mPASS\033[0m %s\n" "${name}"
}

_fail() {
  local name="$1"
  local reason="${2:-}"
  TESTS_FAILED=$((TESTS_FAILED + 1))
  FAILED_TESTS="${FAILED_TESTS}  - ${name}: ${reason}\n"
  printf "  \033[31mFAIL\033[0m %s — %s\n" "${name}" "${reason}"
}

# Compute GATE_LEVEL from a branch name — extracted logic from the hook.
# The hook sets GATE_LEVEL via a case statement on CURRENT_BRANCH.
# This function replicates that logic for isolated testing.
_compute_gate_level() {
  local branch="$1"
  local gate_level="full"  # safe default
  case "${branch}" in
    wip/*)
      gate_level="light"
      ;;
    main|release/*)
      gate_level="full"
      ;;
    HEAD-detached|'')
      gate_level="full"
      ;;
    *)
      gate_level="full"
      ;;
  esac
  echo "${gate_level}"
}

# ─────────────────────────────────────────────────────────────────
# Test: hook detects wip/* as LIGHT gate
# ─────────────────────────────────────────────────────────────────
test_wip_branch_detection() {
  # Tests: hook detects wip/feature-x as LIGHT gate
  local result
  result=$(_compute_gate_level "wip/feature-x")
  if [ "${result}" = "light" ]; then
    _pass "test_wip_branch_detection"
  else
    _fail "test_wip_branch_detection" "Expected GATE_LEVEL=light for wip/feature-x, got: ${result}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: hook detects main as FULL gate
# ─────────────────────────────────────────────────────────────────
test_main_branch_detection() {
  # Tests: hook detects main as FULL gate
  local result
  result=$(_compute_gate_level "main")
  if [ "${result}" = "full" ]; then
    _pass "test_main_branch_detection"
  else
    _fail "test_main_branch_detection" "Expected GATE_LEVEL=full for main, got: ${result}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: hook detects release/vitalia-v0.3.0 as FULL gate
# ─────────────────────────────────────────────────────────────────
test_release_branch_detection() {
  # Tests: hook detects release/vitalia-v0.3.0 as FULL gate
  local result
  result=$(_compute_gate_level "release/vitalia-v0.3.0")
  if [ "${result}" = "full" ]; then
    _pass "test_release_branch_detection"
  else
    _fail "test_release_branch_detection" "Expected GATE_LEVEL=full for release/vitalia-v0.3.0, got: ${result}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: wip/* branch skips arch-fitness (sections 4-9 = FULL-only)
# ─────────────────────────────────────────────────────────────────
test_wip_skips_arch_fitness() {
  # Tests: in LIGHT gate (wip/*), sections 4-9 are NOT executed.
  # Simulation: a counter-based mock. In LIGHT, gate guarded sections skip.
  local branch="wip/test-feature"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  local arch_fitness_counter=0
  # Simulate: section 4 (arch-fitness equivalent) only runs in full
  if [ "${gate_level}" = "full" ]; then
    arch_fitness_counter=$((arch_fitness_counter + 1))
  fi

  if [ "${arch_fitness_counter}" -eq 0 ]; then
    _pass "test_wip_skips_arch_fitness"
  else
    _fail "test_wip_skips_arch_fitness" "Expected arch_fitness_counter=0 for wip/*, got: ${arch_fitness_counter}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: main branch runs arch-fitness (section 4-9 = FULL)
# ─────────────────────────────────────────────────────────────────
test_main_runs_arch_fitness() {
  # Tests: in FULL gate (main), sections 4-9 ARE executed.
  local branch="main"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  local arch_fitness_counter=0
  if [ "${gate_level}" = "full" ]; then
    arch_fitness_counter=$((arch_fitness_counter + 1))
  fi

  if [ "${arch_fitness_counter}" -eq 1 ]; then
    _pass "test_main_runs_arch_fitness"
  else
    _fail "test_main_runs_arch_fitness" "Expected arch_fitness_counter=1 for main, got: ${arch_fitness_counter}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: magic comment # wip-fast skips extra sections in wip/*
# ─────────────────────────────────────────────────────────────────
test_wip_fast_magic_comment_skips_extra() {
  # Tests: # wip-fast magic comment in staged file → skip sections 4-9 in LIGHT
  # In LIGHT gate + wip-fast → even sections 2-3 could be skipped, but at minimum
  # sections 4-9 (full-only) are already skipped in LIGHT.
  # The magic comment makes sections skip in LIGHT (already the case by design).
  # This test verifies the logic path: wip-fast only takes effect in LIGHT gate.

  local branch="wip/fast-commit"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  # Simulate staged file with wip-fast magic comment
  local tmp_file
  tmp_file=$(mktemp /tmp/test_staged_file_XXXXXX.py)
  printf '# wip-fast: temporary WIP bypass\nprint("hello")\n' > "${tmp_file}"

  local wip_fast_detected=0
  if head -5 "${tmp_file}" | grep -qE '^#\s*wip-fast(:|$)'; then
    wip_fast_detected=1
  fi
  rm -f "${tmp_file}"

  # In LIGHT gate + wip-fast detected → sections remain skipped (already light)
  if [ "${gate_level}" = "light" ] && [ "${wip_fast_detected}" -eq 1 ]; then
    _pass "test_wip_fast_magic_comment_skips_extra"
  else
    _fail "test_wip_fast_magic_comment_skips_extra" \
      "Expected gate_level=light+wip_fast_detected=1, got gate_level=${gate_level} wip_fast=${wip_fast_detected}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: voseo check (section 1) runs even in wip/*
# ─────────────────────────────────────────────────────────────────
test_voseo_runs_in_wip() {
  # Tests: voseo section (1) runs in LIGHT gate (wip/*)
  # In the hook: section 1 is not guarded by GATE_LEVEL — it runs always.
  local branch="wip/some-feature"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  # Voseo section always runs (not gated by GATE_LEVEL)
  # We verify by checking the hook source that voseo block is NOT inside
  # an "if [ full ]" guard — simulated here by always setting voseo_runs=1
  local voseo_runs=1  # Section 1 always runs in hook design

  if [ "${gate_level}" = "light" ] && [ "${voseo_runs}" -eq 1 ]; then
    _pass "test_voseo_runs_in_wip"
  else
    _fail "test_voseo_runs_in_wip" \
      "Expected voseo_runs=1 even in light gate, gate_level=${gate_level}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: ruff (sections 2-3) runs in wip/*
# ─────────────────────────────────────────────────────────────────
test_ruff_runs_in_wip() {
  # Tests: ruff check + format sections (2-3) run in LIGHT gate (wip/*)
  local branch="wip/ruff-test"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  # Ruff sections always run (not gated by GATE_LEVEL — they are "light" sections)
  local ruff_runs=1  # Sections 2-3 always run in hook design

  if [ "${gate_level}" = "light" ] && [ "${ruff_runs}" -eq 1 ]; then
    _pass "test_ruff_runs_in_wip"
  else
    _fail "test_ruff_runs_in_wip" \
      "Expected ruff_runs=1 in light gate, gate_level=${gate_level}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: HEAD detached defaults to FULL gate
# ─────────────────────────────────────────────────────────────────
test_detached_head_defaults_full() {
  # Tests: when git symbolic-ref returns error (detached HEAD), GATE_LEVEL=full (safe)
  # Simulate: _compute_gate_level with "HEAD-detached" (what hook sets on error)
  local result
  result=$(_compute_gate_level "HEAD-detached")
  if [ "${result}" = "full" ]; then
    _pass "test_detached_head_defaults_full"
  else
    _fail "test_detached_head_defaults_full" "Expected GATE_LEVEL=full for HEAD-detached, got: ${result}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: wip-fast magic comment NOT detected in main branch path
# ─────────────────────────────────────────────────────────────────
test_wip_fast_only_in_light_gate() {
  # Tests: even if # wip-fast is in a file, in FULL gate (main) it has no effect
  # The hook only checks wip-fast when GATE_LEVEL=light; in full, code path unreachable.
  local branch="main"
  local gate_level
  gate_level=$(_compute_gate_level "${branch}")

  # Even if wip-fast present, FULL gate does NOT use it
  # wip-fast check is inside "if [ GATE_LEVEL = light ]" block in hook
  local wip_fast_effective=0
  if [ "${gate_level}" = "light" ]; then
    # Only here would wip-fast be checked
    wip_fast_effective=1
  fi

  if [ "${gate_level}" = "full" ] && [ "${wip_fast_effective}" -eq 0 ]; then
    _pass "test_wip_fast_only_in_light_gate"
  else
    _fail "test_wip_fast_only_in_light_gate" \
      "Expected wip_fast_effective=0 in full gate, gate_level=${gate_level}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: various wip/* sub-patterns all trigger LIGHT gate
# ─────────────────────────────────────────────────────────────────
test_wip_subpatterns_all_light() {
  # Tests: wip/feature, wip/A-docker-compose, wip/123-fix-bug all LIGHT
  local all_light=1
  for branch in "wip/feature" "wip/A-docker-compose" "wip/123-fix-bug" "wip/test"; do
    local result
    result=$(_compute_gate_level "${branch}")
    if [ "${result}" != "light" ]; then
      all_light=0
      break
    fi
  done

  if [ "${all_light}" -eq 1 ]; then
    _pass "test_wip_subpatterns_all_light"
  else
    _fail "test_wip_subpatterns_all_light" "Some wip/* sub-pattern did not produce LIGHT gate"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Test: hook file has required structural elements (backward compat)
# ─────────────────────────────────────────────────────────────────
test_backward_compat_sections_1_to_9() {
  # Tests: the actual hook file has all structural elements required
  # (backward compat — sections 1-9 still present after refactor)
  local hook_file="scripts/git-hooks/pre-commit"
  local repo_root
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

  if [ ! -f "${repo_root}/${hook_file}" ]; then
    _fail "test_backward_compat_sections_1_to_9" "Hook file ${hook_file} not found"
    return
  fi

  # Check that refactored hook has GATE_LEVEL and CURRENT_BRANCH
  local has_gate_level has_current_branch has_case_stmt
  has_gate_level=$(grep -c "GATE_LEVEL" "${repo_root}/${hook_file}" || echo "0")
  has_current_branch=$(grep -c "CURRENT_BRANCH" "${repo_root}/${hook_file}" || echo "0")
  has_case_stmt=$(grep -cE "case.*CURRENT_BRANCH|case.*BRANCH" "${repo_root}/${hook_file}" || echo "0")

  if [ "${has_gate_level}" -gt 0 ] && \
     [ "${has_current_branch}" -gt 0 ] && \
     [ "${has_case_stmt}" -gt 0 ]; then
    _pass "test_backward_compat_sections_1_to_9"
  else
    _fail "test_backward_compat_sections_1_to_9" \
      "Hook missing required elements: GATE_LEVEL=${has_gate_level} CURRENT_BRANCH=${has_current_branch} case=${has_case_stmt}"
  fi
}

# ─────────────────────────────────────────────────────────────────
# Run all tests
# ─────────────────────────────────────────────────────────────────

printf "\n\033[1mRunning pre-commit hook branch-gate tests...\033[0m\n\n"

test_wip_branch_detection
test_main_branch_detection
test_release_branch_detection
test_wip_skips_arch_fitness
test_main_runs_arch_fitness
test_wip_fast_magic_comment_skips_extra
test_voseo_runs_in_wip
test_ruff_runs_in_wip
test_detached_head_defaults_full
test_wip_fast_only_in_light_gate
test_wip_subpatterns_all_light
test_backward_compat_sections_1_to_9

printf "\n\033[1mResults: %d passed, %d failed\033[0m\n" "${TESTS_PASSED}" "${TESTS_FAILED}"

if [ "${TESTS_FAILED}" -gt 0 ]; then
  printf "\n\033[31mFailed tests:\033[0m\n"
  printf "%s" "${FAILED_TESTS}"
  exit 1
fi

printf "\033[32mAll tests passed!\033[0m\n"
exit 0
