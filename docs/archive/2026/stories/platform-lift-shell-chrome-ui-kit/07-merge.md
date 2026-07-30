# 07-merge — platform-lift-shell-chrome-ui-kit

> **Fecha:** 2026-06-11 · **Merge por:** /pm-luana (cadena autónoma ratificada Chris verbatim 2026-06-11 — refinar→arch→build→audit→merge sin pausas) · **Verdict auditor:** APPROVED (CHECKPOINTS.md C1-C5) · **chris_verify:** N/A (autonomous_mode, G saltada por opt-in)

## § 1 — Gherkin verification matrix

Copia canónica: `06-audit/gherkin-matrix.md` — **SC-1..SC-8 PASS · SC-9 N/A** (Bif-1 escape-valve no ocurrió: cero pieza parqueada, sin HANDOFF-next-session.md). Evidencia por SC mapeada a gate-output.json (12/12) + run e2e bcahr2m2j + dod_evidence.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/shell-core-hardening/ \
  e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts
# → 84 passed · 1 skipped (test.fixme deuda inbox-dark CIL L3) · 0 failed (2.5m)
# resizer-matrix.spec.ts standalone → 7/7 (0 retries)
```

Real-backend (FE:3002/BE:8002), Clerk autenticado, fixture base.ts anti-burbuja. **Contra el chrome CONSUMIDO de `@luana/ui-kit`** (chrome brand-local borrado).

## § 3 — Capabilities updated/created

- `cap_change_type: fix` + `cap_target: null` — chrome transversal `map_zone: infraestructura` (precedente vitalia-shell-core-hardening). Sin cap YAML nueva. El inventario del kit se versiona en `core/@luana/ui-kit/CHANGELOG.md` 0.4.0.

## § 4 — Modules MD refreshed

- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` → **v1.5**: el chrome vive en `@luana/ui-kit` (implementación); el contrato sigue siendo SSoT de comportamiento + brand data.
- `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md` → **state: migrated** (este merge).
- `docs/process/harness-backlog.md` → HB-68 (verde-fantasma e2e del hardening — upstream deficiency).

## § 5 — How to verify (reproducible)

```bash
# Kit
cd core/@luana/ui-kit && npx vitest run            # 259/259 · organism tsc 0
grep -riE '#01b2f8|valeria|vitalia|nicolify' core/@luana/ui-kit/src/organism --include='*.ts*' | grep -viE 'CHANGELOG|origen|port|verbatim|e\.g\.|contract'   # 0 en lógica
# Vitalia (consume kit)
cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run src/
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-core-hardening/
# Nicolify (converge — mirror muerto)
cd nicolify/frontend && npx tsc --noEmit && npx vitest run src/    # 514/514
comm -12 <(ls vitalia/frontend/src/components/shared/shell-organism/) <(ls nicolify/frontend/src/components/shared/shell-organism/) | grep -iE 'Sidebar|Chat|Ribbon|Layout|TopBar'   # vacío
```

## Resumen de entrega

**Liftado a `core/@luana/ui-kit` v0.4.0 (organism/shell, 30+ componentes brand-agnostic):** ShellLayout(Client) con fixes v4 SAGRADOS verbatim (key-remount A/B/C, retry-rAF isCollapsed, collapsedSize 44px, push ±actual floor min+hist, Group siempre montado D1-D5, shellReady), Supervisor{Sidebar,CollapsedStrip,History}, ChatPanel/Chat*, Ribbon(Tab), SubTabs/SubSubTabs, TopBarShell (slots), AppPanelSlot, useViewportGuard, createShellStore (SSR-safe vía @luana/hooks, migrate inyectable). Todo brand-specific por props+CSS vars (supervisorName, agentCatalog, getAgentClasses, testIds, slots).

**Vitalia:** consume vía ShellLayoutWire (testIds legacy, keys localStorage conservadas SC-6, @source JIT); chrome local BORRADO; allowlist mirror → ∅. **Nicolify:** converge — máquina legacy (luanaState/LuanaRail/ShellModeToggle) retirada (30 archivos), Wire con catálogo Luana/Abel/Brenda/Christian/Sara/Norvil, migrate legacy→v2. **Mirror cross-brand MUERTO.**

**Hallazgos de proceso:** (1) edge-redirects N3 — 4 redirect() in-render adicionales movidos al proxy 307 (el supuesto "solo landing" del hardening era falso; con el kit el Rendered-more-hooks era determinista); (2) **verde-fantasma del hardening** (HB-68): runs e2e "verdes" escaneaban shell colgado → axe 0-violations fantasma + 2 asserts imposibles; el lift los destapó y corrigió el harness al contrato real; (3) deuda destapada: ~10 contrastes dark en feature inbox (fixme rastreado, CIL L3) + fixes WCAG quirúrgicos aplicados (mateo D20, cyan palette, aria roles).

**Deuda ruteada (no bloquea):** CIL L3 inbox-dark contrast · CIL L3 tsc kit-wide test-types (116 pre-existentes) · HB-68 gate anti-shell-colgado para runs axe · symlink-war container (CIL L1 ya trackeada, agravante lockfile-copy confirmado).
