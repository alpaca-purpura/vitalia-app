---
story_id: vitalia-fase2-camila-reputacion
type: ui-story
agent_owner: camila
map_zone: agentes
map_box: camila
module: reputation
capability: camila.reputacion
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: medium
estimated_dev_days: 2-3
status_phase2: scaffold-mvp                     # planned scaffold per navigation-tree
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-camila-voz                  # signals reseñas alimentan panorama
blocks_hard: []
blocks_soft: []
reuse_map_summary: "SCAFFOLD MVP planned per navigation-tree · panorama estratégico cross-canal · consumer-side de signals reseñas · NEW dashboard reputation scoring + sources matrix · NO response auto (story future)"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes dashboard scaffold + roadmap iteration future"

# Schema v2 migration (cement 2026-05-27)
release: F7   # release ID · ver releases/
cap_target: camila.reputacion   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S14 vitalia-fase2-camila-reputacion — checkpoint

## Goal

Sub-tab Reputación de Camila: **status scaffold-MVP** (planned per navigation-tree). Panorama estratégico cross-canal: reseñas Google · Instagram · TikTok · Web · mentions. Scoreboard general + cards por source + alerts críticos.

MVP = visualización solamente. Sin response auto (delegate F2-S11 voz signals → response manual humano).

## Notas a considerar — NPS vive en fidelización (diagnóstico 2026-06-18)

> **Contexto, NO mandato.** Inyectado por /pm-vitalia (HB-82). Reputación = reseñas externas (Google/IG/TikTok) — NO toca las 5 mutations de re-engagement (esas → `vitalia-fase2-camila-reactivar`). Único cruce posible: NPS.

- 💡 A considerar: el NPS ya tiene **BE vivo** en `fidelizacion` (`GET .../fidelizacion/nps/summary` + `POST .../nps/submit`, openapi-verificado). Si reputación necesita NPS, conviene consumir esos endpoints en vez de reconstruirlo (anti-duplication).
- Existe FE huérfano `features/fidelizacion/components/tabs/NPSResumenTab` + `use-nps-responses.ts` (este llama `nps/responses`, que NO existe en BE — hook imaginado). Cap `patients.nps-tracking` = DEPRECATED. 🧹 **Si esta story no lo reusa, dejarlo para que `camila-reactivar` lo borre** (es el dueño del scaffold) — no duplicar la limpieza.
- Las reseñas externas (objetivo real de esta story) NO tienen BE aún → siguen NEW per Deliverables.

## Anti-objetivos

- NO implementar response automation Google/IG (requiere OAuth + Meta/Google APIs · story future dedicada)
- NO duplicar signals processing (F2-S11 voz es source)
- NO implementar sentiment AI nuevo
- NO tocar engine

## Scope verbatim

### § 1 — Page + dashboard scaffold

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/reputacion/page.tsx`:

`<CamilaReputacionView>` con:
- Hero card: scoreboard general (avg rating cross-source + trend)
- Cards row per source: Google · IG · TikTok · Web · Otros (con count + rating + last sync)
- Alerts críticos: reviews 1-2 stars sin response > 24h
- Link cross-tab F2-S11 voz para acción

### § 2 — `SourceCard`

`vitalia/frontend/src/features/camila/components/reputacion/SourceCard.tsx`:

Per source:
- Icon + nombre source
- Avg rating last 30d
- Total reviews count
- Trend arrow (up/down vs previous 30d)
- "Ver reseñas" CTA → drawer paginated reviews

### § 3 — `ReviewsDrawer`

Drawer lista reviews:
- Star rating
- Texto reseña (sanitized · sin PHI)
- Source + autor (público nick)
- Date
- Action: "Crear signal para Voz" (envía a F2-S11 entrante view)

### § 4 — `AlertsCriticos`

Top alerts cards:
- Reviews 1-2 stars sin response > 24h (con count)
- Trend rating cayendo > 0.5 points last 7d
- New menciones negativas detectadas

Click alert → cross-link a Camila→Voz curaduría con signal pre-seleccionado.

### § 5 — Sync sources

Backend cron `reputation_sync_worker` sync sources hourly:
- Google My Business API
- Instagram Graph API (mentions)
- TikTok Business API (futuro · API limitada)
- Manual + Web (admin upload form)

Sync errors → alerts visible.

### § 6 — Scaffold disclaimer

Banner en page: "Panorama de reputación · Para responder reseñas, dirigirse a Voz del paciente curaduría. Response automation próximamente."

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza scoreboard + 4-5 source cards |
| AC-2 | Source card stats live |
| AC-3 | Reviews drawer paginated funcional |
| AC-4 | Alerts críticos visible si aplica |
| AC-5 | "Crear signal" envía review a F2-S11 entrante |
| AC-6 | Cron sync sources funcional + error alerts visible |
| AC-7 | Scaffold banner disclaimer presente |
| AC-8 | Visual goldens × 4 (dashboard + drawer × 2 themes) |
| AC-9 | a11y axe pass |
| AC-10 | Cross-tenant query bloqueada |
| AC-11 | Sanitize_payload reviews sin PHI |
| AC-12 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: alert critical review

**Given:** Google review 1-star posted hace 26h sin response

**When:** Page carga

**Then:**
- Alert visible "Review 1-star sin response > 24h"
- Click alert → redirect F2-S11 voz curaduría con signal pre-filtered

### Scenario 2 — edge: sync error Google API

**Given:** Google API retorna 503

**When:** Cron sync corre

**Then:**
- Backend captura error
- Source card Google muestra badge "Sync error · last success 6h ago"
- Sentry alert
- NO crash · UI degrada gracefully

### Scenario 3 — adversarial: PHI en review text

**Given:** Review contiene "El doctor X me diagnosticó cáncer terminal"

**When:** Backend processa

**Then:**
- sanitize_payload redacta diagnóstico
- Review stored: "El doctor X me [REDACTED]"
- Audit log

### Scenario 4 — keyboard-a11y

Tab → cards · Enter → drawer · Esc → back.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/reputacion/page.tsx` | MODIFY |
| `vitalia/frontend/src/features/camila/components/reputacion/CamilaReputacionView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reputacion/SourceCard.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reputacion/ReviewsDrawer.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reputacion/AlertsCriticos.tsx` | NEW |
| `vitalia/frontend/src/features/camila/api/reputacion.ts` | NEW |
| `vitalia/frontend/src/features/camila/types/review.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/reputation/api/reputacion_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/reputation/application/sync_workers.py` | NEW (Google · IG · Manual) |
| `vitalia/backend/src/modules/vitalia/reputation/persistence/migrations/XXXX_reviews.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/camila-reputacion-dashboard.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/reputacion/{view}-{light\|dark}.png` (×4) | NEW |
| `vitalia/backend/tests/modules/vitalia/reputation/test_sync_workers.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/reputation/test_sanitize_review.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/reputation/test_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| F2-S11 camila-voz signals service | Signals shared service | CONSUME |
| `core/luana-core-observability` sanitize_payload | PHI redaction | REUSE |
| Google My Business API (npm `googleapis`) | Reviews API | NEW client |
| Instagram Graph API | Mentions | NEW client |
| Shadcn primitives | `Card` · `Drawer` · `Alert` · `Badge` | reuse |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-camila-voz` — signals service consumer

### Esta historia desbloquea
- Story future: response automation Google/IG (dedicated)

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| External API rate limits | Media | Bajo | Cron exponential back-off + cache |
| Source OAuth flows complejos | Alta | Bajo | F2-S21 config-conexiones gestiona OAuth · esta story consume tokens existing |
| Scaffold MVP not enough valor user | Media | Bajo | Documented planned future iterations |

## Definición de "Done"

1. AC verificados (scaffold-MVP suficiente)
2. Visual goldens × 4
3. Backend tests sync + sanitize + cross-tenant pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `camila.reputacion` registrada con status `scaffold-mvp`

## Próximo paso post-done

- Story future: response automation (dedicated · post-MVP)
- F2-S21 config-conexiones expone OAuth Google/IG

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § camila.reputacion (status: scaffold-fase2-mvp)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
