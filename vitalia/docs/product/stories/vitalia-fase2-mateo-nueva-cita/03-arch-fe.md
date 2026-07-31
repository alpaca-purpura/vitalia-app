---
story_id: vitalia-fase2-mateo-nueva-cita
surface: frontend
builder: builder-frontend
auditor: auditor-frontend
architecture_pattern: ADR-vitalia-004
---

# 03-arch-fe — Nueva cita usable (frontend)

> Consume con `03-arch.md` (consolidado) + `mockups/nueva-cita.html` (FINAL firmado) + `mockups/PROPOSED-CANON-ATOMS.md`.
> FSD-Lite · Server-First · React Query (server data) + Zustand (UI state) · RHF + Zod · Storybook = SSoT visual.

## 0. Storybook = SSoT visual — componentes del canon por superficie (HARD · canon §5)

Partir de Storybook (`core/@luana/ui-kit`, dev `:6007` o `storybook-static/`). NO inventar CSS, NO copiar `_shared.css`. Cada superficie del form cita su story:

| Superficie del form | Componente del kit | Storybook story (id) | iframe link | Estado |
|---|---|---|---|---|
| Contenedor hoja leaf | `archetypes.FormPageScaffold` | `archetypes-formpagescaffold--default` | `…/iframe.html?id=archetypes-formpagescaffold--default&viewMode=story` | ✓ existe |
| Canal de ingreso (segmented) | `shell.TogglePill` | `shell-togglepill--default` | `…/iframe.html?id=shell-togglepill--default&viewMode=story` | ✓ existe |
| Servicio (dropdown) | `inputs.RichSelect` | `inputs-richselect--default` | `…/iframe.html?id=inputs-richselect--default&viewMode=story` | ✓ existe |
| Médico (dropdown) | `inputs.RichSelect` | `inputs-richselect--default` | idem | ✓ existe |
| Paciente (typeahead) | `EntityPicker` | `entitypicker--default` | `…/iframe.html?id=entitypicker--default&viewMode=story` | ✓ existe (base) |
| Fecha + hora inicio | `inputs.SmartDatetimePicker` | `inputs-smartdatetimepicker--default` | `…/iframe.html?id=inputs-smartdatetimepicker--default&viewMode=story` | ✓ existe |
| Hora fin (autocalc editable) | `inline-editable` + `Badge` | `inputs-richselect`/`atoms-badge` | — | ✓ existe |
| Notas internas | `textarea` (`@/components/ui/textarea`) | shadcn base | — | ✓ existe |
| Médico card / día | `card` / `EntityInfoCard` | `entityinfocard--default` | — | ✓ existe |
| Toast 409 | `overlays.Sonner` (`sonner`) | base | — | ✓ existe |
| Avatares | `avatar` | base | — | ✓ existe |
| **Barra de acción sticky** | **`FormActionBar`** | `forms-formactionbar--default` (a crear) | — | **★ PROMOTE** |
| **Chips de disponibilidad** | **`Badge variant=success\|warning`** | `atoms-badge--semantic` (a crear) | — | **★ PROMOTE** |
| **Volver a Agenda** | **`PageHeader` back-pill** | `layout-pageheader--with-back-pill` (a crear) | — | **★ PROMOTE** |
| **Crear paciente sin salir** | **`EntityPicker.createAction`** | `entitypicker--with-create-action` (a crear) | — | **★ PROMOTE** |
| Mini-vista del día | `DayAvailabilityStrip` | n/a — componente feature scheduling | — | ◆ feature (lift-candidate) |

> **★ PROMOTE = soft-dep de build.** Los 4 atoms viven en `@luana/ui-kit` (CORE). El FE de vitalia los CONSUME. NO se editan local en `features/`. Precursora: `/pm-vitalia` promotion proposal `2026-06-22-ui-kit-nueva-cita-atoms.md` (contrato en `mockups/PROPOSED-CANON-ATOMS.md`). Si al arrancar el build el kit no los tiene → bloqueo soft (ver dispatch-plan: secuenciar la promoción primero). **El builder NUNCA re-implementa estos atoms en `features/mateo/`** (driftea → auditor CHANGES_REQUESTED).
> **◆ DayAvailabilityStrip** = componente NUEVO de feature scheduling (`features/mateo/components/nueva-cita/`). Default = vitalia. Lift-candidate a `core/luana-core-scheduling` NO ahora (comunify no agenda con disponibilidad).

## 1. Routing (ADR-vitalia-004 § 3.1)

- Ruta estática nueva: `app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/page.tsx` (Server Component default).
- Precedencia estática sobre `[agent]/[subtab]` (igual que `mateo/agenda/page.tsx`).
- `page.tsx` (Server): await params + searchParams (`?date=&time=` prellenado al entrar por slot vacío); SSR initial (servicios + médicos activos via server fetch para hidratar los dropdowns sin flash); pasa initialData al client root. **PHI nunca en URL/searchParams** (`date`/`time` no son PHI — OK; `patient_id` NUNCA en URL).
- `loading.tsx` (skeleton) + `error.tsx` (boundary).
- NO N3-static (la hoja es una sola vista, no 3+ sub-vistas → no `SubSubTabsBar`).

## 2. FSD-Lite layout

```
features/mateo/
  api/nueva-cita.ts                      # React Query hooks
  components/nueva-cita/
    NuevaCitaView.tsx                    # "use client" client root
    ServicePicker.tsx                    # RichSelect + duración prefill
    DoctorPicker.tsx                     # RichSelect médicos activos
    PatientPickerWithCreate.tsx          # EntityPicker + createAction (consume kit)
    AvailabilityChip.tsx                 # Badge success/warning (consume kit)
    DayAvailabilityStrip.tsx             # ◆ feature NUEVO (mini-vista)
    FreeDoctorsList.tsx                  # lista reasignar 1 clic
    NuevaCitaActions.tsx                 # FormActionBar wrapper (consume kit)
  store/nueva-cita-store.ts              # Zustand UI state
  types/agenda-schema.ts                 # MOD: extend availability + reconcile origin
  index.ts                               # MOD: public API exports
app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/{page,loading,error}.tsx
```

`features/{A}` no importa de `features/{B}` (`test_no_cross_feature_imports`). Public API via `index.ts`.

## 3. Client root + data/UI split (ADR-vitalia-004 § 4)

- `NuevaCitaView.tsx` (`"use client"` línea 1) — hidrata con props SSR (servicios, médicos). Orquesta el form.
- **React Query (server data):** `useAvailabilityCheck`, `useFreeDoctors`, `useDayStrip`, `usePatientSearch`, `useCreatePatientInline`, `useCreateAppointment` (extend), `useServicesList`, `useDoctorsList`. Keys convention `["mateo","nueva-cita",action,...stableFilters]` (`test_react_query_keys_convention`).
- **Zustand (UI state ONLY):** `nueva-cita-store` — selected service/doctor/patient, computed endTime, chip status cache, free-doctors panel open. NUNCA mezclar server data en Zustand.
- `useAvailabilityCheck` debounced (≈400ms) sobre `{doctorId, startTime, durationMinutes}`; **revalida al cambiar servicio/hora/médico** (SC-revalida-cambio) — el estado viejo no queda pegado (key incluye la franja efectiva).

## 4. Forms (RHF + Zod, ADR-vitalia-004 § 5)

- RHF + `zodResolver(CreateAppointmentRequestSchema)` (reconciliado, ver § 5).
- Validación inline: fin > inicio (SC-fin-invalido); paciente requerido; servicio requerido; médico requerido.
- Submit explícito (NO autosave — es flujo de creación, `FormActionBar` sticky). Crear deshabilitado hasta chip `AVAILABLE` (fail-closed RN-10) + form válido.
- Paciente inline create: `PatientPickerWithCreate` → `createAction` → mini-form (nombre+teléfono) → `useCreatePatientInline` → `patient_id` preseleccionado, sin salir (AC-10). RN-9: si `find_by_phone` (BE) detecta dup → prompt "Ya existe {nombre} · ¿usar ese?".

## 5. TypeScript types (agenda-schema.ts EXTEND)

camelCase mirror, ISO 8601 datetimes como `string`, optional explícito:
```typescript
export const AvailabilityCheckRequestSchema = z.object({
  doctorId: z.string().uuid(),
  startTime: z.string().datetime({ offset: true }),
  durationMinutes: z.number().int().min(1),
});
export const AvailabilityStatusSchema = z.enum(["available","busy","out_of_hours","no_schedule"]);
export const AvailabilityCheckResponseSchema = z.object({
  status: AvailabilityStatusSchema,
  conflictLabel: z.string().nullable(),
  conflictStart: z.string().datetime({ offset: true }).nullable(),
});
export const FreeDoctorsResponseSchema = z.object({
  doctors: z.array(z.object({ doctorId: z.string().uuid(), doctorLabel: z.string().min(1) })),
});
export const DayStripResponseSchema = z.object({
  doctorId: z.string().uuid(),
  dateLocal: z.string(),
  blocks: z.array(z.object({
    startTime: z.string().datetime({ offset: true }),
    endTime: z.string().datetime({ offset: true }),
    kind: z.enum(["working_hours","busy"]),
  })),
});
export const PatientInlineCreateRequestSchema = z.object({
  name: z.string().min(2, "El nombre debe tener al menos 2 caracteres").max(128),
  phone: z.string().min(6, "El teléfono debe tener al menos 6 caracteres").max(24),
  email: z.string().email("Correo inválido").nullable().optional(),
  channel: z.enum(["walk_in","telefono"]),
});
export const PatientInlineCreateResponseSchema = z.object({
  patientId: z.string().uuid(), nameMasked: z.string().min(1),
});
export const PatientSearchResponseSchema = z.object({
  items: z.array(z.object({ patientId: z.string().uuid(), nameMasked: z.string().min(1), phoneMasked: z.string().min(1) })),
  nextCursor: z.string().nullable(),
});
// CreateAppointmentRequestSchema RECONCILIADO (D-F):
//   origin: z.enum(["walk_in","telefono"])     // canal, no existencia
//   patientId: z.string().uuid()               // SIEMPRE (typeahead o inline)
//   (remover patientNewData)                   // alta = endpoint aparte
```

## 6. Master data / tz (RN-8)

- FE ingresa/muestra en tz IANA del tenant via `useTenantLocale()` / `formatTenantDate*()`. Envía UTC al BE. `SmartDatetimePicker` maneja la conversión. Overlap se compara server-side en UTC absoluto (DST-safe, SC-i18n-tz).
- `tenant_id` del FE via `useTenantId()` — NUNCA `useAuth().orgId` (`test-no-clerk-organizations`).
- `X-Clinic-ID` lo inyecta el fetchClient/contexto de clínica (igual que el resto de mateo).

## 7. Empty / error / availability states (mockup)

- SC-empty-servicios: estado vacío "No hay servicios. Cargalos en Mi Clínica › Servicios" + Crear deshabilitado.
- SC-empty-medicos: "No hay médicos activos".
- SC-empty-pacientes: "Sin resultados" + "+ Crear paciente" prominente.
- SC-sin-horario: chip `Badge warning` "Sin horario cargado" + CTA "Carga el horario… en Mi Clínica › Horarios".
- SC-fuera-horario: `Badge warning` "Fuera de horario".
- SC-solape: `Badge` (destructive-ish) "Ocupado — se solapa con [09:15]" + FreeDoctorsList.
- SC-disponibilidad-falla: chip "No pudimos verificar disponibilidad, reintentá" + Crear deshabilitado + reintentar (RN-10 fail-closed).
- SC-mini-vista: DayAvailabilityStrip pinta working_hours + busy + franja nueva resaltada (amarilla); cambiar hora mueve la franja.

## 8. Spanish neutro LatAm

Todos los strings + chip labels + errores: neutro (tuteo, sin voseo). `test_no_voseo_in_copy`. Sin colores hardcoded (`test_no_hardcoded_colors` — usar tokens, color por agente Mateo `--agent-mateo`/`#FEE209`). Sin `<select>` nativo (`test-no-native-select` — RichSelect). Sin `<div>` de layout donde hay primitiva (`test-no-div-layout` — FormPageScaffold/PageContainer).

## 9. Tests (TDD RED-first)

| Test | Capa | Cubre |
|---|---|---|
| `nueva-cita.test.ts` (hooks) | api | useAvailabilityCheck debounce + revalidate (SC-revalida-cambio), useCreatePatientInline |
| `AvailabilityChip.test.tsx` | component | 4 estados Badge + aria-live (SC-a11y) |
| `DayAvailabilityStrip.test.tsx` | component | render working/busy + franja resaltada (SC-mini-vista) |
| `FreeDoctorsList.test.tsx` | component | reasignar 1 clic re-eval (SC-reasignar), lista vacía (SC-reasignar-vacio) |
| `PatientPickerWithCreate.test.tsx` | component | createAction inline, validación (SC-paciente-incompleto), dup prompt (SC-paciente-duplicado) |
| `NuevaCitaView.test.tsx` | component | fin>inicio (SC-fin-invalido), Crear gated por chip (RN-10), empty states |
| `nueva-cita-store.test.ts` | store | transitions, computed endTime de duración |
| `agenda-schema.test.ts` (MOD) | types | availability schemas + reconciled origin |

**E2E Playwright (autenticado dev-app, write real, Rule #37):** SC-happy, SC-crear-paciente, SC-dur-default, SC-solape, SC-reasignar, SC-mini-vista, SC-empty-servicios, SC-empty-medicos, SC-empty-pacientes, SC-fin-invalido, SC-half-open-ok, SC-cancelled-reuse, SC-pasado, SC-disponibilidad-falla, SC-a11y (axe wcag2aa con `assertShellMounted` antes del scan), SC-i18n-tz, SC-pacientes-grandes. (Smoke nuevo en `e2e/specs/smoke/nueva-cita.smoke.spec.ts` para la ruta nueva.)

## 10. File structure (NEW vs MOD)

Ver § 2 + consolidado § 10. Headers `// cap: scheduling.mateo-agenda` líneas 1-3 en todos los nuevos. `CrearCitaForm.tsx` + `CrearCitaButton.tsx`: el form modal MUERE (AC-9 / D-G) — `CrearCitaButton` pasa a `router.push('.../nueva-cita')`; los tests del legacy form se eliminan/migran a `NuevaCitaView.test.tsx`. `AgendaSlotInteractive.tsx`: click slot vacío → push con `?date=&time=`.
