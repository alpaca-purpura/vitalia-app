---
slug: autosave-primitive-platform
kind: outcome
owner: /pm-luana
state: refining
adr_status: accepted
ratified_by_chris: true
created: 2026-05-31
priority: MEDIUM
adr: docs/architecture/luana-platform/ADR-012-autosave-primitive-platform.md
why_now: |
  Chris definió que el autoguardado debe ser UNIVERSAL en toda la app. Hoy está duplicado
  per-feature: vitalia ~23 archivos + nicolify ~23 archivos lo reimplementan por separado
  (solo en Lisa hay 4 hooks casi idénticos + 2 copias de AutosaveBadge), cero compartido en
  core/@luana. La story arreglar-guardado-voz-y-tono (2026-05-31) encontró 5 bugs apilados en
  UNO de esos hooks (auth-readiness Clerk, error handling, telemetría, contrato FE↔BE); los
  hermanos arrastran la misma fragilidad y el fix de robustez (getTokenReady) quedó solo en
  voz-y-tono. Cada arreglo del autosave hoy es N arreglos. Lift a primitiva compartida =
  un fix arregla todo + UX consistente + cierra la clase de bugs de raíz.
estimated_effort: ~3-5d (build primitiva @luana/{hooks,ui-kit,schemas} + tests + consumer ref; luego adopción incremental vitalia + nicolify)
consumers: [vitalia, nicolify, comunify (futuro), lupulo (futuro), + 6 brands bootstrap]
prior_art:
  - vitalia/frontend/src/features/lisa/hooks/use{Identity,Personality,Contact,Visuals}Autosave.ts
  - vitalia/frontend/src/components/marca/shared/AutosaveBadge.tsx (+ copia en features/lisa/.../identidad/)
  - nicolify/frontend/src/** (~23 archivos con autosave — equivalentes a reconciliar)
homes:
  - core/@luana/hooks        # useAutosave(contract)
  - core/@luana/ui-kit       # <AutosaveBadge>
  - core/@luana/schemas      # AutosaveContract types
stories:
  - build-autosave-primitive-luana          # ✅ DONE 2026-05-31 — @luana primitiva (useAutosave + AutosaveBadge + contrato) + nicolify form-runtime reescrito encima. Auditor APPROVED.
  - vitalia/adopt-autosave-primitive         # ⏳ pendiente — consumer (consolida 4 hooks lisa → useAutosave) · /pm-vitalia
  - nicolify/adopt-autosave-primitive        # ⏳ pendiente — migrar pantallas restantes a la primitiva · /pm-nicolify
related_outcome: luana-core-ui-foundation
---

# Outcome — Autoguardado como primitiva compartida (platform)

## Qué

Construir `useAutosave` (`@luana/hooks`) + `<AutosaveBadge>` (`@luana/ui-kit`) + contrato (`@luana/schemas`)
con: debounce · estados idle/dirty/saving/saved/error · auth-ready robusto · retry/backoff · invalidación
React Query · telemetría estándar · manejo de error consistente. Migrar vitalia + nicolify a consumirlo y
borrar las implementaciones per-feature. Decisión: **ADR-012**.

## Por qué ahora

Ver `why_now` (frontmatter). Resumen: Chris lo quiere universal + la duplicación ya nos costó 5 bugs en una
sola pantalla y el fix no se propaga. ≥2 brands con el patrón = lift candidate confirmado (promotion gate).

## Definición de DONE

`@luana/{hooks,ui-kit,schemas}` exportan la primitiva con tests; vitalia (Lisa: 4 hooks → 1) + nicolify la
consumen; cero copias de `AutosaveBadge`; un fix de autosave se hace en un solo lugar. Verificación REAL
(no mock del backend del surface bajo prueba).

## Próximo paso

`/pm-luana`: con Chris ratificando ADR-012 → arrancar story `build-autosave-primitive-luana` vía `/architect`
(definir el contrato exacto reconciliando vitalia + nicolify). Luego stories consumer por brand.
