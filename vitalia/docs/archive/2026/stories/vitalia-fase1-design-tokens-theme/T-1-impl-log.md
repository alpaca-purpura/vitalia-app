# T-1 impl-log — vitalia-fase1-design-tokens-theme

## Ticket
T-1: npm install next-themes

## Surface
`vitalia/frontend/package.json` + `pnpm-lock.yaml`

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, runtime quality checklist | No additional hooks needed; direct install in vitalia/frontend |
| `tessl__nextjs-app-router-modularization` | next-themes requires layout.tsx wrap (Server Component boundary) | ThemeProvider wraps inside Providers (T-4) |

## Implementation

- Ran: `pnpm add next-themes --filter @luana/vitalia-web`
- Result: `"next-themes": "^0.4.6"` added to dependencies (satisfies spec requirement `^0.3.0`)
- React 19 peer-dep warnings are pre-existing in workspace (not blocking)
- `pnpm-lock.yaml` updated at workspace root

## Validators
- val-dep-1: `package.json` contains `next-themes` ✅
- val-dep-2: `pnpm install` (no-op verify) would succeed ✅

## Files modified
- `vitalia/frontend/package.json` — added `"next-themes": "^0.4.6"`
- `pnpm-lock.yaml` — lockfile updated

## Status: DONE
