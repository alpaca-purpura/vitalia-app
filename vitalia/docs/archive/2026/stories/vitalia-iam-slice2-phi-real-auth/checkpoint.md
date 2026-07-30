---
story_id: vitalia-iam-slice2-phi-real-auth
type: service-story
agent_owner: config
module: iam
cap_target: iam-scaffold-slice-1            # extend: desentuba el decoder PHI (stub→JWKS real)
cap_change_type: extend
release: F2
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale      # BE auth wiring, no sub-tab UI
priority: high
ratified_by_chris: true   # 2026-05-30 Q1-Q3 ratificadas
parallel_safe: false
last_modified: 2026-05-30
state: done
phase: MERGED_DONE
merged_at: 2026-05-30
merged_by: pm-vitalia
audit_verdict: APPROVED
gherkin_matrix: 06-audit/gherkin-matrix.md
live_verification: "god-matrix JWT real 2026-05-30: doctor 200 / marketing 403 / forged+stub 401 (VERIFICATION-godmatrix-live.md). Gaps pre-existentes: vitalia_patients/vitalia_leads tablas faltan en dev (observed-bug)."
prior_art_scan_done: true
prior_story: vitalia-stub-caps-scenario-backfill   # nace del hallazgo de aquella (stub PHI rechaza JWT real)

# Autonomous mode — HARD false (auth/PHI sensible · architect-autonomous-mode.md)
autonomous_mode: false
autonomous_mode_hard_false_reason: "Toca auth + PHI (HIPAA-lite). Per .claude/rules/architect-autonomous-mode.md: security/auth/PHI requiere supervisión Chris. NO auto-build."

next_action: "/dev-team T-1 (BE-auth core) → T-2 (repos-wire) + T-3 (FE hook) → build SUPERVISADO (autonomous_mode false) → gate verificación god-matrix JWT real → /auditor → /pm-vitalia merge."
ready_package: [03-arch.md, 04-validators.yaml, 05-guidelines.md, 06-tickets.yaml, dispatch-plan.md]
ready_closed_at: 2026-05-30
ready_closed_by: architect
# Autonomous ratify — Chris override in-session (escape valve architect-autonomous-mode.md)
autonomous_mode_ratified_in_session: true
autonomous_mode_ratified_by: chris
autonomous_mode_ratified_at: 2026-05-29T23:17:07-05:00
autonomous_mode_ratify_note: "Chris ratificó autónomo explícito ('hazlo de forma autonoma, aplicando todo lo aprendido, todo debe servir'). Gates innegociables: anti-orphan CONN + verificación REAL (JWT real god-matrix + logs, no HTTP 200) + test-design-doctrine."
---

# Slice 2 PHI — desentubar el decoder JWT (stub → JWKS real) + rol desde DB + repos reales

> **Origen:** hallazgo de `vitalia-stub-caps-scenario-backfill` (done 2026-05-30). Las superficies PHI (crm/clinics/inbox/marketing) usan un decoder STUB Slice-1 que SOLO acepta `stub:{tenant}:{clinic}:{role}:{user}` y RECHAZA el JWT real de Clerk → 401. Mientras siga stub, ningún cap PHI puede verificarse live en dev-app (el FE manda JWT real → 401). Esta story lo desentuba reusando el JWKS del engine.

## Prior art scan (anti-duplication-refining · 2026-05-30)

| Fuente | Hallazgo | Decisión |
|---|---|---|
| **Engine `core/luana-core-iam/application/auth.py`** | Ya tiene `verify_token_payload(token)` + `jwt.PyJWKClient(JWKS_URL)` + `verify_clerk_token`. | **REUSE vía import** — NO recrear JWKS (anti-duplication). |
| **Engine `core/luana-core-iam/.../user_tenant_repository.py` + `user_tenant_model.py`** | Rol vive en `user_tenants.role` (DB). | **REUSE** — el rol fluye desde DB, no del token. |
| **Stub actual `vitalia/.../iam/infrastructure/clerk_jwt_decoder.py`** | Slice-1 stub, parsea `stub:...`, rechaza JWT real. | **REEMPLAZAR** por verificación JWKS real (mantener `ClerkJwtPayload` shape / `VitaliaRole` domain). |
| **god-matrix (story previa)** | 8 usuarios RBAC sobre Sanaré (DB↔Clerk alineados, seed `seed_test_users_link.py`). | **REUSE como fixture de verificación.** |

**Conclusión:** cero duplicación — consume engine JWKS + user_tenants vía import; reemplaza el stub brand-local. `cap_change_type: extend` coherente (extiende iam-scaffold a auth real).
