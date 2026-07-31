# Promotion Protocol — brand → Luana core

> Cómo un patrón nacido en una brand se promueve al engine compartido sin romper a las otras.

## Filosofía

> *"Lo que aprendemos en una brand debe poder dar superpoderes a las demás — sin obligar a ninguna."*

Cada brand opera autónoma con su propio backlog, sus propios learnings, sus propias decisiones. Cuando un patrón emerge en brand X y demuestra valor cross-brand potencial, se lifta a `luana-core-*`. Las otras brands lo adoptan **opt-in explícito** vía `{brand}/config/brand.yaml`.

**Reglas cardinales:**

1. **Brand-first, core-second.** Patrón nace en brand. Si después demuestra fit cross-brand, se promueve. NUNCA al revés (no hay "research en core" sin caso de uso brand concreto).
2. **Opt-in por brand.** Promoción NO activa la feature en otras brands. Cada brand elige cuándo adoptar.
3. **Manual ratify por Chris.** Auto-detect ayuda a encontrar candidatos. La decisión final es siempre manual.
4. **Downstream regression mandatory.** Cualquier lift corre tests de TODOS los brands consumidores antes del merge (R3 `.claude/rules/auditor-downstream-regression.md`).
5. **Semver disciplinado.** Patch (bug), minor (feature opcional), major (breaking). Bumps ratificados por `/pm-luana`.

## Estados proposal

```
proposed → under_review → accepted → migrated
                       ↓
                    rejected
```

| State | Significado | Trigger entry | Owner |
|---|---|---|---|
| `proposed` | Patrón flageado por brand (`promotable: candidate\|yes` en learning) o auto-detect | Brand learning + `/pm-luana` abre proposal | `/pm-luana` |
| `under_review` | `/pm-luana` analiza fit core (transversalidad, semver impact, risk) | `/pm-luana` decide review | `/pm-luana` + Chris |
| `accepted` | Chris ratifica APPROVED. Lift a `core/luana-core-X` programado | Chris APPROVED | `/dev-team` ejecuta lift |
| `rejected` | Chris ratifica reject. Brand retiene patrón | Chris REJECTED con razón | `/pm-luana` archive |
| `migrated` | Lift completo + arch test downstream + bump semver | `/dev-team` cierra lift | `/pm-luana` cierra proposal |

## Workflow detallado (8 pasos)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Brand B detecta patrón                                    │
│    → escribe {brand-B}/docs/learnings/{date}-{slug}.md       │
│       con frontmatter: promotable: candidate | yes           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. /pm-luana scan (manual o auto-trigger)                    │
│    → make scan-promotables (signature similarity AST)        │
│    → si match ≥85% en ≥2 brands → flag candidate             │
│    → o lectura manual de learnings con promotable=candidate  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. /pm-luana abre proposal                                   │
│    → docs/promotion-protocol/proposals/{date}-{slug}.md      │
│       (schema en template-proposal.md)                       │
│    → state: proposed                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. /pm-luana analiza (state → under_review)                  │
│    → ¿genuinamente transversal? (≥2 brands viable)           │
│    → ¿semver impact? (minor si nuevo opcional, major si      │
│       breaks contract existente)                             │
│    → ¿brand-specific data leakage? (refs hardcoded brand)    │
│    → ¿riesgo regresión downstream?                           │
│    → recomienda APPROVED / REJECTED a Chris                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Chris ratifica                                            │
│    APPROVED → state: accepted, /pm-luana abre /dev-team     │
│    REJECTED → state: rejected, archive con razón documentada │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. /dev-team ejecuta lift (caso APPROVED)                    │
│    → mueve código {brand-B}/backend/src/.../X →              │
│       core/luana-core-X/src/luana_core_X/                    │
│    → generaliza interface (parametrizar brand-specific bits) │
│    → R3 arch test downstream (corre tests TODOS brands       │
│       consumidores per .claude/rules/                         │
│       auditor-downstream-regression.md)                      │
│    → bump core/luana-core-X/pyproject.toml::version (minor)  │
│    → actualizar core/luana-core-X/CHANGELOG.md               │
│    → actualizar docs/core-modules/{package}.md               │
│       (sección promotion history)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. /pm-luana cierra proposal                                 │
│    → state: migrated                                         │
│    → migrated_date, migrated_pr, lift_summary                │
│    → entry en docs/process/learnings.md (cross-brand learn)  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Brands consumidoras opt-in (default explícito)            │
│    → Brand B (origen): activación automática                 │
│    → Otras brands: cada {brand}/config/brand.yaml puede      │
│       activar la feature cuando lo decidan                   │
│    → DEFAULT: opt-in. NO auto-on (evita romper brands        │
│       existentes con feature no pedida)                      │
└─────────────────────────────────────────────────────────────┘
```

## Auto-detect heurística (signature similarity)

Script `scripts/scan_promotables.py` (deliverable F5) busca:

| Surface | Heurística | Threshold |
|---|---|---|
| Tools sales_agent (`{brand}/backend/.../sales_agent/tools/`) | Pydantic args schema + return type | ≥85% match en ≥2 brands |
| Workflows copilot (`{brand}/backend/.../copilot/workflows/`) | LangGraph state machine + nodes count + transitions count | ≥85% structural match |
| Extractors copilot (`{brand}/backend/.../copilot/extractors/`) | Input schema + output Pydantic + LLM call shape | ≥85% match |
| KB packs (`{brand}/backend/.../copilot/kb/`) | Chunk count + meta tags overlap | ≥70% (más laxo, KB es declarativo) |
| Brand-studio sections (`{brand}/config/brand.yaml::enabled_sections`) | Misma sección activada en ≥2 brands | binary (yes/no) |
| Channel adapters (`{brand}/backend/.../connections/adapters/`) | Adapter ABC method overrides | ≥85% structural |

Output: `docs/promotion-protocol/scan-{date}.yaml` con candidates + reasoning.

> **Filosofía:** auto-detect es _aid_, no _decision_. Encuentra candidates. La decisión "¿esto va al core?" la toma `/pm-luana` + Chris analizando contexto, no algoritmo.

## Anti-patterns

- ❌ Lift sin proposal formal (saltarse el gate)
- ❌ Auto-on default cuando se promueve (rompe brands existentes opinion)
- ❌ Bump major sin ADR + migration notes en `docs/architecture/ADR/`
- ❌ Aceptar promoción con solo 1 brand consumidor (no es "cross-brand")
- ❌ Promover patrón con refs hardcoded brand-specific (data leakage)
- ❌ Saltar R3 downstream regression
- ❌ Editar `{brand}/docs/` desde `/pm-luana` (cross-jurisdiction)

## Referencias

- `template-proposal.md` — schema YAML frontmatter de proposal
- `proposals/` — proposals abiertas + archivadas
- `.claude/skills/pm-luana/SKILL.md` — owner skill
- `.claude/rules/anti-duplication.md` — patrones shared cross-consumer
- `.claude/rules/anti-default-flip-audit.md` — flag flips cross-consumer
- `.claude/rules/auditor-downstream-regression.md` — R3 mandatorio
- `docs/architecture/luana-platform/01-core-audit.md` — plan multibrand original
- `core/luana-core-extension-sdk/` — EP-1..EP-18 registry (donde se cementan extension points)
