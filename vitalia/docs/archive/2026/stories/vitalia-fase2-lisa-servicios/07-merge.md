# 07-merge.md — vitalia-fase2-lisa-servicios

---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
release: F2
merged_at: 2026-06-19T18:00Z
merged_by: /pm-vitalia
commit_squash_sha: pending-manual    # squash wip/vitalia→main = paso Chris-gated (staging deploy MANUAL · git-safety). Story cierra en wip/vitalia.
checkpoints_path: "./CHECKPOINTS.md"
gherkin_matrix_path: "./06-audit/gherkin-matrix.md"
---

## § 1 — Gherkin verification matrix

> Output verbatim de `/auditor` Phase D. Detalle completo: `06-audit/gherkin-matrix.md`.

**Built scenarios (§1-22 del spec):** 20 grupos → todos con test real PASS (BE offer 172 · arch 298 · vitest servicios 164 incl. autosave arch-test). Core happy-path (cap `new`, PISO HARD) verificado LIVE por Chris (dod_evidence).

**Deferred (must_pass:false · owner asignado · NO green-phantom):** E2E full-chain (VR-D1, skip-gated) · visual goldens 8 (VR-D2) · contract-test FE↔BE (VR-D3, HB-42) · RAG sub-phase B (VR-D4, /pm-luana STOP-2).

**Coverage:** built = todos PASS · cero FAIL · cero NO_COVERAGE silencioso (deferidos explícitos con owner).

## § 2 — Playwright E2E run

Story UI, pero el **E2E full-chain está DEFERRED (VR-D1)**: los specs `e2e/shell-organism/lisa-servicios-*.spec.ts` existen pero `test.skip` gated en `E2E_OFFER_ID`/`E2E_ENABLE_WRITES` (no ejercidos) + importan `@playwright/test` directo (requisito: migrar a `fixtures/base.ts` al activar). Owner: auditor Carril R (un-skip + seed offer-id) o follow-up.

`gherkin_coverage_note`: la verificación del happy-path se cubrió **LIVE por Chris** (dod_evidence · § 6), no por E2E automatizado. El E2E automation queda en el ledger deferred (VR-D1).

## § 3 — Capabilities updated/created

### NEW
- `vitalia/docs/product/capabilities/offer/lisa-servicios.yaml` — status: `beta → live` (cap_change_type: new · cap-doctor 0 deriva · ≥1 scenario + e2e file existe → cross_check_3 OK)
  - 8 scenarios (catalogo-activar / crear-plantilla / autosave-campo-rico / faq-objeciones-par-incompleto / especialistas-muestra-nombre / plan-pago-3-cobros / keystone / cross-tenant)
  - 6 business_rules con code_ref real
  - access + dev_preview (rutas/endpoints reales) + test_coverage (## Tests)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/offer.md` — NEW · auto-list incluye `lisa-servicios` (beta → live)

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
# BE módulo offer
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/offer/ -q     # 172 PASS
# Arch fitness
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -q              # 298 PASS
# FE
cd ${WS}/vitalia/frontend && npx tsc --noEmit && npx vitest run src/features/lisa/components/servicios/ src/__tests__/architecture/test-autosave-value-from-local-state.test.ts   # 164 PASS
# Live (autenticado · dev-app vitalia · dr.demo@vitalialat.com): crear servicio → autosave campo → activar → recargar plan-pago muestra montos
```

## § 6 — Verificación live — DoD (Critical Rule #37)

```yaml
dod_live_verified: true
dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Chris ejerció · tenant Sanaré e69a691d · dr.demo@vitalialat.com)"
dod_evidence:
  - action: "POST /api/v1/offer/servicios/custom (crear) + PATCH (autosave nombre + campo rico) + POST /{id}/activate"
    observed: "workspace renderiza · autosave persiste al recargar · card pasa a activo"
    backend_log: "POST 201 · PATCH 200 · activate 200 · DB products.status=active · growth_studio_event service_activated · sin traceback"
dod_verified_at: 2026-06-16
auditor_independent_reverify: "BLOQUEADO por HB-89 (lane-C Chrome sin sesión Clerk → dev-app /sign-in). Documentado · NO defecto · cubierto por dod_evidence de Chris (gold standard) + chris_verify.signoff."
```

**Gate REFUSE (Fase F):** `dod_live_verified: true` ✓ · `dod_evidence` con writes + efecto ✓ · `chris_verify.signoff = SATISFIED_WITH_FOLLOWUPS` (sev≤medium) ✓ · `dev_app_verified.evidence` no-vacío ✓ → **merge habilitado**.

## Cross-references
- `CHECKPOINTS.md` — C1-C5 (APPROVED) · `06-audit/gherkin-matrix.md` — Phase D verbatim
- `01-spec.md § Gherkin RECONCILE §17-22 + § Matriz RECONCILIADA` · `04-validators.yaml § RECONCILE`
- `REVIEW-backend.md` (PASS) · `REVIEW-frontend.md` (APPROVED + 1 WARN currency→follow-up)

## Story → archive
- `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/` → `vitalia/docs/archive/2026/stories/vitalia-fase2-lisa-servicios/` (mismo commit · R2)
- Release F2 actualiza `stories[]` (lisa-servicios → done)

## Pendiente manual (NO parte de "done")
- **Squash-merge `wip/vitalia` → `main`** (integración + staging deploy MANUAL · git-safety · Chris-gated).
- Follow-ups (chris_verify.signoff.open_items): `tenant-currency-config` · `adrian-ficha-rica-knowledge` · `accordion-dedup-cleanup` · VR-D1..D4 deferred · ADR-009→canon proposal /pm-luana.
