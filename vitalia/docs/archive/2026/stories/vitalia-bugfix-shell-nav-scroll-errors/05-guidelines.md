# 05-guidelines.md — vitalia-bugfix-shell-nav-scroll-errors

> Bugfix lite FE-only. Cambios mínimos, root-cause-only (debugging.md). No tech debt nuevo.

## Patterns required

- **Repro-first (ADR-011 / hotfix-repro-mandatory):** por cada bug, test RED que reproduce el fallo
  ANTES del fix; luego GREEN. Bug #2 + #4 + #7 se reproducen LIVE en dev-app antes de tocar código.
- **Bug #1:** un solo SSoT `DEFAULT_LANDING_SUBPATH = "mateo/agenda"` en `src/lib/shell-routes.ts`;
  los 3 redirects lo consumen (no string literal repetido). `redirect()` server-side (no client).
- **Bug #2:** `useStoreHydration(useTenantStore)` dentro del chunk `ssr:false`, con TODOS los hooks
  antes de cualquier branch (invariante D3, ADR-vitalia-006). No romper hook-count.
- **Bug #4:** cambio mínimo `overflow-hidden → overflow-y-auto` en `AppPanelSlot.tsx:61`. Mantener
  `flex-1 min-h-0`. No agregar `h-screen` ni alturas fijas nuevas.
- **Bug #7:** `error.tsx` DEBE ser `"use client"` (requisito Next.js) + `default export` (requisito
  Next.js, excepción a FSD no-default). Portar patrón de `mateo/agenda/error.tsx` (Alert destructive +
  RotateCcw + `reset()` + `console.error` NO-PHI). Fallback ocupa el panel (`flex flex-1`), NO toda la pantalla.
- **Tailwind tokens semánticos** (no hex). Spanish neutro LatAm en todo texto user-facing.
- **Soft-delete de componente (Bug #5):** eliminar archivo + exports + render en el MISMO commit (knip verde).

## Patterns forbidden

- ❌ String literal `"valeria/agenda"` o `"mateo/agenda"` repetido en redirects (usar el const SSoT).
- ❌ `useStoreHydration` dentro de un branch / después de un early-return (rompe D3 hook-count).
- ❌ Tocar `components/ui/*` (Shadcn primitives) o `features/lisa/components/staff/*` (lisa-doctores).
- ❌ `vitest -u` / `--update-snapshots` mecánico para los tests de Bug #1/#3 (revisar diff a mano).
- ❌ Eliminar headings de sección intra-contenido (form sections) creyendo que son el título-eco.
- ❌ Construir el editor de landing (Bug #5 solo ELIMINA el banner).
- ❌ Arreglar el h1 "Staff" de lisa/staff inline (es lisa-doctores → impl-log non-egoísmo).
- ❌ Declarar "verificado" por GET 200 / e2e mockeado (DoD #37: ejercer acción real + leer logs).

## Files in scope (builder edita SOLO estos — bajo vitalia/frontend/)

```
# Bug #1
src/app/page.tsx
src/app/[tenantId]/(shell-organism)/page.tsx
src/app/[tenantId]/(shell-organism)/layout.tsx
src/lib/shell-routes.ts                         (+ DEFAULT_LANDING_SUBPATH)
src/app/[tenantId]/(shell-organism)/not-found.test.tsx   (coverage_update)
src/components/shared/shell-organism/SubSubTabsBar.test.tsx (coverage_update)
# Bug #2 (TBD según repro)
src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx
src/components/shared/shell-organism/TenantSwitcher.tsx
src/hooks/useTenants.ts
src/stores/tenant-store.ts
# Bug #3
src/components/shared/shell-organism/SubTabContent.tsx
src/components/shared/shell-organism/SubTabHeader.tsx        (delete si queda huérfano + test)
src/features/lisa/components/marca/identidad/IdentidadView.tsx
src/features/lisa/components/marca/voz-y-tono/VozTonoView.tsx
src/features/lisa/components/marca/presencia/PresenciaView.tsx
src/features/lisa/components/placeholders/ServiciosPlaceholder.tsx   (doble-título)
src/features/config/components/placeholders/ConexionesPlaceholder.tsx (doble-título)
# Bug #4
src/components/shared/shell-organism/AppPanelSlot.tsx
# Bug #5
src/features/lisa/components/marca/presencia/PresenciaView.tsx
src/features/lisa/components/marca/presencia/index.ts
src/features/lisa/components/marca/presencia/InfoBannerLandingDescoped.tsx   (DELETE)
# Bug #7
src/app/[tenantId]/(shell-organism)/[agent]/error.tsx   (CREATE)
+ e2e/regression/shell-nav-scroll/** (specs nuevos, import desde e2e/fixtures/base.ts)
```

## Files NEVER touched (escalate)

- `core/luana-core-*/**` · `{nicolify,comunify,lupulo}/**` · backend de vitalia
- `vitalia/frontend/src/components/ui/**` (Shadcn) · `src/app/layout.tsx` (shell raíz)
- `vitalia/frontend/src/features/lisa/components/staff/**` (lisa-doctores developing)
- `.claude/**`

## must_load_skills (builder carga + reporta "Skills consulted" en T-{n}-result.md)

required:
  - id: vitalia-design-system
    when: "toda superficie FE shell — SSoT shell-organism + tokens + agentes"
  - id: frontend-expert
    when: "surface=FE — FSD-Lite, Shadcn reuse, tailwind tokens"
  - id: chrome-devtools-verify
    when: "live-verify dev-app (Bug #2/#4/#7 repro + DoD #37 evidence)"
  - id: playwright-expert
    when: "e2e runtime_error_gate + base.ts fixture + Clerk auth"
  - id: ".claude/rules/definition-of-done-live-verify.md"
    purpose: "DoD #37 — ejercer acción real, no GET 200"
  - id: ".claude/rules/hotfix-repro-mandatory.md"
    purpose: "ADR-011 repro-first por bug"
  - id: ".claude/rules/frontend-fsd.md + frontend-visual-fidelity.md"
    purpose: "boundaries + scope discipline (D3 no-egoísmo)"
  - id: ".claude/rules/spanish-text.md"
    purpose: "neutro LatAm en error boundary + fallbacks"
  - id: ".claude/rules/tenant-isolation.md"
    purpose: "Bug #2 — tenant_id de useTenantId() NUNCA Clerk org"

reference_artifacts:
  - "vitalia/docs/product/stories/vitalia-bugfix-shell-nav-scroll-errors/03-arch.md (mapa causa raíz por bug)"
  - "vitalia/docs/product/stories/vitalia-bugfix-shell-nav-scroll-errors/04-validators.yaml (gates + business_rules + visual scope)"
  - "vitalia/docs/product/stories/vitalia-bugfix-shell-nav-scroll-errors/checkpoint.md (spec-lite + repro evidence Chris)"
