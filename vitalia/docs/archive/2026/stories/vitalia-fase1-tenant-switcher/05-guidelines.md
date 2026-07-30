<!-- voseo-allowed: internal guidelines referencing glossary verbatim -->

---
story_id: vitalia-fase1-tenant-switcher
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-22
architect_iter: 1
---

# F1-S3 `vitalia-fase1-tenant-switcher` — 05-guidelines

## § 1 — Must-load skills (builder bootstrap obligatorio)

Builders (`builder-frontend` Sonnet/opencode) MUST cargar estos skills en bootstrap antes de tocar código:

| Skill | Quando cargarlo | Razón |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries, Server-First, "use client" solo hojas con state, React Query patterns, Zustand persist defaults, FE quality runtime checklist |
| `tessl__shadcn-ui` | T-2 (TenantBadge) + T-3 (TenantOption) + T-6 (AddClinicModal) + T-7 (TenantSwitcher) | DropdownMenu primitives canonical · Dialog primitives · Alert primitives · Skeleton primitives. Verify CLI version + scaffolds patterns. |
| `tessl__tailwind` | T-1 (PALETTE) + cualquier component touching shell tokens | Semantic tokens shell (bg/foreground/accent/muted/ring) + contrast utilities verification |
| `tessl__zustand` | T-4 (tenant-store) | persist middleware partialize + version migrations + createJSONStorage canonical |
| `tessl__react-query` | T-5 (useTenants) | useQuery v5 patterns + staleTime/gcTime defaults + useEffect hidratación pattern (NOT deprecated onSuccess) |
| `playwright-expert` | T-9 (E2E specs) | Clerk auth fixture pattern, POM patterns, fixture mocks, freshness gate, retry+sanity, anti-patterns |

NO cargar skills agentic (`copilot-expert`, `sales-agent-expert`) — out-of-scope F1-S3.

NO cargar `backend-expert` ni `brand-expert` ni `offer-expert` ni `metrics-expert` — out-of-scope F1-S3 (frontend-only chrome UI).

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | toda toca FSD boundaries shell-organism |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo (glosario referencial) |
| `.claude/rules/tenant-isolation.md` (raíz) | fetchClient X-Tenant-ID auto-inject (existente F1-S0) |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan (2 brands under threshold) |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright native execution + port 3002 vitalia |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | visual golden side-by-side mockup HTML ratificado |
| `vitalia/.claude/rules/hipaa-lite.md` | scope CHECK: declarar no-PHI-scope explícito (NO aplica funcional este PR) |

## § 3 — Patterns required (debe usarse)

1. **Radix DropdownMenu primitives nativos** — usar `<DropdownMenu>`, `<DropdownMenuTrigger asChild>`, `<DropdownMenuContent role="menu">`, `<DropdownMenuItem onSelect>`, `<DropdownMenuLabel>`, `<DropdownMenuSeparator>`. Radix provee a11y keyboard nav + ARIA roles nativo. NO reinventar dropdown custom.

2. **`fetchClient` auto-inyecta `X-Tenant-ID`** — usar `fetchClient<TenantsApiResponse>('/api/tenants')` desde `vitalia/frontend/src/lib/api/fetchClient.ts` (existente F1-S0). NO `fetch()` manual, NO `axios`, NO bypass del wrapper.

3. **Zustand persist con `partialize` ONLY `activeTenant`** — `availableTenants` SIEMPRE hidrata fresh de API en mount. Garantiza cross-session no-stale data + Scenario 6 isolation.

4. **React Query v5 hidratación store via `useEffect`** — `query.data` watchef en `useEffect`, NO usar `onSuccess` callback (deprecated v5).

5. **`staleTime: 5 * 60 * 1000` para `useTenants`** — tenants list raramente cambia mid-session, 5min reduce network calls.

6. **Hash determinístico cross-session** — `pickPaletteColor(tenant.id)` usa `charCodeAt` sum + `% 6`. NO `Math.random`, NO `Date.now`, NO async. Test reproducible.

7. **Path preservation regex algorithm** — `pathname.replace(/^\/[^/]+/, \`/${newTenantId}\`)`. NO string concat manual. Exported puro para test independiente.

8. **`aria-label="Cambiar clínica"` on trigger button** — screen reader discovery.

9. **`aria-hidden="true"` on TenantBadge** — decorativo, no aporta info nueva al SR.

10. **`sr-only` para "Clínica activa" + "Cargando clínicas…"** — screen reader feedback estados invisibles visualmente.

11. **`title={tenant.name}` tooltip nativo browser** — accesibilidad básica + UX hover. NO Shadcn Tooltip overhead (300ms delay default).

12. **Server Components donde posible** — `TenantBadge` y `TenantOption` son Server Components (pure render, no state). `TenantSwitcher`, `AddClinicPlaceholderModal`, `TenantStoreBootstrap` Client Components justificados (state + effects + DOM events).

13. **`event.preventDefault()` en `<DropdownMenuItem onSelect>`** — prevenir Radix auto-close ANTES del `window.location.href` redirect. Sino race condition dropdown unmount vs redirect.

14. **`window.location.href` para tenant switch (hard redirect)** — NO `router.push()`. Hard reload garantiza:
    - React Query cache full re-mount (no stale tenant-scoped data)
    - Clerk JWT re-validation
    - Cualquier app-level state derivado refresca consistente

15. **TDD RED-first per ticket** — test que falla ANTES de implementar GREEN. Orden domain → infra → app → API/E2E mapeado a hook → component → store → integration.

16. **`structlog`-style log para warn** — N/A FE (no structlog en JS). Usar `console.warn` para Scenario 2 invalid tenant id (NO `console.log`, NO Sentry custom span — over-engineering para edge devtools-only).

17. **Visual goldens side-by-side mockup HTML** — Playwright snapshot `maxDiffPixelRatio: 0.001` (0.1%) per `shell-mockup-per-component.md`. Mockups HTML en `mockups/` son SSoT visual ratificado por Chris.

## § 4 — Patterns forbidden (NUNCA usar)

1. **Clerk Organizations** — `useOrganization`, `orgId`, `Clerk.useOrganizationList`, `<OrganizationSwitcher>`. PROHIBIDO per `MEMORY::no-clerk-organizations` 2026-05-20. Vitalia multi-tenancy vive en engine `luana-core-iam` con tenants+users propios. Clerk solo identity provider (JWT).

2. **Cross-brand imports** — `from '../../../../nicolify/...'`, `from '@/comunify/...'`, `from 'lupulo/...'`. PROHIBIDO per `.claude/rules/anti-duplication.md`. Solo permitido `nicolify/frontend/src/.../TenantSwitcher.tsx` como **referencia visual** (75% reuse documentado § 10 03-arch) NO como import directo.

3. **Hardcoded tenant data** — `const tenants = [{id: 'sonrisa-plena', ...}]` en producción. Data debe venir de `useTenants()` React Query. Hardcoded SOLO permitido en:
   - Fixtures Playwright (`e2e/fixtures/tenants.fixture.ts`)
   - Mock vitest unit tests
   - Storybook stories (si aplican, no scope F1-S3)

4. **Avatar image fetch** — Vitalia usa `TenantBadge` colored square + initials, NO `<img src={tenant.avatar_url} />`. Data shape BE D2 cementado solo `{id, name, city}`.

5. **`window.localStorage.setItem(...)` directo** — debe ir vía Zustand `persist` middleware. Direct localStorage rompe state consistency + persist version migrations.

6. **`useRouter().push()` para tenant switch** — debe ser `window.location.href` hard redirect. Soft push NO invalida React Query cache + NO re-valida JWT.

7. **Inferir `activeTenant` del URL segment `[tenantId]`** — single source of truth = Zustand store. URL segment es derivada (post-redirect). Inferir del URL crea race conditions y stale store.

8. **PHI fields** — patient_name, dni, diagnosis, treatment, medication, lab_results, etc. F1-S3 es scope no-PHI declarado 03-arch § 9. Arch test `val-arch-no-phi-leak` enforce.

9. **Voseo en strings UI** — `vos/tenés/podés/dale/mirá/dejá/sos`. Arch test `val-arch-spanish-neutro` enforce regex match no-voseo (excluye magic-comment `voseo-allowed` files). Excepción: este `05-guidelines.md` cita glosario verbatim → magic-comment header line 1.

10. **`<DropdownMenuItem onClick={...}>`** — usar `onSelect` (Radix canonical). `onClick` funciona pero no integra con Radix focus management.

11. **Default exports** — `export default function TenantSwitcher()`. Usar named exports siempre (`export function TenantSwitcher()`). Excepción única: Next.js pages (no aplica scope F1-S3).

12. **`any` type** — TypeScript strict. Usar `unknown` + type guards si tipo es dinámico.

13. **`Math.random()` en palette** — palette MUST ser determinístico (test fixtures expected cross-session). Hash `charCodeAt` sum.

14. **Storybook stories en lugar de E2E visual goldens** — F1-S3 NO usa Storybook (vitalia frontend no tiene Storybook setup productivo). Visual contract es Playwright snapshot vs mockup HTML ratificado.

15. **`window.location.reload()` o `router.refresh()`** — Scenario 1 happy switch DEBE ser `window.location.href = newPath` para preservar path. Reload retiene mismo URL sin cambio tenant.

16. **Magic strings duplicados** — copy verbatim spec § 9 vive en componentes (single source). NO replicar "Cambiar clínica" / "MIS CLÍNICAS" / etc. en múltiples archivos. Si requiere lift a constants module → propose Fase 2.

## § 5 — Files in scope (whitelist exhaustivo paths)

**NEW files (builders crean):**

```
vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx
vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx
vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx
vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx
vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx
vitalia/frontend/src/stores/tenant-store.ts
vitalia/frontend/src/hooks/useTenants.ts
vitalia/frontend/src/hooks/useSignOutCleanup.ts
vitalia/frontend/src/lib/tenant-palette.ts

# Tests Vitest
vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantBadge.test.tsx
vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantOption.test.tsx
vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantSwitcher.test.tsx
vitalia/frontend/src/stores/__tests__/tenant-store.test.ts
vitalia/frontend/src/lib/__tests__/tenant-palette.test.ts

# Arch fitness NEW
vitalia/frontend/src/__tests__/architecture/test-no-clerk-organizations.test.ts

# Playwright E2E (11 spec files)
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/happy-switch.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-clicks.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/adversarial-cross-tenant.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/race-multi-tab.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-users.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/network-failure.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/empty-state.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/large-dataset.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/a11y-keyboard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/i18n-spanish-neutro.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/single-tenant.spec.ts

# Playwright visual goldens (8 spec files)
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-closed-light.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-closed-dark.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-light.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-dark.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-loading.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-error.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-single-tenant.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/visual-open-12-tenants.spec.ts

# POM + fixtures
vitalia/frontend/e2e/poms/tenant-switcher.pom.ts
vitalia/frontend/e2e/fixtures/tenants.fixture.ts
```

**MODIFY files (builders editan):**

```
vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx
  └─ 1 línea diff: import TenantSwitcher + JSX <TenantSwitcher /> en lugar de <TenantSwitcherSlot />

vitalia/frontend/src/app/layout.tsx
  └─ mount <TenantStoreBootstrap /> dentro QueryClientProvider scope
```

**DELETE files (builders eliminan):**

```
vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx
  └─ placeholder F1-S2 cumplió rol drop-in
```

**OUT-OF-SCOPE (NO tocar este PR):**

- Cualquier archivo bajo `vitalia/frontend/src/features/{lisa,adrian,camila,...}/` (sub-tabs agéntico, scope Fase 2)
- Cualquier archivo bajo `core/luana-core-*/` (engine, requiere `/pm-luana` promotion)
- Cualquier archivo bajo `nicolify|comunify|lupulo/` (cross-brand prohibido)
- `vitalia/backend/` (no BE work — endpoint shipped Story 11)
- `vitalia/frontend/playwright.config.ts` (config existente F1-S0 + F1-S2 cubre)
- `vitalia/frontend/src/lib/api/fetchClient.ts` (existente F1-S0 — sin modificación)
- `vitalia/frontend/src/components/ui/*` (Shadcn primitives — F1-S0 instaló; este PR consume sin modificar)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (reference doc, NO edit este PR)

## § 6 — Build sequence convention (per ticket)

Cada ticket sigue mismo loop (builder Sonnet/opencode autonomous):

```
1. Lee ticket scope (acceptance.validator_ids + gherkin_coverage)
2. Lee/explora archivos PRIMARIOS del scope (whitelist § 5)
3. Lee skills/rules a cargar (§ 1 + § 2 this guide)
4. Escribe RED test primero (TDD — falla con razón explícita)
5. Implementa GREEN minimal — pasa test sin scope creep
6. Run validator(s) del ticket (acceptance.validator_ids)
7. Lint + typecheck + format clean
8. Commit con Conventional Commits + Co-Authored-By
9. Push wip/vitalia (current branch — M11 nunca >30 min)
10. Last line: done -> T-{n}-result.md  o  blocked -> T-{n}-impl-log.md
```

**Ratchet shrink-only** — NO agregar entries a allowlists existentes. Goldens visuales iniciales = baseline ratchet forward.

## § 7 — Cross-cutting concerns reminder

- **Tenant isolation** — `fetchClient` ya inyecta `X-Tenant-ID` (raíz `tenant-isolation.md`). Builders NO escriben código de inyección manual.
- **Native-first lint/tests** — `npx tsc`, `npx eslint`, `npx vitest`, `npx playwright`. NUNCA `docker exec`.
- **Stack levantado per brand para E2E** — `make dev-vitalia` (ports backend=8002, frontend=3002, postgres=5435 shared).
- **Worktree-aware** — todo trabajo en branch `wip/vitalia` (canónico) en `~/Proyectos/luana-vitalia/`. NO crear worktree story-specific salvo `EXPLICIT_USER_REQUEST=1` per `parallel-safety.md` M12.

## § 8 — Definition of Done per ticket

Un ticket cierra `state: developed` solo cuando:
- [ ] Todos los `acceptance.validator_ids` GREEN (run + capture output)
- [ ] Lint + typecheck clean (val-fe-lint + val-fe-tsc)
- [ ] TDD orden respetado (RED commit antes GREEN commit)
- [ ] Push wip/vitalia exitoso (SHA capturado en T-{n}-result.md)
- [ ] Spanish neutro verificado (regex no-voseo grep manual o val-arch-spanish-neutro)
- [ ] NO regression en arch fitness gates (val-arch-fsd + val-arch-no-clerk-orgs + val-arch-no-cross-brand + val-arch-no-phi-leak)
- [ ] T-{n}-result.md escrito con secciones: archivos tocados, validator output, commit SHA, gherkin_coverage achieved

## § 9 — Definition of Done para la STORY

Story cierra `state: developed` solo cuando **todos los tickets T-1..T-N** están `developed`. Auto-handoff a `/auditor` per `story-closure-gate.md` cementado 2026-05-18.

**Sin escape valve `defer_audit: true` ratificado Chris.** Cualquier intento de arrancar otra story con F1-S3 en state developed sin auditar = BLOCKED por skill `/dev-team` Step 5 + pre-commit hook Section 12.

---

**Fin 05-guidelines.md F1-S3 v1.0 · /architect Vitalia · 2026-05-22.**
