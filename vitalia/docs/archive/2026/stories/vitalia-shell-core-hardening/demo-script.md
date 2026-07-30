# Demo Script — vitalia-shell-core-hardening

> **Critical Rule #37 §5 · `definition-of-done-live-verify.md`.** Guion de product demo para que Chris valide el chrome del shell después del hardening de 8 tickets. Ejercer en el stack dev real (`dev-app.vitalialat.com` o `localhost:3002` fallback). En lenguaje de usuario, sin curl ni tokens.

## SETUP (estado inicial)

- **Entorno:** `make dev-app-vitalia` → `https://dev-app.vitalialat.com` (o `localhost:3002` fallback)
- **Usuario de prueba:** `dr.demo@vitalialat.com` (rol doctor, tenant activo)
- **Viewport inicial:** 1280px ancho (Desktop Chrome — ajustar con DevTools si hace falta)
- **Estado inicial:** navegar a `/[tenantId]/lisa/marca` — el shell debe cargar con panel Valeria visible a la izquierda (estado "chat" por default)

---

## FLUJO 1 — Desktop 1280px: estados Valeria + splitter

> Verifica: máquina valeriaOpen, tira strip, historial push, splitter persistido.

1. El shell carga en 1280px → **esperado:** Valeria visible izquierda (~30%), contenido derecha (~70%). Sin chip "web/agéntico" en TopBar.
2. Hacer clic en el botón **"‹"** (colapsar sidebar Valeria) → **esperado:** Valeria colapsa a tira de 44px. La tira muestra el avatar real de Valeria + punto de presencia + label "Valeria". El contenido de la derecha se expande.
3. Hacer clic en la tira de 44px → **esperado:** Valeria reabre al chat (estado B). La tira desaparece, vuelve el panel chat.
4. Con Valeria abierta, hacer clic en el ícono **"◷"** (historial) → **esperado:** aparece un panel de historial a la derecha del chat empujando 260px fijos. El contenido principal se comprime, no se oculta.
5. Hacer clic en **"◷"** nuevamente → **esperado:** el panel de historial se cierra. El splitter vuelve a la posición anterior.
6. Con Valeria abierta, arrastrar el splitter central hacia la izquierda hasta ~320px → **esperado:** el panel Valeria se clampea a 320px mínimo. No puede encogerse más.
7. Refrescar la página → **esperado:** el estado del splitter persiste (misma posición). El valeriaOpen persiste (abierto o cerrado según el último estado).
8. Hacer clic en **"+"** (nueva conversación en header de Valeria) → **esperado:** comienza una conversación nueva en el chat. El historial anterior sigue accesible.

---

## FLUJO 2 — Viewport 1100px: clamp

> Verifica: responsivo entre 1024 y 1280 (clamp zone).

1. Reducir el viewport a 1100px → **esperado:** el shell sigue mostrando Valeria y contenido side-by-side (no drawer). El panel Valeria tiene un mínimo de 320px.
2. Arrastrar el splitter → **esperado:** se puede mover pero no superar el mínimo (320px lado Valeria).

---

## FLUJO 3 — Viewport 800px: drawer

> Verifica: breakpoint <1024 activa drawer Shadcn.

1. Reducir el viewport a 800px → **esperado:** Valeria desaparece del layout inline. Hay un trigger para abrirla (icono o botón visible).
2. Hacer clic en el trigger → **esperado:** Valeria abre como drawer/overlay encima del contenido. No empuja el contenido.
3. Cerrar el drawer → **esperado:** el contenido ocupa el 100% de ancho nuevamente.

---

## FLUJO 4 — Dark mode por sub-tab

> Verifica: dark-aware tokens (bg-background, no bg-white hardcoded).

1. En 1280px, navegar a **Lisa → Doctores → [entrar a un doctor]** (perfil del doctor) → **esperado:** la vista carga correctamente.
2. Activar dark mode con el toggle ☀️/🌙 en el TopBar (segundo ícono desde la derecha) → **esperado:** el fondo del perfil del doctor cambia a oscuro (`bg-background` dark = near-black). No queda ningún rectángulo blanco roto.
3. Ir a **Adrián → Embudo** con dark activo → **esperado:** la vista del embudo carga en oscuro sin parches blancos visibles.
4. Hacer clic en el TakeoverBanner (si visible) con dark activo → **esperado:** el banner aparece en tono ámbar oscuro (`dark:bg-amber-600`), no en amarillo brillante roto.
5. Volver a light mode con el toggle → **esperado:** todo vuelve a colores claros.

---

## FLUJO 5 — Soft-nav: Adrián Embudo → Adrián Inbox

> Verifica: next/link restaurado, sin hard reload.

1. Navegar a **Adrián → Embudo** → **esperado:** carga la vista del embudo con las métricas de embudo.
2. Hacer clic en un KPI badge/chip de métricas que lleva a otra vista (ej. "Conversaciones" o badge de "Recuperar") → **esperado:** la navegación es SPA (sin reload de página completo — el spinner del browser no debería aparecer; la transición es suave).
3. Navegar a **Adrián → Inbox** → **esperado:** la vista del inbox carga sin reload. La URL cambia de `/adrian/embudo` a `/adrian/inbox`.
4. Usar el botón Back del browser → **esperado:** vuelve al embudo sin reload completo (soft-nav preserva el historial del router).

---

## FLUJO 6 — N3 list→detail: Lisa → Staff (doctores) + Lisa → Embudo (leads)

> Verifica: EntitySubNavBar del kit, activeLeaf, back link.

### Sub-flujo A — Doctores

1. Navegar a **Lisa → Doctores** → **esperado:** lista de doctores/staff (directory view). La barra N3 NO aparece aquí (es la lista).
2. Hacer clic en un doctor → **esperado:** aparece la barra N3 con `‹ Doctores | [avatar] [nombre] | Perfil · Horarios · Servicios`. Los leaves están activos.
3. Hacer clic en **Horarios** → **esperado:** la URL cambia al leaf `horarios`. El leaf activo está subrayado/destacado.
4. Hacer clic en **‹ Doctores** → **esperado:** vuelve a la lista de doctores. La barra N3 desaparece.

### Sub-flujo B — Embudo (leads)

1. Navegar a **Adrián → Embudo** → **esperado:** vista kanban del pipeline de leads.
2. Hacer clic en un lead → **esperado:** aparece la barra N3 con `‹ Embudo | [nombre lead] | [leaves]`. Funciona igual que Doctores.
3. Navegar por los leaves del lead → **esperado:** cada leaf carga su contenido. La barra N3 persiste en la parte superior.

---

## EDGE CASES

- **Tira strip con theme dark:** colapsar Valeria en dark mode → **esperado:** la tira de 44px usa colores oscuros (no fondo blanco roto).
- **Drawer en dark mode (800px):** abrir drawer Valeria en dark → **esperado:** el overlay del drawer es oscuro.
- **Viewport resize live:** abrir Valeria en 1280px, arrastrar el viewport a 800px → **esperado:** el splitter inline desaparece, Valeria se cierra en el layout (el store preserva el estado para cuando vuelva a 1280px+).

---

## TEARDOWN

No se crean datos persistentes en este flujo (read-only + navegación + estado de UI). No hay pasos de cleanup.

---

## Resultado (lo firma Chris en G)

> El signoff de la demo **NO vive acá** — vive en `checkpoint.md::chris_verify.signoff` (proceso v5:
> UN solo signoff, en la fase **G** `AWAIT_CHRIS_VERIFY`, ANTES del auditor; `demo_signoff` quedó
> retirado/consolidado). Chris ejerce este script en vivo (dev-app) y registra el resultado allí:
> `result ∈ {SATISFIED | SATISFIED_WITH_FOLLOWUPS | REJECTED}` + `notes` + `open_items`.

<!-- voseo-allowed: template de proceso interno, no user-facing -->
