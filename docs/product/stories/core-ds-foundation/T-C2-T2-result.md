# T-C2-T2 Result — SSoT de valores (shadow+color/typo/radius) @theme guardado

**Story:** core-ds-foundation · Tramo C2 · Ticket C2-T2
**Ticket:** C2-T2 (`@luana/design-tokens` SSoT de VALORES en 4 ejes)
**Tipo:** platform-engineering · verification_nature: técnica · production_code: true
**Fecha:** 2026-06-25
**Estado:** DONE — 5 validators PASS · tests GREEN (31 + 69 + 22) · tsc 0 errores
**Commit:** `9ebbe8a7` — `origin wip/vitalia`

---

## Deliverables

| Archivo | Tipo | Descripción |
|---|---|---|
| `core/@luana/design-tokens/src/shadow.ts` | NEW | `SHADOW` elevation scale (none/sm/md/lg/xl) cross-brand |
| `core/@luana/design-tokens/src/color-values.ts` | NEW | `SEMANTIC_COLOR_DEFAULTS` HSL channels + `AGENT_ACCENT_CONTRAST` |
| `core/@luana/design-tokens/src/typography.ts` | EXTEND | ADD `TYPOGRAPHY_SCALE` (size/lineHeight/weight per tier) |
| `core/@luana/design-tokens/src/radius.ts` | EXTEND | ADD `RADIUS_SCALE` (sm/md/lg/control calc-based) |
| `core/@luana/design-tokens/src/index.ts` | EDIT | Barrel exports shadow + color-values |
| `core/@luana/design-tokens/package.json` | EDIT | exports map: `./shadow` + `./color-values` |
| `core/@luana/design-tokens/src/__tests__/scale.test.ts` | EXTEND | +8 describe blocks, 31 tests total |
| `nicolify/frontend/src/app/globals.css` | EDIT | @theme +shadow scale + semantic colors; :root HSL channels |
| `nicolify/frontend/src/__tests__/architecture/test-ds-single-token-source.test.ts` | EXTEND | C2-T2 shadow equality + typo/radius/colors (69 tests) |
| `vitalia/frontend/src/__tests__/architecture/test-ds-tokens-lock.test.ts` | EXTEND | C2-T2 SC-5 TS export structure (22 tests) |
| `scripts/_assert_no_css_in_tokens_pkg.mjs` | NEW | Guard: canon §6.8 NO-CSS check |
| `scripts/_assert_token_value_renders.mjs` | NEW | Guard: renderable value check per token path |

---

## Validators (04-validators-C2.yaml C2-T2)

| Validator | Comando | Resultado |
|---|---|---|
| `c2_shadow_module_exists` | `node -e "import('@luana/design-tokens').then(m=>{if(!m.SHADOW)process.exit(1)})"` | PASS (SHADOW exported) |
| `c2_value_axes_present` | `cd core/@luana/design-tokens && npx vitest run src/__tests__/scale.test.ts` | PASS (31/31) |
| `c2_no_css_shipped` | `node scripts/_assert_no_css_in_tokens_pkg.mjs` | PASS (0 .css files) |
| `c2_nodrift_guard_extended` | `cd nicolify/frontend && npx vitest run src/__tests__/architecture/test-ds-single-token-source.test.ts` | PASS (69/69, must_pass: true) |
| `c2_value_change_visible` | `node scripts/_assert_token_value_renders.mjs --token=SHADOW.md` | PASS (renderable) |

---

## Decisions + Cardinals

### Cardinal: NO-CSS ship (canon §6.8)

`@luana/design-tokens` es TS-only SSoT de VALORES. NO existe ningún `.css` exportable desde el package.
Las marcas wirean los valores en su `globals.css` vía `@theme` (proyección). El `_assert_no_css_in_tokens_pkg.mjs`
lo valida en CI (3 checks: exports map + src/ + root).

### RN-5: colores de agente per-brand (preservado)

`SEMANTIC_COLOR_DEFAULTS` exporta SOLO colores semánticos (success/warning/danger/info + foregrounds).
Los hexes/HSL de agente (`--agent-mateo`, `--agent-lisa`, etc.) siguen per-brand en `globals.css`.
`color-names.ts` sigue siendo NAMES-only (no hex, no HSL).

### canon §2.8: contraste warning-foreground

`warning-foreground` = `20 14% 4%` (L=4%, dark sobre amber). Test: `L < 30%` (nicolify + vitalia + scale.test).
`AGENT_ACCENT_CONTRAST` declara las familias de contraste (`yellow-warm → dark-foreground`, `dark-neutral → light-foreground`)
sin fijar hex per-brand.

### RN-7: control = md − 2px

`RADIUS_SCALE.control = "calc(var(--radius) - 2px)"`. Test verifica la expresión exacta.
Nicolify mantiene `--radius-control: var(--radius-pill)` como override brand en `:root` (no @theme).

### VALUES vs NAMES split (idiom spacing.ts/z-index.ts)

- `spacing.ts`, `z-index.ts` — VALUES cross-brand (patrón origen, no cambiados)
- `typography.ts` — NAMES (`TYPOGRAPHY_TIERS`) + VALUES (`TYPOGRAPHY_SCALE`) en el mismo archivo
- `radius.ts` — NAMES (`RADIUS_NAMES`) + VALUES (`RADIUS_SCALE`) en el mismo archivo
- `shadow.ts` — VALUES only (ningún name era necesario)
- `color-names.ts` — NAMES only (RN-5)
- `color-values.ts` — VALUES only (semántica shared)

---

## Tests

| Suite | Archivo | Resultado |
|---|---|---|
| design-tokens scale | `core/@luana/design-tokens/src/__tests__/scale.test.ts` | 31/31 PASS |
| nicolify arch-test (no-drift equality) | `test-ds-single-token-source.test.ts` | 69/69 PASS |
| vitalia arch-test (TS export structure) | `test-ds-tokens-lock.test.ts` | 22/22 PASS |
| TypeScript | `core/@luana/design-tokens npx tsc --noEmit` | 0 errors |

**Vitalia globals.css projection:** T-3 (no T-2). El vitalia arch-test verifica solo estructura TS; la proyección
@theme de vitalia es el deliverable de T-3.

---

## Scope NOT implemented (T-3)

- Vitalia `globals.css` @theme shadow + semantic color projection — T-3 deliverable
- Vitalia `test-ds-single-token-source.test.ts` (equality tests vs globals.css) — T-3

---

## Next ticket

**C2-T3** (`vitalia globals.css` — unwind 105 hardcoded defs → TS VALUE vars + @theme projection).
Precondición: T-2 VALUES disponibles en `@luana/design-tokens` (cumplida).
verification_nature: funcional/ambas · demo Chris (G) obligatorio · live-verify writes + leer logs.
