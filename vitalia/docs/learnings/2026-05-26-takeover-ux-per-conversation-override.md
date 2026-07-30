---
brand: vitalia
date: 2026-05-26
slug: takeover-ux-per-conversation-override
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, fitflow]
target_core_package: core/luana-core-ui/inbox/ (futuro · cuando ≥2 brands lo necesiten)
story_introduced: vitalia-fase1-empty-states
phase: fase-1
type: ux-pattern
---

# Takeover UX — botón explícito "Tomar el control" per-conversación en inbox agéntico

**Qué aprendimos:** sales_studio shipped (`ap_sales_agent/frontend/src/features/closer-studio/components/inbox/`) tiene `handler_mode: 'bot'|'human'` con border-l verde como INDICADOR PASIVO de qué conversación está manejando el usuario. Chris feedback durante F1-S10 iter 2: *"el adrián decide / te consulta / manual, sé que es para todos y está bien pero el usuario puede intervenir una conversación específica pausando a adrián y hablando uno mismo, eso lo tienes contemplado? porque no es muy intuitivo"*.

**Origen:** F1-S10 vitalia-fase1-empty-states batch 2 Q6 (cementada 2026-05-26).

**Why (problema UX):** El toggle global "🤖 Adrián decide / 👀 Te consulta / ✋ Manual" arriba aplica a TODAS las nuevas conversaciones. Pero el usuario necesita intervenir UNA conversación específica (ej. paciente complicado) SIN cambiar el modo global. El handler_mode passive border no es discoverable + no comunica "tomar el control activamente".

## Pattern UX cementado

### Estado A — Adrián maneja (default)

- Thread header con chip `🤖 Adrián decidiendo` + botón cyan "✋ Tomar el control" (tooltip: "Tomar el control de esta conversación · Adrián pausará aquí (no afecta otras convs)")
- MessageInput disabled · placeholder "🤖 Adrián decide automáticamente · toma el control para escribir tú"
- Thread footer hint: "Adrián decidirá la próxima respuesta automáticamente · clic ✋ Tomar el control arriba para responder tú"

### Estado B — Usuario en control (post click "Tomar el control")

- Thread header: chip + botón takeover desaparecen
- **TakeoverBanner amarillo** debajo del header:
  - Icon ⚡ + título "Tienes el control · Adrián pausado en esta conversación"
  - Meta "El modo global '🤖 Adrián decide' no se altera · solo aquí · puedes devolver el control cuando quieras"
  - Botón ámbar "🤖 Devolver a Adrián"
- MessageInput enabled · placeholder "Escribir como tú a {patient_name}…" + auto-focus
- Thread footer hint cambia (amarillo): "⚡ Estás respondiendo como tú · Adrián volverá a manejar la conversación cuando devuelvas el control"

### ConversationList signaling

- `handler_mode='human'` → ConversationItem muestra:
  - border-l-2 verde (passive signal — pattern shipped sales_studio)
  - + chip "✋ Tú" (font-size 9px, bg green-100/30, border green-500/50) — NEW
  - tooltip "Tomaste el control · Adrián pausado en esta conversación"

## How to apply

**Cuándo aplica:** inbox agéntico cross-brand donde el bot maneja conversaciones automáticamente pero el usuario necesita override puntual.

**Aplicabilidad:**
- **Nicolify:** agencias B2B inbox lead (Adrián equivalent) — aplicable inmediato si lift a `core/luana-core-ui/inbox/`
- **Comunify:** creator community inbox — aplicable
- **Fitflow:** fitness coach inbox alumnos — aplicable
- **Lupulo:** gastronomy inbox reservas — aplicable

**Implementación F1-S10 (brand-local Vitalia):**
- `features/adrian/components/inbox/ThreadHeader.tsx` (2 estados A/B)
- `features/adrian/components/inbox/TakeoverBanner.tsx` (banner amarillo state B)
- `features/adrian/components/inbox/MessageInput.tsx` (state dual)
- `features/adrian/components/inbox/ConversationItem.tsx` (YouChip inline)
- AdrianInboxPlaceholder organismo con `useState<"adrian"|"human">` local React F1 (mock-only)

**Implementación F2-S3 funcional (Fase 2 — `vitalia-fase2-adrian-inbox`):**

- Frontend:
  - `useInboxStore` Zustand con `handlerOverride: Map<leadId, 'bot'|'human'>` (separate del `handlerMode` global)
  - `takeControl(leadId)` muta map + PATCH `/api/v1/inbox/conversations/{leadId}/handler` body `{mode:'human'}`
  - `releaseControl(leadId)` mismo flujo con `mode:'bot'`
  - URL searchParam preservation `?lead=X` (pattern shipped sales_studio)

- Backend:
  - DB column `conversation.handler_override` (default `null` = sigue global)
  - Engine `core/luana-core-sales-agent` consulta `handler_override` antes procesar mensaje entrante. Si `'human'` → solo logea event + no genera respuesta.
  - Evento `conversation.handler.taken_over` (cuando usuario toma control) → pausa bot
  - Evento `conversation.handler.released` (cuando devuelve) → bot resume normal

- Extension SDK candidate:
  - `core/luana-core-extension-sdk/.../extension_points.py::ExtensionPointRegistry` → EP-N `inbox_handler_override` opt-in per brand

## Promotion path (cross-brand lift)

Cuando ≥2 brands necesiten inbox agéntico con takeover:
1. `/pm-luana` abre proposal `docs/promotion-protocol/proposals/2026-XX-lift-inbox-takeover-ux.md`
2. Lift a `core/luana-core-ui/inbox/` (TS package shared cross-brand frontend)
3. Brand opts-in via `{brand}/config/brand.yaml::features.inbox_takeover: true`
4. Cada brand cablea según su modelo agéntico (Vitalia=Adrián · Nicolify=Adrián equivalente · etc.)

NO requerido lift aún F1-S10 (solo Vitalia shippea inbox actualmente).

## Anti-patterns prohibidos

- ❌ Solo passive border verde sin acción (no es discoverable — feedback Chris confirmó)
- ❌ Toggle global cambia behavior per-conversación (rompe expectativa "global ≠ per-conv")
- ❌ Auto-takeover al escribir (magic UX · poco predecible · difícil discover devolver)
- ❌ MessageInput siempre habilitado sin signaling estado actual (confusión bot vs usuario)
- ❌ NO mostrar quién está respondiendo (sender attribution en MessageBubble crítica)

## Referencias

- `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/01-spec.md` § 3.2 + § 5 SC-4.bis + § 10 microcopy takeover verbatim
- `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/mockups/adrian-inbox-placeholder.html` (UX visual canónico)
- sales_studio reference: `/home/chalreme/Documentos/ap_sales_agent/frontend/src/features/closer-studio/components/inbox/` (handler_mode passive pattern shipped — extendido con takeover UX en Vitalia)
