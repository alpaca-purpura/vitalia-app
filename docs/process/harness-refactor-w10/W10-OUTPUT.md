# W10 · Anti-rot governance + learnings finales — Output (cierre del programa)

**Date:** 2026-06-09 · **Session:** harness-refactor W9/W10 closure (Chris-delegated autonomous) · **Branch:** `wip/vitalia` · **Status:** ✅ PROGRAMA COMPLETO (W0→W10). Machinery **67/0/0** (65→67 = +CHECK 29/30 W10 by-design).

> **North-star card:** el programa triunfa solo si `core-harness/` es REALMENTE extraíble. W8 lo probó (ledgerline); W9 cerró legacy + restart-smoke; W10 cementa los mecanismos para que NO se re-Frankensteinice. Medido: dependency-grep core-harness = 0 (CHECK 29 ahora lo asserta en CADA commit).

## 1 · Mecanismos anti-rot cementados (los 4 del charter §6 W10)

### (a) Sync-check template↔instancia (LSP)
**CHECK 30** en `validate_machinery_consistency.py`: cada `pm-{brand}` activa + `_pm-brand-template` DEBE contener los conceptos cementados (`Auto-chain rule`, `story-closure-gate`, `chris-input`, `Step 0`). Concept-based como CHECK 9 (que ya cubre spec-template raíz↔overrides). **Cazó drift REAL en su primer run:** `pm-comunify` + `pm-lupulo` no tenían § Auto-chain rule (cementada 2026-05-23, replicada solo a vitalia/nicolify) → reparado en el mismo commit. Negative-test: concepto removido → FAIL ✓.

### (b) Gate proxy-clean automatizado (el "cheap W8" en cada commit)
**CHECK 29**: dependency-grep verbatim del charter §0.5 sobre TODO `core-harness/` (excepción blessed: `agents/grep-bot.md` skip-dirs genéricos). Token de proyecto en el CORE → machinery FAIL → el commit no pasa (validator corre en pre-commit/machinery-check). Negative-test: token inyectado → FAIL ✓. **El DoD de extracción dejó de ser una medición manual de sesión y pasó a ser un invariante mecánico.**

### (c) HLP/CIL no se degrada
- El loop completo quedó **path-stable** tras el move: `/harness-issue` → `docs/process/harness-backlog.md` (project data, intacto) · CIL 4 carriles (`continuous-improvement.md` + `harness-lifecycle.md` + `tech-debt.md` viven en `core-harness/process/` con symlink-back — cargan igual) · `/harnesses-improvement` skill + cockpit `/harness` view intactos.
- Esta sesión dogfooded el loop: HB-67 capturado mid-program (mirror form-runtime-array), learnings ruteados a L2 (§3), cero 5º store.

### (d) Cadencia del merge harness→main
- **El gate canónico que CORRE es el de `main`** (D2: `install-hooks` resuelve el source de `.git/hooks` compartido desde el worktree MAIN — `git rev-parse --git-common-dir`). Mientras el programa viva solo en `wip/vitalia`, los otros worktrees corren el pre-commit viejo → **"main lags" es un paso de merge, no un bug**.
- Cadencia cementada: al cerrar un lote harness ratificado (como este programa), `/pm-luana` squash-merge `wip/{brand}` → `main` + `make install-hooks` desde main → D2 toma efecto para TODOS los worktrees. **El merge es decisión de Chris** (ver recomendaciones de cierre del programa).

## 2 · Estado final del programa (W0→W10 todos ✅)

| WS | Resultado 1-liner |
|---|---|
| W0/W0.5/W0.5-bis | Charter + Process Model + req-taking ratificados |
| W1 (P1+P2) | Rules 3-tier; always-on 2012→1741→**1310** (P2 ejecutada esta sesión: 12 domain evictions + 3 Tier-2 `paths:` + Tier-2 gate resuelto empírico) |
| W2/W3/W4/W4b | Skills/agents/hooks/scripts+cockpit tagged + conformados |
| W5a/W5b | Seam 9-slots+D1 ratificado + loader + 13 consumers wired |
| W6 | Templates+process-docs tagged; 01-spec functional-first |
| W7+EXEC | Move físico Option-C; 0 repoint; proxy-grep=2 blessed |
| W8 | Extraction test PASSING (ledgerline Go/single-brand/en-US) |
| W9 | Legacy borrado + reconcile + **restart-smoke PASS** (rules symlinkeadas cargan always-on en sesión fresca) |
| W10 | CHECK 29/30 con dientes + HLP/CIL verificado + cadencia merge + learnings → CIL |
| W7-tail | architect-{be,fe,agentic} rehomed a `architect/references/` (validator+baseline+templates+5 skills repointed, mismo commit) |

## 3 · Learnings del programa → CIL L2

Consolidados en `docs/learnings/tooling/2026-06-09-harness-refactor-program-close.md` (carril L2 — no 5º store). Los 8 durables del kickoff + los nuevos de esta sesión (restart-smoke como prueba pasiva de sesión-fresca · headless `claude -p` como banco de pruebas A/B de mecanismos de carga · sync-check que caza drift en su primer run = el gate paga su costo el día 1 · `globs:` muerto vs `paths:` vivo).

## 4 · Pendientes documentados (NO bloquean el programa)
- **Tier-2 candidatos restantes:** `backend-migrations` (write-time risk, conservador) · `frontend-visual-fidelity` (canon gates po-ux que no lee `frontend/src`).
- **Budget core:** 890 líneas de las 21 core rules = el piso actual; bajar más = decisión de slim-manifest del plugin (SessionStart inyecta 3 hard rules; resto vía `/harness:bootstrap`).
- **HB-67** mirror form-runtime-array (brand-expert vs offer-expert) — pase corto dedicado.
- **HB-65** 6 domain-skills pre-reorg topology-alignment — pase dedicado.

## 5 · Pointers
- charter §6 markers W9 ✅ W10 ✅ · `W9-OUTPUT.md` · `harness-architecture-guide.md` (deliverable Chris) · `core-harness/ADOPTING.md` (deliverable adopción).
