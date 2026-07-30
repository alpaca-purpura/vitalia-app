---
story_id: vitalia-shell-dual-mount-a11y-fix
brand: vitalia
arch_version: 1
schema_version: v4.1
type: bugfix
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale   # shell CORE (no es sub-tab nueva): aplican secciones 1/2/3/9; 4-8 N/A (sin data layer, forms, BE, migrations, telemetría). Rationale en § Architecture Decisions.
architect_run_on: 2026-06-01
autonomous_mode: false
---

# 03-arch — Shell dual-mount + a11y fix (single-main + single-slot)

> **Tipo bugfix arquitectónico (ADR-011).** No hay `01-spec.md`: la SPEC es `checkpoint.md`
> + `vitalia/docs/observed-bugs/2026-05-31-shell-dual-mount-duplicate-testids.md`.
> Modelo Opus 4.8 (cutoff Jan 2026); patrón react-resizable-panels v4 + hook-count stability
> verificado contra el código real de nicolify (prior-art live), no contra conocimiento estático.

## 0. Context Summary

- **Story**: `vitalia-shell-dual-mount-a11y-fix` · release F2 · cap_target `shell-vitalia` · cap_change_type `fix`.
- **Architect run on**: 2026-06-01.
- **Surface tocada**: FE ONLY — `vitalia/frontend/src/components/shared/shell-organism/` (componente core del shell + sus tests). NO BE. NO AGENTIC. NO core engine. NO cross-brand.
- **Síntoma**: el shell monta el slot de contenido (`<AppPanelSlot>`) en 2 ramas a la vez (desktop visible + mobile CSS-hidden) → cada `data-testid` del panel existe 2× (Playwright strict-mode violation) + `id="main-content"` aparece en 3 `<main>` (HTML inválido + a11y landmark dup).
- **Root cause**: "Triple-main pattern" deliberado en `ShellOrganismLayoutClient.tsx` — 3 `<main id="main-content">` mutuamente excluyentes por CSS (agentic `hidden md:block` · web `hidden md:grid` · mobile `md:hidden` SIEMPRE montado). La rama mobile siempre se monta → en desktop hay 2 `<AppPanelSlot>`.

### Surface → builder → auditor mapping (PM consume para spawn)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` + sus tests | **`builder-frontend` (Sonnet)** | **`auditor-frontend` (Opus)** |

> FE NO-AGENTIC → Sonnet (R23 NO aplica: no toca prompt slots / eval goldens / state machine de agente).

- **Skills consultados**: `frontend-expert` (FSD-Lite + Server-First + live-verify gate), `vitalia-design-system` (shell SSoT: 5 agentes Ribbon + Valeria sidebar, tokens, SHELL-DESIGN-CONTRACT), `playwright-expert` (re-verificación transversal + axe + dev-app), `tessl__react-patterns` (hook-count stability), `tessl__vitest` (jsdom matchMedia mock).
- **CONTEXT-BRIEF source**: ausente (story bugfix lite) → self-read directo de checkpoint + observed-bug + prior-art nicolify + código vitalia + tests + arch gates.
- **capability YAML afectado**: `vitalia/docs/product/capabilities/shell-organism/shell-vitalia.yaml` (cap_change_type `fix` → al merge, anotar el fix en business_rules/known-issues; NO agrega scenarios de producto nuevos, user_visible:false).
- **Arch gates que deben seguir verdes**: `src/__tests__/architecture/test-skip-link-target.test.ts` (lee `ShellOrganismLayout.tsx` wrapper — NO se modifica), `src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (mirror=0), `src/__tests__/architecture/test_features_no_cross_imports.test.ts`, ESLint boundaries FSD.

## Prior art audit (anti-duplication-refining · 2026-06-01)

Scope grep ejecutado: `core/` + `vitalia/` propio + `nicolify/` (en main vía sync). Resultado:

- **`nicolify/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx`** — PRIOR ART DIRECTA. Nicolify portó su shell DE vitalia y ya peleó este bug (commits `641dbb4c`/`e153f53d`). **Lección crítica, citada verbatim de su header (líneas 14-19)**:
  > "Layout responsive vía CSS (no JS): el desktop layout (Group resizable o web grid) se monta SIEMPRE y se oculta en mobile con `md:block`; el mobile layout se monta SIEMPRE y se oculta en desktop con `md:hidden`. **Montar/desmontar el `<Group>` condicionalmente (detrás de `useSyncExternalStore(isDesktop)`) disparaba "Rendered more hooks than during the previous render"** — por eso el gate es CSS. UN solo `<main id="main-content">` envuelve ambos layouts (id único, HTML válido)."
- **Hallazgo que refuta el fix del bug doc**: el bug doc original (`observed-bug` § "Fix de producción", approach 1-2) proponía render condicional JS por viewport (`isDesktop ? <AgenticMain/>|<WebMain/> : <MobileMain/>`) que monta/desmonta el `<Group>` resizable. **Nicolify probó que eso CRASHEA** (hook-count diverge entre renders). → ese approach está PROHIBIDO (ver § Architecture Decisions D2).
- **Límite del fix de nicolify**: su single-`<main>` mata el `id` duplicado + el crash, **pero NO mata los testids duplicados** — su código tiene `<AppPanelSlot>{children}</AppPanelSlot>` en la rama desktop (línea 186/194) Y en la rama mobile (línea 201). Ambas en el DOM. Vitalia debe ir UN paso más allá que nicolify: **single-main + single-slot**.
- **No es lift cross-brand**: shell brand-local; cada marca tiene su `ShellOrganismLayoutClient` (vitalia Ribbon 5 agentes + Valeria ≠ nicolify Ribbon 5 agentes B2B + Luana). **Aplicar el PATRÓN, NO compartir el archivo.** Arch gate `test-no-cross-brand-shell-mirror.test.ts` debe seguir en 0 matches.
- **`core/luana-core-*`**: 0 matches de shell layout (es FE brand-local, no engine). No hay capa engine que extender.

**Decisión NO-NEW-LAYER**: **EXTEND** el componente existente (reescritura interna del render de `ShellOrganismLayoutClient`), NO crear nueva capa/wrapper. El wrapper `ShellOrganismLayout.tsx` (dynamic ssr:false + skeleton) NO se toca.

## Architecture Decisions

### D1 — Single `<main id="main-content">` (patrón nicolify) [mata id duplicado + a11y]

Un único `<main id="main-content" tabIndex={-1} aria-label="Contenido principal">` envuelve TODAS las variantes de chrome. El skip-link `#main-content` resuelve a 1 elemento. axe wcag2aa: 0 violaciones de `id` duplicado / landmark único. `containerRef` + `data-shell-ready` viven en ese `<main>` único.

### D2 — Single `<AppPanelSlot>{children}>` renderizado UNA sola vez [mata testids duplicados — supera a nicolify]

El slot de contenido se renderiza EXACTAMENTE 1 vez en el árbol, sin importar viewport ni shellMode. El layout chrome (resizable agentic / grid web / single-col mobile) **rodea** al mismo slot, no lo re-monta. Approach concreto (hook-count estable):

```
<main id="main-content" ref={containerRef} ...>
  {/* TODOS los hooks ya se llamaron arriba, incondicionalmente (D3) */}
  {shellMode === "agentic" ? (
    {/* desktop agentic: Group resizable SIEMPRE montado; oculto < md vía wrapper CSS */}
    <div className="hidden h-full md:block">
      <Group ...>
        <Panel id="valeria-panel" ...><ValeriaSidebar /></Panel>
        <Separator ... />
        <Panel id="app-panel" ...>{appPanel}</Panel>   {/* appPanel = <AppPanelSlot>{children}</AppPanelSlot> — UNA instancia */}
      </Group>
    </div>
  ) : (
    {/* desktop web: grid estático; oculto < md vía wrapper CSS */}
    <div className="hidden h-full md:grid grid-cols-[60px_1px_1fr]">
      <ValeriaSidebar />
      <div className="bg-border" aria-hidden="true" />
      {appPanelWeb}   {/* PROBLEMA: el slot no puede estar físicamente en 2 sitios del JSX a la vez */}
    </div>
  )}
  {/* mobile single-col: oculto >= md vía wrapper CSS */}
  <div className="h-full md:hidden">{appPanelMobile}</div>
</main>
```

**Tensión real**: un nodo React no puede ocupar dos posiciones del JSX. Hay dos chrome desktop (agentic vs web) que son XOR por `shellMode` (solo una rama desktop existe a la vez) + una rama mobile siempre presente por CSS. Eso son **2 instancias del slot** en el peor caso (1 desktop activa + 1 mobile). **Solución elegida (el builder elige A o B y lo documenta; A es la recomendada):**

- **Opción A (recomendada) — single-slot real con chrome por CSS responsive dentro de un solo árbol**: estructurar el chrome de modo que el `<AppPanelSlot>` aparezca **una sola vez** en el JSX, y que las diferencias desktop/mobile sean clases CSS sobre los CONTENEDORES del slot, no re-montajes. Para el modo agentic, el `<Group>` resizable debe contener el slot; en mobile el `<Group>` no aplica (single-col). Como `<Group>`/`<Panel>` no admiten "desaparecer por CSS sin desmontar el slot interior", se usa **un wrapper que decide layout por CSS container queries / `md:` sobre el contenedor del Group, manteniendo el `<Panel id="app-panel">` como ÚNICO host del slot**. En mobile el Group colapsa Valeria (Panel valeria width 0 / `md:` hidden) y el app-panel ocupa 100% — el slot sigue siendo el mismo nodo. Web mode: el grid reemplaza al Group pero el slot sigue siendo una instancia (renderizada vía variable `appPanel` y colocada una sola vez). **Net**: 1 sola `<AppPanelSlot>` en el DOM en cualquier viewport/mode.
- **Opción B (fallback aceptable) — slot único + chrome variant sin doble mount**: si A resulta inviable con la API v4 de react-resizable-panels (el `<Group>` requiere mount desktop-only), entonces renderizar el chrome desktop (agentic XOR web) y el mobile como hermanos PERO con el `<AppPanelSlot>` extraído a una sola posición compartida vía composición (render-prop / portal lógico) de modo que físicamente exista una sola vez. Si B tampoco es viable sin re-mount, el builder DEBE documentar por qué y caer al criterio mínimo: **a lo sumo 1 sola instancia visible y 0 instancias en ramas CSS-hidden** — es decir, la rama oculta por viewport NO renderiza `<AppPanelSlot>` (renderiza `null` o un placeholder vacío), garantizando que `getByTestId('app-panel-slot')` y todo testid del panel resuelvan a 1.

> **Criterio de aceptación duro (independiente de A/B)**: en CUALQUIER viewport y CUALQUIER shellMode, `document.querySelectorAll('[data-testid="app-panel-slot"]').length === 1` y `document.querySelectorAll('#main-content').length === 1`. El builder elige el approach que lo logre con hook-count estable (D3) y lo documenta en el header del componente + en su technical_design.

### D3 — Hook-count stability: TODOS los hooks antes de cualquier branch/early-return [mata "more hooks" crash]

Lección nicolify literal: montar/desmontar `<Group>` detrás de `isDesktop` cambia el número de hooks entre renders → React crash. Por eso:

- **PROHIBIDO**: `useMediaQuery`/`useSyncExternalStore(isDesktop)` que gobierne el mount/unmount del `<Group>` resizable. El `<Group>` se monta SIEMPRE (oculto por CSS en mobile), nunca condicional por viewport JS.
- **OBLIGATORIO**: todos los hooks (`useStoreHydration`, `useShellStore` selectors, `useViewportGuard`, `useRef`, `useState`, `useEffect` ×2, `useGroupRef`, `useDefaultLayout`) se llaman **incondicionalmente al tope del componente**, antes de cualquier `return`/branch por `shellMode`. El render por `shellMode` (agentic vs web) ya era condicional ANTES y NO cambia hook-count (no hay hooks dentro de las ramas JSX). Mantener esa propiedad: ningún hook nuevo dentro de un branch.
- El JSX puede ramificar por `shellMode` (eso no toca hook-count porque no hay hooks en las ramas). Lo que NO se permite es condicionar el mount del `<Group>` por viewport vía hook que cambie el conteo.

### D4 — `useMediaQuery` NO se usa para este fix [evita el crash + evita tocar otros consumers]

El bug doc proponía lazy-sync-init de `useMediaQuery` para `isDesktop`. Decisión: **NO introducir `isDesktop` JS en el shell layout**. El gate desktop/mobile sigue siendo CSS (`md:`), igual que nicolify. `useMediaQuery` se deja intacto (consumido por `ValeriaSidebar`, `mateo/AppointmentDrawer`) — 0 cambios a esos consumers, 0 riesgo de regresión cross-feature. Esto simplifica el fix y elimina por completo la clase de bug "more hooks".

### D5 — Web/agentic/mobile chrome por CSS, slot compartido

`shellMode` (agentic XOR web) sigue siendo un branch JSX (sin hooks dentro). La diferencia desktop↔mobile es CSS (`md:block`/`md:grid`/`md:hidden`) sobre los CONTENEDORES, no sobre el slot. El `data-shell-ready` y `containerRef` quedan en el `<main>` único (no en el div agentic, como hoy) para que el ResizeObserver observe el contenedor correcto en todos los modos.

## Integration design (CONN) — anti-orphan

- **Consumed**: este shell lo renderiza `(shell-organism)/layout.tsx` (Server Component) para **TODOS los agentes** vía `<ShellOrganismLayout tenantId>`. El `<AppPanelSlot>` hostea el `<Ribbon>` (5 agentes: lisa/mateo/adrian/lucas/camila) + `<SubTabsBar>` + `<SubSubTabsBar>` + children de cada sub-tab. La `<ValeriaSidebar>` (supervisora) vive aparte en el panel izquierdo. **Blast radius transversal**: un error rompe la UI de los 5 agentes + valeria simultáneamente.
- **On the map**: home cap = `shell-vitalia` · functional_area = `plataforma-tecnica.shell` (zona Infraestructura, user_visible:false — quality attribute del contenedor visual, no caja de valor). Derivado del árbol del paradigma.
- **Navigable/reachable**: NO se crean rutas nuevas. Se modifica un componente layout YA montado. Reachability: `/{tenantId}/{agent}/{subtab}` → `(shell-organism)/layout.tsx` → `ShellOrganismLayout` → `ShellOrganismLayoutClient` (este fix) → `AppPanelSlot` → Ribbon/SubTabs/children.
- **Notarized/registered**: ya registrado (mount existente en `layout.tsx`). No requiere nuevo `include_router`/nav/registry. El fix NO desconecta nada.

## Cross-cutting

- **Transversal blast radius (★ máximo riesgo)**: shell compartido por 5 agentes + valeria. Re-verificación transversal OBLIGATORIA (ver `04-validators.yaml § visual`): 5 agentes × 3 modos (agentic/web/mobile) + valeria sidebar, vitest + axe + visual smoke + dev-app live.
- **Tenant isolation**: el shell renderiza para cualquier tenant; no introduce queries. `_tenantId` prop ya existe. Sin cambios de aislamiento (FE chrome, sin data fetch).
- **HIPAA-lite**: N/A — chrome UI, sin PHI. No toca `patient_*`/`medical_*`. No audit log (no hay acción de negocio).
- **Spanish neutro LatAm**: `aria-label="Contenido principal"`, `"Redimensionar paneles"`, `"Panel aplicación"`, `"Panel Valeria"` — preservar tuteo neutro existente (sin voseo).
- **Native-first**: tests corren `npx vitest` / `npx playwright` nativo host (NUNCA docker exec).
- **a11y**: 1 solo landmark `<main>` con `id` único + `tabIndex={-1}` (skip-link). axe wcag2aa sin id-dup ni landmark-unique.

## File structure (NEW vs MODIFIED)

```
vitalia/frontend/src/components/shared/shell-organism/
├── ShellOrganismLayoutClient.tsx        MODIFY — single-main + single-slot + D1-D5 (header doc actualizado: borrar "Triple-main pattern", documentar approach elegido + lección nicolify)
├── ShellOrganismLayout.tsx              NO TOCAR — wrapper dynamic ssr:false + skeleton (skip-link arch test lo lee; su <main> skeleton es 1 solo, OK)
├── AppPanelSlot.tsx                      NO TOCAR (probable) — el slot ya es único por instancia; solo se monta 1 vez tras el fix
├── ShellOrganismLayout.test.tsx          REWRITE — borrar asserts triple-main (SC-1 "both branches", SC-4 "all mains", SC-2 plural); asertar single-main + single-slot + window.matchMedia jsdom mock si aplica
└── AppPanelSlot.test.tsx                 REVIEW/light — asertar single-mount en contexto layout si el caso lo cubre (el slot por sí solo ya es 1; el doble venía del layout)
```

> **No se modifica** `useMediaQuery.ts`, `useViewportGuard.ts`, `ValeriaSidebar.tsx`, `Ribbon.tsx`, ni ningún feature/agente. Solo el layout client + sus 2 tests.

## Test surfaces (TDD RED-first)

- **Vitest unit (RED primero)**:
  1. `ShellOrganismLayout.test.tsx` reescrito: assert `container.querySelectorAll('#main-content').length === 1` (RED contra triple-main actual) + `getAllByTestId('app-panel-slot').length === 1` (RED contra dual-mount) + render OK en `shellMode: agentic | web` + `valeriaState: full | rail` + sin error de hooks. Mock `window.matchMedia` en jsdom si el componente lo consulta (D4 dice que NO debería → si el builder cumple D4, no hace falta el mock; documentarlo).
  2. `AppPanelSlot.test.tsx`: preservar contrato (Ribbon/SubTabsBar/aria) + (si se cubre) single-mount.
- **Playwright funcional/regression**: E2E doctores `getByTestId('btn-nuevo-integrante')` resuelve a 1 (SIN `.filter({visible:true})`) — prueba que el dual-mount murió. POMs de doctores pueden quitar el workaround (fuera de scope estricto de esta story, pero es la prueba de fuego).
- **Playwright visual + axe (transversal)**: 5 agentes × 3 modos + valeria sidebar (ver validators).
- **dev-app live (ADR-vitalia-008)**: ejercer lisa + valeria sidebar en desktop+mobile; consola sin "more hooks" / hydration error; `document.querySelectorAll('#main-content').length === 1` en DOM real.

## Research Notes (date-aware)

- **Prior-art live (no WebSearch)**: `nicolify/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` líneas 14-19 + estructura single-main, leído 2026-06-01. Es la fuente autoritativa del patrón (mismo stack react-resizable-panels v4, misma familia de shell portada de vitalia). Knowledge cutoff Opus 4.8 = Jan 2026; el patrón "single-main + CSS gate para evitar hook-count crash" se verificó contra este código real, no contra memoria del modelo.
- **React hook rules** (canónico, estable): "Rendered more hooks than during the previous render" = invariante de Rules of Hooks (mismo número y orden de hooks en cada render). Confirmado por la lección nicolify. Source: react.dev/reference/rules/rules-of-hooks (estable, no requiere fetch).
- **react-resizable-panels v4 API**: `Group`/`Panel`/`Separator`/`useDefaultLayout`/`useGroupRef` — confirmado del código real vitalia + nicolify (ambos v4). `minSize` string `"%"` = percent enforcement nativo (documentado en el header actual del componente vitalia, líneas 138-151).

## Open Questions for PM

- (No bloqueante — Chris ya respondió en chris-input ⚠️ DUDA): confirmado fix shell brand-local vitalia, NO lift a core, NO tocar nicolify. Asumido SÍ.
- ¿Quitar el workaround `.filter({visible:true})` de los POMs de doctores en ESTA story o en la story `vitalia-fase2-lisa-doctores`? Recomendación: dejar el workaround en doctores (no rompe) y validar acá vía un spec de regresión propio del shell; el cleanup del workaround lo hace doctores cuando re-corra. Decisión final: PM.
