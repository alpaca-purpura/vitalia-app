#!/usr/bin/env bash
# test_new_session.sh — Suite de tests bash para scripts/git/new-session.sh
#
# Usage:  bash scripts/tests/test_new_session.sh [TEST_NAME]
# Args:
#   TEST_NAME   (opcional) Nombre de un test especifico a correr.
#               Sin argumento: corre todos los tests.
#
# Exit codes:
#   0  Todos los tests pasaron
#   1  Uno o mas tests fallaron
#
# Tests cubiertos:
#   test_happy_new_session           — crea worktree + branch + exit 0
#   test_negative_duplicate_slug     — branch existente → exit 1 + ::error::
#   test_negative_dir_exists         — dir preexistente → exit 1 + ::error::
#   test_adversarial_path_traversal  — SLUG="../../etc/passwd" → exit 1 + ::error::Invalid slug
#   test_adversarial_slash_in_slug   — SLUG="foo/bar" → exit 1
#   test_adversarial_space_in_slug   — SLUG="foo bar" → exit 1 (requiere quotes)
#   test_env_copy_best_effort        — template existente se copia; ausente no falla

set -uo pipefail
# Nota: NO se usa 'set -e' (exit-on-error) para poder capturar exit codes de comandos fallidos.
# Cada funcion de test verifica manualmente los exit codes con logica explicita.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TARGET_SCRIPT="${REPO_ROOT}/scripts/git/new-session.sh"

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

# Crea un repo git temporal limpio para aislar tests del repo real
setup_temp_repo() {
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  git -C "${tmp_dir}" init -q
  git -C "${tmp_dir}" config user.email "test@test.com"
  git -C "${tmp_dir}" config user.name "Test"
  git -C "${tmp_dir}" commit --allow-empty -m "init" -q
  echo "${tmp_dir}"
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

test_happy_new_session() {
  local name="test_happy_new_session"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="test-happy"
  local branch="wip/${slug}"
  local worktree_dir="${worktree_parent}/luana-${slug}"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -ne 0 ]]; then
    fail "${name}" "exit code ${ec} (esperado 0). Output: ${output}"
    return
  fi

  if [[ ! -d "${worktree_dir}" ]]; then
    fail "${name}" "worktree dir ${worktree_dir} no fue creado"
    return
  fi

  local worktree_branch
  worktree_branch=$(git -C "${worktree_dir}" branch --show-current 2>/dev/null || echo "")
  if [[ "${worktree_branch}" != "${branch}" ]]; then
    fail "${name}" "worktree branch es '${worktree_branch}' (esperado '${branch}')"
    return
  fi

  if ! echo "${output}" | grep -q "Worktree ready"; then
    fail "${name}" "output no contiene 'Worktree ready'. Output: ${output}"
    return
  fi

  pass "${name}"
}

test_negative_duplicate_slug() {
  local name="test_negative_duplicate_slug"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="dup-slug"
  local branch="wip/${slug}"
  local worktree_dir="${worktree_parent}/luana-${slug}"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  # Crear la branch de antemano para simular duplicado
  git -C "${tmp_repo}" branch "${branch}" 2>/dev/null || true

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -eq 0 ]]; then
    fail "${name}" "exit code 0 (esperado != 0 porque branch ya existe)"
    return
  fi

  if ! echo "${output}" | grep -q "::error::"; then
    fail "${name}" "output no contiene '::error::'. Output: ${output}"
    return
  fi

  if [[ -d "${worktree_dir}" ]]; then
    fail "${name}" "worktree dir fue creado a pesar del error"
    return
  fi

  pass "${name}"
}

test_negative_dir_exists() {
  local name="test_negative_dir_exists"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="dir-exists"
  local worktree_dir="${worktree_parent}/luana-${slug}"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  # Crear el directorio de antemano
  mkdir -p "${worktree_dir}"

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -eq 0 ]]; then
    fail "${name}" "exit code 0 (esperado != 0 porque dir ya existe)"
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

test_adversarial_slash_in_slug() {
  local name="test_adversarial_slash_in_slug"

  local output ec
  capture_cmd output ec bash "${TARGET_SCRIPT}" "foo/bar"

  if [[ "${ec}" -ne 1 ]]; then
    fail "${name}" "exit code ${ec} (esperado 1). Output: ${output}"
    return
  fi

  if ! echo "${output}" | grep -q "::error::"; then
    fail "${name}" "output no contiene '::error::'. Output: ${output}"
    return
  fi

  pass "${name}"
}

test_adversarial_space_in_slug() {
  local name="test_adversarial_space_in_slug"

  local output ec
  capture_cmd output ec bash "${TARGET_SCRIPT}" "foo bar"

  if [[ "${ec}" -ne 1 ]]; then
    fail "${name}" "exit code ${ec} (esperado 1). Output: ${output}"
    return
  fi

  if ! echo "${output}" | grep -q "::error::"; then
    fail "${name}" "output no contiene '::error::'. Output: ${output}"
    return
  fi

  pass "${name}"
}

test_env_copy_best_effort() {
  local name="test_env_copy_best_effort"
  local tmp_repo
  tmp_repo="$(setup_temp_repo)"
  local worktree_parent
  worktree_parent="$(dirname "${tmp_repo}")"
  local slug="env-copy-test"
  local worktree_dir="${worktree_parent}/luana-${slug}"

  # shellcheck disable=SC2064
  trap "cleanup_temp '${tmp_repo}'; cleanup_temp '${worktree_dir}'" RETURN

  # Crear un .env.dev.template de prueba para nicolify
  mkdir -p "${tmp_repo}/nicolify"
  echo "DB_URL=postgres://test" > "${tmp_repo}/nicolify/.env.dev.template"

  local output ec
  capture_cmd output ec \
    bash -c "cd '${tmp_repo}' && WORKTREE_PARENT_OVERRIDE='${worktree_parent}' bash '${TARGET_SCRIPT}' '${slug}'"

  if [[ "${ec}" -ne 0 ]]; then
    fail "${name}" "exit code ${ec} (esperado 0). Output: ${output}"
    return
  fi

  # Verificar que el template fue copiado
  if [[ ! -f "${worktree_dir}/nicolify/.env.dev" ]]; then
    fail "${name}" ".env.dev no fue copiado desde el template. Output: ${output}"
    return
  fi

  # Templates para vitalia/comunify/lupulo no existen → no debe fallar (ya verificado con exit 0)
  pass "${name}"
}

# ── Runner ───────────────────────────────────────────────────────────────────

ALL_TESTS=(
  test_happy_new_session
  test_negative_duplicate_slug
  test_negative_dir_exists
  test_adversarial_path_traversal
  test_adversarial_slash_in_slug
  test_adversarial_space_in_slug
  test_env_copy_best_effort
)

run_all() {
  echo "=== test_new_session.sh — ${#ALL_TESTS[@]} tests ==="
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
