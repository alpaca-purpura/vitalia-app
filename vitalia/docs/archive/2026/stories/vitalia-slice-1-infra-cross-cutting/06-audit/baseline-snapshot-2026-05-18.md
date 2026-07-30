# Audit baseline snapshot — vitalia-slice-1-infra-cross-cutting

> **NOT a full /auditor CHECKPOINTS.md.** Baseline snapshot pragmático Opus producido durante
> cement-session 2026-05-18 del story-closure-gate. Documenta el estado real del story al
> momento del session-split + acciones pendientes para sesión nueva.

**Auditor:** Claude Opus 4.7 (pragmático, sesión cement story-closure-gate)
**Date:** 2026-05-18
**Verdict:** NEEDS_FIX_BEFORE_FULL_AUDIT (defer_audit ratificado Chris)

## Contexto

Esta sesión cementó el story-closure-gate (cement-date 2026-05-18) en 5 commits:
- e6d59c9 — foundation rule + ADR-005 + learnings
- fed4675 — paradigm v4 update (CLAUDE.md + pm-redesign)
- de159f7 — 14 skills cementadas (dev-team auto-handoff + auditor Phase D + 11 pm-* bootstrap + template)
- 123de15 — templates (gherkin_coverage field + 07-merge 5 secciones)
- 5a0c643 — hooks + scripts Layer 4-5 enforcement

Operational test final = audit pragmático de este story (infra-cross-cutting) que estaba
state=developed pre-cement. Resultado: 1 FE arch fitness FAIL detectado → demuestra que
el nuevo gate funciona + activa defer_audit como escape valve.

## Quality gates run (snapshot)

### Backend ✅ ALL PASS

| Gate | Result | Detail |
|---|---|---|
| Ruff check | ✅ PASS | All checks passed (cero errores ruleset full) |
| Ruff format | ✅ PASS | 400 files already formatted |
| Architecture fitness (pytest) | ✅ PASS | **226/226 tests passed** en `vitalia/backend/tests/architecture/` |

Tests arch ejecutados incluyen: `test_audit_log_sync_write`, `test_extension_sdk_registration`,
`test_extraction_orchestrator_inheritance`, `test_lucas_cron_tz_aware`, `test_migrations_idempotent`,
`test_no_legacy_paths`, `test_no_observability_mirror`, `test_pgcrypto_phi_columns`, `test_phi_dual_filter`,
`test_response_model_required`, `test_screening_yaml_completeness`, `test_vitalia_cost_bucket_invariant`,
`test_vitalia_no_pii_in_cacheable_slots`, `test_vitalia_no_query_without_tenant_filter`,
`test_vitalia_payment_inherits_core_base`, `test_vitalia_personas_yaml_completeness`,
`test_vitalia_rubric_md_v1_schema`, `test_vitalia_slot_4_safety_markers_present`.

Cubre todas las hard rules HIPAA-lite vitalia: dual filter tenant+clinic, pgcrypto PHI columns,
audit_log sync write, no observability mirror cross-brand.

### Frontend — TSC + ESLint ✅ + Arch fitness 🔴 1 FAIL

| Gate | Result | Detail |
|---|---|---|
| TSC --noEmit | ✅ PASS | 0 type errors |
| ESLint | ✅ PASS | (run no logged en este snapshot pero T-arch-1-result reportaba 0 errors 0 warnings) |
| Vitest arch fitness | 🔴 **1 FAIL / 38 tests** | 1 test failed: `test_no_hardcoded_colors.test.ts` |

#### FE arch FAIL detail — FE-A1 hardcoded colors

Test: `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts`
Allowlist: `KNOWN_COLOR_VIOLATIONS = Set()` (clean baseline declarado en T-infra-4)

**8 archivos violando ratchet clean baseline:**

| File | Violations | Severity |
|---|---|---|
| `src/components/shared/agents/AgentAvatar.stories.tsx` | 4 hex (#6B7280×3, #16A34A) | LOW (Storybook viewer-only) |
| `src/components/shared/attribution/AttributionMatrixWidget.tsx` | 1 `hsl(` | **HIGH (production)** |
| `src/components/shared/channels/ChannelBreakdownRow.stories.tsx` | 1 hex (#E8EAF0) | LOW (Storybook) |
| `src/components/shared/contact-sidebar/ContactSidebar.stories.tsx` | 3 hex (#01B2F8×3) | LOW (Storybook) |
| `src/components/shared/marketing/MarketingBowtieSVG.tsx` | 8 `hsl(...)` literal (no var()) | **HIGH (production SVG)** |
| `src/components/shared/phi/PiiMaskedSpan.stories.tsx` | 2 hex (#6B7280×2) | LOW (Storybook) |
| `src/components/shared/phi/RequireRole.stories.tsx` | 23 hex (#B8DC2A, #F0FDF4, etc.) | LOW (Storybook) |
| `src/components/shared/wizard/WizardChatThread.tsx` | 2 `hsl(` | **HIGH (production)** |

Verificación spot-check `MarketingBowtieSVG.tsx`:
```
line 81: stopColor="hsl(198 99% 49%)"
line 82: stopColor="hsl(198 99% 49%)"
line 85: stopColor="hsl(287 53% 37%)"
line 86: stopColor="hsl(287 53% 37%)"
line 109: fill="hsl(198 99% 49%)"
```

Estos son `hsl(literal)` directos, NO `hsl(var(--vitalia-X))` (cualquier consumo via CSS var
pasa el regex porque empieza con `hsl(`). El fix correcto es refactor a `hsl(var(--vitalia-channel-primary))` u otro token equivalente en `globals.css`.

## C1-C5 grid (parcial, snapshot)

### C1 — Code
- [x] Ruff check + format clean (BE)
- [x] TSC strict 0 errors (FE)
- [x] ESLint 0 errors (FE, per T-arch-1-result + T-infra-* result files)
- [ ] **🔴 FE arch fitness 37/38 PASS — 1 FAIL (FE-A1 hardcoded colors)**

### C2 — Spec compliance (Phase D gherkin)
- [N/A] Story es sub-story infra enabler del padre `vitalia-ux-discovery`. NO tiene scenarios
  Gherkin directos del 01-spec.md padre — los scenarios viven en las 6 sub-stories siguientes
  (onboarding-wizard, inbox, pipeline, agenda, fidelizacion, marketing). Esta sub-story
  aporta plumbing: migrations, registries, observability, AppShell components, IAM/CRM scaffold.
- [N/A] Playwright E2E specs: pendientes definirse en sub-stories consumer
- Recomendación: documentar exenta de Phase D matrix con nota explícita en 07-merge.md
  (gherkin_coverage_note: "Infra enabler sub-story sin scenarios padre — coverage via sub-stories siguientes")

### C3 — Architecture
- [x] BE 226/226 arch fitness PASS (DDD, tenant isolation, anti-duplication, HIPAA-lite dual filter, pgcrypto PHI columns, observability no-mirror cross-brand, extension SDK registration)
- [ ] **🔴 FE 1/9 test files FAIL** (test_no_hardcoded_colors)
- [x] FSD-Lite boundaries respected (per arch tests passed)
- [x] Server-First pattern (per arch tests passed)

### C4 — Cross-cutting
- [x] Spanish neutro LatAm (test_no_voseo_in_copy + test_vitalia_personas_yaml_completeness PASS)
- [x] PHI sanitization (test_phi_dual_filter + test_vitalia_no_pii_in_cacheable_slots PASS)
- [x] Pgcrypto encryption (test_pgcrypto_phi_columns PASS)
- [x] Migrations idempotentes (test_migrations_idempotent PASS)
- [x] HIPAA-lite compliance (vitalia/.claude/rules/hipaa-lite.md adherence per BE arch suite)

### C5 — Trace
- [ ] checkpoint.md final state=done — **DEFERRED** (defer_audit:true)
- [ ] BACKLOG regenerated post-merge — pending sesión nueva
- [ ] Capabilities promoted — pending sesión nueva (paso 2 capability promotion)
- [ ] Module MD refreshed — pending sesión nueva
- [ ] Story archive — pending sesión nueva

## Findings summary
- C1: 3/4 ✅ (1 FAIL FE arch fitness)
- C2: 5/5 N/A (infra enabler exenta de Phase D matrix)
- C3: 5/6 ✅ (1 FAIL FE arch)
- C4: 5/5 ✅
- C5: 0/5 (deferred, pendiente sesión nueva)

## Verdict

**NEEDS_FIX_BEFORE_FULL_AUDIT**

Razón: 1 FE arch fitness FAIL (FE-A1 hardcoded colors) detectado en 8 archivos
(3 production .tsx + 5 Storybook .stories.tsx). Antes de declarar APPROVED + transition
state=reviewing→done, requiere:

1. **Fix production code (3 archivos HIGH priority):**
   - `AttributionMatrixWidget.tsx`: 1 `hsl(` → refactor a `hsl(var(--vitalia-X))` token
   - `MarketingBowtieSVG.tsx`: 8 `hsl(...)` SVG fills/stops → token consumption
   - `WizardChatThread.tsx`: 2 `hsl(` → token consumption

2. **Decide policy Storybook stories (6 archivos LOW priority):**
   - Opción A: agregar a `KNOWN_COLOR_VIOLATIONS` allowlist (ratchet expand documenta
     que stories son viewer-only, no production shipping)
   - Opción B: refactor stories.tsx a token consumption como production

3. **Spawn /auditor real Opus (auditor-backend + auditor-frontend) en sesión nueva**
   post-fix para CHECKPOINTS.md C1-C5 completo + Phase D matrix (con la nota N/A enabler).

4. **Phase E DOCS + Phase F MERGE** post APPROVED real.

## defer_audit ratificado

`defer_audit: true` en `../checkpoint.md` con `defer_audit_reason` explícito + razón session-split + audit_pending_actions enumeradas. Bootstrap `/pm-vitalia` próxima sesión pingeará esta deuda via Step 0 NEW scan.

## Validación gate operacional

Este audit es el **operational test del story-closure-gate cementado 2026-05-18**. Resultados:

- ✅ Gate detecta FAIL real (FE arch fitness) que /dev-team marcó como GREEN
- ✅ Escape valve `defer_audit: true` funciona como diseñado
- ✅ Bootstrap pm-vitalia futura sesión pingeará deuda
- ✅ Pre-commit hook Section 11 NO bloquea este commit (toca BOTH stories open, válido)
- ✅ Pattern documentado para futuros casos similares
