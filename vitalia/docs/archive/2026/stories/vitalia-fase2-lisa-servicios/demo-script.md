# demo-script — vitalia-fase2-lisa-servicios (Lisa · Servicios)

> Funcional (demo_required). Ejercé esto en dev-app y firmá `checkpoint.md::chris_verify.signoff`.
> Stack: `make dev-vitalia` (up) · `dev-app.vitalialat.com` o `localhost:3002` · login `dr.demo@vitalialat.com` / `<DEV_APP_TEST_PASSWORD en vitalia/.env.dev>` · tenant Sanaré LATAM.
> Migración 045+046 ya aplicadas al dev DB.

## Happy path (live-verified 2026-06-16 — replicable)

1. **Lisa → Servicios → Catálogo.** Vacío → empty-state "Empieza tu catálogo desde la biblioteca" + 3 quick-picks (Diseño de sonrisa / Toxina / Cirugía) + "Crear servicio personalizado".
2. **Crear servicio.** "Nuevo servicio" → ruta `/nuevo` (picker inline, NO modal) → toggle **Personalizado** → Nombre + Precio (ARS, de tenant locale) → "Crear y configurar".
   - ✅ `POST /offer/servicios/custom → 201` · redirect al workspace `/[offer-id]/resumen`.
3. **Workspace (N3).** EntitySubNavBar: root-pill ‹ Servicios + EntityPicker ▾ (cambia de servicio sin volver) + 5 leaves (Resumen · Para Adrián · Especialistas · Plan de pago · Prueba social). Resumen = 6 grupos (Identidad·Qué es·Procedimiento·Resultados·Riesgos·Modalidad y agenda).
4. **Autosave.** Editá el Nombre → sin botón Guardar → `PATCH /offer/servicios/{id} → 200` · el EntityPicker refleja el nombre nuevo · DB `products.name` actualizado.
5. **Activar.** Volvé a Catálogo → switch **Activar servicio** en la card → `POST /offer/servicios/{id}/activate → 200` · `growth_studio_event: service_activated` · DB `status=active`.
6. **KEYSTONE (AC-6).** El offer activo queda en la tabla engine `products` (tenant-scoped) que lee `TenantKnowledgeBuilder.build_identity` → Adrián lo conoce. (data shape verificada DB + unit `test_keystone_offer_shape.py`).

## ⚠️ Findings a triar (NO rompen el happy-path)

- **F1 (medium):** el **workspace no muestra la barra de estado** (toggle Activo / chip origen / completitud) — `layout.tsx` monta `ServicioWorkspaceShell` directo y no `ServicioWorkspaceView` (que monta `ServiceStatusBar`). Activar funciona desde la card del catálogo. → fix de wiring (auditor) o decidir.
- **F2 (HIGH · contrato BE):** los campos ricos de la ficha (descripción, qué incluye, procedimiento, resultados, riesgos, cuidados — RN-26 §6 "ficha completa editable") **no se guardan**: `ServicePatchRequest` del BE sólo acepta `{public_name, price, category, modality}`. El dominio/DTO offer no modela esos campos → textareas son placeholders. → decisión: extender contrato (reconcile/historia) o recortar scope.
- **F3 (low):** "Tipo de cita inicial" (appointment_type) no persiste (sin campo BE).

## Pendiente técnico (no demo)
- Visual goldens 8 (project=visual · 0.001) — no generados aún. El render real quedó verificado live (este demo).
- Sub-phase B (RAG) — gated `/pm-luana` (STOP-2).
