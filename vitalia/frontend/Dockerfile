# vitalia/frontend/Dockerfile
# Build context: monorepo root
# Target dev: hot-reload con bind mount
# Target final: Next.js standalone produccion
#
# S-DOCKER-DEV-MULTIBRAND T-4 — 2026-05-15
# Port: 3002 (D6 port allocation)

FROM node:20-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

# ── dev target ──
FROM base AS dev

WORKDIR /app

# Pre-instalar dependencias (package.json viene via bind mount en dev, pero pre-instalamos)
COPY .npmrc pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY patches ./patches
COPY vitalia/frontend/package.json ./vitalia/frontend/package.json
# Workspace packages @luana/* (ui-kit, hooks, format, ...): sin sus package.json el
# install --filter no ve sus deps (ej. tailwind-merge de @luana/format) → store de la
# imagen incompleto → "Module not found" en runtime (bug 2026-06-11 post-lift ui-kit 0.4.0).
COPY core/@luana ./core/@luana

RUN --mount=type=cache,id=pnpm-vitalia,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter "@luana/vitalia-web..."

WORKDIR /app/vitalia/frontend
EXPOSE 3002
# HB-78 (2026-07-11 revisit): raised back 2048→3072. 2GB caused Next's own
# memory-watchdog to self-restart mid-compile on heavier routes (dev-server
# "approaching used memory threshold, restarting..."). Safe again because the
# 3 idle brand stacks (nicolify/comunify/lupulo) that caused the original host
# OOM-kill incident are now stopped by default — freed ~3.6GB host headroom.
# If those stacks come back up concurrently, this may need to drop again.
# Sits under the 6G container limit (docker-compose.dev.yml). Rebuild to take effect.
ENV NODE_OPTIONS="--max-old-space-size=3072"
CMD ["pnpm", "dev", "--port", "3002"]

# ── builder target ──
FROM base AS builder

WORKDIR /app
COPY .npmrc pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY patches ./patches
COPY vitalia/frontend/package.json ./vitalia/frontend/package.json
# @luana/* completos (manifests + src TS): pnpm build transpila ui-kit/format desde source
COPY core/@luana ./core/@luana

RUN --mount=type=cache,id=pnpm-vitalia,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter "@luana/vitalia-web..."

COPY vitalia/frontend/ ./vitalia/frontend/

WORKDIR /app/vitalia/frontend
RUN pnpm build

# ── final target ──
FROM node:20-alpine AS final

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app/vitalia/frontend/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/vitalia/frontend/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/vitalia/frontend/public ./public 2>/dev/null || true

USER appuser
EXPOSE 3002
ENV PORT=3002
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3002/', (r) => r.statusCode < 500 ? process.exit(0) : process.exit(1))"
CMD ["node", "server.js"]
