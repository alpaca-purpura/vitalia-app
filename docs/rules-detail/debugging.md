# Debugging — detalle (ex always-on rule body, evicted W1-Phase2 2026-06-09)

> Runbook completo: `docs/process/docker-dev.md`. Docker-compose **per-brand** (post 2026-05-15 reorg). Stack: `make dev-{brand}` o `make dev-all`.

## Diagnóstico

Containers naming convention: `luana-dev-vitalia_{service}_dev-1` (ej: `luana-dev-vitalia_backend_dev-1`, `luana-dev-vitalia_frontend_dev-1`).

```bash
WS=$(git rev-parse --show-toplevel)
BRAND=vitalia

# BE logs
docker logs luana-dev-${BRAND}_backend_dev-1 --tail 100
docker logs luana-dev-${BRAND}_backend_dev-1 --tail 200 2>&1 | grep -iE 'error|traceback|exception'

# FE logs
docker logs luana-dev-${BRAND}_frontend_dev-1 --tail 100

# Health stack per brand
docker compose -f ${WS}/${BRAND}/docker-compose.dev.yml ps

# Migration (per brand alembic config)
# Ground-truth 2026-06-05 (HB-37): workdir = /workspace/${BRAND}/backend, venv = /workspace/.venv (NO /app, NO bare alembic)
docker exec -t luana-dev-${BRAND}_backend_dev-1 bash -c "cd /workspace/${BRAND}/backend && /workspace/.venv/bin/alembic current"
```

- TSC/lint/tests: ver CLAUDE.md (native, `${WS}/.venv/bin/...` o `npx`).

**Legacy containers** `visionarias_brain_dev` / `visionarias_client_dev` ya no existen — eran single-brand pre-reorg.

## Top patterns (~80% bugs)
1. Missing `tenant_id` filter → empty/cross-tenant leak
2. SA 1.x `session.query()` → debe `select(Model).where(...)`
3. Docker volume stale → `docker compose -f ${WS}/${BRAND}/docker-compose.dev.yml up -d --build <svc>`
4. Migration no aplicada → `alembic current` vs `history` (per-brand)
5. Clerk token expired → 401
6. Cross-module import → viola DDD (o cross-brand mirror — ver `anti-duplication.md`)
7. Next.js build (standalone + Pages Router 404) — pre-existing
8. ETL credential expiry (Meta/GA4)
9. Missing env var (silencioso) — verify `{brand}/.env.dev` vs `{brand}/docker-compose.dev.yml`
10. Qdrant unavailable → vector search falla silencioso
11. Wrong port: vitalia=8002 (BE) / 3002 (FE)
12. Engine package not editable in venv → `cd ${WS} && uv sync` desde root (NUNCA dentro de `{brand}/backend/`)

## Fix Quality
Root cause only. Leave file better (cleanup tech debt mismo file). No new debt (TODO/HACK/`any`/disabled lint). Verify native antes claim. Una hipótesis por fix. **Regression test FIRST** (RED reproduce bug → fix GREEN). Engine bug (`core/luana-core-*/`) → reproducir en cada brand consumer; brand-specific → solo `{brand}/`.
