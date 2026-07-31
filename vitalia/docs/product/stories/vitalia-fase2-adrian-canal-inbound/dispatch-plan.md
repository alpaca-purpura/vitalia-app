# dispatch-plan — canal-inbound (Adrián)

> **autonomous_mode: false** (agentic + PHI = stake-asimétrico). Gate **G (Chris-verify live Telegram)**
> OBLIGATORIO antes del auditor. Invocación **manual** (NO autonomous). Architect propone; Chris ratifica.

## Estado del ready package
- `verdict: BLOCKED-PARTIAL`. Las superficies BE/FE + agentic-overlay son buildable HOY. El **valor agentic
  central (book/match/share via grafo)** está BLOQUEADO hasta el lift `/pm-vitalia` (ESC-1/2/3, ver 03-arch.md
  § Engine-boundary escalations).
- **No se puede transicionar a `developing` el carril agentic lift-gated** hasta merge del lift. El carril
  BE/FE + T-AG-1 SÍ puede arrancar.

## Caps de ejecución
- `responsible_fix_iter` ≤ 6 · `audit_iterations` ≤ 4 · wall-clock ≤ 40 min por ticket.
- Agentic stake-asimétrico (prompt/state/eval/PHI) → auditor Carril C (escalate), NO self-fix de comportamiento.

## Handoff matrix (ticket → agent → model → cost)

| Ticket | Surface | Agent | Model (tier) | Bloqueado | Costo estimado |
|---|---|---|---|---|---|
| T-LIFT-1 | engine | **/pm-vitalia** (gate, no builder) | coordinator | 🔴 (es el desbloqueante) | — (promotion proposal) |
| T-BE-1 | be | builder-backend | workhorse | ✅ no | medio (canal + dedup + security tests) |
| T-BE-2 | be | builder-backend | workhorse | ✅ no | medio-alto (slot-marking + hold + sweep + migrations) |
| T-BE-3 | be | builder-backend | workhorse | ✅ no | medio (bridge + endpoint) |
| T-AG-1 | agentic | builder-agentic | **flagship (R23 HARD)** | ✅ no | alto (overlay + persona tuning + 5 goldens) |
| T-AG-2 | agentic | builder-agentic | **flagship** | 🔴 ESC-1 | alto (provider + bridge sync/async) |
| T-AG-3 | agentic | builder-agentic | **flagship** | 🔴 ESC-2/3 | alto (book + dedup + race + goldens) |
| T-AG-4 | agentic | builder-agentic | **flagship** | 🔴 ESC-2/3 | medio (match) |
| T-AG-5 | agentic | builder-agentic | **flagship** | 🔴 ESC-2/3 | bajo (share URL trivial) |
| T-FE-1 | fe | builder-frontend | workhorse | ✅ no | bajo-medio (composer EXTEND) |

> R23 HARD: todo ticket agentic `production_code: true` → `flagship`. NUNCA sonnet/opencode.

## DAG

```
T-LIFT-1 (/pm-vitalia) ──┬─→ T-AG-2 ──→ T-AG-3
                       ├─→ T-AG-4 ──→ T-AG-3
                       └─→ T-AG-5
T-BE-1 ──┬─→ T-AG-1
         └─→ T-BE-3 ──┬─→ T-FE-1
                      └─→ T-AG-1
T-BE-2 ──→ T-AG-2 / T-AG-3 (consume create_appointment_service)

Carril buildable hoy (paralelo): T-BE-1 → T-BE-2 → T-BE-3 → T-AG-1 → T-FE-1
Carril lift-gated (espera T-LIFT-1 merge): T-AG-2 → T-AG-4 → T-AG-3 ; T-AG-5
```

## Secuenciamiento recomendado al PM
1. **Disparar `/pm-vitalia` T-LIFT-1 (ESC-1/2/3) en paralelo** — es un lift cohesivo (~80 LOC + 2 arch tests) que
   completa el wiring EP-3 (Stories 11-13 "wiring real adapters" quedó a medias). Beneficia toda brand con
   sales_agent propio.
2. **Arrancar carril BE/FE + T-AG-1** ya (no depende del lift). Cierra el canal + plomería + overlay + composer.
3. **Cuando el lift mergea** → carril agentic book/match/share.
4. **Confirmar deps duras done** (lisa-servicios + adrian-inbox + lisa-doctores — archivados = done) antes del BUILD.

## Playwright visual scope (ver 04-validators § playwright_visual_scope)
- Routes: `/{tenantId}/adrian/inbox` (composer extendido — NO ruta nueva).
- Touchable: `features/adrian/components/inbox/composer/`. Forbidden: otras sub-tabs + shell wrapper.
- golden_policy: shrink-only.

## Gate G (Chris-verify live Telegram) — OBLIGATORIO pre-auditor
Enviar mensaje real por Telegram (bot dev, tenant ≠ Chris) contra stack dev → leer reply + logs BE + filas DB
(conversación, scheduling_appointment origin=proactivo_adrian [post-lift], availability_slot marcado [post-lift],
trace, costo). CERO "GET 200". `chris_verify.signoff` antes del `/auditor`.

## Invocación manual (NO autonomous)
```
# carril buildable (tras ratify Chris del ready package):
/dev-team vitalia vitalia-fase2-adrian-canal-inbound   # arranca T-BE-1 (+ paralelos BE/FE)
# carril lift (paralelo):
/pm-vitalia   # T-LIFT-1 promotion proposal ESC-1/2/3
# tras builds: G (Chris-verify live) → /auditor vitalia → /pm-vitalia merge → done
```
