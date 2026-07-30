---
story_id: vitalia-tenant-currency-config
created_at: 2026-06-17T01:15:00-05:00
last_modified: 2026-06-17T01:15:00-05:00
notes_count: 0
refs_count: 1
conversation_count: 1
---

# chris-input.md · vitalia-tenant-currency-config

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales** (mantener el orden + emojis para que parser + cockpit funcionen):
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-17
Chris (verbatim, durante verify de lisa-servicios): "me doy cuenta que has puesto como moneda ARS, nunca conversamos de eso, debería ser la moneda default del tenant, crea una historia para que el tenant/clinica pueda cambiar su moneda por default primaria y secundaria. Este tipo de moneda debe provenir de allí, o sea debe ser propio del tenant. Dicho esto, estos deben ser seleccionados de acuerdo a ISO 4217. Pon a los tenants de nuestras pruebas con PEN"

## 📎 Referencias

- **📖 story-ref** · `vitalia-fase2-lisa-servicios` (origen — Chris detectó el ARS verificándola)
  > El ARS NO era bug de esa story; salió del fallback hardcoded de useTenantLocale.ts.

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-17 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO (story creada · intake-handshake)

Story creada en `state=idea`. cap_target=`config.currency`, cap_change_type=`null` (idea).

**Intake-handshake (dónde va + qué ya existe + empuje):**
- **Zona/caja:** Plataforma → Configuración → Cuenta. La moneda es un ajuste del espacio del tenant, operado a mano (no de un agente) → árbol de paradigma da Plataforma/Configuración. ✓
- **Extiende-o-nuevo:** EXTIENDE infra existente. La moneda **primaria YA existe** en engine iam (`tenant.default_currency` + settings GET/PATCH). NET-NEW: moneda **secundaria**, selector **ISO 4217**, UI de settings, y wire del FE al source canónico (matar fallback ARS) + test tenants PEN.
- **Qué ya existe (no recrear):** `core/luana-core-iam` settings + `core/luana-core-platform` locale.py/currency.py (`FALLBACK_CURRENCY="USD"`). El fallback ARS vive en `vitalia/frontend/src/hooks/useTenantLocale.ts` (`VITALIA_DEFAULT_LOCALE`) — ese hook **ya tenía un TODO** apuntando a esta misma story ("wire actual tenant locale endpoint… follow-up story").
- **Empuje (💡 PROPONE):** la moneda **secundaria** + validación ISO 4217 en `core/luana-core-iam` es un **engine change cross-brand** → requiere **lift /pm-luana** (no se hace brand-local). Esta story vitalia owns el FE + el wiring + el test-data PEN; el campo `secondary_currency` del engine se coordina con /pm-luana en refinement. Lo registré en `checkpoint.md::engine_coordination`.

**Sobre "test tenants con PEN" (tu instrucción directa):** está scopeado como deliverable de la story (seed `default_currency` PEN + el `--clerk-sync` debe pushear `currency` a `publicMetadata`, que hoy NO lo hace → por eso el FE caía a ARS). Es un quick-win que se puede fast-trackear vía /dev-team ANTES de refinar el resto, para que dejes de ver ARS al verificar. **¿Lo fast-trackeo ya, o refinamos la historia completa primero?**

**Nota:** el ARS que viste NO bloquea tu signoff de lisa-servicios (es cosmético/ortogonal a los 5 findings G2 que ya están construidos + gate-green).
