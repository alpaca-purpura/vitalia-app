<!-- voseo-allowed: doc interno de build -->
# T-1b — Keystone resuelto (autosave identidad) + 2 bugs reales de contrato

> Continuación de T-1 (rebuild del layer e2e lisa-marca). Owner: `/dev-team` orchestrator
> (Opus), trabajo directo en el worktree canónico `wip/vitalia` con el stack UP (mandato:
> no delegar a builders aislados). Verificación REAL contra el stack + logs BE.

## Diagnóstico LIVE del keystone (no la hipótesis del handoff)

El handoff suponía "race de hidratación RHF: `fillName` antes del GET → `reset()` pisa el valor".
**Falso** — `IdentityCard` NO hace `reset()` y monta DESPUÉS del GET (skeleton lo gatea). El
diagnóstico real (live, con spec de sondeo + trace + body del GET):

1. El badge quedaba atascado en **`idle`** tras `fillName` → `onSave` NUNCA se llamaba → `isValid`
   nunca era `true`.
2. Body real del GET `/identity` del tenant de test:
   `{"name":"","slug":"","tagline":null,"clinic_vertical":"","primary_specialties":[],"updated_at":null}`.
3. **Mismatch de contrato FE↔BE** (el mock lo ocultaba): el BE vitalia devuelve `BrandIdentityDTO
   {name, tagline:str|None, clinic_vertical}`; el FE consumía una forma FICTICIA importada de
   nicolify (`brand_name`/camelCase + website/industry/founding_year). `fetchClient` casteaba ciego
   → `brand_name=undefined` + **`tagline=null`** → el zod `z.string().optional()` rechaza `null`
   (solo admite `undefined`/`""`) → `isValid=false` perpetuo → autosave muerto, cero PATCH.

## Fix 1 (FE prod, `src/features/lisa/api/marca.ts`)

Mapeo honesto del contrato real + null-safety:
- `getIdentity`: BE `{name, tagline, clinic_vertical, …}` → form `{brand_name: name??"", tagline:
  tagline??"", industry: clinic_vertical??"", …}` (nunca null/undefined). Preserva `clinic_vertical`
  + `primary_specialties` para `ClinicVerticalReadOnly`.
- `updateIdentity`: form → BE `{name?, tagline}` (BrandIdentityPatchDTO). Omite `name` si vacío
  (el BE exige `min_length=2` → mandar "" daría 422). `tagline:""` → `null` en BE.
- TDD: `__tests__/marca-contract.test.ts` (5 tests) RED→GREEN. `marca.test.ts` (25 keys) intacto.

## Fix 2 (BE prod, `brand_studio/.../marca_service.py`) — bug que mi Fix 1 DESTAPÓ

Al destrabar el PATCH /identity, el save+recarga dejó `GET /visuals` en **500**:
`AttributeError: 'BrandIdentity' object has no attribute 'visuals'`. Causa: el modelo de dominio del
**engine** `BrandIdentity` (`luana_core_brand_studio.domain.identity`) **NO declara `visuals`** — es
un atributo dinámico que desaparece al serializar/recargar un identity sin visuals. El test viejo lo
enmascaraba con `MagicMock()` (auto-crea cualquier atributo).
- Fix defensivo en el **servicio** (engine OFF-LIMITS, promotion gate): `getattr(identity, "visuals",
  None)` en `get_visuals` (lectura que crasheaba) + `patch_visuals` (init). Nunca más 500.
- TDD: `tests/.../test_marca_visuals_missing_attr.py` (3 tests) con el `BrandIdentity` REAL del
  engine → RED (AttributeError) → GREEN. ruff clean.

## Fix 3 (harness, `lisa-marca-identidad-autosave.spec.ts`)

Tests `edita el tagline` (SC) + `datos cargan al montar` pasaban solo por seed implícito de otro
test. Convertidos a **write-then-assert** auto-contenidos (RN-6):
- tagline: siembra un brand_name válido + espera su PATCH, luego edita tagline y espera un PATCH
  NUEVO (`>patchesAfterSeed`) — no depende de estado de DB.
- load: round-trip honesto — escribe nombre único → espera PATCH 200 → **reload** → verifica que el
  backend lo hidrató de vuelta (persistió).

## Verificación REAL (no 200-teatro)

- `_diag` live: badge `idle→dirty→saved`, BE log `PATCH /api/v1/lisa/marca/identity 200 OK` +
  invalidation-refetch (GET post-PATCH) confirma persist.
- `GET /visuals`: era 500 (`BrandIdentity has no attribute 'visuals'`) → ahora **200 OK** (live, post
  reload del BE).
- **`lisa-marca-identidad-autosave.spec.ts ×3 → 14 passed, 0 flaky`** contra backend real.
- FE: tsc/eslint clean en scope. BE: nuevo test GREEN, ruff clean.

## Deuda pre-existente (NO de esta story, documentada)

- `test_marca_service.py` = `@pytest.mark.integration` → skipea sin DB (false-green latente).
- `test_marca_router_*.py` usan `AsyncClient(app=app)` → roto por httpx 0.28 (necesita
  `ASGITransport`). El handoff ya lo scopeó fuera.
- La identidad FE (nicolify-importada) tiene inputs `website/industry/founding_year` que el BE vitalia
  no persiste (solo name+tagline). No bloquea el harness; es deuda de producto.

## Estado

Layer **identidad** verde-determinista ×3. Próximo: phantom-POMs restantes (voz-tono/presencia/
contact/logo/trust/voice) + de-mock revelations de esos specs + suite completa ×3 + parent ×5.
