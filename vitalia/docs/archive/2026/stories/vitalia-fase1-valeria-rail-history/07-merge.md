# F1-S5 merge artifact — vitalia-fase1-valeria-rail-history

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Brand:** vitalia
**Outcome:** vitalia-mvp-ui-foundation
**Auditor verdict:** APPROVED (5/5 CHECKPOINTS · 14/14 categorías · 2 WARNs non-blocking)
**Merge date:** 2026-05-24
**PM:** /pm-vitalia (autonomous chain)

---

## § 1 — Gherkin verification matrix (copia 06-audit/gherkin-matrix.md)

| Scenario | Test path | Status |
|---|---|---|
| SC-1 happy · keyboard cycle (r/f/c/Esc/r) + auto-coupling shellMode + persistence | `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/keyboard-cycle.spec.ts` | ✅ PASS (6/6) |
| SC-2 negative · typing 'COMPRAR' en composer NO transita estado | `typing-guard.spec.ts` | ✅ PASS (4/4) |
| SC-3 edge · IME composition (e.isComposing) skip shortcuts | `ime-composition.spec.ts` | ✅ PASS (1/1) |
| SC-4 adversarial · shell-store tampering setState INVALID | `store-tampering.spec.ts` | ✅ PASS (2-3) |
| SC-5 edge · click rail PanelLeftClose → collapsed+web | `click-collapse.spec.ts` | ✅ PASS (4/4) |
| SC-6 empty_state · búsqueda sin resultados → EmptyStateInline | `history-empty-search.spec.ts` | ✅ PASS (5/5) |
| SC-7 a11y · keyboard nav completo + axe wcag2aa | `a11y-keyboard.spec.ts` | ✅ PASS (6/6) + 0 axe |
| SC-8 a11y · mobile drawer aria-modal + focus trap | `a11y-mobile-drawer.spec.ts` | ✅ PASS (8/8) + 0 axe (post T-5.bis Portal + T-8.bis role=dialog) |
| SC-9 i18n · Spanish neutro LatAm rendered + cero PHI | `i18n-spanish-neutro.spec.ts` | ✅ PASS (5/5) |

**Cobertura:** 9/9 SC scenarios mapeados 1:1 a Playwright specs · 100% PASS · Auditor Phase D APPROVED.

---

## § 2 — Playwright E2E run (comando + verdict)

### Functional suite (project=smoke)

```bash
cd vitalia/frontend && \
  E2E_BASE_URL=http://localhost:3002 \
  npx playwright test regression/vitalia-fase1-valeria-rail-history/ \
  --project=smoke --reporter=line
```

**Verdict:** ✅ 45/45 PASS (17.4s)

### Visual goldens (project=visual, ratchet baseline iter 1)

```bash
cd vitalia/frontend && \
  E2E_BASE_URL=http://localhost:3002 \
  npx playwright test regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts \
  --project=visual --reporter=line
```

**Verdict:** ✅ 13/13 PASS (6.1s) — `maxDiffPixelRatio: 0.001` enforced, ratchet shrink-only post-Chris-ratify.

### A11y axe (embedded en a11y specs)

**Verdict:** ✅ 0 violations wcag2aa across {rail, full, collapsed, mobile drawer} × {light, dark}.

### Vitest unit + arch fitness (no regression)

```bash
cd vitalia/frontend && npx vitest run
```

**Verdict:** ✅ 1080/1080 PASS (126 test files, incluyendo NEW `test-shell-store-schema-readonly-f1-s5.test.ts` + 83/83 arch fitness invariants).

---

## § 3 — Capabilities updated/created

### NEW capability: `vitalia.shell-organism.valeria-sidebar`

**Path:** `vitalia/docs/product/capabilities/shell-organism/valeria-sidebar.yaml`

**Status:** `live` (introduced 2026-05-24 by story F1-S5)

**Summary:** ValeriaSidebar organismo del panel izquierdo del shell agéntico. Grid interno `[Rail 60 | Chat 1fr]` o `[History 280 | Chat 1fr]` mutuamente exclusivos. 3 estados macro (collapsed/rail/full) con auto-coupling collapsed↔shellMode='web'. Keyboard shortcuts hardened guard (skip IME + inputs + ancestor). React.createPortal mobile drawer (escape display:none parent). 4 botones MVP rail (PanelLeftOpen/Plus/Search/PanelLeftClose). History con filter case-insensitive + EmptyStateInline. ChatSlot placeholder con avatar Valeria + skeleton bubbles (F1-S6 lo extenderá).

### MODIFIED capability: `vitalia.shell-organism.layout-5050`

**Side-effect MIN_VALERIA_PX 620→580** (D3) — ahora reflectado en `ShellOrganismLayoutClient.tsx`. Slot replacement `ValeriaSidebarSlot` → `ValeriaSidebar` real. Cleanup 2 files DELETE.

Capability YAML `layout-5050.yaml` NO actualizado en este merge (la modificación es interna sin cambio de scope/surfaces externas). Si futuro audit detecta drift, regenerar.

---

## § 4 — Modules MD refreshed

**Path:** `vitalia/docs/product/modules/shell-organism.md`

Sección `## Capabilities <!-- AUTO-GENERATED -->` se regenera automáticamente via `scripts/reconcile_capabilities.py --brand vitalia` después de este merge. Resultado esperado:

```markdown
## Capabilities <!-- AUTO-GENERATED — no editar a mano -->

- [`shell.layout-5050`](../capabilities/shell-organism/layout-5050.yaml) — Layout root split 50/50 agentic + web mode alternativo + mobile triple-main pattern (status: live, 2026-05-23, story F1-S4)
- [`shell.valeria-sidebar`](../capabilities/shell-organism/valeria-sidebar.yaml) — ValeriaSidebar organismo con grid 2-col mutuamente exclusivos + 3 estados + keyboard hardened + mobile drawer Portal + a11y wcag2aa (status: live, 2026-05-24, story F1-S5)

<!-- END AUTO-GENERATED -->
```

### Decisión cardinal agregada a `## Decisiones cardinales`

- **Mobile drawer via React.createPortal:** ValeriaSidebar mobile drawer renderiza via `createPortal(drawer, document.body)` para escapar del hidden agentic main parent (`display:none` bloquea descendants `position:fixed` per CSS spec). React tree intacto, DOM target diferente — zero refactor de ShellOrganismLayoutClient.
- **role="dialog" en mobile drawer:** `aria-modal="true"` no es válido en `role="complementary"` per ARIA spec — mobile drawer usa `role="dialog"` (desktop aside sigue siendo `complementary`). T-8.bis a11y fix.
- **Auto-coupling collapsed↔shellMode='web':** `setValeriaState('collapsed')` triggerea automáticamente `setShellMode('web')`. UX coherente: minimizar Valeria = pasar a modo web. Press r/f restaura agentic.
- **Hardened keyboard guard:** `useKeyboardShortcuts` hook skip si `e.isComposing` (IME) OR target ∈ INPUT/TEXTAREA/[contenteditable]/[role=textbox] OR ancestor con esos atributos. Modifier shortcuts (Cmd+K) bypassan guard.
- **Side-effect MIN_VALERIA_PX 620→580:** F1-S5 ajustó MIN porque rail XOR history (2-col, no 3-col). Math: `280 history + 300 chat_min = 580`. F1-S4 había asumido 3-col errróneamente (60+280+280=620).

---

## § 5 — How to verify (comandos reproducibles)

### Reproducir F1-S5 funcionalmente

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

# 1. Levantar stack vitalia
make dev-vitalia
# Wait for health: curl -sf http://localhost:3002/test-stack/shell-layout

# 2. Vitest full suite
cd vitalia/frontend && npx vitest run

# 3. Playwright F1-S5 funcional
cd vitalia/frontend && \
  E2E_BASE_URL=http://localhost:3002 \
  npx playwright test regression/vitalia-fase1-valeria-rail-history/ --project=smoke

# 4. Playwright visual goldens
cd vitalia/frontend && \
  E2E_BASE_URL=http://localhost:3002 \
  npx playwright test regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts --project=visual

# 5. Arch fitness
cd vitalia/frontend && npx vitest run src/__tests__/architecture/

# 6. Manual smoke en navegador
# Abre http://localhost:3002/test-stack/shell-layout
# - Press 'f' → Valeria se expande con History panel (8 items mock)
# - Press 'r' → Valeria contrae a rail 60px
# - Press 'c' o 'Esc' → shellMode pasa a web (Valeria minimizada + AppPanel 100%)
# - Press 'n' → alert "Nueva conversación (próximamente)"
# - Type "xyzabc" en search history → EmptyStateInline visible
# - Toggle theme 🌗 → tokens dark mode aplican
# - Resize a <768px → hamburger TopBar visible → tap abre drawer mobile

# 7. Reproducir mockup HTML para side-by-side compare
cd vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups
python3 -m http.server 8888
# Abrir http://localhost:8888/valeria-rail.html y /valeria-history.html
# Compare visualmente vs componente real localhost:3002/test-stack/shell-layout
```

### Verificar capability inventory

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS} && .venv/bin/python scripts/reconcile_capabilities.py --brand vitalia
# Expected output: 17 capabilities (16 anteriores + 1 NEW valeria-sidebar)
```

### Verificar story archived

```bash
ls vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/ 2>/dev/null && echo "ERROR — story NOT archived" || echo "✅ Story archived"
ls vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/
# Expected: full snapshot moved
```

---

## Post-merge actions

| Action | Owner | Status |
|---|---|---|
| Capability YAML created | /pm-vitalia | ✅ DONE este merge |
| Module MD auto-list regen | scripts/reconcile_capabilities.py | ⏳ post-merge run (gitignored output) |
| BACKLOG regen | scripts/generate_backlog.py --brand vitalia | ⏳ post-merge run (gitignored output) |
| Story archived (R2 brand-docs-schema) | /pm-vitalia | ✅ DONE este merge (git mv) |
| Outcome story_ids update | /pm-vitalia | ✅ DONE este merge |
| Learning entry | /pm-vitalia | ⏳ optional — useKeyboardShortcuts LIFT CANDIDATE cross-brand (futuro promotable a core/luana-core-ui-hooks/) |
| Squash-merge wip/vitalia → main | Chris (ratify) | ⏸ PENDING ratificación |
| 2 WARNs cleanup (HistoryGroup doc + console.warn placement) | next sprint o follow-up story | ⏳ deferred |

---

## Promotion candidate (cross-brand)

**`useKeyboardShortcuts` hook** = candidate lift a `core/luana-core-ui-hooks/` (engine package futuro) o `core/@luana/hooks/` (TS-side workspace).

**Trigger:** cuando 2da brand (nicolify, comunify, lupulo, o futura) necesite shortcuts pattern similar → `/pm-luana` opens promotion proposal.

**Hoy:** brand-local en `vitalia/frontend/src/hooks/`. NO actuar — Chris pidió focus solo F1-S5.

Documentado en T-1-result.md sección LIFT CANDIDATE.

---

## State transition

```
state: reviewing → done   (post este 07-merge.md commit)
checkpoint.md::audit_artifacts preserved
checkpoint.md::merge_artifact: 07-merge.md
checkpoint.md::merge_date: 2026-05-24
```
