# T-7 Result — Playwright POM + fixtures (tests-only)

**Story:** F1-S6 vitalia-fase1-valeria-chat-skeleton
**Ticket:** T-7
**State:** pushed
**production_code:** false (tests/POM/fixtures only)

## Files

### NEW
- `vitalia/frontend/e2e/shell-organism/poms/valeria-chat-page.pom.ts` — ValeriaChatPage class, 16 métodos
- `vitalia/frontend/e2e/shell-organism/fixtures/chat-store-seed.fixture.ts` — chatPage + chatStoreSeed + chatStoreEmpty fixtures

### MODIFY
- `vitalia/frontend/src/stores/chat-store.ts` — expose `window.__chatStore__` (non-prod only) + read `window.__chatStoreSeed__` on init (non-prod only)

## Skills Consulted

| Skill | Invocada | Decisión tomada |
|---|---|---|
| `playwright-expert` | Patrón POM + addInitScript (PRIORITY — E2E scope) | `addInitScript` DEBE llamarse ANTES de `page.goto()` para que el script inyecte antes de que los módulos JS de la página ejecuten; locators via `data-testid` first, ARIA como fallback; no assertions en POM methods |
| `frontend-expert` | FSD-Lite boundaries, store exposure pattern | Store exposure en `chat-store.ts` wrapped en `NODE_ENV !== 'production' && typeof window !== 'undefined'` — doble guard: prod safety + SSR safety |
| `tessl__react-patterns` | No aplica directo (tests-only) | N/A — T-7 es tests/POM, no componentes React |
| `tdd-mandatory` | RED antes GREEN | POM + fixtures creados para que T-8 specs puedan arrancar en RED antes de no tener implementación adicional |
| `e2e-testing` | Preflight obligatorio, native Linux (host), NUNCA `make e2e*` | Validators corridos nativos: `npx tsc`, `npx eslint`, `npx prettier` — NUNCA `make e2e*` |
| `anti-duplication` | Verificar cross-brand mirror | POM brand-local vitalia; `downstream-regression-na: brand-local E2E POM; no cross-brand consumers` |

## Key Decisions

### 1. `window.__chatStoreSeed__` pattern
- POM `seedChatStore(messages)` usa `page.addInitScript` para setear `window.__chatStoreSeed__` ANTES de navegar
- `chat-store.ts` lee ese array en `resolveInitialMessages()` al inicializar el store (NODE_ENV guard)
- Garantiza que el store se hidrate con los mensajes de test ANTES de que React monte el componente
- Fallback: si `window.__chatStoreSeed__` no está presente → `MOCK_MESSAGES` (comportamiento dev normal)

### 2. `window.__chatStore__` exposure
- Expuesto en `window.__chatStore__` (doble underscore = convención test hook)
- Guard: `process.env.NODE_ENV !== 'production' && typeof window !== 'undefined'`
- Usado por POM para `getActiveAgent()`, `clearMessages()`, `waitForStatus()`
- Alternativa descartada: `window.useChatStore` (03-arch sugería eso) — cambiado a `__chatStore__` per convención estándar de test hooks

### 3. Fixture sin auth.fixture base
- La ruta `/test-stack/shell-layout` es pública (no Clerk auth requerida)
- Fixtures extienden `base` de Playwright directo, no `auth.fixture`
- Si specs futuras (T-8/T-9) necesitan auth, componer explícitamente

### 4. MOCK_MESSAGES import en fixture
- Import desde `../../../src/components/shared/shell-organism/_mock-messages` (path relativo, no `@/`)
- El alias `@/` es src-relative y no funciona en `e2e/` context (fuera de `src/`)
- El cast `as unknown as ChatMessage[]` es necesario porque MOCK_MESSAGES es `readonly` y el type de `seedChatStore` acepta `ChatMessage[]` mutable

## Validators Run (G5 gate T-7)

| Validator | Comando | Resultado |
|---|---|---|
| val-fe-tsc | `npx tsc --noEmit` | ✅ 0 errores |
| val-fe-lint | `npx eslint e2e/shell-organism/ src/stores/chat-store.ts --cache` | ✅ 0 errores, 0 warnings |
| val-fe-prettier | `npx prettier --check e2e/shell-organism/ src/stores/chat-store.ts` | ✅ All matched files use Prettier code style! |

## POM Methods Coverage

Todos los métodos requeridos por `04-validators.yaml § poms_required[0].methods` implementados:

| Método | Implementado | Notas |
|---|---|---|
| `goto()` | ✅ | Seed shell localStorage (agentic/full) + navega `/test-stack/shell-layout` + wait visible |
| `seedChatStore(messages)` | ✅ | addInitScript ANTES de goto() |
| `seedChatStoreEmpty()` | ✅ | Convenience: seedChatStore([]) |
| `getMessage(index)` | ✅ | nth msg-bubble Locator |
| `getDelegateMarker()` | ✅ | [data-testid=msg-delegate] |
| `getThinkingIndicator()` | ✅ | [data-testid=msg-thinking] |
| `getChatHeader()` | ✅ | [data-testid=chat-header] |
| `getModePill()` | ✅ | [data-testid=chat-mode-pill] |
| `getComposer()` | ✅ | [data-testid=composer-input] |
| `getSendButton()` | ✅ | [data-testid=composer-send] |
| `sendMessage(text)` | ✅ | fill + Enter + wait new bubble |
| `getActiveAgent()` | ✅ | page.evaluate window.__chatStore__ |
| `clearMessages()` | ✅ | page.evaluate store.clearMessages() |
| `getEmptyState()` | ✅ | getByText "Empieza una conversación" |
| `setViewport(w, h)` | ✅ | page.setViewportSize |
| `setTheme(theme)` | ✅ | localStorage + dark class toggle + StorageEvent dispatch |

## Gherkin Coverage

- ✅ `ValeriaChatPage exposes goto/seedChatStore/.../setTheme` — class implementada con todos los métodos
- ✅ `chatStoreSeed uses page.addInitScript window.__chatStoreSeed__ MOCK_MESSAGES` — fixture implementada
- ✅ `chatStoreEmpty sets window.__chatStoreSeed__ = []` — fixture implementada

## Nota: T-7 Scope (production_code: false)

La modificación de `chat-store.ts` está INCLUIDA en T-7 scope per decisión documentada en el ticket:
> "window expose wrapped en NODE_ENV guard" — es parte del work de habilitar los fixtures E2E

La modificación NO agrega footprint en producción (guards dobles: NODE_ENV + typeof window).

## Next: T-8

T-8 puede arrancar inmediatamente: specs comportamentales (happy, send, keys, xss) usando
`chatStoreSeed` y `chatStoreEmpty` del fixture. Wave 6 en el DAG.
