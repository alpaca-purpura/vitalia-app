---
proposal_id: 2026-06-15-ui-kit-radius-control-token
state: migrated                # ★ merged a main 2026-06-16 (/pm-luana squash-merge wip/core-radius-control · regression re-verificada: design-tokens 12/12 + vitalia tsc 0 err)
opened_date: 2026-06-15
opened_by: /architect (nicolify-r0-design-system-adoption)
ratified_by: chris
ratified_date: 2026-06-15
migrated_date: 2026-06-16
migrated_by: /pm-luana

# Origen
origin_story: nicolify/docs/product/stories/nicolify-r0-design-system-adoption   # RN-7
origin_brands: [nicolify]                  # nicolify pide pill controls; vitalia/comunify stay md (no visual change)
relates_to: 2026-06-07-design-system-homologation.md   # accepted — esta es una pieza de enforcement de la misma doctrina (ADR-014)
sibling_proposal: 2026-06-12-ui-kit-entity-subnavbar-picker-slot.md   # mismo patrón slot-en-kit (cross-ref accent §B)

# Target
target_package: core/@luana/ui-kit + core/@luana/design-tokens
target_files:
  - core/@luana/ui-kit/src/{button,input,select,textarea}.tsx
  - core/@luana/design-tokens/src/radius.ts
  - core/@luana/ui-kit tailwind preset (utilidad rounded-control)
brands_affected: [nicolify, vitalia, comunify, lupulo]   # todas consumen los controls del kit → downstream-regression obligatoria
---

# Lift: `--radius-control` token brand-overridable en los controls de @luana/ui-kit

## ✅ MIGRATED (2026-06-16) — merged a main · ui-kit 0.5.0 vive en main

- **Worktree:** `wip/core-radius-control` (4 commits, pushed): `0ca11f0f` (lift) · `9574e31c` (fix md-exact — ver abajo) · `9081d1de` (docs) · `125696b4` (bump 0.5.0 + CHANGELOG).
- **Version:** `@luana/ui-kit` 0.4.1 → **0.5.0** (minor).
- **Regression cross-brand VERDE (md-exact, cero cambio visual):** vitalia control=`calc(var(--radius)-2px)` 8px (=old md) · comunify=`0.375rem` 6px (=old md) · lupulo=`var(--radius)` 6px (=its md). tsc 0 err ×brands + arch vitalia 187/187 + comunify 3/3 + ui-kit 270/270 + design-tokens 12/12.
- **★ Regression caught + fixed:** la 1ª pasada mapeó `--radius-control: var(--radius)` (10px) → +2px en vitalia/comunify (habría roto sus goldens 0.001). Corregido a md-exact en `9574e31c`. (El wording de esta proposal decía `var(--radius)` — era impreciso; el INTENT era "stay md".)
- **Mecanismo:** brand `tailwind.config.ts::borderRadius.control: "var(--radius-control, <su-md>)"` + `--radius-control` en globals.css. Kit atoms usan `rounded-control`. Doble fallback → marca que omite el token = md.
- **✅ (1) merged a main** 2026-06-16 (squash-merge `wip/core-radius-control`, sin solape con los 3 commits que main avanzó; regression re-verificada independiente: design-tokens 12/12 + vitalia tsc 0 err). · **✅ (2) proposal → `migrated`** (este commit).
- **⏳ PENDIENTE downstream (handoff `/pm-nicolify`):** (3) nicolify bumpea dep `@luana/ui-kit` → 0.5.0 → controls pill → destraba golden `atoms.png` (hoy `test.skip blocked_on: kit-radius-control-lift`) + demo #37 (Abel) full-fidelity. Esto NO bloquea el merge — es trabajo de la branch `wip/nicolify`.

## Problema

Los átomos de control del kit (`Button`/`Input`/`Select`/`Textarea`) **hardcodean `rounded-md`**. Nicolify ratificó (FIRMA 2, 2026-06-15) un lenguaje visual de **controles fully-rounded (pill)**, coherente con tabs/chips/composer. Hoy es imposible sin (a) hardcodear pill en el kit (rompe vitalia/comunify) o (b) un mirror local (viola anti-duplication). Las **superficies** (card/group/panel) NO cambian — solo los controles.

## Cambio propuesto (chico, low-risk)

1. **`@luana/design-tokens` radius.ts** — agregar el nombre `control` a la escala de radios (nombre compartido, valor por marca).
2. **kit Button/Input/Select/Textarea** — `rounded-md` → `rounded-control` (= `border-radius: var(--radius-control)`).
3. **tailwind preset del kit** — mapear la utilidad `rounded-control` → `var(--radius-control)`.
4. **Cada brand globals.css define `--radius-control`** (brand-scoped, NO en el kit):
   - **nicolify** = `9999px` (pill) — se agrega en esta story (`nicolify-r0-design-system-adoption` T-1, ya brand-scoped).
   - **vitalia / comunify / lupulo** = `var(--radius)` (= md actual) → **cero cambio visual**.

> Salvaguarda: el default del kit cuando `--radius-control` no está definido debe ser `var(--radius-md, 0.625rem)` (= comportamiento actual) — ninguna marca rompe aunque no setee el token.

## Blast radius + downstream regression (auditor-downstream-regression.md)

`Button/Input/Select/Textarea` los consumen las 4 marcas. Obligatorio antes de bump:
- [ ] vitalia: controls renderizan `md` idéntico a hoy (golden/visual sin diff) — vitalia define `--radius-control: var(--radius)`.
- [ ] comunify: idem (define el token = `var(--radius)`).
- [ ] lupulo: placeholder — define el token defensivo.
- [ ] nicolify: controls renderizan pill (post-bump + dep upgrade).
- [ ] arch-fitness de cada marca verde.

## Secuencia (Chris ratificó "decouple + parallel" 2026-06-15)

1. `nicolify-r0-design-system-adoption` cierra `ready` y construye la adopción estructural **sin** depender de este lift (el token brand-scoped se setea; los controls quedan `rounded-md` hasta el bump).
2. `/pm-luana` acepta esta proposal → lift en worktree core efímero → bump `@luana/ui-kit` → regression cross-brand.
3. nicolify bumpea la dep → controls pill → el golden `atoms.png` (control-radius, hoy `blocked_on: kit-radius-control-lift`) + el **demo gate #37** (Abel convergence) corren cuando AMBOS tracks aterrizan.

## §B — Conditional add-on (NO bloqueante): accent-slot en EntitySubNavBar

El active-leaf del `EntitySubNavBar` usa `accent`/`primary` semánticos; el mockup nicolify ratificado muestra acento `agent-abel`. **Solo si** el golden con tokens semánticos no matchea → lift candidate: `EntitySubNavBar` acepta `accentToken`/`agentSlot` opcional (mismo patrón slot que `2026-06-12-ui-kit-entity-subnavbar-picker-slot.md`). Gateado en el golden `abel-icp-detail.png`. Tracked como `kit-accent-slot-lift` en `04-validators.yaml` de la story.

## No-go

- ❌ Hardcodear pill en el kit (rompe vitalia/comunify).
- ❌ Mirror local de los controls en nicolify (anti-duplication).
- ❌ Bump sin la regression cross-brand de arriba.
