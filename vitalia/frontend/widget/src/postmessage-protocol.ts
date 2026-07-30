/**
 * postmessage-protocol.ts — Typed postMessage SSoT for the Vitalia booking widget.
 *
 * Widget (iframe) → parent window communication.
 * Per 03-arch-fe.md § 9.2 + D11 (origin validation + signed patient JWT).
 *
 * Usage:
 *   postMessageToParent({ type: "widget:loaded" }, parentOrigin);
 *   const validate = createOriginValidator(["https://clinic.vitalia.health"]);
 *   if (!validate(event.origin)) return; // origin spoofing prevention
 */

// ── Typed event union ─────────────────────────────────────────────────────────

/**
 * WidgetMessage — all postMessage events emitted by the iframe widget to the parent.
 * Parent listens via window.addEventListener("message", handler).
 */
export type WidgetMessage =
  | { type: "widget:resize"; height: number }
  | { type: "widget:loaded" }
  | { type: "widget:booking-confirmed"; booking_id: string }
  | { type: "widget:payment-redirect"; url: string }
  | { type: "widget:error"; message: string };

// ── Helper: send message to parent ───────────────────────────────────────────

/**
 * Send a typed WidgetMessage to the parent frame.
 *
 * @param message - Typed WidgetMessage payload
 * @param targetOrigin - Parent origin (use specific origin in production, "*" for dev/test)
 */
export function postMessageToParent(message: WidgetMessage, targetOrigin: string): void {
  window.parent.postMessage(message, targetOrigin);
}

// ── Origin validator factory ──────────────────────────────────────────────────

/**
 * createOriginValidator — factory that returns an origin check function.
 * Used to prevent postMessage spoofing (D11 iframe widget origin spoofing mitigation).
 *
 * Security invariants:
 * - Wildcard "*" in allowedOrigins = accept all origins (development/embed-agnostic only)
 * - Exact string match only (no prefix/suffix matching to prevent subdomain spoofing)
 * - Empty string, "null", and other non-https values are blocked by default
 *
 * @param allowedOrigins - Array of exact origin strings ("https://..." or "*")
 * @returns Function (origin: string) => boolean
 *
 * @example
 * const validate = createOriginValidator(["https://clinic.vitalia.health"]);
 * window.addEventListener("message", (e) => {
 *   if (!validate(e.origin)) return; // block spoofed messages
 *   handleMessage(e.data as WidgetMessage);
 * });
 */
export function createOriginValidator(
  allowedOrigins: readonly string[]
): (origin: string) => boolean {
  const allowAll = allowedOrigins.includes("*");

  return function validateOrigin(origin: string): boolean {
    // Reject empty or null-origin (sandboxed iframes)
    if (!origin || origin === "null") return false;

    if (allowAll) return true;

    return allowedOrigins.includes(origin);
  };
}

// ── Incoming message type guard ───────────────────────────────────────────────

/**
 * isWidgetMessage — runtime type guard for inbound messages.
 * Use when parent embeds the widget and listens for events.
 */
export function isWidgetMessage(data: unknown): data is WidgetMessage {
  if (typeof data !== "object" || data === null) return false;
  const msg = data as Record<string, unknown>;
  if (typeof msg["type"] !== "string") return false;

  switch (msg["type"]) {
    case "widget:loaded":
      return true;
    case "widget:resize":
      return typeof msg["height"] === "number";
    case "widget:booking-confirmed":
      return typeof msg["booking_id"] === "string";
    case "widget:payment-redirect":
      return typeof msg["url"] === "string";
    case "widget:error":
      return typeof msg["message"] === "string";
    default:
      return false;
  }
}
