# dispatch-plan — vitalia-shell-dual-mount-a11y-fix

> architect-autonomous-mode.md. Architect propone; Chris ratifica autonomous_mode.

## autonomous_mode

```yaml
autonomous_mode: false   # default. Architect propone false: bugfix transversal (shell de los 5 agentes + valeria) → riesgo blast-radius alto. Recomendado pausa post-T-1 para review visual Chris antes de cerrar. Chris puede flipear a true al ratificar.
caps:
  audit_iterations: 4
  self_fix_iter: 5        # Carril A auditor-frontend (mecánico: lint/format/typo) — NO para hook-count/render logic (eso es Carril B → dev-team)
  wall_clock_min: 30
```

## Handoff matrix (ticket → agent → model → costo)

| Ticket | Surface | primary_agent | model | Auditor | Costo estimado |
|---|---|---|---|---|---|
| T-1 | ShellOrganismLayoutClient + tests (single-main + single-slot) | builder-frontend | **sonnet** | auditor-frontend (opus) | medio (reescritura + RED/GREEN) |
| T-2 | re-verificación transversal + axe + dev-app live | builder-frontend | **sonnet** | auditor-frontend (opus) | medio (Playwright + Chrome MCP) |

> NINGÚN ticket es agentic → NINGÚN Opus para build (R23 NO aplica). Auditor SIEMPRE Opus (auditor-frontend).

## DAG

```
T-1 (single-main + single-slot + tests RED→GREEN)
  └─► T-2 (transversal verify 5 agentes ×3 modos + axe + dev-app live)   [depends_on T-1]
        └─► AUTO-HANDOFF /auditor (auditor-frontend Opus)
              └─► APPROVED → AUTO-HANDOFF /pm-vitalia merge (reviewing → done)
```

## Playwright visual scope (resumen)

- **story_scope**: shell-organism layout core (estructura: 1 main, 1 slot). NO pixel-perfect del contenido de sub-tabs.
- **transversal**: 5 agentes [lisa, mateo, adrian, lucas, camila] + valeria sidebar × 3 modos [agentic, web, mobile].
- **e2e proof**: doctores `getByTestId` → 1 elemento sin `.filter({visible:true})`.
- **dev-app live (ADR-008)**: lisa + valeria desktop+mobile; consola sin 'more hooks'/hydration; 1 main + 1 slot en DOM real. Tool: chrome-devtools-verify (live) + Playwright autenticado (golden).
- **out-of-scope**: cleanup del workaround `.filter` en POMs de doctores (lo hace la story doctores al re-correr).

## Blast radius / riesgo

- ★ **Transversal**: una regresión rompe la UI de los 5 agentes + valeria. T-2 (verificación transversal) NO es opcional.
- Prohibición central (no mount condicional del `<Group>` detrás de `isDesktop`) documentada en 03-arch D3/D4 + 05-guidelines FORBIDDEN. Auditor verifica que el fix NO reintrodujo el approach que crashea.

## Spawn order (si autonomous_mode flipea a true)

1. `/dev-team` T-1 (builder-frontend Sonnet) — RED tests → fix → GREEN + arch gates.
2. `/dev-team` T-2 (builder-frontend Sonnet) — transversal + dev-app live evidence.
3. AUTO `/auditor` (auditor-frontend Opus) — 13 cats + visual fidelity + verifica no-crash-reintroducido.
4. AUTO `/pm-vitalia` merge si APPROVED.
