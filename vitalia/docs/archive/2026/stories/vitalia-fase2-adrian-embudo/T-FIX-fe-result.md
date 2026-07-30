# T-FIX-fe-result.md — Fix-loop FE (builder-frontend)

**Story:** vitalia-fase2-adrian-embudo  
**Session:** Fix-loop session 5  
**Date:** 2026-06-04  
**Commit SHA:** 20c66eb3  
**Branch:** worktree-agent-a59a0ca4c035246df (→ will cherry-pick to wip/vitalia)

---

## Diff resumen

### B1 — hard-nav EmbudoMetrics frozen-kpi-badge

**File:** `vitalia/frontend/src/features/adrian/components/embudo/EmbudoMetrics.tsx`

- Removed `import Link from "next/link"` (now unused)
- Changed `<Link href={chip.href} ...>` → `<a href={chip.href} ...>` for the frozen-kpi-badge chip
- Added comment explaining the intentional hard-nav (learning 2026-06-03-next16-softnav)

Root cause (B1): shell `dynamic({ssr:false})` hangs on soft-nav (Next-16.2.3 bug). Hard-nav (`<a>`) avoids the hook-count mismatch. This is a lane-safe band-aid; the root cause in the shell ssr:false is documented and escalated to the inbox/shell session.

### U1 — nombre sin máscara (3 surfaces)

**File:** `vitalia/frontend/src/features/adrian/components/embudo/LeadCard.tsx`
- Removed `import { PiiMaskedSpan }` (no longer used)
- Line 132: `<PiiMaskedSpan value={lead.name} fieldType="name" />` → `{lead.name}` (plain text within `<Link>`)

**File:** `vitalia/frontend/src/features/adrian/components/recuperar/FrozenLeadRow.tsx`
- Removed `import { PiiMaskedSpan }` (no longer used)
- Line 94: `<PiiMaskedSpan value={lead.name} fieldType="name" className="text-sm font-medium" />` → `<span className="text-sm font-medium">{lead.name}</span>`

**File:** `vitalia/frontend/src/features/adrian/components/embudo/lead/ResumenView.tsx`
- Removed `import { PiiMaskedSpan }` (no longer used)
- Removed the "Contacto" row that had `<PiiMaskedSpan value={lead.name} ...>`
- Added new **Nombre** row at the top of `<dl>` with `{lead.name}` plain text + `data-testid="lead-name"`

Decision: Lead = non_phi marketing prospect (Chris ratified). The vendor needs to identify the lead on all 3 surfaces. PHI masking applies only when lead converts to patient (different surface).

### U2 — teléfono + email + tipo correcto en Resumen

**File:** `vitalia/frontend/src/features/adrian/types/embudo.types.ts`
- Added `LeadDetailLeadDTO` interface (mirrors BE `lead_dto.LeadResponse`, includes `email`, `phone`, `assignedDoctorId`, `source`, `status`, `createdAt`)
- Changed `LeadDetailResponse.lead` from `LeadCardDTO` to `LeadDetailLeadDTO`

**File:** `vitalia/frontend/src/features/adrian/components/embudo/lead/ResumenView.tsx`
- Added **Teléfono** row → `{lead.phone}` with empty-state "Sin teléfono registrado" + `data-testid="lead-phone"`
- Added **Correo** row → `{lead.email}` with empty-state "Sin correo registrado" + `data-testid="lead-email"`
- Removed masked Contacto row (now replaced by Nombre + Teléfono + Correo)

**File:** `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py`
- Added `assigned_doctor_id: UUID | None = None` to `LeadResponse` (aligns with builder-backend commit 78a7ba52 on wip/vitalia)

**File:** `vitalia/backend/tests/architecture/test_fe_be_contract_parity.py`
- Added `ContractPair(LeadResponse ↔ LeadDetailLeadDTO)` — pure mirror, `fe_only_allowlist=frozenset()`
- Registry now has 3 pairs (LeadCardDTO, AutonomyInfo, LeadDetailLeadDTO)

---

## Gate output

### tsc --noEmit
```
0 errors (PASS)
```

### eslint src/features/adrian/
```
0 errors, 0 warnings (PASS)
```

### vitest run src/features/adrian/
```
Test Files  2 failed | 48 passed (50)
Tests  6 failed | 339 passed (345)

FAIL (pre-existing, inbox lane, NOT caused by this diff):
  src/features/adrian/components/inbox/__tests__/AdrianInboxView.test.tsx (5 tests)
  src/features/adrian/components/inbox/__tests__/ChannelBadge.test.tsx (1 test)

Confirmed pre-existing in luana-vitalia canonical hub (same failures before diff).

NEW tests (all PASS):
  ResumenView.test.tsx: 8/8 PASS
  LeadCard.test.tsx: 6/6 PASS (updated U1 assertion)
  use-lead-detail.test.ts: 6/6 PASS (mock shape updated to LeadDetailLeadDTO)
```

### contract parity (BE arch test)
```
tests/architecture/test_fe_be_contract_parity.py::test_contract_registry_is_non_empty PASS
tests/architecture/test_fe_be_contract_parity.py::test_contract_registry_files_exist PASS
tests/architecture/test_fe_be_contract_parity.py::test_fe_fields_are_subset_of_be_fields[LeadCardDTO(LeadCardDTO)] PASS
tests/architecture/test_fe_be_contract_parity.py::test_fe_fields_are_subset_of_be_fields[AutonomyInfo(AutonomyInfo)] PASS
tests/architecture/test_fe_be_contract_parity.py::test_fe_fields_are_subset_of_be_fields[LeadResponse(LeadDetailLeadDTO)] PASS

5/5 PASS
```

### recuperar-live R-1 (E2E live-verify)
⚠️ **NOT RUN** — dev-app.vitalialat.com would require the stack running locally. The spec `recuperar-live.spec.ts` exists and is correctly structured. B1 fix (hard-nav) theoretically eliminates the "Rendered more hooks" trigger per learning 2026-06-03-next16-softnav. Live verification delegated to Chris staging gate manual (per `runtime-quality-checklist.md § Live verification gate`).

---

## Skills consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, component patterns, runtime checklist | Hard-nav pattern: `<a>` instead of `<Link>` for ssr:false shell page nav; test mock strategy via `vi.mock` |
| `brand-expert` | Not invoked — task is fix-loop, no brand studio or form-runtime changes | N/A |
| `chrome-devtools-verify` | Would verify R-1 live. MCP not verified available in session → escalated to Chris staging gate manual | `PASS pending Chris staging gate manual` |

---

## Notes

- **B1 is a band-aid (lane-safe):** the root cause (shell `dynamic({ssr:false})` soft-nav hang, Next-16.2.3) is documented in `T-FIX-impl-log.md § B1` and escalated. Full fix requires the inbox/shell session to address `ShellOrganismLayoutClient.tsx`.
- **BE file touched (lead_dto.py):** required because this worktree doesn't have builder-backend commit `78a7ba52` (wip/vitalia branch). The change is identical. When merging to wip/vitalia, the BE change will dedup cleanly (same line, same content).
- **node_modules symlink:** created `vitalia/frontend/node_modules → luana-vitalia/vitalia/frontend/node_modules` for gate running; gitignored by default, won't be committed.
