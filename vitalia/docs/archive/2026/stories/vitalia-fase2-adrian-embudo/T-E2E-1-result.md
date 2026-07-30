# T-E2E-1 — Result (PARTIAL · mocked-smoke DEFERRED)

**Story:** `vitalia-fase2-adrian-embudo`
**Ticket:** T-E2E-1 — visual goldens + axe + POMs + e2e integration (FE test-scaffolding)
**Date:** 2026-06-04
**Verdict:** **PARTIAL — mocked smoke suite + visual goldens DEFERRED to a follow-up.**
**Production code touched:** none net (a window-hook was added by a builder then removed — see below).
**Ratified by Chris:** proceed-on-live-verify (2026-06-04) — the REAL verification is the DoD basis; the mocked suite is documented test-infra debt.

---

## TL;DR

The **product is verified LIVE and genuine** (see `T-DEMO2-writes-result.md` — board-live.spec 9/9 against `dev-app.vitalialat.com`: create lead POST 201 + DB row, move-stage PATCH 200 + version/transition row, no traceback). `dod_live_verified: true` stands.

The **MOCKED smoke + a11y suite** (`embudo-*.smoke.spec.ts` + `embudo-a11y.spec.ts`) is **NOT green** and is **deferred**: it has a **test-fixture infrastructure blocker** (not a product bug). **Visual goldens baseline was NOT generated** (blocked by the same fixture issue). Tracked as a follow-up.

---

## The fixture-overlay blocker (root cause — for the follow-up)

Running the mocked smoke suite against `dev-app.vitalialat.com` (the domain the Clerk storageState is scoped to): **22 failed / 22 passed**. Dominant failure across nearly every spec:

```
TimeoutError: locator.click: Timeout 15000ms exceeded.
  - <html lang="es" data-theme="light">…</html> intercepts pointer events
```

**Every click on the authenticated MOCKED shell is intercepted by an `<html>`-level overlay** — proven NOT a Radix Select issue because the **Cancel button test also fails** (no Select, just clicks Cancel). A POM-level fix (waiting for the Radix listbox to close) did **not** help and was reverted.

**Discriminator:** the REAL spec `e2e/regression/vitalia-fase2-adrian-embudo/board-live.spec.ts` (real backend, NO shell mocks) clicks submit fine and creates a lead. The MOCKED smoke specs use `e2e/fixtures/authed-runtime.ts` (`setupClerkTestingToken` + `setupClinicContextMocks` + a `/api/v1/iam/users/me/tenants` mock). **The overlay originates from that fixture's shell mocks** — almost certainly a MISSING mock → the shell-organism renders a stuck loading skeleton / error boundary / blocking modal with `pointer-events` over the viewport (or a mock returns data that triggers a blocking overlay).

### Correct follow-up approach (do NOT repeat the window-hook detour)
1. Reproduce ONE failing click test, capture the **page snapshot** (`page.content()` / screenshot in a throwaway probe — do NOT rely on `test-results/` artifacts; concurrent sessions on the shared hub clobber that dir mid-run).
2. Identify the offending overlay element (`position:fixed; inset:0`, an `aria-busy` skeleton, or a Radix Dialog).
3. Fix `authed-runtime.ts` (+ maybe `clinic-context.fixture.ts`) to mock whatever the shell needs so it renders clean + interactable. THIS unblocks ~most reds at once.
4. THEN: update stale route-mocks to the repaired FE↔BE contract (camelCase full `LeadCardDTO` incl `version`), drive stage transitions via the `data-testid="move-stage-{leadId}"` button (not unreliable dnd-kit drag), re-run, generate the `embudo-visual.spec.ts` baseline (14 PNGs light+dark, ADR-003 maxDiffPixelRatio 0.001).
5. Run against the storageState's domain (`E2E_BASE_URL=https://dev-app.vitalialat.com`) or regenerate a localhost storageState — a domain mismatch sends every spec to Clerk /sign-in (the cause of an earlier 30/30 red).

### Do NOT use a production window-hook
A first builder (279k tokens, stalled) worked AROUND the override-dialog by adding a `window.__embudoStore__` test hook to `AdrianEmbudoView.tsx` instead of fixing the fixture overlay. That hook was **removed** (commit `a589cd46`) — test-scaffolding does not belong in production code for a deferred suite. Fix the fixture, not the component.

---

## Gherkin coverage basis (for the auditor Phase D)

With the mocked smoke suite deferred, Phase D coverage rests on:

| Scenario | Covered by |
|---|---|
| SC-1 (stage move), SC-nuevo (create), SC-board (render), SC-1b happy | **board-live.spec.ts (REAL backend, 9/9 PASS)** — POST 201 + DB row, PATCH 200 + version + transition row |
| SC-2 (422 skip), SC-5 (409 lock), SC-1b override, SC-3/4 (tenant), SC-freeze | **BE unit/integration** (`test_funnel_service` +89) + **Chris manual demo** (`demo-script.md` EDGE cases) |
| Anti-burbuja (#37) | board-live imports `base.ts` (pageerror / console.error / 4xx-5xx / Next overlay) — 0 errors |

The mocked-smoke FE-behavior-on-edge (toast/rollback on 409/422) is the **only** uncovered slice while the suite is deferred — a documented gap, not a product defect.

---

## Partial work preserved

- `e24f7e80` — builder WIP (POMs EmbudoBoardPage/LeadWorkspacePage + embudo-board.smoke rework + the window-hook, now removed). Recoverable base for the follow-up.
- `a589cd46` — window-hook removed from `AdrianEmbudoView.tsx` (component back to clean live-verified state).

---

## Verdict

**PARTIAL.** Product verified LIVE (real backend, DB effects) — DoD #37 satisfied. Mocked smoke suite + visual goldens **DEFERRED** (fixture-overlay test-infra blocker, tracked above). Proceeding to `/auditor` + Chris demo on the live-verify basis per Chris's ratified decision.

PARTIAL -> vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/T-E2E-1-result.md
