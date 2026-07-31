<!-- voseo-allowed: contenido arquitectónico interno, no user-facing -->
# ADR-013 — Empleados-IA + auto-extensión: el producto es un equipo, el motor se auto-extiende

- **Status:** accepted (ratificado Chris 2026-06-01 — "vamos con la (a)")
- **Implementation state:** ⚠️ dirección ratificada, stories aún en `idea` / refinamiento (2026-06-01). Las stories derivadas listadas en "Consecuencias" NO arrancaron (`developing`). El MEMORY pointer `luana-empleados-ia-vision` refleja este estado ("NO ADR/spec aún" era pre-ratificación; este ADR es el primero post-ratificación). No confundir "ADR accepted" con "implementación iniciada".
- **Date:** 2026-06-01
- **Scope:** platform-wide (10 marcas). SSoT vivo: `PARADIGM.md` (§5b). Detalle/investigación: `docs/architecture/luana-platform/empleados-ia-research.md` (graduado de la story archivada 2026-06-02 — una user-story no es SSoT).
- **Extends:** ADR-010 (orquestación agéntica — 3 planos) + ADR-007 (paradigm v4.1 autonomy). No toca el ciclo SDD (lifecycle.md).
- **Reset:** nace en `/pm-luana` y se propaga a todas las marcas; vitalia (SYSTEM-MAP 3 zonas/12 cajas) y nicolify (roster/shell) pasan a ser las 2 primeras INSTANCIAS del modelo (no se descartan).

## Contexto

ADR-010 cementó el modelo estático (3 planos · supervisora · un engine · acción única) pero no cubre dos dimensiones que emergieron en la sesión 2026-05-31→06-01:

1. **Cómo el sistema se auto-extiende en runtime** — qué pasa cuando el dueño pide algo que el sistema todavía no hace ("el usuario pide → lo creamos"), de forma gobernada y sin volverse un caos de islas.
2. **Cómo se comercializa y coordina** — el producto como equipo de empleados-IA vendido por puesto, y cómo coordinan entre sí sin romper SOLID.

Investigación 2026 consultada (detalle + sources en `empleados-ia-research.md`): AgentSkillOS (árbol de capacidades + DAG, valida la estructura), Agent Skills standard / Pydantic Capabilities (formato de "chunk"), AG-UI/A2UI (generative UI), Cloudflare Dynamic Workflows / Temporal / LangGraph (durable execution), E2B/Modal (sandbox), multi-agent topologías (orchestrator-worker 70% prod; coordination failures 37%; choreography = loose coupling), pricing agent-employee (híbrido base+overage estándar; outcome-based), WhatsApp Flows LatAm.

## Decisión

### D1 · El motor de auto-extensión (12 primitivas × 5 tiers + router 2-niveles + flywheel)

- **12 primitivas = OBJETOS** en 3 familias (Ver / Hacer-Guardar / Gobernar). Las **operaciones de ciclo de vida** (crear/leer/modificar/**desactivar/eliminar**) son **verbos ortogonales**, no primitivas.
- **5 tiers:** T0 rechazo (refuse-with-reframe) · T1 orquestar/mostrar (instant) · T2 configurar/extender (config declarativa sobre extension-points, sin código, tenant-scoped reversible) · T3 construir (sandbox + humano + live-verify) · T3+ decisión de producto / **core invariante**.
- **Router de 2 niveles:** L1 (supervisora) ruteo grueso contra el SYSTEM-MAP (interfaces); L2 (empleado dueño) resolución fina contra SUS extension-points. Resolución nodo-por-nodo (DAG).
- **El "sobre" de T2 = los extension-points declarados** (EP-1..18). **Flywheel:** T3 frecuente → humano lo lifta a EP nuevo (promotion gate) → colapsa a T2 para siempre.

### D2 · Flujo = unidad durable de primera clase

Las acciones son verbos transaccionales sin estado; un **flujo (#7)** es orquestación **durable, con estado, observable, con dueño** sobre acciones existentes. La línea regla(#5)/flujo(#7) es el **estado/seguimiento del conjunto**. **Cornerstone de implementación (fase B):** convertir la composición de flujos durables en un extension-point T2 de 1ª clase (spike: Cloudflare Dynamic Workflows / Temporal / LangGraph+durabilidad).

### D3 · Coordinación de 3 modos (formaliza el "supervisor→swarm con data" de ADR-010)

1. **Coreografía por eventos** = espina dorsal (80%): agentes reaccionan a eventos del `luana-core-events` outbox; loose coupling (DIP). 2. **Orquestación por la supervisora** (20%): ambiguo / cross-dominio / síntesis / user-facing / **PHI** (auditoría obligatoria). 3. **Handoff directo:** excepción medida (loop estrecho, no-PHI, métricamente mejor). **Ningún agente llama a otro concretamente.** Router adaptativo elige el modo (calidad/precio).

### D4 · SOLID como disciplina + ownership de la construcción

- **Cada empleado = un puesto** (S), extensible sin tocar core/otros (O), **etapa sustituible** → cross-brand (L), contratos finos (I), **depende de abstracciones/eventos, nunca de otro agente concreto** → vendible por separado (D).
- **La supervisora NUNCA diseña/decide construcción en dominio ajeno** — reenvía la *intención*; el empleado dueño decide qué y cómo (consistente con ADR-vitalia-005: Valeria no es caja de valor).
- **Orquestación fractal:** supervisora↔empleados = flujo↔acciones (mismo patrón, distinta granularidad; siempre vía interfaces/eventos).

### D5 · Producto = equipo de empleados-IA vendido por puesto

- **Base obligatoria** (identidad "Mi Clínica" + Configuración + Supervisora) + **cadena de valor** (Atraer → Vender → Operar → Retener) como **SKUs** combinables/packs.
- Cada empleado = 4 facetas: cara (FE) · dominio acotado (sobre UN engine, no motor propio) · autonomía (tiers) · SKU.
- **Cross-brand 60/40 (Liskov):** la etapa es interfaz estable (~60% → core); el roster + procesos varían por marca (~40% → extension). Packaging híbrido (base+overage); arquitectura soporta entitlement por empleado + medición de outcomes (pricing exacto = decisión futura).

### D6 · Techo de auto-extensión + separación de poderes (refinamientos del estrés-test)

- **Read/write split (CQRS):** reads/vistas = dueño por vantage/decisión, componibles cross-dominio vía **read-models publicados**; writes/flujos = dueño por outcome.
- **Techo:** la auto-extensión runtime topa en la superficie brand-extension; lo que toca el **core invariante** (compliance, cifrado, contratos cross-brand) NO se auto-construye → escala al gate humano `/pm-vitalia`.
- **Separación de poderes:** un agente NO se auto-otorga autonomía; la gobierna el humano vía Configuración (el agente pide, el humano concede).
- **T0 inteligente:** un remove/cambio que viola compliance se rechaza CON razón + re-rutea al objetivo legítimo.

## Consecuencias

**Positivas:** define el "cómo" del producto vendible (empleados por puesto) + el "cómo" del motor (auto-extensión gobernada); da barandas SOLID que evitan islas/duplicación/brechas; vuelve el cross-brand un problema de instanciación (Liskov), no de fork; conecta la investigación 2026 a decisiones concretas.

**Costos / trabajo derivado (NO en este ADR — plan):**
- Spike del **motor de flujos durables** (cornerstone B) → `/architect`.
- Stories derivadas por marca (instanciar roster + procesos) → `/pm-vitalia` + `/pm-nicolify` (ver outcome).
- Construir el árbol de capacidades runtime-consultable + read-models por dominio + el router 2-niveles.
- Trayectoria B (consolidar el motor para nosotros) → A (exponérselo al usuario vía supervisora).

**Riesgos:** auto-extensión sin barandas → islas/brechas (mitigado por D1/D4/D6 + anti-orphan CONN); "un agente su motor" → N motores (mitigado: un engine, personas/scopes); latencia/costo de orquestación (mitigado por coreografía como default + router adaptativo).

## Alternativas consideradas

- **No formalizar la auto-extensión (dejarla emergente):** descartado — sin tiers/router/techo se vuelve un feature-factory ingobernable (el cementerio del citizen-developer).
- **Generación de código libre por el usuario final:** descartado — los productos que ganan (Decagon/Sierra/Lindy) hacen *configuración gobernada*, no code-gen end-user; el code-gen es T3 humano-en-loop.
- **Swarm puro / A2A directo como default:** descartado — coreografía-por-eventos + supervisora dan loose coupling + auditoría (HIPAA); directo es excepción medida.
- **Un engine/SKU técnicamente separable por empleado:** descartado — packaging ≠ separabilidad arquitectónica; un engine, entitlement gatea las superficies.

## Referencias

- `PARADIGM.md` §5b — SSoT vivo (extensión de este ADR)
- `docs/architecture/luana-platform/empleados-ia-research.md` — investigación + panorama + 4 casos borde (SSoT vivo; graduado de la story archivada 2026-06-02)
- `docs/architecture/luana-platform/durable-flows-L2-design.md` — diseño L2 del motor de flujos durables (FlowCompiler/FlowDefinition/EP-19; L1 ya migrated)
- `docs/product/outcomes/empleados-ia-auto-extension-platform.md` — outcome platform + stories derivadas
- `ADR-010-orquestacion-agentica.md` (extiende) · `ADR-vitalia-005` (Valeria no es caja de valor) · `ADR-009` (single-hub)
- `.claude/rules/paradigm-arquitectura.md` · `anti-duplication.md` · `anti-orphan-integration.md`
- MEMORY `luana-empleados-ia-vision`
