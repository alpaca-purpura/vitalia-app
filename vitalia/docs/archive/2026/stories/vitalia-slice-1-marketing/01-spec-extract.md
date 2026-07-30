---
story_id: vitalia-slice-1-marketing
extracted_from: vitalia/docs/archive/2026/stories/vitalia-ux-discovery/01-spec.md § §§ Ruta /marketing
extraction_date: 2026-05-20
extracted_by: /architect (refresh post REPLAN 2026-05-20 ratificado Chris)
parent_archived: 2026-05-20
brand: vitalia
compliance_level: hipaa_lite
ola: 2
parallel_with: vitalia-slice-1-pipeline
---

# Spec extract — vitalia-slice-1-marketing

> Ruta `/marketing` = Bowtie salud 5 stages (Atracción+Captura · Calificación+Considerando · Reserva c/depósito · Adopción · Expansión+Evangelización). Vista panorámica para Owner clínica. Drill-downs operativos viven en `/inbox`, `/pipeline`, `/agenda`, `/fidelizacion`.
>
> ★ Chris 2026-05-20 ratificado: NO reusar `nicolify/frontend/src/features/growth-studio/` (4-tier loading + 30+ componentes + 13 hooks sobre-ingeniero). Build NUEVO simple consumiendo Lucas tools ya shipped + engine `@cron_envelope` migrado + `CompoundScopeRepositoryBase` (clinic_id dual filter).

## 1. JTBD (refrasado scope marketing)

| JTBD | Persona | Stage de bowtie |
|---|---|---|
| #5 P1 — "ver el panorama del bowtie completo y entender qué etapa está debilitada" | Owner clínica | Cross-stage |
| #1 P2 — "ver KPIs del mes con atribución a agentes (Adrián cerró X · Lucas calificó Y · Lucas detectó top oportunidad escalar Meta)" | Owner clínica + Admin | Cross-stage |

Diferenciador estructural: **AttributionMatrixWidget** (origen lead → resultado downstream Calif→Reserva→Adopción) — ningún producto LATAM (cero · botclinico · rendu · dentalink · doctocliq) muestra atribución cross-origin. Vitalia hace surface aquí.

## 2. 5 stages Bowtie adaptados a salud

| # | Stage canónico | Equivalente salud | KPIs hero Slice 1 | Lucas recommendations stage-specific | Cross-link operativo |
|---|---|---|---|---|---|
| 1 | `attraction` | Atracción + Captura | Leads · Spend · CPL · Best channel | "Escalar Meta campaña X · +12 leads/mes ROI 4.2x" · "IG sin posts 7d agendar 3" · "Walk-ins +5 auditar fuente" | `/inbox` (lead llega WA) |
| 2 | `qualification` | Calificación + Considerando | Leads en calificación · Tiempo per stage · Drop-off Calificando→Considerando | "3 leads sin screening pendiente Adrián propuesta" · "Tiempo Calificando ↑ 40% revisar friction" | `/pipeline` |
| 3 | `reservation` | Reserva con depósito 30% | Reservas confirmadas · Conv Listo→Reserva · Revenue · Mejor origin | "Conv rate ↓ 5pp revisar friction Mercado Pago" · "Walk-ins conv 89% vs sales 41% oportunidad screening pre-cita" | `/pipeline` Stage 4-5 + `/agenda` |
| 4 | `adoption` | Tratamiento en curso (adopción) | Tratamientos activos · Adherencia % · Sessions/paciente · Próximos abandono | "12 tratamientos próximos abandono · cross-link /fidelizacion" · "Adherencia ortodoncia 92% > depilación 78% revisar workflow" | `/fidelizacion` Tab "Tratamientos" |
| 5 | `expansion` | Expansión + Evangelización | Re-engaged · NPS · Referidos · LTV per paciente | "8 promotores NPS 9-10 · campaña referidos opcional" · "Dental tiene LTV 2.3x estética" | `/fidelizacion` Tabs NPS+Referidos |

## 3. Componentes visibles (5 surfaces)

| Componente | Path destino | Tipo |
|---|---|---|
| `MarketingBowtieSVG` (5 stages pixel-invariante centro) | `vitalia/frontend/src/features/marketing/components/` | Build NUEVO simple — promueve scaffold `vitalia/frontend/src/components/shared/marketing/MarketingBowtieSVG.tsx` |
| `LucasStageRecommendationsCard` (3 cards top per stage · protagonista) | idem | Build NUEVO consume scaffold `vitalia/frontend/src/components/shared/lucas-recommendations/` |
| `AttributionMatrixWidget` (Stage Reserva · 4 origins) | idem | Build NUEVO consume scaffold `vitalia/frontend/src/components/shared/attribution/` |
| `ReferralsWidget` (Stage Expansión · leaderboard + Adrián template) | idem | Build NUEVO (no scaffold previo — usa `LucasReferralsService` ya shipped) |
| Read-only Channels viewport (Meta + Google APIs · Slice 1 NO edit budgets) | idem | Build NUEVO — consume `vitalia_channel_metrics` engine sync simplificado |

## 4. UTM tracking lead → origin attribution (Hidden FK)

Cada lead Meta/Google tracked con UTM params `utm_source` + `utm_campaign` + `utm_medium`. Persistido en `vitalia_appointments.utm_source` + `utm_campaign` + `utm_medium` (column additions engine — proposal cementado pre-Ola 2). Si lead llega WA sin UTM → fallback `origin=unknown`. Slice 2 = inference Lucas ML basado en contenido conv.

**PHI scope:** UTM payload NUNCA contiene PHI (no patient.name, no patient.dni). Solo IDs hash + channel slug + timestamp. `vitalia_channel_sync_state.oauth_token_encrypted` via pgcrypto symmetric.

## 5. Persona JTBD (operadora Owner-tier P1 + P2)

María González (Owner Clínica Dental Sonríe, Lima Perú). Necesita:
- A diario: vista panorámica bowtie + qué Lucas recomienda hacer hoy (3 cards top).
- Semanal: ROI publicidad (Meta + Google) + conv funnel (Lead→Reserva) + atribución downstream (origins → Adopción).
- Mensual: NPS distribution + referidos generados (boca-a-boca tracked) + LTV per vertical (dental vs estética vs psicología).

Resistance: Owner no quiere mirar 30 cards de growth-studio Nicolify — quiere **"qué hacer"**, no datos crudos. Lucas-first protagonista.

## 6. Gherkin scenarios (4 obligatorios — heredados parent spec)

### SC-MK-01 — Happy: Owner aprueba recomendación Lucas escalar Meta budget

```gherkin
Scenario: Lucas detecta oportunidad escalar Meta · Owner aprueba · sync ejecuta
  Given Owner "María González" logged in en /marketing tab "attraction"
  And cron `lucas_daily_analysis_sweep` ejecutó hoy 06:00 UTC
  And generó recommendation `meta_campaign_implantes_scale` con projected_impact="+12 leads/mes · ROI 4.2x"
  When María ve card Lucas top stage attraction con titular "Meta 'Implantes' ROI 4.2x · escalar $400 → +12 leads/mes"
  And click [Detalle]
  Then modal `LucasRecommendationDetailModal` abre con:
    - Data análisis: campaign Implantes 30d → 24 conv · cpL $14 · ROI 4.2x
    - Proyección: budget current $1000 → $1400 estimación +12 leads/mes ± 3 (confidence 78%)
    - Audit trail: cron Lucas + criterio "high_roi_campaign_below_budget_cap"
  When María click [Aprobar]
  Then modal `LucasApprovalModal` muestra warning "Acción reversible · puedes deshacer 5min después"
  And María confirma (Idempotency-Key header)
  Then backend marca `vitalia_lucas_recommendations.status = approved`, `approved_by_user_id`, `approved_at`, `undo_until = approved_at + 5min`
  And `vitalia_audit_log` row "lucas_recommendation_approved" sync write pre-response
  And toast "Recomendación aprobada · ejecutándose..."
  And action receipt chip 5min countdown "Deshacer aprobación"
  And card desaparece del stage tab post-toast (moved to history)
```

### SC-MK-02 — Negative: Meta API timeout · sync degraded · UI muestra last_known

```gherkin
Scenario: Meta API timeout · sync degraded · Vitalia muestra warning sin block UI
  Given /marketing /attraction tab activo
  And Meta API endpoint experimenta timeout en cron `channel_metrics_sync_meta` c/4h
  When backend cron falla para `provider=meta_ads` tenant X clinic Y
  And update `vitalia_channel_sync_state.status='error'`, `last_error='Meta API timeout 504'`
  When María refreshea page /marketing
  Then ChannelRow Meta Ads muestra ConnectionBadge warning + tooltip "Sincronización falló hace 4h"
  And Metrics last_known visible (no spinner indefinido) con timestamp "última sync 8h atrás"
  And Botón inline `[Reintentar sync ahora]` → POST `/marketing/channels/meta_ads/sync`
  But otros canales (google_ads) muestran metrics OK
  And bowtie SVG sticky top mantiene visible con last_known data
```

### SC-MK-03 — Edge: Stage tab change · Lucas recommendations re-render correctly

```gherkin
Scenario: Stage tab change · Lucas recomendaciones re-render stage-specific
  Given operadora "Carla" en /marketing tab "attraction"
  And Lucas tiene 3 recomendaciones pendientes stage attraction
  When Carla click tab "reservation"
  Then URL state actualiza ?tab=reservation (replace, intra-state)
  And Lucas card refresca con 3 recomendaciones stage reservation distintas
  And bowtie SVG sticky top destaca stage reservation con highlight cian
  And KPIs hero actualizan a stage reservation (Reservas confirmadas · Conv rate · Revenue · Mejor origin)
  And AttributionMatrixWidget renderiza visible (4 origins)
  When Carla refresca browser
  Then URL ?tab=reservation persistido + estado preservado correcto
```

### SC-MK-04 — Adversarial: Lucas recommendation aprobación + permission check

```gherkin
Scenario: Adversarial recommendation + role check
  Given DB tiene `vitalia_lucas_recommendations` row open
  When operador role=recepción (no admin_clinic ni marketing) intenta click [Aprobar]
  Then 403 Forbidden + `vitalia_audit_log` row "unauthorized_lucas_approval_attempted" + payload_redacted con role=recepción
  And UI muestra "Solo Owner/admin puede aprobar recomendaciones de presupuesto"
  When Owner María (role=admin_clinic) click [Aprobar]
  Then backend valida action_payload range válido (max budget per campaign per tenant config)
  And si action_payload exceed range → reject + audit "lucas_action_payload_out_of_range"
  When cron Lucas siguiente día regenera recommendations
  Then evita re-sugerir same out-of-range action (feedback loop — `vitalia_lucas_recommendations.rationale_json.previous_rejection_reason`)
```

## 7. Acceptance criteria (scoped a marketing route)

- A1: Ruta `/marketing` carga bajo `<MarketingLayout>` con bowtie SVG sticky top + 5 stage tabs + Lucas card protagonista + KPIs hero + Channels viewport + Activity footer.
- A2: Tablas `vitalia_channel_sync_state`, `vitalia_channel_metrics`, `vitalia_lucas_recommendations`, `vitalia_referrals` creadas via migration idempotente `IF NOT EXISTS`.
- A3: 4 cron jobs (`channel_metrics_sync_meta` c/4h, `channel_metrics_sync_google` c/4h, `lucas_daily_analysis_sweep` 06:00 UTC, `referrals_value_sync` daily 10:00 UTC) registrados vía `@cron_envelope` decorator engine `luana_core_platform.workers.cron_envelope`.
- A4: 10 endpoints `/api/v1/vitalia/marketing/...` con `response_model=` + `Bearer + X-Tenant-ID + X-Clinic-ID` headers + Idempotency-Key en POST aprobar/rechazar/undo.
- A5: FE consume hooks React Query (`useBowtieSummary`, `useStageDetail`, `useChannelDetail`, `useLucasRecommendations`, `useApproveRecommendation`, `useAttributionMatrix`, `useReferrals`, `useSyncChannel`).
- A6: Bowtie SVG pixel-invariante respeta `02-design-ui-mockup.html` (Chris ratificó SSoT visual heredado). Visual regression Playwright baseline congelada en commit T-mk-fe-7.
- A7: HIPAA-lite: TODA query dual filter `tenant_id` + `clinic_id` (via `CompoundScopeRepositoryBase` con `scope_field="clinic_id"`). NO PHI en UTM payloads. `oauth_token_encrypted` via pgcrypto. `audit_log` sync write pre-response en aprobar/rechazar/undo.
- A8: Spanish neutro LatAm — todos los strings UI en `vitalia/frontend/src/features/marketing/copy.ts::MARKETING_COPY`. Arch fitness `test_no_voseo_in_copy.test.ts` GREEN.
- A9: Performance budget: LCP < 2.5s · INP < 200ms · CLS < 0.1 · Bowtie SVG bundle < 30KB gzipped. Validado via Lighthouse CI en CD.
- A10: Cross-story handoff: `LucasRecommendation` + `AttributionEntry` types en `vitalia/frontend/src/features/marketing-shared/types.ts` para consumo `/pipeline` (cross-link cards).

## 8. Lucas tools + services ya shipped (READ-ONLY context — NO reimplementar)

Consumir directo, sin tocar:

| Tool / Service | Path | Returns |
|---|---|---|
| Tool `compute_stage_recommendation` | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_stage_recommendation.py` | `StageRecommendationDTO` per stage |
| Tool `compute_attribution_matrix` | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_attribution_matrix.py` | `MatrixDTO` (4 origins breakdown) |
| Tool `compute_referrals_leaderboard` | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_referrals_leaderboard.py` | `LeaderboardDTO` (top referrers + LTV) |
| Service `LucasStageRecommendationService` | `application/services/lucas_stage_recommendation_service.py` | LLM-backed (Lucas growth setter persona) |
| Service `LucasAttributionService` | `application/services/lucas_attribution_service.py` | Pure DB (engine analytics adapter) |
| Service `LucasReferralsService` | `application/services/lucas_referrals_service.py` | Pure DB (engine analytics adapter) |
| Service `LucasOrchestratorService` | `application/services/lucas_orchestrator_service.py` | Coordinator daily sweep |

## 9. Skills consulted (one-liner decisions)

| Skill | Decision |
|---|---|
| `metrics-expert` | Bowtie 5 stages mapeo a engine funnel_stage existing enum. Channels via `core/luana-core-analytics-engine/` stage_services SSoT. Brand opt-in via `vitalia/backend/src/modules/vitalia/analytics/extensions.py` registra `enabled_metrics` (medical subset) + `channel_groups` (LATAM medical). NO mirror stage_service per-brand. |
| `copilot-expert` | NA — Lucas es sales_agent role (growth setter), no copilot. Marketing surface consume Lucas via existing services. |
| `sales-agent-expert` | Lucas tools ya shipped (R23 production). Marketing surface consumer-only — NO new agentic tools en este story. Lucas approval/reject/undo flows van por backend service layer, no agentic runtime. |
| `backend-expert` | DDD Inside-Out. Dual filter `tenant_id + clinic_id` via `CompoundScopeRepositoryBase` (engine migrated 0.4.0). Migrations idempotentes raw SQL `IF NOT EXISTS`. `audit_log` sync write pre-response. Pgcrypto encrypt `oauth_token_encrypted`. |
| `frontend-expert` | FSD-Lite `features/marketing/`. Server Components default. nuqs URL state SSoT. NO cross-feature import sin port. Tokens-only CSS vars per `vitalia/docs/architecture/design-system.md`. Build simple — no growth-studio. |
| `brand-expert` | NA — no afecta brand surface. |
| `offer-expert` | NA — no afecta offer surface (referidos consumen `vitalia_appointments` no offers). |
| `tessl__graceful-degradation` | External calls (Meta Ads API, Google Ads API) wrap timeout + fallback. Cron retry exponential backoff. Soft-fail per provider isolated. |

## 10. Ideas Slice 2+ documentadas (no perder)

Heredadas verbatim del parent spec § §§§ Ideas Slice 2+:

1. Budget adjust automation — Lucas ejecuta budget changes Meta/Google direct con confirmación + audit + rollback 5min
2. CaptureBreakdownChart granular (defer)
3. CampaignDrillDown granular (defer)
4. ConversionBridge per stage (mantener solo Stage Reserva Slice 1)
5. OfferLadder + OfferHealthCard widgets (defer)
6. BenchmarkBadge LATAM salud (defer Slice 3+ — requires data)
7. Sidebar tabs per canal (audience/creatives/breakdown) (defer Slice 3+)
8. IG Business API métricas real
9. Multi-channel attribution model ML (Slice 3+)
10. Lucas auto-generate ad creatives (Slice 3+)
11. Predictive Lucas conv per lead (Slice 3+)
12. Cross-brand benchmarks (defer — requires data)
13. Attribution UTM auto-tag templates WA outbound
14. Referrals gamification tiers (Bronce/Plata/Oro)
15. Cross-link `/inversion-publicitaria` P2 Owner vista dedicada (Slice 2)
16. A/B test recommendations Lucas (Slice 3+)
17. Lucas voice TTS audio (Slice 3+ Premium)

## 11. Engine gaps (escalate /pm-luana — NOT in scope Slice 1)

| Gap | Surface | Resolution route |
|---|---|---|
| `vitalia_appointments.utm_source/utm_campaign/utm_medium` columns | engine `core/luana-core-scheduling/` (post Slice 1 scheduling lift) OR brand-local `vitalia_appointments` table | **CHECK FIRST:** verify column already present in engine schema. If absent in engine, add via vitalia brand-local migration on `vitalia_appointments` table (brand-extension only, no engine touch). |

Architect note: /dev-team MUST verify via grep `appointments.*utm` BEFORE picking T-mk-be-1. Brand-local migration path acceptable Slice 1; engine lift candidate Slice 2 documented `delta-arch-notes.md`.
