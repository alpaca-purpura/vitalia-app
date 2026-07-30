---
brand: vitalia
date: 2026-05-23
slug: shell-layout-race-condition-defer
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, fitflow, saasora]
target_core_package: core/luana-core-platform (suggestion — shell-organism convenience helper podría vivir en platform package)
---

# Shell layout hydration race condition — pattern + deferred fix

## Qué aprendimos

Cuando construís un shell-organism que combina:
- **`next/dynamic({ssr:false})`** lazy-load del componente layout client-only (workaround SSR crash en libraries que usan `localStorage` en default params, ej. react-resizable-panels v4)
- **Persist library** (e.g., `useDefaultLayout` de react-resizable-panels v4) que restora layout desde localStorage on hydration
- **Dynamic minSize** calculated post-mount via `useEffect ResizeObserver` (ej. para mantener pixel minimums en layout responsive)

Hay una **race condition** entre los 3 mecanismos:

1. **T0** — componente mounts. Panel renders con `minSize="0%"` o un placeholder default (container width=0 inicial)
2. **T0+ε** — persist library lee localStorage → restora layout previo (e.g., `[18, 82]` si user había draggeado before)
3. **T0+2ε** — `useEffect ResizeObserver.observe()` fires → setContainerWidth(actualWidth) → minSize recalculated (e.g., `"48.4%"`)
4. **T0+3ε** — Panel rerenders con new minSize, PERO current size persisted (18%) NO snap-up al new min

react-resizable-panels v4 documentación + GitHub issues confirman: `Panel.minSize` solo enforce **durante** resize interactions (drag/touch). On hydration con persisted value smaller que minSize, panel renders below min silently.

### Fix parcial implementado

En F1-S4 commit `46fc8700` agregamos `useGroupRef` Fix A:

```tsx
import { useGroupRef } from "react-resizable-panels";

const groupRef = useGroupRef();

useEffect(() => {
  if (containerWidth <= 0 || !groupRef.current) return;
  const layout = groupRef.current.getLayout();
  const valeriaPct = layout[VALERIA_PANEL_ID];
  if (valeriaPct !== undefined && valeriaPct < minValeriaPct) {
    groupRef.current.setLayout({
      [VALERIA_PANEL_ID]: minValeriaPct,
      [APP_PANEL_ID]: 100 - minValeriaPct,
    });
  }
}, [containerWidth, minValeriaPct, groupRef]);
```

Esto resuelve el caso **drag-clamp** (persisted layout < new min on hydration → snap-up imperativo).

### Gap residual DEFERRED

Edge case **transition + drag inmediato**: `setValeriaStateViaStore('rail')→reload→setValeriaStateViaStore('full')→reload→drag` antes que Fix A useEffect dispare. Race entre `page.reload()` finish + dynamic chunk load + Panel mount + ResizeObserver fire + Fix A snap-up vs test command `dragResizeHandle`.

Fix completo requiere refactor del lifecycle hydration: Panel debería waitForReady o equivalente antes de accept drag interaction (block pointer events hasta `containerWidth > 0 && minSize calculated`).

**DEFERRED a F1-S5/S6 lifecycle work** — cuando refactor el conversational shell tocará el área natural.

## Origen

Story `vitalia-fase1-shell-layout-5050` Fase 7A + Fase 7B audit cycle (commits c1925563 + cbb4af74 + 46fc8700). 3 audit iterations (cap absoluto 3/3). Final verdict APPROVED-WITH-DEFER 33/34 Playwright tests (97% pass rate). Chris ratificó accept-with-defer 2026-05-23 PM.

## Why (rationale)

El paradigm Next.js 16 + React Server Components encouraging dynamic({ssr:false}) para components con localStorage dependencies. Cualquier brand con shell agéntico similar enfrentará este timing si combina los 3 mecanismos.

Lessons:
- **Document race condition** explícitamente cuando combinés persist library + ResizeObserver + dynamic({ssr:false}).
- **Imperative snap-up (Fix A)** resuelve la mayoría de casos but NO transitions + immediate user interaction.
- **Test isolation** (Playwright `page.reload()` + drag inmediato) expone race condition que en uso real probablemente no aparezca (humans toman > 100ms entre reload + drag).
- **Cap audit iterations 3/3** funcionó como circuit-breaker — saved Chris de debugging spiral 4+ hours.

## How to apply

Si construís un shell-organism o cualquier layout que combina los 3 patterns:

1. **Document timing** en doc-string del component layout (race condition + Fix A approach)
2. **Implement Fix A** (useGroupRef o equivalent imperative ref) post-ResizeObserver
3. **Test edge cases** transition + immediate user interaction — si race aparece, marca DEFERRED en spec con plan refactor para futuro
4. **Cap audit iterations** en 3 max para evitar over-engineering (per `.claude/rules/auditor-self-fix-policy.md`)
5. **Splittear story** F1-S{N}b follow-up state=parked para tracking del gap residual sin bloquear merge

## Cross-brand applicability

- **Nicolify** — Si construyen shell-organism similar para CRM B2B con split persist
- **Comunify** — Creator Economy shell con sidebar history persist
- **Lupulo** — KDS layout potencialmente con persist
- **Fitflow** — Gym booking shell con sidebar persist
- **SaaSora** — Productized SaaS shells multi-panel

Patrón canónico podría vivir en `core/luana-core-platform/src/luana_core_platform/frontend/hooks/usePersistentLayoutWithSnapUp.ts` (TypeScript) — promotable candidate.

**Ping `/pm-luana`:** evaluar lift cuando 2da brand encuentre mismo problema (yagni hasta proof of cross-brand need).

## Tracking

- F1-S4 audit final: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/T-7-review.md` § Audit iteration 3 + ESCALATION block
- F1-S4b follow-up: `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050-race-fix/checkpoint.md` (state=parked)
- Promotion candidate scan: `make scan-promotables` periódico (cada Mon /pm-luana)
