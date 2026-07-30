<!-- voseo-allowed: internal step 0 SSoT for skill consumers, not user-facing -->
---
description: "Step 0 obligatorio (mec. N) — detection worktree + manifest + sync KISS activo + enforcement skills /pm-{brand} y /pm-luana. SSoT D13 + v2 cementado 2026-05-18 PM."
---

# Step 0 — Worktree detection + sync + enforcement (mec. N — v2)

**Consumed by:** `/pm-{brand}` (×4 brands activas + 6 futuras) y `/pm-luana` via `@.claude/rules/step-0-worktree.md` en frontmatter o body.

**SSoT model:** `docs/process/parallel-sessions-protocol.md` § D13 + `docs/process/worktree-protocol-v2-plan.md` § CORE #3 (sync KISS) + § CORE #5 (N sesiones mismo cwd).

## Logic v2 (12 pasos, ejecuta al bootstrap de cada invocación)

```text
1. Detect worktree TYPE via path regex (sobre `git rev-parse --show-toplevel`):
     ends with /luana-platform/?$            → PRINCIPAL
     ends with /luana-{brand}/?$              → CANÓNICO brand={brand}
     ends with /luana-{brand}-{slug}/?$       → EFÍMERO story brand={brand}
     ends with /luana-core-{slug}/?$          → EFÍMERO core (D12)
     ends with /luana-protocol-{slug}/?$      → EFÍMERO protocol (v2)
     otherwise                                 → UNKNOWN

   Brands válidas: vitalia, nicolify, comunify, lupulo (+ futuras: saasora,
   inmoflow, retailly, fixia, guestly, fitflow). `core`, `protocol` reservados.

2. Read manifest `.session.yaml` si existe (ausente en PRINCIPAL por diseño).

3. Verify cross-coherence: brand/type del manifest matches path regex.
   - Match → context OK
   - Mismatch v2 NEW: AUTO-FIX manifest in-place (regenera .session.yaml con
     branch real + brand de path + worktree_type derivado). NO escalate.
     Logueá: "manifest auto-fixed: branch X → Y matches current state".
   - Si brand del manifest difiere de brand del path (rare error) → ESCALATE Chris.

4. Manifest ausente + path UNKNOWN → STOP, escalate

5. Manifest ausente + path conocido (no PRINCIPAL) → advisory:
   "manifest ausente — regenerar con scripts/git/regenerate-manifest.sh"

6. Aplicar enforcement matrix (ver tabla más abajo).

7. Run sync KISS activo (v2 — supersedes check-sync.sh):
   `scripts/git/sync-from-main.sh` (no --check, modo ejecutar)
   - tree clean + FF puro       → auto-FF silencioso
   - tree clean + merge real OK → AUTO MERGE silencioso + 1 línea resumen
   - tree clean + merge conflict → STOP + lista archivos + prompt para resolver
   - tree dirty + FF puro       → auto-FF (no toca WIP)
   - tree dirty + merge real    → STOP + "commit/stash WIP, hago merge"
   - update .session.yaml.last_sync

8. List otros worktrees vivos de la misma brand:
   `git worktree list --porcelain | grep -B2 'branch refs/heads/(wip|hotfix|exp)/{brand}'`

9. (v2) Cross-brand mixing detection en HEAD vs main:
   `git diff main..HEAD --name-only | grep -E '^(brand-A|brand-B|brand-C)/'`
   donde brand-{A,B,C} son brands ≠ brand del worktree.
   Match → ADVISORY LOUD (debería haber sido bloqueado por pre-commit Section 13;
   si llegaste acá es porque scope gate fue bypass).

10. (v2) Bucket lock acquire para sesión actual:
    `scripts/git/session-lock.sh acquire {bucket}` donde {bucket} ∈ {code, docs, tests}.
    Skill infiere bucket por contexto:
      - `/po-ux`, `/po`, `/ux-agentico`     → bucket=docs
      - `/dev-team`, `/architect`            → bucket=code
      - `/auditor`                           → bucket=code (escribe reviews + verifica)
      - `/pm-{brand}`, `/pm-luana`           → no acquire (read-mostly + cross-bucket)
    Si bucket tomado por otra sesión → preguntar Chris: esperar, kick-if-crashed, o
    pedir worktree story explícito.

11. Output canonical block (compacto si OK, expandido si advisory/error).

12. (v2) Si CANÓNICO + sync result = "AUTO MERGE" o "auto-FF": loguear 1 línea
    en `~/Proyectos/luana-{brand}/.session-log` para que otras sesiones del mismo
    cwd vean estado fresh.
```

## Enforcement matrix

| Skill | Worktree type / brand | Verdict |
|---|---|---|
| `/pm-{brand-X}` | CANÓNICO brand X | ✅ OK proceed |
| `/pm-{brand-X}` | EFÍMERO brand X | ✅ OK + leer story/lane manifest |
| `/pm-{brand-X}` | CANÓNICO/EFÍMERO brand Y (Y≠X) | ❌ **HARD REFUSE** — STOP + redirect |
| `/pm-{brand-X}` | PRINCIPAL | ❌ **HARD REFUSE** — "principal no edita código brand" |
| `/pm-{brand-X}` | EFÍMERO core | ❌ **HARD REFUSE** — "core lift es /pm-luana territory" |
| `/pm-{brand-X}` | UNKNOWN | ❌ **HARD REFUSE** — escalate Chris |
| `/pm-luana` | PRINCIPAL | ✅ OK (default) |
| `/pm-luana` | CANÓNICO brand X | ✅ OK (cross-brand desde brand context) |
| `/pm-luana` | EFÍMERO core | ✅ OK (lift work) |
| `/pm-luana` | EFÍMERO brand X | ⚠️ OK + soft warn "vista cross-brand desde efímero brand-specific puede sesgar" |
| `/pm-luana` | UNKNOWN | ❌ **HARD REFUSE** — escalate Chris |

## Output canonical

### Caso all-OK (compacto, 5-6 líneas)

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

### Caso advisory (sync needed)

```
[step 0 worktree]
  path:     ~/Proyectos/luana-vitalia/
  branch:   wip/vitalia-copilot-tools-impl (tree clean)
  type:     CANÓNICO vitalia
  manifest: brand=vitalia story=copilot-tools-impl
  sync:     ↑ 3 commits behind origin/main (1 touches core/)
            → AUTO FF aplicado
            ↑ af8dfc3..b1c2d3e wip/vitalia-copilot-tools-impl
  others:   none
[step 0 OK]
```

### Caso advisory loud (dirty + core changed)

```
[step 0 worktree]
  path:     ~/Proyectos/luana-vitalia/
  branch:   wip/vitalia-copilot-tools-impl (tree dirty: 3 modified)
  type:     CANÓNICO vitalia
  sync:     5 commits behind origin/main

  ╔═══ CORE CHANGED while you worked ═══╗
  ║ commits: e5f6789 b1c2d3e             ║
  ║ affected: core/luana-core-observability/ ║
  ║ Recomendado: terminar WIP, push,     ║
  ║   fetch origin main && merge          ║
  ╚══════════════════════════════════════╝

[step 0 OK proceed with caution]
```

### Caso HARD REFUSE

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

## Implementación práctica (skill body)

Cada skill `/pm-{brand}` o `/pm-luana` debe ejecutar al bootstrap (en orden):

```bash
# 1. Detection (script portable o lógica inline)
bash scripts/git/check-sync.sh --detect-only > /tmp/step-0-context.txt
# (alternativa inline si scripts no disponibles)

# 2. Parsear context + aplicar enforcement matrix per la skill invocada

# 3. Si OK: imprimir output canonical + proceder
# 4. Si REFUSE: imprimir output STOP + terminar skill
```

**Importante:** este step 0 ES bloqueante. Si verdict = HARD REFUSE, skill termina sin continuar. Si verdict = OK con advisory → continúa pero deja el advisory visible.

## Cuándo NO aplica

- Skills builders (`builder-backend`, `builder-frontend`, `builder-agentic`) — NO cargan step 0 (no son PM, no manejan SSoT cross-brand)
- Skills domain (`brand-expert`, `offer-expert`, `metrics-expert`, etc.) — NO cargan step 0 (read-only o contextual)
- Skills git/tooling (`commit-push`, `git-manager`, etc.) — NO cargan step 0

Step 0 es exclusivo a skills que manejan SSoT funcional brand-specific o cross-brand (`/pm-{brand}` + `/pm-luana`).

## Referencias

- `docs/process/parallel-sessions-protocol.md` § D8, D10, D12, D13
- `docs/architecture/luana-platform/ADR-005-worktree-policy.md`
- `.claude/rules/parallel-safety.md`
- `scripts/git/check-sync.sh` — T1/T2 sync logic portable
- `scripts/git/regenerate-manifest.sh` — recovery worktrees a mano
- `scripts/git/status-all.sh` — dashboard cross-worktree (mec. H)
