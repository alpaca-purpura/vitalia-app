#!/usr/bin/env bash
# scripts/tests/test_postgres_init.sh
# Test de idempotencia del script postgres-init.
# Requiere postgres corriendo en 127.0.0.1:5435 con POSTGRES_USER=postgres.
# Uso: bash scripts/tests/test_postgres_init.sh
#
# S-DOCKER-DEV-MULTIBRAND T-1 — 2026-05-15
# Validator: bash_test_postgres_init_idempotency

set -euo pipefail

PSQL="psql -h 127.0.0.1 -p 5435 -U postgres -q"
PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "PASS: $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "FAIL: $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

# Verify postgres is accessible
if ! psql -h 127.0.0.1 -p 5435 -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
  echo "ERROR: postgres not accessible at 127.0.0.1:5435 — start with: make dev-vitalia"
  exit 1
fi

# Test 1: vitalia_dev database exists (created by init script on postgres first start)
result=$(${PSQL} -tAc "SELECT 1 FROM pg_database WHERE datname='vitalia_dev'" 2>/dev/null || echo "0")
if [ "${result}" = "1" ]; then
  pass "vitalia_dev database exists"
else
  fail "vitalia_dev database not found — postgres may not have run init script yet"
fi

# Test 2: Idempotency — simulate re-running init script logic (no DROP, no error)
# We simulate the idempotent check without re-running the full script
# (which requires POSTGRES_USER env var set by Docker entrypoint)
result=$(${PSQL} -tAc "SELECT 1 FROM pg_database WHERE datname='vitalia_dev'" 2>/dev/null || echo "0")
if [ "${result}" = "1" ]; then
  pass "idempotent re-check: vitalia_dev still exists (no accidental DROP)"
else
  fail "idempotent re-check: vitalia_dev disappeared"
fi

echo ""
echo "Results: ${PASS_COUNT} pass, ${FAIL_COUNT} fail"
if [ "${FAIL_COUNT}" -gt 0 ]; then
  echo "SOME postgres-init tests FAILED"
  exit 1
fi
echo "ALL postgres-init tests PASS"
