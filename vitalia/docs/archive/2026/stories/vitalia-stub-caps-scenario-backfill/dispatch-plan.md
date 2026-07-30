# Dispatch plan — Story vitalia/vitalia-stub-caps-scenario-backfill (v2)

## autonomous_mode
- value: false
- razón: el bar **deployed-visible** (ratificado Chris) requiere verificación hands-on del orchestrator (Claude) — ejercer en dev-app.vitalialat.com + leer docker logs + chrome-devtools — que no es un gate mecánico. Chain drivear manual esta sesión.
- chain (manual): /architect → /dev-team (T-0,T-A,T-B,T-C,T-D) → **orchestrator verifica dev-app** → /auditor → /pm-vitalia merge
- caps si se reactivara: {iterations: 10, audit_iter: 3, cost_usd: 6.00, walltime: 120min}

## Ticket→Agent→Model matrix

| T-id | Title | Surface | Agent | Model | Est. |
|---|---|---|---|---|---|
| T-0 | Gate extension pytest (scripts/) | TOOLING | builder-backend | sonnet | ~20min |
| T-A | G1 UI-visible 7 caps (wire e2e + dev-app) | DOCS+TESTS | builder-frontend | sonnet | ~35min |
| T-B | G2 admin 5 caps (wire admin e2e) | DOCS+TESTS | builder-frontend | sonnet | ~25min |
| T-C | G3+G4 infra/backend 8 caps (pytest, post T-0) | DOCS+TESTS | builder-backend | sonnet | ~35min |
| T-D | VERIFICATION-REPORT + gates finales | DOCS | builder-backend | sonnet | ~20min |
| Total | — | — | — | sonnet | ~135min |

Cero agentic · cero Opus · cero engine edit.

## DAG
`T-0 → T-C` ; `T-A ∥ T-B` (independientes) ; `(T-A,T-B,T-C) → T-D`

## Verificación deployed-visible (orchestrator hands-on, post dev-team)
- G1: ejercer theme-toggle / topbar / sign-in / /config/avanzado / landing pública en dev-app.vitalialat.com → efecto visible + `docker logs luana-dev-vitalia_backend_dev-1` sin 4xx/5xx
- G2: ejercer login + listar/crear en admin Streamlit deployed
- G3: `curl -fsS https://dev-app.vitalialat.com/api/health` → 200 + body ; smoke suite verde
- G4: pytest verde = evidencia honesta (sin superficie dev-app)
- Resultado → incorporado a VERIFICATION-REPORT.md por-cap

## Invocación manual
`/dev-team vitalia vitalia-stub-caps-scenario-backfill` (toma T-0 primero, luego T-A/T-B paralelos, T-C tras T-0, T-D al final)
