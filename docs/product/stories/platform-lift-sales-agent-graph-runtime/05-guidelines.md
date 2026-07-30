# 05-guidelines.md — platform-lift-sales-agent-graph-runtime (Phase 1)

## Patterns required
- **PYTHONPATH override SIEMPRE** al validar (learning 2026-06-16): `PYTHONPATH=${WS}/core/luana-core-sales-agent/src:${WS}/core/luana-core-platform/src ${WS}/.venv/bin/pytest ...` — el `.venv` symlinkea a main; sin override no ves tus edits.
- **TDD RED→GREEN** por ESC: escribir el arch test que reproduce el muro (RED) ANTES del fix. Para ESC-6 el RED ya está medido (`hasattr(PromptVersion,'tenant_id') == False`).
- **Relationship targets module-qualified** (ESC-4): string con path completo del módulo (`luana_core_sales_agent.infrastructure.models.message_model.MessageModel`), AMBOS lados de un `back_populates`.
- **Path resolution cwd-independiente** (ESC-5): `Path(__file__).resolve().parent / "templates"` para recursos que el paquete ships. NUNCA `Path.cwd()` + path relativo hardcodeado para recursos del paquete.
- **Migraciones idempotentes** (ESC-6 notes): raw SQL `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`. NUNCA `op.create_table()` / `sa.Enum(create_type=True)`.
- `structlog` (no `print`); SQLAlchemy 2.0 `select().where()`; columnas timestamptz `DateTime(timezone=True)`.

## Patterns forbidden
- ❌ Editar código de marca (`{vitalia,nicolify,comunify,lupulo}/**`) en este worktree core — **constraint dura**.
- ❌ Autorear una migración de marca (`*/backend/alembic/versions/**`) acá — la migración ESC-6 la corre cada brand en SU worktree (migration_notes.md).
- ❌ Cambiar comportamiento del agente: `AgentState` TypedDict, contenido de prompts (`prompts/templates/*.j2`), tools, nodes, voz. Es hardening de runtime/persistencia, NO feature. (Si tocás eso = stake-asimétrico agentic → fuera de scope.)
- ❌ Tocar `appointments`/`tenant` relationships en crm.py (fuera de scope ESC-4).
- ❌ Arreglar el sibling bug de copilot (`core/luana-core-platform/.../prompts/base.py:23`) — fuera de scope, va a `/harness-issue`.
- ❌ Cerrar `developed` con downstream regression de alguna marca en rojo (engine compartido).
- ❌ Auto-handoff a `/auditor` (autonomous_mode:false — Chris ratifica).

## ★ Los 3 diffs ya están PROBADOS (architect spike RED→GREEN). Aplicá los exactos de `03-arch.md § TL;DR`. No inventes.

## ESC-4 es UNILATERAL (corrección probada)
Solo `crm.py` (target de `messages` → qualified). **NO tocar `message_model.py:46`** (`"LeadModel"` es único — vitalia no homonyma LeadModel; probado por spike). Qualificar el otro lado = innecesario + acoplamiento inverso.

## Arch tests = código proven en `verified-arch-tests.md` (copy-paste)
- ESC-4 corre en **SUBPROCESO** (import-state determinístico — evita el conftest sintético `AppointmentModel` que vuelve flaky el registry global). NO uses el conftest pesado del paquete para ESC-4.
- TDD: creá el test (RED contra el código actual) ANTES del diff. Verificado que el de ESC-4 RED-failea (returncode 1) sin el fix.

## Files in scope (builder edita SOLO estos)
- `core/luana-core-platform/src/luana_core_platform/infrastructure/models/crm.py` (ESC-4 — SOLO la línea del target de `messages`)
- `core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/prompts/base.py` (ESC-5 — solo `__init__`)
- `core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/models/prompt_version_model.py` (ESC-6 — +columna)
- `core/luana-core-sales-agent/tests/architecture/test_esc{4,5,6}_*.py` + `__init__.py` (NEW — código en verified-arch-tests.md)

## Coupling principle (Chris: alta cohesión / bajo acoplamiento)
- Engine relationship targets → module-qualified string (late-bound, sin import → sin ciclo): el engine declara su target explícito (cohesión↑) sin acoplar imports.
- **NO expandir** el acople platform-kernel → sales-agent (la relación `messages` ya existe; solo se desambigua, no se agranda).
- Engine persistence models → `tenant_id` SIN FK a `tenants` (decouple del schema de platform; igual que MessageModel).

## Files NEVER touched (escalate)
- `{vitalia,nicolify,comunify,lupulo}/**` (cero marca)
- `core/luana-core-sales-agent/.../infrastructure/models/message_model.py` (ESC-4 one-sided — NO tocar)
- `*/backend/alembic/versions/**` (migración = brand-authored)
- `core/luana-core-sales-agent/.../application/**` (comportamiento del agente)
- `core/luana-core-*/.../prompts/templates/**` (contenido de prompts)
- `core/luana-core-platform/.../prompts/base.py` (copilot sibling — fuera de scope → /harness-issue)
- `crm.py` líneas `appointments`/`tenant` (latent finding — fuera de scope)

## must_load_skills (enforceable — builder reporta "Skills consulted" en T-{id}-result.md)
required:
  - id: sales-agent-expert
    when: "todos los tickets (engine sales_agent)"
    purpose: "§3 protected surfaces, anti-patterns, prompt cache, no tocar comportamiento"
  - id: backend-expert
    when: "todos (SQLAlchemy 2.0, DDD, arch fitness)"
    purpose: "relationship/model patterns + currency/master-data N/A acá"
  - id: ".claude/rules/tdd-mandatory.md"
    purpose: "RED→GREEN por ESC"
  - id: ".claude/rules/anti-duplication.md"
    when: "T-ESC4"
    purpose: "no mirror cross-brand; el fix vive en el engine"
  - id: ".claude/rules/auditor-downstream-regression.md"
    when: "T-ESC4 (+ cierre)"
    purpose: "engine compartido → correr suites de las 4 marcas"
  - id: ".claude/rules/backend-migrations.md"
    when: "T-ESC6"
    purpose: "DDL idempotente (validar migration_notes)"

reference_artifacts:
  - "docs/product/stories/platform-lift-sales-agent-graph-runtime/03-arch.md"
  - "docs/product/stories/platform-lift-sales-agent-graph-runtime/04-validators.yaml"
  - "docs/product/stories/platform-lift-sales-agent-graph-runtime/migration_notes.md"
  - "docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md (vía git show wip/vitalia — no en main)"
