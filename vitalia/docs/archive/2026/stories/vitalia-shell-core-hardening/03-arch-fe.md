# 03-arch-fe — vitalia-shell-core-hardening (FE detail)

> Surface única. Owner `builder-frontend` (Sonnet). Auditor `auditor-frontend` (Opus). Behavior-fi HARD: comportamiento del mockup `shell-valeria-states.html`; estilo del design system vigente (canon + tokens). Regresión visual cero en shipped, AMBOS temas.

## 1. Máquina de estados del shell (refactor `shell-store.ts` + `ShellOrganismLayoutClient.tsx`)

### 1.1 Modelo nuevo (RN-1/3/4/5/6/7/13 — supera collapsed/rail/full y nicolify collapsed/history/full)

```ts
// shell-store.ts (refactor) — consume @luana/hooks/create-ssr-safe-persisted-store (ADR-vitalia-006, NO recrear)
type ValeriaOpen = "closed" | "chat";       // A = closed (tira-avatar 44px) · B = chat (split 30/70)
// historyOpen es ADITIVO (empuja) — NO un tercer estado conflado:
interface ShellState {
  valeriaOpen: ValeriaOpen;                  // persisted
  historyOpen: boolean;                      // NOT persisted (RN-5/RN-11: nunca reabre con historial)
  valeriaPct: number | null;                 // split % persisted (null = default 30) — vía react-resizable-panels useDefaultLayout
  mobileDrawerOpen: boolean;                 // persisted, slice independiente (ADR-vitalia-006 §)
  // setters NO persisted; _hasHydrated transient
}
```

- **Estado A (closed):** `valeriaOpen='closed'` → tira-avatar 44px; agente 100%; `historyOpen` forzado false (RN-5).
- **Estado B (chat):** `valeriaOpen='chat'`, `historyOpen=false` → split 30/70 (default, resizable persiste — RN-3/4).
- **Estado C (chat + historial):** `valeriaOpen='chat'`, `historyOpen=true` → historial **empuja** 260px fijo + chat resizable; agente angosta (RN-7).
- **Transiciones (RN-5/6):** colapsar (cabecera) → A (cierra historial también) · clic avatar (tira) → B (NUNCA restaura historial) · abrir historial desde A → B+C (abre Valeria también) · cerrar historial → B · "+" → limpia chat + archiva conv actual al historial UI-local (RN-13).
- **ELIMINAR:** `shellMode` ('agentic'|'web') + `ShellModeToggle` + el grid "web mode" + el rail 60px legacy. (AC-1: grep `shellMode`/`ShellModeToggle` = 0 en `vitalia/frontend/src`.)

### 1.2 Migración legacy (no-crash · SC-18)

`createSsrSafePersistedStore` con `migrate`/fallback que mapea el shape viejo (`valeriaState: 'collapsed'|'rail'|'full'` + `shellMode`) al nuevo:
- `'collapsed'` → `valeriaOpen='closed'`
- `'rail'` → `valeriaOpen='chat'`, `historyOpen=false`
- `'full'` → `valeriaOpen='chat'`, `historyOpen=false` (NO restaura historial — RN-5)
- estado corrupto/desconocido → fallback `{valeriaOpen:'chat', historyOpen:false}` + `console.warn` (SC-18). **NO clobber durante SSR/skeleton** (factory garantiza setItem NO-OP pre-hydration).

### 1.3 ssr:false se CONSERVA
El `dynamic({ssr:false})` de `ShellOrganismLayout.tsx` NO se elimina (causa: react-resizable-panels v4 bare-name localStorage crash). El skeleton store-free (`TopBarGlobal variant="skeleton"`) se conserva (D4/ADR-vitalia-006). El soft-nav se arregla en `proxy.ts` (Decisión A), no removiendo ssr:false.

## 2. Responsive + clamp (`useViewportGuard.ts`)

- **≥1280:** split inline 30/70 default (resizable); historial empuja 260px fijo en C.
- **[1024,1280):** clamp Valeria min ~320px; agente toma el resto, legible, sin overflow-x. **Eliminar** min-width legacy 620px + rail 60px.
- **<1024:** Valeria drawer/overlay (role=dialog, focus-trap, backdrop, Esc); agente 100%; burger en topbar; historial apilado. Slice `mobileDrawerOpen` independiente (desktop 'chat' NO auto-abre drawer).
- **Gate desktop↔mobile = CSS, nunca JS** (montar/desmontar `<Group>` condicional dispara "Rendered more hooks" — lección nicolify ya en el código). El `<Group>` se monta siempre; Valeria panel `hidden md:flex`.
- **BUG#1 squeeze:** el default chat 30/70 + clamp 320 + colapsar propio resuelven U3 + el squeeze (matriz spec). Si live-verify a 1280/1366/1440 muestra squeeze residual del inbox 3-pane → aplicar inbox-local auto-colapsa ContactSidebar (observed-bug opción d, bajo riesgo, NO toca shell). Container-aware (opción c) NO se construye salvo que /pm-vitalia lo pida (Open Q #2).

## 3. Topbar (RN-2 · puntos 1+2)

`TopBarGlobal.tsx`: cluster derecho orden `[ThemeToggle][TenantSwitcher]` (switcher pegado al borde derecho, después del toggle tema). Sin chip web/agéntico (eliminado con ShellModeToggle). Logo a la izquierda (conservar gradient). `variant="skeleton"` store-free se conserva.

## 4. Tira-avatar estado A (NEW · RN-12)

`ValeriaCollapsedStrip.tsx` (o transformar `ValeriaRail.tsx`): tira vertical ~44px en el borde izquierdo con el **avatar real de Valeria** (asset catálogo `public/agents/valeria/thumbnail.png`, NO placeholder "V") + dot estado + label "Valeria". Clic en el avatar → reabre a B (chat-only). `<button aria-label="Abrir a Valeria">`, focus-visible. Atractivo + descubrible (hover). NET-NEW justificado (afford. de reapertura, candidato lift cross-brand).

## 5. Cabecera Valeria (RN-9/13)

`ChatHeader.tsx`/`ValeriaSidebar.tsx`: botones visibles en cabecera: `[+] nueva conversación` · `[◷] historial (toggle)` · `[⟨] colapsar propio`. aria-labels neutro. "+" limpia el chat (estado vacío) + archiva la conv actual a la lista del historial (RN-13, UI-local). Colapsar → A (cierra historial). Historial → C (empuja).

## 6. Historial (RN-7)

`ValeriaHistory.tsx`: ancho **FIJO 260px**; empuja (ensancha el conjunto Valeria, angosta el agente — NO come del chat dentro de panel fijo). Scroll interno cuando muchas convs (SC-14). El chat sigue resizable. `historyOpen` NO persiste abierto.

## 7. N3 list/detail — migrar a `@luana/ui-kit` (Decisión B · AC-9)

### 7.1 Consumir el core (NO cablear a mano, NO reinventar)
- `lisa/staff` → `StaffWorkspaceShell.tsx` consume `EntityWorkspaceLayout` de `@luana/ui-kit` (props `entity/leaves/rootHref/rootLabel/isLoading`). El `[doctor-id]/layout.tsx` server pasa la entidad SSR.
- `adrian/embudo` → su `[leadId]/layout.tsx` monta `EntityWorkspaceLayout` de `@luana/ui-kit` (hoy el layout no existe / N3 no cableado — construirlo consumiendo el core).
- **RETIRAR** `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (copia brand-local, signatura vieja) tras migrar ambos consumers → mata el mirror; encoge el allowlist del arch-test cross-brand-shell-mirror (shrink-only OK).

### 7.2 Canon signature (core v0.3.0)
`EntityWorkspaceLayout`: `{ entity|null, leaves[], rootHref, rootLabel, isLoading?, placeholder?, onAddAffordance?, children }`. `EntitySubNavBar` core: root-pill peer leaf (`‹ {rootLabel}` vuelve a master) + identity slot (avatar+nombre o placeholder) + leaves (rutas, router.push soft-nav) + opcional add-affordance. role=tablist + roving tabindex + flechas (a11y heredado).
- Directory mode (`entity=null`): leaves disabled (aria-disabled, tabIndex=-1, opacity ~.45) — SC-12.
- Master grid: `EntityInfoCard` (canon §2.3) de `@luana/ui-kit` (opcional adoptar — la lista de staff ya existe; AC-9 pide migrar el WORKSPACE al wrapper, el master grid puede quedar como está si ya es coherente. Scope-discipline: no rediseñar el master salvo que rompa con el wrapper).
- **Diferencia con la copia brand vieja** (signatura `{rootHref, rootLabel, entity, leaves, activeLeaf, className}` con back-link separado): el core unifica root-pill + identity. Adaptar los call-sites de staff/embudo a la signatura core.

### 7.3 Edit additivo a `@luana/ui-kit` (solo si falta pieza N3)
Si migrar requiere AGREGAR algo al kit (ej. variante de leaves dinámicos no shipped): edit additivo permitido (proposal accepted). Cualquier edit NO-additivo (refactor del chrome, breaking change) → STOP, escalate /pm-luana. Si se toca el kit: correr `pnpm --filter @luana/ui-kit typecheck && test` + downstream vitalia.

## 8. Dark token-audit (Decisión C · RN-15/AC-12)

### 8.1 Estrategia (reduce deuda)
1. Barrer SHIPPED-only: `lisa/marca`, `adrian/inbox`, `adrian/embudo`, `lisa/staff`, `mateo/agenda` + wrapper.
2. Por cada color hardcodeado (`#hex`, `rgb()`, `bg-white`, `bg-[#...]`, `text-[#...]`) en superficie shipped → migrar al token semántico que YA tiene dark (`bg-card`/`bg-background`/`vt-bg-surface`/`text-foreground`/`vt-text` etc.). PREFERIR migración a token sobre crear nueva variante `[data-theme=dark]` por clase.
3. Completar variante `[data-theme="dark"]` SOLO para `--vitalia-*-soft`/derivados que realmente falten (grep + medición computed live por sub-tab).
4. Conservar el wiring next-themes + tailwind darkMode (correcto).

### 8.2 Casos conocidos (observed-bug BUG#2)
- inbox `ContactSidebar` blanco `rgb(255,255,255)` → token surface (dark-aware).
- cards claras en dark → `bg-card`.
- `body` claro en dark = ya cubierto (`html[data-theme=dark]` + `body bg --vitalia-bg` dark override existe) — verificar live que no haya override que lo pise.

### 8.3 Gate (AC-12)
- arch-test/eslint no-hardcoded-color (si activo) ENCOGE (migra hardcoded→token).
- SC-20 e2e: por sub-tab shipped, toggle dark → medir computed background de body + panel agente + sidebar ≠ claro; toggle light → baseline. axe contraste dark.

## 9. Soft-nav (Decisión A · RN-14/AC-13)

- `proxy.ts`: verificar/extender el edge-redirect 307 de landing (matcher UUID-only `bareTenantLandingRedirect` ya existe) — cubre `/{tenantId}` → `/{tenantId}/{DEFAULT_LANDING_SUBPATH}` con fetch fresco (Router monta limpio).
- `EmbudoMetrics.tsx` (líneas 78-87): **revertir** el band-aid hard-nav del chip `frozen-kpi-badge` de `<a href>` a `next/link` (soft-nav). El comentario B1-fix se actualiza (root cause resuelto vía edge-redirect + Router fresco).
- SC-21 e2e real: board→recuperar soft + loop ×15 cross-tab (Lisa→Adrián→Mateo→back) → cada superficie monta sin "Cargando shell" colgado, cero "Rendered more hooks"/burbuja Next (base.ts), chip = next/link.

## 10. Race / drag inmediato (RN-16/AC-14)

- `resize-and-state.spec.ts`: **reactivar** el test omitido (adaptado a la máquina nueva closed|chat). El spec firmado dice `test.skip(true)` línea ~114 — el grep actual no lo muestra como `.skip` literal; el builder localiza el assert omitido/comentado del race y lo reactiva contra los clamps nuevos (≥320 Valeria). Deliverable explícito.
- SC-22: secuencia transición→reload→transición→reload→drag inmediato → ancho dentro de clamps + persistencia íntegra (no clobber). `useDefaultLayout` + ResizeObserver minSize respetan los clamps de la máquina nueva.

## File map (NEW / MODIFY / RETIRE)

| Path | Acción |
|---|---|
| `stores/shell-store.ts` | MODIFY (máquina closed|chat + historyOpen; migrate legacy; quitar shellMode) |
| `components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | MODIFY (máquina nueva; clamp; drawer; historial empuja; quitar web grid/ShellModeToggle) |
| `components/shared/shell-organism/TopBarGlobal.tsx` | MODIFY (switcher extremo derecho; sin chip) |
| `components/shared/shell-organism/ShellModeToggle.tsx` | RETIRE |
| `components/shared/shell-organism/ValeriaSidebar.tsx` `ValeriaChat.tsx` `ChatHeader.tsx` | MODIFY (cabecera +/historial/colapsar; push) |
| `components/shared/shell-organism/ValeriaRail.tsx` | RETIRE/TRANSFORM → tira-avatar |
| `components/shared/shell-organism/ValeriaCollapsedStrip.tsx` | NEW (tira 44px + avatar; RN-12) |
| `components/shared/shell-organism/ValeriaHistory.tsx` | MODIFY (260px fijo empuja; "+" archiva) |
| `components/shared/shell-organism/useViewportGuard.ts` | MODIFY (clamp 320; drawer 1024; sin 620/rail) |
| `components/shared/shell-organism/EntitySubNavBar.tsx` | RETIRE (migrar a @luana/ui-kit) |
| `features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx` | MODIFY (consume EntityWorkspaceLayout core) |
| `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/layout.tsx` | MODIFY (pasa entity a wrapper core) |
| `app/[tenantId]/(shell-organism)/adrian/embudo/[leadId]/layout.tsx` | NEW/MODIFY (monta EntityWorkspaceLayout core) |
| `features/adrian/components/embudo/EmbudoMetrics.tsx` | MODIFY (revertir band-aid → next/link) |
| `app/globals.css` | MODIFY (dark gaps hardcoded→token; --vitalia-*-soft faltantes) |
| `proxy.ts` | MODIFY (edge-redirect landing 307; verificar matcher) |
| `core/@luana/ui-kit/src/*` | CONSUME (default); EDIT additivo-mínimo solo si falta pieza N3 |
| `e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts` | MODIFY (reactivar test omitido — AC-14) |
| `e2e/regression/shell-core-hardening/{dark,soft-nav,race,regression-cross-tab}.spec.ts` | NEW |

## Design system canon binding (HARD)

- N3 = `EntityWorkspaceLayout` de `@luana/ui-kit` (NUNCA cablear a mano — canon §2.1-2.2).
- Franjas N3 full-bleed `bg-card` + border-bottom sticky (NUNCA card redondeada).
- Tokens (no arbitrary): spacing/radius/color de la escala. Dark via token, no hardcoded.
- Átomos de `@luana/ui-kit`/`components/ui/` — no reinventar primitivas.
- Avatar Valeria = asset catálogo (no placeholder).

## Anti-burbuja (gate funcional)

Todos los e2e importan `vitalia/frontend/e2e/fixtures/base.ts` (pageerror/console-error/`/api`≥400/Next overlay), NUNCA `@playwright/test` directo. SC-20/21/22 + regression cross-tab son real-backend (no mockear el backend del surface bajo prueba — verification-real-not-200).
