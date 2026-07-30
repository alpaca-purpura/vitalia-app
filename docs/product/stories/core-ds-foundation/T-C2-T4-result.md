# T-C2-T4 Result — superficies de extensión 4 tier-2 + consumer stories

**Story:** core-ds-foundation · Tramo C2 · Ticket C2-T4
**Ticket:** C2-T4 (ADR-016 §3 — named additive extension surfaces, composición>fork)
**Tipo:** platform-engineering · verification_nature: técnica · production_code: true
**Fecha:** 2026-06-25
**Estado:** DONE — tsc 0 errores · vitest 313/313 GREEN · render-smoke 274/274 PASS
**Commit:** `158c14d8` — `origin wip/vitalia`

---

## Deliverables

| Archivo | Tipo | Superficie |
|---|---|---|
| `core/@luana/ui-kit/src/__tests__/tier2-slots.test.tsx` | NEW | TDD RED→GREEN: 6 tests slots |
| `core/@luana/ui-kit/src/EntityInfoCard.tsx` | EXTEND | `footer?: React.ReactNode` slot |
| `core/@luana/ui-kit/src/chart.tsx` | EXTEND | `footer?: React.ReactNode` slot + `useChart` ya exportado |
| `core/@luana/ui-kit/src/rich-select.tsx` | EXTEND + FIX | `renderItem?` render-prop + `FormControl` removal |
| `core/@luana/ui-kit/src/smart-datetime-picker.tsx` | EXTEND | `trigger?: React.ReactNode` slot (asChild) |
| `core/@luana/ui-kit/stories/EntityInfoCard.stories.tsx` | EXTEND | `ConSlotFooter` consumer story |
| `core/@luana/ui-kit/stories/data.Chart.stories.tsx` | EXTEND | `ConFooterCustom` consumer story |
| `core/@luana/ui-kit/stories/inputs.RichSelect.stories.tsx` | EXTEND | `ConRenderItem` consumer story |
| `core/@luana/ui-kit/stories/inputs.SmartDatetimePicker.stories.tsx` | EXTEND | `ConTriggerCustom` consumer story |

---

## Extension surfaces (por componente)

### EntityInfoCard — `footer?: React.ReactNode`

Slot opcional después del status chip. Renderiza en `<div data-testid="entity-info-card-footer-{testId}">`.
Sin footer → testid ausente (back-compat total). Consumer: `ConSlotFooter` story con badge warning de lista de espera.

### ChartContainer — `footer?: React.ReactNode`

Slot opcional debajo de `<ResponsiveContainer>`. Renderiza en `<div data-chart-footer={chartId}>`.
`useChart` ya estaba exportado en línea 327 — sin cambio en exports.
Consumer: `ConFooterCustom` story con texto de fuente/aclaración debajo de la línea.

### RichSelect — `renderItem?: (option: RichSelectOption) => React.ReactNode`

Render-prop que override el layout label+descripción por item. Sin prop → layout default preservado.
Consumer: `ConRenderItem` story con color dot semántico por opción.

**Fix incluido (bug pre-existente):** `RichSelect` tenía `<FormControl>` hardcodeado internamente
→ crasheaba fuera de un `<Form>/<FormField>` stack (error: `useFormField should be used within <FormField>`).
La propia codebase tenía el workaround documentado en `ResumenView.tsx` (`// ponytail: plain Select...`).
Fix: eliminado `FormControl` + `import { FormControl }` del componente. Per patrón Shadcn, el consumer
wrappea en `FormItem/FormControl/FormField` si necesita RHF. Back-compat: consumidores standalone ahora funcionan;
consumidores RHF inalterados (ya tenían su propio wrap).

### SmartDateTimePicker — `trigger?: React.ReactNode`

Slot vía `PopoverTrigger asChild` + `React.isValidElement(trigger)` guard.
Sin trigger → `<Button>` default con CalendarIcon (back-compat total).
Con trigger → Popover clona el elemento y merge el handler open/close.
Consumer: `ConTriggerCustom` story con botón compacto `📅 {fecha formateada}`.

---

## Gates

| Gate | Resultado |
|---|---|
| `tsc --noEmit` (`core/@luana/ui-kit`) | **0 errores** |
| `vitest run` (kit suite completa) | **313/313 PASS** (sin regresiones) |
| `render-smoke` (Storybook build → serve → chromium headless) | **274/274 stories CLEAN** |
| TDD RED→GREEN | 6 nuevos tests en `tier2-slots.test.tsx` (EntityInfoCard×2 + RichSelect×2 + SmartDateTimePicker×2) |

Chart slot no tiene tests jsdom (recharts requiere `ResizeObserver` no disponible en jsdom sin mock);
verificado vía consumer story `ConFooterCustom` + render-smoke.

---

## Skills consultadas

- `frontend-expert` — runtime-quality-checklist: back-compat verificado (optional props, `!= null` guards);
  `PopoverTrigger asChild` + `React.isValidElement` patrón correcto para slots de trigger Radix.
- `.claude/rules/frontend-visual-fidelity.md` — composición desde kit existente; no reinventar primitivas.
- ADR-016 §3 toolkit: slot/render-prop pattern; additive-only; no fork.

---

## Decisiones

- **`footer != null` (no `Boolean(footer)`)**: acepta `0` y `""` como contenido intencional.
- **`React.isValidElement(trigger)`**: guard en SmartDateTimePicker previene crash si `trigger` es
  `true`/`false` accidental (PropTypes vacío es posible desde TS opcional).
- **FormControl fix alcance mínimo**: solo se eliminó el import + wrapper; cero cambio a la lógica
  de Select, opciones, o valor. Consumidores RHF existentes no se afectan.

---

## Scope NOT implementado

Ningún out-of-scope según `06-tickets-C2.yaml` C2-T4 deliverables.

---

## Siguiente ticket

**C2-T3** (vitalia `globals.css` unwind 105 hardcoded defs → @theme projection) precede a este ticket
por dependencia en C2-T2 VALUES, pero C2-T4 era independiente y se ejecutó en paralelo.
