# NPSTagBadge

Componente compartido cross-feature para mostrar un puntaje NPS (Net Promoter Score) con colores semánticos según la categoría del paciente.

**Ubicación:** `src/components/shared/nps/`  
**Tipo:** Server Component (sin estado ni efectos — compatible SSR/RSC)  
**Accesibilidad:** WCAG AA — `role="status"` + `aria-label` descriptivo en español neutro

---

## Uso

```tsx
import { NPSTagBadge } from "@/components/shared/nps";

// Básico
<NPSTagBadge score={9} />

// Con tamaño y variante
<NPSTagBadge score={5} size="sm" variant="chip" />

// Sin datos (graceful fallback)
<NPSTagBadge score={null} />
```

---

## Props

| Prop        | Tipo                          | Default   | Descripción                                             |
| ----------- | ----------------------------- | --------- | ------------------------------------------------------- |
| `score`     | `number \| null \| undefined` | —         | Puntaje NPS 0–10. `null`/`undefined` muestra "Sin NPS". |
| `size`      | `"sm" \| "md" \| "lg"`        | `"md"`    | Tamaño visual del badge.                                |
| `variant`   | `"badge" \| "chip" \| "tag"`  | `"badge"` | Forma del contenedor.                                   |
| `className` | `string`                      | —         | Clases CSS adicionales aplicadas al elemento raíz.      |

---

## Categorías y colores

| Rango | Categoría | Color                                             |
| ----- | --------- | ------------------------------------------------- |
| 0–6   | Detractor | Rojo (`vt-bg-danger-12` + `vt-text-danger`)       |
| 7–8   | Pasivo    | Amarillo (`vt-bg-warning-12` + `vt-text-warning`) |
| 9–10  | Promotor  | Verde (`vt-bg-success-12` + `vt-text-success`)    |

Todos los colores usan clases `vt-*` de `globals.css`. No hay literales `hsl()`/`#hex` en el componente (arch fitness FE-A1).

---

## Variantes de forma (`variant`)

| Valor   | Radio                        | Uso recomendado            |
| ------- | ---------------------------- | -------------------------- |
| `badge` | `var(--radius)` = 0.5rem     | Default — uso general      |
| `chip`  | `var(--radius-pill)` = 999px | Pill — inline filter chips |
| `tag`   | `rounded-sm`                 | Compacto — celdas de tabla |

---

## Accesibilidad

- `role="status"` en todos los casos (incluyendo fallback "Sin NPS").
- `aria-label`:
  - Con score: `"Calificación NPS 9, categoría promotor"`
  - Sin score: `"NPS: sin datos"`
- El número de score tiene `aria-hidden="true"` (lo lee el `aria-label`).
- Atributo `data-nps-category="detractor|passive|promoter"` para selectores CSS y tests estables.

---

## Casos de uso en Vitalia

- **Inbox** → filter chip inline (variante `chip`, tamaño `sm`)
- **Fidelización stat card** → badge grande (variante `badge`, tamaño `lg`)
- **Tabla NPS / detalle paciente** → tag compacto (variante `tag`, tamaño `sm`)

---

## Notas

- Puntajes fuera de rango 0–10 se clampean automáticamente (`Math.max(0, Math.min(10, Math.round(score)))`).
- Promoción a `@luana/ui-kit` planificada cuando una segunda brand adopte NPS (gate Slice 2).
