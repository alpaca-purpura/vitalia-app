# Vitalia — Shell-Feature Architecture Mandatory

**Overlay:** extiende `.claude/rules/` raíz Luana platform (refuerza `backend-ddd.md` + `frontend-fsd.md` + `tdd-mandatory.md`).
**Brand:** vitalia
**Scope:** stories Vitalia Fase 2 que construyen sub-tab dentro del shell-organism agéntico.
**Cement-date:** 2026-05-26.
**SSoT:** `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`.

## Regla cardinal

Toda story Vitalia que construye una **sub-tab nueva** dentro del shell-organism (`vitalia/frontend/src/app/[tenantId]/(shell-organism)/{agent}/{subtab}/page.tsx`) MUST seguir las **9 secciones del patrón** cementadas en ADR-vitalia-004. El `/architect` cita ese ADR verbatim en su `03-arch.md § 0` y solo se permite divergir documentando rationale explícito en `03-arch.md § Architecture Decisions`.

Sin esta cita en `01-spec.md` frontmatter (`architecture_pattern: ADR-vitalia-004`) → `/architect` REFUSE arrancar.

## Scope

### Aplica (gate bloqueante)

- Toda story Fase 2 sub-tab con UI (`lisa-*`, `mateo-*`, `adrian-*`, `lucas-*`, `camila-*`, `plataforma-*`, `onboarding-*`) — ★★ v1.2 (2026-05-30): `valeria-*` de valor migradas a `mateo-*`; `config-*` renombradas a `plataforma-*` (excepto `config-onboarding-clinica` → `onboarding-clinica`)
- Stories Fase 1 que construyan componente con data fetching/persistencia (las restantes ya están `done`)
- Stories `state ∈ {idea, refining, refined}` actualmente abiertas

### NO aplica (excepciones explícitas)

- Service-only stories sin UI (`vitalia-payment-adapter-mvp`, `vitalia-fiscal-emission-pe`)
- Stories agentic-conversacionales puras (Camila→Voz si fuera flow puro) — siguen `/ux-agentico`
- Bootstrap/infra stories históricas (F1-S0 stack-stability, F1-S1 design-tokens) — exentas
- La propia source story `vitalia-fase2-valeria-agenda` (es el origen del patrón, NO se cita a sí misma; el ADR la cita verbatim)

## Constraints — checklist 9 secciones (verbatim ADR-vitalia-004 § 3)

Toda story scope MUST cumplir:

1. **Routing**: route group `(shell-organism)/{agent}/{subtab}/page.tsx` con static segment; Server Component default; SSR initial state; PHI nunca en URL/searchParams. **★ v1.1 (2026-05-27):** si la sub-tab agrupa 3+ vistas conceptualmente discretas → MUST usar **N3-static via `SubSubTabsBar`** con routing `[subtab]/[subsubtab]/page.tsx` + entry en `AGENT_SUBSUBTABS` catalog. **NUNCA** Shadcn `Tabs` internas body para sub-secciones — eso es Nivel 4 anti-pattern. Ver ADR-vitalia-004 § 3.1.1.
2. **FSD-Lite**: `features/{agent}/components/{subtab}/`, `api/`, `hooks/`, `store/`, `types/` — paths exactos. Si sub-tab usa N3-static → sub-sub-tab components viven en `features/{agent}/components/{subtab}/{subsubtab}/` (paths anidados un nivel)
3. **Client root**: `{Agent}{Subtab}View.tsx` con `"use client"` línea 1 + props hidratación
4. **Data layer**: React Query para server data + Zustand para UI state (sin mezclar)
5. **Forms**: RHF + Zod en `types/{subtab}-schema.ts` + autosave debounce 600ms cuando aplique + discriminated unions cuando aplique
6. **Backend DDD Inside-Out**: domain → infrastructure → application → api; `PhiRepositoryBase` mandatory para repos PHI; dual filter `tenant_id+clinic_id`; audit log sync write pre-response
7. **Migrations**: raw SQL idempotent (`IF NOT EXISTS`); nunca `op.create_table()` ni `sa.Enum(create_type=True)`
8. **Telemetría**: tabla brand-local `vitalia_growth_studio_event` (NO `copilot_trace_event` engine); bucketed amounts; emitter shipped en `_shared/telemetry/`
9. **Tests**: Vitest unit + Playwright funcional + Playwright visual golden 3×2=6 PNGs + axe + BE pytest dual-tenant + arch fitness EXTEND

## Frontmatter requirements

### `01-spec.md` (responsabilidad `/po-ux`)

```yaml
---
story_id: ...
brand: vitalia
type: ui-story
state: refining
architecture_pattern: ADR-vitalia-004      # ★ MANDATORY para sub-tab stories
---
```

Sin este campo → `/po-ux` Step 5 gate FAIL, no transition refining→refined.

### `03-arch.md` (responsabilidad `/architect`)

```yaml
---
story_id: ...
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004      # ★ MANDATORY
adr_004_compliance: full | partial-with-rationale
---
```

Si `partial-with-rationale` → sección `§ Architecture Decisions` documenta qué sección del ADR se diverge + por qué + qué tradeoff se acepta. Sin justificación → `/architect` REFUSE cerrar ready package.

### `checkpoint.md` (responsabilidad `/pm-vitalia`)

```yaml
architecture_pattern: ADR-vitalia-004
```

Toda story Vitalia `state ∈ {idea, refining, refined, ready, developing, developed, reviewing}` (no done/archived) MUST tener este campo en frontmatter.

## Tests requeridos (que la implementación debe cumplir)

Arch fitness tests (`vitalia/backend/tests/architecture/` + `vitalia/frontend/src/__tests__/architecture/`) bloquean violations:

- `test_phi_dual_filter.py` — TODO repo PHI hereda `PhiRepositoryBase`
- `test_audit_log_sync_write.py` — TODO endpoint PHI escribe audit_log row pre-response
- `test_response_model_required.py` — TODO endpoint declara `response_model=`
- `test_growth_studio_event_no_phi.py` — payload de events no contiene PHI
- `test_no_phi_in_url_params.test.ts` — searchParams whitelist enforced
- `test_react_query_keys_convention.test.ts` — keys siguen `[module, subtab, action, ...filtersStable]`
- `test_features_no_cross_imports.test.ts` — `features/A` no importa de `features/B`

## Anti-patterns prohibidos

- `/architect` arranca sin verificar `01-spec.md::architecture_pattern == "ADR-vitalia-004"` (gate violado)
- `/po-ux` transitions `refining → refined` sin incluir `architecture_pattern` en frontmatter
- **★ v1.1 (2026-05-27): Shadcn `Tabs` internas (body) usadas para agrupar 3+ sub-secciones de una sub-tab** — Nivel 4 anti-pattern. Solución correcta: SubSubTabsBar (N3-static) en cabecera + routing `[subtab]/[subsubtab]/page.tsx` + entry en `AGENT_SUBSUBTABS`
- **★ v1.1: Single scroll con headers H2 múltiples cuando hay 3+ vistas conceptualmente discretas** — pierde discoverability. Usar N3-static
- **★ v1.1: Sub-tab con N3-static cuyo `AGENT_SUBSUBTABS[agent][subtab]` no esté declarado en `shell-routes.ts`** — routing 404 silencioso
- **★ v1.1: Custom tab bar dentro de `{Agent}{Subtab}View.tsx` que duplique función de SubSubTabsBar** — re-implementación contra convención cementada
- Sub-tab que usa Redux/Context para data fetch en lugar de React Query
- Sub-tab que mezcla Zustand con server data (Zustand es UI state ONLY)
- Repo PHI que no hereda `PhiRepositoryBase` "porque single-clinic tenant"
- Endpoint PHI sin `write_audit_log_sync` antes response
- Migration con `op.create_table()` o `sa.Enum(create_type=True)` (no idempotente)
- Telemetría escribe en `copilot_trace_event` engine en lugar de `vitalia_growth_studio_event` brand-local
- Forms sin Zod schema o sin RHF (custom state useState)
- Visual goldens omitidos (gate ADR-vitalia-003 cubre componentes; este ADR cubre integración completa)
- Capability YAML post-merge omitido (gate `pm-vitalia/SKILL.md § Capability inventory post-merge`)
- Divergir del patrón sin documentar rationale en `03-arch.md § Architecture Decisions`

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 — `/po-ux` Step 5 gate | Verifica `architecture_pattern: ADR-vitalia-004` en frontmatter spec | `/po-ux` |
| 2 — `/architect` REFUSE pre-arch | Verifica spec cita ADR + valida 9 secciones cobertura en arch output | `/architect` |
| 3 — `/auditor` checklist 9 secciones | Score cobertura per sección + REJECT si divergencias sin rationale | `/auditor` |
| 4 — Arch fitness tests | Bloquean violations cardinales (PhiRepositoryBase, audit, response_model, no-cross-imports, etc.) | CI |
| 5 — Pre-commit hook | Bloquea commit de `01-spec.md` Vitalia sub-tab story sin `architecture_pattern` field | `scripts/git-hooks/pre-commit` (TBD) |
| 6 — `/pm-vitalia` bootstrap Step 0 | Reporta stories abiertas sin `architecture_pattern` para backfill | `/pm-vitalia` |
| 7 — Capability inventory gate | `scripts/reconcile_capabilities.py --check-mode` exit 1 si capability YAML faltante | CI |

## Referencias

- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` — autoridad arquitectónica brand-local (SSoT del patrón)
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` — source story que origina el patrón
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT del shell
- `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` — mockup gate (complementario)
- `.claude/rules/backend-ddd.md` — DDD raíz
- `.claude/rules/frontend-fsd.md` — FSD-Lite raíz
- `.claude/rules/backend-migrations.md` — migrations idempotent
- `.claude/rules/tdd-mandatory.md` — TDD raíz
- `.claude/rules/tenant-isolation.md` — tenant filter raíz
- `vitalia/.claude/rules/hipaa-lite.md` — overlay HIPAA-lite (dual filter, audit, retention)
- `vitalia/.claude/rules/shell-mockup-per-component.md` — overlay mockup gate (ADR-003)
