// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
"use client";

/**
 * Sidebar — navigation sidebar for Vitalia app shell.
 *
 * Width: 240px expanded / 64px collapsed.
 * Active nav item: vt-bg-cian-10 + vt-border-cian-l per design-system.md.
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/cn";

export interface NavItem {
  label: string;
  href: string;
  /** Icon element (e.g. from lucide-react or inline SVG) */
  icon?: React.ReactNode;
}

export interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
  /** Navigation items to render */
  navItems?: NavItem[];
}

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { label: "Inicio", href: "/dashboard" },
  { label: "Pacientes", href: "/dashboard/patients" },
  { label: "Agenda", href: "/dashboard/schedule" },
  { label: "Tratamientos", href: "/dashboard/treatments" },
  { label: "Pagos", href: "/dashboard/payments" },
  { label: "Copiloto", href: "/dashboard/copilot" },
];

/**
 * Sidebar navigation component.
 * Active state uses vt-bg-cian-10 + vt-border-cian-l classes (from globals.css).
 */
export function Sidebar({
  collapsed = false,
  onToggle,
  navItems = DEFAULT_NAV_ITEMS,
}: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex flex-col shrink-0 h-screen",
        "vt-bg-surface vt-border",
        "border-r",
        "transition-[width] duration-200 ease-in-out",
        collapsed ? "w-16" : "w-60",
      )}
      aria-label="Navegación principal"
      role="navigation"
    >
      {/* Logo area */}
      <div className="flex items-center h-14 px-4 shrink-0 border-b vt-border">
        <span
          className="font-bold text-lg vt-text-azul-marino truncate"
          aria-label="Vitalia"
        >
          {collapsed ? "V" : "Vitalia"}
        </span>
      </div>

      {/* Navigation */}
      <nav
        className="flex-1 overflow-y-auto py-4 px-2"
        aria-label="Menú principal"
      >
        <ul className="space-y-0.5" role="list">
          {navItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === item.href
                : pathname.startsWith(item.href);

            return (
              <li key={item.href} role="listitem">
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius)]",
                    "text-sm font-medium transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
                    "border-l-[3px] -ml-[1px]",
                    isActive
                      ? "vt-bg-cian-10 vt-text-azul-marino vt-border-cian-l"
                      : "vt-text-muted hover:vt-bg-muted hover:vt-text border-transparent",
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.icon && (
                    <span className="shrink-0 w-4 h-4" aria-hidden="true">
                      {item.icon}
                    </span>
                  )}
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <div className="px-2 pb-4 shrink-0">
        <button
          onClick={onToggle}
          className={cn(
            "w-full flex items-center justify-center py-2 px-3",
            "text-sm vt-text-muted",
            "rounded-[var(--radius)]",
            "hover:vt-bg-muted",
            "focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
            "transition-colors",
          )}
          aria-label={
            collapsed ? "Expandir barra lateral" : "Contraer barra lateral"
          }
          aria-expanded={!collapsed}
        >
          <span aria-hidden="true">{collapsed ? "→" : "←"}</span>
          {!collapsed && <span className="ml-2 text-xs">Contraer</span>}
        </button>
      </div>
    </aside>
  );
}
