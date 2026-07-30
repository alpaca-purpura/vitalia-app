---
story_id: vitalia-cockpit-live-reconciliation
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # NO es story sub-tab/feature; es diagnóstico+infra+ledger. Ver § Architecture Decisions
priority: high
---

# 03-arch — Reconciliación cockpit ↔ realidad live

## Surfaces involved

- **INFRA (dev-stack):** sí — `vitalia/docker-compose.dev.yml` remount `core/` (Fase 0 boot fix).
- **FE / E2E:** sí — suite Playwright de diagnóstico (sweep harness + specs por superficie); fixes inline FE acotados (gates verdes).
- **BE:** condicional — solo fixes inline acotados que el sweep revele (gates verdes); NO módulo nuevo.
- **DOCS / LEDGER:** sí — reconciliación de `vitalia/docs/product/capabilities/**/*.yaml` (status real) + artefacto vivo `vitalia/docs/domains/ops/live-reconciliation.md`.
- **AGENTIC:** no (R23 n/a).
- **ENGINE `core/luana-core-*/src/`:** NO se edita. El remount monta `core/` read-write en el container pero el scope NO toca lógica engine; si un fix lo requiriera → STOP + `/pm-luana`.

## Architecture Decisions

- **adr_004_compliance = n/a:** ADR-vitalia-004 (shell-feature 9 secciones) aplica a stories que construyen una **sub-tab nueva**. Esta historia NO construye feature: diagnostica, repara drift, y reconcilia el ledger. Se cita el ADR en frontmatter por requisito de campo, marcado `n/a-with-rationale`. Los fixes inline que toquen una sub-tab existente SÍ respetan el ADR de esa sub-tab (no lo violan).
- **Two-stage tickets:** Fase 0 (boot) + Fase 1 (sweep + matriz v1) son concretos y enumerables AHORA. Fase 2 (review técnico) + Fase 3 (reparar/reconciliar) son **findings-driven**: el detalle de QUÉ reparar emerge del sweep. Se modela como un ticket iterativo (T-3) cuyo bitácora registra cada fix; los items que se MAPEAN (no se reparan) salen como entradas de backlog F2, NO como tickets de esta story.
- **Sweep deriva superficies del SSoT, no hardcodea:** el harness lee `vitalia/frontend/src/lib/shell-routes.ts` (RIBBON_SUBTABS + AGENT_SUBSUBTABS) + rutas `app/**/page.tsx` para enumerar superficies navegables. Robusto ante cambios del shell.
- **Verde = criterio estricto (anti-falso-verde):** una cap solo queda `verified-live` si ruta OK + ≥1 scenario con e2e que existe y pasa (cross_check_3 HARD) + flujo de negocio del spec original cumplido. Renderizar el cascarón ≠ verde.

## Prior art audit

- **Engine consumed via import:** N/A (no se crea código que deba consumir engine; el remount EXPONE `core/@luana/*` al container vía bind mount — eso es el fix, no consumo nuevo).
- **Tooling reusado (NO recrear):** `scripts/compute_capability_status.py` (computa verified-live/drift/declared-live/partial/stub) · `scripts/reconcile_capabilities.py --validate-ledger` · `scripts/validate_code_cap_bidirectional.py` (cross_check_3) · `scripts/generate_code_to_cap_index.py`. La reconciliación del ledger se apoya 100% en estos.
- **Suite e2e reusada:** `vitalia/frontend/e2e/` (~30 specs: shell-organism, a11y, visual, auth, regression) — el sweep EXTIENDE, no reescribe. Reusa `auth.fixture.ts` (Clerk storage state).
- **Prior-art directo:** `vitalia/docs/learnings/2026-05-27-live-audit.md` (mapa 71 caps + workflow generalizable § 8) + `2026-05-25-mockup-playwright-audit-cycle.md` (técnica inspect). Esta historia operacionaliza ambos.
- **Net-new justificado:** `vitalia/docs/domains/ops/live-reconciliation.md` (matriz viva) + harness de sweep. No existe equivalente; es cap `ops.live-reconciliation-sweep` nueva (promotable cross-brand).
- **Cross-brand mirror:** cero. Single-brand (vitalia). El patrón es lift-candidate futuro (no en esta story).

## Fase 0 — Boot fix (INFRA)

**Causa raíz:** container frontend bind-montea solo `vitalia/frontend`; `core/@luana/*` no está en el container → linking workspace de `@luana/hooks@0.2.0` (export `use-store-hydration` nuevo) quedó stale → `:3002` 500.

**Fix:** en `vitalia/docker-compose.dev.yml` servicio `vitalia_frontend_dev`, agregar bind mount de `core/` (read-write para preservar symlinks workspace) + el anonymous volume de node_modules que corresponda. Diseño:

```yaml
# vitalia/docker-compose.dev.yml · vitalia_frontend_dev.volumes
volumes:
  - ./vitalia/frontend:/app/vitalia/frontend:rw
  - ./core:/app/core:rw                          # ★ NEW — expone @luana/* workspace al container
  - /app/vitalia/frontend/node_modules           # anonymous volume (image-baked)
  - /app/core/node_modules                        # ★ NEW — proteger node_modules de core si aplica
```

Post-edit: `docker exec ... pnpm install --prefer-offline` (ahora resuelve el workspace) + `docker exec ... alembic upgrade head` (reconciliar migraciones, prior-art mostró drift 032→033) + `docker restart vitalia_frontend_dev`.

**Gate Fase 0:** `:3002/sign-in` → 200 · `Module not found`=0 en logs · `valeria-chat-happy.spec.ts` PASS.

> **Riesgo + verificación:** montar `core/` podría cambiar cómo resuelve pnpm dentro del container. Verificar que NO rompe otros `@luana/*` ya funcionando (ui-kit, design-tokens). Si el remount introduce regresión de resolución → fallback documentado: rebuild de imagen (Q1 opción b) como plan B, NO inventar otra cosa.

## Fase 1 — Sweep harness + matriz v1 (FE/E2E + tooling)

- **Harness:** spec(s) Playwright en `vitalia/frontend/e2e/regression/live-reconciliation/` que:
  1. Login Clerk (reusa `auth.fixture.ts`).
  2. Enumera superficies navegables desde `shell-routes.ts` + rutas `app/`.
  3. Por superficie: navega, captura `status HTTP | console errors | screenshot | a11y snapshot básico`, clasifica verdict `OK|ROTO|INACCESIBLE|SIN-UI`.
  4. Emite findings estructurados (JSON) que un script convierte en la matriz markdown.
- **Anotación externas (Q2):** admin Streamlit / `/public/[clinic-slug]` / `/onboarding/wizard` → anotadas (status observado), sin barrido profundo.
- **Matriz v1:** `vitalia/docs/domains/ops/live-reconciliation.md` — tabla `cap_id | declared_status | computed_status | ruta | sweep_verdict | evidencia | technical_verdict | acción | story_mapeada`. `computed_status` viene de `compute_capability_status.py`.

## Fase 2+3 — Review técnico + reparar/reconciliar (findings-driven, T-3 iterativo)

- **Review técnico per cap con código** (las ~24 navegables + las que el sweep tope): estándares FSD/DDD, tenant isolation, visual fidelity, a11y declarada, reglas de negocio del spec original, español neutro. Clasifica `cumple | easy-fix | map`.
- **Reparar inline (agresivo, gates verdes):** aplicar fixes acotados (multi-archivo + lógica simple OK) MIENTRAS `ruff+tsc+eslint+mypy+arch-fitness+jscpd+tests` queden verdes. Fix que rompe gate → revertir + mapear.
- **Mapear:** lo grande (reconstruir cap slice-1, feature nueva, test nuevo de comportamiento no cubierto que rompe gates) → entrada de backlog F2 con evidencia (NO ticket de esta story).
- **Reconciliar ledger:** por cada cap, set status real (`compute_capability_status.py` da el computed); caps sobre-declaradas pasan a status honesto + `replaced_by` cuando superseded. Correr `reconcile_capabilities.py --validate-ledger` (exit 0) + `validate_code_cap_bidirectional.py` (cross_check_3 sin drift en caps que queden live).

## Integration design (CONN)

- **Reachability path:** `Chris abre cockpit (:4002) → tab que lista caps → ve computed_status REAL por cap` (post-reconcile, no "live" uniforme). Paralelo: `Chris/Claude corre el sweep harness → genera vitalia/docs/domains/ops/live-reconciliation.md → fuente de verdad cap↔realidad`.
- **Consumers:** la matriz `live-reconciliation.md` la consume (a) Chris (revisión), (b) `/pm-vitalia` (priorizar backlog F2), (c) futuros audits (regeneran). El sweep harness lo consume el comando `make`/`npx playwright` + futuros re-audits. El ledger reconciliado lo consume el cockpit (lee `_status-computed.json` + frontmatter caps).
- **Registration points:** (1) el harness se registra como proyecto/spec en `playwright.config.ts` (alcanzable vía `npx playwright test`). (2) la cap nueva `ops.live-reconciliation-sweep` se registra en `vitalia/docs/product/capabilities/ops/`. (3) el doc vivo se enlaza desde `vitalia/docs/domains/INDEX.md` (si existe) para ser navegable.
- **Home:** cap_target `ops.live-reconciliation-sweep` (new). `dev_preview` apunta al harness spec + el doc vivo.

## Cross-cutting decisions

- **Tenant isolation:** el sweep corre autenticado multi-tenant (reusa fixture); cualquier cross-tenant leak detectado = fila ROTO crítica.
- **HIPAA-lite:** el sweep NO debe loguear PHI en evidencia (screenshots de superficies con datos paciente → verificar seed es mock, sanitizar). Evidencia con datos sensibles → redactar.
- **Spanish neutro:** microcopy revisado como parte del review técnico (sin voseo salvo sales_agent).
- **Engine boundary:** remount expone `core/` pero ningún ticket edita `core/luana-core-*/src/`.
