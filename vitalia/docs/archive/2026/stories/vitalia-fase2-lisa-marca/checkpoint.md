---
story_id: vitalia-fase2-lisa-marca
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
agent_owner: lisa
module: brand_studio
capability: lisa.marca
state: done                                             # ★ 2026-05-27T03:45 — /pm-vitalia merge complete · 07-merge.md shipped · capability lisa-marca LIVE · archive R2 applied
state_done_at: 2026-05-27T03:45:00Z
state_done_by: /pm-vitalia
merge_artifact: 07-merge.md
squash_to_main: pending_chris_ratify                    # ★ 253 commits cross-story scope, Chris ratifica squash en morning
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
phase: DONE                                             # ★ story closure complete
last_modified: 2026-05-27
transitioned_at: 2026-05-27T05:52:36Z
transitioned_by: /architect (Opus 4.7 single-shot full-stack)
ratified_by_chris: true
ratified_by_chris_at: 2026-05-27T01:00:00-05:00
po_ux_iter: 3
po_ux_v2_at: 2026-05-27
po_ux_v2_changes: "Out-of-scope Landing (→ vitalia-fase2-lisa-landing-public idea); In-scope Presencia (sub-sub-tab); arquitectura N3-static SubSubTabsBar cabecera (no Tabs body); 4 archivos mockups _shared.css tokens reales"
po_ux_v21_at: 2026-05-27T00:45:00-05:00
po_ux_v21_changes: "Refactor wrapper mockups: shell topbar/ribbon/subtabs/chat-side portados verbatim del canónico (dual-mode-shell + valeria-chat-sample + valeria-rail). Panel content fluido (sin max-width hardcoded). Splitter control 3-estados. Colores marca reforzados (gradient mariposa logo, agent borders, agent-soft active). Origen: Chris feedback 'detalles que quiero afinar'."
po_ux_v3_at: 2026-05-27T01:00:00-05:00
po_ux_v3_changes: "OQs resueltas verbatim spec: OQ-A N3-static (ya cementada v2), OQ-B 4 archetypes salud, OQ-C BE endpoint voice-preview, OQ-D hybrid trust catalog, OQ-E preview footer único. Definición Done gate refining→refined GREEN."
architect_iter: 1
architect_at: 2026-05-27T05:52:36Z
architect_artifacts:
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/03-arch.md       # 1904 lines consolidated BE+FE
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/04-validators.yaml  # 780 lines, 5 categories, 11 SCs coverage
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/05-guidelines.md   # 695 lines, must_load_skills enforceable
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/06-tickets.yaml    # 864 lines, 12 tickets atomic
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-27T01:00:00-05:00
ratified_visual_iter: 2.1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/identidad-section.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/voz-tono-section.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/presencia-section.html
oq_resolutions:
  OQ-A: "N3-static SubSubTabsBar (resuelta en v2)"
  OQ-B: "4 archetypes salud-friendly (Caregiver/Sage/Healer/Hero)"
  OQ-C: "BE endpoint /lisa/marca/voice-preview"
  OQ-D: "Hybrid trust catalog cerrado per país + free-text"
  OQ-E: "Preview footer único debajo card Tratamiento+idioma"
autonomous_chain_authorized: true
autonomous_chain_authorized_at: 2026-05-27T01:00:00-05:00
autonomous_chain_authorized_reason: "Chris se retira a descansar. Delegó autonomía hasta done + merge a main. Sub-agentes manejados por Opus PM coordinator."
uses_n3_static: true
agent_subsubtabs_entry: "lisa.marca = ['identidad', 'voz-y-tono', 'presencia']"
parallel_safe: true
priority: high
estimated_dev_days: 4-5                                 # 38 hours / 8h = ~5 dev-days
total_tickets: 12
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft: []
blocks_hard: []
blocks_soft:
  - vitalia-fase2-camila-reputacion
  - vitalia-fase2-adrian-propuestas
reuse_map_summary: "REUSE 90% brand_studio shipped (core/luana-core-brand-studio + nicolify FE schemas IMPORT verbatim) · NEW BE módulo vitalia.brand_studio brand-extension + NEW FE features/lisa · ADAPT salud overlay (4 archetypes + prohibited phrases tabla + trust hybrid catalog PE seed)"
spawned_at: 2026-05-22
next_action: "AUTO-CHAIN: invocar Skill(dev-team) con args 'vitalia vitalia-fase2-lisa-marca' → build 12 tickets atomic per 06-tickets.yaml. Owner pool: [qwen-opencode, claude-sonnet, claude-opus] — NO claude_opus_required (zero agentic surface)"

# Schema v2 migration (cement 2026-05-27)
release: F2   # release ID · ver releases/
cap_target: lisa-marca   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S7 vitalia-fase2-lisa-marca — checkpoint

## State transition log

| State | Date | Owner | Action |
|---|---|---|---|
| `refining` | 2026-05-22 | `/po-ux` | Spec v1 redactada (Tabs body internal) |
| `refining` | 2026-05-27 | `/po-ux` v2 | N3-static cementación + mockups v2 |
| `refining` | 2026-05-27 | `/po-ux` v2.1 | Wrapper canónico-fiel refactor (mockups iter v2.1 ratificados) |
| `refining → refined` | 2026-05-27T01:00:00-05:00 | `/po-ux` v3 + Chris ratify | OQ-A..E resueltas + Definición Done GREEN + autonomous chain authorized |
| `refined → ready` | 2026-05-27T05:52:36Z | `/architect` (Opus 4.7 single-shot full-stack) | Ready package generated: 03-arch.md (1904) + 04-validators.yaml (780) + 05-guidelines.md (695) + 06-tickets.yaml (864) |

## Goal (verbatim spec)

Sub-tab Marca de Lisa: workspace administración brand-identity salud-overlay. 3 sub-sub-tabs N3-static (Identidad / Voz y tono / Presencia). Reuse 90% engine `core/luana-core-brand-studio` (shipped) + nicolify FE schemas IMPORT verbatim. NEW BE módulo `vitalia/backend/src/modules/vitalia/brand_studio/` + NEW FE `vitalia/frontend/src/features/lisa/`. ADAPT salud overlay (4 archetypes Caregiver/Sage/Healer/Hero + tabla `vitalia_prohibited_phrases` soft warning configurable + hybrid trust catalog per país PE seed shipped).

## Architecture decisions cementadas (ratified)

- **D1-arch:** Citar ADR-vitalia-004 verbatim — adr_004_compliance: full
- **D2-voice:** NUNCA crear `health_voice_validator.py`. Reuse compiler v2 + tabla `vitalia_prohibited_phrases` soft warning configurable
- **D3-clinic:** `clinic_vertical` + `primary_specialties` read-only desde onboarding-clinica story
- **D4-extract:** Visual extraction = stub local + botón disabled hasta `/pm-luana` accept proposal
- **D5-archetype:** 4 archetypes salud-friendly (Caregiver default / Sage / Healer / Hero) — omit Outlaw/Magician/Lover/Innocent
- **OQ-A → A11:** N3-static SubSubTabsBar cabecera (ADR-004 v1.1)
- **OQ-B:** 4 archetypes salud
- **OQ-C → A3:** BE endpoint `/lisa/marca/voice-preview` server-side compile + LRU+Redis cache key `(tenant_id, profile_id, compiler_version, hash(blocks))`
- **OQ-D → A4:** Hybrid trust catalog cerrado per país (PE seed shipped) + free-text "Otra"
- **OQ-E → § 6.8:** BrandVoicePreview footer único debajo card Tratamiento+idioma · refresh on autosave 600ms debounce hash
- **A1:** NEW módulo `vitalia.brand_studio` brand-extension (NO mirror engine, NO modify engine)
- **A2:** Repos heredan `Repository` base normal (NO `PhiRepositoryBase`) — story owner config, no PHI directo
- **A5:** REUSE `vitalia_growth_studio_event` (shipped F2-S1) + extend whitelist 13 events
- **A6/A7:** NEW arch tests creep guards `test_no_health_voice_validator.py` + `test_no_brand_voice_summary_table.py`
- **A8:** Schemas Zod IMPORT verbatim de nicolify (FE shared pattern post-shipped) + ADAPT salud overlay
- **A13:** Logo dual validation server + client ≤5MB + format whitelist

## Deliverables ratificados

### Artefactos `/architect` (esta iteración)

| Path | LOC | Status |
|---|---|---|
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/03-arch.md` | 1904 | ✅ Generated |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/04-validators.yaml` | 780 | ✅ Generated |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/05-guidelines.md` | 695 | ✅ Generated |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/06-tickets.yaml` | 864 | ✅ Generated |

### Mockups ratificados Chris iter v2.1 (2026-05-27)

| Path | Status |
|---|---|
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/identidad-section.html` | ✅ Ratified |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/voz-tono-section.html` | ✅ Ratified |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/presencia-section.html` | ✅ Ratified |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/_shared.css` | ✅ Ratified (tokens HSL real vitalia) |

## Tickets summary (12 atomic, owner_pool open)

| ID | Title | Surface | Hours | claude_opus_required | Blocks |
|---|---|---|---|---|---|
| T-1 | BE migration + telemetry whitelist extend | BE | 2 | false | T-2, T-3 |
| T-2 | BE API + services + RBAC | BE | 6 | false | T-3, T-4 |
| T-3 | BE pytest + arch fitness creep guards | BE | 4 | false | — |
| T-4 | FE routing N3-static + SubSubTabsBar + catalog | FE | 3 | false | T-5, T-6, T-7 |
| T-5 | FE Identidad sub-sub-tab | FE | 5 | false | T-9, T-10 |
| T-6 | FE Voz y tono sub-sub-tab | FE | 5 | false | T-9, T-10 |
| T-7 | FE Presencia sub-sub-tab | FE | 4 | false | T-9, T-10 |
| T-8 | FE forms RHF + Zod IMPORT nicolify | FE | 2 | false | T-5, T-6, T-7 |
| T-9 | FE Vitest unit tests | FE | 3 | false | — |
| T-10 | FE E2E Playwright 11 scenarios | FE | 5 | false | T-11, T-12 |
| T-11 | FE visual goldens 6 PNGs + cleanup legacy | FE | 2 | false | — |
| T-12 | FE a11y axe WCAG 2.1 AA | FE | 1 | false | — |
| **Total** | | | **38** | **0** | |

## Scenario coverage (11 SCs declared)

✅ SC-1 happy autosave · SC-2 negative voice warning · SC-3 edge logo oversized · SC-4 adversarial cross-tenant · SC-5 race condition · SC-6 concurrent owners · SC-7 network failure · SC-8 empty state · SC-9 large dataset · SC-10 accessibility · SC-11 i18n

## Service-deps

NONE blocking. Engine `core/luana-core-brand-studio` + `core/luana-core-sales-agent` shipped. Visual extraction (D4) defaults to stub + disabled — gating solo IF `/pm-luana` accepts proposal 2026-05-26.

## Definición de "Done" (gate ready → developed → reviewing → done)

### Para `/dev-team` (build phase)

- [ ] 12 tickets cierran con T-{n}-result.md + gate-output.json GREEN per ticket
- [ ] All validators de `04-validators.yaml` pasan (5 categories: non_functional / functional / visual / architectural_validation; agentic_eval N/A)
- [ ] 11 Gherkin scenarios cubiertos per `scenario_coverage` map
- [ ] Visual goldens × 6 generated (3 subsubtabs × 2 themes)
- [ ] Spanish neutro pre-commit hook GREEN
- [ ] Auto-handoff `/auditor`

### Para `/auditor` (review phase)

- [ ] 9 secciones ADR-vitalia-004 cumplidas (full compliance) — checklist per § 6.3 ADR
- [ ] 11 Gherkin scenarios mapped to tests verified (Phase D gherkin-matrix)
- [ ] Anti-creep arch tests GREEN (no_health_voice_validator + no_brand_voice_summary_table)
- [ ] APPROVED → AUTO-HANDOFF `/pm-vitalia` merge

### Para `/pm-vitalia` (merge phase)

- [ ] Squash-merge wip/vitalia → main + `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` created
- [ ] `vitalia/docs/product/modules/brand_studio.md` NEW module doc
- [ ] BACKLOG regen via scripts/generate_backlog.py
- [ ] state: reviewing → done

## Próximo paso post-done

- F2-S8 lisa-doctores extiende equipo preview con CRUD doctors (consume lisa-marca team-preview surface)
- F2-S9 lisa-servicios consume voice brand para descripciones
- vitalia-fase2-lisa-landing-public (state=idea) — defer Landing pública Vitalia editor

## Referencias

- **ADR transversal:** `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`
- **Design Contract visual:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Source story patrón:** `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md`
- **Mockup gate:** `vitalia/.claude/rules/shell-mockup-per-component.md` + `ADR-vitalia-003`
- **Architecture mandatory:** `vitalia/.claude/rules/shell-feature-architecture-mandatory.md`
- **HIPAA-lite overlay:** `vitalia/.claude/rules/hipaa-lite.md`
- **Anti-creep cardinal:** `.claude/rules/sales-agent-brand-voice.md`
- **Spanish neutro:** `.claude/rules/spanish-text.md`
- **brand-expert skill:** PersonalityProfile compiler v2 SSoT + Jung archetypes
- **sales-agent-expert skill:** compiler v2 slot 5 BRAND_VOICE library API
- **Engine brand_studio:** `core/luana-core-brand-studio/`
- **Engine sales-agent compiler v2:** `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py`
- **Nicolify schemas IMPORT source:** `nicolify/frontend/src/features/brand-studio/schemas/`
- **Promotion proposal D2 (pending):** `docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md`
