# ADR-vitalia-009 — Autosave Field Contract (value-from-local-state, never from query data)

- **Status:** accepted
- **Date:** 2026-06-19
- **Brand:** vitalia
- **Scope:** transversal FE — toda hoja con campos editables + autosave (lisa / adrián / mateo / lucas / camila / plataforma)
- **Authors:** /architect (vitalia)
- **Supersedes:** nada. **Extiende:** `docs/architecture/luana-platform/design-system-canon.md` §2.6 + §6.7 (canon platform, NO se edita acá — ver § 7 Nota de promoción)
- **Origen:** bug confirmado live (Chris) en `…/lisa/servicios/{id}/resumen` — los textareas ricos "procesan cada letra".

---

## 1. Contexto + bug confirmado (root cause)

### 1.1 Síntoma reportado (Chris, live)

En `…/lisa/servicios/{id}/resumen`, al escribir en los campos ricos (descripción, incluye, riesgos, etc.) el input "demora mucho en detectar que escribo y solo se escribe la última letra y se guarda, como si procesara cada letra". En **Marca/Identidad** el autosave anda fluido (tecleo normal, guarda a los segundos).

### 1.2 Root cause — confirmado leyendo los 3 archivos (NO re-investigado)

Confirmo el diagnóstico de Chris, con precisión sobre el mecanismo:

- **ROTO — `ResumenView.tsx`:** los ~18 campos ricos son `<Textarea value={servicio.X ?? ""} onChange={(e)=>schedule({X:e.target.value})} />`. El `value` está atado **directo al dato de react-query** (`useServicioDetail`); el `onChange` SOLO agenda autosave, **no mantiene estado de edición local**. Cada ciclo de `useAutosave` llama `setStatus` (idle→saving→saved→idle), que **re-renderiza toda la vista**; en cada re-render el `value` del textarea vuelve a `servicio.X` (el valor del server, que va atrasado respecto a lo que el usuario tipeó). Resultado: el input "pelea" con el tecleo → se ve "procesa cada letra". El campo `public_name` del mismo archivo NO sufre esto porque vive en RHF (`Controller` → `field.value` sale del form, no del server).
- **BIEN — `IdentityCard.tsx`:** estado en RHF (`register(...)`), `value` SALE del formulario (nunca del server), `watch()` → `useEffect(valuesJson)` → `onSave` debounced fire-and-forget. El round-trip al server **jamás toca el value visible** → tecleo fluido.
- **El hook ya es correcto** — `use-autosave.ts` (600ms + coalesce + flush) NO es el bug. El bug es el **binding del `value`** (server vs estado de edición local). El que `useAutosave` haga `setStatus` es legítimo (necesita pintar el indicador); el error es que ese re-render alcanza un `value` derivado del server.

### 1.3 Por qué los tests no lo cazaron (relevante para el gate)

`ResumenView.test.tsx` **mockea `use-autosave`** (`useAutosave: () => ({ schedule: mockSchedule, status: "idle", ... })`). Al mockear el hook, el `status` queda congelado en `"idle"`: **no hay ciclo idle→saving→saved → no hay re-render por status → el feedback loop que causa el bug no existe en el test**. Los asserts ("schedule llamado en onChange", "value hidratado de servicio") pasan verdes sobre un componente que NO reproduce el problema. Esto es un **falso verde de unit-test**: el bug solo aparece con el hook real corriendo + el render real. La detección honesta es live-verify (DoD #37) o un test que NO mockee el ciclo de status. El gate de § 3 ataca la **causa estructural** (el binding), no el síntoma.

### 1.4 Qué codifica (y qué NO) el canon hoy

`design-system-canon.md` §2.6 + §6.7 codifican: el hook `use-autosave` 600ms+coalesce, UNA `FloatingAutosaveIndicator` por página, sin badge por-grupo, barrita de color del agente. El ejemplo §6.7 usa `register(...)` (RHF) — implícitamente correcto — pero **la prosa nunca enuncia la invariante**: *"el `value` de un input editable sale SIEMPRE del estado de edición local (RHF/useState), nunca de `value={queryData.x}`"*. Ese hueco es exactamente por donde se filtró el bug. Este ADR lo cierra brand-local + propone amendar el canon (§ 7).

---

## 2. Contrato canónico de campo-autosave (la receta reusable)

> **Invariante cardinal (HARD):** en una hoja con autosave, el `value` (o `defaultValue`/`checked`) de **todo input editable** sale del **estado de edición local** — RHF (`Controller`/`register`) o, en último caso, `useState` local hidratado una vez. **PROHIBIDO** `value={queryData.x}` en un campo editable. El dato de react-query es la **fuente de hidratación inicial** (una vez por entidad), NUNCA el `value` vivo.

### 2.1 Las 6 reglas del contrato

1. **Estado de edición = RHF (local).** Toda hoja con campos editables monta `useForm`. El `value` de cada campo sale del form, no del server.
2. **`value` siempre del form.** `Controller render={({field}) => <Input {...field} />}` o `{...register("x")}`. Nunca `value={servicio.x}` en un input editable. (Display read-only — un `<a>`, un `<p>` — sí puede leer del server: no es editable, no re-renderiza contra el tecleo.)
3. **Autosave fire-and-forget vía `use-autosave`.** El `onChange`/`watch` agenda el PATCH (600ms + coalesce). El resultado del PATCH **no re-hidrata el form** mientras el usuario edita. El status pinta la píldora, nada más.
4. **Hidratar UNA vez por entidad con `form.reset`.** Al cambiar de entidad (`offer_id`/`id` distinto) → `form.reset({...serverData})`. La dependencia del efecto es el **id de la entidad**, NO el objeto entero (resetear en cada cambio del objeto clobbearía el tecleo en vuelo). Alternativa equivalente: `key={entityId}` en el componente para forzar remonte limpio.
5. **UNA `FloatingAutosaveIndicator` por página** (canon §2.6). Sin badge por-grupo.
6. **PROHIBIDO `value={queryData.x}` en input editable** — es el anti-pattern raíz. Si necesitás el valor del server, va al `defaultValues`/`form.reset`, no al `value`.

### 2.2 Patrón mínimo correcto — Textarea rico (Controller)

```tsx
// Schema: incluí TODOS los campos ricos editables (no solo public_name)
const resumenSchema = z.object({
  public_name: z.string().min(1),
  description_long: z.string().nullable().optional(),
  includes: z.string().nullable().optional(),
  risks: z.string().nullable().optional(),
  // … los ~18 campos ricos
});
type ResumenFormValues = z.infer<typeof resumenSchema>;

export function ResumenView({ offerId }: { offerId: string }) {
  const { data: servicio } = useServicioDetail({ offerId });
  const { mutateAsync: patchFieldAsync } = usePatchField(offerId);
  const { schedule, status } = useAutosave<ServicePatchRequest>({
    saveFn: (patch) => patchFieldAsync(patch),
  });

  const form = useForm<ResumenFormValues>({
    resolver: zodResolver(resumenSchema),
    defaultValues: { public_name: "", description_long: "", includes: "", risks: "" },
  });

  // Hidratar UNA vez por entidad (id como dep, NO el objeto)
  useEffect(() => {
    if (servicio) {
      form.reset({
        public_name: servicio.public_name ?? "",
        description_long: servicio.description_long ?? "",
        includes: servicio.includes ?? "",
        risks: servicio.risks ?? "",
      });
    }
  }, [servicio?.offer_id]); // eslint-disable-line react-hooks/exhaustive-deps -- reset solo al cambiar de entidad

  return (
    <>
      <Controller
        control={form.control}
        name="description_long"
        render={({ field }) => (
          <Textarea
            {...field}                                   // ← value SALE del form
            value={field.value ?? ""}                    // nullable → "" para input controlado
            onChange={(e) => {
              field.onChange(e);                          // 1) update estado local (mantiene cursor + tecleo)
              schedule({ description_long: e.target.value || null }); // 2) autosave fire-and-forget
            }}
          />
        )}
      />
      {/* … resto de campos ricos idénticos … */}
      <FloatingAutosaveIndicator status={status} />       {/* UNA por página */}
    </>
  );
}
```

**Clave del fix:** `field.onChange(e)` mantiene el valor en RHF; el re-render por `status` lee `field.value` (lo que el usuario tipeó), NO `servicio.description_long` (server atrasado). El loop se rompe.

### 2.3 Variante `register` (cuando no necesitás Controller)

Para inputs nativos sin lógica de transformación, `{...register("x", { onChange: (e) => schedule({ x: e.target.value || null }) })}` es equivalente y más liviano. `IdentityCard.tsx` usa el patrón `watch()` → `useEffect(valuesJson)` → `onSave` — también válido (el `value` sale del form vía `register`). Ambos cumplen la invariante; elegí por ergonomía del campo.

---

## 3. Gate de enforcement — atrapar la recurrencia

### 3.1 Qué se quiere atrapar

Un `<Input|Textarea|Select|Checkbox>` **editable** cuyo `value=` (o `checked=`) lee un **objeto de react-query** (p. ej. `servicio.X`, `data.X`, `detail.X`) **Y** cuyo `onChange` llama `schedule(...)` (o el `saveFn` de `useAutosave`) **sin** pasar por estado local (`field.value` de RHF / `useState`).

### 3.2 Viabilidad: eslint custom vs arch-fitness regex — recomendación

| Opción | Precisión | Costo | Falsos+ / Falsos− |
|---|---|---|---|
| **eslint `no-restricted-syntax`** (AST, selector JSX) | media-alta | medio (selector frágil, no resuelve de dónde sale `servicio`) | F+ medio (no distingue `servicio` query-data de un objeto local), F− medio (no liga `value` ↔ `onChange→schedule` en el mismo JSXElement) |
| **eslint rule custom dedicada** (plugin propio, visita `JSXOpeningElement`) | alta | alto (escribir + testear plugin) | bajo si se restringe a "archivo que importa `useAutosave` + `<Textarea/Input>` con `value={<ident>.<member>}` + onChange que referencia `schedule`" |
| **arch-fitness test (regex sobre archivos con `useAutosave`)** | media | bajo (un test, regex acotada) | F+ bajo-medio, F− medio (regex no entiende multilínea/Controller) |

**Recomendación: arch-fitness test FE (regex acotada), como gate HARD de primera línea + ítem de checklist del auditor como red de seguridad.** Razón: el heurístico de valor es inherentemente impreciso (un linter no sabe en general si `servicio` es query-data o un objeto local), así que un eslint custom dedicado es over-engineering para el ROI; pero un arch-fitness test **acotado al universo correcto** (solo archivos que importan `useAutosave`) tiene F+ muy bajo y se escribe en ~30 LOC. El eslint genérico `no-restricted-syntax` queda como opción descartada (frágil + ruidoso).

### 3.3 Heurística del arch-fitness test (diseño, NO implementación)

Archivo nuevo: `vitalia/frontend/src/__tests__/architecture/test-autosave-value-from-local-state.test.ts`.

```
Universo:   archivos .tsx bajo features/** que importan `useAutosave` (from "@/hooks/use-autosave").
            (Acota el scan: una hoja sin autosave no puede tener este bug.)

FLAG (violación) si, en el MISMO archivo, coexisten:
  (a) un input editable con value/defaultValue/checked atado a un member de
      objeto:  /<(Input|Textarea|Select|Checkbox)[^>]*\svalue=\{[a-zA-Z_]\w*\.[a-zA-Z_]/
      (o las variantes value={x.y ?? ...} / defaultValue={x.y} / checked={x.y})
  Y (b) ese mismo objeto-raíz NO es `field` (RHF Controller) ni `form` ni un useState local
      → lista de identificadores "permitidos como fuente de value": {field, form, ...whitelist}
      → si el identificador raíz NO está en la whitelist → es query-data → VIOLACIÓN.

Ratchet: allowlist KNOWN_AUTOSAVE_VALUE_FROM_QUERY (shrink-only). ResumenView.tsx entra
         a la allowlist hoy (deuda conocida) y SALE cuando el fix de § 4 mergee.
```

### 3.4 Honestidad sobre el heurístico (falsos +/−)

- **Falsos positivos esperados:**
  - Display **read-only** que casualmente usa `<Input readOnly value={servicio.x}/>` (no editable → no es bug). Mitigación: excluir cuando el elemento tiene `readOnly`/`disabled` literal, o whitelistear el caso con justificación en la allowlist.
  - Campos `value={servicio.x}` que NO tienen `onChange→schedule` (no participan del loop). Mitigación: requerir co-presencia de `schedule(`/`saveFn` en el archivo ya acota; refinar pidiendo el `onChange` en el mismo elemento eleva precisión a costa de regex multilínea.
- **Falsos negativos esperados (el regex NO los ve):**
  - Componentes **hijos** que reciben `value={servicio.x}` como prop y el `<Input>` real vive adentro (indirección de un nivel). El scan single-file no lo sigue. → red de seguridad: ítem del auditor.
  - `value={getValue(servicio)}` (envuelto en función) o desestructurado (`const {risks} = servicio; value={risks}`). → auditor.
  - `Controller` con `value={servicio.x}` adentro del `render` (mal uso de Controller). El regex puede no matchear si está multilínea. → auditor.
- **Conclusión:** el arch-test es **gate HARD para el 80% directo** (el caso ResumenView exacto y sus clones), el auditor cubre el 20% indirecto. Ninguno reemplaza la **live-verify** (DoD #37): tipear en un textarea rico del stack dev real y confirmar que NO procesa letra-a-letra es la verificación última.

### 3.5 Ítem exacto para el checklist de `auditor-frontend`

> **[Autosave field binding — ADR-vitalia-009]** En toda hoja con `useAutosave`: ¿el `value`/`checked`/`defaultValue` de cada input **editable** sale del estado de edición local (RHF `field.value`/`register`, o `useState` local) y **nunca** de `value={queryData.x}` (objeto react-query)? Verificar incluyendo: (a) componentes hijos que reciben `value` como prop desde query-data, (b) `Controller` con `value=` server adentro del render, (c) hidratación una-vez-por-entidad (`form.reset` con dep = id de entidad, o `key={entityId}`). Si el componente toca textareas ricos → **ejercer live** (tipear ≥1 párrafo en el stack dev real) y confirmar tecleo fluido (no procesa-cada-letra). Sin esto → CHANGES_REQUESTED.

---

## 4. Scope del fix — servicios (ResumenView)

> **Este ADR NO implementa el fix** (eso es `/dev-team`). Define el scope para que el ticket sea preciso.

### 4.1 Campos ricos a migrar a RHF (estado local)

Hoy SOLO `public_name`, `category`, `modality`, `appointment_type` están en RHF. Migrar el resto de **campos de texto editables** atados a `servicio.*` (todos con `value={servicio.X}` + `onChange→schedule`):

`description_long · includes · excludes · warranty · procedure_steps · anesthesia_pain · prep · aftercare · downtime · expected_result · result_timing · result_lifespan · realistic_expectations · risks · red_flags`

(≈15 textareas/inputs ricos.)

**Fuera de scope del fix RHF (ya correctos / patrón distinto, NO tocar salvo verificación):**
- `VariantsRepeater` (`value={servicio.variants ?? []}`) — array repeater con su propio estado; no es input de texto controlado contra el tecleo. Verificar que su edición interna no sufra el mismo loop; si lo sufre, es ticket aparte.
- `session_interval` / `recurrence_interval` / `initial_appt_duration_minutes` (`NumberWithUnit` + `Select`) — número/select, no texto libre. El loop letra-a-letra no aplica igual, pero por consistencia conviene moverlos al form también; marcar como **nice-to-have** dentro del mismo ticket, no bloqueante.
- `RungPicker` (value_level) — ya tiene el PATCH gap documentado (`T-6-impl-log.md § Upstream deficiency`), no es autosave de texto.

### 4.2 Cambio exacto (3 piezas)

1. **`servicios-schema.ts`** — extender un schema `resumenSchema` (o el form schema que use ResumenView) con los ~15 campos ricos: `z.string().nullable().optional()` cada uno. (El schema actual del archivo cubre create/edit; el form de la hoja Resumen necesita su propio `resumenSchema` con los campos ricos — hoy en `ResumenView.tsx` el inline schema solo tiene 4 campos.)
2. **`ResumenView.tsx`** — para cada campo rico: (a) agregar al `defaultValues` + al `form.reset` del efecto de hidratación (dep `servicio?.offer_id`, ya existe); (b) envolver en `Controller` (o `register`); (c) `value={field.value ?? ""}`; (d) `onChange` = `field.onChange(e)` + `schedule({ X: e.target.value || null })`. Quitar todos los `value={servicio.X}` de inputs editables.
3. **`ResumenView.test.tsx`** — **dejar de mockear `use-autosave`** en al menos un test nuevo de regresión que reproduzca el loop: render con el hook real (o un fake que sí cicle `status`), tipear en `description_long`, y assert que el `value` del textarea = lo tipeado (NO el valor del server). Mantener los tests existentes (hidratación, conditionals) adaptados al binding del form. Agregar assert: ningún `<Textarea>` editable tiene `value` derivado directo de `servicio.*`.

### 4.3 Tamaño estimado

**1 archivo FE de componente** (`ResumenView.tsx`) + **1 schema** (`servicios-schema.ts`, extender) + **tests** (`ResumenView.test.tsx`, 1-2 tests de regresión + adaptación). Mecánico y acotado — el patrón ya existe en `IdentityCard`/`public_name`; es replicarlo a 15 campos. Naturaleza: bugfix FE con regression test RED-first. Live-verify obligatoria (tipear en el stack dev real).

---

## 5. Decisión

1. **Adoptar el Contrato de campo-autosave de § 2** como invariante FE transversal de vitalia (toda hoja con autosave, todos los agentes). Brand-local hoy; candidato a canon platform (§ 7).
2. **Construir el gate de § 3** — arch-fitness test FE `test-autosave-value-from-local-state.test.ts` (HARD, ratchet shrink-only, `ResumenView.tsx` en allowlist hasta el fix) + ítem de checklist en `auditor-frontend`. El arch-test es gate de primera línea; el auditor + live-verify cubren el 20% indirecto.
3. **Fix de servicios (§ 4)** como story `bugfix` separada (la owna `/dev-team`), repro-first, con live-verify.

## 6. Consecuencias

- **Positivas:** el bug raíz (binding server-en-value) queda enunciado + enforceado; futuras hojas nacen correctas; el gate corta la recurrencia en el 80% directo; el auditor + DoD #37 cubren el resto.
- **Costo:** 1 arch-test nuevo (~30 LOC) + 1 ítem de checklist; el fix de servicios es mecánico (~1 archivo + schema + tests).
- **Deuda conocida:** `ResumenView.tsx` entra a la allowlist del arch-test hasta que el fix de § 4 mergee (entonces SALE — ratchet shrink-only). Otras hojas con autosave deben auditarse contra el contrato (barrido fuera de scope de este ADR; lo dispara el arch-test al correr).
- **Límite honesto:** ningún gate estático reemplaza la live-verify de tipear en un textarea rico del stack dev real (el unit-test que mockea el hook fue exactamente lo que ocultó el bug).

---

## 7. Nota de promoción al canon platform (propuesta para `/pm-vitalia` — NO editar el canon acá)

> El patrón de § 2 es **React universal** (cross-brand): cualquier marca con hojas autosave (nicolify, comunify, lupulo) puede caer en el mismo bug. El canon platform `design-system-canon.md` §2.6/§6.7 codifica el hook + indicador pero **no enuncia la invariante del value-binding**. Propongo amendar el canon (vía `/pm-vitalia` promotion gate — el canon es core, no se edita brand-local).

**Texto propuesto del amendment a `design-system-canon.md` §2.6 (agregar una bullet):**

> - **Value-binding (HARD):** el `value`/`checked`/`defaultValue` de **todo input editable** sale del **estado de edición local** (RHF `field.value`/`register`, o `useState` local hidratado **una vez** por entidad vía `form.reset`/`key`). **PROHIBIDO `value={queryData.x}`** en un campo editable: el dato del fetch es fuente de **hidratación inicial**, nunca el `value` vivo. Atar el `value` al dato de react-query + `setStatus` del autosave produce un re-render que pisa el tecleo ("procesa cada letra"). Display read-only (`<a>`/`<p>`) sí puede leer del fetch. Enforcement: arch-test FE por marca (`value` editable derivado de query-data → fail; ratchet shrink-only) + checklist auditor-frontend.

**Y agregar al snippet §6.7** un comentario explícito: `{/* value SALE del form (register/Controller), NUNCA value={queryData.x} */}`.

**Gate de promoción sugerido:** lift del **contrato + arch-test replicable** (patrón hermano de `ADR-012-autosave-primitive-platform.md` + del contrato dark-mode §2.10 que ya se replica por marca). Cada brand replica el arch-test en su `__tests__/architecture/` (mismo molde que `test-no-clerk-organizations.test.ts`). Proposal candidate: `docs/promotion-protocol/proposals/2026-06-NN-autosave-value-binding-contract.md`.

---

## 8. Referencias

- `docs/architecture/luana-platform/design-system-canon.md` §2.6 + §6.7 — canon autosave (hook + indicador; SIN la invariante de value-binding — este ADR la añade brand-local + propone amendarla)
- `docs/architecture/luana-platform/ADR-012-autosave-primitive-platform.md` — patrón hermano (autosave como primitiva platform)
- `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` — doctrina DS + enforcement mecánico
- `.claude/rules/frontend-visual-fidelity.md` § Design System Canon — binding HARD del canon por actor
- `.claude/rules/definition-of-done-live-verify.md` (Critical #37) — la live-verify que caza este bug donde el unit-test mockeado falla
- `vitalia/frontend/src/hooks/use-autosave.ts` — el hook (correcto; NO es el bug)
- `vitalia/frontend/src/features/lisa/components/marca/identidad/IdentityCard.tsx` — referencia del patrón correcto (RHF, value del form)
- `vitalia/frontend/src/features/lisa/components/servicios/leaves/ResumenView.tsx` — el archivo roto (scope del fix § 4)
- `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md` § 5 Forms — RHF+Zod+autosave 600ms (este ADR concreta el "cómo" del value-binding que §5 daba por implícito)
