<!-- voseo-allowed: internal /po-ux spec documentation, not user-facing -->
---
story_id: vitalia-fase1-empty-states
brand: vitalia
type: ui-story
state: refining
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.empty-states
po_ux_version: 2
ratified_by_chris: true
ratified_at: 2026-05-26T11:55:00-05:00
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-26T11:55:00-05:00
ratified_visual_iter: 2
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/empty-states-grid.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/lisa-servicios-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-embudo-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-inbox-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/valeria-agenda-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/config-conexiones-placeholder.html
batch_1_ratified_at: 2026-05-26
batch_1_decisions:
  Q1_mockup_strategy: combo_1_grid_plus_6_standalone   # extract 6 standalone + 1 grid integral
  Q2_toggle_interactivity: funcionales_js_local        # mockup JS local toggles 4 placeholders especiales
  Q3_header_copy_generic: uniforme                     # 16 genéricos comparten description estándar
batch_2_ratified_at: 2026-05-26
batch_2_decisions:
  Q4_inbox_depth: sales_studio_parity                  # CampaignTag pill + widths 320/flex/288 + sidebarOpen toggle + temp-dot+stage-badge+channel-abbr+handler_mode
  Q5_agenda_depth: enriquecer_placeholder              # toolbar period nav + filters visuales + grid 6d + slot content rico (paciente·service·doctor) + footer Adrián summary
  Q5_agenda_func_scope: F1_mockup_full_F2_react_full   # mockup HTML rich AHORA + componente React F1-S10 también rich; funcionalidad real (sidebar selectable, payment subform, fiscal capa 2, historial, cross-links, filters func, PHI masking) difiere a F2-S1 valeria-agenda
  Q6_inbox_takeover_ux: explicit_button_take_return     # botón explícito "✋ Tomar el control" en thread header (Adrián maneja) + banner amarillo "Tienes el control · Adrián pausado" (usuario en control) + botón "🤖 Devolver a Adrián" + MessageInput disabled↔enabled + ConversationItem chip "✋ Tú" para human-handled (override pattern shipped en sales_studio extendido per-conversation)
  Q7_camila_voz_copy: aclarar_minimo_F1                  # Chris feedback "no entiendo nada" — aclarar copy del placeholder F1-S10 (description + 3 cards descriptions + footer) sin tocar estructura ni componentes React. F2-S11 vitalia-fase2-camila-voz sigue ownership del flow conversacional Camila + tool calling sentiment + integraciones Reactivar/Reputación/Multiplicar.
ratified_visual_mockups_expected:
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/empty-states-grid.html        # integral navegable 22 sub-tabs
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/lisa-servicios-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-embudo-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-inbox-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/valeria-agenda-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/config-conexiones-placeholder.html
last_modified: 2026-05-26
authors: [/po-ux]
spec_anchors:
  shell_design_contract: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
  shell_template: vitalia/docs/specs/templates/01-spec-shell-template.md
  agent_catalog_ssot: vitalia/frontend/src/lib/agent-catalog.ts
  ssot_visual_integral: vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
  predecessor_F1_S8: vitalia/docs/archive/2026/stories/vitalia-fase1-sub-tabs-line2/01-spec.md
  predecessor_F1_S9: vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/01-spec.md
ssot_extensions:
  agent_catalog: vitalia/frontend/src/lib/agent-catalog.ts (READ-ONLY — consume RIBBON_SUBTABS as SSoT del inventory 22 sub-tabs)
overlay_rules:
  - vitalia/.claude/rules/shell-mockup-per-component.md   # gate visual bloqueante — 7 mockups requeridos
  - vitalia/.claude/rules/hipaa-lite.md                   # placeholder data = mock-only, no PHI real
external_docs:
  - https://nextjs.org/docs/app/api-reference/file-conventions/page
  - https://www.radix-ui.com/primitives/docs/components/tabs
---

# F1-S10 · `vitalia-fase1-empty-states` — 01-spec.md (unified)

> **/po-ux UI-standard.** Última story Fase 1 — puebla los 22 sub-tab pages con placeholders ricos (6 especiales con mockup-parity per dual-mode-shell.html) + 16 genéricos (EmptyState molécula). Cierra el shell-organism navegable end-to-end.

---

## § 1 — Resumen ejecutivo

F1-S10 puebla el dispatcher `[agent]/[subtab]/page.tsx` (route shipped por F1-S9) con un componente `SubTabContent` que mapea 22 combos `{agent}.{subtab}` → placeholder React. Seis sub-tabs especiales replican estructura del mockup SSoT (`dual-mode-shell.html` líneas 1098-1170 + secciones siguientes): Lisa Servicios (toggle Catálogo|Escalera + cards), Adrián Embudo (Kanban 6 cols), Adrián Inbox (3-modos + 3-column), Camila Voz (3-modos + 3 cards), Valeria Agenda (grilla semana + slots), Config Conexiones (grid 6 categorías). Las 16 restantes usan `EmptyState` molécula con icon + title + descripción Spanish neutro.

**Outcome del usuario después del merge:** "navego cualquiera de los 22 sub-tabs y veo una pantalla con sentido (no whitespace ni 404), entiendo qué va a vivir ahí cuando Fase 2 lo implemente, y las 6 vistas especiales me hacen sentir que la UI es real aunque no esté funcional todavía".

**Cierre Fase 1:** este es el último átomo. Al merge, la chain F1-S0..F1-S10 cierra y Fase 2 (22 stories sub-tab funcionales) puede arrancar en cualquier orden.

**Anti-objetivos (anti-creep):**
- NO interactividad real (Kanban DnD, agenda CRUD, inbox conversación) — Fase 2
- NO fetch data API real — mocks hardcoded en placeholder components
- NO filtros funcionales / búsqueda / paginación
- NO toggles funcionales (Catálogo|Escalera, Kanban|Lista, 3-modos) cambian state local visual pero NO cambian data
- NO `mateo` sub-tabs (catalog SSoT confirma `mateo: []`)
- NO routing nuevo (F1-S9 ya cementó URL tree)

---

## § 2 — Visión (paradigma shell-organism)

F1-S10 es la "fachada decorada" del edificio cuyo esqueleto Fase 1 levantó. Sin esta historia, el dueño que entra a `/{tenantId}/lisa/servicios` ve una page vacía o título suelto — rompe la sensación de "producto real". Con F1-S10, el dueño puede recorrer las 22 vistas y formarse expectativas concretas sobre qué hará Fase 2.

Las 6 placeholders especiales son inversión doble: (a) calidad demo para stakeholders/Chris (mockup parity vs HTML SSoT) y (b) andamiaje real (los componentes Toggle / Kanban shell / GridSlot que Fase 2 va a heredar y poblar con data). Las 16 genéricas son hold-the-space (consistencia visual + a11y heading hierarchy + descripción "qué va a vivir acá").

**Agente owner:** Shell (transversal — F1-S10 es plomería decorativa, no de un agente específico).

---

## § 3 — Atomic Design Layers (referencia Design Contract § 3)

### § 3.1 — Átomos consumidos

| Átomo | Fuente | Variante | Path |
|---|---|---|---|
| `Button` | Shadcn | default + ghost + outline | `components/ui/button.tsx` |
| `Tabs` (Toggle pill) | Shadcn | default | `components/ui/tabs.tsx` |
| `Badge` | Shadcn | secondary + outline | `components/ui/badge.tsx` |
| `Card` | Shadcn | default | `components/ui/card.tsx` |

### § 3.2 — Moléculas construidas en esta historia

| Molécula | Path nuevo | Responsabilidad |
|---|---|---|
| `EmptyState` | `components/shared/shell-organism/EmptyState.tsx` | Genérico: icon emoji + title + description + opcional CTA. Used by 16 placeholders + null-state |
| `PlaceholderCard` | `components/shared/shell-organism/PlaceholderCard.tsx` | Card con icon + title + desc + status dot (shipped/planned/todo) per mockup |
| `SubTabHeader` | `components/shared/shell-organism/SubTabHeader.tsx` | Title (label sub-tab) + descripción contextual + opcional CTA right-aligned |
| `StatusDot` | `components/shared/shell-organism/StatusDot.tsx` | Indicador color (verde/amarillo/gris) reusado por PlaceholderCard + slot status agenda |
| `TogglePill` | `components/shared/shell-organism/TogglePill.tsx` | Wrapper Shadcn Tabs styled como pill — used by Lisa Servicios + Adrián Embudo + Adrián Inbox + Camila Voz |

**Sales_studio parity (Inbox enriquecido — batch 2 cement 2026-05-26)** — F1-S10 reusa los componentes y patterns de `ap_sales_agent/frontend/src/features/closer-studio/components/inbox/` shipped:

| Molécula sales_studio parity | Path nuevo F1-S10 | Responsabilidad | Reusa pattern de |
|---|---|---|---|
| `CampaignTag` | `features/adrian/components/inbox/CampaignTag.tsx` | Pill clickable "📣 {campaignName}" trunca >30 chars + tooltip + link `/{tenantId}/lucas/lanzar?campaign={id}` | `closer-studio/components/inbox/CampaignTag.tsx` |
| `ConversationItem` | `features/adrian/components/inbox/ConversationItem.tsx` | Avatar initials + temp-dot (hot/warm/cold) + stage-badge (Nuevo/Calificando/Negociando/Cerrando) + channel-abbr (WA/IG/TG) + handler_mode border-l verde si human | `closer-studio/components/inbox/ConversationItem.tsx` |
| `MessageBubble` | `features/adrian/components/inbox/MessageBubble.tsx` | In/out variants + timestamp + sender attribution | `closer-studio/components/inbox/MessageBubble.tsx` |
| `MessageInput` | `features/adrian/components/inbox/MessageInput.tsx` | Textarea + attach + submit. F1-S10 disabled state. Fase 2 cablea RHF + Zod | `closer-studio/components/inbox/MessageInput.tsx` |
| `ContactSidebar` | `features/adrian/components/inbox/ContactSidebar.tsx` | Patient header + masked PHI (+51 9** ***-4321) + origen + tags + cross-action buttons (Agendar / Historial / Pasar a embudo) | `closer-studio/components/inbox/ContactSidebar.tsx` |
| `ThreadHeader` (★ takeover UX) | `features/adrian/components/inbox/ThreadHeader.tsx` | 2 estados: (A) Adrián maneja → avatar+nombre+canal + chip "🤖 Adrián decidiendo" + botón "✋ Tomar el control" + sidebar toggle (×). (B) Usuario en control → mismo avatar+nombre+canal pero con `TakeoverBanner` debajo en lugar del chip | NUEVO conceptual (sales_studio NO tiene takeover explícito — extiende el shape original) |
| `TakeoverBanner` (★ takeover UX) | `features/adrian/components/inbox/TakeoverBanner.tsx` | Banner amarillo `border-left #f59e0b` con icon ⚡ + título "Tienes el control · Adrián pausado en esta conversación" + meta "El modo global no se altera · solo aquí" + botón "🤖 Devolver a Adrián" | NUEVO conceptual |
| `MessageInput` (★ con state dual) | `features/adrian/components/inbox/MessageInput.tsx` | Textarea + send btn + attach. Estado A (Adrián maneja): disabled + placeholder "🤖 Adrián decide automáticamente · toma el control para escribir tú". Estado B (usuario): habilitado + placeholder "Escribir como tú a {paciente}…" + auto-focus | `closer-studio/components/inbox/MessageInput.tsx` extendido |
| `ConversationItem.YouChip` (★ takeover UX) | inline en `ConversationItem.tsx` | Cuando `handler_mode='human'` además del border-l-2 verde, agregar chip `✋ Tú` (font-size 9px, bg green-100/30, border green-500/50) con tooltip "Tomaste el control · Adrián pausado en esta conversación" | NUEVO conceptual |

**Agenda enriquecida (batch 2 cement 2026-05-26)** — F1-S10 mockup + componente React reflejan structure ratificada del prototipo `/home/chalreme/Trabajo/Vitalia/Prototipos/agenda.html`:

| Molécula agenda enriquecida | Path nuevo F1-S10 | Responsabilidad |
|---|---|---|
| `AgendaToolbar` | `features/valeria/components/agenda/AgendaToolbar.tsx` | Period nav (‹ Semana X-Y ›) + Día/Semana/Mes toggle + Hoy button + CTA "Crear cita" con dropdown 3 origins (Walk-in/Phone/Proactivo) |
| `AgendaFilters` | `features/valeria/components/agenda/AgendaFilters.tsx` | Filter chips visuales (Doctor/Especialidad/Status pago/no-show/walk-in). F1-S10 disabled. Fase 2 cablea Zustand state |
| `AgendaDayHeader` | `features/valeria/components/agenda/AgendaDayHeader.tsx` | Cell header con label (Lun/Mar) + day-num grande + `today` highlight (color agent-valeria/agent-adrian) |
| `AgendaSlot` | `features/valeria/components/agenda/AgendaSlot.tsx` | Slot content: paciente name + service + doctor + origin icon (🚶/📞/✉) + status pill (PAG/30%/SIN PAGO/NO-SHOW). 4 variants color border-left |
| `AgendaSummaryFooter` | `features/valeria/components/agenda/AgendaSummaryFooter.tsx` | Leyenda 4 status + Adrián+Lucas summary text ("Adrián propuso 4 turnos hoy · 3 sin pago · Lucas: 3 leads listos") |

### § 3.3 — Organismos construidos en esta historia

| Organismo | Composición | State management | Path nuevo |
|---|---|---|---|
| `SubTabContent` | Dispatcher: mapea `{agent}.{subtab}` → Placeholder component vía PLACEHOLDER_MAP | local (useState toggles especiales) | `components/shared/shell-organism/SubTabContent.tsx` |
| `LisaServiciosPlaceholder` | TogglePill (Catálogo\|Escalera) + 5 PlaceholderCards | local toggle state | `features/lisa/components/placeholders/ServiciosPlaceholder.tsx` |
| `AdrianEmbudoPlaceholder` | TogglePill (Kanban\|Lista) + 6 KanbanColumn (3 leads mock c/u) | local toggle state | `features/adrian/components/placeholders/EmbudoPlaceholder.tsx` |
| `AdrianInboxPlaceholder` (★ enriquecido batch 2) | TogglePill (3-modos) + 3-col layout (ConversationList 320px\|Thread flex-1\|ContactSidebar 288px) + 5 ConversationItem mock con CampaignTag/temp-dot/stage-badge/channel-abbr · 1 con `handler_mode=human` border-l-2 verde · Thread con 4 MessageBubble + MessageInput disabled · ContactSidebar collapse toggle | local (selected=mock-fixed, sidebarOpen toggle) | `features/adrian/components/placeholders/InboxPlaceholder.tsx` |
| `CamilaVozPlaceholder` | TogglePill (3-modos) + 3 PlaceholderCards (Entrante 12 \| Curaduría 4 \| Activos 47) | local toggle state | `features/camila/components/placeholders/VozPlaceholder.tsx` |
| `ValeriaAgendaPlaceholder` (★ enriquecido batch 2) | `AgendaToolbar` (period nav + period toggle + Hoy + CTA Crear cita dropdown) + `AgendaFilters` row visual disabled + `AgendaDayHeader` × 6 (Lun-Sáb today highlight) + grid 6d × 8h con 8 AgendaSlot mock variados (4 status pago · 3 origins · service · doctor) + 6 cells lunch-time pattern stripe + `AgendaSummaryFooter` (leyenda + Adrián+Lucas summary) | local (period toggle visual) | `features/valeria/components/placeholders/AgendaPlaceholder.tsx` |
| `ConfigConexionesPlaceholder` | Grid 6 categorías (Marketing/Mensajería/Pagos/Calendarios/Presencia/Técnicas) | static | `features/config/components/placeholders/ConexionesPlaceholder.tsx` |
| `GenericEmptyStatePlaceholder` | Wrapper EmptyState con copy estándar | static | `features/{agent}/components/placeholders/{Subtab}Placeholder.tsx` (×16) |

### § 3.4 — Templates / Pages tocadas

| Template/Page | Acción | Path |
|---|---|---|
| `[agent]/[subtab]/page.tsx` | MODIFY — reemplazar placeholder "TBD F1-S10" por `<SubTabContent agent={params.agent} subtab={params.subtab} />` | `app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` |
| `[agent]/page.tsx` | NO TOCAR — F1-S9 ya redirige a defaultSubtab | — |
| `not-found.tsx` | NO TOCAR — F1-S9 cementó | — |

---

## § 4 — Inventario 22 sub-tabs (SSoT consume `RIBBON_SUBTABS` de `agent-catalog.ts`)

| # | Agent | Subtab | Tipo | Mockup parity | Componente |
|---|---|---|---|---|---|
| 1 | lisa | marca | genérico | EmptyState | `LisaMarcaPlaceholder` |
| 2 | lisa | doctores | genérico | EmptyState | `LisaDoctoresPlaceholder` |
| 3 | lisa | **servicios** | **especial** | TogglePill Catálogo\|Escalera + 5 cards | `LisaServiciosPlaceholder` |
| 4 | lisa | compliance | genérico | EmptyState | `LisaCompliancePlaceholder` |
| 5 | lucas | lanzar | genérico | EmptyState | `LucasLanzarPlaceholder` |
| 6 | lucas | envuelo | genérico | EmptyState | `LucasEnvueloPlaceholder` |
| 7 | lucas | recursos | genérico | EmptyState | `LucasRecursosPlaceholder` |
| 8 | lucas | resultados | genérico | EmptyState | `LucasResultadosPlaceholder` |
| 9 | lucas | mercado | genérico | EmptyState | `LucasMercadoPlaceholder` |
| 10 | adrian | **inbox** | **especial** | TogglePill 3-modos + 3-col | `AdrianInboxPlaceholder` |
| 11 | adrian | **embudo** | **especial** | TogglePill Kanban\|Lista + 6 cols | `AdrianEmbudoPlaceholder` |
| 12 | adrian | outbound | genérico | EmptyState | `AdrianOutboundPlaceholder` |
| 13 | adrian | propuestas | genérico | EmptyState | `AdrianPropuestasPlaceholder` |
| 14 | valeria | **agenda** | **especial** | Grilla 5d×8h + 6 slots | `ValeriaAgendaPlaceholder` |
| 15 | valeria | pacientes | genérico | EmptyState | `ValeriaPacientesPlaceholder` |
| 16 | camila | **voz** | **especial** | TogglePill 3-modos + 3 cards | `CamilaVozPlaceholder` |
| 17 | camila | reactivar | genérico | EmptyState | `CamilaReactivarPlaceholder` |
| 18 | camila | multiplicar | genérico | EmptyState | `CamilaMultiplicarPlaceholder` |
| 19 | camila | reputacion | genérico | EmptyState | `CamilaReputacionPlaceholder` |
| 20 | config | cuenta | genérico | EmptyState | `ConfigCuentaPlaceholder` |
| 21 | config | **conexiones** | **especial** | Grid 6 categorías | `ConfigConexionesPlaceholder` |
| 22 | config | avanzado | genérico | EmptyState | `ConfigAvanzadoPlaceholder` |

**Total:** 16 genéricos + 6 especiales = 22. Mateo NO incluido (catálogo SSoT confirma `mateo: []`).

---

## § 5 — Gherkin scenarios

### SC-1 happy · 22 sub-tabs navegables sin error

**Given:** Usuario autenticado en `/{tenantId}` con shell montado
**When:** Click cada ribbon tab (5 agents + Config) → click cada sub-tab disponible
**Then:**
- Cada combo `{agent}.{subtab}` renderiza su placeholder sin console error
- 22 transiciones sin 404 / sin pantalla blanca
- SubTabHeader visible en cada vista con label correcto (label español verbatim del catalog SSoT)

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-01-navegacion-22-subtabs.spec.ts" }` · `playwright_required: true`
- `{ type: state_check, target: console, expect: "no errors during 22-subtab traversal" }`

### SC-2 happy · placeholder especial Lisa Servicios

**Given:** URL `/{tenantId}/lisa/servicios`
**When:** Página carga
**Then:**
- TogglePill "Catálogo | Escalera" visible (Catálogo active default)
- Grid 5 PlaceholderCards: "Limpieza dental", "Blanqueamiento", "Implante", "Mantenimiento periodontal", "+ Nuevo tratamiento" (CTA card outline)
- Click pill "Escalera" → state local cambia, contenido secundario aparece (placeholder canvas "Escalera de valor — próximamente"), NO recarga page

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-02-lisa-servicios.spec.ts" }` · `playwright_required: true`
- `{ type: visual_state, screen: "lisa-servicios-catalogo", element: "[data-testid=lisa-servicios-placeholder]", expect: "matches mockup lisa-servicios-placeholder.html tolerance 0.001" }`
- `{ type: visual_state, screen: "lisa-servicios-escalera", element: "[data-testid=lisa-servicios-placeholder]", expect: "matches state escalera" }`

### SC-3 happy · placeholder especial Adrián Embudo

**Given:** URL `/{tenantId}/adrian/embudo`
**When:** Página carga
**Then:**
- TogglePill "Kanban | Lista" visible (Kanban active default)
- 6 columnas con header `{emoji} {label} — {count} — {value}`: ⚪ Interesado 12 · $84k · 🟢 Calificando 8 · $62k · 🟡 Considerando 5 · $41k · 🔵 Listo 3 · $28k · 🟣 Reservado 2 · $15k · ⚫ Decidió no 4 · —
- Cada columna: 3 dummy lead cards (nombre + valor + última actividad mock)
- Horizontal scroll en viewport <1280px
- Click pill "Lista" → state local cambia, lista vertical aparece (placeholder "Vista lista — próximamente")

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-03-adrian-embudo.spec.ts" }` · `playwright_required: true`
- `{ type: visual_state, screen: "adrian-embudo-kanban", element: "[data-testid=adrian-embudo-placeholder]", expect: "matches mockup adrian-embudo-placeholder.html" }`

### SC-4 happy · placeholder especial Valeria Agenda (★ enriquecido batch 2)

**Given:** URL `/{tenantId}/valeria/agenda`
**When:** Página carga
**Then:**
- **AgendaToolbar** visible con: period nav (‹ "Semana 26-31 May 2026" ›) + toggle Día/Semana/Mes (Semana active default) + botón "📅 Hoy" + CTA "+ Crear cita ▾"
- Click CTA "+ Crear cita ▾" → dropdown visible con 3 opciones (Walk-in / Reserva por teléfono / Reagendar proactivamente)
- **AgendaFilters** row visible con 6 chips disabled: buscador paciente · Doctor: Todos ▾ · Especialidad: Todas ▾ · Status pago: Todos ▾ · ☐ Solo riesgo no-show · ☐ Solo walk-in
- **AgendaDayHeader** × 6 (Lun 26 / Mar 27 / Mié 28 / Jue 29 / Vie 30 / Sáb 31) — Lun 26 marcado `today` (color highlight agent-valeria/agent-adrian per breakpoint)
- Grid 6d × 8h (08:00-16:00) visible
- ≥ 8 **AgendaSlot** mock distribuidos con: paciente name + service + doctor (NO solo nombre) + origin icon (🚶/📞/✉) + status pill verbatim (✓ PAG · 30% · SIN PAGO · ⚠ NO-SHOW)
- 6 cells fila 13:00 con pattern stripe (`background: repeating-linear-gradient(...)` aria-label="Horario de almuerzo")
- **AgendaSummaryFooter** visible con leyenda 4 status + texto "Adrián propuso N turnos hoy · M sin pago · Lucas: K leads listos"
- Click slot ocupado → NO acción Fase 1 (Fase 2 abre ContactSidebar con detail + payment subform)
- Click slot vacío → NO acción Fase 1 (Fase 2 abre modal "Crear cita en {hora} {día}")

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-04-valeria-agenda.spec.ts" }` · `playwright_required: true`
- `{ type: visual_state, screen: "valeria-agenda-week-default", element: "[data-testid=valeria-agenda-placeholder]", expect: "matches mockup valeria-agenda-placeholder.html (Lun 26 today)" }`
- `{ type: e2e_action, scenario: "click period toggle Día", expect: "active state moves to Día (visual only)" }`
- `{ type: e2e_action, scenario: "click CTA Crear cita", expect: "dropdown 3 opciones visible" }`

### SC-4.bis happy · placeholder Adrián Inbox (★ sales_studio parity batch 2)

**Given:** URL `/{tenantId}/adrian/inbox`
**When:** Página carga
**Then:**
- TogglePill "🤖 Adrián decide / 👀 Te consulta / ✋ Manual" visible (Adrián decide active default)
- Layout 3-column con widths shipped `320px / flex-1 / 288px` (parity sales_studio `closer-studio/components/inbox/InboxView.tsx` shipped)
- **ConversationList** (320px) muestra 5 ConversationItem mock con cada uno:
  - Avatar initials redondo (color agent-adrian)
  - `temp-dot` (🔴hot / 🟠warm / 🔵cold) leading nombre
  - Channel-abbr badge (WA/IG/TG)
  - Stage-badge (Nuevo / Calificando / Negociando / Cerrando)
  - ≥2 ConversationItem con `CampaignTag` pill "📣 {campaignName}" (Limpieza-PE · Blanqueamiento)
  - ≥1 ConversationItem con `handler_mode=human` → border-l-2 verde
  - 1 ConversationItem `selected` con `border-l-2` color agent-adrian
- **ConversationThread** (flex-1) muestra:
  - Header con avatar paciente + nombre + channel + handler_mode pill ("🤖 Adrián decidiendo")
  - Botón "×" cerrar ContactSidebar (toggle funcional `sidebarOpen` local)
  - ≥4 MessageBubble alternados in/out con timestamps
  - Footer: textarea MessageInput placeholder "Escribir mensaje… (Manual)" DISABLED · botón "Enviar" disabled opacity 0.5
- **ContactSidebar** (288px) muestra:
  - Nombre paciente (María González)
  - Teléfono con PHI masking (+51 9** ***-4321) + botón unlock 🔓 (decorativo Fase 1, Fase 2 cablea RBAC)
  - Email con masking (m***@gmail.com) + 🔓
  - Origen con CampaignTag pill linkeable a `/{tenantId}/lucas/lanzar?campaign={id}` (NO navega Fase 1)
  - Stage-badge "🟢 Calificando"
  - Tags pills (limpieza · primera vez)
  - 3 action buttons: "📅 Agendar cita" / "📋 Ver historial paciente" / "→ Pasar a embudo" (todos NO acción Fase 1)
- Click "×" header thread → ContactSidebar oculta + grid-template-columns cambia a `320px 1fr 0`
- ★ **Takeover UX (per-conversation handler override) — Fase 1 visual completo:**
  - Por defecto thread muestra estado A (Adrián maneja): chip "🤖 Adrián decidiendo" + botón "✋ Tomar el control" en thread header; MessageInput disabled con placeholder "🤖 Adrián decide automáticamente · toma el control para escribir tú"; thread footer hint "Adrián decidirá la próxima respuesta automáticamente · clic ✋ Tomar el control arriba para responder tú"
  - Click "✋ Tomar el control" → transición a estado B (usuario en control):
    - Chip "🤖 Adrián decidiendo" + botón takeover desaparecen del header
    - `TakeoverBanner` amarillo aparece debajo del header: "⚡ Tienes el control · Adrián pausado en esta conversación" + meta "El modo global '🤖 Adrián decide' no se altera · solo aquí · puedes devolver el control cuando quieras" + botón "🤖 Devolver a Adrián"
    - MessageInput se habilita con placeholder "Escribir como tú a María González…" + auto-focus
    - Send button + attach button habilitados
    - Thread footer hint cambia a (amarillo) "⚡ Estás respondiendo como tú · Adrián volverá a manejar la conversación cuando devuelvas el control"
  - Click "🤖 Devolver a Adrián" en banner → transición de vuelta a estado A
  - ConversationItem con `handler_mode='human'` (Carlos Pérez en mock) muestra chip "✋ Tú" además del border-l-2 verde

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-04bis-adrian-inbox.spec.ts" }` · `playwright_required: true`
- `{ type: visual_state, screen: "adrian-inbox-state-A-adrian", element: "[data-testid=adrian-inbox-placeholder]", expect: "matches mockup state A (Adrián maneja con botón takeover)" }`
- `{ type: visual_state, screen: "adrian-inbox-state-B-human", element: "[data-testid=adrian-inbox-placeholder]", expect: "matches mockup state B (banner amarillo + MessageInput enabled)" }`
- `{ type: e2e_action, scenario: "click ✋ Tomar el control", expect: "state transitions A→B (banner visible, MessageInput enabled, hint cambia)" }`
- `{ type: e2e_action, scenario: "click 🤖 Devolver a Adrián", expect: "state transitions B→A (chip restored, MessageInput disabled)" }`
- `{ type: e2e_action, scenario: "click × cerrar sidebar", expect: "ContactSidebar oculta + grid-template-columns 320px 1fr 0" }`
- `{ type: e2e_action, scenario: "click toggle global 'Te consulta'", expect: "active state moves visually (no data change, no afecta takeover de la conv selected)" }`

### SC-5 negative · sub-tab inválido en URL → 404 dentro del shell

**Given:** URL `/{tenantId}/lisa/xxxnotvalid`
**When:** Página carga
**Then:**
- `not-found.tsx` jerárquico (F1-S9 cementó) renderiza dentro del shell
- Ribbon + ValeriaSidebar visibles
- SubTabContent vacío con mensaje "Sub-tab inexistente. Volver a Lisa/Marca."

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-05-subtab-invalido.spec.ts" }` · `playwright_required: true`

### SC-6 edge · 22 sub-tabs render sin re-mount completo del shell

**Given:** Usuario en `/{tenantId}/lisa/marca`
**When:** Click 21 sub-tabs en secuencia rápida (Playwright `.click()` × 21)
**Then:**
- Ribbon DOM node NO re-mounts (assertion: same `data-testid=ribbon-root` ref across clicks)
- ValeriaSidebar DOM node NO re-mounts
- Solo `SubTabContent` se re-renderiza per route change
- No errores console "Maximum update depth exceeded"

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-06-edge-no-shell-remount.spec.ts" }` · `playwright_required: true`

### SC-7 adversarial · XSS payload en URL subtab → safe render

**Given:** URL `/{tenantId}/lisa/<script>alert(1)</script>`
**When:** Página carga
**Then:**
- `isValidSubtab()` (F1-S9) bloquea → renders `not-found.tsx`
- DOM NO contiene `<script>` tag inyectado
- NO `alert()` fires (Playwright `page.on('dialog')` assertion = never)

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-07-adversarial-xss.spec.ts" }` · `playwright_required: true`

### SC-8 sub-categoría · empty_state — 16 sub-tabs genéricas

**Given:** URL `/{tenantId}/{agent}/{subtab}` donde subtab NO está en lista 6 especiales
**When:** Página carga
**Then:**
- `EmptyState` renderiza con: icon (del catalog SSoT), title `"{Subtab label} — próximamente"`, descripción `"Esta vista vive acá. El contenido real se diseña en Fase 2."`
- Sin botón CTA (Fase 2 puede agregar uno)

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-08-empty-states-genericos.spec.ts" }` · `playwright_required: true` · parametrizado over 16 generic subtabs
- `{ type: visual_state, screen: "lisa-marca-empty", expect: "matches mockup empty-states-grid.html § lisa.marca" }`

### SC-9 sub-categoría · accessibility — heading hierarchy + keyboard

**Given:** Cualquier sub-tab (especial o genérica)
**When:** axe scan + keyboard Tab navigation
**Then:**
- `SubTabHeader` usa `<h2>` (h1 ya está en TopBarGlobal o page-level — verify no duplicates)
- PlaceholderCard internal headings = `<h3>`
- Toggle pills focusable con Tab, activables con Space/Enter
- axe `wcag2aa` → 0 violations (color contrast incluido)

**graders:**
- `{ type: axe, ruleset: "wcag2aa" }`
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-09-a11y.spec.ts" }` · `playwright_required: true`

### SC-10 sub-categoría · i18n — Spanish neutro LatAm + tenant_locale

**Given:** Cualquier sub-tab + tenant con `currency: PEN` y `timezone: America/Lima`
**When:** Página carga
**Then:**
- Toda copy en español neutro (verificación contra glosario voseo: ver § 9 microcopy)
- Valeria Agenda placeholder mock slots con horarios formato 24h `America/Lima`
- Adrián Embudo mock values formato `${money} {currency}` usando `tenant_locale.currency`

**graders:**
- `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-10-i18n.spec.ts" }` · `playwright_required: true`
- `{ type: state_check, target: dom, query: "grep voseo verbs in rendered HTML", expect: "0 matches" }`

### SC-11 sub-categoría · network_failure — N/A justificada

**not_applicable_reason:** F1-S10 NO hace fetch API (todo mock hardcoded en componentes). Sin network call no hay failure mode que probar. Cuando Fase 2 cablee data real, cada sub-tab story probará su propio network failure.

### SC-12 sub-categoría · race_condition + concurrent_users + large_dataset — N/A justificadas

**not_applicable_reason:** F1-S10 NO escribe DB, NO tiene unique constraints, NO tiene paginación. Mock data es constante hardcoded. Cuando Fase 2 cablee writes/lists, cada sub-tab story probará concurrencia.

---

## § 6 — Wireframes

### § 6.1 — ASCII inline: SubTabContent dispatcher decision tree

```
[agent]/[subtab]/page.tsx
        │
        └── <SubTabContent agent={X} subtab={Y} />
                │
                ├── key = `${X}.${Y}` in PLACEHOLDER_MAP?
                │       ├── YES → <SubTabHeader/> + <SpecialPlaceholder/>
                │       └── NO  → <SubTabHeader/> + <GenericEmptyStatePlaceholder agent={X} subtab={Y}/>
                │                            (lookup label+icon de RIBBON_SUBTABS[X])
                │
                └── never reach SubTabContent si subtab inválido (F1-S9 not-found.tsx intercepta antes)
```

### § 6.2 — ASCII inline: EmptyState molécula (16 genéricas)

```
┌─────────────────────────────────────────────┐
│   SubTabHeader (h2 + descripción + spacer)   │
├─────────────────────────────────────────────┤
│                                              │
│                                              │
│              {emoji 5xl opacity-50}          │
│                                              │
│        {label} — próximamente   (h3)         │
│                                              │
│   Esta vista vive acá. El contenido real     │
│   se diseña en Fase 2.   (muted-foreground)  │
│                                              │
│                                              │
└─────────────────────────────────────────────┘
```

### § 6.3 — ASCII inline: 6 placeholders especiales (layouts)

**Lisa Servicios** (toggle + cards):
```
┌────────────────────────────────────────────┐
│ SubTabHeader: Servicios                    │
├────────────────────────────────────────────┤
│  [Catálogo•] [Escalera]                    │
├────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │🦷   │ │✨   │ │🦴   │ │🪥   │ │  +  │  │
│  │Limp.│ │Blan.│ │Impl.│ │Mant.│ │Nuevo│  │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘  │
└────────────────────────────────────────────┘
```

**Adrián Embudo** (Kanban 6 cols):
```
┌──────────────────────────────────────────────┐
│ SubTabHeader: Embudo  [Kanban•] [Lista]      │
├──────────────────────────────────────────────┤
│ ⚪Interesado│🟢Calif.│🟡Cons.│🔵Listo│🟣Res.│⚫No│
│ 12·$84k    │8·$62k │5·$41k │3·$28k│2·$15k│4·— │
│ ──────────────────────────────────────────── │
│ [lead 1]   │[lead]  │[lead] │[lead]│[lead]│   │
│ [lead 2]   │[lead]  │[lead] │[lead]│[lead]│   │
│ [lead 3]   │[lead]  │[lead] │[lead]│      │   │
└──────────────────────────────────────────────┘  ← horizontal scroll <1280px
```

**Adrián Inbox** (3-modos + 3-col):
```
┌──────────────────────────────────────────────┐
│ [🤖 Decide•] [👀 Consulta] [✋ Manual]        │
├────────────┬─────────────────────┬───────────┤
│ Conversa-  │  Thread             │ Contacto  │
│ ciones     │                     │  sidebar  │
│ (240px)    │  (1fr)              │  (220px)  │
│ • María    │  María: "Hola..."   │  Nombre   │
│ • Carlos   │  Bot:   "Buen..."   │  Tel      │
│ • Lucía    │  ...                │  Origen   │
└────────────┴─────────────────────┴───────────┘
```

**Camila Voz** (3-modos + 3 cards):
```
┌──────────────────────────────────────────────┐
│ [🤖 Decide•] [👀 Curaduría] [✋ Manual]       │
├──────────────────────────────────────────────┤
│  ┌──────────────┐┌─────────────┐┌──────────┐│
│  │📥 Entrante   ││🔍 Curaduría ││🔁 Activos││
│  │     12       ││      4      ││    47    ││
│  │ ● mensajes   ││ ● en revis. ││ ● ciclos ││
│  └──────────────┘└─────────────┘└──────────┘│
└──────────────────────────────────────────────┘
```

**Valeria Agenda** (grilla 5d×8h):
```
┌──────────────────────────────────────────────┐
│ SubTabHeader: Agenda  [+ Crear cita]         │
│ Legend: 🟢Pagado 🟡Depósito 🔴Sin pago ⚫No-sh│
├──────┬─────┬─────┬─────┬─────┬─────┬─────────┤
│      │ Lun │ Mar │ Mié │ Jue │ Vie │         │
├──────┼─────┼─────┼─────┼─────┼─────┤         │
│ 09:00│     │     │🟢Mar│     │     │         │
│ 10:00│🟡Luc│     │     │     │🔴Ana│         │
│ ...  │ ... │ ... │ ... │ ... │ ... │         │
│ 17:00│     │⚫JP │     │🟢Sof│     │         │
└──────┴─────┴─────┴─────┴─────┴─────┴─────────┘
```

**Config Conexiones** (grid 6 categorías):
```
┌──────────────────────────────────────────────┐
│ SubTabHeader: Conexiones                     │
├──────────────────────────────────────────────┤
│ ┌─────────┐┌─────────┐┌─────────┐            │
│ │📣 Mark. ││💬 Mens. ││💳 Pagos ││            │
│ │ Meta·GA ││ WA·Mch  ││ Stripe  ││            │
│ └─────────┘└─────────┘└─────────┘            │
│ ┌─────────┐┌─────────┐┌─────────┐            │
│ │📅 Calen.││🌐 Pres. ││🔧 Técn. ││            │
│ │ GCal·Out││ Web·IG  ││ Webhk   ││            │
│ └─────────┘└─────────┘└─────────┘            │
└──────────────────────────────────────────────┘
```

### § 6.4 — HTML mockups (gate visual bloqueante per shell-mockup-per-component.md)

7 mockups expected (frontmatter cita paths):
1. `empty-states-grid.html` — navegable 22 sub-tabs con anchor links a las 6 secciones especiales + 16 cards muestra empty-state
2. `lisa-servicios-placeholder.html` — extract from `dual-mode-shell.html` sección equivalente
3. `adrian-embudo-placeholder.html` — extract `pipelinePreview()` líneas 1170+
4. `adrian-inbox-placeholder.html` — extract sección inbox 3-modos
5. `camila-voz-placeholder.html` — extract sección Camila voz 3-cards
6. `valeria-agenda-placeholder.html` — extract sección agenda grilla
7. `config-conexiones-placeholder.html` — extract sección conexiones grid

Serve local:
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups && python3 -m http.server 8888
```

Chris ratifica visualmente cada uno → `ratified_visual_by_chris: true` cementado en checkpoint.

---

## § 7 — Estados visuales

### § 7.1 — SubTabContent dispatcher

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `loading` | route transition (Next.js suspense) | Skeleton SubTabHeader + Skeleton card grid | Placeholder real |
| `genericEmpty` | subtab ∉ 6 especiales | SubTabHeader + EmptyState | Placeholder especial |
| `specialPlaceholder` | subtab ∈ 6 especiales | SubTabHeader + Special component | EmptyState |
| `notFound` | subtab inválido | not-found.tsx (intercepta antes que dispatcher) | SubTabContent |

### § 7.2 — Estados locales toggle (4 placeholders especiales con toggle)

| Placeholder | Toggle states | Default | Behavior |
|---|---|---|---|
| Lisa Servicios | `catalogo` / `escalera` | `catalogo` | switch local — catalogo muestra 5 cards, escalera muestra "Escalera de valor — próximamente" |
| Adrián Embudo | `kanban` / `lista` | `kanban` | switch local — kanban muestra 6 cols, lista muestra "Vista lista — próximamente" |
| Adrián Inbox | `decide` / `consulta` / `manual` | `decide` | switch local — decoración: chip activo cambia, contenido placeholder no cambia (Fase 2 cablea) |
| Camila Voz | `decide` / `curaduria` / `manual` | `decide` | switch local — idem |

Toggle state es `useState` local, no persiste cross-navegación (sub-tab change re-mounts placeholder).

---

## § 8 — Componentes (reutilizar > inventar)

| Componente | Path repo | Reutilizado vs nuevo |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | reuse (F1-S0) |
| `Tabs` | `vitalia/frontend/src/components/ui/tabs.tsx` | reuse (F1-S0) |
| `Badge` | `vitalia/frontend/src/components/ui/badge.tsx` | reuse (F1-S0) |
| `Card` | `vitalia/frontend/src/components/ui/card.tsx` | reuse (F1-S0) |
| `RIBBON_SUBTABS` (catalog) | `vitalia/frontend/src/lib/agent-catalog.ts` | reuse READ-ONLY (F1-S8) |
| `EmptyState` molécula | `vitalia/frontend/src/components/shared/shell-organism/EmptyState.tsx` | **NEW** (no existe equivalente) |
| `PlaceholderCard` molécula | `vitalia/frontend/src/components/shared/shell-organism/PlaceholderCard.tsx` | **NEW** |
| `SubTabHeader` molécula | `vitalia/frontend/src/components/shared/shell-organism/SubTabHeader.tsx` | **NEW** |
| `StatusDot` molécula | `vitalia/frontend/src/components/shared/shell-organism/StatusDot.tsx` | **NEW** |
| `TogglePill` molécula | `vitalia/frontend/src/components/shared/shell-organism/TogglePill.tsx` | **NEW** (wrapper styled de Shadcn Tabs) |
| `SubTabContent` organismo | `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` | **NEW** (dispatcher) |
| 22 placeholders (6 especiales + 16 genéricos) | `vitalia/frontend/src/features/{agent}/components/placeholders/{Subtab}Placeholder.tsx` | **NEW** (22 files) |
| ★ batch 2 — Inbox parity sales_studio | | |
| `CampaignTag` molécula | `vitalia/frontend/src/features/adrian/components/inbox/CampaignTag.tsx` | **NEW** (pattern from `ap_sales_agent/closer-studio`) |
| `ConversationItem` molécula | `vitalia/frontend/src/features/adrian/components/inbox/ConversationItem.tsx` | **NEW** (pattern from `ap_sales_agent/closer-studio`) |
| `MessageBubble` molécula | `vitalia/frontend/src/features/adrian/components/inbox/MessageBubble.tsx` | **NEW** (pattern from `ap_sales_agent/closer-studio`) |
| `MessageInput` molécula | `vitalia/frontend/src/features/adrian/components/inbox/MessageInput.tsx` | **NEW** (F1-S10 disabled state; Fase 2 cablea RHF + Zod) |
| `ContactSidebar` molécula | `vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.tsx` | **NEW** (pattern from `ap_sales_agent/closer-studio` con PHI masking visual) |
| ★ batch 2 — Agenda enriquecida | | |
| `AgendaToolbar` molécula | `vitalia/frontend/src/features/valeria/components/agenda/AgendaToolbar.tsx` | **NEW** (period nav + period toggle + Hoy + CTA dropdown) |
| `AgendaFilters` molécula | `vitalia/frontend/src/features/valeria/components/agenda/AgendaFilters.tsx` | **NEW** (F1-S10 disabled state) |
| `AgendaDayHeader` molécula | `vitalia/frontend/src/features/valeria/components/agenda/AgendaDayHeader.tsx` | **NEW** (today highlight) |
| `AgendaSlot` molécula | `vitalia/frontend/src/features/valeria/components/agenda/AgendaSlot.tsx` | **NEW** (paciente · service · doctor · origin · status pill) |
| `AgendaSummaryFooter` molécula | `vitalia/frontend/src/features/valeria/components/agenda/AgendaSummaryFooter.tsx` | **NEW** (Adrián+Lucas summary) |

**Justificación NEW (batch 2):** Inbox parity reusa el SHAPE/UX de `ap_sales_agent/frontend/src/features/closer-studio/components/inbox/` (8 componentes shipped) — Vitalia construye sus propios componentes brand-local (no cross-brand mirror prohibido per `.claude/rules/anti-duplication.md` § Multibrand awareness). El sales_studio shipped es referencia conceptual, no import. Si Fase 2 valida que el shape resiste y otras brands lo necesitan → `/pm-luana` lift a `core/luana-core-ui/inbox/` (futuro promotion candidate).

**Justificación NEW (foundational):** ninguno existe en codebase (`components/shared/shell-organism/` listado en context build NO contiene `EmptyState` / `SubTabContent` / placeholders). NoEmptyState existente en `components/shared/shell-organism/EmptyStateInline.tsx` es chat-specific (F1-S5/S6) — diferente molde (inline en chat thread vs page-level).

**Lift candidate cross-brand:** TogglePill + EmptyState + PlaceholderCard son patterns reusable cross-brand. Si comunify/lupulo/fitflow construyen shell similar Fase 2+ → escalá `/pm-luana` para lift a `core/luana-core-ui/` (futuro).

---

## § 9 — Data flow (conceptual, no técnico)

### F1-S10 (placeholder visual)

- **API endpoints consumidos:** NINGUNO (Fase 1 = mock-only)
- **React Query keys:** NINGUNAS
- **Mutations:** NINGUNAS
- **Form library:** N/A
- **Estado global:** `null` (todo toggle state es local `useState` excepto `sidebarOpen` en inbox placeholder — Zustand pattern preview)
- **Mock data location:** hardcoded en cada placeholder component (constantes top-of-file)
- **Mock data realista LatAm:** nombres (María, Carlos, Lucía, Ana, Sofía, JP), montos en PEN/USD según `tenant_locale.currency`, horarios formato 24h `tenant_locale.timezone`

### Fase 2 reuse map (★ documentado batch 2)

**F2-S3 `adrian-inbox`** hereda los patterns shipped del sales_studio (`ap_sales_agent/frontend/src/features/closer-studio/`):

| Pattern shipped | F2-S3 adopción |
|---|---|
| `useCloserStore` Zustand store | Crear `useInboxStore` en `features/adrian/store/inbox-store.ts` con `selectedLeadId`, `sidebarOpen`, `handlerMode` (global default), `handlerOverride` (Map<leadId, 'bot'\|'human'>), `filters` |
| URL searchParam `?lead=X` + `localStorage` fallback per-tenant | Replicar pattern de `InboxView.tsx` líneas 15-41 con key `inbox:lastLead:{tenantId}` |
| Widths shipped 320/flex/288 | Heredar exactos (F1-S10 ya los inicia visualmente) |
| ConversationItem temp-dot + stage-badge + channel-abbr + handler_mode border | Heredar mapping (`TEMP_DOT`, `STAGE_LABEL`, `getChannelAbbr`) |
| CampaignTag link a `/campanas/{id}` | Cambiar destino a `/{tenantId}/lucas/lanzar?campaign={id}` (campañas viven en Lucas en Vitalia, no en módulo Adrián) |
| `useTenantLocale` para `timezone` en formatDistanceToNow | Reusar hook ya shipped en F1-S0+ |
| ★ **Takeover real per-conversation** (NUEVO conceptual — sales_studio no lo tiene explícito) | `useInboxStore.takeControl(leadId)` muta `handlerOverride[leadId]='human'` + envía PATCH `/api/v1/inbox/conversations/{leadId}/handler` body `{mode:'human'}`; backend genera evento `conversation.handler.taken_over` que pausa el bot para ese lead específico; al `releaseControl(leadId)` mismo flujo con `mode:'bot'`. Persistencia: column `conversation.handler_override` Postgres (default `null` = sigue global) |
| ★ **Backend wiring takeover** (NUEVO) | Engine `core/luana-core-sales-agent` consulta `conversation.handler_override` antes de procesar mensaje entrante; si `'human'` → solo logea event + no genera respuesta. Cuando llega evento `release_control` → siguiente mensaje entrante el bot procesa normalmente. Probable `/pm-luana` promotion: extender Extension SDK EP-N `inbox_handler_override` para que otras brands lo opt-in |

**F2-S1 `valeria-agenda`** construye sobre los componentes de F1-S10:

| F1-S10 (placeholder) | F2-S1 (funcional) |
|---|---|
| `AgendaToolbar` period nav visual | Cablea `useAgendaWeek(weekStart)` React Query + nav real (±7 días, Hoy reset) |
| `AgendaFilters` disabled chips | Cablea Zustand `useAgendaFilters` + URL searchParam preservation |
| `AgendaSlot` mock | Cablea con `Appointment` DTO real (paciente_id + service_id + doctor_id + payment_status) |
| ContactSidebar NO existe en F1-S10 (inbox sí lo tiene) | NEW component `agenda/ContactSidebar.tsx` con payment subform + fiscal capa 2 + historial cronológico + cross-link a `/{tenantId}/adrian/inbox?lead={id}` |
| Sin PHI masking real | RBAC `@require_phi_access` server-side + masking server-side antes de retornar API response per hipaa-lite |

`/architect-fe` concreta cómo se cablea Fase 2 (probable: cada sub-tab story expone `useXxxList()` hook React Query que reemplaza el mock import).

---

## § 10 — Microcopy (Spanish neutro LatAm)

<!-- voseo-allowed: glosario reference -->

### § 10.1 — Strings genéricos EmptyState (16 sub-tabs)

| Slot | Copy |
|---|---|
| h2 SubTabHeader | "{Subtab label}" (de RIBBON_SUBTABS — ej. "Marca", "Doctores", "Outbound") |
| Description SubTabHeader | "Vista placeholder — el contenido real se cablea en Fase 2." (todos los 16 genéricos) |
| h3 EmptyState title | "{Subtab label} — próximamente" |
| Description EmptyState | "Esta vista vive acá. Cuando Fase 2 implemente {agent}/{subtab}, lo que ves cambiará." |

### § 10.2 — Strings placeholders especiales

**Lisa Servicios:**

| Slot | Copy |
|---|---|
| h2 | "Servicios" |
| Description | "Catálogo de tratamientos y escalera de valor (placeholder Fase 1)." |
| Toggle | "Catálogo" / "Escalera" |
| Card 1-4 nombre | "Limpieza dental" · "Blanqueamiento" · "Implante" · "Mantenimiento periodontal" |
| Card 5 CTA | "+ Nuevo tratamiento" |
| Escalera placeholder | "Escalera de valor — próximamente" |

**Adrián Embudo:**

| Slot | Copy |
|---|---|
| h2 | "Embudo" |
| Description | "Pipeline de leads en 6 estados (placeholder con leads ficticios)." |
| Toggle | "Kanban" / "Lista" |
| Cols header | "Interesado" · "Calificando" · "Considerando" · "Listo" · "Reservado" · "Decidió no" |
| Lista placeholder | "Vista lista — próximamente" |

**Adrián Inbox** (★ sales_studio parity):

| Slot | Copy |
|---|---|
| h2 | "Inbox" |
| Description | "Bandeja de conversaciones con tres modos de operación de Adrián." |
| Header subtitle global | "Modo por defecto para nuevas conversaciones · usa el control de cada conversación para overrides puntuales" |
| Toggle (3-modos global default) | "🤖 Adrián decide" / "👀 Te consulta" / "✋ Manual" |
| ★ Takeover button thread header (Adrián maneja) | "✋ Tomar el control" (tooltip: "Tomar el control de esta conversación · Adrián pausará aquí (no afecta otras convs)") |
| ★ Takeover banner title (usuario en control) | "Tienes el control · Adrián pausado en esta conversación" |
| ★ Takeover banner meta | "El modo global '🤖 Adrián decide' no se altera · solo aquí · puedes devolver el control cuando quieras" |
| ★ Takeover return button | "🤖 Devolver a Adrián" |
| ★ Thread footer hint state A (Adrián) | "Adrián decidirá la próxima respuesta automáticamente · clic ✋ Tomar el control arriba para responder tú" |
| ★ Thread footer hint state B (usuario) | "⚡ Estás respondiendo como tú · Adrián volverá a manejar la conversación cuando devuelvas el control" |
| ★ MessageInput placeholder state A (Adrián) | "🤖 Adrián decide automáticamente · toma el control para escribir tú" (disabled) |
| ★ MessageInput placeholder state B (usuario) | "Escribir como tú a {patient_name}…" (enabled, auto-focus) |
| ★ ConversationItem YouChip tooltip | "Tomaste el control · Adrián pausado en esta conversación" |
| ★ ConversationItem YouChip label | "✋ Tú" |
| ConversationList search placeholder | "Buscar conversación" |
| Mock conv. 1 (selected · hot · WA · Calificando · CampaignTag) | "María González" · "Hola, vi su anuncio sobre limp..." · "hace 2 min" · "📣 Limpieza-PE" |
| Mock conv. 2 (human-handled · warm · IG · Nuevo) | "Carlos Pérez" · "¿tienen turno mañana?" · "hace 8 min" · "✋ Manual" pill |
| Mock conv. 3 (cold · WA · Cerrando · CampaignTag) | "Lucía Ramos" · "Gracias por la info!" · "hace 1 h" · "📣 Blanqueamiento" |
| Mock conv. 4 (warm · WA · Negociando) | "Diego Flores" · "¿el blanqueamiento incluye...?" · "hace 3 h" |
| Mock conv. 5 (cold · WA · Cerrando) | "Sofía M." · "Confirmado el martes 10am" · "ayer" |
| Stage badges | "Nuevo" / "Calificando" / "Negociando" / "Cerrando" |
| Channel abbreviations | "WA" (WhatsApp) / "IG" (Instagram) / "TG" (Telegram) |
| Thread header handler_mode pill | "🤖 Adrián decidiendo" / "✋ Manual" |
| Thread divider (today) | "Hoy · {time}" |
| Thread mock messages | "Hola, vi su anuncio sobre limpieza dental. ¿Cuánto sale?" / "¡Hola María! La limpieza dental es S/ 120, dura 30 min. ¿Te agendo?" / "Sí, mañana al mediodía si tienen" / "Genial. Tengo disponible Mar 27 a las 12:00 con Dra. Soto. Te confirmo con un depósito de S/ 36 (30%). ¿Continúo?" |
| Thread footer hint | "Adrián decidirá la próxima respuesta automáticamente · cambia a 'Te consulta' o 'Manual' arriba para intervenir" |
| MessageInput placeholder | "Escribir mensaje… (Manual)" |
| ContactSidebar header | "Detalles paciente" |
| ContactSidebar fields | "Nombre" / "Teléfono" / "Email" / "Origen" / "Estado embudo" / "Etiquetas" |
| ContactSidebar PHI masking ejemplo | "+51 9** ***-4321" / "m***@gmail.com" (RBAC `@require_phi_access` cablea Fase 2) |
| ContactSidebar action buttons | "📅 Agendar cita" / "📋 Ver historial paciente" / "→ Pasar a embudo" |

**Camila Voz** (★ copy aclarado batch 2 — Chris feedback "no entiendo nada"):

| Slot | Copy |
|---|---|
| h2 | "Voz del paciente" |
| Description (★ aclarada) | "Camila pide feedback al paciente tras la visita y categoriza la respuesta para derivarla a reactivación, reputación o nueva venta." |
| Toggle (3-modos) | "🤖 Camila decide" / "🔍 Curaduría" / "✋ Manual" |
| Card 1 title | "Entrante" · valor "12" |
| Card 1 description (★ aclarada) | "Pacientes que respondieron — esperando que Camila analice y categorice" |
| Card 2 title | "Curaduría" · valor "4" |
| Card 2 description (★ aclarada) | "Casos ambiguos que necesitan tu revisión antes de derivar" |
| Card 3 title (★ renombrada) | "Ciclos activos" · valor "47" |
| Card 3 description (★ aclarada) | "Pacientes en flujo de seguimiento automático" |
| Footer (★ aclarado) | "Camila gestiona el ciclo de voz del paciente: te avisa cuando algo sale del patrón esperado · te ahorra responder cada feedback uno por uno." |

**Valeria Agenda** (★ enriquecido batch 2):

| Slot | Copy |
|---|---|
| h2 | "Agenda" |
| Description | "Tus turnos del día + cobranza · 6 días" |
| Toolbar period label (mock) | "Semana 26-31 May 2026" |
| Toolbar period toggle | "Día" / "Semana" / "Mes" (Semana active default) |
| Toolbar Hoy button | "📅 Hoy" |
| Toolbar CTA | "+ Crear cita ▾" |
| CTA dropdown opciones | "🚶 Walk-in · Paciente presente ahora" / "📞 Reserva por teléfono · Fecha futura" / "✉ Reagendar proactivamente · Desde un lead caliente" |
| Filters chips | "🔍 Buscar paciente" / "🩺 Doctor: Todos ▾" / "📋 Especialidad: Todas ▾" / "💰 Status pago: Todos ▾" / "☐ Solo riesgo no-show" / "☐ Solo walk-in" |
| Day headers labels | "Lun 26" / "Mar 27" / "Mié 28" / "Jue 29" / "Vie 30" / "Sáb 31" |
| Status pills verbatim | "✓ PAG" (verde) / "30%" (cian/depósito) / "SIN PAGO" (ámbar) / "⚠ NO-SHOW" (rojo, tachado) |
| Mock slots verbatim (paciente · service · doctor · origin) | "M. Rodríguez · Limpieza · Dr. Mendoza · ✓ PAG" · "S. López · Blanqueamiento · Dra. Soto · 30%" · "L. Vega 📞 · Consulta · Dra. Soto · 30%" · "J. Pérez · Consulta · Dr. Mendoza · 30%" · "A. Ruiz 🚶 · Consulta · Dr. Mendoza · SIN PAGO" · "P. Sosa · Endodoncia · Dr. Mendoza · ✓ PAG" · "M. Díaz ✉ · Blanqueamiento · Dra. Soto · 30%" · "R. Cruz · Consulta · Dr. Mendoza · 30%" · "C. Núñez · Consulta · Dr. Mendoza · histórico 2 faltas · ⚠ NO-SHOW" · "Sofía B. ✋ · Limpieza · Dra. Soto · ✓ PAG" |
| Lunch-time slots aria-label | "Horario de almuerzo" |
| Footer leyenda | "Pagado" / "30% depósito" / "Sin pago" / "No-show riesgo" |
| Footer origin icons hint | "🚶 walk-in · 📞 phone · ✉ proactiva" |
| Footer Adrián+Lucas summary | "Adrián propuso 4 turnos hoy · 3 sin pago · Lucas: 3 leads listos" |
| Doctores mock (consistencia cross-slots) | "Dr. C. Mendoza" / "Dra. M. Soto" |
| Services mock | "Consulta general" / "Limpieza dental" / "Blanqueamiento" / "Endodoncia" |

**Config Conexiones:**

| Slot | Copy |
|---|---|
| h2 | "Conexiones" |
| Description | "Integraciones externas agrupadas por categoría." |
| Cat 1 | "📣 Marketing — Meta Ads · Google Ads" |
| Cat 2 | "💬 Mensajería — WhatsApp · ManyChat" |
| Cat 3 | "💳 Pagos — Stripe · MercadoPago" |
| Cat 4 | "📅 Calendarios — Google Calendar · Outlook" |
| Cat 5 | "🌐 Presencia — Sitio web · Instagram" |
| Cat 6 | "🔧 Técnicas — Webhooks · API" |

### § 10.3 — not-found.tsx (F1-S9 cementado — solo referencia)

(No tocar — F1-S9 cementó copy.)

### § 10.4 — Spanish neutro check

NO voseo: prohibido `vos/sos/tenés/podés/dale/mirá/elegí/agregá/configurá/ofrecés`. NO regionalismos. SI tildes + ñ + apertura `¿!`. Validación: pre-commit hook `scripts/git-hooks/pre-commit` Section 4 voseo glosario.

---

## § 11 — Responsive breakpoints

| Breakpoint | Comportamiento |
|---|---|
| Mobile (< 768px) | Modo agentic NO disponible (F1-S4 cementó force `rail`). SubTabContent visible solo en modo rail = panel app full-width. Adrián Embudo Kanban → horizontal scroll. Adrián Inbox 3-col → stack vertical. Config grid 3×2 → 1×6. |
| Tablet (768-1023px) | Modo agentic 50/50 disponible (F1-S4). Cards grid 5 cols → 3 cols. Kanban 6 cols → horizontal scroll. |
| Desktop (≥ 1024px) | Layout completo per § 6 wireframes. Cards 5 cols inline. Kanban 6 cols visible. |

---

## § 12 — Accessibility

- `SubTabHeader` usa `<h2>` (single h2 per page; h1 vive en TopBarGlobal o page-level único)
- PlaceholderCard nombre usa `<h3>` (consistencia heading hierarchy)
- TogglePill = Shadcn Tabs con `role="tablist"` + `role="tab"` + `aria-selected` (free per Shadcn primitive)
- EmptyState description tiene `aria-live="polite"` (anuncia state change cuando toggle cambia)
- Kanban columnas tienen `aria-label="Embudo columna {label}, {count} leads, valor {value}"`
- Slot agenda mock: cada slot tiene `aria-label="Cita {paciente} {hora} día {dia} — {status}"`
- Contrast ratio ≥ 4.5:1 verificable con axe-core `wcag2aa`
- Keyboard navigation: Tab → next toggle pill / next sub-tab card; Space/Enter → activa
- Focus visible: `focus:ring-2 focus:ring-ring focus:ring-offset-2` (Vitalia tokens)
- Skip-link "Saltar al contenido" ya cementado en F1-S2 (no tocar)

---

## § 13 — Telemetría (Fase 2 prep — opcional, no obligatorio Fase 1)

```yaml
events:
  - { name: "subtab_viewed", trigger: "SubTabContent mount", props: ["agent", "subtab"] }
  - { name: "subtab_toggle_changed", trigger: "TogglePill click", props: ["agent", "subtab", "from_state", "to_state"] }
```

Decision: implementar instrumentación es opcional Fase 1 (no bloqueante). Si /architect-fe lo agrega como hook estándar `useTrackSubtabView()`, OK. Si lo difiere a Fase 2 first sub-tab story, también OK.

---

## § 14 — Brand voice

F1-S10 muestra texto chrome UI (placeholders + EmptyState messages). Spanish neutro estándar — NO per-tenant voice (sales_agent personality es solo para output sales_agent runtime). Copy aprobado verbatim per § 10.

---

## § 15 — Compliance scope (HIPAA-lite overlay)

**Aplica scope NO PHI:** mock data es completamente ficticia (nombres falsos, montos arbitrarios, horarios genéricos). NO toca `patient_*`, `medical_*`, `treatment_*`, `prescription_*`, `appointment_*` tablas reales. Cuando Fase 2 cablee data real:

- Valeria Agenda → toca `appointment_*` (subset hipaa-lite: tenant+clinic dual filter + audit log)
- Valeria Pacientes → toca `patient_*` (full hipaa-lite: encryption + audit + RBAC `@require_phi_access`)
- Adrián Inbox → toca conversaciones (subset: tenant+clinic dual filter)
- Camila Voz → toca feedback paciente (subset si data anonimizada, full si linked a paciente)

F1-S10 mismo NO requiere compliance gates — solo mock placeholders.

---

## § 16 — Batch 1 decisions cementadas 2026-05-26 (Chris)

| Q | Decisión | Razón |
|---|---|---|
| Q1 mockup strategy | **(A) Combo: 1 grid integral + 6 standalone** | Cumple overlay rule verbatim (mockup-per-component) + audit visual aislado por placeholder + grid integral sirve de "TOC visual" navegable |
| Q2 toggle interactivity | **(A) Funcionales JS local** | Chris valida UX completo "click pill → veo cambio" antes de implementar React (reduce ciclos audit Fase /dev-team) |
| Q3 header copy genérico | **(A) Uniforme** — "Vista placeholder — el contenido real se cablea en Fase 2." | Consistencia visual + agente da identidad suficiente vía icon + label |

## § 16.bis — Batch 2 cementadas 2026-05-26 (Chris)

| Q | Decisión | Razón |
|---|---|---|
| Q4 Inbox depth | **(A) Enriquecer con sales_studio parity** | F2-S3 hereda decisiones UX validadas en sales_studio shipped — evita reinventar +20% tiempo Fase 2 |
| Q5 Agenda depth | **(A) Enriquecer placeholder ahora** | Chris valida "agenda como cockpit de Adrián" desde Fase 1 + componentes React rich (toolbar/filters/grid/footer) listos para F2-S1 cablear data real |
| Q5.bis Agenda func scope | **F1 mockup full + F1 React full · F2 funcionalidad real** | F1-S10 mockup HTML + componentes React rich (visual completo), F2-S1 cablea: sidebar selectable, payment subform inline, fiscal capa 2 Nubefact PE, historial cronológico, cross-link inbox, filtros funcionales, PHI masking RBAC, useAgendaWeek React Query |

## § 16.ter — Batch 3 cementadas 2026-05-26 (Chris ratify autonomous defaults)

| Q | Decisión | Razón |
|---|---|---|
| Q8 Mateo scope | **Excluido** — catálogo SSoT `agent-catalog.ts::RIBBON_SUBTABS.mateo: []` confirma. No se construye `MateoPlaceholder` ni page route `/{tenantId}/mateo/{subtab}`. URL `/{tenantId}/mateo` → `not-found.tsx` jerárquico (F1-S9 cementado vía `isValidAgent("mateo") === false`). | Mateo es transversal agent (Mateo trabaja como dev, no tiene UI sub-tab dedicada) |
| Q9 Default landing | **`valeria/agenda`** — heredado de F1-S9 routing-shell ya cementado. F1-S10 NO cambia default landing | F1-S9 ya escribió el redirect; F1-S10 solo puebla los 22 sub-tab pages |
| Q10 Telemetría | **Defer a Fase 2** — `subtab_viewed` event NO se implementa en F1-S10. Cada sub-tab story F2-S{N} cablea su propio event al construir data real | Mínimo costo F1-S10, no bloquea. Telemetría sin datos reales (Fase 1 = mocks) sería ruido |

---

## § 17 — Deliverables (preview — `/architect` cierra exact)

| File | Acción | Owner ticket |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` | NEW | T-? (architect dicta) |
| `vitalia/frontend/src/components/shared/shell-organism/EmptyState.tsx` | NEW | T-? |
| `vitalia/frontend/src/components/shared/shell-organism/PlaceholderCard.tsx` | NEW | T-? |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabHeader.tsx` | NEW | T-? |
| `vitalia/frontend/src/components/shared/shell-organism/StatusDot.tsx` | NEW | T-? |
| `vitalia/frontend/src/components/shared/shell-organism/TogglePill.tsx` | NEW | T-? |
| ★ Inbox parity (sales_studio shipped) | | |
| `vitalia/frontend/src/features/adrian/components/inbox/CampaignTag.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/adrian/components/inbox/ConversationItem.tsx` | NEW (con YouChip cuando handler_mode='human') | T-? |
| `vitalia/frontend/src/features/adrian/components/inbox/MessageBubble.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/adrian/components/inbox/MessageInput.tsx` | NEW (state dual: disabled state A / enabled state B) | T-? |
| `vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.tsx` | NEW (F1-S10 con PHI masking visual) | T-? |
| ★ **Takeover UX** (NEW conceptual): | | |
| `vitalia/frontend/src/features/adrian/components/inbox/ThreadHeader.tsx` | NEW (2 estados A=Adrián / B=usuario) | T-? |
| `vitalia/frontend/src/features/adrian/components/inbox/TakeoverBanner.tsx` | NEW (banner amarillo state B) | T-? |
| ★ Agenda enriquecida | | |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaToolbar.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaFilters.tsx` | NEW (F1-S10 disabled state) | T-? |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaDayHeader.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaSlot.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaSummaryFooter.tsx` | NEW | T-? |
| `vitalia/frontend/src/features/lisa/components/placeholders/{Marca,Doctores,Servicios,Compliance}Placeholder.tsx` | NEW (4) | T-? |
| `vitalia/frontend/src/features/lucas/components/placeholders/{Lanzar,Envuelo,Recursos,Resultados,Mercado}Placeholder.tsx` | NEW (5) | T-? |
| `vitalia/frontend/src/features/adrian/components/placeholders/{Inbox,Embudo,Outbound,Propuestas}Placeholder.tsx` | NEW (4) | T-? |
| `vitalia/frontend/src/features/valeria/components/placeholders/{Agenda,Pacientes}Placeholder.tsx` | NEW (2) | T-? |
| `vitalia/frontend/src/features/camila/components/placeholders/{Voz,Reactivar,Multiplicar,Reputacion}Placeholder.tsx` | NEW (4) | T-? |
| `vitalia/frontend/src/features/config/components/placeholders/{Cuenta,Conexiones,Avanzado}Placeholder.tsx` | NEW (3) | T-? |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | MODIFY (replace placeholder con `<SubTabContent>`) | T-? |
| `vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/sc-01..10.spec.ts` | NEW (10 specs) | T-? |
| `vitalia/frontend/e2e/__screenshots__/visual/empty-states/` | NEW (44 goldens — 22 sub-tabs × light+dark) | T-? |
| Vitest unit tests por placeholder especial (6 files) | NEW | T-? |
| `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/*.html` | NEW (1 o 7 según Q1) | (po-ux owns) |

---

## § 18 — Próximo paso post-ratify

Una vez Chris ratifica `ratified_by_chris: true` + `ratified_visual_by_chris: true`:

1. `/po-ux` transitions `state: refining → refined` en checkpoint
2. AUTO-CHAIN → `/architect vitalia vitalia-fase1-empty-states` produce ready package (03-arch-fe.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml + § Test Construction Plan)
3. AUTO-CHAIN → `/dev-team vitalia vitalia-fase1-empty-states` autonomous build
4. AUTO-CHAIN → `/auditor vitalia vitalia-fase1-empty-states`
5. AUTO-CHAIN → `/pm-vitalia merge` cierra Fase 1

**Cierre Fase 1 expected.** Capability NEW `vitalia/docs/product/capabilities/shell-organism/empty-states.yaml` + module refresh `shell-organism.md` auto-list.
