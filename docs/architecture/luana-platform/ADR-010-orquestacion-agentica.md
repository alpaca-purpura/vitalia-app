# ADR-010 — Orquestación agéntica: trabajadores sobre un sistema, vía una capa de acción única

- **Status:** accepted (ratificado Chris 2026-05-30)
- **Date:** 2026-05-30
- **Scope:** platform-wide (10 marcas) — define el modelo operativo. SSoT vivo: `PARADIGM.md`.
- **Supersedes/extends:** ADR-007 (paradigm v4.1 autonomy) en la dimensión de *cómo* trabajan los agentes. No toca el ciclo SDD (lifecycle.md).
- **Extended by:** ADR-013 (empleados-IA + auto-extensión runtime + cadena de valor por puesto · 2026-06-01).

## Contexto

Refinando la organización del "Mapa Implementado" del cockpit surgió la pregunta de fondo: *¿qué ES Luana, arquitectónicamente, por encima de las features?* Sin esa definición, las "cajas" del mapa (Auth, Onboarding, Infra, agentes) se decidían ad-hoc y aparecían dos riesgos reales:

1. **Duplicación:** tratar a los agentes a la vez como "módulos web" y como un "módulo motor agéntico" llevaba a recrear lógica de negocio dentro de los agentes.
2. **Cajas sin doctrina:** Auth/Onboarding metidos dentro de "Configurar"; cifrado/observabilidad mezclados en un tacho "Infra".

Investigación 2026 consultada: business capability maps (TOGAF: tiers core/supporting/enabling), arc42 (§8 cross-cutting concepts, §10 quality attributes), multi-agent orchestration (supervisor/orchestrator-worker es el patrón más desplegado; empezar supervisor, graduar a swarm con data), MCP vs code-execution (no es "uno u otro": SSoT = capa de acción protocol-agnostic; consumo interno code-execution + progressive disclosure, externo MCP), y la tesis "vertical AI / agent-employee / managed labor".

## Decisión

1. **Modelo de 3 planos** (Sistema · Capa de acción · Trabajadores). El sistema funciona sin agentes; los agentes orquestan, no reimplementan. Detalle en `PARADIGM.md` §2.
2. **Capa de acción única, protocol-agnostic, como SSoT** (el service layer del DDD). Consumo: **code-execution + progressive disclosure** interno (token-barato), **MCP** como gateway externo/PHI/gobernado. El invariante es "acción única descubrible"; MCP/code-mode = implementación swappable.
3. **Orquestación supervisor:** **Valeria = supervisora** y única cara conversacional (WhatsApp + web). Especialistas scoped (Lisa, Adrián, Lucas, Camila, Mateo). agent-as-tool para composición, handoff para delegación total. **La pestaña web es sesgo de ruteo**, no un chat aislado (se preserva la composición multi-paso). Empezar supervisor; `routing_accuracy` como canario para evaluar swarm a futuro.
4. **Un solo engine por audiencia:** `core/luana-core-copilot` (interno, habla al dueño) · `core/luana-core-sales-agent` (externo, habla a leads). Las marcas agregan acciones scoped + personas, nunca otro engine.
5. **Adrián es bifronte:** especialista interno (config/reportes para el dueño) + agente externo autónomo (atiende leads). Es el puente entre audiencias.
6. **Reconciliación de roles:** **Valeria** pasa a supervisora transversal (no posee una caja de proceso). **Mateo** toma "Operar / Mi Día".
7. **El mapa = 3 zonas** (Agentes · Plataforma · Infraestructura). Cada cap tiene hogar zona→caja→área, **derivado** del registro SYSTEM-MAP, declarado desde la idea, validado al merge. Auth y Onboarding salen de "Configurar" a cajas propias en Plataforma; Infraestructura se sub-divide (Seguridad/Cumplimiento, Observabilidad, Plataforma técnica, Motor agéntico).

## Consecuencias

**Positivas:** elimina la duplicación por diseño (un engine, una acción); da un norte estable independiente de la tech; vuelve comercializable cada trabajador; las cajas del cockpit pasan a tener doctrina; el cap↔código bidireccional + índice de acciones habilita navegación agéntica sin grep.

**Costos / trabajo derivado (NO en este ADR, se listan como plan):**
- Migración `agent_owner: config/infra` → cajas nuevas (acceso/onboarding/configuracion/seguridad/…) en los ~71 caps de vitalia (story dedicada, incremental).
- Reorganizar `MapView.tsx` para render por zona + 2 lentes (trabajadores / proceso).
- Construir/generar el índice de acciones (Plano 2) desde las firmas del service layer + headers `# cap:`.
- Promover Valeria→supervisora / Mateo→Operar en SYSTEM-MAP + caps afectadas.

**Riesgos:** latencia del supervisor (mitigación: medir `routing_accuracy` + considerar swarm si la data lo pide); sandbox para code-execution (mitigación: empezar con el set de acciones tipado, sandbox cuando se habilite ejecución de código generado).

## Alternativas consideradas

- **Chat directo por pestaña (sin supervisora):** descartado — pierde la composición multi-paso que Chris quiere preservar.
- **Swarm puro (handoff peer-to-peer sin orquestador):** prematuro — el consenso 2026 es empezar supervisor y graduar con data; swarm exige tracing distribuido para debuggear.
- **MCP como SSoT (fat server con todos los tools):** descartado — quema 55k+ tokens antes del primer mensaje; el SSoT es la capa de acción, MCP es un adaptador.
- **Un engine/módulo agéntico por agente:** descartado — duplica el engine y rompe el lift gate a core.

## Referencias

- `docs/architecture/luana-platform/PARADIGM.md` — SSoT vivo del modelo operativo
- `.claude/rules/paradigm-arquitectura.md` — rule enforce-able + árbol de decisión zona/caja
- `.claude/rules/anti-duplication.md` · `.claude/rules/anti-orphan-integration.md`
- ADR-007 (paradigm v4.1) · ADR-009 (single-hub worktree)

## Bitácora (2026-06-01)

Estado de las 4 tareas derivadas listadas en Consecuencias (ninguna tenía story de tracking al cierre de esta sesión):

| Tarea derivada | Status |
|---|---|
| Migración `agent_owner: config/infra` → cajas nuevas (~71 caps vitalia) | **DEFERRED** — asignada a track B/Vitalia. Ratificada por Chris (D-7, 2026-06-01). NO es deliverable del harness; se ejecuta como story incremental dentro del backlog de vitalia cuando se retome track B. |
| Reorganizar `MapView.tsx` (render por zona + 2 lentes) | Sin story de tracking — on-demand cuando se retome el cockpit. |
| Construir/generar índice de acciones (Plano 2) desde service layer + `# cap:` headers | Sin story de tracking — on-demand. |
| Promover Valeria→supervisora / Mateo→Operar en SYSTEM-MAP + caps afectadas | Sin story de tracking — on-demand. |

Cross-ref: **ADR-013** (`docs/architecture/luana-platform/ADR-013-empleados-ia-auto-extension.md`) extiende este ADR en la dimensión empleados-IA + auto-extensión runtime + cadena de valor por puesto.
