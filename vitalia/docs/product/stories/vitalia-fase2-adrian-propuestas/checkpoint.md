---
story_id: vitalia-fase2-adrian-propuestas
type: ui-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: proposals
capability: adrian.propuestas
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
    - vitalia-payment-adapter-mvp           # service-blocker BE: planes pago Stripe/MP
  soft:
    - vitalia-fase2-adrian-embudo           # propuesta crea-se desde lead detail
    - vitalia-fase2-valeria-agenda          # propuesta aprobada → slot inicial auto-crea
    - vitalia-fase2-lisa-servicios          # treatments shipped consumidos
blocks_hard: []
blocks_soft:
  - vitalia-fase2-camila-reactivar          # cohorte "propuesta sin firmar 7d"
reuse_map_summary: "NEW workspace propuestas (no shipped prior) · REUSE treatments shipped · REUSE Stripe/MP shipped via payment-adapter-mvp · NEW firma digital embebida (canvas + audit hash) · NEW opt-in flag per vertical (dental/estética yes · psicología/psiquiatría no)"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes builder + plan pago + firma digital · /architect evaluar canvas/PDF embedded"

# Schema v2 migration (cement 2026-05-27)
release: F4   # release ID · ver releases/
cap_target: adrian.propuestas   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S6 vitalia-fase2-adrian-propuestas — checkpoint

## Goal

Sub-tab Propuestas de Adrián: opt-in per vertical (dental/estética sí · psicología/psiquiatría no). Workspace para crear/enviar/firmar propuestas de tratamiento con planes de pago. Builder visual:
1. **Tratamientos** — Multi-select desde catalog Lisa (treatments shipped)
2. **Plan pago** — Total · cuotas · método (efectivo · tarjeta · transferencia · MP suscripción · Stripe payment plan)
3. **Términos** — Condiciones · cancelación · garantías
4. **Firma digital** — Embedded canvas (paciente firma desde link público) + hash auditable

Estado de propuesta: `borrador · enviada · vista · firmada · pagada · vencida · cancelada`. Trazabilidad pagos por cuota.

## Anti-objetivos

- NO implementar firma con certificado digital legal (esto es firma simple + audit hash · firma legal-grade es story futura)
- NO implementar plantillas reutilizables de propuesta (story dedicada futura)
- NO implementar e-invoicing inline (delegado a F2-S1 cobrar saldo subform + fiscal-emission service)
- NO duplicar `Treatment` model (vive en `vitalia/backend/src/modules/vitalia/treatments/`)
- NO tocar `core/luana-core-*` (read-only)

## Scope verbatim

### § 1 — Page + opt-in vertical check

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/propuestas/page.tsx`:

```tsx
import { ProposalsView } from '@/features/adrian/components/propuestas/ProposalsView'
import { getInitialProposalsState } from '@/features/adrian/api/propuestas-server'
import { getBrandConfig } from '@/lib/brand/config-server'

export default async function Page({ params }: PageProps) {
  const { tenantId } = await params
  const brandConfig = await getBrandConfig(tenantId)
  
  // OPT-IN check per vertical
  if (!brandConfig.features?.proposals_enabled) {
    return <ProposalsDisabledView vertical={brandConfig.vertical} />
  }
  
  const initialData = await getInitialProposalsState({ tenantId })
  return <ProposalsView initialData={initialData} />
}
```

`opt_in_per_vertical` per navigation-tree:
- `dental`: true
- `estetica`: true  
- `psicologia`: false
- `psiquiatria`: false

`ProposalsDisabledView` renderiza Design Contract `EmptyState` con explicación + link a F2-S20 config-cuenta para enable feature.

### § 2 — `ProposalsView`

Composición:
1. `<ProposalsHeader>` — Métricas tiny (active · sent · signed · won-value-mtd) + "+ Nueva propuesta" button
2. `<ProposalsTable>` — Lista con cols: Paciente PHI-masked · Treatments · Total · Status badge · Sent date · Signed date · Acciones
3. Click row → N3-dyn workspace `[proposal-id]`

### § 3 — `NewProposalBuilder` workspace (★ corazón valor)

`vitalia/frontend/src/features/adrian/components/propuestas/NewProposalBuilder.tsx`:

Layout 2-col: builder izq (form) + preview live der (PDF-style render del documento).

Builder sections (Shadcn `Tabs`):

#### Tab 1 — Paciente + tratamientos

- Paciente: autocomplete (consume `/api/crm/patients` PHI-masked) ó lead existente
- Treatments: multi-select desde catalog Lisa (consume `/api/treatments`)
- Cantidad por treatment (default 1, editable)
- Override precio per treatment (opcional · audit log row si override)
- Notas clínicas (textarea staff-facing)

#### Tab 2 — Plan pago

```tsx
// Esquema config:
type PaymentPlan = {
  totalAmount: number,
  currency: 'PEN' | 'USD' | 'ARS' | 'CLP',
  installments: number,           // 1 = pago único · 2-12 = cuotas
  installmentAmount: number,      // auto = totalAmount / installments
  firstPaymentDue: 'sign_date' | 'first_appointment' | 'custom',
  customFirstDate?: Date,
  intervalDays: number,           // 30 default
  method: 'cash' | 'card' | 'transfer' | 'mp_subscription' | 'stripe_payment_plan',
  earlyPaymentDiscount?: { type: 'percentage' | 'fixed', value: number },
}
```

UI:
- Total auto-calculado desde tab 1
- Slider/input cuotas
- Method selector (Shadcn `Select`)
- Preview cuotas tabla (fechas + amounts)
- Estimación intereses si payment-plan provider cobra (Stripe payment plan terms)

#### Tab 3 — Términos

- Textarea condiciones generales (template default vertical-specific)
- Política cancelación (radio: rígida · flexible · custom)
- Política garantías (textarea opcional)
- Notas legales (footer)

#### Tab 4 — Revisar + enviar

- Preview PDF-style full
- Channel envío: WhatsApp · Email · SMS · Link copy (todos generan link público + audit)
- Schedule: Inmediato · Programado
- Submit → POST `/api/proposals` + envío

### § 4 — Firma digital embebida (★)

`vitalia/frontend/src/features/adrian/components/propuestas/SignatureCanvas.tsx`:

Cuando paciente abre link público (`/sign/{proposal-token}`):

```tsx
// Página pública (no shell-organism — separate route):
// - Render PDF-style readonly del proposal
// - Canvas para firma (signature_pad library)
// - Checkbox "Acepto los términos descritos"
// - Submit → POST /api/proposals/{token}/sign con:
//   - signature_image_base64
//   - typed_name (legal name)
//   - timestamp
//   - ip_address (server-side capture)
//   - user_agent
//
// Backend:
// - Genera SHA-256 hash de (signature_image + typed_name + timestamp + ip)
// - Almacena hash + signature image en S3 encrypted
// - Audit log row signed + dispatcher event "ProposalSigned"
// - Si payment plan tiene immediate first installment → redirect a Stripe/MP checkout
// - Notification a clinic staff vía email + dashboard
```

Página pública NO requiere auth Clerk (link público con token cifrado). Token expira 30d desde send.

### § 5 — Proposal Detail N3-dyn workspace

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/propuestas/[proposal-id]/page.tsx`:

Tabs:
- **Resumen** — Status timeline (sent · viewed · signed · paid milestones) + actions (Reenviar · Cancelar · Duplicar)
- **Detalles** — Treatments + plan pago + términos
- **Firma** — Image firma + hash + IP + timestamp (audit-ready)
- **Pagos** — Tabla cuotas con status (pendiente · pagado · vencido) + dispatch nuevo payment
- **Comunicaciones** — Historial mensajes enviados (WhatsApp/Email/SMS log)
- **Trazabilidad** — Activity log completo

### § 6 — Status state machine

```
borrador → enviada → vista → firmada → pagada
                  ↘ vencida (link token expired)
                  ↘ cancelada (clinic ó paciente)
```

Side-effects automáticos:
- `firmada` → si payment plan first installment → check pago en 24h
- `firmada + payment_plan first paid` → `pagada` → auto-crear Appointment en Agenda Valeria (consume F2-S1)
- `vencida` → notify clinic + sugerir reenvío
- `pagada parcial > installment_overdue` → dispatch Camila trigger "propuesta sin pago"

### § 7 — HIPAA-lite voice patterns

Per `hipaa-lite.md`:
- Link público NUNCA contiene PHI clínico (solo treatments + amounts · sin diagnósticos)
- WhatsApp/SMS mensaje contiene SOLO link + nombre paciente (truncado initial+apellido)
- Email contiene preview + link
- Signature page tiene aviso "Esta información es confidencial. NO compartas el link."

### § 8 — Mobile responsive

- Builder → vertical accordion tabs
- Preview live → modal toggle ("Ver vista previa")
- Signature canvas → touch-friendly (tested @project=mobile)

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza opt-in check per vertical (disabled view si NO opt-in) |
| AC-2 | Builder wizard 4-tabs funciona end-to-end |
| AC-3 | Preview live actualiza al cambiar fields |
| AC-4 | Submit envía propuesta via canal seleccionado + audit log |
| AC-5 | Link público firma renderiza PDF-style + canvas firma |
| AC-6 | Sign submit guarda firma + hash + IP + dispatch event |
| AC-7 | Proposal `firmada + payment_plan paid` → auto-create Appointment Agenda |
| AC-8 | Status state machine transitions correctos |
| AC-9 | Proposal detail tabs funcionan |
| AC-10 | Token expiration 30d enforced (vencida si > 30d sin firma) |
| AC-11 | Visual goldens builder + preview + sign-public + detail × 2 themes |
| AC-12 | Mobile signature canvas touch-friendly |
| AC-13 | a11y axe pass (incluido sign-public page) |
| AC-14 | Cross-tenant query bloqueada |
| AC-15 | NO PHI clínico en link público / mensajes WhatsApp |
| AC-16 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: crear propuesta + firma + auto-create appointment

**Given:**
- Tenant dental opt-in
- Lead/paciente `P. Hernández` en embudo stage `listo`
- Treatment `Implante dental` $1500 PEN shipped
- `vitalia-payment-adapter-mvp` shipped
- F2-S1 valeria-agenda shipped

**When:**
1. User abre "+ Nueva propuesta" desde Adrián propuestas
2. Select paciente · select 1 implant · plan 3 cuotas $500 c/u · first due sign_date
3. Channel WhatsApp · submit
4. Paciente recibe link · abre sign-public page
5. Firma canvas · typed name "Pedro Hernández" · accept terms
6. Submit firma
7. Backend procesa primer pago via Stripe payment plan
8. Pago primer cuota OK

**Then:**
- Proposal status: `borrador → enviada → vista (cuando opens link) → firmada → pagada (cuando primer cuota OK)`
- Audit logs: per transition + signature hash stored
- Appointment auto-creado en Agenda Valeria (consume F2-S1 API)
- Notification staff vía email + dashboard
- Outbound mensaje paciente: "Propuesta firmada y primera cuota recibida. Tu próximo turno: Dr. X · martes 15:00"

**playwright_required:** true  
**Graders:**
- E2E shell + sign-public
- BE integration test full cycle
- Audit log full chain assert

### Scenario 2 — negative: token expirado

**Given:** Proposal sent hace 31 días, status `enviada` (paciente nunca firmó)

**When:** Paciente abre link

**Then:**
- Backend detecta token expirado
- Sign-public page muestra mensaje "Esta propuesta ha vencido. Contactá a la clínica para una nueva."
- Status proposal updated → `vencida` (background worker)
- Clinic staff notification
- NO firma posible

**playwright_required:** true  
**Graders:** E2E + BE token check

### Scenario 3 — edge: payment first installment fails

**Given:** Proposal firmada + payment plan first installment via Stripe

**When:** Stripe charge fails (card declined)

**Then:**
- Status proposal: `firmada` (no `pagada`)
- UI clinic: badge warning "Pago pendiente · reintentar"
- Outbound paciente: "Hubo un problema con el pago. Acá tienes un nuevo link para reintentar"
- Audit log: `payment_failed`
- NO auto-create Appointment (waits for paid status)

**playwright_required:** true  
**Graders:** E2E + BE retry logic test

### Scenario 4 — adversarial: signature replay attack

**Given:** Adversarial intent to replay signature from another proposal

**When:** POST `/api/proposals/{token}/sign` con signature_image de otra propuesta

**Then:**
- Backend valida hash signature vs original metadata (timestamp + ip)
- Si signature image hash already exists in another proposal → reject with audit `replay_attempt`
- Sentry alert

**playwright_required:** false (BE security test)  
**Graders:** `vitalia/backend/tests/modules/vitalia/proposals/test_signature_replay_protection.py`

### Scenario 5 — adversarial: link public sin auth con PHI leak

**Given:** Link public abierto sin auth

**When:** Page renderiza proposal

**Then:**
- NO clinical diagnosis visible (solo treatments names + amounts)
- NO patient DNI completo (truncado masking)
- Page server-side filtra PHI fields del response
- Audit log: `public_link_viewed` (sin contenido PHI)

**playwright_required:** true  
**Graders:** E2E + BE response inspection + axe

### Scenario 6 — keyboard-a11y sign canvas

**Given:** Sign-public page abierta en desktop

**When:** Foco en canvas

**Then:**
- Canvas tiene aria-label "Espacio para firmar"
- Tab + Enter activa modo touch (cursor visible)
- Esc cancela firma
- Submit button accesible Tab

**playwright_required:** true  
**Graders:** E2E + axe

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/propuestas/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/propuestas/[proposal-id]/page.tsx` | NEW (N3-dyn) |
| `vitalia/frontend/src/app/sign/[token]/page.tsx` | NEW (página pública firma) |
| `vitalia/frontend/src/features/adrian/components/propuestas/ProposalsView.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/propuestas/ProposalsDisabledView.tsx` | NEW (opt-in vertical) |
| `vitalia/frontend/src/features/adrian/components/propuestas/ProposalsTable.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/propuestas/NewProposalBuilder.tsx` | NEW (★) |
| `vitalia/frontend/src/features/adrian/components/propuestas/builder/{Paciente,PlanPago,Terminos,Revisar}Tab.tsx` | NEW (4 files) |
| `vitalia/frontend/src/features/adrian/components/propuestas/builder/ProposalPreview.tsx` | NEW (live render) |
| `vitalia/frontend/src/features/adrian/components/propuestas/SignatureCanvas.tsx` | NEW (signature_pad) |
| `vitalia/frontend/src/features/adrian/components/propuestas/proposal-detail/ProposalWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/propuestas/proposal-detail/tabs/{Resumen,Detalles,Firma,Pagos,Comunicaciones,Trazabilidad}Tab.tsx` | NEW (6 files) |
| `vitalia/frontend/src/features/adrian/api/propuestas.ts` | NEW |
| `vitalia/frontend/src/features/adrian/api/propuestas-server.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/proposal.types.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/proposal-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/proposals/api/proposals_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/proposals/api/signature_router.py` | NEW (public token) |
| `vitalia/backend/src/modules/vitalia/proposals/application/proposal_service.py` | NEW (state machine) |
| `vitalia/backend/src/modules/vitalia/proposals/application/signature_service.py` | NEW (hash + audit) |
| `vitalia/backend/src/modules/vitalia/proposals/application/payment_plan_dispatcher.py` | NEW (Stripe/MP) |
| `vitalia/backend/src/modules/vitalia/proposals/persistence/migrations/XXXX_proposals_init.py` | NEW (idempotent · pgcrypto cols) |
| `vitalia/frontend/e2e/shell-organism/adrian-propuestas-builder.spec.ts` | NEW |
| `vitalia/frontend/e2e/sign-public/sign-flow.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/propuestas/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/frontend/e2e/__screenshots__/sign-public/{desktop,mobile}.png` (×2) | NEW |
| `vitalia/backend/tests/modules/vitalia/proposals/test_state_machine.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/proposals/test_signature_replay_protection.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/proposals/test_token_expiration.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/proposals/test_phi_public_link_protection.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/proposals/test_payment_plan_dispatch.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/treatments` | Treatment model + catalog | CONSUME via API |
| Service-story `vitalia-payment-adapter-mvp` | Stripe payment plan + MP subscription | CONSUME via payment dispatcher |
| Service-story `vitalia-fiscal-emission-pe` | Future invoice emission (post-MVP) | NOT consumed F2-S6 — story future |
| `core/luana-core-compliance` | Outbound message validation | REUSE |
| `core/luana-core-events` | DomainEvent ProposalSigned · ProposalPaid | EMIT via outbox |
| F2-S1 `vitalia-fase2-valeria-agenda` | API `/api/scheduling/appointments` | CONSUME para auto-create |
| Shadcn primitives | `Tabs` · `Dialog` · `Select` · `Slider` · `Textarea` · `Table` · `Badge` | npx install |
| `signature_pad` library | Canvas firma | NEW npm install (~5KB) |
| `react-pdf` o html2canvas | PDF-style preview | NEW npm install (preview only · backend genera PDF real) |
| Nicolify FE — sales-agent proposals (if exists) | Pattern proposal builder | TRANSPONER si existe |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` — shell
- `vitalia-fase1-routing-shell` — App Router + public route `/sign/[token]`
- `vitalia-payment-adapter-mvp` — payment plan dispatch

### Soft
- `vitalia-fase2-adrian-embudo` — propuesta crea-se desde lead detail (link)
- `vitalia-fase2-valeria-agenda` — auto-create Appointment al pagar
- `vitalia-fase2-lisa-servicios` — treatments catalog

### Esta historia desbloquea
- `vitalia-fase2-camila-reactivar` — cohorte propuesta-sin-firmar-7d
- Future: story templates reutilizables · firma legal-grade

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Signature legal disputado | Media | Alto | Hash + IP + timestamp audit-ready · documentar "firma simple" no "firma cualificada" |
| PDF preview mismatched con backend final PDF | Media | Medio | Backend genera PDF post-firma con mismo template · screenshot comparison test |
| Signature canvas mobile UX pobre | Media | Medio | signature_pad library probado mobile · tests `@project=mobile` |
| Token brute-force | Baja | Crítico | Token 256-bit + rate-limit + audit attempts |
| Payment plan dispatch race | Media | Alto | Idempotency keys + outbox pattern (per anti-default-flip rule) |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 10 (builder + detail × 2 themes + sign-public desktop/mobile)
3. Backend tests state-machine + signature-replay + token-expiration + PHI-public-link + payment-dispatch pass
4. Story commits pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `adrian.propuestas` registrada

## Próximo paso post-done

- F2-S12 camila-reactivar consume cohorte propuesta-sin-firmar
- Story futura: templates reutilizables propuestas
- Story futura: firma legal-grade certificado digital

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Template spec:** `vitalia/docs/specs/templates/01-spec-shell-template.md`
- **Navigation tree:** § adrian.propuestas (opt_in_per_vertical)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Service stories:** `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/`
