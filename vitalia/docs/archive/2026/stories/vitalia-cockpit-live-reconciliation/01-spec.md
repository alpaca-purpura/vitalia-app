---
story_id: vitalia-cockpit-live-reconciliation
brand: vitalia
type: technical-story
state: refined
po_version: 2
cap_target: ops.live-reconciliation-sweep
cap_change_type: new
matrix_home: vitalia/docs/domains/ops/live-reconciliation.md
priority: high
ratified_by_chris: true
---

# 01-spec — Reconciliación cockpit ↔ realidad live (diagnóstico + reparación-o-mapeo)

## Resumen ejecutivo

El cockpit muestra ~59 capabilities `status: live`, pero la realidad de la app diverge: al entrar a `:3002` sale **500** y la mayoría de las caps "live" no están verificadas. Esta historia técnica **(1)** repara el boot del dev-stack, **(2)** recorre con Playwright cada superficie navegable produciendo una matriz cap↔realidad con evidencia, **(3)** repara inline lo acotado (gates verdes) y mapea lo grande a stories de Fase 2, y **(4)** corrige el ledger para que el cockpit diga la VERDAD. **NO reconstruye** las ~47 caps slice-1 superseded (eso es la Fase 2 = 20 stories).

**Resultado medible:** `:3002` 200 + las caps live-accesibles verificadas verdes + `LIVE-RECONCILIATION-MATRIX.md` (SSoT) + ledger reconciliado (cross_check_3) + backlog F2 priorizado con evidencia.

## Context (diagnóstico previo · repro_verified)

- **Backend `:8002/health` → 200.** Frontend `:3002/` → **500**: `Module not found: Can't resolve '@luana/hooks/use-store-hydration'` (en `ShellOrganismLayoutClient.tsx`).
  - NO es bug de código: el export existe (`@luana/hooks@0.2.0`, commit `135af14a`). Es **drift de infra del dev-stack** — el container frontend bind-montea solo `vitalia/frontend`, no `core/`, y el linking workspace `@luana/*` quedó stale. `pnpm install` en el container falla (`ERR_PNPM_WORKSPACE_PKG_NOT_FOUND`).
- **Foto del ledger (computada `scripts/compute_capability_status.py --brand vitalia`, 2026-05-29):** 67 caps → **stub=55 · declared-live=6 · verified-live=1 · partial=5 · drift=0**. Solo **1 cap está realmente verified-live**.
- **Prior art:** `vitalia/docs/learnings/2026-05-27-live-audit.md` mapeó 71 caps → ~24 navegables (shell-organism) / ~47 slice-1 superseded / ~10 infra. Esta historia lo operacionaliza.
- **Tooling reusable (NO recrear):** `scripts/{compute_capability_status,reconcile_capabilities,validate_code_cap_bidirectional,generate_code_to_cap_index}.py` + suite `vitalia/frontend/e2e/` (~30 specs).

## Scope ratificado (Chris 2026-05-29)

- **Entregable:** "honesto + verdes lo real" — A (reparar runtime/infra) + B (reconciliar ledger). C (reconstruir slice-1) = Fase 2, FUERA de scope: esta story solo produce el mapa priorizado.
- **Límite "fácil" = agresivo inline:** reparar inline todo lo razonablemente acotado (multi-archivo acotado + lógica simple) MIENTRAS los gates queden verdes (lint/tsc/mypy/arch-fitness/jscpd/tests). Se mapea a story solo: reconstruir cap slice-1, features nuevas, o lo que requiera test nuevo de comportamiento + rompa gates.

## Definiciones operativas

- **Superficie navegable:** ruta del shell-organism alcanzable con login Clerk (`/[tenantId]/(shell-organism)/...` + `[agent]/[subtab]` + agentes Valeria/Lisa + topbar/theme/tenant-switcher + `/sign-in`). Lista semilla derivada de `find app -name page.tsx` + `RIBBON_SUBTABS`.
- **Verdict de sweep** (por superficie): `OK` (carga + interacción base sin error) · `ROTO` (500 / console-error / crash / acción falla) · `INACCESIBLE` (ruta declarada pero no alcanzable desde nav) · `SIN-UI` (cap live sin ruta en shell-organism = slice-1/infra).
- **Verdict técnico** (por cap con código): `cumple` · `easy-fix` (acotado, gates verdes) · `map` (grande → story Fase 2).
- **Matriz** `LIVE-RECONCILIATION-MATRIX.md`: filas = caps; columnas = `cap_id | declared_status | computed_status | ruta | sweep_verdict | evidencia | technical_verdict | acción | story_mapeada`.

---

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `boot-restored` (`type: happy`)
```gherkin
Given el dev-stack vitalia con frontend devolviendo 500 por @luana/hooks no resuelto
When se aplica el fix de infra Fase 0 (remount core/ en el compose del frontend O rebuild de imagen) y se aplican migraciones pendientes (alembic upgrade head)
Then GET http://127.0.0.1:3002/ responde 200 (tras redirect Clerk a /sign-in 200)
And el import '@luana/hooks/use-store-hydration' resuelve sin error en los logs del container
And el login Clerk con storage state válido carga el shell-organism (topbar + ribbon + Valeria sidebar visibles)
```
graders:
- `{ type: shell, cmd: "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:3002/sign-in", expect: "200" }`
- `{ type: shell, cmd: "docker logs luana-dev-vitalia_frontend_dev-1 --tail 50 2>&1 | grep -c 'Module not found'", expect: "0" }`
- `{ type: playwright, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts", expect: "PASS" }`

### Scenario 2 — `surface-broken-flagged` (`type: negative`)
```gherkin
Given una superficie navegable que el cockpit declara live pero que falla en runtime (500/console-error/acción rota)
When el sweep Playwright la recorre
Then la fila de esa cap en LIVE-RECONCILIATION-MATRIX.md queda sweep_verdict=ROTO
And adjunta evidencia (screenshot + console log + status HTTP + selector/acción que falló)
And NO se marca esa cap como verde ni se cierra la story como si funcionara
```
graders:
- `{ type: artifact, path: "vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/LIVE-RECONCILIATION-MATRIX.md", contains: "sweep_verdict" }`
- `{ type: review, check: "toda fila ROTO tiene columna evidencia no vacía con ruta a screenshot/log" }`

### Scenario 3 — `superseded-cap-detected` (`type: edge`)
```gherkin
Given una cap con status: live cuyo código existe pero cuya ruta UI fue reemplazada por shell-organism (slice-1 superseded)
When el sweep no encuentra ruta navegable que la sirva
Then la fila queda sweep_verdict=SIN-UI
And en Fase 3 su frontmatter se reconcilia (status discriminado live-superseded + replaced_by: <cap_id> cuando aplique)
And se registra en el backlog F2 con la story que la reconstruiría (F2-S2..S22), sin reconstruirla en esta story
```
graders:
- `{ type: shell, cmd: ".venv/bin/python scripts/compute_capability_status.py --brand vitalia --strict; echo $?", note: "post-reconcile: 0 caps en estado 'drift'; declared-live solo en infra-only justificadas" }`
- `{ type: review, check: "ninguna cap reconstruida (cero código nuevo de feature slice-1 en el diff)" }`

### Scenario 4 — `false-green-resisted` (`type: adversarial`)
```gherkin
Given la tentación de marcar una cap como verified-live porque su ruta carga 200 aunque sus scenarios sean stub o su flujo de negocio no se cumpla
When se evalúa el cierre de la cap
Then el criterio de "verde" exige: ruta OK + ≥1 scenario con e2e que existe y pasa (cross_check_3 HARD) + flujo de negocio del spec original cumplido + estándares (tenant isolation, a11y declarada, visual fidelity)
And una ruta que solo renderiza el cascarón sin cumplir reglas de negocio se marca ROTO o easy-fix, NUNCA verde
And el ledger NO se infla: status: live solo sobrevive si computed_status ∈ {verified-live} o es infra-only declarada explícita
```
graders:
- `{ type: shell, cmd: ".venv/bin/python scripts/validate_code_cap_bidirectional.py 2>&1 | tail -5", note: "cross_check_3 (scenarios→e2e existen) sin drift para caps que queden live" }`
- `{ type: review, check: "cada cap marcada verde cita el path del e2e que la verifica" }`

### Scenario 5 — `network-failure` (`type: edge`, sub: network_failure)
```gherkin
Given una superficie cuyo backend o dependencia (payment/fiscal stub MSW) no responde durante el sweep
When Playwright la recorre
Then se distingue "fallo de runtime real de la UI" (ROTO) de "dependencia stubbeada/ausente esperada" (anotado, no ROTO)
And la matriz documenta cuál dependencia faltó para no contar como falso ROTO
```
graders:
- `{ type: review, check: "filas con dependencia stub (payment/fiscal Option A MSW) anotadas, no marcadas ROTO por eso" }`

### Scenario 6 — `accessibility` (`type: edge`, sub: accessibility)
```gherkin
Given las caps que declaran criterios de accesibilidad (a11y) en su spec/cap YAML (ej. ribbon tablist, valeria-chat)
When el sweep corre los specs a11y existentes (vitalia/frontend/e2e/a11y/)
Then se reporta el estado a11y real (PASS/FAIL/timeout) en la matriz
And los timeouts conocidos (valeria-agenda, lisa-marca a11y >5min del audit 2026-05-27) se investigan: si es data-testid drift → easy-fix; si es bug → ROTO + map
```
graders:
- `{ type: playwright, path: "vitalia/frontend/e2e/a11y/", expect: "ejecutado, resultado registrado en matriz (PASS/FAIL/timeout con causa)" }`

### Scenario 7 — `ledger-honest-after` (`type: edge`, sub: empty_state)
```gherkin
Given el ledger post-reconciliación
When se regenera la vista del cockpit (compute_capability_status + reconcile_capabilities)
Then el cockpit muestra el computed_status real por cap (verified-live / partial / declared-live / superseded / wip), no un "live" uniforme engañoso
And el conteo "live verde" del cockpit coincide con las caps que el sweep verificó verdes (sin sobre-declaración)
```
graders:
- `{ type: shell, cmd: ".venv/bin/python scripts/reconcile_capabilities.py --brand vitalia --validate-ledger; echo $?", expect: "0" }`
- `{ type: artifact, path: "vitalia/docs/product/capabilities/_status-computed.json", note: "verified-live count == caps marcadas verdes en la matriz" }`

> **Sub-categorías N/A (con justificación):** `race_condition`, `concurrent_users`, `large_dataset`, `i18n` no aplican como criterios de aceptación de esta historia — es un harness de diagnóstico + reconciliación de ledger, no una feature CRUD con datos/concurrencia propia. Si el sweep DETECTA un bug de esas categorías en una cap concreta, se registra como fila ROTO/easy-fix de esa cap, no como scenario de esta story.

---

## Non-functional requirements

- **Disciplina de scope (HARD):** cero reconstrucción de caps slice-1. El diff de esta historia no agrega features nuevas; solo: fix infra Fase 0, fixes inline acotados (gates verdes), specs e2e de diagnóstico, edición de frontmatter de caps (status/replaced_by), y los artefactos de matriz/backlog.
- **Gates verdes obligatorios** para cualquier fix inline: `ruff` + `tsc --noEmit` + `eslint` + `mypy` (si BE) + `arch-fitness` (ratchet) + `jscpd` + tests existentes. Un fix que rompe un gate → revertir y mapear.
- **Evidencia auditable:** toda fila de la matriz con verdict ROTO/easy-fix adjunta evidencia concreta (screenshot path, console/network log, o test path). Sin evidencia → no cuenta.
- **No-egoísmo / anti-isla:** si el sweep revela un bug en una superficie fuera del scope reparable, se documenta en la matriz + backlog, no se ignora (anti-orphan-integration.md).
- **Two-stage tickets:** Fase 0 + Fase 1 (boot + sweep) se especifican concretos en `06-tickets.yaml`; los tickets de reparación de Fase 3 se generan a partir de los findings reales de la matriz (no se pueden enumerar antes del sweep).

## Constraints técnicos heredados

- `tenant-isolation` (todo query/route tenant-scoped) · `frontend-fsd` + `frontend-visual-fidelity` (sweep verifica fidelidad de las caps live) · `spanish-text` (microcopy neutro) · `backend-ddd` · `e2e-testing` (Playwright NATIVE Linux, NUNCA `make e2e*` Docker; preflight `scripts/e2e-preflight.sh`) · `test-design-doctrine` (batería por naturaleza) · `capability-protocol` cross_check_3 (HARD).

## Cross-module impact

Toca transversalmente: FE shell-organism (boot), infra dev-stack (compose mount), ledger de capabilities (todos los módulos), suite e2e. NO toca `core/luana-core-*/src/` (si el fix Fase 0 requiere tocar el compose o `@luana/hooks` build → es consumo/infra, no edición de lógica engine; si requiriera editar engine → STOP + `/pm-luana`).

## Decisiones ratificadas (Chris 2026-05-29)

- **Q1 — Fix Fase 0 = remount `core/` en `vitalia/docker-compose.dev.yml`.** Montar `core/@luana/*` en el container frontend (bind mount declarativo, persistente). Ataca la causa raíz (el container nunca debió quedar sin `core/`) y evita rebuilds en cada bump de `@luana/*`. El ticket Fase 0 edita el compose + corre `pnpm install` en container + restart + `alembic upgrade head`. Gate: `:3002` 200 + import resuelve + `Module not found`=0 en logs.
- **Q2 — Alcance sweep = shell-organism profundo + anotar 3 externas.** Barrido profundo de todo el shell-organism (agentes, sub-tabs, sub-sub-tabs, topbar, theme, tenant-switcher). Las 3 superficies fuera de shell (**admin Streamlit** en subdominio, **`/public/[clinic-slug]`** landing, **`/onboarding/wizard`**) se ANOTAN en la matriz con su estado observado (sin barrido profundo, distinto stack/auth). Si una anotación revela ROTO evidente → se registra, no se ignora (anti-isla).
- **Q3 — Matriz = artefacto vivo recurrente.** Vive en **`vitalia/docs/domains/ops/live-reconciliation.md`** (no efímero en story). Es la capability nueva `ops.live-reconciliation-sweep` (metodología + matriz versionada, regenerable en cada audit futuro). Ya `promotable: candidate` cross-brand (replicable a nicolify/comunify/lupulo — el audit 2026-05-27 § 8 ya dio el workflow generalizable). La story produce v1 de ese artefacto; futuros audits lo actualizan.

## Próximo paso

Spec ratificada v2 (`ratified_by_chris: true`). Service/technical-story → directo a `/architect` (ready package: 03-arch + 04-validators + 05-guidelines + 06-tickets, con tickets two-stage: Fase 0 boot + Fase 1 sweep concretos; reparación Fase 3 generada post-sweep).

## Changelog
- v2 (2026-05-29) — Q1-Q3 ratificadas por Chris. Fix Fase 0 = remount core/. Sweep = shell-organism + anotar 3 externas. Matriz = artefacto vivo `vitalia/docs/domains/ops/live-reconciliation.md` (cap ops.live-reconciliation-sweep). state→refined.
- v1 (2026-05-29) — draft inicial /po. Scope ratificado Chris. 7 scenarios (4 core + network/a11y/empty + N/A justificadas).
