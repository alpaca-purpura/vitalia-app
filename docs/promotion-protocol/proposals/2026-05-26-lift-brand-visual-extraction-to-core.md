<!-- voseo-allowed: internal promotion proposal, not user-facing -->

# Promotion Proposal — Lift Brand Visual Extraction Pipeline to `core/luana-core-brand-studio`

| Campo | Valor |
|---|---|
| **Proposal ID** | 2026-05-26-lift-brand-visual-extraction-to-core |
| **State** | `accepted` (/pm-luana 2026-06-06 · ratificado Chris · prioridad menor, detrás del shell · EP TBD + verificar source backup antes del lift) |
| **Spawned from** | `/po-ux` session refining `vitalia-fase2-lisa-marca` (2026-05-26) |
| **Initiator** | Chris (ratificó escalation 2026-05-26 D2=A) |
| **Target package** | `core/luana-core-brand-studio` |
| **Target extension point** | EP-1 (FieldOverride) o NEW EP-N tooling (TBD `/pm-luana`) |
| **Source evidence** | `/home/chalreme/Documentos/ap_sales_agent/.planning/quick/260319-g7y-fix-brand-studio-visual-identity-extract/` |
| **Beneficiarios** | vitalia (lisa-marca Identidad), nicolify (brand-studio existing), comunify (creator brand setup), lupulo (futuro), 6 brands bootstrap pendientes |

---

## /pm-luana review (under_review · 2026-06-06)

**Recomendación: ACCEPT en principio, PRIORIDAD MENOR** — es un lift de FEATURE (pipeline extracción visual de marca → `core-brand-studio`), separado de la convergencia de shell/FE. Beneficio multi-brand claro.

**Abierto antes de APPROVED:** (1) decisión EP — EP-1 (FieldOverride) vs nuevo EP-N tooling (TBD); (2) `Source evidence` apunta a un backup externo (`~/Documentos/ap_sales_agent/...`) — verificar que sigue válido/accesible antes de planear el lift; (3) secuenciar DETRÁS del shell-organism (mayor impacto de convergencia).

**Para ratificar (Chris):** ¿confirmás la dirección + lo dejamos en cola detrás del shell?

---

## § 1 — Context (qué descubrimos)

Durante el reuse-map enrichment para `vitalia-fase2-lisa-marca` (sub-tab Lisa→Marca, sub-sección "Identidad"), un subagente de research detectó en el backup `ap_sales_agent` un pipeline **funcional production-ready** para extracción automática de identidad visual de marca desde URL del sitio web del tenant:

**Pipeline (verbatim del backup):**

```
POST /api/v1/brand/tools/extract
  → CopilotBrandAIActionsService.extract_brand_identity(url)
  → BrandExtractionService.extract_visuals_only(url)
  → crawl_content(url) (HTML fetch + parse)
  → _run_section() con template Jinja2 `brand_extract_visuals.j2`
  → LLM call (LangChain → litellm → Claude/equivalent)
  → returns BrandVisuals JSON
```

**Output schema (`BrandVisuals` aggregate):**

- `primary_color`, `accent_color`, `background_color`, `text_primary_color`, `text_on_primary` (hex)
- `font_heading`, `font_body` (font family)
- `style_preset`, `design_style`, `usage_guidelines` (free-text guidelines)

**FE integration:**

- TypeScript interface `ExtractedVisuals` en `frontend/src/features/brand/types/index.ts`
- `BrandVisualsWizard` UI + `extractBrandVisuals` API fn helper

---

## § 2 — Problem statement (por qué promote ahora)

Existen 3 demands cross-brand ya identificadas + 3 latentes:

| Brand | Caso de uso | Estado |
|---|---|---|
| **vitalia** | Sub-sección Identidad de `lisa-marca` necesita botón "Extraer desde mi sitio web" que auto-popula paleta clínica | active (próxima story) |
| **nicolify** | `brand-studio` shipped pero sin auto-extract (onboarding manual) | gap latente |
| **comunify** | Creator brand setup — auto-extract desde landing personal/website creator | gap latente |
| **lupulo** | Bootstrap pending — necesitará auto-extract gastronomía | futuro |
| **6 brands bootstrap pendientes** | Mismo gap onboarding identity | futuro |

**Si no promovemos:**
- Vitalia re-implementa el pipeline en `vitalia/backend/src/modules/vitalia/brand_studio/application/visual_extraction_service.py` (~600 LOC: service + crawler + prompt + DTO)
- Nicolify hace lo mismo cuando alguien lo pida (mirror cross-brand prohibido per `.claude/rules/anti-duplication.md`)
- Comunify lo replica ad-hoc
- Cada brand mantiene su propio prompt template + tests + retry/timeout/error handling

**Si promovemos:**
- 1 implementación en engine consumida via `from luana_core_brand_studio.application.services import VisualExtractionService` o via tool plugin registered EP-N
- Cada brand opta-in via `{brand}/config/brand.yaml::brand_studio.enable_visual_extraction: true`
- Tests engine + 1 test consumer per brand activa
- Prompt template + retry/timeout/observability cementados centralmente

---

## § 3 — Lift scope propuesto

### § 3.1 — Carve-out source

Files del backup `/home/chalreme/Documentos/ap_sales_agent/`:

```
backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_visuals.j2
backend/src/modules/brand/application/services/brand_extraction_service.py          (método extract_visuals_only)
backend/src/modules/brand/api/routes/extract.py                                      (endpoint POST /brand/tools/extract)
backend/src/modules/brand/domain/visuals.py                                          (aggregate BrandVisuals)
backend/src/modules/brand/infrastructure/crawler.py                                  (crawl_content helper)
frontend/src/features/brand/types/index.ts                                           (ExtractedVisuals interface)
frontend/src/features/brand/api/extract.ts                                           (extractBrandVisuals fn)
frontend/src/features/brand/components/BrandVisualsWizard.tsx                        (UI shell)
backend/tests/modules/brand/test_visual_extraction.py                                (unit + integration)
```

**TBD `/pm-luana`:** confirmar que estos paths del backup todavía existen en alguna release de nicolify y/o si fueron mergeados parcialmente a `core/luana-core-brand-studio` (grep en worktree principal `luana-platform/` requerido).

### § 3.2 — Destino engine

```
core/luana-core-brand-studio/src/luana_core_brand_studio/
├── application/
│   ├── ports/
│   │   └── visual_extraction_port.py        # interface (Port pattern — testeable)
│   └── services/
│       └── visual_extraction_service.py     # default impl con crawler + LLM
├── infrastructure/
│   ├── crawlers/
│   │   └── http_crawler.py                  # crawl_content (extracted to subsystem)
│   └── prompts/
│       └── brand_extract_visuals.j2         # Jinja2 template (moved from copilot/)
└── domain/
    └── visuals.py                            # BrandVisuals aggregate (extend existing if conflict)
```

### § 3.3 — Brand opt-in

```yaml
# {brand}/config/brand.yaml
brand_studio:
  enabled_sections: [identity, contact, team, testimonials]
  enable_visual_extraction: true              # ★ NEW opt-in
  visual_extraction_provider: anthropic       # default; future: openai, local
```

### § 3.4 — Engine arch fitness test

```python
# core/luana-core-brand-studio/tests/architecture/test_visual_extraction_port.py
def test_visual_extraction_port_returns_brand_visuals_aggregate():
    """Toda impl Port retorna BrandVisuals dataclass — no dict raw."""

def test_visual_extraction_does_not_persist_url_verbatim():
    """URL crawleada no se loguea en traces sin sanitize_payload (PII potencial)."""

def test_visual_extraction_respects_compliance_level():
    """Brand con compliance_level: hipaa_lite bloquea extraction si URL contains PHI subdomain pattern."""
```

---

## § 4 — Open questions para `/pm-luana`

| # | Question | Impact |
|---|---|---|
| Q1 | ¿El backup pipeline está disponible en alguna rama mergeable o requiere re-extraction manual desde `Documentos/ap_sales_agent`? | High — define effort |
| Q2 | ¿LLM dispatch via `core/luana-core-llm` (router pattern shipped) o LLM call directo? | Medium — afecta tests + observabilidad |
| Q3 | ¿EP-N nuevo o reusar EP-1 (FieldOverride) con tool registration extendida? | Medium — define Extension SDK contract |
| Q4 | ¿Storage CDR de extraction (URL crawleada + LLM response) en `core/luana-core-observability` traces o brand-local? | Low — HIPAA-lite implication para vitalia |
| Q5 | ¿Versionado prompt template — `brand_extract_visuals.v1.j2`, `.v2.j2`? Re-prompts pueden cambiar output schema | Medium — backwards compat |
| Q6 | ¿Bloquear `vitalia-fase2-lisa-marca` build hasta lift accepted, o lisa-marca usa stub local que se reemplaza por engine import post-lift? | High — define ordering deps |

**Recomendación inicial Q6:** lisa-marca ships con stub local `pending_visual_extraction()` que retorna `BrandVisuals.empty()`. Sub-sección Identidad muestra botón disabled con tooltip "Próximamente — extracción automática desde URL". Post-lift accepted, ticket de 1 día reemplaza stub por engine import + habilita botón. Esto desbloquea lisa-marca sin esperar lift.

---

## § 5 — Costo + tiempo estimado

| Phase | Effort | Owner |
|---|---|---|
| `/pm-luana` evaluate proposal | 0.5 día | `/pm-luana` |
| Carve-out + cleanup (extract pipeline, generalize for brand opt-in) | 2-3 días | builder-backend (Opus) — engine touch requires Opus |
| Migration brand-aware (FE wizard + API client) | 1-2 días | builder-frontend (Sonnet) |
| Tests engine + 1 consumer brand (nicolify smoke) | 1 día | builder-backend |
| Documentation engine + capability YAMLs per brand | 0.5 día | `/pm-{brand}` cada brand consumer |
| **Total** | **5-7 días dev** | — |

Comparación re-implementación per-brand sin lift:
- 4-5 días por cada brand activa × 4 brands = 16-20 días totales + mantenimiento dividido + drift garantizado

**ROI:** lift gana incluso solo con 2 brands consumer. Hoy hay 1 demand active + 3 latent → break-even claro.

---

## § 6 — Decision gate

`/pm-luana` evalúa:
- ¿Acepta lift? → state: `accepted` + asigna milestone + arranca carve-out
- ¿Rechaza? → state: `rejected` + documenta rationale + vitalia re-implementa local con anti-duplication comment "lifted attempt rejected 2026-MM-DD see proposal #ID"
- ¿Defer? → state: `deferred` + condition para re-evaluar (ej. "cuando comunify llegue a brand-studio story")

---

## § 7 — References

- **Backup evidence (full paths):** `/home/chalreme/Documentos/ap_sales_agent/.planning/quick/260319-g7y-fix-brand-studio-visual-identity-extract/260319-g7y-PLAN.md`
- **Spec downstream consumer:** `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/01-spec.md` (en redacción — referencia futura tras producirse)
- **Engine target:** `core/luana-core-brand-studio/`
- **Extension SDK:** `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py`
- **Anti-duplication rule:** `.claude/rules/anti-duplication.md`
- **Promotion protocol:** `docs/promotion-protocol/README.md`
- **Cross-brand opt-in pattern:** `vitalia/config/brand.yaml::brand_studio.enabled_sections` (ya shipped)
- **Related ADR brand-local vitalia:** `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`

---

## § 8 — Subagent research traceability

Source de descubrimiento: subagent `a61407fad33264249` (Sonnet, 2026-05-26) durante reuse-map enrichment de lisa-marca. Pattern 3 verbatim:

> "🔥 Visual identity extract pipeline — `BrandExtractionService.extract_visuals_only(url)` + crawl + LLM (`brand_extract_visuals.j2`) → `BrandVisuals` JSON, funcional production en backup"
> "Recomendación: promotion candidate"

Chris ratificó escalation 2026-05-26 D2=A.
