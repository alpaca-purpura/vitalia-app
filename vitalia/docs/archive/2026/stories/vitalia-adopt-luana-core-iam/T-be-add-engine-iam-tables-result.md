# T-be-add-engine-iam-tables — Result

**Ticket:** T-be-add-engine-iam-tables
**Title:** Migration 022 vitalia — CREATE TABLE users/tenants/user_tenants (mirror engine, schema verbatim)
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Created idempotent Alembic migration `022_vitalia_add_engine_iam_tables.py` that mirrors
engine IAM tables into the vitalia database. This is the schema-mirror exception per
`backend-ddd.md` — engine migration DDL must have a matching SQLAlchemy model in the brand's
domain module for ORM to work.

Migration adds 3 tables used by `luana_core_iam.TenantRepository`, `UserRepository`,
`UserTenantRepository`:
- `tenants` (id UUID, name, slug, country, is_active, created_at, deleted_at)
- `users` (id UUID, email, name, clerk_user_id, is_active, created_at)
- `user_tenants` (id UUID, user_id FK, tenant_id FK, role, is_active, created_at)

Migration 014 (`014_vitalia_tenants_columns.py`) was guarded with a `DO $ ... END $` block
to skip its `ALTER TABLE tenants` statements when tenants table is created fresh by 022
(columns included inline in CREATE TABLE).

## Files touched

- `vitalia/backend/alembic/versions/022_vitalia_add_engine_iam_tables.py` — NEW, idempotent
- `vitalia/backend/alembic/versions/014_vitalia_tenants_columns.py` — MODIFIED (DO $ guard)

## Validators

- ✅ `val-be-arch-1`: Migration uses raw SQL `CREATE TABLE IF NOT EXISTS` (not op.create_table)
- ✅ `val-be-arch-2`: Migration uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- ✅ `val-be-arch-3`: No `sa.Enum(..., create_type=True)` in migration
- ✅ `val-be-unit-1`: Architecture test `test_admin_consumes_engine_repos.py` passes

## Migration applied to DB

Applied directly via psql (Docker bind mount issue: container binds to `/home/chalreme/Proyectos/luana-platform`,
not the worktree `/home/chalreme/Proyectos/luana-vitalia`). SQL applied manually + `alembic_version`
updated to `022_vitalia` via psql.

See T-be-apply-pending-migrations-result.md for full migration chain resolution.
