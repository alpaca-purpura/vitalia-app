#!/usr/bin/env bash
# test_cleanup_session.sh — Suite de tests bash para scripts/git/cleanup-session.sh
#
# Usage:  bash scripts/tests/test_cleanup_session.sh [TEST_NAME]
# Args:
#   TEST_NAME   (opcional) Nombre de un test especifico a correr.
#               Sin argumento: corre todos los tests.
#
# Exit codes:
#   0  Todos los tests pasaron
#   1  Uno o mas tests fallaron
#
# Tests cubiertos:
#   test_happy_cleanup_session       — worktree limpio → push + remove + exit 0
#   test_edge_uncommitted_changes    — tree dirty → exit 2 + worktree intacto
#   test_negative_no_worktree        — slug sin worktree → exit 1
#   test_adversarial_path_traversal  — SLUG="../../etc/passwd" → exit 1 + ::error::Invalid slug

set -uo pipefail
# Nota: NO se usa 'set -e' (exit-on-error) para poder capturar exit codes de comandos fallidos.
# Cada funcion de test verifica manualmente los exit codes con logica explicita.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TARGET_SCRIPT="${REPO_ROOT}/scripts/git/cleanup-session.sh"

# ── Colores para output ──────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  local name="$1"
  echo -e "${GREEN}PASS${RESET} ${name}"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  local name="$1"
  local reason="${2:-}"
  echo -e "${RED}FAIL${RESET} ${name}${reason:+ — ${reason}}"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

# ── Helpers ──────────────────────────────────────────────────────────────────

setup_temp_repo() {
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  git -C "${tmp_dir}" init -q
  git -C "${tmp_dir}" config user.email "test@test.com"
  git -C "${tmp_dir}" config user.name "Test"
  git -C "${tmp_dir}" commit --allow-empty -m "init" -q
  echo "${tmp_dir}"
}

# Crea un worktree en el repo temporal con un commit de prueba
setup_worktree() {
  local repo="$1"
  local slug="$2"
  local worktree_parent
  worktree_parent="$(dirname "${repo}")"
  local branch="wip/${slug}"
  local worktree_dir="${worktree_parent}/luana-${slug}"

  git -C "${repo}" worktree add -b "${branch}" "${worktree_dir}" HEAD -q
  git -C "${worktree_dir}" config user.email "test@test.com"
  git -C "${worktree_dir}" config user.name "Test"
  git -C "${worktree_dir}" commit --allow-empty -m "wip: test commit" -q

  echo "${worktree_dir}"
}

cleanup_temp() {
  local dir="$1"
  if [[ -d "${dir}" ]]; then
    chmod -R u+w "${dir}" 2>/dev/null || true
    rm -rf "${dir}"
  fi
}

# Ejecuta un comando y captura output + exit code en variables.
# Compatible con set -uo pipefail: captura el exit code real aunque sea != 0.
# Uso: capture_cmd <var_output> <var_exit> cmd args...
capture_cmd() {
  local _out_var="$1"
  local _ec_var="$2"
  shift 2
  local _tmp _ec
  _tmp="$(mktemp)"
  { "$@" > "${_tmp}" 2>&1; }; _ec=$?
  # shellcheck disable=SC2229
  read -r -d '' "${_out_var}" < "${_tmp}" || true
  rm -f "${_tmp}"
  printf -v "${_ec_var}" '%d' "${_ec}"
}

# ── Tests ────────────────────────────────────────────────────────────────────

test_happy_cleanup_session() {
  local name="test_happy_cleanup_session"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="happy-cleanup"
  local worktree_dir
  worktree_dir="$(setup_worktree "${tmp_repo}" "${slug}")"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' GIT_PUSH_DRY_RUN=1 bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -ne 0 ]]; then
    fail "${name}" "exit code ${ec} (esperado 0). Output: ${output}"
    return
  fi

  # Verificar que el worktree fue removido
  if [[ -d "${worktree_dir}" ]]; then
    fail "${name}" "worktree dir ${worktree_dir} aun existe despues del cleanup"
    return
  fi

  if ! echo "${output}" | grep -q "Cleanup complete"; then
    fail "${name}" "output no contiene 'Cleanup complete'. Output: ${output}"
    return
  fi

  # Verificar que la branch sigue existiendo en el repo
  if ! git -C "${tmp_repo}" rev-parse --verify "wip/${slug}" > /dev/null 2>&1; then
    fail "${name}" "branch wip/${slug} fue borrada (no deberia serlo)"
    return
  fi

  pass "${name}"
}

test_edge_uncommitted_changes() {
  local name="test_edge_uncommitted_changes"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="dirty-cleanup"
  local worktree_dir
  worktree_dir="$(setup_worktree "${tmp_repo}" "${slug}")"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  # Crear cambio uncommitted en el worktree
  echo "uncommitted change" > "${worktree_dir}/dirty_file.txt"

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -ne 2 ]]; then
    fail "${name}" "exit code ${ec} (esperado 2). Output: ${output}"
    return
  fi

  if ! echo "${output}" | grep -q "::error::Worktree"; then
    fail "${name}" "output no contiene '::error::Worktree'. Output: ${output}"
    return
  fi

  # Verificar que el worktree sigue intacto
  if [[ ! -d "${worktree_dir}" ]]; then
    fail "${name}" "worktree dir fue removido a pesar del error (no deberia)"
    return
  fi

  if [[ ! -f "${worktree_dir}/dirty_file.txt" ]]; then
    fail "${name}" "archivo dirty_file.txt fue removido del worktree"
    return
  fi

  pass "${name}"
}

test_negative_no_worktree() {
  local name="test_negative_no_worktree"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="nonexistent-worktree"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'" RETURN

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -eq 0 ]]; then
    fail "${name}" "exit code 0 (esperado != 0 porque no existe worktree)"
    return
  fi

  if ! echo "${output}" | grep -q "::error::"; then
    fail "${name}" "output no contiene '::error::'. Output: ${output}"
    return
  fi

  pass "${name}"
}

test_adversarial_path_traversal() {
  local name="test_adversarial_path_traversal"

  local output ec
  capture_cmd output ec bash "${TARGET_SCRIPT}" "../../etc/passwd"

  if [[ "${ec}" -ne 1 ]]; then
    fail "${name}" "exit code ${ec} (esperado 1). Output: ${output}"
    return
  fi

  if ! echo "${output}" | grep -q "::error::Invalid slug"; then
    fail "${name}" "output no contiene '::error::Invalid slug'. Output: ${output}"
    return
  fi

  pass "${name}"
}

# ── Runner ───────────────────────────────────────────────────────────────────

ALL_TESTS=(
  test_happy_cleanup_session
  test_edge_uncommitted_changes
  test_negative_no_worktree
  test_adversarial_path_traversal
)

run_all() {
  echo "=== test_cleanup_session.sh — ${#ALL_TESTS[@]} tests ==="
  for test_fn in "${ALL_TESTS[@]}"; do
    "${test_fn}"
  done
  echo ""
  echo "Results: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
  if [[ ${FAIL_COUNT} -gt 0 ]]; then
    exit 1
  fi
}

run_single() {
  local test_name="$1"
  if declare -f "${test_name}" > /dev/null 2>&1; then
    echo "=== Running ${test_name} ==="
    "${test_name}"
    echo ""
    echo "Results: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
    if [[ ${FAIL_COUNT} -gt 0 ]]; then
      exit 1
    fi
  else
    echo "::error::Test '${test_name}' not found"
    exit 1
  fi
}

if [[ $# -gt 0 ]]; then
  run_single "$1"
else
  run_all
fi
