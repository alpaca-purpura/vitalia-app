# Cap Coherence Audit — vitalia + nicolify (2026-06)

> **Sweep del carril L4 del CIL** (`docs/process/continuous-improvement.md`). Owner: `/pm-vitalia`.
> **Objetivo:** que al entrar al cockpit se vea el efecto del harness bien ejecutado
> (proceso v5 + cap-deterministic HB-51 + cap-display HB-52, ya BUILT).
> **Método:** verify-first — diagnóstico sobre el FS real, NO sobre el audit viejo.
> **Fecha:** 2026-06-06 · **Worktree:** `~/Proyectos/luana-vitalia` (wip/vitalia).

## FASE 0 · Diagnóstico (cero edición)

| Check | Resultado |
|---|---|
| `cap_doctor.py --all-brands --strict` | **exit 1** · vitalia ✅ SANO (74) · comunify ✅ SANO (18) · **nicolify ❌ G6 ×2** |
| `make cap-gates BRAND=vitalia` | SOFT_DRIFT · G1-G7 **0 drift** · único drift = cross-check 4 (roles↔decorators) ×1 · cap-gate drift 0 · in HARD 0 |
| `make cap-gates BRAND=nicolify` | SOFT_DRIFT · **G6 drift ×2** · cap-gate drift 2 · in HARD 0 |
| `make caps-schema-check` | ✅ todas las brands schema-válido (0 errores) · vitalia 1 warning menor |
| `make machinery-check` | ✅ **68 checks · 0 fallos** · sin drift |

### Corrección verify-first vs estimación previa

El brief estimaba "vitalia ~2 sin user_facing_description". **Realidad medida: 0.** Todas las
43 caps `user_visible: true` de vitalia tienen `user_facing_description` → la sección
**«✨ Qué puedo hacer» (HB-52) muestra función real para TODAS**. Además se verificó que
`what_you_can_do` **no es campo del cockpit** — la display lee `scenarios` (rico) → fallback
`user_facing_description` (`ScenariosSection.tsx`). Conteos sobre `what_you_can_do` = ruido.

## Tabla por brand

### vitalia — 74 caps (43 visible)

| Métrica | Valor | Veredicto |
|---|---|---|
| 🔴 drift cockpit-breaking (cap_doctor G1-G7) | **0** | ✅ cockpit limpio |
| ⚠️ visible sin `user_facing_description` | **0** | ✅ todas muestran función |
| ⚠️ sin `scenarios` | **39** | L4 · riqueza opcional · cae al UFD · **NO bloquea** |
| jerga v3.x/F.3/migrará en texto user-facing | **0** real (1 "slice" en *nombre* de cap, cosmético) | ✅ |
| access-enforcement (cross-check 4) | **1** · `compliance.hipaa-lite-defensive-stack` | ⚠️ SOFT · no-display · ver Hallazgo V1 |

**35 caps ✅ plenamente coherentes** (UFD + scenarios). **39 caps** son ✅ coherentes para el
cockpit pero sin scenarios materializados (muestran el UFD funcional en «✨ Qué puedo hacer»,
sin jerga). Lista de las 39 sin scenarios:

```
eval-goldens-slice-1, lucas-daily-analysis, lucas-recommendation-tool, medical-agentic-tools,
medical-safety-guardrails, booking-widget-embed, brand-studio-medical-sections,
clinics-brand-extension, compliance-hipaa-lite-audit, whatsapp-template-registry,
oauth-meta-google-ads, registries-medical-vertical, inbox-tools-extensions, medical-kb-rag,
medical-pdf-extractors, valeria-wizard-onboarding-agentic, adrian-embudo, crm-consent-optout,
crm-scaffold-slice-1, re-engagement, fiscal-emission-pe, 3-clinic-fixture-latam,
attribution-matrix-4-origins, bowtie-funnel-5-stages, lucas-stage-recommendations,
referrals-leaderboard, medical-services-offer-preset, clinic-onboarding-3step,
wizard-brand-studio-slice-1, patient-records-medical-history, payment-gateways-latam-recurring,
vertical-medical-extension-sdk, adrian-3-tools-mvp, adrian-reengagement-tool, medical-guardrails,
sales-agent-state-overlay, empty-states, layout-5050, treatment-followup-workflow
```

### nicolify — 3 caps (1 visible)

| cap | estado | qué falta |
|---|---|---|
| `abel.icp-buyer` (uv=true, status=**wip**) | ⚠️ sin `user_facing_description` | **PERO tiene `scenarios`** → cockpit muestra la lista rica igual. UFD ausente = cosmético (backfill chico) |
| `shell-organism.shell-nicolify` (uv=false, live, infra) | 🔴 **G6 drift** | no tiene NI `functional_area` NI `map_box` → G6 lo ve "live sin caja" |
| `nicolify-platform-brand-runtime-foundation` (uv=false, live, infra) | 🔴 **G6 drift** | declara `map_box: plataforma-tecnica` (válido) pero **G6/resolver leen `functional_area`** (vacío) → no deriva de map_box |

## Hallazgos detallados

### 🔴 N1 · nicolify G6 ×2 — raíz CONFIRMADA: **cap-content** (faltan `functional_area`)
> **Hipótesis inicial "harness-gap" REFUTADA por data dura (verify-first).** El gate G6 es
> consistente y correcto. La evidencia cross-brand:

| Brand | SYSTEM-MAP | caps infra/shell live | declaran `functional_area`? | G6 |
|---|---|---|---|---|
| **vitalia** (referencia) | SÍ → G6 corre | shell-vitalia, design-tokens, product-map-zonas | **SÍ** (`plataforma-tecnica.shell`, `.platform`, `.map`) + map_box adicional | ✅ 29/29 pass |
| **comunify** | **NO** → G6 skipped (vacuo) | 18 live sin fa ni map_box | no | ✅ SANO (G6 no corre) |
| **nicolify** | SÍ → G6 corre | shell-nicolify, brand-runtime-foundation | **NO** (cero functional_area) | ❌ 2 drift |

- `shell-nicolify`: NO tiene `functional_area` NI `map_box` (cero campo de hogar).
- `nicolify-brand-runtime-foundation`: tiene `map_box: plataforma-tecnica` pero **NO** `functional_area`; G6 valida `functional_area` (que es el formato `<box>.<area>`, el alias-área del resolver), no `map_box`.

vitalia PRUEBA que el gate funciona cuando la cap declara `functional_area` (formato `<box>.<area>`).
Las caps de nicolify simplemente **nunca recibieron `functional_area`** (predatan la dimensión
v3 — schema la marca opcional, pero G6 la requiere para colocar una cap live en un brand que
TIENE SYSTEM-MAP). **No es un bug de gate; es backfill de cap-content.**

**Fix correcto:** agregar a las 2 caps nicolify `functional_area: plataforma-tecnica.<area>`
(infra zone, box `plataforma-tecnica` ya existe en su SYSTEM-MAP), espejo de vitalia. **Jurisdicción
`/pm-nicolify` · cross-worktree `~/Proyectos/luana-nicolify`.** NO se toca desde el worktree vitalia.

Son `user_visible: false` (infra): NO producen "caja vacía" en el mapa de valor principal,
pero SÍ aparecen como huérfanas en el panel `/drift` del cockpit nicolify (:4001).

> **Nota harness (opcional, no-bug):** el schema declara `functional_area` *opcional* (legacy
> comunify/nicolify) mientras G6 la hace *requerida* para caps live en brands con SYSTEM-MAP.
> Tensión latente, no incorrecta. Mejora posible: el `drift_reason` de G6 podría sugerir
> explícito "agregá `functional_area: <box>.<area>`" para caps legacy. Candidato L1 menor, no bloquea.

### ⚠️ V1 · vitalia cross-check 4 — `compliance.hipaa-lite-defensive-stack`
La cap declara `requires_role: [admin_clinic, staff_vitalia]` sobre
`/api/v1/vitalia/medical-compliance/events` pero el validador no encontró mecanismo de
enforcement reconocido (`@require_phi_access` / `require_brand_owner_access` /
`_assert_phi_access` / frozenset inline). **SOFT_DRIFT, NO-HARD, no afecta el display.** Es
access-control (potencialmente stake-asimétrico/seguridad) → NO auto-fix, decisión de Chris:
¿el endpoint usa un mecanismo no reconocido por el validador (→ ampliar validador) o le falta
el decorator (→ gap real de enforcement, bugfix vitalia)?

## Veredicto

- **vitalia cockpit YA está limpio** para el efecto buscado: 0 drift cockpit-breaking, 0 caps
  visibles sin función en «✨ Qué puedo hacer», 0 jerga de versión en texto user-facing. El
  harness (v5 + HB-51 + HB-52) se ve bien ejecutado **sin tocar nada**.
- **nicolify tiene 2 drift G6 reales** = **cap-content** (faltan `functional_area`), NO harness-gap
  (refutado). Fix `/pm-nicolify` cross-worktree. + 1 UFD cosmético (`abel.icp-buyer`, tiene scenarios).
- Las 39 vitalia sin scenarios = **L4 riqueza opcional**, no bloquean.

## Ratificación Chris (2026-06-06)

1. **vitalia 39 sin scenarios → dejar como L4** (sin backfill · anti-mass-invent). ✅
2. **nicolify G6 → ruta "harness-gap" ratificada, REFUTADA por verify-first, RE-RATIFICADA
   como cap-content** (Chris 2026-06-06: "cap-content /pm-nicolify"). La data prueba que es
   cap-content (faltan `functional_area` en 2 caps infra), no un bug de gate. NO se editó el
   harness. **TODO `/pm-nicolify` (cross-worktree `~/Proyectos/luana-nicolify`):** agregar
   `functional_area: plataforma-tecnica.<area>` a `shell-organism/shell-nicolify.yaml` +
   `platform/nicolify-brand-runtime-foundation.yaml`, espejo de vitalia. Hasta entonces
   `cap_doctor --all-brands --strict` queda en exit 1 por nicolify (esperado).
3. **V1 vitalia compliance → flag para bugfix story `/pm-vitalia`** (no investigar ahora). ✅

## FASE 3 · Live-verify cockpit vitalia — evidencia (Chrome DevTools MCP)

> **Hallazgo principal de FASE 3 (verify-first doble): el source está CORRECTO; el cockpit
> que estaba corriendo servía un BUILD STALE pre-HB-52.** Sin ejercer el cockpit vivo no se
> habría detectado: el scan de FS (source) daba limpio, pero lo que Chris VE al abrir el
> cockpit mostraba jerga.

### 🔴 F3-1 · Cockpit stale build (pre-HB-52) — defeats el objetivo
- El cap-drawer de `lisa-marca` (:4002, instancia corriendo) mostraba en **«✨ Qué puedo hacer»**:
  *"Cap todavía v3.1 · migrará a v3.2 cuando la próxima story la toque (Fase F.3 enforce)."*
  = **exactamente la jerga v3.x/F.3/migrará** que este sweep busca eliminar.
- **Raíz:** la instancia corría `next start -p 4002` (build de **producción**, uptime 7 h 45 m)
  servida desde un `.next/` compilado **antes** del fix HB-52. `next start` NO recompila ante
  cambios de source. El string literal "migrará a v3.2" existe SOLO en
  `.next/dev/server/chunks/ssr/*.js` (build viejo), **NO** en el source ni en ninguna cap YAML
  ni en el API `/api/capabilities/status`.
- El source actual (`ScenariosSection.tsx` HB-52) cae correctamente a `user_facing_description`
  + "Disponible en: {how_to_navigate}" — cero jerga.
- **Remediación verificada:** relancé el cockpit desde source actual (`PORT=4099
  scripts/cockpit-up.sh` → `next dev`, Turbopack). El cap-drawer de `lisa-marca` ahora muestra
  en **«✨ Qué puedo hacer»**: *"El workspace donde la clínica configura su identidad completa:
  nombre, logo, paleta de colores, tipografía y equipo médico… voz y tono con los 4 arquetipos
  de salud y frases prohibidas… presencia web…"* + *"Disponible en: Login → ribbon → Lisa →
  Marca…"* — **CERO jerga v3.x/F.3/migrará**. Screenshot: `cap-coherence-fase3-lisa-marca-clean.png`.

### Evidencia estructural (cap-coherence, lo que sí valida este sweep)
| Verificación | Resultado |
|---|---|
| `/drift` (panel verified-live) | renderiza · 0 errores de orphan-header / "caja vacía" estructural · (52/68 no-verificadas-live = métrica DoD #37, **otra cosa** que cap-coherence) |
| `/map` (paradigma 3 zonas) | Agentes / Plataforma / Infraestructura · cajas con nombres + descripciones user-facing en español neutro · cero jerga · cero caja huérfana |
| cap-drawer `lisa-marca` «✨ Qué puedo hacer» (source actual) | función real (UFD + "Disponible en") · **0 jerga** ✅ |
| Consola | limpia · único 404 = `favicon.ico` (inocuo) · `/api/capabilities/status?brand=vitalia` → 200 · `/api/watch` → 200 |

### Remediación durable (aplicada · Chris ratificó "relanzar canónico :4002")
La instancia stale (`next start`) quedó **detenida**. El cockpit canónico **:4002** se relanzó
con `make cockpit-up` (`next dev`, source actual) y se **re-verificó live**: el cap-drawer de
`lisa-marca` muestra en «✨ Qué puedo hacer» la función real + "Disponible en:" — **CERO jerga**.
El fix durable de fondo (HB-55): `make cockpit-up` debe preferir `next dev` (recompila) o
rebuild + estampar SHA del build en el footer; el port-check de `scripts/cockpit-up.sh` debería
filtrar solo LISTEN (el socket residual de Chrome MCP retenía el bind ESTABLISHED de :4002, no es
un listener real).

## Veredicto FASE 3
✅ El **source** del harness (proceso v5 + HB-51 + HB-52) está bien ejecutado: «✨ Qué puedo
hacer» muestra función real, cero jerga, paradigma 3-zonas limpio. El **efecto que Chris VE**
dependía de que el cockpit sirviera source fresco → la instancia stale lo ocultaba. Remediado +
verificado live en :4099.
