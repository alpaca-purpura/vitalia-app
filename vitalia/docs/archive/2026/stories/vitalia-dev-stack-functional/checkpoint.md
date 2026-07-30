---
story_id: vitalia-dev-stack-functional
outcome: dev-environment-multibrand
state: done
phase: ARCHIVED
last_artifact: 07-merge.md
last_modified: 2026-05-17T17:00:00Z
next_action: "Archived. Receta extensible documentada en 07-merge.md § 'Recetas no rompibles' para retomar bootstrap nicolify/comunify/lupulo."
ratified_by_chris: true
ratified_at: 2026-05-17T17:00:00Z
spawned_at: 2026-05-17T01:50:00Z
spawned_by: claude-direct
parallel_safe: true
blocked_reason: null
audit_iterations: 0
hotfix_metadata:
  repro_verified: true
  repro_command: "make dev-vitalia-tunnel && docker logs luana-dev-vitalia_frontend_dev-1"
  diagnosis_validates_handoff: true
closure:
  state_transition: refining → done (skip refined/ready/developing/developed/reviewing — hotfix con repro_verified shipped + smoke green)
  shipped_commits: [e7dc4a0, 930df59]
  capability_yaml_written: false  # infra/bootstrap, no surface user-facing
  adr_written: false               # receta prescriptiva mecánica, no tradeoff estructural
  archived_to: vitalia/docs/archive/2026/stories/vitalia-dev-stack-functional/

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-dev-stack-functional — checkpoint

## Goal

Dejar la stack `vitalia` levantable end-to-end vía `make dev-vitalia-tunnel` con dominio público `https://dev-app.vitalialat.com/` sirviendo:
- Frontend Next.js renderizando home + login Clerk
- Backend FastAPI respondiendo `/api/v1/health` + endpoints vitalia montados
- Postgres `luana_postgres_dev` saludable + DB `vitalia_dev` con migrations aplicadas
- Tunnel Cloudflare conectando 4 edges sin reconnect loops

## Contexto

Story 11 (`luana-vitalia-bootstrap`, shipped 2026-05-15) entregó código vitalia completo (86 BE tests + 22 FE + 24 E2E pasando), pero la **stack de dev local NUNCA se validó end-to-end**. Commit `e7dc4a0` (2026-05-17, feat(dev-tunnels)) montó el tunnel Cloudflare → validado capa transporte (chain CF→cloudflared→docker network probado vía 530→502→ingressRule logs), pero al levantar la stack completa con `make dev-vitalia-tunnel` los containers FE+BE quedan en restart loop por bugs de bootstrap del image.

**Repro confirmado:**
```
docker logs luana-dev-vitalia_frontend_dev-1
  → sh: next: not found / ELIFECYCLE Command failed
docker logs luana-dev-vitalia_backend_dev-1
  → uv error: Project virtual environment directory `/workspace/vitalia/backend/.venv`
    cannot be used because it is not a compatible environment
```

## Issues identificados

| # | Issue | Causa raíz | Surface fix |
|---|---|---|---|
| 1 | FE `next: not found` | Named volume `vitalia_frontend_node_modules` shadowea `/app/node_modules` del bind mount, queda vacío en first creation | `vitalia/frontend/Dockerfile` o `vitalia/docker-compose.dev.yml` |
| 2 | BE `.venv` incompatible | Named volume `vitalia_backend_venv` corrupto entre rebuilds (uv no recrea sobre directorio existente) | `vitalia/backend/Dockerfile` o compose |
| 3 | DB `vitalia_dev` no se crea automáticamente | Root `docker-compose.dev.yml` levanta postgres pero no crea DBs per brand (no init.sql) | `docker-compose.dev.yml` raíz o entrypoint backend |
| 4 | Migrations no aplicadas en first start | Backend no corre `alembic upgrade head` al startup | `vitalia/backend/Dockerfile` o entrypoint |
| 5 | Clerk authorized origin | `dev-app.vitalialat.com` no está en allowed list del tenant Clerk vitalia | Manual dashboard Clerk |
| 6 | `.env.dev` placeholders | `pk_test_REPLACE_ME`, `sk_test_REPLACE_ME`, `OPENAI_API_KEY=sk-REPLACE_ME` | Manual user (gitignored, no commit) |
| 7 | `/health` endpoint 404 | Endpoint no registrado en FastAPI app. 4 paths probados sin éxito: `/health`, `/api/health`, `/api/v1/health`, `/api/v1/vitalia/health`. Rompe smoke check CLAUDE.md (`curl http://127.0.0.1:8002/health`) + healthcheck Docker | `vitalia/backend/src/main.py` |
| 8 | `alembic.ini` DB URL localhost | `alembic current` desde container falla con `localhost:5432 connection refused` (default psycopg2). `alembic.ini` apunta a localhost en lugar de `luana_postgres_dev`. Migrations NO auto-aplicadas en startup → issue #4 sigue abierto pese a DB `vitalia_dev` existir | `vitalia/backend/alembic.ini` (env DATABASE_URL o `postgresql://...@luana_postgres_dev:5432/vitalia_dev`) + entrypoint Docker auto-upgrade |

## Out of scope (no tocar este story)

- HIPAA-hardening (diferido a Story 11.bis per `vitalia/config/brand.yaml`)
- Multi-site UI (Q2=B D13, diferido)
- Voice cloning (D8 ratificado)
- Production deploy (cloudflared prod tunnel + K8s deploy)
- Cualquier feature funcional vitalia nueva (este story solo fix bootstrap)

## Bitácora

- 2026-05-17 01:50: story creada por chalreme + claude directo post smoke-test tunnel
- 2026-05-17 01:50: spec en `01-spec.md`, state=refining → esperar ratificación Chris
- 2026-05-17 03:50: **STACK OPERATIVA END-TO-END** (sesión Chris + Claude /pm-luana modo Portfolio)
  - Frontend ✅ HTTP 200 `https://dev-app.vitalialat.com/sign-in` con Clerk widget (moral-gator-27)
  - Backend ✅ Uvicorn running 0.0.0.0:8002, OpenAPI 60KB sirviendo, 15 rutas registradas
  - Tunnel ✅ 4 conns CF edges, routing /api → backend, / → frontend
  - Tenant isolation ✅ verificado: `/api/v1/vitalia/treatments` retorna 422 missing X-Tenant-ID
  - Mem healthy: BE 10%/1G, FE 68%/1G — sin OOM

  **Receta aplicada (extender a nicolify/comunify cuando se retomen):**

  1. `.env.dev` con Clerk values + `CLERK_ISSUER` (faltaba en template) + URLs sign-in/up
  2. Compose volumes:
     - `vitalia_backend_venv:/workspace/.venv` (no `:/workspace/vitalia/backend/.venv`)
     - `./vitalia/frontend:/app/vitalia/frontend:rw` (no `:/app`)
     - `/app/vitalia/frontend/node_modules` anonymous (mask host symlinks pnpm)
  3. Compose env: `UV_PROJECT_ENVIRONMENT=/workspace/.venv` (force uv usar venv workspace root)
  4. Dockerfile backend: COPY `vitalia/pyproject.toml` además de `vitalia/backend/pyproject.toml` (workspace-visible stub con deps runtime)
  5. Dockerfile backend: `RUN uv sync --no-dev --package luana-vitalia` (no `--frozen` que fallaba silencioso 0.3s)
  6. `vitalia/pyproject.toml`: agregar deps runtime (uvicorn, sqlalchemy, asyncpg, alembic, luana_core_*)
  7. Borrar stale `vitalia/backend/.venv` host (root-owned de uv sync previo, vía container con bind mount RW)
  8. Volume `vitalia_backend_venv` drop+recreate post Dockerfile change

  **Gaps no resueltos pero documentados en `docs/product/outcomes/dev-stack-cross-brand-fixes.md`:**
  - Issue B: nicolify FE Dockerfile no COPY `core/@luana/*` (workaround bind-mount, rompe CI build prod)
  - Issue A: gap uvicorn era cross-brand (vitalia fixed, nicolify+comunify defer)
  - vitalia/backend/ no es workspace member (subproyecto aislado) — solución estructural diferida
  - vitalia/pyproject.toml hatch build target ahora `bypass-selection = true` (vitalia/src/ no existe)

  state=refining → próximo paso: Chris ratifica spec + considerar promover este story a outcome platform (cross-brand) o cerrarlo brand-specific con receta cementada.

- 2026-05-17 mañana: **Diagnóstico /pm-luana** sobre stack live descubre 2 gaps no documentados en bitácora previa → sumados como issues 7+8:
  - Issue 7: `/health` endpoint 404 confirmado en 4 paths candidatos (`/health`, `/api/health`, `/api/v1/health`, `/api/v1/vitalia/health`). OpenAPI confirma 20 endpoints vitalia registrados pero ningún health. Surface fix: `vitalia/backend/src/main.py`.
  - Issue 8: `alembic current` desde `luana-dev-vitalia_backend_dev-1` falla con `psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused`. `alembic.ini` apunta a localhost cuando debería usar `postgresql://...@luana_postgres_dev:5432/vitalia_dev` o env `DATABASE_URL`. Migrations NO auto-aplican en startup → issue #4 original sigue abierto pese a DB `vitalia_dev` confirmada existente (verificación `\l` en postgres lista las 4 DBs brand).
  - Verificaciones positivas: 4 containers UP healthy (uptime 35-60min), FE 200, BE OpenAPI 200, tunnel CF 200, tenant isolation OK (`/api/v1/vitalia/treatments` → 422 missing X-Tenant-ID), Postgres lista `vitalia_dev`+`nicolify_dev`+`comunify_dev`+`lupulo_dev`.
  - Outcome brand-local `vitalia/docs/product/outcomes/dev-environment-multibrand.md` creado (resuelve gap `active_outcomes` huérfano en `vitalia/docs/product/checkpoint.md`). Consume outcome platform `docs/product/outcomes/dev-stack-cross-brand-fixes.md` para gaps cross-brand.
  - Scope ampliado de 6 → 8 issues. Si Chris ratifica scope quirúrgico (issues 7+8 son hot-fix con `repro_verified: true` ya) → handoff directo `builder-backend` per `.claude/rules/hotfix-repro-mandatory.md`. Si Chris prefiere full ready package → handoff `/architect` para 03-arch + 04-validators + 06-tickets antes de implementación.

- 2026-05-17T17:00: **CIERRE refining → done** (sesión /pm-vitalia). Chris ratificó scope cerrado tras smoke verification live:
  - `curl 127.0.0.1:8002/health → 200 {"status":"ok","brand":"vitalia","version":"0.1.0"}` (issue 7)
  - `curl 127.0.0.1:3002/sign-in → 200` (issues 1, 5, 6)
  - `alembic_version.version_num = 001_vitalia` (issues 4, 8)
  - 12 public tables en `vitalia_dev` (issue 3)
  - 3 containers `luana-dev-vitalia_*` up 4-5h estables (issues 1, 2)
  - Tunnel CF 4 conns + routing /api → BE, / → FE OK

  Skip cadena refined/ready/developing/developed/reviewing (work shipped en commits `e7dc4a0` + `930df59` + sesión 03:50 bitácora previa).

  07-merge.md escrito con receta no rompible 12 pasos para extender a nicolify/comunify/lupulo. No capability YAML (infra/bootstrap, no surface user-facing). No ADR (receta prescriptiva mecánica, no tradeoff estructural).

  Story archived a `vitalia/docs/archive/2026/stories/vitalia-dev-stack-functional/`. Outcome brand-local `dev-environment-multibrand` permanece active hasta replicar receta cross-brand (gaps en outcome platform `docs/product/outcomes/dev-stack-cross-brand-fixes.md`).
