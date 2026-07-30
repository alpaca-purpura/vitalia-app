<!-- voseo-allowed: contrato técnico interno, no user-facing -->
# 03-arch-fe — Surface FE shell realign (builder-frontend)

> Subconjunto FE del contrato consolidado `03-arch.md` §3. Owner: **builder-frontend** (Sonnet). Auditor: **auditor-frontend** (Opus).
> Toca SOLO `vitalia/frontend/src/**` + `vitalia/frontend/e2e/**`. `architecture_pattern: ADR-vitalia-004` (realinea taxonomía, no crea sub-tab nueva).

## F6 — Shell realineado (opción B ratificada)

### Orden de ejecución (catalog PRIMERO, propagar)
1. **`src/lib/agent-catalog.ts`** (SSoT — cambiar primero):
   - `AGENT_RIBBON_ORDER = [lisa, mateo, adrian, lucas, camila]` (Valeria fuera · Mateo entra).
   - `AGENT_CATALOG.mateo.tabLabel = "Operar"`, `defaultSubtab = "agenda"` (deja "Tecnología"/"ia").
   - `AGENT_CATALOG.valeria` permanece (sidebar supervisor + `DEFAULT_CHAT_AGENT`), pero **fuera del ribbon**.
   - `RIBBON_SUBTABS.mateo = [{agenda},{pacientes}]`; `RIBBON_SUBTABS.valeria = []`.
   - `isValidAgent`: incluir `mateo`, excluir `valeria` del ribbon (mantener válido como chat agent).
   - `SHIPPED_STATIC_SUBTABS`: `valeria.agenda` → `mateo.agenda`.
2. **Routing** (`app/[tenantId]/(shell-organism)/`): `git mv valeria/agenda → mateo/agenda` (dir + page.tsx); eliminar `valeria/` dir. Dispatcher `[agent]/[subtab]` lee del catalog → automático.
3. **Features**: `git mv features/valeria → features/mateo` (agenda real ~30 componentes); actualizar imports + `// cap:` headers (`valeria.agenda`→`mateo.agenda`).
4. **Ribbon.tsx**: lee `AGENT_RIBBON_ORDER` → automático. `ConfigTab` label "Configurar"→"Plataforma".
5. **`config` slug**: recomendado mantener slug `config` en routing, solo cambiar `tabLabel` (ver Open Q1). Features/config placeholders sin tocar.

### Design-system-first
- `--agent-mateo` (#FEE209) ya en `globals.css` → reusar (cero token nuevo).
- Reusar átomos Ribbon/SubTabsBar existentes; cero primitiva nueva.

### Mockup gate (ADR-003) — WAIVED
`mockup_gate_waived: true` (Chris). Sin mockups. Verificación visual = e2e Ribbon scoped (T-6).

## Riesgos de regresión (CRÍTICO — migrar junto)
1. Catalog mueve agenda a mateo pero routing/features siguen en valeria → **404 silencioso**. Migrar catalog + routing + features en el MISMO ticket (T-5).
2. e2e que buscan `[aria-label="Operar"]` en tab Valeria o tab Valeria presente → actualizar (T-6).
3. Tests arch FE de `agent-catalog` (allowlist mateo excluido) → invertir: mateo incluido, valeria excluido del ribbon.

## Patrones forbidden
- ❌ Componentes UI nuevos sin reusar átomos/tokens (Ribbon es realineación).
- ❌ `toHaveScreenshot()` de página completa fuera del scope Ribbon.
- ❌ Tocar `core/@luana/*`, otras brands, `tools/luana-cockpit/`.
- ❌ Microcopy con voseo ("Operar", "Plataforma" — neutro).
- ❌ Dejar `features/valeria` huérfano post-migración (git mv completo).

## playwright_visual_scope
- story_scope_routes: `/[tenantId]/mateo/agenda` · Ribbon (cualquier ruta shell).
- story_scope_components: `Ribbon.tsx`, `RibbonTab`, `ConfigTab`, `SubTabsBar`.
- forbidden_visual_changes: `components/ui/` (Shadcn primitives), `app/layout.tsx`, `ValeriaSidebar` (no cambia función).
- non_egoismo: bug visible en otro feature no tocado → documentar en T-{n}-impl-log § Cross-story observed bugs, NO fix inline.

## Tests (RED primero)
- Vitest arch: `agent-catalog` — `AGENT_RIBBON_ORDER` incluye mateo/excluye valeria; `RIBBON_SUBTABS.mateo` agenda+pacientes; `SHIPPED_STATIC_SUBTABS` mateo.agenda.
- E2E Playwright (`e2e/`): Ribbon 5 tabs (Lisa·Mateo·Adrián·Lucas·Camila) + Plataforma; "Operar"=Mateo; sin tab Valeria; `mateo/agenda` carga.

## Gates verdes
```bash
cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
```
