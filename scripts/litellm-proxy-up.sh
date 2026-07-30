#!/usr/bin/env bash
# litellm-proxy-up.sh — idempotent: bring up the shared dev LLM gateway.
#
# Cross-brand: ONE LiteLLM proxy on luana_dev_net serves every brand backend
# (each brand's LITELLM_BASE_URL points here). Cognitive-load routing = the
# engine's ModelRole abstraction; this proxy maps friendly model_name → provider.
#
# Chinese-first policy (DeepSeek V4 Flash + Kimi K2; OpenAI = exception).
# Config:  deploy/litellm/config.dev.yaml   (tracked, no secrets)
# Keys:    deploy/litellm/.env              (gitignored: DEEPSEEK/MOONSHOT/OPENAI/MASTER)
#
# Reversible: `docker rm -f luana_litellm_dev`.
# NOTE (deferred, /pm-luana): fold this into root docker-compose.dev.yml as a
# first-class shared service. Standalone script today keeps the close in-lane.
set -euo pipefail

WS="$(git rev-parse --show-toplevel)"
NAME="luana_litellm_dev"
NET="luana_dev_net"
IMAGE="${LITELLM_IMAGE:-ghcr.io/berriai/litellm:main-stable}"
CONFIG="${WS}/deploy/litellm/config.dev.yaml"
ENVFILE="${WS}/deploy/litellm/.env"

[ -f "$CONFIG" ]  || { echo "✗ missing $CONFIG"; exit 1; }
[ -f "$ENVFILE" ] || { echo "✗ missing $ENVFILE (provider keys — gitignored). Create from deploy/litellm/.env.example"; exit 1; }

# Ensure the shared network exists (created by make dev-{brand} normally).
docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET" >/dev/null

# Idempotent: remove a prior instance, then (re)create.
docker rm -f "$NAME" >/dev/null 2>&1 || true

docker run -d \
  --name "$NAME" \
  --network "$NET" \
  --network-alias "$NAME" \
  --network-alias "visionarias_litellm" \
  --env-file "$ENVFILE" \
  -v "${CONFIG}:/app/config.yaml:ro" \
  -p 4000:4000 \
  "$IMAGE" \
  --config /app/config.yaml --port 4000 >/dev/null

echo "→ litellm proxy '${NAME}' starting on ${NET}:4000 (image ${IMAGE})"

# Readiness gate (proxy boots in a few seconds).
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:4000/health/liveliness" >/dev/null 2>&1 \
     || curl -fsS "http://127.0.0.1:4000/health/liveness" >/dev/null 2>&1; then
    echo "✓ litellm proxy live at http://127.0.0.1:4000 (alias luana_litellm_dev / visionarias_litellm on ${NET})"
    exit 0
  fi
  sleep 1
done
echo "✗ proxy did not become live in 30s — check: docker logs ${NAME}"
exit 1
