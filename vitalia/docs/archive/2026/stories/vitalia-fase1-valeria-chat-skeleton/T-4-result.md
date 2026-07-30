# T-4 Result — ChatComposer molécula

**Story:** vitalia-fase1-valeria-chat-skeleton
**Ticket:** T-4
**Brand:** vitalia
**Builder:** claude-sonnet-4-6
**Commit SHA:** ef879cd1
**Pushed at:** 2026-05-24T20:15:00-05:00
**Branch:** wip/vitalia

## Summary

ChatComposer molécula implementada — `'use client'` interactive footer para el panel de chat Valeria (F1-S6). TDD RED→GREEN cycle completado (23 tests escritos primero, luego implementación).

## Files created

| File | LOC | Type |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` | 162 | production |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.test.tsx` | 367 | test |

## Quality gates

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict mode |
| ESLint | PASS | 0 errors, 0 warnings (on T-4 files) |
| Vitest T-4 | PASS | 23/23 tests green |
| Vitest full | PASS | 1162/1162 tests (coverage 73.26% statements) |
| Architecture fitness | PASS | 83/83 tests (16 test files) |

## TDD cycle

**RED phase:** wrote 23 tests covering all gherkin_coverage scenarios (SC-2, SC-3, SC-6, IME guard, idempotency, kbd hint, auto-resize, empty guard).

**Key technical fix — IME guard in JSDOM:**
- React synthetic `KeyboardEvent<T>` does NOT expose `isComposing` directly
- Implementation uses `e.nativeEvent.isComposing` (accesses native DOM event)
- Test uses `Object.assign(new KeyboardEvent(...), { isComposing: true })` to bypass JSDOM's readonly prototype property

**GREEN phase:** minimal implementation satisfying all 23 tests.

## Implementation decisions

| Decision | Choice | Reason |
|---|---|---|
| `e.nativeEvent.isComposing` vs `e.isComposing` | `nativeEvent` | React synthetic type doesn't expose it directly |
| Native `<textarea>` vs Shadcn `<Textarea>` | Native | Shadcn uses `field-sizing-content` CSS; spec requires JS `useEffect + scrollHeight` resize |
| Plain `<button>` for Send vs Shadcn `Button` | Plain | Spec uses `bg-agent-valeria text-white` — no matching Shadcn variant |
| Store anti-pattern | `useChatStore.setState()` in tests | NO `vi.mock` per 03-arch.md tessl__vitest |
| 3 icon stubs | NOT disabled | D3 spec explicitly says NOT disabled, title="próximamente" |

## Gherkin coverage (T-4)

| Scenario | Tests | Status |
|---|---|---|
| SC-2: Enter envía + clears | 4 tests | GREEN |
| SC-3: Shift+Enter newline | 1 test | GREEN |
| SC-6: a11y sr-only label + id | 4 tests | GREEN |
| IME guard isComposing | 1 test | GREEN |
| Stubs render NOT disabled | 4 tests | GREEN |
| Empty/whitespace guard | 2 tests | GREEN |
| kbd hint Cmd+K | 3 tests | GREEN |
| Auto-resize useEffect | 1 test | GREEN |
| Idempotency status=thinking | 1 test | GREEN |
| **Total** | **23** | **23/23 GREEN** |

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary, component placement | `components/shared/shell-organism/` correct per shell chrome scope |
| `tessl__react-patterns` | Error boundary, loading/empty states, accessible markup | sr-only label, aria-labels, aria-hidden emoji spans, `aria-busy` pattern |
| `tessl__shadcn-ui` | Component reuse check | Native `<textarea>` justified — Shadcn conflict with JS auto-resize |
| `tessl__tailwind` | `cn()` for conditional classes, no inline `style={{}}` | Exception: `el.style.height` in useEffect (DOM manipulation, not Tailwind) |
| `tessl__vitest` | Test setup, zustand setState pattern | `useChatStore.setState()` for reset; `vi.spyOn` for sendMessage |
| `frontend-fsd.md` | Boundary matrix verification | `components/shared/shell-organism/` — cross-feature shell chrome allowed |
| `spanish-text.md` | All user-facing strings | "Enviar", "Escribe a Valeria…", "Mensaje para Valeria", "Adjuntar archivo", "Mensaje de voz", "Comandos rápidos" — all tuteo |
| `tdd-mandatory.md` | RED before GREEN mandatory | Tests written and verified failing before implementation |

## spec_anchor

`01-spec.md § 0 D3 + § 4 ChatComposer + § 6 microcopy · 03-arch.md § 2.5`

## Next ticket

T-5 — ValeriaChat organism + ChatMessages branch logic (depends on T-2, T-3, T-4)
