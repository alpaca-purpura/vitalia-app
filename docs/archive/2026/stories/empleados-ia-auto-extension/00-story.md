# 00-story.md — Empleados-IA + Auto-extensión (paradigma platform)

> Owner: `/pm-luana`. El QUÉ y el PORQUÉ de la visión unificada, antes de bajar a implementación.
> NO es spec ejecutable. La implementación (fase B→A) se diseña después con `/architect` + stories derivadas por marca.

---
story_id: empleados-ia-auto-extension
type: platform-paradigm                            # no es ui/agentic/service buildable aún — es visión cross-brand
module: platform (core + extension-sdk)
capability: null                                   # platform-level
links:
  paradigm: "../../../architecture/luana-platform/PARADIGM.md"
  adr_010: "../../../architecture/luana-platform/ADR-010-orquestacion-agentica.md"
  research: "./00-research.md"
  memory: "luana-empleados-ia-vision (MEMORY.md)"
---

## Job-To-Be-Done

**Como** dueño de un negocio de servicios (clínica, agencia, etc.)
**Quiero** un equipo de "empleados-IA" que opere mi negocio por proceso (atraer, vender, operar, retener) — usable a mano y también de forma conversacional — y que **cuando le pido algo que el sistema todavía no hace, lo entienda, me lo proponga y lo construya**
**Para** correr todo mi go-to-market con un equipo digital que crece con mis necesidades, sin contratar devs ni esperar releases.

## Por qué importa

2026 es "el año del agente-empleado": los **agentes verticales se comen al SaaS** porque venden *trabajo terminado*, no asientos ([Forrester](https://www.forrester.com/blogs/predictions-2026-ai-agents-changing-business-models-and-workplace-culture-impact-enterprise-software/), [VC Cafe](https://www.vccafe.com/2026-ai-predictions-the-year-of-the-agent-employee/)). Luana puede ser eso, **nativo, vertical y para LatAm** — y diferenciarse con un sistema que es **determinista usable sin agente** (moat en salud regulada) **+ auto-extensible** (el usuario pide → el sistema construye, gobernado). Es la convergencia de las dos caras: el **producto** (empleados-IA por puesto) y el **motor** (sistema que se auto-extiende).

## Outcome esperado

- El cliente compra y combina "empleados" por puesto (cadena de valor), con una **Base** obligatoria (identidad + configuración + supervisora).
- El cliente opera el sistema a mano O le pide a la supervisora (Valeria/Luana) que orqueste; puede pedir capacidades nuevas en lenguaje natural.
- El sistema clasifica cada pedido (12 primitivas × 5 tiers), lo orquesta/configura/construye según corresponda, y **aprende** (flywheel: lo que muchos piden se vuelve estándar).
- Cross-brand: el esqueleto (etapas + supervisor + base) es invariante (~60% core); el roster + procesos varían por marca (~40% extension).

## Antecedentes / Contexto

- Evoluciona `PARADIGM.md` (3 planos: Sistema · Acción única · Trabajadores) + `ADR-010` (orquestación agéntica).
- Consistente con `ADR-vitalia-005` (Valeria = supervisora, no caja de valor).
- Nicolify ya tiene roster + shell agentic-first; vitalia tiene SYSTEM-MAP 3 zonas/12 cajas. Son las 2 primeras instancias.

## Out of scope (explícito)

- El **cómo implementarlo** (secuencia B→A, qué OSS se monta, qué se toca del core/Extension SDK) — eso es fase posterior con `/architect`.
- El **pricing exacto** (per-empleado vs outcome vs packs) — decisión de Chris sobre la marcha; la arquitectura solo debe soportar entitlement por empleado + medición de outcomes.
- Reescribir PARADIGM.md / ADR-010 ahora — primero se ratifica este bundle.

## Riesgos / Asunciones

- **Riesgo:** auto-extensión runtime sin barandas → islas / caos / brechas compliance. **Mitigación:** 12 primitivas + 5 tiers + router 2-niveles + techo de core + separación de poderes + anti-orphan CONN (ya cementados acá).
- **Riesgo:** "cada agente su motor" → N motores duplicados. **Mitigación:** UN engine, personas/scopes (invariante doctrina).
- **Asunción:** un **motor de flujos durables** como extension-point T2 es construible y es el cornerstone de B (validar con spike).

## Próximo paso

`→ Chris decide vía de promoción (ADR-platform + outcome + stories derivadas por marca, o refining directo). Luego /architect diseña la implementación B→A.`
