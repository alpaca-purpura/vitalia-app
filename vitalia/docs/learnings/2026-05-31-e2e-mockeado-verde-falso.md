---
brand: vitalia
date: 2026-05-31
slug: e2e-mockeado-verde-falso
promotable: candidate
applies_to_other_brands_potentially: [vitalia, comunify, nicolify, lupulo]
target_core_package: n/a (doctrina de testing, no código)
tags: [e2e, playwright, verification-real, mocking, false-green, clerk, harness]
---

# E2E mockeado = verde falso: la verificación-real destapa lo que el mock esconde

## Qué aprendimos

El bug `arreglar-guardado-voz-y-tono` (un "Error al guardar" en el arquetipo) eran en realidad **5 fallas
apiladas** en el mismo guardado: (1) `sanitize_payload(compliance_level=)` kwarg muerto → 500, (2) SQL
`:x::uuid` cast roto en SQLAlchemy text() → 500, (3) voice-blocks camelCase vs BE snake_case `extra=forbid`
→ 422, (4) `_emit_telemetry` sync llamando async + sin tenant_id → telemetría perdida, (5) GET /personality
flaky por auth-readiness de Clerk. **El E2E existente NUNCA vio ninguna** porque el harness lisa-marca
**mockeaba el backend** (`page.route`), usaba **data-testids fantasma** (`lisa-marca-content` que no existía),
y apuntaba a un **tenant ficticio**. La suite "pasaba" sin ejercer nada real → la cap estaba `live` con
`e2e_test: null`. Ése es **el motivo estructural por el que el bug shipeó**.

## Aplicación práctica

- **Cuándo aplica:** todo E2E de comportamiento (guardado, persistencia, flujos críticos).
- **Cómo aplica:** los specs de regresión que prueban "que funciona" deben pegarle al **backend real**
  (no `page.route` del endpoint bajo prueba) y ejercer la **acción real** (write/save), confirmando el
  efecto (persistencia round-trip) + leyendo logs. Mockear el backend del happy-path = verde falso.
  Mockeo permitido SOLO para inyectar fallas deliberadas (ej. 503 para probar el badge de error).
- **Señal de alarma:** un scenario de cap con `status: live` + `e2e_test: null`, o un POM que espera
  data-testids que no existen en los componentes, o un fixture que setea `setupMocks(GET ...)`.
- **Cuándo NO aplica:** unit/component tests (ahí el mock es correcto y necesario).

## Cómo verificar de verdad (bar mínimo)

Ejercer la acción (incl. el **write**), leer logs del backend (sin 4xx/5xx inesperado), confirmar el efecto
(DB/persistencia round-trip), no asumir por un `GET 200`. Ver `.claude/rules/test-design-doctrine.md`
§ Verificación REAL ≠ HTTP 200.

## Referencias

- Story: `vitalia/docs/archive/2026/stories/arreglar-guardado-voz-y-tono/`
- Follow-up harness: `vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/`
- Rule: `.claude/rules/test-design-doctrine.md` § Verificación REAL
- Memory: `verification-real-not-200`
