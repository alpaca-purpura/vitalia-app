---
story_id: vitalia-compliance-audit-rbac-gap
type: service-story
agent_owner: config
module: compliance
capability: compliance.hipaa-lite-defensive-stack
cap_target: hipaa-lite-defensive-stack
cap_change_type: fix
state: dropped
release: F2
architecture_pattern: ADR-vitalia-004
priority: critical
ratified_by_chris: false
parallel_safe: true
last_modified: 2026-06-07
security_finding: true
repro_verified: false
dropped_date: 2026-06-07
dropped_reason: >-
  Ya fixeado por hotfix `18e10822` (RBAC en GET /medical-compliance/{events,export-csv} +
  test_compliance_endpoints_rbac.py). El gap que motivaba esta story está cerrado.
  Detectado durante el reencuadre de vitalia-fase2-lisa-compliance (2026-06-07).
  Residual SOFT: cross_check_4 estructural (router compliance vive en routes.py
  `# cap: __shared__`) → follow-up HB-59, no es esta story.
---

> ⛔ **DROPPED 2026-06-07** — el fix RBAC ya landed en hotfix `18e10822`. Ver frontmatter `dropped_reason`. Lo de abajo es el hallazgo histórico (ya resuelto).

# Gap de seguridad RBAC · endpoint del log de auditoría HIPAA-lite

> **Origen:** consolidación SDD 2026-05-28 (Fase 5, investigación cross_check_4). Único gap de seguridad REAL detectado en la auditoría de realidad. Ver `docs/process/lifecycle.md` + `docs/process/learnings.md` § 2026-05-28.

## Hallazgo

Los endpoints del **log de auditoría HIPAA-lite** no tienen guard de rol — cualquier rol autenticado puede acceder:

- `GET /api/v1/vitalia/medical-compliance/events` — `vitalia/backend/src/modules/vitalia/api/routes.py:842` (`list_compliance_events`)
- `GET /api/v1/vitalia/medical-compliance/export-csv` — `routes.py:875`

El docstring afirma "Requires admin role (clinic_owner) — auth enforced by Clerk JWT middleware", pero **no existe tal middleware de roles** en `main.py` (Clerk autentica pero no gatea roles a nivel handler). La cap `compliance.hipaa-lite-defensive-stack` declara `requires_role: [admin_clinic, staff_vitalia]` que el código NO enforcea.

**Severidad:** ALTA (es el surface de compliance más sensible). **Exposición actual:** baja — ambos endpoints son stubs que devuelven vacío (`ComplianceEventListResponse(events=[], total=0)`). El gate falta pero todavía no hay datos que filtrar. Se vuelve crítico cuando se cablee la query real.

## Scope del fix

- Agregar guard de rol explícito en ambos endpoints (consistente con el patrón del codebase: `@require_phi_access` o `Depends(require_brand_owner_access())` o check inline `if user_role not in {admin_clinic, staff_vitalia}: 403`).
- Reconciliar el rol `staff_vitalia` (no-estándar) contra el SSoT de roles HIPAA-lite (`_shared/auth/rbac.py`).
- TDD: test RED que pega sin rol → 403; GREEN con rol válido.
- Al cerrar, cross_check_4 baja a 0 → Fase 5.1 puede flipear cc4 a HARD para vitalia.

## Notas

- Esta historia es el vehículo SDD correcto para el fix (no se hot-patcheó en el sweep de consolidación — la seguridad va por el flujo /po → /architect → /dev-team → /auditor).
- Bloquea: flip de cross_check_4 a HARD (Fase 5.1 del roadmap en lifecycle.md).
