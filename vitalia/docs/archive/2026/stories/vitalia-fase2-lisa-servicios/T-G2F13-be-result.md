# T-G2F13-BE — Resultado: specialist DTO carries doctor name+specialty via roster port

**Ticket:** G2-F13-BE (bugfix BE, fix-loop G round 2)
**Story:** vitalia-fase2-lisa-servicios
**Estado:** tests-passing

## Problema

En "Especialistas habilitados" la FE recibía solo `{id, offer_id, doctor_id}` — sin nombre ni especialidad del doctor. El UUID aparecía en la UI en lugar del nombre visible.

## Causa raíz

`SpecialistLinkService.list_for_offer` devolvía `ServiceSpecialistLink` crudos (solo IDs). El `_detail_dto` los convertía con `SpecialistLinkDTO.model_validate(link)` que tampoco tenía campos de nombre. El `DoctorRosterPort` ya existía en el módulo (usado en `link` para validar), pero no se usaba en el path de lectura.

## Fix (BE-join, degradación grácil)

### 1. `SpecialistLinkDTO` (dtos.py)

Agregados dos campos opcionales:

```python
display_name: str | None = None
specialty: str | None = None
```

Backward-compatible: ambos son `None` por defecto cuando no hay enriquecimiento.

### 2. `EnrichedSpecialistLink` + `list_for_offer` (specialist_link_service.py)

Nuevo dataclass frozen `EnrichedSpecialistLink{id, offer_id, doctor_id, display_name, specialty}`.

`list_for_offer` acepta `clinic_id: UUID | None = None` (keyword-only). Cuando `clinic_id` está presente:
- Una llamada bulk `list_doctors(tenant_id, clinic_id)` construye el mapa `{doctor_id: RosterDoctor}`.
- Para doctores ausentes del bulk (e.g. inactivos), fallback `get_doctor(...)`.
- Si el doctor no se halla en ninguno de los dos → `display_name=None, specialty=None` (nunca rompe).

Cuando `clinic_id` es `None` → todos los campos son `None` sin llamar al roster.

### 3. `servicios_router.py`

- `get_service` agrega `clinic_id_header: str | None = Header(default=None, alias="X-Clinic-ID")`. OPCIONAL — el detail funciona igual sin él.
- UUID inválido → `clinic=None` (degradación grácil, no 422).
- `_detail_dto` acepta `clinic_id: UUID | None = None` y lo pasa a `list_for_offer`.
- `specialists=` se construye EXPLÍCITO (no `model_validate(link)`) con `display_name` y `specialty` desde el link enriquecido.

## Tests escritos (TDD — RED first)

### `test_specialist_link_service.py` (3 nuevos + 4 existentes = 7 total)

| Test | Descripción |
|---|---|
| `test_list_for_offer_enriches_name_and_specialty_when_clinic_id_given` | Con `clinic_id`: `display_name=full_name`, `specialty=specialty` |
| `test_list_for_offer_no_clinic_id_returns_nones` | Sin `clinic_id`: ambos `None`, sin crash |
| `test_list_for_offer_doctor_not_in_roster_graceful` | Doctor desaparecido del roster → `None`, sin crash |

### `test_servicios_router.py` (3 nuevos + 11 existentes = 14 total)

| Test | Descripción |
|---|---|
| `test_get_detail_with_clinic_id_carries_specialist_name` | `X-Clinic-ID` presente → `display_name` + `specialty` en respuesta; `clinic_id` forwarded al service |
| `test_get_detail_without_clinic_id_specialists_have_none_name` | Sin header → `null` en respuesta, `clinic_id=None` al service |
| `test_get_detail_invalid_clinic_id_degrades_gracefully` | UUID inválido → 200 OK, `clinic_id=None` al service |

## Gates

| Gate | Resultado |
|---|---|
| `ruff check src/modules/vitalia/offer/ tests/modules/vitalia/offer/` | PASS (0 errores) |
| `pytest tests/modules/vitalia/offer/` | 164/164 PASS |
| `pytest tests/architecture/` | 361/361 PASS |

## Archivos modificados

- `vitalia/backend/src/modules/vitalia/offer/application/services/specialist_link_service.py`
- `vitalia/backend/src/modules/vitalia/offer/api/dtos.py`
- `vitalia/backend/src/modules/vitalia/offer/api/servicios_router.py`
- `vitalia/backend/tests/modules/vitalia/offer/test_specialist_link_service.py`
- `vitalia/backend/tests/modules/vitalia/offer/test_servicios_router.py`

## Skills consultados

- `backend-expert` — anti-patterns FastAPI/SQLA/tests/migrations, runtime-quality-checklist
- `offer-expert` — contexto módulo offer (DoctorRosterPort boundary, no cross-module import directo)
- `brand-expert` — invocado (no aplica a este ticket BE puro; confirmado out-of-scope)
- `offer-type-preset-expert` — invocado (no aplica a este ticket BE puro; confirmado out-of-scope)
- `metrics-expert` — invocado (no aplica; confirmado out-of-scope)
