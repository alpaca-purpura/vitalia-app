# Worktree Strategy — Single-Hub default, detail operativo (moved from .claude/rules/ 2026-05-30)

**Origen:** conversación 2026-05-27 — Chris quiere paralelizar refinamiento+UX y arquitectura+desarrollo sin pisarse.

**Cement-date:** 2026-05-27. **★ v2 cement 2026-05-28 (ADR-009):** el default se INVIRTIÓ — de "2 worktrees separados" a **hub único por marca con N sesiones**. Razón: los worktrees separados fragmentaban el estado (las builds no veían las refinadas nuevas, el cockpit nunca tenía la foto completa, sync ceremonial crónico). SSoT: `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md`. **Aplica a:** brands activas (vitalia, comunify) + futuras.

## Regla cardinal v2 — hub único por marca (DEFAULT)

Para paralelizar refinamiento + build dentro de la MISMA marca, **NO se crean worktrees separados**. Todas las sesiones corren sobre el **único worktree canónico** de la marca (el "hub"), coordinadas por **bucket locks** (M14):

```
~/Proyectos/luana-{brand}/   (wip/{brand})  = HUB único · cockpit corre aquí (:400X) y ve TODO
  ├── Sesión 1: Chris refina            → bucket docs        (/pm-{brand}, /po-ux, /architect)
  ├── Sesión 2: build historia A        → bucket code:{modA} (/dev-team, /auditor)
  └── Sesión 3: build historia B        → bucket code:{modB} (/dev-team, /auditor)
```

Por qué funciona (los 4 dolores del modelo viejo desaparecen): un solo filesystem = un solo SSoT de estado → las builds ven las refinadas al instante, el cockpit tiene la foto completa, refino viendo qué se construye, cero sync. Detalle + riesgos acotados (locks module-scoped + commit por pathspec): ADR-009 § 2.

### Dos mecanismos que blindan el cruce de archivos

1. **Bucket locks module-scoped** (`.claude/rules/parallel-safety.md` M14): `code:{module}` → dos builds de módulos distintos corren en paralelo; mismo módulo se serializa (dependencia real). `docs` no choca con `code:*`. Cada skill hace `scripts/git/session-lock.sh acquire {bucket} {skill} [story-id]` en su step 0; `release` al cerrar.
2. **Commit por pathspec** (`.claude/rules/git-haiku-delegation.md`): el índice git es compartido entre sesiones del mismo árbol → commitear con `git commit <ruta-exacta>` (nunca `git add .`) evita contaminación cruzada.

### Build-claim + visibilidad en el cockpit

`/dev-team` Step 0 hace `session-lock.sh acquire code:{module} dev-team {story-id}` (lane vía `$LUANA_LANE`, fallback `pid<PID>`). El cockpit lee `.session-locks/*.lock` y pinta **"🔨 {lane}"** sobre la story en construcción → Chris tiene mapeado qué sesión construye qué. `release` al cerrar; si la sesión muere, el lock auto-libera por PID muerto.

## Modo EXCEPCIÓN — worktree separado (solo scopes divergentes)

Worktrees dedicados NO desaparecen, pero dejan de usarse para "refine vs build dentro de una marca". Se reservan para: lift core (`wip/core-*`), cross-cutting (`wip/protocol-*`), experimento divergente (`exp/*`), hot-fix aislado (`hotfix/*`), u **otra marca** (su propio hub). El split refine-lane/build-lane del v1 (tabla abajo) queda como referencia histórica para esos casos divergentes, NO como operación diaria.

## Scope per worktree (cuando usás el modo excepción)

| Worktree | Permitido editar | Prohibido editar |
|---|---|---|
| `luana-{brand}-refine` (refine lane · EXCEPCIÓN) | `{brand}/docs/product/stories/{new-id}/` (specs/designs/arch) + `{brand}/docs/product/{outcomes,capabilities,modules}/` + `{brand}/docs/learnings/` (prior-art capture) | `{brand}/backend/src/` + `{brand}/frontend/src/` (rompe story-in-progress en worktree build) |
| `luana-{brand}` (canonical · HUB en v2) | `{brand}/docs/**` + `{brand}/backend/src/` + `{brand}/frontend/src/` + tests + migrations — todo bajo bucket locks | (nada extra · scope gate M13 aísla por marca) |

## Setup ad-hoc

```bash
# Worktree refining lane (nuevo, además del canónico build)
cd ~/Proyectos/luana-platform
git worktree add ~/Proyectos/luana-{brand}-refine -b wip/{brand}-refine
cd ~/Proyectos/luana-{brand}-refine
cat > .session.yaml <<EOF
brand: {brand}
type: REFINE_LANE
canonical: false
purpose: "Refinamiento concurrent stories mientras canónico build develop story READY"
EOF
```

`scripts/git/new-session.sh` debería tener flag `--refine-lane` que lo automatice (TBD).

## Naming convention worktrees

| Tipo | Path | Branch | Cuándo |
|---|---|---|---|
| `~/Proyectos/luana-platform/` | PRINCIPAL | `main` | Siempre (read cross-brand + merges) |
| `~/Proyectos/luana-{brand}/` | CANÓNICO build | `wip/{brand}` | Story READY → dev-team construye |
| `~/Proyectos/luana-{brand}-refine/` | REFINE_LANE | `wip/{brand}-refine` | Refinar próximas stories en paralelo |
| `~/Proyectos/luana-{brand}-story-{id}/` | EFÍMERO build (ad-hoc) | `wip/{brand}-{id}` | Hot-fix urgente o experimento |
| `~/Proyectos/luana-protocol-{slug}/` | EFÍMERO protocol | `wip/protocol-{slug}` | Cross-cutting changes (rules/hooks/skills) |
| `~/Proyectos/luana-core-{slug}/` | EFÍMERO core lift | `wip/core-{slug}` | Promotion gate brand→core via /pm-luana |

## "No egoísmo" clause

Si la sesión refine ve un bug claro en código vivo (que pertenece al worktree build), **NO lo ignora**. Workflow:

1. Documenta en `T-{n}-impl-log.md` de la story que estás refinando, sección `## Cross-worktree observed bugs`
2. Crea archivo `{brand}/docs/observed-bugs/{date}-{slug}.md` con: file:line + symptom + suggested fix
3. Notifica a Chris en respuesta ("vi bug en X, lo dejé documentado en {path}, ¿lo arreglo aquí o lo dejo para hotfix?")
4. Chris decide:
   - **Hotfix here**: refine lane fixea + commit en mismo wip/{brand}-refine + push (override sospecha = ratificación Chris)
   - **Hotfix dedicado**: crear worktree `~/Proyectos/luana-{brand}-hotfix-{slug}/` con branch `hotfix/{brand}-{slug}` (per parallel-safety) + Chris asigna a sesión que lo trabaje
   - **Deferred**: documentado en observed-bugs/ + agregado al BACKLOG.md como story idea

Anti-egoísmo: **NUNCA** ignorar un bug visible "porque no es mi worktree" — siempre dejar rastro (mínimo file en observed-bugs/).

## Cross-worktree sync (post squash-merge)

Cuando worktree build squash-mergea su story a main:

1. Worktree refine debe **sincronizarse con main** ANTES de cerrar próxima refinement (per `.claude/rules/git-safety.md` § Sync wip/{brand} con main).
2. Si refine tiene cambios specs/designs ahead, hacer merge `origin/main` en refine (preserva refinement work + trae build work).
3. Sin sync: refine queda atrasado + spec puede contradecir código ya mergeado.

## WIP cap impact

Per `parallel-safety.md` M14: N sesiones mismo cwd permitido con lock por bucket (code/docs/tests). Worktree dual reduce contención:

- Worktree refine → lock bucket `docs` (PM/PO/architect están en bucket docs)
- Worktree build → lock bucket `code` (dev-team/auditor están en bucket code)
- Sin colisión: paralelismo natural sin esperar locks

## Anti-patterns prohibidos

- ❌ Worktree refine editando `{brand}/backend/src/` o `{brand}/frontend/src/` (viola scope discipline)
- ❌ Worktree build editando `{brand}/docs/product/stories/{id-distinto}/` (rompe refinamiento concurrent)
- ❌ Misma branch en 2 worktrees (`wip/{brand}` en build + `wip/{brand}` en refine — git bloquea por diseño)
- ❌ Bug visto en otra worktree pero ignorado sin documentar en observed-bugs/
- ❌ Refine lane sin sync con main post squash-merge → spec contradice código merged
- ❌ Hot-fix urgente desde refine lane sin Chris ratify scope override
- ❌ Worktree refine creado sin `.session.yaml` (manifest mandatory per `step-0-worktree.md`)
- ❌ Worktree build cerrando story sin sync refine (refine pierde context post-merge)

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | Pre-commit hook scope gate (`scripts/git-hooks/pre-commit` Sec 13) extend a detectar worktree type via `.session.yaml.type` + bloquea cross-scope | ⏳ hook extend |
| 2 | `scripts/git/new-session.sh` agregar flag `--refine-lane` que setup correcto | ⏳ script update |
| 3 | `/dev-team` Step 0 detecta si está en REFINE_LANE → HARD REFUSE ("dev-team no aplica en refine lane, ve a worktree canónico build") | ⏳ skill update |
| 4 | `/pm-{brand}` y `/po-ux` step 0 detectan si están en CANÓNICO build con story develop activa → advisory "considera worktree refine lane" | ⏳ skill update |
| 5 | `scripts/git/status-all.sh` dashboard incluye column `lane` (build/refine) per worktree | ⏳ script update |

## Referencias

- `.claude/rules/parallel-safety.md` D2 + M14 — base topología + locks
- `.claude/rules/step-0-worktree.md` — manifest + verification
- `.claude/rules/git-safety.md` § Sync wip/{brand} con main — post squash-merge cross-worktree sync
- `.claude/rules/anti-duplication-refining.md` — prior-art scan (consumer de refine lane)
- `docs/architecture/luana-platform/ADR-005-worktree-policy.md` — decisión worktrees
