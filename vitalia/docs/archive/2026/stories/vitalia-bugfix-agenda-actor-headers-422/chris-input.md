---
story_id: vitalia-bugfix-agenda-actor-headers-422
created_at: 2026-06-15T00:00:00-05:00
last_modified: 2026-06-15T00:00:00-05:00
notes_count: 1
refs_count: 0
conversation_count: 1
---

# chris-input.md · vitalia-bugfix-agenda-actor-headers-422

> Cocina de la story (conversación). 3 secciones: 💭 Notas · 📎 Referencias · 💬 Conversación.

## 💭 Notas

### 2026-06-15
Chris (al entrar a dev-app): la Agenda de Mateo carga vacía + errores. Pidió solucionar el
problema pre-existente del 422 (separado del shell-CSS, que confirmó arreglado).

## 📎 Referencias

(sin referencias)

## 💬 Conversación

> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-15 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Diagnóstico + repro confirmados ANTES de crear la story (repro-first):
- Root cause: el handler BE `agenda/grid` exige `X-Tenant-ID` + `X-Clinic-ID` + `X-User-ID`
  (HIPAA-lite); el FE (SSR `agenda-server.ts` + todos los hooks de `agenda.ts`) manda solo
  `X-Tenant-ID` → 422 → agenda vacía. **No es bug del BE.**
- Repro HARD: `curl … -H 'X-Tenant-ID: …'` → 422 con detail `X-Clinic-ID`/`X-User-ID` "Field required".
- Enmascarado por tests que mockean el BE (MSW) = verde-fantasma.

Story creada `state=idea` `type=bugfix` `cap_target=scheduling.mateo-agenda` `cap_change_type=fix`.
Próximo: Opus builder-frontend fix-and-own (agregar los 2 headers a SSR + client, mirror del
patrón staff, sin cross-feature import) + regression guard REAL.

⚠️ Live-verify browser (#37) PENDIENTE: Chrome DevTools MCP se desconectó esta sesión. Verifico a
nivel BE (curl 200 con los 3 headers) + FE gates; el live en dev-app queda para cuando reconecte
el MCP o lo confirmes vos (abrir mateo/agenda → slots cargan, 0 errores 422).

### 2026-06-15 (cont.) · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Fix completo (2 capas + 1 bonus), ratificaste arreglar ambos bugs BE + agregar `owner` a roles PHI:
- **FE (commit 729613aa):** los 5 hooks de agenda + SSR + payments/fiscal/notify mandan
  X-Clinic-ID + X-User-ID + X-User-Role (lift a `src/hooks/useActorHeaders.ts`). 422 eliminado.
- **BE (commit b7ccc360):** (1) RBAC — nuevo SSoT `scheduling/api/rbac.py` con `owner` agregado
  (ratificado); (2) 500 repo — `select().select_from(text()).outerjoin(ORM)` reescrito a `text()`
  parametrizado (mata el crash + el surface de SQL-injection); (3) BONUS destapado por la
  live-verify — el audit row `appointment.agenda_read` se rolleaba (session non-committing) →
  fix a `get_async_session_committing` (compliance HIPAA-lite).
- **Verificado live** (BE, seed real): owner→200 + audit persistido, doctor→200, recepcion→403,
  suspicious→400+audit. FE Playwright real-backend 4/4 (headers viajan, had422=false).
  173 scheduling + 353 arch tests verdes.

Queda tu signoff (G): abrí `/{tenant}/mateo/agenda` (incognito fresco) → debería cargar slots sin
errores. Con eso firmás y mergeo a done.
