# AGENTS.md

**vitalia-app** (standalone single-brand, post extracción 2026-07-30) — Marca **vitalia** + engine vendored `core/luana-core-*` (27 paquetes). FastAPI async + Next.js 16 FSD + Clerk + Postgres/Qdrant. Modular Monolith DDD + Docker-First.

Overlay project-specific: ver `CLAUDE.md`. Overlay de marca (auto-load en `vitalia/**`): `vitalia/CLAUDE.md`.

## Quick Commands

| Action | Command |
|---|---|
| Dev up | `make dev-vitalia` |
| BE full suite | `cd vitalia/backend && ${WS}/.venv/bin/ruff check . && ${WS}/.venv/bin/pytest tests/architecture/ -v && ${WS}/.venv/bin/pytest --cov=src` |
| FE full suite | `cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run --coverage` |
| Full CI gate | `make ci-parity` (mandatory pre-push-to-main) |
| BE single module | `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/{name}/ -v` |
| Alembic | `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"` |
| E2E smoke | `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke` |
| ETL contract regen | `make extraction-contract` |
| Cockpit | `make cockpit-up` (:4002) · `cockpit-status` · `cockpit-down` |

Ports: backend=8002, frontend=3002, cockpit=4002, postgres=5435. `${WS}` = `$(git rev-parse --show-toplevel)`.

## Native-First (mandatory)

NEVER lint/tests/type-check dentro Docker. Siempre native Linux (host):
- BE: `cd vitalia/backend && ${WS}/.venv/bin/{ruff,pytest,pip-audit}` (venv 3.12 AT ROOT)
- FE: `cd vitalia/frontend && npx {tsc,eslint,vitest,playwright}`
- Docker solo para: runtime (`make dev-vitalia`), migrations, `make ci-parity`.

## Architecture (high-level)

**Backend**: `vitalia/backend/src/modules/vitalia/{m}/{domain,infrastructure,application,api}/` — Inside-Out DDD. Engine: `core/luana-core-*/src/luana_core_*/`. Mirror del engine en la marca PROHIBIDO (ver `.claude/rules/anti-duplication.md`).

**Frontend**: `vitalia/frontend/src/{app,components,features/{m},lib}/` — FSD-Lite. `fetchClient` auto-inyecta `X-Tenant-ID`.

**DB**: Alembic migrations idempotentes (`IF NOT EXISTS` / `IF EXISTS`). Never `sa.Enum()` en `create_table`.

**Modules conceptuales:** brand, offer, landing, sales_agent, copilot, crm, scheduling, analytics, connections, assets, tenant_domains, commercial_calendar, campaigns, iam. Mapping engine ↔ marca: `project.config.yaml::domain_modules`.

## Git Workflow

**Trunk-based** (SSoT `docs/process/git-workflow.md`): `main` único branch permanente · por story `story/{id}` vida corta → squash-merge → borrar · releases hoy `release/vitalia-vX.Y.Z` (objetivo: tags).

**Forbidden:** `git pull` con merge/rebase (solo `--ff-only` sobre branch limpio), `git push --force`, `git revert` sin aprobación, `git add .` / `-A`, `git commit --no-verify`. Push non-fast-forward → STOP.

## Skills (load on-demand cuando tocás módulo)

Tabla completa: `CLAUDE.md` § "Conditional Rules".

Esenciales:
- `/pm-vitalia` (alias `/pm`) — SSoT funcional marca + engine governance
- `/po-ux` / `/po` / `/ux-agentico` — story refinement
- `/architect` — ready package · `/dev-team` — build Conv 2 · `/auditor` — review Conv 3
- `copilot-expert` / `sales-agent-expert` / `metrics-expert` / `brand-expert` / `offer-expert` / `backend-expert` / `frontend-expert` / `vitalia-design-system` — module-specific
- `playwright-expert` — E2E + Clerk · `commit-push` — git delegation Haiku

## Quality Gates

- Lint → arch fitness → tests → coverage → CI parity. Stop on first failure.
- BE coverage threshold: 43%. FE coverage: 20% all categories.
- Ruff line-length: 120. Format: `ruff format --check` (double quotes, spaces).
- TypeScript: `tsc --noEmit` (strict).
- Hooks locales = enforcement primario (`make install-hooks` obligatorio). Pre-commit: light en `story/*`/`wip/*`, full en `main`.
- `make ci-parity` mandatory pre-push-to-main (marker `.git/ci-parity-passed-vitalia-<sha>`).

## SSoT Guard (contract-guard hook)

Editing estos files dispara reminder:
- `analytics/infrastructure/providers/` o `etl/` → `make extraction-contract` + arch test
- `analytics/domain/metric_catalog.py` → catalog↔contract alignment
- `offer/domain/{archetype,value_level,format}_catalog.py` → bump `_CATALOG_VERSION` + arch tests
- `analytics/application/services/channel_registry.py` → no duplicate STAGE_CHANNEL_MAP
- `copilot/domain/module_registry.py` → ModuleDescriptor entry required

## Key Constraints

- **Tenant isolation**: every query filter `tenant_id`. Ver `.claude/rules/tenant-isolation.md`.
- **PII sanitisation**: response models exclude PII. Ver `.claude/rules/pii-sanitisation.md`.
- **Spanish neutro LatAm**: user-facing text. Ver `.claude/rules/spanish-text.md`.
- **TDD mandatory**: tests before implementation. Ver `.claude/rules/tdd-mandatory.md`.
- **Idempotent migrations**: every DDL `IF NOT EXISTS` / `IF EXISTS`.
- **BE venv path**: `${WS}/.venv/` (Python 3.12, root). Use `.venv/bin/pytest`, not system.
- **E2E Clerk testing token**: required. `playwright-expert` skill cubre lifecycle.
- **DoD live-verify**: nada es `done` sin ejercerlo contra el stack real. Ver `.claude/rules/definition-of-done-live-verify.md`.
