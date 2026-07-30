# Luana core-modules — public contracts

> SSoT pública de los 27 paquetes `luana-core-*`. Una entrada por package con: contract, EPs expuestas, brands consumidoras, status.
>
> **Pointer-first:** este dir documenta el _contract_, no la implementación. Código vive en `core/luana-core-*`. Tests + ADRs locales viven en cada package.

## Índice

| Package | Tipo | Verdict | EPs expuestas | Status |
|---|---|---|---|---|
| [iam](./iam.md) | CORE-FULL | base | — | active |
| [platform](./platform.md) | CORE-FULL | base infra | — | active |
| [observability](./observability.md) | CORE-FULL | base infra | — | active |
| [events](./events.md) | CORE-FULL | base events + outbox | — | active |
| [extension-sdk](./extension-sdk.md) | CORE-FULL | base | EP-1..EP-18 registry | active |
| [extraction](./extraction.md) | CORE-FULL | base | — | active |
| [llm](./llm.md) | CORE-FULL | base | — | active |
| [idempotency](./idempotency.md) | CORE-FULL | base | — | active |
| [flows](./flows.md) | CORE-FULL | durable-runtime | EP-19 (L2 deferred) | active |
| [channels](./channels.md) | CORE-FULL | base | — | active |
| [compliance](./compliance.md) | CORE-FULL | base | — | active |
| [billing](./billing.md) | CORE-FULL | base | — | active |
| [crm](./crm.md) | CORE-FULL | engine | EP-15 (pipeline stages) | active |
| [assets](./assets.md) | CORE-FULL | engine | EP-12 (templates) | active |
| [social-proof](./social-proof.md) | CORE-FULL | engine | — | active |
| [commercial-calendar](./commercial-calendar.md) | CORE-FULL | engine | — | active |
| [tenant-domains](./tenant-domains.md) | CORE-FULL | engine | — | active |
| [tenant-profile](./tenant-profile.md) | CORE-FULL | engine | — | active |
| [copilot](./copilot.md) | ENGINE + EXTENSION | engine | EP-4, EP-7, EP-14 | active |
| [sales-agent](./sales-agent.md) | ENGINE + EXTENSION | engine | EP-3, EP-13 | active |
| [brand-studio](./brand-studio.md) | ENGINE + CONFIG | engine | EP-1 | active |
| [offer-studio](./offer-studio.md) | ENGINE + CONFIG | engine | EP-2 | active |
| [analytics-engine](./analytics-engine.md) | ENGINE + CONFIG | engine | EP-9 | active |
| [campaigns](./campaigns.md) | ENGINE + CONFIG | engine | EP-11 | active |
| [landing](./landing.md) | ENGINE + CONFIG | engine | EP-10 | active |
| [connections](./connections.md) | ENGINE + EXTENSION | engine | EP-8 | active |

## Cross-cutting concerns (transversal a 22 surfaces)

Detalle: `docs/architecture/luana-platform/01-core-audit.md` § 4.

## Patrón doc per-package

Cada `{package}.md` contiene:
- Frontmatter: `package, verdict, version, eps, consumers, status`
- Sección **Contract público** (clases/funciones exportadas, sin implementación)
- Sección **Extension points** (cómo brands extienden — code samples)
- Sección **Brands consumidoras** (lista actual + opt-in flag en `{brand}/config/brand.yaml`)
- Sección **Promotion history** (qué proposals migraron acá)
- Sección **Drill-down** (paths a código + tests)

Templates iniciales se generan en F5 (auto-gen via `scripts/generate_core_modules.py`).
