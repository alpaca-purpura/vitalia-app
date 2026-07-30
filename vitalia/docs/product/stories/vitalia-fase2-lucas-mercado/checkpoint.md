---
story_id: vitalia-fase2-lucas-mercado
type: ui-story
agent_owner: lucas
map_zone: agentes
map_box: lucas
module: market_intel
capability: lucas.mercado
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: medium
estimated_dev_days: 4-5
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lucas-resultados              # benchmark interno vs market
blocks_hard: []
blocks_soft: []
reuse_map_summary: "NEW (trends mining no shipped) · NEW tendencias rubro + hashtags + competencia + sugerencias Lucas · CONSUME engine sales-agent intent_detector + core/luana-core-* observability"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes 4 sub-secciones · /architect evaluar trends mining sources"

# Schema v2 migration (cement 2026-05-27)
release: F6   # release ID · ver releases/
cap_target: lucas.mercado   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S19 vitalia-fase2-lucas-mercado — checkpoint

## Goal

Sub-tab Mercado de Lucas: market intelligence cross-vertical. 4 sub-secciones:
- **Tendencias rubro** — Topics tracking per vertical (dental · estética · psicología) con engagement aggregate
- **Hashtags** — Top hashtags + trending + suggested per content type
- **Competencia** — Tracking competidores (5-10 max per tenant) cross-channels (no scraping legal-bound)
- **Sugerencias Lucas** — Lucas AI suggestions content/timing/targeting based on data anterior

## Anti-objetivos

- NO scraping ilegal competidores (solo APIs públicas + manual entry de tenant)
- NO duplicar Mateo generation (F2-S17 owns)
- NO implementar buy/sell market data integrations (story future)

## Scope verbatim

### § 1 — Page + 4 sub-secciones tabs

`<LucasMercadoView>` Shadcn Tabs.

### § 2 — `TendenciasRubro`

Tracking trending topics per vertical (data source: Meta Audience Insights + Google Trends + IG TikTok hashtag APIs):
- Cards top 10 trending topics
- Trend chart 30d
- Engagement aggregate score
- CTA "Crear contenido sobre X" → linkea F2-S15 lanzar

### § 3 — `HashtagsExplorer`

Hashtags discovery:
- Top hashtags vertical
- Trending hashtags week
- Sugeridos per content type (post · reel · story)
- Saved hashtag bundles (reusable en F2-S17 recursos)

### § 4 — `CompetenciaTracking`

Lista competidores (max 10 tracked):
- Add competitor: nombre + handle channels (IG · FB · TikTok · web)
- Metrics público disponible: followers · post frequency · engagement avg · top posts
- Benchmark interno vs competitor visual

NO scraping privado · solo APIs públicas + manual data entry tenant.

### § 5 — `SugerenciasLucas`

Cards sugerencias AI Lucas (consume `core/luana-core-llm` engine):
- "Postear viernes 14h - mejor engagement window detectado"
- "Topic limpieza dental trending - aproveches"
- "Competitor X aumentó frequency posts - tu performance puede dropear sin response"

Cada card click → drawer detalle + CTA action (linkea F2-S15 lanzar o F2-S17 recursos).

### § 6 — Backend trends mining

`vitalia/backend/src/modules/vitalia/market_intel/`:
- Cron sync APIs públicas (Google Trends · Meta Audience Insights · IG Graph API)
- Lucas AI suggestions service consume engine LLM + tenant data anterior
- Cache 6h server-side

### § 7 — HIPAA-lite

Mercado data agregada · NUNCA PHI. Backend filter.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 4 sub-secciones |
| AC-2 | Tendencias cards trending + trend chart |
| AC-3 | Hashtags explorer + saved bundles |
| AC-4 | Competencia CRUD (max 10) + benchmark |
| AC-5 | Sugerencias Lucas AI consume engine LLM |
| AC-6 | Cross-links a F2-S15 lanzar y F2-S17 recursos funcionan |
| AC-7 | Cron sync sources resilient |
| AC-8 | Visual goldens × 8 |
| AC-9 | a11y axe pass |
| AC-10 | Cross-tenant + no PHI |
| AC-11 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: sugerencia → action

**Given:** Lucas sugiere "Postear viernes 14h"

**When:** Click card → "Crear post programado"

**Then:** Redirect F2-S15 quick-post con schedule pre-cargado viernes 14h

### Scenario 2 — edge: limit competidores

**Given:** Tenant ya tracked 10 competidores

**When:** Click "+ Nuevo competidor"

**Then:** UI alert "Máximo 10 competidores. Eliminá uno antes."

### Scenario 3 — adversarial: scraping competidor private data

**Given:** Tenant intenta add competidor URL privada con auth

**When:** Backend processa

**Then:** Backend reject "Solo APIs públicas soportadas" · audit log · NO scraping

### Scenario 4 — keyboard-a11y

Tabs + cards traversable.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/mercado/page.tsx` | MODIFY |
| `vitalia/frontend/src/features/lucas/components/mercado/LucasMercadoView.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/mercado/TendenciasRubro.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/mercado/HashtagsExplorer.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/mercado/CompetenciaTracking.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/mercado/SugerenciasLucas.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/api/mercado.ts` | NEW |
| `vitalia/frontend/src/features/lucas/types/mercado.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/market_intel/api/mercado_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/market_intel/application/trends_sync.py` | NEW (cron) |
| `vitalia/backend/src/modules/vitalia/market_intel/application/lucas_suggestions.py` | NEW (LLM consumer) |
| `vitalia/backend/src/modules/vitalia/market_intel/persistence/migrations/XXXX_market_intel.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lucas-mercado.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/mercado/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/backend/tests/modules/vitalia/market_intel/test_trends_sync_resilience.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/market_intel/test_lucas_suggestions_llm.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/market_intel/test_competidor_max_limit.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/market_intel/test_no_private_scraping.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| `core/luana-core-llm` | LLM router | CONSUME para Lucas suggestions (Sonnet OK · no agentic prod code · solo LLM call) |
| `core/luana-core-observability` | trace + cost | CONSUME |
| Google Trends API · Meta Audience Insights · IG Graph | External APIs | NEW clients |
| F2-S15 lanzar + F2-S17 recursos | Cross-link targets | CONSUME |
| Shadcn primitives | `Card` · `Tabs` · `Drawer` · `Badge` · `Table` | reuse |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lucas-resultados` — benchmark interno

### Esta historia desbloquea
- ninguna directa · MVP scaffold para market intel layer

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| External APIs rate limits | Media | Bajo | Cron back-off + cache 6h |
| Lucas suggestions hallucination | Media | Bajo | Validation rules + grader low-confidence flag |
| Competencia data accuracy variable | Alta | Bajo | Disclaimer "data público APIs" |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 8
3. Backend tests sync + LLM + limits + no-private-scraping pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lucas.mercado` registrada

## Próximo paso post-done

- Story future: integrations buy market data services

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lucas.mercado
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
