---
outcome_id: bootstrap-brand-template-hardening
type: platform
state: refining
opened_date: 2026-05-20
opened_by: /pm-luana
priority: MEDIUM-HIGH (prevención sistémica)
why_now: "3 gaps idénticos detectados en Comunify (sweep vitalia parcial) — escalfold _pm-brand-template/ incompleto. Cada gap × 6 brands futuras = 18 incidents-en-cadena evitables."
affected_brands: [vitalia, comunify, lupulo, + 6 pendientes]
consumer_brands: [vitalia, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_packages_potencial: [.claude/skills/_pm-brand-template/, core/luana-core-platform]
ssot_owner: /pm-luana
last_updated: 2026-05-20
---

# Outcome platform — Bootstrap brand template hardening

## Spark

Tres learnings comunify (promotable=yes) tienen el mismo root cause: **el scaffold `_pm-brand-template/` no es exhaustivo**. Brands que bootstrappean copiando el scaffold heredan gaps silenciosos que solo se detectan post-merge cuando ya causaron incident.

| Gap | Origen story comunify | Síntoma típico | Sweep vitalia status |
|---|---|---|---|
| 1 — Tailwind v4 PostCSS wiring | `comunify-design-system-tailwind-v4-tokens` | `.bg-X` utilities NO emiten en bundle (CSS 467 líneas vs 1673 con fix) | ❌ vitalia tiene gap latente (verified: NO `postcss.config.*`, NO `@tailwindcss/postcss` devDep) |
| 2 — Playwright runner devDep | `comunify-dev-stack-functional` | Scripts `test:e2e:smoke` declarados pero `@playwright/test` no en devDeps | ❌ vitalia + lupulo tienen gap idéntico |
| 3 — Camino B design system a11y | `comunify-design-system-a11y-contrast-cement` | Token system shipped sin pares foreground/background canónicos → WCAG AA fail latente | ⏸ vitalia no audit ejecutado todavía (probable gap latente) |

## Why now (oportunidad)

- **Coste compuesto:** cada gap × 6 brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) = **18 incidents-en-cadena evitables** si actualizamos el scaffold ahora.
- **Verificación cross-brand barata:** Vitalia ya está confirmada con 2 de 3 gaps (postcss + playwright). Sweep durante outcome.
- **Brand bootstraps inminentes:** las 6 brands futuras heredarán los gaps si no fixamos el template antes.
- **No requiere lift a core inmediato:** el scaffold es un `.claude/skills/` doc + per-brand files (FE config). Lift bajo riesgo.

## Decomposition a stories + proposals

Cada gap = 1 promotion proposal individual abierta en paralelo (state=proposed). Vinculadas a este outcome:

| Proposal | Slug | State | Cubre |
|---|---|---|---|
| `2026-05-20-lift-camino-b-design-system.md` | lift-camino-b-design-system | proposed | Gap 3 — design system a11y Camino B |
| `2026-05-20-lift-tailwind-v4-postcss-scaffold.md` | lift-tailwind-v4-postcss-scaffold | proposed | Gap 1 — Tailwind v4 PostCSS wiring |
| `2026-05-20-lift-playwright-runner-scaffold.md` | lift-playwright-runner-scaffold | proposed | Gap 2 — Playwright runner devDep |

### Stories child outcome (después de proposals ratificadas)

1. **Story S1 (Sweep vitalia):** `vitalia-frontend-scaffold-sweep` — aplicar los 3 fixes a vitalia/. Estimate M (4-6 horas). Owner: `/pm-vitalia` + `/dev-team`.

2. **Story S2 (Sweep lupulo):** `lupulo-frontend-scaffold-sweep` — idem (lupulo es placeholder, fix preventivo). Estimate S. Owner: `/pm-lupulo` + `/dev-team`.

3. **Story T1 (Template update):** `update-pm-brand-template-scaffold` — actualizar `_pm-brand-template/SKILL.md` con los 3 fixes integrados en checklist bootstrap 13 pasos. Estimate S. Owner: `/pm-luana`.

4. **Story D1 (Cross-brand audit):** `audit-existing-brands-scaffold-gaps` — audit explícito de nicolify/vitalia/lupulo verificando NO hay otros gaps similares latentes. Estimate S. Owner: `/pm-luana`.

## Definición de éxito

- 3 proposals ratificadas Chris (APPROVED) + migrated
- Vitalia + lupulo sin gaps de los 3 tipos identificados
- `_pm-brand-template/SKILL.md` actualizado con scaffold hardening
- 0 nuevos incidents del mismo tipo en próximas 6 brands bootstrap

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Sweep vitalia introduce regression downstream | Media | R3 downstream regression mandatory en cada proposal |
| Camino B pattern no aplica a otros brand styles | Baja | Optional pattern (brand puede no usarlo) — solo registra en template como recommended |
| Template update sin verify causa nuevo gap | Baja | Story D1 audit cross-brand previo a cerrar outcome |

## Bitácora

- 2026-05-20: opened by /pm-luana (autonomous Chris autorización "resolvamoslo todo de una vez"). 3 proposals abiertas simultáneamente como children.

## Próximo paso

Chris ratifica APPROVED/REJECTED cada uno de los 3 proposals individuales. Una vez ratificados → handoff `/dev-team` para lift execution. Stories sweep brand-specific se abren después de proposals migrated.

## Cross-references

- 3 proposals children:
  - `docs/promotion-protocol/proposals/2026-05-20-lift-camino-b-design-system.md`
  - `docs/promotion-protocol/proposals/2026-05-20-lift-tailwind-v4-postcss-scaffold.md`
  - `docs/promotion-protocol/proposals/2026-05-20-lift-playwright-runner-scaffold.md`
- Comunify learnings origen:
  - `comunify/docs/learnings/2026-05-18-tailwind-v4-postcss-wiring-gap.md`
  - `comunify/docs/learnings/2026-05-17-playwright-runner-parity-gap.md`
  - `comunify/docs/learnings/(pending)-camino-b-design-system-a11y.md` (write pendiente /pm-comunify)
- INDEX consolidado: `comunify/docs/learnings/INDEX-promotables.md`
- Scaffold target: `.claude/skills/_pm-brand-template/SKILL.md`
- Sister outcome: `docs/product/outcomes/linux-live-verification-replacement.md`
