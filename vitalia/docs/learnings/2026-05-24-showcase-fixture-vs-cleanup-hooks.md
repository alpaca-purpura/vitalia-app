---
brand: vitalia
date: 2026-05-24
slug: showcase-fixture-vs-cleanup-hooks
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: docs/architecture/patterns/test-fixtures.md (pattern doc) o core/luana-core-testing/ (package futuro)
origin_story: vitalia-fase1-valeria-rail-history (F1-S5)
origin_commit: efc0c64b
related_stories:
  - vitalia-fase1-tenant-switcher (F1-S3 — origen del cleanup hook que causa el flash)
  - vitalia-fase1-shell-layout-5050 (F1-S4 — origen del showcase fixture)
related_learnings: [2026-05-24-ui-hit-area-1px-anti-pattern]
---

# Test fixture showcase deben blindarse contra cleanup hooks que asumen production auth

**Qué aprendimos:** una "test page" / "showcase fixture" que pre-hidrata un Zustand store con MOCK data via `useEffect` puede ser **silenciosamente desmontada** por cleanup hooks globales (mounted en root layout) que asumen un flow de auth productivo. El flash visible (data aparece → desaparece) es la huella del race condition entre showcase hydration y global cleanup.

**Origen concreto:** F1-S4 creó `/test-stack/shell-layout` como showcase pública (sin Clerk auth) del shell organism. F1-S3 introdujo `useSignOutCleanup` (mounted en `TenantStoreBootstrap` en root layout) que limpia el tenant-store cuando detecta `isSignedIn === false`. F1-S5 expuso el bug al usar Shell completo en showcase real.

**Sequence del race:**

```
t=0     Page mount, Clerk loading. isSignedIn=undefined → useSignOutCleanup early returns (!isLoaded)
t=50ms  Showcase useEffect: setAvailableTenants(MOCK_TENANTS) + setActiveTenant(MOCK_TENANTS[0]) → TenantSwitcher renderiza ✅
t=500ms Clerk loads. isLoaded=true, isSignedIn=false (route público sin auth)
t=1s    useSignOutCleanup fires: clearStore() → store vacío → TenantSwitcher returns null → trigger DESAPARECE ❌
```

Bug visible solo en testing fixture. PROD con Clerk login real (`isSignedIn=true`) → cleanup nunca corre → store stays hydrated → cero flash.

**Why (causa fundamental):**

- **Test fixtures son simulacros parciales.** Mockean DATA (MOCK_TENANTS) pero NO mockean AUTH STATE. Clerk SDK sigue corriendo real → emite eventos reales → cleanup hooks reaccionan a eventos reales.
- **Cleanup hooks asumen production semantics.** `useSignOutCleanup` fue diseñado para production: "si user sign-out, limpiar tenant data anterior". No consideró que existe un flow donde `isSignedIn=false` es **estado normal permanente** (showcase público).
- **Race condition por orden de mount.** Showcase hidrata ANTES que Clerk termine loading. Cuando Clerk resuelve, el cleanup gana porque el showcase useEffect ya corrió y NO observa cambios subsecuentes.

**How to apply (pattern correcto):**

### Pattern 1 — Auto-rehydrate defensivo en el fixture (lo aplicado en F1-S5)

```tsx
// Showcase page
const availableTenants = useTenantStore((s) => s.availableTenants);

useEffect(() => {
  // Re-hydrate cuando store queda vacío (cleanup hook lo vació)
  if (availableTenants.length === 0) {
    setAvailableTenants(MOCK_TENANTS);
    setActiveTenant(MOCK_TENANTS[0]);
  }
}, [availableTenants, setAvailableTenants, setActiveTenant]);
```

Pros: 1 línea de cambio en el fixture. Cero touch a production code.
Cons: parche reactivo. Si cleanup corre 1000 veces, showcase reacciona 1000 veces.

### Pattern 2 — Flag "test mode" en el store, cleanup hook lo respeta (production change)

```ts
// tenant-store.ts
type State = {
  // ...
  isTestFixtureMode: boolean;
  setTestFixtureMode: (b: boolean) => void;
};

// useSignOutCleanup.ts
useEffect(() => {
  if (!isLoaded) return;
  const { isTestFixtureMode } = useTenantStore.getState();
  if (isSignedIn === false && !isTestFixtureMode) {
    clearStore();
    // ...
  }
}, [isLoaded, isSignedIn]);

// Showcase
useEffect(() => {
  setTestFixtureMode(true);
  setAvailableTenants(MOCK_TENANTS);
  return () => setTestFixtureMode(false);
}, []);
```

Pros: idempotente, intención explícita. Cleanup hook auto-documenta excepción.
Cons: production code modificado para satisfacer fixture (anti-pattern moderado).

### Pattern 3 — Showcase mockea Clerk SDK (más complejo)

Pre-mount un mock provider de Clerk que reporte `isSignedIn=true` con user mock. Bypass total del cleanup porque condición nunca se cumple.

Pros: el más "correcto" arquitectónicamente — el fixture imita PROD completamente.
Cons: requiere mock provider package, cross-cuts varios files, lock-in con Clerk SDK internals que pueden cambiar.

**Recomendación práctica:**

- **Pattern 1** para showcases simples (1 fixture, 1 store). Bajo costo, blast radius mínimo. Fue lo aplicado en F1-S5.
- **Pattern 2** para multiples showcases que comparten múltiples cleanup hooks. Vale la pena introducir el flag.
- **Pattern 3** solo si Clerk mock SDK ya existe y es estable, o si fixture necesita simular más auth state (roles, permissions, multi-org).

**Cuándo aplicar:**

Cualquier brand que cree una "showcase page" / "test fixture" / "dev playground" pública (sin auth) DEBE auditar:

1. ¿Existe algún hook global mounted en root layout que use `useAuth().isSignedIn`?
2. ¿Ese hook tiene `clearStore`, `localStorage.removeItem`, `signOut`, o cualquier mutation reactiva a `isSignedIn === false`?
3. Si sí → showcase debe usar Pattern 1 (auto-rehydrate) como mínimo.

**Test arch-fitness suggested:**

```ts
// __tests__/architecture/test-showcase-fixture-defensive-rehydrate.test.ts
import { readFileSync } from "fs";
import { globSync } from "glob";

test("public showcase pages auto-rehydrate stores on cleanup", () => {
  const showcases = globSync("e2e/__test-pages__/**/*.tsx");
  for (const file of showcases) {
    const content = readFileSync(file, "utf-8");
    const usesStore = /useTenantStore|useShellStore|use\w+Store/.test(content);
    const hasDefensiveEffect = /availableTenants?\.length === 0|store\.\w+ === undefined/.test(content);
    if (usesStore) {
      expect(hasDefensiveEffect, `${file}: showcase usa store sin auto-rehydrate guard`).toBe(true);
    }
  }
});
```

**Cross-brand applicability:**

CRÍTICO para todas las brands. Patrón global Luana:

- Cada brand tendrá test-stack/showcase pages para componentes shell-organism
- Cada brand mountará bootstrap hooks (TenantStoreBootstrap análogo, AuthCleanup, etc.) en root layout
- El race condition aplica a TODA brand que combine ambos

Lift candidates a `core/luana-core-*/`:

1. **`core/luana-core-testing/src/fixture-utils.ts`** — utility hook `useDefensiveStoreHydration(store, mockData)` que encapsula Pattern 1
2. **`core/luana-core-iam/src/cleanup-hooks/`** — el `useSignOutCleanup` actual de vitalia es candidate lift cross-brand. Pero antes de lift, agregar flag `isTestFixtureMode` (Pattern 2) para que ya nazca con la excepción documentada.
3. **`docs/architecture/patterns/test-fixtures.md`** — pattern doc transversal con los 3 patterns + decision matrix

**Trigger para `/pm-luana` promotion proposal:**

Cuando 2da brand (probablemente Nicolify, próxima cronológicamente) introduzca su primer test-stack/showcase page y reporte mismo bug. O preventivo: levantar proposal antes de que las brands futuras pisen el mismo rastrillo.

## Referencias

- Commit fix: `efc0c64b` (vitalia/test-stack showcase auto-rehydrate)
- Showcase original: `vitalia/frontend/e2e/__test-pages__/shell-layout/shell-layout-showcase.tsx`
- Cleanup hook origen: `vitalia/frontend/src/hooks/useSignOutCleanup.ts` (F1-S3 T-4)
- Bootstrap component: `vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx` (F1-S3 T-8)
- Tenant store: `vitalia/frontend/src/stores/tenant-store.ts`
- F1-S3 spec/arch (origen flow): `vitalia/docs/archive/2026/stories/vitalia-fase1-tenant-switcher/`
- React 19 + Zustand + Clerk auth lifecycle docs
