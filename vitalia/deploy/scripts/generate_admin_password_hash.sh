#!/usr/bin/env bash
# vitalia/deploy/scripts/generate_admin_password_hash.sh
# Genera el hash bcrypt de VITALIA_ADMIN_PASSWORD para el K8s secret.
#
# Uso:
#   VITALIA_ADMIN_PASSWORD='mi_password_seguro' bash vitalia/deploy/scripts/generate_admin_password_hash.sh
#
# O interactivo (solicita password sin eco):
#   bash vitalia/deploy/scripts/generate_admin_password_hash.sh
#
# Output: imprime el hash bcrypt en stdout.
# Pegar el hash en:
#   - vitalia/deploy/k8s/secrets.template.yaml: VITALIA_ADMIN_PASSWORD_HASH
#   - vitalia/.env.dev.template: VITALIA_ADMIN_PASSWORD_HASH (para dev local)
#
# Cost factor: 12 (balance seguridad / velocidad de verificacion en Streamlit).
# Requiere: Python 3.12+ con passlib[bcrypt] instalado en el venv del workspace.
#
# Arch ref: vitalia-auth-base-functional T-5 D8 — single password env-var (bcrypt)

set -euo pipefail

# ── Detectar Python con passlib disponible ────────────────────────────────────
WS_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
PYTHON="${WS_ROOT}/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    # Fallback a python3 del sistema
    PYTHON="python3"
fi

# Verificar que passlib esta disponible
if ! "$PYTHON" -c "import passlib.hash" 2>/dev/null; then
    echo "ERROR: passlib no encontrado." >&2
    echo "Instalar con: pip install passlib[bcrypt]" >&2
    echo "O desde el workspace root: uv sync" >&2
    exit 1
fi

# ── Obtener password ──────────────────────────────────────────────────────────
if [ -n "${VITALIA_ADMIN_PASSWORD:-}" ]; then
    PASSWORD="$VITALIA_ADMIN_PASSWORD"
else
    # Solicitar password interactivo sin eco
    read -r -s -p "Ingresa el password del admin Vitalia: " PASSWORD
    echo ""
    read -r -s -p "Confirmar password: " PASSWORD_CONFIRM
    echo ""

    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
        echo "ERROR: Los passwords no coinciden." >&2
        exit 1
    fi
fi

if [ -z "$PASSWORD" ]; then
    echo "ERROR: El password no puede estar vacio." >&2
    exit 1
fi

# ── Generar hash bcrypt ───────────────────────────────────────────────────────
HASH=$("$PYTHON" -c "
from passlib.hash import bcrypt
# Cost factor 12: balance seguridad/velocidad (D8 ratified)
h = bcrypt.using(rounds=12).hash('${PASSWORD}')
print(h)
")

echo ""
echo "Hash bcrypt generado (cost=12):"
echo "$HASH"
echo ""
echo "Pasos siguientes:"
echo "1. Copiar el hash de arriba."
echo "2. Pegar en vitalia/deploy/k8s/secrets.template.yaml:"
echo "   VITALIA_ADMIN_PASSWORD_HASH: '\$2b\$12\$...'"
echo "3. Aplicar al cluster:"
echo "   export VITALIA_ADMIN_PASSWORD_HASH='$HASH'"
echo "   envsubst < vitalia/deploy/k8s/secrets.template.yaml | kubectl apply -f -"
echo ""
echo "Para dev local (.env.dev):"
echo "   VITALIA_ADMIN_PASSWORD_HASH=$HASH"
