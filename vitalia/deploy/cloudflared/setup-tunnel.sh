#!/usr/bin/env bash
# vitalia/deploy/cloudflared/setup-tunnel.sh
#
# Cloudflare Tunnel setup script for Vitalia.
# This script prepares cloudflared in-cluster as a K8s Deployment.
#
# IMPORTANT — Chris UI gate Q4=B:
#   Steps 1 and 2 require Cloudflare authentication and create irreversible resources.
#   Run from a machine authenticated via: cloudflared tunnel login
#
# Prerequisites:
#   - cloudflared CLI installed (https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)
#   - kubectl configured pointing to the vitalia K8s cluster
#   - Cloudflare account with DNS zone for vitalia.health
#   - Namespace vitalia created: kubectl create namespace vitalia
#
# Arch ref: 03-arch.md § 5.3 · T-deploy-1
# voseo-allowed: this is a shell script with technical comments — not user-facing UI copy.

set -euo pipefail

TUNNEL_NAME="vitalia-tunnel"
NAMESPACE="vitalia"
CF_CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Vitalia Cloudflare Tunnel setup ==="
echo "Namespace: ${NAMESPACE}"
echo "Tunnel name: ${TUNNEL_NAME}"
echo ""

# ── Step 1: Create the tunnel (Chris: run once, then commit the TUNNEL_ID) ──
echo "[Step 1] Create Cloudflare Tunnel..."
echo "  Run: cloudflared tunnel create ${TUNNEL_NAME}"
echo "  Output includes TUNNEL_ID — copy it into config.yml <TUNNEL_ID> placeholder."
echo "  Then re-run this script to continue with Step 2+."
echo ""

# Abort if TUNNEL_ID placeholder not filled
if grep -q "<TUNNEL_ID>" "${CF_CONFIG_DIR}/config.yml"; then
  echo "ERROR: config.yml still has <TUNNEL_ID> placeholder."
  echo "  1. Run: cloudflared tunnel create ${TUNNEL_NAME}"
  echo "  2. Copy the UUID from the output into config.yml"
  echo "  3. Re-run this script."
  exit 1
fi

TUNNEL_ID=$(grep "^tunnel:" "${CF_CONFIG_DIR}/config.yml" | awk '{print $2}')
echo "  Tunnel ID from config.yml: ${TUNNEL_ID}"

# ── Step 2: Route DNS (Chris executes via Cloudflare dashboard OR CLI) ──────
echo ""
echo "[Step 2] Route DNS records to tunnel..."
echo "  Option A — CLI (requires cloudflared login):"
echo "    cloudflared tunnel route dns ${TUNNEL_NAME} app.vitalia.health"
echo "    cloudflared tunnel route dns ${TUNNEL_NAME} cdn.vitalia.health"
echo "  Option B — Cloudflare dashboard (see DNS-RECORDS.md)"
echo ""

# ── Step 3: Create K8s Secret with tunnel credentials ───────────────────────
echo "[Step 3] Create K8s Secret for tunnel credentials..."
CREDENTIALS_FILE="${HOME}/.cloudflared/${TUNNEL_ID}.json"

if [ ! -f "${CREDENTIALS_FILE}" ]; then
  echo "ERROR: Credentials file not found: ${CREDENTIALS_FILE}"
  echo "  Run: cloudflared tunnel create ${TUNNEL_NAME}  (generates credentials)"
  exit 1
fi

kubectl create secret generic cloudflared-credentials \
  --from-file=credentials.json="${CREDENTIALS_FILE}" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "  Secret cloudflared-credentials created in namespace ${NAMESPACE}"

# ── Step 4: Apply cloudflared ConfigMap ─────────────────────────────────────
echo ""
echo "[Step 4] Apply cloudflared ConfigMap from config.yml..."
kubectl create configmap cloudflared-config \
  --from-file=config.yml="${CF_CONFIG_DIR}/config.yml" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "  ConfigMap cloudflared-config applied."

# ── Step 5: Deploy cloudflared as K8s Deployment ────────────────────────────
echo ""
echo "[Step 5] Apply cloudflared Deployment..."

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudflared
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: cloudflared
    app.kubernetes.io/component: tunnel
    app.kubernetes.io/part-of: luana-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cloudflared
  template:
    metadata:
      labels:
        app: cloudflared
        app.kubernetes.io/name: cloudflared
    spec:
      containers:
        - name: cloudflared
          image: cloudflare/cloudflared:latest
          args:
            - tunnel
            - --config
            - /etc/cloudflared/config.yml
            - run
          volumeMounts:
            - name: config
              mountPath: /etc/cloudflared/config.yml
              subPath: config.yml
              readOnly: true
            - name: credentials
              mountPath: /etc/cloudflared/credentials.json
              subPath: credentials.json
              readOnly: true
          resources:
            requests:
              memory: "64Mi"
              cpu: "10m"
            limits:
              memory: "128Mi"
              cpu: "100m"
          livenessProbe:
            httpGet:
              path: /ready
              port: 2000
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: config
          configMap:
            name: cloudflared-config
        - name: credentials
          secret:
            secretName: cloudflared-credentials
EOF

echo "  cloudflared Deployment applied."
echo ""
echo "=== Setup complete ==="
echo "  Verify tunnel status: cloudflared tunnel info ${TUNNEL_NAME}"
echo "  Watch pods:           kubectl get pods -n ${NAMESPACE} -w"
echo "  Test connectivity:    curl -I https://app.vitalia.health/health"
