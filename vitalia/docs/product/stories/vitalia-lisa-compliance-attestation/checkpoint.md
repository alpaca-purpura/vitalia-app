---
story_id: vitalia-lisa-compliance-attestation
type: ui-story
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: compliance
capability: lisa.compliance-attestation
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: '2026-06-07T03:20:00.000Z'
ratified_by_chris: false
parallel_safe: true
priority: medium
release: F3
cap_target: lisa.compliance-attestation
cap_change_type: null
parent_story: vitalia-fase2-lisa-compliance
spawned_at: 2026-06-07
spawned_from: vitalia-fase2-lisa-compliance
next_action: "/pm-vitalia refinar cuando lisa-compliance esté done (provee la base de datos de confianza que el PDF snapshotea)"
---

# vitalia-lisa-compliance-attestation — checkpoint

> Spin-out de `vitalia-fase2-lisa-compliance` (decisión Chris 2026-06-07, batch 1 Q4: diferir attestation a story propia).

## Goal

**Attestation de compliance** generable por el dueño: un **PDF/documento** que snapshotea la postura de cumplimiento HIPAA-lite de la clínica (controles defensivos activos + consentimientos al día + metadata del tenant + timestamp + disclaimer) para mostrar a **pacientes** (confianza) o **auditores** (evidencia).

Es el artefacto "para afuera" que complementa la vista interna `lisa.compliance` ("Confianza y cumplimiento").

## Por qué story aparte

- La vista de confianza (`lisa-compliance`) es read-mostly + accionable interna; el attestation es **generación de documento** (worker background, PDF render, plantilla legal) — naturaleza técnica distinta + scope propio.
- No bloquea el MVP de la vista de confianza. Se construye encima cuando esa base exista.

## Scope (draft · refinar con /po-ux cuando arranque)

- Botón "Generar attestation" en `lisa/compliance` → worker background → PDF.
- Contenido: snapshot postura (controles activos), resumen consentimientos (N firmados/total), metadata tenant (razón social, clínicas), timestamp, disclaimer HIPAA-lite ("NO certificación HIPAA US").
- Historial de attestations generados + descarga (TTL).
- PHI-safe (sin diagnósticos/datos de paciente en el documento).

## Dependencias

- **Hard:** `vitalia-fase2-lisa-compliance` (provee la data de confianza + la ruta donde vive el botón).

## Anti-objetivos

- NO claim de certificación HIPAA US (es attestation defensiva interna).
- NO incluir PHI de pacientes en el documento.

## Referencias

- Story madre: `vitalia/docs/product/stories/vitalia-fase2-lisa-compliance/`
- HIPAA-lite: `vitalia/.claude/rules/hipaa-lite.md`
