<!-- voseo-allowed: internal session documentation, architecture exploration, Spanish LatAm regional dialect in decision notes -->

# Vitalia Shell Organism — Sesión base 2026-05-21

> **Propósito:** snapshot maestro de TODO lo decidido + pendiente en la conversación de rediseño agéntico de vitalia. Punto de retoma cuando se rompa contexto. Leer este doc PRIMERO antes de continuar.
>
> **Estado conversación:** 4 de 6 preguntas resueltas. Próxima decisión: cuál iteración de subestructura Lucas (v1 features vs v2 ciclo-temporal). Luego Q5 (pagos) + Q6 (audit log HIPAA) → estructura completa.
>
> **Última actualización:** 2026-05-21
> **Branch:** `wip/vitalia` (no rotar — same canónico)
> **Status story:** `vitalia-shell-organism` informal (no checkpoint.md formal aún)

---

## 1. Por qué existe esta sesión

Chris detectó que el frontend vitalia "se ve pésimo": el sidebar tiene 6 links hardcoded de los cuales 5 apuntan a routes inexistentes (`/dashboard/patients` cuando la route real es `/patients`, etc.) y hay 13 features shippeadas-pero-orphan invisibles al usuario (`/marketing`, `/inbox`, `/fidelizacion`, `/medical-compliance`, `/brand-studio`, `/offers`, etc.).

La hipótesis inicial era "actualizar el sidebar". La conversación evolucionó a un **rediseño paradigmático completo**:

- Pasar de la metáfora "studios/módulos" (nicolify) a la metáfora "**empleados IA**" como organizadores top-level.
- Cada empleado IA tiene rol + foto + color + dominio del negocio.
- El sistema completo es manipulable conversacionalmente vía Valeria-chat (visión norte: dueño de clínica opera todo desde WhatsApp como si tuviera secretaria real).

---

## 2. Visión norte cementada

> **"Como una secretaria real."** El dueño de la clínica le habla a Valeria por WhatsApp/web y le pide información o acciones sin entrar al sistema. Valeria delega internamente a Lisa/Lucas/Adrián/Camila según corresponda. El sistema web existe para ser manejado por los agentes; la cara visual es solo visualización de lo que los agentes ejecutan.

**Implicancias arquitectónicas:**
- Backend DDD intacto (`compliance/`, `marketing/`, `fidelizacion/`, `sales_agent/`, `crm/`, `clinics/`, etc. siguen como están).
- Frontend FSD intacto (`features/{inbox,marketing,fidelizacion,...}` siguen como están).
- Los "dueños agéntico" son **etiquetas de navegación + UX + marketing**, no estructura de filesystem.
- LangGraph multi-agente sí debe acomodarse — pero es trabajo futuro de sesión dedicada (anotado en `vitalia/docs/architecture/notes/langgraph-multi-agent-layout.md`).

---

## 3. Set final de agentes (cementado)

| Tab | Agente | Color | Rol resumen | PNG local |
|---|---|---|---|---|
| Mi Clínica | 🟢 **Lisa** | `#00D084` | Estratega de marca + escalera de valor + catálogo tratamientos + doctores + compliance + landing | `vitalia/frontend/public/agents/lisa/` |
| Atraer | 🖤 **Lucas** | `#111111` | Growth: campañas (pagas+orgánicas) + creatividades + tendencias mercado | `vitalia/frontend/public/agents/lucas/` |
| Vender | 🔵 **Adrián** | `#01b2f8` | Closer: inbox + pipeline + reservas + cualificación + outbound | `vitalia/frontend/public/agents/adrian/` |
| Operar | 🟣 **Valeria** | `#7b2d91` | Día-a-día: agenda + pacientes activos + tratamientos en curso + tareas + check-in/out + **chat principal shell** | `vitalia/frontend/public/agents/valeria/` |
| Mantener | 🟦 **Camila** | `#180d95` | Relación cliente: testimonios + reseñas + NPS + ausencia + referidos + reputación online + menciones redes | `vitalia/frontend/public/agents/camila/` |
| Configurar | ⚙️ — | (ícono genérico) | Setup técnico + conexiones + roles + apariencia + integraciones | n/a |
| (transversal) | 🟡 **Mateo** | `#fee209` | Sin tab. Asiste en landing (sí o sí) + diseño gráfico futuro | `vitalia/frontend/public/agents/mateo/` |

**5 tabs con cara + 1 tab genérica.** Valeria además es el chat persistente en el panel izquierdo del shell (rol dual: tab "Operar" + chat-router del shell).

---

## 4. Principios cementados durante la sesión

### P1 — Atomic ownership (Q2/Q3)
Cada átomo de información (testimonio, reseña, mención, paciente, tratamiento, etc.) tiene **un dueño semántico** (= el agente bajo cuya tab se produce/cura/monitorea). Los demás agentes son **consumidores read-only** vía import/projection.

| Átomo | Dueña | Consumidores principales |
|---|---|---|
| Identidad de marca, estrategia comercial, escalera de valor, catálogo, doctores, landing strategy, compliance | 🟢 Lisa | Todos los demás |
| Campañas, creatividades, copy, tendencias mercado | 🖤 Lucas | Camila (sourcing), Mateo (assets landing) |
| Conversaciones, leads, pipeline, scoring, reservas, attribution | 🔵 Adrián | Lucas (segmentos), Camila (cohortes) |
| Agenda, pacientes activos, tratamientos en curso, tareas | 🟣 Valeria | Adrián (booking confirmation), Camila (followup trigger) |
| Testimonios, reseñas, casos pre/post, NPS, ausencia, referidos, menciones | 🟦 Camila | Lisa (landing), Lucas (campaign content), Mateo (website) |
| Tenant, conexiones, roles, apariencia, webhooks, LLM keys | ⚙️ Configurar | Todos los demás (CTAs inline cuando falta conexión) |

**Implementación técnica:** átomos viven en backend module dueño. Tabs consumidoras solo hacen `GET` read-only. Mutaciones solo desde la tab dueña. NO se duplica.

### P2 — Recomendaciones de cualquier agente = notificaciones cross-shell (Q4)
NO son sub-tab dedicada. Son **señales temporales** que viven en el bell icon de la TopBar (modelo Facebook/Linear/GitHub). Click en notificación → deep-link al átomo concreto donde tomar la acción.

Cada agente además puede mostrar tips contextuales inline en su vista (modelo Notion AI/Copilot), pero el centro de "lo nuevo / urgente" es UN solo bell.

### P3 — Conexiones SIEMPRE viven en Configurar + CTAs inline (Q4)
Una sola tab dueña de TODAS las conexiones (Meta, Google, WhatsApp Business, Stripe, MercadoPago, etc.). En cualquier feature que requiera conexión faltante, componente reusable `<RequireConnection provider="meta_ads">` muestra inline:
> "Necesitas conectar Meta Ads — [Conectar ahora]" → deep-link a `/configurar/conexiones/{provider-slug}` con return URL preservada.

### P4 — Campañas son workspaces, no formularios (Q4)
Una campaña no es "$presupuesto + audiencia + plataforma". Es proyecto completo: brief + audiencia + creatividades + copy + materiales + aprobación + performance + post-mortem. Inspirado en Meta Ads Manager + Loomly + Sprout Social.

### P5 — Backend/Frontend NO se rearman según agentes (Q3 cement explícito Chris)
La metáfora agéntica es UI + UX + marketing. La estructura DDD backend y FSD frontend siguen organizadas por **dominio del negocio**, no por agente. Solo la **navegación** (tabs + sub-tabs + rutas visibles) sigue la metáfora agéntica.

---

## 5. Decisiones tomadas (registro Q-by-Q)

| # | Pregunta | Decisión | Razón |
|---|---|---|---|
| Q1 | ¿Mateo a Configurar? | **NO — Configurar es ícono genérico** | Chris prefiere set de empleados-cara separado de Configurar funcional |
| Q1.b | ¿Qué hacemos con Mateo? | **Transversal sin tab** | Mateo asiste en landing (sí o sí) + diseño gráfico futuro; PNGs conservados en `frontend/public/agents/mateo/` |
| Q2 | Reseñas Google/Yelp ¿Camila o Lisa? | **Camila dueña de TODO lo de relación con cliente (incluido testimonios + casos pre/post)** | Lisa hace estrategia, Camila monitorea+ejecuta. Principio P1 cementado. |
| Q3 | Menciones redes sociales ¿Camila o Lucas? | **Camila (menciones marca) + Lucas (tendencias mercado)** | Separación clara: cliente vs mercado. Bajo P1. |
| Q4 | Calendario contenido orgánico ¿Lucas o tab nueva? | **Lucas — unificado con campañas pagas** | Mismo objetivo (atraer); diferencia paga/orgánica = atributo, no rama de menú. Más 3 ajustes Chris: recomendaciones cross-shell, conexiones en Configurar, campañas = workspace. |
| Q4.b | Subestructura Lucas: v1 features vs v2 ciclo temporal | **v2 ciclo temporal** (Lanzar / En vuelo / Recursos / Resultados / Mercado) | Calza mejor con metáfora agéntica; reduce fricción de decisión al abrir tab; replicable a otros agentes para consistencia narrativa. |
| Q-valeria-macro | Universo Valeria/Operar: qué entra, qué se simplifica | **Sitemap 3 sub-tabs: Agenda · Pacientes · Caja.** Simplificaciones: sin perfil doctor, sin notas médicas/prescripción/consentimientos (no es PMS, es marketing+ventas+follow-up); cobro inline en slot agenda; "Crear cita" dropdown {🚶 Walk-in · 📞 Teléfono}; click slot → drawer detalle con subform Cobrar saldo; sub-tab Caja solo reporte/cierre, no captura. Ver § 11 detalle. |
| Q-doctores | ¿Dónde vive "Doctores" (horarios + vacaciones + servicios)? | **🟢 Mi Clínica (Lisa)** — doctores son asset semi-estático de la clínica como entidad. Bloqueos del momento (Dr. X llamó que no viene hoy) inline en Agenda (Valeria) con un clic. Separa setup estable (Lisa) vs ajuste operativo (Valeria). |
| Q5 | Pagos en recepción ¿Operar/Valeria o Configurar? | **Eliminar sub-tab Caja.** Post benchmark Square/Jane/Cliniko/Pabau 2026 — apps modernas NO tienen "tab Caja" estilo ERP. Cobro siempre inline desde slot agenda (drawer). Valeria queda con **2 sub-tabs: Agenda · Pacientes**. Estado cuenta paciente vive en su ficha; cohort deudores = filtro segmento en directorio; anticipos sin imputar = bell notification; reportes financieros = se deciden cuando lleguemos a Lisa (KPI estratégico clínica) o botón TopBar. Setup gateway sigue en Configurar con `<RequireConnection>` inline. |
| Q6 | Audit log HIPAA ¿Lisa o Configurar? | **Híbrido suave.** Post foco-reset marketing+ventas+CLTV (vertical electivo, sin historial médico). Compliance dashboard ligero en 🟢 Lisa → Compliance sub-tab (status semáforo + política retención + reportes exportables) + raw log técnico discreto en ⚙️ Configurar → Avanzado → Registro técnico (uso poco frecuente IT/forensics). NO panel pesado tipo Vanta. Patient transparency = futuro Patient Portal. |
| Q-mi-clinica | Estructura macro Lisa (Mi Clínica) | **4 sub-tabs cementadas**: 🏥 Marca · 👨‍⚕️ Doctores (CRUD adecuado, perfil-marca rico) · 🩺 Servicios · 🛡️ Compliance. Brand Studio heredado Nicolify adaptado salud (clínica como sumatoria de doctores, no gran corporativa). Ver § 11 detalle. |
| Q-servicios-vs-ladder | ¿Tratamientos y Escalera son sub-tabs separadas? | **NO — una sub-tab "Servicios" con toggle Catálogo (CRUD flat) \| Escalera de valor (canvas estratégico)**. Post benchmark value ladder vertical electivo (dental/estética/psico): mismo treatment puede aparecer en múltiples niveles con roles distintos. Ladder = composición de slots que referencian treatments del catálogo (no atributo del treatment). Para vertical electivo el ladder ES el modelo de negocio, no feature opcional. |
| Q-vender-macro | Estructura macro Adrián (Vender) | **4 sub-tabs cementadas**: 💬 Inbox · 🎯 Embudo (toggle 📋 Kanban \| 📑 Lista CRM) · 📣 Outbound · 💼 Propuestas opt-in. REUSE mockups ratificados v1 Batch 2 (inbox.html) + Batch 3 (pipeline.html). Incorpora: Segmented control 3-modos (Adrián decide/consulta/Yo escribo) · 6 stages dental ratificados (Interesado→Calificando→Considerando→Listo→Reservado→Decidió no) · atribución agéntica visible (Lucas/Adrián por columna) · Activity stream observabilidad · Voice transcript + image analysis + Revertir 4:32. REUSE backend shipped: `vitalia/backend/src/modules/vitalia/{inbox,sales_agent,fidelizacion,crm,patients}/` + 5 templates Meta-approved + tools médicas + guardrails (no_diagnosis/no_prescription) + archetype warm_close. Gap shippeado: **Pipeline NO existe en vitalia** (solo mockup), REUSE base `nicolify/frontend/src/features/closer-studio/`. Ver § 11 detalle. |
| Q-mantener-macro | Estructura macro Camila (Mantener) | **4 sub-tabs cementadas**: 🎧 Escucha · 🌟 Pruebas sociales · 🪃 Reactivar · 📊 Reputación. Diferencia clara con Adrián Outbound: **Camila Reactivar audience = pacientes existentes (post-revenue); Adrián Outbound audience = leads (pre-paciente)**. Referidos mudan de Lucas (Marketing) a Camila per P1 atomic ownership. Renombre "Cohorts" → "Listas de reactivación" (jerga SaaS confundía). 8 listas dinámicas para vertical electivo: sin actividad reciente, fin tratamiento sin recall, mantenimiento por vencer, promotor NPS sin referir, cumpleaños, aniversario cliente, propuesta sin firmar, detractor NPS pendiente recovery. REUSE shipped: `vitalia/backend/src/modules/vitalia/{fidelizacion,marketing/referrals_leaderboard,sales_agent}` + NPS shipped orphan + 5 templates Meta-approved. Gaps planned: reseñas externas multi-canal, reputación agregada, menciones redes. Ver § 11 detalle. |
| Q-configurar-macro | Estructura macro Configurar | **3 sub-tabs cementadas (versión simplificada — patrón "Valeria hace todo conceptualmente, Configurar es panel del dueño usado 1-2x/mes")**: 🏢 Mi cuenta (info clínica + plan facturación Luana + equipo) · 🔌 Conexiones HUB detallado **estilo nicolify** (REUSE `nicolify/frontend/src/features/connections/` 12 providers + grid health semáforo + per-provider drawer OAuth/sync/permissions/config/disconnect) · 🔬 Avanzado (reglas + audit log raw + LLM keys + flags + API tokens + import/export + zona peligrosa). NO incluye marca visual/voz/landing (ese es 🟢 Lisa). NO incluye doctores/horarios (ese es 🟢 Lisa). Single tab del shell SIN cara agéntica (Configurar es panel admin, no empleado IA). Ver § 11 detalle. |
| Q-camila-v3 | Refit Camila: fusión Escuchar+Curar + separar growth/churn | **Camila refit v3**: 4 sub-tabs **🎤 Voz del paciente** (UN flujo: entrante→curaduría→activos vivos, reemplaza Escucha+Pruebas sociales separadas) · 🪃 Reactivar (churn defense — listas en riesgo) · 🤝 Multiplicar (growth — referidos + advocacy promotores) · 📊 Reputación. Fusión Escuchar+Curar refleja la realidad: input + procesamiento + publicación son UN flujo, no dos. Separación Reactivar (dormants/riesgo) vs Multiplicar (promotores/advocacy) honra que son audiencias distintas pese a infra compartida. Términos: todos verbos activos, sin ambigüedad "Curar" en vertical clínico. |
| Q7 | ¿Modelo cross-agente — ciclo-temporal v2 a todos o per-agente? | **Opción A — Modelo propio per agente según naturaleza del rol** (formalización de lo cementado). Lucas único ciclo-temporal v2 puro (5 cols: Lanzar/En vuelo/Recursos/Resultados/Mercado — marketing tiene ciclo natural). Lisa/Adrián/Camila modelo espacial 4 sub-tabs. Valeria espacial 2 (recepción día a día). Configurar espacial 3 (sin cara agéntica). Coherencia metafórica viene del color+foto+rol per agente (§ 3), NO de uniformidad estructural cross-tab. Validado por industria: Slack/Notion/Linear cada workspace estructura propia, sin "uniformidad" como UX value. |
| Q-camila-agente-ops | Cómo opera Camila como agente IA (no UI pasiva) | **Paradigma 3-modos extensible** (mismo que Adrián Inbox): 🤖 Camila decide (default auto-procesa entrante) / 💬 Camila consulta (sugiere + vos aprobás) / ✍️ Yo decido. Toggle global header + override por tipo de señal. **12 triggers cementados SSoT** (NPS 9-10/7-8/0-6 · reseñas ≥4⭐/3-4⭐/<3⭐ · menciones positiva/negativa · dormant 60d · fin tratamiento · mantenimiento por vencer · promotor sin referir · cumpleaños · propuesta sin firmar · imagen testimonio). Acciones default con preview + timer + Revertir (3-5min) + audit log + compliance gate `requires_marketing_opt_in` enforced. Reglas configurables en ⚙️ Configurar → Avanzado → Reglas Camila. Defaults sensibles por vertical (dental/estética más outbound · psico/psiquiatría conservador). Modelo Valeria-céntrico: dueño habla con Valeria por chat, Valeria delega a Camila. Camila trabaja en background + responde eventos + invocable explícita via Valeria. Paciente nunca ve "Camila" — solo mensajes desde la clínica. |

## 6. Decisiones pendientes (próximas)

**TODAS LAS PREGUNTAS DE DISEÑO CERRADAS** ✅ (Q1, Q1.b, Q2, Q3, Q4, Q4.b, Q-valeria-macro, Q-doctores, Q5, Q6, Q-mi-clinica, Q-servicios-vs-ladder, Q-vender-macro, Q-mantener-macro, Q-configurar-macro, Q-camila-v3, Q7, Q-camila-agente-ops). Próximo paso: artefactos finales (mockup + navigation-tree + handoff /pm-vitalia).

---

## 7. Catálogo de artefactos creados esta sesión

### Documentos (en `vitalia/docs/product/stories/vitalia-shell-organism/`)

| Archivo | Propósito | Estado |
|---|---|---|
| `00-session-baseline.md` | **ESTE doc** — punto de retoma | live |
| `nicolify-feature-inventory.md` | Inventario exhaustivo de TODAS las funcionalidades nicolify (referencia para qué átomos copiar/adaptar al vertical médico) | ✅ completo |
| `vitalia-feature-inventory.md` | Inventario exhaustivo TODO lo construido en vitalia hoy (59 capabilities + sidebar real + brand config). Diagnóstico de gaps. | ✅ completo |
| `agentic-navigation-proposal.md` | Primera propuesta árbol agéntico (6 top-level: 5 agentes + 1 config). 10 preguntas pendientes. | 🟡 obsoleto parcial — será reemplazado por estructura final post Q6 |
| `navigation-tree.md` | Árbol JSON editable por Chris (en edición humana) | 🟡 user editing |
| `mockups/dual-mode-shell.html` | Mockup HTML interactivo modo web/agéntico, layout 50/50, navegación direccional. Estado pre-Apple (Tailwind-classic teal/slate). | ✅ live mockup |

### Scripts (en `scripts/r2/`)

| Archivo | Propósito | Estado |
|---|---|---|
| `upload-platform-agents.sh` | Sube los 6 PNGs agentes (incluida Lisa) a R2 `luana-assets-platform/agents/`. Soporta wrangler o rclone. Dry-run validado. | ⏳ pendiente credenciales R2 |

### Assets (en `vitalia/frontend/public/agents/`)

| Path | Contenido |
|---|---|
| `lisa/{thumbnail,full}.png` | ✅ copiados |
| `valeria/{thumbnail,full}.png` | ✅ copiados |
| `adrian/{thumbnail.png,full.jpeg}` | ✅ copiados (Adrián full es jpeg porque no había png) |
| `lucas/{thumbnail,full}.png` | ✅ copiados |
| `camila/{thumbnail,full}.png` | ✅ copiados |
| `mateo/{thumbnail,full}.png` | ✅ copiados (reservados para uso transversal futuro) |

**Pendiente R2:** Chris debe ejecutar `wrangler login` (opción A) o entregar API token (opción B). Ver `scripts/r2/upload-platform-agents.sh` head para instrucciones.

### Notas arquitectónicas (en `vitalia/docs/architecture/notes/`)

| Archivo | Propósito |
|---|---|
| `langgraph-multi-agent-layout.md` | Inquietud anotada de Chris: cuando toque refactor LangGraph multi-agente, decidir entre 3 layouts (carpeta única `agents/` vs módulos separados `luana-core-agent-{nombre}/` vs híbrido subagent-as-tool). Investigación pre-decision pendiente. |

### Decisiones cross-platform pendientes (en `docs/promotion-protocol/proposals/`)

| Archivo | Estado | Esperando |
|---|---|---|
| `2026-05-21-luana-core-ui-extraction.md` | `state: proposed` | Ratificación Chris |
| `2026-05-21-deferred-e2e-blocker-gate.md` | `state: proposed` | Ratificación Chris |

### ADR (en `docs/architecture/luana-platform/`)

| Archivo | Estado |
|---|---|
| `ADR-008-luana-core-ui-shadcn-cli-pattern.md` | `state: proposed` — pending ratify |

---

## 8. Open questions / Backlog estructurado

### Pendiente esta sesión (ANTES de cerrar shell-organism)

- [ ] Q4.b — Elegir subestructura Lucas (v1 features vs v2 ciclo-temporal)
- [ ] Q5 — Ubicación de pagos en recepción
- [ ] Q6 — Ubicación de audit log HIPAA
- [ ] Re-armar mockup `dual-mode-shell.html` con tabs reales de 5 agentes + colores correctos + foto PNG real
- [ ] Reemplazar `navigation-tree.md` con árbol final ratificado
- [ ] `/pm-vitalia` regenera todas las historias de usuario rotas (las pre-paradigm) para que reflejen la nueva estructura

### Pendiente próximas sesiones (post shell-organism)

- [ ] Setup R2 bucket `luana-assets-platform` + upload agents (Chris credenciales)
- [ ] Story formal `vitalia-shell-organism` checkpoint.md + 01-spec.md (paradigm v4)
- [ ] Story `vitalia-tailwind-v4-diag` (PRE-REQUISITE para shell)
- [ ] Story `vitalia-slice-1-marketing-integration` (re-evaluar — quizás absorbida por shell-organism)
- [ ] Ratificación ADR-008 (luana-core-ui shadcn copy-paste pattern)
- [ ] Ratificación promotion proposals (luana-core-ui + deferred-e2e-blocker-gate)
- [ ] Investigación LangGraph multi-agent layout (ver `vitalia/docs/architecture/notes/langgraph-multi-agent-layout.md`)
- [ ] Diseño visual de Lisa (PNG cuadrado + transparente) — ya hecho por Chris, solo confirmar consistencia con set
- [ ] Lisa naming check — confirmar nombre "Lisa" definitivo (no es typo de Valeria)

---

## 9. Glosario de términos cementados en esta sesión

| Término | Significado |
|---|---|
| **Empleado IA** | Cada uno de los 5 agentes-cara visibles en el top-bar como tab. Metáfora de marketing del producto vitalia. |
| **Tab top-level** | Cada uno de los 6 elementos del nav superior: 5 agentes + 1 Configurar. |
| **Modo agéntico** | Layout 50/50 (chat Valeria izquierdo + contenido derecho). Default UX. |
| **Modo web** | Layout alternativo: chat colapsado a rail derecho 64px con FAB, contenido full-width. Para sesiones largas operativas. |
| **Átomo / atomic ownership** | Cada unidad de información tiene un dueño semántico (agente bajo cuya tab se produce/cura). Otros agentes consumen read-only. |
| **Sub-tab** | Sección dentro de una tab top-level (ej. dentro de Lucas: Embudo, Campañas, etc.) |
| **N3 hoja** | Vista dentro de sub-tab accesible vía menú directo. |
| **N3-dyn hoja dinámica** | Vista accesible vía selección de item (deep-link), no aparece en menú (ej. "detalle campaña X"). |
| **Workspace** | Espacio multi-tab interno dentro de una hoja N3-dyn (modelo Loomly), ej. detalle campaña con tabs Brief/Audiencia/Creativos/etc. |
| **Escalera de valor clínica** | Metodología propuesta de 5 niveles (consulta → puntual → multi-sesión → mantenimiento → premium integral) para maximizar CLTV en sector salud/belleza. |
| **`<RequireConnection provider="X">`** | Componente reusable que muestra CTA inline para conectar provider faltante con deep-link a Configurar. |
| **Bowtie funnel** | Modelo embudo 5 stages (Atracción/Calificación/Reserva/Adopción/Expansión) ya implementado en vitalia. Mitad izquierda = pre-revenue (Lucas+Adrián), mitad derecha = post-revenue (Camila). |
| **R2** | Cloudflare R2 — bucket de assets de plataforma (transversales, no per-tenant), recomendado para PNGs de agentes. |
| **Mateo transversal** | Mateo NO tiene tab. Sus PNGs/assets se usan en landing (sí o sí) + futuras features de diseño gráfico. Reservado, no activo en navegación. |

---

## 10. Topología contextual (qué leer para continuar la conversación)

**Si retomás esta conversación en sesión nueva:**

1. Lee este doc completo (`00-session-baseline.md`)
2. Lee `nicolify-feature-inventory.md` solo si necesitás referencia de funcionalidades pre-existentes
3. Lee `vitalia-feature-inventory.md` solo si necesitás snapshot actual vitalia
4. Lee `agentic-navigation-proposal.md` solo para ver primera iteración (será obsoleta una vez cerremos Q5+Q6)
5. Continuar exactamente desde "Q4.b — elegir subestructura Lucas (v1 vs v2)" → Q5 → Q6
6. Tras Q6 cerrada: re-armar mockup + reemplazar `navigation-tree.md` + handoff a `/pm-vitalia` para regenerar historias

**Convención path:** workspace root = `/home/chalreme/Proyectos/luana-vitalia/`. Branch actual = `wip/vitalia`. Story dir = `vitalia/docs/product/stories/vitalia-shell-organism/`.

---

## 11. Subestructuras de agente cementadas (live)

> Sección que va creciendo conforme cerremos cada agente. Cuando estén todos, reemplaza al `navigation-tree.md` actual y es el SSoT del menú.

### 🖤 Lucas (Atraer) — cementado Q4.b

Modelo: **ciclo temporal del marketer** (Lanzar → En vuelo → Recursos → Resultados → Mercado).

```
🖤 Atraer (Lucas)
│
├── 🚀 Lanzar
│     ├── Nueva campaña (wizard adaptivo paga/orgánica)
│     ├── Quick-post (post suelto sin campaña asociada)
│     ├── Borradores
│     └── Pendientes aprobación
│
├── 📡 En vuelo
│     ├── Campañas activas (filtros: tipo/plataforma/responsable)
│     ├── Posts programados próximos 7 días
│     ├── Performance live (KPIs día: impresiones, leads, CPC, ROAS)
│     ├── 📁 Detalle campaña activa [dyn — workspace]
│     │     ├── Estado live
│     │     ├── Creatividades vigentes (rendimiento variante A/B)
│     │     ├── Conjuntos/Audiencias activas
│     │     ├── Ajustes (pausar/ajustar presupuesto/cambiar copy)
│     │     └── Alertas activas
│     └── 📁 Detalle post programado [dyn] (preview + edit + cancel)
│
├── 📚 Recursos
│     ├── Biblioteca creatividades (videos, imágenes, plantillas, reels base)
│     ├── Copy reusable (claims, hashtags, frases ganadoras, A/B variants)
│     ├── Generador IA (Lucas crea variantes desde brief)
│     ├── Importados (read-only de testimonios + casos pre/post de Camila)
│     └── Solicitudes a Mateo (queue diseño gráfico — transversal)
│
├── 📈 Resultados
│     ├── Embudo Bowtie izquierdo (Atracción → Calificación → Reserva — KPIs overview)
│     ├── Comparativa canal (Meta vs Google vs TikTok vs Orgánico vs Referidos)
│     ├── Campañas históricas (terminadas/pausadas indefinidamente)
│     ├── Calendario publicado (vista mensual histórica)
│     ├── 📁 Detalle campaña cerrada [dyn — post-mortem]
│     │     ├── Resultados finales vs objetivo
│     │     ├── Qué funcionó / qué no (learning estructurado)
│     │     ├── Mejor creatividad (winner ad)
│     │     └── Recomendación Lucas para próxima iteración
│     └── 📁 Detalle post publicado [dyn] (engagement final + comments destacados)
│
└── 🌍 Mercado
      ├── Tendencias del rubro (mining IG/TikTok/Google trends salud/belleza)
      ├── Hashtags performing (por geo + especialidad)
      ├── Análisis de competencia (clínicas del barrio/categoría)
      └── Sugerencias Lucas (semillas de campañas inspiradas en trends — feed alimenta "Lanzar")
```

**Quedan fuera de Lucas (cementados en P1-P5):**
- Recomendaciones de Lucas → bell icon shell-level (P2)
- Conexiones publicitarias (Meta Ads, Google Ads, TikTok Ads) → Configurar (P3)
- Testimonios/casos pre-post fuente → Camila (P1) — Lucas solo lee read-only

### 🟣 Valeria (Operar) — cementado Q-valeria-macro + Q-doctores + Q5

Modelo: **espacial 2-sub-tabs** (post benchmark Square/Jane/Cliniko/Pabau 2026 — sin sub-tab Caja ERP). **Dos sub-tabs: Agenda · Pacientes**. Sin perfil doctor, sin notas médicas/prescripción/consentimientos (no es PMS, es marketing+ventas+follow-up CLTV). Captura cobros = inline drawer en slot agenda. Estado cuenta = ficha paciente.

```
🟣 Operar (Valeria)
│
├── 📆 Agenda  ← entrada por default
│     │
│     ├── Vista calendario (día / semana / mes)
│     │     ├── Grilla columna-día × fila-hora (modelo Google Cal / Calendly)
│     │     ├── 4 estados visuales slot: PAGADO ✓ · 30% depósito · SIN PAGO · NO-SHOW
│     │     ├── Iconos origen: 🚶 walk-in · 📞 phone · ✉ proactiva (Adrián)
│     │     ├── Filtros: doctor / especialidad / status pago / origen / riesgo no-show
│     │     └── Búsqueda paciente inline
│     │
│     ├── [Click slot] → Drawer detalle inline (no modal full-screen):
│     │     ├── Header paciente (PHI masked default 🔓 reveal)
│     │     ├── Detalle turno (servicio / doctor / status pago / saldo)
│     │     ├── 💳 Subform "Cobrar saldo" (monto / método / notas / fiscal Capa 2)
│     │     │     · Métodos: efectivo / tarjeta / transferencia / MP / otro
│     │     │     · Fiscal: Boleta / Factura RUC / recibo interno (Nubefact PE)
│     │     ├── Acciones secundarias:
│     │     │     · ✅ Marcar asistió
│     │     │     · ❌ Marcar no-show
│     │     │     · 🔔 Recordar pago pendiente
│     │     │     · 📅 Re-agendar
│     │     │     · ➕ Agregar próxima cita (cuando doctor indique cuándo volver)
│     │     │     · ❌ Cancelar turno
│     │     │     · 🚫 Bloquear slot (Dr. llamó que no viene) — atajo a config Lisa
│     │     ├── Historial cross-agéntico (Adrián propuso → confirmó WA → depósito MP)
│     │     └── CTA "Abrir conversación" cross-link a Inbox (Adrián)
│     │
│     ├── [Botón "Crear cita"] → Dropdown:
│     │     ├── 🚶 Walk-in (presente ahora, slot inmediato)
│     │     └── 📞 Reserva por teléfono (fecha futura)
│     │
│     └── Sub-vistas filtradas (presets sobre la misma grilla):
│           ├── "Hoy" (default al abrir)
│           ├── "Por confirmar mañana" (batch confirmar)
│           ├── "Re-agendar pendientes" (canceladas + no-shows sin re-agendar)
│           └── "No-shows del día"
│
└── 👥 Pacientes
      │
      ├── Directorio (buscar nombre/dni/teléfono/email + filtros segmentos)
      │     └── Segmento "Deudores" (cohort estados cuenta abiertos — reemplaza sub-tab Caja "Estados cuenta")
      │
      ├── 📁 Ficha paciente [dyn — workspace]
      │     ├── Datos básicos (contacto + canal preferido)
      │     ├── Historial citas (asistió/no/canceló + método pago)
      │     ├── Tratamientos (activos + pasados, sesión X de Y)
      │     ├── Estado de cuenta (saldos + anticipos + comprobantes + acción "Cobrar" inline)
      │     └── Etiquetas (alto valor / frecuente / deudor / en seguimiento)
      │
      ├── ➕ Nuevo paciente (form rápido — accesible también desde Crear cita)
      │
      └── Tratamientos activos (cohort: quién falta agendar próxima sesión)
```

**NO existe sub-tab Caja** (cementado Q5 post benchmark Square/Jane/Cliniko/Pabau 2026). Reportes financieros se deciden en Lisa Mi Clínica o como botón TopBar.

**Quedan fuera de Valeria (cementados):**
- Notas médicas / prescripción / consentimientos firmados → no aplica (no es PMS)
- Cierre formal de atención por el doctor → no aplica (no hay perfil doctor)
- Doctores (horarios estándar + vacaciones + servicios que atiende) → 🟢 Lisa Mi Clínica (Q-doctores)
- Setup gateway MercadoPago / Stripe / POS físico / Nubefact PE → ⚙️ Configurar (P3) con `<RequireConnection>` inline en subform Cobrar
- Pedir reseña post-tratamiento → 🟦 Camila
- Recomendaciones de Valeria → bell icon shell-level (P2)
- Tareas operativas / checklist diario → absorbido como sub-vistas en Agenda + bell

### 🟢 Lisa (Mi Clínica) — cementado Q-mi-clinica + Q-servicios-vs-ladder + Q6

Modelo: **espacial estratégico** (semi-estático, no temporal). 4 sub-tabs cubren los activos de marca + gente + venta + cumplimiento. Brand Studio heredado Nicolify adaptado a salud — clínica como **sumatoria de doctores** (personal branding de proveedores = marca de clínica). Vertical electivo (dental/estética/psico/psiquiatría), NO atención primaria.

```
🟢 Mi Clínica (Lisa)
│
├── 🏥 Marca de la clínica   ← brand studio adaptado salud (heredado Nicolify)
│     │
│     ├── Identidad
│     │     ├── Nombre, logo, paleta visual (favicons, isotipo)
│     │     ├── Ubicación + contacto + redes (IG/FB/TikTok/Google Maps)
│     │     ├── Historia + propósito de la clínica
│     │     └── Especialidades que atendemos (chips capability)
│     │
│     ├── Voz y tono (heredado Brand Studio Nicolify, simplificado)
│     │     ├── Personalidad (Jung simplificado: ej. Sanador/Cuidador/Experto)
│     │     ├── Cómo hablamos (ASÍ habla / NO habla)
│     │     └── Frases de marca / claims
│     │
│     └── Landing & presencia pública
│           ├── Mensaje principal (UVP — qué nos hace distintos)
│           ├── Doctores destacados en home (cuáles aparecen)
│           ├── Servicios destacados en home (cuáles aparecen)
│           ├── Reseñas destacadas (read-only de 🟦 Camila)
│           ├── Llamada a la acción primaria (qué cita pedimos primero — usualmente N1 escalera)
│           ├── URL pública + estado dominio (CTA inline ⚙️ Configurar si falta conexión)
│           └── 💡 Mateo (transversal) asiste en diseño visual
│
├── 👨‍⚕️ Doctores  ← CRUD adecuado al sistema (perfil-marca, no ficha técnica)
│     │
│     ├── Directorio doctores (lista con foto + nombre + especialidad + status activo)
│     ├── ➕ Nuevo doctor (alta con datos básicos + credenciales)
│     │
│     └── 📁 Perfil doctor [dyn — workspace]
│           ├── Foto + bio + redes personales (IG/TikTok/LinkedIn)
│           ├── Credenciales (matrícula, especialidades, años exp, idiomas)
│           ├── Servicios que atiende (multi-select del catálogo Servicios)
│           ├── Horarios estándar (lun-dom × hora) + vacaciones + bloqueos
│           ├── Capacidad / consultorio asignado
│           ├── Galería antes/después (opt-in vertical estética)
│           ├── Reseñas y testimonios destacados (read-only de 🟦 Camila)
│           ├── KPI doctor (pacientes activos, NPS, recall rate, % no-shows)
│           └── Apariciones públicas (campañas Lucas, landing destacada)
│
├── 🩺 Servicios   ← UNA sub-tab con toggle dos vistas (mismo dataset, dos lentes)
│     │
│     ├── [Toggle vista]: 📋 Catálogo  |  🪜 Escalera de valor
│     │
│     ├── 📋 Vista Catálogo (default — CRUD operativo)
│     │     ├── Directorio plano (filtros: categoría / doctor / precio / activo)
│     │     ├── ➕ Nuevo tratamiento
│     │     └── 📁 Detalle tratamiento [dyn] — CRUD entidad pura:
│     │           ├── Nombre + descripción + duración estimada
│     │           ├── Tipo: puntual / multi-sesión / membresía
│     │           ├── Precio base + planes de pago (1 pago / N cuotas / suscripción)
│     │           ├── Categoría (Preventiva / Estética / Restaurativa / Salud mental / ...)
│     │           ├── Doctores que lo atienden
│     │           ├── Política reserva (anticipo %, cancelación, no-show)
│     │           ├── Indicaciones generales (high-level — NO notas clínicas)
│     │           └── Related treatments (cross-sell, no jerarquía)
│     │
│     └── 🪜 Vista Escalera de valor (canvas estratégico — modelo de negocio)
│           ├── Canvas 5 columnas:
│           │     · N1 Consulta entry (low friction, tripwire)
│           │     · N2 Tratamiento puntual (single visit)
│           │     · N3 Tratamiento multi-sesión (paquete core)
│           │     · N4 Mantenimiento (suscripción / recall)
│           │     · N5 Premium integral (high-ticket)
│           ├── Cada columna lista LadderSlots actuales del nivel
│           ├── Drag-and-drop: agregar tratamiento del catálogo → slot
│           ├── 📁 Detalle slot [dyn]:
│           │     · rol (entry / tripwire / core / continuidad / premium)
│           │     · treatment_ref → TreatmentEntity (mismo treatment puede aparecer en múltiples slots)
│           │     · bundle_treatments[] (pack de varios)
│           │     · pricing_override ($0 si entry gratuita aunque treatment cuesta $80)
│           │     · cta_copy / story_hook (narrativa de venta)
│           │     · target_segment (buyer persona)
│           ├── Métricas panorámicas (pacientes en cada nivel + tasas transición N1→N2, etc.)
│           ├── Movimientos (lista: "Marina P. subió N2→N3 esta semana")
│           └── Hooks cross-agente:
│                 · 🖤 Lucas (campañas captan N1)
│                 · 🔵 Adrián (closer empuja N1→N2, N2→N3)
│                 · 🟦 Camila (recall mantiene N4, reactiva dormants)
│
└── 🛡️ Compliance HIPAA-lite   ← SUAVE — vertical electivo sin historial médico
      │
      ├── Status semáforo lectura rápida
      │     · encryption at-rest ✅
      │     · RBAC roles activos ✅
      │     · sanitization en traces ✅
      │     · política retención 10y ✅
      │
      ├── Política de privacidad y retención (visible + editable)
      ├── Consentimiento de datos del paciente (al registrarse, NO consentimientos médicos)
      ├── Reportes mensuales/trimestrales (export PDF para inspecciones)
      └── 🔗 Link a "Registro técnico crudo" → ⚙️ Configurar → Avanzado (raw log IT/forensics)
```

**Modelo de datos clave (Servicios):**

```
TreatmentEntity  ← entidad atómica del catálogo
LadderSlot       ← composición estratégica que referencia TreatmentEntity (n:m)
```

**Quedan fuera de Lisa (cementados):**
- Notas clínicas / diagnósticos / prescripción / historial médico → fuera scope (no es PMS)
- Captura cobros → 🟣 Valeria → Agenda → drawer slot
- Reseñas / testimonios fuente (creación, moderación) → 🟦 Camila (Lisa solo consume read-only)
- Campañas / creatividades → 🖤 Lucas
- Conexiones técnicas (Stripe/MP/Nubefact/dominio/etc.) → ⚙️ Configurar
- Raw audit log técnico → ⚙️ Configurar → Avanzado (Lisa Compliance solo dashboard + link)

### 🔵 Adrián (Vender) — cementado Q-vender-macro

Modelo: **espacial 4 sub-tabs**. Closer + AI agent que orquesta el funnel comercial (bowtie izquierdo: Atracción → Calificación → Reserva). REUSE mockups ratificados v1 Batch 2 (inbox) + Batch 3 (pipeline) + backend shipped vitalia. Pipeline NO está shippeado FE, REUSE base nicolify closer-studio.

```
🔵 Vender (Adrián)
│
├── 💬 Inbox  ← conversaciones vivas (REUSE inbox.html ratificado + sales_agent shipped)
│     │
│     ├── ConversationList 320px
│     │     ├── Filtros chips: canal (WA/IG/Email) · estado (Activa/Esperando depósito/NPS pendiente/Cerradas) · alertas (🔴 Adrián pide ayuda · 📎 audio/imagen sin abrir)
│     │     ├── Búsqueda paciente/canal
│     │     └── Lista conversaciones con avatar/nombre/canal/stage/tiempo
│     │
│     ├── 🎛 Segmented control 3-modos (★ paradigma UX clave):
│     │     · 🤖 Adrián decide      (auto, avisa si pide ayuda)
│     │     · 💬 Adrián consulta    (sugiere respuesta, vos aprobás antes enviar)
│     │     · ✍️ Yo escribo          (manual, Adrián en modo escucha)
│     │
│     ├── ConversationThread
│     │     ├── Mensajes user vs Adrián con burbujas + timestamps
│     │     ├── Voice notes con transcripción auto ✨ ("Hola, me interesaba saber precios...")
│     │     ├── Image analysis ("Adrián está analizando esta imagen…")
│     │     ├── Ventana Revertir (4:32) post-send Adrián
│     │     ├── Help-needed banner si agent-failed ("Adrián te pide ayuda" + botón "Tomar yo")
│     │     └── Suggest banner si agent-waiting-approval ("Adrián te sugiere esta respuesta. Edítala")
│     │
│     ├── ContactSidebar 280px
│     │     ├── Header paciente avatar + nombre + last-active
│     │     ├── Contacto (teléfono/email/DNI PHI masked + 🔓 reveal con audit log)
│     │     ├── Stage decisión bowtie (Interesado→Considerando→Reservar→Cerrada — progress bar)
│     │     ├── Oferta vinculada (treatment + precio + depósito)
│     │     ├── Próximo turno · Historial NPS
│     │     ├── "Voz Brand Studio aplicada" chip
│     │     └── CTA "Ver ficha completa" → drilldown 🟣 Pacientes
│     │
│     ├── Composer
│     │     ├── Textarea + adjuntos + grabar voz
│     │     ├── Botón principal cambia per modo (Enviar como Adrián / Aprobar y enviar / Enviar)
│     │     └── Pause Adrián button (handoff manual)
│     │
│     └── Activity stream Adrián collapsible (observabilidad agéntica):
│           · 14:21 — Adrián propuso turno martes 12:00
│           · 14:21 — Adrián verificó disponibilidad agenda (libre)
│           · 14:21 — Adrián consultó precio Blanqueamiento Premium ($24.000)
│           · 14:19 — Adrián detectó stage paciente preguntó precio (2/4)
│           · 14:18 — Adrián clasificó interés alto · vertical odontológica
│
├── 🎯 Embudo  ← toggle vista mismo dataset Lead (patrón Lisa Servicios)
│     │
│     ├── [Toggle vista]: 📋 Pipeline Kanban  |  📑 Lista CRM
│     │
│     ├── 📋 Vista Pipeline Kanban (default — estratégica visual, REUSE pipeline.html Batch 3)
│     │     │
│     │     ├── Header metrics: "27 leads · $324k potencial · funnel 12→6→4→3→2 · conv lead→reserva 16.7%"
│     │     ├── Filtros: Oferta (Blanqueamiento/Implantes/Limpieza/Todas) · Canal · Período
│     │     ├── DnD entre columnas (@dnd-kit/core)
│     │     │
│     │     └── 6 columnas dental ratificadas (per-vertical customizable):
│     │           ├── ⚪ Interesado (lead nuevo, count + $ potencial)
│     │           ├── 🟢 Calificando (Lucas atribuido — viene de campaña)
│     │           ├── 🟣 Considerando (Adrián atribuido — en cierre)
│     │           ├── 🔵 Listo para reservar (link pago activo, "expira en Xh")
│     │           ├── ✅ Reservado con depósito (Adrián ✓ — handoff Valeria)
│     │           └── ⚫ Decidió no (→ handoff Camila re-engagement)
│     │
│     │     Card hover → peek expanded inline:
│     │           · Etapa actual + última actividad
│     │           · Tools usadas (3): consultó agenda · generó link pago · catálogo
│     │           · CTA "Abrir conversación completa" deep-link a Inbox
│     │
│     └── 📑 Vista Lista CRM (operativa CRUD)
│           ├── Tabla searchable: nombre · avatar · canal · última act · stage · oferta · tags · score · doctor matched
│           ├── Filtros + segmentos guardables:
│           │     · "Mis leads" · "Hot >score 80" · "Dormants 7d" · "Sin propuesta enviada" · "Custom..."
│           ├── Bulk actions: bulk re-engagement · asignar a doctor · tag · enviar template Outbound · cambiar stage
│           ├── ➕ Nuevo lead manual (recepción carga llamada/walk-in pre-cita)
│           └── 📁 Lead detalle [dyn — workspace]
│                 ├── Datos lead + origen (campaña Lucas / referido Camila / orgánico)
│                 ├── Historial conversación cross-canal (deep-link a Inbox)
│                 ├── Propuestas enviadas + estado
│                 ├── Próxima acción sugerida (Adrián AI)
│                 ├── Score lead detallado (intención + presupuesto + urgencia)
│                 ├── Time-in-stage + SLA alerts (ej. >48h en Propuesta sin respuesta)
│                 └── Tools registry usadas (audit trace)
│
├── 📣 Outbound  ← broadcasts + re-engagement (REUSE fidelizacion shipped + 5 templates Meta-approved)
│     │
│     ├── Campañas outbound activas (lista con KPI: sent · delivered · read · replied · converted)
│     │
│     ├── ➕ Nueva campaña outbound (wizard 3 pasos):
│     │     1. Segmento (selector):
│     │           · Dormants 30/60/90+ días
│     │           · NPS pendientes
│     │           · Tratamiento por vencer (recall)
│     │           · Stage "Decidió no" (re-engagement Slice 2)
│     │           · Custom (filter builder)
│     │     2. Template (selector + preview):
│     │           · `recordatorio_sesion` (Meta-approved)
│     │           · `re_engagement_ausencia` (Meta-approved)
│     │           · `nps_post_tratamiento` (Meta-approved)
│     │           · `recordatorio_control` (Meta-approved)
│     │           · `invitacion_mantenimiento` (Meta-approved)
│     │           · Custom (review pre-aprobación)
│     │     3. Schedule + compliance gate:
│     │           · Fecha/hora send (single shot o secuencia)
│     │           · ✅ `requires_marketing_opt_in` enforced (auto-filtra leads sin consent)
│     │           · ✅ Quiet hours respect (no 22:00-08:00)
│     │
│     ├── Plantillas registry (Lisa cementa base, Adrián AI genera variantes con voz Brand Studio)
│     │
│     ├── Segmentos guardables (reusables cross-campaña)
│     │
│     └── Historial envíos
│           · Métricas detalladas per campaña
│           · Drill-down por lead → deep-link a Inbox
│           · Tasa opt-out (alerta si >5%)
│
└── 💼 Propuestas y planes  ← opt-in per vertical (dental/estética ON · psico/psiquiatría OFF default)
      │
      │  Activable via `{brand}/config/brand.yaml::vender.propuestas_enabled: true|false`
      │
      ├── Filtros: borradores · enviadas · aceptadas · rechazadas · vencidas (link pago expirado)
      │
      ├── 📁 Propuesta [dyn — workspace]
      │     ├── Tratamiento(s) propuesto(s) (ref TreatmentEntity de 🟢 Lisa)
      │     ├── Bundle (multi-treatment ej. "Sonrisa completa")
      │     ├── Plan de pago (1 pago · N cuotas · tokenized recurring monthly/installments)
      │     │     · REUSE Stripe Connect + MercadoPago shipped vitalia
      │     ├── Términos y condiciones (template per vertical — Lisa cementa)
      │     ├── Firma digital (consent signature modal REUSE shipped)
      │     ├── Estado pagos (cuántas cuotas pagadas + próxima fecha + atraso)
      │     ├── Trazabilidad (enviada → vista → respondida → firmada → primera cuota)
      │     └── Próxima acción (recordar pago / re-enviar firma / escalate Valeria)
      │
      └── Plantillas propuesta (Adrián AI genera variantes — Lisa aprueba templates base)
```

**Stages por vertical (customizables via brand.yaml):**
- **Dental** (default): Interesado · Calificando · Considerando · Listo · Reservado · Decidió no — 6 columnas
- **Estética**: idéntico dental + stage extra "Consulta evaluación gratuita" antes de Calificando
- **Psicología**: Interesado · Primera sesión · Pack/membresía · Decidió no — 4 columnas
- **Psiquiatría**: Interesado · Primera sesión · Receta inicial · Seguimiento · Decidió no — 5 columnas

**Quedan fuera de Adrián (cementados):**
- Atender el día (citas confirmadas + cobro presencial) → 🟣 Valeria → Agenda
- Reservas como entidad (cita confirmada en agenda) → 🟣 Valeria (Adrián la genera, Valeria la opera)
- Creación campañas captación/leads de Meta/Google → 🖤 Lucas (Adrián recibe leads ya capturados)
- Pedido reseña post-tratamiento → 🟦 Camila (Adrián solo lee reseñas como contexto)
- Setup gateway pago / WhatsApp Business API / Instagram OAuth → ⚙️ Configurar (con `<RequireConnection>` inline)
- Doctores / horarios / capacidad → 🟢 Lisa Mi Clínica → Doctores
- Catálogo tratamientos + escalera valor → 🟢 Lisa Mi Clínica → Servicios

### 🟦 Camila (Mantener) — cementado v3 Q-mantener-macro + Q-camila-v3 + Q-camila-agente-ops

Modelo: **espacial 4 sub-tabs con paradigma agéntico 3-modos**. Refit v3 fusiona Escuchar+Curar en UN flujo activo (Voz del paciente) y separa growth (Multiplicar) de churn (Reactivar). Camila es agente IA en background — no UI pasiva. Mismo paradigma Adrián.

**Distinciones clave:**
- 🔵 Adrián Outbound (audience LEADS pre-revenue) ≠ 🟦 Camila Reactivar (audience PACIENTES EXISTENTES post-revenue)
- 🪃 Reactivar (churn defense — dormants/riesgo) ≠ 🤝 Multiplicar (growth — promotores/advocacy)
- 🎤 Voz del paciente UNE input + curaduría + publicación (escuchar sin curar es pasivo)

```
🟦 Mantener (Camila)
│
│  [🤖 Camila decide ▼]  [⚙ Reglas]   ← toggle 3-modos global (extensible por tipo señal)
│
├── 🎤 Voz del paciente  ← captura señales + curaduría + publicación (UN flujo activo)
│     │
│     │  Concepto: la voz entra, se procesa, se convierte en activo o se resuelve.
│     │  Camila AI procesa entrante según reglas con preview + timer + Revertir.
│     │
│     ├── 📥 Entrante (badge contador sin procesar)
│     │     │
│     │     ├── NPS nuevos (últimas respuestas con score + texto + paciente)
│     │     │     · 9-10 promotor → 🤖 Camila: pedir testimonio + review Google + invitar referir +14d
│     │     │     · 7-8 pasivo → 🤖 Camila: schedule recall mantenimiento N4
│     │     │     · 0-6 detractor → 🤖 Camila pide aprobación: abrir concern + draft respuesta empática
│     │     │
│     │     ├── Reseñas externas detectadas (Google · Yelp · Doctoralia · Doctify · FB)
│     │     │     · ⭐⭐⭐⭐⭐ → 🤖 Camila: auto-respond gracias + destacar landing pinned
│     │     │     · 3-4⭐ → 🤖 Camila: respond con plantilla
│     │     │     · <3⭐ → 🤖 Camila pide aprobación: abrir concern + draft respuesta empática
│     │     │
│     │     ├── Menciones redes capturadas (IG · TikTok · FB · Twitter)
│     │     │     · positiva → 🤖 Camila: auto-thank + sugerir repostear con consent
│     │     │     · negativa → 🤖 Camila: escalate + draft respuesta + aprobación
│     │     │
│     │     └── Concerns abiertos (derivados detractores + reseñas <3⭐)
│     │           · Bandeja tickets · asignar a doctor/recepción/dueño · SLA tracking
│     │
│     ├── 🎨 En curaduría (señales siendo procesadas en activos)
│     │     ├── Testimonios pendientes consent firma digital
│     │     ├── Casos pre/post listos para sesión foto profesional
│     │     ├── Reseñas marcadas para destacar (esperando moderación)
│     │     ├── Quotes destacables (LLM extract NPS largos o reseñas extensas)
│     │     └── Concerns asignados sin resolver (SLA tracking + alertas)
│     │
│     ├── 🌟 Activos vivos (publicados/resueltos — galería filtrable)
│     │     ├── Testimonios published (texto + foto + video + star + doctor + tratamiento)
│     │     │     · Placements: 🟢 Lisa landing + perfil doctor + catálogo
│     │     ├── Casos pre/post published (galería filtrable tratamiento/doctor/especialidad)
│     │     │     · Card: foto antes + después + narrativa + resultado + tiempo + consent
│     │     ├── Reseñas destacadas pinned (5⭐ en landing home + perfil doctor)
│     │     ├── Quotes vivos (placements en Lisa)
│     │     └── Concerns resueltos archivo (audit trail compliance HIPAA-lite)
│     │
│     └── 🤖 Camila AI sugiere acciones (mismo paradigma Inbox Adrián):
│           ┌──────────────────────────────────────────────────────┐
│           │ Cada card en Entrante muestra:                       │
│           │  • Acciones default Camila va a ejecutar             │
│           │  • Timer countdown si modo "decide" (4:32 → enviar)  │
│           │  • Botón "Editar acciones" + "Pausar Camila aquí"    │
│           │  • Borrador inline si pide aprobación (modo consulta)│
│           │  • Ventana Revertir 3-5min post-send                 │
│           │  • Help-banner si Camila no sabe ("¿podés vos?")     │
│           └──────────────────────────────────────────────────────┘
│
├── 🪃 Reactivar  ← audience: PACIENTES EN RIESGO (churn defense)
│     │
│     ├── 📋 Listas dinámicas en riesgo:
│     │     ├── 🟡 Sin actividad reciente (≥60d / ≥90d / ≥180d split)
│     │     ├── 🔵 Fin de tratamiento sin recall (terminaron N3, no compraron N4 mantenimiento)
│     │     ├── 🟣 Mantenimiento por vencer (suscriptores N4 caducando ≤30d)
│     │     ├── 📋 Propuesta sin firmar (>7d en stage "Listo para reservar")
│     │     └── 🔴 Detractor NPS pendiente recovery (NPS 0-6 ticket abierto >5d)
│     │
│     │   [Listas se actualizan automáticamente — paciente entra/sale según condición day-to-day]
│     │
│     ├── Campañas reactivación activas (KPI: sent/delivered/read/replied/reactivated)
│     │
│     ├── ➕ Nueva campaña reactivación (wizard 3 pasos, REUSE fidelización shipped):
│     │     1. Lista de reactivación (selector)
│     │     2. Template Meta-approved:
│     │           · `recordatorio_control_doctor`
│     │           · `re_engagement_ausencia`
│     │           · `invitacion_mantenimiento`
│     │     3. Schedule + compliance gate `requires_marketing_opt_in` enforced + quiet hours
│     │
│     └── Métricas reactivación
│           · Tasa win-back (dormants reactivados / total dormants targeteados)
│           · Cost per reactivation
│           · LTV recovered atribuible a Camila
│
├── 🤝 Multiplicar  ← audience: PROMOTORES (growth via existentes)
│     │
│     ├── 🎁 Programa referidos (mudanza desde 🖤 Lucas — P1 atomic ownership)
│     │     ├── Configuración programa (recompensa: descuento próxima cita / sesión gratis / regalo)
│     │     ├── Link único por paciente (compartible WA/IG/email)
│     │     ├── Tracking: OPEN → SHARED → SIGNED_UP → CONVERTED → EXPIRED
│     │     └── Leaderboard top-N pacientes referidores (gamification)
│     │
│     ├── 📋 Listas dinámicas growth:
│     │     ├── 🌟 Promotor NPS sin referir (9-10 que no usó link referido)
│     │     ├── 🎂 Cumpleaños este mes (pretextos warmup)
│     │     └── 🎉 Aniversario cliente (1 año / 2 años de relación con la clínica)
│     │
│     ├── Auto-triggers (cierre del loop con Voz del paciente):
│     │     · NPS promotor (9-10) → invitación referir +14d si no refirió aún
│     │     · Cumpleaños → mensaje warmup con descuento N1 entry
│     │     · Reseña 5⭐ Google → sugerir caso pre/post
│     │
│     └── Métricas referral
│           · Conversion rate referral (signed up → converted)
│           · New patients via referral
│           · Cost per referral (vs cost per lead Lucas — comparativa)
│
└── 📊 Reputación  ← panorama estratégico cross-canal (⚠️ planned)
      │
      ├── Score agregado multi-canal
      │     ├── Semáforo unificado (Google ⭐ + Yelp ⭐ + Doctoralia ⭐ + FB ⭐ → consolidado)
      │     ├── Tendencia 30/90/365d (gráfico evolutivo)
      │     └── Volumen reseñas (nuevas por canal este mes)
      │
      ├── Benchmark competencia
      │     ├── Clínicas comparables (mismo barrio + especialidades)
      │     └── Insights ("Sonrisa Plena está 0.4⭐ encima del promedio")
      │
      ├── Alertas
      │     ├── Score drop >X% en 7d
      │     ├── Reseña <3⭐ recibida → trigger service recovery (Voz del paciente)
      │     ├── Mención negativa viral en redes
      │     └── Sin reviews nuevos >30d (review request automation no funciona)
      │
      └── Reportes exportables (PDF mensual para dueño + auditor compliance)
```

### Paradigma agéntico Camila — taxonomía completa de triggers

| Trigger (evento) | Acción default Camila | Backend |
|---|---|---|
| NPS recibido = 9-10 (promotor) | Auto-pedir review Google + +14d invitar referir | ✅ shipped vitalia/fidelización + cron |
| NPS recibido = 7-8 (pasivo) | Schedule recall mantenimiento N4 | ✅ shipped |
| NPS recibido = 0-6 (detractor) | Abrir concern + draft respuesta + aprobación humana | ✅ shipped (workflow nuevo planned para auto) |
| Reseña externa ≥4⭐ | Auto-respond gracias + destacar landing | ⚠️ planned (GMB API + connections nueva) |
| Reseña externa <3⭐ | Concern abierto + draft respuesta + aprobación | ⚠️ planned |
| Mención red social positiva | Auto-thank + sugerir repostear con consent | ⚠️ planned (social listening) |
| Mención red social negativa | Escalate + draft respuesta + aprobación | ⚠️ planned |
| Paciente dormant ≥60d | Iniciar campaña reactivación `re_engagement_ausencia` | ✅ shipped vitalia/sales_agent reengagement_tool |
| Fin tratamiento detectado | Auto-pedir NPS 24h después | ✅ shipped TreatmentFollowupWorkflow |
| Mantenimiento N4 vence ≤30d | Trigger campaña `invitacion_mantenimiento` | ✅ shipped |
| Promotor NPS sin referir +14d | Auto-invitar referir | ⚠️ planned (workflow compuesto) |
| Cumpleaños paciente | Mensaje warmup con descuento N1 | ⚠️ planned (cron diario) |
| Propuesta sin firmar >7d | Camila prueba ángulo relacional (Adrián ya intentó cierre) | ✅ shipped |
| Imagen clínica subida en testimonio | Sugerir uso galería pre/post + flag sesión foto | ⚠️ planned (upload trigger) |

Cada trigger evalúa compliance gate `requires_marketing_opt_in` ANTES de ejecutar.

### Reglas configurables (vive en ⚙️ Configurar → Avanzado → Reglas Camila)

```
Por trigger NPS:
  · 9-10 → [auto-pedir review ✓] [auto-pedir testimonio ✓] [invitar referir +14d ✓]
  · 7-8  → [recall mantenimiento N4 ✓]
  · 0-6  → [abrir concern ✓] [draft respuesta ✓] [requiere aprobación ON ⚠️]

Por trigger reseña externa:
  · ≥4⭐ → [auto-respond ✓] [destacar landing ✓] [pedir caso pre/post +24h ✓]
  · 3⭐  → [respond plantilla ✓]
  · <3⭐ → [abrir concern ✓] [draft respuesta ✓] [requiere aprobación ON ⚠️]

Por trigger mención red social:
  · positiva → [auto-thank ✓] [sugerir repostear ✓]
  · negativa → [escalate ✓] [requiere aprobación ON ⚠️]

Templates Meta-approved usados (registry técnico)
Compliance gate `requires_marketing_opt_in` ON (no editable abajo)
```

Defaults sensibles por vertical (dental/estética = más outbound · psico/psiquiatría = conservador por sensibilidad emocional).

### Modelo Valeria-céntrico (paciente nunca ve "Camila")

| El dueño dice a Valeria... | Valeria delega a Camila... | Camila ejecuta... |
|---|---|---|
| "¿Cómo están las reseñas Google esta semana?" | Camila genera resumen | "+3 reseñas (2× ⭐⭐⭐⭐⭐ + 1× ⭐⭐⭐⭐). Score 4.6→4.7." |
| "Pedile a Marina un testimonio" | Camila Identifica + envía template | "Listo, le mandé por WA. Plantilla pedir-testimonio Meta-approved." |
| "Activá campaña reactivación dormants 90d" | Camila valida lista + setea campaña | "23 pacientes. Empieza mañana 9:00, template `re_engagement_ausencia`." |
| "Qué pasó con concern Federico?" | Camila trae estado ticket | "Carla M. lo llamó hace 2h. Federico volvió a agendar viernes. Cerrado." |

El paciente recibe mensajes via WhatsApp/IG/email desde la clínica — no ve "Camila" como entidad. Camila es internal-only.

### Hooks cross-agente cementados:

- 🟢 Lisa Mi Clínica → **lee** testimonios + casos pre/post + reseñas destacadas de Camila (read-only)
- 🖤 Lucas Atraer → **lee** testimonios + casos pre/post (creatividades campañas)
- 💡 Mateo (transversal) → **diseña** activos visuales con material Camila
- 🔵 Adrián Vender → **trigger** Camila cuando lead pasa a stage "Decidió no" (handoff re-engagement)
- 🟣 Valeria Operar → **trigger** Camila post-tratamiento (auto-envío NPS)

### Quedan fuera de Camila (cementados):

- Creación campañas captación NUEVOS leads (Meta/Google ads) → 🖤 Lucas
- Closure venta (lead → cita) → 🔵 Adrián
- Atender cita + cobrar → 🟣 Valeria
- Identidad/voz/marca → 🟢 Lisa
- Conexiones técnicas (GMB API · Doctoralia · social listening) → ⚙️ Configurar
- Catálogo tratamientos + escalera valor → 🟢 Lisa
- Reglas Camila configuración explícita → ⚙️ Configurar → Avanzado

### ⚙️ Configurar — cementado Q-configurar-macro

Modelo: **espacial 3 sub-tabs** (versión simplificada post-validación Chris). Filosofía: Configurar es **panel del dueño usado 1-2x/mes**; Valeria hace todo conceptualmente vía comandos; UI explícita queda como **espejo visual** para cambios + flujos OAuth que requieren browser. Single tab del shell SIN cara agéntica (no es empleado IA).

```
⚙️ Configurar
│
├── 🏢 Mi cuenta  ← uso poco frecuente, agrupa info + plan + equipo
│     │
│     ├── Información de la clínica
│     │     ├── Nombre comercial + razón social + RUC/CUIT/RFC (fiscal)
│     │     ├── País + zona horaria + moneda (TenantLocale)
│     │     ├── Dirección física + Google Maps embed
│     │     ├── Email institucional + teléfono central
│     │     ├── Idiomas habilitados (es-LA default)
│     │     └── Multi-clínica (si plan habilita >1 location)
│     │           · Lista sucursales (cada una = clinic_id distinta)
│     │           · ➕ Agregar sucursal
│     │           · Per sucursal: nombre + dirección + horarios + doctores asignados
│     │
│     ├── Plan y facturación de Luana (suscripción del SaaS)
│     │     ├── Plan actual (starter / pro / enterprise — plan_tiers brand.yaml)
│     │     ├── Features activas en el plan (lista visible)
│     │     ├── Próximo cobro + método pago
│     │     ├── Historial facturas Luana (PDF downloadable)
│     │     └── CTA upgrade/downgrade plan
│     │
│     └── Equipo de la clínica (staff que accede al sistema)
│           ├── Lista usuarios staff (max 5-10 rows en clínica típica)
│           ├── ➕ Invitar usuario (email + rol + sucursales asignadas)
│           ├── Roles cementados (RBAC vitalia + HIPAA-lite enforce):
│           │     · Dueño (owner) — full access + billing
│           │     · Admin clínica — todo menos billing
│           │     · Recepción — Valeria full + Adrián read + sin compliance
│           │     · Marketing — Lucas full + Camila full + Lisa read
│           │     · Solo lectura (read-only auditor externo)
│           ├── Permisos custom (override por usuario si plan habilita)
│           ├── Sesiones activas + 2FA enforcement
│           └── 🚫 Revocar acceso
│
├── 🔌 Conexiones  ← HUB DETALLADO estilo nicolify (REUSE pattern)
│     │
│     │  REUSE base: `nicolify/frontend/src/features/connections/`
│     │  Patrón Pabau/Boulevard 2026: "30+ integrations activable from settings in few clicks"
│     │  Backend shipped vitalia: 9 OAuth providers operativos
│     │
│     ├── Vista principal: grid de provider cards con status semáforo
│     │     · ✅ Conectado y saludable (last sync OK)
│     │     · ⚠️ Conectado con warning (rate limit / token expira pronto / sync errors)
│     │     · ❌ Desconectado / nunca conectado / OAuth expirado
│     │     · 🔄 Sincronizando ahora
│     │
│     ├── Categorías visuales (agrupación scroll, no sub-tabs):
│     │
│     │   📣 Marketing y publicidad
│     │     · Meta Ads (Facebook + Instagram + Audience Network)
│     │     · Google Ads
│     │     · TikTok Ads (planned)
│     │     · Google Analytics 4
│     │     · Meta Pixel
│     │     · Google Tag Manager (futuro)
│     │
│     │   💬 Mensajería y atención
│     │     · WhatsApp Business API (config templates registry)
│     │     · Instagram DM (OAuth Meta)
│     │     · Facebook Messenger
│     │     · Email SMTP (Gmail / Outlook / custom IMAP)
│     │     · SMS provider (Twilio / Vonage — planned)
│     │     · Telegram (futuro)
│     │     · ManyChat (legacy nicolify integration — opt-in)
│     │
│     │   💳 Pagos y facturación electrónica
│     │     · MercadoPago (primary LatAm)
│     │     · Stripe Connect
│     │     · Nubefact PE (Boleta/Factura electrónica)
│     │     · Bsale CL (futuro)
│     │     · AFIP AR (futuro — facturación electrónica)
│     │     · POS físico (futuro)
│     │     · Bancos / transferencia (referencias bancarias)
│     │
│     │   🗓 Calendarios externos
│     │     · Google Calendar (sync doctor disponibilidad bidireccional)
│     │     · Outlook / Microsoft 365 (futuro)
│     │     · iCloud Calendar (futuro)
│     │
│     │   🌐 Presencia online (Camila consume reviews/menciones)
│     │     · Google My Business (reviews + listings + posts)
│     │     · Doctoralia (reviews via API / scraper)
│     │     · Yelp / Foursquare (futuro)
│     │     · Doctify / RateMDs (futuro internacional)
│     │
│     │   🔧 Integraciones técnicas avanzadas
│     │     · Webhooks custom (eventos del sistema → tu app externa)
│     │     · Zapier / Make.com (planned plan pro)
│     │     · API REST tokens (BYO integration)
│     │     · Slack notifications (futuro)
│     │
│     ├── 📁 Click provider card → drawer detalle [dyn]
│     │     ├── Header: logo + nombre + status semáforo + CTA primary (Conectar / Reconectar / Configurar)
│     │     ├── Estado salud
│     │     │     · Last sync timestamp + duración
│     │     │     · Errors recientes (lista 5 últimos)
│     │     │     · Rate limit usage (X/Y this hour)
│     │     │     · Quota / billing del provider (si aplica)
│     │     ├── Credenciales / OAuth
│     │     │     · Cuenta conectada (email/business name)
│     │     │     · Fecha conexión + último refresh token
│     │     │     · CTA: Refresh OAuth / Reconectar
│     │     ├── Permisos otorgados
│     │     │     · Lista scopes del OAuth (ej. ads_management, pages_messaging)
│     │     │     · Diff vs scopes requeridos por vitalia (alerta si falta uno)
│     │     ├── Configuración específica del provider
│     │     │     · WhatsApp: phone number ID + templates Meta-approved sync + opt-in default
│     │     │     · Meta Ads: ad accounts seleccionadas + auto-tagging medical vertical
│     │     │     · Stripe: account ID + connect mode + currencies
│     │     │     · Google Cal: calendar ID por doctor + sync direction (one-way/two-way)
│     │     │     · Nubefact: emisor + serie boleta/factura
│     │     │     · etc.
│     │     ├── Actividad reciente (log últimos eventos provider)
│     │     │     · "Webhook recibido: payment.success"
│     │     │     · "Sync error: rate limit exceeded (auto-retry en 5 min)"
│     │     ├── Documentación + soporte
│     │     │     · Link a guía setup oficial
│     │     │     · Link soporte provider (FB Business, Stripe support, etc.)
│     │     └── 🚫 Desconectar (con confirmación + advertencia features que se rompen)
│     │
│     └── 💡 `<RequireConnection provider="X">` deep-links
│           · Cualquier feature en otra tab que necesite conexión faltante apunta acá
│           · Return URL preservada (vuelve a donde estaba después de conectar)
│           · Ejemplos:
│                 - 🟣 Valeria cobra → Stripe/MP falta → CTA inline → Configurar/Conexiones/stripe
│                 - 🖤 Lucas crea campaña Meta → Meta Ads falta → CTA → Configurar/Conexiones/meta-ads
│                 - 🟦 Camila ver reseñas Google → GMB falta → CTA → Configurar/Conexiones/google-my-business
│
└── 🔬 Avanzado  ← cajón cosas raras + poco-frecuentes + dev-mode
      │
      ├── Reglas y políticas
      │     ├── Políticas de reserva
      │     │     · Anticipo % default (30% — overridable per treatment en 🟢 Lisa)
      │     │     · Política cancelación (cuántas horas antes sin penalidad)
      │     │     · Política no-show (cuántos no-shows bloquean a paciente)
      │     │     · Lead time mínimo / máximo para reservar
      │     │     · Slots máximos abiertos por doctor por día
      │     ├── Notificaciones automáticas
      │     │     · Recordatorio cita (24h / 1h antes — toggle por canal)
      │     │     · Confirmación post-reserva
      │     │     · NPS post-tratamiento (delay configurable)
      │     │     · Recall mantenimiento (cada cuánto trigger)
      │     │     · Aniversarios y cumpleaños (auto-trigger Camila)
      │     ├── Templates Meta-approved (registry técnico)
      │     │     · Lista 5 templates shipped + custom registrados
      │     │     · Estado aprobación Meta (approved/pending/rejected)
      │     │     · Versionamiento + historial cambios
      │     │     · 💡 Copy/voz lo cementa 🟢 Lisa → Voz y tono
      │     ├── Stages pipeline customizables (Adrián Embudo override default vertical)
      │     │     · Drag-and-drop stages
      │     │     · Templates por stage (auto-envío al mover lead)
      │     └── Compliance HIPAA-lite
      │           · Compliance level (hipaa_lite default — no editable hacia abajo)
      │           · Retención datos (10 años PHI mínimo regulatorio LatAm)
      │           · Política privacidad URL pública (auto-gen + editable)
      │           · Consentimiento marketing opt-in default
      │           · Canales encriptados only para medical data (toggle)
      │
      │   💡 La mayoría de estas las cambia Valeria conversacionalmente.
      │       UI Avanzado es backup visual + onboarding inicial.
      │
      ├── Registro técnico crudo (raw audit log per Q6 híbrido)
      │     · Tabla filtrable (user / acción / recurso / IP / rango fecha)
      │     · Exportar (CSV / JSON para auditor externo)
      │     · Retención técnica configurable (default 10y HIPAA-lite, no editable abajo)
      │     · Uso típico: 1-2 veces al año (auditor externo, forensics post-incidente)
      │
      ├── LLM keys (BYO — Bring Your Own — opt-in plan pro)
      │     · OpenAI · Anthropic · DeepSeek · Kimi · Google Gemini
      │     · Cost tracking per provider
      │     · Fallback orden
      │
      ├── Feature flags (semi-técnicos del brand.yaml)
      │     · propuestas_enabled (Adrián Propuestas sub-tab)
      │     · multi_site_ui
      │     · insurance_integration
      │     · wellness_deep_coverage
      │     · Otros toggles plan
      │
      ├── API tokens / Webhooks
      │     · Generate API key (integrations custom plan pro)
      │     · Webhooks subscriptions (eventos del sistema)
      │     · Zapier / Make.com integration
      │
      ├── Importar / exportar datos
      │     · Importar pacientes desde CSV / otra plataforma
      │     · Exportar todos los datos (GDPR right to portability)
      │     · Backup manual
      │
      └── Zona peligrosa
            · Resetear datos demo
            · Eliminar cuenta (irreversible — soft delete + retención legal)
            · Cambiar tenant slug (rompe URLs públicas)
```

**REUSE shipping cementado:**
- 🟢 BE conexiones: `vitalia/backend/src/modules/vitalia/connections/` (9 providers OAuth + registry medical-vertical)
- 🟢 BE IAM: `vitalia/backend/src/modules/vitalia/iam/` (RBAC + @require_phi_access decorator)
- 🟢 BE audit log: `vitalia/backend/src/modules/vitalia/compliance/` (HIPAA-lite + dual-filter + pgcrypto)
- 🟢 BE brand.yaml: feature flags + plan_tiers
- 🟢 BE payment: MercadoPago + Stripe Connect + tokenized recurring
- 🔴 FE: Settings UI desde cero — REUSE base `nicolify/frontend/src/features/settings/` + `nicolify/frontend/src/features/connections/` + `core/luana-core-ui/`

**Quedan fuera de Configurar (cementados):**
- Logo · paleta visual · isotipo · favicons → 🟢 Lisa → Marca → Identidad
- Voz y tono · personalidad Jung · frases marca → 🟢 Lisa → Marca → Voz y tono
- Landing strategy · doctores destacados · UVP → 🟢 Lisa → Marca → Landing
- Doctores · horarios · vacaciones · servicios que atiende c/u → 🟢 Lisa → Doctores
- Catálogo tratamientos · escalera valor → 🟢 Lisa → Servicios
- Compliance dashboard panorámico (semáforo lectura rápida) → 🟢 Lisa → Compliance
- Templates COPY/voz → 🟢 Lisa → Voz (Configurar gestiona REGISTRO técnico approve/pending)

---

## 12. Versionamiento

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-21 | Snapshot inicial sesión rediseño shell-organism agéntico. Q1-Q4 cerradas, Q4.b/Q5/Q6 pendientes. 6 docs creados + scripts R2 + assets PNG copiados. Principios P1-P5 cementados. |
| 1.1 | 2026-05-21 | Q4.b cerrada → Lucas cementado v2 ciclo-temporal. Sección 11 nueva "Subestructuras de agente cementadas". Pendientes: Q5, Q6, Q7 (¿aplicar v2 al resto?). |
| 1.2 | 2026-05-21 | Q-valeria-macro + Q-doctores cerradas. Valeria cementado **modelo espacial propio** (Agenda · Pacientes · Caja). Cobro inline en slot agenda (no sub-tab Caja captura). Doctores movidos a Lisa Mi Clínica. Simplificaciones: sin perfil doctor, sin notas médicas/prescripción, foco marketing+ventas+CLTV. Pendientes: Q5 ratificar, Q6 audit log, Q7 patrón cross-agente. |
| 1.3 | 2026-05-21 | Q5 cerrada **post benchmark Square/Jane/Cliniko/Pabau 2026**. Eliminada sub-tab Caja (era reminiscencia ERP). Valeria queda con **2 sub-tabs: Agenda · Pacientes**. Cobro 100% inline drawer slot agenda. Estado cuenta paciente = ficha. Cohort deudores = filtro segmento directorio. Anticipos = bell notification. Reportes financieros TBD (Lisa o TopBar). Pendientes: Q6 audit log, Q7 patrón cross-agente. |
| 1.4 | 2026-05-21 | **Foco reset marketing+ventas+CLTV** (vertical electivo dental/estética/psico/psiquiatría, NO atención primaria). Q-mi-clinica + Q-servicios-vs-ladder + Q6 cerradas. Lisa cementada **4 sub-tabs: Marca · Doctores · Servicios (toggle Catálogo\|Escalera) · Compliance HIPAA-lite suave**. Brand Studio Nicolify heredado adaptado salud (clínica = sumatoria de doctores, personal branding). Modelo datos: TreatmentEntity (catálogo) + LadderSlot (composición estratégica n:m). HIPAA suavizado: compliance dashboard ligero en Lisa + raw log discreto en Configurar. Sin historial médico, sin consentimientos clínicos. Pendientes: Adrián, Camila, Configurar, Q7. |
| 1.5 | 2026-05-21 | **Q-vender-macro cerrada**. Adrián cementado **4 sub-tabs: 💬 Inbox · 🎯 Embudo (toggle 📋 Kanban \| 📑 Lista CRM) · 📣 Outbound · 💼 Propuestas opt-in**. REUSE mockups ratificados v1 Batch 2 (inbox) + Batch 3 (pipeline) + backend shipped: `vitalia/backend/src/modules/vitalia/{inbox,sales_agent,fidelizacion,crm,patients}/` + 5 templates Meta-approved + tools médicas + guardrails (no_diagnosis/no_prescription) + archetype warm_close. Paradigma UX clave: Segmented control 3-modos (Adrián decide/consulta/Yo escribo). 6 stages dental ratificados con atribución agéntica visible Lucas/Adrián. Gap shipping: Pipeline NO existe FE vitalia (REUSE base nicolify closer-studio). Stages customizables per vertical via brand.yaml (dental 6 cols · estética 7 · psico 4 · psiquiatría 5). Pendientes: Camila, Configurar, Q7. |
| 1.6 | 2026-05-21 | **Q-mantener-macro cerrada**. Camila cementado **4 sub-tabs: 🎧 Escucha · 🌟 Pruebas sociales · 🪃 Reactivar · 📊 Reputación**. Distinción cementada Camila Reactivar (audience pacientes existentes) vs Adrián Outbound (audience leads). Referidos mudados de Lucas → Camila per P1 atomic ownership. "Cohorts" renombrado a "Listas de reactivación" (dinámicas, 8 listas vertical electivo). REUSE shipped: NPS + 5 templates Meta-approved + referrals_leaderboard + casos pre/post BE core. Gaps planned: reseñas externas multi-canal, reputación agregada, menciones redes — fuera de scope MVP. Pendientes: Configurar, Q7. |
| 1.7 | 2026-05-21 | **Q-configurar-macro cerrada (versión simplificada post-feedback Chris)**. Configurar cementado **3 sub-tabs: 🏢 Mi cuenta · 🔌 Conexiones (HUB detallado estilo nicolify) · 🔬 Avanzado**. Filosofía: panel del dueño usado 1-2x/mes, Valeria hace todo conceptualmente vía comandos, UI es espejo visual + flujos OAuth. Mi cuenta agrupa info clínica + plan Luana + equipo (clínicas chicas 5-10 staff no merece tab equipo separada). Conexiones detallada con 6 categorías (Marketing/Mensajería/Pagos/Calendarios/Presencia/Técnicas) + drawer per provider (OAuth/health/permissions/config) — REUSE base `nicolify/frontend/src/features/connections/` 12 providers. Avanzado es cajón (reglas + audit log raw + LLM keys + flags + API + import/export + danger zone). Cementado: Configurar NO tiene cara agéntica (única tab del shell sin empleado IA). Quedan fuera de Configurar (cementados): visual identity/voz/landing (todos en Lisa). Pendientes: Q7, mockup, navigation-tree, handoff. |
| 1.8 | 2026-05-21 | **Q-camila-v3 + Q7 + Q-camila-agente-ops cerradas — TODAS las preguntas de diseño cerradas**. Camila refit v3: **4 sub-tabs cementadas 🎤 Voz del paciente (fusión Escuchar+Curar: entrante+curaduría+activos vivos UN flujo) · 🪃 Reactivar (churn defense audience dormants) · 🤝 Multiplicar (growth audience promotores, referidos mudados de Lucas) · 📊 Reputación**. Paradigma agéntico cementado: Camila = agente IA con 3-modos (decide/consulta/manual) extensible del patrón Adrián Inbox. **12 triggers SSoT cementados** (NPS 9-10/7-8/0-6, reseñas ≥4⭐/3-4⭐/<3⭐, menciones ±, dormant 60d, fin tratamiento, mantenimiento por vencer, promotor sin referir +14d, cumpleaños, propuesta sin firmar >7d, imagen testimonio). Cada acción con preview + timer + Revertir 3-5min + audit log + compliance gate enforced. Reglas configurables en Configurar → Avanzado → Reglas Camila con defaults sensibles per vertical. **Q7 cerrada: Opción A — modelo propio per agente según naturaleza del rol** (Lucas único ciclo-temporal puro 5 cols; Lisa/Adrián/Camila espacial 4; Valeria espacial 2; Configurar espacial 3 sin cara agéntica). Coherencia metafórica viene de color+foto+rol per agente, NO uniformidad estructural. Modelo Valeria-céntrico: dueño habla con Valeria, Valeria delega a Camila; paciente nunca ve "Camila" — solo mensajes desde la clínica. **TODO listo para artefactos finales: mockup + navigation-tree + handoff /pm-vitalia.** |
