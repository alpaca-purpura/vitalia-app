# Observed bug — tablas base `vitalia_patients` + `vitalia_leads` faltan en DB dev

**Fecha:** 2026-05-30 · **Origen:** verificación live god-matrix de `vitalia-iam-slice2-phi-real-auth` (anti-teatro). **Severidad:** media (bloquea verificación live de endpoints PHI de paciente/lead en dev; NO afecta el código de auth). **Pre-existente:** sí (no causado por la story de auth).

## Síntoma

Con JWT real de doctor + headers correctos:
- `GET /api/v1/crm/leads` → **HTTP 500**
- `GET /api/v1/crm/patients/{id}` → **HTTP 500** (esperado, misma causa)

## Causa raíz

Backend log: `sqlalchemy.exc.ProgrammingError: relation "vitalia_leads" does not exist`. La DB `vitalia_dev` NO tiene las tablas base `vitalia_patients` ni `vitalia_leads` (sí tiene `vitalia_patient_dental_histories`, `vitalia_patient_medical_histories`, `vitalia_conversations`, `vitalia_messages`, `vitalia_audit_log` + particiones, `vitalia_medical_audit_log`).

```bash
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -t -c \
  "select tablename from pg_tables where schemaname='public' and tablename ~ 'lead|^vitalia_patients';"
# -> vacío
```

## Impacto

- El auth wiring (decoder JWKS real + rol DB + RBAC) **funciona** — el 500 ocurre DESPUÉS de pasar auth, en la query del repo (tabla faltante).
- Bloquea la verificación live del audit-row-on-patient-access (el endpoint de paciente da 500 antes de escribir/leer el audit). El audit está codeado en `patient_repository.py` + integration-tested.

## Fix sugerido (follow-up, NO en esta story)

1. Confirmar si falta una migración Alembic (`vitalia_patients` / `vitalia_leads` create) o si el dev DB quedó desactualizado: `docker exec luana-dev-vitalia_backend_dev-1 alembic current` vs `history`.
2. Si la migración existe → `alembic upgrade head` en dev. Si NO existe → crear migración idempotente (`CREATE TABLE IF NOT EXISTS`) + seed mínimo para god-matrix.
3. Re-ejercer god-matrix sobre `/crm/patients/{id}` + confirmar audit row en `vitalia_audit_log`.

## Decisión

Documentado por la cláusula no-egoísmo (`worktree-dual-strategy.md`). NO se arregla inline (fuera del scope de la story de auth). Candidato a story/hotfix de migración dev.
