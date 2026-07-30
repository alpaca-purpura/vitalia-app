---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
architecture_pattern: ADR-vitalia-004
autonomous_mode: true          # Chris ratified 2026-06-15 (checkpoint) — SUB-PHASE A ONLY
---

# dispatch-plan — vitalia-fase2-lisa-servicios

## autonomous_mode: true — scope + HARD stops

`autonomous_mode: true` aplica **SOLO a Sub-phase A** (T-1..T-8, NO-RAG). La cadena autónoma corre:

```
/architect (done) → /dev-team (Sub-phase A · sin pausa G) → /auditor → STOP-1 (chris_verify.signoff funcional)
```

**STOP-1 (merge gate · funcional):** al cerrar `/auditor` APPROVED + live-verified, la story queda en `reviewing`/`developed` con `chris_verify.signoff` requerido (verification_nature: ambas → demo_required). NO auto-merge a `done` sin signoff humano. (Esto NO lo maneja el dispatch — es el story-closure-gate; se estructura para que el auditor pare ahí.)

**STOP-2 (engine-lift gate · Sub-phase B):** la cadena autónoma **PARA antes de Sub-phase B**. Sub-phase B (RAG: T-B1/T-B2/T-B3) requiere `/pm-luana` engine-lift:
> "Sub-phase B requires /pm-luana engine-lift gate — produce promotion proposal `docs/promotion-protocol/proposals/2026-06-15-offer-knowledge-rag-indexer-and-sales-agent-retrieval.md`, present to Chris, do NOT build without OK."

La story NO alcanza `done` 100% autónoma: dos stops downstream (chris_verify.signoff + /pm-luana RAG OK). RN-17(b)/RN-22/AC-15(B) quedan `verification_phase: B` deferred → el auditor + reconcile NO fallan Sub-phase A por su ausencia.

## chain_if_true
- [x] `/dev-team vitalia vitalia-fase2-lisa-servicios` — Sub-phase A autonomous build (T-1 primero, DAG abajo).
- [x] auto-handoff `/auditor` post developed (autonomous_mode → sin pausa G).
- [ ] STOP antes de Sub-phase B (/pm-luana).
- [ ] STOP en reviewing/APPROVED+live-verified para chris_verify.signoff (funcional · merge gate).

## Caps (Auditor Responsable v5)
- `responsible_fix_iter` ≤ 6 · `audit_iterations` ≤ 4 · wall-clock ≤ 40 min.
- Stake-asimétrico (tenant-isolation, RBAC, Case consent HIPAA-lite, keystone shape, engine-boundary) → Carril C escalate Chris, NO override.
- Fix de feature entera (>~2 archivos producto nuevos) → Carril C' (plan + CHANGES_REQUESTED a dev-team).

## ticket → agent → model → cost matrix

| Ticket | Surface | Agent | Model tier | Est. cost | Notas |
|---|---|---|---|---|---|
| T-1 | BE | builder-backend | workhorse | $$ | domain+infra+migrations (RED-first; pricing/completeness mutation) |
| T-2 | BE | builder-backend | workhorse | $$ | services+routers+RBAC+search |
| T-3 | BE | builder-backend | workhorse | $ | EP-2 preset pack + typeahead |
| T-4 | BE | builder-backend | workhorse | $$ | doc-autocomplete (consume copilot) + KEYSTONE (consume-only · NO agentic → workhorse OK) |
| T-5 | FE | builder-frontend | workhorse | $$ | NumberWithUnit shared + moléculas |
| T-6 | FE | builder-frontend | workhorse | $$$ | catálogo + escalera (dnd+a11y) + N3 routing |
| T-7 | FE | builder-frontend | workhorse | $$$ | workspace 5 leaves + autosave + picker (el más grande) |
| T-8 | BE+FE | builder-frontend (coord) | workhorse | $$ | tests + visual goldens + live-verify |
| T-B1/B2/B3 | engine | **/pm-luana → flagship** | **flagship** | gated | BLOCKED · NO build sin /pm-luana OK (R23 agentic) |

> **NO agentic-runtime ticket en Sub-phase A** → ningún ticket workhorse viola R23. T-4 es consume-only (data shape + copilot extract consume), NO escribe `copilot/`/`sales_agent/` brand code. Sub-phase B (engine agentic) = flagship + /pm-luana.

## DAG + paralelización (bucket `code:offer` — single-hub commit por pathspec)

```
                ┌─→ T-2 ─┬─────────────→ T-4 ──┐
   T-1 ─────────┤        │                      │
   (BE domain)  └─→ T-3 ─┼──→ T-6 ──┐           ├─→ T-8 ─→ STOP-1 (chris_verify)
                         │           │           │            │
   T-5 ─────────────────┴──→ T-7 ───┘───────────┘            └─→ STOP-2 (/pm-luana Sub-phase B)
   (FE primitives)
```
- T-1 + T-5 arrancan en paralelo (BE domain ⟂ FE primitives, sin dep).
- T-2/T-3 tras T-1. T-4 tras T-2. T-6 tras T-2+T-3+T-5. T-7 tras T-2+T-4+T-5. T-8 tras T-4+T-6+T-7.
- Single-hub: bucket lock `code:offer` (FE+BE mismo módulo). Commit por pathspec siempre (`git commit <rutas>`).

## playwright visual scope (resumen · detalle en 04-validators)
- story_scope_routes: `/{tenantId}/lisa/servicios{,/catalogo,/escalera,/[offer-id]/*,/nuevo}`.
- forbidden_visual_changes: `components/ui/**`, `@luana/ui-kit/src/**`, `components/shared/shell-organism/**`, otras features.
- allowed new: `components/shared/NumberWithUnit.tsx`, `shell-routes.ts` AGENT_SUBSUBTABS append.
- non_egoismo: commit pathspec; no tocar scope ajeno.

## Definition of Done (Sub-phase A · DoD #37)
- AC-1..AC-14, AC-18, AC-19 (Sub-phase A) verificados. AC-15(B) deferred.
- Visual goldens 8 verdes (maxDiffPixelRatio 0.001).
- BE pytest dual-tenant + RBAC + consent + keystone + arch fitness verdes. Mutation hard sobre pricing/completeness/RBAC/tenant.
- **LIVE-verify (dev-app vitalia):** crear servicio + activar + autosave (write real) + KEYSTONE (Adrián cita el servicio) + leer logs → `dod_evidence`. NO GET 200.
- `make ci-parity` (engine + vitalia) verde.
- → STOP-1 chris_verify.signoff → /pm-luana Sub-phase B.
