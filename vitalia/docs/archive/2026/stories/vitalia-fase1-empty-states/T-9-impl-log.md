# T-9 Implementation Log — page.tsx MODIFY + 3 arch tests NEW
# F1-S10 vitalia-fase1-empty-states
# Brand: vitalia | Builder: claude-sonnet-4-6

## Skills Consulted (must_load enforcement v4.1)

| Skill | Invocado | Decisión |
|---|---|---|
| `frontend-expert` | YES — always required | FSD-Lite boundary matrix confirmed; feature public API (`index.ts`) must be used for cross-feature imports. Direct internal paths like `@/features/lisa/components/placeholders/MarcaPlaceholder` are forbidden — arch test `test_no_cross_feature_imports.test.ts` enforces. |
| `tessl__react-patterns` | YES — always required | Server Component default applied (SubTabContent is pure Server Component dispatcher). Error boundary at route level via Next.js `not-found.tsx`. Loading/error/empty states applied (EmptyState fallback for unknown sub-tabs). Stable keys: PLACEHOLDER_MAP uses static keys. |
| `tessl__nextjs-app-router-modularization` | YES — page.tsx mixes params (async) + delegation | Next.js 16 App Router: `params` is `Promise<{...}>` — MUST `await params` before use. Page is pure Server Component (no `"use client"`). SubTabContent is pure Server Component dispatcher; individual placeholders that need state mark themselves `"use client"`. |
| `tessl__vitest` | YES — 3 new arch tests | Vitest `readFileSync` pattern for source-level arch tests. `resolve(__dirname, "../..")` from `src/__tests__/architecture/` to reach `src/`. Import `{ describe, it, expect }` from `vitest`. Regex-based source parsing for SubTabContent PLACEHOLDER_MAP keys. |

## Scope

Files modified:
1. `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` — MODIFY: replaced F1-S9 static text with `<SubTabContent agent={agent} subtab={subtab} />`, added `isValidAgent` + `isValidSubtab` guards + `notFound()` on invalid routes
2. `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` — UPDATE: replaced 22 `makeStub()` inline stubs with real placeholder component imports via feature public APIs; populated PLACEHOLDER_MAP with all 22 entries
3. `vitalia/frontend/src/__tests__/architecture/test_subtab_content_uses_ribbon_subtabs_ssot.test.ts` — NEW: 6 tests verifying PLACEHOLDER_MAP ↔ RIBBON_SUBTABS alignment
4. `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_subtab_keys.test.ts` — NEW: scans all TS/TSX source for hardcoded composite `"agent.subtab"` keys outside ALLOWED_FILES
5. `vitalia/frontend/src/__tests__/architecture/test_no_phi_real_data.test.ts` — NEW: scans placeholder components for unmasked PHI (phone, email, DNI)
6. `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.test.tsx` — UPDATE: 6 tests updated from F1-S9 static text assertion (`/Contenido próximamente/`) to T-9 data-testid assertion (`subtab-content-{agent}-{subtab}`)

## Key Decisions

### FSD-Lite compliance (critical fix)
Initial SubTabContent.tsx draft used internal import paths like `@/features/lisa/components/placeholders/MarcaPlaceholder`. This violated FSD-Lite boundary rule — arch test `test_no_cross_feature_imports.test.ts` detected 22 violations. Fixed by using feature barrel exports exclusively: `import { MarcaPlaceholder, ... } from "@/features/lisa"`. All feature `index.ts` files were already exporting the needed components from T-2..T-8 work.

### Arch test path resolution
`__dirname` in Vitest = filesystem path of the test file itself. From `src/__tests__/architecture/`, going `../..` reaches `src/`. All 3 arch tests use `const SRC_ROOT = resolve(__dirname, "../..")`.

### ALLOWED_FILES in test_no_hardcoded_subtab_keys
Paths are relative to `SRC_ROOT` (i.e., relative to `src/`):
- `"components/shared/shell-organism/SubTabContent.tsx"` (no `src/` prefix)
- `"lib/agent-catalog.ts"`
- `"__tests__/architecture/test_subtab_content_uses_ribbon_subtabs_ssot.test.ts"`
- `"__tests__/architecture/test_no_hardcoded_subtab_keys.test.ts"`
- `"__tests__/architecture/test_no_phi_real_data.test.ts"`

### HIPAA-lite PHI arch test
`test_no_phi_real_data.test.ts` enforces vitalia brand overlay rule (`hipaa-lite.md`). Regex patterns:
- Phone: `UNMASKED_PHONE_REGEX = /(?<!\*)\+?\d[\d\s-]{9,}\d(?!\*)/g` (no `\-` — avoids ESLint `no-useless-escape`)
- Email: `UNMASKED_EMAIL_REGEX = /\b[a-zA-Z0-9][a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/g`
- DNI: `UNMASKED_DNI_REGEX = /(?<![*\d])\d{8,}(?![*\d])/g`

### page.test.tsx fix
After T-9 replaced F1-S9 static placeholder with `<SubTabContent>`, 6 existing tests were checking for `screen.getByText(/Contenido próximamente/)` — text that no longer renders (SubTabContent dispatches to real placeholder components). Updated assertions to use `screen.getByTestId("subtab-content-{agent}-{subtab}")` — the wrapper `data-testid` that SubTabContent always renders.

## Validators

| Validator | Result |
|---|---|
| `val-fe-tsc` | PASS — 0 errors |
| `val-fe-lint` | PASS — 0 errors |
| `val-fe-format` | PASS |
| `val-fe-arch-subtab-content-uses-ribbon-subtabs-ssot` | PASS — 6/6 tests green |
| `val-fe-arch-no-hardcoded-subtab-keys` | PASS — 2/2 tests green |
| `val-fe-arch-no-phi-real-data` | PASS — 4/4 tests green |
| `val-fe-arch-fsd-boundaries` | PASS — 0 violations |
| `val-fe-arch-no-cross-brand-mirror` | PASS |
| `val-fe-vitest` | PASS — 1691/1691 tests, 165/165 files |

## Coverage

Coverage thresholds (≥20% all categories) — PASS. Pre-existing coverage levels maintained.

## ESLint baseline

check-file / jsdoc / react-perf warning baselines: unchanged (not grown).

## Live Verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux Mint. Manual verification documented:
- Route `/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` now renders `<SubTabContent>` with correct agent/subtab for all 22 valid combos
- Invalid agent/subtab triggers `notFound()` → Next.js `not-found.tsx`
- Visual verification: `data-testid="subtab-content-{agent}-{subtab}"` wrapper confirmed in test renders
- Escalated to Chris staging gate per protocol
