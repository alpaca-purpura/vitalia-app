# BACKFLOW.md — auditoría pre-reinstalación kit Prenter v0.5.0

> **Fecha:** 2026-07-02 · **Repo:** luana-platform (worktree luana-vitalia, `wip/vitalia`)
> **Baseline comparado:** kit fábrica tag `v0.4.0` (`core-harness/` en root del repo prenter-harness)
> **Kit destino:** `products/kit/core-harness/` @ `f1f32bb` · `KIT_VERSION=0.5.0`
> **Nota pin:** el `core-harness/` local NO tiene archivo `VERSION` (la instalación local es el ORIGEN
> histórico del kit — nació en `8b39ff64` harness-refactor W0→W10, previo a la disciplina de pin).
> La reinstalación deja el pin correcto por primera vez.

## Deltas locales vs v0.4.0 — 7 archivos

| # | Archivo | Qué es el delta local | Veredicto |
|---|---|---|---|
| 1 | `rules/architect-autonomous-mode.md` | ajustes doctrinales menores | ✅ **YA ABSORBIDO** en kit v0.5.0 (archivo idéntico al kit nuevo) |
| 2 | `rules/test-design-doctrine.md` | HB-94 seam-testing (covered = colaborador real) + HB-95/96/97 gate | ✅ **YA ABSORBIDO** en kit v0.5.0 (idéntico) |
| 3 | `rules/learning-capture.md` | ciclo de vida `applied:` de learnings (2026-06-11) | ✅ contenido presente en kit v0.5.0 (verificado grep) |
| 4 | `rules/parallel-safety.md` | HB-73 `LUANA_LANE` / SingletonLock Chrome MCP multi-sesión | ✅ contenido presente en kit v0.5.0 (verificado grep) |
| 5 | `rules/story-closure-gate.md` | HB-79 validators deferidos → `must_pass: false` (anti verde-fantasma) | ✅ contenido presente en kit v0.5.0 (verificado grep) |
| 6 | `templates/01-spec-template.md` | doctrina Storybook-first HB-103/105/106/107 (commit `15accff4`) | ✅ contenido presente en kit v0.5.0 (4 menciones Storybook) |
| 7 | `process/tech-debt.md` | local borró la fila placeholder "(sin deuda L3 registrada…)"; kit la trae de vuelta | ⚪ **DESCARTE CONSCIENTE** — cosmético; ledger local con 0 filas reales → el reemplazo wholesale no pierde datos |

## Veredicto global

**CERO hot-fixes pendientes de backflow a la fábrica.** Los 6 deltas doctrinales locales
ya viven en el kit v0.5.0 (la fábrica sincronizó desde luana el 2026-06-11 y absorbió lo posterior).
El único delta no absorbido (#7) es una fila placeholder — se descarta conscientemente.
Nada se entierra con el reemplazo wholesale.

## Hallazgos colaterales (para decidir en el checkpoint)

1. **Tree sucio** — precondición 0 del runbook pide tree limpio. Hay 2 files modificados ajenos al
   reinstall: `vitalia/docs/product/stories/vitalia-fase2-mateo-vista-semana/{checkpoint,chris-input}.md`
   (¿otra sesión tuya?). Propuesta: los dejo fuera (commit por pathspec) — o los commiteás vos antes.
2. **Exposición vieja inventariada** (paso 2 la retira):
   - 21 symlinks `.claude/rules/*` → `core-harness/rules/` (los 26 files reales restantes = capa proyecto, QUEDAN)
   - `.claude/agents/grep-bot.md` = única copia de agent del kit (los otros 10 agents = capa proyecto, QUEDAN)
   - `.claude/skills/` = 61 skills, CERO copias del kit (harness-bootstrap no está copiado) → nada que retirar
   - `settings.json` hooks: ninguna referencia a `core-harness/` → nada que retirar
3. `process/` del core-harness contiene docs de proceso que el kit REEMPLAZA (tech-debt.md ledger vacío
   verificado — sin datos vivos que perder).

---

**FIRMA CHRIS (backflow ratificado):** ✅ **CONCEDIDA retroactiva 2026-07-02** ("firma retroactiva CONCEDIDA — veredicto cero-por-upstrear aceptado").

## Anexo — propuestas de seam (sweep del bootstrap) — ✅ FIRMADAS Y APLICADAS 2026-07-02

Chris ordenó "presentame las 5 propuestas y las firmo ahora" + "slots → doctor exit 0" → aplicadas tal como propuestas (nicolify VS con `operar: []` hasta Sara; comunify/lupulo `[]` declarado-vacío pendiente-ADR/bootstrap). **Doctor: exit 0.** Registro original:

1. **`value_stream.nicolify`** — procedencia: roster nicolify en el mismo seam + comentario del slot que instruye derivarlo + `canonical_stages`:
   ```yaml
   nicolify:
     - { id: atraer,  name: Atraer,  order: 1, description: "Estrategia de oferta + growth/pauta que trae cuentas.", boxIds: [abel, brenda] }
     - { id: vender,  name: Vender,  order: 2, description: "Outbound SDR: calificar y cerrar cuentas B2B.",         boxIds: [christian] }
     - { id: operar,  name: Operar,  order: 3, description: "Gestión/delivery de la cuenta activa.",                 boxIds: [] }   # Sara pendiente ADR-nicolify-002
     - { id: retener, name: Retener, order: 4, description: "Retención + expansión de cuentas.",                     boxIds: [norvil] }
   ```
2. **`agent_roster.comunify` + `value_stream.comunify`** — sin roster en cockpit (ADR propio pendiente). Opciones: `[]` declarado-vacío (doctor exit 0) o dejar `__FILL_ME__` (doctor te lo sigue gritando).
3. **`agent_roster.lupulo` + `value_stream.lupulo`** — marca placeholder. Mismas opciones.

Al firmar: escribir valores + re-correr `python3 core-harness/scripts/harness_config.py --doctor` → exit 0 cierra el paso 5 completo.
