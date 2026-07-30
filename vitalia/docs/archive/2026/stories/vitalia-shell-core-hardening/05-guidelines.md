# 05-guidelines — vitalia-shell-core-hardening

> Reglas enforceables que `builder-frontend` DEBE cargar y respetar. El auditor las usa en review. Surface única FE (chrome del shell).

## must_load_skills (verbatim — builder cita estos en su report "Skills consulted")

- `frontend-expert` — FSD-Lite, Server-First, React Query/Zustand, live-verify gate
- `vitalia-design-system` — SHELL-DESIGN-CONTRACT + tokens globals.css + agent-colors + 5 especialistas + Valeria supervisora (★ HARD para todo ticket FE vitalia)
- `playwright-expert` — Clerk auth, POMs, base.ts fixture, anti-burbuja, freshness gate
- `chrome-devtools-verify` — live-verify dev-app (gate #37: ejercer write/acción real + leer logs + confirmar efecto)
- `.claude/rules/frontend-fsd.md` — boundary matrix; import @luana/ui-kit permitido
- `.claude/rules/frontend-visual-fidelity.md` — D1 design-system-first + Design System Canon (binding HARD) + D3 scope discipline
- `.claude/rules/spanish-text.md` — neutro LatAm sin voseo (microcopy chrome)
- `.claude/rules/tdd-mandatory.md` — RED→GREEN→REFACTOR
- `.claude/rules/definition-of-done-live-verify.md` — gate #37 (verde ≠ done)
- `.claude/rules/tenant-isolation.md` — useTenantId() NUNCA Clerk org (FE)
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` — ADR-vitalia-004 (N3, FSD)
- `docs/architecture/luana-platform/design-system-canon.md` — contratos binding (N3, page-primitives, tokens)

## must_load_artifacts

- `vitalia/docs/product/stories/vitalia-shell-core-hardening/01-spec.md` (umbrella — manda en conflicto)
- `vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/01-spec.md` (backbone — SC-1..19, RN-1..13, AC-1..11 verbatim)
- `vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html` (mockup FINAL firmado — behavior-fi)
- `vitalia/docs/product/stories/vitalia-shell-core-hardening/03-arch.md` + `03-arch-fe.md` (este contrato)
- `vitalia/docs/architecture/{SHELL-DESIGN-CONTRACT.md, ADR-vitalia-004-shell-feature-architecture.md, ADR-vitalia-006-ssr-safe-persisted-store.md}`
- `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` (B1 root cause + edge-redirect)
- `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` (N3 ya en core)
- `vitalia/docs/observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md` (BUG#1+#2)
- `core/@luana/ui-kit/src/{EntityWorkspaceLayout,EntitySubNavBar}.tsx` (signatura canon a consumir)

## forbidden_to_touch (HARD)

- `vitalia/frontend/src/components/ui/` — Shadcn primitives (re-estilizar impacta toda la app). Escalate /pm-vitalia.
- `vitalia/frontend/src/lib/api/fetchClient.ts` — tenant injection.
- `vitalia/frontend/src/features/*/components/**` EXCEPTO `embudo/EmbudoMetrics.tsx` + `lisa/.../staff/workspace/**` (los del scope). El CONTENIDO de las sub-tabs de agente NO se re-estiliza — solo color hardcoded→token para dark.
- `nicolify/` — cross-brand (read-only). Convergencia vía /pm-luana post-merge.
- `core/luana-core-*/src/` — Python engine. No se toca.
- `core/@luana/ui-kit/src/**` — **CONSUMIR (default)**. Edit SOLO additivo-mínimo si falta una pieza N3 (proposal accepted 256517a3). Cualquier edit no-additivo (refactor chrome, breaking) → STOP /pm-luana. Si se toca: correr typecheck+test del kit + downstream vitalia.

## Hard constraints (chrome FE)

1. **Behavior-fi, NO pixel-fi:** el mockup comunica COMPORTAMIENTO; el estilo sale del design system vigente (canon + tokens). UI actual NO retrocede (AC-10/SC-19). Avatar Valeria = asset catálogo, NO placeholder "V".
2. **ssr:false se CONSERVA** — root cause react-resizable-panels v4. NO eliminarlo. Soft-nav se arregla en proxy.ts (edge-redirect), no removiendo ssr:false.
3. **Store SSR-safe vía factory** `createSsrSafePersistedStore` (@luana/hooks) — NO recrear. Migrate legacy sin crash (SC-18). NO clobber durante SSR/skeleton (setItem NO-OP pre-hydration).
4. **N3 = consumir `@luana/ui-kit`** — NUNCA cablear EntitySubNavBar a mano; retirar la copia brand-local (mata mirror). Adaptar call-sites a la signatura canon (root-pill + identity + leaves).
5. **Gate desktop↔mobile = CSS, nunca JS** — montar/desmontar `<Group>` condicional → "Rendered more hooks". El Group se monta siempre.
6. **Dark = token, no hardcoded** — preferir migrar hardcoded→token semántico (que ya tiene dark) sobre crear variante nueva. Reduce deuda.
7. **Spanish neutro LatAm** en microcopy chrome (sin voseo).
8. **Native-first** — `cd vitalia/frontend && npx ...`. ui-kit: `pnpm --filter @luana/ui-kit ...`. NUNCA `docker exec` ni `make e2e*` (OOM).
9. **TDD RED-first** por capa (vitest hook/component/store → playwright). Test omitido de race REACTIVADO (AC-14).
10. **Anti-burbuja** — todos los specs importan `base.ts`, NUNCA `@playwright/test` directo. SC-20/21/22 real-backend (no mockear el surface bajo prueba).
11. **No `any`, no default exports** (FSD-Lite). `cn()` de `lib/utils`. CSS vars, no hex hardcoded.

## Exit criteria por ticket FE (gate #37 — NO "tests verdes")

Cada ticket FE cierra con:
- Suite verde (tsc + eslint + vitest + arch + e2e + axe) — **necesario, no suficiente**.
- **live-verify dev-app + dod_evidence** (≥1 acción/write real + logs + efecto observado). Ej: toggle dark en inbox → computed bg oscuro confirmado; colapsar Valeria → write localStorage observado; N3 staff workspace montado live.
- `demo-script.md` para la demo Chris (G chris_verify.signoff).
- NUNCA declarar "funciona"/"done" por suite verde o GET 200 (verification-real-not-200).

## Definition of Done (story)

- AC-1..14 cubiertos (backbone + umbrella), verificados LIVE en AMBOS temas.
- Regresión cero shipped (SC-19) + embudo board/writes intactos.
- `EntitySubNavBar` brand-local RETIRADO; staff+embudo consumen `@luana/ui-kit` (AC-9).
- Band-aid hard-nav revertido a next/link (AC-13).
- Test de race REACTIVADO y verde (AC-14).
- Dark consistente shipped-only, hardcoded→token (AC-12).
- `SHELL-DESIGN-CONTRACT.md` actualizado (N3 consume core + dark + máquina estados).
- Handoff proposal a /pm-luana (chrome brand listo para lift `2026-06-01-lift-shell-organism`).
- `dod_live_verified: true` + `dod_evidence` + `chris_verify.signoff`.
