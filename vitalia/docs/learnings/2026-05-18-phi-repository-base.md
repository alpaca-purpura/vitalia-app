---
brand: vitalia
date: 2026-05-18
slug: phi-repository-base
promotable: yes
proposal_link: docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md
migrated_engine_path: core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py
migrated_at: 2026-05-20
migrated_engine_class: CompoundScopeRepositoryBase  # renamed brand-agnostic
applies_to_other_brands_potentially: [vitalia, fitflow, fixia, retailly, comunify, saasora]
target_core_package: core/luana-core-platform/repositories/
origin_story: vitalia-slice-1-infra-cross-cutting
origin_ticket: T-infra-3 (PHI compliance HIPAA-lite)
related_capabilities:
  - vitalia/docs/product/capabilities/compliance/hipaa-lite-defensive-stack.yaml
arch_test: vitalia/backend/tests/architecture/test_phi_dual_filter.py
---

# Dual-filter repository base class (`PhiRepositoryBase`) — patrón cross-brand candidate

**Qué aprendimos:** El patrón `PhiRepositoryBase` introducido por T-infra-3 enforza dos filtros simultáneos en TODA query de un repositorio sensible (en vitalia: `tenant_id` raíz + `clinic_id` HIPAA-lite). Es una abstracción genérica del concepto **"compound-scope multitenancy"**: cuando una brand necesita aislar datos por una sub-jerarquía dentro del tenant (clinic, oficina regional, store_id, gym_id, etc.), `tenant_id` solo no alcanza. El patrón usa un ABC con `validate_compound_filter()` que dispara excepción `MissingScopeFilterError` si cualquier filtro del compound contract es None.

**Origen:** vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py (T-infra-3, mergeado 2026-05-18 via squash `50143d5`). Subclases productivas: `PatientRepository`, `TreatmentRepository`, futuras `MedicalRecordRepository`, etc. Gate arquitectónico: `test_phi_dual_filter.py` (6 tests PASS).

**Why:** Antes de este patrón, cada repositorio brand vitalia hacía manual `.where(Model.tenant_id == X, Model.clinic_id == Y)` con riesgo de olvido (skip dual filter "porque single-tenant clinic" era el anti-pattern más frecuente en stories pre-infra). El ABC fuerza el contrato a nivel API del repo, no a nivel código de cada método. Arch fitness gate sella la regresión: ningún repo PHI puede mergear sin honrar la validación. Patrón análogo aplicable a:

- **Fitflow** (gimnasios): `tenant_id` + `box_id` (gimnasio físico dentro del franquicia tenant)
- **Fixia** (técnicos hogar): `tenant_id` + `region_id` (zona operativa con técnicos certificados por jurisdicción)
- **Retailly** (e-commerce): `tenant_id` + `store_id` (multi-tienda dentro de la misma marca D2C)
- **Comunify** (creator economy): `tenant_id` + `cohort_id` (programa/cohorte dentro del creator)
- **SaaSora** (SaaS): `tenant_id` + `workspace_id` (workspaces dentro de la org cliente)
- **Vitalia** misma: ya en producción

**How to apply:**
- Identificación: una brand necesita el patrón si existe AL MENOS UN módulo donde queries deben filtrar por una sub-jerarquía dentro del tenant Y un olvido del segundo filtro causa data leak cross-sub-entidad (no solo cross-tenant).
- Promoción a core: lift `PhiRepositoryBase` → `CompoundScopeRepositoryBase` (renombrar PHI-specific → generic). Subclases brand-specific overriden `_required_scopes()` para declarar qué filtros son obligatorios. Engine emite `MissingScopeFilterError` con nombre del scope omitido.
- Arch gate genérico: `core/luana-core-compliance/tests/architecture/test_compound_scope_filter.py` que recibe brand path como param y verifica que repos en `{brand}/backend/src/modules/{brand}/{module}/repositories/` que extiendan `CompoundScopeRepositoryBase` honran `validate_compound_filter()` en cada `await` query.
- Brand opt-in: cada brand declara qué módulos requieren compound scope en `{brand}/config/brand.yaml::compliance_level` (`hipaa_lite` enable dual `tenant+clinic`, `multi_workspace` enable dual `tenant+workspace`, etc.).

**Cross-brand candidacy:** El patrón aplica a CUALQUIER brand multi-jerarquía. Vitalia es el primer caso productivo. Promote a `/pm-luana` para evaluar:

1. Lift `PhiRepositoryBase` → `CompoundScopeRepositoryBase` en `core/luana-core-compliance/` (o `core/luana-core-platform/repositories/`)
2. Generalizar `MissingClinicFilterError` → `MissingScopeFilterError(scope_name: str)` con scope_name dinámico
3. Documentar en `docs/core-modules/compliance.md` con catálogo de compliance_level → required_scopes mapping
4. Brand templates `_pm-brand-template/{brand}/config/brand.yaml` incluyen field `compliance_level` con default `single_tenant`

**Proposal trigger:** `/pm-luana` puede levantar proposal `docs/promotion-protocol/proposals/2026-MM-DD-lift-compound-scope-repository-base.md` cuando otra brand (típicamente fitflow al bootstrappear, o comunify Story 13+) requiera el mismo patrón. Threshold sugerido: 2 brands consumer probable → lift.

**Anti-patterns a evitar al promover:**
- ❌ Hardcodear `clinic_id` como parameter name en API base — usar `**required_scopes` o `scopes: dict[str, UUID]`
- ❌ Lift sin renombrar — `PhiRepositoryBase` semántica vitalia-medical específica
- ❌ Lift sin arch test genérico — sin gate sintetiza protección
- ❌ Lift sin migration path — brands que ya usan single-filter deben opt-in explícito en brand.yaml
