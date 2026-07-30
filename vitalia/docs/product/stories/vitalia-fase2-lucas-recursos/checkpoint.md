---
story_id: vitalia-fase2-lucas-recursos
type: ui-story
agent_owner: lucas
map_zone: agentes
map_box: lucas
module: assets
capability: lucas.recursos
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lisa-marca               # voice brand para AI generator
blocks_hard: []
blocks_soft:
  - vitalia-fase2-lucas-lanzar               # campañas consumen creatividades
  - vitalia-fase2-camila-voz                 # testimonios imágenes
reuse_map_summary: "REUSE marketing module shipped + assets module · NEW biblioteca creatividades + copy reusable + AI generator (Mateo integration · transversal asistente) + importados + solicitudes Mateo · NEW N3-dyn workspace [asset-id]"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes biblioteca + Mateo cards · /ux-agentico diseñar flujo Mateo agentic"

# Schema v2 migration (cement 2026-05-27)
release: F6   # release ID · ver releases/
cap_target: lucas.recursos   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S17 vitalia-fase2-lucas-recursos — checkpoint

## Goal

Sub-tab Recursos de Lucas: biblioteca centralizada de creatividades + copy reusable. Sub-secciones:
- **Biblioteca** — Grid creatividades (imágenes · videos · copy templates)
- **Generador IA** — Tooling Mateo (transversal asistente · cards de tareas pendientes Mateo + UI invocar Mateo para create assets)
- **Importados** — Assets uploaded manual
- **Solicitudes Mateo** — Cola tareas pendientes Mateo (e.g., "Generá 5 variaciones del post de viernes")

**Mateo integration** = asistente transversal (sin tab propio · vive en cards aquí) per navigation-tree.

## Anti-objetivos

- NO duplicar Mateo logic (vive en `vitalia/backend/src/modules/vitalia/assets/mateo/`)
- NO implementar video generation AI (out-of-scope MVP · imagen + copy only)
- NO duplicar assets shipped en `vitalia/backend/src/modules/vitalia/assets/`

## Scope verbatim

### § 1 — Page + 4 sub-secciones

`<LucasRecursosView>` Shadcn Tabs.

### § 2 — `BibliotecaGrid`

Grid cards assets:
- Thumbnail
- Tipo (image · video · copy · template)
- Tags (vertical · campaña type · channel suggested)
- Usage count (cuántas campañas consumieron)
- Acciones: Ver · Duplicar · Editar · Eliminar · "Solicitar variación Mateo"

### § 3 — `GeneradorIA` Mateo cards

Cards:
- "Generar imagen post sociales" (Mateo invocar)
- "Generar copy WhatsApp HSM"
- "Generar variaciones imagen existente"
- "Generar carousel IG"

Cada card → drawer wizard input prompts (consume voice brand from F2-S7) → Mateo background job → asset added to biblioteca.

### § 4 — `Importados`

Upload form drag-drop:
- Multi-file upload S3
- Tag automático ML (sentiment + content type detection)
- Manual tags override

### § 5 — `SolicitudesMateo`

Lista tareas en cola Mateo:
- Status: queued · processing · done · failed
- Acciones: Approve resultado · Reject · Re-generate
- Timeline events

### § 6 — N3-dyn `assets/[asset-id]`

Workspace detalle asset:
- Preview full
- Metadata (tags · created_at · creator · usage stats)
- Variants (regen Mateo · 5 sizes · channel-specific crops)
- Usage history (campañas que usaron)
- Download original

### § 7 — Mateo backend

`vitalia/backend/src/modules/vitalia/assets/mateo/`:
- Agent orchestrator (LangGraph subagent · consume engine sales-agent pattern OR custom · `/ux-agentico` define)
- Tools: `generate_image_prompt` · `generate_copy` · `generate_variation`
- Background worker procesa solicitudes

Per `.claude/rules/anti-duplication.md`: Mateo NUNCA mirror engine code · usa engine LLM router + observability + cost recording per `R23` Opus 4.7 obligatorio (agentic production code).

### § 8 — HIPAA-lite

Assets generados NUNCA incluyen PHI · validation pre-publish.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 4 sub-secciones |
| AC-2 | Biblioteca grid carga assets paginated |
| AC-3 | Click asset → N3-dyn workspace |
| AC-4 | Generador IA cards invocan Mateo con voice brand |
| AC-5 | Importados drag-drop upload S3 + auto-tags |
| AC-6 | Solicitudes Mateo queue visible + approve/reject |
| AC-7 | Variants generation funcional |
| AC-8 | Audit log per asset create + per Mateo invocation |
| AC-9 | Visual goldens × 10 |
| AC-10 | a11y axe pass |
| AC-11 | Cross-tenant + sanitize |
| AC-12 | Vitest + Playwright + a11y pass + Mateo evals (`/ux-agentico` defines if applicable) |

## Gherkin scenarios

### Scenario 1 — happy: Mateo genera post Instagram

**Given:** Voice brand definido. Mateo available.

**When:** Click "Generar imagen post sociales" → drawer input "Post limpieza dental" → submit

**Then:**
- Mateo background job queued
- Solicitud aparece en cola con status `processing`
- Mateo invoca tools internamente (cost tracked per R23)
- Cuando done → asset added biblioteca + notify user
- Audit log full chain

### Scenario 2 — edge: Mateo fail

**Given:** Mateo job fails (LLM timeout)

**When:** Background processes

**Then:** Status `failed` con razón · re-generate available · Sentry alert

### Scenario 3 — adversarial: assets cross-tenant

GET asset_id de otro tenant → 404 · dual filter.

### Scenario 4 — keyboard-a11y

Tab grid cards · Enter view · Esc back · drag-drop alternative button upload.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/recursos/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lucas/recursos/assets/[asset-id]/page.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/recursos/LucasRecursosView.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/recursos/BibliotecaGrid.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/recursos/GeneradorIA.tsx` | NEW (Mateo cards) |
| `vitalia/frontend/src/features/lucas/components/recursos/Importados.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/recursos/SolicitudesMateo.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/components/recursos/asset-detail/AssetWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/lucas/api/recursos.ts` | NEW |
| `vitalia/frontend/src/features/lucas/types/asset.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/assets/api/recursos_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/assets/api/mateo_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/assets/mateo/orchestrator.py` | NEW (★ agentic production code · Opus 4.7 per R23) |
| `vitalia/backend/src/modules/vitalia/assets/mateo/tools/{generate_image_prompt,generate_copy,generate_variation}.py` | NEW |
| `vitalia/backend/src/modules/vitalia/assets/mateo/extensions.py` | NEW (register Mateo via EP) |
| `vitalia/backend/src/modules/vitalia/assets/persistence/migrations/XXXX_assets_mateo.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lucas-recursos-mateo.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/recursos/{view}-{light\|dark}.png` (×10) | NEW |
| `vitalia/backend/tests/modules/vitalia/assets/test_mateo_orchestrator.py` | NEW |
| `vitalia/backend/tests/agentic_evals/mateo/test_voice_fidelity.py` | NEW (eval goldens per sales-agent-expert pattern) |
| `vitalia/backend/tests/modules/vitalia/assets/test_recursos_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/assets/` | Asset model + S3 | REUSE + extend Mateo |
| Vitalia shipped — marketing module | Asset library primer versión | REFACTOR migrar al lucas/recursos |
| `core/luana-core-llm` engine | LLM router + cost recording | CONSUME (anti-duplication mandate) |
| `core/luana-core-observability` | Trace events + sanitize | CONSUME |
| `core/luana-core-sales-agent` patterns | LangGraph subagent patterns | INSPIRE Mateo architecture |
| F2-S7 lisa-marca voice brand | PersonalityProfile slot | CONSUME via brand-studio API |
| Shadcn primitives | `Card` · `Grid` · `Dialog` · `Tabs` · `Upload` | reuse |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lisa-marca` — voice brand source

### Esta historia desbloquea
- F2-S15 lucas-lanzar consume creatividades
- F2-S5 outbound consume copy templates

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Mateo voice fidelity drift | Media | Medio | Eval goldens + brand voice graders (per sales-agent-expert pattern) |
| LLM costs Mateo bloat | Media | Alto | Cost budget per tenant (BudgetGuard engine) + model routing (Haiku para simples · Opus solo creativo) |
| Generated assets PHI leak | Baja | Crítico | Sanitize + manual review pendiente aprobación pre-publish |
| Mateo orchestrator complejo | Alta | Medio | `/ux-agentico` design flow detallado pre builder |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 10 + Mateo eval goldens
3. Backend tests mateo + cross-tenant + cost recording + sanitize pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lucas.recursos` registrada

## Próximo paso post-done

- F2-S15 lanzar + F2-S5 outbound consumen biblioteca

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lucas.recursos (mateo_integration: true)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Anti-duplication rule:** `.claude/rules/anti-duplication.md`
- **R23 Opus 4.7 obligatorio** agentic production code
- **/ux-agentico skill:** flujo Mateo design
