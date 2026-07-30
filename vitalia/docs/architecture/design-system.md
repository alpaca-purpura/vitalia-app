---
brand: vitalia
type: design-system
status: draft
last_updated: 2026-05-17
ssot_owner: /pm-vitalia
consumers: [vitalia/frontend, vitalia/promo-site]
supersedes: brandbook-raw (Chris brief 2026-05-17)
---

# Vitalia — Design System (frontend SSoT)

> Resumen accionable del brandbook. **Esta es la única fuente de tokens visuales para Vitalia FE.** Si algo no está acá, no es Vitalia. Cambios → ADR.

**Esencia:** "Tu agencia de marketing y ventas para salud y belleza, con un equipo de agentes IA que trabajan como personas." Mezcla profesionalismo médico (sobriedad, trust, compliance HIPAA-lite) + cuidado cálido (tratamos al cliente como ellos tratan a su paciente) + diferenciación agéntic (5 worker avatars con personalidad).

**Vertical:** clínicas LatAm que se promocionan — dental, psicología, psiquiatría, estética, fertilidad. Excluye urgencias y medicina general (donde no se necesita marketing).

## 0. Promo vs App — diferenciación obligatoria

Mismos tokens, distinto uso. Sin excepción.

| | Web promo (`vitalialat.com`) | App interna (`dev-app.vitalialat.com`) |
|---|---|---|
| Audiencia | Clínicas que aún no compraron | Doctor + recepción + admin de clínica cliente |
| Job-to-be-done | Convencer + capturar lead | Operar día a día clínica |
| Gradient mariposa | Sí — hero, logos grandes, secciones marketing | Solo loading/empty/onboarding splash (one-time) |
| Agentes (Valeria, Adrián, Lucas, Camila, Mateo) | Páginas dedicadas `/equipo/{nombre}` con headline "Hola, soy X" + CTA "Contratá al equipo" | Atribución funcional ("Adrián cerró tu turno"), avatar pequeño con iniciales, sin páginas dedicadas |
| Avatares con foto IA-generated | Sí (cuando se produzcan) | No — solo iniciales con gradient |
| Videos / animaciones agentes | Sí | No — eye-candy sin valor operativo |
| Densidad info | Baja (storytelling) | Alta (operación) |
| Tipografía Display | clamp grande (hero) | Solo H1 de página |

Mezclar ambas en la app desenfoca al usuario operativo (decisión arquitectónica, no estética).

## 1. Color tokens

### Fuente de verdad (HEX + HSL channels)

HSL en formato `H S% L%` (Tailwind v4 / Shadcn pattern — consumido vía `hsl(var(--x))`).

#### Brand core (4 colores oficiales del brandbook 2026-05-17)

| Slot | Uso | HEX | HSL |
|---|---|---|---|
| `--vitalia-cian` | Color hero, links, primary CTA secundario, info, badges depósito | `#01B2F8` | `198 99% 49%` |
| `--vitalia-purpura` | Acento secundario, hover, agent gradient stop, decorative | `#7B2D91` | `287 53% 37%` |
| `--vitalia-amarillo` | Highlight, badge premium plan, warning soft, CTA promo | `#FEE209` | `53 99% 51%` |
| `--vitalia-azul-marino` | Texto cuerpo + títulos, primary button, app shell logo, dark surfaces | `#180D95` | `244 84% 32%` |

#### Acento secundario (5to color presente en isotipo)

| Slot | Uso | HEX | HSL |
|---|---|---|---|
| `--vitalia-verde-lima` | Acento natural, success soft, agent Lucas avatar, success indicators secundarios | `#B8DC2A` | `70 73% 51%` |

> **Origen:** capa translúcida visible en el isotipo mariposa (pétalos secundarios). No estaba en el brandbook raw pero existe en el logo — la formalizamos como 5to token para coherencia con el activo gráfico ya impreso. Si Chris decide eliminarlo, removerlo aquí y del isotipo en mismo PR.

#### Neutrales (app shell)

| Slot | Uso | HEX | HSL |
|---|---|---|---|
| `--vitalia-bg` | Fondo principal app | `#F7F9FC` | `220 28% 98%` |
| `--vitalia-surface` | Cards, modals, sidebar background | `#FFFFFF` | `0 0% 100%` |
| `--vitalia-surface-alt` | Fondo sutil para diferenciar zones (calendar slot empty) | `#FAFBFE` | `220 38% 98%` |
| `--vitalia-muted` | Background de chips, tool calls, empty states | `#F1F4FA` | `220 33% 96%` |
| `--vitalia-text` | Texto cuerpo principal | `#1A1F36` | `226 36% 16%` |
| `--vitalia-text-muted` | Texto secundario, metadata, captions | `#6B7280` | `220 9% 46%` |
| `--vitalia-text-faint` | Texto disabled, hints | `#9CA3AF` | `220 9% 65%` |
| `--vitalia-border` | Bordes default | `#E8EAF0` | `222 18% 93%` |
| `--vitalia-border-soft` | Bordes muy sutiles (grid separators) | `#F0F2F8` | `220 25% 96%` |

#### Semantic (status médico)

| Slot | Uso | HEX | HSL |
|---|---|---|---|
| `--vitalia-success` | Pago confirmado, status verde, paciente al día | `#16A34A` | `142 76% 36%` |
| `--vitalia-warning` | Pago pendiente, atención requerida | `#D97706` | `33 91% 44%` |
| `--vitalia-danger` | Error, cancelado, acción destructiva | `#DC2626` | `0 73% 50%` |
| `--vitalia-info` | Info neutra (= cian con menos saturación) | `#0EA5E9` | `199 89% 48%` |

### Gradient mariposa (logo + hero promo only)

```css
--vitalia-gradient-mariposa: linear-gradient(135deg, #01B2F8 0%, #7B2D91 50%, #B8DC2A 100%);
--vitalia-gradient-agent:    linear-gradient(135deg, #01B2F8 0%, #7B2D91 100%);
--vitalia-gradient-app-cta:  linear-gradient(135deg, #01B2F8 0%, #180D95 100%);
```

**Uso permitido gradient mariposa:**
- Logo + isotipo (siempre)
- Hero web promo (`vitalialat.com`)
- Empty state "Bienvenido a Vitalia" (one-time per session)
- Loading screen splash

**Prohibido gradient mariposa:**
- Background app extenso (cansa la vista, contradice sobriedad médica)
- Buttons primary estándar (usar `bg-vitalia-azul-marino` sólido)
- Cards genéricas
- Texto sobre gradient sin overlay claro

**Uso gradient-agent (agent avatars circulares):**
- Valeria, Adrián, Lucas, Camila, Mateo — fondo circular del avatar con iniciales
- Decorative elements relacionados a "equipo IA trabajando"

### Combinaciones aprobadas

| Contexto | Tokens |
|---|---|
| App shell | `bg` + `text` + `border` + `cian` (links/acciones secundarias) + `azul-marino` (CTAs primary) |
| Hero promo | gradient mariposa + white + amarillo CTA |
| Dashboard agenda | `bg` + `cian` (badge depósito) + `success` (pagado) + `warning` (pendiente) |
| Patient PHI section | `surface` + `border` + `text` + `cian` (highlights informativos) — sin gradient |
| Agent attribution | `gradient-agent` (avatar circular) + `azul-marino` (nombre del agente) |
| Activity feed | `surface` + `text` + agent avatars con sus gradients |
| Calendar slot booked-paid | `success` border-left + verde wash 8% |
| Calendar slot booked-deposit | `cian` border-left + cian wash 10% |
| Calendar slot booked-pending | `warning` border-left + warning wash 8% |

## 2. Typography

### Stack final (3 fuentes — propuesta a confirmar)

| Rol | Familia (propuesta) | Peso | Uso |
|---|---|---|---|
| Display/H1 | **General Sans** (Indian Type Foundry, open-source, sans futurista con A sin barra) | `700` | Hero web promo, page titles de app |
| Headings | **Manrope** (Google Fonts) | `600` SemiBold | H2–H4, section titles, button labels |
| Body | **Inter** (Google Fonts) | `400` / `500` | Body, forms, tables, tooltips |

**Fallbacks:** `ui-sans-serif, system-ui, -apple-system, sans-serif`

**Alternativas válidas para Display** (si Chris quiere cambiar):
- **Cabinet Grotesk** (Indian Type Foundry) — A con barra pero geometría futurista similar
- **Eudoxus Sans** (open-source, A neutra)
- **Neue Haas Grotesk Display** (comercial — requiere licencia)

Decisión final → ADR-vitalia-001-typography si difiere de General Sans.

### Carga en Next.js (App Router)

General Sans requiere self-host (`next/font/local`). Manrope + Inter via `next/font/google`.

Ejemplo `vitalia/frontend/src/app/layout.tsx`:

```ts
import localFont from "next/font/local";
import { Manrope, Inter } from "next/font/google";

const generalSans = localFont({
  src: [
    { path: "../assets/fonts/GeneralSans-Bold.woff2", weight: "700", style: "normal" },
    { path: "../assets/fonts/GeneralSans-Semibold.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-general-sans",
  display: "swap",
});
const manrope = Manrope({
  subsets: ["latin"],
  weight: ["500","600","700"],
  variable: "--font-manrope",
  display: "swap"
});
const inter = Inter({
  subsets: ["latin"],
  weight: ["400","500","600"],
  variable: "--font-inter",
  display: "swap"
});
```

Aplicar `${generalSans.variable} ${manrope.variable} ${inter.variable}` al `<html>`.

### Escala (clamp responsive)

| Token | Min → Max | line-height | Uso |
|---|---|---|---|
| `text-display` | `clamp(2.5rem, 6vw, 4.5rem)` | `1.05` | Hero promo |
| `text-h1` | `clamp(1.75rem, 4vw, 2.5rem)` | `1.15` | Page title app |
| `text-h2` | `1.5rem` | `1.2` | Section title |
| `text-h3` | `1.25rem` | `1.3` | Sub-section |
| `text-body` | `0.875rem` (14px) | `1.5` | UI body (más denso que comunify por contexto operación médica) |
| `text-small` | `0.75rem` (12px) | `1.4` | Metadata, captions |
| `text-mono-xs` | `0.625rem` (10px) | `1.3` | Tool call labels, audio timer, technical |

## 3. Shape & spacing

```css
--radius:        8px;     /* botones, inputs, cards estándar */
--radius-lg:     14px;    /* cards grandes, modals */
--radius-bubble: 18px;    /* chat message bubbles */
--radius-pill:   999px;   /* badges, chips */
```

Sombras:
- `shadow-sm` para cards estándar
- `shadow-md` para chat panel persistente, popovers
- `shadow-lg` con tint `rgba(24,13,149,0.12)` para CTAs primary en hover

Spacing scale: Tailwind default (4px base).

## 4. CSS variables — drop-in `globals.css`

Pegar en `vitalia/frontend/src/app/globals.css` (crear si no existe) o `:root` del layout root.

```css
:root {
  /* Brand core */
  --vitalia-cian:        198 99% 49%;
  --vitalia-purpura:     287 53% 37%;
  --vitalia-amarillo:    53 99% 51%;
  --vitalia-azul-marino: 244 84% 32%;
  --vitalia-verde-lima:  70 73% 51%;

  /* Neutral */
  --vitalia-bg:           220 28% 98%;
  --vitalia-surface:      0 0% 100%;
  --vitalia-surface-alt:  220 38% 98%;
  --vitalia-muted:        220 33% 96%;
  --vitalia-text:         226 36% 16%;
  --vitalia-text-muted:   220 9% 46%;
  --vitalia-text-faint:   220 9% 65%;
  --vitalia-border:       222 18% 93%;
  --vitalia-border-soft:  220 25% 96%;

  /* Semantic */
  --vitalia-success:  142 76% 36%;
  --vitalia-warning:  33 91% 44%;
  --vitalia-danger:   0 73% 50%;
  --vitalia-info:     199 89% 48%;

  /* Shape */
  --radius:        0.5rem;     /* 8px */
  --radius-lg:     0.875rem;   /* 14px */
  --radius-bubble: 1.125rem;   /* 18px */

  /* Gradients (literal, no HSL) */
  --vitalia-gradient-mariposa: linear-gradient(135deg, #01B2F8 0%, #7B2D91 50%, #B8DC2A 100%);
  --vitalia-gradient-agent:    linear-gradient(135deg, #01B2F8 0%, #7B2D91 100%);
  --vitalia-gradient-app-cta:  linear-gradient(135deg, #01B2F8 0%, #180D95 100%);
}
```

**Dark mode:** out of scope MVP. Cuando se aborde → ADR-vitalia-002 con tokens `--vitalia-bg-dark` etc.

## 5. Tailwind config — extender slots

Editar `vitalia/frontend/tailwind.config.ts`:

```ts
colors: {
  "vitalia-cian":          "hsl(var(--vitalia-cian))",
  "vitalia-purpura":       "hsl(var(--vitalia-purpura))",
  "vitalia-amarillo":      "hsl(var(--vitalia-amarillo))",
  "vitalia-azul-marino":   "hsl(var(--vitalia-azul-marino))",
  "vitalia-verde-lima":    "hsl(var(--vitalia-verde-lima))",
  "vitalia-bg":            "hsl(var(--vitalia-bg))",
  "vitalia-surface":       "hsl(var(--vitalia-surface))",
  "vitalia-surface-alt":   "hsl(var(--vitalia-surface-alt))",
  "vitalia-muted":         "hsl(var(--vitalia-muted))",
  "vitalia-text":          "hsl(var(--vitalia-text))",
  "vitalia-text-muted":    "hsl(var(--vitalia-text-muted))",
  "vitalia-text-faint":    "hsl(var(--vitalia-text-faint))",
  "vitalia-border":        "hsl(var(--vitalia-border))",
  "vitalia-border-soft":   "hsl(var(--vitalia-border-soft))",
  "vitalia-success":       "hsl(var(--vitalia-success))",
  "vitalia-warning":       "hsl(var(--vitalia-warning))",
  "vitalia-danger":        "hsl(var(--vitalia-danger))",
  "vitalia-info":          "hsl(var(--vitalia-info))",
},
backgroundImage: {
  "vitalia-gradient-mariposa": "var(--vitalia-gradient-mariposa)",
  "vitalia-gradient-agent":    "var(--vitalia-gradient-agent)",
  "vitalia-gradient-app-cta":  "var(--vitalia-gradient-app-cta)",
},
fontFamily: {
  display: ["var(--font-general-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
  heading: ["var(--font-manrope)", "ui-sans-serif", "system-ui", "sans-serif"],
  body:    ["var(--font-inter)",   "ui-sans-serif", "system-ui", "sans-serif"],
},
borderRadius: {
  DEFAULT: "var(--radius)",
  lg:      "var(--radius-lg)",
  bubble:  "var(--radius-bubble)",
},
```

## 6. Component recipes

### Botón primary (sólido, no gradient)

```tsx
className="bg-vitalia-azul-marino text-white font-heading font-semibold
           px-5 py-2.5 rounded-[var(--radius)] transition
           hover:bg-vitalia-purpura hover:shadow-md"
```

### Botón secundario (outline cian)

```tsx
className="border border-vitalia-cian text-vitalia-azul-marino font-heading font-semibold
           px-5 py-2.5 rounded-[var(--radius)] hover:bg-vitalia-cian/5"
```

### Botón destructive

```tsx
className="bg-vitalia-danger text-white font-heading font-semibold
           px-5 py-2.5 rounded-[var(--radius)] hover:brightness-95"
```

### Card estándar

```tsx
className="bg-vitalia-surface border border-vitalia-border rounded-lg p-5
           shadow-sm hover:shadow-md transition"
```

### Badge status pago

```tsx
// Pagado completo
<span className="text-[10px] font-bold tracking-wide uppercase
                 bg-vitalia-success/12 text-vitalia-success px-2 py-0.5 rounded">PAGADO</span>

// Depósito 30%
<span className="text-[10px] font-bold tracking-wide uppercase
                 bg-vitalia-cian/12 text-vitalia-cian px-2 py-0.5 rounded">30%</span>

// Pendiente
<span className="text-[10px] font-bold tracking-wide uppercase
                 bg-vitalia-warning/12 text-vitalia-warning px-2 py-0.5 rounded">SIN PAGO</span>
```

### Agent avatar (iniciales con gradient)

```tsx
// Valeria — gradient cian→púrpura
<div className="w-7 h-7 rounded-full bg-vitalia-gradient-agent
                text-white text-[11px] font-bold
                flex items-center justify-center">V</div>

// Adrián — gradient púrpura→azul-marino
<div className="w-7 h-7 rounded-full
                bg-[linear-gradient(135deg,_#7B2D91_0%,_#180D95_100%)]
                text-white text-[11px] font-bold
                flex items-center justify-center">A</div>

// Lucas — gradient verde-lima→cian (cuando portado)
<div className="w-7 h-7 rounded-full
                bg-[linear-gradient(135deg,_#B8DC2A_0%,_#01B2F8_100%)]
                text-white text-[11px] font-bold
                flex items-center justify-center">L</div>
```

### Stat card

```tsx
<div className="bg-vitalia-surface border border-vitalia-border rounded-lg p-4 shadow-sm">
  <div className="text-[11.5px] font-semibold uppercase tracking-wide text-vitalia-text-muted mb-1.5">
    Turnos hoy
  </div>
  <div className="text-2xl font-bold text-vitalia-azul-marino tracking-tight">4</div>
  <div className="text-[11.5px] text-vitalia-success mt-1">+1 vs ayer</div>
</div>
```

### Sidebar nav item

```tsx
// Inactive
<div className="flex items-center gap-2.5 px-3 py-2 rounded-[var(--radius)]
                text-sm text-vitalia-text-muted cursor-pointer
                hover:bg-vitalia-bg hover:text-vitalia-text">
  <Icon className="w-4 h-4" />Agenda
</div>

// Active
<div className="flex items-center gap-2.5 px-3 py-2 rounded-[var(--radius)]
                text-sm font-semibold text-vitalia-azul-marino
                bg-gradient-to-r from-vitalia-cian/10 to-transparent
                border-l-[3px] border-vitalia-cian pl-[9px]">
  <Icon className="w-4 h-4" />Agenda
</div>
```

### Calendar slot booked-deposit

```tsx
<div className="bg-gradient-to-br from-vitalia-cian/10 to-vitalia-cian/[0.02]
                border-l-[3px] border-vitalia-cian
                px-2 py-1.5 text-xs cursor-pointer hover:bg-vitalia-surface-alt">
  <strong className="block font-semibold text-vitalia-text text-xs">M. Rodríguez</strong>
  <span className="text-[10px] text-vitalia-text-muted">Consulta · ✓ depósito</span>
</div>
```

### Activity feed item con atribución agéntic

```tsx
<div className="flex gap-2.5 py-2.5 border-b border-vitalia-border-soft items-start">
  <AgentAvatar agent="adrian" size="sm" />
  <div className="flex-1 text-[12.5px]">
    <span className="font-semibold text-vitalia-azul-marino">Adrián</span> cerró el turno de las{" "}
    <strong>10:30 (M. Rodríguez)</strong> por WhatsApp · depósito 30% confirmado.
    <div className="text-[11px] text-vitalia-text-faint mt-0.5">hace 14 minutos</div>
  </div>
</div>
```

### Componentes heredados de Nicolify (fork directo)

Estos componentes se forkean de `nicolify/frontend/src/features/copilot/` y se adaptan a tokens vitalia (reemplazar `purple-600` → `vitalia-azul-marino`, `slate-100` → `vitalia-muted`, etc.):

- `UserMessage` / `UserMessageV2` — bubble derecha azul-marino, `rounded-bubble rounded-br-md`
- `AssistantMessage` / `AssistantMessageV2` — bubble izquierda muted con avatar gradient-agent
- `TypingIndicator` — 3 dots bounce 900ms delays 0/180/360ms
- `ToolCallChip` — pill con spinner + label + progress bar + stage text (estados running/done)
- `AudioBlock` — player con play button azul-marino + scrubber gradient cian→púrpura + speed + transcript collapsible
- `VoiceOverlay` — replaces composer durante grabación, 40 barras animadas + timer + cancel rojo + accept verde
- `ChatComposer` — attachment + voice + textarea autosize + send (azul-marino) + context chips

Referencia visual completa: `/tmp/vitalia-mockups.html` tab D.4 (mockup exploratorio, no diseño final ratificado).

### Autoguardado — indicador flotante (ESTÁNDAR · ratificado Chris 2026-06-07)

Todo bloque funcional con autoguardado usa el **único** componente compartido
`src/components/shared/FloatingAutosaveIndicator.tsx` — NO un hint inline ni un badge
por-sección en el header. Es un pill **flotante anclado bottom-center** del panel de
contenido (`sticky bottom-4`), **siempre visible** (incluso en idle muestra "Los cambios
se guardan automáticamente"), que sigue visible al hacer scroll.

- Se renderiza como **último hijo** del contenedor scrolleable de la vista
  (`<div className="flex flex-col gap-6 p-6"> … <FloatingAutosaveIndicator status savedAt/> </div>`).
- Estados: `idle | dirty | saving | saved | error` (perfil omite `dirty`). `saved` muestra
  tiempo relativo si se pasa `savedAt`.
- Reemplaza al viejo `AutosaveBadge` de header. Consumidores actuales: Perfil de doctor +
  marca (Identidad · Voz y tono · Presencia). Toda vista nueva con autosave DEBE usarlo.
- Anti-pattern: hint de autoguardado inline propio, badge en el header, o no mostrar estado.

## 7. Agentes en la UI

Vitalia tiene 5 worker agents IA con nombres + roles. **Las páginas dedicadas a cada agente viven en la web promo (`vitalialat.com/equipo/{nombre}`).** En el app interna los agentes aparecen como atribución funcional, NO como producto separado.

### Roster

| Agente | Rol técnico | Avatar gradient | Cuándo aparece en UI app | Estado backend MVP |
|---|---|---|---|---|
| **Valeria** | Copilot conversacional (hub) | cian → púrpura | Chat panel persistente o central, depende patrón ratificado | Backend scaffold — tools T-tools-1..4 pending |
| **Adrián** | Sales agent (closer) | púrpura → azul-marino | Inbox conversaciones badge "Adrián respondió" + activity feed "Adrián cerró turno X" | Backend scaffold |
| **Lucas** | Growth studio (setter) | verde-lima → cian | Activity feed "Lucas calificó 5 leads" + futuro surface "Crecimiento" | Backend defer — depende port `nicolify/advertising` |
| **Camila** | Diseñadora (flyers) | amarillo → púrpura | NO MVP — defer | No existe backend |
| **Mateo** | Developer (landings) | azul-marino → cian | NO MVP — defer | Backend `luana-core-landing` solo scaffold vitalia |

### Atribución pattern (cómo se nombran en UI)

- En notificaciones: `"Adrián cerró tu turno de las 10:30"` (no "Sales agent closed booking #X")
- En activity feed: agent avatar + nombre + acción verbo simple en pasado
- En badges en mensajes inbox: pill pequeña "Adrián respondió" (gradient avatar + nombre)
- En tooltips de avatares: `"Adrián — Closer del equipo"`
- En código backend: mantener nombres técnicos (`sales_agent`, `copilot`)
- Mapping FE: crear `vitalia/frontend/src/lib/agent-names.ts` con `agentNameByRole: Record<string,string>`

### Componente reutilizable

```tsx
<AgentAttribution
  agent="adrian"          // 'valeria' | 'adrian' | 'lucas' | 'camila' | 'mateo' | 'sistema'
  action="cerró"
  target="el turno de las 10:30 (M. Rodríguez)"
  via="WhatsApp"          // optional
  timestamp={...}
/>
```

### Anti-patterns (NO hacer en app)

- ❌ Crear página `/equipo/{nombre}` en app — vive en promo
- ❌ Headline "Hola, soy Adrián" dentro del app — eso es marketing
- ❌ Botón "Contratá a Adrián" — el agente ya está incluido en el plan
- ❌ Avatar IA-generated con foto custom — usar iniciales con gradient en MVP
- ❌ Animación introducción agente — eye-candy sin valor operativo
- ❌ Mostrar el rol técnico (`sales_agent`) — siempre el nombre del agente

## 8. PHI surface conventions

Heredado de `vitalia/.claude/rules/hipaa-lite.md`. La UI debe respaldar las salvaguardas defensivas.

### Masking

| Campo | Masked display | Full display |
|---|---|---|
| DNI / Documento | `12***5678` (2 primeros + 4 últimos) | Solo con role check `doctor` o `admin_clinic` + audit log row |
| Teléfono | `+54 11 ***-4567` | Idem |
| Email | `j***@gmail.com` (1ra letra + dominio) | Idem |
| Nombre completo | Permitido en listas (no PII directo per regulaciones LatAm) | — |
| Diagnóstico | **Nunca en listas/tooltips** | Solo en página dedicada con role check + audit |
| Notas médicas | **Nunca en hover/preview** | Idem |
| Plan de tratamiento | **Nunca en listas** | Idem |

### Componentes especiales

```tsx
// Masking automático según role del user actual
<PiiMaskedSpan field="dni" value={patient.dni} />

// Section solo visible para roles autorizados
<RequireRole roles={["doctor", "nurse", "admin_clinic"]}>
  <DiagnosisSection ... />
</RequireRole>

// Section que registra audit log row al renderizar
<AuditedSection action="view_diagnosis" patientId={patient.id}>
  <DiagnosisDetail ... />
</AuditedSection>
```

### Indicadores visuales

- Badge "PHI" pequeño (`bg-vitalia-warning/12 text-vitalia-warning`) en cualquier section que contenga datos médicos sensibles
- Icono 🔒 en headers de patient detail
- Tooltip "Este acceso queda registrado" antes de revelar diagnóstico

### Anti-patterns

- ❌ PHI en `localStorage` / `sessionStorage` (solo IDs hash)
- ❌ PHI en URL query params (`?dni=12345678`)
- ❌ PHI en tooltips/hover/preview de listas
- ❌ Mostrar diagnóstico en lista de pacientes (solo en detalle audited)
- ❌ Foto del paciente en sidebar/lista (defer — privacidad)

## 9. Brand voice médica (UI strings)

Heredado de `vitalia/config/brand.yaml::guardrails`.

### Disclaimers requeridos

- En cualquier output con info clínica: `"Información de referencia. Consultá con tu doctor."`
- En cualquier flujo de booking con consentimiento: `"Al continuar, aceptás los términos de tratamiento y la política de privacidad médica."`
- En footer del app: `"Vitalia es una plataforma de gestión y marketing. No reemplaza la consulta médica."`

### Tono

| Sí | No |
|---|---|
| "Te acompañamos en tu tratamiento" | "Somos tu solución médica" |
| "Tu próximo turno es..." | "Su próxima cita médica es..." (Ud. formal — pan-LATAM usa tuteo) |
| "Andrés está al día con su tratamiento" | "El paciente Andrés tiene adherencia 100%" (jergon técnico) |
| "Reservar turno" | "Agendar cita" (regionalismo) |

### Anti-patterns

- ❌ Diagnóstico generado por IA visible (guardrail backend bloquea, pero UI tampoco debe sugerirlo)
- ❌ Prescripción (mismo)
- ❌ Resultados médicos por canal no encriptado (siempre derivar a portal seguro)
- ❌ Términos médicos sin glosario (UI para clínica, no para paciente — pero leer comprensible)

## 10. Spanish neutro LatAm

Aplicar `.claude/rules/spanish-text.md`. **Tuteo neutro pan-LATAM. NO voseo (Vitalia opera MX/CO/PE/CL/AR/BR-ES).**

Excepción: output de `sales_agent` puede respetar voz local del tenant (si tenant AR configura voseo en personality_profile, mensajes al paciente OK con voseo — esto NO aplica a UI chrome del app).

## 11. Implementation handoff

| Paso | Path | Owner | Esfuerzo |
|---|---|---|---|
| 1. Crear `globals.css` con `:root` vars | `vitalia/frontend/src/app/globals.css` | builder-frontend | XS |
| 2. Importar `globals.css` en `layout.tsx` | `vitalia/frontend/src/app/layout.tsx` | builder-frontend | XS |
| 3. Cargar General Sans (local) + Manrope/Inter (Google) | `layout.tsx` + `assets/fonts/` | builder-frontend | S |
| 4. Extender `tailwind.config.ts` (sección §5) | `vitalia/frontend/tailwind.config.ts` | builder-frontend | S |
| 5. Crear `<AgentAvatar>` + `<AgentAttribution>` components | `vitalia/frontend/src/components/shared/agents/` | builder-frontend | M |
| 6. Crear `<PiiMaskedSpan>` + `<RequireRole>` + `<AuditedSection>` | `vitalia/frontend/src/components/shared/phi/` | builder-frontend | M |
| 7. Fork componentes Copilot Nicolify | `vitalia/frontend/src/features/copilot/` | builder-frontend | L (~3-4d) |
| 8. Arch fitness test: prohibir HEX literales en componentes | `vitalia/frontend/src/__tests__/architecture/` | builder-frontend | S |

**Implementación efectiva:** abrir story `vitalia-design-system-cement` en `vitalia/docs/product/stories/` → `/po-ux` redacta spec → `/architect` saca tickets → `/dev-team` ejecuta. O bien subsumir como T-fe-X de story UX foundation.

## 12. Referencias

- Brandbook raw (Chris brief sesión 2026-05-17) — origen visual (logo PNG + paleta + tono)
- `comunify/docs/architecture/design-system.md` — formato sibling (template estructural)
- `nicolify/frontend/src/features/copilot/` — fuente de fork para componentes copilot reales (65+ componentes auditados sesión 2026-05-17)
- `/tmp/vitalia-mockups.html` — mockup exploratorio sesión 2026-05-17 (3 patrones B/D.1/D.4) — **NO ratificado, solo referencia visual**
- `vitalia/docs/product/stories/vitalia-ux-discovery/00-research.md` — handoff sesión UX (decisiones cementadas + próximos pasos)
- `.claude/rules/frontend-fsd.md` — FSD-Lite + Shadcn UI baseline
- `.claude/rules/spanish-text.md` — strings user-facing (tuteo LatAm)
- `vitalia/.claude/rules/hipaa-lite.md` — PHI surface rules + audit log + dual filter
- `vitalia/config/brand.yaml` — feature flags + guardrails médicos + plan tiers
- `core/luana-core-platform/src/luana_core_platform/design-tokens/` — tokens engine cross-brand (futuro, cuando se lifteen patrones)

## Decisiones pendientes (post sesión 2026-05-17)

1. **Tipografía Display final** — confirmar General Sans o reemplazar (Cabinet Grotesk / Eudoxus / otra) → ADR-vitalia-001
2. **Verde-lima como 5to color oficial** — confirmar inclusión o eliminar del isotipo + tokens
3. **Dark mode roadmap** — Slice 2+ o ADR-vitalia-002 (out of scope MVP)
4. **Patrón UI primario** — pendiente sesión UX (ver `vitalia-ux-discovery/00-research.md`). Tokens base de este doc aplican independiente del patrón final
