#!/usr/bin/env bash
# Build completo: UI estática + binario.
set -euo pipefail
cd "$(dirname "$0")"
./build-ui.sh
# Versión del kit (core-harness/VERSION · línea KIT_VERSION=x.y.z) → main.version
KIT_VERSION="$(grep -E '^KIT_VERSION=' ../../../core-harness/VERSION 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)"
go build -ldflags="-s -w -X main.version=${KIT_VERSION:-dev}" -o cockpit .
echo "✓ $(ls -lh cockpit | awk '{print $5}') → ./cockpit"
