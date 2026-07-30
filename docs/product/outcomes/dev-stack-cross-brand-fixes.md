---
slug: dev-stack-cross-brand-fixes
kind: outcome-platform
owner: /pm-luana
state: refining
created: 2026-05-16
last_updated: 2026-05-17
priority: HIGH                                  # bumped: bloquea bootstrap comunify+nicolify+lupulo
consumer_brands:
  vitalia: shipped                              # vitalia-dev-stack-functional cerrada 2026-05-17 (receta 12 pasos cementada)
  nicolify: pending                             # nicolify-dev-stack-functional NO abierta (Issue B + workaround bind-mount in-place)
  comunify: pending                             # comunify-dev-stack-functional ABIERTA 2026-05-17 state=refining (replica receta vitalia)
  lupulo: deferred                              # placeholder, bootstrap brand pendiente
canonical_recipe: vitalia/docs/archive/2026/stories/vitalia-dev-stack-functional/07-merge.md  # 12 pasos no rompibles
why_now: |
  Tras configurar Clerk en las 3 brands activas (vitalia/nicolify/comunify) el 2026-05-16,
  descubiertos 4 bugs cross-brand en el dev compose multibrand bootstrap S-DOCKER-DEV-MULTIBRAND.
  2 ya fixed inline ese día (volume path + memory limit nicolify), 2 quedan abiertos
  (uvicorn gap cross-brand + Dockerfile FE COPY core/@luana incompleto). Sin estos fixes,
  no se puede llegar más allá del login Clerk en stack dev — backend autenticado falla.
  Bloquea testing end-to-end de flows que pegan a backend.

origen:
  trigger: Chris pidió configurar Clerk dev de 3 brands homologadamente
  session: 2026-05-16 post commit e7dc4a0
  artifacts_fixed_inline:
    - "{vitalia,nicolify,comunify}/.env.dev (Clerk values + CLERK_ISSUER)"
    - "{vitalia,nicolify,comunify}/.env.dev.template (homologated for future brands)"
    - "{vitalia,nicolify,comunify}/docker-compose.dev.yml (volume mount paths)"
    - "pnpm-workspace.yaml (missing comunify/frontend entry)"
    - "pnpm-lock.yaml (regenerated for comunify/frontend importer)"
    - "nicolify/docker-compose.dev.yml (memory 1G→2G; core/ bind-mount for @luana/*)"

consumer_stories:
  - vitalia/docs/archive/2026/stories/vitalia-dev-stack-functional/  # state=done 2026-05-17, receta canónica cementada
  - comunify/docs/product/stories/comunify-dev-stack-functional/     # state=refining 2026-05-17, replica receta vitalia
  # - nicolify/docs/product/stories/nicolify-dev-stack-functional/   # TODO abrir cuando se priorice
  # - lupulo/docs/product/stories/lupulo-dev-stack-functional/       # TODO abrir cuando brand bootstrap

estimated_effort: 6-10h
---

# dev-stack-cross-brand-fixes — Fixes pendientes dev compose multibrand

> Outcome platform abierto post-mortem tras incidente operativo 2026-05-16 (Clerk login bootstrap 3 brands).
> Reúne 2 issues cross-brand no resueltos. Los issues ya resueltos quedan documentados como
> referencia (no aparecen en stories activas — fueron fixed inline).

## Tablero issues

| # | Issue | Scope | Severity | State | Fixed inline? |
|---|---|---|---|---|---|
| **A** | `uvicorn` no declarado en pyproject de ningún brand backend | vitalia + nicolify + comunify backends | HIGH | open | NO — separate story |
| **B** | Dockerfile FE no COPY core/@luana → image pnpm install incompleto | nicolify FE (vitalia/comunify no usan workspace deps todavía) | MEDIUM | open — workaround via bind-mount runtime | partial |
| C | Compose volume `:/workspace/{brand}/backend/.venv` apuntaba a path inexistente | vitalia + nicolify + comunify | HIGH | **fixed** | YES — `:/workspace/.venv` |
| D | Compose volume FE `:/app` overlaps WORKDIR `/app/{brand}/frontend` | vitalia + nicolify + comunify | HIGH | **fixed** | YES — `:/app/{brand}/frontend` |
| E | `pnpm-workspace.yaml` falta entrada `comunify/frontend` | comunify FE | MEDIUM | **fixed** | YES — entrada agregada + lockfile regen |
| F | Nicolify FE compila /sign-in → OOM-pressure (1G limit) → request hang | nicolify FE only | HIGH | **fixed** | YES — bump 1G→2G |

> Los fixed (C/D/E/F) viven en commits del 2026-05-16. Esta outcome trackea solo A + B.

---

## Issue A — `uvicorn` no declarado en pyproject backends (HIGH)

### Síntoma
Tras fixear compose volumes (C), backends de los 3 brands crashean inmediatamente con:

```
error: Failed to spawn: `uvicorn`
  Caused by: No such file or directory (os error 2)
```

### Root cause
Los 3 brand backends declaran solo `fastapi`, `starlette`, `python-multipart`, `structlog` en
`{brand}/backend/pyproject.toml::dependencies`. **Ninguno declara `uvicorn`.** Verificado:

```bash
grep -lE "uvicorn" pyproject.toml core/luana-core-*/pyproject.toml */backend/pyproject.toml
# (empty — uvicorn NOT in any workspace pyproject)

grep "^name = \"uvicorn\"" uv.lock
# (empty — uvicorn NOT in lockfile either)
```

Pero el compose de los 3 brands llama:

```yaml
command: >
  uv run uvicorn src.main:app --host 0.0.0.0 --port 800X --reload ...
```

Legacy nicolify single-brand pre-multibrand tenía uvicorn en `nicolify/backend/requirements-runtime.txt` (sistema pip). El migrate a uv workspace en S-DOCKER-DEV-MULTIBRAND lo perdió silenciosamente.

### Opciones de fix

1. **Agregar `uvicorn[standard]>=0.34.0` a cada `{brand}/backend/pyproject.toml::dependencies`** (simple, repetido)
2. **Crear `core/luana-core-platform-dev-tools/` con uvicorn + asyncpg + alembic shared, depended-on por todos los brand backends en dev** (DRY, requiere bump core package — promotion gate)
3. **Inyectar via Dockerfile** (`RUN uv pip install uvicorn` post sync) — hack, no semánticamente correcto
4. **Mover uvicorn a un workspace `[dependency-groups.dev]` y sync con `--all-groups` en build** (uv ≥0.4 supported)

Recomendación: **Opción 1** (más simple, ratchet). Brands futuras (saasora/inmoflow/retailly/fixia/guestly/fitflow) heredan vía `_pm-brand-template/`. Promotion candidate a Opción 2 (core dev-tools package) cuando haya ≥5 brands activas.

### Verification gate
- `make dev-{brand}` con cualquier brand: `docker logs luana-dev-{brand}_backend_dev-1` muestra `Uvicorn running on http://0.0.0.0:80XX` dentro de 30s
- `curl http://localhost:80XX/health` retorna 200 + JSON
- Aplicable a vitalia/nicolify/comunify simultáneamente

---

## Issue B — Nicolify FE Dockerfile no COPY core/@luana → install incompleto (MEDIUM)

### Síntoma
Tras fix compose volume (D), nicolify FE muere compilando:

```
Module not found: Can't resolve '@luana/ui-kit'
  > 6 | import { Button } from "@luana/ui-kit";
```

### Root cause
`nicolify/frontend/Dockerfile` dev target hace:

```dockerfile
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY nicolify/frontend/package.json ./nicolify/frontend/package.json
RUN --mount=type=cache,id=pnpm-nicolify,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter "@luana/nicolify-web"
```

NO copia `core/@luana/*`. pnpm install crea symlinks correctos:

```
/app/nicolify/frontend/node_modules/@luana/ui-kit -> ../../../../core/@luana/ui-kit
```

Pero `core/@luana/ui-kit/` no existe en image (no COPYed). Symlinks rotos.

### Workaround aplicado inline (2026-05-16)
Bind mount `./core:/app/core:ro` en `nicolify/docker-compose.dev.yml` para que los symlinks resuelvan al host. Funciona pero:
- Webpack watcha 101 archivos extra (`core/@luana/**/*.ts`), aumenta footprint runtime
- Solo aplicable en dev (no en image final para CI/CD)
- En build de prod ese workaround no aplica → CI build de nicolify FE falla cuando se intente

### Fix propuesto
Modificar `nicolify/frontend/Dockerfile` dev target:

```dockerfile
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY nicolify/frontend/package.json ./nicolify/frontend/package.json
COPY core/@luana/ ./core/@luana/          # NEW: source workspace deps
RUN --mount=type=cache,id=pnpm-nicolify,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter "@luana/nicolify-web..."
                                                              ^^^ NEW: transitive deps
```

Si vitalia/comunify futuras adoptan `@luana/*` deps (ahora no las usan), hereda mismo gap → preventivo: aplicar mismo patrón a sus Dockerfiles ahora (idempotent — solo COPYea si existen workspaces matched).

### Verification gate
- Build `vitalia/frontend/Dockerfile` con target dev sin bind-mount runtime → `next dev` arranca sin "Module not found"
- Mismo para nicolify + comunify
- CI build target final también pasa (consistency)
- Cross-check con builder target (no afecta producción standalone)

---

## Decisión Chris ratificada 2026-05-17

Outcome promovido state=`idea`→`refining` por `/pm-luana` con autorización Chris en sesión
auditoría harness comunify. Decisiones:

- [x] **Priorización HIGH** (bumped from MEDIUM) — bloquea bootstrap dev stack comunify+nicolify+lupulo
- [x] **Patrón story per-brand** (no story brand-agnostic) — cada brand abre `{brand}-dev-stack-functional` y replica receta vitalia 12 pasos. Razón: Dockerfile + compose + pyproject diff per-brand (puertos, names, deps específicos)
- [x] **Receta canónica = vitalia 07-merge.md** — 12 pasos no rompibles ya cementados, ejecución mecánica
- [x] **comunify-dev-stack-functional abierta 2026-05-17** state=refining — primer consumer post-receta
- [ ] nicolify-dev-stack-functional defer (workaround bind-mount in-place mantiene operación)
- [ ] lupulo-dev-stack-functional defer (brand bootstrap pendiente)

Outcome cierra cuando ≥3 brands consumer hayan replicado receta (vitalia ✅ + comunify + 1 más).

## Referencias

- Existing brand story: `vitalia/docs/product/stories/vitalia-dev-stack-functional/01-spec.md`
- Parent outcome: `docs/product/outcomes/docker-dev-multibrand.md` (S-DOCKER-DEV-MULTIBRAND, state=refining)
- Original docker dev multibrand outcome: `docs/product/outcomes/infra-dev-multibrand.md`
- Promotion candidate (opción 2 issue A): `docs/promotion-protocol/` → futuro `core/luana-core-platform-dev-tools/`
- Anti-pattern reference: `.claude/rules/anti-duplication.md` (uvicorn duplicado per brand vs lift shared)

## Bonus — fixes ya aplicados (auditoría 2026-05-16, ratchet shrink-only)

Cementado en commits del 2026-05-16 (`make dev-{vitalia,nicolify,comunify}-tunnel` ahora funcional hasta login Clerk):

- `vitalia/docker-compose.dev.yml`, `nicolify/docker-compose.dev.yml`, `comunify/docker-compose.dev.yml`:
  - Backend named volume `:/workspace/.venv` (no `:/workspace/{brand}/backend/.venv`)
  - Frontend bind mount `:/app/{brand}/frontend` (no `:/app`)
  - Frontend anonymous volume `/app/{brand}/frontend/node_modules` (masking host)
- `vitalia/.env.dev`, `nicolify/.env.dev`, `comunify/.env.dev`: Clerk values + `CLERK_ISSUER` (faltaba — backend `core/luana-core-iam/application/auth.py` lo requiere)
- `pnpm-workspace.yaml`: agregada entrada `comunify/frontend`
- `nicolify/docker-compose.dev.yml`: memory 1G→2G (webpack OOM thrashing con bind-mounted core/)
- `nicolify/docker-compose.dev.yml`: bind mount `./core:/app/core:ro` (workaround issue B)

Verification final 2026-05-16 22:30 LATAM:

| Brand | URL | Status | Title | Clerk pk_test → instance |
|---|---|---|---|---|
| vitalia | https://dev-app.vitalialat.com/sign-in | ✅ 200 | "Iniciar sesión — Vitalia" | moral-gator-27 |
| nicolify | https://dev-app.nicolify.com/sign-in | ✅ 200 | "Nicolify - Dashboard" | more-leech-83 |
| comunify | https://dev-app.comunifyagents.com/sign-in | ✅ 200 | "Iniciar sesión — Comunify" | climbing-lioness-56 |
