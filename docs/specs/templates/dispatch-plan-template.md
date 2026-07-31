# dispatch-plan.md — Template (5º artefacto del ready package)

> Vive en: `{brand}/docs/product/stories/{story-id}/dispatch-plan.md`
> Owner: `/architect` (Step 7.5). Consumer: `/dev-team` Step 0.7.
> SSoT del schema: `.claude/rules/architect-autonomous-mode.md`.
> Cap ≤100 líneas. Reemplazá los placeholders `{...}`.

# Dispatch plan — Story {brand}/{story-id}

## autonomous_mode
- value: false                      # default. Chris opt-in explícito al ratificar ready
- chain_if_true: [/dev-team → /auditor → /pm-{brand} merge]
- caps: { max_iterations_per_ticket: 10, self_fix_iter: 5, audit_iterations: 4, max_total_cost_usd: 5.00, max_wall_clock_minutes: 90, on_cap_exceeded: "state=blocked + escalate Chris" }
  # self_fix_iter (Carril R · default fix-and-own ≤6 en v5), audit_iterations<=4 total — Auditor Responsable v5 (`.claude/rules/auditor-self-fix-policy.md`)

> Reglas HARD para `autonomous_mode: true` (ver architect-autonomous-mode.md):
> NUNCA true si — algún ticket AGENTIC `production_code: true` · toca `core/luana-core-*` · toca fuera de `vitalia/**`/`core/**` (out-of-scope) · validators con `pass_k` < 0.66 · hot-fix `repro_verified: false` · `defer_audit: true`.

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | primary_agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | {título} | BE | builder-backend | sonnet | ${x} | {n} min |
| T-2 | {título} | AGENTIC | builder-agentic | opus (R23) | ${x} | {n} min |
| T-3 | {título} | FE | builder-frontend | sonnet | ${x} | {n} min |
| **Total** | — | — | — | — | **${X}** | **~{N} min** |

## DAG dependencies
T-1 → T-2 → T-3   (citar el grafo real de `06-tickets.yaml` blocks/blocked_by)

## Playwright visual scope discipline (si ui-story)
- story_scope_routes: [{rutas donde aplicar cambios visuales}]
- story_scope_components: [{componentes en scope}]
- forbidden_visual_changes: [`{brand}/frontend/src/components/ui/`, `components/shared/`, `app/layout.tsx`]
- non_egoísmo: bug visible en feature/ruta NO tocada por esta story → reportar en `T-{n}-impl-log.md § Cross-story observed bugs`, NO arreglar inline.

## DoD live-verify gate (Critical Rule #37)

> Ref: `.claude/rules/definition-of-done-live-verify.md`

- Para toda story **funcional/user-reachable** (FE page, endpoint con consumer FE, flujo agentic):
  - `/dev-team` ejerce la acción real en `dev-app.{brand}lat.com` (o localhost:{port} fallback) via Chrome DevTools MCP antes de cerrar `developed`.
  - Registra `dod_live_verified: true` + `dod_evidence` (writes ejercidos + efecto observado + backend logs sin traceback) en `checkpoint.md`.
  - Gate anti-burbuja: specs importan `base.ts` (no `@playwright/test` directo); `pageerror`/`console[error]`/`response>=400` colectados en teardown.
  - Demo manual (`demo-script.md` 4 secciones) + el signoff de Chris en `checkpoint.md::chris_verify.signoff` (fase G · proceso v5) requerido si `demo_required: true`.
- Para stories **técnicas puras** (config/docs/migration-only/tooling sin endpoint ejecutable): `demo_required: false` + `demo_skip_reason` en checkpoint.
- `/pm-{brand}` REFUSE merge→done si falta `dod_live_verified: true` o `dod_evidence`, o si gherkin-matrix tiene `MISSING`, o si `demo_required: true` sin `chris_verify.signoff.result ∈ {SATISFIED, SATISFIED_WITH_FOLLOWUPS}`.

## Nota para stories tipo `bugfix`

Stories `bugfix` usan ceremonia reducida (sin diseño nuevo, sin spec completa):
- Sin `01-spec.md` de diseño; basta `repro_evidence` en `04-validators` (ver `.claude/rules/hotfix-repro-mandatory.md`).
- `cap_change_type: fix | extend` (nunca `new`).
- El resto del flujo (TDD RED→GREEN, auditor, DoD live-verify) aplica igual — la reducción es de diseño, NO de verificación.
- Ref: `MEMORY.md [[bugfix-story-type]]` + `docs/process/lifecycle.md § Tipos de story`.

## Invocación recomendada
```
# Manual (Chris elige cuándo arrancar cada ticket):
/dev-team <brand>: {brand}, ticket: T-1

# Autonomous (si Chris opt-in true al ratificar):
echo 'autonomous_mode: true' >> {brand}/docs/product/stories/{story-id}/checkpoint.md
# /dev-team toma T-1 → auto-handoff T-2 → T-3 → /auditor → /pm-{brand} merge
```
