# Anti-Orphan Integration (guardián CTO — nada llega a `done` como isla) — operational detail (loaded on-demand by /architect, moved from .claude/rules/ 2026-05-30)


**Origen:** sesión 2026-05-28 — Chris, viendo el panorama desde el cockpit, detectó **funcionalidades huérfanas**: código creado que no está realmente conectado a la solución (islas). Causa raíz diagnosticada: no había un rol tipo CTO velando que lo construido **tenga sentido, esté conectado, viva en un lugar real del sistema y no duplique**. Esta rule codifica ese rol como gate desde la idea hasta el `done`.

**Cement-date:** 2026-05-28. **Aplica a:** `/pm-vitalia`, `/architect`, `/dev-team` (builders), `/auditor`. **Complementa:** `anti-duplication.md` (no recrear) + `anti-duplication-refining.md` (prior-art scan) + `capability-protocol.md` (cap como hogar permanente).

## Regla cardinal

Ninguna story alcanza `done` si su salida es una **isla**. Toda funcionalidad construida MUST cumplir las **4 contenciones de conexión** (CONNECT), verificables mecánicamente:

| # | Contención | Significa | Verificable por |
|---|---|---|---|
| **C — Consumed** | Tiene ≥1 consumidor real | Algo la llama/usa: UI que invoca el endpoint, hook que consume la API, agente que registra la tool, otro servicio vía port/event. Cero consumidores + no es entry point → **huérfano**. | grep de usages del símbolo nuevo |
| **O — On the map** | Vive en un hogar declarado | Pertenece a un `capability` (`{brand}/docs/product/capabilities/{module}/{cap}.yaml`) — o, si es puramente técnico, a un módulo en la estructura del map con un consumidor declarado. NO existe funcionalidad sin hogar. | `cap_target` en checkpoint + cap YAML existe |
| **N — Navigable / reachable** | Hay un camino de acceso | Un usuario (ruta + nav/botón/trigger) o un sistema (cron, webhook, event handler, agente) puede LLEGAR a ella. Camino explícito: `entry → … → feature`. | `cap.dev_preview` entry_points + nav/router |
| **N — Notarized (registered)** | Está cableada en el runtime | Registrada donde el runtime la descubre: router (`include_router`), nav tree, DI container, tool registry, event subscriber, Extension SDK EP. Crear el archivo NO basta. | grep del registro |

> Mnemónica: **CONN** — Consumed · On-the-map · Navigable · Notarized. Si una de las 4 falta → la funcionalidad es una isla → NO `done`.

## Gates idea → done (dónde se enforce cada contención)

| Fase | Owner | Gate de conexión |
|---|---|---|
| **idea / refining** | `/pm-vitalia` | Declara `cap_target` + hogar en el map (módulo/funcionalidad). Si es técnico-puro (sin user-facing), declara el **consumidor explícito** ("esto lo consume X"). Sin hogar declarado → no pasa a `refined`. |
| **refined → ready** | `/architect` | **`03-arch.md § Integration design` OBLIGATORIA** (ver abajo). Cada surface nuevo declara: entry point(s), consumer(s), registration point(s), y el **reachability path** verbatim. Si un ticket crea un artefacto sin ticket/deliverable de wiring → el ready package está incompleto, NO cierra `ready`. |
| **developing** | `/dev-team` builders | El builder **CABLEA**, no solo crea: registra router/nav/DI/tool-registry/event en el MISMO ticket. `register_router` (BE) / barrel + nav (FE) / tool registry (agentic) son deliverables, no opcionales. |
| **developed → reviewing** | `/auditor` | **Categoría Connectivity (anti-isla)**: verifica las 4 contenciones CONN sobre el diff. Huérfano (creado sin consumer/registro) → CHANGES_REQUESTED. Duplica un cap existente → FAIL (ver anti-duplication). |
| **reviewing → done** | `/pm-vitalia` | Fase F.3: el cap YAML refleja `dev_preview` real (entry_points + main_component + api_endpoints existen en filesystem). cross-check 3 (scenarios→e2e) verde. |

## `03-arch.md § Integration design` (schema obligatorio architect)

Toda story que crea/modifica un surface MUST incluir esta sección en `03-arch.md`:

```markdown
## Integration design (CONN)

### Reachability path (cómo se LLEGA)
usuario en /agenda → click "Nueva reserva" (CitaNuevaButton, T-3)
  → POST /api/v1/scheduling/appointments (T-1)
  → AppointmentService.create (T-1)
  → fila visible en /agenda (refetch React Query, T-3)

### Consumers (quién la USA)
- POST /api/v1/scheduling/appointments → consumido por useCreateAppointment hook (T-3) + sales_agent tool book_appointment (T-2)
- (si CERO consumers planeados → NO se construye, o se declara explícitamente como infra con consumer futuro fechado)

### Registration points (dónde se CABLEA — deliverables verificables)
- BE: router.include_router(scheduling_router) en {brand}/backend/src/modules/{brand}/scheduling/api/__init__.py (T-1)
- FE: ruta /agenda/nueva en app/ + entry en nav tree (T-3)
- Agentic: tool registry en copilot_agent.py (T-2)

### Home (cap)
- cap_target: scheduling.valeria-agenda · cap_change_type: extend
- dev_preview se actualiza al merge: main_component + api_endpoints + e2e_test
```

Sin `Integration design` con reachability path concreto → `/architect` NO cierra `state: ready`.

## Detección de isla (algoritmo auditor — categoría Connectivity)

```bash
WS=$(git rev-parse --show-toplevel); BRAND={brand}
# 1. Símbolos nuevos del diff (endpoints, components, tools, services públicos)
# 2. Por cada símbolo nuevo S:
grep -rn "\b${S}\b" ${WS}/${BRAND}/{backend,frontend}/src --include="*.py" --include="*.ts" --include="*.tsx" | grep -v "def ${S}\|class ${S}\|const ${S}\|: ${S}\b"
#    cero usages fuera de su propia definición + no es entry point (route/nav/webhook/tool registrada) → ISLA
# 3. Endpoint nuevo: ¿está en un include_router alcanzable desde main.py?
grep -rn "include_router" ${WS}/${BRAND}/backend/src | grep "{module}"
# 4. Component/page nuevo: ¿referenciado en app/ router o nav tree?
# 5. Tool agéntica nueva: ¿en el tool registry del agente?
```

Veredicto: símbolo nuevo público con cero consumers + no registrado como entry point → **CHANGES_REQUESTED (huérfano)**. El builder debe cablearlo o el architect explicar por qué es infra-con-consumer-futuro.

## Anti-patterns prohibidos

- ❌ Story `done` con endpoint que ningún FE/agente/sistema llama (isla BE)
- ❌ Component creado pero no referenciado en ninguna ruta/nav (isla FE)
- ❌ Tool agéntica definida pero no registrada en el tool registry (isla agentic)
- ❌ `03-arch.md` sin `Integration design` / sin reachability path concreto
- ❌ Builder crea el archivo pero NO lo registra (router/nav/DI/registry) en el mismo ticket
- ❌ Funcionalidad sin `cap_target` (sin hogar en el map) llegando a `developing`
- ❌ Auditor APPROVED sin correr la categoría Connectivity
- ❌ Construir un surface que duplica un cap existente (→ ver `anti-duplication.md`, es FAIL distinto pero relacionado: la isla muchas veces ES una duplicación no detectada)
- ❌ Cap sin **caja/zona** del mapa (Agentes/Plataforma/Infraestructura, registro `{brand}/docs/architecture/SYSTEM-MAP.yaml`) — sin hogar de 3 niveles (zona→caja→área) = isla. El "On-the-map" (O de CONN) se concreta como la caja/zona del paradigma: `.claude/rules/paradigm-arquitectura.md` + `docs/architecture/luana-platform/PARADIGM.md`

## Por qué (rationale CTO)

Una funcionalidad huérfana es **valor perdido + deuda + ruido**: ocupa código, confunde el map, y un futuro agente puede creer que "ya existe" y construir encima de algo que nunca se conectó. El costo de un huérfano se paga tres veces (build + mantenimiento + el día que alguien intenta usarlo y no anda). Conectar desde el diseño (no después) es más barato que des-huerfanizar después. Este es el trabajo que un CTO hace sin que se lo pidan: *"¿esto realmente se enchufa a la solución o es una isla linda?"*

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | `/pm-vitalia` refining: exige `cap_target` + hogar antes de `refined` | ⏳ skill update |
| 2 | `/architect` Step: `03-arch.md § Integration design` obligatoria + reachability path | ⏳ skill update (architect SKILL.md) |
| 3 | builders: registro (router/nav/DI/tool) es deliverable del mismo ticket | ✅ parcial (register_router BE) → generalizar FE/agentic |
| 4 | `/auditor` categoría Connectivity (anti-isla) sobre el diff | ⏳ auditor SKILL + sub-auditores |
| 5 | `scripts/validate_code_cap_bidirectional.py` cross-check 3 (cap dev_preview paths existen) | ✅ existe (extender a reachability) |

## Referencias

- `.claude/rules/anti-duplication.md` — no recrear (la isla suele ser duplicación)
- `.claude/rules/anti-duplication-refining.md` — prior-art scan en refining
- `docs/process/capability-protocol.md` — cap = hogar permanente + `dev_preview` (entry points)
- `docs/process/lifecycle.md` — modelo 4-ejes (Release→Story→Capability→Scenario)
- `docs/process/audits/2026-05-28-agentic-machinery-audit.md` § 4 — cap pointers de salida no de entrada
