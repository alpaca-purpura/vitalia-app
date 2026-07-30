# Brand Docs Schema — R1+R2+R3+R4 consolidated

> **W0.5 conformance (2026-06-08):** `outcomes/` purgado (D-X2 — la entidad *outcome* murió en la consolidación SDD 4-ejes: Release→Story→Capability→Scenario). `02-design-ui.md` DEAD (UI usa § Wireframes del 01-spec compuestos del design-system-canon); `02-design-agentic.md` sigue vivo (solo agentic-story). **tier: project** (layout de docs por marca).

**Origen:** Sesión 2026-05-19 — purga docs/ Fase C reveló 3 reglas implícitas no codificadas. Auditor del caos doc detectó que el schema canónico (post pm-redesign 2026-05-15) no estaba enforced contra drift orgánico.

**Cement-date:** 2026-05-19.

**Scope:** aplica a `{brand}/docs/` para `{brand}` ∈ {vitalia, nicolify, comunify, lupulo + 6 brands pendientes bootstrap}. NO aplica a `docs/` raíz (ese tiene su propio schema cross-brand en CLAUDE.md § SDD Level 3).

## Schema canónico TARGET — qué SÍ puede existir en `{brand}/docs/`

```
{brand}/docs/
├── product/
│   ├── releases/{F0..FN}.yaml                # Release entity (4-ejes · reemplaza outcome)
│   ├── stories/{story-id}/                   # stories ACTIVAS (state ∉ {done})
│   │   ├── 01-spec.md
│   │   ├── 02-design-agentic.md             # opcional · SOLO agentic-story (02-design-ui DEAD → § Wireframes del 01-spec)
│   │   ├── 03-arch.md (+ 03-arch-{be,fe,agentic}.md opcionales)
│   │   ├── 04-validators.yaml
│   │   ├── 05-guidelines.md
│   │   ├── 06-tickets.yaml
│   │   ├── 06-audit/                         # opcional, post-auditor
│   │   │   ├── CHECKPOINTS.md
│   │   │   ├── gherkin-matrix.md
│   │   │   └── T-{n}-review.md (×N)
│   │   ├── 07-merge.md                       # al cerrar state=done
│   │   ├── 00-research.md                    # opcional state=idea
│   │   ├── checkpoint.md                     # state vivo
│   │   ├── T-{n}-impl-log.md (×N)
│   │   └── T-{n}-result.md (×N)
│   ├── capabilities/{module}/{cap}.yaml      # R32 inventory
│   ├── modules/{module}.md                   # auto-list R32
│   ├── BACKLOG.md                            # AUTO-GEN — DO NOT EDIT
│   ├── BACKLOG-TLDR.md                       # AUTO-GEN — DO NOT EDIT
│   ├── BACKLOG.yaml                          # AUTO-GEN — DO NOT EDIT
│   ├── checkpoint.md                         # state global brand
│   └── README.md                             # índice (opcional)
├── archive/{year}/stories/{story-id}/        # stories state=done (immutable snapshot)
├── learnings/{date}-{slug}.md                # insights brand-local
├── architecture/ADR-{brand}-{NNN}-{slug}.md  # ADRs locales brand
└── domains/{ep}/{component}.md               # tools/workflows registrados via Extension SDK
```

**Anything outside this schema** → violation. Tres reglas hard:

## R1 — No MDs sueltos en `{brand}/docs/` raíz

**Regla:** `{brand}/docs/` raíz puede contener SOLO sub-directorios (`product/`, `archive/`, `learnings/`, `architecture/`, `domains/`). NO archivos `.md` sueltos. Excepciones permitidas (whitelist exhaustivo):

- Ninguna por default. README.md raíz NO necesaria (cada subdir puede tener su propio README opcional).

**Why:** la purga 2026-05-19 reveló que `docs/` raíz tenía `ARCHITECTURE.md`, `CONTRIBUTING.md`, `RELEASES.md`, `extension-points.md`, `migration-from-nicolify.md` sueltos — todos útiles pero misplaced, generando confusión y duplicación de ubicación. La misma deriva ocurre en `{brand}/docs/` si no se enforce.

**How to apply:** cuando una brand necesita documentar algo arquitectónico o de proceso, debe ir al sub-dir apropiado:

| Tipo de contenido | Ubicación canónica |
|---|---|
| Decisión arquitectónica | `{brand}/docs/architecture/ADR-{brand}-{NNN}-{slug}.md` |
| Procedimiento operacional brand-local | `{brand}/docs/domains/{component}.md` |
| Spec/diseño de feature | dentro de `{brand}/docs/product/stories/{story-id}/` |
| Release (épica · 4-ejes) | `{brand}/docs/product/releases/{FN}.yaml` |
| Learning histórico | `{brand}/docs/learnings/{date}-{slug}.md` |
| Roadmap/backlog | `{brand}/docs/product/BACKLOG.md` (auto-gen) |
| Handoff cross-session | dentro de la story relevante (`HANDOFF-next-session.md` adjunto a `checkpoint.md`) |

**Anti-pattern:** `{brand}/docs/ROADMAP.md`, `{brand}/docs/IDEAS.md`, `{brand}/docs/TODO.md` o cualquier file ad-hoc fuera del schema.

## R2 — Stories `done` auto-move a `{brand}/docs/archive/{year}/stories/`

**Regla:** cuando una story transitions `state: reviewing → done` (Fase F merge per `story-closure-gate.md`), el directorio completo `{brand}/docs/product/stories/{story-id}/` MUST moverse a `{brand}/docs/archive/{year}/stories/{story-id}/` en el MISMO commit del merge. NO viven en active stories indefinidamente.

**Why:** la purga 2026-05-19 detectó 4 platform stories + 2 vitalia stories en state=done viviendo en `product/stories/` desde semanas, contaminando vistas de "stories activas". Además detectó 1 duplicate exacto (`vitalia-slice-1-onboarding-wizard` en active + archive) — sin enforce de auto-move, los duplicates se acumulan.

**How to apply:** `/pm-{brand}` ejecuta como parte del 07-merge:

```bash
YEAR=$(date +%Y)
git mv {brand}/docs/product/stories/{story-id} {brand}/docs/archive/${YEAR}/stories/{story-id}
```

El move debe ir en el commit del squash-merge a main (mismo commit que escribe `07-merge.md`).

Esto está mencionado en cada `pm-{brand}/SKILL.md` § "Capability promotion (al merge)" paso 5, y profundamente codificado en `.claude/rules/story-closure-gate.md` § Fase F MERGE.

**Anti-pattern:** mergear story a main con state=done sin mover a archive. Resultado: story aparece en BACKLOG auto-gen como "active" eternamente. `make portfolio` overhead crece linealmente sin auto-cleanup.

**Detección:** scanner heuristic — story con `state: done` en `{brand}/docs/product/stories/` (fuera de archive) → flag para `/pm-{brand}` cleanup en próxima sesión.

## R3 — Auto-gen files son GITIGNORED + NO se editan manual

**Regla v2 (cement 2026-05-20):** los siguientes archivos son **OUTPUT auto-gen** de scripts Y están **GITIGNORED** desde 2026-05-20. NO se commitean nunca; cada quien los regenera localmente. Editarlos manualmente provoca pérdida silenciosa al próximo regen.

| Path | Generator | Frecuencia regen | Tracked? |
|---|---|---|---|
| `{brand}/docs/product/BACKLOG.md` | `scripts/generate_backlog.py --brand {brand}` | post story state-change | ❌ gitignored |
| `{brand}/docs/product/BACKLOG-TLDR.md` | idem | idem | ❌ gitignored |
| `{brand}/docs/product/BACKLOG.yaml` | idem | idem | ❌ gitignored |
| `docs/product/BACKLOG.{md,yaml,-TLDR.md}` (legacy) | `scripts/generate_backlog.py` (sin --brand) | idem | ❌ gitignored |
| `{brand}/docs/product/modules/{module}.md` (sección auto-list) | `scripts/reconcile_capabilities.py --brand {brand}` | post capability change | ✅ tracked (hybrid: intro hand-written + auto-list block) |
| `docs/portfolio/PORTFOLIO.md` | `scripts/generate_portfolio.py` | `make portfolio` | ❌ gitignored |
| `docs/portfolio/{brand}.md` (×11 brands + luana.md) | idem | idem | ❌ gitignored |
| `docs/portfolio/INFRA-MATRIX.md` | `scripts/generate_infra_matrix.py` | `make infra-matrix` | ❌ gitignored |
| `docs/promotion-protocol/scan-{date}.yaml` | `scripts/scan_promotables.py` | `make scan-promotables` | ❌ gitignored |
| `docs/etl/extraction-contract.md` (cuando exista) | `make extraction-contract` | post analytics provider change | TBD |
| `**/__generated__/*` (frontend, ej. offer-field-paths.ts) | `nicolify/backend/scripts/generate_offer_field_paths.py` | post field-paths change | ❌ gitignored |

**Why gitignored (2026-05-20 cement):** durante semanas múltiples sesiones paralelas regeneraban con timestamps + ordenamientos distintos → merge conflicts crónicos (top 14 días: BACKLOG/PORTFOLIO con 9-11 modifs cada uno). Chris ratificó "gitignore total": SSoT vive en sources (`stories/`, `capabilities/`, `releases/`, `brand.yaml`); estos files son **vistas derivadas regenerables**, no fuente. Trade-off aceptado: GitHub UI no muestra la vista master sin clonar+regen, pero el costo de mantenerlos sincronizados era mayor.

**How to apply:**

1. **Headers explícitos:** todo file auto-gen incluye en sus primeras 5 líneas el marker (sigue siendo cierto aunque ya no se commitee):
   ```markdown
   <!-- AUTO-GENERATED por scripts/{generator}.py — NO editar a mano -->
   ```
   o equivalente en frontmatter YAML.

2. **Workflow correcto cuando contenido necesita cambio:** modificar la SOURCE (no el output). Sources:
   - BACKLOG → source es `{brand}/docs/product/{stories,capabilities,releases}/`
   - PORTFOLIO → source es `{brand}/docs/portfolio/...` + brand 1-pagers + `{brand}/config/brand.yaml`
   - INFRA-MATRIX → source es `{brand}/config/brand.yaml::infra`
   - scan-promotables → source es `{brand}/docs/learnings/*.md` con `promotable: candidate|yes`

   Luego: regen via `make {target}` o `scripts/generate_*.py` (idempotente).

3. **Ver la vista actualizada cuando la necesites:**

   ```bash
   make portfolio           # docs/portfolio/{PORTFOLIO,brand,luana}.md
   make infra-matrix        # docs/portfolio/INFRA-MATRIX.md
   .venv/bin/python scripts/generate_backlog.py --brand vitalia   # per-brand
   make scan-promotables    # docs/promotion-protocol/scan-{date}.yaml

   cat docs/portfolio/PORTFOLIO.md
   cat vitalia/docs/product/BACKLOG.md
   ```

4. **Si urge agregar nota:** crear archivo nuevo en el sub-dir correcto (ej. `{brand}/docs/learnings/{date}-{slug}.md`), NO inline en auto-gen output.

**Pre-commit hook behavior (Section 6 + 10):** sigue regenerando archivos auto-gen localmente cuando cambian sources (para mantener vista local fresh), pero ya NO ejecuta `git add` sobre ellos (son gitignored). Mensajes hook clarifican "regenerated localmente (gitignored, no incluido en commit)".

**Anti-pattern:** editar `BACKLOG.md` para "agregar TODO list" o cambiar prioridades manualmente — esos cambios viven en `checkpoint.md` o en stories/capabilities, no en el output consolidado. Ahora además los cambios manuales se pierden silenciosamente porque ni siquiera se commitean.

## R4 — chris-input.md nace con la idea (state=idea) — v3 cement 2026-05-28

Toda story creada (desde `state: idea`) MUST tener `chris-input.md` en su directorio, **junto con `checkpoint.md`**. Nace con la idea — NO se espera a `refining`. Es el buzón donde Chris vuelca lo que desea; Claude lo puede rebatir (verdict ❌ REFUTADO) durante el ciclo de vida.

**How to apply:**
- `/pm-{brand}` al CREAR la story (`state: idea`) crea `checkpoint.md` + `chris-input.md` juntos (desde template `docs/specs/templates/00-chris-input-template.md`). El cockpit (`extend-cap`, `from-done`) ya lo hace vía `createNewStoryDocs`.
- `/pm-{brand}` Fase F MERGE (`reviewing → done`) ejecuta `git mv` de chris-input.md junto con el resto de la story al `archive/{year}/stories/{id}/`
- Pre-commit hook (Section 16) bloquea commit de checkpoint.md con `state ∈ {idea, refining...reviewing}` si chris-input.md ausente (magic comment `# chris-input-skip: razón` permite override puntual).

**Anti-pattern:** Chris invoca `/po-ux <story>` sin que exista chris-input.md → skill debe rechazar. Story creada en `idea` sin chris-input.md.

Doc canónico: `docs/process/chris-input-protocol.md`.

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 — `/pm-{brand}` skill | "Surfaces propias" lista enforce schema. "NO toca" anti-creep. Bootstrap Step 0 scan stories done sin archivar. | ✅ active |
| 2 — Pre-commit hook (opcional) | Section nueva: bloquea stage de `*.md` directo en `{brand}/docs/` raíz (R1) | ⏳ TBD (decisión Chris) |
| 3 — Auditor backend/agentic/frontend | Cat 12 (anti-duplication) extendida: detect stories done viviendo en `product/stories/` (R2) | ✅ already covers |
| 4 — `scripts/reconcile_capabilities.py --check-mode` | Exit 1 si detecta R1 o R2 violations | ✅ exists, ⏳ extend opcional |
| 5 — Headers explícitos en auto-gen | `<!-- AUTO-GENERATED -->` marker (R3 prevention) | ✅ active per file |

## Anti-patterns

- ❌ Crear `{brand}/docs/ROADMAP.md`, `{brand}/docs/STATUS.md`, `{brand}/docs/NOTES.md` (R1)
- ❌ Mergear story state=done sin `git mv` a archive en mismo commit (R2)
- ❌ Editar `{brand}/docs/product/BACKLOG.md` para "agregar prioridad" (R3 — modificá la source: checkpoint o story)
- ❌ Editar `docs/portfolio/PORTFOLIO.md` directo (R3 — `make portfolio` desde sources)
- ❌ Mantener story state=done en active stories "porque la podemos consultar" — el move a archive NO la pierde, sigue accesible via path archive

## Multibrand awareness

- Esta rule aplica a las 4 brands activas (vitalia, nicolify, comunify, lupulo) y a todas las brands futuras bootstrap (saasora, inmoflow, retailly, fixia, guestly, fitflow).
- El template `.claude/skills/_pm-brand-template/SKILL.md` debe enforce esta rule desde el día 1 de bootstrap.

## Referencias

- `.claude/rules/story-closure-gate.md` — Fase F MERGE concreta R2 (archive como parte del merge)
- `.claude/rules/anti-duplication.md` — anti-creep cross-brand mirror (relacionado pero distinto scope)
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 (10 estados macro)
- `docs/process/story-closure-gate.md` — rationale ciclo `developed → reviewing → done`
- `CLAUDE.md` § SDD Level 3 — schema canónico cross-brand (relacionado, para `docs/` raíz no `{brand}/docs/`)
- Sesión 2026-05-19 purga docs/ Fase C — caso origen + ratificación Chris
