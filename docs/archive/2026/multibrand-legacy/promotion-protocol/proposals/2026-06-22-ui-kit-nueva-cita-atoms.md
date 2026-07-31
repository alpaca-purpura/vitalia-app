---
slug: 2026-06-22-ui-kit-nueva-cita-atoms
state: migrated                       # build cerrado 2026-06-22 · @luana/ui-kit 0.6.0→0.7.0 · tsc verde · vitest 307 passed
migrated_at: 2026-06-22
migrated_summary: "FormActionBar (nuevo) + Badge success/warning + PageHeader back-pill + EntityPicker.createAction · tokens success/warning agregados · 4 stories + 18 tests nuevos · consumible source-resolved (workspace:*)"
kind: net-new-canon-additions         # NO es un lift de código brand existente — son primitivas nuevas al canon
target_package: core/@luana/ui-kit
origin_story: vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita
contract: vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita/mockups/PROPOSED-CANON-ATOMS.md
semver_impact: minor                  # 4 adiciones aditivas opt-in, cero breaking
ratified_by: Chris
ratified_at: 2026-06-22
blocks: [vitalia-fase2-mateo-nueva-cita (tickets FE)]
---

# Promotion proposal — 4 átomos al canon `@luana/ui-kit` (P-0 de Nueva cita)

## Resumen

La hoja **"Nueva cita"** (agenda de Mateo, vitalia) necesita 4 primitivas transversales que el
canon `@luana/ui-kit` todavía no tiene. Se detectaron en el refinamiento `/po-ux` (auditoría del
mockup vs Storybook, 2026-06-22). Chris greenlit las 4 + eligió promoverlas **antes** del build FE
(son soft-dep de los tickets FE de la story). La marca las DESCUBRIÓ; el canon las POSEE.

Las 4 son transversales (formularios · feedback · page chrome · entity selection) → pertenecen al
kit compartido, NO a `features/scheduling`. La mini-vista del día (`DayAvailabilityStrip`) NO entra
acá — es componente de feature scheduling (lift-candidate aparte, lo decide el architect).

## Los 4 átomos (contrato completo: `…/mockups/PROPOSED-CANON-ATOMS.md`)

| # | Átomo | Tipo | Destino (layout REAL flat del kit) | Story |
|---|---|---|---|---|
| 1 | `FormActionBar` | molécula NUEVA | `src/FormActionBar.tsx` (flat, junto a `form.tsx`) | `forms.FormActionBar` |
| 2 | `Badge` variants `success` \| `warning` | extender existente | `src/badge.tsx` (+ tokens `--c-success/--c-warning` si faltan) | `atoms.Badge` (grupo variants) |
| 3 | `PageHeader` back-pill (`backLabel`/`onBack`) | extender existente | `src/layout/page.tsx` | `layout.PageHeader` |
| 4 | `EntityPicker` `createAction` slot | extender existente | `src/EntityPicker.tsx` | `EntityPicker` (variant `with-create-action`) |

> ⚠ El contrato sugiere paths `src/forms/`, `src/feedback/`, `src/page/`, `src/entity/` que **NO
> existen** — el kit es FLAT. El build usa el layout real (arriba).

## Análisis de fit (promotion gate)

- **¿Transversal?** SÍ — las 4 son chrome/form/feedback genéricos. FormActionBar = el "segundo modo"
  del canon (hoy solo autosave). Badge success/warning = estados semánticos que hoy se resuelven con
  clases ad-hoc (reinvención de primitiva). PageHeader back-pill = retorno de hoja-leaf (cualquier
  marca). EntityPicker createAction = pick-or-create (patrón universal).
- **Consumers ≥2 viables:** vitalia (inmediato) + nicolify (shell gemelo, mismas hojas-leaf) +
  comunify. No salud-específico.
- **¿Breaking?** NO — las 4 son aditivas opt-in (variants/props/slots nuevos con default no-op).
  `semver: minor`.
- **¿Brand leakage?** NO — cero refs vitalia/salud. `accent?: AgentColor` usa tokens de agente
  genéricos (foundations.AgentColors ya existe).
- **Anti-duplication:** extender los 3 componentes existentes (badge/PageHeader/EntityPicker), NO
  crear mirrors. FormActionBar es genuinamente net-new (grep del kit: no hay action-bar/form-footer).

## Ejecución (handoff build)

`/pm-luana` no escribe core src (anti-creep) → el build lo ejecuta un builder en `core/@luana/ui-kit`:
componente/variant + story (estilo de las stories existentes) + export en `src/index.ts` + tokens
faltantes + bump `package.json::version` (minor) + verificar (tsc + build-storybook). Al cerrar →
state `migrated` + desbloquea los tickets FE de la story.

## Verificación

- `pnpm --filter @luana/ui-kit typecheck` (o `tsc --noEmit`) verde.
- Las 4 stories renderizan en Storybook (`build-storybook` o dev `:6007`).
- Export desde `@luana/ui-kit` resuelve (consumible por `vitalia/frontend`).
