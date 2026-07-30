# T-BE-L3 — Fix picker médico: nombre real en lugar de placeholder Dr.{uuid8}

## Root cause

`AvailabilityQueryRepository.list_active_doctors` ejecutaba:

```python
select(VitaliaAvailabilitySlotModel.doctor_id).distinct()
```

…y producía el label con un string sintético:

```python
return [(row.doctor_id, f"Dr. {str(row.doctor_id)[:8]}") for row in rows]
```

No había JOIN a `vitalia_doctors`, por lo que el nombre real nunca se
resolvía. El resultado llegaba crudo al picker del FE como "Dr. 2b0d9466".

## Diff — qué cambió

**Archivo modificado:**
`vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/availability_query_repository.py`

- Se reemplazó el `select(... .distinct())` ORM por raw SQL con LEFT JOIN a
  `vitalia_doctors` (mismo patrón que `AgendaGridRepositoryImpl._GRID_PROJECTION`
  líneas 83-84).
- Label: `COALESCE(NULLIF(TRIM(CONCAT(first_name, ' ', last_name)), ''), 'Sin asignar')`
- Dual filter aplicado en AMBAS tablas: `slot.tenant_id = :tenant_id` y
  `doc.tenant_id = :tenant_id` (HIPAA-lite dual filter).
- Se eliminó el comentario `# ponytail: label is a placeholder — router enriches...`
- Se actualizó el docstring del módulo y del método.
- Se agregó `from sqlalchemy import bindparam` (necesario para el raw SQL).

**Archivo nuevo (tests):**
`vitalia/backend/tests/modules/vitalia/scheduling/test_list_active_doctors_real_name.py`

5 tests de integración reales (HB-108: no mock — el bug vive en el SQL JOIN):

| Test | Qué verifica |
|---|---|
| `test_returns_real_first_and_last_name` | Nombre real "María González" en vez de placeholder |
| `test_doctor_without_name_returns_sin_asignar` | doctor_id huérfano (sin row en vitalia_doctors) → "Sin asignar" |
| `test_cross_tenant_isolation_not_visible` | Dual filter L1: TENANT_B no visible desde TENANT_A |
| `test_cross_clinic_isolation_not_visible` | Dual filter L2: CLINIC_B no visible desde CLINIC_A |
| `test_deleted_slot_excluded` | Slot con deleted_at seteado no aparece |

## Gates

```
ruff check ... → All checks passed
ruff format --check ... → 2 files already formatted
pytest tests/modules/vitalia/scheduling/ → 272 passed
pytest tests/modules/vitalia/scheduling/test_list_active_doctors_real_name.py → 5 passed (integration, Postgres UP)
```

Failures pre-existentes NO relacionadas a este fix:
- `test_ep3_resolvers_wired` → missing `luana_core_sales_agent.application.orchestrator.inbound_mode_seam` (story canal-inbound en curso)
- `test_pgcrypto_phi_columns` → otro arc test pre-existente
- `test_ep3_handlers_sync_callable` → ídem

## Commit SHA

`e4d1f170` — pushed a `wip/vitalia`

## Nota live-verify

El doctor del dev-DB tendrá nombre real si fue creado a través del flujo
de staff (primer ingreso desde la UI de Lisa/doctores). Si el doctor fue
creado directamente por seed sin nombre, el picker mostrará "Sin asignar"
(comportamiento correcto según la nueva implementación). Para verificar
live: crear un médico con nombre desde la UI, abrir nueva cita y confirmar
que el picker muestra el nombre real.
