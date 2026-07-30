---
description: "Consulta + troubleshoot + modificación del modelo multi-sesión worktree-based Luana (D1-D14 + ADR-005). Pointer-first. Activá cuando: algo del flow no funciona, no entendés una regla, querés modificar comportamiento del sync/merge/step-0, querés ver cheatsheet rápido, querés explicar a alguien el modelo. Triggers: 'worktree', 'sesión paralela', 'multi-brand workflow', 'step 0', 'sync canónicos', 'lift core', 'merge policy', 'no funciona el sync', 'mainframe del worktree', 'modificar regla worktree', 'cómo cambio el step 0', 'qué hace check-sync', 'qué hace push-wip', 'manifest .session.yaml', 'parallel-safety', 'D10/D11/D12/D13/D14', 'ADR-005', 'cleanup-session', 'new-session', 'status-all', 'regenerate-manifest', 'Warp Workflows luana'."
---

<!-- voseo-allowed: internal skill documentation for Chris, not user-facing -->

# Worktree Protocol — punto único de consulta + troubleshoot + modificación

> **★ v2 cementado 2026-05-18 PM:** modelo actualizado con 5 CORE changes + 7 refinements. Ver `docs/process/worktree-protocol-v2-plan.md` para SSoT del rediseño. Cambios principales: canónico estable `wip/{brand}` (no rota), sync KISS activo, sub-agent worktree ban, scope per branch, N sesiones mismo cwd con lock buckets.
>
> Skill consultable de todo el modelo multi-sesión worktree-based de Luana.
> Vivo, no estático: cuando algo no funciona o querés cambiar una regla, **arrancá aquí**.
>
> **Modo conversacional:** preguntá específicamente qué necesitás (troubleshoot / explicar / modificar / cheatsheet). Skill carga el contexto mínimo relevante on-demand.

## v2 cheatsheet (lo nuevo)

| Caso | Comando |
|---|---|
| Sync mi wip con main | `scripts/git/sync-from-main.sh` |
| Solo chequear sync (no integrar) | `scripts/git/sync-from-main.sh --check` |
| Acquire bucket lock (sesión paralela mismo cwd) | `scripts/git/session-lock.sh acquire {code\|docs\|tests} {skill-name}` |
| Release bucket lock | `scripts/git/session-lock.sh release {bucket}` |
| Ver buckets ocupados | `scripts/git/session-lock.sh status` |
| Kick lock (PID crashed) | `scripts/git/session-lock.sh kick {bucket}` |
| Crear worktree story EXPLÍCITO (v2 requiere flag) | `EXPLICIT_USER_REQUEST=1 scripts/git/new-session.sh {brand} story {story-id}` |
| Push bloqueado por behind main | `scripts/git/sync-from-main.sh` primero, luego `scripts/git/push-wip.sh` |

## SSoTs del modelo (jerarquía cementada)

| Capa | Archivo | Cuándo modificar |
|---|---|---|
| **Decisión arquitectónica** | `docs/architecture/luana-platform/ADR-005-worktree-policy.md` | Cambio fundamental (e.g., revocar worktrees nuevamente, cambiar triple-branch) |
| **Diseño + decisiones D1-D14** | `docs/process/parallel-sessions-protocol.md` | Refinar comportamiento dentro del modelo (e.g., cambiar umbral FF, agregar excepción) |
| **Runtime rule** | `.claude/rules/parallel-safety.md` | Reflejar cambio del diseño en regla que Claude/skills cargan |
| **Step 0 SSoT** | `.claude/rules/step-0-worktree.md` | Cambiar enforcement matrix o lógica detection |
| **Scripts portables** | `scripts/git/*.sh` (×6) | Implementación de lógica (sync, push, new/cleanup, regenerate, status, ps1) |
| **Manual operativo** | `docs/process/warp-multibrand-handbook.md` | Reflejar cambio de flow día a día en Warp |
| **Hooks Claude (sample)** | `.claude/hooks-settings.sample.json` | Cambiar trigger hooks SessionStart/PreToolUse |
| **Warp Workflows** | `scripts/warp-workflows/*.yaml` | Cambiar atajos palette Warp |

**Regla de propagación al modificar:** cualquier cambio relevante debe sincronizarse en TODAS las capas afectadas (decisión → diseño → runtime → scripts → handbook). Skill puede ayudarte a hacer este sweep.

## Quick map del modelo

```
Multi-sesión worktree-based (D1-D14)
├── D1  Modelo conceptual: 1 repo / N worktrees / 1 branch por worktree
├── D2  Topología: PRINCIPAL + CANÓNICO long-lived + EFÍMERO brand + EFÍMERO core
├── D3  Naming convention (tabla canonical/story/multi-lane/hotfix/exp/core)
├── D4  Política: TODO a main, NADA wip→wip
├── D5  Recursos compartidos: venv symlink, max 1 docker stack por brand, alembic secuencial
├── D6  Reglas heredadas M1-M11 vigentes
├── D7  Visibilidad: PS1 + dashboard status-all.sh + .session.yaml + Warp Tabs/Workflows
├── D8  Detección automática: path regex + manifest
├── D9  Multi-lane: excepcional, max 3 lanes/story, mergean independientes
├── D10 Sincronización canónicos: T1 SessionStart + T2 step-0 + T-push (mec. A/E/L)
├── D11 Política merge: 1 squash/story + checkpoint opcional + excepciones (hotfix/exp/multi-lane/core)
├── D12 Cambios al core: efímero dedicado `luana-core-{slug}` + cross-worktree dependency
├── D13 Step 0 enforcement skills: SSoT step-0-worktree.md + HARD refuse brand mismatch
└── D14 opencode parity: 3 capas (scripts portable + Claude hooks + Warp Workflows)
```

```
Mecanismos (A-N)
├── A SessionStart hook Claude (T1 sync auto)        → ~/.claude/settings.json + check-sync.sh
├── B new-session.sh (crear worktree)                → scripts/git/new-session.sh
├── C cleanup-session.sh (cerrar worktree)           → scripts/git/cleanup-session.sh
├── D pre-commit checks extras (main-block)          → scripts/git-hooks/pre-commit § 11
├── E /pm-{brand} step 0 obligatorio                 → .claude/rules/step-0-worktree.md
├── F make dev-{brand} wrapper con lock              → scripts/dev-lock-check.sh + Makefile
├── G alembic wrapper con lock                        → stub (TODO cuando aparezca primer caso)
├── H status-all.sh dashboard                         → scripts/git/status-all.sh
├── I PS1 bash customizado                            → scripts/git/ps1-luana.sh
├── J .session.yaml manifest (auto-gen por B)        → covered by new-session.sh
├── K Warp Workflows                                  → scripts/warp-workflows/
├── L push-wip.sh (T-push sync check)                → scripts/git/push-wip.sh + PreToolUse hook
├── M regenerate-manifest.sh                          → scripts/git/regenerate-manifest.sh
└── N step-0-worktree.md SSoT                        → .claude/rules/step-0-worktree.md
```

## Modos de consulta

### Modo 1 — Troubleshoot ("no funciona X")

Decime el síntoma. Skill diagnostica + apunta al fix.

| Síntoma | Probable causa | Skill carga + acción |
|---|---|---|
| "step 0 STOP — brand mismatch" | Skill `/pm-X` invocado desde worktree brand Y | Apunta a §4.1 handbook. Cambiar tab. |
| "manifest absent" | Worktree creado a mano sin `new-session.sh` | Apunta a `regenerate-manifest.sh`. §4.2 handbook. |
| "push rejected non-fast-forward" | Otra sesión adelantó remote | Apunta a regla M5 + §4.3 handbook. Fetch + merge, NUNCA pull. |
| "CORE CHANGED banner permanente" | Tree dirty + main mergeó core changes | §4.4 handbook. Push WIP → fetch + merge → resolver conflicts. |
| "dev-lock-check warning" | Otra sesión corre `make dev-{brand}` para la misma brand | §4.5 handbook + D5. |
| "claude no arranca por hooks" | `~/.claude/settings.json` hooks broken | §4.7 handbook. Backup + remover hooks bloque. |
| "auto-FF no se aplica aunque clean" | Probable: ahead > 0 (merge real, no FF puro) | D10 acción graduada. Verificar `git rev-list --count origin/main..HEAD`. |
| "lift core no consume desde brand X" | Cross-worktree dependency caso B (deps changed) | D12. Correr `uv sync` o `pnpm install` según hint. |

### Modo 2 — Explicar ("cómo / qué hace / por qué X")

Decime qué te confunde. Skill drillea SSoT relevante.

Preguntas típicas + dónde vive la respuesta:
- "¿Cuándo se hace squash-merge a main?" → D11 (`parallel-sessions-protocol.md`)
- "¿Por qué efímeros no tienen T1 SessionStart?" → D10 (efímeros nacen frescos, vida corta)
- "¿Qué pasa si brand B necesita feature en lift core in-flight?" → D12 caso A
- "¿Por qué multi-lane mergea independiente?" → D9 + D11 (lanes son peers)
- "¿Qué archivos toca el step 0?" → `.claude/rules/step-0-worktree.md` § Logic
- "¿Cómo se detecta 'toca core'?" → D10 (regex `^core/luana-core-[^/]+/src/`)
- "¿Por qué hotfix bypass auditor?" → D11 excepción + `.claude/rules/hotfix-repro-mandatory.md`

### Modo 3 — Modificar ("quiero cambiar X regla / comportamiento")

Decime QUÉ querés cambiar. Skill identifica TODAS las capas que hay que tocar + propone diff.

Ejemplo flow:
```
Chris: "quiero que T1 auto-FF aplique también en EFÍMERO brand, no solo CANÓNICO"

Skill:
  Capas afectadas:
  1. D10 tabla acción graduada → cambiar fila EFÍMERO_BRAND
  2. .claude/rules/parallel-safety.md § Sincronización → mismo cambio
  3. .claude/rules/step-0-worktree.md § Logic step 7 → adjust condition
  4. scripts/git/check-sync.sh → ramificación EPHEMERAL_BRAND
  5. docs/process/warp-multibrand-handbook.md → §2.2 ejemplo update (opcional)

  Tradeoffs a considerar:
  - Pro: efímeros se mantienen más al día con main
  - Con: si efímero está a 5h de cerrarse, FF agrega ruido + posibles conflicts
  - Alternativa: solo FF cuando efímero >3 días viejo

  ¿Confirmás cambio + tradeoff? Si sí, procedo capa por capa.
```

### Modo 4 — Cheatsheet rápido

```bash
# Crear worktree
scripts/git/new-session.sh BRAND TYPE SLUG [LANE]

# Ver dashboard
scripts/git/status-all.sh

# Sync manual
scripts/git/check-sync.sh

# Push con advisory
scripts/git/push-wip.sh [BRANCH]

# Cerrar worktree
scripts/git/cleanup-session.sh BRAND-SLUG [--delete-branch]

# Recovery manifest
scripts/git/regenerate-manifest.sh
```

### Modo 5 — Onboarding (alguien nuevo / tú mismo en 6 meses)

Orden de lectura recomendado:
1. `docs/process/warp-multibrand-handbook.md` (manual operativo Warp)
2. `docs/process/parallel-sessions-protocol.md` (modelo completo D1-D14)
3. `docs/architecture/luana-platform/ADR-005-worktree-policy.md` (decisión)
4. `.claude/rules/parallel-safety.md` (runtime rule)

## Reglas de propagación al modificar

Cuando cambies algo del modelo, **siempre sincronizá las capas afectadas**. El skill puede ayudarte a hacer el sweep:

```
1. ADR-005 (si cambio fundamental) → escribir addendum, no editar versión accepted
2. parallel-sessions-protocol.md (si cambio diseño D1-D14) → editar in-place + bump revision frontmatter
3. parallel-safety.md (si cambia comportamiento runtime) → sincronizar
4. step-0-worktree.md (si cambia enforcement matrix o detection logic)
5. scripts/git/*.sh (si cambia implementación)
6. warp-multibrand-handbook.md (si cambia flow día a día)
7. Este SKILL.md (si cambia mapa mental)
8. CLAUDE.md/AGENTS.md (si cambia trigger principal o invocación)
```

NO dejar capas desalineadas. Skill chequea al cierre de cualquier cambio.

## Anti-patterns

- ❌ Editar `parallel-safety.md` sin actualizar `parallel-sessions-protocol.md` → runtime rule drift del modelo
- ❌ Cambiar `check-sync.sh` sin actualizar D10 + handbook → script hace algo distinto al doc
- ❌ Agregar mecanismo nuevo (O, P, ...) sin tabla mecanismos updated en `parallel-sessions-protocol.md`
- ❌ Modificar enforcement matrix step 0 sin actualizar tabla D13 + step-0-worktree.md
- ❌ Cambiar política merge sin reflejar en D11 + handbook
- ❌ Bootstrap brand nueva sin actualizar `new-session.sh` KNOWN_BRANDS + status-all.sh + step-0-worktree.md brand list + portfolio

## Cómo querés que te ayude hoy?

Decime:
1. **Algo no funciona** → describime síntoma → modo troubleshoot
2. **No entiendo X** → preguntame → modo explicar
3. **Quiero cambiar X** → describime el cambio → modo modificar (propago en todas las capas)
4. **Cheatsheet** → ya lo tenés arriba § Modo 4
5. **Onboarding alguien nuevo** → seguir orden de lectura § Modo 5

## Referencias rápidas

- ADR-005 (decisión arquitectónica): `docs/architecture/luana-platform/ADR-005-worktree-policy.md`
- Diseño D1-D14: `docs/process/parallel-sessions-protocol.md`
- Runtime rule: `.claude/rules/parallel-safety.md`
- Step 0 SSoT: `.claude/rules/step-0-worktree.md`
- Manual Warp: `docs/process/warp-multibrand-handbook.md`
- Scripts: `scripts/git/{new-session,cleanup-session,check-sync,push-wip,status-all,regenerate-manifest,ps1-luana}.sh`
- Hooks sample: `.claude/hooks-settings.sample.json`
- Warp Workflows: `scripts/warp-workflows/`
- Dev lock: `scripts/dev-lock-check.sh` + Makefile § dev-* targets
- Pre-commit § 11: `scripts/git-hooks/pre-commit`
