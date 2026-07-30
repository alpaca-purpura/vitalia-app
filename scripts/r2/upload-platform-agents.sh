#!/usr/bin/env bash
# upload-platform-agents.sh
#
# Sube los 6 agentes (Lisa/Valeria/Adrián/Lucas/Camila/Mateo) al bucket
# Cloudflare R2 `luana-assets-platform/agents/`.
#
# Pre-requisitos (uno de los dos caminos):
#   Camino A — wrangler (recomendado):
#     1) npm install -g wrangler  (o usar `npx wrangler`)
#     2) wrangler login   (abre browser para auth Cloudflare)
#     3) bash scripts/r2/upload-platform-agents.sh
#
#   Camino B — rclone con R2 API token (CI-friendly):
#     1) Obtener R2 API token en dash.cloudflare.com → R2 → Manage R2 API Tokens
#     2) Configurar rclone con remote tipo "s3" provider "Cloudflare":
#          access_key_id, secret_access_key, endpoint = https://<account_id>.r2.cloudflarestorage.com
#     3) Set USE_RCLONE=1 antes de correr este script
#
# Uso:
#   bash scripts/r2/upload-platform-agents.sh             # wrangler mode
#   USE_RCLONE=1 bash scripts/r2/upload-platform-agents.sh # rclone mode
#   DRY_RUN=1 bash scripts/r2/upload-platform-agents.sh   # solo listar acciones

set -euo pipefail

BUCKET="luana-assets-platform"
SRC_DIR="${SRC_DIR:-/home/chalreme/Trabajo/Vitalia/agentes}"
DRY_RUN="${DRY_RUN:-0}"
USE_RCLONE="${USE_RCLONE:-0}"

# Mapping: <agente_slug> <thumbnail_src> <full_src>
# Nota: Adrián solo tiene Adrian-Cuadrado.png + Adrian.jpeg (no Adrian.png).
AGENTS=(
  "lisa|Lisa-Estratega/Lisa-Cuadrado.png|Lisa-Estratega/Lisa.png"
  "valeria|Valeria-Ejecutiva/Valeria-Cuadrado.png|Valeria-Ejecutiva/Valeria.png"
  "adrian|Adrian-Closer/Adrian-Cuadrado.png|Adrian-Closer/Adrian.jpeg"
  "lucas|Lucas-Setter/Lucas-Cuadrado.png|Lucas-Setter/Lucas.png"
  "camila|Camila-Fidelizacion/Camila-Cuadrado.png|Camila-Fidelizacion/Camila.png"
  "mateo|Mateo-Desarrollador/Mateo-Cuadrado.png|Mateo-Desarrollador/Mateo.png"
)

echo "==> Upload agents → R2://${BUCKET}/agents/"
echo "    SRC_DIR=${SRC_DIR}"
echo "    DRY_RUN=${DRY_RUN}"
echo "    USE_RCLONE=${USE_RCLONE}"
echo

upload_file() {
  local local_path="$1"
  local r2_key="$2"
  local content_type="$3"

  if [ "$DRY_RUN" = "1" ]; then
    echo "  [DRY] ${local_path} → ${r2_key} (${content_type})"
    return 0
  fi

  if [ "$USE_RCLONE" = "1" ]; then
    rclone copyto "${local_path}" "r2:${BUCKET}/${r2_key}" \
      --header-upload "Content-Type: ${content_type}" \
      --header-upload "Cache-Control: public, max-age=31536000, immutable"
  else
    wrangler r2 object put "${BUCKET}/${r2_key}" \
      --file="${local_path}" \
      --content-type="${content_type}" \
      --cache-control="public, max-age=31536000, immutable"
  fi
}

for entry in "${AGENTS[@]}"; do
  IFS='|' read -r slug thumb_rel full_rel <<< "$entry"

  thumb_src="${SRC_DIR}/${thumb_rel}"
  full_src="${SRC_DIR}/${full_rel}"

  if [ ! -f "$thumb_src" ]; then
    echo "  ✗ ${slug} thumbnail not found: ${thumb_src}"
    continue
  fi
  if [ ! -f "$full_src" ]; then
    echo "  ✗ ${slug} full not found: ${full_src}"
    continue
  fi

  echo "→ ${slug}"

  # Thumbnail (cuadrado 1:1)
  thumb_ext="${thumb_src##*.}"
  upload_file "$thumb_src" "agents/${slug}/thumbnail.${thumb_ext}" "image/${thumb_ext}"

  # Full (transparente)
  full_ext="${full_src##*.}"
  if [ "$full_ext" = "jpeg" ] || [ "$full_ext" = "jpg" ]; then
    ctype="image/jpeg"
  else
    ctype="image/png"
  fi
  upload_file "$full_src" "agents/${slug}/full.${full_ext}" "$ctype"

  echo
done

echo "==> Done. Verify with:"
echo "    wrangler r2 object list ${BUCKET} --prefix agents/"
echo
echo "==> Public URLs (después de configurar custom domain o R2 public bucket):"
echo "    https://assets.luana.app/agents/{slug}/thumbnail.{png,jpeg}"
echo "    https://assets.luana.app/agents/{slug}/full.{png,jpeg}"
