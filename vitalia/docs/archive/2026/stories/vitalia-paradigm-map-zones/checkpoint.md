---
story_id: vitalia-paradigm-map-zones
brand: vitalia
type: infra-migration
title: "Migración del mapa a 3 zonas (PARADIGM/ADR-010) + reorganización del backlog"
agent_owner: infra
module: platform
state: done
architecture_pattern: ADR-010-orquestacion-agentica + ADR-vitalia-005-capability-model-4-dimensions (extiende → 5ª dim: zona)
last_modified: 2026-05-30
ratified_by_chris: true
ratified_at: 2026-05-30
spec_ratified_by_chris: true
mockup_gate_waived: true
mockup_gate_waived_by: chris
ready_package_closed_by: architect
ready_package_closed_at: 2026-05-30
autonomous_mode: true
autonomous_mode_authorized_by: chris
autonomous_mode_authorized_at: 2026-05-30
autonomous_mode_note: "Chris autorizó 'continua autonoma hasta el done' (2026-05-30) — override del default false del architect. Chain: /dev-team T-1..T-6 → /auditor → /pm-vitalia merge."
ready_package_artifacts: [03-arch.md, 03-arch-be.md, 03-arch-fe.md, 04-validators.yaml, 05-guidelines.md, 06-tickets.yaml, dispatch-plan.md]
mockup_gate_waived_reason: "Realineación Ribbon (5 tabs Lisa·Mateo·Adrián·Lucas·Camila + Plataforma; Valeria→sidebar). Sin componente nuevo → cambio mínimo. Chris ratificó skip ADR-vitalia-003 (2026-05-30)."
parallel_safe: false        # toca SYSTEM-MAP + ~71 caps + cockpit (cross-brand tool) — serializar
priority: high
estimated_dev_days: 3-4
dependencies:
  hard: []
  soft:
    - vitalia-fase2-lisa-doctores      # refining — comparte taxonomía a re-mapear
release: F2
cap_target: platform.product-map-zonas
cap_change_type: new
parent_story: null

# ── Decisiones ratificadas Chris 2026-05-30 ──
ratified_decisions:
  d1_valeria_mateo: "Valeria=supervisora (chat sidebar, NO caja de valor) + Mateo=Operar/Mi Día (agenda+bookings). Zona Agentes = 5 especialistas: Lisa·Mateo·Adrián·Lucas·Camila."
  d2_valeria_pacientes: "Split: 'pacientes del día' → Mateo (operativo) · 'historial médico' (config.patients-records) → Configuración/clínico."
  d3_lisa_compliance: "Vista compliance al cliente → Plataforma·configuracion (user-facing) · enforcement técnico (cifrado/audit/dual-filter) → Infraestructura·seguridad-cumplimiento."
  d4_naming: "Renombrar stories config-* a su caja nueva (coherencia), no solo re-tag."
  d5_cockpit: "F3 cockpit MapView misma tanda, tool-scope cross-brand (fase solo-bootstrap) · F4 índice de acciones puede diferir a story propia."

# ── Paradigma (caja/zona del mapa · cement 2026-05-30) ──
map_zone: infraestructura
map_box: plataforma-tecnica
user_visible: false
paradigm_refs:
  - docs/architecture/luana-platform/PARADIGM.md
  - docs/architecture/luana-platform/ADR-010-orquestacion-agentica.md
  - .claude/rules/paradigm-arquitectura.md
  - vitalia/docs/architecture/SYSTEM-MAP.yaml (zones)

# ── Scope (4 frentes) ──
scope:
  - "F1 · Re-tag ~71 caps: agent_owner config/infra → cajas nuevas por zona (SYSTEM-MAP.zones.target_boxes.absorbs)"
  - "F2 · Reasignar Valeria→supervisora (chat sidebar, no caja de valor) + Mateo→Operar/Mi Día (agenda+bookings)"
  - "F3 · Cockpit MapView.tsx: render por zona + lentes trabajadores/proceso (★ cross-brand TOOL — scope tools/, no producto vitalia)"
  - "F4 · Índice de acciones (Plano 2) generado del service layer (navegación agéntica sin grep) — diseño, posible diferir"
  - "F0 · Re-mapear backlog Fase 2 (~20 idea-stories) a las cajas/zonas nuevas (renombrar/re-tag)"

scope_boundary_note: >
  F3 (cockpit MapView) vive en tools/luana-cockpit/ = herramienta operativa CROSS-BRAND, NO producto vitalia.
  /pm-vitalia NO la owna. Se ejecuta en la misma tanda (fase solo-bootstrap permite) pero se trackea como
  tool-scope, no como cap de producto vitalia. La parte vitalia-propia es F0+F1+F2 (data: caps + SYSTEM-MAP + reassign).

next_action: "T-1 DONE · T-2 DONE · T-3 DONE · T-4 DONE (rename backlog Fase 2 + map_box en 22 checkpoints). Pendiente: T-5 (FE shell realign) + T-6 (e2e tests) → luego /auditor → /pm-vitalia merge."
---

# vitalia-paradigm-map-zones

Story infra que **materializa el paradigma** (PARADIGM.md + ADR-010, cementados 2026-05-30) en el mapa del producto: migra de la taxonomía de 2 pseudo-agentes (`config`/`infra`) a **3 zonas** (Agentes · Plataforma · Infraestructura), reorganiza el backlog Fase 2 acorde, y prepara el cockpit para renderizar por zona.

Propuesta de organización completa + re-mapeo del backlog: ver `00-research.md`.

## Prior art scan

- **Engine:** N/A (el cockpit es tool operativa cross-brand, no engine package).
- **Vitalia propio:** `ADR-vitalia-005-capability-model-4-dimensions.md` (define las 4 dims actuales — esta story agrega la 5ª: zona, derivada) · `SYSTEM-MAP.yaml` (ya tiene el bloque `zones` draft 2026-05-30) · archive `vitalia-cockpit-live-reconciliation` (patrón cockpit lee filesystem) · archive `vitalia-shell-organism` (Ribbon + Valeria sidebar — informa el rol supervisor).
- **Comunify:** sin taxonomía de mapa propia aún (no aplica).
- **Decisión:** **extend** del modelo de capability (ADR-vitalia-005) + **new** cap infra `platform.product-map-zonas`. NO net-new from scratch — la doctrina ya está en PARADIGM.md/ADR-010; esto la aplica a los datos + tool.
