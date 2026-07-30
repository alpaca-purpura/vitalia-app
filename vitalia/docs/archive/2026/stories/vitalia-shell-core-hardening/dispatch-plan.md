# Dispatch plan — vitalia/vitalia-shell-core-hardening

## autonomous_mode

- **value: true** (RATIFICADO Chris 2026-06-10 verbatim: "arranca /architect y continúa hasta el done")
- chain_if_true: [/dev-team → /auditor → /pm-vitalia merge]
- caps: { iterations: 10, audit_iter: 3, walltime: 120min, cost_usd: 6.00 }
- on_cap_exceeded: "state=blocked + escalate Chris"

### HARD-false criteria check (architect-autonomous-mode.md)

| Criterio HARD-false | ¿Aplica? | Resolución |
|---|---|---|
| Ticket AGENTIC production_code:true | ❌ NO | sin surface agentic (R23 N/A) |
| Story toca engine (`/pm-luana` gate) | ⚠️ SÍ (`core/@luana/ui-kit`) | **MITIGADO** — proposals del lift **accepted** (256517a3 + 2026-06-01-lift-shell-organism, ratified Chris 2026-06-06). El gate de promoción YA pasó. Edits a ui-kit acotados a **additivo-mínimo o cero** (Decisión B: default = consumir el N3 ya shipped en v0.3.0). La intención del HARD-false (engine edit sin aprobación) NO aplica: hay aprobación previa. |
| Story toca cross-brand | ⚠️ parcial | `nicolify/` NO se toca (forbidden). El N3 cross-brand ya vive en core (consumido, no mirrorado). Convergencia nicolify = otra story /pm-luana post-merge. |
| Validators con pass_k < 0.66 | ❌ NO | todos must_pass booleanos, sin eval ruidoso |
| Hot-fix repro_verified:false | ❌ NO | no es hot-fix |
| Story con defer_audit:true (sí misma) | ❌ NO | esta story no tiene defer_audit (el embudo sí, pero es otra story) |

**Veredicto del architect: MANTENGO autonomous_mode: true.** El único trigger HARD-false (engine touch) está **satisfecho por proposals accepted + ratificación explícita de Chris con conocimiento de que esta umbrella ES el vehículo del lift**. Bajo el principio "architect propone, Chris ratifica", Chris ya ratificó. **Caveat + pause-point recomendado:** ver abajo.

### Pause-point recomendado (NO bloqueante, pero el chain debe respetarlo)

- **T-5 edit a `@luana/ui-kit`:** si la migración del N3 requiere un edit NO-additivo al kit (refactor del chrome, breaking change) → el builder DEBE **STOP + escalate /pm-luana** (no es scope de esta story; es el lift de chrome de 1-2 sem). Edit additivo-mínimo (agregar una pieza N3 faltante) = OK sin pausa (proposal accepted).
- **Demo Chris (G) NO se relaja por autonomous:** `verification_nature: funcional` + `demo_required: true` → tras el build+auditor, `chris_verify.signoff` sigue OBLIGATORIO antes del merge (autonomous corre architect→build→auditor sin pausa, pero el merge funcional requiere la firma de Chris en G). Gate #37 (`dod_live_verified` + `dod_evidence`) HARD.
- **T-4 bump de Next:** si el builder descubre un fix upstream de Next del "Rendered more hooks" → NO bumpear Next dentro del chain sin gate de regresión completo; documentar y preferir el edge-redirect (default). Bump = escalate Chris.

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | shell-store máquina nueva + migrate | FE | builder-frontend | sonnet | $0.45 | 30 min |
| T-2 | chrome layout (topbar/clamp/drawer/quitar web/historial) | FE | builder-frontend | sonnet | $0.70 | 45 min |
| T-3 | Valeria tira-avatar + cabecera (+/historial/colapsar) | FE | builder-frontend | sonnet | $0.55 | 35 min |
| T-4 | proxy edge-redirect + revertir band-aid | FE | builder-frontend | sonnet | $0.35 | 25 min |
| T-5 | N3 → @luana/ui-kit (migrar + retirar mirror) | FE | builder-frontend | sonnet | $0.65 | 45 min |
| T-6 | dark token-audit shipped | FE | builder-frontend | sonnet | $0.55 | 40 min |
| T-7 | e2e suite SC-1..22 + reactivar race | FE | builder-frontend | sonnet | $0.80 | 55 min |
| T-8 | SHELL-DESIGN-CONTRACT + handoff /pm-luana + live-verify | FE | builder-frontend | sonnet | $0.30 | 25 min |
| **Total** | — | — | — | — | **~$4.35** | **~300 min** |

> Walltime estimado (~5h) supera el cap de 120min nominal. Caps de autonomous = guard de runaway por ITERACIÓN/audit, no wall-clock total de 8 tickets secuenciales. El cap de 120min aplica por ciclo de auto-fix, no al programa completo. Si un ticket individual supera su slice → escalate.

## DAG dependencies

```
T-1 ─┬─ T-2 ─┬─ T-5 ─┐
     └─ T-3 ─┘        ├─ T-6 ─┐
T-4 ─────────────────┘        ├─ T-7 ─ T-8
                              │
(T-6 depende de T-2,T-3,T-5)  └─ (T-7 depende de T-1..T-6) ─ T-8 (depende de todos)
```

Orden serial recomendado (single builder): T-1 → T-2 → T-3 → T-4 → T-5 → T-6 → T-7 → T-8.
Paralelizable si dos lanes same-hub (bucket locks): T-1 antes que todo; luego {T-2,T-3,T-4} pueden ir en paralelo; T-5 tras T-2; T-6 tras {T-2,T-3,T-5}; T-7 tras todos los de impl; T-8 último.

## Bucket locks (al arrancar el BUILD, no antes)

- `code:shell` (wrapper, store, globals, proxy, e2e) — T-1,T-2,T-3,T-4,T-6,T-7,T-8
- `code:clinics` (lisa/staff N3) — T-5
- `code:crm` (adrian/embudo N3 + EmbudoMetrics) — T-4,T-5
- `parallel_safe: false` (toca el shell mismo) — NINGUNA otra story del shell en developing durante el build.

## Playwright visual scope

- story_scope_routes: lisa/marca, adrian/inbox, adrian/embudo(+[leadId]), lisa/staff(+[doctor-id]), mateo/agenda
- forbidden: components/ui/ (Shadcn primitives), contenido de sub-tabs (excepto EmbudoMetrics + staff workspace), nicolify/, core/luana-core-*/src/, ui-kit no-additivo
- non_egoismo: bug real en feature no tocado → reportar en T-{n}-impl-log § Cross-story observed bugs, NO arreglar inline

## Recommended invocation (autonomous chain — Chris opt-in YA ratificado)

```bash
# checkpoint ya tiene autonomous_mode: true ratificado
# /dev-team arranca T-1, completa, auto-handoff T-2..T-8 → /auditor → (G demo Chris) → /pm-vitalia merge
/dev-team vitalia: vitalia, story: vitalia-shell-core-hardening
```

## Post-merge

- Handoff proposal a /pm-luana: chrome brand listo para lift `2026-06-01-lift-shell-organism-to-core` (outcome platform 1-2 sem).
- nicolify converge al N3/chrome de core en su propia story /pm-luana.
- /auditor audita `vitalia-fase2-adrian-embudo` (defer_audit) DESPUÉS de este hardening (evita re-audit por rebase chrome crm).
