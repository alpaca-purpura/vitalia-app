# T-C2-T1 Result — Catálogo generado + gate paridad 1:1

**Story:** core-ds-foundation · Tramo C2 · Ticket C2-T1
**Ticket:** C2-T1 (catálogo generado del source real + gate paridad 1:1)
**Tipo:** platform-engineering · verification_nature: técnica · production_code: false
**Fecha:** 2026-06-25
**Estado:** DONE — 4/4 validators PASS · 319/319 vitest GREEN · tsc 0 errores

---

## Deliverables

| Archivo | Tipo | Descripción |
|---|---|---|
| `scripts/generate_ui_catalog.mjs` | NEW | Generador: cruza 3 fuentes → catalog.json + catalog.md |
| `scripts/_check_catalog_parity.mjs` | NEW | Gate de paridad CLI (--mode=coverage · default parity) |
| `scripts/_assert_parity_gate.mjs` | NEW | Probe TDD (--plant=export-without-story · --plant=retiring-no-story) |
| `core/@luana/ui-kit/tests/catalog-parity.test.ts` | NEW | Arch-test vitest 6 tests (TDD RED→GREEN) |
| `Makefile` (target `ui-catalog`) | EDIT | Makefile target |
| `.gitignore` | EDIT | catalog.json + catalog.md gitignored (R3) |

**Outputs gitignored (auto-gen R3):**
- `core/@luana/ui-kit/catalog.json` — 54 módulos, machine-readable
- `core/@luana/ui-kit/catalog.md` — humano, 7 capas, links Storybook

---

## Fuentes cruzadas (Source A + B + C)

| Source | Path | Resultado |
|---|---|---|
| A — index.ts | `core/@luana/ui-kit/src/index.ts` | 54 módulos (`export * from` + named exports shell) |
| B — react-docgen-typescript | config mirror de `.storybook/main.ts` | `props_source` ref path (no duplicado — Storybook autodocs tiene los props) |
| C — storybook-static | `core/@luana/ui-kit/storybook-static/index.json` | 263 stories · 83 docs · componentPath → story mapping |

---

## Resultados catalog.json

- **54 entradas** (53 vigentes · 1 retiring)
- **RETIRING_NO_STORY = ["AutosaveBadge"]** (exento per canon §2.6)
- **0 vigentes sin story** — paridad 100%
- **7 capas:** Atoms · Molecules · Organisms · Shell · Templates · Foundations · Uncategorized
- Shell: 68 story IDs mapeados vía `componentPath: "./src/index.ts"`
- Archetypes y layout: directorios multi-file → múltiples story titles por entrada

---

## Validators (04-validators-C2.yaml)

| ID | Cmd | Resultado |
|---|---|---|
| `c2_cat_gen_runs` | `make ui-catalog && test -f catalog.json && JSON.parse(...)` | PASS |
| `c2_cat_covers_exports` | `node scripts/_check_catalog_parity.mjs --mode=coverage` | PASS — 54 módulos cubiertos |
| `c2_parity_gate_has_teeth` | `node scripts/_assert_parity_gate.mjs --plant=export-without-story` | PASS — gate falla para vigente sin story |
| `c2_lifecycle_exempts` | `node scripts/_assert_parity_gate.mjs --plant=retiring-no-story` | PASS — retiring exento correctamente |

---

## Quality gates

| Gate | Resultado |
|---|---|
| vitest (core/@luana/ui-kit) | 319/319 PASS (incl. 6 nuevos tests catalog-parity) |
| tsc --noEmit | 0 errores |
| TDD RED→GREEN | Confirmado: RED antes de generate_ui_catalog.mjs · GREEN después |

---

## Decisiones de diseño

**Module-level granularity (no symbol-level):**
- 1 entrada por `export * from "..."` source module, no por cada símbolo exportado
- Para shell: `./organism/shell` → `componentPath: "./src/index.ts"` (special case, 61 stories)
- Para directorios (archetypes, layout): match por prefix de componentPath (`./src/{mod}/`)

**props_source ref only (ponytail):**
- react-docgen-typescript ya corre en Storybook; los props viven en autodocs
- El catálogo referencia el path fuente, no duplica las props
- Satisface "props referenciadas, NO duplicadas" per 03-arch-C2.md §4

**RETIRING_NO_STORY allowlist shrink-only:**
- Seed: `["AutosaveBadge"]` — export vigente en index.ts sin story dedicada per canon §2.6
- La probe `--plant=retiring-no-story` verifica que el allowlist funciona en producción
- El vitest arch-test verifica que entradas en el allowlist tengan `lifecycle: "retiring"` (no `"vigente"`)

---

## Prohibited (verified clean)

- No `core/@luana/ui-kit/src/**` modificado
- No `{brand}/frontend/src/**` modificado
- No `export default` (arch test)
- No cross-brand pollution

---

## Próximos pasos (DAG C2)

- **C2-T2** (design-tokens = SSoT de valores) — independiente de T1, puede arrancar en paralelo
- **C2-T4** (tier-2 extension slots) — independiente de T1, puede arrancar en paralelo
- **C2-T3** (unwind vitalia off dual-system) — requiere T2 primero
