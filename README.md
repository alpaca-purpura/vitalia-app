# vitalia-app

**Vitalia** — SaaS multitenant de Salud + Bienestar (reservas prepagadas, HIPAA-lite, seguimiento post-tratamiento), operado por un equipo de trabajadores digitales (Valeria supervisora + Lisa · Lucas · Adrián · Mateo · Camila).

> Repo standalone extraído de `luana-platform` (2026-07-30). Contiene la marca `vitalia/` + el engine `core/` (vendored) + el harness de desarrollo agentic completo + el cockpit SDD (`tools/cockpit/`). Las referencias históricas a otras marcas (nicolify/comunify/…) en docs son de origen — esas marcas viven en `luana-platform`.

**¿Nuevo en el equipo? → [`docs/onboarding/README.md`](docs/onboarding/README.md)** (setup paso a paso + flujo git + flujo agentic). Flujo git: [`docs/process/git-workflow.md`](docs/process/git-workflow.md).

## Stack

FastAPI async (DDD modular monolith) · Next.js 16 (FSD-Lite) · Clerk · Postgres · Python 3.12 + uv · pnpm 9.15.9 · Docker Compose (runtime only — lint/tests SIEMPRE nativos en host).

## Quick start (dev)

```bash
# 1. Toolchain
curl -LsSf https://astral.sh/uv/install.sh | sh
nvm install 20 && corepack enable && corepack prepare pnpm@9.15.9 --activate

# 2. Deps + hooks
uv sync && pnpm install && make install-hooks

# 3. Config
cp vitalia/.env.dev.template vitalia/.env.dev   # pedir claves dev al owner

# 4. Stack dev (backend :8002 · frontend :3002 · postgres :5435)
make dev-vitalia
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
curl http://127.0.0.1:8002/health

# 5. Cockpit SDD (board de stories/capabilities · :4002)
make cockpit-up
```

## Layout

| Path | Qué es |
|---|---|
| `vitalia/backend/` | Backend DDD (`src/modules/vitalia/{m}/{domain,infrastructure,application,api}/`) |
| `vitalia/frontend/` | Next.js FSD-Lite + e2e Playwright |
| `vitalia/docs/product/` | SSoT funcional: stories, capabilities, releases, checkpoint |
| `core/` | Engine compartido (27 paquetes `luana-core-*` + `@luana/*` FE) — vendored |
| `.claude/` + `core-harness/` | Harness de desarrollo agentic (rules/skills/agents/hooks · kit 0.5.2) |
| `tools/cockpit/` | Cockpit SDD vendored (Go + UI embebida) — `make cockpit-{up,down,status,build}` |
| `project.config.yaml` | THE SEAM — SSoT de valores project-specific que lee el harness |

## Quality gates

`make ci-parity` pre-push-to-main · BE: ruff + mypy strict + pytest (arch tests primero) · FE: tsc + eslint + vitest · E2E: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke`.

Documentación de proceso: `CLAUDE.md` + `AGENTS.md` + `docs/process/`.
