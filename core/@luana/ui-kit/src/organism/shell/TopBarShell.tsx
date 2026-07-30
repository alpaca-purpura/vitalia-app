// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * TopBarShell — brand-agnostic global top bar (T-K2 port of TopBarGlobal).
 *
 * Slots replace the brand-coupled internals:
 *   - logoSlot           (was <LogoMark/>) — brand logo element.
 *   - rightClusterSlot   (was [ThemeToggle][TenantSwitcher]) — brand cluster.
 *   - onBurgerClick      optional override; default opens the mobile drawer via
 *                        the injected shell store (D5: independent mobileDrawer
 *                        slice — NOT the desktop supervisorOpen slice; that was
 *                        the Bug #2 root cause).
 *
 * variant="skeleton" keeps a store-free, inert burger placeholder so this bar
 * can render OUTSIDE the ssr:false boundary without touching the persist
 * middleware (Bug #1 PROD REAL). The interactive variant subscribes the store.
 *
 * data-testid preserved EXACT (vitalia e2e contract 68+7): topbar-global,
 * topbar-hamburger.
 */

import { Menu } from "lucide-react";
import { Button } from "../../button";
import type { ReactNode } from "react";
import type { ShellLayoutLabels, ShellStore } from "./types";

export type TopBarVariant = "interactive" | "skeleton";

export interface TopBarShellProps {
  /** REQUIRED for the burger aria-label (brand passes supervisor identity). */
  supervisorName: string;
  /** brand logo element (full + mark responsive handled by the slot itself). */
  logoSlot: ReactNode;
  /** brand right cluster (theme toggle + tenant switcher, etc.). */
  rightClusterSlot: ReactNode;
  /** injected shell store (interactive variant only). */
  useShellStore?: ShellStore;
  /** override the burger behaviour; default = open mobile drawer. */
  onBurgerClick?: () => void;
  labels?: Partial<ShellLayoutLabels>;
  className?: string;
  /** @default "interactive" */
  variant?: TopBarVariant;
}

const BASE_CLASSES = [
  "h-12",
  "border-b border-border",
  "bg-background",
  "flex items-center justify-between",
  "px-5",
  "relative z-50",
];

function classOf(extra?: string): string {
  return [...BASE_CLASSES, extra].filter(Boolean).join(" ");
}

// ─── Interactive (store-subscribed) ──────────────────────────────────────────
function TopBarShellInteractive({
  supervisorName,
  logoSlot,
  rightClusterSlot,
  useShellStore,
  onBurgerClick,
  labels,
  className,
}: Omit<TopBarShellProps, "variant">) {
  // useShellStore is required for the interactive variant; guard for type safety.
  const store = useShellStore;
  const mobileDrawerOpen = store ? store((s) => s.mobileDrawerOpen) : false;
  const setMobileDrawerOpen = store ? store((s) => s.setMobileDrawerOpen) : undefined;

  const handleBurger = () => {
    if (onBurgerClick) {
      onBurgerClick();
      return;
    }
    // D5: mobile drawer has its own independent slice (NOT supervisorOpen).
    setMobileDrawerOpen?.(true);
  };

  const openLabel = labels?.openSupervisor ?? `Abrir panel ${supervisorName}`;
  const closeLabel = labels?.collapseSupervisor ?? `Cerrar panel ${supervisorName}`;

  return (
    <header role="banner" data-testid="topbar-global" className={classOf(className)}>
      <div className="flex items-center gap-2 md:gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={handleBurger}
          aria-label={mobileDrawerOpen ? closeLabel : openLabel}
          aria-expanded={mobileDrawerOpen}
          data-testid="topbar-hamburger"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </Button>
        {logoSlot}
      </div>
      <div className="flex items-center gap-2">{rightClusterSlot}</div>
    </header>
  );
}

// ─── Skeleton (store-FREE) ───────────────────────────────────────────────────
function TopBarShellSkeleton({
  supervisorName,
  logoSlot,
  rightClusterSlot,
  labels,
  className,
}: Pick<
  TopBarShellProps,
  "supervisorName" | "logoSlot" | "rightClusterSlot" | "labels" | "className"
>) {
  const openLabel = labels?.openSupervisor ?? `Abrir panel ${supervisorName}`;
  return (
    <header
      role="banner"
      data-testid="topbar-global"
      data-shell-variant="skeleton"
      className={classOf(className)}
    >
      <div className="flex items-center gap-2 md:gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label={openLabel}
          aria-disabled="true"
          tabIndex={-1}
          data-testid="topbar-hamburger"
          data-skeleton="true"
          onClick={undefined}
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </Button>
        {logoSlot}
      </div>
      <div className="flex items-center gap-2">{rightClusterSlot}</div>
    </header>
  );
}

export function TopBarShell({ variant = "interactive", ...rest }: TopBarShellProps) {
  if (variant === "skeleton") {
    return (
      <TopBarShellSkeleton
        supervisorName={rest.supervisorName}
        logoSlot={rest.logoSlot}
        rightClusterSlot={rest.rightClusterSlot}
        labels={rest.labels}
        className={rest.className}
      />
    );
  }
  return <TopBarShellInteractive {...rest} />;
}
