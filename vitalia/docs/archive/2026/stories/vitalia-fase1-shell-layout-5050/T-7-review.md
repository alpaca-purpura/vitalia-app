# T-7 Audit review — F1-S4 shell-layout-5050

**Auditor:** `/auditor` (orchestrator Opus 4.7) — Conv 3 review+merge
**Brand:** vitalia
**Story:** vitalia-fase1-shell-layout-5050
**Branch:** wip/vitalia
**Last commit reviewed:** aafb0717 (chore: developing → developed)
**Pre-audit commits:** c1925563 (Fase 7A refit) + cbb4af74 (Fase 7B goldens)

---

## Audit iteration 1 (2026-05-23T16:05:00-05:00)

### Verdict
CHANGES_REQUESTED — spawn dev-team Caso B (auto-fix loop)

### Gate verification

`gate-output.json` (iter 1, command: test-vitalia frontend, exit_code: 1):

| Gate | Status | Errors |
|---|---|---|
| tsc | ✅ PASS | 0 |
| eslint | ✅ PASS | 0 |
| **vitest** | ❌ **FAIL** | **2** |
| jscpd | ✅ PASS | 0 |
| knip | ⚠️ UNKNOWN | command not found (not installed) |
| madge | ⚠️ UNKNOWN | requires positional argument |

**Overall:** any_fail=true · 977 passed / 2 failed of 979 tests · vitest blocking.

### Findings (2 — both blockers)

#### F1 — Architecture violation: ShellOrganismLayoutClient.tsx falta "use client" en line 1

**Path:** `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx`
**Test que falla:** `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts`
**Categoría:** NEVER self-fix #2 (architecture-relevant, requires understanding convention) → Caso B spawn dev-team

**Detalle:**
El arch fitness test `test_server_first` detecta que el archivo usa React client-only hooks (`useRef`, `useState`, `useEffect`) pero la directiva `"use client"` NO está en línea 1. Actualmente vive en línea 29 después del JSDoc.

Next.js 16 convention: `"use client"` debe ser el primer statement no-comment del file. JSDoc comments before are allowed por algunos linters pero arch test enforce strict convention.

**Fix sugerido:**
Mover `"use client";` (línea 29) a línea 1 del file. JSDoc comment block puede ir DESPUÉS de la directiva.

```diff
+ "use client";
+
  /**
   * ShellOrganismLayoutClient — actual shell layout implementation.
   * F1-S4 vitalia-fase1-shell-layout-5050 — T-3 + T-7 SSR fix
   * ...
   */

- "use client";

  import { useEffect, useRef, useState } from "react";
```

#### F2 — Test expectations stale: ValeriaSidebarSlot.test.tsx esperaba placeholder vacío

**Path:** `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx`
**Component refactored:** `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` (c1925563)
**Categoría:** NEVER self-fix #1 (test update con assertions múltiples nuevas) → Caso B spawn dev-team

**Detalle:**
El test existente assertions:
```
expected 'Valeria — abrir desde menúValeriaSidebarSlot · F1-S5/S6' to be ''
(placeholder slot renders no children)
```

Pre-refit (T-2 commit base): `ValeriaSidebarSlot` era placeholder vacío con solo `<aside>` + slot label.

Post-refit (c1925563): renderiza skeleton siluetas matching mockup ratificado iter 4 — rail 60px (5 íconos) + history 280px (rows grouped) + chat area (5 bubbles + composer) + mobile fallback "Valeria — abrir desde menú" + slot label flotante.

El test viejo está obsoleto vs new behavior intencional ratificado por Chris.

**Fix sugerido:**
Update test para reflejar nueva estructura skeleton:
- Assert `data-testid="valeria-sidebar-slot"` exists + visible
- Assert `aria-label="Panel Valeria (placeholder — F1-S5/S6 lo construirá)"`
- Assert slot label text "VALERIASIDEBARSLOT · F1-S5/S6" present
- Assert mobile fallback hint "Valeria — abrir desde menú" present (for mobile viewport behavior — el test puede asertar el texto existe en DOM aun si CSS-hidden)
- Mantener structural assertions ya existentes (role, named export, etc.)

NO escribir nuevo test scenario — update existing assertions. Caso B porque cambia múltiples assertion lines + requiere inferencia del component structure.

### Action taken

1. ✅ Documented findings verbatim en este review file
2. ✅ Update checkpoint.md: `auditor_iter: 1`, `audit_iterations: 1`
3. → Spawn builder-frontend (Sonnet, no production_code) con mode: AUDITOR_AUTO_FIX_LOOP

### Re-audit plan

Post dev-team Caso B fix:
1. Spawn gate-runner re-iter para verify any_fail=false
2. Si GREEN → continue Step 2.5 Phase D gherkin matrix + Step 4 CHECKPOINTS.md C1-C5
3. Si RED iteration 2 → check audit_iterations cap (3 absoluto)

---

## Audit iteration 2 (2026-05-23T16:45:00-05:00)

### Verdict
CHANGES_REQUESTED — spawn dev-team Caso B (auto-fix loop iter 2)

### Gate verification

`gate-output.json` iter 2 status: ✅ any_fail=false (5 native FE gates GREEN — tsc/eslint/vitest 980/jscpd/arch fitness 64).

Sub-auditor `auditor-frontend` verdict: ✅ **APPROVED** (12 categorías GREEN, 2 nit-WARNs Cat 3 useEffect dep scope non-blocking).

### Phase D — Gherkin matrix execution

Comando: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/`.

Resultado: **24 passed / 10 failed** (de 34 total tests). Failures categorizados:

| # | Test | Type | Root cause |
|---|---|---|---|
| F3 | `render-agentic-default :: redirect /lisa/marca executed` | functional SC-1 | `expect(url).toContain(tenantId)` falla — POM.gotoShell navega a `/test-stack/shell-layout`, NO al route real `/{tenantId}/lisa/marca`. Assertion stale vs fixture behavior. |
| F4 | `mobile-collapse :: ValeriaSlot oculto mobile` | functional SC-2 | `locator.boundingBox: Timeout 15000ms` — POM.valeriaSlot ahora usa `filter({ visible: true }).first()` post Fase 7B fix POM. En mobile viewport ValeriaSidebar es CSS-hidden → filter no resuelve → timeout. Test legacy esperaba probar VISIBILITY 'oculto' pero locator filtro requiere visible match. |
| F5 | `resize-and-state :: drag handle left below 620 clamped` (line 54) | functional SC-3 | `expect(clampedWidth).toBeGreaterThanOrEqual(380)` falla — Fase 7A refit cambió min calculation: ResizeObserver convierte MIN_VALERIA_PX (620 full / 360 rail) a percentage dinámico con clamp `[10, 70]`. En el viewport del test, 620px representa >70% del container → clamped a 70% → resultado pixel < 620 + < 380. Assertion legacy presumía min fijo 620px ratio. |
| F6 | `resize-and-state :: state rail->full snap-up to 620` (line 134) | functional SC-3 | Same root cause F5: `snapWidth` no llega a 620 por clamp 70% post-ResizeObserver refit. |
| F7..F12 | 6 visual goldens en smoke project | visual SC-1..SC-4 | Smoke project testMatch incluye `e2e/regression/.*\.spec\.ts/` cubriendo visual-goldens.spec.ts — pero smoke NO tiene `snapshotPathTemplate` ni `maxDiffPixelRatio: 0.001` config. Solo el `visual` project tiene esa config. Tests fallan porque expect.toHaveScreenshot() no encuentra snapshots en path standard. |

### Findings (5 — iter 2)

#### F3 — render-agentic-default URL assertion stale

**Path:** `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/render-agentic-default.spec.ts:42`
**Categoría:** NEVER self-fix #1 (test assertion update con conceptual change) → Caso B

**Fix sugerido:**
La POM `gotoShell()` navega a `/test-stack/shell-layout` por design (no requiere F1-S9 routing). Assertion debe verificar URL `/test-stack/shell-layout` (no tenantId). O alternative: skip `tenantId` check + verify TopBar/slots rendered (already cubierto en otros tests).

```diff
- expect(url).toContain(tenantId);
+ // POM.gotoShell navega a /test-stack/shell-layout (fixture, no requiere F1-S9 routing).
+ // Assertion alterna: verificar shell hidratado en lugar de URL pattern.
+ expect(url).toContain("/test-stack/shell-layout");
```

#### F4 — mobile-collapse ValeriaSlot visibility check

**Path:** `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts`
**Categoría:** NEVER self-fix #1 (POM strategy mismatch) → Caso B

**Fix sugerido:**
POM.valeriaSlot ahora usa `filter({ visible: true }).first()` (Fase 7B fix) — en mobile retornaría nothing (CSS-hidden). Test mobile esperaba verificar AUSENCIA visible. Cambiar approach:

Opción A: usar locator base sin filter visible para verificar DOM presence + check `:visible` count = 0:
```ts
const valeriaSlotsAll = page.getByTestId("valeria-sidebar-slot");
const count = await valeriaSlotsAll.count();
const visibleCount = await valeriaSlotsAll.filter({ visible: true }).count();
expect(count).toBeGreaterThan(0);  // exist in DOM
expect(visibleCount).toBe(0);       // none visible at mobile
```

Opción B: omit Valeria locator (POM filter visible only) + assert mobile fallback hint "Valeria — abrir desde menú" present.

#### F5 + F6 — resize boundary tests legacy min 620

**Path:** `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts:54, 134`
**Categoría:** NEVER self-fix #1 (test conceptual update + branch logic) → Caso B

**Root cause:** Fase 7A refit (c1925563) cambió min calculation de pixel fijo a percentage dinámico con clamp `[10, 70]` via ResizeObserver. Test legacy presumía 620px hard min independiente del viewport.

**Fix sugerido:**
Updated assertions para reflejar new clamp behavior:

Opción A: testear en viewport ancho suficiente (e.g. 1600px) donde 620/1600 ~38% < 70% clamp → assertion 620 holds.
Opción B: cambiar assertion para verificar clamp behavior verbatim (containerWidth * 0.7 cap if > min absolute).

```diff
- expect(clampedWidth).toBeGreaterThanOrEqual(380);
+ // ResizeObserver clamp [10, 70]% del container. Verify mínimo respetado.
+ // En viewport del test, container es ~{XXXX}px. Min Valeria 620px = {YY}% > 70% → clamp 70%.
+ const containerWidth = await pom.getMainContainerWidth();
+ const expectedMin = Math.min(620, containerWidth * 0.7);
+ expect(clampedWidth).toBeGreaterThanOrEqual(expectedMin * 0.95);  // 5% tolerance
```

#### F7..F12 — 6 visual goldens fall en smoke project

**Paths:** los 6 tests dentro `visual-goldens.spec.ts`
**Categoría:** ✅ self-fix whitelist #18 (config testMatch update — 1 archivo + ~5 líneas) → Caso C OR delegate Caso B

**Fix sugerido:**
Exclude visual-goldens.spec.ts del smoke project (solo debe correr en visual project con sus config-specific). Update playwright.config.ts:

```diff
  {
    name: "smoke",
    testMatch: [
      /.*\.smoke\.spec\.ts/,
      /.*\/e2e\/auth\/.*\.spec\.ts/,
      /.*\/e2e\/dashboard\/.*\.spec\.ts/,
      /.*\/e2e\/visual\/.*\.spec\.ts/,
-     // F1-S4 shell-layout regression specs (functional + visual-goldens structure)
+     // F1-S4 shell-layout regression FUNCTIONAL specs (visual-goldens corre SOLO en project=visual)
      /.*\/e2e\/regression\/.*\.spec\.ts/,
    ],
+   testIgnore: [
+     // visual-goldens corre exclusivamente en project=visual (snapshotPathTemplate + maxDiffPixelRatio config)
+     /.*\/visual-goldens\.spec\.ts/,
+   ],
```

### Action taken iter 2

1. ✅ Documented 5 findings verbatim
2. ✅ Update audit_iterations: 2
3. → Spawn builder-frontend Caso B (Sonnet, no production code en specs/config)

### Cap check

audit_iterations: 2/3 (under cap). Si iter 3 también requires Caso B → ESCALATE Chris Caso D.

---

## Audit iteration 3 (2026-05-23T17:25:00-05:00)

### Verdict
CHANGES_REQUESTED — Chris ratified spawn dev-team Caso B iter 3 (FINAL — cap 3/3 absoluto)

### Phase D status post audit-iter-2 (commit 8fc6593f)

- Total: 34 Playwright tests
- Passed: 26
- Failed: **2** (down from 10)

### Findings (1 — F13 last gap)

#### F13 — Component snap-up logic missing post-ResizeObserver hydration

**Path:** `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx`
**Tests que fallan:**
- `resize-and-state.spec.ts:40 :: drag handle left below 620 clamped` — `Expected >= 589, Received 239.25`
- `resize-and-state.spec.ts:114 :: state rail->full at width 400 snap-up to 620` — similar pattern
**Categoría:** NEVER self-fix #3 (refactor 2+ archivos, lógica del component) → Caso B spawn dev-team (último intento)

**Root cause (analysis profundo Phase D):**

react-resizable-panels v4 `useDefaultLayout({ id, panelIds, storage })` persiste el layout en localStorage. En hydration, el component lee persisted layout (e.g., `[18, 82]`). Pero el `minSize` del Panel es **calculated dinámicamente** post-mount via `useEffect ResizeObserver`. Race condition:

1. T0: component mounts → Panel renders con persisted layout (e.g., 18%)
2. T0+ε: useEffect ResizeObserver.observe() fires → setContainerWidth(actualWidth) → re-calc minValeriaPct (e.g., 48%)
3. T0+2ε: Panel rerenders con new minSize=48%, BUT current size (18%) NO snap-up al new min

react-resizable-panels v4 NO enforce minSize on persisted layout load. Documentación + GitHub issues confirman: `Panel minSize` solo enforce DURANTE resize interactions; on hydration with smaller persisted value, panel renders below min.

**Fix sugerido:**

Agregar `useImperativePanelGroupHandle` o `useRef<ImperativePanelGroupHandle>` al PanelGroup + useEffect que snap-up post-ResizeObserver:

```tsx
import { useRef, useEffect, ... } from "react";
import { Group, ..., ImperativePanelGroupHandle } from "react-resizable-panels";

// Inside component:
const panelGroupRef = useRef<ImperativePanelGroupHandle>(null);

// Post ResizeObserver settles (containerWidth stable + minValeriaPct calculated):
useEffect(() => {
  if (containerWidth > 0 && panelGroupRef.current) {
    const layout = panelGroupRef.current.getLayout();
    if (layout[0] < minValeriaPct) {
      // Snap-up Valeria al min calculated, App takes remainder
      panelGroupRef.current.setLayout([minValeriaPct, 100 - minValeriaPct]);
    }
  }
}, [containerWidth, minValeriaPct]);

// Pass ref al Group:
<Group ref={panelGroupRef} id={SHELL_GROUP_ID} ...>
```

Esto resuelve:
- F5 (drag below 620 clamped): persisted layout < minValeriaPct → snap-up al hydrate
- F6 (rail->full snap-up to 620): cuando valeriaState cambia full→rail, minValeriaPct sube → snap-up

### Action taken iter 3

1. ✅ Documented F13 verbatim con root cause + fix code
2. ✅ Update audit_iterations: 3 (CAP ABSOLUTO reached after this)
3. → Spawn builder-frontend Caso B FINAL iter

### Cap check

audit_iterations: **3/3 — cap absoluto**. Si esta iter NO converge → ESCALATE Caso D Chris.

---

## ESCALATION — Caso D (audit_iterations 3/3 reached, partial fix)

**Date:** 2026-05-23T17:55:00-05:00
**Commit iter 3 partial:** 46fc8700

### Status final F1-S4 audit

| Metric | Value |
|---|---|
| audit_iterations | 3/3 (cap absoluto) |
| Playwright F1-S4 tests | **33/34 passed** (97% pass rate) |
| Vitest unit + arch | 980/980 ✓ (no regression) |
| gate-output.json | any_fail=false (5/5 native FE gates) |
| auditor-frontend verdict | APPROVED (12/12 categorías) |
| Phase D gherkin matrix | 4 scenarios SC-1..SC-4 mapped → 3 PASS / 1 PARTIAL (SC-3) |

### Único gap residual

**Test:** `resize-and-state.spec.ts:114 :: state rail->full at width 400 snap-up to 620`

**Root cause analysis (builder iter 3 exhaustive):**
Race condition entre 3 mechanismos:
1. `setValeriaStateViaStore("rail")` → `page.evaluate(localStorage.setItem)` + `page.reload()`
2. `dynamic({ssr:false})` lazy-loads `ShellOrganismLayoutClient` post-reload
3. `useDefaultLayout` reads localStorage layout PRE-mount; Panel initial minSize based on persisted `valeriaState="rail"` (~28%)
4. Test fires `dragResizeHandle(-300)` antes que Fix A useEffect dispare snap-up

Builder analizó deep dive + minified code react-resizable-panels v4 dist/ y concluded que requiere refactor del lifecycle hydration: Panel debe waitForReady o equivalente antes de aceptar drag interaction. Fuera del scope T-7 Fase 7A+7B y de iter 3 self-fix.

### Decisión propuesta /pm-vitalia

3 paths posibles:
- (A) Accept 33/34 + spec amendment SC-3 final assertion (test rail->full snap-up es nice-to-have, current behavior es persisted layout wins on hydration)
- (B) Split into F1-S4b follow-up story: "race-condition refactor lifecycle Panel hydration" — pequeña, autoreferenciada
- (C) Block merge hasta refactor complete (riesgo: block dev de F1-S5..S10 que dependen del shell)

Recomendación auditor: **opción A o B**. 1 test que verifica edge-case rail→full→drag-immediately race no es blocker para merge cuando 33/34 + audit-frontend APPROVED + Phase D matrix dice 3/4 SC pass + visual goldens locked.

---
