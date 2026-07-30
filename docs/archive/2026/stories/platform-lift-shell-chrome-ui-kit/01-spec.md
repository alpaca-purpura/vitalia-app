---
story_id: platform-lift-shell-chrome-ui-kit
brand: platform
type: service-story            # lift técnico FE (refactor move+parametrize) — sin UI nueva, sin agentic
state: refining
po_version: 1
ratified_by_chris: true        # criterios de éxito dictados VERBATIM por Chris 2026-06-11 (autonomous_mode ratificado) — el spec formaliza, no inventa
promotion_proposal: docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md
predecessor_story: vitalia-shell-core-hardening
---

# 01-spec — Lift del chrome shell-organism a @luana/ui-kit + convergencia nicolify

## Context

- Proposal `2026-06-01-lift-shell-organism-to-core` **accepted** (Chris 2026-06-06). Esta story ES su ejecución (Decisión B del hardening la difirió explícitamente a /pm-luana).
- Predecesora `vitalia-shell-core-hardening` **done 2026-06-11**: chrome vitalia endurecido (máquina `valeriaOpen: 'closed'|'chat'` + `historyOpen: boolean`, strip 44px, push historial 280px, clamp 320, drawer <1024, viewport-guard) con suite e2e real-backend 68/68 + `resizer-matrix.spec.ts` 7/7 como **contrato de conducta**.
- Mirror cross-brand CONCRETO: `nicolify/frontend/src/components/shared/shell-organism/` = port verbatim re-temizado con **máquina legacy** (`valeriaState` + `LuanaRail` + `ShellModeToggle`) — diverge del hardened.
- N3 (`EntityWorkspaceLayout` + `EntitySubNavBar`) **ya en kit v0.3.0** — fuera de scope (no rehacer).

## Mapa funcional

### Happy path (narrado)

El chrome del shell-organism (layout splitter + sidebar supervisora + strip colapsado + historial + viewport-guard + store SSR-safe) se **mueve** de `vitalia/frontend/src/components/shared/shell-organism/` a `core/@luana/ui-kit` como organism layer **brand-agnostic**: todo lo brand-specific (nombre de la supervisora, avatar, agent catalog, colores/tokens, copy) entra **vía props + CSS vars** — el kit no conoce a "Valeria" ni a vitalia. Vitalia re-apunta sus imports al kit y **borra** su copia local. Nicolify retira su espejo legacy y consume el mismo chrome del kit (re-temizado vía sus props/tokens). Resultado: **un solo origen** del chrome, mirror cross-brand muerto, dos brands consumidoras. La conducta observable en vitalia **no cambia** — la suite e2e existente corre verde contra el chrome consumido del kit.

### Bifurcaciones

| # | Condición | Resultado | Covers |
|---|---|---|---|
| Bif-1 | Pieza del chrome imposible de parametrizar sin breaking-change indecidible | Documentar + **parquear esa pieza** (queda brand-local) + seguir con el resto + HANDOFF-next-session.md (instrucción Chris verbatim) | SC-9 |
| Bif-2 | Stack dev nicolify no levanta | Criterio nicolify degrada a tsc/vitest/arch verdes + render verificado (vitest/component) — "e2e/live si su stack levanta" (Chris verbatim) | SC-2 |
| Bif-3 | Suite e2e vitalia falla contra el chrome del kit | Root cause en el PORT (fix en kit) — PROHIBIDO ajustar asserts de conducta para que pasen; solo paths/imports del harness de test si el move lo exige | SC-1, SC-5 |
| Bif-4 | Pre-commit M13 bloquea commit mix core+vitalia+nicolify | `SCOPE_GATE_SKIP=1` + razón en commit body (lift sancionado, proposal accepted) | — (operativo) |
| Bif-5 | Estado persistido viejo en localStorage (shape/key legacy) | Shell monta con defaults sin crash (degradación limpia); migración o reset documentado | SC-6 |

### Reglas de negocio

- **RN-1 (contrato de conducta):** la conducta del chrome en vitalia NO cambia. El contrato ejecutable = `e2e/regression/shell-core-hardening/` 68/68 + `resizer-matrix.spec.ts` 7/7 + vitest existentes, corriendo contra el chrome consumido del kit.
- **RN-2 (brand-agnostic estricto):** cero hardcode vitalia en lógica del kit — grep `#01B2F8|vitalia|valeria` (case-insensitive) = 0 en `core/@luana/ui-kit/src/**` lógica (nombres de agente/supervisora vía props; colores vía CSS vars con fallbacks neutros; comentarios/docstrings citando origen permitidos solo en CHANGELOG/README).
- **RN-3 (un solo origen):** vitalia + nicolify importan del kit; cero import cross-brand; la copia local vitalia se BORRA y el espejo nicolify se RETIRA en los mismos tickets del re-wire.
- **RN-4 (fixes v4 sagrados):** key-remount + retry-rAF + `collapsedSize` px + push real ±histPct + `grid-cols-[minmax(0,1fr)]`/`min-w-0` + container queries `@[24rem]` se portan **tal cual** (comentarios ★ Live-fix 2026-06-11 preservados). NO simplificar.
- **RN-5 (ratchet):** allowlists arch (mirror/cross-feature) ENCOGEN, actualizadas en el MISMO commit que cada move.
- **RN-6 (governance):** SEMVER bump kit (minor si additivo / major si breaking — documentado en proposal) + CHANGELOG + proposal → `migrated` al merge.
- **RN-7 (convergencia nicolify):** nicolify adopta el modelo hardened (máquina legacy `valeriaState`/`LuanaRail`/`ShellModeToggle` RETIRADA); sus unit tests se actualizan a la conducta nueva; el cambio visual/UX resultante está sancionado por la proposal (es la convergencia, no una regresión).
- **RN-8 (store SSR-safe):** el store del chrome en el kit usa `@luana/hooks/create-ssr-safe-persisted-store` (CONSUMIR, no recrear — ADR-vitalia-006).
- **RN-9 (live-verify #37):** ≥ colapsar/reabrir/historial/drag ejercidos live en vitalia :3002 + logs limpios. Playwright autenticado válido si Chrome MCP no está.

### Criterios de aceptación (Chris verbatim 2026-06-11)

- **AC-1** Vitalia: `e2e/regression/shell-core-hardening/` 68/68 + `resizer-matrix.spec.ts` 7/7 contra chrome consumido del kit (stack :3002) + vitest/tsc/eslint/arch FULL verdes.
- **AC-2** Nicolify: tsc/vitest/arch verdes + shell renderiza con el kit (e2e/live si stack levanta).
- **AC-3** Kit: tests propios verdes + bump SEMVER documentado + grep brand-token/lógica = 0.
- **AC-4** Allowlists mirror encogen (shrink-only) en el mismo commit de cada move.
- **AC-5** Live-verify #37 real en vitalia + `dod_evidence` en checkpoint.
- **AC-6** Proposal → `migrated` + 07-merge + archive de la story.

## Scenarios (Gherkin ejecutable)

### SC-1 · happy · vitalia consume el chrome del kit sin cambio de conducta
- **given:** chrome movido al kit + vitalia re-wired (imports → `@luana/ui-kit`) + copia local borrada + stack dev vitalia FE:3002/BE:8002 vivo
- **when:** corre la suite completa vitalia (tsc, eslint, vitest full, arch fitness, e2e shell-core-hardening + resizer-matrix, real-backend autenticado)
- **then:** 68/68 e2e + 7/7 resizer-matrix + 0 errores tsc/eslint + vitest 0 fail + arch fitness verde; `git ls-files vitalia/frontend/src/components/shared/shell-organism/` ya no contiene los archivos del chrome lifteado
- **graders:**
  - `{ type: e2e, cmd: "cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-core-hardening/ e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts", expect: "68 passed" }`
  - `{ type: suite, cmd: "cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run src/", expect: "0 fail" }`
  - `{ type: arch_fitness, path: "vitalia/frontend/src/__tests__/architecture/" }`
- **Covers:** [RN-1, RN-3, RN-4, AC-1, Bif-3]

### SC-2 · happy · nicolify converge al chrome del kit
- **given:** espejo nicolify retirado + shell nicolify re-wired al kit con su theming (agent catalog Luana/Abel/Brenda/Christian/Sara/Norvil vía props, tokens nicolify vía CSS vars)
- **when:** corre tsc + vitest + arch fitness nicolify; shell renderiza (e2e/live si stack :3001 levanta, sino render-verify component-level)
- **then:** 0 errores tsc + vitest 0 fail (tests legacy actualizados a conducta hardened) + arch verde + shell monta con supervisor sidebar/strip/historial del kit
- **graders:**
  - `{ type: suite, cmd: "cd nicolify/frontend && npx tsc --noEmit && npx vitest run src/", expect: "0 fail" }`
  - `{ type: arch_fitness, path: "nicolify/frontend/src/__tests__/architecture/" }`
  - `{ type: render_verify, note: "e2e/live :3001 si levanta (Bif-2); fallback render component-level" }`
- **Covers:** [RN-3, RN-7, AC-2, Bif-2]

### SC-3 · happy · kit brand-agnostic versionado
- **given:** organism chrome en `core/@luana/ui-kit/src/**` con props + CSS vars
- **when:** corren tests propios del kit + grep de tokens brand + revisión SEMVER
- **then:** kit tests verdes; grep lógica = 0; `package.json::version` bumpeada + CHANGELOG entry + decisión minor/major documentada en proposal
- **graders:**
  - `{ type: suite, cmd: "cd core/@luana/ui-kit && npx vitest run && npx tsc --noEmit", expect: "0 fail" }`
  - `{ type: grep_gate, cmd: "grep -riE '#01B2F8|vitalia|valeria' core/@luana/ui-kit/src --include='*.ts*' | grep -v test | grep -v CHANGELOG", expect: "0 matches en lógica" }`
- **Covers:** [RN-2, RN-6, AC-3]

### SC-4 · negative · mirror residual o import cross-brand
- **given:** lift completo
- **when:** corren mirror-scan + arch fitness de ambas brands
- **then:** cero archivo del chrome duplicado entre brands; cero import `vitalia/... → nicolify/...` o inverso; allowlists `KNOWN_SANCTIONED_SHELL_MIRROR` (o equivalentes) reducidas — entradas del chrome lifteado REMOVIDAS
- **graders:**
  - `{ type: arch_fitness, path: "vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts", expect: "PASS con allowlist encogida" }`
  - `{ type: grep_gate, cmd: "basename-match chrome files entre {vitalia,nicolify}/frontend/src/components/shared/shell-organism/", expect: "0 espejos del chrome lifteado" }`
- **Covers:** [RN-3, RN-5, AC-4]

### SC-5 · edge · máquina splitter v4 preservada (props-capture-on-mount)
- **given:** chrome del kit montado en vitalia; estados A(closed)/B(chat)/C(chat+historial)
- **when:** ciclos colapsar→strip 44px→reabrir→drag (crece/clamp 320/below-min)→historial push 280→cerrar→persistencia reload→viewports 1280/1100/800
- **then:** `resizer-matrix.spec.ts` 7/7 — strip sin gap, drag vivo post-ciclo, push real (chat nunca < min), sin recorte de contenido (overhang 0)
- **graders:**
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-core-hardening/resizer-matrix.spec.ts", expect: "7/7" }`
- **Covers:** [RN-1, RN-4, AC-1]

### SC-6 · edge · estado persistido legacy en localStorage
- **given:** localStorage con shape/key del store previo al lift (usuario existente)
- **when:** shell del kit monta
- **then:** monta con defaults sin crash ni pantalla rota; estrategia (misma key compat | migración | reset documentado) explícita en CHANGELOG del kit
- **graders:**
  - `{ type: unit, note: "vitest del store kit: hydrate con shape legacy → defaults sin throw" }`
- **Covers:** [RN-8, Bif-5]

### SC-7 · adversarial · fuga de brand al kit
- **given:** revisión adversarial del código del kit
- **when:** grep case-insensitive `#01B2F8|vitalia|valeria|nicolify|luana-orquestadora` en lógica + revisión de defaults de props
- **then:** 0 matches en lógica (solo CHANGELOG/README/comentario-origen permitidos); defaults de props neutros (ej. `supervisorName` SIN default brand); CSS vars con fallback neutro, nunca hex de marca
- **graders:**
  - `{ type: grep_gate, como SC-3 + extensión nicolify-tokens }`
- **Covers:** [RN-2, AC-3]

### SC-8 · live-verify #37 (vitalia)
- **given:** stack dev vitalia vivo, chrome consumido del kit, sesión autenticada real (dr.demo@vitalialat.com)
- **when:** se ejercen LIVE: colapsar → strip 44px → reabrir · abrir historial (push 280) · drag clamp · "+" nueva conversación; se leen logs BE/consola
- **then:** efectos observados en DOM + persistencia + 0 pageerror/console-error/`/api`≥400 + 0 traceback BE; `dod_evidence` registrado en checkpoint
- **graders:**
  - `{ type: live_verify, tool: "Chrome MCP | Playwright autenticado (2ª válida #37)", evidence: "dod_evidence checkpoint" }`
- **Covers:** [RN-9, AC-5]

### SC-9 · edge · pieza imposible de parametrizar (escape valve Chris)
- **given:** una pieza del chrome requiere breaking-change indecidible para ser brand-agnostic
- **when:** se detecta durante build/audit
- **then:** la pieza queda brand-local documentada (HANDOFF-next-session.md + nota en proposal § migrated parcial si aplica) y el resto del lift CONTINÚA — no se bloquea la story entera
- **graders:**
  - `{ type: doc_check, path: "docs/product/stories/platform-lift-shell-chrome-ui-kit/HANDOFF-next-session.md (solo si Bif-1 ocurre)" }`
- **Covers:** [Bif-1]

## Matriz de cobertura

| Bif/RN/AC | SC | Verificación REAL |
|---|---|---|
| RN-1, RN-4 | SC-1, SC-5 | suite e2e real-backend ejercida contra kit (no mocks del chrome) |
| RN-2 | SC-3, SC-7 | grep gate + revisión defaults props |
| RN-3, RN-5 | SC-1, SC-2, SC-4 | files borrados + arch fitness + allowlists encogidas |
| RN-6 | SC-3 | version+CHANGELOG+proposal diff |
| RN-7 | SC-2 | suites nicolify actualizadas verdes + render |
| RN-8 | SC-6 | unit hydrate legacy shape |
| RN-9 / AC-5 | SC-8 | acciones reales ejercidas + logs + dod_evidence |
| Bif-1 | SC-9 | escape valve documentado |
| Bif-2 | SC-2 | degradación criterio nicolify |
| Bif-5 | SC-6 | defaults sin crash |
| AC-6 | merge | proposal migrated + 07-merge + archive |

## Out of scope

- N3 (`EntityWorkspaceLayout`/`EntitySubNavBar`) — ya en kit v0.3.x.
- Tokens de color de marca (cada brand su `globals.css` — ADR-014 homologación es otra story).
- Comunify/lupulo adopción (opt-in futuro — el kit queda listo).
- Cambios de conducta/UX del chrome (refactor puro; la única conducta que cambia es nicolify convergiendo al hardened, RN-7).
- Backend (story FE-only: kit + 2 frontends).

## Prior art applied

Ver `checkpoint.md § prior_art_scan` (engine kit v0.3.0 · mirror nicolify · learnings hardening pre-cargados). Decisión: LIFT + CONVERGER. El corte exacto de componentes (qué archivo entra al kit vs queda brand) lo cierra `/architect` en 03-arch con inventario file-by-file.
