---
brand: vitalia
date: 2026-05-21
slug: auto-handoff-deferred-e2e-blocker
promotable: yes
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: docs/process/ (process layer, no engine package)
severity: HIGH
origin_story: vitalia-slice-1-marketing
origin_commit: fa921711 (squash-merge to main 2026-05-21)
---

# Auto-handoff con E2E deferred = integration bugs slip past audit

## Qué aprendimos

Cuando `/dev-team` cierra `state: developed` con E2E validators `DEFERRED CI` (motivo legítimo: stack infra inestable, missing tokens, etc.), la cadena auto-handoff `dev-team → auditor → pm-{brand} merge` actualmente acepta el DEFERRED como WARN no-blocker y procede al merge.

**Pero el DEFERRED de un E2E suite es el ÚNICO gate verdadero de integración** — unit tests + arch fitness + Gherkin scenario coverage NO atrapan estos bugs porque cada uno verifica un slice aislado:

| Gate | Qué verifica | Qué NO verifica |
|---|---|---|
| Unit tests | Función/componente individual | Integración con app real |
| Arch fitness | Boundaries DDD/FSD | Que la nav real linkee al route |
| Gherkin coverage | Scenario → test path mapping | Que el browser real renderice |
| Vitest snapshot | DOM tree per componente | Tailwind tokens aplicados en runtime |
| Playwright unit-level | Componente en harness aislado | App shell + sidebar + tema integrados |
| **E2E smoke (live)** | **Stack completo end-to-end** | (este es el único que cierra el loop) |

## Caso origen — vitalia-slice-1-marketing (2026-05-21)

Story shipped state=done con merge `fa921711` a main. Audit cycle 3 iter APPROVED. CHECKPOINTS.md C1-C5 GREEN.

**Pero al navegar al app real:**
- `app/marketing/page.tsx` existe ✓
- Sidebar nav `Sidebar.tsx` NO incluye link a Marketing ✗
- Home dashboard `SliceOneStubsRow.tsx` sigue mostrando "Marketing·pronto" placeholder ✗
- Tailwind v4 tokens NO renderizan en runtime (HTML sin estilo) ✗

User no puede LLEGAR al `/marketing` porque la sidebar no lo linkea. La story es funcionalmente invisible.

**Root cause:** 13 tickets del ready package describieron componentes + route + tests pero **NUNCA enumeraron explicitamente "update Sidebar.tsx nav items" ni "remove MarketingStub de SliceOneStubsRow"**. Builders ejecutaron exactly what was specified. Auditor verificó tests + arch fitness — pero E2E smoke spec marketing quedó DEFERRED CI por Turbopack stack instability (learning 2026-05-20).

Yo (orchestrator Opus) acepté el DEFERRED como non-blocker WARN y cerré el merge. **Decisión incorrecta:** debí STOP en `developed` y exigir manual visual verification antes de pasar a `reviewing/done`.

## Why: la cadena confía en gates indirectos cuando el directo está caído

La cadena auto-handoff cementada 2026-05-18 (`story-closure-gate.md`) asume implícitamente que **al menos UN gate verdadero de integración corre en cada merge**. En la práctica:

- Si E2E pasa → integración verificada ✓
- Si E2E DEFERRED + manual visual verification → integración verificada ✓
- Si E2E DEFERRED + no manual verify → **integración NO verificada, pero el merge procede igual** ✗

El paradigm v4 no contempla este caso porque el cap implícito era "deferred = excepción rara documentada con razón". En Vitalia llevamos 2 stories consecutivas con E2E deferred (copilot-tools-impl 2026-05-18 + marketing 2026-05-21) — la excepción se volvió la regla y el gate de integración nunca corrió.

## How to apply

**Hard rule propuesta (forward-only post 2026-05-21):**

> Si `T-{n}-result.md` o `T-{n}-review.md` marca CUALQUIER validator de categoría `visual` o `e2e_smoke` como DEFERRED, la cadena auto-handoff `developed → reviewing → done` NO procede automáticamente.
>
> El orchestrator (Opus) DEBE:
> 1. Pausar en `developed`
> 2. Emitir ping explícito a Chris: "story X tiene N deferred E2E/visual validators — ratifica manual visual verification o reabro como `state: changes-requested`"
> 3. Si Chris ratifica visual verification manual → orchestrator levanta stack, navega manualmente, captura screenshot, anexa a `06-audit/manual-verification.md` ANTES de proceder
> 4. Si Chris dice "skip, mergeá igual" → marca learning con `severity: HIGH, deferred_verification_accepted_by: chris, risk: integration_bugs_possible`

**Update donde:**

- `.claude/rules/story-closure-gate.md` § Layer 1-3 — agregar Layer 8 (deferred-e2e gate)
- `.claude/skills/dev-team/SKILL.md` Step 4.5 Phase D — verificar deferred count, si > 0 → no auto-handoff
- `.claude/skills/auditor/SKILL.md` Step 4 CHECKPOINTS.md template — agregar checkbox C2 "manual visual verification ran post-deferred E2E"
- `docs/process/pm-redesign-2026-05.md` § Conv 3 — actualizar "auto-handoff default" con caveat deferred-e2e

**Casos donde NO aplica el gate strict:**

- Service-only stories (no UI) — N/A
- Pure refactor (functional unchanged, regression covered) — N/A
- Hot-fix tickets con `repro_verified: true` — el repro test ya es el gate
- Stories cuyo único deferred es Chromatic (visual regression solo, sin functional impact) — el visual diff queda como WARN aceptable

## Cross-brand applicability

Este gap se reproduce inevitablemente cualquier brand que:
1. Use Next.js + Turbopack en dev (mismo stack que Vitalia → comunify, lupulo, nicolify ya activas; saasora/inmoflow/retailly/fixia/guestly/fitflow al bootstrapearse)
2. Tenga sidebar/nav centralizada que requiera updates explícitos al agregar rutas
3. Acepte E2E deferred como WARN

→ Promotable cross-brand al process layer (`docs/process/`), no a engine package.

## Action items inmediatos (vitalia)

1. ✓ Este learning escrito 2026-05-21 (promotable: yes)
2. Story follow-up `vitalia-slice-1-marketing-integration` creada (3 gaps trivial fixes + manual visual verification)
3. Ping `/pm-luana` para evaluación lift cross-brand del nuevo gate process rule
4. Update `docs/process/story-closure-gate.md` propose Layer 8 (orchestrator pause si deferred e2e/visual)

## Referencias

- Caso origen: `vitalia/docs/archive/2026/stories/vitalia-slice-1-marketing/` (29 commits merged fa921711)
- Learning previo relacionado: `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md` (la causa de los E2E DEFERRED)
- Process SSoT actual: `.claude/rules/story-closure-gate.md` (no contempla este caso)
- Paradigm v4.1: `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` (auto-handoff cementado, sin caveat deferred)
