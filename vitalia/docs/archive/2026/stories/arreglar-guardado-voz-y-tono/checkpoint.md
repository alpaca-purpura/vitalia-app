---
story_id: arreglar-guardado-voz-y-tono
brand: vitalia
type: bugfix
state: done
phase: MERGED
last_artifact: 07-merge.md
gherkin_matrix: 06-audit/gherkin-matrix.md
audit_verdict: APPROVED
last_artifact_prev: T-3-result.md
build_summary: >-
  4 root causes fixed + VERIFIED LIVE (curl real backend → 200 + audit + telemetry).
  T-1 38aa5c8b (sanitize TypeError) · T-1.bis a0060e7a (SQL ::uuid cast) ·
  T-2 98a903a5 (camelCase DTO alias) · T-2.bis 81b13787 (telemetry async+tenant_id) ·
  T-3 2b12924e (E2E specs + a11y; tsc+Vitest 13/13 green). Unit/arch all GREEN.
e2e_status: >-
  Suite voz-y-tono VERDE-DETERMINISTA (2x consecutivas, 0 failed/flaky) sobre backend REAL para la
  regresión núcleo: arquetipo autosave (badge saving→saved, PATCH 200 no 500) + bloque no-422
  (camelCase fix). Quarantine (authTest.fixme → estabilizar-harness-e2e-lisa-marca) de los asserts
  dependientes de la race de auth-readiness de Clerk: reload-persist (arquetipo+bloque), error-UX SC-5,
  a11y. Persistencia verificada REAL (curl PATCH→GET round-trip). Robustez producción: getTokenReady()
  en VozTonoView. Contraste verde WCAG AA pre-existente → observed-bugs/2026-05-30-voz-y-tono-contraste-verde-wcag.md.
e2e_followup: "estabilizar-harness-e2e-lisa-marca (creada) re-habilita los quarantined + contraste"
last_artifact_files: 06-tickets.yaml
autonomous_mode: true
autonomous_mode_ratified_by: chris
autonomous_mode_caps: { iterations_per_ticket: 8, audit_iter: 3, cost_usd: 2.50, walltime_min: 60 }
release: F2
cap_target: lisa-marca
cap_change_type: fix
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na
parent_story: vitalia-fase2-lisa-marca
agent_owner: lisa
module: brand_studio
last_modified: '2026-05-30T22:10:00.000Z'
spawned_at: '2026-05-30'
spawned_by: cockpit-extend-cap
ratified_by_chris: true
ratified_by_chris_at: '2026-05-30T22:10:00-05:00'
repro_verified: true
parallel_safe: true
next_action: /pm-vitalia merge → 07-merge.md + wire e2e_test cap lisa-marca + git mv archive → state=reviewing→done
goal: >-
  Cuando cambio de Arquetipo principal me sale un mensaje de error en el
  guardado automático. Corregirlo + revisar/crear la prueba E2E Playwright que
  verifique cambio y autoguardado de Arquetipo principal (y voz-y-tono).
---
# arreglar-guardado-voz-y-tono — checkpoint

## Goal

Cuando cambio de Arquetipo principal sale un mensaje de error en el guardado automático.
Corregir el guardado + cubrir con E2E Playwright real (no mock) el flujo cambio + autoguardado.

## Tipo: `bugfix` (lite — ADR-011)

Arreglo de comportamiento roto, scope quirúrgico, **sin diseño nuevo**. No construye componente UI
nuevo → gates `shell-mockup-per-component` y `shell-feature-architecture` (9 secciones) **N/A**.
Hereda gate **repro-first** (`hotfix-repro-mandatory.md`) → `repro_verified: true` (abajo).

## Root cause (reproducido EN VIVO 2026-05-30, stack `make dev-vitalia`)

El engine `luana_core_observability.recording.sanitization.sanitize_payload(payload)` **perdió el kwarg
`compliance_level`** (lift commit `bdefd801`, firma actual `def sanitize_payload(payload: dict) -> dict`).
**3 call sites de vitalia siguen pasando `compliance_level="hipaa_lite"`** → `TypeError` → **HTTP 500**.

**Repro verbatim:**
```
PATCH /api/v1/lisa/marca/personality  {"archetype":"sage"}  → HTTP 500
Traceback:
  marca_router.py:427  patch_personality
  marca_service.py:486  → self._audit.write(...)
  audit_writer.py:90/186  sanitize_payload(payload, compliance_level="hipaa_lite")
  TypeError: sanitize_payload() got an unexpected keyword argument 'compliance_level'
```
(`{"archetype":"sage"}` pasa RBAC+validación; el 500 ocurre en la escritura de audit log.)

### Blast radius (NO es solo el arquetipo)

Las 3 llamadas rotas son infra-shared brand-local → rompen **toda** mutación que escribe audit log o telemetría:

| Archivo:línea | Call | Impacto |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py:90` | `write_audit_log_sync` (sync/admin) | audit writes sync |
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py:186` | `AsyncAuditWriter.write` | **todo** PATCH brand_studio (identity/visuals/personality/contact), trust-signals, CRM activity, sales_agent obs |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py:147` | `emit_event` props sanitize | toda telemetría growth_studio |

## Fix recomendado (brand-local — sin engine edit, sin /pm-luana lift)

Apuntar las 3 llamadas al **wrapper brand-local ya existente**:
`vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py::sanitize_phi_payload(payload)`
— hace redacción genérica del engine (`sanitize_payload(payload)`) **+** redacción de los 22 PHI fields
canónicos (`phi_fields.py`). Beneficio doble: (1) arregla el 500, (2) **restaura** la redacción PHI que
estaba silenciosamente muerta (la llamada rota nunca redactó PHI → hueco HIPAA-lite). Ya está wired en
`compliance/audit.py` + `whatsapp_free_phi_guard.py` → patrón probado, cero duplicación.
⚠️ Arquitecto: verificar no-ciclo de import (audit → compliance).

## Bug secundario (mismo sub-sub-tab voz-y-tono — confirmado en vivo)

FE manda voice-blocks en **camelCase** (`soISpeak`, `soIDontSpeak`, `identityAnchor`, `domainContext`,
`technicalContext`, `formatInstructions`) vs BE `BrandPersonalityPatchDTO` **snake_case + `extra="forbid"`**
→ editar un bloque de voz da **422 `extra_forbidden`** (`{"soISpeak":"hola"}` → 422 reproducido).
El cambio de arquetipo solo no lo dispara (`{archetype}` es palabra única). Decisión del arquitecto:
alinear FE→snake_case · ó BE `populate_by_name` + alias · ó transform en `fetchClient`. **In-scope
recomendado** (la story es "voz-y-tono" completo); si se quiere scope ultra-quirúrgico, separar a bugfix hijo.

## E2E gap (lo que pidió Chris revisar)

- `usePersonalityAutosave.test.ts` **mockea** `updatePersonality` → verde falso (nunca tocó el 500).
  Anti-patrón `test-design-doctrine.md` § Verificación REAL ≠ 200.
- **NO existe E2E** de voz-y-tono autosave. Los specs lisa-marca existentes solo cubren `identidad`
  (`lisa-marca-identidad-autosave.spec.ts`). El autoguardado de arquetipo/personality tiene **cero** cobertura real.
- Requerido: (a) pytest BE regresión que ejerza `AsyncAuditWriter.write`/`patch_personality` (RED → TypeError),
  (b) E2E Playwright voz-y-tono que ejerza cambio de arquetipo + edición de bloque, **contra backend real (sin mock)**.

## Prior art scan (anti-duplication-refining)

- **Engine**: `luana_core_observability...sanitize_payload(payload)` — consumir vía wrapper, NO recrear.
- **Reuse**: `sanitize_phi_payload` (brand-local) ya existe = target del fix (cero recreación).
- **Cross-brand**: comunify usa `compliance_level=creator_economy` solo en docstrings/metadata, NO en llamadas
  `sanitize_payload()` → sin mirror que liftear. **Nota /pm-luana**: el engine dropeó `compliance_level` y dejó
  callers de marca rotos → learning candidate (¿el engine debería ofrecer sanitizer compliance-aware, o cada marca
  envuelve?). No bloquea este bugfix (wrapper brand-local es correcto).

## Scope (archivos)

- BE fix: `audit/audit_writer.py` (×2) + `_shared/telemetry/growth_studio_emitter.py` (×1)
- [secundario] FE/BE contract voice-blocks: `features/lisa/api/marca-voice-api.ts` ó `brand_studio/api/dtos/marca_dtos.py` ó `lib/api/fetchClient.ts`
- Tests: pytest BE regresión (audit write) + Playwright E2E voz-y-tono autosave + des-mockear/ampliar unit
- **NO toca**: `core/luana-core-*` · otros brands · componentes UI nuevos

## Estado

Repro-first ✅ · ratificado por Chris (instrucción directa) ✅ · listo para `/po-ux` lite.
