---
story_id: vitalia-fase2-onboarding-clinica
type: ui-story
agent_owner: null
module: onboarding
capability: onboarding.clinica
state: idea
architecture_pattern: ADR-vitalia-004
created: 2026-06-11T00:00:00Z
priority: critical
estimated_dev_days: 5-6
dependencies:
  hard: []
  soft:
    - vitalia-fase2-config-cuenta
blocks_hard: []
blocks_soft: []
release: F3
cap_target: onboarding.clinica
parent_story: null
---
# vitalia-fase2-onboarding-clinica — idea

**Goal:** Flujo onboarding nuevo tenant (clínica) — captura datos esenciales, configuración inicial, signup completo.

**Scope candidato:** Multi-step form wizard (patrón RHF + Zod) · datos clínica · especialidades · usuarios admin · finalización.

**Constraints:** CONSUME iam · clinics · fiscal · autosave deshabilitado (wizard secuencial) · ENFORCE-CHECKLIST.md · Spanish neutro LatAm.

**Next action:** Chris ratifica patrón → `/po-ux` refina spec + mockups.
