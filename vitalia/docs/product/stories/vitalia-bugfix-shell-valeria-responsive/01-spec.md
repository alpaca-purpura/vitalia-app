---
story_id: vitalia-bugfix-shell-valeria-responsive
brand: vitalia
type: ui-story                       # ★ reclasificado desde `bugfix` (2026-06-06): el scope creció a rediseño de máquina de estados + contrato N3 → ya no es bugfix lite. /pm-vitalia debe bumpear checkpoint.type.
state: refining
architecture_pattern: ADR-vitalia-004   # punto 7 (N3 list/detail) lo invoca; wrapper cambios citan ADR-vitalia-006 (shell-state)
po_ux_version: 3
spec_round: 2                        # RONDA 2 (Gherkin + matriz) escrita; ambas firmas dadas
input_spec_signed: true              # ★ RONDA 1 firmada — las 7 decisiones + 4 dudas + secuencia resueltas (Chris 2026-06-06)
mockup_final_signed: true            # ★ firma 2 — mockup FINAL ratificado (Chris 2026-06-06: "confirmo") + caveat design-system (ver § Design system constraint)
ratified_by_chris: true
cross_module_scope: [shell, clinics, crm]   # ★ bundle 1-7 (Chris): punto 7 refactoriza staff(clinics) + embudo(crm). REQUIERE coordinación /pm — ver § Coordinación punto 7
cap_target: null                     # higiene UX cross-cap del shell-organism (transversal, sin agente)
cap_change_type: fix                 # corrige squeeze + redefine collapse + cementa N3 (no crea cap user-visible nueva)
---

# 01-spec — vitalia-bugfix-shell-valeria-responsive (v1 · RONDA 1)

> **Proceso v5 · 2 rondas / 2 firmas.** Este archivo se firma DOS veces sobre sí mismo. RONDA 1 (este turno) = § Context/Dónde vive + § Mapa funcional + § Wireframes BORRADOR + § Dudas → Chris firma intención (`input_spec_signed`). RONDA 2 (post-firma) = § Gherkin + § Matriz de cobertura + mockup FINAL → `refined`. SSoT: `docs/process/spec-mapa-funcional.md`.
>
> **Origen:** `bugfix` de responsive (3 puntos, ya construido = BASELINE) **promovido** a `ui-story` por scope expandido (7 puntos · Chris 2026-06-06). Ver `chris-input.md § 💬 Conversación` (2026-06-06) + `checkpoint.md § Re-planning 2026-06-06`.

## Prior art applied

Scan ejecutado sobre el shell-organism real + brands activas (anti-duplication-refining). **Esta story NO crea primitivas nuevas — modifica el wrapper existente + cementa un patrón ya construido.**

- **Wrapper del shell (modificado, no recreado):**
  - `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` — topbar (puntos 1+2)
  - `vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx` — chip web/agéntico DISABLED (punto 1 = eliminar)
  - `vitalia/frontend/src/stores/shell-store.ts` — `valeriaState{collapsed,rail,full}` + `shellMode{agentic,web}` (puntos 1,3,5,6 = refactor de la máquina de estados)
  - `vitalia/frontend/src/components/shared/shell-organism/{ValeriaSidebar,ValeriaRail,ValeriaHistory,ValeriaChat,ChatHeader}.tsx` (punto 6)
  - `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts` — `FULL_STATE_MIN_VIEWPORT=1104` calculado con Valeria=620px (punto 4 = recalc para 30/70)
- **Patrón N3 list/detail (cementar, ya construido en 3 lugares — punto 7):**
  - `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` — N3-**dynamic** entity workspace nav (la pieza canónica del list/detail). `[‹ raíz] | [avatar entidad] | [leaf tabs]`. ADR-vitalia-004 § D-1.
  - `vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx` — N3-**static** (catálogo `AGENT_SUBSUBTABS`). Complementaria, no es el list/detail.
  - Consumidores LIVE: `lisa/staff` (directorio → workspace doctor), `adrian/embudo` (lista → lead workspace), nicolify `abel/icp` (`[agent]/[subtab]/[subsubtab]/[leaf]`).
- **Engine consumed:** `@luana/hooks/create-ssr-safe-persisted-store` (store SSR-safe, ADR-vitalia-006). No recrear.
- **Learnings aplicados:** `vitalia/docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` (shell `ssr:false` — cuidado con nav dura/blanda) · ADR-vitalia-006 (4 técnicas fallidas de persistencia).
- **Lift candidates detectados:** el wrapper del shell completo está en proposal `accepted` de lift a `@luana/ui-kit` (256517a3) — esta story es ruta crítica. El **patrón N3 list/detail** (EntitySubNavBar) es candidato lift cross-brand (vive igual en nicolify) → escalar a `/pm-vitalia` post-merge.
- **Net-new justificado:** el **modelo de estados legacy-push (punto 6)** es net-new para AMBAS marcas (ver comparación abajo) — ninguna lo implementa hoy.

### Nicolify comparison (2026-06-06 · pedido Chris "¿lo tiene igual?")

Nicolify = **port re-skinneado** del mismo shell (Valeria→Luana). Mismos componentes (`TopBarGlobal`, `Ribbon`, `SubTabsBar`, `EntitySubNavBar`, `ShellModeToggle`, `useViewportGuard`). Diferencias materiales:

| Eje | vitalia | nicolify | Veredicto |
|---|---|---|---|
| Estado panel | `collapsed/rail/full` | `collapsed/history/full` | **mismo** (renombró `rail`→`history`; `railWidth = full?280:60` idéntico) |
| ¿Historial empuja? | ❌ reemplaza dentro de panel fijo | ❌ **igual** | el punto 6 (push) es **nuevo para las dos** |
| web/agéntico | `ShellModeToggle`+`shellMode`+D2 | **idéntico** (también muerto) | quitar en vitalia (punto 1) = lift candidate quitar en nicolify |
| `splitState` enum | no existe | declarado pero semi-vestigial (composición usa `luanaState`+panel resizable, `MIN_LUANA_PX 580/360`) | no copiar — ruido |
| N3 list/detail | `EntitySubNavBar` cableado a mano por layout | ✅ **`EntityWorkspaceLayout`** (wrapper reusable: EntitySubNavBar + children + skeleton SSR-safe, store-free G2) | **nicolify mejor** → portar a vitalia (punto 7) |

**Decisiones derivadas de la comparación:**
- **Punto 6:** diseñar modelo limpio NUEVO (`closed / chat` + `historyOpen` aditivo que empuja) que supere a ambas marcas — NO copiar el `collapsed/rail/full` conflado de ninguna. Candidato lift cross-brand.
- **Punto 7:** adoptar el patrón de nicolify `EntityWorkspaceLayout` como contrato canónico vitalia (port verbatim re-temizado, NO reinventar). Es la mejor factorización existente del list/detail.
- **Cross-brand (flag /pm-vitalia):** ambas marcas casi gemelas + shell aprobado para lift a `@luana/ui-kit` (256517a3). El punto 6 + `EntityWorkspaceLayout` + quitar web-mode deberían CONVERGER ambas y alimentar el lift. /po-ux vitalia NO toca nicolify — se escala como promotion candidate post-merge.

---

## § Context · Dónde vive (RONDA 1)

### Zona / caja del mapa (árbol `paradigm-arquitectura.md`)

- **Zona:** Infraestructura → caja **plataforma-técnica** (el shell-organism wrapper es superficie no-funcional, no es una caja de agente). `map_zone: infraestructura`, `user_visible` del wrapper = chrome.
- **Excepción punto 7:** el patrón N3 list/detail es chrome de navegación que habilita superficies de agente (staff = Lisa, embudo = Adrián), pero el patrón en sí vive en el shell (transversal).

### Shell que aplica

`vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (existe). Esta story TOCA el contrato del shell en 3 ejes: topbar (§ TopBar), panel Valeria (§ Valeria states), y nav N3 (§ SubSubTabs/EntitySubNav). El contrato se actualiza como parte de la story.

### Dónde aterriza el usuario

Todo el shell: `app/[tenantId]/(shell-organism)/**`. Los cambios son **transversales** — aplican a TODAS las sub-tabs de agente (Lisa/Mateo/Adrián/Lucas/Camila) + Plataforma. No hay una ruta nueva; se modifica el wrapper que todas comparten.

### § Design system constraint (caveat Chris 2026-06-06 · HARD)

El mockup `shell-valeria-states.html` es **behavior-fi, NO pixel-fi** — comunica el COMPORTAMIENTO (estados, push, "+", avatar, drawer, N3), no el estilo final. La implementación real **DEBE seguir los lineamientos UI vigentes** y **no regresar lo que ya está bien**:

- **Design system first (D1 · frontend-visual-fidelity):** reutilizar átomos `components/ui/` + tokens `globals.css` / `@luana/design-tokens` + moléculas `components/shared/`. NO inventar primitivas ni estilos ad-hoc del mockup.
- **Wrapper fidelity:** topbar, ribbon, sub-tabs, ValeriaChat, logo gradient, agent-colors ya shipped se **conservan** — esta story cambia COMPORTAMIENTO + posición (switcher, sin chip, colapso/push, "+", avatar), no re-estiliza lo existente.
- **SSoT visual:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` + skill `vitalia-design-system`. El avatar de Valeria usa el asset/estilo del catálogo de agentes (no el placeholder "V" del mockup).
- **Dark mode:** NO tocar (story hermana). El wrapper nuevo debe respetar las variantes dark existentes sin romperlas.
- **Regresión cero:** las sub-tabs ya `done` (lisa/marca, inbox) + el dark mode siguen iguales tras el wrapper nuevo (AC-10).

> Regla: "lo que veo (comportamiento) = lo que se programa; el ESTILO sale del design system, no del mockup".

### Out-of-scope explícito (anti-creep)

- ❌ Dark mode half-applied (`vt-*` sin variante dark) — story hermana (token audit). BUG #2.
- ❌ ContactSidebarToggle del inbox — ya existe (BUG #3).
- ❌ Cambiar el contenido de cualquier sub-tab de agente (solo el wrapper + el patrón N3, no las features).
- ❌ Lift del shell a `@luana/ui-kit` — es otra story (esta es prerequisito).
- ❌ Construir instancias N3 list/detail NUEVAS (sub-tabs que hoy no son list/detail). Punto 7 = portar `EntityWorkspaceLayout` + migrar las instancias EXISTENTES (staff/embudo) al patrón canónico, no inventar casos nuevos.
- ❌ Tocar nicolify (`abel/icp`) — cross-brand prohibido; convergencia vía `/pm-vitalia` + lift.

---

## § Mapa funcional (capa humana — va ANTES del Gherkin)

### Happy path (camino dorado narrado)

1. El usuario entra al shell de Vitalia (cualquier sub-tab de agente, ej. Adrián → Inbox). En desktop ancho (≥1280) ve: **topbar** arriba (logo a la izquierda · `[🌙 tema][▼ Clínica Sanaré]` pegados a la derecha · **sin** chip "agéntico/web") + **Valeria a la izquierda ocupando ~30%** (chat, sin historial) + **el agente a la derecha ocupando ~70%**.
2. El usuario trabaja en el agente (70% usable — el inbox/embudo/staff respira). Valeria está presente como supervisora pero no exprime el contenido.
3. El usuario quiere ver el **historial** de Valeria → toca el botón de historial → el panel de historial **empuja**: Valeria se ensancha (historial + chat), el agente se angosta. Trabaja, vuelve a cerrar el historial → el agente recupera su ancho.
4. El usuario no necesita a Valeria → toca el **botón de colapsar propio** de Valeria (en su cabecera) → Valeria se cierra; queda una **tira fina vertical (~44px)** con el avatar de Valeria en el borde izquierdo; el agente toma el **100%**. (Si el historial estaba abierto, también se cierra.)
5. El usuario quiere a Valeria de vuelta → clic en la tira fina → Valeria reabre **solo el chat** (estado B, sin historial), 30/70.
6. El usuario achica la ventana (ej. a una tablet, <1024) → Valeria deja de ser split inline y pasa a **drawer/overlay**; el agente toma el 100% y aparece el burger en el topbar para invocar a Valeria.
7. Dentro de una sub-tab tipo **lista/detalle** (ej. Lisa → Staff): ve el **directorio** (lista); clic en un doctor → entra al **workspace del doctor** con una barra N3 `[‹ Staff] [avatar Dr.] [Perfil · Horarios · Servicios]`; navega los leaf tabs; `[‹ Staff]` lo regresa a la lista. (Mismo patrón en Adrián→Embudo y nicolify→ICP.)

### Bifurcaciones (árbol de decisión)

```
Viewport del usuario
├─ ≥1024 (desktop) → Valeria INLINE SPLIT (resizable)            [Bif-1]
│   └─ Estado de Valeria (máquina nueva):
│       ├─ A · CERRADA → tira fina 44px (AVATAR Valeria destacado); agente 100% [Bif-2a]
│       │     └─ clic AVATAR → abre a B (chat-only, NO restaura historial)  [Bif-2b]
│       ├─ B · ABIERTA (chat) → 30/70; sin historial (DEFAULT fresh)        [Bif-3]
│       │     ├─ botón colapsar (cabecera) → A                              [Bif-3a]
│       │     ├─ botón historial → C                                        [Bif-3b]
│       │     └─ botón "+" nueva conv → limpia chat + conv actual→historial [Bif-3c]
│       └─ C · ABIERTA + HISTORIAL → historial EMPUJA (Valeria↑ agente↓)    [Bif-4]
│             ├─ cerrar historial → B                                       [Bif-4a]
│             └─ botón colapsar (cabecera) → A (historial también colapsa)  [Bif-4b]
│   └─ Ancho [1024,1280): Valeria clamp a min ~320px, agente toma resto     [Bif-5]
├─ <1024 (tablet/móvil) → Valeria DRAWER/overlay; agente 100%; burger       [Bif-6]
│   ├─ burger → abre drawer (historial apilado + chat)                      [Bif-6a]
│   └─ cerrar drawer (botón colapsar / backdrop / Esc) → agente 100%        [Bif-6b]
└─ Sub-tab tipo lista/detalle (N3-dynamic, transversal a cualquier viewport)
    ├─ sin entidad → modo DIRECTORIO (lista; leaf tabs disabled)            [Bif-7a]
    └─ con entidad → modo WORKSPACE (EntitySubNavBar: ‹raíz · avatar · leafs)[Bif-7b]
```

### Reglas de negocio (invariantes)

- **RN-1** — El shell corre **siempre en modo agéntico**. No existe "modo web" (eliminado: chip + `shellMode` + acople `collapsed↔web`).
- **RN-2** — El switcher de tenant vive en el **cluster derecho del topbar, al extremo** (orden `[🌙 tema][▼ tenant]`).
- **RN-3** — Default fresh (sin preferencia persistida): Valeria **abierta en chat (estado B)**, **historial colapsado**, split **30/70**.
- **RN-4** — El split Valeria/agente sigue **resizable**; el default 30/70 solo aplica cuando no hay valor persistido (no pisa la preferencia del usuario · ADR-vitalia-006).
- **RN-5** — Colapsar Valeria (estado A) **colapsa también el historial** si estaba abierto. Reabrir nunca restaura el historial (reabre a B).
- **RN-6** — Abrir el historial estando Valeria **cerrada** → abre Valeria también (no se puede tener historial sin Valeria).
- **RN-7** — El historial **empuja** (ensancha el panel de Valeria, angosta el agente) — NO come del ancho del chat dentro de un panel fijo. El historial tiene **ancho FIJO (~260px)**; el chat sigue resizable (Chris 2026-06-06). (Cambio vs comportamiento actual.)
- **RN-8** — En [1024,1280) Valeria se clampa a un mínimo legible (~320px); por debajo de 1024 Valeria es drawer (no inline). El min-width legacy (620px) se elimina.
- **RN-9** — El botón de colapsar de Valeria es **propio y visible** (cabecera de Valeria). El botón inferior del rail de íconos se elimina (junto con el rail de 60px).
- **RN-12** — Reabrir Valeria desde el estado A: el affordance de la tira fina es la **imagen/avatar de Valeria** (clic en el avatar abre a B), no una flecha. Debe ser **visualmente atractivo + descubrible** (avatar destacado, hover, dot de estado, label "Valeria"). (Chris 2026-06-06 punto 1.)
- **RN-13** — Valeria tiene un botón **"+" nueva conversación** en su cabecera (visible junto al de historial). Al activarlo: **limpia el chat** a estado vacío (nueva conversación en blanco) y la **conversación actual se archiva al historial** (aparece en la lista del historial). (Chris 2026-06-06 punto 2.)
- **RN-10** — Patrón N3 list/detail canónico: directorio (lista) → entidad (workspace con `EntitySubNavBar`: `[‹ raíz][avatar entidad][leaf tabs]`); sin entidad los leafs van disabled (aria-disabled, roving tabindex). Es el contrato que futuras sub-tabs lista/detalle DEBEN seguir.
- **RN-11** — Persistencia: la preferencia de Valeria (cerrada/abierta + ancho) se persiste SSR-safe (ADR-vitalia-006); el historial NO se persiste como abierto (RN-5).

### Criterios de aceptación (feature-done)

- **AC-1** — No existe el chip "agéntico/web" en ninguna parte del shell; `shellMode` no aparece en el store ni en el código (grep limpio). [RN-1]
- **AC-2** — El switcher de tenant aparece al extremo derecho del topbar, después del toggle de tema. [RN-2]
- **AC-3** — Fresh load (sin persistencia): Valeria abierta en chat, historial cerrado, 30/70; el agente recibe ~70% usable. [RN-3]
- **AC-4** — El split sigue moviéndose con el splitter y la preferencia persiste al recargar. [RN-4]
- **AC-5** — Valeria tiene un botón de colapsar propio visible; colapsar deja la tira de 44px con el **avatar de Valeria** destacado; **clic en el avatar** reabre a chat-only. [RN-9, RN-5, RN-12]
- **AC-11** — En la cabecera de Valeria hay un botón **"+" nueva conversación**: al activarlo el chat se limpia (estado vacío) y la conversación previa aparece en el historial. [RN-13]
- **AC-6** — Abrir el historial empuja (Valeria se ensancha en ~260px fijos, agente se angosta); cerrarlo lo revierte. Abrir historial con Valeria cerrada la abre. [RN-7, RN-6]
- **AC-7** — En [1024,1280) Valeria no rompe el layout (clamp ~320px, agente legible, sin overflow/scroll horizontal). El rail de 60px ya no existe. [RN-8]
- **AC-8** — <1024: Valeria es drawer, agente 100%, burger funcional; el botón colapsar cierra el drawer. [Bif-6]
- **AC-9** — El patrón N3 list/detail queda **refactorizado** (no solo documentado): `EntityWorkspaceLayout` portado a vitalia (de nicolify) + `lisa/staff` y `adrian/embudo` migrados a usarlo, funcionando + consistentes + verificados live; contrato cementado en SHELL-DESIGN-CONTRACT/ADR. (Sujeto a § Coordinación punto 7.) [RN-10]
- **AC-10** — Sin regresión cross-tab: las sub-tabs ya `done` (lisa/marca, adrian/inbox, etc.) siguen funcionando con el wrapper nuevo. Dark mode sin tocar.

---

## § Wireframes

> **Mockup FINAL (interactivo, firma 2):** `mockups/shell-valeria-states.html` — tokens portados verbatim de `globals.css`; toggles para estados A/B/C (historial empuja, fijo 260px), viewport 1280/1100/800 (clamp 320 + drawer), N3 directorio↔workspace, dark. Servir: `cd vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups && python3 -m http.server 8888` → `http://localhost:8888/shell-valeria-states.html`. **Pendiente firma 2** (`mockup_final_signed`).
>
> Abajo, los wireframes ASCII (RONDA 1 — la forma; el HTML es la versión navegable).

### Topbar (puntos 1 + 2)

```
ANTES:  [☰][logo Vitalia][▼ Clínica Sanaré] ·················· [🌙]
                          └ switcher a la izq         chip web/agéntico = overlay (no en topbar)

DESPUÉS:[☰][logo Vitalia] ······························· [🌙 tema][▼ Clínica Sanaré]
        sin chip web/agéntico                            switcher al extremo derecho ─┘
```

### Valeria — 3 estados (punto 6, desktop ≥1024)

```
┌──────────────────────── ESTADO A · CERRADA ────────────────────────┐
│[☰][logo] ··················································· [🌙][▼ Sanaré]│
├──┬──────────────────────────────────────────────────────────────────┤
│(V)│                                                                   │  (V) = avatar Valeria
│Val│             AGENTE (inbox / embudo / staff)  100%                 │       destacado + dot
│   │                                                                   │       estado · label
└──┴──────────────────────────────────────────────────────────────────┘
 └ tira 44px · clic en el AVATAR reabre a B (RN-12 · atractivo, no una flecha)

┌──────────────────────── ESTADO B · VALERIA (chat) · DEFAULT ────────┐
│[☰][logo] ··················································· [🌙][▼ Sanaré]│
├──────────────────┬──────────────────────────────────────────────────┤
│ Valeria [+][◷][⟨]│                                                    │  + = nueva conversación
│ ───────────────  │              AGENTE  ~70%                          │  ◷ = abrir historial
│  chat ~30%       │                                                    │  ⟨ = colapsar (propio)
│  [composer]      │                                                    │
└──────────────────┴──────────────────────────────────────────────────┘
        ↑ splitter resizable (default 30/70)
   "+" → limpia el chat (nueva conv) + la conversación actual va al historial (RN-13)

┌──────────────────── ESTADO C · VALERIA + HISTORIAL (empuja→) ───────┐
│[☰][logo] ··················································· [🌙][▼ Sanaré]│
├──────────┬──────────────┬───────────────────────────────────────────┤
│ Historial│ Valeria [⟨][◷]│                                            │
│ ──────── │ ──────────── │            AGENTE  (angostado)             │
│ · conv 1 │  chat        │                                            │
│ · conv 2 │  [composer]  │                                            │
└──────────┴──────────────┴───────────────────────────────────────────┘
   ↑ historial EMPUJA: Valeria se ensancha, el agente cede ancho (RN-7)
```

### Tablet/móvil (<1024) — drawer (punto 6t · reutiliza)

```
[☰][logo] ································· [🌙][▼ Sanaré]      [☰] tocado → drawer:
┌─────────────────────────────────────────────┐          ┌──────────────────────┐
│                                             │          │ V Valeria        [✕] │
│        AGENTE  100% (single panel)          │   ──►    │ ──────────────────── │
│                                             │          │ Historial (apilado)  │
│                                             │          │ ──────────────────── │
└─────────────────────────────────────────────┘          │ chat + composer      │
                                                          └──────────────────────┘ (overlay + backdrop)
```

### N3 list/detail (punto 7 · patrón a cementar)

```
DIRECTORIO (lista · sin entidad)            WORKSPACE (entidad seleccionada)
┌───────────────────────────────┐          ┌───────────────────────────────────────────┐
│ Staff                         │          │ [‹ Staff] [👤 Dra. Pérez] Perfil·Horarios·Serv│  ← EntitySubNavBar
│ ───────────────────────────── │  clic →  │ ─────────────────────────────────────────── │
│ 👤 Dra. Pérez      Activa     │  doctor  │                                             │
│ 👤 Dr. Gómez       Activo     │          │   contenido del leaf activo (Perfil)        │
│ 👤 Dra. Ruiz       Inactiva   │          │                                             │
└───────────────────────────────┘          └───────────────────────────────────────────┘
 leafs disabled (aria-disabled)              leafs enabled · roving tabindex · ‹ raíz vuelve a lista
```

---

## § Dudas / open questions (RONDA 1) — RESUELTAS (Chris 2026-06-06)

1. ✅ **Historial estado C = ancho FIJO** (~260px); el chat sigue resizable; el conjunto Valeria empuja al agente. → RN-7 + AC-6 actualizados.
2. ✅ **Tira fina estado A = borde izquierdo** ("de momento sí"). Valeria siempre vive a la izquierda.
3. ✅ **Punto 7 = REFACTOR REAL** (no solo documentar). Chris: "dejemos todo mejor y funcional, aquí dejamos todo bien". → portar `EntityWorkspaceLayout` (de nicolify) a vitalia + **migrar `lisa/staff` + `adrian/embudo` a usarlo** (funcional + consistente) + cementar el contrato. ⚠️ Esto cruza módulos `clinics` (staff) + `crm` (embudo) que tienen stories ABIERTAS → ver § Coordinación punto 7 (decisión de secuencia pendiente).
4. ✅ **Reclasificación bugfix→ui-story confirmada.** /pm-vitalia bumpea `checkpoint.type`.

## § Coordinación punto 7 (REFACTOR cross-módulo — decisión de secuencia PENDIENTE)

El refactor del punto 7 toca superficies que viven en **otros módulos con stories abiertas**:

| Superficie N3 | Módulo | Story | Estado |
|---|---|---|---|
| `lisa/staff` (directorio→workspace doctor) | clinics | `vitalia-fase2-lisa-doctores` | **developing** |
| `adrian/embudo` (lista→lead workspace) | crm | `vitalia-fase2-adrian-embudo` | **developed** |
| (nicolify `abel/icp`) | — | nicolify | otra marca (no se toca acá) |

Refactorizar staff + embudo desde esta story (`module: shell`) = colisión M14 con 2 stories abiertas (bucket `code:clinics` + `code:crm`).

**DECISIÓN Chris 2026-06-06: BUNDLE 1-7 en esta story** ("dejemos todo bien"). Esta story absorbe el N3 de staff + embudo. Implicaciones que **`/pm-vitalia` DEBE ejecutar ANTES del build** (no bloquean refinar):

1. **Bumpear `checkpoint.type`** bugfix→ui-story + `module` shell → cross-module `[shell, clinics, crm]` (o declarar multi-bucket lock).
2. **Pausar `vitalia-fase2-lisa-doctores`** (developing, clinics): no debe construir su N3 de staff en paralelo — esta story lo entrega. Coordinar para que no haya doble-trabajo / colisión de bucket `code:clinics`.
3. **Plegar `vitalia-fase2-adrian-embudo`** (developed, crm): su N3 de embudo se migra acá. Como está `developed` (dod_live_verified=false, no mergeada — ver learning embudo-imagined-contract), su migración a `EntityWorkspaceLayout` se coordina (reabrir a developing o que esta story lo entregue antes de su merge).
4. **Bucket locks al build:** adquirir `code:shell` + `code:clinics` + `code:crm` (o serializar) — ninguna otra sesión construyendo esos módulos durante esta story.

> Riesgo aceptado por Chris: story grande cross-módulo que serializa 3 módulos + reestructura 2 stories. Beneficio: el N3 list/detail queda canónico + funcional + consistente en un solo paso, alimentando el lift a `@luana/ui-kit`. **Refinar (spec + mockup + Gherkin) es safe ahora**; la coordinación de estados es responsabilidad de `/pm-vitalia` en la transición a build.

---

## § Gherkin scenarios (RONDA 2)

> Todos `playwright_required: true` (UI shell user-reachable) salvo nota. Graders citan superficies; `/architect` dicta paths exactos en `04-validators § test_construction_plan`. Verificación REAL = ejercer la acción + observar efecto (no GET 200).

```gherkin
# ── HAPPY ──────────────────────────────────────────────────────────────
SC-1 (happy) Default fresh = Valeria chat 30/70, historial cerrado
  Given un tenant sin preferencia de shell persistida (localStorage limpio)
  When el usuario entra a cualquier sub-tab de agente (ej. Adrián→Inbox) en viewport 1280
  Then Valeria se muestra en estado B (chat), ocupando ~30% (~384px) y el agente ~70% (~896px)
  And el historial NO está visible · el panel del agente es usable (>600px, sin squeeze)
  Covers: [Bif-3, RN-3, AC-3]
  graders:
    - { type: e2e, intent: "fresh load mide anchos Valeria/agente" }
    - { type: visual_state, screen: "shell-default", expect: "history hidden, agent ~70%" }

SC-2 (happy) No existe el toggle web/agéntico ni shellMode
  Given el shell cargado
  When el usuario inspecciona el topbar y el código
  Then no hay chip "Agéntico/Web" en ninguna parte · grep de `shellMode`/`ShellModeToggle` = 0 en src
  Covers: [Bif-(topbar), RN-1, AC-1]
  graders:
    - { type: e2e, intent: "topbar no contiene data-testid=shell-mode-toggle" }
    - { type: architectural, intent: "grep shellMode/ShellModeToggle = 0 ocurrencias en vitalia/frontend/src" }

SC-3 (happy) Tenant switcher al extremo derecho
  Given el topbar
  When se renderiza
  Then el orden del cluster derecho es [ThemeToggle][TenantSwitcher] (switcher pegado al borde derecho)
  And el switcher NO está junto al logo (izquierda)
  Covers: [Bif-(topbar), RN-2, AC-2]
  graders: [{ type: e2e, intent: "DOM order: theme antes que tenant-switcher en el cluster derecho" }]

SC-4 (happy) Splitter resizable + persiste
  Given Valeria en estado B (30/70)
  When el usuario arrastra el splitter a ~45% y recarga la página
  Then el ancho ~45% se conserva (preferencia persistida SSR-safe) · el default 30/70 NO la pisa
  Covers: [Bif-(split), RN-4, AC-4]
  graders:
    - { type: e2e, intent: "drag splitter, reload, assert ancho persistido" }
    - { type: state_check, target: localStorage, key: "vitalia-shell-state", expect: "ancho usuario" }

SC-5 (happy) Colapsar con botón propio → tira con avatar → reabrir por avatar
  Given Valeria en estado B
  When el usuario hace clic en el botón propio de colapsar (cabecera de Valeria)
  Then Valeria pasa a estado A: tira de ~44px con el AVATAR de Valeria destacado (dot estado + label) · el agente toma 100%
  When el usuario hace clic en el AVATAR de la tira
  Then Valeria reabre a estado B (chat-only) · NO restaura el historial
  Covers: [Bif-2a, Bif-2b, Bif-3a, RN-9, RN-5, RN-12, AC-5]
  graders:
    - { type: e2e, intent: "colapsar → strip visible con avatar; click avatar → chat visible, history hidden" }
    - { type: visual_state, screen: "valeria-collapsed-strip", element: "avatar", expect: "destacado + clickable" }

SC-6 (happy) Abrir historial EMPUJA (fijo 260px), cerrarlo revierte
  Given Valeria en estado B
  When el usuario abre el historial (botón ◷)
  Then estado C: el historial aparece a la izquierda con ancho FIJO ~260px · Valeria se ensancha · el agente se ANGOSTA (recibe menos ancho que en B)
  When el usuario cierra el historial
  Then vuelve a B · el agente recupera su ancho
  Covers: [Bif-3b, Bif-4, Bif-4a, RN-7, AC-6]
  graders:
    - { type: e2e, intent: "abrir historial: medir ancho agente C < ancho agente B; historial == 260px" }

SC-7 (edge) Abrir historial con Valeria cerrada → abre Valeria
  Given Valeria en estado A (cerrada)
  When el usuario invoca "abrir historial" (vía la tira / atajo)
  Then Valeria abre Y el historial abre (estado C) — no se puede tener historial sin Valeria
  Covers: [Bif-2→C, RN-6]
  graders: [{ type: e2e, intent: "desde A, abrir historial → estado C (valeria+historial visibles)" }]

SC-8 (happy) "+" nueva conversación limpia chat + archiva la actual al historial
  Given Valeria en estado B con una conversación activa
  When el usuario hace clic en "+" (nueva conversación)
  Then el chat se limpia a estado vacío (nueva conversación) · la conversación previa aparece como ítem en el historial
  Covers: [Bif-3c, RN-13, AC-11]
  graders:
    - { type: e2e, intent: "click +: chat vacío + nuevo ítem en lista de historial (count +1)" }
    - { type: state_check, target: store, expect: "conversación previa archivada, activa = nueva vacía" }

# ── EDGE / RESPONSIVE ──────────────────────────────────────────────────
SC-9 (edge) Desktop angosto [1024,1280): clamp 320, sin romper
  Given viewport 1100, Valeria en B
  When se renderiza
  Then Valeria se clampa a min ~320px · el agente toma el resto y es legible · NO hay scroll horizontal · NO existe la tira de 60px de íconos (rail eliminado)
  Covers: [Bif-5, RN-8, AC-7]
  graders:
    - { type: e2e, intent: "viewport 1100: Valeria==320px, sin overflow-x, no existe rail 60px" }

SC-10 (edge) Tablet/móvil <1024: drawer
  Given viewport 800
  When se renderiza
  Then Valeria NO es inline (drawer) · el agente toma 100% · el burger aparece en el topbar
  When el usuario abre el drawer y luego lo cierra (botón colapsar / backdrop / Esc)
  Then el drawer cierra · valeriaState (desktop) no se ve afectado (slice independiente)
  Covers: [Bif-6, Bif-6a, Bif-6b, AC-8]
  graders: [{ type: e2e, intent: "viewport 800: burger visible, click abre drawer overlay, close lo cierra" }]

# ── N3 LIST/DETAIL (punto 7) ───────────────────────────────────────────
SC-11 (happy) Directorio → workspace (EntityWorkspaceLayout) → volver
  Given una sub-tab list/detail (Lisa→Staff) en modo directorio
  When el usuario hace clic en una entidad (un doctor)
  Then entra al workspace con EntitySubNavBar: [‹ Staff] [avatar entidad] [Perfil·Horarios·Servicios] · leaf activo derivado de la URL
  When hace clic en "‹ Staff"
  Then vuelve al directorio
  And embudo (Adrián) usa el MISMO patrón (EntityWorkspaceLayout) tras la migración
  Covers: [Bif-7a, Bif-7b, RN-10, AC-9]
  graders:
    - { type: e2e, intent: "staff: directorio→workspace→back; embudo usa EntityWorkspaceLayout (mismo componente)" }
    - { type: architectural, intent: "staff + embudo layouts importan EntityWorkspaceLayout (no cablean EntitySubNavBar a mano)" }

SC-12 (negative) Directorio sin entidad → leaf tabs disabled
  Given el modo directorio (sin entidad seleccionada)
  When se renderiza la EntitySubNavBar
  Then los leaf tabs van disabled (aria-disabled, tabIndex=-1, opacidad reducida)
  Covers: [Bif-7a, RN-10]
  graders: [{ type: e2e, intent: "directorio: leafs con aria-disabled=true" }]

# ── EMPTY / LARGE ──────────────────────────────────────────────────────
SC-13 (empty_state) Vacíos: directorio sin entidades, historial vacío, conversación nueva
  Given un tenant sin doctores (directorio vacío) y sin conversaciones previas
  When entra a Staff y abre el historial / crea nueva conversación
  Then directorio muestra empty-state (no tabla vacía sin guía) · historial muestra empty-state · chat nuevo muestra estado vacío con guía
  Covers: [empty_state, RN-13]
  graders: [{ type: e2e, intent: "0 entidades → empty-state visible (no crash, no lista vacía muda)" }]

SC-14 (large_dataset) Muchos: directorio con 1000 entidades, historial con muchas convs
  Given un directorio con ≥1000 entidades y un historial con ≥100 conversaciones
  When se renderiza
  Then la lista pagina/virtualiza sin romper el layout · el historial scrollea dentro de sus 260px fijos
  Covers: [large_dataset, RN-7]
  graders: [{ type: e2e, intent: "1000 entidades: render sin overflow del shell; historial scroll interno" }]

# ── NETWORK ────────────────────────────────────────────────────────────
SC-15 (network_failure) Fetch falla → error state, no blank
  Given la carga de la entidad N3 (o de tenants del switcher) responde 5xx/timeout
  When el usuario navega a un workspace de entidad (o abre el switcher)
  Then se muestra error-state con retry (no pantalla en blanco, no burbuja Next) · el resto del shell sigue usable
  Covers: [network_failure, RN-2, RN-10]
  graders:
    - { type: e2e, intent: "mock 500 entity fetch → error-state + retry; sin nextjs-portal" }

# ── A11Y / I18N ────────────────────────────────────────────────────────
SC-16 (accessibility) Teclado + ARIA + sin burbuja
  Given el shell
  When el usuario navega solo con teclado
  Then avatar-reabrir, "+", botón historial y colapsar son focusables (focus visible) con aria-label correctos
  And la EntitySubNavBar cumple tablist (role=tablist/tab, roving tabindex, flechas)
  And axe wcag2aa = 0 violations · contraste ≥ 4.5:1 · `nextjs-portal` ausente (gate anti-burbuja)
  Covers: [accessibility, RN-9, RN-12, RN-13, RN-10]
  graders:
    - { type: axe, ruleset: "wcag2aa" }
    - { type: e2e, intent: "tab order alcanza avatar/+/historial/colapsar; flechas en N3 tablist" }

SC-17 (i18n) Spanish neutro + locale tenant
  Given los textos del shell
  When se renderizan
  Then copy en español neutro sin voseo ("Nueva conversación", "Historial", "Abrir a Valeria", "Colapsar") · el switcher respeta el locale/moneda del tenant donde aplique
  Covers: [i18n, RN-13]
  graders: [{ type: e2e, intent: "strings = neutro, sin voseo; tenant switcher locale-aware" }]

# ── ADVERSARIAL ────────────────────────────────────────────────────────
SC-18 (adversarial) Estado persistido inválido + no clobber en SSR (regresión Bug #1)
  Given un localStorage con valeriaState corrupto/desconocido
  When el shell hidrata
  Then fallback a un estado válido (sin crash, console.warn) · la persistencia NO se sobrescribe durante SSR/skeleton (ADR-vitalia-006)
  Covers: [adversarial, RN-11, RN-4]
  graders:
    - { type: e2e, intent: "inyectar estado inválido → fallback sin crash" }
    - { type: e2e, intent: "reload no clobbea la preferencia (SSR-safe persist)" }

# ── REGRESSION GUARD ───────────────────────────────────────────────────
SC-19 (regression) Cross-tab + dark mode sin regresión
  Given el wrapper nuevo aplicado
  When se abren sub-tabs ya `done` (lisa/marca, inbox) en desktop y en dark mode
  Then renderizan correctamente con el wrapper nuevo · agent-colors/logo gradient intactos · dark mode igual que antes (no se tocó)
  Covers: [AC-10]
  graders:
    - { type: e2e, intent: "lisa/marca + inbox render OK con wrapper nuevo; dark sin cambios" }
    - { type: visual_state, screen: "regression-existing-subtabs", expect: "sin diffs no intencionales" }
```

> **race_condition / concurrent_users:** `not_applicable_reason` = el estado del shell es UI-local **por usuario** (persistido en localStorage, sin recurso compartido con unique constraint). El único riesgo tipo-carrera (hidratación que pisa la preferencia) está cubierto por SC-18. Ratificar con Chris si se quiere un escenario explícito multi-tab.

## § Matriz de cobertura (Bif/RN → SC → verificación REAL)

| Ítem | Tipo | Cubierto por | Verificación REAL (acción + efecto) |
|---|---|---|---|
| Bif-1/Bif-5 split inline + clamp | branch | SC-1, SC-9 | medir anchos a 1280 y 1100; assert clamp 320 + sin overflow-x |
| Bif-2a/2b cerrada + avatar reabre | branch | SC-5 | colapsar → strip+avatar; clic avatar → chat (DOM observado) |
| Bif-3/3a/3b/3c estado B + acciones | branch | SC-1, SC-5, SC-6, SC-8 | default B; colapsar; abrir historial; "+" |
| Bif-4/4a historial empuja | branch | SC-6 | ancho agente C < B; historial==260 |
| Bif-6/6a/6b drawer tablet | branch | SC-10 | viewport 800: burger abre/cierra drawer |
| Bif-7a/7b N3 dir/workspace | branch | SC-11, SC-12 | clic entidad→workspace; back; leafs disabled en dir |
| RN-1 sin modo web | rule | SC-2 | grep shellMode=0 + no chip |
| RN-2 switcher derecha | rule | SC-3, SC-15 | DOM order + locale |
| RN-3 default B 30/70 | rule | SC-1 | medición fresh |
| RN-4 resizable+persist | rule | SC-4, SC-18 | drag+reload; no clobber SSR |
| RN-5 colapsar→cierra historial / reabrir sin restaurar | rule | SC-5 | colapsar en C → reabrir = B |
| RN-6 historial sin Valeria imposible | rule | SC-7 | desde A abrir historial → C |
| RN-7 historial empuja fijo 260 | rule | SC-6, SC-14 | medición + scroll interno |
| RN-8 clamp 320 / sin rail 60 | rule | SC-9 | 1100: 320 + grep no rail |
| RN-9 botón colapsar propio | rule | SC-5 | clic en cabecera colapsa |
| RN-10 contrato N3 EntityWorkspaceLayout | rule | SC-11, SC-12 | staff+embudo importan el wrapper; leafs disabled |
| RN-11 persist SSR-safe / fallback | rule | SC-18 | estado inválido + no clobber |
| RN-12 reabrir por avatar atractivo | rule | SC-5, SC-16 | avatar clickable + focusable |
| RN-13 "+" nueva conv | rule | SC-8, SC-13 | chat vacío + archivo a historial |
| AC-1..11 | accept | SC-1..SC-12, SC-19 | (cada AC ligado arriba) |

**Huecos detectados:** ninguno (cada Bif y RN mapea a ≥1 SC). **SC huérfanos:** ninguno (cada SC mapea a ≥1 ítem del mapa). _race_condition/concurrent_users con not_applicable_reason ratificable._

## § Estados visuales

| Estado | Trigger | Visible | Oculto |
|---|---|---|---|
| A · cerrada | colapsar / default-not | tira 44px (avatar + dot + label), agente 100% | chat, historial |
| B · chat | default / reabrir / cerrar historial | cabecera (+, ◷, ⟨), chat, composer; agente ~70% | historial, tira |
| C · +historial | abrir historial | historial 260px fijo, chat, agente angostado | tira |
| drawer (<1024) | viewport <1024 | overlay Valeria (historial apilado + chat) + backdrop; agente 100% | split inline |
| N3 directorio | sin entidad | lista entidades; leafs disabled | workspace |
| N3 workspace | entidad seleccionada | EntitySubNavBar + leaf activo | — |
| empty | 0 datos | empty-state (directorio/historial/chat-nuevo) | listas vacías mudas |
| error | fetch 5xx | error-state + retry | contenido |

## § Componentes (reuse > new)

| Componente | Path | Acción |
|---|---|---|
| `TopBarGlobal` | `components/shared/shell-organism/TopBarGlobal.tsx` | MODIFICAR (quitar nada del topbar; mover TenantSwitcher al cluster derecho) |
| `ShellModeToggle` | `…/ShellModeToggle.tsx` | **ELIMINAR** (punto 1) + limpiar `shellMode` del store + acople D2 |
| `shell-store` | `stores/shell-store.ts` | REFACTOR máquina de estados (quitar `rail`+`shellMode`; modelo closed/open + historyOpen; `historial` no-persist) |
| `ValeriaSidebar` + `ValeriaChat`/`ChatHeader` | `…/Valeria*.tsx` | MODIFICAR (cabecera: botón colapsar propio + "+" + historial; push) |
| `ValeriaRail` | `…/ValeriaRail.tsx` | **ELIMINAR/transformar** (rail 60px se va; tira-avatar nueva en estado A) |
| `ValeriaHistory` | `…/ValeriaHistory.tsx` | MODIFICAR (260px fijo, empuja; "+" archiva acá) |
| `useViewportGuard` | `…/useViewportGuard.ts` | REFACTOR (clamp 320, sin 620; umbral drawer 1024) |
| `EntityWorkspaceLayout` | `…/EntityWorkspaceLayout.tsx` | **NEW (port de nicolify)** — wrapper N3 list/detail |
| `EntitySubNavBar` | `…/EntitySubNavBar.tsx` | REUSE (ya existe) |
| `lisa/staff` + `adrian/embudo` layouts | `app/[tenantId]/(shell-organism)/{lisa/staff,adrian/embudo}/...` | MIGRAR a `EntityWorkspaceLayout` |
| avatar Valeria | catálogo agentes `public/agents/valeria/` | REUSE asset real (no placeholder "V") |

> NEW justificados: `EntityWorkspaceLayout` (port de nicolify — mejor factorización existente, ver § Prior art) + la tira-avatar de estado A (afforance de reapertura nuevo, RN-12).

## § Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| Tira avatar (aria) | "Abrir a Valeria" |
| Botón colapsar (aria) | "Colapsar a Valeria" |
| Botón "+" (aria/title) | "Nueva conversación" |
| Botón historial (aria) | "Mostrar historial" / "Ocultar historial" |
| Chat nuevo (empty) | "Nueva conversación" · "Escribí a Valeria para empezar" |
| Historial vacío | "Aún no hay conversaciones" |
| Directorio vacío (staff) | "Aún no hay personal cargado" + CTA |
| Error fetch | "No pudimos cargar esto. Reintentar." |

Sin voseo salvo donde el output del agente respete la voz del tenant (no aplica al chrome del shell).

## § Responsive breakpoints

- **<1024 (tablet+móvil):** Valeria drawer/overlay; agente 100%; burger en topbar; historial apilado en el drawer.
- **[1024, 1280):** split inline; Valeria clamp min ~320px; agente toma el resto; sin rail 60px.
- **≥1280:** split inline 30/70 default (resizable); historial empuja 260px fijo en C.

## § Accessibility

- Avatar-reabrir, "+", historial, colapsar: `<button>` con `aria-label`, focus visible (`focus:ring`).
- EntitySubNavBar: `role=tablist`/`tab`, `aria-selected`, roving tabindex, flechas (ya implementado — conservar).
- Drawer: `role=dialog` + `aria-modal` + focus trap + restauración de foco al burger al cerrar (ya existe — conservar).
- Live region para cambios de estado de Valeria (ya existe — conservar).
- Gate anti-burbuja: `nextjs-portal` ausente; sin errores de consola/hidratación (fixture `base.ts`).
- Contraste ≥ 4.5:1; respeta `prefers-reduced-motion` (transición del panel ya lo hace).

## § Telemetría (opcional)

```yaml
events:
  - { name: "shell_valeria_state_changed", props: ["from", "to"] }   # A/B/C
  - { name: "shell_new_conversation", props: [] }                    # "+"
  - { name: "shell_history_toggled", props: ["open"] }
```
(Brand-local `vitalia_growth_studio_event`, sin PHI — `/architect` decide si entran en scope.)
