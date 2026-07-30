// canon: design-system-canon.md §2.3 · story-origin: core-ds-foundation
"use client";

/**
 * EntityInfoCard.tsx — Canon §2.3 grid-friendly entity card (Opción B · @luana/ui-kit).
 *
 * Brand-agnostic card for entity grids (doctores, servicios, leads, ICPs, …). The
 * parent grid uses `grid auto-fill minmax(250px,1fr)`. Generalizes 3 brand sources:
 *   - vitalia StaffCard       → circular media, title + subtitle badge, metrics grid
 *   - nicolify IcpCard        → agent-color icon media, status chip
 *   - vitalia ReEngagementCard → declarative status color map (token-driven)
 *
 * Anatomy (Opción B):
 *   ┌─ agent-color TOP border accent (border-t-4, token-driven) ──────── ⋮ kebab ─┐
 *   │  [circular media]  title (truncate)                                          │
 *   │                    subtitle badge                                            │
 *   │  ┌──────────┬──────────┬──────────┐  ← metrics row, equal cols, centered     │
 *   │  │ value    │ value    │ value    │                                          │
 *   │  │ label    │ label    │ label    │                                          │
 *   │  └──────────┴──────────┴──────────┘                                          │
 *   │  · status chip (footer) ·                                                     │
 *   └──────────────────────────────────────────────────────────────────────────────┘
 *
 * The WHOLE card is clickable (role=button, tabIndex=0, Enter/Space activate) with
 * hover / focus-visible / selected states. The kebab ⋮ (ui-kit DropdownMenu) stops
 * propagation so its clicks never fire the card onClick.
 *
 * Token-driven accent: pass `accentClass` (a Tailwind border-color utility, e.g.
 * "border-t-agent-lisa") OR `accentVar` (a CSS var name, applied via inline style).
 * NEVER a hardcoded hex.
 *
 * Slot/prop driven + brand-agnostic. Strings default to Spanish neutro LatAm.
 */

import * as React from "react";
import { MoreVertical } from "lucide-react";

import { cn } from "@luana/format/utils";
import { Avatar, AvatarImage, AvatarFallback } from "./avatar";
import { Badge, type BadgeProps } from "./badge";
import { Skeleton } from "./skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";

// ── Types ───────────────────────────────────────────────────────────────────────

export interface EntityMetric {
  /** Short label shown under the value (e.g. "Pacientes"). */
  label: string;
  /** Value shown emphasized (string or number; format upstream). */
  value: React.ReactNode;
}

export interface EntityStatus {
  /** Status label (e.g. "Activo", "Borrador"). */
  label: string;
  /** Badge variant (maps to ui-kit Badge variants). */
  variant?: BadgeProps["variant"];
  /** Optional extra classes for the status chip (token-driven). */
  className?: string;
}

export interface EntityCardAction {
  /** Stable key for React + testid. */
  id: string;
  /** Menu item label. */
  label: string;
  /** Click handler — receives nothing; closure owns the entity. */
  onSelect: () => void;
  /** Optional leading icon. */
  icon?: React.ReactNode;
  /** Render a separator BEFORE this item. */
  separatorBefore?: boolean;
  /** Destructive styling (e.g. delete). */
  destructive?: boolean;
  disabled?: boolean;
}

export interface EntityInfoCardProps {
  /** Primary title (truncated). */
  title: string;
  /** Optional subtitle rendered as a Badge below the title. */
  subtitle?: string;
  /** Badge variant for the subtitle. */
  subtitleVariant?: BadgeProps["variant"];
  /** Image URL for the circular media (Avatar). Falls back to `initials`. */
  media?: string;
  /** Initials for the Avatar fallback (when no `media`). */
  initials?: string;
  /**
   * Agent-color icon node — alternative to media/initials (e.g. an emoji or icon).
   * Rendered inside the circular media slot with `accentClass` background context.
   */
  icon?: React.ReactNode;
  /**
   * Token-driven TOP-border accent class (e.g. "border-t-agent-lisa").
   * Applied alongside the structural `border-t-4`. NEVER a hex.
   */
  accentClass?: string;
  /**
   * Alternative: a CSS variable name (e.g. "--agent-lisa") applied to the top border
   * via inline style `borderTopColor: hsl(var(--agent-lisa))`. Use when no utility class exists.
   */
  accentVar?: string;
  /** Optional token-driven class for the circular media background (agent-soft, etc.). */
  mediaClass?: string;
  /** Metrics spread across the card width (equal columns, centered). */
  metrics?: EntityMetric[];
  /** Footer status chip. */
  status?: EntityStatus;
  /** Kebab menu actions. When empty/omitted, no kebab renders. */
  actions?: EntityCardAction[];
  /** Selected state (e.g. active in a workspace). */
  selected?: boolean;
  /** Disabled / inactive visual (dimmed). */
  inactive?: boolean;
  /** Whole-card click handler. Makes the card role=button + keyboard-activatable. */
  onClick?: () => void;
  /** Accessible label override (defaults to a Spanish-neutro label built from title). */
  ariaLabel?: string;
  /** Stable testid suffix; renders `entity-info-card-{testId}`. */
  testId?: string;
  className?: string;
  /**
   * C2-T4 · extension surface: optional footer slot for custom content (badge, CTA, etc.).
   * Rendered below the status chip. Composición sobre fork (ADR-016 §3).
   */
  footer?: React.ReactNode;
}

// ── Component ─────────────────────────────────────────────────────────────────────

/**
 * EntityInfoCard — Opción B grid-friendly entity card.
 * data-testid="entity-info-card-{testId}".
 */
export function EntityInfoCard({
  title,
  subtitle,
  subtitleVariant = "secondary",
  media,
  initials,
  icon,
  accentClass,
  accentVar,
  mediaClass,
  metrics,
  status,
  actions,
  selected = false,
  inactive = false,
  onClick,
  ariaLabel,
  testId,
  className,
  footer,
}: EntityInfoCardProps) {
  const interactive = typeof onClick === "function";
  const hasMetrics = Array.isArray(metrics) && metrics.length > 0;
  const hasActions = Array.isArray(actions) && actions.length > 0;

  const resolvedInitials = (initials ?? title.charAt(0) ?? "·").toUpperCase().slice(0, 2);
  const resolvedAriaLabel = ariaLabel ?? `Ver ${title}`;
  const idSuffix = testId ?? "item";

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!interactive) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick?.();
    }
  };

  return (
    <div
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onClick : undefined}
      onKeyDown={interactive ? handleKeyDown : undefined}
      aria-label={interactive ? resolvedAriaLabel : undefined}
      aria-pressed={interactive ? selected : undefined}
      data-testid={`entity-info-card-${idSuffix}`}
      data-selected={selected ? "true" : undefined}
      style={accentVar ? { borderTopColor: `hsl(var(${accentVar}))` } : undefined}
      className={cn(
        "group relative flex flex-col gap-3 rounded-xl border border-border bg-card p-4 text-card-foreground",
        "border-t-4", // structural top accent thickness — color via accentClass/accentVar
        accentClass,
        interactive && "cursor-pointer transition-all hover:border-border/80 hover:shadow-md",
        interactive &&
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        selected && "border-border ring-2 ring-ring ring-offset-1",
        inactive && "opacity-60",
        className,
      )}
    >
      {/* Kebab ⋮ — top-right, stops propagation so it never fires the card onClick */}
      {hasActions && (
        <div className="absolute right-2 top-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => e.stopPropagation()}
                aria-label="Acciones"
                data-testid={`entity-info-card-kebab-${idSuffix}`}
                className={cn(
                  "inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground",
                  "hover:bg-muted hover:text-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                )}
              >
                <MoreVertical className="h-4 w-4" aria-hidden="true" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              onClick={(e) => e.stopPropagation()}
            >
              {actions!.map((action) => (
                <React.Fragment key={action.id}>
                  {action.separatorBefore && <DropdownMenuSeparator />}
                  <DropdownMenuItem
                    disabled={action.disabled}
                    onSelect={() => action.onSelect()}
                    data-testid={`entity-info-card-action-${action.id}`}
                    className={cn(action.destructive && "text-destructive focus:text-destructive")}
                  >
                    {action.icon}
                    {action.label}
                  </DropdownMenuItem>
                </React.Fragment>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      {/* Media (circular) + title + subtitle */}
      <div className="flex items-start gap-3 pr-7">
        <Avatar className={cn("h-12 w-12", mediaClass)}>
          {media && <AvatarImage src={media} alt="" />}
          <AvatarFallback className={cn("text-sm font-bold", mediaClass)} aria-hidden="true">
            {icon ?? resolvedInitials}
          </AvatarFallback>
        </Avatar>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-foreground" title={title}>
            {title}
          </p>
          {subtitle && (
            <Badge
              variant={subtitleVariant}
              className="mt-1 max-w-full truncate text-xs"
              data-testid={`entity-info-card-subtitle-${idSuffix}`}
            >
              {subtitle}
            </Badge>
          )}
        </div>
      </div>

      {/* Metrics row — equal columns, centered, spread across the width */}
      {hasMetrics && (
        <dl
          className="grid gap-1 text-center"
          style={{ gridTemplateColumns: `repeat(${metrics!.length}, minmax(0, 1fr))` }}
          data-testid={`entity-info-card-metrics-${idSuffix}`}
        >
          {metrics!.map((metric, i) => (
            <div key={`${metric.label}-${i}`} className="space-y-0.5">
              <dd className="text-sm font-semibold text-foreground">{metric.value}</dd>
              <dt className="text-[10px] text-muted-foreground">{metric.label}</dt>
            </div>
          ))}
        </dl>
      )}

      {/* Footer status chip */}
      {status && (
        <div className="mt-auto flex items-center">
          <Badge
            variant={status.variant ?? "outline"}
            className={cn("text-xs", status.className)}
            data-testid={`entity-info-card-status-${idSuffix}`}
          >
            {status.label}
          </Badge>
        </div>
      )}

      {/* C2-T4 extension surface: footer slot — custom badge/CTA/content (composición, no fork) */}
      {footer != null && (
        <div
          data-testid={`entity-info-card-footer-${idSuffix}`}
          className="mt-auto"
        >
          {footer}
        </div>
      )}
    </div>
  );
}

// ── Skeleton ────────────────────────────────────────────────────────────────────

export interface EntityInfoCardSkeletonProps {
  /** Number of metric placeholder columns to render (default 3). */
  metrics?: number;
  className?: string;
}

/**
 * EntityInfoCardSkeleton — loading placeholder matching EntityInfoCard layout.
 */
export function EntityInfoCardSkeleton({
  metrics = 3,
  className,
}: EntityInfoCardSkeletonProps) {
  return (
    <div
      data-testid="entity-info-card-skeleton"
      aria-hidden="true"
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border border-t-4 bg-card p-4",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="min-w-0 flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: `repeat(${metrics}, minmax(0, 1fr))` }}
      >
        {Array.from({ length: metrics }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="mx-auto h-4 w-8" />
            <Skeleton className="mx-auto h-2 w-12" />
          </div>
        ))}
      </div>
      <Skeleton className="h-5 w-16" />
    </div>
  );
}

// ── Empty ───────────────────────────────────────────────────────────────────────

export interface EntityInfoCardEmptyProps {
  /** Headline (default Spanish neutro). */
  title?: string;
  /** Supporting text. */
  description?: string;
  /** Optional icon / illustration node. */
  icon?: React.ReactNode;
  /** Optional action slot (e.g. a "Crear" button). */
  action?: React.ReactNode;
  className?: string;
}

/**
 * EntityInfoCardEmpty — empty-state for an entity grid (no items yet).
 * Spans the full grid row when placed inside `grid auto-fill`.
 */
export function EntityInfoCardEmpty({
  title = "Sin elementos aún",
  description = "Cuando agregues elementos, aparecerán aquí.",
  icon,
  action,
  className,
}: EntityInfoCardEmptyProps) {
  return (
    <div
      data-testid="entity-info-card-empty"
      role="status"
      className={cn(
        "col-span-full flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card/50 p-8 text-center",
        className,
      )}
    >
      {icon && <div className="text-muted-foreground" aria-hidden="true">{icon}</div>}
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="max-w-sm text-xs text-muted-foreground">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
