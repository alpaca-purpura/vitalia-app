---
story_id: empleados-ia-auto-extension
state: idea
created: 2026-06-01
researcher: chris + /pm-luana
last_modified: 2026-06-01
research_iterations: 1
decision_pending: true
decision_options: ["promote-adr-platform", "refining", "parked"]
---

<!-- voseo-allowed: doc interno SDD (research bundle); cita ejemplos de pedidos de usuario en voz natural + términos internos, no strings user-facing -->

# Research — Luana como sistema operativo de empleados-IA con auto-extensión

> **SSoT de arranque** del paradigma unificado. Bundlea la investigación (estado del arte 2026 + OSS), las decisiones cementadas en sesión 2026-05-31→06-01, el panorama completo, y 4 casos borde que estresan el modelo. Complementa (no reemplaza) `PARADIGM.md` + `ADR-010`.

## §0 · Tesis maestra (lo que une todo)

> **Lo que el cliente compra** = un equipo de **empleados-IA** sobre una cadena de valor. **Cómo funciona por dentro** = un sistema que **se auto-extiende**: la intención del usuario → primitivas → tiers, coordinada por eventos y por una supervisora. **Son la misma cosa**: cada empleado es la *cara* de un dominio de capacidades que puede crecer solo, sobre **un único motor**.

Y el insight de fase: **el pipeline de desarrollo (architect→build→auditor→live-verify) ES el motor que la supervisora-runtime flexiona.** Por eso **B (consolidar el motor para nosotros) ahora, A (exponérselo al usuario) como norte.**

## §1 · Problema / Oportunidad

- **Dolor del dueño:** correr el go-to-market de un negocio de servicios exige muchas herramientas + gente; los SaaS venden asientos y features, no resultados; y siempre falta "esa cosa que mi negocio necesita".
- **Oportunidad de mercado (2026):** los **agentes verticales se comen al SaaS** — venden *trabajo terminado*, no asientos ("we need 5,000 tickets handled", no "50 licencias"). 2026 = "el año del agente-empleado": agentes con título, presupuesto y management.
- **Moat de Luana:** (1) sistema **determinista usable sin agente** (clave en salud regulada — los pure-generative-UI no pueden decirlo), (2) **auto-extensible gobernado** (el usuario pide → el sistema construye, con barandas), (3) **vertical + LatAm + omnicanal (WhatsApp-first)**.

## §2 · Estado del arte 2026 (lo que hacen otros + OSS)

| Pilar | Qué existe (2026) | Implicación para Luana |
|---|---|---|
| **Empleados-IA / digital workers** | Categoría dominante. Artisan vende "AI Employees"; vertical agents > SaaS | Validación directa de la visión — somos esto, nativo/vertical/LatAm |
| **Agent Skills standard** (Anthropic, SKILL.md, progressive disclosure, registro skills.sh) | Estándar de facto (32 herramientas) | Formato candidato del "chunk"/capacidad (ya lo usamos para dev) |
| **Pydantic AI Capabilities / AgentSpec** | Unidades componibles cargables de YAML | Formato del "chunk" en nuestro BE Python |
| **AG-UI + A2UI** (Google) | Server-driven / generative UI; el agente inyecta UI sin reprogramar front | La capa "Reflejo en interfaz" / propuesta-como-artefacto |
| **Cloudflare Dynamic Workflows** (MIT, may-2026) / Temporal / LangGraph | Durable execution per-tenant ("el workflow sigue al tenant") | El **motor de flujos durables** (la "esencia de flujo") |
| **E2B / Modal** (+ OpenAI Agents SDK sandbox nativo, 7 proveedores) | Sandbox aislado para código generado | El aislamiento de la "Fase de Creación" (T3) |
| **AgentSkillOS** (arXiv 2603.02176) | Skills en **árbol de capacidades** + orquestación **DAG**; tree-retrieval ≈ oracle; DAG ≫ flat; escala 200→200K skills | Valida la estructura: árbol (registro) + DAG (router) |
| **Multi-agent topologías** | Orchestrator-worker = 70% prod; coordination failures = 37%; overhead centralizado ~285% vs independiente ~58%; adaptive routing +22.9% | Funda la decisión de coordinación (§5) |
| **Pricing** | Híbrido (base+overage) = estándar 41%; per-agent $50-200; outcome-based (Intercom Fin $0.99/ticket → $1M→$100M ARR) | Funda el packaging por puesto + packs |
| **WhatsApp (LatAm)** | Conversational commerce $18.2B, 72% por WhatsApp; WhatsApp Flows = UI dentro del chat | La omnicanalidad WhatsApp-first + deep-links |

Sources completos en §13.

## §3 · La visión de producto: empleados-IA sobre una cadena de valor

**Metáfora maestra:** *Luana = una empresa de empleados-IA, vendida por puesto, sobre un solo motor.*

| Concepto empresa | En Luana | Capa |
|---|---|---|
| La empresa | El tenant | — |
| Los empleados | Agentes, cada uno dueño de un **departamento** (caja del SYSTEM-MAP = puesto por proceso) | Plano 3 |
| Gerente/COO | **Supervisora** (Valeria/Luana) — interpreta intención + rutea + coordina (NO construye) | Supervisor |
| Infraestructura (datos, seguridad, RRHH) | **Core engine** (luana-core-*) | Plano 1 |
| El "trabajo" | La **acción única** (la misma que usa la web) | Plano 2 |
| Organigrama | **"Work chart"** orientado a la cadena de valor | SYSTEM-MAP |

**Organigrama = cadena de valor:**
- **BASE obligatoria (no vendible suelta):** identidad ("Mi Clínica"/Lisa) + Configuración + Supervisora.
- **Cadena de valor (empleados = SKUs):** Atraer → Vender → Operar → Retener.
- **Cada empleado = 4 facetas:** una **cara** (módulo FE) · un **dominio acotado** (capacidades sobre el core — NO motor propio: persona+scope sobre UN engine) · **autonomía** (12 primitivas × 5 tiers sobre su dominio) · un **SKU** (entitlement/tier-gating).

**Cross-brand (Liskov · ~60/40):** la **etapa** (Atraer/Vender/Operar/Retener + Base + Supervisor) es la **interfaz estable** (~60% → core); el **agente de marca** es **implementación sustituible** (~40% → extension). Una marca puede partir/fusionar etapas.

| Pieza | vitalia | nicolify |
|---|---|---|
| Base | Lisa (Mi Clínica) + Config | "Mi Agencia" + Config |
| Atraer | Lucas | Brenda / Abel |
| Vender | Adrián | Christian |
| Operar | Mateo | Sara |
| Retener | Camila | Norvil |
| Supervisor | Valeria | Luana |

**Packaging (research-backed):** Base obligatoria + empleados como SKUs add-on combinables en packs; modelo **híbrido (base+overage)**. Pricing exacto = decisión futura de Chris; la arquitectura solo debe soportar **entitlement por empleado + medición de outcomes por empleado**.

## §4 · El motor: cómo el sistema se auto-extiende

### 4.1 · 12 primitivas (OBJETOS) × operaciones de ciclo de vida (VERBOS)

Cualquier pedido, en cualquier sistema, se reduce a cambiar uno de **12 objetos** (en 3 familias), aplicándole una **operación** (crear/leer/modificar/**desactivar/eliminar** — los verbos son ortogonales, no son primitivas):

- **👁️ VER:** 1) Vista/reporte/métrica
- **✋ HACER/GUARDAR:** 2) Dato/campo/entidad · 3) Acción/comando · 4) Estado/ciclo de vida · 5) Regla/automatización · 6) Validación/restricción · 7) Proceso/flujo · 8) Plantilla/documento
- **⚙️ GOBERNAR:** 9) Permiso/rol · 10) Apariencia/nomenclatura · 11) Conexión/canal · 12) Comportamiento de agente

> Refinamiento vs las 10 originales: se quitó "oferta" (es una *instancia*, no primitiva) y se agregaron estado/ciclo, validación/restricción, plantilla/documento. (Validado por convergencia: speech acts · metadata Salesforce/ServiceNow · configurabilidad SaaS · taxonomía de tools de agentes.)

### 4.2 · 5 tiers (autonomía / cómo se resuelve un pedido)

| Tier | Qué | Tiempo |
|---|---|---|
| **T0** Rechazo/guardrail | Inseguro / anti-compliance / fuera de dominio | inmediato (refuse-with-reframe) |
| **T1** Orquestar/mostrar | Ya existe, solo hay que componerlo/mostrarlo | instantáneo |
| **T2** Configurar/extender | No existe pero entra en un **extension-point** declarado (config declarativa, sin código) | casi instantáneo, reversible, tenant-scoped |
| **T3** Construir | Net-new (código/datos/integración) | minutos/horas + humano + sandbox + live-verify |
| **T3+** Decisión de producto | Módulo/producto nuevo, o cambio al **core invariante** | humano / roadmap / promotion gate `/pm-luana` |

### 4.3 · Router de 2 niveles

- **L1 (Supervisora):** ruteo grueso — *¿de qué dominio/dueño es esto?* — resuelve contra el SYSTEM-MAP (interfaces, no internals).
- **L2 (empleado dueño):** resolución fina — *dentro de MI dominio, ¿T1/T2/T3?* — resuelve contra SUS extension-points.
- Si el usuario ya está en la pestaña del dueño → se salta L1.
- Resolución **nodo-por-nodo** (DAG): un pedido puede mezclar nodos T1/T2/T3.

### 4.4 · El "sobre" de T2 + el flywheel

- **El alcance de T2 = los extension-points declarados** (nuestros EP-1..18). Lo que no entra → T3.
- **Flywheel:** T3 frecuente de la misma forma → un humano lo **lifta a un extension-point nuevo** (promotion gate) → colapsa a **T2 instantáneo para siempre**. El sistema *ensancha su propia capacidad de configurar* (= consolidación AgentSkillOS + promotion gate).

### 4.5 · Flujo = unidad durable de PRIMERA CLASE

Las **acciones** son verbos transaccionales sin estado. Un **flujo** (#7) es otra naturaleza: **orquestación durable, con estado, observable y con dueño** sobre verbos existentes. 6 propiedades: composición · estado durable · disparador · seguimiento/observabilidad · dueño · gobernanza.

- **Regla #5 vs Flujo #7:** la línea es el **estado/seguimiento del conjunto**. ¿Necesita esperar / saber en qué paso va / trackear el conjunto? → flujo.
- **Tier de un flujo:** si acciones/eventos existen **Y hay motor de flujos durables + compositor declarativo** → **T2** (el estado+tracking vienen gratis del motor). Nodo faltante → ese nodo T3. **Si el motor de flujos no existe aún → cualquier flujo es T3 hoy.**
- **★ Decisión estratégica B (cornerstone):** convertir la **composición de flujos durables** en un **extension-point de 1ª clase (T2)** colapsa una clase enorme de pedidos T3→instantáneo. Es el porqué de evaluar Cloudflare Dynamic Workflows / Temporal / LangGraph durable execution.
- **UX del seguimiento:** el flujo es un **objeto visible+monitoreable en la superficie del dueño** (la pestaña de Operar muestra "Auto-liberación de cupos" + stats), no magia de fondo.

### 4.6 · La capa conversacional (cómo "calza" un pedido en una primitiva)

> La taxonomía convierte **ambigüedad infinita en slot-filling finito**: clasificar en una primitiva define exactamente qué slots llenar. Y se confirma **mostrando, no preguntando**.

Loop (research-backed): 1) capturar el **objetivo** (no la feature) · 2) clasificar (acto de habla: ver/cambiar + primitiva candidata) · 3) aterrizar vocabulario contra el mapa · 4) resolver ambigüedad **proponiendo un borrador concreto** (explore-with-guidance, no interrogar 20×) · 5) confirmar el plan resuelto.
La clasificación se **valida por si el plan resuelve** contra el registro, no por la confianza del LLM.

## §5 · Coordinación entre empleados (3 modos · orquestación fractal)

**Decisión (delegada a /pm-luana):** **coreografía por eventos = espina dorsal; supervisora orquesta lo ambiguo; handoff directo = excepción medida. Ningún agente llama a otro concretamente.**

| Modo | Cuándo | Costo |
|---|---|---|
| **1 · Coreografía (eventos)** — 80% | Trabajo conocido/recurrente/async. Usa `luana-core-events` outbox (ya existe). DIP = loose coupling = vendible por separado | barato |
| **2 · Orquestación (supervisora)** — 20% | Ambiguo / cross-dept / síntesis / user-facing / **PHI**. Visibilidad+auditoría (obligatorio HIPAA). Supervisora **liviana** (rutea/sintetiza) | acotado |
| **3 · Handoff directo** — excepción | Loop estrecho no-solapado, latencia-crítico, **medido que gana** y **no-PHI** | medido |

**Orquestación FRACTAL:** la supervisora orquesta **empleados**; un flujo orquesta **acciones** — mismo patrón, distinta granularidad, **siempre dependiendo de interfaces/eventos, nunca de internals ajenos**. Por eso ni la supervisora invade a un empleado, ni el flujo de un empleado invade a otro.

## §6 · SOLID como disciplina de diseño del trabajo de agentes

| Principio | Aplicación |
|---|---|
| **S** | Cada agente = un puesto/etapa (1 razón de cambio) |
| **O** | Se extiende un agente sin modificar el core ni a otros (Extension SDK) |
| **L** | La **etapa** es interfaz estable; el agente de marca es impl sustituible → **hace cross-brand** |
| **I** | Contratos finos entre agentes (no acoplamiento gordo) |
| **D** | Agentes dependen de **abstracciones** (contratos+eventos vía core), NUNCA de otro agente concreto → **permite vender por separado** (si un agente no se compra, su abstracción la cumple la Base — degradado, no roto) |

**Ownership de la construcción (corrección clave):** la auto-extensión (analista→propone→construye) vive **siempre en el dominio del empleado DUEÑO**. La **supervisora NUNCA diseña/decide construcción ajena** — reenvía la *intención*; el dueño decide qué y cómo. (Consistente con ADR-vitalia-005: la supervisora no es caja de valor → no puede ser dueña de una construcción.)

## §7 · El panorama en capas + 2 trazas

```
CANALES (WhatsApp Flows · Web shell embedded+adaptativo · deep-links a vista+filtro)
   │ intención
   ▼
SUPERVISORA (Valeria/Luana): interpreta objetivo → clasifica (12 primitivas) →
   aterriza vocabulario → MUESTRA propuesta (no interroga) → rutea L1 / coordina
   │ asigna / coordina (3 modos)
   ▼
EMPLEADOS-IA (cadena de valor) — el PRODUCTO, vendido por puesto
   Base: Mi Clínica + Config   |   Atraer → Vender → Operar → Retener
   cada uno: cara · dominio · autonomía (5 tiers) · SKU   ↔ coordinan por EVENTOS (DIP)
   │ resuelven fino (L2) / ejecutan / extienden        ▲ reaccionan a eventos (coreografía)
   ▼                                                    │
CAPA DE ACCIÓN (acción única) + REGISTRO/ÁRBOL DE CAPACIDADES
   router DAG · T0/T1/T2/T3/T3+ · extension-points = "sobre" de T2
   │                                                    ▲ FLYWHEEL: T3 frecuente → EP nuevo → T2
   ▼                                                    │
CORE ENGINE (luana-core-*) — UN motor · ~60% invariante
   negocio · datos · event bus (outbox) · seguridad/compliance (HIPAA) · LLM router · Extension SDK
   │ self-extension T3: sandbox (E2B/Modal) + humano + live-verify
   ▼  ⟵ el pipeline de dev ES el motor que la supervisora-runtime flexiona
```

**Traza A (existe):** *"mostrame disponibilidad de doctores en junio"* → supervisora: VER/vista → router: existe → **T1** → dominio Operar → deep-link `/operar/agenda?mes=2026-06`. Instantáneo.

**Traza B (auto-extensión):** *"si no confirma 24h antes → liberá cupo + avisá al de la lista de espera"* → supervisora (L1) interpreta grueso → reenvía la intención al **dueño de Operar** (no construye ella) → el dueño (L2) clasifica (flujo #7 sobre acciones existentes), resuelve contra sus EP → si hay motor de flujos = **T2** (tracking gratis); si "lista de espera" no existe = ese nodo **T3** → **propone el blueprint** (artefacto) → confirmás → construye (sandbox+humano+live-verify) → borrador tenant-scoped → live. Coordina por **evento** `cupo_liberado` (el dueño de Retener lo suscribe). HIPAA gate: aviso sin PHI por canal no-encriptado. Flywheel: si N clínicas lo piden → lift a EP → T2 para siempre.

## §8 · Estrés-test (4 casos borde · el núcleo aguantó, 4 refinamientos)

| # | Caso | Veredicto | Refinamiento |
|---|---|---|---|
| 1 | Dashboard cross-dominio (CAC: marketing+ventas+oper) | 🟡 hueco | **Split read/write (CQRS):** reads = dueño por **vantage/decisión**, componibles cross-dominio vía **read-models publicados** (no internals); writes/flujos = dueño por **outcome**. El core debe publicar read-models por dominio |
| 2 | "Soportá país nuevo / cambiá el cifrado PHI" | 🟢 + límite | **Techo de auto-extensión:** runtime topa en brand-extension; lo que toca **core invariante** NO se auto-construye → escala a `/pm-luana`. Nodo-por-nodo (país parametrizado=T2; algoritmo cifrado=T3+ core). La supervisora **detecta + escala**, nunca construye core |
| 3 | "Sacá el historial médico / agendá sin consentimiento" | 🟡 hueco | (a) "quitar/desactivar" NO es primitiva — es **operación de ciclo de vida** ortogonal a los 12 objetos; (b) **T0 inteligente (refuse-with-reframe):** rechaza lo que viola compliance CON razón legal + re-rutea al objetivo legítimo |
| 4 | "Cambiá la autonomía de un agente" | 🟢 + principio | **Separación de poderes:** un agente NO se auto-otorga autonomía; la gobierna el **humano vía Configuración**; restringir=T2 siempre, ampliar=decisión humana gateada (compliance); el agente **pide**, el humano **concede** |

## §9 · Riesgos / decisiones abiertas

| Tema | Estado |
|---|---|
| Motor de flujos durables (Cloudflare DW vs Temporal vs LangGraph+durabilidad) | spike pendiente (cornerstone B) |
| Formato del "chunk" (Pydantic Capabilities vs propio) | decisión de implementación |
| Generative UI (AG-UI/A2UI) vs schema-driven form-runtime actual | evaluar en A |
| Pricing exacto (per-empleado / outcome / packs) | decisión Chris sobre la marcha (arquitectura solo soporta entitlement+medición) |
| Read-models publicados por dominio | requisito arquitectónico (Caso 1) |

## §10 · Trayectoria B → A

- **B (ahora):** consolidar el motor para nosotros — árbol de capacidades/chunks · protocolo de intenciones · **motor de flujos durables como EP T2 (cornerstone)** · read-models por dominio · acción única + event bus (ya existe) · verificación real (ya cementado).
- **A (norte):** exponérselo al usuario vía supervisora — auto-extensión runtime (T1/T2/T3) · generative UI / WhatsApp Flows · grafos per-tenant · pricing por empleado/outcomes.
- **Insight:** el mismo músculo — el pipeline de dev ES el motor de la supervisora-runtime.

## §11 · Grounding vitalia + HIPAA (validado)

Los registros del router **ya existen** en vitalia: `SYSTEM-MAP.yaml` (3 zonas/12 cajas/functional_areas) + `ADR-vitalia-005` (5 dims cap · `nature: extension-point` = marcador T2 · `dev_preview`). HIPAA **agranda T0/T3**: campo "alergias"=PHI → T3 (pgcrypto+audit+dual-filter); "diagnóstico por WhatsApp" → T0 (ComplianceService bloquea PHI en canal no-encriptado).

## §12 · Cómo lo haríamos mejor (UX frontier-injertado)

Embedded > attached (no chat 50/50 fijo) · split adaptativo · propuesta como **artefacto en el panel de trabajo** (no burbujas) · T3 aterriza en **borrador tenant-scoped reversible** · WhatsApp Flows para UI liviana + deep-link a vista+filtro para densa.

## §13 · Sources

- [Forrester — Predictions 2026: AI Agents](https://www.forrester.com/blogs/predictions-2026-ai-agents-changing-business-models-and-workplace-culture-impact-enterprise-software/)
- [VC Cafe — The Year of the Agent Employee](https://www.vccafe.com/2026-ai-predictions-the-year-of-the-agent-employee/)
- [Artisan — Digital Workers / AI Employees](https://www.artisan.co/blog/digital-workers)
- [Anthropic — Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Pydantic AI — Capabilities](https://pydantic.dev/docs/ai/core-concepts/capabilities/)
- [AG-UI — Introduction](https://docs.ag-ui.com/introduction) · [A2UI v0.9 (Google)](https://developers.googleblog.com/a2ui-v0-9-generative-ui/)
- [Cloudflare — Dynamic Workflows](https://blog.cloudflare.com/dynamic-workflows/)
- [E2B](https://e2b.dev/) · [Modal — Best sandboxes 2026](https://modal.com/resources/best-code-execution-sandboxes-ai-agents)
- [AgentSkillOS (arXiv 2603.02176)](https://arxiv.org/abs/2603.02176)
- [LangGraph supervisor vs swarm](https://www.augmentcode.com/guides/swarm-vs-supervisor) · [orchestration vs choreography (orkes)](https://orkes.io/blog/workflow-orchestration-vs-choreography/)
- [The future of AI agents is event-driven (Confluent)](https://www.confluent.io/blog/the-future-of-ai-agents-is-event-driven/)
- [Generative UI 2026 (CopilotKit)](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026)
- [AI agent pricing 2026 (Monetizely)](https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models) · [Chargebee playbook](https://www.chargebee.com/blog/pricing-ai-agents-playbook/)
- [Vertical AI agents eating SaaS (ACTGSYS)](https://actgsys.com/en/blog/vertical-ai-agents-industry-specific-2026)
- [The new org chart / work chart (CIO)](https://www.cio.com/article/4060162/the-new-org-chart-unlocking-value-with-ai-native-roles-in-the-agentic-era.html)
- [Clarifying agents / underspecification (arXiv 2505.13360)](https://arxiv.org/html/2505.13360v2) · [Intent mismatch lost (arXiv 2602.07338)](https://arxiv.org/html/2602.07338v1)
- [WhatsApp Flows](https://helo.ai/resources/blog/whatsapp-flows) · [LatAm WhatsApp adoption](https://www.aurorainbox.com/en/2026/03/05/whatsapp-business-latam-adoption/)
- Internos: `PARADIGM.md` · `ADR-010-orquestacion-agentica.md` · `ADR-vitalia-005` · `vitalia/docs/architecture/SYSTEM-MAP.yaml` · MEMORY `[[luana-empleados-ia-vision]]`

## §14 · Decisión pendiente

- [ ] **Promover a ADR-platform** (evolución `PARADIGM.md` + `ADR-010`) + outcome platform + **stories derivadas por marca** (vitalia/nicolify primeras instancias) — vía recomendada (reset desde /pm-luana).
- [ ] **Refining directo** (si Chris prefiere ir a spec antes de ADR).
- [ ] **Park.**
- Luego: `/architect` diseña la implementación (fase B→A), arrancando por el **spike del motor de flujos durables**.

## §15 · Bitácora

- 2026-06-01 — Research v1 (/pm-luana): bundle inicial. Visión ratificada conversacionalmente (sesión 2026-05-31→06-01) + estrés-testeada con 4 casos borde. Pendiente decisión Chris sobre vía de promoción.
