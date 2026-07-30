# T-7-result — E2E suite SC-1..22 + race reactivado + regression ambos temas

**State:** pushed · **Builders:** builder-frontend ×3 continuations (contexto e2e-debug es caro) + fix quirúrgico final + orquestación gates. Commits incrementales preservaron todo.

## Commits

| SHA | Contenido |
|---|---|
| `00b3e259` | 20 specs `e2e/regression/shell-core-hardening/` + `shell-hardening.fixture.ts` + `EntityWorkspacePage.ts` POM + `ShellLayoutPage` ext + race reactivado |
| `93ccf620` | **Fix producto #1:** `next.config.ts` rewrites `/api`+`/public`→BE (bug global conocido: client hooks fetch relativo → 404, caso useTenants) + **fix #2:** strip `collapsedSize={isLg ? stripPct : 0}` (SC-5) + selectors |
| `cd99265d` | topbar-order async TenantSwitcher + collapse-strip disambiguation |
| `e1a0bad0` | **Fix producto #3:** drag below min clampea a 320 (no colapsa al strip) — `collapsible` dinámico: `closed/!isLg → true` (collapse programático strip) · `chat abierto → false` (lib clampa nativo). RN-8/RN-9. CAZADO por el race spec reactivado |

## Resultados suite (real-backend, stack dev FE:3002/BE:8002, fixture base.ts anti-burbuja)

| Run | Resultado |
|---|---|
| `e2e/regression/shell-core-hardening/` (20 specs · SC-1..21) | **52 passed + 2 flaky (pass-on-retry)** · 4.4m · exit 0 |
| `resize-and-state.spec.ts` (race SC-22/AC-14 reactivado + SC-4) | **8/8** (post fix e1a0bad0; pre-fix 1 RED legítimo que cazó el bug #3) |
| Non-regresión post-fix: collapse-strip + default-30-70 + drawer | ✅ |
| Vitest shell-organism | 503/503 |

**2 flaky (pass-on-retry, para el auditor):** `regression-cross-tab.spec.ts` [dark] lisa/marca render + agent-colors/logo gradient. Hipótesis: timing de theme-hydration. NO masked — documentado para adjudicación en audit.

## Cobertura SC

SC-1..SC-19 (backbone) + SC-20 dark per-subtab (axe AA en dark ✓) + SC-21 soft-nav loop ×15 (board→recuperar via next/link, consola limpia) + SC-22 race drag inmediato (reactivado, verde). Mapping detallado: specs nombrados por SC en el dir.

## Bugs de producto encontrados + arreglados por la suite (TDD e2e = RED real)

1. **Rewrites `/api`→BE faltantes** (bug global flaggeado por story embudo: useTenants 404). → next.config.ts.
2. **Strip 44px colapsaba a 0** (SC-5). → collapsedSize dinámico.
3. **Drag below min colapsaba al strip** (violaba RN-8/RN-9). → collapsible dinámico.

## Skills consulted (must_load enforcement v4.1)

playwright-expert ✅ (auth fixture/storageState + trace debugging) · frontend-expert ✅ · tdd-mandatory ✅ · definition-of-done-live-verify ✅ (suite ES real-backend; live-verify #37 manual va en T-8).
