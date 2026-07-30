# Observed bug — voz-y-tono: contraste verde insuficiente (WCAG 2.1 AA)

**Fecha:** 2026-05-30 · **Origen:** axe scan durante `arreglar-guardado-voz-y-tono` (a11y spec)
**Severidad:** serious (axe) · **Estado:** documentado, no arreglado (visual, fuera de scope del bugfix de guardado)

## Síntoma
En `/lisa/marca/voz-y-tono`, un texto verde `#009966` a 12px (9pt) sobre fondo blanco `#ffffff` tiene
ratio de contraste **3.65:1**; WCAG 2.1 AA exige **4.5:1** para texto normal. axe rule `color-contrast`.
El elemento cuelga del panel `[data-testid="app-panel-slot"]` (probable badge/acento verde — agent-lisa / "Guardado").

## Por qué no se arregló acá
`arreglar-guardado-voz-y-tono` es un bugfix del **guardado** (no toca presentación). Es deuda a11y
**pre-existente** (el verde estaba antes). Arreglarlo = cambio visual/token (oscurecer el verde a un tono
con ≥4.5:1, p.ej. `#007a52` o ajustar tamaño/peso).

## Fix sugerido
- Subir el contraste del token verde usado en texto pequeño (badge "Guardado" / acento agent-lisa) a ≥4.5:1, o
- aumentar tamaño/peso del texto a ≥18px/14px-bold (umbral AA texto grande = 3:1).

## Dónde re-habilitar el test
`vitalia/frontend/e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts` — los describes full-page WCAG están en
`authTest.describe.fixme` (quarantined). Re-habilitar al corregir contraste + cerrar la race de auth del harness.
