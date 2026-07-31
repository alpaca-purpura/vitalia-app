---
slug: luana
kind: core
status: active
last_updated: 2026-06-12
ssot_live:
  - docs/product/
  - docs/core-modules/
  - docs/promotion-protocol/
  - docs/architecture/luana-platform/
owner: /pm-luana
---

# Luana — core engine

> El núcleo compartido del portfolio. NO es brand consumidora — es la "constitución" sobre la que las 10 brands construyen.

## Razón de existir

Acelerar dev cross-brand. Cada brand aporta aprendizaje → core captura abstracciones reutilizables → nuevas brands arrancan ya con superpoderes acumulados.

## Surfaces

| Tipo | Path | Descripción |
|---|---|---|
| Engine packages | [`core/luana-core-*`](../../core/) | 26 paquetes Python + TS publicables |
| Extension SDK | `core/luana-core-extension-sdk/` | EP-1..EP-18 contracts |
| Cross-cutting concerns | [`docs/core-modules/`](../core-modules/) | 22 transversales |
| Promotion protocol | [`docs/promotion-protocol/`](../promotion-protocol/) | brand→core lift gate |

## Promotion proposals (live)

- Proposed: 8
- Under review: 0
- Accepted (lift programado): 1
- Migrated (cerrados OK): 9
- Rejected (archive): 0

## State portfolio

- 26 packages extraídos
- 4 brands consumidoras (3 shipped: Nicolify, Vitalia, Comunify + 1 placeholder: Lupulo)
- 6 pendientes bootstrap (SaaSora, InmoFlow, Retailly, Fixia, Guestly, FitFlow)

## Ownership

- `/pm-luana` (skill) — owner promotion gate, semver, breaking changes, EPs
- `/pm` (master) — orquesta visibility cross-portfolio

## Drill-down

- Roadmap platform: `docs/product/outcomes/`
- Promotion candidates: `docs/promotion-protocol/proposals/`
- Plan multibrand original: `docs/architecture/luana-platform/01-core-audit.md`
- Purge audit: `docs/architecture/luana-platform/02-core-purge-audit.md`
