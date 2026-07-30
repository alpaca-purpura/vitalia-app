---
brand: platform
date: 2026-06-03
slug: e2e-seeded-state-masks-cold-start
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
tags: [e2e, playwright, verification, cold-start, storageState, seeded-state, real-backend, false-green, dod-37, tenant-switcher]
origen: "story vitalia-bugfix-shell-nav-scroll-errors bug#2 · 2026-06-03"
ratified_by: chris
---

# Un e2e "real-backend" NO es honesto si depende de estado sembrado (cold-start masking)

## Qué aprendimos

Refactorizar un e2e de *hybrid-mock* a *real-backend* (forwardear `/api/v1/**` al BE real,
no mockear el surface bajo prueba) **NO lo hace automáticamente honesto**. Si el test depende
de **estado persistido sembrado** —`storageState` de Clerk, `localStorage` (ej. `activeTenant`),
una cookie, un seed— puede pasar **sin ejercer el cold-start** que pega al endpoint real → y
así **enmascara un contrato roto** que SÍ rompe la experiencia del usuario nuevo.

**Caso bug#2 (vitalia):** el e2e del selector de tenant pasaba (`tenant-switcher-trigger`
visible) porque el `storageState` sembraba un `activeTenant` → el shell lo restauraba y el
selector aparecía. Pero en **cold-start real** (usuario fresco, sin estado persistido) el shell
llamaba a `useTenants` → `GET /api/tenants` → **404** (el path no existe en el BE; el real es
`/api/v1/iam/users/me/tenants`) → lista vacía → **selector oculto**. El e2e "real-backend" lo
tapó porque nunca ejerció el fetch en frío. Es la **2da vez** que la trampa muerde (1ra:
lisa-marca, e2e que mockeaba el backend — `[[verification-real-not-200]]`).

## El bar (extiende verificación-real-≠-200)

`GET 200` ≠ verificado · e2e que **mockea** el surface ≠ verificado · **y ahora:** e2e
**real-backend que depende de estado sembrado** ≠ verificado para el camino cold-start.

Para UI cuya **visibilidad o datos dependen de estado persistido** (tenant switcher, shell
mode, vista auth-derived, cualquier store con `persist`), el e2e DEBE incluir una variante
**cold-start**: limpiar el estado persistido ANTES de navegar y assertar que el **fetch real
lo repuebla**.

```ts
test("cold-start → el fetch real puebla la UI", async ({ page }) => {
  await page.addInitScript(() => {
    try { localStorage.removeItem("vitalia-tenant-state"); } catch {}  // borra el estado sembrado
  });
  await page.goto(`/${TENANT_ID}/ruta-limpia`);   // ruta sin /api 4xx propios → gate anti-burbuja ON
  await expect(page.getByTestId("tenant-switcher-trigger")).toBeVisible();  // solo pasa si el fetch real funcionó
});
```

Si el endpoint regresa al path roto → el selector queda oculto → el test **FALLA** (la señal
que el e2e con estado sembrado no daba).

## Cómo se cazó (y la regla operativa)

Lo cazó la **live-verify en dev-app** (browser fresco, sin estado sembrado) — NO la suite
verde. **Regla:** para toda story con UI dependiente de estado, la live-verify de DoD #37
debe ejercer el **cold-start** (limpiar `localStorage`/`storageState` o usar contexto/incógnito
fresco), no solo el warm path. Y el e2e persistido debe tener su variante cold-start.

## Aplicación cross-brand

Aplica a cualquier brand con stores `persist` que gobiernen render (todas las que adoptan el
shell Luana). Auditor: al revisar un e2e de UI estado-dependiente, verificar que exista la
variante cold-start; si solo hay warm path → sospechar masking.

## Referencias

- Caso origen: `vitalia/docs/archive/2026/stories/vitalia-bugfix-shell-nav-scroll-errors/` (07-merge § Corrección root-cause bug#2)
- Fix: `vitalia/frontend/src/hooks/useTenants.ts` (→ `/me/tenants`) + `e2e/regression/shell-nav-scroll/bug2-tenant-selector-visible.spec.ts` (cold-start)
- Extiende: `[[verification-real-not-200]]` · `.claude/rules/definition-of-done-live-verify.md` · `.claude/rules/test-design-doctrine.md`
- Relacionado: `[[next16-softnav-redirect-rendered-more-hooks]]` (misma sesión; ambos los cazó la live-verify, no el verde)
