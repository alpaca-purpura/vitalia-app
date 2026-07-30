---
story_id: vitalia-fase2-camila-multiplicar
type: ui-story
agent_owner: camila
module: campaigns
capability: camila.multiplicar
state: idea
architecture_pattern: ADR-vitalia-004
created: 2026-06-11T00:00:00Z
priority: high
estimated_dev_days: 4-5
dependencies:
  hard: []
  soft: []
blocks_hard: []
blocks_soft: []
release: F3
cap_target: camila.multiplicar
parent_story: null
---
# vitalia-fase2-camila-multiplicar — idea

**Goal:** Vista especialista Camila (Retener) — crear + gestionar campañas de re-engagement multipaquete.

**Scope candidato:** Form autosave (patrón Group + use-autosave 600ms) · parámetros de campaña · segmentación pacientes · scheduling.

**Constraints:** CONSUME campaigns.engine · autosave debounce 600ms + FloatingAutosaveIndicator · ENFORCE-CHECKLIST.md · Spanish neutro LatAm.

**Next action:** Chris ratifica patrón → `/po-ux` refina spec + mockups.
