# AGENTS.md

**Luana platform** (multimarca, post reorg 2026-05-15) — Engine compartido `core/luana-core-*` (26 paquetes) + 10 brand verticals consumidoras. Multitenant AaaS marketing/sales automation. FastAPI async + Next.js 16 FSD + Clerk + Postgres/Qdrant. Modular Monolith DDD + Docker-First.

**Nota:** AGENTS.md mantiene defaults heredados de la era single-brand Nicolify. Para topología multimarca + skill `/pm-luana` unificado (Modo Portfolio + Modo Core Engineering) + filosofía pointer-first, ver `CLAUDE.md` (overlay project-specific) + `docs/portfolio/PORTFOLIO.md` (vista master 11 universos).

## Agent Rules <!-- tessl-managed -->

@.tessl/RULES.md follow the [instructions](.tessl/RULES.md)

## Quick Commands

| Action | Command |
|---|---|
| Dev up | `make dev` (Docker) |
| BE full suite | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/ruff format --check src/ tests/ && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts=" && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| FE full suite | `cd frontend && npx tsc --noEmit && npx eslint src/ --cache --cache-location .eslintcache && npx vitest run --coverage --reporter=default --reporter=json --outputFile=/tmp/vitest-coverage.json` |
| Full CI gate | `make ci-parity` (mandatory before `git push origin main`) |
| BE single module | `cd backend && .venv/bin/pytest tests/modules/{name}/ -v` |
| FE single feature | `cd frontend && npx vitest run src/features/{name}/` |
| Alembic migration | Generate + review + make idempotent (`IF NOT EXISTS`), then `docker exec visionarias_brain_dev alembic upgrade head` |
| E2E smoke | `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` |
| ETL contract regen | `make extraction-contract` (required after touching analytics providers/scheduler/workers) |

## Native-First (mandatory)

**NEVER** run lint/tests/type-check inside Docker. Always native Linux (host):
- BE: `cd backend && .venv/bin/{ruff,pytest,pip-audit}` (venv 3.12)
- FE: `cd frontend && npx {tsc,eslint,vitest,playwright}`
- Docker only for: runtime (`make dev`), migrations (`docker exec visionarias_brain_dev alembic`), and `make ci-parity`.

## Architecture

**Backend** `backend/src/modules/{name}/{domain,infrastructure,application,api}/` — Inside-Out DDD. `main.py` mounts `/api/v1/{module}/`. `shared/` = events + entities + infra. `core/` = config + DB session.

**Frontend** `frontend/src/{app,components/{ui,shared},features/{domain},lib}/` — FSD-Lite. `fetchClient` auto-injects `X-Tenant-ID`.

**DB**: Alembic migrations must be **idempotent** (`IF NOT EXISTS` / `IF EXISTS`). Never `sa.Enum()` in `create_table`.

**Modules**: brand, offer, landing, sales_agent, copilot, crm, scheduling, analytics, connections, assets, tenant_domains, commercial_calendar, campaigns, iam, core, shared. Detail → `docs/domains/INDEX.md`.

## Git Workflow

**Triple-branch policy** (post multibrand reorg 2026-05-15 — ADR-004):

| Branch | Rol | CI/CD |
|---|---|---|
| `wip/{slug}` | Autosave por sesion paralela. TTL 30d (cron cleanup). | `ci-wip.yml` (light gates) |
| `main` | Integracion estable. CI gates on push + PR. **Staging deploy MANUAL** (post 2026-05-19 ratificada Chris — ADR-004 § policy update). | `ci.yml` (full) — `cd-staging.yml` solo via `workflow_dispatch` |
| `release/{brand}-vX.Y.Z` | Produccion brand-especifica. Desde main validado. **Único auto-deploy.** | `cd-prod.yml` |

**Worktrees por sesion paralela** (ADR-004 revocó ban legacy 2026-05-15 · ADR-005 cementó modelo D1-D14 2026-05-18):

```bash
# Sesion nueva: worktree dedicado (mec. B — D2/D3/D8)
scripts/git/new-session.sh vitalia story copilot-tools-impl be
# crea ~/Proyectos/luana-vitalia-copilot-tools-impl-be/ on wip/vitalia-copilot-tools-impl-be

# Dashboard cross-worktree (mec. H)
scripts/git/status-all.sh

# Sync + push con advisory (mec. A logic + L)
scripts/git/check-sync.sh
scripts/git/push-wip.sh [BRANCH]

# Terminar sesion
scripts/git/cleanup-session.sh vitalia-copilot-tools-impl-be [--delete-branch]
```

**Skill consultable:** `worktree-protocol` — troubleshoot/explicar/modificar reglas. **Manual Warp:** `docs/process/warp-multibrand-handbook.md`. **SSoT:** `docs/process/parallel-sessions-protocol.md` D1-D14 + ADR-005.

**Forbidden**: `git pull`, `git fetch && merge`, `git push --force`, `git revert` (without approval), `git add .` / `git add -A`, `git commit --no-verify`. Push non-fast-forward → STOP, report. No `git pull`.

**Required**: `git add <path>` by exact file name. M11: nunca >30 min sin push con cambios significativos.

Detail: `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md` + `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md`.

## Skills (load when touching these modules)

| Module/Stack | Skill |
|---|---|
| `copilot/` | `copilot-expert` |
| `sales_agent/` | `sales-agent-expert` |
| `offer/` catalogs/presets | `offer-expert` / `offer-type-preset-expert` |
| `analytics/` ETL/metrics | `metrics-expert` |
| `brand/` identity/positioning | `brand-expert` |
| Backend quality, DDD, currency, arch fitness | `backend-expert` |
| Frontend quality, form runtime | `frontend-expert` |
| Git/PR/release | `git-manager` |
| Deploy to production | `pase-produccion` |
| E2E live verification | `chrome-devtools-verify` |
| Social content creation | `content-hunter` |
| ManyChat integration | `manychat-expert` |
| PM Luana unificado (cross-portfolio 11 universos + core engineering, promotion gate, semver, EPs) | `pm-luana` skill, alias `/pm` (SSoT: `docs/portfolio/PORTFOLIO.md` + `docs/promotion-protocol/` + `docs/core-modules/` — pointer-first, drill-down on demand) |
| PM brand-specific (×4: nicolify, vitalia, comunify, lupulo + 6 templates pendientes) | `pm-{brand}` skill (SSoT: `{brand}/docs/product/`) |
| Bootstrap brand nueva (saasora, inmoflow, retailly, fixia, guestly, fitflow) | `_pm-brand-template` scaffold |
| User story (UI std) — Gherkin + wireframes inline | `po-ux` skill (fusión `/po` + `/ux-ui`) |
| User story (service-only) — Gherkin pure | `po` skill |
| Agentic conversational flow | `ux-agentico` skill |
| Architecture + ready package (validators + guidelines + tickets) | `architect` skill |
| Autonomous build (Conv 2) | `dev-team` skill |
| Code review (Conv 3) | `auditor` skill |
| Portfolio freshness (cross-brand 11 universos) | `make portfolio` → `scripts/generate_portfolio.py` |
| Promotion candidates scan (brand→core lift) | `make scan-promotables` → `scripts/scan_promotables.py` |
| Backlog freshness (per-brand legacy) | `scripts/generate_backlog.py` (per brand) |
| Capability reconciliation (R32 per-brand) | `scripts/reconcile_capabilities.py` (per brand) |

## Quality Gates

- Lint → arch fitness → tests → coverage → CI parity. Stop on first failure.
- BE coverage threshold: 43%. FE coverage: 20% all categories.
- Ruff line-length: 120. Format: `ruff format --check` (double quotes, spaces).
- TypeScript: `tsc --noEmit` (strict).
- CI parity (`make ci-parity`) catches env/UTC/heap/build-context divergences that native runs miss. Mandatory pre-push-to-main.
- Pre-commit hook: ruff on staged `.py` files (native, backend venv).

## SSoT Guard (contract-guard hook)

Editing these files triggers a reminder to run their associated verification:
- `analytics/infrastructure/providers/` or `etl/` → run `make extraction-contract` + arch test
- `analytics/domain/metric_catalog.py` → verify catalog↔contract alignment
- `offer/domain/{archetype,value_level,format}_catalog.py` → bump `_CATALOG_VERSION` + run arch tests both stacks
- `analytics/application/services/channel_registry.py` → no duplicate STAGE_CHANNEL_MAP
- `copilot/domain/module_registry.py` → ModuleDescriptor entry required for new modules

## Key Constraints

- **Tenant isolation**: every query must filter by `tenant_id`. See `.claude/rules/tenant-isolation.md`.
- **PII sanitisation**: Tessl rule loaded via `@.tessl/RULES.md`. Response models must exclude PII.
- **Spanish neutro LatAm**: all user-facing text. Technical terms in English OK.
- **TDD mandatory**: tests before implementation.
- **Idempotent migrations**: every DDL statement must use `IF NOT EXISTS` / `IF EXISTS`.
- **BE venv path**: `backend/.venv/` (Python 3.12). Use `.venv/bin/pytest`, not system `pytest`.
- **E2E requires Clerk testing token**: `make e2e` auto-generates it. Native E2E needs `CLERK_TESTING_TOKEN` env var.
