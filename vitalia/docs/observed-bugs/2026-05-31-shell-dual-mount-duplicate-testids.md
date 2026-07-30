# Observed bug — shell-organism monta el panel-content 2× → testids duplicados

**Fecha:** 2026-05-31
**Origen:** live-verify de `vitalia-fase2-lisa-doctores` (Playwright contra backend real, stack dev-app)
**Severidad:** media (no rompe UX visible; rompe E2E browser por strict-mode + huele a a11y/perf)
**Estado:** observado, no parcheado

## Síntoma

Al correr los specs E2E de doctores contra el stack real (sesión Clerk + storageState),
cada `getByTestId(...)` del contenido del panel resuelve a **2 elementos** → Playwright
strict-mode violation. Ejemplo verbatim:

```
strict mode violation: getByTestId('btn-nuevo-integrante') resolved to 2 elements:
  1) ... aka getByTestId('app-panel').getByTestId('btn-nuevo-integrante')
  2) ... aka getByTestId('btn-nuevo-integrante').nth(1)
```

Lo mismo aplicaría a `staff-directory`, `staff-card-*`, `staff-pagination`, etc.

## Causa raíz (hipótesis fuerte)

`ShellOrganismLayout` renderiza el `children` (el contenido de la sub-tab) en **dos ramas**:
una para layout mobile y otra para desktop. Ambas quedan en el DOM; una se oculta por CSS
(la otra es la visible según viewport). Evidencia: `ShellOrganismLayout.test.tsx` usa
`getAllByTestId("app-panel-slot")` (plural) en la rama mobile + `AppPanelSlot.tsx` testid
`app-panel-slot`.

Consecuencia: todo `data-testid` dentro del panel existe 2× en el DOM. Para el usuario es
invisible (solo ve la rama visible), pero:
- Rompe E2E con strict-mode (hay que `.filter({ visible: true })` o scopear al panel visible).
- Es un smell de a11y (elementos interactivos duplicados en el árbol) y de perf (doble montaje
  + posible doble fetch de los hooks de datos de cada rama).

## Impacto

- **E2E doctores:** los 10 specs (~38 tests) no pueden ir verde sin scopear los POMs
  (`StaffDirectoryPage`, `DoctorWorkspacePage`, `AvailabilityCalendarPage`) al panel visible.
- **No es bug de producto** funcional: la UI renderiza y funciona (verificado live: directorio
  con 3 doctores seed reales + botón "Nuevo integrante" + búsqueda + lista).

## ★ CAUSA RAÍZ CONFIRMADA (2026-05-31): "Triple-main pattern" deliberado

`ShellOrganismLayoutClient.tsx` (líneas 24-27 doc + 196-274) implementa a propósito el
**"Triple-main pattern"**: TRES elementos `<main id="main-content">` mutuamente excluyentes
por CSS Tailwind:
1. Agentic desktop — `shellMode === 'agentic' && ... hidden md:block` (resizable panels)
2. Web desktop — `shellMode === 'web' && ... hidden md:grid` (grid estático)
3. Mobile fallback — `... md:hidden` (single-column) — **SIEMPRE en el DOM**

`shellMode` es agentic XOR web (una de 1/2 renderiza), pero la rama **mobile (3) SIEMPRE
se monta** (solo oculta por CSS en desktop). → en desktop hay **2 `<AppPanelSlot>` montados**
(la desktop visible + la mobile oculta) → cada `data-testid` del panel existe 2× + **`id="main-content"`
duplicado en 3 elementos (HTML inválido / a11y)**.

**Esto NO es accidente — es un patrón con tests que lo asertan** (`ShellOrganismLayout.test.tsx`
SC-1/SC-2/SC-4: "all 3 main branches have id='main-content'", "triple-main: appears in both
desktop+mobile branches", `getAllByTestId` plural). Por eso fixearlo = **cambio de arquitectura**,
no un parche.

## Fix de producción (diseño — requiere /architect + re-verificación transversal)

**Approach:** reemplazar el CSS-mutuamente-exclusivo por **render condicional por viewport** (JS),
de modo que SOLO una rama exista en el DOM:
1. Usar `useMediaQuery("(min-width: 768px)")` (`src/hooks/useMediaQuery.ts`) → `isDesktop`.
   - ⚠️ El hook inicializa en `false` (useEffect) → causaría **flash mobile→desktop** + montaría
     los resizable panels tarde. Fix: lazy synchronous initializer
     (`useState(() => typeof window !== 'undefined' && window.matchMedia(query).matches)`) — seguro
     porque el shell es `dynamic({ssr:false})` (client-only). Cambio backward-compatible para los
     otros consumers (ValeriaSidebar, mateo/AppointmentDrawer).
2. Render: `isDesktop ? (shellMode === 'agentic' ? <AgenticMain/> : <WebMain/>) : <MobileMain/>` —
   NUNCA ambas. Un solo `<main id="main-content">` a la vez (resuelve también el id duplicado).
3. **Tests a reescribir** (asertan el triple-main): `ShellOrganismLayout.test.tsx`
   (SC-1/SC-2/SC-4 + "passes children to AppPanelSlot triple-main") + posible mock de
   `window.matchMedia` en jsdom (hoy no se usa en el layout → habrá que mockearlo en el setup).
4. **Re-verificación transversal OBLIGATORIA** (es shell compartido): los 5 agentes
   (lisa/mateo/adrian/lucas/camila) + valeria en los 3 modos (agentic/web/mobile) — vitest shell
   + axe wcag2aa + visual smoke. Un error rompe la UI de TODOS los agentes.

**Costo/riesgo:** medio-alto (transversal). Recomendado: story dedicada `/architect` →
`/dev-team` → re-verificación full, NO un edit apresurado. El harness scoping (`.filter({visible:true})`,
ya aplicado en los POMs de doctores, commit b3730693) es el workaround temporal mientras tanto.

## Relacionado

- `vitalia/docs/observed-bugs/2026-05-31-zustand-workspace-resolution-luana-hooks.md`
- Story harness mirror: `estabilizar-harness-e2e-lisa-marca` (mismo patrón para marca)
- `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/06-audit/CHECKPOINTS.md` (C2: browser-E2E pendiente)
