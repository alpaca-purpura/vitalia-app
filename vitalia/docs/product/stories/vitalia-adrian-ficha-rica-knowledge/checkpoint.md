---
story_id: vitalia-adrian-ficha-rica-knowledge
type: ui-story
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
priority: medium
cap_target: lisa.servicios
cap_change_type: extend
parent_story: vitalia-fase2-lisa-servicios
spawned_at: '2026-06-19T00:00:00.000-05:00'
spawned_from: vitalia-fase2-lisa-servicios   # G round deferred ledger
last_modified: 2026-06-19
defer_audit: true              # HB-79 spawned deferred · ledger-stage only (state:idea) · auditor ratifies post-parent-merge
next_action: "Refinar con /pm-vitalia → /po-ux. Intake-handshake: zona/caja + extiende-o-nuevo + prior-art (§ Modelo de conocimiento del servicio del 01-spec de lisa-servicios)."
---

# vitalia-adrian-ficha-rica-knowledge — modelo de conocimiento del servicio para Adrián

## Origen (deferred de lisa-servicios · G round)

Spawneada en la Fase R de `vitalia-fase2-lisa-servicios` (2026-06-19). Citada en la nota `reconciled`
original + `RECONCILE-HANDOFF §7`. La ficha rica (Resumen: cómo se hace, riesgos, cuidados, resultados,
etc.) ya es editable + persiste; falta el **modelo de conocimiento** que Chris pidió ("el form es muy
pesado, que el sistema agéntico facilite" · ver `01-spec.md § Modelo de conocimiento del servicio`).

## Goal (a refinar)

- Que cargar la ficha rica sea asistido (autocompletar/sugerir desde la voz de marca + documentos),
  no un formulario pesado manual.
- Estructurar el conocimiento de modo que Adrián lo cite limpio (capa curada, no texto libre).
- Distinto de Sub-phase B RAG (eso es runtime indexer/retrieval engine-lift /pm-vitalia). Esta story =
  la **capa estructurada brand-local** del conocimiento del servicio.

## Anti-objetivos (preliminar)
- NO RAG runtime (Qdrant indexer + tool retrieval) → Sub-phase B `/pm-vitalia` (STOP-2).
- NO tocar engine offer-studio.

## Referencias
- Spec madre: `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/01-spec.md § Modelo de conocimiento del servicio` + `§ Recomendación #9 — documentos → RAG`
- Cap: `vitalia/docs/product/capabilities/offer/lisa-servicios.yaml`
