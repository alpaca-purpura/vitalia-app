# T-FIX impl-log — open_findings (sesión 5, /dev-team fix-loop)

> Fix-loop sobre story `developed`. Hallazgos post-developed de la revisión UX live (sesión 4).
> Lane: `code:crm` (embudo). NO toca shell ni inbox (índice compartido, sesión inbox viva).
> Investigación completa por /dev-team (Opus orchestrator) ANTES de delegar a builders.

## Diagnóstico verificado (lectura de código + 1 repro live)

### B2 · score 10-vs-0 (BE, my lane) — CONFIRMADO
`crm/application/services/funnel_service.py::get_lead_detail` (línea 517) computa
`score, factors = self._scorer.compute(lead)` pero el response (línea 527
`_lead_to_response(lead)`) serializa `lead.score` (STORED, 0 para lead nuevo sin
transiciones). El breakdown usa `factors` (suma 10) → contradicción glass-box en el Resumen.
- **Score lifecycle:** transiciones SÍ persisten `compute()` (líneas 262/270/341); el CREATE
  no computa score inicial → `lead.score=0` stored hasta la 1ª transición. El create vive en
  el `lead_service` compartido (**lane inbox**) → fix write-side PROHIBIDO cruzar lane.
- **Fix (read-side, my lane):** en `get_lead_detail`, poner el score COMPUTADO en el response
  (`_lead_to_response(lead)` + override `.score = score`, o `model_copy(update={"score": score})`).
  El board (línea 414 `_lead_to_card` usa `lead.score`) NO está flagged por Chris y no muestra
  breakdown al lado → no es contradicción visible; queda como P2 (empty-states "sin puntuación").
- **TDD:** RED → lead con factores que suman 10 reporta `detail.lead.score == 10` (no 0).

### U1 · nombre enmascarado (FE, my lane) — RATIFICADO Chris=nombre completo
`PiiMaskedSpan` **siempre enmascara** (componente dumb; "role-based unmasking handled at BE
level" pero el BE manda el nombre crudo). Lead = `phi_classification: non_phi` (prospecto
marketing). El masking estaba sobre-aplicado. Quitar en:
- `LeadCard.tsx:132` · `ResumenView.tsx:153` · `FrozenLeadRow.tsx:94` (consistencia: el 3º es la
  lista Recuperar, misma decisión — el vendedor debe distinguir el lead en las 3 superficies).
- Remover imports `PiiMaskedSpan` que queden sin uso.

### U2 · Resumen sin teléfono/email (BE+FE, my lane) — contract-safe
BE `LeadResponse` (lead_dto.py) YA expone `email`+`phone`. Pero el detail FE tipa
`LeadDetailResponse.lead` como `LeadCardDTO` (board projection, SIN phone/email por diseño —
board_dto excluye PII a propósito). El contract-parity gate (`test_fe_be_contract_parity.py`,
FE⊆BE) PROHÍBE widenar FE `LeadCardDTO` con phone/email (board BE no los manda → FAIL).
- **Fix contract-safe:** crear FE `LeadDetailLeadDTO` que ESPEJE BE `lead_dto.LeadResponse`
  (incl. email, phone, name, score, assignedDoctorId…); retipar `LeadDetailResponse.lead`;
  registrar `ContractPair(lead_dto.LeadResponse ↔ LeadDetailLeadDTO)` en CONTRACT_PAIRS.
- BE: agregar `assigned_doctor_id: UUID | None = None` a `LeadResponse` + poblarlo en
  `_lead_to_response` (el detail DEBE mostrar el doctor — hoy la fila Doctor está siempre vacía
  porque LeadResponse no lo manda; bug latente que el espejo resuelve de paso).
- FE: ResumenView — bloque "Datos del lead" → Nombre (completo, plain) + Teléfono + Correo (plain;
  non_phi marketing → el vendedor necesita contactar; masking PHI aplica al convertir lead→paciente).

### B1 · Recuperar crashea (root cause = SHELL, NO recuperar-component) — CONFIRMADO live
**El handoff asumió "orden de hooks en recuperar". FALSO.** `RecuperarView` + `FrozenLeadRow`
tienen hooks limpios (incondicionales antes de cualquier return). Repro live (recuperar-live.spec
R-1, soft-nav board→recuperar ×25): 1 flaky reprodujo → page snapshot = `main "Cargando shell"`
STUCK. Root cause = el shell `dynamic({ssr:false})` (`ShellOrganismLayout`/`ShellOrganismLayoutClient`)
NO monta tras soft-nav (bug Next-16.2.3, learning 2026-06-03). **Es shell-level (lane inbox: su
`ShellOrganismLayoutClient.tsx` está en WIP sin commitear) → fix propio PROHIBIDO cruzar lane.**
- proxy.ts YA tiene el edge-redirect para el caso bare-tenant (mismo bug class) pero NO aplica
  acá (no hay redirect en la ruta recuperar; es soft-nav directo a página real).
- **Fix lane-safe (completo para recuperar):** el `frozen-kpi-badge` (EmbudoMetrics) es el ÚNICO
  entry point a `/adrian/recuperar` (no está en shell-routes) → hard-nav (`<a>` en vez de Next
  `<Link>`; "nav dura no lo trippea" — learning). Cubre el 100% de la superficie recuperar.
- **Escalado:** el flake del shell ssr:false en soft-nav sigue latente para OTROS intra-shell
  navs → finding shell-level (junto a U3) para cuando aterrice inbox / story de shell.

## Plan de ejecución
1. builder-backend (Sonnet): B2 (override score + TDD) + U2-BE (assigned_doctor_id en LeadResponse + _lead_to_response).
2. builder-frontend (Sonnet): B1 (hard-nav) + U1 (unmask ×3) + U2-FE (LeadDetailLeadDTO mirror + ResumenView + CONTRACT_PAIR + component test). Corre DESPUÉS del BE (dependencia de contrato).
3. Live-verify: resumen-live (score 10 + nombre + contacto) + recuperar-live R-1 (green tras hard-nav) + board-live (no regresión).

## iteration_log
- 2026-06-04T14:10 · /dev-team investigación completa + recuperar-live.spec creado + B1 reproducido live (1/25 flaky → shell stuck "Cargando shell"). Spawning builder-backend.
- 2026-06-04T14:12 · builder-backend (worktree, M9 footgun) → commit 342ba0bc (3 files). Cherry-pick a wip/vitalia = 78a7ba52. Verify nativo en mi worktree: ruff clean · funnel_service 12/12 · contract-parity 4/4. Pushed.
- 2026-06-04T14:27 · builder-frontend (worktree, M9 footgun) → commit 20c66eb3 (impl, 9 files) + 92053423 (docs). Cherry-pick impl a wip/vitalia = b1d32f83 (lead_dto auto-dedup). T-FIX-fe-result recovered. Verify nativo: tsc 0 · eslint adrian 0 · vitest embudo 20/20 (ResumenView 8 + LeadCard + use-lead-detail 6) · contract-parity 5/5 · 6 fallas = inbox-lane (AdrianInboxView×5 + ChannelBadge×1, blocker, NO mías).
- 2026-06-04T14:38 · live-verify B1: el FE builder NO pudo correr live (dev-app inalcanzable desde su worktree) → lo corrí YO. Rewrite R-1 (hard-nav aislado, sin goBack) → recuperar-live R-1 ×3 repeat (15 ciclos) = **5/5 PASS**. B1 confirmado: el chip hard-nav elimina el hang del shell ssr:false en board→recuperar (única superficie de acceso). Residual: el flake del shell en OTROS soft-navs (goBack, otros tabs) sigue latente → escalado (shell/inbox lane).
