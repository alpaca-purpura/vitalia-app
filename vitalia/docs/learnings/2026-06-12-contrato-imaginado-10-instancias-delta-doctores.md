---
brand: vitalia
date: 2026-06-12
slug: contrato-imaginado-10-instancias-delta-doctores
promotable: yes
applies_to_other_brands_potentially: [nicolify, comunify, lupulo]
target_core_package: harness (HB-42 contract-test gate)
---

# 10 instancias del patrón contrato-imaginado FE↔BE en UN delta

**Qué aprendimos:** en el delta v3 de lisa-doctores (12 tickets, builders verdes en aislamiento), la integración live destapó **10 contratos imaginados**: URL proxy upload fantasma (rota desde mayo — avatar nunca subió), FK engine a tabla inexistente (latente porque la ruta jamás se ejerció), tabla assets sin migración, DTOs sin camel (×2 rondas), profileState sin poblar, página SSR con env+path+shape inventados (×3), endpoint del editor inexistente (404 live), shapes ricos nunca diseñados, items null vs str. **Cada test unitario estaba verde.** Solo el ejercicio live + el gate anti-burbuja (base.ts) los cazaron.

**Origen:** story vitalia-fase2-lisa-doctores delta v3 · HB-42 (5ª..10ª instancia) + HB-71.

**Why:** el builder de un lado LEE el resultado del otro como doc, no como contrato ejecutable. La suite verde por-lado es una burbuja.

**How to apply:** (1) HB-42 = prioridad 1: contract-test generado del OpenAPI BE que el FE consume en CI (schemathesis FE-side o typegen + assert). (2) Mientras tanto: todo prompt de builder FE exige "curl el endpoint REAL antes de tipear el hook" (funcionó cuando se siguió). (3) El e2e que mockea el surface bajo prueba NO cuenta como cobertura del contrato (W5).
