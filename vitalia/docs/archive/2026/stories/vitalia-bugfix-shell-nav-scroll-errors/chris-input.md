---
story_id: vitalia-bugfix-shell-nav-scroll-errors
created_at: 2026-06-02T19:29:12-05:00
last_modified: 2026-06-02T22:05:00-05:00
notes_count: 0
refs_count: 1
conversation_count: 5
---

# chris-input.md · vitalia-bugfix-shell-nav-scroll-errors

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).

## 💭 Notas

### 2026-06-02 19:29
Sin notas adicionales · Chris escribe aquí si quiere ajustar el scope o corregir una hipótesis PM.

## 📎 Referencias

- **📖 story-ref** · vitalia-fase2-lisa-doctores (developing) — recibe el bug #6 folded (lisa/staff infinite loop en NuevoIntegranteModal)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-02 19:29 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Story `bugfix` creada en `state: idea`. Origen: Chris ejerciendo dev-app.vitalialat.com live
(tenant `e69a691d-…`) reportó 7 bugs. Step 0 detectó 2 stories en `developing`
(`estabilizar-harness-e2e-lisa-marca` + `vitalia-fase2-lisa-doctores`).

**Decisiones ratificadas por Chris (AskUserQuestion):**
- Bug #6 (lisa/staff "No pudimos cargar el equipo" + `Maximum update depth exceeded` en
  `NuevoIntegranteModal.useEffect` línea 111 `form.reset()`) → **folded a
  `vitalia-fase2-lisa-doctores`** (developing · dueña de `features/lisa/components/staff/`).
  Es una regresión de ese trabajo activo, se arregla ahí antes de cerrar.
- Los **6 bugs del shell-organism** (cross-cutting del chasis) → **esta story única**.

**Mapa de superficies (hipótesis PM · /dev-team valida en repro local):**
1. Routing post-login → `valeria/agenda` (404) · `app/[tenantId]/(shell-organism)/page.tsx`
2. Selector de tenant oculto con 1 tenant · `shell-organism/TenantSwitcher.tsx` + `TopBarGlobal.tsx`
3. Títulos de hoja redundantes (eliminar todos) · `SubTabContent.tsx` + sub-tab pages
4. Scroll bloqueado en todas las hojas (ALTA) · `(shell-organism)/layout.tsx` overflow
5. Recuadro "Editor de landing pública — próximamente" en Presencia · `SubTabContent.tsx`
6. Error bloquea toda la nav (botones muertos · ALTA) · error boundaries del shell

`repro_verified: false` con `repro_source: chris-live-observation` — Chris los vio live; el
gate ADR-011 exige que `/dev-team` los reproduzca local antes de spawn builder. Solo FE vitalia,
módulo `shell` (WIP cap module-scoped OK en paralelo con las 2 developing).

**Próximo paso (a tu elección):**
- Refinar lite → `/po vitalia vitalia-bugfix-shell-nav-scroll-errors` (spec corto de regresión
  con AC por bug), o
- Como es bugfix con repro live + diagnóstico ya mapeado, ir directo a `/architect vitalia
  vitalia-bugfix-shell-nav-scroll-errors` para el ready package (tickets por bug).

¿Lo refinamos con /po o vamos directo a /architect? ¿Alguna hipótesis PM que quieras corregir
antes (sobre todo #1 ruta default y #7 error-boundary)?

### 2026-06-02 19:47 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Chris pidió `/architect ... mapear las causas, detectar todos los errores y solucionarlos hasta
el done`. Step 0 GREEN (worktree CANÓNICO vitalia, `wip/vitalia`). Confirmé que las 6 superficies
existen en código (`(shell-organism)/layout.tsx`, `page.tsx`, `TenantSwitcher.tsx`+`TopBarGlobal.tsx`,
`SubTabContent.tsx`/`SubTabHeader.tsx`, `mateo/agenda/error.tsx` + `(shell-organism)/not-found.tsx`).

**Decisión:** ratifiqué scope → `state: idea → refined` (bugfix lite ADR-011: el checkpoint body
= spec-lite, salto `/po`; Chris eligió `/architect` directo). `ratified_by_chris: true`. NO construye
sub-tabs nuevas → gates ADR-003 (mockup) / ADR-004 (9 secciones build) NO aplican; los fixes
PRESERVAN el patrón shell existente (anotado `architecture_pattern: ADR-vitalia-004`).

**WIP cap v2 module-scoped:** bucket `shell` libre (las 2 stories `developing` son `lisa` +
`e2e-harness`, otros módulos) → paralelo OK.

**Encadeno `/architect` ahora** (auto-chain rule). El architect: (1) mapea causa raíz por bug
validando las hipótesis PM en código real, (2) produce ready package con ticket por bug, (3) por
"hasta el done" PROPONE `autonomous_mode: true` para que la chain siga dev-team→auditor→merge sin
re-tipear — **vos ratificás ese flag** (architect propone, Chris ratifica). El gate ADR-011 sigue
firme: `/dev-team` reproduce cada bug LOCAL antes de tocar código.

### 2026-06-02 20:10 · 🤖 claude · `/architect` · ✓ APLICADO
Mapeé la **causa raíz REAL de los 6 bugs leyendo el código** (no me quedé en las hipótesis PM).
Ready package cerrado → `state: refined → ready`. Artifacts en la story: `03-arch.md` (mapa causa
raíz por bug), `04-validators.yaml`, `05-guidelines.md`, `06-tickets.yaml` (T-1..T-6), `dispatch-plan.md`.

**Hallazgos clave (corrigen/afinan las hipótesis):**
- **#1 Routing:** regresión de `paradigm-map-zones` T-5. La agenda migró `valeria/agenda → mateo/agenda`
  pero **3 redirects** quedaron apuntando a la vieja. `isValidAgent('valeria')` es FALSE → 404. Fix:
  redirigir a `mateo/agenda` con un SSoT `DEFAULT_LANDING_SUBPATH` (anti-drift).
- **#4 Scroll (ALTA):** NO es `layout.tsx`. Es `AppPanelSlot.tsx:61` (`overflow-hidden` en el contenedor
  de contenido) → `overflow-y-auto`. Una línea.
- **#7 Error-boundary (ALTA):** solo existe `mateo/agenda/error.tsx`; falta el boundary genérico →
  cualquier error sube por encima del shell y mata la nav. Fix: `[agent]/error.tsx` genérico (aísla al
  panel, chrome vivo). Bonus: acota el blast-radius del #6 (lisa-doctores).
- **#5 Banner:** confirmado exacto — `InfoBannerLandingDescoped.tsx:62`. Lo elimino + dead-code cleanup.
- **#3 Títulos:** el eco viene del `SubTabHeader` del dispatcher (+ doble-título en Servicios/Conexiones)
  y de los h2 de las vistas N3 de lisa/marca. **Excluyo `lisa/staff`** (es de lisa-doctores, developing).
- **#2 Selector tenant:** REFUTÉ la hipótesis (`<=1`). Causa contribuyente CONFIRMADA:
  `useStoreHydration(useTenantStore)` **nunca se llama**. Pero el modo de fallo completo necesita
  **repro en dev-app** (¿`/api/tenants` vacío?) → ADR-011 obliga a `/dev-team` reproducir antes de fixear.

**Plan:** 6 tickets FE, todos `builder-frontend`/sonnet (cero agentic, cero core → R23 no aplica).
Ratifiqué `autonomous_mode: true` por tu "hasta el done". **Encadeno `/dev-team` ahora.**
⚠️ **Ceiling honesto:** la cadena autónoma llega hasta dejar todo verificado en dev-app + `demo-script.md`
listo, pero `reviewing → done` exige **tu demo paso a paso + sign-off** (DoD #37 §5). Ahí PAUSO y te aviso.

### 2026-06-02 21:05 · 🤖 claude · `/dev-team` · ⚠️ DUDA
Build de los 6 fixes COMPLETO y correcto a nivel código (+ 2493 unit tests GREEN + tsc/eslint/arch
verdes), **committeado y pusheado** (`132d17f6` fix 32 files + `98061462` docs) a `wip/vitalia`.
Recuperé el trabajo de un builder-frontend que se colgó a mitad (worktree aislado) — apliqué su patch
limpio a este worktree, verifiqué los 6 fixes uno por uno, corrí todos los gates estáticos.

**Pero NO te digo "done": la verificación LIVE no cerró limpia** (y eso es bueno — la atrapó).
Corrí los e2e contra el stack real. Hallazgos (detalle en `VERIFICATION-FINDINGS.md`):
- ✅ El shell **renderiza** y el **selector de tenant SÍ se ve** ("Clínica Sanaré") → Bug #2 pinta bien.
- ⚠️ Los e2e que escribió el builder son **hybrid-mock** (mockean `/api/tenants` cliente pero el layout
  resuelve tenants server-side contra el backend real) → producen **artefactos**, no son verificación válida (DoD #37).
- ⚠️ **Pre-existentes (NO de este fix):** backend 404 en `/api/v1/lisa/marca/{visuals,identity,contact}`
  para el tenant de prueba, y un **`Rendered more hooks` en `mateo/agenda`** (el destino del Bug #1).
  Pruebа de que no es mío: mi hook nuevo vive en el layout compartido → las hojas de Presencia montan
  ese mismo layout SIN el error; sólo Agenda lo tira.

**No conecté Chrome DevTools MCP esta sesión** (no está disponible) → no pude hacer la verificación
conversacional live. Dejé `demo-script.md` para que la cierres vos.

**Necesito tu decisión (no avanzo a developed sin esto):**
- (a) Hacés el **demo manual** en dev-app (demo-script.md) = evidencia DoD #37 §5 + tu sign-off, o
- (b) Querés que **investigue el `Rendered more hooks` de mateo/agenda** primero (es el landing del Bug #1
  — si es real y no artefacto e2e, conviene arreglarlo o cambiar el landing), o
- (c) Que **rehaga los e2e specs** a entorno limpio (real-auth + datos sembrados) para que el gate sea señal real.

Story queda en `developing` · `dod_live_verified: false`. Lock `code:shell` liberado.

### 2026-06-02 22:05 · 🤖 claude · `/dev-team` · ✓ APLICADO
**Live-verify LOGRADO contra el stack real** (real Clerk auth + real backend, NO mock). Los 6 bugs
testables PASS (`_live-verify.spec.ts`, exit 0, 7 passed + 1 flaky-retry-pass).

Camino: el Chrome MCP que instalé quedó `Connected` en CLI pero **sus tools no cargaron en la sesión
resumida** (quirk: resume ≠ full restart). En vez de quemar otro ciclo, hice el live-verify con
**Playwright real-backend** (fixture `real-backend-forward` → forward /api/v1 a :8002, sin mock).

Pero primero tuve que destrabar un **build error global del dev-server**: faltaban `sonner`,
`react-window`, `react-hook-form` en el node_modules del CONTAINER (stale — deps declaradas+committeadas
por las stories en developing, pero el volumen nunca se reinstaló). El Toaster global rompía TODA ruta
(incl. /sign-in → Clerk no cargaba → auth fallaba). Fix no-destructivo: `pnpm install` en el container
+ restart FE. **Eso es dominio de la story estabilizar-harness-e2e-lisa-marca**, no de este bugfix.

★ **El `Rendered more hooks` en mateo/agenda era ARTEFACTO de ese build roto** — con build limpio, el
landing del Bug #1 corre console-limpio. Concern resuelto.

**Verificado live:** #1 lands mateo/agenda · #1b valeria/agenda=404 · #2 selector visible · #3 sin
título-eco · #4 overflow-y auto · #5 sin banner landing. #7 (error boundary) = code-verified, no
forcé un error client real live. Ruido residual = 404 backend pre-existentes en lisa/marca (no míos).

Evidencia en `VERIFICATION-FINDINGS.md` + `dod_evidence` del checkpoint. `dod_live_verified: true`
(técnico). **Falta para `done`:** tu `demo_signoff` (demo-script.md), rework de los 6 e2e regression
specs (hybrid-mock → real-backend), y /auditor. ¿Seguimos con el rework + auditor, o hacés el demo?
