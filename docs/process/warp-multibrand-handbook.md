<!-- voseo-allowed: internal Warp workflow manual for Chris, not user-facing -->

# Warp Multibrand Handbook

> Manual operativo Warp para day-to-day multi-brand multi-session.
> SSoT del modelo: `docs/process/parallel-sessions-protocol.md` (D1-D14) + ADR-005.
> Audiencia: Chris (workflow Warp Terminal + Claude Code + opencode).

> ⚠️ **ADR-009 SINGLE-HUB (2026-05-28):** El default cambió. Cada brand tiene UN worktree canónico (`~/Proyectos/luana-{brand}/`) sobre el que corren N sesiones paralelas coordinadas por bucket locks M14. Los worktrees efímeros multi-lane (§3.4) son la **excepción** (lift core, hotfix aislado, spike), no la norma diaria. Para sincronizar con main, usar EXCLUSIVAMENTE `bash scripts/git/sync-from-main.sh` — `git pull`, `git fetch && merge` están **PROHIBIDOS**. Ver `docs/architecture/luana-platform/ADR-009-single-hub-worktree.md` + `.claude/rules/parallel-safety.md`.

## 0. Topología visual

```
~/Proyectos/
  luana-platform/                  ← PRINCIPAL (main, no editar código brand)
                                     ↓ Warp tab: "luana-main"
  luana-vitalia/                   ← CANÓNICO Vitalia — hub único (N sesiones, ADR-009)
                                     ↓ Warp tab: "luana-vitalia"
  luana-nicolify/                  ← CANÓNICO Nicolify
                                     ↓ Warp tab: "luana-nicolify"
  luana-comunify/                  ← CANÓNICO Comunify
                                     ↓ Warp tab: "luana-comunify"
  luana-vitalia-copilot-tools-be/  ← EFÍMERO Vitalia multi-lane (story X, lane BE)
                                     ↓ Warp tab: "luana-vitalia-X-be"
  luana-vitalia-copilot-tools-fe/  ← EFÍMERO Vitalia multi-lane (story X, lane FE)
                                     ↓ Warp tab: "luana-vitalia-X-fe"
  luana-comunify-hotfix-kb-bug/    ← EFÍMERO Comunify hotfix
                                     ↓ Warp tab: "luana-comunify-hotfix"
  luana-core-extract-handler/      ← EFÍMERO lift core (D12)
                                     ↓ Warp tab: "luana-core-lift"
```

Cada tab Warp tiene su propio `cwd` + branch + sesión Claude/opencode.

## 1. Setup inicial (one-time)

### 1.1 PS1 bashrc (mec. I)

Agregar al `~/.bashrc`:

```bash
if [[ -f ~/Proyectos/luana-platform/scripts/git/ps1-luana.sh ]]; then
  source ~/Proyectos/luana-platform/scripts/git/ps1-luana.sh
fi
```

Resultado: cada terminal abierta dentro de `luana-*/` muestra prompt:
```
[luana-vitalia wip/vitalia-copilot-tools-impl ✓]$
```

Marker `✗` = dirty tree, `✓` = clean.

### 1.2 Hooks Claude Code (mec. A + L)

Merge contenido de `.claude/hooks-settings.sample.json` (en este repo) a tu `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{"matcher": ".*", "hooks": [
      {"type": "command", "command": "bash $CLAUDE_PROJECT_DIR/scripts/git/check-sync.sh 2>/dev/null || true"}
    ]}],
    "PreToolUse": [{"matcher": "Bash", "hooks": [
      {"type": "command", "command": "[[ \"$CLAUDE_TOOL_INPUT\" =~ git\\ push\\ origin\\ (wip|hotfix|exp)/ ]] && bash $CLAUDE_PROJECT_DIR/scripts/git/push-wip.sh --check-only 2>/dev/null; true"}
    ]}]
  }
}
```

Resultado:
- Cada vez que `claude` arranca → check-sync corre auto (T1 logic)
- Cada vez que Claude intenta `git push origin wip/*` → advisory pre-push

### 1.3 Warp Workflows (mec. K)

Importar los 6 workflows desde `scripts/warp-workflows/`:

```
Warp → Cmd+Shift+R → Workflows → Import each .yaml
```

Resultado: comandos `sync-check`, `push-wip`, `new-session`, `cleanup-session`, `status-all`, `regenerate-manifest` quedan disponibles en la palette (Cmd+P).

### 1.4 Warp Tab naming

Warp puede auto-nombrar tabs basándose en `cwd`. Settings → Appearance → Tab naming → "Current working directory" (basename).

Resultado: tab abierto en `~/Proyectos/luana-vitalia/` se llama "luana-vitalia" automáticamente.

### 1.5 Pre-commit hooks

```bash
cd ~/Proyectos/luana-platform/
make install-hooks
```

Instala `scripts/git-hooks/pre-commit` (incluye Section 11 — main-direct-commit block per ADR-005).

## 2. Workflow día a día

### 2.1 Mañana: abrir el día

```bash
cd ~/Proyectos/luana-platform/   # principal
bash scripts/git/status-all.sh   # ver qué quedó vivo de ayer
```

`status-all.sh` muestra:
```
WORKTREE                          BRANCH                          STATUS      LAST COMMIT     STORY              DOCKER
luana-platform                    main                            clean       af8dfc3 5h      —                  —
luana-vitalia                     wip/vitalia-copilot-tools       3 modif     b1c2d3e 7h      copilot-tools-impl vitalia ✓
luana-comunify                    wip/comunify-design-cement      clean       e5f6789 35m     design-cement      —
```

Decisión: ¿retomar Vitalia (3 modif → push pendiente) o arrancar nueva story?

### 2.2 Retomar canónico Vitalia

```bash
cd ~/Proyectos/luana-vitalia/    # canónico
claude                            # SessionStart hook corre T1 auto
```

T1 output (típico):
```
[step 0 worktree]
  path:     ~/Proyectos/luana-vitalia
  branch:   wip/vitalia-copilot-tools-impl
  type:     CANONICAL vitalia
  manifest: brand=vitalia story=copilot-tools-impl lane=—
  sync:     ✓ 0 commits behind origin/main
[step 0 OK]
```

Si `sync:` muestra ↑ N commits behind con CORE label → sincronizar antes de seguir:

```bash
# Si tree clean + FF puro → ya lo hizo auto. Si advisory:
bash scripts/git/sync-from-main.sh
```

### 2.3 Arrancar nueva story (canónico ya existe)

```bash
cd ~/Proyectos/luana-vitalia/
# Si vieja story está done + mergeada a main, cerrá branch vieja:
bash scripts/git/cleanup-session.sh vitalia-copilot-tools-impl --delete-branch
# Crear nueva:
git checkout -b wip/vitalia-new-story-slug origin/main
# Actualizar manifest:
bash scripts/git/regenerate-manifest.sh
```

### 2.4 Arrancar nueva story (efímero)

```bash
cd ~/Proyectos/luana-platform/   # desde principal
bash scripts/git/new-session.sh vitalia story landing-redesign
# o con lane:
bash scripts/git/new-session.sh vitalia story landing-redesign be
# o desde Warp Workflow:
# Cmd+P → new-session → vitalia / story / landing-redesign / be

# Cambiar a la nueva tab Warp
cd ~/Proyectos/luana-vitalia-landing-redesign-be/
claude
```

### 2.5 Trabajar (durante el día)

- Edit / test / iterate
- **M11: push cada ≤30 min** si hay cambios significativos. Use `push-wip` workflow o:

```bash
bash scripts/git/push-wip.sh
```

T-push hook (Claude) o script (manual) imprime advisory si origin/main adelantó:
```
⚠ origin/main adelantó 3 commits desde tu HEAD
  ⚠ 1 archivos en core/luana-core-*/src/ cambiaron
  Recomendado antes de push: bash scripts/git/sync-from-main.sh
```

NO bloquea push. Decidís acción.

### 2.6 Cerrar story (state=done)

`/pm-{brand}` ejecuta squash-merge cuando `/auditor` APPROVED:

```bash
# Dentro del worktree wip/vitalia-X
/pm-vitalia "story X done, merge a main"
# /pm-vitalia ejecuta squash-merge a main + push + cleanup
```

O manual:

```bash
cd ~/Proyectos/luana-platform/
bash scripts/git/sync-from-main.sh   # sincroniza con main (FF puro o advisory)
git merge --squash wip/vitalia-X
git commit -m "feat(vitalia): X shipped — short summary"
git push origin main
bash scripts/git/cleanup-session.sh vitalia-X --delete-branch
```

### 2.7 Cerrar sesión efímera (sin merge — solo pausa)

```bash
cd ~/Proyectos/luana-{slug}/
# stage + commit + push
git add <files>
git commit -m "wip(brand): paused — short note"
bash scripts/git/push-wip.sh
# (worktree puede quedar para volver mañana, o cleanup si terminás)
```

## 3. Casos especiales

### 3.1 Hotfix urgente

```bash
bash scripts/git/new-session.sh vitalia hotfix payment-broken
cd ~/Proyectos/luana-vitalia-hotfix-payment-broken/
claude

# Trabajar fix
# IMPORTANTE: agregar test regression que falla RED antes del fix, GREEN después
# Citar repro_verified en .session.yaml.notes

# Squash-merge bypass auditor formal (D11):
cd ~/Proyectos/luana-platform/
bash scripts/git/sync-from-main.sh   # sincroniza antes de squash
git merge --squash hotfix/vitalia-payment-broken
git commit -m "fix(vitalia): payment broken — repro verified in .session.yaml"
git push origin main
bash scripts/git/cleanup-session.sh vitalia-hotfix-payment-broken --delete-branch
```

### 3.2 Experimento / spike (NUNCA mergea)

```bash
bash scripts/git/new-session.sh vitalia exp voice-cloning-spike
cd ~/Proyectos/luana-vitalia-exp-voice-cloning-spike/
claude

# Spike work, learnings...
# Al cerrar: extract learnings to {brand}/docs/learnings/{date}-{slug}.md
# Después: cleanup (NO se mergea a main):
bash scripts/git/cleanup-session.sh vitalia-exp-voice-cloning-spike --delete-branch
```

### 3.3 Lift core (D12)

```bash
# /pm-luana ratifica proposal accepted → imprime comando:
bash scripts/git/new-session.sh core lift extract-callback-handler
cd ~/Proyectos/luana-core-extract-callback-handler/
claude
# (claude tiene contexto del lift via 03-arch.md de la promotion proposal)

# /dev-team ejecuta lift (move código brand B → core, refactor brand B imports, tests, bump version)
# Squash-merge a main (auditor APPROVED + R3 downstream regression GREEN)
cd ~/Proyectos/luana-platform/
git merge --squash wip/core-extract-callback-handler
git commit -m "feat(core): extract-callback-handler shipped from vitalia"
git push origin main
bash scripts/git/cleanup-session.sh core-extract-callback-handler --delete-branch

# Otros canónicos brand: T1 detecta ↑ N commits CORE en próxima invocación claude
```

### 3.4 Multi-lane (misma story, lanes simultáneas)

> **ADR-009 EXCEPCIÓN:** El patrón de worktrees separados por lane es la **excepción**, no el default. Para builds paralelos dentro de la misma marca, el default es el hub único con bucket locks M14 (`code:{module}`). Crear worktrees multi-lane solo cuando los módulos comparten estado de filesystem que lo justifique (ej. lift core simultáneo BE+FE en brands distintas). Ver `.claude/rules/worktree-dual-strategy.md`.

```bash
# Lane BE (excepción — solo si hub único no aplica):
bash scripts/git/new-session.sh vitalia story copilot-tools be
# → ~/Proyectos/luana-vitalia-copilot-tools-be/ on wip/vitalia-copilot-tools-be

# Lane FE (otra Warp tab):
bash scripts/git/new-session.sh vitalia story copilot-tools fe
# → ~/Proyectos/luana-vitalia-copilot-tools-fe/ on wip/vitalia-copilot-tools-fe

# Cada lane mergea independiente (D11 — lanes son peers).
```

### 3.5 Multi-brand paralelo (típico día Chris)

Warp con 3 tabs simultáneas:
- Tab "luana-vitalia": `cd ~/Proyectos/luana-vitalia/ && claude`
- Tab "luana-comunify": `cd ~/Proyectos/luana-comunify/ && claude`
- Tab "luana-main": `cd ~/Proyectos/luana-platform/` (no claude — solo merges + status)

Constraint D5: max 1 stack `make dev-{brand}` por brand. Pero `make dev-vitalia` + `make dev-comunify` simultáneo está OK (brands distintas, ports distintos: 8001/8002/8003/8004).

## 4. Troubleshooting

### 4.1 `step 0 STOP — brand mismatch`

Causa: invocaste `/pm-vitalia` desde worktree comunify.

Fix:
1. Cambiar a Warp tab donde corre `~/Proyectos/luana-vitalia/`
2. O usar `/pm-luana` (cross-brand visibility)

### 4.2 `manifest: ABSENT`

Causa: worktree creado a mano sin `new-session.sh` o manifest fue borrado.

Fix:
```bash
cd <worktree>
bash scripts/git/regenerate-manifest.sh
# o desde Warp: Cmd+P → regenerate-manifest
```

### 4.3 `push rejected (non-fast-forward)`

Causa: alguien (vos en otra sesión / colaborador / squash-merge a main) pusheó a remote y tu branch quedó behind.

Fix:
```bash
# Regla M5: NUNCA git pull / git fetch + merge manual
bash scripts/git/sync-from-main.sh   # FF puro o advisory con conflict detection
# Resolver conflictos si los hay, luego:
git push origin wip/<branch>
```

### 4.4 `CORE CHANGED while you worked` banner

Causa: tree dirty + origin/main mergeó cambios al `core/luana-core-*/`.

Fix:
1. Terminar WIP actual (commit + push lo que tengas)
2. `bash scripts/git/sync-from-main.sh`
3. Resolver conflicts si hay (probable si tu WIP toca mismos archivos)
4. Continuar

### 4.5 `dev-lock-check: containers luana-{brand}-* already running`

Causa: otra sesión está corriendo `make dev-{brand}` para la misma brand.

Fix:
1. Identificar la otra sesión (status-all.sh ayuda)
2. `make dev-down-{brand}` en la otra sesión
3. Re-correr `make dev-{brand}` aquí

### 4.6 Worktree quedó huérfano (sin claude/opencode session)

```bash
bash scripts/git/status-all.sh   # ver qué worktrees existen
# Si querés cerrarlo:
bash scripts/git/cleanup-session.sh <BRAND-SLUG>
# Si la branch ya mergeó a main, agregar --delete-branch
```

### 4.7 No me arranca claude por hooks broken

Si tu `~/.claude/settings.json` tiene hooks que rompen:
```bash
# Backup + remover hooks temporal
cp ~/.claude/settings.json ~/.claude/settings.json.bak
# editar y quitar el bloque "hooks": {...}
# probar claude
# si funciona, debuggear el hook + re-agregar
```

## 5. Cheatsheet

| Comando | Para qué |
|---|---|
| `bash scripts/git/status-all.sh` | Ver todos los worktrees + estado |
| `bash scripts/git/new-session.sh BRAND TYPE SLUG [LANE]` | Crear worktree nuevo |
| `bash scripts/git/cleanup-session.sh BRAND-SLUG [--delete-branch]` | Cerrar worktree |
| `bash scripts/git/push-wip.sh [BRANCH]` | Push wip con advisory |
| `bash scripts/git/check-sync.sh` | Manual T1 sync check |
| `bash scripts/git/regenerate-manifest.sh` | Regenerar manifest huérfano |
| `make dev-{brand}` | Levantar stack docker (con lock check) |
| `make dev-down-{brand}` | Bajar stack docker |
| `make dev-all` | Levantar todas las brands |
| `/pm-{brand}` (desde worktree brand) | PM brand-specific (step 0 enforce) |
| `/pm-luana` o `/pm` | PM cross-brand / core |

## 6. Referencias

- `docs/process/parallel-sessions-protocol.md` — SSoT D1-D14
- `docs/architecture/luana-platform/ADR-005-worktree-policy.md` — decisión arquitectónica
- `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` — triple-branch base
- `.claude/rules/parallel-safety.md` — runtime rules sincronizadas
- `.claude/rules/step-0-worktree.md` — step 0 SSoT
- `.claude/rules/git-safety.md` — triple-branch operacional
- `.claude/rules/git-haiku-delegation.md` — commit+push pattern
- `scripts/git/*.sh` — scripts portables
- `scripts/warp-workflows/` — workflows yaml para Warp
