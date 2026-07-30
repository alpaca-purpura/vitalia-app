# 05-guidelines — platform-lift-shell-chrome-ui-kit

> Patterns required/forbidden + files-in-scope exactos + must_load_skills enforceable. Los aprendizajes técnicos son **verbatim del checkpoint § Aprendizajes** + del predecesor `vitalia-shell-core-hardening` — **NO redescubrir, NO simplificar** (RN-4 sagrado).

## must_load_skills (enforceable por ticket)

| Ticket surface | must_load_skills |
|---|---|
| Kit (T-K) | `frontend-expert` · `.claude/rules/anti-duplication.md` · checkpoint § Aprendizajes (este archivo) |
| Vitalia (T-V) | `frontend-expert` · `vitalia-design-system` · `playwright-expert` (e2e) · `.claude/rules/anti-duplication.md` · este archivo |
| Nicolify (T-N) | `frontend-expert` · `nicolify-design-system` · `.claude/rules/anti-duplication.md` · este archivo |

## PATTERNS REQUIRED (sagrados — RN-4 · portar verbatim)

### 1. react-resizable-panels v4 — props-capture-on-mount (NO SIMPLIFICAR)
La lib **captura `collapsible`/`collapsedSize`/`minSize` EN MOUNT**. La transición runtime open↔closed con props dinámicas es INERTE. El chrome del kit DEBE conservar TAL CUAL (del `ShellOrganismLayoutClient.tsx` origen):
- **`key`-remount del Panel** por estado: `key={`valeria-${!isLg ? "mobile" : supervisorOpen === "closed" ? "A" : historyOpen ? "C" : "B"}`}` → fuerza remount → la lib registra props frescas + limpia drag-state interno (resize vivo post-ciclo). Renombrar `valeria-` → `supervisor-` (genérico) PERO conservar la lógica idéntica.
- **retry-rAF hasta `isCollapsed()`** (max ~30 frames) para el collapse de estado A: el Group re-aplica el layout PERSISTIDO al panel remontado y pisa el collapse si llega antes del registro. El collapse imperativo único es no-op en transición runtime.
- **`collapsedSize={STRIP_VALERIA_PX}` (number = PX), NO string-pct** — `collapsedSize={stripPct}` (3.4) daba 3.4 PX (strip invisible). v4 units: number=PX, string "NN%"=%.
- **`defaultSize` nace en el tamaño destino:** closed → `stripPct` (< minSize + collapsible=true → la lib AUTO-colapsa a collapsedSize por contrato v4). El collapse() del effect queda como backup.
- **`collapsible` DINÁMICO:** true SOLO en estado A (closed) o drawer (!isLg); false en B/C → la lib clampea en minSize en drag (RN-8/RN-9: collapse SOLO por botón/avatar).
- **push REAL del historial ±histPct** (RN-7): el historial ENSANCHA el panel del supervisor (empuja al agente), NO le roba ancho al chat. `HISTORY_PX = 280` = la columna real del grid (state C: `280px 1fr`). Floor en C: `minValeriaPct + histPct` (chat nunca < min legible con historial). retry-rAF contra la persistencia.
- **`setLayout` clampea (no colapsa); collapse real = `panelRef.collapse()`; `expand()` ANTES de cualquier setLayout** post-reopen (sin expand el panel queda "collapsed" interno y el drag se ignora).
- **Conservar los comentarios `★ Live-fix 2026-06-11`** en el código lifteado (son la memoria de por qué — auditor los verifica).

### 2. Grid implícito (NO recortar contenido)
`grid-rows-[...]` sin cols explícitas recorta → conservar **`grid-cols-[minmax(0,1fr)]` + `min-w-0`** en `ChatPanel` (ex-ValeriaChat): `@container grid min-w-0 grid-rows-[auto_1fr_auto] grid-cols-[minmax(0,1fr)] overflow-hidden h-full bg-background`.

### 3. Container queries Tailwind v4
`@container` (en ChatPanel) + `@[24rem]:inline-flex` (pill del ChatHeader) — depende del panel, no del viewport. **Estas clases son JIT/arbitrary → requieren que el archivo esté en el Tailwind content scan.** Al mover al kit, agregar `@source` del kit organism en vitalia globals.css (ver 03-arch § Tailwind — deliverable real, gate = SC-5 + live-verify, NO basta tsc).

### 4. Store SSR-safe (CONSUMIR, no recrear)
El `createShellStore` del kit usa `@luana/hooks/createSsrSafePersistedStore` + `use-store-hydration` (ADR-vitalia-006). NUNCA reimplementar. `skipHydration:true` + `_hasHydrated` + setItem NO-OP pre-hydration. La rehidratación se dispara UNA vez desde `ShellLayoutClient` (dentro del chunk ssr:false). `migrate`/`merge`/`sanitize` toleran shape legacy sin crash (SC-6).

### 5. ssr:false (NECESARIO — no eliminar)
`react-resizable-panels v4.11.1` usa `storage: n = localStorage` como default param bare-name que crashea el SSR pass de Next (ReferenceError, no fixeable desde el caller). El wrapper `dynamic({ssr:false})` vive en el kit (`ShellLayout`). El skeleton SSR es store-free (no subscribe el store → no clobber localStorage en pre-hydration) — se parametriza por `skeletonSlot`.

## PATTERNS FORBIDDEN

- ❌ Simplificar la máquina del splitter al moverla (los fixes v4 son quirúrgicos — RN-4).
- ❌ Eliminar el `ssr:false` (re-introduce el crash SSR de react-resizable-panels v4).
- ❌ Dejar `'Valeria'`/`'vitalia'`/`#01B2F8`/`nicolify` en lógica del kit (RN-2/SC-7) — todo brand-data por prop/CSS var.
- ❌ Default de prop con nombre de marca (`supervisorName` SIN default).
- ❌ Importar `@/stores/chat-store` o `@/stores/shell-store` desde el kit (inyectar por prop).
- ❌ Re-exportar el `Group`/`Panel`/`Separator` de react-resizable-panels desde el barrel del kit (colisión con el `Group` form ya exportado).
- ❌ Tocar asserts de conducta de la e2e vitalia para que pasen (Bif-3 — root cause en el PORT, fix en el kit; solo paths/imports del harness si el move lo exige).
- ❌ Import cross-brand (vitalia↛nicolify): ambos importan del kit (arch-test CHECK A zero-tolerance).
- ❌ Cambiar la localStorage key del shell store/group (rompe la e2e — conservar `vitalia-shell-state`/`vitalia-shell-split-agentic`).
- ❌ Migrar el N3 de nicolify en esta story (ortogonal — 03-arch § Open Q1).
- ❌ Tocar `core/luana-core-*/src/` (Python engine — sigue prohibido; lo autorizado es `core/@luana/ui-kit`, package TS).
- ❌ `op.create_table` / migrations / BE (story FE-only).

## Operativa de build (RN del checkpoint — verbatim)

- **COMMIT INCREMENTAL por pathspec** apenas un bloque esté verde (los builders mueren ~140 tool-uses). Builder muerto → verificar tree+commits + spawn agent nuevo (NO restart from scratch). `git commit <rutas-exactas>`, NUNCA `git add .`/`-A`.
- **`SCOPE_GATE_SKIP=1` permitido** con razón en el commit body (lift sancionado, proposal `2026-06-01-lift-shell-organism` accepted) — M13 bloquea el mix core+vitalia+nicolify.
- **Allowlists arch actualizadas en el MISMO commit** que cada move (mirror ratchet shrink-only RN-5).
- **pnpm symlink-war host↔container:** host-install (`pnpm install` desde el host) para vitest/tsc; container-install para e2e. NUNCA alternar sin re-install; restart del container FE pierde node_modules raíz. Para el kit: `pnpm --filter @luana/ui-kit ...` native host.
- **Verificación visual REAL:** screenshots + overhang-check — los números solos mienten (RN-4).
- **Modelos:** subagents HEREDAN el modelo de sesión (Fable 5) — `model_preference: inherit`, sin override en spawns.

## Files in scope (exactos)

- **Kit (editable — autorización /pm-luana):** `core/@luana/ui-kit/src/organism/shell/**` (NEW) · `core/@luana/ui-kit/src/index.ts` (barrel) · `core/@luana/ui-kit/package.json` (deps+version) · `core/@luana/ui-kit/CHANGELOG.md`.
- **Vitalia:** `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` · `vitalia/frontend/src/stores/shell-store.ts` · `vitalia/frontend/src/components/shared/shell-organism/**` (DELETE chrome lifteado) · `vitalia/frontend/src/lib/agent-catalog.ts` (re-point helpers) · `vitalia/frontend/src/app/globals.css` (@source) · `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (allowlist shrink) · mover `_mock-*` a `stores/`/`lib/` ANTES de borrar el chrome.
- **Nicolify:** `nicolify/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` · `nicolify/frontend/src/stores/shell-store.ts` · `nicolify/frontend/src/components/shared/shell-organism/**` (RETIRE legacy chrome) · `nicolify/frontend/src/lib/agent-catalog.ts` (re-point helpers) · tests legacy update/retire.
- **Forbidden:** `vitalia/frontend/src/features/**` · `nicolify/frontend/src/features/**` · `{brand}/backend/**` · `core/luana-core-*/src/**` · `{brand}/frontend/src/components/ui/**` (salvo borrado de archivos lifteados).

## Proposal governance

Al merge: `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md` → `state: migrated` + nota de SEMVER (0.4.0 minor) + el target real reconciliado (`src/organism/shell/`). `SHELL-DESIGN-CONTRACT.md` (vitalia) → § origen (chrome vive en `@luana/ui-kit`).
