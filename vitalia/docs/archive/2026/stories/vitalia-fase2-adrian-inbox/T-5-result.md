# T-5 result — FE piezas NEW + ensamblaje 3-pane

**State:** pushed (GREEN) · **Commits:** `811f01b6` (piezas) + `bb0fc3ce` (wiring CONN) en `wip/vitalia`.

## Qué se hizo

- **AdrianInboxView** (M): skeleton → **3-pane real** (`ResizablePanelGroup`: ConversationListPanel | InboxThread | ContactSidebar), 100% del lienzo (RN-11, sin max-width), hidrata de SSR initialData, fallback tabs mobile.
- **ConversationModeButton** (NEW ★ — el botón que pediste): "Modo conversación" colapsa Valeria vía `useShellStore.setValeriaState('collapsed')` + **recuerda el estado previo** (rail/full) en `inbox-store.priorValeriaState` para restaurar (RN-12 / SC-5). aria-pressed refleja colapso. Renderizado en AdrianInboxView.
- **NudgeButton** (NEW — SC-6): consume `POST /nudge` (T-2) vía `use-nudge`, confirm inline, copy en `INBOX_COPY.nudge`. **Cableado en ThreadHeader** (barra de acciones).
- **ToolCallCard** (NEW): card colapsable de tool-call. **Cableado en ActivityStream** para `kind==='tool_call'` (summary→resultSummary, payload_redacted→toolName/payload). (El modelo de mensaje no lleva tool-data; vive en el trace/activity stream.)
- **useValeriaReaccion** (NEW): hook básico — al abrir conv deriva contexto + acciones sugeridas para el panel de Valeria. Consumido en AdrianInboxView.

## Gates (hub, GREEN)

- tsc 0 · eslint 0 · vitest **465/465** (63 files) · arch fitness **171/171** (incl. no-hardcoded-strings ahora cubre las piezas NEW vía INBOX_COPY.nudge).

## Anti-isla (CONN)

Las 4 piezas NEW + el hook están **renderizadas/consumidas** (ConversationModeButton + useValeriaReaccion en AdrianInboxView; NudgeButton en ThreadHeader; ToolCallCard en ActivityStream). Cero islas.

## Notas

El builder corrió in-place + stalleó cerca del budget; el orchestrator cerró los fixes mecánicos (hex→token `var(--agent-adrian)`, mock typing useShellStore, copy NudgeButton→INBOX_COPY, eslint dirs) + el wiring CONN. Excluí del commit el `RecuperarPlaceholder` + el delta de `index.ts` (work de la sesión paralela adrian-embudo).

## Pendiente

- **T-6:** e2e (base.ts anti-burbuja: pageerror/console/response/Next-overlay) + visual goldens 3-pane (light/dark/modo-conversación) + a11y axe + **demo-script.md** (para tu demo, DoD #37).

## Skills consulted

| Skill / Rule | Status |
|---|---|
| frontend-expert · vitalia-design-system | ✅ |
| frontend-fsd.md · tenant-isolation.md · spanish-text.md | ✅ |
