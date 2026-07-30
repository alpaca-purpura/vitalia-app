# Dispatch plan — Story vitalia/estabilizar-harness-e2e-lisa-marca

> Owner: `/architect`. Consumer: `/dev-team`. SSoT schema: `.claude/rules/architect-autonomous-mode.md`.
> Tipo: `bugfix` (lite, ADR-011). Naturaleza: harness E2E honesto + determinista + 2 sub-bugs de auth-header.

## autonomous_mode
- value: **false**                  # default. Chris opt-in explícito al ratificar ready.
- chain_if_true: [/dev-team → /auditor → /pm-vitalia merge]
- caps: { max_iterations_per_ticket: 8, self_fix_iter: 5, audit_iterations: 4, max_total_cost_usd: 4.00, max_wall_clock_minutes: 90, on_cap_exceeded: "state=blocked + escalate Chris" }

> **Por qué false (recomendado):** la story requiere `make dev-vitalia` UP + sesión Clerk + tenant real para
> SC-1/SC-4/SC-6/SC-7 (live-verify). No es una build hermética. Chris decide cuándo arrancar con el stack listo.
> No hay bloqueador HARD para true (ningún ticket AGENTIC `production_code:true`; cero `core/`; cero cross-brand;
> sin `pass_k`; sin `defer_audit`), pero la dependencia del stack dev favorece el modo manual.

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | primary_agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-3 | BE: X-User-ID opcional (sub-bug #1) + actor desde clerk_sub (#2b) | BE | builder-backend | sonnet | ~$0.60 | ~35 min |
| T-2 | FE-prod: actor audit real (sub-bug #2) | FE | builder-frontend | sonnet | ~$0.40 | ~25 min |
| T-1 | FE-tests: de-mock 11 specs + web-first + fixture forwarding + des-quarantine 5 fixme | FE-tests | builder-frontend | sonnet | ~$1.20 | ~70 min |
| T-4 | Docs: re-cable cap lisa-marca.yaml | docs | builder-frontend | sonnet | ~$0.20 | ~15 min |
| **Total** | — | — | — | — | **~$2.40** | **~145 min** |

> Ningún ticket es AGENTIC production_code → R23 no aplica → todo Sonnet (T-1/T-4 son `production_code:false`,
> pool [qwen, sonnet]; T-2/T-3 son `production_code:true` non-agentic, pool [sonnet, opus] → Sonnet sweet spot).

## DAG dependencies

```
T-3 (BE: header opcional #1 + actor resolver #2b) ──┐
        │                                            ├──> T-1 (FE-tests de-mock + web-first) ──> T-4 (docs cap)
T-2 (FE-prod actor real #2) <── depende T-3 ─────────┘
```

Racional: la suite de-mockeada (T-1) corre contra el BE REAL; para que SC-6 (audit actor real) y SC-7
(prohibited-phrases 200) pasen, el BE debe tener el header opcional + el actor real (T-3) y el FE debe mandar
el actor real (T-2). T-4 cierra apuntando a los specs ya honestos.

## Playwright visual scope discipline

- story_scope_routes: **N/A** — bugfix de harness, cero UI nueva, cero cambio visual.
- story_scope_components: ninguno (no se renderiza nada nuevo).
- forbidden_visual_changes: `vitalia/frontend/src/components/ui/`, `components/shared/`, `app/layout.tsx`, cualquier componente de producto.
- **Sin visual goldens nuevos** (ratificado: a11y/i18n `not_applicable` a nivel meta-harness — Chris 2026-06-02).
- non_egoísmo: bug visible en feature/ruta NO tocada por esta story (valeria/camila/doctores) → reportar en
  `T-{n}-impl-log.md § Cross-story observed bugs`, NO arreglar inline.

## DoD live-verify gate (Critical Rule #37)

> Ref: `.claude/rules/definition-of-done-live-verify.md`. Esta story es **funcional/user-reachable**
> (toca FE-prod marca-voice-api + flujos lisa-marca) → `demo_required: true`.

- `/dev-team` ejerce las acciones reales en el stack dev vitalia (`make dev-vitalia` → localhost:3002/:8002, o
  `make dev-app-vitalia` → dev-app.vitalialat.com) via **Chrome DevTools MCP** antes de cerrar `developed`:
  - **SC-6:** PATCH personality real (owner Clerk `dr.demo@vitalialat.com`) → leer Network + Console (0 burbuja) +
    query DB `vitalia_audit_log` → actor = `users.id` real (≠ tenant_id).
  - **SC-7:** abrir voz-y-tono → GET `prohibited-phrases` **200** en el Network panel (sin header inyectado) +
    `docker logs luana-dev-vitalia_backend_dev-1` sin 422.
- Registra `dod_live_verified: true` + `dod_evidence` (writes ejercidos + efecto + backend logs sin traceback) en `checkpoint.md`.
- Gate anti-burbuja: los 11 specs de-mockeados importan `base.ts` (vía `real-backend-forward.fixture`), NO `@playwright/test` directo.
- `demo-script.md` lite (4 secciones) + `demo_signoff` de Chris requerido.
- `/pm-vitalia` REFUSE merge→done si falta `dod_live_verified: true` / `dod_evidence`, si gherkin-matrix tiene `MISSING`,
  o si `demo_signoff.result ∉ {APPROVED, APPROVED_WITH_NOTES}`.

## Nota tipo `bugfix` (ceremonia reducida)

- `cap_change_type: fix` (nunca `new`). `adr_004_compliance: bugfix-lite-na` (no es sub-tab nueva → no exige las 9 secciones de ADR-vitalia-004).
- `repro_verified: true` (re-repro 2026-06-02 contra HEAD — root-cause fresco; direcciones viejas #1/#2 obsoletas).
- La reducción es de **diseño** (no spec UI completa), NO de **verificación**: TDD RED→GREEN, auditor, DoD live-verify aplican igual.

## § Open item para PM (ver 03-arch.md § 16)

- **Sub-bug #2 mecánica FE+BE:** Chris ratificó "scope completo · sub-bug #2 in-story". La restricción dura
  (audit actor DEBE ser UUID; Clerk userId no es UUID) obliga a un **par FE (T-2) + BE (T-3 #2b)**: el FE deja de
  mandar el tenant como actor + el BE resuelve el actor real desde el `clerk_sub` del JWT (vía `_resolve_user_uuid`,
  consumido no recreado). Esto agrega un toque BE chico al `brand_studio` (no core, no otra brand). Confirmar con PM
  que cae dentro de "in-story". Surfaceado, NO bloqueante (es la única forma de cerrar AC-3/RN-5 sin un actor falso).

## Invocación recomendada

```
# Manual (recomendado — requiere make dev-vitalia UP para live-verify):
/dev-team <brand>: vitalia, ticket: T-3      # BE primero (desbloquea T-1/T-2)
# luego T-2 (FE-prod) → T-1 (FE-tests) → T-4 (docs cap)

# Autonomous (solo si Chris opt-in true al ratificar + stack dev garantizado UP):
echo 'autonomous_mode: true' >> vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/checkpoint.md
```
