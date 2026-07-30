# Auditoría técnica — maquinaria agéntica (architect → dev-team → auditor)

<!-- voseo-allowed: reporte técnico interno de auditoría — contiene análisis code review que cita glosario voseo -->

> **Fecha:** 2026-05-28 · **Auditor:** `/pm-luana` (Opus 4.8) · **Scope:** revisión técnica del paradigma de desarrollo agéntico — skills (`architect`, `dev-team`, `auditor`) + agentes (`architect-orchestrator`, `builder-{be,fe,agentic}`, `auditor-{be,fe,agentic}`, `gate-runner`, `context-builder`) + rules + templates + sistema de punteros cap↔código.
> **Método:** lectura full de 25+ archivos vía 4 lectores paralelos + verificación manual de los 2 claims más decisivos.
> **Naturaleza:** READ-ONLY. Cero cambios aplicados. Las recomendaciones requieren ratificación de Chris + worktree `protocol`.

---

## 0. Veredicto ejecutivo (honesto)

El paradigma está **bien diseñado a nivel de control de flujo** (state machine de 10 estados, story-closure gate, autonomous loop con cap, gate-runner determinista, separación adversarial dev↔auditor). Es de los pipelines agénticos más maduros que vas a encontrar.

Pero tiene **tres clases de problema** que erosionan la promesa:

1. **Drift de templates vs skills/rules** — la doctrina vive en los SKILL.md/rules, pero los **templates que los agentes copian** quedaron atrás. El agente lee la regla nueva y copia el template viejo. Esto es el patrón de bug más frecuente y más caro (produce artefactos no-conformes de forma silenciosa).
2. **Punteros pre-multibrand** — varios greps de auditoría cross-module en `architect-be` / `architect-agentic` apuntan a paths que **dejaron de existir en la reorg 2026-05-15** (`backend/src/shared/`, `backend/src/core/`). El guard anti-duplicación más importante (NO-NEW-LAYER) es **un no-op silencioso**: no encuentra nada, pasa siempre.
3. **El sistema de punteros cap↔código es de salida, no de entrada** — los caps se ESCRIBEN al merge, pero **ningún agente de razonamiento los LEE** para navegar. La promesa "encontrar la info fácil siguiendo punteros" todavía no es real para los agentes (sí para vos en el cockpit).

Tus 3 intuiciones (auditor que se auto-corrige, architect que entregue todo detallado, devs con fases internas rígidas) son **correctas y todas tienen gap real hoy**. Detalle abajo.

---

## 1. Tu pregunta #1 — ¿el auditor debería auto-corregirse en vez de spawnear devs?

**Respuesta corta: sí, deberías expandir el self-fix del auditor — pero NO "todo". La línea correcta ya existe en el árbol de decisión actual; el problema es que las ramas 2 y 3 sobre-restringen.**

### Lo que pasa hoy (verificado)

El árbol de decisión (`auditor-self-fix-policy.md`):

```
¿El fix requiere ESCRIBIR un nuevo test?
├─ SÍ  → SPAWN dev-team. Auditor NUNCA escribe tests.
└─ NO  → ¿Toca ≥3 archivos O cambia lógica de negocio?
        ├─ SÍ  → SPAWN dev-team.
        └─ NO  → ¿Está en WHITELIST (17 categorías cosméticas)?
                ├─ SÍ  → SELF-FIX (cap 4 iter, ≤2 files, ≤10 líneas).
                └─ NO  → ESCALATE Chris.
```

La whitelist es 100% cosmética (lint, format, typo, import order, docstring, magic comment…). **Todo lo que tenga contenido semántico — incluso una rama lógica de 1 línea, un empty-state faltante, un `response_model=` no cableado — se va a un round-trip a dev-team.**

### El costo del round-trip (estimado, evidenciado)

Cuando el auditor encuentra algo estructural, la secuencia real es:

`auditor (Opus) audita ~40-60k → escribe T-review → spawn gate-runner (Haiku) → spawn dev-team (Sonnet) re-lee contexto ~20-35k + fix → gate-runner (Haiku) → RE-SPAWN sub-auditor (Opus) re-lee TODO + re-scorea ~40-50k`

- **Round-trip total:** ~110-155k tokens, ~80-110k de ellos **Opus**. ≈ **US$1.2-1.65 por finding estructural**, y **se duplica** con 2 iteraciones (lo común).
- **El sumidero real es el re-spawn del sub-auditor**: re-audita las 12-15 categorías desde cero aunque solo cambiaron 2-3 archivos (~40-50k Opus de puro desperdicio).

Path hipotético self-fix (sin test nuevo, gates re-corren como verificación): ~60-90k, **ahorro 30-60% por finding**.

### El argumento estructural que SÍ importa (y que Opus 4.8 NO resuelve)

El riesgo de que el auditor se auto-corrija **no es de capacidad** — es **estructural**: el mismo agente que detecta un problema y lo arregla **no puede verificar independientemente su propio fix** (sesgo de confirmación). Opus 4.8 es más inteligente, pero "Opus auditando su propio fix de Opus" sigue siendo el mismo actor verificándose. Más capacidad **no** crea independencia.

**PERO** — y este es el insight clave — los **gates son verificación independiente y determinista**: lint, type-check, arch-fitness, tests existentes, coverage **no les importa quién escribió el código**. Si la corrección de un fix está **totalmente capturada por gates + tests EXISTENTES**, entonces *self-fix + re-correr gates ES verificación independiente*. El sesgo de confirmación solo muerde donde hace falta un **test nuevo** — que es justo la primera rama del árbol actual.

→ **La primera rama del árbol ("¿requiere test nuevo?") es la línea correcta.** Las ramas 2-3 (≥3 files / "lógica de negocio" / whitelist cosmética) sobre-restringen y mandan a round-trip caro fixes que los tests existentes ya verifican.

### Recomendación (diseño correcto)

Rediseñar la política a **3 carriles por naturaleza de verificación, no por tamaño**:

| Carril | Qué cubre | Quién | Verificación |
|---|---|---|---|
| **A — Self-fix gate-verified** | Cualquier fix donde (a) NO hace falta test nuevo, (b) el suite de tests existente + arch-fitness YA ejercita el comportamiento afectado, (c) no es stake-asimétrico (ver C). **Sin límite de files/líneas** — el criterio es "¿lo verifica un gate existente?", no el tamaño. | **El sub-auditor mismo** (auditor-be/fe/agentic, Opus) con tool Edit | **Re-correr gate-runner (Haiku, barato)**. Si todo verde → audit-passed. **Sin re-spawn de sub-auditor.** |
| **B — Needs-new-test** | El fix requiere un test nuevo (RED→GREEN). | **dev-team** (preserva disciplina TDD + calidad de test) | dev-team valida + auditor re-audita |
| **C — Stake-asimétrico** | Security, `tenant_id`/PII, migrations, prompt slots, eval goldens, engine (`core/luana-core-*`), cross-brand. | **ESCALATE** o dev-team; opción: **2º auditor Opus independiente** como verifier (el costo se justifica) | independiente obligatoria |

Cambios concretos vs hoy:
- **Mover el self-fix del orquestador `/auditor` a los sub-auditores** (`auditor-be/fe/agentic`). Hoy los sub-auditores son read-only (sin Edit) y el fix sube al orquestador en una 2ª pasada — coordinación innecesaria. Que cada sub-auditor Opus arregle SU surface inline y re-corra SUS gates. Esto es exactamente tu "auditor frontend/backend/agentico que se corrige a sí mismo".
- **Eliminar el re-spawn full del sub-auditor en el carril A** → la verificación es el gate-runner, no una segunda lectura Opus de 12-15 categorías.
- **Mantener intacto "auditor NUNCA escribe test nuevo"** — la integridad RED→GREEN y la calidad del test son no-negociables. Acá tu intuición de ahorro NO aplica: el round-trip a dev-team es correcto.
- **Caveat agentic:** auditor-agentic más conservador. Los "gates" agénticos (eval goldens, pass^k) son **no-deterministas** → un self-fix podría sobre-ajustar. Para agentic, self-fix solo mecánico; comportamiento/prompt/eval → builder-agentic (que ya es Opus igual).

**Bug bloqueante a corregir antes de tocar esto** (verificado a mano): el prompt de spawn Caso B dice `NO new tests added` en la línea 104, pero Caso B se dispara *precisamente* cuando hace falta un test nuevo (NUNCA-self-fix #1). El guardrail contradice su propio trigger. Hay que separar: spawn-por-test-nuevo (permite tests) vs spawn-por-estructural-cubierto (no agrega tests).

---

## 2. Tu pregunta #2 — ¿el architect le entrega TODO bien detallado a los devs?

**Respuesta corta: la doctrina está completa y es excelente; los TEMPLATES que materializan esa doctrina están desactualizados. El architect "sabe" entregar todo, pero la plantilla que llena no tiene los campos.**

### Lo que SÍ entrega (fuerte)

El "ready package" es ambicioso y mayormente sólido:
- **Por ticket:** `primary_agent`, `owner_eligibility`, `model_preference`, `must_load_skills` (lista verbatim, no "skills relevantes"), `must_load_artifacts`, `forbidden_to_touch`, `gherkin_coverage` (scenario→test path).
- **Plan de test:** `04-validators.yaml § test_construction_plan` es lo mejor documentado del sistema — `creation_order` numerado con `depends_on`, `scenario_to_test` mapeado, POMs con firmas, fixtures con contenido, comandos **ejecutables** (`must_pass: true`), y subcategorías obligatorias (race conditions, empty states, a11y, i18n).
- **Self-audit:** categoría `architectural_validation` con 5 sub-tests `must_pass` (DDD boundaries, tenant isolation, anti-dup scan, FSD boundaries, no cross-brand imports).
- **Dispatch plan:** la rule `architect-autonomous-mode.md` manda producir un `dispatch-plan.md` (matriz ticket→agente→modelo→costo + Playwright visual scope discipline + cláusula no-egoísmo).

### Los gaps (rankeados)

**CRÍTICO**
1. **El bloque `assignment` está MANDADO por la rule + SKILL.md Step 7.5 pero AUSENTE de `06-tickets-template.yaml`.** El template usa solo `owner_eligibility` (flags). Un architect que copia el template produce tickets sin `primary_agent`/`model_preference`/`forbidden_to_touch` estructurados. La doctrina existe; la plantilla no la materializa.
2. **`dispatch-plan.md` no tiene template.** Es el 5º artefacto del ready package pero no hay `dispatch-plan-template.md` en `docs/specs/templates/`. Se genera ad-hoc desde un schema inline del skill → frágil. Además el output block del SKILL.md (Step 9) lista solo los 5 originales y no menciona `dispatch-plan.md` (inconsistencia interna con su propio checklist Step 8).

**ALTO**
3. **Greps de auditoría cross-module en paths muertos.** `architect-be/SKILL.md` y `architect-agentic/SKILL.md` hacen `grep -rn ... backend/src/shared/` / `backend/src/core/` — paths eliminados en la reorg 2026-05-15. El correcto es `${WS}/core/luana-core-*/src/`. **Consecuencia: el audit NO-NEW-LAYER (el guard anti-duplicación más importante) no encuentra nada y pasa siempre. Es un no-op silencioso.** Este es probablemente el bug de mayor impacto del subsistema architect.
4. **Inconsistencia de paths en `04-validators-template.yaml`:** la sección `non_functional` usa `cd backend && .venv/bin/pytest` (pre-multibrand); `architectural_validation` usa el path brand-scoped correcto. El gate-runner falla en resolución de path al ejecutar.

**MEDIO**
5. **`# cap:` headers no mencionados en artefactos builder-facing.** El architect no le dice al builder en `05-guidelines` ni en `deliverables` de ticket que agregue headers `# cap:`. (Ver §4 — esto rompe el sistema de punteros.)
6. **`architect-orchestrator.md` llama al output `CONTRACT.md`** en sus secciones internas, mientras el SKILL.md lo llama `03-arch.md`. Drift de nomenclatura.
7. **Campos legacy `sprint`/`pi` y posibles `atomics[]`** sobreviven en templates → paradigma los mató (ver §4).

---

## 3. Tu pregunta #3 — ¿los devs tienen fases internas (análisis → diseño técnico → desarrollo → verificación → validación iterando)?

**Respuesta corta: tienen el carril de implementación + el loop iterate-until-green (fuerte), pero les falta la fase de DISEÑO TÉCNICO antes de codear, y el TDD es honor-system (no verificado mecánicamente).**

### Lo que SÍ existe (fuerte)

- **Loop iterate-until-green: el mejor enforced del pipeline.** Cap de 10 iteraciones (`04-validators.yaml::iteration.max_iterations`), `on_fail`/`on_all_pass`/`on_cap_reached` definidos, gate G5 pre-commit que bloquea commit con RED, y fallback manual si gate-runner falla 2 veces. `cap_reached` → `state: blocked` + escalate. Tu "iterando hasta que todo esté verde" ya está, sólido.
- **Fases de implementación explícitas por builder:** builder-frontend tiene `implement_types_first → api_layer → hooks → components → forms → page → write_tests_red_first → validate → live_verify`. builder-backend impone orden DDD estricto (domain→infra→app→api con RED por capa). builder-agentic incluye `cross_module_systems_audit_NO_NEW_LAYER` + `eval_goldens`.
- **Estrategia de test por naturaleza:** existe, pero es **responsabilidad del architect** vía `04-validators.yaml`. El builder ejecuta lo que el validators dicta.

### Los gaps (rankeados)

**CRÍTICO**
1. **No hay fase de DISEÑO TÉCNICO con gate antes de codear.** Verificado a mano: builder-backend salta `read_brief_and_invoke_skills` → `implement_inside_out` directo. El `## Plan inicial` del `T-impl-log-template.md` es **advisory** — ningún gate ni categoría de auditor lo verifica. Un builder que improvisa produce los mismos artefactos que uno que diseñó. **Esto es exactamente lo que pedís y no existe como step enforced.**
2. **TDD es honor-system.** `tdd-mandatory.md` es tajante ("tests PRIMERO"), pero **nada verifica el orden temporal**. El `gate-output.json` registra pass/fail, no la secuencia. Un builder podría escribir todo el código, después los tests, correrlos, y los gates se ven idénticos. La única evidencia es el formato timestamped del impl-log, que ningún gate lee.

**ALTO**
3. **No hay "doctrina de testing" canónica como skill.** El TDD vive en una rule; hay `tessl__pytest-api-testing`/`tessl__vitest` para patrones de framework, pero no un skill consolidado "dada esta naturaleza de ticket, este es el diseño de test (unit vs integration vs contract vs E2E) que debés construir". Si el architect escribió un `04-validators.yaml` flaco, el builder **no tiene doctrina de fallback** independiente.

**MEDIO**
4. **Stale en `T-result-template.md`:** `git push origin development` (branch eliminado en la reorg) + paths `docs/projects/active/PI-N/...` (pre-reorg). Riesgo de que qwen pattern-matchee el ejemplo y empuje a branch inexistente.
5. **`chrome-devtools-verify` marcado DEPRECATED pero OBLIGATORIO** en builder-frontend → cada ticket FE no cierra sin invocar un skill roto o escalar a Chris. Ruido en cada ciclo FE.

### Lo que recomiendo agregar

- **Step `technical_design` enforced** entre `read_brief` e `implement` en los 3 builders: el builder escribe a `T-{n}-impl-log.md § Plan` (a) firmas de clases/funciones/DTOs que va a crear, (b) qué tests por capa y de qué tipo según naturaleza del ticket, (c) qué mecanismos de auto-verificación. **Gate:** una categoría de auditor verifica que el impl-log tenga `§ Plan` con ≥3 entradas Y que la **primera entrada timestamped del bitácora sea un test RED** (no un write de código). Esto enforcea de un saque la fase de diseño + una prueba ligera de orden TDD.
- **Skill nuevo `test-design-doctrine`** (o rule): "dado tipo de ticket → matriz de tests requeridos" como fallback independiente del builder cuando el `04-validators.yaml` es delgado. Esto es tu "bases sólidas de desarrollo que nos pertenezcan como skill o rule".

---

## 4. Premisa transversal — ¿el sistema cap↔código hace "encontrar la info fácil"?

**Respuesta corta: los punteros son REALES pero ASIMÉTRICOS y de SALIDA. Los caps se escriben al merge; ningún agente de razonamiento los LEE para navegar. Para los agentes, `03-arch.md` sigue siendo el mapa; el cap YAML es una isla.**

### Evidencia
- **Código → Cap:** 564 archivos backend con header `# cap: <module>.<slug>` (consistente, todos los slugs resuelven a un YAML). `_code-index.json` poblado. **Pero los 562 archivos frontend tienen CERO `// cap:` headers.** El mapeo bidireccional cubre medio codebase.
- **Cap → Código:** parcial. `dev_preview.{main_component,api_endpoints,e2e_test}` presente en feature caps, pero `test_coverage` (el puntero más rico) está solo en **1 cap** (`valeria-agenda`) y no está en el template estándar. **55/67 caps son `stub`** (sin scenarios); solo 1 es `verified-live`.
- **Wiring en agentes (la pregunta clave):** builder-backend Step 1 lee `03-arch.md` + `modules/{module}.md` — **NO lee el cap YAML del `cap_target`**. context-builder tampoco. Ningún agente usa el header `# cap:` para navegar de un archivo a su cap. El `_code-index.json` es para el cockpit, no para razonamiento de Claude. **El cap YAML solo entra al workflow en 2 puntos: architect chequeando `cap_change_type` coherence, y PM escribiéndolo al merge.**

### Staleness (CRÍTICO — landmine auto-cargado)
- **`story-closure-gate.md` (auto-load en CADA sesión) todavía exige `atomics_added >= 1`** para `new`/`extend` en la tabla Fase F.3 (v3.1/v3.2). Pero MEMORY + `lifecycle.md` dicen que **atomics murió el 2026-05-28** (mismo día que se cementó esa versión de la rule — contradicción intra-día). Un agente siguiendo Fase F.3 va a buscar `atomics_added`, no encontrarlo en el schema nuevo, y errar o alucinar.
- **`capability-protocol.md _template.yaml`** todavía scaffold-ea `atomics_added: [...]` en el `change_log`.

### Recomendaciones
1. **Patch `story-closure-gate.md` + `_template.yaml`:** `atomics_added` → `scenarios_added` (alinear con lifecycle v4). Es el stale más peligroso porque es auto-load. **Hacelo primero.**
2. **Agregar el cap YAML como read step explícito** en builder-backend Step 1 + dev-team pickup: "si `06-tickets.yaml` declara `cap_target`, leé `capabilities/{m}/{cap}.yaml` — `dev_preview` + `scenarios[]` te dicen qué ya existe y qué comportamiento preservar". Cambio mínimo que vuelve los punteros **útiles** en vez de decorativos.
3. **Stampar `// cap:` headers en los 562 archivos FE** (variante FE de `generate_code_to_cap_index.py`). Hasta entonces el mapeo bidireccional cubre solo backend y cross_check_3 saltea E2E de FE.

---

## 5. Arquitectura & escalabilidad — evaluación de patrones

Lo que está **bien** (mantener):
- **Separación de responsabilidades** architect (diseño) / builder (impl) / auditor (verificación) / gate-runner (gates deterministas) / context-builder (amortización de lectura). Patrón limpio.
- **Cost-routing por naturaleza** (Haiku mecánico / Sonnet BE-FE / Opus agentic+estratégico) — económicamente sano.
- **State machine + WIP caps + story-closure gate** — previene el abandono de stories y el trabajo huérfano.
- **Anti-telephone-game** (subagent devuelve 1 línea + path) — correcto para no inflar contexto.
- **Gate-runner que produce `gate-output.json`** consumido por auditores en vez de parsear 50k de logs — excelente.

Lo que **no escala** (deuda):
- **Drift template↔doctrina** es sistémico, no puntual. No hay test que verifique que los templates están alineados con las rules que los mandan. **Recomendación: un `scripts/validate_templates_vs_rules.py` en pre-commit** que falle si un campo mandado por una rule está ausente del template correspondiente. Sin esto, cada cementación nueva de doctrina genera un template stale más.
- **Punteros pre-multibrand** en greps (no-ops silenciosos) — mismo problema: nada verifica que los paths citados en skills existan. **Recomendación: un lint de skills que valide que los paths hardcodeados resuelven.**
- **Caps por verificación-vacía:** 82% stub. La infraestructura de navegación scenario-level no existe para la mayoría del producto todavía. Escala solo si el backfill de scenarios avanza.

---

## 6. Recomendaciones priorizadas

| # | Acción | Tu pregunta | Severidad | Esfuerzo | Worktree |
|---|---|---|---|---|---|
| 1 | Patch `story-closure-gate.md` + `_template.yaml`: `atomics_added`→`scenarios_added` (stale auto-load) | #4 premisa | 🔴 CRÍTICO | bajo | protocol |
| 2 | Fix greps pre-multibrand en `architect-be`/`architect-agentic` (NO-NEW-LAYER no-op) | #2 | 🔴 CRÍTICO | bajo | protocol |
| 3 | Resolver contradicción `NO new tests added` en Caso B del auditor | #1 | 🔴 CRÍTICO | bajo | protocol |
| 4 | Agregar bloque `assignment` + crear `dispatch-plan-template.md` | #2 | 🟠 ALTO | medio | protocol |
| 5 | Rediseñar self-fix del auditor → 3 carriles por verificación; mover Edit a sub-auditores; eliminar re-spawn en carril A | #1 | 🟠 ALTO | medio-alto | protocol |
| 6 | Agregar step `technical_design` enforced + gate de orden TDD (1ª entrada = RED) en los 3 builders | #3 | 🟠 ALTO | medio | protocol |
| 7 | Builders leen cap YAML del `cap_target` (Step 1) + agregan `# cap:`/`// cap:` headers al codear | #4 premisa | 🟠 ALTO | medio | protocol |
| 8 | `scripts/validate_templates_vs_rules.py` (anti-drift sistémico) + lint de paths en skills | escalabilidad | 🟡 MEDIO | medio | protocol |
| 9 | Skill/rule `test-design-doctrine` (fallback independiente del builder) | #3 | 🟡 MEDIO | medio | protocol |
| 10 | Stampar `// cap:` headers en 562 archivos FE | #4 premisa | 🟡 MEDIO | bajo (script) | protocol |
| 11 | Fix stale `T-result-template.md` (`git push origin development`, paths PI-N) + resolver `chrome-devtools-verify` deprecado | #3 | 🟡 MEDIO | bajo | protocol |

**Quick wins (1-3) = 3 fixes de bajo esfuerzo y alto impacto.** Los 3 son landmines silenciosos hoy en producción del pipeline.

---

## 7. Notas de método / confianza

- **Verificado a mano:** contradicción Caso B (`auditor-self-fix-policy.md:104`), ausencia de step de diseño en `builder-backend.md`, stale `atomics` en `story-closure-gate.md` (texto en contexto auto-cargado).
- **De lectores paralelos (alta confianza, con cita):** completitud del ready package, greps pre-multibrand, conteos de headers (564 BE / 0 FE), 55/67 caps stub.
- **Estimaciones (orden de magnitud, no medición):** costos de round-trip vs self-fix. No hay telemetría real de tasa de éxito de self-fix — **gap de diseño en sí mismo**: las caps (4 self-fix iter, 3 audit iter) están calibradas por intuición, no por datos. `emit_process_metric.py` captura verdict pero nadie analiza la serie.

---

*Próximo paso sugerido: Chris ratifica el rediseño del self-fix (§1) + autoriza quick-wins 1-3. La implementación es trabajo cross-cutting → worktree `protocol-machinery-hardening`.*
