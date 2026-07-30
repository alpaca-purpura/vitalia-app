<!-- voseo-allowed: glosario reference (forbidden voseo examples documented) -->
# 05-guidelines.md — F2-S7 vitalia-fase2-lisa-marca

> Owner: `/architect` orchestrator. Patterns concretos que el `/dev-team` builder DEBE seguir/evitar — SIN AMBIGÜEDAD.
> Si dev-team sigue al pie + corre validators GREEN → ticket pasa auditoría.

---
story_id: vitalia-fase2-lisa-marca
brand: vitalia
arch_version: 1
schema_version: v4.1
last_modified: 2026-05-27T05:52:36Z
hipaa_lite_overlay: true
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
---

## must_load_skills (★ v4.1 enforceable — builder MUST cargar todas + reportar "Skills consulted" en T-{n}-result.md)

> Builder spawn prompt cita esta lista verbatim. Si builder no carga + documenta → auditor CHANGES_REQUESTED automático.

### required (sin condición)

| ID | Tipo | Aplica a | Razón |
|---|---|---|---|
| `.claude/rules/tenant-isolation.md` | rule | TODOS tickets | Every query filter tenant_id |
| `vitalia/.claude/rules/hipaa-lite.md` | rule (brand overlay) | TODOS tickets BE | Audit log sync + PHI sanitization (defense-in-depth aunque story scope = owner config sin PHI directo) |
| `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` | rule (brand overlay) | TODOS tickets | ADR-vitalia-004 compliance 9 secciones + N3-static cementado |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | rule (brand overlay) | TODOS tickets FE UI | Mockup visual fidelity gate — visual goldens ratchet |
| `.claude/rules/anti-duplication.md` | rule | TODOS tickets | Cross-brand mirror BE ban (FE Zod schemas IMPORT verbatim from nicolify es OK shared pattern post brand-studio shipped multi-brand) |
| `.claude/rules/sales-agent-brand-voice.md` | rule | TODOS tickets BE/FE voz | Anti-creep cardinal — NO health_voice_validator, NO brand_voice_summary mirror, NO LLM voice-rewriter, NO fine-tuning per tenant |
| `.claude/rules/tdd-mandatory.md` | rule | TODOS tickets | RED→GREEN→REFACTOR — tests FIRST por capa |
| `.claude/rules/spanish-text.md` | rule | TODOS tickets FE | Voseo glosario neutro LatAm |
| `.claude/rules/auditor-self-fix-policy.md` | rule | TODOS | Conocer qué findings auditor self-fix vs spawn dev-team |
| `.claude/rules/git-safety.md` | rule | TODOS | Triple-branch + forbidden ops + Conventional Commits |
| `.claude/rules/parallel-safety.md` | rule | TODOS | M11 push >30min + sub-agents NO crean worktree |

### required by surface

| ID | Tipo | When |
|---|---|---|
| `backend-expert` | skill | surface=BE — DDD patterns + arch fitness + currency + master-data |
| `brand-expert` | skill | surface=BE/FE voz — PersonalityProfile compiler v2 SSoT + Jung archetypes salud-friendly + BuyerPersona context |
| `sales-agent-expert` | skill | surface=BE voice-preview — slot 5 BRAND_VOICE compiler v2 anchor |
| `.claude/rules/backend-ddd.md` | rule | surface=BE — Inside-Out + SQLA 2.0 + tenant_id every query + soft delete |
| `.claude/rules/backend-migrations.md` | rule | surface=BE migrations — idempotent raw SQL `IF NOT EXISTS` + `ON CONFLICT DO NOTHING` para seed |
| `.claude/rules/master-data.md` | rule | surface=BE — UTC store + `DateTime(timezone=True)` |
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | code SSoT | surface=BE mutation endpoint — usar AsyncAuditWriter |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | code SSoT (extend) | surface=BE — emit telemetry events + agregar 13 nuevos events al whitelist |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/` | engine SSoT (read-only) | surface=BE — CONSUME via repos import + service injection (NO modify) |
| `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py` | engine SSoT (read-only library) | surface=BE voice-preview — invoke compile API |
| `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | engine SSoT (read-only) | surface=BE — sanitize_payload(compliance_level='hipaa_lite') |
| `frontend-expert` | skill | surface=FE — FSD-Lite + Shadcn reuse + form-runtime + tokens |
| `.claude/rules/frontend-fsd.md` | rule | surface=FE — boundary matrix + features/lisa/ |
| `playwright-expert` | skill | test_construction_plan.playwright_required=true — POMs + Clerk auth + MSW + smoke debugging |
| `.claude/rules/e2e-testing.md` | rule | surface=FE E2E — Playwright config vitalia port 3002 |
| `tessl__fastapi` | tessl tile | BE endpoint nuevo |
| `tessl__pytest-api-testing` | tessl tile | BE tests nuevos |
| `tessl__react-patterns` | tessl tile | FE component nuevo |
| `tessl__shadcn-ui` | tessl tile | FE component Shadcn install/use |
| `tessl__tailwind` | tessl tile | FE component (tokens semánticos) |
| `tessl__zod` | tessl tile | FE form con validation |
| `tessl__vitest` | tessl tile | FE tests nuevos |
| `tessl__nextjs-app-router-modularization` | tessl tile | FE route nueva |

### NO required (explicit exclusion)

- `copilot-expert` — N/A (no copilot surface — story administra brand identity, no LLM conversation)
- `tessl__langgraph` — N/A (no LangGraph runtime modify)
- `metrics-expert` — Skill consultada por architect; builder NO carga (no analytics ETL en F2-S7)
- `offer-expert` / `offer-type-preset-expert` — N/A (story toca brand voice/identity, no offers)

### reference_artifacts (re-read mid-build cuando surge ambigüedad)

- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/01-spec.md` — 11 Gherkin scenarios + 3 ASCII wireframes + OQ resolutions
- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/03-arch.md` — Decisiones técnicas + § Test Construction Plan
- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/04-validators.yaml` — validators + test_construction_plan
- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/06-tickets.yaml` — ticket T-{n} entry + gherkin_coverage
- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/{identidad,voz-tono,presencia}-section.html` — 3 mockups ratificados Chris iter v2.1 + `_shared.css`
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` — SOURCE STORY del patrón ADR-vitalia-004
- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` — ADR transversal cementado
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` — overlay gate bloqueante
- `vitalia/.claude/rules/shell-mockup-per-component.md` — overlay mockup gate
- `vitalia/.claude/rules/hipaa-lite.md` — overlay brand defensiva
- `.claude/rules/sales-agent-brand-voice.md` — anti-creep cardinal
- `nicolify/frontend/src/features/brand-studio/schemas/{identity,contact,visuals,personality,team,testimonial-item}.schema.ts` — IMPORT verbatim source

---

## Files in scope (builder PUEDE tocar)

### Backend NEW

```
vitalia/backend/src/modules/vitalia/brand_studio/__init__.py
vitalia/backend/src/modules/vitalia/brand_studio/domain/{__init__.py, prohibited_phrase.py, archetype.py, voice_preview.py, trust_signal.py}
vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/{__init__.py, repositories/{__init__.py, prohibited_phrase_repository.py, trust_signal_repository.py}}
vitalia/backend/src/modules/vitalia/brand_studio/application/{__init__.py, services/{__init__.py, marca_service.py, voice_preview_service.py, voice_blocklist_service.py, trust_catalog_service.py}}
vitalia/backend/src/modules/vitalia/brand_studio/api/{__init__.py, marca_router.py, dtos/{__init__.py, marca_dtos.py}}
vitalia/backend/src/modules/vitalia/brand_studio/persistence/{__init__.py, models/{__init__.py, prohibited_phrase_model.py}}
vitalia/backend/src/modules/vitalia/_shared/telemetry/file_size_bucket.py
vitalia/backend/alembic/versions/XXXX_f2_s7_vitalia_lisa_marca.py
```

### Backend MODIFY

```
vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py    # extend whitelist with 13 lisa_marca_* events
vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py                          # add require_brand_owner_access decorator
vitalia/backend/src/modules/vitalia/extensions.py                                  # register brand_studio router
vitalia/backend/src/main.py                                                        # include new router via include_router
```

### Backend tests NEW

```
vitalia/backend/tests/modules/vitalia/brand_studio/{__init__.py, test_prohibited_phrase_domain.py, test_voice_preview_domain.py, test_prohibited_phrase_repository.py, test_trust_signal_repository.py, test_marca_service.py, test_voice_preview_service.py, test_voice_blocklist_service.py, test_trust_catalog_service.py, test_marca_router_identity.py, test_marca_router_visuals.py, test_marca_router_personality.py, test_marca_router_contact.py, test_marca_router_voice_preview.py, test_marca_router_trust_signals.py, test_marca_cross_tenant.py, test_prohibited_phrases_seed.py, test_voice_warning_audit_log.py}
vitalia/backend/tests/architecture/{test_brand_studio_module_ddd.py, test_no_health_voice_validator.py, test_no_brand_voice_summary_table.py}
```

### Frontend NEW

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/{page.tsx, identidad/page.tsx, voz-y-tono/page.tsx, presencia/page.tsx}
vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx
vitalia/frontend/src/features/lisa/index.ts
vitalia/frontend/src/features/lisa/components/marca/identidad/{IdentidadView, IdentityCard, ClinicVerticalReadOnly, LogoDropZone, ColorTriadEditor, TypographyEditor, TeamPreviewRow, ExtractFromWebsiteButton, AutosaveBadge}.tsx
vitalia/frontend/src/features/lisa/components/marca/identidad/__tests__/*.test.tsx
vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/{VozTonoView, ArchetypeSelector, VoiceCompilerBlocks, VoiceTextareaWithWarning, TreatmentLanguageCard, BrandVoicePreview}.tsx
vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/*.test.tsx
vitalia/frontend/src/features/lisa/components/marca/presencia/{PresenciaView, WebsiteCard, SocialMediaLinksEditor, TrustSignalsEditor, LocationsCard}.tsx
vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/*.test.tsx
vitalia/frontend/src/features/lisa/components/marca/shared/{AutosaveProvider, MarcaFormFooter}.tsx
vitalia/frontend/src/features/lisa/components/marca/shared/__tests__/*.test.tsx
vitalia/frontend/src/features/lisa/api/{marca, marca-server}.ts
vitalia/frontend/src/features/lisa/api/__tests__/*.test.ts
vitalia/frontend/src/features/lisa/hooks/{useIdentityAutosave, useVisualsAutosave, usePersonalityAutosave, useContactAutosave, useVoicePreview, useVoiceBlocklist}.ts
vitalia/frontend/src/features/lisa/hooks/__tests__/*.test.ts
vitalia/frontend/src/features/lisa/store/marca-store.ts
vitalia/frontend/src/features/lisa/store/__tests__/marca-store.test.ts
vitalia/frontend/src/features/lisa/types/marca/{identity-schema, visuals-schema, personality-schema, contact-schema, team-schema, presence-schema, trust-signals-schema, voice-preview-schema, prohibited-phrase-schema, marca.types}.ts
vitalia/frontend/src/components/ui/{label, radio-group, checkbox, switch, sheet}.tsx        # npx shadcn add (verify presence first)
vitalia/frontend/src/test-utils/msw/handlers/lisa-marca-handlers.ts
vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/{fixtures,poms}/*.ts
vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/lisa-marca-*.spec.ts (11 files)
vitalia/frontend/e2e/a11y/lisa-marca-a11y.spec.ts
vitalia/frontend/e2e/visual/lisa-marca-visual.spec.ts
vitalia/frontend/e2e/__screenshots__/lisa-marca/*.png (6 visual goldens)
```

### Frontend MODIFY

```
vitalia/frontend/src/lib/routing/shell-routes.ts                  # add AGENT_SUBSUBTABS catalog + extractSubsubtabFromPath
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx    # mount <SubSubTabsBar /> conditional
vitalia/frontend/src/lib/telemetry.ts                             # extend with file_size_bucket mirror + 13 new event names typed
```

### Frontend DELETE (post-merge)

```
vitalia/frontend/src/app/(dashboard)/brand-studio/[section]/page.tsx                # legacy refactored to lisa/marca
vitalia/frontend/src/features/vitalia/components/brand-studio-section-client.tsx    # legacy (rewritten in features/lisa)
```

---

## Files NEVER touch (HARD ban)

### Engine (read-only — consume via import only)

```
core/luana-core-*/src/**                                              # ALL engine packages — modify requires /pm-luana proposal
core/luana-core-brand-studio/                                          # consumed via repos + library import, NO mirror
core/luana-core-sales-agent/                                           # consumed via PromptFragment.BRAND_VOICE compose API
core/luana-core-platform/                                              # base entities + datetime_utils
core/luana-core-observability/                                         # sanitize_payload + sanitization
core/luana-core-compliance/                                            # ComplianceService — NOT consumed this story
core/luana-core-iam/                                                   # RBAC base
core/luana-core-billing/                                               # NO billing wiring
```

### Other brands (HARD ban BE)

```
nicolify/backend/**                                                    # HARD ban cross-brand BE
comunify/backend/**
lupulo/backend/**
nicolify/frontend/src/**                                               # HARD ban cross-brand FE LOGIC
comunify/frontend/src/**
lupulo/frontend/src/**
```

### Exception: nicolify Zod schemas IMPORT verbatim FE only

**OK (documented shared pattern):**
```
nicolify/frontend/src/features/brand-studio/schemas/{identity, contact, visuals, personality, team, testimonial-item}.schema.ts
```

Estos schemas Zod son contratos UI consumiendo el mismo engine `core/luana-core-brand-studio` — NO duplicación de lógica. Builder COPIA verbatim a `vitalia/frontend/src/features/lisa/types/marca/{name}-schema.ts` + adapta solo el `personalitySchema` para 4 archetypes salud-friendly. Las otras IMPORTs verbatim sin cambios.

**NO IMPORT:** positioning, narrative, story, strategy, methodology, buyer-persona, authority-item, legal, communication-assets, avatars, logos — disabled per `vitalia/config/brand.yaml::brand_studio.enabled_sections` simplified salud.

### Default flag flips R31

```
vitalia/backend/src/core/config.py                                     # DO NOT flip USE_*_PATTERN_* / LITELLM_PROXY_ENABLED / USE_DEEPAGENTS_* — story does not require + would invalidate audit per anti-default-flip-audit.md
```

### Skills + rules + process

```
.claude/skills/**                                                      # meta-paradigm — escalate Chris
.claude/rules/**                                                       # idem
vitalia/.claude/rules/**                                               # idem (brand overlay rules)
docs/process/**                                                        # idem
docs/architecture/**                                                   # idem (workspace-level)
vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md                     # SSoT shell — escalate /pm-vitalia si visual diverge
vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md # SSoT pattern — cite, no modify
vitalia/.claude/rules/shell-mockup-per-component.md                    # gate rule
```

### Cross-module dentro mismo brand (DDD respect)

```
vitalia/backend/src/modules/vitalia/scheduling/                        # NO import directo desde brand_studio — disjoint domain
vitalia/backend/src/modules/vitalia/payments/                          # idem
vitalia/backend/src/modules/vitalia/fiscal/                            # idem
vitalia/backend/src/modules/vitalia/crm/                               # idem — patient data via API si necesario (NO for lisa-marca)
vitalia/backend/src/modules/vitalia/clinics/                           # consume vía DI service injection (clinic_vertical + specialties read-only)
vitalia/backend/src/modules/vitalia/audit/                             # CONSUME AsyncAuditWriter import — do NOT modify
vitalia/backend/src/modules/vitalia/copilot/                           # NO touch — copilot brand-extension surface
vitalia/backend/src/modules/vitalia/sales_agent/                       # NO touch — sales_agent brand-extension surface
```

### Anti-creep cardinal (NEVER CREATE)

```
vitalia/backend/src/modules/vitalia/brand_studio/application/health_voice_validator.py   # FORBIDDEN per .claude/rules/sales-agent-brand-voice.md
# Any "brand_voice_summary" table or model mirror                                         # FORBIDDEN cardinal
# Any voice-rewriter LLM pass module                                                      # FORBIDDEN cardinal
# Any fine-tuning per tenant logic                                                        # FORBIDDEN cardinal
```

Arch tests `test_no_health_voice_validator.py` + `test_no_brand_voice_summary_table.py` enforce.

---

## Patterns required

### Backend (surface=BE)

#### SQLAlchemy 2.0

```python
# ✅ CORRECT — tenant_id every query
result = await session.execute(
    select(VitaliaProhibitedPhraseModel)
    .where(
        VitaliaProhibitedPhraseModel.tenant_id == tenant_id,
        VitaliaProhibitedPhraseModel.deleted_at.is_(None),
    )
)
rows = result.scalars().all()

# ✅ CORRECT — seed defaults lookup (tenant_id IS NULL is intentional, whitelisted)
seed = await session.execute(
    select(VitaliaProhibitedPhraseModel)
    .where(
        VitaliaProhibitedPhraseModel.tenant_id.is_(None),
        VitaliaProhibitedPhraseModel.country_scope == country,
        VitaliaProhibitedPhraseModel.deleted_at.is_(None),
    )
)

# ❌ PROHIBITED — SA 1.x legacy
rows = session.query(VitaliaProhibitedPhraseModel).filter_by(tenant_id=tenant_id).all()
```

#### Repository inheritance (NO PhiRepositoryBase)

```python
# ✅ CORRECT — Repository base normal (no dual filter required — story is owner config)
from src.modules.vitalia._shared.repositories.repository import Repository

class ProhibitedPhraseRepository(Repository):
    async def list_for_tenant(self, *, tenant_id: UUID, country: str | None) -> list[ProhibitedPhrase]:
        # tenant_id filter mandatory (universal rule)
        # country filter optional
        ...

# ❌ PROHIBITED — inheriting PhiRepositoryBase when no PHI present (defense-in-depth con audit_log es suficiente)
class ProhibitedPhraseRepository(PhiRepositoryBase):  # WRONG — implies clinic_id dual filter required
    async def list_for_tenant(self, *, tenant_id, clinic_id):  # clinic_id no aplica
        ...
```

#### Audit log sync write (defense-in-depth — universal vitalia rule)

```python
# ✅ CORRECT — sync write BEFORE response
async def patch_identity(self, *, tenant_id, user_id, patch):
    updated = await self.identity_repo.update(tenant_id=tenant_id, patch=patch)
    await self.audit.write(
        tenant_id=tenant_id, user_id=user_id,
        action="brand_identity_updated",
        resource_type="brand_identity",
        resource_id=updated.id,
        payload_redacted=sanitize_payload({"fields_changed": list(patch.model_fields_set)}, compliance_level="hipaa_lite"),
    )  # sync BEFORE return
    await self.telemetry.emit(
        tenant_id=tenant_id, user_id=user_id,
        event_name="lisa_marca_identity_saved",
        props={"field_count_changed": len(patch.model_fields_set)},
    )  # fire-forget OK
    return self._project_dto(updated)

# ❌ PROHIBITED — async fire-forget on audit (loses transaction atomicity)
asyncio.create_task(self.audit.write(...))   # WRONG
```

#### Pydantic v2

```python
# ✅ CORRECT
class BrandIdentityPatchDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(None, min_length=2, max_length=100)

# ❌ PROHIBITED — inner class Config (v1 style)
class BrandIdentityPatchDTO(BaseModel):
    class Config:
        extra = "forbid"
```

#### structlog (no print/logging)

```python
# ✅ CORRECT
logger.info("brand_identity_patched", tenant_id=str(tenant_id), fields=list(patch.model_fields_set))

# ❌ PROHIBITED
print(f"Patched {patch.model_fields_set}")
logging.info(f"Tenant {tenant_id} patched")
```

#### Migrations idempotentes raw SQL

```python
# ✅ CORRECT
op.execute("CREATE TABLE IF NOT EXISTS vitalia_prohibited_phrases (...);")
op.execute("CREATE INDEX IF NOT EXISTS idx_vit_phrase_lookup ON ...;")
op.execute("INSERT INTO vitalia_prohibited_phrases (...) VALUES (...) ON CONFLICT DO NOTHING;")

# ❌ PROHIBITED
op.create_table("vitalia_prohibited_phrases", ...)
op.bulk_insert(table, [...])  # non-idempotent
sa.Enum(..., create_type=True)
```

#### FastAPI

```python
# ✅ CORRECT
@router.patch("/identity", response_model=BrandIdentityDTO, status_code=200)
async def patch_identity(
    request: BrandIdentityPatchDTO,
    user: User = Depends(require_brand_owner_access()),
    tenant_id: UUID = Depends(get_tenant_id),
    service: MarcaService = Depends(get_marca_service),
) -> BrandIdentityDTO:
    return await service.patch_identity(tenant_id=tenant_id, user_id=user.id, patch=request)

# ❌ PROHIBITED — missing response_model
@router.patch("/identity")
async def patch_identity(request: dict): ...
```

#### Voice preview cache pattern

```python
# ✅ CORRECT — cache key includes compiler_version + hash of blocks
def _build_cache_key(self, tenant_id: UUID, profile: PersonalityProfile) -> str:
    blocks_hash = hashlib.sha256(
        f"{profile.archetype}{profile.so_i_speak}{profile.so_i_dont_speak}...".encode()
    ).hexdigest()[:16]
    return f"voice_preview:{tenant_id}:{profile.id}:{COMPILER_VERSION}:{blocks_hash}"

# ❌ PROHIBITED — cache without version → stale cache after compiler upgrade
key = f"voice_preview:{tenant_id}:{profile.id}"   # WRONG
```

#### Engine library consumption (compose.py)

```python
# ✅ CORRECT — consume engine compose API as library
from luana_core_sales_agent.application.prompts.compose import PromptFragment

class VoicePreviewService:
    async def _compile(self, profile: PersonalityProfile) -> tuple[str, str]:
        # Build slot 5 BRAND_VOICE fragment using engine API
        whatsapp_sample = self._build_whatsapp_sample(profile)
        email_sample = self._build_email_sample(profile)
        return whatsapp_sample, email_sample
    # Pure deterministic — NO LLM dispatch

# ❌ PROHIBITED — call LLM inside voice-preview path
async def _compile(self, profile):
    return await llm.chat(messages=[...])   # WRONG — voice preview is compile-only
```

### Frontend (surface=FE)

#### React Server Components default per N3-static page

```tsx
// ✅ CORRECT — Server Component per subsubtab page
// app/[tenantId]/(shell-organism)/lisa/marca/identidad/page.tsx
export default async function IdentidadPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params
  const initialState = await getInitialMarcaState({ tenantId, subsubtab: 'identidad' })
  return <IdentidadView initialState={initialState} tenantId={tenantId} />
}

// ✅ CORRECT — 'use client' only in interactive root + sub-components
// features/lisa/components/marca/identidad/IdentidadView.tsx
"use client";
export function IdentidadView({ initialState, tenantId }) {
  // hydrate React Query + autosave hooks
}

// ❌ PROHIBITED — 'use client' en page Server Component
"use client";
export default function IdentidadPage() { ... }
```

#### N3-static routing redirect

```tsx
// ✅ CORRECT — lisa/marca/page.tsx redirects to default subsubtab
// app/[tenantId]/(shell-organism)/lisa/marca/page.tsx
import { redirect } from 'next/navigation'
import { AGENT_SUBSUBTABS } from '@/lib/routing/shell-routes'

export default async function LisaMarcaIndex({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params
  const first = AGENT_SUBSUBTABS.lisa?.marca?.[0] ?? 'identidad'
  redirect(`/${tenantId}/lisa/marca/${first}`)
}

// ❌ PROHIBITED — Shadcn Tabs body internal navigation (Nivel 4 anti-pattern per ADR-004 v1.1 § 3.1.1)
"use client";
export function LisaMarcaView() {
  return (
    <Tabs defaultValue="identidad">
      <TabsList>...</TabsList>
      <TabsContent value="identidad">...</TabsContent>
    </Tabs>
  )
}
```

#### React Query keys + invalidation

```ts
// ✅ CORRECT — keys schema centralized
export const marcaKeys = {
  identity: (tenantId: string) =>
    ['brand_studio', 'marca', 'identity', { tenantId }] as const,
  personality: (tenantId: string) =>
    ['brand_studio', 'marca', 'personality', { tenantId }] as const,
  voicePreview: (tenantId: string, debounceHash: string) =>
    ['brand_studio', 'marca', 'voice-preview', { tenantId, debounceHash }] as const,
}

usePatchPersonality onSuccess: (data) => {
  queryClient.invalidateQueries({ queryKey: marcaKeys.personality(tenantId) })
  queryClient.invalidateQueries({ queryKey: ['brand_studio', 'marca', 'voice-preview'] })  // catch-all prefix
}

// ❌ PROHIBITED — inline keys (drift risk)
useQuery({ queryKey: ['identity', tenantId], ... })
```

#### RHF + Zod (IMPORT verbatim nicolify + ADAPT)

```ts
// ✅ CORRECT — IMPORT verbatim from nicolify schemas
// vitalia/frontend/src/features/lisa/types/marca/identity-schema.ts
// Copied verbatim from: nicolify/frontend/src/features/brand-studio/schemas/identity.schema.ts
import { z } from 'zod'
export const identitySchema = z.object({
  name: z.string().min(2).max(100),
  tagline: z.string().max(150).optional(),
})
export type IdentityFormValues = z.infer<typeof identitySchema>

// ✅ CORRECT — ADAPT personality schema for salud overlay (4 archetypes only)
export const SALUD_ARCHETYPES = ['caregiver', 'sage', 'healer', 'hero'] as const
export const personalitySchema = z.object({
  archetype: z.enum(SALUD_ARCHETYPES).default('caregiver'),
  // ... rest identical to nicolify but with 4 archetypes
})

// ❌ PROHIBITED — custom invented schema cuando nicolify exists
const identitySchema = z.object({ ... })  // WRONG — IMPORT verbatim
```

#### Autosave pattern (debounce 600ms)

```ts
// ✅ CORRECT — debounce via dedicated hook + Sonner toast
export function useIdentityAutosave(tenantId: string) {
  const { mutate } = useMutation({
    mutationFn: (patch: BrandIdentityPatchDTO) => patchBrandIdentity({ tenantId, patch }),
    onSuccess: (data) => {
      queryClient.setQueryData(marcaKeys.identity(tenantId), data)
      toast.success('Guardado', { duration: 3000 })
      emitTelemetry('lisa_marca_identity_saved', { field_count_changed: ... })
    },
    onError: (err) => {
      toast.error('No pudimos guardar. Reintentar.', { action: { label: 'Reintentar', onClick: () => mutate(patch) } })
    },
  })
  return { save: useDebounce(mutate, 600) }
}

// ❌ PROHIBITED — submit button (no autosave)
<form onSubmit={handleSubmit(onSubmit)}>
  <button type="submit">Guardar</button>   // WRONG — autosave on-change required
</form>
```

#### Tailwind tokens

```tsx
// ✅ CORRECT — semantic tokens via CSS vars
<div className="border-l-2 border-l-[var(--agent-lisa)] bg-card text-foreground">
<div className="bg-destructive/10 border-destructive text-destructive">

// ❌ PROHIBITED — hex literals
<div className="border-l-2 border-l-[#10b981] bg-white text-black">
```

#### Spanish neutro LatAm

```tsx
// ✅ CORRECT — tuteo neutro
<button>Reintentar</button>
<p>Configurá tu identidad. Te llevará 5 minutos.</p>      // WAIT — "configurá" is voseo!

// ✅ CORRECT — fix
<p>Configura tu identidad. Te llevará 5 minutos.</p>

// ❌ PROHIBITED — voseo
<button>Reintentá</button>      // voseo imperativo
<p>Configurá la marca</p>       // idem
<p>Mirá la vista previa</p>     // idem
```

#### SubSubTabsBar mount

```ts
// ✅ CORRECT — AGENT_SUBSUBTABS declared in shell-routes catalog
export const AGENT_SUBSUBTABS = {
  lisa: {
    marca: ['identidad', 'voz-y-tono', 'presencia'],
  },
} as const

// ShellOrganismLayout mounts conditionally:
<SubSubTabsBar />  // renders null if no subsubtabs for current (agent, subtab)

// ❌ PROHIBITED — hardcoded inside LisaMarcaView client
<Tabs>...</Tabs>  // WRONG — N3-static via routing, not Tabs body
```

#### Voice warning soft (no block)

```tsx
// ✅ CORRECT — Alert variant=warning + override button + audit log
{matched.length > 0 && !allowed && (
  <Alert variant="warning" role="alert" aria-live="polite">
    <AlertTitle>Frase con potencial issue regulatorio</AlertTitle>
    <AlertDescription>
      Esta frase usa lenguaje que puede violar regulaciones de salud.
    </AlertDescription>
    <Button onClick={handleOverride}>Guardar igual con esta frase</Button>
  </Alert>
)}

// ❌ PROHIBITED — hard block submit
{matched.length > 0 && (
  <button type="submit" disabled>...</button>   // WRONG — soft warning only
)}
```

---

## Patterns forbidden

| ❌ Forbidden | ✅ Correct alternative |
|---|---|
| Create `health_voice_validator.py` | NEVER — anti-creep rule cardinal. Use `vitalia_prohibited_phrases` soft warning table |
| Create `brand_voice_summary` table mirror | NEVER — anti-creep rule cardinal. `personality_profiles.system_instruction` is SSoT |
| Voice-rewriter LLM pass post-generation | NEVER — anti-creep rule |
| Fine-tuning per tenant | NEVER — anti-creep rule |
| Inject `{tenant_name}` mid-block in slot 5 prefix | NEVER — cache buster |
| `datetime.utcnow()` | `utc_now()` from `luana_core_platform.domain.datetime_utils` |
| `'USD'` hardcoded default | `currency: str = Field(..., min_length=3, max_length=3)` (story has no monetary fields, but rule universal) |
| Cross-module SQL JOIN (e.g., brand_studio JOIN crm.patients) | API call or service injection |
| Cross-brand BE import (`from nicolify...`) | Lift to `core/luana-core-*` via `/pm-luana` proposal |
| Cross-brand FE LOGIC import | Same. Exception: Zod schemas IMPORT verbatim from `nicolify/.../brand-studio/schemas/` is OK (shared pattern multi-brand) |
| `session.query(Model)` SA 1.x | `select(Model).where(...)` SA 2.0 |
| `sa.Enum(..., create_type=True)` | Raw SQL `IF NOT EXISTS` + `VARCHAR(N)` column |
| `op.create_table()` non-idempotent | `op.execute("CREATE TABLE IF NOT EXISTS ...")` |
| Bulk_insert without ON CONFLICT | `op.execute("INSERT ... ON CONFLICT DO NOTHING;")` |
| `// eslint-disable-next-line` without justification | Refactor or document inline |
| `any` TypeScript type | `unknown` + type guard, or explicit type |
| `export default` (excepto Next.js pages) | Named exports |
| Hex colors literals `#10b981` | CSS vars `var(--agent-lisa)`, `var(--primary)`, `var(--destructive)` |
| PHI in URL query params | POST body or RBAC-derived from JWT (lisa-marca has zero PHI, but rule universal) |
| Audit log async fire-forget | Sync write via `AsyncAuditWriter` antes response |
| Inherit `PhiRepositoryBase` cuando no hay PHI directo | `Repository` base normal (defense via audit_log + sanitize universal) |
| Shadcn Tabs body for sub-sub-tabs | N3-static SubSubTabsBar cabecera (ADR-004 v1.1 § 3.1.1) |
| Single scroll multi-section cuando hay 3+ vistas discretas | N3-static SubSubTabsBar (idem) |
| Custom tab bar inside `{Agent}{Subtab}View.tsx` | SubSubTabsBar shared component |
| `print()` / `logging.info()` | `structlog.get_logger()` + `logger.info(event, **kwargs)` |
| `console.log` in production code FE | Remove pre-commit (ESLint rule) |
| Inline React Query keys | Centralized `marcaKeys.{...}()` factory |
| `make e2e` / `make e2e-smoke` (Docker, crashes) | Native: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test` |
| Modify `core/luana-core-*/src/` | escalate `/pm-luana` promotion proposal |
| Skip `response_model=` on FastAPI endpoint | mandatory per arch test `test_response_model_required.py` |
| Bypass `FastAPI(redirect_slashes=False)` | Already enforced en `main.py`; leave alone |
| `from src.modules.vitalia.X.domain import ...` cross-module | Use `shared/links/ports/` or DI |
| Enable visual extraction pipeline runtime | NEVER until `/pm-luana` accepts proposal 2026-05-26 |

---

## Test discipline (TDD-mandatory per `.claude/rules/tdd-mandatory.md`)

**Order RED → GREEN → REFACTOR per layer:**

1. **Domain** RED: `test_prohibited_phrase_domain.py` + `test_voice_preview_domain.py` (entities + enums + invariants) → GREEN: implement domain
2. **Infrastructure** RED: `test_prohibited_phrase_repository.py` + `test_trust_signal_repository.py` (CRUD + tenant filter + seed lookup) → GREEN: implement repos
3. **Application** RED: `test_marca_service.py` + `test_voice_preview_service.py` + `test_voice_blocklist_service.py` (orchestrator + cache + audit) → GREEN: implement services
4. **API** RED: `test_marca_router_*.py` (end-to-end FastAPI testclient with cross-tenant scenarios) → GREEN: wire routers
5. **FE**: store RED `marca-store.test.ts` → hook RED `useIdentityAutosave.test.ts` → component RED `IdentityCard.test.tsx` → E2E smoke

**Hook order (FE):** zustand store unit → React Query hook → component compose → page integration → E2E.

**No commit con tests rotos.** No `skip`/`xfail` para pasar CI. No reduce coverage sin justification.

---

## Mockup fidelity gate (★ `vitalia/.claude/rules/shell-mockup-per-component.md`)

- Cada subsubtab component debe alinearse a su mockup HTML ratificado:
  - `mockups/identidad-section.html` → `IdentidadView.tsx` + sub-components
  - `mockups/voz-tono-section.html` → `VozTonoView.tsx` + sub-components
  - `mockups/presencia-section.html` → `PresenciaView.tsx` + sub-components
  - `mockups/_shared.css` → tokens fielmente reproducidos en Tailwind classes
- Shell wrapper (TopBar + Ribbon + SubTabsBar + ValeriaChat-side + splitter) portado verbatim del canónico per `shell-mockup-per-component.md` § "Shell wrapper fidelity"
- Visual goldens (Playwright `toHaveScreenshot`) `maxDiffPixelRatio: 0.001` (0.1% tolerance)
- Ratchet shrink-only: una vez generado golden + ratificado, modificar requiere re-ratify explícito Chris

---

## Commit discipline (per `.claude/rules/git-safety.md`)

- Conventional Commits format: `<type>(<scope>): <desc>` — types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `wip`
- `<scope>` = `vitalia/f2-s7-marca` or finer (e.g., `vitalia/f2-s7-marca/voice-preview`)
- Body must include `## Decisions honored` section citing decision IDs from § 12 of `03-arch.md` (e.g., D1-arch, D2-voice, OQ-A, OQ-C, A4)
- Stage by exact filename — NUNCA `git add .` / `-A` / `-u`
- Branch destination: `wip/vitalia` (canonical worktree). Squash-merge to `main` post-auditor APPROVED + `/pm-vitalia` ratify
- Push >30min cumple M11
- Haiku delegation per `.claude/rules/git-haiku-delegation.md` cuando multi-file commits

---

## Definition of Done por ticket

Cada ticket `T-{n}` se considera done cuando:

1. ✅ Tests RED escritos primero (TDD) → GREEN tras impl
2. ✅ Validators de `04-validators.yaml` correspondientes a `acceptance.validator_ids` pasan GREEN
3. ✅ `gherkin_coverage` mapeo verificado en `06-tickets.yaml` (auditor Phase D ejecuta)
4. ✅ Spanish neutro pre-commit hook GREEN
5. ✅ Audit log row creado per mutation (defense-in-depth check)
6. ✅ Visual goldens generados (FE tickets touching UI)
7. ✅ Commit body cita `## Decisions honored` con D-IDs aplicables
8. ✅ `T-{n}-result.md` escrito con SHAs + `## Skills consulted (must_load enforcement v4.1)` section
9. ✅ Push wip/vitalia
