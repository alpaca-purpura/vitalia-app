# Dispatch plan — platform/platform-lift-shell-chrome-ui-kit

> Owner: `/architect` (Step 7.5). Consumer: `/dev-team` Step 0.7. SSoT schema: `.claude/rules/architect-autonomous-mode.md`.

## autonomous_mode
- value: **true**                  # ratificado Chris 2026-06-11 VERBATIM ("RATIFICO autonomous_mode: true verbatim para toda la cadena: refinar→arch→build→audit→merge; trabajá hasta el done sin pausas. Escalá SOLO breaking-change imposible de decidir solo — y aun así documentá+parqueá esa pieza y seguí con el resto.")
- chain_if_true: [/dev-team → /auditor → /pm-luana merge]
- ratified_by: chris
- ratified_at: 2026-06-11
- caps: { max_iterations_per_ticket: 10, self_fix_iter: 6, audit_iterations: 4, max_wall_clock_minutes: 240, on_cap_exceeded: "documentar + parquear pieza + HANDOFF-next-session.md + seguir con el resto (Chris verbatim — NO state=blocked de toda la story)" }

> **autonomous_mode HARD-false override (architect resolution):** la rule `autonomous-mode.md` marca HARD-false "story toca core / cross-brand". **Esta story ES la ejecución del proposal `2026-06-01-lift-shell-organism` ACCEPTED (ratificado Chris 2026-06-06) + autonomous ratificado con conocimiento explícito** (autorización /pm-luana en el prompt del caller). La intención del gate (edit a engine necesita aprobación) está SATISFECHA: el target es `core/@luana/ui-kit` (package TS sancionado), NO `core/luana-core-*/src/` (Python engine, sigue prohibido). Cross-brand (vitalia+nicolify) está sancionado por la proposal (convergencia RN-7). **MANTENGO autonomous_mode: true.** Escape valve Bif-1/SC-9: pieza indecidible → parquear + HANDOFF + seguir (no bloquea la story entera).

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | primary_agent | Model | Est. time |
|---|---|---|---|---|---|
| T-K1 | Kit scaffolding (deps+factory+types) | FE-kit | builder-frontend | inherit | ~30 min |
| T-K2 | Kit chrome port (fixes v4 sagrados) | FE-kit | builder-frontend | inherit | ~70 min |
| T-K3 | Kit barrel+tests+CHANGELOG | FE-kit | builder-frontend | inherit | ~35 min |
| T-V1 | Vitalia re-wire (mount+store+@source) | FE-vitalia | builder-frontend | inherit | ~30 min |
| T-V2 | Vitalia delete+allowlist+suite 68+7 | FE-vitalia | builder-frontend | inherit | ~50 min |
| T-N1 | Nicolify converge | FE-nicolify | builder-frontend | inherit | ~50 min |
| T-G | Gates+live-verify+proposal migrated | FE-platform | builder-frontend | inherit | ~30 min |
| **Total** | — | — | — | inherit | **~5 h (cap 240 min — si supera: parquear residual + HANDOFF)** |

> **model_preference: inherit** en TODOS (Chris verbatim: subagents heredan Fable 5 de la sesión — NO especificar sonnet/opus). Surface FE no-agentic → R23 (Opus obligatorio agentic) NO aplica.

## DAG dependencies
```
T-K1 → T-K2 → T-K3 → T-V1 → T-V2 → T-N1 → T-G
(kit primero con tests propios → vitalia re-wire+borrado+suite → nicolify converge → gates finales)
```
Secuencial estricto: el kit DEBE estar verde antes de que vitalia consuma; vitalia DEBE estar verde (el contrato e2e) antes de converger nicolify; gates al final.

## Playwright visual scope discipline
- story_scope_routes: ["/{tenantId}/{agent}/{subtab}", "/{tenantId}"]
- story_scope_components: [ShellLayout, SupervisorSidebar, SupervisorCollapsedStrip, SupervisorHistory, ChatPanel, ChatHeader, Ribbon, SubTabsBar, TopBarShell (todos del kit)]
- forbidden_visual_changes: ["vitalia/frontend/src/features/**", "nicolify/frontend/src/features/**", "core/luana-core-*/src/**", "{brand}/backend/**", "{brand}/frontend/src/components/ui/**"]
- non_egoísmo: bug visible en feature/ruta NO tocada → reportar en T-{n}-impl-log § Cross-story observed bugs, NO arreglar inline.

## DoD live-verify gate (Critical Rule #37)
- Story **técnica** (refactor) PERO live-verify OBLIGATORIA (Chris verbatim, SC-8): `/dev-team` (T-G) ejerce en vitalia :3002 (Chrome MCP o Playwright autenticado dr.demo@vitalialat.com): colapsar→strip→reabrir · historial push 280 · drag clamp · "+" nueva conv · pill @[24rem] + grid sin recorte (gate Tailwind scan). Lee logs BE/consola.
- Registra `dod_live_verified: true` + `dod_evidence` (writes ejercidos + efecto DOM + persistencia reload + 0 pageerror/console-error/api>=400 + 0 traceback) en checkpoint.
- `demo_required: false` (autonomous, Chris ratificó `chris_verify.required: false`) → NO requiere signoff humano en G. PERO `/pm-luana` REFUSE merge sin `dod_live_verified: true` + `dod_evidence`.

## Escape valve (Bif-1 / SC-9 — Chris verbatim)
Pieza del chrome imposible de parametrizar sin breaking-change indecidible → **documentar + parquear esa pieza (queda brand-local) + HANDOFF-next-session.md + seguir con el resto del lift**. NO bloquear la story entera. Candidatos: `SubSubTab.tsx` (solo nicolify), N3 nicolify divergente (Open Q1 — ortogonal, no se migra acá).

## Build operativa (verbatim 05-guidelines)
- COMMIT INCREMENTAL por pathspec apenas un bloque verde (builders mueren ~140 tool-uses) · `git commit <rutas>`, NUNCA `-A`.
- `SCOPE_GATE_SKIP=1` con razón en body (lift sancionado, proposal accepted) — M13 bloquea mix core+vitalia+nicolify.
- Allowlists arch en el MISMO commit del move (shrink-only).
- pnpm: host-install vitest/tsc · container-install e2e (symlink-war).
- Builder muerto → verificar tree+commits + spawn agent nuevo (NO restart from scratch).
