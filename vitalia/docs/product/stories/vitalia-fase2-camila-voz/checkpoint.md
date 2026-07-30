---
story_id: vitalia-fase2-camila-voz
type: ui-story
agent_owner: camila
map_zone: agentes
map_box: camila
module: voice_of_customer
capability: camila.voz
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 5-7
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-adrian-inbox             # mensaje signals dispara triggers
    - vitalia-fase2-valeria-pacientes        # nps_score per patient
    - vitalia-fase2-lisa-compliance          # channel guards aplican aquí
blocks_hard: []
blocks_soft:
  - vitalia-fase2-camila-reactivar
  - vitalia-fase2-camila-multiplicar
  - vitalia-fase2-camila-reputacion
reuse_map_summary: "REUSE fidelización+NPS shipped · REUSE 12-triggers SSoT (cementado 2026-05-21 shell-organism baseline) · NEW UI 3-sub-vistas (Entrante · Curaduría · Activos vivos) FUSIONADAS · NEW paradigma 3-modos Camila (Decide-solo / Consulta / Manual) idéntico Adrián"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes 3-sub-vistas UN flujo · /ux-agentico diseñar conversación Camila si aplica"

# Schema v2 migration (cement 2026-05-27)
release: F7   # release ID · ver releases/
cap_target: camila.voz   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S11 vitalia-fase2-camila-voz — checkpoint

## Goal

Sub-tab "Voz del paciente" de Camila: corazón de Mantener-CLTV. UN flujo único con 3 sub-vistas conceptuales fusionadas:
1. **Entrante** — Signals brutos desde sources (NPS submissions · reseñas · menciones redes · in-chat sentiment · trigger events SSoT)
2. **Curaduría** — Tracking signals procesados pendientes acción (status: prioridad alta · media · baja)
3. **Activos vivos** — Acciones tomadas activas (campaigns running · responses publicadas · referrals iniciados)

12 triggers SSoT cementados en navigation-tree (paradigma origen 2026-05-21):
1. nps-9-10 (promoter)
2. nps-7-8 (passive)
3. nps-0-6 (detractor)
4. resena-4-plus (review positive)
5. resena-3 (review neutral)
6. resena-menor-3 (review negative)
7. mencion-positiva (social mention +)
8. mencion-negativa (social mention -)
9. dormant-60d (no activity 60+ days)
10. fin-tratamiento (treatment completed)
11. mantenimiento-vence-30d (maintenance reminder)
12. promotor-sin-referir-14d (promoter inactive)
13. cumpleanos (birthday)
14. propuesta-sin-firmar-7d (proposal pending sign)
15. imagen-testimonio (testimonial image opportunity)

(Cuenta total 15 triggers · "12" es shorthand del paradigma original.)

Paradigma 3-modos idéntico Adrián Inbox: Decide-solo (autónomo) · Consulta (sugiere humano aprueba) · Manual.

## Anti-objetivos

- NO duplicar engine sales-agent
- NO implementar respuestas reseñas Google/IG auto (requiere API external · story future)
- NO implementar AI sentiment analysis nuevo (consume engine sales-agent intent_detector)
- NO tocar `core/luana-core-*`
- NO duplicar 12-triggers definition (cementado en `vitalia/backend/src/modules/vitalia/voice_of_customer/triggers.py` post-shipped)

## Scope verbatim

### § 1 — Page + 3-sub-vistas FUSIONADAS

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/voz/page.tsx`:

`<CamilaVozView>` con segmented control 3 sub-vistas (Shadcn `Tabs`):

```
[ Entrante ]  [ Curaduría ]  [ Activos vivos ]
```

Cada sub-vista renderiza misma estructura layout (3-panel: Lista signals/items · Detalle central · ContextSidebar derecho) pero con datasets distintos.

### § 2 — Entrante view

`vitalia/frontend/src/features/camila/components/voz/EntranteView.tsx`:

Lista signals chronological con filter trigger types (multi-select 15 triggers).

Cada signal card:
- Trigger badge (color-coded per priority: 🔴 detractor · 🟢 promoter · 🟡 passive · etc.)
- Patient PHI-masked + canal origen
- Snippet del signal (e.g., "NPS 4/10 - 'Pésimo trato'")
- Timestamp relativo
- Acciones: "Curar" (mover a Curaduría) · "Descartar" · "Auto-actuar" (si modo Decide)

Click card → detalle central + ContextSidebar muestra patient_history.

### § 3 — Curaduría view

`vitalia/frontend/src/features/camila/components/voz/CuraduriaView.tsx`:

Lista signals movidos desde Entrante en estado `curating`. Workspace per signal:
- Plan acción Camila sugiere (modo Decide o Consulta)
- Approve/Edit/Reject controls
- Si signal es detractor → "Plan recuperación" template wizard
- Si signal es promoter → "Plan referencias" template

### § 4 — Activos vivos view

`vitalia/frontend/src/features/camila/components/voz/ActivosVivosView.tsx`:

Lista acciones en curso:
- Campaigns running (referencia F2-S5/F2-S12 cross-link)
- Outbound responses sent (esperando reply)
- Referrals iniciados
- Recovery plans active
- Testimonios in-progress (imagen pendiente upload)

Status badges + métricas live (clicks · replies · conversions).

### § 5 — Mode Toggle (3-modos Camila)

Idéntico Adrián Inbox per § 5 F2-S3:
- 🤖 Decide solo
- 🤝 Consulta
- 👤 Manual

Cambio mode persiste per signal_id o per trigger_type (config global o per-signal).

### § 6 — Triggers SSoT consume

Backend `vitalia/backend/src/modules/vitalia/voice_of_customer/`:

- Triggers registry: `triggers.py` (15 triggers cementados)
- Listener service (event-bus subscriber): cuando `nps.submitted` event → procesa via trigger registry
- Action dispatcher: per trigger + mode → ejecuta o queue para human review

Backend endpoint `/api/voz/signals` agrega signals filtered by status (entrante · curating · active).

### § 7 — HIPAA-lite voice patterns

Camila respuestas auto en chat respetar `hipaa-lite.md`:
- Detractor con menciones clínicas → derive a portal seguro
- Respuestas WhatsApp NUNCA contienen diagnóstico
- ComplianceService valida outbound

### § 8 — Mobile responsive

3-tabs sub-vistas + per-vista tabs (Lista · Detalle · Sidebar accordion).

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 3 sub-vistas toggle |
| AC-2 | Entrante view lista signals con filters 15 triggers |
| AC-3 | Click signal → detalle central + sidebar carga |
| AC-4 | "Curar" mueve signal de Entrante → Curaduría |
| AC-5 | Curaduría view propone plan acción (Camila suggested) |
| AC-6 | Activos vivos lista acciones en curso con métricas live |
| AC-7 | Mode toggle (3-modos) funciona idéntico Adrián |
| AC-8 | Audit log per trigger fired + per mode change + per action dispatched |
| AC-9 | HIPAA-lite voice enforce (ComplianceService bloquea PHI outbound) |
| AC-10 | Visual goldens × 6 (3 sub-vistas × 2 themes) |
| AC-11 | a11y axe pass |
| AC-12 | Cross-tenant query bloqueada |
| AC-13 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: trigger NPS detractor + plan recuperación

**Given:** Paciente envió NPS = 3. Trigger `nps-0-6` fired. Modo Consulta.

**When:**
1. Signal aparece en Entrante con badge 🔴 "Detractor NPS 3"
2. User click "Curar" → signal move a Curaduría
3. Camila sugiere "Plan recuperación: Disculpas + propuesta call con doctor + bonus en próximo tratamiento"
4. User edit propuesta → approve

**Then:**
- Outbound mensaje paciente enviado (WhatsApp / Email per channel pref)
- Signal status → active en "Activos vivos"
- Métricas track: reply received → conversion outcome
- Audit log full chain

### Scenario 2 — edge: trigger cumpleanos paciente opt-out

**Given:** Paciente cumpleaños hoy. Trigger fired. Paciente opt_out=true.

**When:** Action dispatcher processa

**Then:**
- ComplianceService bloquea outbound (opt-out check)
- Signal queda en Entrante con badge 🚫 "Opt-out · no se envió"
- Audit log

### Scenario 3 — adversarial: PHI en signal detalle

**Given:** Reseña Google contiene texto "El doctor X me diagnosticó cáncer" (PHI clínico)

**When:** Backend processa reseña como signal

**Then:**
- sanitize_payload aplica → diagnóstico ofuscado en detalle
- Signal trigger `resena-menor-3` fired pero snippet "El doctor X me [REDACTED]"
- Click expand pide auth role doctor + audit `phi_read_redacted_signal`

### Scenario 4 — keyboard-a11y 3-sub-vistas

**Given:** Foco en primera sub-vista tab

**When:** Arrow → cycle sub-vistas

**Then:** aria-selected actualiza · screen reader anuncia · tabs lógicos

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/voz/page.tsx` | MODIFY |
| `vitalia/frontend/src/features/camila/components/voz/CamilaVozView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/EntranteView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/CuraduriaView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/ActivosVivosView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/SignalCard.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/ModeToggle.tsx` | REUSE shared con Adrián Inbox (lift candidate cross-feature) |
| `vitalia/frontend/src/features/camila/components/voz/PlanRecuperacionWizard.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/voz/PlanReferenciasWizard.tsx` | NEW |
| `vitalia/frontend/src/features/camila/api/voz.ts` | NEW |
| `vitalia/frontend/src/features/camila/types/signal.types.ts` | NEW (15 triggers) |
| `vitalia/frontend/src/features/camila/types/signal-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/voice_of_customer/api/voz_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/voice_of_customer/triggers.py` | NEW (SSoT 15 triggers) |
| `vitalia/backend/src/modules/vitalia/voice_of_customer/application/listener_service.py` | NEW (event-bus subscriber) |
| `vitalia/backend/src/modules/vitalia/voice_of_customer/application/action_dispatcher.py` | NEW |
| `vitalia/backend/src/modules/vitalia/voice_of_customer/persistence/migrations/XXXX_signals.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/camila-voz-flow.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/camila-voz-mode-toggle.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/voz/{view}-{light\|dark}.png` (×6) | NEW |
| `vitalia/backend/tests/modules/vitalia/voice_of_customer/test_triggers_registry.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/voice_of_customer/test_listener_idempotency.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/voice_of_customer/test_phi_sanitize_signal.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/voice_of_customer/test_opt_out_enforce.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/fidelizacion/` (NPS) | NPS submission + score | REUSE + trigger emission |
| `core/luana-core-events` | DomainEvent bus + outbox | EMIT trigger events |
| `core/luana-core-sales-agent` intent_detector | Sentiment analysis on messages | CONSUME via engine API |
| `core/luana-core-compliance` | Channel guards + outbound validate | REUSE |
| F2-S3 adrian-inbox `ModeToggle` | 3-modos pattern | LIFT shared → `components/shared/shell-organism/ModeToggle.tsx` |
| Shadcn primitives | `Tabs` · `Card` · `Dialog` · `Badge` · `Select` | npx install |
| Vitalia archived — `vitalia-slice-1-fidelizacion` | NPS UI primera versión | REFACTOR migrar al camila/voz |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-adrian-inbox` — message signals dispara triggers
- `vitalia-fase2-valeria-pacientes` — nps_score per patient (cohorte source)
- `vitalia-fase2-lisa-compliance` — channel guards

### Esta historia desbloquea
- `vitalia-fase2-camila-reactivar` — consume triggers dormant + propuesta-sin-firmar
- `vitalia-fase2-camila-multiplicar` — consume triggers promoter
- `vitalia-fase2-camila-reputacion` — consume signals reseñas

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Triggers fired duplicate (no idempotency) | Media | Medio | Idempotency keys per (trigger_id + signal_source_id) test arch fitness |
| Mode Toggle lift to shared genera conflicts | Baja | Bajo | Share component path tested cross-feature |
| ComplianceService gap en algunos outbound paths | Baja | Crítico | Arch fitness enumera paths + assert validate llamada |
| 15-triggers cementados expanden post-MVP | Alta | Bajo | Registry extensible · versioning |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 6
3. Backend tests triggers + idempotency + sanitize + opt-out pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `camila.voz` registrada

## Próximo paso post-done

- F2-S12 camila-reactivar consume cohortes desde voz signals
- F2-S13 camila-multiplicar consume promotores
- F2-S14 camila-reputacion consume signals reseñas para panorama

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § camila.voz (15 triggers SSoT)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Engine sales-agent:** `core/luana-core-sales-agent` (intent_detector)
- **F2-S3 ModeToggle:** lift candidate shared
