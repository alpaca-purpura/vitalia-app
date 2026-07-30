# T-2 result — Storybook en `@luana/ui-kit` (render REAL · grupo lista/detalle)

**Ticket:** T-2 (`production_code: false` · dev tooling) · **brand:** platform · **model:** workhorse
**State:** tests-passing (todos los gates GREEN). Awaiting orchestrator → gate-runner → auditor-frontend.

## Qué se construyó

Storybook 10.4.0 en `core/@luana/ui-kit`, framework `@storybook/nextjs` (3 de 4 componentes usan
`next/navigation`), renderizando los componentes **REALES de `src/`** (jamás copias) con:

- **autodocs** (código + props por story vía react-docgen-typescript) — `docs.autodocs: "tag"` + `tags: ["autodocs"]` por story.
- **"## Cuándo usarlo" + "## Cuándo NO / alternativa"** por story, en `meta.parameters.docs.description.component`.
- Tailwind v4 CSS-first cableado en `.storybook/preview.css` (self-contained, sin `@config` cross-brand).

**Scope entregado (incremental, NO big-bang):** infra de Storybook + el grupo LISTA/DETALLE de 4 componentes.
No se construyeron stories del resto del set canónico (eso es batch posterior).

### Archivos nuevos (consumen `src/`, no lo editan)

| Archivo | Rol |
|---|---|
| `core/@luana/ui-kit/.storybook/main.ts` | framework `@storybook/nextjs` + addon-a11y + react-docgen-typescript + autodocs |
| `core/@luana/ui-kit/.storybook/preview.ts` | `import preview.css` + `nextjs.appDirectory: true` (mock de router hooks) |
| `core/@luana/ui-kit/.storybook/preview.css` | Tailwind v4 (`@import` + `@source "../src"` + `@theme inline` que mapea tokens HSL → utilidades `bg-card`/`bg-agent-*`) + bloques de tokens light/dark (espejo de vitalia globals.css) + fix z-index Radix popper |
| `core/@luana/ui-kit/postcss.config.mjs` | plugin `@tailwindcss/postcss` para procesar las directivas v4 |
| `core/@luana/ui-kit/stories/EntityWorkspaceLayout.stories.tsx` | DetailMode / MasterMode / Loading |
| `core/@luana/ui-kit/stories/EntitySubNavBar.stories.tsx` | MasterMode / WorkspaceMode (leaves + add-affordance) |
| `core/@luana/ui-kit/stories/EntityInfoCard.stories.tsx` | Default / WithIcon / Selected / Inactive / Loading (Skeleton) / Empty |
| `core/@luana/ui-kit/stories/EntityPicker.stories.tsx` | Default / Preselected / Disabled · mock `searchFn` cursor-paged sobre 15 doctores LatAm (query-lib agnóstico, sin react-query) |
| `scripts/_check_storybook_stories.mjs` | gate `sb_renders_canon` (batch-aware: cada componente del batch tiene story que importa el real de `../src/` + tiene autodocs) |
| `scripts/_check_storybook_when_to_use.mjs` | gate `sb_when_to_use` (cada story tiene "## Cuándo usarlo") |

`package.json` (v0.6.0): scripts `storybook` (puerto 6007) + `build-storybook`; devDeps `storybook`, `@storybook/nextjs`,
`@storybook/addon-a11y`, `@tailwindcss/postcss`, `tailwindcss`, `react-docgen-typescript`, `next` (todos dev — fuera del
bundle de runtime de cualquier marca).

## Cómo lanzar Storybook (per-component visual-review de Chris)

```bash
cd /home/chalreme/Proyectos/luana-vitalia
pnpm --filter @luana/ui-kit storybook      # dev server → http://localhost:6007
# build estático (gate): pnpm --filter @luana/ui-kit build-storybook
```

Chris navega Batch-by-Batch: el grupo lista/detalle aparece bajo `Lista / Detalle/*`. Cada story trae el
"Cuándo usarlo" en su tab Docs + los props auto-documentados.

## Gates (output literal)

```
=== sb_renders_canon ===
sb_renders_canon PASS: 4 canon stories present (lista/detalle batch)
=== sb_when_to_use ===
sb_when_to_use PASS: 4 stories carry "## Cuándo usarlo"

stories tsc (aislado):  EXIT=0
build-storybook:        └  Storybook build completed successfully  ·  EXIT=0
regression_guard (vitalia/frontend tsc --noEmit):  EXIT=0
```

`build-storybook` emitió advertencias de tamaño de asset del bundler (>244 KiB) — son advisories de
performance web sobre tooling de dev, no fallos de gate (EXIT=0).

### Baseline del paquete (NO en scope · `forbidden_to_touch: src/**`)

`cd core/@luana/ui-kit && npx tsc --noEmit` sale 2, pero los 159 errores son **pre-existentes**:
`src/timezone-select.tsx` (`Intl.supportedValuesOf` por lib-target) + `tests/*` (matchers jest-dom).
`tsconfig` incluye `src/**` + `tests/**` pero **no** `stories/**`. Las 4 stories type-checkean GREEN en
aislado (EXIT=0). Delta introducido por T-2 al tsc del paquete = **0**.

## Skills consultados

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `frontend-expert` | host de render vivo (Storybook) + Tailwind v4 + autodocs en monorepo pnpm | `@storybook/nextjs` (router hooks mockeados); `@source "../src"` ancho (un `@source` angosto purga silenciosamente `dark:`/arbitrary); `@theme inline` para generar utilidades de token (sin esto, `--card` existe pero `bg-card` no se emite) |
| `frontend-visual-fidelity` (rule D1 + design-system-canon §2.1-2.4) | las stories deben renderizar el lego canónico, no maquetas | Las 4 stories importan el componente real de `../src/`; data realista LatAm (doctores), Spanish neutro (tuteo); `EntityPicker` agnóstico de query-lib (mock `searchFn`, sin `QueryClientProvider`) |
| `vitalia-design-system` (mirror del setup probado) | replicar el wiring Storybook que ya funciona en `vitalia/frontend/.storybook` | mismo patrón nextjs + addon-a11y + autodocs:"tag"; preview.css self-contained (sin `@config` cross-brand — prohibido para paquete platform) |

## Bugs de componente observados

Ninguno. Las 4 piezas (EntityWorkspaceLayout, EntitySubNavBar, EntityInfoCard, EntityPicker) renderizan
correctamente en sus modos master/detalle/loading/empty sin requerir cambios en `src/`. (Si un batch
posterior revela un bug → se anota acá como ticket aparte, **nunca** se arregla editando `src/`.)

## Notas para el auditor

- `production_code: false` — Storybook + stories + gates son tooling de dev, fuera del bundle de runtime de toda marca.
- `forbidden_to_touch` respetado: cero edición de `core/@luana/ui-kit/src/**` y `{brand}/frontend/src/**`.
- Las stories viven en `core/@luana/ui-kit/stories/` (nuevo dir), no co-locadas en `src/`.
- `verification_nature: técnica` → verificación-por-efecto: `build-storybook` GREEN ES el efecto (type-check + bundle del preview.css real).
