# Outcome (platform) — Empleados-IA + auto-extensión

> Owner: `/pm-luana`. Outcome cross-brand que materializa ADR-013. Registra el trabajo derivado: spike de implementación + stories por marca. NO es spec ejecutable.

---
outcome_id: empleados-ia-auto-extension-platform
type: platform
status: accepted
created: 2026-06-01
owner: /pm-luana
adr: ADR-013-empleados-ia-auto-extension
source_story: docs/archive/2026/stories/empleados-ia-auto-extension/   # archivada 2026-06-02 (una user-story no es SSoT)
ssot_research: docs/architecture/luana-platform/empleados-ia-research.md   # SSoT vivo graduado
ssot_l2_design: docs/architecture/luana-platform/durable-flows-L2-design.md
consumers: [vitalia, nicolify]   # primeras instancias · resto hereda al bootstrap
---

## Qué cementa

Luana = sistema operativo de **empleados-IA vendidos por puesto** (cadena de valor: Base + Atraer/Vender/Operar/Retener) sobre **un solo motor que se auto-extiende** (12 primitivas × 5 tiers + router 2-niveles + flywheel + flujo durable de 1ª clase), coordinado por **3 modos** (coreografía / supervisora / handoff medido), con disciplina **SOLID** y **techo de auto-extensión** al core. Detalle: ADR-013 + `docs/architecture/luana-platform/empleados-ia-research.md` (SSoT vivo).

## Trayectoria B → A

- **B (ahora):** consolidar el motor para nosotros — árbol de capacidades runtime-consultable · read-models por dominio · router 2-niveles · **motor de flujos durables como EP T2 (cornerstone)** · protocolo de intenciones. (acción única + event bus ya existen.)
- **A (norte):** exponérselo al usuario vía la supervisora — auto-extensión runtime (T1/T2/T3) · generative UI / WhatsApp Flows · grafos per-tenant · pricing por empleado/outcomes.

## § Estado-ahora (foto honesta — snapshot 2026-06-02)

> Esta sección se desactualiza: es un snapshot, no un SSoT vivo. La verdad la dan los `state:` de las stories + el `status:` de las capabilities + el live-verify (DoD #37). Re-mapear con una pasada **read-only** `/pm-{brand}` antes de confiar en estos cuadros.

**El motor (platform):**

| Pieza | Estado |
|---|---|
| **L1 — motor de flujos durables** (`core/luana-core-flows`) | ✅ **DONE + migrated + live-verified** (persist+resume real en Postgres). **EN PAUSA y está bien:** NO es huérfana (la consumen por import 5 grafos scaffold), pero **todavía no tiene un consumidor de producto real** — fue inversión deliberada de cornerstone (research: "flujo durable = T2"). |
| **L2 — `FlowCompiler`/`FlowDefinition`/EP-19** (estático) | ⛔ **SUPERSEDED 2026-06-16 (ADR-015).** Reemplazado por **late-bound saga runtime** (planner LLM dinámico + plan-como-dato + compensaciones). SSoT vigente: `saga-runtime-design.md`. El compilador declarativo NO se construye; L1 se reusa intacto. |
| **Saga runtime** (dinámico, late-bound) | 🎨 **DISEÑADO 2026-06-16, build deferred.** SSoT: `saga-runtime-design.md` + `ADR-015`. Precondición de build: ≥2-3 tools de un dominio `live` + 1er saga hand-rolled (NO generalizar sin ejemplo — § Insight). |

**Vitalia — madurez por dominio (la barra de "sólido" = capability `status: live` + acción de negocio ejercida live, NO líneas de código).** El backend tiene mucho código transplantado del monolito original; LOC alto ≠ acción sólida. Caps `live` totales: 31/73 — pero se concentran en el **substrate** (plataforma/shell), no en acciones-de-agente.

| Dominio (agente) | Superficie real | Caps live | Story | Madurez |
|---|---|---|---|---|
| **Plataforma / Shell** (substrate) | platform · iam/auth · observability · admin · audit · workers · public_landing | platform 8 · shell-organism 3 · iam/auth 4 · observability 3 · admin 5 (live) | Fase 1 (11 stories) **done** | ✅ **SÓLIDO** — es el piso, live-verified |
| **Valeria · Agenda** (scheduling/operación) | `scheduling/` 38 py full-DDD | `scheduling.valeria-agenda` **live** | F2-S1 **done** (live-verify DoD #37) | ✅ **SÓLIDO** — la **única acción de negocio viva** |
| **Lisa · Doctores** (clinics) | `clinics/` 35 py full-DDD | clinics 1 live + 1 partial | F2-S8 **developing** (`e2e_live_run: pending_stack`) | 🚧 **EN CONSTRUCCIÓN** — el candidato más cercano a sólido (no done) |
| **Lisa · Marca/Servicios/Landing/Compliance** | `brand_studio/` 26 py · `compliance/` 13 py | brand_studio 1 live · compliance 0 | idea | 🟡 **SCAFFOLD** — backend transplantado, sin live |
| **Adrián · Inbox/Embudo/Outbound/Propuestas** | `sales_agent/` 36 · `crm/` 34 · `inbox/` 23 py | 0 (sales_agent 5 / crm 2 declaradas) | idea · bloqueado en **payment** | 🟡 **SCAFFOLD** — backend hondo, sin wire/live; service-blocker `payment` (refined, adapters listos sin wirear) |
| **Lucas · Mercado/Lanzar/Recursos/Resultados** | `marketing/` 38 py · `agentic/lucas/` grafo full-DDD | 0 (marketing 4 · agentic 5 declaradas) | idea · grafo `lucas_daily_analysis` scaffold | 🟡 **SCAFFOLD** |
| **Camila · Voz/Reactivar/Multiplicar/Reputación** | `fidelizacion/` 47 py full-DDD | 0 (1 declarada) | idea | 🟡 **SCAFFOLD** — backend hondo transplantado, sin live |
| **Mateo · Pacientes/Operación ("Mi Día")** | `patients`/`treatments` caps · transversal | 0 | idea | 🟡 **SCAFFOLD** |
| **Onboarding / Configuración** (wizard) | `copilot/workflows/wizard_onboarding_graph.py` (route + DTOs + state + 4 tools) | 0 (copilot 4 · onboarding declaradas) | idea | 🟡 **SCAFFOLD** — topología real, pero el LLM se ata "when wired" (su propio docstring) |

**Los 5 grafos "cableados" a L1 son scaffold/stubs** (nodos sin LLM real / rutas que no llaman al grafo), no acciones promovibles: `wizard_onboarding`, `treatment_followup_check`, `lucas_daily_analysis` (vitalia) + `cohort_enrollment`, `community_engagement` (comunify). Importan L1 → por eso L1 **no** es huérfana; pero **no se promueve lo que no está construido** (error ya cometido y corregido: proponer "promover `treatment_followup` a vivo").

**Comunify:** fuera del foco de esta retoma; sus 2 grafos (cohort/community) están en el mismo estado scaffold-wired-a-L1.

## § Insight capstone (el corazón de esta retoma — NO perderlo)

**Un flujo durable es el CAPSTONE de un dominio sólido, NO la próxima user-story.** Vive *encima* de las acciones de negocio (Plano 1) que compone; en el vacío no es nada. De ahí el orden correcto:

1. **Acciones sólidas de UN dominio** (capabilities `live` + live-verify), una por una.
2. **El flujo durable como coronación** que las amarra (y de paso ejercita/pule L1).
3. **Recién después de 1-2 flujos concretos, L2 generaliza** el patrón.

Corolarios duros:
- **NO** construir L2 ahora — sería generalizar sin un solo ejemplo.
- **NO** forzar un flujo durable sobre el scaffold actual — no hay piso de acciones sólidas; sería construir media Vitalia y de paso manosear L1.
- **NO** promover lo que es scaffold (un grafo con nodos stub no se "pone vivo"; se **construye** como cualquier story).
- Hoy el **único** dominio con piso para un capstone es **Valeria·Agenda**, y aun así un capstone necesita ≥2 acciones sólidas que amarrar — Agenda sola todavía no compone un flujo multi-paso que justifique durabilidad.

## § Protocolo de retoma

Cuándo y cómo volver a tirar del hilo empleados-IA (sin volver a suponer):

```
Disparador: un dominio X de Vitalia (Lisa, Adrián, Camila, Lucas, Mateo…)
            junta ≥2 acciones de negocio SÓLIDAS y verificadas live (cap status: live + DoD #37).
   │
   ├─ 1. Pasada READ-ONLY /pm-{brand}  → re-confirmar madurez real (no confiar en este snapshot).
   ├─ 2. Volvé acá (este outcome)       → el primer flujo durable de X es su CAPSTONE.
   ├─ 3. /pm-{brand}                    → refina la story del capstone (idea → refined).
   ├─ 4. /architect                     → arma el grafo HAND-ROLLED sobre L1 (NO L2 todavía;
   │                                        L1 = make_durable_checkpointer + thread_id, ya existe).
   ├─ 5. /dev-team → /auditor           → build + QA.
   └─ 6. live-verify DoD #37            → persist+resume real en Postgres, acción ejercida.

Después de 1-2 capstones hand-rolled concretos → recién ahí: generalizar el **saga runtime**
(`saga-runtime-design.md` / ADR-015 — late-bound dinámico, NO el L2 estático descartado) sobre el
patrón observado, no inventado.
```

Mientras tanto: **Chris sigue construyendo Vitalia a su ritmo**; el hilo empleados-IA queda **mapeado + parqueado** (la claridad vive en el repo, no en la memoria de la IA que se resetea). El roadmap empleados-IA **no avanza por su cuenta** — avanza cuando un dominio madura.

## Trabajo derivado (handoffs — NO los escribe /pm-luana)

| # | Trabajo | Owner | Estado |
|---|---|---|---|
| 1 | **Spike: motor de flujos durables** → recomendación LangGraph durable + Temporal escape + Cloudflare descartado | `/architect` (platform) | ✅ **DONE** 2026-06-02 (`docs/archive/2026/stories/empleados-ia-auto-extension/spike-durable-flows.md`, ratificado Chris; diseño L2 graduado a `docs/architecture/luana-platform/durable-flows-L2-design.md`) |
| 1b | **L1 — motor durable real (un-defer):** lift checkpointer provider a `core/luana-core-flows` + instalar `langgraph-checkpoint-postgres` + cablear 5 grafos (vitalia ×3, comunify ×2) + migraciones + downstream regression + live-verify. Proposal `2026-06-02-durable-flows-engine` (migrated). | `/architect` → `/dev-team` → `/auditor` | ✅ **DONE** 2026-06-02 (T-flows-1..5 wip/vitalia `c8551ed7..335ed390`; proposal migrated; downstream verde 463+182; live-verify DoD #37: persist+resume real en Postgres — vitalia 3 filas, comunify 8 filas; `07-merge.md` + `REVIEW-agentic.md`) |
| 1c | ~~**L2 — `FlowCompiler`/`FlowDefinition`/EP-19** (compositor declarativo estático)~~ | — | ⛔ **SUPERSEDED 2026-06-16 (ADR-015)** — dirección estática descartada. Ver 1d. |
| 1d | **Saga runtime** (late-bound dinámico): planner LLM + plan-como-dato + ledger + compensaciones + contingencias, sobre L1. Diseño técnico cementado esta sesión. | `/architect` (diseño DONE) → `/dev-team` (build futuro) | 🎨 **diseño DONE** 2026-06-16 · SSoT: `docs/architecture/luana-platform/saga-runtime-design.md` + `ADR-015` · build = user-story futura (precondición: piso de tools `live` + 1er saga hand-rolled) |
| 2 | Story derivada vitalia: primer **flujo durable capstone** sobre un dominio sólido (hand-rolled sobre L1) | `/pm-vitalia` | pendiente · **esperando dominio sólido** (NO post-L2 — ver § Protocolo de retoma). Hoy solo Valeria·Agenda es sólido; falta ≥2 acciones que amarrar |
| 3 | Story derivada nicolify: instanciar sobre su roster (Abel/Brenda/Christian/Sara/Norvil + Luana) | `/pm-nicolify` | pendiente |
| 4 | Read-models publicados por dominio (requisito del read/write split, caso borde 1) | `/architect` + builders | pendiente |
| 5 | Entitlement por empleado + medición de outcomes (soporte de packaging — pricing exacto TBD Chris) | `/pm-luana` + `/architect` | pendiente |

## Invariantes que el trabajo derivado debe respetar (de ADR-013)

- Un solo engine (personas/scopes, nunca motor por agente/marca).
- La supervisora reenvía intención, no construye en dominio ajeno (ownership por dueño).
- Coreografía por eventos = default; orquestación para ambiguo/PHI; directo = excepción medida.
- Cross-brand: etapa = interfaz estable (core); roster + procesos = extension (Liskov).
- Techo: core invariante → gate humano `/pm-luana`, nunca auto-construido.
- Separación de poderes: autonomía la concede el humano, no el agente.

## Bitácora

- 2026-06-01 — /pm-luana creó el outcome desde ADR-013 (ratificado Chris). Stories derivadas quedan como handoffs a brand PMs + spike a /architect.
- 2026-06-02 — retoma empleados-IA (sesión limpia, desde wip/vitalia). Pasada **read-only** `/pm-vitalia` mapeó la madurez real por dominio (evidencia: story states + cap `status` + grafos). Se enriqueció el roadmap con **§ Estado-ahora** (foto honesta: L1 done-en-pausa / L2 diseñado-deferred / Vitalia = 1 acción sólida [Valeria·Agenda] + resto scaffold) + **§ Insight capstone** (flujo durable = coronación de dominio sólido, no próxima story) + **§ Protocolo de retoma** (disparador = dominio con ≥2 acciones live → capstone hand-rolled sobre L1). NO se construyó L2, NO se forzó flujo sobre scaffold. El handoff `docs/architecture/luana-platform/empleados-ia-HANDOFF-next-session.md` se pliega aquí (cumplido).
- 2026-06-16 — **pivote de dirección del motor de flujos** (sesión de diseño, ratificado Chris). El diseño L2 estático (`FlowDefinition`/`FlowCompiler` pre-declarado por marca) **se supersede** por **late-bound saga runtime** (planner LLM dinámico compone el plan al vuelo sobre tools, plan-como-dato, compensaciones backward + contingencias forward). Disparador: Chris pidió el modelo Claude-Code (acciones=tools, el modelo entrega el plan, se guarda la "orden" multi-paso async hasta terminar, con riesgos+acciones en el propio plan). Validado contra SOTA junio-2026 (Late-Bound Sagas / SagaLLM / ALAS — patrón con nombre publicado). Cementado: **ADR-015** + **`saga-runtime-design.md`** (diseño técnico profundo: data structures, planner loop 3-nodos, reparto core/marca, determinismo en replay, ejemplo Adrián, EP-19 redefinido `saga_tool_register`, open questions, validators, build-readiness). L1 se reusa intacto. **Cero código** — build = user-story futura (precondición: piso de tools `live` + 1er saga hand-rolled). Sin nuevo estado ni eje; el roadmap empleados-IA sigue parqueado avanzando por madurez de dominio.
