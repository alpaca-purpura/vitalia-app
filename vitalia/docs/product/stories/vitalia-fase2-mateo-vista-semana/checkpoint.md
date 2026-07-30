---
story_id: vitalia-fase2-mateo-vista-semana
type: ui-story
agent_owner: mateo
module: scheduling
capability: mateo.agenda
state: refining                                  # ⤺ /pm-vitalia 2026-06-27: Chris eligió refinar esta (UI chica). Handoff /po-ux.
architecture_pattern: ADR-vitalia-004
created: 2026-06-21T00:00:00Z
priority: medium
estimated_dev_days: 2-3
dependencies:
  hard: []
  soft: [vitalia-scheduling-mateo-review]      # nace de su live-QA (D12)
blocks_hard: []
blocks_soft: []
release: F2
cap_target: scheduling.mateo-agenda
cap_change_type: extend                          # rediseña la vista Semana de la cap agenda
parent_story: null

# Zona/caja del mapa (paradigm-arquitectura · derivada de SYSTEM-MAP.yaml)
zone: agentes
box: mateo
functional_area: mateo.agenda
---

# vitalia-fase2-mateo-vista-semana — refining

**Origen:** D12 de la live-QA `vitalia-scheduling-mateo-review` (2026-06-21). La vista "Semana" es columnas/tarjetas por día sin eje horario, sin leyenda de colores, sin resumen del día.

**Goal:** Rediseñar la grilla de la vista "Semana" para que sea legible de un vistazo.

**Scope candidato:**
- Eje horario a la izquierda (hoy la hora vive dentro de cada tarjeta).
- Leyenda de colores (estados de pago: pagado/depósito/sin-pago/no-show).
- Resumen del día (conteos por columna).
- Porta el wrapper del shell verbatim (Ribbon + SubTabs + ValeriaSidebar) — owna SOLO el `panel-content`.

**Constraints:** CONSUME scheduling (mismo data de la grilla, ya fixed en el bugfix) · tokens de `globals.css` · ENFORCE-CHECKLIST · Spanish neutro LatAm · NO toca core ni otras marcas.

**Next action:** `/po-ux` refina (01-spec unificado: Gherkin + mockup vía Storybook `@luana/ui-kit` + estados visuales + microcopy neutro) → Chris ratifica → `refined` → `/architect`.
