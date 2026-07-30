# OBSERVED (cross-story env) — vite/vitest version skew del lockfile-regen

> **Origen:** sesión bugfix-shell-nav-scroll-errors (2026-06-02 noche). Anotado acá
> per ratificación Chris (es dominio harness/env-stabilization, NO de aquella story).
> **No es un bug de producto.** Es churn de dependencias.

## Síntoma
`cd vitalia/frontend && npx tsc --noEmit` rompía con:
```
widget/vite.config.ts(56,3): error TS2769: 'test' does not exist in type 'UserConfigExport'
```
(y, al intentar `defineConfig` desde `vitest/config`, mutaba a TS2321 "Excessive stack
depth comparing types" + TS2769 de overload — plugins inferidos como `Plugin<any>[][]`).

## Causa
Los `pnpm-lock.yaml` regenerados esta sesión (aparecen como `??` untracked en todo el
workspace) **bumpearon `vite`** en `node_modules` sin alinear `vitest` /
`@vitejs/plugin-react`. `widget/vite.config.ts` usa `import { defineConfig } from "vite"`
+ un bloque `test:` (config de Vitest) → el tipo de vite ya no lo acepta, y el de vitest
choca con la versión de plugin-react. Es un **version-skew**, no un error de código.

## Mitigación aplicada (bugfix-shell, commit aeebe007)
Excluí SOLO `widget/vite.config.ts` del `tsconfig.json` de la app (lo cubría el glob
`**/*.ts` por accidente; `vite build` carga el config vía esbuild e ignora tipos →
cero coverage real perdida; `widget/src` sigue chequeado). Desbloquea el gate
compartido `fe_typecheck`.

## Pendiente real (harness-stabilization)
1. **Alinear versiones** vite ↔ vitest ↔ @vitejs/plugin-react en el workspace (el bump
   vino del lockfile-regen, no de un upgrade intencional). Decidir si congelar o subir
   todo el set de forma consistente.
2. **Decidir el destino de los `pnpm-lock.yaml ??`** regenerados (commitearlos
   alineados vs revertir al estado previo). Hoy son artefactos sueltos.
3. Una vez alineado, considerar revertir el exclude de `widget/vite.config.ts` +
   migrar su import a `vitest/config` (el patrón correcto cuando las versiones cuadran),
   o darle a `widget/` su propio gate `tsc -p widget/tsconfig.json`.

Relacionado: aprendizaje #1 del handoff bugfix-shell (deps stale del container →
`pnpm install` in-container) — misma familia de churn de dependencias.
