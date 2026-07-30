---
story_id: vitalia-bugfix-agenda-actor-headers-422
type: bugfix
architecture_pattern: ADR-vitalia-004
module: scheduling                                # bucket code:scheduling (≠ horarios=clinics/ui-kit) — story-closure-gate cross-module

release: F2

cap_target: scheduling.mateo-agenda
cap_change_type: fix
parent_story: null

state: done
phase_workflow: DONE
last_artifact: 07-merge.md
last_modified: 2026-06-15
next_action: "DONE — merged (07-merge.md). chris_verify SATISFIED. cap change_log type=fix en scheduling.valeria-agenda. Fix FE headers (729613aa) + BE owner-RBAC/repo-SQLA/audit-persist (b7ccc360)."
ratified_by_chris: true
spawned_at: 2026-06-15
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null

# Bucket: code:scheduling (≠ horarios code:lisa/ui-kit) → paralelo OK
autonomous_mode: false

chris_verify:
  required: true                                  # bugfix funcional → demo_required (#37)
  signoff:
    by: Chris
    date: 2026-06-15
    result: SATISFIED
    notes: "Chris confirmó live (incognito fresco): la Agenda de Mateo carga slots sin errores (422/403/500 eliminados)."
    open_items: []
  rounds: []

# Bugfix repro-first gate (ADR-011 · hereda hotfix-repro-mandatory.md)
hotfix_metadata:
  repro_verified: true
  reproduced_local: true
  repro_command: "curl -s 'http://127.0.0.1:8002/api/v1/scheduling/agenda/grid?view=semana&date=2026-06-15' -H 'X-Tenant-ID: e69a691d-070e-5caf-a053-6e74642ec100'  →  HTTP 422 {\"detail\":[{\"loc\":[\"header\",\"X-Clinic-ID\"],\"msg\":\"Field required\"},{\"loc\":[\"header\",\"X-User-ID\"],\"msg\":\"Field required\"}]}"
  diagnosis_validates_handoff: true

# Dev-app live verification gate (ADR-vitalia-008 · #37) — REQUIRED
dev_app_verified:
  required: true
  evidence:
    - action: "FE: Playwright real-backend (localhost:3002, auth dr.demo, tenant e69a691d-…) carga /{tenant}/mateo/agenda + captura la request real a /scheduling/agenda/grid"
      observed: "los 3 headers actor (X-Clinic-ID + X-User-ID + X-User-Role) VIAJAN; had422=false (422 ELIMINADO). 4/4 passed."
    - action: "BE: request real al endpoint /scheduling/agenda/grid en :8002 con seed real (rol owner + clinic/user válidos), tras los fixes RBAC/repo/audit"
      observed: "owner→200 (antes 403); doctor→200 (antes 500 repo crash); recepcion→403 (correcto); suspicious-param→400. Audit row appointment.agenda_read PERSISTIDO en DB (antes se rolleaba — bug 3). 173 scheduling tests + 353 arch tests verdes."
dod_live_verified: true                           # fix ejercido live (request real + efecto: 200 + audit row persistido)
dod_evidence:
  - action: "Cargar la agenda de Mateo (GET grid) autenticado como dueño de clínica (owner), stack dev real"
    observed: "200 con el grid (antes vacía por 422→403→500); audit log row escrito; 0 errores. FE manda headers + BE los acepta + repo no crashea + audit persiste."
    backend_log: "GET /api/v1/scheduling/agenda/grid 200 · audit appointment.agenda_read committed · sin 422/403/500/traceback"
verified_at: 2026-06-15
---

# Bugfix — Agenda de Mateo da 422 (FE no manda X-Clinic-ID + X-User-ID)

## Síntoma

Ruta `/{tenant}/mateo/agenda`. La agenda carga **vacía** + el FE loguea
`[agenda-server] getInitialAgendaState failed: 422` repetidamente. El BE loguea
`GET /api/v1/scheduling/agenda/grid ... 422 Unprocessable Entity`. Chris lo vio al entrar a dev-app.

## Root cause (confirmado · repro curl)

El handler `get_agenda_grid` (`vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py:183`)
exige **3 headers requeridos sin default**: `X-Tenant-ID`, `X-Clinic-ID`, `X-User-ID`
(HIPAA-lite: dual-filter tenant+clinic + audit user). El FE manda **solo `X-Tenant-ID`**:

- **SSR** `vitalia/frontend/src/features/mateo/api/agenda-server.ts:95-99` → headers =
  `{Content-Type, Authorization, X-Tenant-ID}`. Falta clinic/user → 422 → `emptyGrid` (degradación).
- **Client** `vitalia/frontend/src/features/mateo/api/agenda.ts` → TODOS los hooks/mutations
  (`useAgendaGrid`, `useAgendaAggregates`, `useAppointmentDetail`, `useCreateAppointment`,
  `usePatchAppointmentStatus`, `useChargeAppointment`, `useEmitFiscalDoc`, `useSendReminder`)
  llaman `vitaliaFetch(url, { token, tenantId })` → inyecta X-Tenant-ID, NO clinic/user → 422.

**No es bug del BE** (el contrato HIPAA-lite es correcto). Es el FE que no manda los headers.

## Repro (HARD)

```bash
curl -s -w "\nHTTP %{http_code}\n" \
  'http://127.0.0.1:8002/api/v1/scheduling/agenda/grid?view=semana&date=2026-06-15' \
  -H 'X-Tenant-ID: e69a691d-070e-5caf-a053-6e74642ec100'
# → HTTP 422 · detail: X-Clinic-ID "Field required", X-User-ID "Field required"
```

## Por qué estaba enmascarado

Los tests FE mockean el BE (MSW `vitalia/frontend/src/test-utils/msw/handlers/agenda-handlers.ts`)
→ verde pero roto live. Mismo patrón verificación-real-≠-verde (lisa-marca / embudo-imagined-contract).

## Fix (FE · mirror del patrón staff que YA funciona)

Agregar `X-Clinic-ID` + `X-User-ID` a TODOS los fetchers de agenda:
- **Client:** lisa lo resolvió con `useStaffActorHeaders()` (X-User-ID desde `/users/me`) + `useClinicId()`
  (X-Clinic-ID). mateo NO puede cross-importar de `features/lisa` (FSD prohíbe cross-feature). →
  usar mecanismo compartido (`useClinicId()` ya es shared; para X-User-ID buscar el hook compartido
  o **LIFT a `lib/`/`hooks/`** si vive en lisa — NUNCA duplicar ni cross-import). Opción a evaluar:
  que `vitaliaFetch` auto-inyecte clinic+user igual que tenant.
- **SSR (agenda-server.ts):** X-Clinic-ID desde Clerk `session.sessionClaims["clinic_id"]` (así lo
  lee `(shell-organism)/layout.tsx`) + X-User-ID resuelto server-side (IAM `/users/me` o claims).
  Mantener `emptyGrid` como fallback graceful, pero con headers correctos → 200.

## Bar de verificación (DONE)

- `curl` con los 3 headers (X-Tenant-ID + X-Clinic-ID + X-User-ID válidos) → **200** (BE contract).
- FE: tsc + eslint + vitest verdes. Regression guard REAL: assert que los fetchers de agenda
  incluyen X-Clinic-ID + X-User-ID (NO un MSW-mock del propio surface — eso es el verde-fantasma).
- **Live (#37):** abrir `/{tenant}/mateo/agenda` en dev-app autenticado → slots cargan, **0 × 422**
  en logs FE/BE. PENDIENTE: Chrome DevTools MCP se desconectó esta sesión → live-verify cuando
  reconecte, o Chris confirma manual.
- `cap_change_type: fix` → al merge append change_log type=fix a `scheduling.mateo-agenda` (sin scenarios nuevos).

## Notas de scope

- Brand-local vitalia FE (`features/mateo`). No toca core, ni BE (el BE está bien), ni otras marcas.
- Si el helper de actor-headers hay que liftarlo a `lib/`/`hooks/` compartido → sigue siendo
  vitalia-local (no es engine `@luana/*`). Si tocara `@luana/*` → escalar /pm-luana.
