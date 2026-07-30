# T-6 Result — Playwright E2E Suite (POM + 9 specs + visual goldens)

**Story:** vitalia-fase1-sub-tabs-line2 (F1-S8)
**Ticket:** T-6
**State:** pushed
**Builder:** builder-frontend (claude-sonnet-4-6)
**Date:** 2026-05-25
**production_code:** false

## Summary

Playwright E2E suite for SubTabsBar organism: POM + 9 behavior spec files + visual-goldens.spec.ts (13 PNGs pattern). All files follow the F1-S7 Ribbon pattern verbatim (shell-theme.fixture, RibbonPage POM conventions).

## Files Created

| File | Purpose |
|---|---|
| `e2e/regression/vitalia-fase1-sub-tabs-line2/poms/sub-tabs-bar-page.pom.ts` | POM: goto / gotoRaw / getSubTabsBar / getSubTab / getAllSubTabs / clickSubTab / pressKey / getActiveSubTabId / getSubTabAriaSelected / getAriaLabel / getSubTabCount / getFocusedSubTabId / setViewport / setTheme |
| `sub-tabs-nav.spec.ts` | SC-1: click sub-tab navega a nueva ruta (4 tests) |
| `sub-tabs-agent-change.spec.ts` | SC-2: cambio de agente re-renderiza SubTabsBar (2 tests) |
| `sub-tabs-deeplink.spec.ts` | SC-3: deep link → active state correcto desde URL (3 tests) |
| `sub-tabs-null-agent.spec.ts` | SC-4: agente inválido → SubTabsBar return null total (3 tests) |
| `sub-tabs-invalid-subtab.spec.ts` | SC-5: agent válido + subtab inválido → N sub-tabs, ninguno active (2 tests) |
| `sub-tabs-mobile-overflow.spec.ts` | SC-6: overflow-x-auto en viewport 375 mobile (2 tests) |
| `sub-tabs-xss-guard.spec.ts` | SC-7: XSS en URL subtab segment → all inactive + no ejecución (2 tests) |
| `sub-tabs-keyboard.spec.ts` | SC-8: WAI-ARIA roving tabindex + axe wcag2aa (10 tests: 8 keyboard + 2 axe) |
| `sub-tabs-i18n.spec.ts` | SC-9: Spanish neutro + tildes (Adrián/Reputación/Configuración) (dynamic per-agent tests) |
| `visual-goldens.spec.ts` | 13 visual golden screenshots (6 light + 6 dark + 1 mobile 375) |

## Quality Gates

- tsc --noEmit: PASS (0 errors)
- ESLint: PASS (0 errors, 0 warnings)
- All spec files follow F1-S7 Ribbon spec conventions
- POM uses `shellPage` / `darkShellPage` fixtures from `shell-theme.fixture`
- No docker, no `make e2e*` — native Playwright pattern only
- Visual goldens: await `--update-snapshots` iter-1 post Chris ratify

## Gherkin Coverage (T-6)

- SC-1: sub-tabs-nav.spec.ts — click nav + URL update
- SC-2: sub-tabs-agent-change.spec.ts — ribbon agent change re-renders sub-tabs
- SC-3: sub-tabs-deeplink.spec.ts — URL-derived active state
- SC-4: sub-tabs-null-agent.spec.ts — Q5 cement: return null total
- SC-5: sub-tabs-invalid-subtab.spec.ts — N sub-tabs, ninguno active
- SC-6: sub-tabs-mobile-overflow.spec.ts — overflow-x-auto 375px
- SC-7: sub-tabs-xss-guard.spec.ts — XSS safety
- SC-8: sub-tabs-keyboard.spec.ts + @axe — roving tabindex WAI-ARIA
- SC-9: sub-tabs-i18n.spec.ts — Spanish neutro + tildes
- Visual: visual-goldens.spec.ts — 13 PNGs ratchet

## Architectural Decisions

- POM extends same pattern as `ribbon-page.pom.ts` (F1-S7). SubTabsBarPage class.
- Imported `RibbonPage` from F1-S7 pom in agent-change spec (tests ribbon → sub-tabs integration).
- Visual goldens scoped to `[data-testid="sub-tabs-bar"]` locator (avoids full-page noise).
- axe scans include('[data-testid="sub-tabs-bar"]') — organism-scoped per F1-S7 pattern.
- Q5 cement verified in null-agent spec: `sub-tabs-bar` element count = 0 in DOM.
- No visual golden PNGs committed — require `--update-snapshots` run on live app post Chris ratify.

## Execution (when app is running at localhost:3002)

```bash
# Preflight
cd /home/chalreme/Proyectos/luana-vitalia && bash scripts/e2e-preflight.sh

# Behavioral specs
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/vitalia-fase1-sub-tabs-line2/ --project=smoke

# Visual goldens (iter-1, after Chris ratify mockup)
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts \
  --project=visual --update-snapshots
```
