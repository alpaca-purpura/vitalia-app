# RECONCILE-HANDOFF — vitalia-fase2-lisa-servicios

> **Para la conversación NUEVA.** Esta sesión llenó el contexto arreglando la tanda
> de errores de G round 2. Chris confirmó funcional OK ("ya, queda, por fin" ·
> 2026-06-19). Falta la **fase R (reconcile)** + cobertura total de documentación /
> capabilities / gherkins / tests en TODOS los niveles, ANTES de pasar al `/auditor`.
> Bootstrap sugerido: `/pm-vitalia` → "reconcile vitalia-fase2-lisa-servicios" (leer este file primero).

## Estado actual

- `state: developed` · `phase: AWAIT_CHRIS_VERIFY` (G).
- Todos los fixes funcionales **construidos + pusheados + gates verdes** (detalle abajo).
- Chris ejerció live y quedó conforme con el comportamiento. El `dod_evidence` lo ejerció Chris (mi lane no tiene sesión Clerk — ver § Gap infra).
- **NO** está hecho: R (reconcile docs↔realidad), cap F.3, gherkins de los escenarios nuevos, matriz de cobertura, validators reconciliados, learning capture, promoción ADR-009 al canon, spawneo de follow-up stories, `chris_verify.signoff` formal, handoff `/auditor`.

## Scope expandido en G round 2 — qué se construyó (commits)

| # | Finding | Fix | Commit(s) |
|---|---|---|---|
| G2-F1 | gutter padding cross-view (rule#34) | p-5/p-6 en LisaServiciosView + Shell leaf; StatusBar full-bleed | `9b3c0a13` |
| G2-F2a | activar sin aviso | AlertDialog confirm en ServiceStatusBar | `9b3c0a13` |
| G2-F2b | activar no refleja en workspace | useActivateServicio setQueryData(detail) | `9b3c0a13` |
| G2-F3 | crash EntityPicker deriveInitials(undefined) | caller guard vitalia + core hardening null-safe (@luana/ui-kit, proposal accepted) | `9b3c0a13` + ui-kit |
| G2-F4 | "Ver detalle" doctor → 404 | hrefs /lisa/staff (no /lisa/doctores) | `2eabe9bd` |
| G2-F5 | Performance measure negative timestamp (Next16 soft-nav redirect) | regex [offer-id]→resumen en N3_DEFAULT_LEAF | (commit en findings_round2b) |
| G2-F6 | plan-pago price 0 al refrescar | RHF values re-hidrata | `e7d5766f` |
| PlanPago-build | reserva/anticipo separados + Plan de pago completo (3-cobro) | wire BE ThreeChargePricing + canon UI | `91c01be9` |
| PEN fast-track | tenant+products+clerk a PEN | seed + DB live | `d6690e59` |
| G2-F7 | popover EntityPicker detrás de StatusBar | z-index en wrapper Radix (`[data-radix-popper-content-wrapper]`) | `a90b3b3b` |
| G2-F8 | "Fuentes de conocimiento" al fondo | movido al top del workspace | `022bf843` |
| G2-F9 | moneda catálogo/escalera ≠ tenant | data-fix PEN; `?? "USD"` → story currency | (data) |
| G2-F10 | detalle muestra SubSubTabsBar + back no origin-aware | detail-guard core + back origin-aware (?from=) | `0ec2dd84` |
| **G2-F11** | autosave laggy (ResumenView campos ricos `value={servicio.X}`) | 15 campos → RHF Controller + **arch-test gate** + ADR-vitalia-009 | `e6f97173` |
| **G2-F12** | "Para Adrián" Agregar pregunta/objeción → 500 | BE `_apply` coerce faq/objections dict→VO | `cc4a2ea9` (BE) + `54119aaf` (FE estado local) |
| **G2-F12b** | agregar par vacío → 500 (VO exige no-vacío) | FE filtra pares incompletos del payload | `5bfa7d4a` |
| **G2-F13** | Especialistas habilitados muestra UUID no nombre | BE enrich SpecialistLinkDTO via DoctorRosterPort (display_name+specialty, X-Clinic-ID opcional) + FE render nombre+especialidad+iniciales | `f40556ea` (BE) + `8a51ad4b` (FE) |
| **G2-F14** | plan-pago montos desaparecen + crash `reservation.enabled` al recargar | FE `defaultValues` full-shape + values re-sync + `?.` | `c0e89ca1` |
| **G2-F14b** | plan-pago montos VACÍOS al recargar (Decimal→string wire) | FE `toNum()` coerce string→number en pricingToFormValues | `2dc86a85` |

Docs/artefactos: `8e1f2b61`, `5a62fdef`, `600355c1`, `cf27df3d` (+ result files T-G2F1{1,2,3}-*.md, T-G2F11-result.md). **ADR-vitalia-009-autosave-field-contract.md** (accepted).

## Lo que la fase R DEBE hacer (proceso ya estipulado)

> SSoT del proceso: `.claude/rules/story-closure-gate.md` (Fase R) · `docs/process/capability-protocol.md` § F.3 · `.claude/rules/definition-of-done-live-verify.md` · `docs/process/spec-mapa-funcional.md` (matriz) · `.claude/rules/test-design-doctrine.md`.

1. **`01-spec.md` — Gherkin de TODOS los escenarios nuevos/cambiados** (el pedido central de Chris). Cubrir como mínimo:
   - Autosave value-from-local-state (Resumen + Para Adrián + Plan de pago): tecleo fluido, no procesa-cada-letra, persiste, recarga muestra lo guardado.
   - FAQ/Objeciones: agregar fila vacía NO guarda ni error; completar par (ambos campos) guarda; par incompleto no persiste.
   - Especialistas: muestra nombre + especialidad (no UUID); fallback id-corto si el roster no resuelve.
   - Plan de pago 3-cobro: precio/reserva/anticipo/financiamiento editables; calculados ≈equivale/≈por mes; recarga muestra montos (Decimal-string coercion); activar/price_publishable.
   - F7 (popover sobre StatusBar) · F8 (Fuentes arriba) · F10 (detalle sin SubSubTabsBar + back origin-aware) · PEN currency en catálogo/escalera/workspace.
   - **§ Matriz de cobertura** (Bif/RN/AC → Scenario → verificación REAL): poner cada ítem `✅ construido` con su test/ruta. Piso HARD: happy-path de cap `new` = `✅`.
2. **`04-validators.yaml`** — reconciliar: validators de scope DEFERIDO/descopado → `must_pass: false` + tag `deferred:` (HB-79, no dejar verde-fantasma). Agregar como validators los tests nuevos: `test-autosave-value-from-local-state.test.ts` (arch-fitness FE) + las regression (ResumenView sin-mock, ParaAdrianView empty-pair, EspecialistasView name, PlanPagoView string-amount + no-crash) + BE (sales_brief faq/objections VO, specialist enrich). `verification_nature: ambas` · `demo_required: true`.
3. **Capabilities F.3** — `vitalia/docs/product/capabilities/offer/lisa-servicios.yaml` (o el cap_id real): `cap_change_type` (extend para la ficha rica/plan-pago/especialistas; los fixes = change_log type=fix). Embeber `scenarios[]` (gherkin verbatim) + `business_rules` + `access` + `test_coverage` (rutas reales de los tests) + `dev_preview`. `make cap-doctor BRAND=vitalia` → **0 deriva** antes de cerrar. `status=live` requiere ≥1 scenario + e2e (cross_check_3 HARD).
4. **`modules/offer.md`** — regen (auto-list).
5. **Tests de todo nivel (cubrir el gap que Chris teme):**
   - Unit/component: ya hay regression de cada fix (verde). Verificar cobertura por naturaleza (test-design-doctrine).
   - **E2E Playwright** del happy-path del workspace de servicio (crear → editar ficha → plan-pago → especialista → activar) con auth-fixture real-backend (anti-burbuja `base.ts`). HOY FALTA — es el hueco más grande para el auditor.
   - **Contract-test FE↔BE** (HB-42, lección recurrente): el bug G2-F11/F14b nació de contratos imaginados (camelCase / Decimal-string). Agregar test que cruce el shape real.
   - Visual goldens 8 (pendientes desde antes).
6. **`dev_app_verified` / `dod_evidence`** — consolidar la evidencia live que Chris ejerció (writes reales + efecto). Sin esto `/pm-vitalia merge` REFUSE.
7. **Follow-up stories a spawnear (ledger deferred)** — visibles, no huérfanas:
   - `vitalia-tenant-currency-config` (kill `?? "USD"` en ServiceCard/RungColumn + primary/secondary ISO 4217 tenant-owned + flip test tenants). Absorbe G2-F9.
   - `adrian-ficha-rica-knowledge` + `accordion-dedup-cleanup` (ya citadas en checkpoint `reconciled` note).
   - Sub-phase B RAG (T-B1/B2/B3 · `/pm-luana` engine-lift · STOP-2).
8. **Promoción ADR-009 → canon platform §2.6** (value-binding HARD + autosave field contract): abrir proposal `/pm-luana` (`docs/promotion-protocol/proposals/2026-06-NN-autosave-value-binding-contract.md`). Cross-brand (React universal). Texto propuesto en ADR-009 §7.
9. **Learning capture (cross-brand candidate)** — la lección que se repitió **4 veces** esta tanda: *el verde del unit-test no reproduce el runtime* — (a) test que MOCKEA el hook bajo prueba congela su ciclo (G2-F11), (b) fixtures con `number` ocultan que el wire manda `string` Decimal (G2-F14b), (c) test que renderiza sin reproducir el timing de `values` (G2-F14), (d) test BE "par vacío no rompe" que no construye el VO por el path real (G2-F12b). **Regla emergente para test-design-doctrine: los regression deben usar el SHAPE REAL del wire + NO mockear el componente/hook bajo prueba.** Escribir `vitalia/docs/learnings/2026-06-19-unit-green-not-runtime-truth.md` (promotable: candidate) + pointer MEMORY. Extiende [[verification-real-not-200]] · [[dod-live-verify]].
10. **`chris_verify.signoff`** — formalizar (result: SATISFIED_WITH_FOLLOWUPS, listar los follow-up de §7 como open_items) → `reconciled: true` → **AUTO-HANDOFF `/auditor vitalia vitalia-fase2-lisa-servicios`**.

## Gap infra (harness-issue a abrir)

`/pm-vitalia` (yo) **no puede self-serve la live-verify**: el lane no tiene sesión Clerk (todo el `dod_evidence` lo ejerció Chris) + el FE OOMea (host ~3G libres). Para que Claude cierre la DoD #37 sin depender de Chris hace falta: lane-auth (Clerk testing token en el perfil Chrome del lane) + headroom de RAM del FE. Abrir vía `/harness-issue`.

## Anti-recurrencia ya cementada esta tanda

- **ADR-vitalia-009** + arch-test `test-autosave-value-from-local-state.test.ts` (gate HARD: ningún input editable con `value={queryData.x}` en hojas con autosave).
- El resto de los fixes llevan su regression. El auditor los encuentra en los result files + el cap `test_coverage`.

## Lección de proceso

Toda esta tanda fueron findings de la **live-verify de Chris** que los gates verdes NO cazaron. El valor de G (Chris ejerce antes del auditor) quedó demostrado. El reconcile debe dejar al `/auditor` un paquete donde cada comportamiento tenga gherkin + test real + cap, para que audite con qué.
