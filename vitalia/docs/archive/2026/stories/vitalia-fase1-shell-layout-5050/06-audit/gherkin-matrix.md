# Gherkin verification matrix — vitalia/vitalia-fase1-shell-layout-5050

> Auditor: `/auditor` orchestrator (Opus 4.7) + sub-agent `auditor-frontend`
> Date: 2026-05-23T18:05:00-05:00
> Audit iter: 3 (cap absoluto)
> Verdict: APPROVED-WITH-DEFER (33/34 Playwright + 1 DEFERRED documented)

## Scenarios SC-1..SC-4 mapping (4 spec scenarios → tests)

| # | Scenario (01-spec.md) | Test path | Status | Notes |
|---|---|---|---|---|
| SC-1 | happy · render 50/50 default modo agentic | `e2e/regression/vitalia-fase1-shell-layout-5050/render-agentic-default.spec.ts` (8 assertions) | ✅ PASS | TopBar 48px + ShellMode toggle + ValeriaSlot + AppSlot + Separator + split 50/50 + URL test-stack |
| SC-2 | negative · viewport < md colapsa a 1 columna | `e2e/regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts` (4 assertions) | ✅ PASS | ValeriaSlot count + visible=0 mobile + AppSlot visible mobile + skip-link target |
| SC-3 | edge · resize boundary clamp + persistencia + snap-up | `e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts` (5 assertions incluyendo persist + state full↔rail) | ⚠️ PARTIAL (4/5) | drag clamp ✅ · persist localStorage ✅ · state full→rail no shrink ✅ · drag-after-rail narrow ✅ · **rail→full snap-up race condition DEFERRED a F1-S5/S6 lifecycle refactor** |
| SC-4 | adversarial · a11y keyboard nav + skip-link target | `e2e/regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts` (4 assertions + axe wcag2aa) | ✅ PASS | Tab order + ResizeHandle keyboard + axe + skip-link focus |

## Visual goldens (mockup ratchet — Fase 7B)

| Variant | Path | Status |
|---|---|---|
| agentic light 1280x800 | `e2e/__screenshots__/regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts/agentic-1280x800-light.png` | ✅ locked |
| agentic dark 1280x800 | `agentic-1280x800-dark.png` | ✅ locked |
| agentic rail 1280x800 | `agentic-rail-1280x800.png` | ✅ locked |
| web light 1280x800 | `web-1280x800-light.png` | ✅ locked |
| web dark 1280x800 | `web-1280x800-dark.png` | ✅ locked |
| agentic mobile 375x667 | `agentic-mobile-375x667.png` | ✅ locked |

Goldens generados Fase 7B (commit cbb4af74) en project=visual con `maxDiffPixelRatio: 0.001`. Ratchet ahora locked vs mockups ratificados iter 4 Chris 2026-05-23.

## Run command + verdict

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/
```

**Result:** 27 passed + 1 skipped (28 smoke tests, 1 SC-3 assertion DEFERRED documented).
**Plus visual project:** 6 goldens GREEN (corren con `--project=visual`).

**Total coverage:** 33/34 = 97% pass rate · 1 test marked `test.skip` con razón cementada in spec SC-3.

## Coverage gaps + deferred work

### F1-S4b race-condition refactor (DEFERRED)

**Issue:** `setValeriaStateViaStore('rail')→reload→setValeriaStateViaStore('full')→reload→drag` race condition entre:
- `dynamic({ssr:false})` lazy-load del `ShellOrganismLayoutClient`
- `useDefaultLayout` localStorage restore PRE-mount Panel minSize calc
- `useEffect ResizeObserver.observe()` post-mount setContainerWidth

Fix iter 3 `useGroupRef` Fix A (commit 46fc8700) resolvió drag-clamp (F5) pero no este edge case (F6 — drag inmediato post-state-change).

**Tracking:** spec 01-spec.md § SC-3 anotado con bloque "DEFERRED 2026-05-23 (audit iter 3 ESCALATED Caso D)" + test marcado `test.skip(true, ...)` con razón. F1-S5/S6 lifecycle work podrá resolverlo cuando refactor Panel hydration timing.

**Ratified by Chris:** 2026-05-23 PM — accept 33/34 + spec amendment SC-3.

## Verdict

✅ **APPROVED-WITH-DEFER** — story F1-S4 ready for merge per /pm-vitalia.
