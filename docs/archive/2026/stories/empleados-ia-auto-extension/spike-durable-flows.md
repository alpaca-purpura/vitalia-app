<!-- voseo-allowed: doc interno SDD (spike de decisión técnica); términos internos + citas de research, no strings user-facing -->
---
spike_id: durable-flows-engine
story_id: empleados-ia-auto-extension
type: technical-decision-spike
state: decision-doc            # NO ready-package. Alimenta un refined→ready FUTURO.
researcher: /architect (platform)
created: 2026-06-02
research_accessed: 2026-06-02   # date capturada en Step 0 (date -u +%Y-%m-%d)
model_knowledge_cutoff: 2026-01  # Opus 4.8 — todo post-cutoff verificado live vía WebSearch/WebFetch hoy
adr: ADR-013-empleados-ia-auto-extension
outcome: empleados-ia-auto-extension-platform (trabajo derivado #1)
authorization: /pm-luana (Chris ratificó Fase B 2026-06-02)
---

# Spike — Motor de flujos durables brand-agnostic (cornerstone Fase B)

## 1. Resumen ejecutivo + RECOMENDACIÓN

> **RECOMENDACIÓN: LangGraph durable execution (`AsyncPostgresSaver`, paquete `langgraph-checkpoint-postgres`) como motor de flujos durables base, vivido en `core/` y expuesto como EP T2 de composición declarativa.** Es el único candidato que (a) corre nativo en nuestro stack FastAPI async + Postgres, (b) **agrega durabilidad DEBAJO del supervisor LangGraph que YA usamos** (no lo reemplaza — la pregunta del brief), (c) no introduce un cluster/runtime externo (costo operativo cero para solo-operador), (d) respeta multitenancy por `thread_id` tenant-scoped + observabilidad reusando `copilot_trace_event`. **Temporal queda como puerta de escape documentada** (lift futuro vía `/pm-luana`) si un flujo necesita garantías cross-service de días/semanas que el checkpointer no da. **Cloudflare Dynamic Workflows queda DESCARTADO** (TS-only + requiere runtime Cloudflare Workers — incompatible con el backend Python). El riesgo aceptado de LangGraph (los nodos re-ejecutan en resume → deben ser idempotentes/side-effect-aware) se mitiga reusando `core/luana-core-idempotency/` (ya existe) en cada nodo con side-effect.

---

## 2. Estado date-aware de cada candidato (consultado 2026-06-02)

> Disclosure: Opus 4.8 tiene cutoff enero 2026. Cloudflare Workflows V2, Dynamic Workflows y LangGraph v0.4 son posteriores — todos verificados live hoy vía WebSearch + WebFetch de docs canónicas. URLs + fecha de acceso citadas en §7.

### 2.1 · Cloudflare Workflows / Dynamic Workflows
- **GA + V2 (may-2026):** Cloudflare Workflows pasó a GA como motor de durable execution serverless; V2 agrega replay determinístico + 50.000 instancias concurrentes + 300 nuevas/s por cuenta.
- **Dynamic Workflows (may-2026):** librería **MIT** (`@cloudflare/dynamic-workflows`, npm), ~300 líneas de TS, que rutea cada `create()` a código por-tenant vía un "Worker Loader". Steps durables: `step.sleep()`, `step.waitForEvent()`, resumen automático tras eviction del isolate.
- **DISQUALIFIER (verificado en docs):** **TypeScript/JavaScript ONLY** + corre **sobre el runtime de Cloudflare Workers (Dynamic Workers, open beta en Workers Paid)**. "There is no indication it works from external Python/FastAPI backends." Para usarlo tendríamos que portar la capa de flujos a TS y desplegarla en Cloudflare — un segundo runtime, segundo lenguaje, dependencia de plataforma propietaria. Mata el invariante "un solo motor en `core/` Python".
- Pricing (referencia): Workers Paid $5/mes base; billing solo mientras ejecuta. Irrelevante dado el disqualifier.

### 2.2 · Temporal
- **Durable execution maduro (2026):** Workflows + Activities, replay determinístico desde event history, retries de activities, `Continue-As-New`, timeouts, cancelación. SDK Python (`temporalio`) async-first, integra con FastAPI vía worker process separado.
- **Multitenancy:** namespaces (uno por tenant es caro a escala) o single-namespace con `tenant_id` en el `workflow_id` (patrón recomendado a escala). Observabilidad vía signals + queries (consultar estado de un workflow corriendo) + Temporal UI.
- **Costo operativo (verificado, may-2026):** requiere un **cluster Temporal Server separado**. Self-host realista **$2.5-4.5K/mes** + labor ops (K8s + Cassandra); Temporal Cloud desde **~$200/mes** a bajo volumen (On-Demand 500 APS, escala por TRUs). Self-host se vuelve cost-competitive recién a ~30-50M Actions/mes.
- **Veredicto:** sobre-dimensionado para el estado actual (solo-operador, sin cluster, sin flujos durables hoy). Su garantía fuerte (durabilidad cross-service medida en días/años) excede lo que el cornerstone B necesita. **Puerta de escape**, no base.

### 2.3 · LangGraph + durable execution (RECOMENDADO)
- **Durabilidad nativa (LangGraph v0.4, abr-2026 + durable-execution docs):** 3 modos `durability=` (`"exit"` / `"async"` / `"sync"`), checkpointer `AsyncPostgresSaver` (paquete `langgraph-checkpoint-postgres`) = backend de producción recomendado para Postgres + async/FastAPI.
- **Resume:** por `thread_id` (clave primaria del hilo durable). Tras fallo/interrupción, `get_tuple()` repuebla el `StateSnapshot` y re-ejecuta desde el último super-step. **"pending writes are already durable and don't need to be re-run on resume."**
- **Replay semantics (CRÍTICO):** replay = "re-executing steps from a prior checkpoint" — los nodos POST-checkpoint **re-ejecutan** (incl. llamadas LLM e interrupts). ⇒ **los nodos con side-effect deben ser idempotentes** (mitigación: reusar `core/luana-core-idempotency/`).
- **HITL first-class (v0.4):** `interrupt()` + `Command(resume=...)` — pausa/resume para aprobación humana, incluido en `.invoke()` return y stream mode `values` sin `getState()` aparte. Encaja con el "techo de auto-extensión" (T3 humano-en-loop) y con la separación de poderes de ADR-013.
- **Cifrado at-rest:** `EncryptedSerializer.from_pycryptodome_aes()` (`LANGGRAPH_AES_KEY`) — relevante para PHI vitalia (HIPAA).
- **Estado actual en el repo:** `langgraph>=0.2` ya pinneado en `core/luana-core-copilot` + `core/luana-core-sales-agent`; **NO** se usa `AsyncPostgresSaver` hoy (cero checkpointer durable LangGraph). Agregar durabilidad = bump de versión + nuevo paquete `langgraph-checkpoint-postgres`, sin reescribir el supervisor.
- **Patrón híbrido validado (2026):** la industria converge en "LangGraph para razonamiento + Temporal para orquestación durable cross-service". Para flujos intra-tenant single-service (el 95% de nuestro caso B), el checkpointer LangGraph alcanza; Temporal recién cuando hay coordinación cross-service estricta de larga duración.

---

## 3. Matriz de comparación

| Criterio (del brief) | Cloudflare Dyn. Workflows | Temporal | **LangGraph + durable exec (REC)** |
|---|---|---|---|
| Durabilidad per-tenant + replay/resume tras fallo | ✅ (Worker Loader por tenant) | ✅✅ (event-history, days/years) | ✅ (`thread_id` tenant-scoped + `AsyncPostgresSaver`) |
| Estado durable + seguimiento del CONJUNTO (6 props §FLUJO) | ✅ steps/sleep/waitForEvent | ✅✅ signals/queries/UI | ✅ `StateSnapshot` + `get_state_history` + reducers |
| Observabilidad (encaje `copilot_trace_event`) | ❌ runtime/UI ajeno (CF) | 🟡 Temporal UI propia (otro pane) | ✅✅ mismo proceso → reusa recorder + `astream_events` |
| Encaje `luana-core-events` outbox (coreografía default) | 🟡 evento sale del runtime CF | ✅ activity publica al outbox | ✅✅ nodo final del flujo publica al outbox in-process |
| Encaje LangGraph supervisor existente (durabilidad DEBAJO, no reemplazo) | ❌ lo reemplazaría (otro motor) | 🟡 lo envuelve (workflow llama al grafo) | ✅✅ **mismo framework** — agrega `checkpointer=` al grafo |
| Multitenancy + aislamiento (HIPAA vitalia) | 🟡 por tenant code | ✅ namespace/workflow_id | ✅ `thread_id` + filtro tenant + `EncryptedSerializer` PHI |
| SDK Python maturity + fit FastAPI async | ❌ **no Python** | ✅ `temporalio` async | ✅✅ ya en el stack (`langgraph>=0.2`) |
| Managed vs self-host (costo ops solo-operador) | 🟡 managed CF + 2º runtime | ❌ cluster separado $200-4.5K/mes | ✅✅ Postgres que ya corremos, cero infra nueva |
| Compositor DECLARATIVO de flujos (EP T2 sin código end-user) | ✅ steps TS (pero TS) | 🟡 workflows en código Python | ✅ DAG declarativo → compila a StateGraph (ver §4) |
| Techo de auto-extensión (no tocar core sin gate humano) | 🟡 | ✅ (activity allowlist) | ✅ nodos = acciones registradas; net-new nodo = T3 humano |
| **Veredicto** | **DESCARTADO** (TS+runtime ajeno) | **PUERTA DE ESCAPE** (lift futuro) | **✅ BASE RECOMENDADA** |

---

## 4. Boceto del contrato del EP T2 "composición de flujos durables"

> No es código — es el SOBRE declarativo que un dueño de dominio (empleado-IA) usa para declarar un flujo de N nodos sobre **acciones/eventos que YA existen**. El motor (LangGraph + `AsyncPostgresSaver`) le da estado + tracking gratis.

### 4.1 · Forma de la interfaz (qué declara un dueño de dominio)

Un **FlowDefinition** declarativo (Pydantic, brand-agnostic, vive en `core/`):

```
FlowDefinition
├── flow_id: str                  # natural key versionable (slug + version)
├── version: int                  # bump → nueva definición, instancias viejas siguen su versión
├── owner_agent: str              # el empleado dueño (ej. "operar") — ownership por dominio (ADR-013 D4)
├── tenant_scoped: True           # SIEMPRE — toda instancia lleva tenant_id en thread_id
├── trigger:                      # disparador (prop 3 de §FLUJO)
│     kind: event | schedule | manual | signal
│     event_name: str | None      # si event → suscribe al luana-core-events outbox
├── nodes: list[FlowNode]         # el DAG
│     ├── node_id: str
│     ├── action_ref: str         # referencia a UNA acción del Plano 2 (service layer) YA registrada
│     ├── inputs: dict[str, JSONPath]   # mapeo de estado → inputs de la acción
│     ├── on_success: node_id | END
│     ├── on_failure: node_id | retry | END
│     └── idempotency_key_template: str # OBLIGATORIO si la acción tiene side-effect (replay-safe)
├── waits: list[Wait]             # step.sleep equivalente — interrupt + reanudar por schedule/signal
├── human_gate: HumanGate | None  # interrupt() para T3/aprobación (separación de poderes ADR-013)
└── guardrails:                   # techo de auto-extensión
      compliance_gate: bool       # PHI/canal no-encriptado → ComplianceService (HIPAA)
      forbidden_actions: list[str]
```

**Reglas del sobre (qué hace que un flujo sea T2 vs T3):**
- Todos los `action_ref` apuntan a acciones **ya registradas** en el service layer (Plano 2) → **T2** (componer lo existente, sin código). El motor de flujos + compositor declarativo dan estado + tracking gratis.
- Un `action_ref` que NO existe (ej. "lista de espera" inexistente) → ese **nodo es T3** (humano construye la acción, sandbox + live-verify), el resto del flujo sigue T2. (Resolución nodo-por-nodo del DAG, §4.3 research.)
- Net-new tipo de nodo / trigger fuera de los kinds declarados → **T3+** → gate `/pm-luana`.

### 4.2 · Cómo se compila (declarativo → runtime)

`FlowCompiler.compile(flow_def) -> CompiledGraph`:
1. Construye un `StateGraph` LangGraph: cada `FlowNode` = un nodo async que invoca `action_ref` (resuelto contra el registro de acciones del dominio dueño).
2. Envuelve cada nodo con side-effect en un guard de idempotencia (`luana-core-idempotency`, key = `idempotency_key_template` renderizado) → replay-safe (mitigación del riesgo de re-ejecución).
3. `compile(checkpointer=AsyncPostgresSaver(...))` → durabilidad. `thread_id = f"{flow_id}:{tenant_id}:{instance_id}"`.
4. Nodo final publica el resultado al `luana-core-events` outbox (coreografía: otros empleados reaccionan; el flujo NO llama a otro agente concreto — ADR-013 D3/D4).

### 4.3 · Cómo se observa (6ª prop de FLUJO — seguimiento)

- Estado del CONJUNTO: `graph.get_state(config)` → `StateSnapshot` (en qué paso va) + `get_state_history` (timeline) por `thread_id`.
- Trazas: cada nodo emite a **`copilot_trace_event`** (recorder shared de `luana-core-observability`) — NO un pane nuevo. Stream `updates` para UI en vivo ("Auto-liberación de cupos: paso 2/4").
- UX (§12 research): el flujo es un **objeto visible+monitoreable en la pestaña del dueño** ("Operar" muestra el flujo + stats), no magia de fondo.

### 4.4 · Cómo se versiona

- `flow_id` + `version`. Instancias en vuelo siguen su versión compilada (las definiciones viejas se conservan, no se mutan in-place — espejo del patrón `update_state` de LangGraph que crea nuevos checkpoints sin modificar los originales). Bump `version` = nueva definición; migración explícita de instancias vivas si hace falta.
- Tabla de checkpoints declarada: `durable_flow_checkpoints` (gestionada por `AsyncPostgresSaver.setup()`), tenant-filtered.

### 4.5 · Dónde topa el techo

- El compositor solo referencia acciones registradas del **dominio del dueño** (L2 router). No puede componer acciones de otro dominio salvo vía **evento** (DIP) — no internals ajenos.
- `compliance_gate`/`forbidden_actions` + el techo de ADR-013 D6: tocar core invariante (cifrado PHI, contratos cross-brand) NO es declarable como flujo → escala a `/pm-luana`.
- `human_gate` = `interrupt()` para T3 y aprobaciones (el agente pide, el humano concede).

---

## 5. Encaje con lo que YA existe (NO-NEW-LAYER audit)

> Audit cross-module ejecutado (Path B — self-run greps, NO había CONTEXT-BRIEF para este spike). Evidencia abajo.

### Sistemas existentes encontrados

| Sistema | Path | Qué hace HOY | Encaje con el motor de flujos |
|---|---|---|---|
| **Outbox / event bus** | `core/luana-core-events/outbox/` (`dispatcher.py` ARQ 1 tick/s, `OutboxEntry` PENDING→DISPATCHED, `EventBus._dispatch` in-memory) | Coreografía por eventos: 1 evento → 1 dispatch async, con idempotency_key + retry. **SIN estado multi-paso ni replay del CONJUNTO.** | **REUSAR como está** (el 80% coreografía). El motor de flujos cubre el 20% durable/multi-paso; su nodo final **publica al outbox**, no lo reemplaza. |
| **Idempotency** | `core/luana-core-idempotency/` (`redis_store.py`, `decorator.py`, `service.py`) | Dedup de una llamada (Redis, key + TTL). | **REUSAR** para envolver nodos con side-effect → replay-safe (la mitigación del riesgo LangGraph). |
| **LangGraph supervisor** | `core/luana-core-copilot` + `core/luana-core-sales-agent` (`langgraph>=0.2`, StateGraph). `agent_state_checkpoint_model` en sales_agent = estado per-conversación custom, **NO** checkpointer durable LangGraph. | Razonamiento/ruteo de agentes. Cero `AsyncPostgresSaver`. | **EXTEND** — agregar `checkpointer=AsyncPostgresSaver` DEBAJO del mismo framework. NO se reemplaza el supervisor (respuesta directa al brief). |
| **Observability recorder** | `core/luana-core-observability/recording/` (`turn_envelope`, `base_callback_handler`, `sanitize_payload`) + tablas `copilot_trace_event`/`*_llm_call` | Trazas event-sourced + costo + PII sanitization. | **REUSAR** — el motor de flujos emite a `copilot_trace_event` (cero pane nuevo). |
| **Extension SDK** | `core/luana-core-extension-sdk/extension_points.py` (EP-1..18; EP-4 = copilot workflow register, EP-6..18 signature-only) | Registro de extensiones brand. | **EXTEND** — el EP T2 de flujos durables es candidato a **nuevo EP** (o ensanchar EP-4) cuando se promueva; las marcas montan `FlowDefinition`s vía `{brand}/.../extensions.py::register_all(registry)`. |
| **Compliance gates** | `core/luana-core-compliance/` (ComplianceService) | Bloquea PHI en canal no-encriptado. | **REUSAR** en `compliance_gate` del flujo (HIPAA, traza B del research). |

### Decisión por sistema

- **EXTEND (default):** LangGraph (agregar checkpointer durable) + Extension SDK (nuevo EP / ensanchar EP-4) + reuso de outbox/idempotency/observability/compliance.
- **NEW (acotado, justificado):** el **`FlowCompiler` + `FlowDefinition` + registro de flujos** son net-new — no existe hoy un compositor declarativo de flujos durables (verificado: `luana-core-events` es coreografía de evento único; `agent_state_checkpoint_model` es estado per-conversación custom, no durable-flow). Es net-new legítimo, NO un layer paralelo a algo existente. **Vive en `core/`** (brand-agnostic) → su creación requiere `/pm-luana` lift al promoverse a EP.
- **Cross-brand mirror check:** ningún brand tiene un motor de flujos hoy → cero mirror. Debe nacer en `core/` desde el primer commit (no mirror per-brand).

### Greps de evidencia (ejecutados 2026-06-02)

```
core/luana-core-events/outbox/{dispatcher.py,domain/outbox_entry.py}  → coreografía evento-único, sin replay multi-paso
core/luana-core-idempotency/{redis_store,decorator,service}.py        → dedup llamada única
core/luana-core-copilot + core/luana-core-sales-agent  langgraph>=0.2  → StateGraph, CERO AsyncPostgresSaver
grep AsyncPostgresSaver|MemorySaver|PostgresSaver core/luana-core-{copilot,sales-agent}/src  → 0 matches (no durable checkpointer hoy)
core/luana-core-extension-sdk/extension_points.py  → EP-1..18 (EP-4 copilot workflow; EP-6..18 signature-only)
```

---

## 6. Riesgos + mitigaciones + qué queda para el ready-package siguiente

### Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| **Re-ejecución de nodos en replay** (LangGraph re-ejecuta nodos post-checkpoint, incl. side-effects + LLM) | Alta | Envolver cada nodo con side-effect en `luana-core-idempotency` (key = `idempotency_key_template`). El `04-validators` del ready-package futuro debe exigir test de replay-safety por nodo. |
| **Checkpoint bloat** (estado durable crece) | Media | `DeltaChannel` (beta, `langgraph>=1.2`) para canales append-heavy; retención por worker (espejo de la del outbox). Evaluar versión LangGraph al promover. |
| **Techo mal puesto** (flujo declara algo que toca core invariante) | Alta (HIPAA) | `compliance_gate` + `forbidden_actions` + gate `/pm-luana` para net-new node types (T3+). Auditor categoría Connectivity + paradigma. |
| **Acoplamiento accidental** (flujo de un dominio invoca internals de otro) | Media | Contrato: `action_ref` solo del dominio dueño; cross-dominio SOLO vía evento (outbox). Arch fitness test futuro. |
| **Lock-in si después se necesita Temporal** | Baja | El `FlowDefinition` es declarativo y agnóstico del motor; el `FlowCompiler` es el único adaptador. Migrar a Temporal = reimplementar el compiler, no las definiciones. Puerta de escape limpia. |
| **PHI en checkpoints (vitalia HIPAA)** | Alta | `EncryptedSerializer` (`LANGGRAPH_AES_KEY`) + `sanitize_payload` antes de cualquier traza + filtro tenant en `durable_flow_checkpoints`. |

### Qué quedaría para el ready-package siguiente (alto nivel — sin tickets)

El refined→ready FUTURO (un `/architect` formal, NO este spike) tendría que cubrir, en este orden:

1. **Story platform: "Motor de flujos durables (EP T2)"** — `03-arch` formal del `FlowDefinition` + `FlowCompiler` + `AsyncPostgresSaver` wiring + tabla `durable_flow_checkpoints` + registro de flujos en `core/`. Decidir si es EP nuevo o ensanche de EP-4. Surface: `builder-agentic` (Opus) + `auditor-agentic`. Requiere `/pm-luana` lift (vive en `core/`).
2. **Read-models publicados por dominio** (outcome trabajo derivado #4 — requisito del read/write split, caso borde 1). Ortogonal pero precondición de flujos cross-dominio observables.
3. **Story derivada vitalia (outcome #2):** primer flujo durable real — la traza B del research ("auto-liberación de cupos 24h + aviso a lista de espera") sobre el SYSTEM-MAP existente (dominio Operar/Mateo). Es la primera instancia + live-verify (DoD rule #37) del motor.
4. **Árbol de capacidades runtime-consultable + router 2-niveles** (resto de Fase B) — consume el motor pero es trabajo separado.

> Este spike NO produce `03-arch`/`04-validators`/`05-guidelines`/`06-tickets`/`dispatch-plan`, ni transiciona el state a `ready`. Es input de DECISIÓN para esas stories.

---

## 7. Research notes (date-aware — accedido 2026-06-02)

- **LangGraph durable execution** — https://docs.langchain.com/oss/python/langgraph/durable-execution · accessed 2026-06-02. Versión: `langgraph` (durability modes exit/async/sync; `AsyncPostgresSaver` paquete `langgraph-checkpoint-postgres`; `DeltaChannel` beta `>=1.2`; `EncryptedSerializer`). Takeaway: replay re-ejecuta nodos post-checkpoint → idempotencia obligatoria. **Post-cutoff (v0.4 abr-2026): verificado live hoy.**
- **LangGraph v0.4 HITL** — WebSearch "LangGraph durable execution checkpointer ... 2026" · accessed 2026-06-02. `interrupt()` + `Command(resume=)` first-class; incluido en `.invoke()` return + stream `values`. Takeaway: encaja con human_gate T3 + separación de poderes ADR-013.
- **Cloudflare Dynamic Workflows** — https://blog.cloudflare.com/dynamic-workflows/ · accessed 2026-06-02. `@cloudflare/dynamic-workflows` MIT, ~300 líneas TS, Worker Loader por tenant, sobre Dynamic Workers (open beta Workers Paid). Takeaway: **TS-only + runtime Cloudflare** → descartado para backend Python. **Post-cutoff (may-2026): verificado live hoy.**
- **Cloudflare Workflows GA + V2** — WebSearch + InfoQ · accessed 2026-06-02. GA; V2 replay determinístico + 50K concurrentes. Takeaway: maduro pero ajeno al stack.
- **Temporal Cloud vs Self-Hosted 2026** — https://automationatlas.io/guides/temporal-cloud-vs-self-hosted-2026/ + https://temporal.io/pricing · accessed 2026-06-02. Self-host $2.5-4.5K/mes + ops; Cloud ~$200/mes a bajo volumen (On-Demand 500 APS). Takeaway: requiere cluster separado → sobre-dimensionado para solo-operador hoy.
- **Temporal Python SDK** — https://docs.temporal.io/develop/python · accessed 2026-06-02. `temporalio` async, workflows/activities, worker process separado, signals/queries, namespaces para multitenancy. Takeaway: puerta de escape (durabilidad cross-service días/años), no base.
- **Patrón híbrido LangGraph + Temporal** — WebSearch "LangGraph supervisor with Temporal ... 2026" (AgentMarketCap, cordum.io) · accessed 2026-06-02. "LangGraph para razonamiento + Temporal para orquestación durable cross-service"; checkpointer guarda estado ENTRE nodos, no DENTRO. Takeaway: para flujos intra-tenant single-service (caso B), el checkpointer alcanza; Temporal recién con coordinación cross-service estricta de larga duración.
- **Internos:** `00-research.md` §4.5 (FLUJO 1ª clase) + §10 (B→A) · `ADR-013` D2 · `anti-duplication.md` (outbox/idempotency/llm existentes) · `PARADIGM.md` §5b/§6 (LangGraph supervisor = implementación swappable; el invariante es "flujo durable de 1ª clase").

---

## 8. Preguntas abiertas que requieren decisión de Chris

1. **¿Confirmás LangGraph durable como base + Temporal como puerta de escape documentada?** (vs. ir directo a Temporal aceptando el costo de cluster, o vs. parar el spike acá).
2. **¿El motor de flujos es un EP nuevo (EP-19) o un ensanche de EP-4 (copilot workflow)?** — afecta el contrato del Extension SDK. Recomendación del spike: **EP nuevo** (EP-4 está acoplado a copilot workflows; el motor de flujos durables es transversal a todos los empleados). Decisión final en el `03-arch` formal.
3. **¿Primer flujo durable real = traza B vitalia (auto-liberación de cupos)?** El outcome lo lista como story derivada #2; confirmar que es el primer caso de live-verify del motor (vs. un caso nicolify).
4. **Versión LangGraph objetivo:** hoy `>=0.2`. El motor durable + `DeltaChannel` + HITL v0.4 sugieren pinear `langgraph>=0.4` (o `>=1.2` si querés `DeltaChannel`). ¿Aceptás el bump cross-engine (afecta copilot + sales_agent — downstream regression en cada brand)? Esto es un lift `/pm-luana` por sí mismo.
5. **¿Read-models por dominio (outcome #4) van ANTES o EN PARALELO al motor?** Son precondición de flujos cross-dominio observables (caso borde 1) pero no del primer flujo intra-dominio.

---

## 9. Routing (para el ready-package futuro, no este spike)

| Surface (cuando se construya) | Builder | Auditor |
|---|---|---|
| `core/luana-core-*` motor de flujos (FlowCompiler, checkpointer, EP) | **`/pm-luana` promotion gate** (vive en engine — NO builder directo) | n/a hasta lift |
| `{brand}/.../{copilot,sales_agent}/workflows/` instancia de flujos | `builder-agentic` (Opus) | `auditor-agentic` (Opus) |
| `{brand}/.../{operar,scheduling,...}/` acciones referenciadas | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `{brand}/frontend/` panel de seguimiento del flujo (objeto visible) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

---

## Bitácora

- 2026-06-02 — `/architect` (platform) produjo este spike de decisión (Fase B cornerstone). Research date-aware vía WebSearch + WebFetch docs canónicas (LangGraph, Cloudflare, Temporal). Recomendación: LangGraph durable execution como base + Temporal puerta de escape + Cloudflare descartado. NO se tocó código ni `core/luana-core-*/src/`. NO se transicionó a `ready` (es spike, no ready-package).
- 2026-06-02 — **Chris CONFIRMÓ la recomendación** (LangGraph durable base + Temporal escape + Cloudflare descartado). Mandato: arrancar la story platform del motor + **mapear toda la deuda cross-brand + resolverla en esta misma conversación (flujo excepcional, cero deuda para ninguna marca)**. /pm-luana levantó el **drift map real** (greps 2026-06-02) — refina §2.3/§5 con un hallazgo material:
  - **La deuda ya existe y es concreta: el "patrón D10"** — 5 grafos durables YA construidos compilan con `graph.compile(checkpointer=...)` pero corren sobre `MemorySaver` porque `langgraph-checkpoint-postgres` NUNCA se instaló. Sitios: **vitalia ×3** (`agentic/lucas/workflows/lucas_daily_analysis_graph.py:503`, `copilot/workflows/wizard_onboarding_graph.py:323`, `copilot/workflows/treatment_followup_workflow.py:753`) + **comunify ×2** (`copilot/workflows/community_engagement_workflow.py:593`, `copilot/workflows/cohort_enrollment_workflow.py:913`) + soportes (extensions.py, module_registry_entry, cron handlers, wizard_checkpoint_config). nicolify/lupulo = 0 (esqueletos).
  - **Engine packages con `langgraph>=0.2`:** copilot + sales-agent + brand-studio (3). `langgraph-checkpoint-postgres` = NO instalado en ningún lado. `AsyncPostgresSaver` = 0 imports reales (solo comentarios "production target").
  - **Matiz crítico (reduce blast radius):** `AsyncPostgresSaver` (paquete `langgraph-checkpoint-postgres`) es compatible con `langgraph>=0.2` — **resolver la deuda L1 NO requiere bump a >=0.4** (el bump es solo para DeltaChannel/HITL v0.4 = nice-to-have, NO precondición). El bump cross-engine (Q4) puede separarse y NO tomarse ahora → menos riesgo downstream.
  - **2 capas del "motor":** **L1** = un-defer del checkpointer durable (instalar paquete + provider compartido en `core/` + cablear los 5 grafos + migraciones + tests + live-verify) = la deuda concreta cross-brand. **L2** = `FlowCompiler`/`FlowDefinition`/EP-19 (compositor declarativo) = la feature empleados-IA net-new que se construye SOBRE L1.
