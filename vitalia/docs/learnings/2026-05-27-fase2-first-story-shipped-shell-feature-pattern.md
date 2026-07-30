---
brand: vitalia
date: 2026-05-27
slug: fase2-first-story-shipped-shell-feature-pattern
promotable: yes
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: core/luana-core-shell-organism (sugerencia)
related_adr: ADR-vitalia-004-shell-feature-architecture
related_story: vitalia-fase2-valeria-agenda
audit_iterations: 3
chain_total_duration_hours: ~4
---

# Learning — Fase 2 first story shipped + ADR-vitalia-004 shell-feature pattern emerges

**Origen:** F2-S1 vitalia-fase2-valeria-agenda merged 2026-05-27. Primera story Fase 2 vitalia que llega a `done` end-to-end del shell-organism agéntico.

## Qué aprendimos

### 1. Shell-feature pattern es source-of-truth cross-brand candidate

Implementar valeria/agenda como sub-tab dentro del shell-organism reveló un patrón replicable de **9 secciones cementadas** (ratified ADR-vitalia-004):

1. Routing (route group + Server Component default + SSR + PHI nunca en URL)
2. FSD-Lite (features/{agent}/components/{subtab}/ + api/ + hooks/ + store/ + types/)
3. Client root ({Agent}{Subtab}View.tsx con "use client" + composición de hijos via hooks + props hidratación)
4. Data layer (React Query para server data + Zustand para UI state, sin mezclar)
5. Forms (RHF + Zod + autosave debounce 600ms + discriminated unions cuando aplique)
6. BE DDD Inside-Out (domain → infrastructure → application → api + PhiRepositoryBase + dual filter tenant+clinic + audit log sync pre-response)
7. Migrations raw SQL idempotent (IF NOT EXISTS, no sa.Enum() en create_table)
8. Telemetría (tabla brand-local vitalia_growth_studio_event, NO copilot_trace_event engine)
9. Tests (Vitest unit + Playwright funcional + visual goldens 3×2 + axe + BE pytest dual-tenant + arch fitness EXTEND)

**Why:** sin el patrón cementado, cada story sub-tab reinventaría composición + boundaries + tests + arch fitness. Con el patrón, builder spawn ahorra horas de decisión + auditor tiene checklist 9 secciones para REJECT divergencias sin rationale.

**How to apply:** brands con shell agéntico similar (Comunify si construye uno, Nicolify si pivotea hacia agéntico, Lupulo KDS sub-tabs) pueden adoptar ADR-vitalia-004 verbatim. `/pm-luana` evalúa lift candidate a `core/luana-core-shell-organism` package.

### 2. v1.1 cement N3-static SubSubTabsBar (post lisa-marca v2.1 refactor)

Durante F2-S1, en paralelo Chris cementó v1.1 del ADR: **si una sub-tab agrupa 3+ vistas conceptualmente discretas → MUST usar N3-static via SubSubTabsBar** con routing `[subtab]/[subsubtab]/page.tsx` + entry en `AGENT_SUBSUBTABS` catalog. NUNCA Shadcn `Tabs` internas body (Nivel 4 anti-pattern).

F2-S1 valeria-agenda es N2 (vista única con view-modes via URL param día/semana/mes), no requirió N3.

**Why:** caso origen lisa-marca v2 → v2.1 refactor obligado por Chris — single scroll H2 múltiples pierde discoverability cuando hay 3+ vistas. N3-static reusa Ribbon/SubTabsBar pattern existente.

**How to apply:** próximas stories Fase 2 que agrupen 3+ sub-secciones (e.g., adrian-inbox con bandejas, lisa-marca con identity/visuals/voice) MUST declarar N3-static en spec frontmatter.

### 3. Autonomous chain 4-fases viable a 19 tickets / ~62h est

Cadena `/architect → /dev-team → /auditor → /pm-vitalia merge` completada autónomamente para F2-S1 (19 tickets, ~4h wall-clock real con paralelización agresiva).

Tiempos por fase:
- /architect orchestrator single-shot: ~26 min
- /dev-team 19 tickets (paralelizando T-5+T-6+T-8, T-13+T-14+T-16): ~3 hrs
- /auditor iter 1 + iter 1.5 + iter 3 final: ~30 min
- /pm-vitalia merge: ~15 min

**Why:** paradigm v4 Conv 2 + Conv 3 + AUTO-HANDOFF (post 2026-05-18 story-closure-gate) permite cadenas autónomas multi-hora sin Chris intervention mid-chain. Único gate humano: ratificación spec/visual pre-architect.

**How to apply:** stories ui-mixed con 15-20 tickets son viables en sesión autónoma. Tickets >25 → split story. Service-deps blockers se resuelven con Option A (stubs + MSW) en lugar de bloquear chain.

### 4. Audit iteration cap 3 = sweet spot

Iter 1 detectó 7 findings críticos (F1-F7) + 4 WARNs. Iter 2 confirmed F1-F7 RESOLVED + W4 nuevo. Iter 3 cerró W4. Iter cap 3 alcanzado limpio sin ESCALATE.

Anti-pattern observado: iter 1 builder declaró "F1 covers W4" (MobileBottomSheet wired) — incorrecto, auditor iter 2 detectó claim inaccurate. Lesson: builder MUST verify cada claim contra grep + run tests, no asumir.

**Why:** cap 3 da margen para 1 regression cycle (iter 1.5) sin tirar la story. Excede cap → spec o decomposition issue real.

**How to apply:** stories con findings >7 en iter 1 → considerar split (scope demasiado grande). Findings <3 en iter 1 → probable APPROVED iter 2 directo.

## Promotion path

`/pm-luana` evalúa lift cross-brand de ADR-vitalia-004 a `core/luana-core-shell-organism` package post-merge. Trigger: cuando 2da brand (Comunify? Nicolify?) construya shell agéntico — entonces 2 brands replicando = candidate confirmed.

Mientras tanto: `ADR-vitalia-004` queda brand-local con `architecture_pattern: ADR-vitalia-004` en frontmatter de stories vitalia Fase 2 (enforce via `vitalia/.claude/rules/shell-feature-architecture-mandatory.md`).

## Referencias

- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` — autoridad arquitectónica brand-local
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/07-merge.md` — merge artifact F2-S1
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` — overlay rule enforce 9 secciones
- `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` — paradigm cementado
- `.claude/rules/story-closure-gate.md` — AUTO-HANDOFF post 2026-05-18
