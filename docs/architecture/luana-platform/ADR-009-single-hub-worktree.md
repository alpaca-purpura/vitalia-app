# ADR-009 — Single-Hub Worktree por marca (N sesiones / mismo árbol / estado único)

> **Status:** ACCEPTED
> **Date:** 2026-05-28
> **Decision-makers:** Chris (alpacapurpura@) + Claude Opus 4.8 (advisory)
> **Supersedes:** none
> **Superseded by:** none
> **Builds on:** [ADR-005](./ADR-005-worktree-policy.md) (worktree policy + topología + buckets M14)
> **Related docs:**
>
> - `.claude/rules/worktree-dual-strategy.md` — rule 26 (invertida por este ADR: hub único = default)
> - `.claude/rules/parallel-safety.md` — M14 (extendido: code locks module-scoped)
> - `.claude/rules/git-haiku-delegation.md` — commit por pathspec (índice compartido)
> - `scripts/git/session-lock.sh` — bucket lock + build-claim (story_id + lane)
> - `tools/luana-cockpit/` — lee `.session-locks/` → badge "🔨 lane" por story
> - `CLAUDE.md` § Cockpit · Paradigma A — convención per-worktree (sigue válida)

## 1. Context

### 1.1 El flujo diario de Chris cambió

Post-machinery-hardening (2026-05-28), el día a día de Chris es **refinar historias funcionalmente** (cada funcionalidad, regla de negocio, todo claro) antes de pasarlas al `/architect`, y **en paralelo** dejar que un par de sesiones ejecuten `/architect → done` sobre historias ya refinadas. Sube el WIP de `refining` + `refined`; el build corre autónomo de fondo.

### 1.2 El modelo de worktrees separados fragmentaba el estado

`worktree-dual-strategy.md` (rule 26, v1) recomendaba **worktrees separados**: uno `refine` (docs) + uno `build` (código). Operando así aparecieron 4 dolores reales:

1. **Las sesiones de build no se enteran de nuevas historias refinadas** — cada worktree es una copia del filesystem; una refinada en el worktree A no existe en el worktree B hasta merge/sync.
2. **Mientras refino, no veo qué se está construyendo** — sin el estado compartido, refino a ciegas respecto al build en vuelo.
3. **El cockpit nunca tiene la foto completa** — es filesystem-as-DB de UN worktree; el estado vive repartido en N árboles.
4. **Sync ceremonial** — re-sincronizar docs entre worktrees post squash-merge era fricción crónica.

### 1.3 Diagnóstico de causa raíz

Se estaban mezclando **dos SSoT con necesidades opuestas**:

| SSoT | Qué es | Qué necesita | Worktrees |
|---|---|---|---|
| **Código** | `{brand}/{backend,frontend}/src/` | aislamiento (dos editores del mismo archivo = conflicto) | ayudan |
| **Estado/docs** | `stories/*/checkpoint.md`, capabilities, lo que lee el cockpit | visibilidad compartida en tiempo real | **rompen** |

El worktree fue diseñado para forkear *ramas de código*. Pero la unidad de coordinación de Chris es el **estado** (qué historia está dónde) y el estado debe ser único y visible. Forkear el filesystem fragmenta el estado → exactamente los 4 dolores.

## 2. Decision

**Un worktree canónico por marca = el "hub".** Es el único SSoT de la marca: docs, estado, cockpit y los builds viven ahí. Múltiples sesiones Claude/opencode corren sobre el MISMO árbol simultáneamente.

```
~/Proyectos/luana-vitalia   (wip/vitalia)  = HUB único de vitalia
  ├── Sesión 1: Chris refina (bucket docs)
  ├── Sesión 2: /architect → /dev-team → /auditor historia A (bucket code:scheduling)
  └── Sesión 3: /dev-team historia B                        (bucket code:crm)
  → cockpit corre aquí (:4002) y ve TODO: refining + ready + developing + done
```

### 2.1 Por qué resuelve los 4 dolores

1. **Build descubre refinadas** → no hay nada que descubrir cross-worktree: es un solo árbol. `/dev-team` al hacer pickup lee el filesystem vivo y ve las `ready` al instante.
2. **Refino viendo el build** → el cockpit en el hub muestra A `developing` mientras refino C. Tengo la visibilidad para decidir.
3. **Cockpit completo** → un filesystem = una foto. Siempre.
4. **Cero sync ceremonial** → no hay docs repartidas que reconciliar.

### 2.2 El único riesgo (cruce de archivos) está acotado por 2 mecanismos

**(a) Locks por bucket module-scoped (extiende M14).** El bucket `code` se sub-divide por módulo: `code:{module}`. Dos builds sobre módulos distintos (`code:scheduling` vs `code:crm`) NO contienden → corren en paralelo de verdad. Dos historias que tocan el MISMO módulo comparten bucket → se serializan (que es lo correcto: tienen dependencia real). `docs` sigue siendo un bucket único (refinamiento) y no choca con `code:*`.

**(b) Commit por pathspec (índice git compartido).** N sesiones en el mismo árbol comparten `.git/index`. Si la sesión 1 hace `git add fileA` y la 2 `git add fileB`, el commit de una arrastra los archivos de la otra. **Mitigación:** commitear con `git commit <ruta-exacta> -m "..."` (partial commit por pathspec) — commitea SOLO esos paths, ignorando el índice. Combinado con la regla ya vigente (`nunca git add .`, stagear por nombre exacto) elimina la contaminación cruzada. Editar archivos (la fase larga del build) es paralelo-seguro; solo la ventana de commit usa pathspec.

### 2.3 Visibilidad de sesiones en el cockpit

`/dev-team` Step 0 hace **build-claim**: `scripts/git/session-lock.sh acquire code:{module} dev-team {story-id}` (lane vía `$LUANA_LANE`, fallback `pid<PID>`). El claim se registra en `.session-locks/*.lock` (gitignored, runtime). El cockpit lee esos locks (chequea PID vivo) y pinta un badge **"🔨 {lane}"** sobre la card de la historia en construcción → Chris tiene mapeado qué sesión construye qué. Al cerrar la historia, `/dev-team` hace `release`. Si una sesión muere, el lock auto-libera por PID muerto (no quedan claims fantasma en git).

### 2.4 Multi-marca

Cada marca = su propio hub (`~/Proyectos/luana-vitalia`, `~/Proyectos/luana-comunify`, …). Mismo modelo, sin cruce: (a) filesystem distinto, (b) scope gate M13 (pre-commit Section 13) ya prohíbe que `wip/{brand}` toque algo fuera de `{brand}/**`. Una segunda marca en paralelo se resuelve idéntico sin tocar la primera.

### 2.5 Docker refuerza el modelo

Solo se puede correr un stack por marca (los puertos 8002/3002 colisionan). Un hub por marca = un stack = sin conflicto. Esto *refuerza* el hub único en lugar de pelearlo.

### 2.6 Los worktrees separados NO desaparecen — quedan para scopes divergentes

| Caso | Worktree dedicado |
|---|---|
| Lift core brand→core | `~/Proyectos/luana-core-{slug}` (`wip/core-*`) — `/pm-luana` gate |
| Cross-cutting (rules/cockpit/skills/templates) | `~/Proyectos/luana-protocol-{slug}` (`wip/protocol-*`) |
| Experimento divergente que desestabilizaría el hub | `~/Proyectos/luana-{brand}-exp-{slug}` (`exp/*`, nunca mergea) |
| Hot-fix urgente aislado | `~/Proyectos/luana-{brand}-hotfix-{slug}` (`hotfix/*`) |
| **Otra marca** | su propio hub |

Lo que se **deja de hacer** es el split refine-worktree vs build-worktree *dentro de una misma marca*.

## 3. Consequences

### 3.1 Positivas

- Cockpit siempre completo; refinadas visibles al instante para builds; refino con visibilidad del build en vuelo.
- Builds paralelos reales (módulos disjuntos) sin worktrees extra ni sync.
- Menos fricción operativa diaria (cero re-sync de docs cross-worktree).
- Escala lineal a N marcas (cada una su hub).

### 3.2 Costos / riesgos aceptados

- Dos builds sobre el MISMO módulo se serializan (aceptable: es dependencia real).
- Índice git compartido exige disciplina de **pathspec commit** (mecanizado en `git-haiku-delegation.md`).
- El cockpit muestra `developing` desde checkpoint; el lane viene del lock runtime — si una sesión no hace build-claim (build manual sin `/dev-team`), la card muestra `developing` sin lane (degradación graciosa, no error).

### 3.3 Reversibilidad

Si en el futuro el equipo crece (2º dev) o un build necesita aislamiento real de dependencias, se vuelve a worktrees separados puntualmente para ese caso sin revertir el ADR (la § 2.6 ya los contempla como excepción).

## 4. Enforcement

| Layer | Mecanismo | Estado |
|---|---|---|
| 1 | `worktree-dual-strategy.md` rule 26 v2: hub único = default, separado = excepción | ✅ este PR |
| 2 | `parallel-safety.md` M14: code locks module-scoped (`code:{module}`) | ✅ este PR |
| 3 | `session-lock.sh`: acepta `code:{module}` + registra story_id + lane | ✅ este PR |
| 4 | `git-haiku-delegation.md`: commit por pathspec en escenario multi-sesión | ✅ este PR |
| 5 | `/dev-team` Step 0: build-claim acquire + release | ✅ este PR |
| 6 | Cockpit: `/api/sessions` lee `.session-locks/` → badge 🔨 lane por story | ✅ este PR |
| 7 | Scope gate M13 (pre-commit) ya aísla por marca | ✅ vigente |
