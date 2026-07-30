# PII Sanitisation

**Origen:** HB-18 2026-06-01 — el gate PII existía (pre-commit §8/§9) pero los scanners no existían y la referencia canónica colgaba a un tile Tessl inexistente. Esta rule es el hogar real de la guía PII (reemplaza el pointer `@AGENTS.md → Tessl pii-sanitisation`).

## Regla cardinal

PII (nombres reales, emails reales, teléfonos reales, DNI/RFC/CURP/cédula reales, direcciones, historia clínica) **NUNCA** sale en una respuesta de API ni se persiste en datos de eval/observabilidad sin sanitizar. Tres superficies, tres mecanismos:

| Superficie | Mecanismo | SSoT |
|---|---|---|
| **Respuestas de API** | `response_model=<DTO>` en CADA route — el DTO whitelistea los campos que salen; PII no incluida nunca llega al cliente | `.claude/rules/backend-ddd.md` (DTO thin + `response_model=`) · arch test backend `response_model` mandatory |
| **Observabilidad agentic** (trazas, llamadas LLM) | `sanitize_payload(...)` ANTES de persistir cualquier payload | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py::sanitize_payload` (shared — NUNCA reimplementar local, ver `anti-duplication.md`) |
| **Datos de eval** (tenant seeds + sales_agent goldens) | synthetic-first — cero PII real; gate pre-commit §8/§9 corre los scanners contra el dir completo | `scripts/scan_seed_pii.py` (whitelist-aware) · `scripts/scan_goldens_pii.py` (strict) · `scripts/_pii_scan_lib.py` |

## Convención synthetic-first (datos de eval)

Los fixtures usan placeholders que los scanners tratan como limpios por construcción:
- Emails → `usuario@example.com` / `@example.*` (NUNCA gmail/hotmail/yahoo/outlook/icloud/… reales)
- Teléfonos → código de país sintético `+99` (ej. `+99 0 1234 5678`), NUNCA `+51/+52/+57/…` reales
- IDs nacionales → dígitos fake (ej. DNI `"12345678"`) — los scanners NO flaggean runs de dígitos pelados

**Si el scanner bloquea un valor legítimo público** (seeds solamente): agregarlo a `{brand}/backend/tests/fixtures/eval/tenants/.eval-whitelist` (un término literal por línea, `#` comenta) con justificación. **Goldens = sin whitelist** (invariante synthetic-first, spec D10): cualquier PII real en un golden es un bug, se reemplaza por sintético.

## Límites conocidos de los scanners (v1, HB-18)

Detección conservadora (alimenta un HARD gate → no debe falso-bloquear fixtures sintéticos). Cubre 2 vectores de alta confianza: **email en dominio de consumo real** + **teléfono en formato internacional con código de país real** (excluyendo patrones sintéticos). Fuera de scope v1: teléfonos en formato nacional sin `+CC`, nombres reales en texto libre (false-positives sobre DNIs sintéticos y nombres placeholder en español). El bar real sigue siendo la disciplina synthetic-first del autor; el scanner es la red de seguridad.

## Anti-patterns prohibidos

- ❌ Route sin `response_model=` (PII puede filtrar campos del modelo SQLA) → arch test FAIL
- ❌ Persistir payload de traza/LLM call sin `sanitize_payload(...)`
- ❌ Reimplementar sanitización PII local en vez de importar la shared de `core/luana-core-observability` (ver `anti-duplication.md`)
- ❌ PII real en seed/golden YAMLs (gmail/+51/…) — usar placeholders sintéticos
- ❌ `--no-verify` para saltar el gate PII (prohibido por `git-safety.md`)

## Referencias

- `.claude/rules/backend-ddd.md` — DTO thin + `response_model=`
- `.claude/rules/anti-duplication.md` — `sanitize_payload` shared (inventario engine)
- `scripts/{scan_seed_pii.py,scan_goldens_pii.py,_pii_scan_lib.py}` — scanners (HB-18)
- `scripts/git-hooks/pre-commit` §8 (seeds) · §9 (goldens) — gate
- `@AGENTS.md` § Key Constraints — PII sanitisation 1-liner
