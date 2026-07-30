// cap: platform.topbar-global
// story-origin: TBD
"use client";

/**
 * TopBar — top navigation bar for Vitalia app shell.
 *
 * Height: 56px (h-14).
 * Contains: page title + user menu + copilot toggle.
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useClerk, useUser } from "@clerk/nextjs";
import { cn } from "@/lib/cn";

export interface TopBarProps {
  /** Page title to display */
  title?: string;
  /** Whether to show the copilot toggle button */
  showCopilot?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Application top bar with page title, user menu, and copilot toggle.
 */
export function TopBar({ title, showCopilot = true, className }: TopBarProps) {
  const { user } = useUser();
  const { signOut } = useClerk();
  const router = useRouter();

  const handleSignOut = useCallback(async () => {
    await signOut(() => router.push("/sign-in"));
  }, [router, signOut]);

  const initials = user
    ? [user.firstName, user.lastName]
        .filter(Boolean)
        .map((n) => n![0])
        .join("")
        .toUpperCase() || "U"
    : "U";

  return (
    <header
      className={cn(
        "flex items-center justify-between h-14 px-4 shrink-0",
        "vt-bg-surface border-b vt-border",
        className,
      )}
      role="banner"
      aria-label="Barra superior"
    >
      {/* Page title */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Skip to content link for accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:px-2 focus:py-1 focus:text-xs focus:rounded"
          tabIndex={0}
        >
          Ir al contenido principal
        </a>

        {title && (
          <h1
            className="text-base font-semibold vt-text truncate"
            aria-label={`Página: ${title}`}
          >
            {title}
          </h1>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Copilot toggle */}
        {showCopilot && (
          <button
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium",
              "rounded-[var(--radius-pill)]",
              "vt-text-cian vt-border-cian border",
              "hover:vt-bg-cian-8",
              "focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
              "transition-colors",
            )}
            aria-label="Abrir copiloto de IA"
            onClick={() => {
              const url = new URL(window.location.href);
              url.searchParams.set("copilot", "open");
              window.history.pushState({}, "", url.toString());
            }}
          >
            <span aria-hidden="true">✦</span>
            <span>Copiloto</span>
          </button>
        )}

        {/* User menu */}
        <div className="relative group">
          <button
            className={cn(
              "flex items-center justify-center w-8 h-8 rounded-full",
              "vt-bg-azul-marino vt-text-white text-xs font-bold",
              "hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
              "transition-opacity",
            )}
            aria-label={`Menú de usuario: ${user?.firstName ?? "Usuario"}`}
            aria-haspopup="menu"
          >
            {initials}
          </button>

          {/* Dropdown menu */}
          <div
            className={cn(
              "absolute right-0 mt-1 w-48 py-1",
              "vt-bg-surface vt-border border",
              "rounded-[var(--radius-lg)] shadow-lg",
              "invisible opacity-0 group-hover:visible group-hover:opacity-100",
              "transition-all duration-150",
              "z-50",
            )}
            role="menu"
            aria-label="Opciones de usuario"
          >
            {user && (
              <div className="px-3 py-2 border-b vt-border">
                <p className="text-xs font-medium vt-text truncate">
                  {user.firstName} {user.lastName}
                </p>
                <p className="text-xs vt-text-muted truncate">
                  {user.primaryEmailAddress?.emailAddress}
                </p>
              </div>
            )}
            <button
              role="menuitem"
              onClick={() => void handleSignOut()}
              className={cn(
                "w-full text-left px-3 py-2 text-sm",
                "vt-text-muted",
                "hover:vt-bg-muted hover:vt-text",
                "focus-visible:outline-none focus-visible:vt-bg-muted",
                "transition-colors",
              )}
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
