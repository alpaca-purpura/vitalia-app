---
proposal_id: 2026-05-21-luana-core-ui-extraction
state: accepted
opened_date: 2026-05-21
opened_by: /pm-luana
ratified_by: Chris             # APPROVED 2026-06-06 (umbrella; target reconciliado → core/@luana/ui-kit existente, NO package nuevo)
ratified_date: 2026-06-06

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md  # caso visible: vitalia design system roto
  # NOTA: este es PREVENTIVE lift — NO hay mirror cross-brand todavía (vitalia no construyó aún, nicolify legacy no está auditado para lift).
  # Lift se justifica por anti-duplication PROACTIVE: 9 brands futuras heredan.

origin_brands: [vitalia]   # urgente. nicolify retroactivo eventual.

# Target
target_package: core/@luana/ui-kit          # reconciliado 2026-06-06: NO crear luana-core-ui nuevo; EXTENDER el @luana/ui-kit existente (+ @luana/design-tokens/hooks/schemas)
target_module: src/components/ + cli/ + stories/
target_ep: null            # no introduce extension point (es TS UI, no Python plugin)

# Impact assessment
semver_bump: minor         # 0.0.0 → 0.1.0 inicial (package nuevo)
breaking_change: false     # nuevo, no rompe nada
brands_affected_consumers: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: []   # ninguno (package nuevo, ningún test downstream pre-existe)

# Lift plan
lift_estimated_effort: "3-5 días bootstrap + 1 sem atoms foundation"
lift_owner: /dev-team                       # worktree wip/core-ui-extraction
arch_test_downstream_required: true         # post primer brand consumer (vitalia)
migration_notes_required: false             # no breaking, brands opt-in

# Pattern decision
pattern_chosen: shadcn-copy-paste-with-cli   # ver ADR-008
related_adr: docs/architecture/luana-platform/ADR-008-luana-core-ui-shadcn-cli-pattern.md
related_outcome: docs/product/outcomes/luana-core-ui-foundation.md
---

## /pm-luana review (under_review · 2026-06-06)

**Recomendación: ACCEPT (umbrella)** — 10/10 brands consumer potencial; es la fundación que desbloquea el shell-organism (`2026-06-01-lift-shell-organism-to-core`).

⚠️ **El package YA existe parcialmente con OTRO nombre (verify 2026-06-06):** la proposal dice "`core/luana-core-ui` NUEVO, no existe" — pero hoy existe **`core/@luana/ui-kit`** (+ `@luana/design-tokens`, `@luana/hooks`, `@luana/schemas`, etc.). El target real es `@luana/ui-kit` y le falta la capa `organism/`. Reconciliar el target name antes de ejecutar (extender el existente, NO crear un segundo package paralelo).

**Para ratificar (Chris):** (1) ¿reconciliamos target → `core/@luana/ui-kit` (extender) en vez de `luana-core-ui` nuevo? (2) APPROVED del scope atoms+organism foundation. Co-ratificar con el shell-organism child.

---

## 1. Patrón a promover

Engine TS package `core/luana-core-ui/` (nuevo) que provee:

- **Atom primitives** wrappeando Shadcn-ui (Button, Input, Label, Badge, Avatar, Icon, Separator, Skeleton, Spinner, Toast, Dialog)
- **Molecule compositions** (FormField, Card variants, NavItem, EmptyState, ConfirmDialog, FilterBar)
- **Organism layer** (AppSidebar, AgentRail, ActivityStream, DashboardLayout, DetailLayout) — **★ PATTERN PENDING REVIEW con Chris** antes de cementar shell/navigation
- **Default tokens** (CSS variables) que brands override per-brand
- **CLI tool** `@luana/ui` con commands `add`, `update`, `diff`, `list` para distribución shadcn-style (copy-paste, no npm import)
- **Storybook centralizado** con docs cross-brand

**Filosofía:** shadcn-ui upstream "copy don't import" preserved. Brands ownan su copia local en `{brand}/frontend/src/components/ui/{name}/`. Drift visible con arch fitness test diff-against-source.

**Detalle arquitectónico:** ver `docs/architecture/luana-platform/ADR-008-luana-core-ui-shadcn-cli-pattern.md`.

**Origen story:**
- vitalia: caso urgente — frontend visualmente roto post `vitalia-slice-1-marketing` merge `fa921711`. Sidebar plano, sin Nav system, Tailwind v4 tokens no renderizan runtime. Inventario gap brutal vs nicolify reveals need for design system foundation. [[2026-05-21-auto-handoff-deferred-e2e-blocker]]

## 2. Por qué cross-brand

Preventive lift (anti-duplication.md § lift shared rule). No hay mirror cross-brand HOY pero el patrón es transversal obvio:

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya consumirá | Urgente. Caso origen. |
| nicolify | retroactivo eventual | Shell legacy construido brand-only desde 2024 → retrofit a `@luana/ui` cuando estable + Chris ratifica scope |
| comunify | candidato | WIP recovery activo 2026-05-15. Design system pendiente. Consume al refining próxima story shell. |
| lupulo | candidato bootstrap | Placeholder hoy. Consumirá desde día 1 cuando bootstrap. |
| saasora | candidato bootstrap | Pendiente bootstrap. Hereda desde inicio. |
| inmoflow | candidato bootstrap | idem |
| retailly | candidato bootstrap | idem |
| fixia | candidato bootstrap | idem |
| guestly | candidato bootstrap | idem |
| fitflow | candidato bootstrap | idem |

10/10 brands son consumer potencial. Justificación PROACTIVE clara.

## 3. Análisis técnico

### Signature comparison

NO aplica signature comparison clásica (no hay duplicación cross-brand pre-existente). Este es preventive lift — el patrón se crea EN engine PRIMERO, brand consumer adopta after.

### Estructura propuesta

```
core/luana-core-ui/
├── package.json                    # @luana/ui, version 0.1.0
├── tsconfig.json
├── tsup.config.ts                  # build CLI bundle
├── README.md                       # quickstart + filosofía + CLI usage
├── src/
│   ├── components/
│   │   ├── atom/{name}/
│   │   │   ├── {name}.tsx
│   │   │   ├── {name}.stories.tsx
│   │   │   ├── {name}.test.tsx
│   │   │   ├── tokens.css           # CSS variables consumed
│   │   │   ├── version.json         # per-component semver
│   │   │   └── README.md            # usage docs
│   │   ├── molecule/...
│   │   └── organism/...
│   ├── tokens/                     # defaults brands override
│   │   ├── colors.css
│   │   ├── spacing.css
│   │   └── typography.css
│   └── lib/
│       └── cn.ts
├── cli/
│   ├── add.ts
│   ├── update.ts
│   ├── diff.ts
│   ├── list.ts
│   └── _utils/registry.ts
├── tests/
│   ├── architecture/
│   └── cli/
└── stories/                        # Storybook root
    ├── .storybook/
    └── docs/{atoms,molecules,organisms,tokens,patterns}/
```

### Consumer mechanism

```yaml
# {brand}/config/brand.yaml
ui:
  luana_core_ui: true
  theme_overrides_path: src/lib/tokens/
```

```bash
cd {brand}/frontend
npx @luana/ui add button         # copia atom/button/ a src/components/ui/button/
npx @luana/ui update button      # diff + merge guided
npx @luana/ui diff button        # solo report (CI-friendly)
npx @luana/ui list               # ver qué componentes consumed
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Drift cross-brand sin update CLI corrido | Media | Arch fitness test `test-ui-component-source-diff.test.ts` reporta divergencia per-brand. Drift permitido pero VISIBLE. |
| Tailwind v4 runtime issue bloquea engine package | Alta | PRE-REQUISITE: vitalia-tailwind-v4-diag DEBE cerrar GREEN antes de bootstrap engine package. |
| Pattern shell organism prematuro (Chris pending review) | Alta | Organism layer NO se cementa hasta Chris presenta idea. Bootstrap empieza con atoms only. |
| Storybook setup overhead | Baja | Boilerplate estándar, ~1 día setup |
| CLI maintenance burden | Media | CLI testeable, scope limitado (add/update/diff/list — 4 commands). Tests CLI obligatorios. |
| Brand consumer breaking change post lift | Media | Per-component semver permite evolución independiente. Updates no auto-overwrite — diff + merge guided. |

## 4. Lift plan

### Pre-lift checklist

- [ ] Tailwind v4 diag GREEN (story `vitalia-tailwind-v4-diag` cerrada done)
- [ ] Pattern shell organism review con Chris cementado (ratificación nueva idea agéntica)
- [ ] ADR-008 ratificado state=accepted por Chris
- [ ] Workspace `pnpm-workspace.yaml` registra `core/luana-core-ui` member
- [ ] Storybook config decidido (Storybook 8+ + Vite + Tailwind v4 plugin)

### Lift execution (esta proposal cubre solo bootstrap + atoms)

1. `/dev-team` worktree wip/core-ui-extraction crea `core/luana-core-ui/` desde scaffold
2. Setup `package.json` + `tsconfig.json` + `tsup.config.ts` + Storybook
3. Implementar Button atom como vertical-slice prueba (component + stories + tests + tokens + README + version.json)
4. CLI scaffold: `add.ts` + `_utils/registry.ts` mínimo (Button único registered)
5. Test CLI end-to-end: `npx @luana/ui add button` desde vitalia/frontend dir target
6. Arch fitness test engine-side: source structure invariants
7. Bump semver `0.0.0 → 0.1.0`
8. CHANGELOG entry inicial
9. `docs/core-modules/luana-core-ui.md` contracts públicos
10. R3 arch test downstream: vitalia/frontend consume Button vía CLI, test pasa
11. Rollback path: revert lift, vitalia retiene patrón local (no hay loss, package nuevo)

### Post-lift

- Vitalia opt-in en `vitalia/config/brand.yaml::ui.luana_core_ui: true`
- Story `S-CORE-UI-ATOMS-FOUNDATION` arranca después de bootstrap GREEN — agrega 9 atoms restantes (Input, Label, Badge, Avatar, Icon, Separator, Skeleton, Spinner, Toast, Dialog)
- Story `S-VITALIA-THEME-TOKENS` arranca en paralelo (worktree wip/vitalia) — define paleta médica + tokens override
- Stories shell + agentic patterns DEFERRED hasta Chris cementa idea nueva

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED PROACTIVE LIFT

**Razón:**

1. **Anti-duplication preventive justificado:** 10/10 brands son consumer potencial. Costo de construcción brand-only en vitalia + retrofit cross-brand después es estrictamente mayor que construir engine package primero.
2. **Pattern ratificado (shadcn copy-paste con CLI):** filosofía shadcn upstream preserved, brand flexibility maintained, drift visible.
3. **Sin risk regression downstream:** package nuevo, ningún test brand pre-existe.
4. **Stories pre-existentes vitalia desbloqueadas:** `vitalia-slice-1-marketing-integration` (state=idea) y futuros slices Slice-1 dependen de design system foundation. Lift es habilitante.
5. **Scope limitado proposal:** cubre solo bootstrap + atoms foundation. Organism + agentic patterns DEFERRED pending Chris idea. Reduce risk over-commit upfront.

**Ratificación Chris:** _pending_

## 6. Bitácora

- 2026-05-21: opened state=proposed por /pm-luana (handoff modo Core Engineering)
- Pending: Chris ratifica → state=accepted o feedback iteración

## 7. Cross-references

- Outcome platform: `docs/product/outcomes/luana-core-ui-foundation.md`
- ADR pattern: `docs/architecture/luana-platform/ADR-008-luana-core-ui-shadcn-cli-pattern.md`
- Origin learning: `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md`
- Related learning Tailwind: `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md`
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- Frontend FSD rule: `.claude/rules/frontend-fsd.md`
- Process docs: `docs/promotion-protocol/README.md`
- Template usado: `docs/promotion-protocol/template-proposal.md`
