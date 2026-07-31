<!-- voseo-allowed: contenido arquitectónico interno sobre mecánica de trabajadores, no user-facing -->
# PARADIGM — Modelo operativo de Luana (norte arquitectónico)

> **Qué es este archivo:** el **norte vivo** de cómo queremos que Luana funcione, **por encima de cualquier funcionalidad y por encima de la tecnología del momento**. No describe features ni stack — describe la *forma* en que todo lo demás debe encajar. Si una decisión de feature, skill, rule o tech contradice este documento, el problema es la decisión, no el paradigma.
>
> **Para quién:** para Claude (que es el cuerpo y las manos de Chris en este repo) y para todo skill/agente que orqueste trabajo. Debe estar **siempre cargado/claro** (pointer en root `CLAUDE.md` + rule `.claude/rules/paradigm-arquitectura.md` + MEMORY).
>
> **Estado:** cementado 2026-05-30 (`ADR-010`). **Extendido 2026-06-01 (`ADR-013`):** auto-extensión runtime + cadena de valor comercial por puesto (§5b). Cambiarlo requiere ratificación explícita de Chris + bump de ADR.

---

## 1. Tesis

Luana **no es un SaaS de herramientas que un humano opera**. Luana es un **equipo de trabajadores digitales** que **operan por el dueño** un sistema de negocio completo de Go-To-Market (atracción → conversión → operación → fidelización, con CRM). El cliente no compra una herramienta para hacer el trabajo; **contrata trabajadores que hacen el trabajo**. El mercado lo llama *managed labor / agent-employee*: el precio tiende a "trabajo hecho", no a "asiento".

Corolario: el sistema **funciona aunque no haya agentes** (se puede operar a mano desde la web). Los agentes son la capa que hace ese mismo trabajo **conversacionalmente y solo**, y la web **refleja** lo que el trabajador hizo.

---

## 2. Los 3 planos (la columna vertebral)

Todo en Luana vive en uno de tres planos. Confundirlos es la causa raíz de la duplicación.

```
┌─ PLANO 1 · EL SISTEMA (capacidades de negocio) ─────────────────────────────
│   El "SO de Go-To-Market". Los procesos reales: booking, CRM, ofertas,
│   campañas, contenido, NPS, tratamientos… Existe SIN agentes. Operable a
│   mano desde la web. Es el SSoT de "qué SABE hacer el negocio".
│
├─ PLANO 2 · LA CAPA DE ACCIÓN (acciones únicas) ─────────────────────────────
│   Cada caso de uso del sistema se expone UNA sola vez como acción invocable
│   (book_appointment, create_lead, send_campaign…). La web (REST) y los
│   trabajadores (tool-call) ejecutan LA MISMA acción. El trabajador NUNCA
│   reimplementa el negocio — lo invoca, igual que el form de la web.
│
└─ PLANO 3 · LOS TRABAJADORES (orquestación agéntica) ────────────────────────
    Una supervisora (Valeria) + especialistas con scope (Lisa, Adrián, Lucas,
    Camila, Mateo). UN solo engine compartido. Difieren solo en:
    (a) su set de acciones permitidas (scope), (b) su persona/voz, (c) sus
    objetivos y guardrails. El "motor agéntico" es el RUNTIME del Plano 3,
    no un módulo que compite con los trabajadores.
```

**Por qué esto mata la duplicación de raíz:** los trabajadores no copian la web; son una capa fina de orquestación que llama al Plano 2. Hay **un solo engine** (`core/luana-core-copilot` interno · `core/luana-core-sales-agent` externo). Las marcas solo agregan *acciones scoped + personas*, nunca otro engine.

---

## 3. Los trabajadores (Plano 3 en detalle)

### 3.1 Supervisora única + especialistas scoped

- **Valeria = supervisora y única cara conversacional.** Es con quien habla el dueño (WhatsApp *y* web). Recibe todo, clasifica intención, delega y **compone flujos multi-paso** entre especialistas. (Patrón orchestrator-worker / supervisor — el más desplegado en producción; empezar supervisor, graduar a swarm solo con data de latencia.)
- **Especialistas = persona + scope (una franja del value-stream) + acciones permitidas + presupuesto/guardrails.** Lisa→clínica/marca, Lucas→growth, Camila→reputación/fidelización, Mateo→operación. Cada uno es **comercializable como un trabajador** (suelto o en equipo).
- **La pestaña web = sesgo de ruteo, no un silo.** En la tab de Lucas el chat arranca pre-scopeado a Lucas, pero bajo el mismo grafo de Valeria → si pedís algo cross-dominio, rutea/escala solo. Foco cuando lo querés, composición cuando la necesitás.
- **Mecánica:** *agent-as-tool* cuando Valeria orquesta y necesita la respuesta de vuelta · *handoff* cuando delega la tarea completa.

### 3.2 Audiencia: interno vs externo (y Adrián, el puente)

| | Audiencia | Engine | Rol |
|---|---|---|---|
| **Trabajadores internos** (Valeria, Lisa, Lucas, Camila, Mateo) | el **dueño** del negocio | `copilot` | operan el sistema *por* el dueño |
| **Trabajador externo** (Adrián) | los **leads/clientes** del dueño | `sales_agent` | conversa autónomo en los canales del tenant |

**Adrián es bifronte** (no es contradicción, es feature): (1) como especialista bajo Valeria el dueño lo configura/le pide reportes; (2) como front-line atiende leads solo. Mapea limpio a los dos engines existentes.

---

## 4. El mapa del producto = 3 zonas (cómo el paradigma se ve en el cockpit)

El cockpit ("Mapa Implementado") agrupa toda capability en **una de tres zonas**. La zona es el "código postal" del Plano 1+3 y se **deriva** del dueño de la caja (registro en `{brand}/docs/architecture/SYSTEM-MAP.yaml`), no se escribe a mano por cap.

| Zona | Tier (cap-map) | Qué contiene | `user_visible` |
|---|---|---|---|
| **Agentes** | core | El valor user-facing que opera cada trabajador: las cajas de los 5 especialistas (Lisa·Valeria/Mateo·Adrián·Lucas·Camila) | `true` |
| **Plataforma** | supporting | Superficies transversales que el usuario atraviesa pero **no son de ningún agente** (se operan a mano): **Acceso** (auth+authz), **Onboarding** (alta+activación), **Configuración** (ajustes tenant, clínicas, equipo, conexiones) | `true` |
| **Infraestructura** | enabling | No-funcional / técnico (cross-cutting concepts + quality attributes): **Seguridad & Cumplimiento** (cifrado at-rest PHI, audit log, dual-filter, tenant isolation), **Observabilidad**, **Plataforma técnica** (idempotency, eventos, payment rails, IAM engine), **Motor agéntico** (engine copilot/sales_agent, RAG) | `false` |

**Regla de oro del mapa:** ninguna capability existe sin caja, y ninguna caja existe fuera de una zona. Una cap sin zona válida = huérfana (ver `anti-orphan-integration.md`). Desde la **idea**, el árbol de decisión de `.claude/rules/paradigm-arquitectura.md` dice en qué caja/zona aterriza — y se valida hasta el merge.

---

## 5. Principios invariantes (la filosofía — no cambian con la tech)

1. **Toda acción existe una sola vez.** Web y trabajadores comparten la misma acción (Plano 2). Cero reimplementación.
2. **Los trabajadores orquestan, no reimplementan.** Un agente que recrea lógica de negocio es un bug de arquitectura.
3. **Un solo engine.** Persona + scope + guardrails diferencian al trabajador. Nunca un engine por agente ni por marca (lift a `core/` vía `/pm-vitalia`).
4. **Audiencia explícita.** Interno (dueño, `copilot`) vs externo (leads, `sales_agent`). Adrián es el único puente.
5. **Una supervisora conversacional** (Valeria). La pestaña es sesgo de ruteo, no un chat aislado. Se preserva la composición multi-paso.
6. **El cockpit LEE, no genera.** El SSoT son archivos estructurados (caps YAML + código con header `# cap:` + SYSTEM-MAP + service layer). Las vistas e índices son **derivados** regenerables, nunca fuente.
7. **Conectividad total, navegación sin grep.** cap↔código es bidireccional (`dev_preview` apunta al código, header `# cap:` apunta a la cap). Un agente llega a cualquier cosa en mínimos pasos leyendo el índice, **sin grep que queme miles de tokens**. Nada llega a `done` como isla.
8. **Acción única descubrible progresivamente.** Las acciones se descubren on-demand (no se cargan todas al contexto) y los datos se procesan fuera del contexto. La *forma* de exponerlas (code-execution, MCP) es implementación; el principio no.
9. **Cada cap tiene hogar de 3 niveles:** zona → caja (trabajador o superficie) → área. Declarado desde la idea, derivado del registro, validado al merge.

---

## 5b. El sistema se auto-extiende + se comercializa por puesto (ADR-013 · 2026-06-01)

Dos dimensiones que extienden los 3 planos. Detalle completo: `ADR-013` + `docs/architecture/luana-platform/empleados-ia-research.md`.

**(A) El motor se auto-extiende — "el usuario pide → lo creamos", gobernado.** Todo pedido del dueño se reduce a **12 primitivas (objetos)** en 3 familias (Ver/Hacer-Guardar/Gobernar), con **operaciones de ciclo de vida** ortogonales (incl. desactivar/eliminar). Se resuelve en **5 tiers**: T0 rechazo (refuse-with-reframe) · T1 orquestar/mostrar · T2 configurar sobre extension-points (sin código) · T3 construir (sandbox+humano+live-verify) · T3+ producto / **core invariante**. **Router de 2 niveles:** L1 supervisora (¿de qué dominio?) → L2 empleado dueño (¿T1/T2/T3 en mi dominio?). **Flywheel:** T3 frecuente → lift a EP nuevo → colapsa a T2. **El flujo es unidad durable de 1ª clase** (estado+seguimiento), distinto de la acción transaccional — implementado como **late-bound saga** (planner LLM compone el plan al vuelo sobre tools, plan-como-dato + compensaciones), no como flujo pre-declarado (`ADR-015` · `saga-runtime-design.md`).

**(B) El producto es un equipo vendido por puesto.** Base obligatoria (identidad + Configuración + supervisora) + **cadena de valor** (Atraer→Vender→Operar→Retener) como **SKUs** combinables. Cada empleado = cara (FE) · dominio acotado (un engine, no motor propio) · autonomía (tiers) · SKU. **Cross-brand 60/40 (Liskov):** la etapa = interfaz estable (core); roster + procesos = instancia por marca (extension).

**Barandas SOLID (las que evitan el caos):** la supervisora **reenvía intención, no construye** en dominio ajeno (el dueño construye lo suyo); **orquestación fractal** (supervisora↔empleados = flujo↔acciones, siempre vía interfaces/eventos, nunca internals); **coordinación de 3 modos** (coreografía por eventos = default · supervisora para ambiguo/PHI · handoff directo = excepción medida); **read/write split** (reads componibles vía read-models, writes con dueño por outcome); **techo de auto-extensión** (core invariante → gate humano `/pm-vitalia`); **separación de poderes** (el agente pide autonomía, el humano la concede).

---

## 6. Invariante vs implementación (para no confundir filosofía con tech del mes)

Lo de la izquierda **no cambia**. Lo de la derecha es **swappable** sin tocar el paradigma.

| Invariante (el QUÉ — permanente) | Implementación hoy (el CÓMO — reemplazable) |
|---|---|
| Acción única, descubrible progresivamente, datos fuera del contexto | **Code-execution + progressive disclosure** interno · **MCP** como gateway externo/PHI/gobernado. (No "MCP vs CLI": ambos sobre el mismo SSoT) |
| Una supervisora + especialistas scoped | **LangGraph** supervisor + `deepagents SubAgentMiddleware` |
| Flujo durable de 1ª clase (estado + seguimiento del conjunto) | **Late-bound saga runtime** (planner LLM dinámico + plan-como-dato + compensaciones/contingencias) sobre L1 durable checkpointer — `ADR-015` (supersede el L2 `FlowCompiler` estático) |
| Un solo engine por audiencia | `core/luana-core-copilot` · `core/luana-core-sales-agent` |
| Memoria/voz por trabajador con cache | Anthropic prompt cache (slots 5min/1h TTL) |
| cap↔código bidireccional sin grep | header `# cap:` + `dev_preview` + `validate_code_cap_bidirectional.py` |
| Capa de acción = el service layer del DDD | FastAPI application services tipados |

> El día que "code-mode reemplace a MCP" (o al revés), o que cambie el framework de agentes, **este documento no se toca** — solo el adaptador. Eso es lo que lo vuelve un norte estable.

---

## 7. Dónde se enforce (para que NO sea un archivo para el olvido)

| Punto | Mecanismo |
|---|---|
| **Siempre cargado** | Pointer en root `CLAUDE.md` § Paradigma + `.claude/rules/paradigm-arquitectura.md` (Critical Rule #36, auto-load) + MEMORY pointer |
| **Desde la idea** | `/pm-{brand}` + `/po-ux`/`/po`/`/ux-agentico` aplican el árbol de decisión (zona/caja) al crear/refinar story; el checkpoint declara la caja |
| **Diseño** | `/architect` § Integration design (CONN) declara reachability entre planos + hogar (zona) |
| **Build** | `builder-*` no cruzan plano sin escalar; acción única, no mirror |
| **Review** | `/auditor` categoría Connectivity (anti-isla) verifica zona/caja + cap↔código |
| **Cap home** | `docs/process/capability-protocol.md` deriva la zona del registro SYSTEM-MAP |
| **Cockpit** | `{brand}/docs/architecture/SYSTEM-MAP.yaml` (`zones`) es el esqueleto que el mapa lee |
| **DoD live-verify** | `.claude/rules/definition-of-done-live-verify.md` (Critical Rule #37) — ninguna capability user-reachable llega a `done` sin ejercerse live en el stack dev real de la marca + `dod_evidence` registrado |

---

## 8. Referencias

- `docs/architecture/luana-platform/ADR-010-orquestacion-agentica.md` — la decisión registrada (3 planos)
- `docs/architecture/luana-platform/ADR-013-empleados-ia-auto-extension.md` — extensión §5b (auto-extensión + SKU por puesto)
- `docs/architecture/luana-platform/empleados-ia-research.md` — investigación + panorama + casos borde (SSoT vivo)
- `docs/architecture/luana-platform/durable-flows-L2-design.md` — diseño L2 motor de flujos durables (L1 migrated)
- `.claude/rules/paradigm-arquitectura.md` — rule enforce-able + árbol de decisión zona/caja
- `docs/process/capability-protocol.md` — schema cap + derivación de zona
- `docs/process/lifecycle.md` — 4 ejes (Release→Story→Capability→Scenario) + hogar de la cap
- `.claude/rules/anti-orphan-integration.md` — nada llega a `done` como isla (CONN)
- `.claude/rules/anti-duplication.md` — un solo engine, una sola acción (Plano 2)
- `{brand}/docs/architecture/SYSTEM-MAP.yaml` — registro zonas→cajas→áreas (lo que lee el cockpit)
