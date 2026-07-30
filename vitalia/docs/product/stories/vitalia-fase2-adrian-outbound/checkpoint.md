---
story_id: vitalia-fase2-adrian-outbound
type: ui-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: campaigns
capability: adrian.outbound
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 4-5
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-adrian-embudo            # segmentar leads por stage
    - vitalia-fase2-adrian-inbox             # respuestas outbound caen en inbox
blocks_hard: []
blocks_soft:
  - vitalia-fase2-lucas-resultados           # outbound ROI parte del bowtie funnel
reuse_map_summary: "REUSE fidelización module shipped · REUSE 5 templates Meta-approved (vitalia/backend/src/modules/vitalia/campaigns/templates/) · REUSE core/luana-core-campaigns engine · NEW wizard 3-pasos (Segmento · Template · Schedule) · NEW audience builder vs embudo stages"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes wizard + audience builder"

# Schema v2 migration (cement 2026-05-27)
release: F4   # release ID · ver releases/
cap_target: adrian.outbound   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S5 vitalia-fase2-adrian-outbound — checkpoint

## Goal

Sub-tab Outbound de Adrián: campañas dirigidas a leads (audience = leads pre-paciente, NOT pacientes que es scope Camila). Wizard 3 pasos:
1. **Segmento** — Audience builder (por stage embudo · por canal origen · por tags · por last_activity)
2. **Template** — 5 templates Meta-approved (HSM templates oficiales WhatsApp Business API) + preview
3. **Schedule** — Inmediato · Programado · Recurrente (per evento) + rate-limit + opt-out compliance

Reemplaza placeholder Fase 1 + reusa fidelización shipped pero re-target audience (Camila se queda con pacientes existentes; Adrián con leads).

## Anti-objetivos

- NO crear templates nuevos en F2-S5 (5 Meta-approved shipped son suficiente MVP — story dedicada para creator/submission)
- NO implementar A/B testing (out-of-scope MVP)
- NO duplicar audience de Camila (pacientes existentes = Camila exclusive)
- NO implementar audience static lists (sólo dinámicas vs embudo state)
- NO tocar `core/luana-core-campaigns` engine (read-only · brand extension via EP-7)

## Scope verbatim

### § 1 — Page

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/outbound/page.tsx`:

```tsx
import { AdrianOutboundView } from '@/features/adrian/components/outbound/AdrianOutboundView'

// Server initial state: lista campañas activas + métricas tiny
export default async function Page({ params }: PageProps) {
  // ...
}
```

### § 2 — `AdrianOutboundView` layout

Composición:
1. `<OutboundHeader>` — Métricas tiny (campañas activas · enviados últimos 30d · click rate avg · opt-out rate) + "+ Nueva campaña" button
2. `<CampaignsTable>` — Lista campañas con cols: Nombre · Audience · Template · Schedule · Stats · Acciones
3. Click row → detail workspace N3-dyn `[campaign-id]`

### § 3 — `NewCampaignWizard` (★ corazón valor)

`vitalia/frontend/src/features/adrian/components/outbound/NewCampaignWizard.tsx`:

3 steps Shadcn `Tabs` + state machine local:

#### Step 1 — Segmento (audience builder)

```tsx
// Audience builder visual:
// - Por stage embudo (multi-select: interesado · calificando · considerando · listo)
// - Por canal origen (multi-select: WhatsApp · IG · Email · Web · Referido)
// - Por tags (multi-select)
// - Por last_activity (range: 7d · 14d · 30d · custom)
// - Excluir (multi-select: opt-out previos · bot activo · ya en campaña activa)
//
// Live preview: "Estimado X leads matchean este segmento"
// Click "Vista previa" → tabla con 5 leads sample (PHI masked)
```

#### Step 2 — Template

```tsx
// Lista 5 templates Meta-approved:
// 1. recordatorio_cita (HSM utility) — para leads stage 'listo' que aún no reservaron
// 2. promo_servicio (HSM marketing) — para 'calificando'/'considerando'
// 3. educacion_general (HSM marketing) — para 'interesado' (top-of-funnel)
// 4. encuesta_satisfaccion (HSM utility) — para post-conv cerrada
// 5. recordatorio_pago (HSM utility) — para deudores stage 'reservado' pero saldo pendiente
//
// Cada template card muestra:
// - Categoría (utility · marketing) — Meta requirement
// - Preview con variables sample
// - Last edit (read-only — solo Meta admin puede editar)
// - Approval status (✅ Approved · ⏳ Pending · ❌ Rejected)
//
// Click template → editor variables (Zod schema per template)
```

#### Step 3 — Schedule

```tsx
// 3 modes:
// - Inmediato — enviar en próximos minutos
// - Programado — date+time picker + timezone tenant
// - Recurrente — trigger por evento (lead.stage_changed · lead.last_activity > 7d · etc.)
//
// Rate-limit:
// - Max send/min (default 30 — Meta limit per tier)
// - Max send/day per lead (default 1 — anti-spam)
// - Cooldown post send (default 24h)
//
// Compliance:
// - Auto-add opt-out footer "Para no recibir más: respondé STOP"
// - Validar template categoría vs audience consent state
// - Bloquear send si lead opt-out global activo
```

Submit final → POST `/api/campaigns` con full config → audit log row + campaign queued in worker.

### § 4 — `CampaignsTable`

Columns: Nombre · Audience size · Template · Schedule · Sent · Delivered · Clicked · Opt-outs · Acciones (Pausar · Editar · Duplicar · Cerrar).

Active/Paused/Done badges color-coded.

### § 5 — Campaign Detail N3-dyn

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/outbound/campana/[campaign-id]/page.tsx`:

Tabs:
- **Resumen** — Métricas overview · timeline events
- **Audiencia** — Lista leads en campaña (paginated) con per-lead status (delivered · read · clicked · opted-out)
- **Performance** — Charts: delivery rate · click rate · opt-out rate · conversion (lead → reservado)
- **Mensajes** — Preview templates enviados con variables actuales
- **Configuración** — Audience config · template · schedule (edit-only si campaign paused)

### § 6 — Métricas + funnel attribution

Cada send genera event `outbound_send`. Cada click `outbound_click`. Cada lead que avanza stage post-send dentro 7d = attribution `outbound`.

Attribution data alimenta F2-S18 lucas-resultados (bowtie funnel) — read-only consumer.

### § 7 — Opt-out compliance

`vitalia/backend/src/modules/vitalia/campaigns/application/opt_out_service.py`:

- Cuando paciente responde "STOP" / "NO" / "BAJA" / equivalentes → backend processa via sales-agent intent detection → flag `lead.opt_out = true`
- Backend NUNCA envía a leads opt-out (test cross-feature integration `test_no_send_to_opt_out.py`)
- Audit log + Sentry alert si try-send a opt-out

### § 8 — Mobile responsive

- Wizard tabs → vertical stacked
- CampaignsTable → cards stack
- Campaign detail tabs → accordion

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Wizard 3-pasos funciona end-to-end |
| AC-2 | Audience builder live preview muestra estimated leads + sample 5 (masked) |
| AC-3 | Template selector muestra 5 templates Meta-approved con preview |
| AC-4 | Schedule modes (Inmediato · Programado · Recurrente) funcionan |
| AC-5 | Rate-limit + cooldown enforced backend |
| AC-6 | Opt-out compliance: NO send a leads con opt_out=true |
| AC-7 | Audit log row por campaign create + per send |
| AC-8 | CampaignsTable muestra métricas live |
| AC-9 | Campaign detail tabs funcionan + edit limitado si active |
| AC-10 | Visual goldens wizard 3-steps + campaigns table + detail |
| AC-11 | a11y axe pass |
| AC-12 | Mobile wizard accordion funciona |
| AC-13 | Cross-tenant query bloqueada |
| AC-14 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: crear campaña + send inmediato

**Given:**
- 50 leads stage `considerando` last 14d
- Template `promo_servicio` approved
- Tenant config rate-limit 30/min

**When:**
1. Click "+ Nueva campaña"
2. Step 1: select audience stage=considerando + last_activity=14d → preview "50 leads matchean"
3. Step 2: select template `promo_servicio` + variables
4. Step 3: schedule inmediato + accept rate-limit defaults
5. Submit

**Then:**
- POST `/api/campaigns` retorna campaign_id
- Backend queue 50 sends respetando rate-limit (50 → 30/min = 1m40s spread)
- Worker procesa + envía WhatsApp HSM
- Audit log: `campaign_created` + per send `outbound_send`
- CampaignsTable refresh muestra nueva campaña con stats incrementales

**playwright_required:** true  
**Graders:** E2E + BE worker test + audit log assert

### Scenario 2 — negative: opt-out lead intent send

**Given:** Lead `lead_X` opted-out previo (responded "STOP")

**When:** Audience builder incluiría `lead_X` por criterios

**Then:**
- Backend filter excluye `lead_X` ANTES queue send
- Preview audience size = N-1 (excluye opt-outs automáticamente)
- Si attempt force-send via API directo → Sentry alert + audit log `attempted_send_to_opt_out`

**playwright_required:** false (BE test suficiente)  
**Graders:** `vitalia/backend/tests/modules/vitalia/campaigns/test_opt_out_enforcement.py`

### Scenario 3 — edge: template approval status cambia mid-campaign

**Given:** Campaign active usando template `promo_servicio` que Meta cambia a "Pending review"

**When:** Worker intenta send → Meta API rechaza por template no-approved

**Then:**
- Worker captura error → pausa campaign automáticamente
- UI muestra alert "Template promo_servicio pendiente review Meta. Campaña pausada."
- Audit log: `campaign_auto_paused_template_unapproved`
- User puede editar campaign para usar otro template + reanudar

**playwright_required:** true  
**Graders:** E2E + BE error handler test

### Scenario 4 — adversarial: cross-tenant audience leak

**Given:** Usuario tenant A intenta audience por tenant B leads

**When:** POST campaign con `tenant_id: tenant_b` en body

**Then:**
- Middleware tenant filter override body → fuerza tenant_id de session
- Audience builder solo retorna leads del tenant de session
- NO leak

**playwright_required:** false (BE test)  
**Graders:** `test_cross_tenant_audience_block.py`

### Scenario 5 — keyboard-a11y wizard

**Given:** Foco en Step 1 first input

**When:** Tab + arrow + enter traversa wizard

**Then:**
- Foco visible en cada campo
- aria-current en step actual
- Next button enabled solo si step valid (visible feedback)
- Esc en cualquier step → confirma cancel

**playwright_required:** true  
**Graders:** E2E + axe

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/outbound/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/outbound/campana/[campaign-id]/page.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/AdrianOutboundView.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/OutboundHeader.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/CampaignsTable.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/NewCampaignWizard.tsx` | NEW (★) |
| `vitalia/frontend/src/features/adrian/components/outbound/wizard/AudienceBuilder.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/wizard/TemplateSelector.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/wizard/SchedulePicker.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/campaign-detail/CampaignWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/outbound/campaign-detail/tabs/{Resumen,Audiencia,Performance,Mensajes,Configuracion}Tab.tsx` | NEW (5 files) |
| `vitalia/frontend/src/features/adrian/api/outbound.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/campaign.types.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/campaign-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/campaigns/api/campaigns_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns/application/audience_builder_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns/application/send_worker.py` | NEW (rate-limit + cooldown) |
| `vitalia/backend/src/modules/vitalia/campaigns/application/opt_out_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns/persistence/migrations/XXXX_campaigns_outbound.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/adrian-outbound-wizard.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/adrian-outbound-opt-out.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/outbound/{view}-{light\|dark}.png` (×6) | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns/test_opt_out_enforcement.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns/test_rate_limit_worker.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns/test_cross_tenant_audience_block.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns/test_template_approval_check.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `fidelización module` | Templates + send worker | REUSE + re-target audience leads (no patients) |
| Vitalia shipped — 5 templates Meta-approved | HSM WhatsApp Business API templates | REUSE 100% (template registry shipped) |
| `core/luana-core-campaigns` (engine) | Campaign DDD model + CampaignTemplateDef registry | CONSUME via Extension SDK EP-7 |
| `core/luana-core-channels` | format_for_channel | REUSE |
| `core/luana-core-compliance` | ComplianceService outbound validate | REUSE |
| Shadcn primitives | `Tabs` · `Dialog` · `Select` · `DatePicker` · `Checkbox` · `Table` | npx install |
| Vitalia archived — `vitalia-slice-1-fidelizacion` | Outbound UI pattern | REFACTOR (audience era pacientes) |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` — shell con sub-tab nav
- `vitalia-fase1-routing-shell` — App Router

### Soft
- `vitalia-fase2-adrian-embudo` — segmentar por stage del embudo
- `vitalia-fase2-adrian-inbox` — respuestas outbound caen en inbox

### Esta historia desbloquea
- `vitalia-fase2-lucas-resultados` — outbound attribution alimenta bowtie funnel
- `vitalia-fase2-camila-voz` — F2-S5 outbound responses generan NPS triggers

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Meta template approval status drift | Alta | Medio | Backend polling Meta API status cada 6h + auto-pause campaigns |
| Rate-limit insuficiente → Meta bloquea cuenta | Media | Crítico | Cooldown + back-off exponencial + alert si error_rate > 5% |
| Opt-out compliance gap | Baja | Crítico | Multiple defense layers (audience filter + worker check + audit) |
| Recurrente schedule loop | Media | Medio | Cap max-trigger-per-lead 1/30d + monitoring alert |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 12 (wizard 3 steps + table + detail × 2 themes)
3. Backend tests opt-out + rate-limit + cross-tenant + template-approval pass
4. Story commits pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `adrian.outbound` registrada

## Próximo paso post-done

- F2-S18 lucas-resultados consume attribution outbound
- Story futura: bulk template-submission para escalar HSM library

## Nota compliance (cross-link reframe lisa-compliance 2026-06-07)

El **gate opt-out/consent en el path de envío** (§ 7 + AC-6 + `opt_out_service.py`) es un **requisito HARD de compliance** (consentimiento antes de marketing — anti-pattern de marca "recordatorios sin opt-in"). El explore 2026-06-07 confirmó que hoy **solo re-engagement** lo chequea; el outbound proactivo de Adrián DEBE gatear opt-out/consent ANTES de encolar el send (audience filter + worker check + audit, las 3 capas). Esta story es el hogar correcto de ese guardrail (NO se spawnea story aparte). La vista **Lisa→Confianza y cumplimiento** (lisa-compliance, dirección A) **lee** el conteo de bloqueos/opt-outs que este servicio produce. Ref: `vitalia-fase2-lisa-compliance/00-pm-recommendation.md`.

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Template spec:** `vitalia/docs/specs/templates/01-spec-shell-template.md`
- **Navigation tree:** § adrian.outbound
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Slice-1 archived:** `vitalia/docs/archive/2026/stories/vitalia-slice-1-fidelizacion/`
