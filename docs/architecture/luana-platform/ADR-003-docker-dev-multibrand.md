# ADR-003 — Docker dev local multimarca brand-autocontenida

| Campo | Valor |
|---|---|
| ID | ADR-003 |
| Titulo | Docker dev local multimarca brand-autocontenida |
| Estado | Aceptado |
| Fecha | 2026-05-15 |
| Ratificado por | Chris (S-DOCKER-DEV-MULTIBRAND spec ratificada) |
| Implementado en | S-DOCKER-DEV-MULTIBRAND T-1..T-10 |
| Outcome padre | infra-dev-multibrand |
| References | docs/process/docker-dev.md, docs/portfolio/INFRA-MATRIX.md |

## Contexto

Hasta 2026-05-15, el monorepo tenia un `docker-compose.dev.yml` raiz legacy con un postgres single-brand nicolify (solo `nicolify_dev` como POSTGRES_DB). Las 3 brands adicionales (vitalia, comunify, lupulo) no tenian infraestructura de desarrollo local definida, bloqueando:

- Desarrollo local reproducible de vitalia/comunify/lupulo
- CI/CD consistente (S-CICD-DEPLOY necesita Dockerfiles de las brands)
- Paralelismo de desarrollo cross-brand

## Decisiones (D1-D6)

### D1 — 1 postgres shared + N databases via init script idempotente

**Decision:** Un postgres compartido con N databases (nicolify_dev, vitalia_dev, comunify_dev, lupulo_dev), creadas por `scripts/postgres-init/01-create-databases.sh`.

**Alternativa considerada:** N instancias postgres separadas (una por brand).

**Razon de eleccion:** Resource-efficient (1 × 512MB vs 4 × 256MB minimum). Backup cross-brand trivial. La isolation por database es suficiente para desarrollo (no es produccion). N instancias consumirian demasiada RAM en un laptop de desarrollo.

**Consecuencia:** Un DROP accidental afecta solo esa brand (isolation por database, no por servidor). Mitigado con `make dev-clean-{brand}` que recrea la DB via init script.

### D2 — Brand-autocontenida: {brand}/docker-compose.dev.yml per brand

**Decision:** Cada brand tiene su propio compose file `{brand}/docker-compose.dev.yml`. El compose raiz solo contiene shared infra.

**Alternativa considerada:** Un compose raiz unico con todos los servicios de todas las brands.

**Razon de eleccion:** Permite levantar solo la brand que se esta desarrollando (sin consumir RAM de las otras 3). Escala linealmente a las 6 brands futuras sin modificar el compose raiz. Copiar la carpeta brand da un entorno completo (portabilidad).

**Consecuencia:** El Makefile actua como orquestador que compone los archivos. `make dev-vitalia` = `docker compose -f docker-compose.dev.yml -f vitalia/docker-compose.dev.yml up -d`.

### D3 — Qdrant + Redis opt-in profiles

**Decision:** qdrant (profile=vector) y redis (profile=cache) son opt-in. No se activan por default.

**Razon de eleccion:** La mayoria de flujos de desarrollo no necesitan vector search ni cache. Activar por default consumiria 512MB + 256MB extras siempre.

**Consecuencia:** Brands que necesitan qdrant/redis deben usar `make dev-{brand}-vector/cache` o `make dev-all-vector/cache`.

### D4 — Hot-reload monorepo via bind mount source + anonymous volume .venv + uv editable workspace

**Decision:** Bind mount del monorepo completo (`.:/workspace:rw`) + volume nombrado que protege `.venv` del container.

**Razon de eleccion:** Permite que cambios en `core/luana-core-*/` se reflejen inmediatamente en el backend de la brand sin rebuild. El volume protege el `.venv` del container de ser sobreescrito por el host.

**Consecuencia:** Primer cold start lento (~2-3 min mientras uv instala deps). Restart rapido despues (el .venv persiste en el volume).

### D5 — Cloudflared tunnel opt-in profile per brand

**Decision:** cloudflared con `profiles: [tunnel]` en cada brand compose file. Activar con `make dev-{brand}-tunnel`.

**Razon de eleccion:** Solo necesario para pruebas de OAuth/Clerk/webhooks que requieren URL publica. No consumir recursos cuando no se usa.

**Consecuencia:** Chris debe recordar usar `make dev-{brand}-tunnel` cuando prueba integraciones que necesitan URL publica.

### D6 — Port allocation cementada

**Decision:** Puertos fijos por brand, no configurables.

| Brand | Backend | Frontend | Redis DB |
|---|---|---|---|
| nicolify | 8001 | 3001 | 0 |
| vitalia | 8002 | 3002 | 1 |
| comunify | 8003 | 3003 | 2 |
| lupulo | 8004 | 3004 | 3 |
| (futuros) | 8005-8010 | 3005-3010 | 4-9 |

**Cockpit per-worktree (Paradigma A):** el Luana Cockpit (visualizador SDD, filesystem-as-DB) corre por separado en cada worktree y usa el siguiente rango adicional:

> **⚠ SUPERSEDED (I-48, 2026-06-28):** el cockpit dejó de ser per-worktree. Hoy = **un solo multi-cockpit `:4000`** consumido desde chris-corp (home base). La tabla de puertos de abajo se conserva como registro de la decisión original. Modelo vigente: `CLAUDE.md § Cockpit` + `.claude/rules/cockpit-boundary.md`.

| Worktree | Brand inferido | Puerto cockpit |
|---|---|---|
| `luana-platform/` (main) | cross-brand | 4000 |
| `luana-nicolify/` | nicolify | 4001 |
| `luana-vitalia/` | vitalia | 4002 |
| `luana-comunify/` | comunify | 4003 |
| `luana-lupulo/` | lupulo | 4004 |

Estos puertos son independientes del stack brand (backend/frontend). SSoT: root `CLAUDE.md` § Cockpit · Paradigma A.

**Razon de eleccion:** Port collision entre brands levantadas simultaneamente es imposible. Los puertos estan documentados en `{brand}/config/brand.yaml::infra` y en `docs/portfolio/INFRA-MATRIX.md`.

**Consecuencia:** Si los puertos 8001-8004 o 3001-3004 estan ocupados por otra app en el host, hay conflicto. Solucion: detener la otra app o reasignar (actualizar brand.yaml + infra-matrix).

## Pattern canonico: metadata-en-su-lugar + auto-gen index

La decision de arquitectura mas importante no es sobre Docker sino sobre la gestion de metadata de infra:

- **SSoT por instancia:** `{brand}/config/brand.yaml::infra` (puertos, dominios, DB names — el detalle vive ahi)
- **Auto-gen index:** `docs/portfolio/INFRA-MATRIX.md` generado por `make infra-matrix`
- **Auto-freshness:** pre-commit hook Section 10 regenera INFRA-MATRIX.md cuando brand.yaml cambia

Este patron se generaliza a:

| Caso | SSoT | Index | Trigger |
|---|---|---|---|
| Infra (puertos, dominios) | `{brand}/config/brand.yaml::infra` | INFRA-MATRIX.md | pre-commit Section 10 |
| Capabilities shipped | `{brand}/docs/product/capabilities/` | CAPABILITIES-MATRIX.md (futuro) | pre-commit Section 5 (R32) |
| Integraciones activas | `{brand}/config/brand.yaml::integrations` | INTEGRATIONS-MATRIX.md (futuro) | futuro |

## Consecuencias generales

- ✅ Desarrollo local de las 4 brands activas es ahora posible y reproducible
- ✅ Makefile ergonomico (`make dev-vitalia`) oculta la complejidad de multi-compose
- ✅ Port allocation fija elimina colisiones al levantar brands en paralelo
- ✅ Hot-reload funciona para cambios en brand source y en core/ (monorepo bind mount)
- ✅ CI/CD (S-CICD-DEPLOY) tiene Dockerfiles consistentes para build images
- ⚠️ Cold start inicial lento (uv instala deps al crear .venv volume)
- ⚠️ Un postgres compartido: DROP de una DB no afecta otras brands, pero no es isolation de servidor
- ⚠️ lupulo es placeholder hasta Story 13 (S-LUPULO-BOOTSTRAP)
