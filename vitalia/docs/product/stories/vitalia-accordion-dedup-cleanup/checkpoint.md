---
story_id: vitalia-accordion-dedup-cleanup
type: bugfix
agent_owner: lisa
map_zone: agentes
map_box: lisa
map_area: servicios
module: offer
capability: lisa.servicios
architecture_pattern: ADR-vitalia-004
state: idea
ratified_by_chris: false
parallel_safe: true
priority: low
cap_target: lisa.servicios
cap_change_type: fix
parent_story: vitalia-fase2-lisa-servicios
spawned_at: '2026-06-19T00:00:00.000-05:00'
spawned_from: vitalia-fase2-lisa-servicios   # G round deferred ledger
last_modified: 2026-06-19
defer_audit: true              # HB-79 spawned deferred · ledger-stage only (state:idea) · auditor ratifies post-parent-merge
repro_evidence:
  repro_verified: false   # capturar al refinar (bugfix → repro-first)
next_action: "Refinar con /pm-vitalia → /po-ux (bugfix · repro-first). Capturar repro del duplicado de acordeones en el workspace."
---

# vitalia-accordion-dedup-cleanup — dedup de acordeones del workspace de servicio

## Origen (deferred de lisa-servicios · G round)

Spawneada en la Fase R de `vitalia-fase2-lisa-servicios` (2026-06-19). Citada en la nota `reconciled`
original + `RECONCILE-HANDOFF §7`. Cleanup de UI del workspace (los grupos colapsables / acordeones
del Resumen quedaron con duplicación tras los refits de G round 1+2).

## Goal (a refinar · bugfix lite · repro-first)

- Deduplicar los acordeones/grupos colapsables del workspace del servicio (Resumen + leaves).
- Sin diseño nuevo — limpieza estructural sobre lo ya ratificado (mockups firmados de lisa-servicios).

## Anti-objetivos
- NO rediseñar el workspace (los mockups están firmados).
- NO tocar contrato BE.

## Referencias
- Madre: `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/` (workspace 5 leaves + CollapsibleSection @luana/ui-kit)
- Componente: `vitalia/frontend/src/features/lisa/components/servicios/ServicioWorkspaceShell.tsx` + `leaves/ResumenView.tsx`
