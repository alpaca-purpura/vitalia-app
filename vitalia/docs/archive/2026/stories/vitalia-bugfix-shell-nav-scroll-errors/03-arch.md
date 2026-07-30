---
story_id: vitalia-bugfix-shell-nav-scroll-errors
brand: vitalia
type: bugfix
arch_version: 1
schema_version: v4.3
architecture_pattern: ADR-vitalia-004        # fixes preservan el patrón shell existente (no construye sub-tab nueva)
adr_004_compliance: full                      # no diverge; corrige superficies existentes que ya siguen ADR-004
cap_target: null                              # higiene UX cross-cap del shell-organism (cap_change_type: fix)
cap_change_type: fix
last_modified: 2026-06-02T20:05:00-05:00
---

# 03-arch.md — Bugfix Shell-organism: routing / tenant-selector / scroll / títulos / placeholder / error-boundary

> **Naturaleza:** bugfix lite (ADR-011). El checkpoint.md es el spec-lite. Este 03-arch.md
> **mapea la causa raíz REAL de cada bug** (validada leyendo el código, no hipótesis PM) y
> dicta el fix mínimo + su verificación. Todo es **FE-only** (`vitalia/frontend/src/`).
> Cero backend, cero core, cero otra brand. Cero superficie nueva → no es isla (CONN trivial).

## Surfaces involved

- **BE:** no
- **AGENTIC:** no
- **FE:** sí — shell-organism chrome + routing + 3 feature views (lisa/marca) + 1 store/hook (iam/tenants)

## Prior art audit

`fix` sobre superficies existentes — **no introduce patrón nuevo** ni recrea abstracción. No hay
lift candidate ni consumo de engine nuevo. El único "prior art" relevante es el origen de la
regresión: la migración `valeria/agenda → mateo/agenda` de la story `vitalia-paradigm-map-zones`
T-5 (2026-05-30) movió la agenda pero **dejó 3 redirects apuntando a la ruta vieja** (Bug #1).
Engine consumido vía import (sin cambios): `@luana/hooks` (`createSsrSafePersistedStore`,
`useStoreHydration`). Net-new: solo 1 archivo nuevo `[agent]/error.tsx` (boundary genérico),
justificado en Bug #7.

---

## Mapa de causa raíz por bug (★ lo que Chris pidió: "mapear las causas")

### Bug #1 — Routing post-login → 404 · **CONFIRMADO (regresión de paradigm-map-zones T-5)**

**Síntoma:** tras login, `/{tenantId}` redirige a `/{tenantId}/valeria/agenda` → 404.

**Causa raíz REAL (más precisa que la hipótesis PM):**
- 3 redirects apuntan a `valeria/agenda`:
  1. `src/app/page.tsx:49` — root landing post-login
  2. `src/app/[tenantId]/(shell-organism)/layout.tsx:76` — redirect cross-tenant inválido
  3. `src/app/[tenantId]/(shell-organism)/page.tsx:33` — redirect `/{tenantId}` → default
- `agent-catalog.ts:315-320` → **`isValidAgent('valeria') === false`** (valeria es supervisor de
  sidebar, NO ribbon agent desde v1.2). `valeria/` no es segmento estático.
- Por tanto `/valeria/agenda` matchea la ruta dinámica `[agent]/[subtab]`, y `[agent]/layout.tsx:35`
  hace `notFound()` (agent inválido) → 404.
- La agenda **migró a `mateo/agenda`** (ruta estática real, en `SHIPPED_STATIC_SUBTABS`,
  `agent-catalog.ts:285-289`) durante `paradigm-map-zones` T-5, pero los 3 redirects no se
  actualizaron. **Es una regresión, no un diseño.**

**Fix:** redirigir a `mateo/agenda` (ruta estática válida que NO pasa por `isValidAgent`, renderiza
`mateo/agenda/page.tsx`). Para que no vuelva a driftear, introducir **un único SSoT**
`DEFAULT_LANDING_SUBPATH = "mateo/agenda"` en `src/lib/shell-routes.ts` y consumirlo en los 3
redirects (defensivo). Actualizar comentarios stale (`page.tsx:10-14`, `(shell-organism)/page.tsx:9-14`,
`layout.tsx`) + tests que referencian la ruta vieja (`(shell-organism)/not-found.test.tsx:88`,
`SubSubTabsBar.test.tsx:141`).

**Observado (latente, fuera de scope estricto):** `AGENT_CATALOG.valeria` (agent-catalog.ts:75-76)
aún tiene `tabLabel:"Operar"` + `defaultSubtab:"agenda"` (metadata muerta — valeria no está en el
ribbon). No causa el bug; limpieza opcional dentro de T-1 si el builder la ve trivial.

---

### Bug #2 — Selector de tenant no aparece con 1 tenant · **CAUSA CONTRIBUYENTE CONFIRMADA + repro-first obligatorio**

**Síntoma:** con un solo tenant, el `TenantSwitcher` del topbar no se muestra. Debe verse siempre.

**Hipótesis PM REFUTADA:** la PM suponía un guard `tenants.length <= 1`. **No existe.** El
`TenantSwitcher` solo oculta en `availableTenants.length === 0` (`TenantSwitcher.tsx:99`) o
`!activeTenant && !isLoading` (`:106`). El store `tenant-store.ts:72-79` **auto-elige el primer
tenant** cuando no hay activo → con 1 tenant debería mostrarse.

**Causa raíz contribuyente CONFIRMADA:** `useStoreHydration(useTenantStore)` **no se llama en
ningún lado** (grep verbatim: solo `useShellStore` se rehidrata en `ShellOrganismLayoutClient.tsx:99`).
El `tenant-store` usa `createSsrSafePersistedStore` con `skipHydration:true`; su propio doc
(`tenant-store.ts:29-31`) dice "REHYDRATION: call useStoreHydration(useTenantStore) from the first
client-side component that consumes this store" — **y nadie lo hace.** Consecuencia: el `activeTenant`
persistido nunca se restaura; el shell depende 100% del auto-pick de `useTenants`, y queda una
**ventana** donde `activeTenant=null` + `availableTenants=[]` con `isLoading=false` → `:106` retorna
`null` → selector invisible.

**Por qué igual es repro-first (ADR-011):** el modo de fallo COMPLETO no es determinable solo leyendo
código. Falta saber qué devuelve `/api/tenants` para el tenant dev-app `e69a691d-…` (¿lista vacía?
¿1 item?) y si `useTenants` (header `tenantId: userId`, `useTenants.ts:57-60`) resuelve bien tras el
fix de tenant-resolution no-Clerk-org (2026-06-01). **`/dev-team` DEBE reproducir en dev-app**
(login `dr.demo@vitalialat.com`, abrir topbar, inspeccionar Network `/api/tenants` + estado del store
con React DevTools + console) **antes de tocar código**, y confirmar/corregir el diagnóstico.

**Fix probable (a confirmar en repro):**
1. Llamar `useStoreHydration(useTenantStore)` en `ShellOrganismLayoutClient` (junto al de `useShellStore`,
   antes de cualquier branch — invariante D3) **o** en `TenantStoreBootstrap`. → restaura activeTenant persistido.
2. Si el repro muestra `/api/tenants` vacío → es bug de datos/endpoint del tenant dev-app, NO del switcher
   (escalar como hallazgo, posiblemente folded a otra story; documentar en impl-log).
3. Garantizar que con ≥1 tenant el trigger SIEMPRE se renderiza (estado de carga muestra Skeleton trigger,
   no `null`). Si se confirma que con 1 tenant debe verse aunque el dropdown tenga 1 sola opción, ajustar
   `:106` para no retornar `null` cuando hay `availableTenants.length >= 1`.

---

### Bug #3 — Títulos de hoja redundantes (eliminar en todas las hojas) · **CONFIRMADO**

**Síntoma:** cada hoja muestra un título arriba que duplica la opción ya marcada en la navegación.

**Causa raíz:** dos fuentes del título-eco:
1. **Dispatcher:** `SubTabContent.tsx:137` renderiza `<SubTabHeader agent subtab meta>` (h2 ícono+label
   con `border-b`) ANTES del placeholder. Cubre ~17 rutas placeholder. Para `ServiciosPlaceholder`
   (`:82` h2 "Servicios") y `ConexionesPlaceholder` (`:92` h2 "Conexiones") esto produce **doble título**
   (el del dispatcher + el propio del placeholder).
2. **N3 static lisa/marca:** cada vista repite su label como h2 arriba:
   - `IdentidadView.tsx:234` `<h2>Identidad</h2>`
   - `VozTonoView.tsx:197` `<h2>Voz y tono</h2>`
   - `PresenciaView.tsx:126` `<h2>Presencia</h2>` (en fila con `AutosaveBadge`)
   Estas duplican el label activo del `SubSubTabsBar`.

**Fix (regla):** eliminar el **título de hoja de nivel superior que ECO-a la opción de navegación**
(sub-tab o sub-sub-tab activa). Concretamente:
- Quitar `<SubTabHeader>` de `SubTabContent.tsx` (mata el eco para todas las rutas placeholder + el
  doble-título de Servicios/Conexiones). Si `SubTabHeader.tsx` queda huérfano → eliminarlo + su test
  (gate knip).
- Quitar el h2-eco superior de `IdentidadView` / `VozTonoView` / `PresenciaView` (conservar el
  `AutosaveBadge` de Presencia, re-alineado a la derecha sin el h2).
**Preservar (NO tocar):** headings de sección INTRA-contenido (no son eco de la nav): p.ej.
`DoctorPerfilView` "Identidad/Contacto/Profesional", `BioRepoInputs`, `GeneratedBioSections`,
`DayCalendar` (label de día). Son sub-secciones de formulario, `text-sm`.
**FUERA DE SCOPE (coordinación):** `lisa/staff/*` (`StaffDirectoryHeader.tsx:70` h1 "Staff") es
superficie de `vitalia-fase2-lisa-doctores` (developing, bucket `lisa`). **NO tocar acá** — flag
en impl-log para que lisa-doctores lo absorba (non-egoísmo).

---

### Bug #4 — No se puede hacer scroll (contenido fijo) · **CONFIRMADO + PRECISO (ALTA)**

**Síntoma:** el contenido de la hoja no scrollea (ni rueda ni barra). En todas las hojas.

**Causa raíz (más precisa que la hipótesis PM):** NO es `layout.tsx`. El `<main>`
(`ShellOrganismLayoutClient.tsx:210`) y el `<section>` de `AppPanelSlot` (`:47`) son correctamente
`overflow-hidden` (son el marco fijo del shell). El culpable es el **contenedor de contenido interno**:
`AppPanelSlot.tsx:61` → `<div className="flex-1 min-h-0 overflow-hidden">{children}</div>`. Ese div
es el ÚNICO que debería scrollear y tiene `overflow-hidden` → recorta el contenido de toda hoja.

**Fix:** `AppPanelSlot.tsx:61` → `overflow-hidden` ⇒ **`overflow-y-auto`** (mantener `flex-1 min-h-0`).
Una línea. Verificar: hoja con contenido largo scrollea (rueda + barra visible) y las hojas con scroll
interno propio (agenda) siguen OK (no doble-scroll roto).

---

### Bug #5 — Recuadro "Editor de landing pública — próximamente" en Presencia · **CONFIRMADO EXACTO**

**Síntoma:** Presencia (Lisa) muestra un callout placeholder a eliminar.

**Causa raíz:** componente `InfoBannerLandingDescoped.tsx:62` (texto literal "Editor de landing
pública — próximamente"), renderizado por `PresenciaView.tsx:145-148`. Exportado por la public API
`features/lisa/components/marca/presencia/index.ts:15-16`. Sin archivo de test propio.

**Fix:** quitar el render + import del banner en `PresenciaView.tsx`, remover los 2 exports de
`presencia/index.ts`, y **eliminar** `InfoBannerLandingDescoped.tsx` (gate knip — exported-but-unused).
**Scope:** SOLO ese recuadro. NO construir el editor (eso es `vitalia-fase2-lisa-landing-public`, idea).
**Coordinación con Bug #3:** ambos tocan `PresenciaView.tsx` → secuenciar (T-5 #5 antes de T-3 #3, o
mismo builder serial — ver DAG).

---

### Bug #7 — Un fallo bloquea toda la navegación (botones muertos) · **CONFIRMADO (ALTA)**

**Síntoma:** cuando algo falla, no se puede navegar a ninguna parte (chrome inutilizable).

**Causa raíz:** el ÚNICO error boundary del shell es `mateo/agenda/error.tsx` (una sola ruta).
No existe `[agent]/error.tsx` genérico, ni `(shell-organism)/error.tsx`, ni `app/error.tsx` /
`global-error.tsx` (find verbatim: solo `mateo/agenda/error.tsx`). Por tanto un throw en el contenido
de cualquier otra ruta **burbujea por encima del shell layout** hasta el error global por defecto de
Next.js → reemplaza la página entera → el chrome (Ribbon + SubTabsBar + ValeriaSidebar) muere → nav
bloqueada. (El loop infinito del Bug #6 — folded a lisa-doctores — disparaba exactamente esto.)

**Fix:** crear `src/app/[tenantId]/(shell-organism)/[agent]/error.tsx` (Client Component, patrón de
`mateo/agenda/error.tsx` pero genérico). Al vivir DENTRO de `(shell-organism)/layout.tsx` →
`ShellOrganismLayout` → `AppPanelSlot` (que renderiza Ribbon/SubTabsBar + `{children}`), el boundary
captura el error del sub-árbol `[agent]` y renderiza el fallback **en el slot de contenido**, dejando
el chrome y la navegación vivos + botón "Reintentar" (`reset()`). Esto **aísla el fallo al panel** y
de paso acota el blast-radius del Bug #6 antes incluso de arreglar el loop en lisa-doctores.

---

## Cross-cutting decisions

- **Tenant isolation:** sin cambios de query/PHI. Bug #2 toca solo el bootstrap no-PHI de tenants
  (entidades de negocio). Hooks ya usan `useTenantId()` post-fix 2026-06-01 (no Clerk org).
- **Spanish neutro:** todo texto user-facing nuevo/tocado (error boundary, fallbacks) en neutro LatAm.
- **PII / HIPAA-lite:** error boundary NO loguea PHI (solo `error.message` de render, igual que
  `mateo/agenda/error.tsx:41`). N/A en el resto.
- **SSR-safe store (ADR-vitalia-006):** Bug #2 fix #1 (rehidratar tenant-store) debe llamar
  `useStoreHydration` **dentro del chunk ssr:false** y con TODOS los hooks antes de cualquier branch
  (invariante D3 — no romper hook-count).

## Integration design (CONN) — no isla

- **Reachability:** todas las superficies ya están cableadas en el árbol de rutas + nav existente.
  El único archivo nuevo (`[agent]/error.tsx`) es **auto-registrado** por la convención de
  Next.js App Router (error.tsx = boundary del segmento) — no requiere include/registro manual.
- **Consumers:** el shell-organism (chrome) es consumido por todas las rutas `(shell-organism)/**`.
  Bug #2 consumido por `TopBarGlobal`. Bug #7 boundary consumido por todo `[agent]/**`.
- **Registration points:** ninguno nuevo salvo el filename-convention de `error.tsx`. Bug #1 SSoT
  `DEFAULT_LANDING_SUBPATH` consumido por los 3 redirects.
- **Home (zona/caja):** ZONA Plataforma · caja `configuracion` (chasis transversal del shell). `fix`
  sobre comportamiento existente → **no crea cap nueva**; al merge, change_log `type: fix` en la cap
  `shell-organism.shell-vitalia` (+ `brand_studio.lisa-marca` para #3/#5 en presencia/marca).

## Verificación — naturaleza + gates (Critical Rule #37)

- **Naturaleza:** **funcional** (todas user-reachable: routing, topbar, scroll, hojas, error UX).
- **technical_gates.baseline (siempre):** `tsc --noEmit` strict · `eslint --max-warnings 0` ·
  arch-fitness FE (`src/__tests__/architecture/`) · Vitest unit afectados.
- **opt-in:** ninguno (sin endpoint nuevo → no Schemathesis; sin domain-logic con invariantes → no
  Hypothesis/mutmut).
- **runtime_error_gate: required** — toda superficie FE se ejerce con el fixture `e2e/fixtures/base.ts`
  (pageerror / console.error / response ≥400 / overlay Next ausente). **★ Bug #7 + Bug #4 son el
  corazón:** el gate anti-burbuja debe pasar Y el contenido debe scrollear de verdad.
- **demo_required: true** (toca frontend user-reachable) → `demo-script.md` + `demo_signoff` Chris.
- **regression_guard:** tests de comportamientos NO tocados siguen verdes sin modificarse. Tests que
  referencian `valeria/agenda` (Bug #1) se actualizan revisando el diff (no `-u` mecánico).
- **DoD live-verify (ADR-vitalia-008):** cada bug se ejerce en `dev-app.vitalialat.com` autenticado
  (`dr.demo@vitalialat.com`) con Chrome DevTools MCP (acción real + console 0 errores + efecto) →
  `dod_evidence` en checkpoint. `GET 200` NO es evidencia.

## Files in scope (resumen — detalle en 06-tickets.yaml)

| Bug | Archivos | Tipo |
|---|---|---|
| #1 | `app/page.tsx` · `(shell-organism)/page.tsx` · `(shell-organism)/layout.tsx` · `lib/shell-routes.ts` (+const) · tests `not-found.test.tsx` `SubSubTabsBar.test.tsx` | edit |
| #2 | `ShellOrganismLayoutClient.tsx` (rehidratar) · `hooks/useTenants.ts` · `TenantSwitcher.tsx` · `stores/tenant-store.ts` (TBD repro) | edit (repro-first) |
| #3 | `SubTabContent.tsx` · `IdentidadView.tsx` · `VozTonoView.tsx` · `PresenciaView.tsx` · (knip) `SubTabHeader.tsx`+test · Servicios/Conexiones double-title | edit/delete |
| #4 | `AppPanelSlot.tsx` (1 línea) | edit |
| #5 | `PresenciaView.tsx` · `presencia/index.ts` · delete `InfoBannerLandingDescoped.tsx` | edit/delete |
| #7 | NEW `(shell-organism)/[agent]/error.tsx` | create |

**FUERA DE SCOPE (no tocar — non-egoísmo):** `lisa/staff/*` (lisa-doctores developing), backend,
core, otras brands, `components/ui/*` (Shadcn primitives).
