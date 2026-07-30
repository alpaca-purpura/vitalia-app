---
story_id: vitalia-fase2-lucas-lanzar
type: ui-story
agent_owner: lucas
map_zone: agentes
map_box: lucas
module: campaigns_growth
capability: lucas.lanzar
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lucas-recursos             # creatividades catalog
    - vitalia-fase2-lisa-marca                 # voice brand para copy
blocks_hard: []
blocks_soft:
  - vitalia-fase2-lucas-envuelo                # campañas lanzadas → en vuelo
  - vitalia-fase2-lucas-resultados             # campañas data → bowtie
reuse_map_summary: "NEW workspace P4 campaign (paid + orgánica) · model ciclo-temporal-v2 per navigation-tree · NEW wizard adaptivo paga/orgánica · NEW quick-post · NEW borradores + pendientes aprobación · CONSUME core/luana-core-campaigns engine"
spawned_at: 2026-05-22
next_action: "★ TIER reclassified 2026-05-27 (audit sweep): TIER 6 HIGH RISK scope ambiguity. Audience definition NO clara — 'prospects NOT patients' overlap directo con adrian-outbound (campaigns a leads en embudo). DEFER refinement hasta TIER 3 Adrian COMPLETO (post adrian-outbound shipped). Después revaluar con data real adrian-outbound usage: (A) si Lucas-Lanzar = new-customer ACQUISITION (anuncios Meta/Google fuera embudo) → keep, build. (B) si Lucas-Lanzar = re-engagement leads existentes → KILL, fusionar con adrian-outbound. Recommendation: Opción A — defer decision a post-TIER-3. SSoT orden: vitalia/docs/product/outcomes/vitalia-fase-2-tier-roadmap.md § TIER 6 + § Stories deprioritized."

# Schema v2 migration (cement 2026-05-27)
release: F6   # release ID · ver releases/
cap_target: lucas.lanzar   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S15 vitalia-fase2-lucas-lanzar — checkpoint

## Goal

Sub-tab Lanzar de Lucas: workspace creación campañas growth (paid Meta/Google · orgánica social). Sub-secciones:
- **Nueva campaña** — Wizard adaptivo (paga vs orgánica) → ciclo-temporal-v2 model
- **Quick-post** — Posting rápido social (sin campaña full)
- **Borradores** — Campañas en draft
- **Pendientes aprobación** — Posts/campañas pendientes aprobación admin

## Anti-objetivos

- NO duplicar engine `core/luana-core-campaigns`
- NO implementar AI copy-generator (story future · MVP usa voice brand templates)
- NO implementar Meta Pixel install automation (config-conexiones lo expone)
- NO tocar referrals (Camila ownership atomic)

## Scope verbatim

### § 1 — Page + 4 sub-secciones

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/lanzar/page.tsx`:

`<LucasLanzarView>` con Shadcn `Tabs` 4 sub-secciones.

### § 2 — `NuevaCampanaWizard` (wizard adaptivo)

`vitalia/frontend/src/features/lucas/components/lanzar/NuevaCampanaWizard.tsx`:

Step 0 (decision):
- ¿Paga (Meta/Google) o Orgánica (Social posts)?

Step 1 — Objetivo (per type):
- Paga: Awareness · Tráfico · Conversiones · Re-marketing
- Orgánica: Engagement · Reach · Educación

Step 2 — Audiencia (per type):
- Paga: Lookalike from existing patients · Interest targeting · Geolocation · Demographics
- Orgánica: Followers · Public

Step 3 — Creatividad:
- Select desde F2-S17 recursos · upload new
- Preview live

Step 4 — Copy (consume voice brand from F2-S7)

Step 5 — Schedule + budget (per type):
- Paga: budget total + CPM/CPC + start/end dates
- Orgánica: schedule posts (date + time)

Step 6 — Aprobación (si role staff requires admin approve) · Submit

### § 3 — `QuickPost`

`vitalia/frontend/src/features/lucas/components/lanzar/QuickPost.tsx`:

Form rápido (1 step):
- Channel (IG · FB · TikTok · etc.)
- Texto + imagen/video upload
- Schedule inmediato o programado
- Submit → backend posts via channels API

### § 4 — `BorradoresList`

Lista campañas en draft. Click → wizard resume.

### § 5 — `PendientesAprobacion`

Lista campañas + posts pendientes aprobación admin (role: only `admin_clinic` aprueba).

Acciones: Approve · Reject (con razón) · Edit.

### § 6 — Backend ciclo-temporal-v2 model

`vitalia/backend/src/modules/vitalia/campaigns_growth/domain/campaign.py`:

```python
class CampaignType(str, Enum):
    PAID_META = "paid_meta"
    PAID_GOOGLE = "paid_google"
    ORGANIC_IG = "organic_ig"
    ORGANIC_FB = "organic_fb"
    ORGANIC_TIKTOK = "organic_tiktok"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    LIVE = "live"
    PAUSED = "paused"
    DONE = "done"
    CANCELLED = "cancelled"
```

Ciclo-temporal-v2 = state machine + scheduling + lifecycle hooks.

### § 7 — HIPAA-lite voice

Campañas NUNCA mencionan PHI patients · solo aggregated data (e.g., "+ 500 sonrisas restauradas · NO names ni diagnosis").

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 4 sub-secciones |
| AC-2 | Wizard adaptivo step-by-step funciona paga + orgánica |
| AC-3 | Quick-post submits sin wizard |
| AC-4 | Borradores resume en wizard |
| AC-5 | Pendientes aprobación bloquea launch hasta admin approve |
| AC-6 | Estado state machine transitions correctos |
| AC-7 | Audit log per campaign create + per approval |
| AC-8 | Visual goldens × 8 (wizard steps + quick + borradores + pendientes × 2 themes) |
| AC-9 | a11y axe pass |
| AC-10 | Cross-tenant + RBAC enforce |
| AC-11 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: lanzar paid Meta awareness

**Given:** Tenant config Meta OAuth shipped. Role admin_clinic.

**When:** Wizard paga · awareness · lookalike audience · creatividad shipped · copy custom · budget $100 · 7 days

**Then:**
- POST `/api/campaigns_growth` crea campaign DRAFT
- Submit aprobación: si role admin → status SCHEDULED → Meta API call → LIVE
- Audit log full chain

### Scenario 2 — edge: borrador resume múltiples días después

**Given:** Borrador creado hace 5 días con audience definida

**When:** User abre borrador

**Then:**
- Wizard resume desde step 3 (donde quedó)
- Validation re-run en step 2 (audience puede haber cambiado)

### Scenario 3 — adversarial: approve sin role

**Given:** Role staff intenta approve via API direct

**When:** POST `/api/campaigns_growth/{id}/approve`

**Then:** 403 · audit `unauthorized_approval_attempt`

### Scenario 4 — keyboard-a11y wizard

Tab traverse steps · Enter advance · arrow within step.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/lanzar/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/lanzar/nueva/page.tsx` | NEW (wizard standalone) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/lanzar/borradores/[draft-id]/page.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/lanzar/LucasLanzarView.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/lanzar/NuevaCampanaWizard.tsx` | NEW (★) |
| `vitalia/frontend/src/features/lucas/components/lanzar/QuickPost.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/lanzar/BorradoresList.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/lanzar/PendientesAprobacion.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/api/lanzar.ts` | NEW |
| `vitalia/frontend/src/features/lucas/types/campaign.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/api/lanzar_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/domain/campaign.py` | NEW (state machine) |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/application/launch_dispatcher.py` | NEW (Meta/Google API) |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/persistence/migrations/XXXX_campaigns_growth.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lucas-lanzar-wizard.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/lanzar/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_state_machine.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_approval_rbac.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| `core/luana-core-campaigns` (engine) | CampaignTemplateDef via EP-7 | CONSUME |
| `core/luana-core-channels` | format_for_channel · channel adapters | REUSE |
| F2-S5 outbound wizard | 3-step pattern | INSPIRE pattern (wizard adaptivo extiende) |
| Vitalia archived — marketing module | Posting primer versión | REFACTOR migrar al lucas/lanzar |
| Shadcn primitives | `Tabs` · `Dialog` · `Wizard pattern` · `DatePicker` · `Select` | npx install |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lucas-recursos` — creatividades source
- `vitalia-fase2-lisa-marca` — voice brand
- `vitalia-fase2-config-conexiones` — Meta/Google OAuth

### Esta historia desbloquea
- F2-S16 lucas-envuelo — campañas LIVE
- F2-S18 lucas-resultados — data alimenta bowtie

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Meta/Google API rejection campañas | Media | Medio | Pre-flight validation + retry queue |
| OAuth tokens expiry | Media | Medio | F2-S21 conexiones manage refresh |
| Approval workflow rompe lanzamiento urgente | Baja | Bajo | Admin override + audit |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 8
3. Backend tests state-machine + rbac + cross-tenant pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lucas.lanzar` registrada

## Próximo paso post-done

- F2-S16 envuelo monitorea campañas LIVE
- F2-S18 resultados consume campaign data

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lucas.lanzar (model: ciclo-temporal-v2)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Engine campaigns:** `core/luana-core-campaigns`
