# Observed bug — @luana/hooks + @luana/ui-kit: tsc rojo por deuda del lift (PRE-EXISTENTE)

**Fecha:** 2026-05-31 · **Origen:** build-autosave-primitive-luana (gate check) · **Severidad:** medium · **Estado:** documentado (pre-existente, NO de esta story)

## Síntoma
`cd core/@luana/hooks && npx tsc --noEmit` y `cd core/@luana/ui-kit && npx tsc --noEmit` fallan (exit 2). TODOS los errores están en archivos **pre-existentes** (último commit que los tocó: `b1bdb3ab` / `3282768a` — el lift original de los packages @luana, NO build-autosave-primitive-luana):
- `@luana/hooks/src/use-copilot-offset.ts`, `use-currency-catalog.ts`, `use-shell-mutex.ts` — hooks **acoplados a brand** lifteados con imports `@/features/copilot/...`, `@/lib/api/...`, `@tanstack/react-query` que NO resuelven en el contexto del package (el lift movió el código pero no arregló los imports ni agregó las deps).
- `@luana/ui-kit/src/timezone-select.tsx` — `Intl.supportedValuesOf` (lib target) + params `any`.
- `@luana/{hooks,ui-kit}/tests/{_deferred/use-copilot-offset.test.ts, label.test.tsx}` — imports `@/...` rotos + matchers jest-dom (`toBeInTheDocument`/`toHaveClass`) sin los tipos cargados.

Los archivos NUEVOS de la primitiva de autosave (`useAutosave.ts`, `AutosaveBadge.tsx`, `autosave.ts`) typecheck **limpios** (cero errores).

## Por qué no se arregló acá
Es deuda PRE-EXISTENTE del lift de @luana, ortogonal al autoguardado. Arreglarla bien implica: (a) `use-copilot-offset.ts`/`use-shell-mutex.ts` están mal lifteados (acoplados a brand) → deberían volver a la brand o desacoplar sus imports; (b) agregar `@tanstack/react-query` a deps de @luana/hooks; (c) cargar `@testing-library/jest-dom` types en el setup de vitest/tsconfig de los packages. Es su propia tarea de saneamiento de @luana.

## Fix sugerido (story dedicada de saneamiento @luana)
1. Mover/desacoplar `use-copilot-offset.ts` + `use-shell-mutex.ts` (acoplados a copilot/shell de una brand) fuera de @luana/hooks, o arreglar sus imports + deps.
2. Agregar `@tanstack/react-query` a `@luana/hooks` deps (lo usa `use-currency-catalog.ts`).
3. Cargar tipos `@testing-library/jest-dom` en tsconfig/setup de @luana/{hooks,ui-kit} para los `.test.tsx`.
4. `Intl.supportedValuesOf` → bump lib target o guard.

Hasta entonces, el gate de tsc por-package de @luana NO es verde por esta deuda. La story build-autosave-primitive-luana NO introduce errores tsc nuevos (verificado: cero errores en los archivos de autosave).
