# Vitalia — product SSoT

Owner: `/pm-vitalia`. Patrón hereda de Luana core (paradigm v4 — 10 estados macro). Detalle paradigma: `docs/process/pm-redesign-2026-05.md`.

## Estructura

| Path | Contenido | Owner |
|---|---|---|
| `BACKLOG.md` | Auto-gen, vista 10 estados | `make portfolio` |
| `checkpoint.md` | State global del brand | `/pm-vitalia` |
| `outcomes/` | Épicas brand-specific | `/pm-vitalia` |
| `stories/{id}/` | Work units (state idea→done) | `/pm-vitalia` + handoffs |
| `capabilities/{module}/` | Capacidades shipped | `/pm-vitalia` ratifica al merge |
| `modules/` | Per-module narrativa brand-specific | `/pm-vitalia` |

## Workflow

Idéntico a Luana paradigm v4 (3 conversaciones: Discovery+Ready / Autonomous Build / Review+Merge). Detalle en `/pm-vitalia` SKILL.md.

## Cross-references

- Cores consumidos: ver `vitalia/config/brand.yaml` y `vitalia/backend/pyproject.toml`
- Promotion candidates: `vitalia/docs/learnings/` con `promotable_candidate: yes`
- Vista master: [docs/portfolio/vitalia.md](../../../docs/portfolio/vitalia.md)
