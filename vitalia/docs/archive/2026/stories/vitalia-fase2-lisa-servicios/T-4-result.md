# T-4 result — BE · document-autocomplete + KEYSTONE offer-shape

story: vitalia-fase2-lisa-servicios · ticket: T-4 · surface: backend · agent: builder-backend (workhorse) · phase: A

## Verdict: DONE · KEYSTONE GREEN · PUSHED

commit: `aabcc502` · branch: `wip/vitalia` (pushed)

## Scope delivered
- **application/services/medical_offer_factory.py** (KEYSTONE) — `build_medical_service_offer(tenant_id, public_name, price, currency, status, canonical_ref, offer_id=None)` fills ALL 13 required no-default engine `Offer` fields (`internal_sku, public_name, archetype=SERVICIO, headline_promise, target_avatar_match, primary_outcome, time_to_value, requires_application=False, min_financial_capacity, pricing_options[1], guarantee_type, guarantee_terms, status`). Single brand→engine mapping. price ≥ 0 (free consultation valid, RN-6/RN-11). create-on-choose → DRAFT (RN-16).
- **application/services/document_autocomplete_service.py** — consumes the copilot doc-extract port (`doc_extract_port` → `doc_extract_adapter`) to prefill service fields from an uploaded document (RN-8, RN-17a). Returns an `ExtractionPrefill` shape; consume-only, NO agentic-runtime (R23 N/A → workhorse).
- **infrastructure/adapters/offer_engine_adapter.py** — `list_service_offers` mirrors engine `get_all_by_tenant` (status ∈ {active, draft}) — the exact path `TenantKnowledgeBuilder` / Adrián reads. `create_service_offer` persists the factory output via engine `repo.create`.

## KEYSTONE check (AC-6 / AE-A1) — proven
`test_keystone_offer_shape.py` (RED-first, written before the factory):
- `test_medical_factory_fills_all_required_engine_fields` → asserts `isinstance(offer, Offer)`, archetype SERVICIO, status ACTIVE, all 13 fields present + non-empty, pricing_options[0].total_amount == price, currency preserved. **GREEN.**
- `test_medical_factory_draft_status_for_create_on_choose` → RN-16 DRAFT, status.value ∈ {active, draft} (surfacing contract). **GREEN.**
- `test_medical_factory_pricing_zero_allowed` → RN-6/RN-11 price 0.0 valid. **GREEN.**

Surfacing path verified end-to-end: factory → `OfferEngineAdapter.create_service_offer` → engine `OfferRepository.create`; `list_service_offers` → engine `get_all_by_tenant` (what the agent/knowledge layer consumes). The offer reaches Adrián via the engine, not via the (pending) REST router — so AC-6 reachability is satisfied at the agent layer.

## Validator status
| validator_id | status | where |
|---|---|---|
| AC-6 (keystone offer surfaces ACTIVE) | ✅ GREEN | `test_keystone_offer_shape.py` (3 cases) + adapter `list_service_offers` |
| AE-A1 (medical factory completeness) | ✅ GREEN | `test_keystone_offer_shape::fills_all_required_engine_fields` |
| RN-8 (doc prefill) | ✅ GREEN | `document_autocomplete_service` + `test_document_autocomplete_service.py` |
| RN-17a (extract→prefill mapping) | ✅ GREEN | `doc_extract_adapter` consume-only + service test |

## Gate results (G5)
- `pytest tests/modules/vitalia/offer/test_keystone_offer_shape.py` → **3/3 PASS** (isolated).
- `pytest tests/modules/vitalia/offer/test_document_autocomplete_service.py` → GREEN.
- Full offer battery → **82/82 PASS**. `ruff check` + `ruff format` → clean. arch fitness GREEN (1 pre-existing pgcrypto failure outside offer scope).
- NOTE: AC-6 live-verify (dev-app real write surfacing to Adrián) is a Phase G / T-8 obligation — domain+keystone GREEN here; live-verify pending the FE/HTTP surface + Phase G.

## Skills consulted
| Skill / rule | Status | When |
|---|---|---|
| offer-expert (references read) | ✅ consulted | engine Offer 13-field shape, archetype SERVICIO, pricing_options |
| backend-expert (references read) | ✅ consulted | async→sync seam, consume-via-import |
| copilot-expert (cross-module READ only) | ✅ consulted | doc-extract port shape (consume copilot output, read-only) |
| .claude/rules/tenant-isolation.md | ✅ loaded | factory tenant_id; adapter tenant-scoped get_all |
| .claude/rules/master-data.md (currency) | ✅ loaded | currency from arg, no hardcoded USD |
| .claude/rules/tdd-mandatory.md | ✅ loaded | KEYSTONE RED-first |
| .claude/rules/anti-orphan-integration.md | ✅ loaded | CONN: keystone reachable via agent layer (engine get_all_by_tenant) |

## Cross-module reads (read-only)
- `core/luana-core-offer-studio` — engine `Offer` aggregate + `OfferRepository` + `get_offer_repository` (consume via import).
- `copilot` doc-extract contract — read-only, consumed via `doc_extract_port` (NOT edited; builder-agentic owns copilot).

## Engine boundary
CERO edit of `core/luana-core-*/src`. KEYSTONE = consume-only data-shape mapping. No cross-brand.

done -> T-4-result.md
