# Anti-Duplication — Refining Phase — detail (moved from .claude/rules/ 2026-05-30, load on-demand)

Cuerpo operativo completo. La rule slim (`.claude/rules/anti-duplication-refining.md`) tiene la regla cardinal + scan compacto + decision matrix. Este doc lo lee on-demand `/pm-{brand}`, `/po-ux`, `/po`, `/ux-agentico`, `/architect` al refinar.

**Origen:** conversación 2026-05-27 — Chris pidió que refining herede la disciplina anti-duplication que sólo enforcean builders + auditors. **Complementa:** `.claude/rules/anti-duplication.md` (EJECUCIÓN — esta cubre REFINAMIENTO).

## Regla cardinal

ANTES de refinar/diseñar/arquitecturar una story nueva, `/pm-{brand}`, `/po-ux`, `/po`, `/ux-agentico` y `/architect` MUST ejecutar **mandatory cross-brand + core grep** para detectar:

1. **Pattern ya shipped** en otra brand activa → reusable directo o referencia
2. **Engine abstraction** en `core/luana-core-*/` → consumir vía import, NO recrear
3. **Brand activa con feature parecido** → considerar lift a engine como promotion candidate
4. **Learning previo capturado** → aplicar lecciones antes de repetir

## Step `prior-art-scan` (verbatim ejecutable)

Insertar al **inicio** de cada skill (después de Step 0 worktree, ANTES de redactar 01-spec / 02-design / 03-arch).

```bash
WS=$(git rev-parse --show-toplevel)
KEYWORDS="${KEYWORDS}"               # ej: "agenda scheduling slots prepago"

echo "=== Engine packages relacionados ==="
ls ${WS}/core/ | grep -iE "$(echo $KEYWORDS | tr ' ' '|')" 2>/dev/null

echo "=== Brands shipped con módulo similar ==="
for B in nicolify vitalia comunify lupulo; do
  find ${WS}/${B}/backend/src/modules/${B}/ -maxdepth 1 -type d 2>/dev/null | grep -iE "$(echo $KEYWORDS | tr ' ' '|')"
  find ${WS}/${B}/frontend/src/features/ -maxdepth 1 -type d 2>/dev/null | grep -iE "$(echo $KEYWORDS | tr ' ' '|')"
done

echo "=== Capabilities ya implementadas ==="
for B in nicolify vitalia comunify lupulo; do
  grep -rln -iE "$(echo $KEYWORDS | tr ' ' '|')" ${WS}/${B}/docs/product/capabilities/ 2>/dev/null
done

echo "=== Stories archivadas relacionadas (done) ==="
for B in nicolify vitalia comunify lupulo; do
  find ${WS}/${B}/docs/archive/*/stories/ -maxdepth 1 -type d 2>/dev/null | grep -iE "$(echo $KEYWORDS | tr ' ' '|')"
done

echo "=== Learnings cross-brand + per-brand ==="
grep -rln -iE "$(echo $KEYWORDS | tr ' ' '|')" ${WS}/docs/learnings/ 2>/dev/null
for B in nicolify vitalia comunify lupulo; do
  grep -rln -iE "$(echo $KEYWORDS | tr ' ' '|')" ${WS}/${B}/docs/learnings/ 2>/dev/null
done

echo "=== Anti-duplication.md inventario ==="
grep -iE "$(echo $KEYWORDS | tr ' ' '|')" ${WS}/.claude/rules/anti-duplication.md 2>/dev/null
```

### Output obligatorio en spec/design/arch

- **`/pm-{brand}`** (idea→refining): sección `## Prior art scan` en `00-story.md`/`checkpoint.md` con paths + decisión (reuse / extend-from-engine / lift-candidate / net-new).
- **`/po-ux`, `/po`, `/ux-agentico`**: sección `## Prior art applied` en `01-spec.md`/`02-design-agentic.md` con qué se reusó/extendió/aplicó.
- **`/architect`**: sección `## Prior art audit` en `03-arch.md` confirmando cero mirror, engine consumed via import, lift proposals (si aplica).

## Decision matrix (al encontrar prior art)

| Encontrado | Acción | Skill responsable |
|---|---|---|
| Engine package cubre 100% | CONSUMIR via import. Documentar en arch. | `/architect` |
| Engine cubre 60-99% | EXTEND vía herencia/composición. NUNCA mirror. | `/architect` |
| Brand `nicolify/` tiene módulo parecido + esta brand lo necesita igual | **Lift candidate** → escalate `/pm-luana` | `/pm-{brand}` |
| Brand `nicolify/` parecido pero diferenciador clínico/vertical | Extension SDK EP-N en `{brand}/.../X/extensions.py` consumiendo engine | `/architect` |
| Brand otra (no nicolify) parecido | Transversal probable → escalate `/pm-luana`; vertical específica → independiente OK | `/pm-{brand}` |
| Story archivada mismo problema (done) | Leer 07-merge.md + replicar pattern aplicando learnings | `/po-ux` o `/po` |
| Learning con tag relevante | Aplicar verbatim (citar learning path) | TODOS |
| Net-new | Proceder from scratch. Documentar scan vacío. | `/po-ux` o `/po` |

### Decision matrix `cap_target` + `cap_change_type` (v2 cement 2026-05-27)

Durante refinement, validar coherencia entre prior-art y `cap_change_type` declarado en checkpoint.md.

| Situación prior-art | `cap_change_type` válido | Acción |
|---|---|---|
| Cap target NO existe | `new` | Crear story · spec declara cap fresh |
| Cap existe + arregla bug SIN agregar funcionalidad | `fix` | Spec NO declara scenarios nuevos |
| Cap existe + agrega ≥1 scenario nuevo | `extend` | Spec lista scenarios · arch cita cap base |
| Cap existe pero scope distinto (mobile-only/segmento/variante) | `derive` | Cap hijo `parent_cap: {origen}` · `parent_story` en checkpoint |
| Cap NO existe pero engine la cubre | NO crear cap · `architect` propone CONSUMIR | Story = "wire engine into brand" |
| Cap NO existe pero snapshot legacy `nicolify/` la tiene | `derive` o lift candidate | Vertical → `derive`; transversal → escalate `/pm-luana` |

**Anti-patterns cap_change_type:**
- ❌ `new` cuando ya existe el cap (debe ser `fix`/`extend`)
- ❌ `extend` pero arch crea cap nuevo (debe ser `new`/`derive`)
- ❌ `derive` sin citar `parent_story` ni cap padre
- ❌ `fix` pero agrega scenarios nuevos (debe ser `extend`)

Doc canónico: `docs/process/capability-protocol.md` § Sección 3.

## Cross-brand learning extraction — fuentes prior-art REALES (corregido 2026-05-27)

> **★ Corrección 2026-05-27:** la asunción "nicolify ~80% prod" era pre-reorg. Post-reorg, `nicolify/docs/product/` está **vacío** (24 stories shipped → snapshot frozen read-only en `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/`). Live work está en **vitalia** + **comunify**. Audit: `docs/process/audits/2026-05-27-stories-sweep.md` § Hallazgo CRÍTICO #0.

| Source | Path | Estado | Cuándo consultar |
|---|---|---|---|
| **vitalia live** | `vitalia/docs/product/{capabilities,modules,outcomes,stories}/` + archive + learnings | 27 done + Fase 1/2 + 71 caps + 21 learnings | SIEMPRE (brand activa LIVE) |
| **comunify live** | `comunify/docs/product/{capabilities,modules}/` + archive + learnings | 2 done + 18 caps + 4 learnings | SIEMPRE (creator economy + offer ladder) |
| **engine core** | `core/luana-core-*/src/luana_core_*/` (26 pkgs) | SSoT compartido | SIEMPRE — consumir, NO recrear |
| **nicolify snapshot** | `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` | 24 stories + 12 modules + 15 caps — FROZEN read-only | Referencia arqueológica (NO live) |
| **lupulo** | `lupulo/docs/product/` | vacío placeholder | NO consultar |
| **6 brands futuras** | `{saasora,inmoflow,...}/` | bootstrap pendiente | NO consultar |

### Caveat — nicolify snapshot uso permitido

NO prohibido para consulta (sigue siendo prior-art shipped real). Pero: NUNCA "lift from snapshot" como first option · NUNCA asumir pattern válido sin verificar vs vitalia/comunify live · SÍ usar como archaeology cuando vitalia/comunify no cubren el dominio (ej. CRM ciclo largo agencia B2B).

## Anti-patterns prohibidos

- ❌ Refinar story sin grep cross-brand (sólo grep brand propia → riesgo recrear)
- ❌ /architect produciendo 03-arch.md sin sección `## Prior art audit`
- ❌ /po-ux produciendo 01-spec.md sin mencionar referencia (si otra brand tiene módulo paralelo)
- ❌ /pm-{brand} cerrando state=refined sin scan documentado
- ❌ Recrear abstracciones del inventario `anti-duplication.md` sin lift gate
- ❌ Documentar "prior art scan: clean" sin haber ejecutado el grep verbatim
- ❌ Aplicar learning + no citar el path en spec/arch
- ❌ Lift candidate detectado + no escalar a `/pm-luana`

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | `/pm-{brand}` Step 1.5 (prior-art-scan) post Step 0 | ⏳ |
| 2-4 | `/po-ux`, `/po`, `/ux-agentico` Step 0.5 antes de drafting | ⏳ |
| 5 | `/architect` Step 0.5 + Step 8 `prior_art_audit_done: true` | ⏳ |
| 6 | Auditor Cat 12 extiende a refining (verifica sección "Prior art") | ⏳ |
| 7 | Pre-commit valida "## Prior art" en 01-spec/03-arch (advisory) | ⏳ |

## Referencias

- `.claude/rules/anti-duplication.md` — execution-phase rule
- `.claude/rules/learning-capture.md` · `docs/promotion-protocol/README.md` · `docs/portfolio/PORTFOLIO.md`
