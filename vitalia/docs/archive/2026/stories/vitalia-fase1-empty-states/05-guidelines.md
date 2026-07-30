<!-- voseo-allowed: technical guidelines documenting component rules and glosario reference -->
---
story_id: vitalia-fase1-empty-states
brand: vitalia
phase: fase-1
story_type: ui-story
last_modified: 2026-05-26
architect_iter: 1
---

# F1-S10 vitalia-fase1-empty-states — 05-guidelines.md

> Patterns required + forbidden + files in/out of scope + skills enforceable + reference artifacts. Builder MUST consume this before T-1.

---

## § 1 — Patterns required

### § 1.1 — Server-First default (Next.js 16)

- Componentes son **Server Components por defecto**. Solo agregá `"use client"` cuando el componente USA `useState`, `useEffect`, `useRef` o event handlers `onClick`/`onChange`.
- Page route `[agent]/[subtab]/page.tsx` MUST permanecer Server Component (sin state local).
- Dispatcher `SubTabContent` MUST permanecer Server Component (puro mapping).
- Hojas con state local (placeholders especiales con toggle) marcadas `"use client"`.

Referencia: `frontend-expert` skill § Server-First + `https://nextjs.org/docs/app/api-reference/file-conventions/page`.

### § 1.2 — Atomic Design strict

Layers verbatim del Design Contract:

- **Átomos** (`components/ui/`): Button, Tabs, Badge, Card, Input, Textarea. READ-ONLY consume.
- **Moléculas** (`components/shared/shell-organism/` + `features/{agent}/components/{inbox,agenda}/`): 17 NEW.
- **Organismos** (`features/{agent}/components/placeholders/`): 6 especiales + 16 genéricos.
- **Templates / Pages** (`app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx`): 1 MODIFY.

No saltar capa — i.e., page NO consume átomos directo; pasa por organismo `SubTabContent`.

### § 1.3 — LATAM realistic mock data

Spec § 5 mock data verbatim:
- Nombres: María González, Carlos Pérez, Lucía Ramos, Diego Flores, Sofía M., M. Rodríguez, S. López, L. Vega, J. Pérez, A. Ruiz, P. Sosa, M. Díaz, R. Cruz, C. Núñez, Sofía B.
- Doctores: Dr. C. Mendoza, Dra. M. Soto.
- Currency PEN (Perú baseline mock — `S/ 120`, `S/ 36`).
- Phone format Perú masked: `+51 9** ***-4321`.
- Timezone display 24h `America/Lima`.

### § 1.4 — Spanish neutro LatAm verbatim

Copy del spec § 10 ratificado. Pre-commit hook `scripts/git-hooks/pre-commit` Section 4 valida glosario voseo.

Allowed: `tú`, `eres`, `tienes`, `puedes`, `escribir`, `tomar el control`, `devolver`, `próximamente`, `cablea`, `pacientes`, `agenda`.

Prohibited: `vos`, `tenés`, `podés`, `dejá`, `linkeá`, `agregá`, `configurá`, `revisá`, `mirá`.

Magic comment escape NO disponible para placeholders user-facing (solo para docs/audit/test fixtures).

### § 1.5 — `cn()` Tailwind merge mandatory

Toda condicional `className` MUST usar `cn()` de `vitalia/frontend/src/lib/utils.ts`:

```tsx
<div className={cn(
  'flex items-center gap-2',
  isActive && 'bg-primary text-primary-foreground',
  variant === 'human' && 'border-l-green-500'
)}>
```

NUNCA template literal concatenation directa: `className={`flex ${isActive ? 'bg-primary' : ''}`}` (rompe twMerge).

### § 1.6 — Lucide-react icons en componentes React

Componentes React MUST consumir iconos via `lucide-react` package import:

```tsx
import { Building2, Megaphone, MessageCircle, CreditCard, Calendar, Globe, Wrench } from 'lucide-react'
```

EXCEPCIÓN: catálogo `RIBBON_SUBTABS` en `agent-catalog.ts` usa emojis (cementado F1-S7 Q2 — paridad ribbon). Esos emojis se renderizan literal como `<span>{icon}</span>` en `SubTabHeader` (Spec § 4 catálogo SSoT).

### § 1.7 — Zod types para mock data (opcional pero recomendado)

Para mock data complex (inbox conversations, agenda slots), declarar Zod schema top-of-file para validar shape:

```tsx
import { z } from 'zod'

const ConversationItemSchema = z.object({
  id: z.string(),
  patient: z.string(),
  preview: z.string(),
  elapsed: z.string(),
  temp: z.enum(['hot', 'warm', 'cold']),
  channel: z.enum(['WA', 'IG', 'TG']),
  stage: z.enum(['Nuevo', 'Calificando', 'Negociando', 'Cerrando']),
  selected: z.boolean(),
  handler_mode: z.enum(['bot', 'human']),
  campaign: z.string().nullable(),
})
type Conversation = z.infer<typeof ConversationItemSchema>

const INBOX_CONVERSATIONS: Conversation[] = [/* ... */]
```

Vitest unit `inbox-mock-shape.test.ts` valida con `ConversationItemSchema.array().parse(INBOX_CONVERSATIONS)`.

---

## § 2 — Patterns forbidden

### § 2.1 — Anti-patterns universales

- ❌ **Hardcoded hex colors** — usar Tailwind tokens (`bg-green-500`, `text-agent-adrian`). Si necesitás color custom, deriva de design tokens shipped F1-S1.
- ❌ **Lorem ipsum** — usar copy Spanish neutro verbatim del spec § 10.
- ❌ **Voseo** — `tenés/podés/dejá/linkeá/agregá/configurá/mirá/revisá` PROHIBIDOS en strings user-facing.
- ❌ **Default exports** — Next.js pages son excepción (App Router requirement). TODO el resto: named exports.

```tsx
// ❌ PROHIBIDO
export default function EmptyState(...) { ... }

// ✅ CORRECTO
export function EmptyState(...) { ... }
```

- ❌ **`any` type** — usar `unknown` + type guards. Si es indispensable: justify con comment + ESLint disable explícito.
- ❌ **Cross-feature imports prohibido** (anti-duplication): `features/adrian/` NUNCA importa `features/valeria/`. Si necesitás algo compartido, mueve a `components/shared/` o `lib/`.

### § 2.2 — Anti-patterns brand-specific vitalia

- ❌ **Cross-brand imports HARD BAN** — `import from '@/../../nicolify/...'` jamás. Si pattern resiste cross-brand validado F2 → `/pm-luana` lift candidate. Hoy: NO mirror nicolify/comunify/lupulo.
- ❌ **Engine direct edit** — `core/luana-core-*/` READ-ONLY. F1-S10 NO toca engine. Si hipotéticamente surge la necesidad → STOP, escalate `/pm-luana` promotion gate.
- ❌ **Editar mockups HTML como SSoT runtime** — mockups `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/*.html` son baseline visual (gate `shell-mockup-per-component.md`). NO se importan ni se sirven runtime. Builder LEE el mockup para guiar implementación React; NO copia HTML al bundle.
- ❌ **PHI real** — placeholders mock-only. Nombres ficticios, phone/email masked desde origen, NO DNI real. Arch test `test_no_phi_real_data.test.ts` enforce.
- ❌ **Hardcodear sub-tab keys fuera dispatcher** — solo `SubTabContent.tsx` puede literal `'lisa.servicios'`. Otros archivos consume `RIBBON_SUBTABS` runtime o reciben prop. Arch test `test_no_hardcoded_subtab_keys.test.ts` enforce.
- ❌ **Skip mockup visual ratification** — Chris ratificó 7 mockups iter 2 · 2026-05-26. Builder NO cambia visual baseline sin re-ratificación explícita.

### § 2.3 — Anti-patterns React-specific

- ❌ **Stale closures en `useEffect`** — declarar dependencies arrays explícitos. ESLint `react-hooks/exhaustive-deps` enforce.
- ❌ **State derived que debe ser computed** — si `selectedThread = messages.filter(m => m.convId === selectedConvId)`, usar `useMemo`, no `useState`.
- ❌ **Modal edición de item array** — F1-S10 sin modals (placeholder visual). F2 sub-tab stories cablearán modals.
- ❌ **Botón "Guardar" en formularios** — rompe autosave pattern de form-runtime. F1-S10 sin forms; F2-S3/S1 cablearán RHF + autosave.

---

## § 3 — Files in scope (builder MAY edit)

### § 3.1 — NEW component files (43 archivos React + 3 arch tests + 11 specs + 3 POMs)

```
vitalia/frontend/src/components/shared/shell-organism/
├── EmptyState.tsx
├── PlaceholderCard.tsx
├── SubTabHeader.tsx
├── StatusDot.tsx
├── TogglePill.tsx
└── SubTabContent.tsx

vitalia/frontend/src/features/lisa/components/placeholders/
├── MarcaPlaceholder.tsx
├── DoctoresPlaceholder.tsx
├── ServiciosPlaceholder.tsx           ★ especial
└── CompliancePlaceholder.tsx

vitalia/frontend/src/features/lucas/components/placeholders/
├── LanzarPlaceholder.tsx
├── EnvueloPlaceholder.tsx
├── RecursosPlaceholder.tsx
├── ResultadosPlaceholder.tsx
└── MercadoPlaceholder.tsx

vitalia/frontend/src/features/adrian/components/
├── inbox/
│   ├── CampaignTag.tsx
│   ├── ConversationItem.tsx
│   ├── MessageBubble.tsx
│   ├── MessageInput.tsx
│   ├── ContactSidebar.tsx
│   ├── ThreadHeader.tsx
│   └── TakeoverBanner.tsx
└── placeholders/
    ├── InboxPlaceholder.tsx           ★ especial
    ├── EmbudoPlaceholder.tsx          ★ especial
    ├── OutboundPlaceholder.tsx
    └── PropuestasPlaceholder.tsx

vitalia/frontend/src/features/valeria/components/
├── agenda/
│   ├── AgendaToolbar.tsx
│   ├── AgendaFilters.tsx
│   ├── AgendaDayHeader.tsx
│   ├── AgendaSlot.tsx
│   └── AgendaSummaryFooter.tsx
└── placeholders/
    ├── AgendaPlaceholder.tsx          ★ especial
    └── PacientesPlaceholder.tsx

vitalia/frontend/src/features/camila/components/placeholders/
├── VozPlaceholder.tsx                 ★ especial
├── ReactivarPlaceholder.tsx
├── MultiplicarPlaceholder.tsx
└── ReputacionPlaceholder.tsx

vitalia/frontend/src/features/config/components/placeholders/
├── CuentaPlaceholder.tsx
├── ConexionesPlaceholder.tsx          ★ especial
└── AvanzadoPlaceholder.tsx

vitalia/frontend/src/__tests__/architecture/
├── test_subtab_content_uses_ribbon_subtabs_ssot.test.ts
├── test_no_hardcoded_subtab_keys.test.ts
└── test_no_phi_real_data.test.ts

vitalia/frontend/e2e/pages/
├── ShellOrganismPage.ts
├── AdrianInboxPage.ts
└── ValeriaAgendaPage.ts

vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/
├── sc-01-navegacion-22-subtabs.spec.ts
├── sc-02-lisa-servicios.spec.ts
├── sc-03-adrian-embudo.spec.ts
├── sc-04-valeria-agenda.spec.ts
├── sc-04bis-adrian-inbox.spec.ts
├── sc-05-subtab-invalido.spec.ts
├── sc-06-edge-no-shell-remount.spec.ts
├── sc-07-adversarial-xss.spec.ts
├── sc-08-empty-states-genericos.spec.ts
├── sc-09-a11y.spec.ts
└── sc-10-i18n.spec.ts

vitalia/frontend/e2e/__screenshots__/visual/empty-states/
└── (generated automatic on first run; ~70 PNG goldens)
```

### § 3.2 — MODIFY (1 archivo)

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx
```

Reemplazar placeholder body "TBD F1-S10" (F1-S9 cementó) por:

```tsx
import { SubTabContent } from '@/components/shared/shell-organism/SubTabContent'
import type { RibbonTabSlug } from '@/lib/agent-catalog'

interface Props {
  params: Promise<{ tenantId: string; agent: string; subtab: string }>
}

export default async function SubTabPage({ params }: Props) {
  const { agent, subtab } = await params
  // F1-S9 layout ya validó isValidAgent(agent) + isValidSubtab(agent, subtab) — si llegó acá, válidos.
  return <SubTabContent agent={agent as RibbonTabSlug} subtab={subtab} />
}
```

### § 3.3 — Post-merge updates (PM consume — NO builder)

`/pm-vitalia` ejecuta al cierre Fase F MERGE:

- `vitalia/docs/product/capabilities/shell-organism/empty-states.yaml` (NEW capability YAML)
- `vitalia/docs/product/modules/shell-organism.md` (auto-list block actualizado via `scripts/reconcile_capabilities.py --brand vitalia`)
- `vitalia/docs/portfolio/vitalia.md` (regenera automático)
- Story directory → `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/` (R2 brand-docs-schema)

---

## § 4 — Files NEVER touch (HARD BAN)

### § 4.1 — Engine core (read-only)

```
core/luana-core-*/src/**/*       ← READ-ONLY. Lift via /pm-luana promotion gate.
```

### § 4.2 — Other brands (cross-brand mirror prohibido)

```
nicolify/**/*       ← HARD BAN
comunify/**/*       ← HARD BAN
lupulo/**/*         ← HARD BAN
saasora/**/*        ← HARD BAN
inmoflow/**/*       ← HARD BAN
retailly/**/*       ← HARD BAN
fixia/**/*          ← HARD BAN
guestly/**/*        ← HARD BAN
fitflow/**/*        ← HARD BAN
```

### § 4.3 — SSoT consumed (READ-ONLY)

```
vitalia/frontend/src/lib/agent-catalog.ts           ← READ-ONLY (RIBBON_SUBTABS SSoT)
vitalia/frontend/src/lib/utils.ts                   ← READ-ONLY (cn(), formatTenantDate*, etc.)
vitalia/frontend/src/components/ui/                 ← READ-ONLY (Shadcn primitives)
vitalia/frontend/src/components/shared/shell-organism/*Bar.tsx  ← READ-ONLY (F1-S7/S8 shipped)
vitalia/frontend/src/components/shared/shell-organism/Valeria*.tsx ← READ-ONLY (F1-S5/S6 shipped)
vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx  ← READ-ONLY (F1-S2 shipped)
vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md  ← READ-ONLY (atomic SSoT)
```

### § 4.4 — Story mockups (visual baseline, no edit)

```
vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/*.html
```

Ratificados Chris iter 2 · 2026-05-26. Re-ratification gate si builder propone modificar.

### § 4.5 — Cement-date rules + skill artifacts (meta)

```
.claude/rules/**/*       ← meta-paradigm
.claude/skills/**/*       ← meta-paradigm
docs/process/**/*         ← cross-brand process docs
docs/architecture/**/*    ← cross-brand ADRs
vitalia/.claude/rules/**/*  ← brand-specific rules (NO edit Fase 1)
```

---

## § 5 — Must-load skills (enforceable per ticket)

Builder MUST load these skills antes de tocar paths bajo su jurisdicción:

| Surface tocada | Skills obligatorias | Stub rule |
|---|---|---|
| Cualquier `*.tsx` Vitalia FE | `frontend-expert` | `.claude/rules/frontend-fsd.md` |
| `components/shared/shell-organism/*.tsx` (moléculas + organismos) | `frontend-expert` + `tessl__react-patterns` + `tessl__shadcn-ui` + `tessl__tailwind` | `frontend-fsd.md` |
| `features/{agent}/components/*.tsx` | `frontend-expert` + `tessl__react-patterns` | `frontend-fsd.md` |
| Page route `[agent]/[subtab]/page.tsx` MODIFY | `frontend-expert` + `tessl__nextjs-app-router-modularization` | `frontend-fsd.md` |
| Vitest unit `.test.tsx` | `frontend-expert` + `tessl__vitest` | `tdd-mandatory.md` |
| Playwright `.spec.ts` + POMs | `playwright-expert` (SSoT — Clerk auth + POMs + fixtures + anti-patterns) | `e2e-testing.md` |
| Arch tests `__tests__/architecture/*.test.ts` | `frontend-expert` + `tessl__vitest` | `architectural-fitness.md` |
| Visual goldens generation | `playwright-expert` | `e2e-testing.md` |

`frontend-expert` skill carga automático ante triggers: `tsx`, `react`, `next`, `fsd`, `tailwind`, `vitest`. Builder DEBE invocar via Skill tool inline.

`playwright-expert` skill carga automático ante triggers: `playwright`, `e2e`, `smoke`, `pom`. Builder DEBE invocar antes T-10 (Playwright suite).

---

## § 6 — Reference artifacts (re-read mid-build)

Builder re-leer si pierde context mid-build:

| Artifact | Path | Cuándo |
|---|---|---|
| Spec ratificado v2 | `vitalia/docs/product/stories/vitalia-fase1-empty-states/01-spec.md` | T-5/T-6 (inbox parity) + T-7 (agenda enriquecida) — verificar mock data verbatim + copy verbatim |
| Mockup empty-states-grid | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/empty-states-grid.html` | T-2 (16 genéricos) — copia visual y verbiage de cada EmptyState |
| Mockup lisa-servicios | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/lisa-servicios-placeholder.html` | T-3 |
| Mockup adrian-embudo | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-embudo-placeholder.html` | T-4 |
| Mockup adrian-inbox | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-inbox-placeholder.html` | T-5 + T-6 |
| Mockup camila-voz | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html` | T-8 |
| Mockup valeria-agenda | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/valeria-agenda-placeholder.html` | T-7 |
| Mockup config-conexiones | `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/config-conexiones-placeholder.html` | T-2 (config sub-portion) |
| Architecture FE | `vitalia/docs/product/stories/vitalia-fase1-empty-states/03-arch.md` | siempre primero |
| Predecessor F1-S9 arch FE | `vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/03-arch-fe.md` | si dudas en page route pattern |
| Predecessor F1-S8 catalog | `vitalia/docs/archive/2026/stories/vitalia-fase1-sub-tabs-line2/03-arch.md` | si dudas en `RIBBON_SUBTABS` shape |
| Sales_studio inbox shipped (reference conceptual) | `ap_sales_agent/frontend/src/features/closer-studio/components/inbox/` | T-5 — pattern reference (NO import cross-brand) |

---

## § 7 — Native-First commands cheat sheet

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Type check
npx tsc --noEmit

# Lint
npx eslint src/ --cache

# Format
npx prettier --check src/components/shared/shell-organism/ src/features/

# Vitest unit (+ coverage)
npx vitest run --coverage
npx vitest run src/components/shared/shell-organism/SubTabContent.test.tsx  # focused

# Arch tests
npx vitest run src/__tests__/architecture/

# Playwright E2E (preflight obligatorio primero)
cd ${WS} && bash scripts/e2e-preflight.sh
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-empty-states/

# Visual goldens update (cuando intencional)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-empty-states/ --update-snapshots
```

**NUNCA** `make e2e*` (Docker OOM). **NUNCA** `docker exec ruff/pytest/tsc/vitest` (regla native-first).

