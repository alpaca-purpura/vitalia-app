<!-- voseo-allowed: internal protocol redesign documentation for Chris, not user-facing -->

> ✅ IMPLEMENTADO (histórico) — el plan se ejecutó; ver ADR-009 + parallel-safety.md

# Worktree Protocol v2 — plan ejecutable

> **Cement-date target:** 2026-05-18
> **SSoT supersedes:** `docs/process/parallel-sessions-protocol.md` D2/D3/D4/D9/D10 (modelo v1 cementado 2026-05-18 mañana).
> **ADR addendum:** `docs/architecture/luana-platform/ADR-005-worktree-policy.md` (sección v2 al final, no rewrite).
> **Origen:** caso vitalia 2026-05-18 — canónico apuntó a rama temporal de story, fantasma creado por sub-agent isolation:worktree, sesión single-thread (no permitía paralelo docs+dev), cross-brand commits acumulados en wip/vitalia-slice-1-shipping.
> **Filosofía:** KISS. Vos te enfocás en el producto. Yo (claude) manejo git/branches. Imposible trabajar sobre código viejo y desactualizar otra sesión.

## Resumen ejecutivo (5 cambios CORE + 7 refinements)

| # | Cambio | Resuelve qué problema | Toca qué archivos |
|---|---|---|---|
| **1** | Canónico = `wip/{brand}` estable (NO rota story-by-story) | Caso vitalia: canónico apuntó a wip/vitalia-slice-1-shipping mezclando 3 stories | `parallel-sessions-protocol.md` D2/D3/D4 · `new-session.sh` · `step-0-worktree.md` |
| **2** | Sub-agent worktree BAN total (Architect/Auditor/Builder trabajan in-place) | Caso vitalia: fantasma `luana-vitalia-infra-cross-cutting` creado por sub-agent + nunca cleanup | `parallel-safety.md` § sub-agent rule · `.claude/agents/*` system prompts · arch fitness test |
| **3** | Sync KISS activo: auto-merge si limpio, prompt si conflict, BLOQUEA push si behind | Comunify "by luck": cherry-pick funcionó solo porque scopes disjuntos | `parallel-sessions-protocol.md` D10 · `step-0-worktree.md` · NEW `sync-from-main.sh` · `push-wip.sh` |
| **4** | Scope per branch (sin cross-brand mixing) | Caso vitalia: wip/vitalia-slice-1-shipping acumuló cambios de comunify/ + modelo | `pre-commit` Section 13 NEW · `parallel-safety.md` § scope rule |
| **5** | N sesiones paralelas mismo cwd (lock por bucket: code/docs/tests) | Pedido user: sesión docs ideación en paralelo a dev en mismo canónico | `parallel-sessions-protocol.md` D9-bis NEW · `parallel-safety.md` · NEW `session-lock.sh` |
| 6 | Manifest auto-fix si desync (branch real ≠ manifest.branch) | Caso vitalia: manifest decía wip/vitalia-bootstrap, real era wip/vitalia-slice-1-shipping | `step-0-worktree.md` |
| 7 | Worktree story explicit user-only (flag `--explicit-user-request`) | Modelo viejo: skills creaban story worktrees automático → caos | `new-session.sh` |
| 8 | Pre-merge enforce: `git fetch origin main && git merge origin/main` en wip ANTES de squash-merge | Garantía: nunca squash-merge con código viejo | `push-wip.sh` · `/pm-{brand}` skill step pre-merge |
| 9 | `cleanup-session.sh` idempotente + verbose | Limpieza incompleta vitalia | `cleanup-session.sh` |
| 10 | ADR-005 addendum v2 | Documentar decisión cementación v2 | `ADR-005-worktree-policy.md` |
| 11 | Skills `/pm-{brand}` + `/pm-luana` step 0 con sync activo | Skills consumen modelo nuevo | `pm-luana/SKILL.md` + per-brand bootstrap |
| 12 | Plan doc (este file) | SSoT del rediseño | `docs/process/worktree-protocol-v2-plan.md` |

## Detalle de los 5 CORE

### CORE #1 — Canónico `wip/{brand}` estable

**Modelo v1:**
- Canónico `~/Proyectos/luana-{brand}/` con branch `wip/{brand}-{slug}` que **rota** según story
- Resultado: el nombre del path nunca matchea la branch; manifest se desactualiza; trabajo acumula sin context claro

**Modelo v2:**
- Canónico `~/Proyectos/luana-{brand}/` SIEMPRE en branch `wip/{brand}`
- Stories se trabajan EN ESA branch (commits + squash-merge a main sin cambiar de branch)
- Branch `wip/{brand}` vive forever, acumula squash-merges entrantes desde main
- Worktree efímero `~/Proyectos/luana-{brand}-{story-id}/` con branch `wip/{brand}-{story-id}` SOLO si user pide explícito

**Diff D2 en `parallel-sessions-protocol.md`:**

```diff
- | `~/Proyectos/luana-{brand}/` | Canónico long-lived | rota `wip/{brand}-*` según story activa | ✅ SÍ (1 sesión a la vez) | Semanas/meses |
+ | `~/Proyectos/luana-{brand}/` | Canónico long-lived | `wip/{brand}` ESTABLE (nunca rota) | ✅ SÍ (N sesiones paralelas con lock buckets) | Permanente |
```

**Diff D3 en `parallel-sessions-protocol.md`:**

```diff
- | Canónico long-lived | rota `wip/{brand}-{slug}` según story activa | `~/Proyectos/luana-{brand}/` |
+ | Canónico long-lived | `wip/{brand}` ESTABLE | `~/Proyectos/luana-{brand}/` |
```

**Diff `new-session.sh`:** TYPE=canonical NO toma SLUG. Auto-derives `wip/{brand}`. Si already exists → refuse + advise.

### CORE #2 — Sub-agent worktree BAN

**Modelo v1:** sub-agents read-only podían crear worktree (isolation: "worktree" frontmatter).

**Modelo v2:** TODOS los sub-agents (Architect, Auditor, Builder, Explore, etc.) trabajan in-place sobre `cwd` del caller. CERO worktree creation por sub-agents.

**Justificación user:** *"Auditor y architect debe poder hacer write en mi cwd, no hay problema, son los jefes, lo que no debemos hacer es crear worktrees en una misma sesión, los subagentes se spawnean y trabajan todos sobre el mismo código."*

**Diff `parallel-safety.md`:** nueva sección § "Sub-agent worktree ban":

```markdown
## Sub-agent worktree ban (cementado 2026-05-18 v2)

Sub-agents NUNCA crean worktree. Trabajan in-place sobre el cwd del caller.
- ❌ PROHIBIDO: `isolation: "worktree"` en frontmatter de cualquier sub-agent.
- ❌ PROHIBIDO: `git worktree add` desde código de sub-agent.
- ✅ PERMITIDO: caller (vos) crea worktree explícito via `scripts/git/new-session.sh`.

Justificación: caso vitalia 2026-05-18 — sub-agent Architect/Auditor creó
worktree fantasma `luana-vitalia-infra-cross-cutting` que nunca cleanup +
sin manifest. Resultado: rama huérfana con commits valiosos que casi se pierden.
```

**Arch fitness test NEW:** `scripts/test_no_subagent_worktree.sh` (MISSING — create before use) — grep `isolation:\s*['"]?worktree['"]?` en `.claude/agents/*.md` → fail si encuentra.

### CORE #3 — Sync KISS activo

**Modelo v1 (D10):** advisory pasivo cuando merge real o tree dirty.

**Modelo v2 (D10-v2):** acción graduada, garantiza estar al día siempre.

| Trigger | Estado worktree | Acción NUEVA | Acción VIEJA |
|---|---|---|---|
| INICIO sesión (`/pm-{brand}` o `/pm-luana` step 0) | tree clean + FF puro | auto-FF silencioso | igual |
| INICIO sesión | tree clean + merge real, sin conflict | **AUTO MERGE silencioso** + 1 línea | advisory only |
| INICIO sesión | tree clean + merge real CON conflict | **STOP + lista files + prompt para resolver** | advisory only |
| INICIO sesión | tree dirty + FF puro | auto-FF silencioso (no toca WIP) | advisory soft |
| INICIO sesión | tree dirty + merge real | **STOP + "commit/stash tu WIP, hago merge"** | advisory soft |
| **PRE-push** (hook) | rama behind main | **BLOQUEA + force integrate first** | advisory (no bloquea) |
| **PRE-merge-to-main** | nunca skip | **SIEMPRE `git fetch + git merge origin/main`** | no enforced |

**NEW script `scripts/git/sync-from-main.sh`:** wraps el flow correcto. Idempotente.

**Diff `push-wip.sh`:** chequeo behind main → si behind ≥1 commit + branch wip/* (no main, no release/*) → BLOCK push + ofrecer ejecutar `sync-from-main.sh`.

### CORE #4 — Scope per branch

**Modelo v1:** rama wip podía tocar cualquier path. Cross-brand mixing posible.

**Modelo v2:** scope estricto per branch pattern, enforced en pre-commit.

| Branch pattern | Scope permitido | Scope prohibido |
|---|---|---|
| `wip/{brand}` | `{brand}/**` + raíz brand-agnostic (CLAUDE.md, AGENTS.md, scripts triviales) | otra-brand/**, core/luana-core-*/**, .claude/{rules,skills}/** transversales |
| `wip/{brand}-{story-id}` | mismo que `wip/{brand}` | mismo |
| `wip/protocol-{slug}` | `docs/{process,architecture}/**`, `.claude/{rules,skills}/**`, `scripts/**` | brand/** |
| `wip/core-{slug}` | `core/luana-core-*/**` + tests | brand/**, .claude/** |

**Diff `pre-commit` Section 13 NEW:**

```bash
# ─────────────────────────────────────────────────────────────────
# Section 13 — Scope per branch enforcement (v2 cementado 2026-05-18)
# ─────────────────────────────────────────────────────────────────
# Bloquea staging de files que violan scope de la branch actual.
# Patterns: wip/{brand} = solo {brand}/** + raíz brand-agnostic
#           wip/protocol-* = solo docs/process/, .claude/, scripts/
#           wip/core-* = solo core/luana-core-*/
# Override: SCOPE_GATE_SKIP=1 (emergencias documentadas)

if [ "${SCOPE_GATE_SKIP:-0}" != "1" ]; then
  BRANCH=$(git branch --show-current 2>/dev/null || echo "")
  STAGED=$(git diff --cached --name-only 2>/dev/null)

  # Patrón wip/{brand} sin sufijo story-id → canónico estable
  if [[ "$BRANCH" =~ ^wip/(vitalia|nicolify|comunify|lupulo)$ ]]; then
    BRAND="${BASH_REMATCH[1]}"
    # Verificar cada file staged
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      # OK: brand propia
      [[ "$f" =~ ^${BRAND}/ ]] && continue
      # OK: raíz brand-agnostic
      [[ "$f" =~ ^(CLAUDE.md|AGENTS.md|README.md|Makefile|pnpm-lock.yaml|uv.lock)$ ]] && continue
      # OK: scripts triviales (no transversales-modelo)
      [[ "$f" =~ ^scripts/ ]] && [[ ! "$f" =~ ^scripts/git/ ]] && continue
      # BLOCK: cross-brand
      if [[ "$f" =~ ^(vitalia|nicolify|comunify|lupulo)/ ]]; then
        echo "::error::Cross-brand staging blocked: $f (branch=$BRANCH expects only ${BRAND}/)"
        exit 1
      fi
      # BLOCK: transversal modelo (debe ir en wip/protocol-*)
      if [[ "$f" =~ ^(\.claude/(rules|skills)|docs/(process|architecture)|scripts/git)/ ]]; then
        echo "::error::Transversal modelo staging blocked: $f (branch=$BRANCH; usa wip/protocol-{slug})"
        exit 1
      fi
      # BLOCK: core engine (debe ir en wip/core-*)
      if [[ "$f" =~ ^core/luana-core- ]]; then
        echo "::error::Core engine staging blocked: $f (branch=$BRANCH; usa wip/core-{slug} + promotion proposal)"
        exit 1
      fi
    done <<< "$STAGED"
  fi
fi
```

### CORE #5 — N sesiones paralelas mismo cwd (lock por bucket)

**Modelo v1:** 1 sesión por worktree. Para sesión docs paralela → crear worktree extra.

**Modelo v2 (D9-bis NEW):** N sesiones Claude/opencode pueden abrir terminales en mismo `~/Proyectos/luana-{brand}/`. Coordinación por **buckets de scope**:

| Bucket | Paths permitidos |
|---|---|
| `code` | `{brand}/{backend,frontend}/src/**` + `{brand}/{backend,frontend}/tests/**` (excepto `*/docs/*`) |
| `docs` | `{brand}/docs/**` + raíz docs/ |
| `tests` | `{brand}/{backend,frontend}/tests/**` solamente |

**Lock mechanism:** archivo `~/Proyectos/luana-{brand}/.session-locks/{bucket}.lock` con PID + skill + timestamp.

```bash
# NEW: scripts/git/session-lock.sh
acquire_lock() {
  BUCKET="$1"
  SKILL="$2"
  LOCK_DIR="${WORKTREE}/.session-locks"
  mkdir -p "$LOCK_DIR"
  LOCK_FILE="$LOCK_DIR/${BUCKET}.lock"
  if [[ -f "$LOCK_FILE" ]]; then
    OWNER=$(cat "$LOCK_FILE" | head -1)
    OWNER_PID=$(echo "$OWNER" | awk '{print $1}')
    # Si PID ya no corre → liberar lock (auto-cleanup)
    if ! kill -0 "$OWNER_PID" 2>/dev/null; then
      rm "$LOCK_FILE"
    else
      echo "Bucket $BUCKET locked by PID $OWNER"
      return 1
    fi
  fi
  echo "$$ $SKILL $(date -Iseconds)" > "$LOCK_FILE"
}
```

**Skill consumer (`/pm-{brand}` step 0):**
- Detecta cwd → identifica brand
- Infiere bucket por scope de trabajo intencionado (preguntá al user si ambiguo)
- Intenta `acquire_lock $BUCKET $SKILL_NAME`
- Si OK → proceed
- Si bloqueado → ofrecer (a) esperar, (b) abrir worktree story explícito, (c) kick lock si PID crashed

## Implementación a hacer en este worktree (priority order)

| # | Archivo | Action |
|---|---|---|
| A | `docs/process/parallel-sessions-protocol.md` | Editar D2/D3/D4/D9 → D9-bis + D10-v2 |
| B | `.claude/rules/parallel-safety.md` | NEW § Sub-agent worktree ban + § Scope per branch + § N sesiones mismo cwd |
| C | `scripts/git/new-session.sh` | TYPE=canonical sin SLUG + TYPE=story requiere flag explícito |
| D | `scripts/git-hooks/pre-commit` | NEW Section 13 (scope per branch) |
| E | `scripts/git/sync-from-main.sh` | NEW script (sync KISS) |
| F | `scripts/git/push-wip.sh` | BLOCK push si behind main |
| G | `.claude/rules/step-0-worktree.md` | Auto-fix manifest desync + sync activo + lock bucket integration |
| H | `docs/architecture/luana-platform/ADR-005-worktree-policy.md` | Addendum v2 |
| I | `.claude/skills/worktree-protocol/SKILL.md` | Update para reflejar v2 |
| J | `.claude/skills/pm-luana/SKILL.md` | Step 0 actualizado con sync + lock |

## Estado worktrees POST-v2 (target)

```
~/Proyectos/luana-platform/          main          (al día con v2 cementado)
~/Proyectos/luana-vitalia/           wip/vitalia   (estable, sync activo)
~/Proyectos/luana-nicolify/          wip/nicolify  (estable, sync activo)
~/Proyectos/luana-comunify/          wip/comunify  (estable, sync activo)
~/Proyectos/luana-lupulo/            wip/lupulo    (estable cuando se cree, no urgente)
```

Branches obsoletas eliminadas: wip/vitalia-bootstrap, wip/vitalia-slice-1-shipping, wip/vitalia-infra-cross-cutting, wip/nicolify-bootstrap, wip/comunify-bootstrap.

Worktree efímero `luana-protocol-v2` cleanup al final.

## What you (Chris) get out of this

1. Abrís cualquier sesión → step 0 te dice estado real + sync automático si seguro
2. Trabajás en `~/Proyectos/luana-{brand}/` siempre (no pensás en branches)
3. Para sesión docs paralela: abrís otra ventana terminal en mismo cwd. Lock bucket protege scope
4. Cuando hay overload: pedís worktree story explícito (`scripts/git/new-session.sh {brand} story {story-id}`)
5. Pre-commit te avisa si mezclás brands o scope equivocado
6. Push bloqueado si tu rama está vieja → integrate first (KISS)
7. Sub-agents NUNCA crean worktree fantasma
8. Cero "trabajar sobre código antiguo y desactualizar otra sesión"
