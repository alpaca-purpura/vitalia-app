---
story_id: vitalia-fase2-lisa-landing-public
type: ui-story
agent_owner: null
module: landing
capability: lisa.landing_public
state: idea
architecture_pattern: ADR-vitalia-004
created: 2026-06-11T00:00:00Z
priority: medium
estimated_dev_days: 2-3
dependencies:
  hard: []
  soft: []
blocks_hard: []
blocks_soft: []
release: F3
cap_target: lisa.landing_public
parent_story: null
---
# vitalia-fase2-lisa-landing-public — idea

**Goal:** Landing pública (sin autenticación) — describe servicios clínica, galería, testimonios, reserva intro.

**Scope candidato:** Hero section · servicios grid · before/after carousel · testimonios cards · CTA reserva.

**Constraints:** No PHI (público) · responsive mobile-first · página SEO-friendly · ENFORCE-CHECKLIST.md · Spanish neutro LatAm.

**Next action:** Chris ratifica patrón → `/po-ux` refina spec + mockups.

## Nota 2026-06-11 (/po-ux · corrección Chris ronda 3)

La página pública del DOCTOR ya NO vive acá — Chris la movió a `vitalia-fase2-lisa-doctores` (§ D3-D del spec): "la landing de la clínica de momento está parkeada, no sé si irá o no, pero lo del doctor es diferente". Esta story queda SOLO con la landing de la clínica (estado real: idea/parked-ish, decisión pendiente).
