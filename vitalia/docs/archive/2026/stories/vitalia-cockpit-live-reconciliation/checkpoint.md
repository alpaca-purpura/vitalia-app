---
story_id: vitalia-cockpit-live-reconciliation
type: technical-story
agent_owner: config
module: platform
cap_target: ops.live-reconciliation-sweep   # new — la matriz + metodología sweep como capability repetible
cap_change_type: new                          # + acción de mantenimiento cross-cutting: corregir status de caps sobre-declaradas (documentar en 07-merge)
state: done
release: F2
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # no es story sub-tab/feature (ver 03-arch § Architecture Decisions)
matrix_home: vitalia/docs/domains/ops/live-reconciliation.md
priority: high
ratified_by_chris: true             # scope (2026-05-29) + spec v2 ratificada (Q1-Q3)
parallel_safe: false               # toca FE + BE + infra dev-stack + ledger caps — serializar
repro_verified: true               # 500 reproducido (ver § Diagnóstico)
autonomous_mode: true              # ratificado Chris 2026-05-29 (override de la recomendación manual)
autonomous_mode_chain: [dev-team, auditor, pm-merge]
autonomous_mode_ratified_by: chris
autonomous_mode_ratified_at: 2026-05-29T16:18:00-05:00
autonomous_mode_caps:
  max_iterations_per_ticket: 10
  max_audit_iterations: 4
  max_total_cost_usd: 6.00
  max_wall_clock_minutes: 150
  on_cap_exceeded: "state=blocked + escalate Chris"
last_modified: 2026-05-29
phase: DONE_MERGED_TO_WIP
last_artifact: 07-merge.md
gherkin_matrix: 06-audit/gherkin-matrix.md
audit_verdict: APPROVED
merge_to_main_gated: true   # squash-merge wip/vitalia→main pendiente Chris (sesión paralela activa + staging manual)
t1_done: true
t2_done: true
t3_done: true
next_action: "/pm-vitalia merge → 07-merge.md 5 secciones + Fase F.3 cap ledger (new ops.live-reconciliation-sweep) + git mv archive → state reviewing→done"
---

# Reconciliación cockpit ↔ realidad live · diagnóstico + reparación-o-mapeo

> **Origen:** sesión 2026-05-29. Chris: "lo que veo como `live` en mi cockpit no está realmente live — cuando entro a la solución me salen errores. Quiero recorrer funcionalidad por funcionalidad, con Playwright, capturar todo lo que aparece como funcionando pero no funciona, revisar técnicamente cada una contra estándares, reparar lo fácil y mapear el resto. Al término debo tener la solución funcionando con lo que supuestamente ya debe estar live."

## Intent verbatim de Chris

1. **Fase 1 (diagnóstico):** recorrer con Playwright TODO lo marcado live → capturar qué no funciona pero aparece como que sí.
2. **A la par:** por cada funcionalidad, revisión técnica (¿cumple estándares FE visual+técnico, BE, arquitectura, reglas de negocio, flujo funcional, accesibilidad declarada?).
3. **Reparar lo fácil inline; mapear lo difícil** a stories de remediación.
4. **Resultado:** solución funcionando con lo que el cockpit declara live (o un plan honesto para lo que falta).

## Prior art scan (anti-duplication-refining · ejecutado 2026-05-29)

| Fuente | Hallazgo | Decisión |
|---|---|---|
| `vitalia/docs/learnings/2026-05-27-live-audit.md` | **Prior-art directo.** Audit del 2026-05-27 ya mapeó 71 caps `status: live` vs realidad UI: **~24 live-accesibles (shell-organism), ~47 slice-1 legacy superseded, ~10 infra-only.** Produjo lista priorizada C1-C3 / I1-I4 / L1-L3 + propuso schema `ui_paradigm` + `replaced_by`. | **REUSE como mapa base.** Esta story OPERACIONALIZA ese audit con sweep sistemático per-cap + fix/map. NO re-descubrir desde cero. |
| `vitalia/docs/learnings/2026-05-25-mockup-playwright-audit-cycle.md` | Patrón Playwright real-browser inspect pre/post build. | Aplicar técnica de inspección DOM/a11y/visual al sweep. |
| `scripts/{reconcile_capabilities,compute_capability_status,validate_code_cap_bidirectional,generate_code_to_cap_index}.py` | Tooling de reconciliación cap↔código YA existe. | **CONSUMIR** estos scripts para la parte de ledger, NO recrear. |
| `vitalia/frontend/e2e/` (≈30 specs: auth, shell-organism, a11y, visual, admin, regression) | Suite Playwright sustancial ya existe. | **EXTENDER** la suite con specs de diagnóstico per-superficie, no empezar de cero. |
| `docs/process/lifecycle.md` cross_check_3 (HARD) | Doctrina: cap NO puede ser `status: live` sin ≥1 scenario + e2e que exista. | Base normativa para corregir el ledger sobre-declarado. |

**Net del scan:** NO es net-new. Es operacionalización + remediación de un audit ya mapeado, apoyado en tooling existente. Cero mirror cross-brand.

## Diagnóstico inmediato (repro_verified)

- **Backend `:8002/health` → 200 OK.** Sano.
- **Frontend `:3002/` → 500.** Causa raíz: `Module not found: Can't resolve '@luana/hooks/use-store-hydration'` (importado por `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx`).
- **NO es bug de código:** el export existe (`core/@luana/hooks/src/use-store-hydration.ts`, declarado en `exports`, promovido a `@luana/hooks@0.2.0` — commit `135af14a`). Es **drift de infra del dev-stack**: el container frontend solo bind-montea `vitalia/frontend` (NO `core/`), y el linking workspace de `@luana/*` quedó stale tras el bump de versión. `pnpm install` en el container falla (`ERR_PNPM_WORKSPACE_PKG_NOT_FOUND` — `core/@luana/*` no presente en el mount).
- **Implicación:** el 500 bloquea CUALQUIER sweep Playwright. **Fase 0 = arreglar el boot del dev-stack** (remount `core/` en el compose del frontend, o rebuild de imagen) ANTES de poder diagnosticar. Esto es distinto del fix del 2026-05-27 (`@radix-ui/react-select` se resolvió con `pnpm install`; este no, porque el workspace no está montado).

## Decomposición honesta (raise-hand, sin cave mode)

"Que lo live realmente esté live" NO es un solo problema — son **tres**, con costos muy distintos:

| | Problema | Naturaleza | Costo | Cabe en esta story? |
|---|---|---|---|---|
| **A** | **Drift de runtime/infra** (el 500 por `@luana/hooks`, node_modules stale, migraciones sin aplicar) | Bug de entorno, reparable | Bajo (horas) | ✅ Fase 0 — reparar inline |
| **B** | **Ledger sobre-declarado** (cap dice `live` pero es slice-1-superseded o infra-only → cockpit "miente" semánticamente) | Honestidad de docs + schema | Medio (1 pasada PM/architect) | ✅ Fase 3 — reconciliar status + `ui_paradigm`/`replaced_by` |
| **C** | **Features realmente faltantes** (los ~47 slice-1 que Chris QUIERE ver en shell-organism) | Trabajo de feature = las 20 stories F2-S2..S22 pendientes (state=idea) | Alto (semanas, 20 stories) | ❌ NO cabe — ES el roadmap Fase 2. Esta story produce el **mapa priorizado con evidencia** que alimenta ese backlog. |

**El punto clave para Chris:** el cockpit no miente arbitrariamente. `status: live` significó "estado al merge", no "accesible en la UI de hoy". De las 59 caps live, solo ~24 son navegables hoy en shell-organism. Hacer que "todo lo live esté live" en sentido literal = **construir las 20 stories de Fase 2** (eso es C, semanas de trabajo). Lo que SÍ logra esta story en una corrida: (A) la app bootea y las ~24 caps live-reales funcionan verificadas, (B) el cockpit dice la VERDAD (status corregido), y (C) un mapa exacto cap-por-cap con verdict Playwright + deuda técnica → backlog de remediación priorizado.

## Shape propuesto (a ratificar)

- **Fase 0 — Boot:** reparar el dev-stack (remount `core/` o rebuild) → `:3002` 200. Aplicar migraciones pendientes + deps. Gate: app bootea + login Clerk OK.
- **Fase 1 — Sweep Playwright sistemático:** recorrer cada superficie navegable (rutas del shell-organism + sub-tabs + agentes) → matriz `cap → ruta → verdict {OK | roto | inaccesible | no-existe-UI} → evidencia (screenshot/console/network)`.
- **Fase 2 — Revisión técnica per-cap (a la par):** por cada cap con código, revisar contra estándares (DDD/FSD, tenant isolation, visual fidelity, a11y declarada, reglas de negocio del spec, español neutro). Clasificar `easy-fix | map-to-story`.
- **Fase 3 — Reparar / mapear / reconciliar ledger:** aplicar fixes fáciles (con TDD donde aplique); abrir stories de remediación para lo difícil; corregir `status` de las caps sobre-declaradas (cross_check_3) + agregar discriminador `ui_paradigm`/`replaced_by`.
- **Entregable final:** (1) `LIVE-RECONCILIATION-MATRIX.md` (la fuente de verdad cap↔realidad), (2) app booteando con caps live-reales verdes, (3) ledger corregido = cockpit honesto, (4) backlog F2 priorizado con evidencia.

## Decisión de scope (RATIFICADA Chris 2026-05-29)

- **Entregable = "honesto + verdes lo real"** (problema A + B; problema C = roadmap Fase 2, fuera de scope):
  1. App bootea (`:3002` 200), Fase 0 reparada inline.
  2. Las ~24 caps live-accesibles (shell-organism) verificadas verdes con Playwright.
  3. Ledger corregido a la VERDAD: caps sobre-declaradas dejan de figurar `live` plena (discriminar `live-ui` / `live-superseded` / `live-infra` + `replaced_by`), aplicando cross_check_3.
  4. `LIVE-RECONCILIATION-MATRIX.md` (SSoT cap↔realidad) + backlog F2 priorizado con evidencia.
  - **NO** reconstruye los ~47 slice-1 en shell-organism (eso son las 20 stories F2-S2..S22).
- **Límite "fácil" = agresivo inline:** reparar inline todo lo razonablemente acotado aunque toque varios archivos o lógica simple, MIENTRAS los gates queden verdes (lint/tsc/mypy/arch-fitness/jscpd/tests). Se mapea a story separada solo: reconstrucción de cap slice-1, features nuevas, o cualquier cosa que requiera test nuevo de comportamiento no cubierto + rompa gates.

## next_action
- `/po` produce `01-spec.md`: Fase 0 (boot fix) + Fase 1 (metodología sweep + schema de la matriz) concretos; Fase 2/3 como framework de criterios (los tickets de reparación reales se generan DESPUÉS de que el sweep produzca findings). Gherkin AI-resistant del diagnóstico + criterios de reparación/mapeo + reconciliación de ledger.
