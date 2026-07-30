---
title: "docker-compose: environment con \"${VAR}\" pisa env_file con string vacío"
date: 2026-06-11
type: technical
brands_affected: [vitalia, nicolify, comunify, lupulo]
origen: "incidente 2026-06-11 — VITALIA_PHI_KEK vacío → 500 en endpoints PHI (board)"
ratified_by: chris
promotable: yes
tags: [docker-compose, env-file, environment, secrets, kek, precedence]
---

# docker-compose: `environment:` con `"${VAR}"` pisa `env_file` con string vacío

## Contexto

El commit `e67c67a1` (T-2 pgcrypto KEK wiring) agregó al compose de vitalia:

```yaml
env_file:
  - path: vitalia/.env.dev      # ← tiene VITALIA_PHI_KEK=<64-hex real>
environment:
  VITALIA_PHI_KEK: "${VITALIA_PHI_KEK}"   # ← BUG
```

Resultado: el backend SIEMPRE recibía `VITALIA_PHI_KEK=""` (len=0) → `KEKConfigurationError` → 500 en todo endpoint PHI (board CRM), salvo que alguien exportara la var en el shell antes de `docker compose up`.

## Aprendizaje

Dos reglas de compose que combinadas producen el bug silencioso:

1. **Precedencia**: `environment:` SIEMPRE gana sobre `env_file` para la misma key.
2. **Interpolación**: `"${VAR}"` en el YAML se resuelve desde el **shell del que corre compose** (o el `.env` del project dir) — NUNCA desde el `env_file` del servicio. Var no exportada → string vacío + warning ("variable is not set. Defaulting to a blank string") que se pierde en el ruido del build.

El patrón `KEY: "${KEY}"` con la MISMA key presente en `env_file` es **siempre un bug**: en el mejor caso es redundante (shell exportado), en el caso real deja la var vacía.

## Aplicación práctica

- Si la var vive en `env_file` → **NO redeclararla** en `environment:`. Borrar la línea es el fix (commit `8ce72b0e`).
- `environment:` es para valores literales del servicio (puertos, hosts de la red compose) — no para secrets que ya inyecta `env_file`.
- Verificación exprés: `docker exec {svc} bash -c 'echo ${#VAR}'` → len=0 = pisada.
- Red flag en review: cualquier `X: "${X}"` en un compose con `env_file` configurado.
- Scan 2026-06-11: vitalia (fixeado) era la única brand con el patrón; nicolify/comunify/lupulo limpias.

## Referencias

- Commit fix: `8ce72b0e` · commit que introdujo el bug: `e67c67a1`
- Docs compose: environment > env_file precedence + variable interpolation
