---
story_id: vitalia-fase2-lucas-envuelo
type: ui-story
agent_owner: lucas
map_zone: agentes
map_box: lucas
module: campaigns_growth
capability: lucas.envuelo
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
    - vitalia-fase2-lucas-lanzar              # campañas LIVE provienen de aquí
  soft: []
blocks_hard: []
blocks_soft:
  - vitalia-fase2-lucas-resultados            # cierre campañas alimenta post-mortem
reuse_map_summary: "NEW workspace campañas LIVE · NEW posts programados monitor · NEW performance live (Meta Insights API + Google Ads API + IG Insights) · NEW N3-dyn workspace detalle campaign + post"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes live monitor + N3-dyn workspace"

# Schema v2 migration (cement 2026-05-27)
release: F6   # release ID · ver releases/
cap_target: lucas.envuelo   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S16 vitalia-fase2-lucas-envuelo — checkpoint

## Goal

Sub-tab "En vuelo" de Lucas: monitor campañas LIVE + posts programados + performance live. Cards row top (active campaigns count · scheduled posts count · CPM avg · CTR avg) + tabla LIVE campaigns + posts schedule timeline. N3-dyn workspaces per campaign + per post.

## Anti-objetivos

- NO implementar pausar/cancelar logic (delegate a F2-S15 lanzar borradores · or detail workspace inline)
- NO duplicar tracking from Meta/Google (consume APIs)
- NO implementar realtime WebSocket updates (out-of-scope MVP · polling 60s)

## Scope verbatim

### § 1 — Page

`<LucasEnvueloView>`:
1. `<EnvueloMetrics>` — Active campaigns · scheduled posts · CPM · CTR · CPL
2. `<LiveCampaignsTable>` — Tabla campañas LIVE
3. `<PostsTimeline>` — Calendar timeline posts programados

### § 2 — `LiveCampaignsTable`

Columns: Nombre · Channel (Meta/Google/IG) · Status badge · Spend (live) · Impressions · Clicks · CTR · CPL · Conversions · Acciones (Pausar · Editar · Ver detalle).

Click row → N3-dyn `campana/[campaign-id]`.

### § 3 — `PostsTimeline`

Calendar view (week/month) con posts programados. Click → edit/preview/cancel.

### § 4 — N3-dyn campaign detail `campana/[campaign-id]`

Tabs:
- **Live KPIs** — CTR · CPM · CPL · Conversions live charts (refresh 60s)
- **Creatividades** — Lista creatividades + per-creative performance (winning ad detection)
- **Ajustes inline** — Budget bump · audience refine · pause/resume
- **Audit** — Per-action log

### § 5 — N3-dyn post detail `post/[post-id]`

Single post:
- Preview channel mockup
- Edit/cancel buttons
- Engagement stats (likes · comments · shares · saves)

### § 6 — Performance live sources

Backend `campaigns_growth/application/performance_sync.py`:
- Meta Insights API (polling 5min)
- Google Ads API (polling 5min)
- IG Insights API

Cache 60s server-side · FE polling 60s.

### § 7 — HIPAA-lite

Campañas live NUNCA mostrar PHI · solo aggregated stats.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza metrics + table + timeline |
| AC-2 | LiveCampaignsTable carga campaigns LIVE con stats live |
| AC-3 | Pausar action funcional (POST + audit) |
| AC-4 | N3-dyn campaign detail tabs funcionan |
| AC-5 | N3-dyn post detail funciona |
| AC-6 | Posts timeline calendar view interactivo |
| AC-7 | Performance polling cada 60s sin overload |
| AC-8 | Visual goldens × 8 |
| AC-9 | a11y axe pass |
| AC-10 | Cross-tenant + RBAC |
| AC-11 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: pausar campaign LIVE

**Given:** Campaign Meta LIVE consuming budget

**When:** Click "Pausar" en table action

**Then:** Backend Meta API call pause · status → PAUSED · spend congelado · audit log

### Scenario 2 — edge: budget bump inline

**Given:** Campaign detail · budget actual $100

**When:** Ajustes inline budget $200 → save

**Then:** Backend Meta API call update budget · audit · UI confirm

### Scenario 3 — adversarial: editar campaign tenant ajeno

GET/POST → dual filter bloquea · 404 · audit.

### Scenario 4 — keyboard-a11y

Tab table rows · Enter detail · tab actions.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/envuelo/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/envuelo/campana/[campaign-id]/page.tsx` | NEW |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/envuelo/post/[post-id]/page.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/envuelo/LucasEnvueloView.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/envuelo/EnvueloMetrics.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/envuelo/LiveCampaignsTable.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/envuelo/PostsTimeline.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/envuelo/campaign-detail/{LiveKpis,Creatividades,Ajustes,Audit}Tab.tsx` | NEW (4 files) |
| `vitalia/frontend/src/features/lucas/components/envuelo/post-detail/PostWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/api/envuelo.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/api/envuelo_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/campaigns_growth/application/performance_sync.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lucas-envuelo-monitor.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/envuelo/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_pause_resume.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_performance_sync_cache.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/campaigns_growth/test_envuelo_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| F2-S15 lucas-lanzar | Campaign state machine | CONSUME |
| `core/luana-core-channels` | Channel adapters Meta/Google/IG | REUSE |
| Shadcn primitives | `Table` · `Tabs` · `Card` · `Drawer` | reuse |
| Vitalia archived — analytics dashboard | Stats cards layout | REUSE |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell` + `vitalia-fase2-lucas-lanzar`

### Soft
- ninguna

### Esta historia desbloquea
- F2-S18 resultados post-mortem consume cierre campaigns

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| API rate limits Meta/Google | Media | Bajo | Cache + back-off |
| Polling 60s overload tenants grandes | Media | Bajo | Server-side cache + max 10 active campaigns visible |
| Pausar action falla Meta API | Baja | Medio | Retry queue + UI alert |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 8
3. Backend tests pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lucas.envuelo` registrada

## Próximo paso post-done

- F2-S18 lucas-resultados consume cierre campaigns para bowtie

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lucas.envuelo
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
