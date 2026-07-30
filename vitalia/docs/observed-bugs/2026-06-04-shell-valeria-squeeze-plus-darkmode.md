# Observed bug — Shell-organism: Valeria full-state squeezes agent content + dark mode half-applied

**Found:** 2026-06-04 · live inspection (Chrome DevTools MCP) on `dev-app.vitalialat.com` durante el cierre de `vitalia-fase2-adrian-inbox`. Chris confirmó + dirigió el fix.
**Severity:** alta (UX) — el contenido del agente (inbox 3-pane) queda inusable a anchos comunes (~1104–1400px) con Valeria 'full'; el dark mode se ve roto. Afecta **todas las sub-tabs de agente** del shell (Lisa/Mateo/Adrián/Lucas/Camila), no solo el inbox.
**Scope:** **SHELL-organism** (`vitalia/frontend/src/components/shared/shell-organism/` + `src/stores/shell-store.ts` + `src/app/globals.css`) + un componente inbox (ya resuelto, ver #3). NO es defecto del inbox-feature (telemetry/audit/tenant del inbox están DONE+green).

---

## BUG #1 — Valeria 'full' exprime el contenido del agente (responsive)

### Síntoma (medido live, Chrome MCP)
Viewport 1280, Valeria 'full' abierta: `inbox-desktop` = **696px** (Valeria-chat shell se come ~584px). Dentro del inbox el flex-row = `[list w-80=320px][thread flex-1 min-w-0 = 56px][ContactSidebar w-80=320px]`. El **thread se exprime a 56px** (sliver vertical ilegible — confirmado en screenshot `test-results/shell-organism-adrian-inbo-f5805-*/test-failed-1.png`). En sesión Playwright fresca (Valeria 'full' default más ancha) el thread llega a **0px** → Playwright lo ve `hidden` → los e2e modes/states (AC-4/5/7) hacen timeout 15s.

### Causa raíz
`src/components/shared/shell-organism/useViewportGuard.ts` fuerza `valeriaState` 'full'→'rail' **solo en [768, 1104)** (`FULL_STATE_MIN_VIEWPORT = 1104`), asumiendo que el app-panel necesita 480px (`Valeria 620 + handle + app 480 = 1104`). Pero el inbox 3-pane necesita ~640px+ (list 320 + contact 320 + thread usable). A 1104–~1400px con Valeria 'full' el thread se exprime a ~0–56px. El guard es **viewport-based** y su supuesto (app=480) no contempla las sub-tabs anchas.

### Fix — DECISIÓN DE DISEÑO (Chris): "disminuir el tamaño de Valeria o colapsar cuando se llega a este tamaño"
Opciones (afectan TODAS las tabs de agente — elegir):
- **(a)** Subir `FULL_STATE_MIN_VIEWPORT` para que 'full' solo se permita cuando el app-panel queda ≥ ~700px (umbral ~1400–1544) → en laptops comunes Valeria queda 'rail'.
- **(b)** Hacer Valeria 'full' **más angosta** (ej. 480px en vez de 620) → más ancho para el agente, conservando 'full'.
- **(c)** Container-aware: el shell mide el ancho real del app-panel y degrada Valeria (full→rail→collapsed) por ANCHO DE CONTENEDOR, no por viewport.
- **(d)** Complementario inbox-local: el inbox auto-colapsa su ContactSidebar cuando su contenedor es angosto (ResizeObserver) — bajo riesgo, no toca el shell.

Recomendación: (b)+(d) o (c). Definir umbrales en refining con Chris (live judgment en dev-app).

---

## BUG #2 — Dark mode medio aplicado (shell oscuro, contenido claro)

### Síntoma (medido live)
Tras toggle de tema: `<html data-theme="dark">` seteado, TopBar oscuro (`bg rgb(9,9,11)`) PERO `body` claro (`rgb(248,249,251)`) + ContactSidebar blanco (`rgb(255,255,255)`). El **shell-organism** (topbar + Valeria sidebar) va oscuro; el **contenido del agente (inbox)** queda claro → se ve roto/inconsistente.

### Causa raíz (hipótesis fuerte — confirmar en refining)
El wiring de tema es CORRECTO: `next-themes attribute="data-theme"` (`src/app/providers.tsx`) + `globals.css [data-theme="dark"]` (líneas 75/117/393) + tailwind `darkMode: ['class','[data-theme="dark"]']`. El shell consume tokens que responden a `[data-theme="dark"]`. PERO los componentes del inbox (y probablemente otras features) usan clases de color (`vt-*` custom: `vt-border`, `vt-text-muted`, `vt-text-foreground`, fondos) que **NO tienen definición dark** bajo `[data-theme="dark"]`, o usan colores hardcodeados → se quedan en claro.

### Fix
Auditoría de tokens dark-mode del inbox (y barrido de features): toda clase/token de color user-facing debe tener su variante `[data-theme="dark"]`. Verificar `vt-*` utilities en `globals.css` + los fondos/borders/text de los componentes inbox. Live-verify dark mode en cada sub-tab.

---

## #3 — ContactSidebar colapsable: YA EXISTE (no es trabajo nuevo)
`ContactSidebarToggle` (👤) ya está en `ThreadHeader.tsx` (cableado a `toggleContactSidebar`, store `inbox-store.ts` default `contactSidebarOpen: true`). Solo parece faltar porque el toggle vive DENTRO del thread exprimido (#1) → inalcanzable. Al resolver #1 el toggle queda accesible. (Opcional: BUG #1 opción (d) auto-colapsa el contact cuando angosto.)

---

## Verificación (cuando se arregle)
- Live-verify dev-app (Chrome MCP o Playwright propio — NO el MCP compartido con la sesión de Chris): a 1280/1366/1440 el thread del inbox es usable; dark mode consistente (shell + contenido) en cada sub-tab.
- Desbloquea los e2e modes/states del inbox (AC-4/5/7) que hoy fallan por el squeeze.

## Refs
- `vitalia/docs/archive/2026/stories/vitalia-fase2-adrian-inbox/checkpoint.md` § `e2e_suite_status_2026_06_04_pm` (origen del hallazgo · story archivada 2026-06-04 al merge)
- `src/components/shared/shell-organism/useViewportGuard.ts` · `src/stores/shell-store.ts` · `src/app/globals.css` · `src/app/providers.tsx`
- `src/features/adrian/components/inbox/{AdrianInboxView,ThreadHeader,ContactSidebarToggle}.tsx` · `src/features/adrian/store/inbox-store.ts`
