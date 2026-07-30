# T-FE-switcher-wire — Result

- **Ticket:** T-FE-switcher-wire (06-tickets.yaml delta_v3 · group D3A-switcher · surface frontend)
- **Builder:** builder-frontend (Fable 5 — mandato Chris `model_mandate_2026_06_12`)
- **State:** build phase done (tests-passing) — awaiting orchestrator → gate-runner → auditor-frontend
- **Date:** 2026-06-12
- **Dep:** T-CORE-picker-slot shipped (51d1aa80) — `entityIdentitySlot` consumido, core NO tocado.
- **Plan previo:** `T-FE-switcher-wire-impl-log.md § Plan` (technical_design antes de código; primera entrada = test RED).

## Diff resumen (6 archivos producto/test + 2 docs — cero core, cero forbidden)

| Archivo | Cambio |
|---|---|
| `vitalia/frontend/src/features/lisa/api/staff.ts` | EXTEND: `pickerCursorToPage` + `mapDoctorsPageToPickerResult` (adapter page↔cursor PURO) + `useDoctorPickerSearchFn` (searchFn cursor para EntityPicker: `active=true` SIEMPRE (RN-D3A-2) + `q` server-side (RN-D3A-1) + `page_size=limit`; **identidad estable** vía latest-ref — el fetch-effect del picker depende de `searchFn`, identidad inestable = re-fetch loop). Headers verificados contra patrón real: el GET list NO exige actor headers (igual que `useStaffList`; X-User-ID es requisito detail/mutations — bug #5). |
| `…/components/staff/workspace/StaffWorkspaceShell.tsx` | EXTEND: `buildDoctorWorkspaceHref` (puro, exportado — deriva hoja de pathname ∈ {perfil,horarios,servicios,pagina}, fallback perfil) · `onPickDoctor` (same-id no-op; else `router.push` hoja PRESERVADA — ratificado Chris) · slot `useMemo(<EntityPicker value searchFn onChange testId="doctor-picker" searchPlaceholder="Buscar integrante…"/>)` → `entityIdentitySlot` de `EntityWorkspaceLayout`. `entity` ahora `useMemo([doctor])` (estabilidad referencial del subtree). NO se agregó la 4ª hoja (scope T-FE-pagina-publica) — solo el set preservable la conoce. |
| `…/api/__tests__/staff-picker-adapter.test.ts` | NEW (RED-first): 19 tests — cursor↔page (null/garbage/0/neg→1) · nextCursor intermedia/última/única · total · displayName fallback · pageSize-0 guard · contrato request (`active=true`, `q`, `page_size`, cursor→page, tenant+clinic) · **identidad estable cross-render** (cazó el gap real: el mock per-render destabilizaba el useCallback → endurecido a latest-ref). |
| `…/components/staff/__tests__/staff-picker-wire.test.tsx` | NEW (RED-first): 10 tests — `buildDoctorWorkspaceHref` ×6 (horarios/servicios/pagina/missing/null/unknown) + render shell: slot reemplaza bloque estático (`entity-identity-slot` presente, `aria-label="Editando:…"` ausente) · pick otro doctor → `router.push` hoja preservada (SC-D3A-1 unit) · mismo doctor → no push · request `active=true`. Stubs jsdom virtualizer espejo del test core. |
| `vitalia/frontend/e2e/pages/DoctorWorkspacePage.ts` | POM EXTEND: locators picker (trigger panel-scoped; content/search/listbox/empty/footer page-scoped — popover portal) + helpers `openPicker/searchInPicker/pickerOption/pickDoctorById`. |
| `…/e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts` | NEW: SC-D3A-1..4 vía `real-backend-forward.fixture` (Clerk auth + forwarding BE real :8002 + gate anti-burbuja `base.ts` — cero mock del surface, NUNCA `@playwright/test` directo). Precondición ≥2 activos → skip anotado (no falso verde). SC-D3A-3 assertion fuerte: opciones renderizadas ⊆ ids devueltos por el server con `active=true`. |
| `demo-script.md` | NEW (no existía): sección D3-A para Fase G (próximos tickets delta appendean). |
| `T-FE-switcher-wire-impl-log.md` | NEW: plan technical_design (D1/D2/D3 + batería + CONN + riesgos). |

## TDD

RED primero: ambos test files escritos ANTES del código. Run RED: **29/29 failed** (exports inexistentes + trigger no renderizado). GREEN tras implementación: 29/29 → +1 hardening (identidad estable) → 29/29.

## Gates (G5)

| Gate | Resultado |
|---|---|
| `npx tsc --noEmit` | ✅ EXIT 0 (strict) |
| `npx eslint src/features/lisa src/components` + POM + spec `--cache` | ✅ EXIT 0 — 0 errors, 0 warnings nuevos (output vacío) |
| `npx vitest run src/features/lisa` | ✅ **36 files / 403 tests PASS** (incluye los 29 nuevos) |
| Arch fitness `npx vitest run src/__tests__/architecture/` | ✅ 30 files / 187 PASS (fsd-boundaries, no-native-select, no-clerk-orgs, voseo, etc.) |
| Regresión embudo (slot opt-in — EntitySubNavBar default intacto) | ✅ `LeadWorkspace.test.tsx` 3/3 PASS **sin tocarlo** + tsc downstream EXIT 0 (`features/adrian/**` cero ediciones) |
| e2e SC-D3A-1..4 contra stack real (`E2E_BASE_URL=http://localhost:3002 --project=smoke`) | ✅ **6 passed (10.5s)** — setup Clerk + 4 scenarios + precondición. Cero mock del surface. |

## Live verification (dod_evidence — para checkpoint)

Stack real UP (`make dev-vitalia`): BE :8002 `{"status":"ok","brand":"vitalia"}` · FE :3002 · Clerk storageState `playwright/.clerk/user.json` (refrescado por project setup) · tenant `e69a691d-070e-5caf-a053-6e74642ec100` (4 doctores activos reales).

```yaml
dod_evidence:
  - action: "Abrir doctor (2b0d9466…) en hoja Horarios → picker ▾ → elegir otro doctor (2464fad7…) — navegación real autenticada (Clerk testing token, BE real, cero mock)"
    observed: "URL = /lisa/staff/{otro}/horarios (hoja PRESERVADA) + horarios-view del otro doctor renderiza + gate anti-burbuja verde (0 pageerror / 0 hydration / 0 console.error / 0 api 4xx-5xx)"
    backend_log: "GET /api/v1/vitalia/clinics/doctors?page=1&page_size=20&active=true → 200 OK (×N aperturas picker) · sin traceback en docker logs"
  - action: "Buscar 'zzqx' en el picker (server-side, debounced)"
    observed: "estado vacío 'Sin resultados' visible; request con filtro al server"
    backend_log: "GET /api/v1/vitalia/clinics/doctors?page=1&page_size=20&active=true&q=zzqx → 200 OK"
  - action: "Teclado: focus al search al abrir → ↓ mueve opción activa → Enter selecciona (navega preservando hoja) → Esc cierra sin navegar"
    observed: "selección por teclado funciona end-to-end; axe wcag2a/wcag2aa limpio salvo pin core (abajo)"
    backend_log: "mismas GETs 200; sin errores"
verified_at: 2026-06-12
dod_env: "localhost:3002 + BE :8002 real (real-backend-forward.fixture — Playwright chromium, Clerk real)"
```

PICKER_CALLS capturado en el run: `[{"url":"…/clinics/doctors?page=1&page_size=20&active=true","status":200,"itemIds":[4 UUIDs reales]}]`.

Nota live-verify: la acción real se ejerció vía Playwright chromium contra el stack dev real (cero mock del surface, network+console+DOM verificados por el gate anti-burbuja + assertions de red). `chrome-devtools-verify` MCP no estaba disponible como tool en esta sesión de subagent — el mecanismo equivalente (browser real + BE real + logs leídos + efecto confirmado) cumple el bar de Critical Rule #37; el run es reproducible con el comando del spec para la Fase G de Chris (demo-script.md § D3-A).

## ⚠️ Upstream/core finding (escalar a /pm-luana — NO bloquea este ticket)

**`core/@luana/ui-kit/src/EntityPicker.tsx` L334-335 (y hover L261/L334): `bg-accent` SIN el par `text-accent-foreground`.** Con el accent de vitalia (`287 53% 37%` púrpura + foreground blanco) la opción activa renderiza texto near-black sobre púrpura → contraste 2.46 (<4.5:1, axe `color-contrast` serious). `EntitySubNavBar.leafStateClass` sí parea los tokens (patrón Shadcn correcto) — el gap es solo del picker y afecta a cualquier marca con accent oscuro. **Fix = 1 línea core** (`active && "bg-accent text-accent-foreground"` + hovers) → carril lift (mismo paquete del proposal accepted `2026-06-12-ui-kit-entity-subnavbar-picker-slot.md` o micro-ticket core). Mientras tanto el spec SC-D3A-4 corre el scan COMPLETO y **PINEA** la violación conocida (tolera SOLO `color-contrast` + asserta su presencia → cuando el core se arregle el pin FALLA y fuerza restaurar el gate completo — cero falso verde silencioso).

## Mockup scope notes (doctores.html § doctoresN3Bar — qué NO se construyó y por qué)

- **Subtítulo specialty en cada opción** del mockup: el core `EntityPicker` as-is renderiza avatar+nombre (sin segunda línea). Core = forbidden_to_touch → no construido. Si Chris lo pide en G → extender core vía lift (prop `renderOption` o `subtitle`).
- **Glifo ✓ literal** en el activo: el core marca selected con `aria-selected=true` + `font-medium` (+ resaltado). Semántica equivalente; glifo no existe en core as-is.
- **Footer "· inactivos ocultos"**: el core muestra "Mostrando N de M"; el filtrado de inactivos es real (server `active=true`), el sufijo textual no existe en core as-is.
- **4ª hoja "Página"**: scope T-FE-pagina-publica (el set preservable ya la contempla — forward-compat sin acople).

## CONN

Consumed: `StaffWorkspaceShell` (montado en toda ruta `/lisa/staff/[doctor-id]/*` existente — cero ruta nueva) consume hook real → endpoint real existente (CERO cambio BE, 03-arch-delta §2.3). On-map: cap `lisa.doctores` (headers `// cap: clinics.lisa.doctores` en los 3 archivos nuevos de src/e2e, mismo formato que los hermanos). Navigable: trigger visible en la franja N3 de cada hoja. Notarized: cableado vía prop del layout core.

## Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `frontend-expert` (+ `references/runtime-quality-checklist.md` leído pre-commit) | always-on FE | useEffect deps: searchFn endurecido a latest-ref (identidad estable — el test de estabilidad cazó el gap); cero `useEffect` nuevo de data-fetch; routing usa `useTenantId()` para API y prop tenantId solo para URL (patrón existente respetado); mocks de test espejan contrato camelCase real. |
| `vitalia-design-system` + canon §2.4/§6.3-6.4 (must_load_skills/artifacts) | contrato visual + slot | EntityPicker consumido as-is (search server debounced + cursor 20 + windowed — PROHIBIDO colección completa client-side, cumplido por diseño del adapter); identidad = selector que reemplaza bloque estático; tokens canon, cero clase arbitraria nueva (cero clase nueva en absoluto). |
| `playwright-expert` (vía e2e-testing rule + fixtures del proyecto) | e2e SC-D3A | Specs importan `real-backend-forward.fixture` (auth.fixture-equivalente + base.ts anti-burbuja vía mergeTests) — NUNCA `@playwright/test` directo; preflight corrido; NATIVE host `E2E_BASE_URL=3002`; precondición de datos → skip anotado. |
| `chrome-devtools-verify` (must_load — gate live) | exit criterion live | MCP no disponible en esta sesión → mecanismo equivalente ejercido (browser chromium real + BE real + Network/console/DOM verificados + docker logs leídos); evidencia en § Live verification; reproducible por Chris en G (demo-script). |
| React patterns baseline | always-on | Memoización justificada (`entity`/slot/`onPickDoctor` estabilidad referencial del subtree picker); estados loading/master cubiertos por core (slot nunca renderiza sin entity); keys/a11y del picker los posee el core. |
| Shadcn/Tailwind conventions | always-on | Cero primitiva recreada, cero inline style, cero clase nueva — composición pura de `@luana/ui-kit`. |
| `anti-duplication` (Step 0 grep) | pre-write | Cero archivo de componente nuevo; picker NO recreado (CONSUMO core — el brief §7.5 lo manda); adapter = código brand-local mínimo sin equivalente engine (grep `EntitySearchFn` consumers = solo core). |
| `brand-expert`/`offer-expert`/`offer-type-preset-expert`/`copilot-expert`/`sales-agent-expert`/`metrics-expert` | cargadas por el caller | No aplicables — el ticket no toca esos dominios (staff/clinics brand-local). Sin decisiones. |

## Commit

`feat(vitalia/lisa): D3-A entity switcher — EntityPicker en franja N3 vía entityIdentitySlot (hoja preservada)` — pathspec scoped a los 8 archivos de este ticket. ⛔ NO push (orchestrator pushea serial — hub compartido).
