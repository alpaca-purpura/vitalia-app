# Demo Script — C2-T3: Unwind vitalia dual-system → @theme design-tokens

**Story:** core-ds-foundation · Tramo C2 · Ticket C2-T3
**Verificación:** live-verify en G phase (Chris con Chrome MCP — `dod_live_verified` se setea en G, no aquí)
**URL dev-app:** `dev-app.vitalialat.com` (o `localhost:3002`)

---

## Objetivo del demo

Verificar que la migración `@theme + alias-then-migrate` en `vitalia/frontend/src/app/globals.css`
no introduce regresión visual ni de comportamiento, y que los tokens canónicos proyectan correctamente.

**No es una verificación de feature nuevo** — es parity visual + dark mode + status token rendering.

---

## Precondiciones

- [ ] Dev stack levantado: `make dev-vitalia` → esperar `backend healthy + frontend ready`
- [ ] Usuario de prueba: `dr.demo@vitalialat.com` (o el cred per `vitalia/.env.dev`)
- [ ] Chrome DevTools abierto (Console + Network)
- [ ] Consola limpia (cero errores rojos antes de empezar)

---

## Paso 1 — Shell base (sin regresión de layout / tipografía)

1. Navegar a `https://dev-app.vitalialat.com` (o `http://localhost:3002`)
2. Hacer login con `dr.demo@vitalialat.com`
3. Verificar en el shell que:
   - [ ] Ribbon de agentes visible (Lisa, Mateo, Adrián, Lucas, Camila)
   - [ ] Colores de agente correctos (Mateo amarillo, Lisa verde, Adrián cian)
   - [ ] TopBar visible con logo vitalia
   - [ ] Consola sin errores `Uncaught` ni warnings `[vite]`

---

## Paso 2 — Dark mode (dark wiring intacto)

1. En el shell, activar dark mode desde el toggle (ícono de luna/sol)
2. Verificar:
   - [ ] `<html>` tiene `data-theme="dark"` (DevTools → Elements)
   - [ ] Shell se oscurece (background oscuro, foreground claro)
   - [ ] Colores de agente siguen legibles (Camila: check contraste en dark)
   - [ ] `.vt-bg-app` (fondo principal de features) también se oscurece
3. Volver a light mode. Verificar transición limpia.

---

## Paso 3 — Status semantic tokens (success / warning / danger / info)

Navegar a cualquier área con badges de estado (sugerido: Mateo → Agenda → seleccionar un turno).

Verificar que los badges / chips de estado rendean con los colores correctos:
- [ ] **Confirmado / Pagado** → verde (`--success: 142 76% 36%` → `#16A34A`)
- [ ] **Pendiente / Atención** → ámbar (`--warning: 33 91% 44%` → `#D97706`)
- [ ] **Cancelado / Error** → rojo (`--danger: 0 73% 50%` → hsl equivalente)
- [ ] En dark mode: los mismos colores pero más oscuros (overrides dark en :root)

Si se tiene acceso a `vitalia-fase2-mateo-nueva-cita` (en development): verificar el `Badge` de
`@luana/ui-kit` con `variant="success"` / `variant="warning"` en la UI.

---

## Paso 4 — Shadow scale (box shadows)

Verificar en cualquier card/modal/popover:
- [ ] Cards tienen shadow sutil (shadow-sm o shadow-md vía @theme)
- [ ] Modals/drawers tienen shadow más pronunciado (shadow-lg)
- [ ] Ningún elemento tiene shadow negro puro (shadow scale = design-tokens SHADOW)

DevTools → Elements → computed → `box-shadow` en algún card. Debería verse algo como
`0 4px 6px -1px rgb(0 0 0 / 0.1)` (SHADOW.md del package).

---

## Paso 5 — Typography tiers (text-display / text-heading / text-body / text-caption)

Verificar en cualquier pantalla con heading:
- [ ] Título principal de una sub-tab usa `text-display` (2.25rem = 36px) o `text-heading` (1.5rem)
- [ ] Texto de contenido usa `text-body` (1rem = 16px)
- [ ] Metadata/captions usan `text-caption` (0.75rem = 12px)

Los tier utilities son **nuevos** (adición pura, no modifica los `text-sm/lg/xl` existentes).
Si ningún componente los usa aún, verificar que NO hay regresión en los tamaños de fuente
existentes (el `text-display` tier no debe colisionar con `text-4xl`).

---

## Paso 6 — Radius (--radius-lg derivado)

- [ ] Cards grandes / modals tienen `border-radius: 14px` (`calc(0.625rem + 4px) = 14px`)
- [ ] Botones/inputs tienen `border-radius: 8px` (`calc(0.625rem - 2px)`)
- [ ] Chat bubbles tienen `border-radius: 18px` (`--radius-bubble: 1.125rem`)

Valor antes de C2-T3: `--radius-lg: 0.875rem` (literal). Después: `calc(var(--radius) + 4px)`.
Mismo valor numérico (0.625 + 0.25 = 0.875rem = 14px) → **cero cambio visual esperado**.

---

## Pass/Fail criteria

**PASS** (validator `c2_vitalia_visual_parity`):
- Shell renderiza igual que antes (color de agentes + dark mode + layout + shadows)
- Status badges rendean con sus colores (success verde, warning ámbar, danger rojo)
- Consola sin errores CSS/JS nuevos
- Radius de cards/botones visualmente idéntico al pre-C2-T3

**FAIL** → escalate a orchestrator con screenshot + console errors + computed values.

---

## Notas de implementación (para el auditor)

- `@theme` no está en conflicto con `@config "../../tailwind.config.ts"` — v4 los combina; las
  utilidades de `tailwind.config.ts` (bg-primary, bg-success, etc.) siguen funcionando.
- `--color-success/warning/danger/info` en `@theme` son **adiciones** (`bg-success` ya existía vía
  tailwind.config.ts con el mismo valor — `@theme` gana pero el valor es idéntico, cero cambio visual).
- `--shadow-*` en `@theme` override los defaults de Tailwind v4 (más sustanciales que los v4 defaults
  para `shadow-sm`) — efecto intencionado (design-tokens SHADOW = scale de la marca).
- `--radius-lg` cambió de `0.875rem` (literal) a `calc(var(--radius) + 4px)` (derivado) — **mismo
  valor numérico** en vitalia donde `--radius = 0.625rem`.
