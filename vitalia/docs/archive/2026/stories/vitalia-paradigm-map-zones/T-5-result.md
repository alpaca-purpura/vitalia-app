# T-5 result — F6 Shell UI realineado

**Ticket:** T-5 (F6) · surface=FE · sonnet (builder-frontend) + orchestrator finalize
**Commit:** (ver abajo)
**State:** tests-passing

## Qué se hizo

Realineación del shell-organism a la taxonomía nueva (5 especialistas + Valeria supervisora + Mateo Operar):

- **agent-catalog.ts** (SSoT shell): `AGENT_RIBBON_ORDER = [lisa, mateo, adrian, lucas, camila]` (Valeria FUERA del ribbon). `AGENT_CATALOG.mateo` = tabLabel "Operar", defaultSubtab "agenda" (deja "Tecnología"). `RIBBON_SUBTABS.mateo = [agenda, pacientes]` (migrados de valeria). `RIBBON_SUBTABS.valeria = []`. `isValidAgent`: mateo=true, valeria=false. `SHIPPED_STATIC_SUBTABS`: mateo.agenda.
- **ConfigTab.tsx**: label "Configurar" → "Plataforma".
- **Routing**: `git mv` app/(shell-organism)/valeria/agenda/ → mateo/agenda/.
- **features/**: `git mv` features/valeria/ (agenda + api + components) → features/mateo/.
- **★ Valeria sidebar PRESERVADO**: ValeriaChat, ValeriaSidebar, ValeriaRail, ValeriaHistory intactos (es la supervisora/orquestadora — se queda).
- Tests de arquitectura actualizados (agent-catalog-ribbon-taxonomy.test.ts NEW + subtab SSoT tests + cross-brand-shell-mirror gate).

## Fix de cierre (orchestrator · Carril A gate-verified)

`features/mateo/components/placeholders/PacientesPlaceholder.tsx` leía `RIBBON_SUBTABS.valeria.find(...)` (ahora `[]` → `meta` undefined → crash `reading 'icon'`). Fix: `.valeria` → `.mateo`. Verificado por el test existente `mateo/pacientes` (no test nuevo → Carril A). Causa: rename valeria→mateo no actualizó este lookup interno.

## Validators GREEN

- `npx tsc --noEmit` → 0 errores
- `npx eslint src/` → 0 errores
- `npx vitest run` → **212 files / 2319 tests PASS** (incluye los 4 que fallaban pre-fix)
- AGENT_RIBBON_ORDER sin 'valeria', con 'mateo' ✓
- Valeria sidebar/chat components presentes ✓

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status |
|---|---|
| frontend-expert | ✅ (builder) |
| vitalia-design-system | ✅ (builder) |
| .claude/rules/frontend-fsd.md | ✅ |
| .claude/rules/frontend-visual-fidelity.md | ✅ |
| .claude/rules/paradigm-arquitectura.md | ✅ |
| .claude/rules/spanish-text.md | ✅ |
