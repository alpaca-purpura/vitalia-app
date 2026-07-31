---
outcome_id: linux-live-verification-replacement
type: platform
state: refining
opened_date: 2026-05-20
opened_by: /pm-luana
priority: HIGH (4to ciclo consecutivo bloqueado)
why_now: "Sin alternativa Linux-native a chrome-devtools-verify (deprecated 2026-05-15), todas las stories FE quedan APPROVED-WITH-CAVEAT (live verification deferred a Chris). Acumulación deuda técnica."
affected_brands: [all-FE]   # vitalia, nicolify, comunify, lupulo, + 6 pendientes
consumer_brands: [comunify, vitalia, nicolify, lupulo]
target_packages_potencial: [core/luana-core-platform, .claude/skills/]
ssot_owner: /pm-luana
last_updated: 2026-05-20
---

# Outcome platform — Linux live verification replacement

## Spark

Chris trabaja en Linux Mint nativo desde 2026-05-15 (migración desde Windows+WSL2). La skill `chrome-devtools-verify` quedó deprecada porque su arquitectura asumía WSL2 bridge (no aplica Linux nativo). NO se generó reemplazo en su momento.

**4 ciclos consecutivos shippearon con caveat "live verification deferred":**

| # | Story | Fecha | Verificación deferred |
|---|---|---|---|
| 1 | Story 12 — Comunify bootstrap Clerk env | 2026-05-15 | 18/21 smoke tests fail por CLERK_TESTING_TOKEN |
| 2 | comunify-design-system-cement | 2026-05-18 | visual_smoke deferred (worktree mount mismatch) |
| 3 | comunify-design-system-tailwind-v4-tokens | 2026-05-20 AM | CSS bundle verification deferred |
| 4 | comunify-design-system-a11y-contrast-cement | 2026-05-20 PM | 9 Playwright specs authored, live run deferred |

## Why now (urgencia)

- **Acumulación deuda:** cada story FE que cierra "APPROVED-WITH-CAVEAT" confía en verificación post-merge manual de Chris. Si esa verificación NO se ejecuta, podríamos shippear bugs visuales silenciosos.
- **Caso real:** tailwind-v4-tokens viajó 2 días sin detectar que el CSS bundle servía 467 líneas sin utilities — solo se descubrió cuando Chris abrió manualmente el navegador.
- **Tipo de issue acumulado:** Clerk widget rendering (Story 12), CSS bundle emission (tailwind-v4), runtime computed styles (a11y), visual regression cross-component.
- **Bloqueo recurso humano:** Chris es el "verificador único" del frontend. Bottleneck.
- **Brands futuras:** las 6 brands pendientes bootstrap (saasora/inmoflow/retailly/fixia/guestly/fitflow) van a sufrir lo mismo desde el día 1.

## Opciones candidatas a evaluar (research)

### Opción A — Reactivar `chrome-devtools-verify` con adapter Linux

- Reescribir la skill removiendo asunción WSL2 bridge
- Usar Chrome/Chromium headless directo via `chrome --headless --remote-debugging-port`
- DevTools Protocol over WebSocket (Linux-native stack)
- **Pros:** mantiene UX skill conocida, reuse de patterns existentes
- **Cons:** requiere maintaining el wrapper, posible duplicación con Playwright

### Opción B — Playwright como único path (reducción scope live verification)

- Aceptar que Playwright es el reemplazo natural y refinar workflow
- Pre-flight script: levanta dev stack auto + corre regression project
- Make target `make verify-fe-{brand}` que orquesta todo
- **Pros:** Playwright ya está instalado, comprobado, maintained
- **Cons:** overhead de levantar dev stack para cada verificación rápida (mata productividad). Casos "open browser, check 1 element" siguen siendo over-engineered.

### Opción C — DOM-test runner alternativo (jsdom / happy-dom + Vitest)

- Para casos NO-stack (CSS bundle emission, computed styles, runtime checks rápidos)
- Vitest + happy-dom puede simular browser environment sin dev stack
- **Pros:** rapidísimo, no requiere stack levantado
- **Cons:** NO testea integration real (no detecta bugs Clerk widget, etc.). Solo unit-level component rendering.

### Opción D — MCP browser headless Linux-native

- Investigar MCPs disponibles (`mcp__browser`, `mcp__playwright`, etc.)
- Tessl skill o equivalent que abstraiga Chrome headless Linux
- **Pros:** stack moderno, agentic-friendly
- **Cons:** dependencia externa, learning curve, status maturity desconocido

### Opción E — Hybrid (recomendada preliminarmente)

Combinar B + C: Playwright para integration real (dev stack up) + DOM-test runner para checks rápidos sin stack. Documentar workflow:
- "Check rápido CSS/render" → vitest + happy-dom
- "Check integration real" → Playwright regression project + dev stack pre-flight script

## Decomposition a stories

Después de research outcome, descomponer en:

1. **Story R1 (Research):** `linux-live-verification-research-decision` — analizar opciones A-E en profundidad, prototipos quick, decisión arquitectónica con ADR. Owner: `/po` + Chris. Output: ADR `docs/architecture/luana-platform/ADR-{N}-live-verification.md`.

2. **Story I1 (Implementation):** `live-verification-{chosen-option}` — implementar la opción elegida. Owner: `/dev-team`. Scope estimado: M (3-5 días).

3. **Story S1 (Sweep):** `sweep-deferred-verifications` — re-ejecutar las 4 verificaciones deferred acumuladas (Clerk env Story 12 + cement + tailwind-v4-tokens + a11y-contrast-cement) con el stack nuevo. Owner: `/dev-team`. Scope estimado: S (2-3 horas).

4. **Story D1 (Documentation):** `update-process-docs` — update `docs/process/docker-dev-multibrand.md` + `.claude/rules/e2e-testing.md` + skill `playwright-expert` con workflow definitivo. Owner: `/pm-luana`. Scope: S (1 hora).

## Definición de éxito

- 0 stories FE cierran con caveat "live verification deferred"
- Workflow documentado en `.claude/rules/e2e-testing.md` reemplazando referencias a `chrome-devtools-verify`
- Skill `chrome-devtools-verify` archivada/eliminada formalmente
- 4 deferred verifications de stories anteriores resueltas

## Out of scope

- Visual regression baseline (`toMatchScreenshot`) — separate story `comunify-visual-regression-baseline` futura
- E2E coverage gap general (no se trata de cobertura, sino de mecanismo verification rápido)
- CI/CD remoto (esto es local dev verification — CI ya tiene Playwright)

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Opción elegida no Linux-native compatible | Alta | Research story R1 valida prototipos antes commit |
| Playwright overhead mata productividad iteración rápida | Media | Opción E hybrid reduce overhead para checks rápidos |
| Brands futuras bootstrap antes outcome completo | Media | Ojo `_pm-brand-template/` actualizar con workflow nuevo simultáneamente |
| chrome-devtools-verify skill referenciado en docs aún | Baja | Sweep docs como parte de Story D1 |

## Bitácora

- 2026-05-20: opened by /pm-luana (autonomous Chris autorización "resolvamoslo todo de una vez"). Origen: 3er promotable de comunify INDEX-promotables.md.

## Próximo paso

Chris ratifica scope outcome → handoff `/po` (Story R1 research). Mientras tanto, stories FE pueden seguir cerrando con caveat "deferred" hasta outcome completo.

## Cross-references

- Comunify learning origen (pending write): `comunify/docs/learnings/(pending)-linux-live-verification-replacement.md`
- chrome-devtools-verify skill (deprecated): `.claude/skills/chrome-devtools-verify/SKILL.md`
- Workflow E2E actual: `.claude/rules/e2e-testing.md`
- Playwright expert skill: `.claude/skills/playwright-expert/SKILL.md`
- 4 stories afectadas (audit trail):
  - `comunify/docs/archive/2026/stories/comunify-bootstrap/` (Story 12)
  - `comunify/docs/archive/2026/stories/comunify-design-system-cement/`
  - `comunify/docs/archive/2026/stories/comunify-design-system-tailwind-v4-tokens/`
  - `comunify/docs/archive/2026/stories/comunify-design-system-a11y-contrast-cement/`
