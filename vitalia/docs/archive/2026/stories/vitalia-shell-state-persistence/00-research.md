# 00-research — shell-store persistence + mobile drawer

> Diagnóstico recogido en la sesión 2026-05-28 (origen `vitalia-fase1-shell-layout-5050-race-fix`).
> El root cause de alto nivel está claro; el write espurio exacto NO está pinpointeado al 100%.
> **Leer esto antes de tocar código** — evita repetir ~10 iteraciones de fix fallido.

## Bug #1 — Persistencia del shell-store NO sobrevive reload (PROD REAL)

### Síntoma reproducible
Usuario setea `valeriaState='rail'` vía el store (shortcut `r` / botón rail) →
`localStorage['vitalia-shell-state'] = {valeriaState:'rail', shellMode:'agentic'}` ✓
→ **recarga** → `localStorage = {valeriaState:'full', shellMode:'agentic'}` ❌.
La preferencia se pierde. Confirmado vía store (no solo localStorage directo) — es
**bug de producción**, no artefacto del test.

### Lo que SÍ funciona
- Runtime: `setValeriaState`/`setShellMode` escriben localStorage correctamente.
- En frío sin SSR involvement el valor estaría bien.

### Root cause (alto nivel, confirmado)
- El store (`src/stores/shell-store.ts`, Zustand 5 + `persist` + `createJSONStorage(localStorage)`)
  se evalúa **también server-side**: `TopBarGlobal` (consumer del store) se renderiza
  dentro del **skeleton SSR** de `ShellOrganismLayout` (que NO es `ssr:false` — solo
  `ShellOrganismLayoutClient` lo es).
- Bajo SSR + `dynamic({ssr:false})`, la auto-hidratación de `persist` produce un
  **hydration mismatch**: el store se asienta en el slice DEFAULT (`full/agentic`) y
  `persist` lo escribe a localStorage, **pisando** el valor guardado del usuario en
  cada reload.

### Evidencia clave (probes deterministas)
- `compareDocumentPosition`, tabIndex, etc. → el DOM/orden están bien (eso es el bug a11y, OTRO tema; ya resuelto).
- Diag "real-user": set rail vía store → `lsAfterSet=rail`, tras reload `lsAfterReload=full`.
- Con instrumentación (`onRehydrateStorage` + log en module-eval/Client effect): al
  momento en que el rehydrate corre, `localStorage` **ya es `full`** — algo lo escribió
  ANTES, entre el reload y el primer effect del Client. **No se pinpointeó qué write
  exacto** (no es el D2 con guard, no es useViewportGuard a 1280, no es TopBarGlobal —
  solo escribe en onClick). Sospecha: el propio ciclo de auto-hydration/persist de
  Zustand bajo SSR + StrictMode double-invoke.

### Técnicas probadas que NO convergieron (NO repetir tal cual)
1. `skipHydration: true` + `void persist.rehydrate()` **a module-level** → el rehydrate
   es async (microtask) y lee localStorage YA pisado a `full`.
2. `skipHydration: true` + `rehydrate()` en **useEffect del Client** (client-only) →
   igual: al correr, localStorage ya es `full` (write espurio lo precede). StrictMode
   dispara el effect 2×.
3. Guard en el efecto D2 de `ValeriaSidebar` (`if shellMode !== target`) para evitar el
   write redundante de mount → necesario pero NO suficiente solo.
4. Combinaciones de los anteriores + restart de container limpio (descartado HMR stale).

### Enfoque sugerido para el fix (no probado aún)
- **Opción A (atacar la raíz):** sacar el store del path SSR — que el skeleton NO use
  `useShellStore` (TopBarGlobal placeholder sin store en el skeleton, o skeleton sin
  TopBarGlobal). Así el store solo se evalúa client-side (en el Client ssr:false) y
  auto-hidrata limpio sin mismatch. Verificar que no rompe el render inicial.
- **Opción B:** custom storage wrapper que NO escriba (`setItem` no-op) hasta que un
  flag `hydrated` sea true (set tras `rehydrate()` client). Robusto pero más código.
- **Opción C:** investigar el write espurio exacto con un breakpoint/trace fino en el
  persist middleware de Zustand 5 (el mecanismo no se pinpointeó por iteración).
- **TDD:** agregar **unit tests vitest** del store hydration (mock localStorage + SSR
  flag) además del E2E — el E2E solo es lento para iterar este timing.

## Bug #2 — Drawer mobile auto-abre (acoplado a #1)

- `ValeriaSidebar` renderiza el drawer cuando `isMobile && isExpanded`
  (`isExpanded = safeState !== 'collapsed'`). Con default `full` (siempre, por #1) y
  viewport <768, el drawer se monta ABIERTO al cargar.
- `useViewportGuard` solo fuerza `full→rail` en `[768,1104)`; NO cubre `<768`.
- **Decisión UX requerida:** en mobile el shell debería arrancar `collapsed` (drawer
  cerrado; burger abre). Fix candidato: extender `useViewportGuard` para `<768` →
  forzar `collapsed` al montar (one-way, análogo al guard existente). Esto también
  desacopla del #1 (mobile no dependería del default `full`).
- Test de regresión: `mobile-collapse.spec.ts` → `ValeriaSlot oculto mobile`.

## Archivos involucrados
- `vitalia/frontend/src/stores/shell-store.ts` (persist config)
- `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx` (skeleton SSR)
- `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` (client mount)
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` (D2 effect + drawer)
- `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts` (mobile guard)
- `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` (store consumer en skeleton)
