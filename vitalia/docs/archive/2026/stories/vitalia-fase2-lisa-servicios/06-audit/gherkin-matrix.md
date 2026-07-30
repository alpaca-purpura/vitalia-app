# Gherkin verification matrix — vitalia/vitalia-fase2-lisa-servicios

> Auditor: Phase D (proceso v5 · cross-check con `01-spec.md § Matriz de cobertura RECONCILIADA`)
> Date: 2026-06-19
> Verdict: APPROVED (built scenarios PASS via real tests; deferred scenarios honestly must_pass:false con owner — NO green-phantom)

## Built scenarios — PASS (test real)

| Scenario / RN | Test path | Status |
|---|---|---|
| §1 catálogo (activar/buscar/rbac/soft-delete) | `tests/modules/vitalia/offer/test_servicios_router.py` + `test_servicios_rbac.py` + FE `CatalogoView.test.tsx` + `ServiceCard.test.tsx` | PASS |
| §2 crear (plantilla/personalizado/borrador) | `test_biblioteca_service.py` + `test_catalog_service.py` + FE `BibliotecaPicker.test.tsx` | PASS |
| §3 identidad + herencia bloqueada (RN-30) | FE `ChipOrigen.test.tsx` + `RungPicker.test.tsx` | PASS |
| §4 qué es + variantes (RN-29) | FE `VariantsRepeater.test.tsx` + `test_vos.py` | PASS |
| §5 modalidad/agenda (RN-28/31/32) | FE `ModalidadPicker.test.tsx` + `test_vo_dto_to_domain_invariants.py` | PASS |
| §6 ficha paciente (RN-26) | `test_detail_dto_carries_rich.py` + `test_completeness.py` | PASS |
| §7 Para Adrián (argumentario/FAQ/objeciones) | `test_sales_brief_service.py` + FE `FaqPairList.test.tsx` + `ObjecionPairList.test.tsx` | PASS |
| §8 especialistas (vincular/desvincular/sin-doctor) | `test_specialist_link_service.py` + `test_specialist_link_repository.py` + FE `EspecialistaLinkPicker.test.tsx` + `EspecialistasView.test.tsx` | PASS |
| §9 plan de pago (3 cobros/calculados/RN-6/RN-11) | `test_pricing_calc.py` + FE `PlanPagoView.test.tsx` | PASS |
| §10 prueba social (consentimiento RN-33) | `test_proof_service.py` + `test_case_consent_gate.py` + FE `TestimonialsList.test.tsx` | PASS |
| §11 escalera (peldaños/drag/a11y) | FE `EscaleraView.test.tsx` | PASS |
| §12 autoguardado (RN-20) | FE `test-autosave-value-from-local-state.test.ts` (arch) + `ResumenView.test.tsx` | PASS |
| §15 KEYSTONE (AC-6) | `test_keystone_offer_shape.py` + **live (Chris dod_evidence: DB products active + growth_studio_event)** | PASS |
| §16 adversarial (cross-tenant/rbac/idioma) | `test_servicios_cross_tenant.py` + `test_servicios_rbac.py` + arch (298 tests) | PASS |
| §17 autosave value-local (G2-F11) | `test-autosave-value-from-local-state.test.ts` + `ResumenView.test.tsx` (sin-mock) | PASS |
| §18 FAQ/objeciones par-incompleto (G2-F12/F12b) | `test_sales_brief_service.py` + `ParaAdrianView.test.tsx` | PASS |
| §19 especialistas nombre no-UUID (G2-F13) | `test_specialist_link_service.py` + `EspecialistasView.test.tsx` | PASS |
| §20 plan-pago Decimal-string round-trip (G2-F14/F14b) | `PlanPagoView.test.tsx` (strings reales del wire) | PASS |
| §21 activar confirm/reflejo (G2-F2a/F2b) | `ServiceStatusBar.test.tsx` | PASS |
| §22 navegación detalle (G2-F4/F5/F10) | `EspecialistasView.test.tsx` + shell-routes N3_DEFAULT_LEAF tests | PASS |

**Core happy-path (cap_change_type: new · PISO HARD):** crear → autosave → activar → keystone = **verificado LIVE por Chris** (dod_evidence: POST /custom 201, PATCH 200, activate 200, DB products.status=active, growth_studio_event, build_identity data shape) + unit/component/BE green. ✅ El piso HARD se cumple (el core fue ejercido live, no diferido).

## Deferred scenarios — must_pass:false (NO green-phantom · owner asignado)

| Scenario / item | Por qué deferred | Owner | Validator |
|---|---|---|---|
| E2E happy-path full-chain (crear→editar→plan-pago→especialista→activar) | specs existen pero `test.skip` gated en `E2E_OFFER_ID`/`E2E_ENABLE_WRITES` (no ejercidos) | auditor Carril R (un-skip + seed offer-id) o follow-up | VR-D1 |
| 8 visual goldens (catalogo/escalera/workspace/nuevo × 2 themes) | baselines no generados (`e2e/__screenshots__/servicios/` vacío) | dev-team/auditor (generar + ratchet) | VR-D2 |
| Contract-test FE↔BE (shape real del wire) | ausente — los bugs G2-F11/F14b nacieron de contratos imaginados | HB-42 (gate transversal) + esta story | VR-D3 |
| §14 RAG runtime (doc→indexado/retrieval) + §15 build_identity con contexto agente completo | engine-lift (Qdrant indexer + sales_agent tool) | /pm-luana (STOP-2 · Sub-phase B) | VR-D4 |

## Finding (fold into VR-D1)

Los specs e2e `lisa-servicios-{crear,autosave,especialistas,escalera-drag}.spec.ts` + `visual/lisa-servicios-visual.spec.ts` importan **`@playwright/test` directo** (no `fixtures/base.ts`). NO es auto-FAIL acá porque están SKIPPED/deferred (no corren, no se presentan como live-verify — la live-verify es el dod_evidence de Chris). **Requisito agregado a VR-D1:** cuando se activen (un-skip + E2E_OFFER_ID), DEBEN migrar a `fixtures/base.ts` (gate anti-burbuja) antes de contar como cobertura.

## LIVE verification (DoD #37)

- **Owner-verified (gold standard):** Chris ejerció los writes críticos LIVE en dev-app vitalia (`dod_evidence` en checkpoint: POST 201 / PATCH 200 / activate 200 + BE logs + DB + growth_studio_event) + `chris_verify.signoff = SATISFIED_WITH_FOLLOWUPS`.
- **Auditor independent re-verify:** ATTEMPTED (dev stack UP: backend/frontend/cloudflared containers running) → **BLOQUEADO por HB-89** (lane-C Chrome sin sesión Clerk → `dev-app.vitalialat.com` redirige a `/sign-in`). Gap de infra documentado (HB-89), NO defecto de código. NO se fingió evidencia.
