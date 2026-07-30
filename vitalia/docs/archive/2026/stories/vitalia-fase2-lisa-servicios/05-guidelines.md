---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
architecture_pattern: ADR-vitalia-004
---

# 05-guidelines — vitalia-fase2-lisa-servicios

## Patterns REQUIRED

### Backend
- **Net-new `offer` module DDD Inside-Out** (domain → infrastructure → application → api). Inside-Out RED-first per layer.
- **Offer-core persiste como engine `ProductModel`** vía `luana_core_platform.links.ports.offer.get_offer_repository(db)` (D-1). El OfferExt brand-level en tablas `offer_service_*` con FK `offer_id`. **CERO edit de `core/luana-core-offer-studio`.**
- SQLAlchemy 2.0 async (`select(Model).where(...)`, `mapped_column()`). NUNCA `session.query()`.
- Pydantic v2 `model_config = ConfigDict(from_attributes=True)`. Sin `Any`. `response_model=` en TODA ruta.
- `tenant_id` en CADA query (incl `get_by_id`). Soft-delete (`deleted_at`).
- RBAC RN-7 (`@require_role(["admin_clinic","owner"])` write; resto 403).
- Currency de `tenant_locale` (TenantLocale VO). Monetary DTO `currency: str | None`. NUNCA hardcode.
- `Case` (PHI foto) → `CaseRepository` hereda `PhiRepositoryBase` + consent gate RN-33 + `write_audit_log_sync`.
- Cross-module: clinics doctor vía `DoctorRosterPort`; copilot extract vía `DocExtractPort`; lisa-marca voz vía `BrandVoicePort`. NUNCA raw cross-module import.
- Migrations idempotentes raw SQL (`IF NOT EXISTS`). NUNCA `op.create_table()` / `sa.Enum(create_type=True)`.
- EP-2 preset pack en `extensions.py::register_all` (materializar stub `presets=()`). NO bump `_CATALOG_VERSION` (brand preset, no engine catalog).
- `structlog`, NO `print`/`logging`.
- Telemetría `vitalia_growth_studio_event` bucketed (NO `copilot_trace_event`).

### Frontend
- COMPOSE del canon `@luana/ui-kit` 0.4.1 (`design-system-canon.md` §2). Server Components default; `"use client"` solo en root views.
- React Query (server data) + Zustand (UI-only) + URL state (subsubtab toggle). NO Redux/Context.
- RHF + Zod (`servicios-schema.ts` · discriminated union por `modality`). Autosave debounce 600ms (`use-autosave`) + UNA `FloatingAutosaveIndicator`. Sin botón Guardar (RN-20).
- `tenant_id` de `useTenantId()` — NUNCA `useAuth().orgId`. Routes incluyen `[tenantId]`.
- `AGENT_SUBSUBTABS["lisa.servicios"]` en `shell-routes.ts` (SSoT). NO Shadcn Tabs internas.
- N3 list/detail = `EntityWorkspaceLayout`+`EntitySubNavBar`. Toggle Catálogo|Escalera = N3-static `SubSubTabsBar`.
- `RichSelect` (ui-kit shipped) para RN-32. `@dnd-kit/core` para escalera. Shadcn `Tooltip` para RN-18.
- `cn()` de utils. Spanish neutro LatAm. Placeholders orientados al tipo de clínica (RN-24) sin forkear estructura (RN-19).

### Agentic (consume-only Sub-phase A)
- KEYSTONE = data shape (Offer activo en `products` → `build_identity` lo recoge). CERO engine edit, CERO sales_agent/copilot brand code.
- Document→autocomplete consume copilot `extract_from_doc` (one-shot, NOT RAG).
- graceful-degradation: servicio sin doctores → degrada; extract timeout → prefill vacío editable.

## Patterns FORBIDDEN
- ❌ Editar `core/luana-core-*/src` o `@luana/ui-kit/src` → escalate `/pm-luana` (es Sub-phase B RAG + NumberWithUnit lift, ambos diferidos/gated).
- ❌ Crear `Treatment`/`LadderSlot` model nuevo (el catálogo = Offer engine; peldaño = OfferValueLevel).
- ❌ Mirror del Offer-core en tabla brand (rompe keystone — el agente no lo leería).
- ❌ Cross-brand code (NUNCA `comunify/`/`nicolify/`). comunify offer_ladder = STUDY only.
- ❌ `<select>` nativo · arbitrary Tailwind values (hex/px) · Shadcn Tabs internas para sub-secciones.
- ❌ Botón "Guardar" (RN-20 autosave). Más de UNA FloatingAutosaveIndicator.
- ❌ `useAuth().orgId` como tenant_id (no-clerk-organizations). PHI en URL.
- ❌ Construir Sub-phase B (RAG) sin `/pm-luana` engine-lift OK.
- ❌ Hardcode `'USD'`/`'S/'`. `datetime.utcnow()`.

## Files IN SCOPE (Sub-phase A)
### Backend (NEW module)
- `vitalia/backend/src/modules/vitalia/offer/domain/{enums,vos,offer_ext,sales_brief,specialist_link,proof,completeness,pricing_calc}.py`
- `vitalia/backend/src/modules/vitalia/offer/infrastructure/models/{offer_service_ext,specialist_link,case,testimonial,sales_brief}_model.py`
- `vitalia/backend/src/modules/vitalia/offer/infrastructure/repositories/*.py`
- `vitalia/backend/src/modules/vitalia/offer/application/{services,ports}/*.py`
- `vitalia/backend/src/modules/vitalia/offer/api/{servicios_router,dtos}.py`
- `vitalia/backend/src/modules/vitalia/offer/persistence/migrations/XXXX_offer_service_tables.py`
- `vitalia/backend/src/modules/vitalia/extensions.py` (MODIFY · EP-2 preset pack materialize)
- main router include (offer router mount)
- `vitalia/backend/tests/modules/vitalia/offer/*.py`
### Frontend
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/{page,[subsubtab]/page,[offer-id]/{layout,[leaf]/page},nuevo/page}.tsx`
- `vitalia/frontend/src/features/lisa/components/servicios/*.tsx` (+ `__tests__/`)
- `vitalia/frontend/src/features/lisa/api/{servicios,servicios-server}.ts` · `hooks/` · `store/servicios-ui-store.ts` · `types/{servicios.types,servicios-schema}.ts`
- `vitalia/frontend/src/components/shared/NumberWithUnit.tsx` (NEW vitalia-local shared)
- `vitalia/frontend/src/lib/shell-routes.ts` (MODIFY · AGENT_SUBSUBTABS append)
- `vitalia/frontend/e2e/shell-organism/lisa-servicios-*.spec.ts` + `e2e/__screenshots__/servicios/*.png`

## Files NEVER TOUCH
- `core/luana-core-*/src/**` (engine · lift-gate `/pm-luana`)
- `core/@luana/ui-kit/src/**` (lift-gate · NumberWithUnit lift diferido)
- `vitalia/frontend/src/components/ui/**` (Shadcn primitives) · `components/shared/shell-organism/**` (shell chrome shipped)
- `{nicolify,comunify,lupulo,saasora,...}/**` (otras brands)
- Sub-phase B engine surfaces (IRAGIndexerPort impl, sales_agent retrieval tool) sin /pm-luana OK

## must_load_skills (enforceable · por surface)
### Backend tickets
- `backend-expert`, `offer-expert`, `offer-type-preset-expert` (EP-2 preset pack), `tenant-isolation`, `backend-ddd`, `backend-migrations`, `spanish-text`, `anti-duplication`, `tdd-mandatory`, `currency-handling`, `vitalia/.claude/rules/hipaa-lite.md` (Case consent)
### Keystone ticket (consume-only data)
- `backend-expert`, `sales-agent-expert` (read shape — NO escribir agentic), `offer-expert`, `anti-duplication`, `tdd-mandatory`, `definition-of-done-live-verify`
### Frontend tickets
- `frontend-expert`, `vitalia-design-system`, `docs/architecture/luana-platform/design-system-canon.md`, `frontend-visual-fidelity`, `frontend-fsd`, `playwright-expert`, `chrome-devtools-verify` (live-verify), `spanish-text`, `anti-duplication`, `tdd-mandatory`, `tenant-isolation` (FE), `definition-of-done-live-verify`, `ADR-vitalia-004`, `brand-expert`+`offer-expert` (domain surface)

## reference_artifacts
- `03-arch.md` (+ `03-arch-be.md` · `03-arch-fe.md` · `03-arch-agentic.md`)
- `01-spec.md` (§ Mapa funcional · § Gherkin · § Matriz · § Mapa de campos · § Inventario de componentes)
- `00-research.md` (reframe SSoT)
- `mockups/{catalogo,escalera,servicio-workspace,nuevo-servicio}.html` + `_shared.css`
- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` · `ADR-vitalia-003`
- `docs/architecture/luana-platform/design-system-canon.md`
- `vitalia/.claude/rules/{hipaa-lite,shell-feature-architecture-mandatory,shell-mockup-per-component}.md`
- Engine ground truth: `core/luana-core-offer-studio/.../domain/{offer,enums,details}.py` · `.../knowledge_builder.py` · `core/@luana/ui-kit/src/{rich-select,EntityWorkspaceLayout,EntitySubNavBar}.tsx`
