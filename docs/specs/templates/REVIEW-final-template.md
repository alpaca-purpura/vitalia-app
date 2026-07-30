# REVIEW-final.md — Template (auditor del story completo)

> Owner: `/auditor`. Solo después que TODOS los tickets del story estén en `reviewing` (APPROVED por ticket).
> Verificación end-to-end del story como un todo (no ticket-por-ticket).

---
story_id: STORY_ID
audited_at: 2026-05-04T18:30Z
auditor_model: claude-opus-4-8
verdict: APPROVED                                # APPROVED | CHANGES_REQUESTED
---

## Tickets cubiertos

| Ticket | Tipo | Owner | Verdict | SHA |
|---|---|---|---|---|
| T-1 | backend | qwen-opencode | APPROVED | abc1234 |
| T-2 | agentic | claude-opus-4-8 | APPROVED | def5678 |
| T-3 | frontend | qwen-opencode | APPROVED | 9876fed |

## End-to-end verification

> Más allá de tests por ticket — testear el story como user real.

### Test E2E (Playwright si ui-story, eval suite si agentic-story)

```
$ cd {brand}/frontend && npm run test:e2e:smoke -- --grep "{story-id}"
[paste output]
```

> O agentic:
```
$ WS=$(git rev-parse --show-toplevel) && ${WS}/.venv/bin/pytest {brand}/backend/tests/agentic_evals/{module}/{story_id}_eval.py --trials=3
[paste output]
pass^3 score: 0.83 (>= 0.5 threshold) ✅
```

### Smoke test manual (si aplica)

- [ ] Dev server up (`make dev-app-{brand}`)
- [ ] Naveg `https://dev-app.{brand}lat.com/{path}` (o `localhost:300X` si túnel no provisto)
- [ ] Acción reproducida → outcome esperado verificado
- [ ] Edge cases: cross-tenant tested, mobile responsive verified

## Story-level acceptance (del 01-spec.md)

| Scenario | Type | Verifier | Estado |
|---|---|---|---|
| `happy-path` | happy | e2e + state_check | ✅ |
| `invalid-input` | negative | e2e | ✅ |
| `concurrent-edit` | edge | e2e | ✅ |
| `cross-tenant-leak` | adversarial | e2e + state_check | ✅ |

## Cross-cutting checks

- ✅ Story YAML refleja realidad (state `done` post-merge, scenarios type=regression para los aprobados)
- ✅ Capability YAML actualizado (status derivado de stories)
- ✅ Module doc `product/modules/{m}.md` refleja capability nueva
- ✅ Spanish neutro en strings user-facing
- ✅ Telemetría: events emitidos vistos en logs locales
- ✅ Performance: latencia p95 medida y bajo threshold

## Test coverage delta del story

```
Module                  Before   After    Delta
backend/{m}             81.2%    87.4%    +6.2%
frontend/features/{m}   24.5%    29.8%    +5.3%
```

## Eval coverage delta (si agentic)

| Story | Pass^3 antes | Pass^3 después | Status |
|---|---|---|---|
| `{story_id}` | N/A (planned) | 0.83 | promote → done + scenarios → regression |

## Findings residuales (post-merge)

- ⚠️ Performance: cuando hay > 1000 records, list endpoint demora 800ms p95. Crear story de optimización.
- ✅ Sin findings bloqueantes.

## Verdict

**APPROVED** ✅

> `/pm-{brand}` puede proceder con `07-merge.md`: aplicar diff a `product/`, actualizar state `reviewing → done` en story y capabilities, archivar story (`git mv` a `archive/YYYY/stories/`). Release se avanza si corresponde.

## Verificación live (Critical Rule #37 · `definition-of-done-live-verify.md`)

Los scenarios user-reachable de este ticket se ejercieron contra el stack dev real (`make dev-app-{brand}` / `localhost:300X`), no solo tests verdes:

```yaml
dod_live_verified: true|false
dod_env: "<make dev-app-{brand} → dev-app.{brand}lat.com (Chrome DevTools MCP) | localhost:300X>"
dod_evidence:
  - action: "<write/flujo real ejercido>"
    observed: "<efecto visible>"
    backend_log: "<status + sin traceback + efecto DB>"
```
> Un `GET 200` sobre un placeholder NO es verificación. Una e2e que mockea el backend del surface = falso verde.

## Output al orchestrator

```
APPROVED -> ver REVIEW-final.md
story state: reviewing → done (via /pm-{brand} 07-merge)
next: /pm-{brand} aplica merge
```
