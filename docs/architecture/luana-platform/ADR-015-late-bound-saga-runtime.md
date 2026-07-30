<!-- voseo-allowed: contenido arquitectónico interno, no user-facing -->
# ADR-015 — El flujo durable es una *late-bound saga* (planner dinámico + plan-como-dato + compensaciones), no un flujo pre-declarado

- **Status:** accepted (ratificado Chris 2026-06-16 — sesión de diseño empleados-IA)
- **Implementation state:** ⚠️ dirección ratificada + diseño técnico cementado. **Cero código.** La user-story de build es **futura** (precondición: ≥2 acciones de un dominio sólidas+live — ver § Secuencia). No confundir "ADR accepted" con "build iniciado".
- **Date:** 2026-06-16
- **Scope:** platform-wide (10 marcas). SSoT vivo del diseño: `docs/architecture/luana-platform/saga-runtime-design.md`.
- **Extends:** ADR-013 D2 ("flujo durable de 1ª clase"). **Supersedes la *dirección de implementación*** del diseño L2 estático (`durable-flows-L2-design.md` — `FlowCompiler`/`FlowDefinition` declarativo). Reusa L1 (`core/luana-core-flows`, migrated) intacto.
- **No toca** el ciclo SDD (lifecycle.md) ni los 3 planos (PARADIGM §2).

## Contexto

ADR-013 D2 cementó que **un flujo durable es unidad de 1ª clase** (orquestación con estado/seguimiento sobre acciones existentes), pero dejó el *cómo* a un diseño L2 que asumía **flujos pre-declarados por marca**: cada marca autora un `FlowDefinition` (DAG declarativo de nodos), el `FlowCompiler` lo compila a `StateGraph` durable. Modelo **estático**: el grafo se conoce de antemano.

En la sesión 2026-06-16, Chris rechazó la pre-declaración a nivel de código y propuso el modelo que usa Claude Code: **cada acción del sistema es un tool; un modelo fuerte (Kimi K2) entrega el "plan" multi-paso al vuelo; el plan se persiste como una "orden" hasta completarse — porque muchos pasos son asíncronos (sobre todo los que coordinan con humanos); y el plan lleva, en su propia respuesta, los riesgos + qué hacer ante cada uno** (ej. "¿qué pasa si a 1 día el paciente no contesta la reagenda?").

Validación contra el estado del arte (junio 2026, fuentes abajo): esto **tiene nombre publicado** — *late-bound saga* (Agentspan, abr-2026): "un workflow que el LLM escribe un edge a la vez; cada decisión es una transacción con una compensación, escrita antes de ejecutarse". Respaldo académico: **SagaLLM** (VLDB 2025 — saga + memoria persistente + compensación + agentes validadores) y **ALAS** (arxiv 2511 — planificación transaccional y dinámica multi-agente). El consenso 2026: el patrón ganador es **híbrido** — *backbone determinístico durable* + *inteligencia (LLM) en pasos puntuales*, NUNCA un LLM-en-loop autónomo (un run de 200 pasos en loop ingenuo tiene ~13% de éxito).

La pre-declaración estática (L2) no soporta el caso de Chris: el dueño le pide a Valeria algo que **no tiene flujo pre-armado**, y el sistema debe **componerlo dinámicamente** sobre los tools disponibles, persistirlo, y llevarlo a término solo.

## Decisión

### D1 · Plan-como-dato, no flujo-como-código

El flujo durable deja de ser un `FlowDefinition` autorado por la marca. Es una **saga**: un registro multi-paso que el **planner LLM compone dinámicamente** a partir de los **tools** disponibles (= acciones del Plano 2). El plan es **dato estructurado** (lista de intents + compensaciones + contingencias), **NO código** generado (el ADR-013 ya rechazó el code-gen end-user; esto lo respeta — un intent es un tool-call descrito, no código).

### D2 · "El LLM propone; el runtime dispone" (separación planner / ejecución durable)

- El **LLM (planner)** examina el estado y propone el **próximo intent** como dato. **Nunca ejecuta side-effects.**
- El **runtime durable** escribe el intent al **ledger ANTES de ejecutar** (así, tras un crash, sabe "¿esto ya pasó?"), ejecuta el tool, escribe el resultado, y vuelve a consultar al planner.
- **Reconciliación con la durabilidad (clave):** el output del LLM (el intent) queda **checkpointed**; en el **replay** post-crash NO se vuelve a llamar al LLM — se reproduce el intent registrado. El LLM solo se invoca para pasos **nuevos**. Esto preserva el determinismo del replay que exige la ejecución durable (L1/LangGraph ya lo dan: el output de un nodo se checkpointea, el replay restaura desde checkpoint).

### D3 · Cada paso lleva compensación (undo) + contingencia (forward) — la parte de "riesgos" de Chris

La intuición de Chris ("riesgos + acciones a tomar dentro del plan") se formaliza en **dos mecanismos distintos**, ambos parte del intent:

- **Compensación (backward / undo):** cómo deshacer un side-effect ya cometido si un paso posterior falla. Stack LIFO — se ejecutan en orden inverso (patrón saga clásico; SagaLLM). Ej.: si la notificación falla tras reagendar, compensar = revertir la reagenda.
- **Contingencia / timeout (forward recovery):** qué hacer cuando un `wait` expira o una rama falla sin necesidad de deshacer. Ej. de Chris: "a 1 día sin respuesta del paciente" → re-notificar → escalar a Valeria → tras N, compensar la reagenda + avisar al doctor.

Ambos se declaran **como parte del plan** (el planner los emite junto al intent), no se improvisan en runtime.

### D4 · La marca aporta TOOLS + políticas; el engine aporta el saga runtime (Liskov 60/40)

- **Compartido (`core/`):** el saga runtime — planner loop, ledger, compensation executor (LIFO), suspend/resume, idempotencia, observabilidad, validación. **Una sola máquina.**
- **Por marca (Extension SDK):** el **set de tools** (= acciones Plano 2: vitalia `reschedule`/`notify`/`find_slot`; nicolify las suyas) + por tool su **compensación** + su **clase de riesgo** (PHI / reversible / requiere human-gate). El planner y el runtime son idénticos cross-brand; lo único que varía es el espacio de acciones + sus políticas, registrado al boot.
- "Las acciones dependen de cada marca, la arquitectura es compartida" (requisito literal de Chris) ✅.

### D5 · Reusar, no reconstruir

El saga runtime **se monta sobre piezas que ya existen**, minimizando código nuevo:

| Pieza nueva (engine) | Reusa |
|---|---|
| Planner loop (LLM propone intent) | LangGraph supervisor + Kimi K2 vía LiteLLM proxy |
| Suspend-to-disk + resume + replay determinístico | **L1 `make_durable_checkpointer`** (migrated) + LangGraph `interrupt()` |
| Ledger de intents + compensation stack | estado checkpointed (TypedDict) — **no DB nueva** |
| Observabilidad por paso | `copilot_trace_event` (`luana-core-observability`) + `sanitize_payload` |
| Idempotencia de side-effects | `luana-core-idempotency` |
| Cierre por evento (coreografía) | `luana-core-events` outbox |

Código genuinamente nuevo = el planner-loop graph + ledger-en-estado + compensation-executor + el EP de registro de políticas por marca. Superficie acotada.

### D6 · Supersede la dirección L2 estática

`durable-flows-L2-design.md` (`FlowCompiler`/`FlowDefinition`/EP-19 `durable_flow_register`) queda **superseded como dirección de build**. NO se construye el compilador de flujos declarativos. EP-19 se **redefine**: de "registrar flujos pre-declarados" → "registrar **tools + compensaciones + guardrails por dominio**" (signature exacta = decisión de `/architect` al build). L1 NO se toca (sigue siendo el substrate durable).

## Consecuencias

**Positivas:** soporta el caso real de Chris (pedido sin flujo pre-armado, compuesto y llevado a término solo); más SOTA + más Liskov-limpio (marca = tools, engine = runtime); reusa L1 + LangGraph + events + idempotencia + observabilidad (poco código nuevo); las compensaciones/contingencias dan la confiabilidad que el LLM-en-loop ingenuo no tiene.

**Costos / trabajo derivado (NO en este ADR — ver design doc):**
- Build del saga runtime → user-story futura (`/architect` ready-package cuando haya piso de acciones).
- Endurecer ≥2-3 tools de un dominio (scheduling primero) como caps `live` — **precondición**.
- Primer saga **hand-rolled** (caso Adrián) sobre L1, antes de generalizar el runtime.

**Riesgos:** (a) LLM-en-loop autónomo sin barandas → ~13% éxito a 200 pasos (mitigado: backbone durable + compensaciones + validación + human-gates); (b) planificar sobre tools rotos → planes rotos más rápido (mitigado: precondición de piso de acciones sólidas+live, DoD #37); (c) costo/latencia del planner (mitigado: replay no re-llama al LLM; planner solo en pasos nuevos; modelo ruteado por rol).

## Alternativas consideradas

- **Flujos pre-declarados estáticos (L2 `FlowDefinition`/`FlowCompiler`):** superseded — no soporta el pedido sin flujo pre-armado; obliga a la marca a anticipar cada flujo a nivel de código.
- **LLM-en-loop sin saga (Claude-Code suelto, autónomo puro):** descartado — sin compensaciones/validación/human-gates la confiabilidad colapsa en runs largos (~13% a 200 pasos). El ganador 2026 es híbrido.
- **Code-gen del usuario final:** descartado (ya en ADR-013) — el plan es **dato** (intents), no código.
- **Motor de flujos propio sin reusar L1:** descartado — L1 ya da el suspend/replay durable; reconstruirlo viola anti-duplication.

## Secuencia (de la arquitectura, no negociable por el orden)

1. **Fix `/chat` brand-mountable** (tanda actual, ADR/proposal aparte) → un solo motor montado por marca.
2. Endurecer 2-3 tools de scheduling como caps `live` (DoD #37).
3. **Primer saga hand-rolled** (caso Adrián) sobre L1 — UN ejemplo concreto.
4. Recién ahí: generalizar el **saga runtime** como engine compartido (no antes — mismo principio que "no construir L2 sin ejemplo").

## Referencias

- `docs/architecture/luana-platform/saga-runtime-design.md` — **SSoT vivo del diseño técnico** (data structures, planner loop, reparto core/brand, determinismo, ejemplo Adrián, open questions, validators).
- `ADR-013-empleados-ia-auto-extension.md` D2 — flujo durable de 1ª clase (este ADR concreta su *cómo*).
- `durable-flows-L2-design.md` — **superseded** (dirección estática reemplazada).
- `docs/core-modules/flows.md` — L1 contract (substrate durable reusado).
- `PARADIGM.md` §5b (auto-extensión) + §6 (invariante vs implementación).
- SOTA junio 2026: [Late-Bound Sagas — Agentspan](https://medium.com/agentspan/late-bound-sagas-why-your-agent-is-not-an-llm-in-a-loop-a8c50731c551) · [SagaLLM — VLDB 2025](https://arxiv.org/abs/2503.11951) · [ALAS — arxiv 2511](https://arxiv.org/pdf/2511.03094) · [2026 playbook — determinism + replay](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/) · [Temporal — dynamic AI agents](https://temporal.io/blog/of-course-you-can-build-dynamic-ai-agents-with-temporal).
- `.claude/rules/anti-duplication.md` · `anti-orphan-integration.md` · `paradigm-arquitectura.md`.
