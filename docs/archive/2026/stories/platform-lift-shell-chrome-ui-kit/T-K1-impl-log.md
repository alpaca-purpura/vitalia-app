# T-K1 — Kit scaffolding · impl-log

**Ticket:** T-K1 (organism/shell sub-dir + deps + store factory + tipos genéricos + routing helpers)
**Story:** platform-lift-shell-chrome-ui-kit · brand: platform
**Scope autorizado:** `core/@luana/ui-kit/**` (package TS — NO es luana-core-* Python).
**Prohibido T-K1:** `vitalia/frontend/**`, `nicolify/frontend/**`, `core/luana-core-*/src/**`, cualquier backend.
**Phase output (R30):** `tests-passing` ONLY. NO audit verdict.

---

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada (cita) |
|---|---|---|
| `frontend-expert` | `must_load_skills` del ticket Kit T-K = `frontend-expert`. Construcción de package TS `@luana/ui-kit` (organism layer nuevo). | Patrón store SSR-safe → **CONSUMIR** `createSsrSafePersistedStore` de `@luana/hooks` (NO recrear · RN-8 · `anti-duplication.md` inventario engine). Factory re-parametrizable (`storageKey`/`version`/`migrate`) sin acoplar a brand. No-default-exports (barrel). Vitest jsdom + globals (config kit existente). |
| `anti-duplication.md` (rule) | `must_load_skills` Kit T-K. El lift mata el mirror cross-brand vitalia↔nicolify. | `createSsrSafePersistedStore` ya vive en `@luana/hooks/create-ssr-safe-persisted-store` → import, NUNCA mirror. El store factory es la abstracción shared que reemplaza los 2 `shell-store.ts` de marca. Naming genérico (`supervisor`/`split`) — cero token de marca en lógica. |
| checkpoint § Aprendizajes (8 obligatorios) | `must_load_skills` Kit T-K. | Aplicados: RN-2 (naming genérico `supervisorOpen`/`splitPct`/`SupervisorOpen`) · RN-8 (consumir SSR-safe store de hooks) · SC-6 (storageKey por argumento, conservación e2e en marca) · Decisión D (NO re-exportar `Group`/`Panel`/`Separator` de react-resizable-panels — colisión con el `Group` form del kit; si un handle debe ser público → `ShellResizeHandle`, pero NO en T-K1) · SEMVER 0.3.0→0.4.0 minor (capa organism aditiva). |

---

## § Plan (technical_design · TDD RED→GREEN)

**Deliverables T-K1:**
1. `package.json` — deps `react-resizable-panels` (`^4.11.1` exacto vitalia) + `zustand` (`^5.0.5` exacto vitalia); bump `0.3.0→0.4.0`.
2. `src/organism/shell/types.ts` — tipos genéricos VERBATIM 03-arch § API contract. Cero `valeria`/`vitalia`/`nicolify` en lógica.
3. `src/organism/shell/create-shell-store.ts` — factory `createShellStore({ storageKey, version?, migrate? })`, port de vitalia `shell-store.ts` re-parametrizado (`valeriaOpen→supervisorOpen`, `valeriaPct→splitPct`), CONSUME `@luana/hooks/create-ssr-safe-persisted-store`. Conserva sanitize + no-clobber hydration.
4. `src/organism/shell/routing.ts` — `extractAgentFromPath`/`extractSubtabFromPath`/`isValidAgent`/`isValidSubtab` genéricos (catálogo/slug-set por argumento).
5. Vitest RED-first: `src/organism/shell/__tests__/create-shell-store.test.ts` (máquina A/B/C + migrate legacy genérico + no-clobber hydration) + `src/organism/shell/__tests__/routing.test.ts`.

**Orden TDD (RED→GREEN):**
1. **RED** — escribir `create-shell-store.test.ts` + `routing.test.ts` (importan módulos que aún no existen → fallan).
2. **GREEN** — `types.ts` → `create-shell-store.ts` → `routing.ts`.
3. `package.json` (deps + bump) + `CHANGELOG.md` (0.4.0).
4. `pnpm install` (materializa deps en kit) → `pnpm --filter @luana/ui-kit typecheck && test`.
5. Grep gate brand-token = 0.
6. Commit incremental por pathspec (`SCOPE_GATE_SKIP=1`), push wip/vitalia.

**Máquina de estados (port de vitalia, naming genérico):**
- A=closed: `supervisorOpen: "closed"` ⇒ fuerza `historyOpen: false` (RN-5).
- B=chat: `supervisorOpen: "chat"`, sin restaurar historia (RN-6 collapse / RN-7 openHistory abre chat+history).
- C=chat+historyOpen: `supervisorOpen: "chat"` + `historyOpen: true`.
- `splitPct: null` = default (30 lo decide la marca/layout T-K2; el factory persiste null/number).
- Hydration: `historyOpen` SIEMPRE `false` post-merge (no-clobber, no se persiste · SC-6).
- Migrate legacy: v0 `collapsed→closed`, `rail`/`full`→`chat` (sin restaurar history), unknown→fallback `chat` + warn.

**Aprendizajes aplicados:** RN-2 · RN-8 · SC-6 · Decisión D · SEMVER.
