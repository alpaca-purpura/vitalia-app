# Extension Points del SDK de Luana

> **Versión:** v0.1.0 (production-grade alpha) · **Fecha:** 2026-05-12 · **Owner:** luana-core-extension-sdk

Este documento describe los 18 puntos de extensión (EP) formalizados del SDK de Luana,
las políticas transversales (CC-1..CC-5), ejemplos por vertical y la receta completa
para construir un agente vertical sobre `luana-core`.

---

## 1. Descripción General del SDK y Principios de Diseño

### Qué es el Extension SDK

El `luana-core-extension-sdk` es la capa de contrato entre `luana-core` (motor central,
sin conocimiento de verticales) y los backends de marca (`vitalia/backend/src/modules/vitalia/`,
`comunify/backend/src/modules/comunify/`, `lupulo/backend/src/modules/lupulo/`,
`nicolify/backend/src/modules/nicolify/`). Cada marca registra sus extensiones en un
`ExtensionPointRegistry` durante el arranque de la aplicación FastAPI, antes de que el
servidor comience a recibir tráfico.

**Filosofía:** el core no conoce a las marcas; las marcas conocen al core.
Las marcas inyectan comportamiento concreto a través de los 18 EP definidos.
El core invoca los EP en runtime sin importar directamente ningún módulo de marca.

### CC-1 — Patrón de firma por EP natural (DataClass vs Callable)

Cada EP tiene un patrón de firma natural según su semántica:

- **DataClass** cuando el EP registra una definición declarativa (modelos, plantillas, packs,
  políticas). Ejemplo: `PresetPack`, `ToolDef`, `BookingPolicy`, `GuardrailDef`.
- **Callable** cuando el EP registra comportamiento puro (handlers, checkers). Ejemplo: EP-1
  `field_override` recibe un `Callable[[FieldDef, BrandContext], Optional[FieldOverride]]`.

No se fuerza un patrón único para todos. Cada EP usa el que resulta más natural para su dominio.
Esto facilita la introspección, la serialización (DataClasses son JSON-able) y el testing
(Callables son fáciles de mockear).

### CC-2 — Modo append por defecto + override caso a caso (vía flag `mode`)

El modo por defecto de todos los `register_*` es `mode='append'`. Registrar el mismo nombre
dos veces en modo `append` eleva `DuplicateRegistrationError` (CC-4).

Solo **EP-17** (`tenant_plan_tier_register`) y **EP-18** (`onboarding_wizard_steps_register`)
aceptan `mode='override'`. El override reemplaza el registro previo con el mismo nombre,
en lugar de agregarlo. Esto permite que una marca redefina su plan tier o sus pasos de
onboarding sin crear duplicados.

```python
# EP-17 override: reemplaza la definición previa del tier
registry.tenant_plan_tier_register(
    PlanTierDef(tier_id="vitalia.pro", label="Pro Clínica", ...),
    mode="override",
)
```

Intentar `mode='override'` en EP-1..EP-16 eleva `ValueError`.

### CC-3 — Registro solo en startup universal

Todos los `register_*` se deben llamar **exclusivamente** durante el evento `lifespan` de
FastAPI, antes de que el servidor comience a atender requests. Una vez que el lifespan
llama a `registry.close()`, cualquier intento de registro posterior eleva
`RegistrationClosedError`.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ExtensionPointRegistry()
    register_all(registry)
    registry.close()           # ← CC-3: cierra el registro
    app.state.registry = registry
    yield
```

El cierre es idempotente: llamar a `close()` múltiples veces no produce error.

**Rationale:** permitir registro en runtime abriría race conditions en entornos multi-worker
y haría imposible la predicción de comportamiento durante tests. El startup-only pattern
es estándar en frameworks de plugins maduros (Starlette, Django Apps, Gunicorn hooks).

### CC-4 — Excepción estricta en duplicado + namespace obligatorio (prefijo brand_slug)

Cada nombre registrado DEBE comenzar con el `brand_slug` de la marca, seguido de un punto
y un identificador único. El `brand_slug` debe pertenecer al allowlist definido en el SDK:
`_ALLOWED_BRAND_SLUGS` en
`core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py`
(actualmente: `{"nicolify", "vitalia", "comunify", "lupulo", "test-brand"}`; las 6 brands
bootstrap se agregarán al frozenset al incorporarlas, no en este doc).

```python
# Correcto
registry.sales_agent_tool_register(ToolDef(name="vitalia.medical_consent_check", ...))

# Incorrecto — eleva NamespaceViolationError
registry.sales_agent_tool_register(ToolDef(name="medical_consent_check", ...))

# Incorrecto — brand_slug no en allowlist
registry.sales_agent_tool_register(ToolDef(name="unknown_brand.tool", ...))
```

El namespace garantiza que dos marcas no colisionen en el registry global. El core puede
enrutar por `brand_slug` sin ambigüedad.

### CC-5 — Inmutable post-startup (no `unregister_*`)

El registry no expone ningún método `unregister_*`. Una vez registrado un EP, su registro
es permanente durante el ciclo de vida del proceso. Esto simplifica el razonamiento sobre
el estado del sistema y evita bugs difíciles de reproducir (un handler que se des-registra
a mitad de una conversación).

```python
# Esto eleva AttributeError — CC-5 inmutable
getattr(registry, "unregister_field_override")  # AttributeError
```

---

## 2. EP-1..EP-5 Críticos (EJECUTABLES)

Los primeros 5 extension points son **críticos y ejecutables**: el core los invoca en
runtime y espera resultados. El registry expone helpers de dispatch que llaman a los
handlers registrados.

### EP-1 — `field_override` (Callable)

Permite que una marca personalice la definición de un campo del formulario en tiempo real.
El core invoca `resolve_field_override(field, ctx)` antes de renderizar cualquier campo.
El primer handler que retorne un resultado no-`None` gana (orden de registro = prioridad).

**Firma Python:**

```python
def field_override(
    handler: Callable[[FieldDef, BrandContext], Optional[FieldOverride]],
    *,
    name: str,
    mode: Literal["append", "override"] = "append",
) -> None: ...

def resolve_field_override(self, field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]: ...
```

**Ejemplo Vitalia (médico):**

```python
# vitalia/backend/src/modules/vitalia/extensions.py
def _vitalia_consent_field_override(
    field: FieldDef, ctx: BrandContext
) -> Optional[FieldOverride]:
    """Reemplaza el campo 'descripcion_servicio' con aviso legal médico obligatorio."""
    if field.name == "descripcion_servicio" and ctx.compliance_flags.get("regulated_health"):
        return FieldOverride(
            name="descripcion_servicio",
            label="Descripción del servicio médico",
            hint=(
                "Incluye nombre del procedimiento, duración estimada y condiciones previas "
                "del paciente. Este campo es requerido por la Ley 26.529 (derechos del paciente)."
            ),
            required=True,
        )
    return None

registry.field_override(
    _vitalia_consent_field_override,
    name="vitalia.medical_consent_override",
)
```

**Ejemplo Comunify (creator-economy):**

```python
def _comunify_creator_bio_override(
    field: FieldDef, ctx: BrandContext
) -> Optional[FieldOverride]:
    """Adapta el campo 'bio' para creadores de contenido."""
    if field.name == "bio":
        return FieldOverride(
            name="bio",
            label="Tu historia como creador",
            hint="Cuéntale a tu audiencia quién eres, qué los une y por qué deberían seguirte.",
        )
    return None

registry.field_override(_comunify_creator_bio_override, name="comunify.creator_bio_override")
```

**Ejemplo Lupulo (gastronomía):**

```python
def _lupulo_menu_field_override(
    field: FieldDef, ctx: BrandContext
) -> Optional[FieldOverride]:
    """Adapta descripción del producto para carta de cervecería."""
    if field.name == "producto_descripcion":
        return FieldOverride(
            name="producto_descripcion",
            label="Descripción de la cerveza",
            hint="IBUs, porcentaje de alcohol, estilo (IPA/Stout/Lager), maridaje sugerido.",
        )
    return None

registry.field_override(_lupulo_menu_field_override, name="lupulo.menu_field_override")
```

**Registro en lifespan:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ExtensionPointRegistry()
    registry.field_override(_vitalia_consent_field_override, name="vitalia.medical_consent_override")
    registry.close()
    app.state.registry = registry
    yield
```

---

### EP-2 — `offer_preset_pack_register` (DataClass)

Permite que una marca agregue sus propios packs de presets de oferta al catálogo.
`list_offer_preset_packs(ctx)` filtra por `ctx.brand_slug` para retornar solo los packs
de la marca activa.

**Firma Python:**

```python
def offer_preset_pack_register(
    pack: PresetPack,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

def list_offer_preset_packs(self, ctx: BrandContext) -> list[PresetPack]: ...
```

**Ejemplo Vitalia (médico):**

```python
registry.offer_preset_pack_register(
    PresetPack(
        name="vitalia.tratamientos_esteticos",
        presets=(),  # populated by offer-core catalog lookup
        applies_to_brand="vitalia",
        description="Pack de tratamientos estéticos ambulatorios",
    )
)
```

**Ejemplo Comunify (creator-economy):**

```python
registry.offer_preset_pack_register(
    PresetPack(
        name="comunify.creator_offer_pack",
        presets=(),
        applies_to_brand="comunify",
        description=(
            "Pack de ofertas para creadores: membresía premium, masterclass grabada, "
            "comunidad privada, 1:1 coaching call."
        ),
    )
)
```

**Ejemplo Lupulo (gastronomía):**

```python
registry.offer_preset_pack_register(
    PresetPack(
        name="lupulo.experiencias_cerveceras",
        presets=(),
        applies_to_brand="lupulo",
        description="Pack: maridaje guiado, cata privada, tour de producción + copa incluida.",
    )
)
```

---

### EP-3 — `sales_agent_tool_register` (DataClass + Callable)

Registra una herramienta personalizada para el agente de ventas. El `ToolDef` incluye
el handler callable que el agente invocará en runtime.

> **Wiring adaptador:** el registry acepta un `sales_agent_tool_registry_adapter` opcional
> en su constructor. Si se inyecta (Stories 11-13 lo harán), la herramienta también se
> registra en el `ToolRegistry` interno de `luana-core-sales-agent`. En Story 8 (test-brand),
> el adaptador es `None` — la herramienta solo queda en el SDK registry.

**Firma Python:**

```python
def sales_agent_tool_register(
    tool: ToolDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

def get_sales_agent_tool(self, name: str) -> Optional[ToolDef]: ...
```

**Ejemplo Vitalia (médico) — herramienta de consentimiento:**

```python
def _medical_consent_request(
    patient_name: str, procedure: str, appointment_id: str
) -> dict:
    """Genera solicitud de consentimiento informado y lo persiste en el expediente."""
    # ... integra con sistema de consentimientos clínica
    return {"consent_id": "...", "status": "pending_signature", "send_to": "whatsapp"}

registry.sales_agent_tool_register(
    ToolDef(
        name="vitalia.medical_consent_request_tool",
        description=(
            "Genera y envía un formulario de consentimiento informado al paciente "
            "antes del procedimiento. Requerido por Ley 26.529."
        ),
        input_schema={
            "type": "object",
            "required": ["patient_name", "procedure", "appointment_id"],
            "properties": {
                "patient_name": {"type": "string"},
                "procedure": {"type": "string"},
                "appointment_id": {"type": "string"},
            },
        },
        handler=_medical_consent_request,
        tool_groups=("compliance", "pre_appointment"),
    )
)
```

**Ejemplo Comunify (creator-economy) — herramienta de membership check:**

```python
def _check_membership_tier(subscriber_id: str) -> dict:
    """Verifica el tier de membresía de un suscriptor para personalizar la respuesta."""
    return {"tier": "pro", "access": ["masterclass", "comunidad", "1on1"]}

registry.sales_agent_tool_register(
    ToolDef(
        name="comunify.membership_tier_check_tool",
        description="Verifica el tier activo del suscriptor y sus beneficios incluidos.",
        input_schema={
            "type": "object",
            "required": ["subscriber_id"],
            "properties": {"subscriber_id": {"type": "string"}},
        },
        handler=_check_membership_tier,
        tool_groups=("knowledge", "personalization"),
    )
)
```

**Ejemplo Lupulo (gastronomía) — herramienta de disponibilidad de mesa:**

```python
def _check_table_availability(date: str, party_size: int) -> dict:
    """Consulta disponibilidad de mesas en la cervecería para la fecha solicitada."""
    return {"available": True, "suggested_time": "20:30", "section": "terraza"}

registry.sales_agent_tool_register(
    ToolDef(
        name="lupulo.book_table_tool",
        description="Verifica disponibilidad de mesas y realiza la reserva.",
        input_schema={
            "type": "object",
            "required": ["date", "party_size"],
            "properties": {
                "date": {"type": "string", "format": "date"},
                "party_size": {"type": "integer", "minimum": 1},
            },
        },
        handler=_check_table_availability,
        tool_groups=("booking", "qualification"),
    )
)
```

---

### EP-4 — `copilot_workflow_register` (DataClass)

Registra un workflow personalizado para el copiloto de onboarding. Similar a EP-3 pero
para el runtime del copiloto (módulo `luana-core-copilot`).

> **Wiring adaptador:** análogo a EP-3 con `copilot_workflow_registry_adapter`.

**Firma Python:**

```python
def copilot_workflow_register(
    workflow: WorkflowDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

def get_copilot_workflow(self, name: str) -> Optional[WorkflowDef]: ...
```

**Ejemplo Vitalia (médico):**

```python
registry.copilot_workflow_register(
    WorkflowDef(
        name="vitalia.onboarding_clinica_workflow",
        description=(
            "Guía al profesional médico para configurar su clínica: "
            "tipos de tratamiento, consentimientos, disponibilidad, integración con Vitalia Health."
        ),
        steps=(
            {"step": "perfil_clinica", "required_fields": ["nombre_clinica", "especialidad"]},
            {"step": "tratamientos", "required_fields": ["lista_procedimientos"]},
            {"step": "consentimientos", "required_fields": ["plantilla_consentimiento"]},
            {"step": "agenda", "required_fields": ["horarios_disponibles"]},
        ),
        trigger_event="tenant.onboarding_started",
    )
)
```

**Ejemplo Comunify (creator-economy):**

```python
registry.copilot_workflow_register(
    WorkflowDef(
        name="comunify.nurture_via_authority_workflow",
        description=(
            "Workflow de nutrición basado en autoridad: el creador comparte su historia, "
            "sus credenciales y su propuesta única de valor."
        ),
        steps=(
            {"step": "historia_origen", "required_fields": ["por_que_empece"]},
            {"step": "prueba_social", "required_fields": ["testimonios", "logros"]},
            {"step": "propuesta_valor", "required_fields": ["que_transformas"]},
        ),
        trigger_event="offer.draft_started",
    )
)
```

---

### EP-5 — `scheduling_booking_policy_register` (DataClass + Callable)

Registra una política de reserva personalizada para el módulo de agendamiento.
`get_booking_policy(name)` devuelve la política por nombre; el módulo de agendamiento
la invoca para decidir si confirmar o rechazar una reserva.

**Firma Python:**

```python
def scheduling_booking_policy_register(
    policy: BookingPolicy,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

def get_booking_policy(self, name: str) -> Optional[BookingPolicy]: ...
```

**Ejemplo Vitalia (médico) — política de confirmación con anamnesis previa:**

```python
def _vitalia_preop_policy(booking: object, ctx: BrandContext) -> BookingResult:
    """Verifica que el paciente completó el formulario pre-operatorio antes de confirmar."""
    patient_id = getattr(booking, "patient_id", None)
    completed_preop = check_preop_form_completed(patient_id)
    if not completed_preop:
        return BookingResult(
            allowed=False,
            reason="El paciente debe completar el formulario pre-operatorio antes de confirmar.",
        )
    return BookingResult(allowed=True)

registry.scheduling_booking_policy_register(
    BookingPolicy(
        name="vitalia.preop_anamnesis_required_policy",
        can_confirm=_vitalia_preop_policy,
        priority=10,
    )
)
```

**Ejemplo Lupulo (gastronomía) — política de capacidad máxima:**

```python
def _lupulo_capacity_policy(booking: object, ctx: BrandContext) -> BookingResult:
    """Verifica que la reserva no exceda la capacidad máxima del espacio."""
    party_size = getattr(booking, "party_size", 1)
    section = getattr(booking, "section", "general")
    max_capacity = get_section_capacity(section)
    current_reserved = get_current_reservations(section, booking.date)
    if current_reserved + party_size > max_capacity:
        return BookingResult(
            allowed=False,
            reason=f"La sección '{section}' ya está completa para esa fecha.",
        )
    return BookingResult(allowed=True)

registry.scheduling_booking_policy_register(
    BookingPolicy(
        name="lupulo.table_capacity_policy",
        can_confirm=_lupulo_capacity_policy,
        priority=5,
    )
)
```

**Ejemplo Comunify (creator-economy):**

```python
registry.scheduling_booking_policy_register(
    BookingPolicy(
        name="comunify.vip_member_priority_policy",
        can_confirm=lambda b, ctx: BookingResult(
            allowed=True,
            reason="Miembros VIP tienen confirmación automática.",
        ),
        priority=1,
    )
)
```

---

## 3. EP-6..EP-18 Backlog (Firma Únicamente — v0.1.0)

> **Importante:** EP-6..EP-18 son **signature-only** en v0.1.0. El registro siempre tiene
> éxito y las validaciones CC-1..CC-5 se aplican normalmente. Sin embargo, el dispatch
> semántico (`dispatch_*`, `get_sidebar_routes`, etc.) **eleva `NotImplementedError`** con
> el mensaje: `"EP-X foo_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"`.
>
> El despacho real se implementará en v0.2.x cuando las historias 11-13 (brand bootstraps)
> demanden el comportamiento concreto.

### EP-6 — `sidebar_routes_register` (DataClass)

Agrega rutas personalizadas a la barra lateral del panel de administración.

```python
def sidebar_routes_register(
    route: SidebarRouteDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.sidebar_routes_register(
    SidebarRouteDef(
        slug="vitalia.historial_clinico",
        label="Historial Clínico",
        icon="file-medical",
        order=10,
        role_required="medico",
    )
)

# Ejemplo Comunify:
registry.sidebar_routes_register(
    SidebarRouteDef(
        slug="comunify.analytics_creadores",
        label="Analytics de Comunidad",
        icon="bar-chart",
        order=5,
    )
)
```

---

### EP-7 — `extractor_register` (DataClass)

Registra un extractor de onda para el pipeline de extracción LLM
(subclase de `BaseExtractionOrchestrator`).

```python
def extractor_register(
    extractor: ExtractorDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.extractor_register(
    ExtractorDef(
        name="vitalia.medical_protocols_extractor",
        target_module="offer",
        wave_position=3,
        prompt_template_ref="vitalia/medical_protocols_wave.j2",
        output_schema_ref="VitaliaMedicalProtocolsSchema",
    )
)

# Ejemplo Lupulo:
registry.extractor_register(
    ExtractorDef(
        name="lupulo.menu_extractor",
        target_module="offer",
        wave_position=2,
        prompt_template_ref="lupulo/menu_wave.j2",
        output_schema_ref="LupuloMenuSchema",
    )
)
```

---

### EP-8 — `channel_adapter_register` (DataClass + Callables)

Registra un adaptador de canal personalizado para sales_agent, copilot o agentes
verticales. Scope extendido por §7.5.3: cubre `sales_agent`, `copilot` y cualquier
agente de marca vertical (treatment_agent, kitchen_agent, etc.).

```python
def channel_adapter_register(
    adapter: ChannelAdapterDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — canal WhatsApp para seguimiento médico:
registry.channel_adapter_register(
    ChannelAdapterDef(
        channel_slug="vitalia.whatsapp_meta_business",
        send=vitalia_whatsapp_send,
        receive=vitalia_whatsapp_receive,
        format_for_channel=vitalia_whatsapp_format,
        target_agent_runtime="vertical_brand",
        webhook_handler=vitalia_whatsapp_webhook,
    )
)

# Ejemplo Lupulo — canal SMS para confirmaciones:
registry.channel_adapter_register(
    ChannelAdapterDef(
        channel_slug="lupulo.sms_reservas",
        send=lupulo_sms_send,
        receive=lupulo_sms_receive,
        format_for_channel=lupulo_sms_format,
        target_agent_runtime="sales_agent",
    )
)
```

---

### EP-9 — `metric_register` (DataClass)

Registra una métrica personalizada de analítica para el pipeline ETL.

```python
def metric_register(
    metric: MetricDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.metric_register(
    MetricDef(
        name="vitalia.tasa_conversion_consentimiento",
        module="analytics",
        aggregation="avg",
        unit="ratio",
        currency_aware=False,
        stage_assignment="nurture",
        refresh_freq="daily",
    )
)

# Ejemplo Lupulo:
registry.metric_register(
    MetricDef(
        name="lupulo.ticket_promedio_mesa",
        module="analytics",
        aggregation="avg",
        unit="currency",
        currency_aware=True,
        stage_assignment="adoption",
        refresh_freq="hourly",
    )
)
```

---

### EP-10 — `landing_template_register` (DataClass)

Registra una plantilla de landing page personalizada para el vertical.

**También disponible como tipo TypeScript** (ver `@luana/extension-sdk`).

```python
def landing_template_register(
    template: LandingTemplateDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.landing_template_register(
    LandingTemplateDef(
        template_id="vitalia.clinica_estetica_v1",
        vertical_hint="medical_aesthetic",
        sections_schema={
            "sections": ["hero_antes_despues", "testimonios_pacientes",
                         "equipo_medico", "procedimientos", "cta_consulta"]
        },
        preview_url="https://templates.vitalia.com/clinica_estetica_v1",
    )
)

# Ejemplo Comunify:
registry.landing_template_register(
    LandingTemplateDef(
        template_id="comunify.creador_membresía_v1",
        vertical_hint="creator_economy",
        sections_schema={
            "sections": ["hero_creador", "comunidad_prueba_social",
                         "beneficios_tier", "faq", "cta_unirse"]
        },
    )
)
```

---

### EP-11 — `campaign_template_register` (DataClass)

Registra una plantilla de campaña de drip marketing personalizada.

```python
def campaign_template_register(
    template: CampaignTemplateDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — secuencia post-procedimiento:
registry.campaign_template_register(
    CampaignTemplateDef(
        template_id="vitalia.post_procedimiento_followup",
        channel="whatsapp",
        steps=(
            CampaignStepDef(step_id="s1", delay_seconds=3600, template_ref="vitalia/check_24h.j2"),
            CampaignStepDef(step_id="s2", delay_seconds=86400 * 3, template_ref="vitalia/check_3d.j2"),
            CampaignStepDef(step_id="s3", delay_seconds=86400 * 7, template_ref="vitalia/check_7d.j2"),
        ),
        trigger_event="appointment.completed",
    )
)

# Ejemplo Lupulo — campaña de lanzamiento de nueva cerveza:
registry.campaign_template_register(
    CampaignTemplateDef(
        template_id="lupulo.nuevo_lanzamiento_cerveza",
        channel="whatsapp",
        steps=(
            CampaignStepDef(step_id="s1", delay_seconds=0, template_ref="lupulo/tease.j2"),
            CampaignStepDef(step_id="s2", delay_seconds=86400, template_ref="lupulo/reveal.j2"),
        ),
        trigger_event="product.launched",
    )
)
```

---

### EP-12 — `asset_template_register` (DataClass)

Registra una plantilla de asset (imagen, video, PDF, kit) para la generación creativa.

```python
def asset_template_register(
    template: AssetTemplateDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.asset_template_register(
    AssetTemplateDef(
        template_id="vitalia.consentimiento_pdf",
        asset_type="pdf",
        placeholders={
            "patient_name": "str",
            "procedure": "str",
            "date": "str",
            "doctor_name": "str",
        },
        source_path="templates/vitalia/consentimiento_base.html",
    )
)

# Ejemplo Comunify:
registry.asset_template_register(
    AssetTemplateDef(
        template_id="comunify.post_instagram_kit",
        asset_type="kit",
        placeholders={"headline": "str", "cta": "str", "brand_color": "str"},
        source_path="templates/comunify/instagram_kit/",
    )
)
```

---

### EP-13 — `sales_agent_guardrail_register` (DataClass + Callables)

Registra un guardrail personalizado para el agente de ventas. Soporta verificación
pre-envío y pre-recepción desde v0.1.0 (scope extendido por §7.5.3 EP-13).

```python
def sales_agent_guardrail_register(
    guardrail: GuardrailDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — guardrail "informa como enfermera, nunca prescribe":
registry.sales_agent_guardrail_register(
    GuardrailDef(
        name="vitalia.no_medical_recommendations",
        pre_send_check=lambda msg, ctx: GuardrailResult(
            blocked="prescrib" in msg.lower() or "diagnóstic" in msg.lower(),
            reason="Vitalia no emite diagnósticos ni prescripciones médicas. "
                   "El agente informa como enfermera; deriva al médico.",
        ),
        priority=1,
        mode="block",
    )
)

# Ejemplo Comunify:
registry.sales_agent_guardrail_register(
    GuardrailDef(
        name="comunify.no_spam_guardrail",
        pre_send_check=lambda msg, ctx: GuardrailResult(
            blocked=len(msg) > 2000,
            reason="Mensajes demasiado largos se marcan como spam en plataformas de creadores.",
        ),
        pre_receive_check=lambda msg, ctx: GuardrailResult(blocked=False),
        priority=50,
        mode="warn",
    )
)
```

---

### EP-14 — `copilot_kb_pack_register` (DataClass)

Registra un paquete de base de conocimiento para el copiloto. `tenant_scope` tri-modal:
`"brand"` (todas las instancias de la marca), `"tenant"` (solo el tenant específico),
`"both"` (global de marca + override tenant).

```python
def copilot_kb_pack_register(
    pack: KbPackDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — protocolo médico brand-scope + KB interna de clínica tenant-scope:
registry.copilot_kb_pack_register(
    KbPackDef(
        pack_id="vitalia.medical_protocols_kb_pack_v1",
        documents_path="./kb/vitalia/medical_protocols/",
        embedding_model_ref="text-embedding-3-large",
        qdrant_collection_name="vitalia-medical-protocols",
        tenant_scope="both",
    )
)

registry.copilot_kb_pack_register(
    KbPackDef(
        pack_id="vitalia.clinica_internal_kb_pack_v1",
        documents_path="./kb/tenant/{tenant_id}/",
        embedding_model_ref="text-embedding-3-small",
        qdrant_collection_name="vitalia-clinica-internal",
        tenant_scope="tenant",
    )
)

# Ejemplo Lupulo:
registry.copilot_kb_pack_register(
    KbPackDef(
        pack_id="lupulo.carta_cervezas_kb",
        documents_path="./kb/lupulo/menu/",
        embedding_model_ref="text-embedding-3-small",
        qdrant_collection_name="lupulo-menu",
        tenant_scope="brand",
    )
)
```

---

### EP-15 — `crm_lifecycle_stage_register` (DataClass)

Registra una etapa personalizada del ciclo de vida del CRM, insertada entre etapas existentes.

```python
def crm_lifecycle_stage_register(
    stage: LifecycleStageDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — etapa "pendiente anamnesis" entre signup y activo:
registry.crm_lifecycle_stage_register(
    LifecycleStageDef(
        stage_id="vitalia.pendiente_anamnesis",
        label="Pendiente Anamnesis",
        after_stage="signup",
        before_stage="active",
    )
)

# Ejemplo Lupulo — etapa "reserva confirmada":
registry.crm_lifecycle_stage_register(
    LifecycleStageDef(
        stage_id="lupulo.reserva_confirmada",
        label="Reserva Confirmada",
        after_stage="qualified",
        before_stage="active",
    )
)
```

---

### EP-16 — `iam_signup_handler` (Callable)

Registra un handler de signup personalizado que se invoca cuando Clerk notifica un
nuevo usuario. Puede aprobar, poner en revisión o rechazar el acceso.

```python
def iam_signup_handler(
    handler: Callable[[Any, BrandContext], SignupResult],
    *,
    name: str,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — verificación de matrícula médica:
def _vitalia_validate_medical_license(clerk_user, ctx: BrandContext) -> SignupResult:
    """Verifica matrícula médica antes de activar cuenta."""
    license_number = clerk_user.metadata.get("medical_license_number")
    if not license_number:
        return SignupResult(
            status="pending_review",
            metadata={"reason": "Se requiere número de matrícula médica para activar la cuenta."},
        )
    is_valid = validate_medical_license(license_number)
    return SignupResult(
        status="approved" if is_valid else "rejected",
        metadata={"license_validated": is_valid},
    )

registry.iam_signup_handler(
    _vitalia_validate_medical_license,
    name="vitalia.medical_license_signup",
)

# Ejemplo Comunify — alta inmediata para creadores:
registry.iam_signup_handler(
    lambda clerk_user, ctx: SignupResult(status="approved", metadata={"source": "comunify_signup"}),
    name="comunify.creator_auto_approve",
)
```

---

### EP-17 — `tenant_plan_tier_register` (DataClass, override permitido)

Registra un tier de plan personalizado para la marca. **`mode='override'` está permitido**
para redefinir el tier sin duplicarlo.

```python
def tenant_plan_tier_register(
    tier: PlanTierDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia:
registry.tenant_plan_tier_register(
    PlanTierDef(
        tier_id="vitalia.clinica_basica",
        label="Clínica Básica",
        price_monthly=49.0,
        currency="USD",
        features=("agente_ventas", "1_profesional", "agenda_basica"),
        limits={"max_appointments_month": 100},
    )
)

# Ejemplo Lupulo:
registry.tenant_plan_tier_register(
    PlanTierDef(
        tier_id="lupulo.cerveceria_pro",
        label="Cervecería Pro",
        price_monthly=29.0,
        currency="USD",
        features=("reservas_ilimitadas", "menu_digital", "analytics"),
        limits={"max_tables": 50},
    )
)
```

---

### EP-18 — `onboarding_wizard_steps_register` (DataClass, override permitido)

Registra pasos personalizados del wizard de onboarding para la marca. **`mode='override'`
está permitido** para redefinir pasos sin duplicarlos.

**También disponible como tipo TypeScript** (ver `@luana/extension-sdk`).

```python
def onboarding_wizard_steps_register(
    step: WizardStepDef,
    *,
    mode: Literal["append", "override"] = "append",
) -> None: ...

# Ejemplo Vitalia — paso de configuración de consentimientos:
registry.onboarding_wizard_steps_register(
    WizardStepDef(
        step_id="vitalia.setup_consentimientos",
        title="Configuración de Consentimientos",
        component_ref="VitaliaConsentSetupStep",
        prereqs=("vitalia.setup_clinica",),
        skippable=False,
        post_action_event="vitalia.consentimientos.configured",
    )
)

# Ejemplo Comunify:
registry.onboarding_wizard_steps_register(
    WizardStepDef(
        step_id="comunify.setup_canal_youtube",
        title="Conecta tu Canal de YouTube",
        component_ref="ComunifyYouTubeConnectStep",
        skippable=True,
        post_action_event="comunify.youtube.connected",
    )
)
```

---

## 4. Receta: Construir un Agente Vertical sobre luana-core

> **Principio fundamental:** el agente vertical ES un APP del brand, NO un EP del core.
> **NO EP-19.** No existe `vertical_agent_register` ni ningún EP análogo. Los agentes
> verticales son aplicaciones de marca que componen los paquetes de `luana-core`. El core
> provee los primitivos; las marcas los componen.

### Ejemplo trabajado: Vitalia Treatment Agent

**Caso de uso:** agente de seguimiento pre/post-operatorio para pacientes de clínicas
estéticas. El agente mantiene sesiones multi-turno, envía recordatorios de cuidados,
responde preguntas de recuperación y deriva al médico cuando la situación lo requiere.

**Restricción legal crítica:** el agente informa como enfermera de apoyo. NUNCA emite
diagnósticos ni prescripciones médicas. Esta restricción está implementada como
guardrail en EP-13 y es obligatoria para cumplir con la Ley 26.529 (Argentina).

### Arquitectura del agente

```
vitalia/backend/src/modules/vitalia/
└── agents/
    └── treatment_agent/
        ├── __init__.py
        ├── agent.py                     # nodo LangGraph + graph definition
        ├── callback_handler.py          # VitaliaTreatmentCallbackHandler
        ├── observability_context.py     # VitaliaTreatmentObservabilityContext
        └── tools.py                     # tools registradas via EP-3
```

### Composición de paquetes luana-core

```python
# vitalia/backend/src/modules/vitalia/agents/treatment_agent/callback_handler.py
from luana_core_observability import BaseAgentCallbackHandler

class VitaliaTreatmentCallbackHandler(BaseAgentCallbackHandler):
    """Callback handler para el agente de seguimiento Vitalia.

    Hereda observabilidad base (trazas, costos, PII sanitization)
    y agrega contexto clínico al registro de cada turno.
    """
    # Subclasifica BaseAgentCallbackHandler — no mirrors, no duplicación.
    # Ver .claude/rules/anti-duplication.md — shared abstractions inventory.
    pass


# vitalia/backend/src/modules/vitalia/agents/treatment_agent/observability_context.py
from luana_core_observability import BaseObservabilityContext

class VitaliaTreatmentObservabilityContext(BaseObservabilityContext):
    """Contexto de observabilidad para el tratamiento Vitalia.

    Agrega campos específicos: patient_id (anon), procedure_type, session_phase.
    """
    patient_id_anon: str   # hash irreversible del ID del paciente (nunca PII real)
    procedure_type: str
    session_phase: str     # "pre_op" | "post_op_day1" | "post_op_week1" | "followup"
```

### Registro via Extension SDK (EP-3, EP-8, EP-13, EP-14)

```python
# vitalia/backend/src/modules/vitalia/extensions.py
from luana_core_extension_sdk import ExtensionPointRegistry
from vitalia.agents.treatment_agent.tools import (
    _medical_consent_request,
    _treatment_status_check,
)


def register_vitalia_extensions(registry: ExtensionPointRegistry) -> None:
    """Registra todas las extensiones de Vitalia, incluyendo el treatment_agent."""

    # EP-3: herramientas del agente de tratamiento
    registry.sales_agent_tool_register(
        ToolDef(
            name="vitalia.treatment_session_reminder_tool",
            description=(
                "Envía recordatorio de cuidados post-operatorios al paciente vía WhatsApp. "
                "Incluye instrucciones personalizadas según el procedimiento realizado."
            ),
            input_schema={
                "type": "object",
                "required": ["patient_id", "procedure", "days_post_op"],
                "properties": {
                    "patient_id": {"type": "string"},
                    "procedure": {"type": "string"},
                    "days_post_op": {"type": "integer"},
                },
            },
            handler=_send_treatment_reminder,
            tool_groups=("post_treatment", "scheduling"),
        )
    )

    registry.sales_agent_tool_register(
        ToolDef(
            name="vitalia.treatment_status_check_tool",
            description="Verifica el estado del tratamiento del paciente en el historial clínico.",
            input_schema={
                "type": "object",
                "required": ["patient_id"],
                "properties": {"patient_id": {"type": "string"}},
            },
            handler=_treatment_status_check,
            tool_groups=("knowledge", "clinical"),
        )
    )

    # EP-8: canal WhatsApp para el treatment_agent
    registry.channel_adapter_register(
        ChannelAdapterDef(
            channel_slug="vitalia.treatment_whatsapp_adapter",
            send=vitalia_wa_send,
            receive=vitalia_wa_receive,
            format_for_channel=vitalia_wa_format,
            target_agent_runtime="vertical_brand",
            webhook_handler=vitalia_wa_webhook,
        )
    )

    # EP-13: guardrail obligatorio — informa como enfermera, nunca prescribe
    registry.sales_agent_guardrail_register(
        GuardrailDef(
            name="vitalia.no_medical_recommendations",
            pre_send_check=_no_prescriptions_check,
            priority=1,       # máxima prioridad — siempre se evalúa primero
            mode="block",
        )
    )

    # EP-14: base de conocimiento médica (brand-scope) + KB interna de clínica (tenant-scope)
    registry.copilot_kb_pack_register(
        KbPackDef(
            pack_id="vitalia.medical_protocols_kb_pack_v1",
            documents_path="./kb/vitalia/medical_protocols/",
            embedding_model_ref="text-embedding-3-large",
            qdrant_collection_name="vitalia-medical-protocols",
            tenant_scope="both",
        )
    )
```

### Composición de luana-core-scheduling

El treatment_agent usa el scheduler para enviar recordatorios automáticos:

```python
# vitalia/backend/src/modules/vitalia/agents/treatment_agent/agent.py
from luana_core_scheduling import JobQueue

class VitaliaTreatmentAgent:
    """Agente de seguimiento post-operatorio.

    Consume:
    - luana-core-scheduling: enqueue de recordatorios pre/post sesión
    - luana-core-channels: via EP-8 (vitalia.treatment_whatsapp_adapter)
    - luana-core-marketing-kb: via EP-14 (medical_protocols + clínica interna)
    - luana-core-prompt-cache: slot 5 BRAND_VOICE via D-T3 BrandVoicePort (Story 7)
    - luana-core-extension-sdk: para EP-3 tools + EP-13 guardrails
    """

    def __init__(self, job_queue: JobQueue, brand_voice_port: BrandVoicePort):
        self.job_queue = job_queue
        self.brand_voice = brand_voice_port

    async def schedule_post_op_reminders(
        self, patient_id: str, procedure: str, appointment_date: str
    ) -> None:
        """Programa recordatorios automáticos para los días 1, 3 y 7 post-operatorio."""
        reminder_schedule = [
            (86400, "post_op_day1", "vitalia/check_24h.j2"),
            (86400 * 3, "post_op_day3", "vitalia/check_3d.j2"),
            (86400 * 7, "post_op_week1", "vitalia/check_7d.j2"),
        ]
        for delay_seconds, session_phase, template_ref in reminder_schedule:
            await self.job_queue.enqueue(
                "vitalia.send_treatment_reminder",
                patient_id=patient_id,
                procedure=procedure,
                session_phase=session_phase,
                template_ref=template_ref,
                run_at=appointment_date,
                delay_seconds=delay_seconds,
            )
```

### Slot 5 BRAND_VOICE via D-T3 BrandVoicePort (Story 7)

```python
# El agente consume el BrandVoicePort de Story 7 para inyectar la voz de la clínica
# en el prompt del agente — slot 5 BRAND_VOICE del compilador de personalidad.

from luana_core_sales_agent.ports.brand_voice import BrandVoicePort

brand_voice_port = BrandVoicePort(tenant_id=tenant_id)
system_instruction = await brand_voice_port.get_system_instruction()
# → inyectado en el prompt del treatment_agent vía slot 5 del PromptCacheComposer
```

### Lifespan de la app Vitalia

```python
# vitalia/backend/src/modules/vitalia/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from luana_core_extension_sdk import ExtensionPointRegistry
from vitalia.extensions import register_vitalia_extensions


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ExtensionPointRegistry(
        # Stories 11-13 wiran los adaptadores reales:
        # sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tool_registry),
        # copilot_workflow_registry_adapter=_CopilotWorkflowRegistryAdapter(workflow_registry),
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )
    register_vitalia_extensions(registry)
    registry.close()
    app.state.registry = registry
    yield


app = FastAPI(lifespan=lifespan, redirect_slashes=False)
```

---

## 5. Cross-Brand Learning Principle (Principio de Aprendizaje Cross-Brand)

> **Del outcome §7.5.6:** "cada marca inventa para sí misma; el core generaliza lo que
> demuestra ser universal."
>
> Features that prove universal **graduate to core** via `/pm` promotion path — brands B,
> C, D then consume the same primitive via SDK without knowing about each other.

### El camino de graduación

```
Marca A inventa feature X
  ↓
X se prueba en producción (batalla real — pacientes, creadores, comensales)
  ↓
/pm evalúa: ¿X es generalizable a otras marcas?
  ↓
Si sí → lift a luana-core-{domain} → marcas B, C, D consumen el mismo primitivo via SDK
Si no → X queda en vitalia/backend/src/modules/vitalia/ como EP registrado o código interno de marca
```

### Ejemplo concreto: de Vitalia a luana-core

1. **Vitalia inventa** el agente de seguimiento pre/post-operatorio con recordatorios
   programados (Story 8 + Stories 11-13 bootstrap).
2. **Battle-tested** en clínicas estéticas LATAM durante Story 11.5+ Vitalia bootstrap.
3. **/pm evalúa:** ¿el patrón "recordatorio de seguimiento post-conversión" es útil
   para Comunify (post-masterclass) y Lupulo (post-cena/evento)?
4. **Si sí:** el patrón se generaliza como `luana-core-engagement-scheduler` con:
   - Interfaz agnóstica de vertical
   - Marcas consumen via `JobQueue.enqueue("core.send_engagement_reminder", ...)`
   - Vitalia, Comunify, Lupulo usan el mismo primitivo sin saber de las otras marcas.
5. **Si no** (uso muy específico al contexto médico): permanece en `vitalia/backend/src/modules/vitalia/`.

### Invariante fundamental: NO importación cross-brand

```python
# CORRECTO — via SDK primitivo
from luana_core_scheduling import JobQueue  # core provision

# CORRECTO — via EP propio
registry.sales_agent_tool_register(ToolDef(name="vitalia.reminder_tool", ...))

# PROHIBIDO — importación directa entre marcas
from vitalia.agents.treatment_agent import VitaliaTreatmentAgent  # ❌ NUNCA
from comunify.tools.youtube_connect import ComunifyYouTubeConnect  # ❌ NUNCA
```

El namespace CC-4 (`vitalia.*`, `comunify.*`, `lupulo.*`) garantiza que incluso dentro
del registry global, los registros de cada marca están aislados. El core enruta por
`brand_slug` sin cruzar fronteras.

### Costo de pagar hoy vs. refactorizar mañana

La decisión de pagar el precio de diseñar bien desde el principio (CC-1..CC-5, namespace,
inmutabilidad, startup-only) responde a la experiencia con sistemas de plugins en
producción: un plugin system que permite registro en runtime, importaciones cross-brand
o mutación post-startup inevitablemente produce bugs de estado difíciles de reproducir
y regresiones silenciosas.

El contrato v0.1.0 es deliberadamente estricto. EP-6..EP-18 son signature-only precisamente
para no comprometer implementaciones antes de entender los patrones reales de uso. La
iteración ocurre en v0.2.x, cuando las brands bootstraps (Stories 11-13) muestren qué
dispatch necesitan realmente.

---

*Este documento es generado y mantenido por el equipo de arquitectura de Luana Platform.*
*Ver `core/luana-core-extension-sdk/` para el código fuente del SDK.*
*Ver `core/luana-core-extension-sdk/tests/unit/` para el smoke pack de referencia (`test-brand`).*
