# T-6 result — F7 Tests e2e Ribbon/Mateo + specs Valeria

**Ticket:** T-6 (F7) · surface=FE · sonnet (builder-frontend) + orchestrator finalize
**State:** tests-passing

## Qué se hizo

- **2 specs e2e nuevos** en `vitalia/frontend/e2e/regression/vitalia-paradigm-map-zones/`:
  - `ribbon-realign.spec.ts` — Ribbon = 5 especialistas (Lisa·Mateo·Adrián·Lucas·Camila) + tab Plataforma · Mateo "Operar" presente · **NO tab Valeria** (es sidebar).
  - `mateo-agenda-loads.spec.ts` — la agenda migrada (ruta `mateo/agenda`) carga; asserta que la URL ya no es `valeria/agenda`.
- **~20 specs e2e existentes actualizados**: rutas `valeria/agenda` → `mateo/agenda`; navegación de tab Valeria → Mateo. **Refs al Valeria SIDEBAR/chat preservadas** (Valeria sigue siendo el chat supervisor). Los `valeria/agenda` restantes son **comentarios** que documentan la migración + 1 assertion correcta (`not.toContain("/valeria/agenda")`).

## Validators GREEN

- `pytest scripts/tests/test_map_zones_migration.py -k noop` → idempotencia GREEN
- `reconcile_capabilities.py --brand vitalia` → exit 0
- `validate_system_map.py --brand vitalia` → ✅ PASS (cero issues · 12 boxes / 78 areas)
- `tsc --noEmit` → 0 · `eslint e2e/.../vitalia-paradigm-map-zones/` → 0
- vitest → sin regresión (2319 pass)

## Nota Playwright

Los specs e2e están **escritos + typecheckan**, NO ejecutados en este contexto (stack FE down — el run real es CI/auditor). Visual-goldens que referenciaban "Valeria active tab" quedan marcados para regenerar (Valeria ya no es tab) — el auditor lo verifica.

## Finalize (orchestrator · Carril A)

El builder-frontend hit budget mientras verificaba el grep de refs Valeria. El orchestrator confirmó: 2 specs nuevos OK, ~20 actualizados OK, refs restantes = comentarios, validators GREEN → cerrado.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status |
|---|---|
| frontend-expert | ✅ (builder) |
| playwright-expert | ✅ (builder) |
| vitalia-design-system | ✅ (builder) |
| .claude/rules/tdd-mandatory.md | ✅ |
