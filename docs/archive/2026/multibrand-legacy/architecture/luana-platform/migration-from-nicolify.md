> [ARCHIVADO — read-only. Guía de migración desde el monolito nicolify previa al nicolify-reset (2026-05-29). Los ejemplos de SDK/API y el código fuente referenciado ya no aplican (copy-paste produciría errores). Conservado por trazabilidad.]

# Migración desde Nicolify (AISALESHT) a Luana Platform v0.1.0

## §1 Audiencia

Este documento está dirigido a:

- **Equipo Nicolify** (Chris y colaboradores) que quieren consumir `luana-core-*` desde el monorepo
  privado en lugar de `AISALESHT/backend/src/`.
- **Equipos de marcas verticales** (Vitalia, Comunify, Lupulo) que comenzarán el bootstrap en
  Stories 11-13 usando las librerías de Luana como dependencias publicadas en GitHub Packages.
- **Desarrolladores externos** que construyan integraciones sobre el Extension SDK (`EP-1..EP-18`).

**Prerequisito de nivel:** Python ≥ 3.12, Node ≥ 22, pnpm ≥ 9, `uv` instalado.

---

## §2 Lista de verificación antes de migrar

Antes de instalar cualquier paquete de Luana Platform, verifica que tienes:

- [ ] **Python ≥ 3.12** — verifica con `python --version` o `python3 --version`
- [ ] **Node ≥ 22** — verifica con `node --version`
- [ ] **pnpm ≥ 9** — verifica con `pnpm --version`
- [ ] **uv instalado** (Astral) — verifica con `uv --version`
- [ ] **`~/.netrc` o `pip config`** configurado para `https://pypi.pkg.github.com/alpacapurpura/`
- [ ] **`~/.npmrc`** configurado con:
  ```
  @luana:registry=https://npm.pkg.github.com/
  //npm.pkg.github.com/:_authToken=TU_TOKEN
  ```
- [ ] **`GH_PACKAGES_TOKEN`** con scope `read:packages` (o `GITHUB_TOKEN` desde `gh auth login`)
- [ ] **Variable de entorno `LUANA_BRAND_SLUG`** seteada (ej. `nicolify`, `vitalia`) — requerida por CC-4

Para configurar el token:

```bash
# Opción A: GitHub CLI (recomendada)
gh auth login --scopes read:packages,write:packages
export GH_PACKAGES_TOKEN=$(gh auth token)

# Opción B: PAT manual
export GH_PACKAGES_TOKEN=ghp_XXXX  # token con read:packages scope

# Configurar ~/.netrc para Python/uv
echo "machine pypi.pkg.github.com login TU_USUARIO password ${GH_PACKAGES_TOKEN}" >> ~/.netrc
chmod 600 ~/.netrc
```

---

## §3 Mapa de importaciones

| Origen (AISALESHT) | Destino (Luana Platform) | Notas |
|---|---|---|
| `from src.shared.agent_observability.recording.X` | `from luana_core_observability.recording.X` | BaseAgentCallbackHandler, BaseObservabilityContext |
| `from src.shared.agent_observability.cost.X` | `from luana_core_observability.cost.X` | CostRecorder, FXResolver, PricingResolver |
| `from src.shared.events.X` | `from luana_core_events.X` | DomainEvent, EventBus, outbox |
| `from src.shared.billing.X` | `from luana_core_billing.X` | BudgetGuard, OutboundRateLimiter |
| `from src.shared.compliance.X` | `from luana_core_compliance.X` | ComplianceService |
| `from src.shared.idempotency.X` | `from luana_core_idempotency.X` | IdempotencyKey, RedisRateLimiter |
| `from src.shared.infrastructure.llm.X` | `from luana_core_llm.X` | LLMRouter, LiteLLMProvider |
| `from src.shared.application.extraction.X` | `from luana_core_extraction.X` | BaseExtractionOrchestrator |
| `from src.modules.copilot.X` | `from luana_core_copilot.X` | LangGraph graph, registries, phases |
| `from src.modules.sales_agent.X` | `from luana_core_sales_agent.X` | StateGraph, specialists, BrandVoicePort |
| `from src.modules.brand.X` | `from luana_core_brand_studio.X` | BrandSettings, PersonalityProfile, BrandDataPort |
| `from src.modules.offer.X` | `from luana_core_offer_studio.X` | 7 catalogs, FieldContract, presets |
| `from src.modules.analytics.X` | `from luana_core_analytics_engine.X` | stage services, ETL contract |
| `from src.modules.campaigns.X` | `from luana_core_campaigns.X` | DripCampaign, workers |
| `from src.modules.crm.X` | `from luana_core_crm.X` | Lifecycle, deals |
| `from src.modules.iam.X` | `from luana_core_iam.X` | Clerk integration, tenant scoping |
| `from src.modules.landing.X` | `from luana_core_landing.X` | LandingService, templates |
| `from src.modules.connections.X` | `from luana_core_connections.X` | ChannelProvider, OAuth |
| `from src.modules.assets.X` | `from luana_core_assets.X` | MediaLibrary, AssetService |
| TS `from '@/lib/api-client'` | `from '@luana/api-client'` | fetchClient con inyección X-Tenant-ID |
| TS `from '@/lib/format'` | `from '@luana/format'` | formatMoney, formatTenantDate* |
| TS `from '@/hooks/...'` | `from '@luana/hooks'` | useTenantLocale, etc. |
| TS `from '@/components/ui/...'` | `from '@luana/ui-kit/...'` | Shadcn/Radix components |
| TS `from '@/lib/zod-schemas/...'` | `from '@luana/schemas'` | Zod validation schemas |

Para el mapeo completo por paquete, consulta `docs/core-modules/{package}.md` (WIP build-out post-purga 2026-05-19; pre-purga existía `docs/api/python/` auto-gen pdoc, eliminado por generador roto — ver `docs/process/learnings.md` 2026-05-19 entry).

---

## §4 Instalación de dependencias

### Python (uv — recomendado)

```bash
# Configurar índice privado de GitHub Packages
cat >> pyproject.toml <<'EOF'

[[tool.uv.index]]
name = "github-luana"
url = "https://pypi.pkg.github.com/alpacapurpura/simple/"
default = false
EOF

# Instalar un paquete específico
uv add luana-core-platform==0.1.0

# Instalar múltiples paquetes (todos al mismo tiempo)
uv add luana-core-platform==0.1.0 luana-core-extension-sdk==0.1.0

# Instalar todos los core packages (para migración completa)
uv add \
  luana-core-platform==0.1.0 \
  luana-core-llm==0.1.0 \
  luana-core-observability==0.1.0 \
  luana-core-events==0.1.0 \
  luana-core-billing==0.1.0 \
  luana-core-extension-sdk==0.1.0
```

### Python (pip)

```bash
# Configurar ~/.pip/pip.conf
cat > ~/.pip/pip.conf <<'EOF'
[global]
index-url = https://pypi.pkg.github.com/alpacapurpura/simple/
trusted-host = pypi.pkg.github.com
EOF

# O inline con --index-url
pip install luana-core-platform==0.1.0 \
  --index-url https://pypi.pkg.github.com/alpacapurpura/simple/ \
  --extra-index-url https://pypi.org/simple/
```

### TypeScript (pnpm — recomendado)

```bash
# Configurar .npmrc en el root del proyecto (o ~/.npmrc global)
cat >> .npmrc <<'EOF'
@luana:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${GH_PACKAGES_TOKEN}
EOF

# Instalar paquetes
pnpm add @luana/extension-sdk@0.1.0
pnpm add @luana/api-client@0.1.0 @luana/format@0.1.0 @luana/hooks@0.1.0

# O todos juntos
pnpm add @luana/api-client@0.1.0 @luana/design-tokens@0.1.0 \
         @luana/extension-sdk@0.1.0 @luana/format@0.1.0 \
         @luana/hooks@0.1.0 @luana/schemas@0.1.0 @luana/ui-kit@0.1.0
```

**Importante:** todos los paquetes `luana-core-*` deben usar la misma versión (e.g., `==0.1.0`).
Las dependencias cruzadas son strict-pinned.

---

## §5 Patrón de consumo del Extension SDK

El Extension SDK es el punto de entrada principal para construir una aplicación vertical sobre
`luana-core`. Lee `docs/architecture/luana-platform/extension-points.md` para la especificación completa (18 EPs, 5 CC policies).

### Quickstart Python

```python
from fastapi import FastAPI
from luana_core_extension_sdk import (
    ExtensionPointRegistry,
    BrandContext,
    ExtensionHandler,
)

# 1. Crear registry (singleton por aplicación)
registry = ExtensionPointRegistry()

# 2. Registrar handlers para los EPs que tu marca necesita
@registry.offer_preset_pack_register
def mi_preset_pack() -> list[dict]:
    """EP-1: Paquete de presets específico de la marca."""
    return [
        {"preset_id": "mi_servicio_estrella", "label_es": "Mi servicio estrella"},
    ]

@registry.brand_voice_seed_register
def mi_voz_seed() -> dict:
    """EP-2: Semilla de voz de marca para el compilador."""
    return {"archetype": "sage", "warmth": 0.8, "humor": 0.3}

# 3. Bloquear registry post-startup (CC-5: inmutable después del startup)
registry.lock()

# 4. Inicializar FastAPI con el brand context
app = FastAPI(redirect_slashes=False)

@app.on_event("startup")
async def startup():
    brand_ctx = BrandContext.from_env()  # Lee LUANA_BRAND_SLUG del env
    # brand_ctx.brand_slug == "nicolify" (o "vitalia", etc.)
    app.state.brand_ctx = brand_ctx
    app.state.registry = registry
```

### Quickstart TypeScript

```typescript
import { ExtensionPointRegistry } from '@luana/extension-sdk';
import type { BrandContext, ToolRegistryAdapter } from '@luana/extension-sdk';

// EP-3: Registrar herramientas para el sales agent
const registry = new ExtensionPointRegistry();

registry.salesAgentToolRegister({
  tool_id: 'consultar_disponibilidad',
  label_es: 'Consultar disponibilidad',
  handler: async (ctx: BrandContext) => {
    // tu lógica aquí
    return { slots: [] };
  },
});

export default registry;
```

### Variables de entorno requeridas

```bash
LUANA_BRAND_SLUG=nicolify        # CC-4: namespace de marca (requerido)
POSTGRES_URL=postgresql://...    # conexión a la base de datos
REDIS_URL=redis://localhost:6379 # para idempotencia + rate limiting
CLERK_SECRET_KEY=sk_...          # autenticación Clerk (IAM)
LITELLM_PROXY_URL=http://...     # proxy LiteLLM (si aplica)
```

---

## §6 Resolución de problemas

| Error | Causa probable | Solución |
|---|---|---|
| `403 Forbidden` en pip/uv install | Token sin `read:packages` o no configurado | Verifica `~/.netrc` con `cat ~/.netrc`. Regen con `gh auth login --scopes read:packages,write:packages` |
| `Cannot find module '@luana/X'` | `.npmrc` no configurado para el scope `@luana` | Agrega `@luana:registry=https://npm.pkg.github.com/` en `.npmrc` + `_authToken` |
| `Version mismatch` entre paquetes | Versiones mezcladas de `luana-core-*` | Fija todos los paquetes a la misma versión: `uv add luana-core-*==0.1.0` |
| `namespace not registered` en Extension SDK | Variable de entorno `LUANA_BRAND_SLUG` ausente | `export LUANA_BRAND_SLUG=nicolify` (o el slug de tu marca) |
| `ExtensionPointRegistry locked` | Intentas registrar un EP después del startup | Registra todos los handlers **antes** de llamar `registry.lock()` |
| `40 test failures` en `luana-core-sales-agent` | Falla pre-existente Story 7 (fixture issue) | Esperado — ver CHANGELOG.md §Known issues. Story 10+ cleanup |
| `ImportError: cannot import name 'X'` | Cambio de nombre en lifting | Consulta §3 tabla de importaciones. Verifica `docs/core-modules/{package}.md` (WIP build-out) o lee directamente `core/luana-core-{package}/src/luana_core_{package}/__init__.py` |
| `BrandContext.brand_slug is None` | `LUANA_BRAND_SLUG` no seteada o `BrandContext.from_env()` no invocada | Verifica env var + llama `BrandContext.from_env()` en startup |
| `HALT: GH Packages auth missing` en CI | `GITHUB_TOKEN` sin `write:packages` + `GH_PACKAGES_TOKEN` no configurado | Ve a Settings → Secrets → Actions → crear `GH_PACKAGES_TOKEN` con `write:packages` scope. Ver `docs/process/release-procedure-v0.1.0.md §Token-setup` |

### Ejecutar tests post-migración

```bash
# Verificar que tu app arranca correctamente post-migración
uv run python -c "from luana_core_platform import __version__; print(f'platform {__version__} OK')"
uv run python -c "from luana_core_extension_sdk import ExtensionPointRegistry; r = ExtensionPointRegistry(); print('SDK OK')"

# Test suite de humo
cd apps/test-brand && uv run pytest tests/ -x -q --tb=short
```

Para más información sobre el Extension SDK, consulta `docs/architecture/luana-platform/extension-points.md`.
Para reportar problemas, abre un issue en `alpacapurpura/luana-platform`.
