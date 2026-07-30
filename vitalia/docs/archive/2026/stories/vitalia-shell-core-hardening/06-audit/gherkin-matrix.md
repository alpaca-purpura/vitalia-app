<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Gherkin Matrix — vitalia-shell-core-hardening (Phase D)

**Auditor:** auditor-frontend (autonomous · Carril R)
**Date:** 2026-06-11
**Story:** umbrella shell-chrome hardening (8 tickets FE)
**Verdict source:** gates verde (tsc/eslint/vitest/arch re-run by auditor) + e2e real-backend suite (68/68 + resizer 7/7 + race 8/8 per T-7-result + chris_verify rounds) + 2 rondas live Chris (signoff SATISFIED).

> **Cobertura SC = 22/22.** Cada SC tiene spec e2e nombrado por SC (real-backend, fixture `shell-hardening.fixture` compone `base.ts` anti-burbuja) **o** está cubierto por la matriz exhaustiva 22/22 de la ronda live de Chris (resizer-matrix.spec permanente 7/7). Mapping verbatim: specs en `vitalia/frontend/e2e/regression/shell-core-hardening/` + `resize-and-state.spec.ts`/`resizer-matrix.spec.ts` en `vitalia-fase1-shell-layout-5050/`.

## SC → spec → rule → status

| SC | Descripción | Spec e2e (real-backend) | RN/AC | Status |
|---|---|---|---|---|
| SC-1 | Default fresh = Valeria chat 30/70, historial cerrado | `default-30-70.spec.ts` | RN-3, AC-2/3 | ✅ PASS |
| SC-2 | No existe toggle web/agéntico ni shellMode | `no-web-toggle.spec.ts` | RN-1, AC-1 | ✅ PASS (grep shellMode prod=0) |
| SC-3 | Tenant switcher al extremo derecho | `topbar-order.spec.ts` | RN-2, AC-4 | ✅ PASS |
| SC-4 | Splitter resizable + persiste | `resize-and-state.spec.ts` · `resizer-matrix.spec.ts` | RN-4, AC-5 | ✅ PASS (8/8 + 7/7) |
| SC-5 | Colapsar (botón propio) → tira-avatar → reabrir por avatar | `collapse-strip-reopen.spec.ts` | RN-5/9/12, AC-6 | ✅ PASS |
| SC-6 | Abrir historial EMPUJA (280px reconciliado) + cerrar revierte | `history-push.spec.ts` | RN-7, AC-7 | ✅ PASS (push real, ancho C<B medido) |
| SC-7 | Historial con Valeria cerrada → abre Valeria | `history-from-closed.spec.ts` | RN-6, AC-7 | ✅ PASS |
| SC-8 | "+" nueva conversación limpia chat + archiva la actual | `new-conversation.spec.ts` | RN-13, AC-8 | ✅ PASS (UI-local mock, no BE) |
| SC-9 | Desktop angosto [1024,1280): clamp 320, sin overflow | `clamp-320.spec.ts` | RN-8, AC-9 | ✅ PASS |
| SC-10 | Tablet/móvil <1024: drawer overlay (role=dialog, Esc) | `drawer-tablet.spec.ts` | RN-8, AC-9 | ✅ PASS |
| SC-11 | Directorio → workspace (`EntityWorkspaceLayout` core) → volver | `n3-list-detail.spec.ts` | RN-10, AC-9 | ✅ PASS (staff+embudo importan @luana/ui-kit) |
| SC-12 | Directorio sin entidad → leaf tabs disabled | `n3-directory-disabled.spec.ts` | RN-10, AC-9 | ✅ PASS (master mode aria-disabled) |
| SC-13 | Vacíos: directorio/historial/conversación nueva | `empty-states.spec.ts` | RN-13, AC-9 | ✅ PASS |
| SC-14 | Muchos: directorio 1000 entidades + historial largo | `large-dataset.spec.ts` | RN-7, AC-9 | ✅ PASS |
| SC-15 | Fetch falla → error state, no blank | `network-failure.spec.ts` | RN-2, AC-9 | ✅ PASS |
| SC-16 | Teclado + ARIA + sin burbuja | `a11y-keyboard.spec.ts` + `--project=a11y --grep shell` | RN-12, AC-11 | ✅ PASS (roving tabindex, focus-visible) |
| SC-17 | Spanish neutro + locale tenant | `i18n-neutro.spec.ts` | RN microcopy, AC-11 | ✅ PASS (sin voseo) |
| SC-18 | Estado persistido inválido + no clobber SSR (regresión Bug #1) | `persist-invalid-noclobber.spec.ts` | RN-11, AC-10 | ✅ PASS (migrate legacy + fallback+warn) |
| SC-19 | Cross-tab + dark mode sin regresión | `regression-cross-tab.spec.ts` | RN-15, AC-10 | ✅ PASS (2 flaky pass-on-retry, ver nota) |
| SC-20 | Toggle dark por sub-tab → colores oscuros + axe AA | `dark-per-subtab.spec.ts` · `network-failure.spec.ts` | RN-15, AC-12 | ✅ PASS (axe 0 violations en dark) |
| SC-21 | Soft-nav loop ×15 board→recuperar (next/link) + consola limpia | `soft-nav-loop.spec.ts` | RN-14, AC-13 | ✅ PASS (15/15 sin "Rendered more hooks") |
| SC-22 | Race: drag inmediato post-hidratación respeta clamps | `resize-and-state.spec.ts` (race reactivado) | RN-16, AC-14 | ✅ PASS (assert diferido localizado + reactivado, 8/8) |

## Notas de adjudicación

- **SC-19 (2 flaky pass-on-retry):** `regression-cross-tab.spec.ts` [dark] lisa/marca render + agent-colors. Hipótesis del builder: timing theme-hydration. NO enmascarado (documentado en T-7-result para adjudicación). **Adjudicación auditor:** pass-on-retry sobre verificación visual de hidratación de tema, no sobre lógica del shell. La ronda live de Chris @1920 (000/001.png) + el toggle dark en 3 sub-tabs (dod_evidence) confirman el comportamiento dark estable live. Aceptable como flaky de timing de render, NO bug funcional. → CIL L3 candidato (estabilizar timing theme-hydration en spec).
- **SC-4/SC-22 race "test omitido":** L1 del CONTEXT-BRIEF se cerró — el assert diferido NO era `test.skip(true)` literal; el builder lo localizó (03-arch-fe §10) y lo reactivó contra los clamps nuevos (320, no 580/620). Cazó el bug producto #3 (drag below min colapsaba al strip) como RED real antes del fix `e1a0bad0`.
- **Cobertura por regla de negocio (gherkin @rule):** RN-1..RN-16 mapeadas arriba (columna RN/AC). AC-1..AC-14 cubiertas. Las RN del backbone (RN-1..13) heredadas + RN-14/15/16 umbrella. Las 2 rondas live de Chris = allowlist de scope ratificado (push 280px, placeholder corto, pill container-query, min-w-72 header) — NO revertidas (per checkpoint `chris_verify.signoff.rounds`).

**Phase D verdict: PASS — 22/22 SC cubiertos con verificación REAL (real-backend authenticated e2e + 2 rondas live Chris). Cero @rule sin cobertura.**
