# 07-merge — vitalia-bugfix-agenda-actor-headers-422

**Merged:** 2026-06-15 · **type:** bugfix · **cap:** scheduling.valeria-agenda (change_type: fix)
**chris_verify:** SATISFIED (Chris, 2026-06-15 — Agenda de Mateo carga slots, confirmado live)

## Qué se arregló
La Agenda de Mateo cargaba vacía + 422 repetidos. 3 capas:
1. **FE** — los fetchers de agenda (SSR + 5 hooks + payments/fiscal/notify) mandaban solo
   `X-Tenant-ID`; el handler BE exige `X-Clinic-ID` + `X-User-ID` + lee `X-User-Role` (HIPAA-lite).
   Fix: lift de actor-headers a `src/hooks/useActorHeaders.ts` (compartido, sin cross-import FSD).
2. **BE RBAC** — `owner` no estaba en `ALLOWED_PHI_ROLES` → 403 al dueño de clínica. Nuevo SSoT
   `scheduling/api/rbac.py` con `owner` agregado (ratificado Chris).
3. **BE 500** — `select().select_from(text()).outerjoin(ORM)` crasheaba (`TextClause.selectable`)
   → reescrito a `text()` parametrizado. + BONUS: audit row `agenda_read` se rolleaba (sesión
   non-committing) → `get_async_session_committing` (compliance HIPAA-lite).

## Commits
- `729613aa` — FE actor headers (useActorHeaders lift + 5 hooks + SSR + payments/fiscal/notify).
- `b7ccc360` — BE RBAC owner (rbac.py SSoT) + repo SQLA-2.0 + audit-persist.
- `d03933ad` — story state + dod_evidence.

## Verificación
- Live BE (:8002, seed real): owner→200 + audit persistido, doctor→200, recepcion→403, suspicious→400+audit.
- FE Playwright real-backend 4/4 (headers viajan, had422=false). 173 scheduling + 353 arch + 881 FE vitest verdes.

## Cap ledger
`scheduling/valeria-agenda.yaml` — change_log append type=fix (sin scenarios nuevos).

## Deuda derivada (trackeada)
HB-74 (gate contract-test FE↔BE faltante) + HB-75 (rol actor inconsistente SSR vs client).
