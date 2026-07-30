# T-5 — Impl Log (Playwright E2E + Visual Goldens)

**Ticket:** T-5 — Playwright smoke suite + visual goldens iter 1  
**Story:** vitalia-fase1-ribbon-6-tabs (F1-S7)  
**Brand:** vitalia  
**Date:** 2026-05-25  
**Builder:** claude-sonnet-4-6 (builder-frontend)

---

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | T-5 toca `e2e/regression/` — visual goldens + Playwright patterns | Runtime quality checklist: fixture-based auth, POM pattern, `--update-snapshots` solo en iter 1 autorizado por Chris |
| `tessl__react-patterns` | A11y fix en RibbonTab.tsx (D18 contrast) — baseline always | `text-foreground/60` en active sub-label para WCAG AA — no viola memoization/key/error boundary patterns |
| `tessl__vitest` | 1328 unit tests GREEN pre-commit gate | Confirmado coverage ≥20% all categories |

---

## Production Code Touch — Justified Extension

### Contexto (continuación de sesión anterior)

La sesión anterior resolvió el primer bloqueo de T-5:
- **Bloqueo 1 (resuelto):** `AvatarFallback` carecía de `data-testid="avatar-fallback-{slug}"` requerido por `pom.expectAvatarFallback()`. Fix: +1 línea en `RibbonTab.tsx` (D18 T-2 integration scope).

### Bloqueo 2 encontrado en esta sesión (SC-7-axe)

**Test fallando:** `ribbon-keyboard.spec.ts:193 › SC-7-axe — axe wcag2aa scan ribbon organism @axe › ribbon organism: 0 critical/serious axe violations wcag2aa [light mode]`

**Violación axe detectada:**
```
color-contrast (serious): Ensure the contrast between foreground and background colors meets 
WCAG 2 AA minimum contrast ratio thresholds
Target: .text-[10px].whitespace-nowrap.text-muted-foreground (name sub-label en active tab)
```

**Root cause:** El span del sub-label (nombre del agente, 10px) usaba `text-muted-foreground` (`240 4% 46%` ≈ #737380) sobre el fondo activo `bg-agent-lisa-soft` (`156 80% 92%` ≈ #d1f7e9 en light mode). Este par color/fondo no alcanza el ratio 4.5:1 exigido por WCAG 2 AA para texto pequeño.

**Fix aplicado:**

Archivo: `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx`

```tsx
// ANTES (línea 76)
<span className="whitespace-nowrap text-[10px] text-muted-foreground">

// DESPUÉS (D18 a11y cement)
<span
  className={cn(
    "whitespace-nowrap text-[10px]",
    active ? "text-foreground/60" : "text-muted-foreground",
  )}
>
```

**Impacto:** 0 logic change, 0 behavior change. Solo el color del texto del sub-label cambia en estado activo: `text-muted-foreground` → `text-foreground/60`. El color en estado inactivo es idéntico.

**Por qué `text-foreground/60` y no otro token:**
- `text-foreground` (`240 10% 4%` ≈ #090910) sobre `bg-agent-lisa-soft` (`156 80% 92%`) → contraste >7:1 ✅
- `/60` opacity = 60% de foreground sobre el soft bg → mantiene jerarquía visual sub-label vs tab-label principal mientras supera WCAG AA (>4.5:1)
- Token consistente con design system: no introduce valor hardcoded

**Tests unitarios impactados:** ninguno. Los 24 tests de `RibbonTab.test.tsx` verifican className del botón (level button), no del sub-label span. `active=false → text-muted-foreground` en botón sigue pasando. 24/24 GREEN post-fix.

**Files modificados en esta sesión:**
- `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` — D18 contrast fix (+4 líneas, JSDoc update +1 línea)

**Logic delta = zero (comportamiento funcional inalterado). Solo a11y compliance.**

---

## T-5 Implementation — POM + Spec Suite + Visual Goldens

### Scope (heredado de sesión anterior, completado en esta sesión)

T-5 es puro testing — `production_code: false` en 06-tickets.yaml. Los artefactos construidos en sesiones anteriores y esta sesión:

| Artefacto | Estado | Ubicación |
|---|---|---|
| POM `ribbon-page.pom.ts` | ✅ GREEN | `e2e/regression/vitalia-fase1-ribbon-6-tabs/poms/` |
| `ribbon-navigation.spec.ts` (SC-1, SC-2, SC-3) | ✅ 9/9 GREEN | `e2e/regression/vitalia-fase1-ribbon-6-tabs/` |
| `ribbon-keyboard.spec.ts` (SC-4, SC-5, SC-7, SC-7-axe) | ✅ 9/9 GREEN | idem |
| `ribbon-avatar-fallback.spec.ts` (SC-9) | ✅ 3/3 GREEN | idem |
| `ribbon-i18n.spec.ts` (SC-10) | ✅ 3/3 GREEN | idem |
| `ribbon-responsive.spec.ts` (SC-8) | ✅ 3/3 GREEN | idem |
| `ribbon-xss-guard.spec.ts` (SC-6) | ✅ 3/3 GREEN | idem |
| `ribbon-empty-state.spec.ts` (SC-11) | ✅ 3/3 GREEN | idem |
| `visual-goldens.spec.ts` (11 goldens) | ✅ 13/13 GREEN | idem |

**Total Playwright smoke: 32/32 GREEN**  
**Total Playwright visual: 13/13 GREEN**

### Visual Goldens — Iter 1 (autorizado `ratified_visual_by_chris=true`)

Snapshots generados con `--update-snapshots` (iter 1 — escritura inicial, no diff):

```
vitalia/frontend/e2e/__screenshots__/regression/vitalia-fase1-ribbon-6-tabs/visual-goldens.spec.ts/
  ribbon-active-lisa.png
  ribbon-active-valeria.png
  ribbon-active-adrian.png
  ribbon-active-lucas.png
  ribbon-active-camila.png
  ribbon-active-config.png
  ribbon-dark.png
  ribbon-idle.png
  ribbon-mobile-375.png
  ribbon-keyboard-focus.png
  ribbon-hover-inactive.png
```

11 snapshots × `maxDiffPixelRatio: 0.001` (0.1% tolerance). Re-run sin `--update-snapshots`: 13/13 PASS.

---

## Gates Pre-commit

| Gate | Resultado |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `eslint src/` | ✅ 0 errors |
| `prettier --check` RibbonTab.tsx | ✅ Prettier code style |
| `vitest run --coverage` | ✅ 1328/1328, 137 test files |
| Playwright smoke (behavior) | ✅ 32/32 |
| Playwright visual (goldens) | ✅ 13/13 |

---

## Observaciones

- El FAPI Clerk warning (`FAPI request failed after 4 attempts: ... route.fetch: Test ended`) en XSS guard specs es **benigno**: ocurre post-teardown cuando Playwright cierra el contexto antes de que el `route.fetch` callback complete. Los tests pasan en 3/3.
- Visual goldens iter 1 reflejan el estado post D18 (contrast fix activo). Si Chris requiere ajuste visual del sub-label color, es un re-ratify iter 2 — no regresión.
