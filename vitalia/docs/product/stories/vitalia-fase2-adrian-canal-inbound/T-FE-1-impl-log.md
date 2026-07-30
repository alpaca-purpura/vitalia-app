# T-FE-1 — Impl Log — Composer modo-instrucción

**Story:** vitalia-fase2-adrian-canal-inbound  
**Ticket:** T-FE-1  
**Surface:** FE (workhorse)  
**Cap:** adrian.inbox (EXTEND)  
**Date:** 2026-06-21

---

## § Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | ALWAYS | FSD-Lite structure, fetchClient pattern with `{token, tenantId}` options, React Query mutation hook pattern, no `"use client"` on types/api files |
| `brand-expert` | Not applicable (no brand-studio/form-runtime) | — |
| `copilot-expert` | Not applicable | — |
| `sales-agent-expert` | Context only | Operator instruction is NON-PHI commercial text; goes through `override_context_wire.py`; engine reads from JSONB |
| `chrome-devtools-verify` | Live verify gate — PENDING (G phase per checkpoint) | Dev stack must be running; deferred to OLA-1 live-verify per story `next_action` |
| `playwright-expert` | E2E smoke spec written | V-VIS-1 playwright_visual_scope honored; NATIVE Linux; no `make e2e*` |
| `tenant-isolation` | ALWAYS | `useTenantId()` — NEVER `useAuth().orgId`; fetchClient takes `tenantId` param |

---

## § Plan

### Design-system-first (D1)
- Reused existing atoms: `cn()`, vitalia CSS tokens (`vt-bg-cian-8`, `vt-text-cian`, etc.)
- No new primitives invented — `InstructionChip` built from bare HTML with vitalia tokens
- `InstructionChip` intentionally NOT in `components/ui/` — it is feature-specific to adrian.inbox

### Mockup adherence + scope (D2+D3)
- Implemented exactly what SC-8 + RN-13/14 scope: effectiveMode label + chip + send CTA relabeling
- Did NOT add multi-modal file attachment in instruction mode (out of scope per playwright_visual_scope)
- Did NOT touch shell-organism wrapper (forbidden_to_touch)

### Test battery (TDD RED-first)
1. RED: `use-operator-instruction.test.ts` — hook + `getEffectiveMode()` pure function
2. RED: `InstructionChip.test.tsx` — chip render + edit/clear callbacks
3. RED (EXTEND): `ComposerArea.test.tsx` — effectiveMode label + chip + button labels
4. GREEN: all 23 new tests pass
5. REGRESSION: 367 adrian tests pass (53 files), 2589 full suite

### Integration (CONN)
- `ComposerArea` is already wired in `InboxThread` / `AdrianInboxView` — no orphan risk
- Hook invalidates `["adrian", "conversation", conversationId]` query key on success
- New exports added to `index.ts` barrel

---

## § Files Changed

### NEW
- `vitalia/frontend/src/features/adrian/types/operator-instruction.ts` — types
- `vitalia/frontend/src/features/adrian/api/operator-instruction.ts` — API client
- `vitalia/frontend/src/features/adrian/hooks/use-operator-instruction.ts` — React Query mutation + `getEffectiveMode()`
- `vitalia/frontend/src/features/adrian/components/inbox/InstructionChip.tsx` — persistent instruction chip
- `vitalia/frontend/src/features/adrian/hooks/__tests__/use-operator-instruction.test.ts` — 5 tests
- `vitalia/frontend/src/features/adrian/components/inbox/__tests__/InstructionChip.test.tsx` — 4 tests
- `vitalia/frontend/e2e/specs/smoke/instruction-composer.smoke.spec.ts` — V-VIS-1 smoke

### MODIFIED
- `vitalia/frontend/src/features/adrian/components/inbox/ComposerArea.tsx` — effectiveMode integration
- `vitalia/frontend/src/features/adrian/components/inbox/MessageInput.tsx` — `effectiveMode` prop + instruction placeholder
- `vitalia/frontend/src/features/adrian/components/inbox/SendButton.tsx` — `effectiveMode` prop + "Dar instrucción" label
- `vitalia/frontend/src/features/adrian/lib/copy.ts` — `instruction.*` copy + `sendButtonInstruction`
- `vitalia/frontend/src/features/adrian/index.ts` — T-FE-1 exports
- `vitalia/frontend/src/features/adrian/components/inbox/__tests__/ComposerArea.test.tsx` — updated for effectiveMode (intentional RN-14 change)

---

## § Architecture decisions

- `effectiveMode` derived at render time from `handler_mode` (pure fn `getEffectiveMode`) — no Zustand state
- Attach + Voice buttons hidden in instruction mode (no media instruction use case in scope)
- `InstructionChip.onClear()` posts `instruction: ""` to BE — BE interprets empty = deactivate
- `fetchClient` called with `{ token, tenantId }` (vitalia pattern — not manual headers)
- All new TS/TSX files carry `// cap: adrian.inbox` header line 1

---

## § Mockup scope notes

- Mockup (01-spec.md § instrucción FE mechanic) shows the chip and label — implemented exactly
- Audio input in instruction mode: out of scope (V-VIS-1 doesn't mention it; hidden)
- Chip "editar" pattern: copies text back to textarea for re-submission (matches spec)

---

## § Regression guard — intentional changes (RN-14/15 coordinator exception)

Old tests that assumed `handler_mode: "ai"` still means "Enviar" button → updated to use `handler_mode: "human"` explicitly. This is the documented `excepcion_coordinada`:
> "composer en decide EXTENDIDO a modo-instrucción (RN-14/15) — cambio intencional sobre superficie firmada; NO es break"

5 tests updated, behavioral intent preserved.

---

## § Gate results

- `tsc --noEmit`: ✅ 0 errors
- `eslint src/features/adrian/`: ✅ 0 errors
- `vitest run src/features/adrian/`: ✅ 367/367 pass (53 files)
- `vitest run --coverage` (full suite): ✅ 2589/2589 pass (281 files)
- Playwright smoke (V-VIS-1): Written; native exec pending dev-stack up

---

## § Live verify

Per `definition-of-done-live-verify.md` and checkpoint `autonomous_mode: false`:
- Live verify deferred to G phase (Chris-verify gate) — story has `phase: READY_PACKAGE_CLOSED`, G not yet entered
- DoD #37 requires: POST /instruction in dev-app + chip appears + lead not notified + 0 console errors
- Chrome DevTools MCP available when dev stack is up at `localhost:3002`
