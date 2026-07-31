---
name: vitalia-design-system
description: SSoT cargable del sistema de diseño + shell-organism de Vitalia (índice narrado sobre los docs + código que ya existen — NO duplica). Cargá ANTES de tocar cualquier `vitalia/frontend/src/**` UI. Cubre autoridad de tokens (globals.css + tailwind.config.ts), inventario de átomos (components/ui/) + moléculas/organism (components/shared/ + shell-organism/), el shell de 5 especialistas + Valeria supervisora (ribbon N1 [Lisa·Mateo·Adrián·Lucas·Camila+Plataforma] + sub-tabs N2 + sub-sub-tabs N3 + ValeriaSidebar), catálogo de agentes (colores hex + assets · Mateo=Operar #FEE209 · Valeria=sidebar supervisor), gates ADR-003/ADR-004, fidelidad del wrapper (portar verbatim), y convenciones PHI. ★ v1.2 2026-05-30: Valeria salió del Ribbon; Mateo entró como especialista Operar. Triggers: 'pantalla vitalia', 'componente vitalia', 'shell organism', 'átomos vitalia', 'moléculas vitalia', 'colores de marca vitalia', 'agent color', 'ribbon', 'sub-tab', 'ValeriaSidebar', 'tokens vitalia', 'cómo se hizo este módulo en vitalia', 'fidelidad visual vitalia'. Es brand-scoped (instancia de la clase `{brand}-design-system`).
---

<!-- voseo-allowed: internal skill doc (instrucciones al agente builder/architect), no user-facing -->

# vitalia-design-system — SSoT cargable del diseño Vitalia

> **Soy un índice narrado + router, NO una copia.** El SSoT real vive en los docs (`vitalia/docs/architecture/`) y el código (`vitalia/frontend/`). Mi trabajo es que llegues a la fuente correcta sin triangular, y que **el builder reciba esto en el build** (vía `must_load_skills`), que es donde hoy se pierde.
>
> **Regla de oro:** antes de crear cualquier elemento visual → buscá acá si ya existe. Reinventar un átomo/molécula/token existente = FAIL (regla 34 + `anti-duplication.md`).

## 0 · Cuándo cargarme (obligatorio)

- Cualquier ticket que toque `vitalia/frontend/src/{app,components,features}/**` con UI.
- `/architect` (surface FE · references/fe.md) DEBE listarme en `assignment.must_load_skills` de todo ticket FE de vitalia.
- `builder-frontend` me carga y reporta "Skills consulted" en `T-{n}-result.md`.
- `auditor-frontend` me carga antes de scorear categorías 9 (Visual fidelity) y 13 (Anti-duplication).

## 1 · Autoridad de tokens (SSoT real — NO inventar)

| Qué | SSoT autoritativo | Nota |
|---|---|---|
| Colores, tipografía, radios, gradientes (vivos) | `vitalia/frontend/src/app/globals.css` | CSS vars `:root` + `.dark`. ES el SSoT runtime. |
| Wiring de vars → utilidades Tailwind | `vitalia/frontend/tailwind.config.ts` | `hsl(var(--*))`. 3 fuentes: General Sans / Manrope / Inter. |
| Lookup runtime de agent-color (JIT-safe) | `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | Evita purga JIT de Tailwind. |
| Intención visual / brandbook / recipes | `vitalia/docs/architecture/design-system.md` (581 líneas) | doc de diseño (HEX+HSL, recipes por contexto). |

> ⚠️ **Trampa común:** `core/@luana/design-tokens` **solo exporta `Z_INDEX`** — NO colores. No busques tokens de color ahí; el SSoT es brand-local (`globals.css`). Quien busca color en el engine no encuentra nada y reinventa → ese es el bug.

**Reglas de token:** nunca hardcodear hex/px que ya es var. Usá clases Tailwind que mapean a las vars (`bg-primary`, `text-agent-lisa`, etc.). Primario = cian `#01B2F8`. Accent = púrpura `#7B2D91`. Gradiente mariposa (`--vitalia-gradient-mariposa`: cian→púrpura→verde-lima) para logo/CTA destacados.

## 2 · Átomos (`vitalia/frontend/src/components/ui/`) — 19, Shadcn

`accordion · alert · avatar · badge · button · dialog · dropdown-menu · form · input · label · resizable · scroll-area · select · separator · sheet · skeleton · sonner · tabs · textarea · tooltip`

→ **Nunca reinventar uno de estos.** Si falta una primitiva, agregar Shadcn estándar (no `<div>` crudo). `tabs` Shadcn es para tabs internas de contenido — **NO** para sub-secciones de una sub-tab (eso es N3-static, ver §4).

## 3 · Moléculas / organism (`vitalia/frontend/src/components/shared/`)

| Dir | Para qué |
|---|---|
| `shell-organism/` | **El organism principal** (26 componentes). Ver §4. |
| `shell/` | ⚠️ Legacy (`AppShell`/`Sidebar`/`TopBar`) — en deprecación, NO usar para nuevo. |
| `agents/` | `AgentAvatar`, `AgentAttribution`, `agent-names.ts`. |
| `phi/` | `PiiMaskedSpan`, `RequireRole`, `AuditedSection` — superficies PHI (ver §7). |
| `copilot-rail/`, `contact-sidebar/`, `activity-stream/`, `deposits/`, `nps/`, `channels/`, `lucas-recommendations/`, `attribution/`, `marketing/`, `wizard/` | moléculas de dominio (reusar antes de crear). |

`vitalia/frontend/src/components/marca/shared/` → moléculas brand-shared (ej. `AutosaveBadge`).

## 4 · Shell organism (lo que más se pierde en build)

**★ Modelo de navegación cardinal:** son **3 niveles de tabs que GUÍAN hasta la hoja**. La **hoja = el contenido** (lo que renderiza el `page.tsx` del último tab) y **es lo único que cambia**. Una **hoja NUNCA contiene tabs/subtabs**: los tabs son la ruta, la hoja es el destino. Si el contenido parece necesitar sub-secciones tabuladas, esas sub-secciones son en realidad otro nivel de tab (N3), NO `Tabs` de Shadcn dentro de la hoja (eso es anti-pattern, ADR-vitalia-004 §3.1.1).

Los 3 niveles de tab (SSoT: `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`, 665 líneas):

- **N1 — Ribbon de 5 especialistas + Plataforma** (tab nivel 1): `Ribbon.tsx` + `RibbonTab.tsx` + `PlataformaTab.tsx` (antes `ConfigTab.tsx` con label "Configurar"). Orden: Lisa · Mateo · Adrián · Lucas · Camila + Plataforma. ★★ v1.2 (2026-05-30): Valeria removida del Ribbon (es supervisora sidebar); Mateo incorporado como especialista "Operar/Mi Día". Cada tab con su agent-color border.
- **N2 — SubTabsBar** (tab nivel 2): `SubTabsBar.tsx` + `SubTab.tsx` (línea 2, active con `agent-soft`).
- **N3 — SubSubTabsBar** (tab nivel 3, último): `SubSubTabsBar.tsx` + `SubSubTab.tsx` (cuando el destino agrupa 3+ vistas discretas — **N3-static, NO Shadcn Tabs internas**, ADR-vitalia-004 §3.1.1).
- **Hoja (contenido)**: lo que renderiza el `page.tsx` del último tab alcanzado. Es el destino — NO contiene más tabs. Aquí vive el componente de la feature.
- **Panel Valeria izquierdo (3 estados)**: `ValeriaSidebar.tsx` → `ValeriaRail.tsx` (collapsed) / `ValeriaHistory.tsx` / `ValeriaChat.tsx` (con `ChatComposer`/`ChatHeader`/`ChatMessages`/`MessageBubble`/`TypingIndicator`/`ChatStarters`).
- **TopBar global**: `TopBarGlobal.tsx` + `LogoMark.tsx` + `TenantSwitcher.tsx`/`TenantBadge.tsx`/`TenantOption.tsx` + `ThemeToggle.tsx`/`ShellModeToggle.tsx`.
- **Layout**: `ShellOrganismLayout.tsx` (splitter resizable, NO 50/50 hardcoded).

**Routing** (SSoT: `vitalia/frontend/src/lib/shell-routes.ts` → `AGENT_CATALOG` + `AGENT_SUBTABS` + `AGENT_SUBSUBTABS`):
```
app/[tenantId]/(shell-organism)/[agent]/[subtab]/[subsubtab]/page.tsx
```
Server Component default · SSR initial state · PHI nunca en URL/searchParams.

### ★ Fidelidad del wrapper — portar VERBATIM (causa #1 de pérdida)

Cuando un componente/sub-tab aterriza dentro del shell, el wrapper de contexto (TopBar + Ribbon + SubTabsBar + ValeriaSidebar/chat) se **porta verbatim** desde las fuentes canónicas — NO se reinventa simplificado (genera grises en vez de tokens, 50/50 hardcoded, chat inventado):

| Layer | Fuente canónica (archivada, read-only) |
|---|---|
| Shell integral (macro) | `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` |
| ValeriaChat completo | `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html` |
| ValeriaRail (collapsed) | `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` |

SSoT visual (cement 2026-06-22): **Storybook** (`core/@luana/ui-kit`, canon §5) — el shell vive en `@luana/ui-kit`; navegá las stories `Shell/*` para el componente REAL. El viejo `shell-mockup-per-component.md § Shell wrapper fidelity` (mockups `.html`) quedó **SUPERSEDED** por Storybook.

## 5 · Catálogo de agentes — colores + assets (★★ v1.2 2026-05-30)

| Agente | slug | `--agent-{slug}` | rol corto | tab Ribbon | assets |
|---|---|---|---|---|---|
| Lisa | `lisa` | `#00D084` (verde) | marca / presencia | ✅ Ribbon N1 | `vitalia/frontend/public/agents/lisa/` |
| Mateo | `mateo` | `#FEE209` (amarillo) | **Operar / Mi Día** (agenda+bookings+pacientes) | ✅ Ribbon N1 ★★ v1.2 | `…/mateo/` |
| Adrián | `adrian` | `#01B2F8` (cian) | embudo / inbox | ✅ Ribbon N1 | `…/adrian/` |
| Lucas | `lucas` | `#111111` (negro) | recomendaciones / growth | ✅ Ribbon N1 | `…/lucas/` |
| Camila | `camila` | `#180D95` (azul) | copilot (a11y fix dark) | ✅ Ribbon N1 | `…/camila/` |
| Valeria | `valeria` | `#7B2D91` (púrpura) | **supervisora sidebar** (orquesta flujo) | ❌ NO Ribbon · sidebar permanente ★★ v1.2 | `…/valeria/` |
| (Plataforma) | `config` (token) | gris | acceso / onboarding / configuracion | ✅ PlataformaTab (antes "Configurar") ★★ v1.2 | — |

Cada agente especialista: `--agent-{slug}` + `--agent-{slug}-soft`. Cada dir de assets: `thumbnail.png` + `transparent.png/jpeg`. Default chat agent = `valeria` (sidebar).

## 6 · Gates de proceso (cumplir, no re-litigar)

- **ADR-vitalia-003** (`shell-mockup-per-component.md`): **SUPERSEDED 2026-06-22 por Storybook (canon §5).** La ratificación visual ya NO es un mockup HTML por-componente — se hace **partiendo de Storybook** (`@luana/ui-kit`, el componente REAL) y promoviendo lo net-new al kit + story. Ver `.claude/rules/frontend-visual-fidelity.md § Storybook`.
- **ADR-vitalia-004** (`shell-feature-architecture-mandatory.md`): sub-tab nueva → patrón de 9 secciones; `01-spec.md`/`03-arch.md`/`checkpoint.md` citan `architecture_pattern: ADR-vitalia-004`.
- **ADR-vitalia-006**: SSR-safe persisted store (zustand persist).

## 7 · Superficies PHI (HIPAA-lite)

UI que muestra PHI → `PiiMaskedSpan` + `RequireRole` (roles `doctor`/`nurse`/`admin_clinic`). Nunca PHI en `localStorage`/`searchParams`. SSoT: `.claude/rules/hipaa-lite.md`.

## 8 · Checklist "cómo construir una pantalla Vitalia"

1. ¿Es sub-tab del shell? → seguí ADR-vitalia-004 (9 secciones) + routing en `shell-routes.ts`.
2. Tokens: usá clases Tailwind mapeadas a `globals.css`. Cero hex/px nuevo.
3. Átomos: reusá de `components/ui/`. Moléculas: reusá de `components/shared/`. Solo si nada sirve → creá en `features/{agent}/components/` **con** átomos.
4. Wrapper del shell: portá verbatim (§4). No reinventar.
5. Agent-color: usá `--agent-{slug}` del agente dueño de la tab (§5).
6. PHI: `PiiMaskedSpan` + `RequireRole` (§7).
7. Spanish neutro (sin voseo, salvo sales_agent). Estados empty/loading/error/success como el mockup.
8. Tests: Vitest + Playwright visual scoped (composición vs la story de Storybook · canon §5 — el golden-vs-mockup de ADR-003 quedó SUPERSEDED) + axe.

## Referencias (SSoT — leer on-demand)

- `vitalia/docs/architecture/design-system.md` — tokens + recipes (581 líneas)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design + inventario + routing + testing (665 líneas)
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — mapa del sistema
- `vitalia/frontend/src/app/globals.css` + `tailwind.config.ts` — tokens vivos (SSoT runtime)
- `vitalia/frontend/src/lib/shell-routes.ts` — catálogo agentes/subtabs/subsubtabs
- `.claude/rules/{shell-feature-architecture-mandatory,hipaa-lite}.md` (shell-mockup-per-component: SUPERSEDED, archivado en `vitalia/docs/archive/2026/superseded/`)
- `.claude/rules/frontend-visual-fidelity.md` (regla 34) · `.claude/rules/frontend-fsd.md` · `.claude/rules/anti-duplication.md`
