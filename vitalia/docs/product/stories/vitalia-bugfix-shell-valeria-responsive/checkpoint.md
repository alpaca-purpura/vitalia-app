---
story_id: vitalia-bugfix-shell-valeria-responsive
type: ui-story                       # ★ reclasificado bugfix→ui-story (Chris confirmó duda 4, 2026-06-06): scope creció a rediseño de máquina de estados + contrato N3 + refactor cross-módulo. Ya no es bugfix lite.
architecture_pattern: ADR-vitalia-004   # punto 7 (N3 list/detail) lo invoca; wrapper cambios citan ADR-vitalia-006 (shell-state)

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F3

# Capability lineage
cap_target: null                    # higiene UX cross-cap del shell-organism (como vitalia-bugfix-shell-nav-scroll-errors)
cap_change_type: fix                # corrige el squeeze (BUG #1) + ajusta defaults responsive del shell
parent_story: null

state: parked                       # ★ 2026-06-10 FOLDED into vitalia-shell-core-hardening (consolidación ratificada Chris). NO se descarta: su 01-spec v3 (2 firmas) + mockup FINAL + baseline build (614bfbd5+29451ef6) son el BACKBONE del spec de la umbrella.
phase: FOLDED
folded_into: vitalia-shell-core-hardening
parked_at: 2026-06-10T00:00:00-05:00
parked_reason: "Folded en la umbrella vitalia-shell-core-hardening. ★ DELIVERED 2026-06-11: la umbrella llegó a done (APPROVED + signoff Chris) — los 7 puntos de esta story están construidos, live-verified y mergeados. Esta carpeta queda como histórico del refinamiento (spec v3 + mockup firmado son carry-forward citados por la umbrella archivada)."
prior_state_before_fold: refined    # ★ 2026-06-06 /po-ux cerró refined: spec v3 RONDA 1+2 + ambas firmas (input_spec_signed + mockup_final_signed) + mapa funcional + matriz sin huecos. Build previo (614bfbd5 + 29451ef6) = BASELINE (puntos 3+5), NO se descarta.
module: shell                       # ⚠️ scope real cross-módulo [shell, clinics, crm] por bundle 1-7 (punto 7) — ver 01-spec § Coordinación
cross_module_scope: [shell, clinics, crm]
agent_owner: null                   # shell-organism transversal (no es de un agente)
map_zone: infraestructura           # superficie no-funcional del shell (wrapper), no una caja de agente
last_modified: 2026-06-06T20:55:00-05:00

# Ratificación spec (proceso v5 · 2 firmas) + visual (ADR-vitalia-003)
input_spec_signed: true             # RONDA 1 intent (7 decisiones + 4 dudas + secuencia)
mockup_final_signed: true           # firma 2 mockup FINAL (Chris "confirmo" + caveat design-system)
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_visual_at: 2026-06-06T20:50:00-05:00
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html
spec_open_ratify:
  - "race_condition/concurrent_users → not_applicable_reason (UI-local per-usuario); Chris puede pedir escenario multi-tab explícito"

# Naturaleza de verificación (DoD #37 / definition-of-done-live-verify)
verification_nature: funcional      # user-reachable (layout visible) → demo manual + anti-burbuja + live-verify
demo_required: true

# Tablet decision (Point 3) — RATIFICADO Chris 2026-06-04: "Drawer en tablet, split ≥1024"
tablet_decision: drawer-en-tablet-split-1024

repro_evidence: vitalia/docs/observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md   # BUG #1 (responsive squeeze)

# DoD #37 live-verify — ⚠️ cubre SOLO el baseline (puntos 3+5+tablet de la v1). Scope expandido 2026-06-06
# (puntos 1/2/4/6/7) NO está verificado → re-verificar live tras el re-build. NO mergeable con esta evidencia sola.
dod_live_verified: true
dod_env: "dev-app.vitalialat.com — Playwright (smoke storageState, --no-deps), clear shell-state para probar fresh defaults"
dod_evidence:
  - action: "Desktop 1280, fresh: medir Valeria-panel + inbox thread"
    observed: "Valeria 381px (29.8% ≈ 30% → Point 2 + rail default Point 1, ya que history+chat min=580px no cabría en 384) · inbox thread 250px (era 56px con 50/50 → squeeze RESUELTO, desbloquea AC-4/5/7)"
  - action: "Tablet 800, fresh: Valeria inline + ancho del agente + burger"
    observed: "Valeria NO inline (drawer) · inbox = 800px (FULL width — Panel colapsa a 0 < lg) · burger visible → click abre drawer (backdrop + valeria-sidebar visible)"
  - action: "Cross-tab regression: lisa/marca/voz-y-tono desktop 1280"
    observed: "Valeria 30% igual que adrian → el cambio del shell aplica uniforme a todas las tabs"
verified_at: 2026-06-04
commits:
  - "29451ef6 — mount Sonner Toaster (orphan shell fix, toast() eran no-ops)"
  - "614bfbd5 — Track B: rail default + 30/70 + tablet drawer (8 files, 146 shell unit tests green)"

next_action: >-
  ★ 2026-06-06 REFINED (spec v3, ambas firmas). HANDOFF → `/architect vitalia vitalia-bugfix-shell-valeria-responsive`
  (lee 01-spec.md → ready package; aplica ADR-vitalia-004 para el N3 list/detail punto 7 + porta EntityWorkspaceLayout
  de nicolify). ⚠️ PRECONDITIONS que `/pm-vitalia` ejecuta ANTES del BUILD (no bloquean architect, ver 01-spec
  § Coordinación punto 7): pausar `vitalia-fase2-lisa-doctores` (developing, clinics) · plegar `vitalia-fase2-adrian-embudo`
  (developed, crm) · adquirir bucket locks `code:{shell,clinics,crm}`. FLAG: ruta crítica del lift FE/shell→@luana/ui-kit
  (256517a3); el sequencing rework-vs-lift se decide en `ready`. Aprendizaje capturado:
  vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md (promotable: candidate).
---

# vitalia-bugfix-shell-valeria-responsive — checkpoint

## Goal

Mejorar el responsive del shell-organism para que **Valeria deje de exprimir el contenido del agente** a anchos comunes (1104–~1400px). Tres cambios pedidos por Chris (ver `chris-input.md` verbatim):

1. **Rail del historial collapsed por default.** El rail de historial de Valeria arranca colapsado (hoy arranca abierto/rail visible).
2. **Default 30/70 en vez de 50/50.** El estado 'full' de Valeria (hoy ~50/50) pasa a **Valeria 30% / agente 70%** por default — **conservando que sigue siendo resizable** por el usuario (el splitter no desaparece; solo cambia el default).
3. **Tablet.** Revisar + **proponer** cómo se comporta el shell en tamaños tablet (≈768–1024px): ¿Valeria rail forzado? ¿drawer? ¿overlay? Entregar propuesta antes de implementar.

## ★ Re-planning 2026-06-06 (scope expandido · Chris-directed regresión a refining)

Chris pidió **regresar al plan antes de desarrollar** para re-armar la story con la **forma de trabajo nueva (proceso v5 · /po-ux 2 rondas)** + 7 solicitudes. La v1 (3 puntos) ya está construida (BASELINE); los 7 puntos abajo son el scope nuevo que `/po-ux` refina. Input verbatim → `chris-input.md § 💬 Conversación` (entry 2026-06-06).

| # | Punto (Chris verbatim resumido) | Naturaleza | Estado |
|---|---|---|---|
| 1 | El botón "agéntico" que cambia vista web/agéntico (topbar) **ya no es necesario** → quitarlo | 🆕 NUEVO | refinar |
| 2 | El botón+dropdown de cambio de tenant debe estar **pegado a la derecha** (⚠️ typo en input: "a la derecha, no a la derecha" — DUDA para /po-ux R1: ¿pegado al borde derecho vs al centro/separado?) | 🆕 NUEVO | refinar + aclarar |
| 3 | Valeria 50/50 → **~30/70** por default | ✅ = AC-2 (build previo) | hecho · ratificar |
| 4 | El **tamaño mínimo de Valeria "rompe" el responsive** → arreglar | 🔧 refina responsive (useViewportGuard / min-width) | refinar |
| 5 | Rail del historial **collapsed por default** | ✅ = AC-1 (build previo) | hecho · ratificar |
| 6 | Valeria con **su propio botón de colapsar** (el de abajo del rail no es visible ni útil). Colapsar Valeria colapsa también el historial si estuviera abierto. Todo colapsado → "abrir" abre **solo Valeria**; abrir historial **empuja** a Valeria (= comportamiento legacy) | 🆕 NUEVO (interacción · redefine collapse/push) | refinar |
| 7 | Agregar **por diseño** el comportamiento del **3er tab (N3) para casos lista/detalle**, como **staff en Valeria** o **icp en Nicolify** | 🆕 NUEVO (patrón de diseño N3 list/detail) | refinar |

**Notas de refinamiento (para /po-ux):**
- Puntos 1, 2, 6 = cambios al **wrapper del shell** (topbar + ValeriaSidebar/chat collapse). Mockup-per-component (ADR-vitalia-003) + wrapper fidelity aplican.
- Punto 6 = la pieza más compleja: redefine la máquina de estados `valeriaState {collapsed, rail, full}` + relación con el historial. Prior-art legacy obligatorio (cómo "empujaba" antes).
- Punto 7 = patrón N3-static list/detail (ADR-vitalia-004 § 3.1.1 `SubSubTabsBar`). Prior-art LIVE: `staff` en Valeria (vitalia) + `icp` en Nicolify. Esto puede gradear a un **patrón de diseño reutilizable del shell** (candidato cross-tab) más que a la story.
- BASELINE (no descartar): `valeriaState` rail-default + 30/70 + tablet-drawer ya en `shell-store.ts` / `useViewportGuard.ts` / `ShellOrganismLayout.tsx`.

## Anti-objetivos

- NO tocar el **dark mode** (BUG #2 del observed-bug — `vt-*` sin variante dark) → story hermana separada (token audit).
- NO re-hacer el ContactSidebarToggle (BUG #3 — ya existe en `ThreadHeader`).
- NO romper el comportamiento mobile (<768px) existente (drawer governado por `mobileDrawerOpen`, ADR-vitalia-006 § D5).
- NO romper la persistencia del splitter/valeriaState (next-themes-style persist en shell-store, ADR-vitalia-006).

## Estado actual del shell (análisis 2026-06-04 · para architect/builder)

- **Splitter / valeriaState:** `src/stores/shell-store.ts` — `valeriaState ∈ {collapsed, rail, full}` (persistido, ADR-vitalia-006). El default + el ancho de 'full' (~50/50) viven acá / en `ShellOrganismLayout.tsx`.
- **Viewport guard:** `src/components/shared/shell-organism/useViewportGuard.ts` — `FULL_STATE_MIN_VIEWPORT = 1104` (Valeria 620 + handle + app 480). Fuerza 'full'→'rail' SOLO en [768,1104). **El supuesto app=480px es la causa del squeeze**: las sub-tabs de agente (inbox 3-pane) necesitan ~640+. Con el cambio a 30/70 el app-panel gana ancho; revisar si el umbral 1104 sigue sirviendo o sube.
- **Historial rail:** `ValeriaSidebar.tsx` / `ValeriaHistory.tsx` — el rail de historial. Punto 1 = default collapsed.
- **Layout:** `ShellOrganismLayout.tsx` — compone Valeria-side + app-panel (el splitter 50/50).
- **Medición live (Chrome MCP, viewport 1280, Valeria full):** Valeria-side ~584px, app-panel `inbox-desktop` 696px → thread del inbox 56px. Con 30/70: Valeria ~384px, app ~896px → inbox 3-pane (list 320 + contact 320 + thread 256) usable; con ContactSidebar cerrado, thread ~576px.

## Acceptance (borrador — /po-ux refina)

| AC | Verificación |
|---|---|
| AC-1 | Por default, el rail de historial de Valeria arranca **collapsed** (fresh load, sin persistencia previa) |
| AC-2 | El default de Valeria 'full' es **30% / 70%** (no 50/50); el agente recibe ~70% del ancho |
| AC-3 | El splitter **sigue resizable** — el usuario puede mover Valeria a otro ancho; se persiste (ADR-006) |
| AC-4 | A 1280px con Valeria 'full' default, el contenido del agente (inbox thread) es **usable** (no exprimido a <~300px) — desbloquea los e2e modes/states del inbox |
| AC-5 | **Tablet (768–1024):** propuesta documentada + implementada (rail forzado / drawer / overlay — a definir en spec) |
| AC-6 | Mobile (<768) sin regresión (drawer `mobileDrawerOpen` intacto) · persistencia valeriaState intacta |
| AC-7 | Dark mode NO en scope (story hermana) · live-verify dev-app + demo Chris |

## § Tablet — propuesta (Punto 3 de Chris · review + recomendación)

**Problema en tablet:** los breakpoints actuales tratan 768–1104px como "desktop angosto" → `useViewportGuard` fuerza Valeria 'full'→'rail', pero el rail INLINE igual consume ancho. A 768 con rail (~72px) el app-panel queda ~696px → el inbox 3-pane vuelve a exprimir el thread (56px). O sea: en la franja tablet, partir la pantalla entre Valeria + agente (aunque sea rail) no alcanza para el contenido de 3 paneles.

**Tres tiers propuestos (revisar con Chris):**

| Tier | Ancho | Valeria | Agente | Racional |
|---|---|---|---|---|
| **mobile** | < 768 | **drawer/overlay** (`mobileDrawerOpen`, ya existe) | full width, single-panel | sin cambio (ADR-006 § D5) |
| **tablet** | 768–1024 | ★ **drawer/overlay** (extender el patrón mobile hasta `lg`) — NO inline | **full width** → el agente reflowea internamente (inbox: auto-colapsa ContactSidebar o usa su layout tabs) | partir la pantalla a esta franja exprime el contenido; mejor Valeria como capa invocable + agente full |
| **desktop** | ≥ 1024 (o ≥ ~1280) | inline **30/70** default (Punto 2), resizable; rail historial collapsed (Punto 1) | 70% | hay ancho para split + 3-pane usable |

**Recomendación:** en **tablet (768–1024) Valeria pasa a drawer/overlay** (igual que mobile, no split inline) → el agente recibe el 100% del ancho y reflowea solo. Esto resuelve el squeeze en la franja angosta sin micro-tunear umbrales del split. El `useViewportGuard` se reescribe a 3 tiers (mobile-drawer / tablet-drawer / desktop-split) en vez del binario actual (rail-forzado vs full). El breakpoint exacto desktop (1024 vs 1280) lo define `/po-ux`+`/architect` con live-judgment de Chris (a 1024 con 30/70: Valeria ~307px, agente ~717px → inbox list 320 + thread 397 + contact cerrado, o contact 320 + thread 77 → habría que auto-colapsar contact; por eso quizás el split inline arranca recién en ~1280).

**Alternativa (si Chris prefiere mantener Valeria siempre visible en tablet):** rail inline en tablet PERO el agente reflowea agresivo (inbox auto-colapsa ContactSidebar por container-width vía ResizeObserver). Menos limpio (deja a Valeria robando ~72px) pero conserva la presencia de la supervisora.

> Decisión pendiente Chris (en refining /po-ux): drawer-en-tablet (recomendado) vs rail-inline-en-tablet + breakpoint desktop (1024 vs 1280).

## Riesgos

- Cross-tab: toca el shell → afecta TODAS las sub-tabs (Lisa/Mateo/Adrián/Lucas/Camila). Regression-guard de las stories shell ya done.
- Persistencia: cambiar el default no debe pisar la preferencia ya guardada del usuario (default aplica solo a fresh / sin valor persistido).
- El umbral del `useViewportGuard` puede necesitar recálculo con el nuevo 30/70.

## Refs

- `chris-input.md` — input verbatim Chris (3 puntos)
- `vitalia/docs/observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md` — repro BUG #1
- `src/stores/shell-store.ts` · `src/components/shared/shell-organism/{useViewportGuard,ShellOrganismLayout,ValeriaSidebar,ValeriaHistory}.tsx`
- `vitalia/docs/architecture/ADR-vitalia-006*` (shell-state persistence) · `vitalia-fase1-shell-layout-5050` (origen 50/50)
- Sibling pendiente: dark-mode token audit (BUG #2)
