# T-FE-1 Result — Composer modo-instrucción

**State:** pushed  
**Commit:** 6375cb0d  
**Branch:** wip/vitalia  
**Owner:** builder-frontend (workhorse)  
**Date:** 2026-06-21

---

## Delivered

### New files
- `types/operator-instruction.ts` — `SetOperatorInstructionRequest` / `SetOperatorInstructionResponse` / `ComposerMode` (camelCase mirror of BE DTOs, ISO 8601)
- `api/operator-instruction.ts` — `operatorInstructionApi.set(token, tenantId, payload)` → `POST /api/v1/adrian/conversations/{id}/instruction`
- `hooks/use-operator-instruction.ts` — `useOperatorInstruction()` React Query mutation + `getEffectiveMode()` pure helper (effectiveMode logic)
- `components/inbox/InstructionChip.tsx` — persistent instruction chip (RN-13): shows active instruction with Editar / ✕ controls; amber token styling
- `hooks/__tests__/use-operator-instruction.test.ts` — 5 tests (hook + getEffectiveMode)
- `components/inbox/__tests__/InstructionChip.test.tsx` — 4 tests
- `e2e/specs/smoke/instruction-composer.smoke.spec.ts` — V-VIS-1 smoke (3 scenarios; native PW)

### Modified files
- `components/inbox/ComposerArea.tsx` — effectiveMode integration: instruction label + chip + mode-aware send
- `components/inbox/MessageInput.tsx` — `effectiveMode` prop + instruction placeholder
- `components/inbox/SendButton.tsx` — `effectiveMode` prop + "Dar instrucción" label
- `lib/copy.ts` — `INBOX_COPY.instruction.*` + `sendButtonInstruction`
- `index.ts` — T-FE-1 exports
- `__tests__/ComposerArea.test.tsx` — updated per `regression_guard.excepcion_coordinada` (RN-14/15 intentional change)

---

## effectiveMode logic

```typescript
// Pure — no side effects
export function getEffectiveMode(handlerMode: "ai" | "human"): ComposerMode {
  return handlerMode === "human" ? "direct" : "instruction";
}
```

- `handler_mode === "ai"` (Adrián decide) → `"instruction"`: label "🤖 Instrucción a Adrián", hint "el paciente no la verá", CTA "Dar instrucción", POST /instruction, lead NEVER receives
- `handler_mode === "human"` (Adrián paused) → `"direct"`: unchanged composer sends to lead (RN-14)

---

## Gate output

| Gate | Result |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `eslint src/features/adrian/` | ✅ 0 errors |
| `vitest run src/features/adrian/` | ✅ 367/367 PASS (53 files) |
| `vitest run --coverage` (full suite) | ✅ 2589/2589 PASS (281 files) |
| Playwright V-VIS-1 smoke | Written; exec pending dev stack (native: `E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep="instruction"`) |
| Bidirectional cap validator | SOFT_DRIFT advisory (non-blocking, same as T-BE-3) |
| Regression guard (excepcion_coordinada) | 5 ComposerArea tests updated for intentional RN-14 change; behavior preserved |

---

## Skills Consulted

- `frontend-expert` — FSD-Lite boundary, fetchClient `{token, tenantId}` options pattern, React Query mutation hook
- `tenant-isolation` — `useTenantId()` used in hook; NEVER `useAuth().orgId`
- `sales-agent-expert` — confirmed instruction is NON-PHI commercial text; goes through `override_context_wire.py`
- `playwright-expert` — V-VIS-1 smoke spec pattern; native Linux; no `make e2e*`
- `chrome-devtools-verify` — live verify PENDING (deferred to G phase per `autonomous_mode: false`)

---

## Validators covered

- V-VIS-1: composer instruction label + chip (unit tests + smoke spec written)
- V-FN-7 (SC-8): effectiveMode dispatch + POST /instruction wired
- V-ARCH-4: no PHI in URL/searchParams (instruction in POST body)
- regression_guard: 367 tests GREEN; ComposerArea test changes documented as intentional

---

## Live verify (DoD #37) — PENDING

Per `autonomous_mode: false` + `checkpoint.phase: READY_PACKAGE_CLOSED`:  
Live verify deferred to G-phase (Chris-verify). Required evidence:
1. Navigate to inbox with `handler_mode=ai` conversation
2. See "🤖 Instrucción a Adrián" label + amber composer border
3. Type instruction → POST /api/v1/adrian/conversations/{id}/instruction returns 200
4. InstructionChip appears with typed text
5. Lead receives NOTHING on Telegram (no outbound)
6. Pause Adrián → composer switches to direct mode (no instruction label)
7. Console: 0 errors; Network: 0 unexpected 4xx/5xx
