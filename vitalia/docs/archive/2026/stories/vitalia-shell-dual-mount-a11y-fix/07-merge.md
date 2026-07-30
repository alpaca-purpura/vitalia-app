# 07-merge — vitalia-shell-dual-mount-a11y-fix

> Merge artifact · `/pm-vitalia` · 2026-06-01
> Type: bugfix (ADR-011) · cap_change_type: fix · cap_target: shell-organism/shell-vitalia
> Auditor verdict: **APPROVED** (auditor-frontend Opus) · CHECKPOINTS C1-C5 todos verdes
> state: reviewing → **done**

## Resumen

Bugfix arquitectónico del shell-organism: el `ShellOrganismLayoutClient` montaba el panel-content
2× en desktop (rama desktop visible + rama mobile siempre montada oculta por CSS) → cada
`data-testid` resolvía a 2 elementos (strict-mode E2E) + `id="main-content"` aparecía 3× (HTML
inválido + landmark a11y duplicado). Fix: **UN solo `<main id="main-content">`** + **`<AppPanelSlot>`
renderizado UNA vez por rama XOR** (agentic/web), mobile vía CSS-hide de Valeria (no segunda rama),
`<Group>` siempre montado (hook-count estable → sin el crash "rendered more hooks" de nicolify).

## § 1 — Gherkin / DONE-bar verification matrix

Story bugfix sin Gherkin de producto nuevo; el DONE-bar de `03-arch.md` es la matriz:

| Criterio DONE (03-arch) | Verificación | Status |
|---|---|---|
| 1 `<main id="main-content">` por viewport | vitest ShellOrganismLayout + live spec ×3 modos | ✅ PASS |
| 1 `[data-testid=app-panel-slot]` (testids no duplicados) | live spec `.count()===1` agentic/web/mobile | ✅ PASS |
| axe wcag2aa sin id-dup / landmark-dup | live spec axe scoped → 0 violaciones | ✅ PASS |
| 5 agentes + valeria render OK agentic/web/mobile | vitest 501/501 + live lisa/valeria | ✅ PASS |
| dev-app live (ADR-008): lisa+valeria desktop+mobile, consola limpia | dev_app_verified.evidence (checkpoint) | ✅ PASS |
| Sin "more hooks than previous render" | live spec console capture → fatal=[] | ✅ PASS |

Phase D: no aplica matriz Gherkin clásica (bugfix estructural pre-spec-mapa-funcional). WARN no FAIL.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && set -a; source ../.env.dev; set +a
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/vitalia-shell-dual-mount-a11y-fix/single-slot-live.spec.ts --project=smoke
# → 6 passed (18.5s): setup(2) + 4 live tests (agentic-desktop, web-desktop, mobile, axe)
# LIVE contra stack real (FE:3002 + BE:8002), Clerk testing token, SIN backend mocks.
# Backend real golpeado en logs (GET /iam/users/me/tenants 200) → confirma no-mock.
```

Gates independientes (re-corridos por /auditor): tsc 0 · eslint 0 · vitest shell-organism **501/501**.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/shell-organism/shell-vitalia.yaml`
  - cap_change_type=**fix** → change_log entry type=fix appendeada (story `vitalia-shell-dual-mount-a11y-fix`, 2026-06-01). NO toca `scenarios[]` (bugfix no agrega comportamiento de producto). `last_modified: 2026-06-01`.

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/shell-organism.md` — auto-list regenera vía `make portfolio` post-merge (sin edición manual · R3).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
# 1. Unit (single-main + single-slot asserts):
cd ${WS}/vitalia/frontend && npx vitest run src/components/shared/shell-organism/   # 501 pass
# 2. Live (stack real, no mocks) — requiere make dev-vitalia up:
cd ${WS}/vitalia/frontend && set -a; source ../.env.dev; set +a
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/vitalia-shell-dual-mount-a11y-fix/single-slot-live.spec.ts --project=smoke
# 3. DOM sanity (manual): login dev-app → cualquier ruta /{tenant}/lisa/* →
#    document.querySelectorAll('#main-content').length === 1
#    document.querySelectorAll('[data-testid="app-panel-slot"]').length === 1
```

## Notas

- **Unblocks** `vitalia-fase2-lisa-doctores` (Pendiente B): el workaround `.filter({visible:true})` de los POMs ya no es necesario (el slot resuelve a 1).
- **Finding cross-brand para `/pm-luana`** (NO blocker): arch test `no-cross-brand-shell-mirror` falla por `SubTabMeta`/`extractSubtabFromPath` portados a nicolify (PRE-EXISTENTE en origin/main; este fix no los toca).
- **Bug de datos detectado en live-verify** (Pendiente B scope): `GET /clinics/doctors` 500 (X-Clinic-ID UUID) — `vitalia/docs/observed-bugs/2026-06-01-doctors-list-500-clinic-id-uuid.md`. NO afecta el shell.
- Commits: `b65baae6` (T-1 fix) · `bfb6d418` (T-2 live spec) · `387e9550` (audit artifacts).
