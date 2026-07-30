# T-2 IMPL-LOG — BE config-cuenta

**Ticket:** T-2 — BE config-cuenta: campos cuenta Clinic + fiscal/specialty validators + account_router + PATCH editable  
**Story:** vitalia-fase2-config-cuenta  
**Brand:** vitalia  
**cap_target:** configuracion.cuenta  
**cap_change_type:** new  
**Bucket:** code:clinics  
**alembic current (HB-37):** `038_vitalia` (head)  
**down_revision for migration 039:** `"038_vitalia"`

---

## § Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | YES — runtime-quality-checklist: FastAPI Annotated deps, response_model mandatory, tenant isolation on every query, SQLA 2.0 select(), Column() style matches existing models | Anti-patterns avoided: datetime.utcnow(), DateTime() without tz=True, hardcoded currency, session.query() |
| FastAPI canonical patterns | YES — async routes, response_model=, Header(alias="X-Tenant-ID"), redirect_slashes=False already confirmed | Applied throughout api layer |
| pytest async testing patterns | YES — httpx.AsyncClient, fixture scoping, factory fixtures, DB isolation markers | Applied in all test files |
| graceful-degradation | N/A — no external HTTP/LLM calls in this ticket | Skipped |
| brand-expert | N/A — touching clinics module, not brand/ module | Skipped per routing table |
| offer-expert | N/A | Skipped |
| metrics-expert | N/A | Skipped |

---

## § Plan

### Layers + Files to create/extend

**DOMAIN (pure Python)**
- EXTEND `vitalia/backend/src/modules/vitalia/clinics/domain/clinic.py` — add 7 nullable fields: legal_name, fiscal_id, address, phone, email, language, currency
- CREATE `vitalia/backend/src/modules/vitalia/clinics/domain/events.py` — ClinicSpecialtiesChanged event
- CREATE `vitalia/backend/src/modules/vitalia/_shared/validation/fiscal_id_validator.py` — country-specific fiscal ID validators (freetext degradation for unsupported)
- CREATE `vitalia/backend/src/modules/vitalia/_shared/catalogs/specialty_catalog.py` — SPECIALTY_CATALOG per country

**INFRASTRUCTURE**
- EXTEND `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/clinic_model.py` — 7 new Column() entries
- EXTEND `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/clinic_repository.py` — add get_active_for_tenant() + update_account()
- CREATE `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/clinic_config_repository.py` — read/write tenant.config_json["clinic_config"] JSONB
- CREATE `vitalia/backend/alembic/versions/039_vitalia_config_cuenta_fields.py` — idempotent raw SQL migration

**APPLICATION**
- CREATE `vitalia/backend/src/modules/vitalia/clinics/application/clinic_account_service.py` — RBAC + validators + audit + transaction

**API**
- EXTEND `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` — add 4 DTOs
- CREATE `vitalia/backend/src/modules/vitalia/clinics/api/account_router.py` — 4 routes
- EXTEND `vitalia/backend/src/main.py` — register account_router

**TESTS (RED first, then GREEN)**
1. `tests/modules/vitalia/clinics/test_fiscal_id_validator.py`
2. `tests/modules/vitalia/clinics/test_specialty_catalog.py`
3. `tests/modules/vitalia/clinics/test_clinic_account_repository.py`
4. `tests/modules/vitalia/clinics/test_clinic_account_service.py`
5. `tests/modules/vitalia/clinics/test_account_router.py`
6. EXTEND `tests/architecture/test_fe_be_contract_parity.py`

### Key Design Decisions

1. **Fiscal validator freetext degradation:** unsupported countries → freetext (no raise, no block). Only AR CUIT, PE RUC, MX RFC, CL NIT, CO NIT, UY RUT have format checks.
2. **Specialties JSONB:** read `tenant.config_json["clinic_config"]["primary_specialties"]` via TenantModel. Write via read-modify-write in same transaction as clinic fields.
3. **Transaction boundary:** clinic fields (clinic_model) + config_json specialties (tenant_model) in same AsyncSession commit.
4. **Audit log:** SYNC pre-response (await audit_writer.write) for PATCH — NOT fire-and-forget.
5. **RBAC:** `admin_clinic` role required for PATCH. GET is read-only (any authenticated user).
6. **ClinicRepository extension:** `get_active_for_tenant()` returns first active clinic for tenant (N3-static: single clinic per tenant in MVP). `update_account()` uses SQLA update() statement with returning().
7. **Migration:** down_revision = "038_vitalia", raw SQL ALTER TABLE ADD COLUMN IF NOT EXISTS × 7.
8. **Domain event:** ClinicSpecialtiesChanged emitted best-effort (try/except on dispatch).

### Integration (CONN)
- **Consumed by:** FE `features/config/cuenta/api/use-account.ts` (GET + PATCH) + `features/config/cuenta/api/specialty-catalog.ts` (GET catalog)
- **On-map:** `vitalia/docs/product/capabilities/configuracion/cuenta.yaml`
- **Navigable:** `/api/v1/clinics/account/` prefix — distinct from existing `/api/v1/vitalia/clinics` CRUD
- **Notarized:** `app.include_router(account_router, prefix="/api/v1/clinics/account", tags=["account"])`

### First entry: RED test (TDD order proof)
See `test_fiscal_id_validator.py` written BEFORE `fiscal_id_validator.py` exists.

---

## § Default-flip pre-audit
No default flags touched in this ticket. Skipped.

---

## § Cross-module reads
- READ `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — signature confirmed
- READ `vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py` — require_brand_owner_access pattern confirmed
- READ `vitalia/backend/src/modules/vitalia/brand_studio/application/services/marca_service.py` — TenantModel.config_json pattern confirmed
- READ `core/luana-core-iam/...` — TenantModel import path confirmed via marca_service
