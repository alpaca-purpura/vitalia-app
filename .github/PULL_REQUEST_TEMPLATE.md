## Qué cambia

<!-- 1-3 bullet points describiendo el cambio funcional -->

## Por qué

<!-- Razón de negocio o técnica. Link a story / release si aplica. -->

## Módulos tocados

<!-- Marca con [x] -->
- [ ] vitalia/backend
- [ ] vitalia/frontend
- [ ] core/luana-core-* (engine)
- [ ] docs/*
- [ ] scripts/ o .github/ (tooling / CI / gobernanza)

## Checklist (gates locales — el enforcement primario son los hooks)

- [ ] Gates locales corridos en verde (lint + typecheck + tests: `/test-all` o suites BE/FE nativas)
- [ ] Tests nuevos/actualizados para el cambio (TDD — regression test primero si es bugfix)
- [ ] Migraciones idempotentes (`IF NOT EXISTS` / `IF EXISTS`) — si aplica
- [ ] Tenant isolation verificada (queries filtran `tenant_id`) — si toca datos
- [ ] Live-verify ejercida contra el stack dev real (`dod_evidence`) — si la story es funcional

## ADR ref (si toca core/)

<!-- Link al ADR en docs/architecture/ que justifica el cambio al engine. -->

ADR: docs/architecture/...

## Story ref

<!-- Link a la story en vitalia/docs/product/stories/. -->

Story: vitalia/docs/product/stories/...
