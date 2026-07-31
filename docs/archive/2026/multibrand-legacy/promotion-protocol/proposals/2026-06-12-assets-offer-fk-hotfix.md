---
proposal_id: 2026-06-12-assets-offer-fk-hotfix
status: accepted
date: 2026-06-12
accepted_by: mandato autónomo Chris 2026-06-12 (chris-input doctores 01:40) — hotfix engine bug bloqueante, behavior-preserving
target_package: core/luana-core-assets
origin_brand: vitalia (primer consumidor real del proxy upload)
risk: low (model-only; cero relationship; cero DDL afectado — migraciones raw SQL nunca crearon la FK)
---

# Asset.offer_id: quitar ForeignKey("products.id") model-level

**Bug:** mapper SQLA falla con `NoReferencedTableError` en cualquier brand SIN tabla `products` (vitalia) al primer import real de `AssetsService` — la FK cross-módulo asumía el schema de nicolify. Latente desde el origen: el upload de vitalia nunca se había ejercido (URL FE rota → 404 silencioso).

**Fix:** `offer_id` queda como columna UUID indexada SIN constraint model-level. Cross-module hard-FK viola boundaries (backend-ddd.md § Cross-module). Nicolify: sin cambio de comportamiento (sin relationship, DDL intacto).

**Verificación:** suite engine assets + suite clinics vitalia + smoke nicolify tsc/arch + upload live vitalia 200.
