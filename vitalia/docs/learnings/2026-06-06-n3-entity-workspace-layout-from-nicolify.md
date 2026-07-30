---
brand: vitalia
date: 2026-06-06
slug: n3-entity-workspace-layout-from-nicolify
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify]
target_core_package: core/@luana/ui-kit (shell-organism · lift accepted 256517a3)
origin_story: vitalia-bugfix-shell-valeria-responsive
---

# N3 list/detail: factorizar en `EntityWorkspaceLayout` reusable (aprendido de nicolify)

## Qué aprendimos

El patrón N3-dynamic **lista → detalle** (directorio de entidades → workspace de una entidad con leaf-tabs `[‹ raíz][avatar entidad][tabs]`) admite dos niveles de factorización:

- **vitalia (peor):** cablea `EntitySubNavBar` **a mano en cada `layout.tsx`** de cada superficie list/detail (`lisa/staff`, `adrian/embudo`). Duplica el wiring (entity hydration, leaves, rootHref/rootLabel, skeleton) → drift entre superficies + cada nueva list/detail re-inventa el cableado.
- **nicolify (mejor):** factorizó un wrapper reusable **`EntityWorkspaceLayout`** (`components/shared/shell-organism/EntityWorkspaceLayout.tsx`) que monta `EntitySubNavBar + {children}` + skeleton **store-free SSR-safe (gate G2)**. Cada `[entityId]/layout.tsx` solo le pasa `entity / leaves / rootHref / rootLabel`. Un solo lugar = un solo contrato del list/detail.

`EntityWorkspaceLayout` es la mejor factorización existente del list/detail en toda la plataforma.

## Origen

Story `vitalia-bugfix-shell-valeria-responsive` (2026-06-06). Chris pidió comparar el shell de vitalia vs nicolify ("¿lo tiene igual? ¿cuál es mejor?") antes de refinar el punto 7 (cementar el patrón N3 list/detail). La comparación destapó que nicolify, siendo un port re-skinneado del shell de vitalia, había **mejorado** la factorización del N3 que vitalia dejó a mano.

## Why

- **Menos duplicación + cero drift:** un wrapper único garantiza que todas las list/detail se comporten igual (back-to-root, roving tabindex, disabled-en-directorio, skeleton).
- **SSR-safe baked-in:** el skeleton store-free (G2) ya viene resuelto en el wrapper — no se re-implementa mal por superficie.
- **Lift-ready:** el shell-organism va a `@luana/ui-kit` (proposals accepted 256517a3). Convergir vitalia al `EntityWorkspaceLayout` de nicolify reduce el delta del lift y deja UN solo componente cross-brand.

## How to apply

1. **Toda sub-tab list/detail (N3-dynamic) usa `EntityWorkspaceLayout`** — NUNCA cablear `EntitySubNavBar` a mano en el `layout.tsx`. El layout solo provee `entity/leaves/rootHref/rootLabel`.
2. **Vitalia debe portar `EntityWorkspaceLayout`** (port verbatim re-temizado desde nicolify) y migrar `lisa/staff` + `adrian/embudo` a usarlo (story `vitalia-bugfix-shell-valeria-responsive` punto 7, sujeto a coordinación con las stories abiertas de esos módulos).
3. **Meta-learning:** antes de rediseñar una superficie de shell compartida, **comparar cross-brand** — la marca "hija" (port) puede haber evolucionado una factorización mejor que la "madre". (Refuerza `anti-duplication-refining.md`: el grep cross-brand no es solo para no-duplicar, también para adoptar la mejor versión existente.)

## Referencias

- nicolify: `nicolify/frontend/src/components/shared/shell-organism/EntityWorkspaceLayout.tsx`
- vitalia (a portar): `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (existe, falta el wrapper)
- contrato: `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md § 3.1` (N3) + `SHELL-DESIGN-CONTRACT.md`
- lift: promotion proposal shell→`@luana/ui-kit` (commit 256517a3)
- story origen: `vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/01-spec.md § Prior art › Nicolify comparison`
