---
slug: docker-dev-multibrand
kind: outcome-sub
parent_outcome: infra-dev-multibrand
owner: /pm-luana
state: refining
created: 2026-05-15
priority: HIGH
why_now: |
  docker-compose.dev.yml actual es legacy single-brand nicolify (solo postgres, sin redis/qdrant
  ni multibrand). Imposible probar vitalia/comunify/lupulo en local de forma reproducible.
  Bloquea Tema 1 (CI/CD necesita Dockerfiles consistentes para build images).
estimated_effort: 14-16h
stories:
  - S-DOCKER-DEV-MULTIBRAND
---

# docker-dev-multibrand — Docker dev local multimarca brand-autocontenida

> Sub-outcome de [O-INFRA-DEV-MULTIBRAND](./infra-dev-multibrand.md). Resuelve la pieza dev local.

## Decisión final

- **1 postgres shared + N databases** vía init script. Confirmado no afecta prod (cada brand su servidor).
- **Brand-autocontenida:** `{brand}/docker-compose.dev.yml` per brand (vendible copiando carpeta).
- **Qdrant + Redis opt-in profiles** (no all-on por default).
- **Hot-reload monorepo** vía bind mount source + anonymous volume `.venv` + uv editable workspace.
- **Cloudflared tunnel opt-in profile** per brand (para tests OAuth/Clerk/webhooks).

## Estructura archivos

```
luana-platform/
├── docker-compose.dev.yml          # base: shared infra (postgres único + qdrant + redis con profiles)
├── scripts/postgres-init/
│   └── 01-create-databases.sh      # crea N databases en postgres único (idempotente)
├── Makefile                         # wrappers: make dev-{brand}, dev-{brand}-tunnel, dev-all, dev-down-{brand}, dev-clean-{brand}, infra-matrix
└── {brand}/
    ├── docker-compose.dev.yml      # servicios DE ESA brand: backend + frontend + cloudflared
    ├── backend/Dockerfile          # uv-based, bind-mount-friendly
    ├── frontend/Dockerfile         # Node 20 + pnpm, bind-mount-friendly
    ├── config/brand.yaml           # ⭐ AGREGAR sección infra: con metadata canónica
    ├── .env.dev.template            # checked-in, copy a .env.dev (gitignored)
    └── .env.prod.template           # checked-in, placeholder values
```

## Port allocation (cementado)

| Brand | Backend host | Frontend host | DB name | Redis DB | Qdrant collection prefix |
|---|---|---|---|---|---|
| nicolify | 8001 | 3001 | nicolify_dev | 0 | nicolify_ |
| vitalia | 8002 | 3002 | vitalia_dev | 1 | vitalia_ |
| comunify | 8003 | 3003 | comunify_dev | 2 | comunify_ |
| lupulo | 8004 | 3004 | lupulo_dev | 3 | lupulo_ |
| (saasora futura) | 8005 | 3005 | saasora_dev | 4 | saasora_ |
| (inmoflow futura) | 8006 | 3006 | inmoflow_dev | 5 | inmoflow_ |
| (retailly futura) | 8007 | 3007 | retailly_dev | 6 | retailly_ |
| (fixia futura) | 8008 | 3008 | fixia_dev | 7 | fixia_ |
| (guestly futura) | 8009 | 3009 | guestly_dev | 8 | guestly_ |
| (fitflow futura) | 8010 | 3010 | fitflow_dev | 9 | fitflow_ |
| (shared infra) | postgres 5435 / qdrant 6333 / redis 6379 | — | — | — | — |

**Aviso:** redis tiene 16 DBs numéricas (0-15). 10 brands cabe. Si llega 17+ migrar a `KEYS prefix:*`.

## Pattern canónico "metadata-en-su-lugar + auto-gen index"

**Cementado para casos similares (infra, capabilities, integrations, versions, compliance).**

### Aplicación a infra

**SSoT por brand:** `{brand}/config/brand.yaml::infra` (todo el detalle vive acá)

```yaml
brand:
  slug: vitalia
  vertical: salud-bienestar

infra:
  dev:
    backend_port: 8002
    frontend_port: 3002
    database_name: vitalia_dev
    redis_db: 1
    qdrant_collection_prefix: vitalia_
    domain: vitalia-dev.nicolify.com
    cloudflared_tunnel: vitalia-dev
  staging:
    domain: vitalia-test.nicolify.com
    server: tbd-staging-cluster
  prod:
    domain: app.vitalialat.com
    server: tbd
    cloudflared_tunnel: vitalia-prod
```

**Auto-gen index al raíz:** `docs/portfolio/INFRA-MATRIX.md` generado por `make infra-matrix` (script `scripts/generate_infra_matrix.py`)

### Generalización futura (cementar en /pm-luana SKILL.md)

| Caso | SSoT por instancia | Auto-gen index al raíz | Comando regen |
|---|---|---|---|
| Infra (puertos, dominios) | `{brand}/config/brand.yaml::infra` | `docs/portfolio/INFRA-MATRIX.md` | `make infra-matrix` |
| Capabilities shipped | `{brand}/docs/product/capabilities/{cap}.yaml` | `docs/portfolio/CAPABILITIES-MATRIX.md` | `make capabilities-matrix` (futuro) |
| Integraciones activas | `{brand}/config/brand.yaml::integrations` | `docs/portfolio/INTEGRATIONS-MATRIX.md` | `make integrations-matrix` (futuro) |
| Versions core consumed | `{brand}/pyproject.toml::dependencies` | `docs/portfolio/CORE-VERSIONS-MATRIX.md` | `make core-versions-matrix` (futuro) |

## Story `S-DOCKER-DEV-MULTIBRAND` — tickets

| Ticket | Descripción | Tipo |
|---|---|---|
| T-1 | Rewrite `docker-compose.dev.yml` raíz (solo postgres + qdrant + redis con profiles opt-in) + script `scripts/postgres-init/01-create-databases.sh` idempotente | code |
| T-2 | Crear `{brand}/docker-compose.dev.yml` × 4 (nicolify, vitalia, comunify, lupulo) con backend + frontend + cloudflared opt-in profile | code |
| T-3 | Agregar sección `infra:` a `{brand}/config/brand.yaml` × 4 con dev + staging + prod metadata | code |
| T-4 | Crear Dockerfiles faltantes: vitalia/backend, vitalia/frontend, comunify/backend, comunify/frontend, lupulo/backend, lupulo/frontend (patrón nicolify uv-workspace-friendly) | code |
| T-5 | Audit + ajuste `nicolify/{backend,frontend}/Dockerfile` para consistencia uv editable bind-mount-friendly | code |
| T-6 | Nuevo `Makefile` raíz con targets `dev-{brand}`, `dev-{brand}-tunnel`, `dev-all`, `dev-down-{brand}`, `dev-clean-{brand}` | code |
| T-7 | `.env.dev.template` + `.env.prod.template` per brand × 4 + actualizar `.gitignore` | code |
| T-8 | Script `scripts/generate_infra_matrix.py` + target `make infra-matrix` → genera `docs/portfolio/INFRA-MATRIX.md` | code |
| T-9 | Pre-commit hook regenera `INFRA-MATRIX.md` cuando se edita cualquier `{brand}/config/brand.yaml` (auto-freshness) | code |
| T-10 | Runbook `docs/process/docker-dev-multibrand.md` + ADR-003 + actualizar `CLAUDE.md` workspace bootstrap section + actualizar `/pm-luana` SKILL.md para referenciar el INFRA-MATRIX index pattern | docs |

## Trade-offs cementados

| Decisión | Pro | Contra |
|---|---|---|
| 1 postgres + N databases | Resource-efficient (1 × 512MB vs 4 × 256MB), backup cross-brand trivial | Si una brand DROP DB accidental afecta solo su DB (aislado por database) |
| `--profile X` per brand | Levantás solo lo que probás, no consume RAM idle | Mitigado con `make dev-X` wrapper |
| Named volumes per-brand venv/node_modules | Aísla, evita conflict cross-uv-workspace | Más volumes (gestionado por make targets) |
| Anonymous volume `.venv` + bind mount source | Hot reload monorepo perfecto (core change propaga) | Primer build lento ~2-3min (después fast) |
| Qdrant + Redis en profiles opt-in | No consume RAM si brand no los usa | Brand debe declarar dependency en su profile |
| Cloudflared tunnel profile opt-in | No consume cuando no probás integraciones | Chris recuerda `make dev-X-tunnel` cuando lo necesita |

## Referencias

- Outcome padre: [infra-dev-multibrand](./infra-dev-multibrand.md)
- Research sources: Docker Compose Profiles (Docker Docs), Multi-tenant Docker (OneUptime), uv in Docker (Astral)
