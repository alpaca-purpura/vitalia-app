<!-- voseo-allowed: internal step 0 SSoT for skill consumers, not user-facing -->
---
description: "Step 0 obligatorio (mec. N) — detection worktree + manifest + sync KISS + enforcement skills /pm-{sistema} y /pm-{platform}. SSoT D13 + v2 2026-05-18."
---

# Step 0 — Worktree detection + sync + enforcement (mec. N — v2)

**Consumed by:** `/pm-{sistema}` (×4 + 6 futuras) y `/pm-{platform}` via `@.claude/rules/step-0-worktree.md`.

**SSoT model:** `docs/process/parallel-sessions-protocol.md` § D13 + `docs/process/worktree-protocol-v2-plan.md` § CORE #3 + CORE #5.

**Detalle completo (12 pasos logic v2 verbatim + output canonical examples all-OK/advisory/HARD REFUSE + implementación práctica skill body):** `docs/rules-detail/step-0-worktree.md`. Skill `worktree-protocol` cubre troubleshoot + modificar reglas.

## Logic v2 (12 pasos — resumen ejecutable)

1. **Detect TYPE** via path regex sobre `git rev-parse --show-toplevel`: PRINCIPAL / CANÓNICO sistema=X / EFÍMERO story sistema=X / EFÍMERO core / EFÍMERO protocol / UNKNOWN
2. **Read manifest** `.session.yaml` (ausente en PRINCIPAL por diseño)
3. **Verify cross-coherence** sistema/type manifest matches path regex. Mismatch v2 NEW: AUTO-FIX manifest in-place (no escalate). Si sistema difiere (rare) → ESCALATE Chris
4. **Manifest ausente + path UNKNOWN** → STOP escalate
5. **Manifest ausente + path conocido** → advisory regenerar
6. **Aplicar enforcement matrix** (tabla abajo)
7. **Run sync KISS activo** `scripts/git/sync-from-main.sh` (modo ejecutar). Tree clean + FF puro → silent. Merge real OK → silent + 1 línea. Conflict → STOP + prompt. Tree dirty + merge real → STOP + "commit/stash WIP"
8. **List otros worktrees vivos** de la mismo sistema
9. **Cross-sistema mixing detection** HEAD vs main (advisory loud si bypass scope gate)
10. **Bucket lock acquire** `scripts/git/session-lock.sh acquire {bucket}` ∈ {code, docs, tests}
11. **Output canonical block** (compacto si OK, expandido si advisory/error)
12. **Si CANÓNICO + sync result auto-merge** → loguear en `{workspace.worktree_root}/{workspace.repo_prefix}-{sistema}/.session-log`

Bucket por skill: `/po-ux`,`/po`,`/ux-agentico` → docs · `/dev-team`,`/architect` → code · `/auditor` → code · `/pm-*` → no acquire (read-mostly).

## Enforcement matrix

| Skill | Worktree type / sistema | Verdict |
|---|---|---|
| `/pm-{sistema-X}` | CANÓNICO sistema X | ✅ OK proceed |
| `/pm-{sistema-X}` | EFÍMERO sistema X | ✅ OK + leer story/lane manifest |
| `/pm-{sistema-X}` | CANÓNICO/EFÍMERO sistema Y (Y≠X) | ❌ **HARD REFUSE** — STOP + redirect |
| `/pm-{sistema-X}` | PRINCIPAL | ❌ **HARD REFUSE** |
| `/pm-{sistema-X}` | EFÍMERO core | ❌ **HARD REFUSE** — core es /pm-{platform} |
| `/pm-{sistema-X}` | UNKNOWN | ❌ **HARD REFUSE** escalate |
| `/pm-{platform}` | PRINCIPAL | ✅ OK (default) |
| `/pm-{platform}` | CANÓNICO sistema X | ✅ OK (cross-sistema desde sistema context) |
| `/pm-{platform}` | EFÍMERO core | ✅ OK (lift work) |
| `/pm-{platform}` | EFÍMERO sistema X | ⚠️ OK + soft warn |
| `/pm-{platform}` | UNKNOWN | ❌ **HARD REFUSE** escalate |

## Output canonical (formato general)

```
[step 0 worktree]
  path:     <cwd>
  branch:   <branch> [tree state]
  type:     <PRINCIPAL|CANÓNICO|EFÍMERO> <sistema|core>
  manifest: sistema=<X> story=<Y> lane=<Z|—>
  sync:     <status>
  others:   <other worktrees same sistema>
[step 0 <OK|STOP>]
```

Ejemplos completos (all-OK compact, advisory sync, advisory loud core changed, HARD REFUSE): detail doc.

## Bloqueo

Step 0 ES bloqueante. Verdict HARD REFUSE → skill termina. Verdict OK + advisory → continúa pero advisory visible.

## Cuándo NO aplica

- Skills builders (`builder-*`) — NO cargan step 0
- Skills domain (`brand-expert`, `offer-expert`, etc.) — NO cargan step 0
- Skills git/tooling (`commit-push`, `git-manager`) — NO cargan step 0

Step 0 es exclusivo a skills que manejan SSoT funcional sistema-specific o cross-sistema (`/pm-*`).

## Referencias

- `docs/rules-detail/step-0-worktree.md` — **detalle completo** (12 pasos verbatim + output examples)
- `docs/process/parallel-sessions-protocol.md` § D8, D10, D12, D13
- `docs/architecture/{workspace.repo_prefix}-platform/ADR-005-worktree-policy.md`
- `.claude/rules/parallel-safety.md`
- `scripts/git/{check-sync,regenerate-manifest,status-all}.sh`
