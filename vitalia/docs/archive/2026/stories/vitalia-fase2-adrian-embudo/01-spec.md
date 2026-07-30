---
story_id: vitalia-fase2-adrian-embudo
brand: vitalia
release: F3
type: ui-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: crm
capability_target: crm/adrian-embudo
cap_change_type: new
architecture_pattern: ADR-vitalia-004
state: refining
po_ux_version: 3
ratified_by_chris: true                            # ★ "go al spec" (Chris 2026-06-03) — spec funcional ratificado
ratified_visual_by_chris: true                     # ★ Chris vio + aprobó el mockup + pidió replicarlo (ADR-003)
ratified_visual_at: 2026-06-03
ratified_visual_iter: 2                             # v3 → v3.1 (5 ajustes de Chris)
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/mockups/embudo-v3.html
design_spec_section: "§ Design specification (D.0–D.16)"   # contrato visual fiel al mockup para el architect/builder
last_updated: 2026-06-03
phi_classification: non_phi
locked_decisions:
  module_home: extend_crm
  stage_machine: vitalia_local_extension_sdk      # consume sustrato agéntico engine + vocabulario/prompts vitalia
  consume_engine_agentic_substrate: true          # closer-studio + AgentStateCheckpoint + transitions + diagnose + KPIs (propuesta, confirmar)
  pipeline_model: conversation_first              # Adrián mueve; drag manual = override (propuesta, confirmar)
  lead_score: glass_box_rule_based                # recencia + señales + etapa, sin ML
  detail_pattern: page_entitysubnavbar            # ★ Chris ratificó opción C (página con URL propia)
  reservado_side_effect: stub_msw
  lead_detail_scope: core_2_tabs_resumen_historial  # ★ v3: colapsado de 3→2 (Score=bloque, no tab) research-driven
  new_lead_surface: route_workspace_no_modal      # ★ v3: /adrian/embudo/nuevo (hoja con URL) + redirect highlight
  column_order: stage_age_desc                    # ★ v3: RN-17, lo más viejo-en-etapa arriba (no por fecha creación)
  manual_move: drag_or_dropdown_with_guardrail    # ★ v3: RN-4 ampliado (cómo + reglas)
  sla_table: stage_age_7_7_5_14                   # ★ v3 propuesta: RN-11 (confirmar números)
  auto_freeze: inactivity_14d_or_2x_sla_or_30d    # ★ v3 propuesta: RN-13
  board_scope: hot_only_decidio_no_to_frozen      # ★ v3 propuesta: RN-18 (confirmar)
  frozen_surface: subtab_recuperar                # ★ v3.1: V4 = sub-tab hermana /adrian/recuperar (2do nivel, no anidada); Adrián corto plazo, Camila largo plazo
  channel_registry: shared_channel_meta_badge     # ★ v3.1: ChannelBadge + channel-meta reutilizable cross-solución (§ Registro de canales)
  manual_move_feeds_agent: true                    # ★ v3.1: RN-4.1 — override + razón se inyecta al checkpoint del agente, lo alimenta (no lo rompe)
  lead_detail_tabs_in_bar: true                    # ★ v3: vistas Resumen/Historial en EntitySubNavBar (como Staff), NUNCA Shadcn Tabs en el body
  card_data_provenance: read_model_projection      # ★ v3: señales/micro-log/badges = proyección de estado+log, no texto libre (§ Procedencia)
sub_categories_coverage:
  happy: covered
  negative: covered
  edge: covered
  adversarial: covered
  race_condition: covered
  concurrent_users: covered
  network_failure: covered
  empty_state: covered
  large_dataset: covered
  accessibility: covered
  i18n: covered
open_decisions: []                                # ★ todas resueltas 2026-06-03 (ver § Decisiones). Chris afina algo más antes de cerrar refined → /architect
resolved_decisions:
  scope: one_story                                # 1 sola story (no split S4a/S4b)
  consume_engine_substrate: true
  conversation_first: true
  sla_days: {interesado: 7, calificando: 7, consulta: 5, plan: 14}
  auto_freeze: {no_response_days: 14, hard_days: 30}
  dataset_canonico: accepted
  board_decidio_no_to_frozen: true
  new_lead_surface: route_hoja
  recuperar: {surface: sibling_subtab, name: "Recuperar"}
---

# F2-S4 — vitalia-fase2-adrian-embudo · 01-spec UNIFICADO (v2)

> Sub-tab **Embudo** de Adrián: la **superficie de supervisión** sobre Adrián (empleado-IA que vende). Adrián conversa, califica, puntúa y mueve los leads por un funnel clínico de 6 etapas; la coordinadora observa, toma el control y resuelve los trabados; Valeria coordina. Detalle del lead = **página con URL propia** (patrón `EntitySubNavBar`, opción C). Extiende el módulo `crm`. Lead = **non-PHI**.
>
> Soporta investigación: `research/{00-propuesta-embudo-agentico, 01-legacy-pipeline, 02-core-engine, 03-agentic-best-practices, 04-detail-entry-pattern}.md`.

## § Context

- **Release:** F3. **Módulo:** `crm` (EXTEND — el FE shipped `crm-shared/api/use-leads` ya pega a `/api/v1/vitalia/crm/leads`; Lead+lead_service+lead_dto+lead_repository ya viven en `crm`). NO se crea `sales_pipeline`.
- **Insertion point:** sub-tab `Adrián → Embudo`. Reemplaza `EmbudoPlaceholder.tsx` (ratificado 2026-05-26) por la vista real.
- **Caja/zona:** Agentes · Adrián (cap `crm/adrian-embudo`). La acción de transición vive en el service layer (Plano 2); el agente la invoca.
- **Lead = non-PHI** (`crm/domain/lead.py`): aislamiento `tenant_id` único, sin dual `clinic_id`, sin pgcrypto. hipaa-lite full-set NO aplica (toca `lead_*`, no `patient_*`). Audit log SÍ en transiciones (business event).
- **Detalle = página (opción C ratificada):** ruta `/adrian/embudo/[leadId]/{resumen|historial}` (★ v3: 2 tabs) con `EntitySubNavBar` (reusa el componente shipped de `vitalia-fase2-lisa-doctores`, ADR-vitalia-004 § D-1). URL propia → deep-link + reusable cross-surface + agentic.

### Decisiones cementadas
| # | Decisión | Estado |
|---|---|---|
| Módulo home | EXTEND `crm` | ✓ ratificado (batch 1) |
| Lead | non-PHI · tenant-isolation + audit | ✓ |
| Side-effect `→reservado` | stub MSW | ✓ ratificado (batch 1) |
| Lead detail | **2 tabs** (Resumen[Datos+Score]·Historial) ★ v3 research-driven | 🟡 propuesta (era 3, confirmar) |
| **Detalle = página URL propia (C)** | EntitySubNavBar | ✓ **ratificado (UX)** |
| Stage machine | vitalia-local + consumir sustrato agéntico engine | 🟡 propuesta (confirmar) |
| Modelo | conversation-first (Adrián mueve, drag = override) | 🟡 propuesta (confirmar) |
| Score | glass-box rule-based | 🟡 propuesta (confirmar) |

### Out-of-scope (anti-creep)
- ❌ Editor de customización de etapas per-vertical (defaults dental sirven MVP).
- ❌ Side-effect real pago/agenda en `→reservado` (STUB; dep `payment-adapter-mvp` solo `refined`).
- ❌ Tabs Propuestas (F2-S6) / Time-in-stage dedicado / Tools-registry.
- ❌ AI-suggest next-stage automático · bulk-action · lead-merge.
- ❌ Intercepting-route overlay del detalle (mejora futura opcional; esta story = página C directa).
- ❌ Reactivación Camila (desbloqueada por esta story; build en `camila-reactivar`).

## § Modelo agéntico (el alma del embudo)

Tres roles operando un sistema:
- **Adrián (IA, autónomo):** conversa por WhatsApp/IG, califica, detecta señales de compra, puntúa, y **mueve el lead de etapa** según esas señales. Registra cada acción (atribuida).
- **Coordinadora (humano, supervisa):** observa el board, **toma el control** de una conversación, le da **instrucción oculta** a Adrián, hace **nudge**, y **override** manual de etapa cuando hace falta. Resuelve los **congelados**.
- **Valeria (supervisora, coordina):** resume el día, **avisa** lo importante (leads enfriándose, congelados, depósitos), propone acciones, y puede **deep-linkear** a la página de un lead.

**Autonomía gated por tipo de acción** (RN-9): Adrián autónomo en bajo riesgo (mover etapa, agendar, enviar info); requiere OK humano en alto riesgo (cobrar, descuento, cualquier cosa clínica).

## § Vistas — exactamente qué muestra cada una

### V1 · Tablero / directorio — `/adrian/embudo` (vista por defecto)

**Embudo es una sub-tab de Adrián** (misma fila L3 que `Inbox · Embudo · Recuperar · Outbound · Propuestas`). El Tablero NO tiene SubSubTabsBar — es directamente el board. El EntitySubNavBar (`[‹ Embudo] | nombre | Resumen·Historial`) aparece solo en **modo workspace** (página del lead V3 / nuevo lead V5), reemplazando el contenido del board. **Recuperar (V4) es su propia sub-tab hermana** `/adrian/recuperar` (★ v3.1 — Chris: a 2do nivel, no anidada en Embudo).

**Header del board:**
- Título "Embudo" + chip `🤖 operado por Adrián`.
- Toggle **Kanban | Lista** (persistido `?view=`).
- Toggle **Modo Adrián | Todos** (filtra los que opera Adrián vs incluye los tomados por humano).
- **Filtros:** origen (canal) · doctor · etiquetas · rango fecha · score · operador.
- **+ Nuevo lead** (CTA).

**KPI strip (tiny):** `N activos` · `🤖 N Adrián` · `🙋 N humano` · `🔥/🌡️/❄️ hot/warm/cold` · `score prom` · `⭐ tasa depósito %` · `🧊 N congeladas` (link a V4).

**Columnas del funnel (RN-18 — board = solo HOT):** 4 etapas activas (Interesado · Calificando · Consulta agendada · Plan presentado) + Reservado (terminal-éxito). `Decidió no` y los congelados NO son columnas → van a la hoja Congelados (V4). Cada columna = `emoji + label` · `count · Σ valor` · badge de estancados (ámbar/rojo si hay leads sobre SLA, RN-11). **Orden interno: antigüedad-en-etapa descendente** (RN-17).

**LeadCard** (lo que muestra cada tarjeta):
1. Nombre **PII-masked** (`María G███`) + badge **operador** (`🤖 Adrián` cian / `🙋 Tú` verde).
2. `Σ valor estimado` + **canal origen con ícono + color de marca de la red social** (★ v3.1 — `ChannelBadge`, ver § Registro de canales). WhatsApp verde · Instagram rosa/gradient · Meta azul · Web neutro · Referido ámbar.
3. **Score 0-100** como **gráfico de dona compacto** (★ v3.1 — reemplaza la barra ancha; ahorra espacio horizontal) con color por valor (verde≥70 / amarillo 40-69 / rojo<40) + el número al centro.
4. **Chips de señales de compra** detectadas (`💬 preguntó precio`, `⏰ urgencia`, `💬 presupuesto ok`) — máx 2 visibles + `+N`.
5. **Time-in-stage SLA:** dot + texto (`3d`) — verde dentro de SLA, ámbar >1.5× mediana de la etapa, rojo >2× (RN-11). Border-left = temperatura.
6. **Micro-log de la última acción de Adrián** (atribuido): `🤖 Adrián movió a Calificando · hace 2h`.
7. **Badge de estado especial** por etapa: `💳 Esperando pago` / `✅ Depósito recibido` (Reservado), `↻ Camila reactiva 90d` (Decidió no).

Card **clickeable** → navega a la página del lead (V3).

**Estados:** loading (skeleton 6 cols) · success · empty (V1-empty: 6 cols vacías + empty central + CTA "Crear primer lead") · error (banner + Reintentar) · dragging (card fantasma + drop zone resaltada).

### V2 · Lista — `/adrian/embudo?view=lista`

Tabla (mismo data set, vista densa): **Lead** (masked) · **Etapa** (badge) · **Canal** · **Score** · **En etapa** (dot SLA) · **Últ. actividad** · **Operador** (🤖/🙋) · **Doctor**. Filtros = los del header. Columnas ordenables. Paginada (25/pág; el conteo por etapa = total real, no el de la página). Click fila → página del lead (V3).

### V3 · Página del lead — `/adrian/embudo/[leadId]/{resumen|historial}` (★ opción C · **2 tabs**)

> **Cambio v3 (research-driven, 2026-06-03):** colapsamos de 3 tabs a **2**. Convención del rubro (HubSpot limita a 5 tabs y arranca con 2; Clientify/Pabau/LeadMAX usan cabecera + 2 zonas con el **timeline al centro**; el **Score nunca es tab propio** — es bloque/badge junto a los datos). Ver `research/05-lead-detail-benchmark.md`.

**Cabecera del workspace (siempre visible — la "lead-card dinámica"):**
- `EntitySubNavBar (modo workspace)` — **la barra superior ES el switcher** (igual que la página del doctor en Staff, ADR-vitalia-004 § D-1): `[‹ Embudo]` (volver al board) · `avatar + Nombre (masked) + badge etapa` · **vistas-ruta Resumen · Historial al costado del nombre**. ★ **NO hay tabs en el cuerpo** — la hoja NO lleva Shadcn `Tabs` internas; el cuerpo renderiza solo el contenido de la vista activa (Resumen **o** Historial), derivada de la URL.
- Franja resumen bajo la barra: **canal** (WA/IG/Web/Referido) · **procedimiento de interés** · **valor estimado** · **badge temperatura** 🔥/🌡️/❄️ + **score 0-100** · **"última actividad hace X"** · botón **Tomar control**.
- Cada vista = su propia URL (`/resumen`, `/historial`) — deep-linkable, reusable desde Inbox/Valeria. Default `/resumen`.

**Vista Resumen** (`/resumen` · fusiona Datos + Score — la convención del rubro):
- Bloque **Datos del lead:** Contacto (masked) · Origen (canal + campaña) · Interés (servicio) · Valor estimado · Doctor asignado · Etiquetas · Etapa actual.
- Bloque **Estado del agente (autonomía):** "🤖 Adrián la atiende" + botón **Tomar control** · línea de autonomía ("Puede: mover etapa·agendar·enviar info / Necesita tu OK: cobrar·descuentos·clínico") · acciones **💬 Instrucción oculta** · **⚡ Nudge** · control **Mover de etapa** (RN-4, dropdown con allowed_next).
- Bloque **Score (glass-box):** score + temperatura + barra + **breakdown** explicable (factores que suman/restan: `preguntó precio +25`, `respondió <5min +15`, `campaña pagada +10`, `sin agendar 2d −2`). Nota: "Reglas + recencia, sin caja negra. Adrián lo recalcula en cada mensaje."
- **Empty-states honestos** (la ficha nace casi vacía y crece): "Aún sin presupuesto presentado", "Aún sin doctor asignado" — NO se ocultan, se muestran vacíos con su placeholder.

**Vista Historial** (`/historial` · el corazón de la ficha — lo único que crece turn-by-turn):
- **Línea de tiempo** cronológica que **mezcla**: mensajes de la conversación (WA/IG), transiciones de etapa, acciones del agente, y eventos (presupuesto presentado, depósito) — todo **atribuido** (`🤖 Adrián` / `🙋 humano` / `💬 lead`).
- Link **"Abrir conversación en el Inbox →"** (F2-S3).

**Crecimiento en el tiempo (qué se llena cuándo):** la página **nace** con cabecera + canal/procedimiento + 1 evento de timeline ("Adrián saludó"). El **Historial** se llena turn-by-turn. El **Score** aparece/sube al calificar. El **Presupuesto** entra como evento del timeline al presentar el plan (no como superficie desde el día 1). El doctor se asigna al agendar. Nada de esto exige tabs nuevos — todo aterriza en Resumen (bloques) o Historial (eventos).

**Estados V3:** loading (skeleton tabs) · success · error · **not-found (404)** → "Lead no encontrado" (cross-tenant o inexistente, mensaje genérico, RN-1).

### V4 · Recuperar — **sub-tab hermana de Embudo** `/adrian/recuperar` (★ v3.1 — 2do nivel, no anidada)

> **Cambio v3.1 (feedback Chris):** Recuperar NO es sub-sub-tab de Embudo — es una **sub-tab propia de Adrián**, a la misma altura que `Inbox · Embudo · Outbound · Propuestas`. Tiene su URL `/adrian/recuperar`. El KPI 🧊 del Tablero linkea acá (cambia de sub-tab). Embudo queda limpio = solo el board.
>
> **Horizonte (división de responsabilidades agéntica):** acá vive la recuperación **de corto plazo** que opera **Adrián** (el lead recién cayó, todavía caliente-tibio). La recuperación **de largo plazo** (cohortes 90d, campañas win-back, nurture) es de **Camila** → story `camila-reactivar` (separada, esta la desbloquea). No duplicar.

Lista segmentada por `frozen_reason`:
- **🧊 Recién congelados** (`inactividad_lead` / `sin_respuesta_presupuesto` / `agente_trabado`): nombre masked · etapa donde se enfrió · `frozen_reason` · antigüedad. Por cada uno: **AI Diagnose** (recomendación estructurada de Adrián, ej. "trabado en el pago → enviá el link directo") + acciones **Reactivar** (con objetivo) / **Tomar control**. (Consume `diagnose` del engine.)
- **🚫 Decidió no reciente** (RN-18): nombre masked · `closure_reason` · entregado a la cohorte Camila (90d). En esta vista solo se **muestra** + opción **Reactivar** puntual; las campañas de cohorte son de Camila.

**Reactivar** → el lead vuelve al **Tablero** en su última etapa (RN-13) + audit. **Estados:** loading · empty ("Sin leads para recuperar 🎉") · success.

> **Decisión abierta #8 (microcopy + scope):** nombre del sub-sub-tab — **"Recuperar"** (recomendado) vs "En riesgo" vs "Rescate". Y si esta vista entra en **esta** story o se difiere a S4b (§ Decisiones abiertas #3 alcance).

### V5 · Nuevo lead — **hoja con ruta propia** `/adrian/embudo/nuevo` (★ no modal)

> **Cambio v3 (2026-06-03):** NO es modal. Es una **hoja/página con URL propia** (`/adrian/embudo/nuevo`), misma familia que la página del lead. Razón: el "espacio de creación" debe existir como ruta direccionable para que **Valeria (o el propio Adrián) pueda crear un lead por pedido del usuario** y deep-linkear a ese espacio ("creá un lead para María del IG → `/adrian/embudo/nuevo?prefill=...`"). Un modal no tiene URL → no es alcanzable por el agente.

**Render:** `EntitySubNavBar (modo workspace)` `[‹ Embudo] · Nuevo lead` (sin tabs). Form (RHF+Zod): **Nombre*** · **Canal*** (WhatsApp/IG/Web/Referido/Otro) · **Teléfono / Email** (≥1) · **Etapa inicial** (default Interesado) · **Servicio de interés** (autocomplete tratamientos) · **Etiquetas** · **Notas**.

**Alcanzable por:** (1) CTA "+ Nuevo lead" del header del board · (2) deep-link de Valeria/Adrián (futuro: `?prefill=` con datos pre-cargados desde la conversación).

**Submit → redirect + highlight:** `POST /crm/leads` → redirige a `/adrian/embudo?view=kanban&highlight={leadId}` → la card recién creada **se resalta** (ring + pulse 3s) en su columna inicial, con auto-scroll a ella. Así el usuario ve dónde aterrizó sin perder el contexto del board. Cancelar → vuelve al board sin crear.

> **Decisión liviana abierta (§ Decisiones abiertas #6):** ¿`/adrian/embudo/nuevo` como **ruta-workspace** (recomendado — consistente con `[leadId]`, y ADR-vitalia-004 §3.1.1 reserva los SubSubTabs para vistas persistentes discretas, no para "crear" que es transitorio) **vs** como **sub-sub-tab** en la SubSubTabsBar? Recomiendo ruta-workspace; el botón "+ Nuevo lead" puede vivir igual en el header/SubSubTabsBar como **acción**.

## § Dataset canónico (realista — para el mockup "data acordada")

> Proponé/ajustá. Una vez ratificado, el mockup C usa exactamente esto. Moneda PEN (tenant Sanaré). Stages + SLA mediana (días) entre paréntesis.

**Etapas dentales (6) + SLA verde≤ (RN-11):** `Interesado(7d)` · `Calificando(7d)` · `Consulta agendada(5d)` · `Plan presentado(14d)` · `Reservado(—, terminal-éxito)` · `Decidió no(—, terminal · vive en V4 si RN-18)`. Ámbar = sobre SLA; rojo = al doble (o ≥14d sin respuesta → ámbar global).

| Lead (masked) | Etapa | Canal | Valor | Score | En etapa | Operador | Señales | Última acción Adrián |
|---|---|---|---|---|---|---|---|---|
| María G███ | Interesado | WhatsApp | S/ 7k | 48 🟡 | 2d 🟢 | 🤖 | preguntó precio | saludó · 2h |
| Carlos P███ | Interesado | Instagram | S/ 4k | 33 🔴 | 9d 🟠 | 🤖 | — | sin respuesta · 4d |
| Sofía R███ | Interesado | Meta | S/ 12k | 41 🟡 | 5d 🟢 | 🤖 | preguntó precio | info enviada · 1d |
| Ana V███ | Calificando | WhatsApp | S/ 8k | 64 🟡 | 3h 🟢 | 🤖 | urgencia · presupuesto ok | movió a Calificando · 1h |
| Pedro M███ | Calificando | WhatsApp | S/ 6k | 52 🟡 | 8h 🟢 | 🙋 | — | (humano tomó control · 20m) |
| JP Méndez███ | Consulta agendada | WhatsApp | S/ 11k | 71 🟢 | 1d 🟢 | 🤖 | 📅 jue 5 jun 15:00 Dra. Rojas | agendó · ayer |
| Rosa V███ | Plan presentado | Referido | S/ 12k | 78 🟢 | 23d 🔴 estancado | 🤖 | — | seguimiento enviado · 3d |
| Camila B███ | Reservado | WhatsApp | S/ 8k | — | — | 🤖 | ✅ depósito S/ 2k | cobró depósito · hoy 09:12 |
| Mateo L███ | Reservado | Web | S/ 7k | — | — | 🤖 | 💳 esperando pago | envió link · 3h |
| Iván S███ | Decidió no | — | — | — | — | — | razón: precio | ↻ Camila reactiva 90d |
| Patricia C███ | Decidió no | — | — | — | — | — | razón: sin disponibilidad | ↻ cohorte reactivación |

**Congeladas (V4):** Lucía R███ (Calificando · "no responde hace 5 turnos" · diagnose: "baja intención, ofrecé consulta gratis") · Diego F███ (Plan presentado · "trabado en el precio" · diagnose: "enviá opción de financiación").

**Score breakdown de María (Datos/Score):** `preguntó precio +25 · respondió <5min +15 · campaña pagada +10 · sin agendar 2d −2 = 48`.

## § Reglas de negocio

- **RN-1 · Tenant isolation** — toda query filtra `tenant_id` (único, Lead non-PHI). Cross-tenant → 404 genérico, sin leak.
- **RN-2 · PHI firewall** — el embudo opera **datos de interés** (procedimiento/presupuesto/agenda/canal), NUNCA clínicos. La IA deriva lo médico a un profesional. Contacto enmascarado en vistas compartidas.
- **RN-3 · Transición agent-driven (default)** — Adrián mueve `stage` según señales (qualification + buying_signals + score). Cada transición → `lead_stage_transition` (from/to/triggered_by/reason/occurred_at/score) sync.
- **RN-4 · Override manual de etapa — el CÓMO + las reglas** (★ ampliado v3). La coordinadora puede mover un lead de etapa de **dos formas**: (a) **drag-drop** de la card entre columnas del board (`@dnd-kit`); (b) control **"Mover de etapa"** (dropdown) en la página del lead (V3 · Resumen). Reglas:
  - **A etapa adyacente permitida** (`allowed_next`) → transición directa, sin fricción. `triggered_by=manual_override` + audit.
  - **Saltando etapas hacia adelante** (no adyacente) → modal de confirmación + **razón obligatoria**. Backend valida; inválido → `422 {allowed_next}` + rollback + toast (SC-2).
  - **Retroceder etapa** → permitido **con razón** (ej. "el lead pidió reprogramar"). Audit `triggered_by=manual_override`.
  - **`→Reservado` por drag/manual → BLOQUEADO.** Reservado = depósito real (webhook, RN-5). Drag a Reservado muestra tooltip "Reservado se alcanza con el depósito" y rebota. No hay "ganar manualmente".
  - **`→Decidió no` manual** → modal `closure_reason` obligatorio (RN-7) + marca cohorte Camila.
  - **Override de ETAPA ≠ Tomar control de la CONVERSACIÓN.** Mover etapa a mano NO pausa a Adrián (sigue operando la conversación). Para pausar al agente es **Tomar control** (RN-10). Son acciones independientes.
  - **Permiso:** rol coordinadora. **Concurrencia:** optimistic lock por `version` → `409` si otro operador movió primero (SC-5). Toda transición manual → `lead_stage_transition` row con `triggered_by=manual_override` + razón.
  - **★ El override alimenta al agente, no lo rompe (RN-4.1, v3.1).** La razón obligatoria del movimiento manual se **inyecta como contexto/señal en el checkpoint del agente** (`override_context`): Adrián la **incorpora** y ajusta su próximo paso (mensaje/acción) con esa info — NO se cancela, NO se reinicia, NO se confunde. Ej.: humano mueve a `Plan presentado` con razón "ya le pasé el presupuesto por fuera del chat" → Adrián NO vuelve a preguntar precio; encara el seguimiento del presupuesto. El handover queda asentado en el Historial (atribuido `🙋 humano → 🤖 Adrián`). Esto es distinto de **Tomar control** (RN-10): el override mueve la etapa y le da contexto; el agente **sigue operando** salvo que además tomes el control de la conversación.
- **RN-5 · `→Reservado` = depósito** — se alcanza por **webhook de pago** (esta story: STUB). Badge `💳 esperando pago` → `✅ depósito recibido`. Es el WON real, no la promesa.
- **RN-6 · `→Consulta agendada`** consume Agenda (F2-S1) para crear el slot (stub aquí).
- **RN-7 · `→Decidió no`** requiere `closure_reason` + marca cohorte reactivación (Camila).
- **RN-8 · Sin atajo de calificación** — todo lead pasa por intake (NO el bypass outbound B2B del legacy; riesgo clínico).
- **RN-9 · Autonomía gated** — bajo riesgo (mover/agendar/info) autónomo; alto riesgo (cobrar/descuento/clínico) requiere OK humano.
- **RN-10 · Takeover preserva contexto** — tomar control pausa a Adrián sin perder checkpoint; devolver genera handover summary.
- **RN-11 · Time-in-stage SLA** (★ ampliado v3, research-driven — `research/06-pipeline-sla-benchmark.md`). Cada etapa activa tiene un **SLA en días-en-etapa**; la card muestra dot + texto (`3d`) **verde** dentro de SLA, **ámbar** cuando supera el SLA, **rojo** al doble. El supervisor ve el conteo de estancados por columna. Además, señal global **"sin actividad"**: ≥14 días sin respuesta del lead → ámbar aunque el SLA de etapa no se haya vencido (la que dispare primero manda). Tabla SLA propuesta (dental, ticket alto, ciclo total 60-90d):

  | Etapa | SLA (verde ≤) | Ámbar > | Rojo > | Fuente / criterio |
  |---|---|---|---|---|
  | Interesado | 7d | 7d | 14d | speed-to-lead 0-5min; calificar <1h; qualif 7-14d |
  | Calificando | 7d | 7d | 14d | qualif 7-14d (rework deal-aging) |
  | Consulta agendada | 5d | 5d | 10d | ventana hasta que ocurre la consulta |
  | Plan presentado | 14d | 14d | 21d | presupuesto sin respuesta; seguimiento Día1/Día2 + margen (14-30d Proposal) |
  | Reservado | — | — | — | terminal-éxito (sin SLA) |
  | Decidió no | — | — | — | terminal (sin SLA) |

  > **Adrián es IA → speed-to-lead es instantáneo** (responde en segundos). El SLA aquí mide cuánto **avanza** el lead por etapa, no cuánto tarda el primer toque.
- **RN-12 · Atribución total** — todo mensaje/movimiento registra `sender_source` (auto/human_direct/human_instruction).
- **RN-13 · Auto-freeze — el pipeline es solo para lo HOT; los fríos salen a la hoja Congelados** (★ ampliado v3, research-driven). El **board Kanban muestra solo leads activos/calientes**. Un lead **sale automáticamente** de las columnas activas hacia la **hoja Congelados (V4)** cuando se cumple **cualquiera**: (a) **≥14 días sin respuesta** del lead en una etapa activa; (b) **días-en-etapa > 2× el SLA** de su etapa (RN-11); (c) **regla dura: 30 días sin actividad** → freeze sí o sí; (d) Adrián se trabó (no sabe cómo seguir). Al congelar se setea `frozen_reason ∈ {inactividad_lead, sin_respuesta_presupuesto, agente_trabado}` + audit. **Reactivación:** cualquier señal de interés del lead (responde / agenda / abre link) → **vuelve automático** al board en su última etapa; Camila corre la cadencia de reactivación (90d). `is_blacklisted` → excluido de todo (no entra ni a Congelados). Respaldo: Pipedrive "rotting" reset-por-actividad; umbral stale 14d / muerto 30d / 1.5-2× mediana (Outreach, rework deal-aging).
- **RN-14 · Toggle persiste URL** (`?view=`). **RN-15 · i18n** — `formatMoney(tenant.currency)` (PEN/MXN/…), Spanish neutro.
- **RN-16 · Detalle direccionable** — `/adrian/embudo/[leadId]/{tab}` es ruta con URL propia; refresh/deep-link renderiza la página; `leadId` = UUID (nunca PII en URL).
- **RN-17 · Orden de las cards en cada columna** (★ nuevo v3, research-driven). Default = **antigüedad-en-etapa descendente: la card más vieja / más cerca de vencer su SLA va ARRIBA** (priorizar lo que se está por enfriar). **NO** se ordena por fecha de creación. Selector "Ordenar por" en el header: `Antigüedad en etapa` (default) · `Score` · `Valor` · `Última actividad`. El **drag manual sirve solo para cambiar de columna (etapa)** — NO para reordenar dentro de una columna (el orden siempre refleja prioridad real, no preferencia manual que se desactualiza). Convención Pipedrive ("lo urgente arriba") / HubSpot board sort.
- **RN-18 · Alcance del Tablero hot vs Recuperar** (★ propuesta v3 — § Decisiones abiertas #5). El **Tablero** (V1) muestra: **4 etapas activas** (Interesado · Calificando · Consulta agendada · Plan presentado) + **Reservado** (terminal-éxito, visible para celebrar/ver depósitos; auto-archiva a los 14d). **`Decidió no` NO es columna del Tablero** → el lead sale a la sub-tab **Recuperar** (V4, segmento `🚫 Decidió no reciente`, cohorte Camila). Los congelados (RN-13) también viven en Recuperar, no en el Tablero. Así el Kanban queda limpio = solo lo accionable. *(Si Chris prefiere mantener `Decidió no` como 6ª columna visible, se revierte sin costo.)*
- **RN-19 · Sub-tabs de Adrián + rutas reservadas** (★ v3.1). Adrián expone sub-tabs L3: `Inbox · Embudo · Recuperar · Outbound · Propuestas`. `/adrian/embudo` = Tablero directo (sin SubSubTabsBar). Slugs reservados **bajo embudo** (estáticos, resuelven antes que el dinámico): `/nuevo` (V5, alta). `/adrian/embudo/[leadId]/{resumen|historial}` = workspace del lead, `leadId` = **UUID** (RN-16 — nunca colisiona ni lleva PII). `/adrian/recuperar` = sub-tab hermana (V4).

## § Procedencia de los datos (de dónde sale cada cosa que ves en la card)

> Respuesta a "¿cómo poblás esto?". **Principio:** la LeadCard es una **proyección read-only** del estado estructurado del lead + el log de actividad atribuido. **Nada se tipea a mano.** El board NO inventa: lee campos que el agente/eventos ya escribieron.

| Elemento de la card | Campo / fuente | Quién lo escribe | En ESTA story |
|---|---|---|---|
| **Operador** 🤖/🙋 | `lead.operated_by` (`agent`\|`human`) | el agente al operar; **Tomar control** (RN-10) lo flipea a `human` | real (derivado del checkpoint del agente — sustrato engine) |
| **Score 0-100 + temperatura** | derivado glass-box (recencia + señales + etapa) | recalculado server-side en cada mensaje/evento (RN-11/Score) | real (regla determinista vitalia-local, sin ML) |
| **Chips de señales de compra** | `lead.buying_signals[]` (enum: `pregunto_precio`, `urgencia`, `presupuesto_ok`, …) | **detección de intención del sales_agent** (consume `intent_detector` del engine) escribe la señal al parsear cada turno de la conversación | runtime real = el agente lo detecta; **mockup/demo = se siembra del § Dataset**. Depende de que Inbox F2-S3 / sales_agent esté live; si no, seed |
| **Micro-log última acción** | la fila más reciente de `lead_activity` / `lead_stage_transition` (RN-3, RN-12) | **cada** acción (agente o humano) escribe una fila atribuida (`sender_source`) | real — el mismo audit trail que registra transiciones; la card muestra la última |
| **Time-in-stage (dot SLA)** | derivado: `now − stage_entered_at` vs SLA de la etapa (RN-11) | calculado en read-time (no es campo) | real (cálculo) |
| **Badge 💳 esperando / ✅ depósito** | `lead.deposit_status` (`pending`\|`received`) | **webhook de pago** (RN-5) | **STUB MSW** en esta story (el webhook real = `payment-adapter-mvp`, solo `refined`) |
| **Badge ↻ Camila reactiva 90d** | derivado de `lead.closure_reason` + `reactivation_cohort_at` | al `→Decidió no` (RN-7) | real (campo + fecha); la campaña en sí la corre Camila |

**Resumen honesto de lo no-real en ESTA story:** (1) `deposit_status` = stub MSW; (2) `buying_signals` = sembradas del dataset si el agente conversacional aún no está live (cuando Inbox/sales_agent estén, las escribe el agente). Todo lo demás es proyección real de estado/log.

## § Prior art applied
- **Engine consultado:** `core/luana-core-crm` (api/pipeline, lifecycle_service, lifecycle_transitions, scoring) + `core/luana-core-sales-agent/closer_studio` (stop/resume/nudge/diagnose/kpis + `AgentStateCheckpointModel.current_stage`) — **presente y byte-idéntico al legacy** (ver `02-core-engine.md`). Propuesta: **consumir el sustrato agéntico** (closer-studio + checkpoint + transitions + diagnose + KPIs) + vocabulario/prompts dentales vitalia (Extension SDK, patrón EP-15). NO co-optar `LifecycleStage` marketing.
- **Reused vitalia:** `crm/{domain/lead, lead_service, lead_dto, lead_repository}` (EXTEND) · FE `crm-shared/api/use-leads` + `EntitySubNavBar` (de doctores) + `EmbudoPlaceholder` (anchor visual).
- **`@dnd-kit/core ^6.3.1`** ya instalado (drag override). **Nicolify closer-studio = gone** (reset) — Kanban brand-local.
- **Learnings:** patrón stub+MSW de F2-S1 (service-blockers).
- **Benchmark externo (v3):** ficha de lead `research/05-lead-detail-benchmark.md` (HubSpot/Clientify/Pabau/LeadMAX/Pipedrive → 2 tabs + score-bloque) · SLA/freeze/orden `research/06-pipeline-sla-benchmark.md`.
- **Net-new:** funnel clínico 6 etapas (vertical-specific) + SLA dental + auto-freeze rule.

## § Mapa funcional

**Happy path:** (1) la coordinadora entra a Embudo, ve el board con leads que Adrián movió solo + alertas de Valeria. (2) Clic en María → su **página** (Datos). (3) Lee score glass-box + historial; ve que Adrián la atiende. (4) Valeria sugiere ofrecer la promo; acepta (o toma control). (5) Si quiere, override manual de etapa (con razón si salta). (6) Vuelve al board ("‹ Embudo").

**Bifurcaciones:**
```
Lead avanza
├─ Adrián mueve (agent-driven) → transición + audit                          [SC-1]
├─ humano override válido → transición + audit (manual_override)             [SC-1b]
├─ humano override saltando etapas → confirmación+razón → 422 si inválido    [SC-2]
├─ →Reservado → stub pago → badge esperando/recibido                          [SC-1]
├─ →Decidió no → modal razón → cohorte Camila                                 [SC-1c]
├─ 2 operadores mismo lead → optimistic lock 409                             [SC-5]
├─ tenant switch / cross-tenant → cancela / 404                              [SC-3, SC-4]
Carga
├─ con leads → board/lista                                                    [SC-1,6]
├─ 0 leads → empty + CTA                                                      [SC-8]
├─ 1000+ → counts reales + lista paginada                                     [SC-9]
└─ fetch falla → banner + retry                                              [SC-7]
Navegación al detalle
├─ clic card → /adrian/embudo/{id}/resumen (página, URL propia)              [SC-detalle]
├─ deep-link/refresh /{id}/historial → renderiza página directo              [SC-deeplink]
└─ tab change → cambia ruta (/resumen↔/historial)                            [SC-10 a11y]
Crear lead
├─ "+ Nuevo lead" → /adrian/embudo/nuevo (ruta-hoja, URL propia)             [SC-nuevo]
└─ submit → redirect /embudo?highlight={id} → card resaltada en su columna   [SC-nuevo]
Card se enfría
├─ ≥14d sin respuesta / >2× SLA / 30d sin actividad → auto-freeze → V4       [SC-freeze]
└─ lead responde → reactivar → vuelve al board en su etapa                   [SC-freeze]
```
**RN:** RN-1..18 arriba. **AC:** AC-1..18 (board hot real · toggle persiste · orden por antigüedad-en-etapa · transición+audit · override manual cómo+reglas · reservado badge · lista filtrable/paginada · página detalle 2 tabs con URL propia · deep-link renderiza página · nuevo lead ruta-hoja + highlight · auto-freeze + reactivación · cross-tenant 404 · empty/loading/error · a11y · mobile · i18n · congelados+diagnose).

## § Gherkin scenarios (4 base + 7 sub-cat mandatory)

### SC-1 · happy — Adrián mueve a Reservado (stub) + audit
given lead `L1` en `listo` operado por Adrián · when Adrián (o el stub de simulación) ejecuta `PATCH /crm/leads/L1/stage {to:"reservado", triggered_by:"agent"}` + webhook stub de pago · then `stage=reservado` persistido + `lead_stage_transition` row + badge `✅ depósito`/`💳 esperando` + KPI tasa-depósito recalcula. **playwright:** true · graders: e2e + state_check(stage, transition row).

### SC-1b · happy — override manual válido (drag + razón) alimenta al agente
given `L1b` en `calificando` operado por Adrián · when la coordinadora arrastra a `consulta-agendada` (etapa permitida) + escribe razón "ya coordinamos la cita por teléfono" · then transición `triggered_by=manual_override` + `lead_stage_transition` row con la razón + **`override_context` inyectado al checkpoint del agente** + Adrián **sigue operando** ajustando su próximo paso (no reinicia, no re-pregunta lo ya resuelto) + handover asentado en Historial (`🙋 → 🤖`). **playwright:** true · **BE** `test_manual_override_feeds_agent_context.py`.

### SC-2 · negative — override saltando etapas → 422 + rollback
given `L2` en `interesado` (allowed_next=[calificando,decidio-no]) · when humano arrastra a `reservado` · then confirmación → backend 422 `{allowed_next}` → rollback + toast "Etapa permitida: Calificando" + audit `failed_stage_transition`. **playwright:** true.

### SC-3 · edge — tenant switch mid-acción → cancela sin leak
given operador en el board · when TenantSwitcher redirige · then sin `PATCH`; board del nuevo tenant; 0 leads del anterior. **playwright:** true.

### SC-4 · adversarial — deep-link a lead de otro tenant → 404
given operador T1 conoce `leadId` de T2 · when navega `/{T1}/adrian/embudo/{leadId_T2}/datos` · then 404 "Lead no encontrado" + audit `cross_tenant_attempt`, sin leak. **playwright:** false (BE) · `test_cross_tenant_lead_block.py`.

### SC-5 · race_condition — 2 operadores mismo lead → 409
given `L3` version v · when A mueve (→v+1) y B mueve con v · then A 200, B 409 + refetch + toast. **BE** `test_stage_transition_optimistic_lock.py`.

### SC-6 · concurrent_users — 2 tenants en paralelo
given T1+T2 cargan board · then cada uno solo sus leads; RQ keys segmentadas. **playwright:** true (2 contexts).

### SC-7 · network_failure — fetch/PATCH timeout
given board · when (a) GET timeout (b) PATCH timeout · then (a) banner+Reintentar (b) rollback+toast. **playwright:** true.

### SC-8 · empty_state — 0 leads
then 6 columnas vacías + empty central + CTA "Crear primer lead". **playwright:** true.

### SC-9 · large_dataset — 1200 leads
then counts reales por columna + Kanban con scroll virtualizado / Lista paginada, sin congelar. **playwright:** true (perf).

### SC-10 · accessibility — navegación tabs + drag teclado
given foco en card/tab · when teclado (drag: Space+flechas+Esc; tabs EntitySubNavBar: Arrow/Home/End) · then aria-live anuncia movimiento + mismo efecto que mouse + axe-clean. **playwright:** true + axe.

### SC-11 · i18n — currency + neutro
given tenant PEN vs MXN · then `formatMoney` correcto + Spanish neutro. **playwright:** true.

### SC-detalle/deeplink — página del lead con URL propia (2 tabs)
given board · when clic card María · then ruta `/adrian/embudo/maria/resumen`, EntitySubNavBar pinta nombre+tabs (Resumen·Historial), render Resumen con bloques Datos+Score. when refresh en `/maria/historial` · then renderiza la página (tab Historial) directo (no 404, no board). **playwright:** true.

### SC-nuevo — alta de lead = ruta-hoja + redirect con highlight
given board · when clic "+ Nuevo lead" · then ruta `/adrian/embudo/nuevo` (URL propia, EntitySubNavBar `‹ Embudo · Nuevo lead`, sin Dialog). when completa form válido + submit · then `POST /crm/leads` → redirige a `/adrian/embudo?view=kanban&highlight={id}` → la card nueva aparece en la columna inicial **resaltada** (ring+pulse) con auto-scroll. when cancela · then vuelve al board sin crear. **playwright:** true.

### SC-freeze — auto-freeze por inactividad + reactivación
given lead `L4` en `calificando`, última respuesta del lead hace 15d (>14d) · when corre el sweep de freeze (o se evalúa al cargar) · then `is_frozen=true` + `frozen_reason=inactividad_lead` + sale de la columna activa + aparece en V4 Congelados + audit. when el lead responde (señal de interés) · then `is_frozen=false` + vuelve al board en `calificando` + audit `reactivated`. **BE** `test_auto_freeze_and_reactivate.py` + **playwright** (V4 visible).

**N/A:** ninguna sub-categoría.

## § Matriz de cobertura
| Ítem | Tipo | SC | Verificación REAL |
|---|---|---|---|
| Bif Adrián mueve · RN-3 | branch | SC-1 | transición real (agent) → fila stage + transition row |
| Bif override válido · RN-4 | branch | SC-1b | drag+razón → transición + audit (manual_override) |
| Override alimenta agente · RN-4.1 | rule | SC-1b | razón → `override_context` en checkpoint + Adrián ajusta sin reiniciar |
| Bif override inválido · RN-4 | branch | SC-2 | drag saltando → 422 + estado DB sin cambio |
| Bif →Reservado · RN-5 | branch | SC-1 | stub pago → badge + fila stage=reservado |
| Bif →Decidió no · RN-7 | branch | SC-1c | modal razón → closure_reason en DB + cohorte |
| Bif cross-tenant · RN-1 | branch | SC-4 | deep-link ajeno → 404 + audit |
| Bif 2 operadores · RN-6/lock | branch | SC-5 | 2 PATCH → 200/409 + estado consistente |
| Bif 0/1200 leads | branch | SC-8/9 | empty CTA / counts reales paginado |
| Nav detalle URL propia · RN-16 | branch | SC-detalle | clic → URL cambia + página; refresh → página |
| RN-11 SLA | rule | SC (board) | seed >2× mediana → dot rojo + conteo estancados |
| RN-12 atribución | rule | SC-1/10 | cada move → sender_source correcto |
| Nav nuevo lead · V5/RN-16 | branch | SC-nuevo | "+ Nuevo lead" → `/nuevo` (URL) → submit → redirect+highlight card |
| Auto-freeze · RN-13 | rule | SC-freeze | 15d sin respuesta → is_frozen + sale del board + V4; lead responde → vuelve |
| Orden columna · RN-17 | rule | SC (board) | seed mixto → card más vieja-en-etapa arriba |
| Board hot scope · RN-18 | rule | SC (board) | `Decidió no` no es columna → aparece en V4 |
| AC a11y | accept | SC-10 | tabs+drag teclado + axe |
| AC i18n | accept | SC-11 | PEN vs MXN |

**Huecos:** ninguno. **SC huérfanos:** ninguno.

## § Estados visuales
(board: loading/success/empty/error/dragging + card-highlight post-alta · lista: loading/success/empty/error · página lead: loading/success/error/404 · página nuevo lead `/nuevo`: idle/submitting/error · V4 congelados: loading/empty/success). Tabla detallada en V1-V5 arriba.

## § Registro de canales / redes sociales (★ v3.1 — reutilizable cross-solución)

> Chris: "las fuentes (Instagram, WhatsApp…) deben tener su propio ícono + color de la red social, y guardarlo en una parte reutilizable porque será común referenciar redes sociales en toda la solución."

**Decisión:** un **registro único de metadatos de canal** (label · ícono · color de marca · color-soft) consumido por un componente `ChannelBadge` compartido. NUNCA hardcodear el color/ícono de un canal en cada vista (anti-duplication). Lo referencian Embudo, Inbox, Outbound, Analytics, Sales Agent, etc.

| Canal | Color marca | Ícono |
|---|---|---|
| WhatsApp | `#25D366` | logo WhatsApp |
| Instagram | gradient `#E1306C → #F77737` | logo IG |
| Meta / Facebook Ads | `#1877F2` | logo Meta |
| Web | `#475569` (neutro) | globo |
| Referido | `#F59E0B` | persona |
| TikTok | `#000000` | logo TikTok |
| Otro | neutro | etiqueta |

**Hogar (propuesta — prior-art scan pendiente `/architect`):** `vitalia/frontend/src/lib/channels/channel-meta.ts` (mapa) + `components/shared/channel/ChannelBadge.tsx` (molécula). **Candidato a lift cross-brand** → `core/@luana/ui-kit` o consumir del engine `core/luana-core-channels` (que ya existe para format/intent) — escalar a `/pm-luana` si aplica. Iconografía: set de marca (no emoji) en prod; el mockup usa aproximación.

## § Componentes (reuse > new)

**Átomos Shadcn (reuse `components/ui/*`):** `Button` · `Badge` · `Card` · `Table` · `Tooltip` · `Select` · `Input` · `Textarea` · `Label` · `Avatar` · `Progress` (barra de score) · `Skeleton` · `ScrollArea` · `Separator` · `Command`/`Popover` (autocomplete servicio). **NO** `Dialog` (el modal de nuevo lead pasó a ruta-hoja).
**Tokens (reuse `app/globals.css`):** `--agent-adrian` (color firma Adrián) · temperatura (`--success`/`--warning`/`--destructive` para hot/warm/cold + dots SLA) · gradient mariposa del shell. NO inventar HSL.
**Moléculas compartidas (reuse `components/shared/...`):** `EntitySubNavBar` ★ (de doctores, workspace lead/nuevo) · `TogglePill` (Kanban|Lista) · `EmptyState` · `PiiMaskedSpan`. **NEW compartidas (reutilizables cross-solución):** `ChannelBadge` + `channel-meta` (§ Registro de canales) · `ScoreDonut` (gráfico de dona).

| Componente | Path | Reuse/NEW |
|---|---|---|
| `EntitySubNavBar` | `components/shared/shell-organism/EntitySubNavBar.tsx` | **reuse** (de doctores) ★ |
| `TogglePill`,`EmptyState`,`PiiMaskedSpan` | `components/shared/...` | reuse |
| átomos Shadcn (lista arriba) | `components/ui/*` | reuse |
| `AdrianEmbudoView` (board client root) | `features/adrian/components/embudo/` | NEW |
| `KanbanBoard`+`PipelineColumn`+`LeadCard` | idem | NEW (@dnd-kit) |
| `ScoreDonut` (dona compacta) · `ChannelBadge` (ícono+color marca) | `components/shared/` | NEW compartidas ★ |
| `LeadsTable` (vista Lista) · `EmbudoHeader/Filters/Metrics` · `SortBySelect` | idem | NEW |
| `OverrideReasonDialog` (justificar movimiento manual → alimenta al agente, RN-4.1) | idem | NEW |
| `NewLeadPage` (ruta-hoja `/nuevo`, RHF+Zod) | `features/adrian/components/embudo/nuevo/` | NEW (ruta, no modal) ★ |
| `LeadWorkspace`+`{Resumen,Historial}Tab` (2 rutas) | `features/adrian/components/embudo/lead/` | NEW (página, 2 tabs) ★ |
| `LeadSummaryHeader` (cabecera workspace: canal·valor·temp·score·últ.actividad) | idem | NEW |
| `ScoreBreakdown` (glass-box, **bloque** dentro de Resumen — no tab) | idem | NEW |
| `RecuperarView` (sub-tab `/adrian/recuperar`) + `FrozenLeadRow` | `features/adrian/components/recuperar/` | NEW (consume diagnose) |
| `use-leads` | `crm-shared/api/use-leads.ts` | reuse (extend) |
| `use-embudo-board`·`use-lead`·`use-lead-stage-mutation`·`use-frozen`·`use-diagnose`·`use-create-lead` | `features/adrian/api/` | NEW |

## § Design specification (★ contrato visual — fiel al mockup `mockups/embudo-v3.html`)

> **SSoT visual ratificado por Chris (2026-06-03).** El builder DEBE reproducir esto. El mockup `embudo-v3.html` es la referencia ejecutable; esta sección lo formaliza componente por componente con tokens/medidas/estados exactos. Donde el mockup aproxima (wrapper con ancho fijo 330px, íconos de canal como 2 letras), la nota lo indica + apunta a la fuente de producción.

### D.0 · Tokens (espejo de `vitalia/frontend/src/app/globals.css` — NO inventar)
| Token | Light (HSL) | Uso |
|---|---|---|
| `--primary` / ring | `198 99% 49%` (#01B2F8 cian) | CTAs, foco, highlight, URL-accent |
| `--accent` | `287 53% 37%` (púrpura) | gradient mariposa (logo, Valeria) |
| `--agent-adrian` | `198 99% 49%` | identidad Adrián (board chip, donut activo, bordes workspace) |
| `--agent-adrian-soft` | `197 90% 89%` (dark `198 60% 20%`) | fondos suaves Adrián (badge operador, tab activa, diagnose) |
| `--agent-valeria` | `287 53% 37%` | sidebar Valeria (gradiente con accent) |
| `--agent-camila` | `244 84% 32%` (dark `244 80% 78%`) | etiquetas de reactivación (cohorte) |
| `--muted`/`--muted-foreground`/`--border` | `240 5% 96%` / `240 4% 46%` / `240 6% 90%` | superficies, texto secundario, líneas |
| status | emerald `#10b981` · amber `#f59e0b` · red `#ef4444` | score/SLA/temperatura/depósito |
Dark mode: clase `.dark` con los overrides del mockup. Todo color de canal/red social NO sale de aquí → § Registro de canales.

### D.1 · Anatomía del shell (barras, de arriba a abajo)
| Capa | Alto | Specs |
|---|---|---|
| TopBar global | `h-12` (48px) | `bg-card` `border-b`; logo 24px gradient `primary→accent`; "Vitalia · Clínica Sanaré ▾"; estado "en vivo" + toggle tema. **Producción:** TenantSwitcher real (ADR-vitalia-004). |
| Valeria (sidebar izq) | full-height, **ancho real = splitter resizable 3 estados** | mockup usa `330px` fijo (aprox). Header `h-14`, avatar 36px `val-grad`, lista mensajes, composer "Pregúntale a Valeria… ⌘K ➤". **Producción:** portar `valeria-chat-sample.html` + splitter (`shell-mockup-per-component.md § wrapper fidelity`). |
| Ribbon (L2) | `h-10` (40px) | `Lisa · Adrián · Lucas · Camila · Mateo` + `Configurar` (ml-auto). Activo (Adrián) = `text-agent-adrian` + `border-b-2` color adrian. |
| SubTabsBar (L3) | `h-9` (36px), `gap-4` | `Inbox · Embudo · Recuperar · Outbound · Propuestas`. Activo = `font-medium text-foreground` + `border-b-2` adrian + `pb-2`. **Recuperar** lleva badge count `rounded-full bg-muted text-[10px]`. |
| EntitySubNavBar | `h-11` (44px) | **solo en workspace** (lead/nuevo); ver D.7. En Tablero/Recuperar NO se renderiza. |
| URL chip bar | `py-1.5` | `bg-muted/40`, `font-mono text-[10px] text-muted-foreground`; muestra la ruta de la vista (board/recuperar/`{id}/{vista}`/nuevo). |
| Content | `p-4`, scroll | área de la vista activa. |

### D.2 · Tablero — header + KPI strip
- **Header:** título "Embudo" + chip `🤖 operado por Adrián` (`bg-agent-adrian-soft text-agent-adrian rounded-full px-2 py-0.5 text-xs`). Subtítulo muted text-xs. A la derecha: **toggle pill `Kanban | Lista`** (`rounded-full bg-muted p-0.5`; activo `bg-card shadow-sm font-medium`), selector "Ordenar: **Antigüedad en etapa ▾**", botón **+ Nuevo lead** (`bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-xs font-medium`).
- **KPI strip:** fila de chips `text-[11px] px-2 py-1 rounded-md bg-card border`: `N activos` · `🤖 N Adrián` · `🙋 N tú` · `🔥/🌡️/❄️` · `score prom` · `⭐ tasa depósito` · botón `🧊 N congeladas →` (navega a Recuperar).

### D.3 · PipelineColumn
- Grid `grid-cols-5 gap-3 min-w-[1080px]` (scroll-x). **Producción:** columnas `min-w-280` desktop (RN responsive); en mobile scroll horizontal.
- Header de columna: `emoji + label` (`font-medium text-xs`) + `N · S/Xk` (`text-[11px] text-muted-foreground`). Reservado lleva ⭐ y una nota `text-[9px] italic`: "arrastrar aquí = bloqueado (se gana con el depósito)".
- Cuerpo: `space-y-2`, `min-h-[40px]`. Empty `text-[11px] italic "— vacío —"`.
- Es **drop target** (D.10). Drop hover → `outline 2px dashed primary` + fondo `primary/.04`.

### D.4 · LeadCard (anatomía exacta)
Contenedor: `rounded-md border border-border bg-card p-2.5 border-l-2`; `border-left-color = temperatura` (hot `#f43f5e` · warm `#f59e0b` · cold `#64748b`). `draggable=true`. Cursor pointer; hover `ring-1 ring-primary/40`.
Layout = fila `flex items-start gap-2`:
- **Columna izquierda (`flex-1 min-w-0`):**
  1. Nombre (`font-medium truncate`) + `✨ nuevo` (`text-[10px] text-primary`) si highlight.
  2. `ChannelBadge` (D.6) + `· valor` (`text-muted-foreground text-[11px]`).
  3. Chips de señales (D.6 chip) — máx 2 + `+N` (`bg-muted text-muted-foreground`).
  4. SLA: `● en etapa Xd · SLA Nd` (dot `h-2 w-2 rounded-full` + texto `text-[10px]`), color verde/ámbar/rojo (RN-11).
  5. Badge especial (Reservado): `💳 Esperando pago` (amber-soft) / `✅ Depósito recibido · S/X` (emerald-soft), `rounded-full text-[10px]`.
- **Columna derecha (`flex flex-col items-center gap-1 shrink-0`):** badge **operador** (arriba) + **ScoreDonut** (abajo).
- **Footer micro-log:** `border-t mt-1.5 pt-1.5 text-[10px] text-muted-foreground truncate`: `🤖 Adrián · {acción} · {hace X}` o `🙋 Tú · …`. Es la última fila del `lead_activity` (§ Procedencia).
- **Estados:** default · hover (ring) · dragging (`opacity .4`) · highlight (`outline 2px primary` + `ringpulse 1.1s ×3`). Reservado: sin donut/SLA, con badge.

### D.5 · ScoreDonut (reemplaza la barra)
SVG `34×34`, `viewBox 0 0 34 34`, círculo `r=10 stroke-width 4`: track `stroke=hsl(var(--muted))`, arco `stroke = color por score`, `stroke-linecap round`, `transform rotate(-90)`, `stroke-dasharray=2πr`, `dashoffset = c·(1−score/100)`. Número centrado `font-size 10 font-weight 700 fill currentColor`. **Colores:** `≥70 #10b981` · `40-69 #f59e0b` · `<40 #ef4444`. Sin score (Reservado/terminal) → no se renderiza.

### D.6 · ChannelBadge + Signal chip
- **ChannelBadge:** ícono `h-4 w-4 rounded` con `bg = color de marca` (Instagram = gradient `135deg #F77737→#E1306C→#833AB4`) + glyph blanco `text-[7px] font-bold` + nombre `text-muted-foreground`. Mapa de colores en § Registro de canales. **Producción:** logos de marca reales (no 2-letras); el mockup aproxima con iniciales (Wa/Ig/f/We/Re).
- **Signal chip:** `text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400`.
- **Operador:** `🤖 Adrián` → `bg-agent-adrian-soft text-agent-adrian`; `🙋 Tú` → `bg-emerald-500/15 text-emerald-600`. Ambos `text-[10px] px-1.5 py-0.5 rounded-full`.

### D.7 · EntitySubNavBar (workspace — back como peer, sin "vistas:")
Fila `h-11`: `[‹ Embudo]` (pill `text-muted hover:bg-muted/50`, glyph `‹` grande — **es un botón más de la barra**) · separador `w-px h-4 bg-border` · entidad (`avatar 20px bg-adrian "M"` + nombre `font-medium` + badge etapa `bg-muted rounded-full text-[10px]`) · separador · pills **Resumen** / **Historial**. Pill activa = `border` + `bg-agent-adrian-soft` + `border-color/text agent-adrian` + `font-medium`; inactiva = `text-muted hover:bg-muted/50`. **NO** existe el label "vistas:". En `nuevo`: `[‹ Embudo] | ➕ Nuevo lead` (sin pills).

### D.8 · Página del lead — Resumen / Historial
- **Cabecera resumen** (bajo la barra): card `flex flex-wrap gap-x-5` con `canal` (ChannelBadge) · `interés` · `valor` · `temp badge + score` · `última actividad` · botón `🙋 Tomar control` (ml-auto).
- **Resumen** (`grid md:grid-cols-2 gap-4`):
  - Izq **"Datos del lead"** (`rounded-md border p-4 space-y-2`): filas `flex justify-between text-xs` label(muted)/value. Vacíos = `italic muted` ("aún sin asignar", "aún sin presentar").
  - Der (`space-y-4`): card **"Estado del agente"** (`border + bg` = agent-adrian: `border-color hsl(--agent-adrian)`, `background hsl(--agent-adrian-soft)`) con "🤖 Adrián la está atendiendo" + `🙋 Tomar control` + líneas Puede/Necesita-tu-OK + acciones `💬 Instrucción oculta · ⚡ Nudge · ↕ Mover de etapa`. Debajo card **"Score"** (`flex items-center gap-4`): ScoreDonut grande + breakdown (filas `justify-between`: factor muted / delta `+25/+15/+10/−2` con verde/destructive) + nota "Reglas + recencia, sin caja negra".
- **Historial:** `ol` con `border-l pl-4 space-y-3 text-xs`: entradas atribuidas (`🤖 Adrián`/`💬 lead`/`⚪ etapa`), chip de señal inline, link "Abrir conversación completa en el Inbox →" (`text-primary underline`).

### D.9 · Vista Lista
Tabla `text-xs`, header `bg-muted/40 border-b`, `th` con `⇅` (sortable, `cursor-pointer hover:text-foreground`). Columnas: **Lead · Etapa · Canal · Score · En etapa · Últ. actividad · Operador · Doctor**. Fila `border-b hover:bg-muted/40 cursor-pointer` → click abre la página del lead. Etapa = pill `bg-muted rounded-full`. Score = número con color. Footer paginación (`‹ 1 ›`) + nota "counts por etapa = total real (no el de la página)".

### D.10 · Nuevo lead (ruta-hoja) + redirect highlight
Card form `rounded-md border p-4 space-y-3`: Nombre* (input), Canal* + Etapa inicial (selects en `grid-cols-2`), Teléfono/Email, Servicio de interés (autocomplete), Notas (textarea). Footer `flex justify-end gap-2`: Cancelar (outline) · **Crear lead** (primary). Submit → navega a `/embudo?highlight={id}` → la card nueva entra en Interesado con `highlight` (outline primary + pulse) + auto-scroll + toast.

### D.11 · Recuperar (sub-tab)
Título + nota de horizonte (Adrián corto / Camila largo). **Segmento 🧊 Recién congeladas:** `FrozenLeadRow` (`rounded-md border p-3`): nombre + ChannelBadge + pill antigüedad (`bg-muted`); "se enfrió en **etapa** · razón"; caja **Diagnóstico** (`bg-agent-adrian-soft`, "🤖 Diagnóstico de Adrián: …"); acciones `↻ Reactivar` (primary sm) / `🙋 Tomar control` (outline). **Segmento 🚫 Decidió no:** fila con razón + cohorte (`text-agent-camila`) + `↻ Reactivar`.

### D.12 · OverrideReasonDialog (drag → justificar → alimenta al agente, RN-4.1)
Overlay `rgba(15,23,42,.5)`; card `w-[420px] p-5 rounded-md border shadow-xl pop`. Título "Mover «{lead}» a {Etapa}"; línea "De {origen} → {destino}. Justificá…"; **textarea obligatoria** (placeholder "Ej.: ya coordinamos la cita por teléfono…"); footer Cancelar (outline) / **Mover y avisar a Adrián** (primary). Confirmar → mueve la card + `highlight` + toast "Adrián tomó nota y ajusta su próximo paso" + **mensaje de Adrián en el panel de Valeria** ("Anotado… no reinicio, ajusto"). Drag a Reservado → NO abre dialog, toast warn "🔒 Reservado se alcanza con el depósito".

### D.13 · Micro-interacciones
- **Drag-drop:** dragstart → card `opacity .4`; columna dragover → `outline dashed primary` + fondo suave; drop válido → dialog D.12; drop en misma columna → no-op; drop Reservado → toast warn.
- **Highlight:** post-create / post-move → `outline 2px primary` + `ringpulse 1.1s ease ×3` (~3.6s) luego limpia.
- **Valeria contextual:** al abrir un lead reacciona con contexto + acciones; al hacer override responde como Adrián. (Demuestra el triángulo supervisora↔agente↔humano.)
- **Toast:** bottom-right, `border-left 3px` primary (info) / amber (warn), auto-dismiss ~3.4s.
- **Transiciones:** `.fade`/`.pop` (≤.25s) al cambiar de vista/abrir modal.

### D.14 · Estados por superficie (loading/empty/error/success)
| Superficie | loading | empty | error | otro |
|---|---|---|---|---|
| Tablero/Kanban | skeleton 5 cols | 5 cols vacías + empty central "Aún no tienes leads" + CTA | banner + Reintentar | dragging · highlight |
| Lista | skeleton filas | empty central | banner | paginación |
| Página lead | skeleton (cabecera+cuerpo) | — | error | **404** "Lead no encontrado" (RN-1) |
| Nuevo lead | idle | — | error inline por campo (Zod) | submitting |
| Recuperar | skeleton | "Sin leads para recuperar 🎉" | banner | — |

### D.15 · Responsive · a11y (refuerza § Responsive·a11y)
- **Mobile:** Kanban scroll-x (`col min-w-280`); Lista → stack de cards; página lead → barra de vistas con scroll; drag → long-press + alternativa teclado.
- **a11y:** EntitySubNavBar `role=tablist` + roving tabindex + Arrow/Home/End (ya implementado en doctores) · drag `KeyboardSensor` + `aria-live` anuncia el movimiento · **ScoreDonut con número visible** (no solo color) · **SLA con texto `Xd`** (no solo color) · contraste ≥4.5:1 · foco visible.

### D.16 · Mapa mockup → componente → golden (ADR-vitalia-003)
| Mockup (sección `embudo-v3.html`) | Componente React | Golden snapshot | Design Contract |
|---|---|---|---|
| Tablero Kanban + columnas | `KanbanBoard` + `PipelineColumn` | `embudo/kanban-{light,dark}.png` | § 3.2 |
| LeadCard (donut+canal+SLA+log) | `LeadCard` (+ `ScoreDonut`, `ChannelBadge`) | `embudo/lead-card-{estados}.png` | NEW |
| Vista Lista | `LeadsTable` | `embudo/lista-{light,dark}.png` | NEW |
| Página lead Resumen | `LeadWorkspace`+`ResumenTab` (+`LeadSummaryHeader`,`ScoreBreakdown`) | `embudo/lead-resumen-{light,dark}.png` | § D-1 |
| Página lead Historial | `HistorialTab` | `embudo/lead-historial-{light,dark}.png` | NEW |
| Nuevo lead | `NewLeadPage` | `embudo/nuevo-{light,dark}.png` | NEW |
| Recuperar | `RecuperarView`+`FrozenLeadRow` | `recuperar/{light,dark}.png` | NEW |
| Override dialog | `OverrideReasonDialog` | `embudo/override-dialog.png` | NEW |
| EntitySubNavBar workspace | `EntitySubNavBar` (reuse) | reusa golden de doctores | § D-1 |

> **Fidelidad ADR-003:** el wrapper (TopBar/Ribbon/SubTabsBar/Valeria/splitter) se **porta verbatim** de `dual-mode-shell.html` + `valeria-chat-sample.html` (no se reinventa); el mockup `embudo-v3.html` lo aproxima con ancho fijo — el builder usa el shell shipped real. Solo el `panel-content` (board/lista/lead/nuevo/recuperar) es propiedad de esta story.

## § Data flow
- **Endpoints (crm + consume engine substrate):** `GET /crm/leads?view=&stage=&origin=&search=&sort=&page=` (board/lista; `sort` default `stage_age_desc` — RN-17) · `GET /crm/leads/{id}` (página) · `PATCH /crm/leads/{id}/stage {to_stage,reason?,note?,version,triggered_by}` (`reason` obligatorio si salta/retrocede — RN-4) · `POST /crm/leads` (alta — V5) · `GET /crm/leads/{id}/transitions` (historial) · `GET /crm/frozen` + `POST /crm/leads/{id}/diagnose` + `POST /crm/leads/{id}/reactivate` (RN-13) + `POST /crm/leads/{id}/{stop|resume|nudge}` (closer-studio substrate) · **stub** `POST /crm/leads/{id}/reservado-side-effect` (MSW).
- **RQ keys:** `["crm","leads",{view,filters}]` · `["crm","lead",id]` · `["crm","frozen"]` · mutation stage → invalida leads + lead.
- **Forms:** RHF+Zod. **Estado global:** Zustand solo UI (drag/toggle/filtros); server data = React Query.

## § Microcopy (Spanish neutro)
Title "Embudo" · toggle "Kanban"/"Lista" · "+ Nuevo lead" · empty "Aún no tienes leads en el embudo" / "Crear primer lead" · badge "💳 Esperando pago"/"✅ Depósito recibido" · toast salto "No puedes saltar a {Etapa} desde {Origen}. Etapa permitida: {Permitida}" · conflicto "Este lead fue actualizado por otra persona." · network "No pudimos mover el lead. Intenta de nuevo." · cierre "¿Por qué no avanzó este lead?" · 404 "Lead no encontrado" · autonomía "Adrián puede mover etapa, agendar y enviar info. Necesita tu OK para cobrar, descuentos o temas clínicos." Sin voseo, tildes + ¿¡.

## § Responsive · a11y · Telemetría
- **Responsive:** Kanban scroll-horizontal mobile (cols min-w-280); Lista→cards; página lead tabs scroll; drag→long-press+teclado.
- **a11y:** EntitySubNavBar `role=tablist` + roving tabindex + Arrow/Home/End (ya implementado) · drag KeyboardSensor + aria-live · contraste ≥4.5:1 · SLA no solo color (texto `3d`).
- **Telemetría** (`vitalia_growth_studio_event`, sin PII, montos bucketeados): `embudo_viewed{view}` · `embudo_subsubtab_viewed{tablero|recuperar}` · `embudo_stage_changed{from,to,trigger}` · `embudo_lead_opened{vista}` · `embudo_lead_created{origin,stage}` · `embudo_takeover{}` · `embudo_diagnose{}` · `embudo_reactivate{frozen_reason}`.

## § Decisiones (resueltas 2026-06-03 + lo que queda)

**✓ Resueltas (Chris):**
1. **Consumir sustrato agéntico del engine** (closer-studio + checkpoint + transitions + diagnose + KPIs) — ✓ **SÍ** (aceptado).
2. **Conversation-first** (Adrián mueve; drag = override) — ✓ **SÍ**.
3. **Alcance** — ✓ **1 sola story** (board+lista+página+override+nuevo+Recuperar+congelados, ~8-11d). NO se parte en S4a/S4b. El architect arma un ready package único.
4. **Dataset canónico** (§ Dataset) — ✓ aceptado (los 11 leads dental PEN + SLA + breakdown de María).
5. **Tablero hot vs Recuperar (RN-18)** — ✓ `Decidió no` + congelados salen del Tablero a la sub-tab Recuperar. Kanban = solo HOT.
6. **Nuevo lead = ruta-hoja `/nuevo`** (no modal, no sub-sub-tab) — ✓.
7. **Números de SLA (RN-11)** — ✓ **7 / 7 / 5 / 14 días** (Interesado/Calificando/Consulta/Plan) + auto-freeze 14d sin respuesta / 30d duro (RN-13). Aceptados.
8. **Recuperar = sub-tab hermana de Adrián** (2do nivel, nombre **"Recuperar"**) — ✓. División Adrián-corto-plazo / Camila-largo-plazo ✓.

**Estado:** spec funcional + visual **ratificados**; § Design specification D.0–D.16 completo. **Chris quiere afinar algo más antes de `/architect`** (no se cierra `refined` aún). Pendiente: lo que Chris indique en el próximo turno → luego `refining → refined` → `/architect`.

## § Próximo paso
Iterar este spec (detalle de vistas + reglas + dataset). Al acordar la data → **regenerar mockup C** (`mockups/`) con el dataset canónico + gate ADR-003 mockups-per-component → `refined` → `/architect`.
