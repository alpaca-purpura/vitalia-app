---
story_id: vitalia-pricing-decision
state: idea
last_artifact: checkpoint.md
last_modified: 2026-05-17
next_action: "Chris dispara sesión dedicada para definir tier model + precios concretos USD. Análisis competitivo de pricing en vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md § Matriz comparativa funcional (Rendu CLP $40-250k, Doctocliq USD $19+, BotClín no público). Cuando ratificado → update vitalia/config/brand.yaml::plan_tiers + cleanup TBDs en specs."
ratified_by_chris: false
spawned_at: 2026-05-17
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: "★ TIER reclassified 2026-05-27 (audit sweep): TIER 7 DEFERRED (post-MVP maturity). MVP hardcodea pricing placeholder vitalia/config/brand.yaml (solo_doctor 49 USD · clinic 199 USD · multi_site 599 USD). Full pricing engine (cost basis, markup per vertical, tax rules per country, multi-currency rates) se cementa en Fase 3 multi-vertical mature O cuando primer cliente paying pide dynamic pricing. Chris no necesita decidir pricing definitivo HOY — los placeholders son válidos para MVP internal validation. SSoT orden: vitalia/docs/product/outcomes/vitalia-fase-2-tier-roadmap.md § TIER 7."
priority: medium
estimated_dev_weeks: 0 (decision-only, no FE/BE code)

# Schema v2 migration (cement 2026-05-27)
release: F8   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-pricing-decision — checkpoint

## Goal

Definir tier model + precios concretos para Vitalia plan tiers (Starter / Pro / Enterprise) en USD.

Hoy `vitalia/config/brand.yaml` tiene precios placeholders del bootstrap Story 11 (`solo_doctor 49 USD · clinic 199 USD · multi_site 599 USD`) que Chris no ratificó como definitivos. Esta story ratifica oficialmente.

## Scope

### In-scope
- Tier model: ¿3 tiers? ¿2 tiers? ¿pricing variable per vertical?
- Precios USD por tier (en monthly + annual discount opcional)
- Mapping tiers ↔ personas (Plan Starter = P2 solo / Plan Pro = P1+P2 separados / Plan Enterprise = + features)
- Features per tier (qué tiene/no tiene cada plan)
- Free tier? Trial? Demo?
- Update `vitalia/config/brand.yaml::plan_tiers`
- Cleanup TBDs en `vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md` (3 ocurrencias actuales)

### Out-of-scope
- Implementación pantalla /plan-billing (eso es Slice 2 FE)
- Stripe integration (separada — billing engine luana-core-billing)
- Promo codes / discounts dinámicos (Slice 3+)

## Análisis input

Ver `vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md` § Context → tabla comparativa:
- **Rendu** (Chile dental): CLP $40k-$250k/mes (~USD $40-260)
- **Doctocliq** (LATAM dental/médico): USD $19+/mes, free tier 30 pacientes
- **BotClínico/Dentalink CC/Cero.ai**: no publican precios

## Dependencies

- Ninguna. Chris puede ratificar pricing en sesión independiente.

## Bitácora

- 2026-05-17 spawned: idea formal abierta por /pm-vitalia tras decisión Chris de postergar precios en sesión UX. NO bloquea Slice 1 (esa no toca pricing); SÍ bloquea Slice 2 (`/configuracion` + `/tratamientos` muestran tier model).
