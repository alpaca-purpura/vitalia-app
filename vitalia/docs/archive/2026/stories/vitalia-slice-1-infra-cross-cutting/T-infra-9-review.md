# T-infra-9 review — APPROVED

> Auditor: Claude Opus 4.7 (orchestrator-direct)
> Date: 2026-05-18
> Surface: BE IAM + CRM modules Slice 1 scaffold
> Commit SHA: 600f6c3

## Scope
**IAM module** (9 files): VitaliaRole enum (7 roles: doctor, nurse, admin_clinic, marketing, receptionist, patient, vendor) + PHI_ALLOWED_ROLES frozenset (3 roles) + ClerkJwtDecoder stub (format `stub:tenant:clinic:role:user_id`) + ClinicResolver + GET /api/v1/iam/me endpoint.

**CRM module** (14 files): Patient domain entity (PHI, dual filter) + Lead domain entity (non-PHI, single filter) + PatientRepository extends PhiRepositoryBase (dual filter + audit log sync write on every PHI read/write) + LeadRepository (NOT PhiRepositoryBase — Lead non-PHI per spec) + PatientService (@require_phi_access RBAC decorator en get_by_id / update / opt_out; opt_out restricted admin_clinic only) + LeadService (no RBAC — all roles) + 4 CRM endpoints (GET/PATCH patients, POST opt-out, GET leads). main.py mounted iam_router en /api/v1/iam + crm_router en /api/v1/crm.

TDD: 64 NEW tests across 8 files (8 IAM + 7 CRM repo + 6 CRM service + 7 CRM API + 24 role + dual-filter + 12 misc). Raw SQL text() decision Slice 1 (ORM models pending — tables from T-infra-1 ya pushed). AsyncMock repos en API layer (Slice 2 injection via FastAPI Depends).

## Categorías scoring (10 BE categories)
1. **DDD layering** — ✅ Inside-Out: domain (Patient, Lead pure entities) → infrastructure (PatientRepository, LeadRepository) → application (PatientService, LeadService) → API (4 endpoints thin). Verified diff
2. **Tenant isolation** — ✅ EVERY query filters tenant_id. LeadRepository: `.where(Lead.tenant_id == tenant_id)`. PatientRepository inherits PhiRepositoryBase enforcement
3. **HIPAA-lite dual filter** — ✅ PatientRepository extends PhiRepositoryBase. `.validate_dual_filter(tenant_id, clinic_id)` raises MissingClinicFilterError si falta clinic_id. Test `test_phi_dual_filter.py` cubre PatientRepository specifically
4. **HIPAA-lite audit log** — ✅ PatientRepository.get_by_id / update / opt_out invocan `audit_log_repo.write(AuditLogEntry(...))` SYNC antes response. Test verifica row creada con campos correctos (tenant_id, clinic_id, user_id, action, resource_type='patient', resource_id, timestamp)
5. **HIPAA-lite PII sanitization** — ✅ response_model PatientResponse + PatientPatchRequest aplican PII allowlist (masking automático cuando PiiMaskedSpan consume). Trace observability hooks (cuando agentic toca) usan sanitize_phi_payload via agent_spans
6. **HIPAA-lite RBAC** — ✅ @require_phi_access(roles=["doctor", "nurse", "admin_clinic"]) en PatientService.get_by_id/update. opt_out restringido `roles=["admin_clinic"]`. LeadService sin RBAC (Lead non-PHI). Test cubre 24 role-tests
7. **Migrations idempotentes** — N/A (consumer de T-infra-1) ✅
8. **Extension SDK contracts** — N/A (IAM/CRM no son Extension Points) ✅
9. **Anti-duplication / cross-brand mirror** — ✅ IAM module brand-specific (Clerk integration vitalia-aware). CRM Patient/Lead son medical-vertical concepts. Cross-brand grep `VitaliaRole` / `PatientRepository` / `LeadRepository` en otros brands = ZERO matches
10. **Engine boundary** — ✅ ZERO edits a core/luana-core-*/src/. Brand-internal IAM (ClerkJwtDecoder stub vitalia) + CRM (Patient/Lead). NO crm engine package (per arch decision Slice 1 medical-vertical specific)

## Findings count
- FAIL: 0
- WARN: 0
- INFO: ClerkJwtDecoder es STUB por design Slice 1 (per 03-arch-be.md). Real implementation pending ClerkAuth integration Slice 2 (future PR con `/po` sign-off + opt-in real Clerk). Acceptable boundary.
- INFO: AsyncMock repos en API layer — Slice 2 introduces FastAPI Depends injection (per 03-arch-be.md). Documented + acceptable for scaffold.

## Validators acceptance.validator_ids
- be_lint_ruff_check: PASS
- be_format_ruff: PASS
- be_arch_fitness_brand: PASS 216/216
- be_pytest_full: PASS 1125/1125 (54 SKIP Postgres-integration)

## Downstream regression
- Surface: vitalia/backend/src/modules/vitalia/{iam,crm}/ → consumido por sub-stories siguientes (onboarding-wizard usa GET /iam/me, inbox/pipeline/agenda/fidelizacion/marketing consumen Patient/Lead endpoints)
- Engine consumer: luana_core_extension_sdk (IAM uses for Clerk decoder placeholder)
- Cross-brand mirror: ZERO matches (medical-vertical specific)

## Self-fix log
N/A.

## Verdict
**APPROVED**. T-infra-9 establece IAM + CRM scaffold Slice 1 con architectural HIPAA-lite enforcement. Dual filter cardinal rule en PatientRepository. RBAC decorator en PatientService. Audit log sync write per PHI access. Lead non-PHI tratado correctamente (no PhiRepositoryBase). Engine boundary respetado.
