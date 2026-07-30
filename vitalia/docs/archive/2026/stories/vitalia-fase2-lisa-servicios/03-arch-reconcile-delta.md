---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
mode: RECONCILE-DELTA          # NOT a fresh ready-package; widens the closed ready-package
base_ready_package: [03-arch.md, 03-arch-be.md, 03-arch-fe.md, 04-validators.yaml, 06-tickets.yaml, dispatch-plan.md]
arch_version: 1.delta1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
architect_run_on: 2026-06-16
origin: "G round 1 scope-delta ratified by Chris (chris-input.md 2026-06-16 entry). Workspace 'horrible' (flattened collapsibles, dead fields)."
---

# Reconcile delta — vitalia-fase2-lisa-servicios (G round 1)

> **Scope discipline:** this delta designs ONLY the gap Chris ratified in G. It does NOT
> re-open the closed ready-package. The 8 Sub-phase-A tickets stay as-is; this adds T-R0..T-R3.
> Sub-phase B (RAG) remains BLOCKED behind `/pm-luana`. Read the base `03-arch-be.md` / `03-arch-fe.md`
> for everything not touched here.

## 0. Context summary

- **Story state:** `developed · phase: AWAIT_CHRIS_VERIFY` (past-ready). This delta does NOT transition checkpoint state.
- **Three gaps ratified by Chris in G** (mirror `dod_open_findings`):
  - **F1 (medium · FE wiring):** `ServiceStatusBar` orphan — workspace has no Activo toggle / origin chip / completeness chip.
  - **F2 (HIGH · BE contract gap):** `ServicePatchRequest` accepts only 4 fields → the rich ficha fields (description, includes, procedure, results, risks, aftercare…) can't be saved or read.
  - **F3 (low · BE):** `appointment_type` (`initial_appt_type`) doesn't persist.
- **Architectural reframe of F2 (verified against real code, 2026-06-16):**
  - The rich persistence is ALREADY built brand-local: `OfferExt` domain (`offer/domain/offer_ext.py`, 16+ rich fields) + `OfferServiceExtModel` (40 cols) + `offer_ext_repository.py` (serialize/deserialize all). **CERO engine lift.**
  - The hole is **the API on BOTH directions**: (a) write — `ServicePatchRequest` (`offer/api/dtos.py:243`) + `catalog_service.patch_service()` only route `category`/`modality` to OfferExt; (b) **read — `ServiceView` (`catalog_service.py:51`) AND `ServiceDetailDTO` (`dtos.py:133`) DON'T carry the rich fields either**, so the FE GET response never receives them to hydrate. F2 fix MUST widen read + write.
  - **F3 folds into F2** — `initial_appt_type` already on OfferExt; same PATCH-fat fix routes it.

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Ticket | Builder | Auditor |
|---|---|---|---|
| `core/@luana/ui-kit/src/CollapsibleSection.tsx` (ENGINE molecule) | **T-R0** | **`/pm-luana` promotion gate** (NOT a vitalia builder) | n/a (gated by promotion proposal) |
| `vitalia/backend/src/modules/vitalia/offer/{api,application}/` | **T-R1** | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/frontend/src/features/lisa/components/servicios/workspace/` | **T-R2** | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
| `vitalia/frontend/src/features/lisa/components/servicios/leaves/ResumenView.tsx` + shell | **T-R3** | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |

- **Skills consulted:** `backend-expert` (ServicePatchRequest widening + VO DTO shapes + read-path widening) · `offer-expert` (OfferExt is the brand projection; rich fields = OfferExt setters, NOT engine Offer) · `frontend-expert` + `vitalia-design-system` + `frontend-visual-fidelity` (CollapsibleSection composes the canon; ResumenView hydration + autosave) · `sales-agent-expert` (knowledge_builder reads engine Offer not OfferExt → enrichment is a follow-up, see §B).
- **CONTEXT-BRIEF source:** base ready-package CONTEXT-BRIEF.md (validated) consumed at original ready close; this delta re-verified premises [A]/[C]/[D] directly against real code (greps + reads, 2026-06-16). No new NO-NEW-LAYER scan needed — F2 is EXTEND of existing OfferExt+repo (zero new layer).
- **capability YAML affected (post-merge):** `vitalia/docs/product/capabilities/offer/lisa.servicios.yaml` — `cap_change_type: extend` (rich ficha fields now persistible + read; collapsible UX). `dev_preview.main_component` unchanged (workspace). No new cap.
- **Architecture gates that must keep passing:** `vitalia/backend/tests/architecture/{test_response_model_required.py, test_phi_dual_filter.py (n/a — catalog not PHI), no-engine-edit, DDD boundaries}` + `vitalia/frontend/src/__tests__/architecture/{test_features_no_cross_imports, no-arbitrary-values, no-div-layout, test-no-clerk-organizations}`.

---

## Existing systems audit (NO-NEW-LAYER rule)

### Source of evidence
- [x] Self-run greps + reads (Path B) — re-verified 2026-06-16 against real code (premises [A]/[C]/[D] confirmed).

### Audit cross-module ejecutado
```
read offer/domain/offer_ext.py        → OfferExt models all 16+ rich fields (description_long, includes,
                                          excludes, warranty, variants[ServiceVariant], procedure_steps,
                                          anesthesia_pain, prep, aftercare, downtime, expected_result,
                                          result_timing, result_lifespan, realistic_expectations, risks,
                                          red_flags, session_interval[ValueWithUnit], recurrence_interval,
                                          initial_appt_duration_minutes:int, initial_appt_type[enum], pricing[ThreeChargePricing])
read offer/domain/vos.py + enums.py   → ServiceVariant / ValueWithUnit / ThreeChargePricing / InitialApptType all exist
grep patch_service catalog_service.py → routes ONLY category/modality → OfferExt; public_name/price → engine
read ServiceView + ServiceDetailDTO   → NEITHER carries rich fields (read-path gap, NOT just write)
grep _ext.update                       → repo.update(ext) already persists the full OfferExt aggregate
grep ui-kit index.ts                  → accordion + collapsible + Group already exported from @luana/ui-kit
ls vitalia/frontend/.../components/ui/accordion.tsx → DUP local accordion (deleted when CollapsibleSection consumed)
```

### Sistemas existentes encontrados
| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `OfferExt` aggregate (rich fields) | `offer/domain/offer_ext.py` | active · complete | **EXTEND** (route new fields via setters) |
| `OfferServiceExtModel` (40 cols) | `offer/persistence/offer_service_ext_model.py` | active · complete | **CONSUME** (no migration — cols exist) |
| `offer_ext_repository.update()` | `offer/infrastructure/offer_ext_repository.py` | active · serializes all | **CONSUME** (no repo change) |
| `ServicePatchRequest` (4 fields) | `offer/api/dtos.py:243` | active · narrow | **EXTEND** (widen to all patchable fields) |
| `ServiceView` / `ServiceDetailDTO` | `catalog_service.py:51` / `dtos.py:133` | active · narrow | **EXTEND** (widen read to carry rich fields) |
| `@luana/ui-kit` accordion + collapsible + Group | `core/@luana/ui-kit/src/{accordion,collapsible,Group}.tsx` | active · exported | **COMPOSE** (CollapsibleSection composes them — T-R0) |
| `vitalia/.../components/ui/accordion.tsx` | local dup | active · orphan-ish | **DELETE** on T-R3 (consume ui-kit CollapsibleSection) |

### Decisión por sistema
- **OfferExt + repo (write):** EXTEND — `patch_service()` gains the rich kwargs, routes each to the corresponding `ext.<attr>` setter, then `await self._ext.update(ext)`. No migration, no new repo method.
- **ServiceView + ServiceDetailDTO (read):** EXTEND — both widen to carry the rich fields so the GET response hydrates the FE. This is the corrected read-path half of F2 (premise [A] only named the write half).
- **CollapsibleSection:** the molecule does NOT exist yet → composes existing ui-kit primitives. Lives in `core/@luana/ui-kit` (Chris ratified home → cross-brand reuse). NEW file BUT in core → **/pm-luana promotion gate** (T-R0, NOT a vitalia ticket).
- **No NEW layer, no cross-brand mirror.** F2 is pure EXTEND of brand-local code. CollapsibleSection lift is the only core change → covered by promotion proposal.

---

## Part A — BE contract widening (F2 + F3) · ticket T-R1

> Owner: `builder-backend` (workhorse). Auditor: `auditor-backend` (flagship). CERO engine edit.

### A.1 VO DTO shapes (Pydantic v2 — design the VO forms, NOT str)

The rich PATCH must accept the value-objects in DTO form. Add to `offer/api/dtos.py`:

```python
class ValueWithUnitDTO(BaseModel):
    """RN-31 — typed numeric interval (value >= 1) with a unit. Mirrors domain ValueWithUnit."""
    model_config = ConfigDict(from_attributes=True)
    value: int = Field(ge=1)
    unit: IntervalUnit            # StrEnum: dias|semanas|meses|anios

class ServiceVariantDTO(BaseModel):
    """RN-29/RN-11 — named price variant. Mirrors domain ServiceVariant."""
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(min_length=1)
    price: Decimal = Field(ge=0)
    note: str | None = None

class ReservationConfigDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enabled: bool
    amount: Decimal | None = None
    kind: ReservationKind         # monto|porcentaje

class AdvanceConfigDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enabled: bool
    amount: Decimal | None = None
    kind: ReservationKind

class FinancingConfigDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    offered: bool
    installments: int | None = None      # service raises if offered and < 1 (RN-11)
    interest_kind: str | None = None
    finance_partner: str | None = None

class ThreeChargePricingDTO(BaseModel):
    """RN-6 — headline price + 3 independent charges. Mirrors domain ThreeChargePricing."""
    model_config = ConfigDict(from_attributes=True)
    price: Decimal | None = None
    price_mode: PriceMode                 # fijo|rango
    price_publishable: bool
    currency: str | None = None           # from tenant_locale — NEVER hardcode 'USD'
    reservation: ReservationConfigDTO | None = None
    advance: AdvanceConfigDTO | None = None
    financing: FinancingConfigDTO | None = None
```

VO mapping at the service boundary (DTO → frozen domain VO): build the frozen `ValueWithUnit`/`ServiceVariant`/`ThreeChargePricing` from the DTO inside the service, so domain `__post_init__` invariants (price>=0, value>=1, installments>=1) still enforce. ValueError → 422 (router maps).

### A.2 ServicePatchRequest — widen to ALL patchable OfferExt fields (per-field autosave, all Optional)

```python
class ServicePatchRequest(BaseModel):
    """Per-field autosave (RN-20). All optional — last-write-wins per field.
    Widened (G reconcile) to expose the full editable ficha (RN-26 §6)."""
    model_config = ConfigDict(extra="forbid")

    # — existing (keep) —
    public_name: str | None = Field(default=None, min_length=1)
    price: Decimal | None = None
    category: str | None = None
    modality: ServiceModality | None = None
    # — Qué es —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariantDTO] | None = None        # RN-29
    # — Procedimiento (RN-26) —
    procedure_steps: str | None = None
    anesthesia_pain: str | None = None
    prep: str | None = None
    aftercare: str | None = None
    downtime: str | None = None
    # — Resultados —
    expected_result: str | None = None
    result_timing: str | None = None
    result_lifespan: str | None = None
    realistic_expectations: str | None = None
    # — Riesgos —
    risks: str | None = None
    red_flags: str | None = None
    # — Modalidad y agenda —
    session_interval: ValueWithUnitDTO | None = None       # if modality=sesiones
    recurrence_interval: ValueWithUnitDTO | None = None     # if modality=recurrente
    initial_appt_duration_minutes: int | None = Field(default=None, ge=1)
    initial_appt_type: InitialApptType | None = None        # F3 — RN-32
    pricing: ThreeChargePricingDTO | None = None            # RN-6
    candidate_for_library: bool | None = None               # RN-27
```

**`extra="forbid"` preserved.** Per-field autosave semantics: the FE sends a single-key patch per change (existing `usePatchField`); each Optional defaults None → only the present key is applied (last-write-wins). The `value_level` move-rung gap stays out (escalera surface, documented elsewhere — NOT in this delta).

### A.3 `catalog_service.patch_service()` — route the new fields → OfferExt setters

Widen the signature (all new params `| None = None`) and apply present fields to `ext`, then `await self._ext.update(ext)` (already the pattern). Sketch:

```python
async def patch_service(self, *, tenant_id, offer_id, public_name=None, price=None,
                        category=None, modality=None,
                        # widened — rich ficha (G reconcile)
                        description_long=None, includes=None, excludes=None, warranty=None,
                        variants=None, procedure_steps=None, anesthesia_pain=None, prep=None,
                        aftercare=None, downtime=None, expected_result=None, result_timing=None,
                        result_lifespan=None, realistic_expectations=None, risks=None, red_flags=None,
                        session_interval=None, recurrence_interval=None,
                        initial_appt_duration_minutes=None, initial_appt_type=None,
                        pricing=None, candidate_for_library=None) -> ServiceView | None:
    ext = await self._ext.get_by_offer(offer_id, tenant_id=tenant_id)
    if ext is None: return None
    # apply only present fields (None = not in this autosave patch → don't clobber)
    if category is not None: ext.category = category
    if modality is not None: ext.modality = modality
    if description_long is not None: ext.description_long = description_long
    # ... str fields identically ...
    if variants is not None: ext.variants = [v.to_domain() for v in variants]   # frozen VO build
    if session_interval is not None: ext.session_interval = session_interval.to_domain()
    if recurrence_interval is not None: ext.recurrence_interval = recurrence_interval.to_domain()
    if initial_appt_type is not None: ext.initial_appt_type = initial_appt_type
    if pricing is not None: ext.pricing = pricing.to_domain()
    if candidate_for_library is not None: ext.candidate_for_library = candidate_for_library
    ext = await self._ext.update(ext)
    if public_name is not None or price is not None:
        await self._engine.update_service_offer(tenant_id=tenant_id, offer_id=offer_id,
                                                 public_name=public_name,
                                                 price=float(price) if price is not None else None)
    offer = await self._engine.get(tenant_id=tenant_id, offer_id=offer_id)
    if offer is None: return None
    return _view(offer, ext)
```

> **Routing decision (PATCH-fat over per-group endpoints):** widen the EXISTING `PATCH /servicios/{offer_id}` (it is ALREADY per-field autosave — the FE sends one key at a time). NO new per-group endpoints. Coherent with EXTEND > NEW. Router handler maps `request.model_dump(exclude_unset=True)` → service kwargs; VO DTOs `.to_domain()` at the boundary. `exclude_unset=True` is critical so absent keys never overwrite stored values.

### A.4 Read-path widening (corrected F2 half — the FE must RECEIVE the values)

The GET response (`ServiceDetailDTO`) and the read model (`ServiceView`) must carry the rich fields, else the FE has nothing to hydrate.

- **`ServiceView`** (`catalog_service.py:51`) — add the rich fields from `ext` (frozen dataclass; add attrs mirroring OfferExt). `_view(offer, ext)` populates them from `ext.*`.
- **`ServiceDetailDTO`** (`dtos.py:133`) — add the same rich fields (DTO shapes from §A.1 for VOs; str/int/enum directly). `_detail_dto()` populates from `view`. `response_model=ServiceDetailDTO` already on the route → fields auto-whitelist; catalog is NOT PHI (RN-13) so no PII concern.
- TS mirror (`ServiceDetail`) updates land in T-R3 (FE) — camelCase? NO: this codebase mirrors snake_case BE field names verbatim in the TS interfaces (see existing `ServiceDetail` / `description_long`). Keep snake_case in the TS mirror for consistency with the shipped contract.

### A.5 Tenant isolation / currency / locale (unchanged invariants)
- Every query already filters `tenant_id` (incl. `get_by_offer`). No new query.
- `pricing.currency` + `variants[].price` keep `currency: str | None` — never hardcode `'USD'`.
- `initial_appt_duration_minutes` is an int (minutes), no datetime. No UTC concern.

---

## Part B — Adrián knowledge enrichment — **DECISION: follow-up story, NOT this delta**

`core/luana-core-sales-agent/.../knowledge_builder.py::TenantKnowledgeBuilder.build_identity()` reads the engine `offer_repo` (engine Offer), NOT the brand-local `OfferExt` → Adrián does not see the rich ficha.

**Decision: EXCLUDE from this delta. Flag as follow-up story.** Justification:
1. **KEYSTONE AC-6 already works** with the engine Offer (live-verified: offer active in `products`, tenant-scoped, consumed by `build_identity`). Adrián CAN already answer about the service; he just lacks the rich detail.
2. **Enrichment is an enhancement, not a fidelity bug.** The G ratified scope is "workspace horrible / dead fields" — a UI+persistence fidelity problem. Adrián's depth is a separate value-add.
3. **Surface mismatch:** the override touches `sales_agent` runtime behavior reading a brand projection → that is agentic/`flagship` territory and likely a brand-local override of an engine builder (consume-only port or extension). Bundling it inflates this UI reconcile into an agentic change with its own goldens + voice-fidelity gates — out of scope for a G fidelity fix.
4. **No blocker:** T-R1's read-path widening makes the rich fields available via the API; a future story can wire a vitalia-local `build_identity` override (joining OfferExt by `offer_id`) cleanly once the data is API-reachable.

→ **Follow-up:** `vitalia-fase2-adrian-ficha-rica-knowledge` (idea) — vitalia-local override of `build_identity` joining OfferExt rich fields into Adrián's identity context. Owner: `builder-agentic` (flagship) when refined. The `/pm-vitalia` reconcile (R) spawns this as a visible story from the ledger.

## Follow-ups (deferred from this delta — /pm-vitalia reconcile R spawns as visible stories)
1. `vitalia-fase2-adrian-ficha-rica-knowledge` (idea · agentic) — Adrián knowledge enrichment (§ Part B).
2. `vitalia-fe-accordion-dedup-cleanup` (idea · bugfix) — repoint `features/mateo` agenda components off the local `components/ui/accordion.tsx` to `@luana/ui-kit` + delete the dup (§ C.2.5). Deferred to avoid cross-feature scope creep.

---

## Part C — FE fidelity (F1 + ResumenView) · tickets T-R2 + T-R3

> Owner: `builder-frontend` (workhorse). Auditor: `auditor-frontend` (flagship). Design-system-canon HARD.

### C.1 (T-R2) F1 — ServiceStatusBar inside the Shell + resolve orphan View

**Decision (already taken, ratified):** do NOT re-wire `layout.tsx` → `ServicioWorkspaceView` (that would break the G2 store-free SSR-safe layout — the layout is a pure Server Component by design, comment in the file). Instead render `ServiceStatusBar` **inside** `ServicioWorkspaceShell`, above `{children}`, sticky.

- `ServicioWorkspaceShell` ALREADY has `servicio` (from `useServicioDetail`) + `offerId`. Add `useActivateServicio()` and render `<ServiceStatusBar servicio={servicio} onToggleActive={...} isToggling={...} />` immediately before `{children}` inside the `EntityWorkspaceLayout` body.
- `ServiceStatusBar` already accepts `{ servicio, filledCount, totalCount, missingFields, onToggleActive, isToggling }` and renders Switch + ChipOrigen + FichaCompletenessChip. Pass completeness from the servicio detail (compute filled/total from the rich fields now available post-T-R1, or pass through if a completeness field exists).
- **Resolve the orphan `ServicioWorkspaceView.tsx`:** it currently duplicates exactly this (mounts ServiceStatusBar as a child of the Shell). Since the Shell now owns the StatusBar, **DELETE `ServicioWorkspaceView.tsx`** (it is unreferenced by `layout.tsx`). Remove its export from `features/lisa/index.ts` if present, and its `__tests__` for that component (or repoint to the Shell). Verify with grep that nothing imports it before deleting.
- Sticky: `ServiceStatusBar` already has `sticky top-0 z-10 border-b bg-card` — keep.

### C.2 (T-R3) ResumenView fidelity — consume CollapsibleSection + hydrate + autosave + conditionals + KnowledgeSourcesPanel

Gated on **[T-R0 accepted/built]** (CollapsibleSection in ui-kit) + **[T-R1]** (BE fields readable + patchable).

**C.2.1 — 6 collapsible groups (mockup `servicio-workspace.html:497`).** Replace the 6 flat `<Group>` with `<CollapsibleSection>` (from `@luana/ui-kit`, T-R0):
- Order + default-open per mockup: **Identidad → defaultOpen; Qué es / El procedimiento / Resultados / Riesgos / Modalidad y agenda → closed.**
- Each section header: title + field-count summary ("N campos") + agent accent (`accentVar="--agent-lisa"` reusing Group's strip pattern). Click title toggles.
- The field count = number of inputs/textareas/selects in the section (mockup computes `el.querySelectorAll('input,textarea,select').length`).

**C.2.2 — hydrate ALL values from `servicio` + wire onChange→autosave (600ms canon).** Today most rich textareas are placeholders (no value, no onChange). After T-R1 the GET carries the values. Bind each field `.value` from `servicio.<field>` and `onChange → schedule({ <field>: v })`:
- Missing/unhydrated str fields to bind: `description_long` (Descripción corta), `includes`, `excludes`, `warranty`, `procedure_steps`, `anesthesia_pain`, `prep`, `aftercare`, `downtime`, `expected_result`, `result_timing`, `result_lifespan`, `realistic_expectations`, `risks`, `red_flags`.
- `initial_appt_duration_minutes` (Duración cita inicial) → `NumberWithUnit` value bound + onChange autosave.
- `initial_appt_type` (Tipo de cita) → canonical `Select` (already plain Select per the RichSelect-crash note), value bound + onChange autosave (resolves F3 on FE).
- **`VariantsRepeater`** — today `value={[]}` (premise [C]). Hydrate `value={servicio.variants ?? []}` + `onChange → schedule({ variants })`. Currency from `servicio.currency` (NOT `?? "USD"` — use `servicio.currency ?? undefined`; canon currency rule).
- **One `FloatingAutosaveIndicator`** per page (canon §2.6) — keep the single existing one; do NOT add per-section indicators.

**C.2.3 — modality conditionals (mockup `applyMod`).** When `modality === "sesiones"` → reveal `session_interval` (`NumberWithUnit` + unit `ValueWithUnit`); when `modality === "recurrente"` → reveal `recurrence_interval`. Both bind value from servicio + onChange autosave (`schedule({ session_interval: { value, unit } })`). Hidden otherwise. RHF watch on `modality` drives the conditional render.

**C.2.4 — KnowledgeSourcesPanel wired to the shell (persistent cross-leaf).** Today `KnowledgeSourcesPanel` is orphan. Mount it in `ServicioWorkspaceShell` (persistent across leaves, NOT per-leaf), colapsable per mockup `<details class="kpanel">`. It is extract-only in Sub-phase A (no RAG). Decide: a collapsible aside slot inside the Shell body (e.g., below `{children}` or in a side rail per mockup) — keep it OUT of the per-leaf scroll so it survives leaf navigation. (If `EntityWorkspaceLayout` exposes an aside slot, use it; else a `<details>`-style collapsible at the bottom of the Shell body.)

**C.2.5 — the duplicate `accordion.tsx` (scope-aware).** `vitalia/frontend/src/components/ui/accordion.tsx` is a local copy of the Radix accordion. ResumenView consumes `CollapsibleSection` (which composes ui-kit's accordion) → ResumenView itself no longer imports the local accordion. **HOWEVER**, grep (2026-06-16) shows TWO live out-of-scope importers: `features/mateo/components/agenda/{CobrarSaldoSubform,AppointmentDrawer}.tsx`. **DECISION: do NOT delete `accordion.tsx` in this delta** — repointing mateo is cross-feature churn outside this story's scope (`frontend-visual-fidelity` D3). T-R3 only removes any `lisa/servicios` import of the local accordion (there is none after consuming CollapsibleSection). The dup deletion + mateo repoint is flagged as a separate cleanup follow-up (see § follow-ups), so anti-duplication is acknowledged without scope creep. (Premise [D] said "borra accordion.tsx dup" — corrected: dup has live cross-feature consumers, so deletion is deferred to a scoped cleanup, not bundled here.)

### C.3 Design-system-canon compliance (HARD)
- `CollapsibleSection` composes ONLY from the canon (accordion + Group). ResumenView uses page-primitives + `Group`/`GroupHeader` semantics inherited by CollapsibleSection + canonical `Select` (already plain Select, NOT `<select>` nativo) + tokens (no arbitrary values — accent via `--agent-lisa` CSS var).
- No `<div>` layout where a primitive exists; no arbitrary spacing/radius/color. Agent strip via token.

---

## Part D — CollapsibleSection molecule (ENGINE · @luana/ui-kit) · ticket T-R0

> Owner: **`/pm-luana` promotion gate** (NOT a vitalia builder). Gated by promotion proposal `2026-06-16-collapsible-section-ui-kit.md` accepted. T-R0 blocks T-R3.

### D.1 Contract (props + composition)

`CollapsibleSection` = a section with a collapsible body, composing the already-exported `accordion` (Radix) + `Group` (accent strip + GroupHeader) from `@luana/ui-kit`. Header = title + summary/field-count + agent accent; body = collapsible children; `defaultOpen`.

```tsx
// core/@luana/ui-kit/src/CollapsibleSection.tsx  (NEW — composes accordion + Group, canon)
export interface CollapsibleSectionProps {
  /** Section title (rendered in the trigger). */
  title: string;
  /** Whether the body is open on first render. @default false */
  defaultOpen?: boolean;
  /** Right-aligned summary in the header (e.g. "6 campos" field-count). Optional. */
  summary?: React.ReactNode;
  /** Agent accent strip (LEFT), token-driven CSS var (e.g. "--agent-lisa"). Reuses Group accentVar. */
  accentVar?: string;
  /** Agent accent strip via Tailwind utility (e.g. "border-l-agent-lisa"). Alt to accentVar. */
  accentClass?: string;
  /** Semantic error state (red border) + inline missing-fields (delegates to Group). */
  hasError?: boolean;
  missingFields?: string[];
  /** Section body. */
  children: React.ReactNode;
  className?: string;
}
```

**Composition (internal):**
- Outer = `Group` (gives the agent accent strip + error border + rounded card — canon §2.6).
- Header = `Accordion`/`AccordionTrigger` (single-item, `collapsible`, controlled by `defaultOpen`) rendering `title` (left) + `summary` (right, e.g. field-count chip) + chevron (accordion provides). When `missingFields` present, GroupHeader's inline alert shows.
- Body = `AccordionContent` wrapping `children`.
- Controlled vs uncontrolled: `defaultOpen` → uncontrolled `defaultValue` on the Radix Accordion; expose `value`/`onValueChange` only if a future consumer needs controlled (NOT required now — keep minimal, YAGNI).

### D.2 Example usage (vitalia ResumenView, T-R3)

```tsx
import { CollapsibleSection } from "@luana/ui-kit";

<CollapsibleSection
  title="Identidad"
  defaultOpen
  accentVar="--agent-lisa"
  summary={<span className="text-xs text-muted-foreground">3 campos</span>}
>
  {/* nombre · categoría · peldaño */}
</CollapsibleSection>

<CollapsibleSection title="El procedimiento" summary="3 campos" accentVar="--agent-lisa">
  {/* cómo se hace · duración · cuidados */}
</CollapsibleSection>
```

### D.3 Consumers
- **Now:** vitalia `lisa-servicios` ResumenView (6 sections). Replaces the 6 flat `<Group>` + deletes local `accordion.tsx` dup.
- **Later:** nicolify / comunify entity workspaces with grouped collapsible ficha (any brand workspace with sectioned forms). Cross-brand reuse = the reason Chris ratified the core home.

### D.4 Verification (T-R0, owned by /pm-luana lift)
- ui-kit unit test `CollapsibleSection.test.tsx`: renders title + summary + children, `defaultOpen` opens body, click toggles, `accentVar` applies the left strip, `missingFields` renders the inline alert.
- Existing `accordion` + `Group` tests stay green (regression_guard — additive, no edit to those files).
- Downstream: no other brand consumes yet → no cross-brand regression at lift time; vitalia consumes in T-R3.

---

## 9.5 Tests audit (default flip) — **N/A**
- [x] No aplica — este delta NO flipea defaults side-effect (no feature flags, no call-path side-effect change). Pure DTO widening + FE wiring + new ui-kit molecule.

## Integration design (CONN) — anti-orphan

The StatusBar / rich fields / KnowledgeSourcesPanel all already have a home (cap `lisa.servicios`):
- **Consumed:** ResumenView (rich fields), the Shell (StatusBar + KnowledgePanel) — all rendered in the live workspace; CollapsibleSection consumed by ResumenView.
- **On the map:** `vitalia/docs/product/capabilities/offer/lisa.servicios.yaml` (extend).
- **Navigable:** workspace route `/[tenantId]/lisa/servicios/[offer-id]/resumen` (existing). StatusBar appears on every leaf via the Shell.
- **Notarized/registered:** ServiceStatusBar mounted in `ServicioWorkspaceShell` (the registration point — no new router). CollapsibleSection exported from `@luana/ui-kit/index.ts` (T-R0). `ServicioWorkspaceView` orphan DELETED (only barrel-re-exported in `features/lisa/index.ts:132`, no real consumer — remove file + export line). `accordion.tsx` dup deletion DEFERRED to a scoped cleanup follow-up (2 live mateo importers — see § C.2.5).

## Research notes
- No novel pattern. CollapsibleSection composes existing Radix accordion (already in ui-kit) + Group (canon §2.6). No external research required — all primitives are in-repo and verified by read (`core/@luana/ui-kit/src/{accordion,collapsible,Group}.tsx`, accessed 2026-06-16). My model's knowledge of Radix Accordion is consistent with the shipped in-repo version; no live research needed.

## Open questions for PM
1. **Completeness source for ServiceStatusBar:** T-R2 needs `filledCount`/`totalCount`/`missingFields`. Compute on the FE from the now-hydrated rich fields, or does a BE `completeness` read model already exist to surface? (T-1 shipped `offer/domain/completeness.py` — confirm whether `ServiceDetailDTO` should also expose a completeness summary in T-R1, or FE computes.) **Architect recommendation:** surface a lightweight `completeness: {filled, total, missing[]}` on `ServiceDetailDTO` in T-R1 (cheap, single SSoT) rather than re-deriving on the FE.
2. **KnowledgeSourcesPanel slot:** does `EntityWorkspaceLayout` (@luana/ui-kit) expose an aside/footer slot for a persistent cross-leaf panel, or does the Shell render it as a `<details>` collapsible at the bottom of its body? If a slot is needed in ui-kit, that's a second (small) core change — flag before T-R3 (architect leans: render in the Shell body as a `<details>`-style collapsible, NO new ui-kit slot, to keep the core change to just CollapsibleSection).
