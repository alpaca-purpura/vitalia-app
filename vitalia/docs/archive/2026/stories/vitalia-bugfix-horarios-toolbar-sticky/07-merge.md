# 07-merge — vitalia-bugfix-horarios-toolbar-sticky

**Merged:** 2026-06-15 · **type:** bugfix · **cap:** clinics.lisa-doctores (change_type: fix)
**chris_verify:** SATISFIED (Chris, 2026-06-15 — toolbar fijo confirmado live, incognito fresco)

## Qué se arregló
El toolbar de la vista Horarios (Lisa › Staff › {doctor}) no quedaba fijo al scrollear el
calendario. Root cause CORE: `@luana/ui-kit AppPanelSlot` montaba el content-area como `block`
con `overflow-y-auto`, pero `EntityWorkspaceLayout` usa `flex-1` esperando un padre flex-column
→ no clampaba → el panel scrolleaba todo y arrastraba los toolbars. Fix: `+flex flex-col` en el
content-area (`@luana/ui-kit` 0.4.0→0.4.1) + complemento vitalia (grid `min-h-0`).

## Commits
- `88c56dc9` — core fix AppPanelSlot flex-col + ui-kit 0.4.1 + CHANGELOG + complemento vitalia + guards.
- `2657203d` — corrección scope downstream (consumers reales = vitalia + nicolify).
- `6597b3b1` — fix colateral: `@source` Tailwind v4 off-by-one (escaneo @luana/ui-kit).

## Verificación
- Live (Chrome DevTools MCP, dev-app): EWL clampa, grilla = único scroller, toolbars FIJOS al
  scrollear (heading 209→209), día-header sticky, página no scrollea. Screenshot en story dir.
- Playwright behavioural real-backend 3 passed. ui-kit vitest RED/GREEN. Suites FE/ui-kit verdes.
- Consumers de @luana/ui-kit: vitalia ✓ live · nicolify ✓ live · comunify/lupulo no consumen.

## Engine boundary
Fix en `core/@luana/ui-kit` → promotion proposal `docs/promotion-protocol/proposals/2026-06-15-ui-kit-app-panel-slot-flex-col.md` (state accepted, ratificado Chris). Llega a nicolify/comunify vía sync `wip/vitalia → main → wip/{brand}`.

## Cap ledger
`clinics/lisa-doctores.yaml` — change_log append type=fix (sin scenarios nuevos · solo layout).
