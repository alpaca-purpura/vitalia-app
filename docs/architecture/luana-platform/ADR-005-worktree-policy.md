# ADR-005 — Worktree Policy (multi-session paralelo + sincronización + lift core dedicado)

> **Status:** ACCEPTED
> **Date:** 2026-05-18
> **Decision-makers:** Chris (alpacapurpura@) + Claude Opus 4.7 (advisory)
> **Supersedes:** none
> **Superseded by:** ADR-009 (single-hub canonical topology, parcial)
> **Builds on:** [ADR-004](./ADR-004-git-branching-and-environments.md) (triple-branch policy + worktrees revocó ban legacy)
> **Related docs:**
>
> - `docs/process/parallel-sessions-protocol.md` — SSoT detallado del modelo (D1-D14)
> - `.claude/rules/parallel-safety.md` — runtime rules sincronizadas con D1-D14
> - `.claude/rules/step-0-worktree.md` — step 0 obligatorio skills `/pm-{brand}` y `/pm-luana`
> - `scripts/git/new-session.sh` — creación worktree (mec. B)
> - `scripts/git/cleanup-session.sh` — cierre worktree (mec. C)
> - `scripts/git/check-sync.sh` — T1 sync logic portable (mec. A logic)
> - `scripts/git/push-wip.sh` — T-push sync portable (mec. L logic)
> - `scripts/git/status-all.sh` — dashboard cross-worktree (mec. H)
> - `scripts/git/regenerate-manifest.sh` — recovery worktrees a mano (mec. M)
> - `docs/process/warp-multibrand-handbook.md` — manual operativo Warp

## 1. Context

### 1.1 ADR-004 revocó el ban worktrees pero dejó underspecified la operación diaria

ADR-004 (2026-05-15) revocó el ban histórico de worktrees y estableció triple-branch policy
(`wip/*`, `main`, `release/{brand}-vX.Y.Z`) + uso de worktrees por sesión paralela. Pero
quedaron sin codificar:

1. **Topología filesystem:** cuántos worktrees existen, dónde viven, qué los diferencia
2. **Naming convention:** patrones branch + path para distinguir canónicos, efímeros, multi-lane, hotfix, exp, lifts core
3. **Sincronización con `main`:** cómo los canónicos long-lived no se atrasan días respecto a main
4. **Política merge a main:** cuándo squash-merge, quién dispara, excepciones (hotfix bypass, exp nunca, multi-lane independiente)
5. **Cambios al `core/luana-core-*/`:** dónde vive físicamente el lift, cómo otros worktrees consumen
6. **Enforcement skills `/pm-{brand}`:** cómo cada skill detecta worktree mode + refuse invocación inválida
7. **opencode parity:** qué cambia cuando la sesión es opencode en vez de Claude Code

### 1.2 Problemática operativa observada

Chris opera 2-3 sesiones paralelas (brands distintas) + ocasionalmente multi-lane dentro de
una brand. Sin codificación explícita:

- Canónicos long-lived quedan días atrasados → cuando intentan pushear/mergear → conflictos masivos
- Cambios al core en una sesión no se propagan visiblemente a otras sesiones consumidoras
- Skills `/pm-{brand}` invocados accidentalmente desde worktree de otra brand → leaks de scope
- Disciplina humana es la única defensa → frágil

## 2. Decision

Adoptar el modelo cementado en `docs/process/parallel-sessions-protocol.md` D1-D14. Resumen:

### 2.1 Topología (D2)

| Path | Tipo | Branch | Editar código |
|---|---|---|---|
| `~/Proyectos/luana-platform/` | PRINCIPAL | `main` | ❌ NO (solo merges + read cross-brand) |
| `~/Proyectos/luana-{brand}/` | CANÓNICO long-lived | `wip/{brand}` ESTABLE (nunca rota por story — ver Addendum v2 §7.2) | ✅ SÍ |
| `~/Proyectos/luana-{brand}-{slug}/` | EFÍMERO brand | `wip/{brand}-{slug}[-{lane}]` | ✅ SÍ |
| `~/Proyectos/luana-{brand}-hotfix-{slug}/` | EFÍMERO hotfix | `hotfix/{brand}-{slug}` | ✅ SÍ |
| `~/Proyectos/luana-{brand}-exp-{slug}/` | EFÍMERO experimento | `exp/{brand}-{slug}` | ✅ SÍ (NUNCA mergea) |
| `~/Proyectos/luana-core-{slug}/` | EFÍMERO core (D12) | `wip/core-{slug}` | ✅ SÍ (lift gate `/pm-luana`) |

### 2.2 Sincronización canónicos (D10)

3 triggers de sync hacia `origin/main`:

| Trigger | Aplica a | Comportamiento |
|---|---|---|
| T1 SessionStart hook (mec. A) | PRINCIPAL + CANÓNICO | auto-FF si tree clean + FF puro; advisory si merge real; banner LOUD si dirty + core changed |
| T2 `/pm-{brand}` step 0 (mec. N) | TODOS los wip/* | misma lógica T1 |
| T-push PreToolUse (mec. L) | TODOS los wip/* | fetch + advisory pre-push (no bloquea) |

### 2.3 Política merge (D11)

- Default: 1 squash-merge por story al cerrar `state=done` (auditor APPROVED + CHECKPOINTS aplicados). `/pm-{brand}` ejecuta como parte de transición `state=reviewing→done`.
- Checkpoint mid-story opcional cuando mitad lógica está cerrada.
- Hotfix bypass auditor formal (require `repro_verified: true` + test regression RED→GREEN).
- Experimentos NUNCA mergean. Cleanup extrae learnings.
- Multi-lane: cada lane mergea independiente cuando su `/auditor` lane APPROVED.
- Core change requiere `/pm-luana` promotion proposal `state ≥ accepted`.

### 2.4 Cambios al core (D12)

- Worktree dedicado `~/Proyectos/luana-core-{slug}/` con branch `wip/core-{slug}`
- Manifest `.session.yaml::brand = core` (pseudo-brand reservado)
- Cross-worktree dependency: T1 + advisory `uv sync` / `pnpm install` si lift cambió deps
- Breaking change: `/pm-luana` coordina stories cross-brand en release window

### 2.5 Step 0 enforcement (D13)

- SSoT `.claude/rules/step-0-worktree.md` consumido por skills via `@import`
- HARD refuse cuando skill `/pm-{brand-X}` invocado desde worktree de otra brand
- `/pm-luana` permite ejecución desde PRINCIPAL, CANÓNICO brand, EFÍMERO core (soft warn desde EFÍMERO brand-specific)

### 2.6 opencode parity (D14)

3 capas:
1. Bash scripts como SSoT portable
2. Claude Code hooks como sugar daily
3. Warp Workflows como sugar manual/opencode

opencode honra `.claude/skills/` y `.claude/rules/`. Hooks ausentes → scripts manuales.

## 3. Consequences

### 3.1 Positivas

- Aislamiento físico por sesión via worktree dedicado (git impide colisión por diseño)
- Canónicos al día via 3 triggers de sync
- Excepciones formales codificadas (hotfix, exp, multi-lane, core)
- Skills no se invocan accidentalmente cross-brand
- Modelo funciona en Claude Code Y opencode
- Lifts core con worktree dedicado mantienen separation of concerns

### 3.2 Negativas / Trade-offs

- **Espacio en disco:** cada worktree clona `node_modules/` (~500 MB cuando aplica)
- **RAM:** max 1 stack Docker por brand limita paralelo dentro de brand
- **Onboarding:** modelo más complejo que single-branch; requiere lectura del protocol completo + warp handbook
- **opencode requiere disciplina manual** (Warp Workflows mitigan)
- **Checkpoints mid-story no scripteados todavía** (procedimiento documentado, scripteamos cuando aparezca el primer caso)

### 3.3 Riesgos mitigados

- **Disciplina humana:** reemplazada por scripts + hooks + enforcement skills
- **Pérdida de WIP:** mec. B asegura branch wip/* desde origin/main fresco; M11 push ≤30 min
- **Cross-brand leak:** step 0 HARD refuse + auditor cross-brand mirror scan
- **Engine drift:** promotion gate `/pm-luana` + downstream regression R3

## 4. Alternatives Considered

### 4.1 Single-branch development con disciplina humana (legacy)

Status: rejected en ADR-004. Comprobado frágil con 2-3 sesiones paralelas + multimarca.

### 4.2 Worktrees sin enforcement formal (opción libre)

Status: rejected. Sin step 0 + sync triggers, los canónicos se atrasan + skills se invocan cross-brand.

### 4.3 Mono-branch en main + rebase frecuente

Status: rejected. Rebase + force-push prohibido (regla M5). main debe ser deployable siempre.

### 4.4 Auto-merge silencioso main → wip cuando hay cambios

Status: rejected en D10. Sólo FF puro silent; merge real requiere prompt (riesgo conflictos sutiles).

## 5. Implementation status

| Mecanismo | Status |
|---|---|
| B `new-session.sh` | ✅ implementado (promoted from v2 2026-05-18) |
| C `cleanup-session.sh` mejorado | ✅ implementado 2026-05-18 |
| A SessionStart hook + `check-sync.sh` | ✅ implementado 2026-05-18 |
| L `push-wip.sh` + Claude PreToolUse hook | ✅ implementado 2026-05-18 |
| H `status-all.sh` dashboard | ✅ implementado 2026-05-18 |
| M `regenerate-manifest.sh` | ✅ implementado 2026-05-18 |
| N `.claude/rules/step-0-worktree.md` SSoT | ✅ implementado 2026-05-18 |
| I PS1 bashrc snippet | ✅ implementado 2026-05-18 (`scripts/git/ps1-luana.sh`) |
| F wrapper `make dev-{brand}` con lock | ⏳ stub 2026-05-18 (Makefile) |
| G wrapper alembic con lock | ⏳ stub 2026-05-18 (`scripts/generate_migration.py`) |
| D pre-commit checks extras | ✅ implementado 2026-05-18 |
| K Warp Workflows yaml | ✅ implementado 2026-05-18 (`scripts/warp-workflows/`) |
| Warp handbook | ✅ implementado 2026-05-18 (`docs/process/warp-multibrand-handbook.md`) |

## 6. Future addenda

Cuando aparezca el primer caso real de checkpoint mid-story → codificar lessons en `scripts/git/checkpoint-merge.sh` o extender `cleanup-session.sh`. Hasta entonces, procedimiento manual documentado en D11.

Cuando bootstrap brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) → actualizar lista de brands válidas en `new-session.sh`, `step-0-worktree.md`, `status-all.sh`, y `docs/portfolio/PORTFOLIO.md` en mismo commit.

---

## 7. Addendum v2 (cementado 2026-05-18 PM — caso vitalia desorden)

### 7.1 Trigger del addendum

Caso vitalia 2026-05-18 reveló 4 gaps del modelo v1:

1. **Canónico rotaba branch story-by-story** (D2/D3 v1) → manifest se desactualizó, branch real ≠ manifest.branch, acumuló cross-brand mixing (vitalia + comunify + modelo en `wip/vitalia-slice-1-shipping`).
2. **Sub-agents creaban worktrees** (M9 v1) → fantasma `luana-vitalia-infra-cross-cutting` sin cleanup + sin manifest + casi pierde commits valiosos.
3. **Sync D10 v1 pasivo** (advisory only) → permitía trabajar sobre código viejo + cherry-pick comunify funcionó "by luck" (sin overlap).
4. **No había modo "N sesiones mismo cwd"** → forzaba worktree extra para sesión docs paralela a dev activa.

### 7.2 Decisiones v2 (supersedes parcial de v1)

| Decisión v2 | Supersedes v1 |
|---|---|
| **Canónico = `wip/{brand}` ESTABLE** (NUNCA rota story-by-story) | D2/D3 v1 (rota por story) |
| **Sync KISS activo** (auto-merge si limpio, BLOCK push si behind) | D10 v1 (advisory pasivo) |
| **Sub-agent worktree BAN total** (trabajan in-place sobre cwd caller) | M9 v1 (sub-agent responsable cleanup) |
| **Scope per branch enforced** (pre-commit Section 13 NEW) | (no había) |
| **N sesiones paralelas mismo cwd con lock buckets** (M14 NEW) | D9 v1 (1 sesión por worktree) |
| **Worktree story explicit user-only** (`EXPLICIT_USER_REQUEST=1`) | D2 v1 (skills creaban auto) |

### 7.3 Implementación

| Componente | Cambio | Path |
|---|---|---|
| Protocol doc | Update D2/D3/D4 + revision header v2 | `docs/process/parallel-sessions-protocol.md` |
| Plan doc | Resumen ejecutivo 12 puntos | `docs/process/worktree-protocol-v2-plan.md` |
| Runtime rule | M12/M13/M14 NEW + sub-agent ban + N sesiones | `.claude/rules/parallel-safety.md` |
| Hook scope gate | Section 13 NEW | `scripts/git-hooks/pre-commit` |
| Sync script | NEW | `scripts/git/sync-from-main.sh` |
| Push gate | BLOCK si behind main | `scripts/git/push-wip.sh` |
| Session script | TYPE=canonical sin SLUG, TYPE=story requiere flag | `scripts/git/new-session.sh` |

### 7.4 Migration vitalia/nicolify/comunify

- **vitalia:** rebrand `wip/vitalia-slice-1-shipping → wip/vitalia` estable en mismo cement-PR (squash-merge previo a main de 27 commits propios + 3 cherry-pick fantasma).
- **nicolify:** rebrand `wip/nicolify-bootstrap → wip/nicolify` (commit pendiente único f6d366c ya en main vía cherry-pick).
- **comunify:** rebrand `wip/comunify-bootstrap → wip/comunify` (sin trabajo pendiente).
- **Fantasma `wip/vitalia-infra-cross-cutting`:** eliminado worktree + branch local + remote.

### 7.5 Verificación cementación v2

```bash
git worktree list                    # 4 canónicos en wip/{brand} + 1 platform en main
scripts/git/sync-from-main.sh --check  # all canónicos: "up-to-date"
scripts/git-hooks/pre-commit         # Section 13 enforcement activo
```
