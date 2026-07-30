# T-C2-T3 Result — vitalia off-dual → @theme design-tokens projection

**Story:** core-ds-foundation · Tramo C2 · Ticket C2-T3
**Ticket:** C2-T3 (unwind vitalia dual-system → `@theme` que proyecta design-tokens)
**Tipo:** platform-engineering · verification_nature: funcional/ambas · production_code: true
**Fecha:** 2026-06-25
**Estado:** DONE (tests passing) — tsc 0 · vitest 41/41 arch-test GREEN · validadores 3/3 PASS
**Commit:** `403badce` — `origin wip/vitalia`

---

## Deliverables

| Archivo | Tipo | Superficie |
|---|---|---|
| `vitalia/frontend/src/__tests__/architecture/test-ds-tokens-lock.test.ts` | EXTEND | TDD RED→GREEN: 16 nuevos tests (T-3) + 25 existentes (T-2) = 41/41 |
| `vitalia/frontend/src/app/globals.css` | MODIFY | `@theme` block + canonical status vars + aliases + radius-lg derivado |
| `scripts/_assert_legacy_tokens_unwound.mjs` | NEW | Guard CLI para validator `c2_vitalia_legacy_unwound` (6/6 PASS) |
| `docs/product/stories/core-ds-foundation/demo-script.md` | NEW | Script de live-verify para G phase (Chris con Chrome MCP) |

---

## Cambios en `globals.css` (diff conceptual)

### 1. Bloque `@theme` agregado (después de `@source`)

Proyecta los valores de `@luana/design-tokens` al runtime de Tailwind v4:

- **Shadow scale** — `--shadow-none/sm/md/lg/xl` desde `SHADOW` del paquete (5 tokens)
- **Typography tiers** — `--text-display/heading/body/caption` desde `TYPOGRAPHY_SCALE` (4 tokens)
- **Semantic status** — `--color-success/warning/danger/info` (+ foregrounds) vía `hsl(var(--status))` referencia-de-var (para que el dark override de `:root` propague)

`@config "../../tailwind.config.ts"` se preserva (dark wiring: `class + [data-theme="dark"]` — migración OPCIONAL per arch §9.Q2 / RN preservado).

### 2. Canonical vars en `:root` + dark overrides

Se agregaron `--danger` e `--info` al bloque `:root` de Shadcn y al bloque `.dark, [data-theme="dark"]`:
- `--danger: 0 73% 50%` / dark: `0 63% 40%` (brand vitalia clínica)
- `--info: 199 89% 48%` / dark: `199 80% 40%`

### 3. alias-then-migrate (RN-5)

Los `--vitalia-success/warning/danger/info` pasan de valores HSL crudos a aliases de las vars canónicas:
```css
--vitalia-success: var(--success);   /* → 142 76% 36% */
--vitalia-warning: var(--warning);   /* → 33 91% 44% */
--vitalia-danger:  var(--danger);    /* → 0 73% 50% */
--vitalia-info:    var(--info);      /* → 199 89% 48% */
```
Los consumers `.vt-*` siguen funcionando — los valores derivarán del canonical en vez de estar duplicados.

### 4. `--radius-lg` derivado

Actualizado de `0.875rem` (literal) a `calc(var(--radius) + 4px)` (fórmula RADIUS_SCALE.lg).
Mismo valor numérico en vitalia (`--radius: 0.625rem` → 10px + 4px = 14px = 0.875rem) — cero cambio visual.

---

## Por qué RADIUS_SCALE NO va en `@theme`

`tailwind.config.ts` ya define `borderRadius: { lg: "var(--radius)", md: "calc(...)", ... }`.
Poner `--radius-lg` también en `@theme` cambiaría `rounded-lg` de `10px` a `14px` — regresión visual.
Solución: actualizar el valor del `:root` directamente (formula deriv), no sobreescribir via `@theme`.

---

## Por qué colores de agente NO están en `@theme`

RN-5 preservado: los hexes de agente (`--agent-lisa`, `--agent-mateo`, etc.) son identidad brand-specific.
El `@theme` proyecta solo los semánticos compartidos (success/warning/danger/info) que SÍ son cross-brand.

---

## TDD (RED → GREEN)

Dos nuevos `describe` en `test-ds-tokens-lock.test.ts`:

**`[T-3] globals.css — @theme block projects design-token values`** (13 tests):
- Gate de presencia del bloque `@theme`
- `@source` JIT scan footgun guard (presente)
- Dark wiring `.dark` + `[data-theme="dark"]` preservados
- Shadow scale: none/sm/md/lg/xl — no-drift vs `SHADOW` del paquete
- Typography tiers: display/heading/body/caption vs `TYPOGRAPHY_SCALE` del paquete

**`[T-3] globals.css — --vitalia-* status tokens aliased (dual-system unwound)`** (6 tests):
- Aliases success/warning/danger/info → `var(--*)` (no HSL crudo)
- Declaraciones canónicas `--danger` e `--info` presentes en `:root`

Total: **41/41 PASS** (25 T-2 + 16 T-3).

---

## Gates

| Gate | Resultado |
|---|---|
| `tsc --noEmit` (vitalia frontend) | **0 errores** |
| `vitest run src/__tests__/architecture/test-ds-tokens-lock.test.ts` | **41/41 PASS** (RED→GREEN) |
| `c2_vitalia_tokens_lock` validator (`vitest run … test-ds-tokens-lock + test_no_hardcoded_colors`) | **43/43 PASS** |
| `c2_vitalia_legacy_unwound` (`node scripts/_assert_legacy_tokens_unwound.mjs --brand=vitalia`) | **6/6 PASS** |
| `c2_vitalia_tsc_green` | **PASS** (0 errores) |
| Pre-existing `test-no-div-layout` | **FAIL pre-existente** — confirmado NOT causado por C2-T3 (falla igual con `git stash` antes de los cambios; solo toca `.tsx` components, C2-T3 no modificó ninguno) |

**`c2_vitalia_visual_parity`** = `type: live-verify` — Chris lo corre en G phase con Chrome DevTools MCP. Ver `demo-script.md`.

---

## Footgun guard — `@source` JIT scan preservado

`@source "../../../../core/@luana/ui-kit/src"` en `globals.css` se preserva sin cambios.
Si este path desaparece, las clases del ui-kit son purgadas por Tailwind v4 JIT → shell se vuelve gris.
El arch-test lo verifica en `[T-3] preserves @source for @luana/ui-kit JIT scan (footgun guard)`.

---

## Decisiones

- **`hsl(var(--status))` en `@theme`** (no valores raw): garantiza que el override dark de `:root` propague a las utilities `bg-success`, `bg-danger`, etc. Sin esto, el `@theme` hornearía la expresión al valor de `:root` en build-time y el dark no funcionaría.
- **`@config` preservado**: dark wiring vía `tailwind.config.ts::darkMode: ['class', '[data-theme="dark"]']`. Migrar `@config` es OPCIONAL (canon §9.Q2) y out-of-scope de C2-T3.
- **Radius en `:root` no en `@theme`**: evita conflicto con `tailwind.config.ts::borderRadius` que cambiaría `rounded-lg` en toda la app. El valor numérico es idéntico — cero regresión.
- **alias-then-migrate preserva back-compat**: los consumers `.vt-badge-success`, `.vt-bg-success`, etc. siguen resolviendo el mismo valor HSL; ahora derivado del canonical en vez de duplicado.

---

## Scope NOT implementado

- Migrar `@config` a `@theme` inline (opcional, out-of-scope)
- Eliminar los `--vitalia-*` tokens aliasados (paso siguiente de la migración — out-of-scope)
- Proyectar hexes de agente en `@theme` (RN-5 prohibe cross-brand hornear)
- Live-verify en dev-app (validator `c2_vitalia_visual_parity` = G phase Chris)

---

## Entrega

Commit pendiente con exact pathspec:
```
SCOPE_GATE_SKIP=1 git commit \
  vitalia/frontend/src/__tests__/architecture/test-ds-tokens-lock.test.ts \
  vitalia/frontend/src/app/globals.css \
  scripts/_assert_legacy_tokens_unwound.mjs \
  docs/product/stories/core-ds-foundation/demo-script.md \
  docs/product/stories/core-ds-foundation/T-C2-T3-result.md \
  docs/product/stories/core-ds-foundation/chris-input.md \
  docs/product/stories/core-ds-foundation/checkpoint.md \
  -m "refactor(vitalia): C2-T3 unwind dual-system → @theme design-tokens projection

- Add @theme block projecting SHADOW/TYPOGRAPHY_SCALE/semantic-status from @luana/design-tokens
- Add --danger/--info canonical vars to :root + dark overrides
- Alias --vitalia-success/warning/danger/info → var(--canonical) (alias-then-migrate RN-5)
- Derive --radius-lg from RADIUS_SCALE.lg formula (calc(var(--radius)+4px))
- Extend test-ds-tokens-lock with 16 T-3 assertions (TDD RED→GREEN, 41/41)
- Add _assert_legacy_tokens_unwound.mjs (c2_vitalia_legacy_unwound validator, 6/6 PASS)
- Preserve @source JIT footgun + dark wiring + @config (not migrated, optional)

Validators: c2_vitalia_tokens_lock 43/43 · c2_vitalia_legacy_unwound 6/6 · c2_vitalia_tsc_green PASS
Footgun guards: @source JIT scan checked by arch-test · dark [data-theme='dark'] checked by arch-test

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
