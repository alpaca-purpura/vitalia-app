---
story_id: vitalia-fase2-mateo-pacientes
type: ui-story
agent_owner: mateo
module: crm
capability: mateo.pacientes
state: idea
architecture_pattern: ADR-vitalia-004
created: 2026-06-11T00:00:00Z
priority: high
estimated_dev_days: 3-4
dependencies:
  hard: []
  soft: []
blocks_hard: []
blocks_soft: []
release: F2
cap_target: mateo.pacientes
parent_story: null
---

# vitalia-fase2-mateo-pacientes — idea

**Goal:** Vista especialista Mateo (Operar) — directorio central de pacientes, búsqueda avanzada, historial clínico comprimido.

**Scope candidato:** N3 list/detail pacientes · EntityWorkspaceLayout con EntityInfoCard grid · búsqueda/filtro · quick-stats sidebar.

**Constraints:** CONSUME crm.patients · PHI dual filter + audit log · ENFORCE-CHECKLIST.md · Spanish neutro LatAm.

**Next action:** Chris ratifica patrón → `/po-ux` refina spec + mockups.
