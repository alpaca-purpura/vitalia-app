---
story_id: vitalia-shell-core-hardening
brand: vitalia
type: ui-story
state: refined
architecture_pattern: ADR-vitalia-004   # punto 7 (N3 list/detail) lo invoca; wrapper cambios citan ADR-vitalia-006 (shell-state)
po_ux_version: 1                        # v1 de la UMBRELLA — reconcilia el backbone v3 del responsive (firmado) + deltas
spec_round: 2                           # RONDA 1+2 integradas — ver § Firmas y herencia
input_spec_signed: true                 # ★ firma única de reconciliación Chris 2026-06-10 ("Confirmo todo") — cubre deltas dark/B1/race + herencia FIRMA 1 backbone
mockup_final_signed: true               # ★ herencia del mockup firmado (shell-valeria-states.html, backbone 2026-06-06) RATIFICADA Chris 2026-06-10 + caveat behavior-fi re-confirmado ("a nivel UI me gusta como está actualmente")
ratified_by_chris: true
cross_module_scope: [shell, clinics, crm]
cap_target: null                        # higiene UX cross-cap del shell-organism (transversal, sin agente)
cap_change_type: fix
backbone_spec: vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/01-spec.md   # v3, 2 firmas (2026-06-06) — integrado verbatim acá
---

# 01-spec — vitalia-shell-core-hardening (v1 · spec unificado del chrome)

> **Qué es:** spec ÚNICO del hardening del shell-chrome. Integra **verbatim** el backbone firmado (`vitalia-bugfix-shell-valeria-responsive` 01-spec v3, 2 firmas Chris 2026-06-06 — puntos 1-7) + los deltas de la consolidación (ratificados Chris 2026-06-10): **dark-mode token-audit** (BUG #2, antes out-of-scope → ENTRA) · **B1 soft-nav hang** (root cause `ssr:false`) · **race-fix SC-3 generalizado** · **U3 trazado**. Deltas marcados **★ UMBRELLA**.
>
> **Regla de herencia:** lo firmado del backbone NO se re-litiga. Los deltas son adiciones de comportamiento; el material visual nuevo = cero (el mockup firmado ya incluye dark + estados + viewports).

## § Firmas y herencia (proceso v5 · 2 firmas)

| Firma | Fuente | Estado |
|---|---|---|
| FIRMA 1 (funcional, puntos 1-7) | backbone v3 `input_spec_signed: true` (Chris 2026-06-06) | **HEREDADA** |
| FIRMA 2 (mockup FINAL `shell-valeria-states.html`) | backbone v3 `mockup_final_signed: true` (Chris 2026-06-06: "confirmo" + caveat design-system) | **HEREDADA** — mockup vive en `vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html` |
| Firma de reconciliación (deltas ★ UMBRELLA: dark-in-scope + RN-14/15/16 + AC-12/13/14 + SC-20/21/22) | esta umbrella | **PENDIENTE** — una sola firma cubre input_spec + ratifica herencia del mockup |

Los deltas NO introducen forma visual nueva (B1/race = comportamiento de navegación/splitter; dark = lo existente renderizado correcto en dark, ya visible en el toggle dark del mockup firmado) → no se requiere mockup nuevo. Si el architect detecta superficie visual nueva → vuelve a /po-ux.

## Prior art applied

Scan ejecutado sobre el shell-organism real + brands activas (anti-duplication-refining). **Esta story NO crea primitivas nuevas — modifica el wrapper existente + cementa un patrón ya construido + corrige tokens.**

- **Wrapper del shell (modificado, no recreado):**
  - `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` — topbar (puntos 1+2)
  - `vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx` — chip web/agéntico DISABLED (punto 1 = eliminar)
  - `vitalia/frontend/src/stores/shell-store.ts` — `valeriaState{collapsed,rail,full}` + `shellMode{agentic,web}` (puntos 1,3,5,6 = refactor de la máquina de estados)
  - `vitalia/frontend/src/components/shared/shell-organism/{ValeriaSidebar,ValeriaRail,ValeriaHistory,ValeriaChat,ChatHeader}.tsx` (punto 6)
  - `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts` — `FULL_STATE_MIN_VIEWPORT=1104` calculado con Valeria=620px (punto 4 = recalc para 30/70)
  - ★ UMBRELLA `vitalia/frontend/src/app/globals.css` — utilities `vt-*` sin variante `[data-theme="dark"]` (dark token-audit)
  - ★ UMBRELLA layout del shell `app/[tenantId]/(shell-organism)/layout.tsx` + `dynamic({ssr:false})` — root cause B1 (soft-nav hang)
- **Patrón N3 list/detail (cementar, ya construido en 3 lugares — punto 7):**
  - `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` — N3-**dynamic** entity workspace nav (la pieza canónica del list/detail). `[‹ raíz] | [avatar entidad] | [leaf tabs]`. ADR-vitalia-004 § D-1.
  - `vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx` — N3-**static** (catálogo `AGENT_SUBSUBTABS`). Complementaria, no es el list/detail.
  - Consumidores LIVE: `lisa/staff` (directorio → workspace doctor), `adrian/embudo` (lista → lead workspace), nicolify `abel/icp`.
- **Engine consumed:** `@luana/hooks/create-ssr-safe-persisted-store` (store SSR-safe, ADR-vitalia-006). No recrear. ★ UMBRELLA: target del lift = `core/@luana/ui-kit` v0.3.0 (YA existe — `src/layout`, `src/archetypes`; proposals `accepted` 256517a3); el hardening apunta a él (lift-durante, ratificado 2026-06-10).
- **Learnings aplicados:** `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` (B1: `ssr:false` + soft-nav → "Rendered more hooks"; nav dura no trippea; fix sugerido edge-redirect) · `vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md` (race hydration) · `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` (nicolify factorizó mejor) · ADR-vitalia-006 (4 técnicas fallidas de persistencia).
- **Lift candidates detectados:** el wrapper del shell completo está en proposal `accepted` de lift a `@luana/ui-kit` (256517a3) — esta story ES la ruta crítica + vehículo (lift-durante). El patrón N3 (`EntityWorkspaceLayout`) converge cross-brand vía el lift.
- **Net-new justificado:** modelo de estados legacy-push (punto 6) — net-new para AMBAS marcas. Tira-avatar estado A (RN-12).

### Nicolify comparison (heredada del backbone — resumen)

Nicolify = port re-skinneado del mismo shell (Valeria→Luana). Punto 6 (push) nuevo para ambas · `ShellModeToggle` muerto en ambas (quitar = lift candidate) · `EntityWorkspaceLayout` de nicolify es la mejor factorización del N3 → se porta a vitalia (punto 7) · ambas convergen vía `@luana/ui-kit`. /po-ux vitalia NO toca nicolify.

---

## § Context · Dónde vive

### Zona / caja del mapa

- **Zona:** Infraestructura → caja **plataforma-técnica** (el shell-organism wrapper es superficie no-funcional). `map_zone: infraestructura`.
- **Excepción punto 7:** el patrón N3 habilita superficies de agente (staff = Lisa, embudo = Adrián), pero el patrón vive en el shell (transversal).

### Shell que aplica

`vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`. Esta story TOCA el contrato en 4 ejes: topbar, panel Valeria, nav N3, ★ UMBRELLA tokens dark. El contrato se actualiza como parte de la story.

### Dónde aterriza el usuario

Todo el shell: `app/[tenantId]/(shell-organism)/**`. Cambios transversales — TODAS las sub-tabs de agente + Plataforma. No hay ruta nueva.

### § Design system constraint (caveat Chris 2026-06-06 · HARD — heredado)

El mockup `shell-valeria-states.html` es **behavior-fi, NO pixel-fi**. La implementación real DEBE seguir los lineamientos UI vigentes:

- **Design system first (D1):** átomos `components/ui/` + tokens `globals.css` / `@luana/design-tokens` + moléculas `components/shared/`. NO inventar primitivas del mockup. ★ UMBRELLA: componer del `docs/architecture/luana-platform/design-system-canon.md` (EntityWorkspaceLayout/EntitySubNavBar son piezas del canon).
- **Wrapper fidelity:** topbar, ribbon, sub-tabs, ValeriaChat, logo gradient, agent-colors shipped se conservan — cambia COMPORTAMIENTO + posición, no re-estiliza.
- **SSoT visual:** SHELL-DESIGN-CONTRACT + skill `vitalia-design-system`. Avatar Valeria = asset del catálogo (no placeholder "V").
- ★ UMBRELLA **Dark mode AHORA EN SCOPE** (supersede el "NO tocar" del backbone — ratificado Chris 2026-06-10): token-audit acotado (`vt-*` + fondos/borders/text sin variante dark) para que shell + contenido sean consistentes. NO es rediseño de tema: el wiring (`next-themes` + `[data-theme="dark"]` + tailwind darkMode) es correcto y se conserva.
- **Regresión cero:** sub-tabs ya `done` siguen funcionando tras el wrapper nuevo (AC-10).

### Out-of-scope explícito (anti-creep)

- ❌ ~~Dark mode~~ → ★ UMBRELLA **ENTRA** (supersedido 2026-06-10).
- ❌ ContactSidebarToggle del inbox — ya existe (BUG #3 del observed-bug).
- ❌ Cambiar el contenido de cualquier sub-tab de agente (solo wrapper + patrón N3 + tokens).
- ❌ Rediseño del sistema de temas (wiring next-themes correcto — solo variantes faltantes).
- ❌ Construir instancias N3 NUEVAS — solo portar `EntityWorkspaceLayout` + migrar staff/embudo.
- ❌ Tocar nicolify — cross-brand vía `/pm-luana` + lift.
- ❌ Formalizar el lift (proposal final + versionado ui-kit) — gobernanza `/pm-luana`; esta story construye apuntando al target.

---

## § Mapa funcional

### Happy path (camino dorado narrado)

1. El usuario entra al shell (cualquier sub-tab, ej. Adrián → Inbox). Desktop ≥1280: **topbar** (logo izquierda · `[🌙 tema][▼ Clínica Sanaré]` pegados a la derecha · sin chip "agéntico/web") + **Valeria ~30%** (chat, sin historial) + **agente ~70%**.
2. Trabaja en el agente (70% usable). Valeria presente sin exprimir.
3. Abre el **historial** → empuja: Valeria se ensancha (historial 260px fijo + chat), el agente se angosta. Lo cierra → el agente recupera ancho.
4. Colapsa Valeria (botón propio en su cabecera) → tira fina ~44px con el avatar; agente 100%. (Historial abierto también se cierra.)
5. Clic en la tira/avatar → Valeria reabre solo el chat (estado B), 30/70.
6. Achica la ventana (<1024) → Valeria pasa a **drawer/overlay**; agente 100%; burger en topbar.
7. En una sub-tab lista/detalle (Lisa → Staff): directorio → clic doctor → workspace con barra N3 `[‹ Staff] [avatar Dr.] [Perfil · Horarios · Servicios]`; `[‹ Staff]` regresa. (Mismo patrón Adrián→Embudo.)
8. ★ UMBRELLA Activa el **tema oscuro** (toggle 🌙) → **todo el shell Y el contenido del agente** pasan a dark consistente (topbar, Valeria, inbox, staff, embudo — sin "mitad clara").
9. ★ UMBRELLA Navega entre tabs/sub-tabs con **navegación blanda** (links internos, goBack, chips) repetidamente → cada superficie monta sin colgar (sin "Cargando shell" eterno, sin burbuja Next).

### Bifurcaciones (árbol de decisión)

```
Viewport del usuario
├─ ≥1024 (desktop) → Valeria INLINE SPLIT (resizable)            [Bif-1]
│   └─ Estado de Valeria (máquina nueva):
│       ├─ A · CERRADA → tira fina 44px (AVATAR destacado); agente 100%      [Bif-2a]
│       │     └─ clic AVATAR → abre a B (chat-only, NO restaura historial)   [Bif-2b]
│       ├─ B · ABIERTA (chat) → 30/70; sin historial (DEFAULT fresh)         [Bif-3]
│       │     ├─ botón colapsar (cabecera) → A                               [Bif-3a]
│       │     ├─ botón historial → C                                         [Bif-3b]
│       │     └─ botón "+" nueva conv → limpia chat + conv actual→historial  [Bif-3c]
│       └─ C · ABIERTA + HISTORIAL → historial EMPUJA (Valeria↑ agente↓)     [Bif-4]
│             ├─ cerrar historial → B                                        [Bif-4a]
│             └─ botón colapsar → A (historial también colapsa)              [Bif-4b]
│   └─ Ancho [1024,1280): Valeria clamp a min ~320px, agente toma resto      [Bif-5]
├─ <1024 (tablet/móvil) → Valeria DRAWER/overlay; agente 100%; burger        [Bif-6]
│   ├─ burger → abre drawer (historial apilado + chat)                       [Bif-6a]
│   └─ cerrar drawer (colapsar / backdrop / Esc) → agente 100%               [Bif-6b]
├─ Sub-tab tipo lista/detalle (N3-dynamic, transversal)
│   ├─ sin entidad → modo DIRECTORIO (lista; leaf tabs disabled)             [Bif-7a]
│   └─ con entidad → modo WORKSPACE (EntitySubNavBar: ‹raíz · avatar · leafs)[Bif-7b]
├─ ★ Tema del usuario                                                        [Bif-8]
│   ├─ light → todo light (estado actual, sin cambios)                       [Bif-8a]
│   └─ dark → shell + contenido del agente CONSISTENTES en dark              [Bif-8b]
└─ ★ Tipo de navegación interna                                              [Bif-9]
    ├─ nav dura (URL directa / reload) → monta limpio (ya funciona)          [Bif-9a]
    └─ nav blanda (Link/router.push/back) → monta limpio SIN colgar          [Bif-9b]
```

### Reglas de negocio (invariantes)

Heredadas verbatim del backbone (firmadas):

- **RN-1** — Shell siempre en modo agéntico. No existe "modo web" (chip + `shellMode` + acople eliminados).
- **RN-2** — Switcher de tenant en el cluster derecho del topbar, al extremo (orden `[🌙 tema][▼ tenant]`).
- **RN-3** — Default fresh: Valeria abierta en chat (B), historial colapsado, split 30/70.
- **RN-4** — Split resizable; default 30/70 solo sin valor persistido (ADR-vitalia-006).
- **RN-5** — Colapsar Valeria colapsa también el historial. Reabrir nunca restaura historial (reabre a B).
- **RN-6** — Abrir historial con Valeria cerrada → abre Valeria también.
- **RN-7** — El historial EMPUJA con ancho FIJO ~260px; el chat sigue resizable. *(Reconcile 2026-06-11: el ancho real construido es **280px** — columna del grid shipped; ratificado por Chris en chris_verify.rounds[1]. El push es REAL: ensancha el panel, nunca roba al chat; min efectivo en C = chat-min + 280.)*
- **RN-8** — [1024,1280): clamp ~320px; <1024: drawer. Min-width legacy 620px eliminado.
- **RN-9** — Botón colapsar propio y visible (cabecera Valeria). Rail 60px eliminado.
- **RN-10** — Patrón N3 canónico: directorio → workspace (`EntitySubNavBar`); sin entidad leafs disabled. Contrato para futuras sub-tabs list/detail.
- **RN-11** — Preferencia de Valeria (cerrada/abierta + ancho) persiste SSR-safe; historial NO persiste abierto.
- **RN-12** — Reabrir desde A: affordance = avatar de Valeria (atractivo + descubrible).
- **RN-13** — Botón "+" nueva conversación: limpia chat + archiva la actual al historial.

★ UMBRELLA nuevas (ratificadas Chris 2026-06-10):

- **RN-14** — **Toda navegación blanda interna del shell monta sin colgar.** El shell no depende de hard-nav para funcionar: el band-aid hard-nav del chip `frozen-kpi-badge` (board→recuperar) se REVIERTE a soft-nav una vez resuelto el root cause (`dynamic({ssr:false})` + soft-nav → "Rendered more hooks", Next 16.2.3). El mecanismo (eliminar `ssr:false` / edge-redirect / otro) lo decide `/architect`; el invariante de producto es: soft-nav confiable.
- **RN-15** — **Todo token/clase de color user-facing del shell + features que viven en él tiene variante `[data-theme="dark"]`.** Dark consistente: shell (topbar/Valeria) Y contenido del agente (inbox/staff/embudo/etc.) oscuros a la vez. Wiring de tema existente (next-themes + tailwind darkMode) se conserva — solo se completan variantes faltantes (`vt-*` + fondos/borders/text hardcodeados).
- **RN-16** — **Interacción inmediata post-carga es segura** (generaliza el race SC-3 del layout-5050): drag del splitter inmediatamente después de hidratar respeta los clamps de la máquina nueva (sin estados intermedios inválidos, sin snap roto, sin pisar la preferencia persistida). Cubre la secuencia transición→reload→transición→reload→drag.

### Criterios de aceptación (feature-done)

Heredados verbatim (firmados): **AC-1** sin chip web/agéntico + grep `shellMode` = 0 · **AC-2** switcher al extremo derecho · **AC-3** fresh = B 30/70 · **AC-4** splitter resizable + persiste · **AC-5** colapsar propio → tira-avatar → reabrir por avatar · **AC-6** historial empuja 260px fijo y revierte · **AC-7** [1024,1280) clamp 320 sin rail 60px · **AC-8** <1024 drawer + burger · **AC-9** N3 refactorizado real (`EntityWorkspaceLayout` portado + staff y embudo migrados + contrato cementado) · **AC-10** sin regresión cross-tab en sub-tabs done · **AC-11** "+" nueva conversación funcional.

★ UMBRELLA nuevos:

- **AC-12** — Dark mode consistente: con `data-theme="dark"`, CADA sub-tab shipped (lisa/marca, adrian/inbox, adrian/embudo, lisa/staff, mateo/agenda) renderiza shell + contenido oscuros — cero superficies "mitad claras"; grep de clases `vt-*` sin variante dark = 0 en superficies user-facing. [RN-15]
- **AC-13** — Soft-nav confiable: navegar blando entre tabs/sub-tabs (incluido board→recuperar tras revertir el band-aid a soft-nav) ×N ciclos monta siempre, sin "Cargando shell" colgado, sin "Rendered more hooks", sin burbuja Next. El band-aid hard-nav del frozen-kpi-badge está revertido. [RN-14]
- **AC-14** — Drag inmediato post-carga: en cualquier secuencia de transiciones de estado + reloads, un drag inmediato del splitter produce un ancho válido dentro de los clamps (sin snap inválido ni clobber de preferencia). El `test.skip(true)` de `resize-and-state.spec.ts:114` se reactiva (adaptado a la máquina nueva). [RN-16]

---

## § Wireframes

> **Mockup FINAL (firma 2 HEREDADA):** `vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html` — tokens verbatim de `globals.css`; toggles estados A/B/C, viewports 1280/1100/800, N3 directorio↔workspace, **dark** (el toggle dark del mockup ES la referencia de comportamiento esperado para AC-12). Servir: `cd vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups && python3 -m http.server 8888`.
>
> Los deltas ★ UMBRELLA no introducen forma nueva (ver § Firmas). Wireframes ASCII del backbone aplican verbatim (topbar · estados A/B/C · drawer · N3) — ver `backbone_spec` § Wireframes; no se duplican acá.

---

## § Gherkin scenarios

> SC-1..SC-19 heredados **verbatim** del backbone (firmados — texto completo en `backbone_spec` § Gherkin; el architect los consume desde AMBOS archivos o este como índice): SC-1 default fresh 30/70 · SC-2 sin toggle web/agéntico · SC-3 switcher derecha · SC-4 splitter persiste · SC-5 colapsar/tira-avatar/reabrir · SC-6 historial empuja 260 · SC-7 historial desde A abre Valeria · SC-8 "+" archiva · SC-9 clamp 320 · SC-10 drawer 800 · SC-11 N3 directorio↔workspace (staff+embudo con `EntityWorkspaceLayout`) · SC-12 leafs disabled · SC-13 empty states · SC-14 large dataset · SC-15 network failure · SC-16 a11y/axe · SC-17 i18n neutro · SC-18 persistencia inválida + no-clobber SSR · SC-19 regression guard cross-tab.
>
> **Enmienda a SC-19 (★ UMBRELLA):** el backbone decía "dark mode igual que antes (no se tocó)". SUPERSEDIDO — dark ahora se ARREGLA; la regresión guard de SC-19 pasa a verificar "sub-tabs done renderizan correcto con el wrapper nuevo EN AMBOS TEMAS" (el assert dark se formaliza en SC-20).

```gherkin
# ── ★ UMBRELLA · DARK MODE (BUG #2) ────────────────────────────────────
SC-20 (happy + visual) Dark mode consistente shell + contenido
  Given el shell cargado en una sub-tab shipped (inbox / staff / embudo / lisa-marca / mateo-agenda)
  When el usuario activa el tema oscuro (toggle 🌙 → data-theme="dark")
  Then el topbar, Valeria Y el contenido del agente renderizan oscuros consistentes
  And body NO queda claro (rgb(248,249,251)) ni superficies blancas hardcodeadas (ContactSidebar, cards)
  And el texto mantiene contraste ≥ 4.5:1 en dark
  And al volver a light todo regresa al estado actual (sin regresión light)
  Covers: [Bif-8b, RN-15, AC-12]
  playwright_required: true
  graders:
    - { type: e2e, intent: "por cada sub-tab shipped: toggle dark → medir computed background de body + panel agente + sidebar ≠ claro; toggle light → igual a baseline" }
    - { type: visual_state, screen: "dark-per-subtab", expect: "shell y contenido oscuros, sin mitad clara" }
    - { type: architectural, intent: "grep clases vt-* usadas en superficies user-facing sin variante [data-theme=dark] = 0" }
    - { type: axe, ruleset: "wcag2aa", intent: "contraste en dark" }

# ── ★ UMBRELLA · SOFT-NAV (B1) ─────────────────────────────────────────
SC-21 (edge + regression) Navegación blanda interna no cuelga
  Given el shell cargado (board de Adrián)
  When el usuario navega BLANDO board→recuperar (chip frozen-kpi-badge, ya revertido a soft-nav) y luego recorre tabs/sub-tabs (Lisa→Adrián→Mateo→back) ×15 ciclos
  Then cada superficie monta (componente visible) sin "Cargando shell" colgado
  And cero "Rendered more hooks" / burbuja Next / pageerror en consola (fixture base.ts)
  And el chip frozen-kpi-badge es un Link soft-nav (NO <a> hard-nav)
  Covers: [Bif-9b, RN-14, AC-13]
  playwright_required: true
  graders:
    - { type: e2e, intent: "loop ×15 soft-nav cross-tab + board→recuperar: assert montaje + base.ts teardown verde" }
    - { type: architectural, intent: "frozen-kpi-badge usa next/link (soft), no <a href> full-reload" }

# ── ★ UMBRELLA · RACE GENERALIZADO (ex layout-5050-race-fix) ───────────
SC-22 (adversarial) Drag inmediato post-hidratación respeta clamps
  Given una secuencia de transiciones persistidas (B→A→reload→A→B→reload)
  When el usuario arrastra el splitter INMEDIATAMENTE tras el primer paint (antes de que ResizeObserver/medidas se asienten)
  Then el ancho resultante queda dentro de los clamps de la máquina nueva (≥320px Valeria, agente legible)
  And no se produce estado intermedio inválido ni clobber de la preferencia persistida
  And el test reactivado reemplaza el test.skip(true) de resize-and-state.spec.ts:114
  Covers: [Bif-1, RN-16, AC-14, RN-4]
  playwright_required: true
  graders:
    - { type: e2e, intent: "transición→reload→transición→reload→drag inmediato: assert clamp + persistencia íntegra" }
```

> **race_condition / concurrent_users (sub-categorías mandatory):** `not_applicable_reason` = estado del shell es UI-local por usuario (localStorage, sin recurso compartido con unique constraint). El riesgo real tipo-carrera (hidratación/drag) está cubierto por SC-18 + SC-22. Multi-tab explícito NO entra (propuesto ratificar en la firma de reconciliación — ver § Open questions).

## § Matriz de cobertura (Bif/RN → SC → verificación REAL)

> **★ LEDGER (cierre 2026-06-11):** TODO el mapa = `✅ construido`. Backbone (Bif-1..7 · RN-1..13 · AC-1..11 → SC-1..19): construido T-1..T-6, verificado suite e2e **68/68 (0 flaky)** real-backend + matriz runtime 22/22 + 2 rondas live Chris (signoff SATISFIED). Deltas ★ (abajo): ✅ todos. Ítems `→ historia`: ninguno. Happy-path completo (piso HARD cumplido — aunque cap_change_type=fix, sin deuda diferida).

Filas heredadas del backbone (Bif-1..7, RN-1..13, AC-1..11 → SC-1..19) — verbatim en `backbone_spec` § Matriz; sin huecos, firmadas. Filas ★ UMBRELLA (todas ✅ construido):

| Ítem | Tipo | Cubierto por | Verificación REAL (acción + efecto) |
|---|---|---|---|
| Bif-8a/8b tema light/dark | branch | SC-20, SC-19 | toggle dark por sub-tab → computed colors oscuros; toggle light → baseline |
| Bif-9a/9b nav dura/blanda | branch | SC-21 | loop ×15 soft-nav → montaje observado + consola limpia |
| RN-14 soft-nav confiable + band-aid revertido | rule | SC-21 | board→recuperar soft ×15 + grep Link |
| RN-15 variantes dark completas | rule | SC-20 | grep vt-* sin dark = 0 + medición computed |
| RN-16 drag inmediato seguro | rule | SC-22 | secuencia transición/reload/drag → clamps + persistencia |
| AC-12 dark consistente | accept | SC-20 | (arriba) |
| AC-13 soft-nav ×N | accept | SC-21 | (arriba) |
| AC-14 race reactivado | accept | SC-22 | test.skip removido + verde |
| (trazabilidad U3 splitter castiga board) | resolved-by | SC-1, SC-4 | default 30/70 + resizable resuelven U3 — sin trabajo adicional |

**Huecos detectados:** ninguno. **SC huérfanos:** ninguno (SC-20/21/22 mapean a Bif-8/9 + RN-14/15/16 + AC-12/13/14; U3 trazado a SC-1/SC-4).

## § Estados visuales

Tabla heredada (A/B/C/drawer/N3/empty/error — `backbone_spec` § Estados visuales). Fila ★ UMBRELLA:

| Estado | Trigger | Visible | Oculto |
|---|---|---|---|
| dark (cualquier estado A/B/C/drawer/N3) | `data-theme="dark"` | TODA superficie (shell + contenido agente) en tokens dark, contraste AA | superficies claras residuales (= bug) |

## § Componentes (reuse > new)

Tabla heredada del backbone (TopBarGlobal MODIFICAR · ShellModeToggle ELIMINAR · shell-store REFACTOR · Valeria* MODIFICAR · ValeriaRail ELIMINAR · useViewportGuard REFACTOR · EntityWorkspaceLayout NEW-port · EntitySubNavBar REUSE · staff+embudo MIGRAR · avatar catálogo REUSE). Filas ★ UMBRELLA:

| Componente | Path | Acción |
|---|---|---|
| `globals.css` utilities `vt-*` | `vitalia/frontend/src/app/globals.css` | AUDIT + completar variantes `[data-theme="dark"]` faltantes |
| superficies con color hardcodeado (inbox ContactSidebar, cards) | `features/*/components/**` | CORREGIR a tokens con variante dark (solo color — cero cambio de lógica) |
| shell layout `dynamic({ssr:false})` | `app/[tenantId]/(shell-organism)/layout.tsx` (+ donde el architect determine) | RESOLVER root cause soft-nav (mecanismo a decisión /architect) |
| chip `frozen-kpi-badge` | `features/adrian/components/**` | REVERTIR band-aid hard-nav → soft-nav (post root cause) |
| `resize-and-state.spec.ts` | `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/` | REACTIVAR test.skip(true) adaptado a la máquina nueva |
| target lift | `core/@luana/ui-kit` (v0.3.0) | el architect decide qué piezas del wrapper aterrizan directo en ui-kit (lift-durante) |

## § Microcopy (Spanish neutro LatAm)

Heredada verbatim (`backbone_spec` § Microcopy — tira avatar "Abrir a Valeria" · colapsar · "+" "Nueva conversación" · historial · empties · error). ★ UMBRELLA: sin strings nuevos (dark/soft-nav/race no agregan copy).

## § Responsive breakpoints

Heredados: <1024 drawer · [1024,1280) clamp 320 · ≥1280 30/70 + historial empuja 260 fijo. ★ Dark aplica en todos.

## § Accessibility

Heredada (botones aria + tablist N3 + drawer dialog + live region + anti-burbuja + reduced-motion). ★ UMBRELLA agrega: contraste AA verificado EN DARK (axe corre en ambos temas — SC-20).

## § Telemetría (opcional)

Heredada (`shell_valeria_state_changed` · `shell_new_conversation` · `shell_history_toggled`). ★ Sin eventos nuevos.

## § Open questions — RESUELTAS (firma de reconciliación · Chris 2026-06-10 "Confirmo todo")

1. ✅ **Multi-tab explícito:** `not_applicable_reason` RATIFICADO para race_condition/concurrent_users (estado UI-local por usuario; SC-18+SC-22 cubren el riesgo real). Sin escenario multi-pestaña.
2. ✅ **Alcance del barrido dark:** sub-tabs SHIPPED (lisa/marca, inbox, embudo, staff, mateo/agenda) + wrapper. Placeholders fuera (se corrigen al construirse).
3. ✅ **Caveat behavior-fi re-confirmado** (Chris 2026-06-10): el mockup es prototipo de comportamiento (media fidelidad — sin logo/imágenes/textos finales); la UI actual NO retrocede — estilo sale del design system vigente (§ Design system constraint + AC-10/SC-19).
