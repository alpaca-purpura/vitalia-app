# ADR-014 — Homologación del design system (UI consistente cross-brand por enforcement mecánico)

**Status:** accepted (ratificado por Chris 2026-06-07) · **Date:** 2026-06-07 · **Decider:** Chris · **Scope:** platform-wide (cross-brand · design system) · **Owner:** `/pm-luana`

> **Reconciliación (Chris pidió revisar trabajo previo):** completa — NO duplica — el outcome [`luana-core-ui-foundation`](../../product/outcomes/luana-core-ui-foundation.md) (umbrella design-system, refining) + `tech-baseline-homologation-platform`. Esos cubren package/átomos/shell-organism/theme-tokens (lifts `ui-extraction` + `lift-shell-organism` **accepted**). Esta ADR agrega las 3 piezas que faltaban: **(1) capa de layout-primitives de contenido**, **(2) enforcement mecánico** (lock arbitrary), **(3) homologación comprehensiva (todas las hojas)**. Plan: `docs/promotion-protocol/proposals/2026-06-07-design-system-homologation.md`.
>
> **Requisito Chris 2026-06-07 (HARD):** la adopción en cada marca es **comprehensiva — TODAS las hojas sin excepción**, no slice-by-slice. *"Necesito empezar homologado, sino seguiré creciendo teniendo distintas formas UI = mala experiencia de usuario."* El quick-win (Fase 0) frena el drift nuevo desde el día 1; la adopción comprehensiva limpia el drift viejo antes de seguir creciendo.

> Hermana de [ADR-012](ADR-012-autosave-primitive-platform.md) (autosave primitive). Mismo principio: un patrón de UI duplicado/divergente feature-por-feature se eleva a primitiva compartida con **contrato + enforcement**, no a guía opcional.

> **Complemento (2026-06-25): [ADR-016](ADR-016-design-system-inventory-governance.md)** gobierna el *inventario* (reuse/extend/create + vocabulario `DESTINO`/`ACCIÓN` + paridad 1:1 + contrato de fidelidad **mockup===resultado**). **Esta ADR (014) = enforcement de homologación (las 5 capas); ADR-016 = gobernanza de qué se cataloga/comparte/extiende — concerns ortogonales.** Los *contratos concretos* de cada componente viven en `design-system-canon.md` (esta ADR **no los re-tabla**; las filas de "capa 3" de abajo son la descripción de la capa, no el contrato — el contrato es canon §2).

## Contexto

Chris reportó (2026-06-07): *"el dev-team crea siempre a su forma la interfaz y eso hace que cambie de hoja y se sienta una aplicación diferente"*. Quiere **homologar la UI por completo** — padding, curva de borde, espacios, fuentes, posiciones — en todos lados, de una vez.

**Diagnóstico (grounded en código, no teoría):**

| Señal | Evidencia |
|---|---|
| **No existe capa de layout-primitives** | `grep PageHeader/Section/Toolbar/DetailLayout/FormLayout/PageLayout` en `{brand}/frontend/src/components` (fuera de shell-organism) = ~0 sistema. El **área de contenido** de cada sub-tab se arma con `<div>` crudos → padding/estructura distintos cada vez. **Causa #1.** |
| **Cero enforcement contra arbitrary values** | `arbitrary-value classes` en `*/frontend/src/features`: **vitalia 368** (58× `text-[..]`, + `p-[..]`/`gap-[..]`/`rounded-[..]`/`w-[..]`/`h-[..]`), nicolify 4, comunify 0. Tailwind `theme.extend` (suma, no restringe) + **sin regla eslint**. **Causa #2** (el micro-drift de padding/espacios/fuentes). |
| **Spacing no tokenizado como decisión** | radius (`--radius` → sm/md/lg/bubble/pill) y tipografía (display/heading/body) SÍ están tokenizados; **spacing NO** (se usa la escala Tailwind cruda + arbitrary libre). |
| **Las bases compartidas están vacías** | `@luana/design-tokens` exporta **solo `z-index`** — color/radius/tipo viven en el `globals.css` de CADA marca (no compartidos → cada marca puede driftear su propia escala). `@luana/ui-kit` tiene átomos + `detail-panel` pero **sin capa de page-layout**. |

**La verdad incómoda (el por qué de esta ADR):** vitalia YA tiene tokens + skill `vitalia-design-system` + rule `frontend-visual-fidelity` (D1 "design system first") **y aun así driftea 368 veces**. nicolify/comunify están limpias hoy **solo porque son chicas/nuevas** — sin enforcement driftearán igual al crecer. **Conclusión: el enforcement por criterio (docs/skills/rules que el builder *debería* seguir) NO sostiene la consistencia. Solo sostiene el enforcement MECÁNICO** (tailwind lockeado + eslint + arch-test + primitivas como único lego). Esta es la decisión central.

**Qué NO es:** esto **no es parte del shell-organism**. El shell resuelve el **chrome/marco exterior** (topbar/ribbon/Valeria/nav) — y está bien. El "se siente otra app" vive en el **contenido interior**, que el shell no gobierna. Se necesita una **capa de design-system de contenido** adjunta.

## Decisión

Homologar la UI como **un design system de 5 capas, compartido cross-brand en `core/@luana/`, con enforcement mecánico**. Cada capa tiene un home único y una regla que la hace obligatoria.

| # | Capa | Home (cross-brand) | Estado hoy | Acción |
|---|---|---|---|---|
| 1 | **Tokens** (color · radius · tipografía · **spacing** · shadow · z-index) | `core/@luana/design-tokens` | solo z-index | consolidar la escala completa + **lockear** (prohibir arbitrary) |
| 2 | **Átomos** (Shadcn primitives) | `core/@luana/ui-kit` | ✓ (átomos + detail-panel) | mantener + completar |
| 3 | **Layout-primitives** ←★ el hueco | `core/@luana/ui-kit` | falta | construir `Page · PageHeader · Section · Toolbar · FilterBar · EmptyState · ErrorState · DetailLayout · FormLayout · EntityWorkspaceLayout` (padding/espacios/radius **horneados**) |
| 4 | **Page archetypes** (scaffolds list/detail/form/dashboard) | `core/@luana/ui-kit` | falta | scaffolds donde el builder **rellena slots**, no maqueta de cero |
| 5 | **Shell-organism** (chrome) | `core/@luana/ui-kit` (lift en curso, 256517a3) | ✓ | mantener |

**Principio de composición:** una página se **ARMA** desde las capas 3-4 (layout-primitives + archetype), nunca se maqueta a mano con `<div>` + clases sueltas. Los tokens (capa 1) son la única fuente de spacing/radius/tipo.

### Enforcement mecánico (el corazón de la decisión — sin esto, se cae)

| Mecanismo | Qué hace | Leverage |
|---|---|---|
| **Tailwind lockeado** | eslint `no-arbitrary-value` (o theme restringido) → spacing/radius/fuente SOLO de la escala. Prohíbe `text-[13px]`, `gap-[7px]`, etc. | **el más alto + el más rápido** (mata los 368 de un saque + frena drift nuevo) |
| **Arch-test FE** | prohíbe `<div>` de layout donde existe una primitiva; prohíbe hex/px hardcoded; ratchet shrink-only | sostiene la capa 3 |
| **`frontend-visual-fidelity` D1 → mecánico** | deja de ser juicio del auditor, pasa a lint/arch-test | quita la carga del criterio humano |
| **Storybook = SSoT visual** (`core/@luana/ui-kit` · `build-storybook` → `storybook-static/`, o dev `:6007`) | el catálogo de los componentes REALES — "lo que ves en Storybook = lo que se programa". UX **parte** de Storybook (HTML de las stories), el architect **cita la story**, el builder **construye desde** ella; lo net-new se **promueve** de vuelta al kit + story (cero `_shared.css`/mockup-kit · esos quedan SUPERSEDED). Bucle completo: `design-system-canon.md § 5`. | descubribilidad + propose/promote loop (cero drift) |
| **Skills dev-team + auditor** | primitivas = único lego permitido; auditor verifica composición, no estilo a mano | refuerzo de proceso |
| **Arch-test dark-wiring** (cement 2026-06-16) | por marca, asserta el contrato dark del kit: `dark:` → `[data-theme="dark"]`/`.dark` (no `prefers-color-scheme`) + `@source` escanea `ui-kit/src` completo (canon §2.10) | caza la regresión silenciosa que ningún gate cross-brand cubría (origen nicolify ds-adoption) |

### Dónde vive + ownership

Todo en `core/@luana/{design-tokens, ui-kit}` (cross-brand). Es jurisdicción **`/pm-luana`** (promotion gate). Las marcas **adoptan** (opt-in por brand, vitalia primero por ser el peor drift). Mismo carril que los lifts ya aceptados: `2026-06-01-lift-shell-organism-to-core`, `2026-05-21-luana-core-ui-extraction`, `2026-05-30-lift-zone-model`.

## Consecuencias

**Positivas:** una sola fuente de verdad visual → toda hoja se siente la misma app; el drift se vuelve **imposible** (no compila/no pasa lint), no "desaconsejado"; el lift del shell a `@luana/ui-kit` gana su capa de contenido; nuevas marcas heredan el sistema gratis.

**Costo / riesgos:** (a) migración de los 368 arbitrary-values de vitalia (incremental, no big-bang); (b) lockear arbitrary puede romper casos legítimos → se permite un allowlist ratchet shrink-only + escape documentado; (c) construir 8-10 primitivas + archetypes = esfuerzo real (estimado 1-2 semanas core + adopción por marca); (d) requiere disciplina de no maquetar a mano (lo fuerza el lint).

**No-boil-the-ocean:** rollout por fases (ver proposal). Quick-win primero (lockear arbitrary + escala spacing) frena el drift HOY; primitivas + adopción incremental después. Páginas nuevas obligadas al sistema; viejas migran oportunista.

## Alternativas consideradas

- **Solo docs/skills más estrictos** — RECHAZADO: ya existen (skill + rule D1) y driftea 368 veces. El criterio no sostiene.
- **Meterlo en el shell-organism** — RECHAZADO: el shell es el chrome; el drift es del contenido. Capa distinta.
- **Per-brand (cada marca su sistema)** — RECHAZADO: 3 marcas casi gemelas + shell ya lifteándose a core. Un solo sistema cross-brand (anti-duplication).

## Programa (las piezas cuelgan de aquí + del proposal)

1. **Esta ADR** (doctrina) + **promotion proposal** `2026-06-07-design-system-homologation` (plan core + lift).
2. **Story platform de build** (`docs/product/stories/`, `brand: platform`): tokens + primitivas + archetypes + enforcement en `@luana/{design-tokens, ui-kit}`.
3. **Stories de adopción por marca** (`{brand}/docs/product/stories/`): vitalia (primero — peor drift) → nicolify → comunify migran al sistema + encienden el lint.

> Caveat conocido: un programa platform multi-story no tiene contenedor limpio arriba de la story (outcome deprecado en el modelo 4-ejes). Ancla = este par **ADR + proposal**; las stories son los tramos.

## Referencias

- `docs/promotion-protocol/proposals/2026-06-07-design-system-homologation.md` — plan + lift
- `ADR-012-autosave-primitive-platform.md` — precedente (primitiva cross-brand)
- `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` — `EntityWorkspaceLayout` = primera layout-primitive (promotable candidate)
- `.claude/rules/frontend-visual-fidelity.md` (D1) · `.claude/rules/anti-duplication.md`
- `core/@luana/design-tokens` · `core/@luana/ui-kit` — homes
- Lifts precedentes: `proposals/2026-06-01-lift-shell-organism-to-core.md`, `2026-05-21-luana-core-ui-extraction.md`, `2026-05-30-lift-zone-model.md`
