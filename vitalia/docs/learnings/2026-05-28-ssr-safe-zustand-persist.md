---
title: "SSR-safe Zustand persist (Next 16 App Router) — setItem no-op pre-hydration"
date: 2026-05-28
type: technical
brand: vitalia
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
target_core_package: core/@luana/hooks (o core/@luana/ui-kit FE)
origen: "story vitalia-shell-state-persistence (fix de vitalia-fase1-shell-layout-5050-race-fix)"
ratified_by: chris
tags: [zustand, persist, ssr, hydration, nextjs, localstorage, clobber, store]
---

# SSR-safe Zustand persist — setItem no-op pre-hydration

## Contexto

El shell de Vitalia perdía las preferencias del usuario (`valeriaState`, `shellMode`) en cada reload.
Un store Zustand 5 con `persist` + `createJSONStorage(localStorage)` se evaluaba en el path SSR/skeleton
(un consumer `TopBarGlobal` vivía dentro del skeleton `loading` de un componente `dynamic({ssr:false})`,
FUERA del boundary `ssr:false`). El ciclo auto-hydrate/persist corría en ese contexto y **reescribía el
default a localStorage**, pisando la preferencia guardada. Falló ~10 iteraciones con técnicas estándar.

## Aprendizaje

Las técnicas habituales NO convergen por sí solas y NO deben repetirse:
1. ❌ `skipHydration:true` + `rehydrate()` a module-level (async → lee localStorage ya pisado).
2. ❌ `skipHydration:true` + `rehydrate()` en `useEffect` client solo (el write espurio lo precede; StrictMode 2×).
3. ❌ Guard en un efecto de mount como único fix.
4. ❌ Combinaciones de lo anterior + restart container.

**La pieza que faltaba (el fix real):** un **storage wrapper cuyo `setItem` es NO-OP mientras
`_hasHydrated === false`** (getItem/removeItem passthrough). Esto corta el write del default EN LA RAÍZ,
independiente del timing del rehydrate, del SSR y del double-invoke de StrictMode. Combinado con:
- `skipHydration: true`,
- `onRehydrateStorage` que flipea `_hasHydrated = true` post-rehidrate client-side,
- un hook `useStoreHydration(store)` idempotente (ref-guard) disparado DENTRO del chunk `ssr:false`,
- y sacar el store del path del skeleton SSR (consumer con `variant="skeleton"` store-free).

## Aplicación práctica

- **Cuándo aplica:** cualquier store Zustand `persist` en Next App Router que pueda evaluarse en un
  contexto SSR/pre-hydration (especialmente si un consumer vive en un skeleton/loading de `dynamic`).
- **Cómo aplica:** factory `createSsrSafePersistedStore(initializer, options)` que envuelve `persist` con
  el `ssrSafeStorage(getHydrated)` no-op + `skipHydration` + `_hasHydrated`/`setHasHydrated` + rehydrate hook.
- **Cuándo NO aplica:** stores no persistidos (sin localStorage) o estado puramente server.

## Ejemplo

`vitalia/frontend/src/lib/store/create-ssr-safe-persisted-store.ts` (factory) +
`vitalia/frontend/src/lib/store/use-store-hydration.ts` (hook). Aplicado a los 4 stores persist de vitalia.

## Lift candidate (→ /pm-luana)

`nicolify/frontend/src/features/notifications/store/dismiss-store.ts` usa `persist` raw con el mismo
hazard latente. El patrón aplica a TODO brand frontend Next 16 + Zustand. **Recomendación:** promover el
factory a `core/@luana/hooks` (o `core/@luana/ui-kit`) vía promotion gate `/pm-luana` para que nicolify +
futuros brands lo consuman por import en vez de re-descubrir el bug.

## Referencias

- [Story](vitalia/docs/archive/2026/stories/vitalia-shell-state-persistence/) (01-spec + 03-arch + 00-research)
- [ADR-vitalia-006](vitalia/docs/architecture/ADR-vitalia-006-ssr-safe-persisted-store.md)
- Caps: `shell-organism.shell-vitalia` (scenarios shell-state-persists-reload + mobile-drawer-collapsed-pero-recuerda)
