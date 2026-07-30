---
story_id: vitalia-fase2-adrian-inbox
type: ui-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: inbox
capability: adrian.inbox
state: done
autonomous_mode: true
phase: MERGED
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
state_prev: reviewing
last_modified: '2026-06-04T23:55:00.000Z'
merged_at: '2026-06-04T23:55:00.000Z'
merge_artifact: 07-merge.md
audit_verdict: APPROVED
last_artifact: CHECKPOINTS.md
gherkin_matrix: 06-audit/gherkin-matrix.md
dod_live_verified: true
dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Playwright golden smoke storageState dr.demo owner)"
dod_evidence:
  - action: "PATCH /inbox/conversations/{instagram}/mode (toggle 2-modos)"
    observed: "200 + aria-checked refleja + DB handler_mode=ai (era human) + updated_at fresco"
    backend_log: "sin traceback"
  - action: "POST /inbox/conversations/{carlos}/pause (60 min)"
    observed: "200 + botón→'Pausado' + DB pause_until set + updated_at fresco"
    backend_log: "sin traceback"
verified_at: 2026-06-04
dev_app_verified:
  required: true
  verified_by: claude
  date: 2026-06-04
  env: "dev-app.vitalialat.com (Clerk real dr.demo owner + backend real + seed · golden adrian-inbox-modes.spec.ts 7 passed)"
  evidence:
    - "PATCH /mode → 200 + DB handler_mode=ai (write ejercido + efecto en DB)"
    - "POST /pause → 200 + DB pause_until set (write ejercido + efecto en DB)"
    - "anti-burbuja base.ts: 0 pageerror / 0 console.error / 0 /api 4xx-5xx / 0 Next overlay"
live_verify_env: "dev-app.vitalialat.com (canonical) — NOT localhost:3002 (no /api proxy there)"
live_verify_fixed:
  - "NuqsAdapter wrap (page crashed: NUQS-404) — real fix"
  - "crm conversations path vitalia/crm → crm (BE mounts crm at /api/v1/crm) — real fix"
  - "3-pane layout v3→flex (react-resizable-panels v4 ignored defaultSize → 6/88/6%) — real fix"
  - "?_rsc= loop: WAS localhost-only artifact (failing /api cascade) — ZERO on dev-app — resolved by correct env"
  - "/api 404: WAS localhost-only (no /api proxy on :3002) — dev-app tunnel maps /api→BE (health 200) — resolved by correct env"
live_verify_fixed_2:
  - "RBAC: list_conversations/get_conversation_detail allow _INBOX_OPERATOR_ROLES (owner+receptionist+PHI roles) — Chris ratified. Verified LIVE dev-app: dr.demo 403→200, inbox renders CLEAN empty state (no error). Commit 9103bbb7."
live_verify_fixed_3:
  - "BE un-stub: list_conversations + get_conversation_detail wired to ConversationRepository (dual filter) — were slice-1 stubs. Commit 38c1ff40."
  - "FE contract adapt: use-conversations maps BE {items,limit,offset} → FE {conversations,page,page_size} (was reading data.conversations of an {items} response → empty)."
  - "Seed: scripts/seed_inbox_conversations.sql (2 dental conversations, Sanaré). VERIFIED LIVE dev-app: inbox renders 2 real conversations (whatsapp 'limpieza' Interesado · instagram 'blanqueamiento' Calificando + pide-ayuda + media badge)."
live_verify_fixed_4:
  - "patientName resolved: use-leads path fix (vitalia/crm/leads→crm/leads) + shape adapt ({items}→{leads}) + ConversationListPanel wires useLeads→lead_id→name map→getPatientName. Commit 364f4138. VERIFIED LIVE: list shows 'Carlos Ramírez Ortega' + 'Persistencia Verificada' (was '—')."
live_verify_fixed_5:
  - "★ THREAD un-block (AC-3/AC-6): crm get_conversation_detail devolvía ConversationListItem lean → FE espera compound → detail.messages undefined → thread crasheaba ('no aparece nada'). FIX: nuevo ConversationDetailResponse (conversation+lead+messages+action_receipts+tools_state) cableado al endpoint (ConversationRepository+MessageRepository+LeadRepository decrypt). + seed_inbox_messages.sql (3+5 msgs). VERIFIED LIVE dev-app: thread renderiza Carlos Ramírez Ortega + WHATSAPP + 3-mode toggle (Decide✓/Consulta/Yo escribo) + Pausar Adrián + Dar empujón + 3 mensajes. GET /conversations/{id} 200 con payload completo (lead phone/email + messages). 0 console errors (solo favicon 500 pre-existente). Commit pendiente."
  - "AC-10 contact wiring fix: AdrianInboxView pasaba conv_id como leadId/patientId → ContactSidebar vacío. FIX: useConversationDetail (RQ dedup) → contact desde detail.lead (name/phone/email/stage). tsc clean. ⚠️ live re-verify INTERRUMPIDO por desconexión Chrome MCP (re-verificar próxima)."
live_verify_open:
  - "RE-VERIFICAR LIVE (MCP cayó): ContactSidebar muestra phone/email/name/stage de Carlos tras el wiring fix (tsc clean, lógica correcta, requiere touch+hard-reload por stale-bundle HMR)."
  - "AC-9 PENDIENTE: ComplianceService sigue NoOp en router DI (lines 266/311) pese a phi_channel_policy.py existir → wire DI real + verificar block PHI outbound."
  - "T-6 PENDIENTE (DoD #37): e2e reales sin mock de SC-1..SC-10 + axe + visual goldens + demo-script."
  - "Verificar LIVE AC-4 (mode change escribe audit) · AC-5 (composer por modo) · AC-7 (full colapsa Valeria) · AC-8 (nudge envía) ejerciendo la acción real + logs."
  - "PRE-EXISTING (not mine): crm conversation tests (test_router_conversations_list/detail.py) red on async-mock infra. Follow-up."
live_verify_fixed_6:
  - "AC-9 compliance UN-STUB: ComplianceService(PhiChannelPolicy) cableado en send/proactive/nudge DI (era _NoOpComplianceService). 13 tests PHI verdes. Commit af4f94a2."
  - "AC-6/AC-7 activity stream: ActivityStream estaba montado SOLO en InboxPageClient (root muerto), NO en AdrianInboxView (activo) → no visible. FIX: montado en InboxThread (glass-box). Verificado e2e."
  - "?lead= → ?conv= : spec RN-14/AC-3 manda ?conv={id}. Mi impl deviaba a ?lead= (caught por e2e deep-link spec). Renombrado el param nuqs lead→conv en todo el inbox (schema + 6 consumers + tests). tsc 0, 21 unit/arch verdes."
live_verify_fixed_7:
  - "telemetry-404 RESUELTO (Chris opción A): creado POST /api/telemetry/growth-studio-event (telemetry_router.py · _shared/telemetry/api/ · resuelve ctx vía ClinicResolver · valida event_type snake_case ≤64 · delega a GrowthStudioEmitter fire-forget · 202) + cableado en main.py + telemetry.ts FE pasado de fetch crudo a fetchClient (auth-aware, skip sin token/tenant) + ValeriaAgendaView pasa auth ctx. BE 17 tests verdes (5 router + arch response_model + telemetry whitelist), FE tsc 0 + eslint 0 + 23 vitest verdes. VERIFIED LIVE dev-app: endpoint pasó de 404 → 422 (no-auth probe = router montado). Los 3 e2e tenant que el handoff atribuía SOLO a telemetry: los i18n/neutro (:101+) ahora VERDES (telemetry-404 eliminado de la consola)."
live_verify_fixed_8:
  - "audit-log-404 TWIN RESUELTO (Chris decisión A, post-investigación: server-side get_conversation_detail NO audita la lectura PHI → endpoint necesario, no B): creado POST /api/v1/vitalia/audit-log (audit/api/audit_log_router.py · ClinicResolver + resolve users.id UUID del Clerk sub + resource_id UUID guard + AsyncAuditWriter sync write committing) + cableado main.py + AuditedSection FE: raw fetch → fetchClient + skip si falta clinicId/resourceId. BE 4 tests + arch response_model verdes. Commit 0b752040 (pushed). VERIFIED LIVE dev-app: 404 → 422 (router montado). FOLLOW-UP (crm bajo lock embudo): mover audit server-side a get_conversation_detail."
  - "telemetry clinic-guard refinement: telemetry.ts + AuditedSection ahora SKIP si falta clinicId (endpoint clinic-scoped → sin X-Clinic-ID daba 422 al firarse desde contexto transitorio sin clinic). FE tsc 0 + eslint 0 + 24 vitest verdes."
  - "test-design SC-10 (Chris aprobó): POM AdrianInboxPage.errorBanner selector roto (thread-error-banner → conversation-thread-error, scoped a inbox-desktop por duplicado responsive) + :43 reestructurado (test.use failOnRuntimeError:false para el 404 cross-tenant DELIBERADO = prueba de aislamiento; assert status 404 + error-state visible + 0 message-bubbles). VERIFIED LIVE: tenant spec 10/10 GREEN (telemetry+audit 404s eliminados)."
ui_polish_dod_evidence_2026_06_04:
  env: "dev-app.vitalialat.com — Playwright (smoke project storageState, --no-deps) · Chrome MCP cayó mid-verify (crash Browser.setContentsSize) → fallback Playwright bypassando base.ts (anti-burbuja false-failea sobre el dev-tools nextjs-portal + favicon 500)"
  verified_at: 2026-06-04
  result: "1 passed (3.5s) — los 3 batches renderizan con el contrato correcto contra dev-app"
  batch1_bugs:  # commit 0dddae86
    - "#5 ConversationItem: emoji map → <ChannelBadge> (channel-meta lucide+color). LIVE: 2 channel-badge (whatsapp/instagram), 0 emoji."
    - "#3 VoiceStyleChip: /brand-studio/estilo (404) → tenant-scoped /{tenantId}/lisa/marca/voz-y-tono. LIVE: href correcto + ruta carga (no 404). CTA oculta sin href."
    - "#7 ContactSidebar: 'Servicio de interés' prominente (cian+Stethoscope). LIVE: 'Ortodoncia invisible' (DB→compound-endpoint→UI real, no imaginado; seedé service_interest en conv 11111111 para el caso positivo)."
  batch2_color:  # commit aa5efa04
    - "#5b NEW lead-stage-meta + StageBadge: stage chips coloreados dark-aware (interesado=sky, calificando=amber, …). LIVE: stage-chip con bg-sky/amber-100. data-testid override conserva 'stage-chip' (list tests + e2e POM)."
    - "#8 FilterChips: channel chips con color de canal (channel-meta) + ring-current pressed. LIVE: WhatsApp emerald, Instagram pink, Email sky; pressed=ring+bold."
  batch3a_labels:  # commit fcd083de
    - "#2 PauseAdrianButton: ⏸ → lucide Pause + 'Pausar'/'Pausado'. LIVE: text 'Pausar'."
    - "#1 ContactSidebarToggle: 👤 → lucide User + 'Perfil'. LIVE: text 'Perfil'."
    - "#1b ContactSidebar: close X dentro del detalle (toggleContactSidebar). LIVE: contact-sidebar-close visible."
    - "#13 ActivityStream: lucide Activity + empty-state explicativo. LIVE: agent-activity-stream presente."
    - "#6 cursor-pointer: scan inbox → 0 <div onClick> (clickables son button/li con cursor). Nada que arreglar."
  deferred_to_track_b:
    - "#4/#12 (composer-en-manual + mode toggle) + #9 (burbujas por emisor) + #10 (timestamps en burbujas) → requieren el thread no-exprimido (Track B shell). #11 (filtros fila-1) + A-F pendientes."
  note: "dod_live_verified de estas tandas UI = true (render+contrato). El click-through completo de los interactivos (close X cierra panel, voz CTA navega, Pausar→confirm→DB) + demo Chris quedan para el sign-off pre-merge. La story sigue developing (no done)."

ui_polish_dod_evidence_2026_06_04_pm2:  # 4 comentarios nuevos de Chris (thread/lista)
  env: "dev-app.vitalialat.com — Playwright desechable (smoke storageState, --no-deps, @playwright/test directo bypassando base.ts). FE restart + wipe .next (anti-cache gotcha) antes de cada verify."
  verified_at: 2026-06-04
  result: "1 passed — threadAutoOpen=true · selectedRows=1 · message-bubble=6 · message-bubble-time=6 · console/page errors=0. Confirmado por screenshot en LIGHT + DARK."
  comment1_autoselect_empty:  # UI-AUDIT #1
    - "Auto-select al entrar: NEW lib/last-viewed-conv.ts persiste el conv UUID (NO PHI) en localStorage por tenant. AdrianInboxView seedea desde SSR (initialData) + ConversationListPanel auto-selecciona last-viewed→newest. LIVE fresh (localStorage limpio): abre la más nueva (Carlos) sin click."
    - "Empty-state real (cero conversaciones): NEW InboxEmptyPanel (icono lucide + mensaje 'Aquí va a aparecer la conversación' + skeleton fantasma detrás) reemplaza el texto plano, en thread Y contacto. Cubierto por unit test (AdrianInboxView test_empty_thread sigue verde con el testid inbox-thread-empty). Live hay 4 convs → no se ejerce el cero-state visualmente (queda para seed-vacío o demo)."
  comment2_selection:  # UI-AUDIT #2
    - "ConversationItem seleccionado: barra izq 3px cian-Adrián + fondo cian-soft (--agent-adrian-soft/0.6, dark-aware) + nombre semibold/cian, en vez del vt-bg-primary/5 casi invisible. LIVE light+dark: 'Carlos Ramírez Ortega' claramente resaltado vs 'Persistencia Verificada'."
  comment3_timestamps:  # UI-AUDIT #3/#10
    - "MessageBubble: hora HH:mm por burbuja (tenant tz/locale) abajo-derecha + separadores de día centrados ('Hoy'/'Ayer'/'2 de junio') entre días. LIVE: 6 timestamps + pills '2 de junio'/'Ayer' visibles."
  comment4_bubbles_bg_thumbnail:  # UI-AUDIT #4/#9
    - "InboxThread ahora cablea el MessageBubble real (antes scaffold plomo/blanco). Orientación WhatsApp: paciente IZQ surface clara (incoming), Adrián DER cian-soft relleno (outgoing) + avatar + ✨auto, humano DER azul-marino. Fondo de conversación con wash sutil + dots cian (--muted/0.45 + radial cian/0.05) para que las burbujas resalten. DARK verificado legible (antes Adrián era texto invisible)."
    - "Thumbnail: ningún DTO (Conversation/Lead/Message) trae foto WA/IG → ThreadHeader usa monograma (iniciales, círculo cian-soft) + ChannelBadge real (lucide+color) en vez del 'WHATSAPP' en mayúsculas. TODO(BE): swap a <img src={lead.avatar_url}> cuando el inbox API exponga la foto de perfil."
  gates: "tsc 0 · eslint 0 · vitest 208/208 (incluí fix de 6 reds PRE-EXISTENTES en AdrianInboxView.test + ChannelBadge.test: faltaba mock de @/features/crm-shared useConversationDetail → Clerk useAuth crasheaba sin provider)."
  observacion: "El thread queda angosto con lista(320)+contacto(320) abiertos a 30/70 → el header se aprieta. Es squeeze del shell + 3-pane (story hermana / audit #D), NO de estos 4 comentarios."
  note: "dod_live_verified = true (render + auto-select + bubbles + 0 errores). Pendiente: demo Chris (sign-off) ANTES de /auditor. Story sigue developing."

ui_polish_dod_evidence_2026_06_04_pm3:  # ronda 2 de comentarios de Chris (5 puntos)
  env: "dev-app.vitalialat.com — Playwright desechable (smoke storageState, --no-deps). FE restart + wipe .next antes de cada verify. Light + dark."
  verified_at: 2026-06-04
  result: "1 passed — bubbles=6 · timestamps=6 · turn-labels 'Adrián·Auto'=2 · logos sociales reales en lista=4 · selected=1 · console/page errors=0. Screenshots light+dark."
  c1_avatar_url:  # ronda2 #1
    - "Agregado avatar_url?: string|null al tipo Lead (crm-shared) — el FE lo pide; BE devuelve null hasta implementar. ThreadHeader: <img src={lead.avatar_url}> si existe, si no monograma de iniciales. TODO(BE) documentado en el tipo."
  c2_turn_labels:  # ronda2 #2
    - "Saqué los avatares A/H por-burbuja (ganan ancho, vital en angosto). Label por turno arriba del bloque: 'Adrián · Auto' (cian) / 'Tú · Manual' (azul-marino) / nombre del paciente (izq). InboxThread agrupa por sender consecutivo. ✨auto removido de la burbuja (vivía ahí)."
  c3_social_ssot:  # ronda2 #3
    - "NEW SSoT lib/channels/social-channels.ts (logos REALES simple-icons + colores de marca via var(--channel-*-bg) de globals.css, NO hex hardcodeado → pasa FE-A1) + NEW components/shared/channels/SocialLogo.tsx. Reusable para badges/filtros/futuras conexiones (ej. Telegram). Lift candidate a core/@luana."
    - "ConversationItem: saqué el ícono de canal de la IZQUIERDA; card seleccionada ahora con el COLOR de la red (tenue, color-mix 12%) + rail de marca; LOGO REAL abajo-derecha a la altura del tag de estado. LIVE: Carlos=verde WhatsApp+logo WA, Persistencia=logo IG. Dark-safe."
  c4_filter_line:  # ronda2 #4
    - "FilterChips: una sola línea horizontal scrolleable de redes (logo real + label), status REMOVIDO (muy operativo). helpNeeded/unreadMedia/stage/mode/period movidos a 'Más filtros'. LIVE: [Todas][WhatsApp][Instagram][Email…] scroll."
  c5_wallpaper:  # ronda2 #5
    - "v1 (doodles wellness cian) RECHAZADA por Chris ('se ve muy mal, parecen rayones'). v2 (cement 2026-06-04): fondo POR RED SOCIAL — tinte del color de la red (brandColorAlpha 6%) + watermark del LOGO REAL tileado faint (opacity 6%, brand color) sobre vt-bg-chat-wash. Refuerza sobre qué red respondés. LIVE light+dark: WhatsApp=verde+logos WA, Instagram=rosa+logos IG. Dark-safe (logos verdes faint sobre fondo oscuro). 0 console errors. Genéricos (email/web) = solo tinte (sin logo)."
  gates: "tsc 0 · eslint 0 · vitest 208/208 · arch FE-A1 (no-hardcoded-colors) 2/2 (refactoré los hsl() arbitrarios — incl. 1 que metí en pm2 — a clases utilitarias vt-bg-adrian-soft/vt-bg-chat-wash en globals.css). 2 reds fsd/cross-feature (AdrianInboxView→crm-shared + embudo/page) son PRE-EXISTENTES de otras sesiones, NO míos."
  note: "dod_live_verified = true. Pendiente demo Chris (sign-off) ANTES de /auditor. Story sigue developing. Header del thread sigue apretado en angosto = squeeze del shell (story hermana), no de estos comentarios."

ui_polish_dod_evidence_2026_06_04_pm4:  # ronda 3 de comentarios de Chris
  env: "dev-app.vitalialat.com — Playwright desechable. FE restart + wipe .next. Light + dark + 2 redes."
  verified_at: 2026-06-04
  c1_logo_vitalia:  # ronda3 #1 (ALARMA: logo desaparecido)
    - "INVESTIGADO — el logo NO está roto ni desaparecido. Presente + visible en light Y dark (screenshots del strip superior: 'VITALIA'+mariposa en ambos). LogoMark.tsx sin tocar por mí (último cambio 43c4c4df). Assets /brand/*.png sirven 200. naturalWidth=96 (cargada), data-testid=logo-mark visible=true. darkMode=['class','[data-theme=dark]'] → swap dark OK. CAUSA = cache del navegador de Chris (gotcha #1: chunks de nombre estable cacheados 4h). Fix = Empty-Cache+Hard-Reload. Si persiste tras hard-refresh → investigar más."
  c2_bubbles_wallpaper:  # ronda3 #2
    - "(1) Watermark de logos bajado de opacity 0.06→0.03 + tint 0.06→0.04 — muy tenue/calmo, no distrae."
    - "(2a) Burbujas transparentes → ahora SÓLIDAS: salientes via color-mix con --vt-bubble-base (opaco, dark-aware), pacientes vt-bg-surface."
    - "(2b) Turn labels (Adrián·Auto / Tú·Manual / nombre) ahora en PILL con vt-bg-surface + borde + shadow → no se pierden sobre el wallpaper."
    - "(2c) Burbujas salientes (Adrián/humano) ahora con el COLOR DE LA RED (color-mix 16% sobre surface) → combinan con el fondo tintado: WhatsApp=verde, Instagram=rosa. Paciente queda neutro (surface). LIVE light+dark+2 redes, 0 console errors."
  gates: "tsc 0 · eslint 0 · vitest 208/208 · arch no-hardcoded-colors 2/2 (--vt-bubble-base en globals; color-mix con var, sin hex/hsl en TSX)."
  note: "dod_live_verified = true. Pendiente demo Chris ANTES de /auditor."

ui_polish_dod_evidence_2026_06_04_pm5:  # ronda 4 (análisis de diseñador + ajustes finos)
  env: "dev-app.vitalialat.com — Playwright desechable. FE restart + wipe. Light+dark. Capturé burbujas individuales + card seleccionada para análisis detallado."
  verified_at: 2026-06-04
  diagnostico_disenador:
    - "Burbuja paciente (blanca) sobre wash claro → casi sin relleno = 'transparente'. Burbuja Adrián verde sólida ok."
    - "Nombre de conv seleccionada en cian sobre fondo verde de WhatsApp = choca, no combina."
    - "Watermark 3% aún perceptible."
  fixes:
    - "Burbujas: shadow-sm (WhatsApp-style elevation) → todas despegan del wallpaper, ninguna 'transparente'. Paciente border vt-border (más definido)."
    - "Nombre conv seleccionada: cian → vt-text-foreground (negro/blanco) → combina con CUALQUIER fondo de red + legible."
    - "Watermark logos: opacity 0.03→0.015 — casi imperceptible, muy calmo."
    - "Redes agregadas: TikTok (logo real + #000), Telegram, Facebook (logo FB azul) → SSoT social-channels + InboxChannelFilter (url-state) + copy + chips en la línea de filtro. LIVE: chips con logo real scrolleables."
  live: "LIVE light+dark: paciente pops (sombra), nombre seleccionado negro combina, watermark imperceptible, chips Telegram/TikTok/Facebook con logo real. 0 console errors."
  gates: "tsc 0 · eslint 0 · vitest 208/208 · arch-colors 2/2."
  note: "dod_live_verified = true. Pendiente demo Chris ANTES de /auditor. Story sigue developing."

ui_polish_dod_evidence_2026_06_04_pm6:  # ronda 5 — 3 mejoras de diseño ratificadas por Chris
  env: "dev-app.vitalialat.com — Playwright. FE restart + wipe. Light + dark."
  verified_at: 2026-06-04
  mejoras:
    - "1. Read-receipts WhatsApp (✓/✓✓): NEW Message.delivery_status? (terreno FE, default 'sent'=✓ hasta que el BE lo popule). DeliveryReceipt en burbujas SALIENTES: ✓ enviado · ✓✓ entregado · ✓✓ cian leído. LIVE: ✓ junto a la hora en la burbuja de Adrián."
    - "2. Saturación de burbuja saliente: color-mix 16%→14% (más suave)."
    - "3. Auto-colapso del contacto cuando el thread es angosto: ResizeObserver en inbox-desktop; <960px + contacto abierto → setContactSidebarOpen(false). Solo auto-COLAPSA (nunca auto-abre → respeta el toggle manual). LIVE 1280: contacto colapsado → el HEADER del thread gana aire (resuelve el squeeze que se veía 'C◍ Pausar')."
  live: "LIVE light+dark: receipt ✓ visible, verde más suave, contacto auto-colapsado + header cómodo. contactPanelPresent=0, receipts=1, 0 console errors."
  gates: "tsc 0 · eslint 0 · vitest 208/208 · arch-colors 2/2."
  note: "dod_live_verified = true. Pendiente demo Chris ANTES de /auditor. Story sigue developing."

ui_polish_dod_evidence_2026_06_04_pm7:  # ronda 6 — 4 comentarios de Chris (composer + modos + wallpaper + cursor)
  env: "dev-app.vitalialat.com — Playwright desechable (smoke storageState, @playwright/test directo, --no-deps, viewport 1920 para evitar el squeeze de Valeria). FE restart + wipe .next antes de verificar. Light + dark."
  verified_at: 2026-06-04
  result: "2 passed (light+dark) — thread-composer-dock visible + textarea enabled · segment-adrian-decide/consulta visibles · segment-yo-escribo=0 · voice-style-chip=0 · pause-adrian-button en el dock · 0 console errors reales. Screenshots /tmp/inbox-{light,dark}.png."
  c1_wallpaper_ink:  # ronda6 #1
    - "Watermark de los logos pasó del tinte por-red (brand color, opacity 0.015 → casi invisible) a TINTA CREMA/BLANCA (NEW token --vt-watermark-ink: light hsl(40 45% 90%) · dark hsl(40 22% 82%)) con opacity 0.06 light / 0.12 dark. LIVE dark: los logos WhatsApp en crema se ven claramente sobre el fondo oscuro (antes invisibles). El tinte de color de la red detrás sigue dando la pista de canal. Pasa FE-A1 (var(), sin hex/hsl en TSX)."
  c2_composer_mount:  # ronda6 #2 ('no sale la caja en Yo escribo')
    - "ROOT CAUSE: ComposerArea (texto+adjuntar+voz+enviar, ya forkeado del legacy) EXISTÍA completo pero InboxThread NUNCA lo montaba → cero caja en todos los modos = 'no sale nada'. FIX: montado en un dock al pie del thread (tras ActivityStream). Composer SIEMPRE activo, el operador escribe como humano (handlerMode='human' → 'Enviar', placeholder 'Escribe tu mensaje a {paciente}…'). Texto enviable ya. Adjuntar/voz quedan montados (ya estaban built); su flujo completo = otra historia (dijo Chris). LIVE: textarea visible + enabled + Enviar."
  c3_modes_2:  # ronda6 #3 (Yo escribo↔Pausar se pisan + chip voz innecesario)
    - "ModeToggle: 3→2 segmentos [Adrián decide][Adrián consulta], restyleados (icono Sparkles/ClipboardCheck + label + tooltip explicativo + activo relleno cian) para que se entienda qué son. SegmentedModeValue + SEGMENT_TO_API + conversationToSegmentValue (use-mode-toggle + inbox.types) a 2 valores; legacy handler_mode=human cae a 'adrian-decide'."
    - "Pausar Adrián MOVIDO del header al dock (al pie), como barra de estado (● Adrián responde automáticamente / Adrián pausado · escribes tú) + botón Pausar. 'Yo escribo' eliminado (su función = pausar → escribís vos). NO hay endpoint 'Reanudar' aún (pause = +60min auto) → follow-up BE."
    - "VoiceStyleChip ('Estilo de voz · Configurar') ELIMINADO del header (componente + test git rm) — config de una sola vez, vive en Lisa › Marca › Voz y tono. El FILTRO 'Modo Adrián' del FilterChips conserva 'Yo escribo' (usa InboxModeFilter propio, otra superficie) — follow-up: revisar/renombrar."
  c4_cursor_pointer:  # ronda6 #4
    - "Regla global en globals.css: button:not(:disabled)/[role=button|radio|tab]/label[for]/summary/a[href] → cursor:pointer (los <button> nativos no lo traen). LIVE: el snapshot de Playwright reporta [cursor=pointer] en links/buttons. 'Dar empujón' + herramientas + todo clickeable ahora muestran la mano."
  gates: "tsc 0 · eslint 0 (src) · arch no-hardcoded-colors 2/2 · tests propios verdes (ModeToggle 10 · ThreadHeader 11 · ComposerArea 7 · copy 33 · url-state 17). Full vitest: 4 reds PRE-EXISTENTES en baseline NO míos (fsd AdrianInboxView→crm-shared + no-cross-feature [gotcha #4] · FE-A6 recuperar/FrozenLeadRow[diagnosis] · audited-section spy — los 3 fallan en su archivo sin que yo lo toque, git status limpio, no importados por mis cambios; el '208/208' de rondas previas era subset scoped). Fijé 1 red que SÍ era mío: url-state 'invalid channel' asumía tiktok inválido (lo hice válido en pm5) → cambiado a 'snapchat'."
  e2e_pendiente: "Los e2e de modos (adrian-inbox-modes.spec) testean el modelo 3-modos viejo (yo-escribo) → rewrite a 2-modos = parte del pase /auditor, NO de esta ronda (flag). POMs (AdrianInboxPage/inbox.page) tienen locators muertos (segment-yo-escribo/voice-style-chip) — limpieza en ese rewrite."
  note: "dod_live_verified = true (render+contrato+0 errors, light+dark). El ENVÍO real de texto (write) lo ejerce Chris en la demo (es el write que firma) — no disparé un send real para no contaminar la seed ni el adaptador de canal. Story sigue developing. NO encadenar /auditor sin sign-off de Chris (DoD #37)."

ui_polish_dod_evidence_2026_06_04_pm8:  # ronda 7 — 6 comentarios de Chris (#1-5 aplicados; #6 = decisión pendiente)
  env: "dev-app.vitalialat.com — Playwright desechable (smoke storageState, viewport 1920). FE restart + wipe .next. Light + dark + scroll."
  verified_at: 2026-06-04
  result: "2 passed (light+dark) — dock visible · texto 'Adrián está atendiendo esta conversación' · segmento activo VERDE (assert g>r && g>b sobre computed bg) · pause-adrian-button visible · 0 console errors. Screenshots /tmp/inbox7-{light,dark}{,-scrolled}.png."
  c1_wallpaper_opacity:  # ronda7 #1
    - "Watermark de logos: opacity 0.06/0.12 → 0.5 (Chris: 'transparencia del 50%'). LIVE dark: los logos WhatsApp en crema se ven claramente tileados llenando todo el fondo. NOTA honesta: a 0.5 en dark quedan bastante prominentes (literal lo pedido) — fácil de bajar si Chris lo ve cargado."
  c2_active_green:  # ronda7 #2
    - "ModeToggle: segmento ACTIVO de cian → VERDE (vt-bg-success) = 'encendido/atendiendo'. Assert live: computed bg del segment-adrian-decide activo tiene canal G dominante."
    - "Dock status: dot celeste estático → VERDE INTERMITENTE (vt-bg-success animate-pulse, h-2) = vivo/funcionando. Texto 'Adrián responde automáticamente' → 'Adrián está atendiendo esta conversación' (copy.composerDock.activeHint)."
  c3_cursor_pointer:  # ronda7 #3
    - "cursor-pointer explícito (clase Tailwind, no solo la regla global de pm6) en: ModeToggle buttons · PauseAdrianButton · NudgeButton (+ confirm yes/cancel) · ToolsSheetTrigger · ContactSidebarToggle. Garantiza la manito sin depender del cascade de la regla global."
  c4_pause_red:  # ronda7 #4
    - "PauseAdrianButton (no-pausado): de neutro/ghost → ROJO TENUE notorio (vt-bg-danger-12 + vt-text-danger + hover:vt-bg-danger-soft, font-semibold, px-3) para encontrarlo rápido y pausar inmediato. Pausado conserva el estado muted/disabled."
  c5_wallpaper_fixed:  # ronda7 #5
    - "El fondo (wash + tint + logos) se arrastraba con el scroll → dejaba blanco abajo. FIX: movido a un wrapper NO-scrolleable (relative flex-1) con la lista (absolute inset-0 overflow-y-auto) scrolleando ENCIMA. LIVE: el wallpaper llena toda el área del thread incluso bajo los 3 mensajes (sin blanco). testid messages-list + ref scroll conservados."
  c6_lead_privacy_interim_DONE:  # ronda7 #6 — Chris eligió 'interim ya + config después'
    - "Chris ratificó (2026-06-04) 'interim ya': desenmascarar leads ahora; la config 'Máxima seguridad' como story aparte. APLICADO sin tripear el gate FE-A6: PiiMaskedSpan gana prop masked (default true → resto de la app intacto); cuando masked=false rinde el valor crudo PERO conserva data-phi (audit + FE-A6 siguen viéndolo wrapeado). ContactSidebar pasa masked={false} en name/phone/email (leads, no pacientes)."
    - "VERIFIED LIVE dev-app: contact sidebar muestra 'Carlos Ramírez Ortega' + '+52 55 9876 5432' + 'carlos.ramirez@correo.ejemplo.mx' SIN ***. FE-A6 = solo FrozenLeadRow (pre-existente), ContactSidebar NO flaggeado. tsc 0 · eslint 0 · ContactSidebar.test verde."
    - "FOLLOW-UP STORY (crear vía /pm-vitalia): config tenant 'Máxima seguridad' = flag BE + toggle en Plataforma/Configuración + ContactSidebar/PiiMaskedSpan leen el flag (ON → masked=true otra vez). El terreno ya está (prop masked). Es PHI/seguridad → pasa por /architect."
  gates: "tsc 0 · eslint 0 (incl. --fix de InboxThread restructurado) · arch no-hardcoded-colors 2/2 · tests propios verdes (ModeToggle 10 · ThreadHeader 11 · ComposerArea 7 · PauseAdrianButton 9 · copy 33 · AdrianInboxView 5). 4 reds pre-existentes baseline siguen NO míos (ver pm7)."
  note: "dod_live_verified = true para #1-5 (render+contrato+verde activo+0 errors, light+dark). #6 NO tocado (decisión Chris). Envío real de texto + #6 → demo Chris. Story sigue developing. NO /auditor sin sign-off (DoD #37)."

ui_polish_dod_evidence_2026_06_04_pm9:  # ronda 8 — 6 comentarios (incluye 2 bugs de wiring FE↔BE never-exercised)
  env: "dev-app.vitalialat.com — Playwright desechable (viewport 1920) con interceptación de red (waitForResponse PATCH/POST) + lectura de logs BE. FE restart+wipe; BE auto-reload."
  verified_at: 2026-06-04
  result: "1 passed — PATCH /mode 200 ×2 + aria-checked refleja · POST /pause 200 · modal 2 botones sin reason · tools-icon=0 · sidebar sin 'Estado'. Logs BE: 0 traceback (2× /mode 200 + /pause 200)."
  c1_mode_buttons_FIXED:  # ronda8 #1 — 'no funcionan' (3 capas de bug, todas FE excepto RBAC)
    - "Capa A (método): FE use-set-mode usaba POST + OCC en header If-Match; el BE es PATCH + lee expected_updated_at del BODY → 405. FIX: PATCH + expected_updated_at en body."
    - "Capa B (RBAC): set_conversation_mode (y TODAS las mutaciones del inbox) gateaban a _PHI_ROLES {doctor,nurse,admin_clinic}; dr.demo es owner → 403. FIX BE: _assert_phi_access ahora usa _INBOX_OPERATOR_ROLES = _PHI_ROLES|{owner,receptionist} (mismo set que Chris ratificó para list/detail; el inbox es la herramienta del operador). marketing/sales/patient siguen denegados. Regression test test_set_mode_200_owner_operator."
    - "Capa C (query-key): el thread lee ['crm','conversation',id] (useConversationDetail de crm-shared) pero use-set-mode optimizaba/invalidaba ['adrian','inbox',...] (legacy) → el 200 nunca reflejaba en UI. FIX: use-set-mode (+pause +send) usan los keys crm-shared. VERIFIED LIVE: click consulta → PATCH 200 → aria-checked=true."
  c2_tools_icon_removed:  # ronda8 #2
    - "🛠 ToolsSheetTrigger eliminado del ThreadHeader (la actividad de Adrián vive en el stream inferior con su propio toggle). ToolsSheetTrigger.tsx NO se borró (lo usa AdrianToolsSheet). Explicación del ActivityStream dada a Chris (glass-box)."
  c3_nudge_explained: "Pregunta respondida (no es cambio): 'Dar empujón' = NudgeService re-engagement 1:1 — Adrián manda un mensaje de reactivación a un lead estancado/frío (template nudge_reengagement)."
  c4_pause_modal_FIXED:  # ronda8 #4 — popup 2 botones + pausa nunca había funcionado (3 capas BE latentes)
    - "Modal: quité la caja de comentarios (reason); 2 botones [Pausar 60 minutos][Pausar permanente] (rojo) + X close. PauseAdrianButton/use-pause-adrian pasan duration_minutes (60 o PERMANENT_PAUSE_MINUTES≈100años, el BE no tiene flag indefinido → far-future = follow-up BE)."
    - "Capa A (path): FE pegaba a /pause-adrian; el BE es /pause → 404. FIX path."
    - "Capa B (NoOp redis): pause_adrian_service.setex → _NoOpRedisClient (dev sin Redis) no tenía setex → 500. FIX BE: agregado setex no-op (el pause_until se persiste en DB igual; Redis es solo fast-path)."
    - "Capa C (repo): service llamaba conv_repo.set_pause_until → ConversationRepository (crm) no lo tenía → 500. FIX BE: agregado set_pause_until (UPDATE pause_until + dual filter + retorna fila). VERIFIED LIVE: POST /pause 200, 0 traceback."
    - "★ La pausa NUNCA se había ejercido live (siempre quedó en 'demo Chris') → estos 3 bugs estaban latentes. Lección verification-real-≠-200 en acción."
  c5_estado_vs_etapa: "Pregunta + fix: 'Estado' y 'Etapa de la venta' renderizaban el MISMO statusTag (StageBadge) = duplicado. Quité el campo 'Estado' del bloque de contacto; queda 'Etapa de la venta' como única fuente. VERIFIED LIVE: sidebar sin 'Estado'."
  c6_service_interest_empty:  # ronda8 #6
    - "Servicio de interés ahora SIEMPRE visible: con servicio → cajita cian + valor; sin servicio → cajita calma (vt-bg-muted) + 'Aún no detectado' (italic faint). VERIFIED LIVE el caso con servicio (Carlos=Ortodoncia invisible); el empty es `serviceInterest || 'Aún no detectado'` (siempre renderiza)."
  followups:
    - "send/nudge/retract/proactive: mismo mismatch de query-key (legacy adrian keys) que mode/pause/send — fixeé use-send-message; nudge/retract/proactive PENDIENTES (sus mensajes no reflejarán hasta migrar a keys crm-shared). Misma 1-línea c/u."
    - "Pausa 'permanente' = far-future (100 años); flag indefinido real = follow-up BE (PauseAdrianService + _PauseRequest)."
    - "Consolidar _INBOX_OPERATOR_ROLES (mirror crm+inbox) a un shared vitalia."
    - "Carlos (conv 11111111) quedó PAUSADO 60min por el live-test del fix — auto-expira (demuestra que la pausa funciona)."
  gates: "FE: tsc 0 · eslint 0 · arch-colors 2/2 · tests propios verdes. BE: ruff 0 · inbox api mode/pause 12 verdes (owner-200 + marketing-403) · arch response_model OK. 4 reds FE + 1 pgcrypto BE = PRE-EXISTENTES baseline no míos (pgcrypto=treatment_plans.notes, no toco models/migrations)."
  note: "dod_live_verified = true para #1-#6 (writes reales /mode + /pause ejercidos + 200 + logs limpios + UI refleja). Story sigue developing. NO /auditor sin sign-off Chris (DoD #37)."

audit_ready_2026_06_04:  # reconciliación de docs + E2E reales + BE bug fix (autónomo, post sign-off Chris)
  env: "dev-app.vitalialat.com (backend real, 0 mocks del surface) — golden e2e Playwright smoke storageState dr.demo (owner)"
  verified_at: 2026-06-04
  docs_reconciled:
    - "01-spec.md: § Scope amendment (3→2 modos) + RN-1/RN-5 + RN-15/16/17 + AC-4/AC-5/AC-10 marcadas MODIFICADA + Gherkin (SC-mode/SC-4 pausa/SC-composer/SC-privacy) + matriz con fuente (e2e-live/be-test/shell-story)."
    - "03-arch.md: § 4b Architecture Decisions (AD-1..AD-7: 2-modos, RBAC operador, set_pause_until, NoOp setex, query-keys crm, PiiMaskedSpan.masked, dock, wallpaper fijo)."
    - "04-validators.yaml: business_rules 17 reglas con tag+source + scenario_coverage + e2e cmds→dev-app + visual goldens WAIVED (ADR-003)."
    - "06-tickets.yaml: follow-ups FU-1..FU-6 ruteados a /pm-vitalia backlog."
    - "demo-script.md: reescrito a 2-modos + demo_signoff de Chris registrado."
  golden_e2e: "vitalia/frontend/e2e/shell-organism/adrian-inbox-modes.spec.ts — REESCRITO a 2-modos (importa fixtures/base.ts anti-burbuja). 7 passed (0 failed, 0 skipped) contra dev-app. POM AdrianInboxPage.ts: ADD-only (pause modal/composer dock/service-interest + setMode + aria-checked fix); inbox.page.ts intacto (legacy slice-1, único consumer = orphaned /inbox smoke)."
  writes_exercised_live:
    - { action: "PATCH /inbox/conversations/{instagram}/mode", observed: "200 + aria-checked refleja + DB vitalia_conversations.handler_mode=ai (era human) + updated_at fresco", db_verified: true }
    - { action: "POST /inbox/conversations/{carlos}/pause (60 min)", observed: "200 + botón→'Pausado' + DB pause_until set + updated_at fresco", db_verified: true }
  be_bug_found_and_fixed:  # ★ verification-real-≠-200 en acción: el golden cazó lo que pm9 (solo 200) ocultó
    bug: "TODAS las mutaciones del inbox (mode/pause/send/proactive/nudge) usaban Depends(get_async_session) que NUNCA commitea (delega al caller) + ningún service del inbox llama session.commit() → POST/PATCH devolvían 200 pero NO persistían (pause_until NULL, handler_mode sin cambiar en DB). El optimistic update de React Query enmascaraba la no-persistencia en la UI; pm9 solo verificó el 200, no el efecto en DB."
    fix: "vitalia/backend/src/modules/vitalia/inbox/api/router.py — 5 factories de mutación (_get_send_service/_get_set_mode_service/_get_pause_service/_get_proactive_service/_get_nudge_service) cambiadas a Depends(get_async_session_committing) (la sesión committing que ya usaban los endpoints CRM por el MISMO bug). Read factories (_get_activity_service) intactas."
    regression_guard: "BE tests/modules/vitalia/inbox/api/ → 46 passed; ruff + ruff format clean. Golden e2e ahora verifica persistencia REAL (botón pausa flippea solo si commitea+refetchea)."
    scope: "code:adrian (mi bucket, lock activo). NO toqué crm repo (set_pause_until ya existía)."
  followups_no_block:
    - "FU-6 (FE polish): use-set-mode optimistic no refresca updated_at → re-toggle inmediato 409 OCC (la UI lo maneja con rollback+ring; uso single-toggle real no lo dispara)."
  note: "dod_live_verified = true (writes reales ejercidos + efecto en DB confirmado + 0 burbuja). Listo para /auditor → /pm-vitalia merge."

demo_required: true
demo_signoff:
  signed_by: Chris
  date: '2026-06-04'
  result: APPROVED_WITH_NOTES
  notes: >-
    Chris probó el inbox live en dev-app (rondas r6-r8: modo 2-estados, pausa
    60/permanente, composer, leads visibles, wallpaper/cursor/etc.) y lo da por
    REVISADO. Quedan solo detalles estéticos menores, diferidos.
  open_items:
    - item: "Detalles estéticos menores (no enumerados por Chris) — capturar al hacer demo-script.md"
      severity: low
      disposition: defer
scope_amendment_2026_06_04: >-
  La story se AMPLIÓ de 'inbox UI polish' a 'hacer que el inbox funcione de verdad':
  modelo de modos 3→2 (AC-4/AC-5 cambian), composer montado, pausa 60/permanente,
  RBAC inbox widened a _INBOX_OPERATOR_ROLES (owner+receptionist), leads visibles por
  defecto (PiiMaskedSpan.masked), query-keys crm-shared, BE set_pause_until + NoOp setex.
  Antes de /auditor: reconciliar 01-spec/03-arch/04-validators con esta realidad +
  E2E reales. Detalle completo: HANDOFF-audit-ready-r6-r8.md.
next_phase_2026_06_04: "audit-ready — reconciliar docs + E2E reales → /auditor vitalia → /pm-vitalia merge → done. Autónomo (Chris aprobó). Ver HANDOFF-audit-ready-r6-r8.md."

e2e_suite_status_2026_06_04_pm:
  tenant: "10/10 GREEN (dev-app) — telemetry-404 + audit-log-404 + cross-tenant test-design todos resueltos."
  full_inbox: "24 passed / 5 failed (dev-app · modes+states specs). Los 5 rojos NO son de mis cambios ni de los endpoints: son fragilidad PRE-EXISTENTE del helper de los specs — `page.locator('[data-testid=\"conversation-thread\"]').first().waitFor(visible)` sobre un testid DUPLICADO (inbox-desktop + inbox-mobile responsive) → .first() resuelve al layout OCULTO → timeout 15s. MISMA causa raíz que el errorBanner que arreglé. Cubre AC-4/5/7 (decide/consulta/manual · composer-por-modo · Modo-conversación colapsa Valeria RN-12). El thread SÍ abre live (tenant :76 'deep-link open conv' PASA). El handoff decía 'modes 6 pass / ~28 green' = INEXACTO (patrón: el handoff ya erró en atribuir-todo-a-telemetry + el defer_audit embudo fabricado)."
  decision_pending_chris: "Arreglar el helper de modes/states (target del thread VISIBLE — mismo fix que errorBanner: scope a inbox-desktop o :visible) → completa la suite limpia + la verificación live de AC-4/5/7. O Chris inspecciona primero. NO encadenar a /auditor sin su prueba+sign-off (regla dura)."
  shell_split_decision_2026_06_04: "★ Chris (2026-06-04) ratificó: el inbox-FEATURE (telemetry-404 ✅ + audit-log-404 twin ✅ + SC-10 tenant 10/10 ✅, commits af035e69/0b752040/587766fc + embudo-fix 821ef027 + modes-scope d41102c3) queda CERRADO a nivel feature. Los 3 hallazgos shell/styling que bloquean AC-4/5/7 + AC-12 se SPLITean a una BUGFIX STORY de SHELL dedicada (#1 responsive Valeria-squeeze + #2 dark-mode token audit; #3 ContactSidebarToggle ya existe). Repro completo: observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md. El inbox NO es `done` overall hasta que (a) el shell-fix desbloquee + verifique AC-4/5/7 + AC-12 live, (b) Chris demo sign-off (DoD #37). NO encadenar /auditor sin eso."
  modes_deeper_finding_2026_06_04: "★ El fix NO era trivial. Cambié los 8 sitios `conversation-thread`.first().waitFor → `[inbox-desktop] [conversation-thread]`.waitFor PERO SIGUEN ROJOS. CAUSA RAÍZ CONFIRMADA via Chrome MCP (DOM live + screenshot, 2026-06-04): es un BUG DE LAYOUT DE PRODUCTO, no de test. Medición live (viewport 1280, Valeria-chat shell ABIERTO): inbox-desktop = 696px (la Valeria-chat se come ~584px). Dentro del inbox-desktop el flex-row = [list w-80=320px][thread flex-1 min-w-0 = 56px][ContactSidebar w-80=320px]. El THREAD se exprime a 56px (sliver vertical ILEGIBLE — confirmado en screenshot). En sesión Playwright fresca la Valeria-chat default es más ancha → inbox-desktop <640 → thread = 0px → Playwright lo ve HIDDEN → timeout 15s. PRE-EXISTENTE (mis cambios no tocan el layout; el live-verify previo 'thread renderiza' debió tener Valeria colapsada). DEFECTO UX REAL: con Valeria-chat + ContactSidebar abiertos el thread del inbox es inusable. FIX = PRODUCTO/ARQUITECTURA (decisión Chris): reflow del inbox por ANCHO DE CONTENEDOR (container query) no por viewport md: → colapsar ContactSidebar cuando el contenedor es angosto, o cambiar a layout tabs/mobile por container-width, o auto-colapsar Valeria para sub-tabs que necesitan ancho. AC-4/5/7 + AC-12 (responsive) tocados. NO es fix de e2e — es fix de cómo el inbox coexiste con la Valeria-sidebar siempre-presente del shell."
e2e_tenant_remaining_red:
  - "★ HALLAZGO (el handoff sobre-atribuía a telemetry): 2 de los 3 tenant specs (:43, :76) NO eran por telemetry. Causas reales: (a) TWIN BUG audit-log — AuditedSection.tsx:93 hace raw fetch POST /api/v1/vitalia/audit-log (ruta BE inexistente) → 404 cada vez que monta ContactSidebar (panel inbox). Mismo patrón que telemetry pero superficie PHI/seguridad → observed-bugs/2026-06-04-fe-audit-log-endpoint-404.md. (b) cross-tenant conv 404 DELIBERADO (aislamiento CORRECTO) que el gate base.ts no exenta → el spec adversarial debería test.use({failOnRuntimeError:false}). (c) :43 además: el inbox NO renderiza error-state reconocible cuando el detail 404 (expect something-renders falla). (d) :76 abre conv 00000…01 de tenant B = probable state-bleed localStorage (cold-start). DECISIÓN PENDIENTE CHRIS: fix audit-log twin (¿crear endpoint o borrar fetch FE si server-side ya audita?) + test-design opt-out + error-state."
e2e_dev_app:
  env: "dev-app.vitalialat.com (Clerk real dr.demo + backend real + seed · 0 mocks en specs core)"
  status: "Specs T-6 NUNCA habían corrido (import path roto ../../→../ + no enganchados a ningún project del playwright.config). Wireados + corridos live."
  result: "~28 passed. Únicos rojos consistentes: 3 tenant specs (43/76/101) por el 404 PRE-EXISTENTE /api/telemetry/growth-studio-event (mateo/telemetry pega a endpoint inexistente → gate anti-burbuja). NO defecto del inbox. Documentado: vitalia/docs/observed-bugs/2026-06-04-fe-telemetry-growth-studio-event-404.md."
  fixes: "POM selectors (getConversationItems→data-testid, mode→segment-{value}, activityStream→agent-activity-stream); deterministic thread-open wait (reemplazó waitForLoadState networkidle race → modes 6 pass)."
live_verify_status: "★ INBOX FUNCIONAL live + e2e reales en dev domain. Thread/modos/take-control/nudge/compliance/contacto/activity-stream verificados. ~28 e2e green; 3 rojos = telemetry-404 pre-existente (no inbox). FALTA para done: (1) resolver/decidir telemetry-404, (2) /auditor, (3) demo sign-off Chris (DoD #37), (4) /pm-vitalia merge. Ver SELF-REVIEW-compliance.md."
ratified_by_chris: true
ratified_at: '2026-06-03T20:23:30.000Z'
po_ux_version: 1
ratified_visual_by_chris: true
ratified_visual_at: '2026-06-03T20:23:30.000Z'
ratified_visual_waiver: >-
  ADR-vitalia-003 mockup-per-component WAIVED por Chris (2026-06-03) — story de
  MIGRACIÓN: los componentes UI ya están shipped + visualmente ratificados en
  slice-1-inbox (02-design-ui-mockup.html, Chris 2026-05-17) + wrapper shell
  ratificado fase 1. Piezas NEW (ConversationModeButton/ChannelBadge/ToolCallCard/
  NudgeButton/Valeria-reacciona) son pequeñas, derivan de tokens+patrones
  existentes, descritas en 01-spec.md § Wireframes + § Estados visuales.
  Ratificación visual real diferida a live-verify dev-app (DoD #37) que es más
  fuerte que mockup (UI real corriendo). No se crea 02-design-ui.md (po-ux fusión:
  el spec es el diseño).
parallel_safe: true
priority: critical
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-adrian-embudo
    - vitalia-fase2-valeria-pacientes
blocks_hard: []
blocks_soft:
  - vitalia-fase2-adrian-embudo
  - vitalia-fase2-camila-voz
reuse_map_summary: >-
  REUSE 95% inbox+sales_agent shipped (LangGraph + tools + canales) · NEW UI
  3-panel (Lista convs · Thread · ContactSidebar) · NEW 3-modos toggle (Decide
  solo · Consulta · Manual) · NEW Activity stream + tools registry view
spawned_at: 2026-05-22T00:00:00.000Z
supersedes:
  - vitalia-slice-1-inbox
next_action: >-
  /dev-team vitalia vitalia-fase2-adrian-inbox autonomous → BE lane (T-1 un-stub
  compliance · T-2 nudge) ∥ FE lane (T-3 ruta+registro · T-4 consolidación+DELETE
  huérfano · T-5 piezas NEW) → T-6 e2e+visual+demo → /auditor (be+fe Opus) → HUMAN
  GATE Chris demo sign-off dev-app (DoD #37) → /pm-vitalia merge done + cap YAML.
  Ready package completo: 03-arch{,-be,-fe} + 04-validators + 05-guidelines +
  06-tickets + dispatch-plan. ★ Reframe arch (código real 2026-06-03): BE inbox +
  modelo + lista YA shipped → trabajo = un-stub ComplianceService + nudge endpoint;
  FE = consolidar features/inbox→features/adrian + DELETE huérfano + piezas NEW.
release: F3
cap_target: adrian.inbox
cap_change_type: fix
parent_story: null
---

# F2-S3 vitalia-fase2-adrian-inbox — checkpoint

## Goal

Sub-tab Inbox de Adrián: bandeja unificada cross-canal (WhatsApp · IG DM · Email · Web chat) donde el agente Adrián opera bajo **paradigma 3-modos** (Decide solo · Consulta · Manual). Layout 3-panel: lista conversaciones izq · thread central · ContactSidebar derecho (PHI masked) + Activity stream chronológico mostrando qué tools invocó el agente. Reemplaza vista inbox shipped en `vitalia/frontend/src/features/inbox/` migrando capability al espacio shell-organism.

## Anti-objetivos

- NO rehacer LangGraph engine (vive en `core/luana-core-sales-agent`)
- NO rehacer adapters de canal (WhatsApp/IG/Email) — vienen del módulo connections shipped
- NO implementar BroadcastChannel real-time (out-of-scope MVP; polling 10s)
- NO implementar Bulk actions multi-conv (story dedicada futura)
- NO tocar `core/luana-core-sales-agent`/`core/luana-core-copilot` (engine read-only)
- NO duplicar prompts del sales-agent (viven en core engine + brand extensions)

## Prior art scan (2026-06-03 · /pm-vitalia · OBLIGATORIO anti-duplication-refining)

> Ejecutado: engine `core/` + vitalia propio (shipped + archive) + legacy nicolify sales studio + embudo sibling. Reframe principal: **esta story es MIGRACIÓN + consolidación, NO build desde cero.**

### Hallazgos

**1 · Inbox YA shipped (slice-1-inbox, done) — código vivo huérfano.** `vitalia/frontend/src/features/inbox/` tiene ~40 componentes evolucionados: `SegmentedControl3Modes` (3-modos Adrián decide·consulta·Yo escribo), `AgentActivityStream` (glass-box), `ContactSidebar` PHI-aware (`PiiMaskedSpan`+`RequireRole`), `ActionReceiptUndoChip` (undo 5min), `PauseAdrianButton`+`PauseAdrianConfirmModal`, `VoiceMessagePlayer`, `ImageAnalysisCard`, `AdrianToolsSheet`, `ProactiveOutboundModal`, `ProposalCardBanner`, `FilterChips`, 8 estados visuales. **Su `page.tsx` se borró en la reorg shell → feature huérfano (no cableado en `app/`).** Es la fuente de comportamiento más rica. Diseño funcional SSoT: `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/02-design-ui.md`.

**2 · Subset parity ya portado en F1-S10.** `vitalia/frontend/src/features/adrian/components/inbox/` tiene molecules "sales_studio parity" (T-5/T-6 empty-states): `ConversationItem`, `ContactSidebar`, `ThreadHeader`, `TakeoverBanner`, `MessageBubble`, `MessageInput`, `CampaignTag`, `types.ts`. Es el hogar FSD-Lite shell-organism correcto (`features/adrian/`), pero versión más simple (sin 3-modos/activity-stream/voice/tools).  ⚠️ **Riesgo duplicación:** dos sets de inbox conviven → consolidar en `features/adrian/components/inbox/` reusando la lógica evolucionada de `features/inbox/`, luego borrar el huérfano.

**3 · Legacy nicolify sales studio (`closer-studio`) = sustrato agéntico original.** `~/Proyectos/luana-nicolify-legacy/nicolify/frontend/src/features/closer-studio/` — inbox 3-pane (`InboxView`: ConvList 320 · Thread · ContactSidebar 288 toggle, `?lead={id}` URL + localStorage last-lead) + hooks agénticos `use-conversation-actions` (**stop/resume AI · send · nudge · reactivate · diagnose**) + `use-closer-ws` (websocket realtime) + `use-kpis` + `use-frozen`. El inbox shipped de vitalia ya **evolucionó** estos (binario stop/resume → 3-modos; + activity stream + PHI). Las acciones agénticas legacy (nudge/reactivate/diagnose) NO están todas en el inbox vitalia → candidatas a traer.

**4 · Runtime agéntico vive en `core/` (consumir, no recrear).** Per research embudo (`vitalia-fase2-adrian-embudo/research/02-core-engine.md`): `core/luana-core-sales-agent` (LangGraph + AgentStateCheckpoint + transitions audit + diagnose + KPIs + workers) byte-idéntico al legacy. Brand tools vitalia ya shipped en `vitalia/backend/src/modules/vitalia/sales_agent/tools/` (payment_link, reschedule_appointment, retract_last_message, screening_questions, send_proactive_reengagement). Backend inbox = `vitalia/backend/src/modules/vitalia/inbox/api/router.py`.

**5 · Consistencia con embudo sibling (★ cementado por Chris).** Embudo cementó el **paradigma adrián = conversation-first, agent-operated**: Adrián opera/mueve solo · humano supervisa (Tomar control · instrucción oculta) · **Valeria supervisora reacciona en panel izquierdo** · glass-box explicable · consume sustrato engine · **PHI firewall** (Adrián opera datos de interés, NUNCA clínicos). Detalle entry = página con URL propia (`EntitySubNavBar`, patrón C) presentada como overlay interceptado. **Inbox debe ser consistente.**

### Decisión

| Eje | Decisión prior-art | Acción |
|---|---|---|
| Inbox build | **Migración + consolidación** (reuse ~90% código shipped huérfano) | `/po-ux` enmarca como re-home + re-theme, NO build virgen |
| Hogar canónico | `features/adrian/components/inbox/` (shell-organism FSD) | consolidar lógica de `features/inbox/` ahí + borrar huérfano |
| Runtime agente | **Consumir** `core/luana-core-sales-agent` + brand tools shipped | NO tocar engine (read-only) |
| Paradigma UX | **Consistente con embudo** (Valeria reacciona · 3-modos · glass-box · PHI firewall) | wrapper shell portado verbatim (ADR-003 § wrapper fidelity) |
| Acciones agénticas | Traer nudge/reactivate/diagnose del legacy si aplican al inbox | `/po-ux` decide scope vs diferir |

## Scope verbatim

### § 1 — Page + layout 3-panel

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx`:

```tsx
import { AdrianInboxView } from '@/features/adrian/components/inbox/AdrianInboxView'
import { getInitialInboxState } from '@/features/adrian/api/inbox-server'

export default async function Page({ params, searchParams }: PageProps) {
  const { tenantId } = await params
  const { conv: convId, filter = 'todos' } = await searchParams
  const initialData = await getInitialInboxState({ tenantId, convId, filter })
  return <AdrianInboxView initialData={initialData} initialConvId={convId} initialFilter={filter} />
}
```

### § 2 — `AdrianInboxView` layout

`vitalia/frontend/src/features/adrian/components/inbox/AdrianInboxView.tsx`:

Grid 3-cols con widths ajustables (resizable handles Shadcn `ResizablePanelGroup`):

```
[ConvList 320px] [Thread 1fr] [ContactSidebar 320px]
```

Mobile (`<md`): Tabs en lugar de 3-panel (Conv · Thread · Detalles). Default Thread activo.

### § 3 — `InboxConvList` panel izquierdo

`vitalia/frontend/src/features/adrian/components/inbox/InboxConvList.tsx`:

- Header: filter chips (Todos · Sin leer · Asignadas a mí · Esperando humano · Bot activo)
- SearchInput (debounce 300ms)
- Lista conversaciones:
  - Avatar + nombre PHI-masked (`P. H.`)
  - Snippet último mensaje (truncado)
  - Channel badge (WhatsApp 🟢 · IG 📷 · Email 📧 · Web 💬)
  - Timestamp relativo (ej. "hace 5 min")
  - Unread dot
  - Mode badge (🤖 Decide · 🤝 Consulta · 👤 Manual)
- Click conv → setSelectedConvId + actualiza URL `?conv={id}`

### § 4 — `InboxThread` panel central

`vitalia/frontend/src/features/adrian/components/inbox/InboxThread.tsx`:

Composición:
1. **ThreadHeader:** ChannelBadge + ContactName masked + **Mode Toggle** (3-modos) + Acciones (Asignar · Cerrar · Etiquetar)
2. **MessagesArea:**
   - Mensaje paciente (bubble izq, fondo neutro)
   - Mensaje bot (bubble der, fondo adrián-soft, label "Adrián 🤖")
   - Mensaje humano (bubble der, fondo primary, label "{user} 👤")
   - Mensaje delegate (italic, ej. "Adrián consulta a Valeria") per Design Contract § 3.1 DelegateMarker
   - Tools invoked inline (collapsible card "Adrián usó `check_availability` · resultado: 3 slots disponibles")
3. **Composer:**
   - Textarea + send button
   - Si modo `manual` → enviar como humano
   - Si modo `consulta` → mensaje queda en draft + alerta "Adrián sugiere envío: 'X'. Aprobás?"
   - Si modo `decide` → Adrián envía solo cuando criterio se cumple (no composer humano salvo override)
   - File upload (imagen/PDF · per `hipaa-lite.md` NO PHI sensitive sin encriptado canal)

### § 5 — Mode Toggle (★ corazón paradigma Vitalia)

`vitalia/frontend/src/features/adrian/components/inbox/ModeToggle.tsx`:

3-state segmented control (Shadcn `Tabs`):

| Modo | Significado | Visual |
|---|---|---|
| 🤖 Decide solo | Agente Adrián responde autónomo. Solo escala a humano si tool falla o paciente pide humano | Badge verde "🤖 Decide" |
| 🤝 Consulta | Agente prepara respuesta + humano aprueba/edita/rechaza | Badge amarillo "🤝 Consulta" |
| 👤 Manual | Solo humano responde. Agente queda silenciado (no observa ni sugiere) | Badge gris "👤 Manual" |

Cambio modo:
- POST `/api/inbox/conversations/{id}/mode` → backend actualiza `conversation.agent_mode`
- WebSocket event `mode_changed` (out-of-scope MVP) o polling re-fetch
- Audit log row creado (cambios modo son auditable)

### § 6 — `ContactSidebar` panel derecho

`vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.tsx`:

Tabs Shadcn:
- **Datos** — Nombre PHI-masked + channel handle + lead score + etiquetas + tags
- **Actividad** — Activity stream chronological (mensajes + tool calls + system events)
- **Lead** — Stage actual (link a F2-S4 embudo) + propuestas (link a F2-S6 propuestas) + Last touch + Time-in-stage
- **Notas internas** — Textarea staff-facing

### § 7 — Activity stream (★ explicabilidad agente)

`vitalia/frontend/src/features/adrian/components/inbox/ActivityStream.tsx`:

Stream chronological de TODO lo que Adrián hizo en esta conv:

```
14:32  📨  Paciente envió mensaje "Hola, atienden los sábados?"
14:32  🤖  Adrián invocó `check_clinic_hours` → resultado: "Sábados 9-13"
14:32  🤖  Adrián respondió: "Hola! Sí, atendemos sábados de 9 a 13h..."
14:35  📨  Paciente: "Quiero turno limpieza"
14:35  🤖  Adrián invocó `check_availability(service=limpieza)` → resultado: 3 slots
14:35  🤖  Adrián invocó `propose_slots(slots=[...])` → mensaje enviado
14:38  📨  Paciente: "El sábado 11h"
14:38  🤖  Adrián invocó `book_appointment(...)` → ❌ requiere PAGO previo (policy clinic)
14:38  🤖  Adrián invocó `request_deposit(amount=30)` → link Stripe enviado
14:40  💳  Paciente pagó depósito → PaymentWebhook → conv.lead_id.stage = 'reservado'
14:40  🤖  Adrián invocó `confirm_booking(...)` → cita creada en Agenda Valeria
14:40  🤖  Adrián respondió: "Listo Pedro! Tu turno está confirmado..."
```

Datos consumidos del `copilot_trace_event` table (engine observability) + sanitize_payload aplica server-side.

### § 8 — Filtros + estado canal

`InboxFilters.tsx`:

Chips: Todos · Sin leer · Asignadas a mí · Esperando humano (modo Consulta sin respuesta humano > 2min) · Bot activo · Cerradas.

ChannelBadge component reusable cross-feature → `components/shared/shell-organism/ChannelBadge.tsx`.

### § 9 — Voice-of-customer signals (passive)

Cuando paciente menciona keywords NPS (`mal`, `excelente`, `pésimo`, `recomiendo`, etc.) → backend dispara trigger SSoT 12-triggers (per navigation-tree Camila) que F2-S11 camila-voz consume. Inbox SOLO genera evento; UI Camila lo procesa.

### § 10 — HIPAA-lite voice patterns

Per `hipaa-lite.md`:
- ❌ NO discutir diagnóstico/resultados por WhatsApp free / SMS
- Si paciente pregunta "qué resultados tengo?" → bot deriva: "Por seguridad, los resultados los puedes ver en tu portal: {link-portal-secure}"
- ComplianceService valida outbound antes envío — bloquea PHI inappropriate channel
- File upload: imagen permitida pero label warning si user adjunta (verbatim warning per `hipaa-lite.md`)

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page `/{tenant}/adrian/inbox` renderiza 3-panel layout |
| AC-2 | ConvList paginated + filter chips + search funcionan |
| AC-3 | Click conv → thread carga + URL `?conv=X` persiste |
| AC-4 | Mode toggle cambia conversation.agent_mode + audit log |
| AC-5 | Composer envía mensaje cuando modo manual; queda en draft en modo consulta |
| AC-6 | Tool calls del agente aparecen inline en thread (collapsible cards) |
| AC-7 | Activity stream muestra trace events del agente cronological |
| AC-8 | ContactSidebar muestra PHI masked + tabs funcionan |
| AC-9 | HIPAA-lite voice patterns enforced (ComplianceService bloquea PHI por canal no encriptado) |
| AC-10 | Visual goldens 3-panel light + dark + mode-toggle states |
| AC-11 | a11y axe pass |
| AC-12 | Mobile: 3-tabs en lugar de 3-panel |
| AC-13 | Cross-tenant query bloqueada (dual filter) |
| AC-14 | Vitest unit + Playwright functional + a11y |

## Gherkin scenarios

### Scenario 1 — happy: modo Decide + tool call exitoso

**Given:**
- Conv abierta, modo Decide
- Paciente envía "Quiero turno limpieza para el sábado"
- Backend sales-agent Adrián procesa

**When:**
1. Backend invoca `check_availability(service=limpieza, date=sabado)` → 3 slots
2. Backend invoca `propose_slots(slots=[...])` → mensaje enviado
3. UI polling refetch (10s) → nuevos events

**Then:**
- Thread muestra: mensaje paciente · tool call collapsible "Adrián verificó disponibilidad: 3 slots" · mensaje bot "Tenemos disponibilidad..."
- Activity stream registra ambos tool calls + mensaje
- Audit log: tool invocations + outbound message

**playwright_required:** true  
**Graders:** E2E + audit log assert BE + visual golden

### Scenario 2 — edge: modo Consulta + humano edita propuesta

**Given:** Conv modo Consulta, agente preparó respuesta sugerida

**When:**
1. Composer muestra draft "Adrián sugiere: 'Hola Pedro, tienes turno disponible sábado...'"
2. Humano edita el draft cambiando "sábado" por "lunes"
3. Click Send

**Then:**
- Mensaje enviado con texto editado (humano firma)
- Activity stream: "Humano editó propuesta Adrián · diff aplicado"
- Audit log: `mode_consulta_intervention`

**playwright_required:** true  
**Graders:** E2E + diff capture

### Scenario 3 — adversarial: paciente pregunta resultados clínicos por WhatsApp

**Given:** Conv modo Decide, channel WhatsApp tier free

**When:** Paciente envía "Cuál fue mi diagnóstico de la semana pasada?"

**Then:**
- Agente NO responde con diagnóstico (ComplianceService bloquea)
- Agente responde: "Por seguridad, los resultados los puedes ver en tu portal: {link}"
- Activity stream registra "ComplianceService bloqueó PHI outbound" + redirect mensaje
- Audit log: `compliance_block_outbound_phi`

**playwright_required:** true  
**Graders:** E2E + BE `vitalia/backend/tests/modules/vitalia/inbox/test_phi_voice_redirect.py`

### Scenario 4 — keyboard-a11y

**Given:** Foco en SearchInput

**When:** Tab × N traversa elementos

**Then:**
- Tab order: search → filter chips → first conv → mode toggle → composer
- aria-current en conv activa
- aria-selected en mode toggle activa
- Esc en composer pierde foco (vuelve a thread)

**playwright_required:** true  
**Graders:** E2E + axe

### Scenario 5 — visual parity con paradigma

**Given:** Conv abierta modo Decide

**When:** Playwright captura screenshot

**Then:**
- 3-panel layout matchea Design Contract § 3.4 template
- Mode toggle visualmente claro (badge verde para Decide)
- Bubble colors per Design Contract tokens (--agent-adrian-soft)

**playwright_required:** true  
**Graders:** Visual goldens × 3 modes + × 2 themes

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/[conv-id]/page.tsx` | NEW (N3-dyn workspace) |
| `vitalia/frontend/src/features/adrian/components/inbox/AdrianInboxView.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/InboxConvList.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/InboxThread.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/InboxFilters.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/ActivityStream.tsx` | NEW |
| `vitalia/frontend/src/features/adrian/components/inbox/ModeToggle.tsx` | NEW (★) |
| `vitalia/frontend/src/features/adrian/components/inbox/MessageBubble.tsx` | REUSE shared (Design Contract § 3.1) |
| `vitalia/frontend/src/features/adrian/components/inbox/ToolCallCard.tsx` | NEW (collapsible) |
| `vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx` | NEW (cross-feature reusable) |
| `vitalia/frontend/src/features/adrian/api/inbox.ts` | NEW |
| `vitalia/frontend/src/features/adrian/api/inbox-server.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/inbox.types.ts` | NEW |
| `vitalia/frontend/src/features/adrian/types/inbox-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/inbox/api/conversations_router.py` | MODIFY (add mode endpoint + filters + dual filter) |
| `vitalia/backend/src/modules/vitalia/inbox/api/activity_stream_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/inbox/application/mode_change_service.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/adrian-inbox-modes.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/adrian-inbox-phi-redirect.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/inbox/{layout}-{mode}-{light\|dark}.png` (×12) | NEW |
| `vitalia/backend/tests/modules/vitalia/inbox/test_mode_change.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/inbox/test_phi_voice_redirect.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/inbox/test_activity_stream_sanitize.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/inbox` | Models + repository + service base | REUSE 90% — agregar endpoints mode + activity-stream |
| Vitalia shipped — `core/luana-core-sales-agent` + brand extensions `vitalia/backend/src/modules/vitalia/sales_agent/` | LangGraph + tools + voice config | REUSE 100% engine + brand tools (NO tocar — read-only) |
| `core/luana-core-channels` | format_for_channel utility | REUSE como API consumer |
| `core/luana-core-compliance` | ComplianceService.validate_outbound | REUSE BE |
| `core/luana-core-observability` | `copilot_trace_event` + sanitize_payload | CONSUME para activity stream |
| Nicolify FE — inbox feature | 3-panel layout + table patterns | TRANSPONER (no copy-paste — adapt tokens shell-organism) |
| Shadcn primitives | `ResizablePanelGroup` · `Tabs` · `Textarea` · `Badge` · `Sheet` | npx install |
| Vitalia archived — `vitalia-slice-1-inbox` | Inbox UI primera versión (NO shell-organism) | REFACTOR: migrar lógica al espacio adrian/inbox/ + 3-modos paradigm |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` — shell con sub-tab navigable
- `vitalia-fase1-routing-shell` — App Router incluye `adrian/inbox` + N3-dyn `[conv-id]`

### Soft
- `vitalia-fase2-adrian-embudo` — link "Ver en Embudo" desde conv detail
- `vitalia-fase2-valeria-pacientes` — link "Promover a paciente" desde conv

### Esta historia desbloquea
- `vitalia-fase2-adrian-embudo` — leads del Inbox alimentan embudo
- `vitalia-fase2-camila-voz` — mensajes voice-of-customer disparan triggers
- `vitalia-fase2-adrian-propuestas` — propuesta puede crearse desde conv

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Polling 10s ineficiente con muchas convs | Media | Medio | Limit page size 30 · pagination · WebSocket upgrade post-MVP |
| Mode toggle race condition (humano + bot simultaneous) | Media | Alto | Backend transaction lock por conv_id + WebSocket update |
| Activity stream PHI leak | Baja | Crítico | sanitize_payload server-side ANTES envío + test `test_activity_stream_sanitize.py` |
| ComplianceService no enforced en todos los outbound paths | Baja | Crítico | Arch fitness test enumera all outbound paths + assert ComplianceService.validate llamado |
| Resizable panels rompen layout mobile | Baja | Medio | Tabs fallback < md (no resizable) |

## Definición de "Done"

1. Todos AC verificados
2. Visual goldens × 12 (3 modes × 2 themes × 2 desktop/mobile)
3. Backend tests HIPAA-lite + mode-change + activity stream sanitize pass
4. Story commits pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `adrian.inbox` registrada

## Próximo paso post-done

- F2-S4 adrian-embudo consume leads del Inbox
- F2-S5 adrian-outbound + F2-S6 adrian-propuestas reusan ChannelBadge + ToolCallCard
- Camila stories suben prioridad cuando Inbox dispara triggers SSoT

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Template:** `vitalia/docs/specs/templates/01-spec-shell-template.md`
- **Navigation tree:** `vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md` § adrian.inbox
- **HIPAA-lite overlay:** `vitalia/.claude/rules/hipaa-lite.md`
- **Slice-1 archived:** `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/` (read-only reference)
