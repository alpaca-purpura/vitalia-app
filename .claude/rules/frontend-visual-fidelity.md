---
paths:
  - "**/frontend/src/**"
  - "core/@luana/**"
  - "**/mockups/**"
description: Visual fidelity FE — D1 design-system-first + D2 mockup adherence + D3 scope + canon binding
---

# Frontend Visual Fidelity (átomos/moléculas + mockup adherence + scope discipline)

> **Tier-2 `paths:` (2026-06-09 — sesión integración).** Carga POSTREAD al leer `frontend/src`/`@luana`/`mockups/`. Cobertura write-time verificada por canal propio de cada actor: `/po-ux` SKILL § canon checklist Step 5 (HARD) · `/architect` SKILL L193 (FE sin canon → NO ready) · `builder-frontend` agent § technical_design D1 · `auditor-frontend` agent Cat visual-fidelity. **Slim stub (context-rot 2026-05-30).** Cuerpo operativo en `.claude/skills/frontend-expert/references/visual-fidelity.md`. **Origen:** 2026-05-28.

## Regla cardinal

El FE construido debe cumplir tres disciplinas (una verificación vía Playwright + auditor):

- **D1 — Design system first (desde Storybook):** el diseño y el build **parten del set de Storybook** (`@luana/ui-kit` — SSoT visual, ver § Storybook abajo) → tokens `@luana/design-tokens` → moléculas compartidas → solo si nada sirve, **proponer + promover** una pieza nueva al kit (no crearla local-y-olvidada). NUNCA reinventar una primitiva existente.
- **D2 — Mockup adherence:** parecerse al mockup en jerarquía visual, layout, estados (default/hover/loading/empty/error/success) y microcopy. Fidelidad = "un humano reconoce que es la misma pantalla", no pixel-perfect.
- **D3 — Scope discipline:** implementar SOLO lo que scopean los scenarios de `01-spec.md` + deliverables del ticket. Lo demás del mockup NO se construye en esta story.

## ★ Design System Canon (binding HARD — cement 2026-06-08, ratificado Chris)

> **SSoT (mapa de homes):** contratos = `design-system-canon.md` (+ ejemplos de código) · doctrina estructural = `ADR-014` · **gobernanza (reuse/extend/create + vocabulario `DESTINO`/`ACCIÓN` + el contrato de fidelidad por actor que esta rule enforça) = `ADR-016`**. **Toda hoja user-reachable, en TODAS las marcas, se ARMA del canon — no se maqueta a mano ni se reinventa una primitiva.**

### ★★ Storybook = SSoT visual (cement 2026-06-22, ratificado Chris · canon §5)

El catálogo de componentes **REALES** vive en **Storybook** (`core/@luana/ui-kit` · `pnpm --filter @luana/ui-kit build-storybook` → `storybook-static/`, o dev `:6007`). **Es la ÚNICA fuente de verdad visual** — "lo que ves en Storybook = lo que se programa". **MUERTOS (SUPERSEDED):** `_shared.css` espejo · mockup-kit CSS · `preview.html` · el protocolo per-brand `shell-mockup-per-component.md` (ADR-vitalia-003). **El bucle (los 5 actores):**
1. **Partir** de Storybook — el TSX se consume como **HTML renderizado** (`storybook-static/` o iframe `…/iframe.html?id=<story>&viewMode=story`) → misma base que el build. NO inventar CSS ni copiar `_shared.css`.
2. **No limitarse** — si falta algo o hay algo genuinamente mejor, se **PROPONE** (Storybook es el piso, no el techo).
3. **Promover de vuelta** — lo que se usa y prueba bien se **PROMUEVE a `@luana/ui-kit` + su story** (vía `core-ds-*` / flujo engine `/pm-vitalia`) para reuso de futuras historias. Una pieza net-new que queda en `features/{m}/` sin promover = **deuda** (la caza el auditor).

Detalle + el bucle por actor: `design-system-canon.md § 5`.

**D1 se concreta así (deja de ser criterio, pasa a contrato verificable):**

- **Contenedor HOJA:** 100% ancho · franjas N3 **full-bleed** (`bg-card` + `border-bottom` + sticky, mismo lenguaje que Ribbon/SubTabs — **NUNCA** card con borde redondeado) · contenido en `PageContainer` (padding `1.25/1.5rem`) + `PageContentStack`. (canon §1)
- **List/detail = `EntityWorkspaceLayout`** (1-panel URL-driven: master grilla de `EntityInfoCard` + Toolbar; detalle = `EntitySubNavBar` full-bleed + leaf). Root-pill `‹ {RootLabel}` (flechita) vuelve; identidad = `EntityPicker` (▾, cambia sin volver). **NUNCA** cablear el list/detail a mano por superficie. (canon §2.1-2.2)
- **`EntityPicker`** = buscar (server-side debounced) + fetch paginado (cursor) + render windowed + lazy. **❌ cargar toda la colección al cliente.** (canon §2.4)
- **`EntityInfoCard` Opción B** (grid `auto-fill minmax(250px)`, circular, clickeable, kebab ⋮ + Skeleton + Empty). (canon §2.3)
- **`Select` canónico Shadcn-style.** **❌ `<select>` nativo** en producto. (canon §2.5)
- **Autosave:** `use-autosave` 600ms+coalesce + **UNA** `FloatingAutosaveIndicator` por **HOJA** (anclada al fondo de la hoja, NO del viewport — `anchor="sheet"` default; `anchor="page"` = escape hatch excepcional · sin badge por-grupo) + barrita de agente. (canon §2.6)
- **Page-primitives** (PageContainer/PageHeader/Section/Toolbar/FilterBar/EmptyState/ErrorState/skeletons/Pagination/DetailLayout/FormLayout). **❌ `<div>` de layout sueltos** donde hay primitiva. (canon §2.7)
- **Tooltip + color-por-agente** per canon §2.8. **❌ arbitrary-values** (spacing/radius/font-size/color-hex) — todo de tokens (canon §0).

**Binding por actor (HARD):**

| Actor | Gate |
|---|---|
| `/po-ux` | **Parte de Storybook** (consume el HTML de las stories para componer el mockup, no inventa CSS ni copia `_shared.css`) + compone del canon. Pieza que falta o mejor → la **PROPONE** (con plan de promoción). Cita `design-system-canon.md § 5`. Sin eso → NO `refined`. |
| `/architect` | `03-arch.md § FE` **cita la story de Storybook a usar (+ link)**; net-new se marca `PROMOTE` (deliverable = crear el componente en `@luana/ui-kit` + story antes del merge) + `04-validators.yaml` declara los gates mecánicos (eslint no-arbitrary + arch-test no-div-layout). |
| `builder-frontend` (`/dev-team`) | Construye **desde la story citada** (`@luana/ui-kit` = único lego). Una primitiva shared net-new → **se PROMUEVE al kit + story** (no re-implementación local que driftea). Reinventar primitiva / `<select>` nativo / arbitrary = **rechazo**. |
| `auditor-frontend` (`/auditor`) | Verifica **composición** contra Storybook (se usó el kit, no estilo a mano) **+ que el net-new se promovió al kit con story** (no quedó local). Hoja con list/detail a mano, `<select>` nativo, `<div>` de layout, arbitrary, franja N3 en card redondeada, o primitiva shared local sin promover → **CHANGES_REQUESTED**. |

> **Migración (cement 2026-06-08):** punto de partida NUEVO. Lo que ya existe se **modifica** al canon (no se deja como estaba). Las stories de build/adopción (`core-ds-*`, `{brand}-ds-adoption`) lo materializan en `@luana/ui-kit` + lint + arch-test; mientras tanto, **toda hoja nueva o tocada nace/queda homologada al canon**.

## Cuándo carga el detalle

- `builder-frontend` arranca un ticket FE → leer D1/D2/D3 completos + gate pre-crear componente (bash snippet) + patrón Playwright scoped.
- `auditor-frontend` abre categoría Visual fidelity → leer enforcement layers + checklist 6 puntos.
- `/architect` FE declara `04-validators § playwright_visual_scope` → leer D3 + schema `story_scope_routes`/`story_scope_components`/`out_of_mockup_scope`.

## Anti-patterns (top 6 — lista completa en el detalle + canon)

- ❌ Reinventar un átomo/primitiva que ya existe (`@luana/ui-kit` / `components/ui/`)
- ❌ Implementar TODO el mockup cuando la historia scopea solo una parte (scope creep)
- ❌ `toHaveScreenshot()` de página completa fuera del scope de la historia (frágil)
- ❌ **Cablear list/detail a mano** en vez de `EntityWorkspaceLayout` · franja N3 en card redondeada en vez de tercer-ribbon full-bleed (canon §2.1-2.2)
- ❌ **`<select>` nativo** (usar `Select` canónico) · **arbitrary-values** spacing/radius/font-size/color (usar tokens) · `<div>` de layout donde hay page-primitive (canon §2.5, §2.7, §0)
- ❌ `/po-ux` mockup o `/dev-team` build que NO compone del `design-system-canon.md` (binding HARD)
- ❌ **Diseñar/maquetar UI sin partir de Storybook** — inventar CSS o copiar `_shared.css`/mockup-kit (mecanismos MUERTOS, canon §5)
- ❌ **Pieza shared net-new que queda local** en `features/{m}/components/` sin promover a `@luana/ui-kit` + story (drift garantizado · futuras historias no la reusan)
- ❌ `/architect` que NO cita la story de Storybook a usar (builder improvisa sin saber qué lego)

## Referencias

- `docs/architecture/luana-platform/design-system-canon.md` — ★ **CANON binding** (contratos + ejemplos de código · lo que po-ux compone y dev-team construye)
- `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` — doctrina estructural (5 capas + enforcement mecánico)
- `docs/architecture/luana-platform/ADR-016-design-system-inventory-governance.md` — **gobernanza de inventario** (reuse/extend/create · vocabulario `DESTINO`/`ACCIÓN` · toolkit de extensión · §5 = el contrato de fidelidad por actor que esta rule enforça · garantía mockup===resultado)
- `.claude/skills/frontend-expert/references/visual-fidelity.md` — **cuerpo operativo completo** (D1/D2/D3 detallados, gate bash, patrón Playwright, auditor checklist, enforcement layers)
- `.claude/rules/frontend-fsd.md` — boundaries FSD-Lite + design system layers
- `.claude/rules/frontend-quality.md` — gates (tsc/eslint/vitest/jscpd)
- `.claude/rules/architect-autonomous-mode.md § playwright_visual_scope` — disciplina de scope visual
- `.claude/rules/spanish-text.md` — microcopy neutro
- `.claude/rules/anti-orphan-integration.md` — el componente debe estar enchufado (nav/route)
- `core/@luana/design-tokens` — tokens cross-brand
