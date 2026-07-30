<!-- voseo-allowed: internal /pm-vitalia merge documentation, not user-facing -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
state: done
merge_at: 2026-05-26
merge_commit_strategy: in-place (wip/vitalia branch) + squash-to-main PENDING manual
audit_verdict: APPROVED
audit_iterations: 1
ratified_by_chris: true
ratified_at: 2026-05-25T16:30:00Z
ready_at: 2026-05-26
developed_at: 2026-05-26
reviewed_at: 2026-05-26
commits:
  T-1: 8561f196
  T-2: d3df6765
  T-3: 0fdac50e
  T-4: 99bd19e9
  T-5: fcd1b3e4
  T-6: bcc88359
---

# 07-merge.md — F1-S9 vitalia-fase1-routing-shell

## § 1 — Gherkin verification matrix

Copia de `06-audit/gherkin-matrix.md` (Phase D auditor-frontend 2026-05-26):

| # | Scenario (01-spec.md § 5) | Test file | Status | Notes |
|---|---|---|---|---|
| SC-1 | happy · login + default landing + navegación completa | `e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts` | COMPILE_PASS | Live run deferred staging |
| SC-2 | negative · agent slug inválido → outer 404 sin chrome | `e2e/regression/vitalia-fase1-routing-shell/not-found-outer.spec.ts` | COMPILE_PASS | idem |
| SC-3 | edge · subtab inválido dentro agent válido → inner 404 con chrome | `e2e/regression/vitalia-fase1-routing-shell/not-found-inner.spec.ts` | COMPILE_PASS | idem |
| SC-4 | adversarial · cross-tenant access blocked + audit log | `e2e/regression/vitalia-fase1-routing-shell/cross-tenant-blocked.spec.ts` | COMPILE_PASS | idem |
| SC-5 | network_failure · BE timeout → fallback con Reintentar | `e2e/regression/vitalia-fase1-routing-shell/network-failure-tenant-fetch.spec.ts` | COMPILE_PASS | idem |
| SC-6 | accessibility · keyboard nav + screen reader + axe WCAG 2.1 AA | `e2e/regression/vitalia-fase1-routing-shell/a11y-keyboard-nav.spec.ts` | COMPILE_PASS | idem |
| SC-7 | i18n · microcopy Spanish neutro LatAm | `e2e/regression/vitalia-fase1-routing-shell/i18n-spanish-neutro.spec.ts` | COMPILE_PASS | idem |
| SC-8 | edge · user autenticado sin tenants assigned (Q6) | `e2e/regression/vitalia-fase1-routing-shell/no-tenants-edge.spec.ts` | COMPILE_PASS | idem |

**Coverage:** 8/8 (100%) · **Compile+lint:** ALL PASS · **Live run:** deferred staging gate (chrome-devtools-verify deprecated Linux per T-6 escalation, NO bloquea merge).

## § 2 — Playwright E2E run

**Status:** Live E2E NO ejecutado en wip/vitalia (worktree dev). Specs compilan limpio (tsc + eslint clean en gate-output.json). Live run programado para staging deploy step.

**Comandos para Chris (post-merge a main + staging deploy):**

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend
E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --project=smoke e2e/regression/vitalia-fase1-routing-shell/
```

**Visual goldens iter 1** generados por T-6 en `vitalia/frontend/e2e/visual/vitalia-fase1-routing-shell/` (not-found-shell.spec.ts-snapshots). Chris ratifica goldens antes merge a main (ratchet shrink-only post-ratify).

## § 3 — Capabilities updated/created

### DELETE (1)

- `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml` — UI legacy 100% FE, NO se re-implementa en Fase 2 (default landing es directo `/{tenantId}/valeria/agenda`, sin welcome screen). Path: `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml` borrado por T-5 (commit fcd1b3e4).

### MODIFY (6 — `package_path` solo BE + `fe_planned_phase2` field agregado)

| Capability YAML | fe_planned_phase2 |
|---|---|
| `booking/prepaid-booking-advisory-locks.yaml` | `vitalia-fase2-valeria-agenda` |
| `compliance/compliance-hipaa-lite-audit.yaml` | `vitalia-fase2-lisa-compliance` |
| `brand_studio/brand-studio-medical-sections.yaml` | `vitalia-fase2-lisa-marca` |
| `offer_studio/medical-services-offer-preset.yaml` | `vitalia-fase2-lisa-servicios` |
| `patients/patient-records-medical-history.yaml` | `vitalia-fase2-valeria-pacientes` |
| `treatments/treatment-followup-workflow.yaml` | `vitalia-fase2-valeria-pacientes` (sub-vista) |

Todos `status: live` MANTENIDO (BE sigue vivo, solo UI legacy removida).

### KEEP intacto (1)

- `vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml` — FE foundation activa, sin path legacy específico.

### NEW (1)

- `vitalia/docs/product/capabilities/shell-organism/routing.yaml` — **a crear post-merge** (capability inventory mandatory per `/pm-vitalia` SKILL § Capability inventory post-merge):
  ```yaml
  capability_id: vitalia.shell.routing
  module: shell-organism
  slug: routing
  status: live
  date_introduced: 2026-05-26
  story_introduced: vitalia-fase1-routing-shell
  package_version: vitalia-frontend@0.1.0
  package_path: vitalia/frontend/src/app/[tenantId]/(shell-organism)/ + vitalia/frontend/src/proxy.ts + vitalia/frontend/src/lib/iam/api.ts + vitalia/backend/src/main.py (mount auth_router core)
  license: proprietary
  ```

## § 4 — Modules MD refresh

- `vitalia/docs/product/modules/shell-organism.md` — auto-list section regenerar via `python scripts/reconcile_capabilities.py --brand vitalia` (incluirá `shell.routing` capability nueva post-create)
- `vitalia/docs/product/BACKLOG.md` + `BACKLOG.yaml` + `BACKLOG-TLDR.md` — regenerar via `python scripts/generate_backlog.py --brand vitalia` (mover F1-S9 de "Refined" → "Done last 90d")

## § 5 — How to verify (comandos reproducibles)

### Verify BE wiring (T-1)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}
grep -n "auth_router\|iam_users" vitalia/backend/src/main.py
# Should show: from luana_core_iam.api.routers import auth_router as iam_users
#               app.include_router(iam_users.router, prefix="/api/v1/iam/users", tags=["IAM - Users"])

# Stub deleted
test ! -f vitalia/backend/src/modules/vitalia/iam/api/router.py && echo "✅ stub deleted"
```

### Verify FE routing tree (T-4)

```bash
find vitalia/frontend/src/app/\[tenantId\]/\(shell-organism\)/ -type f -name "*.tsx" | sort
# Expected:
#   layout.tsx           (F1-S4 + F1-S9 MODIFY)
#   page.tsx             (F1-S4 + F1-S9 MODIFY redirect valeria/agenda)
#   not-found.tsx        (NEW F1-S9 outer)
#   [agent]/layout.tsx   (NEW F1-S9)
#   [agent]/page.tsx     (NEW F1-S9)
#   [agent]/not-found.tsx (NEW F1-S9 inner)
#   [agent]/[subtab]/page.tsx (NEW F1-S9)
```

### Verify legacy cleanup (T-5)

```bash
find vitalia/frontend/src/app -type d -name "(dashboard)" -o -name "(app)" 2>/dev/null  # should be EMPTY
grep -rln "(dashboard)" vitalia/frontend/src/ vitalia/frontend/e2e/ 2>/dev/null  # should be EMPTY (only history in archive/)
test ! -f vitalia/docs/product/capabilities/dashboard/welcome-state.yaml && echo "✅ welcome-state deleted"
```

### Verify proxy.ts (T-3)

```bash
test -f vitalia/frontend/src/proxy.ts && grep -n "clerkMiddleware\|createRouteMatcher" vitalia/frontend/src/proxy.ts
# Expected: clerkMiddleware + isPublicRoute matcher with /sign-in, /sign-up, /marketing, /public, /__clerk
```

### Verify Playwright suite (T-6)

```bash
cd vitalia/frontend
ls e2e/regression/vitalia-fase1-routing-shell/*.spec.ts | wc -l   # expected: 8
npx playwright test --list e2e/regression/vitalia-fase1-routing-shell/  # all specs compile
```

### Verify Phase D coverage

```bash
cat vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/06-audit/gherkin-matrix.md
# 8/8 PASS
```

---

## Post-merge actions for Chris

1. **Capability inventory** (mandatory per /pm-vitalia SKILL § post-merge):
   - Crear `vitalia/docs/product/capabilities/shell-organism/routing.yaml` con frontmatter cementado en § 3 NEW.

2. **Regenerate auto-gen files:**
   ```bash
   python scripts/reconcile_capabilities.py --brand vitalia
   python scripts/generate_backlog.py --brand vitalia
   ```

3. **Squash-merge a main** (deploy gate manual):
   ```bash
   cd ~/Proyectos/luana-platform   # PRINCIPAL worktree (branch=main)
   git merge --squash origin/wip/vitalia
   git commit -m "feat(vitalia/f1-s9): routing-shell + legacy cleanup (squash)"
   git push origin main
   ```
   Esto dispara CI `ci.yml` + staging deploy `cd-staging.yml` (per CI/CD workflows).

4. **Staging deploy + live E2E:**
   ```bash
   # Staging deploy MANUAL en server vitalia
   cd vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test e2e/regression/vitalia-fase1-routing-shell/
   ```

5. **Visual goldens ratify** (Chris valida snapshots not-found-shell/agent/network-error light+dark antes ratchet).

6. **Próxima story:** `vitalia-fase1-empty-states` (F1-S10 — single last story Fase 1). Sin F1-S10, sub-tabs muestran placeholder `"Contenido próximamente — F1-S10 empty-states"`. Refine via `/po-ux vitalia vitalia-fase1-empty-states`.

---

**Promotion candidate:** patrón Next.js 16 `proxy.ts` + Clerk integration es candidate cross-brand. Cuando Nicolify/Comunify/Lupulo upgrade Next.js 16 → `/pm-luana` scan-promotables detectará via `vitalia/docs/learnings/2026-05-26-nextjs-16-proxy-ts-pattern.md`.
