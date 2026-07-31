---
proposal_id: 2026-06-02-durable-flows-engine
state: migrated                # proposed | under_review | accepted | rejected | migrated
opened_date: 2026-06-02
opened_by: /pm-luana
ratified_by: Chris             # "confirmá la recomendación y arrancá la story platform del motor" + "L1 completo + L2 diseñado"
ratified_date: 2026-06-02
migrated_date: 2026-06-02       # L1 lifted + wired + verified live (durable persist + resume, both brands)
migrated_commits: [c8551ed7, 98006df8, 88175663, 76f9e55b, 335ed390]   # T-flows-1..5 (wip/vitalia)
migration_note: >
  L1 COMPLETE. core/luana-core-flows shipped (provider make_durable_checkpointer +
  build_flow_thread_id/build_phi_flow_thread_id, 13 unit tests). 5 brand graphs wired to the
  core provider via per-brand durable accessors; brand mirror wizard_checkpoint_config.py DELETED
  (anti-dup satisfied: grep build_production_checkpointer = 0). Idempotent migrations vitalia 037 +
  comunify 002 (LangGraph-owned fixed-name tables via setup()). Downstream regression GREEN (vitalia
  463 + comunify 182). Live-verify (DoD #37): durable persist + resume proven in Postgres — vitalia 3
  rows (vitalia.wizard:*), comunify 8 rows (comunify.community:*). L2 (FlowCompiler/FlowDefinition/EP-19)
  remains design-only (deferred-next-story) — NOT migrated, see 03-arch.md § L2.

# Origen
origin_learnings:
  - docs/archive/2026/stories/empleados-ia-auto-extension/spike-durable-flows.md   # decision spike (ADR-013 cornerstone B) — story archivada 2026-06-02; diseño L2 graduado a docs/architecture/luana-platform/durable-flows-L2-design.md
origin_brands: [vitalia, comunify]   # ambas tienen grafos durables stubbed + factory brand-mirror

# Target
target_package: core/luana-core-flows   # NUEVO paquete (o módulo en luana-core-platform — architect decide en 03-arch)
target_module: src/luana_core_flows/checkpointer/   # provider durable compartido (L1) + flow_compiler/ (L2 diseño)
target_ep: EP-19   # composición de flujos durables (L2 — diseño en esta proposal, build siguiente)

# Impact assessment
semver_bump: minor             # NEW core package + add dep langgraph-checkpoint-postgres (compatible langgraph>=0.2 → SIN bump a 0.4)
breaking_change: false
brands_affected_consumers: [vitalia, comunify]   # los 2 con módulos agentic; nicolify+lupulo esqueletos (heredan al bootstrap)
brands_at_risk_regression: [vitalia, comunify]   # downstream regression OBLIGATORIA en ambos (R3 + auditor-downstream-regression)

# Lift plan
lift_estimated_effort: "L1 esta conversación (flujo excepcional Chris); L2 build = story siguiente"
lift_owner: /dev-team (builder-agentic Opus — surface agentic) + builder-backend (migraciones)
arch_test_downstream_required: true
migration_notes_required: true   # tablas checkpoint por marca (idempotentes)
---

## 1. Patrón a promover

Un **motor de flujos durables brand-agnostic** en `core/`, en 2 capas:

- **L1 — provider de checkpointer durable (un-defer):** factory compartido que construye `AsyncPostgresSaver` (paquete `langgraph-checkpoint-postgres`) con `EncryptedSerializer` para PHI + helper de `thread_id` tenant-scoped + `setup()`. Hoy este factory está **mirroreado por marca** (`vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer` + el equivalente comunify) con import diferido y `RuntimeError("package not installed")` — un mirror cross-brand que `anti-duplication.md` prohíbe. Se lifta a core y las marcas lo consumen vía import.
- **L2 — `FlowCompiler` + `FlowDefinition` + EP-19 (diseño en esta proposal, build siguiente):** compositor declarativo de flujos durables (el cornerstone empleados-IA de ADR-013 D2). Net-new — no existe hoy (verificado: `luana-core-events/outbox` es coreografía de evento único; no hay compositor de flujos).

**Origen story/incident:**
- Spike de decisión: `docs/archive/2026/stories/empleados-ia-auto-extension/spike-durable-flows.md` (recomendación LangGraph durable + Temporal escape + Cloudflare descartado, research date-aware 2026-06-02, ratificada por Chris; story archivada 2026-06-02).
- ADR: `docs/architecture/luana-platform/ADR-013-empleados-ia-auto-extension.md` (D2 flujo durable de 1ª clase).

## 2. Por qué cross-brand

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya implementa (stubbed) | 3 grafos durables (`lucas_daily_analysis`, `wizard_onboarding`, `treatment_followup`) compilan con `checkpointer=` sobre `MemorySaver`; factory brand-local |
| comunify | ya implementa (stubbed) | 2 grafos durables (`community_engagement`, `cohort_enrollment`) idem |
| nicolify | candidato (futuro) | esqueleto — sin módulos agentic hoy; hereda al bootstrap del roster |
| lupulo | candidato (futuro) | placeholder |

El factory de checkpointer + el compositor de flujos son **idénticos conceptualmente cross-brand** → deben vivir en `core/` (un solo engine, ADR-013 invariante).

## 3. Análisis técnico

### Drift map (greps 2026-06-02 — `/pm-luana`)

Deuda concreta ("patrón D10" — `graph.compile(checkpointer=...)` sobre `MemorySaver`, paquete nunca instalado):

```
vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/lucas_daily_analysis_graph.py:503
vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_onboarding_graph.py:323
vitalia/backend/src/modules/vitalia/copilot/workflows/treatment_followup_workflow.py:753
comunify/backend/src/modules/comunify/copilot/workflows/community_engagement_workflow.py:593
comunify/backend/src/modules/comunify/copilot/workflows/cohort_enrollment_workflow.py:913
```

Factory brand-mirror a liftar: `vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer` (+ equivalente comunify). Engine pkgs con `langgraph>=0.2`: copilot, sales-agent, brand-studio. `AsyncPostgresSaver` = 0 imports reales (solo comentarios "production target"). `langgraph-checkpoint-postgres` = NO instalado.

### Generalización

```python
# Brand actual (mirror en vitalia + comunify)
def build_production_checkpointer(*, postgres_dsn: str) -> CheckpointerProtocol:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # deferred
    return AsyncPostgresSaver.from_conn_string(postgres_dsn)

# Propuesta core (luana_core_flows.checkpointer)
def make_durable_checkpointer(
    *, postgres_dsn: str, encryption_key: str | None = None, table_prefix: str = "luana_flows_",
) -> BaseCheckpointSaver:
    # AsyncPostgresSaver + EncryptedSerializer (PHI/HIPAA) + setup() idempotente.
    # thread_id helper: f"{flow_id}:{tenant_id}:{instance_id}" (tenant-scoped, dual-filter HIPAA).
    ...
```

Brand-specific bits (table_prefix, encryption_key per compliance_level) parametrizables vía DI / BrandConfig. Marcas borran su factory mirror y consumen el de core.

### Matiz que baja el riesgo

`langgraph-checkpoint-postgres` es compatible con `langgraph>=0.2` → **L1 NO requiere bump a `langgraph>=0.4`** (eso era nice-to-have para `DeltaChannel`/HITL v0.4, separable a una proposal futura). Reduce el blast radius del downstream regression.

## 4. Decisión + alcance autorizado (esta proposal)

- **L1 (build esta conversación, flujo excepcional ratificado Chris):** lift del provider a `core/` + instalar `langgraph-checkpoint-postgres` + cablear los 5 grafos + migraciones idempotentes (tablas checkpoint por marca) + downstream regression vitalia+comunify + live-verify (DoD #37). Resultado: **cero stub "AsyncPostgresSaver pending" en ninguna marca**.
- **L2 (diseño esta conversación, build siguiente):** ready-package formal del `FlowCompiler`/`FlowDefinition`/EP-19 (03-arch + validators + tickets) listo para construir. NO se buildeará en esta conversación (no se puede live-verificar honestamente un compositor cross-brand en una sesión — DoD #37 prohíbe el falso-done).

## 5. Autorización engine

Esta proposal en `state: accepted` **autoriza a `/dev-team` (builder-agentic + builder-backend) a editar `core/` para L1** (crear `core/luana-core-flows` o el módulo equivalente que el `/architect` decida en `03-arch.md`, + tocar pyproject de los engine pkgs consumidores). El `auditor-downstream-regression` debe encontrar esta proposal `accepted` al revisar el PR (engine edit detection PASS).

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Replay re-ejecuta nodos con side-effect | Envolver nodos side-effect con `luana-core-idempotency` (ya existe); validator de replay-safety en 04-validators |
| Downstream regression rompe vitalia/comunify | Suites agentic completas en ambos brands con el paquete instalado, ANTES de cerrar (R3) |
| PHI en checkpoints (vitalia HIPAA) | `EncryptedSerializer` (`LANGGRAPH_AES_KEY`) + dual-filter tenant en thread_id + sanitize_payload en trazas |
| Nuevo paquete core mal integrado al uv workspace | Registrar member en root pyproject + `uv sync` + arch fitness scaffold |

## 7. Cierre

- Al completar L1 + verificar live → `state: migrated` + actualizar `core/luana-core-flows/CHANGELOG.md` + `docs/core-modules/`.
- L2 build → proposal/story siguiente (referenciar esta como origen).
