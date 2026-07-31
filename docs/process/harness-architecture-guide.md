# Harness Architecture Guide — el sistema completo, explicado a fondo

> ⚠ **HISTÓRICO (2026-07-31):** el kit `core-harness/` fue **materializado** en `.claude/` — este repo standalone ya no tiene kit extraíble ni plugin: rules/skills/agents/hooks viven como archivos propios en `.claude/` + `scripts/` + `docs/process/`. Este doc describe la arquitectura previa (kit/símlinks/plugin/re-exposición); sigue útil como referencia de diseño del harness.

> **Para:** Chris. **Fecha:** 2026-06-09 (cierre del programa harness-refactor W0→W10). **Qué es esto:** el deep-dive de CÓMO está armado tu sistema de desarrollo agéntico — las 3 capas, la costura, cómo se parte cada superficie, el mecanismo de re-exposición, el ciclo idea→done, los gates, el loop de mejora continua y el cockpit — con los ejemplos reales de luana. Leélo una vez entero; después usalo como mapa.
>
> **SSoT relacionados:** charter (`harness-refactor-charter-2026-06-08.md`) · outputs por workstream (`harness-refactor-w{n}/`) · kit (`core-harness/README.md` + `ADOPTING.md`) · proceso (`core-harness/process/harness-lifecycle.md`, `continuous-improvement.md`).

---

## 1 · La idea central: el harness es un sistema operativo de desarrollo

Tu plataforma tiene DOS sistemas conviviendo en el mismo repo:

1. **El producto** (luana-platform): engine `core/luana-core-*` + brands + cockpit.
2. **El harness** (el dev-OS): las rules, skills, agents, hooks, templates, process-docs y scripts que hacen que una IDEA se convierta en código mergeado con calidad verificable, operado por vos + agentes.

El programa harness-refactor separó el harness en capas con una **regla de dependencia** (clean architecture aplicada a harnesses): las flechas apuntan SIEMPRE hacia adentro.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  BRAND        vitalia/ · nicolify/ · comunify/ · lupulo/        │
   │  (instancia de mercado: overlay CLAUDE.md, brand.yaml,          │
   │   pm-{brand} skill, capabilities, vision)                       │
   │        │ depende de ↓                                           │
   │  ┌──────────────────────────────────────────────────────────┐   │
   │  │  PROJECT     el stack + dominio de luana                 │   │
   │  │  (rules de stack: backend-ddd, frontend-fsd, tenant-     │   │
   │  │   isolation… · domain skills: offer/copilot/metrics… ·   │   │
   │  │   builders/auditores · pre-commit checks de stack ·      │   │
   │  │   cockpit · docs/rules-detail/)                          │   │
   │  │        │ depende de ↓                                    │   │
   │  │  ┌────────────────────────────────────────────────────┐  │   │
   │  │  │  CORE  =  core-harness/  (el kit extraíble)        │  │   │
   │  │  │  CÓMO se construye software con agentes:           │  │   │
   │  │  │  lifecycle idea→done · gates · roles · TDD · DoD · │  │   │
   │  │  │  git/parallel safety · learning capture · CIL      │  │   │
   │  │  │  → NUNCA nombra una tech, marca, locale o URL      │  │   │
   │  │  └────────────────────────────────────────────────────┘  │   │
   │  └──────────────────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────────────────┘
```

**Por qué importa:** antes del refactor, "vitalia", "ruff", "Clerk" y los paths del engine estaban ADENTRO de las rules de proceso — la flecha apuntaba hacia afuera (violación). Hoy el CORE es portable: lo probamos (W8) dropeándolo en un repo vacío con un producto ficticio Go/single-tenant (`ledgerline`) y el ciclo resuelve **sin editar un solo archivo del core**. Eso es lo que el programa llamó "el DoD de extracción" — y desde W10 lo asserta mecánicamente el **CHECK 29** en cada commit.

## 2 · La costura: `project.config.yaml` (el contrato DIP)

El CORE no puede nombrar tu tech — pero la NECESITA para operar. La solución es la **costura** (seam): un YAML en la raíz del repo con **9 slots + wip_caps** que el core lee en runtime. El core depende de la ABSTRACCIÓN (el slot); el proyecto provee el VALOR.

| Slot | Qué declara | Valor luana (ejemplo) |
|---|---|---|
| `meta` | producto | luana-platform |
| `brands` | instancias de mercado, ports, dev_app, cap_gate per-brand | active: vitalia/nicolify/comunify/lupulo · loop_order 10 |
| `toolchain` | lint/format/typecheck/test/migrate por stack | uv + pnpm · venv root · ci_gate make ci-parity |
| `locale` | regla de copy user-facing | es-LATAM-neutro, tuteo, scope acotado UI/agentic |
| `engine_prefix` | dónde vive el código compartido (target del grep anti-dup) | `core/luana-core-*` (27 pkgs) + `@luana/*` |
| `live_verify_infra` | cómo se ejerce una story LIVE antes de `done` | cloudflared tunnel + creds test + Clerk verify |
| `design_system_ref` | el canon de composición UI | design-system-canon.md + @luana/ui-kit |
| `domain_modules` | los módulos de negocio | brand/offer/copilot/analytics/… |
| `agent_roster` / `value_stream` | roles worker + etapas del mapa | builders/auditores ×3 · Atraer→Vender→Operar→Retener |
| `wip_caps` | límites WIP que enforcean los gates | developed_max etc. (D1: mató una dup verbatim de 2 scripts) |

**Cómo se lee la costura (4 canales):**
- **Python/Bash:** `scripts/harness_config.py` (symlink → `core-harness/scripts/`). `python3 scripts/harness_config.py brands.active` · `--where cap_gate=hard` · `--doctor`. 13 consumidores cableados (validate_session_close, generate_backlog, pre-push, mutation_gate, scan_promotables, sync scripts…). Degrade: si no hay python/yaml → vacío + warning RUIDOSO (nunca fallback hardcodeado silencioso).
- **Cockpit (TS):** `lib/project-config.ts` (server-only) — paridad cross-runtime testeada contra el loader python.
- **Markdown (rules core):** convención `{slot}` — la rule escribe `{engine_prefix.python_glob}` y el lector (humano o agente) lo resuelve vía el loader. No hay interpolación nativa en rules — es convención documentada.
- **Doctor:** `--doctor` exit-3 lista los slots `__FILL_ME__` → es el mecanismo de "detectar qué falta" cuando el kit aterriza en un repo nuevo.

## 3 · Cómo se parte CADA superficie (core vs project, con números reales)

La regla de oro del programa: **`tier:core` se GANA por proxy-grep** (0 tokens de tech/marca), no por intención. Resultado real por superficie:

| Superficie | CORE (en `core-harness/`) | PROJECT (queda en `.claude/`, `docs/`, `scripts/`) |
|---|---|---|
| **rules** | 21 (story-closure-gate, tdd-mandatory, anti-duplication, git-safety, parallel-safety, paradigm-arquitectura, learning-capture, auditor-self-fix, step-0-worktree…) | ~22 de stack/dominio (backend-ddd, tenant-isolation, pii, spanish-text, frontend-visual-fidelity…) — desde W1-Phase2 la mayoría son **slim pointers de 7-9 líneas** cuyo cuerpo vive en el skill dueño |
| **rules-detail** | 0 — los 14 mirrors son la MITAD stack-specific que se stubeó FUERA de la rule slim | todos (`docs/rules-detail/`) |
| **skills** | 1 (harness-bootstrap) — los 5 de refinamiento (pm/po/architect/dev/auditor) son hybrid: esqueleto portable, cuerpo luana | ~50 (pipeline + domain experts + brand PMs) |
| **agents** | 1 (grep-bot) | 11 (builders/auditores/orchestrator/context-builder — el CONTRATO es portable, el cuerpo nombra el stack) |
| **hooks/checks** | 3 checks (07 checkpoint-enum, 11 worktree, 17 dupkeys) + SessionStart injector | 19 checks de stack + dispatcher + event-hooks |
| **templates** | 5 (00-chris-input, 00-research, 00-story, 01-spec, story-ui) | 18 hybrid + overrides por marca |
| **process-docs** | 6 (harness-lifecycle, continuous-improvement, tech-debt, ticket-states, cockpit-permissions, spec-mapa-funcional) | ~30 (los W-OUTPUT, capability-protocol, lifecycle luana…) |
| **scripts** | harness_config.py + 6 git-coordination (commit-paths, session-lock, scope-guard, dod-gate, cleanup-wip, ps1) | ~80 (generadores, validators, scanners) |
| **cockpit** | el READ-SCHEMA (qué shape de .md/.yaml lee) es contrato core | la tool entera (`tools/luana-cockpit/`) es project |

**El patrón de presupuesto de contexto (ISP):** always-on hoy = **1310 líneas** (890 core + 420 project), tras la eviction W1-Phase2 (era 2012 al inicio del programa). Tres tiers:
- **Tier-1 always-on:** invariantes de proceso (core) + write-time-safety (tenant-isolation, pii, backend-ddd, spanish-text… — deben disparar al ESCRIBIR código nuevo, bug #23478 impide scoping).
- **Tier-2 `paths:`:** rules de convención que inyectan SOLO al leer un archivo que matchea (frontend-quality, frontend-fsd, backend-quality). Verificado empírico 2026-06-09: `paths:` funciona (el viejo `globs:` estaba MUERTO — CC lo ignora).
- **Tier-3 skill-references:** el cuerpo vive en `references/` del skill dueño; la rule es un pointer de 7 líneas con trigger + no-skip 1-liner.

## 4 · El mecanismo Option-C de re-exposición (por qué hay symlinks)

Claude Code SOLO auto-carga rules desde `.claude/rules/`, agents desde `.claude/agents/`, skills desde `.claude/skills/`. Mover los archivos core a `core-harness/` a secas habría ROTO la carga. El mecanismo ratificado (Option C, per-surface doc-safe):

```
core-harness/rules/tdd-mandatory.md   ←──símlink──  .claude/rules/tdd-mandatory.md
        (el archivo REAL)                            (lo que CC auto-carga)

core-harness/agents/grep-bot.md       ──copia──→    .claude/agents/grep-bot.md
        (agents-symlink es undocumented → copy)

core-harness/hooks/checks/07-*.sh     ←──source──   scripts/git-hooks/pre-commit (dispatcher)
core-harness/scripts/*.sh|py          ←──símlink──  scripts/… (read-by-path, el OS resuelve)
core-harness/templates|process/*.md   ←──símlink──  docs/specs/templates/… · docs/process/…
```

**La propiedad clave es PATH-STABILITY:** todo consumidor (los 29 paths hardcodeados del validator, el cockpit, los hooks, los scripts) sigue leyendo el path VIEJO y el symlink resuelve → el move físico necesitó **cero repoints**. El restart-smoke (2026-06-09) confirmó que las 21 rules symlinkeadas cargan always-on con cuerpo completo en sesión fresca.

**Distribución:** `core-harness/.claude-plugin/` lo convierte además en un plugin marketplace de CC (skills+agents+hooks namespaced; las rules no tienen canal de plugin → el SessionStart hook inyecta las 3 hard rules ≤9.5k y `/harness:bootstrap` instala el corpus completo).

## 5 · El ciclo idea→done (el proceso que el harness protege)

```
 idea ──→ refining ──→ refined ──→ ready ──→ developing ──→ developed ─┬─[G]─[R]─→ reviewing ──→ done
 (∞)       (≤3)         (≤5)        (≤5)        (≤3)          (≤1)*    │              (≤1)      (90d)
                                                                       │
  parked (∞) · dropped (terminal)                  *exenciones: defer_audit · AWAIT_CHRIS_VERIFY
```

- **idea→refined:** `/pm-{brand}` + `/po-ux`/`/po`/`/ux-agentico`. Intake-handshake (la historia NACE de la conversación) → 2 rondas/2 firmas (input-spec ✍1 → ejecutable con Gherkin+matriz+mockup ✍2). Gates: prior-art scan (anti-duplication-refining) + caja/zona del paradigma (3 planos: Sistema/Acción/Trabajadores → mapa de 3 zonas) + canon de diseño para UI.
- **refined→ready:** `/architect` produce el ready package (03-arch + 04-validators + 05-guidelines + 06-tickets + dispatch-plan), con `verification_nature`, Integration design CONN (anti-isla), assignment explícito por ticket y autonomous_mode propuesto (vos ratificás).
- **ready→developed:** `/dev-team` itera ticket-por-ticket TDD (RED→GREEN→REFACTOR), test-design por naturaleza del ticket, gate-runner Haiku corre las suites, `dod_evidence` con writes reales ejercidos live.
- **G (AWAIT_CHRIS_VERIFY):** pausa-y-ofrece — VOS ejercés el kit live y firmás `chris_verify.signoff` (salvo autonomous_mode). **R (reconcile):** `/pm-{brand}` alinea spec/arch/cap a la realidad ratificada.
- **reviewing:** `/auditor` (Responsable v5): lee docs RECONCILIADOS, sub-auditores be/fe/agentic, gherkin-matrix Phase D, live-verify con ≥1 write real, y **fix-and-own** (Carril R) salvo stake-asimétrico (security/tenant/PII/prompt-slots → Carril C escala a vos).
- **done:** `/pm-{brand}` REFUSE-merge sin signoff + dod_evidence; 07-merge + cap YAML actualizada + archive R2 + ruteo de learnings al CIL.

**Tipos de trabajo (WT1-7):** UI · service · agentic · bugfix (repro-first) · technical caps · promotion brand→core (`/pm-luana` lift gate) · harness-improvement (HLP). Todos pasan por el mismo esqueleto con ceremonia proporcional.

## 6 · Los gates (defensa en profundidad)

| Capa | Qué corre | Cuándo |
|---|---|---|
| **pre-commit dispatcher** | 22 checks aislados (`scripts/git-hooks/checks/NN-*.sh`): spanish §1, PII §8/9, scope-gate §13, chris-input §16, dod-evidence, sweep-guard M15, cap-format G1-G6… | cada commit (light en wip/*, full en main) |
| **machinery validator** | **67 CHECKs** anti-drift (`validate_machinery_consistency.py`): doctrina↔templates↔agentes consistentes. Incluye **CHECK 29** (core-harness proxy-clean — el DoD de extracción mecánico) y **CHECK 30** (sync template↔instancias PM) | pre-commit + `make machinery-check` |
| **pointer-scan ratchet** | `scan_harness_pointers.py` — 25 punteros rotos baselined, NEW debe ser 0, shrink-only | machinery CHECK 28 (advisory) |
| **pre-push** | tests + tsc + arch-fitness por marca | cada push |
| **ci-parity** | suite full equivalente a CI — HOY advisory por sentinel `.ci-parity-deferred` (fase dev-only); el gate real es el nativo. Excepción HARD que persiste: bidirectional cross_check_3 (cap↔código) | pre-push-to-main |
| **DoD live-verify (#37)** | ninguna story `done` sin ejercerla LIVE (writes + logs + efecto) + `dod_evidence` — "verde ≠ done, GET 200 ≠ verificado" | G + auditor + merge |

## 7 · El loop de mejora continua (CIL + HLP)

El harness se auto-mejora con su propio proceso (dogfood):

```
  fricción detectada ──/harness-issue──→ harness-backlog.md (L1)
  learning de cierre ──────────────────→ docs/learnings/ (L2: técnico→docs/, negocio→{brand}/)
  deuda código/infra ──────────────────→ tech-debt.md (L3)
  cap desfasada ───────auto-detect─────→ (L4: cap_doctor/survivors)
                         │
            /harnesses-improvement (stop semanal)
            lee los 4 carriles → vos remediás en lote → deep-sweep opcional (harness-audit-2026)
```

**Regla de oro HLP: NUNCA editar el harness mid-feature** — se captura al backlog y se arregla en sesión harness dedicada (como esta). Apply-pipeline: verify-first (la auditoría sobreestima) → sonnet edita / opus ratifica → Haiku commitea por pathspec.

## 8 · El cockpit (la ventana)

El **Prenter Cockpit** — binario externo (`~/Proyectos/prenter-harness/products/cockpit-go/cockpit`, Go + UI Next embebida), **filesystem-as-DB** (lee los .md/.yaml de cada workspace, NO genera): board por estados, `/functionality` (cap↔código bidireccional), agents, map (3 zonas del paradigma), `/harness` (el backlog CIL como kanban read-only). **luana lo consume, no lo contiene** — su home base + launcher viven en chris-corp (I-48; boundary: `.claude/rules/cockpit-boundary.md`). Un **solo** multi-cockpit en `:4000` lee el registry del portfolio y ve todos los workspaces a la vez; pinta 🔨 lane por sesión leyendo `.session-locks/`. Se prende con `make -C ~/Proyectos/chris-corp cockpit-up`. Para el harness es la capa de OBSERVABILIDAD (R-OBS): el move W7 fue path-stable precisamente para que el cockpit no note nada.

## 9 · Qué quedó probado y qué decide Chris

- **Probado:** extracción (W8 ledgerline) · restart-smoke (rules symlinkeadas cargan) · Tier-2 `paths:` (A/B empírico) · proxy-clean mecánico (CHECK 29) · sync LSP (CHECK 30, cazó drift real día-1).
- **Decisión tuya pendiente:** el **merge `wip/vitalia` → `main`** — main es el gate canónico que corre (D2 install-hooks toma efecto ahí); mientras no se mergee, los otros worktrees corren el pre-commit viejo. Ver recomendaciones del cierre del programa.
- **Cómo evoluciona:** brand nueva = config (OCP, cero core edits) · producto nuevo = `ADOPTING.md` (drop kit + llenar seam) · mejora del proceso = HLP/CIL · kit standalone = `git subtree split` cuando se porte el primer producto real.
