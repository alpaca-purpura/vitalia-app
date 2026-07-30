<!-- voseo-allowed: dispatch plan interno, no user-facing -->
# Dispatch plan — Story vitalia/vitalia-paradigm-map-zones

## autonomous_mode
- value: **false**  (story grande + cross-scope: docs + scripts + caps + shell + tests; toca taxonomía que el cockpit cross-brand consume)
- chain_if_true: n/a
- rationale: realineación definitiva de agentes + migración de ~48 caps + shell FE shipped (agenda real migra de Valeria a Mateo). Riesgo 404 silencioso (02-impact §9.1) → Chris supervisa los handoffs.

## Ticket → Agent → Model → Cost matrix (vitalia-scope)

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | F1+F4 script migración caps + actions-index + cap nuevo | BE/scripts | builder-backend | sonnet | $0.45 | 35 min |
| T-2 | F2 SYSTEM-MAP promover + validate map_box-aware | BE/scripts | builder-backend | sonnet | $0.30 | 25 min |
| T-3 | F5 ADRs + docs + rules + skill | BE/docs | builder-backend | sonnet | $0.35 | 30 min |
| T-4 | F0 rename backlog Fase 2 + map_box checkpoints | BE/docs | builder-backend | sonnet | $0.20 | 20 min |
| T-5 | F6 shell UI realign (catalog+Ribbon+routing+features) | FE | builder-frontend | sonnet | $0.45 | 40 min |
| T-6 | F7 tests e2e Ribbon/mateo-agenda + specs Valeria | FE | builder-frontend | sonnet | $0.40 | 35 min |
| **Total** | — | — | — | — | **~$2.15** | **~3 h** |

## DAG dependencies
```
T-1 ──► T-2 ──► T-5 ──► T-6
         │       ▲       ▲
         └─► T-4 │       │
T-3 (paralelo) ──┘       T-1 ─────┘ (T-6 depende también de T-1)
```
- T-1 (caps re-tag) primero → T-2 (validar map_box) → T-5 (shell depende de taxonomía) → T-6 (tests del shell).
- T-3 (F5 docs) paralelo a todo.
- T-4 (F0 rename) depende de T-2 (cajas válidas para escribir map_box en checkpoints).

## Playwright visual scope
- story_scope_routes: `/[tenantId]/mateo/agenda` · Ribbon (cualquier ruta shell)
- story_scope_components: `Ribbon.tsx`, `RibbonTab`, `ConfigTab`, `SubTabsBar`
- forbidden: `components/ui/`, `app/[tenantId]/layout.tsx`, `ValeriaSidebar`
- non_egoismo: bug cross-feature real → T-{n}-impl-log § Cross-story observed bugs, NO fix inline
- mockup_gate ADR-vitalia-003: **WAIVED** (checkpoint) → sin mockups

## ★ TOOL-SCOPE separado (NO tickets de esta story · SCOPE_GATE_SKIP fase-solo-bootstrap)

> Estos frentes viven fuera de `vitalia/` (tools cross-brand / docs raíz / rules raíz). `/pm-vitalia` NO los owna. Se ejecutan en la **misma tanda** (fase-solo-bootstrap permite) pero como **dispatch tool/protocol-scope** con `SCOPE_GATE_SKIP=1 + razón en commit body`, NO como autonomous chain. Requieren worktree `protocol` o fase-solo-bootstrap.

| Frente | Paths | Trabajo | Cuándo |
|---|---|---|---|
| **F3 cockpit MapView** | `tools/luana-cockpit/{lib/agent-meta.ts, lib/types.ts, components/map/MapView.tsx}` | render por **zona** + 2 lentes (trabajadores/proceso) + Valeria sidebar supervisor + agregar mateo · leer `zones` de SYSTEM-MAP (NO FALLBACK_AGENTS hardcoded) | tras T-2 (SYSTEM-MAP cementado) |
| **F4 consumer cockpit** | `tools/luana-cockpit/` lectura `_actions-index.json` | el GENERADOR (`generate_actions_index.py`) es vitalia-scope (T-1); el consumo en cockpit es tool-scope | tras T-1 |
| **capability-protocol §7** | `docs/process/capability-protocol.md` (raíz cross-brand) | tabla `agent_owner`→`map_box` v2 (12 cajas) | protocol-scope |
| **paradigm rule** | `.claude/rules/paradigm-arquitectura.md` (raíz) | ref menor opcional (ya cementada) | protocol-scope |

Comando tool-scope (ejemplo): `SCOPE_GATE_SKIP=1 git commit <paths> -m "feat(cockpit): MapView render por zona + 2 lentes [tool-scope vitalia-paradigm-map-zones]"` con razón en body.

## Recommended invocation (manual · autonomous_mode false)
```
/dev-team vitalia, ticket: T-1     # Chris arranca; T-2..T-6 secuencial por DAG
# tras vitalia-scope cerrado → tool-scope F3/F4-consumer en worktree protocol o fase-solo-bootstrap
```

## Split recommendation
Conteo: **6 tickets vitalia-scope** → cabe en 1 story (≤10). **Sin split necesario.**
