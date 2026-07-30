---
brand: platform
date: 2026-05-31
slug: lift-sin-dejar-deuda-tsc
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
tags: [lift, @luana, tsc, design-system, anti-duplication, primitive]
---

# Lift a @luana sin dejar deuda tsc + colapsar duplicación per-feature en una primitiva

## Qué aprendimos
1. **Duplicación per-feature = N fixes.** vitalia tenía 4 hooks de autosave idénticos + nicolify su propio form-runtime; un bug (auth-readiness) vivía en uno y no se propagaba el fix. Colapsarlos en una primitiva compartida (`@luana/hooks` useAutosave + `@luana/ui-kit` AutosaveBadge + `@luana/schemas` contrato) = un fix arregla todo + UX consistente. `getToken` inyectado desacopla el auth provider (no importa Clerk en el package).
2. **Un lift puede dejar deuda tsc silenciosa.** El lift original de @luana (b1bdb3ab/3282768a) movió hooks **acoplados a brand** (`use-copilot-offset`, `use-shell-mutex`) con imports `@/...` rotos → el package quedó tsc-rojo desde entonces sin que nadie lo notara (los consumers importan piezas puntuales, no compilan el package entero). Regla: **un lift a un package compartido debe dejar el package tsc-verde** (o el código acoplado a brand NO debe liftarse). Validar `tsc --noEmit` del package completo post-lift.

## Aplicación práctica
- Al detectar ≥2 brands con el mismo patrón → lift a `@luana/*` (promotion gate) con `getToken`/deps **inyectados** (no acoplar a brand/provider).
- Post-lift: `tsc --noEmit` del package entero verde. Si un archivo lifteado referencia `@/...` de una brand → NO pertenece a @luana (devolver a la brand o desacoplar).
- Verificación de librería = Vitest unit/component determinista; el E2E real-backend vive en las stories de adopción (no mockear el surface bajo prueba).

## Referencias
- Story: `docs/archive/2026/stories/build-autosave-primitive-luana/` · ADR-012 · Outcome `autosave-primitive-platform`
- observed-bug: `docs/observed-bugs/2026-05-31-luana-hooks-uikit-tsc-lift-debt.md`
