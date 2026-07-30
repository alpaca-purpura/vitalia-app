# Vitalia — domains

Documentación de qué tools/workflows/extractors/adapters registró este brand vía Extension SDK (EP-1..EP-18).

Estructura sugerida:

| Subdir | EP | Contenido |
|---|---|---|
| `copilot/` | EP-4, EP-7, EP-14 | workflows, extractors, KB packs registrados |
| `sales-agent/` | EP-3, EP-13 | tools, guardrails brand-specific |
| `offer/` | EP-2 | preset packs verticales |
| `landing/` | EP-10 | templates page brand |
| `scheduling/` | EP-5 | bookingPolicy.canConfirm handler |
| `connections/` | EP-8 | channel adapters verticales |
| `analytics/` | EP-9 | custom metrics |
| `campaigns/` | EP-11 | templates campaign |
| `assets/` | EP-12 | templates assets |
| `crm/` | EP-15 | custom pipeline stages |

Cada subdir contiene `{component-name}.md` con contract + tests + status.
