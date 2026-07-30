---
doc_type: architecture-design            # SSoT vivo del diseño (NO una user-story)
title: Late-bound saga runtime — diseño técnico (planner dinámico + plan-como-dato + compensaciones)
home: docs/architecture/luana-platform/
status: design-ready                      # diseño cementado · build = user-story futura (precondición: piso de acciones live)
package: core/luana-core-flows (extiende L1) · core/luana-core-copilot (planner) · core/luana-core-extension-sdk (EP)
depends_on_l1: migrated (proposal 2026-06-02-durable-flows-engine)
adr: ADR-015-late-bound-saga-runtime (decisión) · ADR-013 D2 (flujo durable 1ª clase)
supersedes: durable-flows-L2-design.md   # dirección estática FlowCompiler/FlowDefinition
last_modified: 2026-06-16
---

# Late-bound saga runtime — diseño técnico

> **★ Qué es esto.** El SSoT del que arranca la próxima `/architect` ready-package del **motor de flujos
> durables dinámicos** (late-bound saga). Reemplaza la dirección estática de `durable-flows-L2-design.md`.
> **NO se construye todavía** — precondición: ≥2 acciones de un dominio sólidas + live (ver § Build-readiness).
> Reusa **L1** (`make_durable_checkpointer`, migrated) intacto como substrate de suspend/replay.

## 0. Tesis en una frase

El dueño le habla a la supervisora (Valeria/Luana); un **planner LLM** compone al vuelo una **saga**
(plan multi-paso como dato) sobre los **tools** disponibles; un **runtime durable** la ejecuta paso a
paso, la **suspende a disco** en cada espera (humano/async), y la **lleva a término sola** — con
**compensaciones** (undo) y **contingencias** (timeouts/escalación) declaradas en el propio plan.
*"El LLM propone; el runtime dispone."*

---

## 1. Data structures (dominio — `core/luana-core-flows/domain/saga.py`)

Todo el estado vive en el **TypedDict checkpointed** (no hay DB nueva — el ledger ES el estado durable
que L1 ya persiste). Pydantic v2 para los envelopes; el grafo los carga/serializa vía el checkpointer.

```
SagaInstance (el "order" de Chris — unidad durable de 1ª clase)
├── saga_id: str                 # natural key (uuid) — parte del thread_id durable
├── tenant_id: str               # SIEMPRE — segmento del thread_id (aislamiento)
├── owner_agent: str             # empleado dueño (scope) — quién puede correrla
├── goal: str                    # el pedido en lenguaje natural (auditoría + re-planning context)
├── status: pending|running|waiting|compensating|done|failed|cancelled
├── steps: list[SagaStep]        # el ledger — append-only, en orden de ejecución
├── compensation_stack: list[CompensationRef]   # LIFO — empujado por cada side-effect cometido
├── iterations: int              # guard max-iter (anti-loop, igual que grafos L1)
└── created_at / updated_at

SagaStep (un eslabón del ledger)
├── step_id: int
├── intent: Intent               # lo que el LLM propuso (dato, no código)
├── result: StepResult | None    # lo que el runtime obtuvo (checkpointed → replay-safe)
├── state: proposed|committed|executed|failed|compensated
└── trace_ref: str               # → copilot_trace_event

Intent (la propuesta del planner — el corazón del "plan-como-dato")
├── tool_ref: str                # → tool registrado (acción Plano 2). NUNCA código.
├── inputs: dict                 # args del tool (validados contra su schema)
├── idempotency_key: str         # MANDATORY si el tool tiene side-effect (luana-core-idempotency)
├── compensation: CompensationRef | None   # cómo deshacer ESTE intent (backward)
├── contingencies: list[Contingency]       # qué hacer ante riesgos (forward) — la parte "riesgos" de Chris
└── rationale: str               # por qué el planner lo eligió (auditoría)

CompensationRef            # backward / undo
├── tool_ref: str          # tool que revierte (ej. reschedule→reschedule_back, charge→refund)
└── inputs_template: dict   # cómo derivar sus args del result del intent original

Contingency               # forward recovery — declarada en el plan, no improvisada
├── trigger: timeout(duration) | step_failed | external_signal(name) | guardrail_violation
├── action: retry(n) | escalate(to_agent) | alternative(tool_ref) | wait_more | compensate_all
└── note: str             # ej. "paciente no contesta 24h → re-notificar → escalar Valeria → compensar reagenda"

HumanGate                 # interrupt() para aprobación (separación de poderes ADR-013 D6)
├── prompt: str           # "voy a mover 8 citas, ¿confirmás?"
└── on_reject: Contingency

SagaGuardrails (por dominio, registrado por marca)
├── forbidden_tools: list[str]
├── phi_tools: list[str]          # → ComplianceService antes de ejecutar (auditoría obligatoria)
└── human_gate_required: list[str]   # tools que SIEMPRE piden confirmación humana
```

**Por qué el ledger = estado checkpointed (no DB nueva):** L1 ya persiste el `StateGraph` state en
Postgres (`checkpoints` table) replay-safe. El `SagaInstance` ES ese state. *Ponytail:* no construir un
ledger paralelo — el checkpoint L1 + `copilot_trace_event` ya dan durabilidad + auditoría.

---

## 2. El planner loop (runtime — `core/luana-core-copilot/.../saga/`)

Un `StateGraph` LangGraph de **3 nodos** que cicla, persistido por el checkpointer L1:

```
                 ┌──────────────────────────────────────────────┐
                 ▼                                                │
   [PLAN] ──► [GUARD/VALIDATE] ──► [EXECUTE] ──► (¿goal cumplido?)┤
   LLM Kimi    políticas dominio    runtime        │  no ──────────┘
   propone     + validator agent    ejecuta tool   │
   próximo     (SagaLLM: check      + escribe       └─ sí ──► [FINALIZE] → outbox event
   intent      ANTES de cometer)    result al
   (o "done")                       ledger
```

1. **PLAN** — el LLM (Kimi K2, planner role) recibe `goal` + ledger-hasta-ahora + tools disponibles
   (con sus schemas) y emite **el próximo intent** (structured output) **o** `done`. Un intent a la vez
   (late-bound: el grafo se escribe un edge a la vez), NO el plan completo de antemano. El planner
   **debe** adjuntar `compensation` + `contingencies` al intent (forzado por el schema de salida).
2. **GUARD/VALIDATE** — antes de ejecutar: (a) guardrails de dominio (forbidden/PHI/human-gate);
   (b) **validador independiente** (SagaLLM — un check separado del planner: ¿el intent es factible /
   compliant / no alucinado?). Falla → T0 refuse-with-reframe o re-plan. PHI → `ComplianceService`.
3. **EXECUTE** — escribe el intent al ledger (`committed`) **ANTES** de ejecutar; ejecuta el `tool_ref`
   con guard de idempotencia; escribe `result` (`executed`); empuja `compensation` al stack.
   Side-effect + crash en el medio → replay no re-ejecuta (idempotency key + result checkpointed).
4. **WAIT / HUMAN-GATE** (rama de EXECUTE) — si el tool es async o hay `HumanGate`: `interrupt()` →
   **suspende toda la saga a disco** (0 cómputo) + subscribe al signal/timeout. Llega señal →
   resume desde el checkpoint + re-plan con el nuevo contexto. Timeout → dispara la `Contingency`.
5. **FINALIZE** — publica a `luana-core-events` outbox (coreografía; ningún agente llama a otro
   concretamente). Status → `done`.
6. **Compensación** — si un paso falla sin contingencia forward viable → status `compensating` →
   pop+ejecuta el `compensation_stack` en LIFO → `failed` o `compensated`.

**Determinismo en replay (no negociable para durabilidad):** el output del nodo PLAN (el intent) queda
checkpointed. En replay post-crash, LangGraph restaura desde el último checkpoint — **el LLM NO se
re-invoca** para pasos ya decididos. Solo se llama para el **próximo** intent nuevo. Esto reconcilia
"planner no-determinístico" con "ejecución durable determinística" (el principio que Temporal/LangGraph
exigen). Misma garantía que L1 ya da a los grafos.

---

## 3. Reparto core ↔ marca (la respuesta a "acciones por marca, arquitectura compartida")

| Capa | **COMPARTIDO** (`core/` — el esqueleto único) | **POR MARCA** (Extension SDK) |
|---|---|---|
| Planner | loop + Kimi K2 + structured-output schema del intent | persona/voz (Valeria vs Luana) |
| Runtime durable | suspend/resume/replay = **L1** + LangGraph `interrupt()` | — |
| Ledger + compensation executor (LIFO) | engine | — |
| Validador + guardrail engine | engine | **políticas por dominio** (forbidden/PHI/human-gate) |
| Observabilidad | `copilot_trace_event` + `sanitize_payload` | qué eventos emite cada dominio |
| Idempotencia / outbox | `luana-core-idempotency` / `luana-core-events` | — |
| **Espacio de acciones** | el **contrato** de tool (cómo se declara/invoca) | **los tools concretos** + su `compensation` + `risk_class` |

**Clave (ADR-015 D4):** la marca aporta **tools + compensaciones + guardrails**; el engine aporta el
runtime. El planner es idéntico cross-brand. Liskov 60/40: el saga runtime = interfaz estable (core);
roster + tools + políticas = instancia por marca (extension).

### EP-19 redefinido (Extension SDK)

`durable_flow_register` (L2 estático, nunca construido) → **`saga_tool_register`**: la marca registra
sus tools agénticos con metadata de saga. Borrador (signature exacta = decisión `/architect` al build):

```python
# core/luana-core-extension-sdk/extension_points.py — bump _EP_IDS a range(1, 20), EP-19 en _BACKLOG_EPS
EP-19 saga_tool_register(self, *, tool: AgentToolSpec, mode="append")
#   AgentToolSpec = { tool_ref, input_schema, side_effect: bool, risk_class: phi|reversible|irreversible,
#                     compensation: CompensationRef | None, requires_human_gate: bool, owner_agent }
# dispatch: saga_tools_for(ctx) → filtra por ctx.brand_slug + ctx.owner_agent (scope del empleado)
```

**Decisión: EP nuevo, no ensanchar EP-4** (`copilot_workflow_register`, byte-stable a WorkflowRegistry).
Los tools de saga son transversales a TODOS los empleados (consistente con el rationale original de EP-19).
Nota: si la marca ya registra estos tools para el copilot normal, EP-19 puede **decorar** ese registro
con la metadata de saga (compensation/risk) en vez de duplicarlo — open Q1.

---

## 4. Compensación (undo) vs Contingencia (forward) — el detalle que lo vuelve correcto

La intuición de Chris ("riesgos + acciones a tomar") son **dos cosas distintas**; confundirlas es el bug:

| | **Compensación** | **Contingencia / timeout** |
|---|---|---|
| Dirección | backward (deshacer lo hecho) | forward (seguir por otra rama) |
| Cuándo | un paso posterior falla y hay que revertir lo cometido | un `wait` expira o un paso falla y hay alternativa sin deshacer |
| Estructura | stack LIFO, se ejecuta en orden inverso | policy en el intent: trigger → action |
| Ejemplo Adrián | notify falla → revertir la reagenda | paciente no contesta 24h → re-notificar → escalar → (último recurso) compensar |

Ambas se **declaran en el plan** (el planner las emite con el intent), nunca se improvisan. Un intent
side-effect **sin** `compensation` declarada → el GUARD lo rechaza (invariante: no cometés algo
irreversible sin saber cómo deshacerlo, salvo `risk_class: irreversible` + human-gate explícito).

---

## 5. Ejemplo trabajado — caso Adrián (end-to-end)

> "Mové las citas del Dr. Adrián del jueves 12-jul, avisá a los pacientes, reagendá a cualquier día posterior."

```
goal = ↑ ; owner_agent = valeria·agenda ; tenant = clínica-X
PLAN  → intent#1 list_appointments(doctor=Adrián, date=2026-07-12)   [no side-effect, sin compensación]
EXEC  → result: [appt A, B, C]   (3 citas)
PLAN  → (ve 3 citas) intent#2 find_available_slot(doctor=Adrián, after=2026-07-12)
EXEC  → result: slot S_A
PLAN  → intent#3 reschedule_appointment(appt=A, slot=S_A)
        compensation = reschedule_appointment(appt=A, slot=<original>)        ← undo
        contingencies = [ on step_failed → compensate; ]
GUARD → reschedule ∈ human_gate_required? si la marca lo marcó → interrupt("mover 3 citas, ¿confirmás?")
EXEC  → result ok ; push compensación al stack
PLAN  → intent#4 notify_patient(A, "tu cita se movió a S_A, confirmá")
        contingencies = [ on timeout(24h) → retry(1) → escalate(valeria) → after 48h compensate_all ]
EXEC  → enviado ; tool es async (espera confirmación) → interrupt() → SUSPENDE A DISCO
        ... (0 cómputo; webhook subscription + timer 24h) ...
SIGNAL paciente confirma  → resume → PLAN intent#5 (cita B...) ; loop hasta C
   — o —
TIMEOUT 24h sin respuesta → dispara contingencia: re-notificar → (otra vez) escalate a Valeria →
   Valeria decide (otro human-gate) → si nadie resuelve en 48h → compensate_all (revierte reagendas) +
   evento "reagenda-Adrián-parcial" al outbox + avisar al doctor.
FINALIZE → outbox event "citas-Adrián-reagendadas" ; status done
```

Nota: requiere `list_appointments` / `find_available_slot` / `reschedule_appointment` / `notify_patient`
como **tools sólidos + live** (caps DoD #37). Hoy solo el booking de Valeria·Agenda lo está → de ahí la
precondición (§ Build-readiness).

---

## 6. Observabilidad

Cada nodo del loop emite a `copilot_trace_event` (recorder compartido, sin pane nuevo). Stream `updates`
para la UI live ("Reagenda Adrián: paso 3/8 — esperando confirmación del paciente"). `sanitize_payload`
antes de cualquier trace write (PII/PHI). El ledger (steps + estados) es la fuente de auditoría — todo
side-effect quedó escrito ANTES de ejecutarse.

---

## 7. Open questions para `/architect` (al build — NO resolver acá)

1. **EP-19 ¿decora el registro de tools existente del copilot, o es un registro paralelo?** (evitar duplicar el tool surface).
2. **Planner: structured-output nativo de Kimi K2 vía LiteLLM** ¿soporta el schema del intent (tool-choice + compensación + contingencias en una sola respuesta), o hay que partirlo en 2 llamadas (proponer tool → derivar compensación)?
3. **Validador independiente (SagaLLM):** ¿segundo modelo/llamada, o un guard determinístico basta para v1?** (costo vs seguridad — empezar determinístico, LLM-validator si hace falta).
4. **`compensation_stack` ante compensación que falla** (compensar la compensación): política de dead-letter + escalación humana.
5. **Concurrencia:** ¿una saga por tenant serializa, o N concurrentes? (locks / outbox ordering).
6. **Human-gate UI:** ¿reusa el inbox/copilot chat existente o superficie nueva? (anti-orphan: debe ser reachable).
7. **Límite de auto-extensión:** un goal que requiere un tool inexistente → T3 (construir, humano-en-loop) vs T0 (refuse-with-reframe). ¿Dónde corta v1? (sugerencia: v1 solo compone tools existentes; "crear lo que no existe" = fase posterior).

---

## 8. Validators (deferred — del futuro `04-validators.yaml`)

`v_saga_instance_pydantic` · `v_planner_loop_3nodes` · `v_intent_requires_compensation_when_side_effect` ·
`v_replay_no_llm_reinvoke` (determinismo) · `v_compensation_lifo_order` · `v_contingency_timeout_fires` ·
`v_ep19_saga_tool_register` · `v_guardrail_phi_gate` · `v_suspend_resume_durable` (persist+resume real Postgres, DoD #37).

---

## 9. Build-readiness (la secuencia — gate antes de la user-story)

```
✅ L1 durable runtime (make_durable_checkpointer)            — migrated 2026-06-02
✅ ADR-015 + este diseño                                     — 2026-06-16
⬜ Fix /chat brand-mountable                                 — tanda actual (precede todo)
⬜ ≥2-3 tools de scheduling como caps `live` (DoD #37)       — PRECONDICIÓN del primer saga
⬜ 1er saga HAND-ROLLED (caso Adrián) sobre L1               — UN ejemplo concreto, sin generalizar
⬜ Generalizar saga runtime (este diseño) → user-story       — recién con el ejemplo en mano
```

**No construir el runtime antes del hand-rolled** (mismo principio que "no L2 sin ejemplo" — generalizar
sin un caso observado es el error que ADR-013/outcome ya nombraron dos veces).

## 10. Referencias

- `ADR-015-late-bound-saga-runtime.md` — la decisión (supersede L2 estático).
- `ADR-013-empleados-ia-auto-extension.md` D2 — flujo durable de 1ª clase.
- `docs/core-modules/flows.md` — L1 contract (substrate reusado).
- `durable-flows-L2-design.md` — superseded (dirección estática).
- `docs/product/outcomes/empleados-ia-auto-extension-platform.md` — trabajo derivado + protocolo de retoma.
- SOTA: Late-Bound Sagas (Agentspan abr-2026) · SagaLLM (VLDB 2025) · ALAS (arxiv 2511) · 2026 playbook determinism+replay · Temporal dynamic agents.
