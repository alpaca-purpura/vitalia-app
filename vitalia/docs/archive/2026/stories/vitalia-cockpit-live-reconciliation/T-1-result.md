# T-1-result — Fase 0 boot fix (remount core/)

**Estado:** pushed · **Owner:** orchestrator-direct (infra ops, per delegation matrix) · **Iter:** 1

## Diff resumen
- `vitalia/docker-compose.dev.yml` — servicio `vitalia_frontend_dev`: agregado `./core:/app/core:rw` + anonymous volume `/app/core/node_modules`. Causa raíz: el container nunca montó `core/`, así el linking pnpm de `@luana/*` quedaba stale al bump de versión (`@luana/hooks@0.2.0` → export `use-store-hydration` → 500 en `:3002`).

## Ops aplicadas
- `docker compose -f docker-compose.dev.yml -f vitalia/docker-compose.dev.yml up -d --no-deps vitalia_frontend_dev` (recreate con mount)
- `docker exec ... pnpm install --prefer-offline` (37.9s, resuelve workspace; warnings peer next-themes/react19 pre-existentes benignos)
- `docker restart vitalia_frontend_dev` (limpiar cache módulos)

## Gates (04-validators.yaml acceptance: boot_frontend_200, boot_no_module_not_found, boot_valeria_chat_happy, fe_typecheck)
| Gate | Resultado |
|---|---|
| boot_frontend_200 (`curl :3002/sign-in`) | ✅ 200 |
| `/` raíz (daba 500) | ✅ 307 → /sign-in (redirect Clerk correcto) |
| boot_no_module_not_found (logs) | ✅ 0 ocurrencias |
| boot_valeria_chat_happy (Playwright) | ✅ 9/9 passed (17.9s) — shell-organism renderiza (ChatHeader, bubbles, TypingIndicator, DelegateMarker, Composer) |
| Next.js | ✅ Ready in 415ms |

## Resultado
El 500 que veía Chris al entrar está resuelto en causa raíz. La app bootea y el shell-organism (topbar + ribbon + Valeria) renderiza. Fix de infra persistente (futuros bumps de `@luana/*` solo requieren `pnpm install` en container, no rompen el boot).

## Skills consulted (must_load enforcement v4.1)
| Skill / Rule | Status | When |
|---|---|---|
| playwright-expert | ✅ | gate valeria-chat-happy (NATIVE Linux, no make e2e Docker) |
| .claude/rules/debugging.md | ✅ | diagnóstico container layout + naming convention |
| .claude/rules/git-haiku-delegation.md | ✅ | commit por pathspec (hub índice compartido) |

done -> T-1-result.md
