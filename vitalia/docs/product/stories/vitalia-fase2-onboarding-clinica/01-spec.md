---
story_id: vitalia-fase2-config-onboarding-clinica
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
state: refining
po_ux_iter: 1
ratified_by_chris: false
ratified_visual_by_chris: false
architecture_pattern: ADR-vitalia-004              # ★ MANDATORY cita transversal
agent_owner: config
module: onboarding
capability: config.onboarding_clinic
spawned_at: 2026-05-26
parent_outcome_ref: vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md
---

# vitalia-fase2-config-onboarding-clinica — Spec v1

## § Context

### Outcome ref
`vitalia-mvp-ui-foundation` — foundation UI completa para operar Vitalia desde el shell-organism. Esta story establece el "contrato de configuración" mínimo que todo tenant necesita para que los agentes (Valeria, Lucas, Lisa, etc.) operen con contexto clínico correcto.

### Insertion point
Primer login post-signup de un tenant vitalia nuevo que **no tiene `clinic_vertical` seteado**. El sistema detecta esta condición en el middleware de la shell-organism route y fuerza un redirect a `/onboarding/wizard` (paso extendido sobre el wizard existente de 3 pasos).

La story extiende el wizard actual (`/onboarding/wizard/page.tsx`) agregando **dos nuevos pasos** al flujo existente:
- Paso actual 1: Perfil clínica (clinic_name, clinic_type legacy, country, city) — **se conserva**
- **Paso 1b NUEVO:** `ClinicVerticalSelector` — modelo de negocio médico
- **Paso 1c NUEVO:** `PrimarySpecialtiesSelector` — especialidades del equipo
- Paso actual 2: Selección de plan — **se conserva**
- Paso actual 3: Confirmación / primer offer — **se conserva**

Alternativamente (si el architect decide separar): una página `/onboarding/clinic-config` propia post-paso-1. La especificación es agnóstica a esta decisión (Open question #1).

### Out-of-scope
- NO setup billing (story `vitalia-fase2-config-cuenta` § PlanLuanaSection)
- NO setup del equipo de doctores (story `vitalia-fase2-lisa-doctores`)
- NO setup de conexiones/integraciones (story `vitalia-fase2-config-conexiones`)
- NO implementación de compliance per-specialty (`vitalia_prohibited_phrases`, safeguards psico, COFEPRIS, etc.) — esta story SOLO captura los datos; los safeguards son feed futuro
- NO actualización post-onboarding libre — ese flujo vive en `vitalia-fase2-config-cuenta` § InfoClinicaSection (vertical read-only allí)

### Trigger
Middleware `vitalia/frontend/src/middleware.ts` verifica `clinic_vertical IS NULL` para tenant en primera sesión → redirect forzado a `/onboarding/wizard` (o página dedicada). Si `clinic_vertical` ya tiene valor → skip transparente.

---

## § Gherkin scenarios

> Notación: `playwright_required: true` en todos los scenarios interactivos. `graders` = lista de verificaciones en el test.

### happy — primer setup clinic_vertical + multi-specialty

```gherkin
Scenario: Tenant nuevo completa configuración de vertical y especialidades
  Given un tenant "clinica-dental-mx" acaba de crear su cuenta en Vitalia
  And clinic_vertical IS NULL en la base de datos
  And el usuario está en el paso 1b (ClinicVerticalSelector) del wizard
  When el usuario selecciona la tarjeta "Clínica dental"
  And avanza al paso 1c (PrimarySpecialtiesSelector)
  And selecciona los chips "Odontología general" y "Odontología estética"
  And hace clic en "Continuar"
  Then la UI avanza al paso siguiente (selección de plan)
  And POST /api/v1/onboarding/clinic-config recibe body con clinic_vertical="dental_clinic" y primary_specialties=["odontologia","estetica_dermatologia"]
  And la respuesta es 200 con onboarding_clinic_config_complete=true
  And el campo clinic_vertical en la DB queda seteado
  And el evento telemetría onboarding_completed se dispara con step_at="clinic_config"
playwright_required: true
graders:
  - "card 'Clínica dental' tiene aria-pressed=true tras click"
  - "chips seleccionados tienen clase CSS de estado activo"
  - "POST /api/v1/onboarding/clinic-config interceptado con payload correcto"
  - "step counter avanza de 1b a 1c a 2"
  - "no voseo en ningún texto visible"
```

### negative — submit sin clinic_vertical

```gherkin
Scenario: Usuario intenta avanzar sin seleccionar vertical
  Given el usuario está en el paso 1b (ClinicVerticalSelector)
  And ninguna tarjeta de vertical ha sido seleccionada
  When hace clic en "Continuar"
  Then el formulario NO avanza al siguiente paso
  And aparece mensaje de error inline "Selecciona el modelo de tu clínica para continuar"
  And el foco del teclado retorna al primer elemento interactivo del fieldset
  And NO se dispara ninguna llamada a la API
playwright_required: true
graders:
  - "mensaje de error visible en DOM con role=alert"
  - "ninguna request a /api/v1/onboarding interceptada"
  - "foco regresa al grupo de tarjetas (aria-invalid=true en fieldset)"
```

### negative — submit sin primary_specialties

```gherkin
Scenario: Usuario intenta avanzar sin seleccionar ninguna especialidad
  Given el usuario completó el paso 1b con vertical="medspa_aesthetic"
  And está en el paso 1c (PrimarySpecialtiesSelector)
  And ningún chip de especialidad está seleccionado
  When hace clic en "Continuar"
  Then aparece mensaje "Selecciona al menos una especialidad"
  And el formulario no avanza
playwright_required: true
graders:
  - "role=alert visible con texto esperado"
  - "ningún request API disparado"
```

### edge — switch clinic_vertical después de seleccionar specialties

```gherkin
Scenario: Usuario regresa al paso 1b y cambia la vertical después de haber elegido especialidades
  Given el usuario eligió vertical="dental_clinic" en paso 1b
  And eligió especialidades ["odontologia", "ortopedia"]
  And está en el paso 1c
  When hace clic en "Atrás" para regresar al paso 1b
  And selecciona una vertical diferente: "mental_health_center"
  And avanza al paso 1c nuevamente
  Then las especialidades previamente seleccionadas se LIMPIAN (reset)
  And la UI muestra el selector de especialidades vacío con foco en el primer chip
  And una nota contextual indica "Selecciona las especialidades de tu centro de salud mental"
playwright_required: true
graders:
  - "ningún chip tiene estado activo al retornar al paso 1c con nueva vertical"
  - "nota contextual contiene texto relevante a la nueva vertical"
  - "conteo de seleccionados muestra 0"
```

### adversarial — cross-tenant attempt

```gherkin
Scenario: Tenant A intenta submitear onboarding para tenant B
  Given tenant_a tiene JWT con tenant_id="tenant-a-uuid"
  And el body del POST contiene tenant_id="tenant-b-uuid" manipulado
  When POST /api/v1/onboarding/clinic-config con payload adulterado
  Then el backend retorna 403 Forbidden
  And persiste SOLO el clinic_vertical del tenant_a (no modificado)
  And audit_log registra el intento con action="cross_tenant_onboarding_attempt"
playwright_required: false
graders:
  - "response status 403"
  - "DB tenant_b clinic_vertical no modificada"
  - "audit_log row con action cross_tenant_onboarding_attempt"
```

### adversarial — onboarding ya completado forzado nuevamente

```gherkin
Scenario: Tenant con clinic_vertical ya seteado intenta forzar re-onboarding
  Given tenant "clinica-dental-pe" tiene clinic_vertical="dental_clinic" ya persistido
  When intenta hacer GET /onboarding/wizard directamente via URL
  Then el middleware detecta clinic_vertical != NULL
  And redirige a /(shell-organism)/config o dashboard raíz del tenant
  And NO muestra el wizard de onboarding
playwright_required: true
graders:
  - "URL final no contiene /onboarding/wizard"
  - "no se muestran componentes ClinicVerticalSelector ni PrimarySpecialtiesSelector"
```

### race_condition — 2 tabs abren onboarding simultáneo

```gherkin
Scenario: Mismo tenant abre el wizard en 2 pestañas y ambas intentan submitear
  Given tenant "clinica-nueva" tiene clinic_vertical=NULL
  And el wizard está abierto en tab A (paso 1b) y tab B (paso 1b)
  When tab A selecciona "dental_clinic" y submitea el POST
  And tab B selecciona "medspa_aesthetic" y submitea el POST casi simultáneamente
  Then el backend usa idempotency: el PRIMER write gana
  And el SEGUNDO POST retorna 200 con onboarding_clinic_config_complete=true (idempotente, no error)
  And el valor final en DB es el del primer write (no importa cuál fue primero en la carrera)
  And ambas tabs son redirigidas al paso siguiente (no quedan atascadas)
playwright_required: false
graders:
  - "solo 1 row en onboarding_clinic_config para el tenant"
  - "ambas responses son 2xx"
  - "clinic_vertical en DB tiene exactamente 1 valor (no null, no conflicto)"
```

### concurrent_users — 2 owners mismo tenant abren onboarding al mismo tiempo

```gherkin
Scenario: 2 admins del mismo tenant abren el wizard simultáneamente
  Given tenant "clinica-compartida" tiene 2 usuarios con role=admin_clinic
  And clinic_vertical=NULL
  And admin_1 abre el wizard en su sesión
  And admin_2 abre el wizard en su sesión independiente
  When admin_1 completa y submitea clinic_vertical="primary_care"
  And admin_2 (que aún está en paso 1b) submitea clinic_vertical="multispecialty"
  Then last-write-wins con idempotency key tenant_id
  And ambas UIs muestran el valor final activo
  And se emite 1 sola telemetría onboarding_completed (deduplicado por tenant_id)
playwright_required: false
graders:
  - "exactamente 1 row onboarding_clinic_config"
  - "evento onboarding_completed sin duplicados en telemetría"
```

### network_failure — submit con backend timeout

```gherkin
Scenario: La llamada POST /api/v1/onboarding/clinic-config falla por timeout
  Given el usuario completó la selección de vertical y especialidades
  And el backend simula un timeout de 30 segundos (test mock)
  When hace clic en "Continuar"
  Then aparece estado de carga (spinner visible, botón deshabilitado)
  And después del timeout aparece error toast: "No pudimos guardar tu configuración. Intenta de nuevo."
  And el botón se vuelve a habilitar
  And la selección del usuario se conserva (no se pierde el estado del formulario)
  And el usuario puede reintentar sin rehacer la selección
playwright_required: true
graders:
  - "spinner presente durante la espera"
  - "toast de error visible con texto esperado"
  - "estado de chips/tarjetas preservado tras error"
  - "botón habilitado para reintento"
```

### empty_state — primer login post-signup sin ninguna data previa

```gherkin
Scenario: Tenant nuevo sin ningún dato previo ve el wizard desde cero
  Given tenant "clinica-nueva-fresca" acaba de crearse
  And no tiene clinic_name, clinic_vertical, primary_specialties
  When entra al dashboard de Vitalia
  Then el middleware detecta clinic_vertical=NULL
  And redirige a /onboarding/wizard
  And el wizard muestra el paso 1 (perfil clínica) con todos los campos vacíos
  And el progress indicator muestra "Paso 1 de 4" (o similar según decisión de paso count)
  And no hay pre-selección en ClinicVerticalSelector
  And no hay chips seleccionados en PrimarySpecialtiesSelector
playwright_required: true
graders:
  - "URL es /onboarding/wizard"
  - "no cards pre-selected en vertical selector"
  - "no chips pre-selected en specialty selector"
  - "step indicator visible"
```

### large_dataset — owner selecciona 12 especialidades (máximo razonable)

```gherkin
Scenario: Clínica multispecialty selecciona todas las especialidades disponibles
  Given el usuario está en paso 1c con vertical="multispecialty"
  When hace clic en los 12 chips de especialidades disponibles (incluyendo "Otra (especificar)")
  And completa el campo free-text con "Genética médica"
  And hace clic en "Continuar"
  Then el POST body contiene primary_specialties con los 12 valores válidos
  And el campo other_specialty_text="Genética médica" se incluye en el payload
  And el backend persiste todos sin truncar
  And la UI no colapsa ni rompe el layout con 12 chips seleccionados
playwright_required: true
graders:
  - "12 chips con estado activo visible en DOM"
  - "campo free-text visible y completado"
  - "POST payload contiene array de longitud 12 + other_specialty_text"
  - "no overflow ni truncado en la lista de chips seleccionados"
```

### accessibility — keyboard navigation completa + screen reader

```gherkin
Scenario: Usuario con teclado navega todo el wizard sin mouse
  Given el wizard está en el paso 1b (ClinicVerticalSelector)
  When el usuario usa Tab para llegar al grupo de tarjetas (fieldset/radiogroup)
  And usa flechas ← → para moverse entre opciones de vertical
  And presiona Enter para seleccionar una tarjeta
  And Tab para llegar al botón "Continuar"
  And Enter para confirmar
  And en el paso 1c usa Tab para llegar al grid de chips
  And Space para seleccionar/deseleccionar chips
  Then cada acción produce el resultado esperado sin necesidad de mouse
  And los anuncios de screen reader son correctos (aria-checked, aria-label, role)
  And el foco visible es siempre perceptible (focus-visible ring aplicado)
playwright_required: true
graders:
  - "axe-core 0 violations en paso 1b y paso 1c"
  - "aria-checked=true en chip seleccionado"
  - "focus-visible ring visible (CSS :focus-visible)"
  - "fieldset tiene aria-label descriptivo"
  - "role=radiogroup en vertical selector"
  - "role=group con aria-label en specialty selector"
```

### i18n — Spanish neutro LatAm verificado

<!-- voseo-allowed: Gherkin scenario validando que voseo NO debería aparecer en UI — es test assertion, no string user-facing -->

```gherkin
Scenario: Todos los textos del wizard de configuración están en español neutro sin voseo
  Given el wizard está cargado en cualquiera de sus pasos
  Then no hay ningún texto visible que contenga voseo (tenés, podés, elegí, seleccioná, etc.)
  And los títulos, hints, labels, placeholders, errores y CTAs usan tuteo o forma impersonal
  And las especialidades tienen nombres en español neutro (no regionalismos)
playwright_required: false
graders:
  - "grep en microcopy: ninguna ocurrencia de vocales acentuadas en verbos voseados"
  - "auditor visual confirma spanish-neutro en cada string exportado de microcopy.ts"
```

---

## § Wireframes inline

> Nota: los wireframes usan datos LatAm realistas. Todos los textos en español neutro.

### 1. Welcome / Progress stepper (header del wizard extendido)

```
┌─────────────────────────────────────────────────────────────────┐
│  ● Vitalia                                              [Salir] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Configuración de tu clínica                                    │
│                                                                  │
│  ①──②──③──④                                                    │
│  Perfil · Vertical · Especialidades · Plan                      │
│                                                                  │
│  Paso 2 de 4 — Tipo de clínica                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. ClinicVerticalSelector — paso 1b (8 tarjetas visuales)

```
┌─────────────────────────────────────────────────────────────────┐
│  ¿Qué tipo de clínica describes mejor tu práctica?              │
│  Esto personaliza el comportamiento de tus agentes.             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  🦷          │  │  ✨          │  │  🧠          │             │
│  │ Clínica     │  │ MedSpa /    │  │ Salud       │             │
│  │ dental      │  │ Estética    │  │ mental      │             │
│  │             │  │             │  │             │             │
│  │ Odontología │  │ Dermatología│  │ Psicología  │             │
│  │ general y   │  │ estética,   │  │ y psiquia-  │             │
│  │ especializ. │  │ procedim.   │  │ tría        │             │
│  └─────────────┘  └──[selected]─┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  🏥          │  │  🔬          │  │  🌿          │             │
│  │ Medicina    │  │ Clínica     │  │ Wellness /  │             │
│  │ general y   │  │ multi-      │  │ bienestar   │             │
│  │ familiar    │  │ especialidad│  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  💻          │  │  🦵          │                               │
│  │ Telemedicina│  │ Rehabili-   │                               │
│  │ / Digital   │  │ tación      │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                  │
│                        [← Atrás]  [Continuar →]                 │
└─────────────────────────────────────────────────────────────────┘
```

Tarjeta seleccionada: borde azul/brand + checkmark superior derecho + fondo tinted.
Hover: borde brand/40 + leve shadow.
Estado disabled: opacity-50 + cursor-not-allowed (no aplica en esta pantalla pero sí al regresar si ya fue enviado).

### 3. PrimarySpecialtiesSelector — paso 1c (chips multi-select + search + free-text)

```
┌─────────────────────────────────────────────────────────────────┐
│  ¿Qué especialidades ofrece tu equipo?                          │
│  Puedes seleccionar varias. Esto ayuda a Valeria y Lucas a      │
│  contextualizar recomendaciones y campañas.                     │
│                                                                  │
│  [🔍 Buscar especialidad...                          ]          │
│                                                                  │
│  Especialidades disponibles:                                    │
│                                                                  │
│  [✓ Odontología general] [✓ Odontología estética]               │
│  [ Psicología ]  [ Psiquiatría ]  [ Medicina general ]          │
│  [ Ginecología ]  [ Pediatría ]  [ Oftalmología ]               │
│  [ Fisioterapia ]  [ Nutrición ]  [ Ortopedia y traumatología ] │
│  [ Podología ]  [ Cardiología y endocrinología ]                │
│                                                                  │
│  [ + Otra especialidad ]                                        │
│    ┌────────────────────────────────────────────────────┐       │
│    │ ¿Cuál? (ej: Genética médica)                       │       │
│    └────────────────────────────────────────────────────┘       │
│                                                                  │
│  Seleccionadas: 2 especialidades                                │
│                                                                  │
│                        [← Atrás]  [Continuar →]                 │
└─────────────────────────────────────────────────────────────────┘
```

Chips: fondo blanco + borde gris en idle; fondo brand/10 + borde brand + checkmark inline en selected.
Search: filtra chips por texto sin llamada API (client-side filter sobre el array).
"Otra especialidad": toggle chip que expande un campo `<input type="text">`.

### 4. Confirmation step (revisión antes de avanzar al plan)

```
┌─────────────────────────────────────────────────────────────────┐
│  Resumen de tu configuración                                    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Tipo de clínica: MedSpa / Estética         [Editar]   │     │
│  │  Especialidades:  Odontología estética,     [Editar]   │     │
│  │                   Dermatología, Nutrición             │     │
│  │  País:            Colombia                            │     │
│  │  Ciudad:          Medellín                            │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ✅ Tu asistente Valeria usará esta información para            │
│     personalizar cada interacción con tus pacientes.            │
│                                                                  │
│                 [← Atrás]  [Confirmar y continuar →]            │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Estados vacío / error / carga

```
── Empty state (paso 1b sin selección + intento de avanzar) ──────
│  [!] Selecciona el modelo de tu clínica para continuar          │
│      (aparece inline debajo del fieldset, role=alert)           │

── Loading (submit en curso) ────────────────────────────────────
│  [Continuar →] → [⠋ Guardando...]  botón disabled + aria-busy  │

── Error toast (network failure) ────────────────────────────────
│  ╔══════════════════════════════════════════╗                   │
│  ║ ⚠ No pudimos guardar tu configuración.  ║                   │
│  ║   Intenta de nuevo.          [✕ Cerrar] ║                   │
│  ╚══════════════════════════════════════════╝                   │
│  (Sonner toast, variant=destructive, duration=6000ms)           │
```

---

## § Estados visuales (tabla)

| Componente | Estado | Clase Tailwind clave | aria |
|---|---|---|---|
| Tarjeta vertical (idle) | Default | `border-border bg-card` | `role=radio aria-checked=false` |
| Tarjeta vertical (hover) | Hover | `hover:border-brand/40 hover:shadow-sm` | — |
| Tarjeta vertical (selected) | Active | `border-brand bg-brand/5 ring-2 ring-brand` | `aria-checked=true` |
| Tarjeta vertical (disabled) | Disabled | `opacity-50 cursor-not-allowed` | `aria-disabled=true` |
| Chip especialidad (idle) | Default | `border-border bg-background text-foreground` | `role=checkbox aria-checked=false` |
| Chip especialidad (selected) | Active | `border-brand bg-brand/10 text-brand font-medium` | `aria-checked=true` |
| Chip especialidad (hover) | Hover | `hover:border-brand/40` | — |
| Botón "Continuar" (idle) | Default | `bg-primary text-primary-foreground` | `type=button` |
| Botón "Continuar" (loading) | Busy | `opacity-70 cursor-not-allowed` | `aria-busy=true aria-disabled=true` |
| Campo free-text "Otra" (oculto) | Hidden | `hidden` / `h-0 overflow-hidden` | `aria-hidden=true` |
| Campo free-text "Otra" (visible) | Visible | `block animate-in fade-in-0` | `aria-hidden=false` |
| Error inline | Error | `text-destructive text-xs mt-1` | `role=alert` |
| Toast error | Error | `bg-destructive text-destructive-foreground` | `role=alert aria-live=assertive` |
| Step indicator activo | Active | `text-primary font-semibold` | `aria-current=step` |
| Step indicator completo | Done | `text-muted-foreground` con checkmark | — |

---

## § Componentes (path-by-path con reuse vs new)

### Reuse — Shadcn UI (ya instalados en vitalia/frontend)

| Componente | Path actual | Uso en esta story |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | Botones "Continuar" / "Atrás" |
| `Input` | `vitalia/frontend/src/components/ui/input.tsx` | Campo free-text "Otra especialidad" + search |
| `Dialog` | `vitalia/frontend/src/components/ui/dialog.tsx` | N/A en esta story (usar si se decide modal en vez de page) |
| `Badge` | `vitalia/frontend/src/components/ui/badge.tsx` | Contador "Seleccionadas: N" |
| `Separator` | `vitalia/frontend/src/components/ui/separator.tsx` | Divisores entre secciones |
| `Skeleton` | `vitalia/frontend/src/components/ui/skeleton.tsx` | Loading states |

### Reuse — Vitalia FE existente

| Componente | Path actual | Uso |
|---|---|---|
| `ClinicTypePicker` | `vitalia/frontend/src/features/vitalia/components/clinic-type-picker.tsx` | ADAPT: patrón card-radio reutilizable para `ClinicVerticalSelector`. Los 4 tipos legacy (dental/psychology/psychiatry/wellness) se reemplazan por los 8 clinic_vertical enums nuevos. |
| `OnboardingStep1Client` | `vitalia/frontend/src/features/vitalia/components/onboarding-step-1-client.tsx` | REUSE: patrón wizard step con `onNext`/`onBack` props, inline error state, aria-invalid pattern. |
| `WizardOnboardingLayout` | (via `@/features/onboarding`) | EXTEND: agregar pasos 1b y 1c al flujo existente |
| `MICROCOPY_ONBOARDING` | `vitalia/frontend/src/features/vitalia/config/microcopy.ts` | EXTEND: agregar keys `clinicVertical.*` y `primarySpecialties.*` |

### Componentes nuevos a crear

| Componente | Path destino | Descripción |
|---|---|---|
| `ClinicVerticalSelector` | `vitalia/frontend/src/features/vitalia/components/clinic-vertical-selector.tsx` | Reemplaza/extiende `ClinicTypePicker` con 8 opciones y enum nuevo. ADAPT del patrón ClinicTypePicker. |
| `PrimarySpecialtiesSelector` | `vitalia/frontend/src/features/vitalia/components/primary-specialties-selector.tsx` | Multi-select chips + search + "Otra" free-text. NUEVO. |
| `OnboardingStepVerticalClient` | `vitalia/frontend/src/features/vitalia/components/onboarding-step-vertical-client.tsx` | Wrapper step para `ClinicVerticalSelector` con validación. NUEVO. |
| `OnboardingStepSpecialtiesClient` | `vitalia/frontend/src/features/vitalia/components/onboarding-step-specialties-client.tsx` | Wrapper step para `PrimarySpecialtiesSelector` con validación. NUEVO. |
| `ClinicConfigConfirmStep` | `vitalia/frontend/src/features/vitalia/components/clinic-config-confirm-step.tsx` | Resumen editable antes de avanzar al plan. NUEVO. |

---

## § Data flow conceptual

### API endpoints

```
POST /api/v1/onboarding/clinic-config
  Request body:
    {
      clinic_vertical: "dental_clinic" | "medspa_aesthetic" | "mental_health_center" |
                       "primary_care" | "multispecialty" | "wellness_spa" |
                       "telehealth_only" | "rehab_center",
      primary_specialties: [
        "odontologia" | "estetica_dermatologia" | "psicologia_psiquiatria" |
        "medicina_general" | "ginecologia" | "pediatria" | "oftalmologia" |
        "fisioterapia" | "nutricion" | "ortopedia" | "podologia" |
        "cardiologia_endocrinologia"
      ],
      other_specialty_text?: string | null    # libre texto si "otra" seleccionada
    }
  Response 200:
    {
      tenant_id: string,
      clinic_vertical: string,
      primary_specialties: string[],
      onboarding_clinic_config_complete: boolean
    }
  Response 403: cross-tenant attempt
  Response 422: invalid enum value
  Response 409: idempotency (ya configurado — retorna current config)

GET /api/v1/onboarding/status
  Response: { ..., clinic_config_complete: boolean }   # ya existe, EXTEND campo
```

### Zod schema (FE)

```typescript
// vitalia/frontend/src/features/vitalia/schemas/clinic-config-schema.ts

import { z } from "zod";

export const CLINIC_VERTICAL_ENUM = [
  "dental_clinic",
  "medspa_aesthetic",
  "mental_health_center",
  "primary_care",
  "multispecialty",
  "wellness_spa",
  "telehealth_only",
  "rehab_center",
] as const;

export const PRIMARY_SPECIALTY_ENUM = [
  "odontologia",
  "estetica_dermatologia",
  "psicologia_psiquiatria",
  "medicina_general",
  "ginecologia",
  "pediatria",
  "oftalmologia",
  "fisioterapia",
  "nutricion",
  "ortopedia",
  "podologia",
  "cardiologia_endocrinologia",
] as const;

export const clinicConfigSchema = z.object({
  clinic_vertical: z.enum(CLINIC_VERTICAL_ENUM, {
    errorMap: () => ({ message: "Selecciona el modelo de tu clínica para continuar" }),
  }),
  primary_specialties: z
    .array(z.enum(PRIMARY_SPECIALTY_ENUM))
    .min(1, "Selecciona al menos una especialidad"),
  other_specialty_text: z.string().max(100).optional().nullable(),
});

export type ClinicConfigInput = z.infer<typeof clinicConfigSchema>;
```

### React Query keys

```typescript
// vitalia/frontend/src/features/vitalia/api/clinic-config.ts

export const CLINIC_CONFIG_QUERY_KEYS = {
  onboardingStatus: (tenantId: string) =>
    ["vitalia", tenantId, "onboarding", "status"] as const,
  clinicConfig: (tenantId: string) =>
    ["vitalia", tenantId, "onboarding", "clinic-config"] as const,
};
```

### Mutations

```typescript
// useSaveClinicConfig: POST /api/v1/onboarding/clinic-config
// Invalida: CLINIC_CONFIG_QUERY_KEYS.onboardingStatus(tenantId)
// onSuccess: avanza al siguiente paso del wizard (state local)
// onError: muestra toast Sonner destructive
```

---

## § Microcopy (Spanish neutro — tabla)

| Key | Texto |
|---|---|
| `clinicVertical.title` | "¿Qué tipo de clínica describe mejor tu práctica?" |
| `clinicVertical.subtitle` | "Esto personaliza el comportamiento de tus agentes." |
| `clinicVertical.errorRequired` | "Selecciona el modelo de tu clínica para continuar" |
| `clinicVertical.options.dental_clinic.label` | "Clínica dental" |
| `clinicVertical.options.dental_clinic.hint` | "Odontología general y especialidades" |
| `clinicVertical.options.medspa_aesthetic.label` | "MedSpa / Estética" |
| `clinicVertical.options.medspa_aesthetic.hint` | "Procedimientos estéticos y dermatología" |
| `clinicVertical.options.mental_health_center.label` | "Salud mental" |
| `clinicVertical.options.mental_health_center.hint` | "Psicología y psiquiatría" |
| `clinicVertical.options.primary_care.label` | "Medicina general y familiar" |
| `clinicVertical.options.primary_care.hint` | "Atención primaria y medicina familiar" |
| `clinicVertical.options.multispecialty.label` | "Clínica multispecialidad" |
| `clinicVertical.options.multispecialty.hint` | "Múltiples especialidades bajo un mismo techo" |
| `clinicVertical.options.wellness_spa.label` | "Wellness y bienestar" |
| `clinicVertical.options.wellness_spa.hint` | "Tratamientos integrales y bienestar" |
| `clinicVertical.options.telehealth_only.label` | "Telemedicina / Digital" |
| `clinicVertical.options.telehealth_only.hint` | "Consultas 100% remotas y digitales" |
| `clinicVertical.options.rehab_center.label` | "Rehabilitación" |
| `clinicVertical.options.rehab_center.hint` | "Fisioterapia, recuperación y rehabilitación" |
| `primarySpecialties.title` | "¿Qué especialidades ofrece tu equipo?" |
| `primarySpecialties.subtitle` | "Puedes seleccionar varias. Esto ayuda a tus agentes a contextualizar recomendaciones." |
| `primarySpecialties.searchPlaceholder` | "Buscar especialidad..." |
| `primarySpecialties.errorRequired` | "Selecciona al menos una especialidad" |
| `primarySpecialties.otherLabel` | "+ Otra especialidad" |
| `primarySpecialties.otherPlaceholder` | "¿Cuál? (ej: Genética médica)" |
| `primarySpecialties.selectedCount` | "{n} especialidad seleccionada" / "{n} especialidades seleccionadas" |
| `primarySpecialties.options.odontologia` | "Odontología general" |
| `primarySpecialties.options.estetica_dermatologia` | "Estética y dermatología" |
| `primarySpecialties.options.psicologia_psiquiatria` | "Psicología y psiquiatría" |
| `primarySpecialties.options.medicina_general` | "Medicina general" |
| `primarySpecialties.options.ginecologia` | "Ginecología y obstetricia" |
| `primarySpecialties.options.pediatria` | "Pediatría" |
| `primarySpecialties.options.oftalmologia` | "Oftalmología" |
| `primarySpecialties.options.fisioterapia` | "Fisioterapia" |
| `primarySpecialties.options.nutricion` | "Nutrición y dietética" |
| `primarySpecialties.options.ortopedia` | "Ortopedia y traumatología" |
| `primarySpecialties.options.podologia` | "Podología" |
| `primarySpecialties.options.cardiologia_endocrinologia` | "Cardiología y endocrinología" |
| `confirmStep.title` | "Resumen de tu configuración" |
| `confirmStep.editLink` | "Editar" |
| `confirmStep.cta` | "Confirmar y continuar" |
| `confirmStep.agentNote` | "Tu asistente Valeria usará esta información para personalizar cada interacción con tus pacientes." |
| `cta.next` | "Continuar" |
| `cta.back` | "Atrás" |
| `error.networkFailure` | "No pudimos guardar tu configuración. Intenta de nuevo." |

---

## § Responsive breakpoints

| Breakpoint | Columnas tarjetas vertical | Layout chips especialidades |
|---|---|---|
| `sm` (< 640px) | 1 columna | chips en wrap, ancho 100% cada uno |
| `md` (640–1023px) | 2 columnas | chips en wrap, 50% aprox |
| `lg` (≥ 1024px) | 4 columnas (2 filas de 4) | chips en wrap flexible |

El wizard de onboarding usa `max-w-2xl mx-auto` centrado. El `ClinicVerticalSelector` adapta su grid a `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`.

El `PrimarySpecialtiesSelector` usa `flex flex-wrap gap-2` para los chips — se adapta naturalmente sin breakpoints explícitos.

Botones de navegación: en mobile se apilan verticalmente (`flex-col`) con "Continuar" arriba; en desktop side-by-side a la derecha (`flex-row justify-end`).

---

## § Accessibility

### Semántica obligatoria

- `ClinicVerticalSelector`: `<fieldset role="radiogroup" aria-labelledby>` con `<legend>`. Cada tarjeta es un `<label>` con `<input type="radio" className="sr-only">`. Selección via Enter / Space / flechas.
- `PrimarySpecialtiesSelector`: `<div role="group" aria-labelledby>` con chips `<button type="button" aria-pressed aria-label>`. Multi-select sin radiogroup (permite múltiples).
- Step indicator: elemento con `role="list"` + cada paso como `role="listitem"`, el activo con `aria-current="step"`.
- Mensajes de error: `role="alert"` + `aria-live="assertive"` (los errores de validación deben anunciarse inmediatamente).
- Botón "Continuar" durante loading: `aria-busy="true"` + `disabled` + texto cambia a "Guardando...".
- Campo free-text "Otra": cuando aparece, `aria-hidden="false"` + `aria-required="false"` + reciibe foco automáticamente via `useEffect`.

### Contraste
- Texto principal: ratio ≥ 4.5:1 sobre fondo card (WCAG AA).
- Tarjeta seleccionada: borde brand + ring, perceptible sin depender únicamente de color (checkmark visual adicional).
- Chip seleccionado: borde + fondo + texto brand, no solo fondo.

### Foco visible
- Todos los elementos interactivos deben tener `focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2`.
- Nunca `outline: none` sin reemplazo visible.

---

## § Telemetría

> Path: `vitalia/backend/src/modules/vitalia/_shared/telemetry/` (módulo existente)

| Evento | Cuándo | Propiedades |
|---|---|---|
| `onboarding_started` | Middleware detecta clinic_vertical=NULL + redirige | `tenant_id`, `step_at: "clinic_vertical"` |
| `onboarding_clinic_vertical_selected` | Usuario selecciona una tarjeta (sin enviar aún) | `tenant_id`, `clinic_vertical`, `step_at: "1b"` |
| `onboarding_specialties_selected` | Usuario hace clic en "Continuar" en paso 1c exitosamente | `tenant_id`, `clinic_vertical`, `specialties_count`, `has_other: bool`, `step_at: "1c"` |
| `onboarding_completed` | POST /onboarding/clinic-config retorna 200 | `tenant_id`, `clinic_vertical`, `primary_specialties`, `duration_ms` |
| `onboarding_abandoned` | Usuario cierra el wizard sin completar (beforeunload / timeout sesión) | `tenant_id`, `step_at: string`, `reason: "closed" \| "timeout"` |
| `onboarding_error` | POST falla con error de red o 5xx | `tenant_id`, `error_type`, `step_at` |

Los eventos NO deben incluir `primary_specialties` en texto libre (podría contener PHI si el usuario escribe en "Otra"). Solo `specialties_count` y `has_other: bool`.

---

## § Brand voice
N/A — chrome UI de tenant onboarding institucional. No aplica voz de agente per-tenant. Toda la UI usa microcopy fijo en `MICROCOPY_ONBOARDING` (español neutro, sin voseo, tono amigable y profesional).

---

## § ADR citation
Esta story implementa el patrón **ADR-vitalia-004** (route group `(shell-organism)` + FSD-Lite + Server-First + RHF/Zod + DDD BE). Aunque el onboarding vive fuera del `(shell-organism)` route group, sigue el mismo stack tecnológico:
- Server Component página delega a Client Component (patrón D9)
- Zod schemas en `features/vitalia/schemas/`
- React Query para state server + mutations
- Shadcn primitives como base UI
- DDD en backend: `onboarding/domain/` + `onboarding/application/services/` + `onboarding/api/`

El architect debe citar ADR-vitalia-004 verbatim en `03-arch.md` y decidir si este step vive en `/onboarding/wizard` extendido o en una página dedicada `/onboarding/clinic-config` (Open question #1).

---

## § Open questions

> Chris responde en la siguiente iteración. **OQ-5 ratificada 2026-05-26 — D3=A — ver § Ratified decisions abajo.**

| # | Pregunta | Opciones | Impacto |
|---|---|---|---|
| OQ-1 | ¿El paso de `clinic_vertical` + `primary_specialties` se agrega al wizard de 3 pasos existente (convirtiéndolo en 4-5 pasos) o es una página dedicada `/onboarding/clinic-config` que aparece **antes** de entrar al wizard? | (A) Wizard extendido — coherente visualmente, 1 flujo. (B) Página dedicada — más limpio técnicamente, separación de concerns. | Cambia `WizardOnboardingLayout` vs nueva página. |
| OQ-2 | Cuando el tenant cambia la vertical post-onboarding (desde `vitalia-fase2-config-cuenta`), ¿se conservan las `primary_specialties` o se resetean? | (A) Reset automático + notificación. (B) Se conservan, el admin las edita manualmente. | Afecta `config-cuenta` story y BE migration. |
| OQ-3 | ¿El paso de revisión/confirmación (step 4 en wireframe) es obligatorio o se puede skipear con un "Listo, confirmar"? | (A) Obligatorio — menos errores. (B) Opcional — más fluido. | Reduce fricción si (B). |
| OQ-4 | ¿Se muestra un "step count" explícito (ej: "Paso 2 de 4") o solo un progress bar sin números? | (A) Número explícito — más orientación. (B) Solo barra de progreso — más limpio. | Puro UX/visual. |
| ~~OQ-5~~ | ~~¿La `clinic_vertical` que se captura en este wizard **reemplaza** el campo `clinic_type` legacy o coexisten?~~ | **RATIFICADA D3=A (2026-05-26)** — REPLACE legacy `clinic_type` + migration BE + FE. Detalle abajo. | — |

## § Ratified decisions

### D3 (2026-05-26) — `clinic_vertical` REPLACE legacy `clinic_type`

**Decision:** `clinic_vertical` (8 valores: `dental_clinic | medspa_aesthetic | mental_health_center | primary_care | multispecialty | wellness_spa | telehealth_only | rehab_center`) reemplaza definitivamente el campo legacy `clinic_type` (`ClinicType = "dental" | "psychology" | "psychiatry" | "wellness"`).

**Rationale:** `clinic_type` legacy es un enum de 4 valores que mezcla specialty con vertical (la trap de Doctocliq); el nuevo `clinic_vertical` separa responsabilidad y agrega 4 valores nuevos (`medspa_aesthetic`, `primary_care`, `multispecialty`, `telehealth_only`, `rehab_center`). Coexistencia genera deuda técnica permanente.

**Migration mapping (legacy → new):**

| `clinic_type` legacy | `clinic_vertical` nuevo | `primary_specialties` seed |
|---|---|---|
| `dental` | `dental_clinic` | `[odontologia]` |
| `psychology` | `mental_health_center` | `[psicologia_psiquiatria]` |
| `psychiatry` | `mental_health_center` | `[psicologia_psiquiatria]` |
| `wellness` | `wellness_spa` | `[]` (free-text "otra" si applica) |

**Scope added a la story:**

- **BE migration Alembic idempotente:** copy `clinic_type` → `clinic_vertical` con mapping arriba en mismo script + drop legacy column al final (rollback-safe — keep `clinic_type` for 1 release como deprecated antes drop)
- **FE schema update:** `vitalia/frontend/src/features/vitalia/schemas/clinic-profile-schema.ts` reemplaza enum `ClinicType` por `ClinicVertical` + `PrimarySpecialty[]`
- **All consumers refactor (16 archivos identificados grep):**
  - `vitalia/backend/scripts/seed_fixture_clinics.py`
  - `vitalia/backend/tests/e2e/test_cross_tenant_isolation_e2e.py`
  - `vitalia/backend/tests/e2e/test_onboarding_dental_e2e.py`
  - `vitalia/backend/alembic/versions/032_f2_s1_vitalia_agenda.py` (existing migration — verify no conflict; nueva migration es 033+)
  - `vitalia/backend/tests/unit/application/test_onboarding_service.py`
  - `vitalia/backend/tests/unit/api/test_patient_dtos.py`
  - `vitalia/backend/src/modules/vitalia/application/services/onboarding_service.py`
  - `vitalia/backend/src/modules/vitalia/api/routes.py`
  - `vitalia/backend/src/modules/vitalia/api/dtos/onboarding_dtos.py`
  - `vitalia/backend/src/modules/vitalia/api/dtos/treatment_dtos.py`
  - `vitalia/backend/src/modules/vitalia/copilot/module_registry_entry.py`
  - `vitalia/frontend/e2e/specs/vitalia/onboarding-psych-sanare.smoke.spec.ts`
  - `vitalia/frontend/e2e/fixtures/{aurora-dental-ar,mindful-psych-cl,clinic-context,sanare-latam-mx}.fixture.ts`
  - `vitalia/frontend/tests/unit/features/vitalia/schemas/clinic-profile-schema.test.ts`
  - `vitalia/frontend/src/features/vitalia/components/onboarding-step-1-client.tsx`

**Lisa-marca downstream:** lisa-marca lee `clinic_vertical` + `primary_specialties` (NO legacy `clinic_type`). Display read-only en sub-sección Identidad + link "Editar configuración inicial" → `/onboarding/clinic-config`.

**Estimación impacto en story dev_days:** +1-2 días por migration + 16-archivos refactor (originalmente 2-3 → ahora 3-5 días).

### D2 (2026-05-26) — Visual extraction promotion escalation

**Decision:** Pipeline visual identity extraction descubierto en backup `ap_sales_agent` se escala a promotion candidate via `/pm-luana`.

**Proposal path:** `docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md`

**Impact on this story:** N/A (onboarding no consume visual extraction).

**Impact on lisa-marca (downstream story):** sub-sección Identidad ships con stub local `pending_visual_extraction()` que retorna `BrandVisuals.empty()`. Botón "Extraer desde mi sitio web" disabled con tooltip "Próximamente". Post-lift accepted, ticket 1-día reemplaza stub por engine import + habilita botón.

---

## § Deliverables preliminares (sujetos a arch decision OQ-1)

> Asume opción A (wizard extendido). Si architect elige B, los paths cambiarán.

### Frontend

| File | Acción |
|---|---|
| `vitalia/frontend/src/features/vitalia/components/clinic-vertical-selector.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/components/primary-specialties-selector.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/components/onboarding-step-vertical-client.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/components/onboarding-step-specialties-client.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/components/clinic-config-confirm-step.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/schemas/clinic-config-schema.ts` | NEW |
| `vitalia/frontend/src/features/vitalia/api/clinic-config.ts` | NEW |
| `vitalia/frontend/src/features/vitalia/config/microcopy.ts` | EXTEND (keys `clinicVertical.*` + `primarySpecialties.*`) |
| `vitalia/frontend/src/features/vitalia/types/vitalia.types.ts` | EXTEND (`ClinicVertical`, `PrimarySpecialty` types) |
| `vitalia/frontend/src/app/onboarding/wizard/page.tsx` | MODIFY (o NUEVO `/clinic-config/page.tsx` si OQ-1=B) |

### Backend

| File | Acción |
|---|---|
| `vitalia/backend/src/modules/vitalia/onboarding/domain/enums.py` | EXTEND (ClinicVertical, PrimarySpecialty enums) |
| `vitalia/backend/src/modules/vitalia/onboarding/application/services/clinic_config_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/onboarding/api/clinic_config_router.py` | NEW |
| Alembic migration | NEW (columns `clinic_vertical`, `primary_specialties JSONB`, `other_specialty_text` en tabla tenants o nueva tabla `clinic_configs`) |

### Tests

| File | Acción |
|---|---|
| `vitalia/backend/tests/modules/vitalia/onboarding/test_clinic_config_service.py` | NEW |
| `vitalia/frontend/src/features/vitalia/components/__tests__/clinic-vertical-selector.test.tsx` | NEW |
| `vitalia/frontend/src/features/vitalia/components/__tests__/primary-specialties-selector.test.tsx` | NEW |
| `vitalia/frontend/e2e/onboarding/clinic-config-happy.spec.ts` | NEW |
| `vitalia/frontend/e2e/onboarding/clinic-config-validation.spec.ts` | NEW |

---

## § Notas compliance (informativas, no scope de esta story)

Los siguientes datos capturados aquí **alimentarán** stories futuras de compliance:

- `mental_health_center` → futura activación `vitalia_prohibited_phrases` safeguards salud mental (Colombia Ley 2460/2025 + MX LGS ene-2026)
- `medspa_aesthetic` → futura activación validaciones COFEPRIS/ANVISA para claims estéticos
- `dental_clinic` → futura integración odontograma legal
- `psicologia_psiquiatria` specialty → flag para safeguards adicionales en Camila-voz y Valeria pacientes

Esta story NO implementa ninguno de estos safeguards. Solo persiste los datos que los activarán.
