# T-2 result — BE · offer services + RBAC + tenant + search/filters

story: vitalia-fase2-lisa-servicios · ticket: T-2 · surface: backend · agent: builder-backend (workhorse) · phase: A

## Verdict: DONE (state: tests-passing) · HTTP surface built — island closed

commit (service layer, prior): `aabcc502`
commit (HTTP surface REMAINDER, this run): `86fa8bdf` · branch: `wip/vitalia` (pushed `f55beb01..86fa8bdf`)

The T-2 service/domain/infra/repos/ports/adapters/KEYSTONE-factory were already GREEN & pushed
(82 offer tests). This run built the genuine remainder — the HTTP/API surface — closing the
anti-orphan island (offer/api previously held only `__init__.py`; CONN N-contention now MET).

## HTTP surface delivered (this run)
- **offer/api/dtos.py** — 24 Pydantic v2 DTOs. Response DTOs `ConfigDict(from_attributes=True)`
  whitelist allowlisted fields only (pii-sanitisation: no patient ids, no `tenant_id`/`clinic_id`
  leak in `CaseDTO`); request DTOs `ConfigDict(extra="forbid")`. Monetary fields
  `price: Decimal | None` + `currency: str | None` (never hardcode USD). No `Any`.
- **offer/api/servicios_router.py** — 16 endpoints, `response_model=` on EVERY route
  (`response_model=None` on the 4 DELETE/204 routes per arch gate `test_response_model_required`).
  Thin layer: validate DTO → service → map exception → HTTPException (no business logic in api/).
  DI mirrors canonical twin `brand_studio/api/routers/marca_router.py`
  (`_get_db` Annotated Depends `get_async_session_committing`, module-level `_build_service` →
  `_ServiceBundle(NamedTuple)`, `_resolve_audit_actor`, `_brand_owner_required`).
- **main.py** — `app.include_router(servicios_router, prefix="/api/v1/offer", tags=["offer"])`
  registered right after `marca_router` (Notarized — island closed).

### 16 endpoints
| # | Method | Path | Notes |
|---|---|---|---|
| 1 | GET | `/servicios` | list + server-side filters + keyset cursor (RN-15) |
| 2 | GET | `/servicios/{offer_id}` | detail (composes sales_brief + specialists + cases + testimonials); None→404 |
| 3 | POST | `/servicios/from-template` | 201; biblioteca.get_template (sync) → catalog.create_service (RN-16 DRAFT); RBAC |
| 4 | POST | `/servicios/custom` | 201; canonical_ref=None; RBAC |
| 5 | PATCH | `/servicios/{offer_id}` | None→404; RBAC |
| 6 | POST | `/servicios/{offer_id}/activate` | None→404; RBAC |
| 7 | DELETE | `/servicios/{offer_id}` | 204; get_service None→404 then soft_delete; RBAC |
| 8 | GET | `/biblioteca/search` | sync biblioteca.search (catalog NOT PHI, RN-13 — no X-Clinic-ID) |
| 9 | POST | `/servicios/{offer_id}/specialists` | 201; DoctorNotInRosterError→404; X-Clinic-ID; RBAC |
| 10 | DELETE | `/servicios/{offer_id}/specialists/{id}` | 204; X-Clinic-ID; RBAC |
| 11 | POST | `/servicios/{offer_id}/cases` | 201; ConsentNotSignedError→422 (RN-33); X-Clinic-ID; SYNC audit; RBAC |
| 12 | DELETE | `/servicios/{offer_id}/cases/{id}` | 204; X-Clinic-ID; RBAC |
| 13 | POST | `/servicios/{offer_id}/testimonials` | 201; RBAC |
| 14 | DELETE | `/servicios/{offer_id}/testimonials/{id}` | 204; RBAC |
| 15 | PATCH | `/servicios/{offer_id}/sales-brief` | model_dump(exclude_unset=True)→save; RBAC |
| 16 | POST | `/knowledge/extract` | ValueError→422; prefill DTO; RBAC |

### HTTP contract pins
- **Tenant isolation:** cross-tenant lookup → service returns None → router maps **404** (never 403, never foreign body — no existence leak). Pinned by `test_servicios_cross_tenant.py`.
- **RBAC:** writes require owner+admin_clinic via `require_brand_owner_access()` → **403** `{"error_code":"BRAND_OWNER_RBAC_DENIED"}`; reads open. Pinned by `test_servicios_rbac.py`.
- **HIPAA-lite Case (PHI):** `X-Clinic-ID` mandatory (dual filter) + consent gate RN-33 (`ConsentNotSignedError` → **422** BEFORE persist/audit) + SYNC audit write pre-response (no PHI in payload). PHI never in URL. Pinned by `test_case_consent_gate.py`.
- **Headers:** X-Tenant-ID (all), X-User-ID (audited writes), X-User-Role (RBAC, default ""), X-Clinic-ID (Case + specialist routes only — catalog NOT PHI per RN-13).

## Validator status
| validator_id | status | where |
|---|---|---|
| RN-10 (search/filters server-side) | ✅ GREEN | `catalog_service.list_*` + `test_catalog_service.py` |
| RN-15 (cursor pagination) | ✅ GREEN | `offer_ext_repository.list_by_tenant` tuple + GET `/servicios` `next_cursor` |
| RN-16 (create-on-choose = DRAFT not phantom) | ✅ GREEN | `medical_offer_factory` + from-template route |
| RN-23 / RN-33 (consent gate / proof) | ✅ GREEN | service + `test_case_consent_gate.py` (HTTP 422) |
| RN-13 (catalog not PHI — no clinic header) | ✅ GREEN | GET `/biblioteca/search` no X-Clinic-ID |
| RN-7 (RBAC on HTTP writes) | ✅ GREEN | `require_brand_owner_access()` + `test_servicios_rbac.py` (403) |
| NF-1 (response_model=) | ✅ GREEN | every route; `test_response_model_required` |
| NF-2 (tenant isolation) | ✅ GREEN | cross-tenant→None→404; `test_servicios_cross_tenant.py` |
| NF-3 (redirect_slashes / conventions) | ✅ GREEN | `FastAPI(redirect_slashes=False)` (main.py) |
| CONN (anti-orphan) | ✅ MET | include_router registered → Notarized + Navigable |

## Gate results (G5)
- `pytest tests/modules/vitalia/offer/` → **121/121 PASS** (was 82 service + 39 new HTTP/router/RBAC/cross-tenant/consent).
- arch fitness → **353 passed**; 1 PRE-EXISTING failure deselected: `test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted` → `treatment_plans.notes` lives in **fidelizacion** module (NOT offer — confirmed fails without my diff via stash of main.py; out of scope, FORBIDDEN to touch).
- `ruff check` + `ruff format --check` (offer/api + tests + main.py) → clean (21 files already formatted).
- cap bidirectional validator → G1-G9 HARD **0 drift**; verdict SOFT_DRIFT (1 soft drift in `compliance.hipaa-lite-defensive-stack` — pre-existing, unrelated to offer). `cap: lisa.servicios` resolves to `capabilities/offer_studio/medical-services-offer-preset.yaml` (functional_area matches).
- voseo scanner → clean (dtos.py + router carry `# voseo-allowed` for the `domain.vos` import; tests path-excluded).

## Skills consulted (must_load enforcement v4.1)
| Skill / rule | Status | When |
|---|---|---|
| backend-expert (runtime-quality-checklist) | ✅ consulted | FastAPI Annotated deps, response_model, SQLA, audit writer |
| offer-expert (references read) | ✅ consulted | engine Offer consume-via-import; no `_CATALOG_VERSION` bump |
| FastAPI canonical patterns | ✅ applied | Annotated Depends, response_model= every route, redirect_slashes=False |
| pytest async testing patterns | ✅ applied | httpx ASGITransport AsyncClient, `_build_service` mock, @pytest.mark.integration |
| .claude/rules/tenant-isolation.md | ✅ loaded | cross-tenant → None → 404 |
| .claude/rules/backend-ddd.md | ✅ loaded | api layer thin; map domain exception → HTTPException |
| .claude/rules/pii-sanitisation.md | ✅ loaded | response_model whitelist; CaseDTO no patient/tenant/clinic leak |
| vitalia/.claude/rules/hipaa-lite.md | ✅ loaded | X-Clinic-ID dual filter, consent gate 422, sync audit, no PHI in URL |
| .claude/rules/anti-orphan-integration.md | ✅ loaded | CONN N+navigable closed via include_router |
| .claude/rules/tdd-mandatory.md | ✅ loaded | RED HTTP tests precede router edits |

## Engine boundary
CERO edit of `core/luana-core-*/src`. Engine `Offer`/`OfferRepository`/`get_offer_repository` + `require_brand_owner_access` + iam resolvers consumed via import only. No cross-brand. `offer/{domain,application,infrastructure}` untouched (read-only consume, already DONE).

done -> vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/T-2-result.md
