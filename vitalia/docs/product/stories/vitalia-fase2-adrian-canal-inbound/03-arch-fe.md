---
story_id: vitalia-fase2-adrian-canal-inbound
brand: vitalia
doc: 03-arch-fe
owner_builder: builder-frontend (workhorse)
owner_auditor: auditor-frontend (flagship)
consumes: 03-arch.md
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale
lift_gated: false   # FE brand-local, cero engine — buildable hoy
---

# 03-arch-fe — superficie FE (composer modo-instrucción)

> **Scope chico (FE small).** NO es una sub-tab nueva: **EXTIENDE el composer del inbox shipped** (cap
> `adrian-inbox`) con un modo "instrucción a Adrián". Reusa `MessageInput` legacy (effectiveMode pattern).
> Respeta `vitalia-design-system` + ADR-vitalia-004 (rationale abajo).

## Architecture Decision (ADR-vitalia-004 partial-with-rationale)
ADR-vitalia-004 norma sub-tabs **nuevas**. Esto NO crea sub-tab — extiende un componente existente del inbox
(`AdrianInboxView` → composer). Aplica las secciones relevantes (Client root, Data layer React Query, Forms
RHF/Zod si aplica, tests) pero NO §1 Routing (no hay ruta nueva) ni §8 telemetría nueva (reusa el activity
stream del inbox). Divergencia documentada y justificada.

## 1 · Composer modo-instrucción (EXTEND `features/adrian/components/inbox/composer/`)

### Comportamiento (RN-13/14/15, SC-8)
- **Un solo composer.** El modo depende del estado de Adrián (effectiveMode pattern, reusa `MessageInput` legacy):
  - `handlerMode === 'human'` (pausado) → **`direct`** → el texto se envía al lead como mensaje humano.
  - else (decide) → **`instruction`** → el texto es **instrucción a Adrián** (el lead NO la ve).
- **Label/hint claros (Opción A, Chris):** "🤖 Instrucción a Adrián · el paciente no la verá".
- **Chip "🤖 Instrucción activa: …"** editable/limpiable cuando hay una instrucción persistida (persistente, D1).
- Para escribir directo al lead en `decide`, el operador **pausa a Adrián** primero (RN-14).

### Data layer
- React Query: `useOperatorInstruction(conversationId)` (read activa) + mutation `setInstruction` →
  `POST /api/v1/adrian/conversations/{id}/instruction`. Key: `['adrian','instruction',conversationId]`.
- Zustand SOLO para UI state del composer (no server data).
- Optimistic: el chip aparece on-success; el activity stream del inbox muestra el evento NON-PHI.

### Types (`features/adrian/types/operator-instruction.ts`)
camelCase mirror de los DTOs BE (§ 03-arch.md §5). `ComposerMode = 'instruction' | 'direct'`.

## 2 · Spanish neutro + voz
- UI strings (labels/hints/chip) = español neutro LatAm (sin voseo) — el composer es UI, no output del agente.
- El **texto de la instrucción** lo escribe el operador (libre); el **output de Adrián** respeta la voz del tenant.

## 3 · PHI / seguridad
- La instrucción es **comercial NON-PHI** (RN-15). Nunca PHI clínica.
- `tenant_id` del FE via `useTenantId()` (NUNCA Clerk org). No PHI en localStorage.

## 4 · Tests
- Vitest: `use-operator-instruction.test.ts` (hook) → composer effectiveMode component test (instruction vs
  direct según handlerMode, SC-8) → store.
- Playwright: smoke del composer instrucción (extiende el spec del inbox, no ruta nueva).
- Visual: golden del composer en modo instrucción (chip + label) si aplica al design-system.
- **Regression:** los specs del composer del inbox shipped pasan SIN tocarse (excepción coordinada: el modo
  instrucción es EXTEND intencional sobre la superficie firmada — RN-14/15).
- **Live-verify (`chrome-devtools-verify`):** setear una instrucción real en dev-app → ver el chip + activity
  event + (post-lift) el siguiente reply de Adrián refleja la instrucción. CERO "GET 200".

## 5 · must_load (builder-frontend)
`vitalia-design-system` + `frontend-expert` + `playwright-expert` + `chrome-devtools-verify`. NEVER touch:
`core/`, otros brands, sub-tabs ajenas del inbox.
