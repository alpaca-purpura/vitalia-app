# Capability Protocol — Story ↔ Capability Doctrine (v4 cement 2026-05-28)

**v4 (cement 2026-05-28):** atomics MUERTO, scenario es la unidad atómica. outcome MUERTO. Ver `docs/process/lifecycle.md`.

**Cement-date v4:** 2026-05-28 (colapso del modelo: atomics/outcome/phase/module-alias eliminados · scenario es la unidad atómica de comportamiento).
**Cement-date v3.2:** 2026-05-28 (extiende v3.1 misma fecha · 4 bloques nuevos aditivos + header convention código).
**Cement-date v3:** 2026-05-27 (extiende v2 misma fecha · Sec 7-9 v3 son aditivas).
**Origen v3:** sesión `/pm-vitalia` 2026-05-27 — ADR-vitalia-005 (4 dimensiones + dev_preview + areas/).
**Origen v3.2:** sesión bidirectional code↔cap mapping 2026-05-28 — Chris ratificó P1-P4 (scenarios híbrido + Copy gherkin + comentario header + validator cross-check).
**SSoT capability YAML schema v4.**

> Doctrina cementada: **Story** es transitoria (idea→done→archive), **Capability** es permanente (append-only ledger). Cada story declara `cap_target` + `cap_change_type` para mantener trazabilidad qué tocó qué. Cada cap declara 4 dimensiones (`tech_module` + `agent_owner` + `functional_area` + `user_visible`) + bloque `dev_preview` para que el producto sea navegable en lenguaje humano. La **unidad atómica de comportamiento** es el `scenario` (Gherkin Given/When/Then), no el atomic.

---

## Sección 1 · Story vs Capability — la separación

| Dimensión | Story | Capability |
|---|---|---|
| Naturaleza | unidad **transitoria** de trabajo | unidad **permanente** del producto |
| Lifecycle | idea → refining → ... → done → archive | viva mientras el cap exista en el producto |
| Path activo | `{brand}/docs/product/stories/{id}/` | `{brand}/docs/product/capabilities/{module}/{cap}.yaml` |
| Path archive | `{brand}/docs/archive/{year}/stories/{id}/` | N/A (cap nunca se archiva, queda en `capabilities/`) |
| Append-only | NO (los archivos editan + se cierran) | SÍ (`change_log[]` append-only) |
| Ratifica Chris | sí (en cada transition relevante) | no (Chris ratifica via story que la toca) |

**Regla cardinal:** una story sin `cap_target` declarado en checkpoint NO puede pasar de `refining → refined`. El cap target define qué pieza del producto se toca. Si la story crea un cap nuevo, `cap_target` = el slug nuevo + `cap_change_type: new`.

---

## Sección 2 · Schema cap YAML v4

> **★ HB-51 (cement 2026-06-05) — NUNCA hand-authores una cap.** El formato dejó de
> salir del criterio del modelo y pasó a CÓDIGO determinístico. Para crear una cap:
> **`make new-cap BRAND=<b> MODULE=<m> SLUG=<s> AREA=<box>.<area>`** (genera el YAML
> schema-válido por construcción · REFUSE si el cap_id ya existe). Vos llenás el
> **contenido** (`# TODO`), nunca el **formato**. El schema de abajo es la referencia
> del modelo; el SSoT ejecutable es `scripts/new_cap.py` + `scripts/validate_caps_schema.py`
> + los 6 gates G1-G6 (`make cap-doctor` reporta toda la deriva). Detalle: las 8 capas
> en `docs/process/cap-deterministic-enforcement.md`.

```yaml
---
capability_id: vitalia.scheduling.valeria-agenda
tech_module: scheduling                   # REQUIRED · kebab path canónico (DDD backend · FSD frontend)
slug: valeria-agenda
status: live                              # live | beta | deprecated | sunset
license: brand-local                      # brand-local | core-shared

# Dimensiones v3 (4 campos · cement 2026-05-27 · REQUIRED todos)
agent_owner: mateo                        # caja del mapa (v2.0) — ver SYSTEM-MAP.yaml `zones`
functional_area: mateo.agenda             # <caja>.<area-kebab>
user_visible: true                        # true | false
nature: feature                           # feature | scaffold | extension-point

# Ledger fields (v2 cement 2026-05-27)
created_in_story: vitalia-fase2-valeria-agenda
created_date: 2026-05-27
last_modified: 2026-05-27
package_version: vitalia-fase2-v1.0.0
package_path: vitalia/backend/src/modules/vitalia/scheduling/

# Architecture
architecture_pattern: ADR-vitalia-004     # ADR slug si aplica
hipaa_lite_overlay: true                  # opcional (vitalia-specific)

# Capability lineage
parent_cap: null                          # null si root · slug si derive
derives_capabilities: []                  # caps hijas spawned via derive

# Scenarios — unidad atómica de comportamiento (ver Sección 11 para schema completo)
scenarios:
  - id: doctor-ve-agenda-semanal
    name: "Doctor abre su agenda de la semana"
    actor: doctor
    status: live
    given: "Doctor autenticado con clinic_scope=clinic-A"
    when: "Navega a /valeria/agenda"
    then: "Ve calendario semana actual con turnos coloreados por estado pago"
    e2e_test: "vitalia/frontend/e2e/specs/valeria-agenda-list.spec.ts"
    added_in_story: vitalia-fase2-valeria-agenda
    added_date: 2026-05-27

# Append-only ledger
change_log:
  - story_id: vitalia-fase2-valeria-agenda
    date: 2026-05-27
    type: new                              # new | fix | extend | derive
    summary: "Implementación inicial · vista calendario + drag-to-reschedule + advisory lock"
    scenarios_added: ["doctor-ve-agenda-semanal"]
    merge_sha: 4562140c
    status: done                           # in-progress | done
---

# Resumen markdown opcional debajo del frontmatter
```

---

## Sección 3 · `cap_change_type` ∈ {new, fix, extend, derive}

Cada story declara qué tipo de cambio aplica al cap target. Es enforce-able via pre-commit hook + auditor Phase D + skill /architect coherence check.

| Tipo | Cuándo aplica | Efecto en cap YAML |
|---|---|---|
| `new` | Story crea un cap que NO existía antes | Crea el YAML + `change_log[0]` + scenarios iniciales |
| `fix` | Story arregla bug/regresión SIN agregar funcionalidad | Append `change_log` entry (scenarios NO cambian) |
| `extend` | Story agrega capacidades NUEVAS al mismo cap | Append `change_log` + append nuevos scenarios |
| `derive` | Story crea cap HIJO basado en uno existente | Crea YAML hijo con `parent_cap: {origen}` + `change_log[0]` + actualiza `derives_capabilities[]` del padre |

### Ejemplos:

**new** — F2-S1 `valeria-agenda` (cap nueva):
```yaml
# story checkpoint
cap_target: valeria-agenda
cap_change_type: new
```

**fix** — F1-FIX `shell-layout-5050-race-fix`:
```yaml
cap_target: shell.layout-5050
cap_change_type: fix
```

**extend** — F2-S7v2 `lisa-marca v2` agrega scenarios adicionales a `lisa-marca`:
```yaml
cap_target: lisa.marca
cap_change_type: extend
```

**derive** — Story futura crea `valeria.agenda.mobile` como cap derivado de `valeria.agenda`:
```yaml
cap_target: valeria.agenda.mobile
cap_change_type: derive
parent_story: vitalia-fase2-valeria-agenda
# en cap YAML target:
# parent_cap: valeria-agenda
```

---

## Sección 5 · Fase F MERGE — ledger logic en `/pm-{brand}`

Cuando una story pasa `reviewing → done` (Fase F MERGE), `/pm-{brand}` aplica logic del `cap_change_type` al YAML target:

### Rama A — `cap_change_type: new`
1. Crear la cap con **`make new-cap BRAND=<b> MODULE=<module> SLUG=<slug> AREA=<box>.<area>`** (HB-51 · NUNCA hand-author el YAML — el generator lo produce schema-válido + REFUSE si ya existe), luego llenar el **contenido** (`# TODO`)
2. `change_log[0]` con `type: new` + `summary` + `scenarios_added` listando scenarios iniciales
3. `created_in_story` = story.id
4. `created_date` = today
5. Append commit body: "cap nueva: {slug}"

### Rama B — `cap_change_type: fix`
1. Append `change_log` entry con `type: fix`, `scenarios_added: []`
2. NO modifica `scenarios[]` (eso solo cambia con extend)
3. Update `last_modified` = today

### Rama C — `cap_change_type: extend`
1. Append `change_log` entry con `type: extend` + lista de scenarios nuevos
2. Append nuevos scenarios al array `scenarios[]` con `added_in_story` apuntando a esta story
3. Update `last_modified` = today

### Rama D — `cap_change_type: derive`
1. Crear cap YAML hijo con schema v4 + `parent_cap: {origen_slug}`
2. `change_log[0]` con `type: derive` + `summary` referenciando el cap padre
3. Update cap padre: append `derives_capabilities: [hijo_slug]`
4. Update padre `last_modified` (modificación de su array `derives_capabilities`)

**Order matters:** en `derive`, primero crear cap hijo (con parent_cap declarado), luego actualizar padre. Escritura atómica para evitar estado inconsistente.

### Enforce reglas Fase F.3 (cement 2026-05-28 · cap verification v4)

Antes de cerrar el merge commit, `/pm-{brand}` MUST verificar que el `change_log` entry de esta story cumpla:

| `cap_change_type` | `change_log[ultimo].scenarios_added.length` | Otros checks |
|---|---|---|
| `new` | `>= 1` **REQUIRED** (si `user_visible: true`) | `scenarios[]` overall debe tener ≥1 scenario con shape válido (campos REQUIRED presentes) |
| `extend` | `>= 1` **REQUIRED** | `scenarios[]` debe haber crecido respecto al commit anterior (diff positivo) |
| `fix` | `>= 0` (puede ser `[]`) | NO requiere scenario nuevo · solo append `change_log` con fix entry |
| `derive` | `>= 1` **REQUIRED** en cap hijo | `parent_cap.derives_capabilities[]` debe listar el hijo nuevo |

**Violación detectada** → REFUSE cerrar Fase F.3. Escalar a Chris con message: "cap_change_type={type} declarado pero scenarios_added={n} en change_log · mínimo requerido: 1".

**Enforce point:** `scripts/reconcile_capabilities.py --validate-ledger` detecta violaciones post-merge. Pre-commit hook:
- HARD block en `main/release/*` si commit toca checkpoint con `cap_change_type ∈ {new, extend}` y NO toca cap YAML correspondiente.
- WARN advisory en `wip/*` (no bloquea, muestra mensaje).

**Definición de DONE (cement 2026-05-28):** una capability **no puede ser `live`** sin **≥1 scenario + e2e_test pasando**. `live` con scenarios vacíos = inválido. Esto mata el "verde por vacío".

---

## Sección 6 · Anti-patterns prohibidos

- ❌ Editar `scenarios[]` manualmente desde un commit que no sea Fase F MERGE de la story que los introduce
- ❌ Story sin `cap_target` declarado pasa `refining → refined` (skill /architect debe rechazar)
- ❌ Cross-brand mirror cap: dos brands replican el mismo cap → debe vivir en `core/luana-core-*/` (flujo engine `/pm-vitalia` — arch tests como gate)
- ❌ `change_log[]` modificado (no append) — viola append-only ledger
- ❌ Scenario con `added_in_story` que NO existe en `change_log[]` → inconsistencia (pre-commit hook bloquea)
- ❌ Cap nuevo con `parent_cap` declarado pero padre NO tiene este cap en `derives_capabilities[]` → inconsistencia
- ❌ `cap_change_type: extend` con archivos producidos que crean cap nuevo (incoherencia spec/code)
- ❌ Borrar scenario existente: NUNCA (deprecation cementada → marca `status: deprecated` + sigue en array)
- ❌ Cap YAML sin `agent_owner` o sin `functional_area` declarado (cement · pre-commit hook bloquea)
- ❌ Cap `user_visible: true` sin bloque `dev_preview` (cement · pre-commit hook bloquea)
- ❌ `agent_owner:` con valor fuera del set de cajas v2.0 vitalia `{lisa, mateo, adrian, lucas, camila, acceso, onboarding, configuracion, seguridad-cumplimiento, observabilidad, plataforma-tecnica, motor-agentico}` (cement · `config`/`infra` deprecadas, `valeria` = supervisora sin caja de valor)
- ❌ `functional_area:` sin pattern `<agent>.<slug-kebab>` (e.g. `valeria_agenda` con underscore → debe ser `valeria.agenda`)
- ❌ Crear cap nuevo cuando `functional_area` existente la cubre — refining favorece `extend` over `new` (rule anti-duplication-refining)
- ❌ Renombrar `tech_module:` post-merge (path canónico inmutable · usar `superseded_by:` si hay refactor real)
- ❌ Capability `live` con `scenarios: []` (verde por vacío · inválido)

---

## Sección 7 · Las 4 dimensiones de un cap (v3 cement 2026-05-27)

> Origen: ADR-vitalia-005. Acordado con Chris en sesión `/pm-vitalia` 2026-05-27.

Todo cap declara `change_log[]` + scenarios + **4 dimensiones de clasificación** que el cockpit usa para agrupar caps en lenguaje humano (vs el bucket "Otros módulos" actual).

### Las 4 dimensiones

| # | Campo YAML | Concepto | Valores válidos |
|---|---|---|---|
| 1 | `tech_module:` | dominio técnico (DDD backend · FSD frontend) — path canónico | `scheduling`, `crm`, `brand_studio`, ... (kebab del path real) |
| 2 | `agent_owner:` | la **caja** del mapa dueña de la cap (= `map_box`) | 5 especialistas + 3 cajas Plataforma + 4 cajas Infraestructura — **SSoT: `SYSTEM-MAP.yaml` `zones`** (tabla abajo) |
| 3 | `functional_area:` | sub-categoría **dentro** de la caja | `<caja>.<area-kebab>` (ej. `mateo.agenda`, `seguridad-cumplimiento.compliance`) |
| 4 | `user_visible:` | aparece en mapa principal del producto | `true` (default) · `false` (infra cross-cutting) |

**Regla cardinal:** todo cap (nuevo o existente) MUST declarar las 4 dimensiones. Cap sin `agent_owner` o sin `functional_area` válido → pre-commit hook bloquea y refining no avanza.

### Mapeo brand cajas → zonas (vitalia · v2.0 cement 2026-05-30)

> **SSoT del registro: `vitalia/docs/architecture/SYSTEM-MAP.yaml` `zones[].boxes`.** Esta tabla es vista derivada (no editar a mano por cap). La **zona se deriva** de la caja vía ese registro. `config`/`infra` quedaron DEPRECATED (sus áreas se promovieron a cajas propias). `valeria` = supervisora transversal (sidebar · runtime `motor-agentico`), NO es caja de valor en el Ribbon.

**Zona Agentes** (5 especialistas · `user_visible: true`):

| Caja (`agent_owner`) | Emoji | Subtitle | Functional areas |
|---|---|---|---|
| `lisa` | 🏥 | Mi Clínica | `lisa.marca` · `lisa.servicios` · `lisa.doctores` · `lisa.compliance` · `lisa.landing_public` |
| `mateo` | 📅 | Operar / Mi Día | `mateo.agenda` · `mateo.bookings` · `mateo.pacientes` |
| `adrian` | 💼 | Vender | `adrian.embudo` · `adrian.inbox` · `adrian.crm` · `adrian.reactivacion` · `adrian.outbound` · `adrian.propuestas` |
| `lucas` | 📣 | Marketing | `lucas.atribucion` · `lucas.bowtie` · `lucas.recomendaciones` · `lucas.referrals` · … |
| `camila` | 🌟 | Reputación + cohortes | `camila.reputacion` · `camila.reactivar` · `camila.multiplicar` · `camila.voz` |

**Zona Plataforma** (transversal user-facing · `user_visible: true`):

| Caja (`agent_owner`) | Functional areas |
|---|---|
| `acceso` | `acceso.auth` · `acceso.iam` |
| `onboarding` | `onboarding.onboarding_clinic` |
| `configuracion` | `configuracion.cuenta` · `configuracion.clinics` · `configuracion.conexiones` · `configuracion.patients-records` · `configuracion.admin` · `configuracion.fiscal` · `configuracion.avanzado` |

**Zona Infraestructura** (no-funcional · `user_visible: false`):

| Caja (`agent_owner`) | Functional areas |
|---|---|
| `seguridad-cumplimiento` | `seguridad-cumplimiento.compliance` · `seguridad-cumplimiento.scaffolding` |
| `observabilidad` | `observabilidad.observability` |
| `plataforma-tecnica` | `plataforma-tecnica.platform` · `plataforma-tecnica.payment` · `plataforma-tecnica.shell` · `plataforma-tecnica.map` · `plataforma-tecnica.reconciliation` · … |
| `motor-agentico` | `motor-agentico.copilot` · `motor-agentico.agentic-engine` · `motor-agentico.sales-agent-engine` |

Nota histórica multibrand: otras brands declaraban su propio `SYSTEM-MAP.yaml` por zonas (el lift del modelo vivió en el promotion protocol, hoy archivado en `docs/archive/2026/multibrand-legacy/`).

### Zona del mapa (5ª dimensión DERIVADA — cement 2026-05-30)

La caja (`agent_owner`) pertenece a una de **3 zonas** del mapa: **Agentes** (valor user-facing por trabajador) · **Plataforma** (transversal user-facing: Acceso/Onboarding/Configuración) · **Infraestructura** (no-funcional). La **zona NO se escribe a mano** por cap — se **deriva** del registro `{brand}/docs/architecture/SYSTEM-MAP.yaml` (`zones`). `user_visible` se alinea con la zona (Agentes/Plataforma → `true` · Infraestructura → `false`).

El **árbol de decisión** "¿en qué caja/zona aterriza esta cap?" — aplicado **desde la idea** por `/pm-{brand}`, `/po-ux`, `/po`, `/ux-agentico` — vive en `.claude/rules/paradigm-arquitectura.md`. Doctrina (3 planos + invariantes): `docs/architecture/luana-platform/PARADIGM.md` (+ `ADR-010`).

---

## Sección 8 · `user_visible` + `nature`

### `user_visible: true | false` (default true)

Define si el cap aparece en el **mapa principal** del cockpit (vista user-facing del producto) o solo cuando se activa el toggle "Mostrar infra".

| Cap es… | `user_visible:` | Ejemplos |
|---|---|---|
| Funcionalidad terminada que un user puede ver/usar | `true` | `valeria.agenda`, `lisa.identidad-marca`, `adrian.inbox` |
| Infra cross-cutting que habilita features pero no es navegable | `false` | `infra.observability`, `infra.platform`, `infra.payment` |
| Scaffolding (tests, fixtures, migrations, workers, ops) | `false` | `infra.scaffolding.playwright-smoke-suite`, `infra.scaffolding.3-clinic-fixture-latam` |

**Regla:** si `user_visible: true` → `dev_preview` block obligatorio (Sección 9).

### `nature: feature | scaffold | extension-point` (default feature)

| Valor | Significado | Ejemplos |
|---|---|---|
| `feature` | capacidad user-facing terminada | `valeria.agenda` · `adrian.inbox` |
| `scaffold` | estructura técnica sin user value directo | migrations · fixtures · test suites · cron workers |
| `extension-point` | cap que otras caps consumen (raro en brand · usual en core) | `compliance.phi-repository-base` |

Caps `nature: scaffold` siempre exentas de `dev_preview` (no hay "cómo llegar" porque no es navegable).

---

## Sección 9 · `dev_preview` block (obligatorio si `user_visible: true`)

> Propósito: responder en 1 vistazo "¿dónde está esto en la app? ¿qué endpoint pegar? ¿cómo verlo en development?".

```yaml
user_facing_name: "Agenda semanal de Valeria"
# Nombre human-readable de la capacidad (no el slug · no el tech_module)
# Máx 80 chars · Spanish neutro (NO voseo per .claude/rules/spanish-text.md
# salvo sales_agent voice)

user_facing_description: >
  La vista calendario con drag-to-reschedule donde Valeria muestra los turnos
  de la semana. El doctor arrastra un slot vacío para crear una reserva o
  arrastra un slot ocupado para reagendarlo.
# 2-5 líneas · Spanish neutro · lenguaje humano sin jerga técnica
# Lo que un médico clínica entendería leyendo

dev_preview:
  route: "/valeria/agenda"                # ruta Next.js · null si BE-only
  how_to_navigate: "Login → ribbon clic en avatar Valeria → sub-tab Agenda"
  # Pasos verbatim para llegar al cap en una sesión local dev

  main_component: "vitalia/frontend/src/features/scheduling/components/AgendaWeekly.tsx"
  # Path al componente FE principal · null si BE-only

  api_endpoints:                          # endpoints que el cap consume
    - "GET /api/v1/scheduling/slots?week={iso}"
    - "POST /api/v1/scheduling/appointments"

  e2e_test: "vitalia/frontend/e2e/specs/valeria-agenda-create.spec.ts"
  # Path al test Playwright que cubre el happy path · null si no hay E2E aún

  fixtures_required:                       # fixtures que el cap necesita pre-cargadas
    - "3-clinic-fixture-latam"

  storybook_url: null                      # opcional · null si no aplica
  loom_demo: null                          # opcional · link Loom 30s si Chris grabó demo
```

### Reglas de llenado

- `route:` **null** si cap es BE-only (no hay UI · ej. `infra.payment.mercado-pago-adapter`)
- `how_to_navigate:` siempre poblado si `route:` existe — Spanish neutro 1-2 oraciones
- `main_component:` path absoluto desde repo root — null si BE-only
- `api_endpoints:` lista de strings — vacía `[]` si cap es FE-only sin API
- `e2e_test:` null si cap no tiene E2E aún (advisory · no bloqueante)
- `fixtures_required:` vacía `[]` si cap no requiere fixtures

### Cap BE-only ejemplo

```yaml
agent_owner: infra
functional_area: infra.payment
user_visible: false
nature: feature
user_facing_name: "Adaptador Mercado Pago para reservas prepagadas"
user_facing_description: >
  Integra Mercado Pago para procesar pagos de reservas prepagadas en Vitalia.
  Genera preference, recibe webhook IPN, marca booking como paid.

dev_preview:
  route: null
  how_to_navigate: "BE-only · ver via tests de integración + logs payment_callback"
  main_component: null
  api_endpoints:
    - "POST /api/v1/payments/preference"
    - "POST /api/v1/payments/webhook/mercado-pago"
  e2e_test: null
  fixtures_required: []
```

---

## Sección 11 · Schema v3.2 — bloques nuevos (cement 2026-05-28)

> Origen: sesión bidirectional code↔cap mapping 2026-05-28. Chris ratificó P1-P4 (scenarios híbrido + Copy gherkin + comentario header + validator cross-check). Los bloques v3.2 son **estricto aditivos** — no modifican `identity`, `4 dimensions`, `dev_preview`, `scenarios`, ni `ledger`.

### Propósito v3.2

Que el cockpit Luana sea **la fuente verificable y narrada** de qué hace realmente el sistema:
1. **`access`** — extiende `dev_preview` con roles + multi-entry-point. Validator cross-checks contra `@require_phi_access` decorators del código.
2. **`scenarios`** — captura BDD user-facing (Given/When/Then) como SSoT permanente. Reemplaza navegar archive 01-spec.md.
3. **`business_rules`** — invariantes + HIPAA + retention + business logic explícitos.
4. **`related_capabilities`** — grafo dependencias (depends_on/enables/similar/obsoletes).

### Reglas obligatoriedad v3.2

- Bloques v3.2 son **opcionales** en v3.2 (compat con v3.1 caps existentes).
- Para caps `user_visible: true`, los bloques `access` + `scenarios` + `business_rules` se vuelven **REQUIRED** al merge Fase F.3 cuando `cap_change_type ∈ {new, extend}` (cement 2026-Q3).
- `related_capabilities` siempre opcional.
- v3.1 caps existentes migran gradualmente cuando se tocan via stories.

### Bloque 1 — `access` (extiende `dev_preview`)

```yaml
access:
  entry_points:                          # 1+ rutas para acceder al cap
    - path: "/valeria/agenda"             # REQUIRED · Next.js route O backend path
      navigation: "Login → ribbon Valeria → sub-tab Agenda"  # REQUIRED · Spanish neutro
      requires_role: [doctor, admin_clinic, nurse]  # REQUIRED si HIPAA · []  si público
      requires_clinic_scope: true         # OPTIONAL · default false · true = dual filter HIPAA
      entry_type: ui                      # OPTIONAL · ui | api | webhook | event | cli · default ui
  forbidden_roles: [marketing, patient]   # OPTIONAL · roles explícitamente denegados (audit)
  authentication: required                # REQUIRED · required | optional | none
```

**Roles canónicos vitalia** (per `vitalia/.claude/rules/hipaa-lite.md`):
- `doctor` · `nurse` · `admin_clinic` · `marketing` · `receptionist` · `patient`
- `staff_vitalia` (admin panel)

**Cross-check runtime (P4 ratificada):** validator `validate_code_cap_bidirectional.py` detecta drift entre `access.entry_points[].requires_role` y `@require_phi_access(roles=[...])` decorators en código + middleware Clerk. **Runtime mantiene enforcement actual · cap es fuente documental.**

### Bloque 2 — `scenarios` (BDD user-facing capability lifecycle)

```yaml
scenarios:
  - id: doctor-ve-agenda-semanal         # REQUIRED · kebab unique dentro del cap · max 60 chars
    name: "Doctor abre su agenda de la semana"  # REQUIRED · user-facing Spanish neutro · max 120 chars
    actor: doctor                         # REQUIRED · rol que actúa (debe estar en access.entry_points[].requires_role)
    status: live                          # REQUIRED · live | wip | deprecated
    given: "Doctor autenticado con clinic_scope=clinic-A"  # REQUIRED · 1 línea contexto inicial
    when: "Navega a /valeria/agenda"      # REQUIRED · 1 línea acción del actor
    then: "Ve calendario semana actual con turnos coloreados por estado pago"  # REQUIRED · 1+ líneas resultado esperado
    e2e_test: "vitalia/frontend/e2e/specs/valeria-agenda-list.spec.ts"  # OPTIONAL · path al test que cubre
    story_spec_ref: "vitalia/docs/archive/2026/stories/vitalia-fase2-valeria-agenda/01-spec.md#scenario-1"  # OPTIONAL · trazabilidad spec origen
    surface: FE                           # OPTIONAL · FE | BE | AGENTIC | FE+BE | FE+BE+AGENTIC (superficie del scenario)
    edge_cases:                           # OPTIONAL · lista narrativa Spanish neutro
      - "Semana sin turnos → empty state amigable con call-to-action 'agendar primer turno'"
      - "Doctor sin clinic_scope → 403 + redirect a setup clínica"
    added_in_story: vitalia-fase2-valeria-agenda  # REQUIRED · trazabilidad
    added_date: 2026-05-27                # REQUIRED · ISO date
    # deprecated_in_story: null           # OPTIONAL · si status=deprecated
    # deprecated_date: null               # OPTIONAL · ISO date
```

**Granularidad ratificada:**
- Scenarios cuelgan **directo de cap.scenarios[]** — son la unidad atómica de comportamiento.
- `surface` OPCIONAL para distinguir scenarios cross-surface (FE+BE / FE+BE+AGENTIC).
- Sin niveles intermedios: cap → scenarios → code/tests.

**Migración Gherkin P2 ratificada (Copy + story_spec_ref):**
- Scenarios principales (happy path + business rules) **copy verbatim** desde `01-spec.md` archive al cap YAML al merge Fase F.3.
- Edge cases extensos opcionalmente solo linkean al spec.
- Cap autocontenido = SSoT navegable sin necesidad de leer archive.

### Bloque 3 — `business_rules` (invariantes user-facing + HIPAA + retention)

```yaml
business_rules:
  - id: dual-tenant-clinic-filter         # REQUIRED · kebab unique dentro del cap
    rule: "Toda query a Appointment filtra tenant_id AND clinic_id (HIPAA dual filter)"  # REQUIRED · 1-2 líneas Spanish neutro
    enforcement:                          # REQUIRED · paths a rules/docs que enforce
      - ".claude/rules/tenant-isolation.md"
      - "vitalia/.claude/rules/hipaa-lite.md"
    code_ref: "vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories.py"  # OPTIONAL · path código que implementa
    severity: critical                    # REQUIRED · critical | high | medium | low
    audit_trail: true                     # OPTIONAL · default false · true = action genera audit_log row
```

### Bloque 4 — `related_capabilities` (grafo de dependencias)

```yaml
related_capabilities:
  depends_on:                             # OPTIONAL · caps que ESTE cap necesita activas
    - shell-organism.shell-vitalia
    - iam.luana-core-adoption
  enables:                                # OPTIONAL · caps que SE habilitan por este (rev de depends_on)
    - scheduling.bookings-prepagadas
  similar:                                # OPTIONAL · variantes/derive children
    - valeria.agenda.mobile
  obsoletes:                              # OPTIONAL · caps marcados deprecated por este (refactor)
    - valeria.legacy-agenda-v1
```

### Reglas Fase F.3 enforce v3.2 (extiende § 5)

Al merge story con `cap_change_type ∈ {new, extend}`, `/pm-{brand}` MUST verificar adicionalmente (sobre § 5):

| cap_change_type | scenarios[] | access | business_rules |
|---|---|---|---|
| `new` + `user_visible: true` | `>= 1` REQUIRED (cement 2026-Q3) | REQUIRED (cement 2026-Q3) | OPTIONAL (advisory hasta 2026-Q4) |
| `new` + `user_visible: false` | OPTIONAL | OPTIONAL | OPTIONAL |
| `extend` + cap target tiene scenarios | append nuevos opcional | si nueva entry_point → REQUIRED | si nueva business rule → REQUIRED |
| `fix` | NO requiere cambio | NO requiere cambio | NO requiere cambio |
| `derive` | hijo hereda + customiza scenarios | hijo declara su access | hijo hereda + override |

**Enforce point:** `scripts/validate_code_cap_bidirectional.py` (cement 2026-05-28) detecta drift:
- HARD pre-push si scenarios[].e2e_test path declarado no existe
- HARD pre-push si access.entry_points[].requires_role contradice runtime decorators
- Advisory pre-commit wip si caps user_visible carecen de bloques v3.2 obligatorios (cement 2026-Q3)

---

## Sección 12 · Header convention código (P3 ratificada · cement 2026-05-28)

Cada archivo de código (`.py`, `.ts`, `.tsx`) declara su capability owner via header de 2 líneas en posición 1.

### Formato canónico

**Python (`*.py`):**
```python
# cap: scheduling.valeria-agenda
# story-origin: vitalia-fase2-valeria-agenda
"""(docstring de la función/clase normal)"""
```

**TS/TSX (`*.ts`, `*.tsx`):**
```tsx
// cap: scheduling.valeria-agenda
// story-origin: vitalia-fase2-valeria-agenda
'use client';

export function AgendaWeekly() { ... }
```

**Multi-cap (archivo aporta a 2+ caps):**
```python
# cap: [shell-organism.shell-vitalia, scheduling.valeria-agenda]
# story-origin: [vitalia-fase1-routing-shell, vitalia-fase2-valeria-agenda]
```

### Special markers

| Marker | Significado | Cuándo usar |
|---|---|---|
| `__orphan__` | Archivo sin cap owner principal (candidato refactor) | Cross-module utilities sin claro home |
| `__shared__` | Cross-cap consumer multi-feature | Shadcn UI primitives, format helpers, hooks compartidos |
| `__skip__` | Intencionalmente sin cap (testing infra, fixtures) | `test-setup.ts`, `test-utils/`, fixtures |

### Reglas obligatorias

| Campo | Required | Constraint |
|---|---|---|
| `cap:` | YES | string `<module>.<slug>` OR array OR special marker · debe existir en `{brand}/docs/product/capabilities/{module}/{slug}.yaml` |
| `story-origin:` | YES | story-id del primer commit que tocó este archivo dentro del cap · trazabilidad |

**Position rules:**
- BE Python: header ANTES de docstring del módulo (líneas 1-5). Si shebang `#!/usr/bin/env python3`, header DESPUÉS.
- FE TS/TSX: header ANTES de `'use client'`. Si JSDoc preexistente, header después de JSDoc.
- Idempotente: re-aplicar NO duplica headers (validator detecta header existente).

### Regex parseable (validators usan estos exactos)

```regex
# Python
^\s*#\s*cap:\s*(\[.+?\]|\S+)
^\s*#\s*story-origin:\s*(\[.+?\]|\S+)

# TS/TSX
^\s*//\s*cap:\s*(\[.+?\]|\S+)
^\s*//\s*story-origin:\s*(\[.+?\]|\S+)
```

### Excepciones (NO requieren header)

- `vitalia/backend/alembic/` (migrations infra)
- Test files (`*.test.ts`, `*.spec.ts`, `__tests__/`) — heredan cap del file que testean
- `_pycache_/` (bytecode)

### Tooling

- `scripts/generate_code_to_cap_index.py` (cement 2026-05-28) — grep headers + produce `{brand}/docs/product/capabilities/_code-index.json` (gitignored R3 v2)
- `scripts/git-hooks/pre-commit` § Section 5c — advisory regen al stage code files
- `scripts/validate_code_cap_bidirectional.py` (cement 2026-05-28) — cross-check entre scenarios e2e_test + access roles ↔ decorators runtime

---

## Sección 13 · Bidirectional validator cross-checks (cement 2026-05-28)

`scripts/validate_code_cap_bidirectional.py` ejecuta 2 cross-checks que detectan drift entre code headers + cap YAML + runtime enforcement. (Los cross_check_1 y cross_check_2 atomics↔headers fueron eliminados con atomics — ver `docs/process/lifecycle.md`.)

### Cross-check 3 — Scenarios e2e_test path existence

Para cada `cap.scenarios[*].e2e_test` declarado:
- El path MUST existir en filesystem
- El archivo MUST contener `test(` o `test.describe(` (Playwright pattern)
- Si missing → HARD pre-push block

### Cross-check 4 — Access roles ↔ runtime decorators (P4 ratificada)

Para cada `cap.access.entry_points[*].requires_role: [...]`:
- Si `entry_type: ui` → buscar Next.js route en `vitalia/frontend/src/app/...{path}/page.tsx` + verificar middleware Clerk + tenant context
- Si `entry_type: api` → buscar FastAPI endpoint en `vitalia/backend/src/modules/vitalia/{module}/api/` + verificar `@require_phi_access(roles=[...])` decorator
- Roles declarados en cap MUST coincidir con roles en decorator (cross-check sets equal)
- Drift → **HARD para vitalia** (es salud · el control de acceso a PHI no puede ser advisory). Otras brands: advisory.

### Output

`{brand}/docs/product/capabilities/_bidirectional-validation.json` (gitignored R3 v2):
```json
{
  "validated_at": "2026-05-28T...",
  "brand": "vitalia",
  "cross_check_3": { "total": 0, "pass": 0, "drift": 0, "details": [] },
  "cross_check_4": { "total": 0, "pass": 0, "drift": 0, "details": [] },
  "summary": { "drift_total": 0, "verdict": "PASS" }
}
```

### Enforcement

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | Pre-commit Section 5d advisory wip | cement 2026-05-28 |
| 2 | Pre-push HARD block en main/release/* si cross_check_3 drift > 0 | cement 2026-05-28 |
| 3 | Pre-push HARD block (vitalia) si cross_check_4 drift > 0 (access roles ↔ runtime decorators) | cement 2026-05-28 |
| 4 | Cockpit DriftView lee `_bidirectional-validation.json` + muestra drift visualmente | Fase C |

---

## Sección 14 · Niveles de lectura N0-N4 (cap-levels · ratificado Chris 2026-06-06)

Un cap se LEE en **5 altitudes** (Diátaxis-altitud + caso-de-uso-RUP). **No es dato nuevo:**
cada nivel se PROYECTA de los bloques que el schema ya tiene (Sec 2 + Sec 11). El cockpit
cap-drawer (`CapLevel`) los muestra colapsables; los gates aseguran que no queden viejos.

| Nivel | Pregunta humana | Sale de (campo existente) | Gate de frescura |
|---|---|---|---|
| **N0 · Qué es** | "¿qué tengo, en una frase?" | `user_facing_name` + `user_facing_description` | **G8** (live+visible ⇒ description) |
| **N1 · Qué puedo hacer** | "¿qué casos de uso resuelve?" | `scenarios[]` (actor + given/when/then + edge_cases) | **G9** (live+visible ⇒ ≥1 scenario) + `cross_check_3` (e2e existe) + **mutation_gate `--cap`** (accuracy de código) |
| **N2 · Bajo qué reglas** | "¿qué reglas aplica y dónde?" | `business_rules[]` (rule + enforcement + `code_ref`) | badge 🔴 si `code_ref` ausente (regla de papel) |
| **N3 · Quién y por dónde** | "¿quién entra, en qué ruta?" | `access.entry_points` (path + roles) | `cross_check_4` (role ↔ decorator) |
| **N4 · Dónde vive / conecta** | "¿qué código, qué deps?" | `dev_preview` + `related_capabilities` + headers `# cap:` | `cap_doctor` G1-G7 + `BidirectionalSection` |

**Badge de verdad por caso de uso (N1):** el cockpit deriva el estado de verificación del DATO REAL
(no de un campo decorativo) — ✅ `verified_real` presente (evidencia de live-verify · DoD #37) ·
🟠 `e2e_test` declarado sin `verified_real` · ⚪ ninguno → deuda. Lógica pura: `lib/cap-badges.ts`.

**`verified_real`** (HB-58) está CABLEADO (opción a): lo leen el badge N1 + `cap_doctor --accuracy`
(mide la deuda de scenarios live sin evidencia → carril L4 del CIL). Se setea SOLO cuando la
live-verify de ese scenario quedó registrada (`{at, how}` derivado de `dod_evidence`/`dev_app_verified`).

**DoD (parte de la Definition of Done de toda story user-visible · rule #37):** la cap entrega
**N0-N4 completos** — N0 descripción (G8) · N1 ≥1 scenario que ejerza cada `business_rule` (G9 +
gherkin-matrix Phase D) · N2 reglas con `enforcement`/`code_ref` · N3 `access` si user-reachable ·
N4 `dev_preview` + código cableado. El auditor Phase D lo verifica explícito (no es favor de sesión).

SSoT vivo de la propuesta + fases F0-F3: `docs/process/cockpit-capability-levels-proposal.md`.

---

## Sección 15 · Referencias

- `docs/process/lifecycle.md` — SSoT del modelo 4-ejes (Release → Story → Capability → Scenario) · atomics/outcome/phase muertos
- `vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md` — ADR brand-local que cementa Sec 7-9 v3
- `docs/process/release-protocol.md` — entity Release agrupa stories que tocan caps
- `docs/process/chris-input-protocol.md` — chris-input.md donde Chris ratifica `cap_change_type`
- `docs/process/cockpit-permissions.md` — qué fields del cap son read-only desde cockpit
- `.claude/rules/anti-duplication-refining.md` — prior-art scan detect cap existente antes `cap_change_type: new` · favoreciendo `extend` over `new`
- `.claude/rules/story-closure-gate.md` § Fase F.3 — capability ledger update step
- `.claude/rules/brand-docs-schema.md` — schema canónico `{brand}/docs/product/capabilities/`
- `scripts/migrate_capability_ledger.py` — migration script
- `scripts/reconcile_capabilities.py --validate-ledger` — validation
- `scripts/generate_capability_index.py` — auto-gen `docs/portfolio/{brand}-capabilities.md` user-facing
- `tools/luana-cockpit/lib/cap-ledger.ts` — implementación 4 ramas (new/fix/extend/derive)
- `tools/luana-cockpit/components/map/MapView.tsx` — UI consumer del cap YAML (lee `agent_owner` + `functional_area` + `user_visible`)
- `vitalia/docs/product/areas/` — 7 markdowns user-facing (1 por agent_owner)
- `vitalia/docs/product/modules/` — markdowns técnicos paralelos (DDD paths para devs)
- `scripts/generate_code_to_cap_index.py` (cement 2026-05-28) — code↔cap index R3 v2
- `scripts/validate_code_cap_bidirectional.py` (cement 2026-05-28) — bidirectional validator 2 cross-checks (scenario e2e_test + access roles)
- `scripts/git-hooks/pre-commit` § Section 5c (regen advisory) + 5d (bidirectional advisory) — wip gates
- `_research-notes.md` + `_fase-decisions.md` (temporales · eliminados al cerrar Fase C 2026-05-28)
