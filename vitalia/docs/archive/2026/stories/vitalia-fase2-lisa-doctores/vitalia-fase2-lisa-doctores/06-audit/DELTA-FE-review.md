<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: lisa-doctores DELTA v3 — consolidado FE (D3-A..F + T-CORE-picker-slot)

**Date:** 2026-06-12
**Auditor:** auditor-frontend (Fable 5, mandato `model_mandate_2026_06_12`)
**Scope diff:** `51d1aa80..978702c6` — `vitalia/frontend/**` + `core/@luana/ui-kit` (commit base `51d1aa80` = T-CORE-picker-slot, incluido en el review por mandato)
**Files Reviewed:** 40 FE (vitalia) + 2 ui-kit + routers BE cruzados para verificación de contrato
**Domains touched:** clinics (lisa/staff), shell N3 (EntitySubNavBar slot), assets proxy (consumo), public page `/d/**`
**Skills consulted:** frontend-expert (+ runtime-quality-checklist) · vitalia-design-system / design-system-canon §2.4/2.5/2.6/6.3 · playwright-expert (doctrina e2e) · brand-expert N/A (no toca brand-studio) · offer/copilot/sales-agent/metrics N/A
**Live-verified:** **SÍ — por el auditor** (stack dev real :8002, ver § Live Verification Audit)
**Verdict:** **FAIL (CHANGES_REQUESTED — Carril C' plan abajo)**

---

## /test-frontend Gate Status (gate-output.json audit-1 + re-runs independientes del auditor)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | 0 errores (re-run post self-fix: 0) |
| QUALITY | ESLint (`src/features/lisa src/app`) | PASS | 0 errores (re-run post self-fix: 0) |
| QUALITY | FE arch fitness | PASS | **30 files / 187 tests** — corridos por el auditor (gap del run scoped: gate-runner NO los corrió) |
| FUNCTIONAL | Vitest `src/features/lisa` | PASS | 489/489 (re-run post self-fix: 489/489) |
| FUNCTIONAL | Vitest `src/features/adrian` (downstream EntitySubNavBar) | PASS | **351/351** — corrido por el auditor (gap del run scoped) |
| RATCHET | ui-kit vitest | PASS | **266/266 re-verificado por el auditor** (baseline intacto, back-compat slot) |
| HEALTH | jscpd scoped `src/features/lisa` | **6.67%** | WARN (>5%); driver = boilerplate por-hook en `staff.ts` (~15 hooks repiten getToken/tenant/clinic/headers). Ver W2 |
| HEALTH | knip / madge | not run | run scoped; sin señal de ciclo nuevo (imports revisados manualmente — barrel only) |
| BE (contexto) | ruff/pytest clinics 424 + arch 353 | PASS | per gate-output audit-1 (E702 Carril A del auditor BE `978702c6`) |

> Gate-output freshness: el único commit posterior al run (`978702c6`) es el propio fix E702 del auditor BE sobre un test file — no invalida los gates FE. Re-runs FE posteriores a MIS self-fixes: ALL GREEN (ver § Self-fix log).

## Downstream regression scope

| Surface tocada | Downstream | Verificación |
|---|---|---|
| `core/@luana/ui-kit` `EntitySubNavBar`/`EntityWorkspaceLayout` (slot opt-in, commit `51d1aa80`) | vitalia `features/adrian` (embudo/NewLeadPage), vitalia `features/lisa`, nicolify shell | ui-kit vitest 266/266 (re-run auditor) · vitest adrian 351/351 (re-run auditor) · vitalia tsc 0 errores (cubre todos los consumers) · proposal `2026-06-12-ui-kit-entity-subnavbar-picker-slot` **status: accepted** ✓ — engine-edit gate satisfecho. Slot ausente → bloque estático verbatim (diff revisado línea a línea: aditivo puro) |
| `features/lisa/api/staff.ts` (compartido entre 4 hojas del workspace) | hojas Perfil/Horarios/Servicios/Página | vitest lisa 489/489 + tsc |
| `src/proxy.ts` (matcher público) | toda la app autenticada | matcher agregado = `"/d/(.*)"` exacto — NO amplía el agujero (no toca `/api`, no toca shell). PASS |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 — slots correctos, barrel exports (`index.ts:77`), cero cross-feature, cero deep-import a otra feature; `app/d/**` importa de `@/features/lisa` barrel ✓ |
| 2 | Server/Client | PASS | página pública = Server Component puro + `generateMetadata` + ISR 60s ✓; views client hoja = patrón ADR-004 ✓ |
| 3 | React Patterns | PASS | loading/error/empty en MonthCalendar + DoctorPaginaView + editor skeleton; keys estables; hooks top-level |
| 4 | Code Quality | WARN | jscpd scoped 6.67% (W2) + duplicación de tipo payload D3-F (self-fixed, ver log) |
| 5 | Accessibility | WARN | grid mes `role=grid/row/gridcell`+aria-labels ✓ · chips días `role=checkbox`+`aria-checked`+`onKeyDown` ✓ · picker combobox a11y propio del EntityPicker (ui-kit, testeado) ✓ · **SC-D3D-13 axe wcag2aa de la página pública: SIN spec y SIN evidencia** (F4) |
| 6 | Forms (RHF+Zod) | FAIL | editor estructurado: RHF+Zod ✓ autosave 600ms sin botón Guardar ✓ — pero el write del autosave apunta a ruta inexistente (F1) y la hidratación usa shapes que el BE no manda (F2/F3) |
| 7 | Multitenancy | PASS | `fetchClient` + X-Clinic-ID/X-User-ID/X-User-Role vía `useStaffActorHeaders` (patrón ratificado bug #4); página pública sin tenant context (correcto, anti-enum BE-side); cero tenantId hardcoded |
| 8 | Master Data / Spanish | PASS | español neutro en todo el delta (público + workspace); sin fechas `toLocaleDateString` nuevas problemáticas; sin moneda |
| 9 | Security / Deps | PASS | `/d/(.*)` público scoped ✓ · OG tags sin PHI ✓ · anti-enumeración live-verificada (404 idéntico OFF/unknown) ✓ · sin dangerouslySetInnerHTML/eval |
| 10 | Tests / TDD | FAIL | `useSavePublicProfile` shipped con CERO test (ni unit ni e2e) — por eso la ruta 404 pasó verde (F4) · SC-D3D-13 declarado en 04-validators sin spec · D3-C/E e2e mockean el endpoint del propio fix (W5) |
| 11 | Domain Alignment | FAIL | contrato FE↔BE roto en superficie editor (F1/F2/F3) · resumen recurrencia dual-source divergente (W1) |
| 12 | Architecture Fitness | PASS | 187/187 (run del auditor) — ratchets intactos |
| 13 | Mirror detection | PASS | basenames nuevos (MonthCalendar/PublicLinkBar/PhonePreview/StructuredProfileEditor/DoctorPaginaView) = 0 match cross-brand · EntityPicker REUSADO de ui-kit (no reinventado) ✓ · slot lift con proposal accepted ✓ |
| 14 | Decisions honored (R6) | N/A | `06-tickets.yaml` sin `decisions_applicable` |
| 15 | Connectivity (anti-isla) | PASS | hoja Página en `LEAF_DEFS` ✓ · `/d/**` ruta pública + excluida en proxy ✓ · material MOVIDO de Perfil con cross-link card (`DoctorPerfilView.tsx:363`) ✓ · cap `clinics.lisa.doctores` headers en files nuevos ✓ |
| 16 | Visual fidelity | WARN | mockup `doctores.html` v3.2 hoja Página: PublicLinkBar(pill+copiar+ver+toggle) + Material + editor + PhonePreview TODOS presentes y en orden ✓ · Select canónico en editor recurrencia (cero `<select>` nativo) ✓ · FloatingAutosaveIndicator: exactamente UNA renderizada por página ✓ (emojis inline muertos ✓) · arbitrary px nuevos (W3) · goldens V-VIS pendientes ratificación Chris en G (fuera de este review) |

---

## Findings

### FAIL F1 — El autosave del editor estructurado escribe a una ruta que NO existe (404 live-reproducido)
**Category:** 2/6/11 · **stake:** funcional AC-level (spec `01-spec.md:536` "Todo editable inline + autosave")
**File:** `vitalia/frontend/src/features/lisa/api/staff.ts:1092` (`useSavePublicProfile` → `PATCH /api/v1/vitalia/clinics/doctors/{id}/public-profile`)
**Consumer:** `StructuredProfileEditor.tsx:117` (autosave 600ms de TODAS las secciones del editor)
**Evidence (live, auditor):** `PATCH /doctors/2b0d9466-…/public-profile` con headers RBAC completos → **HTTP 404 `{"detail":"Not Found"}`** contra :8002. El router BE (`doctors_router.py`) NO tiene esa ruta (grep `public-profile` = solo serializers); el `PATCH /{doctor_id}` general (`dtos.py:341` `DoctorPatchRequest`, `extra="forbid"`) NO acepta secciones del perfil estructurado → tampoco hay reruteo posible sin BE.
**Effect:** toda edición manual del perfil estructurado se pierde en silencio. La dod_evidence #5 ejerció generar + Publicar + GET público — **nunca el write del editor** (el patrón exacto de `last-commit write-control`: 9 contratos imaginados fixeados, el 10º quedó vivo).
**Fix:** ver § Plan Carril C'.

### FAIL F2 — `experiencia`: shape FE imaginado vs wire BE real → render vacío silencioso (incluye página pública LIVE)
**Category:** 2/11/16
**Files:** `staff.types.ts:218-224` (`StructuredExperiencia {cargo, institucion, desde, hasta, descripcion}`) · `app/d/[clinica-slug]/[doctor-slug]/page.tsx:218-229` (`e.cargo/e.institucion/e.desde/e.hasta/e.descripcion`) · `PhonePreview.tsx:146` · `StructuredProfileEditor.tsx:142-148` (hidratación)
**BE truth (verificado en código + wire live):** `public_profile.py::ExperienciaItem {puesto, lugar, anios}` — emitido idéntico por detail (`doctors_router.py:553-560`), público (`public_doctor_serializer.py:136`) y generación (`bio_generation_service.py:142,404`). JSON live del endpoint público confirma el contrato (hoy `experiencia: null` — el fallback extractivo no produjo items, lo que ENMASCARÓ el drift en la live-verify del builder).
**Effect:** en cuanto una generación produzca experiencia, la página pública y el preview renderizan bullets con título VACÍO (`e.cargo` = undefined). tsc pasa porque el tipo FE miente sobre el wire.
**Fix:** ver § Plan Carril C' (la dirección — FE→shape del arch §6.1, o BE→shape rico — la reconcilia /architect+Chris; el mockup v3.2 NO pinna campos ricos, el arch §6.1 declara `{puesto, lugar, anios}` verbatim → default = FE se alinea al arch).

### FAIL F3 — `certificaciones`/`idiomas`: FE (workspace) los tipa como objetos; el BE manda `string[]`
**Category:** 2/11
**Files:** `staff.types.ts:227-237,250-251` (`StructuredCertificacion {nombre,otorgante,anio}` / `StructuredIdioma {idioma,nivel}` en `DoctorPublicProfile`) · `PhonePreview.tsx:192-194,218-220` (`c.nombre`/`c.otorgante`/`lang.idioma`/`lang.nivel`) · `StructuredProfileEditor.tsx:150-158` (hidratación `.map(c => c.nombre)`)
**BE truth:** `certificaciones: list[str]`, `idiomas: list[str]` (`public_profile.py:99-100`, `PublicDoctorProfileDTO`, wire live: `"certificaciones":["Colegiatura 12345 (PE)"]`).
**Inconsistencia interna FE:** la página pública SÍ los trata como strings (`page.tsx:262` `{c}`, `:273` `{l}`) y su tipo `PublicDoctorPageData:284-285` es correcto — el FE tiene DOS verdades para el mismo wire. PhonePreview + editor renderizan vacío.
**Fix:** ver § Plan Carril C'.

### FAIL F4 — TDD/verificación: el write nuevo shipped sin NINGÚN test + SC-D3D-13 (axe público) declarado y no implementado
**Category:** 10
**Evidence:** `grep "public-profile" src/features/lisa/**/*.test.*` = **0 hits** — `useSavePublicProfile` no tiene unit test (los demás hooks delta sí: `bio-docs-api.test.ts`, `staff-blocks-api.test.ts`, `staff-occurrences-api.test.ts`). Cero e2e de `/d/**` (no existe spec de página pública) y **ningún spec axe wcag2aa** para SC-D3D-13 pese a estar declarado en `04-validators.yaml § visual` + `03-arch-delta §6.3`. `T-FE-pagina-publica-result.md` no menciona axe.
**Why it matters:** esta es la razón mecánica por la que F1 pasó verde — `tdd-mandatory.md` RED-first violado exactamente en el único write sin cobertura.
**Fix:** incluido en § Plan Carril C' (tests primero).

### WARN W1 — RN-D3F-1 "same source" del resumen de recurrencia: dos formatters que divergen
**Category:** 11 · **Files:** `BloquePopover.tsx:134-197` (FE: "Se repite cada 2 semanas **el** lunes y jueves") vs `recurrence_summary.py:13,74,103` (BE `pattern_summary`: "Se repite cada 2 semanas **los** lunes y jueves"). El chip del calendario (BE) y el editor (FE) muestran strings distintos para el mismo patrón. Cross-stack no hay literal "shared formatter" posible — pero los strings DEBEN ser idénticos y testearse contra goldens compartidos (fixture JSON con casos → test en ambos stacks). Alinear artículo en el round de fixes.

### WARN W2 — jscpd 6.67% scoped en `features/lisa`
**Category:** 4 · driver: cada hook de `staff.ts` (1147 líneas) repite el bloque getToken/tenantId/clinicId/actorHeaders/fetchClient. Extraer `useStaffRequestCtx()` (token+tenant+clinic+headers) bajaría ~300 líneas duplicadas. No bloqueante; hacerlo en el round.

### WARN W3 — arbitrary values nuevos (canon §0)
**Category:** 16 · `PublicLinkBar.tsx:95` `[320px]` (token disponible: `max-w-80` = 320px) · `PhonePreview.tsx:53,60` `[280px]/[6px]/[520px]` (dimensiones de device-frame — aceptable CON comentario de justificación; hoy no lo tienen). El lint mecánico no-arbitrary del canon aún no está cableado (eslint verde) → WARN, se corrige en el round.

### WARN W4 — Autosave status de BioRepoInputs invisible en la hoja Página
**Category:** 6/16 · La única `FloatingAutosaveIndicator` de Página (`StructuredProfileEditor.tsx:671`) refleja SOLO el status del editor; los autosaves de notas/links de `BioRepoInputs` (montado en la misma hoja, `DoctorPaginaView.tsx:131`) no reportan a ningún indicador. Canon §2.6 pide UNA indicator por página — que agregue el status de la página, no solo de un grupo. Fix barato: lift del `useAutosave` status a `DoctorPaginaView` (o status combinado).

### WARN W5 — e2e D3-C/D3-E mockean el endpoint occurrences (el surface del fix) — burbuja de contrato
**Category:** 10 · `horarios-occurrences-d3c.spec.ts:94+` y `horarios-month-view.spec.ts:44+` pintan desde `page.route()` mock del MISMO endpoint cuyo consumo es el fix. La proyección BE está cubierta por la batería SC-D3C-1..8 (424 pytest) y el loop conjunto fue ejercido live (dod_evidence #2, re-verificado coherente por el auditor) — pero la suite committeada NO cazará un drift futuro de wire en ese endpoint (la clase de bug ×10 de esta story). Recomendado: 1 spec paint real-backend (patrón `staff-picker-switcher.spec.ts`, que SÍ es real-backend ✓). `bio-docs-d3b.spec.ts:30` además importa `expect` de `@playwright/test` (el `test` sí viene de `fixtures/base` ✓ — aceptable, anotado).

---

## Plan Carril C' (CHANGES_REQUESTED → dev-team; el endpoint compound NO lo construye el auditor per `auditor-self-fix-policy.md` v5)

Un solo round coherente "D3-D editor wire-contract", orden estricto:

1. **Reconcile shape (decisión /architect, 5 min):** el arch §6.1 declara `experiencia {puesto, lugar, anios}` + `certificaciones/idiomas string[]`. El editor FE inventó shape rico (cargo/desde/hasta/descripcion + objetos cert/idioma) que NADIE diseñó (mockup contenteditable no lo pinna). **Default recomendado: FE se alinea al arch** (opción B). Si Chris quiere el modelo rico → migrar domain+DTO+serializer BE (opción A, más cara).
2. **BE (RED first):** `PATCH /{doctor_id}/public-profile` en `doctors_router.py` — request DTO espejo de `PublicDoctorProfileDTO` secciones (camelCase in), service method que persiste `public_profile` JSONB SIN tocar `bio_generated_at` (RN-D3B-4) + audit row `doctor.public_profile_updated` + RBAC `_STAFF_MUTATION_ROLES` + `response_model=DoctorDetailDTO`. Batería: roundtrip + cross-tenant 404 + extra-key reject.
3. **FE types truth:** `staff.types.ts` — `StructuredExperiencia → {puesto, lugar, anios}`; `DoctorPublicProfile.certificaciones → string[]`; `idiomas → string[]`; borrar `StructuredCertificacion`/`StructuredIdioma` (o conservarlos SOLO si gana la opción A).
4. **FE consumers:** `page.tsx` público (render puesto/lugar/anios), `PhonePreview` (strings), `StructuredProfileEditor` (schema Zod + field arrays + hidratación + payload al shape final). RED first: unit test del hook que asserte **method+URL** (`PATCH …/public-profile`) + payload shape; test de hidratación con el JSON wire REAL (copiar el fixture del response live de este review).
5. **e2e + axe:** spec real-backend del editor (editar Sobre mí → recargar → persiste) + spec `/d/**` con `AxeBuilder` wcag2aa (SC-D3D-13) + assert visual de experiencia poblada.
6. **W1/W3/W4** en el mismo round (artículo "los", `max-w-80`, status agregado).
7. **Live-verify obligatoria del write del editor** (el que faltó en dod_evidence) antes de re-audit.

## Self-fix log (Carril A — mecánico, gate-verified)

| # | Fix | Files | Cobertura existente | Re-run |
|---|---|---|---|---|
| 1 | Consolidar `days_of_week`/`interval` en `CreateBlockPayload`/`UpdateBlockPayload` (estaban duplicados como extensión local "owned by parallel builder" ya obsoleta) | `staff.ts:645-659,700-711` + `BloquePopover.tsx:62-67` (aliases → base types) | tsc + `staff-blocks-api.test.ts` + vitest lisa | tsc 0 · eslint 0 · vitest lisa 489/489 ✓ |
| 2 | Docstring stale: `useTogglePublicVisible` decía `PATCH …/public-visible` (ruta inexistente); el código usa `PATCH /{id}` correcto — comment alineado al código | `staff.ts:1112-1114` | n/a (comment-only) | idem ✓ |

## Upstream deficiency

**/architect (`03-arch-delta.md`):** §6.2 declara el StructuredProfileEditor "inline + autosave" pero la tabla de endpoints (§3.1/§6.1) **nunca declaró el write que ese autosave necesita** — el builder FE quedó sin contrato y lo inventó (10ª instancia de contrato-imaginado en esta story, esta vez habilitada por el diseño). Además §6.1 fija `experiencia {puesto, lugar, anios}` y el ticket FE no citó ese shape como binding para el editor. **HB-71 filed** en `docs/process/harness-backlog.md` (refuerza HB-42: contract-test mecánico FE-hooks↔FastAPI-routes + checklist architect "superficie editable+autosave ⇒ write endpoint declarado o REFUSE ready").

## Live Verification Audit (ejercida por el auditor — stack dev real :8002)

- **Write crítico ejercido:** `PATCH /doctors/{id}` `{"visibleEnLanding":false}` → 200 → GET público **404** ("perfil no disponible" idéntico anti-enum, log `public_profile_doctor_not_found`) → PATCH `true` → 200 → GET público **200** (log `public_profile_served`). Efecto observado + logs BE sin traceback. ✓
- **Repro del FAIL F1:** `PATCH /doctors/{id}/public-profile` (headers RBAC completos) → **404**. ✓
- **Wire-truth capturado:** GET público live → `experiencia:null`, `certificaciones:["Colegiatura 12345 (PE)"]` (strings) — fixture para el round de fixes.
- dod_evidence del builder (×5, checkpoint): coherente con lo re-verificado, PERO no cubre el write del editor (gap que produce F1).

## Allowlist / Baseline Movement

- ui-kit ratchet: 266/266 sin movimiento ✓ · FE arch allowlists: sin crecimiento (187 pass) ✓ · ESLint: 0 errores, sin warnings nuevos en scope ✓

## Native-First / Parallel-safety Audit

- Gates corridos nativos ✓ · sin `make e2e*` ✓ · commits del rango por pathspec (revisados) ✓

---

**Resolution path:** dev-team ejecuta el Plan Carril C' (pasos 1-7) → gate-runner full → re-audit (iter 2/4). Los PASS de D3-A (switcher), D3-B (bio-docs), D3-C (occurrences), D3-E (mes), D3-F (editor recurrencia) y la página pública estructural NO se re-litigan — el re-audit se scopea a la superficie D3-D editor + W1-W5.
