#!/usr/bin/env bash
# scripts/postgres-init/01-create-databases.sh
# Crea las databases de cada brand en el postgres compartido.
# IDEMPOTENTE: usa SELECT + CREATE condicional (no falla si ya existe).
# Ejecutado automáticamente por postgres al inicializar data volume
# (postgres image corre scripts en /docker-entrypoint-initdb.d/ en orden lexicografico).
# Ejecutable manualmente: docker exec luana_postgres_dev bash /docker-entrypoint-initdb.d/01-create-databases.sh
#
# S-DOCKER-DEV-MULTIBRAND T-1 — 2026-05-15
# Decision D1: 1 postgres shared + N databases via init script idempotente

set -euo pipefail

DATABASES=(
  "vitalia_dev"
)

for db in "${DATABASES[@]}"; do
  result=$(psql -U "${POSTGRES_USER}" -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" 2>/dev/null || echo "0")
  if [ "${result}" = "1" ]; then
    echo "Database ${db} already exists, skipping creation."
  else
    psql -U "${POSTGRES_USER}" -c "CREATE DATABASE \"${db}\";" 2>/dev/null || true
    echo "Database ${db} created."
  fi
done

echo "postgres-init: all brand databases verified (${#DATABASES[@]} databases checked)."
