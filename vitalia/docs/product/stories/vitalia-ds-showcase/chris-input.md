# chris-input — vitalia-ds-showcase

> Home vitalia del programa design-system-homologation. Owner `/pm-vitalia` → `/po-ux`.
> Inventario platform (SSoT): `docs/architecture/luana-platform/design-system-inventory-best-of-best.md`.

## 💬 Conversación

### 2026-06-07T23:10 · 🤖 claude · `/pm-vitalia` · 💡 PROPONE
Recibí el handoff de `/pm-luana` con todo el programa de homologación + tu 2ª ronda (revisar mockups,
ver HTML fiel, po-ux dentro del shell). Step 0: 2 stories vitalia abiertas (adrian-embudo developed,
lisa-doctores developing) — NO las toco; esto es Track A independiente.

Abrí esta story `vitalia-ds-showcase` como home vitalia. Su primer deliverable = el **showcase HTML
fiel** que vas a abrir para ratificar la dirección.

**Honestidad sobre "lo que veo ES lo que es" (R-FID):** lo sirve mejor un `/showcase` route en la app
REAL (renderiza los componentes reales). Pero los picks propuestos (EntityInfoCard 8-slots, átomos
sincronizados) **aún no existen como código** → hasta construirlos solo se muestran como mockup.
Secuencia: **ahora** showcase HTML fiel (tokens verbatim de `globals.css` + shell real, NO `_shared.css`
copiado → sin drift) para que ratifiques la dirección; **durable** = `/showcase` route que renderiza lo
real a medida que se construye (R-FID permanente + guard de regresión).

Chaineo a `/po-ux` para producir ese showcase. Cuando lo tengas delante, ratificás (o ajustás): los
picks canónicos · la anatomía de 8 slots de EntityInfoCard · y si el mecanismo durable es route-in-app
(recomendado) o estático-generado. Nada se construye hasta tu OK sobre el showcase.

### 2026-06-07T23:40 · 🤖 claude · `/po-ux` · ✓ APLICADO
Showcase fiel construido + servido: **http://localhost:8893/showcase.html**
(`vitalia/docs/product/stories/vitalia-ds-showcase/mockups/showcase.html`).

Fidelidad por construcción: el bloque de tokens es **verbatim de globals.css** (líneas 30-67),
con `--agent-mateo` en **53° REAL** (corrige el 56° drifteado del `_shared.css` viejo). El shell
chrome (topbar/ribbon 5 agentes+Plataforma/Valeria sidebar/sub-nav) está **reusado** del canónico,
no reinventado. Dark mode (🌓) + splitter states (▏▎50·50) funcionan.

Dentro del shell, la franja N3 navega 6 secciones del catálogo:
- **Átomos** (button ×7 variantes · inputs/textarea/select con estados · badge/chip/switch/checkbox/avatar)
- **N3 Lista/Detalle** (EntityWorkspaceLayout: directorio + entity-subnav + workspace)
- **EntityInfoCard** (3 cajas: doctor/servicio/lead con los **8 slots etiquetados** en azul)
- **Info + Autosave** (Group + autosave-badge + píldora flotante; grupo con estado de error)
- **Page-primitives** (PageHeader · Toolbar/FilterBar · Section · Pagination)
- **Estados** (empty · error · skeleton)

⚠️ Es un **espejo derivado** (estático). El durable = `/showcase` route que renderiza componentes reales.
NO transicioné a refined — espera tu ratificación visual: (a) picks canónicos, (b) anatomía 8 slots,
(c) mecanismo durable route-in-app (recomendado) vs estático generado.

### 2026-06-07T23:58 · 🤖 claude · `/po-ux` · ✓ APLICADO
Iteré el showcase con tus 4 comentarios (mismo HTML, recargá http://localhost:8893/showcase.html):

1. **Tooltips** (Átomos) — tratamiento (label punteado + ⓘ · bubble con flecha al hover/focus = Tooltip
   nicolify Provider+Arrow) + **política**: tooltip = explicación de algo no obvio · NO para info crítica
   (esa va inline) · accesible por teclado · NO solo-hover en mobile.
2. **EntityInfoCard A vs B** (EntityInfoCard) — saqué las etiquetas que ensuciaban + agregué **Opción B**
   (compacta: acento de agente arriba + footer + métricas inline). Elegís A, B, o qué mezclar.
3. **Barrita de color del agente** — aplicada a la info agrupada (verde Lisa a la izquierda), como te gustó.
4. **Color por agente → botones** (Átomos, bloque nuevo) — demo Lisa/Adrián/Mateo/Camila/Global +
   **política**: la acción primaria adopta el color del agente activo (`--agent-active`); texto por contraste
   (Mateo amarillo→texto oscuro); lo semántico (destructivo/éxito) NO cambia; lo global usa `--primary` cian.

Pendiente tu decisión: (b) ¿A o B (o mezcla)? · (a) picks canónicos · (c) mecanismo durable.

### 2026-06-08T00:15 · 🤖 claude · `/po-ux` · ✓ APLICADO
EntityInfoCard reescrita con tu comportamiento (recargá http://localhost:8893/showcase.html → pestaña EntityInfoCard):
- **Grid responsivo 3→5** por fila (`auto-fill / minmax(206px,1fr)`) — movés el splitter (▏▎50·50) y reflúye sola. 5 cards en A y 5 en B para verlo.
- **Card entera clickeable** (cursor + hover + foco por teclado + selección al click).
- **Kebab ⋮** arriba a la derecha, claramente visible (fondo muted), abre menú con **Editar · (contextual: Ver perfil/Ver landing/Abrir conversación/Duplicar) · Eliminar** (danger). El ⋮ no entra a la card (stopPropagation); el resto sí.
- Saqué los botones de acción inline (ya no hacen falta) + las etiquetas de slots que ensuciaban.

Ambos layouts (A densa / B aireada) tienen el mismo comportamiento → la decisión queda en el **layout**.
Pendiente: ¿A o B (o mezcla)? + picks canónicos + mecanismo durable.

### 2026-06-08T00:35 · 🤖 claude · `/po-ux` · ✓ APLICADO
Elegiste **Opción B** + 5 refinamientos (recargá http://localhost:8893/showcase.html → EntityInfoCard):
1. **Densidad** — subí el min de card 206→250px → a este ancho **4 por fila** (antes 5, muy apretadas); sigue variando por tamaño (3-5).
2. **Imágenes** — **todas circulares** (saqué el cuadrado del servicio 🦷).
3. **Indicadores** — en B ahora **repartidos a lo ancho** como en A (grid de columnas iguales, centrados, con banda superior/inferior).
4. A quedó **colapsada** en un `<details>` de referencia (decisión tomada = B).
5. **Info agrupada** — saqué los badges "✓ Guardado hace 2 min" / "● Guardando…" **por grupo** (redundantes): el estado de guardado lo da **UNA sola píldora flotante** por página.

Pendiente tu decisión: **picks canónicos** (¿confirmás los ganadores del inventario?) + **mecanismo durable**
(`/showcase` route en la app real, recomendado, vs estático generado). Seguí mandando ajustes.

### 2026-06-08T00:55 · 🤖 claude · `/po-ux` · ✓ APLICADO
N3 Lista/Detalle ajustado (recargá → pestaña N3 Lista/Detalle):
- Saqué el botón **"‹ Especialistas"** de la tercera franja (redundante — el listado ya está al lado).
- "Especialistas" + "＋ Nuevo" viven en el **header del listado** (columna izquierda), como pediste.
- Agregué un **buscador** ("🔍 Buscar especialista…") debajo del header, por si hay muchos.
La tercera franja del detalle ahora muestra solo: identidad de la entidad + leaf-tabs (Perfil/Agenda/Servicios).

### 2026-06-08T01:05 · 🤖 claude · `/po-ux` · ✓ APLICADO
Contexto copado → armé `HANDOFF-next-session.md` (en esta story) con TODA la esencia: programa,
requisitos R-FID/R-SHELL/R-1SRC, decisiones cementadas (Opción B + comportamiento, autosave 1 píldora,
N3 sin back+buscador, lock scope Fase 0, escala spacing), pendientes (tooltip/color policy OK · picks
canónicos · mecanismo durable), hallazgos (drift, fidelidad por construcción) y todos los paths SSoT.
Las cosas viven en disco (uncommitted) → la sesión nueva las ve. Le di a Chris el prompt para pegar.
Próximo: retomar `/po-ux vitalia vitalia-ds-showcase` iterando el showcase hasta ratificación.

### 2026-06-07T (sesión nueva) · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Retomada la sesión. Step 0: 2 stories code abiertas (adrian-embudo developed, lisa-doctores
developing) — ambas handoff-parked, bucket `code:*`; ds-showcase es bucket `docs` → no choca,
NO las toco (Track A independiente). Leí los 3 SSoT en orden (HANDOFF + este chris-input +
inventario best-of-best + ADDENDUM). Contexto entero recargado: Opción B + comportamiento,
autosave 1 píldora, N3 sin back+buscador, lock Fase 0, spacing 4px, piloto vitalia — todo
cementado. Pendientes vivos: tooltip/agent-color policy · Page-primitives+Estados · picks
canónicos · mecanismo durable. NO arranco builds (tu directiva). Encadeno a `/po-ux` para
seguir puliendo el mismo showcase.html hasta tu ratificación.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ⚠️ DUDA
Recargué grounding entero del showcase (678 líneas, servido en http://localhost:8893/showcase.html).
Las 6 secciones están sólidas y fieles: tokens verbatim de globals.css (`--agent-mateo 53°` correcto),
shell reusado del canónico, dark mode + splitter funcionando. EntityInfoCard B + comportamiento,
autosave 1 píldora flotante + barrita de agente, N3 sin back + buscador — todo cementado y renderizado.

NO construí nada nuevo (tu directiva: no builds, solo pulir hasta ratificar). El showcase ya muestra
todo lo pendiente; lo que falta no es código sino **tus ratificaciones**. Te pregunto en batch (4):
(1) políticas de átomos tooltip + color-por-agente · (2) Page-primitives + Estados (set + look) ·
(3) picks canónicos (4 ganadores del inventario) · (4) mecanismo durable (/showcase route vs estático).
State queda en `refining` esperando tu respuesta. Podés ratificar O mandar ajuste visual libre (opción
"Other" en cada pregunta).

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Respondiste el batch. Cementé 2 + apliqué 1 (recargá http://localhost:8893/showcase.html):

**CEMENTADAS (2):**
- ✅ **Políticas de átomos** (tooltip + color-por-agente) tal como están en el showcase → reglas del DS.
- ✅ **Mecanismo durable = `/showcase` route en la app real** (renderiza componentes reales @luana/ui-kit
  → fiel por construcción + guard de regresión; este `.html` queda como espejo derivado). R-FID resuelto.

**APLICADO — "Falta primitiva":** agregué al showcase las que faltaban del inventario capa 3-4:
- Pestaña **Page-primitives**: FilterBar (orden + toggle vista tarjetas/lista) · PageContainer +
  PageContentStack (frame con el padding del panel + espaciado vertical) · DetailLayout/FormLayout
  (1-col vs 2-col, con la regla "2-col solo si los campos están pareados").
- Pestaña **Estados**: separé el skeleton genérico en **ListPageSkeleton** (N filas) + **FormPageSkeleton**
  (N secciones) y marqué **ErrorState** dedicado con `role=alert`.
Todo con tokens del mismo `globals.css`, Spanish neutro, sin hex/px crudo de styling.

Recargá la pestaña Page-primitives + Estados y decime si el set ahora te cierra o querés ajustar el look.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ⚠️ DUDA
Elegiste **"Cambiar algún pick"** en los picks canónicos. Necesito saber **cuál** de los 4 ganadores
querés revisar antes de confirmarlos (N3 nicolify / autosave vitalia / átomos @luana/ui-kit merge /
EntityInfoCard B sobre StaffCard) — y qué te hace ruido. Te pregunto cuál; con eso itero ese pick puntual.
Los otros 3 quedan en pausa de confirmación hasta que cerremos este. State sigue `refining`.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ⚠️ DUDA
Elegiste **N3** para revisar. Leí el código real (nicolify `EntityWorkspaceLayout` + `EntitySubNavBar`)
y el learning — **encontré una divergencia que vale la revisión**: el showcase **dibuja mal el pick que
dice usar**.

- **Showcase N3 hoy** = **2-columnas persistente** (directorio 300px a la izquierda + detalle a la
  derecha). Eso es en realidad el estilo **vitalia hand-cabled** (`StaffWorkspaceShell`) — el que el
  learning `2026-06-06-n3-...` marca como *la peor factorización* (drift).
- **Nicolify `EntityWorkspaceLayout` (el "ganador" declarado)** = **1 panel, URL-driven**: una franja
  `EntitySubNavBar` arriba (root "Especialistas" como pill + identidad de la entidad + leaves
  Perfil/Agenda/Servicios), contenido **full-width** abajo. El directorio es el **contenido del root-leaf**
  (grilla full-width), NO una columna fija; al elegir una entidad navegás (cambia la URL) a su workspace.

Es una decisión UX de fondo (cuánto espacio al contenido vs lista siempre visible). Te muestro los 2
modelos + un híbrido responsive (preview en la pregunta). Con tu elección **actualizo el showcase N3
para que sea fiel** al pick canónico (hoy no lo es). State sigue `refining`.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Aclaraste tu modelo de N3 y reconstruí la sección (recargá http://localhost:8893/showcase.html →
pestaña N3 Lista/Detalle). Comportamiento implementado:

- **Patrón único** (doctores, servicios, leads…). **Master** = grilla full-width de **cajas
  EntityInfoCard** (reusa el pick) + PageHeader + Toolbar (búsqueda/filtros). NO más lista lateral 300px.
- **Entrás a una caja** (click) → **workspace 1-panel full-width**: franja `‹ Especialistas` (flechita ←
  vuelve a la grilla) + **nombre del doctor como selector `▾`** (dropdown "Cambiar de especialista" →
  cambiás de doctor SIN volver atrás) + leaves (Perfil/Agenda/Servicios) de ESE doctor + contenido abajo.
- Toggle ① Master / ② Detalle para verlo; click en caja entra; `‹` vuelve; `▾` cambia entidad; leaves cambian de sección.

**Reconciliación de decisión:** esto **mata el 2-col persistente** que dibujaba el showcase (era estilo
vitalia hand-cabled, no el EWL ganador). Y **matiza** tu decisión previa "N3 sin back button": ahora el
root-pill `‹ Especialistas` CON flechita ES el camino de vuelta (no un botón aparte) — es lo que pediste.

Verifiqué sintaxis JS (`node --check` OK) + estructura; NO pude screenshot (browser ocupado por tu
sesión), así que el juicio visual es tuyo. Decime si este comportamiento de N3 es el que tenías en mente
o ajusto. Si te cierra → confirmás el pick N3 y seguimos con los otros 3 (autosave/átomos/EntityInfoCard)
+ revisión de Page-primitives/Estados. State sigue `refining`.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Reportaste "no puedo ver el detalle". **Bug encontrado y arreglado:**
- **Root cause:** la función `n3show()` usaba `toggleAttribute('data-show', true)`, que setea el atributo
  a valor VACÍO (`data-show=""`), pero el CSS matchea `[data-show="true"]`. Nunca matcheaba → al togglear
  o entrar a una caja, el master se ocultaba y el detalle NO aparecía → pantalla en blanco.
- **Por qué pasó la verificación previa:** `node --check` valida SINTAXIS, no lógica. Este era bug de
  semántica de `toggleAttribute`. Por eso el screenshot real importaba — y no pude grabarlo (browser
  ocupado). Lección: el verde de sintaxis ≠ verificado (refuerza verification-real-not-200).
- **Fix:** `setAttribute('data-show','true')` / `removeAttribute` explícito → ahora matchea el CSS.

No pude auto-screenshot para confirmar visual: el entorno chrome-devtools-mcp tiene **múltiples MCP
servers huérfanos** de sesiones previas que colisionan el lock del profile de forma no-determinística
(problema de entorno del harness, no del showcase). Maté el chrome de automatización + limpié locks pero
los server-wrappers siguen peleando. El fix es lógicamente certero. Recargá y confirmá que ahora ① Master
↔ ② Detalle, click-en-caja, `‹` volver y `▾` cambiar-doctor funcionan.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Te gustó el N3. Apliqué tus 3 pedidos sobre el dropdown de especialistas → **EntityPicker cimentado**
(recargá http://localhost:8893/showcase.html → N3 → ②Detalle → abrí el `▾`):

- **Buscador** arriba del dropdown (debounce 180ms, filtra por nombre + especialidad, con empty state "Sin resultados").
- **Tope por lote + lazy load:** renderiza de a 12; al scrollear cerca del fondo muestra "Cargando más…" y appendea el siguiente lote. **200 especialistas sintéticos → NO se cargan todos** (footer "Mostrando N de 200").
- **Cimentado eficiente** + a11y: `role=listbox/option`, focus al search al abrir, stopPropagation correcto, avatares por color de agente, nombre+especialidad en 2 líneas.

**Contrato del build real (escrito en la nota del showcase, "cimentar bien"):** búsqueda **server-side**
debounced (no traer todo al cliente) · fetch **paginado** (cap inicial ~20, cursor) · render
**windowed/virtualizado** (react-window/virtualizer) · infinite-scroll o "cargar más" · teclado
(↑↓/Enter/Esc) + a11y combobox. El mockup simula client-side sobre 200 solo para mostrar el comportamiento.

Verifiqué `node --check` (JS válido) + revisión de lógica (usa `setAttribute`, NO el `toggleAttribute`
buggy de antes). **No pude auto-screenshot:** el entorno chrome-devtools-mcp tiene 2+ MCP servers
duplicados que colisionan el lock de forma no-determinística (defecto del harness, no del showcase;
matarlos arriesga romper el MCP de la sesión). Juicio visual tuyo al recargar. Si te cierra → confirmás
el pick N3 + EntityPicker y seguimos con los 3 picks restantes + Page-primitives/Estados.

### 2026-06-07T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Te gustó el EntityPicker. Revisé Page-primitives y arreglé los dropdowns feos (recargá
http://localhost:8893/showcase.html → Page-primitives, N3 master, Átomos):

- **Select canónico Shadcn-style** (reemplaza el `<select>` nativo feo del browser): trigger con borde
  tokenizado + chevron `▾` que rota al abrir + focus-ring + panel estilizado con hover + **check ✓ en
  la opción activa** + agent-color. Handler genérico (un solo patrón para todos).
- **Apliqué a los 6 selects** del showcase (homologación): Átomos (Especialidad) · N3 master toolbar
  (especialidad + estado) · Page-primitives Toolbar (especialidad + estado) · FilterBar (Ordenar).
  **0 `<select>` nativos restantes.**
- Bonus: el "Vista: ▦ ▤" feo de la Toolbar → **viewtoggle** real (tarjetas/lista) consistente con el de FilterBar.

Verificado `node --check` (JS válido) + grep (0 selects nativos · 6 `.sel`). El Select usa
`setAttribute`/`removeAttribute` (patrón correcto, no el `toggleAttribute` buggy). Sigo sin poder
auto-screenshot (mismo defecto MCP servers duplicados). Juicio visual tuyo. Pendiente para cerrar el
showcase: confirmar picks N3/EntityPicker + los 3 restantes (autosave/átomos/EntityInfoCard) + OK a
Estados. State sigue `refining`.

### 2026-06-08T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
Última tanda ("con esto cerramos"). Apliqué tus 3 pedidos (recargá http://localhost:8893/showcase.html
→ N3 → ②Detalle):

1. **N3 detalle ya NO es un contenedor con borde** → la franja (`‹ Especialistas` + picker + leaves) es
   un **tercer ribbon FULL-BLEED**: edge-to-edge, `bg-card` + `border-bottom`, **sticky** — mismo lenguaje
   visual que Ribbon(N1)/SubTabs(N2). Eliminé la card redondeada. (modelo `.leaf` + `.leaf-navbar`)
2. **100% ancho / full responsive:** la hoja ocupa todo el ancho (sin max-width); grids con
   `auto-fill/minmax` reflúyen; agregué colapso de campos pareados en mobile (`grp-fields` → 1-col ≤640px).
3. **Lineamientos del contenedor HOJA (cierre) — escritos en el showcase** (nota 📐 en N3 + refuerzo en
   Page-primitives/PageContainer): (a) hoja 100% ancho · (b) franjas N3 full-bleed (sin padding de
   contenido) · (c) contenido en **PageContainer** (padding `1.25/1.5rem`) + PageContentStack · (d) strips
   sticky arriba. Esto define el **comportamiento de paddings de la hoja** que no veías.

Verificado: `node --check` OK · grep (`.leaf`/`leaf-navbar`/`leaf-body` presentes · 0 container con borde
redondeado · 0 `<select>` nativos). Mismo bloqueo de auto-screenshot (MCP servers duplicados) → juicio
visual tuyo al recargar y scrollear el detalle (la franja queda sticky).

**Showcase: todo lo que pediste está aplicado.** Para RATIFICAR y cerrar (desbloquea los ready packages
del build vía /pm-luana) falta tu OK final a: N3+EntityPicker+contenedor-hoja · los 3 picks restantes
(autosave/átomos/EntityInfoCard) · Estados. Decime "ratificado" (o qué ajustar). State sigue `refining`.

### 2026-06-08T (cont. · po-ux) · 🤖 claude · `/po-ux` · ✓ APLICADO
**RATIFICADO por Chris.** Registré el signoff (`chris_verify.signoff: SATISFIED`) + las 12 decisiones
ratificadas en `checkpoint.md` (`ratified_decisions`). El showcase queda como SSoT visual del best-of-best
para el programa de homologación.

Chris pidió EXPLÍCITO el siguiente paso: que `/pm-luana` garantice que TODO esto lo **respeten
mecánicamente** `/po-ux` (al mostrar funcionalidad en mockups) y `/dev-team` (al programarla), "de una
vez por todas" — generando plantillas/scripts/bindings + reforzando `/harnesses-improvement`. Es trabajo
platform/core (enforcement cross-brand sobre skills + @luana/ui-kit) → dominio de `/pm-luana`.

Encadeno a `/pm-luana` con el contexto completo (showcase ratificado + decisiones + inventario + requisito
de enforcement mecánico). State del showcase: `refining` con `ratified_by_chris: true` (la lifecycle
formal de esta story + el arming de las stories de build las decide /pm-luana).
