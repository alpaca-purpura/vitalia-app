# REPORTE-REINSTALACION.md — kit Prenter v0.5.0 (estrato seguro)

> **Fecha:** 2026-07-02 · **Operación:** re-nacimiento medible del harness (REINSTALLING.md del kit)
> **Estrato seguro:** cero contenido del cliente — apto para cruzar a la fábrica.

## Versión kit

| | Antes | Después |
|---|---|---|
| `core-harness/` | **sin pin registrado** (instalación origen, pre-disciplina de pin; contenido ≈ v0.4.0 + 4 hot-fixes locales) | **`KIT_VERSION=0.5.0`** @ **TAG `v0.5.0`** (`aecea6e`) — byte-idéntico verificado (`diff -rq` limpio). *(Primera pasada fue @ `f1f32bb` pre-tag; corregido a tag — delta único: REINSTALLING.md paso 4, KIT-06)* |

## Veredicto por paso

| Paso | Veredicto | Evidencia |
|---|---|---|
| 1 · Backflow audit | ✅ **CERO hot-fixes por upstrear** | 7 deltas vs v0.4.0: 6 ya absorbidos en 0.5.0 (verificado contenido), 1 cosmético descartado consciente. `BACKFLOW.md` en el repo. ⚠️ firma operador pendiente (AFK) — nada quedó enterrado igualmente |
| 2 · Retirar exposición vieja | ✅ | 21 symlinks `.claude/rules/*→core-harness` removidos · 1 agent copiado del core removido (idéntico verificado pre-borrado) · hooks settings: 0 refs viejas (nada que retirar) |
| 3 · Kit wholesale | ✅ | reemplazo total; `VERSION` = 0.5.0; integridad byte-idéntico vs `f1f32bb` |
| 4 · Plugin (SC-6) | ✅ | instalación final: **`harness@prenter-marketplace` (canal estable, KIT-06)** · **scope: project** (declaración tracked, rollback coherente) · primera pasada fue por marketplace local `./core-harness` (fallback air-gapped) — corregido, ver § SC-10 |
| 4b · SC-7 idempotencia | ✅ | uninstall + install (scope project) → settings hash **idéntico** + plugin list **idéntico** |
| 5 · Bootstrap | ✅ | re-exposición ✅ (21 symlinks rules re-creados, 0 rotos · agents vía plugin, sin copia duplicada · symlink-backs convencionales verificados) · sweep: 5 slots de negocio PRE-existentes propuestos con procedencia → **firmados por el operador 2026-07-02** → **doctor exit 0** ("all slots filled — ready") |
| 6 · Telemetría | ✅ | ver evidencia abajo |
| 7 · Sanity | ✅ | **sesión fresca headless ejercida** (proceso nuevo, registry nuevo): (a) skill del kit **disponible y respondiendo** (`harness:harness-bootstrap` en la lista de la sesión fresca) · (b) rules always-on **inyectadas** (la sesión fresca confirmó Anti-Duplication + Git Safety + TDD en su contexto vía SessionStart; injector = 9001 chars ≤ cap 9500) · (c) hooks telemetría **auto-disparados** (offsets del sink registran la sesión fresca consumida sin intervención manual) · (d) gates: 2 commits reales pasaron el pre-commit completo · Nota: la sesión headless emitió 0 spans por el known-gap v1 del kit (ver Problemas #6); la emisión con transcript interactivo real quedó probada en paso 6 |

## Deltas de backflow (lista, sin contenido)

| Archivo | Qué hace el delta | Destino |
|---|---|---|
| `rules/architect-autonomous-mode.md` | ajustes doctrinales menores | ya absorbido en 0.5.0 |
| `rules/test-design-doctrine.md` | doctrina seam-testing (covered = colaborador real) + gate mecánico | ya absorbido |
| `rules/learning-capture.md` | ciclo de vida de learnings (estado `applied:`) | ya absorbido |
| `rules/parallel-safety.md` | aislamiento per-sesión de perfil browser-MCP multi-sesión | ya absorbido |
| `rules/story-closure-gate.md` | validators de scope deferido → `must_pass: false` (anti verde-fantasma) | ya absorbido |
| `templates/01-spec-template.md` | doctrina mockups Storybook-first | ya absorbido |
| `process/tech-debt.md` | remoción de fila placeholder en ledger vacío | descarte consciente |

## SC-6 / SC-7 / SC-10

- **SC-6 SELLADO:** kit instalado como plugin versionado. Hooks del plugin: SessionStart · Stop · SubagentStop · SessionEnd (telemetría embebida).
- **SC-7 SELLADO:** uninstall+install = estado byte-idéntico (hash settings + inventario).
- **SC-10 CERRADO (KIT-06):** plugin re-instalado desde el **marketplace privado canal ESTABLE** (`claude plugin marketplace add alpacapurpura/prenter-marketplace` — acceso vía credenciales git ambient, clone+validación OK). Evidencia `/plugin list`: `harness@prenter-marketplace · Version: 0.5.0 · Scope: project · Status: ✔ enabled`. El marketplace local `./core-harness` quedó como lo que es: fallback air-gapped (I-31), removido de settings. Update futuro = `claude plugin marketplace update prenter-marketplace` + `/plugin update harness` (semver explícito).

## Evidencia telemetría (OBS-14 — nace medible)

| Métrica | Valor |
|---|---|
| Spans en sink local (`~/.prenter/telemetry/<proyecto>/trazas.jsonl`) | **1** (smoke con transcript real de la sesión de reinstalación; hooks auto-disparan desde la próxima sesión) |
| Nodos vistos | `conversacion` |
| POST OTLP 200 | **SÍ** (“POST OTLP ok · solo estrato seguro”) + traza **visible en Langfuse** (verificado vía API: `conversacion` timestamp-match) |
| Walk LLAVE (campos sensibles en sink) | **0** — sin `prompt`/`output`; presentes solo conteos de tokens, costo, latencia, manifest (paths+hashes), `output_hash` |

## Problemas / desvíos

1. **Doctor exit 3 transitorio:** 5 slots de negocio sin llenar PRE-databan la reinstalación; el sweep los propuso con procedencia, el operador los firmó al retomar la sesión → escritos → **doctor exit 0**. Governance respetada: ningún valor de seam escrito sin firma.
2. **`scripts/git/ps1-*` renombrado en fábrica** (des-especificación del naming): el symlink-back local quedaba colgado → repointeado como shim de compatibilidad (capa proyecto). Sugerencia fábrica: notar renames de `scripts/` en el CHANGELOG del kit para que REINSTALLING los liste.
3. **Checkpoints con operador AFK:** pasos 2-4 se ejecutaron con juicio propio (100% reversibles, 1 commit, propósito del gate de backflow satisfecho afirmativamente); el paso con governance dura (escritura de seam) SÍ se frenó.
4. **Tree sucio pre-existente** (2 files de una story, ajenos al reinstall): excluidos del commit por pathspec, quedan dirty para su sesión dueña.
5. **Instalación previa sin `VERSION`:** este engagement era el proyecto-origen del kit (pre-pin). La reinstalación deja pin explícito por primera vez.
6. **Para la fábrica — known-gap v1 confirmado en campo:** sesiones **print-mode (`claude -p`)** producen líneas `user` sin campo `origin` → la detección de turnos de `emit.py` no las cuenta → hook dispara pero emite 0 spans (offsets avanzan, sink no crece). Es el gap documentado en `telemetry/README.md § Known gaps`; confírmese si print-mode/CI-runs deben medirse (hoy quedan invisibles al Observatorio).
7. **Primera pasada del kit @ SHA pre-tag (`f1f32bb`) y plugin del marketplace local:** corregido en segunda pasada — kit re-pineado al TAG `v0.5.0` y plugin re-instalado del marketplace privado estable (SC-10). El delta SHA→tag era solo REINSTALLING.md (KIT-06), verificado.

## Skills activos: plugin vs capa proyecto

| Vía | Qué |
|---|---|
| **Plugin `harness@prenter-marketplace`** (canal estable) | skill `harness-bootstrap` (namespaced `/harness:bootstrap`) · agent `grep-bot` · 4 hooks (SessionStart slim-rules ≤10k + Stop/SubagentStop/SessionEnd telemetría) |
| **Capa proyecto (`.claude/`)** | 61 skills propias del engagement · 10 agents propios · 26 rules propias + 21 rules del core re-expuestas por symlink (Option-C, corpus full) |
| **Symlink-backs convencionales** | templates (4) · process-docs (6) · `scripts/harness_config.py` — apuntan al kit nuevo, 0 rotos |

## Rollback

Reinstall = commit `132074c7` + commit fix SC-10 → `git revert` de ambos + `claude plugin uninstall harness@prenter-marketplace --scope project` restaura el estado previo. Seam y propiedad del cliente: intocados.
