---
story_id: vitalia-shell-core-hardening
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale   # § Architecture Decisions documenta divergencias (N3 consume @luana/ui-kit en vez de cablear EntitySubNavBar a mano; chrome state-machine cita ADR-vitalia-006)
verification_nature: funcional
demo_required: true
architect_run_on: 2026-06-10
surfaces: [FE]                                # FE-only confirmado (ver § 0 — el "+" de Valeria es UI-local; no toca BE)
core_lift_touch: true                          # toca core/@luana/ui-kit (proposals accepted 256517a3 + 2026-06-01-lift-shell-organism) — excepción documentada
---

# Contract: vitalia-shell-core-hardening (consolidado)

> **Umbrella de hardening del chrome del shell-organism.** Consolida responsive (backbone firmado) + race-fix + B1 soft-nav + dark token-audit + N3 → `@luana/ui-kit`. Behavior-fi HARD: el mockup `shell-valeria-states.html` es comportamiento; el ESTILO sale del design system vigente (canon + tokens). Regresión visual cero en lo shipped, ambos temas.
>
> **Insumos:** `01-spec.md` (umbrella, manda en conflicto) + `vitalia-bugfix-shell-valeria-responsive/01-spec.md` (backbone v3, 2 firmas — SC-1..19, RN-1..13, AC-1..11 verbatim). Detalle FE en `03-arch-fe.md`.

## 0. Context Summary

- **Story ID:** vitalia-shell-core-hardening · Release F3 · programa `design-system-homologation` (ADR-014, owner /pm-luana).
- **Architect run on:** 2026-06-10
- **Modules touched:** `shell` (owner), `clinics` (lisa/staff N3 migración), `crm` (adrian/embudo N3 migración). Bucket locks `code:{shell,clinics,crm}` al build.
- **Surface → builder → auditor mapping** (/dev-team spawn):

  | Surface | Builder | Auditor |
  |---|---|---|
  | `vitalia/frontend/src/**` (shell wrapper, store, globals.css, features migración) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
  | `core/@luana/ui-kit/src/**` (additivo: solo si falta una pieza del chrome lift — ver Decisión B; default = CONSUMIR lo ya shipped) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/proxy.ts` (edge-redirect, Decisión A) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

  **No hay surface BE.** **No hay surface AGENTIC** (R23 no aplica — el chat de Valeria se toca como chrome/layout, no comportamiento del agente).

- **Skills consultados:**
  - `frontend-expert` — FSD-Lite, Server-First, store SSR-safe, live-verify gate. Decisión: el shell vive en `components/shared/shell-organism/`; el N3 se consume de `@luana/ui-kit` (no se reinventa).
  - `vitalia-design-system` (must_load en cada ticket FE) — SHELL-DESIGN-CONTRACT + tokens `globals.css` + agent-colors. Decisión: behavior-fi; estilo del canon; avatar Valeria = asset del catálogo.
  - `copilot-expert` / `sales-agent-expert` / `brand-expert` / `offer-expert` / `metrics-expert` — **consultados y descartados**: ninguna superficie agentic ni de dominio se toca. El "+" nueva-conversación de Valeria es estado UI-local del chat shell (store), NO un turn del copilot ni persistencia BE. Confirmado leyendo `ValeriaChat.tsx` (mock store) + spec RN-13 ("archiva al historial" = lista UI-local). Si el build descubre que "+" debe persistir conversaciones reales → STOP, escalate /pm-vitalia (scope nuevo, surface agentic/BE).
- **CONTEXT-BRIEF source:** ausente (no se generó brief para esta umbrella) → self-ran reads + greps (Path B). R24 brief gate N/A.
- **capability YAML afectadas:** ninguna (`cap_target: null`, `cap_change_type: fix` — chrome transversal sin cap user-visible). NO se crea cap. El lift a `@luana/ui-kit` es cap-work de /pm-luana (core), fuera de esta story. `SHELL-DESIGN-CONTRACT.md` SÍ se actualiza (sección N3 + dark) como parte de la story.
- **Architecture gates que deben seguir verdes** (NATIVE host):
  - `vitalia/frontend` → `npx tsc --noEmit` · `npx eslint src/ --cache` · `npx vitest run`
  - `vitalia/frontend/src/__tests__/architecture/` (FSD boundaries, no-cross-brand-shell-mirror, no-arbitrary-values si activo, no-clerk-organizations)
  - `core/@luana/ui-kit` → `pnpm --filter @luana/ui-kit typecheck && pnpm --filter @luana/ui-kit test` (SOLO si se toca ui-kit)
  - e2e shell suite `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/` + nuevos specs dark/soft-nav/race.

## Prior art audit (anti-duplication-refining · Step prior-art-scan)

### Source of evidence
- [x] Self-run reads/greps (Path B — no CONTEXT-BRIEF)
- [x] Spec § Prior art applied (backbone + umbrella) ratificado
- [x] checkpoint `prior_art_scan` block (engine ui-kit existe, nicolify mirror, learnings)

### Hallazgo CRÍTICO que reencuadra el lift (Decisión B)
`core/@luana/ui-kit` **v0.3.0 YA SHIPPED** (`core-ds-foundation`) las piezas del N3 + layout-primitives + archetypes:
- `EntityWorkspaceLayout` (lift de nicolify, full-bleed N3, skeleton store-free G2) — `core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx`
- `EntitySubNavBar` (canon: root-pill peer leaf + placeholder + onAddAffordance) — `core/@luana/ui-kit/src/EntitySubNavBar.tsx`
- `EntityInfoCard`, `EntityPicker`, page-primitives (PageContainer/PageHeader/Section/Toolbar/EmptyState/ErrorState/skeletons/Pagination/DetailLayout/FormLayout), archetypes.

`vitalia/frontend` ya tiene `@luana/ui-kit: workspace:*` en `package.json` y lo consume en 13 archivos (showcase). **El N3 NO se porta de nicolify — ya vive en core; se MIGRAN los consumers vitalia (`lisa/staff`, `adrian/embudo`) a importar de `@luana/ui-kit`** y se RETIRA la copia brand-local `vitalia/.../shell-organism/EntitySubNavBar.tsx`.

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| N3 list/detail canónico | `core/@luana/ui-kit` (`EntityWorkspaceLayout` + `EntitySubNavBar`) | active v0.3.0 | **CONSUMIR** (migrar consumers vitalia) |
| N3 brand-local (copia) | `vitalia/.../shell-organism/EntitySubNavBar.tsx` | active (legacy, signatura vieja) | **RETIRAR** tras migrar (mata mirror) |
| Shell-store SSR-safe | `vitalia/.../stores/shell-store.ts` (`createSsrSafePersistedStore`) | active | **EXTEND** (refactor máquina de estados, ADR-vitalia-006) |
| Store SSR-safe factory | `@luana/hooks/create-ssr-safe-persisted-store` | active | **CONSUMIR** (no recrear) |
| Shell chrome (TopBar/Ribbon/ValeriaSidebar/...) | `vitalia/.../shell-organism/` | active (origen del lift accepted) | **MODIFICAR brand** + handoff lift /pm-luana (NO ejecutar el lift de chrome acá — Decisión B) |
| Dark tokens `--vitalia-*` | `vitalia/.../globals.css` | active (tienen variante dark) | **EXTEND** (gaps puntuales, no wholesale) |
| Edge-redirect proxy | `vitalia/frontend/src/proxy.ts` | active (bare-tenant redirect ya existe) | **EXTEND** (Decisión A) |
| Cross-brand mirror (nicolify shell) | `nicolify/.../shell-organism/` | active | **NO TOCAR** (otra brand; converge vía /pm-luana post-merge) |

### Decisión por sistema → ver § Architecture Decisions (A/B/C). EXTEND/CONSUMIR > NEW en todos los casos. **Net-new** justificado: solo la tira-avatar estado A (afford. reapertura RN-12) + edge-redirect path (si no cubre el caso) + máquina de estados limpia (RN-5/6/7/13) — net-new para ambas marcas, candidato lift.

## Architecture Decisions

> Las 3 decisiones que Chris delegó (A soft-nav · B lift sequencing · C dark token-audit), cerradas con código real + tradeoffs.

### Decisión A — Mecanismo soft-nav confiable (RN-14 / B1)

**Root cause (confirmado en código):** `ShellOrganismLayout.tsx` envuelve `ShellOrganismLayoutClient` en `dynamic(..., { ssr:false })` porque `react-resizable-panels v4.11.1` usa `storage: n = localStorage` como **default param bare-name** que crashea el SSR pass de Next (ReferenceError, no fixeable desde el caller — evalúa antes de cualquier `typeof` guard). El `ssr:false` es **necesario** y NO se elimina. El learning `2026-06-03-next16-softnav-redirect-rendered-more-hooks` documenta que **soft-nav intra-route-group hacia un layout `ssr:false`** dispara "Rendered more hooks" en el Router interno de Next 16.2.3 (flaky ~40%; nav dura no lo trippea).

**Opciones evaluadas:**
1. Eliminar `ssr:false` del shell → **DESCARTADA**: re-introduce el crash SSR de react-resizable-panels v4 (causa documentada del `ssr:false`). Romper para arreglar.
2. **Edge-redirect en `proxy.ts` (307) + revertir band-aid hard-nav del chip → soft-nav → ELEGIDA.** El 307 hace que el browser pida la ruta destino con fetch fresco → Router monta limpio → sin soft-nav intra-group para el caso landing. Para los soft-navs internos (board→recuperar, ribbon/subtabs) el invariante se cumple porque el chip vuelve a `next/link` y el flake se mitiga con el redirect de landing + el Router fresco. El proxy ya existe (`bareTenantLandingRedirect`) — se EXTIENDE.
3. Subir versión de Next si hay fix upstream → **investigar (no bloqueante)**: ver § Research Notes (verificar Next 16.x release notes por fix de "Rendered more hooks" en Router; si existe en una versión consumible sin breaking, preferirla — pero NO bumpear Next dentro de esta story sin gate de regresión completo. Default = opción 2).

**Tradeoff aceptado:** edge-redirect es **workaround del trigger, no fix del framework** (lo dice el learning). Soft-navs profundas entre sub-tabs pesadas podrían reaparecer; por eso el invariante RN-14 se verifica con **SC-21 loop ×15 real** (no asunción). Si reaparece: misma firma de stack → re-evaluar bump de Next.

**Deliverables A:** (a) `proxy.ts` matcher acotado UUID-only para landing 307 (ya existe — verificar/extender que cubra board→recuperar si aplica); (b) **revertir el band-aid hard-nav** del chip `frozen-kpi-badge` (`features/adrian/components/embudo/EmbudoMetrics.tsx` líneas 78-87) de `<a href>` a `next/link` soft-nav; (c) SC-21 e2e real (loop ×15, base.ts anti-burbuja).

### Decisión B — Sequencing lift a `core/@luana/ui-kit` (lift-durante, acotado)

**Hecho que reencuadra:** el N3 + layout-primitives + archetypes **YA están en `@luana/ui-kit` v0.3.0** (`core-ds-foundation`, accepted). El "lift" del N3 NO está pendiente — está hecho en core. La proposal `2026-06-01-lift-shell-organism-to-core` (accepted 2026-06-06, gated tras estas stories) cubre el **chrome del shell** (ShellOrganismLayout/Ribbon/SubTabsBar/ValeriaSidebar/routing helpers) — eso es **1-2 semanas de /dev-team** (estimado en la propia proposal) y NO se ejecuta en esta umbrella.

**Qué aterriza dónde:**

| Pieza | Hogar | Acción en esta story |
|---|---|---|
| N3 list/detail (`EntityWorkspaceLayout`, `EntitySubNavBar`, `EntityInfoCard`) | `@luana/ui-kit` (YA shipped) | **CONSUMIR** — migrar `lisa/staff` + `adrian/embudo` a importar de `@luana/ui-kit`; retirar `vitalia/.../EntitySubNavBar.tsx` (mata mirror). Excepción engine documentada: proposals accepted 256517a3. |
| Chrome del shell (ShellOrganismLayout/Ribbon/ValeriaSidebar/etc.) | brand `vitalia/.../shell-organism/` (hoy) → `@luana/ui-kit` (futuro) | **MODIFICAR brand** (responsive + máquina estados + tira-avatar + "+"). **NO liftear el chrome acá.** Emitir **handoff proposal a /pm-luana** documentando que el chrome brand quedó "excelente" + listo para el lift de 1-2 sem (su outcome platform). |
| Tokens vitalia (`--vitalia-*`, agent-colors) | brand `globals.css` | **brand-specific — NO liftear** (cada marca su theme; el lift de tokens es ADR-014 Fase 1, otra story). |
| Avatar Valeria, agent-colors | brand assets | **brand-specific — NO liftear.** |

**Criterio:** lo brand-agnostic que YA está en core → consumir; lo brand-specific → queda brand. El chrome del shell es lift-candidate pero su ejecución es un esfuerzo dedicado de /pm-luana (no se infla esta story). **Si el build descubre que migrar el N3 a `@luana/ui-kit` requiere AGREGAR una pieza faltante al kit** (ej. un helper de leaves dinámicos no shipped): edit **additivo** a `@luana/ui-kit` permitido (proposal accepted), pero NO refactor del chrome. Cualquier edit a ui-kit que NO sea additivo-mínimo → STOP, escalate /pm-luana.

**Tradeoff:** dejamos 2 sistemas N3 coexistiendo brevemente (brand-local hasta migrar + core). Se resuelve retirando el brand-local en el MISMO ticket de migración (AC-9). Cross-brand: nicolify converge DESPUÉS (su propia story /pm-luana — NO se toca nicolify acá).

### Decisión C — Dark token-audit (RN-15 / BUG #2) — estrategia que REDUCE deuda

**Hecho que reencuadra:** los tokens core `--vitalia-{bg,surface,surface-alt,muted,text,text-muted,text-faint,border,border-soft,success-soft-bg,danger-soft-bg}` **YA tienen override `[data-theme="dark"]`** (globals.css líneas 248-272). Los `vt-*` utilities que referencian esos tokens **YA son dark-aware** por indirección. **BUG #2 NO es "vt-* sin dark wholesale"** — es:
1. **Colores hardcodeados en componentes de feature** (ej. inbox `ContactSidebar` blanco `rgb(255,255,255)`, cards) que NO usan token → se quedan claros.
2. **Posibles `--vitalia-*-soft` derivados** sin variante dark (auditar: warning-soft, info-soft, agent-*-soft que falten).

**Estrategia (reduce deuda — no agrega sistemas paralelos):**
1. **Auditar SHIPPED-only** (spec § Open questions ratificado): lisa/marca, adrian/inbox, adrian/embudo, lisa/staff, mateo/agenda + el wrapper. Placeholders fuera (se corrigen al construirse).
2. **Patrón preferido: migrar el color hardcodeado al token semántico** (ej. `bg-card`/`bg-background`/`vt-bg-surface`) que YA tiene dark — NO crear una variante `[data-theme=dark]` nueva por cada `vt-*`. Esto **reduce** el sistema paralelo (la nota de duplicación `--radius` + sistema `--vitalia-*` legacy del ds-showcase apunta a esto).
3. **Completar variante dark SOLO** para los `--vitalia-*-soft`/derivados que realmente falten (grep + medición computed live).
4. **AC-12 grep gate:** "clases `vt-*` usadas en superficies user-facing sin variante dark = 0" se reinterpreta como: cero color **hardcodeado** (hex/`rgb()`/`bg-white`/`bg-[#...]`) en superficies shipped + cero token sin dark. El gate mecánico (arch-test no-arbitrary/no-hardcoded-color si existe) + medición computed por sub-tab (SC-20) lo enforce.

**Tradeoff:** NO migramos los 368 arbitrary-values de ADR-014 (eso es la story platform de homologación). Scope acotado a **dark consistency en superficies shipped** — el barrido completo arbitrary→token es ADR-014 Fase 0/2.

## Integration design (CONN — anti-orphan)

Esta story es **hardening de chrome existente** — no nace funcionalidad isla. Las 4 contenciones:

- **Consumed:** todo el chrome (topbar/Valeria/N3) ya tiene consumidores reales (todas las sub-tabs de agente lo montan vía `(shell-organism)/layout.tsx`). El N3 migrado lo consumen `lisa/staff` + `adrian/embudo` (rutas live). El edge-redirect lo consume todo bare-tenant landing.
- **On the map:** zona Infraestructura → caja `plataforma-tecnica` (`map_zone: infraestructura`, chrome no-funcional). `cap_target: null` correcto (chrome transversal sin cap). El N3 habilita superficies de agente (staff=Lisa caja Agentes, embudo=Adrián caja Agentes) pero el patrón vive en el shell.
- **Navigable/reachable:** sin ruta nueva. Reachability = el shell ya es el wrapper de TODAS las rutas `(shell-organism)/**`. El N3 migrado: master `[agent]/[subtab]/page.tsx` → detalle `[agent]/[subtab]/[entityId]/[leaf]`. Tira-avatar estado A reabre Valeria (afford. visible). "+" en cabecera Valeria.
- **Notarized/registered:** el N3 se registra al importar `EntityWorkspaceLayout` de `@luana/ui-kit` en los `[entityId]/layout.tsx` de staff/embudo (no se cablea a mano — AC-9). El edge-redirect en `proxy.ts` (matcher). El chrome ya está en el route group layout. Cero `include_router` nuevo (FE-only).

**Reachability path concreto:** usuario → `/{tenantId}` → (proxy 307) → `/{tenantId}/{DEFAULT_LANDING_SUBPATH}` → shell monta (ssr:false client) → ribbon/subtabs/Valeria → click sub-tab list/detail (staff) → `[agent]/staff/page.tsx` (grid EntityInfoCard) → click doctor → `[agent]/staff/[doctor-id]/[leaf]` (EntityWorkspaceLayout de @luana/ui-kit) → leaf content.

## 1-7. Domain Entities / Models / DTOs / API / TS types / Repos / Services

**N/A — FE-only.** No hay entidades, modelos SQLAlchemy, DTOs Pydantic, rutas FastAPI, repos ni services nuevos. El estado del shell es UI-local (Zustand SSR-safe, localStorage). El "+" nueva-conversación es estado del chat shell (mock store hoy), NO persistencia BE.

**Guard:** si el build determina que "+" o el historial deben persistir conversaciones reales (surface BE/agentic) → **STOP, escalate /pm-vitalia** (scope nuevo fuera del chrome). El spec RN-13 define "+" como UI-local (archiva a la lista del historial), coherente con `ValeriaChat.tsx` mock actual.

## 8. Agentic Surfaces

**N/A.** Ninguna superficie `copilot`/`sales_agent` se toca. R23 no aplica. El chat de Valeria se toca como chrome/layout (posición, máquina de estados, "+", tira-avatar), NUNCA comportamiento del agente (prompts, tools, state graph, goldens, voz).

## 9. Migration Notes

**N/A — sin migración DB.** Cambio de `localStorage` key shape: el `shell-store` refactor (máquina de estados nueva) puede cambiar el shape persistido. **Backward-compat obligatorio:** el factory `createSsrSafePersistedStore` + un `migrate`/fallback debe tolerar estados viejos (`valeriaState: 'collapsed'|'rail'|'full'` → modelo nuevo `closed|chat` + `historyOpen`) sin crash (SC-18 adversarial cubre estado inválido → fallback). Documentar el mapping legacy→nuevo en el ticket del store.

## 9.5 Tests audit (default flip)

- [x] **No aplica** — esta story NO flipea ningún feature flag side-effect (`USE_*_PATTERN_*`, `USE_DEEPAGENTS_*`, `ENABLE_*`, `LITELLM_PROXY_*`). El cambio es FE chrome (estado UI-local + tokens + routing edge). El refactor del `shell-store` cambia defaults de UI (`valeriaState`) pero NO es un flag side-effect (no toca events/persistence-BE/observability/LLM routing). El no-clobber SSR (RN-11) está cubierto por SC-18 + el factory ADR-vitalia-006.

## 10. File Structure

Detalle completo en `03-arch-fe.md § File map`. Resumen (NEW / MODIFIED / RETIRE):

```
vitalia/frontend/src/
├── stores/shell-store.ts                                   MODIFY  (máquina estados: closed|chat + historyOpen; quitar shellMode/rail; migrate legacy)
├── app/globals.css                                         MODIFY  (dark gaps: hardcoded→token; --vitalia-*-soft faltantes)
├── app/[tenantId]/(shell-organism)/layout.tsx              KEEP    (server; redirect ya vía DEFAULT_LANDING_SUBPATH)
├── proxy.ts                                                MODIFY  (edge-redirect landing 307 — verificar/extender matcher; Decisión A)
├── components/shared/shell-organism/
│   ├── TopBarGlobal.tsx                                    MODIFY  (TenantSwitcher al extremo derecho; sin chip)
│   ├── ShellModeToggle.tsx                                 RETIRE  (AC-1: sin modo web; grep shellMode=0)
│   ├── ShellOrganismLayoutClient.tsx                       MODIFY  (máquina estados nueva; clamp 320; drawer <1024; historial empuja 260; quitar ShellModeToggle/web grid)
│   ├── ValeriaSidebar.tsx / ValeriaChat.tsx / ChatHeader.tsx  MODIFY  (cabecera: colapsar propio + "+" + historial; push)
│   ├── ValeriaRail.tsx                                     RETIRE/TRANSFORM  (rail 60px se va; tira-avatar estado A)
│   ├── ValeriaHistory.tsx                                  MODIFY  (260px fijo, empuja; "+" archiva)
│   ├── ValeriaCollapsedStrip.tsx (o equivalente)          NEW     (tira 44px + avatar Valeria; RN-12)
│   ├── useViewportGuard.ts                                 MODIFY  (clamp 320; sin 620; umbral drawer 1024; container-aware si Decisión BUG#1-c)
│   └── EntitySubNavBar.tsx                                 RETIRE  (migrar consumers a @luana/ui-kit; mata mirror)
├── features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx  MODIFY  (consume EntityWorkspaceLayout de @luana/ui-kit)
├── features/adrian/components/embudo/EmbudoMetrics.tsx     MODIFY  (revertir band-aid hard-nav → next/link; Decisión A)
└── app/[tenantId]/(shell-organism)/{lisa/staff,adrian/embudo}/[entityId]/layout.tsx  MODIFY  (montar EntityWorkspaceLayout de @luana/ui-kit)

core/@luana/ui-kit/src/                                     CONSUME (default). EDIT solo additivo-mínimo si falta pieza N3 (Decisión B; proposal accepted)

vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts  MODIFY (reactivar test omitido, adaptado a máquina nueva — AC-14)
vitalia/frontend/e2e/regression/shell-core-hardening/*.spec.ts  NEW (SC-20 dark · SC-21 soft-nav · SC-22 race · regression cross-tab)
```

## 11. Cross-Cutting Concerns

- **Tenant isolation:** N/A en chrome (sin queries). El shell layout server ya valida tenant (Clerk + fetchUserTenants). `tenant_id` del FE vía `useTenantId()` — NUNCA Clerk org (arch-test `test-no-clerk-organizations`). El N3 `[entityId]` es UUID, NUNCA PHI en URL.
- **Currency:** N/A (chrome sin montos).
- **Master data:** N/A (sin fechas/locale nuevos en chrome).
- **Spanish neutro LatAm:** microcopy del chrome neutro sin voseo ("Nueva conversación", "Historial", "Abrir a Valeria", "Colapsar") — heredado verbatim del backbone § Microcopy.
- **PII / HIPAA-lite:** chrome no toca PHI. Audit-log del shell server ya loguea solo userId opaque (sin PHI). No se introduce PHI en localStorage (shell-store es no-phi-scope).
- **Native-first:** todo lint/tsc/vitest/playwright corre NATIVE host (`cd vitalia/frontend && npx ...`). NUNCA `docker exec`. ui-kit: `pnpm --filter @luana/ui-kit ...` native.
- **Engine boundary:** `core/@luana/ui-kit` es editable en esta story SOLO por excepción documentada (proposals accepted 256517a3 + 2026-06-01-lift-shell-organism). Edits additivos-mínimos. `core/luana-core-*/src/` (Python engine) NO se toca. Cualquier edit no-additivo a ui-kit → STOP /pm-luana.
- **Cross-brand:** `nicolify/` NO se toca (read-only fuente histórica del N3 ya en core). Convergencia post-merge vía /pm-luana.
- **Dark mode:** wiring next-themes + `[data-theme="dark"]` + tailwind darkMode SE CONSERVA (correcto). Solo se completan variantes/se migran hardcoded.

## 12. Architecture Fitness Impact

Gates que corren contra el cambio (NATIVE):
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` — el mirror sancionado (allowlist ratchet) puede **encoger** al retirar `EntitySubNavBar` brand-local (shrink-only OK). Verificar que no rompa al migrar consumers.
- `test-no-clerk-organizations.test.ts` — debe seguir verde (shell no introduce org).
- FSD boundaries (`boundaries/dependencies`) — migrar a `@luana/ui-kit` es import permitido (lib/shared cross-brand vía `@luana/*`).
- no-arbitrary-values / no-hardcoded-color (si activos por ADR-014) — el dark token-audit los hace ENCOGER (migra hardcoded→token).
- `core/@luana/ui-kit/tests/` — si se toca el kit, su suite verde + downstream vitalia (R3 auditor-downstream).

**Allowlist plan:** shrink-only. Retirar `EntitySubNavBar` brand-local reduce el set de símbolos del shell mirror sancionado. NO crecer ningún allowlist sin justificación en commit.

## 13. capability YAML + modules/{m}.md updates

- Ninguna cap YAML (`cap_target: null`, fix de chrome).
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` → actualizar § N3 (consume `@luana/ui-kit`, retira brand-local) + § dark (estrategia hardcoded→token) + § Valeria states (máquina nueva closed|chat + historyOpen + tira-avatar + "+"). Actualización es parte de la story (Fase E /pm-vitalia o el builder en el ticket de docs).
- Handoff proposal a /pm-luana: el chrome brand quedó listo para el lift de `2026-06-01-lift-shell-organism-to-core` (outcome platform, 1-2 sem).

## 14. Test Surfaces (TDD-mandatory · RED first)

Detalle en `04-validators.yaml § test_construction_plan`. Resumen por capa:
- **Vitest unit/component** (RED first): shell-store máquina nueva (transiciones A/B/C, migrate legacy, no-clobber) · ValeriaCollapsedStrip · ValeriaHistory empuja 260 · TopBarGlobal orden cluster derecho · useViewportGuard clamp/drawer.
- **Playwright funcional/regression** (real-backend donde aplique, base.ts anti-burbuja):
  - SC-1..19 backbone (default 30/70, sin chip, switcher derecha, splitter persiste, colapsar/tira-avatar/reabrir, historial empuja, "+", clamp 320, drawer, N3, a11y, i18n, adversarial, regression cross-tab AMBOS temas).
  - SC-20 dark per-subtab (computed colors oscuros, sin mitad clara, axe contraste dark).
  - SC-21 soft-nav loop ×15 + board→recuperar (montaje + consola limpia + chip = next/link).
  - SC-22 race drag inmediato post-hidratación (clamps + persistencia íntegra) — **reactiva el test omitido** de `resize-and-state.spec.ts`.
- **axe wcag2aa** en AMBOS temas.
- **NO BE tests** (sin surface BE).

## 15. Research Notes (date-aware — accessed 2026-06-10)

- **Next.js "Rendered more hooks" en Router con `ssr:false` + soft-nav intra-group** — fuente primaria: learning interno `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` (caso vitalia, Next 16.2.3). Knowledge cutoff Opus 4.8 = Jan 2026; este bug es post-cutoff y específico de la versión Next del repo → me apoyo en el learning interno + el código real, NO en memoria del modelo. **Acción de verificación delegada al builder:** chequear release notes de la versión Next instalada en `vitalia/frontend/package.json` por un fix upstream de "Rendered more hooks" en el client Router (WebSearch `"Next.js Router Rendered more hooks fix {current_year}"` + canonical `https://nextjs.org/docs`); si existe fix consumible sin breaking, preferirlo a más edge-redirects — pero NO bumpear Next dentro de esta story sin gate de regresión completo. Default = edge-redirect (opción 2, Decisión A).
- **react-resizable-panels v4 bare-name `localStorage` default param crash en SSR** — confirmado en código (`ShellOrganismLayoutClient.tsx` doc-comment + `ShellOrganismLayout.tsx`). Es la causa documentada del `ssr:false`. No se elimina.
- **Zustand 5 `skipHydration` + `_hasHydrated` + setItem NO-OP pre-hydration** — ADR-vitalia-006 (validado WebSearch 2026-05-29, estado del arte vigente). Patrón SSoT del store; el refactor de la máquina de estados lo CONSERVA.
- **@luana/ui-kit v0.3.0 N3 + page-primitives + archetypes** — verificado leyendo `core/@luana/ui-kit/{package.json, CHANGELOG.md, src/index.ts, src/EntityWorkspaceLayout.tsx, src/EntitySubNavBar.tsx}` (2026-06-10). El N3 lift está HECHO en core (`core-ds-foundation`) — reencuadra Decisión B.

## 16. Open Questions for PM

1. **autonomous_mode + engine-touch:** el spec ratifica `autonomous_mode: true` (Chris verbatim 2026-06-10). La rule `autonomous-mode.md` marca HARD-false "story toca engine/cross-brand". **Resolución del architect:** los proposals del lift están **accepted** (256517a3 + 2026-06-01) y Chris ratificó autonomous CON conocimiento de que es el vehículo del lift → la intención del gate (engine edit necesita aprobación) está satisfecha. **MANTENGO autonomous_mode: true** PERO acoto los edits a `@luana/ui-kit` a "additivo-mínimo o cero" (Decisión B: default = consumir lo ya shipped). Ver dispatch-plan.md § autonomous_mode para el caveat + el pause-point recomendado. Si /pm-vitalia/Chris discrepa → bajar a false es trivial (1 línea checkpoint).
2. **BUG #1 responsive (squeeze)** — el observed-bug ofrece 4 opciones (a subir threshold / b Valeria más angosta / c container-aware / d inbox auto-colapsa). El backbone resuelve la dimensión "Valeria exprime" con default `chat 30/70` + clamp 320 + drawer <1024 + colapsar propio. **¿Confirma /pm-vitalia que el default 30/70 + clamp + colapsar es suficiente (resuelve U3 + BUG#1) sin necesitar container-aware (opción c)?** El spec lo da por resuelto (matriz: U3 → SC-1/SC-4); lo dejo así salvo que el live-verify a 1280/1366/1440 muestre squeeze residual → entonces aplicar (d) inbox-local (bajo riesgo, no toca shell).
3. **Embudo `defer_audit: true`** — el embudo N3 se migra acá (rebase chrome crm). El embudo está `developed` + `defer_audit: true` (ratificado). **Confirmar:** tras esta story, /auditor audita embudo (post-hardening) sin re-litigar su scope ratificado. El build NO debe romper el board/writes live-verified del embudo (AC-10 regression).
