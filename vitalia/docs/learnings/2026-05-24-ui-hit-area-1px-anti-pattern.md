---
brand: vitalia
date: 2026-05-24
slug: ui-hit-area-1px-anti-pattern
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: core/luana-core-ui (TS workspace package futuro) o pattern doc en docs/architecture/
origin_story: vitalia-fase1-valeria-rail-history (F1-S5)
origin_commit: a2915423
related_stories: [vitalia-fase1-shell-layout-5050 (F1-S4 — bug origen no detectado)]
---

# UI hit-area 1px anti-pattern — separar visual indicator vs interactive hit zone

**Qué aprendimos:** todo elemento interactivo (drag handle, resize separator, narrow buttons) con ancho/alto visual ≤ 2px es **prácticamente imposible de grabar con mouse precisión normal**. El usuario clickea en píxeles adyacentes esperando hitearlo y no responde. Tests programáticos (Playwright `mouse.move + down + up`) hitean exacto el centro del bbox, por lo cual el bug pasa los E2E pero falla en manual testing.

**Origen:** F1-S4 introdujo el shell-organism resizable Separator (`react-resizable-panels v4` `PanelResizeHandle`) con `className="w-px"` (1 pixel). Lo combinó con un `<aside>` adyacente que tenía `border-r border-border` (otro pixel). Visualmente 2px adjacentes mismo color = parecía un solo border. **Pero solo el segundo pixel (Separator) era draggable.** Usuario clickeaba el primero (border del aside, sin pointer handler).

F1-S5 expuso el bug porque Chris usó el shell en uso real interactivo. F1-S4 Playwright drag programático hiteaba exacto el handle (mouse.move al center del bbox) → pasaba sin detectar usability gap.

**Why (causa fundamental):**

- CSS spec: pointer-events son captured por el TOPMOST element en cada pixel. Border-r del aside NO tiene pointer handler propio (solo borde visual), pero ocupa el primer pixel del "visual indicator". El Separator empieza en el siguiente pixel.
- Mouse precision: en pantallas modernas (high-DPI, retina) el cursor tiene precision sub-pixel pero hit-testing del browser opera con resolución pixel. Hitear 1 pixel específico requiere precision impráctica para uso normal.
- Tests E2E false-positive: `page.mouse.move(handleX + handleW/2, handleY + handleH/2)` siempre hitea exacto. Manual testing varia.

**How to apply (pattern correcto):**

Separar **visual indicator** (delgado, 1-2px) de **interactive hit zone** (generoso, ≥ 8px). Container transparente con pseudo-element centrado:

```tsx
// ❌ ANTI-PATTERN: visual === hit area
<Separator className="w-px bg-border cursor-col-resize" />

// ✅ PATTERN: 1px visual + 8px hit area via ::after pseudo
<Separator
  className={cn(
    "group relative w-2 shrink-0 bg-transparent cursor-col-resize outline-none",
    // Pseudo-element 1px centrado provee el indicador visual
    "after:absolute after:left-1/2 after:top-0 after:h-full after:w-px after:-translate-x-1/2",
    "after:bg-border after:transition-all after:duration-150",
    // Hover/focus expanden indicator a 2px (sin cambiar hit area)
    "hover:after:w-0.5 hover:after:bg-primary/60",
    "focus-visible:after:w-0.5 focus-visible:after:bg-primary",
  )}
/>
```

**Cuándo aplicar:**

- Resize handles / separators (PanelResizeHandle, Splitter, draggable divider)
- Narrow interactive borders (1-3px visual width)
- Tooltips trigger zones que requieren precision
- Cualquier elemento con `cursor: col-resize | row-resize | grab | grabbing`
- Botones con visual icon-only y `w` o `h` < 32px (mínimo accesibilidad WCAG)

**No aplica cuando:**

- Hit area natural es ya ≥ 24px (botones standard, links inline)
- Elemento es visual-only (sin interactividad)
- Borders puramente decorativos sin handler

**Coexistencia con border duplicado:**

Si el container parent tiene `border-r` y el child Separator también provee visual border, **remover el border del parent** (el Separator pseudo cubre el visual). Sino confunde al usuario sobre dónde está el target interactivo.

**Mínimo hit area accesibilidad (referencia WCAG 2.2):**

- **WCAG 2.5.8 Target Size (Minimum)** Level AA: target ≥ 24×24 CSS pixels (con excepciones)
- **WCAG 2.5.5 Target Size (Enhanced)** Level AAA: target ≥ 44×44 CSS pixels
- Resize handles son excepción del 24px requirement (per WCAG note about "essential UI"), pero la práctica recomendada sigue siendo hit area ≥ 8px aunque visual sea 1px

**Test coverage gap a cubrir:**

Los Playwright E2E NO detectan este bug porque hitean exacto bbox center. Para detectarlo, agregar test que **simule precision imperfecta del usuario**:

```ts
test("resize handle has generous hit area (UX)", async ({ page }) => {
  const handle = page.locator("#shell-handle");
  const bbox = await handle.boundingBox();
  // Mouse a 3 píxeles del borde del bbox debería STILL trigger drag
  await page.mouse.move(bbox.x - 3, bbox.y + bbox.height / 2);
  await page.mouse.down();
  await page.mouse.move(bbox.x - 3 + 100, bbox.y + bbox.height / 2);
  await page.mouse.up();
  // assert resize occurred even when clicked 3px to the left of bbox
});
```

O usar regla CSS arch-test que prohíbe `cursor-col-resize|cursor-row-resize` en elementos `w-px|h-px|w-0.5|h-0.5`.

**Cross-brand applicability:**

Cualquier brand con resizable panels (próximas: dashboards Nicolify, Studio comunify, layouts Saasora, etc.) puede tropezar con el mismo issue. Lift candidate a:

- **TS package:** `core/luana-core-ui/src/separator-resizable.tsx` exportando `<ResizableSeparator>` wrapper que envuelva PanelResizeHandle con el pattern w-2 + ::after
- **O Docs pattern:** `docs/architecture/patterns/ui-hit-area.md` documentando el anti-pattern + pattern correcto para futuras stories cross-brand
- **O arch fitness test** transversal: `core/luana-core-ui-conventions/tests/no-narrow-interactive.test.ts` falla si encuentra `cursor-{col,row}-resize|grab|grabbing` en elementos con `w-px|w-0.5|h-px|h-0.5`

**Recomendación trigger para `/pm-luana`:**

Cuando 2da brand introduzca su primer resizable panel layout, evaluar lift inmediato. Mientras tanto, pattern brand-local en `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx`.

## Referencias

- Commit fix: `a2915423` (vitalia-fase1-valeria-rail-history.fix follow-up)
- Spec original: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/03-arch.md` § Separator
- WCAG 2.2 Success Criterion 2.5.8 Target Size (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- react-resizable-panels v4 docs — `PanelResizeHandle` API
- Pattern análogo en Tailwind UI / shadcn `<ScrollArea>` thumb (8px thumb hit area, 4px visual)
