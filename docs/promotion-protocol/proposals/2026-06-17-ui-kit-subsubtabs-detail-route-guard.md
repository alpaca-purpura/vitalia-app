---
proposal_id: 2026-06-17-ui-kit-subsubtabs-detail-route-guard
status: accepted
date: 2026-06-17
accepted_at: 2026-06-17
proposed_by: /dev-team (vitalia-fase2-lisa-servicios G round 2 · G2-F10)
accepted_by: Chris             # ratificado 2026-06-17 (G round 2 · "arregla F7 y F10 también")
target_package: core/@luana/ui-kit
origin_brand: vitalia
origin_story: vitalia-fase2-lisa-servicios (G2-F10)
risk: low (additive guard · returns null on detail routes · no API change · generic across brands)
---

# SubSubTabsBar — detail-route guard en @luana/ui-kit

**Qué:** `SubSubTabsBar` (línea 3 del shell, N3-static) renderizaba sus sub-sub-tabs
siempre que la ruta tuviera `{agent}.{subtab}` con entry en `subSubTabsByKey`. En una
ruta de **detalle de entidad** (`/{tenant}/{agent}/{subtab}/{entityId}/{leaf}`) el
segmento después del subtab es un **id de entidad**, no un sub-sub-tab declarado — pero
la barra igual se renderizaba, mostrando los N3 (ej. Catálogo/Escalera) ENCIMA del
workspace de la entidad, que ya tiene su propio `EntitySubNavBar`.

**Fix (1 guard genérico):** si el segmento post-subtab existe y NO es un sub-sub-tab
declarado → es una ruta de detalle → `return null` (la barra no se monta). Cero cambio
de API; aditivo. Aplica a TODAS las marcas (cualquier subtab con N3 + rutas de detalle).

**Por qué core:** `SubSubTabsBar` vive en `@luana/ui-kit` (shell compartido cross-brand,
lift `lift-shell-chrome-ui-kit`). El bug es del componente compartido; el fix debe vivir
ahí (no parche por marca). Chris ratificó el edit core en G round 2.

**Caso origen (G2-F10):** en `lisa-servicios`, al entrar al detalle de un servicio
(`/lisa/servicios/{offerId}/resumen`) seguían apareciendo los sub-sub-tabs Catálogo/Escalera.

**Cambio (1 archivo):** `core/@luana/ui-kit/src/organism/shell/SubSubTabsBar.tsx` —
`isDetailRoute` (post-subtab segment no declarado) + condición en el early-return.

**Gate:** ui-kit tsc 0 (archivo) · vitalia servicios suite 153/153. Consumido vía pnpm
workspace (`@luana/ui-kit` → src, sin build step).

**Downstream:** ningún consumidor dependía de que la barra se mostrara en rutas de detalle
(era el bug). Backward-compatible para rutas de lista/sub-sub-tab normales.
