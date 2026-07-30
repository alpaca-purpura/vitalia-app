# Propuesta · Ver los capabilities en niveles (que Chris lea la verdad, auto-mantenida)

> **Pedido (Chris 2026-06-06):** el "✨ Qué puedo hacer" del cap es muy ligero; cada Gherkin es
> un caso de uso y no lo veo; no veo las reglas de negocio implementadas. ¿Cuál es la mejor forma
> de que YO (humano) sepa qué hay — sin tener que narrarlo yo, saliendo de lo que se auto-construye
> y auto-mantiene? Referencia: Diátaxis. Idea: más "niveles", casos de uso tipo RUP. Garantía dura:
> **debo estar seguro de que Claude lo mantiene sin que yo se lo pida.**
> **Owner:** `/pm-luana` (cross-cutting: cockpit + capability-protocol). **Estado:** propuesta para ratificar.

## TL;DR (el reframe — antes de tomar literal lo que pediste)

**Lo que querés ver YA EXISTE en el dato y YA lo mantiene el proceso. El cockpit simplemente lo
esconde.** No hay que inventar una capa de docs nueva que yo narre; hay que (1) **destapar** lo que
ya está, (2) **estructurarlo en niveles** legibles, y (3) **cerrar los gates** que faltan para que no
pueda quedar viejo. Esa es la garantía de mantenimiento: no es "Claude se acuerda de actualizar
docs", es "el proceso lo produce y lo gatea en cada merge".

## 1 · Hallazgo verify-first (la causa de tu queja)

Revisé el dato y el código del cockpit. La cap `lisa-marca` (tu ejemplo) **ya tiene, hoy, en su YAML**:

| Dimensión | Qué hay en lisa-marca.yaml | Tu queja que resuelve |
|---|---|---|
| `scenarios` | **13 casos de uso** (`actor` + `given/when/then` + `e2e_test` + `verified_real` + `edge_cases`) | "cada Gherkin es un caso de uso y no lo veo" |
| `business_rules` | **3 reglas** (`rule` + `enforcement` + `code_ref` + `severity` + `audit_trail`) | "no veo las reglas de negocio implementadas" |
| `access` | entry_points (path + navegación + roles) | "cómo se llega / quién entra" |
| `related_capabilities` | `depends_on` (de qué depende) | "cómo se conecta" |

**Pero el cockpit no las muestra.** Causa exacta: `tools/luana-cockpit/lib/cap-ledger.ts::readCapability`
(que usa el endpoint del cap-drawer, `app/api/capabilities/[module]/[cap]/route.ts:45`) mapea un set
**fijo y viejo** de campos y **dropea** `scenarios`, `business_rules`, `access`, `related_capabilities`.
El `Capability` type SÍ los declara; el loader nunca se actualizó cuando se agregaron (v3.2). Por eso
"✨ Qué puedo hacer" cae al `user_facing_description` (1 frase) y las secciones de reglas/acceso/escenarios
nunca pueblan. **Es un bug de passthrough (~4 líneas), no un sistema faltante.**

→ Conclusión: la mitad de tu pedido se resuelve **mostrando lo que ya tenés**. La otra mitad es
estructurarlo en niveles + gatear su frescura.

## 2 · El modelo de niveles (Diátaxis + casos de uso RUP, mapeado al dato real)

Tu instinto es correcto: el cap es un cruce **producto ↔ técnico**, y Diátaxis ordena por **altitud de
intención**. No necesitamos las 4 cajas literales de Diátaxis (Tutorial/How-to/Reference/Explanation);
necesitamos las **altitudes**, y cada una ya tiene su dato:

| Nivel (altitud) | Pregunta humana | Diátaxis | RUP | Sale de (dato real, auto-mantenido) |
|---|---|---|---|---|
| **N0 · Qué es** | "¿qué tengo, en una frase?" | Explanation | — | `user_facing_name` + `user_facing_description` |
| **N1 · Qué puedo hacer** | "¿qué casos de uso resuelve?" | How-to | **Use case** (actor + flujo) | `scenarios[]` narrados (no Gherkin crudo: "El admin define la voz y tono" + given/when/then colapsable + edge_cases) |
| **N2 · Bajo qué reglas** | "¿qué reglas de negocio aplica y dónde se enforced?" | Reference | Business rules | `business_rules[]` (rule + enforcement + `code_ref` + severity) |
| **N3 · Quién y por dónde** | "¿quién entra, en qué ruta?" | Reference | Actors + UI | `access.entry_points` (path + navegación + roles) |
| **N4 · Dónde vive / cómo se conecta** | "¿qué código, qué endpoints, de qué depende?" | Reference | Realization | `dev_preview` (route/component/endpoints) + `related_capabilities.depends_on` + archivos código + validación bidireccional |

**Caso de uso al estilo RUP, materializado:** cada `scenario` = un caso de uso (un `actor`, un flujo
`given→when→then`, `edge_cases` = flujos alternativos). El cockpit lo muestra como **una tarjeta legible
por caso de uso**, con un **badge de verdad** por caso:

- ✅ **verificado en vivo** (`verified_real: true` + `e2e_test` apunta a un spec que pasa)
- 🟠 **declarado, con test** (`e2e_test` existe, `verified_real` no)
- ⚪ **declarado, sin test** (sin `e2e_test`) → deuda visible

Lo mismo por **regla de negocio**: muestra `enforcement` + `code_ref` → ves *dónde está implementada*.
Si una regla no tiene `code_ref` → 🔴 "regla sin enforcement" (= tu "no veo si está implementada",
respondido con evidencia, no con fe).

> Esto te da exactamente lo que pediste: **leés los casos de uso (qué puedo hacer) + las reglas (bajo
> qué condiciones) + el estado de implementación/verificación de cada uno**, en un solo drawer, en
> niveles que podés expandir/colapsar.

## 3 · La garantía de mantenimiento (lo que más te importa: "sin que yo te lo pida")

> **★ Corrección honesta (verify-first 2026-06-06, pedido de Chris "probá que de verdad se auto-mantiene").**
> Mi versión inicial de esta sección **sobreestimó**. La verdad, trazada en el código real:
>
> | Aspecto | ¿Gateado de verdad HOY? |
> |---|---|
> | Cap FILE existe + formato + en el mapa | ✅ **SÍ, mecánico HARD** (`new_cap.py` scaffold + cap_doctor G1-G7, HB-51, pre-commit vitalia/comunify) |
> | scenarios/business_rules **CONTENIDO** (los casos de uso) | ❌ **NO auto-generado** — lo escribe `/po-ux`/`/po` en `01-spec` y `/pm-{brand}` lo **embebe verbatim al merge** (paso MANUAL de skill). **Sin gate de presencia**: hay 39 caps `live`+`user_visible`+**0 scenarios** sin bloquear |
> | scenario ↔ test (link) | ✅ SÍ pero solo **existencia** (`cross_check_3`: el path del `e2e_test` existe + tiene patrones — NO que pase, NO que el texto coincida) |
> | scenario cobertura vs spec | 🟡 en AUDIT, story-scoped (`gherkin-matrix Phase D`) — corre cuando la story pasa por `/auditor`, compara spec↔tests, NO cap↔código |
> | scenario **accuracy** vs comportamiento real | ❌ **SIN GATE** — un cap puede mostrar un caso de uso lindo pero mentiroso si el código cambió sin tocar ese cap |
> | `verified_real` (badge "verificado live") | ❌ **decorativo** — 0 lecturas en scripts/skills |
>
> **Conclusión honesta:** el cap es **producido por el proceso** (skills lo escriben en pasos definidos) y su
> **estructura está blindada mecánicamente**; pero el **CONTENIDO es autoría manual gateada solo para
> cobertura-en-audit + existencia-de-link, NO para presencia ni accuracy continua**. La garantía "sin que me
> lo pidas" hoy es **disciplina de proceso** (yo corriendo los skills bien en cada story), **no** un generador
> code→cap auto-sincronizado. Eso es exactamente lo que **F2 (gates G8/G9 + accuracy)** convierte en mecánico.
> Gaps registrados: **HB-56** (presencia) · **HB-57** (accuracy) · **HB-58** (`verified_real`).

La tabla de abajo es el OBJETIVO (lo que cada nivel DEBERÍA tener como guardián); la columna "gate NUEVO"
marca lo que falta construir para que la garantía sea real y no aspiracional:

| Nivel | Quién lo mantiene current (gate EXISTENTE) | Qué falta cerrar (gate NUEVO propuesto) |
|---|---|---|
| N0 Qué es | `R · reconcile` (Fase F.3): `/pm-{brand}` reconcilia la cap a la realidad antes del merge | **G8**: cap `live` + `user_visible` SIN `user_facing_description` → FAIL (hoy 0 en vitalia, lo blindamos) |
| N1 Casos de uso | `cross_check_3` HARD (scenario → e2e test) + auditor **Phase D gherkin-matrix** (cada regla → scenario → PASS/MISSING) | **G9**: cada `business_rule` debe tener ≥1 `scenario` que la ejerza (ya es la gherkin-matrix; la volvemos gate de cap, no solo de story) |
| N2 Reglas | `01-spec § Business rules` → backfill a la cap en el merge | **G10**: `business_rule` sin `code_ref` o sin `enforcement` en cap `live` → WARN→FAIL escalable |
| N3 Acceso | `cross_check_4` (access role → @decorator) — ya corre | (sano; el V1 de hoy = 1 caso flag, ya ruteado a bugfix) |
| N4 Código/deps | `cap_doctor` G1-G7 (paths existen, headers resuelven, cockpit-readable) | (sano post-HB-51) |

**Por qué te podés fiar:** el dato que vas a leer en el cockpit es el **mismo** que el auditor y los gates
ya exigen para dejar pasar una story a `done`. Si yo no actualizo los scenarios/reglas al construir,
**la story no mergea** (cross_check_3 + gherkin-matrix Phase D + R-reconcile lo bloquean). Es decir: el
cockpit se vuelve la **superficie de lectura de una verdad que el pipeline ya gatea** — no una doc paralela
que se desincroniza. Eso es "auto-construido + auto-mantenido sin que me lo pidas", concreto.

Y lo blindo más: agrego al `/auditor` y a la rule #37 que **"el cap entrega N0-N4 completos"** sea parte
del DoD de toda story user-visible (ya casi lo es vía gherkin-matrix; lo hago explícito).

## 4 · Plan por fases (de barato y visible-ya, a blindado)

| Fase | Qué | Costo | Resultado |
|---|---|---|---|
| **F0 · Passthrough** | `readCapability` pasa `scenarios`/`business_rules`/`access`/`related_capabilities`; el cap-drawer ya tiene las secciones (`ScenariosSection`/`BusinessRulesSection`/`AccessSection`) — solo no reciben dato | ~1 archivo, ~10 líneas | **Hoy mismo ves los 13 casos de uso + 3 reglas de lisa-marca** en el cockpit. Sin narrar nada. |
| **F1 · Niveles + badges** ✅ **BUILT 2026-06-06 (P3)** | `CapLevel` colapsable (`<details>` nativo) reordena el drawer en N1→N4 (N0 = card «Cómo verlo»); badge de verdad por scenario (✅ verified_real / 🟠 e2e / ⚪ ninguno · `lib/cap-badges.ts`, 4 tests) + por regla (🟢 code_ref / 🔴 sin enforcement); N1/N2 abren, N3/N4 colapsan. tsc + 132/132 cockpit. | ~5 archivos | El drawer pasa de "ficha técnica plana" a "ficha de producto navegable por niveles, con la verdad de verificación a la vista" |
| **F2a · Gate de PRESENCIA** ✅ **BUILT 2026-06-06** | **G8** (live+visible ⇒ `user_facing_description`) + **G9** (live+visible ⇒ ≥1 scenario) en `validate_code_cap_bidirectional` + cap_doctor + machinery CHECK 11 (negative tests con dientes) + HARD pre-commit §5e | ~4 archivos | **Imposible que una cap `live` user-visible vaya sin descripción ni casos de uso.** 0 violaciones hoy (vitalia 13/13); bloquea futuras. machinery 72/0 |
| **F2b · Gate de ACCURACY** (HB-57) — **★ P1 partial-built 2026-06-06** | mecanismo REAL: `mutation_gate.py --cap <id>` (surface del cap vía `_code-index.json`, diff-scoped) + **mutmut instalado** (BE crítico; Stryker FE deferred). El "live⇒e2e PASÓ" hard es **data-blocked** (135/139 live sin `verified_real`, 33 sin e2e en vitalia) → `cap_doctor --accuracy` MIDE la deuda (advisory) → backfill al carril L4. NO mass-invent. | scripts + tool install | El accuracy de CÓDIGO ya se caza (mutación); el de scenarios-sin-test queda MEDIDO, no oculto |
| **F2c · DoD N0-N4** ✅ **BUILT 2026-06-06 (P4)** | `capability-protocol.md §14` (modelo N0-N4 = SSoT, mapeado a campos existentes + badge de verdad + DoD) + auditor SKILL Phase D bullet "Cap N0-N4 completo" + rule #37 obligación `/auditor` + referencias | 1 rule + skill + protocol | El modelo de niveles queda como **proceso**, no favor de sesión |
| **F3 · Backfill dirigido** | Las ~39 caps v3.1 sin scenarios → backfill desde su `01-spec` archivado (SOLO con señal real; las que no la tengan, las marco para que las completes) | incremental, L4 del CIL | Cobertura pareja; sin mass-invent |

**F0 es el quick-win:** ratificás y en la misma sesión ves el efecto real (te lo verifico live en :4002,
Chrome MCP, captura). F1-F3 = waves dedicadas (no mid-feature, regla de oro HLP).

## 5 · Lo que NO recomiendo (para que sepas qué descarté y por qué)

- ❌ **Una capa de docs Diátaxis literal separada** (4 archivos tutorial/how-to/reference/explanation por
  cap) → se desincroniza, la narrás vos o yo a mano = exactamente lo que querés evitar. El dato vive en
  la cap (1 SSoT) y se proyecta en niveles.
- ❌ **Tutoriales auto-generados** (el cuadrante "Tutorial" de Diátaxis) → eso es onboarding/learning, no
  pertenece al cap; mezclarlo ensucia el SSoT.
- ❌ **Re-narrar Gherkin crudo en la UI** → ilegible. Se narra el scenario (`name` + flujo colapsable).

## 6 · Decisión para vos

1. **¿Arranco F0 ya** (passthrough → ves tus 13 casos de uso + 3 reglas hoy, verificado live)? — recomendado.
2. **¿Ratificás el modelo de 5 niveles N0-N4** (Diátaxis-altitud + caso-de-uso-RUP) como la forma canónica
   de leer un cap?
3. **¿Ratificás los gates G8/G9/G10** como la garantía de que no se pone viejo (F2)?

Lo formal (rule #37 + capability-protocol + skill auditor) lo cemento cuando ratifiques el modelo, para
que quede como proceso — no como favor de esta sesión.
