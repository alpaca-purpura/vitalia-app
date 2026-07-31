<!-- voseo-allowed: glosario reference (forbidden voseo examples) -->
# 05-guidelines-template.md (★ v4.1 cement 2026-05-19)

> Owner: `/architect` orchestrator. Patterns concretos que el dev-team builder DEBE seguir/evitar — SIN AMBIGÜEDAD.
> Esta es la GUÍA TÉCNICA del builder. Si la sigue al pie + corre validators GREEN → ticket pasa auditoría.

---
story_id: STORY_ID
brand: BRAND_SLUG                                  # vitalia | nicolify | comunify | lupulo
arch_version: 1
last_modified: 2026-MM-DDTHH:MM:SSZ
---

## must_load_skills (★ v4.1 enforceable — builder MUST cargar todas + reportar "Skills consulted" en T-{n}-result.md)

> Builder spawn prompt cita esta lista verbatim. Si builder no carga + documenta → auditor CHANGES_REQUESTED automático (categoría: process discipline).

required:
  # Skills core obligatorios por surface
  - id: backend-expert
    when: "surface=BE o BE-test"
    purpose: "DDD patterns, arch fitness, currency, master-data, currency-handling"
  - id: frontend-expert
    when: "surface=FE"
    purpose: "FSD-Lite, Shadcn reuse, form-runtime, tailwind tokens"
  - id: "{domain}-expert"
    when: "module touched"
    options: [brand-expert, offer-expert, offer-type-preset-expert, metrics-expert, copilot-expert, sales-agent-expert]
    purpose: "Domain invariants + reference docs por módulo"
  - id: playwright-expert
    when: "test_construction_plan.playwright_required=true"
    purpose: "POM patterns, Clerk auth fixture, network mocking, smoke debugging"
  - id: chrome-devtools-verify
    when: "surface=FE o AGENTIC (live verification durante build/audit)"
    purpose: "Live-verify en dev-app — ejercer acción real, leer Console + Network + logs (DoD Critical Rule #37)"

  # Rules obligatorias siempre
  - id: ".claude/rules/definition-of-done-live-verify.md"
    purpose: "DoD Critical Rule #37 — ninguna story done sin ejercer la acción real en dev-app + dod_evidence"
  - id: ".claude/rules/tenant-isolation.md"
    purpose: "Every query filter tenant_id"
  - id: ".claude/rules/backend-ddd.md o frontend-fsd.md"
    purpose: "Layer boundaries según surface"
  - id: ".claude/rules/spanish-text.md"
    purpose: "Voseo glosario + magic comment escape"
  - id: ".claude/rules/anti-duplication.md"
    purpose: "Cross-brand mirror ban + shared abstractions inventory"
  - id: ".claude/rules/tdd-mandatory.md"
    purpose: "TDD RED→GREEN→REFACTOR discipline"
  - id: ".claude/rules/auditor-self-fix-policy.md"
    purpose: "Conocer qué findings auditor self-fix vs spawn dev-team (forward motion)"
  - id: ".claude/rules/git-safety.md"
    purpose: "Triple-branch policy + forbidden ops"

  # Canonical docs / patterns (WebFetch the canonical docs URL, or `tessl-context` skill if Tessl tiles are installed)
  - id: "FastAPI canonical patterns"
    when: "BE endpoint nuevo"
  - id: "pytest async testing patterns"
    when: "BE tests nuevos"
  - id: "React patterns baseline"
    when: "FE component nuevo"
  - id: "Shadcn UI conventions"
    when: "FE component nuevo (Shadcn reuse)"
  - id: "Tailwind conventions"
    when: "FE component nuevo (tokens)"
  - id: "Zod validation"
    when: "FE form con validation"
  - id: "Vitest conventions"
    when: "FE tests nuevos"
  - id: "Next.js App Router Server/Client split"
    when: "FE route nueva"
  - id: "LangGraph canonical docs"
    when: "AGENTIC surface"
  - id: "claude-api"
    when: "AGENTIC surface"

reference_artifacts:
  # Documentos del ready package que builder re-lee mid-build cuando surge ambigüedad
  - "{brand}/docs/product/stories/{story-id}/01-spec.md"               # Gherkin scenarios (re-read mid-build)
  - "{brand}/docs/product/stories/{story-id}/03-arch.md"               # Decisiones técnicas + § Test Construction Plan
  - "{brand}/docs/product/stories/{story-id}/04-validators.yaml"       # validators + test_construction_plan (orden + POMs + fixtures)
  - "{brand}/docs/product/stories/{story-id}/06-tickets.yaml"          # ticket entry T-{n} + gherkin_coverage

## Patterns required

### Backend (cuando surface=BE)

- SQLAlchemy 2.0 `select(Model).where(...)` — NUNCA `session.query()`
- All DB queries filter `tenant_id` (incluye `get_by_id`)
- Soft deletes only (`deleted_at`)
- Pydantic v2 `model_config = ConfigDict(...)` — NUNCA inner `class Config`
- `structlog` logging — NUNCA `print` / `logging`
- Migrations idempotentes (`IF NOT EXISTS` / `IF EXISTS`)
- FastAPI endpoints `response_model=` mandatory (PII allowlist)
- DateTime fields `timezone=True`
- `utc_now()` from `core/luana-core-platform/src/luana_core_platform/domain/datetime_utils.py` (no `datetime.utcnow()`)
- FastAPI app `redirect_slashes=False` (per backend-ddd.md)

### Frontend (cuando surface=FE)

- React Server Components default — `"use client"` solo cuando necesario
- React Query (TanStack) para data fetching
- RHF + Zod para forms
- Tailwind utility classes con tokens semánticos (no hex literals)
- Spanish neutro LatAm en TODA UI string (no voseo, no léxico regional)
- `useTenantLocale()` para currency / timezone (no hardcoded 'USD')
- Shadcn primitives reuse > new component

### Agentic (cuando surface=AGENTIC)

- LangGraph 2.0 `StateGraph` con state schema explícito
- Anthropic prompt caching slots (TTL 5min/1h según prompt_size)
- `copilot_trace_event` per turn (observability)
- `copilot_llm_call` per LLM call (cost recording)
- `sanitize_payload` ANTES de persistir (PII)
- Brand voice slot 5 cache prefix (sales_agent)
- Eval goldens RED first (TDD agentic)

## Patterns forbidden

- ❌ `datetime.utcnow()` — use `utc_now()`
- ❌ Hardcoded `'USD'` en monetary fields — use `tenant.currency`
- ❌ Cross-module imports (excepto `copilot` infra-like)
- ❌ Cross-brand imports (`from {other_brand}` HARD BAN)
- ❌ `session.query()` (SA 1.x)
- ❌ `sa.Enum()` en `op.create_table()` (broken SA 2.0.27)
- ❌ `op.create_table()` / `add_column()` / `create_index()` no idempotente
- ❌ `// eslint-disable` sin justification comment
- ❌ `any` en TypeScript (use `unknown` + type guards)
- ❌ Default exports (excepto Next.js pages)
- ❌ Hex colors hardcoded en components/styles
- ❌ Voseo (`vos/sos/tenés/podés`) en UI strings
- ❌ Hardcoded paths absolutos `/home/chris/...` — use `${WS}` resuelto

## Files in scope (Sonnet/Opus edits ONLY these — todos brand-scoped bajo {brand}/)

- {brand}/backend/src/modules/{brand}/{m}/api/routes.py
- {brand}/backend/src/modules/{brand}/{m}/application/services/...
- {brand}/backend/src/modules/{brand}/{m}/domain/...
- {brand}/backend/src/modules/{brand}/{m}/infrastructure/...
- {brand}/backend/alembic/versions/{timestamp}_{slug}.py (NEW migration brand-scoped)
- {brand}/backend/tests/modules/{brand}/{m}/test_{name}.py
- {brand}/frontend/src/features/{m}/...
- {brand}/frontend/src/app/{m}/page.tsx
- {brand}/frontend/e2e/regression/{story-id}/{m}-{type}.spec.ts (per test_construction_plan)
- {brand}/frontend/e2e/regression/{story-id}/poms/{m}-{page}.pom.ts
- {brand}/frontend/e2e/fixtures/{story-id}.fixture.ts
- {brand}/frontend/e2e/a11y/{story-id}.spec.ts
- {brand}/frontend/e2e/i18n/{story-id}.spec.ts

## Files Builder NEVER touches (escalate to Chris / /pm-vitalia)

- core/luana-core-*/src/luana_core_*/** (engine — cambios vía flujo engine /pm-vitalia, arch tests como gate; NUNCA en story brand-específica)
- {brand}/backend/src/modules/{brand}/{copilot,sales_agent}/** runtime (agentic — solo via builder-agentic Opus; brand-extension surface OK con R23 check)
- {brand}/backend/src/core/config.py (default flag flips require R31 anti-default-flip-audit)
- {brand}/frontend/src/components/ui/** (Shadcn primitives per-brand — extend via wrappers, no edit)
- {brand}/frontend/src/lib/api/fetchClient.ts (cross-cutting per-brand — escalate)
- .claude/** y {brand}/.claude/** (skill/rule edits — manual only by Chris/PM)
- docs/process/**, docs/architecture/**, docs/specs/** (paradigm change — manual only)

## Changelog

- v1 2026-05-06 — paradigm v4 inicial (post pm-redesign)
- v2 2026-05-19 — ★ v4.1 cement: must_load_skills enforceable + reference_artifacts explícito + paths brand-scoped
- v3 2026-06-02 — DoD #37: agrega `chrome-devtools-verify` skill + `.claude/rules/definition-of-done-live-verify.md` a must_load_skills
