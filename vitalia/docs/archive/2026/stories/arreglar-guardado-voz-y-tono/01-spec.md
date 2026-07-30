---
story_id: arreglar-guardado-voz-y-tono
brand: vitalia
type: bugfix
state: refining
release: F2
cap_target: lisa-marca
cap_change_type: fix
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na
po_ux_version: 1
ratified_by_chris: true
---

# 01-spec (lite · bugfix) — arreglar-guardado-voz-y-tono

> **Bugfix lite (ADR-011):** spec corto enfocado en **scenarios de regresión**. Sin mockups ni
> `02-design-*` (no hay UI nueva). Hereda gate repro-first (`repro_verified: true` en checkpoint).

## § Context

- **Release:** F2 · **Módulo:** `brand_studio` · **Sub-sub-tab:** Lisa › Marca › Voz y tono (`/lisa/marca/voz-y-tono`)
- **Síntoma reportado (Chris):** al cambiar el *Arquetipo principal*, el guardado automático muestra "Error al guardar".
- **Root cause (reproducido en vivo · ver checkpoint.md):** el engine `luana_core_observability...sanitize_payload(payload)`
  dropeó el kwarg `compliance_level`; 3 callers de vitalia (`audit_writer.py:90/186`, `growth_studio_emitter.py:147`)
  siguen pasándolo → `TypeError` → **HTTP 500** en la escritura de audit log de `PATCH /api/v1/lisa/marca/personality`.
- **Bug secundario (mismo flujo):** voice-blocks FE camelCase (`soISpeak`…) vs BE `extra="forbid"` snake_case → **422** al editar un bloque.
- **Por qué shipeó:** el scenario `admin-define-voz-y-tono` de la cap `lisa-marca` está `status: live` con **`e2e_test: null`**
  (declarado live, nunca verificado — anti-patrón `verde por vacío`). El unit `usePersonalityAutosave.test.ts` **mockea** el API.

### Out-of-scope (anti-creep)

- NO se rediseña la UI de Voz y tono (componentes ya ratificados Fase 2).
- NO se toca el engine `core/luana-core-*` (fix es brand-local vía wrapper existente).
- NO se reescribe el compilador de voz v2 ni el voice-preview (solo el guardado).

## § Prior art applied

- **Engine consumido:** `luana_core_observability.recording.sanitization.sanitize_payload(payload)` — vía wrapper, NO recrear.
- **Reuse brand-local (target del fix):** `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py::sanitize_phi_payload(payload)`
  (engine genérico + 22 PHI fields `phi_fields.py`). Ya wired en `compliance/audit.py` + `whatsapp_free_phi_guard.py` → cero duplicación.
- **E2E pattern reusado:** `lisa-marca-identidad-autosave.spec.ts` + `lisa-marca-cross-tenant.spec.ts` (mismo módulo) como base del nuevo spec de voz-y-tono.
- **Cross-brand:** comunify usa `compliance_level=creator_economy` solo en docstrings, sin llamadas `sanitize_payload()` rotas → sin mirror que liftear.
  **Nota /pm-luana:** engine dropeó `compliance_level` y dejó callers de marca rotos → learning candidate (no bloquea este bugfix).
- **Net-new:** ninguno (es reconciliación de contrato + cobertura faltante).

## § Gherkin scenarios (regresión)

```yaml
scenarios:
  # ── PRIMARY: el bug reportado ──────────────────────────────────────────────
  - id: voz-arquetipo-autosave-persiste
    type: happy
    given: "Owner autenticado en Lisa › Marca › Voz y tono con un arquetipo actual (Caregiver)"
    when: "Cambia el Arquetipo principal a 'Sage' (Sabio); transcurre el debounce 600ms del autosave"
    then: >-
      El badge de autosave pasa saving→saved (NUNCA 'error') · PATCH /api/v1/lisa/marca/personality
      responde 200 (NO 500) · al recargar la página el arquetipo persiste en 'Sage' · se escribió 1 fila
      en vitalia_audit_log action='brand_personality_updated'
    playwright_required: true
    graders:
      - { type: e2e, path: "vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts" }
      - { type: state_check, target: db, query: "SELECT action FROM vitalia_audit_log WHERE action='brand_personality_updated' ORDER BY created_at DESC LIMIT 1", expect: "1 row" }
      - { type: be_regression, path: "vitalia/backend/tests/modules/vitalia/brand_studio/test_patch_personality_audit.py", note: "RED reproduce TypeError sanitize_payload(compliance_level=...) → GREEN tras fix" }

  # ── REGRESSION 500 (root cause) ────────────────────────────────────────────
  - id: audit-write-no-typeerror
    type: regression
    given: "Cualquier mutación brand_studio que escribe audit log (AsyncAuditWriter.write / write_audit_log_sync)"
    when: "Se invoca la escritura de audit con un payload de props"
    then: >-
      No se lanza TypeError 'sanitize_payload() got an unexpected keyword argument compliance_level' ·
      la fila de audit se escribe correctamente · idéntico para GrowthStudioEmitter.emit_event
    playwright_required: false
    graders:
      - { type: be_regression, path: "vitalia/backend/tests/modules/vitalia/audit/test_audit_writer_sanitize.py" }

  # ── COMPLIANCE: PHI redaction (HIPAA-lite) ─────────────────────────────────
  - id: audit-personality-sin-phi
    type: adversarial
    given: "Un payload de audit que contuviera campos PHI canónicos (p.ej. patient.dni, diagnosis)"
    when: "Se escribe la fila de audit del update de personality vía sanitize_phi_payload"
    then: >-
      Los 22 PHI fields canónicos quedan REDACTED en payload_redacted · la redacción genérica del engine
      (emails/teléfonos/tokens) también aplica · NUNCA texto verbatim de PHI en vitalia_audit_log
    playwright_required: false
    graders:
      - { type: be_unit, path: "vitalia/backend/tests/modules/vitalia/audit/test_audit_writer_sanitize.py::test_phi_redacted" }

  # ── REGRESSION 422 (bug secundario voice-blocks) ───────────────────────────
  - id: voz-bloque-edita-no-422
    type: regression
    given: "Owner en Voz y tono con el bloque 'Así hablo' visible"
    when: "Edita el texto del bloque 'Así hablo' y transcurre el debounce del autosave"
    then: >-
      El badge pasa saving→saved (NO 'error') · PATCH /api/v1/lisa/marca/personality responde 200
      (NO 422 extra_forbidden) · el texto del bloque persiste al recargar
    playwright_required: true
    graders:
      - { type: e2e, path: "vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-bloque-autosave.spec.ts" }
      - { type: contract_check, note: "FE PersonalityPatchPayload ↔ BE BrandPersonalityPatchDTO field-name alignment (decisión architect)" }

  # ── NEGATIVE ───────────────────────────────────────────────────────────────
  - id: arquetipo-invalido-validacion
    type: negative
    given: "Request directo a PATCH /personality con archetype fuera del enum {caregiver,sage,healer,hero}"
    when: "Se envía {archetype:'sabio'}"
    then: "Responde 422 de validación (literal_error) · NO 500 · el front no crashea (badge 'error' + retry)"
    playwright_required: false
    graders:
      - { type: be_unit, path: "vitalia/backend/tests/modules/vitalia/brand_studio/test_patch_personality_audit.py::test_invalid_archetype_422" }

  # ── NETWORK FAILURE ────────────────────────────────────────────────────────
  - id: autosave-error-muestra-badge
    type: edge
    given: "Owner en Voz y tono; el endpoint PATCH /personality responde 5xx/timeout (mock route)"
    when: "Cambia el arquetipo y dispara autosave"
    then: "El badge muestra estado 'error' · la UI no crashea · el usuario puede reintentar (próximo cambio re-dispara)"
    playwright_required: true
    graders:
      - { type: e2e, path: "vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-autosave-error.spec.ts" }

  # ── ADVERSARIAL cross-tenant ───────────────────────────────────────────────
  - id: cross-tenant-personality-bloqueado
    type: adversarial
    given: "Owner del tenant A autenticado"
    when: "Intenta PATCH /personality apuntando a datos del tenant B (X-Tenant-ID distinto al del token)"
    then: "403/404 · NO escribe ni lee personality del tenant B · sin leak cross-tenant"
    playwright_required: false
    graders:
      - { type: be_unit, path: "vitalia/backend/tests/modules/vitalia/brand_studio/test_patch_personality_audit.py::test_cross_tenant_blocked" }

  # ── ACCESSIBILITY ──────────────────────────────────────────────────────────
  - id: autosave-badge-aria-live
    type: accessibility
    given: "Owner en Voz y tono usando lector de pantalla"
    when: "El autosave transita dirty→saving→saved (o error)"
    then: "El estado del badge se anuncia vía aria-live (no solo color); contraste AA del badge"
    playwright_required: true
    graders:
      - { type: axe, ruleset: "wcag2aa" }
```

### Sub-categorías mandatory — cobertura / no-aplica (bugfix lite)

| Sub-categoría | Cubierta por | Nota |
|---|---|---|
| race_condition | `not_applicable` | autosave de personality cancela el debounce previo (un solo campo en vuelo); race de 2 tabs ya cubierto a nivel cap por `autosave-concurrente-dos-tabs` (identidad). |
| concurrent_users | `cross-tenant-personality-bloqueado` | — |
| network_failure | `autosave-error-muestra-badge` | — |
| empty_state | `not_applicable` | personality siempre tiene defaults (arquetipo Caregiver + bloques seed). |
| large_dataset | `not_applicable` | payload fijo (arquetipo + 6 bloques), sin paginación. |
| accessibility | `autosave-badge-aria-live` | — |
| i18n | `§ Microcopy` | Spanish neutro (sin voseo). |

## § Estados visuales (AutosaveBadge — existente, sin rediseño)

| Estado | Trigger | Visible |
|---|---|---|
| `idle` | Sin cambios | Badge neutro / oculto |
| `dirty` | Cambio detectado, pre-debounce | "Sin guardar" |
| `saving` | Mutación en curso | Spinner + "Guardando…" |
| `saved` | 200 OK | Check + "Guardado · hace un momento" |
| `error` | 4xx/5xx | Icono error + "No se pudo guardar. Reintenta." |

## § Microcopy (Spanish neutro LatAm — existente, verificar)

| Lugar | Copy |
|---|---|
| Badge saving | "Guardando…" |
| Badge saved | "Guardado" |
| Badge error | "No se pudo guardar. Reintenta." |
| Error carga | "No se pudo cargar la configuración de voz. Intenta de nuevo." |

Sin voseo. Tildes correctas.

## § Wireframes

**N/A** — bugfix sin UI nueva. La pantalla Voz y tono ya está ratificada (Fase 2, story `vitalia-fase2-lisa-marca`).

## § Telemetría

Sin eventos nuevos. (El fix de `growth_studio_emitter.py` restaura la emisión existente que hoy crashea.)

## § Nota cap ledger (para architect + merge)

El scenario `admin-define-voz-y-tono` (cap `lisa-marca`) tiene `e2e_test: null`. Al cerrar esta story, los
e2e nuevos (`voz-arquetipo-autosave.spec.ts`) deben **wirearse** a ese scenario (o a un scenario nuevo
`voz-arquetipo-autosave-persiste`). Si se agrega scenario nuevo → reclasificar `cap_change_type` a `extend`
en Fase F.3. Esto mueve la cap de `declared-live` → `verified-live`.
