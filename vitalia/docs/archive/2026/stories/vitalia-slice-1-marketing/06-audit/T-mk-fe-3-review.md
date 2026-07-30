<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-3

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-3 (Wave 5 — LucasStageRecommendationsCard + 4 modals + UndoChip + RejectModal)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** 205e8d9..40cd57a
**Files Reviewed:** 9 (5 components + 4 test files)
**Domains touched:** Lucas approval flow UI (SC-MK-01 happy + SC-MK-04 RBAC)
**Skills consulted:** frontend-expert, tessl__react-patterns (dialog roles, focus management, ESC close), tessl__zod (LucasRejectModal reason enum runtime validation), sales-agent-expert (consumer-only invariant respected — no agentic logic in this surface)
**Live-verified:** Manual escalated to Chris staging gate (chrome-devtools-verify DEPRECATED on Linux — documented in result.md)
**Verdict:** **PASS** (1 WARN — nested interactive a11y in card row)

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors, no new warnings |
| Vitest marketing | PASS | 17 new tests (5 Card + 5 Approval + 4 Reject + 3 UndoChip) |
| Arch fitness (42 tests) | PASS | 42/42, no allowlist growth |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | All modals correctly `"use client"`; no Server-Component hooks misuse |
| 3 | React Patterns | PASS | Hooks rules respected (`useCallback` before conditional return in UndoChip — line 59 fix per result.md); useEffect deps minimal/correct |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | **WARN** | nested interactive content (`LucasUndoChip` button inside `RecommendationItem` button) — see Finding W1 |
| 6 | Forms (RHF + Zod) | PASS | LucasRejectModal uses Zod `safeParse` + native state (RHF not installed in vitalia frontend per result.md — documented decision); reason enum validation correct |
| 7 | Multitenancy | PASS | inherits dual filter from hooks |
| 8 | Master Data / Spanish | PASS | `LucasRecommendationDetailModal.tsx:56` uses `toLocaleString("es-PE", ...)` — see Finding W2 |
| 9 | Security / Deps | PASS | no XSS surface; modal renders `String(value)` for arbitrary rationaleJson |
| 10 | Tests / TDD | PASS | 17 tests RED→GREEN per result.md (`userEvent.setup()` for radio inputs — correct pattern) |
| 11 | Domain Alignment / Agentic UI | PASS | UndoChip reads `marketing-store.pendingUndoTimers` set by ApprovalModal post-mutation — clean architecture |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | no cross-feature/cross-brand mirror |
| 14 | Decisions honored cite (R6) | N/A | |

## Strengths

- **Dialog a11y:** all 3 modals (`LucasRecommendationDetailModal`, `LucasApprovalModal`, `LucasRejectModal`) have `role="dialog" aria-modal="true" aria-labelledby` + ESC handler via `onKeyDown` + `useEffect(() => el.focus(), [])` mount focus. Overlay separate with `aria-hidden="true"`.
- **RBAC tooltip pattern:** `userRole === "recepcion"` disables Approve button + tooltip + `aria-disabled` ⊕ `aria-live="polite"` explanation. Tests verify (SC-MK-04 covered).
- **Idempotency:** ApprovalModal handler awaits `useApproveRecommendation` mutation → BE returns `undoUntil` → store `setPendingUndoTimer(rec.id, expiryMs)` based on BE-derived timestamp (not client-side clock skew prone).
- **Hooks rules:** `LucasUndoChip` declares `useCallback(handleUndo)` BEFORE conditional early return (`expiryMs === null` branch) per Rules of Hooks. Comment line 58 documents the constraint.
- **Stable keys** (`rec.id` for list iteration); no array index.
- **No premature memoization** — list is short (top 3 + expand all), no `React.memo`/`useMemo` overkill.
- **Modal phase pattern:** ApprovalModal uses `phase: "confirm" | "approved"` state with auto-close timeout — clean state machine.
- **HIPAA scope respect:** LucasRecommendation contains no PHI (only marketing analytics + rec text); modal displays `rationaleJson` keys/values via `String()` cast — acceptable since BE guarantees no PHI per rationale schema.

## Findings

### WARN W1 — Nested interactive content (button inside button)

**Category:** 5 (Accessibility)
**File:** `vitalia/frontend/src/features/marketing/components/LucasStageRecommendationsCard.tsx:223-261`
**Issue:** `RecommendationItem` renders an outer `<button>` (card click → detail modal). Inside it (line 259) `<LucasUndoChip recId={rec.id} />` is conditionally rendered — and `LucasUndoChip` itself contains a `<button>` ("Deshacer", line 85 of LucasUndoChip.tsx). HTML5 forbids nesting interactive content inside `<button>`. axe-core `nested-interactive` rule will flag this. Browsers tolerate the markup but keyboard nav becomes ambiguous (Tab order on inner button + Enter on outer button can trigger both). Screen readers may not announce the inner button.

Currently the chip only renders when `expiryMs !== null` (post-approve window), so the bug surfaces only during the 5-min countdown after approval — but during that window, screen-reader users cannot reliably reach/activate the undo control.

**Suggested fix:**
- Option A (preferred, no test churn): Restructure `RecommendationItem` to use a `<div>` with `role="button"` + `tabIndex={0}` + `onKeyDown` (Enter/Space) for the card surface, leaving real `<button>` only for the inner undo action. Pattern already used by `ChannelBreakdownRow.tsx:61-69`.
- Option B: Move the `LucasUndoChip` OUT of the card button (render it as a sibling `<aside>` adjacent to the item).

Either fix is structural (NOT auditor self-fix whitelist per `.claude/rules/auditor-self-fix-policy.md`); spawn `builder-frontend` autonomous loop OR Chris ratifies WARN-only since the deferred `visual_a11y_axe` validator would flag this in CI.

**Skill ref:** `tessl__react-patterns` — semantic HTML, nested interactive prohibited (WCAG 4.1.2 `Name, Role, Value`).

### WARN W2 — `toLocaleString` instead of tenant-locale wrapper

**Category:** 8 (Master Data)
**File:** `vitalia/frontend/src/features/marketing/components/LucasRecommendationDetailModal.tsx:56`
**Issue:** `new Date(iso).toLocaleString("es-PE", ...)` is hardcoded to Peru locale. Per `.claude/rules/master-data.md` BE/FE rule: "Display: `formatTenantDate*()`" — should use the tenant locale via `useTenantLocale()` hook so a Mexican/Argentine/Colombian clinic sees their own date format.
**Suggested fix:** Replace with `formatTenantDateTime(iso, locale.timezone)` (or equivalent helper from `vitalia/frontend/src/lib/format/`). If a helper doesn't exist yet, use `new Intl.DateTimeFormat(undefined, { ... })` to inherit browser locale (still imperfect, but tenant-correct vs hardcoded PE).
**Skill ref:** `.claude/rules/master-data.md` (FE: `formatTenantDate*()` — NOT `toLocaleDateString()`).

## Contract / UI-SPEC Compliance

- [x] Approval modal warning per `02-design-ui.md § 1` ("Acción reversible · puedes deshacer 5min")
- [x] Reject modal radio options per `02-design-ui.md § 4` (`MARKETING_COPY.rejectReasons` 5 enum values)
- [x] Undo chip 5-min countdown from BE `undoUntil` (correct, not client-derived)
- [x] Detail modal 2 tabs (Análisis + Acción a ejecutar) per `02-design-ui.md § 1` mockup

## Allowlist Movement / Native-First / Live Verification

- [x] No allowlist growth
- [x] No docker/make e2e
- [x] No `git add .`
- [x] Manual verification steps documented in T-mk-fe-3-result.md § Live verification status

## Verdict Math

- 0 FAILs · 2 WARNs (W1 a11y + W2 master-data)
- 2 WARNs > 1 ⇒ formally **overall WARN**, but neither blocks critical functionality. Per Chris paradigm (forward-motion autonomy v4.1) and given gate-output.json all 8 gates PASS, recommend **APPROVED with WARN follow-up**:
  - W1 should be fixed before deferred `visual_a11y_axe` runs in CI (or it will FAIL CI gate).
  - W2 self-fix candidate (whitelist category — not in NEVER list; but `toLocaleString` swap is logic-shaping → safer to spawn dev-team).

**Result:** PASS (with 2 WARNs to address).
