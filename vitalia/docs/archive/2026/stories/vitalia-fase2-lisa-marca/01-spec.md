<!-- voseo-allowed: glosario reference inline en § Microcopy (forbidden voseo examples) -->

---
story_id: vitalia-fase2-lisa-marca
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
state: refined                                  # ★ 2026-05-27 — transition refining→refined ratificada Chris
architecture_pattern: ADR-vitalia-004           # ★ MANDATORY — sin esto /architect REFUSE
adr_004_compliance: full                        # v2.1 cumple ADR-004 v1.1 (N3-static SubSubTabsBar) + wrapper canónico-fiel
po_ux_iter: 3                                   # v3 — OQs resueltas + wrapper refactor v2.1 ratificado
po_ux_started_at: 2026-05-26
po_ux_v2_at: 2026-05-27
po_ux_v3_at: 2026-05-27T01:00:00-05:00
last_modified: 2026-05-27
ratified_by_chris: true
ratified_by_chris_at: 2026-05-27T01:00:00-05:00
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-27T01:00:00-05:00
ratified_visual_iter: 2.1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/identidad-section.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/voz-tono-section.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/presencia-section.html
oq_resolutions:                                 # OQs ratificadas en § Open questions
  OQ-A: "N3-static SubSubTabsBar (resuelta en v2)"
  OQ-B: "4 archetypes salud-friendly (Caregiver/Sage/Healer/Hero)"
  OQ-C: "BE endpoint /lisa/marca/voice-preview"
  OQ-D: "Hybrid trust catalog cerrado per país + free-text"
  OQ-E: "Preview footer único debajo card Tratamiento+idioma"
agent_owner: lisa
module: brand_studio
capability: lisa.marca
parent_outcome_ref: vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md
parent_adr_ref: vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md
hipaa_lite_overlay: true                        # touches owner config, no PHI directo pero overlay aplica defense-in-depth
uses_n3_static: true                            # ★ v2 — sub-sub-tabs cabecera (Identidad/Voz/Presencia)
agent_subsubtabs_entry: "lisa.marca = ['identidad', 'voz-y-tono', 'presencia']"
---

# vitalia-fase2-lisa-marca — Spec v2 (post-cementación N3-static)

## § Changelog v1 → v2 (2026-05-27)

**Disparador:** Chris revisó mockups v1 (servidos en localhost:8888) y detectó:
1. Mis Tabs internas Shadcn en body = Nivel 4 anti-pattern (no convención cementada). Sub-secciones deben vivir como **N3-static SubSubTabsBar en cabecera**.
2. AppPanelSlot en dual-mode 50/50 = ~720px wide, no full-width 1024 como diseñé.
3. Landing pública out-of-scope esta story — defer a story futura. **Presencia digital (redes/sitio web/Google Business) SÍ in-scope.**

**Cambios v2:**
- ★ Out-of-scope **Landing pública Vitalia** → defer a story `vitalia-fase2-lisa-landing-public` (state=idea creada)
- ★ In-scope **Presencia** como sub-sub-tab N3-static (redes sociales + sitio web propio + Google Business + trust signals + ubicaciones)
- ★ Arquitectura: 3 sub-sub-tabs N3-static en cabecera (`identidad / voz-y-tono / presencia`) con routing `[subtab]/[subsubtab]/page.tsx` per ADR-004 v1.1
- ★ Eliminados componentes intermedios `LisaMarcaView` Tabs body — reemplazados por 3 panel components directos
- ★ Mockups v2 con max-width ~720px (AppPanelSlot real) + chat Valeria mock al costado
- ★ Update Files in scope + deliverables + estados visuales

## § Context

### Outcome ref
`vitalia-mvp-ui-foundation` — sub-tab Marca de Lisa: workspace administración brand-identity con salud-overlay. Reemplaza dashboard legacy `/(dashboard)/brand-studio/[section]/page.tsx`.

### Insertion point
Tab Lisa → sub-tab "Marca" en shell-organism agéntico. Path:
```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/page.tsx
```
Sub-tab "Marca" es 1 de los N sub-tabs de Lisa (otros: doctores, servicios, compliance — stories paralelas Fase 2).

### Out-of-scope
- ❌ Editar `clinic_vertical` o `primary_specialties` — esos viven en `vitalia-fase2-config-onboarding-clinica` (esta story los muestra **read-only** con edit-link).
- ❌ CRUD doctores team — story `vitalia-fase2-lisa-doctores` (esta story muestra **preview read-only** vía API).
- ❌ AI logo generator (defer post-MVP).
- ❌ **★ v2 (2026-05-27): Landing pública Vitalia editor** — defer a story dedicada `vitalia-fase2-lisa-landing-public` (state=idea). Chris ratificó "no sé dónde va aún". Sub-sub-tab Presencia SÍ in-scope (redes sociales + sitio web propio + Google Business + trust signals).
- ❌ Editor visual de landing pública (delegate story futura).
- ❌ **Voice rewriter LLM post-generación** — PROHIBIDO per `.claude/rules/sales-agent-brand-voice.md` § creep guards.
- ❌ Tabla `brand_voice_summary` mirror — PROHIBIDO mismo rule (arch test `test_brand_voice_no_summary_table.py` enforces).
- ❌ Habilitar visual extraction pipeline runtime — depende de `/pm-luana` accept proposal `2026-05-26-lift-brand-visual-extraction-to-core.md` (esta story ships con **stub local + botón disabled**).
- ❌ Fine-tuning per tenant — PROHIBIDO mismo rule.
- ❌ **★ v2: Shadcn `Tabs` internas body** — Nivel 4 anti-pattern (per ADR-004 v1.1 § 3.1.1). Usar N3-static `SubSubTabsBar` cabecera.

### Trigger
Usuario tipo `owner` o `admin_clinic` navega Lisa → tab Marca. Si tenant nuevo sin `clinic_vertical` seteado → middleware redirige a onboarding (gate de `vitalia-fase2-config-onboarding-clinica`); este spec asume tenant ya pasó onboarding.

### Repro evidence (no aplica)
No es hot-fix. Story greenfield post-shell-organism cementación 2026-05-22.

---

## § Reuse map (subagent enrichment 2026-05-26)

### Engine `core/luana-core-brand-studio` (CONSUME via API — NO tocar)

| Path | Surface | Acción |
|---|---|---|
| `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/identity.py` | BrandIdentity aggregate | CONSUME |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py` | PersonalityProfile aggregate (Jung archetypes) | CONSUME |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/team.py` | Team aggregate | CONSUME (read-only preview) |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/section_catalog.py::BRAND_SECTION_CATALOG` | Sections registry | CONSUME |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/infrastructure/repositories/personality_repository.py` | PersonalityProfile persistence | CONSUME via service |
| `core/luana-core-brand-studio/src/luana_core_brand_studio/api/personality.py` | PersonalityProfile API | CONSUME |
| `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py::PromptFragment.BRAND_VOICE` | Slot 5 cacheable compiler v2 que lee `personality_profiles.system_instruction` | CONSUME implícito (sales_agent ya wired) |

### Vitalia FE legacy (REFACTOR → migrar a lisa/marca)

| Source | Destino | Cambios |
|---|---|---|
| `vitalia/frontend/src/features/vitalia/components/brand-studio-section-client.tsx` | `vitalia/frontend/src/features/lisa/components/marca/LisaMarcaView.tsx` | REWRITE: Zod+RHF (no useState per-field) · debounce 500→600ms · tokens shell-organism (`--agent-lisa`, `border-brand`, `ring-brand`) · fix empty state bug (líneas 234-240 body vacío) |
| `vitalia/frontend/src/features/vitalia/components/clinic-type-picker.tsx` | NO usado en lisa-marca | Read-only display vía edit-link a `/onboarding/clinic-config` |
| `vitalia/frontend/src/features/vitalia/schemas/clinic-profile-schema.ts` | Cleanup post D3 (REPLACE legacy `ClinicType`) | Coordinado con story `vitalia-fase2-config-onboarding-clinica` migration |
| `vitalia/frontend/src/app/(dashboard)/brand-studio/[section]/page.tsx` | DELETE post-merge | Reemplazado por nuevo `app/[tenantId]/(shell-organism)/lisa/marca/page.tsx` |

### Nicolify components (importables/adaptables)

| Source | Acción | Justificación |
|---|---|---|
| `nicolify/frontend/src/features/brand-studio/schemas/identity.schema.ts` | IMPORT verbatim → `features/lisa/types/marca/identity-schema.ts` | Schema Zod identity production-ready |
| `nicolify/frontend/src/features/brand-studio/schemas/contact.schema.ts` | IMPORT verbatim → `features/lisa/types/marca/contact-schema.ts` | idem |
| `nicolify/frontend/src/features/brand-studio/schemas/visuals.schema.ts` | IMPORT + ADAPT `ClinicBrandVisuals` (overlay extract pipeline cuando lift accepted) | Schema base reusable |
| `nicolify/frontend/src/features/brand-studio/schemas/personality.schema.ts` | IMPORT + ADAPT salud overlay (default `Caregiver`, omit `Outlaw`/`Magician` problematic for health) | Jung archetypes editable |
| `nicolify/frontend/src/features/brand-studio/schemas/team.schema.ts` | IMPORT verbatim (read-only en lisa-marca, CRUD vive en lisa-doctores) | Schema base |
| `nicolify/frontend/src/features/brand-studio/schemas/testimonial-item.schema.ts` | IMPORT verbatim | Schema base |
| `nicolify/frontend/src/features/brand-studio/components/TestimonialInstancePicker.tsx` | ADAPT pattern (no copy directo — tokens distintos) | Instance picker pattern |
| `nicolify/frontend/src/features/brand-studio/pages/SectionDispatcher.tsx` | ADAPT pattern (`dynamic()` lazy imports per sub-section evita Next.js OOM) | Lazy loading pattern |
| `nicolify/frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx` | OMIT (lisa-marca usa Shadcn `Tabs` internas — Open Question OQ-A) | Decisión arquitectónica |
| `nicolify/frontend/src/features/brand-studio/schemas/{positioning,narrative,story,strategy,buyer-persona,methodology,authority-item,legal,communication-assets,avatars,logos}.schema.ts` | OMIT (disabled per `vitalia/config/brand.yaml::brand_studio.enabled_sections = [identity, contact, team, testimonials]`) | Vitalia simplificado salud — no requiere StoryBrand/Jung/buyer-persona complexity |

### Backup `ap_sales_agent` patterns (referenciados, no IMPORT directo)

| Pattern | Aplicación lisa-marca | Estado |
|---|---|---|
| 4 estados (Zero / In Progress / Established / Returning) | Empty state CTA + edit-on-hover sections + happy path | ADAPT — incorporar en wireframes |
| SmartFillSheet (Side Panel AI tool wrapper) | Container para futuro AI refine personality | DEFER MVP — placeholder en Voz y Tono |
| Visual identity extract pipeline | Botón "Extraer desde mi sitio web" en Identidad | **STUB local** hasta `/pm-luana` accept proposal D2 |
| `ExtractedVisuals` TypeScript interface | `ClinicBrandVisuals` en `features/lisa/types/marca/visuals-schema.ts` | IMPORT-with-rename (campos: primary_color, accent_color, background_color, text_primary_color, text_on_primary, font_heading, font_body, design_style, usage_guidelines) |

---

## § Voice architecture (post `sales-agent-brand-voice.md` re-design)

> **Cambio crítico vs checkpoint original:** el `health_voice_validator.py` propuesto inicialmente está **eliminado** porque viola `.claude/rules/sales-agent-brand-voice.md` § creep guards. Reemplazado por configurable blocklist + reuse compiler v2.

### Pipeline (3 capas)

1. **SSoT inalterable:** `personality_profiles.system_instruction` (engine `core/luana-core-brand-studio`) — sales_agent compiler v2 `compose.py::PromptFragment.BRAND_VOICE` (slot 5) lo lee como cache prefix estable.
2. **Editor UI en Lisa → Marca → Voz y tono** — formulario directo sobre `personality_profiles.system_instruction` 6 bloques (compiler v2 verbatim): identidad / contexto / "ASÍ HABLO" / "ASÍ NO HABLO" / contexto técnico / formato. Brand voice preview muestra cómo se compila para el agente.
3. **Soft warning client-side pre-save:** tabla brand-local `vitalia_prohibited_phrases (tenant_id, phrase, suggested_alternative, severity, created_at, updated_at)` con seed defaults salud (`curamos`, `garantizado`, `100% efectivo`, `sin riesgos`, `tratamiento milagroso`). Owner ve warning inline si su input incluye phrase blocked → puede "Guardar igual" con audit log row (`voice_warning_overridden`). **NO bloquea** persistencia.

### Tests anti-creep

Heredados del rule (ya shipped en engine + nicolify):
- `nicolify/backend/tests/architecture/test_brand_voice_no_summary_table.py` — verifica que no exista tabla mirror `brand_voice_summary`
- `core/luana-core-brand-studio/tests/test_voice_fidelity_grader.py` — golden eval voice fidelity
- `vitalia/backend/tests/agentic_evals/grader/test_voice_fidelity_per_fixture.py` — per-fixture golden

Nuevos para esta story:
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_seed.py` — seed defaults salud presentes
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_voice_warning_audit_log.py` — override `voice_warning_overridden` escribe audit row
- `vitalia/backend/tests/architecture/test_no_health_voice_validator.py` — bloquea regresión `health_voice_validator.py` accidental

---

## § Gherkin scenarios (4 base + 7 sub-categorías mandatory v4.1)

> Notación: `playwright_required: true` en todos los scenarios funcionales FE. `graders` = lista verificable.

### happy — editar identidad con autosave

```gherkin
Scenario: Owner edita nombre clínica + autosave dispara silencioso
  Given owner del tenant "clinica-dental-pe" navega a /lisa/marca
  And está en tab interno "Identidad"
  And input "Nombre clínica" muestra valor actual "Clínica Dental Lima"
  When tipea " Centro" al final → "Clínica Dental Lima Centro"
  And waits 600ms (debounce)
  Then UI muestra toast tiny "Guardado" (3s timeout) en bottom-right
  And PATCH /api/v1/lisa/marca/identity con body { name: "Clínica Dental Lima Centro" } intercepted
  And response 200 con updated_at refrescado
  And audit_log row creado con action="brand_identity_updated"
  And input mantiene foco (no re-render destructivo)
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-identidad-autosave.spec.ts"
  - type: state_check
    target: db
    query: "SELECT name FROM brand_identity WHERE tenant_id = $1"
    expect: "Clínica Dental Lima Centro"
  - type: state_check
    target: db
    query: "SELECT action FROM vitalia_audit_log WHERE resource_type='brand_identity' ORDER BY timestamp DESC LIMIT 1"
    expect: "brand_identity_updated"
  - type: visual_state
    screen: "lisa-marca-identidad-saved"
    element: "[data-testid=autosave-toast]"
    expect: "visible-3s-then-fadeout"
```

### negative — voice warning soft (no bloquea, owner ratifica)

```gherkin
Scenario: Owner agrega phrase prohibida a voice → warning inline, no bloqueo
  Given owner edita Lisa → Marca → Voz y tono
  And bloque "ASÍ HABLO" tiene texto base
  When agrega frase "Garantizamos curar tu sonrisa en 30 días"
  And waits 600ms
  Then UI muestra Alert variant="warning" inline debajo del textarea con texto
    "Esta frase usa lenguaje que puede violar regulaciones de salud
    (`curar`, `garantizamos`). Considerá: 'Acompañamos tu tratamiento con
    protocolos clínicos avalados'."
  And el botón explicit "Guardar igual con esta frase" aparece
  When owner click "Guardar igual con esta frase"
  Then PATCH /api/v1/lisa/marca/personality persistido
  And audit_log row con action="voice_warning_overridden" + payload_redacted incluye phrase_id + tenant_id
  And toast tiny "Guardado con advertencia" (5s timeout) ámbar
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-voice-warning.spec.ts"
  - type: state_check
    target: db
    query: "SELECT action, payload_redacted FROM vitalia_audit_log WHERE action='voice_warning_overridden' ORDER BY timestamp DESC LIMIT 1"
    expect_contains: "phrase_id"
  - type: visual_state
    screen: "lisa-marca-voice-warning"
    element: "[role=alert][data-variant=warning]"
    expect: "visible-with-suggested-alternative-text"
```

### edge — logo upload > 5 MB client-side + server-side validation

```gherkin
Scenario: Owner intenta upload logo de 8 MB
  Given owner en Lisa → Marca → Identidad sub-sección Logos
  When selecciona archivo logo-clinica-original.png (8 MB)
  Then client-side validation bloquea ANTES request
  And UI muestra inline error "Logo máximo 5 MB. Tu archivo tiene 8 MB.
    Comprimí la imagen o usá un formato más liviano (WebP recomendado)."
  And input file se resetea
  And NO request a /api/v1/lisa/marca/logos disparado
  When owner usa imagen comprimida 2 MB
  Then upload procede + preview live + autosave fires + tabla `brand_visuals.logo_url` updated
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-logo-upload-size.spec.ts"
  - type: state_check
    target: network
    expect: "no_request_for_oversized_file"
  - type: visual_state
    screen: "lisa-marca-logo-error-oversized"
    element: "[data-testid=logo-upload-error]"
    expect: "visible-with-size-message"
```

### adversarial — cross-tenant brand-studio edit attempt

```gherkin
Scenario: Tenant A intenta editar brand-identity de tenant B via payload manipulation
  Given tenant_a JWT con tenant_id="tenant-a-uuid"
  And payload PATCH incluye tenant_id="tenant-b-uuid" en URL/body
  When PATCH /api/v1/lisa/marca/identity con payload adulterado
  Then backend retorna 403 Forbidden
  And tenant_b brand_identity row NO modificada (DB query verifica)
  And audit_log de tenant_a registra action="cross_tenant_brand_edit_attempt"
  And NO response body PHI leak (response model strict)
playwright_required: false                # service-only adversarial — BE pytest sufficient
graders:
  - type: state_check
    target: api_response
    expect_status: 403
  - type: state_check
    target: db
    query: "SELECT updated_at FROM brand_identity WHERE tenant_id='tenant-b-uuid'"
    expect: "unchanged_from_before_attack"
  - type: state_check
    target: db
    query: "SELECT action FROM vitalia_audit_log WHERE tenant_id='tenant-a-uuid' ORDER BY timestamp DESC LIMIT 1"
    expect: "cross_tenant_brand_edit_attempt"
```

### race_condition — 2 tabs autosave simultáneo (last-write-wins + dual audit)

```gherkin
Scenario: Owner abre 2 tabs en Lisa → Marca → Identidad y autosavea simultáneo
  Given tab A muestra name="Clínica Dental Lima"
  And tab B muestra name="Clínica Dental Lima"
  When tab A edita name → "Clínica Dental Lima Norte" (autosave dispara en 600ms)
  And tab B (delay 50ms) edita name → "Clínica Dental Lima Sur" (autosave dispara en 600ms)
  And ambos PATCH llegan al backend casi simultáneo
  Then backend resuelve last-write-wins basado en server-side timestamp ordering
  And DB persiste el último (probablemente "Sur" si llega después)
  And audit_log registra 2 rows distintos (1 por cada attempt)
  And tab A recibe response 200 con `updated_at` que es ≥ su request
  And tab A re-fetches en próximo refresh (React Query stale-while-revalidate) → muestra valor server-side correcto
  And no hay corruption ni dato perdido silencioso
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-race-autosave.spec.ts"
  - type: state_check
    target: db
    query: "SELECT COUNT(*) FROM vitalia_audit_log WHERE action='brand_identity_updated' AND tenant_id=$1 AND created_at > NOW() - INTERVAL '10 seconds'"
    expect: 2
  - type: state_check
    target: db
    query: "SELECT name FROM brand_identity WHERE tenant_id=$1"
    expect_one_of: ["Clínica Dental Lima Norte", "Clínica Dental Lima Sur"]
```

### concurrent_users — 2 owners mismo tenant editan misma sub-sección

```gherkin
Scenario: Owner A y Owner B (mismo tenant, distintos JWT) editan Voz y tono simultáneo
  Given owner_a edita textarea "ASÍ HABLO" → agrega frase "Tono cálido"
  And owner_b edita misma textarea → agrega frase "Tono profesional"
  When autosave de ambos dispara con 100ms de diferencia
  Then backend persiste both attempts secuencialmente (last-write-wins)
  And ambos audit_log rows incluyen user_id distinto
  And owner_a next-refresh muestra texto consolidado server-side (puede haber perdido su edit si llegó primero)
  And UI de owner_a muestra notification non-blocking "Esta sección fue editada por otro usuario hace X segundos. Recargá para ver cambios."
playwright_required: true                  # 2 browser contexts
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-concurrent-owners.spec.ts"
  - type: state_check
    target: db
    query: "SELECT user_id FROM vitalia_audit_log WHERE action='brand_personality_updated' ORDER BY timestamp DESC LIMIT 2"
    expect: "two_distinct_user_ids"
```

### network_failure — autosave timeout retry

```gherkin
Scenario: Autosave dispara con backend timeout 30s
  Given owner edita name field en Identidad
  And backend simula timeout 30s (msw network mock)
  When autosave fires post-debounce
  Then UI muestra spinner "Guardando..." durante intento
  And tras 30s timeout, UI muestra Alert variant="error" inline
    "No pudimos guardar tu cambio. Reintentar."
  And botón "Reintentar" disponible
  When click "Reintentar"
  Then nueva request fires
  And si succeed → toast "Guardado" + Alert se cierra
  And si re-fail → contador retry (max 3) + permite "Cancelar cambios" rollback local
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-autosave-timeout.spec.ts"
  - type: visual_state
    screen: "lisa-marca-autosave-error"
    element: "[role=alert][data-variant=error]"
    expect: "visible-with-retry-button"
```

### empty_state — tenant nuevo sin brand data inicial

```gherkin
Scenario: Tenant nuevo entra a Lisa → Marca por primera vez
  Given tenant "nueva-clinica-mx" pasó onboarding con clinic_vertical="dental_clinic"
  And NO tiene rows en brand_identity, brand_visuals, personality_profiles, brand_contact
  When navega a /lisa/marca
  Then tab Identidad muestra empty state hero
    "Configurá tu identidad de marca"
    "Vitalia personaliza la conversación de tus agentes con la voz y estilo
     de tu clínica. Llevate 5 minutos."
    + CTA primary "Empezar"
  And clic "Empezar" muestra form con valores prellenados por defecto
    (name="Clínica Dental Nueva-Clinica-Mx" sugerido desde tenant.subdomain)
  And autosave fires al primer cambio
  And progress bar interna muestra "1 de 3 sub-secciones completas" tras Identidad save
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-empty-state.spec.ts"
  - type: visual_state
    screen: "lisa-marca-empty-state-identidad"
    element: "[data-testid=empty-state-cta]"
    expect: "visible-with-primary-button"
```

### large_dataset — render perf con 50 testimonials + 30 team members

```gherkin
Scenario: Owner navega a Marca tab con tenant que tiene 50 testimonials y 30 team members (read-only previews)
  Given tenant "clinica-grande-co" con brand data extensa
  And brand_testimonials.count = 50
  And brand_team.count = 30 (read-only preview vía API lisa-doctores)
  When owner navega a /lisa/marca
  Then página renderiza en ≤ 1.5s (LCP medido)
  And lista testimonials usa virtualization (react-window) visible scroll
  And primer 20 testimonials visibles al mount
  And scroll 60fps sin jank
  And memory footprint < 50 MB heap incremento
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-large-dataset.spec.ts"
  - type: perf
    metric: LCP
    expect: "<= 1500ms"
  - type: perf
    metric: heap_memory_delta
    expect: "<= 50MB"
```

### accessibility — WCAG AA full keyboard nav + screen reader

```gherkin
Scenario: Usuario solo teclado navega Lisa → Marca completo
  Given usuario sin mouse, solo teclado + NVDA screen reader (Chrome)
  When Tab desde header hasta primer tab interno (Identidad)
  Then aria-selected="true" en tab Identidad
  And NVDA anuncia "Tab Identidad, seleccionada, 1 de 3"
  When Arrow right → tab Voz y tono
  Then NVDA anuncia "Tab Voz y tono, seleccionada, 2 de 3"
  When Tab → primer input dentro panel
  Then focus ring visible (Tailwind focus:ring-2 focus:ring-primary)
  And NVDA anuncia label + valor input
  When edit field + Tab next
  Then autosave dispara (debounce respeta keyboard nav)
  And toast "Guardado" anunciado con aria-live="polite"
  When axe-core audit corre en cada estado (idle / loading / success / error / empty)
  Then 0 violations WCAG AA
playwright_required: true
graders:
  - type: e2e
    path: "vitalia/frontend/e2e/shell-organism/lisa-marca-a11y-keyboard.spec.ts"
  - type: axe
    ruleset: "wcag2aa"
    expect: "0_violations"
  - type: aria
    selector: "[role=tab][aria-selected=true]"
    expect: "exactly_one_per_tablist"
```

### i18n — Spanish neutro LatAm completo (no voseo, no léxico regional)

```gherkin
Scenario: Auditoría manual + automated grep de copy
  Given todos los strings user-facing del componente LisaMarcaView + sub-secciones
  When grep contra glosario `.claude/rules/spanish-text.md` § voseo
  Then 0 matches verbatim
    (sin "vos", "sos", "tenés", "podés", "dale", "mirá", "andá", "fijate")
  And tildes + ñ + apertura ¿¡ presentes donde corresponde
  And léxico regional ("laburo", "quilombo", "pibe", "che") = 0 matches
  And copy es comprensible para usuarios MX, CO, PE, CL, AR sin ambigüedad
playwright_required: false                  # tooling check, no E2E
graders:
  - type: grep
    pattern: "(vos|sos|tenés|podés|mirá|andá|fijate)\\b"
    path: "vitalia/frontend/src/features/lisa/components/marca/"
    expect: "0_matches"
  - type: grep
    pattern: "(laburo|quilombo|pibe|che|dale)\\b"
    path: "vitalia/frontend/src/features/lisa/components/marca/"
    expect: "0_matches"
```

---

## § Wireframes inline (ASCII)

> Mockups HTML detallados por componente: `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/{identidad-section,voz-tono-section,landing-presencia-section}.html` (gate bloqueante overlay `shell-mockup-per-component.md` — producir en próximo turn).

### Layout root — LisaMarcaView con tabs internas

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Lisa › Marca                                              [⚙][🔔][👤]    │  ← top bar shell-organism (heredado)
├─────────────────────────────────────────────────────────────────────────┤
│ [Lisa] [Lucas] [Adrián] [Valeria] [Camila] [Configurar]                 │  ← ribbon 6 tabs (heredado)
├─────────────────────────────────────────────────────────────────────────┤
│ [Marca]  [Doctores]  [Servicios]  [Compliance]                          │  ← sub-tabs Lisa (heredado F1-S8)
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┬─────────────────┬─────────────────┐                  │
│  │  Identidad  ✓   │  Voz y tono  ○  │  Landing  ○     │  ← Shadcn Tabs   │
│  └─────────────────┴─────────────────┴─────────────────┘                  │
│                                                                           │
│  {Panel del tab activo — ver sub-wireframes abajo}                        │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tab Identidad (panel)

```
┌──────────────────────────────────────────────────────────────┐
│  Identidad de tu clínica                                       │
│  Esta información personaliza la voz de Valeria y la marca     │
│  visible en tu landing pública.                                │
│                                                                  │
│  ┌── Datos básicos ───────────────────────────────────────┐    │
│  │ Nombre clínica       [ Clínica Dental Lima Centro    ] │    │
│  │ Slug público         [ clinica-dental-lima      ] (RO) │    │  ← read-only, cambio en config
│  │ Tagline (opcional)   [ Sonrisas que cuidan tu salud  ] │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Vertical y especialidades (read-only) ───────────────┐    │
│  │ Modelo de negocio:   🏥 Clínica dental                  │    │
│  │ Especialidades:      [Odontología general]              │    │
│  │                      [Odontología estética]             │    │
│  │                      [Ortopedia maxilar]                │    │
│  │ → Editar configuración inicial                          │    │  ← link a /onboarding/clinic-config
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Logo + colores ───────────────────────────────────────┐    │
│  │ Logo principal       [drop-zone con preview]            │    │
│  │ Color primario       [⬛ #1A8FE0 ] hex                  │    │
│  │ Color acento         [⬛ #FF6F61 ] hex                  │    │
│  │ Fondo                [⬜ #FFFFFF ] hex                  │    │
│  │                                                          │    │
│  │ [⌗ Extraer desde mi sitio web] (disabled)               │    │  ← stub D2 pending /pm-luana
│  │   tooltip: "Próximamente — extracción automática"       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Tipografía ───────────────────────────────────────────┐    │
│  │ Fuente títulos       [ Inter ▼ ]                        │    │
│  │ Fuente cuerpo        [ Inter ▼ ]                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Equipo (read-only preview) ──────────────────────────┐    │
│  │ Doctores destacados (3 de 8)                            │    │
│  │  [👨🏼‍⚕️ Dr. Pérez] [👩🏽‍⚕️ Dra. López] [👨🏿‍⚕️ Dr. Tan]                │    │
│  │ → Gestionar equipo                                       │    │  ← link a /lisa/doctores
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  💾 Guardado hace 2s                                            │    │  ← autosave indicator footer
└──────────────────────────────────────────────────────────────┘
```

### Tab Voz y tono (panel)

```
┌──────────────────────────────────────────────────────────────┐
│  Voz y tono de tu marca                                        │
│  Definí cómo tu clínica habla con pacientes. Esto alimenta     │
│  directamente a Valeria y Camila al conversar.                 │
│                                                                  │
│  ┌── Arquetipo (sugerido por tu especialidad) ────────────┐    │
│  │ Arquetipo principal:   ⊙ Caregiver (Cuidador) recomendado│   │
│  │                        ○ Sage (Sabio)                    │    │
│  │                        ○ Healer (Sanador)                │    │
│  │                        ○ Hero (Héroe)                    │    │
│  │ Tooltip Caregiver: "Habla con calidez, prioriza el       │    │
│  │   bienestar del paciente, evita lenguaje técnico frío."  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── ASÍ HABLO (vocabulario, frases que te representan) ──┐    │
│  │ [textarea autosave]                                     │    │
│  │ Ejemplo:                                                 │    │
│  │  - "Acompañamos tu tratamiento con cuidado"              │    │
│  │  - "Te explicamos cada paso del procedimiento"           │    │
│  │  - "Tu salud es nuestra prioridad"                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── ASÍ NO HABLO (lo que evitamos) ──────────────────────┐    │
│  │ [textarea autosave]                                     │    │
│  │ Ejemplo:                                                 │    │
│  │  - "Garantizamos curar"  ⚠️ Lenguaje no permitido salud   │    │  ← warning soft inline
│  │  - "Sin riesgos"                                          │    │
│  │ ⚠️ Sugerencia: usar "protocolos avalados" o "respaldados"│    │
│  │ [Guardar igual con esta frase]                            │    │  ← override con audit
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Preview compilado del agente ────────────────────────┐    │
│  │ Así te escuchará un paciente al conversar con Valeria:  │    │
│  │ ┌─────────────────────────────────────────────────────┐ │    │
│  │ │ "Hola, soy Valeria. Acompañamos tu tratamiento con   │ │    │
│  │ │  el cuidado que tu salud merece. ¿Cómo puedo ayudarte│ │    │
│  │ │  hoy?"                                                │ │    │
│  │ └─────────────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  💾 Guardado hace 5s                                            │    │
└──────────────────────────────────────────────────────────────┘
```

### Tab Landing y presencia (panel)

```
┌──────────────────────────────────────────────────────────────┐
│  Landing pública y presencia digital                           │
│                                                                  │
│  ┌── Landing pública Vitalia ──────────────────────────────┐   │
│  │ URL pública:  https://clinica-dental-lima.vitalia.app  │   │
│  │ [👁 Ver landing] [📋 Copiar link]                        │   │
│  │ Última actualización: hace 2 días                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌── Sitio web propio ─────────────────────────────────────┐   │
│  │ URL sitio web:  [ https://clinicadentallima.com.pe  ]  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌── Redes sociales ───────────────────────────────────────┐   │
│  │ Instagram:        [ @clinicadentallima               ]   │   │
│  │ TikTok:           [ @clinicadental_lima              ]   │   │
│  │ Facebook:         [ ClinicaDentalLima                ]   │   │
│  │ Google Business:  [ link a perfil GMB                ]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌── Trust signals ────────────────────────────────────────┐   │
│  │ Certificaciones (drag&drop logos):                       │   │
│  │  [DIGESA] [Colegio Odontólogos PE] [+ Agregar]          │   │
│  │ Años de experiencia: [ 15 ]                              │   │
│  │ Pacientes atendidos (opcional): [ 8000+ ]                │   │
│  │ Premios: [textarea]                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  💾 Guardado hace 12s                                           │    │
└──────────────────────────────────────────────────────────────┘
```

---

## § Estados visuales (tabla)

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle` | Mount inicial | `SkeletonTabs` (3 tabs gris) + `SkeletonForm` (campos placeholder) | Forms reales |
| `loading-fetch` | React Query fetch inicial | `<Skeleton>` por sub-sección + spinner sutil | Forms |
| `success-with-data` | Data hidratada | Tabs + Forms + `data-state="success"` | Skeletons, EmptyState |
| `success-empty` | Tenant nuevo sin brand data | `EmptyStateHero` con CTA "Empezar" | Forms |
| `editing` | User edita field | Form fields + `[data-dirty=true]` | EmptyState |
| `saving` | Autosave debounce flush | Toast tiny "Guardando..." + spinner inline en field | Toast "Guardado" |
| `saved` | Mutation success | Toast tiny "Guardado" (3s ámbar fade) | Toast "Guardando" |
| `error-network` | Mutation fail timeout/5xx | Alert variant="error" inline + botón "Reintentar" + counter retry | Toast saved |
| `voice-warning` | Voice phrase blocked | Alert variant="warning" inline + sugerencia + botón "Guardar igual" | — |
| `cross-tenant-403` | Backend rechaza | Toast variant="error" "No tenés permiso" + log audit | — |
| `logo-too-large` | Client-side size validation fail | Inline error en drop-zone | Preview logo |
| `dark-theme-active` | User toggle theme | Mismo layout con tokens dark CSS vars | — |
| `mobile-stacked` | < 768px | Tabs colapsadas a Accordion vertical + form full-width | Tabs horizontal |
| `keyboard-focus-visible` | Tab keyboard nav | `focus:ring-2 focus:ring-primary` en elemento activo | — |

---

## § Componentes (path-by-path)

### Reusar (Shadcn primitives + shell-organism heredado)

| Componente | Path | Origen |
|---|---|---|
| `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | `vitalia/frontend/src/components/ui/tabs.tsx` | shipped F1-S0 |
| `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` | `vitalia/frontend/src/components/ui/form.tsx` | shipped F2-S1 |
| `Input`, `Textarea`, `Button`, `Alert`, `Tooltip`, `Avatar`, `Badge`, `Separator`, `Skeleton`, `Sonner` (toast) | `vitalia/frontend/src/components/ui/*.tsx` | shipped F1-S0+ |
| `Card`, `Select`, `Popover`, `Sheet` | `vitalia/frontend/src/components/ui/*.tsx` | shipped F2-S1 |
| `LisaSidebar`, `RibbonTab`, `SubTabsBar`, `SubTabContent` | `vitalia/frontend/src/components/shared/shell-organism/*` | shipped F1-S5..S9 |
| `EmptyState`, `EmptyStateInline` | `vitalia/frontend/src/components/shared/shell-organism/EmptyState*.tsx` | shipped F1-S10 |

### Nuevo en esta story

| Componente | Path NUEVO | Justificación |
|---|---|---|
| `LisaMarcaView` (root client) | `vitalia/frontend/src/features/lisa/components/marca/LisaMarcaView.tsx` | Entry desde page.tsx — 3 tabs internas |
| `IdentidadSection` | `vitalia/frontend/src/features/lisa/components/marca/IdentidadSection.tsx` | Panel tab Identidad |
| `VozTonoSection` | `vitalia/frontend/src/features/lisa/components/marca/VozTonoSection.tsx` | Panel tab Voz y tono — archetype selector + dual textarea + preview compilado |
| `LandingPresenciaSection` | `vitalia/frontend/src/features/lisa/components/marca/LandingPresenciaSection.tsx` | Panel tab Landing y presencia |
| `LogoDropZone` | `vitalia/frontend/src/features/lisa/components/marca/LogoDropZone.tsx` | Logo upload con preview + size validation |
| `ColorTriadEditor` | `vitalia/frontend/src/features/lisa/components/marca/ColorTriadEditor.tsx` | 3 color pickers (primary/accent/background) + hex input + accessibility contrast warning |
| `ClinicVerticalReadOnly` | `vitalia/frontend/src/features/lisa/components/marca/ClinicVerticalReadOnly.tsx` | Display read-only `clinic_vertical` + `primary_specialties` + edit-link |
| `TeamPreviewRow` | `vitalia/frontend/src/features/lisa/components/marca/TeamPreviewRow.tsx` | Avatars row (max 3 visible) + counter "+5 más" + link "Gestionar equipo" |
| `ArchetypeSelector` | `vitalia/frontend/src/features/lisa/components/marca/ArchetypeSelector.tsx` | Radio cards 4 archetypes salud-friendly + tooltips |
| `VoiceTextareaWithWarning` | `vitalia/frontend/src/features/lisa/components/marca/VoiceTextareaWithWarning.tsx` | Textarea con detector blocklist + soft warning + override |
| `BrandVoicePreview` | `vitalia/frontend/src/features/lisa/components/marca/BrandVoicePreview.tsx` | Preview compilado fragment BRAND_VOICE (debounced server fetch) |
| `TrustSignalsEditor` | `vitalia/frontend/src/features/lisa/components/marca/TrustSignalsEditor.tsx` | Certificaciones drag+drop + years exp + patients count + premios textarea |
| `SocialMediaLinksEditor` | `vitalia/frontend/src/features/lisa/components/marca/SocialMediaLinksEditor.tsx` | IG/TikTok/FB/GMB inputs con validation URL/handle |
| `AutosaveBadge` | `vitalia/frontend/src/features/lisa/components/marca/AutosaveBadge.tsx` | Footer "Guardado hace Xs" con states (saving/saved/error/dirty) |

---

## § Data flow (conceptual — `/architect-fe` concreta detalle)

### API endpoints (BE — `/architect-be` define schema)

```
GET  /api/v1/lisa/marca/identity                  → BrandIdentityDTO
GET  /api/v1/lisa/marca/visuals                   → BrandVisualsDTO
GET  /api/v1/lisa/marca/personality               → PersonalityProfileDTO
GET  /api/v1/lisa/marca/contact                   → BrandContactDTO
GET  /api/v1/lisa/marca/team                      → BrandTeamPreviewDTO (read-only, top 3)
GET  /api/v1/lisa/marca/clinic-config             → ClinicConfigDTO (read-only: vertical + specialties)
GET  /api/v1/lisa/marca/voice-preview             → VoicePreviewDTO (compiled BRAND_VOICE fragment)

PATCH /api/v1/lisa/marca/identity                 → 200 + audit row
PATCH /api/v1/lisa/marca/visuals                  → 200 + audit row
PATCH /api/v1/lisa/marca/personality              → 200 + audit row + voice_warning_count (si override)
PATCH /api/v1/lisa/marca/contact                  → 200 + audit row

POST  /api/v1/lisa/marca/logos                    → 200 + S3 URL + audit row (multipart upload)
DELETE /api/v1/lisa/marca/logos/{id}              → 204 + audit row

POST  /api/v1/lisa/marca/voice-warning-override   → 201 audit_log row (action=voice_warning_overridden)
```

### React Query keys (convención ADR-004 § 3.4)

```typescript
['brand_studio', 'marca', 'identity', { tenantId }]
['brand_studio', 'marca', 'visuals', { tenantId }]
['brand_studio', 'marca', 'personality', { tenantId }]
['brand_studio', 'marca', 'contact', { tenantId }]
['brand_studio', 'marca', 'team-preview', { tenantId, limit: 3 }]
['brand_studio', 'marca', 'clinic-config', { tenantId }]            // shared with onboarding-clinica
['brand_studio', 'marca', 'voice-preview', { tenantId, debounceHash }]
```

### Mutations (autosave debounce 600ms per ADR-004 § 3.5)

```typescript
// useIdentityAutosave hook
const { mutate } = useMutation({
  mutationFn: (patch: Partial<BrandIdentity>) =>
    patchBrandIdentity({ tenantId, patch }),
  onSuccess: (updated) => {
    queryClient.setQueryData(['brand_studio', 'marca', 'identity', { tenantId }], updated)
    toast.success('Guardado', { duration: 3000 })
  },
  onError: (err) => {
    toast.error('No pudimos guardar. Reintentar.', { action: { label: 'Reintentar', onClick: () => mutate(...) } })
  },
})
```

### Forms (RHF + Zod per ADR-004 § 3.5)

```typescript
// identity-schema.ts (IMPORT from nicolify + ADAPT)
import { z } from 'zod'

export const identitySchema = z.object({
  name: z.string().min(2).max(100),
  tagline: z.string().max(150).optional(),
  // slug es read-only (lectura desde tenant.subdomain)
})

export type IdentityFormValues = z.infer<typeof identitySchema>
```

### Zustand stores (UI state only)

```typescript
// marca-store.ts
interface MarcaUIState {
  activeTab: 'identidad' | 'voz_tono' | 'landing'
  setActiveTab: (tab: MarcaTab) => void
  pendingVoiceOverride: { phrase: string; section: string } | null
  setPendingVoiceOverride: (override: ...) => void
}
```

---

## § Microcopy (Spanish neutro LatAm — auditado contra `.claude/rules/spanish-text.md`)

| Lugar | Copy |
|---|---|
| Page title shell | "Lisa · Marca" |
| Tab Identidad label | "Identidad" |
| Tab Voz y tono label | "Voz y tono" |
| Tab Landing label | "Landing y presencia" |
| Hero subtitle Identidad | "Esta información personaliza la voz de Valeria y la marca visible en tu landing pública." |
| Hero subtitle Voz | "Definí cómo tu clínica habla con pacientes. Esto alimenta directamente a Valeria y Camila al conversar." |
| Hero subtitle Landing | "Conectá tu presencia digital y mostrá la autoridad de tu clínica." |
| Field "Nombre clínica" label | "Nombre de la clínica" |
| Field "Slug público" hint | "Tu URL en Vitalia. Para cambiarla, andá a Configurar." |
| Field "Tagline" placeholder | "Ej: Sonrisas que cuidan tu salud" |
| Section "Vertical y especialidades" label | "Modelo de negocio y especialidades" |
| Edit-link clinic_vertical | "Editar configuración inicial" |
| Logo drop-zone empty | "Arrastrá tu logo o seleccionalo. PNG, JPG o WebP, máximo 5 MB." |
| Logo upload error oversized | "Logo máximo 5 MB. Tu archivo tiene {N} MB. Comprimí la imagen." |
| Color picker label | "Color primario / acento / fondo" |
| Extract from website button | "Extraer desde mi sitio web" |
| Extract from website tooltip (disabled) | "Próximamente — extracción automática de paleta y tipografía" |
| Section "Equipo (preview)" | "Equipo destacado (preview)" |
| Edit-link team | "Gestionar equipo completo" |
| Archetype selector label | "Arquetipo principal de tu marca" |
| Archetype Caregiver tooltip | "Habla con calidez, prioriza el bienestar del paciente, evita lenguaje técnico frío. Recomendado para clínicas." |
| Archetype Sage tooltip | "Comunica conocimiento, expertise, datos. Profesional y educativo." |
| Archetype Healer tooltip | "Tono empático y restaurador. Foca en proceso de sanación." |
| Archetype Hero tooltip | "Inspirador, transforma. Resalta logros y superación del paciente." |
| Textarea "ASÍ HABLO" placeholder | "Ej: 'Acompañamos tu tratamiento con cuidado'" |
| Textarea "ASÍ NO HABLO" placeholder | "Ej: Frases que evitamos por tono o regulación" |
| Voice warning soft | "Esta frase usa lenguaje que puede violar regulaciones de salud ({palabras_detectadas}). Considerá: '{sugerencia}'." |
| Voice warning override button | "Guardar igual con esta frase" |
| Voice preview header | "Así te escuchará un paciente al conversar con Valeria:" |
| Landing public URL label | "URL pública en Vitalia" |
| Landing view button | "Ver landing" |
| Landing copy link button | "Copiar link" |
| Sitio web propio field | "Tu sitio web propio (si tenés)" |
| Trust signals certs add | "Agregar certificación" |
| Trust signals años exp | "Años de experiencia" |
| Autosave saving | "Guardando..." |
| Autosave saved | "Guardado" |
| Autosave saved-with-warning | "Guardado con advertencia" |
| Autosave error | "No pudimos guardar tu cambio. Reintentar." |
| Autosave retry button | "Reintentar" |
| Autosave footer indicator | "💾 Guardado hace {N}s" |
| Empty state Identidad heading | "Configurá tu identidad de marca" |
| Empty state Identidad body | "Vitalia personaliza la conversación de tus agentes con la voz y estilo de tu clínica. Llevate 5 minutos." |
| Empty state CTA | "Empezar" |
| Cross-tenant 403 toast | "No tenés permiso para editar esta marca." |
| Concurrent edit notification | "Esta sección fue editada por otro usuario hace {N} segundos. Recargá para ver cambios." |
| Confirm modal voice override | "Esta frase puede generar advertencias en compliance. ¿Confirmás guardarla igual?" |
| Confirm modal logo replace | "¿Reemplazar el logo actual? El cambio se aplica al instante en tu landing pública." |

<!-- voseo-allowed: Spanish neutro forbidden words listing -->
**Verificación voseo (palabras prohibidas):** `vos`, `sos`, `tenés`, `podés`, `mirá`, `andá`, `fijate`, `dale`, `laburo`, `quilombo`, `pibe`, `che` → 0 ocurrencias en copy arriba.

---

## § Responsive breakpoints

| Breakpoint | Layout adapt |
|---|---|
| `< 640px` (mobile) | Tabs → Accordion vertical. Form fields full-width. Avatars team → grid 2 col. Color triad → stack vertical. |
| `640-768px` (tablet small) | Tabs visible compactas (icon + label). Form 1-col. |
| `768-1024px` (tablet) | Tabs full. Form 1-col con max-width 720px centrado. Sidebar shell visible compacta. |
| `> 1024px` (desktop) | Tabs full. Form 2-col donde aplique (Color triad horizontal). Sidebar shell full. |

---

## § Accessibility (WCAG AA mandatory)

- ARIA labels en todos los inputs (`aria-label` o `aria-labelledby`)
- Focus visible (`focus:ring-2 focus:ring-primary focus:ring-offset-2`)
- Keyboard nav: Tab order lógico topbar → ribbon → sub-tabs → tabs internas → form fields → autosave indicator
- Arrow keys cycle tabs internas (Shadcn `Tabs` default)
- Contrast ratio ≥ 4.5:1 (text) y ≥ 3:1 (UI components) — verificado por `axe-core/playwright`
- Toast `sonner` con `aria-live="polite"`
- Alert errors con `role="alert"` + `aria-live="assertive"`
- Color picker accesible: Enter abre popover, Esc cierra, Tab cycle dentro
- Logo drop-zone keyboard-friendly: Enter abre file picker
- Voice warning announced via screen reader (no solo visual)
- Form errors anchored al field con `aria-describedby`
- Skip-link al inicio del page si form muy largo

---

## § Telemetría (eventos `growth_studio_event` — ADR-004 § 3.8)

```yaml
events:
  - name: lisa_marca_viewed
    trigger: page mount
    props: [tab_initial]
  - name: lisa_marca_tab_changed
    trigger: tab click
    props: [tab_from, tab_to]
  - name: lisa_marca_identity_saved
    trigger: autosave success identity
    props: [field_count_changed]
  - name: lisa_marca_visuals_saved
    trigger: autosave success visuals
    props: [field_count_changed, has_logo]
  - name: lisa_marca_personality_saved
    trigger: autosave success personality
    props: [archetype, voice_warning_triggered]
  - name: lisa_marca_voice_warning_shown
    trigger: blocklist phrase detected
    props: [phrase_severity, suggested_alternative_present]
  - name: lisa_marca_voice_warning_overridden
    trigger: user click "Guardar igual"
    props: [phrase_severity]
  - name: lisa_marca_logo_uploaded
    trigger: logo upload success
    props: [file_size_bucket, format]
  - name: lisa_marca_logo_oversized
    trigger: client-side size validation fail
    props: [file_size_mb_int]
  - name: lisa_marca_extract_website_clicked
    trigger: click extract button (currently disabled — track desire)
    props: []
  - name: lisa_marca_team_preview_clicked
    trigger: click "Gestionar equipo" link
    props: []
  - name: lisa_marca_clinic_config_edit_clicked
    trigger: click "Editar configuración inicial" link
    props: []
  - name: lisa_marca_autosave_failed
    trigger: mutation error
    props: [error_type, retry_count]
```

**PHI-safe:** todos los payloads son metadata (no contenido user-facing verbatim). `phrase_severity` es enum bucketed (low/medium/high), `field_count_changed` es int, etc.

---

## § Brand voice usage (esta story EDITA el SSoT)

Esta story es la UI principal donde owner configura `personality_profiles.system_instruction` (slot 5 BRAND_VOICE del compiler v2 sales-agent). Por tanto:

- Output del compiler v2 cambia inmediatamente tras autosave personality (cache prefix ≥1024 tokens estable → invalidation natural)
- Tests de fidelidad voice (`vitalia/backend/tests/agentic_evals/grader/test_voice_fidelity_per_fixture.py`) deben pasar con golden fixtures pre/post-edit
- **NO inyectar tenant context mid-block** (creep guard rule `.claude/rules/sales-agent-brand-voice.md`)

---

## § ADR-vitalia-004 compliance (v1.1 — N3-static cementado)

Esta story cumple las 9 secciones del patrón + § 3.1.1 N3-static SubSubTabsBar:

| § ADR-004 | Aplicación lisa-marca v2 |
|---|---|
| 1 Routing | **★ v2: N3-static.** `app/[tenantId]/(shell-organism)/lisa/marca/page.tsx` (redirect a `/lisa/marca/identidad`) + `lisa/marca/identidad/page.tsx` + `lisa/marca/voz-y-tono/page.tsx` + `lisa/marca/presencia/page.tsx` (Server Components con SSR initial state per subsubtab) |
| 1.1 N3-static | **★ v2: SubSubTabsBar** en cabecera renderiza si `AGENT_SUBSUBTABS[lisa][marca]?.length > 0`. Entry catalog: `lisa.marca = ['identidad', 'voz-y-tono', 'presencia']` agregar a `shell-routes.ts` |
| 2 FSD-Lite | **★ v2: nested per subsubtab.** `features/lisa/components/marca/{identidad,voz-y-tono,presencia}/` + `api/` + `hooks/` + `store/` + `types/` |
| 3 Client root | **★ v2: 3 vistas root.** `IdentidadView.tsx`, `VozTonoView.tsx`, `PresenciaView.tsx` con `"use client"` + props initial hidratados per subsubtab |
| 4 Data layer | React Query (fetch + mutations) + Zustand (`marca-store.ts` UI state global cross-subsubtab) — NO mezcla |
| 5 Forms | RHF + Zod schemas per subsubtab (identity-schema, visuals-schema, personality-schema, contact-schema, social-schema, trust-signals-schema) + autosave 600ms debounce |
| 6 BE DDD | `vitalia/backend/src/modules/vitalia/brand_studio/{domain,infrastructure,application,api}/` extended; consume engine `core/luana-core-brand-studio`; NEW `prohibited_phrases` repository hereda `Repository` base (no PHI) |
| 7 Migrations | NEW tabla `vitalia_prohibited_phrases` raw SQL `CREATE TABLE IF NOT EXISTS` |
| 8 Telemetría | 13 events en `vitalia_growth_studio_event` (extender propname con `subsubtab` field) |
| 9 Tests | Vitest unit + Playwright funcional (10 specs cross-subsubtab) + visual goldens (3 subsubtabs × 2 themes = 6 PNGs) + axe + BE pytest cross-tenant + arch fitness EXTEND |

**adr_004_compliance:** `full` (v1.1 N3-static aplicado).
**adr_004_subsubtabs_count:** 3 (`identidad`, `voz-y-tono`, `presencia`)
**adr_004_default_subsubtab:** `identidad` (primera entry del array per convention)

---

## § Deliverables (preliminar — `/architect` concreta paths exactos en `03-arch.md`)

### Frontend

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/page.tsx` | NEW Server Component |
| `vitalia/frontend/src/features/lisa/components/marca/LisaMarcaView.tsx` | NEW client root |
| `vitalia/frontend/src/features/lisa/components/marca/{IdentidadSection,VozTonoSection,LandingPresenciaSection}.tsx` | NEW × 3 |
| `vitalia/frontend/src/features/lisa/components/marca/{LogoDropZone,ColorTriadEditor,ClinicVerticalReadOnly,TeamPreviewRow,ArchetypeSelector,VoiceTextareaWithWarning,BrandVoicePreview,TrustSignalsEditor,SocialMediaLinksEditor,AutosaveBadge}.tsx` | NEW × 10 |
| `vitalia/frontend/src/features/lisa/api/marca.ts` | NEW (React Query hooks) |
| `vitalia/frontend/src/features/lisa/api/marca-server.ts` | NEW (`getInitialMarcaState` SSR) |
| `vitalia/frontend/src/features/lisa/store/marca-store.ts` | NEW (Zustand UI state) |
| `vitalia/frontend/src/features/lisa/hooks/{useIdentityAutosave,useVisualsAutosave,usePersonalityAutosave,useVoicePreview,useVoiceBlocklist}.ts` | NEW × 5 |
| `vitalia/frontend/src/features/lisa/types/marca/{identity,visuals,personality,contact,team-preview,clinic-config,voice-preview,prohibited-phrase}-schema.ts` | NEW × 8 (Zod schemas — IMPORT base nicolify + ADAPT salud) |
| `vitalia/frontend/src/features/lisa/types/marca.types.ts` | NEW (TypeScript types) |
| `vitalia/frontend/src/app/(dashboard)/brand-studio/[section]/page.tsx` | DELETE post-merge |
| `vitalia/frontend/src/features/vitalia/components/brand-studio-section-client.tsx` | DELETE post-merge (refactored en lisa) |

### Backend

| File | Acción |
|---|---|
| `vitalia/backend/src/modules/vitalia/brand_studio/api/marca_router.py` | NEW (FastAPI router con 11 endpoints arriba) |
| `vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py` | NEW (Pydantic v2 DTOs response_model) |
| `vitalia/backend/src/modules/vitalia/brand_studio/application/services/marca_service.py` | NEW (orquesta engine consume + audit) |
| `vitalia/backend/src/modules/vitalia/brand_studio/application/services/voice_blocklist_service.py` | NEW (CRUD + seed defaults) |
| `vitalia/backend/src/modules/vitalia/brand_studio/application/services/voice_preview_service.py` | NEW (compila slot BRAND_VOICE preview sin invocar LLM) |
| `vitalia/backend/src/modules/vitalia/brand_studio/domain/prohibited_phrase.py` | NEW dataclass |
| `vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/prohibited_phrase_repository.py` | NEW |
| `vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/models/prohibited_phrase_model.py` | NEW SQLA model |
| `vitalia/backend/alembic/versions/0XX_vitalia_lisa_marca_prohibited_phrases.py` | NEW migration idempotent (CREATE TABLE IF NOT EXISTS `vitalia_prohibited_phrases` + seed defaults via INSERT ON CONFLICT) |
| `vitalia/backend/scripts/seed_prohibited_phrases_defaults.py` | NEW (idempotent seed: 10-15 phrases salud default per `clinic_vertical`) |
| `vitalia/backend/src/modules/vitalia/brand_studio/application/services/health_voice_validator.py` | **NUNCA CREAR** — explícitamente eliminado del scope per § Voice architecture |

### Tests

| File | Acción |
|---|---|
| `vitalia/frontend/e2e/shell-organism/lisa-marca-identidad-autosave.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-voice-warning.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-logo-upload-size.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-race-autosave.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-concurrent-owners.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-autosave-timeout.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-empty-state.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-large-dataset.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-marca-a11y-keyboard.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/{identidad,voz-tono,landing-presencia}-{light,dark}.png` | NEW × 6 visual goldens |
| `vitalia/frontend/src/features/lisa/components/marca/__tests__/*.test.tsx` | NEW Vitest unit per componente |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_marca_service.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_voice_blocklist_service.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_marca_cross_tenant.py` | NEW (adversarial scenario) |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_seed.py` | NEW (anti-regression seed default) |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_voice_warning_audit_log.py` | NEW |
| `vitalia/backend/tests/architecture/test_no_health_voice_validator.py` | NEW (bloquea regresión `health_voice_validator.py` accidental — creep guard) |

### Mockups HTML (gate bloqueante overlay `shell-mockup-per-component.md`)

| File | Acción |
|---|---|
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/identidad-section.html` | NEW (próximo turn) |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/voz-tono-section.html` | NEW (próximo turn) |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/landing-presencia-section.html` | NEW (próximo turn) |

---

## § Ratified decisions (referenciadas en checkpoint.md)

| ID | Decisión | Source turn |
|---|---|---|
| D1-arch | Citar ADR-vitalia-004 verbatim — patrón replicable transversal | Chris 2026-05-26 |
| D2-voice | Eliminar `health_voice_validator.py`. Reuse compiler v2 + `ComplianceService`. NEW tabla `vitalia_prohibited_phrases` soft warning configurable | Chris 2026-05-26 |
| D3-clinic | `clinic_vertical` + `primary_specialties` se capturan en `vitalia-fase2-config-onboarding-clinica` (story paralela). lisa-marca los muestra **read-only** con edit-link | Chris 2026-05-26 |
| D4-extract | Visual extraction pipeline = **stub local + botón disabled** hasta `/pm-luana` accept proposal `2026-05-26-lift-brand-visual-extraction-to-core.md` | Chris 2026-05-26 |
| D5-archetype | Subset Jung salud-friendly (Caregiver default + Sage + Healer + Hero) — omit problematic (Outlaw/Magician para salud) | Cementada en `personality-schema.ts` adapter — Chris ratifica en próxima iter |

---

## § Open questions — RESUELTAS 2026-05-27 (Chris ratify + defaults aplicados)

| # | Pregunta | Resolución | Razón |
|---|---|---|---|
| OQ-A | Tabs internas vs sub-routing | **RESUELTA v2** → N3-static SubSubTabsBar cabecera con sub-routing `[subtab]/[subsubtab]/page.tsx` (ADR-vitalia-004 v1.1 § 3.1.1). Tabs body = Nivel 4 anti-pattern. | Cementación arquitectónica v1.1 |
| OQ-B | 4 vs 6 archetypes salud-friendly | **(A) 4 archetypes** (Caregiver default / Sage / Healer / Hero). Omit Outlaw, Magician, Lover, Innocent. | Decision paralysis < expresividad ganada · salud requiere tono apropiado siempre |
| OQ-C | `BrandVoicePreview` BE endpoint vs client-side | **(A) Backend endpoint `/lisa/marca/voice-preview`** consume compiler v2 sales-agent + retorna sample dos canales (WhatsApp + email reactivación). | Single SSoT compilación · cache server por personality_profile hash · evita duplicar slot logic en FE |
| OQ-D | Trust certs catalog | **(A) Hybrid: catalog cerrado per país (PE/AR/CL/CO/MX/BR) + free-text "Otra"**. Seed PE: DIGESA, MINSA, SUSALUD, Colegio Odontólogos PE, Colegio Médico PE, SUNAT, ISO 9001, ESSALUD. | Catalog facilita filterable + autoridad reconocible + free-text válvula escape |
| OQ-E | Preview placement | **(A) Footer único** debajo del card "Tratamiento y idioma" en sub-sub-tab Voz y tono. Refresh on autosave 600ms debounce. | Inline distrae · footer único refresh visible al guardar cualquier campo voz

---

## § Referencias

- **ADR transversal:** `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`
- **Design Contract visual:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Mockup gate:** `vitalia/.claude/rules/shell-mockup-per-component.md` + `ADR-vitalia-003`
- **Architecture mandatory:** `vitalia/.claude/rules/shell-feature-architecture-mandatory.md`
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Sales-agent brand voice (anti-creep):** `.claude/rules/sales-agent-brand-voice.md`
- **Spanish neutro glosario:** `.claude/rules/spanish-text.md`
- **Engine brand_studio:** `core/luana-core-brand-studio/`
- **Engine sales-agent compiler v2:** `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py`
- **Engine compliance:** `core/luana-core-compliance/`
- **Vitalia legacy refactor source:** `vitalia/frontend/src/features/vitalia/components/brand-studio-section-client.tsx`
- **Nicolify schemas IMPORT source:** `nicolify/frontend/src/features/brand-studio/schemas/`
- **Story paralela onboarding:** `vitalia/docs/product/stories/vitalia-fase2-config-onboarding-clinica/01-spec.md`
- **Promotion proposal D2:** `docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md`
- **Source story patrón:** `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md`
- **brand-expert skill:** PersonalityProfile + Jung + StoryBrand context
- **sales-agent-expert skill:** voice compiler v2 + slot architecture

---

## § Definición de "Done" (gate refining → refined) — GATE GREEN 2026-05-27

- [x] 4 scenarios base + 7 sub-categorías mandatory v4.1 = 11 scenarios cubiertos
- [x] Cada scenario funcional FE tiene `playwright_required: true`
- [x] Graders declarados per scenario (e2e + state_check + visual_state + axe)
- [x] Wireframes ASCII por sub-sección
- [x] 3 mockups HTML v2.1 con shell wrapper canónico-fiel + splitter responsive (gate bloqueante overlay) — ratificados 2026-05-27
- [x] Ratificados visualmente por Chris (`ratified_visual_by_chris: true`) — iter v2.1
- [x] Microcopy Spanish neutro auditado
- [x] Reuse map exhaustivo (subagent enrichment integrado)
- [x] Voice architecture anti-creep alineada a rule sales-agent
- [x] Componentes reuse vs new justificados
- [x] Responsive breakpoints declarados
- [x] Accessibility section WCAG AA
- [x] Telemetría events declarados PHI-safe
- [x] ADR-vitalia-004 citado en frontmatter + compliance: full
- [x] Open questions resueltas con defaults aplicados (OQ-A..E)
- [x] Ratificado Chris (`ratified_by_chris: true`) — 2026-05-27

✅ **Transition `refining → refined` ejecutada 2026-05-27** → handoff `/architect` autochain autorizado por Chris.
