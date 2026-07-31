---
slug: 2026-06-25-ui-kit-datepicker-atom
state: migrated                       # build cerrado 2026-06-25 · @luana/ui-kit 0.7.0→0.8.0 · tsc 0 · vitest 326/326 (0 regresiones)
migrated_at: 2026-06-25
migrated_summary: "SmartDateTimePicker += prop aditiva showTime (default true). showTime=false → oculta TimePicker + trigger date-only. Cero componente nuevo (extend, no DatePicker). Story date-only + test (date-only + regression-guard). tsc 0 · vitest 326/326. Consumible workspace:* → T-D2 desbloqueado."
kind: extend-existing-canon           # EXTENSIÓN aditiva de SmartDateTimePicker (NO átomo nuevo, NO lift de código brand)
target_package: core/@luana/ui-kit
target_component: src/smart-datetime-picker.tsx   # extender, no crear DatePicker.tsx
origin_story: vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita
contract: vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita/03-arch-delta-availability.md  # § "FE contract — Fecha/Hora split (1a)"
semver_impact: minor                  # 0.7.0 → 0.8.0 · prop aditiva opt-in, cero breaking
ratified_by: Chris                    # "Hay forma de extenderlo en vez de crear uno nuevo… buenos patrones" (2026-06-25)
ratified_at: 2026-06-25
blocks: [vitalia-fase2-mateo-nueva-cita (ticket FE T-D2)]
related: 2026-06-22-ui-kit-nueva-cita-atoms   # P-0 de la misma story
---

# Promotion proposal — Extender `SmartDateTimePicker` con `showTime` (date-only) — NO crear `DatePicker` nuevo

## Resumen

El comentario G #1 de **"Nueva cita"** (agenda de Mateo, vitalia · ratificado Chris 2026-06-25) pide
**separar Fecha de Hora**. La **Hora** ya tiene átomo (`TimePicker`). La **Fecha** necesita un control
date-only.

**Decisión (Chris 2026-06-25):** en vez de crear un `DatePicker` nuevo (duplicaría la lógica de
calendario/popover que `SmartDateTimePicker` ya tiene), se **EXTIENDE `SmartDateTimePicker`** con una
prop aditiva. Sigue buenos patrones (open-closed), no afecta a los consumidores existentes, no duplica
código.

## El cambio (extensión aditiva · NO componente nuevo)

`core/@luana/ui-kit/src/smart-datetime-picker.tsx` — agregar prop:

```ts
interface SmartDateTimePickerProps {
  // ...existentes (value, onChange, timezone, className, placeholder, trigger)...
  /** Cuando false, oculta la sección de hora y formatea el trigger date-only. Default true (conducta actual). */
  showTime?: boolean; // default true
}
```

Comportamiento:
- `showTime` omitido o `true` → **idéntico a hoy** (Calendar + TimePicker en el popover, trigger `dd/MM/yyyy HH:mm`). Consumidores existentes intactos por construcción.
- `showTime={false}` → NO renderiza el `<div>` con `<TimePicker>` (líneas 117-119); trigger formatea `dd/MM/yyyy` (sin `HH:mm`). `onChange` sigue emitiendo UTC ISO (contrato intacto — el form toma la parte fecha y la compone con su `TimePicker` separado).

Uso en el form (T-D2): `<SmartDateTimePicker showTime={false}>` para la **Fecha** + `<TimePicker>` standalone para la **Hora**.

## Por qué extender y no crear `DatePicker` (buenos patrones · pedido de Chris)

- **Open-closed:** se extiende vía prop sin modificar la conducta existente (default preserva todo).
- **Cero duplicación:** reusa el mismo `Calendar mode="single"` + `Popover` + `TimePicker` que el componente ya compone (`smart-datetime-picker.tsx:118,120`). Un `DatePicker` nuevo habría re-implementado calendario+popover = duplicación.
- **Single source of truth:** una sola implementación del calendario en el kit (la del SmartDateTimePicker), parametrizada.
- **Filosofía propia del componente:** ya declara `trigger` slot + "Composición sobre fork (ADR-016 §3)" → la extensión por prop es la dirección canónica.

## Análisis /pm-luana (Modo Core)

- **¿Transversal?** Sí — date-only es genérico cross-brand; la extensión vive en el kit compartido.
- **¿Brand-specific leakage?** No — tz por prop, cero PHI, cero lógica de scheduling.
- **¿Semver?** **minor** (0.7.0 → 0.8.0). Prop aditiva con default que preserva conducta — cero breaking.
- **¿Riesgo downstream?** Mínimo por construcción: `showTime` default `true` ⇒ todo call-site existente sin cambios. Gate: `tsc` + `vitest` del kit verdes (0 regresiones).

## Plan de ejecución (accepted → migrated)

1. Builder extiende `smart-datetime-picker.tsx` (prop `showTime`, default true · render condicional de la sección hora · formato date-only del trigger).
2. Story: agregar variante `--date-only` a la story de SmartDateTimePicker (si no existe story, crearla con default + date-only).
3. Tests: (a) `showTime={false}` no monta el TimePicker + trigger date-only; (b) default (omitido) sigue montando la hora (regresión-guard de los consumidores).
4. Bump `0.7.0 → 0.8.0` + CHANGELOG.
5. Verificación independiente: `cd core/@luana/ui-kit && tsc` exit 0 + `vitest` (0 regresiones).
6. Consumible `workspace:*` → desbloquea el FE delta (T-D2).
7. `state → migrated` + summary.
