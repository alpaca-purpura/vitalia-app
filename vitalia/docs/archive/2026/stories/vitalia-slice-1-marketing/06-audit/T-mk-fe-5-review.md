<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-5

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-5 (Wave 5 — Channel components: ConnectionBadge + ChannelBreakdownRow + ChannelDetailSidebar + ChannelConnectionWizard)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** b8edd54..04f64ab
**Files Reviewed:** 8 (4 components + 4 test files) + AttractionStage edit
**Domains touched:** SC-MK-02 channel sync degraded UI + OAuth wizard
**Skills consulted:** frontend-expert, tessl__react-patterns (security: OAuth full-page nav vs popup, target=_blank rel=noopener), `tessl__graceful-degradation` (retry on sync error)
**Live-verified:** Manual escalated to Chris staging gate (documented in result.md)
**Verdict:** **PASS**

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors, no new warnings |
| Vitest marketing | PASS | 31 new tests (Badge 7 + BreakdownRow 8 + Sidebar 9 + Wizard 7) |
| Arch fitness (42 tests) | PASS | 42/42, no allowlist growth |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | All `"use client"` (state + event handlers + mutations) |
| 3 | React Patterns | PASS | loading/error/empty/disconnected states explicit; stable keys; `forwardRef + displayName` consistent |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | `role="dialog" aria-modal="true" aria-label` on sidebar + wizard; ConnectionBadge has `data-state` + textual label (no color-only signal); ChannelBreakdownRow `role="button" tabIndex={0} onKeyDown(Enter/Space)`; retry button has `aria-label="Reintentar {providerName}"` |
| 6 | Forms (RHF + Zod) | N/A | wizard uses native state (no form schema needed for provider picker) |
| 7 | Multitenancy | PASS | inherits dual filter from useChannelDetail + useSyncChannel hooks |
| 8 | Master Data / Spanish | PASS for strings; **WARN** for `toLocaleDateString` direct call in 2 places — see Finding W1 |
| 9 | Security / Deps | PASS | OAuth full-page nav (NOT popup); external `<a>` has `target="_blank" rel="noopener noreferrer"`; test asserts `window.open` never called |
| 10 | Tests / TDD | PASS | 31 tests RED→GREEN per result.md |
| 11 | Domain Alignment / Agentic UI | PASS | ChannelDetailSidebar embeds `LucasStageRecommendationsCard` correctly (passes `stage="attraction"`) |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | no cross-feature/cross-brand mirror |
| 14 | Decisions honored cite (R6) | N/A | |

## Strengths

- **Security invariants (CRITICAL — explicit in result.md):**
  - OAuth uses `window.location.href = authUrl` (full page navigation), NEVER `window.open()` popup
  - External link to Ads Manager: `target="_blank" rel="noopener noreferrer"` (no `referrerpolicy` leak)
  - Test `test_oauth_uses_full_page_navigation` asserts `window.open` spy never called
  - Test `test_external_link_has_target_blank` asserts the rel attribute
- **SC-MK-02 (degraded sync UI) implemented correctly:**
  - ConnectionBadge maps `error|disconnected` → `vt-text-danger` token, `running` → `vt-text-warning`, `idle` → `vt-text-neutral`
  - ChannelBreakdownRow shows `last_success_at` timestamp even in error state (last-known display, no spinner indefinido per `tessl__graceful-degradation`)
  - Retry button appears only on error/disconnected; `stopPropagation` prevents row click from opening sidebar
  - `disabled={isSyncing}` and "Sincronizando..." label during pending mutation
- **ConnectionBadge multi-channel a11y:** uses textual label (`MARKETING_COPY.channels.{idle,running,error,disconnected}Status`) in addition to color token — color is NOT the only signal (WCAG 1.4.1 compliance).
- **Keyboard navigation on ChannelBreakdownRow:** `role="button" tabIndex={0} onKeyDown` handles both Enter and Space with `preventDefault` (prevents space-scroll).
- **AttractionStage edit additive:** preserves `data-testid="channel-breakdown-placeholder"` container — T-mk-fe-4 test backward-compatible.
- **Mock isolation:** `vi.mock("../components/ChannelBreakdownRow")` in AttractionStage.test.tsx prevents cross-ticket regression.
- **Test injection prop `_testAuthorizationUrl`:** prefixed with `_` (TS convention for internal/test), avoids needing to mock fetch for OAuth init endpoint. Used only in tests, never in production handler.
- **Idempotency-Key correct** via inherited `useSyncChannel` hook.

## Findings

(no FAILs)

### WARN W1 — `toLocaleDateString("es-419", ...)` direct calls instead of tenant-locale wrapper

**Category:** 8 (Master Data)
**Files:**
- `vitalia/frontend/src/features/marketing/components/ChannelBreakdownRow.tsx:87`
- `vitalia/frontend/src/features/marketing/components/ChannelDetailSidebar.tsx:120`

**Issue:** Both files format `lastSuccessAt` ISO 8601 via direct `new Date(iso).toLocaleDateString("es-419", { day, month, hour, minute })`. Per `.claude/rules/master-data.md`:
> FE: `useTenantLocale()` → `{ currency, timezone }`. Display: `formatTenantDate*()`, `formatMoneyDual()`.
> **Prohibido:** `toLocaleDateString()`

The hardcoded `"es-419"` locale tag bypasses the tenant's `useTenantLocale().timezone` — a clinic in Mexico vs Argentina vs Peru sees identical formatting. Browser will pick LOCAL timezone instead of tenant timezone (clinic-relative time may differ from owner-relative time).

**Suggested fix:** Replace with a `formatTenantDate(iso, locale.timezone)` helper from `vitalia/frontend/src/lib/format/`. If the helper doesn't exist for this brand yet, use `new Intl.DateTimeFormat(undefined, { ..., timeZone: locale.timezone })` to respect both browser locale + tenant timezone. Pattern that ReferralsWidget already uses (`useTenantLocale()` + Intl) is the canonical reference.

**Auditor self-fix policy:** This is **NOT** whitelist category (replacing `toLocaleDateString` with helper involves shaping logic + adding hook call). Spawn `builder-frontend` autonomous loop OR document deferral.

**Skill ref:** `.claude/rules/master-data.md`.

## Contract / UI-SPEC Compliance

- [x] 4 ConnectionBadge states per `03-arch-fe.md § 7` (idle/running/error/disconnected)
- [x] ChannelBreakdownRow per `02-design-ui.md` (badge + last success ts + retry on error + chevron)
- [x] ChannelDetailSidebar 3 sections (sync state KPIs + top-3 campañas + Lucas recs) per `03-arch-fe.md § 1`
- [x] ChannelConnectionWizard 3 steps per `02-design-ui.md § 4 connection_wizard`
- [x] SC-MK-02 last-known data + retry implemented

## Allowlist Movement / Native-First / Live Verification

- [x] No allowlist growth
- [x] No docker/make e2e
- [x] No `git add .`
- [x] Manual verification documented in result.md (11 steps)

## Verdict Math

- 0 FAILs · 1 WARN (master-data toLocaleDateString)
- 1 WARN ≤ 1 ⇒ **PASS**

**Result:** APPROVED — recommend WARN follow-up in subsequent ticket or self-fix iter (replacing 2 sites with a helper is mechanical but logic-shaping).
