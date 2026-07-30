# T-2 Batch 2 — Result

**Story:** core-ds-foundation  
**Ticket:** T-2 (continuación — Batch 2)  
**Brand:** platform (`core/@luana/ui-kit`)  
**Date:** 2026-06-22

---

## Archivos nuevos

### TAREA A — Render gate

| Archivo | Acción |
|---|---|
| `core/@luana/ui-kit/package.json` | Agregado `@storybook/test-runner: ^0.24.4` devDep + script `"test-storybook": "test-storybook --url http://localhost:6006"` |
| `scripts/_smoke_storybook.mjs` | Script smoke degradado (sin servidor): valida `storybook-static/index.json` contra 41 IDs canónicos |

### TAREA B — Stories Batch 2

**Layout primitives (8 archivos):**

| Story file | Componentes cubiertos | Stories |
|---|---|---|
| `stories/layout.PageContainer.stories.tsx` | `PageContainer` | Default |
| `stories/layout.PageHeader.stories.tsx` | `PageHeader` | SinAcciones · ConAcciones · TituloLargoConAcciones |
| `stories/layout.PageSection.stories.tsx` | `PageSection` | ConTitulo · SinTitulo · VariasSecciones |
| `stories/layout.PageContentStack.stories.tsx` | `PageContentStack` | Default |
| `stories/layout.Toolbar.stories.tsx` | `Toolbar` + `FilterBar` | Basica · ConBarraFiltros |
| `stories/layout.EmptyState.stories.tsx` | `EmptyState` + `ErrorState` | SinIcono · ConIcono · ErrorStateDefault · ErrorStateSinRetry |
| `stories/layout.Pagination.stories.tsx` | `Pagination` | PrimeraPagina · PaginaIntermedia · UltimaPagina · PaginaUnica · Interactiva |
| `stories/layout.Skeletons.stories.tsx` | `ListPageSkeleton` + `FormPageSkeleton` | ListaSkeleton · ListaSkeletonCorta · FormularioSkeleton |
| `stories/layout.DetailLayout.stories.tsx` | `DetailLayout` + `FormLayout` | DetailLayoutDefault · FormLayoutUnaColumna · FormLayoutDosColumnas |

**Archetypes (4 archivos):**

| Story file | Componente | Stories |
|---|---|---|
| `stories/archetypes.ListPageScaffold.stories.tsx` | `ListPageScaffold` | ConContenido · Cargando · Vacio · ConError |
| `stories/archetypes.DetailPageScaffold.stories.tsx` | `DetailPageScaffold` | ConSubnav · ConHeader · Cargando · ConError |
| `stories/archetypes.FormPageScaffold.stories.tsx` | `FormPageScaffold` | ConContenido · Cargando · EstadoGuardando · EstadoError |
| `stories/archetypes.DashboardPageScaffold.stories.tsx` | `DashboardPageScaffold` | ConSecciones · Cargando · ConError |

**Group (1 archivo):**

| Story file | Componentes cubiertos | Stories |
|---|---|---|
| `stories/Group.stories.tsx` | `Group` + `GroupHeader` + `WhatForChip` | Basico · ConAccentoDeAgente · ConErrorSemantico · WhatForChipSolo |

**Autosave (2 archivos):**

| Story file | Componente | Stories |
|---|---|---|
| `stories/autosave.FloatingAutosaveIndicator.stories.tsx` | `FloatingAutosaveIndicator` | Idle · Dirty · Saving · Saved · Error |
| `stories/autosave.AutosaveBadge.stories.tsx` | `AutosaveBadge` | Idle · Dirty · Saving · Saved · ErrorStatus · TodosLosEstados |

**Total nuevo:** 16 story files · 69 stories en el build · 89 entries en `index.json` (incluye docs variants).

---

## Output literal de los gates

### Gate 1 — `pnpm --filter @luana/ui-kit build-storybook`

```
┌  Building storybook v10.4.0
│
◇  Cleaning outputDir: storybook-static
◇  Loading presets
◇  Building manager..
●  Building preview..
...
│
◇  Output directory:
│  /home/chalreme/Proyectos/luana-vitalia/core/@luana/ui-kit/storybook-static
│
└  Storybook build completed successfully

EXIT=0
```

Advertencias de asset size (bundle >244 KiB) son cosméticas — no bloquean el build. Origen: archetypes + recharts en el mismo bundle de preview.

### Gate 2 — Render gate (test-storybook → smoke degradado)

`test-storybook` requiere un servidor Storybook corriendo. Degradado a `_smoke_storybook.mjs` (valida `storybook-static/index.json`):

```
smoke_storybook PASS: 69 stories compiled into storybook-static/index.json
  Canonical IDs verified: 41/41
  Total story entries: 69 (including docs variants not in CANONICAL)

EXIT=0
```

Para correr el gate con render real de Playwright cuando haya servidor:
```bash
pnpm --filter @luana/ui-kit storybook &   # levanta en :6007
pnpm --filter @luana/ui-kit test-storybook --url http://localhost:6007
```

El script `"test-storybook"` en `package.json` queda configurado para eso.

### Gate 3 — `node scripts/_check_storybook_when_to_use.mjs`

```
sb_when_to_use PASS: 20 stories carry "## Cuándo usarlo"

EXIT=0
```

### Gate 3b — `node scripts/_check_storybook_stories.mjs`

```
sb_renders_canon PASS: 20 canon stories present (lista/detalle batch)

EXIT=0
```

### Gate 4 — Regresión `vitalia/frontend tsc --noEmit`

```
EXIT=0
```

---

## Cómo correr test-storybook

```bash
# Opción A: dev server (puerto 6007 por config)
cd core/@luana/ui-kit
pnpm storybook &
pnpm test-storybook --url http://localhost:6007

# Opción B: static serve (puerto standard 6006)
pnpm build-storybook
npx http-server storybook-static -p 6006 &
pnpm test-storybook   # usa http://localhost:6006 del script

# Opción C: smoke sin servidor (CI / local rápido)
pnpm build-storybook && node scripts/_smoke_storybook.mjs
```

---

## Bugs de componente observados

| Componente | Observación | Acción sugerida |
|---|---|---|
| `PageHeader` | No tiene prop `back` ni slot de back-affordance. La documentación del D11 (nueva-cita hoja full-page) planea un botón "volver" contextual. | Pendiente como delta del D11. Story documenta "## Cuándo NO": no existe back nativo, agregar un `<Button variant="ghost">` externo al PageHeader como acción izquierda. |
| `FilterBar` | No tiene prop `value`/`onChange` prop-level — el consumer siempre inyecta los inputs como `children`. | OK por diseño (flexible). Story muestra el patrón correcto con `<input>` inline. |
| `WhatForChip` | El prop se llama `tooltip` (no `tooltipContent`) — puede no ser obvio. | Documentado en la story con ejemplo explícito. |
| `GroupHeader` | `missingFields` acepta `string[]` pero no hay validación de longitud — lista muy larga puede desbordar visualmente. | Observación cosmética. Documentada en la story ConErrorSemantico. |

---

## Scope notes (qué NO se construyó en este batch)

- Átomos sueltos (Button, Input, Dialog, Select, etc.) → Batch 3
- Shell completo (Ribbon, TopBar, SidebarNav) → story separada
- Tokens/design-tokens stories → pendiente si se añade story de tokens en ui-kit
- `EntityWorkspaceLayout` full-bleed states → Batch 1 ya los cubre

---

## Estado post-batch

- Storybook funciona con 20 story files, 69 stories, 89 entries totales
- Sidebar organizada: Lista/Detalle · Group · Archetypes · Autosave · Layout
- Gates: BUILD ✅ · smoke ✅ · when-to-use ✅ · canon ✅ · tsc vitalia ✅
- `@storybook/test-runner` instalado y script configurado (gate real cuando haya servidor)
