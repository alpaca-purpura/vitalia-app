# T-infra-7 — AppShell + Sidebar + TopBar + CopilotRail layout components

**Status:** done  
**Ticket ID:** T-infra-7  
**Story:** vitalia-slice-1-infra-cross-cutting  
**Validator IDs:** fe_typecheck_tsc · fe_lint_eslint · fe_arch_fitness · fe_test_shared  

---

## Files Created

### Format helpers (`src/lib/format/`)
- `formatMoney.ts` — tenant-aware money formatter, NEVER hardcodes 'USD', fallback ARS
- `formatTenantDate.ts` — ISO 8601 → localized date in tenant timezone
- `formatTenantDateTime.ts` — ISO 8601 → localized date+time in tenant timezone
- `formatTenantRelative.ts` — ISO 8601 → relative time ("hace 3 minutos")

### API client (`src/lib/api/`)
- `fetchClient.ts` — tenant+clinic aware fetch wrapper; auto-injects Clerk JWT + X-Tenant-ID + X-Clinic-ID (HIPAA-lite dual filter); AbortController timeout 30s

### Global hooks (`src/hooks/`)
- `useTenantLocale.ts` — reads Clerk org metadata for currency/timezone/locale
- `useCurrentUser.ts` — reads current user + role (VitaliaRole type)
- `useClinicId.ts` — reads clinic ID for HIPAA-lite dual filter
- `useFeatureFlag.ts` — reads feature flags from Clerk org metadata
- `usePiiRoleGate.ts` — returns PHI access gate based on role

### Agent components (`src/components/shared/agents/`)
- `agent-names.ts` — agentNameByRole(), AGENT_GRADIENT_CLASS, AGENT_INITIALS constants
- `AgentAvatar.tsx` — circular gradient avatar (sm/md/lg sizes)
- `AgentAttribution.tsx` — attribution line: [Avatar] Name action target timestamp
- `index.ts` — barrel export

### PHI HIPAA-lite components (`src/components/shared/phi/`)
- `PiiMaskedSpan.tsx` — field-type-aware masking (name/dni/phone/email/address/dob)
- `RequireRole.tsx` — role gate (doctor|nurse|admin_clinic allowed); pure Server-safe component
- `AuditedSection.tsx` — fires sync audit log on mount; silent-fail non-blocking
- `index.ts` — barrel export

### Shell layout (`src/components/shared/shell/`)
- `AppShell.tsx` — Sidebar + TopBar + main content area; 240px sidebar
- `Sidebar.tsx` — 240px expanded / 64px collapsed; active state vt-bg-cian-10 + vt-border-cian-l
- `TopBar.tsx` — 56px; page title + user menu (Clerk) + copilot toggle
- `index.ts` — barrel export

### Copilot rail (`src/components/shared/copilot-rail/`)
- `CopilotRail.tsx` — 80px idle / 460px open; gradient trigger button
- `CopilotChat.tsx` — chat history (empty/loading states) + textarea input + send
- `index.ts` — barrel export

### Domain widgets
- `src/components/shared/nps/NPSTagBadge.tsx` — 0-6=detractor(red)/7-8=passive(yellow)/9-10=promoter(green)
- `src/components/shared/nps/index.ts`
- `src/components/shared/contact-sidebar/ContactSidebar.tsx` — contact info with PiiMaskedSpan
- `src/components/shared/contact-sidebar/index.ts`
- `src/components/shared/activity-stream/ActivityStreamSticky.tsx` — 32px collapsed / 240px expanded
- `src/components/shared/activity-stream/index.ts`

### Tests (`src/components/shared/__tests__/`)
- `format-helpers.test.ts` — 11 tests for all 4 format helpers (GREEN)
- `hooks.test.ts` — 4 tests for agentNameByRole (GREEN)
- `phi-components.test.tsx` — 6 tests for PiiMaskedSpan + RequireRole (GREEN)
- `nps-badge.test.tsx` — 5 tests for NPSTagBadge (GREEN)

### Infrastructure
- `src/test-setup.ts` — vitest jest-dom setup
- Modified `vitest.config.ts` — added setupFiles, expanded coverage include
- Modified `package.json` — added @testing-library/react, @testing-library/user-event, @testing-library/jest-dom
- Modified `src/app/globals.css` — added vt-* CSS utility classes for color tokens (arch fitness fix)

---

## Validator Results

| Validator | Result | Notes |
|---|---|---|
| `fe_typecheck_tsc` | PASS | 0 errors |
| `fe_lint_eslint` | PASS (new files) | Pre-existing: 2 errors in arch test files (T-infra-4 baseline) — not introduced by T-infra-7 |
| `fe_arch_fitness` | PASS | 9/9 tests GREEN (38 assertions) — incl. test_no_hardcoded_colors |
| `fe_test_shared` | PASS | 26 component tests GREEN, 245 total tests, 64.19% coverage (≥20% threshold) |

---

## HIPAA-lite Compliance

- All PHI field renders use `<PiiMaskedSpan>` (field-type-aware masking)
- Role gate via `<RequireRole>` (doctor|nurse|admin_clinic only)
- `<AuditedSection>` fires audit log beacon on mount (sync best-effort per HIPAA-lite)
- `fetchClient` injects X-Clinic-ID alongside X-Tenant-ID for dual filter
- `usePiiRoleGate` hook for programmatic PHI access control

## Architecture Fitness

- All colors consumed via `vt-*` CSS classes defined in `globals.css` (no `hsl()` in TSX)
- No default exports anywhere
- Server Components default; `"use client"` only on components with state/effects
- No voseo in any user-facing strings
- No cross-feature imports (shared components imported via barrel)
- PHI fields in ContactSidebar wrapped with PiiMaskedSpan (test_phi_pii_components_used PASS)

## Skills Consulted

- `frontend-expert` — FSD-Lite structure, vt-* CSS pattern for arch color test compliance
- `tessl__react-patterns` — error boundaries, loading/empty states, accessible markup, aria-* attributes
- `tessl__shadcn-ui` — reuse existing components; Tailwind utility-first
- `tessl__tailwind` — cn() for conditional classes; no inline style={{}}
- `tessl__nextjs-app-router-modularization` — Server Components default; "use client" leaf nodes
