---
brand: vitalia
date: 2026-05-16
slug: capabilities-inventory-gap
promotable: yes
promotion_proposal: docs/promotion-protocol/proposals/2026-05-16-capability-inventory-enforcement.md
promotion_state: accepted
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, vitalia]
target_core_package: scripts/ (process tooling, no core engine package)
---

# Capability promotion step omitted at Story 11 merge

**Qué aprendimos:** El merge de Story 11 (`luana-vitalia-bootstrap` 2026-05-15) shipped 16 capabilities reales pero NO ejecutó el paso 2 del capability promotion descrito en `.claude/skills/pm-vitalia/SKILL.md` (escribir `vitalia/docs/product/capabilities/{module}/{cap}.yaml`). El BACKLOG quedó vacío y la SSoT funcional desincronizada del código por 1 día.

Recuperado 2026-05-16 con inventory manual desde:
- 8 capabilities archivadas en `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/capabilities/vitalia/` (Story 11 SSoT pre-reorg)
- Inspección de código vivo (76 endpoints + 25 FE hooks + 21 components + 86 BE tests + 24 E2E smokes + 22 FE unit/integration)
- Diff vs `vitalia/.claude/rules/hipaa-lite.md` (aspirational vs shipped)

**Origen:** chequeo de estado por Chris vía `/pm-vitalia "tenemos frontend con nuestra marca? qué funcionalidades?"` 2026-05-16

**Why:** El SKILL.md describe el capability promotion como paso obligatorio del `07-merge.md`, pero no hay enforcement automático. Story 11 mergeó pre-multibrand reorg, y la migración del SSoT funcional desde `docs/` raíz a `vitalia/docs/` no completó este paso. Sin capability YAMLs, la pregunta "qué tenemos" sólo se contesta leyendo código + rules + archive.

**How to apply:**
- Cada `/pm-{brand}` MUST verificar al merge que existan capability YAMLs por cada feature shipped (no solo modules.md update)
- Pre-commit hook `scripts/reconcile_capabilities.py --brand X --check` ya existe pero no enforza creación (solo drift de status). Considerar extender para enforzar que outcome→story→capability tenga al menos 1 YAML mapping post-merge
- Bootstrap brands futuras (saasora/inmoflow/retailly/fixia/guestly/fitflow): incluir capability inventory en checklist de bootstrap pattern (CLAUDE.md "Bootstrap pattern para brand nueva")
- Audit cross-brand: `comunify` (Story 12 shipped) y `nicolify` (production) pueden tener mismo gap — verificar `comunify/docs/product/capabilities/` y `nicolify/docs/product/capabilities/`

**Cross-brand candidacy:** este gap aplica a CUALQUIER brand que mergee outcomes sin enforcement. Promote a `/pm-luana` para evaluar:
1. Extender `reconcile_capabilities.py` con `--require-capabilities-exist`
2. Agregar paso explícito al `_pm-brand-template/SKILL.md` para que brands futuras hereden el chequeo
3. Documentar como anti-pattern en `docs/process/learnings.md` cross-brand
