---
story_id: vitalia-fase2-lisa-marca
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
module: brand_studio
capability_target: brand_studio/lisa-marca
agent_owner: lisa
arch_version: 1
schema_version: v4.1
last_modified: 2026-05-27
generated_by: /architect (Opus 4.7 single-shot full-stack)
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
hipaa_lite_overlay: true
uses_n3_static: true
agent_subsubtabs_entry: "lisa.marca = ['identidad', 'voz-y-tono', 'presencia']"
service_deps_status: {}
mockups_ratified: 3/3                     # 2026-05-27 iter v2.1 ratified
---

# F2-S7 vitalia-fase2-lisa-marca — 03-arch CONSOLIDADO

> Single-file architecture (BE + FE + cross-cutting). Architect run on **2026-05-27** via Opus 4.7 single-shot full-stack. **No agentic surface** — Lisa.marca es sub-tab UI administrativa que **consume** el sales-agent compiler v2 como CLIENT (endpoint `/lisa/marca/voice-preview` invoca el slot compiler), pero NO modifica engine ni LangGraph runtime.
>
> Story type: `ui-story` mixed (BE brand-extension NEW módulo `brand_studio` + FE feature root NEW `features/lisa`). N3-static SubSubTabsBar cementado (ADR-vitalia-004 v1.1 § 3.1.1).

---

## § 0 — Context Summary

### 0.1 Surface → builder → auditor mapping (★ /dev-team spawn dispatcher)

| Surface | Paths primarios | Builder | Auditor | Owner pool |
|---|---|---|---|---|
| **BE — brand_studio brand-extension** (NEW módulo) | `vitalia/backend/src/modules/vitalia/brand_studio/{domain,infrastructure,application,api,persistence}/` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | `[qwen-opencode, claude-sonnet, claude-opus]` |
| **BE — telemetry emitter EXTEND** | `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` (shipped F2-S1 — reuse) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | idem |
| **FE — feature root `features/lisa`** (NEW) | `vitalia/frontend/src/features/lisa/{components,api,hooks,store,types}/` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **FE — N3-static routing** (NEW) | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/{page.tsx,identidad,voz-y-tono,presencia}/page.tsx` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **FE — SubSubTabsBar component + AGENT_SUBSUBTABS catalog** (NEW per ADR-004 v1.1 § 3.1.2/3.1.3) | `vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx` + `vitalia/frontend/src/lib/routing/shell-routes.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **FE — Shadcn primitives install** | `vitalia/frontend/src/components/ui/{label,radio-group,checkbox,switch,sheet}.tsx` (NEW si faltan) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **Tests E2E Playwright** | `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/*.spec.ts` + `e2e/__screenshots__/lisa-marca/*.png` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **BE tests** | `vitalia/backend/tests/modules/vitalia/brand_studio/*.py` + `tests/architecture/*.py` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | idem |

**NO agentic surface.** Cero tickets `surface=AGENTIC`. Endpoint `/lisa/marca/voice-preview` consume `core/luana-core-sales-agent/.../compose.py::PromptFragment.BRAND_VOICE` como **biblioteca pura** (compile sin LLM call). No persiste estado conversational, no toca LangGraph, no toca personality_profile runtime.

### 0.2 Skills consultadas (architect orchestrator)

| Skill | Decisión tomada | Anchor en CONTRACT |
|---|---|---|
| `backend-expert` | DDD Inside-Out + `Repository` base normal (NO PHI en esta story — owner config) + raw-SQL idempotent migration + audit_log SÍ aplica (defense-in-depth) | § 2, § 3, § 5, § 9 |
| `brand-expert` | PersonalityProfile compiler v2 SSoT cementado — UI edita `system_instruction` 6 bloques directo; 4 archetypes salud-friendly (Caregiver default / Sage / Healer / Hero); NO mirror `brand_voice_summary` (anti-creep); soft warning client via tabla configurable | § 2, § 7, § 12 D2 |
| `sales-agent-expert` | Slot 5 BRAND_VOICE compiler v2 lectura SSoT `personality_profiles.system_instruction`; voice-preview server endpoint compila slot sin LLM call (deterministic); cache server por `(personality_profile_id, version)` evita re-compile | § 5, § 7.2, § 8.6 |
| `frontend-expert` | FSD-Lite `features/lisa/components/marca/{identidad,voz-y-tono,presencia}/` + Server Components per subsubtab + React Query + RHF/Zod + autosave 600ms | § 6 |
| `playwright-expert` | POMs por sub-sub-tab + 11 scenarios mandatory + visual goldens 6 PNGs (3×2 themes) + axe a11y | § 11 Test Construction Plan |
| `metrics-expert` | `vitalia_growth_studio_event` brand-local emitter (shipped F2-S1) — extend con 13 eventos `lisa_marca_*` PHI-safe bucketed | § 10 |
| HIPAA-lite overlay | Story toca owner config (NO PHI directo). Dual filter NO aplica (config a nivel tenant, no clinic). Audit log SÍ aplica defense-in-depth (todas mutaciones marca). PHI sanitization en traces SÍ (regla universal). | Cross-cutting § 8 |
| `.claude/rules/anti-duplication.md` | NEW brand-extension `brand_studio/` consumiendo engine `core/luana-core-brand-studio` READ-ONLY via API — NO mirror. Nicolify schemas IMPORT verbatim (shared pattern post brand-studio shipped multi-brand) — NO mirror cross-brand backend, solo FE schemas Zod. | § 1 Existing Systems Audit |
| `.claude/rules/sales-agent-brand-voice.md` | Anti-creep cardinal: NO crear `brand_voice_summary`, NO fine-tuning per tenant, NO voice-rewriter LLM, NO inyectar `{tenant_name}` mid-block. UI edita SSoT inalterable `personality_profiles.system_instruction`. `vitalia_prohibited_phrases` tabla = soft warning configurable (no bloqueo) — NO regla cardinal LLM compile. | § Voice architecture |
| `tessl__fastapi` | `redirect_slashes=False` ya shipped en `main.py` vitalia. `response_model=` en cada endpoint nuevo. PATCH endpoints partial-update con Pydantic v2 `model_config = ConfigDict(extra="forbid")`. | § 4, § 5 |
| `tessl__pytest-api-testing` | AsyncSession fixtures + dual-tenant test pattern (cross-tenant 403) + AsyncAuditWriter mock | § 11 |
| `tessl__react-patterns` | Server components per subsubtab page con `getInitialMarcaState({tenantId, subsubtab})` SSR + `'use client'` solo en `{Identidad,VozTono,Presencia}View.tsx` | § 6 |
| `tessl__shadcn-ui` | `npx shadcn@latest add label radio-group checkbox switch sheet` batch (los que faltan verificar pre-install) | § 6.1 |
| `tessl__zod` | Schemas IMPORT verbatim de nicolify + ADAPT salud overlay (default archetype Caregiver, omit Outlaw/Magician/Lover/Innocent) | § 7.4 |
| `tessl__tailwind` | Tokens semánticos `var(--agent-lisa)`, `var(--primary)`, `var(--destructive)` — NO hex literals | § 6 |
| `tessl__vitest` | Unit tests co-located por componente + hooks + form validators | § 11.2 |
| `tessl__nextjs-app-router-modularization` | N3-static routing — `[subtab]/page.tsx` redirect a primer subsubtab; `[subtab]/[subsubtab]/page.tsx` Server Components | § 6.0 |

### 0.3 CONTEXT-BRIEF source

Direct reads (no `CONTEXT-BRIEF.md` produced by context-builder Haiku). Self-ran greps Path B per `.claude/rules/anti-duplication.md`. Audit detail en § 1 Existing Systems Audit. Source-story `vitalia-fase2-valeria-agenda/03-arch.md` consultado verbatim como ADR-vitalia-004 origin.

### 0.4 capability YAML files affected (post-merge mandatory)

- **NEW:** `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` (capability `brand_studio/lisa-marca` promoción post-done)
- **NEW:** `vitalia/docs/product/modules/brand_studio.md` (módulo brand-local NEW — auto-list regen via `scripts/reconcile_capabilities.py --brand vitalia`)
- **MODIFY (auto):** `vitalia/docs/product/BACKLOG.md` (gitignored — regen via `scripts/generate_backlog.py --brand vitalia`)

### 0.5 Architecture fitness gates (que deben mantenerse GREEN)

| Test | Path | Modificación |
|---|---|---|
| `test_phi_dual_filter.py` | `vitalia/backend/tests/architecture/` | sin cambio (esta story NO PHI directo; repos heredan `Repository` base normal, NO `PhiRepositoryBase`) |
| `test_audit_log_sync_write.py` | `vitalia/backend/tests/architecture/` | EXTEND (cada mutación brand_studio escribe audit_log row pre-response defense-in-depth) |
| `test_response_model_required.py` | `vitalia/backend/tests/architecture/` | sin cambio (nuevos endpoints mandatory cumplen) |
| `test_growth_studio_event_no_phi.py` | `vitalia/backend/tests/architecture/` | EXTEND (13 nuevos eventos `lisa_marca_*` se agregan al whitelist sin contener PHI) |
| `test_no_health_voice_validator.py` | `vitalia/backend/tests/architecture/` (★ NEW) | NEW arch test creep guard — bloquea creación accidental de `health_voice_validator.py` per `.claude/rules/sales-agent-brand-voice.md` |
| `test_no_brand_voice_summary_table.py` | `vitalia/backend/tests/architecture/` (★ NEW si no existe nicolify version) | NEW (o EXTEND existing si nicolify ya tiene) — bloquea tabla mirror `brand_voice_summary` |
| `test_brand_studio_module_ddd.py` | `vitalia/backend/tests/architecture/` (★ NEW) | NEW arch test — enforces DDD boundaries en módulo brand_studio brand-extension |
| `test_features_no_cross_imports.test.ts` | `vitalia/frontend/src/__tests__/architecture/` | sin cambio (`features/lisa` no importa de `features/{valeria,adrian,...}`) |
| `test_react_query_keys_convention.test.ts` | `vitalia/frontend/src/__tests__/architecture/` | sin cambio (keys siguen `[module, subtab, subsubtab, action, ...]`) |
| `test_no_phi_in_url_params.test.ts` | `vitalia/frontend/src/__tests__/architecture/` | sin cambio (lisa-marca SOLO `[subsubtab]` static segment + body params en PATCH) |

Allowlists shrink-only: módulo `brand_studio` se agrega de cero (no expande allowlist legacy).

---

## § 1 — Existing Systems Audit (NO NEW LAYER rule)

### 1.1 Source of evidence

- [x] Self-run greps (Path B — fallback, sin `CONTEXT-BRIEF.md`)
- [ ] CONTEXT-BRIEF § 7 + § 8 (no producido para esta story)

### 1.2 Greps ejecutados

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Engine brand-studio — qué existe shipped (read-only)
find ${WS}/core/luana-core-brand-studio/src -type d
# → domain/ (identity, personality, team, section_catalog) + infrastructure/ (repos) + application/ + api/ + copilot_provider/ + workers/

# 2. Vitalia brand backend — qué módulos ya existen vs NEW brand_studio
ls ${WS}/vitalia/backend/src/modules/vitalia/
# → admin agentic api application audit clinics compliance connections copilot crm fidelizacion fiscal iam inbox infrastructure marketing payment payments persistence sales_agent scheduling _shared
# → NO brand_studio/ → NEW módulo brand-extension

# 3. Audit writer
cat ${WS}/vitalia/backend/src/modules/vitalia/audit/audit_writer.py
# → AsyncAuditWriter + write_audit_log_sync ya shipped — REUSE

# 4. Telemetry emitter
ls ${WS}/vitalia/backend/src/modules/vitalia/_shared/telemetry/
# → growth_studio_emitter.py + amount_bucket.py ya shipped F2-S1 — REUSE (extend with 13 new events)

# 5. Engine sales-agent compiler v2
find ${WS}/core/luana-core-sales-agent/src -name "compose.py"
# → application/prompts/compose.py::PromptFragment.BRAND_VOICE — consume via import (compile-only, NO LLM)

# 6. Nicolify schemas (shared pattern post brand-studio shipped multi-brand)
ls ${WS}/nicolify/frontend/src/features/brand-studio/schemas/
# → identity, contact, visuals, personality, team, testimonial-item, positioning, narrative, story, strategy, methodology, buyer-persona, authority-item, legal, communication-assets, avatars, logos
# → IMPORT verbatim FE only: identity, contact, visuals, personality (ADAPT), team (read-only), testimonial-item (vital trust-signals)

# 7. Cross-brand mirror check (HARD ban)
for B in nicolify comunify lupulo; do
  grep -rln "vitalia_prohibited_phrases\|lisa_marca" ${WS}/$B/backend/src/ 2>/dev/null | head -3
done
# → zero match — NEW vitalia-specific table

# 8. health_voice_validator scan (creep guard — should be 0 matches per anti-creep rule)
grep -rn "health_voice_validator" ${WS}/ 2>/dev/null
# → zero match. NEW arch test `test_no_health_voice_validator.py` prevents future regression.

# 9. brand_voice_summary table mirror check (anti-creep rule cardinal)
grep -rn "brand_voice_summary" ${WS}/ 2>/dev/null
# → zero match (per nicolify test_brand_voice_no_summary_table.py shipped). Extend o create equivalente vitalia.

# 10. Visual extraction pipeline (depends /pm-luana proposal)
cat ${WS}/docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md 2>/dev/null | head -5
# → state: proposed (NOT accepted). Story ships con stub + botón disabled. Re-evaluar cuando state=accepted.
```

### 1.3 Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Engine `BrandIdentity` aggregate + repo | `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/identity.py` + `infrastructure/repositories/brand_identity_repository.py` | shipped | **CONSUME via engine API** — `vitalia.brand_studio.application.marca_service.MarcaService.get_identity()` instancia `BrandIdentityRepository` engine y filtra `tenant_id` brand-local |
| Engine `PersonalityProfile` aggregate + compiler v2 | `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py` + `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py::PromptFragment.BRAND_VOICE` | shipped | **CONSUME via engine API + library** — `MarcaService.get_personality()` consume repo; voice-preview compila slot 5 BRAND_VOICE via `compose.py` import (deterministic, no LLM) |
| Engine `BrandIdentity` API thin | `core/luana-core-brand-studio/src/luana_core_brand_studio/api/identity.py` | shipped | **NO usar directo** — vitalia expone wrapper `/api/v1/lisa/marca/identity` (audit log + tenant validation + DTO masking) |
| Engine `Team` aggregate | `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/team.py` | shipped | **CONSUME read-only** — preview "Equipo destacado" en sub-sub-tab Identidad consume top 3 via API (CRUD vive en `lisa-doctores` story futura) |
| Engine `BrandVisuals` aggregate | `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/identity.py` (sub-aggregate) | shipped | **CONSUME via engine** — wrapper `/api/v1/lisa/marca/visuals` permite update colores/tipografía/logo |
| Engine `BrandContact` aggregate | `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/team.py` (BrandContact dataclass) | shipped | **CONSUME via engine** — wrapper `/api/v1/lisa/marca/contact` permite update social_media + URLs |
| Vitalia `audit/audit_writer.py` | `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | shipped | **REUSE** — cada mutación brand_studio escribe `vitalia_audit_log` row via `AsyncAuditWriter` |
| Vitalia `_shared/telemetry/growth_studio_emitter.py` | `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | shipped F2-S1 | **REUSE + EXTEND** — 13 nuevos events `lisa_marca_*` agregados al whitelist `_KNOWN_EVENT_NAMES`. NO crear tabla nueva. |
| Vitalia `_shared/telemetry/amount_bucket.py` | idem | shipped F2-S1 | N/A (story brand config, no monetary amounts) |
| Engine `sanitize_payload` | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | shipped | **REUSE** — audit_log + telemetry events pasan por sanitize_payload(`compliance_level='hipaa_lite'`) defense-in-depth |
| Engine `ComplianceService` | `core/luana-core-compliance/` | shipped | **NO usar esta story** — lisa-marca no envía mensajes outbound. Pertenece a sales_agent surface. |
| Nicolify FE schemas Zod | `nicolify/frontend/src/features/brand-studio/schemas/{identity,contact,visuals,personality,team,testimonial-item}.schema.ts` | shipped | **IMPORT verbatim** → `vitalia/frontend/src/features/lisa/types/marca/{identity,contact,visuals,personality,team,testimonial-item}-schema.ts` con ADAPT salud overlay (default Caregiver + omit Outlaw/Magician/Lover/Innocent). NO IMPORT BE — Zod schemas son FE shared pattern, no cross-brand BE import. |
| Nicolify schemas omit | positioning, narrative, story, strategy, methodology, buyer-persona, authority-item, legal, communication-assets, avatars, logos | shipped nicolify | **NO IMPORT** — vitalia/config/brand.yaml::brand_studio.enabled_sections = [identity, contact, visuals, personality, team, testimonials, presence, trust_signals]. Simplificado salud overlay. |
| `vitalia_prohibited_phrases` table | NO existe | greenfield | **NEW brand-local migration** + seed defaults salud per país (PE primero) per OQ-D |
| `health_voice_validator.py` | NO existe (creep guard) | n/a | **NEVER CREATE** (anti-creep rule). Arch test `test_no_health_voice_validator.py` enforces |
| `brand_voice_summary` mirror table | NO existe (anti-creep cardinal) | n/a | **NEVER CREATE**. Arch test `test_no_brand_voice_summary_table.py` enforces |
| Visual extraction pipeline runtime | NO existe (depends /pm-luana proposal 2026-05-26) | proposed | **STUB local + botón disabled** con tooltip "Próximamente" hasta state=accepted. Re-evaluar story futura |
| Cross-brand mirror nicolify/comunify/lupulo `brand_studio` extension | n/a (brand_studio BE extension brand-local pattern — cada brand puede tener su overlay) | zero match | OK. Si nicolify replica `vitalia/brand_studio/api/marca_router.py` exact pattern → lift `/pm-luana` candidate (NOT blocker F2-S7) |

### 1.4 Decisión por sistema (EXTEND > REPLACE > NEW)

- **Engine `BrandIdentity` + `PersonalityProfile` + `Team` + `BrandVisuals` + `BrandContact`** → **CONSUME via engine API repos + library compose** (read-only). Brand-local `MarcaService` instancia engine repositories pasando `tenant_id`. NO mirror engine, NO modify engine. Engine modify requiere `/pm-luana` promotion proposal (out-of-scope F2-S7).
- **Sales-agent compiler v2 `PromptFragment.BRAND_VOICE`** → **CONSUME via library import** (`from luana_core_sales_agent.application.prompts.compose import PromptFragment, compose_brand_voice_preview`). Compile-only path (no LLM dispatch). Voice-preview endpoint compila slot 5 deterministic.
- **`vitalia_prohibited_phrases`** → **NEW brand-local table** + idempotent migration + seed defaults salud PE. Configurable per tenant (default seed + tenant overrides via UI futura — esta story NO expone CRUD, solo edit defaults via admin Streamlit existente). Justificación: regla `sales-agent-brand-voice.md` permite soft warning configurable, NO LLM validator.
- **`growth_studio_emitter`** → **EXTEND** — agregar 13 nuevos `event_name` al whitelist + arch test EXTEND. NO crear nueva tabla; `vitalia_growth_studio_event` ya shipped F2-S1.
- **Audit writer** → **REUSE 100%** — agregar nuevas `action` values en string enum (`brand_identity_updated`, `brand_visuals_updated`, `brand_personality_updated`, `brand_contact_updated`, `voice_warning_overridden`, `cross_tenant_brand_edit_attempt`, `voice_preview_compiled`). Schema sin cambios.
- **Nicolify FE schemas** → **IMPORT verbatim FE only** + ADAPT salud overlay (default archetype Caregiver, omit 4 archetypes problemáticos). FE shared pattern documentado en `.claude/rules/anti-duplication.md` § "Cross-brand mirror ban" — los schemas Zod son contratos de UI consumiendo el mismo engine, NO duplicación de lógica de negocio.
- **Cross-brand mirror BE** → **N/A** (zero match). Si futuro nicolify replica exact patrón `brand_studio` brand-extension → escalate `/pm-luana` para lift `core/luana-core-brand-studio-overlay/` (NOT blocker F2-S7).

**Engine boundary respect:** zero edits a `core/luana-core-*/src/`. Si scope requiere engine modify → escalate `/pm-luana` promotion proposal explícita (out-of-scope F2-S7).

---

## § 2 — Domain Entities (BE)

### 2.1 Brand-local domain entities NEW

`vitalia/backend/src/modules/vitalia/brand_studio/domain/`

```python
# prohibited_phrase.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ProhibitedPhraseSeverity(StrEnum):
    """Severity bucket for soft warning UI hint."""
    LOW = "low"        # estilo (e.g., "rapidísimo")
    MEDIUM = "medium"  # potencial regulatory (e.g., "tratamiento milagroso")
    HIGH = "high"      # regulación clara (e.g., "curamos", "garantizado")


@dataclass
class ProhibitedPhrase:
    """Vitalia-specific configurable phrase blocklist for soft warning UI.

    Brand-local. NO bloquea persistencia. UI muestra warning + suggested_alternative + permite override
    con audit_log row `voice_warning_overridden`. Defense-in-depth per `.claude/rules/sales-agent-brand-voice.md`
    anti-creep: NO crear LLM validator, NO crear brand_voice_summary mirror.
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID | None = None                  # NULL = seed default (cross-tenant); UUID = tenant override
    phrase: str = ""                                # lowercase normalized
    suggested_alternative: str = ""                 # microcopy de sugerencia
    severity: str = ProhibitedPhraseSeverity.MEDIUM.value
    country_scope: str | None = None                # ISO 3166-1 alpha-2 (PE/AR/CL/CO/MX/BR) — None = global
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
```

```python
# archetype.py (salud overlay)
from enum import StrEnum


class SaludArchetype(StrEnum):
    """4 Jung archetypes salud-friendly (OQ-B resolution 2026-05-27).

    Omit Outlaw/Magician/Lover/Innocent (problematic tone para health context).
    Default: CAREGIVER.
    """
    CAREGIVER = "caregiver"   # default — calidez, cuidado, prioriza paciente
    SAGE = "sage"              # expertise, datos, educativo
    HEALER = "healer"          # tono empático, sanación, proceso restaurador
    HERO = "hero"              # transformación, superación, inspirador
```

```python
# voice_preview.py
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VoicePreview:
    """Compiled BRAND_VOICE slot 5 sample (deterministic, no LLM dispatch).

    Generated by VoicePreviewService consuming PromptFragment.BRAND_VOICE compose function
    of core/luana-core-sales-agent. Output is a textual sample shown in UI footer of sub-sub-tab Voz.
    """
    personality_profile_id: str        # opaque hash hex (for cache key)
    sample_whatsapp: str               # canal WhatsApp short greeting
    sample_email_reactivation: str     # canal email longer reactivation
    compiled_at: datetime
    compiler_version: str              # v2 cementado sales-agent
```

### 2.2 No PHI dataclasses

Esta story NO toca PHI (paciente, appointment, medical_record). Es **owner configuration** sobre la marca/identidad tenant-wide. Repositories heredan `Repository` base normal — NO `PhiRepositoryBase`, NO `validate_dual_filter(clinic_id=...)`.

**Defense-in-depth aplica igual:**
- `audit_log` sync write antes response (regla universal vitalia).
- `sanitize_payload(compliance_level='hipaa_lite')` en telemetry events.
- `tenant_id` filter en cada query (tenant_isolation universal raíz).
- `vitalia_growth_studio_event.props` sin contener PII/PHI (whitelist test `test_growth_studio_event_no_phi.py`).

---

## § 3 — SQLAlchemy 2.0 Models

### 3.1 `vitalia_prohibited_phrases` (brand-local NEW)

`vitalia/backend/src/modules/vitalia/brand_studio/persistence/models/prohibited_phrase_model.py`

```python
from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class VitaliaProhibitedPhraseModel(Base):
    """SA 2.0 model — vitalia brand-local prohibited phrases table.

    tenant_id NULL → seed default (cross-tenant baseline). UUID → tenant override.
    NO PHI; safe for full text indexing.
    """

    __tablename__ = "vitalia_prohibited_phrases"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True, index=True)
    phrase: Mapped[str] = mapped_column(String(200), nullable=False)
    suggested_alternative: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    country_scope: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

Composite indexes via migration:
- `idx_vit_phrase_tenant_severity` `(tenant_id, severity) WHERE deleted_at IS NULL` — fetch tenant overrides
- `idx_vit_phrase_country_severity` `(country_scope, severity) WHERE deleted_at IS NULL AND tenant_id IS NULL` — fetch seed defaults per country
- `idx_vit_phrase_lookup` `(phrase) WHERE deleted_at IS NULL` — fast substring lookup en FE warning detection

### 3.2 NO modify engine tables

Engine `personality_profiles`, `brand_identities`, `brand_visuals`, `brand_contacts`, `brand_teams` viven en `core/luana-core-brand-studio` shipped. Esta story **NO modifica schema engine**. Solo CONSUME via engine repositories en `MarcaService`.

### 3.3 No nuevas tabla observability

`vitalia_growth_studio_event` ya shipped F2-S1. Solo se agregan 13 nuevos `event_name` values en whitelist.

---

## § 4 — Pydantic v2 DTOs

### 4.1 Identity DTOs (sub-sub-tab Identidad)

`vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py`

```python
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrandIdentityDTO(BaseModel):
    """GET /lisa/marca/identity response."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    name: str
    slug: str                         # read-only (lectura desde tenant.subdomain)
    tagline: str | None
    clinic_vertical: str              # read-only — capturado en onboarding-clinica
    primary_specialties: list[str]    # read-only — idem
    updated_at: datetime | None


class BrandIdentityPatchDTO(BaseModel):
    """PATCH /lisa/marca/identity request — partial update."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=2, max_length=100)
    tagline: str | None = Field(None, max_length=150)


class BrandVisualsDTO(BaseModel):
    """GET /lisa/marca/visuals response."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    primary_color: str | None         # hex "#RRGGBB"
    accent_color: str | None
    background_color: str | None
    text_primary_color: str | None
    font_heading: str | None
    font_body: str | None
    logo_url: str | None
    updated_at: datetime | None


class BrandVisualsPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text_primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    font_heading: str | None = Field(None, max_length=64)
    font_body: str | None = Field(None, max_length=64)


class LogoUploadResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    logo_id: UUID
    logo_url: str
    size_bytes: int
    format: Literal["png", "jpg", "jpeg", "webp"]
```

### 4.2 Personality + Voice DTOs (sub-sub-tab Voz)

```python
class BrandPersonalityDTO(BaseModel):
    """GET /lisa/marca/personality response."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    personality_profile_id: UUID
    archetype: Literal["caregiver", "sage", "healer", "hero"]
    so_i_speak: str                   # block "ASÍ HABLO" (compiler v2 block 3)
    so_i_dont_speak: str              # block "ASÍ NO HABLO" (compiler v2 block 4)
    technical_context: str            # block 5
    format_instructions: str          # block 6
    identity_anchor: str              # block 1 (read-only? — TBD policy; default editable)
    domain_context: str               # block 2 (idem)
    compiled_at: datetime | None
    compiler_version: str


class BrandPersonalityPatchDTO(BaseModel):
    """PATCH /lisa/marca/personality — partial update of compiler v2 6 blocks."""
    model_config = ConfigDict(extra="forbid")

    archetype: Literal["caregiver", "sage", "healer", "hero"] | None = None
    so_i_speak: str | None = Field(None, max_length=4000)
    so_i_dont_speak: str | None = Field(None, max_length=4000)
    technical_context: str | None = Field(None, max_length=2000)
    format_instructions: str | None = Field(None, max_length=2000)
    identity_anchor: str | None = Field(None, max_length=2000)
    domain_context: str | None = Field(None, max_length=2000)


class ProhibitedPhraseDTO(BaseModel):
    """GET /lisa/marca/prohibited-phrases response item."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    phrase: str
    suggested_alternative: str
    severity: Literal["low", "medium", "high"]
    country_scope: str | None
    is_seed: bool                     # tenant_id IS NULL → True


class ProhibitedPhrasesListDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[ProhibitedPhraseDTO]
    total: int


class VoiceWarningOverrideRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phrase_id: UUID                   # which prohibited phrase was triggered
    section: Literal["so_i_speak", "so_i_dont_speak"]
    user_text_excerpt: str = Field(..., max_length=500)  # NO PHI (microcopy fragment user typed)


class VoicePreviewDTO(BaseModel):
    """GET /lisa/marca/voice-preview response."""
    model_config = ConfigDict(from_attributes=True)

    personality_profile_id: UUID
    sample_whatsapp: str              # short greeting "Hola, soy Valeria. Acompañamos tu tratamiento..."
    sample_email_reactivation: str    # longer email body
    compiled_at: datetime
    compiler_version: str
    cache_hit: bool                   # debug indicator (server cache by hash)
```

### 4.3 Contact + Presence + Trust DTOs (sub-sub-tab Presencia)

```python
class BrandContactDTO(BaseModel):
    """GET /lisa/marca/contact response."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    public_landing_url: str | None    # read-only — auto-generated from tenant.subdomain
    website_url: str | None
    instagram_handle: str | None
    tiktok_handle: str | None
    facebook_page: str | None
    google_business_url: str | None
    updated_at: datetime | None


class BrandContactPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    website_url: str | None = Field(None, max_length=300)
    instagram_handle: str | None = Field(None, max_length=64)
    tiktok_handle: str | None = Field(None, max_length=64)
    facebook_page: str | None = Field(None, max_length=128)
    google_business_url: str | None = Field(None, max_length=300)


class TrustSignalDTO(BaseModel):
    """Certificación/autoridad listed via hybrid catalog (OQ-D resolution)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    label: str                        # "DIGESA" o free-text "Otra"
    catalog_code: str | None          # NULL si free-text
    logo_url: str | None
    issued_year: int | None
    is_seed: bool


class TrustSignalsCatalogDTO(BaseModel):
    """Hybrid catalog per country — OQ-D resolution 2026-05-27."""
    model_config = ConfigDict(from_attributes=True)
    country: str                      # ISO 3166-1 alpha-2
    items: list[dict[str, str]]       # [{code, label, hint}]


class TrustSignalCreateRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(..., min_length=2, max_length=128)
    catalog_code: str | None = Field(None, max_length=64)
    issued_year: int | None = Field(None, ge=1900, le=2100)


class BrandTeamPreviewDTO(BaseModel):
    """Read-only top-N team preview consumed in sub-sub-tab Identidad."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    total_count: int
    preview_count: int                # min(total_count, 3)
    members: list["TeamMemberPreviewItemDTO"]


class TeamMemberPreviewItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: UUID
    display_name: str                 # "Dr. Pérez" — no PHI (staff label, not patient)
    role: str                         # "Odontólogo"
    avatar_url: str | None


class ClinicConfigDTO(BaseModel):
    """Read-only display of clinic_vertical + primary_specialties (capturado en onboarding-clinica)."""
    model_config = ConfigDict(from_attributes=True)
    tenant_id: UUID
    clinic_vertical: str              # "dental_clinic" | "psychology_clinic" | ...
    primary_specialties: list[str]    # ["Odontología general", ...]
```

### 4.4 Initial state DTO (SSR consumption per subsubtab)

```python
class MarcaInitialStateDTO(BaseModel):
    """SSR initial state per subsubtab — Server Component fetches and hydrates React Query cache."""
    model_config = ConfigDict(from_attributes=True)

    subsubtab: Literal["identidad", "voz-y-tono", "presencia"]
    identity: BrandIdentityDTO | None
    visuals: BrandVisualsDTO | None
    personality: BrandPersonalityDTO | None
    contact: BrandContactDTO | None
    team_preview: BrandTeamPreviewDTO | None
    clinic_config: ClinicConfigDTO | None
    voice_preview: VoicePreviewDTO | None            # only for subsubtab=voz-y-tono
    prohibited_phrases: ProhibitedPhrasesListDTO | None  # idem
    trust_signals: list[TrustSignalDTO] | None
    trust_catalog: TrustSignalsCatalogDTO | None     # only for subsubtab=presencia
```

---

## § 5 — API Routes

All routes under `/api/v1/lisa/marca/...`. `Bearer` (Clerk session) + `X-Tenant-ID` header (middleware-derived). `FastAPI(redirect_slashes=False)` already enforced. **No `clinic_id` filter** — owner-level config (no PHI).

### 5.1 Routes table

| Method | Path | Auth | Request DTO | response_model | RBAC roles | Description |
|---|---|---|---|---|---|---|
| GET | `/api/v1/lisa/marca/initial-state/{subsubtab}` | Bearer + Tenant | — | `MarcaInitialStateDTO` | owner, admin_clinic | SSR initial state per subsubtab |
| GET | `/api/v1/lisa/marca/identity` | idem | — | `BrandIdentityDTO` | idem | Get current identity |
| PATCH | `/api/v1/lisa/marca/identity` | idem | `BrandIdentityPatchDTO` | `BrandIdentityDTO` | owner | Update identity (audit log) |
| GET | `/api/v1/lisa/marca/visuals` | idem | — | `BrandVisualsDTO` | idem | Get visuals |
| PATCH | `/api/v1/lisa/marca/visuals` | idem | `BrandVisualsPatchDTO` | `BrandVisualsDTO` | owner | Update colors/fonts (audit log) |
| POST | `/api/v1/lisa/marca/logos` | idem | multipart `file` | `LogoUploadResponseDTO` | owner | Upload logo (≤ 5 MB validation server + client) |
| DELETE | `/api/v1/lisa/marca/logos/{logo_id}` | idem | — | `204 No Content` | owner | Delete logo |
| GET | `/api/v1/lisa/marca/personality` | idem | — | `BrandPersonalityDTO` | idem | Get personality compiler v2 6 blocks |
| PATCH | `/api/v1/lisa/marca/personality` | idem | `BrandPersonalityPatchDTO` | `BrandPersonalityDTO` | owner | Update personality (audit log + invalidate voice-preview cache) |
| GET | `/api/v1/lisa/marca/contact` | idem | — | `BrandContactDTO` | idem | Get contact + social media |
| PATCH | `/api/v1/lisa/marca/contact` | idem | `BrandContactPatchDTO` | `BrandContactDTO` | owner | Update contact (audit log) |
| GET | `/api/v1/lisa/marca/team-preview?limit=3` | idem | — | `BrandTeamPreviewDTO` | idem | Read-only top-N preview |
| GET | `/api/v1/lisa/marca/clinic-config` | idem | — | `ClinicConfigDTO` | idem | Read-only clinic_vertical + specialties |
| GET | `/api/v1/lisa/marca/voice-preview` | idem | — | `VoicePreviewDTO` | idem | Compile slot 5 BRAND_VOICE preview (cached server-side) |
| GET | `/api/v1/lisa/marca/prohibited-phrases?country=PE` | idem | — | `ProhibitedPhrasesListDTO` | idem | List seed defaults + tenant overrides |
| POST | `/api/v1/lisa/marca/voice-warning-override` | idem | `VoiceWarningOverrideRequestDTO` | `{audit_id: UUID}` | owner | Log override decision (audit row `voice_warning_overridden`) |
| GET | `/api/v1/lisa/marca/trust-signals` | idem | — | `list[TrustSignalDTO]` | idem | List tenant trust signals |
| POST | `/api/v1/lisa/marca/trust-signals` | idem | `TrustSignalCreateRequestDTO` | `TrustSignalDTO` | owner | Add trust signal (audit log) |
| DELETE | `/api/v1/lisa/marca/trust-signals/{id}` | idem | — | `204 No Content` | owner | Soft-delete trust signal |
| GET | `/api/v1/lisa/marca/trust-catalog?country=PE` | idem | — | `TrustSignalsCatalogDTO` | idem | Hybrid catalog per país |

### 5.2 RBAC decorator

```python
# vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py (EXTEND)
ALLOWED_BRAND_OWNER_ROLES = frozenset(["owner", "admin_clinic"])

def require_brand_owner_access(roles: frozenset[str] = ALLOWED_BRAND_OWNER_ROLES):
    """FastAPI dependency: only owner/admin_clinic can mutate brand config."""
    async def _dep(user=Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, detail={"error_code": "BRAND_OWNER_RBAC_DENIED"})
        return user
    return _dep
```

Every PATCH/POST/DELETE route decorated `Depends(require_brand_owner_access())`. GET endpoints allow broader read (consumer Lisa + Valeria + Camila pueden leer brand voice para conversation context).

### 5.3 Voice-preview caching (OQ-C resolution)

Server-side cache (in-process LRU + Redis fallback):
- **Key:** `f"voice_preview:{tenant_id}:{personality_profile_id}:{compiler_version}:{hash(blocks)}"`
- **TTL:** 1 hour (or until next PATCH personality invalidates)
- **Invalidation:** `MarcaService.update_personality()` calls `cache.delete(prefix=f"voice_preview:{tenant_id}:*")` after audit_log write.
- **Cache size cap:** 1000 entries in-process LRU (tenant scale moderate). Redis fallback for cross-instance.

Compile pure-deterministic call: `compose_brand_voice_preview(personality_profile)` → returns 2 strings (whatsapp + email). Zero LLM dispatch. Slot 5 BRAND_VOICE compiler v2 verbatim.

### 5.4 Idempotency

PATCH endpoints son idempotent by design (same payload → same result). No idempotency_key needed. Last-write-wins per Scenario 5 (race_condition).

POST logos + POST trust-signals: server-generated UUID return. Cliente repite → fresh UUID. No dedup natural (file uploads can be intentional re-upload).

POST voice-warning-override: log only (no dedup needed; multiple overrides are valid behavior).

---

## § 6 — Frontend Architecture

### 6.0 Routing (N3-static per ADR-vitalia-004 § 3.1.1)

Folder structure post F2-S7:

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/
├── [agent]/                          # dynamic — unchanged
├── valeria/agenda/                    # static segment shipped F2-S1
├── lisa/                              # ★ NEW static segment
│   └── marca/
│       ├── page.tsx                   # → redirect to /lisa/marca/identidad
│       ├── identidad/page.tsx         # Server Component
│       ├── voz-y-tono/page.tsx        # Server Component
│       └── presencia/page.tsx         # Server Component
└── layout.tsx
```

`lisa/marca/page.tsx` Server Component redirects to first AGENT_SUBSUBTABS entry:

```tsx
// app/[tenantId]/(shell-organism)/lisa/marca/page.tsx
import { redirect } from 'next/navigation'
import { AGENT_SUBSUBTABS } from '@/lib/routing/shell-routes'

interface PageProps {
  params: Promise<{ tenantId: string }>
}

export default async function LisaMarcaIndex({ params }: PageProps) {
  const { tenantId } = await params
  const first = AGENT_SUBSUBTABS.lisa?.marca?.[0] ?? 'identidad'
  redirect(`/${tenantId}/lisa/marca/${first}`)
}
```

Each subsubtab page:

```tsx
// app/[tenantId]/(shell-organism)/lisa/marca/identidad/page.tsx
import { IdentidadView } from '@/features/lisa'
import { getInitialMarcaState } from '@/features/lisa/api/marca-server'

interface PageProps {
  params: Promise<{ tenantId: string }>
}

export default async function IdentidadPage({ params }: PageProps) {
  const { tenantId } = await params
  const initialState = await getInitialMarcaState({ tenantId, subsubtab: 'identidad' })
  return <IdentidadView initialState={initialState} tenantId={tenantId} />
}
```

Same pattern for `voz-y-tono/page.tsx` and `presencia/page.tsx`.

### 6.1 SubSubTabsBar component + AGENT_SUBSUBTABS catalog (ADR-vitalia-004 v1.1 § 3.1.2 + § 3.1.3)

```
vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx     # NEW
vitalia/frontend/src/lib/routing/shell-routes.ts                            # NEW or MODIFY
```

**SubSubTabsBar.tsx:** copy verbatim de `SubTabsBar.tsx` (F1-S8) con ajustes:
- Roving tabindex WAI-ARIA tablist pattern idéntico
- URL-derived active subsubtab: `extractSubsubtabFromPath(pathname)`
- Render condicional: `if (subsubtabs.length === 0) return null`
- Tint color heredada del agente activo (`--agent-{name}`) — consistencia visual

```ts
// lib/routing/shell-routes.ts
export const AGENT_SUBSUBTABS: Partial<Record<AgentKey, Partial<Record<string, readonly string[]>>>> = {
  lisa: {
    marca: ['identidad', 'voz-y-tono', 'presencia'],
  },
} as const

export function extractSubsubtabFromPath(pathname: string): string | null {
  // /tenant-x/lisa/marca/voz-y-tono → "voz-y-tono"
  const parts = pathname.split('/')
  // [empty, tenantId, agent, subtab, subsubtab]
  return parts[4] ?? null
}
```

**ShellOrganismLayout MODIFY:** mounts `<SubSubTabsBar />` between `<SubTabsBar />` and content slot — renders null if no subsubtabs declared for current (agent, subtab).

### 6.2 Shadcn primitives — verify install

Run in `vitalia/frontend/`:

```bash
npx shadcn@latest add label radio-group checkbox switch sheet
```

Primitives target: `vitalia/frontend/src/components/ui/{label,radio-group,checkbox,switch,sheet}.tsx`. **NOTE:** Tabs/Input/Textarea/Button/Alert/Tooltip/Avatar/Badge/Separator/Skeleton/Sonner/Card/Select/Popover/Form/Dialog ya shipped F1/F2-S1 — verify presence, skip install.

### 6.3 FSD-Lite layout

```
vitalia/frontend/src/features/lisa/
├── index.ts                              # public API exports
├── components/
│   └── marca/
│       ├── identidad/                    # nested per subsubtab (ADR-004 § 3.2)
│       │   ├── IdentidadView.tsx              # ★ client root for /lisa/marca/identidad
│       │   ├── IdentityCard.tsx               # form datos básicos (name + tagline)
│       │   ├── ClinicVerticalReadOnly.tsx     # display vertical + specialties + edit-link
│       │   ├── LogoDropZone.tsx               # upload + preview + 5MB validation
│       │   ├── ColorTriadEditor.tsx           # 3 color pickers + hex inputs + contrast warning
│       │   ├── TypographyEditor.tsx           # 2 selects (heading + body fonts)
│       │   ├── TeamPreviewRow.tsx             # avatars row + counter + edit-link
│       │   ├── ExtractFromWebsiteButton.tsx   # disabled stub (D4)
│       │   ├── AutosaveBadge.tsx              # footer "Guardado hace Xs"
│       │   └── __tests__/
│       ├── voz-y-tono/
│       │   ├── VozTonoView.tsx                # ★ client root
│       │   ├── ArchetypeSelector.tsx          # 4 radio cards Caregiver/Sage/Healer/Hero
│       │   ├── VoiceCompilerBlocks.tsx        # 6 textareas (ASÍ HABLO + ASÍ NO + 4 más)
│       │   ├── VoiceTextareaWithWarning.tsx   # textarea + soft warning detector inline
│       │   ├── TreatmentLanguageCard.tsx      # tratamiento (tú/usted) + idioma fallback
│       │   ├── BrandVoicePreview.tsx          # footer único compiled sample (OQ-E)
│       │   └── __tests__/
│       ├── presencia/
│       │   ├── PresenciaView.tsx              # ★ client root
│       │   ├── WebsiteCard.tsx                # public landing URL (read-only) + own website
│       │   ├── SocialMediaLinksEditor.tsx     # IG/TikTok/FB/Google Business
│       │   ├── TrustSignalsEditor.tsx         # hybrid catalog per país + free-text
│       │   ├── LocationsCard.tsx              # ubicaciones (read-only — viven en clinics module)
│       │   └── __tests__/
│       └── shared/                            # cross-subsubtab utilities
│           ├── AutosaveProvider.tsx           # debounce 600ms hook context
│           ├── MarcaFormFooter.tsx            # "Guardado hace Xs" indicator (badge variant per state)
│           └── __tests__/
├── api/
│   ├── marca.ts                          # React Query hooks per resource
│   ├── marca-server.ts                   # SSR getInitialMarcaState({tenantId, subsubtab})
│   └── __tests__/
├── hooks/
│   ├── useIdentityAutosave.ts
│   ├── useVisualsAutosave.ts
│   ├── usePersonalityAutosave.ts
│   ├── useContactAutosave.ts
│   ├── useVoicePreview.ts
│   ├── useVoiceBlocklist.ts
│   └── __tests__/
├── store/
│   └── marca-store.ts                    # zustand UI state (activeArchetype, pendingVoiceOverride, draft state)
└── types/
    └── marca/
        ├── identity-schema.ts            # IMPORT verbatim nicolify + ADAPT
        ├── visuals-schema.ts             # idem
        ├── personality-schema.ts         # IMPORT + ADAPT (default Caregiver, omit 4)
        ├── contact-schema.ts             # IMPORT verbatim
        ├── team-schema.ts                # IMPORT verbatim (read-only preview)
        ├── presence-schema.ts            # NEW (social media + URL validation)
        ├── trust-signals-schema.ts       # NEW (catalog hybrid + free-text)
        ├── voice-preview-schema.ts       # NEW (compiled output type)
        ├── prohibited-phrase-schema.ts   # NEW
        └── marca.types.ts                # union types + helpers
```

### 6.4 Client root views (3 — one per subsubtab)

```tsx
// features/lisa/components/marca/identidad/IdentidadView.tsx
"use client"

import type { MarcaInitialStateDTO } from '@/features/lisa/types/marca/marca.types'

interface IdentidadViewProps {
  initialState: MarcaInitialStateDTO
  tenantId: string
}

export function IdentidadView({ initialState, tenantId }: IdentidadViewProps) {
  // 1. Hydrate React Query cache with initialState (identity + visuals + team_preview + clinic_config)
  // 2. useIdentityAutosave + useVisualsAutosave per card
  // 3. Compose IdentityCard + ClinicVerticalReadOnly + LogoDropZone + ColorTriadEditor + TypographyEditor + TeamPreviewRow + AutosaveBadge
  return (
    <section role="region" aria-label="Identidad de tu clínica">
      <IdentityCard />
      <ClinicVerticalReadOnly />
      <LogoDropZone />
      <ColorTriadEditor />
      <TypographyEditor />
      <TeamPreviewRow />
      <AutosaveBadge />
    </section>
  )
}
```

`VozTonoView.tsx` and `PresenciaView.tsx` follow same pattern. Each handles its own React Query cache hydration + autosave hooks per resource.

### 6.5 Data layer (React Query keys + invalidation)

```ts
// features/lisa/api/marca.ts
export const marcaKeys = {
  all: ['brand_studio', 'marca'] as const,
  identity: (tenantId: string) =>
    ['brand_studio', 'marca', 'identity', { tenantId }] as const,
  visuals: (tenantId: string) =>
    ['brand_studio', 'marca', 'visuals', { tenantId }] as const,
  personality: (tenantId: string) =>
    ['brand_studio', 'marca', 'personality', { tenantId }] as const,
  contact: (tenantId: string) =>
    ['brand_studio', 'marca', 'contact', { tenantId }] as const,
  teamPreview: (tenantId: string, limit: number) =>
    ['brand_studio', 'marca', 'team-preview', { tenantId, limit }] as const,
  clinicConfig: (tenantId: string) =>
    ['brand_studio', 'marca', 'clinic-config', { tenantId }] as const,
  voicePreview: (tenantId: string, debounceHash: string) =>
    ['brand_studio', 'marca', 'voice-preview', { tenantId, debounceHash }] as const,
  prohibitedPhrases: (tenantId: string, country: string) =>
    ['brand_studio', 'marca', 'prohibited-phrases', { tenantId, country }] as const,
  trustSignals: (tenantId: string) =>
    ['brand_studio', 'marca', 'trust-signals', { tenantId }] as const,
  trustCatalog: (country: string) =>
    ['brand_studio', 'marca', 'trust-catalog', { country }] as const,
}
```

Mutations + invalidations:

| Mutation | Invalidates |
|---|---|
| `usePatchIdentity` | `marcaKeys.identity(tenantId)` |
| `usePatchVisuals` | `marcaKeys.visuals(tenantId)` |
| `usePatchPersonality` | `marcaKeys.personality(tenantId)` + `marcaKeys.voicePreview(tenantId, '*')` |
| `usePatchContact` | `marcaKeys.contact(tenantId)` |
| `useUploadLogo` | `marcaKeys.visuals(tenantId)` |
| `useDeleteLogo` | `marcaKeys.visuals(tenantId)` |
| `useCreateTrustSignal` | `marcaKeys.trustSignals(tenantId)` |
| `useDeleteTrustSignal` | `marcaKeys.trustSignals(tenantId)` |
| `useLogVoiceWarningOverride` | none (log-only) |

### 6.6 Forms (RHF + Zod IMPORT verbatim nicolify + ADAPT salud)

```ts
// types/marca/personality-schema.ts
// IMPORT base from nicolify + ADAPT salud overlay
import { z } from 'zod'

export const SALUD_ARCHETYPES = ['caregiver', 'sage', 'healer', 'hero'] as const
export type SaludArchetype = typeof SALUD_ARCHETYPES[number]

export const personalitySchema = z.object({
  archetype: z.enum(SALUD_ARCHETYPES).default('caregiver'),
  so_i_speak: z.string().max(4000).optional(),
  so_i_dont_speak: z.string().max(4000).optional(),
  technical_context: z.string().max(2000).optional(),
  format_instructions: z.string().max(2000).optional(),
  identity_anchor: z.string().max(2000).optional(),
  domain_context: z.string().max(2000).optional(),
})

export type PersonalityFormValues = z.infer<typeof personalitySchema>
```

Other schemas: `identity-schema.ts`, `visuals-schema.ts`, `contact-schema.ts`, `team-schema.ts` IMPORT verbatim from `nicolify/frontend/src/features/brand-studio/schemas/{identity,visuals,contact,team}.schema.ts`. `presence-schema.ts` + `trust-signals-schema.ts` NEW.

### 6.7 Autosave pattern (debounce 600ms — ADR-004 § 3.5)

```ts
// hooks/useIdentityAutosave.ts
import { useDebounce } from '@/lib/hooks/useDebounce'
import { useMutation } from '@tanstack/react-query'

export function useIdentityAutosave(tenantId: string) {
  const queryClient = useQueryClient()
  const { mutate, status } = useMutation({
    mutationFn: (patch: BrandIdentityPatchDTO) =>
      patchBrandIdentity({ tenantId, patch }),
    onSuccess: (data) => {
      queryClient.setQueryData(marcaKeys.identity(tenantId), data)
      toast.success('Guardado', { duration: 3000 })
      emitTelemetry('lisa_marca_identity_saved', { field_count_changed: Object.keys(patch).length })
    },
    onError: (err) => {
      toast.error('No pudimos guardar. Reintentar.', {
        action: { label: 'Reintentar', onClick: () => mutate(patch) },
      })
      emitTelemetry('lisa_marca_autosave_failed', {
        error_type: err.code ?? 'unknown', retry_count: 0,
      })
    },
  })
  return { save: useDebounce(mutate, 600), status }
}
```

### 6.8 BrandVoicePreview footer (OQ-E resolution)

```tsx
// components/marca/voz-y-tono/BrandVoicePreview.tsx
"use client"

import { useVoicePreview } from '@/features/lisa/hooks/useVoicePreview'

export function BrandVoicePreview({ tenantId }: { tenantId: string }) {
  // Refresh on any voice block autosave (subscribes to personality query updatedAt)
  const { data: preview, isFetching } = useVoicePreview({ tenantId })
  return (
    <footer
      role="region"
      aria-label="Vista previa de voz compilada"
      className="border-t border-border pt-4 mt-4"
    >
      <h3 className="text-sm font-medium mb-2">
        Así te escuchará un paciente al conversar con Valeria:
      </h3>
      <div className="space-y-2">
        <div className="bg-muted/30 p-3 rounded">
          <span className="text-xs text-muted-foreground">WhatsApp:</span>
          <p className="text-sm mt-1">{preview?.sample_whatsapp ?? '—'}</p>
        </div>
        <div className="bg-muted/30 p-3 rounded">
          <span className="text-xs text-muted-foreground">Email reactivación:</span>
          <p className="text-sm mt-1">{preview?.sample_email_reactivation ?? '—'}</p>
        </div>
      </div>
      {isFetching && <p className="text-xs text-muted-foreground mt-1">Actualizando…</p>}
    </footer>
  )
}
```

Hook subscribes to debounced refetch on any personality field change (600ms debounce hash). Single source of truth (footer único per OQ-E).

### 6.9 VoiceTextareaWithWarning (soft warning inline + override)

```tsx
// components/marca/voz-y-tono/VoiceTextareaWithWarning.tsx
"use client"

interface Props {
  value: string
  onChange: (v: string) => void
  blocklist: ProhibitedPhraseDTO[]
  section: 'so_i_speak' | 'so_i_dont_speak'
}

export function VoiceTextareaWithWarning({ value, onChange, blocklist, section }: Props) {
  const matched = useMemo(() => detectPhrases(value, blocklist), [value, blocklist])
  const [allowed, setAllowed] = useState(false)

  const handleOverride = async () => {
    await logVoiceWarningOverride({
      phrase_id: matched[0].id,
      section,
      user_text_excerpt: value.slice(0, 500),
    })
    setAllowed(true)
    emitTelemetry('lisa_marca_voice_warning_overridden', { phrase_severity: matched[0].severity })
  }

  return (
    <div>
      <Textarea value={value} onChange={(e) => onChange(e.target.value)} />
      {matched.length > 0 && !allowed && (
        <Alert variant="warning" role="alert" aria-live="polite" className="mt-2">
          <AlertTitle>Frase con potencial issue regulatorio</AlertTitle>
          <AlertDescription>
            Esta frase usa lenguaje que puede violar regulaciones de salud
            ({matched.map((m) => `"${m.phrase}"`).join(', ')}).
            Considera: "{matched[0].suggested_alternative}"
          </AlertDescription>
          <Button variant="ghost" size="sm" onClick={handleOverride}>
            Guardar igual con esta frase
          </Button>
        </Alert>
      )}
    </div>
  )
}
```

### 6.10 Mobile responsive

- `<640px`: Cards stacked full-width. Color triad → vertical. Archetype cards → grid 1 col.
- `640-768px`: Cards stacked. Form 1-col.
- `768-1024px`: Cards stacked max-width 720px. SubSubTabsBar visible compacta.
- `>1024px`: Cards 2-col donde aplique. Footer voice preview side-by-side WhatsApp + Email.

### 6.11 Zustand store (UI state only)

```ts
// store/marca-store.ts
import { create } from 'zustand'

interface MarcaState {
  pendingVoiceOverride: { phrase: string; section: string } | null
  setPendingVoiceOverride: (o: MarcaState['pendingVoiceOverride']) => void
  trustSignalDraft: TrustSignalCreateRequestDTO | null
  setTrustSignalDraft: (d: TrustSignalCreateRequestDTO | null) => void
}

export const useMarcaStore = create<MarcaState>((set) => ({
  pendingVoiceOverride: null,
  setPendingVoiceOverride: (o) => set({ pendingVoiceOverride: o }),
  trustSignalDraft: null,
  setTrustSignalDraft: (d) => set({ trustSignalDraft: d }),
}))
```

NO data fetched in store (React Query es SSoT). Only UI ephemeral state.

---

## § 7 — Repository Interfaces + Application Services

### 7.1 Repositories (BE — NO PHI base)

`vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/`

```python
# prohibited_phrase_repository.py
from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.vitalia.brand_studio.domain.prohibited_phrase import ProhibitedPhrase


class ProhibitedPhraseRepository(ABC):
    """Repo for prohibited phrases — tenant-scoped seeds + overrides."""

    @abstractmethod
    async def list_for_tenant(
        self, *, tenant_id: UUID, country: str | None = None,
    ) -> list[ProhibitedPhrase]:
        """Returns seed defaults (tenant_id IS NULL) + tenant overrides merged."""

    @abstractmethod
    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> ProhibitedPhrase | None: ...

    @abstractmethod
    async def create(self, phrase: ProhibitedPhrase) -> ProhibitedPhrase: ...

    @abstractmethod
    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None: ...
```

```python
# trust_signal_repository.py
class TrustSignalRepository(ABC):
    @abstractmethod
    async def list_for_tenant(self, *, tenant_id: UUID) -> list[TrustSignal]: ...

    @abstractmethod
    async def create(self, signal: TrustSignal) -> TrustSignal: ...

    @abstractmethod
    async def soft_delete(self, signal_id: UUID, *, tenant_id: UUID) -> None: ...
```

Implementations `*_repository_impl.py` use SQLA 2.0 `select(Model).where(...)`. Both inherit base `Repository` (NOT `PhiRepositoryBase`) — story is owner config, no PHI dual filter.

### 7.2 Application services

`vitalia/backend/src/modules/vitalia/brand_studio/application/services/`

#### `marca_service.py` (core orchestrator)

```python
class MarcaService:
    """Orchestrator for sub-tab Marca — wraps engine brand_studio + brand-local audit + telemetry."""

    def __init__(
        self,
        identity_repo: BrandIdentityRepository,      # engine repo via DI
        visuals_repo: BrandVisualsRepository,        # engine repo
        personality_repo: PersonalityProfileRepository,  # engine repo
        contact_repo: BrandContactRepository,        # engine repo
        team_repo: BrandTeamRepository,              # engine repo
        audit: AsyncAuditWriter,
        telemetry: GrowthStudioEmitter,
        voice_preview_service: VoicePreviewService,  # cache + compile
    ): ...

    async def get_initial_state(
        self, *, tenant_id: UUID, user_id: UUID, subsubtab: Literal["identidad", "voz-y-tono", "presencia"],
    ) -> MarcaInitialStateDTO:
        """SSR-friendly state hydration. Audit log row `read_marca_initial_state`."""

    async def patch_identity(
        self, *, tenant_id: UUID, user_id: UUID, patch: BrandIdentityPatchDTO,
    ) -> BrandIdentityDTO:
        # 1. Engine repo update with partial fields
        # 2. Audit log sync write action='brand_identity_updated'
        # 3. Telemetry emit lisa_marca_identity_saved
        # 4. Return projected DTO

    async def patch_visuals(self, *, tenant_id, user_id, patch) -> BrandVisualsDTO: ...
    async def patch_personality(
        self, *, tenant_id: UUID, user_id: UUID, patch: BrandPersonalityPatchDTO,
    ) -> BrandPersonalityDTO:
        # 1. Engine personality_repo update
        # 2. Invalidate voice_preview cache for this tenant
        # 3. Audit log action='brand_personality_updated' (sanitize payload — no full text in log)
        # 4. Telemetry emit lisa_marca_personality_saved with {archetype, voice_warning_triggered=False}

    async def patch_contact(self, *, tenant_id, user_id, patch) -> BrandContactDTO: ...

    async def upload_logo(self, *, tenant_id, user_id, file) -> LogoUploadResponseDTO:
        # Server-side validation: max 5MB + format in {png, jpg, jpeg, webp}
        # Upload to S3-compatible storage via existing infrastructure
        # Update visuals.logo_url
        # Audit log + telemetry
```

#### `voice_preview_service.py` (OQ-C resolution)

```python
class VoicePreviewService:
    """Compile slot 5 BRAND_VOICE preview deterministic — NO LLM dispatch."""

    def __init__(
        self,
        personality_repo: PersonalityProfileRepository,
        cache: VoicePreviewCache,  # in-process LRU + Redis fallback
    ): ...

    async def get_preview(self, *, tenant_id: UUID) -> VoicePreviewDTO:
        # 1. Load personality_profile via engine repo
        # 2. Build cache key f"voice_preview:{tenant_id}:{profile.id}:{compiler_version}:{hash(blocks)}"
        # 3. Cache hit → return cached preview
        # 4. Cache miss → call compose_brand_voice_preview(profile) from luana_core_sales_agent
        # 5. Two canonical samples: WhatsApp short greeting + email reactivation
        # 6. Store + return + cache_hit=False

    async def invalidate(self, *, tenant_id: UUID) -> None:
        """Called by MarcaService.patch_personality post-write."""
```

`compose_brand_voice_preview` is a NEW pure function we'll add to `core/luana-core-sales-agent` IF NEEDED — but FIRST verify: engine `compose.py::PromptFragment.BRAND_VOICE` already exposes the compile logic; we just need to wrap it in a 2-sample generator. If wrapping requires engine modify → escalate `/pm-luana`. Default path: we use engine's `compose.py` API as-is + build the 2-sample loop in `voice_preview_service.py` brand-local.

#### `voice_blocklist_service.py` (NEW + seed)

```python
class VoiceBlocklistService:
    """CRUD + seed defaults salud per country (OQ-D)."""

    def __init__(self, repo: ProhibitedPhraseRepository): ...

    async def list_for_tenant(self, *, tenant_id: UUID, country: str | None = None) -> ProhibitedPhrasesListDTO:
        items = await self.repo.list_for_tenant(tenant_id=tenant_id, country=country)
        return ProhibitedPhrasesListDTO(items=[...], total=len(items))

    async def log_warning_override(
        self, *, tenant_id: UUID, user_id: UUID, request: VoiceWarningOverrideRequestDTO,
    ) -> UUID:
        # 1. Audit log row action='voice_warning_overridden' with payload sanitized
        # 2. Telemetry emit lisa_marca_voice_warning_overridden with phrase_severity
        # 3. Return audit_id

    @staticmethod
    def seed_defaults_pe() -> list[ProhibitedPhrase]:
        """Hard-coded seed defaults for PE (OQ-D resolution).

        Inserted by migration as tenant_id=NULL rows. PE primero; AR/CL/CO/MX/BR follow stories.
        """
        return [
            ProhibitedPhrase(phrase="curamos", suggested_alternative="acompañamos tu tratamiento", severity="high", country_scope="PE"),
            ProhibitedPhrase(phrase="garantizado", suggested_alternative="con protocolos avalados", severity="high", country_scope="PE"),
            ProhibitedPhrase(phrase="100% efectivo", suggested_alternative="con alta tasa de éxito clínico", severity="high", country_scope="PE"),
            ProhibitedPhrase(phrase="sin riesgos", suggested_alternative="con protocolos de seguridad clínica", severity="high", country_scope="PE"),
            ProhibitedPhrase(phrase="tratamiento milagroso", suggested_alternative="tratamiento basado en evidencia", severity="medium", country_scope="PE"),
            ProhibitedPhrase(phrase="cura definitiva", suggested_alternative="solución duradera respaldada por protocolos", severity="high", country_scope="PE"),
            ProhibitedPhrase(phrase="sin dolor", suggested_alternative="con técnicas de manejo del dolor", severity="medium", country_scope="PE"),
            ProhibitedPhrase(phrase="resultados inmediatos", suggested_alternative="resultados visibles según protocolo", severity="medium", country_scope="PE"),
            ProhibitedPhrase(phrase="los mejores del mercado", suggested_alternative="con experiencia reconocida en el sector", severity="low", country_scope="PE"),
            ProhibitedPhrase(phrase="terapia exclusiva", suggested_alternative="terapia especializada", severity="low", country_scope="PE"),
        ]
```

#### `trust_catalog_service.py`

```python
class TrustCatalogService:
    """Hybrid catalog per país (OQ-D) — seed catalog read-only."""

    HYBRID_CATALOG: dict[str, list[dict[str, str]]] = {
        "PE": [
            {"code": "DIGESA", "label": "DIGESA (Dirección General de Salud Ambiental)", "hint": "Autoridad sanitaria PE"},
            {"code": "MINSA", "label": "MINSA (Ministerio de Salud)", "hint": "Autoridad nacional salud"},
            {"code": "SUSALUD", "label": "SUSALUD (Superintendencia Nacional de Salud)", "hint": "Regulador salud"},
            {"code": "COP_ODONTO", "label": "Colegio Odontológico del Perú", "hint": "Para clínicas dentales"},
            {"code": "CMP", "label": "Colegio Médico del Perú", "hint": "Para clínicas médicas"},
            {"code": "SUNAT", "label": "SUNAT (vigente)", "hint": "Contribuyente activo"},
            {"code": "ISO_9001", "label": "ISO 9001 Calidad", "hint": "Certificación gestión calidad"},
            {"code": "ESSALUD", "label": "EsSalud (convenio)", "hint": "Convenio seguro social"},
        ],
        "AR": [],  # populate future
        "CL": [],
        "CO": [],
        "MX": [],
        "BR": [],
    }

    async def get_catalog(self, *, country: str) -> TrustSignalsCatalogDTO:
        items = self.HYBRID_CATALOG.get(country.upper(), [])
        return TrustSignalsCatalogDTO(country=country.upper(), items=items)
```

### 7.3 Transaction boundaries

- Each `patch_*` service method runs inside a single AsyncSession transaction. `audit_log` row uses same session (per `AsyncAuditWriter`) — atomic commit.
- Voice preview cache invalidation is **post-commit** (`session.commit() → cache.invalidate(...)`). If cache fails → log warning, no rollback (preview will re-compile on next request).
- Telemetry emit is fire-forget (try/except + structlog warning per `_shared/telemetry/growth_studio_emitter.py` shipped pattern).

### 7.4 No idempotency tables

PATCH endpoints idempotent by design (same payload → same state). POST endpoints (logos, trust-signals, voice-warning-override) generate server-side UUIDs — natural per-call uniqueness.

---

## § 8 — Cross-cutting Concerns

### 8.1 Tenant isolation (single filter — owner config, no PHI)

- Every query filters `tenant_id`. Repos heredan `Repository` base normal — NO `PhiRepositoryBase`, NO `validate_dual_filter(clinic_id=...)`.
- HIPAA-lite dual filter NO aplica (story scope = brand identity tenant-wide config, no patient PHI).
- Cross-tenant edit attempt → 403 with `cross_tenant_brand_edit_attempt` audit row + telemetry event.
- Arch test `test_brand_studio_module_ddd.py` extended con `select(.*Model).where(...tenant_id...)` regex scan.

### 8.2 Audit log (sync write antes response — defense-in-depth)

Every mutation persists row antes return:

| Endpoint | action value |
|---|---|
| PATCH `/lisa/marca/identity` | `"brand_identity_updated"` |
| PATCH `/lisa/marca/visuals` | `"brand_visuals_updated"` |
| PATCH `/lisa/marca/personality` | `"brand_personality_updated"` |
| PATCH `/lisa/marca/contact` | `"brand_contact_updated"` |
| POST `/lisa/marca/logos` | `"brand_logo_uploaded"` |
| DELETE `/lisa/marca/logos/{id}` | `"brand_logo_deleted"` |
| POST `/lisa/marca/voice-warning-override` | `"voice_warning_overridden"` |
| POST `/lisa/marca/trust-signals` | `"trust_signal_added"` |
| DELETE `/lisa/marca/trust-signals/{id}` | `"trust_signal_removed"` |
| GET initial-state (always) | `"read_marca_initial_state"` |
| Cross-tenant detected | `"cross_tenant_brand_edit_attempt"` |
| GET voice-preview (cache miss compile) | `"voice_preview_compiled"` (low-volume, info-level) |

Arch test `test_audit_log_sync_write.py` extended con grep verificación per nuevo PATCH/POST/DELETE endpoint.

### 8.3 PII/PHI sanitization (server-side traces + telemetry)

- Audit_log payloads → `sanitize_payload(payload, compliance_level="hipaa_lite")` (already enforced en `AsyncAuditWriter`).
- Telemetry events idem.
- structlog WARN events: no interpolate user-typed text verbatim. Use bucketed metadata only.
- `user_text_excerpt` field in `VoiceWarningOverrideRequestDTO` capped at 500 chars + sanitized before audit log write.

### 8.4 Spanish neutro LatAm

All UI strings + microcopy validated against `.claude/rules/spanish-text.md` glosario. Pre-commit hook verifies. **Exception:** sales_agent output respeta voz tenant (puede voseo). Lisa-marca UI = neutro tuteo strict (no voseo).

### 8.5 Native-first dev gates

- BE: `cd vitalia/backend && ${WS}/.venv/bin/{ruff,pytest,mypy}` (root venv)
- FE: `cd vitalia/frontend && npx {tsc,eslint,vitest,playwright}` (no docker exec)

### 8.6 Anti-creep guards (`.claude/rules/sales-agent-brand-voice.md`)

- ❌ NO crear `brand_voice_summary` mirror — arch test `test_no_brand_voice_summary_table.py` enforces
- ❌ NO crear `health_voice_validator.py` LLM validator — arch test `test_no_health_voice_validator.py` enforces
- ❌ NO fine-tuning per tenant
- ❌ NO voice-rewriter LLM pass post-generación
- ❌ NO inyectar `{tenant_name}` mid-block en slot 5 (cache invalidation risk)
- ✅ Soft warning configurable vía `vitalia_prohibited_phrases` (no bloqueo, audit log override)

### 8.7 Visual extraction stub (D4)

- Sub-sub-tab Identidad muestra botón "Extraer desde mi sitio web" **disabled** con Tooltip "Próximamente — extracción automática de paleta y tipografía".
- Telemetry event `lisa_marca_extract_website_clicked` capturado en click (track desire, no action).
- Implementación real espera `/pm-luana` accept proposal `2026-05-26-lift-brand-visual-extraction-to-core.md`. Re-evaluar story dedicada futura.

---

## § 9 — Migration Notes (idempotent raw SQL)

### 9.1 Migration `XXXX_f2_s7_vitalia_lisa_marca.py`

```python
"""F2-S7 Vitalia lisa-marca: prohibited_phrases table + seed defaults PE.

Idempotent — uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

Revision ID: f2_s7_vitalia_lisa_marca
Revises: <last vitalia revision>
Create Date: 2026-MM-DDT00:00:00.000000

downstream-regression-na: brand-local prohibited phrases table; no engine modify.
"""
from __future__ import annotations
from alembic import op

revision = "f2_s7_vitalia_lisa_marca"
down_revision = "<previous>"

def upgrade() -> None:
    # vitalia_prohibited_phrases — soft warning blocklist (NO LLM validator)
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_prohibited_phrases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID,
            phrase VARCHAR(200) NOT NULL,
            suggested_alternative VARCHAR(500) NOT NULL,
            severity VARCHAR(16) NOT NULL DEFAULT 'medium',
            country_scope VARCHAR(2),
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_phrase_tenant_severity ON vitalia_prohibited_phrases (tenant_id, severity) WHERE deleted_at IS NULL;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_phrase_country_severity ON vitalia_prohibited_phrases (country_scope, severity) WHERE deleted_at IS NULL AND tenant_id IS NULL;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_phrase_lookup ON vitalia_prohibited_phrases (phrase) WHERE deleted_at IS NULL;")

    # Seed defaults PE (tenant_id IS NULL → cross-tenant baseline). ON CONFLICT DO NOTHING for idempotency.
    op.execute("""
        INSERT INTO vitalia_prohibited_phrases (phrase, suggested_alternative, severity, country_scope) VALUES
            ('curamos', 'acompañamos tu tratamiento', 'high', 'PE'),
            ('garantizado', 'con protocolos avalados', 'high', 'PE'),
            ('100% efectivo', 'con alta tasa de éxito clínico', 'high', 'PE'),
            ('sin riesgos', 'con protocolos de seguridad clínica', 'high', 'PE'),
            ('tratamiento milagroso', 'tratamiento basado en evidencia', 'medium', 'PE'),
            ('cura definitiva', 'solución duradera respaldada por protocolos', 'high', 'PE'),
            ('sin dolor', 'con técnicas de manejo del dolor', 'medium', 'PE'),
            ('resultados inmediatos', 'resultados visibles según protocolo', 'medium', 'PE'),
            ('los mejores del mercado', 'con experiencia reconocida en el sector', 'low', 'PE'),
            ('terapia exclusiva', 'terapia especializada', 'low', 'PE')
        ON CONFLICT DO NOTHING;
    """)
    # NOTE: Other countries (AR/CL/CO/MX/BR) seeded via dedicated story `vitalia-fase2-lisa-marca-seed-countries` (state=idea).

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vitalia_prohibited_phrases;")
```

### 9.2 No modifications to engine tables

Engine `personality_profiles`, `brand_identities`, `brand_visuals`, `brand_contacts`, `brand_teams` viven en `core/luana-core-brand-studio/` shipped — NO schema changes from this story. Cualquier engine change requeriría `/pm-luana` promotion proposal.

### 9.3 Prod-clone test command

```bash
# Verify migration idempotency against a clone of vitalia prod schema
WS=$(git rev-parse --show-toplevel)
docker exec luana-vitalia-postgres-dev psql -U postgres -d vitalia_migration_test -c "BEGIN;" \
  && docker exec luana-vitalia-backend-dev alembic upgrade head \
  && docker exec luana-vitalia-backend-dev alembic upgrade head    # second run = no-op (idempotency)
```

Pre-prod gate: run migration twice; second run MUST produce zero DDL changes (CREATE TABLE IF NOT EXISTS + ON CONFLICT DO NOTHING).

---

## § 9.5 — Tests Audit (default flip — N/A for F2-S7)

| Field | Value |
|---|---|
| `[x] No aplica` | F2-S7 NO flippea defaults side-effect. No toca `USE_OUTBOX_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` ni equivalente. |

(Reference: `.claude/rules/anti-default-flip-audit.md` — story arquitectura no modifica feature flag inventory.)

---

## § 10 — Telemetría arquitectura

### 10.1 Sink: REUSE `vitalia_growth_studio_event` brand-local table (shipped F2-S1)

NO crear tabla nueva. Emitter `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` ya shipped. Esta story EXTEND con 13 nuevos `event_name` agregados al whitelist `_KNOWN_EVENT_NAMES` constante.

### 10.2 13 nuevos events (HIPAA-lite payload constraints — bucketed metadata)

| Event | Trigger | Props sanitized |
|---|---|---|
| `lisa_marca_viewed` | Page mount per subsubtab | `{subsubtab_initial}` |
| `lisa_marca_subsubtab_changed` | SubSubTabsBar click | `{from, to}` |
| `lisa_marca_identity_saved` | PATCH /identity 200 | `{field_count_changed}` |
| `lisa_marca_visuals_saved` | PATCH /visuals 200 | `{field_count_changed, has_logo}` |
| `lisa_marca_personality_saved` | PATCH /personality 200 | `{archetype, voice_warning_triggered}` |
| `lisa_marca_contact_saved` | PATCH /contact 200 | `{field_count_changed}` |
| `lisa_marca_voice_warning_shown` | Blocklist phrase detected client-side | `{phrase_severity, suggested_alternative_present}` |
| `lisa_marca_voice_warning_overridden` | POST /voice-warning-override 200 | `{phrase_severity}` |
| `lisa_marca_logo_uploaded` | POST /logos 200 | `{file_size_bucket, format}` |
| `lisa_marca_logo_oversized` | Client-side ≥5MB validation fail | `{file_size_mb_int}` |
| `lisa_marca_extract_website_clicked` | Click disabled button | `{}` |
| `lisa_marca_team_preview_clicked` | Click "Gestionar equipo" link | `{}` |
| `lisa_marca_clinic_config_edit_clicked` | Click "Editar configuración inicial" link | `{}` |
| `lisa_marca_autosave_failed` | Mutation error post-debounce | `{error_type, retry_count}` |
| `lisa_marca_trust_signal_added` | POST /trust-signals 200 | `{catalog_code_or_freetext}` |

NO props verbatim text user-typed (`name`, `tagline`, `so_i_speak`, `so_i_dont_speak` field values NEVER in payload). Solo metadata bucketed.

### 10.3 file_size_bucket function

```python
def bucket_file_size(size_bytes: int) -> str:
    mb = size_bytes / (1024 * 1024)
    if mb < 0.5: return "0-500KB"
    if mb < 1: return "500KB-1MB"
    if mb < 2: return "1-2MB"
    if mb < 5: return "2-5MB"
    return "5MB+"
```

Brand-local helper en `vitalia/backend/src/modules/vitalia/_shared/telemetry/file_size_bucket.py` (NEW). FE mirror en `vitalia/frontend/src/lib/telemetry.ts`.

### 10.4 Arch test EXTEND `test_growth_studio_event_no_phi.py`

Verifica:
1. 13 nuevos events declarados en whitelist `_KNOWN_EVENT_NAMES`.
2. Payload sample per event NO contiene keys matching PHI regex (`patient_*`, `dni`, `diagnosis`, `treatment`, `medication`, `appointment_id` raw, `name`, `tagline`, `email`).
3. Bucketed fields use enum string (e.g., `file_size_bucket: "0-500KB"`) not raw bytes count beyond bucket label.

---

## § 11 — Test Surfaces (TDD-mandatory + ★ v4.1 Test Construction Plan)

### 11.1 BE test layers (RED-first per layer)

| Layer | File | Coverage |
|---|---|---|
| Domain | `tests/modules/vitalia/brand_studio/test_prohibited_phrase_domain.py` | ProhibitedPhrase + SaludArchetype enums + invariants |
| Domain | `tests/modules/vitalia/brand_studio/test_voice_preview_domain.py` | VoicePreview dataclass + compiler_version match |
| Infra | `tests/modules/vitalia/brand_studio/test_prohibited_phrase_repository.py` | tenant override + seed lookup + country filter |
| Infra | `tests/modules/vitalia/brand_studio/test_trust_signal_repository.py` | CRUD + tenant isolation + soft delete |
| Application | `tests/modules/vitalia/brand_studio/test_marca_service.py` | patch_identity + patch_visuals + patch_personality + patch_contact + audit + telemetry |
| Application | `tests/modules/vitalia/brand_studio/test_voice_preview_service.py` | compile + cache hit/miss + invalidate on patch |
| Application | `tests/modules/vitalia/brand_studio/test_voice_blocklist_service.py` | seed defaults + override audit log |
| Application | `tests/modules/vitalia/brand_studio/test_trust_catalog_service.py` | hybrid catalog per country (PE seed + AR/CL/CO/MX/BR empty) |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_identity.py` | GET/PATCH identity end-to-end + audit row |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_visuals.py` | idem + logo upload size validation 5MB |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_personality.py` | idem + voice-preview cache invalidate post-patch |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_contact.py` | idem |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_voice_preview.py` | GET compile + cache hit second call |
| API | `tests/modules/vitalia/brand_studio/test_marca_router_trust_signals.py` | CRUD + catalog hybrid per país |
| API | `tests/modules/vitalia/brand_studio/test_marca_cross_tenant.py` | Cross-tenant 403 + audit row `cross_tenant_brand_edit_attempt` |
| API | `tests/modules/vitalia/brand_studio/test_prohibited_phrases_seed.py` | Seed defaults PE present post-migration |
| API | `tests/modules/vitalia/brand_studio/test_voice_warning_audit_log.py` | Override action `voice_warning_overridden` audit row |
| Architecture | `tests/architecture/test_brand_studio_module_ddd.py` (NEW) | DDD layers + tenant_id every query |
| Architecture | `tests/architecture/test_no_health_voice_validator.py` (NEW) | Grep `health_voice_validator` returns 0 matches (creep guard) |
| Architecture | `tests/architecture/test_no_brand_voice_summary_table.py` (NEW or EXTEND) | Grep `brand_voice_summary` returns 0 matches (creep guard cardinal) |
| Architecture | `tests/architecture/test_growth_studio_event_no_phi.py` (EXTEND) | 13 new events declared + payload has no PHI fields |

### 11.2 FE Vitest unit tests

| File | Coverage |
|---|---|
| `features/lisa/components/marca/identidad/__tests__/IdentidadView.test.tsx` | Composition + initial state hydration + autosave hook integration |
| `features/lisa/components/marca/identidad/__tests__/IdentityCard.test.tsx` | RHF form + Zod validate + autosave 600ms |
| `features/lisa/components/marca/identidad/__tests__/LogoDropZone.test.tsx` | Drag drop + 5MB client validation + preview + telemetry on oversized |
| `features/lisa/components/marca/identidad/__tests__/ColorTriadEditor.test.tsx` | 3 pickers + hex input + contrast warning |
| `features/lisa/components/marca/identidad/__tests__/TypographyEditor.test.tsx` | Font selects + autosave |
| `features/lisa/components/marca/identidad/__tests__/TeamPreviewRow.test.tsx` | Avatars + counter + edit-link |
| `features/lisa/components/marca/identidad/__tests__/ClinicVerticalReadOnly.test.tsx` | Read-only display + edit-link |
| `features/lisa/components/marca/voz-y-tono/__tests__/VozTonoView.test.tsx` | Composition + cards order + BrandVoicePreview footer mounting |
| `features/lisa/components/marca/voz-y-tono/__tests__/ArchetypeSelector.test.tsx` | 4 radio cards + Caregiver default + tooltips |
| `features/lisa/components/marca/voz-y-tono/__tests__/VoiceCompilerBlocks.test.tsx` | 6 textareas + RHF + autosave per block |
| `features/lisa/components/marca/voz-y-tono/__tests__/VoiceTextareaWithWarning.test.tsx` | Detect blocklist phrase + Alert + override button + audit log |
| `features/lisa/components/marca/voz-y-tono/__tests__/BrandVoicePreview.test.tsx` | Footer single instance + debounce refresh + 2 samples display |
| `features/lisa/components/marca/voz-y-tono/__tests__/TreatmentLanguageCard.test.tsx` | tú/usted toggle + idioma fallback select |
| `features/lisa/components/marca/presencia/__tests__/PresenciaView.test.tsx` | Composition |
| `features/lisa/components/marca/presencia/__tests__/WebsiteCard.test.tsx` | Public URL read-only + own website input |
| `features/lisa/components/marca/presencia/__tests__/SocialMediaLinksEditor.test.tsx` | 4 social inputs + URL/handle validation |
| `features/lisa/components/marca/presencia/__tests__/TrustSignalsEditor.test.tsx` | Hybrid catalog dropdown + free-text "Otra" + CRUD + logo upload |
| `features/lisa/components/marca/shared/__tests__/AutosaveProvider.test.tsx` | Debounce + state propagation |
| `features/lisa/api/__tests__/marca.test.ts` | React Query hooks + mutations + invalidations |
| `features/lisa/hooks/__tests__/useVoicePreview.test.ts` | Debounce hash + cache key + fetch trigger |
| `features/lisa/hooks/__tests__/useVoiceBlocklist.test.ts` | List fetch + match detection |
| `features/lisa/store/__tests__/marca-store.test.ts` | Zustand state shape |

### 11.3 Playwright E2E specs (★ Test Construction Plan v4.1)

`base_path:` `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/`

**creation_order:**

| Step | File | Content | Depends_on |
|---|---|---|---|
| 1 | `fixtures/lisa-marca.fixture.ts` | Clerk authedAsOwner + tenant PE setup + DB seed brand_identity/visuals/personality + MSW handlers brand engine | [] |
| 2 | `fixtures/voice-preview-mock.ts` | MSW handler GET /voice-preview variants: hit/miss/compile error | [1] |
| 3 | `fixtures/large-dataset.fixture.ts` | DB seed 50 testimonials + 30 team members for SC large_dataset | [1] |
| 4 | `fixtures/network-failure.ts` | route.abort() helper for autosave timeout | [1] |
| 5 | `poms/lisa-marca-page.pom.ts` | LisaMarcaPage POM: navigateToSubsubtab(name), getActiveSubsubtab, getAutosaveBadge, waitForLoaded |
| 6 | `poms/identidad-section.pom.ts` | IdentidadSectionPage POM: getNameInput, fillName, getLogoDropZone, uploadLogo(file), getColorPicker, getTeamPreviewLink, getEditConfigLink |
| 7 | `poms/voz-tono-section.pom.ts` | VozTonoSectionPage POM: selectArchetype(name), getBlockTextarea(section), fillBlock, getWarningAlert, clickOverride, getBrandVoicePreview, getPreviewSamples |
| 8 | `poms/presencia-section.pom.ts` | PresenciaSectionPage POM: fillWebsite, fillInstagram, fillTikTok, fillGoogleBusiness, selectTrustSignal(code), addCustomTrustSignal(label), removeTrustSignal(id) |
| 9 | `lisa-marca-identidad-autosave.spec.ts` | SC-1 happy autosave + audit row created | [5, 6] |
| 10 | `lisa-marca-voice-warning.spec.ts` | SC-2 negative warning soft + override + audit row | [5, 7] |
| 11 | `lisa-marca-logo-upload-size.spec.ts` | SC-3 edge logo >5MB client + server + retry compressed | [5, 6] |
| 12 | `lisa-marca-race-autosave.spec.ts` | SC-5 race condition 2 tabs + last-write-wins + dual audit | [5, 6] |
| 13 | `lisa-marca-concurrent-owners.spec.ts` | SC-6 concurrent_users 2 BrowserContexts + non-blocking notification | [5, 7] |
| 14 | `lisa-marca-autosave-timeout.spec.ts` | SC-7 network_failure 30s timeout + retry counter + rollback | [5, 6] |
| 15 | `lisa-marca-empty-state.spec.ts` | SC-8 empty_state tenant nuevo + CTA Empezar + prellenado | [5, 6] |
| 16 | `lisa-marca-large-dataset.spec.ts` | SC-9 large 50 testimonials + 30 team + perf LCP ≤1500ms | [5, 6, 3] |
| 17 | `lisa-marca-cross-tenant.spec.ts` | SC-4 adversarial cross-tenant 403 + audit row | [5, 6] (mostly BE) |
| 18 | `lisa-marca-keyboard.spec.ts` | SC-10 accessibility keyboard nav Tab + Arrow keys subsubtab cycle | [5, 6, 7] |
| 19 | `lisa-marca-i18n.spec.ts` | SC-11 i18n Spanish neutro grep + axe | [5] |
| 20 | `../a11y/lisa-marca-a11y.spec.ts` | axe-core wcag2aa 3 subsubtabs idle/loading/success/error/empty states | [9] |
| 21 | `../visual/lisa-marca-visual.spec.ts` | Visual goldens: 3 subsubtabs × 2 themes = 6 PNGs | [9, 10] |

**scenario_to_test mapping:**

| Gherkin SC | Spec file | test() function | Validator |
|---|---|---|---|
| SC-1 happy autosave | `lisa-marca-identidad-autosave.spec.ts` | `test("owner edits name + autosave fires + audit row", ...)` | scenario_happy_path |
| SC-2 negative voice warning | `lisa-marca-voice-warning.spec.ts` | `test("voice warning soft + override audit", ...)` | scenario_negative |
| SC-3 edge logo oversized | `lisa-marca-logo-upload-size.spec.ts` | `test("logo >5MB client blocks + retry compressed", ...)` | scenario_edge |
| SC-4 adversarial cross-tenant | `lisa-marca-cross-tenant.spec.ts` + BE `test_marca_cross_tenant.py` | `test("cross-tenant PATCH 403 + audit row", ...)` | scenario_adversarial |
| SC-5 race autosave | `lisa-marca-race-autosave.spec.ts` | `test("2 tabs autosave concurrent last-write-wins", ...)` | scenario_race_condition |
| SC-6 concurrent owners | `lisa-marca-concurrent-owners.spec.ts` | `test("2 owners same tenant edit voice non-blocking notify", ...)` | scenario_concurrent_users |
| SC-7 network failure | `lisa-marca-autosave-timeout.spec.ts` | `test("autosave 30s timeout retry counter", ...)` | scenario_network_failure |
| SC-8 empty state | `lisa-marca-empty-state.spec.ts` | `test("tenant nuevo empty state hero + CTA", ...)` | scenario_empty_state |
| SC-9 large dataset | `lisa-marca-large-dataset.spec.ts` | `test("50 testimonials + 30 team render LCP ≤1500ms", ...)` | scenario_large_dataset |
| SC-10 accessibility | `lisa-marca-keyboard.spec.ts` + a11y spec | `test("keyboard nav subsubtab cycle + focus visible", ...)` | scenario_accessibility |
| SC-11 i18n | `lisa-marca-i18n.spec.ts` | `test("Spanish neutro grep 0 matches voseo", ...)` | scenario_i18n |

### 11.4 POMs spec

- `LisaMarcaPage`: navigateToSubsubtab(name), getActiveSubsubtab(), getAutosaveBadge(), waitForLoaded(), getSubSubTabsBar()
- `IdentidadSectionPage`: getNameInput(), fillName(v), getLogoDropZone(), uploadLogo(filePath), getColorPicker(slot), fillHexColor(slot, hex), getTeamPreviewLink(), getEditConfigLink(), getExtractWebsiteButton()
- `VozTonoSectionPage`: selectArchetype(name), getBlockTextarea(section), fillBlock(section, text), getWarningAlert(), clickOverride(), getBrandVoicePreview(), getPreviewSamples(), getTreatmentToggle()
- `PresenciaSectionPage`: fillWebsite(url), fillInstagram(handle), fillTikTok(handle), fillGoogleBusiness(url), selectTrustSignal(code), addCustomTrustSignal(label), removeTrustSignal(id), getLocationsList()

### 11.5 Fixtures spec

- `authedAsOwner`: returns `BrowserContext` with Clerk storage state injected for `owner` role
- `dbSeedBrandData(tenant_id, country='PE')`: seeds brand_identity + visuals + personality + contact
- `dbSeedLargeDataset(tenant_id, testimonials=50, team=30)`: large dataset for SC-9
- `mockVoicePreviewMiss()` / `mockVoicePreviewHit()` / `mockVoicePreviewError()`: MSW handler variants
- `networkFailure(endpoint)`: Playwright `page.route(endpoint, route => route.abort('timedout'))`

---

## § 12 — Architecture Decisions (ratified spec + arch additions)

Source decisions (cementadas en `01-spec.md` § Ratified decisions + new architect decisions below). Builders MUST honor each in commits via `## Decisions honored` block.

### From spec (D-decisions cemented 2026-05-26 / 2026-05-27)

| ID | Decision | Spec anchor |
|---|---|---|
| D1-arch | Citar ADR-vitalia-004 verbatim — patrón replicable transversal | Chris 2026-05-26 |
| D2-voice | Eliminar `health_voice_validator.py`. Reuse compiler v2 + `vitalia_prohibited_phrases` soft warning configurable | Chris 2026-05-26 |
| D3-clinic | `clinic_vertical` + `primary_specialties` capturados en `vitalia-fase2-config-onboarding-clinica` story paralela. Lisa-marca muestra read-only + edit-link | Chris 2026-05-26 |
| D4-extract | Visual extraction pipeline = stub local + botón disabled hasta `/pm-luana` accept proposal | Chris 2026-05-26 |
| D5-archetype | Subset Jung salud-friendly (Caregiver default + Sage + Healer + Hero) — omit Outlaw/Magician/Lover/Innocent | OQ-B resolution 2026-05-27 |
| OQ-A | N3-static SubSubTabsBar cabecera (no Tabs body — Nivel 4 anti-pattern) | spec v2 2026-05-27 |
| OQ-B | 4 archetypes salud (Caregiver/Sage/Healer/Hero) | OQ-B resolution 2026-05-27 |
| OQ-C | BE endpoint `/lisa/marca/voice-preview` server-side compile + cache | OQ-C resolution 2026-05-27 |
| OQ-D | Hybrid trust catalog cerrado per país + free-text "Otra"; seed PE shipped | OQ-D resolution 2026-05-27 |
| OQ-E | Preview footer único debajo card Tratamiento+idioma en sub-sub-tab Voz · refresh on autosave 600ms | OQ-E resolution 2026-05-27 |

### Architect decisions NEW

| ID | Decision | Rationale |
|---|---|---|
| A1 | NEW módulo `vitalia/backend/src/modules/vitalia/brand_studio/` (brand-extension, NO mirror engine) | Engine `core/luana-core-brand-studio` shipped multi-brand; brand-local wrapper agrega audit + telemetry + voice preview cache + prohibited phrases. Engine modify requeriría `/pm-luana` (out-of-scope). |
| A2 | NO `PhiRepositoryBase` para repos brand_studio — story es owner config, no PHI directo | Defense-in-depth aplica via audit_log + sanitize_payload universal. Dual filter `clinic_id` no aplica (config tenant-wide). |
| A3 | `VoicePreviewService` server-side compile + LRU+Redis cache key `(tenant_id, profile_id, compiler_version, hash(blocks))` (OQ-C resolution) | Single SSoT compilación slot 5 BRAND_VOICE. Cache hit ≥80% expected post-deploy (autosave triggers re-compile only on field change). |
| A4 | NEW `vitalia_prohibited_phrases` brand-local table + seed defaults PE (NULL tenant_id row) | Anti-creep rule cumple: NO LLM validator, NO brand_voice_summary mirror. Configurable soft warning. Future stories seed AR/CL/CO/MX/BR. |
| A5 | REUSE `vitalia_growth_studio_event` (shipped F2-S1) — extend whitelist 13 nuevos events | NO crear tabla telemetry separate. Bucketed metadata only (no PHI). |
| A6 | NEW arch test `test_no_health_voice_validator.py` creep guard | Origin: anti-creep cardinal `.claude/rules/sales-agent-brand-voice.md` § "NO crear LLM validator". Bloquea regresión accidental futura. |
| A7 | NEW (or EXTEND) arch test `test_no_brand_voice_summary_table.py` creep guard | Idem — bloquea tabla mirror cardinal forbidden. Si nicolify ya tiene → EXTEND con vitalia scope. |
| A8 | Schemas Zod IMPORT verbatim de nicolify + ADAPT salud overlay (omit 4 archetypes problematic) | FE shared pattern post brand-studio shipped multi-brand. NO BE cross-brand import. Documentado en `.claude/rules/anti-duplication.md` § "Cross-brand schemas FE OK pero BE no". |
| A9 | Visual extraction stub local + botón disabled (D4) | Promotion proposal `/pm-luana` 2026-05-26 NOT accepted aún. Stub respeta UX placeholder + telemetry track desire. |
| A10 | Audit log mandatory en cada mutación brand (10 actions declarados) | Defense-in-depth — owner config también auditado (similar HIPAA-lite pattern aunque no PHI directo). |
| A11 | SubSubTabsBar component verbatim copy de SubTabsBar (F1-S8) | Pattern reuse — minimiza divergencia visual + a11y. Tint color cambia heredada agent (`--agent-lisa`). |
| A12 | AGENT_SUBSUBTABS catalog en `lib/routing/shell-routes.ts` (NEW o MODIFY si ya existe AGENT_SUBTABS) | Convention ADR-vitalia-004 v1.1 § 3.1.3. lisa.marca first entry `'identidad'` = default redirect. |
| A13 | Logo upload server-side dual validation (≥5MB + format whitelist) — client-side validation defense-in-depth | Network bandwidth saving (client blocks pre-request) + server resilience (DevTools bypass). |
| A14 | `vitalia_prohibited_phrases` table seed via raw SQL `INSERT ... ON CONFLICT DO NOTHING` (idempotent) | Per `.claude/rules/backend-migrations.md` — raw SQL idempotent only. Tenant overrides via UI futura. |

---

## § 13 — capability YAML + modules/brand_studio.md Updates

### 13.1 NEW capability file (post-merge)

`vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml`

```yaml
capability_id: brand_studio/lisa-marca
title: "Workspace administración brand-identity salud-overlay Lisa→Marca"
agent_owner: lisa
module: brand_studio
status: shipped
shipped_at: 2026-MM-DD                    # post-merge
story: vitalia-fase2-lisa-marca
deliverable_paths:
  backend:
    - vitalia/backend/src/modules/vitalia/brand_studio/
  frontend:
    - vitalia/frontend/src/features/lisa/
    - vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/
gherkin_scenarios: [SC-1, SC-2, SC-3, SC-4, SC-5, SC-6, SC-7, SC-8, SC-9, SC-10, SC-11]
hipaa_lite_overlay: true                  # overlay aplica (audit log) aunque story scope sea owner config no PHI directo
api_endpoints:
  - GET /api/v1/lisa/marca/initial-state/{subsubtab}
  - GET/PATCH /api/v1/lisa/marca/identity
  - GET/PATCH /api/v1/lisa/marca/visuals
  - POST/DELETE /api/v1/lisa/marca/logos
  - GET/PATCH /api/v1/lisa/marca/personality
  - GET/PATCH /api/v1/lisa/marca/contact
  - GET /api/v1/lisa/marca/team-preview
  - GET /api/v1/lisa/marca/clinic-config
  - GET /api/v1/lisa/marca/voice-preview
  - GET /api/v1/lisa/marca/prohibited-phrases
  - POST /api/v1/lisa/marca/voice-warning-override
  - GET/POST/DELETE /api/v1/lisa/marca/trust-signals
  - GET /api/v1/lisa/marca/trust-catalog
service_dependencies:
  - (none — engine brand_studio shipped, sales_agent compiler v2 shipped)
```

### 13.2 NEW `vitalia/docs/product/modules/brand_studio.md`

NEW module-level documentation file (brand_studio módulo brand-extension new). Schema per `.claude/rules/brand-docs-schema.md`:

```markdown
# brand_studio (vitalia)

Brand-local extension of engine `core/luana-core-brand-studio` providing
salud-overlay capabilities (clinic vertical context, prohibited phrases soft
warning, voice preview cached compile, trust signals hybrid catalog).

## Capabilities operativas
<!-- AUTO-GENERATED por scripts/reconcile_capabilities.py — NO editar a mano -->
- brand_studio/lisa-marca — Workspace administración brand-identity salud-overlay
<!-- END AUTO-GENERATED -->

## Engine consumed
- core/luana-core-brand-studio (BrandIdentity, PersonalityProfile, BrandVisuals, BrandContact, BrandTeam)
- core/luana-core-sales-agent (PromptFragment.BRAND_VOICE compose API)
```

Auto-list regen via:
```bash
WS=$(git rev-parse --show-toplevel)
${WS}/.venv/bin/python ${WS}/scripts/reconcile_capabilities.py --brand vitalia
```

---

## § 14 — Research Notes (DATE-AWARE — accessed 2026-05-27)

| Topic | Source | accessed | Key takeaway |
|---|---|---|---|
| React Server Components per N3-static segment | https://nextjs.org/docs (canonical) | 2026-05-27 | Each `[subsubtab]/page.tsx` is Server Component with own initial state fetch. Server-First pattern reduces hydration cost vs single Client view with internal Tabs. Opus 4.7 cutoff Jan 2026; researched via live canonical docs URL. |
| React Query v5 hydration + initial data per subsubtab | https://tanstack.com/query/latest/docs/framework/react/guides/ssr | 2026-05-27 | `initialData` per subsubtab page fetched server-side; client root view hydrates only relevant resources. staleTime longer for read-mostly resources (clinic_config, team_preview). |
| Anthropic prompt caching slot architecture | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-05-27 | Slot 5 BRAND_VOICE = cacheable per-tenant. Marca UI patches mutate slot 5 directly → cache invalidation on next sales_agent turn natural. NO inject `{tenant_name}` mid-block (cache buster). Knowledge cutoff Jan 2026; live research current state. |
| LangGraph compiler v2 slot SSoT | https://docs.langchain.com/oss/python/langgraph/workflows-agents | 2026-05-27 | N/A para esta story directamente. F2-S7 NO modifica LangGraph runtime. Solo CONSUME `compose.py` library API. Cita para auditor trazabilidad. |
| Shadcn Form + RHF + Zod resolver | https://ui.shadcn.com/docs/components/form | 2026-05-27 | RHF + `zodResolver` + autosave on-change 600ms debounce. Form subscribes per-field watch + parent dispatches mutation per dirty fields. |
| Pydantic v2 partial PATCH update | https://docs.pydantic.dev/latest/concepts/models/ | 2026-05-27 | `model_config = ConfigDict(extra="forbid")` rejects unknown fields. Optional fields `None` por default ignored on update — model `.model_dump(exclude_unset=True)` for partial patch. |
| MSW v2 + Playwright fixtures multi-route | https://mswjs.io/docs/integrations/browser | 2026-05-27 | Per-spec MSW worker handlers — overlap with global fixtures via `worker.use(...)` per test. |
| WCAG 2.1 AA + axe-core scan per state | https://www.deque.com/axe/ | 2026-05-27 | Per-screen-state axe scan (idle/loading/success/error/empty). Critical+serious violations = fail. |
| Anti-creep sales-agent brand voice rule | Internal SSoT `.claude/rules/sales-agent-brand-voice.md` | 2026-05-27 | NO brand_voice_summary mirror, NO LLM validator, NO fine-tuning per tenant. Configurable soft warning blocklist OK. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = Jan 2026. For Next.js 16 + React Query v5 + Pydantic v2 patterns current as of access date, MSW v2, and slot 5 BRAND_VOICE compiler researched via canonical URLs on 2026-05-27.

---

## § 15 — File Structure Summary

### 15.1 Backend NEW + MODIFIED

```
vitalia/backend/src/modules/vitalia/
├── brand_studio/                                       # NEW módulo brand-extension
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── prohibited_phrase.py                       # ProhibitedPhrase + ProhibitedPhraseSeverity StrEnum
│   │   ├── archetype.py                               # SaludArchetype StrEnum (Caregiver/Sage/Healer/Hero)
│   │   ├── voice_preview.py                           # VoicePreview frozen dataclass
│   │   └── trust_signal.py                            # TrustSignal dataclass
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   └── repositories/
│   │       ├── prohibited_phrase_repository.py        # ABC + impl
│   │       └── trust_signal_repository.py             # ABC + impl
│   ├── application/
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── marca_service.py                       # ★ orchestrator
│   │       ├── voice_preview_service.py               # cache + compile (consume engine compose.py)
│   │       ├── voice_blocklist_service.py             # CRUD + override audit
│   │       └── trust_catalog_service.py               # hybrid per país
│   ├── api/
│   │   ├── __init__.py
│   │   ├── marca_router.py                            # 21 endpoints
│   │   └── dtos/
│   │       ├── __init__.py
│   │       └── marca_dtos.py                          # 18 Pydantic v2 DTOs
│   └── persistence/
│       ├── __init__.py
│       └── models/
│           ├── __init__.py
│           └── prohibited_phrase_model.py
├── _shared/
│   ├── telemetry/
│   │   ├── growth_studio_emitter.py                   # MODIFY — extend whitelist 13 events
│   │   └── file_size_bucket.py                        # NEW helper
│   └── auth/
│       └── rbac.py                                    # MODIFY add require_brand_owner_access
└── extensions.py                                       # MODIFY — register brand_studio router

vitalia/backend/alembic/versions/
└── XXXX_f2_s7_vitalia_lisa_marca.py                   # NEW migration (1 table + 10 seed rows PE)

vitalia/backend/tests/
├── modules/vitalia/brand_studio/                       # NEW
│   ├── __init__.py
│   ├── test_prohibited_phrase_domain.py
│   ├── test_voice_preview_domain.py
│   ├── test_prohibited_phrase_repository.py
│   ├── test_trust_signal_repository.py
│   ├── test_marca_service.py
│   ├── test_voice_preview_service.py
│   ├── test_voice_blocklist_service.py
│   ├── test_trust_catalog_service.py
│   ├── test_marca_router_identity.py
│   ├── test_marca_router_visuals.py
│   ├── test_marca_router_personality.py
│   ├── test_marca_router_contact.py
│   ├── test_marca_router_voice_preview.py
│   ├── test_marca_router_trust_signals.py
│   ├── test_marca_cross_tenant.py
│   ├── test_prohibited_phrases_seed.py
│   └── test_voice_warning_audit_log.py
└── architecture/
    ├── test_brand_studio_module_ddd.py                 # NEW
    ├── test_no_health_voice_validator.py               # NEW (creep guard)
    └── test_no_brand_voice_summary_table.py            # NEW or EXTEND (creep guard cardinal)
```

### 15.2 Frontend NEW + MODIFIED

```
vitalia/frontend/src/
├── app/[tenantId]/(shell-organism)/
│   └── lisa/                                           # NEW static segment
│       └── marca/
│           ├── page.tsx                                # → redirect to /identidad
│           ├── identidad/page.tsx                      # Server Component
│           ├── voz-y-tono/page.tsx                     # Server Component
│           └── presencia/page.tsx                      # Server Component
├── components/shared/shell-organism/
│   └── SubSubTabsBar.tsx                               # NEW (per ADR-004 § 3.1.2)
├── components/ui/                                       # NEW Shadcn primitives (verify install)
│   ├── label.tsx
│   ├── radio-group.tsx
│   ├── checkbox.tsx
│   ├── switch.tsx
│   └── sheet.tsx
├── features/lisa/                                       # NEW feature root
│   ├── index.ts
│   ├── components/marca/
│   │   ├── identidad/
│   │   │   ├── IdentidadView.tsx
│   │   │   ├── IdentityCard.tsx
│   │   │   ├── ClinicVerticalReadOnly.tsx
│   │   │   ├── LogoDropZone.tsx
│   │   │   ├── ColorTriadEditor.tsx
│   │   │   ├── TypographyEditor.tsx
│   │   │   ├── TeamPreviewRow.tsx
│   │   │   ├── ExtractFromWebsiteButton.tsx
│   │   │   ├── AutosaveBadge.tsx
│   │   │   └── __tests__/
│   │   ├── voz-y-tono/
│   │   │   ├── VozTonoView.tsx
│   │   │   ├── ArchetypeSelector.tsx
│   │   │   ├── VoiceCompilerBlocks.tsx
│   │   │   ├── VoiceTextareaWithWarning.tsx
│   │   │   ├── TreatmentLanguageCard.tsx
│   │   │   ├── BrandVoicePreview.tsx
│   │   │   └── __tests__/
│   │   ├── presencia/
│   │   │   ├── PresenciaView.tsx
│   │   │   ├── WebsiteCard.tsx
│   │   │   ├── SocialMediaLinksEditor.tsx
│   │   │   ├── TrustSignalsEditor.tsx
│   │   │   ├── LocationsCard.tsx
│   │   │   └── __tests__/
│   │   └── shared/
│   │       ├── AutosaveProvider.tsx
│   │       ├── MarcaFormFooter.tsx
│   │       └── __tests__/
│   ├── api/
│   │   ├── marca.ts                                    # React Query hooks
│   │   ├── marca-server.ts                             # SSR fetch helper
│   │   └── __tests__/
│   ├── hooks/
│   │   ├── useIdentityAutosave.ts
│   │   ├── useVisualsAutosave.ts
│   │   ├── usePersonalityAutosave.ts
│   │   ├── useContactAutosave.ts
│   │   ├── useVoicePreview.ts
│   │   ├── useVoiceBlocklist.ts
│   │   └── __tests__/
│   ├── store/
│   │   ├── marca-store.ts
│   │   └── __tests__/
│   └── types/marca/
│       ├── identity-schema.ts                          # IMPORT verbatim nicolify
│       ├── visuals-schema.ts                           # idem
│       ├── personality-schema.ts                       # IMPORT + ADAPT salud (4 archetypes only)
│       ├── contact-schema.ts                           # IMPORT verbatim
│       ├── team-schema.ts                              # IMPORT verbatim (read-only)
│       ├── presence-schema.ts                          # NEW
│       ├── trust-signals-schema.ts                     # NEW
│       ├── voice-preview-schema.ts                     # NEW
│       ├── prohibited-phrase-schema.ts                 # NEW
│       └── marca.types.ts                              # union helpers
├── lib/routing/
│   └── shell-routes.ts                                 # MODIFY — add AGENT_SUBSUBTABS catalog + extractSubsubtabFromPath
├── lib/telemetry.ts                                    # MODIFY — extend with file_size_bucket mirror
└── test-utils/msw/handlers/
    └── lisa-marca-handlers.ts                          # NEW

vitalia/frontend/e2e/
├── regression/vitalia-fase2-lisa-marca/                # NEW
│   ├── fixtures/
│   │   ├── lisa-marca.fixture.ts
│   │   ├── voice-preview-mock.ts
│   │   ├── large-dataset.fixture.ts
│   │   └── network-failure.ts
│   ├── poms/
│   │   ├── lisa-marca-page.pom.ts
│   │   ├── identidad-section.pom.ts
│   │   ├── voz-tono-section.pom.ts
│   │   └── presencia-section.pom.ts
│   └── *.spec.ts                                       # 11 spec files
├── a11y/
│   └── lisa-marca-a11y.spec.ts
└── __screenshots__/lisa-marca/                          # 6 visual goldens (3 subsubtabs × 2 themes)
    ├── identidad-light.png · identidad-dark.png
    ├── voz-y-tono-light.png · voz-y-tono-dark.png
    └── presencia-light.png · presencia-dark.png
```

### 15.3 Legacy DELETE post-merge

```
vitalia/frontend/src/app/(dashboard)/brand-studio/[section]/page.tsx       # legacy refactored
vitalia/frontend/src/features/vitalia/components/brand-studio-section-client.tsx  # legacy
```

---

## § 16 — Open Questions for PM

(Resolved during architect orchestration — listed for transparency)

1. ✅ **N3-static vs Tabs body** → RESUELTA OQ-A v2: N3-static SubSubTabsBar cabecera (ADR-004 v1.1 § 3.1.1 cementación)
2. ✅ **Archetypes salud subset** → RESUELTA OQ-B: 4 archetypes (Caregiver default / Sage / Healer / Hero) — omit Outlaw/Magician/Lover/Innocent (D5)
3. ✅ **Voice-preview BE endpoint vs client-side** → RESUELTA OQ-C: BE endpoint con cache server por hash (A3)
4. ✅ **Trust catalog hybrid scope** → RESUELTA OQ-D: hybrid per país (PE seed shipped, AR/CL/CO/MX/BR future stories) + free-text "Otra" (A4)
5. ✅ **Preview footer placement** → RESUELTA OQ-E: footer único debajo card Tratamiento+idioma + refresh on autosave 600ms debounce (§ 6.8)
6. ✅ **`PhiRepositoryBase` aplica?** → NO. Story scope = owner config tenant-wide, no PHI directo. Defense-in-depth via audit_log universal (A2)
7. ✅ **`vitalia_growth_studio_event` REUSE o NEW table?** → REUSE shipped F2-S1. Extend whitelist 13 events (A5)
8. ✅ **`compose_brand_voice_preview` library function lives where?** → Brand-local en `voice_preview_service.py` wrapping engine `compose.py::PromptFragment.BRAND_VOICE`. NO engine modify needed.

(No outstanding open questions blocking /dev-team pickup.)
