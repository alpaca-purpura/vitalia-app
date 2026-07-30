# Design System — Inventario "best of best" (para homologar TODO antes del build)

> **★ ARCHIVADO (génesis) 2026-06-25 — homes vivos: [ADR-016](ADR-016-design-system-inventory-governance.md) + `design-system-canon.md`. La auditoría de paridad 2026-06-25 (`core-ds-foundation/chris-input.md`) reemplaza este catálogo manual.**
>
> **⚠️ Catálogo histórico (2026-06-07).** Lo construido vive ahora en `core-ds-foundation` + **`design-system-canon.md § 5` (Storybook = SSoT visual)**. El "Mockup-kit para /po-ux" derivado de `_shared.css` que proponía este doc quedó **DESCARTADO** — Storybook-only: `/po-ux` parte del HTML de las stories `@luana/ui-kit`, no de un mockup-kit CSS espejo (que driftea). El resto (átomos/archetypes/Storybook como catálogo vivo) sigue vigente como referencia.

> **Para revisión de Chris antes de dar OK.** Owner: `/pm-luana`. Origen: pedido Chris 2026-06-07 (ampliar Fase 0 a homologación completa + plantillas obligatorias por átomo + mismas plantillas en `/po-ux` para que el mockup = lo construido). Método: 5 catalogadores read-only barrieron vitalia+nicolify+comunify+`@luana/ui-kit` y extrajeron el mejor de cada arquetipo (con `file:line`). **Cero código nuevo todavía** — esto es el catálogo para que decidas qué se vuelve canónico.

> Complementa: ADR-014 (doctrina) · proposal 2026-06-07 (plan core+lift) · `core-ds-foundation/01-spec.md` (Fase 0 = el lock). Este doc llena el "muéstrame todo y saquemos lo mejor".

---

## Cómo leer esto

Por cada **capa** y **arquetipo**: qué existe hoy (variantes dispersas) → **el mejor** (con por qué + path) → **la plantilla canónica** que el dev y el `/po-ux` tomarán de base. Al final: el mecanismo de "plantilla obligatoria" + cómo se ata `/po-ux` + la reestructura del programa.

---

## CAPA 1 · Tokens (spacing/radius/typo/color) — recap Fase 0

Ya cubierto por `core-ds-foundation/01-spec.md`. Resumen: **spacing** se consolida (idéntico cross-brand, 4px-base) en `@luana/design-tokens`; **radius/typo/color** = valores per-brand sobre nombres compartidos; el lock eslint prohíbe arbitrary en {spacing,radius,font-size,color-hex}. **Hallazgo bueno:** los átomos de `@luana/ui-kit` ya son 100% token-based (cero hex/px crudo) — el drift NO está en los átomos, está en el **contenido maquetado a mano** (capas 3-4) y en los **arbitrary sueltos** de features.

---

## CAPA 2 · Átomos — `@luana/ui-kit` es la fuente, pero está desincronizado

**Estado:** `@luana/ui-kit` tiene ~21 átomos, todos token-based + CVA + Radix + z-index centralizado. **Es el canónico.** Problema: **desincronización en 3 direcciones.**

### 2a · Versión de marca MEJOR que la del core → liftear de vuelta
| Átomo | Mejor versión | Por qué |
|---|---|---|
| `input` | vitalia `components/ui/input.tsx:7-21` | shadow-xs + selection styling + estados focus completos (core es más pobre) |
| `textarea` | vitalia `components/ui/textarea.tsx:5-21` | `field-sizing-content` + min-h-16 + focus states |
| `badge` | vitalia/nicolify `badge.tsx:9-28` | `rounded-md` (no `rounded-full`), tamaño 3, asChild — decisión de marca real |
| `dropdown-menu` | nicolify `dropdown-menu.tsx:64-85` | variante `destructive` en item + estructura anidada |
| `tooltip` | nicolify `tooltip.tsx:10-61` | `TooltipProvider` factory + Arrow + delay controlado |

### 2b · Átomos en core NO exportados a marcas → features los reinventan con `<div>`
`checkbox` · `switch` · `radio-group` · `card` · `popover` · `alert-dialog` (existen en `@luana/ui-kit/src/` pero las marcas no los consumen → se maquetan a mano).

### 2c · Átomos solo-en-marca (no aplica — el core los tiene todos)
Profundidad extra en core ya disponible: `calendar`, `command`, `table`, `progress`, `slider`, `loading-button`, `inline-editable`, `detail-panel`, `AutosaveBadge`, etc.

**→ Plantilla canónica por átomo:** UNA versión en `@luana/ui-kit` (mergeando la mejor de cada dirección 2a) + export completo + **lint prohíbe recrear un átomo localmente** + **showcase/Storybook** donde `/po-ux` y el dev VEN el set. *Esto es tu "plantilla obligatoria por átomo".*

---

## CAPA 3 · N3 lista/detalle (la "tercera franja") — ganador claro: nicolify

**Mejor:** nicolify `components/shared/shell-organism/EntityWorkspaceLayout.tsx` + `EntitySubNavBar.tsx`.
**Por qué:** un solo wrapper encapsula todo el patrón · SSR-safe + skeleton **store-free** (gate G2) · `activeLeaf` derivado de la URL (no de estado) · contrato de props mínimo y explícito · soporta `onAddAffordance` (crear entidad antes de navegar) · root como tab par (toggle master/detalle con `entity=null`).
**Peor (a migrar):** vitalia lo **cablea a mano por superficie** (`StaffWorkspaceShell`, `LeadWorkspace`) → reimplementa extracción de leaf + skeleton + back-link cada vez = drift.

**Plantilla canónica (contrato a generalizar a `@luana/ui-kit`):**
```
EntityWorkspaceLayout({ entity|null, leaves[], rootHref, rootLabel, isLoading, onAddAffordance, children })
  EntitySubNavLeaf = { id, label, href, isAddAffordance?, prefixEmoji?, avatarBgClass?, isPrimary? }
  entity=null ⇒ modo master (leaves disabled, root activo) · entity ⇒ modo detalle
```
*Regla:* toda superficie lista→detalle usa este wrapper, **nunca** cableado propio. (Ya alineado con el learning `2026-06-06-n3-entity-workspace-layout-from-nicolify`.)

---

## CAPA 3bis · Info agrupada con textbox autoguardados — 3 piezas, 3 ganadores

El patrón "secciones que agrupan campos que se guardan solos" (marca/voz, perfil doctor, ICP). Hoy: cada feature reinventa contenedor + hook + indicador.

| Pieza | Mejor versión | Por qué |
|---|---|---|
| **(A) Contenedor de grupo** | nicolify `IcpDatosForm.tsx:123-163` (`Group` + `GroupHeader`) | estado de error semántico (borde rojo + campos faltantes inline) + chip "para qué" + animación de borde |
| **(B) Mecanismo autosave** | vitalia `hooks/use-autosave.ts:112-139` | debounce 600ms + **payload coalescing** (merge — evita que edits rápidos se pisen) + `flush()` + ref-based (sin stale closure) |
| **(C) Indicador de guardado** | vitalia `components/shared/FloatingAutosaveIndicator.tsx:68-116` | píldora sticky abajo-centro, 1 por página (SSoT), `pointer-events-none`, accesible (`role=status`) |
| **(D) Regla de layout** | — | 1-col por defecto; **2-col solo si los campos están conceptualmente pareados** (tratamiento+idioma, color+tipografía) |

**Hoy en core:** `useAutosave` (2000ms, **sin coalescing**) + `AutosaveBadge` inline. → adoptar el coalescing de vitalia + el indicador flotante.
**→ Liftear a core:** `GroupContainer` (de nicolify) + `use-autosave` 600ms+coalesce (de vitalia) + `FloatingAutosaveIndicator` (de vitalia). Patrón hermano: ADR-012 (autosave primitive).

---

## CAPA 3ter · Cajas de entidad (doctores/servicios/leads/…) — anatomía única

10+ variantes, **todas distintas** (contenedor `article`/`li`/`div`/`section`; padding p-2.5→p-6; radius `rounded-xl`/none; estado vía borde-izq / badge / dot). Hay que unificar a **una lógica visual** con slots.

**Anatomía canónica `EntityInfoCard` (slots) + mejor ejemplo por slot:**
| Slot | Mejor ejemplo | Path |
|---|---|---|
| Media (avatar img+iniciales / ícono agent-color) | vitalia `StaffCard.tsx:68-85` · nicolify `IcpCard.tsx:110-119` | (íconos: caja agent-color JIT-safe) |
| Título (jerarquía + truncate) | vitalia `StaffCard.tsx:87-90` | |
| Subtítulo (badge especialidad/segmento) | vitalia `StaffCard.tsx:91-105` | |
| Grid de metadata (stats 3-col + fallback) | vitalia `StaffCard.tsx:109-134` | |
| Riel de estado (borde-izq 3-4px + class-map) | vitalia `ReEngagementCard.tsx:35-45` | mapa declarativo de color |
| Badge de estado | nicolify `IcpCard.tsx:122-128` | |
| Acción primaria (botón/Link agent-color) | vitalia `StaffCard.tsx:137-146` | |
| Estado seleccionado/hover | vitalia `ConversationItem.tsx:110-128` · `StaffCard.tsx:52-56` | |
| Empty/loading | vitalia `StaffCard.tsx:130-134` | + skeleton |

**→ Construir:** `EntityInfoCard` (slots configurables) + `EntityInfoCardSkeleton` + `EntityInfoCardEmpty` en `@luana/ui-kit`; padding p-4 estándar / p-3 compacto; radius `rounded-xl` grid.

---

## CAPA 4 · Scaffolding de página + estados universales — solo 2 de 10 existen

Hoy: solo `EmptyState` + `Skeleton` shipped. Los otros 8 **a mano** → ~208 `<div className="p-4|p-6|p-8">` repetidos + 4 paginaciones reimplementadas.

**Inventario canónico (~10 layout-primitives):**
| # | Primitiva | Responsabilidad | Hoy |
|---|---|---|---|
| 1 | `PageContainer` | padding interior del shell + stack vertical | a mano (SubTabContent p-7) |
| 2 | `PageHeader` | H1 + subtítulo + acciones (flex-between) | a mano (6+ páginas) |
| 3 | `PageSection` | H2 + bloque + semántica/a11y | a mano |
| 4 | `PageContentStack` | gestor de espaciado (space-y-6) | a mano |
| 5 | `Toolbar` | búsqueda + toggles + filtros (gap-2) | `AgendaToolbar` (1) |
| 6 | `FilterBar` | sort + view-mode + search | — |
| 7 | `EmptyState` | ícono + título + desc + CTA | **shipped** (vitalia `shell-organism/EmptyState.tsx:38-82`) |
| 8 | `ErrorState` | alerta + mensaje + retry (`role=alert`) | a mano (3-5) |
| 9 | `ListPageSkeleton` / `FormPageSkeleton` | skeleton N filas / N secciones | a mano (40+ `[1..N].map`) |
| 10 | `Pagination` | prev/next + indicador + estado | a mano (4 tablas) |
| + | `DetailLayout` / `FormLayout` | 1-col vs 2-col de contenido | a mano |

**Mejor EmptyState:** vitalia `shell-organism/EmptyState.tsx:38-82` (ya cross-brand con nicolify).

---

## El mecanismo "plantilla obligatoria" + atar `/po-ux` (tu req #1 y #2)

Para que el mockup termine siendo lo que se ve en dev, las plantillas son **una sola fuente** que consumen LOS DOS lados:

1. **Showcase/Storybook de `@luana/ui-kit`** = el catálogo vivo de átomos + layout-primitives + archetypes. El dev arma desde ahí; **prohibido maquetar a mano** (lint + arch-test). *Plantilla obligatoria = el átomo/primitiva canónica es el único lego.*
2. **Mockup-kit para `/po-ux`** derivado de los MISMOS tokens + el mismo set de componentes (HTML/CSS que referencia las clases tokenizadas y los archetypes). El `/po-ux` **no inventa** layout en el mockup: compone los mismos PageHeader/Section/EntityInfoCard/EntityWorkspaceLayout. → el mockup ratificado **ya es** la pantalla real.
3. **Page archetypes** (capa 4): scaffolds `list / detail / form / dashboard` donde se **rellenan slots**, no se maqueta de cero — el mismo archetype lo usa el mockup del `/po-ux` y el código del dev.
4. **Enforcement:** eslint no-arbitrary (Fase 0) + arch-test "no `<div>` de layout donde hay primitiva / no hex-px" + `frontend-visual-fidelity` D1 pasa de criterio a mecánico + skills `/po-ux`+`/dev-team`+`/auditor` apuntan al showcase como único set.

---

## Reestructura del programa (lo que cuelga de ADR-014 + proposal)

| Story | Capa | Contenido | Owner build |
|---|---|---|---|
| **`core-ds-foundation`** (Fase 0+1+2 CONSOLIDADA 2026-06-08) | 1-4 | tokens+lock eslint · ~10 layout-primitives + archetypes + EntityWorkspaceLayout/EntitySubNavBar/EntityInfoCard/EntityPicker + autosave(lift) + /showcase route · arch-test FE. **Contratos+código = `design-system-canon.md`.** Bindings skills/rule ya hechos. `Select`/`tooltip`/`AutosaveBadge` ya en ui-kit (consumir). | /architect→/dev-team |
| `{brand}-ds-adoption` (vitalia→nicolify→comunify) | adopción | adopción **comprehensiva** (todas las hojas) + encender lock | cada /pm-{brand} |

*(Caveat: programa multi-story sin contenedor 4-ejes; ancla = ADR-014 + proposal + este inventario.)*

---

## ADDENDUM 2026-06-07 (2ª ronda Chris) — mockups, fidelidad por construcción, requisitos nuevos

Chris pidió: (a) revisar también los **mockups** (no solo dev) — ¿parten de lo mismo? (b) ratificar **viendo HTML** confiando que "lo que veo ES lo que es"; (c) `/po-ux` siempre entrega **dentro del shell-organism**. Auditoría de mockups + hallazgos:

### Los mockups NO parten de lo mismo "por construcción"
| Grupo | Estado | Evidencia |
|---|---|---|
| servicios (catálogo/escalera/nuevo/workspace) + cuenta | **dentro del shell, fiel** | shell portado de `dual-mode-shell.html` SSoT; tokens HSL = `globals.css` |
| doctores.html + embudo-*.html (8) | **aislados, divergen** | sin shell; HEX hardcoded / Tailwind CDN inline; Valeria+Adrián como espacio bespoke |
| **TODOS los "fieles"** | **fidelidad por disciplina, no por construcción** | el `_shared.css` es un **espejo a mano** de `globals.css` → **ya driftó**: `--agent-mateo` 56° vs real 53° |

### El protocolo que ya existe (y hay que arreglar + liftear)
`ADR-vitalia-003` (rule `shell-mockup-per-component.md`) YA exige: mockup dentro del shell + `_shared.css` espejo de `globals.css` + wrapper portado verbatim. **Pero** es **vitalia-only** + fidelidad **por copia** (driftea). → Homologación: **liftear el principio a platform** + cambiar el mecanismo a **fidelidad por construcción**.

### Mecanismo de fidelidad POR CONSTRUCCIÓN (lo que mata "el HTML miente")
- El mockup-kit **NO copia** tokens: **importa el CSS de tokens REAL generado** desde la fuente única (`@luana/design-tokens` → `globals.css`). Un cambio de token se refleja en el mockup sin tocar nada. **No puede driftear.**
- El **showcase canónico = una ruta en la app real** (`/showcase` o Storybook) que **renderiza los componentes reales** → lo que Chris ve ES el componente. El `.html` estático es el espejo derivado, no un dibujo.
- `/po-ux` **siempre dentro del shell-organism** (ADR-003 ya lo pide para sub-tabs → se vuelve **regla dura platform**: ningún mockup user-reachable se ratifica fuera del shell).

### Los tokens reales TAMBIÉN necesitan homologarse (capa 1, hallazgo nuevo)
`vitalia/frontend/src/app/globals.css` tiene **dos sistemas en paralelo**: el Shadcn (`--primary`/`--agent-*`) **y** el legacy `--vitalia-*` (con su propio `--radius: 0.5rem` que **choca** con el `--radius: 0.625rem` de Shadcn). → consolidar a UN sistema es parte de capa 1 (no solo "spacing"). El lock Fase 0 no alcanza si la fuente está duplicada.

### Requisitos nuevos cementados (entran al programa)
- **R-FID** — ratificación = HTML **fiel por construcción** (deriva de la fuente única; idealmente ruta de la app real). Cero mockup que mienta.
- **R-SHELL** — `/po-ux` entrega toda funcionalidad user-reachable **dentro del shell-organism** (lift de ADR-vitalia-003 a platform).
- **R-1SRC** — UNA fuente de tokens (resolver duplicación `--radius` + `--vitalia-*` vs Shadcn) antes de declarar "fuente única".

## Qué necesito que ratifiques (antes de armar ready packages)

1. **Picks canónicos** — ¿confirmás los "mejor de cada uno" de arriba, o querés cambiar algún ganador? (especialmente: nicolify para N3 + grupos; vitalia para autosave + indicador flotante + StaffCard como base de EntityInfoCard).
2. **Alcance comprehensivo** — ¿el programa cubre capas 1-4 + plantillas obligatorias + atar `/po-ux`, tal cual la reestructura? ¿algo entra/sale?
3. **Orden** — Fase 0 (lock) ya independiente. ¿Las primitivas (átomos+layout) antes de cerrar las 4 stories abiertas, o después? (el handoff las gateaba; vos pediste "empezar homologado").
4. **EntityInfoCard slots** — ¿la anatomía de 8 slots te cierra para doctores/servicios/leads, o falta/sobra algún slot?
