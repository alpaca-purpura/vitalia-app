# HANDOFF — Motor de flujos durables L1 (terminar en sesión fresca)

> **Para:** la próxima conversación (Opus, worktree `~/Proyectos/luana-vitalia`, branch `wip/vitalia`).
> **Objetivo:** cerrar **L1 cero-deuda VERIFICADA** — ninguna marca con stub "AsyncPostgresSaver pending". Construir T-flows-3 + T-flows-4 + T-flows-5 (downstream regression + live-verify DoD #37) → auditor-agentic → /pm-luana close.
> **Origen:** story platform `empleados-ia-auto-extension` (ADR-013 Fase B cornerstone). Autoriza editar `core/`: proposal `docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md` (**state: accepted**).
> **NO construir L2** (FlowCompiler/FlowDefinition/EP-19 = `deferred-next-story`).

---

## 1. Qué YA está hecho (committed + pushed a `wip/vitalia` @ `98006df8`)

| Commit | Qué |
|---|---|
| `e083fb91` | Gobernanza: proposal accepted + outcome + spike + ready-package completo (03-arch + 04-validators + 05-guidelines + 06-tickets + dispatch-plan) |
| `c8551ed7` | **T-flows-1** — scaffold `core/luana-core-flows` (pyproject + paquete + uv workspace member 27→28) |
| `1b2d9ab5` | T-flows-1 result doc |
| `98006df8` | **T-flows-2** — `core/luana-core-flows/src/luana_core_flows/checkpointer/` = `make_durable_checkpointer` (provider) + `build_flow_thread_id`/`build_phi_flow_thread_id`. **13 unit tests GREEN**, lint+format clean. |

`origin/main` intacto. Leé en orden al arrancar: `00-research.md`, `spike-durable-flows.md`, `03-arch.md` + `03-arch-agentic.md` + `03-arch-be.md`, `04-validators.yaml`, `06-tickets.yaml`, la proposal.

## 2. Gotchas que me costaron tiempo (LEÉ ESTO o los repetís)

1. **★ Sub-builders se AÍSLAN en worktree propio brancheado de `main`.** Spawnear `builder-backend`/`builder-agentic` vía Agent tool crea un worktree `…/.claude/worktrees/agent-*` y commitea en una branch `worktree-agent-*` separada de `wip/vitalia` → **rompe el DAG secuencial single-hub** (T-flows-N+1 no ve a T-flows-N). **NO uses sub-builders para este DAG.** Construí **IN-PLACE** vos mismo (sos Opus → R23 OK para agentic production). Si igual spawnás uno, cherry-pickeá sus commits a `wip/vitalia` + `git worktree remove` + borrá la branch (local+remote).
2. **★ Scope gate bloquea `core/` en `wip/vitalia`.** El pre-commit (per-branch scope) rechaza commits que tocan `core/`. Es una platform story sobre el hub vitalia → commitéa con `SCOPE_GATE_SKIP=1 git commit <paths> -m "...\n\nSCOPE_GATE_SKIP: platform engine story (durable-flows) sobre hub wip/vitalia. Autorizado por proposal 2026-06-02-durable-flows-engine (accepted) + flujo excepcional Chris."`. **Commit por pathspec SIEMPRE** (índice compartido single-hub; NUNCA `git add .`/`-A`). Cherry-pick NO dispara el hook.
3. **★ Venv compartido entre worktrees.** `${WS}/.venv` es uno solo; `uv sync` desde vitalia repunta los editable installs a paths vitalia. Corré `cd ${WS} && uv sync` desde el worktree vitalia ANTES de construir/testear.
4. **★ psycopg sin libpq nativo.** `import langgraph.checkpoint.postgres` falla nativo (`no pq wrapper available`). El provider ya usa **import diferido** (módulo importable; unit tests mockean vía `sys.modules`). Para integración + live-verify NATIVO necesitás `${WS}/.venv/bin/pip install "psycopg[binary]"` (o agregar `psycopg[binary]` al pyproject del flows pkg) **O** ejercer dentro del contenedor `luana-dev-vitalia_backend_dev-1` (ya tiene libpq).
5. **table_prefix NO existe** en langgraph-checkpoint-postgres 3.1.0 (nombres de tabla fijos). Aislamiento = **DB-por-marca** (cada marca su Postgres vía `postgres_dsn`) + tenant en `thread_id`. El provider ya refleja esto (sin param table_prefix). No reintroducir.
6. **comunify dev-app** tiene un bug conocido de migración (tabla `tenants` faltante — ver MEMORY `dev-app-test-creds`). El **live-verify se hace en VITALIA** (wizard_onboarding); comunify se cubre con downstream regression (suite verde), no necesariamente live.

## 3. Trabajo restante (DAG)

### T-flows-3 — Wire 5 grafos + DELETE mirror (surface agentic, in-place)

**Realidad mapeada (NO es un swap trivial):** `build_production_checkpointer` es **dead code** (definido + exportado en `wizard_checkpoint_config.py`, nunca llamado). La durabilidad de prod nunca se cableó. Sitios de construcción reales del checkpointer:

- **vitalia lucas:** `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/__init__.py:~87-91` construye `LucasOrchestratorService(..., checkpointer=_MemorySaver())`. → Volver el factory **async** + construir `make_durable_checkpointer(postgres_dsn=..., encryption_key=<LANGGRAPH_AES_KEY vitalia PHI>)` + propagar al caller (cron job `agentic/lucas/cron/daily_analysis_job.py`). Usar `build_phi_flow_thread_id` (lucas toca PHI).
- **vitalia wizard:** `copilot/application/services/wizard_orchestrator_service.py` (recibe checkpointer por DI) + `copilot/workflows/cron_handler.py`. El checkpointer durable se construye en el **lifespan del worker ARQ** que invoca los `@register_cron_handler` handlers → cablear ahí. `build_flow_thread_id(flow_id="vitalia.wizard", ...)`.
- **vitalia treatment:** `copilot/workflows/cron_handler.py` (`@register_cron_handler("vitalia.treatment_followup.tick")`). Mismo worker ARQ lifespan.
- **comunify community + cohort:** `comunify/backend/src/modules/comunify/copilot/workflows/cron_handler.py` (handlers `community_engagement.drift_check` + cohort) — su worker ARQ lifespan. `encryption_key=None` (comunify no-PHI).

**DELETE (anti-dup, validator `v_no_brand_mirror` exige 0 matches `build_production_checkpointer` en src):**
- `vitalia/.../copilot/workflows/wizard_checkpoint_config.py` (`build_production_checkpointer` + `WIZARD_CHECKPOINT_TABLE_PREFIX` + `CheckpointerProtocol`).
- Limpiar `copilot/workflows/__init__.py` (re-exports `WIZARD_CHECKPOINT_TABLE_PREFIX`, `CheckpointerProtocol`, `WizardCheckpointerProtocol`, import de `wizard_checkpoint_config`). Si algún módulo aún importa `CheckpointerProtocol` → re-exportar desde un alias mínimo o tipar con `langgraph.checkpoint.base.BaseCheckpointSaver`. Hay un `CheckpointerProtocol` propio en `lucas/workflows/lucas_daily_analysis_graph.py:142` (ese es de lucas, evaluá si se unifica o se deja).
- `+ luana-core-flows` en `vitalia/backend/pyproject.toml` y `comunify/backend/pyproject.toml` (dep).
- **NO tocar** las 5 firmas/topología `build_*_graph` (ya aceptan `checkpointer` por DI). NO tocar `agent_state_checkpoints` (tabla sales_agent, protegida/ortogonal).

### T-flows-4 — Migraciones checkpoint (surface backend, in-place)
- `vitalia/backend/alembic/versions/037_vitalia_durable_flow_checkpoints.py` + `comunify/backend/alembic/versions/002_comunify_durable_flow_checkpoints.py`. Idempotentes (`IF NOT EXISTS`). LangGraph `AsyncPostgresSaver.setup()` OWNS la DDL de sus tablas internas → la migración es **prereq idempotente** (schema/grants si hace falta), no recrea las tablas internas de LangGraph. Validador `v_migration_idempotent`: `alembic upgrade head` dos veces sin error.

### T-flows-5 — Downstream regression + live-verify DoD #37 (surface agentic, in-place)
- **Downstream (R3):** `v_downstream_vitalia` (`cd vitalia/backend && ${WS}/.venv/bin/pytest tests/unit/modules/vitalia/copilot/workflows/ tests/unit/modules/vitalia/agentic/lucas/ tests/architecture/ -x -q`) + `v_downstream_comunify` (`cd comunify/backend && ${WS}/.venv/bin/pytest tests/modules/comunify/copilot/ tests/architecture/ -x -q`) → VERDES con el paquete instalado. Tests existentes inyectan InMemorySaver directo → no deberían romperse (provider es prod-only); composition-root tests se actualizan revisando diff (no mecánico).
- **Live-verify (DoD #37, el gate honesto):** `make dev-vitalia` (BE 8002) → ejercer el wizard_onboarding durable real (Chrome MCP o invocación scripteada) → **`psql` confirma filas de checkpoint en Postgres** (NO MemorySaver) → reiniciar el backend → **resume desde el checkpoint persistido**. Registrar `dod_evidence` en `07-merge.md § Verificación live` + checkpoint. `psycopg[binary]` o correr dentro del contenedor.
- `v_replay_safety`: test integración (vitalia wizard) compila con el checkpointer durable, avanza ≥1 checkpoint, re-invoca mismo thread_id → resume.

### Cierre (/pm-luana)
- proposal `accepted → migrated` + `core/luana-core-flows/CHANGELOG.md` + entry en `docs/core-modules/`.
- Borrar comentarios "package install pending" / "D10" residuales en vitalia+comunify (confirmar 0 con grep).
- `07-merge.md` (5 secciones + dod_evidence). checkpoint `reviewing → done`. Archive R2 (`git mv` story a `docs/archive/2026/stories/`) en el mismo commit del merge — **OJO:** es story platform (`docs/...`, no brand) → archive path = `docs/archive/2026/stories/empleados-ia-auto-extension/` (NO `{brand}/docs/archive`).
- Actualizar outcome `empleados-ia-auto-extension-platform.md` (1b → DONE) + MEMORY pointer `luana-empleados-ia-vision`.

## 4. Validators (SSoT: `04-validators.yaml`)
Baseline: `v_lint_flows_pkg`, `v_lint_brands`, `v_workspace_members`, `v_unit_checkpointer_provider`, `v_unit_thread_id` (ya verdes salvo brands tras wiring). Restantes: `v_no_brand_mirror`, `v_no_factory_test_mock`, `v_migration_idempotent`, `v_setup_idempotent` (integration), `v_replay_safety` (integration), `v_downstream_vitalia`, `v_downstream_comunify`, `v_live_verify_durable_persist`.

## 5. Reglas vigentes a respetar
`tenant-isolation` + `hipaa-lite` (vitalia: EncryptedSerializer en checkpoints PHI + dual-filter en thread_id) · `anti-duplication` (mirror DELETE es el punto) · `backend-migrations` (idempotente) · `auditor-downstream-regression` (engine edit → proposal accepted ✓ + downstream ∀ brand) · `definition-of-done-live-verify` #37 (sin live-verify ejercido + dod_evidence NO hay `done`) · `tdd-mandatory` · `git-safety`/`parallel-safety` (pathspec, SCOPE_GATE_SKIP doc, no `git add .`, no pull/force).
