# Git Haiku Delegation — operational detail (moved from .claude/rules/ 2026-05-30)

**Origen:** 2026-05-09 — análisis report.html. `git status/add/commit/push` = ~10709 Bash tool uses (top tool). Operación mecánica + repetitiva = waste de Opus 4.8.

## Regla cardinal

Cuando orchestrator (Opus 4.8) llega a fase commit+push, MUST delegar la ejecución a un sub-agent Haiku 4.5 via Agent tool. Opus prepara el plan (qué archivos, qué mensaje, qué guardrails); Haiku ejecuta el git workflow.

**Exception:** delegación NO aplica si:

- Single-file `Edit` tool ya ejecutado y user pide commit conversacional rápido sin push (Bash directo OK, < 200 tokens)
- Non-tracked filesystem ops (mv, cp, rm) — Haiku worker no resuelve esos casos sin contexto
- Conflict resolution / merge / rebase manual — orchestrator decide caso a caso

Default: cualquier "commitea + sube" / "commit y push" / multi-file commit → delegate Haiku.

## Cost saving estimado

| Operación | Opus tokens (antes) | Haiku tokens (ahora) | Saving |
|---|---|---|---|
| Stage 6 files + commit + push | ~3-5k | ~1-2k | ~70% |
| Mensaje commit con HEREDOC | parte de Opus context | dedicated Haiku context | sin overhead Opus |
| Status verify post-push | ~500 | bundled en Haiku | inline |

162 sessions × ~2 commits avg × ~3k saving = **~1M tokens/15d**. Real cumulative más alto.

## Guardrails obligatorios (Haiku worker prompt)

Todo Agent spawn que ejecute git workflow MUST contener estos guardrails verbatim en prompt:

```text
## Critical safety rules
- ⛔ NEVER edit file CONTENT. Tu trabajo ENTERO es `git commit <pathspec>` (stage + commit). NUNCA tocar el contenido de un archivo — ni un campo de checkpoint/cap YAML, ni código, ni un valor "para que pase un gate". Si un hook BLOQUEA el commit → STOP + reportá el mensaje del hook VERBATIM al orchestrator. NO "arregles" nada. (Caso HB-76: un worker flipeó `cap_change_type: new→fix` para esquivar el gate 5b → corrupción silenciosa de SSoT que SATISFIZO el gate con dato errado. El gate tenía razón; el dato no.)
- NEVER `git add .` / `git add -A` / `git add -u` — parallel sessions WIP en tree
- Stage ONLY by exact filename (lista provista)
- HUB único (N sesiones mismo árbol · ADR-009): el índice git es COMPARTIDO entre sesiones (= yo en N terminales) → **commit por pathspec** `git commit --only <file1> <file2> -m ...` (commitea SOLO esos paths, ignora lo demás del índice). NO `git add` + `git commit` suelto. **★ Trap real (caso 0072388f, 2026-05-29):** `git mv` AUTO-stagea el rename en el índice compartido → un `git commit` pelado en otra sesión lo barre. Helper que lo blinda: `scripts/git/commit-paths.sh "<msg>" <paths...>` (usa `--only`, rechaza `.`/`-A`/sin paths). Si por algo usás `git add`, primero `git reset` para limpiar el índice ajeno.
- NEVER `git commit --no-verify` — pre-commit hook mandatory
- NEVER `git pull` / `git fetch && merge` — banned per git-safety.md
- NEVER `git push --force` / `--force-with-lease` — banned
- NEVER `git revert` sin aprobación explícita — banned
- Si push fails non-fast-forward → STOP, report. NO pull.
- Si pre-commit hook fails → fix issue, create NEW commit (never `--amend` for pushed commits)

## Destination branch (triple-branch policy — ver git-safety.md)
Orchestrator indica destino. Guardrails por destino:
  wip/*      → push OK siempre que sea el branch de trabajo actual. No force.
  main       → squash-merge previo requerido. Si non-fast-forward → STOP.
  release/*  → solo desde main validado. Verificar CI green antes push.
NUNCA cambiar destino sin instrucción explícita del orchestrator.

## Files to stage (exact names)
<orchestrator provides exact list>

## Files to LEAVE ALONE (parallel sessions WIP — verify intactos post-stage)
<orchestrator provides explicit list from git status output>

## Commit message (HEREDOC required)
<orchestrator provides full message ending with Co-Authored-By line>

## Steps
1. `git status --short` — verify state
2. `git branch --show-current` — confirm current branch matches destination
3. **Commit por pathspec** (índice compartido en hub único — ADR-009): `git commit <file1> <file2> ... -m "$(cat <<'EOF' … EOF)"`. El partial commit incluye SOLO esos paths, ignora lo que otra sesión haya dejado staged → cero contaminación. (Pre-commit hook corre sobre esos paths igual.)
4. `git status --short` — verify other-session files still unstaged + intact
5. `git push origin <CURRENT_BRANCH>` — push to current branch (wip/*, main, or release/*)
6. `git log --oneline -2` — confirm commit pushed
7. Report final commit SHA + push result

Last line MUST be: `done -> <commit-sha>` or `failed -> <reason>`
```

## Orchestrator pre-spawn checklist

Antes de spawn Haiku worker, Opus orchestrator MUST:

1. **Run `git status --short`** y categorizar:
   - Files MINE (modified/added by current session) → stage list
   - Files OTHERS (parallel session WIP) → leave-alone list
2. **Verify branch type** (`git branch --show-current`) — determinar destino:
   - `wip/*` → push autosave normal
   - `main` → squash-merge previo requerido, verificar CI
   - `release/*` → verificar main validado, CI green
   - Otro (legacy) → STOP, switch a wip/* o main primero
3. **Compose commit message** con:
   - Conventional Commits format (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`)
   - Body explica "why" (1-3 lines), no "what"
   - Referencias a tickets/origen si aplica
   - `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` line al cierre
4. **Reject pre-spawn si:**
   - User pidió commit pero hay archivos secret-likely (`.env*`, `credentials*`, `*.pem`) en stage list → STOP, escalate
   - Branch es legacy o desconocido (no wip/*, main, release/*) → STOP, switch first
   - Tree completamente limpio (nada para commitear) → STOP, no spawn

## Spawn template (Opus copy-paste)

```js
Agent({
  description: "Commit + push <short-summary>",
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: "<full prompt with guardrails verbatim + files lists + HEREDOC message>"
})
```

## Anti-patterns prohibidos

- ❌ Opus orchestrator ejecuta `git commit -m` directo cuando hay >2 files stage → debió delegar
- ❌ Opus pasa "commit todos los cambios" a Haiku sin explicit file list (Haiku usaría `git add .`)
- ❌ Haiku worker recibe prompt sin guardrails verbatim
- ❌ Haiku worker recibe permission para `git pull` / `--force` / `--no-verify`
- ❌ HEREDOC commit message provisto como "auto-generate from diff" (Opus debe componerlo, Haiku no tiene contexto del diff semantic)
- ❌ Spawn Haiku con `subagent_type: builder-*` (esos son Opus por design — wrong agent type para git workflow)
- ❌ Worker edita CONTENIDO (campo de checkpoint/cap, código, cualquier valor) para que pase un gate → corrupción silenciosa de SSoT (HB-76). El worker REPORTA el bloqueo verbatim, NUNCA lo "arregla"
- ❌ Orchestrator instruye al worker "arreglá X para que pase el gate" — el spawn de commit NUNCA pide editar contenido; si el gate bloquea, el orchestrator (no el worker) decide el fix

## Failure handling

Haiku worker last-line:

- `done -> <sha>` → orchestrator continua
- `failed -> <reason>` → orchestrator lee reason:
  - "non-fast-forward" → STOP, escalate Chris (no pull). Aplica a main y release/*.
  - "pre-commit hook" → orchestrator inspecciona hook output, fix, re-spawn Haiku
  - "secret detected" → orchestrator escalates Chris immediately (security)
  - "branch mismatch" → orchestrator verifica branch type (wip/*/main/release/*) y corrige

## Referencias

- `.claude/rules/git-safety.md` — git fundamentals (single branch development, no pull, etc.)
- `.claude/rules/git-safety.md` — prohibiciones git + stage por pathspec
- `.claude/skills/commit-push/SKILL.md` — slash command wrapping este pattern
