# T-7 Fase 7A — result

**Status:** tests-structure-passing · visual-goldens deferred a Fase 7B (Chris ratify side-by-side gate)
**Owner:** `/dev-team` (Opus orchestrator) — sub-agent builder-frontend Sonnet hit context cap mid-debug del strict-mode triple-main, remate manual orchestrator.
**Branch:** `wip/vitalia`
**Files modified:** 3 (playwright.config.ts + ShellOrganismLayout.tsx SSR guard + checkpoint.md)
**Files new:** 7 (POM + fixture + 5 spec files)
**Tests new:** 5 spec files structured (4 functional + 1 visual-goldens skipped pending ratify)

## Scope Fase 7A (implementado)

- **POM** `vitalia/frontend/e2e/pages/ShellLayoutPage.ts` — wrappers Locator + helpers `dragHandle`, `getValeriaWidth`, `getStorageSplit`, `getStorageState`
- **Fixture** `vitalia/frontend/e2e/fixtures/shell-theme.fixture.ts` — extends Clerk auth + theme initial light/dark + localStorage reset
- **4 functional E2E specs**:
  - `render-agentic-default.spec.ts` (SC-1 happy · 6 assertions)
  - `mobile-collapse.spec.ts` (SC-2 negative · 4 assertions)
  - `resize-and-state.spec.ts` (SC-3 edge · 4 assertions)
  - `a11y-keyboard.spec.ts` (SC-4 adversarial · 4 assertions + axe wcag2aa)
- **Visual goldens spec STRUCTURED** `visual-goldens.spec.ts` (6 test cases, `test.skip` annotations pending Fase 7B)

## Cambios paralelos requeridos durante Fase 7A

- **`vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx`** — defensive SSR guard `globalThis.localStorage` (en vez de bare `localStorage` ref), evita ReferenceError en SSR pre-hydration. Bug-fix legítimo descubierto durante test boot.
- **`vitalia/frontend/playwright.config.ts`** — agregar `e2e/regression/` glob al smoke project para que los nuevos specs corran.

## Conocidos pending Fase 7B

1. **Strict-mode `app-panel-slot` 2x** — el triple-main pattern (CSS-driven mutually-exclusive `md:hidden` / `hidden md:block` / `hidden md:grid`) hace que `<main>` con `data-testid="app-panel-slot"` aparezca en DOM en 2 ramas (mobile fallback + agentic/web active). El POM ya usa `.first()` / `:visible` filter — pero Fase 7B debe verificar contra dev-server real que los Locator queries no rompen por strict-mode antes de tomar goldens.
2. **`--update-snapshots`** — 6 PNG goldens NO generadas todavía. Pending Chris ratify side-by-side mockup HTML vs componente React real → orchestrator ejecuta Fase 7B.

## Validators output (parcial Fase 7A)

| Validator | Status | Output |
|---|---|---|
| `val-fe-tsc` | ✅ PASS | `npx tsc --noEmit` clean (no output) |
| `val-fe-lint` | ✅ PASS | `npx eslint` (POM + fixture + 5 specs + ShellOrganismLayout) clean |
| `val-fe-vitest-unit` | ✅ PASS | 121 test files / 979 tests pass (no regressions de T-1..T-6) |
| `val-fe-e2e-render-agentic-default` | ⏸ DEFERRED 7B | requires dev-server boot |
| `val-fe-e2e-mobile-collapse` | ⏸ DEFERRED 7B | idem |
| `val-fe-e2e-resize-and-state` | ⏸ DEFERRED 7B | idem |
| `val-fe-e2e-a11y-keyboard` | ⏸ DEFERRED 7B | idem |
| `val-fe-axe` | ⏸ DEFERRED 7B | idem |
| `val-fe-visual-agentic-light` | ⏸ DEFERRED 7B post-ratify | --update-snapshots |
| `val-fe-visual-agentic-dark` | ⏸ DEFERRED 7B post-ratify | idem |
| `val-fe-visual-agentic-rail` | ⏸ DEFERRED 7B post-ratify | idem |
| `val-fe-visual-web-light` | ⏸ DEFERRED 7B post-ratify | idem |
| `val-fe-visual-web-dark` | ⏸ DEFERRED 7B post-ratify | idem |
| `val-fe-visual-mobile` | ⏸ DEFERRED 7B post-ratify | idem |

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| `playwright-expert` | ✅ loaded | Step 0 · POM patterns + Clerk auth + visual goldens contract |
| `frontend-expert` | ✅ loaded | Step 0 · FSD-Lite + Tailwind tokens |
| `tessl__react-patterns` | ✅ loaded | Step 0 |
| `.claude/rules/frontend-fsd.md` | ✅ loaded | mid-build · POM imports cross-feature OK |
| `.claude/rules/spanish-text.md` | ✅ loaded | mid-build · aria-label assertions |
| `.claude/rules/anti-duplication.md` | ✅ loaded | Step 0 · ShellLayoutPage no mirror cross-brand |
| `.claude/rules/tdd-mandatory.md` | ✅ loaded | Step 0 |
| `.claude/rules/e2e-testing.md` | ✅ loaded | Step 0 · Playwright invocation pattern |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | ✅ loaded | Step 0 · visual golden side-by-side contract maxDiffPixelRatio 0.001 |
| `.claude/rules/auditor-self-fix-policy.md` | ✅ loaded | Step 0 |

## gherkin_coverage matched (Fase 7A — structure)

| Scenario | Test file | Status |
|---|---|---|
| SC-1 happy · render 50/50 default agentic | `render-agentic-default.spec.ts` | ⏸ structure ✓ · run Fase 7B |
| SC-2 negative · viewport < md colapsa | `mobile-collapse.spec.ts` | ⏸ structure ✓ · run Fase 7B |
| SC-3 edge · resize boundary clamp + persist + snap-up | `resize-and-state.spec.ts` | ⏸ structure ✓ · run Fase 7B |
| SC-4 adversarial · a11y keyboard nav + axe wcag2aa | `a11y-keyboard.spec.ts` | ⏸ structure ✓ · run Fase 7B |

## Pause Gate · Fase 7B requirements

Antes de ejecutar `npx playwright test --update-snapshots` (Fase 7B), Chris MUST ratificar side-by-side:

1. Servidor local mockups: `python3 -m http.server 8888` en `mockups/` dir (ya corriendo desde sesión `/po-ux` original)
2. Dev-server vitalia/frontend localhost:3002 vía `make dev-vitalia` (orchestrator levanta pre Fase 7B)
3. Chris abre browser: http://localhost:8888/shell-layout-agentic.html (mockup ratificado) vs http://localhost:3002/{tenantId} (componente real)
4. Side-by-side comparison + Chris confirma "ratificado" → orchestrator ejecuta Fase 7B
5. Fase 7B steps: dev-server up + `npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/ --update-snapshots` + verify 6 PNGs generadas + commit goldens + push

## Next action

Chris invoca pause-ratify procedure (orchestrator levanta dev-server + reporta URLs).

---

## Fase 7A fidelity refit (iter post-screenshot — 2026-05-23 PM)

Tras screenshot side-by-side mockup vs componente real, Chris detectó que vs el mockup ratificado iter 4 el componente real se veía tosco (slots vacíos, handle no respeta px cementados, TenantSwitcher mock missing). Refit aplicado en mismo branch `wip/vitalia` sin transición de state:

### Cambios aplicados (4 files)

| File | Cambio |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` | Skeleton siluetas matching mockup: rail 60px (5 íconos cuadrados) + history 280px (rows agrupadas con headers) + chat area (5 bubbles muted/agent-valeria-soft + composer). Slot label flotante centrado. Mobile fallback "abrir desde menú" |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | Skeleton ribbon 5 agentes colored (lisa-soft · lucas-soft · adrian-soft · valeria-soft · camila-soft) + Configurar grey + sub-tabs bar 40px + content cards 2x2 grid. Children layer encima del skeleton (cuando F1-S7 active ribbon real domina) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | `useRef + ResizeObserver` al containerRef del `<main>` agentic para calcular `minSize` PERCENT desde MIN px cementados (`MIN_VALERIA_PX = valeriaState==='full' ? 620 : 360` + `MIN_APP_PX = 480`). Workaround a react-resizable-panels v4 que usa percent en `minSize` no px. Separator también más sutil (`w-px → hover w-1`) |
| `vitalia/frontend/e2e/__test-pages__/shell-layout/shell-layout-showcase.tsx` | Mock tenant store con `MOCK_TENANTS` (Sonrisa Plena PE + Dermalia MX) hidratado via `useEffect` — best-effort (ver gap conocido abajo) |

### Visual ratify markers (Playwright DOM probe)

```json
{
  "hasValeria": true,         // ValeriaSidebarSlot mounted (640x752 at x=0)
  "hasApp": true,             // AppPanelSlot mounted (640x752 at x=641)
  "hasTenant": false,         // TenantSwitcher gap (ver abajo)
  "skeletonState": false      // ShellOrganismLayoutClient hidratado client-side
}
```

Side-by-side screenshots: `/tmp/mockup-agentic-light.png` vs `/tmp/real-shell-light.png` (Chris ratificó visual 2026-05-23 PM, modulo TenantSwitcher gap aceptado).

### Gap conocido — TenantSwitcher mock en showcase fixture

**Symptom:** `<TenantSwitcher />` renderiza `null` en `/test-stack/shell-layout` aún con mock tenants hidratados via `setAvailableTenants` + `setActiveTenant` en useEffect.

**Root cause:**
- `TenantSwitcher.tsx:97-99` graceful-degrade: `if (!isLoading && !isError && availableTenants.length === 0) return null`
- En primer render: `availableTenants = []` (store default) → returns null inmediatamente
- `useTenants()` hook está `enabled: isLoaded && isSignedIn === true` — en showcase `isSignedIn = false` → query never fires → store nunca hidrata vía hook
- Mock del showcase corre `useEffect` post-mount, pero el TenantSwitcher dentro de `dynamic({ssr:false})` chunk + Zustand subscription post-null-return no triggera re-render reliable
- Probé 3 approaches en orden: `useEffect` original (la del primer commit T-7) → module-level `useTenantStore.setState()` → `useState(() => setState; return null)` lazy init. Los tres fallan por timing diferente.

**En PROD real funciona:** Clerk signed-in → `useTenants()` corre `/api/tenants` → response hidrata store → TenantSwitcher renderiza normal (probado en F1-S3 dedicated tests `TenantSwitcher.test.tsx` + spec).

**Decisión Chris 2026-05-23:** aceptar gap. NO bloquea visual ratify del shell layout 5050 (split + slots skeleton + handle son lo prioritario). Follow-up nice-to-have: refactor TenantSwitcher con `__forceMock` prop o wrappear showcase con `MockClerkProvider isSignedIn=true` — out-of-scope T-7 Fase 7A.

**Mock retenido en showcase** (useEffect original) para preservar la intención + facilitar resolución futura cuando alguien refactor TenantSwitcher.

### Vitest no-regression post-refit

121 test files / 979 tests pass (sin regresiones vs T-1..T-6 baseline).

### Próximos pasos Fase 7B

1. Servidor mockups corriendo: `http://localhost:8888/shell-layout-agentic.html`
2. Dev-server vitalia: `http://localhost:3002/test-stack/shell-layout`
3. `cd vitalia/frontend && npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/ --update-snapshots` → genera 6 PNGs
4. Commit goldens + push
5. Phase D local coverage check
6. State transition `developing → developed`
7. AUTO-HANDOFF `/auditor`

---

**Last line per anti-telephone-game contract:**

`done -> /home/chalreme/Proyectos/luana-vitalia/vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/T-7-result.md`
