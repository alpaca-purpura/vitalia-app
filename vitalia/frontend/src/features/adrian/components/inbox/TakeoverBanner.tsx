// cap: sales_agent.inbox-handler-mode-occ
// story-origin: vitalia-fase1-s10-TBD
/**
 * TakeoverBanner — banner amarillo indicador de usuario en control.
 * F1-S10 vitalia-fase1-empty-states — T-6
 *
 * Visible SOLO cuando handlerState="human" (renderizado condicionalmente por padre).
 * Layout:
 *   - Background gradient amber-100 + border-left 3px amber-500 + border amber-500/50
 *   - Icon ⚡ grande a la izquierda
 *   - Texto central: título bold + meta muted text-xs
 *   - Botón "🤖 Devolver a Adrián" a la derecha
 *
 * Mockup parity: adrian-inbox-placeholder.html .takeover-banner styles
 *
 * Client Component — botón "🤖 Devolver a Adrián" tiene callback onClick.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only (amber-* tokens).
 * Spanish neutro — spec § 10 verbatim (copy ratificado Chris batch 2).
 *
 * F2 anchor: onReturnControl disparará Zustand action
 *   `setHandlerOverride(leadId, 'bot')` en features/adrian/store/inbox-store.ts.
 *   F1: local useState callback desde InboxPlaceholder.
 *
 * spec_anchor: 03-arch.md § 3.3 + CONTEXT-BRIEF § 6 + 06-tickets.yaml T-6
 * downstream-regression-na: brand-local vitalia inbox; no cross-brand consumers
 */

"use client";

import { cn } from "@/lib/utils";

export interface TakeoverBannerProps {
  /**
   * Callback — devuelve el control a Adrián (B→A).
   * Spec § 10 verbatim: "🤖 Devolver a Adrián".
   * F2-S3: Zustand setHandlerOverride(leadId, 'bot').
   */
  onReturnControl: () => void;
  className?: string;
}

/**
 * TakeoverBanner — indicator that user has taken control.
 * Renders inside thread area BELOW the ThreadHeader when handlerState="human".
 * Client Component.
 */
export function TakeoverBanner({
  onReturnControl,
  className,
}: TakeoverBannerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Tienes el control de esta conversación · Adrián pausado"
      className={cn(
        // Container — mockup parity gradient + border-l-[3px]
        "mx-3 my-2 flex items-center gap-3 rounded-md border border-amber-500/50 p-3",
        "border-l-[3px] border-l-amber-500",
        "bg-gradient-to-r from-amber-100/60 to-amber-50/30",
        "dark:from-amber-900/20 dark:to-amber-900/10",
        className,
      )}
    >
      {/* Icon ⚡ */}
      <span aria-hidden="true" className="shrink-0 text-xl text-amber-600">
        ⚡
      </span>

      {/* Text block */}
      <div className="min-w-0 flex-1">
        {/* Title — spec § 10 verbatim */}
        <p className="text-xs font-semibold text-foreground">
          Tienes el control · Adrián pausado en esta conversación
        </p>
        {/* Meta — spec § 10 verbatim */}
        <p className="mt-0.5 text-[10px] text-muted-foreground">
          El modo global &apos;🤖 Adrián decide&apos; no se altera · solo aquí ·
          puedes devolver el control cuando quieras
        </p>
      </div>

      {/* Botón "🤖 Devolver a Adrián" — spec § 10 verbatim */}
      <button
        type="button"
        onClick={onReturnControl}
        aria-label="Devolver el control a Adrián en esta conversación"
        className={cn(
          "shrink-0 inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition-opacity",
          "bg-amber-500 dark:bg-amber-600 text-white hover:opacity-90 cursor-pointer border border-amber-500 dark:border-amber-600",
        )}
      >
        🤖 Devolver a Adrián
      </button>
    </div>
  );
}
