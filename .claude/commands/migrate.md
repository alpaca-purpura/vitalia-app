Generate and apply an Alembic migration inside Docker.

Arguments: $ARGUMENTS (migration message)

Steps:
1. Generate migration: `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic revision --autogenerate -m '$ARGUMENTS'"`
2. Show the generated migration file
3. **CRITICAL:** Review the generated code and convert to idempotent SQL:
   - Replace `op.create_table()` with `CREATE TABLE IF NOT EXISTS`
   - Replace `op.add_column()` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
   - Replace `op.create_index()` with `CREATE INDEX IF NOT EXISTS`
   - Never use `sa.Enum()` in `create_table` — reference existing types in raw SQL
4. Apply migration: `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"`
5. Verify: `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic current"`
