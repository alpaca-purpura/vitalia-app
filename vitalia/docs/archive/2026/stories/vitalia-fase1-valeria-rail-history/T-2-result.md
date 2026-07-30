# T-2 Result — _mock-conversations data + MockConversation type

**Ticket:** T-2 of vitalia-fase1-valeria-rail-history (F1-S5)
**Commit:** d52292a0
**Branch:** wip/vitalia
**State transition:** ready → pushed

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite naming + `_mock-*` prefix convention for mock data modules | `_mock-conversations.ts` prefix confirmed — underscore prefix marks file as non-production dev fixture. Located in `components/shared/shell-organism/` per spec. No barrel export needed (internal use by ValeriaHistory T-4). |
| `brand-expert` | Checked if `MockConversation` type could conflict with brand-studio BuyerPersona or offer shapes | No overlap — `MockConversation` is shell-organism UI-only, zero semantic relation to brand/offer domain models. |
| `offer-expert` | Rule says invoke if touching offer-studio — not applicable here | Confirmed NOT touching offer-studio. Skipped (scope=N/A). |
| `copilot-expert` | Rule says invoke if touching copilot — not applicable here | Confirmed NOT touching copilot. Skipped (scope=N/A). |
| `tessl__react-patterns` | Always-on baseline | Pure data module — no components, no hooks. No error boundaries, loading states, or memoization needed. tsc + ESLint suffice as quality gates per ticket acceptance criteria. |
| `spanish-text.md` | 8 mock titles must be Spanish neutro LatAm (no voseo) | All 8 titles verified: "Resumen reseñas Google semana", "Ideas campaña Día de la Madre", "Reporte ocupación martes", "Borrador respuesta a reseña 3⭐", "Tutorial agenda online turnos", "Plan ofertas mes mayo", "Métricas conversión landing", "Revisar copy WhatsApp bienvenida" — tuteo form, no voseo imperative verbs, tildes/ñ/accents correct. |
| `anti-duplication.md` (cross-brand scan) | Pre-write mandatory grep | `grep -rln "_mock-conversations\|MockConversation\|MOCK_CONVERSATIONS" nicolify/frontend/src comunify/frontend/src lupulo/frontend/src` → 0 matches. NEW correctly (first brand consumer). |
| `hipaa-lite.md` (vitalia overlay) | PHI fields canonical list verification | Scope=N/A for F1-S5 per CONTEXT-BRIEF § 5 Rules table (UI chrome, demo data only, no real patient identifiers). Manual check: all 8 mock items contain operational business topics only — zero fields from PHI canonical list (`patient.name`, `diagnosis`, `treatment_plan`, `medication`, `dosage`, `allergies`, `symptoms`, `medical_notes`, `lab_results`, `imaging_url`, etc.). |

## Diff

**File created:** `vitalia/frontend/src/components/shared/shell-organism/_mock-conversations.ts`

- 61 lines total
- Exports: `MockConversation` (type) + `MOCK_CONVERSATIONS` (const array, 8 items)
- Groups: `today` (3 items), `yesterday` (2 items), `this_week` (3 items)
- No default exports (arch test gate)

## Validators

| Gate | Command | Result |
|---|---|---|
| tsc strict | `npx tsc --noEmit` | PASS (0 errors) |
| ESLint | `npx eslint src/components/shared/shell-organism/_mock-conversations.ts --cache` | PASS (0 errors, 0 warnings) |
| Prettier | `npx prettier --check src/components/shared/shell-organism/_mock-conversations.ts` | PASS ("All matched files use Prettier code style!") |
| HIPAA manual | Zero PHI fields verbatim canonical list cross-check | PASS (zero patient names, diagnoses, dosages, identifiers) |

## Ticket acceptance criteria

Per 06-tickets.yaml T-2:
- validator_ids: `val-fe-tsc` ✓ + `val-fe-lint` ✓
- note: "Pure data + types module — no dedicated test. Consumer types verify via T-3 (ValeriaRail no usa) y T-4 (ValeriaHistory consume) unit tests + tsc." → acknowledged, no test file created.
- gherkin_coverage SC-9: "cero PHI patterns en mock data" → satisfied (manual HIPAA check + will be verified by T-8 i18n-spanish-neutro.spec.ts)

## Notes

- T-2 is Wave 1 parallel (no deps). Completes independently before T-4 (ValeriaHistory) needs it.
- Consumer: `ValeriaHistory` (T-4) imports `MOCK_CONVERSATIONS` and `MockConversation` type.
- File will be deleted/replaced in Fase 2 when real API endpoint is wired.
- Cross-brand scan: 0 matches across nicolify/comunify/lupulo — NEW correctly per anti-duplication rule.
