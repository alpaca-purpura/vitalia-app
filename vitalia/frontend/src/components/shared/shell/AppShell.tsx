// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
"use client";

/**
 * AppShell — main layout container for authenticated Vitalia pages.
 *
 * Layout structure:
 *   [Sidebar 240px] | [Main: [TopBar 56px] | [Content fill]]
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { useState } from "react";
import { cn } from "@/lib/cn";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import type { ReactNode } from "react";

export interface AppShellProps {
  /** Page content */
  children: ReactNode;
  /** Page title shown in TopBar */
  title?: string;
  /** Whether the CopilotRail is available on this page */
  showCopilot?: boolean;
  /** Additional CSS classes for the content area */
  contentClassName?: string;
}

/**
 * Root layout shell for Vitalia authenticated pages.
 * Sidebar + TopBar + main content area.
 */
export function AppShell({
  children,
  title,
  showCopilot = true,
  contentClassName,
}: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div
      className="flex h-screen overflow-hidden vt-bg-app"
      aria-label="Interfaz principal Vitalia"
    >
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
      />

      {/* Main column */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar title={title} showCopilot={showCopilot} />

        {/* Content area */}
        <main
          className={cn("flex-1 overflow-y-auto vt-bg-app", contentClassName)}
          id="main-content"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
