# Dispatch plan — vitalia/vitalia-shell-state-persistence

## autonomous_mode
- value: false
- reason: "ui-story standard ≤10 tickets, NO agentic, NO engine — autonomous SEGURO, pero Chris opt-in explícito requerido (default false per architect-autonomous-mode.md). El riesgo (NO repetir 4 técnicas fallidas + slice mobile independiente) amerita supervisión inicial."
- chain_if_true: [/dev-team → /auditor → /pm-vitalia merge]
- caps: { max_iterations_per_ticket: 10, max_audit_iterations: 3, max_total_cost_usd: 5.00, max_wall_clock_minutes: 120, on_cap_exceeded: "state=blocked + escalate Chris" }

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | Factory SSR-safe + shell-store + ADR-006 | FE | builder-frontend | sonnet | $0.45 | 35 min |
| T-2 | Skeleton store-free (TopBar variant + rehydrate) | FE | builder-frontend | sonnet | $0.35 | 25 min |
| T-3 | Factory → 3 stores transversal | FE | builder-frontend | sonnet | $0.30 | 20 min |
| T-4 | Mobile collapsed-pero-recuerda slice | FE | builder-frontend | sonnet | $0.40 | 30 min |
| T-5 | Un-skip 3 + nuevos e2e + POM | FE | builder-frontend | sonnet | $0.40 | 30 min |
| Total | — | — | — | — | **$1.90** | **~140 min** |

## DAG dependencies
```
T-1 ──┬─→ T-2 ──┐
      └─→ T-3   ├─→ T-4 (needs T-1+T-2) ─→ T-5 (needs T-2+T-3+T-4)
                │
T-2 ∥ T-3 (paralelizables tras T-1)
```

## Playwright visual scope
- story_scope_routes: ["/[tenantId]/(shell-organism)/** (shell wrapper, toda ruta autenticada)"]
- story_scope_components: lib/store/**, los 4 stores persist, shell-organism {ShellOrganismLayout,Client,TopBarGlobal,ValeriaSidebar,useViewportGuard}
- forbidden: components/ui/, otros features (salvo 2 agenda stores), app/layout.tsx
- non_egoismo: report cross-story bugs en T-n-impl-log § Cross-story observed bugs; NO fix inline
- mockup gate: EXEMPT (Chris 2026-05-28) — no pixel goldens nuevos; mobile drawer = behavior test

## Recommended invocation if autonomous
```bash
echo 'autonomous_mode: true' >> vitalia/docs/product/stories/vitalia-shell-state-persistence/checkpoint.md
# /dev-team toma T-1 → T-2∥T-3 → T-4 → T-5 → /auditor → /pm-vitalia merge
```

## Recommended invocation if manual (default)
```
/dev-team vitalia: vitalia-shell-state-persistence, ticket: T-1
```

## Critical reminders for /dev-team
- PROHIBIDO repetir las 4 técnicas fallidas (00-research.md). El fix = boundary store-free + setItem no-op pre-hydration.
- mobileDrawerOpen es slice INDEPENDIENTE de valeriaState (NO derivar drawer de valeriaState).
- Tests nativos: npx vitest / E2E_BASE_URL=http://localhost:3002 npx playwright. NUNCA make e2e.
- Governing ADR = ADR-vitalia-006 (NO 005 — colisión con capability-model).
