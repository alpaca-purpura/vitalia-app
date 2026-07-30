<!-- AUTO-GENERATED por scripts/build_live_reconciliation_matrix.py — NO editar a mano -->
<!-- Generado: 2026-05-29T21:34:19.794276+00:00 | brand: vitalia -->

# Live Reconciliation Matrix — Vitalia v1

> Artefacto vivo `ops.live-reconciliation-sweep`. Regenerar: `python3 scripts/build_live_reconciliation_matrix.py --brand vitalia`

**Generado:** 2026-05-29T21:34:19.794276+00:00
**Total superficies en matriz:** 88

## Resumen

### Conteos por sweep_verdict

| sweep_verdict | Count |
|---|---|
| ✅ OK | 21 |
| ❌ ROTO | 0 |
| ⚠️ INACCESIBLE | 0 |
| 🔲 SIN-UI | 67 |

### Conteos por computed_status

| computed_status | Count |
|---|---|
| 🟢 verified-live | 1 |
| 🟡 partial | 5 |
| 🟠 declared-live | 6 |
| ⬜ stub | 55 |

## Matriz completa

| cap_id | declared_status | computed_status | ruta | sweep_verdict | evidencia | technical_verdict | acción | story_mapeada |
|---|---|---|---|---|---|---|---|---|
| 3-clinic-fixture-latam | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · fixture seed · verificado live via DB 3 tenants | mantener status:planned · fixture activo en dev DB | — |
| admin-streamlit-service | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · admin-panel · accesible via subdomain separado (localhost:8502) | mantener status:live + ui_paradigm:admin-panel | — |
| adrian-3-tools-mvp | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE agentic tools · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-adrian-embudo |
| adrian-reengagement-tool | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE tool · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-camila-reactivar |
| api-health-endpoint | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · /api/health endpoint · no ruta UI shell | mantener status:live + ui_paradigm:infra-only | — |
| attribution-matrix-4-origins | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · slice-1 UI · reemplazada por /lucas/resultados F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lucas-resultados |
| audit-writer-ssot | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · BE audit log writer · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| auth.sign-in-sign-up-pages | — | — | /sign-in | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/sign-in.png`, HTTP 200, n… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| booking-widget-embed | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · widget standalone · no shell-organism UI | deprecated + ui_paradigm:slice-1-superseded · sin F2 story directa | — |
| bowtie-funnel-5-stages | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · slice-1 UI · reemplazada por /adrian/embudo F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-adrian-embudo |
| brand-studio-medical-sections | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · reemplazado por lisa-marca F2-S7 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-doctores |
| brand_studio.lisa-marca | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lisa/marca/presencia | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| clerk-middleware | live | verified-live | — | 🔲 SIN-UI | sin hallazgo de sweep | verified-live · computed por script · e2e en filesystem | mantener status:live · computed=verified-live | — |
| clinic-onboarding-3step | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · wizard slice-1 · reemplazado por lisa-doctores F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-doctores |
| clinics-brand-extension | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | pendiente T-3 | pendiente T-3 | pendiente T-3 |
| clinics-crud | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · admin-panel · parte del panel Streamlit admin | mantener status:live + ui_paradigm:admin-panel | — |
| clinics.clinics-brand-extension | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lisa/doctores | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lisa/doctores presente, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lisa-doctores | vitalia-fase2-lisa-doctores |
| compliance-hipaa-lite-audit | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE compliance · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-compliance |
| compliance.compliance-hipaa-lite-audit | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lisa/compliance | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lisa/compliance presente, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lisa-compliance | vitalia-fase2-lisa-compliance |
| connections.oauth-meta-google-ads | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/config/conexiones | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /config/conexiones presente, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-config-conexiones | vitalia-fase2-config-conexiones |
| crm-consent-optout | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE consentimiento · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-valeria-pacientes |
| crm-scaffold-slice-1 | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · scaffold slice-1 · superseded por shell-organism | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-valeria-pacientes |
| design-tokens-foundation | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · CSS vars globals.css · no ruta directa | mantener status:live + ui_paradigm:infra-only | — |
| design-tokens-theme | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · shell-organism · ThemeToggle visible en topbar | mantener status:live + ui_paradigm:shell-organism | — |
| eval-goldens-slice-1 | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · agentic test infra · no ruta UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · sin F2 story directa | — |
| fiscal-emission-pe | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · story service-lateral refining · no UI aún | mantener status:planned | vitalia-fiscal-emission-pe (service story) |
| hipaa-dual-filter-decorator | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · BE decorator · sin ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| hipaa-lite-defensive-stack | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE stack defensivo · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-compliance |
| iam-scaffold-slice-1 | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · shell-organism · API /api/health y rutas /config/avanzado OK | mantener status:live + ui_paradigm:shell-organism | — |
| iam.iam-scaffold-slice-1 | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/config/avanzado | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| iam.luana-core-adoption | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/config/cuenta | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| idempotent-cron-arq-scaffold | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · BE cron workers · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| inbox-handler-mode-occ | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE inbox handler · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-adrian-inbox |
| inbox-tools-extensions | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE inbox tools · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-adrian-inbox |
| k8s-admin-deployment | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · infra K8s manifests · sin UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · infra pura | — |
| lisa-marca | live | partial | — | 🔲 SIN-UI | sin hallazgo de sweep | live · shell-organism · sweep OK /lisa/marca | mantener status:live + ui_paradigm:shell-organism | — |
| luana-core-adoption | live | partial | — | 🔲 SIN-UI | sin hallazgo de sweep | live · partial · shell-organism · /config/cuenta sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| lucas-daily-analysis | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE agentic tool · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lucas-resultados |
| lucas-recommendation-tool | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE agentic tool · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lucas-lanzar |
| lucas-stage-recommendations | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · slice-1 UI · reemplazada por /lucas/lanzar F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lucas-lanzar |
| marketing.attribution-matrix-4-origins | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lucas/resultados | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lucas/resultados, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lucas-resultados | vitalia-fase2-lucas-resultados |
| marketing.bowtie-funnel-5-stages | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/adrian/outbound | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /adrian/outbound, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-adrian-embudo | vitalia-fase2-adrian-embudo |
| marketing.lucas-recommendation-tool | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lucas/mercado | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lucas/mercado, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lucas-lanzar | vitalia-fase2-lucas-lanzar |
| marketing.lucas-stage-recommendations | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lucas/lanzar | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lucas/lanzar, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lucas-lanzar | vitalia-fase2-lucas-lanzar |
| marketing.referrals-leaderboard | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/camila/multiplicar | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /camila/multiplicar, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-camila-multiplicar | vitalia-fase2-camila-multiplicar |
| medical-agentic-tools | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE agentic tools · sin ruta UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · BE infra | — |
| medical-guardrails | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE guardrails · sin ruta UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · BE infra | — |
| medical-kb-rag | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE RAG · sin ruta UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · BE infra | — |
| medical-pdf-extractors | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · BE extractors · sin implementacion UI | mantener status:planned | — |
| medical-safety-guardrails | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE guardrails · sin ruta UI shell-organism | deprecated + ui_paradigm:slice-1-superseded · BE infra | — |
| medical-services-offer-preset | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · BE preset · UI pendiente F2 | mantener status:planned | vitalia-fase2-lisa-servicios |
| migrations-slice-1-schema | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · schema DB migrations · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| nps-tracking | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE NPS · UI reemplazada por /camila/reputacion F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-camila-reputacion |
| oauth-meta-google-ads | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE OAuth · UI reemplazada por config/conexiones F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-config-conexiones |
| offer_studio.medical-services-offer-preset | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/lisa/servicios | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /lisa/servicios, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-lisa-servicios | vitalia-fase2-lisa-servicios |
| otel-sentry-graceful-degradation | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · observabilidad BE · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| patient-records-medical-history | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · BE parcial · UI pendiente F2-S2 | mantener status:planned | vitalia-fase2-valeria-pacientes |
| patients.nps-tracking | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/camila/reputacion | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /camila/reputacion, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-camila-reputacion | vitalia-fase2-camila-reputacion |
| patients.patient-records-medical-history | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/valeria/pacientes | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /valeria/pacientes, empty state F2) | planned · ruta presente como empty state · esperar F2 | vitalia-fase2-valeria-pacientes |
| payment-gateways-latam-recurring | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE stubs MSW activos · service story lateral en refining | deprecated + ui_paradigm:slice-1-superseded | vitalia-payment-adapter-mvp (service story) |
| playwright-smoke-suite | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · suite E2E local · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| prepaid-booking-advisory-locks | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE locks · UI reemplazada por valeria-agenda F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-valeria-agenda |
| public-clinic-landing | live | declared-live | — | 🔲 SIN-UI | sin hallazgo de sweep | live · public-landing · ruta /public/{clinic-slug} · no shell-organism | mantener status:live + ui_paradigm:public-landing | — |
| re-engagement | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · sin codigo implementado aun | mantener status:planned | — |
| referrals-leaderboard | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · slice-1 UI · reemplazada por /camila/multiplicar F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-camila-multiplicar |
| registries-medical-vertical | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · sin código implementado aún | mantener status:planned | — |
| sales_agent.adrian-3-tools-mvp | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/adrian/embudo | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /adrian/embudo, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-adrian-embudo | vitalia-fase2-adrian-embudo |
| sales_agent.inbox-handler-mode-occ | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/adrian/inbox | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /adrian/inbox, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-adrian-inbox | vitalia-fase2-adrian-inbox |
| sales_agent.state-overlay-langgraph | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/adrian/propuestas | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /adrian/propuestas, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-adrian-propuestas | vitalia-fase2-adrian-propuestas |
| scheduling.valeria-agenda | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/valeria/agenda | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| shell-foundation-shadcn-tailwind-v4 | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · Shadcn install + Tailwind v4 · no ruta directa | mantener status:live + ui_paradigm:infra-only | — |
| shell-organism.routing | — | — | /e69a691d-070e-5caf-a053-6e74642ec100 | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · shell-organism · sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| shell-vitalia | live | partial | — | 🔲 SIN-UI | sin hallazgo de sweep | live · partial · shell-organism · topbar+ribbon+valeria+sub-tabs verificados | mantener status:live + ui_paradigm:shell-organism | — |
| sign-in-sign-up-pages | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · shell-organism · /sign-in verificado por sweep | mantener status:live + ui_paradigm:shell-organism | — |
| state-overlay-langgraph | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE LangGraph state · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-adrian-propuestas |
| streamlit-tenants-users | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · admin-panel · parte del panel Streamlit admin | mantener status:live + ui_paradigm:admin-panel | — |
| tenant-switcher | live | partial | — | 🔲 SIN-UI | sin hallazgo de sweep | live · partial · shell-organism · dropdown visible en topbar | mantener status:live + ui_paradigm:shell-organism | — |
| tenants-crud | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · admin-panel · parte del panel Streamlit admin | mantener status:live + ui_paradigm:admin-panel | — |
| topbar-global | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · shell-organism · topbar visible en a11y snapshot | mantener status:live + ui_paradigm:shell-organism | — |
| treatment-followup-workflow | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE workflow · UI reemplazada por /camila/reactivar F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-camila-reactivar |
| treatments.treatment-followup-workflow | — | — | /e69a691d-070e-5caf-a053-6e74642ec100/camila/reactivar | ✅ OK | screenshot: `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/e69a691d-070e-5caf-a053-6… | live · sweep OK (ruta /camila/reactivar, empty state F2) | deprecated → replaced_by_story:vitalia-fase2-camila-reactivar | vitalia-fase2-camila-reactivar |
| users-crud | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · admin-panel · parte del panel Streamlit admin | mantener status:live + ui_paradigm:admin-panel | — |
| valeria-agenda | live | partial | — | 🔲 SIN-UI | sin hallazgo de sweep | live · partial · shell-organism · /valeria/agenda sweep OK | mantener status:live + ui_paradigm:shell-organism | — |
| valeria-wizard-onboarding-agentic | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · wizard agéntico · UI pendiente F2-S2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-valeria-pacientes |
| vertical-medical-extension-sdk | planned | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | planned · Extension SDK infra · sin UI directa | mantener status:planned + ui_paradigm:infra-only | — |
| vitalia-callback-subclasses | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | live · infra-only · subclases observabilidad · no ruta UI | mantener status:live + ui_paradigm:infra-only | — |
| whatsapp-template-registry | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · BE templates · UI pendiente F2 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-compliance |
| wizard-brand-studio-slice-1 | live | stub | — | 🔲 SIN-UI | sin hallazgo de sweep | deprecated · wizard slice-1 · reemplazado por lisa-marca F2-S7 | deprecated + ui_paradigm:slice-1-superseded | vitalia-fase2-lisa-marca |

## Backlog mapeado (T-3 — 2026-05-29)

> T-3 completado: sweep detectó 0 ROTO + 0 drift. Todos los caps SIN-UI son infra-only,
> admin-panel o slice-1-superseded. Las stories F2 mapean caps a implementar.
>
> Nota: el sweep encontro 21 rutas OK (empty states F2 navegables) — las caps
> correspondientes se marcaron `deprecated` porque el CODIGO slice-1 existe pero la
> UI shell-organism las reconstruye desde cero en las stories F2 respectivas.

### Prioridad 1 — primer valor end-to-end (ya en refining/ready)

| cap_id | ui_paradigm | computed_status | story_F2 | estado_story |
|---|---|---|---|---|
| valeria-agenda | shell-organism | partial | vitalia-fase2-valeria-agenda | done (LIVE) |
| lisa-marca | shell-organism | partial | vitalia-fase2-lisa-marca | refining |
| inbox-handler-mode-occ | slice-1-superseded | deprecated | vitalia-fase2-adrian-inbox | refining |
| crm-scaffold-slice-1 | slice-1-superseded | deprecated | vitalia-fase2-valeria-pacientes | idea |
| bowtie-funnel-5-stages | slice-1-superseded | deprecated | vitalia-fase2-adrian-embudo | refining |

### Prioridad 2 — Fase 2 stories por agente

| cap_id | ui_paradigm | computed_status | story_F2 | agente |
|---|---|---|---|---|
| patient-records-medical-history | infra-only (planned) | stub | vitalia-fase2-valeria-pacientes | valeria |
| crm-consent-optout | slice-1-superseded | deprecated | vitalia-fase2-valeria-pacientes | valeria |
| valeria-wizard-onboarding-agentic | slice-1-superseded | deprecated | vitalia-fase2-valeria-pacientes | valeria |
| inbox-tools-extensions | slice-1-superseded | deprecated | vitalia-fase2-adrian-inbox | adrian |
| adrian-3-tools-mvp | slice-1-superseded | deprecated | vitalia-fase2-adrian-embudo | adrian |
| state-overlay-langgraph | slice-1-superseded | deprecated | vitalia-fase2-adrian-propuestas | adrian |
| brand-studio-medical-sections | slice-1-superseded | deprecated | vitalia-fase2-lisa-doctores | lisa |
| clinic-onboarding-3step | slice-1-superseded | deprecated | vitalia-fase2-lisa-doctores | lisa |
| clinics-brand-extension | slice-1-superseded | deprecated | vitalia-fase2-lisa-doctores | lisa |
| compliance-hipaa-lite-audit | slice-1-superseded | deprecated | vitalia-fase2-lisa-compliance | lisa |
| hipaa-lite-defensive-stack | slice-1-superseded | deprecated | vitalia-fase2-lisa-compliance | lisa |
| whatsapp-template-registry | slice-1-superseded | deprecated | vitalia-fase2-lisa-compliance | lisa |
| nps-tracking | slice-1-superseded | deprecated | vitalia-fase2-camila-reputacion | camila |
| treatment-followup-workflow | slice-1-superseded | deprecated | vitalia-fase2-camila-reactivar | camila |
| adrian-reengagement-tool | slice-1-superseded | deprecated | vitalia-fase2-camila-reactivar | camila |
| referrals-leaderboard | slice-1-superseded | deprecated | vitalia-fase2-camila-multiplicar | camila |
| lucas-daily-analysis | slice-1-superseded | deprecated | vitalia-fase2-lucas-resultados | lucas |
| attribution-matrix-4-origins | slice-1-superseded | deprecated | vitalia-fase2-lucas-resultados | lucas |
| lucas-recommendation-tool | slice-1-superseded | deprecated | vitalia-fase2-lucas-lanzar | lucas |
| lucas-stage-recommendations | slice-1-superseded | deprecated | vitalia-fase2-lucas-lanzar | lucas |
| oauth-meta-google-ads | slice-1-superseded | deprecated | vitalia-fase2-config-conexiones | config |
| wizard-brand-studio-slice-1 | slice-1-superseded | deprecated | vitalia-fase2-lisa-marca | lisa |

### Infra y service stories (no stories F2 de agente)

| cap_id | ui_paradigm | story_lateral | nota |
|---|---|---|---|
| payment-gateways-latam-recurring | slice-1-superseded | vitalia-payment-adapter-mvp | service story en refining |
| booking-widget-embed | slice-1-superseded | — | widget standalone; sin F2 story directa aun |
| prepaid-booking-advisory-locks | slice-1-superseded | vitalia-fase2-valeria-agenda | wired parcialmente en F2-S1 |
| medical-guardrails | slice-1-superseded | — | BE infra; sin F2 UI story directa |
| medical-agentic-tools | slice-1-superseded | — | BE infra; sin F2 UI story directa |
| medical-safety-guardrails | slice-1-superseded | — | BE infra; sin F2 UI story directa |
| eval-goldens-slice-1 | slice-1-superseded | — | test infra; sin F2 UI story directa |
| k8s-admin-deployment | slice-1-superseded | — | infra K8s; sin F2 UI story directa |
| medical-kb-rag | slice-1-superseded | — | BE RAG; sin F2 UI story directa |

---
*T-3 actualizado manualmente · 2026-05-29 · computado por scripts/compute_capability_status.py · generado originalmente por scripts/build_live_reconciliation_matrix.py*
