# Propuesta — Budget Core always-on (slim-manifest) · DECISIÓN DE CHRIS

> **Estado: PROPUESTA — NO aplicada.** Escrita en la sesión de integración post-programa (2026-06-09, Fase 5 del prompt). El que decide es Chris; esta página solo deja los números, las opciones y la recomendación.

## 1 · Estado actual (medido hoy, post W1-Phase2 + Fase 4c de esta sesión)

| Bloque | Líneas always-on | Detalle |
|---|---|---|
| **Core** (21 rules symlink → `core-harness/rules/`) | **890** | top-5: step-0-worktree 80 · story-closure-gate 71 · paradigm 68 · parallel-safety 67 · auditor-self-fix 66 |
| **Project** (rules locales sin `paths:`) | **352** | DoD live-verify 59 · PII 42 · arch-fitness 40 · backend-ddd 39 · spanish-text 36 · backend-migrations 24 · tenant-isolation 12 · + ~9 stubs de 7 líneas |
| **Total** | **1242** | (programa: 2012 → 1741 → 1310 → 1242 tras Fase 4c frontend-visual-fidelity → `paths:`) |
| Tier-2 `paths:` (cargan POSTREAD, no cuentan) | — | backend-quality · frontend-quality · frontend-fsd · frontend-visual-fidelity |

## 2 · La opción slim-manifest (lo que habilitó W7)

El plugin lift-kit ya tiene construido y smoked el canal alternativo:
- `core-harness/hooks/always-on-core.manifest` — 3 hard rules: **anti-duplication (3715 ch) + git-safety (2731 ch) + tdd-mandatory (1821 ch) = 8267 chars ≤ 9.5k**.
- Injector SessionStart (smoke JSON 8090 chars) — inyecta SOLO esas 3 como always-on.
- `/harness:bootstrap` skill — carga on-demand del resto del kit.

**Opción B (slim):** luana adopta ese canal → always-on baja de 1242 líneas a ~115 (las 3 rules). Todo lo demás pasa a: skill-channel (ya verificado para varias) · `paths:` POSTREAD · `/harness:bootstrap` manual · gates mecánicos pre-commit.

## 3 · Riesgos (el porqué de NO aplicarlo wholesale)

1. **#23478 — `paths:` es read-only.** Una rule evictada del always-on solo dispara si algo LEE un archivo matching. Las reglas cuyo momento crítico es **escribir código nuevo** no tienen trigger: tenant-isolation (query nueva) · PII `response_model=` (route nueva) · spanish-text (microcopy nuevo) · backend-ddd (módulo nuevo) · anti-orphan (registration) · paradigm (declarar caja) · story-closure-gate (transición de estado) · backend-migrations (decidido DEFINITIVO always-on en Fase 4c por esto mismo).
2. **El método seguro es rule-by-rule, no wholesale.** La Fase 4c demostró el patrón: una rule sale del always-on SOLO tras verificar que cada actor que escribe esa superficie porta el deber por su propio canal (skill/agent prompt) + A/B live `claude -p` DEFAULT/POSTREAD. Eso costó ~1 h por PAR de rules. Hacerlo para ~30 rules = pase dedicado de varias sesiones.
3. **Gates mecánicos cubren parte pero no todo.** Pre-commit caza voseo/PII-seeds/cap/scope DESPUÉS de escrito; la rule always-on previene ANTES. Quitar la prevención sube el costo del loop (escribir mal → gate rojo → rehacer).
4. **El core 890 es el piso real.** W1-Phase2 ya documentó honesto que el target ~500 era inalcanzable sin slimear las 21 core (story-closure/step-0/parallel-safety son protocolo operativo denso, no grasa).

## 4 · Recomendación (mía — Chris decide)

**Mantener 1242 para luana hoy; slim-manifest SOLO para el kit extraído.**

- **Luana (este monorepo):** el canal always-on actual queda. Eviction adicional = rule-by-rule con el método 4c (candidatas con mejor ratio: `github-actions-deferred` 34 — solo importa al tocar workflows; `anti-default-flip-audit` 40 — solo al flipear flags, su skill-channel es tdd-mandatory que se queda; `git-haiku-delegation` 26 — su consumidor es la skill commit-push que ya la porta). Estimado alcanzable sin riesgo: **−100/−150 líneas más**, no −1100.
- **Kit extraído (`core-harness/` en otro producto):** el slim-manifest de 3 rules + `/harness:bootstrap` ES el diseño correcto — un producto nuevo no arranca con 21 reglas de protocolo que aún no practica; arranca con anti-dup + git-safety + TDD y va subiendo reglas a medida que adopta el proceso (ADOPTING.md ya lo narra así).
- **Si Chris quiere bajar más en luana:** el siguiente paso de mayor impacto NO es evictar rules — es slimear las 3 core densas (step-0 80 + story-closure 71 + parallel-safety 67 = 218) moviendo sus tablas/matrices a rules-detail con el patrón stub que ya usamos. Estimado: −80/−100 líneas, riesgo bajo (las tablas son lookup, no prevención write-time).

## 5 · Qué haría falta para ejecutar (si Chris ratifica alguna)

| Opción | Esfuerzo | Riesgo |
|---|---|---|
| (a) Status quo 1242 | 0 | 0 |
| (b) Eviction selectiva −100/150 (3 candidatas § 4) | 1 sesión corta, método 4c por rule | bajo (verificación por canal) |
| (c) Slim de las 3 core densas −80/100 | 1 sesión, patrón stub→detail + validate-after-apply (CHECK strings!) | medio (load-bearing strings de machinery) |
| (d) Slim-manifest 3-rules wholesale | varias sesiones de verificación actor-channel | ALTO (#23478 write-time) — NO recomendado para luana |
