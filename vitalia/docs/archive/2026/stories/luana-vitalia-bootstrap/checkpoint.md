---
story_id: luana-vitalia-bootstrap
type: tech

release: F0

cap_target: null
cap_change_type: new
parent_story: null

state: done
phase_workflow: MERGE
last_artifact: checkpoint.md
last_modified: 2026-05-30T20:10:00-05:00
next_action: "n/a — story histórica cerrada (registro retroactivo de trazabilidad)"
ratified_by_chris: true
spawned_at: 2026-05-15T00:00:00-05:00
spawned_by: bootstrap
parallel_safe: true
blocked_reason: null
audit_iterations: 0
defer_audit: false
defer_audit_reason: null
parked_reason: null
dropped_reason: null

# Stub retroactivo · creado 2026-05-30 para cerrar gap de trazabilidad
# (reconcile_capabilities.py: live cap created_in_story → checkpoint real)
retroactive_stub: true
---

# luana-vitalia-bootstrap — Bootstrap de la marca Vitalia (registro retroactivo)

> **Stub retroactivo de trazabilidad** creado 2026-05-30. NO es una story que se haya
> ejecutado vía el pipeline SDD normal (idea→…→done). Documenta, después de hecho, el
> **bootstrap original de la marca Vitalia** (2026-05-15, durante el reorg multibrand) que
> shippeó el primer lote de capabilities directamente, sin una carpeta de story.
>
> **Por qué existe este archivo:** `scripts/reconcile_capabilities.py` exige que toda cap
> `live`/`beta` trace (`created_in_story`/`story_introduced`) a un `checkpoint.md` real
> (activo o archivado). 16 caps apuntan a `luana-vitalia-bootstrap`, que no tenía carpeta →
> WARN advisory `live_created_in_story_unresolved`. Este stub provee el destino de la traza
> sin falsear historia (re-apuntar las caps a otra story sería incorrecto: salieron del
> bootstrap).

## Qué fue el bootstrap

`date_introduced: 2026-05-15`. Scaffolding inicial de la marca Vitalia (Salud + Bienestar,
HIPAA-lite) durante el reorg multibrand — pattern de bootstrap de brand nueva
(`_pm-brand-template`, análogo a Story 11/12). Estableció módulos + caps base del vertical
médico antes de que el pipeline SDD per-story estuviera en uso pleno para la marca.

## Capabilities trazadas a esta story (16)

| status | cap |
|---|---|
| live | `public_landing/public-clinic-landing` |
| deprecated | `agentic/medical-agentic-tools` · `agentic/medical-safety-guardrails` · `booking/booking-widget-embed` · `booking/prepaid-booking-advisory-locks` · `brand_studio/brand-studio-medical-sections` · `compliance/compliance-hipaa-lite-audit` · `copilot/medical-kb-rag` · `onboarding/clinic-onboarding-3step` · `payment/payment-gateways-latam-recurring` · `treatments/treatment-followup-workflow` |
| planned | `copilot/medical-pdf-extractors` · `fixtures/3-clinic-fixture-latam` · `offer_studio/medical-services-offer-preset` · `patients/patient-records-medical-history` · `platform/vertical-medical-extension-sdk` |

(Las `deprecated` quedaron superseded por stories posteriores reales; las `planned` son
forward-declared. Solo la `live` disparaba el WARN; este stub resuelve la traza de las 16.)

## Notas

- Stub mínimo: solo `checkpoint.md` (lo que el validador necesita). No hay spec/arch/tickets
  porque la story nunca corrió el pipeline — es registro histórico.
- Prevención futura: el `_pm-brand-template` / bootstrap de marcas nuevas debería crear un
  stub de story archivada equivalente al shippear el primer lote de caps (evita re-introducir
  este gap en comunify/nicolify/lupulo/futuras).
