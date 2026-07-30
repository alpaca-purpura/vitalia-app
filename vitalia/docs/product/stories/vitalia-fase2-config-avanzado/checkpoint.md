---
story_id: vitalia-fase2-config-avanzado
type: ui-story
agent_owner: config
module: admin_advanced
capability: config.avanzado
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-22
ratified_by_chris: false
parallel_safe: true
priority: medium
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lisa-compliance            # cross-link raw audit log
blocks_hard: []
blocks_soft: []
reuse_map_summary: "NEW workspace técnico admin (uso poco frecuente per filosofía paradigma) · 7 sub-secciones (Reglas · Raw audit · LLM keys BYO · Flags · API tokens · Import/Export · Danger zone) · CONSUME engine compliance + observability"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes 7 sub-secciones · /architect evaluar danger zone safety"

# Schema v2 migration (cement 2026-05-27)
release: F4   # release ID · ver releases/
cap_target: config.avanzado   # capability slug target (v2 cement 2026-05-27)
cap_change_type: null   # (null en idea phase)
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S22 vitalia-fase2-config-avanzado — checkpoint

## Goal

Sub-tab Avanzado de Configurar: workspace técnico admin. 7 sub-secciones per navigation-tree:
1. **Reglas & políticas** — Business rules · stage rules embudo · etc.
2. **Registro técnico raw** — Audit log raw inspection (cross-link desde Lisa compliance)
3. **LLM keys BYO** — Bring-your-own LLM keys (Anthropic · OpenAI · etc.) opcional
4. **Feature flags** — Toggle features per tenant
5. **API tokens & webhooks** — Outgoing tokens custom + webhooks subscribe
6. **Import/Export** — Bulk import pacientes / treatments · Export DB tenant
7. **Danger zone** — Reset tenant · delete account · cancelation con multi-step confirm

## Anti-objetivos

- NO duplicar engine compliance audit log
- NO permitir delete sin multi-step confirmation + cool-off period
- NO exponer raw secrets en UI (masked + reveal solo con re-auth)

## Scope verbatim

### § 1 — Page + 7 sub-secciones

`<ConfigAvanzadoView>` Shadcn Tabs vertical (sub-sections largas):

### § 2 — `ReglasPoliticasSection`

Listas configurable rules:
- Stage rules embudo (per F2-S4 transitions)
- Audit log retention — **editor de política de retención per categoría** (★ reframe 2026-06-07: el editor MOVIDO acá desde lisa-compliance; antes decía "edit en compliance"). Lisa→Compliance solo muestra el ESTADO read-only de retención. Defaults regulados (no reducir bajo mínimo). Ver `vitalia-fase2-lisa-compliance/00-pm-recommendation.md`.
- Time-zones default · idioma · currency
- HSM templates approval workflow toggle

### § 3 — `RawAuditLogSection`

Tabla raw audit_log:
- Columns: timestamp · user · action · resource · clinic_id · ip · payload_redacted
- Filter por action type · date range · user · resource
- Export CSV
- Cross-link a Lisa Compliance semáforo

PHI sanitize aplicado (sin diagnóstico raw).

### § 4 — `LLMKeysBYOSection`

Bring-your-own keys (cost optimization · enterprise feature):
- Anthropic key (masked · reveal con re-auth)
- OpenAI key
- Otros (Kimi · DeepSeek · Gemini · Qwen)
- Test connection button
- Si configured → backend routea via BYO en lugar Luana default
- Encryption at-rest (pgcrypto)

### § 5 — `FeatureFlagsSection`

Lista flags per tenant:
- `proposals_enabled` (per F2-S6 opt-in vertical)
- `realtime_websocket` (post-MVP enable per tenant)
- `analytics_attribution_model` (per F2-S18)
- ... extensible

Toggle on/off · audit log per flag flip · backend valida side-effects per `anti-default-flip-audit.md` rule.

### § 6 — `APITokensWebhooksSection`

API tokens custom para integrations terceras:
- Generate token con scope
- Revoke / rotate
- Webhook subscribe URLs custom (HMAC verified)
- Activity log

### § 7 — `ImportExportSection`

Bulk operations:
- **Import** — Upload CSV pacientes / treatments / doctors (mapping fields · dry-run preview · audit log)
- **Export** — Full tenant data dump (paths · async background job → S3 download link · TTL 7d)

NO PHI en export sin re-auth.

### § 8 — `DangerZoneSection` (★ multi-step)

Acciones destructivas:
- **Reset tenant data** — Borra todos los datos brand pero mantiene tenant config (confirm "reset" type-text + email confirm + cool-off 24h)
- **Cancel subscription** — Cancela Plan Luana (managed Stripe · cool-off 30d con downgrade gradual)
- **Delete tenant** — Full delete (multi-step: type-text + email confirm + cool-off 30d + admin approval Luana)

Audit log per acción + Sentry alert + Luana ops notification.

### § 9 — Mobile

Todas accordion vertical.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 7 sub-secciones |
| AC-2 | Raw audit log table filterable + export CSV |
| AC-3 | LLM keys BYO masked + reveal con re-auth + test conn |
| AC-4 | Feature flags toggle + audit + side-effect validation |
| AC-5 | API tokens generate + revoke + webhook subscribe |
| AC-6 | Import CSV dry-run preview + audit |
| AC-7 | Export full data async + S3 link TTL |
| AC-8 | Danger zone multi-step confirm + cool-off + audit |
| AC-9 | Visual goldens × 14 (7 sub-sections × 2 themes) |
| AC-10 | a11y axe pass |
| AC-11 | Cross-tenant + RBAC (admin_clinic only) |
| AC-12 | PHI fields sanitize en raw audit + import / export |
| AC-13 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: feature flag flip + validate side-effect

**Given:** Flag `realtime_websocket=false` actual

**When:**
1. Toggle ON
2. Submit

**Then:**
- Backend valida side-effect (per `anti-default-flip-audit.md` Step 1 grep tests)
- Si side-effect OK → persist + audit log + WebSocket subscriber activates
- UI confirm + side-effect status visible

### Scenario 2 — adversarial: reset tenant sin permission

Role staff intenta DELETE `/api/avanzado/reset` → 403 · audit · Sentry.

### Scenario 3 — edge: LLM key inválido test conn

**Given:** User pega key Anthropic inválida

**When:** Test connection click

**Then:** Backend test call fail → UI muestra error + sugerencia + NO persist key.

### Scenario 4 — danger zone delete tenant

**Given:** Admin_clinic role · type "DELETE" en confirm input · click

**When:** Submit

**Then:**
- Email confirmation enviado a admin · cool-off 30d active
- UI muestra "Eliminación programada · 30d cool-off · 'Cancelar eliminación' visible"
- Audit + Luana ops notification
- Si admin no cancela en 30d → cron `tenant_deletion_executor` borra · audit final

### Scenario 5 — keyboard-a11y

Tab tabs + forms + dangerous actions require explicit focus + confirm.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/avanzado/page.tsx` | MODIFY |
| `vitalia/frontend/src/features/config/components/avanzado/ConfigAvanzadoView.tsx` | NEW |
| `vitalia/frontend/src/features/config/components/avanzado/sections/{ReglasPoliticas,RawAuditLog,LLMKeysBYO,FeatureFlags,APITokensWebhooks,ImportExport,DangerZone}Section.tsx` | NEW (7 files) |
| `vitalia/frontend/src/features/config/components/avanzado/DangerZoneConfirmModal.tsx` | NEW (★ multi-step) |
| `vitalia/frontend/src/features/config/api/avanzado.ts` | NEW |
| `vitalia/frontend/src/features/config/types/avanzado.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/avanzado_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/raw_audit_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/llm_keys_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/feature_flags_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/api_tokens_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/import_export_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/api/danger_zone_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/application/feature_flags_validator.py` | NEW (consume anti-default-flip rule) |
| `vitalia/backend/src/modules/vitalia/admin/application/import_csv_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/admin/application/export_data_worker.py` | NEW (async S3) |
| `vitalia/backend/src/modules/vitalia/admin/application/tenant_deletion_executor.py` | NEW (cron post cool-off) |
| `vitalia/backend/src/modules/vitalia/admin/persistence/migrations/XXXX_admin_advanced.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/config-avanzado-danger-zone.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/config-avanzado-feature-flags.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/avanzado/{section}-{light\|dark}.png` (×14) | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_feature_flag_side_effect.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_danger_zone_cool_off.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_raw_audit_phi_sanitize.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_export_no_phi_unauth.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_llm_key_encrypted.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/admin/test_avanzado_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| `core/luana-core-observability` audit_log | Raw audit table | CONSUME read-only |
| `core/luana-core-llm` | LLM router config | EXTEND para BYO keys override |
| F2-S10 lisa-compliance retention service | Retention config | CONSUME |
| `core/luana-core-events` | DomainEvent bus | EMIT FeatureFlagFlipped · TenantDeletionScheduled |
| Vitalia shipped — Clerk auth | Re-auth flow for reveal secrets | REUSE |
| Shadcn primitives | `Tabs` · `Form` · `Table` · `Dialog` · `Alert` · `Switch` · `Textarea` | reuse |
| `anti-default-flip-audit.md` rule | Side-effect validation | APPLY backend |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lisa-compliance` — raw audit cross-link

### Esta historia desbloquea
- ninguna directa (es endpoint admin · uso 1-2x/mes)

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Delete tenant sin cool-off → data loss | Baja | Crítico | Multi-step + email confirm + cool-off 30d + admin approval |
| Feature flag flip rompe production silenciosamente | Media | Alto | anti-default-flip-audit.md enforce (Step 1 grep tests) |
| BYO LLM keys leak en logs | Baja | Crítico | pgcrypto + sanitize_payload + arch test no log llm_key |
| Import CSV malformed corrupts data | Media | Alto | Dry-run preview + transaction rollback + audit |
| Export PHI sin re-auth | Baja | Crítico | Re-auth required + audit + S3 link TTL |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 14
3. Backend tests danger-zone + feature-flag + audit-sanitize + export-phi-protection + llm-key-encrypted pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `config.avanzado` registrada

## Próximo paso post-done

- Story future: marketplace integrations 3rd party
- Story future: webhooks bidireccional (incoming + outgoing)

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § config.avanzado (7 secciones)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **anti-default-flip-audit:** `.claude/rules/anti-default-flip-audit.md`
- **Engine compliance:** `core/luana-core-compliance`
