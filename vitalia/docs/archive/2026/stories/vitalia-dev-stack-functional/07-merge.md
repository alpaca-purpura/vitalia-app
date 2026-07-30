---
story_id: vitalia-dev-stack-functional
outcome: dev-environment-multibrand
merged_at: 2026-05-17T17:00:00Z
merged_by: /pm-vitalia
ratified_by_chris: true
review_final_path: null  # hotfix track — sin /auditor formal porque scope quirúrgico + repro_verified
shipped_commits:
  - e7dc4a0  # feat(dev-tunnels): cloudflared per-brand
  - 930df59  # feat(vitalia): close issues 7-8 + skills capability inventory backport
  # más fixes 1-6 implícitos en bitácora 2026-05-17 03:50 (sesión Claude /pm-luana modo Portfolio)
state_transition: refining → done (skip refined/ready/developing/developed/reviewing — hotfix con repro_verified shipped + smoke green)
capability_yaml_written: false  # infra/bootstrap, no surface user-facing tied a un módulo
adr_written: false               # receta cementada en bitácora checkpoint + outcome platform parent
---

# vitalia-dev-stack-functional — merge

> Story de bootstrap dev-stack. Cierre directo refining → done (skip cadena intermedia). Trabajo shipped en commits `e7dc4a0` + `930df59` + sesión 2026-05-17 03:50.

## Scope cerrado (8 issues)

| # | Issue | Fix shipped | Verificación live 2026-05-17T17:00 |
|---|---|---|---|
| 1 | FE `next: not found` (named volume shadow) | Compose volumes split: bind `./vitalia/frontend:/app/vitalia/frontend:rw` + anonymous `/app/vitalia/frontend/node_modules` (mask host symlinks pnpm) | container `luana-dev-vitalia_frontend_dev-1` up 5h · `curl 127.0.0.1:3002/sign-in → 200` |
| 2 | BE `.venv` incompatible | `UV_PROJECT_ENVIRONMENT=/workspace/.venv` + named volume `vitalia_backend_venv:/workspace/.venv` (no más `:/workspace/vitalia/backend/.venv`) + Dockerfile `RUN uv sync --no-dev --package luana-vitalia` | container `luana-dev-vitalia_backend_dev-1` up 4h · `curl 127.0.0.1:8002/health → 200` |
| 3 | DB `vitalia_dev` no auto-creada | Compose root postgres init.sql crea `{vitalia,nicolify,comunify,lupulo}_dev` (per receta 03:50) | `\l` postgres lista las 4 DBs · `vitalia_dev` tiene 12 public tables |
| 4 | Migrations no aplicadas first start | Compose BE service `command: sh -c "cd /workspace/vitalia/backend && uv run alembic upgrade head && uv run uvicorn src.main:app ..."` (commit `930df59`) | `alembic_version.version_num = 001_vitalia` (head) |
| 5 | Clerk authorized origin | `dev-app.vitalialat.com` añadido a tenant Clerk `moral-gator-27` (manual dashboard, no commit) | FE `/sign-in` renderiza widget Clerk OK |
| 6 | `.env.dev` placeholders | User rellenó `vitalia/.env.dev` con valores reales Clerk + OpenAI (gitignored, no commit) | Stack levanta sin reconnect loops |
| 7 | `/health` endpoint 404 | `vitalia/backend/src/main.py` + `GET /health` con `HealthResponse` DTO (`response_model` mandatory per arch test V-AE-2) — commit `930df59` | `curl 127.0.0.1:8002/health → 200 {"status":"ok","brand":"vitalia","version":"0.1.0"}` |
| 8 | `alembic.ini` localhost | `vitalia/backend/alembic/env.py` prioriza `DATABASE_URL` del compose, convierte `asyncpg→psycopg2` driver sync · Bonus fix `001_vitalia_initial_snapshot.py` jsonb bind-param bug — commit `930df59` | `alembic current → 001_vitalia (head)` desde container |

## Recetas no rompibles (extender a otras brands)

Cuando se levante stack nicolify/comunify/lupulo:

1. `.env.dev` con Clerk values + `CLERK_ISSUER` (faltaba en template original) + URLs sign-in/up
2. Compose volumes:
   - `{brand}_backend_venv:/workspace/.venv` (no `:/workspace/{brand}/backend/.venv`)
   - `./{brand}/frontend:/app/{brand}/frontend:rw` (no `:/app`)
   - `/app/{brand}/frontend/node_modules` anonymous (mask host symlinks pnpm)
3. Compose env BE: `UV_PROJECT_ENVIRONMENT=/workspace/.venv`
4. Dockerfile backend: `COPY {brand}/pyproject.toml` además de `{brand}/backend/pyproject.toml` (workspace-visible stub con deps runtime)
5. Dockerfile backend: `RUN uv sync --no-dev --package luana-{brand}` (no `--frozen` que fallaba silencioso)
6. `{brand}/pyproject.toml`: agregar deps runtime (uvicorn, sqlalchemy, asyncpg, alembic, luana_core_*)
7. Compose BE `command:` `sh -c "cd /workspace/{brand}/backend && uv run alembic upgrade head && uv run uvicorn src.main:app ..."`
8. `{brand}/backend/alembic/env.py` lee `DATABASE_URL` env con `asyncpg→psycopg2` swap
9. `{brand}/backend/src/main.py` registra `GET /health` con `response_model=HealthResponse`
10. Postgres root init.sql crea `{brand}_dev` database
11. Para tunnel CF: agregar `{brand}/deploy/cloudflared/dev-config.yml` + credentials JSON
12. Clerk tenant: agregar `dev-app.{brand}.tld` a authorized origins

## Cambios al producto

### `vitalia/docs/product/checkpoint.md`

```diff
 active_stories:
-  - vitalia-dev-stack-functional   # state: refining (issues 7+8 backend, spec writeup awaiting Chris ratification)
   - vitalia-ux-discovery
   - vitalia-pricing-decision
   - vitalia-payment-adapter-mvp
   - vitalia-copilot-tools-impl
```

### `vitalia/docs/product/stories/vitalia-dev-stack-functional/` → `vitalia/docs/archive/2026/stories/vitalia-dev-stack-functional/`

Snapshot inmutable archivado.

### Sin capability YAML

Trabajo es infra/bootstrap (dev-stack containers + tunnel + migrations + health endpoint), no surface user-facing tied a un módulo del SSoT funcional. Receta cementada en este 07-merge.md (12 pasos arriba) + checkpoint bitácora 2026-05-17 03:50 + outcome platform parent `docs/product/outcomes/dev-stack-cross-brand-fixes.md` (cross-brand work pendiente nicolify/comunify/lupulo).

### Sin ADR

Decisiones técnicas son consecuencia de constraints uv workspace + pnpm + Docker bind mount semantics + Alembic env.py contract. No hay tradeoff arquitectónico cross-cutting que justifique ADR — la receta es prescriptiva mecánica, no estructural.

## Gaps cross-brand pendientes (no scope esta story)

Documentados en outcome platform `docs/product/outcomes/dev-stack-cross-brand-fixes.md` (owner `/pm-luana` modo Portfolio):

- Issue A: gap uvicorn cross-brand (vitalia fixed, nicolify+comunify defer)
- Issue B: nicolify FE Dockerfile no COPY `core/@luana/*` (workaround bind-mount, rompe CI build prod)
- vitalia/backend/ no es workspace member (subproyecto aislado) — solución estructural diferida
- vitalia/pyproject.toml hatch build target con `bypass-selection = true` (vitalia/src/ no existe)

## Próximo paso

Outcome brand-local `dev-environment-multibrand` permanece en `active_outcomes` del brand checkpoint hasta que cross-brand receta se replique a nicolify+comunify+lupulo (cada brand tendrá su propia story bootstrap análoga).

Brand vitalia retoma camino crítico MVP UI via `vitalia-ux-discovery` (next: `/po-ux` v1 spec Slice 1).
