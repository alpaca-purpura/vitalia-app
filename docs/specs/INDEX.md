# Specs — Templates + Rubrics + Personas

**Qué es:** infraestructura ejecutable para SDD Level 3. Reusable cross-stories.

## Sub-dirs

### `templates/`

Templates Markdown + YAML que skills consumen:

| Archivo | Quién lo usa | Para qué |
|---|---|---|
| `story-{ui,agentic,service}.yaml` | `/po` | Schema de cada tipo de story |
| `ticket.yaml` | `/architect` | Schema de un ticket en `04-tickets.yaml` |
| `00-story-template.md` | `/pm` | PM redacta inicio de story |
| `01-spec-template.md` | `/po` | PO redacta gherkin AI-resistant |
| `02-design-ui-template.md` | `/ux-ui` | Diseño UI |
| `02-design-agentic-template.md` | `/ux-agentico` | Diseño flujo conversacional |
| `03-arch-template.md` | `/architect-{be,fe,agentic}` | Documento técnico arq |
| `04-tickets-template.yaml` | `/architect` | Pila tickets |
| `T-handoff-template.md` | `/architect` | Input al developer |
| `T-impl-log-template.md` | `/dev-team` | Bitácora developer |
| `T-result-template.md` | `/dev-team` | Output developer post-build |
| `T-review-template.md` | `/auditor` | Veredicto auditor |
| `REVIEW-final-template.md` | `/auditor` | Veredicto story completo |
| `checkpoint-template.md` | todos | Resume protocol cualquier nivel |
| `07-merge-template.md` | `/pm` | Diff aplicado a `../product/` |

### `rubrics/`

LLM-as-judge rubrics. Cada rubric tiene:
- `header` con `id`, `applies_to` (story_type), `version`
- Bloque `assertions[]` con criterios numerados pass/fail
- Score 0.0-1.0 con threshold pass

| Rubric | Aplica a | Mide |
|---|---|---|
| `voice-fidelity.md` | agentic-story | Voz tenant fiel (sales_agent SSoT) |
| `no-hallucination.md` | agentic-story | No inventa fields/datos inexistentes |
| `no-overpromise.md` | agentic-story | No promete resultados garantizados |
| `tool-trajectory.md` | agentic-story | Tools correctas en orden razonable |
| `empathy-tone.md` | agentic-story | Tono empático en contexto sensible |
| `completeness.md` | agentic-story + service-story | Cubre todos criterios pedidos |
| `code-quality.md` | tickets implementados | Code review estructurado |

### `personas/`

YAML con persona profile + simulated-user prompt. Consumidas por agentic-story scenarios `user_simulation:` y por las eval suites (`vitalia/backend/tests/agentic_evals/`).

| Sub-dir | Qué hay |
|---|---|
| `archetype-aware/` | **29 personas activas** — dialect-coded (es-AR/CL/MX), con `actor_goal`, `traits`, `objections`, `persona_kind` (happy/nurture/adversarial) + ejes `persona_gym_axes`. Ej: `patient-anxious-dental-ar`, `lead-prompt-injection-attempt`, `pregunton-comparador-pe`. Schema enforced por `vitalia/backend/tests/architecture/test_vitalia_personas_yaml_completeness.py`. |
| `_legacy/` | 5 originales (`lead-frio-impaciente`, `tenant-novato-tech`, …) — superseded por archetype-aware. |

Personas per-agent adicionales viven junto a sus suites: `vitalia/backend/tests/agentic_evals/sales_agent/personas/` (20) + `copilot/wizard_personas/` (4). El generador de conversaciones IA↔IA (`apps/client-simulator/`) está **dormant** — rescatado de Nicolify, integración pendiente.

## Versionado

Cada rubric/persona tiene `version` en frontmatter. Cambio mayor → bump version → stories que lo usan deciden migrar (no auto).
