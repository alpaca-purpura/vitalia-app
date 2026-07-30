# 07-merge — vitalia-paradigm-map-zones

> Fase F MERGE · 2026-05-30 · /pm-vitalia · state reviewing → done
> Auditor APPROVED (CHECKPOINTS.md C1-C5). Build 6 tickets + 1 fix Carril B (F-1).

## § 1 — Gherkin verification matrix

| Scenario | Cobertura | Status |
|---|---|---|
| SC-1 re-tag caps + SYSTEM-MAP | `reconcile_capabilities --brand vitalia` exit 0 · grep cero config/infra/valeria | ✅ |
| SC-2 Valeria→supervisora / Mateo→Operar | `validate_system_map --brand vitalia` PASS · Valeria fuera de boxes · agenda→mateo | ✅ |
| SC-3 cap-sin-caja → STOP no-silent | `test_unmapped_cap_halts` | ✅ |
| SC-4 idempotencia + user_visible derivado | `test_rerun_is_noop` + **re-run REAL contra SYSTEM-MAP v2.0 = NO-OP 69 ok/0 updated** (F-1 fixed) | ✅ |
| SC-5 box-inventado + cross-brand + render | `test_invalid_box_rejected` · cross-brand-shell-mirror gate GREEN · cero caps otras brands | ✅ |
| SC-6 backlog Fase 2 re-mapeado | 5 renames + 22 checkpoints con map_box · grep -L map_box → 0 | ✅ |
| SC-7 actions-index + 2 lentes cockpit | `_actions-index.json` generado · (render cockpit = TOOL-SCOPE separado) | ✅ (índice) |

## § 2 — Playwright E2E run

E2E specs escritos + typecheckan (ribbon-realign + mateo-agenda + ~20 actualizados). **NO ejecutados** en esta sesión (stack FE down — corren en CI/auditor). Unit/component/arch: **vitest 2319/2319 PASS** (incl. agent-catalog-ribbon-taxonomy + cross-brand-shell-mirror). tsc 0 · eslint 0.

## § 3 — Capabilities updated/created

- **`vitalia/docs/product/capabilities/platform/product-map-zonas.yaml`** — NEW (cap_change_type:new · map_box:plataforma-tecnica · user_visible:false · change_log[0] type:new).
- **68 caps re-taggeadas** con `map_box` + `map_zone` (derivada) + `user_visible` alineado a zona (config/infra/valeria → cajas de SYSTEM-MAP v2.0). 3 functional_areas inválidas pre-existentes normalizadas (camila.reactivacion→reactivar, config.fiscal→configuracion, ops.reconciliation→plataforma-tecnica).

## § 4 — Modules / SYSTEM-MAP / ADRs refreshed

- `vitalia/docs/architecture/SYSTEM-MAP.yaml` **v2.0** (3 zonas · 12 cajas de 1er nivel · Valeria supervisora · Mateo Operar · config/infra deprecados).
- `ADR-vitalia-005` → **v2.0** (5ª dim zona) · `ADR-vitalia-004` addendum v1.2 (Ribbon 5 especialistas) · `ADR-vitalia-003` ref · `SHELL-DESIGN-CONTRACT.md`.
- 5 stories Fase 2 renombradas + 22 checkpoints con map_box.

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel); cd $WS
.venv/bin/python scripts/reconcile_capabilities.py --brand vitalia            # exit 0
.venv/bin/python scripts/validate_system_map.py --brand vitalia               # PASS (12 boxes / 78 areas)
.venv/bin/python -m pytest scripts/tests/test_map_zones_migration.py -q       # 9 GREEN
.venv/bin/python scripts/map_zones_migration.py                               # re-run = NO-OP (idempotente)
cd vitalia/frontend && npx tsc --noEmit && npx vitest run                     # tsc 0 · 2319 PASS
```

## Pendiente post-merge (TOOL-SCOPE separado · NO esta story)

- Cockpit `MapView.tsx` render por zona + 2 lentes (tools/luana-cockpit/ — cross-brand tool).
- `docs/process/capability-protocol.md` §7 tabla agent_owner → boxes v2 (docs raíz).
- Estos van como dispatch tool/protocol-scope con SCOPE_GATE_SKIP (fase-solo-bootstrap).

## Promotion candidate

Modelo de zonas (ADR-vitalia-005 v2) → lift candidate a otras brands. Ping /pm-luana.
