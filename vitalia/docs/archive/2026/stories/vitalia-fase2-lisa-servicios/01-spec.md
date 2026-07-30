---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
type: ui-story
state: refining
architecture_pattern: ADR-vitalia-004
po_ux_version: 3
round: 2
input_spec_signed: true
mockup_final_signed: true         # ✍ FIRMA 2 Chris 2026-06-15 (visual "queda" + ratificó spec RONDA 2 + pasar a architect)
state_note: refined               # /pm-vitalia flip refining→refined 2026-06-15 (ver checkpoint.md)
last_session: 2026-06-15          # reconciliación cambios sesión 15-jun + § Mapa de campos + § Inventario de componentes + RONDA 2 Gherkin/Matriz
---

# 01-spec · vitalia-fase2-lisa-servicios — Catálogo de servicios de Lisa (agente-first)

> **RONDA 1 (intención) — draft.** Este doc se escribe en 2 rondas / 2 firmas (`docs/process/spec-mapa-funcional.md`).
> RONDA 1 = § Context/Dónde vive + § Mapa funcional + pantallas-borrador + dudas → Chris firma "esto es lo que quiero".
> RONDA 2 = § Gherkin + § Matriz de cobertura + mockup FINAL → transition refining→refined.
> Reframe agéntico + recomendación PM + decisiones Chris: **`00-research.md`** (SSoT).

---

## § Context

- **Release:** F2. **Módulo:** `offer` (consume Offer Studio engine · NO `treatments` — eso es el followup de Camila).
- **Capability:** `lisa.servicios` (`cap_change_type: new`).
- **User journey:** la dueña/admin de la clínica entra a **Lisa → Servicios** para declarar QUÉ ofrece la clínica. Es la fuente de verdad del catálogo que después **Adrián vende** (canal-inbound match + Propuestas), **Mateo agenda** (duración), **Lucas promociona** y la **landing pública** muestra (la landing es **su propia historia** `lisa-landing-public` — fuera de scope acá).
- **Por qué importa (visión agéntica):** el catálogo no es una grilla bonita para el dueño — es el **cerebro compartido** que el equipo de agentes vende. Diferenciador H1 (agente que conoce el catálogo + cotiza + maneja objeciones). Hueco de mercado: ningún competidor (cero.ai · botclinico · rendu · Dentalink · doctocliq) conecta catálogo → conversación de venta de forma self-serve con un equipo de agentes.

### Dónde vive (zona/caja → shell → ruta)

- **Zona:** Agentes · **Caja:** Lisa (`agent_owner: lisa`) · **Área:** `lisa.servicios` (SYSTEM-MAP `agents.lisa.functional_areas.servicios`).
- **Shell:** shell-organism (ADR-vitalia-004 + `SHELL-DESIGN-CONTRACT.md`): TopBar global + Ribbon 5 especialistas + SubTabsBar + ValeriaSidebar (50/50 split). El contenido vive en el `panel-content`.
- **Rutas:**
  - `/{tenantId}/(shell-organism)/lisa/servicios` — toggle **Catálogo | Escalera** (persiste `?view=catalogo|escalera`).
  - `/{tenantId}/(shell-organism)/lisa/servicios/[offer-id]` — workspace N3-dyn de un servicio (5 leaves `EntitySubNavBar`).
  - **Crear (★ Chris #1 2026-06-07):** NO hay ruta/Sheet aparte. "+ Nuevo servicio" **crea un borrador** (Offer draft) y **redirige al MISMO workspace `[offer-id]`** pero **vacío** para llenarlo (idéntico a editar uno existente). El workspace vacío ofrece **arranque por documento** (cargar material → "Procesar con Lisa" → autocompleta los campos · extracción editable, NO RAG).
  - (★ eliminada · Chris #3 2026-06-06) ~~`…/servicios/ladder/[slot-id]`~~ — peldaños FIJOS, sin workspace de peldaño.
- **Mockup de partida (referencia):** `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/mockups/lisa-servicios-placeholder.html` (ya tiene el toggle Catálogo|Escalera + tokens del shell).

### Out-of-scope explícito (anti-creep)
- A/B testing de pricing · imports bulk (CSV) · AI suggested-pricing (anti-objetivos ratificados).
- El **tool agéntico** `match_service_and_specialist` (vive en `canal-inbound`, decisión Chris 2026-06-06). Esta story SOLO entrega la **data**: Offers publicadas + link servicio↔doctor.
- Edición del engine `core/luana-core-offer-studio` (consume vía EP-2; cambio de engine → `/pm-luana`).
- **Documento → conocimiento (A autocompletar + B RAG)** ahora **EN scope** (Chris #1 + #2 · RN-17/RN-21/RN-22 · § Modelo de conocimiento). **Sigue fuera:** que el agente **responda libre lo clínico** (contraindicaciones/diagnóstico) — eso **escala al doctor**, nunca RAG; y el **precio nunca sale del documento**. Una **Base de conocimiento cross-servicio a nivel tenant** (más allá del per-servicio) queda para su propia story.

## Prior art applied

- **Engine consumed:** `core/luana-core-offer-studio` — `Offer` + `OfferValueLevel` (5 peldaños: Gancho Gratuito·Primera Compra·Oferta Principal·Maximización·Corporativo) + `ServiceDetails` (duración, sesiones) + `value_level_catalog.py` + `offer_ladder_hints.py` (filas `PROFESIONAL_SALUD` con ejemplos médicos). Registrado vía **Extension SDK EP-2 preset pack** (`vitalia/backend/.../offer/extensions.py` — hoy stub vacío → materializar). CERO edit engine.
- **Engine consumed:** `core/luana-core-sales-agent` — `TenantKnowledgeBuilder.build_identity()` ya inyecta las Offers publicadas en la identidad del agente → Adrián lee el catálogo **sin plomería nueva** (desbloquea canal-inbound RN-16).
- **Reused from vitalia:** `lisa-marca` (done) — voz de marca (slot 5 BRAND_VOICE) genera las descripciones de cada servicio. `lisa-doctores` (developing) — tabla `vitalia_doctors` + roster para el link servicio↔doctor.
- **Reused from vitalia:** componentes shell shipped (TopBar, Ribbon, SubTabsBar, ValeriaSidebar) + `@dnd-kit/core` (ya usado en `adrian-embudo`).
- **Net-new justificado:** link servicio↔doctor brand-level (engine no lo tiene) · **3 cobros por servicio** (reserva/seña + anticipo + financiamiento) brand-level — el hueco que ningún competidor llena. (★ ya NO hay `pricing_override`/`cta_copy` por peldaño — peldaños fijos, Chris #3 2026-06-06.)
- **Lift candidate:** si comunify/otra brand necesita el mismo "canvas escalera sobre Offer Studio" → escalar `/pm-luana` (promotion a `core/luana-core-ui` futuro). Por ahora brand-local.
- **NO es PHI:** el catálogo de servicios es información comercial pública, NO datos de paciente → aplica tenant-isolation raíz, NO el full HIPAA-lite (dual-filter clinic se evalúa por multi-clínica, no por PHI — ver interrogatorio Q2).

---

## § Modelo del servicio (resuelto RONDA 1 · nivel humano — `/architect` concreta el schema)

Un **servicio = una Offer de Offer Studio** (engine, vía EP-2). Campos (offer engine + proyección brand-level):

| Campo | Origen | Notas |
|---|---|---|
| nombre | engine `Offer.public_name` | — |
| qué incluye / descripción | engine + **voz de marca** (lisa-marca) | Lisa la sugiere; editable |
| especialidad / categoría | brand-level | dental, estética, etc. |
| **duración** | engine `ServiceDetails.session_duration_minutes` | Mateo agenda con esto |
| **precio fijo o rango** ("desde $X") | engine pricing + brand flag `price_is_range` | moneda = `tenant_locale` |
| **multi-sesión / paquete** | engine `ServiceDetails.total_sessions_count` | "diseño de sonrisa" = paquete; ortodoncia/botox = N sesiones |
| **peldaño (value_level)** | engine `OfferValueLevel` | 5 rungs canónicos, labels médicos |
| **recurrente** (flag + frecuencia) | brand-level `is_recurring` + `recurrence_interval` | atributo, NO peldaño; Camila lo usa para recall |
| **doctores** (N) | brand-level link servicio↔doctor → `vitalia_doctors` | opcional; cimiento canal-inbound RN-17 |
| **reserva de cita / seña** (monto fijo o %) | brand-level | monto chico para **apartar el turno** (reserva prepagada Vitalia · anti-no-show); **se descuenta del total** |
| **anticipo para iniciar** (% o monto del total) | brand-level | pago inicial **del tratamiento**, aparte de la reserva (clave en implantes/ortodoncia/cirugía); lo consume Adrián/Propuestas |
| **financiamiento en cuotas** (admite + N cuotas + MSI) | brand-level | el **saldo** en cuotas; ≈monto/mes calculado; lo consume Adrián/Propuestas |
| **scope clínica** (opcional) | brand-level | a qué clínicas se ofrece (null = todas) |
| **activo** (toggle único) | brand-level | Adrián lo conoce + vende. (★ toggle "landing" ELIMINADO de esta story — Chris #2 2026-06-06; la landing es otra historia) |
| **vínculo a servicio estándar** (`canonical_service_ref`) | brand-level → biblioteca | ★ 2026-06-12 · null = personalizado. Estandariza nombres + reportes comparables + match de Adrián (§ Biblioteca de servicios estándar) |

> **★ Cambio Chris 2026-06-06 (post-mockup):** los peldaños de la escalera son **FIJOS** (5 columnas canónicas). El peldaño de un servicio = su `value_level` (un solo dato). **NO** existe `pricing_override` ni `cta_copy` por slot, ni un workspace de peldaño — eso agregaba complejidad sin valor. Mover un servicio entre peldaños solo cambia su `value_level`.
>
> El engine NO se toca. Lo brand-level vive en la tabla de offers de vitalia (extensión) + el link servicio↔doctor. `/architect` decide la forma exacta (columnas brand vs tabla aparte) + el preset pack EP-2.

## § Workspace del servicio — contenido por pestaña (★ Chris #1 · agente-first · research 2026-06-06)

> Objetivo: que **Adrián tenga TODO lo que necesita para ofrecer y cerrar el servicio**. Fundado en research de treatment-coordinators dentales/estéticos + manejo de objeciones + FAQ de pacientes high-ticket + KBs de agentes IA clínicos (fuentes en `00-research.md` / research log). Marca: **🔴 must-have** (el agente no vende bien sin esto) · 🟡 nice-to-have. El workspace usa **`EntitySubNavBar`** (patrón staff) — **5 leaves** (★ Chris 2026-06-07 #4: se quitó **Stats** — esto es configuración, no analítica), cada uno es una hoja con secciones (cards), sin Shadcn tabs.

### Pestaña 1 · **Resumen** — "qué es y qué se lleva el paciente" (★ Chris #5 renombrada · ★ 2026-06-12 reagrupada + ficha de paciente completa — RATIFICADO)
- **Identidad:** 🔴 nombre · ★ chip **"Servicio estándar: {canónico}" / "Personalizado"** (read-only + tooltip RN-23 · § Biblioteca) · 🔴 **categoría/especialidad** (heredada+🔒 si estándar; editable de las áreas de la clínica si personalizado · RN-30) · 🔴 **peldaño** (`value_level`) = **5 botones fijos** (heredado+🔒 si estándar; editable si personalizado · RN-30) — ★ Chris #8: el badge vive **aquí**, no en el header. (★ 2026-06-15: el flag "recurrente" se movió a **Modalidad** · RN-28.)
- **Qué es:** 🔴 descripción corta (lenguaje paciente, **voz de marca**) · 🟡 descripción larga · 🔴 **qué incluye** (lista) · 🟡 qué NO incluye (exclusiones) · 🟡 **variantes estructuradas** `{nombre · precio · qué cambia}` (RN-29) · 🟡 garantía
- **★ El procedimiento (NEW 2026-06-12 · paciente-facing):** 🔴 **cómo se hace** (pasos numerados, lenguaje paciente) · 🟡 **anestesia / manejo del dolor** · 🔴 duración: sesión única **o** paquete (N sesiones + min c/u) · 🟡 tiempo total del tratamiento · 🟡 preparación previa · 🟡 cuidados posteriores · 🟡 tiempo de recuperación/downtime
- **Resultados:** 🔴 resultado esperado · 🔴 duración del resultado (vida útil) · 🟡 tiempo a ver resultados · 🟡 sesiones requeridas · 🟡 expectativas realistas (qué NO esperar)
- **★ Riesgos (NEW 2026-06-12 · paciente-facing · capa curada):** 🔴 **riesgos y efectos secundarios** (lista) · 🟡 **señales de alarma post-tratamiento** ("si pasa X, contacta a la clínica"). Adrián los cita textual; interpretación clínica libre escala al doctor (RN-22/RN-26).
- **★ Modalidad y agenda (★ Chris 2026-06-15 · renombrado de "Operación"):** 🔴 **modalidad** {sesión única · por sesiones · recurrente} (RN-28; `por sesiones` → nº de sesiones + intervalo; `recurrente` → cadencia · campos numéricos+unidad RN-31) · 🔴 **duración de la cita inicial** (number + min) · 🔴 **tipo de cita inicial** (RichSelect · enum fijo · RN-32)

### Pestaña 2 · **Para Adrián** (Argumentario) ⭐ — "el brief de venta del agente" (TAB NUEVO)
> El research es contundente: ~95% del cierre vive aquí (candidatura + consecuencia de no tratarse + objeciones + match), no en la ficha técnica. Es el diferencial.
- **Candidatura & seguridad:** 🔴 candidato ideal · 🔴 **contraindicaciones / quién NO es candidato** · 🔴 preguntas de calificación (descubrimiento) · 🔴 requiere evaluación previa (sí/no) · 🔴 **condiciones de escalada a humano** (dolor/diagnóstico/medicación → no lo maneja el agente · HIPAA-lite) · 🟡 requisitos previos · 🟡 restricciones (edad/embarazo)
- **Argumentario:** 🔴 beneficios emocionales (vender el resultado) · 🔴 dolor de no tratarse (urgencia) · 🔴 diferenciadores (por qué esta clínica) · 🟡 comparativa con alternativas · 🟡 ganchos promocionales vigentes
- 🔴 **FAQ** — pares pregunta→respuesta editables (¿duele? ¿cuánto dura? ¿cuántas sesiones? ¿se ve natural? ¿soy candidato?)
- 🔴 **Objeciones→respuestas** — pares para las 5 universales (precio · miedo · tiempo · "lo voy a pensar" · confianza)
- **Para el match (RN-16):** 🔴 **palabras clave/sinónimos** (cómo el paciente lo nombra: "carillas", "fundas", "arreglarme los dientes") · 🟡 intenciones disparadoras · 🟡 problemas que resuelve · 🟡 lenguaje a evitar (jerga que asusta)

### Pestaña 3 · **Especialistas** (★ Chris round 3 · renombrada de "Doctores" — más fiel a centros estéticos/no-médicos · #6/#7 · cómo funciona el vínculo)
> **★ Nota cross-story:** "Especialistas" es el **label canónico user-facing**. La **sub-tab roster `Lisa → Doctores`** y la story `lisa-doctores` deberían adoptar el mismo label para consistencia → **cross-story, escalar `/pm-vitalia`** (la tabla `vitalia_doctors` y la ruta pueden quedar igual en código; solo cambia el label).
- 🔴 **especialistas habilitados** (link servicio↔especialista · cimiento canal-inbound RN-17). Lista de los vinculados (avatar + nombre + especialidad).
- 🔴 **Vincular especialista** = NO crea uno: abre un **selector del roster de la clínica** (los que ya existen en el roster · buscador + checkboxes); marcar = "este especialista realiza este servicio". El roster es la SSoT (`vitalia_doctors` de `lisa-doctores`); si falta → link "Agrégalo en Lisa → Especialistas ↗".
- 🔴 **"Ver detalle ↗"** por especialista vinculado → **deep-link a su ficha exacta en el roster de Lisa** (ruta code `/{tenantId}/lisa/doctores/[id]`, label "Especialistas"). Botón **Desvincular** (no borra al especialista del roster).
- 🟡 credenciales relevantes que el agente puede citar · 🟡 sedes donde se ofrece

### Pestaña 4 · **Plan de pago** (★ Chris #2/#3 · son **3 cobros distintos**, no mezclar)
> Tres conceptos separados porque significan cosas distintas y el research marcó que confundirlos es el error #1. Cada uno es opcional por servicio.
- **1 · Precio del tratamiento:** 🔴 precio o rango + moneda (`tenant_locale`) · 🔴 **precio publicable** (¿el agente lo dice en chat o agenda valoración?).
- **2 · Reserva de la cita (la "seña"):** 🔴 monto chico para **apartar el turno** (reserva prepagada Vitalia · reduce inasistencias) — monto **fijo o %** · **se descuenta del total** · flag pide/no-pide. (Esto es lo que en el catálogo se veía como "seña X%" y confundía → ahora se crea y se explica **aquí**.)
- **3 · Anticipo para iniciar (★ Chris #3 · faltaba):** 🔴 pago inicial **sobre el costo del tratamiento** que el paciente da para **empezar** (aparte de la reserva) — **% o monto del total** · flag ofrece/no · ≈equivalente calculado. Clave en implantes, ortodoncia y cirugía.
- **4 · Financiamiento del saldo:** 🔴 ofrece cuotas (sí/no) · N cuotas · interés/MSI · **≈ por mes** calculado · 🟡 socio financiero · 🟡 medios de pago.

### Pestaña 5 · **Prueba social** (renombra "Reseñas")
- 🔴 **casos antes/después** — **carga manual** (foto antes + foto después + **consentimiento firmado** del paciente · HIPAA-lite · RN-33) · 🔴 **testimonios** — **carga manual** `{★ rating · texto · autor · origen}` con agregar/quitar (RN-33) · 🟡 prueba de volumen ("+300 sonrisas"). NO se auto-derivan de reseñas en esta story (integración Camila/NPS = futura).

> ★ Chris #4 (2026-06-07): la pestaña **Stats** se eliminó — esta superficie es **configuración** del catálogo, no analítica. Las métricas del servicio (leads · % cierre Adrián · sesiones/mes · revenue · LTV) viven donde corresponde el reporting, **no** en la ficha de configuración (futura story de analítica/Stats, si se decide).

> **MVP del registro (★ 2026-06-12: 24 → 26 campos 🔴 mínimos para que Adrián venda):** nombre · categoría · descripción corta · qué incluye · **cómo se hace** ★ · **riesgos y efectos secundarios** ★ · candidato ideal · contraindicaciones · preguntas de calificación · requiere evaluación · condiciones de escalada · beneficios emocionales · dolor de no tratarse · diferenciadores · FAQ · objeciones→respuestas · resultado esperado · duración del resultado · precio/rango · precio publicable · reserva (seña) · financiamiento (cuotas) · fotos antes/después · doctores habilitados · duración de cita · palabras clave/sinónimos. (El **anticipo para iniciar** es must-have **en los servicios que lo usan** — implantes/ortodoncia/cirugía.) Completar la ficha **NUNCA bloquea** "Activo" — indicador de completitud en el workspace ("ficha 22/26 · faltan: …") · decisión Chris 2026-06-12 #3.
>
> **Decisión de implementación (a confirmar /architect):** `FAQ` + `objeciones→respuestas` = listas de pares editables (alimentan limpio el KB del agente), NO texto libre. `contraindicaciones` + `condiciones_escalada` son campos de **seguridad** (HIPAA-lite), no solo venta.

## § Mapa funcional (RONDA 1 · resuelto)

> Capa humana que Chris valida. El Gherkin (RONDA 2) lo formaliza. Profundidad alta (story keystone).

### Happy path (camino dorado)

1. La dueña entra a **Lisa → Servicios**. Catálogo vacío → **empty-state que invita a agregar desde la biblioteca estándar** (★ 2026-06-12: el seed ES la biblioteca — absorbe los "seed presets"); con datos → **vista Catálogo** (grid de tarjetas) con **buscador + filtros** (patrón staff).
2. Crea un servicio (**+ Nuevo servicio**) → **★ paso picker de la biblioteca** (2026-06-12 · typeahead por nombre canónico **y sinónimos**, scoped al tipo de clínica del tenant):
   - **(a) Plantilla encontrada** → "Usar esta plantilla" → workspace **PRE-LLENADO** ✨ (descripción, cómo se hace, riesgos, FAQ, sinónimos — todo editable, origen "biblioteca") → la dueña completa **lo suyo**: precio, duración real, especialistas, cobros. Tipeo mínimo.
   - **(b) No está** → "Crear servicio personalizado" → **workspace vacío** (mismo que editar, NO Sheet · ★ Chris #1) → **arranque por documento** (folleto/precios/protocolo → **"Procesar con Lisa"** → campos autocompletados, editables) **o a mano** (Lisa redacta la descripción en **voz de marca**; peldaño con selector autoexplicativo).
   - Todo servicio guarda `canonical_service_ref` (null si personalizado) → nombres estándar + reportes comparables + Adrián entiende el servicio aunque cambien el display-name.
3. **Activa** el servicio (toggle único "Activo" → Adrián lo conoce + vende).
4. Vista **Escalera de valor**: servicios distribuidos en los 5 peldaños con **labels médicos** (Gancho gratuito · Primera visita · Tratamiento principal · Premium · Plan/convenio). **Arrastra** una tarjeta a otro peldaño; ajusta `pricing_override` + `cta_copy` del peldaño en un drawer.
5. **Workspace del servicio** (`[offer-id]`, patrón staff `EntitySubNavBar`): 5 leaves Resumen · **Para Adrián** · Especialistas · Plan de pago · Prueba social (contenido en § Workspace del servicio).
6. **Resultado:** servicio activo → conocimiento de **Adrián** (lo cita + argumentario; con doctores → match especialista), **Propuestas** (line-item + financiamiento), **Mateo** (duración).

### Bifurcaciones (árbol — Chris valida COMPLETITUD)

```
Entrar a Lisa → Servicios
├─ catálogo vacío
│   ├─ agrega desde la biblioteca estándar (seed = biblioteca · 2026-06-12) ─ [SC happy-seed]
│   └─ crea servicio → ★ picker biblioteca (typeahead nombre+sinónimos)
│       ├─ plantilla encontrada → workspace PRE-LLENADO ✨ ───────────  [SC happy-plantilla] ★
│       └─ no está → "Crear personalizado" → workspace VACÍO (· #1)
│           ├─ lo llena a mano ───────────────────────────────────────  [SC happy-create]
│           └─ carga documento → "Procesar con Lisa" → autocompleta ──  [SC happy-doc-autocomplete] ★
└─ catálogo con datos
    ├─ vista Catálogo (grid)
    │   ├─ crear/editar servicio
    │   │   ├─ precio fijo ───────────────────────────────────────────  [SC happy-create]
    │   │   ├─ precio rango "desde $X" ───────────────────────────────  [SC edge-rango]
    │   │   ├─ paquete / multi-sesión ────────────────────────────────  [SC edge-paquete]
    │   │   └─ servicio recurrente (flag + frecuencia) ───────────────  [SC edge-recurrente]
    │   ├─ buscar por nombre + filtro especialidad/activo ────────────  [SC happy-search]
    │   ├─ editar (admin/owner) vs read-only (doctor/staff) ──────────  [SC adversarial-rbac]
    │   ├─ eliminar servicio (soft-delete) ───────────────────────────  [SC edge-delete]
    │   └─ toggle único "Activo" (agente lo conoce) ──────────────────  [SC happy-activar]
    └─ vista Escalera (5 peldaños FIJOS · autoexplicativa)
        ├─ peldaño con servicios → muestra las tarjetas + "crear aquí" ─  [SC happy-rung-filled]
        ├─ peldaño VACÍO → muestra qué va ahí + ejemplos por vertical ──  [SC happy-rung-empty-guidance] ★
        ├─ drag servicio de peldaño A → B (cambia value_level) ────────  [SC edge-move-rung]
        └─ keyboard-only mover peldaño (a11y) ────────────────────────  [SC a11y-keyboard]

Cross-cutting:
├─ servicio activo SIN doctores → UI avisa + agente degrada (responde, no matchea) ── [SC edge-sin-doctor]
├─ servicio activo CON doctores → entra al conocimiento de Adrián ─────────────────── [SC happy-agente]  ★ KEYSTONE
└─ query cross-tenant bloqueada ──────────────────────────────────────────────────── [SC adversarial-tenant]
```

### Reglas de negocio (RN — resueltas)

- **RN-1** · Un servicio = una **Offer** de Offer Studio (consume engine EP-2; NO modelo `Treatment`/`LadderSlot` nuevo).
- **RN-2** · El peldaño = `OfferValueLevel` del engine (5 rungs canónicos) con **labels médicos** de display. NO se inventan peldaños.
- **RN-3** · Precio nunca hardcoded; moneda `tenant_locale`; soporta **fijo o rango** ("desde $X").
- **RN-4** · Soporta **paquete/multi-sesión** (`total_sessions_count`).
- **RN-5 (★ superseded by RN-28 · 2026-06-15)** · La recurrencia dejó de ser un flag binario: ahora es un valor de la **Modalidad** (`recurrente`) — ver RN-28. Sigue siendo atributo del servicio (aplicable en cualquier peldaño), NO un peldaño.
- **RN-6** · El servicio tiene **3 cobros distintos e independientes** (config en Lisa · cada uno opcional): **(a) reserva/seña** para apartar la cita (se descuenta del total) · **(b) anticipo** para iniciar el tratamiento (% o monto del total, aparte de la reserva) · **(c) financiamiento** del saldo en cuotas. Adrián/Propuestas los consumen. NO confundir reserva con anticipo.
- **RN-7** · Edición (crear/precio/activar) = **`admin_clinic` + `owner`**; `doctor` + `nurse` + `staff` = read-only.
- **RN-8** · La descripción default se genera en **voz de marca** (lisa-marca); editable.
- **RN-9** · Link servicio↔doctor **opcional** (N doctores); sin doctores la UI avisa + el agente degrada. Con doctores → match canal-inbound RN-17.
- **RN-10** · **Un toggle "Activo"** (el agente lo conoce + vende). El toggle "landing" se eliminó de esta story (la landing pública es `lisa-landing-public`, otra historia).
- **RN-15** · El catálogo tiene **buscador + filtros** (mismo patrón que staff: buscar por nombre + filtro especialidad + filtro activo).
- **RN-11** · Precio del servicio ≥ 0 (Zod + backend). Los peldaños son FIJOS — el peldaño es el `value_level` del servicio, sin precio propio ni override.
- **RN-12** · Catálogo **por-tenant**, scope clínica **opcional** por servicio (null = todas). Tenant-isolation siempre.
- **RN-13** · El catálogo **NO es PHI** (info comercial) → tenant-isolation raíz, sin dual-filter PHI.
- **RN-14** · Spanish neutro LatAm en toda la UI.
- **RN-16 (★ Chris #1 · refinada 2026-06-12)** · **Crear servicio = EL MISMO workspace que editar** (mismo componente, misma estructura de grupos/leaves — las únicas diferencias: campos vacíos/pre-llenados, chip Borrador, completitud baja). NO un form/Sheet/popup separado. El "+ Nuevo servicio" navega a la hoja "Nuevo servicio" cuya **primera vista es el picker de la biblioteca INLINE** (contenido de la hoja, NO modal); el **borrador recién se crea al elegir** plantilla o "Crear personalizado" (sin borradores fantasma) y ahí aparece el workspace.
- **RN-17 (★ Chris #1 + #9-B)** · **Documento → doble uso:** la dueña carga material (PDF/DOCX/imagen/enlace) y al procesarlo Lisa **(a) autocompleta los campos por extracción** (one-shot, editable, revisado) **y (b) lo indexa como conocimiento consultable por Adrián** (RAG, con el scope/safety de RN-22). Reusa la entidad engine `KnowledgeSource` (per-offer) + el extractor copilot. La dueña controla por fuente si "Adrián la consulta" (RAG on/off).
- **RN-18 (★ Chris #2 · política UI)** · Todo campo **no obvio o pesado** lleva **tooltip** explicativo (subrayado punteado + ⓘ, detalle al hover — como en el cockpit). No aplica a campos triviales (nombre, etc.).
- **RN-19 (★ Chris #3 · vertical)** · La **estructura** del catálogo es **idéntica** para clínica dental vs estética (un servicio es un servicio). La diferenciación es por **contenido/data**, derivado de la **especialidad del tenant** (ver § Diferenciación por vertical para el mecanismo). NO se forkea la UI por vertical.
- **RN-20 (★ Chris · política UX autoguardado)** · **Nunca hay botón "Guardar".** Todo cambio **autoguarda** (on-change, debounce). La UI muestra un indicador "💾 guardado" + "última edición". Vincular especialista, togglear activo, editar un campo → se persisten solos. (Excepción semántica: "Activar" es un toggle de estado, no un guardar; "Descartar borrador" elimina.)
- **RN-21 (★ Chris · modelo de conocimiento)** · Crear y editar son **el mismo workspace**. Lleva un panel **"Fuentes & conocimiento"** **persistente y colapsable** (no un paso de onboarding que desaparece): la dueña carga material UNA vez y Lisa **(a)** autocompleta los campos (extracción · editable · marcado con ✨ + fuente) y **(b)** lo deja como **conocimiento consultable por Adrián** (RAG). Reduce el llenado manual — el sistema agéntico hace el trabajo pesado. Ver § Modelo de conocimiento.
- **RN-22 (★ Chris #9-B · RAG en scope · safety)** · El conocimiento que Adrián consulta por RAG se limita a **contenido comercial**; **NO** responde libre sobre lo clínico (contraindicaciones/diagnóstico/medicación → **escala al doctor**). El **precio** SIEMPRE sale del **campo estructurado**, nunca del documento (anti-staleness). Ingesta con **scrub PHI** (HIPAA-lite). Los campos curados (precio, contraindicaciones, candidatura) son la capa de alta precisión; el RAG es el complemento para preguntas libres de cola larga.
- **RN-23 (★ Chris round 3 · política de edición)** · **Todo campo se edita en su vista** (autosave). Excepciones, ambas señalizadas: **(a) dato de otra superficie** → read-only aquí + **tooltip que dice dónde se edita** (ej. moneda → config · datos del especialista → Lisa → Especialistas · opciones de especialidad → tipo de clínica · voz → Lisa → Marca); **(b) calculado** → read-only + tooltip "se calcula solo". Sin tooltip de origen un campo read-only es un bug de UX. (Auditoría completa en § Auditoría de campos.)
- **RN-24 (★ Chris round 3 · placeholders por tipo)** · Los **placeholders, ejemplos y sugerencias** de las vistas se **orientan al tipo de clínica** (dental → "Ej: Diseño de sonrisa" · estética → "Ej: Botox preventivo"; opciones de especialidad, ejemplos del rung-picker, redacción de Lisa). El tipo viene del atributo de clínica (Onboarding/Marca · story `vitalia-fase2-marca-especialidad-clinica`). NO cambia la estructura (RN-19), solo el contenido de ayuda.
- **RN-25 (★ Chris 2026-06-12 · estandarización)** · Crear servicio arranca en el **picker de la biblioteca estándar** (typeahead nombre+sinónimos, scoped al tipo de clínica). Servicio desde plantilla guarda `canonical_service_ref`; personalizado permitido siempre (la biblioteca ayuda, no bloquea). La biblioteca = data del preset pack EP-2 (Offer Studio), read-only para tenants.
- **RN-26 (★ Chris 2026-06-12 · ficha de paciente completa)** · El servicio publica info completa paciente-facing: **cómo se hace** · **riesgos y efectos secundarios** · preparación · cuidados · downtime · resultados. Pre-llenada desde la plantilla cuando existe; siempre editable. Riesgos = **capa curada**: Adrián los cita textual, no interpreta (extiende RN-22). Completar la ficha NUNCA bloquea "Activo" — indicador de completitud ("ficha 22/26 · faltan: …").
- **RN-27 (★ Chris 2026-06-12 · personalizado → candidatura)** · Servicio personalizado queda **solo en la clínica**. Flag interno "candidato a biblioteca" para curaduría central periódica — NO entra automático a la biblioteca global (calidad > volumen).
- **RN-28 (★ Chris 2026-06-15 · modalidad de servicio)** · Todo servicio declara una **Modalidad** ∈ {**sesión única**, **por sesiones**, **recurrente**} (reemplaza el flag "¿Recurrente?" — no se entendía · research Zenoti/Pabau/Fresha). `por sesiones` revela **nº de sesiones + intervalo**; `recurrente` revela la **cadencia**. La plantilla la **sugiere** (✨ editable). Vive en el grupo **"Modalidad y agenda"** del Resumen (renombrado de "Operación" — sonaba quirúrgico). `por sesiones` → el paquete se vende junto (Adrián lo ofrece como un tratamiento, Mateo agenda las sesiones); `recurrente` → Camila reactiva al tocar repetir.
- **RN-29 (★ Chris 2026-06-15 · variantes estructuradas)** · Las **Variantes** son opciones del **mismo** servicio que cambian el precio (NO servicios separados, NO texto libre): lista de `{nombre · precio · qué cambia}`. Comparten la ficha clínica; Adrián cotiza la variante exacta ("en porcelana te queda S/ 4.500"). Sin variantes → vale el precio del tratamiento. (Research: "service variants" de Zenoti/Pabau/Fresha — material/duración/zonas/unidades.)
- **RN-30 (★ Chris 2026-06-15 · herencia bloqueada desde plantilla)** · Servicio creado desde la biblioteca **hereda categoría + peldaño** y quedan **BLOQUEADOS** (no editables · 🔒 + tooltip "lo define el servicio estándar") — un servicio estándar no se re-categoriza. Solo el **personalizado** los pide: peldaño = los **5 botones fijos**; categoría = de las **áreas de la clínica**. (Corrige la versión previa "heredados editables".) La **Modalidad** SÍ es editable aun desde plantilla (la clínica ajusta sesiones/cadencia/precio).
- **RN-31 (★ Chris 2026-06-15 · datos numéricos tipados)** · Los campos de cantidad/tiempo son **numéricos tipados**, no texto libre: nº de sesiones (number), duración de sesión / duración de cita (number + "min"), intervalo y cadencia (number + **unidad** días/semanas/meses/años). Habilita cálculo, validación y que Mateo agende con el dato real.
- **RN-32 (★ Chris 2026-06-15 · "Tipo de cita inicial" = enum fijo + dropdown enriquecido)** · "Tipo de cita inicial" es un **enum fijo del sistema** (3: valoración+diagnóstico · primera sesión directa · consulta informativa gratuita) — **NO configurable por clínica**; lo consume la agenda (Mateo/Valeria). Se renderiza con un **RichSelect** (Select con **descripción por opción** · candidato CORE `@luana/ui-kit`). Inventario de selects de la story: **~7 enums fijos del sistema** (peldaño 5 · modalidad 3 · tipo-cita 3 · precio-modo 2 · reserva-tipo 2 · anticipo-unidad 2 · interés 2); **el único configurable por clínica es "Especialidad/categoría"** (áreas Onboarding/Marca).
- **RN-33 (★ Chris 2026-06-15 · prueba social = carga manual)** · Casos antes/después y **testimonios** son **carga manual** de Lisa en la pestaña Prueba social (testimonio = `{rating · texto · autor · origen}`; caso = foto antes + foto después + **consentimiento firmado** del paciente · HIPAA-lite). NO se derivan automáticamente de reseñas/NPS en esta story (esa integración con Camila = story futura).

### Criterios de aceptación (AC — feature-done)

- **AC-1** · Toggle Catálogo|Escalera persiste en URL (`?view=`).
- **AC-2** · CRUD de servicios con los campos del § Modelo (fijo/rango, paquete, recurrente, **reserva/seña + anticipo + financiamiento (3 cobros distintos)**, doctores, peldaño, toggle único Activo).
- **AC-3** · Escalera: 5 peldaños FIJOS; servicios ubicados por su `value_level`; drag mueve de peldaño; **peldaño vacío muestra qué va ahí + ejemplos por vertical + "crear aquí"** (autoexplicativo). SIN workspace de peldaño ni override.
- **AC-4** · Workspace de servicio = patrón **staff** (`EntitySubNavBar`, NO Shadcn tabs): **5 leaves** Resumen · **Para Adrián** · Especialistas · Plan de pago · Prueba social (★ sin Stats); back vuelve a Servicios. El badge del peldaño vive en **Resumen**, no en el header. Contenido por leaf = § Workspace del servicio.
- **AC-4.bis** · Leaf **"Para Adrián"** entrega el argumentario must-have: candidatura + contraindicaciones + condiciones de escalada + FAQ (pares) + objeciones→respuestas (5) + diferenciadores + palabras clave/sinónimos.
- **AC-9** · Crear servicio = **"+ Nuevo servicio" navega a la hoja cuya primera vista es el ★ picker de la biblioteca INLINE** (2026-06-12 · NO modal/popup — contenido de la hoja; en ese estado la franja muestra solo "‹ Servicios" + título, SIN leaves porque el workspace aún no existe): plantilla encontrada → **el borrador se crea** → workspace **PRE-LLENADO** ✨ con `canonical_service_ref`; no está → "Crear personalizado" → **el borrador se crea** → workspace VACÍO. El workspace de crear es **ESTRUCTURALMENTE IDÉNTICO** al de editar (mismos leaves + grupos · RN-16) + selector de peldaño autoexplicativo + Lisa redacta la descripción en voz de marca.
- **AC-18 (★ 2026-06-12)** · **Picker de la biblioteca (vista inline):** typeahead busca por nombre canónico **y sinónimos** ("fundas" encuentra "Carillas"), scoped al tipo de clínica; resultado muestra nombre + categoría + peldaño sugerido; "Usar esta plantilla" pre-llena ✨ los campos de contenido (NO precio/duración/especialistas — esos son de la clínica); fallback "Crear personalizado" siempre visible; "↻ Volver a elegir de la biblioteca" disponible desde el workspace borrador.
- **AC-19 (★ 2026-06-12)** · **Indicador de completitud** en el workspace ("ficha 22/26 · faltan: riesgos, cómo se hace") — informativo, NUNCA bloquea "Activo". Los 26 must-have del § MVP son el denominador.
- **AC-11** · **Documento → autocompletar:** en el workspace (sobre todo vacío) la dueña carga un documento + **"Procesar con Lisa"** → los campos se **pre-llenan** y quedan **editables** (los revisa antes de guardar). El documento se usa para extracción, **no** se indexa a RAG runtime.
- **AC-12** · **Tooltips** en los campos no obvios/pesados (peldaño, contraindicaciones, escalada, anticipo, reserva, palabras clave): subrayado punteado + detalle al hover.
- **AC-13** · **Autoguardado** en todo el workspace (sin botón "Guardar"): editar un campo, vincular especialista, togglear activo → persisten solos (debounce) + indicador "💾 guardado". "Descartar borrador" elimina; "Activar" es toggle de estado.
- **AC-14** · **Panel "Fuentes & conocimiento" persistente + colapsable** (crear y editar): cargar material → "Procesar con Lisa" → **(a)** campos pre-llenados marcados ✨+fuente (editables) **y (b)** fuentes indexadas para RAG con toggle "Adrián consulta" por fuente + estado (extraído/indexado).
- **AC-15** · **RAG con guardas (RN-22):** verificable que Adrián responde de fuentes **comerciales**; lo clínico **escala al doctor**; el **precio** sale del campo, no del documento; ingesta con scrub PHI. **A + B en esta story** (engine-lift = dependencia hard · § Modelo de conocimiento).
- **AC-16** · **Política de edición (RN-23):** cada campo se edita en su vista; los read-only (moneda, datos del especialista, opciones de especialidad, voz, calculados) muestran **tooltip que dice dónde se editan / que se calculan**. (Auditoría: § Auditoría de campos.)
- **AC-17** · **Placeholders por tipo de clínica (RN-24):** los placeholders/ejemplos/opciones se orientan al tipo (dental/estética) sin cambiar la estructura; el tipo viene del atributo de clínica.
- **AC-10** · Catálogo con **buscador + filtros** (nombre + especialidad + activo), patrón staff.
- **AC-5** · Link servicio↔especialista: **Vincular especialista** abre un selector del **roster** (`lisa-doctores`, NO crea especialistas) con buscador + checkboxes; el link **autoguarda** al marcar (sin botón Guardar · RN-20) y es consultable (cimiento canal-inbound RN-17). Cada especialista vinculado tiene **"Ver detalle ↗"** que deep-linkea a su ficha en **Lisa → Especialistas** + **Desvincular** (no borra al especialista del roster).
- **AC-6** · **KEYSTONE:** un servicio activo aparece en el conocimiento del agente (verificable live: `TenantKnowledgeBuilder` lo inyecta / Adrián lo cita).
- **AC-7** · Empty-state invita a **agregar desde la biblioteca estándar** (★ 2026-06-12: el seed ES la biblioteca — dental + estética Tier 1, contenido generado por Lisa + curado).
- **AC-8** · RBAC (admin/owner editan, resto read-only) + cross-tenant bloqueado + a11y (keyboard drag + axe).

---

## § Gherkin — casuística completa (RONDA 2 · ★ Chris 2026-06-15 "todos los escenarios posibles · que no haya huecos al desarrollar")

> Cada scenario lleva tags `@categoría` (`@happy`/`@negative`/`@edge`/`@adversarial`/`@a11y`/`@keystone`) + `@RN-N` (regla que verifica) + `@SC-id` (bifurcación del § Mapa funcional). La **Matriz de cobertura** (abajo) garantiza que **cada RN-1..33 y cada bifurcación** tiene ≥1 scenario, y lista lo deliberadamente fuera de scope (cero hueco silencioso). Keywords en inglés (convención ejecutable); contenido en español neutro.

```gherkin
Background:
  Given estoy autenticada como "admin_clinic" del tenant "Sonrisa Plena"
  And estoy en Lisa → Servicios
```

### 1 · Catálogo (lista · búsqueda · filtros · RBAC · borrado)

```gherkin
@happy @RN-25 @AC-7 @SC-happy-seed
Scenario: Catálogo vacío invita a la biblioteca
  Given el catálogo no tiene servicios
  Then veo un empty-state que invita a "agregar desde la biblioteca estándar"
  And NO veo una grilla vacía sin guía

@happy @RN-15 @AC-10 @SC-happy-search
Scenario: Buscar y filtrar el catálogo
  Given hay 12 servicios
  When busco "carillas" y filtro especialidad="Estética dental" y estado="Activo"
  Then la grilla muestra solo los servicios que matchean nombre/sinónimo + filtros
  And puedo filtrar por origen "Estándar"/"Personalizado"

@happy @RN-10 @RN-20 @AC-2 @SC-happy-activar
Scenario: Activar un servicio desde la card
  When toggleo "Activo" en la card de "Diseño de sonrisa"
  Then el estado persiste solo (autosave · sin botón Guardar)
  And el servicio entra al conocimiento de Adrián (ver @keystone)

@adversarial @RN-7 @AC-8 @SC-adversarial-rbac
Scenario: Rol sin permiso ve el catálogo read-only
  Given estoy autenticada como "doctor"
  Then NO veo "+ Nuevo servicio" ni toggles editables
  And cualquier intento de editar precio responde 403

@edge @SC-edge-delete
Scenario: Eliminar un servicio es soft-delete
  When elimino "Botox facial"
  Then desaparece de la lista
  And queda con deleted_at (recuperable · no hard-delete)

@edge @RN-15
Scenario: Catálogo grande no carga todo al cliente
  Given hay 300 servicios
  Then la grilla pagina con cursor (EntityInfoCard · canon §2.4)
  And el buscador consulta server-side (no filtra en memoria toda la colección)
```

### 2 · Crear servicio (picker biblioteca inline · plantilla · personalizado · borrador)

```gherkin
@happy @RN-16 @RN-25 @AC-9 @AC-18 @SC-happy-plantilla
Scenario: Crear desde plantilla de la biblioteca
  When hago "+ Nuevo servicio"
  Then la primera vista de la hoja es el picker de la biblioteca INLINE (no modal/popup)
  And la franja muestra solo "‹ Servicios" + título (sin leaves: el borrador aún no existe)
  When elijo la plantilla "Diseño de sonrisa"
  Then se crea el borrador y aparece el workspace PRE-LLENADO con ✨
  And el chip de origen dice "Estándar" y se guarda canonical_service_ref

@edge @RN-25 @AC-18
Scenario: Typeahead encuentra por sinónimo
  When en el picker escribo "fundas"
  Then aparece "Carillas de porcelana" (match por sinónimo, no solo nombre canónico)

@happy @RN-16 @SC-happy-create
Scenario: Crear servicio personalizado
  When en el picker hago "Crear servicio personalizado"
  Then se crea el borrador y aparece el workspace VACÍO
  And el chip de origen dice "Personalizado" y canonical_service_ref es null

@negative @RN-16
Scenario: Salir del picker sin elegir no crea borradores fantasma
  Given estoy en la vista picker
  When vuelvo a "‹ Servicios" sin elegir plantilla ni personalizado
  Then NO se creó ningún servicio borrador

@edge @RN-16
Scenario: Volver a elegir de la biblioteca
  Given creé un borrador desde una plantilla
  When hago "↻ Volver a elegir de la biblioteca"
  Then regreso al picker

@edge @RN-16
Scenario: Crear y editar son el MISMO workspace
  Then el workspace de crear tiene los mismos 5 leaves y los mismos 6 grupos de Resumen que el de editar
  And las únicas diferencias son: campos vacíos/✨, chip Borrador, completitud baja
```

### 3 · Resumen · Identidad + herencia bloqueada (RN-30)

```gherkin
@happy @RN-30
Scenario: Servicio estándar hereda categoría y peldaño BLOQUEADOS
  Given el servicio viene de la plantilla "Diseño de sonrisa"
  Then "Especialidad/categoría" = "Estética dental" en un Select disabled con 🔒
  And "Peldaño" muestra los 5 botones con "Tratamiento principal" marcado y los demás no clickeables
  And ambos labels tienen tooltip "lo define el servicio estándar"

@happy @RN-30
Scenario: Servicio personalizado pide categoría y peldaño
  Given el servicio es personalizado
  Then "Peldaño" = 5 botones clickeables (sin 🔒)
  And "Especialidad/categoría" es editable con las áreas de la clínica

@adversarial @RN-30
Scenario: No se puede re-categorizar un servicio estándar
  Given el servicio es estándar (peldaño bloqueado)
  When intento clickear otro peldaño o cambiar la categoría
  Then no pasa nada (campo locked) — un servicio estándar no se re-categoriza

@happy @RN-23
Scenario: Chip de origen es read-only con tooltip
  Then el chip "Estándar: {canónico}" / "Personalizado" es read-only
  And su tooltip explica el vínculo a la biblioteca
```

### 4 · Resumen · Qué es + variantes (RN-8 · RN-29)

```gherkin
@happy @RN-8
Scenario: La descripción se redacta en voz de marca
  When dejo la descripción vacía y pido que Lisa la redacte
  Then se genera en la voz de marca (lisa-marca) y queda editable
  And el tono no es editable aquí (tooltip: se ajusta en Lisa → Marca)

@happy @RN-29
Scenario: Agregar una variante estructurada
  When hago "+ Agregar variante" y cargo {nombre:"Porcelana", precio:4500, nota:"premium"}
  Then aparece una fila nueva y autosave persiste la variante

@edge @RN-29
Scenario: Quitar una variante
  When quito la variante "Composite"
  Then la fila desaparece y autosave persiste

@edge @RN-29
Scenario: Servicio sin variantes usa el precio del tratamiento
  Given el servicio no tiene variantes
  Then Adrián cotiza el precio base del tratamiento

@happy @RN-29 @keystone
Scenario: Adrián cotiza la variante exacta
  Given el servicio tiene variantes Composite S/2.500 y Porcelana S/4.500
  When el paciente pregunta por porcelana
  Then Adrián responde "en porcelana te queda S/ 4.500"
```

### 5 · Resumen · Modalidad y agenda (RN-28 · RN-31 · RN-32)

```gherkin
@happy @RN-28
Scenario: Modalidad sesión única no pide campos extra
  When elijo modalidad "Sesión única"
  Then no se revela ningún campo adicional

@happy @RN-28 @RN-31 @SC-edge-paquete
Scenario: Modalidad por sesiones revela paquete
  When elijo modalidad "Por sesiones"
  Then se revelan "Número de sesiones" (numérico) y "Cada cuánto" (número + unidad)
  And el hint dice que el paquete se vende junto y Mateo agenda las sesiones

@happy @RN-28 @RN-31 @SC-edge-recurrente
Scenario: Modalidad recurrente revela cadencia
  When elijo modalidad "Recurrente"
  Then se revela "Se repite cada" (número + unidad: meses/semanas/años)
  And el hint dice que Camila lo usa para reactivar

@happy @RN-28
Scenario: La plantilla sugiere la modalidad (editable)
  Given creo desde la plantilla "Botox facial"
  Then la modalidad llega pre-seleccionada "Recurrente" con ✨ y es editable

@negative @RN-31
Scenario: Cantidad de sesiones inválida se rechaza
  When ingreso "0" o un texto en "Número de sesiones"
  Then se rechaza (validación numérica · min 1)

@happy @RN-32
Scenario: Tipo de cita inicial es un RichSelect con descripción por opción
  When abro "Tipo de cita inicial"
  Then cada opción muestra su descripción ("Primera cita para evaluar y planificar", etc.)
  When elijo "Consulta informativa gratuita"
  Then la selección persiste (autosave)

@happy @RN-31
Scenario: La duración de la cita es numérica en minutos
  Then "Duración de la cita inicial" es number + "min" y Mateo agenda con ese valor
```

### 6 · Resumen · ficha paciente (procedimiento · riesgos · RN-26)

```gherkin
@happy @RN-26
Scenario: La ficha paciente-facing está completa y editable
  Then veo "cómo se hace", "riesgos y efectos secundarios", preparación, cuidados, downtime, resultados
  And si vienen de plantilla están pre-llenados con ✨ y son editables

@happy @RN-22 @RN-26
Scenario: Los riesgos son capa curada que Adrián cita textual
  When el paciente pregunta por riesgos
  Then Adrián cita el campo "riesgos" textual y deriva al doctor para interpretación clínica
```

### 7 · Para Adrián (argumentario · FAQ · objeciones · keywords · safety)

```gherkin
@happy @AC-4.bis
Scenario: El argumentario must-have está completo
  Then la pestaña "Para Adrián" tiene candidato ideal, contraindicaciones, condiciones de escalada,
    preguntas de calificación, FAQ (pares), objeciones (5), diferenciadores y palabras clave

@happy
Scenario: FAQ y objeciones son pares editables
  When agrego un par {pregunta, respuesta} en FAQ
  Then alimenta limpio el KB del agente (no texto libre)

@happy @RN-16
Scenario: Palabras clave alimentan el match
  Given cargo sinónimos "carillas", "fundas", "arreglarme los dientes"
  Then el servicio matchea la intención del paciente aunque no diga el nombre clínico (data para canal-inbound)

@adversarial @RN-22
Scenario: Contraindicaciones y escalada frenan al agente
  Given el paciente es un no-candidato según contraindicaciones
  Then el agente NO le ofrece el servicio y deriva al doctor
  And ante dolor/diagnóstico/medicación escala a humano
```

### 8 · Especialistas (vincular · desvincular · sin doctores · RN-9 · AC-5)

```gherkin
@happy @RN-20 @AC-5
Scenario: Vincular especialista desde el roster
  When hago "+ Vincular especialista"
  Then se abre un selector del roster de la clínica (checklist + buscador)
  When marco "Dra. Carla López"
  Then el vínculo autosave persiste (sin botón Guardar)

@negative @AC-5
Scenario: Vincular no crea especialistas
  Then el panel aclara que elige del roster (Lisa → Especialistas), no crea especialistas
  And si falta uno, ofrece link "Agrégalo en Lisa → Especialistas ↗"

@edge @AC-5
Scenario: Ver detalle y desvincular
  When hago "Ver detalle ↗" de un especialista vinculado
  Then deep-linkea a su ficha en Lisa → Especialistas
  When hago "Desvincular"
  Then se quita el vínculo pero el especialista sigue en el roster

@edge @RN-9 @SC-edge-sin-doctor
Scenario: Servicio activo sin especialistas
  Given activo un servicio sin especialistas vinculados
  Then la UI avisa que falta vincular
  And el agente degrada: responde sobre el servicio pero no matchea especialista
```

### 9 · Plan de pago (3 cobros · calculados · publicable · RN-6 · RN-11)

```gherkin
@happy @RN-6
Scenario: Los 3 cobros son distintos e independientes
  Then "Reserva de la cita", "Anticipo para iniciar" y "Financiamiento del saldo" se configuran por separado
  And cada uno es opcional

@happy @RN-6
Scenario: Los montos derivados se calculan solos
  Given precio 4500, anticipo 30%, 6 cuotas
  Then "≈ equivale a" = S/ 1.350 (read-only, tooltip "se calcula solo")
  And "≈ por mes" = (precio − reserva − anticipo) ÷ cuotas (read-only)

@edge
Scenario: Precio no publicable agenda valoración
  When apago "Adrián puede decir el precio"
  Then el agente agenda una valoración en vez de dar el precio en el chat

@edge @SC-edge-rango
Scenario: Precio en modo rango
  When elijo modo "Rango"
  Then el precio se muestra como "desde S/ X"

@adversarial @RN-11
Scenario: Precio o monto negativo se rechaza
  When ingreso un precio -50
  Then Zod y el backend lo rechazan con "Precio debe ser >= 0"

@happy @RN-23
Scenario: La moneda es read-only con origen
  Then la moneda (S/) es read-only con tooltip "sale de la configuración de tu clínica"
```

### 10 · Prueba social (carga manual · consentimiento · RN-33)

```gherkin
@happy @RN-33
Scenario: Agregar un testimonio manual
  When hago "+ Agregar testimonio" y cargo {rating, texto, autor, origen}
  Then aparece la fila y autosave persiste

@edge @RN-33
Scenario: Quitar un testimonio
  When quito un testimonio
  Then la fila desaparece

@happy @RN-33
Scenario: Subir un caso antes/después requiere consentimiento
  When hago "+ Subir caso"
  Then me pide foto antes + foto después + confirmar el consentimiento firmado del paciente

@adversarial @RN-33
Scenario: Caso sin consentimiento se bloquea
  When intento guardar un caso sin confirmar el consentimiento
  Then se bloquea (HIPAA-lite)
```

### 11 · Escalera de valor (peldaños fijos · drag · a11y · RN-2 · AC-3)

```gherkin
@happy @SC-happy-rung-filled
Scenario: Peldaño con servicios
  Then cada peldaño con servicios muestra sus tarjetas + "crear aquí"

@happy @SC-happy-rung-empty-guidance
Scenario: Peldaño vacío guía
  Given un peldaño sin servicios
  Then muestra qué va ahí + ejemplos de la biblioteca + "crear aquí"

@edge @RN-2 @RN-20 @SC-edge-move-rung
Scenario: Mover un servicio entre peldaños
  When arrastro un servicio del peldaño "Premium" al "Tratamiento principal"
  Then cambia su value_level y autosave persiste

@adversarial @RN-30
Scenario: Mover un servicio estándar de peldaño
  Given un servicio estándar tiene su peldaño bloqueado
  Then el drag entre peldaños aplica solo a personalizados (o el peldaño del estándar es fijo) — decisión /architect

@a11y @SC-a11y-keyboard @AC-8
Scenario: Mover peldaño solo con teclado
  Given el foco está en una tarjeta de servicio
  When uso Space (seleccionar) → Arrow (recorrer peldaños) → Space (soltar)
  Then el cambio se aplica y un aria-live anuncia la transición
```

### 12 · Autoguardado (RN-20)

```gherkin
@happy @RN-20 @AC-13
Scenario: Todo autoguarda sin botón Guardar
  When edito cualquier campo del workspace
  Then se guarda solo (debounce) y veo UNA píldora flotante "Guardando…" → "Guardado"
  And no existe ningún botón "Guardar"

@edge @RN-20
Scenario: Acciones de estado vs autoguardado
  Then "Activar" es un toggle de estado y "Descartar borrador" elimina (no son "guardar")
```

### 13 · Tooltips + política de edición (RN-18 · RN-23)

```gherkin
@happy @RN-18 @AC-12
Scenario: Campos no obvios tienen tooltip
  Then peldaño, contraindicaciones, escalada, anticipo, reserva, palabras clave y modalidad muestran tooltip al hover
  And los campos triviales (nombre) no

@happy @RN-23 @AC-16
Scenario: Read-only de otra superficie dice dónde se edita
  Then moneda, voz, datos del especialista y opciones de especialidad son read-only con tooltip de origen
  And los calculados muestran tooltip "se calcula solo"
```

### 14 · Fuentes & conocimiento (autocompletar + RAG + guardas · RN-17/21/22)

```gherkin
@happy @RN-17 @AC-11 @AC-14 @SC-happy-doc-autocomplete
Scenario: Documento autocompleta los campos
  When cargo un folleto y hago "Procesar con Lisa"
  Then los campos se pre-llenan, marcados con ✨ + la fuente, y quedan editables (los reviso)

@happy @RN-17 @AC-14
Scenario: Documento queda como conocimiento de Adrián
  Then la fuente queda indexada para RAG con un toggle "Adrián consulta" por fuente y su estado (extraído/indexado)

@adversarial @RN-22 @AC-15
Scenario: El precio nunca sale del documento
  Given un folleto menciona un precio viejo
  Then Adrián cotiza desde el campo estructurado, no desde el documento

@adversarial @RN-22
Scenario: Pregunta clínica libre escala al doctor
  When el paciente pregunta algo clínico (contraindicación/diagnóstico)
  Then Adrián escala al doctor en vez de responder de RAG

@adversarial @RN-22
Scenario: Ingesta con scrub de PHI
  Given un documento trae datos de paciente
  Then la ingesta los sanitiza (HIPAA-lite) antes de indexar
```

### 15 · KEYSTONE — el agente conoce el catálogo (AC-6)

```gherkin
@keystone @happy @AC-6 @SC-happy-agente
Scenario: Servicio activo entra al conocimiento de Adrián
  Given un servicio activo con especialistas vinculados
  Then TenantKnowledgeBuilder lo inyecta en la identidad del agente
  And Adrián lo ofrece, lo cita y matchea al especialista (verificable LIVE)
```

### 16 · Adversarial transversal (tenant · RBAC · idioma · vertical)

```gherkin
@adversarial @RN-12 @RN-13 @SC-adversarial-tenant
Scenario: Query cross-tenant bloqueada
  Given existe el tenant "Otra Clínica"
  When intento leer un servicio de "Otra Clínica" desde "Sonrisa Plena"
  Then la query se bloquea (tenant-isolation) y no hay leak

@adversarial @RN-7
Scenario: Staff no puede editar precio
  Given soy "staff"
  When intento cambiar un precio
  Then responde 403 (read-only)

@happy @RN-14
Scenario: UI en español neutro LatAm
  Then todos los textos están en español neutro (sin voseo)

@happy @RN-19 @RN-24
Scenario: Misma estructura dental y estética
  Given el tenant es estético
  Then la estructura (5 leaves, mismos campos) es idéntica a la dental
  And solo cambian placeholders/ejemplos/opciones (orientados al tipo de clínica)
```

## § Matriz de cobertura (RN + bifurcación → scenario → verificación)

> Garantía anti-huecos: cada RN y cada bifurcación del árbol tiene ≥1 scenario. **Verificación** (qué prueba lo cierra · `definition-of-done-live-verify.md`): `unit` (Vitest/pytest) · `int` (integración BE) · `e2e` (Playlist real-backend) · `live` (ejercer la acción real en dev-app + leer logs) · `arch` (arch-fitness).

| RN | Qué garantiza | Scenarios | Verificación |
|---|---|---|---|
| RN-1 | servicio = Offer (engine EP-2) | §2 crear · §15 keystone | int + arch (no modelo nuevo) |
| RN-2 | peldaño = value_level (5 fijos) | §11 move-rung | unit + e2e |
| RN-3 | precio fijo/rango + moneda tenant | §9 rango · moneda | unit + e2e |
| RN-4 | paquete/multi-sesión | §5 por-sesiones | unit + e2e |
| RN-5→28 | recurrencia = modalidad | §5 recurrente | unit |
| RN-6 | 3 cobros distintos + calculados | §9 (3 cobros · derivados) | unit + e2e |
| RN-7 | RBAC admin/owner edita | §1 rbac · §16 staff | int + e2e |
| RN-8 | descripción en voz de marca | §4 voz | int (live keystone) |
| RN-9 | link doctor opcional + degradación | §8 sin-doctor | e2e + live |
| RN-10 | toggle único Activo | §1 activar | e2e |
| RN-11 | precio ≥ 0 | §9 negativo | unit (Zod) + int |
| RN-12/13 | tenant-isolation · no PHI | §16 cross-tenant | int + arch |
| RN-14 | español neutro | §16 idioma | arch (voseo) + e2e |
| RN-15 | buscador + filtros | §1 search | e2e |
| RN-16 | crear = editar · picker inline · borrador on-choose | §2 (plantilla/personalizado/fantasma/idéntico) | e2e + live |
| RN-17 | doc → autocompletar + RAG | §14 (a)(b) | int + live (engine-lift) |
| RN-18 | tooltips en no-obvios | §13 tooltip | e2e |
| RN-19/24 | misma estructura, contenido por vertical | §16 vertical | e2e |
| RN-20 | autosave sin botón Guardar | §12 · §8 vincular | e2e + live |
| RN-21 | panel Fuentes persistente+colapsable | §14 | e2e |
| RN-22 | guardas RAG (comercial · precio-campo · clínico-escala · scrub PHI) | §14 adversariales · §6 riesgos | int + live + eval |
| RN-23 | edición en su vista / read-only con origen | §3 chip · §13 read-only · §9 moneda | e2e |
| RN-25 | picker biblioteca + canonical_ref + sinónimos | §2 plantilla/sinónimo | e2e + live |
| RN-26 | ficha paciente completa + completitud no bloquea | §6 · AC-19 (§ Mapa) | e2e |
| RN-27 | personalizado solo-clínica + candidatura | (backend flag) | int |
| RN-28 | modalidad {única/sesiones/recurrente} | §5 (3 variantes + herencia) | unit + e2e |
| RN-29 | variantes estructuradas | §4 (agregar/quitar/sin/cotiza) | unit + e2e + live(keystone) |
| RN-30 | herencia categoría+peldaño bloqueada | §3 (estándar/personalizado/adversarial) · §11 adversarial | e2e |
| RN-31 | numéricos tipados | §5 (numérico/inválido) | unit (Zod) + e2e |
| RN-32 | tipo-cita enum fijo + RichSelect | §5 richselect | unit + e2e |
| RN-33 | prueba social manual + consentimiento | §10 (agregar/quitar/consent/sin-consent) | e2e + int(consent) |

**Bifurcaciones del árbol → scenario:** `happy-seed`→§1 · `happy-plantilla`→§2 · `happy-create`→§2 · `happy-doc-autocomplete`→§14 · `happy-search`→§1 · `adversarial-rbac`→§1/§16 · `edge-delete`→§1 · `happy-activar`→§1 · `edge-rango`→§9 · `edge-paquete`→§5 · `edge-recurrente`→§5 · `happy-rung-filled`→§11 · `happy-rung-empty-guidance`→§11 · `edge-move-rung`→§11 · `a11y-keyboard`→§11 · `edge-sin-doctor`→§8 · `happy-agente`→§15 · `adversarial-tenant`→§16. **Cobertura: 18/18 bifurcaciones.**

**Fuera de scope — declarado (NO es hueco · es decisión):**
- **Tool `match_service_and_specialist`** (la *lógica* de match) → vive en `canal-inbound`. Acá solo entregamos la **data** (keywords + link) — verificada en §7/§8/§15.
- **RAG runtime (indexer Qdrant real + tool retrieval del sales_agent)** → **engine-lift `/pm-luana`**, dependencia HARD del ready package (RN-22/§14 dependen de él para verificarse LIVE; `/architect` lo dimensiona).
- **Integración testimonios ↔ reseñas/NPS (Camila)** → story futura (RN-33 = manual por ahora).
- **Landing pública** (`lisa-landing-public`) · **analítica/Stats del servicio** · **A/B pricing** · **imports bulk CSV** · **AI suggested-pricing** → anti-objetivos / otras stories.
- **Gestión de áreas/especialidades de la clínica** → story `vitalia-fase2-marca-especialidad-clinica` (Servicios la consume read-only).

---

## § Gherkin RECONCILE — comportamientos descubiertos en G (Chris live-verify · 2026-06-16/19)

> Estos scenarios NACIERON de la **live-verify de Chris en G** (el verde de los gates NO los cazó — ver § learning `2026-06-19-unit-green-not-runtime-truth`). Cada uno se construyó + tiene su regression. Tags `@G2-FN` mapean al finding del checkpoint. Mismo Background.

```gherkin
### 17 · Autoguardado fluido — value desde RHF local (G2-F11 · RN-20 · ADR-vitalia-009)

@happy @RN-20 @G2-F11
Scenario: Tipear en un campo rico del Resumen es fluido
  Given el workspace del servicio, leaf Resumen
  When tipeo en "Descripción corta" / "Qué incluye"
  Then el tecleo es fluido (no "procesa cada letra, guarda solo la última")
  And el debounce guarda y al recargar veo lo guardado
  # value SIEMPRE de RHF local — PROHIBIDO value={servicio.X} (gate arch-fitness)

@adversarial @RN-20 @G2-F11
Scenario: Ningún input editable con autosave ata su value al server
  Then el arch-test test-autosave-value-from-local-state falla si un input editable
    en una hoja con useAutosave usa value={<queryData>.x}

### 18 · Para Adrián — FAQ/Objeciones par incompleto (G2-F12/F12b · RN-7-brief)

@happy @G2-F12
Scenario: Agregar un par FAQ vacío no guarda ni rompe
  Given el leaf "Para Adrián", lista FAQ (pares pregunta/respuesta)
  When hago "+ Agregar" y dejo el par vacío
  Then la fila queda local, NO se schedulea autosave y NO hay error 500
  When completo ambos campos
  Then guarda limpio al KB del agente (par completo)

@negative @G2-F12b
Scenario: El VO exige ambos campos (invariante no se debilita)
  Given un par con solo pregunta o solo respuesta
  Then el FE lo filtra del payload (no llega al BE) — el VO FaqPair/ObjectionPair sigue exigiendo ambos

### 19 · Especialistas muestran nombre, no UUID (G2-F13 · RN-9 · AC-5)

@happy @RN-9 @AC-5 @G2-F13
Scenario: Especialistas habilitados muestran nombre + especialidad
  Given un servicio con ≥1 especialista vinculado
  Then cada uno renderiza nombre + especialidad + iniciales (no el UUID)
  And si el roster no resuelve, cae a id-corto no-UUID (degradación grácil · NO-PHI)

### 20 · Plan de pago — 3 cobros persisten al recargar (G2-F6/F14/F14b · RN-6/RN-11)

@happy @RN-6 @G2-F14
Scenario: Los montos del plan de pago no desaparecen ni crashean al recargar
  Given configuré precio/reserva/anticipo/financiamiento y guardé
  When recargo la página
  Then los 3 cobros muestran sus montos (no vacíos, no 0)
  And no hay crash "Cannot read undefined enabled" (defaultValues full-shape)
  # G2-F14b: el BE serializa Decimal money como string JSON; el FE coerce string→number (toNum)

### 21 · Activar — confirm + reflejo inmediato (G2-F2a/F2b · RN-10)

@happy @RN-10 @G2-F2a
Scenario: Activar un servicio pide confirmación
  When toggleo Activo
  Then aparece un confirm dialog antes de activar

@happy @RN-10 @G2-F2b
Scenario: Activar refleja en el workspace sin refresh
  When activo desde la card o el StatusBar
  Then el StatusBar del workspace refleja Activo (setQueryData(detail)) sin recargar

### 22 · Detalle de servicio — navegación (G2-F4/F5/F10)

@negative @G2-F4
Scenario: "Ver detalle" de un especialista no da 404
  When hago "Ver detalle" de un doctor desde Especialistas
  Then navega a /lisa/staff (ruta real), no a /lisa/doctores (404)

@edge @G2-F10
Scenario: El detalle de un servicio no muestra el SubSubTabsBar y el back es origin-aware
  Given entré al detalle desde Catálogo (o desde Escalera)
  Then NO veo el SubSubTabsBar (Catálogo/Escalera N3) dentro del detalle
  And el pill de back dice "Catálogo" (o "Escalera") y vuelve al origen

@edge @G2-F5
Scenario: Entrar a un servicio no dispara el error de Performance de Next 16
  When entro a un servicio (soft-nav intra route group con shell ssr:false)
  Then no aparece "OfferIdPage cannot have a negative time stamp"
  # [offer-id]→resumen resuelto en N3_DEFAULT_LEAF (edge-redirect, no redirect() in-render)
```

## § Matriz de cobertura RECONCILIADA (G round → fix → test REAL → estado)

> Cierra el hueco que el verde de unit no cubre: cada finding de G mapeado a su **test real** + estado honesto. `✅` = construido + test verde · `✅(manual/visual)` = construido + verificado live por Chris, sin test automatizado aún · `⏳` = deferred (must_pass:false en 04-validators · NO green-phantom).

| Finding | Fix (commit) | Scenario | Test real | Estado |
|---|---|---|---|---|
| G2-F1 gutter padding | `9b3c0a13` | (fidelidad rule#34) | visual goldens 8 ⏳ | ✅(manual) |
| G2-F2a confirm activar | `9b3c0a13` | §21 confirm | `ServiceStatusBar.test.tsx` | ✅ |
| G2-F2b activar refleja | `9b3c0a13` | §21 reflejo | `ServiceStatusBar.test.tsx` (setQueryData) | ✅ |
| G2-F3 EntityPicker null-safe | `9b3c0a13` + ui-kit | (crash guard) | ui-kit EntityPicker 7/7 + caller guard | ✅ |
| G2-F4 doctor → /lisa/staff | `2eabe9bd` | §22 ver-detalle | `EspecialistasView.test.tsx` (hrefs) | ✅ |
| G2-F5 Next16 negative timestamp | findings_round2b | §22 perf | `shell-routes` N3_DEFAULT_LEAF 5 tests | ✅ |
| G2-F6 plan-pago price 0 | `e7d5766f` | §20 | `PlanPagoView.test.tsx` | ✅ |
| PlanPago 3-cobro build | `91c01be9` | §20 + §9 | `PlanPagoView.test.tsx` + `test_pricing_calc.py` | ✅ |
| PEN fast-track | `d6690e59` | (seed/data) | data live | ✅(manual) |
| G2-F7 popover z-index | `a90b3b3b` | (fidelidad) | visual ⏳ | ✅(manual) |
| G2-F8 Fuentes arriba | `022bf843` | (orden) | `KnowledgeSourcesPanel.test.tsx` (mount) | ✅ |
| G2-F9 moneda ≠ tenant | (data) | §9 moneda | → follow-up `tenant-currency-config` | ⏳→story |
| G2-F10 detalle sin SubSubTabsBar + back | `0ec2dd84` | §22 detalle | detail-guard core + back origin-aware tests | ✅ |
| G2-F11 autosave value-local | `e6f97173` | §17 | `test-autosave-value-from-local-state.test.ts` + `ResumenView.test.tsx` (sin-mock) | ✅ |
| G2-F12 faq/objeciones 500 | `cc4a2ea9` (BE) + `54119aaf` (FE) | §18 | `test_sales_brief_service.py` + `FaqPairList/ObjecionPairList.test.tsx` | ✅ |
| G2-F12b par vacío 500 | `5bfa7d4a` | §18 negative | `ParaAdrianView.test.tsx` (add vacío no schedulea) | ✅ |
| G2-F13 especialistas UUID→nombre | `f40556ea` (BE) + `8a51ad4b` (FE) | §19 | `test_specialist_link_service.py` + `EspecialistasView.test.tsx` | ✅ |
| G2-F14 montos desaparecen + crash | `c0e89ca1` | §20 | `PlanPagoView.test.tsx` (transición undefined→defined) | ✅ |
| G2-F14b Decimal-string vacío | `2dc86a85` | §20 | `PlanPagoView.test.tsx` (strings reales del wire) | ✅ |

**Deferred (must_pass:false · 04-validators § RECONCILE · NO green-phantom):**
- **E2E happy-path del workspace** (crear→editar→plan-pago→especialista→activar): specs `e2e/shell-organism/lisa-servicios-*.spec.ts` existen pero `test.skip` gated en `E2E_OFFER_ID`/`E2E_ENABLE_WRITES` → owner auditor Carril R (un-skip + seed offer-id) o follow-up.
- **Visual goldens 8** (`e2e/__screenshots__/servicios/` vacío): baselines no generados.
- **Contract-test FE↔BE** (HB-42): ausente — los bugs G2-F11/F14b nacieron de contratos imaginados.

---

## § Wireframes (mockups · ★ v3 2026-06-12 · canon `@luana/ui-kit` + biblioteca · cambios Chris 2026-06-06/12)

`mockups/` — **shell-organism completo verbatim** (TopBar + Ribbon Lisa + SubTabsBar + ValeriaSidebar 50/50, portado de lisa-marca v2.1). ★ v3: el N3 se compone del **canon `design-system-canon.md`** — `EntityWorkspaceLayout` + `EntitySubNavBar` **full-bleed** (franja tercer-ribbon §2.2, NO card) + **`EntityPicker` ▾ switcher** (§2.4 · cambiar de servicio sin volver — RATIFICADO Chris 2026-06-12) + **`EntityInfoCard` Opción B** (§2.3) + `Select` canónico (§2.5) + **una sola `FloatingAutosaveIndicator`** (§2.6). `_shared.css` = chrome canónico + clases servicios. Tokens HSL de `globals.css`, datos LatAm reales, Spanish neutro.

- `catalogo.html` — sub-tab Servicios → N3 SubSubTabsBar **[Catálogo · Escalera]** · ★ v3 grid de **`EntityInfoCard`** (acento Lisa arriba · media circular · título + especialidad · fila de métricas duración/precio/especialistas · footer chip Activo/Borrador + 🟡 chip origen Estándar/Personalizado · kebab ⋮) + filtros con `Select` canónico + empty-state que invita a **agregar desde la biblioteca**. ★ Chris #2: sin chips "seña X%" (la seña se explica en Plan de pago).
- `escalera.html` — **5 peldaños FIJOS** (labels médicos sobre `OfferValueLevel`) **autoexplicativos**: cada peldaño dice qué va ahí; el **vacío muestra ejemplos de la biblioteca** (★ v3 · antes "por vertical") + "crear aquí". Drag mueve de peldaño. SIN drawer de override. **★ Layout (Chris 2026-06-12):** Gancho gratuito = **fila full-width arriba** · Primera visita + Tratamiento principal + Premium = **3 columnas al medio** · Plan/convenio = **fila full-width abajo** (reparte mejor + refleja el recorrido: entrada → núcleo de venta → permanencia).
- `servicio-workspace.html` — `[offer-id]` con **`EntitySubNavBar` canon full-bleed**: root-pill **‹ Servicios** + **`EntityPicker` ▾** (saltar de servicio sin volver) + **5 leaves** Resumen / Para Adrián / Especialistas / Plan de pago / Prueba social + strip KEYSTONE (activo → Adrián lo conoce). ★ v3 Resumen reagrupado: Identidad (+ chip "Servicio estándar") · Qué es · **El procedimiento** (cómo se hace + anestesia + duración/sesiones + preparación/cuidados/downtime) · Resultados · **Riesgos** (riesgos + señales de alarma) · Operación. + **indicador de completitud** ("ficha 22/26") + **una** píldora autosave flotante. **Plan de pago** = los 3 cobros (#2/#3). **Especialistas** = vincular-desde-roster + "Ver detalle ↗" (#6/#7).
- `nuevo-servicio.html` — ★ v3.1 (Chris 2026-06-12) **crear arranca en el picker de la biblioteca como VISTA INLINE de la hoja** (NO modal/popup): typeahead nombre+sinónimos → resultado con categoría + peldaño sugerido → "Usar esta plantilla" / "Crear personalizado". En el estado picker la franja muestra solo "‹ Servicios" + título (el workspace aún no existe); **al elegir se crea el borrador** y aparece el workspace — **ESTRUCTURALMENTE IDÉNTICO al de editar** (mismos 5 leaves + mismos 6 grupos de Resumen · RN-16): plantilla → PRE-LLENADO ✨ (chip estándar, ficha 9/26); personalizado → VACÍO (chip Personalizado, ficha 2/26). El panel "Fuentes & conocimiento" vacío absorbe el viejo "Arranca rápido" (documento → "Procesar con Lisa" → autocompleta). "↻ Volver a elegir" regresa al picker.

> **★ Root de la franja (Chris 2026-06-12 · = construcción nueva de staff/ui-kit):** el "‹ Servicios" es **un leaf-peer más del tablist** (`EntitySubNavBar` de `@luana/ui-kit`: el root es la primera entrada con "‹" adelante, mismas clases/forma que los demás leaf-tabs, estado inactivo) — NO un pill con estilo propio. Aplicado en ambos workspaces (clase `entity-leaf-root` en mockups).

> ★ Cambios de shell (FIRMA-2 + round 3): **#4 (RATIFICADO global por Chris)** los leaf-tabs del workspace (`.entity-leaf`) tienen **el mismo color y forma que los SubSubTabs** → se aplica **global** al `EntitySubNavBar` shipped (staff/doctores también) para consistencia en todo el shell. Nota a `/architect` + `SHELL-DESIGN-CONTRACT`. **#2** campos no obvios → **tooltip** (`.tip` · Shadcn `Tooltip` en código). **Round 3:** panel **"Fuentes & conocimiento"** persistente+colapsable (`<details>`/Shadcn) visible en crear+editar · **autosave** (sin botón Guardar · indicador 💾) · `Doctores`→**`Especialistas`** · tarjetas sin badge de peldaño.

```bash
cd vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups && python3 -m http.server 8899
# http://127.0.0.1:8899/catalogo.html · /escalera.html · /servicio-workspace.html · /nuevo-servicio.html
```

## § Componentes (reuse > new · verificar en `vitalia-design-system`)

> ★ v3 2026-06-12 — el N3 **compone del canon** (`design-system-canon.md` §2): las piezas Entity* + page-primitives vienen de **`@luana/ui-kit` 0.4.0** (shippeadas — verificado `core/@luana/ui-kit/src/index.ts`), NO de la réplica local vieja.
> ★ 2026-06-15 — **el inventario campo-por-campo + las primitivas nuevas con contrato (RichSelect, NumberWithUnit, ModalidadPicker, VariantsRepeater, TestimonialsList, FichaCompletenessChip, ServiceStatusBar…) viven en `§ Mapa de campos` + `§ Inventario de componentes`** (abajo · SSoT para `/architect`+`/dev-team`). Esta tabla queda como vista resumida histórica.

| Componente | Path (verificar) | reuse/new |
|---|---|---|
| Shell chrome (TopBar · Ribbon · SubTabsBar · ValeriaSidebar) | `components/shared/shell-organism/` | reuse (shipped) |
| **SubSubTabsBar** (Catálogo · Escalera, N3-static) | `components/shared/shell-organism/SubSubTabsBar.tsx` | reuse (shipped) |
| **★ `EntityWorkspaceLayout`** (N3 list/detail · canon §2.1) | `@luana/ui-kit` (`core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx`) | reuse (ui-kit 0.4.0) |
| **★ `EntitySubNavBar`** (franja full-bleed canon §2.2 · root-pill ‹ + picker + leaves) | `@luana/ui-kit` (reemplaza réplica local) | reuse (ui-kit 0.4.0) |
| **★ `EntityPicker`** (switcher ▾ · buscador server-side + paginado · canon §2.4 · RATIFICADO 2026-06-12) | `@luana/ui-kit` | reuse (ui-kit 0.4.0 · = lisa-doctores) |
| **★ `EntityInfoCard`** (cards del catálogo · Opción B canon §2.3 + Skeleton + Empty) | `@luana/ui-kit` | reuse (ui-kit 0.4.0) |
| **★ `Group` / `GroupHeader` + `FloatingAutosaveIndicator`** (info agrupada + 1 píldora autosave · canon §2.6) | `@luana/ui-kit` | reuse (ui-kit 0.4.0) |
| **★ Page-primitives** (`PageContainer` · `PageContentStack` · `Toolbar` · `FilterBar` · `EmptyState` · canon §2.7) | `@luana/ui-kit` (`layout/`, `archetypes/`) | reuse (ui-kit 0.4.0) |
| Card · Badge · Switch · **`Select` canónico (§2.5 · NO `<select>` nativo)** · Avatar | `@luana/ui-kit` + `components/ui/` | reuse |
| **Input + Search icon (buscador) + Select (filtros)** — patrón `StaffDirectoryHeader` | `components/ui/{input,select}.tsx` | reuse |
| **★ `BibliotecaPicker`** (modal "+ Nuevo": typeahead nombre+sinónimos sobre la biblioteca + "Usar plantilla" / "Crear personalizado" · RN-25) | `features/lisa/components/servicios/` | NEW (justif: picker de plantillas de contenido, no existe equivalente — distinto de `EntityPicker` que cambia entidad existente) |
| **★ `FichaCompletenessChip`** (indicador "ficha 22/26 · faltan: …" · AC-19) | `features/lisa/components/servicios/` | NEW (justif: derivado de los 26 must-have del § MVP) |
| ~~Sheet (crear servicio)~~ — ★ #1: crear ya NO usa Sheet; reusa `ServiceWorkspace` en modo vacío | — | eliminado |
| DnD (mover servicio de peldaño) | `@dnd-kit/core` (ya en `adrian-embudo`) | reuse |
| `ServiciosDirectoryHeader` (título + buscador + filtros + Nuevo) · `ServiceCard` (★ sin badge de peldaño · #8) · `EscaleraView` (5 rungs fijos) · `RungColumn` (con guía de vacío) · `ServiceWorkspace` (crear + editar = mismo · #1) + leaves (`ResumenView` · **`ParaAdrianView`** · `EspecialistasView` · `PlanPagoView` · `PruebaSocialView`) · **`EspecialistaLinkPicker`** (selector del roster `lisa-doctores` · #6) · **`KnowledgeSourcesPanel`** (★ panel "Fuentes & conocimiento" persistente+colapsable · dropzone + "Procesar con Lisa" + lista de fuentes con estado extraído/indexado + toggle "Adrián consulta" · #1+#9B) · `SeedPresetCard` · `RungPicker` (peldaño autoexplicativo) · `FaqPairList` + `ObjecionPairList` | `features/lisa/components/servicios/` | NEW (feature-local) |
| **`FieldTooltip`** (#2 · subrayado punteado + hover) — átomo reutilizable | `components/shared/` o `components/ui/tooltip.tsx` (Shadcn) | reuse Shadcn `Tooltip` |

> ★ Eliminados del scope (Chris 2026-06-06): `LadderSlotWorkspace`, ruta `ladder/[slot-id]`, `pricing_override`/`cta_copy` por slot, Shadcn `Tabs` en el workspace. El workspace usa `EntitySubNavBar` (consistencia con staff).
> ★ Eliminados (Chris 2026-06-07 FIRMA-2): `StatsView` (leaf Stats · #4 — esto es configuración, no analítica) · chips "seña X%" en `ServiceCard` (#2 · confundían). `PlanPagoView` modela **3 cobros separados** (reserva + anticipo + cuotas).

---

## § Mapa de campos (★ Chris 2026-06-15 · "cada campo: su tooltip, su por qué, a qué entidad va, qué átomo usa")

> SSoT campo-por-campo para que `/architect` modele el schema y `/dev-team` construya sin improvisar. **Tooltip** = el texto literal del hover (RN-18: solo campos no obvios/pesados; "—" = trivial, sin tooltip). **Entidad** = dónde persiste (leyenda abajo). **Átomo/molécula/token** = de qué se compone (canon `design-system-canon.md`; ⊕ = primitiva nueva, contrato en § Inventario de componentes).

**Leyenda de entidades:**
- **`Offer` (engine)** — Offer Studio (`core/luana-core-offer-studio`, vía EP-2): `public_name`, `description`, `value_level`, `ServiceDetails.session_duration_minutes`, `ServiceDetails.total_sessions_count`, pricing, `canonical_service_ref`.
- **`OfferExt` (brand)** — extensión brand-level vitalia del offer (columnas/tabla aparte · `/architect` define la forma · § Pendientes). Aloja todo lo que el engine no tiene.
- **`SalesBrief` (brand · sub-entidad de OfferExt)** — el argumentario "Para Adrián"; lo lee `TenantKnowledgeBuilder` → Adrián.
- **`ServiceSpecialistLink` (brand)** — FK servicio↔`vitalia_doctors` (roster de `lisa-doctores`).
- **`KnowledgeSource` (engine, per-offer)** — material cargado (extrae + RAG · RN-17/22).
- **`Case` / `Testimonial` (brand)** — prueba social (Case = Asset foto antes/después + consentimiento; Testimonial = texto curado).
- **`Computed`** — derivado, no se persiste (read-only).
- **`Tenant` (externo)** — dato de otra superficie (moneda, áreas de la clínica, voz) — read-only aquí + tooltip de origen (RN-23).

### Leaf 1 · Resumen

| Campo | Entidad | Por qué / quién consume | Tooltip | Átomo/molécula/token |
|---|---|---|---|---|
| Nombre | `Offer.public_name` | identifica el servicio; lo muestran catálogo/Adrián/landing | — | `Input` |
| Especialidad / categoría | `OfferExt.category` (opciones = `Tenant` áreas) | clasifica + filtra + alimenta hints/presets | "Categoría del servicio · sale de las áreas de tu clínica (Lisa → Marca). En un servicio estándar la define la biblioteca." | `Select` canónico (§2.5); `disabled`+🔒 si estándar (RN-30) |
| Chip origen (Estándar/Personalizado) | `OfferExt.canonical_service_ref` (null=personalizado) | estandariza nombres + reportes comparables + match Adrián | "Vinculado a la biblioteca estándar: '{nombre canónico}'" | `Badge` var. `chip-origen` ⊕ |
| Peldaño | `Offer.value_level` (enum engine) | ubicación en la escalera; Adrián/escalera/Propuestas | "En qué momento del recorrido del paciente entra. En un servicio estándar lo define la biblioteca." | `RungPicker` ⊕ (5 botones; `locked`+🔒 si estándar · RN-30) |
| Descripción corta | `Offer.description` (voz de marca) | lenguaje paciente; landing/Adrián | "El tono/voz lo toma de Lisa → Marca. El texto es editable; el estilo viene de Marca." | `Textarea` + `Badge` "✨ voz de marca" |
| Descripción larga | `OfferExt.description_long` | FAQ + landing | — | `Textarea` |
| Qué incluye | `OfferExt.includes` | fija expectativa; Adrián la cita | — (✨ si pre-llenado) | `Textarea` |
| Qué no incluye | `OfferExt.excludes` | evita malentendidos/objeciones | — | `Textarea` |
| **Variantes** | `OfferExt.variants[]` `{name,price,note}` | opciones que cambian el precio; Adrián cotiza la exacta (RN-29) | "opciones del mismo servicio que cambian el precio" | `VariantsRepeater` ⊕ (`Input`+`NumberWithUnit`⊕) |
| Garantía | `OfferExt.warranty` | confianza; Adrián la cita | — | `Input` |
| Cómo se hace (pasos) | `OfferExt.procedure_steps` | Adrián cita textual; ficha paciente (RN-26) | (hint: "Adrián cita esto textual; lo clínico escala al doctor") | `Textarea` (✨) |
| ¿Lleva anestesia / duele? | `OfferExt.anesthesia_pain` | FAQ dolor (objeción top) | — | `Input` (✨) |
| Duración de cada sesión | `Offer.ServiceDetails.session_duration_minutes` (number) | Mateo agenda con esto (RN-31) | — | `NumberWithUnit` ⊕ (min) |
| Preparación previa | `OfferExt.prep` | reduce cancelaciones | — | `Input` (✨) |
| Cuidados posteriores | `OfferExt.aftercare` | post-venta; Adrián la cita | — | `Input` (✨) |
| Tiempo de recuperación / downtime | `OfferExt.downtime` | objeción "¿cuánto falto al trabajo?" | — | `Input` (✨) |
| Resultado esperado | `OfferExt.expected_result` | vende el resultado; Adrián | — | `Input` |
| ¿Cuándo se ve el resultado? | `OfferExt.result_timing` | expectativa | — | `Input` |
| ¿Cuánto dura el resultado? | `OfferExt.result_lifespan` | justifica el precio | — | `Input` |
| Expectativas realistas | `OfferExt.realistic_expectations` | seguridad/confianza | — | `Input` |
| Riesgos y efectos secundarios | `OfferExt.risks` (capa curada) | Adrián cita textual, no interpreta (RN-22/26) | banner safety: "Adrián cita esto textual — siempre deriva al doctor para diagnóstico" | `Textarea` (✨) |
| Señales de alarma | `OfferExt.red_flags` | seguridad post-tratamiento | — | `Textarea` (✨) |
| **Modalidad** | `OfferExt.modality` enum {unica,sesiones,recurrente} | define cómo se vende/agenda (RN-28) | "Cómo se entrega y se agenda el servicio. Define si Adrián vende una cita, un paquete de sesiones, o un plan que se repite." | `ModalidadPicker` ⊕ (3 cards + progressive disclosure) |
| · Número de sesiones (si `sesiones`) | `Offer.ServiceDetails.total_sessions_count` (number) | paquete; Mateo agenda N citas | — | `NumberWithUnit` ⊕ (sesiones) |
| · Cada cuánto / intervalo (si `sesiones`) | `OfferExt.session_interval` `{value,unit}` | cadencia del paquete; Mateo | — | `NumberWithUnit` ⊕ + `Select` unidad |
| · Se repite cada / cadencia (si `recurrente`) | `OfferExt.recurrence_interval` `{value,unit}` | Camila reactiva al tocar repetir | — | `NumberWithUnit` ⊕ + `Select` unidad |
| Duración de la cita inicial | `OfferExt.initial_appt_duration_minutes` (number) | Mateo agenda el primer turno (RN-31) | — | `NumberWithUnit` ⊕ (min) |
| **Tipo de cita inicial** | `OfferExt.initial_appt_type` enum (3 fijo) | la agenda trata el primer turno (RN-32) | descripción **por opción** (en el dropdown): "Primera cita para evaluar y planificar" / "El tratamiento arranca en la primera cita" / "Charla sin costo para resolver dudas" | `RichSelect` ⊕ (CORE candidate) |

**Barra de estado del servicio (`svc-statusbar`, arriba del leaf):**

| Campo | Entidad | Por qué | Tooltip | Átomo/molécula/token |
|---|---|---|---|---|
| Toggle **Activo** | `OfferExt.is_active` | Adrián lo conoce + vende; NUNCA bloqueado por completitud (RN-26) | — | `Switch` |
| "Adrián lo ofrece" | `Computed` (is_active) | señal de estado | — | texto + emoji |
| **N especialistas vinculados** | `Computed` (count `ServiceSpecialistLink`) | atajo a la pestaña Especialistas (#6) | "Ver/editar quién realiza este servicio" | `statuslink` ⊕ → leaf Especialistas |
| Chip origen | `OfferExt.canonical_service_ref` | ver arriba | ver arriba | `Badge` `chip-origen` ⊕ |
| **ficha N/26** | `Computed` (completitud vs § MVP) | informativo, NUNCA bloquea Activo (AC-19) | "Faltan: {campos}. No bloquea 'Activo' — solo enriquece lo que Adrián puede responder." | `FichaCompletenessChip` ⊕ |

### Leaf 2 · Para Adrián (todos → `SalesBrief`, los lee `TenantKnowledgeBuilder` → Adrián)

| Campo | Por qué / quién consume | Tooltip | Átomo/molécula/token |
|---|---|---|---|
| Candidato ideal | calificación del lead | — | `Textarea` |
| **Contraindicaciones / NO candidato** | seguridad: el agente NO ofrece a un no-candidato (RN-22) | "Quién NO es candidato. Seguridad (HIPAA-lite): el agente NO ofrece a un no-candidato y deriva al doctor. Lo escribís una vez, protege siempre." | `Textarea` |
| Preguntas de calificación | descubrimiento del agente | — | `Textarea` |
| **Condiciones de escalada a humano** | freno de seguridad del agente (RN-22) | "Qué temas el agente NO maneja y pasa a una persona: dolor, sangrado, diagnóstico, medicación." | `Textarea` |
| Requiere evaluación previa | gate antes de cerrar | — | `Switch` |
| Beneficios emocionales | vender el resultado | — | `Textarea` |
| Dolor de no tratarse | urgencia | — | `Textarea` |
| Diferenciadores | por qué esta clínica | — | `Textarea` |
| Ganchos / promos vigentes | cierre | — | `Textarea` |
| **FAQ** (pares q→a) | KB del agente (limpio, no texto libre) | — | `FaqPairList` ⊕ |
| **Objeciones → respuestas** (5 universales) | manejo de objeciones | — | `ObjecionPairList` ⊕ |
| **Palabras clave / sinónimos** | match canal-inbound RN-16 (cómo el paciente lo nombra) | "Cómo nombra el paciente al servicio (no el nombre clínico): 'carillas', 'fundas'. Así Adrián entiende la intención aunque no diga el término técnico." | `TagInput` ⊕ (chips + agregar) |
| Problemas que resuelve | match/argumentario | — | `Textarea` |
| Lenguaje a evitar | no asustar al paciente | — | `Textarea` |

### Leaf 3 · Especialistas (entidad → `ServiceSpecialistLink`)

| Campo / acción | Por qué | Tooltip | Átomo/molécula/token |
|---|---|---|---|
| Lista de vinculados (avatar+nombre+especialidad) | quién realiza el servicio; cimiento canal-inbound RN-17 | — | `EntityInfoCard`/list row + `Avatar` |
| **+ Vincular especialista** | abre selector del **roster** (NO crea especialistas) | banner: "Vincular no crea especialistas: elige del roster de tu clínica (Lisa → Especialistas)." | `EspecialistaLinkPicker` ⊕ (checklist del roster + buscador) |
| Ver detalle ↗ | deep-link a la ficha en Lisa→Especialistas | — | link / `Button` ghost |
| Desvincular | quita el link (no borra del roster) | — | `Button` ghost destructive |

### Leaf 4 · Plan de pago (entidad → `OfferExt` pricing · 3 cobros distintos RN-6)

| Campo | Por qué | Tooltip | Átomo/molécula/token |
|---|---|---|---|
| Precio | Adrián cotiza | (moneda) "La moneda (S/) sale de la configuración de tu clínica (no se edita aquí)." | `Input`(number) + `Badge` S/ (moneda = `Tenant`, read-only) |
| Modo (rango/fijo) | "desde $X" vs fijo | — | `Select` canónico |
| Adrián puede decir el precio | si off → agenda valoración en vez de dar precio | (hint inline) | `Switch` |
| Pide reserva (seña) | reduce inasistencias | — | `Switch` |
| Monto de la reserva + tipo (fijo/%) | apartar el turno; se descuenta del total | — | `Input`(number) + `Select` |
| Requiere anticipo | pago para iniciar (≠ reserva) | "Pago inicial sobre el costo del tratamiento para empezar (aparte de la reserva). Ej: 30% antes de la 1ª sesión." | `Switch` |
| Anticipo (% o monto) | clave en implantes/ortodoncia | — | `Input`(number) + `Select` unidad |
| ≈ equivale a (anticipo) | `Computed` | "Se calcula solo a partir del % y el precio. No se edita." | `Input` `disabled` |
| Ofrece cuotas | financia el saldo | — | `Switch` |
| Cuotas (N) · Interés (MSI/con) | financiamiento | — | `Input`(number) · `Select` |
| ≈ por mes | `Computed` | "(precio − reserva − anticipo) ÷ cuotas. No se edita." | `Input` `disabled` |
| Medios de pago · Socio financiero | logística de cobro | — | `Input` |

### Leaf 5 · Prueba social (entidades → `Case` · `Testimonial` · carga manual RN-33)

| Campo / acción | Por qué | Tooltip | Átomo/molécula/token |
|---|---|---|---|
| Casos antes/después + **Subir caso** | confianza visual; Adrián los muestra | "Cada caso requiere el consentimiento firmado del paciente (HIPAA-lite). '+ Subir caso' abre: foto antes · foto después · confirmar consentimiento." | grid `Case` + uploader ⊕ + `Badge` "con consentimiento" |
| **Testimonios** `{rating·texto·autor·origen}` + agregar/quitar | confianza; Adrián los cita | — | `TestimonialsList` ⊕ |
| Prueba de volumen ("+300 …") | autoridad | — | `Badge` chip-lisa |

### Panel transversal · Fuentes & conocimiento (persistente+colapsable · entidad → `KnowledgeSource`)

| Campo / acción | Por qué | Tooltip | Átomo/molécula/token |
|---|---|---|---|
| Dropzone + "Procesar con Lisa" | (a) autocompleta campos (b) RAG para Adrián (RN-17/22) | "El precio siempre sale del campo (no del documento). Lo clínico escala al doctor." | `KnowledgeSourcesPanel` ⊕ (`<details>`/`Collapsible` + dropzone) |
| Toggle "Adrián consulta" por fuente | controla qué entra al RAG | — | `Switch` |
| Estado (extraído / en RAG) | `Computed` (del sistema) | "El precio sale del campo estructurado, no del PDF (evita que quede viejo)." | `Badge` `src-chip` |

---

## § Inventario de componentes — átomos · moléculas · organismos (existe vs crear · contrato)

> Regla (canon `design-system-canon.md` + `frontend-visual-fidelity.md` D1): **componer del canon**; crear solo lo que no existe. Cada primitiva nueva (⊕) ya está **mockup'eada** (HTML/CSS/JS en `mockups/`) — el build la materializa en Next. **`/po-ux` no toca `vitalia/frontend/src` (refining=docs); declara el contrato, `/architect` lo aprueba, `/dev-team` lo construye.**

### A · Existe — reusar (NO recrear)

| Componente | Tipo | Vive en | Uso en esta story |
|---|---|---|---|
| `Input` · `Textarea` · `Switch` · `Badge` · `Avatar` · `Card` · `Button` | átomo | `@luana/ui-kit` / `components/ui/` | campos base, toggles, chips |
| **`Select` canónico** (§2.5 · ❌ `<select>` nativo) | átomo | `@luana/ui-kit` | unidades, modo precio, interés |
| **`FloatingAutosaveIndicator`** (§2.6 · UNA por página) | molécula | `@luana/ui-kit` | la pastilla de guardado (#2 · ya canon) |
| `Tooltip` (`FieldTooltip`) | átomo | `components/ui/tooltip.tsx` (Shadcn) | todos los tooltips RN-18 |
| `EntityWorkspaceLayout` · `EntitySubNavBar` · `EntityPicker` · `EntityInfoCard` | organismo | `@luana/ui-kit` 0.4.0 | shell N3 list/detail + switcher ▾ + cards |
| Page-primitives (`PageContainer` · `Toolbar` · `FilterBar` · `EmptyState` · skeletons) | molécula | `@luana/ui-kit` | layout de catálogo/workspace |
| `SubSubTabsBar` | molécula | `components/shared/shell-organism/` | toggle Catálogo·Escalera |
| `@dnd-kit/core` | lib | dep | drag servicio entre peldaños |
| **Tokens** | token | `globals.css` / `@luana/design-tokens` | `--agent-lisa`, `--radius`, `--border`, escala de spacing, `--warning`/`--success` (estados autosave). ❌ arbitrary-values (canon §0) |

### B · Crear (⊕) — mockup'eado, build en Next

| Componente | Tipo | Dónde vive | Contrato (props) | Aplica a | Mockup |
|---|---|---|---|---|---|
| **`RichSelect`** | átomo | **`@luana/ui-kit` (candidato CORE → nota `/pm-luana`)** | `options: {value, title, description}[]` · `value` · `onChange` · `placeholder?` · popover `position:fixed` (escapa overflow) · a11y `listbox` | Tipo de cita inicial (reusable: cualquier enum donde la descripción ayuda a elegir) | `.rich-select` |
| **`NumberWithUnit`** | molécula | **`@luana/ui-kit` (candidato CORE)** | `value:number` · `onChange` · `unit:string` **o** `units:string[]`+`unitValue`+`onUnitChange` · `min`/`step` | sesiones, duración, intervalo, cadencia (RN-31) | `.num-affix` |
| **`ModalidadPicker`** | molécula | `features/lisa/components/servicios/` (generalizable → `OptionCardGroup` CORE) | `value:'unica'\|'sesiones'\|'recurrente'` · `onChange` · `options:{value,title,desc}[]` · slot de detalle revelado (progressive disclosure) | Modalidad (RN-28) | `.modalidad-picker` |
| **`RungPicker`** | molécula | `features/lisa/components/servicios/` | `value:ValueLevel` · `onChange` · `locked?:boolean` (estándar → no editable · RN-30) · 5 opciones fijas | Peldaño en Identidad | `.rung-picker` |
| **`VariantsRepeater`** | molécula | `features/lisa/components/servicios/` | `value:{name,price,note}[]` · `onChange` (add/remove/edit) · moneda del tenant | Variantes (RN-29) | `.variants-list` |
| **`TestimonialsList`** | molécula | `features/lisa/components/servicios/` | `value:{rating,text,author,source}[]` · `onChange` (add/remove) | Prueba social (RN-33) | `.testi-list` |
| **`FaqPairList`** · **`ObjecionPairList`** | molécula | `features/lisa/components/servicios/` | `value:{q,a}[]` / `{type,response}[]` · `onChange` | Para Adrián (KB del agente) | (markup pares) |
| **`TagInput`** | molécula | `@luana/ui-kit` (candidato) o feature | `value:string[]` · `onChange` · chips + agregar | Palabras clave/sinónimos | (chips) |
| **`FichaCompletenessChip`** | molécula | `features/lisa/components/servicios/` | `filled:number` · `total:number` · `missing:string[]` (tooltip) | barra de estado (AC-19) | `.completeness-chip` |
| **`ServiceStatusBar`** | organismo | `features/lisa/components/servicios/` | compone toggle Activo + nota + `chip-origen` + `FichaCompletenessChip` + `statuslink` | header del workspace | `.svc-statusbar` |
| **`BibliotecaPicker`** | organismo | `features/lisa/components/servicios/` | typeahead nombre+sinónimos sobre la biblioteca + "Usar plantilla"/"Crear personalizado" · inline (NO modal · RN-16/25) | crear servicio | `.biblio-*` |
| **`EspecialistaLinkPicker`** | organismo | `features/lisa/components/servicios/` | checklist del roster `vitalia_doctors` + buscador · autosave al marcar (RN-20) | Vincular especialista (#7) | `#link-doctor-panel` |
| **`KnowledgeSourcesPanel`** | organismo | `features/lisa/components/servicios/` | dropzone + "Procesar con Lisa" + lista de fuentes (estado extraído/RAG) + toggle por fuente | panel Fuentes (RN-17/21/22) | `.kpanel` |
| **`chip-origen`** (Badge variant) | átomo | `@luana/ui-kit` (variant de `Badge`) o feature | `variant:'estandar'\|'personalizado'` | catálogo + statusbar | `.chip-origen` |
| `ServiciosDirectoryHeader` · `ServiceWorkspace` (crear=editar) + 5 leaves (`ResumenView`·`ParaAdrianView`·`EspecialistasView`·`PlanPagoView`·`PruebaSocialView`) · `EscaleraView` · `RungColumn` | organismo | `features/lisa/components/servicios/` | composición de la story | los 4 mockups |

> **Candidatos CORE (`/pm-luana` promotion gate · nota para `/architect`):** `RichSelect` + `NumberWithUnit` (+ `OptionCardGroup` si se generaliza `ModalidadPicker`) son primitivas genéricas reusables cross-brand → evaluar lift a `@luana/ui-kit` en vez de feature-local. El resto es feature-local de servicios.

## § Decisiones RONDA 1 (cerradas — interrogatorio gate)

Batch 1: todo servicio = Offer · catálogo por-tenant + scope clínica opcional · precio fijo+rango · paquetes en MVP.
Batch 2: labels médicos sobre el enum engine · recurrente = atributo (no peldaño) · seña/financiamiento por servicio en Lisa.
Batch 3: link doctor opcional pero recomendado · RBAC admin+owner editan / resto read-only · **toggle único Activo** (landing eliminada de esta story, Chris #2 2026-06-06).

## § Pendientes para /architect (no bloquean RONDA 1)
- Forma exacta del schema brand-level (columnas en tabla offers vitalia vs tabla aparte) + el preset pack EP-2 (`offer/extensions.py`).
- Dónde persiste el link servicio↔doctor (FK brand-level → `vitalia_doctors`).
- Mapeo fino label médico ↔ `OfferValueLevel` + qué ejemplos `PROFESIONAL_SALUD` del engine se muestran como hints.
- Contenido de los seed presets dental/estética (escalera ejemplo por vertical).
- **(#1+#9B · ENGINE-LIFT · dependencia HARD · TODO junto)** Modelo de conocimiento `KnowledgeSource` per-offer en esta story: **(a)** extractor→autocompletar (reusar copilot `document_processor`) **(b)** indexer Qdrant real (hoy **STUB** → lift `/pm-luana`) **(c)** tool de retrieval del **sales_agent** (hoy **no existe** → lift `/pm-luana`) **(d)** guardas RN-22 (scope comercial · precio del campo · clínico→escala · scrub PHI). Chris: A+B juntos. El lift (b)(c) es **dependencia hard del ready package**. Archivo subido = Asset (PHI handling).
- **(#4 · RATIFICADO global)** `EntitySubNavBar` restyle a estilo SubSubTab se aplica **global** al shell shipped (staff/doctores incluidos · consistencia) → actualizar `SHELL-DESIGN-CONTRACT` + arch-test del componente.
- **(autosave)** Patrón autoguardado del workspace (debounce on-change · sin botón Guardar · RN-20) reusando el patrón shipped de otras sub-tabs (ADR-vitalia-004 §5 autosave 600ms).
- **(#3)** **Especialidad de la clínica** (tenant-level): confirmar si existe el campo en brand/onboarding; si no, su autoría es **cross-story onboarding/marca** (`/pm-vitalia`). Servicios lo **consume** read-only (presets + hints + opciones del dropdown per-servicio). Distinto del campo per-servicio `especialidad/categoría`, que sí vive aquí.
- **(#2)** Átomo `FieldTooltip` (Shadcn `Tooltip`) + convención de cuáles campos lo llevan.
- **(★ 2026-06-12 · biblioteca)** Modelo de la **biblioteca de servicios estándar**: tabla brand-level read-only (entrada canónica: nombre + sinónimos + categoría + peldaño sugerido + plantilla de contenido) como **data del preset pack EP-2** (`offer/extensions.py`) · `canonical_service_ref` en el offer vitalia · endpoint typeahead (nombre+sinónimos, scoped tipo de clínica) · flag interno "candidato a biblioteca" (RN-27) · seed dental + estética (contenido Lisa-generado + curado — proceso de curaduría a definir).
- **(★ 2026-06-12 · completitud)** Cálculo del indicador "ficha N/26" (denominador = § MVP must-have; campos condicionales como anticipo cuentan solo donde aplican).

## § Auditoría de campos — editable / dónde se edita (★ Chris round 3 · "dale una auditoría")

> Recorrí cada vista campo por campo. Regla establecida (**RN-23**): **todo campo se edita en su vista**, salvo que sea **(a) dato de otra superficie** (entonces es read-only aquí + **tooltip dice dónde se edita**) o **(b) calculado** (read-only + tooltip "se calcula solo"). Marqué los hallazgos y los **arreglé en los mockups**.
>
> ★ 2026-06-15 — esta auditoría (editable / dónde-se-edita) la **complementa `§ Mapa de campos`** (entidad · por qué · tooltip · átomo/molécula/token por campo). Las dos juntas = el contrato completo para `/architect`.

| Vista | Campo | ¿Editable aquí? | Si no — dónde se edita / nota |
|---|---|---|---|
| **Resumen** | Nombre · Especialidad · **Peldaño** · Descripción · Qué incluye/no · Variantes · Garantía · Duración/sesiones · Resultado · Preparación · Cuidados · Cita inicial · Recurrente | ✅ editable aquí | **★ FIX:** estaban como texto read-only en Identidad → ahora **inputs/selects editables** (autosave). Peldaño también se mueve por drag en **Escalera**. |
| **Resumen** | Especialidad / categoría (opciones del dropdown) | ✅ eliges aquí | **★ tooltip:** las **opciones** salen del **tipo de clínica** (Onboarding · editable en Lisa → Marca). |
| **Resumen** | Tono/voz de la descripción | la descripción ✅; el **tono** no | **★ tooltip:** el estilo lo toma de **Lisa → Marca** (voz de marca). |
| **Para Adrián** | Candidato · contraindicaciones · escalada · preguntas · beneficios · dolor · diferenciadores · ganchos · FAQ (pares) · objeciones (pares) · palabras clave · problemas · lenguaje a evitar | ✅ editable aquí | (FAQ/objeciones = listas de pares editables; alimentan el KB del agente). |
| **Especialistas** | Vínculo servicio↔especialista (marcar/desmarcar) | ✅ aquí (autosave) | — |
| **Especialistas** | Nombre · especialidad · **credenciales** del especialista | ❌ read-only aquí | **★ nota + "Ver detalle ↗":** se editan en **Lisa → Especialistas** (roster `lisa-doctores`). |
| **Plan de pago** | Precio (monto) · Modo · "Adrián dice el precio" · Reserva (monto/tipo/pide) · Anticipo (% o monto/ofrece) · Cuotas · Interés · Medios · Socio financiero | ✅ editable aquí | — |
| **Plan de pago** | **Moneda (S/)** | ❌ read-only aquí | **★ FIX:** la separé del monto + **tooltip:** sale de la **config de tu clínica** (tenant_locale · Configuración → Cuenta/Localización). |
| **Plan de pago** | **≈ equivale a** (anticipo) · **≈ por mes** (cuotas) | ❌ calculado | **★ tooltip "se calcula solo"** (del % + precio + reserva). |
| **Prueba social** | Fotos antes/después · testimonios · casos | ✅ editable aquí | (el consentimiento de las fotos lo gobierna Compliance — fuera de scope). |
| **Fuentes & conocimiento** | Documentos cargados · toggle "Adrián consulta" | ✅ aquí | estado extraído/indexado = del sistema (read-only). |
| **Catálogo (tarjetas)** | toggle Activo | ✅ inline | el resto de la tarjeta = resumen read-only (se edita entrando al servicio). |

**Hallazgos arreglados en los mockups esta ronda:** (1) Identidad de Resumen era read-only → editable. (2) Moneda incrustada en el precio → separada + read-only con tooltip de origen. (3) Campos calculados sin señal → tooltip "se calcula solo". (4) Datos del especialista → nota explícita "se editan en Lisa → Especialistas". (5) Especialidad/voz → tooltip de origen.

## § Modelo de conocimiento del servicio (★ Chris round 3 · "el form es muy pesado, que el sistema agéntico facilite")

> Problema que planteó Chris: un servicio tiene ~55 campos posibles (24 must-have). Llenarlos a mano = pesado, anti-agéntico. La idea de un equipo de agentes es **facilitar el trabajo**, no dar un formulario gigante.

**Mi propuesta — invertir el flujo: de "llená el formulario" a "dale material, Lisa lo arma, vos revisás".**

1. **Panel "Fuentes & conocimiento" — persistente y colapsable** (NO un paso de onboarding que desaparece · vive arriba del workspace, visible en crear y editar). La dueña arrastra el material del servicio **una vez**: folleto · lista de precios · protocolo · ficha técnica · enlace web · (a futuro) una conversación.
2. **Lisa procesa → doble uso del mismo documento:**
   - **(a) Autocompleta los campos** (extracción): los campos de las 5 pestañas se **pre-llenan** y quedan **editables**, marcados con **✨ + de qué fuente salió** (la dueña revisa lo marcado, no escribe de cero).
   - **(b) Queda como conocimiento de Adrián** (RAG): para preguntas libres del paciente que los campos estructurados no cubren. Toggle por fuente: "Adrián la consulta" on/off.
3. **Los campos estructurados se quedan** — son la capa **curada y de alta precisión** que Adrián usa para lo crítico (precio, contraindicaciones, candidatura). El RAG es el **complemento** para la cola larga. **El precio nunca sale del RAG** (sale del campo, anti-staleness).
4. **El trabajo de la dueña se encoge a revisar + curar**, no tipear. Autoguardado siempre (RN-20).

```
  [ 📚 Fuentes & conocimiento ]  ← persistente, colapsable
        │  arrastra folleto / precios / protocolo / enlace
        ▼  "Procesar con Lisa"
   ┌────────────┬─────────────────────────────┐
   ▼ (a) extrae                          (b) indexa ▼
  campos pre-llenados (✨ editable)      RAG de Adrián (comercial · scope+safety RN-22)
   │  la dueña REVISA                      │  preguntas libres del paciente
   ▼                                       ▼
  capa curada (precio/contra/candidatura = SSoT)   complemento cola larga
```

**Por qué esto sí es agéntico:** la dueña no enfrenta 24 campos vacíos; suelta un folleto y corrige lo que Lisa armó. Es el diferenciador (ningún competidor conecta material → catálogo vendible + agente que consulta).

**⚠️ Esto agranda la story (Chris lo ratificó · "historia más grande pero necesaria"). ★ Chris round 3: TODO ACÁ — A (autocompletar) + B (RAG) en esta misma story, junto, no se parte.** Suma: ingesta `KnowledgeSource` (extraer **+** indexar) + un **tool de retrieval del sales_agent** que HOY **no existe** + el indexer Qdrant que HOY es **STUB**. → **Dependencia HARD de lift de engine (`/pm-luana`)** dentro del alcance de esta story: el indexer real + el retrieval tool del sales_agent son engine y deben landear para que B se vea live. `/architect` la dimensiona como parte del ready package (no como story aparte).

## § Diferenciación por vertical — dental vs estética (★ Chris #3 · mi recomendación UX)

> Pregunta: ¿cómo tratamos una clínica **dental** vs una **estética**? ¿cambia algo en los servicios?

> **★ ¿Dónde se declara la especialidad? (Chris round 3) — son DOS cosas distintas:**
> - **Especialidad de la CLÍNICA** (qué tipo de centro es: dental cosmético · medicina estética · multi-especialidad) = **atributo del tenant**. **NO se crea aquí.** **★ RATIFICADO Chris 2026-06-07: se crea en el Onboarding (set once) y se edita en Lisa → Marca.** **Servicios lo CONSUME** (read-only) para presets + ejemplos del rung-picker + opciones del dropdown. → capturado como story propia **`vitalia-fase2-marca-especialidad-clinica`** (idea · pendiente `/pm-vitalia`); servicios solo lo lee (dependencia soft).
> - **Especialidad/categoría del SERVICIO** (este servicio es odontología, ese otro estética) = **per-servicio · sí vive aquí** (campo del § Modelo). El dropdown se **alimenta** de las especialidades declaradas de la clínica (un centro multi-especialidad tiene servicios de varias).

**Mi recomendación: NO forkear la UI. Un servicio es un servicio — la estructura es la misma. Lo que cambia es el CONTENIDO, derivado del vertical del tenant.** El vertical (dental / estética / dermatología / …) es un **atributo del tenant** (se fija en marca/onboarding — "tipo de clínica"), NO un campo por-servicio ni una UI distinta. Razón: forkear la UI por vertical multiplica superficie + mantenimiento sin valor; los competidores que vimos no lo hacen. La adaptación vive en los **datos y las sugerencias**, donde sí aporta:

| Qué adapta el vertical | Cómo |
|---|---|
| **Seed presets** (ya en scope) | dental: evaluación→limpieza→diseño/implante→carillas→mantenimiento · estética: valoración→peeling→botox/fillers→paquete→mantenimiento trimestral |
| **Ejemplos del selector de peldaño** | el rung-picker muestra ejemplos del vertical (dental: "diseño de sonrisa, implante" · estética: "botox, peeling") |
| **Opciones de especialidad** | el dropdown se filtra al vertical del tenant |
| **Sugerencias de Lisa** (descripción · FAQ · objeciones) | redactadas con sabor del vertical + voz de marca |
| **Énfasis natural** (no campos distintos, mismos campos con peso distinto) | estética → recurrencia (botox c/4-6m) + antes/después + downtime · dental → paquetes/garantía + financiamiento largo (implantes) |

**Qué NO hago:** campos exclusivos por vertical, pantallas separadas, lógica condicional de UI por tipo de clínica. Mismos 5 leaves, mismos campos.

**★ Alternativa mejor que pediste (#4 · ejemplos más acertados a la especialidad, sin forkear):** en vez de un switch grueso dental/estética, usar la **especialidad/sub-vertical declarada del tenant como CLAVE** de dos cosas:

1. **Catálogo de hints por sub-vertical (engine):** hoy el engine tiene UNA fila genérica `PROFESIONAL_SALUD` en `OFFER_LADDER_HINTS`. **Propongo expandirla a filas por sub-vertical** (odontología-cosmética · medicina-estética · oftalmología · dermatología · …) → el selector de peldaño y los seed presets muestran ejemplos del sub-vertical exacto, no genéricos. (Refinar el engine → `/pm-luana`.)
2. **Ejemplos GENERADOS por Lisa, condicionados a la clínica (más agéntico y más preciso que cualquier tabla):** los ejemplos y sugerencias (qué va en cada peldaño, descripción, FAQ, objeciones) los **genera Lisa** a partir de **(especialidad + el catálogo real que ya tiene la clínica + voz de marca)**. Una tabla estática nunca le pega tan bien como un modelo que mira el contexto real del centro. Los seed presets estáticos son solo el **cold-start** (clínica sin nada); apenas hay especialidad + 2-3 servicios, Lisa adapta los ejemplos a ESA clínica.

→ **Resultado:** ejemplos cada vez más acertados a la especialidad, **sin** una UI distinta por vertical. Capa 1 (hints por sub-vertical) = engine. Capa 2 (Lisa genera) = capa agéntica de Lisa. En el **MVP** de esta UI alcanza con: especialidad declarada + seed presets dental/estética + rung-picker que ya lee la especialidad; las capas finas se profundizan en engine + Lisa.

**★ Cómo se ve cuando hay un "tipo de clínica" (Chris round 3 · placeholders · RN-24):** la **misma pantalla** muestra **placeholders/ejemplos orientados al tipo**. Demo interactivo en **`nuevo-servicio.html`** (botones `🦷 Odontología | 💉 Estética`): al cambiar el tipo cambian los placeholders del nombre ("Ej: Diseño de sonrisa" ↔ "Ej: Botox preventivo"), de la descripción, de "qué incluye", las **opciones del dropdown de especialidad**, y los **ejemplos del selector de peldaño** ("diseño de sonrisa, implante" ↔ "botox, rellenos, peeling"). En producción el tipo NO es un toggle: sale del **atributo de clínica** (Onboarding/Marca) y el usuario ve directamente lo de su tipo. Cero pantallas distintas — solo el texto de ayuda se adapta.

## § Recomendación #9 — documentos → RAG para Adrián (research · esperando tu decisión)

> Chris pidió: averiguar + recomendar si debería poder **"Cargar" documentos** en algún lugar para que entren al **RAG** y Adrián responda consultas libres.

> **★ RESUELTO en parte por Chris #1 (2026-06-07):** hay **dos features de "documento" distintas** — hay que separarlas:
> - **(A) Documento → AUTOCOMPLETAR campos** (lo que pediste en #1): subir material → extraer → **pre-llenar los campos editables** del servicio. Es **one-shot**, la dueña revisa, NO se indexa. **El engine YA lo hace** (copilot `document_processor`: parse → LLM extraction → merge a campos). **Bajo riesgo · ENTRA en esta story** (RN-17/AC-11). `/architect` confirma el wiring para offers de vitalia.
> - **(B) Documento → RAG runtime** (la consulta libre de Adrián sobre el PDF): el agente responde leyendo el documento en vivo. **Esto es lo que recomiendo DIFERIR** (abajo). Indexer Qdrant del engine = STUB; precio/contraindicaciones en PDF = staleness + riesgo; PHI → HIPAA-lite.
>
> O sea: **sí a cargar documentos** (para autocompletar · A) en esta story; **no todavía** a que el agente conteste libremente desde ellos (B).

**Qué encontré (estado del engine, 2026-06-07):**
- El conocimiento de Adrián HOY se arma **solo de data estructurada** (`TenantKnowledgeBuilder`: offers + marca + personalidad + FAQ/objeciones). NO hay pipeline de ingesta documento→chunk→embedding vivo.
- El engine **ya tiene el esqueleto**: Offer Studio tiene una entidad `KnowledgeSource` + endpoint `/{offer_id}/knowledge/upload` (PDF/DOCX/URL) **por offer** — pero el indexer Qdrant real es un **STUB** (no indexa). O sea: el gancho existe, el motor no está conectado. Conectarlo = trabajo de **engine (`/pm-luana`)**, no de esta UI-story.
- Qdrant para sales_agent existe a nivel infra, pero **ningún tool del agente lo consulta** todavía.

**Qué dice el best-practice (2025-26 · Intercom Fin · Ada · Sierra · clinical AI):**
- Para un agente de **venta**, los **campos estructurados curados** (FAQ pares, objeciones, contraindicaciones) son **mejor** que volcar PDFs: más precisión, cero chunking roto, sin drift.
- Los **2 datos más peligrosos** en PDF acá: **precio** (se pone stale apenas cambia una promo) y **contraindicaciones** (riesgo clínico/legal si el agente responde mal).
- Los PDFs clínicos (consentimientos, protocolos) **traen PHI casi seguro** → ingestarlos sin un scrub de PHI viola HIPAA-lite.
- El patrón bueno cuando se ofrece: **base de conocimiento a nivel tenant** (no adjunto por-servicio), **copilot-interno primero**, con freshness + scoping de qué agente la ve.

**Mi recomendación (vos decidís):**
1. **NO** meter "subir documentos → RAG" en el **MVP** de este catálogo. Los campos estructurados que ya diseñamos (Para Adrián: FAQ, objeciones, contraindicaciones, palabras clave) **son** el substrate de RAG, mejor y más seguro.
2. Hacerlo como **story aparte, a nivel tenant** ("Base de conocimiento de la clínica"), **copilot-interno primero** (protocolos/SOP con scrub PHI), y recién después exponer al sales_agent **solo contenido comercial** (folletos, post-cuidado sin PHI) con freshness + escalada en preguntas clínicas.
3. Requiere **lift de engine** (`/pm-luana`): conectar el indexer real (hoy STUB) + un tool de retrieval para el agente.

**★ DECIDIDO (Chris round 3, 2026-06-07): A + B TODO EN ESTA STORY (junto, no se parte).** Mi recomendación de diferir queda **superada** — pero **conservo las guardas** no-negociables (RN-22): RAG solo comercial · precio siempre del campo (no del PDF) · clínico escala al doctor · scrub PHI en ingesta. El **cómo** (modelo dual documento→extrae+indexa) está en **§ Modelo de conocimiento**. La **dependencia de engine-lift** (`/pm-luana`: indexer Qdrant real hoy STUB + tool de retrieval del sales_agent hoy inexistente) es **parte del alcance** → `/architect` la dimensiona en el ready package.

## § Biblioteca de servicios estándar + ficha completa de paciente (★ DELTA Chris 2026-06-12 · ✅ RATIFICADO 4/4 — INTEGRADO al cuerpo: § Modelo + § Workspace/Resumen + § Mapa funcional + RN-25/26/27 + AC-7/9/18/19 + § Componentes + § Pendientes. Esta sección queda como registro de la decisión.)

> Pedido Chris (reanudación, 2026-06-12): (1) servicios **asociados al tipo de centro**; (2) NO una plantilla de UI por tipo, sino una **base de servicios disponibles** por tipo de clínica — la dueña elige de la lista y si no está, lo agrega — para **estandarizar nombres** (evitar "ponerle nombres de un servicio a otro"); (3) **toda la información disponible para el paciente**: cómo se hace, riesgos, etc. Research: Fresha/Booksy = menú 100% libre sin lista maestra (el caos de nombres es real, esto es diferencial) · RealSelf = estructura canónica de ficha de tratamiento paciente-facing (qué es / cómo funciona / candidatos / qué esperar / riesgos / recuperación / costo / resultados).

### Concepto — Biblioteca de servicios estándar

Una **biblioteca curada por-vertical** (keyed por el **tipo de clínica** del tenant — story `marca-especialidad-clinica`): entradas canónicas finitas (odontología ≈ 40-60 servicios reales, estética ≈ 30-50). Cada entrada = **plantilla de contenido**, NO una UI distinta (RN-19 intacta — misma estructura, distinto contenido):

| Campo de la entrada canónica | Para qué |
|---|---|
| nombre canónico + **sinónimos** ("carillas" = "fundas" = "arreglarme los dientes") | estandarización + match RN-16 de Adrián pre-llenado |
| categoría/especialidad + **peldaño sugerido** (`value_level`) | clasificación consistente |
| descripción base (lenguaje paciente) | pre-fill editable |
| **cómo se hace** (pasos) · anestesia/dolor · duración típica · nº sesiones típico | pre-fill ficha procedimiento |
| **riesgos y efectos secundarios** base · preparación · cuidados posteriores · downtime típico | pre-fill seguridad/recuperación |
| FAQ skeleton + objeciones típicas | pre-fill Para Adrián |

**Dónde vive (anti-dup):** data de **Offer Studio preset pack EP-2** (mecanismo ya diseñado — `ExpertBusinessType`/presets del engine; CERO edit engine). Tabla brand-level vitalia read-only para tenants; `/architect` concreta. Nota: Chris la llamó "BS" — interpretado como **base de servicios**; técnicamente es dominio Offer Studio (no Brand Studio).

### Flujo "+ Nuevo servicio" v3 (reemplaza el aterrizaje directo al workspace vacío)

1. **+ Nuevo servicio** → **paso picker**: typeahead sobre la biblioteca del tipo de clínica (busca por nombre canónico **y sinónimos**). Resultado muestra: nombre + categoría + peldaño sugerido.
2. **Lo encuentra** → "Usar esta plantilla" → workspace creado **PRE-LLENADO** (campos plantilla marcados ✨ con origen "biblioteca", todos editables) → la dueña completa **lo suyo**: precio, duración real, especialistas, cobros. Tipeo mínimo.
3. **No lo encuentra** → "Crear servicio personalizado" → workspace vacío (flujo actual: doc-autocomplete RN-17 o a mano). El servicio queda `origen: personalizado`.
4. Todo servicio guarda su **vínculo a la entrada canónica** (`canonical_service_ref`, null si personalizado) → estandarización real: reportes comparables + Adrián entiende el servicio aunque la dueña le cambie el display-name.
5. El **empty-state "seed presets"** (Bif `happy-seed`) se **absorbe**: el seed ES la biblioteca ("agrega tus primeros servicios desde la biblioteca").

### Campos NUEVOS por vista (delta sobre lo firmado — el resto NO cambia)

**Workspace → Resumen** (reagrupado en cards):
- Grupo Identidad: + chip **"Servicio estándar: {nombre canónico}"** read-only (tooltip RN-23: "estandariza el nombre — viene de la biblioteca") o "Personalizado".
- **Grupo NUEVO "El procedimiento"** (paciente-facing): 🔴 **cómo se hace** (pasos numerados, lenguaje paciente) · 🟡 **anestesia / manejo del dolor** · (absorbe los ya-firmados: duración sesión 🔴 · nº sesiones 🔴 · preparación previa 🟡 · cuidados posteriores 🟡 · downtime 🟡).
- **Grupo NUEVO "Riesgos"** (paciente-facing): 🔴 **riesgos y efectos secundarios** (lista) · 🟡 **señales de alarma post-tratamiento** ("si pasa X, contacta a la clínica").
- Grupo Resultados: sin campos nuevos (ya firmados).

**Workspace → Para Adrián:** sin campos nuevos; **sinónimos/palabras-clave llegan PRE-LLENADOS** desde la biblioteca (el match RN-16 arranca con base). Riesgos curados: Adrián **puede citarlos textual** (capa de alta precisión); interpretación clínica libre **escala al doctor** (extiende RN-22).

**Catálogo (grid):** 🟡 chip origen "Estándar/Personalizado" en la card + 🟡 filtro origen. Resto igual.

**Escalera:** sin cambios de campos; los **ejemplos de peldaño vacío** ahora salen de la biblioteca (antes: generados).

**MVP must-have: 24 → 26 campos** (+ cómo se hace · + riesgos).

### RN nuevas (post-aprobación se integran arriba)

- **RN-25 (estandarización)** · Crear servicio arranca en el **picker de la biblioteca** (typeahead nombre+sinónimos). Servicio desde plantilla guarda `canonical_service_ref`. Personalizado permitido siempre (la biblioteca ayuda, no bloquea).
- **RN-26 (ficha de paciente completa)** · El servicio publica info completa paciente-facing: cómo se hace · riesgos · preparación · cuidados · downtime · resultados. Pre-llenada desde la biblioteca cuando hay plantilla; siempre editable; los campos de seguridad (riesgos) son capa curada (Adrián cita textual, no interpreta — RN-22).
- **RN-27 (personalizado → candidatura)** · Servicio personalizado queda **solo en la clínica** (MVP). Flag interno "candidato a biblioteca" para curaduría nuestra periódica — NO entra automático a la biblioteca global (calidad > volumen). *(decisión b abierta)*

### Decisiones que Chris aprueba/ajusta (gate del mockup)

1. **Flujo picker-primero** ("+ Nuevo" → biblioteca → plantilla o personalizado) — ¿OK?
2. **Personalizado:** recomendación = solo-clínica + candidatura interna curada (NO auto-publicar a biblioteca global). ¿OK?
3. **Completitud sin bloqueo:** activar un servicio NUNCA se bloquea por ficha incompleta; en su lugar **indicador de completitud** en el workspace ("ficha 22/26 · faltan: riesgos, cómo se hace"). ¿OK, o preferís bloquear "Activo" sin los 🔴?
4. **Seed inicial:** biblioteca curada para **odontología + medicina estética** (Tier 1), contenido generado por Lisa + curado, como data del preset pack. Otras verticales después. ¿OK?

## Próximo paso
**✍ FIRMA 1 (intención)** sobre este § Mapa funcional + § Modelo → luego mockups per-component (catálogo card · escalera canvas · workspace servicio · drawer peldaño) con fidelidad de shell (ADR-003) → **✍ FIRMA 2** → RONDA 2 (Gherkin + matriz de cobertura) → transition refining→refined.

> ★ 2026-06-12: FIRMA 1 dada (2026-06-06) + switcher `EntityPicker` confirmado. Pendiente: aprobación del § DELTA biblioteca/ficha-paciente (arriba) → integrar al cuerpo → refresco de los 4 mockups (canon `@luana/ui-kit`: `EntityWorkspaceLayout` + `EntityPicker` + `EntityInfoCard` + picker biblioteca) → **✍ FIRMA 2** → RONDA 2.
>
> ★ 2026-06-15: mockups iterados + **visto-bueno visual de Chris ("queda")**. Spec reconciliado con la sesión (modalidad RN-28 · variantes RN-29 · herencia bloqueada RN-30 · numéricos RN-31 · RichSelect/tipo-cita RN-32 · prueba social manual RN-33) + agregados **§ Mapa de campos** y **§ Inventario de componentes** (campo→entidad→por qué→tooltip→átomo + contratos de primitivas nuevas). **Falta SOLO para `refined`:** (1) tu ✍ FIRMA 2 formal · (2) **RONDA 2 ejecutable** = § Gherkin (scenarios `@rule` por RN) + § Matriz de cobertura (Bif/RN→SC→verificación) — la genero apenas confirmes. Luego `refining → refined` → handoff `/architect`.
