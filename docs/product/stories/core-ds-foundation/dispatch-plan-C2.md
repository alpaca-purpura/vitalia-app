# Dispatch plan (C2 · SPINE) — core-ds-foundation

> Cómo `/dev-team` spawnea el Tramo C2. Modelo fijado por ADR-016 (accepted). Architect propone · Chris ratifica.

## autonomous_mode: **false** (default)

Architect NO declara autonomous. Razones:
- **T-3 es funcional/ambas** (unwind vitalia · riesgo visual): exige live-verify en dev-app + firma de Chris en **G** (`chris_verify.signoff`). No es autonomizable — la garantía "app idéntica post-migración" la cierra el ojo de Chris, no un gate verde (`definition-of-done-live-verify` #37).
- T-1/T-2/T-4 son técnicas y SÍ podrían correr sin pausa, pero el riesgo de T-3 + el hecho de que C2 toca **engine core/@luana** (downstream a 4 marcas) aconseja el gate humano. Chris puede opt-in a autonomous para T-1/T-2/T-4 si quiere, dejando T-3 con G.

## Matriz ticket → agent → model → costo

| Ticket | primary_agent | model | tier | surface | auditor | verificación |
|---|---|---|---|---|---|---|
| C2-T1 | `builder-frontend` | workhorse | workhorse | tooling (`scripts/` + `catalog.*` + arch-test) | `auditor-frontend` | técnica · efecto + RED-probe del gate |
| C2-T2 | `builder-frontend` | workhorse | workhorse | engine `core/@luana/design-tokens` | `auditor-frontend` | técnica · efecto (valor → render) + no-drift |
| C2-T3 | `builder-frontend` | workhorse | workhorse | brand `vitalia/frontend` | `auditor-frontend` | **funcional/ambas · live-verify + demo G** |
| C2-T4 | `builder-frontend` | workhorse | workhorse | engine `core/@luana/ui-kit` (4 tier-2) | `auditor-frontend` | técnica · render-smoke del slot |

Ningún ticket es agentic → **cero flagship obligatorio** (R23 no aplica). Todos workhorse. Costo estimado: bajo-medio (tooling + tokens + slots aditivos + 1 migración FE acotada).

## Orden de spawn (DAG)

```
paralelo:  C2-T1  ‖  C2-T2  ‖  C2-T4
secuencia: C2-T2 (GREEN) → C2-T3
```

- **T-2 BLOQUEA T-3** (dep dura: vitalia consume los valores nuevos). NO arrancar T-3 hasta T-2 verde.
- T-1 + T-4 independientes (paralelos con todo).
- Multi-sesión hub: commit por pathspec. Buckets — T-1=`code` · T-2=`code:ui-kit` (design-tokens) · T-4=`code:ui-kit` (ui-kit/src) · T-3=`code:vitalia-fe`. T-2 y T-4 tocan core pero scopes distintos (design-tokens vs ui-kit/src) → paralelizables; si una sola sesión, serializar.

## Caps

- `audit_iterations` ≤ 4 · `responsible_fix_iter` ≤ 6 · wall-clock ≤ 40 min/ticket (auditor-self-fix v5).
- T-3 caveat: si el unwind revela que un consumer no tiene token canónico equivalente → NO inventar; promover a NAME del contrato (escala a T-2 / `/pm-luana`) o documentar override de identidad. NO forzar.
- Engine-edit (T-2/T-4 tocan `core/@luana`): el auditor corre **downstream-regression** (cada marca consumidora: tsc + render-smoke/arch-suite) antes de APPROVE. NO requiere promotion proposal (ADR-016 = ratificación).

## Forbidden cross-cutting (todos los tickets)

- NO tocar otras marcas salvo vitalia en T-3 (declarado).
- NO editar `core/@luana` fuera de lo declarado (T-2=design-tokens · T-4=los 4 tier-2 nombrados).
- NO reintroducir un CSS shipeado desde `@luana/design-tokens` (canon §6.8 lo descartó · auditor FAIL).
- NO fork del interno de un tier-2 (T-4 = slot/composición aditiva · ADR-016 §3).
- NO `git add .`/`-A` — pathspec. NO docker exec para lint/test (native-first).

## Handoff de cierre

`/dev-team` cierra `developed` → **G** (Chris live-verify de T-3 en dev-app vitalia + firma) → **R** (`/pm-luana` reconcilia) → `/auditor` (auditor-frontend · gate-verifier + downstream-regression) → APPROVED → `/pm-luana` merge. `/pm-luana` maneja el state del checkpoint (story sigue `developing` con C2 como scope; no lo transiciona el architect).
