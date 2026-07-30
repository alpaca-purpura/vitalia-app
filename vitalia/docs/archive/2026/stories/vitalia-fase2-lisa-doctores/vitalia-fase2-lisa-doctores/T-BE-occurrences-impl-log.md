# T-BE-occurrences-endpoint — impl log

Ticket: D3-C BE availability-occurrences range endpoint (06-tickets.yaml).
Builder: builder-backend · Modelo: Fable 5 (mandato `model_mandate_2026_06_12`).
Brand: vitalia · Módulo: clinics · cap: `lisa.doctores` (header código: `# cap: clinics.lisa.doctores`, convención del módulo).

## R24 brief gate

`CONTEXT-BRIEF.md` tiene `Validator pass: _pending_` → NO consumido (R24 REFUSE del brief).
Lectura directa de artifacts per caller: 06-tickets.yaml (entry L411) + 03-arch-delta.md § 4.3 +
01-spec.md § D3-C/D3-C.1 + 04-validators.yaml V-D3C-1..8 + código fuente del módulo.

## Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `backend-expert` (+ `references/runtime-quality-checklist.md`) | Ticket BE FastAPI/DDD — siempre obligatorio | Patrón router existente reusado (deps `_get_db` + builder fn, NO type-alias Annotated con AsyncSession — anti-pattern checklist §1); query param `date` typed (no parsing manual datetime); test fixture TestClient con override `_get_db` sin params (checklist §2); SQLA no tocado (read endpoint sin queries nuevas — repo port existente) |
| FastAPI canonical patterns (SOP skill body) | endpoint nuevo | `response_model=` + `response_model_by_alias=True` (wire camelCase como AvailabilityBlockDTO — lección imagined-contract 2026-06-04); `Query(alias="from"/"to")` porque `from` es keyword Python; headers UUID-typed → 422 automático |
| pytest async testing patterns (SOP skill body) | batería SC-D3C-1..8 | asyncio_mode=auto (pyproject) · unit con AsyncMock repo (patrón `test_availability_blocks_api.py`) · TestClient app mínima con `monkeypatch` de `_build_block_service` para integration-through-router con servicio REAL + repo mock |
| `brand-expert` / `offer-expert` / `offer-type-preset-expert` / `metrics-expert` | NO invocadas operativamente | Ticket no toca brand_studio/offer/analytics — fuera de routing matrix Step 3. Cargadas por el caller pero sin decisión aplicable |
| graceful-degradation | Evaluado | NO aplica: cero llamadas externas (proyección pura in-process + repo port) |

Rules cargadas per ticket `must_load_rules`: hipaa-lite (dual filter tenant+clinic — delegado al repo
`AvailabilityBlockRepository`/CompoundScopeRepositoryBase ya existente; occurrences = scheduling metadata
no-PHI, sin audit write en read, igual que GET availability-blocks), tenant-isolation, tdd-mandatory,
hotfix-repro-mandatory (`repro_evidence.trace_evidence` presente en ticket — root cause FE confirmado),
master-data (UTC siempre; sin currency).

## § Plan (technical design — ANTES de código)

### Diseño por capa (inside-out)

**Domain:** sin cambios — `AvailabilityBlock` ya modela todo (kind/freq/end_condition/occurrences/created_at).

**Application:**
1. `recurrence_summary.py` (NEW) — `format_recurrence_summary(block) -> str`. SSoT humano del patrón
   (RN-D3F-1; D3-F lo extiende a days_of_week+interval). Pre-D3-F per arch § 4.3 verbatim:
   `"Único"` (one_off) · `"Semanal"` (weekly) · `"Quincenal"` (biweekly).
2. `availability_projection_service.py` (EXTEND, no reimplementar): nuevo método público
   `occurrence_dates_in_range(block, *, range_start, range_end, series_anchor=None) -> list[date]`
   + refactor interno `_recurrent_occurrence_dates()` extraído de `_project_recurrent` (cero duplicación
   rrule — jscpd). `_project_recurrent` conserva contrato idéntico (202 tests previos verdes).
3. `availability_block_service.py` (EXTEND): dataclass `BlockOccurrence` + método
   `list_occurrences(doctor_id, tenant_id, clinic_id, range_start, range_end)`:
   valida rango (to>=from, ≤62 días → `ValueError`) → `repo.list_blocks` (dual filter) →
   por bloque `occurrence_dates_in_range` → colapsa a 1 ocurrencia por (block, date) → ordena.

**API:**
4. `dtos.py`: `AvailabilityOccurrenceDTO {block_id, occurrence_date, start_time, end_time, kind, freq, pattern_summary}`
   (camelCase wire) + `AvailabilityOccurrencesResponse {occurrences}`.
5. `doctors_router.py`: `GET /{doctor_id}/availability-occurrences?from=&to=` —
   `response_model=AvailabilityOccurrencesResponse`, headers X-Tenant-ID + X-Clinic-ID + X-User-ID (UUID,
   consistencia useStaffActorHeaders per constraint del ticket), thin: valida DTO→service→map ValueError→422.

### ★ Decisión de anclaje (divergencia documentada vs sketch arch § 4.3)

El sketch dice `project_block(block, reference_date=from)`. Eso **reintroduce el bug server-side** para
`end_condition_kind=occurrences`: `rrule(count=N)` con `dtstart` derivado de `from` REINICIA la serie en
cada ventana consultada → N fechas en TODA ventana = pintado indefinido (exactamente lo que V-D3C-1
prohíbe: "EXACTAMENTE 2 fechas"). Lo mismo rompe la paridad quincenal (interval=2 ancla la paridad de
semana en dtstart — V-D3C-2 espaciado 14d).

**Decisión:** la serie se ancla en `series_anchor = block.created_at.date()` (== reference_date usado al
materializar en `create_block`, reproduce la serie original; estable ante edits → SC-D3C-5 conteo no se
reinicia). `open_ended` usa horizonte rodante `hoy+90d` (no `anchor+90d`: un bloque open_ended viejo debe
seguir pintando — "ni corta ni infinita", V-D3C-4; espeja la rematerialización rolling del docstring del
servicio). Los validators V-D3C-1..8 mandan sobre el one-liner del sketch (acceptance = validators).

### Batería de tests (RED first — `test_availability_occurrences.py`)

Naturaleza: BE endpoint nuevo + service read-projection + regression bugfix (matriz test-design-doctrine):

| SC | Test | Nivel |
|---|---|---|
| SC-D3C-1 ★REGRESSION | weekly occurrences=2 anclado lunes 2026-06-01 → EXACTAMENTE 2 fechas (Jun 1, Jun 8) en ventana amplia; ventana posterior (Jul) → **0** (guard pintado indefinido — el RED reproduce el off-by-week si la serie se reinicia por ventana) | service unit |
| SC-D3C-2 | biweekly occurrences=3 → 3 fechas espaciadas 14d (Jun 1/15/29); ventana en semana de paridad off → vacía | service unit |
| SC-D3C-3 | end_date EN lunes → incluido (3 fechas); end_date domingo previo → excluido (2) — inclusividad TZ | service unit |
| SC-D3C-4 | open_ended creado hace 100d → pinta HOY (ni corta) y nada > hoy+90d (ni infinita) | service unit |
| SC-D3C-5 | edit (mismo id+created_at, otra hora, updated_at posterior) → mismas 2 fechas, sin dup, conteo no reiniciado; doble listado idempotente | service unit |
| SC-D3C-6 | one_off + recurrente solapados mismo día → ambos (2 entries misma fecha, block_id distinto) | service unit |
| SC-D3C-7 | repo sin bloques activos (post-delete) → 0 ocurrencias; dual-filter kwargs asserted | service unit |
| SC-D3C-8 | medianoche UTC (00:00) → occurrence_date = día correcto sin shift; day_of_week=6 → domingo | service unit |
| Endpoint | response_model declarado (arch gate) · happy path HTTP con servicio REAL + repo AsyncMock → 200 camelCase `{occurrences:[{blockId, occurrenceDate, patternSummary,...}]}` · 422 rango>62d · 422 to<from · 422 X-User-ID ausente · 422 X-Tenant-ID malformado | TestClient |
| Formatter | `format_recurrence_summary`: Único/Semanal/Quincenal | unit |

Cross-tenant: dual filter delegado al repo (mock assert kwargs) — el repo real ya está cubierto por
`test_availability_block_mutable.py`/integration previos; endpoint no introduce query nueva.

### Integración (CONN — anti-orphan)

- **Registro:** sub-route del `doctors_router` ya montado en `main.py` vía `clinics/api/router.py`
  (prefix `/api/v1/vitalia/clinics/doctors`) — cero wiring nuevo necesario (verificar import chain).
- **Consumer:** `T-FE-occurrences-consume` (`useAvailabilityOccurrences` en `features/lisa/api/staff.ts`,
  depends_on este ticket) + `T-FE-vista-mes`. NO isla.
- **Hogar:** cap `lisa.doctores` (checkpoint `cap_target`), zona Agentes→Lisa, hoja Horarios.

### Prior-art (Step 0 grep)

`availability`/occurrences/rrule: solo `vitalia/.../clinics/` (este módulo) — `core/luana-core-commercial-calendar`
descartado por D-2 del 03-arch original (marketing calendar, cero RRULE); `scheduling/` consume slots, no
proyecta. `core/luana-core-*`: sin abstracción de recurrencia (grep `rrule|recurrence` en engine = solo
commercial-calendar event windows, no RRULE). EXTEND brand-local confirmado — sin mirror cross-brand
(nicolify/comunify/lupulo: grep `availability_projection` = 0).

## Bitácora

1. **RED** — `tests/modules/vitalia/clinics/test_availability_occurrences.py` escrito ANTES de tocar
   src/. Run: `pytest tests/modules/vitalia/clinics/test_availability_occurrences.py --maxfail=100`
   → **26/26 FAILED** (`AttributeError: 'AvailabilityBlockService' object has no attribute
   'list_occurrences'` + `ModuleNotFoundError recurrence_summary` + routes ausentes). RED limpio.
2. **GREEN inside-out** — application: `recurrence_summary.py` (new) → projection: refactor
   `_recurrent_occurrence_dates()` extraído (único builder rrule) + `occurrence_dates_in_range()` →
   service: `BlockOccurrence` + `list_occurrences()` (cap 62d) → api: DTOs + endpoint GET
   `availability-occurrences`. Batería → **26/26 PASSED**.
3. **Regression guard** — suite módulo entera: **322/322 PASSED** (296 previos intactos, incluye
   `test_availability_projection.py` 12/12 — el refactor del builder rrule no movió el contrato de
   `_project_recurrent`).
4. **Gates nativos** — `ruff check` clean (1 E501 en test corregido) · `ruff format --check` clean ·
   arch fitness: **340 passed / 1 failed** = `test_pgcrypto_phi_columns` (`treatment_plans.notes`
   TEXT→BYTEA, migración `005_vitalia_treatment_plans.py` committed pre-ticket; el test scannea SOLO
   `alembic/versions/` y mi diff toca 0 migrations → **pre-existente conocido**, deuda migración BYTEA
   registrada en MEMORY cierre 2026-06-01 — fuera de scope: ticket prohíbe migrations). mypy: binario
   no presente en `${WS}/.venv` (gate-runner tools-verify lo reportará).

## Cross-module reads

Ninguno — todo dentro de `clinics/` (+ `_shared/` audit repo ya importado por el servicio existente).
