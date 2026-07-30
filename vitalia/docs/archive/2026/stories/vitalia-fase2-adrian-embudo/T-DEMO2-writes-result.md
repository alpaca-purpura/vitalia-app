# T-DEMO-2 — Writes Live-Verify Result
# vitalia-fase2-adrian-embudo
# DoD Critical Rule #37

**Verificado:** 2026-06-04T04:26:38Z  
**Entorno:** `https://dev-app.vitalialat.com` (cloudflared → localhost:3002/8002)  
**Usuario de prueba:** `dr.demo@vitalialat.com` (role owner, tenant Sanaré, `E2E_TENANT_ID=e69a691d-070e-5caf-a053-6e74642ec100`)  
**Auth:** Clerk storageState playwright/.clerk/user.json  
**Spec:** `vitalia/frontend/e2e/regression/vitalia-fase2-adrian-embudo/board-live.spec.ts`  
**Project:** `smoke`

---

## Resultado global

| Tests | Resultado |
|---|---|
| Total | 9 |
| PASS | **9** |
| FAIL | **0** |
| SKIP | 0 |

**Overall: FULL PASS** — todos los writes ejercidos y confirmados en backend + DB.

---

## Playwright stdout

```
  ✓  [setup] › clerk setup (fast — auth file fresh, skip re-auth)
  ✓  [setup] › authenticate
  ✓  A-1: board carga sin Next bubble y columnas visibles
  ✓  A-2: lead cards sin 'undefined' (buyingSignals.slice ya no crashea)
  ✓  A-3: KPI strip visible (EmbudoMetrics no crash)
  ✓  B-1: form Nuevo lead accesible sin crash
  ✓  B-2: submit con datos dentales LatAm → POST /api/v1/crm/leads 201 [PASS]
  ✓  C-1: mover lead → PATCH /api/v1/crm/leads/:id/stage [PASS — 200 OK]
  ✓  C-2: reload tras move no crashea (persistencia)
  9 passed (38.8s)
```

---

## Fixes aplicados

### Fix B-2: data-testid en SelectTrigger canal

**Archivo:** `vitalia/frontend/src/features/adrian/components/embudo/nuevo/NewLeadPage.tsx`  
**Cambio:** `SelectTrigger id="channel"` → agregado `data-testid="lead-channel-select"` (1 atributo, additive).  
**Efecto:** Playwright puede localizar el trigger con `[data-testid="lead-channel-select"]`, hacer click, seleccionar "WhatsApp", y Zod valida el formulario → POST dispara.

### Fix C-1: move-stage button (non-drag affordance)

**Archivos:**
- `LeadCard.tsx` — prop `onMoveStage?: (leadId: string) => void` + botón `data-testid="move-stage-{leadId}"` (ChevronRight, aria-label="Mover a siguiente etapa")
- `PipelineColumn.tsx` — prop `onLeadMoveStage?` wired a `LeadCard.onMoveStage`
- `KanbanBoard.tsx` — prop `onMoveStage?` wired a `PipelineColumn.onLeadMoveStage`
- `AdrianEmbudoView.tsx` — `handleMoveStage` callback (busca lead en displayData, calcula next adjacent stage via `STAGE_ALLOWED_NEXT`, llama `handleStageDrop`) wired a `KanbanBoard.onMoveStage`

**Efecto:** El DnD-kit drag sigue disponible (PointerSensor + KeyboardSensor intactos). El botón es una affordance adicional accesible por teclado (SC-10) y por Playwright headless. Ambos caminos invocan el mismo `handleStageDrop` → `useLeadStageMutation` → `PATCH /api/v1/crm/leads/{id}/stage` con `version` field.

---

## Scenario B — WRITE create-lead

**B-2: PASS**

### Evidencia

**Payload enviado:** nombre (Demo Paciente {timestamp}), channel=whatsapp, phone=+99 9 1234 5678, serviceInterest=Ortodoncia invisible.  
**Respuesta:** `POST /api/v1/crm/leads → 201 Created`  
**lead_id creado:** `0d2313ff-72fa-45be-9e8e-e14eb0c3633e`  
**Redirect:** navegación a `/adrian/embudo?view=kanban&highlight=0d2313ff-72fa-45be-9e8e-e14eb0c3633e`  
**Gate anti-burbuja:** 0 pageerror, 0 hydration error, 0 console.error accionables.

### Backend log

```
2026-06-04 04:26:38 [info     ] lead_created  lead_id=0d2313ff-72fa-45be-9e8e-e14eb0c3633e tenant_id=e69a691d-070e-5caf-a053-6e74642ec100
2026-06-04 04:26:38 [info     ] lead_service.create  lead_id=0d2313ff-72fa-45be-9e8e-e14eb0c3633e tenant_id=e69a691d-070e-5caf-a053-6e74642ec100
INFO: 38.25.16.6:0 - "POST /api/v1/crm/leads HTTP/1.1" 201 Created
```

Sin Traceback. Sin ERROR.

### DB delta (create-lead)

| Métrica | Antes | Después |
|---|---|---|
| `vitalia_leads` count | 2 | **3** |
| Lead nuevo | — | `0d2313ff...` (stage=interesado, version=1, channel=whatsapp) |

---

## Scenario C — WRITE stage-transition

**C-1: PASS**

### Evidencia

**Lead:** `66afe78e-968b-545c-9454-449da3d7e66d` (stage=interesado, version=1)  
**Acción:** click en `[data-testid="move-stage-66afe78e-..."]` (ChevronRight button)  
**Respuesta:** `PATCH /api/v1/crm/leads/66afe78e-.../stage → 200 OK`  
**Stage transition:** interesado → calificando  
**Version exercised:** version=1 en payload → lead.version actualizado a 2  
**Gate anti-burbuja:** 0 errors. Board recargó sin crash (C-2 PASS).

### Backend log

```
2026-06-04 04:26:21 [info     ] funnel_transition_complete  from_stage=interesado lead_id=66afe78e-... score=10 tenant_id=e69a691d-... to_stage=calificando
INFO: 38.25.16.6:0 - "PATCH /api/v1/crm/leads/66afe78e-.../stage HTTP/1.1" 200 OK
```

Sin Traceback. Sin ERROR.

### DB delta (stage-transition)

| Tabla | Antes | Después |
|---|---|---|
| `vitalia_leads` (lead 66afe78e) | stage=interesado, version=1 | **stage=calificando, version=2** |
| `vitalia_lead_stage_transition` | 0 filas | **1 fila** (from=interesado, to=calificando, triggered_by=manual_override) |

---

## Conclusión DoD #37

`dod_live_verified: true`

**Los 2 writes fueron ejercidos LIVE con backend real:**

1. **POST /api/v1/crm/leads → 201** — lead creado, efecto en DB confirmado (count 2→3)
2. **PATCH /api/v1/crm/leads/:id/stage → 200** — etapa cambiada (interesado→calificando), version field ejercitado (1→2), fila en `vitalia_lead_stage_transition`

**9/9 tests PASS.** Sin Next bubble, sin Traceback, sin console.error accionables.

**Siguiente paso:** `/auditor` (Phase D gherkin-matrix + demo-script.md) → demo manual Chris → `demo_signoff: APPROVED` → merge.

---

*Generado por builder-frontend (Claude Sonnet 4.6) — 2026-06-04T04:30:00Z*
