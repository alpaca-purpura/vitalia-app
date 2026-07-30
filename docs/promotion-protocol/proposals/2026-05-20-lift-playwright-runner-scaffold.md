---
proposal_id: 2026-05-20-lift-playwright-runner-scaffold
state: proposed
opened_date: 2026-05-20
opened_by: /pm-luana
ratified_by: null
ratified_date: null

# Origen
origin_learnings:
  - comunify/docs/learnings/2026-05-17-playwright-runner-parity-gap.md   # promotable=yes physical file

origin_brands: [comunify]

# Target
target_package: .claude/skills/_pm-brand-template/
target_module: scaffold FE bootstrap (package.json devDeps + scripts)
target_ep: null

# Impact assessment
semver_bump: n/a   # scaffold
breaking_change: false
brands_affected_consumers: [vitalia, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: [comunify]

# Lift plan
lift_estimated_effort: "30 min"
lift_owner: /dev-team
arch_test_downstream_required: false
migration_notes_required: false

# Parent outcome
parent_outcome: docs/product/outcomes/bootstrap-brand-template-hardening.md
---

## 1. Patrón a promover

**Playwright runner scaffold** = declarar `@playwright/test` como devDependency + scripts `test:e2e:*` consistentes con nicolify pattern. Sin esto, scripts existen pero ejecutarlos falla con `playwright: not found` porque pnpm no hoistea Playwright al `node_modules/` del brand si no está declarado localmente.

### Componentes del scaffold

1. `{brand}/frontend/package.json::devDependencies` con `@playwright/test ^1.59.1`
2. Scripts `test:e2e:smoke`, `test:e2e:fresh`, `test:e2e:auth`, `test:e2e:regression` (mirror nicolify 4 scripts)
3. Estructura `{brand}/frontend/e2e/{specs/smoke/,fixtures/,playwright.config.ts}` con paths consistentes

**Origen story:**
- Comunify: `comunify-dev-stack-functional` (mergeada 2026-05-17)
- Bug origen: Story 12 bootstrap shippeó `playwright.config.ts` + 5 specs + scripts pero NUNCA agregó `@playwright/test` en devDeps
- Síntoma: `npm run test:e2e:smoke` falla con `playwright: not found`
- Fix: agregar devDep + mirror nicolify 4 scripts pattern

## 2. Por qué cross-brand

Todas las brands con Playwright E2E necesitan el devDep declarado localmente. Pnpm workspace NO hoistea Playwright automáticamente si solo está en otro workspace member.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Comunify | ya implementa | origen — dev-stack-functional |
| Vitalia | **gap idéntico** | learning explícitamente cita "vitalia tiene mismo gap" |
| Nicolify | ya implementa | brand referencia (setup completo) |
| Lupulo | gap preventivo | placeholder, mejor heredar correcto |
| 6 brands pendientes | aplicables al bootstrap | heredan template scaffold |

## 3. Análisis técnico

### Signature comparison

```jsonc
// Comunify (post-fix dev-stack-functional)
// comunify/frontend/package.json
{
  "devDependencies": {
    "@playwright/test": "^1.59.1"
  },
  "scripts": {
    "test:e2e:smoke": "playwright test --project=smoke",
    "test:e2e:fresh": "rm -rf playwright/.clerk && playwright test --project=smoke",
    "test:e2e:auth": "playwright test --project=auth",
    "test:e2e:regression": "playwright test --project=regression"
  }
}

// Vitalia (gap)
// vitalia/frontend/package.json
{
  "devDependencies": {
    // NO @playwright/test  ← gap
  },
  "scripts": {
    "test:e2e:smoke": "playwright test --project=smoke"  // ← falla "not found"
  }
}
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Vitalia sweep cambia version Playwright | Baja | Pin exact version `^1.59.1` consistente cross-brand |
| Brand quiere otro test runner | Muy baja | Scaffold es opcional — brand puede no usar Playwright |
| Conflict con setup workspace pnpm | Baja | Validation pnpm install post-add devDep |

## 4. Lift plan

### Pre-lift checklist

- [x] Learning physical file existe (`comunify/docs/learnings/2026-05-17-playwright-runner-parity-gap.md`)
- [ ] Verificar nicolify pattern como reference (4 scripts)
- [ ] Document scaffold en `_pm-brand-template/SKILL.md` § FE Playwright bootstrap

### Lift execution

1. Actualizar `.claude/skills/_pm-brand-template/SKILL.md`:
   - Agregar § "FE Playwright bootstrap"
   - Include verbatim `package.json` devDep line + 4 scripts
   - Cite nicolify como reference impl
   - Warning: "Sin devDep declarado, scripts fallan `not found` aunque otros workspace members lo tengan"
2. NO toca código brand directamente

### Post-lift

- Comunify (origen): ya consume
- Vitalia + lupulo: Story S1 sweep
- Brands futuras: heredan via template

## 5. Decisión

**Recomendación `/pm-luana`:** **APPROVED**

**Razón:**
- DRY threshold: 2 brands ya consumen (comunify + nicolify) — válido
- Gap idéntico CONFIRMADO en vitalia (learning cita explícitamente)
- Riesgo MUY BAJO: scaffold doc + 1 línea devDep + 4 scripts mirror
- ROI: 6 brands futuras evitan rediscover bug + 1 sesión wasted hunting

**Ratificación Chris:** _(pending)_

## 6. Bitácora

- 2026-05-20: opened by /pm-luana. state=proposed.

## 7. Cross-references

- Origin learning: `comunify/docs/learnings/2026-05-17-playwright-runner-parity-gap.md`
- Capability impl: `comunify/docs/product/capabilities/` (verify si dev-stack-functional tiene yaml)
- Parent outcome: `docs/product/outcomes/bootstrap-brand-template-hardening.md`
- Sister proposals: `2026-05-20-lift-camino-b-design-system.md`, `2026-05-20-lift-tailwind-v4-postcss-scaffold.md`
- Reference impl: `nicolify/frontend/package.json` (4 scripts + devDep)
