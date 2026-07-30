// cap: adrian.inbox
// story-origin: TBD
"use client";
/**
 * FilterChips.tsx — Filter chip bar for the conversation list.
 *
 * Chip groups per 01-spec-extract.md § 4:
 *   Primary (always visible):
 *     [✕ Todas] [WhatsApp] [Instagram] [Email]
 *     [Activa] [Esperando depósito] [NPS pendiente] [Cerradas]
 *     [🔴 Adrián pide ayuda] [📎 Audio/imagen sin abrir]
 *   Collapsible under "Más filtros ▼":
 *     Stage (Etapa), Modo Adrián, Período
 *
 * Single-active per dimension: channel, status, stage, mode, period are mutually-exclusive
 * per group. helpNeeded + unreadMedia are boolean toggles.
 * Clicking ✕ Todas resets all filters.
 *
 * Props are controlled (value/onChange) — URL state managed by ConversationListPanel.
 *
 * "use client" required for useState (expanded toggle).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { cn } from "@/lib/cn";
import { getChannelMeta } from "@/lib/channels/channel-meta";
import { SocialLogo } from "@/components/shared/channels/SocialLogo";
import { INBOX_COPY } from "../../lib/copy";
import type {
  InboxChannelFilter,
  InboxStatusFilter,
  InboxStageFilter,
  InboxModeFilter,
  InboxPeriodFilter,
} from "../../lib/url-state";

/** Full filter state shape (mirrors InboxUrlState minus `lead` and `search`) */
export interface FilterChipsValue {
  channel: InboxChannelFilter | null;
  status: InboxStatusFilter | null;
  stage: InboxStageFilter | null;
  mode: InboxModeFilter | null;
  period: InboxPeriodFilter | null;
  helpNeeded: boolean | null;
  unreadMedia: boolean | null;
}

interface FilterChipsProps {
  value: FilterChipsValue;
  onChange: (next: FilterChipsValue) => void;
  className?: string;
}

const EMPTY_FILTERS: FilterChipsValue = {
  channel: null,
  status: null,
  stage: null,
  mode: null,
  period: null,
  helpNeeded: null,
  unreadMedia: null,
};

/** Generic chip button.
 *  When `channel` is set, the chip wears its channel's soft brand color
 *  (channel-meta SSoT) instead of the neutral primary/surface palette, with a
 *  brand-colored ring as the pressed state (UI-AUDIT-2026-06-04 #8). */
function Chip({
  label,
  active,
  onClick,
  channel,
  className,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  /** Channel slug — colors the chip with its brand soft color when set. */
  channel?: string;
  className?: string;
}) {
  const channelClasses = channel
    ? cn(
        getChannelMeta(channel).colorClass,
        active
          ? "ring-2 ring-inset ring-current font-semibold"
          : "border-transparent",
      )
    : active
      ? "vt-bg-primary vt-text-primary-foreground vt-border-primary"
      : "vt-bg-surface vt-text-muted vt-border";

  return (
    <button
      type="button"
      role="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full",
        "px-3 py-1 text-xs font-medium transition-colors",
        "border focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-offset-2 focus-visible:vt-outline-primary",
        channelClasses,
        "hover:opacity-90",
        className,
      )}
    >
      {/* Real social logo inside the channel chip (UI-AUDIT-2 #3/#4) */}
      {channel && <SocialLogo channel={channel} size={14} className="shrink-0" />}
      {label}
    </button>
  );
}

/**
 * FilterChips — horizontal chip bar with collapsible advanced filters.
 * Single-active per dimension (channel / status / stage / mode / period).
 * Boolean toggles for helpNeeded + unreadMedia.
 */
export function FilterChips({ value, onChange, className }: FilterChipsProps) {
  const [expanded, setExpanded] = useState(false);

  const hasAnyFilter =
    value.channel !== null ||
    value.status !== null ||
    value.stage !== null ||
    value.mode !== null ||
    value.period !== null ||
    value.helpNeeded !== null ||
    value.unreadMedia !== null;

  function toggle<K extends keyof FilterChipsValue>(
    key: K,
    val: FilterChipsValue[K],
  ) {
    onChange({
      ...value,
      [key]: value[key] === val ? null : val,
    });
  }

  return (
    <div
      className={cn("flex flex-col gap-1.5", className)}
      role="group"
      aria-label="Filtros de conversaciones"
    >
      {/* Single horizontally-scrollable channel line (UI-AUDIT-2 #4): swipe left/right
          to pick the social network. Status filters removed (too operational). */}
      <div
        className={cn(
          "flex items-center gap-1.5 overflow-x-auto px-3 pb-0.5",
          "[-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
        )}
        role="toolbar"
        aria-label="Filtrar por red social"
      >
        {/* Todas — reset all */}
        <Chip
          label={INBOX_COPY.filters.all}
          active={!hasAnyFilter}
          onClick={() => onChange(EMPTY_FILTERS)}
        />

        {/* Channel chips — real logo + brand soft color */}
        <Chip
          label={INBOX_COPY.filters.channels.whatsapp}
          active={value.channel === "whatsapp"}
          onClick={() => toggle("channel", "whatsapp")}
          channel="whatsapp"
        />
        <Chip
          label={INBOX_COPY.filters.channels.instagram}
          active={value.channel === "instagram"}
          onClick={() => toggle("channel", "instagram")}
          channel="instagram"
        />
        <Chip
          label={INBOX_COPY.filters.channels.telegram}
          active={value.channel === "telegram"}
          onClick={() => toggle("channel", "telegram")}
          channel="telegram"
        />
        <Chip
          label={INBOX_COPY.filters.channels.tiktok}
          active={value.channel === "tiktok"}
          onClick={() => toggle("channel", "tiktok")}
          channel="tiktok"
        />
        <Chip
          label={INBOX_COPY.filters.channels.facebook}
          active={value.channel === "facebook"}
          onClick={() => toggle("channel", "facebook")}
          channel="facebook"
        />
        <Chip
          label={INBOX_COPY.filters.channels.email}
          active={value.channel === "email"}
          onClick={() => toggle("channel", "email")}
          channel="email"
        />

        {/* Más filtros — at the end of the line */}
        <button
          type="button"
          onClick={() => setExpanded((x) => !x)}
          aria-expanded={expanded}
          aria-controls="advanced-filters"
          className={cn(
            "inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full",
            "px-3 py-1 text-xs font-medium vt-text-muted vt-border vt-bg-surface",
            "hover:opacity-90 transition-colors",
            "focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-offset-2 focus-visible:vt-outline-primary",
          )}
        >
          {expanded
            ? INBOX_COPY.filters.lessFilters
            : INBOX_COPY.filters.moreFilters}
          <span aria-hidden="true">{expanded ? "▲" : "▼"}</span>
        </button>
      </div>

      {/* Collapsible advanced filters (flags + stage + mode + period) */}
      {expanded && (
        <div id="advanced-filters" className="flex flex-col gap-1.5 px-3 pb-2">
          {/* Highlight flags */}
          <div className="flex flex-wrap gap-1.5">
            <Chip
              label={INBOX_COPY.filters.helpNeeded}
              active={value.helpNeeded === true}
              onClick={() =>
                onChange({
                  ...value,
                  helpNeeded: value.helpNeeded === true ? null : true,
                })
              }
            />
            <Chip
              label={INBOX_COPY.filters.unreadMedia}
              active={value.unreadMedia === true}
              onClick={() =>
                onChange({
                  ...value,
                  unreadMedia: value.unreadMedia === true ? null : true,
                })
              }
            />
          </div>

          {/* Stage filter */}
          <div className="flex flex-wrap gap-1.5">
            <span className="self-center text-xs font-medium vt-text-muted">
              {INBOX_COPY.filters.stage.label}:
            </span>
            <Chip
              label={INBOX_COPY.filters.stage.interested}
              active={value.stage === "interested"}
              onClick={() => toggle("stage", "interested")}
            />
            <Chip
              label={INBOX_COPY.filters.stage.considering}
              active={value.stage === "considering"}
              onClick={() => toggle("stage", "considering")}
            />
            <Chip
              label={INBOX_COPY.filters.stage.readyToBook}
              active={value.stage === "ready-to-book"}
              onClick={() => toggle("stage", "ready-to-book")}
            />
            <Chip
              label={INBOX_COPY.filters.stage.decidedNo}
              active={value.stage === "decided-no"}
              onClick={() => toggle("stage", "decided-no")}
            />
          </div>

          {/* Mode Adrián filter */}
          <div className="flex flex-wrap gap-1.5">
            <span className="self-center text-xs font-medium vt-text-muted">
              {INBOX_COPY.filters.mode.label}:
            </span>
            <Chip
              label={INBOX_COPY.filters.mode.adrianDecide}
              active={value.mode === "adrian-decide"}
              onClick={() => toggle("mode", "adrian-decide")}
            />
            <Chip
              label={INBOX_COPY.filters.mode.adrianConsulta}
              active={value.mode === "adrian-consulta"}
              onClick={() => toggle("mode", "adrian-consulta")}
            />
            <Chip
              label={INBOX_COPY.filters.mode.yoEscribo}
              active={value.mode === "yo-escribo"}
              onClick={() => toggle("mode", "yo-escribo")}
            />
          </div>

          {/* Period filter */}
          <div className="flex flex-wrap gap-1.5">
            <span className="self-center text-xs font-medium vt-text-muted">
              {INBOX_COPY.filters.period.label}:
            </span>
            <Chip
              label={INBOX_COPY.filters.period.today}
              active={value.period === "today"}
              onClick={() => toggle("period", "today")}
            />
            <Chip
              label={INBOX_COPY.filters.period.yesterday}
              active={value.period === "yesterday"}
              onClick={() => toggle("period", "yesterday")}
            />
            <Chip
              label={INBOX_COPY.filters.period.week}
              active={value.period === "week"}
              onClick={() => toggle("period", "week")}
            />
            <Chip
              label={INBOX_COPY.filters.period.month}
              active={value.period === "month"}
              onClick={() => toggle("period", "month")}
            />
          </div>
        </div>
      )}
    </div>
  );
}
