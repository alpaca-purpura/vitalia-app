<!-- voseo-allowed: handoff interno fix-loop -->
# UX Fix-loop · vitalia-fase2-mateo-nueva-cita · 2026-06-24

> SSoT del fix-loop. Origen: auditoría UX live (Chrome DevTools MCP, dr.demo, :3002) por `/pm-vitalia` 2026-06-24. Chris: "resuelve todo, uno a uno".
> 16 hallazgos. Owner: `builder-frontend` (todo FE brand-local, `vitalia/frontend/src/features/mateo/components/nueva-cita/**`). Cero core, cero otras marcas.
> Verificación: cada fix con su test (TDD donde hay lógica) + **live-verify final obligatoria** (Rule #37) ejerciendo el happy path + el estado afectado. Gates: tsc 0 · eslint 0 · vitest verde · a11y 0.

Tags: `[BUG]`=defecto build · `[DIVERGE]`=build peor que mockup ratificado (`mockups/nueva-cita.html`) · `[DESIGN]`=está en el mockup ratificado (cambio = avisar que diverge de la firma de Chris).

---

## 🔴 HIGH

### H1 · [BUG] "Hora de fin" muestra UTC, no la hora local del tenant
- **File:** `NuevaCitaView.tsx` — helper `isoToHHMM` (~L114) + uso en `endTimeDisplay` (~L291).
- **Síntoma live:** 09:00 + 30min → muestra `12:30` (debería `09:30`). `isoToHHMM` usa `getUTCHours()/getUTCMinutes()` sobre el ISO UTC sin convertir a tz tenant.
- **Fix:** formatear el instante en `timezone` (ya disponible en el componente). Reemplazar el cuerpo por `Intl.DateTimeFormat("es", { timeZone: timezone, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(isoString))`. Pasar `timezone` como arg.
- **También (mismo bug, menor):** `buildIsoFromDateAndTime` (~L91) construye `new Date(\`${date}T${time}:00Z\`)` → interpreta el wall-clock del prefill como UTC. Sólo afecta el path de prefill `?date/?time`. Dejar TODO documentado o normalizar con la misma tz (preferible: mismo util que use SmartDateTimePicker). No bloquear el fix-loop por esto si el prefill no está en scope vivo — pero anotarlo.
- **Test:** unit del helper — `isoToHHMM("2026-06-29T12:30:00Z", "America/Lima")` → `"07:30"` (Lima UTC-5); con `"America/Argentina/Buenos_Aires"` (UTC-3) → `"09:30"`. RED→GREEN.

### H2 · [BUG+DESIGN] "Crear cita" disabled sin comunicar qué falta
- **File:** `NuevaCitaView.tsx` (compone el motivo) + `NuevaCitaActions.tsx` / `FormActionBar` (lo muestra).
- **Síntoma live:** servicio+fecha+médico+"disponible" pero botón muerto por falta Paciente, sin pista.
- **Fix:** computar el **primer motivo de bloqueo** y mostrarlo. Orden sugerido: sin paciente → "Seleccioná un paciente" · sin servicio → "Elegí un servicio" · sin fecha/hora → "Elegí fecha y hora" · sin médico → "Elegí un médico" · `availabilityStatus !== "available"` → "El horario no está disponible". Render: línea junto a la barra de acción (reemplaza/acompaña el `hint` cuando `submitDisabled`), `role="status"`. Mantener fail-closed RN-10 (no desbloquear el submit), solo COMUNICAR. No usar `aria-disabled` falso.
- **Test:** vitest NuevaCitaView — con form parcial, el blocking-reason esperado aparece; con todo válido + available, desaparece.

### H3 · [DIVERGE] DayAvailabilityStrip quedó en barra pelada de 20px
- **File:** `DayAvailabilityStrip.tsx` (reescritura del render) — comparar con `mockups/nueva-cita.html` L840-865 (`.miniday`).
- **Falta vs ratificado:** header (médico + rango "09:00–18:00") · eje de horas (08..18/21) · leyenda (Atención / Ocupado / Cita nueva) · labels de hora en bloques ocupados · helper "Elegí una hora libre de un vistazo — la franja amarilla es la cita nueva."
- **Fix:** construir el mini-día a la spec del mockup. La franja de color actual queda como track; agregar encima: fila de header, `aria-hidden` axis con labels de hora (reusar el grid de markers existente pero con `<span>` de hora), leyenda con swatches (success/destructive/agent-mateo) + helper. Mantener `role="img"` + `aria-label` descriptivo. Bloques `busy` con su hora (`block.start` → HH:MM en tz tenant, ver H1). Sin átomos nuevos salvo que algo amerite promover (entonces `/pm-luana`).
- **Test:** vitest — render con blocks working+busy + selected → assert que aparecen labels de eje + leyenda + el bloque busy con su hora. Visual: el spec e2e de mini-vista ya existe (regression mateo) — ajustar.

### H4 · [BUG] ServicePicker/DoctorPicker pintan "vacío" ante ERROR de fetch
- **Files:** `NuevaCitaView.tsx` (threadear `isError` de `useNuevaCitaServices`/`useNuevaCitaFreeDoctors`) + `ServicePicker.tsx` + `DoctorPicker.tsx` (nuevo prop `error?: boolean` + estado de error).
- **Síntoma (código):** `data` undefined ante error → `[]` + `loading=false` → "No hay servicios/médicos disponibles" (error disfrazado de vacío legítimo).
- **Fix:** agregar `error` prop. Si `error` → bloque distinto ("No se pudieron cargar los servicios/médicos." + botón Reintentar que llame al `refetch` del hook). NuevaCitaView pasa `error={servicesError}` / `error={doctorsError}`.
- **Test:** vitest ServicePicker/DoctorPicker — `error=true` → render error+retry, NO el empty.

---

## 🟠 MEDIUM

### M1 · [DIVERGE] Columna "Disponibilidad" = dead space
- **File:** `NuevaCitaView.tsx` (right column, ~L603-642).
- **Fix:** estado intro/vacío cuando `!startTime` (en vez de solo el texto de FreeDoctorsList): un bloque que explique qué aparecerá ("Elegí servicio, fecha y médico para ver disponibilidad y el día del profesional."). Con H3 el panel poblado ya tiene cuerpo. Evitar la columna de 380px con una sola línea gris.
- **Test:** vitest — `!startTime` → intro visible; con startTime+doctor → chip+strip.

### M2 · [DIVERGE] Notas perdió la guía HIPAA del mockup
- **File:** `NuevaCitaView.tsx` (~L590 placeholder de la Textarea de notas).
- **Fix:** placeholder = `"Solo logística — sin información clínica. Ej: la paciente prefiere las mañanas."` (verbatim mockup L823). Spanish-neutro: "la paciente prefiere" OK.
- **Test:** snapshot/string assert del placeholder.

### M3 · [DIVERGE] Duración sin helper + autocalc inerte con seed
- **File:** `NuevaCitaView.tsx` (sección Duración ~L434-463).
- **Fix:** agregar helper bajo el input: `"Viene del servicio · editable"` (mockup L788). **Además:** verificar que los servicios reales traigan `initialApptDurationMinutes` — con el seed actual son null y el autocalc no dispara. Si es seed: anotar HB/seed-fix (no código de mateo). Si el contrato del endpoint no manda el campo → es bug BE (escalar). Confirmar contra `/api/v1/offer/servicios` real.
- **Test:** string assert del helper.

### M4 · [BUG] Mobile: hint de la barra choca con el FAB de Valeria + se trunca
- **File:** `FormActionBar` (`@luana/ui-kit`) — ⚠️ es engine. El hint se trunca y lo tapa el FAB de Valeria colapsada (avatar flotante bottom-left del shell).
- **Fix:** en `<sm` ocultar el `hint` (o pasar a 2 filas la barra). Si el cambio es genérico del átomo `FormActionBar` → va por **`/pm-luana`** (promotion gate, beneficia toda marca). Si se puede resolver brand-local sin tocar el átomo (ej. no pasar `hint` en mobile desde `NuevaCitaActions`) → preferir eso. Decidir en el fix: lo más barato que no toque engine. Reproducir a 390px.
- **Test:** e2e/visual a 390 — hint no visible o no solapado.

### M5 · [DESIGN] Mobile: disponibilidad lejísimos del Médico
- **File:** `NuevaCitaView.tsx`.
- **Fix:** en `<lg` renderizar el `AvailabilityChip` inline justo bajo el DoctorPicker (además del rail). El panel rico (strip+free-doctors) puede quedar abajo. No duplicar la lógica del store; reusar el mismo chip condicionado por breakpoint (Tailwind `lg:hidden` para el inline, `hidden lg:block` para el del rail).
- **Test:** vitest/e2e — a viewport chico el chip aparece tras Médico.

### M6 · [BUG] Console: Select uncontrolled→controlled (×2)
- **Files:** `ServicePicker.tsx` / `DoctorPicker.tsx` (`value={value ?? undefined}`).
- **Fix:** investigar la fuente real (Radix Select controlado admite `undefined`; el warning puede venir de un nodo nativo interno). Si es el patrón `?? undefined`, mantener el Select **controlado desde el mount** (p.ej. value siempre definido vía la API del wrapper, o `defaultValue` + controlado consistente). Si tras investigar es un quirk benigno de Radix imposible de evitar sin romper el placeholder → documentarlo con comentario y NO forzar un fix que rompa el empty-state. Verificar que el warning desaparezca en consola live.
- **Test:** correr live + `list_console_messages` → 0 del warning.

---

## 🟡 LOW

### L1 · [DESIGN] "🚶 Walk-in" / "📞 Teléfono" — inglés + emoji
- **File:** `CanalPicker.tsx` (`CANAL_OPTIONS`, L32-35).
- **Fix:** Spanish-neutro sin emoji: `walk_in` → `"Sin cita"` · `telefono` → `"Teléfono"`. ⚠️ **DIVERGE del mockup firmado** (que tenía emoji + "Walk-in"). Aplicar pero dejar nota en chris-input para que Chris vete si quiere. (Si prefiere ícono, usar lucide, no emoji.)
- **Test:** assert labels.

### L2 · [behavior] Fin manual se descarta silencioso
- **File:** `NuevaCitaView.tsx` — handlers de `startTime.onChange` (~L412) + duración (~L449) + effect de servicio (~L214).
- **Fix:** si `endTimeEditMode === true` NO sobrescribir `endTime` ni hacer `setEndTimeEditMode(false)` automático. Guardar el setValue("endTime",...) tras `if (!endTimeEditMode)`. Así el valor manual del usuario persiste.
- **Test:** vitest — entrar a editar fin, setear manual, cambiar inicio → endTime conserva el manual.

### L3 · [data] Labels doctor = UUID + servicio seed con cruft
- **No es código de mateo.** "Dr. 2b0d9466" + servicio "Limpieza dental profunda (live-verify · autosave)" = seed sucio. Acción: limpiar el seed de la clínica de prueba antes de demo (script de seed vitalia) + fallback en DoctorPicker si `doctorLabel` vacío (defensivo, opcional). Anotar HB si el seed lo generan los tests.

### L4 · [consistency] Opcionales sin marcar en crear-paciente
- **File:** `PatientPickerWithCreate.tsx` (labels Teléfono L292, Correo L314).
- **Fix:** agregar `(opcional)` a Teléfono y Correo (mismo patrón que "Notas internas (opcional)").
- **Test:** assert labels.

### L5 · [pulido] Chip de paciente: salto de alto + nombre enmascarado post-create
- **File:** `PatientPickerWithCreate.tsx` (rich chip ~L370 + `handleInlineSubmit` ~L179).
- **Fix:** (a) tras crear inline, mostrar el **nombre tipeado** (`data.name`) en el chip, no `result.nameMasked` (el chip de búsqueda ya muestra nombre real → consistencia). (b) `min-h` estable en el chip para que no salte cuando falta la sub-línea de teléfono.
- **Test:** vitest — tras create, chip muestra el nombre tipeado.

### L6 · [pulido] Textarea Notas sin contador
- **File:** `NuevaCitaView.tsx` (sección Notas).
- **Fix:** contador `{n}/500` discreto bajo la textarea (usa el value length). Si `@luana/ui-kit` ya tiene un Textarea con contador, reusar; si no, span simple.
- **Test:** assert contador refleja length.

---

## Cierre del fix-loop
1. Todos los gates verdes (tsc/eslint/vitest a11y).
2. **Live-verify** (Chrome DevTools MCP, dr.demo, :3002): ejercer happy path completo + confirmar H1 (fin = hora local), H2 (motivo de bloqueo visible), H3 (mini-día con eje+leyenda), H4 (estado error si se fuerza), M4/M5 a 390px. Screenshots.
3. Actualizar `checkpoint.md` (`dod_evidence` + `live_verify_findings`) + appendear cierre a `chris-input.md`.
4. Quedar listo para **G** (firma de Chris) → R (reconcile) → `/auditor`.
