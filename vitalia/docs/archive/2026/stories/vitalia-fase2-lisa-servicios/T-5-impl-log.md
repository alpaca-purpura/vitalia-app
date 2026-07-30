# T-5 impl-log — FE · NumberWithUnit (shared) + field primitives (moléculas)

**Story:** vitalia-fase2-lisa-servicios · **Ticket:** T-5 · **Surface:** frontend · **Agent:** builder-frontend (workhorse)
**Cap:** clinics.lisa.servicios · **Branch:** wip/vitalia

## Plan (technical_design — pre-code)

### D1 — Design-system-first (reúso)
- **Átomos `@luana/ui-kit` (CONSUME, no recrear):** `Input`, `Textarea`, `Select` (raw, sin RHF), `Button`, `Badge`, `RichSelect` (shipped 0.4.1 — RN-32). Verificado: RichSelect envuelve trigger en `FormControl` (requiere contexto RHF) → para el unit-picker standalone de NumberWithUnit se usa `Select` raw, NO RichSelect (no hay RHF en una molécula suelta).
- **Tokens `globals.css`:** `--agent-lisa` / `bg-agent-lisa-soft` / `text-agent-lisa` (chip-origen estándar), `text-vitalia-warning` (estrellas testimonios), `--radius` vía `rounded-lg`/`rounded-full`/`rounded-md`, `bg-muted`/`text-muted-foreground`. CERO hex arbitrario. CERO `text-[Nrem]` arbitrario (canon §0 — todo `text-xs`).
- **`cn()`** desde `@/lib/cn`.
- **NumberWithUnit** = único net-new primitive → `components/shared/NumberWithUnit.tsx` (vitalia-local shared, lift-candidate `/pm-luana` documentado — NO lift en esta story per dispatch/arch).

### D2 — Mockup adherence (servicio-workspace.html + _shared.css)
Portado: ★★★★★ testimonios (text-vitalia-warning), pares Q/A FAQ, par tag/respuesta objeciones, chips de palabras-clave (Badge secondary + ✕), chip-origen estándar (agent-lisa-soft + 📚) vs personalizado (muted), barra completitud ficha. Estados: empty (`*-empty` testid) / default / disabled por molécula.

### D3 — Scope discipline
Implementado SOLO las 9 moléculas + NumberWithUnit scopeadas en T-5. La composición en el workspace (5 leaves), catálogo grid, escalera dnd, autosave wiring → T-6/T-7 (NO en este ticket). Las moléculas exponen `onChange` (caller owna persistencia/autosave) — no hay botón "Guardar" ni modal de edición (form-runtime-array.md).

### Tests (TDD RED→GREEN, matriz test-design-doctrine FE component + hook)
- NumberWithUnit: render value+unit · onChange parsea numérico · min validation (no emite < min) · combobox presence (open-flow → Playwright).
- RungPicker: locked state. ModalidadPicker: discriminated reveal. VariantsRepeater: add/remove. FichaCompletenessChip: count. + Testimonials/Faq/Objecion/TagInput/ChipOrigen: render/empty/add/remove/patch + de-dupe case-insensitive (TagInput).

### Integración (CONN)
Moléculas exportadas vía barrel `features/lisa/index.ts` (named exports, sin default). Las consumirá `LisaServiciosView` (T-7) dentro de la ruta `(shell-organism)/lisa/servicios` ya cableada. NO quedan islas: cada molécula es hoja consumida por el workspace de T-7.

### Header de cap
Todo `.tsx` de producción nuevo lleva `// cap: clinics.lisa.servicios` + `// story-origin: vitalia-fase2-lisa-servicios T-5` en líneas 1-2.

## Decisiones / desvíos durante build

1. **happy-dom `user.clear()` flaky en `type="number"`** → tests de edición de NumberWithUnit usan `fireEvent.change(input, { target: { value } })` (set atómico, sin append). Lógica del componente correcta; el bug estaba en el test (esperaba 30, obtenía 1030 por append a "10").
2. **Controlled input + spy onChange** que no actualiza value → desync React/DOM → harness `StatefulNumber` con `useState` en el test.
3. **RichSelect NO usable standalone** (envuelve trigger en FormControl → necesita RHF) → unit-picker de NumberWithUnit usa `Select` raw. Documentado.
4. **Canon §0 — arbitrary font-size:** 5 ocurrencias `text-[0.625rem]`/`text-[0.6875rem]` (micro-labels 10-11px) → `text-xs` (token). Eslint `@luana/ds/no-arbitrary-value` las bloqueaba.
5. **Canon §2.7 — raw layout `<div>` ratchet (shrink-only, baseline 301/121):** las moléculas array + pickers tenían `<div flex-col gap->` (stacks verticales) y `<div grid-cols->` (pares de campos / segmented pickers).
   - Stacks verticales → `space-y-N` (equivalente, NO flageado).
   - Pares de campos 2-col (Testimonials autor/origen, Objecion tag/respuesta/del, Variants name/price/note/del) → `space-y-2 sm:flex sm:gap-2 sm:space-y-0` + hijos `sm:flex-1` (responsive, sin `flex-col`+`gap` ni `grid-cols`).
   - Segmented pickers (RungPicker 5-rung, ModalidadPicker 3-opt) → `flex gap-1.5` + botones `flex-1 basis-0` (ancho igual, sin `grid-cols`). Semánticamente idéntico, canon-clean.
   - Resultado: ratchet vuelve a baseline (302→301, 122→121). CERO nuevo layout-div.

## §11 CONTEXT-BRIEF gaps
CONTEXT-BRIEF.md validado (`Validator pass` poblado, `Faithfulness flag` no-blocking). Sin gaps §11 que afecten T-5 (moléculas presentacionales puras, sin PHI, sin tenant_id). NumberWithUnit lift a @luana/ui-kit diferido a `/pm-luana` (no bloquea esta story).

## Gate results (G5)
- `npx tsc --noEmit` → 0 errores
- `npx eslint src/features/lisa/components/servicios src/components/shared/NumberWithUnit.tsx src/features/lisa/index.ts` → 0 errores
- `npx vitest run` (10 files T-5) → 45/45 PASS
- `npx vitest run src/__tests__/architecture/` → 187/187 PASS (div-layout ratchet, native-select, ds-tokens-lock, FSD boundaries, no-default-export, react-query-keys, no-phi-url, no-clerk-organizations)
