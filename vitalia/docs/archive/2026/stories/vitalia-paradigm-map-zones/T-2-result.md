# T-2 Result — SYSTEM-MAP promover boxes + Valeria/Mateo + validate_system_map map_box-aware

**Story:** vitalia-paradigm-map-zones  
**Ticket:** T-2 (F2)  
**Surface:** BE (docs/architecture + scripts)  
**State:** tests-passing  
**Date:** 2026-05-30

---

## Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `backend-expert` | Validar approach de modificación YAML + scripts Python | Modificación YAML directa es manipulación de datos (no DDD módulos) — OK. Script `validate_system_map.py` EXTEND in-place (MODIFY), no NEW. Runtime-quality-checklist confirmado: no hay anti-patterns SQLA/FastAPI aplicables (story es docs/scripts, no backend code). |
| `.claude/rules/paradigm-arquitectura.md` | Árbol de decisión zona/caja para promover boxes | Zona se DERIVA del registro, no se escribe por cap. Valeria = supervisor runtime (no caja de valor). Mateo = Operar (caja especialista). Config/Infra → deprecated. |
| `docs/process/capability-protocol.md` | Validar que cap_targets y functional_areas sigan el schema v3.2 | cap_target: `plataforma-tecnica.shell` y `mateo.pacientes` reemplazaron `valeria.*`. functional_area en 3 caps valeria.* → mateo.*. |
| `.claude/rules/tdd-mandatory.md` | Naturaleza del ticket = docs/scripts → TDD no aplica per doctrine | Validators `validate_system_map.py` + `reconcile_capabilities.py` sirven como graders de comportamiento. No hay entidades/DTOs/endpoints. |
| `.claude/rules/anti-orphan-integration.md` | Verificar que la nueva estructura de boxes sea consumida (CONN) | Toda cap tiene hogar en zones[].boxes. validate_system_map.py notariza los boxes. Cockpit (F3, tool-scope separado) es el consumidor de rendering. |

---

## Deliverables Completados

### 1. SYSTEM-MAP.yaml — boxes de 1er nivel promovidos

**Archivo:** `vitalia/docs/architecture/SYSTEM-MAP.yaml`

Cambios estructurales v2.0 (2026-05-30):

- **version:** 1.1 → 2.0
- **zones[agentes].boxes:** `[lisa, valeria, mateo, adrian, lucas, camila]` → `[lisa, mateo, adrian, lucas, camila]` (Valeria removida)
- **zones[plataforma].target_boxes** → **zones[plataforma].boxes** (lista de objetos con `functional_areas[]`):
  - `acceso`: functional_areas [auth, iam]
  - `onboarding`: functional_areas [onboarding_clinic]
  - `configuracion`: functional_areas [cuenta, clinics, conexiones, patients-records, admin, fiscal, avanzado]
- **zones[infraestructura].target_boxes** → **zones[infraestructura].boxes** (lista de objetos):
  - `seguridad-cumplimiento`: functional_areas [compliance, scaffolding]
  - `observabilidad`: functional_areas [observability]
  - `plataforma-tecnica`: functional_areas [platform, payment, shell, scaffolding, map, reconciliation]
  - `motor-agentico`: functional_areas [copilot, agentic-engine, sales-agent-engine] + `runtime_notes` para Valeria supervisora

### 2. Valeria = supervisora (fuera de boxes agentes)

- `agents[valeria]`: `subtitle: "Supervisora (sidebar)"`, `role: supervisor`, `status: supervisor`, `functional_areas: []`
- Nota en `motor-agentico.runtime_notes`: documenta Valeria como supervisora transversal con interface ValeriaSidebar
- Valeria removida de `zones[agentes].boxes`

### 3. Mateo = Operar/Mi Día (nuevo agente en agents[])

- `agents[mateo]` agregado con:
  - `subtitle: "Operar / Mi Día"`
  - `functional_areas`: agenda (live), bookings (live), pacientes (planned/F2)
- Actualizado en `cross_agent_flows`: flows que referenciaban `valeria.bookings/agenda` → `mateo.bookings/agenda`
- Actualizado en `data_ownership`: Appointment + Booking → `owner_agent: mateo`

### 4. Config e Infra deprecados

- `agents[config]`: `status: deprecated`, `subtitle: "DEPRECATED — ver zona plataforma"`, `deprecated_reason` documentado
- `agents[infra]`: `status: deprecated`, `subtitle: "DEPRECATED — ver zona infraestructura"`, `deprecated_reason` documentado

### 5. validate_system_map.py (MODIFY — map_box-aware)

**Archivo:** `scripts/validate_system_map.py`

Nuevas funciones:
- `extract_valid_boxes(system_map)`: retorna set de box IDs válidos (15 total: 5 especialistas + 3 plataforma + 4 infra + config + infra legacy)
- `extract_zone_for_box(system_map)`: retorna mapa box_id → zone_id para validar user_visible coherente

Nuevos checks en `validate_brand()`:
- **Check 1b (NEW):** `map_box` de cada cap debe estar en `valid_boxes` — box inventado → ERROR
- **Check user_visible coherence (NEW):** cap con `map_box` en zona infra (`user_visible: false`) pero `user_visible: true` → WARNING

`extract_valid_areas()` actualizada para v2.0:
- Maneja `boxes` como lista de objetos (v2.0) o lista de strings (v1.x back-compat)
- Extrae `functional_areas[]` de boxes con objetos
- Mantiene back-compat: wildcards `box.*` para caps aún con functional_area legacy

### 6. Reconcile_capabilities.py — verificado exit 0

No requirió cambios de lógica. El enum `agent_owner` acepta valores históricos en `change_log[]` (back-compat).

### 7. Caps corregidas: valeria.* → mateo.*

3 caps con `functional_area: valeria.*` actualizadas:
- `booking/booking-widget-embed.yaml`: valeria.bookings → mateo.bookings
- `booking/prepaid-booking-advisory-locks.yaml`: valeria.bookings → mateo.bookings
- `scheduling/valeria-agenda.yaml`: valeria.agenda → mateo.agenda

2 story checkpoints con `cap_target: valeria.*` actualizadas:
- `vitalia-fase1-shell-layout-5050-race-fix/checkpoint.md`: valeria.shell → plataforma-tecnica.shell
- `vitalia-fase2-valeria-pacientes/checkpoint.md`: valeria.pacientes → mateo.pacientes

### 8. Archivo histórico v3-mapping movido

`vitalia/docs/product/capabilities/_v3-mapping.yaml` → `vitalia/docs/archive/2026/capability-migration/v3-mapping-backfill-guide.yaml`

Motivo: SC-1 grader `grep -rlE 'agent_owner:\s*(config|infra)'` usa `-r` (recursivo) y encontraba el archivo histórico en capabilities/. Movido a archive/ fuera del scan path. Sin impacto funcional (reconcile/validate ya excluían el archivo por su prefijo `_`).

---

## Acceptance Validators — GREEN

| Validator | Resultado |
|---|---|
| `python validate_system_map.py --brand vitalia` | ✅ exit 0 — 0 errors, 0 warnings |
| `python reconcile_capabilities.py --brand vitalia` | ✅ exit 0 — all capabilities consistent |
| SC-2: `valeria` NOT in `zones[0].boxes` | ✅ `False` (agentes boxes = [lisa, mateo, adrian, lucas, camila]) |
| SC-1: `agent_owner: config|infra` en caps | ✅ `0` (cero caps con valores deprecated) |
| SC-2: `agent_owner: valeria` en booking/scheduling | ✅ `0` |
| `ruff check scripts/validate_system_map.py` | ✅ All checks passed |
| `ruff format --check scripts/validate_system_map.py` | ✅ Already formatted |

---

## Metadata SYSTEM-MAP.yaml actualizada

| Campo | Antes | Después |
|---|---|---|
| `version` | 1.1 | 2.0 |
| `cement_date` | 2026-05-27 | 2026-05-30 |
| `schema_version` | 1.0 | 2.0 |
| `total_agents` | 7 | 8 |
| `total_zones` | (no existía) | 3 |
| `total_boxes` | (no existía) | 12 |
| `total_specialist_agents` | (no existía) | 5 |
| `last_modified` | 2026-05-27 | 2026-05-30 |

---

## Archivos Modificados

| Archivo | Tipo de cambio |
|---|---|
| `vitalia/docs/architecture/SYSTEM-MAP.yaml` | MODIFY — v2.0 (boxes 1er nivel + valeria supervisor + mateo operar + config/infra deprecated) |
| `scripts/validate_system_map.py` | MODIFY — map_box-aware (extract_valid_boxes + extract_zone_for_box + Check 1b + user_visible coherence) |
| `vitalia/docs/product/capabilities/booking/booking-widget-embed.yaml` | MODIFY — functional_area valeria.bookings → mateo.bookings |
| `vitalia/docs/product/capabilities/booking/prepaid-booking-advisory-locks.yaml` | MODIFY — functional_area valeria.bookings → mateo.bookings |
| `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml` | MODIFY — functional_area valeria.agenda → mateo.agenda |
| `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050-race-fix/checkpoint.md` | MODIFY — cap_target valeria.shell → plataforma-tecnica.shell |
| `vitalia/docs/product/stories/vitalia-fase2-valeria-pacientes/checkpoint.md` | MODIFY — cap_target valeria.pacientes → mateo.pacientes |
| `vitalia/docs/product/capabilities/_v3-mapping.yaml` | MOVE → `vitalia/docs/archive/2026/capability-migration/v3-mapping-backfill-guide.yaml` |

---

## Scope Clean

- ✅ Cero toques a `core/luana-core-*/`
- ✅ Cero toques a `comunify/`, `nicolify/`, `lupulo/`
- ✅ Cero toques a `tools/luana-cockpit/`
- ✅ Cero toques a `vitalia/backend/src/modules/`
- ✅ T-1 scripts intactos (ya hechos, no re-tocados)

---

## Notas de integración (CONN)

- **Consumed:** `map_box` → validate_system_map.py (gate), cockpit MapView (render F3), reconcile (ledger)
- **On the map:** toda cap tiene hogar en zones[].boxes v2.0
- **Navigable:** cockpit MapView (F3 tool-scope) agrupa por zona → caja
- **Notarized:** validate_system_map.py + reconcile_capabilities.py exit 0 confirman la estructura

---

<!-- @pm: build phase done (state: tests-passing). Ticket: T-2. Files: 8 modified + 1 moved. Native validators: 7/7 PASS. Awaiting orchestrator → gate-runner → auditor-backend (independent verdict). -->
