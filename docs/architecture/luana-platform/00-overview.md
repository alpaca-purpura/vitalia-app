# Arquitectura — Luana Platform

## Visión general

`luana-platform` es un monorepo privado que contiene el motor de automatización
AI para ventas y marketing (`core`) y las aplicaciones SaaS de cada brand vertical.

## Topología del monorepo

```
luana-platform/                          ← monorepo raíz
├── core/                                ← Motor SSoT (engine)
│   ├── luana-core-{26 paquetes}/        ← Paquetes Python engine (luana_core_*)
│   └── @luana/                          ← Paquetes TS compartidos (@luana/*)
│       ├── api-client/
│       ├── design-tokens/
│       ├── extension-sdk/
│       ├── format/
│       ├── hooks/
│       ├── schemas/
│       └── ui-kit/
├── nicolify/                            ← Brand: agencias + servicios B2B (flagship)
│   ├── backend/                         ← FastAPI DDD (módulos nicolify/*)
│   ├── frontend/                        ← Next.js FSD-Lite
│   └── config/                          ← brand.yaml + secrets template
├── vitalia/                             ← Brand: salud/bienestar (HIPAA-lite)
│   ├── backend/
│   ├── frontend/
│   └── config/
├── comunify/                            ← Brand: creator economy + educación
│   ├── backend/
│   ├── frontend/
│   └── config/
├── lupulo/                              ← Brand: gastronomía (KDS + reservas)
│   ├── backend/
│   ├── frontend/
│   └── config/
├── .claude-shared/                      ← Reglas + skills Claude Code (harness)
├── .claude/                             ← Config local Claude Code
├── .github/
│   ├── CODEOWNERS                       ← Anti-island gate: paths críticos protegidos
│   ├── PULL_REQUEST_TEMPLATE.md         ← Template PR obligatorio
│   └── workflows/
│       └── ci.yml                       ← CI: python-lint + python-test + ts-lint + ts-test (deferred)
├── docs/
│   └── architecture/
│       └── luana-platform/              ← ADRs + overviews (este directorio)
├── pyproject.toml                       ← uv workspace root
├── package.json                         ← pnpm workspace root
├── pnpm-workspace.yaml                  ← workspace packages
└── turbo.json                           ← pipeline de tareas
```

## Workspace members

### Python (uv)

Declarados en `pyproject.toml` — 26 paquetes engine + 4 brand backends:
```toml
[tool.uv.workspace]
members = [
    "core/luana-core-analytics-engine",
    "core/luana-core-assets",
    "core/luana-core-billing",
    "core/luana-core-brand-studio",
    "core/luana-core-campaigns",
    "core/luana-core-channels",
    "core/luana-core-commercial-calendar",
    "core/luana-core-compliance",
    "core/luana-core-connections",
    "core/luana-core-copilot",
    "core/luana-core-crm",
    "core/luana-core-events",
    "core/luana-core-extension-sdk",
    "core/luana-core-extraction",
    "core/luana-core-iam",
    "core/luana-core-idempotency",
    "core/luana-core-landing",
    "core/luana-core-llm",
    "core/luana-core-observability",
    "core/luana-core-offer-studio",
    "core/luana-core-platform",
    "core/luana-core-sales-agent",
    "core/luana-core-scheduling",
    "core/luana-core-social-proof",
    "core/luana-core-tenant-domains",
    "core/luana-core-tenant-profile",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]
```

**Venv canónico en la raíz:** `${WS}/.venv/bin/{python,pytest,ruff}`. NUNCA `cd {brand}/backend && python -m venv`.

### TypeScript (pnpm)

Declarados en `pnpm-workspace.yaml`:
```yaml
packages:
  - core
  - core/@luana/*
  - nicolify
  - nicolify/frontend
  - vitalia
  - vitalia/frontend
  - vitalia/frontend/widget
  - comunify
  - comunify/frontend
  - lupulo
```

## Subfolders en detalle

### `core/`

Motor SSoT de la plataforma. Todo el código compartido cross-brand vive aquí.

**26 paquetes Python** (`luana_core_*`): analytics-engine, assets, billing, brand-studio,
campaigns, channels, commercial-calendar, compliance, connections, copilot, crm, events,
extension-sdk, extraction, iam, idempotency, landing, llm, observability, offer-studio,
platform, sales-agent, scheduling, social-proof, tenant-domains, tenant-profile.

**7 paquetes TS** (`@luana/*`): api-client, design-tokens, extension-sdk, format, hooks,
schemas, ui-kit.

**Governance:** CODEOWNERS protege `core/**` — requiere review de Chris.
Cambios arquitectónicos requieren ADR (ver `docs/architecture/luana-platform/`).
Lift de brand a engine: ver `docs/promotion-protocol/README.md`.

### `{brand}/`

Cada brand activa (nicolify, vitalia, comunify, lupulo) tiene:
- **backend/**: FastAPI async, DDD modular monolith — `src/modules/{brand}/{módulo}/`
- **frontend/**: Next.js 16 FSD-Lite — `src/{app,components,features,lib}/`
- **config/**: `brand.yaml` (opt-in métricas/canales) + templates `.env`

Cross-brand mirror prohibido — dos brands replican lógica → lift a `core/`.
Ver `.claude/rules/anti-duplication.md`.

## Stack tecnológico

| Capa | Elección | Razón |
|---|---|---|
| Python package manager | **uv** (Astral) | Workspaces nativos, 2026 standard |
| TS package manager | **pnpm 9.15.9** | Workspaces + `workspace:*` protocol |
| Monorepo orchestrator | **Turborepo 2.x** | Task pipeline + caching |
| CI | **GitHub Actions** (deferred) | Calidad se enforce via hooks locales + `make ci-parity` |
| Runtime | **Docker Compose** per brand | `make dev-{brand}` o `make dev-all` |
| Versionado | **SemVer** per brand | `release/{brand}-vX.Y.Z` |

## ADR de referencia

| ADR | Decisión | Link |
|---|---|---|
| 001 | Topología monorepo (monorepo vs multi-repo) | [ADR-001](ADR-001-luana-platform.md) |
| 004 | Git branching + environments | [ADR-004](ADR-004-git-branching-and-environments.md) |
| 009 | Single-hub worktree (N sesiones, 1 árbol) | [ADR-009](ADR-009-single-hub-worktree.md) |
| 010 | Orquestación agéntica (3 planos, trabajadores) | [ADR-010](ADR-010-orquestacion-agentica.md) |

Índice completo: `docs/architecture/luana-platform/README.md`.
