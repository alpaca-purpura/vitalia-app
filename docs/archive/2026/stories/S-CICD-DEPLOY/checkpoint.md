---
story_id: S-CICD-DEPLOY
outcome: infra-dev-multibrand
parent_sub_outcome: cicd-multibrand-deploy
state: done
phase: DONE
last_artifact: docs/product/outcomes/infra-dev-multibrand-CHECKPOINTS.md
last_modified: 2026-05-15T13:00:00Z
next_action: "Outcome cerrado. Capabilities promovidas. Story archivable post rolling 90d."
verdict: APPROVED (post-fix 3 bugs comunify deployment.yaml)
audit_review: docs/product/stories/S-CICD-DEPLOY/REVIEW.md
ratified_by_chris: true
spawned_at: 2026-05-15T00:00:00Z
spawned_by: /pm-luana
ready_at: 2026-05-15T00:00:00Z
ready_by: "/architect (combo /po+/architect session)"
parallel_safe: true
blocked_reason: null
blocked_by: []
estimated_hours: 16-17
tickets_count: 9
audit_iterations: 0
---

# S-CICD-DEPLOY — CI/CD selectivo per brand (GH Actions + Environments)

> Sub-story de [cicd-multibrand-deploy](../../outcomes/cicd-multibrand-deploy.md).

## Ready package (state=ready — 5 artefactos completos)

| Artefacto | Estado | Notas |
|---|---|---|
| `01-spec.md` | DONE | 7 scenarios Gherkin AI-resistant (3 happy + 1 negative + 1 edge + 1 adversarial + 1 happy changelog). ratified_by_chris=true. |
| `03-arch.md` | DONE | Surface diff completo: 15 files new + 5 modified + 2 preserved. Skeletons YAML concretos para todos los workflows + k8s manifests. |
| `04-validators.yaml` | DONE | 14 validators: 6 non_functional + 8 functional. Visual=SKIP, agentic_eval=SKIP (infra pura). |
| `05-guidelines.md` | DONE | 11 patterns required (P1-P11) + 9 patterns forbidden (F1-F9). Files in scope completo. Skills a cargar. |
| `06-tickets.yaml` | DONE | 9 tickets draft. T-2 es primer bloqueante (3h). Total estimado: 16-17h. |

## Tickets (estado ready)

| Ticket | Descripcion | Tipo | production_code | Estimate | Depends on |
|---|---|---|---|---|---|
| T-1 | Runbook setup GitHub Environments per brand × per ambiente | docs | false | 1h | ninguno |
| T-2 | `_deploy-brand.yml` reusable (build image + push GHCR + kubectl apply) | code | true | 3h | ninguno |
| T-3 | `cd-prod.yml` orchestrator (parse release/* + dorny + deploy) | code | true | 2h | T-2 |
| T-4 | Crear `nicolify/deploy/k8s/` desde cero (5 manifests) | code + manifests | true | 2h | ninguno |
| T-5 | Wire vitalia/comunify k8s manifests (comentarios + imagePullSecrets) | code | true | 1h | T-2 |
| T-6 | `lupulo/deploy/k8s/` placeholder (deployment replicas:0 + service) | code | true | 0.5h | ninguno |
| T-7 | `cd-staging.yml` base (push main → staging per-brand) | code | true | 2h | T-2 |
| T-8 | `CHANGELOG-PUBLIC.md` x 4 brands + script extract + tests TDD | docs + code | true | 3h | ninguno |
| T-9 | ADR-002 + runbook cicd + .claude/rules/ refs | docs | false | 1.5h | ninguno |

## Paralelismo recomendado para /dev-team

```
Bloque 1 (paralelo, 0 deps): T-1 + T-4 + T-6 + T-8a (CHANGELOG-PUBLIC.md)
Bloque 2 (bloqueante clave): T-2 (_deploy-brand.yml)
Bloque 3 (paralelo, dep T-2): T-3 + T-5 + T-7
Bloque 4 (TDD, independiente): T-8b (script extract + tests)
Bloque 5 (docs, al final): T-9
```

## Bitacora

- 2026-05-15 — /pm-luana creo folder + checkpoint.md (state=refining)
- 2026-05-15 — /po+/architect combo-session produjo ready package completo (state refining→ready). Decisiones D1-D7 ratificadas por Chris en outcome doc + sesion commit ff33858.
- 2026-05-15 — /dev-team (claude-sonnet-4-6) implementacion autonoma Conv 2. 9/9 tickets done. 16/16 validators GREEN. TDD: 13 tests pytest changelog-extract 100% pass. actionlint 0 errores. yamllint 0 errores (solo warnings aceptables en GH Actions). Anti-duplication: build-push-action en 1 solo archivo. state=ready→developed.
