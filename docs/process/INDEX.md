# Process — Reglas transversales del harness

**Qué es:** reglas de proceso que aplican a cualquier PI/sprint/story. Bound contract entre Chris + Claude + sub-agents.

## Archivos

| Archivo | Owner | Cuándo leer |
|---|---|---|
| `lifecycle.md` | `/pm` | Modelo 4-ejes (Release→Story→Capability→Scenario) — roadmap fases SDD |
| `ticket-states.md` | `/architect` + `/dev-team` + `/auditor` | Antes mover ticket de estado |
| `checkpoint-protocol.md` | todos | Resume cualquier sesión |
| `parallel-sessions-protocol.md` | todos | Multi-instancia Claude (M1-M14) |
| `learnings.md` | `/pm` | Append-only post-incident |
| `harness-lifecycle.md` (HLP) | Chris + Claude | Mantener el harness (skills/rules/agents/hooks/cockpit/templates) — captura sin fricción + lotes + auditoría periódica |
| `harness-backlog.md` | Chris + Claude (`/harness-issue`) | Tracker vivo de deficiencias del harness (HB-N) |
| `release-protocol.md` | `/pm` | Entidad Release SSoT — reemplaza outcome+phase legacy |
| `capability-protocol.md` | `/architect` + `/pm` | Schema cap + story↔cap doctrine + CONN anti-isla (Critical Rules #28/#32/#33) |
| `story-closure-gate.md` | `/dev-team` + `/auditor` + `/pm` | Gate developed→reviewing→done + WIP cap module-scoped (Critical Rule #17) |
| `chris-input-protocol.md` | todos | Protocolo chris-input.md por story (Critical Rule #30) |
| `cockpit-permissions.md` | Chris + `/pm` | Whitelist transiciones Chris vs Claude en el cockpit (Critical Rule #31) |
| `spec-mapa-funcional.md` | `/po-ux` + `/po` | Mapa funcional happy-path + bifurcaciones encima del Gherkin |
| `cap-deterministic-enforcement.md` | `/architect` + `/pm` | Enforcement determinístico del formato/estado de la cap (8 capas · 9 gates G1-G9 · HB-51) |
| `code-health-gate.md` | `/dev-team` + `/auditor` | Gate de salud del código (ruff/jscpd/vulture/pip-audit · HB-61) |
| `continuous-improvement.md` | `/pm-luana` | Router CIL 4 carriles (L1 backlog · L2 learnings · L3 tech-debt · L4 cap-desfasada) — NO un 5º store |
| `tech-debt.md` | `/pm` + `/auditor` | Carril L3 del CIL — deuda técnica/infra (apunta a learning-capture / harness-backlog) |
| `contributing.md` | todos | Convenciones de contribución (stack / quality / Spanish-neutro) |

## Reglas globales

- **Anti-teléfono-descompuesto.** Subagents devuelven `done -> path/to/artifact.md`. NO payload en chat.
- **Tool subtraction (Vercel).** Cada subagent tiene tools mínimas. Documentación > tooling.
- **Resume protocol.** Cada nivel (PI/sprint/story) tiene `checkpoint.md`. Cualquier sesión retoma desde `next_action`.
- **Ticket state transitions** son explícitas (ver `ticket-states.md`).
- **Single owner por artefacto.** Si 2 agents tocan mismo archivo → conflict → escalate Chris.
- **Self-evaluation prohibida.** Builder no aprueba su propio trabajo. Auditor separado.
- **Auditor con autoridad limitada.** Fixea triviales (lint/typo). Diseño/security/arch → escala.
- **Spanish neutro UI strings.** No voseo (excepto sales_agent voz tenant).
