<!-- voseo-allowed: internal architecture decision record, not user-facing -->

# ADR-vitalia-005 — Capability Model · 5 dimensiones + dev_preview + MapView por zona

| Campo | Valor |
|---|---|
| **Status** | Accepted (v2.0 — 2026-05-30 taxonomía 3 zonas / 12 cajas) |
| **Date** | 2026-05-27 (v1.0) · **2026-05-30 (v2.0)** |
| **Authors** | Chris + `/pm-vitalia` (orchestrator Opus 4.7) |
| **Brand** | vitalia (modelo aplicable a otras brands vía promotion gate `/pm-luana`) |
| **Scope** | Schema `vitalia/docs/product/capabilities/{tech_module}/{slug}.yaml` + cockpit MapView + zonas 3-niveles |
| **Supersedes** | ADR-vitalia-005 v1.0 (campos `agent_owner: config/infra` → deprecados; `areas/` → reemplazado por zonas derivadas de SYSTEM-MAP) |
| **Sources** | v1.0: Sesión `/pm-vitalia` 2026-05-27 (Chris ratificó modelo 4 dimensiones + merge shell-organism + areas/). v2.0: Story `vitalia-paradigm-map-zones` 2026-05-30 (taxonomía 3 zonas · 12 cajas · Valeria=supervisora · Mateo=Operar) |
| **Changelog** | v1.0 (2026-05-27): cementación inicial · 4 dimensiones + dev_preview + areas/ + merge shell-organism 7 caps → 1 cap atomics. **v2.0 (2026-05-30): 5ª dimensión `map_box` (derivada de SYSTEM-MAP) · enum 12 cajas · config/infra deprecados · Valeria=supervisora/Mateo=Operar · MapView por zona + 2 lentes · `areas/` redefinido como derivado-por-zona.** |

---

## § 1 — Context

El modelo capability v2 (cement 2026-05-27) introdujo `cap_change_type ∈ {new, fix, extend, derive}` + `change_log[]` append-only + atomics objects con `added_in_story`. Eso resolvió la trazabilidad story↔cap (qué story creó/modificó qué cap).

Pero al inventariar el estado vitalia (55 caps en 30 directorios al 2026-05-27) emergen 5 problemas raíz que el modelo v2 no resuelve:

**P1 · 27 caps "huérfanas" en el cockpit.** `MapView.tsx:22-72` hardcodea 6 agentes con `modules: string[]` que cubre solo 6 módulos. Los demás 24 módulos caen en bucket "Otros módulos" (❓) sin pertenencia clara a ningún agente ni a infra explícita. Resultado: el mapa user-facing del producto está roto — Chris no puede contestar "¿qué tiene Vitalia?" leyendo el cockpit porque la mitad del producto está en el bucket "Otros".

**P2 · El campo `module:` mezcla 3 ejes distintos.** Hoy `module:` significa cosas diferentes según el cap:

- `scheduling`, `crm`, `brand_studio` → dominio técnico backend (DDD)
- `shell-organism`, `marketing` → área funcional UI (no DDD)
- `agentic`, `copilot`, `observability` → infra cross-cutting
- `tests`, `fixtures`, `ops`, `workers` → scaffolding no user-facing

Un solo campo cargando 3 conceptos colapsa la taxonomía.

**P3 · Stories crean cap 1:1 en vez de extender.** Aunque doctrina v2 cementa `extend`/`derive`/`fix`, la práctica muestra que la mayoría de stories nuevas marcan `cap_change_type: new` aunque exista cap relacionado. Resultado: granularidad excesiva. Caso emblemático: shell-organism con 7 caps (`empty-states`, `layout-5050`, `ribbon`, `routing`, `sub-tabs`, `valeria-chat`, `valeria-sidebar`) cuando todas son partes de **una sola capacidad humana**: "el shell visual de Vitalia post-login".

**P4 · Caps no tienen "user guide".** Ninguna cap declara cómo verla en development: qué ruta, qué componente, qué endpoint pegar, qué fixture cargar, qué test E2E la cubre. Resultado: para confirmar "¿esto existe en producción?" hay que leer múltiples archivos cross-codebase.

**P5 · `modules/{m}.md` desincronizado.** 23 module.md vs 30 dirs capabilities/. `tests/`, `fixtures/`, `ops/`, `workers/`, `audit/`, `clinics/`, `agentic/`, `admin/`, `auth/` tienen caps pero NO module.md. Drift silencioso del SSoT funcional.

**Decisión Chris (2026-05-27):** "los capabilities son capacidades de mi producto, si no tengo mapeado exactamente a qué modulo, funcionalidad exacta es, no tiene sentido. (...) debe ser entendible, casi en lenguaje humano. (...) cada capability debería tener el cómo verlo en development, como llegar a el, como una guía de usuario".

---

## § 2 — Decision

Cada YAML `vitalia/docs/product/capabilities/{tech_module}/{slug}.yaml` declara **4 dimensiones explícitas** + bloque `dev_preview` + naturaleza + visibilidad. El cockpit MapView agrupa por las dimensiones leídas del YAML (no por hardcoded mapping en TS). Se promueve una taxonomía paralela `areas/` user-facing (7 archivos · 1 por agente + Configurar + Infra) como SSoT del producto en lenguaje humano. Los `modules/{m}.md` técnicos se mantienen para devs.

### 2.1 · Las 5 dimensiones (v2.0)

```yaml
# Dim 1 — TÉCNICA (DDD backend · FSD frontend · path canónico)
tech_module: scheduling
# Path donde vive el código. Inmutable post-merge. Equivale al `module:` previo
# del schema v2, pero renombrado para evitar el cargo de 3 conceptos en uno.

# Dim 2 — CAJA DEL MAPA (★ v2.0 — reemplaza agent_owner enum plano)
map_box: mateo
# Enum cerrado de 12 cajas derivadas de SYSTEM-MAP.yaml zones:
#
# Zona agentes (user_visible:true · tier:core):
#   lisa · mateo · adrian · lucas · camila
#
# Zona plataforma (user_visible:true · tier:supporting):
#   acceso · onboarding · configuracion
#
# Zona infraestructura (user_visible:false · tier:enabling):
#   seguridad-cumplimiento · observabilidad · plataforma-tecnica · motor-agentico
#
# DEPRECADOS (mantienen back-compat hasta migración completa):
#   config → mapear a acceso|onboarding|configuracion|seguridad-cumplimiento
#   infra  → mapear a seguridad-cumplimiento|observabilidad|plataforma-tecnica|motor-agentico
#
# Nota: Valeria NO es una caja. Es supervisora transversal (runtime en motor-agentico,
# interface ValeriaSidebar). Sus caps de valor pasaron a mateo (agenda, bookings, pacientes).
# Mateo = caja de zona agentes (Operar/Mi Día: agenda + bookings + pacientes del día).

functional_area: mateo.agenda
# Sub-categoría DENTRO de la caja. Slug `<box>.<area>` (kebab).
# Ej: lisa.marca, mateo.agenda, mateo.bookings, adrian.embudo, lucas.atribucion,
# camila.reputacion, acceso.auth, configuracion.clinics, motor-agentico.copilot.
# La zona se DERIVA de map_box vía SYSTEM-MAP — nunca se escribe a mano.
# NO existe "huérfano" — todo cap declara functional_area. Si no se sabe →
# refining bloqueado hasta que Chris ratifique.

# Dim 3 — VISIBILIDAD (filtro del mapa)
user_visible: true
# true  → zona agentes o plataforma. Visible en mapa principal del cockpit.
# false → zona infraestructura. Visible solo con lente "Mostrar infra".
# Regla: user_visible se VALIDA contra la zona de map_box (validate_system_map.py).
#   agentes/plataforma → user_visible SHOULD be true
#   infraestructura    → user_visible SHOULD be false

# Dim 4 — NATURALEZA (qué tipo de pieza es)
nature: feature
# feature           → capacidad user-facing terminada
# scaffold          → estructura técnica (migration, test suite, fixture)
# extension-point   → cap que otras caps consumen (raro en brand · usual en core)

# Dim 5 — ZONA (★ v2.0 — derivada, no se escribe a mano)
# zone: agentes | plataforma | infraestructura
# Derivada de map_box vía SYSTEM-MAP.yaml. El cockpit la lee del YAML generado
# (scripts/validate_system_map.py enriquece el índice). NO poner en caps YAML
# (evita drift si se mueve una caja entre zonas).
```

### 2.2 · Bloque `dev_preview` (obligatorio si `user_visible: true`)

```yaml
user_facing_name: "Agenda semanal de Valeria"
user_facing_description: >
  La vista calendario con drag-to-reschedule donde Valeria muestra los turnos
  de la semana. El doctor arrastra un slot vacío para crear una reserva o
  arrastra un slot ocupado para reagendarlo.

dev_preview:
  route: "/valeria/agenda"
  how_to_navigate: "Login → ribbon clic en avatar Valeria → sub-tab Agenda"
  main_component: "vitalia/frontend/src/features/scheduling/components/AgendaWeekly.tsx"
  api_endpoints:
    - "GET /api/v1/scheduling/slots?week={iso}"
    - "POST /api/v1/scheduling/appointments"
  e2e_test: "vitalia/frontend/e2e/specs/valeria-agenda-create.spec.ts"
  fixtures_required: ["3-clinic-fixture-latam"]
  storybook_url: null  # opcional · link Storybook si existe
  loom_demo: null      # opcional · video Loom 30s si existe
```

Caps `user_visible: false` (infra) pueden omitir `dev_preview` o llenarlo parcial. Caps `nature: scaffold` siempre exentas.

### 2.3 · Taxonomía completa Vitalia v2.0 — 3 zonas · 12 cajas

**Zona Agentes** (tier:core · user_visible:true) — el valor user-facing que opera cada trabajador:

| Caja (map_box) | Emoji | Subtitle | Functional areas |
|---|---|---|---|
| `lisa` | 🏥 | Mi Clínica | `lisa.marca` · `lisa.servicios` · `lisa.doctores` · `lisa.compliance` · `lisa.landing-publica` |
| `mateo` | 📅 | Operar / Mi Día | `mateo.agenda` · `mateo.bookings` · `mateo.pacientes` |
| `adrian` | 💼 | Vender | `adrian.embudo` · `adrian.inbox` · `adrian.crm` · `adrian.reactivacion` · `adrian.outbound` · `adrian.propuestas` |
| `lucas` | 📣 | Marketing | `lucas.atribucion` · `lucas.bowtie` · `lucas.recomendaciones` · `lucas.referrals` |
| `camila` | 🌟 | Reputación + cohortes | `camila.reputacion` · `camila.reactivar` · `camila.multiplicar` · `camila.voz` |

> **Valeria** NO es caja de valor. Es supervisora transversal: runtime en `motor-agentico`, interface via `ValeriaSidebar` (sidebar del shell, siempre visible). Las caps de valor (agenda, bookings) pasaron a mateo en v2.0.

**Zona Plataforma** (tier:supporting · user_visible:true) — superficies que el usuario atraviesa, sin agente dueño:

| Caja (map_box) | Emoji | Subtitle | Functional areas |
|---|---|---|---|
| `acceso` | 🔑 | Acceso | `acceso.auth` · `acceso.iam` |
| `onboarding` | 🚀 | Onboarding | `onboarding.onboarding-clinic` |
| `configuracion` | ⚙ | Configuración | `configuracion.cuenta` · `configuracion.clinics` · `configuracion.conexiones` · `configuracion.patients-records` · `configuracion.admin` · `configuracion.fiscal` · `configuracion.avanzado` |

**Zona Infraestructura** (tier:enabling · user_visible:false) — no-funcional / técnico:

| Caja (map_box) | Emoji | Subtitle | Functional areas |
|---|---|---|---|
| `seguridad-cumplimiento` | 🔒 | Seguridad & Cumplimiento | `seguridad-cumplimiento.compliance` · `seguridad-cumplimiento.scaffolding` |
| `observabilidad` | 📡 | Observabilidad | `observabilidad.observability` |
| `plataforma-tecnica` | 🏗 | Plataforma técnica | `plataforma-tecnica.platform` · `plataforma-tecnica.payment` · `plataforma-tecnica.shell` · `plataforma-tecnica.scaffolding` · `plataforma-tecnica.map` · `plataforma-tecnica.reconciliation` |
| `motor-agentico` | 🤖 | Motor agéntico | `motor-agentico.copilot` · `motor-agentico.agentic-engine` · `motor-agentico.sales-agent-engine` |

> **Valeria runtime:** vive en `motor-agentico`. Su functional_area es implícita (runtime_notes en SYSTEM-MAP). NO posee caja de proceso propia.

**Deprecated (back-compat):**

| map_box (obsoleto) | Migrar a |
|---|---|
| `config` | `acceso` \| `onboarding` \| `configuracion` \| `seguridad-cumplimiento` (según la functional area) |
| `infra` | `seguridad-cumplimiento` \| `observabilidad` \| `plataforma-tecnica` \| `motor-agentico` (según la functional area) |

### 2.4 · Merge shell-organism (decisión Chris #3)

Las 7 caps actuales de `shell-organism/` (`empty-states`, `layout-5050`, `ribbon`, `routing`, `sub-tabs`, `valeria-chat`, `valeria-sidebar`) se mergean a **1 sola capability** `shell-organism/shell-vitalia.yaml`:

- `agent_owner: valeria` (Valeria es el host del shell)
- `functional_area: valeria.shell`
- `user_facing_name: "Shell visual de Vitalia post-login"`
- `nature: feature`
- `atomics:` 7 items (uno por slice F1-S4..S10) — `added_in_story` preserva trazabilidad
- `change_log:` 7 entries (una por slice) — `type: new` para S4, `type: extend` para S5..S10
- Las 7 caps actuales se mergean a archive: NO se borran sus YAML (preserva trazabilidad histórica), pero el cockpit solo lee el cap merged (campo `superseded_by: shell-vitalia` en los 7 originales)

Pattern análogo aplicable a otros casos de granularidad excesiva (e.g. compliance/* tres caps que probablemente son atomics de `config.compliance`).

### 2.5 · Areas/ (redefinido en v2.0 — derivado por zona)

En v1.0, `vitalia/docs/product/areas/` se planificó como SSoT user-facing (7 archivos manuales). En v2.0 este concepto se **reemplaza por zonas derivadas de SYSTEM-MAP**: el cockpit MapView agrupa caps por zona → caja → functional_area leyendo `map_box` del YAML. **`areas/` nunca se construyó (Fase D nunca ejecutada) — se descarta formalmente en v2.0.**

El SSoT user-facing del producto es ahora:

```
vitalia/docs/
├── architecture/SYSTEM-MAP.yaml  ← SSoT de 3 zonas · 12 cajas · functional_areas (semántico)
└── product/
    ├── capabilities/{module}/{slug}.yaml  ← YAML con map_box + functional_area (Dim 2 v2.0)
    ├── modules/{m}.md            ← técnico para devs (DDD paths) — mantener
    └── (sin areas/)              ← descartado · derivado por zona vía SYSTEM-MAP
```

El auto-gen de vistas user-facing por zona se produce en el cockpit (MapView lee SYSTEM-MAP + YAML caps) sin necesidad de archivos intermedios `areas/*.md`.

### 2.6 · Cockpit MapView por zona + 2 lentes (v2.0)

`tools/luana-cockpit/components/map/MapView.tsx` (dispatch plan tool-scope — ver T-dispatch):

1. Lee `SYSTEM-MAP.yaml` para obtener 3 zonas → 12 cajas → functional_areas (esqueleto del mapa).
2. Lee `cap.map_box` + `cap.functional_area` del YAML de cada cap. La zona se deriva de map_box vía registro SYSTEM-MAP.
3. Agrupa por zona → caja → functional_area → caps (3 niveles jerárquicos).
4. **Lente 1 (default): "Solo agentes + plataforma"** — filtra zona infraestructura (`user_visible:false`). Muestra el valor del producto.
5. **Lente 2: "Todo el mapa"** — incluye zona infraestructura con indicador visual `tier:enabling`. Toggle en la UI del cockpit.
6. **Valeria en el mapa:** aparece como nota en `motor-agentico` (supervisora transversal), NO como caja de valor. Su ValeriaSidebar es parte de `plataforma-tecnica.shell`.
7. **Mateo en el mapa:** caja de zona agentes con functional_areas `mateo.agenda`, `mateo.bookings`, `mateo.pacientes`.
8. Cap drawer (sin cambio de schema vs v1.0):
   - **Cómo verlo** → render `dev_preview` block
   - **Historial** → timeline `change_log[]`
9. **Cero bucket "Otros módulos"** — si un cap llega sin `map_box` declarado → warning visual rojo + sugiere refining flow.

> **Nota:** la implementación concreta del MapView refactor es tool-scope (Cockpit · `tools/luana-cockpit/`) y va en dispatch separado. Este ADR cementa el CONTRATO que esa implementación debe cumplir.

---

## § 3 — Consequences

### Positivas

- **Cero "huérfanos" en el cockpit.** Todo cap declara dueño explícito → mapa user-facing completo.
- **Lenguaje humano del producto.** `areas/{agent}.md` legible sin entender DDD ni paths.
- **Trazabilidad reversa.** Drawer Historial expone qué stories crearon/modificaron cada cap.
- **Onboarding nuevo dev.** "Cómo verlo" responde "dónde está esto en la app" en 1 click.
- **Anti-mirror.** Refining `extend` favorecido sobre `new` cuando functional_area ya existe.
- **Promotion candidate.** Modelo aplicable a otras brands (nicolify, comunify) si pasa el lift gate `/pm-luana`.

### Negativas / costos

- **Backfill 55 caps existentes** anotar 4 dimensiones + dev_preview. Sesión única autónoma (Fase B).
- **Refactor cockpit** MapView + drawer tabs. ~1-2 horas de subagent (Fase C).
- **Drift potencial** si stories nuevas olvidan declarar las 4 dimensiones. Mitigación: pre-commit hook valida que YAML cap nuevo tenga los 4 campos + `dev_preview` si `user_visible: true`.
- **Cross-brand divergence.** Si otras brands no adoptan el modelo, vitalia diverge. Mitigación: promotion proposal post-cement en vitalia.

### Migración (Fase A → F)

| Fase | Output | Owner | Estimado |
|---|---|---|---|
| A | ADR-vitalia-005 (este) + capability-protocol.md secciones 7-9 + template v3 | orchestrator | 30 min |
| B | 55 caps anotados con 4 dims + dev_preview | 3 subagentes paralelos | 30-45 min |
| C | Cockpit MapView + drawer refactor + typecheck pass | 1 subagente dedicado | 45-60 min |
| D | `areas/` 7 markdowns user-facing | orchestrator | 15 min |
| E | `scripts/generate_capability_index.py` + Makefile target | orchestrator | 30 min |
| F | Validate (lint + typecheck + cockpit smoke) + commit + push | orchestrator + haiku | 15 min |

Total: ~3 horas autónomo en una sesión.

---

## § 4 — Alternatives considered

### Alt 1 — Solo agregar `agent_owner` + `user_visible` (rechazada)

Más liviano (2 campos vs 4 + dev_preview). Pero no resuelve P2 (mezcla 3 conceptos en `module:`) ni P4 (user guide). Funcionalmente equivalente a hardcoded mapping movido al YAML — gana muy poco vs el costo de refactor.

### Alt 2 — Renombrar `modules/` → `areas/` borrando los técnicos (rechazada)

Más limpio en el árbol, pero rompe links cross-codebase de devs (los `modules/{m}.md` son linkeados desde 03-arch + audit reviews). Coexistencia paralela (modules técnicos + areas user-facing) tiene doble mantenimiento pero compatible.

### Alt 3 — Mantener taxonomía actual + solo arreglar hardcoded mapping (rechazada)

Hace 1 PR pequeño cockpit-only sin tocar YAML schema. Resuelve P1 mecánicamente. Pero deja P2, P3, P4, P5 sin resolver. Sería deuda técnica que vuelve la próxima ronda.

### Alt 4 — Modelo elegido (accepted)

4 dimensiones + dev_preview + areas/ paralela + merge shell-organism. Resuelve los 5 problemas raíz + entrega "lenguaje humano del producto" pedido por Chris.

---

## § 5 — Replication to other brands (promotion candidate)

Este ADR es brand-local vitalia. Si nicolify, comunify o futuras brands quieren adoptar el modelo:

1. `/pm-luana` evalúa promotion proposal post-Fase F cementada en vitalia
2. Si accepted → lift `docs/process/capability-protocol.md` secciones 7-9 + template a engine
3. Cada brand replica `areas/` con sus agentes propios (nicolify tiene agentes distintos: account_manager, project_lead, etc.)
4. Cockpit MapView ya quedaría brand-agnostic (lee del YAML, no hardcoded)

Promotion candidate flag: `promotable: candidate` en learnings post-cement vitalia (Fase F).

---

## § 6 — Anti-patterns

- ❌ Cap YAML nuevo sin `map_box` declarado (refining bloqueado · v2.0 reemplaza `agent_owner` como campo obligatorio)
- ❌ `map_box: valeria` (Valeria NO es caja de valor en v2.0 — era `agent_owner:valeria` en v1.0; migrar a `mateo` o `motor-agentico` según qué cap)
- ❌ `map_box: config` o `map_box: infra` en caps NUEVAS (deprecados — usar las 12 cajas nuevas)
- ❌ Cap `user_visible: true` sin `dev_preview` block (pre-commit hook bloquea)
- ❌ `functional_area` que no respete pattern `<box>.<slug-kebab>` (e.g. `mateo_agenda` con underscore en vez de kebab)
- ❌ `map_box: orphan` o `map_box: other` (taxonomía cerrada · 12 valores válidos en v2.0)
- ❌ Mover el bucket "Otros módulos" al cockpit sin resolver el YAML (Band-aid)
- ❌ Borrar `modules/{m}.md` técnicos (los devs los usan)
- ❌ Crear `areas/` archivos manuales (descartado en v2.0 — la vista user-facing es el cockpit MapView)
- ❌ Crear nueva cap `shell-organism/X` post-merge cuando `plataforma-tecnica.shell` ya cubre (debe ser extend del cap merged)
- ❌ Escribir `zone:` en el YAML de la cap (es derivado — lo calcula validate_system_map.py desde map_box)

---

## § 7 — References

- `docs/process/capability-protocol.md` (v2 cement 2026-05-27 · este ADR cementa Sección 7-9 v3)
- `docs/specs/templates/04-validators-template.yaml`
- `tools/luana-cockpit/components/map/MapView.tsx` (target refactor Fase C)
- `vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md` (gap detection origen)
- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` (patrón shell que mergea a `valeria.shell`)
- `.claude/rules/anti-duplication-refining.md` (favoreciendo `extend` over `new`)
- `.claude/skills/pm-vitalia/SKILL.md` § "Capability promotion (al merge)"

---

## § 8 — Status board

- ✅ v1.0 cemented 2026-05-27 — Chris ratificó 4 decisiones (modelo 4 dims · renombrar `modules→areas` paralelo · merge shell-organism · sesión autónoma)
- ✅ v2.0 cemented 2026-05-30 — Story `vitalia-paradigm-map-zones` ratificada Chris: 5ª dim map_box · 3 zonas · 12 cajas · config/infra deprecated · Valeria=supervisora · Mateo=Operar · MapView 2 lentes · areas/ descartado (Fase D)
- ✅ Fase B — backfill 70 caps (T-1 de story paradigm-map-zones)
- ✅ Fase A2/SYSTEM-MAP v2.0 — T-2 de story paradigm-map-zones
- ✅ Fase F5 (este ADR) — T-3 de story paradigm-map-zones
- ⏳ Fase C — cockpit refactor MapView por zona (tool-scope · dispatch separado)
- ~~Fase D~~ — areas/ descartado en v2.0 (reemplazado por derivado MapView)
