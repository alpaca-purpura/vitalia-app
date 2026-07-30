---
story_id: vitalia-fase2-lisa-servicios
surface: agentic
owner: builder-backend (Sub-phase A consume-only) / /pm-luana (Sub-phase B engine-lift)
auditor: auditor-backend (Sub-phase A) / n/a (Sub-phase B gated)
parent: 03-arch.md
---

# 03-arch-agentic — KEYSTONE consume-only (Sub-phase A) + RAG dimension (Sub-phase B gated)

> **Sub-phase A = consume-only, CERO engine edit, CERO sales_agent/copilot brand-extension code.** No es un ticket agentic-runtime → R23 (flagship) NO aplica a Sub-phase A. El único trabajo agentic real (Sub-phase B) es engine-lift `/pm-luana`.

## A. KEYSTONE (AC-6) — Sub-phase A · verificable LIVE

### A.1 Read path (engine-existing · verificado 2026-06-15)
`core/luana-core-sales-agent/.../application/services/knowledge_builder.py::TenantKnowledgeBuilder.build_identity(tenant_id)`:
```python
offer_repo = get_offer_repository(db)               # luana_core_platform.links.ports.offer
offers = offer_repo.get_all_by_tenant(tenant_id)    # engine OfferRepository (sync Session)
active = [o for o in offers if o.status.value in ("active", "draft")]
offers_data = [o.model_dump(mode="json") for o in active]
# → enriched con preset metadata (preset_label/description/flags) → agent_identity.j2
```

### A.2 Qué garantiza esta story (data shape, NO plomería nueva)
- Los servicios activos se persisten como engine `Offer`/`ProductModel` rows (D-1 en `03-arch-be.md`) con `status=active`, `archetype=SERVICIO`, `specific_details=ServiceDetails(session_duration_minutes,total_sessions_count)`, `value_level` (peldaño), `public_name`, `description` (voz marca), `preset_id`.
- → `build_identity` los recoge SIN tocar el engine ni escribir código agéntico nuevo.
- `SalesBrief` write-through a campos engine `Offer` existentes (D-2 · builder confirma `objection_handlers`/`anti_avatar_keywords`/`headline_promise`/`primary_outcome`) → Adrián cita el argumentario. Lo que no mapea (FAQ pairs, escalation_conditions, keywords/sinónimos para match) queda brand y lo consume canal-inbound (fuera de scope).

### A.3 Verificación LIVE (DoD #37 · NO GET 200)
1. dev-app vitalia: crear servicio + activar (`admin_clinic` real, write real).
2. query `products` → row status=active del tenant.
3. invocar Adrián / inspeccionar `build_identity(tenant_id)` output → el servicio aparece (public_name + descripción + value_level) y Adrián lo ofrece/cita.
4. leer logs (sin traceback). Evidencia → `dod_evidence`.

### A.4 Document → autocomplete (AC-11 · NOT RAG · Sub-phase A)
- Consume copilot `core/luana-core-copilot/.../tools/extract_from_doc.py` + `services/document_processor.py` (one-shot extractor, engine-existing) vía `DocExtractPort`.
- Crea `KnowledgeSource` engine row (status extraído). El `IRAGIndexerPort` **stub default binding** marca la fuente como indexada con chunk count sintético → la UI del panel Fuentes muestra estado "extraído"/"indexado" sin Qdrant real. CERO engine edit.
- El prefill es **editable** (la dueña lo revisa antes de guardar). El documento NO se indexa a RAG runtime en Sub-phase A.

## B. RAG runtime — Sub-phase B · ENGINE-LIFT `/pm-luana` · GATED (dimension only)

> **NO buildable tickets en este package.** Solo se dimensiona. La cadena autónoma de `/dev-team` PARA antes de B.

### B.1 Lo que falta (3 superficies engine)
- **(b)** Impl real de `core/luana-core-offer-studio/.../application/ports.py::IRAGIndexerPort` con binding Qdrant (hoy = stub). Reemplaza `index_source`/`reindex_source`/`delete_source` con el pipeline embeddings+Qdrant real (tenant-scoped collection).
- **(c)** sales_agent **offer-knowledge retrieval tool** en `core/luana-core-sales-agent/.../application/tools/` (hoy = payment/scheduling/registry; NO existe retrieval de offer-knowledge). Contrato: input `query + tenant_id + offer_id scope`; output `chunks comerciales con cita`; tenant-scoped; tool group `knowledge`.
- **(d)** RAG guards: **commercial-only** (no clínico libre) · **price-always-from-field** (anti-staleness — el precio sale del campo estructurado, NUNCA del documento) · **clinical→escalate-to-doctor** (contraindicación/diagnóstico/medicación) · **PHI scrub on ingest** (`sanitize_payload` HIPAA-lite).

### B.2 Promotion proposal a dimensionar (la finaliza `/pm-luana`)
Path: `docs/promotion-protocol/proposals/2026-06-15-offer-knowledge-rag-indexer-and-sales-agent-retrieval.md`.
Debe contener:
1. Las DOS superficies engine (IRAGIndexerPort real binding + sales_agent retrieval tool).
2. El contrato del retrieval tool (input/output/tenant-scope/guard hooks).
3. Los 4 guards (B.1.d) + cómo se enforzan (prompt + tool-level).
4. Goldens del sales_agent: 1 commercial-answer happy + 3 adversariales (precio-del-doc-rechazado · clínico-escala-al-doctor · PHI-scrub-on-ingest). Drift threshold `grader_score >= 0.85`.
5. Prompt cache slot: el contexto de offer-knowledge entra como slot per-tenant cacheable (no per-turn) si se inyecta estable; el resultado del retrieval es per-turn (NOT cached). Documentar TTL (default 5min) en la proposal.

### B.3 Routing (06-tickets + dispatch)
- `06-tickets.yaml`: Sub-phase B tickets → `phase: B-rag-engine-lift`, `status: blocked`, `blocked_on: "/pm-luana promotion proposal (IRAGIndexerPort impl + sales_agent retrieval tool)"`, `owner_eligibility: flagship` (R23 — agentic production).
- `dispatch-plan.md`: la cadena autónoma cubre **Sub-phase A ONLY** y STOP antes de B con nota explícita: "Sub-phase B requires /pm-luana engine-lift gate — produce promotion proposal, present to Chris, do NOT build without OK."
- `04-validators.yaml`: RN-17(b)/RN-22/AC-15(B)/§14(b)+adversariales → `verification_phase: B` / `deferred-pending-engine-lift` → el auditor + reconcile NO fallan Sub-phase A por su ausencia.

## C. Skill decisions referenced
- `sales-agent-expert`: keystone read shape confirmado (get_all_by_tenant + status active/draft). NO mirror. Sub-phase B retrieval tool = nuevo tool en engine sales_agent (flagship). Guards: price-from-field (anti-staleness), clinical-escalate, PHI-scrub.
- `copilot-expert`: extract_from_doc one-shot reusable (Sub-phase A). NO RAG indexing en A.
- `offer-expert`: KnowledgeSource engine per-offer + IRAGIndexerPort stub (A funciona; B = real binding).
- graceful-degradation: servicio activo sin doctores → agente degrada (responde, no matchea · RN-9 · SC-edge-sin-doctor). Document extract: timeout+fallback si extractor falla (prefill vacío editable, no rompe el workspace).
