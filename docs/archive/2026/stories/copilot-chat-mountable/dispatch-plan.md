# Dispatch plan — copilot-chat-mountable (platform technical-story)

## autonomous_mode
- value: false               # Chris ratifica el DISEÑO (este ready-package) antes del build (proposal §4: "ratificación final antes de commitear código a core/")
- chain_if_true: [/dev-team → /auditor → /pm-luana merge]
- caps: {iterations: 10, audit_iter: 4, walltime: 90min}

## Worktree
- ~/Proyectos/luana-core-copilot-mountable (wip/core-copilot-mountable, base main 2b3450aa)
- Setup builder T-1: `uv sync` en el worktree (venv propio — editable installs apuntan a este checkout).

## Ticket → Agent → Model matrix
| T-id | Title | Surface | Agent | Model | Notas |
|---|---|---|---|---|---|
| T-1 | config+database lazy + shim | BE core | builder-backend | workhorse | root unblock |
| T-2 | migrar import-path chat → get_settings() | BE core | builder-backend | workhorse | driver = test de efecto |
| T-3 | chat.py contract + bump + CHANGELOG + doc | BE core | builder-backend | workhorse | — |
| T-4 | completar C (~48 off-path) + deprecar shim | BE core | builder-backend | workhorse | mecánico masivo |
| T-5 | R3 4 marcas + /chat 401/200 | BE verif | builder-backend | workhorse | DoD técnica |

(Ningún ticket agentic → ningún flagship R23. Todo workhorse.)

## DAG
T-1 → T-2 → {T-3 ∥ T-4} → T-5

## Punto de corte recomendado
- **T-1+T-2+T-3 ya desbloquean comunify** (el shim cubre los off-path). T-4 (completar C) puede shipear en el mismo lote o como follow-up — Chris decide al ratificar.

## Invocation
- Manual: `/dev-team <brand>: platform, story: copilot-chat-mountable, ticket: T-1` (desde el worktree core, tras `uv sync`)
- Autonomous: `echo 'autonomous_mode: true' >> checkpoint.md` (NO recomendado — Chris quiere ratificar el diseño + ver la blast-radius del cambio a luana_core_platform antes del build)
