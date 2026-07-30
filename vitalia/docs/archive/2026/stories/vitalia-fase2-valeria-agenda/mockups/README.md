# F2-S1 valeria-agenda — Mockups HTML per-component

**Gate bloqueante:** `vitalia/.claude/rules/shell-mockup-per-component.md` (cement 2026-05-22).
**Estado:** ⏳ pending — Chris debe ratificar 10/10 antes de transition `refining → refined`.

## Inventario (10 archivos)

| # | File | Contenido | Status |
|---|---|---|---|
| 0 | `agenda-cockpit-grid.html` | TOC navegable + 9 mini-previews + dark mode toggle | ✅ drafted v1 — awaiting Chris ratify |
| 1 | `agenda-day.html` | DayCalendar timeline 8-18h × 3 doctores (García/Ríos/Vega), 12 slots LatAm + virtualización note | ✅ drafted v1 |
| 2 | `agenda-week.html` | WeekCalendar grid 7d × 9-15h (vista default) con 18 slots LatAm + chips + crear-cita button + footer stats | ✅ drafted v1 |
| 3 | `agenda-month.html` | MonthCalendar grid 5 semanas con dots agregados por día (success/warning/destructive counts) + today highlight | ✅ drafted v1 |
| 4 | `slot-states-matrix.html` | 12 cells base (4 estados pago × 3 orígenes) + 4 estados interactivos + legend mapping completo | ✅ drafted v1 |
| 5 | `appointment-drawer.html` | Drawer 440px abierto · resize handle · 5 acordeones (Turno+Pago expanded) · disabled "Ver ficha" tooltip · Dialogs Cancelar/No-show | ✅ drafted v1 |
| 6 | `cobrar-saldo-subform.html` | 10 states (collapsed/expanded × 4 currency + submitting + success + 2 errors + conflict-409) · MX disclaimer fiscal | ✅ drafted v1 |
| 7 | `preset-filters.html` | 5 chips × 4 estados (default/hover/active/focus) + spec table mapping URL params → SQL filter + empty state | ✅ drafted v1 |
| 8 | `crear-cita-dropdown.html` | DropdownMenu 3 opciones + 3 form variants (walk-in/teléfono/desde-existente con autocomplete PHI masked) + Mobile FAB ref | ✅ drafted v1 |
| 9 | `mobile-drawer-fullscreen.html` | <768px iPhone-frame · 2 vistas side-by-side (DayCalendar + bottom-sheet abierto) · constraints checklist | ✅ drafted v1 |

## Constraints obligatorios (per shell-mockup-per-component.md)

- ✅ Tailwind CSS CDN (`https://cdn.tailwindcss.com`) o precompilado equivalente
- ✅ Tokens Vitalia via CSS vars (`:root { --background: ...; --agent-valeria: ...; ... }` + `.dark`)
- ✅ Datos LatAm realistas (no Lorem ipsum, no USA placeholders)
- ✅ Spanish neutro LatAm (validar contra `.claude/rules/spanish-text.md` glosario)
- ✅ TODAS las variantes del componente visibles
- ✅ Dark mode toggle local en cada mockup
- ✅ Sin frameworks externos (NO Bootstrap, NO Material UI)
- ✅ PHI masked visual: `P. Hernández`, `12.***.***`, `+51 9** *** 423`, `p***@gmail.com`

## Servir local para revisión Chris

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/agenda-cockpit-grid.html
# Itera con /po-ux hasta ratificación de los 10
```

## Cementación post-ratify

Cuando Chris ratifica los 10/10 → update `checkpoint.md` frontmatter:

```yaml
ratified_visual_by_chris: true
ratified_visual_at: 2026-MM-DDTHH:MM:SSZ
ratified_visual_iter: N
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/agenda-cockpit-grid.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/agenda-day.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/agenda-week.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/agenda-month.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/slot-states-matrix.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/appointment-drawer.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/cobrar-saldo-subform.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/preset-filters.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/crear-cita-dropdown.html
  - vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/mobile-drawer-fullscreen.html
```

Después → transition `refining → refined` + AUTO-CHAIN `/architect vitalia vitalia-fase2-valeria-agenda`.

## Referencia visual macro

- Mockup integral del shell: `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html`
- Mockup F1-S10 (patrón TOC + standalone): `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/mockups/empty-states-grid.html`
- Slice-1 agenda mockup (concept legacy refactor): `vitalia/docs/archive/2026/stories/vitalia-slice-1-agenda/02-design-ui-mockup.html`
