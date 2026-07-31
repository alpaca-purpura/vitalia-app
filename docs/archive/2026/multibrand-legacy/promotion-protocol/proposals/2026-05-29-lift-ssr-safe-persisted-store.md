---
proposal_id: 2026-05-29-lift-ssr-safe-persisted-store
state: migrated                  # proposed | under_review | accepted | rejected | migrated
opened_date: 2026-05-29
opened_by: /pm-luana
ratified_by: chris               # APPROVED 2026-05-29
ratified_date: 2026-05-29
migrated_date: 2026-05-29
migrated_commit: cf19d1f5
target_version: "@luana/hooks@0.2.0"

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-28-ssr-safe-zustand-persist.md

origin_brands: [vitalia]         # vitalia implementó el factory; nicolify tiene el hazard latente sin fix

# Target
target_package: core/@luana/hooks         # TS/FE — React/Zustand store helpers
target_module: src/store/                  # createSsrSafePersistedStore + useStoreHydration
target_ep: null

# Impact assessment
semver_bump: minor               # nuevo export opcional, opt-in
breaking_change: false
brands_affected_consumers: [vitalia, nicolify]   # vitalia migra (origen); nicolify opt-in
brands_at_risk_regression: [vitalia]             # vitalia tiene tests downstream del factory
# nicolify NO está en riesgo: hoy usa persist raw; el opt-in es voluntario

# Lift plan
lift_estimated_effort: "0.5-1 day"
lift_owner: /dev-team (worktree core lift wip/core-ssr-safe-persist)
arch_test_downstream_required: true
migration_notes_required: false
---

## 1. Patrón a promover

`createSsrSafePersistedStore` — factory que envuelve Zustand 5 `persist` para hacerlo **seguro bajo
Next 16 App Router SSR/hydration**. Tres propiedades: (1) `skipHydration: true`; (2) un storage wrapper
cuyo `setItem` es **NO-OP mientras `_hasHydrated === false`** (getItem/removeItem passthrough) —
neutraliza el write espurio del default durante SSR/skeleton/StrictMode-double-invoke; (3) `_hasHydrated`
flag + `onRehydrateStorage` + hook `useStoreHydration(store)` que dispara el rehydrate client-side una vez.

**Problema que resuelve:** un store `persist` evaluado en un contexto SSR/skeleton (consumer dentro del
`loading` de un `dynamic({ssr:false})`) auto-hidrata contra el default y **reescribe localStorage**,
pisando la preferencia del usuario en cada reload. El `setItem` no-op corta ese write en la raíz,
independiente del timing — la pieza que ~10 iteraciones de técnicas estándar (rehydrate module-level /
useEffect / guards) NO lograron.

**Origen story:**
- vitalia: [[vitalia-shell-state-persistence]] — `vitalia/docs/archive/2026/stories/vitalia-shell-state-persistence/` (state=done 2026-05-28, ADR-vitalia-006). Factory + hook en `vitalia/frontend/src/lib/store/`.

## 2. Por qué cross-brand

Todo brand frontend es **Next 16 App Router + Zustand**. Cualquier store `persist` consumido en un path
SSR/skeleton es vulnerable al mismo clobber. No es vertical-specific — es infra FE transversal.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya implementa (origen) | 4 stores persist migrados al factory · bug real resuelto |
| nicolify | candidato (hazard latente) | `nicolify/frontend/src/features/notifications/store/dismiss-store.ts` usa `persist` raw (sin skipHydration/createJSONStorage). No reporta bug hoy, pero es vulnerable si el consumer entra a un path SSR |
| comunify | candidato futuro | 0 stores persist hoy; cuando agregue UI con prefs persistidas, mismo riesgo |
| lupulo | candidato futuro | idem (placeholder) |

## 3. Análisis técnico

### Signature comparison

```ts
// vitalia HOY (vitalia/frontend/src/lib/store/create-ssr-safe-persisted-store.ts)
export function createSsrSafePersistedStore<T extends SsrSafeHydration>(
  initializer: StateCreator<T>,
  options: PersistOptions<T, Partial<T>>,   // name, partialize, version
): StoreApi<T> & { persist: { rehydrate: () => void } }
export interface SsrSafeHydration { _hasHydrated: boolean; setHasHydrated: (v: boolean) => void; }
// + use-store-hydration.ts: useStoreHydration(store) idempotente (ref-guard StrictMode)

// nicolify HOY (dismiss-store.ts) — persist raw, vulnerable
export const useDismissStore = create<DismissState>()(persist((set,get)=>({...}), { name: "notifications-dismiss" }));

// Propuesta core (core/@luana/hooks/src/store/create-ssr-safe-persisted-store.ts)
// IDÉNTICO al de vitalia — el factory ya es brand-agnóstico (cero refs hardcoded vitalia).
// nicolify opt-in: const useDismissStore = createSsrSafePersistedStore(initializer, { name: "notifications-dismiss" })
```

**Nota clave:** el factory de vitalia **ya es genérico** (no tiene refs hardcoded a vitalia). El lift es
casi un `git mv` + generalizar el import path. Bajo esfuerzo.

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| nicolify opt-in descubre un límite del contract | Baja | Documentar contract en `docs/core-modules/` antes del opt-in; nicolify migra cuando quiera |
| Bump minor + brand sin opt-in → sin cambio | Baja | Default opt-in protege (vitalia migra a consumir el package; los demás siguen igual) |
| vitalia regresa al re-importar desde core | Media | R3: correr la suite FE vitalia (2310 vitest + 28 E2E) tras el swap import |
| `@luana/hooks` no publicado/wired en pnpm workspace para consumir | Media | Verificar `@luana/hooks` exporta + está en `pnpm-workspace.yaml` (ya lo está — es package activo) |

## 4. Lift plan

### Pre-lift checklist
- [ ] Confirmar `@luana/hooks` tiene `src/store/` o crear el subpath + export en su index
- [ ] Tests unitarios (port de `create-ssr-safe-persisted-store.test.ts` de vitalia → `core/@luana/hooks/tests/`)
- [ ] Contract doc en `docs/core-modules/luana-hooks.md` (sección SSR-safe persist)
- [ ] CHANGELOG `@luana/hooks` entry (minor)

### Lift execution (worktree `wip/core-ssr-safe-persist`)
1. `git mv` factory + hook de `vitalia/frontend/src/lib/store/` → `core/@luana/hooks/src/store/` (generalizar import)
2. Export desde `@luana/hooks` index
3. vitalia: re-importar `createSsrSafePersistedStore` + `useStoreHydration` desde `@luana/hooks` (swap 4 stores + lib)
4. Bump `@luana/hooks` package.json minor + CHANGELOG
5. R3 downstream: correr suite FE vitalia completa (vitest + arch + E2E) — todo debe seguir GREEN
6. Rollback: revert lift, vitalia retiene `lib/store/` local

### Post-lift
- vitalia (origen): consume `@luana/hooks` (migración automática, es de donde nació)
- nicolify: opt-in voluntario — swap `dismiss-store` al factory cuando `/pm-nicolify` lo priorice
- comunify/lupulo: opt-in al agregar stores persist

## 5. Decisión

**Recomendación `/pm-luana`: APPROVED.**

**Razón:** patrón genuinamente transversal (infra FE Next+Zustand, no vertical-specific), ≥2 brands con el
hazard (vitalia con bug real resuelto + nicolify latente), factory **ya genérico** (lift de bajo esfuerzo /
bajo riesgo), bump minor opt-in (cero riesgo para brands sin opt-in). El único riesgo material es regresión
en vitalia al re-importar, cubierto por R3 (su suite ya es 2310 vitest + 28 E2E verde). Evita que nicolify
+ futuros brands re-descubran el mismo bug de ~10 iteraciones.

**Ratificación Chris:** _pending — requiere APPROVED explícito antes de pasar a state=accepted + handoff /dev-team._

## 6. Bitácora

- 2026-05-29: opened by /pm-luana (manual, post-merge de vitalia-shell-state-persistence). Scan Step 0.5 confirmó ≥2 brands (vitalia + nicolify).
- 2026-05-29: state proposed → under_review + recomendación APPROVED. Espera ratificación Chris.
- 2026-05-29: Chris APPROVED → state accepted.
- 2026-05-29: lift ejecutado (commit `cf19d1f5`) → state **migrated**. Factory+hook a `@luana/hooks@0.2.0` (subpath exports + peerDep zustand). vitalia migrado a consumir vía workspace:* + subpath. R3 GREEN (vitalia 2296/2296 + @luana/hooks 19/19). Descubrimiento: vitalia NO tenía wiring `@luana/*` previo → se estableció (1er consumer @luana en vitalia). Pendiente opt-in voluntario nicolify (`dismiss-store`) via /pm-nicolify.

## 7. Cross-references

- Origin learning: `vitalia/docs/learnings/2026-05-28-ssr-safe-zustand-persist.md`
- Origin story (archived): `vitalia/docs/archive/2026/stories/vitalia-shell-state-persistence/`
- ADR: `vitalia/docs/architecture/ADR-vitalia-006-ssr-safe-persisted-store.md`
- Target package: `core/@luana/hooks/` (contract doc TBD `docs/core-modules/luana-hooks.md`)
- Consumer latente: `nicolify/frontend/src/features/notifications/store/dismiss-store.ts`
- Process: `docs/promotion-protocol/README.md`
