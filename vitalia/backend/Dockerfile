# vitalia/backend/Dockerfile
# Build context: monorepo root (accede a core/ y vitalia/backend/)
# Target dev: hot-reload + uv editable workspace via bind mount
# Target final: produccion estatica
#
# IMPORTANTE: No copiar .venv del host — se instala dentro del container.
# El compose file protege .venv con anonymous volume (D4 — bind mount pattern).
#
# S-DOCKER-DEV-MULTIBRAND T-4 — 2026-05-15
# Port: 8002 (D6 port allocation)

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=0 \
    UV_LINK_MODE=copy

# Instalar uv
RUN pip install --no-cache-dir uv==0.4.18

WORKDIR /workspace

# ── dev target ── (usado en vitalia/docker-compose.dev.yml via bind mount)
FROM base AS dev

# En dev, el source viene via bind mount (no COPY).
# Pre-instalamos dependencias usando pyproject.toml del workspace raiz.
# El .venv es protegido por named volume en compose file.
COPY pyproject.toml uv.lock ./
COPY core/ ./core/
# vitalia/pyproject.toml = workspace member (declara deps runtime backend incl. uvicorn).
# vitalia/backend/pyproject.toml = subproyecto aislado (mantained por separado, mismo nombre).
COPY vitalia/pyproject.toml ./vitalia/pyproject.toml
COPY vitalia/backend/pyproject.toml ./vitalia/backend/pyproject.toml

# `uv sync` con --frozen falla silenciosa cuando un workspace member referenciado en
# lockfile no está físicamente presente en el filesystem del image build context.
# Sin --frozen, uv regenera el lock y procede. Sin --no-dev se evita instalar dev deps.
# El `--package luana-vitalia` filtra al package que importa runtime deps backend.
RUN uv sync --no-dev --package luana-vitalia 2>&1

WORKDIR /workspace/vitalia/backend

EXPOSE 8002
# CMD sobreescrito en compose file (uvicorn --reload con --reload-dir)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ── final target ── (produccion — usado por CI/CD)
FROM base AS final

RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

COPY pyproject.toml uv.lock ./
COPY core/ ./core/
COPY vitalia/backend/ ./vitalia/backend/

RUN uv sync --frozen --no-dev --package luana-vitalia

WORKDIR /workspace/vitalia/backend
RUN chown -R appuser:appuser /workspace
USER appuser

EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
