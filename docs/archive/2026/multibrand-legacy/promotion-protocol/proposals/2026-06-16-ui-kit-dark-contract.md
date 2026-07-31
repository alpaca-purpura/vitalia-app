---
proposal_id: 2026-06-16-ui-kit-dark-contract
state: migrated                # ★ lift ejecutado 2026-06-16 — rerouteado a wip/vitalia (contrato+gate) + wip/comunify (fix), NO temp worktree (decisión Chris)
opened_date: 2026-06-16
opened_by: /pm-luana
ratified_by: chris
ratified_date: 2026-06-16
migrated_date: 2026-06-16
migrated_commits:
  - "5ded7a1c wip/vitalia — canon §2.10 + §6.8 + ADR-014 enforcement-row + §7 ref + vitalia arch-test (mechanism-agnostic)"
  - "c17bb36b wip/comunify — mount <ThemeProvider attribute=data-theme> + @custom-variant + CSS-var override widen .dark→[data-theme] + comunify arch-test"

# Origen
origin_story: nicolify/docs/product/stories/nicolify-r0-design-system-adoption   # G round-1 dark-mode fix (commit b09bc9dc)
origin_brands: [nicolify]                  # destapado por nicolify; afecta a todas las consumidoras del kit
relates_to: 2026-06-07-design-system-homologation.md   # accepted — misma doctrina ADR-014 (homologar el design system compartido)

# Target
target_package: core/@luana/ui-kit (+ docs/architecture/luana-platform/design-system-canon.md)
target_files:
  - core/@luana/ui-kit/src/styles/  # (a crear) snippet/css canónico de dark-wiring que el consumer importa
  - docs/architecture/luana-platform/design-system-canon.md  # cláusula § Dark-mode wiring
  - "{brand}/frontend/src/__tests__/architecture/  # arch-test consumer replicable (modelo: nicolify test-ds-single-token-source.test.ts +3)"
brands_affected: [nicolify, vitalia, comunify, lupulo]   # todas consumen componentes del kit con dark: variants

# Impact assessment
semver_bump: none              # pieza-3 (asset importable) descartada en migración → ui-kit/src NO tocado, kit queda 0.4.1; el contrato vive en canon + arch-test + el globals.css de cada consumer
breaking_change: false
brands_at_risk_regression: [vitalia, comunify]   # tienen dark wiring propio — la homologación no debe romperlo
---

# Lift: dark-mode wiring contract para `@luana/ui-kit`

## 1. Problema

`@luana/ui-kit` shippea **5 componentes con `dark:` Tailwind variants** (AutosaveBadge, alert, chart, FloatingAutosaveIndicator, + chrome del shell) pero **NO shippea CSS, NO `@custom-variant dark`, y no documenta ningún contrato de cómo se cablea el dark mode**. Resultado: cada brand consumer re-deriva el wiring por su cuenta → **divergencia de mecanismo + regresión silenciosa** que ningún gate cross-brand cubre.

Lo destapó `nicolify-r0-design-system-adoption` (G round-1): al adoptar el organism shell del kit, el dark mode dejó de conmutar — el port había dropeado el cableado que vitalia sí tenía. Fix nicolify en `b09bc9dc`. Pero el scan cross-brand muestra que **el problema es del kit, no de nicolify**.

## 2. Estado real cross-brand (scan 2026-06-16)

| Brand | `@custom-variant dark` | `@config`+tailwind.config darkMode | `@source` ui-kit | Dark mode |
|---|---|---|---|---|
| **vitalia** | no | **sí** (`darkMode: ["class", '[data-theme="dark"]']` + `@config`) | `ui-kit/src` (completo) | ✅ funciona |
| **nicolify** | **sí** (recién, v4-puro) | no | `ui-kit/src` (completo, recién widened) | ✅ funciona (fix b09bc9dc) |
| **comunify** | no | no | **none** | ❌ **ROTO** (cero wiring + kit no escaneado — bug latente sin notar) |
| **lupulo** | — | — | — | n/a (placeholder, sin globals.css) |

Dos mecanismos distintos para el mismo efecto (vitalia `@config` v3-compat · nicolify `@custom-variant` v4-puro) + **comunify directamente roto**. El kit canon (`design-system-canon.md` / `ADR-014`) **no tiene cláusula dark**. Es exactamente el anti-patrón "cada consumer re-deriva → regresión silenciosa" que la homologación (ADR-014) busca matar.

## 3. Por qué cross-brand (genuinamente transversal)

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya consume | dark wiring propio (`@config`) — homologar al canon |
| nicolify | ya consume | dark wiring propio (`@custom-variant`) — origen del fix |
| comunify | **consume + roto** | sin wiring → fix obligatorio (no solo hardening) |
| lupulo | consumer futuro | hereda el contrato al construir su shell (evita repetir el bug) |

Todas las brands consumen componentes del kit con `dark:` variants. El contrato es del engine. ≥2 brands viable + 1 rota + 1 futura = lift justificado.

## 4. Cambio propuesto (a refinar en `under_review`)

3 piezas, de menor a mayor superficie:

1. **Cláusula `§ Dark-mode wiring` en `design-system-canon.md`** (+ SHELL-DESIGN-CONTRACT por brand) — documenta el contrato HARD que todo consumer cumple: `next-themes attribute="data-theme"` + selector `[data-theme="dark"]`/`.dark` + `@source` del `ui-kit/src` completo. Define el mecanismo canónico (recomendado: `@custom-variant dark` v4-puro — menos superficie que `@config`+tailwind.config; vitalia migra cuando toque, sin urgencia).
2. **Arch-test consumer replicable por brand** — generalizar los +3 que nicolify ya tiene (`test-ds-single-token-source.test.ts`: `@custom-variant` apunta a `[data-theme="dark"]` + cubre `.dark` + `@source` escanea `ui-kit/src` completo). Cada brand replica → el gate caza el drop antes de shippear (lo que faltó acá).
3. **(a evaluar) el kit ship-ea el snippet canónico** — `@luana/ui-kit/src/styles/dark.css` (o export del preset) con el `@custom-variant` + el `@source` hint, para que el consumer lo importe en vez de re-tipearlo. Reduce el wiring del consumer a 1 import. Evaluar vs simplemente documentarlo (Tailwind v4 `@source`/`@custom-variant` viven en el globals.css del consumer, no son trivialmente importables — verificar viabilidad técnica en `under_review`).

## 5. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Homologar rompe el dark de vitalia (tiene `@config`, no `@custom-variant`) | Media | NO forzar migración de mecanismo de golpe — el canon acepta ambos selectores mientras el EFECTO sea `[data-theme="dark"]`. vitalia migra a `@custom-variant` como follow-up opcional. Arch-test asserta el efecto, no el mecanismo exacto. |
| comunify fix introduce cambio visual inesperado | Media | comunify está roto HOY (dark no conmuta) — el fix lo arregla; correr su suite + live-verify del toggle (doctrina verification-real). |
| El kit no puede shippear `@custom-variant`/`@source` importables (limitación v4) | Baja | Pieza 3 es opcional; piezas 1+2 (contrato + arch-test) ya cierran el gap sin ella. |

## 6. Decisión

**Recomendación `/pm-luana`:** APPROVED — gap del engine confirmado con evidencia (3 mecanismos divergentes + 1 brand rota + kit sin contrato + canon sin cláusula). Es hardening de la doctrina ADR-014 ya accepted, + arregla un bug real (comunify). Bajo riesgo (minor, opt-in, arch-test protege).

**Scope NO incluye:** el fix de nicolify (ya hecho, `b09bc9dc`). Esta proposal es el contrato del kit + el gate replicable + el fix de comunify.

**Ratificación Chris:** ✅ APPROVED 2026-06-16 ("ratifico el proposal del dark-contract"). state → `accepted`. Lift ejecuta en worktree core efímero (M13).

## 7. Bitácora

- 2026-06-16: opened by /pm-luana. Origen: nicolify ds-adoption G round-1 (dark fix `b09bc9dc`). Scan cross-brand confirma sistémico (comunify roto, 3 mecanismos divergentes, kit sin contrato).
- 2026-06-16: Chris ratifica APPROVED → state proposed → accepted. Lift pendiente en worktree core efímero.
- 2026-06-16: **lift ejecutado → state accepted → migrated.** Chris decidió NO temp worktree core; el lift viajó en 2 lanes de marca:
  - **wip/vitalia `5ded7a1c`** — pieza 1 (canon `§2.10 Dark-mode wiring` + `§6.8` snippet) + nota enforcement en ADR-014 + pieza 2 para vitalia (arch-test `test-ds-single-token-source.test.ts` bloque dark-wiring, **mechanism-agnostic**: acepta el `@config` legacy de vitalia, asserta el EFECTO no el mecanismo). Gates: tsc 0 · FE arch 30 files/190 tests verde.
  - **wip/comunify `c17bb36b`** — fix comunify **rerouteado a su propio lane** (NO wip/vitalia como decía el plan original): la base de comunify había divergido +5 commits vs main (143 líneas, `@source` ya presente, `attribute=data-theme`); editarla desde el worktree de vitalia con la base stale (31 líneas) habría clobbeado la sesión activa de shell-adoption. Decisión Chris (2026-06-16). Pieza 2 comunify = arch-test `test-ds-dark-wiring.test.ts`.
  - **Hallazgo no previsto:** comunify NO tenía `<ThemeProvider>` montado en ningún lado (toggle muerto, no solo los `dark:` del kit). Chris ratificó montarlo en este lift (mirror nicolify, storageKey `comunify-theme`). Live-verify real en dev :3003 (Chrome DevTools MCP, tras limpiar `.next` cache de Turbopack): provider setea `data-theme=dark`, token swap conmuta (`--bg 240 20% 99% ↔ 240 18% 8%`), kit `dark:` utils scoped a `[data-theme=dark]`, prefers-color-scheme variant rules = 0, console sin errores de dark.
  - **Pieza 3 (asset importable del kit): DESCARTADA.** Verificado: Tailwind v4 `@custom-variant`/`@source` son directivas del CSS entry del consumer (resuelven relativo a su `globals.css`), no re-exportables útilmente desde el paquete TS. Piezas 1+2 cierran el gap sin tocar `ui-kit/src` → **sin bump del kit (queda 0.4.1)**. El snippet canónico quedó documentado en canon §6.8.
  - **nicolify:** sin cambios (su fix `b09bc9dc` ya estaba hecho; out of scope). **lupulo:** n/a (placeholder sin `globals.css`).

## 8. Cross-references

- Origen: `nicolify/docs/product/stories/nicolify-r0-design-system-adoption/` (checkpoint `chris_verify.rounds[0]` + chris-input 2026-06-16) · fix commit `b09bc9dc`
- Doctrina: `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` + proposal `2026-06-07-design-system-homologation.md` (accepted)
- Canon: `docs/architecture/luana-platform/design-system-canon.md` (target de la cláusula § Dark-mode wiring)
- Arch-test modelo: `nicolify/frontend/src/__tests__/architecture/test-ds-single-token-source.test.ts` (§ DS dark-mode wiring)
- Process: `docs/promotion-protocol/README.md`
