---
story_id: vitalia-fase2-mateo-nueva-cita
brand: vitalia
type: ui-story
state: refined
architecture_pattern: ADR-vitalia-004
po_ux_version: 2
ronda: 2                       # FIRMA 2 ✍ mockup_final_signed (Chris 2026-06-22) → Gherkin+matriz generados
input_spec_signed: true
mockup_final_signed: true
ratified_by_chris: true
---

# 01-spec — Nueva cita usable (D11)

> RONDA 1 (funcional). Mockup + Gherkin se GENERAN tras la FIRMA 1. Origen: live-QA D11 de `vitalia-scheduling-mateo-review`.

## § Context — dónde vive

- **Zona/caja:** Agentes → **Mateo** (Operar) → área `mateo.agenda`.
- **Shell / contenedor (decidido 2026-06-21 · investigación de contenedor):** **hoja full-page (leaf)** en ruta `/{tenantId}/mateo/agenda/nueva-cita`, dentro del shell-organism. Se entra desde un **botón de acción "+ Nueva cita"** (toolbar de Agenda + click en slot vacío) — NO un drawer, NO un sub-tab de navegación (un verbo/acción no va como tab; un drawer pierde datos al click-afuera). La hoja tiene **Guardar/Cancelar explícitos + back-pill "‹ Agenda"**. Patrón Google Calendar "Más opciones" (escala a página); consistente con el modelo árbol+hojas; data-safe por construcción. Ver `00-research-availability.md` (no aplica) → la investigación de contenedor está en el chris-input + esta decisión.
- **Cap target:** `scheduling.mateo-agenda` (`extend`). Toca además el list DTO de `offer.lisa-servicios` (1 campo).
- **Rol (quién lo usa):** recepción (`admin_clinic`) + médico (`doctor`). Ambos con acceso PHI (`@require_phi_access`).
- **Naturaleza:** funcional (writes reales + reglas de negocio) → live-verify obligatoria.

## § Mapa funcional

### Happy path

1. El operador toca **"+ Nueva cita"** (toolbar de Agenda, o click en un slot vacío) → entra a la **hoja Nueva cita** (full-page, back-pill "‹ Agenda"). Si entró por un slot, fecha/hora vienen prellenadas.
2. **Paciente:** typeahead que busca **existentes primero** (devuelve `patient_id`). Si no existe → **"+ Crear paciente"** expande un **mini-form inline DENTRO del picker** (nombre + teléfono requeridos, email opcional). "Crear y elegir" → crea un **registro real mínimo** en `vitalia_patients` → colapsa con el paciente preseleccionado, **sin salir del form de la cita**. No es descartable (queda en el directorio D10, donde se enriquece el perfil completo). NO es popup ni hoja aparte.
3. **Servicio:** dropdown del catálogo de servicios activos (`offer.lisa-servicios`). Al elegirlo trae su **duración** (`initial_appt_duration_minutes`).
4. **Fecha + hora de inicio:** entrada manual. La **hora de fin** se autocalcula = inicio + duración (editable; si se edita debe ser > inicio).
5. **Médico:** dropdown de médicos activos de la clínica. Al quedar definidos {médico, fecha, hora, duración} aparece un **chip de disponibilidad live**: `Disponible` · `Ocupado — se solapa con [cita]` · `Fuera de horario`. Junto al médico se muestra una **mini-vista del día** de ese médico (franja horaria con sus bloques de atención + citas ocupadas + la franja nueva propuesta resaltada) para que el operador elija una hora buena de un vistazo.
6. Si el chip NO es `Disponible` → el form ofrece **"Médicos disponibles a esta hora"** (los activos que están dentro de horario y libres para esa franja) → 1 clic reasigna y re-chequea. (O el operador cambia la hora — la mini-vista lo guía.)
7. Con chip `Disponible` → **Crear**. El backend garantiza no-solape; éxito → toast "Cita creada" + se cierra + la grilla la refleja.

### Bifurcaciones (árbol)

```
Crear cita
├─ ¿hay servicios activos en el catálogo?
│   ├─ no → estado vacío: "No hay servicios. Cargalos en Mi Clínica › Servicios" (no se puede crear) [SC-empty-servicios]
│   └─ sí → sigue
├─ servicio elegido ¿tiene duración configurada?
│   ├─ no (null) → default 30 min + editable [SC-dur-default]
│   └─ sí → usa la del servicio
├─ ¿hay médicos activos en la clínica?
│   ├─ no → estado vacío: "No hay médicos activos" (no se puede crear) [SC-empty-medicos]
│   └─ sí → sigue
├─ médico elegido ¿tiene horario cargado para ese día?
│   ├─ no → chip "Sin horario cargado" → BLOQUEA + "cargá el horario de este médico primero" [SC-sin-horario]
│   └─ sí → evalúa la franja {hora, duración}:
│       ├─ fuera del horario de atención → chip "Fuera de horario" → BLOQUEA + sugiere reasignar/cambiar hora [SC-fuera-horario]
│       ├─ se solapa con otra cita activa del médico → chip "Ocupado — se solapa con [cita]" → BLOQUEA + "Médicos disponibles a esta hora" [SC-solape]
│       └─ dentro de horario y libre → chip "Disponible" → habilita Crear [SC-happy]
├─ al Crear, otro operador acaba de tomar la franja (carrera) → 409 "Ese horario acaba de ocuparse, elegí otro" [SC-race]
├─ fin ≤ inicio (override manual) → validación inline [SC-fin-invalido]
└─ paciente nuevo sin nombre/teléfono → validación inline [SC-paciente-incompleto]
```

### Reglas de negocio

- **RN-1** — No se permite solape de citas **activas** (status ≠ CANCELLED) del mismo médico. Bloqueo DURO, garantizado a nivel DB (constraint EXCLUDE). Es el invariante central.
- **RN-2** — Intervalos **half-open**: back-to-back NO es solape (10:00–10:30 y 10:30–11:00 conviven).
- **RN-3** — Una cita solo se crea si el médico está **dentro de su horario de atención** para esa franja (fuera de horario = bloqueo).
- **RN-4** — Médico **sin horario cargado** → no se puede agendar (bloqueo accionable).
- **RN-5** — La **duración** sale del servicio (`initial_appt_duration_minutes`); `null` → 30 min. Hora-fin = inicio + duración (editable, > inicio).
- **RN-6** — CANCELLED no cuenta como conflicto (su franja se libera).
- **RN-7** — Solo roles `admin_clinic` y `doctor` crean. PHI: dual filter tenant+clinic + audit log sync.
- **RN-8** — Tiempos en UTC; se muestran/ingresan en la zona horaria del tenant (IANA). DST seguro (compara instantes absolutos).
- **RN-9 [PROPUESTO 2026-06-22 · confirmar Chris/architect]** — Al crear paciente inline, si el teléfono coincide con uno existente (mismo tenant+clinic) → NO crear duplicado: ofrecer "Ya existe {nombre} con ese teléfono · ¿usar ese?". Guard liviano de calidad de datos PHI (evita pacientes duplicados por typo en el typeahead). Si se descopa → fast-follow; el resto de la story no depende de RN-9.
- **RN-10** — La disponibilidad (chip + mini-vista) es **advisory**: la garantía dura es el constraint DB `EXCLUDE` + la validación in-horario en `create_appointment` (server-side). UI fail-**closed** sobre el chip (si no se pudo verificar → no habilita Crear), pero un POST directo que saltee la UI igual lo rechaza el server.

### Criterios de aceptación

- **AC-1** — El médico se elige de un dropdown de médicos activos (nunca se tipea un UUID).
- **AC-2** — El servicio se elige de un dropdown del catálogo activo (nunca texto libre).
- **AC-3** — La hora de fin se autocalcula desde inicio + duración del servicio (editable).
- **AC-4** — El form muestra disponibilidad del médico (chip) y bloquea solape y fuera-de-horario.
- **AC-5** — Cuando el médico no está disponible, el form ofrece médicos disponibles a esa hora y permite reasignar en 1 clic.
- **AC-6** — Dos creaciones concurrentes de la misma franja: una gana, la otra recibe error claro y reintenta.
- **AC-7** — Crear una cita válida la persiste y la grilla de la agenda la muestra (live-verify real).
- **AC-8** — El form muestra una mini-vista del día del médico elegido (bloques de atención + citas ocupadas + la franja nueva resaltada).
- **AC-9** — "Nueva cita" es una hoja full-page (no drawer, no sub-tab): se entra desde "+ Nueva cita", tiene back-pill + Guardar/Cancelar, no pierde datos por click-afuera.
- **AC-10** — El paciente nuevo se crea **inline dentro del picker** (sin salir del form de la cita): registro real mínimo (nombre+teléfono), no descartable, queda en el directorio D10. No es popup ni hoja aparte.

## § Pantallas (campos — sin mockup todavía)

**Hoja full-page** `/{tenantId}/mateo/agenda/nueva-cita` (back-pill "‹ Agenda", FormLayout del canon). Orden funcional:

| Campo | Origen del dato | Tipo control (mockup definirá) | Requerido | Validación |
|---|---|---|---|---|
| Canal de ingreso | enum walk_in / telefono | segmented | sí | uno de 2 |
| Paciente | typeahead `GET patients` **existing-first** → `patient_id`; **"+ Crear paciente"** → mini-form inline en el picker (nombre+tel) → `POST patients` registro mínimo real → preseleccionado, sin salir | `EntityPicker` con `createAction` inline | sí | patient_id uuid |
| **Servicio** | `GET /offer/servicios` (activos) | **dropdown** (Select canónico) | sí | del catálogo |
| Duración | `servicio.initial_appt_duration_minutes` (null→30) | número min (prellenado, editable) | sí | ≥ 1 |
| **Fecha + hora inicio** | manual | datetime | sí | fecha/hora válida |
| **Hora fin** | autocalc inicio+duración | datetime read-only (editable override) | sí | > inicio |
| **Médico** | `GET /clinics/.../doctors` (activos) | **dropdown** (Select canónico) | sí | del roster |
| Disponibilidad | endpoint nuevo (médico+franja) | chip live (no editable) | — | Disponible para habilitar Crear |
| Mini-vista día del médico | endpoint disponibilidad (bloques + citas del día) | franja horaria read-only (libre/ocupado + slot nuevo resaltado) | — | — |
| Médicos disponibles | endpoint nuevo (franja → médicos libres) | lista accionable (aparece si bloqueado) | — | — |
| Notas internas | input | textarea | no | ≤ 500 |

### Notas técnicas (el architect las concreta)
- **BE-1** Exponer `initial_appt_duration_minutes` en `ServiceListItemDTO` (hoy solo en detail).
- **BE-2** Endpoint disponibilidad: dado (doctor_id, fecha, hora, duración) → `{status: available|busy|out_of_hours|no_schedule, conflict?}`; y "médicos libres en franja". Reusa `vitalia_availability_slots` + bloques + citas activas.
- **BE-3** Constraint `EXCLUDE USING gist` (btree_gist, tstzrange, partial `WHERE status<>CANCELLED`) en `vitalia_appointments` → garantía anti-solape. Migración idempotente.
- **BE-4** `create_appointment`: validar dentro-de-horario antes de insert; capturar `23P01` → 409. (Arregla el bug latente: walk-in/teléfono hoy no protege.)
- **BE-5** Dropdown médicos: endpoint ya existe.
- **BE-6** Alta de paciente **inline mínima**: `POST patients` con {nombre, teléfono, email?, canal} → registro real en `vitalia_patients` (mismos tenant+clinic + audit). NO requiere los campos PHI completos de D10 — el perfil se enriquece después en `mateo-pacientes`. Misma entidad/tabla que D10 (dep suave: comparten `vitalia_patients`, no la superficie UI).
- **BE-7** Reconciliar el enum `origin`: hoy `walk_in/telefono/existing_patient` acopla origen con existencia del paciente. Con typeahead+crear, la existencia es ortogonal → `origin` queda como **canal** (`walk_in/telefono`). El architect concreta la migración del schema (FE `agenda-schema.ts` + BE).

## § Decisiones (FIRMA 1 · Chris 2026-06-21)
- ✅ **Mini-vista del día del médico = IN scope** (franja con bloques + ocupado + slot nuevo resaltado). AC-8.
- ✅ **Buffer entre citas = fuera de scope** (default 0, sin UI).
- ✅ **Contenedor = hoja full-page (leaf)** vía botón "+ Nueva cita" (NO drawer, NO sub-tab). AC-9. Investigación de contenedor ratificada Chris 2026-06-21.
- ✅ **Nuevo paciente = inline en el picker** (`EntityPicker.createAction`): mini-form nombre+teléfono → registro real mínimo, sin salir del form de la cita, no descartable, queda en D10. AC-10. (Chris 2026-06-22 · SUPERSEDES la decisión previa "hoja aparte" — preserva el form de la cita + más rápido para walk-in.) Dep suave D10 (misma tabla `vitalia_patients`).

## § Out-of-scope (anti-creep)
- Overbooking intencional con override (toggle futuro si la clínica lo pide).
- Multi-recurso (sala/equipo) — vitalia no modela salas hoy.
- Modo "cualquier médico disponible" (pooled) — se elige médico explícito.
- Citas recurrentes / series.
- Cobro en la creación (el pago vive en el flujo "cobrar saldo" del detalle).

## § Gherkin scenarios (GENERADO RONDA 2 · FIRMA 2 · 2026-06-22)

> Generados del § Mapa funcional (bifurcaciones + RN + AC) + el mockup FINAL. `Covers:` liga cada SC al mapa. Graders: `e2e` = Playwright autenticado contra dev-app (Rule #37 · write real + efecto + log, NUNCA GET 200); `state_check` = fila/estado DB; `axe` = wcag2aa. Disponibilidad = advisory (RN-10); la garantía dura es el constraint DB (SC-race + SC-bypass son los dientes). Todo SC funcional FE: `playwright_required: true` salvo nota.

### Happy + creación inline de paciente

```
SC-happy · happy
  given: operador admin_clinic en /{tenant}/mateo/agenda/nueva-cita; ≥1 servicio activo; ≥1 médico activo con horario ese día
  when:  paciente existente + servicio (dur 30) + fecha/hora dentro de horario y libre + médico → chip "Disponible" → Crear
  then:  201; fila vitalia_appointments {status SCHEDULED, rango [inicio,fin) half-open, tenant_id+clinic_id, origin=canal, patient_id, doctor_id, service}; audit_log row sync; la grilla de Agenda muestra la cita; toast "Cita creada"
  playwright_required: true
  Covers: [SC-happy, RN-1, RN-5, RN-7, AC-1, AC-2, AC-3, AC-7]

SC-crear-paciente · happy
  given: typeahead de paciente sin resultados para el texto tipeado
  when:  "+ Crear paciente" (inline en el picker) → nombre + teléfono → "Crear y elegir"
  then:  201 paciente: fila vitalia_patients {tenant_id+clinic_id, nombre, teléfono, canal} + audit_log; el picker colapsa con el paciente preseleccionado; el resto del form de la cita queda intacto; el paciente aparece en el directorio Mateo › Pacientes (D10)
  playwright_required: true
  Covers: [AC-10, RN-7]

SC-dur-default · edge
  given: servicio con initial_appt_duration_minutes = null
  when:  se elige ese servicio
  then:  campo "Duración (min)" se prellena 30 (editable); hora-fin = inicio + 30
  playwright_required: true
  Covers: [SC-dur-default, RN-5]
```

### Negative

```
SC-fin-invalido · negative
  given: cita con inicio 09:00
  when:  el operador edita hora-fin a 08:45 (≤ inicio)
  then:  error inline "La hora de fin debe ser posterior al inicio"; Crear deshabilitado; sin POST
  playwright_required: true
  Covers: [SC-fin-invalido, RN-5, AC-3]

SC-paciente-incompleto · negative
  given: "+ Crear paciente" inline expandido
  when:  intenta "Crear y elegir" sin nombre o sin teléfono
  then:  validación inline "El nombre y el teléfono son obligatorios"; sin POST; sin fila en vitalia_patients
  playwright_required: true
  Covers: [SC-paciente-incompleto, RN-7]

SC-paciente-duplicado · negative · [PROPUESTO RN-9 · confirmar Chris/architect]
  given: existe paciente {nombre "Ana Ruiz", teléfono "+51 998 111 222"} en tenant+clinic
  when:  "+ Crear paciente" inline con teléfono "+51 998 111 222"
  then:  NO crea duplicado; ofrece "Ya existe Ana Ruiz con ese teléfono · ¿usar ese?"; al confirmar → preselecciona el existente
  playwright_required: true
  Covers: [RN-9]
```

### Empty states

```
SC-empty-servicios · empty_state
  given: catálogo sin servicios activos
  when:  el operador abre Nueva cita
  then:  estado vacío "No hay servicios. Cargalos en Mi Clínica › Servicios"; no se puede crear (Crear deshabilitado)
  playwright_required: true
  Covers: [SC-empty-servicios]

SC-empty-medicos · empty_state
  given: clínica sin médicos activos
  when:  el operador abre Nueva cita
  then:  estado vacío "No hay médicos activos"; no se puede crear
  playwright_required: true
  Covers: [SC-empty-medicos]

SC-empty-pacientes · empty_state
  given: typeahead de paciente con 0 resultados
  when:  el operador busca un nombre inexistente
  then:  "Sin resultados" + acción "+ Crear paciente" prominente
  playwright_required: true
  Covers: [AC-10]
```

### Disponibilidad — bloqueos + reasignar + mini-vista

```
SC-sin-horario · negative
  given: médico activo SIN horario de atención cargado ese día
  when:  se elige ese médico + fecha
  then:  chip "Sin horario cargado"; Crear bloqueado; CTA accionable "Carga el horario de este médico primero en Mi Clínica › Horarios"
  playwright_required: true
  Covers: [SC-sin-horario, RN-4, AC-4]

SC-fuera-horario · negative
  given: médico con horario 09:00–18:00
  when:  franja propuesta 08:00–08:30 (fuera del horario)
  then:  chip "Fuera de horario"; Crear bloqueado; sugiere cambiar la hora o reasignar a un médico que atienda más temprano
  playwright_required: true
  Covers: [SC-fuera-horario, RN-3, AC-4]

SC-solape · negative
  given: médico con cita activa 09:15–09:45 (status ≠ CANCELLED)
  when:  franja propuesta 09:00–09:30 (se solapa)
  then:  chip "Ocupado — se solapa con [cita 09:15]"; Crear bloqueado; aparece "Médicos disponibles a esta hora"
  playwright_required: true
  Covers: [SC-solape, RN-1, AC-4]

SC-reasignar · happy
  given: chip "Ocupado" con lista "Médicos disponibles a esta hora" (≥1 libre)
  when:  el operador toca "Asignar" en un médico libre
  then:  médico reasignado en 1 clic; el chip re-evalúa → "Disponible"; Crear habilitado
  playwright_required: true
  Covers: [AC-5]

SC-reasignar-vacio · edge
  given: chip "Ocupado" y NINGÚN médico libre en esa franja
  when:  se despliega "Médicos disponibles a esta hora"
  then:  lista vacía + "Ningún médico libre a esta hora; cambiá la hora"
  playwright_required: true
  Covers: [AC-5]

SC-mini-vista · happy
  given: médico elegido con bloques de atención + citas del día
  when:  se define {médico, fecha, hora, duración}
  then:  la mini-vista del día pinta horario de atención + ocupado + la franja nueva resaltada (amarilla); cambiar la hora mueve la franja resaltada
  playwright_required: true
  Covers: [AC-8]

SC-revalida-cambio · edge
  given: chip "Disponible" para {médico A, 09:00, dur 30}
  when:  el operador cambia el servicio (dur 30→60) o la hora → la franja efectiva cambia
  then:  el chip + la mini-vista se re-evalúan sobre la franja nueva (puede pasar a "Fuera de horario"/"Ocupado"); el estado viejo no queda pegado
  playwright_required: true
  Covers: [RN-1, RN-3, RN-5, AC-4]
```

### Edge — half-open, cancelled, carrera, retry, pasado

```
SC-half-open-ok · edge
  given: cita activa 10:00–10:30 del médico A
  when:  se crea 10:30–11:00 del mismo médico (back-to-back)
  then:  201; ambas conviven (intervalos half-open, no es solape)
  playwright_required: true
  Covers: [RN-2]

SC-half-open-block · edge
  given: cita activa 10:00–10:30 del médico A
  when:  se intenta 10:15–10:45 (se pisa)
  then:  bloqueado (chip "Ocupado") y, si se fuerza, 409 del server
  playwright_required: true
  Covers: [RN-1, RN-2]

SC-cancelled-reuse · edge
  given: cita 10:00–10:30 del médico A en status CANCELLED
  when:  se crea otra 10:00–10:30 del mismo médico
  then:  201; la franja CANCELLED no cuenta como conflicto (liberada)
  playwright_required: true
  state_check: { target: db, query: "2 filas mismo rango: 1 CANCELLED + 1 SCHEDULED" }
  Covers: [RN-6]

SC-race · edge · race_condition
  given: dos operadores con la misma franja {médico A, 11:00–11:30} ambos con chip "Disponible"
  when:  ambos tocan Crear casi a la vez
  then:  uno → 201; el otro → 409 (constraint EXCLUDE / 23P01) con toast "Ese horario acaba de ocuparse, elegí otro"; el segundo reintenta con otra hora/médico
  playwright_required: true
  Covers: [SC-race, RN-1, AC-6]

SC-create-timeout-retry · edge · network_failure
  given: el POST create se corta por timeout (respuesta ambigua)
  when:  el operador reintenta la misma creación
  then:  si la 1ª aterrizó → el reintento da 409 "ya creada" (constraint, NO duplica); si no aterrizó → crea normal. Nunca dos filas para la misma franja
  playwright_required: true
  Covers: [RN-1]

SC-pasado · edge
  given: el operador ingresa una fecha/hora en el pasado (registro de un walk-in que ya ocurrió)
  when:  define la franja
  then:  permitido (RN-1/RN-3 siguen aplicando: no solape, dentro de horario); recomendación: NO bloquear el pasado del mismo día
  playwright_required: true
  Covers: [AC-7]
```

### Network failure + concurrencia + dataset grande

```
SC-disponibilidad-falla · network_failure
  given: el endpoint de disponibilidad responde 5xx/timeout mientras se arma la cita
  when:  se define {médico, fecha, hora}
  then:  chip "No pudimos verificar disponibilidad, reintentá"; Crear deshabilitado (fail-closed sobre el chip); botón reintentar
  playwright_required: true
  Covers: [RN-10, AC-4]

SC-concurrent-availability · concurrent_users
  given: dos operadores del mismo tenant+clinic consultan disponibilidad del mismo médico a la vez
  when:  ambos abren Nueva cita
  then:  ambos ven el mismo free/busy consistente (scoped tenant+clinic); la resolución de carrera real al crear es SC-race
  playwright_required: true
  Covers: [RN-1, RN-7]

SC-pacientes-grandes · large_dataset
  given: clínica con 1500+ pacientes
  when:  el operador busca en el typeahead de paciente
  then:  EntityPicker pagina + lazy + render windowed (no carga la colección entera); búsqueda debounced server-side; scroll infinito al final
  playwright_required: true
  Covers: [AC-10]
```

### Accesibilidad + i18n

```
SC-a11y · accessibility
  given: la hoja Nueva cita montada
  when:  navegación 100% por teclado + lector de pantalla
  then:  Tab order lógico; el picker es combobox (↑↓ mueve, Enter elige, Esc cierra); el chip de disponibilidad se anuncia por aria-live al cambiar; focus visible; contraste AA; axe wcag2aa sin violations
  playwright_required: true
  graders: [ { type: axe, ruleset: wcag2aa } ]
  Covers: [AC-4, AC-8]

SC-i18n-tz · i18n
  given: tenant con timezone IANA (ej. America/Lima) y una clínica que cruza un cambio de DST
  when:  se ingresa/visualiza la cita
  then:  horas se ingresan/muestran en la tz del tenant, se persisten en UTC; el cómputo de solape compara instantes absolutos (sin falso solape por DST); strings en español neutro LatAm
  playwright_required: true
  Covers: [RN-8]
```

### Adversarial (AI-resistant · PHI · server-side guarantee)

```
SC-cross-clinic · adversarial
  given: operador de la clínica A (mismo tenant)
  when:  POST create/availability con doctor_id de la clínica B (request manipulado)
  then:  403; sin leak; sin fila creada (dual filter tenant_id+clinic_id · hipaa-lite)
  playwright_required: true
  Covers: [RN-7]

SC-cross-tenant · adversarial
  given: request con tenant A + doctor_id de tenant B
  when:  POST create/availability
  then:  404 (no leak de existencia)
  playwright_required: false
  graders: [ { type: e2e, note: "BE integration test — no UI" } ]
  Covers: [RN-7]

SC-bypass-availability · adversarial
  given: una franja ocupada o fuera-de-horario
  when:  POST create_appointment directo (saltea el chip de la UI)
  then:  el server rechaza igual — 409 (EXCLUDE) si solapa, 422 si fuera de horario; la garantía es server-side, no la UI
  playwright_required: false
  graders: [ { type: e2e, note: "BE integration test" } ]
  Covers: [RN-1, RN-3, RN-10]

SC-rbac · adversarial
  given: usuario con rol fuera de {admin_clinic, doctor} (ej. marketing)
  when:  intenta crear cita
  then:  403 (@require_phi_access)
  playwright_required: false
  Covers: [RN-7]

SC-phi-audit · adversarial
  given: una creación de cita exitosa
  when:  se inspecciona la respuesta + el audit_log
  then:  audit_log row escrito sync ANTES de la respuesta; el response_model NO expone PHI fuera de los campos whitelisted
  playwright_required: false
  Covers: [RN-7]
```

## § Matriz de cobertura

Cada `Bif-N` y `RN-N` del Mapa funcional → ≥1 SC → verificación REAL (acción ejercida + efecto observado, no GET 200).

| Ítem (Mapa funcional) | Tipo | Cubierto por | Verificación REAL |
|---|---|---|---|
| Bif SC-empty-servicios | branch | SC-empty-servicios | abrir form sin servicios → estado vacío + Crear deshabilitado |
| Bif SC-dur-default | branch | SC-dur-default | elegir servicio dur=null → campo 30 editable + fin recalcula |
| Bif SC-empty-medicos | branch | SC-empty-medicos | abrir form sin médicos → estado vacío |
| Bif SC-sin-horario | branch | SC-sin-horario | elegir médico sin horario → chip bloquea + CTA |
| Bif SC-fuera-horario | branch | SC-fuera-horario | franja 08:00 fuera 09–18 → chip bloquea |
| Bif SC-solape | branch | SC-solape, SC-half-open-block | franja pisa cita activa → chip "Ocupado" + lista |
| Bif SC-happy | branch | SC-happy | crear válida → 201 + fila + grilla |
| Bif SC-race | branch | SC-race | 2 creates misma franja → 1×201 + 1×409 |
| Bif SC-fin-invalido | branch | SC-fin-invalido | fin ≤ inicio → error inline, sin POST |
| Bif SC-paciente-incompleto | branch | SC-paciente-incompleto | crear inline sin tel → validación, sin fila |
| RN-1 no-solape activo | rule | SC-solape, SC-race, SC-bypass | POST que solapa → 409 (EXCLUDE), sin 2ª fila |
| RN-2 half-open | rule | SC-half-open-ok, SC-half-open-block | 10:30–11:00 tras 10:00–10:30 → 201; 10:15 → bloqueo |
| RN-3 dentro-de-horario | rule | SC-fuera-horario, SC-bypass | franja fuera → 422 aún por POST directo |
| RN-4 sin-horario | rule | SC-sin-horario | médico sin horario → bloqueo accionable |
| RN-5 duración del servicio | rule | SC-dur-default, SC-fin-invalido, SC-happy | dur del servicio → fin autocalc; override > inicio |
| RN-6 CANCELLED libera | rule | SC-cancelled-reuse | rebook sobre franja CANCELLED → 201 |
| RN-7 RBAC + PHI dual + audit | rule | SC-rbac, SC-cross-clinic, SC-cross-tenant, SC-phi-audit | rol no-autorizado 403; cross-clinic 403; cross-tenant 404; audit row sync |
| RN-8 UTC + tz IANA + DST | rule | SC-i18n-tz | crear cruzando DST → sin falso solape; UTC en DB |
| RN-9 dedup paciente [PROP] | rule | SC-paciente-duplicado | inline create con tel existente → ofrece usar el existente |
| RN-10 disponibilidad advisory | rule | SC-disponibilidad-falla, SC-bypass, SC-race | endpoint cae → Crear fail-closed; POST directo → server rechaza |
| AC-1 médico dropdown | accept | SC-happy | médico de RichSelect (nunca UUID a mano) |
| AC-2 servicio dropdown | accept | SC-happy | servicio del catálogo activo |
| AC-3 fin autocalc | accept | SC-happy, SC-fin-invalido | fin = inicio+dur, editable >inicio |
| AC-4 chip + bloqueo | accept | SC-solape, SC-fuera-horario, SC-sin-horario, SC-revalida-cambio | chip refleja estado + bloquea |
| AC-5 reasignar 1 clic | accept | SC-reasignar, SC-reasignar-vacio | Asignar médico libre → re-eval Disponible |
| AC-6 carrera | accept | SC-race | 2ª creación → error claro + reintento |
| AC-7 persiste + grilla | accept | SC-happy, SC-pasado | fila DB + Agenda la muestra (live) |
| AC-8 mini-vista del día | accept | SC-mini-vista, SC-a11y | franja con bloques + ocupado + slot resaltado |
| AC-9 hoja full-page data-safe | accept | SC-happy, SC-crear-paciente | crear paciente inline no pierde el form |
| AC-10 paciente real inline | accept | SC-crear-paciente, SC-empty-pacientes, SC-pacientes-grandes | fila real en directorio + sin salir del form |

- **Huecos detectados (Bif/RN sin SC):** ninguno.
- **SC huérfanos (SC sin ítem del mapa):** ninguno (SC-concurrent-availability y SC-create-timeout-retry refuerzan RN-1/RN-7; SC-revalida-cambio refuerza AC-4).

## Prior art applied
- **Engine/infra consumido:** `vitalia_availability_slots` + `availability_block_service` + `availability_projection_service` (clinics) para free/busy; `vitalia_doctors` + `GET /clinics/.../doctors` para médicos; `offer.lisa-servicios` (`initial_appt_duration_minutes`, dominio comentado "RN-31 Mateo agenda") para duración; `CrearCitaForm.tsx` + `agenda-schema.ts` (se extiende, no se reescribe).
- **Patrón UX:** Tebra (input manual + chip disponibilidad + reasignar), Jane/Acuity (política de conflicto), Cal.com (reassign). Ver `00-research-availability.md`.
- **Algoritmia/DB:** half-open overlap + Postgres `EXCLUDE`/btree_gist + 23P01→409 (PostgreSQL docs, Cybertec). Ver `00-research-availability.md`.
- **Net-new justificado:** endpoint de disponibilidad para el form + constraint DB (no existían; el bug de doble-booking estaba abierto).
- **Lift candidate:** el cómputo free/busy + la condición de solape podrían lift a `core/luana-core-scheduling` si otra marca agenda con disponibilidad → escalar `/pm-vitalia` en `/architect` (no ahora).
