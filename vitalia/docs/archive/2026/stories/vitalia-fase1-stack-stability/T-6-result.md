---
ticket: T-6
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: pushed
validator_ids: [val-t6-adr-exists, val-t6-8-sections]
---

# T-6 — ADR-vitalia-002 vt-deprecation-plan — Result

## Deliverables

### ADR-vitalia-002-vt-deprecation-plan.md
- Path: `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md`
- Status: accepted
- Magic comment: `<!-- voseo-allowed: internal architecture documentation -->`

### 8 sections
1. § 1 Contexto — por qué .vt-* existen + problema deuda técnica + alineación Shadcn
2. § 2 Inventario .vt-* — scan globals.css ~42 clases categorizadas
3. § 3 Estrategia compatibility temporal — coexistencia + mapping table vitalia→shadcn
4. § 4 Migration policy progresiva — regla forward-only + proceso por story
5. § 5 Final drop — story vitalia-fase2-vt-deprecation-final + decisión diferida --vitalia-* vars
6. § 6 Arch fitness test enforcement — ratchet test + eslint futuro
7. § 7 Post-install audit checklist supply-chain — diff vs oficial + 8 primitivos auditados F1-S0
8. § 8 Riesgos + mitigaciones — 8 riesgos con probabilidad/impacto/mitigación

## Validators

| Validator | Status |
|---|---|
| val-t6-adr-exists | PASS — file at vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md |
| val-t6-8-sections | PASS — 8 sections §1..§8 present with required content |
