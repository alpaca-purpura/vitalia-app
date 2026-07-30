---
slug: mateo-agenda-hooks-crash-ssr422
date: 2026-05-30
severity: high
surface: FE
feature: scheduling / agenda (features/mateo)
cap_target: scheduling.mateo-agenda
discovered_by: "Task 4 e2e run — story vitalia-paradigm-map-zones regression specs (primer run real)"
repro_verified: true
proposed_story_type: bugfix
status: open
---

# mateo/agenda crashea en render cuando el SSR `getInitialAgendaState` devuelve 422

## Resumen

La ruta `/{tenantId}/mateo/agenda` (agenda real, `ValeriaAgendaView` de `features/mateo`)
**no degrada con gracia**: cuando el fetch SSR `getInitialAgendaState` falla con **422**
(p. ej. tenant sin data/config de agenda, o BE caído), el árbol de la agenda crashea en
render con el error de React **"Rendered more hooks than during the previous render"**.
El subtree completo de la agenda no commitea → en pantalla solo queda el `ValeriaSidebar`
(sin Ribbon de contenido ni grilla). Viola el requisito de graceful degradation de
ADR-vitalia-004 § 8 (SSR hydration con degradación).

**No es regresión de `vitalia-paradigm-map-zones`** — el componente de agenda
(`ValeriaAgendaView` + `AgendaCalendar`) se construyó en `vitalia-fase2-valeria-agenda`
(pre map-zones); map-zones solo lo movió `features/valeria → features/mateo` + renombró la
ruta (T-5). Estos e2e (T-6) son los **primeros en ejercer el contenido de la agenda** bajo
la condición 422 del tenant de test, por eso recién ahora se ve.

## Repro (verificado 2026-05-30)

Stack vitalia arriba (`make dev-vitalia` · BE :8002 · FE :3002). Native Playwright:

```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
  e2e/regression/vitalia-paradigm-map-zones/mateo-agenda-loads.spec.ts
```

Resultado: `FE-2-c` (contenido de la agenda renderiza) **falla** — `agenda-preset-filters`
(marker always-rendered de la vista real) nunca aparece. El DOM solo muestra el
`ValeriaSidebar`. `FE-2-a/b/d/e/f/g` (shell montado, no-not-found, Mateo tab activo,
sidebar, deep-link, subtab activa) **pasan** — el shell sí monta; lo que crashea es el
panel de contenido de la agenda. `FE-1-e` (ribbon-realign) también queda bloqueado: la
navegación client-side a mateo/agenda no commitea porque la ruta destino crashea.

### Evidencia en logs (container FE `luana-dev-vitalia_frontend_dev-1`)

```
[agenda-server] getInitialAgendaState failed: 422 Unprocessable Entity {
  tenantId: 'e69a691d-070e-5caf-a053-6e74642ec100',
  view: 'semana',
  date: '2026-05-30'
}
[browser] Uncaught Error: Rendered more hooks than during the previous render.
```

(El error de hooks aparece 1× por cada render de mateo/agenda en el test.)

## Diagnóstico (parcial — pendiente confirmar la causa exacta)

- `ValeriaAgendaView` (`src/features/mateo/components/agenda/ValeriaAgendaView.tsx`) llama
  todos sus hooks de forma incondicional al tope (OK). El "more hooks" vive en un **hijo**
  del árbol de la agenda (`AgendaHeader` / `AgendaPresetFilters` / `AgendaCalendar` y sus
  variantes Day/Week/Month, o un custom hook `useAgendaGrid`/`useFreshness`/`useClinicId`)
  que cambia la cantidad de hooks entre el render con `initialData` placeholder y el render
  tras la transición a estado de error (422).
- `AgendaCalendar.tsx` tiene `if (isLoading) return <SkeletonCalendar/>` **después** de sus
  hooks (consistente), así que no es ahí.
- Dos frentes a investigar: (a) por qué `getInitialAgendaState` 422ea con
  `{view:'semana', date:'2026-05-30'}` — ¿contrato BE o falta de fixtures del tenant de
  test?; (b) el hook condicional que dispara el crash en el path degradado.

## Fix sugerido (bugfix story · repro-first)

- **Tipo de story:** `bugfix` (lite, repro-first — el e2e ES el repro). Ver
  `docs/architecture/luana-platform/ADR-011-bugfix-story-type.md`.
- **cap_change_type:** `fix` sobre `scheduling.mateo-agenda` (no agrega scenarios; arregla
  comportamiento roto de degradación).
- **Bar de verificación:** quitar el `test.fixme` de `FE-2-c` + `FE-1-e` y que pasen
  ejerciendo la acción real (no GET 200) + leer logs sin el error de hooks.
- **Alcance:** (1) que la agenda monte un estado de error/empty sin crashear cuando no hay
  `initialData` (graceful degradation), arreglando el hook condicional; (2) opcional:
  resolver el 422 del SSR (fixtures del tenant de test o contrato de params).

## Specs afectados (con `test.fixme` apuntando a este doc)

- `vitalia/frontend/e2e/regression/vitalia-paradigm-map-zones/mateo-agenda-loads.spec.ts` → `FE-2-c`
- `vitalia/frontend/e2e/regression/vitalia-paradigm-map-zones/ribbon-realign.spec.ts` → `FE-1-e`

Los selectores ya quedaron correctos (`agenda-preset-filters` = marker real de la vista);
solo hay que quitar el `.fixme` cuando se arregle el crash.

## Referencias

- `vitalia/docs/archive/2026/stories/vitalia-paradigm-map-zones/` (story que migró la ruta)
- `.claude/rules/hotfix-repro-mandatory.md` (repro-first gate del tipo bugfix)
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` (ADR-vitalia-004 § 8 graceful degradation)
