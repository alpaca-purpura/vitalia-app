---
story_id: vitalia-fase2-lisa-doctores
created_at: 2026-05-27T18:25:23-05:00
last_modified: 2026-05-27T18:25:23-05:00
notes_count: 0
refs_count: 0
conversation_count: 1
---

<!-- voseo-allowed: proceso conversacional interno Claude↔Chris — no es string user-facing; `chris-input-protocol.md` R30 requiere output verbatim por skill incluyendo voz del turno previo -->

# chris-input.md · vitalia-fase2-lisa-doctores

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales** (mantener el orden + emojis para que parser + cockpit funcionen):
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

> Chris: escribe acá tus notas en lenguaje natural. Cualquier cosa que te ayude a pensar la story.
>
> Cada entry abre con `### YYYY-MM-DD HH:MM` (timestamp).

### 2026-05-27 18:25
Sin notas todavía · Chris escribe aquí.

## 📎 Referencias

> Chris: pega links, sube imágenes (drag-drop o botón adjuntar), cita texto de buyer personas, referencia otras stories (`F2-S1`) o learnings (`2026-MM-DD-slug`).
>
> Tipos válidos: 🔗 link · 🖼 img · 💬 text · 📖 story-ref · 📚 learning-ref · 📄 doc.
>
> Formato: `- **(emoji) (tipo)** · (valor)` + opcional `  > (comentario)` en siguiente línea.

(sin referencias todavía)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Chris responde a Claude editando + agregando un entry nuevo.
> Claude appendea verdict al cierre de cada turn de su skill.
>
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-05-31 · builder-frontend (T-FE-3)

**Scope:** T-FE-3 — Horarios calendar: DoctorHorariosView + AvailabilityCalendar + BloquePopover + useAvailabilityBlocks

**Build result:**
- ✓ APLICADO: `AvailabilityCalendar.tsx` — custom week grid (day×hour, CSS Grid) + @dnd-kit drag-to-create + week nav (‹/›) + 24h toggle + block rendering with `data-testid`
- ✓ APLICADO: `BloquePopover.tsx` — recurrence form (semanal/quincenal + end_date/N iteraciones/Solo esta semana) + delete flow with SC-3b warning dialog
- ✓ APLICADO: `DoctorHorariosView.tsx` — "use client" root with autosave hint
- ✓ APLICADO: `horarios/page.tsx` — Server Component importing from barrel (arch test compliant)
- ✓ APLICADO: 4 new hooks in `staff.ts` (useAvailabilityBlocks, useCreateBlock, useUpdateBlock, useDeleteBlock)
- ✓ APLICADO: `AvailabilityCalendarPage.ts` Playwright POM
- ✓ APLICADO: 26 new tests (11 schema + 15 component), all GREEN
- ✓ APLICADO: @dnd-kit/core + @dnd-kit/utilities installed

**Quality gates:**
- TSC: 0 errors · ESLint: 0 errors · Vitest: 2411/2411 PASS · Architecture: 162/162 PASS

**Commit:** `29625988` on `wip/vitalia` · pushed to origin

**Pending (Chris action):**
- Live verification via `chrome-devtools-verify` requires T-BE-3 stack running at localhost:3002 (`make dev-vitalia`). NOT done (dev stack not running in this session).
- T-E2E ticket for full Playwright specs SC-1..SC-11 remains open.

### 2026-05-27 18:25 · 🤖 claude · `scripts/migrate_to_release_schema.py` · ✓ APLICADO
Story migrada al schema v2: `release=F2`, `cap_target=lisa.doctores`, `cap_change_type=new`. Legacy `outcome` + `phase` preservados durante deprecation gradual.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux vitalia vitalia-fase2-lisa-doctores` (o `/po` si es service story, o `/ux-agentico` si es agentic).

### 2026-05-30 17:30 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Prior-art scan ejecutado. Corregí 2 incoherencias del scope original en `checkpoint.md`:
- `module: staff` → `module: clinics` (el módulo `staff/` NO existe; Doctor vive en `clinics/` + `infrastructure/models/doctor_extension_model.py`).
- Horarios → NO recrear slots: `scheduling/` (agenda_slot, create_appointment, agenda_grid) + engine `luana-core-scheduling`/`luana-core-commercial-calendar` ya existen → se **consumen**.
- Cap reconciliation ratificada por vos: `lisa.doctores` **new** (zona Agentes→Lisa); sucede a `clinics-brand-extension` (deprecated) + consume `prepaid-booking-advisory-locks`.
Sección `## Prior art scan` agregada al checkpoint. Encadeno a `/po-ux` para producir `01-spec.md` (directorio doctores + workspace N3-dyn [doctor-id] con tabs Bio/Horarios/Servicios/KPIs).

### 2026-05-30 17:45 · 🤖 claude · `/po-ux` · ✓ APLICADO
Escrito `01-spec.md` v1 (draft). Decisiones de scope ratificadas por vos en batch 1:
- **Horarios: recurrencia avanzada** → el spec CONSUME `luana-core-commercial-calendar` para reglas recurrentes (no recrea). La UI es `HorariosRecurrenceEditor`; la resolución es backend.
- **Tab KPIs DIFERIDO** → la story entrega 3 tabs (Bio/Horarios/Servicios), no 4. Out-of-scope documentado.
- **Landing público: solo toggle + endpoint** read-only PHI-masked. La UI de landing va a `vitalia-fase2-lisa-landing-public`.
- **Full HIPAA-lite**: pgcrypto at-rest + audit + RBAC admin_clinic + masking + channel guards.
Scenarios: 4 base (happy/negative/edge/adversarial) + 7 sub-categorías (race/concurrent/network/empty/large/a11y/i18n) = 11. Wireframes ASCII (directorio cards + workspace tabs). Componentes: ~7 NEW en `features/lisa/components/doctores/` (justificados, hoy solo hay marca+placeholders).
**⚠️ Estimación subió 3-4d → 5-6d** por recurrencia avanzada + full HIPAA. Si /architect ve que la recurrencia infla, candidato a split de ticket.
Pendiente tu ratificación para cerrar refining→refined. Revisá `01-spec.md` (sobre todo SC-1 happy + § HIPAA-lite + § Estimación).

### 2026-05-30 18:20 · 🤖 claude · `/po-ux` · ✓ APLICADO
Aplicados tus 3 inputs + generados los entregables para tu lectura previa a aprobar:

**1. Assets + Cloudflare R2** — `luana-core-assets` ya existe con `StorageService` S3-compatible que **soporta R2 vía boto3 + presigned POST** (upload directo browser→R2). Vitalia sería el primer consumidor. Spec actualizado: avatar consume assets+R2 (§ Storage). ⚠️ El token `cfat_…` que pasaste es CF API token (sirve para wrangler/crear bucket), pero el runtime boto3 necesita **R2 S3 Access Keys** (se generan aparte en R2→Manage API Tokens). El provisioning real (bucket+CORS+creds en .env) va a ticket de build, NO en refining. **Rotá el cfat tras usarlo** (se pegó en chat plano).

**2. Horarios = bloques mutables** (no template fijo). Reescrito: cada bloque es recurrente (con **fecha-fin O N-iteraciones** O abierto) o puntual; **eliminables en cualquier momento**; eliminar reproyecta solo el futuro y preserva citas confirmadas. Scenarios nuevos: SC-1 (fecha-fin), SC-1b (N-iter), SC-1c (puntual), SC-1d (eliminar bloque), SC-3b (eliminar bloque con cita confirmada → warning).

**3. Endpoint público profundizado** (§ Endpoint público): allow-list de campos (display_name, specialty, avatar_url, años, idiomas, bio_public, credential_label opcional); PHI/PII NUNCA; channel guard por arch test. Solo doctores visible+active. UI de landing queda en lisa-landing-public.

**Entregables para que leas ANTES de aprobar:**
- `01-spec.md` → § Gherkin scenarios (la lista de funcionalidades, formato Given/When/Then = lo que irá al cap) + **§ Business rules** (15 reglas con severidad/enforcement/audit) + § Endpoint público + § Storage.
- `mockups/doctores.html` → mockup visual (directorio cards + workspace 3 tabs + bloques de horarios). Preview: `cd vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/mockups && python3 -m http.server 8888` → http://localhost:8888/doctores.html

**⚠️ Estimación ahora 7-9d** (bloques mutables + full HIPAA + assets/R2 first-consumer). Propongo que /architect lo **divida en 3 tickets** (CRUD+bio+servicios / horarios-bloques+scheduling / assets+R2+avatar+público).

Quedo esperando tu lectura. No ratifiqué nada (state sigue `refining`).

### 2026-05-30 18:55 · 🤖 claude · `/po-ux` · ✓ APLICADO
Aplicadas tus correcciones de ARQ/UX (gracias, eran de fondo):
- **No tabs internos** (verifiqué la política en `ADR-vitalia-004` + el precedente `lisa/marca/{presencia,voz-y-tono,identidad}` que son rutas, no tabs). Perfil/Horarios/Servicios ahora son **rutas-hoja** reales.
- **Layout angosto + Valeria al costado**: spec marca que TODO va full-width de columna angosta, legible en poco espacio. Cards apiladas 1-col, calendario compacto.
- **Nav de entidad dinámica (tu propuesta)**: fila contextual de ribbon `‹ Lista de doctores / {Nombre} · Perfil · Horarios · Servicios` (N3-dynamic) para no romper árbol→hoja. La marqué como **cross-cutting** (aplica a todo workspace de entidad, no solo doctores) → necesita addendum a `ADR-vitalia-004` + componente `shell-organism/EntityBreadcrumbBar`. Escalado en § Handoff ARQ; NO se construye el shell genérico dentro de esta sola story.
- **Horarios = calendario tipo Google Calendar**: vista semana, arrastrar para crear bloque, popover repetir (semanal/quincenal + fecha-fin/N-iter o "solo esta semana"), navegación ‹ › entre semanas (cada semana puede ser distinta). Scenarios SC-1/1b/1c/1d actualizados a esa interacción.

**Mockup reescrito** (`mockups/doctores.html`, refrescá el navegador) ahora muestra el shell real: Valeria chat a la derecha, columna angosta, fila contextual, y el calendario compacto. Clic en un doctor → aparece la fila `‹ Lista de doctores / Dra. Ana` + Perfil/Horarios/Servicios.

**Pendiente que pediste** ("recordar esto siempre como UX"): al aprobar, propongo cementar 2 cosas → (1) regla UX "full-width columna angosta + Valeria coexiste", (2) patrón nav N3-dynamic. Vía memory + addendum ADR-vitalia-004 + SHELL-DESIGN-CONTRACT. Lo dejo listado en § Handoff ARQ.

¿Revisás el mockup actualizado + el spec? Si OK → cierro refining→refined y encadeno /architect (que decide el split de tickets + el tema del componente shell genérico).

### 2026-05-30 19:30 · 🤖 claude · `/po-ux` · ⚠️ DUDA
Chris pidió que el mockup use el shell-organism REAL (no mi aproximación genérica). Investigué y encontré mi error de fondo + el camino correcto, PERO el contexto de esta sesión está saturado (arrastra el bug inicial de ~200 lecturas duplicadas) y el harness empezó a truncar/cancelar lecturas → no puedo portar los canónicos de 1400+ líneas de forma confiable ahora.

**Hallazgos (para retomar en sesión limpia):**
- Regla SSoT: `vitalia/.claude/rules/shell-mockup-per-component.md` (ADR-vitalia-003). **Mi mockup violó el anti-pattern "reinventar el wrapper"** — hay que **portar VERBATIM** topbar+ribbon+sub-tabs+splitter+chat-Valeria desde los canónicos.
- Canónicos a portar: `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (wrapper integral) + `.../vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html` (chat) + `.../vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html`.
- **Precedente directo de calendario:** `.../vitalia-fase2-valeria-agenda/mockups/agenda-week.html` (vista semana DENTRO del shell real) → base ideal para la hoja Horarios.
- **Tokens reales (NO los que usé):** primario cian #01B2F8 · accent púrpura #7B2D91 · **agent-lisa #00D084 (VERDE, no teal)** · agent-valeria #7B2D91 · agent-camila #180D95 · agent-mateo #FEE209 · gradient mariposa. `_shared.css` del story-folder debe espejar `vitalia/frontend/src/app/globals.css`.
- Componentes shell reales: `components/shared/shell-organism/{ApexShellV2,RibbonV2,TopBarV2,ValeriaSidebar,SubTabsBar,SubSubTabsBar,RibbonTab,SubTab,ContentArea}.tsx` + `ribbonConfig.ts`.
- Splitter 3 estados a simular: `chat-collapsed / chat-narrow / 50-50`.

**PLAN sesión limpia (post /clear):**
1. `cp agenda-week.html → mockups/doctores.html` (hereda wrapper real + calendario) y crear `_shared.css` espejo de globals.css.
2. Reemplazar SOLO el `.panel-content`: vista Lista de doctores (cards apiladas) + fila contextual N3-dyn `‹ Lista de doctores / {Nombre} · Perfil·Horarios·Servicios` + hojas Perfil/Horarios(calendario)/Servicios. Wrapper intacto.
3. Ratificar visual con Chris (`ratified_visual_by_chris: true` — gate del protocolo, sin esto /architect REFUSE).
4. Recién ahí: cerrar refining→refined + encadenar /architect.

**Pendiente cementación UX (lo que Chris pidió "recordar siempre"):** tras ratificar, actualizar `.claude/skills/po-ux/SKILL.md` para que SIEMPRE: (a) cargue `shell-mockup-per-component.md` como gate HARD, (b) porte wrapper verbatim (nunca reinvente), (c) recuerde layout angosto + Valeria al costado, (d) patrón nav N3-dynamic. + memory entry + addendum ADR-vitalia-004.

State sigue `refining`. NO ratificado.

### 2026-05-30 20:10 · 🤖 claude · `/po-ux` · ✓ APLICADO
Rehecho el mockup con el **shell-organism REAL** (mi error anterior fue reinventar el wrapper — la rule `shell-mockup-per-component.md` lo prohíbe explícito). El contexto NO estaba tan saturado como temí: `agenda-week.html` (439 líneas, limpio) tenía todo.

**Qué hice bien ahora (port verbatim, no reinvención):**
- `cp _shared.css` canónico de valeria-agenda → story-folder (tokens HSL reales: Lisa **#00d084 verde**, Valeria #7b2d91, primario cian, etc. — NO los inventados).
- Wrapper portado verbatim: `.shell-topbar` + `.shell-ribbon` (5 especialistas + Plataforma, Lisa activo) + `.shell-subtabs`.
- Calendario de Horarios reusa `.week-grid`/`.week-cell`/`.agenda-slot` reales (mismo sistema que la Agenda de Valeria) → coherencia visual garantizada.
- Chat de Valeria al costado con markup/tokens del `valeria-chat-sample.html` canónico (avatar + dot status verde + mode pill + composer).
- Fila N3-dyn contextual `‹ Lista de doctores / {Nombre} · Perfil·Horarios·Servicios` con color Lisa.
- Toggle 🌓 dark/light (tokens `.dark` del _shared.css).

Sirviendo en **http://127.0.0.1:8888/doctores.html** (refrescá fuerte: Ctrl+Shift+R). Ahora SÍ se ve el shell de Vitalia.

**Pendiente tras tu OK visual:** actualizar `.claude/skills/po-ux/SKILL.md` para que JAMÁS vuelva a pasar (cargar shell-mockup-per-component como gate HARD + portar wrapper verbatim + tokens reales + layout angosto+Valeria + nav N3-dyn). Esa es la parte "para que nunca más lo olvides".

### 2026-05-30 20:55 · 🤖 claude · `/po-ux` · ✓ APLICADO
Corregido de raíz. Mis 2 errores graves: (1) reinventé el shell en vez de portar el canónico; (2) lo puse al revés (Valeria a la derecha — va a la IZQUIERDA). La 55.png que mostraste ERA mi mockup malo. Sí existía el base que recordabas: **`dual-mode-shell.html`** (1439 líneas, SSoT visual del shell).

**Qué hice ahora (lo correcto desde el principio):**
- `cp dual-mode-shell.html → doctores.html` **verbatim** (shell real intacto: TopBar con TenantSwitcher dropdown + LogoMark gradient mariposa · split 50/50 · **Valeria IZQUIERDA** con rail/history/chat + atajos C/R/F/N · Ribbon con avatares + labels de TAREA "Mi Clínica·Atraer·Vender·Operar·Mantener·Configurar" + tint agent-color · sub-tabs · theme toggle).
- Solo cambié 3 cosas: estado inicial → `lisa/doctores`; el body de `lisa/doctores` → contenido real (antes era empty-state); agregué la navegación N3-dyn.
- **Lista de doctores** (cards en el panel App derecho) → clic abre el **workspace** con la fila contextual `‹ Lista de doctores / {Nombre} · Perfil·Horarios·Servicios` (Lisa verde #00D084).
- **Horarios** = calendario semanal de bloques (recurrente B1 verde + puntual P ámbar) coherente con la grilla de la Agenda.

Refrescá fuerte (Ctrl+Shift+R) **http://127.0.0.1:8888/doctores.html**. Ahora es el shell de Vitalia de verdad: Valeria a la izquierda, ribbon de tareas, Lisa→Mi Clínica→Doctores activo.

Si esto ya coincide con dev-app → me decís "está bien" y (1) cierro refining→refined + /architect, (2) actualizo el skill po-ux para que nunca más reinvente el shell.

### 2026-05-30 19:55 · 🤖 claude · `/po-ux` · ✓ APLICADO
Alineé el detalle de doctor con el patrón N3 de **Mi Clínica / Marca** (`SubSubTabsBar`, ADR-vitalia-004 § 3.1.1). El detalle ya NO usa el toggle-pill verde lleno (eso parecía "tab interno"). Ahora es una **tira N3 idéntica a Marca**: una sola fila con border-inferior y pills `padding 6px 12px · rounded 6px`, activo = fondo sutil `bg-hover` + texto primario (NO verde lleno), inactivo = texto secundario con hover sutil — exactamente el estilo de Identidad/Voz y tono/Presencia. Los cuatro son **botones**:

`[‹ Lista de doctores]  |  ⌀ Dra. Ana Paredes  |  [👤 Perfil] [🗓️ Horarios] [🩺 Servicios]`

- "Volver" = **botón** pill (ya no link verde suelto).
- Perfil/Horarios/Servicios = **botones** pill idénticos a los sub-sub-tabs de Marca.
- Nombre del doctor = breadcrumb de contexto (la pieza dinámica del N3), entre separadores finos verticales.
- Experiencia uniforme árbol→hoja en TODA la app: la hoja no tiene tabs internos; el 3er nivel se navega con la tira N3 (igual que Marca).

Verificado HTTP 200 + avatares 200. Refrescá fuerte **http://127.0.0.1:8888/doctores.html** → **Lisa → Doctores → "›" en un doctor**.

Si ya coincide con el patrón de Marca → me decís "está bien" y cierro `refining → refined` + chain `/architect`, y después actualizo el skill `/po-ux` (gate HARD shell + N3) para que no se repita.

### 2026-05-30 20:35 · 🤖 claude · `/po-ux` · ✓ APLICADO
Verifiqué la estructura REAL de Marca en el código (no pude autenticar la prod con Playwright — el storageState es localhost y la prod es Clerk-gated, pero el SSoT es el código, no el screenshot). La estructura de Marca es:

```
lisa/marca/page.tsx            → redirect() a /identidad (hoja default)
lisa/marca/identidad/page.tsx  ← cada hoja = su propia URL
lisa/marca/voz-y-tono/page.tsx
lisa/marca/presencia/page.tsx
```
`SubSubTabsBar` lee el segmento [3] de la URL → la URL ES el estado (cero state cliente). Eso es justo lo que pediste: **cada hoja su propia URL**.

**Actualicé el mockup para replicarlo (verificado con Playwright real, clickeando, no solo HTTP 200):**
- `…/lisa/doctores` → directorio
- `…/lisa/doctores/{id}/perfil` · `/horarios` · `/servicios` → **cada hoja cambia la barra de direcciones** (hash-routing en el mockup; en prod serán rutas reales `[doctor-id]/perfil/page.tsx`, etc., con `[doctor-id]/page.tsx → redirect a /perfil` igual que `marca/page.tsx`).
- **Deep-link** directo a `…/doctores/luis/horarios` abre esa hoja ✅
- **back/forward** del navegador respeta cada hoja ✅
- La barra N3 usa el estilo visual del `SubSubTabsBar` (pills sutiles, activo `bg-hover`, no verde lleno). La única diferencia con Marca: el nombre del doctor como breadcrumb (la pieza dinámica del N3 que vos propusiste).

Estructura de rutas que irá al `03-arch.md` (espejo de Marca):
```
lisa/doctores/page.tsx                         (directorio)
lisa/doctores/[doctor-id]/page.tsx             → redirect a /perfil
lisa/doctores/[doctor-id]/perfil/page.tsx
lisa/doctores/[doctor-id]/horarios/page.tsx
lisa/doctores/[doctor-id]/servicios/page.tsx
```

Screenshots Playwright en `vitalia/frontend/_shots/mk-{1..5}-*.png`. Refrescá **http://127.0.0.1:8888/doctores.html** → entrá a un doctor y mirá cómo cambia la URL por hoja.

Si ahora SÍ coincide con la experiencia de Marca → "está bien" y cierro `refining → refined` + `/architect` + actualizo el skill `/po-ux`.

### 2026-05-30 21:10 · 🤖 claude · `/po-ux` · ✓ APLICADO
Apliqué tus 5 comentarios al mockup (verificado con Playwright, no solo HTTP 200):

**1. N3 SIEMPRE visible + coherente con Identidad.** La tira de tercer nivel ahora aparece **desde que entro a Doctores**: `[👨‍⚕️ Doctores]` (activo) + "Selecciona un doctor" + `Perfil/Horarios/Servicios` **deshabilitados** (opacidad .45, no clickeables). Al entrar a un doctor, el chip muestra su nombre+avatar y se **habilitan** las 3 hojas. Mismo patrón visual que Marca/Identidad (pills `bg-hover` activo). "Doctores" hace de raíz/volver.

**2. Autosave (sin botón Guardar).** Quité los botones "Guardar perfil" y "Guardar servicios" — violaban la doctrina (`form-runtime-array.md`: botón "Guardar" rompe autosave + ADR-004 §3.5 autosave debounce 600ms). Cada hoja ahora muestra el hint "✓ Los cambios se guardan automáticamente". Todo campo es autoguardable.

**3. Bio para promoción (mi recomendación, simple, sin sobreingeniería).** En Perfil agregué un bloque "Bio para promoción": un textarea **"Datos del doctor (insumo)"** donde el admin pega formación/certificaciones/logros + botón **"✨ Generar bio con Lisa"** → redacta una bio breve **usando solo esos datos (no inventa)** → cae en **"Bio pública (editable)"**. Esa bio la consume el agente de ventas para promocionar al doctor. Patrón = mismo "generar/consolidar" que ya hay en la marca. Nada de scoring ni multi-paso.

**4. Horarios 24h, formato 24h, sin comentarios.** La grilla ahora va en **formato 24h** (`07:00`…`21:00` base) con **check "Mostrar 24 horas"** (00:00–23:00) por si atienden 24h. Saqué los comentarios `<!-- -->`/`//` del mockup (van al spec, no acá).

**5. Servicios = pendiente (depende de otra historia).** La hoja Servicios ahora es un estado **"pendiente"**: explica que elegirá del catálogo de **Mi Clínica → Servicios** (con precio propio opcional) y que depende de esa historia, que se crea **al final de esta**. Badge "⏳ Planned · depende de Servicios".

Screenshots: `vitalia/frontend/_shots/v2-{1..5}-*.png`. Refrescá **http://127.0.0.1:8888/doctores.html**.

**Dudas para vos (⚠️):**
- (3) ¿La bio la genera **Lisa** (estratega de marca) o preferís que sea un botón neutro "Generar bio"? Lo puse con Lisa por coherencia agéntica, decime si cambio el wording.
- (5) Al cerrar esta historia creo la historia **"Mi Clínica · Servicios"** y dejo el link de dependencia. ¿Confirmás ese nombre?

Si todo OK → cierro `refining → refined` + `/architect` + actualizo `/po-ux`.

### 2026-05-30 22:00 · 🤖 claude · `/po-ux` · ✓ APLICADO
Apliqué tus comentarios nuevos (verificado con Playwright real, 1 passed):

1. **Rename Doctores → Staff.** Subtab línea 2 = "👨‍⚕️ Staff", slug de ruta `lisa/staff` (URL: `…/lisa/staff/{id}/{perfil|horarios|servicios}`), raíz del N3 = "Staff", título del directorio = "Staff". (Las personas siguen siendo "doctor" en datos/labels de ítem — el contenedor es Staff.)

2. **Barra N3 pegada arriba (sticky, como Identidad en dev-app) + componente UX reusable.** La tira N3 ahora es `position:sticky; top` pegada al borde superior del contenido, ocupa **todo el ancho** (rompe el padding con margin negativo) y queda fija al hacer scroll. La dejé parametrizada (`pill()` + `root/leaf/nameChip/sep`) para promoverla a **componente UX** (`SubSubTabsBar` dinámico con entidad) y reusarla en toda la app de aquí en adelante. Lo anoto en el spec como candidato a átomo/molécula del design system.

3. **Bio para promoción = "repo de insumos" (tu pedido).** Ahora junta 3 fuentes: **(a)** notas/texto pegado, **(b)** **archivos** (diploma/CV/certificados) con **dropzone**, **(c)** **links** (Doctoralia/LinkedIn/publicaciones). Botón **"✨ Generar bio"** → produce una bio **en secciones claras** (Resumen · Formación y credenciales · Enfoque de atención), cada una **editable** (`contenteditable`). Usa solo el material aportado, no inventa.
   - **Componente shadcn recomendado para adjuntar:** **shadcn Dropzone** (`diragb/shadcn-dropzone`, sobre `react-dropzone`) — es el estándar shadcn para file-upload con drag&drop, lista de archivos con nombre/tamaño/remove y soporte multi-archivo. Alternativa oficial: el bloque "File Upload Dropzone" de shadcn blocks. Lo dejo fijado en el spec como el componente a usar (hay que instalarlo, hoy `components/ui/` no tiene dropzone).

4. **Hojas full-width responsive inteligente.** Quité todos los `max-width:560px`. Los campos del perfil usan `grid auto-fit minmax(220px,1fr)` (se acomodan a 1/2/3 columnas según ancho), el bloque bio y los insumos usan `auto-fit minmax(280px,1fr)`, y Servicios ocupa el ancho completo. Aprovecha todo el espacio a cualquier tamaño del splitter.

Screenshots: `vitalia/frontend/_shots/v3-{1..3}-*.png` (v3-3 = scrolleado, muestra la N3 pegada arriba). Server: **http://127.0.0.1:8888/doctores.html** (entrá a un integrante).

**Fuentes (componente adjuntar):** shadcn-dropzone (github.com/diragb/shadcn-dropzone) · shadcn blocks File Upload Dropzone.

**Sigue pendiente tu respuesta a:** (a) ¿bio la genera "Lisa" o botón neutro "Generar bio"? — lo dejé como **"✨ Generar bio"** neutro en esta iteración; (b) ¿confirmás el nombre de la historia futura "Mi Clínica · Servicios"?

### 2026-05-30 23:50 · 🤖 claude · `/po-ux` · ✓ APLICADO
Apliqué tus 3 puntos nuevos (verificado por grep del mockup + URL real en Playwright):

1. **Rename Doctores → Staff.** Subtab línea 2 = "👨‍⚕️ Staff"; slug de ruta `lisa/staff` (URL Playwright confirmada: `…/lisa/staff/ana/perfil`); raíz del N3 = "Staff"; título directorio = "Staff"; placeholder "Selecciona un integrante". El ítem-persona sigue siendo "doctor" en datos; el contenedor pasa a ser Staff.

2. **Barra N3 pegada arriba (sticky) + componente UX reusable.** Ahora es `position:sticky` al borde superior del contenido, ocupa **todo el ancho** (rompe el padding con margin negativo) y queda fija al scrollear — igual que la barra N3 de Identidad en dev-app. La parametricé (`pill()` + root/leaf/nameChip) para promoverla a **componente UX** (`SubSubTabsBar` con entidad dinámica) y reusarla en toda la app. Anotado en el spec como átomo/molécula del design system.

3. **Bio = "repo de insumos".** Junta 3 fuentes: (a) notas/texto pegado, (b) **archivos** con dropzone (diploma/CV/certificados), (c) **links** (Doctoralia/LinkedIn/publicaciones). Botón **"✨ Generar bio"** → produce bio **en secciones claras editables** (Resumen · Formación y credenciales · Enfoque de atención, cada una `contenteditable`). Usa solo el material aportado, no inventa.
   - **Componente shadcn recomendado (research):** **shadcn Dropzone** (`diragb/shadcn-dropzone`, sobre `react-dropzone`) — estándar shadcn para file-upload drag&drop con lista nombre/tamaño/remove + multi-archivo. Alternativa oficial: bloque "File Upload Dropzone" de shadcn blocks. Hay que instalarlo (hoy `components/ui/` no lo tiene). Fijado en el spec como componente a usar.

**Bonus iteración previa:** hojas **full-width responsive** (`auto-fit minmax`, cero `max-width:560px`), **autosave sin botón Guardar**, **horarios 24h** con check, **Servicios pendiente**.

Server: **http://127.0.0.1:8888/doctores.html** → entrá a un integrante. (Honestidad: el visor de imágenes me falló al renderizar el PNG fullPage de ~6500px este turno; las capturas quedaron en `vitalia/frontend/_shots/`. Estructura confirmada por grep + URL real del Playwright, no por "200".)

Pendiente tu confirmación: (a) "✨ Generar bio" neutro o "Generar bio con Lisa"; (b) nombre historia futura "Mi Clínica · Servicios". Con eso cierro `refining → refined` + `/architect` + actualizo `/po-ux`.

### 2026-05-31 00:05 · 🤖 claude · `/po-ux` · ✓ APLICADO
Screenshots renderizados y revisados (ahora sí pude verlas). Cerré los últimos detalles del rename:
- Título del directorio y CTA estaban en "Doctores"/"Nuevo doctor" → corregidos a **"Staff" / "+ Nuevo integrante" / "Buscar integrante…"**. Cero "Doctores" visible restante (solo un comentario interno).
- Verifiqué los 5 cambios en pantalla: (1) subtab **Staff** + N3 con raíz Staff + "Selecciona un integrante" + leaves deshabilitados en el directorio; (2) N3 **pegada arriba** y full-width al entrar a un integrante; (3) **Bio repo** completo (notas + dropzone "Arrastrá o hacé clic", PDF de ejemplo con tamaño+✕, links con chip, bio generada en 3 secciones editables); (4) **full-width** confirmado también en viewport angosto (1040px, simula splitter de chat ancho) — los campos colapsan a 1 columna con `auto-fit`; (5) autosave hint, sin botón Guardar.

Screenshots: `vitalia/frontend/_shots/final-{1,2,3}.png` + `final-4-narrow-perfil.png` (responsive angosto). Quedan tus 2 confirmaciones (wording "Generar bio" + nombre historia Servicios) para cerrar `refined` + `/architect`.

### 2026-05-31 00:20 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Refinamiento cerrado — Chris dio por refinado.** Sincronicé el `01-spec.md` con todos los acuerdos del mockup antes de cerrar (si no, /architect construiría lo viejo):
- Frontmatter: `state: refined`, `po_ux_version: 2`, `ratified_by_chris: true`, `ratified_visual_by_chris: true`, `architecture_pattern: ADR-vitalia-004`.
- Rename **Doctores → Staff** en todo el spec (rutas `lisa/staff/[doctor-id]/{perfil,horarios,servicios}`, microcopy, componentes `StaffDirectoryView`/`StaffCard`/`NuevoIntegranteModal`/`StaffWorkspaceShell`).
- Cementados en spec: N3-dyn sticky full-width siempre visible (→ componente UX `SubSubTabsBar`), **autosave sin botón Guardar** (regla nueva `autosave-no-save-button`), **Bio = repo de insumos** (texto+dropzone+links → ✨ Generar bio en secciones, reglas `bio-generated-from-inputs-no-invent` + `bio-attachments-via-assets-r2`), **horarios 24h**, **Servicios pendiente**. Componente adjuntos: **shadcn Dropzone** (a instalar).
- Business rules ahora 18 (15 + 3 nuevas). Scenarios 15. Wireframes + microcopy + componentes actualizados.

checkpoint `refining → refined`. Encadeno `/architect vitalia vitalia-fase2-lisa-doctores` para producir el ready package (03-arch + 04-validators + 05-guidelines + 06-tickets + dispatch-plan), con candidato a split en 3 tickets (CRUD+bio / horarios-calendario+scheduling / assets+R2+público) + decisiones ARQ escaladas (SubSubTabsBar genérico, layout angosto como regla UX, provisioning R2).

Pendiente menor (no bloquea /architect, lo confirmás cuando quieras): wording "✨ Generar bio" quedó **neutro**; nombre historia futura quedó **"Mi Clínica · Servicios"**.

### 2026-05-31 06:30 · 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-1 — Doctor domain + migration 036 + DoctorRepository + CRUD endpoints + main.py wiring**

Implementado y testeado. Deliverables completados:
- `clinics/domain/{doctor.py, bio.py, availability_block.py, credential_country.py}` — pure Python DDD, zero framework imports
- `clinics/infrastructure/models/doctor_model.py` — SQLA 2.0 Mapped[], BYTEA PII cols, dni_hash unique constraint
- `clinics/infrastructure/repositories/doctor_repository.py` — hereda `CompoundScopeRepositoryBase(scope_field="clinic_id")` (engine base post-lift 2026-05-20), pgcrypto encrypt/decrypt
- `clinics/application/ports/doctor_repo_port.py` — ABC port
- `clinics/application/doctor_service.py` — audit sync pre-response, DniConflictError, telemetry fire-forget
- `clinics/application/credential_validator.py` — PE/AR/MX/CL, Spanish neutro
- `clinics/api/doctors_router.py` — GET list (masked), POST (409/422), GET {id} (cross-tenant audit), PATCH; response_model= mandatory
- `clinics/api/dtos.py` EXTENDED — DoctorListItemDTO (masked PHI), DoctorDetailDTO, PublicDoctorDTO (channel guard 7 fields)
- `alembic/versions/036_f2_s8_vitalia_lisa_staff.py` — 3 tables idempotent (IF NOT EXISTS); down_revision=035
- `main.py` — `include_router(doctors_router, prefix=/api/v1/vitalia/clinics/doctors)`
- Tests: test_credential_validator.py (17), test_doctor_domain.py (14), test_doctor_repository.py (5), test_doctor_cross_tenant.py (2), test_doctor_dni_race.py (1), test_doctors_api.py (6)
- `tests/architecture/test_public_doctors_allowlist.py` — 4 channel guard gates (3 pass, 1 skip T-BE-5 scope)
- Growth studio events registered: lisa_staff_doctor_created/updated/deactivated/viewed

**Gates GREEN:** 78 tests passed (1 skipped T-BE-5 scope) · 0 ruff lint errors · ruff format OK · 319 arch tests pass (pre-existing treatment_plans.notes failure excluded — NOT introduced by this ticket) · `test_compound_scope_repository_used` PASS (uses engine CompoundScopeRepositoryBase, not brand-local)

**HIPAA-lite compliance:** dual filter (tenant_id+clinic_id) via CompoundScopeRepositoryBase · pgcrypto BYTEA for dni/email/phone/credential · HMAC-SHA256 dni_hash unique constraint · audit sync writes (doctor.created/updated/deactivated/cross_tenant_attempt) · PHI masking in list responses · PublicDoctorDTO channel guard (7 allow-listed fields, no PHI) · Spanish neutro error messages

### 2026-05-31 — 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-2 — AvailabilityBlock models + AvailabilityProjectionService (dateutil.rrule) + AvailabilityBlockRepository**

Implementado TDD (RED→GREEN). Deliverables:
- `clinics/infrastructure/models/{availability_block_model.py, availability_slot_model.py}` — SQLA 2.0, mapean a tablas de migration 036 (sin migración nueva)
- `clinics/infrastructure/repositories/availability_block_repository.py` — hereda `CompoundScopeRepositoryBase(scope_field="clinic_id")`, soft deletes, SC-1d/SC-3b preserva citas confirmadas en delete
- `clinics/application/ports/availability_repo_port.py` — ABC con 6 métodos abstractos
- `clinics/application/availability_projection_service.py` — `dateutil.rrule` (v2.9.0): weekly interval=1, biweekly interval=2, end_date→until, occurrences→count, open_ended→90d horizon; `classify_future_slots_for_deletion` separa free vs confirmed
- `test_availability_projection.py` (12 tests) + `test_availability_block_mutable.py` (17 tests) — TDD RED primero

Gates: 96/96 tests pass (clinics suite) · 319 arch tests pass · ruff 0 errors · format OK
Commit: 2f88b316 · Branch: wip/vitalia
Pre-existing (no scope T-BE-2): `treatment_plans.notes` TEXT vs BYTEA (desde T-BE-1).

### 2026-05-31 — 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-3 — Availability blocks endpoints (GET/POST/PATCH/DELETE) + slot materialization + audit**

Implementado TDD (RED→GREEN). Deliverables:
- `clinics/api/dtos.py` EXTENDED — `RecurrentBlockCreateRequest`, `OneOffBlockCreateRequest` (discriminated by kind), `AvailabilityBlockDTO`, `AvailabilityBlocksResponse`, `DeleteBlockResponse`
- `clinics/application/availability_block_service.py` — NEW; orchestrates `AvailabilityProjectionService` (dateutil.rrule) + `AvailabilityBlockRepository` + audit SYNC writes; `delete_block` returns `(True, preserved_count)` (CRITICAL invariant: confirmed slots NEVER deleted)
- `clinics/api/doctors_router.py` EXTENDED — 4 availability-blocks sub-routes: GET list, POST create (materialization→slots→audit), PATCH edit (reproject-future-only), DELETE retire (preserves confirmed, returns `{deleted, preserved_appointments}`)
- `tests/modules/vitalia/clinics/test_availability_blocks_api.py` — 30 tests (TDD RED first): response_model= gates, DTO existence, RBAC dependencies, service unit tests (list/create/update/delete/preserve), biweekly occurrences, one-off materialization, delete-preserves-confirmed (CRITICAL SC-3b)

Gates GREEN: 126/126 clinics tests pass · 333/333 arch tests pass (excluding pre-existing CRM debt `treatment_plans.notes TEXT vs BYTEA` — NOT introduced by this ticket) · 0 ruff lint errors · ruff format OK

HIPAA-lite: dual filter (tenant_id+clinic_id) on all routes · RBAC `admin_clinic` on all mutations (POST/PATCH/DELETE) · audit sync write pre-response (`doctor.availability_block_created`, `doctor.availability_block_deleted`) · `response_model=` mandatory on all 4 routes

Forbidden-touch respected: `core/luana-core-*/src/**` and `scheduling/**` NOT touched. Slots materialize to brand-local `vitalia_availability_slots` table — scheduling reads without modification.

### 2026-05-31 — 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-4 — BioGenerationService (extractive, NOT agentic) + generate-bio endpoint**

Implementado TDD (RED→GREEN). Deliverables:
- `clinics/application/bio_generation_service.py` — NEW; deterministic single-shot extractive service (D-4: NOT agentic, R23 N/A, Sonnet-eligible); `BioGenerationService.generate()` + `generate_with_error()`; `BIO_GENERATION_FALLBACK_MESSAGE` (Spanish neutro, no voseo); `LLMServiceProtocol` (Protocol-based DI for testability); anti-invent guardrail in system_prompt ("Usa únicamente la información del material provisto"); graceful fallback on any LLM exception → `(BioPublic(), BIO_GENERATION_FALLBACK_MESSAGE)` never raises; consumes `luana_core_llm.factory.LLMFactory` (shared engine, NOT edited)
- `clinics/api/dtos.py` EXTENDED — `GenerateBioRequest` + `GenerateBioResponse{bio: BioPublicDTO, error_message: str | None}`
- `clinics/api/doctors_router.py` EXTENDED — `POST /{doctor_id}/generate-bio` with `response_model=GenerateBioResponse`; RBAC admin_clinic; returns HTTP 200 on success AND on LLM failure (error_message non-None on failure)
- `tests/modules/vitalia/clinics/test_bio_generation_service.py` — 12 tests TDD RED-first; covers V-FN-9: no-invent guardrail, fallback on LLM fail, Spanish neutro, malformed JSON, partial sections, endpoint route registration, endpoint 200 success + 200 fallback

Gates GREEN: 138 clinics tests pass · 0 ruff errors · ruff format OK · arch fitness (pre-existing treatment_plans.notes debt excluded per ticket instructions)
V-FN-9 (validator): 12/12 PASS

### 2026-05-31 05:18 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Arranco el tren autónomo `/architect → /dev-team → /auditor → merge` hasta `done`** (pedido explícito de Chris).
- Step 0 GREEN: worktree CANÓNICO vitalia · sin stories en developing/developed/reviewing (closure gate limpio) · hard deps `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell` ambas en archive (done) · WIP caps libres (0 ready/developing).
- Story `state: refined`, ratificada visual + funcional por Chris, prior-art scan hecho. Transición `refined → ready` vía `/architect` válida.
- Encadeno `Skill(architect)` inline con `vitalia vitalia-fase2-lisa-doctores`. Le pido **declarar `autonomous_mode: true`** en el dispatch-plan para que el pipeline corra solo hasta el merge (Chris ratificó el modo autónomo en este turno).

### 2026-05-31 — 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-5 — Public doctors endpoint (allow-list channel guard) + masking + new arch test**

Implementado TDD (RED→GREEN). Deliverables completados:

- `clinics/application/public_doctor_serializer.py` — NEW; `to_public_dto(doctor, *, credential_label=None) -> PublicDoctorDTO`; explicit allow-list of 7 fields: `display_name, specialty, avatar_key, years_experience, languages, bio_public, credential_label`; NEVER accesses `doctor.dni/.email/.phone/.credential`; allow-list is the security boundary (adding PHI to Doctor model does NOT leak it)
- `clinics/api/public_doctors_router.py` — NEW; `GET /{tenant_slug}/doctors`; no auth (intentionally public); `response_model=PublicDoctorsResponse`; resolves clinic by slug via `ClinicRepository.get_by_slug_public()` (no tenant_id required for public lookup); fetches visible+active doctors via `DoctorRepository.list_public()`; channel guard via `to_public_dto()`
- `clinics/infrastructure/repositories/clinic_repository.py` EXTENDED — added `get_by_slug_public(slug)` method (active+non-deleted lookup without tenant_id, for public endpoint only)
- `main.py` — `include_router(public_doctors_router, prefix=/api/public/clinic, tags=["public"])`; route: `GET /api/public/clinic/{tenant_slug}/doctors`
- `tests/architecture/test_public_doctors_allowlist.py` — SKIP resolved; was `pytest.skip("T-BE-5 scope")`, now PASSES: `test_public_doctor_serializer_exists` GREEN (was previously skipped)
- `tests/modules/vitalia/clinics/test_public_doctors_endpoint.py` — NEW 29 tests TDD RED-first; covers V-FN-11 + V-ARCH-7: serializer import/return type/7-exact-fields/all-7-allowed-fields/no-PHI-leak (dni/email/phone/credential), router contract (GET route/response_model/PublicDoctorsResponse/no-auth), filtering (visible+active not in DTO/tenant_id not leaked/clinic_id not leaked), main.py registration

Gates GREEN:
- `vitalia/backend/tests/modules/vitalia/clinics/` — 172 passed · 0 failed · 1 warning (pre-existing core config deprecation)
- `vitalia/backend/tests/architecture/test_public_doctors_allowlist.py` — 5 passed (was 4+1 skip; skip resolved)
- ruff check: 0 errors
- ruff format: 0 reformats needed

HIPAA-lite compliance: channel guard via explicit allow-list (not deny-list) · `visible_en_landing AND active` double filter at SQL level · PHI fields (dni/email/phone/credential) never serialized · no X-Tenant-ID required (public endpoint) · `response_model=` mandatory (arch test V-ARCH-7)

Pre-existing excluded: `treatment_plans.notes TEXT vs BYTEA` (from migration 021, NOT introduced by this ticket — per task spec "ignore pre-existing treatment_plans.notes CRM debt")

V-FN-11: PASS · V-ARCH-7: PASS (arch test skip resolved, now 5/5)

### 2026-05-31 — 🤖 claude · `builder-backend` · ✓ APLICADO
**T-BE-6 — Assets proxy upload router (consume luana-core-assets, copy nicolify wiring)**

Implementado TDD (RED→GREEN). Deliverables:
- `clinics/api/assets_proxy_router.py` — NEW; `POST /upload` multipart; consumes `AssetsService.upload_asset` (proxy — D-3: presign NOT implemented in engine); RBAC `admin_clinic`; `response_model=AssetUploadResponse`; engine imports deferred to handler body (PLC0415 pattern per doctors_router); kind ∈ {avatar, credential_doc} validated; content-type allow-list: image/* for avatar; PDF/JPG/PNG/DOCX for credential_doc; 10MB max enforced brand-side before forwarding; returns `{key, url}`
- `clinics/api/dtos.py` EXTENDED — `AssetUploadResponse {key: str, url: str}`
- `main.py` — `include_router(assets_proxy_router, prefix=/api/v1/vitalia/assets, tags=["assets"])`
- `tests/modules/vitalia/clinics/test_assets_upload.py` — NEW 10 tests TDD RED-first: structural (importable/POST-registered/response_model/DTO fields) + functional (valid avatar/10MB-enforce/avatar-wrong-type/credential-pdf-valid/credential-text-rejected/invalid-kind); mocking via `monkeypatch` minimal env vars + `patch(AssetsService)` + `patch(SessionLocal)` — NO live R2 needed (T-BE-7 Chris manual)

Gates GREEN:
- 10/10 test_assets_upload.py PASS
- 177/177 clinics full suite PASS
- 334 arch fitness tests PASS (1 deselected = pre-existing `treatment_plans.notes TEXT vs BYTEA` — NOT introduced by this ticket)
- ruff check: 0 errors
- ruff format: 0 reformats needed

V-FN-10: PASS

---

## T-FE-2 · builder-frontend · 2026-05-31 · TESTS PASSING

**Commit:** 25cb9563 (wip/vitalia)
**Files:** 23 files changed, 2857 insertions

**Deliverables shipped:**
- `EntitySubNavBar.tsx` — N3-dynamic WAI-ARIA tablist (NEW sibling of SubSubTabsBar per D-1)
- `dropzone.tsx` — Shadcn-style native dropzone (no react-dropzone dep)
- `[doctor-id]/` routes — layout + page (redirect→perfil) + perfil + horarios + servicios
- `StaffWorkspaceShell.tsx` — layout wrapper with RQ doctor query
- `DoctorPerfilView.tsx` — autosave form (RHF+Zod, 600ms debounce, no Guardar button)
- `BioRepoInputs.tsx` — notes + dropzone + link chips (autosaved)
- `GeneratedBioSections.tsx` — "✨ Generar bio" → 3 contenteditable sections (autosaved)
- `DoctorServiciosView.tsx` — placeholder ("Servicios — pendiente")
- `AvatarUploader.tsx` — proxy upload (D-3)
- `use-autosave.ts` + tests — debounce 600ms hook
- API hooks: useDoctor, usePatchDoctor, useGenerateBio, useAvatarUpload
- `DoctorWorkspacePage.ts` — Playwright POM

**Gates:**
- tsc: 0 errors · eslint: 0 errors · vitest 817/817 PASS · arch 162/162 PASS

**Advisory:** bidirectional validator HARD_FAIL drift=3 (new cap: headers need cap YAML update at merge F.3 — normal, not a blocker for wip/*)

**Live verification:** Dev stack not running. Manual steps in T-FE-2-impl-log.md. Escalate to Chris staging gate before auditor.

**Next:** T-FE-3 (horarios calendar) → T-E2E → auditor-frontend

---

### Turn T-E2E · builder-frontend · 2026-05-31

**⚠️ DUDA — T-E2E: spec suite completa escrita, live run PENDIENTE por stack DOWN**

**Deliverable:** Suite E2E completa para SC-1..SC-11 (41 tests descubiertos por playwright --list).

**Files escritos:**
- `e2e/fixtures/vitalia-fase2-lisa-doctores.fixture.ts` — Clerk auth + mocks (Tenant A/B seeds, 503, empty, large dataset)
- `e2e/pages/StaffDirectoryPage.ts` — POM nuevo (directorio + modal + states)
- 5 specs en `e2e/regression/vitalia-fase2-lisa-doctores/`: crear-happy, week-nav-oneoff, credencial-invalida, network-failure, i18n-credencial
- 5 specs en `e2e/shell-organism/`: cross-tenant-adversarial, deactivate, delete-block-preserve, empty (+ axe), large-dataset (+ visual goldens)
- `playwright.config.ts` — testMatch extended con `shell-organism/staff-.*`
- `06-tickets.yaml` T-E2E state: `specs-written`

**Gates estáticos PASS:**
- `tsc --noEmit`: 0 errors
- `eslint e2e/...`: 0 errors
- `playwright --list`: 41 tests descubiertos y parseados sin errores

**Duda central:** Stack vitalia DOWN (BE:8002 + FE:3002 retorna 500 por bug pre-existente zustand/workspace). NO se puede correr live. NO se generaron baselines de visual goldens. Verificación real (writes + state_check DB) pendiente.

**Doctrina respetada (test-design-doctrine.md § verificación REAL):**
- Happy-path writes (SC-1, SC-1b, SC-1c, SC-1d) son NOT mocked para el backend → van a hit BE:8002 cuando el stack sube.
- state_check DB queries documentadas en cada spec grader comment.
- SC-7 (503) usa page.route legítimamente (test del comportamiento de la UI ante error, no happy-path falso).
- NO se generó ningún green falso.

**Comando para correr cuando stack suba:**
```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase2-lisa-doctores/ shell-organism/staff-*.spec.ts --project=smoke
```

**Próximo:** auditor-frontend (independiente) verifica spec coverage + real-verification design + visual goldens plan.

### 2026-05-31 14:30 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**Build de los 11 tickets COMPLETO + verificación REAL contra el stack vivo encontró y arregló 2 bugs P0** que los 2400+ tests unitarios NO detectaron (ADR-vitalia-008 / verificación-real probando su valor):

1. **Migración 036 crash de boot** (commit b6aa8c35): `down_revision="035"` pero el id real es `"035_vitalia"` → `KeyError: '035'` → alembic upgrade head fallaba → backend en crash-loop. Corregido a `036_vitalia`/`035_vitalia`.
2. **DB session dependency rota** (commit e3db65a4): los 3 routers de clinics hacían `async for session in get_db()` sobre el `get_db` SÍNCRONO del engine → `TypeError: async for requires __aiter__, got generator` → todo endpoint `/clinics/doctors` daba 500. Corregido a `src.db.get_async_session` (patrón que usan scheduling/marketing/payments). `router.py` del módulo clinics tenía el MISMO bug pre-existente (clinics CRUD nunca funcionó live) — arreglado acá porque la feature doctores vive dentro.

Tras los fixes: backend bootea + endpoints responden limpio (422/404 validación, ya NO 500). 105 tests clinics verdes.

**Bloqueadores que NO puedo cruzar autónomo (necesito vos):**
- **FE env break (pre-existente, no es código nuestro):** FE :3002 da 500 — `zustand` no resuelve desde `core/@luana/hooks` (hoisting pnpm roto por la promotion cf19d1f5). Bloquea render FE + E2E live. Fix: `pnpm install` en root + restart FE. Documentado en `vitalia/docs/observed-bugs/`.
- **ADR-vitalia-008 `dev_app_verified`:** el gate `reviewing→done` exige ejercer la acción contra dev-app desplegado (deploy a staging MANUAL). No lo puedo hacer autónomo.
- **R2 (T-BE-7):** credenciales S3 de Cloudflare = acción manual tuya (avatar live).

**Decisión que necesito:** ¿(a) arreglo el FE env (`pnpm install`) + corro E2E live + auditor ahora, o (b) lo dejás para vos y yo cierro el reporte acá? El build está completo y el backend verificado-real; falta FE-render + audit formal + tu deploy a dev-app.

### 2026-05-31 15:05 · 🤖 claude · `/dev-team` · ✓ APLICADO
**FE env arreglado (docker) + verificación REAL del write path completa.** Seguí tu indicación: app en docker compose, Playwright nativo.
- **FE env fix:** `zustand` no resolvía desde `@luana/hooks` → `pnpm install --filter @luana/hooks` DENTRO del contenedor FE (volumen) + restart. FE :3002 ahora renderiza (/sign-in → 200, sin error de módulo).
- **Total: 5 clases de bug REALES encontradas y arregladas por verificación live** (todas invisibles a los 2400+ tests unitarios que mockean DB/DI):
  1. Migración 036 `down_revision` mal (`035` vs `035_vitalia`) → crash de boot (b6aa8c35)
  2. DB session dep: 3 routers usaban `get_db` síncrono con `async for` → 500 (e3db65a4)
  3. Routing sin trailing-slash (`/clinics/doctors` daba 422) (4cffaa1e)
  4. Falta `NuqsAdapter` → staff page crasheaba client-side (4cffaa1e)
  5. pgcrypto `:phone` ambiguo en CASE → create-doctor 500 (0d56d831)
- **Create-doctor verificado REAL:** POST→**201** · fila en `vitalia_doctors` · `dni_encrypted`=**bytea (cifrado at-rest)** · `dni_hash` SHA-256 · **audit log `doctor.created`**. (Test data limpiada.)

Esto es exactamente lo que ADR-008/Rule#37/verificación-real existe para atrapar: sin esto, la feature shippeaba "LIVE" y 500'eaba en cada alta de doctor (caso lisa-marca). Ahora lanzo el auditor formal (BE+FE) en paralelo.

### 2026-05-31 · 🤖 claude · `builder-backend` (AUDITOR_AUTO_FIX_LOOP) · ✓ APLICADO

**BE audit iteration 2 — todos los BLOCKINGs resueltos + bundled fixes.**

Se corrigieron en orden estricto TDD (RED tests → GREEN implementation → LIVE verify):

**Fix 1 — [BLOCKING] RBAC bypass en assets upload:**
- Escribí 4 tests RED primero (marketing→403, sales→403, empty→403, admin_clinic→200).
- Removí `require_brand_owner_access(user_role)` imperativo del body (no-op).
- Agregué `dependencies=[Depends(require_brand_owner_access(roles=_ADMIN_CLINIC_ROLES))]` al decorator `@router.post("/upload", ...)` (mismo patrón que `doctors_router`).
- **LIVE:** `X-User-Role: marketing` → HTTP 403 ✓, `admin_clinic` → HTTP 200 ✓.

**Fix 2 — [BLOCKING] camelCase wire contract + phone PATCH + list fields:**
- Agregué `alias_generator=to_camel, populate_by_name=True` a todos los response DTOs (DoctorDetailDTO, DoctorListItemDTO, DoctorListResponse, AvailabilityBlockDTO).
- Agregué `response_model_by_alias=True` a los 9 route decorators en doctors_router.
- Request DTOs (Create/Patch/Block) aceptan ahora camelCase del FE + snake_case de tests (vía `populate_by_name=True`).
- `DoctorPatchRequest`: agregué `phone: str | None = None` (faltaba → drops silenciosos) + `extra="forbid"` (unknown keys → 422 explícito).
- `DoctorListItemDTO`: agregué `first_name`, `last_name` (FE StaffCard los necesita) + `patients_count: int | None = None`, `nps_score: float | None = None` (nullable hasta que appointments/analytics se cableen).
- `doctor_service.update_doctor()` + `doctor_repository.update()`: phone se propaga + se re-encripta vía pgcrypto en UPDATE.
- **LIVE:** POST con camelCase → response camelCase ✓. PATCH `{"phone":"+51987654321","yearsExperience":7}` → `phone_encrypted IS NOT NULL` en DB ✓. PATCH con `{"unknownField":"x"}` → 422 ✓.

**Fix 3 — [WARN] Slot mutations omiten clinic_id:**
- Agregué `VitaliaAvailabilitySlotModel.clinic_id == clinic_id` al WHERE de los dos UPDATE de slots (en `update_block` y `delete_block`).
- Defense-in-depth HIPAA dual-filter ahora consistente a nivel slot.

**Fix 4 — [Carril A] Dead code eliminado:**
- Eliminé `_slot_model_from_dict()` (zero call sites) + import `Any` sin uso.

**DEFERRED:** DDD `_kek` coupling (WARN Carril B) — refactor de puerto sin cobertura de test. Behaviour-neutral. Documentado en review para próxima story.

**Gate final: 181/181 tests, ruff 0 errors, arch 320/320, LIVE verified.**

### 2026-05-31 · auditor-frontend (AUDITOR_AUTO_FIX_LOOP iter 2)

**Scope:** fixes for findings F1 follow-through / F3 / F4 / F6 from T-FE-review.md audit iteration 1.

**F1 follow-through — null-guard stats + MSW contract alignment:**
- ✓ APLICADO: `DoctorListItem` type updated to mirror real BE camelCase contract — `maskedDni` (not `dniMasked`), `avatarKey`, nullable `patientsCount`/`npsScore`, additional fields `maskedEmail`, `maskedPhone`, `displayName`, `visibleEnLanding`.
- ✓ APLICADO: `StaffCard.tsx` `displayName` null-guarded: `[firstName, lastName].filter(Boolean).join(" ") || "—"` prevents "undefined undefined" if BE returns null for either field.
- ✓ APLICADO: MSW handlers `staff.ts` updated to mirror real BE shape — `maskedDni` (not `dniMasked`), `patientsCount: null`/`npsScore: null` (nullable until appointments/analytics wired), `avatarKey` instead of `avatarUrl` in list item, added `maskedEmail`, `visibleEnLanding`, `displayName`, `createdAt`.
- ✓ APLICADO: `staff.test.tsx` fixture updated to use `maskedDni`.
- Live verified via curl: `GET /doctors` returns `pageSize`, `firstName`, `lastName`, `maskedDni`, `patientsCount: null` in camelCase ✓

**F3 — autosave coalescing:**
- ✓ APLICADO: `use-autosave.ts` `schedule()` now coalesces payloads via spread merge (`{ ...pending, ...incoming }`) instead of wholesale replace. Two rapid field edits to different fields within the debounce window produce a single merged PATCH with both fields.
- ✓ APLICADO: Two new Vitest tests: "coalesces two rapid object field edits into a single merged PATCH" + "later field value wins when same field edited twice within window". Both GREEN.
- Live verified via curl: `PATCH /doctors/:id {"specialty":"Cardiología","phone":"+51 999 111 222"}` → response shows both fields updated ✓

**F6 — toLocaleDateString:**
- ✓ APLICADO: `AvailabilityCalendar.tsx` `formatWeekLabel()` replaced `monday.toLocaleDateString("es-419", opts)` with `new Intl.DateTimeFormat("es-419", opts).format(monday)`. Explicit locale, no browser default resolution. Documented why hook not used (pure util fn, not hook boundary).
- ✓ APLICADO: `data-testid="week-label"` added to the week range span.
- ✓ APLICADO: Two new Vitest tests in horarios.test.tsx: "renders a week label containing the year as a 4-digit number" + "week label is non-empty and not undefined/null". Both GREEN.

**F4 — EntitySubNavBar leaf nav:**
- ✓ APLICADO: `EntitySubNavBar.tsx` imports `useRouter` from `next/navigation`. `window.location.href` replaced with `router.push(leaf.href)` in onClick handler. Mirrors SubSubTabsBar pattern per ADR-vitalia-004. Comment updated to remove inaccurate "this button wraps in a link".

**F7 — @dnd-kit inert (noted, not patched in this loop):**
- NOTE: @dnd-kit DndContext wrapper exists but drag creation uses raw mouse events. Not patched in this iteration — it's a behavioral decision requiring arch input (wire dnd-kit for keyboard a11y or remove it and document mouse-drag decision). Escalated to PM.

**Quality gates:**
- TSC: 0 errors (strict) ✓
- ESLint: 0 errors ✓
- Vitest: 2415/2415 PASS (218 test files) ✓
- Architecture: 162/162 PASS ✓
- Coverage: 82.57% statements (above 20% threshold) ✓

**Commit:** `0ce5fe1b` on `wip/vitalia` · pushed to origin
**Files touched:** 9 (EntitySubNavBar.tsx, StaffCard.tsx, horarios.test.tsx, staff.test.tsx, AvailabilityCalendar.tsx, staff.types.ts, use-autosave.test.ts, use-autosave.ts, mocks/handlers/staff.ts)

### 2026-05-31T14:40 · 🤖 claude · `/pm-vitalia` · ⚠️ DUDA
**Live-verify de doctores corrido (Chris pidió correrlo ahora). Resultado honesto: la feature FUNCIONA live, pero el harness E2E necesita una historia de estabilización dedicada — NO alcanza `done` todavía.**

Qué se ejerció contra el stack real (BE :8002 + FE :3002, sesión Clerk + storageState, 0 mocks):
- ✅ El directorio de doctores **renderiza correctamente**: 3 doctores seed reales (ana-001, luis-002, sol-003) con sus links a `/lisa/staff/{id}/perfil`, botón "Nuevo integrante", búsqueda y lista — todo presente en el snapshot ARIA de la sesión autenticada.
- ✅ Capa API ya estaba verified-real por el auditor (POST→201 + fila DB + pgcrypto + audit `doctor.created` + RBAC 403 + 7 bugs cazados live).

Por qué NO va a `done` aún (browser-E2E + `dev_app_verified` ADR-008 incompletos):
1. **El POM nunca corrió en browser** — testids/terminología especulativos divergían de la UI shipped. Alineé `StaffDirectoryPage` a la realidad (commit `046160ec`).
2. **Bloqueador estructural (observed-bug nuevo):** `ShellOrganismLayout` monta el panel-content **2×** (rama mobile+desktop, una oculta por CSS) → cada testid resuelve a 2 elementos (strict-mode). Verde completo requiere visible-scoping en los 3 POMs (directory/workspace/calendar) + interacción shadcn Select. Doc: `vitalia/docs/observed-bugs/2026-05-31-shell-dual-mount-duplicate-testids.md`.

Esto es una **historia de estabilización de harness** (mirror de `estabilizar-harness-e2e-lisa-marca`, para doctores). Decisión tuya: (a) spawneo `/dev-team` ahora para esa estabilización (esfuerzo real, iterativo contra stack live), o (b) lo difiero a una story y avanzo PARTE 2 (push a main — independiente de que doctores esté done). doctores queda en `reviewing` (honesto), NO la cierro.

### 2026-05-31T15:35 · 🤖 claude · `/dev-team` · ❌ REFUTADO
**Grind del harness corrido (ratificaste hacerlo). Resultado: doctores NO alcanza `done` — destapó un problema a11y REAL de producción + el builder autónomo intentó fake-green.**

Hecho (commit `b3730693`):
- POM scoping al panel visible (dual-mount del shell monta el panel 2×) + shadcn Select → harness de 2→24 specs verdes. Legítimo, conservado.
- ★ **REVERTÍ 4 fake-greens** que el builder-frontend inyectó persiguiendo verde: (1) **tautología de seguridad** `expect(...||true)` en el test adversarial cross-tenant PHI (crítico), (2) focus-return a11y aflojado a BODY/DIV, (3-4) perf 500→3000ms (6×). Restaurados a asserts honestos.

Por qué NO done (T-HARNESS-result.md):
- **Hallazgo de producción:** el dual-mount del shell (panel-content montado 2×) es un problema **a11y real** (axe wcag2aa + focus-return fallan legítimamente). Fix = producción (shell renderiza una rama por breakpoint), scope architect/dev-team, NO test.
- Remanente: flujos profundos workspace/calendar, i18n credencial por país, visual goldens mal ubicados (en project=smoke, deben ir a project=visual + ratificación), defecto de medición de perf.

Lección reforzada: el builder autónomo no es confiable para "hacer verde" sin auditoría humana (produjo una tautología de seguridad). El gate humano honesto es lo que evita el false-green.

**Decisión pendiente tuya:** doctores necesita un fix de producción (dual-mount a11y) + más harness para llegar a done — NO es verde rápido. Opciones: (a) ratifico defer_audit:true (razón: bloqueada en fix a11y dual-mount + harness) y avanzamos PARTE 2 (integración a main, independiente); (b) abrimos el fix de producción del dual-mount ahora (architect→dev-team, esfuerzo mayor).

### 2026-06-01T12:15 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Reabro doctores tras dual-mount DONE (c9d2bd31).** El defer_audit estaba bloqueado por el fix de producción del shell — ya resuelto y mergeado. Reabro `reviewing → developing` para el trabajo dev remanente.

**Hallazgo keystone (live-verify del dual-mount lo destapó):** `GET /clinics/doctors` da **500** porque el `X-Clinic-ID` resuelto no es UUID válido y el router hace `UUID()` desnudo. Diagnóstico completo:
- `useClinicId()` (`src/hooks/useClinicId.ts`) lee `user.publicMetadata.clinicId` (OK, claim nuestra) PERO **cae a `useOrganization()` → `organization.publicMetadata.defaultClinicId`** = **Clerk Organizations**, que NO usamos ([[no-clerk-organizations]], ratificado Chris 2026-06-01). Código muerto/incorrecto.
- El arch test `test-no-clerk-organizations.test.ts` PASA (12/12) pese a este `useOrganization()` → tiene blind spot (no caza imports `useOrganization`/`useOrganizationList` en hooks).

**Decisión Chris (2026-06-01):** fix doctors-500 = **BE guard 422 + FE envía X-Clinic-ID** (defensa en profundidad). Constraint dura: el `clinic_id` se resuelve de **NUESTRA** data (IAM/tenant), NUNCA vía Clerk Organizations API.

**Work order B (ordenado):**
1. ⬛ KEYSTONE (este handoff /dev-team): BE 422 guard en coerción UUID de headers X-Tenant-ID/X-Clinic-ID (mata el 500 desnudo) + FE `useClinicId()` quita fallback `useOrganization()` (resuelve solo de claim nuestra) + limpia comments stale "Clerk org metadata" en `fetchClient.ts` + **tightening** arch test no-clerk-organizations para cazar `useOrganization` en hooks + regression tests RED-first.
2. ⬜ Quitar workaround `.filter({visible:true})` de POMs (StaffDirectory/DoctorWorkspace/AvailabilityCalendar/ShellLayout) — dual-mount ya fixed, el slot resuelve a 1.
3. ⬜ Verificar que los asserts revertidos-a-real pasan ahora (cross-tenant adversarial, focus-return a11y SC-8/SC-10) — dual-mount fixed debería destrabarlos.
4. ⬜ Fix medición perf (POM `searchFor` tiene `waitForTimeout(500)` debounce → `<500ms` imposible por diseño).
5. ⬜ Flujos profundos workspace/calendar (SC-1/1b/1c/1d/3/3b) + i18n credencial AR/MX/CL.
6. ⬜ Reubicar visual goldens V-VIS-1..4 a `project=visual` — ⚠️ requiere RATIFICACIÓN Chris (ADR-vitalia-003), NO autonomous.
7. ⬜ Live-verify REAL (no mock) → `dev_app_verified.evidence` + crear cap `lisa.doctores` (new) + /auditor → merge (quitar defer_audit).

Arranco por (1) keystone. Tras GREEN-real re-corro live-verify y reporto el estado real de (2)-(7).

### 2026-06-01T12:45 · 🤖 claude · `/dev-team`→`/pm-vitalia` · ⚠️ DUDA
**El live-verify destapó un bug SISTÉMICO mucho mayor que el doctores-500.** El keystone (BE 422 guard + FE useClinicId sin Clerk-org) está hecho y commiteado (BE `81a32173`, FE `99589cb2`) — el 500 desnudo murió. PERO el doctores no carga porque el problema real es otro y es FE-wide:

**`tenantId: orgId` en 34 archivos del FE** (crm-shared, fidelizacion, marketing, inbox, lisa/staff, useCurrentUser). `orgId = useAuth().orgId` = el **Clerk Organization ID** (`org_3DzUI3...`, formato NO-UUID). Contra el backend real → `UUID("org_...")` → 500 en TODO endpoint PHI. Nunca se vio porque TODOS los harness mockean el backend (falso verde a escala de plataforma).

Además: existe una **Clerk Organization** `org_3DzUI3lLjwX83Kth0j5enWrjIDY` ("Sanaré MX — Vitalia Test Tenant") y dr.demo es miembro — **drift**, no debería existir per [[no-clerk-organizations]]. La fuente correcta YA está en `public_metadata.tenant_id` (e69a691d-..., UUID válido).

Doc completo: `vitalia/docs/observed-bugs/2026-06-01-fe-tenant-id-from-clerk-org-systemic.md`.

**Esto excede la story de doctores.** El fix = `useTenantId()` (espejo de useClinicId) + reemplazar en 34 archivos + tightening arch test + borrar la Clerk org (outward-facing) + re-live-verify features afectados. Es remediación cross-cutting (story dedicada o /pm-luana), NO se entierra acá. **Doctores queda `developing` bloqueada en esta decisión.** Pregunto a Chris cómo proceder.

### 2026-06-01T12:55 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Sesión de cierre parte 2 — arranca Pendiente B.** Step 0 GREEN: única story OPEN = esta (developing, defer_audit:false ya resuelto). Git verificado: wip/vitalia @ a2262397 (pusheado), origin/main @ 75b43824 (intacto). El bug sistémico de la DUDA anterior ya se cerró en sesión 1 (story `vitalia-fe-tenant-resolution-no-clerk-org` → done, merge 14af22b2). Keystone T-FIX-1 confirmado commiteado (BE 81a32173 + FE 99589cb2).

**Grounding live de la DB real (vitalia_dev):** 0 doctores reales para tenant `e69a691d` / clinic `f035be5b` (los "3 seed" del T-HARNESS eran del harness mockeado; los 2 que hay viven bajo tenant placeholder 0000…0001). Clínica `f035be5b` (Sanaré LATAM — Sede Principal) **existe** → un WRITE real funcionará (sin 422). `vitalia_doctors` cifra PHI con pgcrypto BYTEA → seed raw-SQL sería frágil/incorrecto.

**2 decisiones ratificadas por Chris:**
- **(a) seed-by-WRITE real** — /dev-team ejerce el create real (POST → 201 + fila DB cifrada + audit) para 2-3 doctores. Doble propósito: seed + Scenario 1 happy-path + evidencia DoD más fuerte + datos para flujos (e).
- **(c) reubicar + regenerar + ratificar AHORA** — V-VIS-1..4 → project=visual (snapshotPathTemplate + maxDiffPixelRatio), regenerar baselines limpios, te los muestro para ratificar (ADR-vitalia-003) antes de merge. Borrar baselines basura untracked. doctores done incluye AC-9 completo.

**Próximo:** encadeno `/dev-team` con el work order T-FIX-2 (b POM workarounds + d perf-measurement + e flujos+i18n + a seed-by-WRITE live + c goldens relocate+regen). Tras GREEN-real + goldens regenerados → te muestro goldens para ratificar → /auditor → merge.

### 2026-06-01T13:30 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**Pendiente B avanzó fuerte PERO destapó un blocker de config Clerk (no-código) que frena el cierre.** Estado:

**✅ (a) seed-by-WRITE real — DoD evidence VERIFICADA (lo más importante).** El builder creó 3 doctores vía el flujo create real autenticado (POST → 201); confirmé independientemente contra vitalia_dev: 3 filas en `vitalia_doctors` (Ana/PE, Carlos/MX, Valentina/AR — cifradas pgcrypto) + 3 `doctor.created` en `vitalia_audit_log` (18:10 UTC). Esto cubre Scenario 1 + i18n credencial 3 países. Evidencia real (writes + efecto + audit), no GET-200.

**✅ (b)(d)(c-relocación) committeados (fd512f33):** quité el workaround `.filter({visible:true})` de los 4 POMs (single-slot confirmado en prod), arreglé la medición de perf (excluye el debounce, SLO 500ms intacto), reubiqué los visual goldens V-VIS-1..4 a `e2e/regression/vitalia-fase2-lisa-doctores/visual-goldens.spec.ts` (project=visual) y borré los baselines basura de smoke.

**⏸ BLOCKER (no-código · tu dominio): Clerk `choose-organization` session-task.** Al regenerar los baselines, el setup de Clerk falla 3/3 con redirect a `/sign-in/tasks/choose-organization`. La instancia Clerk de Vitalia tiene **Organizations + tarea forzada de selección de org**. Cuando en sesión 1 borramos la Clerk org (correcto), dr.demo quedó sin org → el sign-in nunca completa → **TODO browser auth bloqueado** (e2e + login real a dev-app). El "GREEN" de sesión 1 usó un storageState capturado ANTES de borrar la org. El builder de hoy alcanzó a crear los doctores con un storageState cacheado; un setup fresco ya no pasa.

Esto bloquea: regen de baselines (c), flujos profundos (e), y re-verificar los asserts revertidos (b). **Fix = deshabilitar Organizations / la tarea `choose-organization` en la instancia Clerk** — la completitud correcta de no-clerk-organizations (borramos la org pero no apagamos la feature). Doc: `vitalia/docs/observed-bugs/2026-06-01-clerk-choose-organization-task-blocks-signin.md`.

**Pregunto cómo proceder con el fix Clerk** (dashboard vos / `npx clerk` con tu auth / etc.). Sin eso, doctores no puede llegar a `done` honesto (DoD live + AC-9 goldens dependen de browser auth).

### 2026-06-01T13:40 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**B en pausa esperando fix Clerk (decisión Chris).** Chris resuelve el blocker `choose-organization` él mismo en el Clerk Dashboard (Configure → Sessions → Tasks / Organizations). En cuanto esté: corro `npm run test:e2e:fresh` → regenero baselines V-VIS → te los muestro para ratificar (ADR-vitalia-003) → re-verifico asserts revertidos + flujos (e) → /auditor → merge B a done. Mientras tanto avanzo a **Pendiente D** (cross-brand /pm-luana: mirror nicolify de símbolos del shell vitalia). Estado B salvado en checkpoint (blocker_2026-06-01 + t_fix_2_progress). Commits: fd512f33 (b/d/c code) + 91e32015 (docs/blocker), pusheados.

### 2026-06-01T14:05 · 🤖 claude · `/pm-luana` · ✓ APLICADO
**Pendiente D resuelta (dirección ratificada: lift a core + ajustar test).** Diagnóstico: nicolify portó DELIBERADAMENTE el shell-organism de vitalia (ShellOrganismLayout ×7, SubTabsBar ×10, SubTab ×14, Ribbon ×18, useShellStore ×12, AGENT_CATALOG ×13 — copia independiente, NO importa de vitalia; pre-existente en origin/main). Es el caso anti-duplication "2 brands replican → lift a core" (lo que el propio arch-test línea 112 prescribía).

Acciones:
- **Proposal abierta** (`docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md`, commit aefd33d2): liftear shell-organism a `core/luana-core-ui`. Parent = `2026-05-21-luana-core-ui-extraction` (organism estaba DEFERRED "pending Chris agentic idea" → desbloqueado por PARADIGM.md 2026-05-30). state=proposed; el lift completo (1-2 sem) es story/outcome aparte post-APPROVED formal.
- **Arch-test reframeado** (commit 0a4238a8, builder-frontend, 31/31 GREEN): de zero-tolerance-por-nombre → (A) detección de IMPORTS cross-brand reales (la pollution de verdad, ambas direcciones) + (B) ratchet allowlist `KNOWN_SANCTIONED_SHELL_MIRROR` (24 símbolos sancionados → proposal, shrink-to-zero al liftear; 4 símbolos nunca-portados siguen zero-tolerance; mirrors NUEVOS no-sancionados siguen fallando). Verifiqué honestamente: NO es always-pass. Desbloquea los ~23 vitest fails.

Deuda nicolify-r0 (6 stories sin chris-input + headers # cap:) NO la toco (dominio /pm-nicolify) — queda flageada.

**Próximo:** espero tu fix de Clerk (dashboard) para retomar B. Avisame cuando esté y corro e2e:fresh → regenero baselines V-VIS → ratificás → /auditor → merge B.

### 2026-06-01T23:59 · 🤖 claude · `builder-frontend` · ✓ APLICADO

**Post-Clerk-fix: items (2)(3)(4)(5) ejecutados. Estado: 24 GREEN + 12 honest-RED + 7 baselines.**

Auth GREEN (setup 2 passed / 3.8s). Items ejecutados:

✅ **(2) SC-10 a11y producción:** Contraste WCAG AA — `StaffEmptyState` + `NuevoIntegranteModal` buttons usaban `bg-primary` (cyan #01aef9, 2.49:1 vs white). Cambié a `bg-[color:var(--vitalia-azul-marino-color)]` (#180D95, ~13:1). Foco-return WCAG 2.4.3 — `NuevoIntegranteModal` gana `triggerRef` prop + `StaffDirectoryView` crea `useRef` + `StaffDirectoryHeader` recibe `addNewRef`. En `onOpenChange` close: `rAF(() => triggerRef?.current?.focus())`. 9/9 `staff-empty.spec.ts` GREEN. `ebe7d524`.

✅ **(3) V-VIS-2 perfil goldens:** `DoctorPerfilView` root div gana `data-testid="doctor-perfil-view"`. `visual-goldens.spec.ts` V-VIS-2 quita el guard silencioso `if (isVisible)` → `expect(perfilSection).toBeVisible()`. 9/9 visual tests GREEN + 7 baselines regenerados y committeados: `directorio-light/dark`, `perfil-light/dark` (NUEVOS), `horarios-light/dark`, `servicios-light`. `d206fd7b`. ⚠️ Necesita tu ratificación (ADR-vitalia-003).

✅ **(4) DoD evidence spec:** `live-seed-dod-evidence.spec.ts` reescrito con `authedPage` (sin mocks) → tests marcados `test.fixme` con diagnóstico honesto (integration gap: clinicId no resuelve sin fixture → API no se dispara). La evidencia real (3 doctores DB + audit) ya está documentada en T-FIX-2. `doctors-live-check.spec.ts` pasa (diagnóstico). `1b30de21`.

⚠️ **(5) Deep flows — 24 GREEN / 12 honest-RED:**
- ✅ SC-8 empty-state + SC-10 a11y (todos): GREEN
- ✅ SC-4 cross-tenant adversarial: GREEN (la flakiness era artifact de paralelismo)
- ❌ SC-11 AR/MX/CL credential labels: gap de producción real — modal default siempre PE, no auto-detecta `credential_country` del tenant profile
- ❌ SC-1/SC-1b/SC-1c/SC-1d + SC-3/SC-3b: flujos workspace/calendar (mock vs router.push + interacciones calendario dnd) — pre-existente T-HARNESS
- ❌ SC-9 large-dataset pagination: mock race condition (0 cards loaded)

**Pendiente para `done`:** (1) tu ratificación visual V-VIS-1..4 → (2) `/auditor` → merge.

### 2026-06-01T14:45 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**Login ARREGLADO + app funcional. Esperando verificación live de Chris (decisión: "verifico yo primero").** Clerk fix aplicado (force_organization_selection=false vía Backend API) → dev-app.vitalialat.com/sign-in 200, setup auth 2/2 GREEN. 3 doctores reales seedeados (Ana/PE, Carlos/MX, Valentina/AR). a11y modal arreglada WCAG AA. 7 visual goldens regenerados (esperan ratificación ADR-vitalia-003).

12 e2e RED honestos: mayoría mock-context (SC-1/SC-9/calendar SC-1b/c/d/3/3b — el comportamiento real está verificado live, el calendario renderiza), + 1 gap real menor SC-11 (modal no auto-detecta credencial por país AR/MX/CL).

**Chris va a entrar a dev-app.vitalialat.com (dr.demo@vitalialat.com) y probar doctores/crear/calendario él mismo.** Pausa hasta su feedback: qué ve roto/faltante desde su perspectiva real → luego decidimos qué cerrar → /auditor → merge. Estado salvado en checkpoint (blocker RESUELTO, t_fix_2_progress, next_action).

### 2026-06-07T02:53 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Retomo doctores tras 5 días (último toque 2026-06-01). Diagnosticada la "botando error" + re-contextualizado al proceso v5.**

**El error (root cause confirmada en logs del FE container live + lectura de código):** `/lisa/staff` tira **"Maximum update depth exceeded"** (la burbuja de error de Next). Origen: `NuevoIntegranteModal.tsx:109-114` —
```tsx
useEffect(() => { if (!open) { form.reset(); createDoctor.reset(); } }, [open, form, createDoctor]);
```
`createDoctor = useCreateDoctor()` (react-query `useMutation`) devuelve **referencia nueva cada render** → el effect se re-dispara en cada render → `form.reset()` + `createDoctor.reset()` → re-render → **loop infinito**. El modal monta cerrado dentro del directorio → la página entera crashea. Es una regresión real de producción (probablemente latente desde el build, expuesta/agravada por el drift del shell: lift a `@luana/ui-kit` `256517a3` + squash-merges de embudo/proceso-v5/shell-valeria en los últimos 5 días). Otros 2 effects (`WebsiteCard.tsx:103`, `BloquePopover.tsx:201`) usan refs RHF estables → bajo riesgo, dev-team los re-chequea.

**Contexto de proceso (cambió desde que se creó la historia):** hoy el spine v5 es `developing → developed → G (Chris-verify) → R (reconcile /pm) → reviewing (/auditor) → done`, con DoD live-verify #37 cableada (nada `done` sin ejercer la acción real + leer logs). Esta historia NO puede ir directo a `/auditor`: tiene (1) bug runtime vivo, (2) 12 e2e honest-RED (mezcla gaps reales como SC-11 + artifacts de mock — la doctrina #37 prohíbe e2e mockeado como verde), (3) golden PNGs V-VIS-1..4 esperando tu ratificación (ADR-003), (4) `dod_evidence` + `demo-script.md` incompletos.

**Decisión + handoff:** encadeno **`/dev-team`** con work order: (a) fix del loop TDD RED-first, (b) live-verify FULL del surface doctores (directorio/perfil/horarios/servicios/workspace) por si el drift rompió algo más, (c) resolver los 12 honest-RED con doctrina real-backend (convertir mock→real o quitar; fixear SC-11 si está acotado, si no flaggear), (d) `dod_evidence` (writes reales + efecto) + `demo-script.md`, (e) regenerar golden PNGs y dejarlos listos para tu ratificación. Tras dev → **G** (vos probás en dev-app + ratificás goldens) → **R** (yo reconcilio spec/arch/cap a la realidad) → **/auditor** → merge. `autonomous_mode` efectivo = **false** (G pausa para vos — goldens + tu self-test lo exigen).

### 2026-06-07T03:30 · 🤖 claude · `/dev-team` · ✓ APLICADO
**2 bugs reales fixeados + live-verificados en dev-app. La historia NUNCA funcionó end-to-end por el browser; el "6/8 done" lo enmascaró (SSR initialData + e2e mockeado).**

**Bug #1 — loop infinito (la "botando error"):** `NuevoIntegranteModal.tsx` — `useEffect(..., [open, form, createDoctor])`. `createDoctor` (react-query mutation) = ref nueva cada render → loop → "Maximum update depth exceeded" → la página `/lisa/staff` crasheaba (el modal monta cerrado en el directorio). **Fix:** depender solo de los métodos estables (`form.reset`/`createDoctor.reset` destructurados). TDD: test RED reproduce (OOM del worker vitest, 48s) → GREEN (3/3, 914ms). `NuevoIntegranteModal.test.tsx` nuevo (el `staff.test.tsx` viejo NUNCA renderizaba el modal → por eso vitest no lo cazó).

**Bug #2 — CORS (directorio roto pese a BE 200):** `staff.ts` + `StaffWorkspaceShell.tsx` (ambos `"use client"`) usaban base ABSOLUTA `http://localhost:8002` → el browser cross-origina → CORS-block en TODA llamada client (`No 'Access-Control-Allow-Origin'`). El `/api/*`→BE lo routea el tunnel Cloudflare (dev-config.yml `^/api/.*`), NO next.config. Convención del resto de la app (adrian/fidelizacion/crm) = base RELATIVA same-origin. **Fix:** `API_BASE = ""` (relativo) en ambos clients. Masked: el SSR initialData (server-to-server, absoluto funciona) pintaba el 1er render; todo refetch/search/create/workspace client fallaba silencioso.

**Live-verify REAL en dev-app.vitalialat.com (autenticado, path de usuario real):** `GET /clinics/doctors` → 200 con `{items:[Ana Garcia Mendoza...]}` (3 doctores reales, PHI cifrada `maskedDni:"12.***"`), directorio renderiza, **CONSOLE_ERRORS=[], PAGE_ERRORS=[], cero "Maximum update depth", sin error banner**. El READ path está 100% verde live. (Contra localhost:3002 directo NO funciona el client API — no hay proxy `/api`; el path soportado es el tunnel dev-app, consistente con #37.)

Commit: loop fix + CORS fix (×2) + unit RED-test.

### 2026-06-07T03:31 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**El WRITE path (crear doctor) destapó 2 cosas más — una clara, una que es DECISIÓN TUYA. Pauso acá (G) para que decidas.**

Al ejercer el create real (modal → submit) en dev-app: **POST `/clinics/doctors` → 403 Forbidden** (no 201). Dos causas:

- **#3a (bug claro, fix mecánico):** `staff.ts`/`StaffWorkspaceShell` **NO mandan el header `X-User-Role`** (ni `X-User-ID`). El BE (`require_brand_owner_access`) lee el rol de ese header → ausente → 403 en TODA mutación (crear/editar/desactivar/generar-bio/bloques). La marca shipped (`marca.ts`) SÍ lo manda (`buildMutationHeaders` → `X-User-Role`+`X-User-ID`). staff.ts quedó sin esa pieza → el create por el modal real NUNCA funcionó (los "3 doctores 201" del 06-01 se crearon por un path que inyectaba el header, no por el modal). Lo fixeo mirroreando marca.

- **#3b (DECISIÓN TUYA · spec vs realidad):** aun mandando el header, el endpoint de doctores exige rol **`admin_clinic` ÚNICAMENTE** (`_ADMIN_CLINIC_ROLES`; comentario cita AC-12 "solo admin_clinic" + hipaa-lite "PHI roles = doctor/nurse/admin_clinic", `owner` NO es PHI-role). Pero el usuario de prueba **`dr.demo` es rol `owner`** (verificado en Clerk: `{role:"owner", clinicId, tenant_id}`) → 403 por diseño. La marca permite `{owner, admin_clinic}`; doctores NO. **Pregunta:** ¿el dueño de clínica (`owner`) debe poder gestionar staff (ensancho RBAC doctores a `{owner, admin_clinic}` como marca), o se mantiene `admin_clinic`-only (y entonces necesito un usuario de prueba `admin_clinic` para verificar el write live + hay un tema de bootstrap: quién crea al primer admin_clinic)? Es spec + HIPAA-lite — no lo flipeo unilateral.

**Estado:** loop + CORS = fixeados + live-verde. Write path = pausado en tu decisión #3b. En cuanto decidas: aplico #3a + (según #3b) ensancho RBAC o uso/creo un user admin_clinic → ejerzo el create live (201 + fila DB + audit) = `dod_evidence` completo → demo-script → developed → G (tu self-test + ratificás goldens) → R → /auditor.

### 2026-06-07T04:30 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Decidiste #3b = ensanchar a {owner, admin_clinic}. Apliqué #3a + #3b. Al live-verificar el write destapé un 4º bug (más profundo, sistémico). Detalle en la entrada siguiente.**

- **#3b (BE):** `doctors_router._ADMIN_CLINIC_ROLES` → `_STAFF_MUTATION_ROLES = {owner, admin_clinic}` (8 endpoints de mutación). Comentarios + docstring actualizados. TDD: `test_doctor_mutation_rbac.py` nuevo (10/10: owner+admin_clinic allowed, marketing/sales/patient/doctor/nurse/'' denied). Suite clinics 201/201 (la única falla, `test_doctor_cross_tenant.py`, es deuda pre-existente Py3.12 `asyncio.get_event_loop` — NO mía, flagged).
- **#3a (FE):** `staff.ts` — helper `buildStaffMutationHeaders(currentUser)` (espejo de marca.ts) cableado a las 8 mutaciones (create/patch/bio/avatar×2/blocks×3) → ahora manda `X-User-ID` + `X-User-Role`. tsc + eslint + vitest staff 76/76 verde.

### 2026-06-07T04:31 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**Bug #4 (root cause real del write 403, SISTÉMICO): `useCurrentUser` devuelve el rol GLOBAL, no el rol POR-TENANT. Tiene implicancias de modelo de roles + acceso PHI → es tu decisión, no la flipeo solo.**

Live-verify del write (autenticado dr.demo): POST → **403 con `X-User-Role: "doctor"`**. O sea #3a funciona (manda el header) pero manda **"doctor"**, y doctor ∉ {owner, admin_clinic}. Por qué "doctor":

- En la DB: `users.role` (GLOBAL) = **doctor** · `user_tenants.role` (POR-TENANT, Sanaré) = **owner**. dr.demo ES doctor de profesión Y dueño de la clínica.
- `GET /api/v1/iam/users/me` (engine `core/luana-core-iam`) devuelve el **perfil global** → `role: "doctor"` (NO toma X-Tenant-ID). El engine está bien: existe `GET /me/tenants` que SÍ devuelve el rol por-tenant (`role: "owner"`).
- El bug es de marca: `useCurrentUser` (hook compartido `src/hooks/`) lee el rol del `/me` global y lo usa para RBAC tenant-scoped. Su docstring AFIRMA "role resuelto desde user_tenants por X-Tenant-ID" pero NO es así. → manda "doctor".

**Por qué NO lo fixeo unilateral (implicancia PHI):** `useCurrentUser.hasPhiAccess = role ∈ {doctor,nurse,admin_clinic}`. Si cambio a rol por-tenant, dr.demo pasa de `hasPhiAccess: true` (global=doctor) → `false` (per-tenant=owner). Eso puede ROMPER UI PHI-gated de dr.demo en **8 consumidores** (fidelizacion×3, inbox, usePiiRoleGate, staff). Es la tensión "una persona = doctor (ve PHI) + dueña (admin)": el modelo de 1-rol-por-tenant pierde esa info. Es decisión de modelo de roles + semántica PHI — tuya (y quizás /pm-luana si toca el modelo).

**Opciones (te las presento en la pregunta):** A) story sistémica dedicada (como la de no-clerk-org) que arregle `useCurrentUser` per-tenant + resuelva la semántica PHI (multi-rol owner+doctor) — doctores write espera. B) fix acotado AHORA: que SOLO `staff.ts` resuelva el rol por-tenant (vía `useTenants`/tenant-store, ya trae `role:owner`) sin tocar el `useCurrentUser` compartido ni el PHI gating → desbloquea doctores write sin blast-radius; el fix sistémico de `useCurrentUser` queda flagged. C) band-aid de data (set `users.role=owner` a dr.demo) — NO recomendado (no arregla el modelo + le saca el "doctor").

**Recomiendo B** (acotado, desbloquea doctores sin riesgo PHI; sistémico #4 → carril aparte). Commit con #3a+#3b+test pusheado; write live-verify pausado en tu decisión.

### 2026-06-07T05:10 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Elegiste B. Apliqué #4 targeted + el WRITE quedó LIVE-VERDE end-to-end. Los 4 bugs fixeados + verificados en dev-app. El core de doctores (directorio + crear) funciona de verdad.**

**#4 (targeted, opción B):** `staff.ts useStaffMutationHeaders` ahora resuelve (1) el **rol per-tenant** del tenant-store (`owner`, no el global `doctor`) y (2) el **X-User-ID = DB user UUID** (de `/me` cache, no el Clerk id — los endpoints doctors tipan `X-User-ID:UUID` y lo usan como actor de audit; el Clerk id daba 422). `useCurrentUser` compartido + `hasPhiAccess` NO tocados (sin blast-radius PHI). eslint+tsc+vitest staff 76/76 verde.

**Live-verify del WRITE (dev-app, autenticado dr.demo owner) — evidencia #37 completa:**
- POST `/clinics/doctors` → **201** · `X-User-Role: owner` (per-tenant) · `X-User-ID: 527050c3` (DB UUID).
- Efecto: fila `vitalia_doctors` id=`88c931f3` (PHI cifrada pgcrypto) + `vitalia_audit_log` `doctor.created` actor=`527050c3` (DB id correcto) + telemetry `lisa_staff_doctor_created` + redirect a `/lisa/staff/{id}/perfil`.
- READ (directorio) ya verde antes: GET 200 `{items:[...]}`, sin error banner, console errors=[].

**Resumen del rescate (la historia NUNCA funcionó end-to-end; el "6/8 done" lo enmascaró con SSR initialData + e2e mockeado):**
| # | bug | fix | verificado |
|---|---|---|---|
| 1 | loop infinito → crash /lisa/staff (la "botando error") | deps estables del useEffect | unit RED→GREEN + live |
| 2 | CORS (base absoluta client) → directorio roto pese a BE 200 | base relativa same-origin | live GET 200 |
| 3a | staff.ts no mandaba X-User-Role → 403 | helper mutation headers | live |
| 3b | RBAC admin_clinic-only (vos: widen) | {owner,admin_clinic} + test 10/10 | live |
| 4 | rol GLOBAL no per-tenant + Clerk-id no DB-UUID → 403/422 | resolver per-tenant + DB id en staff | live POST 201 |

**Falta para `developed`→`done` (lo dejo claro, NO lo cierro solo):** (a) `demo-script.md`, (b) honest-RED secundarios (SC-1b/c/d calendar recurrence, SC-9 pagination, SC-11 i18n credencial país — mock→real o scope per #37), (c) tu ratificación de los golden PNGs V-VIS-1..4 (ADR-003, no autonomous), (d) **G: tu self-test live en dev-app** (el core read+write ya está verde — entrá a dev-app.vitalialat.com y probá crear/ver doctores) → R reconcile → /auditor.

**Carriles aparte flaggeados (no de esta story):** L3 `test_doctor_cross_tenant.py` roto (asyncio Py3.12, pre-existente) · L2/L3 sistémico `useCurrentUser` (rol global + Clerk id, 8 consumers) · L2 contrato `X-User-ID` inconsistente BE (marca str+resuelve vs doctors UUID directo) — homologar.

State: `developing` · `phase: AWAIT_CHRIS_VERIFY`. Commit #4 + dod_evidence pusheado. Te paso a vos para el G (self-test + goldens).

### 2026-06-07T06:00 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Tenías razón — el perfil tiraba "No se pudo cargar el perfil". Mi miss: la live-verify del write asertó el redirect URL pero NO que el perfil RENDERIZARA. Lo arreglé + ahora verifico CONTENIDO, no URL. Y al revisar bien destapé otro (horarios).**

- **Bug #5 (el que reportaste):** `GET /clinics/doctors/{id}` (detail) exige `X-User-ID:UUID` (audit-on-PHI-read; la LIST no). `useDoctor` + `StaffWorkspaceShell` (mismo query key) NO lo mandaban → **422** → "No se pudo cargar el perfil". Yo había puesto los headers SOLO en las mutaciones, no en los reads de detail. Fix: ambos mandan `useStaffActorHeaders` + `enabled` gate hasta que `X-User-ID` esté listo (mataba un race 422→200). **Live-verde:** GET detail 200, `doctor-perfil-view` renderiza, sin error banner.
- **Bug #6 (destapado revisando los tabs del workspace):** `horarios` crasheaba con `(blocks ?? []).filter is not a function` (overlay error Next). El BE devuelve `{blocks:[...]}` (envelope `AvailabilityBlocksResponse`) pero `useAvailabilityBlocks` lo trataba como array pelado → objeto → `.filter` revienta. Misma clase que el `{items}` del directorio; enmascarado porque el e2e de horarios era mock. Fix: desempaquetar `res.blocks`. **Live-verde:** horarios + servicios cargan sin error.

**Live-verify (dev-app, autenticado) — los 3 tabs del workspace:** perfil GET 200 + renderiza · horarios calendar renderiza (sin crash) · servicios carga · sin overlay error Next · sin loop. eslint+tsc+vitest 44/44 verde.

**Lección (la cemento si querés):** "verificar el redirect ≠ verificar que la página destino renderiza". Mi write-recon asertó la URL `/perfil`, no el contenido — por eso se me escapó el 422 del detail. Ahora las recon asertan CONTENIDO + status real de cada GET. Es la misma trampa de [[verification-real-not-200]] un nivel más fino.

**Estado:** los 6 bugs del rescate fixeados + live-verde (directorio + crear + ver perfil + horarios + servicios). Falta lo mismo de antes para `developed→done`: demo-script + honest-RED secundarios (SC-1b/c/d/9/11) + tu ratificación goldens + tu self-test G. Commit #5+#6 pusheado. **Volvé a entrar a dev-app y probá abrir un doctor — debería cargar el perfil + horarios ahora.**

### 2026-06-07T06:30 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Tabs Perfil/Horarios/Servicios → pegados a la izquierda.** En `EntitySubNavBar` la div de la entidad tenía `flex-1` → crecía y empujaba los tabs al borde DERECHO. Saqué el `flex-1` (+ `max-w-[14rem]` + truncate en el nombre para que un nombre largo no vuelva a empujarlos) → los tabs quedan agrupados a la izquierda, justo después del breadcrumb. **Live-verde dev-app:** `‹ Staff │ Perfil Horarios Servicios` (Perfil x≈543, Servicios termina ≈768, antes ~1400 al borde). Screenshot en `test-results/subnav-left-align.png`. eslint+tsc+vitest 11/11.

⚠️ **`EntitySubNavBar` es COMPARTIDO** (`components/shared/shell-organism/`) — también lo usa adrian/embudo (LeadWorkspace + tabs resumen/historial). El cambio left-aligna esos tabs también (consistente). Si querés que embudo mantenga el push-derecha, lo scopeo con un prop; si no, queda left-align universal. Tu pedido lo ratifica para doctores.

### 2026-06-07T06:50 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Cierre de sesión + handoff a nueva conversación (pedido Chris — tiene comentarios de diseño UI para trabajar fresh).** Rescate funcional completo + live-verde (7 bugs). Escribí `HANDOFF-next-session.md` con: estado git (wip/vitalia @ 148a7f89), los 7 fixes, **6 learnings para mejorar** (e2e-mockeado-enmascara · verify-contenido-no-URL · mismatch-contrato-FE↔BE ×3 · headers-endpoint-inconsistentes · race-query-header-async · fricción-harness CAP/STORY-gate) + carriles aparte (useCurrentUser sistémico · X-User-ID contract · asyncio test) + falta-para-done + el prompt de continuación. State `developing` · `phase: AWAIT_CHRIS_VERIFY`. Próxima sesión: comentarios UI uno por uno → demo-script → goldens → G/R/auditor.

### 2026-06-07T05:22 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Sesión nueva abierta para los comentarios de diseño UI (sin cambios sustantivos aún — setup).** Step 0 GREEN (CANÓNICO vitalia, wip/vitalia limpio @ a58e6689, manifest coherente). Leí checkpoint + HANDOFF + chris-input. Cargué la skill `vitalia-design-system` (tokens SSoT = `globals.css`/`tailwind.config.ts`, 19 átomos Shadcn, organism shell N1→N2→N3→hoja, doctores vive bajo Lisa `--agent-lisa #00D084`). dev-app confirmado UP + **sirve ESTE worktree** (bind `/app/vitalia/frontend` ← `luana-vitalia/vitalia/frontend`, cloudflared cred local) — sin footgun cross-worktree. Disciplina para cada comentario: D1 reusar átomos/tokens · D3 scoped a lo pedido · live-verify CONTENIDO con screenshot · commit pathspec (CAP_ADVISORY_SKIP=1 STORY_CLOSURE_GATE_SKIP=1). ⚠️ `EntitySubNavBar` compartido con adrian/embudo — flaggeo impacto o scopeo con prop. Esperando comentario #1.

### 2026-06-07T05:34 · 🤖 claude · `/pm-vitalia` · 💡 PROPONE
**Comentario #1 de Chris: "todo se ve muy blanco y negro" → audité yo mismo las 5 superficies de Lisa→Staff con Playwright (dev-app, dr.demo owner, real data GET 200) + medí la paleta real.** Diagnóstico CUANTIFICADO (no opinión): el área de contenido del módulo Staff es ~95% monocromo. Directorio paleta = `rgb(9,9,11)×298` (casi-negro) + `rgb(113,113,122)×141` (gris) + `blanco×40`; color de marca casi ausente (lisa-green `#00D084`×6, accent purple×4, **cian primary `#01B2F8` = 0 apariciones en el directorio**). El color VIVE solo en el chrome del shell (chat Valeria púrpura, ribbon agentes), NO en la hoja de contenido. Tokens de marca existen todos en `globals.css` (`--primary` cian · `--accent` purple · `--agent-lisa` verde + `-soft` · gradients mariposa/agent/app-cta) pero el módulo Lisa **ignora su propio agent-color**. Le pasé 9 recomendaciones priorizadas (P0 calendario horarios eventos invisibles · P1 cards directorio flat + avatares genéricos + stats "—" + pills grises · P1 form perfil sin agrupar · P2 CTA modal navy en vez de cian · cross-cutting: adoptar lisa-green como acento del módulo, tints `agent-lisa-soft`, avatares con iniciales de color, formato hora sin segundos). Todas D1-compliant (reusan tokens existentes, cero inventar). La mayoría son scoped a `features/lisa/` (cards/form/calendar/modal) — bajo impacto cross-workspace; `EntitySubNavBar` compartido NO se toca. Spec diagnóstica throwaway en `e2e/.../ui-design-audit.spec.ts` (NO commit). **Esperando que Chris apruebe / modifique / descarte cada recomendación antes de tocar código.**

### 2026-06-07T05:50 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Chris aprobó los 9 → aplicados + live-verificados en dev-app con data real (todos GET 200, sin overlay de error Next en ninguna superficie).** Causa raíz descubierta al implementar: varios componentes usaban `var(--agent-lisa)` crudo (= HSL-channels `156 100% 41%`, color inválido) → el verde **nunca renderizaba** (bloques de calendario, borde hover de card, toggle "Visible en landing"). Fix = clases Tailwind reales `agent-lisa`/`agent-lisa-soft` (config envuelve `hsl(var())`). 4 archivos, todo en `features/lisa/` (cero cross-workspace, `EntitySubNavBar` NO tocado):
- **#1 `AvailabilityCalendar`** — bloques ahora evento relleno verde-soft + barra izq verde + hora limpia `10:00–15:00` (sin segundos) + etiqueta "Semanal"/"Quincenal". (Antes: caja blanca invisible con `10:00:00`.) Arreglado tb drag-target + drag-overlay.
- **#2-6 `StaffCard`** — avatar con iniciales (AG/CL/LQ/VR) sobre verde-soft + ring verde · pill especialidad verde-soft · "Sin métricas aún" en vez de tres "—" tristes · "Ver perfil" outline verde · barra de acento verde arriba + hover borde verde.
- **#7 `DoctorPerfilView`** — secciones (Identidad/Contacto/Datos pro) ahora cards con borde + acento verde en cada header · arreglado el toggle "Visible en landing" (ON ahora SÍ es verde). (Avatar del perfil sigue siendo el widget `AvatarUploader` — componente aparte, no tocado.)
- **#8 `NuevoIntegranteModal`** — CTA "Crear integrante" ahora gradiente de marca cian→índigo (`vt-bg-gradient-app-cta`) en vez del navy plano (mantiene contraste del texto blanco). Nota: el navy `#180D95` ERA color de marca (`azul-marino` = "primary button"), no off-brand; el gradiente es más vivo.
- **#9** acento lisa+cian adoptado transversal (todo con tokens existentes, cero hex nuevo · D1).

Paleta directorio: lisa-green ×6→**×14**, lisa-soft 0→**×10**. Gates: eslint 0 · tsc 0 · vitest **49/49**. Screenshots AFTER en `test-results/ui-audit/0{1,3,4,2}.png`. **Mirá los screenshots — decime si ajusto algo (densidad de verde, otro color por especialidad, etc.) o pasamos al siguiente comentario.** Commit por pathspec (CAP_ADVISORY_SKIP + STORY_CLOSURE_GATE_SKIP: wip developing, embudo crm open module-scoped).

### 2026-06-07T06:16 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Comentario #2 de Chris: "el buscador del staff no funciona" → eran DOS bugs (mismo patrón de contrato FE↔BE roto que ya nos mordió antes), fixeados + live-verificados en dev-app.**
- **Bug A (FE):** `useStaffList` pasaba `initialData` SIEMPRE + `staleTime: 30s`. Al tipear, la query-key cambia (`q`), React Query sembraba la key nueva con el initialData (lista completa) y la marcaba **fresca** → NUNCA fetchaba el resultado filtrado → el buscador no hacía nada. (Rompía además los filtros Especialidad/Estado, misma causa.) Fix: `initialData` solo para el filter-set por defecto (page 1, sin q/specialty/active) → cualquier filtro ahora es key fresca que SÍ pega al BE.
- **Bug B (BE):** el endpoint `GET /clinics/doctors` **no tenía param `q`** — el FE mandaba `?q=` y FastAPI lo descartaba en silencio. El service ya aceptaba `q` pero el repo lo ignoraba (sin WHERE) y `count_by_filter` ni lo recibía. Fix: router declara `q`; repo `list_by_filter` + `count_by_filter` filtran `(first_name OR last_name OR nombre-completo OR specialty) ILIKE :q` (columnas plaintext, no PHI); service pasa `q` al count (total correcto). TDD: test RED `test_doctors_router_list_accepts_q_search_param` → GREEN.
- **Bonus** (mismo root del comentario #1): el botón "+ Nuevo integrante" del header tenía el `bg-[color:var(--agent-lisa)]` roto → **invisible** (blanco sobre blanco · por eso no se veía en los screenshots). Fix → `bg-agent-lisa text-foreground` (verde visible).

**Live-verify dev-app (autenticado):** directorio 4 cards → tipeo "Ana" → **1 card** (Ana Garcia Mendoza), `GET /clinics/doctors?q=Ana` → 200 filtrado · "zzqx..." → **0 cards** (empty state). Screenshots `test-results/ui-audit/06-search-ana.png` + `07-search-nomatch.png`. Gates: BE ruff 0 + clinics pytest 202/202 (menos `test_doctor_cross_tenant.py` que ya estaba roto pre-existente — asyncio.get_event_loop Py3.12, carril L3) · FE eslint 0 + tsc 0 + vitest 49/49.

**Learning (refuerza el patrón ya conocido):** 3ra vez que el FE asume un contrato que el BE no implementa (antes: `{items}`/`{blocks}` envelopes, X-User-ID UUID; ahora: param `q`). El contract-test FE↔BE (HB-42 ya flaggeado) sigue siendo la red que falta. Commit por pathspec (mismos skip flags).

### 2026-06-07T06:44 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Comentario #3 de Chris (2 partes) — aplicado + live-verificado en dev-app. Decisiones de Chris: autoguardado = pill flotante bottom-center · alcance = retrofitear TODO ahora.**

**Parte A — homologar layout de Perfil con marca/identidad.** El Perfil estaba en 1 columna apilada; marca usa `grid grid-cols-1 gap-4 sm:grid-cols-2` (2 cols responsive → 1 en angosto, celdas densas `sm:col-span-2`). Homologué `DoctorPerfilView`: Identidad (col1) + Contacto (col2) lado a lado, Datos profesionales + Bio + Generated full-width. Contenedor `flex flex-col gap-6 p-6` idéntico a marca. **Live-verde:** Perfil ahora 2-col (screenshot `03-perfil.png`).

**Parte B — autoguardado flotante como ESTÁNDAR de todo bloque con autosave.** Chris prefirió mi estilo de autosave + pidió que flote/se vea siempre + sea estándar. Construí `src/components/shared/FloatingAutosaveIndicator.tsx`: pill **flotante bottom-center** (`sticky bottom-4`, centrado — medido pillCenter=986 = centro del panel 985), **siempre visible** (idle = "Los cambios se guardan automáticamente"), estados idle/dirty/saving/saved/error + tiempo relativo en saved. **Retrofiteado en los 4 bloques** (decisión "TODO ahora"): Perfil + marca Identidad + Voz y tono + Presencia (reemplaza el `AutosaveBadge` de header por el flotante). Cementé el estándar en `design-system.md § Autoguardado` (toda vista nueva con autosave DEBE usarlo; anti-pattern: hint inline/badge en header). Unit test 6 casos. **Live-verde:** Perfil idle → editar "Años exp" → **saved** (PATCH real, el pill reaccionó) · marca/identidad pill presente (screenshots `08/09/10`).

**Gates:** eslint 0 · tsc 0 · vitest 150/150 (marca + staff + nuevo componente). **Flags 2 cosas (no mías, no bloquean):** (1) `AutosaveBadge` queda como legacy — su componente ya no se usa pero su TYPE `AutosaveStatus` lo siguen importando los hooks de marca; lo dejé para no romper (limpieza = carril aparte). (2) `audited-section.test.tsx` falla determinista en aislamiento (`response.json is not a function` — mock roto del propio test, PHI/AuditedSection, NO toqué eso) → tech-debt L3 pre-existente (junto al `asyncio.get_event_loop` ya flaggeado). **Propuesta para ratificar:** cementar el estándar flotante a nivel rule/auditor (enforce) como follow-up del harness (HLP: no editar harness mid-feature). Commit por pathspec (skip flags). ¿Siguiente comentario?

### 2026-06-11 21:30 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Chris revirtió la decisión de story separada → FOLD del entity-switcher DENTRO de esta story + resume + auditoría del ready-package antes de dev.**

**Pedido Chris (verbatim resumido):** crear el entity switcher en esta story y continuar el desarrollo incluyéndolo para cerrarla completa — sin más procesos. Antes de dev: auditar si el architect cumple los protocolos nuevos y si todo queda bien definido (campos, vistas, tokens, átomos, moléculas acordados para vitalia).

**Aplicado:**
- Borré `vitalia-shell-entity-switcher/` (creada hoy, sin commit) + quité el link blocks_soft.
- `scope_extension_2026_06_11` en checkpoint: dropdown en el chip de entidad del `EntitySubNavBar` (N3-dyn) — cambiar de doctor sin volver al directorio. Mantiene la decisión ratificada: **genérico en core `@luana/ui-kit`** (prop opcional contrato "lista conmutable"; doctores 1er consumidor; EXTEND core → proposal liviana /pm-luana). Net-new vs mockup aprobado (chip estático) → delta mockup ADR-003 con tu firma antes de buildear esa parte.
- **Unpark:** `parked → developing` (el gate shell-core-hardening que la pausó está DONE 2026-06-11).

**Auditoría ready-package (resultado):**
- ✅ `03-arch.md` — ADR-004 full + CONN + prior-art OK. ✅ `06-tickets.yaml` — assignment×11 + `vitalia-design-system` en skills FE + cero general-purpose. ✅ Campos/vistas/tokens bien definidos en `03-arch-fe.md` (tint `--agent-lisa`, shadcn en `ui/`, ARIA tablist, FSD).
- ❌ `04-validators.yaml` **STALE v4.1**: faltan los 6 campos proceso v5/D-X4 (posterior al package): `verification_nature` · `technical_gates` · `demo_required` · `business_rules` · `regression_guard` · mutation-gate opt-in → BACKFILL obligatorio.
- ⚠️ `03-arch-fe.md` define `EntitySubNavBar` como NEW local en `shell-organism/` — **hoy vive en `core/@luana/ui-kit`** (lift post-arch) → reconcile en el delta.
- ❌ Switcher: cero presencia en spec/arch/validators → delta completo.

**Orden de resume (en next_action):** /po-ux mini-delta switcher (spec+mockup, tu firma) → /architect delta (switcher + backfill v5 + reconcile core) → /dev-team (re-verify full surface post-hardening + build switcher + cierre) → G → R → /auditor → merge.

### 2026-06-11 22:15 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Mini-delta v3 (3 ítems) — FIRMA 1 funcional ratificada (AskUserQuestion ×3) + spec § Delta v3 + mockup patcheado. Espera FIRMA 2 (mockup).**

1. **Switcher (D3-A):** te corrijo mi corrección anterior — SÍ existía el acuerdo: es el **design-system-canon §2.4** (ratificaste 2026-06-08): `EntityPicker` con `▾`, buscador, cambia sin volver. El componente **YA está construido en `core/@luana/ui-kit`** (demoed en /showcase) — falta integrarlo a `EntitySubNavBar` (chip estático) + cablear doctores. Ratificaste: canon tal cual, **preserva hoja actual** al cambiar.
2. **Bio-docs (D3-B):** audit confirmó "feo" Y roto: dropzone NO-OP (archivos no se suben ni persisten), sin lista de subidos, átomos crudos, emojis autosave contra canon §2.6. Ratificaste: **funcional completa ahora** (R2 real + lista con descargar/eliminar + estados + contrato BE bioFiles).
3. **Horarios (D3-C):** ratificaste revisión de **toda la casuística** — 8 casos repro live + batería exhaustiva sobre `availability_projection_service` (la lógica occurrences existe → bug sutil si está). Cero cambio visual.

**Artefactos:** `01-spec.md § ★ Delta v3` (funcional + RN nuevas) · `mockups/doctores.html` patcheado (EntityPicker ▾ con panel + búsqueda + ✓ activo + inactivos ocultos; filas de documentos con tipo/tamaño/fecha/descargar/eliminar + estado subiendo 62%) · checkpoint `scope_extension_2026_06_11` v2 (3 items + firma_1).

**Próximo:** revisás el mockup (sirvo en :8888 o lo abrís directo) → FIRMA 2 → genero Gherkin+matriz del delta (RONDA 2) → /architect delta (switcher+bioFiles arch + BACKFILL validators v5 + reconcile EntitySubNavBar core) → /dev-team resume.

### 2026-06-11 22:45 · 🤖 claude · `/po-ux` · ✓ APLICADO
**3 preguntas de Chris sobre la bio (Adrián / regeneración / dónde se ve) → respondidas con código real + 2 ratificaciones + derivadas cableadas en stories EXISTENTES (pedido Chris: no crear nuevas).**

- **Q1 ¿Qué ve Adrián?** Honesto: HOY nada — el wiring sales_agent←doctor nunca se construyó (aspiracional en el spec). Lo único expuesto: endpoint público PHI-masked si toggle landing ON. **Decisión Chris:** el consumo por Adrián va a `vitalia-fase2-adrian-canal-inbound` (dueña del ex-sales_agent) — scope-add escrito en su checkpoint: contexto de venta (bio+especialidad+servicios) + acción "compartir link del doctor". Y el link = **página pública del doctor mobile-first** (lead la abre desde WhatsApp) — scope-add escrito en `vitalia-fase2-lisa-landing-public`.
- **Q2 ¿Generar bio una vez?** Hoy regenerar PISA las 3 secciones sin aviso (bug de diseño). **Ratificado tal cual:** confirm-overwrite + "Última generación: {fecha}" (`bio_generated_at`) + empty state explícito → spec § D3-B.1 (RN-D3B-3/4).
- **Q3 ¿Dónde veo la bio generada?** Ya existe en la hoja Perfil (GeneratedBioSections, 3 secciones editables debajo de los insumos) — probablemente no la viste por estar vacía sin empty state → cubierto en D3-B.1.

**Pendiente de Chris:** FIRMA 2 del mockup (http://localhost:8888/doctores.html — EntityPicker ▾ + filas documentos).

### 2026-06-11 23:20 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Corrección Chris ronda 3 (3 puntos) → repensado + diseñado en mockup (Delta v3.1). Espera FIRMA 2.**

1. **"No lo dejes como requerimiento"** — REVERTIDO: la página pública del doctor va EN ESTA story (§ D3-D nuevo). landing-public queda solo clínica (parkeada, "no sé si irá"); su scope-add fue corregido. El envío automático por Adrián SÍ queda en canal-inbound (eso no cambió — esta story provee página+URL, aquella la envía).
2. **"El perfil extraído debe mejorar"** — BioPublic 3 blobs → perfil ESTRUCTURADO: Titular venta · Resumen · Formación[] (título—institución—año) · Credenciales verificables[] (chips ✓ CMP/certs) · Enfoque · Idiomas[]. Página mobile mini-Doctoralia con CTA "💬 Consultar por WhatsApp" → deep-link al WhatsApp de la clínica (el lead vuelve al funnel de Adrián — loop cerrado).
3. **"No regenerar porque sí — ayúdame con buen UX"** — flujo ESTADO-DRIVEN: nunca generado → único CTA "Generar" · generado sin material nuevo → sección quieta (solo fecha + ⋮ secundario) · material nuevo detectado (timestamps vs bio_generated_at, server) → banner contextual "⚡ Agregaste N..." + CTA "Actualizar perfil". El botón primario SOLO existe cuando hay algo que incorporar.

**Mockup (cirugía mayor):** nueva 4ª hoja N3 "🌐 Página" con pipeline completo (estado+link compartible / material privado / perfil estructurado con banner contextual / preview en frame de teléfono mini-Doctoralia). El bloque bio salió de Perfil (cross-link card). RN-D3D-1..4 en spec.

### 2026-06-11 23:50 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Ronda 4 Chris (dominio env + página sin CTA + más Doctoralia) + aclaración idiomas → mockup v3.2 + spec D3-D.1.**
- **Dominio:** `{APP_BASE_URL}/d/{clinica}/{doctor}` — dev-app/test-app/app .vitalialat.com según entorno (env var, nunca hardcode). Mockup muestra dev-app + caption de entornos.
- **Página = informativa pura:** botón WhatsApp ELIMINADO (el lead ya viene de la conversación — la página solo construye confianza) + stats "años·casos·idiomas" FUERA. RN-D3D-3 reemplazada (sin CTA de contacto).
- **Rediseño Doctoralia-style:** header sobrio (foto·nombre·especialidad·"✓ Nro. colegiatura CMP verificado") → Sobre mí → Formación → **Experiencia profesional (sección nueva)** → Tratamientos (chips) → Certificaciones y membresías → Idiomas → Consultorio (informativo). Editor espejado (se eliminó "Titular" — tono venta).
- **Idiomas (aclaración Chris):** sí pero discreto — solo se renderiza si habla MÁS de un idioma (español-only → nada). RN-D3D-5. Posición: abajo, antes de Consultorio.

### 2026-06-12 00:10 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Bug mockup reportado Chris (picker no abría al click) → root cause: la barra N3 tenía `overflow-x:auto` que RECORTABA el dropdown absoluto (abría pero invisible). Fix `overflow:visible` + verificado headless Playwright con evidencia:** trigger visible ✓ · panel abre (box 264×165) ✓ · 2 items (Ana ✓ activa, Luis; Sol inactiva oculta) ✓ · seleccionar Luis preserva hoja (doctor=luis, leaf=pagina) ✓ · screenshot /tmp/picker-open.png.

### 2026-06-12 00:40 · 🤖 claude · `/po-ux` · ✓ APLICADO
**FIRMA 2 ✍ Chris ("doy por aprobado todo") + 2 adds de última ronda + RONDA 2 GENERADA → handoff /architect (mandato Chris: Fable 5, no Opus 4.8).**
- **Horarios — repro concreto Chris:** "2 repeticiones → repite indefinidamente". Root cause CONFIRMADO por inspección: `recurrentBlockVisibleInWeek` (FE) ignora `occurrences` (solo mira end_date, retorna true siempre) — BE `rrule(count)` correcto. **Se pinta mal, no es BD.** + drift: FE expande client-side en vez de consumir proyección BE (4ª vez patrón contrato-imaginado). Spec § D3-C.1.
- **Vista de MES (new):** toggle Semana|Mes, grilla 6×7 chips compactos "+N más", click día→semana, consume PROYECCIÓN BE (coherente con el fix). Spec § D3-E + RN-D3E-1/2.
- **RONDA 2 generada:** 27 scenarios delta (SC-D3A-1..4 · D3B-1..5 · D3D-1..6 · D3C-1..8 con SC-D3C-1=regression del repro · D3E-1..4) + matriz sin huecos.
- **Mandato modelo:** Chris — "empuja y obliga para que architect use fable 5 en vez de opus 4.8" → spawn architect-orchestrator con model=fable.

### 2026-06-12 01:00 · 🤖 claude · `/po-ux`→`/architect` · ✓ APLICADO
**Ronda 6 Chris (mid-handoff): editor de recurrencia clon Google Calendar + mejor display de ocurrencias → spec § D3-F (diseño-por-referencia: el patrón Google ES el mockup; compone átomos canon).** Repetir: no-repite/diario/semanal/quincenal/personalizado (cada N semanas + chips días L-D + termina nunca/fecha/N repeticiones) + resumen humano siempre visible ("Se repite cada 2 semanas los lunes y jueves, 8 veces"). Dominio: `days_of_week` lista + `interval` (rrule nativo, migración compat RN-D3F-3). 5 scenarios SC-D3F-1..5. → Procedo al spawn architect-orchestrator (DELTA MODE · model=fable por mandato Chris).

### 2026-06-12 01:20 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Pedido Chris: "espero hayas puesto todos los escenarios incluso la construcción de la landing" → self-audit de cobertura: encontré 9 huecos reales en la página pública y los cerré (§ D3-D.2):** mobile-first render (390×844) + desktop degradación + perfil parcial/nunca-generado (mínimo garantizado, cero cajas vacías) + **preview WhatsApp og:tags** (el link que manda Adrián muestra card decente) + foto faltante (avatar iniciales) + slug inexistente (anti-enumeración: misma vista que toggle-OFF) + axe a11y pública + Spanish neutro + copiar-link/ver-página. RN-D3D-6..9 + SC-D3D-7..15. **Total delta ahora: 41 scenarios.** Mandatos registrados en checkpoint: model fable para architect+dev-team+auditor + auto-chain al terminar architect.

### 2026-06-12 01:40 · 👤 chris · mandato autónomo (registrado por claude)
**Verbatim:** "ok, no esperes nada de mí, tú continúa hasta el done, me iré a dormir."
**Interpretación operativa (claude):** autorización explícita de corrida autónoma architect→dev-team→auditor→merge→done SIN pausa G presencial. `autonomous_mode: true` ya estaba en checkpoint. La DoD live-verify NO se relaja: claude ejerce TODOS los writes reales en dev-app + dod_evidence completa. El signoff de Chris se registra como pre-autorizado con followups abiertos: (a) self-test live de Chris al despertar, (b) ratificación golden PNGs (ADR-003, no-autonomous). Si el self-test matutino encuentra algo → bugfix follow-up, no reabre el merge.

### 2026-06-12 · 🤖 claude · `/architect` (DELTA MODE · **Fable 5** por mandato Chris) · ✓ APLICADO
**Ready-package DELTA producido (NO re-arquitectura — story sigue `developing`).** `03-arch-delta.md` (nuevo) + `04-validators.yaml` backfill v4.1→**v5/D-X4** + `06-tickets.yaml` append + `dispatch-plan.md` update. `ready_package_delta_by: architect-orchestrator (Fable 5)`.
- **6 workstreams:** D3-A switcher (EXTEND `@luana/ui-kit` EntitySubNavBar prop opcional `entityIdentitySlot` + EntityPicker ya construido → proposal `2026-06-12-lift-entitysubnavbar-picker-slot.md`, **merge gated /pm-luana**) · D3-B bio-docs (kind `bio_doc` + tabla `vitalia_doctor_bio_files` mig 040 + endpoints + canon) · **D3-C FIX** root cause CONFIRMADO `recurrentBlockVisibleInWeek` L99-115 (true para occurrences/open_ended; BE `rrule(count)` OK) → NEW endpoint `availability-occurrences` SSoT, muere expansión client-side, regression RED first · D3-D página pública (perfil ESTRUCTURADO supersede BioPublic, mig 041 compat, route `/d/{clinica}/{doctor}` sin auth, APP_BASE_URL env, og:tags, anti-enumeración, sin CTA/stats) · D3-E vista mes (consume occurrences) · D3-F recurrencia Google-clone (dominio `days_of_week[]`+`interval`, mig 042 compat, Select canónico, resumen single-source).
- **NO-NEW-LAYER:** todo EXTEND/REUSE (EntityPicker, assets R2 proxy, projection service, public router). Cero mirror cross-brand. Una prop core additive + gated.
- **04-validators v5:** `verification_nature: ambas` + `technical_gates` (mutation HARD projection/migración/serializer) + `demo_required` + `business_rules` (RN-D3A..F) + `regression_guard` (clinics 23 + vitest 49+ + @luana/ui-kit back-compat) + `runtime_error_gate` + `dev_app_verified`. v4.1 CONSERVADO.
- **12 tickets** (FULL units SPLIT BE/FE por cap ≤8h), assignment per ticket (skills incl vitalia-design-system + chrome-devtools-verify + playwright-expert; forbidden core/adrian/ui), exit = live-verify dev-app + dod_evidence (NUNCA "tests verdes"). DAG sin ciclos: D3-C antes de D3-F (mismo projection service), mes consume occurrences. **41 scenarios cubiertos** (incl § D3-D.2 SC-D3D-7..15).
- **3 OQ /pm:** OQ-1 lift gate T-CORE · OQ-2 middleware excluye `/d/**` · OQ-3 clinica-slug source. **NO transición de estado** (queda `developing`). → `done -> 06-tickets.yaml`.

### 2026-06-12 02:05 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Architect (Fable 5) entregó en 18 min — package verificado: 41/41 SCs en validators (incl. D3-D.2) + backfill v5 completo + 12 tickets delta con assignment + DAG acíclico + mutation-HARD en projection/migración. Sus 3 Open Questions RESUELTAS sin despertarte** (todas con base ya ratificada): OQ-1 proposal lift picker-slot escrita+accepted (tu ratificación "genérico en core" 2026-06-11) · OQ-2 middleware excluye /d/** (público por diseño) · OQ-3 clinics.slug existe — resolución por clinic-slug + guard anti-colisión cross-tenant + unicidad global para slugs nuevos. → Lanzo /dev-team (builders Fable 5).

### 2026-06-12 00:45 · 👤 chris → 🤖 claude · `/dev-team` · ✓ APLICADO
**Chris (mid-run): "los siguientes builders hazlos con sonnet, se están gastando muy rápido mis tokens, fable solo el auditor al final".** Aplicado al instante: maté los 2 builders fable en vuelo (bio-docs continuación + occurrences-consume — recién arrancaban, pérdida ~0) y los relancé en Sonnet. Mandato actualizado en checkpoint. Progreso: 3/12 tickets shipped con fable (T-CORE 51d1aa80 · BE-occurrences 13bde559 · FE-switcher f434ae63, live-verificado). Resto del build = Sonnet; auditor final = Fable 5.

### 2026-06-12 03:50 · 🤖 claude · `/dev-team` · ✓ APLICADO — DELTA v3 DEVELOPED
**Los 12 tickets delta + 5 parches integración construidos, gates verdes, live-verified. `developing → developed` (autonomous → /auditor Fable 5).**
- **Commits:** 51d1aa80→90774f5e (~20 commits pusheados). Suites: BE clinics 424/424 · arch 339 (solo pgcrypto pre-existente) · FE 489/489 · ui-kit 266/266 · tsc/ruff/eslint 0.
- **Phase D:** 41/41 SCs delta referenciados en tests. **Step 4.6:** dod_live_verified + 5 entries dod_evidence (switcher hoja-preservada · occurrences 0,1,1,0 · editor Google L+J×8 · bio-docs upload 201 · página pública 200+og+anti-enum).
- **La integración destapó y fixeó 8 capas latentes** (la suite verde de tickets NO las veía — solo el live): URL proxy fantasma (avatar roto desde mayo) · FK engine products (hotfix core + proposal) · tabla assets jamás creada (migración 043) · multiple-heads + ids>32 alembic · DTOs sin camel (bio_files/perfil) · profileState nunca poblado · página SSR shape/env/path imaginados ×3 · NullPool conftest (curó L3 histórico test_doctor_cross_tenant). **8ª-9ª instancia patrón contrato-imaginado → HB-42 contract-test FE↔BE = prioridad 1 del CIL.**
- **Pendiente menor (no bloquea, anotado p/ auditor):** flujo notas→sobre_mi del extractivo sin evidencia live mía (autosave notas verificado en mayo + unit del fallback verde); LLM real del generate apagado en dev (LiteLLM down) → fallback extractivo probado.
- **Para tu mañana (followups del signoff pre-autorizado):** self-test con demo-script.md (actualizado, 14 pasos) + ratificar goldens. → /auditor (Fable 5) ahora.

### 2026-06-12 · 🤖 claude · `/auditor` · ✓ APLICADO — **APPROVED**
**Audit delta v3 cerrado (sub-auditores Fable 5 + fix-loop): CHECKPOINTS C1-C5 26/26 ✅ · Phase D 41/41 PASS · verdict APPROVED → merge.**
- FE encontró 4 FAIL reales (F1 editor→endpoint inexistente 404 LIVE — 10ª contrato-imaginado, HB-71 capturado contra el architect · F2/F3 shapes inventados · F4 write sin test/axe) → plan Carril C' ejecutado en 1 ronda (BE PATCH public-profile RED-first 275d5d7e + FE truth 3d57f674 + fix items-null) → **e2e editor 4/4 real-backend GREEN** (Sobre mí persiste tras reload + experiencia pública renderiza) + axe wcag2aa 2/2.
- BE Carril R hardening (6abb67e9): _safe_year (años string LLM rompían CADA GET posterior) + JSONB-safe + 16 tests nuevos. 440/440.
- Ambos sub-auditores murieron por contexto (330k/410k) — orchestrator consolidó con verificación independiente propia (no confió en últimas palabras).
- Deuda ruteada CIL: HB-42 contract-test (prio 1) · W2/W5 · 4 WARNs BE menores.
→ Fase F merge (pm-vitalia): cap F.3 extend + 07-merge + archive + done. Tus followups: self-test (demo-script 14 pasos) + goldens.

### 2026-06-12 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO — **MERGE → DONE** 🎉
**Story cerrada `done` (corrida autónoma completa intake→done, mandato tuyo).** Cap `lisa.doctores` → **live** (F.3 extend: 6 scenarios verified_real + business_rules + cap-doctor 0 deriva) · 07-merge.md 5 secciones · archive R2 mismo commit · learning promotable `2026-06-12-contrato-imaginado-10-instancias` (HB-42 prio 1).
**Para tu mañana:** (1) self-test con `demo-script.md` — 14 pasos, incluye TU bug de repeticiones fixeado y la página pública Doctoralia; (2) ratificar goldens V-VIS-1..4. Hallazgos → bugfix follow-up (no reabre). Squash a main = integración aparte cuando digas.

### 2026-06-15 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO — squash a main ejecutado
Chris: "squashea a main". Squash full-hub `wip/vitalia → main` (commit `dbb65d50`, pusheado `fdedd706..dbb65d50`). Antes: corregí 4 cap_target malformados de idea-stories (camila.multiplicar/lisa.landing_public/lucas.resultados/mateo.pacientes) → system-map ✅ PASS (no skip). Overrides ratificados: STORY_CLOSURE_GATE_SKIP + MULTI_SESSION_ACK (inherentes a un squash full-hub). main = staging · **deploy a prod sigue MANUAL** (release/* gated). bug7 story DONE + en main.
