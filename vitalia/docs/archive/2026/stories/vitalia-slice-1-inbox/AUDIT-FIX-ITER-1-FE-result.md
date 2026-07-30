# Audit Fix Loop — FE Iter 1 Result

> Story: vitalia-slice-1-inbox
> Iter: 1 / 3 (FE)
> Commit: 88f06b3
> Branch: wip/vitalia
> Date: 2026-05-20

## Findings Addressed

### FAIL #4 — InboxPageClient not wired to real components

**Status: FIXED**

`InboxPageClient.tsx` now wires all 5 real components:
- `ConversationListPanel` (left pane — search + filters + list)
- `ConversationThread` (center — conditional render when `conversationId` non-null)
- `AgentActivityStream` (center — sticky bottom activity strip)
- `ContactSidebar` (right pane — HIPAA-lite PHI-aware, role-gated NPS)
- `AdrianToolsSheet` (slide-over — read-only tools panel)

Key decisions:
- `toolsSheetOpen` uses local `useState(false)` since store doesn't have it yet (T-inbox-fe-6 scope)
- `ConversationThread` only renders when `conversationId` is non-null (interface requires `string`)
- `ContactSidebar.npsHistory` receives `undefined` (`ConversationDetail` type has no `nps_history`)
- `"use client"` moved to first line (before JSDoc) to satisfy arch test FE-A5 first-500-bytes check
- `InboxPageClient.tsx` added to `KNOWN_FSD_BOUNDARY_VIOLATIONS` allowlist (crm-shared consumer, same justification as other inbox components)
- HIPAA-lite PHI wrapping (PiiMaskedSpan + RequireRole + AuditedSection) preserved unchanged in ContactSidebar

### FAIL #1 — master-data violations (toLocaleDateString / Intl.DateTimeFormat hardcoded locale)

**Status: FIXED**

4 files updated to use `formatTenantDate*()` + `useTenantLocale()`:
- `AgentActivityStream.tsx` — `toLocaleTimeString("es-419", ...)` → `formatTenantTime(event.occurred_at, timezone, locale)`
- `AdrianToolsSheet.tsx` — `toLocaleDateString("es-419", ...)` → `formatTenantDateTime(invocation.invoked_at, timezone, locale)`
- `ContactSidebar.tsx` — `new Date(...).toLocaleDateString("es-419", ...)` → `formatTenantDate(entry.recorded_at, timezone, locale)`
- `ConversationItem.tsx` — `Intl.DateTimeFormat("es-419", ...)` fallback → `formatRelativeTime(ts, timezone, locale)` (accepts timezone/locale params)

New helper created: `vitalia/frontend/src/lib/format/formatTenantTime.ts` (time-only: HH:MM:SS with tenant timezone, no existing formatter covered seconds).

All 4 components now call `useTenantLocale()` and thread `{ timezone, locale }` into sub-components / pure functions.

### FAIL #2 — Missing error.tsx and loading.tsx for /inbox route

**Status: FIXED**

- `vitalia/frontend/src/app/(app)/inbox/error.tsx` — Client Component (required by Next.js), useEffect logs non-PHI error digest/message, shows `INBOX_COPY.errors.generic` + retry button with `INBOX_COPY.errors.retry`, uses `vt-*` tokens, no inline styles
- `vitalia/frontend/src/app/(app)/inbox/loading.tsx` — Server Component, 3-column skeleton (list 320px | thread flex-1 | sidebar 280px), `aria-busy="true"`, animate-pulse with `vt-bg-muted`, mirrors InboxLayout column structure

Import fix: `error.tsx` import changed from `@/features/inbox/copy` (internal path) to `@/features/inbox` (public API barrel) — resolves arch test FE-A4 violation.

### FAIL #3 — Hardcoded Tailwind named colors bypassing design tokens

**Status: FIXED**

Named color classes replaced with `vt-*` semantic tokens in 3 files:
- `AdrianToolsSheet.tsx` — `STATUS_CLASSES` map: `text-green-*`/`bg-green-*`/`text-red-*`/`bg-red-*`/`text-gray-*`/`bg-gray-*` → `vt-text-success`/`vt-bg-success-12`/`vt-text-danger`/`vt-bg-danger-soft`/`vt-text-muted`/`vt-bg-muted/{opacity}`. HIPAA guard note: `border-amber-200 bg-amber-50 text-amber-700` → `vt-border-warning-30 vt-bg-warning-12 vt-text-warning`
- `ContactSidebar.tsx` — `NpsScoreBadge`: `text-green-700 bg-green-100 border-green-300` → `vt-text-success vt-bg-success-soft vt-border-success-30`, amber/red equivalents replaced
- `ProactiveOutboundModal.tsx` — TemplatePreview: `bg-green-100 text-gray-800 border-green-200` → `vt-bg-success-12 vt-text-foreground border vt-border-success-30`. Success banner: `bg-green-50 border-green-200 text-green-700` → `vt-bg-success-soft vt-border-success-30 vt-text-success`

### WARN #1 — Hardcoded error string in ConversationListPanel

**Status: FIXED**

`ConversationListPanel.tsx` hardcoded `"No se pudieron cargar las conversaciones. Intenta de nuevo."` replaced with `{INBOX_COPY.errors.loadConversations}` (already exists in `copy.ts`).

### WARN #2 — Missing hook tests for useTranscribeAudio and useAttachMedia

**Status: FIXED**

Two new test files created:

`use-transcribe-audio.test.ts` (4 tests):
- SC-01: Happy path — audio blob uploaded, transcription returned with confidence >= 0.5
- SC-02: Low-confidence result (< 0.5) returned as-is (UI layer responsible for fallback)
- Error path: server returns 422, hook surfaces error
- PHI safety: Authorization + X-Tenant-ID + X-Clinic-ID headers present, no PHI in headers

`use-attach-media.test.ts` (4 tests):
- SC-01: Audio file upload — `media_kind: "audio"`, CDN URL returned
- SC-02: Image file upload — `media_kind: "image"`, `duration_s: null`
- Error path: server returns 413 (too large), hook surfaces error
- PHI safety: dual-filter headers (X-Tenant-ID + X-Clinic-ID) per hipaa-lite.md, no PHI in headers

### WARN #3 — Playwright E2E (adversarial + a11y)

**Status: NOT RUN — live stack not available in this session**

Playwright E2E requires live dev stack (`make dev-vitalia` on port 3002). Escalated to Chris staging gate per `chrome-devtools-verify` deprecation note (2026-05-15 — WSL2 skill deprecated for Linux Mint, requires rewrite).

Manual verification commands:
```bash
cd /home/chalreme/Proyectos/luana-vitalia
make dev-vitalia  # starts stack on port 3002

# Then in another terminal:
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/specs/regression/inbox.adversarial.spec.ts \
  e2e/specs/a11y/inbox.a11y.spec.ts
```

### WARN #4 — Arch test allowlist entries (FSD boundary)

**Status: FIXED** (addressed as part of FAIL #4)

`InboxPageClient.tsx` added to `KNOWN_FSD_BOUNDARY_VIOLATIONS` with justification: crm-shared is an infrastructure-like PRODUCER of CRM contracts (Ola 1+), inbox is a consumer per 03-arch-fe.md § 1.

## Clerk Mock Cascade Fix

After adding `useTenantLocale()` calls to 4 components, 4 existing test files needed `@clerk/nextjs` mock to prevent `useOrganization can only be used within the <ClerkProvider />` errors:

- `ConversationList.test.tsx` — mock added
- `ContactSidebar.test.tsx` — mock added
- `AgentActivityStream.test.tsx` — mock added
- `AdrianToolsSheet.test.tsx` — mock added

Pattern used: `vi.mock("@clerk/nextjs", () => ({ useOrganization: () => ({ organization: null }) }))` — `organization: null` triggers vitalia default locale (ARS / America/Argentina/Buenos_Aires / es-419).

## Validators Green

```
tsc --noEmit:          0 errors
eslint src/features/inbox/ src/app/(app)/inbox/:  0 errors
vitest run src/features/inbox/:    223/223 PASS (27 test files)
vitest run src/__tests__/architecture/:    42/42 PASS (10 test files)
Total:                 265/265 PASS
```

## Files Modified / Created

### Created (5)
- `vitalia/frontend/src/app/(app)/inbox/error.tsx`
- `vitalia/frontend/src/app/(app)/inbox/loading.tsx`
- `vitalia/frontend/src/features/inbox/api/__tests__/use-attach-media.test.ts`
- `vitalia/frontend/src/features/inbox/api/__tests__/use-transcribe-audio.test.ts`
- `vitalia/frontend/src/lib/format/formatTenantTime.ts`

### Modified (12)
- `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts`
- `vitalia/frontend/src/features/inbox/components/AdrianToolsSheet.tsx`
- `vitalia/frontend/src/features/inbox/components/AgentActivityStream.tsx`
- `vitalia/frontend/src/features/inbox/components/ContactSidebar.tsx`
- `vitalia/frontend/src/features/inbox/components/ConversationItem.tsx`
- `vitalia/frontend/src/features/inbox/components/ConversationListPanel.tsx`
- `vitalia/frontend/src/features/inbox/components/InboxPageClient.tsx`
- `vitalia/frontend/src/features/inbox/components/ProactiveOutboundModal.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/AdrianToolsSheet.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/AgentActivityStream.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/ContactSidebar.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/ConversationList.test.tsx`
