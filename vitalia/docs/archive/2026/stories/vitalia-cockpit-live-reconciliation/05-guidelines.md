# 05-guidelines — vitalia-cockpit-live-reconciliation

## Patterns required
- **Disciplina de scope (HARD):** cero reconstrucción de caps slice-1 (Fase 2). El diff solo contiene: fix compose Fase 0, harness de sweep, script de matriz, fixes inline acotados (gates verdes), edición de frontmatter de caps (status/replaced_by), y el doc vivo.
- **Fixes inline = agresivo pero gates verdes:** multi-archivo acotado + lógica simple OK. ANTES de cerrar cualquier fix → `ruff` + `tsc --noEmit` + `eslint` + `mypy` (si BE) + `arch-fitness` + `jscpd` + tests existentes en VERDE. Si un fix rompe un gate → revertir + mapear a backlog F2.
- **Sweep deriva superficies del SSoT:** leer `vitalia/frontend/src/lib/shell-routes.ts` (RIBBON_SUBTABS + AGENT_SUBSUBTABS) + `app/**/page.tsx`. NUNCA hardcodear la lista de rutas.
- **Reusar fixture Clerk:** el harness usa `vitalia/frontend/e2e/auth.fixture.ts` (storage state). NO reinventar auth.
- **Verde estricto:** cap → `status: live` SOLO si computed_status=verified-live (ruta OK + ≥1 scenario con e2e existente y pasa + flujo de negocio cumplido). Cascarón que renderiza ≠ verde.
- **Evidencia auditable:** toda fila ROTO/easy-fix de la matriz cita path a screenshot/console-log/test. Sin evidencia → no cuenta.
- **HIPAA-lite en evidencia:** screenshots de superficies con datos paciente → verificar seed mock; redactar/sanitizar PHI. NUNCA evidencia con PHI real.
- **Spanish neutro** en microcopy revisado (sin voseo salvo sales_agent).
- **Tooling de ledger reusado** (NO recrear): `compute_capability_status.py`, `reconcile_capabilities.py --validate-ledger`, `validate_code_cap_bidirectional.py`.
- **Migrations idempotentes** si algún fix inline tocara schema (`IF NOT EXISTS`).

## Patterns forbidden
- ❌ Reconstruir cualquier feature slice-1 (adrian/lucas/camila inbox/embudo/etc.) — eso es Fase 2, se MAPEA.
- ❌ Editar el shell wrapper compartido (`components/ui/`, `components/shared/shell-organism/`, `app/layout.tsx`) para "arreglar" una superficie — rompe las 24 a la vez. Mapear.
- ❌ Editar `core/luana-core-*/src/` (engine boundary — `/pm-luana`).
- ❌ Editar `{other_brand}/**`.
- ❌ Marcar cap verde porque la ruta carga 200 (cascarón ≠ verified-live).
- ❌ Inflar el ledger: dejar `status: live` en caps que computan stub/declared-live/drift sin justificación infra-only explícita.
- ❌ Hardcodear lista de rutas del sweep (derivar de SSoT).
- ❌ `git add .` / `-A` (índice compartido del hub — commit por pathspec).
- ❌ Evidencia con PHI sin sanitizar.

## Files in scope (builder edita SOLO estos)
- `vitalia/docker-compose.dev.yml` (Fase 0 remount core/)
- `vitalia/frontend/e2e/regression/live-reconciliation/**` (harness + specs nuevos)
- `scripts/build_live_reconciliation_matrix.py` (script generador matriz — NEW)
- `scripts/check_matrix_evidence.py` (helper validación evidencia — NEW, opcional)
- `vitalia/docs/domains/ops/live-reconciliation.md` (matriz viva — NEW)
- `vitalia/docs/product/capabilities/**/*.yaml` (frontmatter: status real + replaced_by — Fase 3)
- `playwright.config.ts` (registrar proyecto/spec del sweep si hace falta)
- **Fixes inline findings-driven:** archivos puntuales que el sweep revele rotos, ACOTADOS + gates verdes (FE features, BE módulos — NUNCA el shell compartido ni engine).

## Files builder NEVER touches (escalate)
- `core/luana-core-*/src/**` (engine — `/pm-luana`)
- `{otro_brand}/**`
- `vitalia/frontend/src/components/ui/**` + `components/shared/shell-organism/**` + `app/layout.tsx` (shell compartido — mapear, no reparar inline)
- `.claude/**` + `vitalia/.claude/**`

## must_load_skills (builder MUST cargar + reportar "Skills consulted")
required:
  - { id: playwright-expert, when: "harness sweep + a11y", purpose: "POM, Clerk fixture, network mocking, smoke debugging, NATIVE Linux (nunca make e2e Docker)" }
  - { id: vitalia-design-system, when: "fixes inline FE + review fidelidad", purpose: "SSoT shell-organism + átomos/moléculas + tokens + 6 agentes — canal único de builder-frontend (no hereda overlay)" }
  - { id: frontend-expert, when: "fixes inline FE", purpose: "FSD-Lite, Shadcn reuse, visual fidelity" }
  - { id: backend-expert, when: "fixes inline BE", purpose: "DDD, tenant isolation, arch fitness" }
  - { id: ".claude/rules/tenant-isolation.md", purpose: "cross-tenant leak = ROTO crítico" }
  - { id: "vitalia/.claude/rules/hipaa-lite.md", purpose: "no PHI en evidencia + dual filter en fixes BE PHI" }
  - { id: ".claude/rules/spanish-text.md", purpose: "microcopy neutro en review" }
  - { id: ".claude/rules/anti-duplication.md", purpose: "no recrear tooling de ledger" }
  - { id: ".claude/rules/frontend-visual-fidelity.md", purpose: "criterio de fidelidad del review per cap" }
  - { id: ".claude/rules/anti-orphan-integration.md", purpose: "registrar harness + matriz (no isla)" }
  - { id: ".claude/rules/tdd-mandatory.md", purpose: "fix con regression test RED→GREEN cuando aplique" }
reference_artifacts:
  - "vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/01-spec.md"
  - "vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/03-arch.md"
  - "vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/04-validators.yaml § test_construction_plan + playwright_visual_scope"
  - "vitalia/docs/learnings/2026-05-27-live-audit.md (mapa base + workflow § 8)"
