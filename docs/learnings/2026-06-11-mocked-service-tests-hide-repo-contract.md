---
title: "Tests con repo mockeado no validan el contrato service→repo (falso verde BE-interno)"
date: 2026-06-11
type: technical
brands_affected: [vitalia, nicolify, comunify, lupulo]
origen: "bug demo vitalia-fase2-adrian-embudo — channel no persistía; fix 'verde 12/12' que 500eaba live"
ratified_by: chris
promotable: yes
tags: [testing, mocks, contract-test, asyncmock, falso-verde, tdd, ddd-layers]
---

# Tests con repo mockeado no validan el contrato service→repo (falso verde BE-interno)

## Contexto

Bug demo: lead creado con canal, el canal no aparecía en el detalle. Un fix extendió `LeadService.create()` para pasar los campos funnel al repo y citó "BE tests: 12/12 funnel ✅". En live: **500 en POST /crm/leads** — `LeadRepository.create()` no aceptaba esos kwargs (`TypeError: unexpected keyword argument 'stage'`).

Los 12/12 eran verdes porque `test_funnel_api.py` mockea el SERVICE completo, y los tests del service usan `AsyncMock` como repo — **un AsyncMock acepta cualquier kwarg sin quejarse**. El `TypeError` solo existía en runtime real. Peor: el builder ORIGINAL de la story había chocado con la misma pared y la "resolvió" dropeando silenciosamente los campos en `funnel_service.create_lead` (documentados en el docstring, nunca pasados al repo).

## Aprendizaje

Es la versión **BE-interna** del patrón "contrato imaginado" FE↔BE (caso embudo 2026-06-04, HB-42): cada capa verde en aislamiento, el contrato entre capas jamás ejercido. Con DDD por capas (api→service→repo), mockear la capa N+1 en TODOS los tests de la capa N significa que **ninguna firma real se valida hasta runtime**.

`AsyncMock`/`MagicMock` sin `spec=` aceptan cualquier llamada → cambios de firma en la capa inferior son invisibles. Y `spec=` no basta para kwargs nuevos que SÍ existen: hay que ejercer el código real.

## Aplicación práctica

- **Al extender la firma de un service que delega a un repo: el ticket DEBE incluir un test que ejercite el REPO REAL** (session mockeada está OK — lo que se valida es la firma + el SQL + los params), no solo el service con repo mockeado. Patrón de referencia: `vitalia/backend/tests/modules/vitalia/crm/test_lead_repo_funnel_fields.py` (regresión RED→GREEN de este caso: assert columnas en el SQL + valores en params).
- **Smell de review**: diff que agrega kwargs a una llamada `self._repo.X(...)` sin diff correspondiente en el repo → verificar firma destino a mano (el verde no lo va a atrapar).
- **Mock con `spec=` siempre** (`AsyncMock(spec=LeadRepository)`) — atrapa al menos métodos inexistentes; los kwargs requieren `autospec`/test real.
- La doctrina ya existente aplica: el verde de suite NUNCA cierra un fix sin live-verify del write real ([[verification-real-not-200]], rule #37).

## Referencias

- Test de regresión patrón: `vitalia/backend/tests/modules/vitalia/crm/test_lead_repo_funnel_fields.py`
- Commit fix: `59894c99`
- Caso hermano FE↔BE: `vitalia/docs/learnings/2026-06-04-embudo-imagined-contract-never-integrated.md` (HB-42)
- `.claude/rules/test-design-doctrine.md` § Verificación REAL ≠ HTTP 200
