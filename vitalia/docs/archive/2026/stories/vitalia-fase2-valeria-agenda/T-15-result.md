# T-15-result.md — FE CobrarSaldoSubform

**Ticket:** T-15 — FE CobrarSaldoSubform  
**Story:** vitalia-fase2-valeria-agenda  
**Brand:** vitalia  
**Branch:** wip/vitalia  
**Completed:** 2026-05-27

---

## Deliverables

### New Files

| Path | Description |
|------|-------------|
| `vitalia/frontend/src/features/valeria/components/agenda/CobrarSaldoSubform.tsx` | Main inline cobro subform — RHF + Zod (flat working schema + discriminated union validation on submit), saga error handling, 3 error states |
| `vitalia/frontend/src/features/valeria/components/agenda/CobrarSaldoSubformErrorAlert.tsx` | Error/Warning alert component for saga states (payment_failed, fiscal_failed, conflict_409, validation_422, server_error) |
| `vitalia/frontend/src/features/valeria/components/agenda/CobrarSaldoSubformSuccessToast.tsx` | Success toast trigger via sonner + ChargeSuccessToastDescription with fiscal doc link |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CobrarSaldoSubform.test.tsx` | 16 unit tests covering A1-A9 acceptance criteria |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CobrarSaldoSubform.saga.test.tsx` | 12 saga integration tests for 503/409 error states |

### Modified Files

| Path | Change |
|------|--------|
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerPagoSection.tsx` | Replaced `CobrarSaldoSubformPlaceholder` with real `<CobrarSaldoSubform />`, added `tenantId` + `defaultEmitInvoice` props |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawer.tsx` | Pass `tenantId` to `AppointmentDrawerPagoSection` |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawerPagoSection.test.tsx` | Updated tests: replaced placeholder testId with `cobrar-saldo-subform`, added QueryClient wrapper + mocks |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawer.test.tsx` | Added `useChargeAppointment`, `useEmitFiscalDoc`, `sonner` mocks |
| `vitalia/frontend/src/features/valeria/index.ts` | Added barrel exports for CobrarSaldoSubform, CobrarSaldoSubformErrorAlert, CobrarSaldoSubformSuccessToast |

---

## Acceptance Criteria Status

| # | Criterion | Status |
|---|-----------|--------|
| A1 | Form renders with default values (amount = balance pendiente) | PASS — test verifies default amount = cents/100 |
| A2 | Discriminated union ChargeRequestSchema validates on submit | PASS — validated via ChargeRequestSchema.safeParse() on submit |
| A3 | Loading state during POST charge | PASS — aria-busy attribute on submit button |
| A4 | fiscalDocType shown only when emitInvoice=true | PASS — conditional rendering tested |
| A5 | Error 503 payment → ErrorAlert + Reintentar | PASS — saga test verifies |
| A6 | Error 503 fiscal → Warning + standalone retry | PASS — saga test verifies |
| A7 | Error 409 → "saldo ya cobrado" alert | PASS — saga test verifies |
| A8 | Currency override hidden by default in "Más opciones" | PASS — accordion collapsible |
| A9 | emit_invoice defaults from prop | PASS — tested with true/false variants |

---

## Quality Gate Results

| Gate | Result |
|------|--------|
| `tsc --noEmit` | PASS (0 errors, strict mode) |
| ESLint full src/ | PASS (0 errors, 0 new warnings) |
| Vitest 181 test files | PASS (1925/1925 tests) |
| Coverage threshold | PASS (>20% all categories) |

---

## Architecture Decisions

### RHF + Zod Discriminated Union

The `ChargeRequestSchema` uses `z.discriminatedUnion("currency", [...])` which creates complex TypeScript types incompatible with RHF's generic `useForm<T>`. Solution: flat `ChargeFormWorkingSchema` for RHF state management + `ChargeRequestSchema.safeParse()` validation on submit. This pattern is idiomatic for complex Zod unions with RHF.

### Slot Replacement (T-14 → T-15)

`CobrarSaldoSubformPlaceholder` from T-14 removed in-place. The `AppointmentDrawerPagoSection` now renders `<CobrarSaldoSubform />` when `hasDueBalance=true`. Props extended with `tenantId` (forwarded from AppointmentDrawer where it was already available).

### Currency Override via "Más opciones"

Currency override uses Shadcn Accordion collapsible. Default currency from `appointment.currencyOverride ?? appointment.currency ?? tenantCurrency`. Changing currency resets `fiscalDocType` to prevent invalid enum value being submitted.

### Idempotency Key

UUID v4 generated in `useRef` on mount. Same key reused on retry (per A5 spec). Key would reset on full form remount.

---

## Skills Consulted

| Skill | Why | Decision |
|-------|-----|----------|
| `frontend-expert` | FSD-Lite boundaries, ESLint config, test patterns | Named exports only, flat RHF schema pattern |
| `tessl__react-patterns` | Error boundaries, loading states, accessible markup | aria-busy on submit, role="alert" on error alerts, keyboard navigation |
| `tessl__zod` | Discriminated union + RHF resolver | Flat working schema + safeParse on submit |
| `tessl__shadcn-ui` | Component selection | Accordion for collapsible, Alert variants |
| `tessl__tailwind` | Utility classes | cn() for conditional, no inline style |
| `tessl__vitest` | Mock patterns, async tests | vi.mock per-module pattern |
| `tessl__graceful-degradation` | Saga error states | 3 distinct error states + saga compensation |
| `vitalia/.claude/rules/hipaa-lite.md` | PHI safety | amount + method NOT PHI, no masking needed |

---

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (2026-05-15 note). Manual verification required at Chris staging gate. API dependencies (vitalia-payment-adapter-mvp, vitalia-fiscal-emission-pe) not yet developed — full E2E Playwright scenarios (SC-1, SC-2, SC-5, SC-11) blocked on service deps.

---

<!-- @pm: build phase done (state: tests-passing). Commit: see SHA below. Files: 10. Native ticket tests: 28/28 PASS + 9 regression PASS + 11 regression PASS. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
