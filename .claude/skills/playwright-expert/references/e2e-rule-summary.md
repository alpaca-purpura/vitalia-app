# E2E Testing — ex always-on rule body (evicted W1-Phase2 2026-06-09 — era `.claude/rules/e2e-testing.md`)

**SSoT skill: `playwright-expert`** (auto-loads on any e2e/playwright/smoke trigger). Carga el skill ANTES de tocar `{brand}/frontend/e2e/**` o `{brand}/frontend/playwright.config.ts` o el workflow E2E de CI (deferred).

Cuándo: nueva UI feature, bug fix interaction, nav/auth flow change. NO: BE-only, styling-only, utils.

**Preflight obligatorio antes correr:**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS} && bash scripts/e2e-preflight.sh
```

**Execution NATIVE Linux (host)** (NUNCA Docker — `make e2e*` puede causar OOM en Docker local).

Port allocation per brand (ver `docs/process/docker-dev-multibrand.md`):

| Brand | Frontend port | Backend port |
|---|---|---|
| nicolify | 3001 | 8001 |
| vitalia | 3002 | 8002 |
| comunify | 3003 | 8003 |
| lupulo | 3004 | 8004 |

```bash
WS=$(git rev-parse --show-toplevel)

# Per brand (ejemplo nicolify):
cd ${WS}/nicolify/frontend && E2E_BASE_URL=http://localhost:3001 npx playwright test --project=smoke

# Vitalia:
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke

# npm scripts (asumen port correcto en config per brand):
cd ${WS}/{brand}/frontend && npm run test:e2e:smoke
# auth roto / siempre falla:
cd ${WS}/{brand}/frontend && npm run test:e2e:fresh
```

**Prohibido:** `make e2e`/`make e2e-smoke` (Docker, crashea). Spawn webServer dentro Playwright (siempre `E2E_BASE_URL`). Importar `test` de `@playwright/test` directo en specs autenticados (usar `auth.fixture`). Locators CSS/XPath. `test.skip` permanente. Editar `playwright/.clerk/user.json` manualmente.

## Multibrand awareness (post reorg 2026-05-15)

- Cada brand tiene su propia `{brand}/frontend/e2e/` suite + `playwright.config.ts`.
- Storage state Clerk: `{brand}/frontend/playwright/.clerk/user.json` per brand (no compartido).
- `make dev-{brand}` o `make dev-all` levanta el stack target antes del E2E (preflight verifica).
