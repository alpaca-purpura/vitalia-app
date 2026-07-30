# Cap format — enforcement determinístico end-to-end (resolución definitiva del proceso flaky)

> **HB-51 · solución fuerte/máxima.** Pedido Chris 2026-06-05: *"resolver de una vez por todas este proceso flaky"*. Decisión base: **(b)** `functional_area` como alias del cap_id (cero churn de producto). Este doc es el **diseño completo** del enforcement determinístico que hace **imposible** entregar una cap en formato/estado incorrecto. Se construye como **tanda de harness dedicada** (verify-first), NO a mano mid-feature.
>
> **Origen:** reconciliación cap `inbox.adrian-inbox` — la cap canónica del inbox NO existía (headers `# cap: inbox.adrian-inbox` huérfanos), edité la cap slice-1 equivocada, y la caja del Inbox salía vacía en el cockpit. Nada falló: el error fue silencioso. SSoT relacionado: `docs/process/capability-protocol.md`, HB-43 (cap-as-locator), `scripts/{resolve_cap,validate_code_cap_bidirectional,generate_code_to_cap_index}.py`.

## Principio rector

**El formato de una cap sale del criterio de Claude (prosa de un skill) y pasa a CÓDIGO DETERMINÍSTICO.** Un skill *aconseja*; un **generator** *produce* el formato y un **gate** *lo enforce fallando el commit*. El gate es lo único que "nunca se equivoca" porque es independiente del modelo. Defensa en profundidad: si una capa se salta, la siguiente lo caza.

### Por qué era flaky (las 3 causas raíz, para que el diseño las mate todas)

1. **Convención dual en el código:** headers en forma `module.slug` (`crm.adrian-embudo` ✅ resuelve a YAML) Y en forma `functional_area` (`adrian.inbox`, 68+ archivos, NO resuelve). Al imitar precedentes, ambas parecían válidas. → **mata: Capa 1 (resolver único two-way) + Capa 4/G1.**
2. **`cap_target` ambiguo** (`adrian.inbox` → no resuelve a un path único; footgun HB-43). → **mata: Capa 1 + Capa 2 (generator deriva el cap_id).**
3. **Nada falla:** no hay gate para "header → cap inexistente", "área viva sin cap canónica", "cap sin hogar en el mapa". → **mata: Capa 4 (6 gates HARD).**

## Las 8 capas (máximo)

### Capa 1 — Llave canónica única + alias registrado · resolver dos-vías

> **★ Corrección verificada contra data (build 2026-06-05).** El diseño original decía que
> `functional_area` resuelve a **EXACTAMENTE un** cap_id. **Eso es falso en la data real:**
> `functional_area` es la **AREA del cockpit** (`${box}.${area}`) y es **1:N** — ej.
> `configuracion.admin` → 5 caps live, `plataforma-tecnica.platform` → 5, `observabilidad.observability` → 3.
> Es el mismo modelo que usa el cockpit (`capsByFunctionalArea` agrupa N caps por área). El caso
> `adrian.inbox` da 1 cap live SOLO porque las otras 2 son deprecated/superseded. Implementación final:
> el resolver devuelve un **SET** y G1 pasa con **≥1** (no `==1`); `canonical_cap_id` aplica
> **live-filter** para el caso alias→cap-canónica. Esto preserva el GOAL (G1+G2 cazan el incidente,
> unifican las 2 convenciones) sin churn de producto.

- **`cap_id = {module}.{slug}`** (= `{parent-dir}.{slug}`) es la identidad canónica de toda cap.
- **`functional_area = {box}.{area}`** es el **alias/área registrado** (1:N): el set de caps de esa caja del mapa. `canonical_cap_id(area)` = la cap live non-superseded del área (1 si está bien formada).
- **`scripts/resolve_cap.py` es el ÚNICO resolver** (SSoT), **two-way** + por TIERS (identidad-exacta gana sobre alias/área):
  - `resolve_cap_ids(brand, token, live_only=False) -> set[cap_id]` — G1 pasa si ≥1.
  - `canonical_cap_id(brand, token) -> str|None` — alias → cap canónica (live-filter). Test: `canonical_cap_id("adrian.inbox") == canonical_cap_id("inbox.adrian-inbox") == "inbox.adrian-inbox"`.
  - `functional_area_of(cap_id)` · `cap_id_of(path)`. Formas-alias cubiertas (zero churn de las ~168 headers FE): `functional_area` · `{module}.{fa}` (`clinics.lisa.doctores`) · `{module}.{fa-dashed}` (`scheduling.mateo-agenda`).

### Capa 2 — Generator (cero hand-authoring)
- **`make new-cap MODULE=inbox SLUG=adrian-inbox`** (o `AREA=adrian.inbox` → deriva module/slug) · `scripts/new_cap.py`:
  - Deriva `cap_id`, valida que el `module` existe, que el `slug` es único, que la `functional_area` está en el SYSTEM-MAP.
  - **Scaffolds el YAML COMPLETO desde UN template canónico** (todos los campos required + `# TODO` markers de contenido + change_log[0] + dev_preview + code_pointers + regression_tests vacíos a llenar).
  - **REFUSE** si el cap_id ya existe (evita editar la equivocada).
  - Resultado: **schema-valid por construcción**. Claude NUNCA tipea el YAML a mano; corre el generator y llena el contenido.

### Capa 3 — Schema validation (pydantic / JSON-Schema)
- **`scripts/validate_caps_schema.py`**: modelo formal de la cap. Valida CADA cap: campos required, tipos, `status ∈ {live,beta,planned,deprecated,sunset,partial,wip}`, `module` válido, `functional_area` formato `{box}.{area}`, `change_log[].type` válido. **★ Parseo ESTRICTO** (`strict_parse_error`): rechaza claves duplicadas — PyYAML las tolera (last-wins) pero el cockpit (gray-matter/js-yaml) las RECHAZA → la cap queda invisible en el mapa. El validador es tan estricto como el consumidor real. Corre en **pre-commit**.

### Capa 4 — 9 gates HARD bidireccionales (pre-commit + pre-push)
Extender `validate_code_cap_bidirectional.py` (ya corre en pre-commit) con checks **HARD** (hoy solo cross_check_3 es HARD):

| Gate | Qué verifica | Qué hubiera cazado |
|---|---|---|
| **G1 · header-resuelve** | Todo `# cap:`/`// cap:` resuelve a una cap REAL (por cap_id O alias). Header → cap inexistente = **FAIL** | `inbox.adrian-inbox` header sin YAML |
| **G2 · área-viva-tiene-cap** | Toda `functional_area` `status: live` en SYSTEM-MAP tiene ≥1 cap live non-superseded = **FAIL** si 0 | **La caja Inbox vacía en el cockpit** |
| **G3 · cap-tiene-hogar** | Toda `functional_area` de una cap mapea a un `box.area` real del SYSTEM-MAP = **FAIL** | cap apuntando a un área inexistente |
| **G4 · paths-existen** | `e2e_test` + `code_ref` + `test_coverage` + `code_pointers` → todos existen en disco = **FAIL** | path inventado (anti-hallucination con dientes) |
| **G5 · superseded-válido** | `superseded_by` → cap real (live) = **FAIL** | cadena de supersesión rota |
| **G6 · map-coverage** | Toda cap `live` aparece en el mapa (su `functional_area` está cubierta por un box) = **FAIL** | cap huérfana invisible en el mapa |
| **G7 · cockpit-readable** | Toda cap parsea bajo YAML ESTRICTO (= gray-matter/js-yaml del cockpit · sin claves duplicadas) = **FAIL** | **15 caps vitalia con `map_box`/`last_modified` duplicado → ILEGIBLES por el cockpit → cajas vacías (incl. Inbox)** |
| **G8 · visible-tiene-descripción** | Toda cap `status: live/beta` + `user_visible: true` tiene `user_facing_description` non-placeholder = **FAIL** | cap de valor live sin QUÉ decir → «✨ Qué puedo hacer» cae a fallback vacío (HB-52/56) |
| **G9 · visible-tiene-scenario** | Toda cap `status: live/beta` + `user_visible: true` tiene ≥1 `scenario` = **FAIL** | cap de valor sin caso de uso verificable que el `cross_check_3` ate a un e2e (HB-56) |

> **G8/G9 (agregados 2026-06-05 · F2 cap-levels):** gates de **PRESENCIA forward-looking** — 0 violaciones hoy (vitalia/comunify/nicolify limpias) → bloquean SOLO regresiones futuras (una cap nueva no puede ir `live`+`user_visible` sin describir qué hace ni listar ≥1 caso de uso). El «≥1 scenario al merge» de `new_cap.py` deja de ser paper-rule y pasa a mecánico.

> **★ Lección 2026-06-05 (verify-the-real-consumer):** los gates Python pasaban (PyYAML tolera claves duplicadas) pero **el cockpit no mostraba la cap** (gray-matter/js-yaml las rechaza → la cap se dropea silenciosa). Un gate verde con el consumidor roto = el gate miente. G7 hace al validador tan estricto como el consumidor REAL. Misma clase que [[verification-real-not-200]]: verificar el path real, no el proxy.

### Capa 5 — Resolver único como SSoT (elimina la lógica paralela = causa raíz)
- **Hoy:** el mapa (`map-zones.ts`) resuelve por `functional_area`; el índice code↔cap (`generate_code_to_cap_index.py`) por `cap_id`. **Divergencia = la causa raíz.**
- **Fix:** `resolve_cap.py` es la única función de resolución. El index generator, el validador, el cockpit y el architect la consumen. **Una sola fuente de verdad de "qué cap es este header".**

### Capa 6 — Skill = puntero al generator (NO describe el formato)
- `docs/process/capability-protocol.md`, `/pm-vitalia` Fase F.3, `/architect` dejan de describir *"escribí el YAML así"* → **"corré `make new-cap`; NUNCA hand-authores una cap; llená el contenido en el scaffold"**. El skill apunta a la tool determinística, no al formato. (Es la lección recurrente: prosa advisory ≠ enforcement.)

### Capa 7 — Backstop CI/pre-push + harness audit
- Los 6 gates + schema corren en **pre-commit** (rápido, fail-fast) **+ pre-push** (full) **+ `/harness-audit-2026`**. Defensa en profundidad.

### Capa 8 — `make cap-doctor` (health report de un vistazo)
- Un comando (+ panel en el cockpit) que lista TODA la deriva en un reporte: orphan headers, áreas vivas vacías, caps sin hogar, paths rotos, supersesiones rotas. Chris ve la salud del mapa code↔cap sin clickear caja por caja.

## Acceptance criteria (con dientes — sin esto, no cuenta)

- **Negative test por gate:** cada gate (G1-G9) probado con un caso que DEBE fallar (header a cap inexistente → G1 RED; área live sin cap → G2 RED; path inventado → G4 RED; …). Un gate sin negative test que lo prueba en rojo **no cuenta**.
- **Reproducir el caso origen:** si se borra `capabilities/inbox/adrian-inbox.yaml`, el pre-commit DEBE fallar en **G1 + G2** (hoy pasa silencioso). Test de regresión del incidente.
- **`make new-cap`** produce un YAML que pasa schema + los 6 gates **sin edición manual**.
- **`resolve_cap.py`** two-way: `resolve("adrian.inbox").cap_id == "inbox.adrian-inbox"` y viceversa.
- **`make cap-doctor`** sobre vitalia: 0 deriva tras el backfill (las 168 headers forma-`functional_area` quedan **válidas por el alias** — NO se tocan).

## Orden de construcción (incremental, verify-first)

1. `resolve_cap.py` two-way + tests (la base de todo).
2. Schema model + `validate_caps_schema.py` + wire pre-commit.
3. **G1 + G2** (los que hubieran cazado ESTE incidente) + negative tests + el test de reproducción del origen.
4. `new_cap.py` generator + template canónico.
5. G3-G6 + negative tests.
6. Skill repoint (Capa 6) + `cap-doctor` (Capa 8).
7. Backfill: correr `cap-doctor` sobre vitalia + las otras marcas, arreglar la deriva pre-existente (sin tocar las 168 headers — el alias las cubre).

## Disciplina de ejecución

Tanda de harness **dedicada**, fuera de toda feature en curso (`docs/process/harness-lifecycle.md` § apply-pipeline): **verify-first** (la auditoría sobreestima — verificar cada claim), Sonnet edita / Opus sintetiza+ratifica / **Haiku commit por pathspec**, `SCOPE_GATE_SKIP`. Cada gate con **negative test con dientes** antes de declararlo hecho. NUNCA construir esto mid-feature.

## Estado de construcción (CONSTRUIDO 2026-06-05)

Las 8 capas construidas verify-first. SSoT ejecutable:

| Capa | Artefacto | Estado |
|---|---|---|
| 1 · resolver two-way | `scripts/resolve_cap.py` (`resolve_cap_ids`/`canonical_cap_id`/`functional_area_of`/`cap_id_of`) | ✅ + 23 tests |
| 2 · generator | `scripts/new_cap.py` · `make new-cap` (REFUSE si existe · scaffold schema-válido) | ✅ + tests |
| 3 · schema | `scripts/validate_caps_schema.py` (pydantic + `strict_parse_error` dup-key) · `make caps-schema-check` | ✅ + 13 tests |
| 4 · 9 gates G1-G9 | `validate_code_cap_bidirectional.py::run_cap_gates` (`--cap-gates-hard`) — **G7 cockpit-readable + G8/G9 cap-levels-PRESENCIA agregados 2026-06-05** | ✅ + negative test c/u + **test repro origen** (borrar cap inbox → G1+G2 RED) |
| 5 · resolver único | `generate_code_to_cap_index.py` → `resolved_cap_to_files` (unifica `adrian.inbox`+`inbox.adrian-inbox`) | ✅ |
| 6 · skill=puntero | `capability-protocol.md` + `pm-vitalia` F.3 + `vitalia/CLAUDE.md` → `make new-cap` | ✅ |
| 7 · backstop | pre-commit §5e + pre-push §4e (HARD vitalia/comunify · override `CAP_GATES_SKIP`/`CAP_GATES_PUSH_OVERRIDE`) | ✅ |
| 8 · cap-doctor | `scripts/cap_doctor.py` · `make cap-doctor` + cockpit `GET /api/capabilities/doctor` | ✅ (panel UI = follow-up) |

**Anti-rot:** `validate_machinery_consistency.py` CHECK 11 (borrar un gate/negative-test/script → CHECK RED). **OCP (W6 2026-06-09):** CHECK 11 **deriva** el set de gates de `def gate_gN_*` + del dispatcher `run_cap_gates` (no un literal congelado) con un piso G1-G9 → un **G10** futuro queda auto-cubierto (agregalo + dispatchalo + `test_g10_red` y CHECK 11 lo exige solo).

**Backfill realizado (vitalia → 0 deriva):** 1 header huérfano re-apuntado (`sales_agent.adrian-override-context` → `crm.adrian-embudo`, el wire servía al embudo) + 6 paths de cap corregidos (`middleware.ts`→`proxy.ts` ×3 · `features/valeria/…`→`features/mateo/…` · `brand_studio/_shared/auth/rbac.py`→`_shared/auth/rbac.py` · `sign-in/page.tsx`→`sign-in/[[...rest]]/page.tsx`) + **15 caps con clave duplicada deduplicadas** (`last_modified` ×14 + `map_box` ×1 inbox) — eran ILEGIBLES por el cockpit (cajas vacías, incl. Inbox). El síntoma que reportó Chris ("no veo la cap en Mapa/Adrián/Inbox") era esto: el gate Python verde, el cockpit roto → G7 cierra el agujero.

**HARD flip per-brand (decisión 2026-06-05):** vitalia + comunify HARD (cap-doctor 0); **nicolify + lupulo ADVISORY** — nicolify tiene 2 G6 (`shell-organism.shell-nicolify` + `platform.nicolify-brand-runtime-foundation` sin `functional_area` válida) que son **deuda de su rebuild** (caps estilo reconcile sin fence + SYSTEM-MAP all-`planned`); asignarles hogar es juicio de producto de `/pm-nicolify`, fuera del scope de esta tanda (no se hand-editan caps reconcile-managed). Cuando nicolify madure → agregarla a `CAP_GATES_HARD_BRANDS` en pre-commit §5e + pre-push §4e.

## Referencias
- `docs/process/harness-backlog.md` § HB-51 (este doc es su solución) · HB-43 (cap-as-locator, resolver origen)
- `docs/process/capability-protocol.md` — schema cap + dimensiones (Capa 6 lo repointa)
- `scripts/resolve_cap.py` · `scripts/validate_code_cap_bidirectional.py` · `scripts/generate_code_to_cap_index.py`
- `tools/luana-cockpit/lib/map-zones.ts` (consumidor del resolver, Capa 5) · `MapView.tsx`
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` (registro de áreas, fuente de G2/G3/G6)
- `.claude/rules/definition-of-done-live-verify.md` + HB-50 — la doctrina "advisory ≠ enforcement, el gate es lo que enforce"
