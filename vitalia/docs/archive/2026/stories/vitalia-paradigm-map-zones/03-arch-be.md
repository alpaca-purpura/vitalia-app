<!-- voseo-allowed: contrato técnico interno, no user-facing -->
# 03-arch-be — Surface BE/scripts/docs (builder-backend)

> Subconjunto BE del contrato consolidado `03-arch.md`. Owner: **builder-backend** (Sonnet). Auditor: **auditor-backend** (Opus).
> NO toca `vitalia/backend/src/modules/` (cero DDD nuevo). Toca: `scripts/`, `vitalia/docs/product/capabilities/`, `vitalia/docs/architecture/`, `vitalia/.claude/rules/`, stories Fase 2 (rename).

## Frentes BE

### F1 — Re-tag de caps (48) + cap nuevo
- Script `scripts/map_zones_migration.py` (NEW · §2.1 de 03-arch): consume `SYSTEM-MAP zones[].target_boxes[].absorbs`, escribe `map_box` por cap, alinea `user_visible`, re-mapea functional_area Plataforma/Infra. HALT-no-silent si unmapped (SC-3). Idempotente (SC-4).
- Mapeo verbatim: `02-impact.md` §1-3. NO inventar.
- Cap nuevo `vitalia/docs/product/capabilities/platform/product-map-zonas.yaml` (`new` · `map_box: plataforma-tecnica` · `user_visible: false` · schema v4 completo + change_log[0] type:new).

### F2 — SYSTEM-MAP + validador
- Promover `zones[].target_boxes` → boxes de 1er nivel (12 cajas con functional_areas heredadas de absorbs).
- `config`/`infra` en `agents[]` → `status: deprecated`. Mateo → caja Operar en `agents[]`. Valeria → nota supervisor (no caja de proceso) movida a `motor-agentico.runtime`.
- `scripts/validate_system_map.py` (MODIFY): agregar `valid_boxes` desde `zones[].boxes` + check `cap.map_box ∈ valid_boxes` (SC-5) + coherencia `user_visible`↔zona. Back-compat functional_area.
- Verificar `scripts/reconcile_capabilities.py` exit 0 (ajustar enum agent_owner si rechaza ausencia config/infra).

### F4 (generador) — actions-index (EXTEND, no NEW layer)
- `scripts/generate_actions_index.py` (NEW thin): compone `_code-index.json` (ya existe) + `dev_preview.api_endpoints`/`route`/`main_component` de caps → `vitalia/docs/product/capabilities/_actions-index.json` (gitignored R3).
- NO grep-walker paralelo — reusa `generate_code_to_cap_index.py` output (NO-NEW-LAYER, ver 03-arch §7).

### F5 — ADRs/docs/rules
- ADR-vitalia-005 → v2.0 · ADR-vitalia-004 addendum v1.2 · ADR-vitalia-003 ref menor · SHELL-DESIGN-CONTRACT.md · vitalia/CLAUDE.md · vitalia-design-system SKILL · shell-*.md rules. Detalle: 03-arch §4.

### F0 — Backlog rename
- `git mv` 5 stories + actualizar checkpoints (map_zone/map_box). Tabla: 03-arch §5. Todas las Fase 2 ganan `map_box` en checkpoint (SC-6).

## Patrones required
- Scripts Python idempotentes con `--dry-run` / `--apply`; `${WS}/.venv/bin/python`.
- YAML Edit preservando comentarios/orden donde posible; nunca borrar campos legacy (deprecar, no remover).
- `git mv` para renames (preserva historia); commit por pathspec (índice compartido hub).
- HALT-no-silent en migración (cardinal SC-3).

## Patrones forbidden
- ❌ Editar `vitalia/backend/src/modules/` (cero código de módulo en esta story).
- ❌ Tocar `core/luana-core-*` o `{comunify,nicolify,lupulo}/`.
- ❌ Tocar `tools/luana-cockpit/` (TOOL-SCOPE separado).
- ❌ Asignar caja por defecto cuando una cap no mapea (debe halt).
- ❌ Editar `_actions-index.json` / `modules/{m}.md` / `BACKLOG.*` a mano (auto-gen R3).
- ❌ Grep-walker paralelo para el actions-index (reusar `_code-index.json`).

## Tests (RED primero)
`scripts/tests/test_map_zones_migration.py`: `test_unmapped_cap_halts` · `test_rerun_is_noop` · `test_invalid_box_rejected` · `test_config_infra_valeria_fully_retagged`. Validator: rechaza map_box inventado, acepta 12 válidos.

## Gates verdes
```bash
WS=$(git rev-parse --show-toplevel)
${WS}/.venv/bin/python scripts/map_zones_migration.py --brand vitalia --apply
${WS}/.venv/bin/python scripts/validate_system_map.py --brand vitalia        # exit 0
${WS}/.venv/bin/python scripts/reconcile_capabilities.py --brand vitalia      # exit 0
grep -rlE 'agent_owner:\s*(config|infra)\b' vitalia/docs/product/capabilities/ | wc -l   # 0 (top-level)
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q        # intacto
```
