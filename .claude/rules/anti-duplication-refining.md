# Anti-Duplication — Refining Phase (extends anti-duplication.md)

> **Slim stub (context-rot pass 2026-05-30 · materializada single-brand 2026-07-31).** Scan verbatim ejecutable + decision matrices completas + tabla fuentes prior-art + enforcement layers en `docs/rules-detail/anti-duplication-refining.md` — load on-demand al refinar. **Origen:** 2026-05-27. **Complementa:** `anti-duplication.md` (EJECUCIÓN — esta cubre REFINAMIENTO).

## Regla cardinal

ANTES de refinar/diseñar/arquitecturar una story nueva, `/pm-vitalia`, `/po-ux`, `/po`, `/ux-agentico`, `/architect` MUST correr el **Step `prior-art-scan`** (grep vitalia + engine `core/luana-core-*` + snapshot histórico) y documentar el resultado en el artifact:
- `/pm-vitalia` → `## Prior art scan` en checkpoint
- `/po-ux`/`/po`/`/ux-agentico` → `## Prior art applied` en spec/design
- `/architect` → `## Prior art audit` en 03-arch

Detecta: (1) pattern ya shipped en vitalia, (2) engine abstraction → consumir vía import NO recrear, (3) feature parecido en el snapshot histórico → lift candidate, (4) learning previo → aplicar.

## Cuándo carga el detalle (`docs/rules-detail/anti-duplication-refining.md`)

- Arranque de cualquier refining/design/arch → copiar el scan verbatim + correrlo
- Duda sobre `cap_change_type` (new/fix/extend/derive) vs prior-art → decision matrix v2
- Necesitás la tabla de fuentes prior-art REALES (vitalia = live; snapshot pre-multibrand = frozen, NO prod)

## Decision matrix (resumen)

Engine cubre 100% → CONSUMIR import · 60-99% → EXTEND herencia · patrón útil transversal → lift a `core/` (flujo engine de `/pm-vitalia`) · vertical-specific → Extension SDK EP-N · net-new → from scratch documentando scan.

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Refinar sin grep engine + vitalia (sólo el módulo propio → riesgo recrear)
- ❌ Documentar "prior art scan: clean" sin haber corrido el grep verbatim
- ❌ Lift candidate detectado + no llevarlo al flujo engine de `/pm-vitalia` (pollution per-módulo silenciosa)

## Referencias

- `docs/rules-detail/anti-duplication-refining.md` — **scan verbatim + matrices + fuentes + enforcement**
- `.claude/rules/anti-duplication.md` · `.claude/rules/learning-capture.md`
