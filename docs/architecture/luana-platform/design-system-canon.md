# Design System Canon — contratos RATIFICADOS (binding cross-brand)

**Status:** ratified (Chris 2026-06-08, vía showcase `vitalia-ds-showcase`, 8 rondas `/po-ux`) · **Owner:** `/pm-vitalia` · **Scope:** platform-wide (todas las marcas) · **Home de los componentes:** `core/@luana/{design-tokens, ui-kit}`

> **Qué es este doc:** el **contrato binding** del design system — las decisiones que `/po-ux` (mockups), `/architect` (ready package), `/dev-team` (build) y `/auditor` (review) DEBEN respetar **tal cual**, sin reinterpretar. Es el SSoT durable que sobrevive al archivado de la story que lo originó (`user-story-no-es-ssot`).
>
> **Mapa de homes (1 SSoT por concern · no se duplica · cement 2026-06-25 ADR-016):**
> - **ADR-014** = *doctrina estructural* (las 5 capas + por qué enforcement mecánico).
> - **ADR-016** = *gobernanza de inventario* (reuse/extend/create + vocabulario `DESTINO`/`ACCIÓN` + toolkit de extensión + contrato de fidelidad por actor). ★ apuntá acá para **"¿reúso, extiendo o creo?"**.
> - **Este doc (canon)** = los *contratos concretos* de cada componente (el QUÉ). ★ apuntá acá para **"¿qué hace / cómo se ve la pieza?"**.
> - **`.claude/rules/frontend-visual-fidelity.md`** = el *enforcement* (quién verifica qué · el bucle de 5 actores).
> - **proposal 2026-06-07-design-system-homologation** = el *plan + lift* (Fases 0-3).
> - ~~`design-system-inventory-best-of-best.md`~~ · ~~`design-system-homologation-HANDOFF.md`~~ · ~~`storybook-component-inventory-to-be.md`~~ = **genesis-docs archivados** (su contenido vivo se consolidó en ADR-016 + este canon). La fuente visual es **Storybook** (`:6007`), no la `showcase.html` (espejo derivado, histórico).

---

## 0. Autoridad (la cadena que hace imposible el drift)

```
Tokens (1 fuente)  →  Átomos  →  Layout-primitives  →  Page archetypes  →  Shell-organism (chrome)
core/@luana/design-tokens     core/@luana/ui-kit ──────────────────────────────────────────┘
```

**Regla de composición (HARD):** una hoja se **ARMA** desde átomos + layout-primitives + archetype. **NUNCA** se maqueta a mano con `<div>` + clases sueltas, ni se reinventa una primitiva que ya existe. Tokens = única fuente de spacing/radius/tipografía/color. (ADR-014 §Decisión.)

---

## 1. Contenedor HOJA — lineamientos (cement 2026-06-08)

Toda superficie user-reachable que renderiza dentro del panel del shell es una **hoja**. Lineamientos:

1. **100% del ancho · full-responsive.** Sin `max-width` en la hoja. Los grids reflúyen (`auto-fill/auto-fit` + `minmax`). Campos pareados colapsan a 1-col en viewport chico.
2. **Franjas de navegación de la hoja = FULL-BLEED.** Las barras N3 (entity-subnav / sub-sub-tabs) van **edge-to-edge**, `bg-card` + `border-bottom`, **sticky** — mismo lenguaje visual que Ribbon (N1) / SubTabs (N2). **NUNCA** dentro de una card con borde redondeado.
3. **Contenido en PageContainer.** El cuerpo de la hoja usa `PageContainer` (padding interior estándar `1.25rem 1.5rem`) + `PageContentStack` (espaciado vertical uniforme). NO `<div p-4/p-6/p-8>` sueltos.
4. **Padding:** las franjas NO llevan padding de contenido (solo el del strip) · el contenido SÍ (PageContainer). Strips sticky arriba.

---

## 2. Contratos de componentes RATIFICADOS

### 2.1 · N3 Lista/Detalle — `EntityWorkspaceLayout` (patrón ÚNICO)

Patrón único para **TODA** lista/detalle (doctores, servicios, leads, ICPs, cuentas…). **1-panel, URL-driven** (NO 2-columnas persistente).

- **Master (sin entidad seleccionada):** grilla **full-width de `EntityInfoCard`** (§2.3) + `PageHeader` + `Toolbar/FilterBar` (búsqueda + filtros). La grilla **es el contenido del root**. Click en una caja → navega (cambia URL) al workspace.
- **Detalle (entidad seleccionada):** `EntitySubNavBar` (§2.2, franja full-bleed) arriba + contenido del leaf activo full-width abajo (`leaf-body` con PageContainer padding).
- SSR-safe + skeleton **store-free** (G2). `activeLeaf` derivado de la URL, nunca de store.
- Contrato de props (generalizar a `@luana/ui-kit`): `{ entity|null, leaves[], rootHref, rootLabel, isLoading, onAddAffordance, children }`.

### 2.2 · `EntitySubNavBar` — la franja N3 como TERCER RIBBON

- **Full-bleed strip** (no card): `bg-card` + `border-bottom` + **sticky top:0** + `border-radius:0`. Mismo lenguaje que Ribbon/SubTabs.
- Composición: `[ ‹ {RootLabel} ]` (root-pill con **flechita ←** → vuelve a la grilla master) · **EntityPicker** (§2.4 — identidad de la entidad = selector) · **leaves** (secciones de ESA entidad: Perfil/Agenda/Servicios…).
- Sin botón "back" separado: el root-pill `‹ {RootLabel}` ES la vuelta.
- a11y: `role=tablist` + roving tabindex + flechas (←→/Home/End).

### 2.3 · `EntityInfoCard` (Opción B)

- Grid responsivo `auto-fill / minmax(250px, 1fr)` → 3-5 por fila según ancho (reflúye solo).
- **Media circular** (avatar iniciales o ícono agent-color). Acento del agente arriba. Título + subtítulo (badge).
- **Fila de métricas repartida a lo ancho** (columnas iguales, centradas, banda superior/inferior) + footer (chip de estado).
- **Card entera clickeable** (cursor + hover + focus por teclado + selección). **Kebab `⋮`** arriba-derecha (`stopPropagation`) → menú contextual (Editar / Ver perfil|landing / Duplicar / Abrir conversación / Eliminar-danger).
- Variantes obligatorias: `EntityInfoCardSkeleton` + `EntityInfoCardEmpty`.

### 2.4 · `EntityPicker` — selector de entidad (cambiar sin volver atrás)

El nombre de la entidad en la franja es un **selector `▾`** que permite cambiar de entidad **sin volver a la grilla**. **Cimentado para escala (200+):**

- **Buscador** arriba del dropdown — en el build real: **server-side, debounced** (NO traer todo al cliente).
- **Fetch paginado** (cap inicial ~20, cursor) + **render windowed/virtualizado** (react-window/virtualizer) + **infinite-scroll o "cargar más"**.
- Empty state ("Sin resultados") · footer de conteo ("Mostrando N de M").
- a11y: `role=listbox/option`, combobox keyboard (↑↓/Enter/Esc), focus al search al abrir.
- ❌ Prohibido: cargar TODA la colección al cliente.

### 2.5 · `Select` canónico (Shadcn-style)

Reemplaza el `<select>` nativo del browser (feo, no-tokenizado). Componente custom:

- Trigger con borde tokenizado + **chevron `▾`** que rota al abrir + focus-ring.
- Panel estilizado (`bg-card`, shadow, radius) + items con hover + **check `✓` en la opción activa** + agent-color.
- ❌ Prohibido: `<select>` nativo en superficies de producto.

### 2.6 · Info agrupada + Autosave

- Contenedor `Group` + `GroupHeader` (chip "para qué" + estado de error semántico: borde rojo + campos faltantes inline).
- `use-autosave` **600ms + payload coalescing** (merge, evita pisar edits rápidos) + `flush()`.
- **UNA sola `FloatingAutosaveIndicator`** por **HOJA** (anclada al borde inferior de la **hoja** — el panel del shell —, centro, `role=status`). **Pertenece a la hoja, NUNCA a la página/viewport:** default `anchor="sheet"` (`absolute` al marco `relative` de la hoja, siempre pegada abajo, contenido corto o largo); `anchor="page"` (`fixed` al viewport) es escape hatch SOLO para el caso excepcional no-mapeado sin hoja contenedora. **Sin badge por-grupo** (redundante).
- **Barrita de color del agente** a la izquierda del grupo (marca de quién es la info).
- Layout: 1-col por defecto; **2-col solo si los campos están conceptualmente pareados** (color+tipografía, tratamiento+idioma).

### 2.7 · Page-primitives (capa 3-4)

`PageContainer · PageHeader · PageSection · PageContentStack · Toolbar · FilterBar (orden + view-toggle + búsqueda) · EmptyState · ErrorState (role=alert + retry) · ListPageSkeleton · FormPageSkeleton · Pagination · DetailLayout / FormLayout (1-col default; 2-col solo pareados)`. Toda página se arma de acá, no con `<div>` sueltos (~208 hoy a mano).

### 2.8 · Políticas de átomos (ratificadas)

- **Tooltip:** `ⓘ` con hover/focus, SOLO para lo no-obvio (info crítica va inline/hint, siempre visible) · accesible por teclado · NO solo-hover en mobile (tap-to-toggle). Componente = Shadcn Tooltip (Provider + Arrow + delay 0).
- **Color por agente:** dentro del módulo de un agente, la **acción primaria** adopta el color del agente (`--agent-active`); texto por contraste (Mateo amarillo→oscuro; Lucas negro→blanco). Lo **semántico NUNCA cambia** (destructivo rojo, éxito verde, advertencia ámbar). Lo **global/transversal** (topbar, Valeria, onboarding, Plataforma) usa `--primary` (cian de marca).

### 2.9 · Picks canónicos (de dónde sale cada cosa)

| Pieza | Canónico |
|---|---|
| N3 list/detail | `EntityWorkspaceLayout` + `EntitySubNavBar` (base nicolify) → `@luana/ui-kit` |
| Autosave | `use-autosave` 600ms+coalesce + `FloatingAutosaveIndicator` (base vitalia) |
| Átomos | `@luana/ui-kit` mergeando lo mejor: input/textarea/badge (vitalia) + dropdown/tooltip (nicolify) |
| EntityInfoCard | Opción B sobre base `StaffCard` (vitalia) + ícono agent-color (nicolify IcpCard) |
| Grupo info | `Group`/`GroupHeader` (base nicolify) |

### 2.10 · Dark-mode wiring (contrato del consumer · cement 2026-06-16)

`@luana/ui-kit` shippea componentes con `dark:` variants de Tailwind (`AutosaveBadge`, `alert`, `chart`, `FloatingAutosaveIndicator`, + chrome del shell), pero **NO shippea CSS ni `@custom-variant`** — el wiring de dark vive en el `globals.css` de cada consumer (limitación Tailwind v4 · ver §6.8). El kit define el contrato; el consumer lo cumple. **Contrato HARD que TODO consumer del kit cumple en su `globals.css`:**

1. **Toggle:** next-themes con `attribute="data-theme"` → pone `<html data-theme="dark">`. (Requiere `<ThemeProvider attribute="data-theme">` montado en `providers.tsx` — sin él el toggle es no-op.)
2. **`@custom-variant dark`** re-apuntando `dark:` al selector `[data-theme="dark"]`/`.dark`. Por default Tailwind v4 manda `dark:` a `@media (prefers-color-scheme)` e **ignora el atributo** → los `dark:` del kit no conmutan con el toggle. Mecanismo canónico: `@custom-variant dark (&:where(.dark, .dark *, [data-theme="dark"], [data-theme="dark"] *))` (v4-puro, 1 línea, sin `tailwind.config`).
3. **`@source "<rel>/core/@luana/ui-kit/src"`** (el `src` COMPLETO, no un subdir). Los molecules consumidos (`EntityWorkspaceLayout`/`EntitySubNavBar`/`Group`/`AutosaveBadge`) viven en `ui-kit/src` raíz, fuera de `organism/shell`; un `@source` angosto purga sus clases `dark:`/arbitrary **en silencio** (tsc verde, visual roto).
4. **Overrides de CSS-var dark** (token swap) bajo el **mismo** par de selectores (`.dark, [data-theme="dark"]`), no solo `.dark`.

**Equivalente legacy aceptado (vitalia):** `@config "../../tailwind.config.ts"` + `darkMode: ["class", '[data-theme="dark"]']` produce el **mismo efecto** que `@custom-variant`. Es válido — el gate asserta el **EFECTO** (`dark:` responde a `[data-theme="dark"]`/`.dark`, no a `prefers-color-scheme`), NO el mecanismo exacto. Migrar vitalia a `@custom-variant` es follow-up opcional, no urgente.

**Gate (replicable por marca):** `{brand}/frontend/src/__tests__/architecture/` asserta el contrato leyendo `globals.css` (+ `tailwind.config.ts` si usa `@config`): dark variant → `[data-theme="dark"]`/`.dark` por cualquiera de los dos mecanismos + `@source` escanea el `ui-kit/src` completo. nicolify + vitalia lo tienen; cada marca nueva lo replica. Es lo que faltó y dejó pasar la regresión (origen: nicolify ds-adoption G round-1, fix `b09bc9dc`).

---

## 3. Binding — quién consume el canon y CÓMO (enforcement)

| Actor | Obligación (HARD) |
|---|---|
| **`/po-ux`** | Los mockups se **componen partiendo de Storybook** (`@luana/ui-kit` = SSoT visual · §5 · átomos + layout-primitives + archetypes REALES, tokens de la fuente única) — NO se inventan primitivas ni layout a mano. El mockup ratificado = lo que se construye. Cita este canon §5; pieza net-new → PROPONE + PROMUEVE al kit. (El `mockup-kit`/`_shared.css` quedó **SUPERSEDED** — ver §5.) |
| **`/architect`** | El `03-arch.md` + `04-validators.yaml` referencian el canon: toda superficie list/detail usa `EntityWorkspaceLayout`; toda página se arma de page-primitives; selects = `Select` canónico; etc. Declara los gates mecánicos (lint no-arbitrary + arch-test no-div-layout) en validators. |
| **`/dev-team`** | Construye **desde** `@luana/ui-kit` (único lego). Prohibido maquetar a mano una primitiva existente o usar `<select>` nativo / arbitrary-values. |
| **`/auditor`** | Verifica **composición** (que se usó el canon), no estilo a mano. `frontend-visual-fidelity` D1 = mecánico (lint/arch-test), no criterio. |

**Gates mecánicos** (los construye el programa — Fases 0-2): eslint `no-arbitrary-value` (spacing/radius/font-size/color-hex) · arch-test FE (prohíbe `<div>` de layout donde hay primitiva + hex/px hardcoded · ratchet shrink-only) · `/showcase` route (descubribilidad + guard de regresión).

---

## 4. Estado del programa (qué falta construir)

| Fase | Story | Estado | Contenido |
|---|---|---|---|
| **0+1+2** | **`core-ds-foundation`** (consolidada 2026-06-08) | refining (/pm-vitalia → /architect) | **TODO el build en una story:** escala tokens + eslint no-arbitrary (Fase 0) · ~10 layout-primitives + archetypes + `EntityWorkspaceLayout`/`EntitySubNavBar`/`EntityInfoCard`/`EntityPicker` + `/showcase` route (Fase 1) · arch-test FE + D1 mecánico (Fase 2). **Bindings de skills/rule = YA hechos 2026-06-08 (no re-armar).** `Select`/`tooltip`/`AutosaveBadge` = ya en `@luana/ui-kit` (consumir). |
| 3 | `{brand}-ds-adoption` ×N | ⬜ a armar (aparte, por marca) | adopción COMPREHENSIVA por marca (vitalia→nicolify→comunify), migrar pantallas existentes + encender el lock |

---

## 5. Storybook = SSoT visual (render vivo · R-FID · cement 2026-06-22, ratificado Chris)

El catálogo de los **componentes REALES** vive en **Storybook** (`core/@luana/ui-kit`), construido con `pnpm --filter @luana/ui-kit build-storybook` → `storybook-static/` (HTML real: cada story = DOM del componente real que la marca consume vía `@luana/ui-kit`) o servido en dev (`pnpm --filter @luana/ui-kit storybook --port 6007`). **Es la ÚNICA fuente de verdad visual de la plataforma** — "lo que ves en Storybook = lo que se programa", por construcción (cero drift). Cada story trae tab **Docs** (props reales + "Cuándo usarlo"/"Cuándo NO").

**SUPERSEDED (mecanismos muertos — el "HTML que miente" que esto mata):** `_shared.css` espejo · mockup-kit CSS · `preview.html` estático · `vitalia-ds-showcase/*.html` · el protocolo per-brand `shell-mockup-per-component.md` (ADR-vitalia-003). Ya no se maqueta a mano ni se copia CSS: se parte del componente REAL renderizado.

### El bucle de diseño UI (los 5 actores lo siguen — binding)

1. **Partir de Storybook.** `/po-ux` y `/ux-agentico`, al maquetar, **arrancan del set de Storybook** — el TSX se consume como **HTML renderizado** (`storybook-static/` o iframe `…/iframe.html?id=<story>&viewMode=story`) para componer el mockup desde la **misma base que el build**. NO se inventa CSS ni se copia `_shared.css`.
2. **No limitarse (Storybook es el piso, no el techo).** Si falta una pieza, o existe algo genuinamente **mejor**, se **PROPONE** (mockup + justificación + test del 2º consumidor). El catálogo no congela el diseño: lo encauza.
3. **Promover de vuelta.** Lo que se usa y prueba bien se **PROMUEVE a `@luana/ui-kit` + su story** (vía `core-ds-*` / flujo engine `/pm-vitalia`) para que **futuras historias lo reusen**. Cero "local" que driftee — una pieza net-new que queda en `features/{m}/` sin promover es deuda.
4. **`/architect` cita la story.** El ready package (`03-arch.md § FE` + `04-validators.yaml`) **nombra qué story usar + link**; una pieza net-new se marca `PROMOTE` (deliverable del ticket = crear el componente en `@luana/ui-kit` + su story ANTES del merge).
5. **`builder-frontend` construye DESDE la story citada** (único lego = `@luana/ui-kit`) + promueve el net-new al kit con story. **`auditor-frontend` verifica composición** contra Storybook + que el net-new se promovió con story (no quedó local) → si no, CHANGES_REQUESTED.

> SSoT enforce-able de este bucle: `.claude/rules/frontend-visual-fidelity.md` (lo citan los 5 actores). (R-FID, ADR-014 §5.)

---

## 6. Ejemplos de código (referencia de implementación — refleja el showcase ratificado)

> Estos snippets son el **contrato de implementación** para `/dev-team` (qué construir en `@luana/ui-kit`) y la **base de composición** para `/po-ux` (el mockup compone ESTAS piezas). Tailwind + tokens; "lo que se ve = lo que se programa".

### 6.1 · Tokens — fuente única (cada eje se consume de acá, NUNCA arbitrary)

```css
/* core/@luana/design-tokens → globals.css de cada marca importa esta escala (no la redefine) */
:root{
  --radius: .625rem;                          /* ÚNICO --radius (resolver el 0.5 legacy) */
  --background:0 0% 100%; --foreground:240 10% 4%; --card:0 0% 100%;
  --muted:240 5% 96%; --muted-foreground:240 4% 46%;
  --primary:198 99% 49%;                       /* cian de marca = global/transversal */
  --border:240 6% 90%; --input:240 6% 90%; --ring:198 99% 49%;
  /* color por agente (la acción primaria del módulo usa --agent-active) */
  --agent-lisa:156 100% 41%; --agent-mateo:53 99% 51%; /* … */
}
/* spacing/radius/font-size/color SOLO de la escala → eslint no-arbitrary los lockea */
```

### 6.2 · Contenedor HOJA — layout-primitives (full-bleed strip + PageContainer)

```tsx
// Toda hoja list/detail se ARMA así — NUNCA <div> de layout sueltos
<EntityWorkspaceLayout entity={entity} leaves={leaves} rootHref="/lisa/staff" rootLabel="Especialistas">
  {/* leaf activo — va dentro de PageContainer (padding estándar) */}
  <PageContainer>
    <PageContentStack>
      <Group title="Identidad">…</Group>
    </PageContentStack>
  </PageContainer>
</EntityWorkspaceLayout>
```

```css
/* La FRANJA N3 = tercer ribbon full-bleed (NO card redondeada) */
.entity-sub-nav{ position:sticky; top:0; z-index:12;
  background:hsl(var(--card)); border-bottom:1px solid hsl(var(--border)); border-radius:0;
  min-height:46px; display:flex; align-items:center; padding:0 1.5rem; }   /* full-bleed */
.page-container{ padding:1.25rem 1.5rem; }                                  /* contenido */
.page-content-stack{ display:flex; flex-direction:column; gap:1.5rem; }
/* 100% ancho, sin max-width; grids reflúyen */
.entity-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:.875rem; }
```

### 6.3 · `EntitySubNavBar` (root-pill con flechita + EntityPicker + leaves)

```tsx
export function EntitySubNavBar({ rootHref, rootLabel, entity, leaves, activeLeaf, agentSlug, onEntityChange }: Props){
  return (
    <nav role="tablist" className="entity-sub-nav">            {/* full-bleed sticky */}
      <button role="tab" onClick={() => router.push(rootHref)}  {/* ‹ vuelve a la grilla master */}
        className="entity-root inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md font-semibold">
        ‹ {rootLabel}
      </button>
      <EntityPicker entity={entity} agentSlug={agentSlug} onChange={onEntityChange} />  {/* ▾ cambia sin volver */}
      {leaves.map(l => (
        <LeafTab key={l.id} leaf={l} active={l.id === activeLeaf} agentSlug={agentSlug} />
      ))}
    </nav>
  );
}
```

### 6.4 · `EntityPicker` — buscar + paginado + windowed (cimentado 200+)

```tsx
// ❌ NUNCA traer toda la colección. Búsqueda server-side debounced + fetch paginado + render windowed.
export function EntityPicker({ entity, agentSlug, onChange }: Props){
  const [q, setQ] = useState("");
  const dq = useDebouncedValue(q, 200);                                  // debounce
  const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({       // fetch paginado (cap ~20, cursor)
    queryKey: ["entities", "picker", dq],
    queryFn: ({ pageParam }) => api.searchEntities({ q: dq, cursor: pageParam, limit: 20 }),
    getNextPageParam: p => p.nextCursor,
  });
  const items = data?.pages.flatMap(p => p.items) ?? [];
  return (
    <Popover>
      <PopoverTrigger className="entity-picker">          {/* avatar + nombre + ▾ */}
        <Avatar slug={agentSlug}>{entity?.initials}</Avatar><span>{entity?.name}</span><ChevronDown/>
      </PopoverTrigger>
      <PopoverContent role="listbox" className="w-72">
        <Input value={q} onChange={e=>setQ(e.target.value)} placeholder="Buscar…" autoFocus/>
        <Virtuoso style={{height:248}} data={items}                    {/* render windowed/virtualizado */}
          endReached={() => hasNextPage && fetchNextPage()}            {/* infinite-scroll / lazy */}
          itemContent={(_, it) => <EntityPickerItem item={it} onSelect={onChange}/>}/>
        {items.length === 0 && <Empty>Sin resultados</Empty>}
      </PopoverContent>
    </Popover>
  );
}
```

### 6.5 · `EntityInfoCard` (Opción B) — clickeable + kebab

```tsx
export function EntityInfoCard({ entity, accentSlug, actions, onClick }: Props){
  return (
    <article role="button" tabIndex={0} onClick={onClick}
      className="relative bg-card border border-t-4 rounded-xl cursor-pointer hover:shadow-md focus-visible:outline-2"
      style={{ borderTopColor:`hsl(var(--agent-${accentSlug}))` }}>
      <Kebab actions={actions} className="absolute top-2 right-2" />     {/* stopPropagation */}
      <div className="p-4 flex flex-col gap-2.5">
        <div className="flex items-center gap-2.5">
          <Avatar slug={accentSlug} className="rounded-full">{entity.initials}</Avatar>  {/* circular */}
          <div className="min-w-0"><h3 className="truncate font-semibold">{entity.name}</h3>
            <p className="text-xs text-muted-foreground">{entity.subtitle}</p></div>
        </div>
        <MetricsRow metrics={entity.metrics} />                          {/* repartida a lo ancho */}
      </div>
      <CardFooter><StatusChip status={entity.status}/></CardFooter>
    </article>
  );
}
// + EntityInfoCardSkeleton + EntityInfoCardEmpty obligatorios
```

### 6.6 · `Select` canónico (reemplaza `<select>` nativo)

```tsx
// ❌ Prohibido <select> nativo. ✅ Shadcn Select (trigger + chevron + check en activo)
<Select value={value} onValueChange={setValue}>
  <SelectTrigger className="h-9">                  {/* borde tokenizado + chevron ▾ */}
    <SelectValue placeholder="Todas las especialidades" />
  </SelectTrigger>
  <SelectContent>
    {options.map(o => <SelectItem key={o.id} value={o.id}>{o.label}</SelectItem>)}  {/* ✓ en activo */}
  </SelectContent>
</Select>
```

### 6.7 · Autosave — 1 píldora flotante (sin badge por-grupo)

```tsx
export function AgentScopedForm({ agentSlug }: Props){
  const { register, isSaving, isSaved } = useAutosave({ debounceMs:600, coalesce:true, onSave: api.patch });
  return (
    <>
      <Group title="Identidad" agentStrip={agentSlug}>      {/* barrita de color del agente a la izq */}
        <Field {...register("name")} label="Nombre" />       {/* sin botón Guardar */}
      </Group>
      <FloatingAutosaveIndicator saving={isSaving} saved={isSaved} role="status" />  {/* UNA por hoja (anchor sheet) */}
    </>
  );
}
```

### 6.8 · Dark-mode wiring — snippet canónico del consumer (§2.10)

```css
/* {brand}/frontend/src/app/globals.css */
@import "tailwindcss";

/* (2) dark: responde al toggle data-theme/.dark, NO a prefers-color-scheme */
@custom-variant dark (&:where(.dark, .dark *, [data-theme="dark"], [data-theme="dark"] *));

/* (3) JIT escanea el kit COMPLETO (molecules fuera de organism/shell se purgan si no) */
@source "../../../../core/@luana/ui-kit/src";

@layer base {
  /* (4) token swap bajo el MISMO par de selectores que (2) */
  .dark,
  [data-theme="dark"] { --background: 240 18% 8%; /* … */ }
}
```

> **Por qué no lo shippea el kit (pieza-3 evaluada, descartada 2026-06-16):** `@custom-variant`/`@source` son directivas del **CSS entry** de Tailwind v4 — se procesan en el `globals.css` del consumer y `@source` resuelve relativo a ese archivo. No son re-exportables útilmente desde un paquete TS, y empaquetar un `.css` importable ahorraría ~2 líneas por marca a cambio de una superficie de export versionada + un `@source` con path relativo frágil. Las piezas 1 (contrato §2.10) + 2 (arch-test por marca) cierran el gap sin tocar `ui-kit/src` (sin bump del kit). vitalia usa el equivalente legacy `@config` + `tailwind.config.ts`.

## 7. Referencias

- `ADR-014-design-system-homologation.md` — doctrina (5 capas + enforcement mecánico)
- `docs/promotion-protocol/proposals/2026-06-07-design-system-homologation.md` — plan + lift (Fases 0-3)
- `design-system-inventory-best-of-best.md` — análisis best-of-best (file:line)
- `vitalia/docs/product/stories/vitalia-ds-showcase/` — origen ratificación (`checkpoint.md::ratified_decisions` + `mockups/showcase.html`)
- `.claude/rules/frontend-visual-fidelity.md` — D1/D2/D3 (bindea a este canon)
- `docs/promotion-protocol/proposals/2026-06-16-ui-kit-dark-contract.md` — lift del contrato §2.10 (dark-mode wiring + arch-test replicable)
- `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` — `EntityWorkspaceLayout` (primera primitiva)
- `ADR-012-autosave-primitive-platform.md` — patrón hermano
- `core/@luana/{design-tokens, ui-kit}` — homes
