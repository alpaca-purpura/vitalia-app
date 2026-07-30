# Plan de implementación — machinery hardening (post-auditoría 2026-05-28)

> Deriva de `docs/process/audits/2026-05-28-agentic-machinery-audit.md` § 6.
> **Worktree:** in-sitio `wip/vitalia` (Fase solo-bootstrap, `SCOPE_GATE_SKIP=1` + razón en commit). El worktree `protocol` prolijo requeriría primero merge vitalia→main (49 commits ahead) — decisión aparte de Chris.
> **Ratificado por Chris:** 2026-05-28 ("todo el plan, secuencial").
> **Naturaleza:** cross-cutting (`.claude/`, `docs/`, `scripts/`).

## Secuencia (6 fases · 11 items)

| Fase | Items | Severidad | Gate de avance | Estado |
|---|---|---|---|---|
| **0 — Quick-wins** | 1 atomics→scenarios (3 rules) · 2 greps multibrand (2 skills) · 3 contradicción Caso B | 🔴 CRÍTICO | grep limpio | ✅ DONE |
| **1 — Architect handoff** | 4 bloque `assignment` + dispatch-plan-template + reconcile CONTRACT/03-arch · 11 stale T-result + chrome-devtools | 🟠/🟡 | template valida | 🔄 en curso |
| **2 — Self-fix auditor** | 5 rediseño 3-carriles + Edit a sub-auditores + sin re-spawn | 🟠 | **RATIFICAR Chris** | ⏸ pausa |
| **3 — Rigor builder** | 9 skill `test-design-doctrine` (primero) · 6 step `technical_design` + gate orden TDD | 🟠 | builder agents actualizados | ⏳ |
| **4 — Punteros cap↔código** | 7 builders leen cap YAML + `# cap:` headers · 10 `// cap:` en 562 FE | 🟠/🟡 | validator cc3 verde | ⏳ |
| **5 — Anti-drift lock-in** | 8 `validate_templates_vs_rules.py` + lint paths skills + pre-commit | 🟡 | corre sobre todo lo anterior | ⏳ |

## Razón del orden
- **0 primero** — landmines vivos hoy (atomics auto-load alucina, NO-NEW-LAYER no-op).
- **1 antes de 5** — los templates deben estar correctos antes de construir el validador que los chequea.
- **9 antes de 6** — el step `technical_design` referencia la doctrina de testing.
- **2 con pausa** — cambio de política (no mecánico); Chris da forma al diseño antes de codear.
- **8 al final** — lock-in que valida todo + previene regresión futura (el drift template↔rule fue el bug-class #1 de esta auditoría).

## Criterios de aceptación por fase
- **0:** `grep -i atomic` en rules auto-load solo devuelve notas "MUERTO"; greps de architect resuelven en filesystem; guardrail Caso B condicional al motivo del spawn. ✅
- **1:** cada ticket del template tiene bloque `assignment`; existe `dispatch-plan-template.md`; T-result-template sin `git push origin development` ni paths PI-N; chrome-devtools-verify resuelto.
- **2:** política reescrita a 3 carriles; sub-auditores con Edit + policy; carril A re-corre gates sin re-spawn full; agentic conservador documentado.
- **3:** skill/rule test-design-doctrine existe; los 3 builders tienen step `technical_design` con gate; auditor verifica 1ª entrada bitácora = RED.
- **4:** builder Step 1 lee cap YAML del cap_target; builders agregan headers; 562 FE stampeados; cc3 verde.
- **5:** `validate_templates_vs_rules.py` falla ante drift sintético; lint de paths corre en pre-commit; suite verde.

## Tracking
Tasks #1-#8 en el task list de la sesión.

---

## Estado final 2026-05-28 (sesión autónoma — todas las fases DONE)

Chris amplió a autonomía plena ("toma las mejores decisiones... que en un mes sea código de un genio ordenado") + reforzó: cero islas/huérfanos, cero duplicación, fidelidad visual FE, alta cohesión/bajo acoplamiento, y que seguimos usando el stack de calidad (ruff/vitest/jscpd/etc.). Se ratificaron las 5 decisiones del self-fix + se agregaron **2 fases nuevas** (6 anti-isla, 7 visual). Todo implementado y autoverificado.

| Fase | Estado | Entregables |
|---|---|---|
| 0 | ✅ | 3 rules atomics→scenarios · greps multibrand · contradicción Caso B |
| 1 | ✅ | assignment block + dispatch-plan-template + T-result fix + chrome-devtools |
| 2 | ✅ | self-fix v4.2 (3 carriles) · sub-auditores con Edit · auditor SKILL Step 3 |
| 3 | ✅ | `test-design-doctrine.md` + step `technical_design` (con orden TDD RED-first) en 3 builders |
| 4 | ✅ | builders leen cap YAML del cap_target + escriben headers `# cap:`/`// cap:` |
| 5 | ✅ | `scripts/validate_machinery_consistency.py` + `make machinery-check` (12/12 verde) |
| 6 | ✅ | `anti-orphan-integration.md` (CONN) + architect Integration design + auditor Cat Connectivity (be/fe/agentic) |
| 7 | ✅ | `frontend-visual-fidelity.md` + builder-frontend (design-system/mockup/scope) + auditor-frontend Cat Visual fidelity |

3 reglas nuevas registradas en CLAUDE.md (filas 33-35, auto-load). Validador 12/12.

### Corrección 2026-05-28 (revisión post-pregunta de Chris)
- **Item 10 — backfill `// cap:` FE: NO era un gap.** La auditoría (subagente) reportó "FE = 0 headers"; era FALSO. Verificación real: **561 archivos FE de producción tienen `// cap:` en línea 1** (de 746; los ~185 sin header son `.test.tsx`, skip-eligibles). El mapeo bidireccional FE↔cap YA funciona en el cockpit. (Lección: relayé un claim de subagente sin re-verificarlo — los 2 claims más decisivos sí los verifiqué a mano, ése no.)
- **Pre-commit wiring de `machinery-check`: HECHO.** `scripts/git-hooks/pre-commit` Section 13 invoca `validate_machinery_consistency.py` cuando el commit toca `.claude/{rules,skills,agents}/` o `docs/specs/templates/` (ambos gate levels, con override `MACHINERY_CHECK_SKIP=1`). Nota worktree: el hook activo (symlink en git-common-dir) resuelve al checkout de **main** → la Section 13 **activa al mergear wip/vitalia→main**. CHECK 8 del validador verifica que la wiring exista.

### Diferido (genuinamente cosmético, no afecta cockpit)
- **Item 4c — nomenclatura `CONTRACT.md`→`03-arch.md` en `architect-orchestrator.md`:** NO afecta cockpit (lee `03-arch.md`, que es lo que realmente se produce). Es higiene de claridad interna en la prosa del agente. Bajo valor, bajo riesgo. Pasada focalizada opcional.

### Hallazgo separado (deuda PM, NO maquinaria — surgido del validador CHECK 6)
Skills PM brand referencian rules brand-domain que **no existen aún**: `hipaa-lite.md` (pm-vitalia + pm-luana ref), `creator-funnels.md` (pm-comunify), `field-services-and-local-seo.md` (pm-fixia), `memberships-and-capacity.md` (pm-fitflow), `ota-sync-and-seasonal-pricing.md` (pm-guestly). Son forward-refs a rules planeadas. Acción sugerida: cada `/pm-{brand}` crea su rule o quita la ref. Fuera de scope de este hardening.
