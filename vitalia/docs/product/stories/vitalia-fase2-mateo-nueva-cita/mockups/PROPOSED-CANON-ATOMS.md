# Átomos propuestos al canon @luana/ui-kit

Propuestas de adición al canon detectadas en el refinamiento de `vitalia-fase2-mateo-nueva-cita`.
Ruteo: `/pm-luana` promotion gate (ui-kit es CORE). Greenlit por Chris 2026-06-22.

---

Cuatro primitivas que la hoja "Nueva cita" (agenda de Mateo, vitalia) necesita y el canon
`@luana/ui-kit` todavía no tiene. Cada una es transversal (no salud-específica) → candidata
real a vivir en el kit compartido, no en `features/scheduling`. La mini-vista del día
(`DayAvailabilityStrip`) NO entra acá: es componente de feature scheduling, lift-candidate
aparte.

Contexto visual: ver `mockups/nueva-cita.html` (cada átomo está marcado `★ PROPUESTO` inline
+ galería "Átomos propuestos al canon" al final del documento + caja "Mapeo al canon").

---

## 1 · FormActionBar

- **Nombre:** `FormActionBar`
- **Archivo destino:** `core/@luana/ui-kit/src/forms/FormActionBar.tsx`
- **Motivación:** El canon hoy solo cubre autosave (`use-autosave` + `FloatingAutosaveIndicator`). Falta el segundo modo: la barra sticky de submit explícito para flujos de crear / submit (Nueva cita, alta de entidad).
- **API / props propuesta:**
  ```tsx
  <FormActionBar
    hint?={ReactNode}          // texto izquierda, ej. "Sin guardar todavía"
    cancelLabel={string}       // ej. "Cancelar"
    submitLabel={string}       // ej. "Crear cita"
    onCancel={() => void}
    onSubmit={() => void}
    submitting?={boolean}      // deshabilita + spinner en submit
    submitDisabled?={boolean}  // bloqueo por validación (ej. disponibilidad)
    accent?={AgentColor}       // color del primary, ej. "mateo"
  />
  ```
  - Sticky `bottom: 0`, `border-top` + `box-shadow` hacia arriba (mismo lenguaje que la franja N3 invertida).
  - El primary toma el color de agente vía `accent` (token, no hex).
- **Story destino:** `core/@luana/ui-kit/stories/forms/FormActionBar.stories.tsx`

---

## 2 · Badge — variants success | warning

- **Nombre:** `Badge` (extensión de variants)
- **Archivo destino:** `core/@luana/ui-kit/src/feedback/Badge.tsx` (extender el componente existente)
- **Motivación:** Hoy `Badge` solo tiene `default | secondary | destructive | outline`. Faltan `success` y `warning` para estados semánticos (disponibilidad del médico: Disponible / Fuera de horario / Sin horario). Hoy se resuelven con clases ad-hoc (`avail-chip ok/outhours`) → reinvención de primitiva.
- **API / props propuesta:**
  ```tsx
  <Badge variant="success" | "warning">{children}</Badge>
  ```
  - `success` → token `--c-success` / `--c-success-soft`.
  - `warning` → token `--c-warning` / `--c-warning-soft`.
  - Soporte dark-mode vía los tokens soft ya existentes.
- **Story destino:** `core/@luana/ui-kit/stories/feedback/Badge.stories.tsx` (agregar grupo de variants semánticas)

---

## 3 · PageHeader — back-pill

- **Nombre:** `PageHeader` (modo back-pill)
- **Archivo destino:** `core/@luana/ui-kit/src/page/PageHeader.tsx`
- **Motivación:** Para hojas-leaf (Nueva cita, Crear paciente) hace falta un retorno explícito a la sección raíz sin abusar de `EntitySubNavBar` (que es nav de entidad, no de hoja). El back-pill `‹ {RootLabel}` es el patrón correcto de retorno + título de la hoja.
- **API / props propuesta:**
  ```tsx
  <PageHeader
    backLabel?={string}        // ej. "Agenda" → renderiza pill "‹ Agenda"
    onBack?={() => void}
    title={string}             // ej. "Nueva cita"
    subtitle?={ReactNode}      // ej. "Mateo · Agenda — Clínica Dental Sonrisa"
    leading?={ReactNode}       // dot de agente / ícono
    actions?={ReactNode}       // botones a la derecha
  />
  ```
  - Franja full-bleed (`bg-card` + `border-bottom` + sticky), mismo lenguaje que Ribbon / SubTabs — NUNCA card redondeada (canon §1).
  - El back-pill usa flechita `‹`, no `←`.
- **Story destino:** `core/@luana/ui-kit/stories/page/PageHeader.stories.tsx`

---

## 4 · EntityPicker — createAction

- **Nombre:** `EntityPicker` (prop `createAction`)
- **Archivo destino:** `core/@luana/ui-kit/src/entity/EntityPicker.tsx` (extender el componente existente)
- **Motivación:** Patrón pick-or-create: cuando la entidad buscada no existe, crearla sin salir del picker (caso "+ Crear paciente" en Nueva cita). Hoy `EntityPicker` solo selecciona de lo existente.
- **API / props propuesta:**
  ```tsx
  <EntityPicker
    createAction?={{
      label: (query: string) => string,   // ej. q => `Crear paciente «${q}»`
      onCreate: (query: string) => void,   // abre la hoja-leaf de alta + vuelve preseleccionado
    }}
    ...restEntityPickerProps
  />
  ```
  - Renderiza una fila final en el panel (`border-top` punteado) con `＋ {label}` cuando hay query sin match exacto.
  - `onCreate` navega a la hoja de alta (full-page leaf) y vuelve al picker con la entidad recién creada preseleccionada.
- **Story destino:** `core/@luana/ui-kit/stories/entity/EntityPicker.stories.tsx` (agregar variant `with-create-action`)

---

## Nota de ruteo

Las 4 son transversales (formularios, feedback, page chrome, entity selection) → pertenecen a
`@luana/ui-kit` (CORE), no a una marca. Por eso van por el **promotion gate `/pm-luana`** antes
de que `/architect` las consuma en `03-arch.md`. La marca (vitalia) las DESCUBRIÓ; el canon las
posee.
