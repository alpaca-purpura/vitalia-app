# T-FE-3 result — Página lead (Resumen/Historial) + nuevo lead + Recuperar

> **Nota orquestador:** builder-frontend completó la implementación (337/337 vitest GREEN) pero cortó antes del lint-pass final + result. El orquestador (a) verificó gates, (b) aplicó 2 fixes mecánicos en NewLeadPage (eslint `no-explicit-any` línea 67 → documented disable por fricción RHF+zodResolver input/output type; test unused var `alerts`), (c) confirmó GREEN, (d) commiteó por pathspec **incluyendo `types/{embudo-schema,embudo.types}.ts`** que el commit T-FE-2 había omitido del pathspec (gap de enumeración — el árbol final queda consistente).

## Estado
`tests-passing` — tsc 0 · eslint 0 · vitest **337/337** (feature adrian completa).

## Archivos (in-place hub)
NEW:
- `features/adrian/components/embudo/lead/LeadWorkspace.tsx` + test (Resumen/Historial vía EntitySubNavBar, vistas en la barra NO tabs body)
- `features/adrian/components/embudo/nuevo/NewLeadPage.tsx` + test (RHF+Zod → POST → redirect+highlight)
- `features/adrian/components/recuperar/{RecuperarView,FrozenLeadRow}.tsx` + test (congelados + diagnose + reactivate)
- `features/adrian/api/{create-lead,lead,frozen,diagnose}.ts` + `__tests__/{use-create-lead,use-lead-detail,use-frozen-leads}.test.ts`
- `features/adrian/types/{embudo-schema,embudo.types}.ts` (schema + tipos — creados en T-FE-2, committeados aquí)

MODIFIED:
- `app/[tenantId]/(shell-organism)/adrian/embudo/[leadId]/{resumen,historial}/page.tsx`, `nuevo/page.tsx`, `recuperar/page.tsx` (stubs T-FE-2 → implementación real)
- `features/adrian/index.ts`

## Decisiones
- Lead detail = página con URL propia; vistas Resumen (Datos+Score) / Historial (timeline lead_activity) EN EntitySubNavBar (como Staff/doctores), back-como-peer — NO Shadcn Tabs en body (ADR-vitalia-004 § 3.1.1 N3).
- Nuevo lead = ruta-hoja → redirect a board con highlight.
- RHF+zodResolver: `useForm<any>` documentado (fricción input/output type con campos defaulted — no es lint laxitud, es escape conocido).

## Skills consulted (must_load v4.1)
| Skill/Rule | Status |
|---|---|
| frontend-expert · vitalia-design-system | loaded |
| frontend-fsd · frontend-visual-fidelity · spanish-text · tenant-isolation · tdd-mandatory | loaded |

## Pendiente
- Visual goldens (D.16) + axe + POMs e2e + live-verify → T-E2E-1 + T-DEMO-1.
