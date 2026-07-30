<!-- voseo-allowed: internal architecture guidelines, infra-only story -->

# F1-S0 vitalia-fase1-stack-stability — 05-guidelines

## Patterns required (MUST follow)

1. **Shadcn copy-paste vendored** — `npx shadcn@latest add` descarga `.tsx` source local en `src/components/ui/`. NO npm package consumption. Los 8 primitivos quedan committed + editable post-install.
2. **CSS vars Shadcn-standard HSL formato** — `--agent-lisa: 156 100% 41%;` (sin función `hsl()`, sin coma). Tailwind config consume via `'hsl(var(--agent-lisa))'`.
3. **Tailwind theme.extend.colors.agent.*** — verbatim Design Contract § 5.2. NO sobreescribir `theme.colors` raíz (use `extend`).
4. **.vt-* preservation strategy** — bloque legacy intacto en `globals.css`, apunta a nuevas CSS vars Shadcn-style (compatibility temporal). ADR-vitalia-002 § 3 documenta.
5. **Idempotent install** — todos los pasos (`npx shadcn init`, `add primitives`, edit globals.css, edit tailwind.config.ts) MUST ser re-ejecutables sin romper estado. Si Shadcn CLI detecta files presentes, prompt "overwrite?" → answer "n" preserve existing.
6. **Arch fitness shrink-only** — `test-no-vt-classes-in-new-features.test.ts` empieza GREEN by emptiness. Cuando F1-S4+ poblean SHELL_PATHS, test sigue GREEN porque builder NO usa `.vt-*`. NO se expande allowlist.
7. **ADR-vitalia-002 § 7 post-install audit checklist obligatorio** — `/auditor` review del PR examina diff line-by-line los 8 primitivos `.tsx` contra registry Shadcn oficial `https://ui.shadcn.com/r/`. Cualquier divergencia injustificada → REJECT.
8. **NATIVE Linux host execution** — `npx tsc`, `npx eslint`, `npx vitest`, `npx playwright`, `npm run build` corren NATIVE (host), NUNCA `docker exec`. Excepción: `make dev-vitalia` levanta containers Postgres + backend + frontend (NO se ejecutan tests/lint dentro de esos).
9. **Lockfile committed** — `vitalia/frontend/package-lock.json` (o `pnpm-lock.yaml`) con SHA pin de cada nueva dep Shadcn (Radix + class-variance-authority + clsx + tailwind-merge + lucide-react). Commit junto con `components.json`.
10. **Playwright @project=visual maxDiffPixelRatio 0.001** — verbatim Design Contract § 9.4 (0.1% tolerance + animations disabled + caret hide). NO relajar threshold sin Chris ratificación explícita.
11. **Storybook N/A** — F1-S0 NO construye componentes user-facing (las 2 test pages son fixtures Playwright). Storybook stories empiezan en F1-S2+ cuando primer organism real existe.
12. **Mobile responsive N/A** — idem (no UI nueva user-facing). Breakpoints + responsive verificación per-organismo F1-S1..S10.

## Patterns forbidden (MUST NOT)

1. ❌ **Editar `vitalia/frontend/src/app/[tenantId]/(dashboard)/` legacy** — `(dashboard)/` debe seguir funcionando idéntico post-install. Goldens 1+2 (regression light+dark) catchan visualmente.
2. ❌ **Instalar Shadcn en `nicolify/frontend/`, `comunify/frontend/`, `lupulo/frontend/`** — scope brand-local Vitalia exclusivo. Otras brands fuera de scope.
3. ❌ **Migrar `.vt-*` a Tailwind directo en esta story** — eso es `vitalia-fase2-vt-deprecation-final` al cierre Fase 2. F1-S0 documenta plan, NO ejecuta.
4. ❌ **Cross-brand imports** — `vitalia/frontend/` NUNCA importa `nicolify/frontend/`, `comunify/frontend/`, `lupulo/frontend/`. Compartir via `@luana/*` engine packages (no aplica F1-S0).
5. ❌ **Cross-feature imports nuevo código** — FSD-Lite enforce. Si arch test detecta violation → REJECT.
6. ❌ **Hex hardcoded en componentes** — usar `bg-agent-lisa text-agent-lucas-soft`, no `bg-[#00D084] text-[#111111]`.
7. ❌ **Default exports en código nuevo** — FSD-Lite enforce named exports only (`export function PrimitivesShowcase()`, no `export default`).
8. ❌ **`any` TypeScript en código nuevo** — `utils.ts`, test pages, arch test, ADR referencias. Use `unknown` + type guards si necesario.
9. ❌ **`// eslint-disable-next-line` sin justification comment** — cada disable requiere explanation inline (`// eslint-disable-next-line ... — reason: ...`).
10. ❌ **Importar `core/luana-core-*/` directo desde frontend** — engine packages BE consume via Python imports `luana_core_*`. FE consumiría via `@luana/*` TS packages (no aplica F1-S0).
11. ❌ **Hardcoded paths `/home/chalreme/` o absolutos** — use `process.cwd()` + relative paths o `git rev-parse --show-toplevel` env var.
12. ❌ **Frameworks no-Tailwind** — NO Bootstrap, NO Material UI, NO Chakra. Tailwind + Shadcn vendored only.
13. ❌ **Bootstrap/Material UI/Chakra** — same as #12 explicit listing.
14. ❌ **Fixtures con Lorem ipsum o data USA** — test pages renderizan datos realistic LatAm (clínicas AR/MX/CO/PE/CL, nombres pacientes Latam). NO `Lorem ipsum dolor sit amet`. NO `John Smith` placeholders.

## Files in scope (T-1..T-7 scope strict)

NEW files:

1. `vitalia/frontend/components.json` (T-1)
2. `vitalia/frontend/src/components/ui/button.tsx` (T-1)
3. `vitalia/frontend/src/components/ui/avatar.tsx` (T-1)
4. `vitalia/frontend/src/components/ui/dropdown-menu.tsx` (T-1)
5. `vitalia/frontend/src/components/ui/input.tsx` (T-1)
6. `vitalia/frontend/src/components/ui/badge.tsx` (T-1)
7. `vitalia/frontend/src/components/ui/textarea.tsx` (T-1)
8. `vitalia/frontend/src/components/ui/tabs.tsx` (T-1)
9. `vitalia/frontend/src/components/ui/tooltip.tsx` (T-1)
10. `vitalia/frontend/e2e/__test-pages__/stack-stability/primitives-showcase.tsx` (T-3)
11. `vitalia/frontend/e2e/__test-pages__/stack-stability/agent-tokens-swatch.tsx` (T-3)
12. `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts` (T-4)
13. `vitalia/frontend/e2e/__screenshots__/stack-stability/*.png` (T-4 — 6 goldens generados)
14. `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` (T-5)
15. `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` (T-6)

MODIFIED files:

- `vitalia/frontend/src/app/globals.css` (T-2 — agregar :root + .dark blocks; preserve .vt-* legacy)
- `vitalia/frontend/tailwind.config.ts` (T-2 — extend theme.extend.colors)
- `vitalia/frontend/src/lib/utils.ts` (T-1 — NEW or MODIFY si ya existe, agregar `cn()` named export)
- `vitalia/frontend/playwright.config.ts` (T-3 — agregar @project=visual block)
- `vitalia/frontend/package.json` (T-1 — Shadcn CLI agrega deps automáticamente)
- `vitalia/frontend/package-lock.json` (T-1 — lockfile pin nuevas deps)

## Files NEVER touches (HARD ban)

1. ❌ `core/luana-core-*/` (engine packages — F1-S0 NO toca engine)
2. ❌ `nicolify/`, `comunify/`, `lupulo/` (otros brands — scope exclusivo Vitalia)
3. ❌ `vitalia/frontend/src/app/[tenantId]/(dashboard)/` legacy (debe coexistir intacto)
4. ❌ `vitalia/.claude/` (brand overlay rules — story no toca meta-paradigm)
5. ❌ `.claude/` raíz (rules globales — story no toca meta-paradigm)
6. ❌ `vitalia/backend/` (story 100% FE — NO endpoints, NO DTOs, NO migrations)
7. ❌ `vitalia/frontend/src/components/ui/*` si pre-existing (verify pre-install — Shadcn CLI prompt "overwrite?" → answer "n" si conflict)

## must_load_skills (★ v4.1 enforceable verbatim list)

Builder T-{n}-result.md DEBE incluir sección "Skills consulted (must_load enforcement v4.1)" con tabla skill/rule + status (loaded | n/a) + when consulted. Auditor flag CHANGES_REQUESTED si missing.

1. `frontend-expert` — FSD-Lite boundaries, arch fitness ratchet, FE quality gates
2. `playwright-expert` — `@project=visual` config, maxDiffPixelRatio, goldens generation, snapshot strategy
3. `tessl__shadcn-ui` — copy-paste vendored pattern (NO npm package consumption)
4. `tessl__tailwind` — theme.extend, CSS vars HSL formato, dark mode strategy
5. `tessl__vitest` — arch test patterns, walk file system, regex matching
6. `tessl__nextjs-app-router-modularization` — route group isolation, App Router conventions
7. `.claude/rules/frontend-fsd.md` — boundary matrix, named exports, no cross-feature
8. `.claude/rules/spanish-text.md` — no-copy-scope F1-S0 (ADR-002 lleva magic comment `voseo-allowed`)
9. `.claude/rules/anti-duplication.md` — verify NO mirror cross-brand del install pattern
10. `.claude/rules/tdd-mandatory.md` — RED tests precede GREEN (arch test creado pre-uso real)
11. `vitalia/.claude/rules/shell-mockup-per-component.md` (consume — F1-S0 declarada **exenta** per ADR-vitalia-003 § Excepciones, infra-only sin componentes user-facing nuevos)
12. `vitalia/.claude/rules/hipaa-lite.md` (consume — **no-phi-scope declared**: F1-S0 NO toca rutas autenticadas ni tablas PHI; compliance dual-filter aplica desde F1-S1 onwards)

## reference_artifacts (load on demand durante build)

1. `vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md` — Gherkin scenarios + acceptance criteria (665 LOC ratified)
2. `vitalia/docs/product/stories/vitalia-fase1-stack-stability/03-arch.md` (this story) — technical decisions + surfaces involved
3. `vitalia/docs/product/stories/vitalia-fase1-stack-stability/04-validators.yaml` § test_construction_plan — orden creación tests + scenario→test mapping verbatim
4. `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3.1 (átomos) + § 5 (tokens) + § 9.4 (Playwright visual config) — atomic design SSoT
5. `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` (T-6 deliverable — escrito durante story) — plan deprecación + post-install audit checklist supply-chain
