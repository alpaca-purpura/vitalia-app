# T-8 Result — Playwright behavior specs (happy/send/keys/xss)

**Story:** vitalia-fase1-valeria-chat-skeleton  
**Ticket:** T-8  
**State:** pushed  
**Commit:** b804eb73  
**Date:** 2026-05-24  
**Builder:** builder-frontend (claude-sonnet-4-6)  
**production_code:** false (tests-only)

---

## Scope

4 Playwright E2E behavior spec files covering Gherkin scenarios SC-1..SC-4.

| File | Scenario | Tests | Result |
|---|---|---|---|
| `valeria-chat-happy.spec.ts` | SC-1 happy render (6 mock messages) | 7 | PASS |
| `valeria-chat-send.spec.ts` | SC-2 send mock message flow | 7 | PASS |
| `valeria-chat-keys.spec.ts` | SC-3 keyboard behavior | 4 | PASS |
| `valeria-chat-xss.spec.ts` | SC-4 XSS adversarial guard | 6 | PASS |

**Total: 26/26 tests GREEN** — executed against live stack `http://localhost:3002` (vitalia dev port).

---

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| ESLint (60+ rules) | PASS — 0 errors |
| Prettier check | PASS — all files formatted |
| Playwright 26/26 | PASS — 14.2s wall clock |

---

## Files Created

- `vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts` (113 lines)
- `vitalia/frontend/e2e/shell-organism/valeria-chat-send.spec.ts` (157 lines)
- `vitalia/frontend/e2e/shell-organism/valeria-chat-keys.spec.ts` (175 lines)
- `vitalia/frontend/e2e/shell-organism/valeria-chat-xss.spec.ts` (205 lines)

## Files Modified

- `vitalia/frontend/playwright.config.ts` — smoke project testMatch extended with `/.*\/e2e\/shell-organism\/valeria-chat-.*\.spec\.ts/`
- `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` — added `data-testid` to 3 stub buttons (`composer-attach`, `composer-voice`, `composer-quick`) needed by SC-1 test
- `vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/06-tickets.yaml` — T-8 state: ready → pushed

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | Mandatory baseline — FSD-Lite patterns, ESLint gates, studio section precedent | Confirmed E2E specs live in `e2e/shell-organism/` alongside POM + fixtures. Pattern matches T-7 placement. |
| `tessl__react-patterns` | Error boundaries, stable keys, accessible markup patterns applied in spec assertions | Confirmed assertions check `aria-live="polite"` on chat-messages container (a11y baseline). |
| `playwright-expert` (via e2e-testing.md) | E2E spec patterns, fixture composition, POM consumption | Native Linux execution (NEVER docker). Smoke project. `chatStoreSeed` for SC-1 (seeded state), `chatStoreEmpty` for SC-2/SC-3/SC-4 (clean slate for precise counting). |

---

## Notable Decisions

1. **Import path fix**: Specs import `"./fixtures/chat-store-seed.fixture"` (same-level `fixtures/` dir inside `shell-organism/`), not `"../fixtures/"` (root fixtures dir). Fixed after first Playwright run surfaced module-not-found error.

2. **data-testid added to ChatComposer stubs**: T-4 built stub buttons without data-testid attributes. T-8 SC-1 spec requires them to be findable via locator. Added `composer-attach`, `composer-voice`, `composer-quick` to the 3 existing stub buttons — no logic change, pure test hookup.

3. **`chatStoreEmpty` for SC-2/SC-3/SC-4**: All interactive behavior tests start from empty state to allow precise message counting (0 → 2 after send+bot reply). `chatStoreSeed` used only for SC-1 (seeded render verification).

4. **`waitForStatus("idle")` for SC-2**: Used POM `waitForStatus()` (polling `window.__chatStore__`) instead of hardcoded `waitForTimeout` for the 800ms thinking transition. Resilient to timing variance.

5. **IME test is stability-check only**: True IME composition simulation is unreliable in Playwright/Chromium. SC-3 IME test verifies component stability post synthetic event dispatch. Authoritative IME guard test lives in `ChatComposer.test.tsx` (unit).

6. **XSS dialog listener pattern**: `page.on('dialog', ...)` registered before any action per Playwright docs. Dialog listener dismisses + sets `dialogFired` flag. Verified after 1500ms wait to allow any async alert.

---

## Playwright Execution

**Live stack:** YES — executed against `http://localhost:3002` (vitalia dev Next.js server running).  
**Project:** smoke  
**Auth:** public route `/test-stack/shell-layout` — no Clerk auth required (fixture does NOT use auth.fixture, extends base `@playwright/test` directly).  
**Result:** 26/26 PASS in 14.2s  
**Retries needed:** 0 (import path fix preceded successful run)
