<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-4

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-4 (Wave 5 — AttributionMatrixWidget + ReferralsWidget + 5 stage section components)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** fc8f6aa..9341106
**Files Reviewed:** 14 (7 components + 7 test files)
**Domains touched:** SC-MK-03 attribution matrix (Reserva stage) + Referrals (Expansión) + 5 stage sections + StageDispatcher refactor
**Skills consulted:** frontend-expert, tessl__react-patterns (semantic table for a11y), tessl__shadcn-ui (no primitive recreation), `.claude/rules/master-data.md` (currency on referrals)
**Live-verified:** Manual escalated to Chris staging gate (documented in result.md)
**Verdict:** **PASS**

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors, no new warnings |
| Vitest marketing | PASS | 42 new tests (Attribution 8 + Referrals 7 + 5×5..6 stages) |
| Arch fitness (42 tests) | PASS | 42/42, no allowlist growth |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 (stage components correctly co-located in marketing/components/) |
| 2 | Server/Client | PASS | All stages `"use client"` (need React Query hooks); StageDispatcher consume-only |
| 3 | React Patterns | PASS | loading/error/empty states per widget; `forwardRef + displayName` consistent |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | semantic `<table>` with `<th scope="col">` + per-cell `aria-label` heatmap; `role="tabpanel" aria-labelledby` on every stage; HIPAA leaderboard column header explicit |
| 6 | Forms (RHF + Zod) | N/A | no forms |
| 7 | Multitenancy | PASS | inherits dual filter from hooks (useAttributionMatrix, useReferrals, useStageDetail) |
| 8 | Master Data / Spanish | PASS | `ReferralsWidget` uses `useTenantLocale().currency` fallback (`data.currency ?? locale.currency`); formatMoney via `Intl.NumberFormat("es-419", { style: "currency", currency, ... })` — currency comes from data, not hardcoded |
| 9 | Security / Deps | PASS | `String(rawValue)` on AttributionRow cell render; no DOM injection |
| 10 | Tests / TDD | PASS | 42 tests RED→GREEN per result.md; HIPAA test asserts DOM has no `patient.name` |
| 11 | Domain Alignment / Agentic UI | PASS | AttributionMatrix consumes Lucas data via service-shipped hook; topInsightText from BE |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | no cross-feature/cross-brand mirror |
| 14 | Decisions honored cite (R6) | N/A | |

## Strengths

- **AttributionMatrix is semantic `<table>`** with `<thead>` + `<tbody>` + `<th scope="col">` + per-cell `aria-label="{originLabel}, {colLabel}: {displayValue}"` — screen reader friendly. Heatmap via `convRateColorClass` mapped to `vt-text-success/warning/danger` tokens (no hardcoded HEX). Threshold: ≥40% success, ≥20% warning, <20% danger — documented in code.
- **`getRate` numerator/denominator handles div-by-zero** correctly (`if (!den) return 0;`).
- **ReferralsWidget HIPAA-aware:**
  - Header column label `MARKETING_COPY.referrals.referrerLabel = "Referidor (ID anónimo)"` — never `patient.name`
  - Renders `referrerPatientIdHash` in `font-mono` span with `aria-label="Referidor N"` (positional ARIA, not patient identifying)
  - Test `test_hipaa_no_patient_names` asserts DOM contains no `patient.name` string
  - `referrerPatientIdHash` JSDoc on type says "NEVER patient.name per phi_fields.py"
- **`formatMoney` correct master-data:** `data.currency ?? locale.currency` fallback (NO hardcoded USD). `try/catch` around `Intl.NumberFormat` (graceful degradation for unknown currency codes).
- **Stage panels with `role="tabpanel" id="stage-panel-{stage}" aria-labelledby="stage-tab-{stage}"`** properly link to tabs via the IDs declared in `MarketingStageTabs.tsx`.
- **Conditional widgets** per UI spec: AttributionMatrix only in Reservation stage, Referrals only in Expansion stage. NPS placeholder explicitly marked `data-testid="nps-placeholder"` for future ticket — slot pattern.
- **AttractionStage slot pattern:** retains `data-testid="channel-breakdown-placeholder"` even after T-mk-fe-5 swaps in `<ChannelBreakdownRow>` — preserves test backward compat.
- **forwardRef + displayName** on all 7 components.
- **`useTenantLocale()` used correctly** in ReferralsWidget (currency fallback).

## Findings

(no FAILs)

(no WARNs)

## Contract / UI-SPEC Compliance

- [x] AttributionMatrix 4 origins (sales_agent, walk_in, phone_manual, proactive_outbound) + total row + 5 KPI columns (leads, qualified, convListo, reservations, adoption) — matches `01-spec-extract.md § 3` and `02-design-ui.md § 4 attribution_matrix`
- [x] ReferralsWidget 3 KPI hero cards + top-5 leaderboard per `02-design-ui.md § 4 referrals_widget`
- [x] HIPAA-lite header label rendered verbatim from copy.ts
- [x] StageDispatcher correctly dispatches all 5 stage components per `03-arch-fe.md § 1`

## Allowlist Movement / Native-First / Live Verification

- [x] No allowlist growth
- [x] No docker/make e2e
- [x] No `git add .`
- [x] Manual verification documented in result.md (steps 1-9)

## Verdict Math

- 0 FAILs · 0 WARNs · → **PASS**

**Result:** APPROVED.
