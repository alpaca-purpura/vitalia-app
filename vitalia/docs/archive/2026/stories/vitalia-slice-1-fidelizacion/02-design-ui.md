# vitalia-slice-1-fidelizacion — Design UI

> **Mockup SSoT cementado Chris 2026-05-17:** `02-design-ui-mockup.html` (paleta 4 colores + chat-RIGHT rail + sidebar progresivo v3 + tabs verticales 5 patrones).
> **Tokens cementados:** `vitalia/frontend/src/app/globals.css` (CSS vars `--vitalia-cian`, `--vitalia-azul-marino`, `--vitalia-bg`, `--vitalia-text-muted`, etc.).

## § 1 — Component tree

```
app/(app)/fidelizacion/page.tsx                          ← Server Component thin
├── <AppShell>                                            ← shared/shell (consume Ola 0)
│   ├── <TopBar />                                        ← shared/shell
│   ├── <Sidebar />                                       ← shared/shell (slot ▮Fidelización activo)
│   ├── <main>                                            ← /fidelización area
│   │   └── <FidelizacionLayout>                          ← features/fidelizacion/components NEW
│   │       ├── <FidelizacionKPIsHero />                  ← NEW 5 stat cards (Pacientes seguim · Próximos abandonar · Tasa retorno · Re-engaged · NPS secundaria)
│   │       ├── <FidelizacionTabsBar />                   ← NEW 5 tabs verticales (Shadcn Tabs + counts dynamic)
│   │       ├── <FidelizacionActivityFooter />            ← NEW activity sticky bottom
│   │       └── <Outlet/Tab content based on URL state>
│   │           ├── <MultiSessionTab />                   ← Patrón 1
│   │           ├── <FollowUpTab />                       ← Patrón 2
│   │           ├── <MaintenanceTab />                    ← Patrón 3
│   │           ├── <AbsenceTab />                        ← Patrón 4
│   │           └── <NPSResumenTab />                     ← NPS reducido Slice 1
│   ├── <ContactSidebar slot="right" collapsible>         ← shared/contact-sidebar (consume Ola 0)
│   │   └── <ReEngagementContactSidebar />                ← features/fidelizacion (composes ContactSidebar shared + content)
│   └── <CopilotRail slot="right" idle 80px>              ← shared/copilot-rail (consume Ola 0)
└── (Modals — portal)
    ├── <ConfirmTemplateModal />                          ← NEW (Adrián recordatorio antes envío)
    ├── <SuggestSlotsModal />                             ← NEW (Sugerir 3-5 slots disponibles)
    ├── <PausePatientModal />                             ← NEW (motivo + duration)
    └── <ManualCallLoggedModal />                         ← NEW (Llamar manual + outcome)
```

**Common card across tabs:** `<ReEngagementCard variant={pattern}>` polymorphic — renderiza headline/badges/acciones según `pattern` prop (1 componente NEW, 4 variantes visual).

## § 2 — Reuse explícito (Nicolify)

| Component need | Reuse from | Adapter required |
|---|---|---|
| Cards layout + lifecycle buttons base | `nicolify/frontend/src/features/campaigns-lite/components/{CampaignDetailClient,CampaignLifecycleButtons,CampaignStatsCard}.tsx` | Token overrides (HEX → vitalia CSS vars). Strip Nicolify-specific copy. Add `<RequireRole>` PHI gate wrapper. |
| Notification card rendering | `nicolify/frontend/src/features/notifications/components/{NotificationCard,NotificationCenter,NotificationPanel}.tsx` | Same token overrides. Use for `ConfirmTemplateModal` preview area. |
| Notification hooks + store | `nicolify/frontend/src/features/notifications/{hooks,store}/` | Reference pattern only — Vitalia notifications go through Adrián sales_agent proactive_outbound (NOT in-app notifications layer). Fork copy paste hooks shape, point at `vitalia/frontend/src/features/fidelizacion/api/*` endpoints. |
| Campaign API hook patterns (React Query mutation + invalidation keys) | `nicolify/frontend/src/features/campaigns-lite/api/use-*-mutation.ts` | Same pattern: `useMutation` + `queryClient.invalidateQueries(['fidelizacion', pattern])` on success. |
| Empty state illustration + microcopy pattern | `nicolify/frontend/src/features/*/components/EmptyState*.tsx` | Vitalia tokens + microcopy LatAm neutro. Replace mariposa illustration with placeholder Slice 1 (SVG inline). |

**Cross-brand mirror flag:** `<ReEngagementCard>` + `<ConfirmTemplateModal>` + `<PausePatientModal>` son patterns potencialmente repetibles en otra brand (creator economy comunify usa re-engagement curso). Si pattern aparece en >1 brand → lift to `@luana/ui-kit` o `core/luana-core-fidelizacion/` (futuro paquete). Promotion gate `/pm-luana` post Slice 2.

## § 3 — Componentes NEW Vitalia (mapping)

| Componente | Path | Rationale |
|---|---|---|
| `<FidelizacionLayout>` | `vitalia/frontend/src/features/fidelizacion/components/FidelizacionLayout.tsx` | Página orquestadora — KPIs + Tabs + Activity footer |
| `<FidelizacionKPIsHero>` | `.../components/FidelizacionKPIsHero.tsx` | 5 stat cards horizontal — consume `useFidelizacionSummary()` hook |
| `<FidelizacionTabsBar>` | `.../components/FidelizacionTabsBar.tsx` | Shadcn `<Tabs>` + counts dynamic per pattern |
| `<FidelizacionActivityFooter>` | `.../components/FidelizacionActivityFooter.tsx` | Activity stream sticky bottom — consume `useReEngagementActivity()` |
| `<MultiSessionTab>` | `.../components/tabs/MultiSessionTab.tsx` | Patrón 1 lista (urgency descending) |
| `<FollowUpTab>` | `.../components/tabs/FollowUpTab.tsx` | Patrón 2 lista |
| `<MaintenanceTab>` | `.../components/tabs/MaintenanceTab.tsx` | Patrón 3 lista |
| `<AbsenceTab>` | `.../components/tabs/AbsenceTab.tsx` | Patrón 4 lista (con opt-in guard UI) |
| `<NPSResumenTab>` | `.../components/tabs/NPSResumenTab.tsx` | NPS tabla reducida Slice 1 (sin chart) |
| `<ReEngagementCard variant={pattern}>` | `.../components/ReEngagementCard.tsx` | Polymorphic 4 variantes (multi_session / follow_up / maintenance / absence) |
| `<NPSRowCompact>` | `.../components/NPSRowCompact.tsx` | NPS tabla row |
| `<ReEngagementContactSidebar>` | `.../components/ReEngagementContactSidebar.tsx` | Composes shared `<ContactSidebar>` + timeline + acciones contextuales |
| `<ConfirmTemplateModal>` | `.../components/ConfirmTemplateModal.tsx` | Preview WA + variables auto-fill + [Cancelar] / [Enviar template] |
| `<SuggestSlotsModal>` | `.../components/SuggestSlotsModal.tsx` | Calendar mini + 3-5 slots disponibles (consume `availabilityApi.getOpenSlots`) |
| `<PausePatientModal>` | `.../components/PausePatientModal.tsx` | Duración (7d/30d/custom) + razón + confirm |
| `<ManualCallLoggedModal>` | `.../components/ManualCallLoggedModal.tsx` | Notas + outcome radio (Sí vendrá / No lo perdimos / Pendiente) |
| `<NPSTagBadge>` | `vitalia/frontend/src/components/shared/nps/NPSTagBadge.tsx` | Chip compartido cross-feature (verde 9-10 · amarillo 7-8 · rojo 0-6) |
| `<MaintenanceScheduleField>` | `vitalia/frontend/src/features/offer-studio/components/MaintenanceScheduleField.tsx` | Slice 1 stub Form select (option_3m/6m/yearly/custom) — defer UI completo offer-studio Slice 2 |
| `<FollowUpField>` | `vitalia/frontend/src/features/agenda/components/FollowUpField.tsx` | Cross-link Batch 4 retro — OWNED by /agenda story Ola 3 (NOT this story) |

## § 4 — Hooks (React Query)

| Hook | Endpoint | Cache key | Description |
|---|---|---|---|
| `useFidelizacionSummary({period})` | `GET /api/v1/vitalia/fidelization/summary` | `['fidelizacion', 'summary', period]` | 5 KPIs hero (Pacientes seguim · Próximos abandonar · Tasa retorno · Re-engaged · NPS) |
| `useReEngagementPatterns({pattern, filters})` | `GET /api/v1/vitalia/fidelization/re-engagement/patterns?pattern={x}&filters={}` | `['fidelizacion', pattern, filters]` | Pattern listing per tab |
| `useNPSResponses({period})` | `GET /api/v1/vitalia/fidelization/nps/summary?period={x}` | `['fidelizacion', 'nps', period]` | NPS lista reducida tab |
| `useReEngagementActivity({limit=20})` | `GET /api/v1/vitalia/fidelization/activity-stream?limit={n}` | `['fidelizacion', 'activity', limit]` | Activity footer stream |
| `useSendProactiveTemplate()` | `POST /api/v1/vitalia/fidelization/patients/{patient_id}/send-proactive` | invalidates `['fidelizacion', *]` + `['inbox', 'conversations']` | Mutation Adrián recordatorio |
| `usePausePatient()` | `POST /api/v1/vitalia/fidelization/patients/{patient_id}/pause` | invalidates pattern listing | Mutation pause |
| `useMarkExternal()` | `POST /api/v1/vitalia/fidelization/patients/{patient_id}/mark-external` | invalidates pattern listing | Mutation silence external |
| `useMarkNoContinue()` | `POST /api/v1/vitalia/fidelization/patients/{patient_id}/mark-no-continue` | invalidates pattern listing | Mutation marcar paciente decidió no |
| `useLogManualCall()` | `POST /api/v1/vitalia/fidelization/patients/{patient_id}/manual-call` | invalidates pattern listing | Mutation registrar llamada manual |
| `useSubmitNPS()` (paciente external — webhook) | `POST /api/v1/vitalia/fidelization/nps/submit` | n/a (webhook desde Adrián backend) | Patient NPS response submission |
| `useAvailabilitySlots({doctorId, dateRange})` | `GET /api/v1/vitalia/agenda/availability` | `['agenda', 'availability', doctorId, dateRange]` | Slot suggestions modal (CONSUME desde agenda) |

## § 5 — URL state (nuqs)

```ts
// features/fidelizacion/types/url-state.ts
export const fidelizacionParsers = {
  tab: parseAsStringEnum(['multisession', 'followup', 'maintenance', 'absence', 'nps']).withDefault('multisession'),
  period: parseAsStringEnum(['7d', '30d', '90d']).withDefault('30d'),
  vertical: parseAsString,                                  // dental | estetica | psicologia | otro
  doctor: parseAsString,                                    // doctor_id filter
  urgency: parseAsArrayOf(parseAsStringEnum(['critical', 'alert', 'near', 'waiting', 'up_to_date'])),
  selectedPatient: parseAsString,                           // patient_id → ContactSidebar open
  pauseModal: parseAsString,                                // patient_id → PausePatientModal open
  confirmTemplateModal: parseAsString,                      // re_engagement_event_id → ConfirmTemplateModal open
  manualCallModal: parseAsString,                           // patient_id → ManualCallLoggedModal open
  suggestSlotsModal: parseAsString,                         // patient_id → SuggestSlotsModal open
};

// tab/period/vertical/doctor/urgency/selectedPatient/modals = replace (sub-state)
// "Ver conversación" click → router.push('/inbox?lead={conv_id}') = push history
// "Ver turno" click → router.push('/agenda?selectedSlot={appt_id}') = push history
```

## § 6 — Estados visuales por componente

### `<FidelizacionLayout>` (page-level)
- `idle` mount: skeleton stat cards + tabs + empty list
- `loading`: spinner overlay
- `success`: data
- `error`: banner rojo + skeleton holds

### `<ReEngagementCard>`
- `urgency=critical` ⚠ CRÍTICO: border-l-rojo 3px + bg-rojo/0.05 + ícono `alert-octagon`
- `urgency=alert` ⚠ ALERTA: border-l-naranja + bg-naranja/0.05 + ícono `alert-triangle`
- `urgency=near` ⚠ PRÓXIMO: amber + ícono `clock-alert`
- `urgency=waiting` ✓ ESPERANDO: gris + ícono `clock` + texto "Adrián envió recordatorio hace {time_ago}"
- `urgency=up_to_date` ✓ AL DÍA: verde + ícono `check-circle` (solo visible si filter urgency incluye)
- `paused`: gris + chip "Pausado hasta {date}" + razón + ícono `pause-circle`

### `<AbsenceTab>` Patrón 4 — opt-in guard
- Si `patient.marketing_opt_in=false`: botón `[📲 Adrián WA]` aparece `disabled cursor-not-allowed` + tooltip "Paciente no aceptó marketing. Llamar manualmente o pedir opt-in en próxima visita."
- Botón `[📞 Llamar manual]` siempre activo (no requiere opt-in)

### `<ConfirmTemplateModal>`
- Preview WA template + variables auto-fill ({patient_name}, {offer_label}, {next_slot_date_1..3}, {follow_up_reason} si patrón 2)
- 2 botones: `[Cancelar]` (gris) / `[✓ Enviar template]` (vitalia-cian)
- Loading state on submit: spinner inline en botón + disable inputs
- Success: toast verde "Recordatorio enviado · {patient}" + modal close + invalidate queries
- Error: toast rojo "Envío template falló — {error_kind}" + modal stays open + retry button

## § 7 — Accesibilidad (WCAG 2.1 AA)

- KPIs hero: cada stat card con `role="status"` + `aria-label="{kpi_name}: {value}, {trend} vs período anterior"`
- Tabs verticales: Shadcn `<Tabs>` nativos cumplen ARIA. `aria-orientation="vertical"`.
- Cards re-engagement: keyboard nav `Tab` → expand on `Enter`. `[Adrián recordatorio]` button `aria-describedby={tooltip-if-disabled}`.
- Modal `<ConfirmTemplateModal>`: focus trap + `aria-modal="true"` + `aria-labelledby={title}` + Escape closes.
- Contraste tokens: validado en design-system.md § Contrast ratios. `--vitalia-text-muted` sobre `--vitalia-bg` >= 4.5:1.

## § 8 — Microcopy centralizado (`vitalia/frontend/src/features/fidelizacion/copy.ts`)

Spanish neutro LatAm estricto (tuteo `tú` — NO voseo, NO regionalismos). Glosario completo heredado del parent spec § Microcopy. Cero hardcoded JSX strings — arch fitness test `test_no_hardcoded_strings.test.ts` enforces.

Keys principales:
- `page.{title, subtitle}`
- `kpis.{patients_in_followup, near_abandonment, return_rate, re_engaged_this_month, nps_average, ...}`
- `tabs.{multi_session, follow_up, maintenance, absence, nps}`
- `urgency.{critical, alert, near, expired, waiting, up_to_date}`
- `actions.{send_reminder, suggest_slots, pause_patient, mark_external, mark_no_continue, open_conversation, call_manually}`
- `multi_session_card.{template, gap_label, sent_reminder_waiting, paused}`
- `follow_up_card.{template, requested_label, due_label, reason_label, reason_default}`
- `maintenance_card.{template, cadence_label, last_service_label, next_recommended}`
- `absence_card.{template, last_appointment_label, lifetime_label, last_doctor_label, opt_in_enabled, opt_in_disabled, opt_in_disabled_tooltip}`
- `nps_card.{score_label, comment_truncated, tag_inbox_label}`
- `send_reminder_confirm.{title, preview_label, variables_label, cta_cancel, cta_send, success_toast}`
- `pause_modal.{title, duration_label, duration_7d, duration_30d, duration_custom, reason_label, reason_placeholder, cta_cancel, cta_confirm, success_toast}`
- `empty_states.{multi_session_all_ok, follow_up_all_ok, maintenance_all_ok, absence_all_engaged, nps_no_responses}`
- `states.{loading, error, agent_thinking, agent_waiting_approval, agent_failed}`
- `activity_footer.template`

(Schema completo verbatim heredado parent spec — `FIDELIZACION_COPY` constants Latam neutro · 70+ keys.)

## § 9 — Performance budgets

- Page mount → LCP `<FidelizacionKPIsHero>` skeleton + first card render < 2.5s
- Tab switch INP < 200ms (React Query cache prefetched onHover ideally)
- Cards list virtualization si > 50 cards (use `@tanstack/react-virtual`)
- `<ConfirmTemplateModal>` preview area lazy load on open (no inline render de 5 templates)
- Image avatars `<AgentAvatar>` SVG inline (no remote img — evita CLS)

## § 10 — Storybook coverage (mandatory cross-cutting policy)

Cada componente NEW tiene `.stories.tsx` cubriendo: default state · loading · error · empty · all urgency variants · opt-in disabled (absence) · paused. Stories en `vitalia/frontend/src/features/fidelizacion/components/*.stories.tsx`.

## § 11 — Referencias visuales

- Mockup SSoT: `02-design-ui-mockup.html` (428 líneas)
- Design system: `vitalia/docs/architecture/design-system.md`
- Tokens: `vitalia/frontend/src/app/globals.css`
- Parent spec § Componentes mapping: `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/01-spec.md` (líneas 2947-2978)
- Parent spec § Microcopy: `01-spec.md` (líneas 2979-3115)
