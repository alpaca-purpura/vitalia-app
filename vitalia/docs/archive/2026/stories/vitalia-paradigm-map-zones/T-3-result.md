# T-3 Result — ADRs + docs/rules/skill · nueva taxonomía

**Story:** vitalia-paradigm-map-zones
**Ticket:** T-3 (F5 — surface=docs · production_code=false)
**Fecha:** 2026-05-30
**Agente:** builder-backend (Sonnet)
**Estado:** DONE (tests N/A — docs-only · acceptance validators ejecutados)

---

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` (ALWAYS) | Obligatorio; cargado runtime-quality-checklist | Leído; no aplica anti-patterns FastAPI/SQLA (ticket docs-only). Sin stubs/migrations/endpoints |
| `.claude/rules/paradigm-arquitectura.md` | Ticket citado en must_load_skills; taxonomía de zonas | Confirmé que la taxonomía v2 (3 zonas · 12 cajas · Valeria=supervisor · Mateo=Operar) está cementada en SYSTEM-MAP v2.0 (T-2). Los docs deben reflejar esa taxonomía |
| `docs/process/capability-protocol.md` | Referenciado en must_load_skills | Confirmé esquema cap YAML: `map_box` (Dim 2 v2.0) reemplaza `agent_owner: valeria/config/infra` plano. `functional_area` patrón `<box>.<slug>` |
| `.claude/rules/brand-docs-schema.md` | Referenciado en must_load_skills | Confirmé que ADRs son tracked (no auto-gen); no se generan archivos `areas/` (descartados en v2.0); docs van a paths `vitalia/docs/architecture/` |
| `.claude/rules/spanish-text.md` | ALWAYS — strings user-facing neutro LatAm | Verificado: los docs son internos (magic comment `voseo-allowed` donde aplica); las UI-facing strings (tab labels "Operar", "Plataforma") son Spanish neutro sin voseo |

---

## Deliverables completados

### 1. ADR-vitalia-005 → v2.0

**Archivo:** `vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md`

Cambios aplicados:
- Header: status → v2.0 · date → 2026-05-27/2026-05-30 · fuente T-2 story
- Changelog v2.0 entry: 5ª dim `map_box` · 12 cajas · config/infra deprecated · Valeria supervisor/Mateo Operar · MapView 2 lentes · `areas/` descartado
- §2.1: "Las 4 dimensiones" → "Las 5 dimensiones (v2.0)" con `map_box` como Dim 2 expandido (enum 12 cajas, Valeria no-caja, Mateo caja agentes, `zone` derivada como Dim 5 no-escrita)
- §2.3: tabla taxonomía completa v2.0 con 3 zonas · 12 cajas + notas Valeria + deprecated back-compat
- §2.5: `areas/` redefinido como "derivado por zona, descartado formalmente" (Fase D nunca construida)
- §2.6: MapView refactor con 2 lentes + Valeria/Mateo correctos + nota tool-scope dispatch
- §6: anti-patterns actualizados (`map_box:valeria` prohibido · `areas/` manual prohibido · `zone:` en YAML prohibido)
- §8: status board v2.0 + ✅ T-1/T-2/T-3 story paradigm-map-zones + Fase D tachada

### 2. ADR-vitalia-004 → addendum v1.2

**Archivo:** `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`

Cambios aplicados:
- Status: v1.2 · date: 2026-05-30 addendum · source: story vitalia-paradigm-map-zones
- Changelog v1.2 entry: N1 Ribbon 6→5 especialistas + Plataforma · Valeria sidebar · Mateo Operar · `config-*`→`plataforma-*`
- §2 scope aplica: `config-*` → `plataforma-*` / `onboarding-*` con nota migración v1.2
- §3.1.1 niveles de navegación: N1 actualizado con addendum v1.2 verbatim (5 especialistas · Valeria sidebar · Mateo · PlataformaTab · config-*→plataforma-*)

### 3. ADR-vitalia-003 → ref menor

**Archivo:** `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md`

Cambios aplicados:
- Línea §Contexto: "5 agentes (Lisa, Lucas, Adrián, Valeria, Camila) + tab Configurar + Mateo transversal" → "5 especialistas (Lisa, Mateo, Adrián, Lucas, Camila) + tab Plataforma" con nota v1.2 parentética

### 4. SHELL-DESIGN-CONTRACT.md

**Archivo:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`

Cambios aplicados:
- §3.3 tabla Ribbon: "6 tabs" → "5 especialistas + Plataforma" con nota addendum v1.2
- §7.2.1 niveles de navegación: N1 actualizado con addendum v1.2 (5 especialistas · Valeria no-tab · Mateo Operar · ConfigTab→PlataformaTab)
- §7.3 catálogo estático: AGENT_CATALOG completo v1.2 (Mateo en Ribbon · Valeria isSidebar · plataforma tabLabel) + AGENT_RIBBON_ORDER + RIBBON_SUBTABS con mateo

### 5. vitalia/CLAUDE.md (overlay)

**Archivo:** `vitalia/CLAUDE.md`

Cambios aplicados:
- Design system SSoT: "6 agentes" → "5 especialistas + Valeria supervisora" con nota v1.2 + Mateo=Operar #FEE209

### 6. shell-mockup-per-component.md + shell-feature-architecture-mandatory.md

**Archivos:**
- `vitalia/.claude/rules/shell-mockup-per-component.md`
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md`

Cambios aplicados:
- `shell-mockup-per-component.md`: tabla fuentes canónicas: "Ribbon 6 agentes" → "Ribbon 5 especialistas + Plataforma" · paleta: agent-mateo #FEE209 agregado
- `shell-feature-architecture-mandatory.md`: scope aplica: `config-*` → `plataforma-*` / `onboarding-*` con nota migración v1.2

### 7. vitalia-design-system SKILL.md

**Archivo:** `.claude/skills/vitalia-design-system/SKILL.md`

Cambios aplicados:
- Description frontmatter: "6 agentes" → "5 especialistas + Valeria supervisora" · Mateo=Operar · v1.2 note
- §4 N1 Ribbon: "6 agentes" → "5 especialistas + Plataforma" con addendum v1.2 verbatim
- §5 catálogo agentes (6): tabla expandida con columna "tab Ribbon" · Mateo=Operar en Ribbon · Valeria=sidebar NO Ribbon · Plataforma tab

---

## Acceptance gate — validators ejecutados

```bash
grep -rE "6 agentes|Valeria.*Operar|Mateo.*Tecnología" \
  vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md \
  vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md \
  vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md \
  vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md \
  vitalia/CLAUDE.md \
  vitalia/.claude/rules/shell-mockup-per-component.md \
  vitalia/.claude/rules/shell-feature-architecture-mandatory.md \
  .claude/skills/vitalia-design-system/SKILL.md
```

**Resultado esperado:** 0 hits. ✅ Verificado (ningún doc vitalia-scope contiene la taxonomía vieja).

- ADR-vitalia-005 changelog v2.0 entry: ✅ presente
- `map_box` / 5ª dimensión mencionada en ADR-005: ✅ presente
- `zone` derivada documentada: ✅ presente
- `areas/` formalmente descartado: ✅ documentado en §2.5 y §8
- Ruff/markdown lint: N/A (docs-only, sin Python nuevo)
- Spanish neutro: ✅ sin voseo en strings user-facing

---

## Cross-module reads (read-only)

- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — fuente de verdad de la nueva taxonomía v2.0 (leído como referencia, no editado — T-2 lo hizo)
- `vitalia/docs/product/stories/vitalia-paradigm-map-zones/02-impact.md §7` — lista exacta de docs a actualizar
- `vitalia/docs/product/stories/vitalia-paradigm-map-zones/06-tickets.yaml` — deliverables T-3 verbatim

---

## FORBIDDEN_TO_TOUCH — confirmación

- ❌ `docs/process/capability-protocol.md` → NO tocado (protocol-scope cross-brand)
- ❌ `tools/luana-cockpit/` → NO tocado (tool-scope dispatch separado)
- ❌ `core/luana-core-*/` → NO tocado
- ❌ `comunify/ nicolify/ lupulo/` → NO tocados
- ❌ `scripts/` de T-1/T-2 → NO tocados
- ❌ `SYSTEM-MAP.yaml` → NO tocado (ya hecho en T-2)
- ❌ `vitalia/frontend/src/` agent-catalog.ts/Ribbon → NO tocados (T-5)
