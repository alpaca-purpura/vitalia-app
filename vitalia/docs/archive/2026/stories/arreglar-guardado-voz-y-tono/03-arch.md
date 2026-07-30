---
story_id: arreglar-guardado-voz-y-tono
brand: vitalia
arch_version: 1
schema_version: v4.1
type: bugfix
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na
cap_target: lisa-marca
cap_change_type: fix
---

# 03-arch.md (lite · bugfix) — arreglar-guardado-voz-y-tono

> Ready package **reducido** (ADR-011 bugfix lite). Arch + guidelines inline aquí; validators en `04-validators.yaml`;
> work units en `06-tickets.yaml`; dispatch en `dispatch-plan.md`.

## Surfaces involved

- **BE:** yes — (a) repoint 3 callers de `sanitize_payload` al wrapper PHI brand-local; (b) alias camelCase en 2 DTOs personality.
- **FE:** mínimo — sin cambios de componente; solo E2E nuevos. (El contrato se arregla en BE → FE intacto.)
- **AGENTIC:** no.

## Prior art audit (re-ejecutado desde architect)

- **Engine consumido vía import:** `luana_core_observability.recording.sanitization.sanitize_payload(payload)`
  (firma actual sin `compliance_level`). NO se edita engine.
- **Reuse brand-local (target del fix):** `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py::sanitize_phi_payload(payload)`
  — ya hace engine genérico + 22 PHI fields. Ya wired en `compliance/audit.py` + `whatsapp_free_phi_guard.py`. **Cero recreación.**
- **Import-cycle verificado:** `compliance/*` NO importa `audit/*` → `audit_writer → compliance_service_adapter` es seguro (una dirección).
- **Lift candidates:** ninguno para este bugfix. **Nota /pm-luana** (no bloqueante): el engine dropeó `compliance_level` dejando
  callers de marca rotos → evaluar si el engine debería exponer un sanitizer compliance-aware (hoy cada marca envuelve).
- **Net-new:** ninguno (reconciliación de contrato + cobertura E2E faltante).

## Decisión BE-1 — Fix root cause (HTTP 500)

`sanitize_payload(payload, compliance_level="hipaa_lite")` → `TypeError` (kwarg muerto). Repointar a `sanitize_phi_payload(payload)`:

| Archivo | Línea | Cambio |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | ~88/90 (`write_audit_log_sync`) | import `sanitize_phi_payload`; `safe_payload = sanitize_phi_payload(payload or {})` |
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | ~184/186 (`AsyncAuditWriter.write`) | idem |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | ~137/147 | import `sanitize_phi_payload`; `sanitized = sanitize_phi_payload(raw_props)` |

**Beneficio doble:** arregla el 500 **y restaura la redacción PHI** (la llamada rota nunca redactaba → hueco HIPAA-lite).
Actualizar los docstrings que citan `sanitize_payload(..., compliance_level='hipaa_lite')` para que reflejen el wrapper.
Mantener el `try/except ImportError` existente (entorno de tests sin engine) — `sanitize_phi_payload` ya lo maneja internamente.

## Decisión BE-2 — Fix contrato voice-blocks (HTTP 422 + hydration vacía)

**Causa:** FE usa camelCase (`soISpeak`, `identityAnchor`, …) en request **y** response; BE `BrandPersonality*DTO` es snake_case +
`extra="forbid"`. Sin transform en `fetchClient`. → editar un bloque de voz da `422 extra_forbidden`; y el GET devuelve snake_case
que el FE lee como `undefined` (bloques vacíos al cargar). El arquetipo solo no lo dispara (palabra única).

**Decisión:** alias camelCase en los **2 DTOs personality** (no tocar FE ni los otros DTOs):

```python
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

class BrandPersonalityDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    ...

class BrandPersonalityPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_camel)
    ...
```

`to_camel` mapea exacto al contrato FE: `so_i_speak↔soISpeak`, `so_i_dont_speak↔soIDontSpeak`, `identity_anchor↔identityAnchor`,
`domain_context↔domainContext`, `technical_context↔technicalContext`, `format_instructions↔formatInstructions`,
`personality_profile_id↔personalityProfileId`, `compiled_at↔compiledAt`, `compiler_version↔compilerVersion`, `tenant_id↔tenantId`;
`archetype` queda igual. FastAPI serializa response con `by_alias=True` (default) → emite camelCase. `populate_by_name=True` mantiene
que el código interno siga construyendo por nombre snake_case (`from_attributes`). `extra="forbid"` sigue bloqueando campos genuinamente extra.

**Alternativa descartada (Opción A):** migrar FE a snake_case (`PersonalityPatchPayload` + `PersonalityResponse` + `VozTonoView` apiFieldMap
+ unit tests). Más churn FE + tocar tests verdes. Opción B (BE alias) es más localizada y arregla request+response de un saque.
⚠️ Chris puede overridear a Opción A si prefiere convención snake_case end-to-end.

## Integration design (CONN)

- **Reachability path:** Owner en `/lisa/marca/voz-y-tono` → `ArchetypeSelector.onSelect` / `VoiceCompilerBlocks.onChange`
  → `usePersonalityAutosave.scheduleAutosave` (debounce 600ms) → `PATCH /api/v1/lisa/marca/personality`
  → `marca_router.patch_personality` → `MarcaService.patch_personality` → `AsyncAuditWriter.write` (ahora OK) → 200 → badge `saved`.
- **Consumers:** los 3 call sites reparados tienen consumers reales hoy (todo PATCH brand_studio + trust-signals + CRM + sales_agent obs + telemetría). NO se crea símbolo nuevo huérfano. Los DTOs aliasados los consume el FE existente.
- **Registration points:** ninguno nuevo (router `marca_router` ya montado en `main.py:82`). Cero islas.
- **Home (cap):** `brand_studio.lisa-marca` · `cap_change_type: fix`. Al merge, wire `e2e_test` del scenario voz-y-tono (hoy `null`) → cap pasa `declared-live → verified-live`.

## Guidelines (inline · bugfix lite)

**Required:** `sanitize_phi_payload` para toda escritura audit/telemetría PHI · `structlog` · Pydantic v2 `ConfigDict` ·
TDD RED→GREEN (test de regresión RED reproduce el TypeError ANTES del fix) · Spanish neutro · E2E contra **backend real** (sin mock del API).
**Forbidden:** llamar `sanitize_payload(..., compliance_level=...)` (kwarg muerto) · editar `core/luana-core-*` · mockear el API en el E2E
(verde falso, `verification-real-not-200`) · tocar otros DTOs/módulos fuera de scope · tocar componentes UI (no hay rediseño).
**Files NEVER touch:** `core/luana-core-*/src/**` · `{other_brand}/**` · `fetchClient.ts` · `components/ui/**`.

**must_load_skills (builder reporta "Skills consulted"):** `backend-expert`, `playwright-expert` (T-3), `tessl__pytest-api-testing`,
`.claude/rules/tenant-isolation.md`, `.claude/rules/backend-ddd.md`, `.claude/rules/tdd-mandatory.md`,
`.claude/rules/test-design-doctrine.md` (§ Verificación REAL), `vitalia/.claude/rules/hipaa-lite.md` (PHI redaction).

## Test Construction Plan (lite)

- `playwright_required: true`. base_path: `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/`
- **Orden:** (1) BE regression pytest RED (audit_writer + patch_personality) → fix BE-1/BE-2 → GREEN. (2) E2E specs.
- **scenario_to_test:** ver `04-validators.yaml § scenario_coverage` + `§ test_construction_plan`.
- **playwright_visual_scope:** ver `04-validators.yaml` (esta story NO cambia visual; E2E es funcional, no snapshot).
