# Gherkin verification matrix — vitalia/vitalia-fase2-adrian-inbox

> Auditor: Phase D (/auditor vitalia, autónomo)
> Date: 2026-06-04
> Model: 2-modos (amendment 2026-06-04 — ver 01-spec § Scope amendment)
> Verdict: **APPROVED** — 17/17 reglas con cobertura PASS, 0 MISSING.

Fuente de verificación: `e2e-live` = golden Playwright `adrian-inbox-modes.spec.ts` (importa `fixtures/base.ts` anti-burbuja) contra `dev-app.vitalialat.com` (backend real, 0 mocks del surface) — **7 passed**, writes DB-verified · `be-test` = pytest módulo inbox (103 passed) · `shell-story` = `vitalia-bugfix-shell-nav-scroll-errors` (`done`) · `regression` = suite slice-1/features-adrian reusada (344 vitest passed).

| Regla (RN) | Tag | Scenario | Fuente | Status | Evidencia |
|---|---|---|---|---|---|
| RN-1 modo por conversación (2-modos decide/consulta) | @rule-mode-per-conv | SC-mode | e2e-live | ✅ PASS | golden: `PATCH /mode` 200 + `aria-checked` refleja + DB `handler_mode=ai` |
| RN-2 audit de modo/pausa/nudge sync write | @rule-mode-audit | SC-mode/SC-4 | e2e-live + be-test | ✅ PASS | golden writes + BE audit-log tests (suite 103) |
| RN-3 decide autónomo + escala (sales_agent runtime, consume-only) | @rule-escalate | SC-3 | be-test | ✅ PASS | runtime engine read-only; BE PHI/redirect tests |
| RN-4 consulta = humano firma (0 msgs pre-aprobación) | @rule-consulta-signs | SC-2 | be-test + e2e-live | ✅ PASS | toggle consulta live + BE send-gating tests |
| RN-5 pausar silencia a Adrián (reemplaza manual) | @rule-pause-silence | SC-4 | e2e-live | ✅ PASS | golden: `POST /pause` 200 + DB `pause_until` set + botón→Pausado |
| RN-6 glass-box (activity stream montado) | @rule-glassbox | SC-1 | e2e-live | ✅ PASS | golden: `agent-activity-stream` visible al abrir conv |
| RN-7 PHI firewall (ComplianceService bloquea canal no-encriptado) | @rule-phi-firewall | SC-3 | be-test | ✅ PASS | `test_phi_voice_redirect.py` (13 PHI tests, en suite 103) |
| RN-8 ContactSidebar RBAC + wrapper data-phi | @rule-contact-masked | SC-privacy | be-test + e2e-live | ✅ PASS | golden: ficha visible + `data-phi` conservado (FE-A6); RBAC BE |
| RN-9 tenant isolation (cross-tenant → 404) | @rule-tenant-isolation | SC-10 | be-test + e2e-live | ✅ PASS | BE dual-tenant + cross-tenant 404 (arch dual-filter green) |
| RN-10 activity stream sanitizado | @rule-activity-sanitize | SC-1 | be-test | ✅ PASS | `sanitize_payload` server-side (BE test) |
| RN-11 inbox 100% del lienzo | @rule-full-canvas | SC-5 | shell-story | ✅ PASS | verificado en `vitalia-bugfix-shell-nav-scroll-errors` (`done`) |
| RN-12 modo conversación reversible (recuerda estado Valeria) | @rule-conversation-mode | SC-5 | shell-story | ✅ PASS | idem shell-story; `ConversationModeButton` presente |
| RN-13 nudge sólo sobre conv viva | @rule-nudge-live | SC-6 | be-test + e2e-live | ✅ PASS | `test_nudge_service.py` (suite) + botón `nudge-button` presente |
| RN-14 deep-link estable, PHI nunca en URL | @rule-deeplink | SC-10/SC-1 | e2e-live | ✅ PASS | golden: `?conv={uuid}` sin PHI en URL |
| RN-15 RBAC `_INBOX_OPERATOR_ROLES` (owner 200; marketing/sales 403) | @rule-inbox-rbac | SC-4 | be-test + e2e-live | ✅ PASS | `test_router_mode.py` owner-200/marketing-403 (suite); golden owner |
| RN-16 leads visibles por defecto (interim; data-phi conservado) | @rule-lead-visible | SC-privacy | e2e-live | ✅ PASS | golden: nombre/teléfono/correo sin `***` |
| RN-17 composer dock siempre montado + pausa 60/permanente sin reason | @rule-composer-dock | SC-composer | e2e-live | ✅ PASS | golden: `thread-composer-dock` + textarea enabled; modal 2 botones sin reason |

**Huecos (MISSING): 0.** **SC huérfanos: 0.** Todas las reglas del `01-spec § Scope amendment` + `§ Matriz de cobertura` tienen cobertura real (acción ejercida + efecto, no GET 200 — `test-design-doctrine.md`).

## Cross-check con la § Matriz de cobertura del 01-spec (mitad trasera del loop)

Cada `Bif` / `RN` que el spec mapea a `SC-X` llegó a test/verificación real. El full-canvas (RN-11/12/AC-7) + responsive (AC-12) están explícitamente SPLITeados a la shell-story (`done`) — no es un hueco, es un hogar declarado.

## Live-verify (DoD #37) — writes reales ejercidos

| Acción | Status | Efecto observado |
|---|---|---|
| `PATCH /inbox/conversations/{instagram}/mode` | ✅ | 200 + aria-checked + DB `handler_mode=ai` (era `human`) + `updated_at` fresco |
| `POST /inbox/conversations/{carlos}/pause` (60min) | ✅ | 200 + botón→"Pausado" + DB `pause_until` set + `updated_at` fresco |

Anti-burbuja: el golden importa `fixtures/base.ts` (0 pageerror / 0 hydration / 0 console.error / 0 `/api` 4xx-5xx / 0 Next overlay). 7 passed.

## Hallazgo del auditor (Carril R) — incomplete-fix cazado

`_get_retract_service` (endpoint `POST .../revert`) tenía el MISMO bug HB-50 (escribe pero usaba la sesión no-committing) — la commit-fix original cubrió 5 factories, omitió retract. Auditor-backend lo arregló (Carril R mecánico) + re-corrió gates (103 inbox tests verdes). Detalle: `T-reconcile-be-review.md`.

## Pre-existentes (NO de esta story — no atribuir)

- 4 reds FE en `src/__tests__/architecture/{test_fsd_boundaries,test_no_cross_feature_imports}.test.ts` + `phi/FrozenLeadRow` + `audited-section` spy — fuera de `features/adrian/` (que está 344/344 verde); los arch `.ts` están `M` por sesiones concurrentes (embudo/canal-inbound). Documentado en HANDOFF §8.
- BE arch `test_pgcrypto_phi_columns` (`fidelizacion treatment_plans.notes` TEXT vs BYTEA) — deuda HIPAA separada, no toca inbox.
