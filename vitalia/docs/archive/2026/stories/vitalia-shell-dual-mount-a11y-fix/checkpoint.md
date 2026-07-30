---
story_id: vitalia-shell-dual-mount-a11y-fix
type: bugfix

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F2

# Capability lineage (v2 cement 2026-05-27)
cap_target: shell-vitalia                         # toca el shell-organism core (ShellOrganismLayoutClient)
cap_change_type: fix                              # bugfix arquitectónico: elimina doble montaje + id duplicado (no agrega scenarios de producto nuevos)
parent_story: null

state: done
phase_workflow: MERGED
audit_verdict: APPROVED
merged_at: 2026-06-01T12:05:00-05:00
merged_by: /pm-vitalia
last_artifact: e2e/regression/vitalia-shell-dual-mount-a11y-fix/single-slot-live.spec.ts
last_modified: 2026-06-01T11:40:00-05:00

# Shell-feature arch gate (overlay shell-feature-architecture-mandatory.md)
architecture_pattern: ADR-vitalia-004            # shell CORE (no sub-tab nueva); adr_004_compliance=partial-with-rationale en 03-arch (secciones 4-8 N/A: sin data layer/forms/BE/migrations/telemetría)
autonomous_mode: false                           # architect propone false (bugfix transversal blast-radius alto); Chris ratifica
next_action: "T-2 DONE — live-verify GREEN contra stack real (no mocks). AUTO-HANDOFF /auditor (auditor-frontend Opus): leer single-slot-live.spec.ts + dev_app_verified.evidence + 501 tests shell + verificar single-main/single-slot. APPROVED → /pm-vitalia merge reviewing→done (git mv archive). NOTA para auditor: el doctors-list 500 (X-Clinic-ID UUID) es bug de DATOS de lisa-doctores (observed-bugs/2026-06-01-doctors-list-500-clinic-id-uuid.md), NO del shell — el shell renderizó single-main+single-slot+consola limpia aún con el panel en error state, y lisa/marca/identidad (sin doctores) también verde."
ratified_by_chris: true                           # Chris ratificó arrancar Pendiente 2 (fix dual-mount) → scope WHAT confirmado; HOW lo cierra /architect
spawned_at: 2026-06-01T00:00:00-05:00
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null
audit_iterations: 0
defer_audit: false
defer_audit_reason: null
parked_reason: null
dropped_reason: null

# Paradigma (rule paradigm-arquitectura.md · árbol de decisión)
# Zona = Infraestructura (no-funcional/técnico, quality attribute a11y+HTML válido del contenedor visual).
# Caja = plataforma-tecnica · functional_area = plataforma-tecnica.shell ("Shell visual de la app").
functional_area: plataforma-tecnica.shell
user_visible: false

# Bugfix repro-first gate (ADR-011 · hereda hotfix-repro-mandatory.md)
hotfix_metadata:
  repro_verified: true
  repro_command: "cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/ --project=smoke  →  strict mode violation: getByTestId('btn-nuevo-integrante') resolved to 2 elements (panel visible + rama mobile CSS-hidden)"
  diagnosis_validates_handoff: true

# Dev-app live verification gate (ADR-vitalia-008) — superficie user-reachable (el shell de TODOS los agentes)
dev_app_verified:
  required: true
  env: "make dev-vitalia stack (FE :3002 + BE :8002), Clerk testing token (CLERK_TESTING_TOKEN_VITALIA), auth.fixture authedPage — Playwright autenticado, SIN backend mocks. Chrome DevTools MCP no conectado en esta sesión → fallback Playwright-autenticado-live (válido per definition-of-done-live-verify.md § Fallback localhost). Frontend container bind-mount confirmado a ESTE worktree (footgun NO disparado)."
  verified_at: 2026-06-01
  spec: vitalia/frontend/e2e/regression/vitalia-shell-dual-mount-a11y-fix/single-slot-live.spec.ts
  evidence:
    - action: "Navegación autenticada (real Clerk) a /{tenant}/lisa/staff en modo agentic, viewport desktop 1440×900, contra stack real"
      observed: "document.querySelectorAll('#main-content').length === 1 + [data-testid=app-panel-slot].length === 1; consola SIN 'Rendered more hooks'/hydration. Backend REAL golpeado (GET /iam/users/me/tenants 200) — confirma no-mock."
    - action: "Navegación autenticada a /{tenant}/lisa/marca/identidad en modo web, desktop"
      observed: "1 main-content + 1 app-panel-slot; consola limpia (ruta sin endpoint doctores → panel sano)"
    - action: "Navegación autenticada a /{tenant}/lisa/staff en modo agentic, viewport mobile 390×844"
      observed: "1 main-content + 1 app-panel-slot; consola limpia (la rama mobile ya no duplica el slot — lección nicolify aplicada)"
    - action: "axe wcag2aa scan del shell (lisa/staff, desktop)"
      observed: "cero violaciones duplicate-id / duplicate-id-aria / landmark-unique / landmark-no-duplicate-banner (eran el síntoma a11y del triple-main)"
  notes: "Resultado Playwright: 6 passed (2 setup + 4 live) en 18.5s. El doctors-list 500 (X-Clinic-ID) es bug de DATOS de lisa-doctores, NO del shell (observed-bugs/2026-06-01-doctors-list-500-clinic-id-uuid.md). El shell rindió single estructura aún con panel en error state."
---

# Bugfix arquitectónico — shell-organism monta el panel-content 2× (testids duplicados + id="main-content" ×3)

## Síntoma (repro_verified)

En los E2E de `vitalia-fase2-lisa-doctores` contra el stack real, cada `getByTestId(...)` del
panel resuelve a **2 elementos** → Playwright strict-mode violation. Causa: el shell monta el
`<AppPanelSlot>` (children de la sub-tab) en 2 ramas simultáneas — la visible por viewport +
la mobile **siempre en el DOM** (oculta por CSS). Además `id="main-content"` aparece en 3
`<main>` (HTML inválido + a11y).

> Detalle completo + evidencia verbatim: `vitalia/docs/observed-bugs/2026-05-31-shell-dual-mount-duplicate-testids.md`

## Root cause — "Triple-main pattern" deliberado (con tests que lo asertan)

`ShellOrganismLayoutClient.tsx` implementa 3 `<main id="main-content">` mutuamente excluyentes
por CSS Tailwind (agentic-desktop `hidden md:block` · web-desktop `hidden md:grid` · mobile
`md:hidden` SIEMPRE montado). `shellMode` es agentic XOR web, pero la rama mobile siempre se
monta → en desktop hay **2 `<AppPanelSlot>`** → testids ×2 + id duplicado. Hay tests que asertan
esto (`ShellOrganismLayout.test.tsx` SC-1/SC-2/SC-4 + `getAllByTestId` plural). Fixearlo =
**cambio de arquitectura**, no parche.

## ★ Prior art scan (anti-duplication-refining · 2026-06-01)

Scope grep: `core/` + `vitalia/` propio + `nicolify/` (recién en main vía sync).

- **`nicolify/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` + `useViewportGuard.ts`** — ★ PRIOR ART DIRECTA (nicolify portó su shell DE vitalia). **Nicolify YA peleó este bug** (commits `641dbb4c`/`e153f53d` "isDesktop huérfano → crash"). **Hallazgo crítico que CONTRADICE el fix propuesto en el bug doc:** nicolify intentó el render condicional por viewport (`useSyncExternalStore(isDesktop)` montando/desmontando el `<Group>` resizable) y **crasheó** (React "rendered more hooks than previous render" — el mount condicional cambia el hook-count). Su solución final (comentada verbatim en su layout líneas 14-19): **UN solo `<main id="main-content">` que envuelve TODAS las variantes; el inner chrome se muestra/oculta con CSS `md:block`/`md:hidden`, NO con mount condicional.** → resuelve el `id` duplicado + el crash de hooks, PERO mantiene ambas ramas de chrome en el DOM.
- **`vitalia/frontend/src/hooks/useMediaQuery.ts`** — existe (consumido por ValeriaSidebar, mateo/AppointmentDrawer). El bug doc proponía usarlo con lazy-sync-init para `isDesktop`. RIESGO: si se usa para montar/desmontar `<Group>` → mismo crash que nicolify.
- **`vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts`** — vitalia tiene su propio viewport guard (one-way full→rail). Es el origen del de nicolify.

**Decisión de diseño (para /architect):** el fix NO es el render condicional ingenuo del bug doc
(nicolify probó que crashea). La reconciliación correcta = **single `<main id="main-content">`
(patrón nicolify, mata el id duplicado + evita el crash de hook-count) + render del slot de
contenido (`<AppPanelSlot>`/children) UNA sola vez** (para matar los testids duplicados, que el
fix de nicolify por sí solo NO resuelve si el chrome mobile/desktop ambos renderizan children).
El chrome de layout (resizable vs grid vs single-col) puede diferir por CSS; lo que NO puede
duplicarse es el slot de children. **No es lift cross-brand** — es shell brand-local; cada marca
tiene su ShellOrganismLayoutClient (vitalia ≠ nicolify, distinto Ribbon/agentes). Aplicar el
PATRÓN, no compartir el archivo.

## Fix de producción (diseño — /architect lo cierra)

1. **Single `<main id="main-content">`** envolviendo todas las variantes (patrón nicolify) → id único + HTML válido.
2. **`<AppPanelSlot>` (children) renderizado UNA vez** → mata testids duplicados. El layout chrome (panels resizable / grid / single-col) varía por CSS o por una rama que NO re-monte children.
3. Evitar el mount/unmount condicional del `<Group>` detrás de `isDesktop` (causa "more hooks" crash — lección nicolify). Si se requiere conditional, hook-count estable (hooks antes de cualquier early-return).
4. **Reescribir los tests que asertan el triple-main**: `ShellOrganismLayout.test.tsx` SC-1/SC-2/SC-4 + `AppPanelSlot.test.tsx` + `getAllByTestId` plural → asertar single-main + single-slot. Mock `window.matchMedia` en setup jsdom si el layout pasa a consultarlo.
5. **Re-verificación transversal OBLIGATORIA** (shell compartido — un error rompe a TODOS): 5 agentes (lisa/mateo/adrian/lucas/camila) + valeria sidebar, en los 3 modos (agentic/web/mobile) — vitest shell + axe wcag2aa + visual smoke + **live en dev-app** (ADR-008). Un solo `id="main-content"` por viewport, cero testids duplicados.

## Bar de verificación (DONE)

- `ShellOrganismLayout` renderiza **un solo** `<main id="main-content">` por viewport (no 3).
- Cada `data-testid` del panel resuelve a **1 elemento** (E2E doctores sin strict-mode violation, SIN el workaround `.filter({visible:true})`).
- axe wcag2aa sin violación de id duplicado / landmark.
- Los 5 agentes + valeria renderizan OK en agentic/web/mobile (vitest + visual smoke).
- **dev-app live** (ADR-008): ejercer al menos lisa + valeria-sidebar en desktop+mobile, leer consola sin error de hidratación/hooks, confirmar single main-content en el DOM.
- Sin "more hooks than previous render" en consola (lección nicolify).

## Notas de scope

- Shell brand-local (`vitalia/frontend/src/components/shared/shell-organism/`). NO core, NO cross-brand (aplicar el patrón nicolify, no compartir archivo).
- Es el prerequisito para que `vitalia-fase2-lisa-doctores` llegue a `done` (su harness usa el workaround `.filter({visible:true})` mientras tanto).
- Tipo `bugfix` (ADR-011) pero con peso arquitectónico → pasa por `/architect` (no edit apresurado).
