<!-- voseo-allowed: prompt interno de handoff para la próxima sesión (voz de Chris / instrucción a Claude), NO es string user-facing -->

# Handoff — vitalia-fase2-lisa-doctores · UI design polish (continúa 2026-06-07)

> Sesión 2026-06-06/07: rescate funcional del story (7 bugs, todos live-verde).
> Próxima sesión = **comentarios de diseño UI de Chris** (él tiene varios) + cierre.
> Pegá el bloque entre `═══` como prompt de la nueva conversación.

## Estado git EXACTO (verificá primero)
- `wip/vitalia` @ `148a7f89` (pusheado). 5 commits de este story: `1a37c8c9` → `a1c4c7fb` → `b33a5839` → `f41ccadb` → `148a7f89`.
- `origin/main` @ `e98e09a8` (INTACTO — no se pusheó squash).
- Story `vitalia-fase2-lisa-doctores`: `state: developing` · `phase: AWAIT_CHRIS_VERIFY`. NO está done.
- ⚠️ Hay cambios uncommitted de OTRAS sesiones (compliance, servicios, etc.) — NO son de este story, no los toques.

## Lo que se arregló esta sesión (rescate funcional — TODO live-verde en dev-app)
La historia estaba "6/8 done" pero **NUNCA funcionó end-to-end por browser** (SSR initialData + e2e mockeado enmascaraban todo). 7 bugs reales:
1. **Loop infinito** `/lisa/staff` ("botando error") — `NuevoIntegranteModal` useEffect con `createDoctor` (RQ mutation, ref nueva/render) en deps → fix: deps estables. Unit RED(OOM)→GREEN.
2. **CORS** — `staff.ts`+`StaffWorkspaceShell` (client) base absoluta `localhost:8002` → CORS-block. Fix: base relativa (tunnel routea `/api/*`).
3a. **X-User-Role faltante** en mutaciones → 403. Fix: `useStaffActorHeaders` (espejo marca).
3b. **RBAC** doctores `admin_clinic`-only → **widen `{owner, admin_clinic}`** (decisión Chris). `_STAFF_MUTATION_ROLES` + test 10/10.
4. **Rol GLOBAL vs per-tenant + Clerk-id vs DB-UUID** — `useCurrentUser` da rol global (`doctor`) y Clerk id; los endpoints quieren rol per-tenant (`owner`) + `X-User-ID:UUID`. Fix (opción B Chris, targeted en `staff.ts`): rol per-tenant del tenant-store + DB UUID del `/me` cache.
5. **Perfil 422** ("No se pudo cargar el perfil" — Chris lo reportó) — `GET /{id}` detail exige `X-User-ID`; `useDoctor`+`StaffWorkspaceShell` no lo mandaban. Fix: actor headers + `enabled` gate hasta X-User-ID listo.
6. **Horarios crash** `(blocks).filter is not a function` — BE devuelve `{blocks:[...]}` envelope, FE esperaba array pelado. Fix: desempaquetar `res.blocks`.
7. **Tabs Perfil/Horarios/Servicios** empujados a la derecha (entity `flex-1`) → **left-aligned** (`EntitySubNavBar`, COMPARTIDO con embudo).

**dod_evidence live** (dr.demo owner, dev-app): directorio GET 200 · crear POST 201 (+DB+audit+telemetry+redirect) · perfil GET 200 renderiza · horarios+servicios cargan · tabs izquierda. Ver `checkpoint.md` § dod_evidence + regression_2026-06-06_bug{2..6}.

## ★ LO APRENDIDO (que sirva para mejorar)
1. **"6/8 done" mentía porque el e2e mockeaba el backend + SSR initialData pintaba el primer render.** Cada bug estaba enmascarado. Refuerza [[verification-real-not-200]] + [[embudo-imagined-contract-never-integrated]]. **Mejora:** ninguna story funcional a `developed` sin live-verify REAL contra dev-app de CADA flujo user-reachable (no solo el happy sembrado).
2. **Verificar el redirect URL ≠ verificar que la página destino RENDERIZA.** Mi write-recon asertó `…/perfil` (URL) y di "funciona" — pero el perfil 422eaba. Chris lo cazó. **Mejora (regla fina):** las recon/e2e asertan CONTENIDO (testid del view + status real del GET) no la URL. Candidato a learning `verify-content-not-redirect-url`.
3. **Mismatch de contrato FE↔BE recurrente** (mismo patrón ×3): list `{items}`, blocks `{blocks}` (envelopes vs array pelado) + `X-User-ID` UUID-vs-Clerk + rol per-tenant vs global. **Mejora:** contract-test FE↔BE (HB-42 ya flaggeado) — el FE asume shapes que el BE no manda. Cada hook nuevo debe verificar el shape real del response.
4. **Headers de endpoint inconsistentes en el MISMO módulo:** la LIST no pide `X-User-ID`, el DETAIL sí (audit-on-PHI-read); marca tipa `X-User-ID:str`+resuelve, doctores `:UUID`. **Mejora:** homologar el contrato de auth-headers cross-endpoint (carril aparte).
5. **Race en queries auto-firing que dependen de headers async** (X-User-ID viene de `/me`): el query disparó con header vacío → 422→200 flake. **Mejora:** `enabled` gate hasta que el header esté listo (patrón aplicado; documentar como convención).
6. **Fricción de harness (3× cada commit):** `CAP_ADVISORY_SKIP` (cap existe pero el hook lo re-pide en commits in-progress de developing) + `STORY_CLOSURE_GATE_SKIP` (el commit-hook NO es module-scoped per ADR-009 → bloquea commit a `clinics` porque embudo `crm` está open). **Mejora:** `/harness-issue` para ambos (commit-hook module-scoped + cap-gate no-refire en developing).

## Carriles aparte flaggeados (NO de este story — para /pm-luana o stories dedicadas)
- **Sistémico FE:** `useCurrentUser` (hook compartido, 8 consumers) devuelve rol GLOBAL no per-tenant + expone Clerk id no DB id. El fix de doctores lo sortea targeted; el sistémico merece story propia (como la de no-clerk-org).
- **Contrato BE:** `X-User-ID` inconsistente (marca str+resuelve · doctores UUID directo) — homologar.
- **Tech-debt:** `test_doctor_cross_tenant.py` usa `asyncio.get_event_loop()` (roto Py3.12, pre-existente).

## Falta para `developed → done`
1. **★ Comentarios de diseño UI de Chris** (el foco de la próxima sesión — él los tiene).
2. `demo-script.md` (story funcional).
3. Honest-RED secundarios: SC-1b/c/d calendar recurrence · SC-9 paginación · SC-11 i18n credencial por país (mock→real o scope per #37).
4. Visual goldens V-VIS-1..4 → ratificación Chris (ADR-vitalia-003, NO autonomous).
5. G (Chris self-test live) → R reconcile (/pm-vitalia: spec AC-12 widen RBAC + cap) → /auditor → merge.

## Archivos clave tocados (para contexto FE)
- `vitalia/frontend/src/features/lisa/api/staff.ts` (useStaffActorHeaders + per-tenant role + DB-UUID + enabled gates + blocks unwrap)
- `vitalia/frontend/src/features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx`
- `vitalia/frontend/src/features/lisa/components/staff/NuevoIntegranteModal.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (COMPARTIDO — afecta embudo)
- `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` (_STAFF_MUTATION_ROLES)
- design system SSoT: skill `vitalia-design-system` + `vitalia/docs/architecture/{design-system.md, SHELL-DESIGN-CONTRACT.md}` + `globals.css` + `tailwind.config.ts`

═══════════════════════════════════════════════════════════════════════════════

/pm-vitalia Continúo `vitalia-fase2-lisa-doctores` (handoff 2026-06-07). El rescate FUNCIONAL ya está hecho + live-verde en dev-app (7 bugs: loop · CORS · X-User-Role · RBAC widen · rol per-tenant/DB-id · perfil 422 · horarios envelope · tabs left-align). State `developing` · `phase: AWAIT_CHRIS_VERIFY`. wip/vitalia @ 148a7f89 pusheado, origin/main @ e98e09a8 intacto.

AHORA quiero trabajar **comentarios de diseño UI** que tengo sobre el módulo de doctores (Lisa → Staff: directorio + crear + perfil + horarios + servicios). Te los voy a ir pasando uno por uno.

Antes de tocar nada UI:
1. Step 0 worktree + leé `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/{checkpoint.md, HANDOFF-next-session.md, chris-input.md}`.
2. Cargá la skill `vitalia-design-system` (SSoT shell + átomos/moléculas + tokens + agentes) — obligatoria ANTES de tocar `vitalia/frontend/src/**`. NO inventes tokens/átomos; reusá los existentes (D1 frontend-visual-fidelity).
3. Confirmá dev-app: `make dev-app-vitalia` → dev-app.vitalialat.com (dr.demo@vitalialat.com, owner). Stack ya corre; footgun cross-worktree: re-`up` desde ESTE worktree si dudás.
4. Para cada comentario UI: cambio scoped (D3 — solo lo que pido) + reusá átomos Shadcn/`@luana/ui-kit` + tokens `globals.css` + **live-verify CONTENIDO en dev-app con screenshot** (no solo la URL — lección de esta sesión) + commit por pathspec (CAP_ADVISORY_SKIP=1 STORY_CLOSURE_GATE_SKIP=1 documentado: wip developing, embudo crm open module-scoped).
5. ⚠️ `EntitySubNavBar` es COMPARTIDO con adrian/embudo — si un cambio UI lo toca, avisame el impacto cross-workspace o scopealo con prop.

Empezá confirmando que leíste el handoff + dev-app levantado, y pedime el primer comentario de diseño. Después seguimos uno por uno. Cuando terminemos el polish UI: demo-script + honest-RED secundarios + ratificación goldens + G/R/auditor.

═══════════════════════════════════════════════════════════════════════════════
