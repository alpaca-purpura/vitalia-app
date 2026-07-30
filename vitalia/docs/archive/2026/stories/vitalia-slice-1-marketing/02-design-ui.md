---
story_id: vitalia-slice-1-marketing
parent_mockup: 02-design-ui-mockup.html (heredado parent · Chris ratificó 2026-05-17)
design_date: 2026-05-20
designer: /architect (refresh)
brand: vitalia
ssot_design_system: vitalia/docs/architecture/design-system.md
---

# Design UI — `/marketing` (refresh post REPLAN 2026-05-20)

> SSoT visual = `02-design-ui-mockup.html` heredado del parent `vitalia-ux-discovery`. Este doc agrega: estados, microcopy referencias, breakpoints, a11y, tokens map.
>
> NO REUSAR growth-studio Nicolify (Chris 2026-05-20). Build simple con `vitalia-cian` + `vitalia-purpura` + `vitalia-amarillo` + `vitalia-azul-marino` + `vitalia-verde-lima` per design-system.md § 1.

## 1. Layout (refresh sintetizado del mockup)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TopBar 56px · Vitalia | Clínica X ▾                                          │
├──────┬───────────────────────────────────────────────────────────┬───────────┤
│ NAV  │ MAIN /marketing · Bowtie salud · 1-31 May 2026 ▼          │ Copilot   │
│ 240  │                                                            │ rail 80   │
│ ■Mk  │ ┌─ Bowtie SVG sticky top (5 stages pixel-invariante) ──┐  │ idle      │
│ ...  │ │ Atracción→ Calif→ Reserva→ Adopción→ Expansión        │  │           │
│      │ │  ▮182    ▮87   ▮36   ▮62        ▮28                   │  │           │
│      │ │  CPL$24  conv48% conv41% adh87%  NPS72                 │  │           │
│      │ │ Conversión funnel: 182→28 = 15.4% · ROI 3.2x · LTV 890│  │           │
│      │ └───────────────────────────────────────────────────────┘  │           │
│      │                                                             │           │
│      │ ┌─ Tabs 5 stages ──────────────────────────────────────┐   │           │
│      │ │ [▮Atracción 182▮][Calif 87][Reserva 36]              │   │           │
│      │ │ [Adopción 62][Expansión 28]                          │   │           │
│      │ ├──────────────────────────────────────────────────────┤   │           │
│      │ │ TAB ACTIVO: Atracción + Captura                      │   │           │
│      │ │                                                       │   │           │
│      │ │ ┌─ 💡 Lucas en Atracción ★ PROTAGONISTA (3 cards) ─┐  │   │           │
│      │ │ │ "Meta 'Implantes' ROI 4.2x · escalar"            │  │   │           │
│      │ │ │   [Aprobar] [Detalle] [Rechazar]                 │  │   │           │
│      │ │ │ "IG orgánico sin posts 7d · agendar 3"           │  │   │           │
│      │ │ │ "Walk-ins +5 vs mes ant · auditar fuente"        │  │   │           │
│      │ │ │ [Ver todas (8 más) →]                            │  │   │           │
│      │ │ └──────────────────────────────────────────────────┘  │   │           │
│      │ │                                                       │   │           │
│      │ │ KPIs hero stage (4 stat cards)                       │   │           │
│      │ │ [Leads 182 +18][Spend $3.2k][CPL $24 -$3][Best Meta]│   │           │
│      │ │                                                       │   │           │
│      │ │ Channels viewport (read-only)                        │   │           │
│      │ │  ├ Meta Ads     $1200  68 leads  $18 cpL  drill →  │   │           │
│      │ │  ├ Google Ads   $800   42 leads  $19 cpL  drill →  │   │           │
│      │ │  ├ IG orgánico  $0     28 leads  organic  drill →  │   │           │
│      │ │  ├ Referidos    $0     21 leads  ★boca   drill →   │   │           │
│      │ │  └ Walk-ins     $0     23 leads  presencial drill→ │   │           │
│      │ │                                                       │   │           │
│      │ │ Activity footer: "Lucas analizó 182 leads · c/4h"   │   │           │
│      │ └──────────────────────────────────────────────────────┘   │           │
└──────┴────────────────────────────────────────────────────────────┴───────────┘
```

Tabs (5) cambian Tab activo + URL `?tab=...` replace + Lucas re-renderiza con stage-specific recommendations + AttributionMatrixWidget aparece solo en Tab `reservation` + ReferralsWidget solo en Tab `expansion`.

## 2. Estados visuales (8 totales)

| Estado | Trigger | Visual |
|---|---|---|
| `idle` | Page mount sin fetch | Skeleton bowtie placeholder + tabs vacíos + Lucas cards skeleton |
| `loading` | Fetch metrics + recommendations en curso | Spinner overlay bowtie + Lucas cards skeleton (no spinner indefinido) |
| `success` | Data fetched | Bowtie real con números · KPIs · Lucas recomendaciones · channels |
| `error` | Fetch falló | Banner `vitalia-danger` "No pudimos cargar el bowtie. [Reintentar]" |
| `empty` | Sin canales conectados ni histórico | Empty illustration mariposa + CTA "[+ Conectar primer canal]" |
| `agent-thinking` | Lucas analizando mid-fetch | Banner sutil "Lucas está analizando data..." sobre Lucas cards area |
| `agent-waiting-approval` | Lucas tiene recommendation pending Owner | LucasApprovalModal abierto con preview + estimación |
| `agent-failed` | Cron Lucas falló o Meta API exhausted | Toast `vitalia-danger` + Lucas card muestra "Análisis falló · reintentar" |

## 3. URL state contract (nuqs · 7 params)

Heredado parent `03-arch-fe.md § 3.5`:

```ts
export const marketingParsers = {
  tab: parseAsStringEnum(["attraction", "qualification", "reservation", "adoption", "expansion"]).withDefault("attraction"),
  period: parseAsStringEnum(["7d", "30d", "90d"]).withDefault("30d"),
  channel: parseAsString,                                // canal filter (provider+slug)
  selectedRecommendation: parseAsString,                 // recommendation_id modal abierto
  approvalModal: parseAsBoolean.withDefault(false),      // approval modal abierto
  channelDetailSidebar: parseAsString,                   // channel slug sidebar abierto
  connectionWizard: parseAsStringEnum(["meta_ads", "google_ads"]),  // wizard conectar canal
};
```

Patrón: `replace` para intra-state (tab, modals, sidebars, filters). `push` para cross-route (drill → `/inbox`, `/pipeline`, `/fidelizacion`). External links (Meta Ads Manager, Google Ads UI) abren en `target="_blank"` con `rel="noopener noreferrer"`.

## 4. Microcopy (Spanish neutro LatAm — `vitalia/frontend/src/features/marketing/copy.ts::MARKETING_COPY`)

Centralizado verbatim. Vive en file separado (arch fitness `test_no_hardcoded_strings.test.ts` enforce no inline strings). Per parent spec § §§§ Microcopy:

- `page.title` = "Marketing"
- `page.subtitle` = "Bowtie salud — performance funnel completo"
- `bowtie_labels.stage_1..5` = (heredado parent verbatim)
- `tabs.stage_1..5` = (heredado)
- `lucas_card.{section_title, cta_approve, cta_detail, cta_reject, cta_view_all, expires_in, confidence_label, impact_projected, audit_label, approve_success, approve_undo, reject_modal_title, reject_reasons}` = (heredado)
- `channel.{meta_ads, google_ads, ig_organic, referrals, walk_ins, organic_search, direct, other}`
- `channel_actions.{connect, edit_in_provider, sync_now, sync_status_ok, sync_status_syncing, sync_status_failed, sync_status_idle}`
- `attribution_matrix.{title, column_origin, column_leads, column_qualified, column_conv, column_reservations, column_adoption, column_value, origin_sales_agent, origin_walk_in, origin_phone_manual, origin_proactive, origin_total, insight_label}`
- `referrals_widget.{title, kpi_referrals_count, kpi_conv_rate, kpi_ltv_avg, leaderboard_title, leaderboard_column_patient, leaderboard_column_referrals, leaderboard_column_value, cta_send_template, referral_code_label, referral_link_label}`
- `connection_wizard.{title, step_1, step_2, step_3, cta_connect_oauth, cta_test_sync, cta_finish, success_message}`
- `empty_states.{no_data_period, no_recommendations, no_channels_connected}`
- `states.{loading, error, agent_thinking, agent_waiting_approval, agent_failed}`
- `activity_footer.template` = "Lucas analizó {leads_analyzed} leads · sistema sync c/4h · última {last_sync}"

No voseo, tuteo only. Magic comment `<!-- voseo-allowed: NO -->` head of file. Test enforces.

## 5. Responsive breakpoints

| Breakpoint | Ancho | Layout adapt |
|---|---|---|
| mobile | < 768px | Bowtie SVG escala horizontal scroll + tabs scrollable + Lucas cards stack vertical + Channels viewport tabular vertical |
| tablet | 768-1023 | Bowtie SVG escala fit + sidebar nav comprime a 60px iconos + Lucas cards 1 col |
| desktop | 1024-1439 | Full layout per mockup |
| wide | ≥ 1440 | Idem desktop, max-width container 1440px centrado |

Tested via Playwright + Chromatic visual regression baselines per breakpoint.

## 6. A11y notes (WCAG 2.1 AA)

| Surface | Requisito |
|---|---|
| Bowtie SVG | `<title>` per `<g>` stage + `aria-describedby` con KPI summary + role="img" |
| Tabs | `role="tablist"` + `role="tab"` aria-selected + Tab/ArrowKey nav |
| Lucas cards | Keyboard nav Tab order lógico + Enter/Space activate detail modal + focus visible ring |
| Modal approval | `role="dialog"` + `aria-modal="true"` + focus trap + ESC close |
| Channels rows | `<table>` semantic OR `role="grid"` con `aria-rowcount`/`aria-colcount` |
| Color contrast | ≥ 4.5:1 text · ≥ 3:1 UI components. Verificado via Axe per token combo (per design-system.md § 1.1 combinaciones aprobadas) |
| Live regions | Status toasts via `role="status"` + `aria-live="polite"` |

Validado via:
- `cd vitalia/frontend && npx playwright test e2e/specs/a11y/marketing.a11y.spec.ts`
- Axe runs en CI per component story Chromatic

## 7. Tokens map (consume design-system.md § 1 + § 5)

| Surface | Token (CSS var) |
|---|---|
| Bowtie SVG center axis line | `--vitalia-azul-marino` |
| Bowtie SVG acquisition gradient stop 1 | `--vitalia-cian-color` |
| Bowtie SVG retention gradient stop 1 | `--vitalia-verde-lima-color` |
| Lucas card avatar gradient | `vitalia-agent-gradient-lucas` (cian → verde-lima per agent-attribution) |
| Stage active tab | `--vitalia-azul-marino` bg + white text |
| Stage inactive tab | `--vitalia-bg` bg + `--vitalia-text-muted` |
| KPI stat card | `vt-bg-surface` + `vt-border` + numbers `vt-text` |
| Connection badge OK | `vt-text-success` |
| Connection badge warning | `vt-text-warning` |
| Connection badge error | `vt-text-danger` |
| AttributionMatrix conv cell heatmap | `color-mix(in srgb, var(--vitalia-cian-color) ${conv_pct}%, transparent)` |
| ReferralsWidget leaderboard top 1 | `--vitalia-amarillo` highlight |
| ReferralsWidget leaderboard top 2-5 | `vt-bg-muted` |

Arch fitness `test_no_hardcoded_colors.test.ts` GREEN: zero HEX literales fuera de `app/globals.css`.

## 8. Mockup pixel-invariante baseline

Visual regression Playwright + Chromatic congela snapshots de:
- `<MarketingBowtieSVG>` (5 stage variants, 4 breakpoints) = 20 baselines
- `<LucasStageRecommendationsCard>` (4 estados: open · approved+countdown · rejected · expired) = 4 baselines
- `<AttributionMatrixWidget>` (4 origins × 3 periods 7d/30d/90d, populated + empty) = 8 baselines
- `<ReferralsWidget>` (con/sin top promoters, populated + empty) = 4 baselines
- `<ChannelBreakdownRow>` (5 canales × 4 sync states ok/error/syncing/disconnected) = 20 baselines
- Full page `/marketing` per stage tab (5 stages × 3 breakpoints) = 15 baselines

Total ≈ 71 visual baselines. Diff threshold 0.1% pixel per Chromatic config. Mockup HTML es la referencia pre-baseline.

## 9. References

- `02-design-ui-mockup.html` (SSoT visual heredado)
- `vitalia/docs/architecture/design-system.md` (tokens cementados + tipografía + agent attribution)
- `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md` (fork físico Slice 1)
- `.claude/rules/spanish-text.md` (neutro LatAm sin voseo)
- `vitalia/.claude/rules/hipaa-lite.md` (PHI compliance — UTM payload scope)
