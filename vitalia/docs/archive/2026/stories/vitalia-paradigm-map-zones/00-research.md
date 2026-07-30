<!-- voseo-allowed: research interno de organización, no user-facing -->
# 00-research — Propuesta de organización del mapa (nueva visión de producto)

> Story `vitalia-paradigm-map-zones` · state=idea · 2026-05-30
> Doctrina: `docs/architecture/luana-platform/PARADIGM.md` + `ADR-010` + rule `paradigm-arquitectura.md`.
> Esta propuesta **mejora** el draft `SYSTEM-MAP.yaml::zones` (sobre todo el rol de Valeria) y re-mapea el backlog Fase 2.

## 1. El problema concreto que destapó el prior-art scan

Las ~20 stories de Fase 2 (todas en `idea`) están nombradas por la taxonomía VIEJA: `vitalia-fase2-config-cuenta`, `…-config-onboarding-clinica`, `…-valeria-pacientes`, `…-lisa-*`, etc. **Reorganizar el mapa reorganiza el backlog.** Por eso esto es re-planificación, no solo un cambio visual del cockpit.

## 2. Refinamiento clave de la visión: ¿qué es Valeria en el mapa?

El draft del SYSTEM-MAP puso `boxes: [lisa, valeria, mateo, …]` en la zona Agentes. **Eso es incoherente con el paradigma:** Valeria es la **supervisora** (Plano 3 orquestación) — la cara conversacional con quien hablás. NO es una "caja de valor" del producto; es el **conductor** que enruta y compone sobre las cajas de los demás.

**Refinamiento (mejora sobre el draft):**

- **Valeria = supervisora = el chat lateral** (el sidebar con quien conversás, web + WhatsApp). NO ocupa una caja en la zona Agentes. Se pinta como el **conductor transversal** (sidebar del cockpit/shell + su runtime vive en Infraestructura → motor-agentico).
- **"Mi Día" (agenda + bookings)** — hoy `valeria.agenda` / `valeria.bookings` — pasa a **Mateo (Operar)**, que es el especialista operativo.
- La zona **Agentes = 5 cajas de especialistas** que el dueño "contrata": **Lisa · Mateo · Adrián · Lucas · Camila**. Valeria los orquesta.

> Esto además **alinea perfecto con el shell-organism ya shipped**: el Ribbon = los especialistas (tabs de workspace), y Valeria = el chat sidebar (el orquestador). El paradigma y la UI ya construida convergen.

## 3. Organización propuesta (final) — 3 zonas

### ZONA AGENTES (core · `user_visible: true`) — los trabajadores que el dueño "contrata"

| Caja | Subtitle | Absorbe (functional areas) |
|---|---|---|
| 🏥 **lisa** | Mi Clínica | marca · servicios · autoridad · equipo (doctores) · landing pública |
| 🗓 **mateo** | Operar (Mi Día) | agenda · bookings · pacientes-del-día *(ex `valeria.agenda/bookings`)* |
| 💼 **adrian** | Vender | embudo · inbox · crm · reactivación · outbound · propuestas |
| 📣 **lucas** | Marketing | atribución · bowtie · recomendaciones · referrals · campañas · mercado · resultados |
| 🌟 **camila** | Reputación | nps · followup · multiplicar/cohortes · voz |
| 🧭 **valeria** | *(supervisora — transversal, NO caja de valor)* | orquestación + composición multi-paso; runtime en Infra→motor-agentico; UI = chat sidebar |

### ZONA PLATAFORMA (supporting · `user_visible: true`) — transversal, se opera a mano (sin agente)

| Caja | Absorbe |
|---|---|
| 🔐 **acceso** | auth (Clerk, sesiones) + authz (RBAC, roles, scope por clínica) *(ex `config.auth` + `config.iam`)* |
| 🚀 **onboarding** | alta de clínica + wizard + provisioning *(ex `config.onboarding_clinic`)* |
| ⚙️ **configuracion** | cuenta/tenant · clínicas · conexiones · historial pacientes · panel admin · avanzado *(ex resto de `config.*`)* |

### ZONA INFRAESTRUCTURA (enabling · `user_visible: false`) — no-funcional / técnico

| Caja | Absorbe |
|---|---|
| 🛡️ **seguridad-cumplimiento** | cifrado pgcrypto PHI · audit log · dual-filter · tenant isolation · retention *(ex `config.compliance` + scaffolding)* |
| 📊 **observabilidad** | trace events · llm_calls · cost · pricing · OTel/Sentry |
| 🔧 **plataforma-tecnica** | design tokens/shell · payment rails · idempotency · eventos · IAM engine adoption · foundation |
| 🤖 **motor-agentico** | engine copilot/sales_agent · supervisor graph (Valeria) · RAG/Qdrant · prompt cache — RUNTIME, no feature |

## 4. Re-mapeo del backlog Fase 2 (lo que cambia para Chris)

| Story actual (idea) | Zona → caja nueva | Cambio |
|---|---|---|
| `vitalia-fase2-config-onboarding-clinica` | Plataforma → **onboarding** | sale de "config" |
| `vitalia-fase2-config-cuenta` | Plataforma → **configuracion** | — |
| `vitalia-fase2-config-conexiones` | Plataforma → **configuracion** | — |
| `vitalia-fase2-config-avanzado` | Plataforma → **configuracion** | — |
| `vitalia-fase2-lisa-compliance` | ⚠️ DECISIÓN: vista al cliente → Plataforma; enforcement → Infra→seguridad | split |
| `vitalia-fase2-valeria-pacientes` | ⚠️ DECISIÓN: "pacientes del día" → **mateo** (Operar); "historial médico" → configuracion/clínico | reasignar (Valeria ya no es caja) |
| `vitalia-fase2-lisa-doctores/-servicios/-landing-public` | Agentes → **lisa** | sin cambio de caja |
| `vitalia-fase2-adrian-*` (embudo/inbox/outbound/propuestas) | Agentes → **adrian** | sin cambio |
| `vitalia-fase2-lucas-*` (envuelo/lanzar/mercado/recursos/resultados) | Agentes → **lucas** | sin cambio |
| `vitalia-fase2-camila-*` (multiplicar/reactivar/reputacion/voz) | Agentes → **camila** | sin cambio |
| (agenda/bookings — ya `done`/`ready`) | Agentes → **mateo** | re-tag de `valeria.*` → `mateo.*` |

**Implicación:** las stories `config-*` se renombran a su zona/caja (ej. `vitalia-fase2-onboarding-clinica`, `vitalia-fase2-configuracion-cuenta`). Los `agent_*` mayormente conservan caja salvo Valeria→Mateo.

## 5. Decisiones abiertas (Chris ratifica antes de refining)

1. **Valeria = supervisora (no caja de valor) + Mateo = Operar/Mi Día.** ¿Confirmás esta reasignación? (es el corazón del refinamiento).
2. **`valeria-pacientes`:** "pacientes del día" → Mateo (operativo) vs caja clínica propia. ¿Dónde?
3. **`lisa-compliance` (vista compliance al cliente):** ¿Plataforma→configuracion (user-facing) con el enforcement técnico en Infra→seguridad, o todo Infra?
4. **Naming stories:** ¿renombramos las `config-*` a su caja nueva (más claro) o solo re-taggeamos el `agent_owner` y dejamos el slug? (recomiendo renombrar para coherencia).
5. **Cockpit (F3):** es tool cross-brand. ¿Lo hacemos en esta misma tanda (fase solo-bootstrap lo permite) o lo separamos a una tarea tool-scope?

## 6. Plan de migración (alto nivel · para /architect)

1. **F0 · Backlog:** renombrar/re-tag ~20 stories Fase 2 a zona/caja (git mv + checkpoint `map_zone`/`map_box`).
2. **F1 · Caps:** script que re-tag ~71 caps `agent_owner` config/infra → caja nueva (según `SYSTEM-MAP.zones.target_boxes.absorbs`); `user_visible` se deriva de la zona. Validar con `reconcile_capabilities.py`.
3. **F2 · SYSTEM-MAP:** promover `target_boxes` a `agents`/boxes de primer nivel; Valeria→supervisora; Mateo→Operar; deprecar pseudo-agentes `config`/`infra`. Bump `ADR-vitalia-005` (5ª dim) o nuevo `ADR-vitalia-006`.
4. **F3 · Cockpit (tool-scope):** MapView render por zona + 2 lentes (trabajadores/proceso) + Valeria como sidebar supervisor.
5. **F4 · Índice de acciones (Plano 2):** generador desde firmas del service layer + headers `# cap:` (posible diferir a story propia).

## 7. No-objetivos (para no sobre-ingeniar)

- NO construир el motor agéntico real (LangGraph supervisor) — eso es otra epopeya; acá solo el **mapa/taxonomía**.
- NO poblar campos que no se van a usar: `zone` es **derivada**, no se escribe por cap.
- NO tocar el engine `core/luana-core-*` (lift sería `/pm-luana`).
