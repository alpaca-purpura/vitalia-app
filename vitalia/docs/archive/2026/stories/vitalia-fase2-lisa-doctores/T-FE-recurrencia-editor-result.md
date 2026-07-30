# T-FE-recurrencia-editor — result (consolidado por orchestrator)

**Estado:** DONE (commits `333c5771` UI + `fe7e0b52` fix e2e + `e966926a` patch BE create-request). El builder agotó contexto tras commitear y ANTES de escribir este result — lo consolida el orchestrator con verificación propia.

## Hallazgo cross-ticket del builder (valioso)
`RecurrentBlockCreateRequest` BE solo había extendido el DTO de RESPUESTA — create seguía exigiendo `day_of_week`/`freq` y no aceptaba `{daysOfWeek, interval}`. **5ª instancia del patrón contrato-imaginado FE↔BE en esta story.** Resuelto por patch quirúrgico `e966926a` (request DTOs opcionales legacy + validación una-forma + plumbing; tests 398/398).

## Live-verify (orchestrator, localhost:3002 autenticado, real backend, 2026-06-12)
- action: drag-create lunes 10:00 → popover → Repetir=Personalizado… → interval=2 → chips L+J → Termina=Después de 8 repeticiones
- observed: resumen humano EXACTO "Se repite cada 2 semanas el lunes y jueves, 8 veces" (RN-D3F-1 ✓) → Guardar → bloque pinta en semana + chips en vista Mes → eliminar → 0 bloques restantes
- backend_log: POST /availability-blocks **201** (payload daysOfWeek/interval aceptado) · GET availability-occurrences 200 ×N · 0 console/page errors
- nota conteo: probe sin filtro por blockId mezcló bloques seed pre-existentes del doctor demo; la exactitud de counts la cubren la batería BE SC-D3C/D3F (GREEN aislada) + e2e SC-D3C-1.

## Gates (del builder, pre-muerte + patch)
vitest horarios + e2e SC-D3F-5 (chips teclado — fix `fe7e0b52`) GREEN · tsc/eslint GREEN · suite clinics post-patch 398/398 + arch 339/339.
