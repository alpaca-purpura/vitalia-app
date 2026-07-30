---
globs: "**/*"
description: "Seguridad multi-sesion paralela Claude Code/opencode — worktree-based + sincronizacion canonicos + step 0 enforcement (post 2026-05-18 D1-D14)"
---

# Parallel Safety (OBLIGATORIO)

Chris opera 2-3 sesiones Claude/opencode en paralelo en Linux Mint. **Default (ADR-009): single-hub** — N sesiones sobre el MISMO worktree canónico por marca (`~/Proyectos/luana-{brand}`, branch `wip/{brand}` ESTABLE), coordinadas por bucket locks M14. Worktree físico dedicado (`hotfix/*`/`exp/*`/`wip/core-*`/otra marca) = excepción. Modelo cementado en `docs/process/parallel-sessions-protocol.md` D1-D14 + `docs/architecture/luana-platform/ADR-{005,009}-worktree-policy.md`.

## Topologia filesystem (D2)

| Path | Tipo | Branch | Editar codigo |
|---|---|---|---|
| `~/Proyectos/luana-platform/` | PRINCIPAL | `main` | ❌ NO (solo merges + read cross-brand) |
| `~/Proyectos/luana-{brand}/` | CANÓNICO **HUB único** (ADR-009) | `wip/{brand}` ESTABLE (M12 — NO rota story-by-story) | ✅ SÍ · N sesiones con bucket locks M14 |
| `~/Proyectos/luana-{brand}-{slug}/` | EFIMERO brand | `wip/{brand}-{slug}[-{lane}]` | ✅ SI |
| `~/Proyectos/luana-{brand}-hotfix-{slug}/` | EFIMERO hotfix | `hotfix/{brand}-{slug}` | ✅ SI |
| `~/Proyectos/luana-{brand}-exp-{slug}/` | EFIMERO exp | `exp/{brand}-{slug}` | ✅ SI (NUNCA mergea) |
| `~/Proyectos/luana-core-{slug}/` | EFIMERO core (D12) | `wip/core-{slug}` | ✅ SI (lift gate `/pm-luana`) |

`{brand}` ∈ {vitalia, nicolify, comunify, lupulo} + futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow). `core` reservado para lifts engine.

## Crear y cerrar sesion

```bash
# Crear (mec. B)
scripts/git/new-session.sh <BRAND> <TYPE> <SLUG> [LANE]
# Ejemplo
scripts/git/new-session.sh vitalia story copilot-tools-impl be
# Lift core
scripts/git/new-session.sh core lift extract-callback-handler

# Cerrar (mec. C)
scripts/git/cleanup-session.sh <BRAND>-<SLUG>[-LANE]
```

Worktrees creados a mano sin script → regenerar manifest con `scripts/git/regenerate-manifest.sh` (mec. M) antes de operar.

## Sincronizacion canonicos (D10)

3 triggers de sync hacia `origin/main`:

| Trigger | Aplica | Comportamiento |
|---|---|---|
| T1 SessionStart hook (mec. A) | PRINCIPAL + CANONICO | auto-FF silent si tree clean + FF puro; advisory si merge real; banner LOUD si dirty + core changed |
| T2 `/pm-{brand}` step 0 (mec. N) | TODOS los wip/* | misma logica T1 al bootstrap del skill |
| T-push PreToolUse (mec. L) | TODOS los wip/* | fetch + advisory pre-push (no bloquea) |

Definicion "toca core": `git diff main..origin/main --name-only | grep -E '^core/luana-core-[^/]+/src/'` → cualquier match escala label CORE en output.

T1/T-push NUNCA ejecutan `uv sync` ni `pnpm install`. Solo advisory cuando `core/**/pyproject.toml` o `core/**/package.json` cambiaron.

## Politica merge a main (D11)

- Default: 1 squash-merge por story al cerrar `state=done` (auditor APPROVED + CHECKPOINTS.md). `/pm-{brand}` ejecuta como parte de transicion reviewing→done.
- Checkpoint mid-story opcional cuando mitad logica esta lista (procedimiento documentado, scripteamos cuando aparezca primer caso).
- Hotfix bypass auditor formal — REQUIERE `repro_verified: true` + test regression RED→GREEN + smoke pass.
- Experimentos NUNCA mergean. Cleanup extrae learnings.
- Multi-lane: cada lane mergea independiente cuando su auditor lane APPROVED.
- Core change requiere `/pm-luana` promotion proposal `state >= accepted`.

Pre-merge checklist verifica:
1. Worktree tree limpio
2. Story state = developed o reviewing (NUNCA mergear desde developing)
3. Validators GREEN per `04-validators.yaml::must_pass=true`
4. Si delta toca `core/luana-core-*/src/`: promotion proposal accepted/migrated
5. Commit message Conventional Commits + co-authored

## Cambios al core (D12)

Worktree dedicado `~/Proyectos/luana-core-{slug}/` con branch `wip/core-{slug}`. Manifest brand=core (pseudo-brand). Cross-worktree dependency:
- Caso A — feature en lift in-flight → brand consumer queda `state=ready` hasta merge a main (NUNCA merge wip→wip)
- Caso B — feature mergeada → T1 auto-FF o advisory; deps changed → `uv sync` / `pnpm install` advisory
- Caso C — overlap WIP brand con archivos lift refactoro → FF falla por conflict, advisory LOUD

Breaking change cross-brand → `/pm-luana` coordina stories cross-brand en release window.

## Step 0 enforcement skills (D13)

SSoT `.claude/rules/step-0-worktree.md` (mec. N) consumido por `/pm-{brand}` y `/pm-luana` via `@import`.

**Enforcement matrix:**

| Skill | Worktree | Verdict |
|---|---|---|
| `/pm-{brand-X}` | CANONICO/EFIMERO brand X | OK proceed |
| `/pm-{brand-X}` | CANONICO/EFIMERO brand Y (Y≠X) | **HARD REFUSE** + redirect |
| `/pm-{brand-X}` | PRINCIPAL | **HARD REFUSE** "principal no edita codigo brand" |
| `/pm-{brand-X}` | EFIMERO core | **HARD REFUSE** "core lift es /pm-luana territory" |
| `/pm-{brand-X}` | UNKNOWN | **HARD REFUSE** escalate Chris |
| `/pm-luana` | PRINCIPAL | OK (default) |
| `/pm-luana` | CANONICO brand X | OK (cross-brand desde brand context) |
| `/pm-luana` | EFIMERO core | OK (lift work) |
| `/pm-luana` | EFIMERO brand X | OK + soft warn |
| `/pm-luana` | UNKNOWN | **HARD REFUSE** escalate Chris |

## opencode parity (D14)

opencode honra `.claude/skills/` y `.claude/rules/` igual que Claude Code. Hooks no nativos en opencode → wrappers bash portable + Warp Workflows como atajo.

| Logic | Claude Code | opencode |
|---|---|---|
| T1 SessionStart | Hook nativo → script | Manual: `scripts/git/check-sync.sh` (Warp Workflow `sync-check`) |
| T-push | Hook nativo PreToolUse | Manual: `scripts/git/push-wip.sh wip/X` (Warp Workflow `push-wip`) |
| Step 0 | Skill `@import` mec. N | Identico |
| new/cleanup-session | Bash directo | Identico |

## Reglas M1-M14 (vigentes — M12/M13/M14 cementados v2 2026-05-18)

| # | Regla |
|---|---|
| M1 | Sesiones paralelas usan branches DISTINTOS — EXCEPTO sesiones paralelas en MISMO canónico (mismo cwd + mismo branch wip/{brand}) con lock por bucket. Ver M14. |
| M2 | SSoT (`learnings.md`, BACKLOG, MEMORY, PORTFOLIO) SOLO `/pm-{brand}` o `/pm-luana`. Builders nunca. |
| M3 | Tests/Docker/migrations SECUENCIAL por brand. Max 1 stack docker por brand vivo (D5). |
| M4 | Claim by commit: `/pm-{brand}` cambia state en checkpoint.md + commit/push inmediato pre-claim. |
| M5 | NO pull. NO force push. NO revert sin aprobacion. Push falla non-fast-forward → STOP, reportar. |
| M6 | Bootstrap PM pregunta story activa antes proceder. |
| M7 | Subagentes paths PRIMARIOS story + read all + extend-no-destroy archivos ajenos. |
| M8 | Tocar archivos otra sesion OK si entiendes leyendo + extend/append no replace + STOP si rompe. |
| M9 | **REVOCADA v2 2026-05-18:** Sub-agents NO crean worktrees. Trabajan in-place sobre cwd del caller (ver § Sub-agent worktree ban). |
| M10 | branches `wip/*` son autosave. Push frecuente (M11) garantiza recovery ante crash. NO stash > 30 min. |
| M11 | NUNCA pasar >30 min sin push si hay cambios significativos. Push activa `ci-wip.yml`. |
| **M12** | **Canónico = `wip/{brand}` ESTABLE** (NO rota story-by-story). Stories se trabajan EN ESA branch. Worktree story efímero SOLO por pedido explícito user (`EXPLICIT_USER_REQUEST=1`). |
| **M13** | **Scope per branch enforced** (pre-commit Section 13). `wip/{brand}` SOLO toca `{brand}/**` + raíz brand-agnostic. `wip/protocol-*` SOLO toca modelo. `wip/core-*` SOLO toca engine. Cross-brand mixing PROHIBIDO. |
| **M14** | **N sesiones mismo cwd permitido** (canónico) con lock por bucket: code / docs / tests. Lock auto-acquire por skill `/pm-{brand}` step 0 (`scripts/git/session-lock.sh`). |

## Sub-agent worktree ban (cementado 2026-05-18 v2 — supersedes M9 original)

Sub-agents NUNCA crean worktree. Trabajan in-place sobre el `cwd` del caller.

- ❌ **PROHIBIDO:** `isolation: "worktree"` en frontmatter de cualquier sub-agent (Architect, Auditor, Builder, Explore, etc.)
- ❌ **PROHIBIDO:** `git worktree add` desde código/scripts ejecutados por sub-agent
- ✅ **PERMITIDO:** caller (Chris) crea worktree explícito vía `scripts/git/new-session.sh`
- ✅ **PERMITIDO:** sub-agents write directo sobre `cwd` del caller (Architect/Auditor son "los jefes", trabajan sobre el código real)

**Justificación:** caso vitalia 2026-05-18 — sub-agent creó worktree fantasma `luana-vitalia-infra-cross-cutting` que nunca cleanup + sin manifest. Rama huérfana con commits valiosos casi se pierden.

**Enforcement:**
- Arch fitness test `scripts/test_no_subagent_worktree.sh` — grep `isolation:\s*['"]?worktree['"]?` en `.claude/agents/*.md` → fail si encuentra
- Auditor checklist Cat 11 — verifica no creation de worktrees por sub-agent durante PR

## Scope per branch (cementado 2026-05-18 v2 — M13)

Pre-commit Section 13 enforce. Branch pattern → scope permitido/prohibido:

| Branch pattern | Scope permitido | Scope prohibido |
|---|---|---|
| `wip/{brand}` | `{brand}/**` + raíz brand-agnostic (CLAUDE.md, AGENTS.md, scripts triviales) | otra-brand/**, core/luana-core-*/**, `.claude/{rules,skills}/`, `docs/{process,architecture}/`, `scripts/git/` |
| `wip/{brand}-{story-id}` | mismo que `wip/{brand}` | mismo |
| `wip/protocol-{slug}` | `docs/{process,architecture,specs}/`, `.claude/`, `scripts/` | brand/**, core/** |
| `wip/core-{slug}` | `core/luana-core-*/**` + tests + lockfiles | brand/**, .claude/** |

**Override:** `SCOPE_GATE_SKIP=1 git commit ...` (emergencias documentadas, auditor escruta razón).

## N sesiones paralelas mismo cwd (cementado 2026-05-18 v2 — M14)

Modelo v2 permite N sesiones Claude/opencode en MISMO canónico `~/Proyectos/luana-{brand}/` (mismo branch `wip/{brand}`), coordinadas por **buckets de scope**:

| Bucket | Paths permitidos |
|---|---|
| `code` | `{brand}/{backend,frontend}/src/**` |
| `docs` | `{brand}/docs/**` + raíz docs/ |
| `tests` | `{brand}/{backend,frontend}/tests/**` |

**Lock mechanism:** `~/Proyectos/luana-{brand}/.session-locks/{bucket}.lock` con PID + skill + timestamp. Auto-cleanup si PID ya no corre.

**Caso de uso típico:** Chris quiere refinar specs (`docs`) en paralelo a una sesión `/dev-team` activa (`code`). Abre otra ventana terminal en mismo cwd, otra invocación skill, lock `docs` libre → proceed.

**Commits:** cada sesión stagea por nombre exacto, commits separados al mismo branch. Push intercalados sin conflict porque scope físicamente disjunto.

### Chrome DevTools MCP — aislamiento per-sesión vía `LUANA_LANE` (HB-73, 2026-06-15)

El MCP `chrome-devtools` (`~/.claude.json`, user-level global) lanza un Chrome con perfil
`--userDataDir=…/chrome-devtools-mcp/luana-vitalia-${LUANA_LANE:-solo}`. Chrome protege su
perfil con `SingletonLock` → **dos sesiones que comparten el mismo perfil chocan**: la 2ª no
toma el lock y **toda tool-call de Chrome DevTools de esa sesión falla** (sin error legible).

El env se **fija al arrancar `claude`** (el server MCP lo hereda) → no se puede inyectar desde
dentro de la sesión ni con `/mcp` reconnect. **Por eso es un paso de arranque humano**, no algo
que el agente pueda hacer.

**Regla:** con **≥2 sesiones `claude` concurrentes** (mismo o distinto worktree — el base
`luana-vitalia` está hardcodeado global, así que `LUANA_LANE` es el ÚNICO diferenciador entre
cualquier par de sesiones vivas), exportá un lane único en CADA terminal **antes** de lanzar
claude:

```bash
export LUANA_LANE=A          # B, C, … único por terminal (igual convención que el bucket-lock M14)
claude --dangerously-skip-permissions
```

1 sola sesión → no hace falta (cae en `…-solo`). Stale lock tras crash → limpiar SOLO el lock,
nunca el perfil entero (perderías el login Clerk): `rm -f ~/.cache/chrome-devtools-mcp/luana-vitalia*/Singleton*`.
SSoT del diagnóstico: `docs/learnings/tooling/2026-06-15-chrome-devtools-mcp-per-session-isolation.md`.

## Inicio de conversacion (branch check + sync activo v2)

```bash
git status --short && git branch --show-current && git log --oneline -3
git worktree list
scripts/git/status-all.sh                    # dashboard cross-worktree (mec. H)
scripts/git/sync-from-main.sh --check        # sync KISS v2 — solo reportar (no integra)
```

Step 0 skill (`/pm-{brand}` o `/pm-luana`) ejecuta `sync-from-main.sh` activo si tree clean (auto-merge si limpio, prompt si conflict).

- Branch `wip/*` o `hotfix/*` o `exp/*` o `wip/core-*` limpio en worktree dedicado → proceder
- Branch `main` en `~/Proyectos/luana-platform/` (principal) → OK para merges, NO codigo brand
- Tree sucio archivos AJENOS → NO tocar, reportar lista
- Worktree desconocido → STOP, escalate Chris

## Cierre de sesion

`"eso es todo"` / `"gracias"` / `"cierra"` / `/cierra-limpio`:

1. `git status --short`
2. Cambios propios → stage por nombre exacto + Conventional Commit + push (via `push-wip.sh` recomendado) + reportar SHA
3. Archivos ajenos → reportar intactos
4. Si efimero + story cerrada → `scripts/git/cleanup-session.sh {brand}-{slug}`

## Prohibido

- `git pull` (cualquier forma)
- `git fetch && merge` automatico (solo fetch + merge --ff-only/squash deliberado)
- `git push --force` / `--force-with-lease`
- `git revert` sin aprobacion
- `git reset --hard` sin aprobacion
- `git add .` / `-A` / `-u`
- `git commit --no-verify`
- Editar codigo en PRINCIPAL (`luana-platform/` en `main`)
- Misma branch en 2 worktrees (git lo bloquea)
- `make dev-{brand}` en 2 worktrees de la misma brand simultaneamente (mec. F enforce)
- Builders editando SSoT (`learnings.md`, BACKLOG, MEMORY, PORTFOLIO)
- Invocar `/pm-{brand-X}` desde worktree brand Y (D13 HARD REFUSE)
- Cierre sin commit/reporte
- Lift core sin promotion proposal `state >= accepted` (D11/D12)

## M14 v2 — N sesiones con bucket module-scoped (cement 2026-05-28 · ADR-009)

El bucket `code` se sub-divide: `code:{module}` (ej. `code:scheduling`, `code:crm`). Dos builds de módulos distintos corren en paralelo; mismo módulo se serializa. `code` (whole) bloquea cross-módulo (refactor).

Auto-acquire por skill step 0: `scripts/git/session-lock.sh acquire {bucket} {skill} [story-id]`. Build-claim registra `story_id + $LUANA_LANE` → cockpit pinta 🔨 lane sobre la story. Índice git compartido → commit por pathspec (`git commit <ruta-exacta>`, nunca `git add .`).

## Worktree EFÍMERO protocol (cross-cutting · cementado 2026-05-28)

`~/Proyectos/luana-protocol-{slug}/` con branch `wip/protocol-{slug}`. Scope permitido: `tools/**`, `.claude/**`, `docs/process/**`, `docs/specs/templates/**`, `CLAUDE.md`, `scripts/git-hooks/**`, `Makefile`, multi-brand `{brand}/docs/**`. Commits requieren `SCOPE_GATE_SKIP=1` con razón documentada en commit body.

## Fase solo-bootstrap — SCOPE_GATE_SKIP relajado (cement 2026-05-28)

Durante construcción activa de reglas/cockpit (solo dev, sin CI), `SCOPE_GATE_SKIP=1` está PERMITIDO para edición intencional cross-cutting desde cualquier worktree cuando Chris está seguro, con razón documentada en commit body. El worktree `protocol` sigue siendo lo recomendado-prolijo pero no obligatorio. Guardrails que se mantienen: `--no-verify` sigue prohibido; razón obligatoria en commit body; `--force`/`git pull`/amend de pusheados siguen prohibidos. Re-endurecer cuando: entra 2º developer, Chris declara reglas estables, o se activa CI/CD real. SSoT: `.claude/rules/git-safety.md` § Fase solo-bootstrap.

## Conflict resolution

Si encontras archivo modificado por otra sesion (en wip propio o al mergear a main):
1. **NO sobreescribir.** Leer primero.
2. Conflict de scope → escalate Chris.
3. Append-friendly (logs, IMPL-LOG, history) → append OK.
4. Replacement obvio (typo, refactor) → STOP + reportar antes proceder.

## Referencias

- `docs/process/parallel-sessions-protocol.md` — SSoT D1-D14
- `docs/architecture/luana-platform/ADR-005-worktree-policy.md` — decision record
- `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` — triple-branch base
- `.claude/rules/git-safety.md` — triple-branch operacional
- `.claude/rules/git-haiku-delegation.md` — commit+push delegation pattern
- `.claude/rules/step-0-worktree.md` — mec. N step 0 SSoT
- `docs/process/warp-multibrand-handbook.md` — manual operativo Warp
- `scripts/git/new-session.sh`, `cleanup-session.sh`, `check-sync.sh`, `push-wip.sh`, `status-all.sh`, `regenerate-manifest.sh`
