<!-- voseo-allowed: internal spec documentation, ratchet against root spanish-text rule -->

---
story_id: vitalia-fase1-stack-stability
brand: vitalia
type: ui-story
phase: fase-1
module: shell-organism / infra
agent_owner: shell                                 # transversal — no es de un agente
capability: shell.foundation
po_version: 1.0
last_modified: 2026-05-22
state: refined
ratified_by_chris: true                            # ratificado whole-doc por Chris 2026-05-22 (3 batches consolidados)
ratified_visual_by_chris: not_applicable          # F1-S0 EXENTA del protocolo mockup-per-component (ADR-vitalia-003 § Excepciones)
ratified_visual_reason: "F1-S0 es infra-only — no construye componentes user-facing nuevos. Las 2 test pages auxiliares (primitives-showcase.tsx, agent-tokens-swatch.tsx) son fixtures Playwright, no UI prod."
parallel_safe: false                               # blocker hard de toda Fase 1
priority: critical
estimated_dev_days: 3-5
dependencies:
  hard: []
  soft: []
service_blockers: []
blocks_hard:
  - vitalia-fase1-design-tokens-theme
  - vitalia-fase1-topbar-global
  - vitalia-fase1-tenant-switcher
  - vitalia-fase1-shell-layout-5050
  - vitalia-fase1-valeria-rail-history
  - vitalia-fase1-valeria-chat-skeleton
  - vitalia-fase1-ribbon-6-tabs
  - vitalia-fase1-sub-tabs-line2
  - vitalia-fase1-routing-shell
  - vitalia-fase1-empty-states
reuse_map_summary: "infra-only — verifica Tailwind v4 + instala Shadcn primitives copy-paste + agent tokens via CSS vars + plan deprecación .vt-* (no migra contenido todavía) + Playwright @project=visual configurado para baseline goldens"
links:
  design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
  mockup_visual: "vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html"
  baseline_session: "vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md"
  outcome_master: "vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md"
  template_shell_spec: "vitalia/docs/specs/templates/01-spec-shell-template.md"
  mockup_per_component_protocol: "vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md"
---

# F1-S0 `vitalia-fase1-stack-stability` — 01-spec

## § 1 — Resumen ejecutivo

F1-S0 establece la base técnica para el shell-organism Vitalia: verifica Tailwind v4 empíricamente en runtime, instala Shadcn UI con 8 primitivos copy-paste oficiales (Button, Avatar, DropdownMenu, Input, Badge, Textarea, Tabs, Tooltip), agrega CSS vars para los 7 agent tokens (Lisa #00D084 + Lucas #111111 son nuevos · Adrián/Valeria/Camila/Mateo/Config preexistentes en mockup), configura Playwright `@project=visual` con 6 goldens baseline (regression del legacy `(dashboard)/`, primitives showcase light+dark, agent tokens swatch light+dark), y cementa plan de deprecación incremental de las 150+ utility classes `.vt-*` vía `ADR-vitalia-002`. Sin esta story las 10 stories Fase 1 restantes (F1-S1..S10) no pueden empezar — F1-S0 es **blocker hard** del shell-organism completo.

**Anti-objetivos** (explícito qué NO hace esta historia):

- NO migrar `.vt-*` existentes a Tailwind directo (eso es story dedicada al final de Fase 2: `vitalia-fase2-vt-deprecation-final`)
- NO crear componentes shell (TopBarGlobal, ValeriaSidebar, Ribbon, etc. — eso son F1-S1..S10)
- NO tocar route group `(shell-organism)/` (eso es F1-S4)
- NO modificar `(dashboard)/` legacy (debe seguir funcionando idéntico post-install)
- NO instalar Shadcn en otras brands (nicolify, comunify, lupulo) — scope brand-local Vitalia
- NO refactor cross-feature en `vitalia/frontend/` existente

---

## § 2 — Visión (paradigma shell-organism)

F1-S0 es el **bootstrap técnico de la base UI de toda la aplicación Vitalia**. El shell-organism (5 agentes + Configurar + Mateo transversal sobre layout 50/50 con Valeria sidebar permanente) requiere primero que Tailwind v4 esté operativo + los primitivos Shadcn instalados + los agent tokens definidos como CSS vars + el sistema de goldens visuales configurado. Sin estos 4 ingredientes técnicos, las 10 stories siguientes (que construyen los componentes reales del shell) no tienen piso donde apoyarse.

**Agente owner:** SHELL (transversal — no es de un agente específico)
**Color oficial:** neutral (no aplica color de agente)
**Avatar PNG:** N/A (story infra, sin avatar)

---

## § 3 — Atomic Design Layers (referencia Design Contract § 3)

> F1-S0 INSTALA los átomos vía Shadcn CLI pero NO construye moléculas ni organismos. Eso es responsabilidad de F1-S1..S10.

### § 3.1 — Átomos INSTALADOS (8 primitivos Shadcn copy-paste)

| Átomo | Comando install | Path local post-install | Variantes que ofrece | Consumer downstream |
|---|---|---|---|---|
| `Button` | `npx shadcn@latest add button` | `vitalia/frontend/src/components/ui/button.tsx` | `default \| secondary \| ghost \| destructive \| outline \| link` × `size: default \| sm \| lg \| icon` | TopBarGlobal (F1-S2) · Rail btns (F1-S5) · Composer send (F1-S6) · everywhere |
| `Avatar` | `npx shadcn@latest add avatar` | `vitalia/frontend/src/components/ui/avatar.tsx` | `default` + `<AvatarImage>` + `<AvatarFallback>` | TenantSwitcher (F1-S3) · RibbonTab (F1-S7) · ChatHeader (F1-S6) |
| `DropdownMenu` | `npx shadcn@latest add dropdown-menu` | `vitalia/frontend/src/components/ui/dropdown-menu.tsx` | items + separator + label + shortcut | TenantSwitcher (F1-S3) |
| `Input` | `npx shadcn@latest add input` | `vitalia/frontend/src/components/ui/input.tsx` | `type: text \| email \| password \| search \| ...` | History search (F1-S5) · Composer input (F1-S6) |
| `Badge` | `npx shadcn@latest add badge` | `vitalia/frontend/src/components/ui/badge.tsx` | `default \| secondary \| destructive \| outline` | Chat mode pill (F1-S6) · Camila modes (F2) · Adrián modes (F2) |
| `Textarea` | `npx shadcn@latest add textarea` | `vitalia/frontend/src/components/ui/textarea.tsx` | `rows`, `placeholder` | Composer (F1-S6) |
| `Tabs` | `npx shadcn@latest add tabs` | `vitalia/frontend/src/components/ui/tabs.tsx` | `defaultValue`, `<TabsList>`, `<TabsTrigger>`, `<TabsContent>` | Catálogo\|Escalera Lisa (F2) · Kanban\|Lista Adrián (F2) · 3-modos Camila (F2) |
| `Tooltip` | `npx shadcn@latest add tooltip` | `vitalia/frontend/src/components/ui/tooltip.tsx` | `content`, `side: top \| right \| bottom \| left` | Rail buttons (F1-S5) · Topbar icons (F1-S2) |

**Dependencias NPM** que Shadcn CLI agrega automáticamente al `package.json`:
- `@radix-ui/react-{avatar,dropdown-menu,tabs,tooltip,slot,label}` (peer deps de Shadcn)
- `class-variance-authority` (variant system)
- `clsx` + `tailwind-merge` (cn helper)
- `lucide-react` (íconos default Shadcn)

### § 3.2 — Moléculas construidas en esta historia

**N/A — esta story es bootstrap técnico; las moléculas las construye F1-S1+ onwards.**

Moléculas planificadas para F1-S1..S10 según Design Contract § 3.2:
- `TenantSwitcher`, `ThemeToggle` (F1-S1, F1-S3)
- `RibbonTab`, `ConfigTab`, `SubTab` (F1-S7, F1-S8)
- `TenantOption`, `HistoryItem`, `HistoryGroup`, `ChatHeader` (F1-S3, F1-S5, F1-S6)
- `EmptyState`, `PlaceholderCard` (F1-S10)

### § 3.3 — Organismos construidos en esta historia

**N/A — esta story es bootstrap técnico; los organismos los construye F1-S1+ onwards.**

Organismos planificados según Design Contract § 3.3:
- `TopBarGlobal` (F1-S2) · `ValeriaSidebar` + `ValeriaRail` + `ValeriaHistory` + `ValeriaChat` (F1-S5, F1-S6) · `Ribbon` + `SubTabsBar` (F1-S7, F1-S8) · `ShellOrganismLayout` (F1-S4)

### § 3.4 — Templates / Pages modificadas

| Path | Acción | Detalle |
|---|---|---|
| `vitalia/frontend/components.json` | NEW | Output de `npx shadcn@latest init`. Config: style=`new-york`, baseColor=`slate`, cssVariables=true, importAlias=`@/`, tailwindConfig=existing |
| `vitalia/frontend/src/app/globals.css` | MODIFY | Agregar bloque `:root { ... }` con CSS vars Shadcn-style + 7 agent tokens (`--agent-lisa: 156 100% 41%; ...`). Agregar bloque `.dark { ... }` con dark variants. **Preservar bloque `.vt-*` legacy** (deprecación documentada en ADR-vitalia-002, NO ejecutada acá) |
| `vitalia/frontend/tailwind.config.ts` | MODIFY | Extend `theme.colors` con `background`, `foreground`, `primary`, `accent`, `muted`, `card`, `popover`, `border`, `input`, `ring`, `destructive`, y bloque `agent.{lisa,lucas,adrian,valeria,camila,mateo,config}` + soft variants. Verbatim copia de Design Contract § 5.2 |
| `vitalia/frontend/src/lib/utils.ts` | NEW or MODIFY | `cn()` helper Shadcn estándar: `import { clsx, type ClassValue } from "clsx"; import { twMerge } from "tailwind-merge"; export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }` |
| `vitalia/frontend/playwright.config.ts` | MODIFY (condicional) | Agregar `@project=visual` si no existe. Config verbatim Design Contract § 9.4: `viewport: 1440×900`, `snapshotPathTemplate`, `maxDiffPixelRatio: 0.001`, `animations: 'disabled'`, `caret: 'hide'` |
| `vitalia/frontend/package.json` | MODIFY | Shadcn CLI agrega deps automáticamente. Pre-merge: verificar lockfile `package-lock.json` versionado |
| `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` | NEW | Arch fitness test — falla si código bajo `src/components/shared/shell-organism/` o `src/app/[tenantId]/(shell-organism)/` usa `\bvt-[a-z]` class. Inicialmente GREEN by emptiness (esos paths no existen aún) |
| `vitalia/frontend/e2e/__test-pages__/stack-stability/primitives-showcase.tsx` | NEW | Test page Playwright — renderiza los 8 primitivos con todas sus variantes para golden visual |
| `vitalia/frontend/e2e/__test-pages__/stack-stability/agent-tokens-swatch.tsx` | NEW | Test page Playwright — renderiza 7 swatches color con label hex esperado para golden visual |
| `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts` | NEW | Spec Playwright `@project=visual` que genera los 6 goldens baseline (§ 7) |
| `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` | NEW | ADR brand-local. 8 secciones (§ 1-8). Deliverable de esta story (NO ejecuta migración) |

---

## § 4 — Reuse Map exhaustivo

### § 4.1 — REUSE desde Nicolify

**N/A — F1-S0 es greenfield Vitalia.** No se reutiliza componente ni pattern de Nicolify shipped UI. (Las stories F1-S1+ sí van a reusar patterns de Nicolify, ej. CopilotSidebar para ValeriaSidebar en F1-S5.)

### § 4.2 — REUSE desde core/luana-core-*

**N/A — F1-S0 es 100% infra FE local.** No consume packages `luana_core_*` ni TS packages `@luana/*`.

### § 4.3 — REUSE desde Vitalia shipped

| Asset | Path actual | Acción en F1-S0 |
|---|---|---|
| `vitalia/frontend/src/app/globals.css` (legacy `.vt-*` block) | shipped | **PRESERVAR INTACTO**. Decisión D2 deprecación es PROGRESIVA, no inmediata. El bloque `.vt-*` queda apuntando a nuevos CSS vars (`--background`, `--foreground`, etc.) para compatibilidad temporal. ADR-vitalia-002 documenta plan deprecación |
| `vitalia/frontend/tailwind.config.ts` existente | shipped | **EXTENDER** con nuevas keys `theme.extend.colors.agent.*`. NO romper config existente |
| Avatars PNGs `vitalia/frontend/public/agents/{lisa,lucas,adrian,valeria,camila,mateo}/thumbnail.png` | shipped (recovery 2026-05-21) | **NO TOCAR**. F1-S0 no los consume; F1-S1+ sí |
| Storage Clerk auth + middleware existente | shipped | **NO TOCAR**. F1-S0 no toca rutas autenticadas |
| Legacy `(dashboard)/` page tree | shipped | **NO TOCAR**. Coexiste hasta Fase 2 completa. F1-S0 verifica via golden regression que NO se rompe post-install |

### § 4.4 — NEW (creado en esta historia)

| Artefacto NEW | Razón |
|---|---|
| 8 primitivos Shadcn (`button.tsx`, `avatar.tsx`, etc.) en `src/components/ui/` | **Vendored Shadcn CLI registry** — copy-paste oficial desde `https://ui.shadcn.com/r/`. No es código de autor Luana ni replica patrones existentes en Vitalia/Nicolify/core. Editable post-install (esa es la promesa Shadcn vs npm package) |
| 7 agent tokens CSS vars (`--agent-lisa`, `--agent-lucas`, `--agent-adrian`, etc.) | Tokens cementados en Design Contract § 5.1 — Lisa #00D084 + Lucas #111111 son NEW (no estaban en globals.css pre-F1-S0); Adrián/Valeria/Camila/Mateo preexistían en mockup pero NO como CSS vars formales |
| Tailwind config extend `theme.colors.agent.*` | Required para que clases utility como `bg-agent-lisa text-agent-lucas-soft` resuelvan |
| `src/lib/utils.ts::cn()` helper | Shadcn standard — sin esto los primitivos no compilan. Si ya existe (de shipped Vitalia), reusar; si no, crear |
| `playwright.config.ts @project=visual` block | Required para generar los 6 goldens baseline. Si ya existe en config Vitalia shipped, skip; si no, agregar verbatim Design Contract § 9.4 |
| Arch fitness test `test-no-vt-classes-in-new-features.test.ts` | Enforcement maquina del plan deprecación `.vt-*` ADR-vitalia-002. Greenfield-protective (path scan vacío inicialmente) |
| `ADR-vitalia-002-vt-deprecation-plan.md` | Estrategia documentada deprecación 150+ `.vt-*` classes. NO ejecuta migración acá |
| 2 test pages auxiliares + 1 spec Playwright visual baseline | Goldens infra-baseline que F1-S1..S10 heredan como contrato |

### § 4.5 — Legacy `/home/chalreme/Documentos/ap_sales_agent`

**N/A — F1-S0 no consulta legacy single-brand pre-multibrand.**

---

## § 5 — API contracts (BE ↔ FE)

**N/A runtime — esta story es 100% infra FE local, sin endpoints consumidos en runtime.**

### Build-time note: Shadcn CLI registry fetch

`npx shadcn@latest init` y `npx shadcn@latest add ...` hacen fetch HTTP a `https://ui.shadcn.com/r/` durante el install para descargar los `.tsx` source de los primitivos. Los archivos resultantes (`components/ui/*.tsx`, `components.json`) quedan **committed en el repo Vitalia**, por lo que **post-merge la reproducibilidad es 100% determinística desde git** — las stories F1-S1..S10 NO requieren acceso al registry Shadcn durante su build. Solo stories futuras que agreguen primitives nuevos (Fase 2 según mapping Design Contract § 4 — Card, ScrollArea, Separator, Sheet, Popover, Accordion, Progress, etc.) van a necesitar conectividad al registry durante install.

**Implicancia operativa:**
- CI build offline: ✅ funciona (los `.tsx` están commited)
- Reproducir install desde git clone limpio: ✅ funciona vía `npm install` (lockfile pin de Radix deps + class-variance-authority + clsx + tailwind-merge + lucide-react)
- Si registry Shadcn temporalmente caído durante F1-S0 install: STOP, escalate Chris — install se reintenta cuando registry vuelve

---

## § 6 — Acceptance Criteria (Gherkin AI-resistant)

> 6 scenarios funcionales activos + 1 adversarial-declared con razón + 1 bloque consolidado de N/A con razón. Total: 8 entradas que satisfacen gate `/po-ux v4.1` (cada sub-categoría tiene scenario o `not_applicable_reason` explícito).

### Scenario 1 — `happy-path` (type: happy)

**Given:**
- Repo Vitalia clonado limpio en `~/Proyectos/luana-vitalia/`
- Dependencias raíz instaladas (`uv sync` + `pnpm install` desde root workspace)
- F1-S0 implementación pre-cambios: Shadcn NO instalado, CSS vars Shadcn-style ausentes, primitivos `components/ui/{button,avatar,...}.tsx` no existen

**When:**
- Developer/builder ejecuta los 7 pasos § 1-§ 7 del checkpoint en orden
- Developer ejecuta `make dev-vitalia` desde workspace root
- Stack arranca → `http://localhost:3002` abierto en browser

**Then:**
- Página default del legacy `(dashboard)/` carga sin errors visual ni console
- Tailwind classes (ej. `bg-blue-500`, `text-gray-800`, `rounded-lg`) renderizan correctamente
- DevTools Console NO muestra "Failed to fetch CSS" ni "Tailwind plugin failed"
- Visual NO regresión vs golden `e2e/__screenshots__/stack-stability/dashboard-legacy-light.png`
- 8 primitivos Shadcn existen en `src/components/ui/`
- `import { Button } from '@/components/ui/button'` resuelve sin TS errors
- `globals.css` contiene bloques `:root { ... }` + `.dark { ... }` con CSS vars Shadcn-style + 7 agent tokens
- `tailwind.config.ts` `colors.agent.{lisa,lucas,adrian,valeria,camila,mateo,config}` accesibles
- `npx tsc --noEmit` retorna exit 0
- `npx eslint src/` retorna exit 0
- `npm run build` (production build) retorna exit 0
- `npx vitest run` (tests existentes regresión) retorna exit 0 todos green

**playwright_required:** true
**Graders:**
- E2E functional: `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts`
- Visual golden: `vitalia/frontend/e2e/__screenshots__/stack-stability/dashboard-legacy-light.png`
- State check: file existence (`components.json`, 8 primitivos)
- TS check: `tsc --noEmit` shell command exit 0

---

### Scenario 2 — `negative` (type: negative) — Tailwind v4 ROTO

> Cubre learning 2026-05-21 `auto-handoff-deferred-e2e-blocker` que reportó "Tailwind no renderiza en runtime" en sesión previa. F1-S0 atrapa empíricamente.

**Given:**
- `make dev-vitalia` ejecutado
- Browser abierto en `http://localhost:3002`

**When:**
- Página carga pero estilos NO se aplican (raw browser default visible)
- DevTools Console muestra warnings o errors relacionados a Tailwind/PostCSS

**Then:**
- Developer documenta repro en `T-1-impl-log.md` (commit/sub-ticket dedicado)
- Diagnosis estructurado checkea:
  - `postcss.config.{js,mjs,ts}` presente y correcto
  - `globals.css` contiene `@tailwind base; @tailwind components; @tailwind utilities;` (v3) o equivalente v4 directives
  - Turbopack vs Webpack: `next dev` está usando el bundler esperado
  - Tailwind v4 plugin React 19 compat verificado (peer-deps satisfechos)
- Fix aplicado + verificado visualmente reload browser
- Story NO transitions a `developed` hasta AC-2 (este Scenario) pass

**playwright_required:** true
**Graders:**
- E2E functional: `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts` (mismo spec con assertion explícita: Tailwind class resuelve a color esperado)
- Manual browser check Chris ratifica visualmente

---

### Scenario 3 — `happy-shadcn` (type: edge — primitive render correcto post-install)

**Given:**
- F1-S0 completado: Shadcn instalado, 8 primitivos en `src/components/ui/`
- Test page Playwright `e2e/__test-pages__/stack-stability/primitives-showcase.tsx` renderiza los 8 primitivos con todas sus variantes

**When:**
- Playwright `@project=visual` ejecuta spec contra la test page

**Then:**
- `<Button variant="default">` renderiza con `bg-primary text-primary-foreground` + `rounded-md` + padding según `--radius`
- `<Button variant="secondary">`, `ghost`, `destructive`, `outline` cada uno renderiza con su variant esperado
- `<Avatar>` con fallback letras renderiza círculo con texto centrado
- `<DropdownMenu>` open state muestra items
- `<Input>` renderiza con borde `--input` + focus ring `--ring`
- `<Badge>` con cada variant renderiza con colores correctos
- `<Textarea>` renderiza textarea con estilos Shadcn
- `<Tabs>` con `<TabsList>` + `<TabsTrigger>` + `<TabsContent>` renderiza segmented control
- `<Tooltip>` open state muestra tooltip con flecha
- Visual diff vs golden `shadcn-primitives-showcase-light.png` < 0.1% pixel ratio
- Visual diff vs golden `shadcn-primitives-showcase-dark.png` < 0.1% pixel ratio en `colorScheme: 'dark'`

**playwright_required:** true
**Graders:**
- Visual golden: `e2e/__screenshots__/stack-stability/shadcn-primitives-light.png`
- Visual golden: `e2e/__screenshots__/stack-stability/shadcn-primitives-dark.png`
- Hover/focus state assertion (Playwright `page.hover()` + `expect(elem).toHaveCSS(...)`)

---

### Scenario 4 — `happy-tokens` (type: happy + theme-switch inline structural check)

> Incorpora la verificación estructural dark mode (decisión B Batch 2): F1-S0 NO construye el toggle visual (eso es F1-S1), pero SÍ deja las dark vars correctas en `globals.css`. Scenario verifica estructuralmente.

**Given:**
- F1-S0 completado: agent tokens agregados en `globals.css` + `tailwind.config.ts`
- Test page `e2e/__test-pages__/stack-stability/agent-tokens-swatch.tsx` renderiza 7 swatches con label hex esperado

**When:**
- Grep `globals.css` post-install
- Playwright `@project=visual` ejecuta spec contra swatch test page en light + dark

**Then:**
- `globals.css` contiene bloque `:root { --agent-lisa: 156 100% 41%; --agent-lucas: 0 0% 7%; --agent-adrian: 198 99% 49%; --agent-valeria: 287 53% 37%; --agent-camila: 244 84% 32%; --agent-mateo: 53 99% 51%; --agent-config: 240 4% 46%; ... }`
- `globals.css` contiene bloque `.dark { --agent-lisa-soft: 156 60% 15%; --agent-lucas-soft: 0 0% 20%; --agent-adrian-soft: 198 60% 20%; --agent-valeria-soft: 287 40% 25%; --agent-camila-soft: 244 50% 20%; ... }`
- `tailwind.config.ts` `colors.agent.lisa` resuelve via Tailwind class `bg-agent-lisa` a `hsl(156 100% 41%) = #00D084`
- Idem `bg-agent-lucas` → `hsl(0 0% 7%) = #111111`
- Idem 5 agents restantes (adrian/valeria/camila/mateo/config)
- Visual diff vs golden `agent-tokens-swatch-light.png` < 0.1%
- Visual diff vs golden `agent-tokens-swatch-dark.png` < 0.1% (verifica `.dark` block aplica soft variants)

**playwright_required:** true
**Graders:**
- Visual golden: `e2e/__screenshots__/stack-stability/agent-tokens-swatch-light.png`
- Visual golden: `e2e/__screenshots__/stack-stability/agent-tokens-swatch-dark.png`
- State check structural: `grep -c "^\\s*--agent-" vitalia/frontend/src/app/globals.css` ≥ 12 (7 base + 5+ soft variants dark)
- Vitest token introspection: `src/__tests__/tokens/test-agent-tokens.test.ts` valida hex exacto

---

### Scenario 5 — `edge` (type: edge — Shadcn install partial failure)

**Given:**
- `npx shadcn@latest init` ejecutado, prompts respondidos
- React 19 instalado en `package.json` Vitalia

**When:**
- Shadcn CLI detecta peer-dep conflict con `@radix-ui/react-*` que requieren React ≤18 (o reporta warning React 19)
- O Shadcn CLI falla en medio del install dejando `components.json` parcial

**Then:**
- Build artifact corrupto (algunos primitivos presentes, otros ausentes)
- Developer ejecuta `npm install --force` o investiga compatibility matrix Shadcn × React 19
- Si Shadcn declared NO React 19 compat al momento de F1-S0: STOP, escalate `/pm-vitalia` → posible workaround (Shadcn fork temporal con React 18 peer-dep override, o downgrade React 18 temporal hasta Shadcn ship React 19 compat)
- Documentado en `T-impl-log.md` + ADR-vitalia-002 § 8 Riesgos + mitigaciones
- Story NO transitions a `developed` hasta install completo + golden Scenario 3 pass

**playwright_required:** false (es failure mode pre-Playwright)
**Graders:**
- State check: `ls vitalia/frontend/src/components/ui/` = 8 files exactos
- State check: `cat vitalia/frontend/components.json` válido JSON
- npm: `npm ls @radix-ui/react-avatar` resuelve sin UNMET PEER DEP

---

### Scenario 6 — `error-state` (type: error — build post-install)

**Given:**
- F1-S0 implementación completa (todos los pasos § 1-§ 7 checkpoint ejecutados)
- Pero hay inconsistencia: alguna CSS var referenciada en `tailwind.config.ts` NO existe en `globals.css` (typo, drift, copy-paste error)

**When:**
- Developer ejecuta `npm run build` (production build verifica todo el pipeline)

**Then:**
- Build FALLA con error útil que cita:
  - Nombre del CSS var faltante (ej. `--agent-lisa-soft was used but not defined`)
  - File + line donde se usa
  - Sugerencia fix (ej. "agregar `--agent-lisa-soft: 156 80% 92%;` en `:root`")
- Developer aplica fix, re-ejecuta `npm run build` → exit 0
- Sin esta verificación: el dev stack runtime puede funcionar (Tailwind v4 lenient en dev) pero production build rompe → catch tardío en CD pipeline

**playwright_required:** false (es build-time check)
**Graders:**
- Shell: `npm run build` exit code 0
- Smoke regression: re-ejecutar Scenario 1 post-build

---

### Scenario 7 — `adversarial` (type: not_applicable con razón rigurosa)

**adversarial: not_applicable**

**Razón:** F1-S0 es bootstrap técnico build-time sin user input surface, sin auth runtime, sin PHI exposure. El único vector adversarial es **supply-chain del registry Shadcn** (`https://ui.shadcn.com/r/`). Esto NO se cubre como scenario en este spec porque:

1. El blast radius es developer-machine durante install, no producción runtime.
2. Mitigación canónica vive en `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` § 7 "Post-install audit checklist" (diff review de los 8 primitivos line-by-line, lockfile pin review, version pinning Shadcn CLI, no auto-upgrades sin re-review).
3. `/auditor` review del PR F1-S0 examina el diff de los 8 primitivos `.tsx` copy-paste contra el registry Shadcn oficial — auditor manual catchea código injection si lo hubiera.
4. Cualquier story Fase 2 que agregue primitives nuevos repite este review gate `/auditor`.

**Si en el futuro escaneo `/pm-luana scan-promotables` detecta patrón cross-brand de supply-chain risk significativo → lift a `core/luana-core-platform/security/supply-chain-policy.md`** o a `.claude/rules/supply-chain-policy.md` raíz (promotable candidate).

---

### Scenario 8 — `not_applicable batch` (sub-categorías mandatory que no aplican)

> Gate `/po-ux v4.1` requiere cubrir sub-categorías con scenario o `not_applicable_reason` explícito. F1-S0 es infra-only, las siguientes 8 sub-categorías genuinamente no aplican:

```yaml
not_applicable_sub_categories:
  - sub_category: race_condition
    reason: "F1-S0 no introduce endpoints con create/update ni unique constraints DB. Es 100% infra FE local."
  - sub_category: concurrent_users
    reason: "F1-S0 no introduce list/detail filterable user-facing. Los primitivos Shadcn son stateless. No hay surface multi-user."
  - sub_category: network_failure
    reason: "F1-S0 no introduce fetch FE runtime. El único fetch es build-time al registry Shadcn (cubierto en § 5 Build-time note + Scenario 5 edge)."
  - sub_category: empty_state
    reason: "F1-S0 no introduce list/dashboard que pueda tener 0 items. Empty states son responsabilidad de F1-S10."
  - sub_category: large_dataset
    reason: "F1-S0 no introduce pagination ni list rendering. No hay dataset que pueda crecer."
  - sub_category: accessibility (keyboard-a11y)
    reason: "F1-S0 no introduce UI user-facing nueva (las 2 test pages son fixtures Playwright). Los primitivos Shadcn vienen con a11y nativa upstream (Radix). A11y verificación per-organismo es responsabilidad F1-S1..S10."
  - sub_category: mobile-responsive
    reason: "F1-S0 no introduce UI nueva. Mobile responsive verificación per-organismo es responsabilidad F1-S1..S10."
  - sub_category: loading-state
    reason: "F1-S0 no introduce async UI ni async data fetching. Install Shadcn es comando shell síncrono."
  - sub_category: i18n
    reason: "F1-S0 no introduce copy user-facing nuevo en pantalla. ADR-vitalia-002 es doc interno (voseo-allowed via magic comment). Test pages auxiliares no son user-facing."
```

---

## § 7 — Visual Goldens (mockup como source of truth)

> **F1-S0 es la story que ESTABLECE el contrato visual baseline que las 10 stories siguientes heredan.** Sin los 6 goldens infra de F1-S0, F1-S1..S10 no tienen ratchet anti-drift cuando consuman los primitivos Shadcn ni los agent tokens.

### § 7.1 — 6 snapshots requeridos (baseline infra-only)

| # | Snapshot | Viewport | Theme | Propósito | Path golden |
|---|---|---|---|---|---|
| 1 | `dashboard-legacy-regression-light` | 1440×900 | light | **CRITICAL**: pre-install vs post-install del `(dashboard)/` legacy. Confirma D2 plan deprecación `.vt-*` NO rompe shipped UI durante coexistencia | `vitalia/frontend/e2e/__screenshots__/stack-stability/dashboard-legacy-light.png` |
| 2 | `dashboard-legacy-regression-dark` | 1440×900 | dark | Idem dark mode legacy | `vitalia/frontend/e2e/__screenshots__/stack-stability/dashboard-legacy-dark.png` |
| 3 | `shadcn-primitives-showcase-light` | 1280×800 | light | **BASELINE**: 8 primitivos Shadcn renderizando todas sus variantes (Button × 5 variants × 4 sizes, Input, Avatar, Badge × 4 variants, Textarea, Tabs, Tooltip) — contrato visual para F1-S1+ que reusan | `vitalia/frontend/e2e/__screenshots__/stack-stability/shadcn-primitives-light.png` |
| 4 | `shadcn-primitives-showcase-dark` | 1280×800 | dark | Idem dark mode primitivos | `vitalia/frontend/e2e/__screenshots__/stack-stability/shadcn-primitives-dark.png` |
| 5 | `agent-tokens-swatch-light` | 800×600 | light | **BASELINE**: 7 swatches color con label hex esperado (lisa #00D084, lucas #111111, adrian #01b2f8, valeria #7b2d91, camila #180d95, mateo #fee209, config gray) — contrato hex para F1-S1+ que consumen agent tokens | `vitalia/frontend/e2e/__screenshots__/stack-stability/agent-tokens-swatch-light.png` |
| 6 | `agent-tokens-swatch-dark` | 800×600 | dark | Idem con dark soft variants — verifica `.dark` block aplica correctamente | `vitalia/frontend/e2e/__screenshots__/stack-stability/agent-tokens-swatch-dark.png` |

### § 7.2 — Trazabilidad mockup → golden → componente (contrato auditable)

> Para F1-S0 (infra-only) el mapping es directo: los goldens cementan baseline. Para F1-S1..S10 (que construyen componentes) el mapping va a expandirse según ADR-vitalia-003 § Workflow.

| Mockup ref | Golden path | Componente verificado | Design Contract ref |
|---|---|---|---|
| Mockup integral `dual-mode-shell.html` (página default current) | `dashboard-legacy-light.png` + `dashboard-legacy-dark.png` | Legacy `(dashboard)/` page (NO rompe post-install) | § 5.1 CSS vars coexistencia |
| Shadcn primitives oficiales (registry `https://ui.shadcn.com/r/`) | `shadcn-primitives-light.png` + `shadcn-primitives-dark.png` | 8 primitivos `src/components/ui/` | § 3.1 átomos |
| Design Contract § 5.1 agent tokens (hex declarado) | `agent-tokens-swatch-light.png` + `agent-tokens-swatch-dark.png` | CSS vars + `tailwind.config.ts colors.agent.*` | § 5.1 + § 5.2 |

### § 7.3 — Test pages auxiliares (Playwright fixtures)

**Path:** `vitalia/frontend/e2e/__test-pages__/stack-stability/`

```
__test-pages__/
└── stack-stability/
    ├── primitives-showcase.tsx       # Renderiza los 8 primitivos con TODAS sus variantes
    └── agent-tokens-swatch.tsx        # Renderiza 7 swatches color con label hex
```

Estas test pages son **fixtures Playwright NO user-facing** — montadas solo por specs `@project=visual` para generar goldens. NO son rutas Next.js prod. Quedan bajo `e2e/__test-pages__/` (consumidas via Playwright `goto` con file:// o test server local).

Mockups HTML aux (para discusion previo a builder dev):

```
mockups/                                # NO requerido per ADR-vitalia-003 § Excepciones
                                        # F1-S0 es EXENTA del protocolo mockup-per-component
                                        # (no construye componentes user-facing nuevos)
```

### § 7.4 — Generación inicial vs verify

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Generación inicial (builder ejecuta tras finalizar install Shadcn + tokens):
npx playwright test --project=visual --grep "stack-stability" --update-snapshots
# Chris revisa diff humano vs mockup HTML + Design Contract § 5.1 antes de ratify

# Verify CI (auto en cada PR FE):
npx playwright test --project=visual --grep "stack-stability"
# Falla si diff > 0.1% pixels
```

### § 7.5 — Tolerancia + animaciones (verbatim Design Contract § 9.4)

- `maxDiffPixelRatio: 0.001` (0.1%)
- `animations: 'disabled'` (sin flaky)
- `caret: 'hide'` (cursores textareas no afectan diff)

---

## § 8 — Acceptance criteria operacionales

> Consolida los 13 AC del checkpoint en formato tabla del template.

| # | Criterio | Verificación |
|---|---|---|
| AC-1 | `make dev-vitalia` arranca sin errors en console (browser + terminal) | Manual + Scenario 1 grader |
| AC-2 | `http://localhost:3002` renderiza con estilos Tailwind aplicados | Scenario 1 + 2 graders |
| AC-3 | `vitalia/frontend/components.json` existe + config Shadcn correcta (style=new-york, baseColor=slate, cssVariables=true) | State check file existence + JSON parse |
| AC-4 | Los 8 primitivos existen: `button avatar dropdown-menu input badge textarea tabs tooltip` en `src/components/ui/` | `ls vitalia/frontend/src/components/ui/` = exactly 8 files (+ utils.ts si está acá) |
| AC-5 | Import test `import { Button } from '@/components/ui/button'` funciona sin TS errors | `npx tsc --noEmit` exit 0 |
| AC-6 | `globals.css` tiene CSS vars `--agent-lisa`, `--agent-lucas`, etc. en `:root` + dark variants en `.dark` | Scenario 4 state check structural |
| AC-7 | `tailwind.config.ts` `colors.agent.{lisa,lucas,adrian,valeria,camila,mateo,config}` accesibles vía Tailwind classes | Scenario 4 visual goldens 5+6 |
| AC-8 | `ADR-vitalia-002-vt-deprecation-plan.md` escrito + ratificado Chris | File existence + ratificación manual |
| AC-9 | Arch fitness test `test-no-vt-classes-in-new-features.test.ts` creado | File existence + `npx vitest run` GREEN by emptiness |
| AC-10 | `npx tsc --noEmit` 0 errors | Shell exit 0 |
| AC-11 | `npx eslint src/` 0 errors | Shell exit 0 |
| AC-12 | `npm run build` PASS (production build) | Scenario 6 grader |
| AC-13 | Tests existentes regresión PASS (`npx vitest run` GREEN sobre Vitalia shipped) | Shell exit 0 |
| AC-14 ★ NEW | Playwright `@project=visual` configurado en `playwright.config.ts` con maxDiffPixelRatio 0.001 + animations disabled + caret hide | grep config snippet |
| AC-15 ★ NEW | 6 goldens baseline generados + ratificados Chris visualmente (post-install dashboard regression + primitives showcase + agent tokens swatch, light + dark cada uno) | Playwright `@project=visual` GREEN + ratificación manual |
| AC-16 ★ NEW | `src/lib/utils.ts::cn()` helper Shadcn presente (`twMerge(clsx(inputs))`) | File grep + import test |

---

## § 9 — Zero deuda técnica — checklist mandatorio

> Auditor REFUSE merge si algún item aplicable falla.

- [ ] **Lint:** `npx eslint src/` --max-warnings 0 (sobre `globals.css` no aplica; sobre `tailwind.config.ts` + `utils.ts` + arch test + test pages aplica)
- [ ] **TypeScript:** `npx tsc --noEmit` 0 errors
- [ ] **Format:** `npx prettier --check vitalia/frontend/src/`
- [ ] **Vitest tests:** todos los tests existentes + arch fitness nuevo PASS
- [ ] **Playwright functional E2E:** Scenarios 1, 2, 3, 5, 6 pass
- [ ] **Playwright visual goldens:** 6 baseline goldens generados + reviewed por Chris
- [ ] **NO `.vt-*` classes en código nuevo:** arch test green (by emptiness inicial)
- [ ] **NO `any` TypeScript** en código nuevo (utils.ts, test pages, arch test)
- [ ] **NO default exports** en código nuevo (FSD-Lite enforce)
- [ ] **NO cross-feature imports** (boundaries ESLint pass)
- [ ] **NO cross-brand imports** (`{other_brand}/...`)
- [ ] **NO core engine direct edits** (F1-S0 NO toca `core/luana-core-*`)
- [ ] **CSS variables consumidas** en `tailwind.config.ts` extend (NO hex hardcoded)
- [ ] **Spanish neutro LatAm:** N/A (F1-S0 no introduce strings user-facing nuevos; ADR-vitalia-002 lleva magic comment `voseo-allowed: internal architecture documentation`)
- [ ] **ADR-vitalia-002 ratificado** por Chris (8 secciones según checkpoint § 5 + recomendación batch 3)
- [ ] **Lockfile committed:** `vitalia/frontend/package-lock.json` o `pnpm-lock.yaml` con nuevas deps Shadcn (Radix + class-variance-authority + clsx + tailwind-merge + lucide-react)
- [ ] **Build production:** `npm run build` exit 0
- [ ] **Storybook story:** N/A (F1-S0 no construye componentes — F1-S1+ sí)
- [ ] **Mobile responsive:** N/A (F1-S0 no introduce UI nueva)
- [ ] **Dark mode:** infra ready (CSS vars `.dark` block presentes) — toggle visual es F1-S1
- [ ] **HIPAA-lite no-phi-scope declared:** F1-S0 es infra UI bootstrap; compliance dual-filter aplica desde F1-S1 onwards cuando se tocan rutas autenticadas con data sensible
- [ ] **`ratified_visual_by_chris: not_applicable`** declarado en frontmatter con razón (ADR-vitalia-003 § Excepciones — F1-S0 exenta por infra-only)

---

## § 10 — Dependencies map

### § 10.1 — Dependencies hard (bloquean implementación)

```
F1-S0 NO depende de ninguna story. Es el bootstrap técnico del shell.
```

### § 10.2 — Dependencies soft

```
N/A
```

### § 10.3 — Service blockers BE

```
N/A — F1-S0 es 100% FE.
```

### § 10.4 — Esta historia bloquea (downstream)

```
F1-S0 desbloquea HARD las 10 stories Fase 1 siguientes:
  1. vitalia-fase1-design-tokens-theme       (F1-S1)
  2. vitalia-fase1-topbar-global              (F1-S2)
  3. vitalia-fase1-tenant-switcher            (F1-S3)
  4. vitalia-fase1-shell-layout-5050          (F1-S4)
  5. vitalia-fase1-valeria-rail-history       (F1-S5)
  6. vitalia-fase1-valeria-chat-skeleton      (F1-S6)
  7. vitalia-fase1-ribbon-6-tabs              (F1-S7)
  8. vitalia-fase1-sub-tabs-line2             (F1-S8)
  9. vitalia-fase1-routing-shell              (F1-S9)
  10. vitalia-fase1-empty-states               (F1-S10)
```

Razón: sin Shadcn instalado + agent tokens + Playwright `@project=visual` + arch fitness `.vt-*` enforce, las 10 stories siguientes no tienen piso técnico ni ratchet anti-drift.

---

## § 11 — Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Tailwind v4 runtime bug** (learning 2026-05-21 reportó "no renderiza"; subagent Explore 2026-05-22 reportó "operativo" — discrepancia abierta) | Media | Alto | Scenario 2 verifica empíricamente. Fallback documentado en ADR-vitalia-002 § 8: si Tailwind v4 incompatible con React 19 → downgrade temporal Tailwind v3 hasta v4 stabilize (Tailwind v4 stable Q1 2026 per upstream) |
| **Shadcn primitives React 19 peer-dep conflict** | Baja-Media | Alto | Shadcn declared React 19 compat 2025-Q4. Scenario 5 atrapa install partial failure. Workaround: peer-deps override en `package.json` si necesario |
| **`.vt-*` deprecation rompe shipped `(dashboard)/`** | Media | Medio | Goldens 1+2 (regression light+dark) catchan visualmente. ADR-vitalia-002 § 3 documenta estrategia compatibility temporal (bloque `.vt-*` apunta a nuevas CSS vars) |
| **Shadcn registry supply-chain** (código injection en primitive copy-paste) | Baja | Alto | ADR-vitalia-002 § 7 post-install audit checklist (diff review line-by-line). `/auditor` review del PR examina los 8 primitivos `.tsx` |
| **CSS vars colisión con `.vt-*` legacy** (ej. `--background` redefine semántica) | Media | Medio | Goldens 1+2 regression light+dark catchan. Spec § 4.3 declara preservar `.vt-*` block intacto durante transición |
| **Playwright `@project=visual` flaky en CI** (font rendering, browser version drift) | Media | Bajo | Design Contract § 9.4 config (animations disabled + caret hide + maxDiffPixelRatio 0.001). Si flaky persiste: pin browser version en CI workflow + Chris re-ratifica goldens trimestral |
| **Goldens commit weight** (PNG files crece repo) | Baja | Bajo | `vitalia/frontend/e2e/__screenshots__/` con `.gitattributes` LFS si crecen >5MB cumulative. F1-S0 baseline ~500KB total |

---

## § 12 — Definición de "Done"

F1-S0 transitions `developing → developed` cuando:

1. **Todos los AC-1..AC-16 del § 8 verificados** (manual + automated)
2. **Todos los items aplicables del checklist § 9 ✓**
3. **6 Playwright visual goldens generados + ratificados Chris** visualmente
4. **6 Gherkin scenarios funcionales (1, 2, 3, 4, 5, 6) pass** + Scenario 7 documentado N/A + Scenario 8 bloque N/A documentado
5. **ADR-vitalia-002 escrito + ratificado** Chris (8 secciones)
6. **Arch fitness test creado + GREEN** (`test-no-vt-classes-in-new-features.test.ts`)
7. **Story commits pushed** + branch `wip/vitalia` sync con `main`
8. **`T-{n}-result.md`** escrito con SHA commits + log decisiones implementación (Shadcn CLI prompts respuestas, dark vars elegidas, fallback Tailwind v3 si se activó, etc.)
9. **Handoff `/auditor`** emitido automáticamente (story closure gate)

Auditor APPROVED → `/pm-vitalia merge` → state `done` → 10 stories Fase 1 unblocked.

---

## § 13 — Referencias

### SSoT obligatorios citados

- **Design Contract** atomic design SSoT: `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (633 líneas)
- **Template spec SHELL** (esqueleto 14 secciones): `vitalia/docs/specs/templates/01-spec-shell-template.md` (494 líneas)
- **Mockup HTML integral** visual SSoT: `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (1439 líneas, ratificado 2026-05-22)
- **Baseline funcional shell** (17 decisiones): `vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md` (1068 líneas)
- **Outcome master** Fase 1+2: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` v2.0 (214 líneas)

### Deliverables de esta story (referenciados, no embedded)

- **ADR-vitalia-002 plan deprecación `.vt-*`** (NEW en F1-S0): `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` — 8 secciones (contexto, inventario, estrategia compatibility, migration policy, final drop, arch fitness test, post-install audit checklist supply-chain, riesgos + mitigaciones)
- **ADR-vitalia-003 protocolo mockup-per-component** (cementado durante refining F1-S0): `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md`
- **Rule overlay enforcement**: `vitalia/.claude/rules/shell-mockup-per-component.md`
- **Learning brand-local promotable**: `vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md`

### Reglas raíz aplicables

- **FSD-Lite enforcement**: `.claude/rules/frontend-fsd.md` (boundaries que F1-S1+ van a cumplir cuando consuman los primitivos)
- **HIPAA-lite overlay**: `vitalia/.claude/rules/hipaa-lite.md` — **no-phi-scope declared**: F1-S0 es infra UI bootstrap; compliance dual-filter aplica desde F1-S1 onwards cuando se tocan rutas autenticadas con data sensible
- **Spanish neutro**: `.claude/rules/spanish-text.md` — **no-copy-scope declared**: F1-S0 no introduce strings user-facing nuevos. ADR-vitalia-002 lleva magic comment `voseo-allowed: internal architecture documentation`
- **Brand docs schema R1+R2+R3**: `.claude/rules/brand-docs-schema.md` — todo `01-spec.md` vive en `vitalia/docs/product/stories/{id}/`, NO en raíz `vitalia/docs/`
- **Story closure gate**: `.claude/rules/story-closure-gate.md` — Fase F MERGE concreta archive a `vitalia/docs/archive/{year}/stories/`

### § 13.1 — Protocolo mockup-per-component (F1-S1..S10) — gate bloqueante pre-`/architect`

> **F1-S0 NO está sujeta a este protocolo** (declarada exenta en ADR-vitalia-003 § Excepciones porque es infra-only sin componentes user-facing nuevos). **Las 10 stories siguientes Fase 1 SÍ lo están**, así como las ~22 stories Fase 2 que construyan componentes UI.

**SSoT del protocolo:**
- `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` — autoridad arquitectónica brand-local (por qué + criterios evaluados + consecuencias)
- `vitalia/.claude/rules/shell-mockup-per-component.md` — enforcement de máquina (skills lo cargan automáticamente al trabajar en stories Vitalia Fase 1+2)

**Workflow obligatorio para F1-S1..S10 + stories Fase 2 con UI nueva:**

1. `/po-ux` redacta `01-spec.md` con § 3 Atomic Design Layers + § 4 Reuse Map del template SHELL
2. `/po-ux` genera mockup HTML por componente nuevo en `vitalia/docs/product/stories/{story-id}/mockups/{component}.html` (Tailwind CDN + tokens Vitalia via CSS vars + datos LatAm realistas + Spanish neutro + dark mode si soporta)
3. `/po-ux` levanta `python3 -m http.server 8888` desde `mockups/` y comparte URL local con Chris
4. Chris revisa visual + interactivo + ratifica componente-por-componente o pide cambios
5. `/po-ux` itera mockups hasta ratify whole-spec
6. `checkpoint.md::ratified_visual_by_chris: true` + `ratified_visual_mockups: [paths]` actualizado
7. Spec transitions `state: refining → refined` SOLO si flag visual ratificado
8. `/architect` REFUSE arrancar si flag ausente o `mockups/` vacío

**Excepciones (no aplica el protocolo):**

- F1-S0 (esta story — infra-only, declarada exenta)
- Service-stories (BE only)
- Agentic-stories conversacionales puras (usar `/ux-agentico` en su lugar)
- Stories Fase 2 que solo agregan data a componentes ya ratificados Fase 1

**Promotion candidate:** patrón cross-brand candidato a lift cuando N≥2 brands adopten — `vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md` lleva `promotable: candidate` para `/pm-luana scan-promotables` detection.

### § 13.2 — Compliance scope (no-phi-scope declared)

F1-S0 es infra UI bootstrap. **NO toca `patient_*`, `medical_*`, `treatment_*`, `prescription_*`, ni ninguna tabla/módulo PHI**. Las salvaguardas HIPAA-lite (`vitalia/.claude/rules/hipaa-lite.md`) NO aplican a este spec.

Compliance dual-filter `tenant_id` + `clinic_id` aplica desde **F1-S1 onwards** cuando las stories del shell tocan rutas autenticadas (`(shell-organism)/[agent]/[subtab]`) con data sensible — esa cobertura se documenta en cada spec subsequent.

---

## § 14 — Changelog spec

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Draft inicial `/po-ux` post 3 batches de refinement con Chris. Decisiones ratificadas: Batch 1 (template adaptación infra-only — N/A explícito § 3.2/3.3, § 4.4 Shadcn vendored, § 5 build-time note), Batch 2 (8 scenarios = 6 funcionales + 1 adversarial-declared + 1 bloque N/A; theme-switch inline a Scenario 4), Batch 3 (6 goldens baseline + test pages auxiliares + Playwright `@project=visual` configurado por F1-S0 + ADR-vitalia-002 8 secciones). 3 artifacts protocolo mockup-per-component cementados simultáneamente (ADR-vitalia-003 + rule overlay + learning promotable). |
