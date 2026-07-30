---
proposal_id: 2026-05-17-auto-regen-backlog-precommit
state: proposed
opened_date: 2026-05-17
opened_by: /pm-luana
ratified_by: null
ratified_date: null

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-17-tooling-auto-regen-backlog.md

origin_brands: [vitalia]                          # detectado en vitalia, aplica universal

# Target
target_package: scripts/git-hooks/pre-commit      # cross-brand tooling, NO core engine package
target_module: scripts/git-hooks/pre-commit       # archivo único shared cross-brand
target_ep: null                                   # no introduce EP — es enforcement de tooling existente

# Impact assessment
semver_bump: patch                                # no rompe nada — pre-commit es opt-in via install-hooks
breaking_change: false
brands_affected_consumers: [vitalia, nicolify, comunify, lupulo]  # 4 activas + 6 futuras heredan
brands_at_risk_regression: []                     # solo agrega; no toca scripts/generate_backlog.py (ya brand-aware)

# Lift plan
lift_estimated_effort: "2-4h"
lift_owner: /dev-team                             # cambio mecánico, no requiere /architect
arch_test_downstream_required: true               # tests vivirán en core/luana-core-platform/tests/scripts/test_pre_commit_hook.py
migration_notes_required: false                   # no breaking
---

## 1. Patrón a promover

**Auto-regen del BACKLOG per-brand en `pre-commit` cuando se modifican artefactos SSoT funcionales.**

El BACKLOG.md / BACKLOG.yaml / BACKLOG-TLDR.md per-brand son auto-generated por `scripts/generate_backlog.py --brand {slug}` desde `{brand}/docs/product/{outcomes,stories,capabilities,modules}/`. Pero la regeneración hoy depende de disciplina humana — el dev/PM recuerda correr el script después de editar SSoT. En la práctica el BACKLOG queda stale entre sesiones (vitalia drift 24h+ confirmado 2026-05-17, comunify drift detectado mismo día — 3 archivos en DRIFT al correr `--check`).

Propuesta: agregar Section al pre-commit hook que detecte cambios staged en `^[a-z]+/docs/product/(outcomes|stories|capabilities|modules)/.+\.(md|yaml)$`, extraiga brand slug del path (primer componente), ejecute `python3 scripts/generate_backlog.py --brand {slug}`, y si los 3 archivos BACKLOG.* cambian → stage + commit en mismo commit (no separado).

**Origen story/incident:**
- Vitalia: detectado en sesión [[vitalia-ux-discovery]] 2026-05-17 cuando Chris pidió estado real backlog y BACKLOG.md no reflejaba 24h de cambios (outcome creado + story v0 ratificada + 5 stories spawned). Resolved manual `python3 scripts/generate_backlog.py --brand vitalia`.
- Comunify: confirmado mismo día — auditoría harness `/pm-luana` 2026-05-17 mostró DRIFT en 3 archivos BACKLOG comunify pre-regen.

## 2. Por qué cross-brand

10 brands sufren mismo problema (BACKLOG stale entre sesiones es genérico al patrón "auto-gen depende de disciplina humana"). Aplica universal a:

- **Vitalia** — confirmado drift 2026-05-17 (24h+)
- **Nicolify** — pre-multibrand legacy, mismo patrón
- **Comunify** — confirmado drift 2026-05-17 (sesión auditoría)
- **Lupulo** — bootstrap pendiente, hereda al opt-in
- **Saasora/InmoFlow/Retailly/Fixia/Guestly/FitFlow** — bootstrap pendiente (6 brands), heredan al bootstrap via `_pm-brand-template/`

NO es candidate para core engine package (`luana-core-*`) — es tooling de proceso. Vive en `scripts/git-hooks/pre-commit` que ya es shared cross-brand (instalado vía `make install-hooks`).

## 3. Plan de lift

### Cambio único (no es lift de código, es enforcement nuevo)

Agregar Section N al `scripts/git-hooks/pre-commit` (después de Section 10 existente — auto-regen INFRA-MATRIX cuando `brand.yaml` staged). Modelo conceptual idéntico:

```bash
# Section 11 — Auto-regen BACKLOG per-brand cuando docs/product/** staged
STAGED_PRODUCT_DOCS=$(git diff --cached --name-only --diff-filter=ACMR | \
    grep -E '^[a-z]+/docs/product/(outcomes|stories|capabilities|modules)/.+\.(md|yaml)$' || true)

if [ -n "${STAGED_PRODUCT_DOCS}" ]; then
    BRANDS_TOUCHED=$(echo "${STAGED_PRODUCT_DOCS}" | cut -d/ -f1 | sort -u)
    for BRAND in ${BRANDS_TOUCHED}; do
        # Magic escape: skip si commit body o file tiene comment "backlog-regen-skip: ..."
        if git diff --cached "${STAGED_PRODUCT_DOCS}" | grep -qE 'backlog-regen-skip:'; then
            continue
        fi
        python3 scripts/generate_backlog.py --brand "${BRAND}"
        # auto-stage si cambios
        git add "${BRAND}/docs/product/BACKLOG.md" \
                "${BRAND}/docs/product/BACKLOG.yaml" \
                "${BRAND}/docs/product/BACKLOG-TLDR.md" 2>/dev/null || true
    done
fi
```

### Cross-platform extension

Si commit toca `docs/` raíz (cross-brand platform) → trigger también `make portfolio` (regen `docs/portfolio/PORTFOLIO.md` + 10 brand 1-pagers). Modelo análogo a Section 10 que regenera INFRA-MATRIX.md.

### Tests cubren

`core/luana-core-platform/tests/scripts/test_pre_commit_hook.py` (donde ya viven tests del hook):

- `test_section11_regen_backlog_when_product_doc_staged` — modifica `vitalia/docs/product/stories/X/checkpoint.md` → hook regenera 3 archivos vitalia + stage
- `test_section11_skip_magic_comment` — agrega `# backlog-regen-skip: ...` → hook no regenera
- `test_section11_multi_brand_commit_regenera_ambos` — commit toca files de 2 brands → ambos regenerados
- `test_section11_root_docs_dispara_portfolio` — commit toca `docs/portfolio/*.md` → `make portfolio` corre

### Verification gate post-lift

- Manual smoke: editar `vitalia/docs/product/stories/X/checkpoint.md`, `git add`, `git commit` → ver BACKLOG.md regenerado en mismo commit
- Pre-existing tests pre-commit hook pasan sin regression
- 4 tests nuevos green

## 4. Decisiones Chris pending

- [ ] APPROVED (mover state proposed → accepted) → handoff `/dev-team` para implementar
- [ ] REJECTED (con razón documentada) → mantener disciplina manual + considerar alternativa CI-only
- [ ] Modificación scope (e.g., también auto-regen `docs/portfolio/PORTFOLIO.md` cuando toca platform docs)

## Referencias

- Origen learning: `vitalia/docs/learnings/2026-05-17-tooling-auto-regen-backlog.md`
- Tooling existente: `scripts/generate_backlog.py` (ya `--brand` aware post 2026-05-15)
- Tests vivos hook: `core/luana-core-platform/tests/scripts/test_pre_commit_hook.py`
- Bug related fixed inline 2026-05-17: `scripts/generate_backlog.py` línea 606 hardcoded "Nicolify" header → `brand_label.capitalize()`
- Pattern análogo ya implementado: Section 10 INFRA-MATRIX auto-regen (mismo modelo trigger + auto-stage)
