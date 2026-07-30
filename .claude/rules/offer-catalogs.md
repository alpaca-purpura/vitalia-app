# Offer Catalogs SSoT

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body (DAG 6 catalogs, no-skip ×6) en `offer-expert` skill → `references/offer-catalogs.md`. Presets: `offer-type-preset-expert`.

Trigger: `core/luana-core-offer-studio/**` (engine catalogs) · `{brand}/.../offer/extensions.py` (preset packs EP-2) · `{brand}/frontend/src/features/offer-studio/**`. El hook `contract-guard.js` recuerda bump `_CATALOG_VERSION`.

No-skip 1-liner: catálogos = SSoT engine (NUNCA hardcodear labels/metadata en FE — arch test bloquea) · catalog edit → bump `_CATALOG_VERSION` + arch tests engine + cada brand consumer · mirror per-brand prohibido (EP-2).
