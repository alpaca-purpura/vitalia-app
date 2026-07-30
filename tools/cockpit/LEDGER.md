# Ledger — P2 · DevHub (fichas DH-NN)

> Registro de decisiones de ESTA célula (I-69). Decisiones de ECOSISTEMA → `tooling/strategy/LEDGER.md` (I-NN).
> Mismo formato/disciplina que el global. Gate: pendiente de extender `validate_ledger` a células.

## Fichas

### DH-01 · Fundación de la célula — DevHub, sistema independiente de gestión del desarrollo — `decidida` · `vig:vigente`

*Cruda (operador):* sistema completamente independiente; visualización y gestión de todo el ciclo de vida del software; ingeniería alta en ramas/repos/versiones; releases próximamente; roles CEO/líder (global) vs desarrollador (restringido a lo asignado); corre de la mano del Kit; "las carnes" del kit se gestionan aquí. Nombre elegido: **DevHub** (AskUserQuestion 2026-07-01).

*Desarrollo:* hereda el código completo del ex-cockpit (`go/` + `ui/`, movido de `products/cockpit` — I-69). Lo construido (board/roadmap/map/drift/CIL/multi-workspace) = el visor maduro; el delta hacia la visión = gestión de ramas/repos/versiones + releases + roles/auth. La lente `(directorio)` es huésped (embrión de P1) hasta su extracción. Rename del binario/CLI `cockpit` → pendiente (breaking para installs; va con la primera release comercial de la célula).

*Extracción del embrión (CK-02, 2026-07-01):* Stage 1 hecha — `lib/directorio/portfolio.ts` salió de este árbol, ahora vive en `products/cockpit/ui/lib/portfolio.ts`; DevHub sigue consumiéndolo (`SistemaProvider`/`AppShell`/`Sidebar`/`EmpresaDependencias`/`SistemaSwitcher`/`SystemOverview`) vía el alias `@cockpit/*` (tsconfig + vitest), sin cambio de build/binario. Resto del huésped (`portfolio.go`/`handlers_negocio.go`, `NegocioView`/`SystemOverview`, la página `negocio`) sigue acá — Stage 2-4 en CK-02.

*Conecta:* I-69 · I-64 (superada; su seam de route-groups = frontera P1/P2) · I-40..I-52 (la historia del visor) · KIT-01 (las carnes se gestionan aquí).

*Siguiente:* sesión de célula — roadmap desde los gaps (ramas/releases/roles) + TBDs del grill.

### DH-02 · Épica Torre de Control — F0: norte firmado + auditoría fría — `decidida` · `vig:vigente`

*Cruda (operador):* DevHub pasa a soportar/monitorear la construcción de TODOS nuestros
desarrollos. Un solo tablero que responde, por sistema en construcción (4 células del monorepo +
repos hermanos prenter/engagements): ¿gate verde o rojo? ¿qué hay en vuelo sin commitear? ¿último
tag/release? ¿actividad del ledger? ¿estado de ramas/PRs? READ-ONLY primero; gestión (escritura)
solo cuando el read-only demuestre cadencia. Fase posterior: arquitectura por sistema consumiendo
`arquitectura.yaml` de célula. Caso motivador real (2026-07-02): sesión cerró OBS-15 mientras otra
reestructuraba cockpit/devhub — gate de fábrica ROJO por un paso ajeno + gate de prenter rojo
aparte, nada visible pal operador. Checkpoint de confirmación del norte expiró sin respuesta
(AFK) — se aplicó la opción recomendada por método de la casa.

*Desarrollo:* auditoría fría (cero build, cero código nuevo) sobre el estado real de DevHub y su
entorno, con 11 hallazgos que reforman el contenido de F1 sin tocar el orden de fases propuesto.
(1) **I-74/CK-08 verificado ejecutado**: Cockpit ya corre como binario propio `directorio`
(puerto 4100); DevHub retiene el binario `cockpit` (colisión de nombre, DH-01 rename sigue
pendiente); contrato de datos DevHub→Cockpit diseñado (Pull API versionada) sin código, sin
consumidor. (2) DevHub hoy expone 27 rutas HTTP reales (`main.go`), 5900 líneas en `go/`; 156
tests verdes al cierre de CK-08 (no re-verificado en esta sesión por regla "cero build" de F0).
(3) **Colisión de nombre real**: `gates.go` ya es el dominio del ciclo SDD de 10 estados
(board de historias, G1-G8) — el gate anti-drift de fábrica (`gen_all.py --check`) es un concepto
DISTINTO; la torre debe decir "gate de fábrica"/"gate del hook", nunca "gate" pelado dentro de
DevHub. (4) **Multi-repo YA EXISTE y fue probado**: `cockpit add <path>` registra workspaces
externos arbitrarios en `~/.cockpit/cockpit.yaml` (única condición: "parecer" workspace SDD, i.e.
tener `docs/product/`); CK-08 lo corrió en modo multi-workspace real con 5 proyectos a la vez.
(5) **Pero ese registro vivo está huérfano**: se genera desde
`chris-corp/harnesses/scripts/gen_cockpit_registry.py` ← `chris-corp/portfolio/registry.yaml` —
SSoT PRE-I-39 (chris-corp = nombre viejo de la EMPRESA); el registro vigente post-I-39 vive en
`prenter/clientes/registry.yaml`, nunca migrado. (6) **Patrón gemelo ya resuelto por P4**: OBS-15
(2026-07-02) cortó el mismo problema para telemetría/arnés en 3 bandas — curado en la EMPRESA
(`prenter/clientes/flota.yaml`) + join en runtime (`~/.prenter/flota/`, nunca en la fábrica) +
fábrica solo contrato/adapter/check/fixture; recomendación para F1: espejar ese corte para el lado
repo/proceso en vez de parchar el huérfano o inventar un tercer mecanismo. (7) **2 formatos de
"ledger" que no se hablan**: `/api/ledger` del board lee `docs/product/ledger.yaml` (YAML, para
sistemas cliente); los ledgers reales de célula (`products/{cockpit,devhub,kit,harness-studio}/LEDGER.md`)
son Markdown con fichas, sin equivalente `.yaml` — F1 tiene que diseñar el contrato de lectura.
(8) No existe `validate_ledger.py` suelto — la validación de ledger vive dentro de `gen_all.py` y
solo cubre el ledger global; los `LEDGER.md` de célula se mantienen a mano, sin gate. (9) Gate de
fábrica confirmado VERDE en esta sesión (`gen_all.py --check`, exit 0, cero efectos secundarios).
(10) Señal real de "en vuelo" observada en el propio repo durante F0: 3 archivos modificados sin
commit, preexistentes a la sesión (`products/devhub/CLAUDE.md`, `ui/CLAUDE.md`,
`ui/tsconfig.tsbuildinfo`) — no tocados (trabajo ajeno). (11) **Reformula el modelo de datos de
F1**: las 4 células comparten UN repo git (rama/tag/gate únicos a nivel raíz) pero
ledger/roadmap/board son por célula — "sistema" ≠ "repo" 1:1; la torre modela dos ejes, REPO ×
CÉLULA/PROYECTO, no uno solo.

*Conecta:* I-69 (fronteras de célula) · I-74/CK-07/CK-08 (estado verificado del split Cockpit↔DevHub)
· OBS-15 (patrón de 3 bandas a espejar en F1) · I-39 (el huérfano chris-corp es su resaca sin
migrar) · DH-01 (rename `cockpit`→otro nombre sigue pendiente, ahora con más urgencia por la
colisión de binarios).

*Siguiente:* F1 — modelo de datos 2-niveles + SSoT del registro (AskUserQuestion: espejar patrón
`flota.yaml` vs. reusar/migrar el huérfano) + contrato de lectura de ledger de célula + SPEC
congelada de la torre read-only en `products/devhub/specs/`.

### DH-03 · Norte v3 de la épica Torre de Control — DevHub = consola de delivery GOBERNADA POR PROCESO — `decidida` · `vig:vigente`

*Cruda (operador):* tres jugadas de debate sobre el norte v1 (torre read-only sola). (1) "DevHub
sigue siendo un sistema para la construcción de software... dependiendo del producto puede que
tengamos un proceso diferente, tenemos que prepararlo para eso." (2) "Actualmente depende de los
arneses del kit dev... tiene que ser multi — el CTO debe ver absolutamente todo, incluso pasos
adicionales del paso a producción; tendría otros skills, otros arneses." (3) "Cockpit, devhub,
harness-studio... tecnologías, arquitectura y probablemente arneses diferentes, pero a las finales
lo que terminamos construyendo son capabilities del sistema." Pidió investigación state-of-the-art
y que lo existente "pueda renderizarse dependiendo de la casuística del proyecto". Luego sumó:
"que sea un instalable, una aplicación de escritorio que permita conectarse con claude code para
trabajar desde allí". Y el diferencial vía conductor.build: "nos basamos en proceso, no solo un
facilitador al DEV — agarramos tickets bien especificados (o realizamos la especificación) y la
entregamos; nuestra pantalla de prompting por detrás se conecta con claude code parametrizándose
sobre el proceso establecido por la empresa... arquitectura as code, diseño técnico as code,
visión de producto todo as code para que el developer solo se asegure de encausar la entrega y
aumentar los capabilities."

*Desarrollo:* dos investigaciones (condensadas en `epicas/torre-de-control/INVESTIGACION.md`).
**(A) State of the art** (Jira · Azure DevOps · Backstage · CDEvents/DevLake · ASL/XState/
Temporal · Score/Humanitec/Kratix · OMG Essence/SEMAT · OSLC-CM): receta de 5 ingredientes sin
contraejemplo — categorías semánticas fijas ~5 estilo Azure (la consola ata comportamiento a
categoría, jamás a nombre de estado; nativo se preserva al lado, patrón DevLake
`original_status`) · descriptor+intérprete con hooks por nombre (dueños/arneses = bindings, no
hardcode) · gates = checklists como dato (Essence: el estándar OMG cuya premisa es exactamente
esto; falló por no tener consola) · catálogo de capabilities con sobre de entidad (Backstage) ·
verbos normalizados en transiciones (CDEvents). El embrión del ingrediente 1 YA existe en el
código propio (`TERMINAL_STATES`/`IN_PROGRESS_STATES` en `release-resolver.ts`). **(B) Claude
Code**: vía oficial = Agent SDK (bundlea runtime propio; streaming, `canUseTool`, resume,
multi-sesión N repos); headless CLI insuficiente para aprobaciones en vivo; JSONL de sesiones =
formato interno, prohibido parsear; ToS 2026: branding propio, API key, sin pass-through
claude.ai; stack: sidecar Node junto al binario Go = ruta mínima. **(C) Conductor verificado**:
app Mac de sesiones paralelas CC/Codex/Cursor en workspaces aislados — capa de orquestación
SOLA, sin proceso ni as-code.

*Decisión (norte v3, firmado por AskUserQuestion):* **DevHub = consola de delivery gobernada por
proceso — 3 capas: (1) proceso-como-dato (descriptor: estados·transiciones·gates·dueños/arneses
sobre categorías semánticas fijas), (2) contexto as-code (capabilities + arquitectura + diseño +
visión), (3) orquestación de sesiones Claude Code — donde la 1 parametriza a la 3 y la 2 la
alimenta.** Diferencial: Conductor orquesta sesiones; DevHub orquesta ENTREGA (ticket
especificado → sesión parametrizada por el proceso de la empresa + as-code inyectado → gates →
capability; el developer encausa). El ciclo SDD de 10 estados pasa de hardcode a primera
instancia del descriptor. Torre de control = primera vista; read-only = primer entregable.
Decisiones satélite firmadas: **descriptor de proceso = contrato de ECOSISTEMA** (ficha I-NN al
diseñarlo en F4; kit lo shipea — superficie `process/` del plugin —, DevHub lo renderiza; espejo
de I-72 Kit=MOTOR·consolas por producto) · **desktop instalable ENTRA a la épica como F5**
(sidecar Agent SDK, embrión del instalable). Fases v3: F1 registro+SPEC torre · F2 torre MVP ·
F3 arquitectura por sistema (`meta.clase` — I-75, el Atlas murió durante esta misma sesión) ·
F4 descriptor · F5 cockpit de delivery · F6 verbos+cierre. Fronteras actualizadas: P4 ahora se
llama Harness Studio (OBS-17); costura DevHub↔Harness Studio permitida SOLO como eventos de delivery
normalizados publicados por contrato; branding/auth CC según ToS.

*Fuentes (§1.1):* Azure DevOps state categories + DevLake `original_status` (kernel semántico
probado en batalla) · ASL/XState (topología como dato, hooks por nombre) · Essence/SEMAT (kernel
método-agnóstico + checklists; su fracaso de adopción = advertencia: el diseño sin consola no
vende — nosotros tenemos la consola) · Backstage (sobre de entidad, catálogo heterogéneo) ·
CDEvents (verbos normalizados) · Conductor (el hueco de mercado: capa 3 sin capas 1-2).

*Conecta:* DH-02 (la auditoría que ancló el debate) · I-72 (Kit=MOTOR — el descriptor lo shipea
el kit) · I-73/I-75 (arquitectura-como-dato, `meta.clase`, muerte del Atlas) · I-74 (frontera
negocio→Cockpit intacta) · KIT-NN futuro (superficie `process/` del plugin pasa de prosa a dato)
· PROCESS-AS-DATA.md (mismo patrón una capa arriba — precedente de la casa).

*Siguiente:* F1 — registro de sistemas + modelo 2 ejes + contrato lectura ledger de célula +
SPEC congelada de la torre (nombrando estados/veredictos compatibles con las categorías del
ingrediente 1, para no bloquear F4).

### DH-04 · Épica Torre de Control — F1: 4 decisiones + SPEC congelada de la torre read-only — `decidida` · `vig:vigente`

*Cruda (operador):* checkpoint de las 4 decisiones (AskUserQuestion) expiró sin respuesta (AFK)
→ método de la casa: recomendadas aplicadas y registradas.

*Desarrollo:* las 4 decisiones de F1, cada una validada contra evidencia real antes de proponerse.
**(D1) Modelo 2 ejes firmado**: REPO (rama·en-vuelo·último-tag·gate-de-fábrica, un veredicto por
repo) × PROYECTO (ledger·board, N por repo, descubiertos por convención — `products/*/LEDGER.md`
→ célula; `docs/product/` → sdd). Validación contra los 3 casos reales: prenter-harness = 1 repo
× 4 células ✓; luana-vitalia = WORKTREE de luana-platform (hooksPath apunta al `.git` de
luana-platform) → los hechos git se computan EN el path del workspace, no en un root asumido ✓;
prenter = gate propio (`harnesses/scripts/check.py`) pero SIN tags ni LEDGER.md raíz → eje
PROYECTO 100% nullable con empty-state honesto ✓ (su `marketing/ledger.yaml` es ledger COMERCIAL
de deals — otro dominio, la torre no lo lee). **(D2) SSoT del registro = espejo 3 bandas de
OBS-15** (leído `gen_flota.py` real antes de proponer): CURADO nuevo en la EMPRESA
(`prenter/sistemas/sistemas.yaml` — slugs/refs, jamás rutas, I-39; reemplaza la prosa de
`SISTEMAS.md` que aún apunta al chris-corp huérfano) + RUNTIME (adapter
`products/devhub/scripts/gen_registro.py` emite `~/.cockpit/cockpit.yaml` conforme al wire
format ACTUAL — el binario no cambia para leerlo; rutas locales en
`~/.config/prenter/devhub.yaml`, espejo de `harness-studio.yaml`) + FÁBRICA solo
contrato/check/fixture (el adapter importa el mismo `validate()` del check, patrón SC-30).
Huérfano chris-corp queda obsoleto de facto — retiro NO va de rebote (ficha aparte si amerita).
**(D3) Ledger de célula = espejo máquina generado**, no parser Markdown en Go: `gen_ledger.py`
(que YA parsea el formato del LEDGER global) se extiende para emitir
`products/<célula>/ledger.yaml` (mismas llaves + `log:` aditivo con fechas); UN parser del
formato en la fábrica, DevHub reusa su reader YAML existente, y los ledgers de célula ganan gate
anti-drift como consecuencia arquitectónica (mata hallazgo F0 §8). Toca `gen_ledger.py`
(fábrica): se implementa en F2; si se eleva a governance de ecosistema → I-NN entonces.
**(D4) Nombre del veredicto anti-drift**: UI = «gate de fábrica» · API = `gate_fabrica`; nunca
«gate» pelado (G1-G8 del board). Veredictos por columna = categorías semánticas FIJAS + dato
nativo al lado (patrón DevLake `original_status`; nombres inmutables desde v1, regla Azure) —
compatible con el principio 1 del norte: F4 los mapea como statusCategories sin romperlos.
Con las 4 firmadas: **SPEC congelada** en `specs/torre-read-only.md` (RN-01..RN-19: contrato de
cada columna, refresh/staleness con `medido_en` visible, `no-medido` ≠ `rojo`, principio
omnigent — cada pixel objeto operable, veredictos accionables sin gráficas; fuera de alcance:
escritura, fetch remoto, F3/F4, umbrales). Carpeta permanente `specs/` creada (README con la
regla Rust).

*Conecta:* DH-02 (hallazgos §5-§8, §11 que estas decisiones resuelven) · DH-03 (norte v3,
principio 1) · OBS-15 (patrón 3 bandas espejado) · I-39 (curado en la EMPRESA, refs no rutas) ·
I-75 (F3 colgará su renderizador del eje PROYECTO — esta SPEC no lo contradice).

*Siguiente:* F2 — torre MVP read-only implementando la SPEC (adapter+schema+fixture del
registro, extensión `gen_ledger.py`, `GET /api/torre`, vista tabla).

### DH-05 · Épica Torre de Control — F2 ejecutada: torre MVP read-only VIVA — `decidida` · `vig:vigente`

*Cruda (operador):* sesión F2 lanzada con el NEXT-PROMPT de F1: implementar la SPEC congelada
(`specs/torre-read-only.md`, RN-01..RN-19) sin retocar diseño. Cero forks nuevos — la SPEC cubrió
todo; no hizo falta AskUserQuestion.

*Desarrollo:* las 7 piezas de la SPEC, cada una verificada sola y luego en vivo. **(1) Banda
FÁBRICA del registro** (RN-04..RN-07): contrato `scripts/sistemas-registro.schema.yaml` + fixture
ficticio (`testdata/sistemas-fixture.yaml`: fábrica + EMPRESA + engagement Vértice de la
persona-muestra) + `check_registro.py` (fixture SIEMPRE, curado real si existe — espejo RN-23) en
el pipeline de `gen_all.py`, + adapter `gen_registro.py` (curado × `~/.config/prenter/devhub.yaml`
→ `~/.cockpit/cockpit.yaml` wire format actual; importa el MISMO `validate()` — SC-30; respaldo
`.bak` del registro anterior; sistema sin workspace se emite igual con `active:false` — RN-17).
El registro vivo huérfano (chris-corp, pre-I-39) quedó REEMPLAZADO como fuente; retiro del script
huérfano sigue aparte (RN-08). **(2) Aditivos del wire** (RN-06): `nombre` + `gate_check` flat en
`registryProject`; `TestRegistryWireFormatRoundTrip` extendido y verde. **(3) `gen_ledger.py`
extendido** (RN-09/RN-10): emite `products/<célula>/ledger.yaml` (shape RN-10: fichas + `log:` con
fechas) para las 4 células; en `GENERATED` de repo-map → gate anti-drift los cubre; ficha mal
formada = exit 1 = gate rojo (las células ganan gate — muere el hallazgo F0 §8). **(4) Colectores
eje REPO** (`torre.go`): rama/upstream/ahead-behind · en-vuelo porcelain (XY intacto, el espacio
de X importa) · último tag + commits_desde — todo `git -C <workspace>` (worktree-aware RN-01, se
reporta `repo_root`), cache 5s; `gate_fabrica` = `sh -c gate_check` cwd=workspace timeout 3min,
medido al BOOT + `?medir=gate_fabrica` con TTL 10min, jamás loop (RN-16); timeout/no-ejecutable →
`no-medido` ≠ `rojo` (RN-13). **(5) Colectores eje PROYECTO** (RN-03/RN-11): células por
`products/*/LEDGER.md` + contrato ledger (ultima_ficha·ultima_fecha·total_fichas); sdd por la
convención de `sistemasIn`; board = stories por estado + release en curso. **(6) `GET /api/torre`**
(RN-15/RN-17): shape exacto; fila sin workspace NO desaparece (todo `no-medido` con motivo).
**(7) Vista `/torre`** (RN-18/19): tabla sistemas × columnas REPO, fila expandible al eje
PROYECTO, cada celda click → objeto del dominio (salida del check, archivos XY, ficha, detalle
ahead/behind) + acción sugerida; staleness visible («medido hace N min»); categorías con estilo
fijo, `no-medido` punteado ≠ rojo; terminología «gate de fábrica» en toda la superficie.
**Verificación en vivo** (browser + API): 3 sistemas (fábrica con 4 células con-ledger + prenter +
vertice-crm no-medido); demo definición-de-hecho: archivo ensuciado apareció en `en_vuelo` (`??`)
y desapareció al borrarlo (cache 5s). **La torre cazó un drift REAL en su primer boot**: gate de
fábrica ROJO transitorio porque `harness-graph.data.js` quedó stale tras editar `gen_all.py` en
esta misma sesión — el caso motivador de la épica, reproducido en vivo y auto-regenerado.

*Hallazgo para la EMPRESA:* `prenter/harnesses/scripts/check.py` imprime `✗ 1 error(es)` pero
retorna **exit 0** — la torre lo categoriza `verde` (por exit code, honesto) con el error visible
en el nativo. El "gate rojo de prenter" que bloqueó F1 era el hook, no el exit del check. Fix =
repo prenter (no va de rebote desde aquí); mientras tanto el curado real sigue pendiente y la
torre corre contra el fixture (RN-07).

*Conecta:* DH-04 (la SPEC implementada tal cual — cero ediciones) · DH-02 §5/§8/§11 (huérfano
reemplazado · células con gate · modelo 2 ejes en producción) · OBS-15 (el corte 3 bandas espejado
funcionó — segundo uso del patrón) · I-39 (curado en la EMPRESA; fixture sin data de cliente) ·
DH-01 (el binario sigue llamándose `cockpit`; el rename ganó otra superficie pendiente).

*Siguiente:* F3 — arquitectura por sistema consumiendo `arquitectura.yaml` de célula vía
`meta.clase` (I-75), colgada del eje PROYECTO de la torre (la SPEC lo dejó previsto en §7).

### DH-06 · Épica Torre de Control — F3: lente ARQUITECTURA en el eje PROYECTO (render por clase, I-75) — `decidida` · `vig:vigente`

*Cruda (operador):* checkpoint de las 3 decisiones de F3 (AskUserQuestion) expiró sin respuesta
(AFK) → método de la casa: recomendadas aplicadas y registradas.

*Desarrollo:* las 3 decisiones, cada una anclada a evidencia verificada en sesión. **(D5) DevHub
gana su `arquitectura.yaml` — sí, con gate**: nace `products/devhub/arquitectura.yaml` (curado a
eventos de decisión, mismo formato CK-07, `meta.clase: modelo` explícito = dogfood del
discriminador) + check genérico `tooling/scripts/check_arquitectura_celula.py` en `gen_all.py` —
descubre `products/*/arquitectura.yaml` por convención y valida fichas/joins/enums/rutas +
`meta.clase ∈ enums.clase`; **check-only, cero emisión**: la torre ES el renderizador de DevHub
(I-75), emitir data.js al shell de P4 sería resucitar el Atlas. Cockpit queda doble-cubierto
(su gen valida+emite; este check valida) — mismas reglas espejadas. Patrón DH-04/RN-12: fábrica
al servicio de la célula; elevarlo a governance de ecosistema = ficha I-NN del operador.
**(D6) Render v1 = tabla por planos** (no grafo): componentes agrupados por las bandas del
modelo, click en componente → propósito·fichas·ruta·relaciones (hereda RN-18 omnigent); grafo =
v2. **(D7) Lectura cross-célula = filesystem directo**: el YAML gated ES el contrato de datos
(schema L0 + gate de fábrica, cero imports — frontera #3 del norte se cumple; mismo patrón que
`ledger.yaml`/RN-09); CK-08 Pull API queda como precedente para cross-BINARIO en runtime, no
aplica a artefactos curados de un workspace ya monitoreado. Con las 3 firmadas: **SPEC congelada**
`specs/torre-arquitectura.md` (RN-20..RN-26): fuente solo `tipo: celula` (sdd → v2) · `meta.clase`
discriminador con default `modelo` (el CURADO es arquitectura-como-dato por naturaleza, I-73 —
distinto del default `arnes` del descriptor EMITIDO) · veredicto `con-arquitectura ·
sin-arquitectura · no-medido` con el modelo inline como nativo (campo ADITIVO en `proyectos[]`,
RN-15 intacto) · clase desconocida → render degradado, la fila jamás rompe. Implementación:
colector `torreArquitectura` en `torre.go` (cache 5s vía `torreFacts`) + celda/detalle en
`TorreView.tsx` (render por clase) + tests go.

*Conecta:* DH-05 (la torre donde cuelga) · DH-04/RN-12 (patrón fábrica-al-servicio-de-célula,
segundo uso) · I-73 (arquitectura-como-dato) · I-75 (muerte del Atlas — cada producto su
renderizador; `meta.clase` entró al L0 para esta fase) · CK-07 (el formato espejado) · CK-08
(el precedente que D7 decidió NO usar aquí).

*Siguiente:* F4 — descriptor de proceso (ficha ECOSISTEMA I-NN: kit shipea, DevHub renderiza).

### DH-07 · Épica Torre de Control — F4: el ciclo SDD deja de ser hardcode — descriptor de proceso vivo (motor + vista, I-77) — `decidida` · `vig:vigente`

*Cruda (operador):* checkpoint de las 3 decisiones de F4 (AskUserQuestion) expiró sin respuesta
(AFK) → método de la casa: recomendadas aplicadas y registradas (D8-D10).

*Desarrollo:* la ficha grande del norte v3 ejecutada — el contrato es de ECOSISTEMA (`I-77`:
kit SHIPEA · DevHub RENDERIZA · schema L0); esta ficha registra el lado CÉLULA. **(D8) Alcance
v1 = topología completa + bindings**: estados `{id nativo, categoria}` + transiciones
`{ejecutor, requiere_razon}` + gates-checklist + dueños como bindings `{rol, arnes, nota}` +
parámetros — mata LOS DOS hardcodes de `gates.go` (`operatorAllowed` y `stateOwners`); verbos =
campo reservado (F6). **(D9) Instancia 1 = kit SSoT + espejo gated**:
`products/kit/core-harness/process/sdd-default.yaml` (la superficie `process/` pasa de prosa a
dato) → `gen_proceso_descriptor.py` valida contra el L0 y emite
`go/process/sdd-default.yaml` (cabecera GENERADO, en `repo-map::generated` — drift = gate
rojo); el binario lo embebe (`go:embed`, fail-fast al boot). **(D10) Render F4 = motor + vista
nueva, board intacto**: `gates.go` DERIVA sus tablas del descriptor (firmas intactas —
`proceso.go` parsea y deriva; terminalidad SIEMPRE por categoría, jamás por nombre) + `GET
/api/proceso` + vista `/proceso` (nav propio) que rinde TODO desde el dato: cero literal de
estado en el componente. Las 8 definiciones duplicadas de la UI del board migran en F5/F6.
SPEC congelada `specs/proceso-descriptor.md` (RN-27..RN-34). **Round-trip probado**: suite Go
completa verde SIN tocar un test viejo + `TestProcesoRoundTripLegacy` congela el hardcode
pre-F4 como expectativa (si el kit cambia su instancia, el test avisa que el comportamiento
observable cambió) + `TestProcesoDescriptorAlterno` prueba "otra empresa, otro descriptor,
cero cambio de motor" con estados inventados (`triage→build→staging→prod`). Verificado en
browser (:4777): vista viva con 10 estados (categoría + nativo al lado), transiciones por
ejecutor con ⚡razón≥10, 3 gates con checklist, drill-down de `done` → terminal-por-categoría +
binding `/pm-{sistema} · pm (Fase F MERGE)`.

*Conecta:* I-77 (el contrato de ecosistema — el lado kit/schema vive allá) · DH-03 (el norte
que pre-firmó esto) · DH-04/D4 (categorías fijas + nativo — el embrión) · DH-06/D7 (el patrón
copia-propia + gate que el espejo reusa) · I-72 (el espejo motor/consola) · KIT-08 (CHANGELOG
del kit: la instancia viaja con el plugin).

*Siguiente:* F5 — cockpit de delivery (pantalla de prompting + sesiones CC parametrizadas por
ESTE descriptor + contexto as-code; sidecar Agent SDK, embrión del instalable).

### DH-08 · Épica Torre de Control — F5: cockpit de delivery — el descriptor parametriza sesiones de agente (sidecar Agent SDK, embrión del instalable) — `decidida` · `vig:vigente`

*Cruda (operador):* AskUserQuestion de los 4 forks de F5 respondida — recomendadas confirmadas
(D11-D14).

*Desarrollo:* las 3 capas del norte v3 conectadas — la capa 1 (descriptor, F4) PARAMETRIZA la
capa 3 (sesiones de agente) con la capa 2 (as-code) inyectada. **(D11) Sidecar supervisado por
el binario**: `products/devhub/sidecar/` (TS, `@anthropic-ai/claude-agent-sdk` 0.1.77,
`node:http` puro, branding propio `devhub-sidecar`); el binario Go lo spawnea al boot
(handshake `SIDECAR_PORT=` por stdout, muerte ligada por stdin-pipe — cero huérfanos,
portable), auto-detección `{exeDir}/[../]sidecar` + flag `-sidecar`; sin Node/sidecar → 503
honesto (`disponible:false` + motivo) y el resto de la consola vive. UN comando
(`cockpit start`) sirve UI+API+sesiones = embrión del instalable (DH-03). **(D12) Primera
sesión parametrizada = ESPECIFICACIÓN** (texto, barato, minutos); BUILD con worktree = fase
posterior. **(D13) Vista nueva `/delivery`**, board intacto (las 8 defs duplicadas NO migraron
— D10 sigue vigente, F6). **(D14) As-code v1 = checkpoint de la story + arquitectura.yaml +
VISION.md de la célula**, descubiertos por el MISMO glob que el gate D7 (`{sistemaRoot}[/*]
/arquitectura.yaml`), selector de contexto en la pantalla; capabilities NO entra (principio 4
sin sobre de entidad definido — sería inventar formato sin ficha). La plantilla
(`GET /api/delivery/plantilla`, Go-nativo, funciona AUN sin sidecar) deriva el tramo SOLO del
descriptor: `siguienteTramoRol` (primera transición de rol alcanzable, profundidad ≤2 — cubre
el estado inicial) + dueño binding del destino + gates del momento con checklist verbatim;
cero literales de estado; probado también contra el descriptor alterno (otra empresa, otro
proceso, cero cambio de motor). Workspace aislado por sesión
(`~/.prenter/devhub/sesiones/<id>/`: PROMPT.md verbatim + contexto/ COPIAS + salida/ +
eventos.jsonl); tools acotados (Read/Write/Edit/Glob/Grep, sin Bash/Web, maxTurns 25, sin
settingSources); **RN-31 intacto**: la sesión NO transiciona estados — el humano revisa
salida/ y aplica. Auth: contrato de producto = API key (frontera #6/ToS 2026 — jamás
pass-through de login claude.ai); en el control plane del operador el runtime resuelve la
credencial local (precedente I-76/P4, operador-only). **El contrato del sidecar es
intra-célula (Go↔Node loopback de P2) → NO pide ficha I-NN.** SPEC congelada
`specs/delivery-cockpit.md` (RN-35..RN-44). Tests: 9 casos Go nuevos (tramo ×2 descriptores ·
gates del tramo · contextos as-code · plantilla · no-lanzable por categoría · errores · proxy
honesto · validación de POST) — suite completa verde sin tocar tests viejos; UI typecheck +
156 vitest verdes. **Dogfood end-to-end verificado en browser (:4777)**: story real
`rename-binario-devhub` (la deuda DH-01) creada en el board de products → `/delivery` precargó
el prompt desde el descriptor (arnés `/architect` binding, tramo `refining→refined`), el
operador cambió el contexto cockpit→devhub (la plantilla se re-derivó sola), lanzó → sesión
`s-20260703195018-lhnk` con eventos en vivo (init opus-4-5 · Glob · Read×3 · Write) →
`terminada · success · 7 turnos · 59s` → spec refinada de 131 líneas en
`salida/spec-rename-binario-devhub.md`, story intacta en `idea`.

*Conecta:* DH-03 (norte v3: las 3 capas + desktop DENTRO de la épica) · DH-07/I-77 (el
descriptor que parametriza) · DH-06/D7 (el glob de as-code reusado) · I-76 (precedente P4:
patrón conductor + credencial local operador-only) · DH-01 (la story dogfood ES esa deuda — y
el sidecar le suma superficie al rename pendiente).

*Siguiente:* F6 — veredictos y verbos (CDEvents, campo `verbo` reservado) + migrar las 8 defs
del board a `/api/proceso` + cierre de épica (promover specs, BORRAR la carpeta temporal,
ficha de cierre).

### DH-09 · Épica Torre de Control — F6: verbos CDEvents + board gobernado por el descriptor + CIERRE DE ÉPICA — `decidida` · `vig:vigente`

*Cruda (operador):* checkpoint de los 3 forks de F6 expiró sin respuesta (60s, AFK) →
recomendadas aplicadas (mecánica de la casa): **(D15)** vocabulario v1 = solo verbos como
DATO (sin log/endpoint de eventos persistente) · **(D16)** migración de las defs del board =
COMPLETA · **(D17)** botón «lanzar sesión» desde el story-drawer ENTRA (cierra el fork que
D13 dejó).

*Desarrollo — F6:* el principio 5 del norte hecho dato y la muerte del último hardcode del
ciclo en la UI. SPEC congelada `specs/proceso-verbos-board.md` (RN-45..RN-54). **Verbos
(D15)**: `transicion.verbo` pasa de RESERVADO a INTERPRETADO en el contrato L0 (v2, aditivo —
formato `<sujeto>.<predicado>` validado por el gen; nombra el EVENTO, no la transición → NO
único: `story.parked` ocurre desde idea Y refining); la instancia del kit (v2, entry en su
CHANGELOG/KIT-08) nombra las 13: `spec.started · story.refined · story.queued ·
build.started · build.finished · review.started · story.merged · story.parked ·
story.dropped · story.backlogged · story.reactivated` (sujetos {story,spec,build,review},
predicados CDEvents). El verbo viaja como DATO (RN-47): `/api/proceso`, respuesta de
`POST /api/transition` (`{"verbo":"spec.started"}` verificado por curl) y
`tramo.verbo` en la plantilla de delivery; el log/timeline persistente = ficha posterior (ES
la costura publicada con P4 — frontera #1). Aditivos del contrato para que las defs tengan
fuente (RN-48): `transicion.nombre` (etiqueta humana de la acción) + `estado.wip` (límite
WIP). Motor: `handleTransition` genérico — `requiere_razon` escribe `{target}_reason`, ya no
conoce parked/dropped por nombre (RN-49, byte-igual para sdd-default). **Migración completa
(D16)**: nace `ProcesoProvider` (un fetch a `/api/proceso`) + helpers puros `lib/proceso.ts`;
mueren las 8 defs mapeadas en D10 (STATES_ORDER · STATE_CLASSES→theme por id + fallback por
CATEGORÍA · STATE_OWNERS ×2 · OPERATOR_ALLOWED_TRANSITIONS+isOperatorAllowed ·
STATE_TOOLTIPS/TOOLTIPS.state_* · WIP_CAPS+chips · edit-permissions STATE_ORDER→`editOrden`
derivado: índice del array, pausado edita como el inicial, descartado=∞) **y las que la fase
encontró fuera del mapa**: ProcesoTab (MAIN_FLOW→happy-path por categoría · STEP_META→dueños+
descripcion · STEP_CURRENT_CLS→theme · el literal `developed` del form gate G→gate con
autoridad operador y momento-estado) + NewStoryModal (estado inicial derivado) + las routes
dev-mode Next derivan del MISMO espejo (`lib/proceso-server.ts`). `LOCK_FROM_STATE` QUEDA:
política de ENTIDAD por artefacto, fuera del descriptor v1 (SPEC F4 §6). **Botón (D17)**:
«⚡ Lanzar sesión de delivery» en el tab Proceso → `/delivery?story=<id>` con preselección.
Tests (RN-54): los que fijaban hardcodes se REEMPLAZARON por tests de contrato —
`lib/__tests__/proceso.test.ts` (fixture default + ALTERNO: "otra empresa, otro descriptor,
cero cambio de consola") + edit-permissions matriz contra fixture; Go `TestProcesoVerbos`.
Suites: Go verde + vet · 172 vitest + typecheck · gate de fábrica verde. **Round-trip visual
verificado en browser (:4777)**: board idéntico (mismas columnas/orden/colores, tooltips desde
`descripcion`, WIP chips derivados), drawer con stepper G·R derivado y botones nombre+verbo,
`/proceso` rinde los 13 verbos, `/delivery` preseleccionada desde el drawer con chip
`⚡ story.refined`; transición ida-y-vuelta por curl dejó el checkpoint byte-idéntico.

*Desarrollo — CIERRE (resumen F0→F6):* F0 norte v3 firmado tras debate + investigación
(DH-02/DH-03) · F1 modelo 2 ejes + registro 3 bandas + SPEC torre (DH-04) · F2 torre MVP
read-only viva — cazó un drift real en su primer boot (DH-05) · F3 lente arquitectura por
`meta.clase` (DH-06/I-75) · F4 descriptor de proceso — kit shipea, DevHub deriva (DH-07/I-77)
· F5 cockpit de delivery — sidecar Agent SDK, dogfood e2e success (DH-08) · F6 verbos + board
gobernado + cierre (esta ficha). Las 4 SPECs permanentes viven en `products/devhub/specs/`
(torre-read-only · torre-arquitectura · proceso-descriptor · delivery-cockpit ·
proceso-verbos-board). La carpeta temporal `epicas/torre-de-control/` se BORRÓ (era temporal
por diseño); lo no-promovido de INVESTIGACION.md que vale retener quedó como deudas abajo.

*Deudas que quedan (post-épica):* **(a)** rename comercial del binario/CLI `cockpit` (DH-01 —
hay spec ya refinada por la sesión dogfood en
`~/.prenter/devhub/sesiones/s-20260703195018-lhnk/salida/spec-rename-binario-devhub.md`;
aplicarla = story aparte) · **(b)** curado real `prenter/sistemas/sistemas.yaml` — la torre
corre contra fixture (RN-07) y el check de prenter no propaga exit (hallazgo DH-05, lado
EMPRESA) · **(c)** sesiones BUILD con worktree (D12 dejó solo ESPECIFICACIÓN) · **(d)**
catálogo de capabilities con sobre de entidad (principio 4 — único principio del norte sin
ejecutar; sin ficha aún) · **(e)** log/timeline de eventos de delivery como dato PUBLICADO
(la costura con P4; D15 lo dejó fuera) · **(f)** transiciones GLOBAL estilo Jira
(cualquier-estado → X) — hoy el descriptor enumera `→parked/→dropped` a mano (nota de
INVESTIGACION §A) · **(g)** superficies del Agent SDK sin usar (permisos en vivo
`canUseTool`, `resume`, `fork_session` — INVESTIGACION §B murió con la carpeta; rederivar de
code.claude.com/docs al retomarlas).

*Conecta:* DH-02..DH-08 (las fases) · I-77 (contrato de ecosistema que F6 extiende a v2) ·
KIT-08 (CHANGELOG del kit — la instancia v2 viaja Unreleased; la versión la decide P3) ·
I-75/I-72 (espejos CLASE: cada producto su renderizador · motor/consola) · D4/DevLake
(categorías fijas + nativo al lado — la regla que hizo trivial esta migración).

*Siguiente:* la épica MURIÓ — el trabajo sigue por stories/fichas normales. Candidatos en las
deudas (a)-(g); el norte vivo de la célula = `VISION.md` + las 5 SPECs.

### DH-10 · Mecanismo de conexión con Claude Code — driver CLI-nativo sobre la instalación del usuario (BYO licencia, sin API) — `decidida` · `vig:vigente`

*Cruda (operador):* "leí que podíamos conectarnos a claude code con stdin y stdout — nuestra
'aplicación' solo es un visor que facilita la interacción con claude code. Antes de continuar
quiero ver el mecanismo de conexión con claude code y que quede como decisión, ¿cuál es el
mejor? considerando que estamos ahora en linux, pero de alguna forma deberemos tener
instaladores para windows y linux". Condición agregada a mitad del debate: **"es condición que
no sea por API de Anthropic — cada usuario tendrá su licencia claude code instalada en la
computadora"**. Checkpoint del fork expiró sin respuesta (60s, AFK) → recomendada aplicada
(mecánica de la casa).

*Desarrollo:* verificación fresca contra docs oficiales (agente claude-code-guide — la deuda
(g) de DH-09 pedía rederivar de docs al retomar): (1) **el Agent SDK no es un transporte
distinto** — spawnea el binario `claude` como subproceso y le habla por stdin/stdout
stream-json; SDK = driver oficial sobre el mismo tubo (tipado, `canUseTool`, `resume`/`fork`;
el npm exige Node 22+, bundlea un binario CC como optional dependency,
`pathToClaudeCodeExecutable` permite apuntar a otro). (2) **CLI headless**:
`--input-format/--output-format stream-json` existen; el esquema de mensajes está
sub-documentado público (costo de mantenimiento propio si se usa crudo); aprobaciones en vivo
vía `--permission-prompt-tool` (MCP, v2.1.199+) — la conclusión de DH-03 §B ("headless CLI
insuficiente para aprobaciones en vivo") queda **SUPERADA**. (3) **CC tiene instaladores
nativos oficiales** para Windows, Linux y macOS sin Node — Anthropic mantiene ese runtime.
(4) **Política verificada** (docs auth): "Anthropic does not allow third party developers to
offer claude.ai login or rate limits for their products, including agents built on the Claude
Agent SDK" → la vía sancionada del SDK para productos = API key; la condición del operador la
excluye. (5) JSONL de sesiones sigue interno (la superficie soportada = API pública de
sesiones del SDK). **Opciones evaluadas:** A CLI-nativo (Go spawnea el `claude` DEL usuario) ·
B sidecar SDK apuntado al CC del usuario (arrastra bundle de Node al instalador + zona gris
suscripción-vía-SDK) · C puerto con 2 adapters (difiere, doble mantenimiento). **Decisión:
A — driver CLI-nativo.** Modelo Conductor: el usuario instala y loguea SU Claude Code (su
licencia, su binario, su config); DevHub opera esa instalación local igual que su terminal,
sin tocar credenciales; cero API de Anthropic en el producto. Instalador DevHub = **binario Go
solo** (cross-compile Win/Linux/Mac); muere la necesidad de bundle de Node. El sidecar (DH-08)
queda como **adapter transitorio de dogfood** hasta que el driver Go-nativo alcance paridad
con el contrato interno — RN-35..RN-44 NO cambian: se reemplaza el motor, no el contrato
UI/API. Mitigaciones del drift de formato (el CC del usuario se auto-actualiza): gate de
versión mínima (`claude --version` al conectar) + parser tolerante a eventos desconocidos
(patrón `eventos.jsonl` actual). ⚠ Salvaguarda: el modelo BYO-CC es el estándar del ecosistema
de wrappers (Conductor verificado en DH-03 §C) pero los docs no lo bendicen explícito por
escrito — verificación formal de Consumer Terms ANTES de vender instalables a cliente.
**Supersede parcial de DH-08**: "auth = API key como contrato de producto" deja de ser el
norte del delivery-cockpit; queda válido solo si un cliente elige API key por su cuenta.

*Conecta:* DH-03 (§B investigación — parcialmente superada aquí; §C Conductor = el modelo
adoptado) · DH-08 (el sidecar = embrión, ahora adapter transitorio; supersede parcial de su
auth) · DH-09 deudas (c)(g) (BUILD worktree y superficies SDK se rederivan sobre el CLI:
`--permission-prompt-tool`, `--resume`) · DH-01 (el rename precede al instalable) · I-76
(patrón conductor, precedente P4).

*Siguiente:* story «driver CLI-nativo en Go» (spawn del `claude` del usuario + stream-json +
gate de versión + paridad con el contrato del sidecar) → al verificarla, borrar el sidecar →
story «instalable v1» (cross-compile + firma + updater) tras el rename DH-01.

### DH-11 · Graduación de P2 — DevHub sale a repo propio; esta célula queda CONGELADA como fuente del port — `decidida` · `vig:vigente`

*Cruda (operador, 2026-07-04):* "esto ya creció más de lo que buscábamos y será un producto
propio con su propio repositorio… debe nacer limpio, con la nueva visión [construir y mantener
software basado en proceso y arquitectura; trabajo orquestado multi-rol (CTO·developer·devops·
PO) sobre uno o varios sistemas; GitHub como conector], y como arneses de construcción vamos a
usar los del KIT DEV (plugin)". Forks firmados por AskUserQuestion: nombre **DevHub** (repo
`devhub`, binario `devhub`) · graduación con célula congelada · GitHub privado en alpacapurpura.

*Desarrollo:* graduación ejecutada — repo `~/Proyectos/devhub` (remote
`alpacapurpura/devhub`, privado) nacido limpio: VISION.md ampliada + LEDGER propio (arranca
**DH-12**; DH-01..DH-11 quedan AQUÍ como historia) + épica «Experiencia Orquestada» (borrador
de norte, F0 por firmar allá) + kit dev instalado como plugin
(`harness@prenter-marketplace` estable, scope project — dogfood del flujo KIT-06). La
mecánica de graduación I-69 ("clientes + cadencia propia") se adelanta deliberadamente sin
clientes — decisión del operador, registrada. **Esta célula queda CONGELADA**: read-only,
fuente del port gradual (nada nuevo se desarrolla aquí); el rename DH-01 muere de nacimiento
en el repo nuevo (binario `devhub`); las deudas (a)-(g) de DH-09 y la DH-10 (driver
CLI-nativo) se ejecutarán en el repo nuevo cuando la épica las pida. Se archiva la célula
cuando el port termine.

*Conecta:* DH-12 (la ficha fundacional en el repo nuevo) · I-NN ecosistema (graduación, en
`tooling/strategy/LEDGER.md`) · I-69 (mecánica de graduación) · DH-10 (decisión que viaja) ·
KIT-06 (el marketplace que alimenta al repo nuevo).

*Siguiente:* todo el trabajo de producto sigue en `~/Proyectos/devhub` (F0 de la épica). En
este monorepo: solo consultas de fuente para el port.

<!-- CÉLULA CONGELADA (DH-11) — próximas fichas del producto: en ~/Proyectos/devhub (DH-12+) -->

## Log

| Fecha | Decisión | Fichas |
|---|---|---|
| 2026-07-01 | Fundación de la célula P2 (de I-69): nombre DevHub; hereda go+ui; delta = ramas/releases/roles; (directorio) = huésped de P1. | DH-01 |
| 2026-07-03 | Épica Torre de Control, F0: norte firmado (checkpoint expiró → recomendada aplicada); auditoría fría — I-74/CK-08 verificado, colisión de nombre "gate", multi-repo ya existe pero registro vivo huérfano (pre-I-39), patrón `flota.yaml` de OBS-15 como espejo recomendado, 2 formatos de ledger incompatibles, modelo de datos reformulado a 2 ejes (repo × célula). | DH-02 |
| 2026-07-03 | Norte v3 de la épica FIRMADO tras debate + investigación: DevHub = consola de delivery gobernada por proceso (3 capas: proceso-como-dato · as-code · sesiones CC; diferencial vs Conductor = orquestar ENTREGA, no sesiones). Descriptor de proceso = ficha ecosistema futura (kit shipea, DevHub renderiza); desktop instalable entra como F5 (Agent SDK, sidecar Node); fases F0-F6; fronteras actualizadas (Harness Studio, muerte del Atlas/I-75). | DH-03 |
| 2026-07-03 | Épica Torre de Control, F1 (checkpoint expiró → recomendadas): modelo 2 ejes REPO×PROYECTO validado contra 3 casos reales (worktree-aware, proyecto nullable); registro = espejo 3 bandas de OBS-15 (curado `prenter/sistemas/sistemas.yaml` + adapter → wire format actual + fábrica contrato/check/fixture); ledger de célula = `ledger.yaml` generado por `gen_ledger.py` extendido (un parser, células ganan gate); veredicto anti-drift = «gate de fábrica»/`gate_fabrica`, categorías fijas + nativo al lado. SPEC congelada: `specs/torre-read-only.md` (RN-01..RN-19). | DH-04 |
| 2026-07-03 | Épica Torre de Control, F2: torre MVP read-only VIVA implementando la SPEC sin retocarla — registro 3 bandas ejecutado (fixture RN-07, huérfano chris-corp reemplazado con `.bak`), `nombre`+`gate_check` aditivos al wire (round-trip verde), `ledger.yaml` × 4 células gated, colectores 2 ejes + `GET /api/torre` + vista `/torre` omnigent; demo en_vuelo verificada en vivo; la torre cazó un drift real en su primer boot. Hallazgo EMPRESA: `check.py` de prenter no propaga exit (imprime error, retorna 0). | DH-05 |
| 2026-07-03 | Épica Torre de Control, F3 (checkpoint expiró → recomendadas D5-D7): lente ARQUITECTURA viva en el eje PROYECTO — SPEC congelada `specs/torre-arquitectura.md` (RN-20..RN-26); nace `products/devhub/arquitectura.yaml` (curado, `meta.clase: modelo`) + check genérico `check_arquitectura_celula.py` en gen_all (check-only, cero emisión — la torre ES el renderizador de DevHub, I-75); colector `torreArquitectura` aditivo en `proyectos[]`; render por clase en `/torre` (tabla por planos, componente → fichas·ruta·relaciones). Verificado en browser: devhub y cockpit `con-arquitectura · modelo · 14 comp`; kit/harness-studio `sin-arquitectura` honesto. Cross-célula = filesystem directo: el YAML gated ES el contrato (RN-21). | DH-06 |
| 2026-07-03 | Épica Torre de Control, F4 (checkpoint expiró → recomendadas D8-D10): el ciclo SDD 10-estados deja de ser hardcode — instancia 1 del descriptor de proceso (contrato de ecosistema I-77: kit shipea `process/sdd-default.yaml` · schema L0 `process-descriptor` · DevHub deriva e interpreta). SPEC `specs/proceso-descriptor.md` (RN-27..RN-34); `gen_proceso_descriptor.py` valida+emite espejo gated que el binario embebe; `gates.go` deriva sus tablas (firmas intactas, terminalidad por categoría); `GET /api/proceso` + vista `/proceso` cero-literales. Round-trip: suite Go verde sin tocar tests viejos + legacy congelado como test + descriptor alterno probado. Verificado en browser :4777. | DH-07 |
| 2026-07-03 | Épica Torre de Control, F5 (D11-D14 confirmadas): cockpit de delivery VIVO — el descriptor parametriza sesiones de agente con as-code inyectado. Sidecar Node/Agent SDK supervisado por el binario (handshake stdout + muerte por stdin-pipe; un comando sirve todo = embrión del instalable); `GET /api/delivery/plantilla` deriva tramo/dueño/gate SOLO del dato (probado con descriptor alterno); vista `/delivery` (prompt precargado → humano encausa → lanza → eventos por polling); workspace aislado por sesión, RN-31 intacto; auth = API key (dogfood: credencial local, I-76). SPEC `specs/delivery-cockpit.md` (RN-35..RN-44). Dogfood end-to-end en browser: sesión `refining→refined` sobre la deuda DH-01 → success · 7 turnos · 59s → spec en `salida/`. Contrato sidecar intra-célula → sin I-NN. | DH-08 |
| 2026-07-03 | Épica Torre de Control, F6 + CIERRE (checkpoint expiró → recomendadas D15-D17): verbos CDEvents vivos — contrato L0 v2 (`verbo` INTERPRETADO `<sujeto>.<predicado>` + `nombre` + `wip`, aditivos), instancia del kit v2 nombra los 13 eventos (CHANGELOG/KIT-08); el verbo viaja como DATO en `/api/proceso` + respuesta de transition + `tramo.verbo` (sin log — la costura P4 queda como deuda). Board GOBERNADO por el descriptor: `ProcesoProvider` + `lib/proceso.ts`; mueren las 8 defs de D10 + las de ProcesoTab/NewStoryModal/routes-dev; `{target}_reason` genérico; botón «lanzar sesión» drawer→`/delivery?story=` (D17). SPEC `specs/proceso-verbos-board.md` (RN-45..RN-54); tests de hardcode → tests de contrato (fixture default+alterno); suites Go+UI+gate verdes; round-trip visual verificado en browser. ÉPICA CERRADA: carpeta temporal BORRADA, resumen F0-F6 + deudas (a)-(g) en la ficha. | DH-09 |
| 2026-07-03 | Mecanismo de conexión con Claude Code FIRMADO (checkpoint expiró → recomendada A): **driver CLI-nativo** — Go spawnea el `claude` instalado DEL USUARIO vía stdin/stdout stream-json (BYO licencia, SIN API de Anthropic; modelo Conductor). Verificación fresca de docs: el SDK es wrapper del mismo tubo; `--permission-prompt-tool` supera el «headless insuficiente» de DH-03 §B; CC tiene instaladores nativos en las 3 plataformas. Instalador DevHub = binario Go solo (muere el bundle de Node); el sidecar DH-08 queda como adapter transitorio de dogfood; supersede parcial del auth de DH-08 (API key deja de ser el norte). Salvaguarda: verificación formal de Consumer Terms antes de vender. | DH-10 |
| 2026-07-04 | **GRADUACIÓN**: DevHub sale a repo propio `~/Proyectos/devhub` (`alpacapurpura/devhub`, privado) con visión ampliada (proceso+arquitectura as code · trabajo orquestado multi-rol · GitHub conector); binario `devhub` (muere DH-01 de nacimiento); kit dev como plugin (`harness@prenter-marketplace`); épica «Experiencia Orquestada» sembrada. ESTA CÉLULA QUEDA CONGELADA = fuente read-only del port gradual. El ledger del producto continúa en el repo nuevo (ficha 12 en adelante). | DH-11 |
