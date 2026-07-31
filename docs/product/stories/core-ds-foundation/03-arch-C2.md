# Contract (C2 · SPINE): core-ds-foundation — inventario-espina + tokens-de-valor + unwind vitalia

> **Technical-story · platform-engineering · `user_visible: false`.** Contract-spec (NO Gherkin).
> Modelo YA fijado por **ADR-016 (accepted 2026-06-25)** — esto es el package de EJECUCIÓN del Tramo C2.
> Suffix `-C2` (no clobbera los deliverables de Fase 0). El checkpoint lo maneja `/pm-vitalia` (story sigue `developing`).

## 0. Context Summary

- **Story:** `core-ds-foundation` · **Tramo:** Fase C · C2 (SPINE) · approach **B1** (incluye el unwind del dual-system de vitalia).
- **Architect run on:** 2026-06-25
- **Surfaces tocadas:** tooling (catálogo + parity-gate) · engine `core/@luana/design-tokens` · engine `core/@luana/ui-kit` (4 tier-2) · brand `vitalia/frontend` (unwind).
- **Surface → builder → auditor mapping** (PM usa para spawnear):

  | Ticket | Surface | Builder | Auditor |
  |---|---|---|---|
  | C2-T1 | tooling: `scripts/` + `core/@luana/ui-kit/catalog.*` + arch-test paridad | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
  | C2-T2 | engine: `core/@luana/design-tokens/src/**` + per-brand no-drift arch-test | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
  | C2-T3 | brand: `vitalia/frontend/src/**` (globals + consumers + arch-test) | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
  | C2-T4 | engine: `core/@luana/ui-kit/src/{EntityInfoCard,chart,rich-select,smart-datetime-picker}.tsx` + 4 stories | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |

- **ENGINE BOUNDARY (T-2, T-4 tocan `core/@luana`):** NO requiere `/pm-vitalia` lift aparte. ADR-016 (accepted) **es** la ratificación + esta es una technical-story core-targeting (la story justifica el build de core, no es un lift WT6). NO abrir promotion proposal. Los src-bugfixes y los value-adds promueven con los commits DS (no cambian API pública del kit salvo el slot aditivo de T-4).
- **Skills consultados:** ADR-016 §1-6 · design-system-canon §2/§2.10/§6.1/§6.8 · frontend-visual-fidelity (Storybook=SSoT). Decisiones tomadas: ver § Existing systems audit + § 4 piezas.
- **CONTEXT-BRIEF source:** sin brief — recon directo (ADR-016 + checkpoint + chris-input §2026-06-25 + código real: design-tokens/src, ui-kit/src/index.ts, vitalia+nicolify globals.css, .storybook/main.ts).
- **cap YAML afectados:** ninguno (`cap_target: null` — infra del DS, no capability de producto). Updates de doctrina (canon/ADR) ya cableados en C1.
- **Arch gates que deben seguir verdes:** `vitalia` arch-suite FE (incl. `test-ds-tokens-lock`, `test-ds-single-token-source`, dark-wiring, `test_no_hardcoded_colors`, `test-semantic-badge-tokens`) · `nicolify` `test-ds-single-token-source` · `core/@luana/ui-kit` render-smoke + tsc + vitest · `make ci-parity`.

## 1. Existing systems audit (NO-NEW-LAYER · §2 ADR-016 = un solo engine/componente)

Audit cross-codebase ejecutado (recon directo · paths reales):

| Sistema existente | Path | Estado | Decisión C2 |
|---|---|---|---|
| Token contract TS (names + value-scales) | `core/@luana/design-tokens/src/{color-names,radius,typography,spacing,z-index}.ts` | spacing+z = VALUES · color/typo/radius = NAMES-only · **no existe shadow** | **EXTEND** (T-2): agregar VALUES a los ejes que faltan + `shadow.ts` NEW. NO nuevo package. |
| Per-brand no-drift guard | `nicolify/.../architecture/test-ds-single-token-source.test.ts` · `vitalia/.../architecture/test-ds-tokens-lock.test.ts` | guarda SPACING/RADIUS-names/TYPO-tiers vs TS | **EXTEND** (T-2/T-3): ampliar el contrato del guard a los nuevos ejes de valor. NO nuevo arch-test paralelo. |
| Render-smoke gate | `scripts/_smoke_storybook.mjs` (gate `sb_render_smoke`) | headless chromium, caza pageerror/render-error | **REUSE** (T-4): la consumer-story de cada tier-2 pasa por este gate existente. NO nuevo runner. |
| Catalog tooling | Fase 0 T-1 (`scripts/generate_ui_catalog.mjs` planned) | aún no built (Fase 0 T-1 no cerró) | **EXTEND/REPLACE-forward**: C2-T1 ES el catálogo generado + parity-gate (supersede el T-1 Fase-0; mismo home, ahora con lifecycle + paridad shrink-only). |
| Storybook autodocs pipeline | `.storybook/main.ts` (react-docgen-typescript + autodocs:"tag") + `storybook-static/index.json` | corre, props+"cuándo usar" viven en stories | **REUSE como SOURCE** (T-1): el catálogo se EXTRAE de este pipeline (cero tooling de props nuevo). |

**Decisión cardinal — NO se reintroduce el CSS shipeado desde el package.** El canon §6.8 (cement 2026-06-16) **evaluó y DESCARTÓ** empaquetar un `.css` importable desde `@luana/design-tokens` (superficie de export versionada + `@source` con path relativo frágil, para ahorrar ~2 líneas/marca). El mecanismo ratificado es: **el package es TS-only (SSoT de los VALORES); cada marca escribe su bloque `@theme` que PROYECTA esos valores; un arch-test per-brand asserta no-drift.** "Consumir vía @theme (patrón nicolify)" = ese mirror GUARDADO, NO un `@import` literal de CSS. Si C2 reintrodujera un CSS-ship → viola canon §6.8 → auditor FAIL. (Un re-litigio de §6.8 sería decisión aparte de `/pm-vitalia`, fuera de C2.)

**Sin cross-brand mirror nuevo.** T-3 toca SOLO vitalia (declarado). nicolify YA es el patrón bueno (no se toca en C2). comunify/lupulo = C3/adopción (fuera de C2).

## 2. Las 4 piezas (contrato · superficie · consumers · invariante · verificación-por-efecto)

### Pieza C2-T1 — Catálogo generado + gate de paridad 1:1

- **Contrato/superficie.** Un script node (`scripts/generate_ui_catalog.mjs`) que cruza 3 fuentes ya existentes y emite el inventario-espina:
  - **fuente A** `core/@luana/ui-kit/src/index.ts` → los ~156 exports (módulo + símbolo).
  - **fuente B** props de **react-docgen-typescript** (MISMO config que `.storybook/main.ts`: `propFilter` no-node_modules, literals-from-enum) — NO se duplican, se referencian.
  - **fuente C** `storybook-static/index.json` (de `build-storybook`) → story-IDs + **tags de lifecycle** + descripción autodocs ("cuándo usar / cuándo no").
  - **Emite:** `core/@luana/ui-kit/catalog.json` (máquina · GITIGNORED output R3) + `core/@luana/ui-kit/catalog.md` (humano · agrupado por capa · cada entry → link `…/iframe.html?id=<story>`). Makefile target `ui-catalog`.
  - **+ Gate de paridad 1:1** = script (`scripts/_check_catalog_parity.mjs`) + **arch-test FE** (vitest, en el package o en `core/@luana/ui-kit/tests/`): por export `vigente` sin story O sin código → **FAIL**; sin entrada en el catálogo → FAIL. **Lifecycle exime:** tag de story `deprecated`/`retiring` exime del requisito de story; export SIN story se trata `vigente` salvo que esté en una **allowlist `RETIRING_NO_STORY` shrink-only** (ratchet, justificación al agregar) — `AutosaveBadge` la siembra (story removida, retiring per canon §2.6). El allowlist **solo encoge**.
- **Consumers.** skill `vitalia-design-system` (deja de hand-narrar → LEE `catalog.md/json`) · cockpit · `/po-ux` + `/architect` (citan la entrada exacta · contrato ADR-016 §5). El gate corre en arch-test/`ci-parity`.
- **Invariante.** Nada en código sin entrada · ninguna entrada `vigente` sin código+story · paridad shrink-only. El catálogo deja de ser doc y se vuelve generado del source (mata el hand-narration: skill dice "19/Z-only", real 23/5-ejes).
- **Verificación-por-efecto (técnica).** `make ui-catalog` regenera + `catalog.json` cubre los 156 exports reales (cero huérfanos). **Probar RED:** plantar un export en `index.ts` sin story → el parity-gate FALLA; quitarlo o darle story → GREEN. Plantar una entrada de catálogo huérfana → FALLA.
- `production_code: false` (tooling/script · no runtime).

### Pieza C2-T2 — `@luana/design-tokens` = SSoT de los VALORES

- **Contrato/superficie.** Ampliar el package TS para que sea SSoT de los **valores** de TODOS los ejes (hoy color/typo/radius son names-only), **respetando el split shared-value ⊥ brand-identity** (reconcilia ADR-016 §4 con RN-5 "agent colors per-brand"):
  - **`shadow.ts` (NEW)** — escala de elevación = **valor COMPARTIDO** (idéntico cross-brand, idioma de `spacing.ts`/`z-index.ts`). p.ej. `SHADOW = { sm, md, lg, … }`. Misma sombra = mismo look.
  - **`typography.ts`** — hoy solo TIERS. Agregar la **escala compartida** (size/line-height/weight por tier) como VALUES. La **font-family queda per-brand** (override declarado).
  - **`radius.ts`** — hoy NAMES. Agregar las **relaciones de escala** (sm/md/lg deltas · control = md−2px) como VALUES; la **magnitud base `--radius` queda per-brand**.
  - **`color-names.ts`** — el contrato de NAMES se queda (identidad per-brand · RN-5). El "value-lift" de color = los **defaults SEMÁNTICOS compartidos** (success/warning/danger/info estructura) + el **contrato de contraste** (agent-mateo/lucas → foreground oscuro, canon §2.8). Los **accents de identidad de agente quedan como superficie de override per-brand** (NO se hornean hexes cross-brand → no rompe RN-5).
  - **Mecanismo de consumo = el RATIFICADO (canon §6.8):** el package NO shipea CSS. Cada marca escribe `@theme` que PROYECTA estos valores; el **arch-test per-brand no-drift** (EXTEND del existente `test-ds-single-token-source` / `test-ds-tokens-lock`) pasa a cubrir los nuevos ejes:
    - ejes shared-value (shadow/typo-scale/radius-scale) → guard de **igualdad** (`@theme` == valor TS).
    - eje color-identidad → guard de **completitud** (todos los NAMES presentes) + **contraste** (no de hex).
- **Consumers.** Las **4 marcas** (vía su `@theme`). En C2: el guard se EXTIENDE en vitalia+nicolify; comunify/lupulo entran en C3/adopción.
- **Invariante.** Una marca NO inventa un valor que no sea (a) un valor de la escala compartida del package, o (b) un override declarado de un token de identidad nombrado. El `@theme` es una **proyección guardada**, no una invención.
- **Verificación-por-efecto (técnica).** Cambiar un valor compartido en el package (p.ej. un `SHADOW.md`) → el render de Storybook (kit + marcas que lo consumen) refleja el cambio. **Probar RED:** mutar un valor del `@theme` de una marca para que difiera del TS → el arch-test no-drift FALLA.
- `production_code: true`. **BLOQUEA C2-T3.**

### Pieza C2-T3 — Migración vitalia OFF dual-system (el unwind B1)

- **Contrato/superficie.** Reemplazar el **dual-system** de vitalia por el `@theme` que proyecta los valores de `@luana/design-tokens` (patrón nicolify guardado). Hoy vitalia tiene: `@config "../../tailwind.config.ts"` (idioma legacy v3) + **105 definiciones `--vitalia-*`** (capa de valores INVENTADOS) consumidas por **~121 archivos** (`var(--vitalia-*)` / clases `.vt-*`) + `--radius: 0.625rem`.
  - **Reemplazar los valores inventados** color/typo/shadow/radius por la proyección de design-tokens en el bloque `@theme` (off-invención).
  - **Eliminar / reconciliar la capa legacy `--vitalia-*`:** los consumers migran al token canónico (`var(--primary)`, `bg-agent-*`, escala compartida). Estrategia recomendada (builder confirma en technical_design): **alias-then-migrate** — los `--vitalia-*` ya están parcialmente aliaseados al canónico (`--vitalia-cian: var(--primary)`); completar el alias de TODOS + migrar los 121 consumers al token canónico + borrar las defs `--vitalia-*` huérfanas. Si un consumer no tiene equivalente canónico (p.ej. `--vitalia-verde-lima` sin Shadcn equiv), promoverlo a un NAME del contrato o documentarlo como override de identidad.
  - **`@config` legacy:** migrar a `@custom-variant`/`@theme` CSS-first es **OPCIONAL** (canon §2.10/§6.8: `@config` + `darkMode:["class",'[data-theme="dark"]']` es **equivalente legacy ACEPTADO** — el gate asserta el EFECTO, no el mecanismo). NO es obligatorio para C2; si el unwind de los `--vitalia-*` es más limpio migrando off-`@config`, hacerlo; si no, dejar `@config` válido. NO regresionar el dark-wiring.
- **Consumers.** La app vitalia entera (debe verse **IDÉNTICA** post-migración).
- **Invariante.** Cero valor de token inventado en vitalia que no derive de design-tokens (salvo override de identidad declarado). El look NO cambia (es refactor de procedencia de valor, no de diseño).
- **Verificación (FUNCIONAL/AMBAS — TICKET DE MÁS RIESGO).** Exige:
  - **live-verify** (dev-app vitalia + Chrome DevTools): recorrer shell + ≥2 hojas reales, confirmar render idéntico + cero regresión visual + dark toggle conmuta.
  - **visual parity:** Storybook brand-switcher vitalia + el showcase/render — antes/después idénticos en los componentes que consumían `--vitalia-*`.
  - **demo** + `dod_evidence` obligatorio (writes/navegación ejercidos + efecto observado + logs).
  - arch-test vitalia (`test-ds-tokens-lock` extendido + dark-wiring + `test_no_hardcoded_colors`) verde + tsc + el `@source "../../../../core/@luana/ui-kit/src"` sigue escaneando (footgun JIT: lift/migración rompe estilos si el scan se rompe — gate = visual, no tsc).
- `production_code: true`. **DEPENDE de C2-T2.**

### Pieza C2-T4 — Superficies de extensión de los 4 tier-2

- **Contrato/superficie.** Los 4 tier-2 hoy fuerzan fork (techo de extensión): `EntityInfoCard` (grid fijo) · `Chart` (wrapper recharts) · `RichSelect` (no windowed) · `SmartDatetimePicker` (UI hardcodeada). Declarar su **superficie de extensión NOMBRADA** (slot / render-prop · toolkit ADR-016 §3) + **1 story-consumidora c/u** que EJERCE el slot:
  - `EntityInfoCard` → **slot** (children/render-prop) para contenido custom de marca (p.ej. footer o un badge custom vía slot) sin tocar el grid fijo. Story: `EntityInfoCard` con badge custom inyectado por slot.
  - `Chart` → **render-prop / children pass-through** a recharts (la marca compone series/tooltips sin forkear el wrapper). Story: una variante con un tooltip/serie custom vía el slot.
  - `RichSelect` → **render-prop del item** (la marca controla el render de la opción) — superficie hacia el windowed-futuro sin forkear hoy. Story: opciones con render custom.
  - `SmartDatetimePicker` → **slot/prop** para la pieza de UI hoy hardcodeada (p.ej. el trigger/footer). Story: trigger custom vía slot.
  - Cambios **ADITIVOS** (props/slot opcionales · back-compat · cero break de consumers actuales · composición sobre config · NUNCA fork del interno).
- **Consumers.** El **builder** (EXTEND no fork) + las consumer-stories. Le da **dientes** al **extension-contract gate** (que se CONSTRUYE en **C3**, no acá): cuando C3 lo cablee, los 4 tier-2 ya declaran superficie + traen story-consumidora → no caen en CHANGES_REQUESTED.
- **Invariante.** Tier-2 = composición/slot, no fork. Cada tier-2 con superficie de extensión declarada + ≥1 story que la ejerce.
- **Verificación-por-efecto (técnica).** La story-consumidora rendea el slot (contenido custom visible) → **render-smoke** (`scripts/_smoke_storybook.mjs`) GREEN. tsc del kit verde (slot opcional, no rompe consumers). **Probar:** la story SIN el slot rendea el default; CON el slot rendea el custom.
- `production_code: true`. **Independiente** (paralelo a T-1).

## 3. Integration design (CONN · ADR-016 §5 + anti-orphan)

Ninguna pieza es isla — las 4 contenciones:

| Pieza | **C**onsumed | **O**n-map (hogar) | **N**avigable | **N**otarized (registrado donde el runtime/gate lo descubre) |
|---|---|---|---|---|
| T-1 catálogo | skill `vitalia-design-system` + cockpit + po-ux/architect | inventario-espina (ADR-016 §4) | `catalog.md` → links a stories | Makefile `ui-catalog` + **arch-test paridad** en `ci-parity` |
| T-1 parity-gate | el flujo SDD (architect cita entradas) | backstop ADR-016 §6 | — | arch-test FE (vitest) corre en la suite del kit + `ci-parity` |
| T-2 tokens | las 4 marcas vía `@theme` | `@luana/design-tokens` (SSoT valores) | exports del package | **arch-test no-drift per-brand** (EXTEND existente) — el "registro" que descubre el drift |
| T-3 vitalia | app vitalia entera | `vitalia/frontend/src/app/globals.css` | dev-app vitalia (live-verify) | arch-test vitalia (tokens-lock + dark-wiring) + `@source` JIT scan |
| T-4 tier-2 | el builder (EXTEND) + consumer-stories | `core/@luana/ui-kit/src` + entrada de catálogo | la story en Storybook | la consumer-story (Notarized) — habilita el **extension-contract gate de C3** |

**Reachability path concreto:** un valor cambia en `@luana/design-tokens` (T-2) → el `@theme` de cada marca lo proyecta (guard no-drift) → los componentes del kit lo renderean → el catálogo (T-1) los indexa → po-ux/architect citan la entrada → el mockup === el render. El gate de paridad (T-1) + el guard no-drift (T-2/T-3) son los puntos donde el runtime/CI lo descubre (cero isla).

## 4. Por surface

### TOOLING (T-1) — `builder-frontend`
- Node ESM script(s) en `scripts/`. Lee `src/index.ts` + react-docgen (MISMO config que `.storybook/main.ts`) + `storybook-static/index.json`. Emite `catalog.json` (gitignored) + `catalog.md`. Makefile `ui-catalog`.
- Arch-test paridad = vitest en `core/@luana/ui-kit/tests/` (consume `catalog.json` + `index.json`). Lifecycle: tag story `deprecated`/`retiring` exime · allowlist `RETIRING_NO_STORY` shrink-only (siembra `AutosaveBadge`).
- TDD: el test de paridad va RED primero (export plantado sin story → FAIL), luego GREEN.

### ENGINE-TOKENS (T-2) — `builder-frontend`
- TS modules en `core/@luana/design-tokens/src/`: `shadow.ts` NEW + VALUES a `typography.ts`/`radius.ts` + semantic/contrast a `color-names.ts` (o un `color-values.ts` si el split lo pide — builder decide; mantener `index.ts` barrel).
- NO shipear CSS desde el package (canon §6.8). El consumo = `@theme` per-brand guardado.
- EXTEND el arch-test no-drift (vitalia `test-ds-tokens-lock` + nicolify `test-ds-single-token-source`) para cubrir los nuevos ejes (igualdad para shared-value · completitud+contraste para color).
- TDD: el test no-drift extendido va RED (un valor de marca que difiere) → GREEN.

### BRAND-VITALIA (T-3) — `builder-frontend`
- `vitalia/frontend/src/app/globals.css` (`@theme`/tokens) + ~121 consumers `var(--vitalia-*)`/`.vt-*` + `tailwind.config.ts` (si se toca el `@config`) + arch-test vitalia.
- Estrategia: alias-then-migrate (los `--vitalia-*` ya parcialmente aliaseados) → migrar consumers al token canónico → borrar defs huérfanas. NO romper `@source` JIT scan ni dark-wiring.
- TDD + **live-verify obligatorio** (dev-app vitalia + Chrome) + visual parity + demo + `dod_evidence`.

### KIT (T-4) — `builder-frontend`
- `core/@luana/ui-kit/src/{EntityInfoCard,chart,rich-select,smart-datetime-picker}.tsx` — slot/render-prop ADITIVO (back-compat) + 4 stories-consumidoras en `core/@luana/ui-kit/stories/`.
- TDD: cada consumer-story pasa el render-smoke (slot rendea contenido custom).

## 5. Cross-Cutting Concerns

- **Spanish neutro LatAm** — strings de stories/catálogo user-facing (NO el harness/docs). Las stories ya lo respetan.
- **Tenant/currency/PII/master-data** — N/A (es DS/tokens/tooling, sin datos de tenant ni monetarios ni PHI).
- **Native-first** — todo nativo (pnpm/vitest/eslint/tsc/storybook en host · NUNCA docker exec). Ports/lanes: si corre en paralelo a otra sesión → `export LUANA_LANE=<x>` antes de Chrome (T-3 usa Chrome DevTools MCP).
- **Visual fidelity (canon §5)** — Storybook = SSoT visual. T-4 stories citan/extienden la entrada del componente. T-2/T-3 verifican el efecto en el render de Storybook + dev-app.
- **Dark-wiring (canon §2.10)** — T-3 NO regresiona el contrato `dark:` → `[data-theme]`/`.dark`. El `@config` legacy de vitalia es equivalente aceptado (gate = efecto).
- **Multi-sesión hub** — buckets: T-1=`code` (tooling/scripts) · T-2/T-4=`code:ui-kit` (engine) · T-3=`code:vitalia-fe`. Commit por pathspec (índice compartido · `solo-chris-single-operator`). T-3 (brand) vs T-2/T-4 (core) = scopes distintos → paralelizables salvo el DAG T-2→T-3.

## 6. Architecture Fitness Impact

- **NEW gate (T-1):** arch-test de paridad catálogo↔código↔story (shrink-only · allowlist `RETIRING_NO_STORY` solo encoge).
- **EXTENDED gate (T-2/T-3):** el arch-test no-drift per-brand crece su contrato a shadow/typo-scale/radius-scale (igualdad) + color (completitud+contraste). Allowlists existentes solo encogen.
- **REUSED gate (T-4):** render-smoke existente.
- **Mantener verde:** vitalia arch-suite FE completa · nicolify `test-ds-single-token-source` · kit tsc+vitest+render-smoke · `ci-parity`.
- **Fuera de C2 (NO construir acá):** promote-gate (C3 · HB-107) · extension-contract gate (C3 — T-4 le da dientes pero NO lo construye) · no-div/no-native-select replication cross-brand (C3) · comunify-eslint (C3).

## 7. Test Surfaces (TDD RED-first)

- **T-1:** vitest paridad RED (export sin story → FAIL) → GREEN · `make ui-catalog` efecto.
- **T-2:** vitest no-drift extendido RED (valor de marca ≠ TS → FAIL) → GREEN · efecto: cambiar `SHADOW.md` se ve en Storybook.
- **T-3:** arch-test vitalia RED→GREEN · **live-verify dev-app** (render idéntico + dark) · visual parity Storybook · demo.
- **T-4:** render-smoke por consumer-story (slot rendea custom) · tsc kit (aditivo no rompe).

## 8. Research Notes

Sin investigación externa novel — Tailwind v4 `@theme`/`@custom-variant`, react-docgen-typescript, Storybook 10 autodocs, recharts wrapper son todos patrones YA en el codebase (recon directo). Fuentes de doctrina (accedidas 2026-06-25):
- `docs/architecture/luana-platform/ADR-016-design-system-inventory-governance.md` (accepted) — §1 ejes ortogonales · §2 árbol reuse/extend/create · §3 toolkit extensión · §4 inventario-espina + tokens · §5 contrato por actor · §6 backstops.
- `docs/architecture/luana-platform/design-system-canon.md` — §2.10 + §6.8 dark-wiring + **el descarte explícito del CSS-ship desde el package** (driver de la decisión cardinal de T-2).
- Evidencia Fase 1: `core-ds-foundation/chris-input.md §2026-06-25` (kit 156/83/0-tier3/4-tier2 · 4 fuentes de drift · color names-only = driver #1 · nicolify @theme bueno · vitalia dual-system).

## 9. Open Questions for PM (`/pm-vitalia`)

1. **Split color shared-vs-identity (T-2).** El contrato fija: shared-value (shadow/typo-scale/radius-scale) = igualdad guardada; color-identidad = completitud+contraste (no hex), preservando RN-5. **Confirmar** que NO se quieren hornear hexes de agente cross-brand (eso rompería la identidad per-brand). Si Chris quisiera una paleta semántica (success/warning/danger/info) compartida por VALOR cross-brand → declarar cuáles, el resto queda override.
2. **`@config` de vitalia (T-3).** El unwind del dual-system NO obliga a migrar off-`@config` (canon §2.10 lo acepta como equivalente legacy). Recomendación: migrar solo si limpia el unwind de los `--vitalia-*`; si no, dejar `@config` válido. **Ratificar** que migrar off-`@config` es opcional (no scope-creep obligatorio).
3. **Riesgo visual T-3.** 121 consumers = el ticket de más riesgo. Confirmar que la live-verify + demo de Chris (G) es el gate de cierre (no solo arch-test verde).
