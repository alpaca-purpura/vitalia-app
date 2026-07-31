# Onboarding — vitalia-app

> Guía de inicialización para un developer nuevo. Objetivo: al final del día 1 tienes el stack corriendo, los hooks instalados, el cockpit abierto y entiendes cómo fluye una story de idea a producción. Si algo de esta guía no funciona tal cual, repórtalo — este doc es parte del producto.

## 1. Qué es vitalia-app

**Vitalia** es un SaaS multitenant de Salud + Bienestar (HIPAA-lite): clínicas y profesionales gestionan reservas prepagadas, pacientes y seguimiento post-tratamiento, operados por un equipo de trabajadores digitales (Valeria como supervisora + especialistas Lisa · Mateo · Adrián · Lucas · Camila). La arquitectura es un **modular monolith DDD**: el backend FastAPI vive en `vitalia/backend/src/modules/vitalia/{módulo}/{domain,infrastructure,application,api}/` y consume un **engine vendored** de 27 paquetes Python (`core/luana-core-*`) vía Extension SDK — la regla de oro es *consumir el engine por import, nunca duplicarlo*. El frontend es Next.js 16 con arquitectura FSD-Lite (`vitalia/frontend/src/{app,components,features,lib}/`), auth con Clerk y Postgres como base. Todo dato está aislado por `tenant_id` — sin excepciones.

Lo segundo que tienes que saber: el producto **se construye con un flujo agentic**. Chris (y tú) orquestan Claude Code con *skills* especializados (`/pm-vitalia`, `/po-ux`, `/architect`, `/dev-team`, `/auditor`) que refinan, diseñan, implementan con TDD y auditan cada story. Los `.md`/`.yaml` bajo `vitalia/docs/product/` son la base de datos de ese proceso, y el **cockpit** (un visualizador local) la muestra en vivo. Tu trabajo no es solo escribir código: es operar y supervisar ese pipeline.

## 2. Setup local paso a paso

Requisitos previos: Linux/macOS, `git`, Docker + Docker Compose v2 corriendo.

### 2.1 Toolchain

```bash
# Python: uv (gestiona el venv del workspace, Python 3.12)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node 20 vía nvm + pnpm 9.15.9 vía corepack
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install 20
corepack enable && corepack prepare pnpm@9.15.9 --activate
```

### 2.2 Dependencias + hooks (OBLIGATORIO)

```bash
cd vitalia-app   # raíz del repo
uv sync              # crea .venv/ en la RAÍZ del workspace (27 paquetes core editable)
pnpm install         # workspace pnpm (frontend + paquetes @luana/*)
make install-hooks   # ← OBLIGATORIO: sin hooks no hay gates de calidad
```

`make install-hooks` symlinkea `pre-commit`, `pre-push` y `post-commit` desde `scripts/git-hooks/`. **Los hooks locales SON el enforcement de calidad de este repo** (GitHub Actions está en modo deferred). Saltárselos (`--no-verify`) está prohibido.

Importante: el venv vive en la **raíz** (`.venv/`). Nunca crees un venv dentro de `vitalia/backend/` — rompe la resolución de los paquetes `luana_core_*`.

Verificación:

```bash
.venv/bin/python -c "import luana_core_extension_sdk, luana_core_platform; print('OK')"
ls -l "$(git rev-parse --git-path hooks)/pre-commit"   # → symlink a scripts/git-hooks/pre-commit
```

### 2.3 Variables de entorno

```bash
cp vitalia/.env.dev.template vitalia/.env.dev
```

Pide a Chris los valores reales (claves Clerk dev, passwords). **NUNCA se commitea `.env.dev`** ni ningún `.env*` — el pre-commit y la política de git lo prohíben.

### 2.4 Levantar el stack dev

```bash
make dev-vitalia
```

Levanta Postgres (`127.0.0.1:5435`) + backend (`:8002`) + frontend (`:3002`) en Docker con hot-reload (bind mount: editas en el host, uvicorn/next recargan solos).

### 2.5 Migraciones

Las migraciones Alembic se corren **dentro del container** (ground-truth del entorno):

```bash
docker exec luana-dev-vitalia_backend_dev-1 bash -c \
  "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
```

### 2.6 Verificación final

```bash
curl http://127.0.0.1:8002/health    # → {"status": "ok"}
# Frontend: abre http://localhost:3002 en el navegador
docker logs -f luana-dev-vitalia_backend_dev-1   # logs backend en vivo
```

¿Algo falla? Troubleshooting completo (healthcheck de Postgres, hot-reload, build context): **`docs/process/docker-dev.md`**.

Regla operativa: Docker es SOLO runtime. Lint, tests y type-check se corren **nativos en el host** desde el venv raíz (`.venv/bin/pytest`, `npx tsc`, etc.) — nunca dentro del container.

## 3. Levantar el cockpit

```bash
make cockpit-up       # → http://localhost:4002
make cockpit-status   # UP/DOWN + pid
make cockpit-down
```

El **cockpit SDD** (`tools/cockpit/`, binario Go vendored con UI embebida) es el visualizador del proceso. Es **filesystem-as-DB**: no tiene base de datos propia — lee y escribe directamente los `.md`/`.yaml` de este repo (stories, checkpoints, capabilities, releases, gates). Lo que ves en el cockpit ES el estado real del repo, y viceversa.

Tabs (el sidebar lo controla `cockpit.config.yaml::nav`): **roadmap** (releases F0..F8), **evolucion**, **board** (stories por estado — tu vista diaria), **map** (mapa del sistema: zonas/cajas/capabilities), **drift** (gates y desalineaciones código↔docs), **learnings**, **harness**.

## 4. Flujo git (resumen)

**SSoT: `docs/process/git-workflow.md`** — léelo completo el día 1. El modelo es trunk-based:

```
main (único branch permanente)
 ├─ story/{story-id}  ← horas de vida → squash-merge → borrar
 ├─ fix/{slug}        ← bugfix chico → squash-merge → borrar
 └─ tags vX.Y.Z       ← objetivo de release (hoy: branches release/vitalia-vX.Y.Z)
```

**Para ti como dev nuevo: durante el primer mes, TODO va por PR** — creas `story/{id}` (o `fix/{slug}`), pusheas, abres PR; corre el review IA y Chris revisa el review + el diff. Después del primer mes aplican las mismas reglas tiered que a Chris (directo a main solo docs/chores; tier de riesgo — auth, tenant-isolation, migraciones, pagos, comportamiento de agentes — siempre PR + review humano).

Hábitos no negociables: push cada ≤30 min · Conventional Commits (`feat(vitalia): ...`) · stage por pathspec exacto (NUNCA `git add .`/`-A`/`-u`) · squash-merge · prohibido `git push --force`, `git commit --no-verify` y amend de pusheados · `git pull` solo en su forma `--ff-only` sobre branch limpio.

## 5. Flujo de trabajo agentic (`/pm-vitalia` + cockpit)

Así fluye una story de punta a punta. Cada flecha es un skill de Claude Code que tú invocas (o que se auto-encadena):

```
idea ──/pm-vitalia──▶ refining ──/po-ux | /po (+/ux-agentico)──▶ refined
     (intake, backlog,          (spec 01-spec.md con Gherkin
      estados, prioridad)        + wireframes / flujo conversacional)

refined ──/architect──▶ ready ──/dev-team──▶ developing ▶ developed
          (ready package:        (build autónomo TDD,
           03-arch + 04-validators  ticket por ticket,
           + 05-guidelines           gates en verde)
           + 06-tickets)

developed ─[G: Chris verifica LIVE]─[R: reconcile docs⟵realidad]─▶
          ──/auditor──▶ reviewing ──APPROVED──▶ /pm-vitalia merge ▶ done
            (review independiente + gherkin matrix + veredicto)
```

Los **10 estados macro** de una story:

| # | Estado | Quién lo cierra |
|---|---|---|
| 1 | `idea` | Chris + `/pm-vitalia` |
| 2 | `refining` | `/po-ux` / `/po` / `/ux-agentico` |
| 3 | `refined` | `/pm-vitalia` |
| 4 | `ready` | `/architect` (ready package completo) |
| 5 | `developing` | `/dev-team` |
| 6 | `developed` | `/dev-team` (→ gate G: verificación live de Chris) |
| 7 | `reviewing` | `/auditor` (veredicto APPROVED/CHANGES_REQUESTED) |
| 8 | `done` | `/pm-vitalia` (merge) |
| 9 | `parked` | Chris |
| 10 | `dropped` | Chris (terminal) |

El **cockpit muestra todo esto en vivo**: el **board** es el tablero de stories por estado, **drift** muestra los gates y desalineaciones, **map** las capabilities y su hogar en el sistema. Detalle de estados y gates: `CLAUDE.md § SDD Level 3` + `docs/process/story-closure-gate.md`.

**Cómo arranca tu día:**

1. `make cockpit-up` (si no corre) y abre http://localhost:4002 → tab **board**.
2. Mira qué stories están en el estado que te toca trabajar.
3. Abre Claude Code en la raíz del repo y di `/pm-vitalia` (panorama + próxima acción) — o directamente el skill de la fase (`/dev-team toma T-2 de {story}`, `/auditor audita {story}`, etc.).
4. El skill hace el trabajo pesado; tú supervisas, verificas live y ratificas.

**Regla de oro:** los `.md`/`.yaml` de `vitalia/docs/product/` (checkpoint, stories, releases, capabilities) **SON la base de datos del proceso**. No los edites a mano por fuera de los skills/PM — un checkpoint editado a mano desincroniza el board, los gates y el trabajo de los agentes. Lo mismo aplica al revés: lo que el cockpit escribe queda en git.

## 6. Reglas de calidad no negociables

Las rules completas viven en `.claude/rules/` (los agentes las cargan solas; tú también estás sujeto a ellas):

| Regla | 1-liner | Detalle |
|---|---|---|
| TDD obligatorio | Tests PRIMERO (RED→GREEN→REFACTOR); bug fix = regression test que reproduce el bug antes del fix | `.claude/rules/tdd-mandatory.md` |
| Tenant isolation | TODA query filtra `tenant_id` (incluye `get_by_id`); FE usa `useTenantId()`, nunca Clerk org | `.claude/rules/tenant-isolation.md` |
| Migraciones idempotentes | Raw SQL `IF NOT EXISTS`/`IF EXISTS`; nunca `op.create_table()` ni `sa.Enum()` en create_table | `.claude/rules/backend-migrations.md` |
| Spanish neutro | Texto user-facing en español neutro LatAm (tuteo, sin voseo) — solo UI/agentes, no docs internos | `.claude/rules/spanish-text.md` |
| PII / PHI | Rutas con `response_model=` siempre; `sanitize_payload()` en trazas; cero PII real en fixtures | `.claude/rules/pii-sanitisation.md` |
| DoD live-verify | NADA es "done" por suite verde: se ejerce la acción real contra el stack dev + se leen logs + se registra `dod_evidence` | `.claude/rules/definition-of-done-live-verify.md` |
| Anti-duplication | ANTES de crear un archivo/subsistema: grep del engine `core/luana-core-*` — match → consumir por import, nunca duplicar | `.claude/rules/anti-duplication.md` |

Gates mecánicos: pre-commit (23 checks) + pre-push a main (`make ci-parity` marker) + arch fitness tests (`vitalia/backend/tests/architecture/`).

## 7. Mapa de lectura (en este orden)

1. `README.md` (raíz) — qué es el repo, stack, quick start.
2. **Este doc** — setup + flujo.
3. `CLAUDE.md` + `AGENTS.md` (raíz) — el contrato de los agentes: paradigma, estados, rules, comandos. Léelos aunque no seas "el agente": describen cómo se trabaja aquí.
4. `vitalia/CLAUDE.md` — overlay de la marca (dominio salud, HIPAA-lite, agentes).
5. `docs/process/INDEX.md` — índice de reglas de proceso (lifecycle, capability-protocol, story-closure-gate…).
6. Cuando toques código: `.claude/rules/backend-ddd.md` / `frontend-fsd.md` + `vitalia/docs/product/vision.md`.

## 8. Checklist día 1

- [ ] Toolchain instalado: `uv`, node 20 (nvm), `pnpm@9.15.9` (corepack), Docker
- [ ] `uv sync && pnpm install` sin errores
- [ ] `make install-hooks` corrido y verificado (symlink en `.git/hooks/pre-commit`)
- [ ] `vitalia/.env.dev` creado desde el template con valores reales de Chris (y NO commiteado)
- [ ] `make dev-vitalia` arriba: `curl http://127.0.0.1:8002/health` responde ok
- [ ] Migraciones aplicadas (comando `docker exec … alembic upgrade head` de § 2.5)
- [ ] Frontend abre en http://localhost:3002
- [ ] `make cockpit-up` → board visible en http://localhost:4002
- [ ] `docs/process/git-workflow.md` leído — entiendes: story branch → PR → squash-merge
- [ ] Mapa de lectura (§ 7) al menos hasta CLAUDE.md/AGENTS.md
- [ ] Acceso al repo GitHub confirmado + primer branch de prueba `story/onboarding-{tu-nombre}` con un commit trivial vía PR
- [ ] Preguntaste a Chris por la story activa del board para tu primera tarea
