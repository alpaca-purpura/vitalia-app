<!-- voseo-allowed: internal process documentation for Chris, not user-facing -->

# Parallel Sessions Protocol (worktree-based) — v2 cementado 2026-05-18 PM

> **★ v2 Revision (2026-05-18 PM — post caso vitalia desorden):**
>
> Actualizado D2/D3/D4/D9/D10 al modelo v2:
> - **Canónico estable** `wip/{brand}` (NO rota story-by-story) — supersedes D2/D3
> - **Sync KISS activo** — supersedes D10 (auto-merge si limpio, BLOQUEA push si behind)
> - **Sub-agent worktree BAN** — revoca M9 original
> - **Scope per branch enforced** (pre-commit Section 13)
> - **N sesiones mismo cwd** con lock por bucket — D9-bis NEW
>
> SSoT detalle: `docs/process/worktree-protocol-v2-plan.md`. Runtime: `.claude/rules/parallel-safety.md` M12/M13/M14.
>
> **Status:** v2 cemented (2026-05-18 PM). v1 cemented por la mañana es supersedido en las secciones marcadas.
> **ADR asociado:** `docs/architecture/luana-platform/ADR-005-worktree-policy.md` (con addendum v2).
> **Owner:** `/pm-luana` (alias `/pm`). Aplica a todas las brands y opencode.
> **Cambios futuros:** requieren ADR addendum + bump revision en frontmatter del doc + sync `parallel-safety.md`.

---

## TL;DR

1. **1 repo = N worktrees = 1 branch por worktree.** Git prohíbe la misma branch en 2 worktrees → aislamiento por diseño.
2. **Topología:** `luana-platform/` (principal en `main`, solo merges) + `luana-{brand}/` (canónico long-lived, 1 sesión a la vez) + `luana-{brand}-{slug}/` (efímeros para paralelo extra).
3. **Política de merge:** TODO va a `main`. NADA se mergea entre branches `wip/*`.
4. **Recursos compartidos no-aislables** (Docker, ports, `.venv`, lockfiles, migrations) → reglas operativas codificadas en hooks/scripts/skills, no en disciplina humana.

---

## Decisiones cementadas

### D1. Modelo conceptual

- Sesión Claude/opencode = proceso en un `cwd`. Una sesión = un worktree = una branch `wip/*`.
- `git worktree list` es el radar canónico (corrido desde cualquier worktree muestra todos).
- `.git/` objects + refs son compartidos entre worktrees (beneficio). `HEAD`/`index`/working tree son por-worktree (aislamiento).

### D2. Topología filesystem

| Path | Tipo | Branch | Editar código? | Vida |
|---|---|---|---|---|
| `~/Proyectos/luana-platform/` | Principal | `main` | ❌ NO (solo merges + lectura cross-brand) | Permanente |
| `~/Proyectos/luana-{brand}/` | Canónico long-lived | **`wip/{brand}` ESTABLE** (v2 — NUNCA rota) | ✅ SÍ (N sesiones paralelas mismo cwd con lock buckets — M14) | Permanente |
| `~/Proyectos/luana-{brand}-{story-id}/` | Efímero story | `wip/{brand}-{story-id}` único | ✅ SÍ (sesión paralela adicional explícita user — `EXPLICIT_USER_REQUEST=1`) | Días (mientras dure la story) |
| `~/Proyectos/luana-protocol-{slug}/` | Efímero modelo | `wip/protocol-{slug}` | ✅ SÍ (rediseños modelo/skills/scripts) | Días |

### D3. Naming convention

| Tipo | Branch pattern | Worktree path |
|---|---|---|
| Canónico long-lived (v2 — ESTABLE) | `wip/{brand}` único per brand | `~/Proyectos/luana-{brand}/` |
| Story estándar (efímero, explicit user) | `wip/{brand}-{story-id}` | `~/Proyectos/luana-{brand}-{story-id}/` |
| Story multi-lane (raro) | `wip/{brand}-{story-id}-{lane}` | `~/Proyectos/luana-{brand}-{story-id}-{lane}/` |
| Hotfix sin story formal | `hotfix/{brand}-{slug-corto}` | `~/Proyectos/luana-{brand}-hotfix-{slug-corto}/` |
| Experimento / spike | `exp/{brand}-{slug-corto}` | `~/Proyectos/luana-{brand}-exp-{slug-corto}/` |
| Lift core / cambio engine (D12) | `wip/core-{slug}` | `~/Proyectos/luana-core-{slug}/` |
| Rediseño modelo/skills/scripts (v2 — NEW) | `wip/protocol-{slug}` | `~/Proyectos/luana-protocol-{slug}/` |
| Integración estable | `main` (única) | `~/Proyectos/luana-platform/` |
| Producción brand-específica | `release/{brand}-vX.Y.Z` | (CI/CD, no worktree local) |

**Reglas duras de naming:**
- `{slug}` solo `[a-z0-9-]`, lowercase. Sin `_` ni mayúsculas (filesystem-friendly + git-friendly).
- Max 40 chars el slug completo; path total objetivo <60 chars para legibilidad en `ls` y prompts.
- Si `story-id` es muy largo (>30 chars), `/po-ux` o `/po` al crear la story debe acortar a un alias estable.
- `{lane}` típicos: `be`, `fe`, `tests`, `docs` (libres pero recomendados).
- Hotfix/exp prefijos separados (no `wip/`) para diferenciar visualmente en `git branch` y limitar TTL distinto si hace falta.

### D4. Política de merge

> **⚠️ ADR-009 supersede el modelo de rotación canónico (cement 2026-05-28):** el canónico `wip/{brand}` es ESTABLE y NUNCA rota story-by-story. Lo que antes se describía como "canónico rota a nueva branch" quedó revocado por el modelo single-hub (ver `.claude/rules/parallel-safety.md` M12 + `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md`). El tercer bullet (tachado abajo) se mantiene solo como referencia histórica.

- **TODO va a main, NADA merge entre branches wip/*.**
- Efímero termina story → squash-merge a `main` (desde worktree principal) + cleanup del worktree con `cleanup-session.sh` (branch remota queda hasta cron purge 30d).
- ~~Canónico termina story → squash-merge a `main` → rota a nueva `wip/{brand}-{slug-siguiente}` para próxima story.~~ **REVOCADO por ADR-009:** el canónico `wip/{brand}` NUNCA rota — permanece estable; el squash-merge a main no cambia la branch del hub.
- Para que worktree B "vea" un cambio que A mergeó a main: `scripts/git/sync-from-main.sh` (NUNCA `git pull` ni `git fetch && merge` manual sin script).
- Efímeros nacen desde `origin/main` fresco siempre (NO desde HEAD del worktree donde se lanza el script).

### D5. Recursos compartidos (lo que NO se aísla)

| Recurso | Compartido | Decisión técnica |
|---|---|---|
| `.git/` objects + refs | Sí (beneficio) | No tocar — funcionamiento normal de git worktrees |
| `.git/hooks/` | Sí | Compartido como hoy. Hooks deben usar `git rev-parse --show-toplevel` (no hardcodear paths) |
| Docker daemon + ports + postgres `:5435` | Sí (sistema operativo) | **Regla M3 + nueva:** máximo 1 stack docker por brand vivo, sin importar cuántos worktrees de esa brand haya |
| `.venv/` raíz (884 MB) | No (cada worktree tendría que tenerlo) | **Symlink** `${worktree}/.venv → ~/Proyectos/luana-platform/.venv/` creado automático por `new-session.sh` |
| `node_modules/` | No | Cada worktree corre su `pnpm install` (gitignored, ~500 MB extra por worktree, asumible) |
| Lockfiles root (`pnpm-lock.yaml`, `uv.lock`) | Físicamente por-worktree, pero merge conflict al integrar | Declarar `touches_root_lockfiles: true` en `checkpoint.md` de la story; coordinación 1-a-la-vez |
| Alembic migration grafo (por brand) | Lógicamente compartido (down_revision lineal) | 1 sesión por brand genera migration a la vez; la segunda actualiza su `wip/*` desde main antes de generar la suya |
| `.claude/` (skills/rules/settings) | Físicamente por-worktree hasta merge | OK como está. Si modificás skill, ratificá rápido a main para que todas las sesiones lo recojan |
| RAM | Sí (~1.5-2 GB por stack docker activo) | Limita stacks docker → regla "max 1 por brand" arriba |

### D7. Visibilidad cross-terminal (cómo a las 11pm sabés qué corre dónde)

| Capa | Estado | Propósito |
|---|---|---|
| **PS1 customizado bash** | Obligatorio | Cada terminal muestra worktree + branch + dirty status permanentemente. Resuelve 80% del problema visual día a día |
| **Dashboard `scripts/git/status-all.sh`** | Obligatorio (mecanismo H, ver tabla mecanismos) | `git worktree list` enriquecido: branch + dirty/clean + last commit + Docker activo per brand + story-id leído de `.session.yaml` |
| **Manifest `.session.yaml` por worktree** | Obligatorio (excepto principal `main`) | Generado auto por `new-session.sh`. Estructura: `brand`, `story_id`, `lane` (opcional), `tickets`, `created_at`, `created_by_skill`. Gitignored (por-worktree no versionable). Consumido por skills (mecanismo E) + dashboard |
| **Warp Tabs** (Chris usa Warp como terminal) | Recomendado: 1 tab Warp por worktree, con auto-naming basado en `cwd` (o slug del manifest). Reemplaza la idea genérica "Terminator/tmux config" | Configurable en Warp settings (Tab naming) |
| **Warp Workflows** (Chris OK integrarlos) | Atajos para `new-session`, `cleanup-session`, `status-all` ejecutables desde la palette de Warp. Capa por encima de los scripts bash (los scripts son la fuente de verdad portable) | Configurables como mecanismo K |

Formato PS1 propuesto (a confirmar según shell de Chris):
```
[luana-{worktree-suffix} {branch} {dirty-marker}]$
```
Ejemplo: `[luana-vitalia-copilot-tools-impl-be wip/vitalia-copilot-tools-impl-be ✗]$`

Formato dashboard:
```
WORKTREE                              BRANCH                              STATUS       LAST COMMIT      STORY                    DOCKER
luana-platform                        main                                clean        9e78002 (10m)    —                        —
luana-vitalia-copilot-tools-impl-be   wip/vitalia-copilot-tools-impl-be   3 modified   abc1234 (2h)     copilot-tools-impl       vitalia ✓ running
luana-comunify-design-cement          wip/comunify-design-cement          clean        def5678 (35m)    design-system-cement     —
```

### D9. Multi-lane (misma story, N sesiones simultáneas)

> **⚠️ ADR-009 supersede el modelo de "canónico como lane" (cement 2026-05-28):** el default actual es N sesiones sobre el MISMO hub canónico coordinadas por bucket locks M14 (`code:{module}`, `docs`, `tests`). Las lanes separadas (worktrees efímeros por lane) son **excepción explícita** solicitada por Chris, no el default operativo. Ver `.claude/rules/parallel-safety.md` M14 + `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md`.

Caso de uso: misma story, distintos esfuerzos paralelos (BE+FE+tests). Es **excepcional, no default** — la mayoría de stories corren en el hub canónico con bucket locks.

| Decisión | Resultado |
|---|---|
| Cuándo usar | Solo cuando la misma story tiene 2+ sesiones simultáneas Y Chris solicita explícitamente worktrees separados. Default ADR-009 = N sesiones sobre el mismo hub canónico con lock `code:{module}` |
| Catálogo recomendado | `be`, `fe`, `tests`, `docs` (libres pero recomendados) |
| Max lanes simultáneas por story | 3. Si llegás a 4 → escalar split de story (paradigm v4: >10 tickets = story demasiado grande) |
| Merge order | Cada lane mergea a main por separado en su orden de cierre. NO consolidación entre lanes |
| Cross-lane dependency | Ruta por main: lane BE mergea primero → lane FE corre `scripts/git/sync-from-main.sh` en su wip |
| Lane "principal" de una story | NO existe. Las lanes son peers |
| ~~Canónico puede ser una lane temporalmente~~ | **REVOCADO por ADR-009.** El hub canónico NUNCA adquiere sufijo lane. Si se necesita efímero lane adicional → nace aparte; el canónico sigue siendo `wip/{brand}` sin slug. NUNCA 2 lanes en el mismo worktree |

### D8. Detección automática del modo worktree

Sistema clasifica con 2 fuentes complementarias:

**Fuente 1 — Path regex (clasificación primaria, sin I/O):**

```python
# Aplicado sobre git rev-parse --show-toplevel
cwd ends with /luana-platform/?$        → PRINCIPAL
cwd ends with /luana-{brand}/?$          → CANÓNICO brand={brand}
cwd ends with /luana-{brand}-{slug}/?$   → EFÍMERO brand={brand}, slug={slug}
cwd ends with /luana-core-{slug}/?$      → EFÍMERO type=core (pseudo-brand, no brand-real, ver D12)
otherwise                                 → UNKNOWN
```

`{brand}` ∈ {`vitalia`, `nicolify`, `comunify`, `lupulo`, futuros} + reservado `core` para lifts/engine changes (D12). Si el primer token después de `luana-` no es brand conocida ni `core` ni `platform` → UNKNOWN.

**Fuente 2 — Manifest `.session.yaml` (datos estructurados):**

Archivo en raíz del worktree, generado auto por `new-session.sh`, gitignored:
```yaml
brand: vitalia
worktree_type: ephemeral          # principal | canonical | ephemeral
story_id: copilot-tools-impl
lane: be                           # opcional
tickets: [T-2, T-3]                # opcional, /pm-{brand} mantiene
created_at: 2026-05-17T20:00:00-05:00
created_by_skill: pm-vitalia
parent_branch: origin/main
notes: ""
```

Manifest NO incluye: estado dinámico story (vive en `{brand}/docs/product/stories/{story-id}/checkpoint.md`), archivos modificados (vive en `git status`), commit hashes (vive en `git log`). Es identidad estática del worktree.

**Coexistencia de las dos fuentes:**

| Caso | Path | Manifest | Resultado |
|---|---|---|---|
| Worktree creado con `new-session.sh` | EFÍMERO vitalia | presente, coincide | OK, contexto completo |
| Worktree principal | PRINCIPAL | ausente (no se crea ahí) | OK, contexto = PRINCIPAL |
| Canónico creado con script | CANÓNICO vitalia | presente, brand=vitalia, type=canonical | OK, contexto completo |
| Carpeta a mano sin script | EFÍMERO vitalia | ausente | UNKNOWN_EPHEMERAL → `/pm-{brand}` pide regularizar o regenerar manifest |
| Carpeta renombrada a mano | EFÍMERO comunify | presente, brand=vitalia | ERROR brand mismatch → escalate Chris |
| Nombre raro | UNKNOWN | irrelevante | UNKNOWN → escalate Chris |

**Consumidores:**
- Mecanismo A (SessionStart hook) — corre detección al abrir Claude/opencode
- Mecanismo E (`/pm-{brand}` step 0) — corre detección al invocar skill
- Mecanismo H (dashboard) — enriquece output con manifest
- Mecanismo F (wrapper docker) — sabe qué brand activar
- Mecanismo K (Warp Workflows) — usa misma lógica para naming auto de tabs

### D10. Sincronización canónicos (auto-FF + advisory)

Canónicos long-lived (`~/Proyectos/luana-{brand}/`) inevitablemente se atrasan respecto a `main`. Resuelto con 3 triggers + acción graduada por estado del worktree.

**Triggers:**

| ID | Trigger | Aplica a | Mec. |
|---|---|---|---|
| T1 | SessionStart hook (al abrir Claude/opencode) | PRINCIPAL + CANÓNICO | A |
| T2 | `/pm-{brand}` step 0 (bootstrap PM) | TODOS los `wip/*` (cualquier type) | E |
| T-push | PreToolUse hook en `git push` (+ wrapper portable opencode/manual) | TODOS los `wip/*` | L (nuevo) |

T3 (post-merge signal global) descartado: T1 + T-push cubren los dos momentos críticos. Fetch es barato; flag global agregaba complejidad sin ganancia.

**Acción graduada (T1 en CANÓNICO):**

| Estado worktree | Behind | Toca core? | Acción |
|---|---|---|---|
| Tree clean, 0 ahead | 0 | — | silencioso |
| Tree clean, 0 ahead | ≥1, FF puro posible | no | **AUTO FF** + 1 línea (`↑ synced N commits from main`) |
| Tree clean, 0 ahead | ≥1, FF puro posible | sí | **AUTO FF** + 1 línea con label CORE (`↑ N commits, K touch core/`) |
| Tree clean, ≥1 ahead | ≥1 (merge real) | — | advisory only (`behind N, ahead M — mergear manual`) |
| Tree dirty | ≥1 | no | advisory soft (`N commits behind — mergear cuando esté limpio`) |
| Tree dirty | ≥1 | sí | **advisory LOUD**: banner `CORE CHANGED while you worked` con commits + paths afectados |

**Worktree PRINCIPAL (en `main`):**
- Hook hace `git fetch origin main && git merge --ff-only origin/main` silencioso
- Si FF falla (raro — alguien commiteó local en main) → advisory + STOP, escalate
- Regla M5 vigente: `git pull` sigue prohibido. Fetch + merge --ff-only explícito sí está permitido (no es pull semánticamente).

**Definición operativa "toca core":**
```bash
git diff main..origin/main --name-only | grep -E '^core/luana-core-[^/]+/src/'
```
Cualquier match → label CORE escalado en output.

**T-push (PreToolUse + wrapper):**
- Antes de cualquier `git push origin wip/*`: fetch + chequea `git rev-list --count main..origin/main`
- Si ≥1 commit behind: advisory en stderr ("origin/main adelantó N commits, K tocan core"), recomienda merge antes
- **NO bloquea push** — Chris/Claude pueden continuar; si remoto rechaza non-fast-forward → STOP (regla M5)
- Wrapper portable `scripts/git/push-wip.sh` provee misma lógica para opencode/manual

**Estado guardado en `.session.yaml` (canónicos + efímeros):**
```yaml
# Campos extra escritos por T1/T2 — auto-actualizados, no editar a mano
last_sync:
  fetched_at: 2026-05-17T22:30:00Z
  origin_main_sha: b1c2d3e4...
  result: ff_auto | advisory_soft | advisory_loud | nothing | error
  commits_pulled: 3
  core_touched: false
```
`status-all.sh` (mec. H) consume `last_sync.fetched_at` + `last_sync.commits_pulled` para enriquecer dashboard.

### D11. Política merge a main (cadencia + trigger + excepciones)

**Cadencia base (default):**
- 1 squash-merge por story cuando `state=done` (auditor APPROVED + CHECKPOINTS.md aplicados)
- Checkpoint mid-story **opcional** cuando una mitad lógica está terminada (e.g., BE listo, FE pendiente). Requiere wip en estado limpio: todos los commits = unidad cerrada, próximos tickets no iniciados

**Trigger:** `/pm-{brand}` ejecuta squash-merge como parte de la transición `state=reviewing→done`. Plan + ejecución dentro del mismo step PM (delegable a Haiku worker via `commit-push` pattern).

**Mecánica squash-merge canonical:**
```bash
cd ~/Proyectos/luana-platform/                # principal
git fetch origin main
git merge --ff-only origin/main                # actualizar main local
git merge --squash wip/{brand}-{story-id}
git commit -m "feat({brand}): {story-id} shipped — {one-line summary}"
git push origin main
scripts/git/cleanup-session.sh {brand}-{story-id}  # remove worktree + branch local
```

**Mecánica checkpoint mid-story:** documentado, **no scripteado todavía**. Cuando aparezca el primer caso → codificar en `scripts/git/checkpoint-merge.sh` o extender `cleanup-session.sh`. Principio: rotar `wip/{brand}-{story-id}` a nueva branch desde `origin/main` post-squash (preservar uncommitted via stash si aplica).

**Excepciones formales:**

| Tipo | Branch pattern | Merge policy | Pre-merge check |
|---|---|---|---|
| Story estándar | `wip/{brand}-{story-id}[-{lane}]` | `/auditor` APPROVED → `/pm-{brand}` squash-merges al cerrar `state=done` | CHECKPOINTS.md aplicado + validators GREEN |
| Hotfix urgente | `hotfix/{brand}-{slug}` | **Bypass `/auditor` formal**. `/pm-{brand}` o Chris squash-merge directo | `repro_verified: true` (per `.claude/rules/hotfix-repro-mandatory.md`) + test regression RED→GREEN + smoke tests pass |
| Experimento / spike | `exp/{brand}-{slug}` | **NUNCA mergea a main**. Cleanup: extraer learnings + delete branch + remove worktree | Learning entry en `{brand}/docs/learnings/{date}-{slug}.md` antes de delete |
| Multi-lane story | `wip/{brand}-{story-id}-{lane}` | Cada lane mergea independiente cuando su `/auditor` lane APPROVED (D9: lanes son peers). Story cierra cuando todas las lanes mergearon | Checklist story estándar por lane |
| Core change | story estándar que toca `core/luana-core-*/src/` | Story estándar + `/pm-luana` promotion proposal con state ≥ `accepted` ANTES merge | Auditor downstream regression scope (R3) corrió en TODAS las brands consumidoras |

**Pre-merge checklist (`/pm-{brand}` verifica antes de squash):**

1. Worktree tree limpio (no uncommitted, no untracked salvo gitignored)
2. Story state = `developed` o `reviewing` — NUNCA mergear desde `developing`
3. Si state=`done`: CHECKPOINTS.md presente + APPROVED registrado
4. Validators GREEN: items de `04-validators.yaml::must_pass=true` corrieron en el worktree
5. Si delta toca `core/luana-core-*/src/`: promotion proposal `state=accepted|migrated`
6. Commit message: Conventional Commits + co-authored line

Cualquier check falla → reporta + STOP. Nunca silenciar.

### D12. Cambios al core (`luana-core-*`) — worktree dedicado + cross-brand consumption

**Tipos de cambio al core:**
- Promotion lift brand→core (sigue protocol `/pm-luana`)
- Nuevo Extension Point (EP-N)
- Cambio interno engine sin breaking (patch/minor)
- Breaking change engine (major bump, coordinación cross-brand requerida)

**Dónde vive: efímero dedicado `~/Proyectos/luana-core-{slug}/`**

| Item | Valor |
|---|---|
| Path filesystem | `~/Proyectos/luana-core-{slug}/` |
| Branch | `wip/core-{slug}` |
| Manifest `.session.yaml::brand` | `core` (pseudo-brand reservado) |
| Manifest `.session.yaml::worktree_type` | `ephemeral` |
| D8 detection | `luana-core-{slug}/?$` → EFÍMERO type=core (no brand) |
| Creator | `scripts/git/new-session.sh core <type> {slug}` (script aceptará `BRAND=core` como excepción al validador actual) |
| Cleanup | `scripts/git/cleanup-session.sh` (mismo que efímero brand) |

D3 naming table extendida con row "Lift core / cambio engine". D8 detection table extendida con caso CORE.

**Workflow promotion lift (post adopción worktree):**

```
1. Brand B (canónico ~/Proyectos/luana-{B}/) detecta patrón → escribe
   {B}/docs/learnings/{date}-{slug}.md con promotable=yes
2. /pm-luana scan → abre docs/promotion-protocol/proposals/{date}-{slug}.md state=proposed
3. /pm-luana ratifica fit core → state=under_review
4. Chris APPROVED → state=accepted
5. /pm-luana imprime comando para Chris ejecutar en nueva Warp tab:
     scripts/git/new-session.sh core lift {slug}
     cd ../luana-core-{slug}/
     claude
6. /dev-team en ese worktree:
   - mueve código {B}/backend/src/... → core/luana-core-X/src/luana_core_X/...
   - refactor {B}: import luana_core_X
   - tests en core + verifica tests brand B siguen pasando
   - bump core/luana-core-X/pyproject.toml::version (minor) + CHANGELOG
   - R3 downstream regression scope (corre tests TODAS las brands consumidoras)
7. /pm-luana o auditor APPROVED → squash-merge a main (D11 flow estándar)
8. cleanup worktree
9. T1 en TODOS los canónicos brand: detecta ↑ N commits CORE → AUTO FF (clean) o advisory LOUD (dirty)
```

**Cross-worktree dependency — 3 casos:**

| Caso | Escenario | Protocolo |
|---|---|---|
| A — Lift in-flight | Brand C necesita feature que está en `wip/core-{slug}` aún sin merge a main | Brand C story queda `state=ready` hasta lift mergee. Regla M5: NUNCA merge wip→wip. `/pm-luana` coordina prioridad si bloquea |
| B — Lift mergeado | Brand C quiere consumir feature ya en main | T1 detecta + auto-FF si tree clean. Brand C implementa import + tests. Si lift cambió `pyproject.toml`/`package.json`: T1 pide `uv sync` o `pnpm install` |
| C — Overlap WIP | Brand B canónico tiene cambios en archivos que el lift refactoró | T1 FF falla por conflict → advisory LOUD "merge conflict, resolver manual". Mitigación: cuando `/pm-luana` ratifica, dashboard H avisa qué brand canónicos overlap con lift scope |

**Detección "deps changed" (T1 + T-push extra):**
```bash
git diff main..origin/main --name-only | grep -E 'core/luana-core-[^/]+/(pyproject\.toml|package\.json)'
```
Match → advisory extra recomendando comando concreto:
- Python: `cd ~/Proyectos/luana-platform/ && uv sync`
- TS: `cd {brand}/frontend/ && pnpm install`

**No autorun:** T1/T-push NUNCA ejecutan `uv sync` ni `pnpm install`. Solo advisory. Chris/Claude deciden cuándo.

**Breaking change cross-brand:**
- Proposal con `breaking: true` en frontmatter
- `/pm-luana` plan incluye stories en cada brand consumidora coordinando migración
- Stories deben mergear a main en "release window" coordinado por `/pm-luana`
- Mientras una brand no migrada: tests fallan (esperado, parte del rollout)

### D13. Step 0 worktree detection (mec. E — SSoT en `.claude/rules/step-0-worktree.md`)

**SSoT:** `.claude/rules/step-0-worktree.md` (a crear). Cada `/pm-{brand}` y `/pm-luana` carga via `@.claude/rules/step-0-worktree.md` en frontmatter o body.

**Logic (10 pasos, ejecuta al bootstrap de cada invocación del skill):**

1. Detect worktree type via path regex (PRINCIPAL / CANÓNICO / EFÍMERO brand / EFÍMERO core / UNKNOWN)
2. Read manifest `.session.yaml` si existe
3. Verify cross-coherence: brand/type del manifest matches path regex
4. Manifest ausente + path UNKNOWN → STOP, escalate
5. Manifest ausente + path conocido → advisory "regenerar con `scripts/git/regenerate-manifest.sh` (mec. M)"
6. Si skill = `/pm-{brand-X}` y worktree.brand ≠ X → **HARD REFUSE + STOP + redirect**
7. Si skill = `/pm-{brand-X}` y worktree = CANÓNICO/EFÍMERO brand X → OK + leer story/lane manifest
8. Si skill = `/pm-luana` → permitir desde PRINCIPAL, CANÓNICO brand X, EFÍMERO core. Soft warn desde EFÍMERO brand-specific
9. Run T2 sync (misma lógica T1: fetch + maybe FF + advisory según estado tree+behind)
10. Output canonical block (compacto, visible Chris)

**Enforcement matrix:**

| Skill | Worktree | Verdict |
|---|---|---|
| `/pm-{brand-X}` | CANÓNICO/EFÍMERO brand X | OK proceed |
| `/pm-{brand-X}` | CANÓNICO/EFÍMERO brand Y (Y≠X) | **HARD REFUSE** — redirect "tab worktree X o /pm-luana" |
| `/pm-{brand-X}` | PRINCIPAL | **HARD REFUSE** — "principal no edita código brand" |
| `/pm-{brand-X}` | EFÍMERO core | **HARD REFUSE** — "core lift es /pm-luana territory" |
| `/pm-{brand-X}` | UNKNOWN | **HARD REFUSE** — escalate Chris |
| `/pm-luana` | PRINCIPAL | OK (default) |
| `/pm-luana` | CANÓNICO brand X | OK (cross-brand desde brand context) |
| `/pm-luana` | EFÍMERO core | OK (lift work) |
| `/pm-luana` | EFÍMERO brand X | OK + soft warn |
| `/pm-luana` | UNKNOWN | **HARD REFUSE** — escalate Chris |

**Output canonical (silent si all-OK, expandido si advisory/error):**

```
[step 0 worktree]
  path:     ~/Proyectos/luana-vitalia/
  branch:   wip/vitalia-copilot-tools-impl
  type:     CANÓNICO vitalia
  manifest: brand=vitalia story=copilot-tools-impl lane=—
  sync:     ✓ 0 commits behind origin/main
  others:   1 efímero vivo brand vitalia (wip/vitalia-design-review)
[step 0 OK]
```

Caso refuse:
```
[step 0 worktree]
  path:     ~/Proyectos/luana-comunify/  (manifest brand=comunify)
  skill:    /pm-vitalia
  verdict:  ✗ HARD REFUSE — brand mismatch

  Opciones:
  1. Cambiar Warp tab a worktree Vitalia (~/Proyectos/luana-vitalia/)
  2. Cross-brand visibility: /pm-luana

[step 0 STOP]
```

### D14. opencode parity

**Skills + rules:** opencode honra mismo directorio (`.claude/skills/`, `.claude/rules/`) + sintaxis compatible (`@imports`, frontmatter, slash commands). Step 0 (mec. N) y skills `/pm-{brand}` funcionan idéntico en ambos.

**Hooks:** NO paridad nativa. opencode no tiene SessionStart ni PreToolUse equivalentes.

**Estrategia: bash scripts como SSoT portable + Warp Workflows como atajo manual.**

| Logic | Claude Code | opencode |
|---|---|---|
| T1 SessionStart sync (mec. A) | Hook nativo invoca `scripts/git/check-sync.sh` | Manual: Chris corre `scripts/git/check-sync.sh` (Warp Workflow `sync-check` 2-click) |
| T-push PreToolUse (mec. L) | Hook nativo intercepta `git push` | Manual: Chris usa `scripts/git/push-wip.sh wip/X` en vez de `git push` (Warp Workflow `push-wip` 2-click) |
| Step 0 (mec. N) | Skill via `@.claude/rules/step-0-worktree.md` | Idéntico |
| new-session/cleanup-session (mec. B/C) | Bash scripts manuales | Idéntico |

**Scripts portables canonical (SSoT):**
- `scripts/git/new-session.sh` (mec. B)
- `scripts/git/cleanup-session.sh` (mec. C)
- `scripts/git/check-sync.sh` (T1 logic — Claude hook A + manual/opencode)
- `scripts/git/push-wip.sh` (T-push logic — Claude hook L + manual/opencode)
- `scripts/git/status-all.sh` (mec. H)
- `scripts/git/regenerate-manifest.sh` (mec. M)

**Rationale 3 capas:**
1. **Scripts bash** = verdad portable, funcionan terminal pelado
2. **Claude hooks** = sugar layer Claude Code (zero fricción daily)
3. **Warp Workflows** = sugar layer opencode/manual (2-click vs typing)

Si Claude rompe layer (2) o Warp rompe (3) → scripts (1) siguen funcionando manualmente.

**Compatibility check (al agregar feature nuevo):**
1. Funciona en Claude Code (hook + script)
2. Funciona en opencode (script + Warp Workflow opcional)
3. Funciona en terminal pelado sin tooling (script only)

Si (3) rompe → feature es Claude-exclusive, marcar como tal.

### D6. Reglas operativas heredadas (siguen vigentes con redefinición worktree)

| Regla | Resumen | Estado |
|---|---|---|
| M2 — Owner único SSoT | Solo `/pm-luana` o `/pm-{brand}` editan `learnings.md`, `BACKLOG.md`, `MEMORY.md`, `PORTFOLIO.md`. Builders nunca | Vigente |
| M3 — Tests/Docker/migrations SECUENCIAL por brand | Una sesión por brand corre `make dev-{brand}`, `pytest --integration`, alembic generate a la vez | Vigente + endurecida (max 1 stack/brand) |
| M4 — Claim by commit | `/pm-{brand}` cambia `state` en checkpoint.md + commit/push inmediato pre-claim | Vigente |
| M5 — NO pull / NO force / NO revert sin aprobación | `git pull`, `git push --force`, `git revert` prohibidos. Push falla non-fast-forward → STOP, reportar | Vigente |
| M6 — `/pm-{brand}` bootstrap pregunta story activa | No asume default | Vigente |
| M7 — Subagentes con paths PRIMARIOS del story | Read-all OK, extend-no-destroy en archivos ajenos | Vigente |
| M8 — Tocar archivos otra sesión | Solo si entendés leyendo + extend/append no replace + STOP si rompe | Vigente |
| M11 — Push cada ≤30 min con cambios significativos | Safety net WIP | Vigente |

---

## Mecanismos (estado verificado 2026-06-01)

| # | Mecanismo | Dónde | Estado |
|---|---|---|---|
| A | Hook `SessionStart` Claude Code que detecta cwd + clasifica worktree + verifica symlink venv + imprime estado | `~/.claude/settings.json` | ✅ **implementado** (SessionStart en settings.json confirmado) |
| B | `new-session.sh`: nace de `origin/main` fresco + crea symlink `.venv` + copia `.env.dev.template` por brand + genera `.session.yaml` manifest | `scripts/git/new-session.sh` | ✅ **implementado** (`new-session.sh` existe y es el script canónico) |
| C | `cleanup-session.sh`: verifica tree limpio + push final + prompt "¿mergee branch a main?" + remove worktree | `scripts/git/cleanup-session.sh` | ⚠️ **existe** — verificar si las mejoras descritas están completas |
| D | Pre-commit hook checks: (i) bloquear commit directo en `main`; (ii) migration collision detection; (iii) lockfile root undeclared warning | `scripts/git-hooks/pre-commit` | ✅ **implementado** (sección "Block direct commit to main" confirmada en pre-commit) |
| E | `/pm-{brand}` step 0 obligatorio: detect worktree mode + verify branch wip + list cross-brand modified files + list otros worktrees vivos de la misma brand | `.claude/skills/pm-{brand}/SKILL.md` (×4 + template) | ✅ **implementado** (step 0 confirmado en pm-vitalia/SKILL.md + consumido via `@.claude/rules/step-0-worktree.md`) |
| F | Wrapper `make dev-{brand}` con lock: aborta si ya hay containers vivos de esa brand | `scripts/dev-lock-check.sh` + `Makefile` | ✅ **implementado** (`scripts/dev-lock-check.sh` existe, Makefile lo invoca) |
| G | Wrapper alembic generate con lock: warning si remote tiene otra `wip/{brand}-*` con migrations recientes | `scripts/generate_migration.py` | ❌ **pendiente** (`scripts/generate_migration.py` no existe) |
| H | Dashboard `scripts/git/status-all.sh`: enriquece `git worktree list` con dirty status + last commit + story-id (manifest) + Docker activo per brand | `scripts/git/status-all.sh` | ✅ **implementado** (113 líneas, existe en scripts/git/) |
| I | PS1 customizado bash: `[luana-{suffix} {branch} {dirty}]$` | `scripts/git/ps1-luana.sh` | ✅ **implementado** (`scripts/git/ps1-luana.sh` existe — integración a `~/.bashrc` depende de Chris) |
| J | `.session.yaml` manifest auto-generado por `new-session.sh` (parte de mecanismo B) + consumido por mecanismos E, H | dentro de B | ✅ **implementado** (parte de `new-session.sh`) |
| K | **Warp Workflows** envolviendo B, C, H como atajos ejecutables desde palette Warp. Scripts bash siguen siendo SSoT portable | Warp settings (yaml export per workflow) | ⏳ **pending** (opcional, depende de Chris setup Warp) |
| L | **Pre-push sync check**: PreToolUse hook en Claude Code + wrapper portable `scripts/git/push-wip.sh`. NO bloquea (si remoto rechaza → STOP per M5) | `~/.claude/settings.json` PreToolUse + `scripts/git/push-wip.sh` | ✅ **implementado** (PreToolUse en settings.json + `push-wip.sh` existe) |
| M | **`regenerate-manifest.sh`**: utility para worktrees creados a mano sin `new-session.sh`. Idempotent. | `scripts/git/regenerate-manifest.sh` | ✅ **implementado** (`regenerate-manifest.sh` existe) |
| N | **Step 0 worktree SSoT**: `.claude/rules/step-0-worktree.md` consumido por `@import` desde cada `/pm-{brand}` y `/pm-luana` | `.claude/rules/step-0-worktree.md` | ✅ **implementado** (file existe, skills cargan via `@.claude/rules/step-0-worktree.md`) |

---

## Temas pendientes de discutir (orden actual)

- **#4 Naming + descubribilidad** — cómo a las 11pm con 3 worktrees activos sabés qué corre dónde + cómo `/pm-{brand}` lo detecta al bootstrap. (Refina D3 + alimenta mecanismos A y E.)
- ✅ **#5 Política merge + sincronización canónicos** — cementado 2026-05-17
  - Sub-tema sincronización → D10 + mec. A/E/L
  - Sub-tema merge policy → D11 + excepciones (hotfix bypass, exp nunca, multi-lane independiente, core change con promotion proposal)
- ✅ **#6 Caso especial core (`luana-core-*`)** — cementado 2026-05-18 → D12 (efímero dedicado `luana-core-{slug}` + cross-worktree dependency 3 casos + deps changed advisory)
- ✅ **#7 Skills `/pm-{brand}` enforcement** — cementado 2026-05-18 → D13 + mec. M (regenerate-manifest) + mec. N (step-0-worktree SSoT)
- ✅ **#8 Opencode parity** — cementado 2026-05-18 → D14 (3 capas: scripts portable + Claude hooks + Warp Workflows)

Una vez cubiertos #4-#8 + cementadas las decisiones derivadas → este doc se promueve a `status: cemented`, se crea ADR-005, y arrancamos implementación A-K.

### Entregables finales del proceso (estado verificado 2026-06-01)

| Entregable | Para | Status |
|---|---|---|
| Este doc en `status: cemented` | Owner /pm-luana | ⚠️ pending (actualizar ADR-009 addendum) |
| ADR-005 worktree policy | Decisión arquitectónica | ✅ existe (`docs/architecture/luana-platform/ADR-005-worktree-policy.md`) |
| ADR-009 single-hub (supersede D4/D9) | Decisión arquitectónica | ✅ cementado 2026-05-28 |
| `.claude/rules/parallel-safety.md` sincronizado con este doc | Runtime rule cargada en CLAUDE.md | ✅ sincronizado (M1-M14 en parallel-safety.md) |
| **Manual operativo Warp** (`docs/process/warp-multibrand-handbook.md` o equivalente) | Chris — cómo usar Warp día a día con el proceso completo: tabs, workflows, atajos, troubleshooting | **pending (Chris-explícito 2026-05-17)** |
| Mecanismos A-N implementados (excepto G, K) | Sistema | ✅ mayoría implementados — ver tabla mecanismos arriba |

---

## Inicio sesión (snapshot operativo actual, refinable)

```bash
cd ~/Proyectos/luana-{brand}/                # canónico de la brand
git status --short
git branch --show-current                    # debe ser wip/{brand}-{slug}
git worktree list                            # ver qué otros worktrees están vivos
git log --oneline -3
```

- Branch `wip/{brand}-*` limpio en worktree dedicado → proceder.
- Branch `main` → estás en principal, no editar código.
- Tree sucio con archivos AJENOS a la brand del worktree → STOP, reportar lista, no tocar.

## Cierre sesión (snapshot operativo actual, refinable)

`"eso es todo"` / `"gracias"` / `"cierra"` / `/cierra-limpio`:

1. `git status --short`
2. Cambios propios → stage por nombre exacto + conventional commit + `git push origin wip/{brand}-{slug}` + reportar SHA
3. Archivos ajenos → reportar intactos
4. Si efímero y story cerrada → `scripts/git/cleanup-session.sh {brand}-{slug}` desde principal (cuando esté mejorado, mecanismo C)

## Prohibido (actualizado)

- `git pull` (cualquier forma)
- `git fetch && merge` automático (solo `fetch + merge` deliberado para traer main a wip)
- `git push --force` / `--force-with-lease`
- `git revert` sin aprobación
- `git reset --hard` sin aprobación
- `git add .` / `-A` / `-u`
- `git commit --no-verify`
- Editar código en worktree principal (`luana-platform/` en `main`)
- Misma branch `wip/*` checkouteada en 2 worktrees (git lo bloquea por diseño)
- `make dev-{brand}` en 2 worktrees de la misma brand simultáneamente
- Builders editando SSoT (`learnings.md`, `BACKLOG.md`, `MEMORY.md`, `PORTFOLIO.md`)

## Conflict resolution (vigente)

Si encontrás archivo modificado por otra sesión (en el branch wip propio o al mergear a main):
1. **NO sobreescribir.** Leer primero.
2. Si conflict de scope → escalate Chris.
3. Si append-friendly (logs, IMPL-LOG, history) → append OK.
4. Si replacement obvio (typo, refactor) → STOP + reportar antes proceder.

---

## Referencias

- `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` — triple-branch policy (rationale)
- `docs/architecture/luana-platform/ADR-005-worktree-policy.md` — worktree policy (existe)
- `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md` — **single-hub canonical topology (supersede D4/D9 rotación)**
- `.claude/rules/parallel-safety.md` — runtime rules sintetizadas M1-M14 (sincronizadas)
- `.claude/rules/git-safety.md` — triple-branch operacional
- `.claude/rules/git-haiku-delegation.md` — commit+push delegation pattern
- `scripts/git/new-session.sh` — creación worktree (mecanismo B, implementado)
- `scripts/git/cleanup-session.sh` — cierre worktree (mecanismo C, existe)
- `docs/process/git-workflow-multibrand.md` — workflow git multi-brand (verificar consistencia al cementar)
