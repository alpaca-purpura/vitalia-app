---
proposal_id: 2026-06-07-design-system-homologation
state: accepted               # ★ ratificado Chris 2026-06-07
opened_date: 2026-06-07
opened_by: /pm-luana
ratified_by: chris
ratified_date: 2026-06-07

# Reconciliación (NO duplica — completa trabajo previo)
parent_outcome: docs/product/outcomes/luana-core-ui-foundation.md   # umbrella design-system (refining, HIGH)
relates_to_outcome: docs/product/outcomes/tech-baseline-homologation-platform.md
sibling_proposals_accepted:
  - 2026-05-21-luana-core-ui-extraction.md   # umbrella package/atoms (accepted)
  - 2026-06-01-lift-shell-organism-to-core.md # shell→@luana/ui-kit (accepted, GATED on open stories)
adds_over_prior:                              # el gap que el outcome previo NO tenía
  - "capa 3 layout-primitives de CONTENIDO sistemática (page archetypes incluidos)"
  - "enforcement MECÁNICO (eslint no-arbitrary + tailwind lock + arch-test layout) — el outcome solo tenía drift-detection de átomos"
  - "homologación COMPREHENSIVA (todas las hojas de cada marca, no slice-by-slice opportunista) — req Chris 2026-06-07"

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md
origin_brands: [vitalia, nicolify, comunify]   # las 3 tienen el shell portado; drift confirmado cross-brand

# Target
target_package: core/@luana/{design-tokens, ui-kit}
target_module: design-tokens/src/ (scale spacing+radius+typo) + ui-kit/src/ (layout-primitives + archetypes)
target_ep: null                # no introduce EP nuevo (es design system FE, no backend extension point)

# Impact assessment
semver_bump: minor             # nuevas primitivas opcionales + nueva escala de tokens (opt-in)
breaking_change: false         # opt-in por marca; el lock de arbitrary se enciende por brand al adoptar
brands_affected_consumers: [vitalia, nicolify, comunify]   # + futuras heredan
brands_at_risk_regression: [vitalia]   # vitalia es quien más migra (368 arbitrary + 5 layout files dispersos)

# Lift plan
lift_estimated_effort: "1-2 semanas core (tokens+primitivas+archetypes+enforcement) + adopción incremental por marca"
lift_owner: /dev-team (+ /architect para el ready package del build platform)
arch_test_downstream_required: true   # R3 — corre tests en cada brand consumer al adoptar
migration_notes_required: false       # opt-in, no breaking; el allowlist ratchet cubre la transición
---

# Promotion Proposal — Design system homologation (UI consistente cross-brand por enforcement mecánico)

> Doctrina: [ADR-014](../../architecture/luana-platform/ADR-014-design-system-homologation.md). Este proposal = el **plan core + lift**.

## 0. Reconciliación con trabajo previo (Chris: "revisá si ya hicimos algo, quedó en el olvido")

**SÍ había trabajo previo** — y este proposal lo COMPLETA, no lo duplica:

| Artefacto previo | Estado | Relación |
|---|---|---|
| `outcome luana-core-ui-foundation` (2026-05-21, HIGH) | refining | **umbrella** del design system: package `@luana/ui-kit` + átomos + shell-organism + theme-tokens + slices. Lista de stories ⏳ (CORE-UI-PACKAGE-BOOTSTRAP, ATOMS, THEME-TOKENS, SHELL-ORGANISM, AGENTIC-PATTERNS, SLICE-*). **Este proposal le agrega la capa 3 (layout-primitives) + el enforcement + la homologación comprehensiva que le faltaban.** |
| `outcome tech-baseline-homologation-platform` | accepted | homologación de baseline técnico (ADRs→platform + paridad por marca). Ortogonal: ese homologa la DOCTRINA; este homologa la UI VISUAL. |
| proposal `2026-05-21-luana-core-ui-extraction` | **accepted** | umbrella package/atoms. Este es child. |
| proposal `2026-06-01-lift-shell-organism-to-core` | **accepted** (GATED on open stories) | el lift del shell. Separado: el shell es el chrome; este es el contenido. |
| `ADR-008-luana-core-ui-shadcn-cli-pattern` | proposed | patrón de distribución (CLI shadcn). Aplica. |
| `vitalia-fase1-design-tokens-theme` | archivada (done) | tokens base vitalia ya existen — este los consolida a `@luana/design-tokens` + lock. |

**El gap que llena ADR-014 + este proposal (lo que el outcome NO tenía):** (1) capa de **layout-primitives de contenido** sistemática (el "se siente otra app" vive ahí); (2) **enforcement mecánico** (lock arbitrary — el outcome solo tenía drift-detection de átomos, no del spacing/padding); (3) **homologación comprehensiva** (todas las hojas, req Chris 2026-06-07). El outcome `luana-core-ui-foundation` se actualiza (status 2026-06-07) para absorber estas 3 piezas.

## 1. Patrón a promover

Un **design system de contenido de 5 capas** compartido en `core/@luana/`, con **enforcement mecánico**, que homologa padding · curva de borde · espacios · fuentes · posiciones en toda la app y todas las marcas. Hoy NO existe como sistema: el área de contenido se maqueta a mano feature-por-feature → cada hoja se siente otra app.

**Origen:** reporte de Chris 2026-06-07 (*"el dev-team crea cada interfaz a su forma → se siente otra app"*) + diagnóstico grounded en la sesión `/pm-vitalia`→`/po-ux` de `vitalia-bugfix-shell-valeria-responsive` (donde `EntityWorkspaceLayout` de nicolify se identificó como la primera layout-primitive — ver [[2026-06-06-n3-entity-workspace-layout-from-nicolify]]).

## 2. Por qué cross-brand

| Brand | Aplicabilidad | Razón / evidencia |
|---|---|---|
| vitalia | origen + peor drift | **368 arbitrary-values** en features · 5 layout-files dispersos sin sistema · shell ya lifteándose a `@luana/ui-kit` (256517a3) |
| nicolify | consumidor | shell port de vitalia · 4 arbitrary hoy (chico) · **0 layout-primitives** → driftea al crecer sin enforcement |
| comunify | consumidor | 0 arbitrary hoy (nuevo) · **0 layout-primitives** → mismo riesgo |
| futuras (6) | heredan | bootstrap nuevo arranca con el sistema gratis |

Las bases compartidas hoy están **vacías**: `@luana/design-tokens` exporta **solo z-index**; `@luana/ui-kit` tiene átomos + `detail-panel` pero **sin capa de page-layout**. Color/radius/tipo viven en el `globals.css` de cada marca → vector de divergencia per-brand.

## 3. Análisis técnico

### Gaps (estado actual → target)

| Pieza | Hoy | Target |
|---|---|---|
| Escala spacing | Tailwind cruda + 368 arbitrary, per-brand | escala tokenizada en `@luana/design-tokens` + **lock** |
| Radius / tipografía | tokenizados pero en `{brand}/globals.css` (no compartido) | consolidar a `@luana/design-tokens` (single scale) |
| Layout-primitives | ~0 sistema (5 files dispersos en vitalia) | `Page · PageHeader · Section · Toolbar · FilterBar · EmptyState · ErrorState · DetailLayout · FormLayout · EntityWorkspaceLayout` en `@luana/ui-kit` |
| Page archetypes | n/a | scaffolds list/detail/form/dashboard en `@luana/ui-kit` |
| Enforcement | ninguno (skill+rule por criterio, driftea igual) | eslint no-arbitrary + arch-test layout + `frontend-visual-fidelity` D1 mecánico |

### Primera primitiva ya identificada

`EntityWorkspaceLayout` (nicolify · `nicolify/frontend/src/components/shared/shell-organism/EntityWorkspaceLayout.tsx`) = la mejor factorización existente del N3 list/detail (EntitySubNavBar + children + skeleton store-free SSR-safe G2). Es el primer ladrillo de la capa 3 → se generaliza a `@luana/ui-kit`. La story `vitalia-bugfix-shell-valeria-responsive` (punto 7) ya la porta a vitalia — esa adopción alimenta este proposal.

## 4. Lift plan (por fases — no big-bang)

**Fase 0 · quick-win (frena el drift HOY):** escala spacing tokenizada en `@luana/design-tokens` + eslint `no-arbitrary-value` (+ allowlist ratchet shrink-only). Enciende en una marca piloto (vitalia) → mide.

**Fase 1 · layout-primitives core:** construir las ~10 primitivas + page archetypes en `@luana/ui-kit` (story platform de build). Storybook/showcase. `EntityWorkspaceLayout` generalizado.

**Fase 2 · enforcement:** arch-test FE (prohíbe layout a mano donde hay primitiva + hex/px hardcoded) + `frontend-visual-fidelity` D1 mecánico + skills dev-team/auditor apuntan a primitivas como único lego.

**Fase 3 · adopción por marca — COMPREHENSIVA (req Chris 2026-06-07):** vitalia primero, **TODAS sus hojas sin excepción** (no slice-by-slice opportunista). Razón de Chris: *"necesito empezar homologado, sino seguiré creciendo teniendo distintas formas UI = mala experiencia"*. Migrar las superficies existentes completas → encender el lock → recién entonces toda hoja nueva nace homologada. Luego nicolify → comunify igual (comprehensivo). R3 downstream arch-test por marca. (El quick-win de Fase 0 frena el drift NUEVO desde el día 1; Fase 3 limpia el drift VIEJO acumulado.)

## 5. Stories que cuelgan de este proposal

- **Story platform de build:** `docs/product/stories/{id}/` (`brand: platform`) — Fases 0-2 (tokens + primitivas + archetypes + enforcement en core). Owner build: `/architect`→`/dev-team`.
- **Stories de adopción:** `vitalia/docs/product/stories/...`, `nicolify/...`, `comunify/...` — Fase 3 por marca. Owner: cada `/pm-{brand}`.
- **No bundlear** en `vitalia-bugfix-shell-valeria-responsive` (queda enfocada; su punto 7 es el primer consumidor del patrón).

## 6. Impact assessment

- **semver:** minor (primitivas + escala opt-in). El lock de arbitrary se enciende **por marca** al adoptar → no rompe marcas que aún no migran.
- **Riesgo regresión:** vitalia (migra 368). Mitigado: allowlist ratchet shrink-only + migración incremental + visual goldens existentes.
- **Anti-default-flip:** el lock de arbitrary es un flag de enforcement por marca; aplicar `.claude/rules/anti-default-flip-audit.md` al encenderlo (grep tests, run suite, doc commit).

## 7. Recomendación

**APPROVED** sugerido (con arranque por Fase 0 quick-win para validar leverage antes de comprometer las primitivas). Es cross-brand genuino (3 marcas + futuras), las bases ya existen como paquetes, y el carril es el mismo de los lifts ya aceptados. **Pendiente: ratificación de Chris** (state → accepted) para abrir el handoff `/architect` de la story platform de build.

## Referencias

- [ADR-014](../../architecture/luana-platform/ADR-014-design-system-homologation.md) — doctrina (5 capas + enforcement mecánico)
- [[2026-06-06-n3-entity-workspace-layout-from-nicolify]] — primera primitiva
- `proposals/2026-06-01-lift-shell-organism-to-core.md` · `2026-05-21-luana-core-ui-extraction.md` · `2026-05-30-lift-zone-model.md` — carril precedente
- `ADR-012-autosave-primitive-platform.md` — patrón hermano (primitiva cross-brand)
- `core/@luana/design-tokens` · `core/@luana/ui-kit` — homes
