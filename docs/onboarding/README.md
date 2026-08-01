# Onboarding — vitalia-app

> Guía de inicialización para un developer nuevo. Objetivo: al final del día 1 tienes el stack corriendo, los hooks instalados, el cockpit abierto y entiendes cómo fluye una story de idea a producción. Asume que trabajarás **desde Claude Code** (no hace falta ser programador experto — el flujo agentic hace el trabajo pesado; tú operas, supervisas y verificas). Si algo de esta guía no funciona tal cual, repórtalo — este doc es parte del producto.

## 0. Antes de todo — cuentas, git y Claude Code

Esto va ANTES de clonar nada.

### 0.1 GitHub

1. Chris te invita al repo privado (Settings → Collaborators). Acepta la invitación desde el mail o https://github.com/notifications.
2. Configura tu identidad git (aparece en cada commit):
   ```bash
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu-email@ejemplo.com"
   ```
3. Genera una SSH key y agrégala a GitHub (Settings → SSH and GPG keys → New SSH key):
   ```bash
   ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"   # enter a todo
   cat ~/.ssh/id_ed25519.pub                          # copia esto a GitHub
   ssh -T git@github.com                              # verifica: "Hi {usuario}!"
   ```
4. Clona:
   ```bash
   git clone git@github.com:{org}/vitalia-app.git
   cd vitalia-app
   ```

### 0.2 `gh` CLI (obligatorio — Claude Code opera GitHub con esto)

Tu primer mes TODO va por PR (§ 4), y Claude Code crea/consulta PRs vía `gh`:

```bash
# Debian/Ubuntu: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
sudo apt install gh
gh auth login          # GitHub.com → SSH → browser login
gh auth status         # verifica
```

### 0.3 Claude Code

Necesitas **tu propia cuenta** (suscripción Pro/Max, o API key de Anthropic Console) — no se comparte la de Chris.

```bash
# Instalador nativo (recomendado):
curl -fsSL https://claude.ai/install.sh | bash
# (alternativa: npm install -g @anthropic-ai/claude-code)

claude --version
cd vitalia-app && claude    # primera sesión: sigue el /login
```

**Primera sesión en el repo:** Claude Code pregunta si confías en el folder y en los hooks del proyecto (`.claude/settings.json` trae hooks de sesión/commit propios del harness) → **acepta**. El repo se auto-documenta: Claude carga solo `CLAUDE.md`, `AGENTS.md`, el overlay `vitalia/CLAUDE.md` y las rules de `.claude/rules/` — no necesitas "explicarle" el proyecto.

## 1. Qué es vitalia-app

**Vitalia** es un SaaS multitenant de Salud + Bienestar (HIPAA-lite): clínicas y profesionales gestionan reservas prepagadas, pacientes y seguimiento post-tratamiento, operados por un equipo de trabajadores digitales (Valeria como supervisora + especialistas Lisa · Mateo · Adrián · Lucas · Camila). La arquitectura es un **modular monolith DDD**: el backend FastAPI vive en `vitalia/backend/src/modules/vitalia/{módulo}/{domain,infrastructure,application,api}/` y consume un **engine vendored** de 27 paquetes Python (`core/luana-core-*`) vía Extension SDK — la regla de oro es *consumir el engine por import, nunca duplicarlo*. El frontend es Next.js 16 con arquitectura FSD-Lite (`vitalia/frontend/src/{app,components,features,lib}/`), auth con Clerk y Postgres como base. Todo dato está aislado por `tenant_id` — sin excepciones.

Lo segundo que tienes que saber: el producto **se construye con un flujo agentic**. Chris (y tú) orquestan Claude Code con *skills* especializados (`/pm-vitalia`, `/po-ux`, `/architect`, `/dev-team`, `/auditor`) que refinan, diseñan, implementan con TDD y auditan cada story. Los `.md`/`.yaml` bajo `vitalia/docs/product/` son la base de datos de ese proceso, y el **cockpit** (un visualizador local) la muestra en vivo. Tu trabajo no es solo escribir código: es operar y supervisar ese pipeline.

## 2. Setup local paso a paso

Requisitos previos: **Linux** (los scripts usan GNU coreutils — `stat -c`, `setsid`; en macOS varios rompen, avisa si es tu caso), `git`, `make`, `curl`, Docker + Docker Compose v2.

### 2.1 Toolchain

```bash
# Utilidades base (make suele venir; jq/unzip los usan scripts de auditoría E2E)
sudo apt install -y make curl jq unzip

# Docker: tu usuario DEBE estar en el grupo docker (si no, TODO docker falla con permission denied)
sudo usermod -aG docker $USER
# → cierra sesión y vuelve a entrar (o `newgrp docker`). Verifica: docker ps

# Python: uv (gestiona el venv del workspace, Python 3.12)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node 20 vía nvm + pnpm 9.15.9 vía corepack
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install 20
corepack enable && corepack prepare pnpm@9.15.9 --activate

# Google Chrome estable — lo usa la verificación live (gate DoD #37, ver § 6)
# https://www.google.com/chrome/ → .deb → sudo apt install ./google-chrome-stable_*.deb
```

### 2.2 Dependencias + hooks (OBLIGATORIO)

```bash
cd vitalia-app   # raíz del repo
uv sync              # crea .venv/ en la RAÍZ del workspace (27 paquetes core editable)
pnpm install         # workspace pnpm (frontend + paquetes @luana/*)
make install-hooks   # ← OBLIGATORIO: sin hooks no hay gates de calidad

# Playwright: los browsers los baja pnpm, pero las libs de sistema NO — instálalas:
cd vitalia/frontend && npx playwright install --with-deps && cd ../..
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

Pide a Chris los valores reales — son **tres bloques**, no solo Clerk:
1. **Clerk** (claves `pk_test_`/`sk_test_` + issuer + webhook secret).
2. **LLM** (`LITELLM_MASTER_KEY` — mismo valor que el proxy de § 2.4; los `AI_MODEL_*`/`AI_PROVIDER_*` ya vienen correctos en el template).
3. **Live-verify/E2E** (`DEV_APP_TEST_*`, `CLERK_TESTING_TOKEN_VITALIA` — ver § 6).

**NUNCA se commitea `.env.dev`** ni ningún `.env*` — el pre-commit y la política de git lo prohíben.

### 2.4 Proxy LLM (LiteLLM) — sin esto los agentes IA no responden

Todas las llamadas LLM del backend (copilot, sales_agent, extracción) pasan por **un proxy LiteLLM** (Chinese-first: DeepSeek + Kimi; OpenAI solo embeddings). El proxy es un container standalone — **NO lo levanta `make dev-vitalia`**:

```bash
cp deploy/litellm/.env.example deploy/litellm/.env   # rellena las 4 keys (pide a Chris)
make litellm-up                                      # → :4000 · verifica: make litellm-status
```

El stack arranca sin él, pero cualquier feature con IA falla al conectar. Si un agente "no responde", primer chequeo: `make litellm-status`.

### 2.5 Levantar el stack dev

```bash
make dev-vitalia
```

Levanta Postgres (`127.0.0.1:5435`) + backend (`:8002`) + frontend (`:3002`) en Docker con hot-reload (bind mount: editas en el host, uvicorn/next recargan solos).

### 2.6 Migraciones

Las migraciones Alembic se corren **dentro del container** (ground-truth del entorno):

```bash
docker exec luana-dev-vitalia_backend_dev-1 bash -c \
  "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
```

### 2.7 Verificación final

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

El **cockpit SDD** (`tools/cockpit/`, binario Go vendored con UI embebida — ya viene compilado, no necesitas Go) es el visualizador del proceso. Es **filesystem-as-DB**: no tiene base de datos propia — lee y escribe directamente los `.md`/`.yaml` de este repo (stories, checkpoints, capabilities, releases, gates). Lo que ves en el cockpit ES el estado real del repo, y viceversa.

Tabs (el sidebar lo controla `cockpit.config.yaml::nav`): **roadmap** (releases F0..F8), **evolucion**, **board** (stories por estado — tu vista diaria), **map** (mapa del sistema: zonas/cajas/capabilities), **drift** (gates y desalineaciones código↔docs), **learnings**, **harness**.

## 4. Flujo git (resumen)

**SSoT: `docs/process/git-workflow.md`** — léelo completo el día 1. El modelo es trunk-based:

```
main (único branch permanente)
 ├─ story/{story-id}  ← horas de vida → squash-merge → borrar
 ├─ fix/{slug}        ← bugfix chico → squash-merge → borrar
 └─ tags vX.Y.Z       ← objetivo de release (hoy: branches release/vitalia-vX.Y.Z)
```

**Para ti como dev nuevo: durante el primer mes, TODO va por PR** — creas `story/{id}` (o `fix/{slug}`), pusheas, abres PR (Claude Code lo hace con `gh pr create`); corre el review IA y Chris revisa el review + el diff. Después del primer mes aplican las mismas reglas tiered que a Chris (directo a main solo docs/chores; tier de riesgo — auth, tenant-isolation, migraciones, pagos, comportamiento de agentes — siempre PR + review humano).

Hábitos no negociables: push cada ≤30 min · Conventional Commits (`feat(vitalia): ...`) · stage por pathspec exacto (NUNCA `git add .`/`-A`/`-u`) · squash-merge · prohibido `git push --force`, `git commit --no-verify` y amend de pusheados · `git pull` solo en su forma `--ff-only` sobre branch limpio.

### 4.1 Convivencia entre devs (para no pisarse)

Con 2+ personas sobre el mismo trunk:

- **WIP cap por módulo:** máximo **1 story** en `developing`/`developed`/`reviewing` por módulo de código. Antes de arrancar, mira el **board** del cockpit — si el módulo ya tiene una story en vuelo, NO arranques otra ahí (elige otro módulo o espera).
- **Antes de crear tu branch:** `git pull --ff-only` sobre `main` limpio. Si el ff falla → STOP y reporta (nunca pull-merge).
- **Scope del branch = una story = (idealmente) un módulo.** No toques archivos de módulos ajenos "de paso" — eso es lo que genera conflictos.
- **Merges de story a `done` los hace SOLO `/pm-vitalia`** (Fase F del story closure gate) — ni tú ni Claude mergean una story por su cuenta. El gate G (verificación live) lo firma **Chris siempre**.
- El stack Docker usa un project name compartido (`luana-dev`) → **1 stack por máquina**; cada dev corre el suyo en su propia máquina.

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
2. Mira qué stories están en el estado que te toca trabajar (y qué módulos están ocupados — § 4.1).
3. Abre Claude Code en la raíz del repo y di `/pm-vitalia` (panorama + próxima acción) — o directamente el skill de la fase (`/dev-team toma T-2 de {story}`, `/auditor audita {story}`, etc.).
4. El skill hace el trabajo pesado; tú supervisas, verificas live y ratificas.

**Regla de oro:** los `.md`/`.yaml` de `vitalia/docs/product/` (checkpoint, stories, releases, capabilities) **SON la base de datos del proceso**. No los edites a mano por fuera de los skills/PM — un checkpoint editado a mano desincroniza el board, los gates y el trabajo de los agentes. Lo mismo aplica al revés: lo que el cockpit escribe queda en git.

## 6. Verificación live (DoD — regla #37)

**NADA es "done" por suite verde.** Cada story con UI o endpoint se cierra **ejerciendo la acción real** (sobre todo writes: POST/PATCH/PUT/DELETE) contra el stack corriendo, leyendo logs y registrando `dod_evidence`. Runbook completo: `vitalia/docs/domains/dev-app/live-verification.md`.

Para ti como dev nuevo:

- **Tu modo default es `localhost:3002`** — es verificación válida (se anota en `dod_evidence` que faltó el dominio público).
- **El túnel `dev-app.vitalialat.com` es de Chris** (1 túnel = 1 máquina). NUNCA copies `.credentials/dev-tunnel.json` a tu máquina (réplicas HA → routing aleatorio entre ambos stacks) y NUNCA corras `scripts/cloudflared-setup.sh --recreate` (destruye el túnel de Chris). Si más adelante necesitas dominio público propio, se te provisiona un subdominio aparte — pídelo.
- Herramientas: **Chrome DevTools MCP** (skill `chrome-devtools-verify`; requiere Chrome de § 2.1 + registrarlo una vez: `claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest` + sesión Clerk: `make lane-auth-vitalia`) y **Playwright autenticado** (skill `playwright-expert`; preflight: `bash scripts/e2e-preflight.sh`).

## 7. Personas + evals de agentes

Los agentes IA (sales_agent, copilot) se prueban con **personas simuladas** (pacientes/leads sintéticos con dialecto, objeciones y objetivos) contra **goldens** por vertical:

- Librería de personas: `docs/specs/personas/archetype-aware/` (29 activas) + rubrics LLM-as-judge en `docs/specs/rubrics/`.
- Suites que corren hoy (deterministic, sin LLM por default):
  ```bash
  cd vitalia/backend && ../../.venv/bin/pytest tests/agentic_evals/ -v
  # juez LLM real opt-in: RUN_LLM_JUDGE=1 (usa el proxy de § 2.4)
  ```
- `apps/client-simulator/` (conversaciones IA↔IA completas contra un agente vivo) está **dormant** — rescatado del repo origen, pendiente de integración. No lo uses todavía; si una story lo necesita, es trabajo a agendar con `/pm-vitalia`.

Regla PII: los fixtures de eval son **synthetic-first** — cero datos reales (emails `@example.com`, teléfonos `+99`). El pre-commit lo escanea.

## 8. Reglas de calidad no negociables

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

## 9. Mapa de lectura (en este orden)

1. `README.md` (raíz) — qué es el repo, stack, quick start.
2. **Este doc** — setup + flujo.
3. `CLAUDE.md` + `AGENTS.md` (raíz) — el contrato de los agentes: paradigma, estados, rules, comandos. Léelos aunque no seas "el agente": describen cómo se trabaja aquí.
4. `vitalia/CLAUDE.md` — overlay de la marca (dominio salud, HIPAA-lite, agentes).
5. `docs/process/git-workflow.md` — flujo git completo (trunk-based, PRs, releases).
6. `docs/process/INDEX.md` — índice de reglas de proceso (lifecycle, capability-protocol, story-closure-gate…).
7. Cuando toques código: `.claude/rules/backend-ddd.md` / `frontend-fsd.md` + `vitalia/docs/product/vision.md`.

## 10. Checklist día 1

**Cuentas + acceso (§ 0):**
- [ ] Invitación GitHub aceptada · `git config user.name/email` · SSH key agregada · repo clonado
- [ ] `gh auth status` OK
- [ ] Claude Code instalado con TU cuenta (`claude --version` + login) · primera sesión en el repo con trust aceptado

**Toolchain + stack (§ 2):**
- [ ] `make`, `jq`, `unzip`, Chrome instalados · usuario en grupo `docker` (`docker ps` sin sudo)
- [ ] `uv sync && pnpm install` sin errores · `npx playwright install --with-deps` corrido
- [ ] `make install-hooks` corrido y verificado (symlink en `.git/hooks/pre-commit`)
- [ ] `vitalia/.env.dev` creado con los 3 bloques de valores reales de Chris (y NO commiteado)
- [ ] `deploy/litellm/.env` creado + `make litellm-up` → `make litellm-status` OK
- [ ] `make dev-vitalia` arriba: `curl http://127.0.0.1:8002/health` responde ok
- [ ] Migraciones aplicadas (comando `docker exec … alembic upgrade head` de § 2.6)
- [ ] Frontend abre en http://localhost:3002
- [ ] `make cockpit-up` → board visible en http://localhost:4002

**Proceso (§ 4-7):**
- [ ] `docs/process/git-workflow.md` leído — entiendes: story branch → PR → squash-merge · § 4.1 convivencia
- [ ] Runbook live-verify leído (`vitalia/docs/domains/dev-app/live-verification.md`) — entiendes: localhost es tu default, el túnel NO se comparte
- [ ] Mapa de lectura (§ 9) al menos hasta CLAUDE.md/AGENTS.md
- [ ] Primer branch de prueba `story/onboarding-{tu-nombre}` con un commit trivial vía PR (Claude Code te guía: `gh pr create`)
- [ ] Preguntaste a Chris por la story activa del board para tu primera tarea
