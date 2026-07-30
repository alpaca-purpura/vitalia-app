---
doc_type: architecture-design            # SSoT vivo del diseño L2 (NO una user-story)
title: Durable flows engine — L2 design (FlowCompiler / FlowDefinition / EP-19)
home: docs/architecture/luana-platform/
status: SUPERSEDED                        # dirección estática reemplazada por late-bound saga (ADR-015 · 2026-06-16)
superseded_by: docs/architecture/luana-platform/saga-runtime-design.md
package: core/luana-core-flows
depends_on_l1: migrated (proposal 2026-06-02-durable-flows-engine)
adr: ADR-013-empleados-ia-auto-extension (D2 — flujo durable de 1ª clase)
graduated_from: docs/archive/2026/stories/empleados-ia-auto-extension/03-arch.md § L2   # story archivada 2026-06-02
last_modified: 2026-06-16
---

# Durable flows engine — L2 design (⛔ SUPERSEDED)

> **⛔ SUPERSEDED (2026-06-16 · ADR-015).** Este diseño asumía **flujos pre-declarados estáticos**
> (`FlowDefinition` declarativo por marca + `FlowCompiler`). Chris + el estado del arte (junio 2026)
> ratificaron el modelo **dinámico** (*late-bound saga*: planner LLM compone el plan al vuelo sobre
> tools, plan-como-dato, compensaciones). El `FlowCompiler` declarativo **NO se construye**. EP-19 se
> **redefine** (de `durable_flow_register` → `saga_tool_register`). **SSoT vigente:**
> `docs/architecture/luana-platform/saga-runtime-design.md`. **L1 sigue intacto** (substrate durable
> reusado por el saga runtime). Este doc se conserva por historia + para entender qué se descartó y por qué.

> **★ Graduación SSoT (2026-06-02).** El diseño L2 nació como `§ L2` del `03-arch.md` de la story
> `empleados-ia-auto-extension`. Al archivar la story (una user-story no debe ser SSoT), el diseño se
> graduó a este doc. L1 (el provider durable + wiring de 5 grafos) está **migrated + live-verified**
> (ver `docs/core-modules/flows.md` + `CHANGELOG.md`).

## Contexto

L1 entregó el **runtime durable** (`make_durable_checkpointer` + `build_flow_thread_id`) que hace que
los flujos multi-paso sobrevivan reinicios vía Postgres. L2 entrega el **compositor declarativo**: un
empleado-IA (domain owner) declara un flujo de N nodos sobre acciones EXISTENTES (Plano 2), y el
`FlowCompiler` lo convierte en un `StateGraph` durable, replay-safe, con outbox final. Cornerstone de
ADR-013 D2.

## L2.1 — `FlowDefinition` (Pydantic declarativo, `core/luana-core-flows/domain/`)

Envelope declarativo brand-agnostic:

```
FlowDefinition (Pydantic v2, ConfigDict, brand-agnostic)
├── flow_id: str                  # natural key (slug)
├── version: int                  # bump → new def; in-flight instances keep their compiled version
├── owner_agent: str              # owning employee (ADR-013 D4 ownership)
├── tenant_scoped: Literal[True]  # ALWAYS — every instance carries tenant_id in thread_id
├── trigger: FlowTrigger          # kind: event|schedule|manual|signal; event_name → subscribes luana-core-events outbox
├── nodes: list[FlowNode]         # the DAG
│     ├── node_id, action_ref (→ Plano-2 registered action), inputs (state→action JSONPath map)
│     ├── on_success / on_failure (node_id | retry | END)
│     └── idempotency_key_template: str  # MANDATORY if action has side-effect (replay-safe via luana-core-idempotency)
├── waits: list[Wait]             # step.sleep equivalent → interrupt + resume by schedule/signal
├── human_gate: HumanGate | None  # interrupt() for T3/approval (ADR-013 separation of powers)
└── guardrails: FlowGuardrails    # compliance_gate (PHI → ComplianceService), forbidden_actions
```

## L2.2 — `FlowCompiler.compile(flow_def) -> CompiledGraph`

1. Build a `StateGraph`: cada `FlowNode` → async node que invoca `action_ref` (resuelto contra el registry de acciones del domain owner).
2. Envolver nodos side-effect con guard de `luana-core-idempotency` (key = `idempotency_key_template` renderizado) → replay-safe (LangGraph re-ejecuta nodos post-checkpoint).
3. `compile(checkpointer=make_durable_checkpointer(...))` (consume el provider **L1, ya migrated**). `thread_id = build_flow_thread_id(flow_id, tenant_id, instance_id)`.
4. Nodo final publica a `luana-core-events` outbox (coreografía — ningún agente llama a otro concretamente; ADR-013 D3/D4).
5. State (TypedDict) DEBE incluir `tenant_id: str` + guard `iterations: int` (max-iter).

## L2.3 — EP-19 `durable_flow_register` (Extension SDK)

- `core/luana-core-extension-sdk/extension_points.py`: bump `_EP_IDS = tuple(f"EP-{i}" for i in range(1, 20))`, agregar `EP-19` a `_BACKLOG_EPS` (signature-only v0.1.0), agregar `durable_flow_register(self, *, flow: FlowDefinition, mode="append")` + `durable_flows_for(ctx)` dispatch (filtra por `ctx.brand_slug`).
- **Decisión: EP-19 NUEVO, no ensanchar EP-4.** EP-4 (`copilot_workflow_register`) está acoplado al WorkflowRegistry byte-stable de copilot; los flujos durables son transversales a TODOS los empleados (copilot, sales_agent, lucas, futuros). Un EP nuevo mantiene el boundary limpio (spike §8 Q2).
- Marcas montan `FlowDefinition`s vía `{brand}/.../extensions.py::register_all(registry)`.

## L2.4 — Observabilidad

Cada nodo emite a `copilot_trace_event` (recorder compartido, `luana-core-observability`) — sin pane nuevo. Stream `updates` para UI live ("Auto-liberación de cupos: paso 2/4"). PII vía `sanitize_payload` antes de cualquier trace write.

## Validators (deferred — del 04-validators.yaml § l2_design_validators)

`v_l2_flow_definition_pydantic` · `v_l2_flow_compiler` · `v_l2_ep19` · `v_l2_idempotency_replay`.

## Primer flujo durable real (cuando se construya L2)

Outcome item 2 (story derivada vitalia): traza B — auto-liberación de cupos (ADR-013 / outcome). O3/O5 abiertos.

## Referencias

- L1 (migrated): `docs/core-modules/flows.md` · `core/luana-core-flows/CHANGELOG.md` · proposal `2026-06-02-durable-flows-engine`.
- Spike de decisión (detalle completo, archivado): `docs/archive/2026/stories/empleados-ia-auto-extension/spike-durable-flows.md` (§4 = origen de este diseño).
- ADR-013 D2 · `empleados-ia-research.md` §4.5 (flujo durable de 1ª clase).
