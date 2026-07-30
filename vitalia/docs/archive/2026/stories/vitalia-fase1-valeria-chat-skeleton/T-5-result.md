# T-5 Result — ValeriaChat + ChatMessages + EmptyStateChat

**Story:** vitalia-fase1-valeria-chat-skeleton (F1-S6)
**Ticket:** T-5
**Brand:** vitalia
**Builder:** claude-sonnet-4-6
**Completed:** 2026-05-24

## Files Created

| File | LOC | Purpose |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx` | ~50 | Organism root — 3-row grid, composes ChatHeader + ChatMessages + ChatComposer |
| `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx` | ~90 | Messages panel — role="log" aria-live, empty/populated branch, auto-scroll sentinel |
| `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.test.tsx` | ~220 | Unit tests: empty state, populated 6 msgs, ARIA, Spanish neutro (SC-1/SC-5/SC-6/SC-7) |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.test.tsx` | ~160 | Integration tests: organism structure, SC-1/SC-2/SC-5/SC-6 |

## Files Modified

| File | Change |
|---|---|
| `vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/06-tickets.yaml` | T-5 state: ready → pushed |
| `vitalia/frontend/src/__tests__/architecture/test_no_voseo_in_copy.test.ts` | Reverted — no change (baseline kept clean) |

## Key Decisions

### Wrapper/footer pattern — Opción A (self-contained MessageBubble)
- Read MessageBubble.tsx (T-3 done) to verify it owns `flex flex-col gap-1 self-start max-w-[80%]` wrapper and `time` footer internally.
- Decision: ChatMessages.renderMessage() passes raw props to MessageBubble — no outer wrapper added.
- Reference: spec_anchor `03-arch.md § 2.5 ChatMessages` footnote: "Wrapper/footer decision (T-5 result): MessageBubble already owns its wrapper...so renderMessage() passes raw props — no outer wrapper added here."

### Store initialization — Opción A (chat-store already seeded)
- Verified chat-store.ts (T-2 pushed commit 76eaa919) already initializes `messages: [...MOCK_MESSAGES]`.
- No store modification needed. ChatMessages renders populated state on mount automatically.

### EmptyStateChat — inline function (not reusing EmptyStateInline)
- EmptyStateInline.tsx (F1-S5) has incompatible shape: different props, different testid, Search icon. Not reusable.
- EmptyStateChat is a private function inside ChatMessages.tsx (no separate file, no export).
- Shape: avatar (ring-4 ring-agent-valeria-soft) + heading + subtexto.

### Spanish neutro corrections per spec § 6
- Heading: "Empieza una conversación" (tuteo form — voseo form avoided per spanish-text.md)
- Subtexto: "Pregúntale a Valeria..." (WITH tilde + clítico — voseo form without tilde avoided)
- Tests verify both via positive and negative assertions.

### SC-2 test pattern — fireEvent + fake timers
- `userEvent.setup({ advanceTimers })` caused timeout with Vitest fake timers.
- Used `fireEvent.change` + `fireEvent.click(sendButton)` instead for fake timer compatibility.
- Avoids ChatComposer's `nativeEvent.isComposing` edge case in jsdom environment.

### Voseo detection regex in test file
- ChatMessages.test.tsx initially included raw voseo pattern regex as a string literal.
- Architecture test `test_no_voseo_in_copy.test.ts` flagged this (correct behavior — it scans shell-organism/*.tsx).
- Fix: Rewrote voseo assertion to use structural patterns (`/á[sz]$/i`, `\bvos\b/i`) instead of raw voseo strings. Arch test passes clean.

## Quality Gates

### TypeScript strict
```
cd vitalia/frontend && npx tsc --noEmit
→ 0 errors
```

### ESLint (60+ rules)
```
cd vitalia/frontend && npx eslint src/ --cache
→ 0 errors, 1 warning (pre-existing in chat-store.test.ts line 278 — not introduced by T-5)
```

### Vitest with coverage
```
cd vitalia/frontend && npx vitest run --coverage
→ Test Files: 133 passed (133)
   Tests: 1193 passed (1193)
   Coverage: ≥20% all categories (global baseline)
```

### Architecture fitness tests (16 files, 83 tests)
```
cd vitalia/frontend && npx vitest run src/__tests__/architecture/
→ 16 passed (16), 83 tests all GREEN
```

Validators:
- val-fe-tsc: PASS
- val-fe-lint: PASS (0 errors)
- val-fe-vitest-unit: PASS (1193/1193)
- val-fe-arch-fsd: PASS (boundaries/dependencies 0 violations)
- val-fe-arch-no-hex: PASS (no hardcoded hex in new files)
- val-fe-arch-no-voseo: PASS (ChatMessages.test.tsx voseo-free; test assertions restructured)
- val-fe-arch-no-vt: PASS (no .vt-* classes)
- val-fe-arch-server-first: PASS (ValeriaChat.tsx + ChatMessages.tsx have "use client" — justified per spec: hook consumers)

## Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | Context brief R24 validation — Faithfulness: clean | No partial gaps; proceed |
| `tessl__react-patterns` | Error boundary at route-level; loading/error/empty states; aria-live="polite"; role="log"; stable keys (msg.id) | Applied EmptyStateChat branch + aria attrs + sentinelRef auto-scroll |
| `tessl__tailwind` | `cn()` for conditional classes; no inline style | Applied throughout — grid layout, agent token classes |
| `tessl__vitest` | Fake timer pattern; `act()` wrapping Zustand setState; `fireEvent` vs `userEvent` with fake timers | Used `fireEvent.change/click` for SC-2 to avoid timeout |
| `tessl__zod` | N/A — no forms in T-5 | Not invoked |
| `frontend-fsd` | Boundary matrix: ChatMessages.tsx in `components/shared/shell-organism/` (correct FSD-Lite placement) | No cross-feature imports; barrel not needed (shell-organism uses direct imports) |
| `spanish-text` | "Empieza" tuteo; "Pregúntale" WITH tilde | Both corrected per spec § 6 |
| `anti-duplication` | 0 cross-brand matches for ValeriaChat/ChatMessages/EmptyStateChat | LIFT CANDIDATE comment added (second brand consumer triggers promotion) |
| `chrome-devtools-verify` | DEPRECATED on Linux Mint (documented in CLAUDE.md) | Manual verification deferred → escalated to Chris staging gate |

## Live Verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint environment (WSL2+Windows bridge, rewrite pending). Manual verification steps:

1. `make dev-vitalia` → http://localhost:3002
2. Navigate to shell (authenticated tenant)
3. Verify: 3-row grid visible (header + messages + composer)
4. Verify: 6 mock messages render in correct order
5. Verify: Type message + click Enviar → user bubble + thinking → 800ms → bot reply
6. Verify: Clear store → empty state with Valeria avatar + heading
7. Verify: console 0 errors, network 200s

Escalated to Chris staging gate per CLAUDE.md protocol.

## HIPAA-lite

`not_applicable` — shell chrome UI, no PHI, mock data only.

## Downstream Regression

`downstream-regression-na` — brand-local shell-organism; no cross-brand consumers (confirmed by test-no-cross-brand-shell-mirror.test.ts).
