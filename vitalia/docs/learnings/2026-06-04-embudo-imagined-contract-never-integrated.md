---
brand: vitalia
date: 2026-06-04
slug: embudo-imagined-contract-never-integrated
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
target_core_package: n/a (process — gate FE↔BE contract test)
---

# El "6/8 done GREEN" que nunca tocó el backend real (contrato imaginado FE↔BE)

**Qué aprendimos:** una story (vitalia-fase2-adrian-embudo) llegó a "6/8 tickets done, todos los gates GREEN" y **estaba rota en TODAS sus pantallas contra el backend real**. La live-verify (DoD #37) lo destapó: el board crasheaba (`buyingSignals.slice` sobre `undefined` → burbuja de Next) y el resto mis-bindeaba en silencio.

**Causa raíz (NO fue un typo — fue estructural):** el `/architect` escribió en `03-arch` un **contrato FE↔BE imaginado**:
- camelCase en el FE vs snake_case real de los DTOs BE de `crm` (sin alias camel).
- campos que el BE **nunca manda** (ej. el FE esperaba `lastActivityDescription` + `lastActivityAt`, el BE manda un solo `last_activity`).

Los builders FE construyeron contra ese contrato imaginado; los builders BE contra los DTOs reales. **Cada lado tenía sus tests verdes — pero los tests nunca se cruzaron:** component tests con fixtures camelCase + BE unit tests snake. Ninguno de los 8 hooks de fetch transformaba; todos casteaban el JSON snake crudo como tipo camel. El "BE live-smoke: 6 endpoints reachable" de la corrida previa era `GET /board → 422 sin header` — **reachable ≠ renderizar**.

**Origen:** story `vitalia-fase2-adrian-embudo`, 2da sesión de cierre 2026-06-04.

**Why:** "tests verdes" mide cada lado en aislamiento. El contrato es lo único que vive ENTRE los lados, y nada lo verificaba. Es el mismo patrón que el caso lisa-marca (e2e que mockea el backend del surface bajo prueba = falso verde) elevado un nivel: acá ni siquiera había un contrato real, había uno **inventado en el diseño**.

**How to apply:**
1. **Gate faltante = contract-test FE↔BE** (capturado como **HB-42**): un test que tome la respuesta REAL del endpoint (o su OpenAPI) y valide que matchea el tipo/zod del FE. Sin esto, el drift snake↔camel + campos-inventados queda invisible hasta la live-verify.
2. **El `/architect` debe anclar el contrato al DTO BE REAL**, no describir uno deseado. Si el FE necesita un campo que el BE no expone → es un ticket BE explícito (extender el DTO), no un supuesto.
3. **La DoD live-verify (#37) es la red que lo cazó** — reforzar: ninguna story user-reachable es `done` sin ejercerla contra el stack real (no `GET 200`, no mock del propio backend).
4. **Fix pattern (cuando aparece):** camelización en el borde FE (`keysToCamel` en cada hook), consistente con la convención inbox/lucas "snake API → camel view-model"; NO tocar `fetchClient` global; gaps estructurales (1 campo BE → N campos FE) se mapean explícito o el componente se hace resiliente.

**Ver también:** `verification-real-not-200`, caso lisa-marca, `.claude/rules/definition-of-done-live-verify.md`, `docs/process/harness-backlog.md` HB-42, handoff `vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/HANDOFF-next-session.md`.
