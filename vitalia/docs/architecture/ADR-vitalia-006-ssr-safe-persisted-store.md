<!-- voseo-allowed: internal ADR, not user-facing -->

# ADR-vitalia-006 — SSR-safe Persisted Store (Zustand 5 + Next.js 16 App Router)

| Campo | Valor |
|---|---|
| **Status** | Proposed (v1.0 — 2026-05-29) |
| **Date** | 2026-05-29 |
| **Authors** | Chris + `/architect` (orchestrator Opus 4.8) |
| **Brand** | vitalia (patrón aplicable a otras brands vía promotion gate `/pm-luana`) |
| **Scope** | Todo store Zustand con `persist` bajo Next.js 16 App Router en `vitalia/frontend/` (4 stores actuales + futuros) |
| **Supersedes** | — (complementa ADR-vitalia-004 shell-feature-architecture; ADR-004 NO cubre persistencia-bajo-SSR → gap) |
| **Sources** | Story `vitalia-shell-state-persistence` (`01-spec.md`, `00-research.md` root cause + 4 técnicas fallidas); WebSearch Zustand persist + Next.js hydration (accessed 2026-05-29); código real `shell-store.ts` + `ShellOrganismLayout.tsx` |
| **Knowledge cutoff note** | Opus 4.8 cutoff Jan 2026; el patrón Zustand 5 `skipHydration` + `_hasHydrated` se validó live vía WebSearch 2026-05-29 (estado del arte vigente). |

---

## § 1 — Context

Vitalia es la única brand activa (al 2026-05-29) que usa `zustand/middleware persist`. Tiene
**4 stores persistidos**: `shell-store`, `tenant-store`, `agenda-store`, `agenda-filters-store`.

La story `vitalia-shell-state-persistence` confirmó un **bug de producción real**: `valeriaState`/
`shellMode` NO sobreviven al reload. El store auto-hidrata contra el default (`full/agentic`) y
**pisa `localStorage`** en cada carga.

**Causa raíz (pinpointeada):** `ShellOrganismLayout.tsx` es `"use client"` y su skeleton SSR/
`loading` (`ShellOrganismLayoutSkeleton`) renderiza `<TopBarGlobal/>`, que suscribe `useShellStore`.
El `dynamic({ssr:false})` envuelve SOLO a `ShellOrganismLayoutClient` — el skeleton queda **fuera**
de ese boundary. El middleware `persist` se evalúa en server-render + ventana pre-hidratación del
skeleton, auto-hidrata contra el default y lo reescribe a `localStorage`, clobbering la preferencia.

**4 técnicas que NO convergieron** (documentadas en `00-research.md`):
1. `skipHydration:true` + `rehydrate()` a module-level (async → lee localStorage ya pisado).
2. `skipHydration:true` + `rehydrate()` en `useEffect` Client solo (write espurio lo precede; StrictMode 2×).
3. Guard en efecto D2 de `ValeriaSidebar` solo (necesario, no suficiente).
4. Combinaciones + restart container.

**Por qué ninguna funcionó:** todas dependían del *timing* del `rehydrate()` pero dejaban `setItem`
activo. El ciclo `persist` escribía el default ANTES de que el rehydrate corriera. El hazard es
**transversal** (cualquiera de los 4 stores puede sufrirlo si un consumer lo suscribe en un path SSR)
y ADR-vitalia-004 (sub-tab pattern) NO lo cubre.

---

## § 2 — Decision

Todo store Zustand con `persist` en `vitalia/frontend/` **MUST** crearse vía el factory
`createSsrSafePersistedStore` (`vitalia/frontend/src/lib/store/`), que combina **defensa en
profundidad** de dos mecanismos:

### Mecanismo A (surgical) — el store NUNCA se evalúa en el skeleton SSR

El skeleton/`loading` de cualquier `dynamic({ssr:false})` NO debe suscribir un persisted store.
Para el shell: `TopBarGlobal` recibe `variant: "interactive" | "skeleton"` (default `interactive`);
en `variant="skeleton"` no suscribe `useShellStore` (burger inerte). El skeleton pasa `"skeleton"`.

### Mecanismo B (factory) — el `persist` es write-safe hasta rehidratar client-side

`createSsrSafePersistedStore` aplica:
1. **`skipHydration: true`** — sin auto-hydrate en module-eval.
2. **Storage `setItem` NO-OP pre-hydration** — `ssrSafeStorage(getHydrated)` envuelve
   `createJSONStorage`; `setItem` es no-op mientras `_hasHydrated === false`. `getItem`/`removeItem`
   pasan derecho. Esto neutraliza el write espurio aunque el store se evalúe en SSR/skeleton/
   StrictMode-double-invoke — **independiente del timing**, que es la pieza que faltaba.
3. **`_hasHydrated` flag + `onRehydrateStorage`** — el hook `useStoreHydration(store)` llama
   `store.persist.rehydrate()` UNA vez client-side (idempotente, ref-guard StrictMode); el callback
   flipea `_hasHydrated = true`. A partir de ahí `setItem` escribe normal.

El `rehydrate()` se dispara DENTRO del chunk `ssr:false` (shell: desde `ShellOrganismLayoutClient`;
otros stores: primer Client Component consumer). NUNCA a module-level.

### Slice independiente para estado responsive-sensible

Estado que depende del viewport (ej. drawer mobile abierto/cerrado) MUST persistir en un slice
**independiente** del estado desktop equivalente. En shell-store: `mobileDrawerOpen: boolean`
(default `false`), separado de `valeriaState`. Razón: una preferencia desktop (`full`) NUNCA debe
traducirse en comportamiento mobile (auto-open drawer).

---

## § 3 — Patrón cementado (contrato)

```ts
// lib/store/create-ssr-safe-persisted-store.ts
export interface SsrSafeHydration {
  _hasHydrated: boolean;
  setHasHydrated: (v: boolean) => void;
}
export function createSsrSafePersistedStore<T extends SsrSafeHydration>(
  initializer: StateCreator<T>,
  options: PersistOptions<T, Partial<T>>,   // name, partialize, version
): UseBoundStore<...>;   // skipHydration:true + ssrSafeStorage + onRehydrateStorage→setHasHydrated(true)

// lib/store/use-store-hydration.ts
export function useStoreHydration(store: { persist: { rehydrate: () => void } }): void; // idempotente
```

**Reglas duras:**
- `lib/store/` (capa `lib` FSD) — importable por `stores/` y `features/*/store/`. NUNCA en `components/`.
- Skeleton de cualquier `dynamic({ssr:false})` = store-free.
- `rehydrate()` solo client-side, dentro del boundary `ssr:false`, vía `useStoreHydration`.
- Estado viewport-sensible → slice independiente.

---

## § 4 — Consequences

**Positivas:**
- El clobber del default no puede ocurrir (setItem no-op pre-hydration corta el write en la raíz).
- Patrón transversal cementado → cero re-discovery por store nuevo.
- Defensa en profundidad: aunque un futuro consumer suscriba un persisted store en un path SSR, el factory lo protege.

**Negativas / tradeoffs:**
- Más código que `persist` raw (factory + hook + flag por store).
- Refactor de los 4 stores existentes a la convención.
- `react-resizable-panels` v4 sigue forzando `dynamic({ssr:false})` (bare-name localStorage) — el ADR opera SOBRE ese boundary, no lo elimina.

**Anti-patterns prohibidos (verbatim — las 4 técnicas fallidas):**
- ❌ `rehydrate()` a module-level.
- ❌ `rehydrate()` en `useEffect` Client sin no-op de setItem.
- ❌ Guard de efecto en componente como único fix.
- ❌ Drawer mobile derivado del estado desktop (slices acoplados).

---

## § 5 — Cross-brand lift candidate

`nicolify/frontend/src/features/notifications/store/dismiss-store.ts` también usa `persist` raw →
mismo hazard latente. El patrón es transversal a futuros brand frontends (Next 16 + Zustand 5).
**Lift candidate `/pm-luana`** a `core/@luana/hooks` (o similar). NO se mirror cross-brand en esta
story (fix vitalia-local); se captura learning `promotable: candidate` al merge.

---

## § 6 — Status / next

- **Proposed.** Se cementa a `Accepted` cuando `vitalia-shell-state-persistence` mergea a `done`
  con los 4 stores migrados + tests verdes (8 scenarios SC-1..SC-8 + SC-5b).
- Enforcement futuro: arch fitness test `test_persisted_store_uses_factory.test.ts` (todo `persist(`
  bajo `vitalia/frontend/src/` debe venir del factory) — TBD post-merge.

---

## § 7 — References

- `vitalia/docs/product/stories/vitalia-shell-state-persistence/{01-spec,03-arch,00-research}.md`
- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` (complementario)
- WebSearch "zustand v5 persist skipHydration Next.js App Router hydration" — accessed 2026-05-29
- `.claude/rules/frontend-fsd.md` · `.claude/rules/anti-duplication.md`
