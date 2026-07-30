# vitalia-slice-1-fidelizacion — Spec (extracted from parent)

> **Story:** `vitalia-slice-1-fidelizacion` · **Brand:** vitalia · **State:** refined → ready
> **Origen:** recorte directo del parent `vitalia-ux-discovery` (archived 2026-05-20) Batch 5 §§ Ruta /fidelización ratificado Chris 2026-05-17 + reframe scope.
> **Scope locked:** 4 patrones re-engagement automatizado + NPS reducido stat card + 6 cron jobs + 5 templates Meta-approved + tag cross-ruta /inbox (consumer). Detractor flow + dashboard NPS completo + Google Reviews + birthday → Slice 2 ideas.

## § 1 — JTBD + Diferenciador

**JTBD #4 P1 (refraseado Batch 5):** *"Maximizar la vuelta de pacientes existentes."* Vitalia automatiza 4 patrones de re-engagement con Adrián disparando proactive_outbound preservando atribución agentic correcta. Costo per re-engagement = 5-10× menos que adquisición lead nuevo (industria salud LATAM).

**Diferenciador:** ningún competidor LATAM (cero · botclinico · rendu · dentalink · doctocliq) tiene re-engagement agentic vivo. Vitalia primero.

## § 2 — Layout (Tabs verticales 5 totales — heredado mockup `02-design-ui-mockup.html`)

```
TopBar 56px · Sidebar 240px · MAIN ── ContactSidebar 280px collapsible ── Copilot Rail 80px idle
                                       │
KPIs hero (5 stat cards en línea):     │
  Pacientes seguim · Próximos abandonar · Tasa retorno · Re-engaged este mes · NPS promedio (secundaria)
                                       │
Tabs verticales por patrón (5):        │
  ▮ Tratamientos en curso  [12]        │  ← default activo (mayor volumen alertas)
    Follow-ups médicos       [5]       │
    Mantenimientos peri.    [23]       │
    Ausencias prolongadas    [8]       │
    NPS recibido (resumen) [142]       │  ← stat card reducido Slice 1
                                       │
Cards re-engagement por paciente con urgency + acciones inline
Activity footer: "Adrián envió N recordatorios hoy · sistema ejecutó cron X"
```

**Defaults tab activa al entrar:** `multisession` (Tratamientos en curso).

**Row click** → `ReEngagementContactSidebar 280px` PHI-aware (audit log on open) muestra paciente · tratamiento completo (offer + plan multi-sesión 4/12 + último servicio + próximo agendado) · doctor · timeline cronológico eventos re-engagement · acciones contextuales (Reservar siguiente sesión · Cambiar template · Pausar paciente N días · Abrir conv Adrián · Marcar paciente abandonó voluntario).

## § 3 — 4 patrones re-engagement (matrix completa SSoT)

| # | Patrón | Tab UI | Trigger detection | Cron job | Acción agentic |
|---|---|---|---|---|---|
| **1** | Tratamiento multi-sesión incompleto | Tratamientos en curso | `offer.requires_multi_session=true` + `treatment_plans.sessions_completed < sessions_expected` + `last_session_at + offer.gap_alert_days < now()` | `multi_session_gap_sweep` daily 07:00 UTC | Adrián WA template `recordatorio_proxima_sesion` + 3 slot suggestions próximos 7d |
| **2** | Follow-up médico programado | Follow-ups médicos | `appointments.follow_up_due_at <= now() + 7d` AND no new appointment booked since `follow_up_due_at` | `follow_up_due_sweep` daily 07:30 UTC | Adrián WA template `recordatorio_control_doctor` |
| **3** | Mantenimiento periódico | Mantenimientos periódicos | `offers.maintenance_schedule != none` + `last_appointment(patient, offer).completed_at` + cadencia vencida | `maintenance_due_sweep` daily 08:00 UTC (evaluación) · efectivo mensual | Adrián WA template `invitacion_mantenimiento` |
| **4** | Ausencia prolongada (re-engagement frío) | Ausencias prolongadas | `patient.last_appointment_at < now() - 6m` AND `lifetime_appointments >= 1` AND NOT marked decidió_no_continuar AND NOT `opt_out` | `absence_sweep` weekly Mon 06:00 UTC | Adrián WA template `re_engagement_ausencia` (MARKETING — opt-in obligatorio) |
| (NPS) | NPS post-tratamiento (reducido) | NPS recibido | `appointments.balance_status=full_paid` + 24h elapsed (configurable per offer Slice 2) | `nps_post_treatment_sweep` hourly :15 | WA template `nps_post_tratamiento` (sistema, no Adrián directo) |

**Cementado cross-pattern (invariants):**
- Cada disparo agentic = `proactive_outbound` origin · atribución `"Adrián abrió conversación · solicitado por sistema (cron {nombre})"`
- Templates Meta-approved per categoría:
  - **UTILITY** (no requieren opt-in): `recordatorio_proxima_sesion` · `recordatorio_control_doctor` · `invitacion_mantenimiento`
  - **MARKETING** (requieren opt-in checkbox consentimiento clínica): `re_engagement_ausencia` · `nps_post_tratamiento`
- Throttle: 1 reminder per pattern per paciente per 7d MINIMUM (regulación + UX)
- Si paciente responde dentro 24h → conv normal flow Adrián + posible lead /pipeline Stage Interesado si reserva nueva
- Si NO responde 7d → marcar `re_engagement_events.outcome=not_responsive`
- Operador puede pausar re-engagement per paciente con razón + duration (CRM card toggle `do_not_contact_re_engagement`)
- Re-engagement events NO contaminan analytics ventas (cohort separado pipeline)
- `opt_out=true` → paciente NUNCA re-aparece en ningún tab (filter cron + UI)

## § 4 — NPS stat card secundaria (Slice 1 reducido)

Vista compacta sin chart distribución (defer Slice 2):

```
Paciente     │ Score │ Comentario corto       │ Fecha     │ Tag /inbox
M. Rodríguez │ 10 ★ │ "Excelente trato..."   │ 18 May    │ ✓ tagged
J. Pérez     │  9   │ "Muy bien"              │ 18 May    │ ✓ tagged
A. Ruiz      │  4 ⚠│ "Esperé mucho..."       │ 17 May    │ ✓ tagged
```

**Slice 1 limit explícito:** sin chart distribución promotores/pasivos/detractores · sin detractor flow agentic · sin Google Reviews CTA · sin Owner notification escalation. Stat card hero "NPS promedio: 72 (142r)" + tag cross-ruta `/inbox` + historial `/pipeline` (Slice 2) cubren visibilidad mínima viable.

**Cross-ruta tag NPS (consumer — produced por fidelización, consumed por inbox):**
- `/inbox` conv list: chip `🌟 NPS {N}` visible per conv (verde 9-10 / amarillo 7-8 / rojo 0-6)
- `/inbox` thread header: badge NPS persistente
- `/pipeline` card historial (Slice 2 re-engaged): scores históricos del paciente

## § 5 — Cross-link /agenda (consumer — RETRO-ADD Batch 4)

ContactSidebar /agenda al marcar turno completado (`status → completed`) agrega sección opcional **"Follow-up médico programado"**:

```
¿Doctor pidió control de seguimiento?  ⚪ No  ◉ Sí
Volver en: [____] [días ▾ / semanas / meses / años]
Razón opcional: [textarea]
[Guardar follow-up]
```

**Captura:**
- Doctor o recepción (si doctor dictó) llena el campo
- Backend graba `appointments.follow_up_due_at = appointment.completed_at + N days_or_months` + `appointments.follow_up_reason`
- audit_log row "follow_up_set" con responsable
- Card aparece en `/fidelización` Tab "Follow-ups médicos" T-7d antes vencimiento

**Producer:** /agenda (Ola 3 — separate story). **Consumer:** /fidelización Patrón 2.
**Slice 1 scope:** Ola 1 fidelización **NO** implementa la captura en /agenda (eso vive en Ola 3). PERO sí consume `appointments.follow_up_due_at` cuando esté seteado (column ya existe en engine post promotion proposal `core-platform-extensions-slice-1`).

## § 6 — Cross-link /offer-studio — `maintenance_schedule` config Slice 1 stub

Field NEW Slice 1 dependency (sin él, Tab Mantenimientos no funciona):

```python
# core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py (engine promotion gate)
class Offer:
    requires_multi_session: bool = False
    sessions_expected: int | None = None
    gap_alert_days: int | None = None
    maintenance_schedule: MaintenanceSchedule = MaintenanceSchedule.NONE  # NEW
    maintenance_custom_days: int | None = None

class MaintenanceSchedule(str, Enum):
    NONE = "none"
    EVERY_3_MONTHS = "every_3_months"
    EVERY_6_MONTHS = "every_6_months"
    YEARLY = "yearly"
    CUSTOM_DAYS = "custom_days"
```

**Engine defaults per offer-type vertical** (Slice 1 hardcoded defaults — brand override):

| offer_type | maintenance_schedule default |
|---|---|
| `consulta_general_dental` | NONE |
| `limpieza_dental` | EVERY_6_MONTHS |
| `implante_dental` | YEARLY (control anual) |
| `ortodoncia` | NONE (multi-session covered Patrón 1) |
| `depilacion_laser_maintenance` | EVERY_3_MONTHS |
| `consulta_estetica` | NONE |
| `tratamiento_estetico_facial` | EVERY_3_MONTHS |
| (default) | NONE |

**Slice 1 scope:** ruta `/offer-studio` no entra Slice 1. Field se persiste en DB (cols ya creadas post promotion proposal) + endpoint admin update + defaults hardcoded per vertical. UI `/offer-studio` para editar es **defer Slice 2**. Patrón 3 lee `offers.maintenance_schedule` runtime — funciona ya con defaults seedeados.

## § 7 — Gherkin scenarios (4 obligatorios — AI-resistant)

### SC-01 (happy) — Multi-sesión detecta + Adrián recordatorio + paciente reagenda

```gherkin
Scenario: Cron detecta ortodoncia incompleta + Adrián recordatorio + paciente reagenda
  Given paciente "M. Rodríguez" tenant_id=A clinic_id=Sanaré-MX tiene treatment_plan ortodoncia activo
  And sessions_completed=4, sessions_expected=12, last_session_at=2026-04-18
  And offer.gap_alert_days=30 (ortodoncia default)
  When cron `multi_session_gap_sweep` ejecuta 2026-05-19 07:00 UTC
  Then detecta gap_days=31 > 30 → urgency=CRÍTICO
  And inserta row en `vitalia_re_engagement_events` con pattern=multi_session + trigger_at=now + audit_log_id
  And operadora dr.demo ve card en /fidelización Tab "Tratamientos en curso" con badge ⚠ CRÍTICO
  When operadora click [📲 Adrián recordatorio WA]
  Then modal ConfirmTemplateModal abre con preview WA template `recordatorio_proxima_sesion` + 3 slot suggestions auto-fill
  When operadora click [✓ Enviar template]
  Then backend dispatch proactive_outbound con conversations.origin=proactive_outbound, attribution="Adrián abrió conv · solicitado por sistema (cron multi_session_gap_sweep) confirmado operador {dr.demo.id}"
  And Adrián envía template WA a paciente
  And re_engagement_events row update outcome=sent + sent_at=now
  And card en /fidelización refresca urgency → ✓ ESPERANDO
  When paciente responde "Sí, mañana 10:00 me viene bien" dentro 24h
  Then conv aparece /inbox como activa con tag re_engagement linked
  And re_engagement_events update outcome=responded + response_at=now
```

### SC-02 (negative) — Ausencia prolongada SIN opt-in MARKETING

```gherkin
Scenario: Paciente sin opt-in marketing detectado, operador no puede enviar Adrián
  Given paciente "L. Vega" tenant_id=A clinic_id=Sanaré-MX con last_appointment_at=2025-11-15 (>6m sin venir)
  And lifetime_appointments=8, valor histórico $1200 MXN
  And patient.marketing_opt_in=false (no firmó consentimiento marketing)
  When cron `absence_sweep` ejecuta 2026-05-19 06:00 UTC
  Then detecta ausencia + crea re_engagement_events row pattern=absence
  And operadora ve card en Tab "Ausencias prolongadas"
  But botón [📲 Adrián WA] aparece deshabilitado + tooltip "Paciente no aceptó marketing. Llamar manualmente o pedir opt-in en próxima visita."
  When operadora click [📞 Llamar manual]
  Then audit_log row "manual_call_initiated_re_engagement"
  And modal "Llamada registrada" con campo notas opcional
  And operadora marca "Sí, vendrá" / "No, lo perdimos" / "Pendiente revisar"
```

### SC-03 (edge) — Follow-up médico T-7d antes vencimiento

```gherkin
Scenario: Doctor pidió volver en 3 meses + cron alerta T-7d antes
  Given operadora "Carla" tiene /agenda turno "C. Núñez" completado 2026-02-15
  And appointments.follow_up_due_at=2026-05-15, follow_up_reason="control implante" (capturado /agenda — Ola 3)
  When cron `follow_up_due_sweep` ejecuta 2026-05-08 07:30 UTC
  Then detecta follow_up_due_at - now() <= 7d → urgency=PRÓXIMO
  And card aparece en Tab "Follow-ups médicos" con badge ⚠ PRÓXIMO + razón visible
  When cron ejecuta 2026-05-16 07:30 UTC (post vencimiento)
  Then urgency=VENCIDO
  When operadora click [📲 Adrián recordatorio]
  Then template `recordatorio_control_doctor` enviado con variable {follow_up_reason}="control implante"
  And card update urgency=ESPERANDO
```

### SC-04 (adversarial) — opt-out + cross-tenant + PHI + XSS

```gherkin
Scenario: Adversarial intentos protegidos
  Given paciente "X. Adv" tenant_id=A clinic_id=Sanaré con opt_out=true (anteriormente respondió "STOP")
  When cron `absence_sweep` evalúa este paciente
  Then card NO aparece en Tab "Ausencias prolongadas" (filtro opt_out=true excluye)
  And NO se envía Adrián template aún si operador intentara manual
  When operador tenant_id=A intenta GET /api/v1/vitalia/fidelization/re-engagement/patterns?patient_id={cross_tenant_id}
  Then 404 not_found (dual filter tenant+clinic bloquea)
  When operador con role=marketing intenta acceder /fidelización card detalle (PHI clínica)
  Then 403 Forbidden + audit_log row "unauthorized_phi_access_attempted role=marketing"
  When operador modifica notes PausePatientModal con XSS payload "<script>alert(1)</script>"
  Then backend sanitiza server-side via DOMPurify-equivalent
  And tabla `vitalia_re_engagement_events.notes` almacena encoded safe
  And render frontend escapes correctamente (no execute)
```

## § 8 — Estados visuales (8)

| Estado | Trigger | Visual |
|---|---|---|
| `idle` | Page mount sin fetch | Skeleton 5 stat cards + 5 tabs + lista placeholder |
| `loading` | Fetch patrones en curso | Spinner overlay + dots animados "Cargando seguimiento..." |
| `success` | Data fetched, hay patrones | KPIs hero llenos + tab activo + cards + activity footer real |
| `error` | Fetch falló | Banner rojo "No pudimos cargar el seguimiento. [Intentá de nuevo]" |
| `empty` | Fetch OK, 0 patrones tab activo | Empty illustration mariposa + copy contextual ("Todos al día ✓") |
| `agent-thinking` | Cron mid-render (raro) | Banner sutil "Sistema ejecutando cron {nombre}..." |
| `agent-waiting-approval` | Adrián requiere confirm operador | Modal ConfirmTemplateModal con preview WA + [Cancelar] [Enviar] |
| `agent-failed` | Template WA send falló (Meta API error / opt-out detectado mid-flow) | Toast error + card status_failed + chip "Envío falló · reintentar?" |

## § 9 — Telemetría events

```yaml
events:
  - { name: "fidelizacion_viewed", trigger: "page mount" }
  - { name: "fidelizacion_tab_changed", props: ["from_tab", "to_tab"] }
  - { name: "fidelizacion_card_clicked", props: ["patient_id", "pattern", "urgency"] }
  - { name: "fidelizacion_reminder_sent", props: ["patient_id", "pattern", "template_id"] }
  - { name: "fidelizacion_reminder_cancelled", props: ["patient_id", "pattern"] }
  - { name: "fidelizacion_patient_paused", props: ["patient_id", "duration_days"] }
  - { name: "fidelizacion_mark_external", props: ["patient_id", "pattern"] }
  - { name: "fidelizacion_mark_no_continue", props: ["patient_id", "pattern"] }
  - { name: "fidelizacion_manual_call_logged", props: ["patient_id", "pattern", "outcome"] }
  - { name: "fidelizacion_cron_executed", props: ["cron_name", "patterns_detected_count", "duration_ms"] }
  - { name: "fidelizacion_reminder_responded", props: ["re_engagement_event_id", "hours_to_respond"] }
  - { name: "fidelizacion_re_engaged_appointment_created", props: ["re_engagement_event_id", "appointment_id", "days_from_reminder"] }
```

## § 10 — Ideas Slice 2+ documentadas (no perder)

1. Dashboard NPS completo (4 KPIs + bar chart distribución + lista filtrable)
2. Detractor flow agentic real (Adrián responde según score)
3. Owner notification escalation cuando detractor 0-3
4. Google Reviews integration (Places API) — solo promotores 9-10
5. NPS sentiment analysis via Lucas tool
6. NPS configurable per offer + per vertical
7. Birthday cron mensual (template "Feliz cumple")
8. Re-engagement frío segundo touchpoint (template alternativo 7d)
9. Lucas patrón insights agentic (clusters re-engagement)
10. Re-engagement segments custom (VIP, premium >$5000)
11. Multi-channel (SMS Twilio · email SendGrid)
12. A/B testing templates
13. Auto-pause feriados clínica
14. Re-engagement por especialidad doctor (doctor X se va → pacientes a Y)
15. Cross-link `/marketing` Re-engagement ROI metric
16. Predicción abandono Lucas ML
17. Doctor view dedicada con sus follow-ups

## § 11 — Anti-patterns prohibidos (forbid)

- ❌ Enviar template MARKETING sin opt-in paciente (Meta sanciona + regulación local LATAM)
- ❌ Atribución falsa "Adrián decidió enviar recordatorio autónomo" cuando cron disparó
- ❌ Spammear paciente sin throttle (1 reminder per pattern per 7d MINIMUM)
- ❌ Skip `opt_out=true` flag en queries cron
- ❌ PHI visible si role no autorizado (dual filter tenant+clinic + RBAC hipaa-lite)
- ❌ Hardcoded strings en componentes `fidelizacion/*.tsx` (todo via `FIDELIZACION_COPY`)
- ❌ Cron sin idempotency key (re-trigger duplicates re_engagement_events)
- ❌ Marcar paciente "no continuar" sin razón + audit row
- ❌ NPS detractor visible sin masking comentario
- ❌ Tag NPS en /inbox sin role check (PHI cruza rutas — respetar hipaa-lite)
- ❌ Follow-up captured campo libre sin parsing duration robusto
- ❌ Maintenance config offer sin migration retroactiva (offers existentes default NONE)
- ❌ Cron timing server-local TZ vs UTC (TZ confusion)
- ❌ Re-engagement count contaminando /pipeline ventas analytics (cohort separado)
- ❌ Templates Meta sin submit pre-aprobación (Meta rechaza envío templates no aprobados)
- ❌ Skip throttle template WA Business cost (limit per tenant per día)
- ❌ Cron bypass `@cron_envelope` engine (post lift core 2026-05-20 idempotency + OTel + audit + sentry centralizado)
- ❌ Repos PHI sin `CompoundScopeRepositoryBase` (post lift core — scope_field="clinic_id")
- ❌ `send_medical_summary` por WhatsApp tier free (ComplianceService canal seguro guard)

## § 12 — Cross-story consumer/producer summary (post HANDOFF doc)

**Esta story PRODUCE** (consumida por otras Ola 1+ Slice 1):
- NPS schema (`NPSScoreCollected` event + tabla `vitalia_nps_responses` o columna `vitalia_patients.nps_score`) → `/inbox` tag detractor
- Re-engagement patterns endpoint (`GET /api/v1/vitalia/fidelization/re-engagement/patterns`) → `/marketing` Lucas card source (Slice 2)
- `ReEngagementTriggered` domain event → `/inbox` proactive_outbound conversation auto-creada

**Esta story CONSUME** (producido por otras stories):
- `vitalia_appointments` columns `follow_up_due_at` + `follow_up_reason` + `completed_at` + `balance_status` (producer: Ola 3 `/agenda` para captura UI · pero columns ya creadas vía engine promotion proposal — fidelización lee runtime)
- `vitalia_offers` columns `requires_multi_session` + `sessions_expected` + `gap_alert_days` + `maintenance_schedule` (producer: engine promotion proposal `2026-05-17-offer-studio-multi-session-maintenance` — state migrated pre-Ola 1)
- `vitalia_patients` columns `marketing_opt_in` + `opt_out` + `opt_out_reason` + `opt_out_at` (producer: infra-cross-cutting Ola 0 — DONE 2026-05-18)
- `core/luana-core-platform/workers/cron_envelope` (producer: promotion proposal `2026-05-20-core-platform-extensions-slice-1` — pre-flight gate)
- `core/luana-core-platform/repositories/CompoundScopeRepositoryBase` (idem pre-flight gate)
- `core/luana-core-campaigns/workers/{scheduler_tick, execution_task, segment_refresh_tick, audit_retention_task}` (engine ya shipped — Vitalia consume direct)
- Adrián sales_agent (engine `core/luana-core-sales-agent/`) + brand extension overlay (consumida via `proactive_outbound_service`)
- Lucas re-engagement recommendations (tools ya shipped en story side `vitalia-copilot-tools-impl` — Lucas no ejecuta cron, solo consume re_engagement_events para recomendar)

**NO produce:**
- Lucas `compute_*` tools — viven en side story `vitalia-copilot-tools-impl` o Ola 2 `/marketing`. Esta story solo CONSUME outputs cuando Lucas evalúe re_engagement_events agregados.
- Cron execution para Adrián mismo — Adrián NO ejecuta cron (cron-only Lucas territory). Adrián envía cuando el cron lo invoca con `proactive_outbound` origin.

## § 13 — Referencias

- Parent spec: `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/01-spec.md` §§ Ruta /fidelización (líneas 2670-3324)
- Mockup: `vitalia/docs/product/stories/vitalia-slice-1-fidelizacion/02-design-ui-mockup.html`
- HANDOFF cross-story: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`
- Rule HIPAA-lite: `vitalia/.claude/rules/hipaa-lite.md`
- Rules Luana: `.claude/rules/{tenant-isolation,backend-ddd,frontend-fsd,architectural-fitness,anti-duplication,spanish-text,tdd-mandatory,story-closure-gate,brand-docs-schema}.md`
