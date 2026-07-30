---
story_id: vitalia-shell-dual-mount-a11y-fix
created_at: 2026-06-01T00:00:00-05:00
last_modified: 2026-06-01T00:00:00-05:00
notes_count: 0
refs_count: 3
conversation_count: 1
---

<!-- voseo-allowed: doc interno / buzón conversacional Chris↔Claude, no user-facing -->

# chris-input.md · vitalia-shell-dual-mount-a11y-fix

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-01 00:00
Bugfix arquitectónico del shell-organism (dual-mount → testids duplicados + id="main-content" ×3). Sale del live-verify de doctores. Es shell compartido: un error rompe la UI de TODOS los agentes → re-verificación transversal obligatoria. NO un edit apresurado.

## 📎 Referencias

- **📄 doc** · `vitalia/docs/observed-bugs/2026-05-31-shell-dual-mount-duplicate-testids.md`
  > Root-cause confirmado (Triple-main pattern deliberado) + fix design + impacto E2E.
- **📖 story-ref** · `vitalia-fase2-lisa-doctores`
  > Story bloqueada por este bug (su harness usa workaround `.filter({visible:true})`).
- **📖 story-ref** · `nicolify-r0-shell` (commits 641dbb4c / e153f53d "isDesktop huérfano → crash")
  > Prior-art: nicolify peleó el mismo bug; el render condicional crasheó → usaron single-main + CSS.

## 💬 Conversación

> Append-only · turn-by-turn cronológico. Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-01 00:00 · 🤖 claude · `/pm-vitalia` · 💡 PROPONE
Story creada (`state: idea → refined`, type=bugfix ADR-011, repro_verified=true) con cap_target=`shell-vitalia`, cap_change_type=`fix`, functional_area=`plataforma-tecnica.shell` (zona Infraestructura, derivada del árbol del paradigma — el shell es quality-attribute del contenedor visual, no caja de valor).

**Prior art scan corrido (anti-duplication-refining):** hallazgo que CAMBIA el fix propuesto. Nicolify (su shell se portó DE vitalia) ya peleó este bug y el **render condicional por viewport del bug doc CRASHEA** (React "more hooks than previous render" al montar/desmontar el `<Group>` resizable detrás de `isDesktop`). Su solución: **UN solo `<main id="main-content">` + CSS** (mata el id duplicado + el crash), pero eso por sí solo NO mata los testids duplicados. → **PROPONGO** que /architect diseñe la reconciliación: single-main (patrón nicolify) **+ render del `<AppPanelSlot>`/children UNA sola vez** (mata testids). Es shell brand-local: aplicar el PATRÓN, no compartir el archivo.

Encadeno a `/architect` para cerrar el ready package (03-arch reconciliando ambos approaches + 04-validators con el plan de re-verificación transversal 5 agentes ×3 modos + axe + dev-app, + 06-tickets con la reescritura de los tests del triple-main).

⚠️ DUDA para vos Chris (no bloqueante — /architect puede arrancar): ¿confirmás que el fix es shell brand-local de vitalia (NO lift a core / NO tocar el de nicolify)? Asumo que sí.

### 2026-06-01 00:30 · 🤖 claude · `/architect` · ✓ APLICADO
Ready package cerrado (`state: refined → ready`). 5 artifacts en el story-folder. Decisión arquitectónica central resuelta (reconciliación que el bug doc no tenía):
- **D1** single `<main id="main-content">` (patrón nicolify) → mata id duplicado + a11y landmark.
- **D2** `<AppPanelSlot>{children}>` renderizado **UNA sola vez** → mata testids duplicados. **Va más allá de nicolify** (cuyo single-main dejó los testids duplicados porque renderiza children en ambas ramas desktop+mobile).
- **D3** hook-count estable (todos los hooks arriba, incondicionales) + **D4** NADA de mount condicional del `<Group>` detrás de isDesktop → evita el crash "more hooks" que sufrió nicolify.
- Chrome responsive (resizable agentic / grid web / single-col mobile) rodea al MISMO slot vía CSS, no lo re-monta.

Tickets: **T-1** (builder-frontend **Sonnet** — FE no-agentic, R23 N/A — reescribir ShellOrganismLayoutClient + RED-first sus tests SC-1/2/4) + **T-2** (verificación transversal 5 agentes ×3 modos + axe + dev-app live ADR-008). `autonomous_mode: false` — lo propongo porque el blast-radius es transversal (un error rompe la UI de TODOS los agentes), conviene tu check antes del build.

⚠️ DUDA para Chris: ¿arranco `/dev-team` T-1 ahora (build con gates transversales protegiendo el blast-radius; el merge igual frena para vos por ADR-008), o querés revisar el ready package / mockear primero? Recomiendo arrancar el build — los validators RED-first + transversales son la red de seguridad.

### 2026-06-01 10:25 · 🤖 claude · `/dev-team` · ✓ APLICADO
**T-1 construido y GREEN** (builder-frontend Sonnet, commit `b65baae6`, 2 archivos). El fix implementa D1-D5:
- `ShellOrganismLayoutClient.tsx` reescrito: UN solo `<main id="main-content">` + `<AppPanelSlot>{children}>` renderizado **una sola vez** (línea 280), hooks incondicionales al tope (D3), SIN useMediaQuery/isDesktop (D4), gate desktop↔mobile por CSS (D5). Header doc actualizado (borra Triple-main, documenta la lección nicolify).
- `ShellOrganismLayout.test.tsx` reescrito (RED→GREEN): asserts triple-main → single-main + single-slot.

**Verificación (Step 4):** ShellOrganismLayout 22/22 · AppPanelSlot 13/13 · skip-link arch 2/2 · **suite shell-organism completa 31 archivos / 501 tests ALL PASS** (regresión transversal: cero) · `tsc src/` 0 errores · eslint limpio.

⚠️ **Finding pre-existente (NO de este fix, para /pm-luana):** el arch test `test-no-cross-brand-shell-mirror.test.ts` falla (4 matches `SubTabMeta`/`extractSubtabFromPath` en nicolify). Causa: el **rebuild de nicolify portó el shell de vitalia** (ya en origin/main) sin renombrar esos símbolos TS. Mi T-1 no lo introdujo (solo tocó 2 archivos vitalia). Es un mirror cross-brand que pide decisión /pm-luana (renombrar en nicolify, o aceptar el port + ajustar el arch test).

**Pendiente T-2 (verificación transversal LIVE · ADR-008):** axe wcag2aa + dev-app live (ejercer lisa + valeria sidebar desktop+mobile, confirmar 1 main-content + 1 slot en DOM real, consola sin "more hooks") + prueba de fuego E2E doctores (getByTestId resuelve a 1 sin `.filter visible`). Esto llena `dev_app_verified.evidence` (requerido para developed→reviewing→done). `autonomous_mode:false` → checkpoint con Chris antes de T-2 live.

### 2026-06-01T11:05 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**Sesión de cierre — arranco Pendiente A (dual-mount).** Step 0 GREEN verificado: wip/vitalia @ 2356bd26 (pusheado), origin/main @ 75b43824 intacto, squash stale 63b3adf1 en platform main local (NO se pushea). Story closure scan: 2 stories abiertas (esta `developing`; doctores `reviewing` defer_audit:true). Esta destraba doctores → prioridad.

Stack dev vitalia UP (backend/frontend/cloudflared 18-26h) · dev-app.vitalialat.com responde 307 (auth redirect, esperado). ⚠️ Footgun cross-worktree activo: el frontend container lleva 18h up mientras T-1 (b65baae6) se commiteó esta sesión → dev-team debe re-correr `make dev-app-vitalia` DESDE este worktree antes de verificar, o servirá código stale.

Encadeno `/dev-team` para T-2 (verificación LIVE transversal · ADR-008): los 5 agentes + valeria sidebar ×3 modos en dev-app, single-main+single-slot en DOM real, axe wcag2aa, prueba de fuego E2E doctores sin `.filter({visible:true})`. dev-team llena `dev_app_verified.evidence` → developing→developed → AUTO /auditor → vuelvo a /pm-vitalia para merge reviewing→done.

### 2026-06-01T11:40 · 🤖 claude · `/dev-team` · ✓ APLICADO
**T-2 (verificación LIVE · ADR-008) GREEN — dual-mount fix VERIFICADO en el stack real.** Chrome DevTools MCP no está conectado en esta sesión → usé el fallback canónico (Playwright autenticado live contra el stack real, válido per `definition-of-done-live-verify.md § Fallback`). Footgun NO disparado: confirmé que el frontend container bind-mountea ESTE worktree (`/home/chalreme/Proyectos/luana-vitalia/vitalia/frontend`), o sea ya servía el código del fix.

Nueva spec **live** (NO mockea backend): `e2e/regression/vitalia-shell-dual-mount-a11y-fix/single-slot-live.spec.ts`. **6 passed (18.5s)** — setup (Clerk sign-in fresco) + 4 tests:
- agentic-desktop · lisa.staff → 1 `#main-content` + 1 `app-panel-slot`, consola sin hooks/hydration
- web-desktop · lisa.marca.identidad → 1 + 1, consola limpia
- mobile · lisa.staff → 1 + 1, consola limpia (la rama mobile ya no duplica el slot)
- axe wcag2aa → cero violaciones duplicate-id / landmark-unique (el síntoma a11y del triple-main)

**Confirmación de que es LIVE real (no falso verde):** el backend REAL respondió en los logs (`GET /iam/users/me/tenants 200`). El `app-panel-slot` resuelve a **1** directamente → el workaround `.filter({visible:true})` ya no hace falta (prueba de fuego al nivel del shell).

⚠️ **Hallazgo (bug de DATOS, NO del shell · para Pendiente B):** `GET /clinics/doctors` da **500** (`UUID(clinic_id)` con `X-Clinic-ID` no-UUID que el FE no envía válido). Nunca se vio porque el harness de doctores **mockea el backend** (mismo patrón lisa-marca). Registrado en `observed-bugs/2026-06-01-doctors-list-500-clinic-id-uuid.md`. El shell rindió single-estructura aún con el panel en error state, y lisa/marca (sin doctores) también verde → el dual-mount fix NO está afectado.

Story `developing → developed`. AUTO-HANDOFF `/auditor` (auditor-frontend Opus). Build-claim `code:shell-organism` liberado.

### 2026-06-01T11:58 · 🤖 claude · `/auditor` · ✓ APLICADO
**APPROVED** (auditor-frontend Opus, 16 categorías). El fix elimina el triple-main/dual-slot vía single `<main>` (D1) + single `<AppPanelSlot>` por rama XOR (D2), hooks incondicionales al tope (D3), gating desktop/mobile por CSS (D4/D5) — sin reintroducir el crash "more hooks" de nicolify. Los tests reescritos **tightening real** (`toBeGreaterThanOrEqual(1)` → `.toBe(1)` estricto, NO debilitados). Live-verify honesta (stack real, sin mocks, DOM real ×3 modos + axe scoped). Scope limpio (solo el archivo prod + su test + la spec live; sin core/, sin cross-brand).

Gates re-corridos independiente: tsc 0 · eslint 0 · vitest **501/501** · Playwright live **6 passed**.

Findings: C1 4/4 · C2 5/5 · C3 6/6 · C4 8/8 · C5 6/6.

⚠️ Finding cross-brand para `/pm-luana` (NO blocker de esta story): arch test `no-cross-brand-shell-mirror` falla por `SubTabMeta`/`extractSubtabFromPath` portados a nicolify (PRE-EXISTENTE en origin/main, este fix no los toca).

CHECKPOINTS.md + T-1-review.md escritos. AUTO-HANDOFF `/pm-vitalia` para merge reviewing→done (07-merge.md + cap change_log fix + git mv archive).

### 2026-06-01T12:05 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
**MERGE reviewing→done.** Gate ADR-008 OK (`dev_app_verified.evidence` poblado), CHECKPOINTS C1-C5 verdes, auditor APPROVED. Apliqué:
- `07-merge.md` (5 secciones) escrito.
- `capabilities/shell-organism/shell-vitalia.yaml`: change_log entry type=**fix** (NO scenarios, es bugfix) + `last_modified: 2026-06-01`.
- Story archivada: `git mv` a `vitalia/docs/archive/2026/stories/vitalia-shell-dual-mount-a11y-fix/` en este mismo commit (R2).
- `state: done`.

**Pendiente A CERRADO.** Esto destraba Pendiente B (vitalia-fase2-lisa-doctores): el workaround `.filter({visible:true})` ya no hace falta. Próximo: Pendiente B (harness doctores) — que además debe resolver el `GET /clinics/doctors` 500 (X-Clinic-ID) detectado en el live-verify para llegar a `done` con evidencia real.
