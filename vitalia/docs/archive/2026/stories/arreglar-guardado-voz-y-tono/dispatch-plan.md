# Dispatch plan — Story vitalia/arreglar-guardado-voz-y-tono (bugfix lite)

## autonomous_mode
- value: true
- ratified_by: chris (instrucción directa "hasta el done" 2026-05-30)
- chain_if_true: [/dev-team → /auditor → /pm-vitalia merge]
- caps: { iterations_per_ticket: 8, audit_iter: 3, cost_usd: 2.50, walltime_min: 60 }
- on_cap_exceeded: "state=blocked + escalate Chris"
- safe_for_autonomous: true (no agentic prod · no engine · ≤3 tickets · validators must_pass claros · bugfix lite)

## Ticket → Agent → Model → Cost matrix
| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | BE fix sanitize_phi_payload (audit+telemetry) | BE | builder-backend | sonnet | ~$0.30 | 20 min |
| T-2 | BE camelCase alias 2 DTOs personality | BE | builder-backend | sonnet | ~$0.30 | 20 min |
| T-3 | E2E voz-y-tono autosave (backend real) | FE | builder-frontend | sonnet | ~$0.40 | 30 min |
| Total | — | — | — | — | **~$1.00** | **~60 min** |

## DAG
T-1 ∥ T-2 (independientes · módulos distintos: `audit`+`_shared/telemetry` vs `brand_studio`) → T-3 (depende T-1+T-2)

## Playwright visual scope
- story_scope_routes: [/[tenantId]/lisa/marca/voz-y-tono]
- forbidden: components/ui/, components/shared/, layout.tsx
- non_egoismo: bugs fuera scope → T-n-impl-log § Cross-story observed bugs (NO fix inline)
- NOTA: esta story NO cambia visual; E2E es funcional (sin snapshots de página).

## Invocation autonomous
/dev-team vitalia arreglar-guardado-voz-y-tono   # toma T-1/T-2, luego T-3, auto-handoff /auditor → /pm-vitalia merge

## Verificación REAL (gate de honestidad)
El E2E NO debe mockear el API (`verification-real-not-200`). Debe ejercer la acción real contra backend
corriendo (`make dev-vitalia` :8002) y confirmar persistencia + ausencia de 4xx/5xx en logs.
