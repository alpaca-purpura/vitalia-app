# AGENTS.md

**Luana platform** (multimarca, post reorg 2026-05-15) — Engine compartido `core/luana-core-*` (27 paquetes) + 10 brand verticals. FastAPI async + Next.js 16 FSD + Clerk + Postgres/Qdrant. Modular Monolith DDD + Docker-First.

Overlay project-specific: ver `CLAUDE.md`. Detalle histórico completo: `docs/rules-detail/_AGENTS-original-backup.md` (load con Read on-demand).

## Quick Commands

| Action | Command |
|---|---|
| Dev up per brand | `make dev-{brand}` o `make dev-all` |
| BE full suite per brand | `cd {brand}/backend && ${WS}/.venv/bin/ruff check . && ${WS}/.venv/bin/pytest tests/architecture/ -v && ${WS}/.venv/bin/pytest --cov=src` |
| FE full suite per brand | `cd {brand}/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run --coverage` |
| Full CI gate | `make ci-parity` (mandatory pre-push-to-main) |
| BE single module | `cd {brand}/backend && ${WS}/.venv/bin/pytest tests/modules/{brand}/{name}/ -v` |
| Alembic per brand | `docker exec luana-dev-{brand}_backend_dev-1 bash -c "cd /workspace/{brand}/backend && /workspace/.venv/bin/alembic upgrade head"` (HB-37 ground-truth) |
| E2E smoke per brand | `cd {brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --project=smoke` |
| ETL contract regen | `make extraction-contract` |

Port allocation: nicolify=8001/3001, vitalia=8002/3002, comunify=8003/3003, lupulo=8004/3004. `${WS}` = `$(git rev-parse --show-toplevel)`.

## Native-First (mandatory)

NEVER lint/tests/type-check dentro Docker. Siempre native Linux (host):
- BE: `cd {brand}/backend && ${WS}/.venv/bin/{ruff,pytest,pip-audit}` (venv 3.12 AT ROOT)
- FE: `cd {brand}/frontend && npx {tsc,eslint,vitest,playwright}`
- Docker solo para: runtime (`make dev-{brand}`), migrations, `make ci-parity`.

## Architecture (high-level)

**Backend** per brand: `{brand}/backend/src/modules/{brand}/{m}/{domain,infrastructure,application,api}/` — Inside-Out DDD. Engine: `core/luana-core-*/src/luana_core_*/`. Cross-brand mirror prohibido (ver `.claude/rules/anti-duplication.md`).

**Frontend** per brand: `{brand}/frontend/src/{app,components,features/{m},lib}/` — FSD-Lite. `fetchClient` auto-inyecta `X-Tenant-ID`.

**DB**: Alembic migrations idempotentes (`IF NOT EXISTS` / `IF EXISTS`). Never `sa.Enum()` en `create_table`.

**Modules conceptuales:** brand, offer, landing, sales_agent, copilot, crm, scheduling, analytics, connections, assets, tenant_domains, commercial_calendar, campaigns, iam. Mapping engine ↔ brand: ver `CLAUDE.md` § "Brand → Core mapping" + tabla full en `docs/rules-detail/_AGENTS-original-backup.md`.

## Git Workflow

**Triple-branch**: `wip/{slug}` (autosave per worktree) → `main` (integración, staging deploy MANUAL) → `release/{brand}-vX.Y.Z` (auto-deploy prod).

**Worktrees obligatorios** sesiones paralelas. Detail completo + scripts + ADR: `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md` + `docs/architecture/luana-platform/ADR-{004,005}*.md`.

**Forbidden:** `git pull`, `git fetch && merge`, `git push --force`, `git revert` sin aprobación, `git add .` / `-A`, `git commit --no-verify`. Push non-fast-forward → STOP.

## Skills (load on-demand cuando tocás módulo)

Tabla completa: ver `CLAUDE.md` § "Conditional Rules" + skills SSoT en `docs/rules-detail/_AGENTS-original-backup.md` § "Skills".

Esenciales por uso frecuencia:
- `/pm-luana` (alias `/pm`) — portfolio + core engineering + promotion gate
- `/pm-{brand}` (×4 activas + 6 templates) — SSoT funcional brand
- `/po-ux` / `/po` / `/ux-agentico` — story refinement
- `/architect` — ready package
- `/dev-team` — autonomous build Conv 2
- `/auditor` — code review Conv 3
- `copilot-expert` / `sales-agent-expert` / `metrics-expert` / `brand-expert` / `offer-expert` / `backend-expert` / `frontend-expert` — module-specific
- `playwright-expert` — E2E + Clerk
- `worktree-protocol` — parallel sessions troubleshoot
- `commit-push` — git workflow delegation Haiku

## Quality Gates

- Lint → arch fitness → tests → coverage → CI parity. Stop on first failure.
- BE coverage threshold: 43%. FE coverage: 20% all categories.
- Ruff line-length: 120. Format: `ruff format --check` (double quotes, spaces).
- TypeScript: `tsc --noEmit` (strict).
- CI parity (`make ci-parity`) mandatory pre-push-to-main.
- Pre-commit hook: ruff staged `.py` files (native, root venv).

## SSoT Guard (contract-guard hook)

Editing estos files dispara reminder:
- `analytics/infrastructure/providers/` o `etl/` → `make extraction-contract` + arch test
- `analytics/domain/metric_catalog.py` → catalog↔contract alignment
- `offer/domain/{archetype,value_level,format}_catalog.py` → bump `_CATALOG_VERSION` + arch tests
- `analytics/application/services/channel_registry.py` → no duplicate STAGE_CHANNEL_MAP
- `copilot/domain/module_registry.py` → ModuleDescriptor entry required

## Key Constraints

- **Tenant isolation**: every query filter `tenant_id`. Ver `.claude/rules/tenant-isolation.md`.
- **PII sanitisation**: response models exclude PII (cuando Tessl rules disponibles).
- **Spanish neutro LatAm**: user-facing text. Ver `.claude/rules/spanish-text.md`.
- **TDD mandatory**: tests before implementation. Ver `.claude/rules/tdd-mandatory.md`.
- **Idempotent migrations**: every DDL `IF NOT EXISTS` / `IF EXISTS`.
- **BE venv path**: `${WS}/.venv/` (Python 3.12, root). Use `.venv/bin/pytest`, not system.
- **E2E Clerk testing token**: required. `playwright-expert` skill cubre lifecycle.
