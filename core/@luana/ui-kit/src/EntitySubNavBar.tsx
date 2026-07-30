// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
"use client";
/**
 * EntitySubNavBar.tsx — Canon N3 entity workspace navigation bar (@luana/ui-kit).
 *
 * Brand-agnostic third ribbon (N3) for entity list/detail workspaces. Full-bleed,
 * sticky, store-free. Supports a fixed root leaf + N dynamic content leaves +
 * an optional add-affordance.
 *
 * Layout (canon §2.1-§2.2):
 *   MASTER (entity=null):  [ {rootLabel} ] <-- root leaf active | placeholder
 *   DETAIL (entity set):   [ {rootLabel} ] (inactive peer) | {entity identity} | [leaves] | [+ add]
 *
 * The root (e.g. "ICPs") is the FIRST entry in the tablist as a special peer leaf —
 * same pill shape as content leaves, with a leading ‹ arrow that navigates back to
 * the master grid (rootHref).
 *
 * States:
 *   - entity=null (master/no-selection mode):
 *       Root leaf is ACTIVE (aria-selected=true). Only the root leaf renders.
 *       No content leaves, no add affordance. Optional placeholder text shown.
 *   - entity present (workspace mode):
 *       Root leaf is INACTIVE (same pill shape, clickable → rootHref navigation).
 *       Entity identity (avatar/icon + name) shown.
 *       Full leaves rendered (content leaves + add affordance).
 *
 * Accessibility (WAI-ARIA tablist pattern):
 *   - role="tablist" on <nav>
 *   - role="tab" + aria-selected + aria-current per leaf
 *   - Root leaf is included in the tablist; roving tabindex covers it too
 *   - Arrow key navigation (Left/Right/Home/End)
 *   - focus() called on programmatic focus changes
 *
 * Per-leaf color (avatarBgClass) MUST be a full static Tailwind class string
 * (JIT-safe — no template literals in class strings).
 *
 * Full-bleed N3 ribbon: sticky top, bg-card, border-bottom, radius:0 (NOT a rounded card).
 *
 * Named export (NO default).
 */

import { useRouter, usePathname } from "next/navigation";
import { useState, useRef, useCallback, type KeyboardEvent, type ReactNode } from "react";

import { cn } from "@luana/format/utils";

import { Avatar, AvatarFallback, AvatarImage } from "./avatar";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EntitySubNavLeaf {
  /** URL segment identifier — kebab-case (e.g., "datos", "buyer-a1b2") */
  id: string;
  /** Visible label */
  label: string;
  /** Full href (pre-built by the caller — includes tenantId + entityId) */
  href: string;
  /**
   * When true, renders as a special "+ add" affordance (visual distinction).
   */
  isAddAffordance?: boolean;
  /**
   * Optional emoji/text prefix rendered before the label.
   * MUST be a static string — not a dynamic icon component (JIT-safe).
   */
  prefixEmoji?: string;
  /**
   * When set, renders a colored avatar circle before the label (visual identity).
   * MUST be a full static Tailwind class string (JIT-safe — no template literals).
   */
  avatarBgClass?: string;
  /**
   * When true, renders a ★ star after the label (marks the primary leaf).
   * Only meaningful when avatarBgClass is also set.
   */
  isPrimary?: boolean;
  /**
   * Internal flag — set by the component for the root leaf (first in tablist).
   * Callers set the root via the rootHref/rootLabel props, NOT by adding a leaf here.
   */
  isRootLeaf?: boolean;
}

export interface EntitySubNavEntity {
  id: string;
  name: string;
  avatarUrl?: string | null;
  /**
   * Optional icon/emoji rendered in the entity identity section before the name.
   * Static string (JIT-safe).
   */
  icon?: string;
}

export interface EntitySubNavBarProps {
  /** Href for the root leaf (master grid navigation) */
  rootHref: string;
  /** Label for the root leaf (e.g., "ICPs") */
  rootLabel: string;
  /**
   * Stable id for the root leaf testid — used by e2e (entity-leaf-root).
   * Defaults to "root".
   */
  rootLeafId?: string;
  /** Entity descriptor — null = master/no-selection mode (root leaf active) */
  entity: EntitySubNavEntity | null;
  /**
   * Ordered list of leaf tabs for the DETAIL state (content leaves + add affordance).
   * NOT rendered in master mode (entity=null) — only the root leaf is shown.
   */
  leaves: EntitySubNavLeaf[];
  /** Active leaf id — null in master mode (root leaf is active instead) */
  activeLeaf: string | null;
  /**
   * Optional placeholder text shown in master mode (entity=null) in the identity slot.
   */
  placeholder?: string;
  /**
   * Callback fired when the add-affordance leaf (isAddAffordance=true) is clicked.
   * When provided, the affordance leaf calls this INSTEAD of router.push(href).
   * This allows the parent to trigger a mutation and then navigate programmatically.
   *
   * If not provided, add-affordance leaves behave like normal leaves (router.push).
   */
  onAddAffordance?: () => void;
  /**
   * Optional entity-identity selector (canon §6.3 — "cambiar sin volver").
   *
   * Workspace mode (entity set): when provided, this node renders in the
   * entity-identity slot INSTEAD of the static avatar+name block (e.g., an
   * EntityPicker). The slot owns its own a11y (EntityPicker already provides
   * combobox/listbox roles + keyboard nav); it is NOT a tab and does not
   * participate in the tablist roving tabindex.
   *
   * Absent → the static identity block renders verbatim (back-compat:
   * existing consumers render unchanged).
   * Master mode (entity=null) → the slot is NEVER rendered.
   */
  entityIdentitySlot?: ReactNode;
  /** Additional className for the wrapper */
  className?: string;
}

// ── LeafTabButton (sub-component — extracted to reduce cognitive complexity) ──

interface LeafTabButtonProps {
  leaf: EntitySubNavLeaf;
  idx: number;
  isActive: boolean;
  isFocused: boolean;
  isDisabled: boolean;
  tabRef: (el: HTMLButtonElement | null) => void;
  onLeafClick: (idx: number, isAdd: boolean, href: string) => void;
  onLeafFocus: (idx: number) => void;
}

function leafStateClass(isDisabled: boolean, isAdd: boolean, isActive: boolean): string {
  if (isDisabled) return "opacity-45 cursor-not-allowed";
  if (isAdd)
    return "border border-dashed border-border text-muted-foreground hover:border-primary hover:text-primary";
  if (isActive) return "font-medium bg-accent border border-border text-accent-foreground";
  return "text-muted-foreground hover:text-foreground hover:bg-muted/50";
}

const LEAF_BASE =
  "inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1";

function LeafTabButton({
  leaf,
  idx,
  isActive,
  isFocused,
  isDisabled,
  tabRef,
  onLeafClick,
  onLeafFocus,
}: LeafTabButtonProps) {
  const isAdd = leaf.isAddAffordance === true;
  const isRoot = leaf.isRootLeaf === true;
  // Testid: root leaf → "entity-leaf-root" (stable, e2e-safe)
  //         add affordance → "entity-leaf-add-affordance"
  //         regular leaf → "entity-leaf-{id}"
  const testId = isRoot
    ? "entity-leaf-root"
    : isAdd
      ? "entity-leaf-add-affordance"
      : `entity-leaf-${leaf.id}`;
  const tabIdx = isDisabled ? -1 : isFocused ? 0 : -1;
  const showPrefix = Boolean(leaf.prefixEmoji) && !isAdd && !isRoot;
  const showAvatar = Boolean(leaf.avatarBgClass) && !isAdd && !isRoot;
  const showStar = Boolean(leaf.isPrimary) && !isAdd && !isRoot;

  return (
    <button
      ref={tabRef}
      type="button"
      role="tab"
      aria-selected={isActive}
      aria-disabled={isDisabled || undefined}
      aria-current={isActive ? "page" : undefined}
      tabIndex={tabIdx}
      data-testid={testId}
      data-add-affordance={isAdd ? "true" : undefined}
      data-root-leaf={isRoot ? "true" : undefined}
      disabled={isDisabled}
      onClick={() => onLeafClick(idx, isAdd, leaf.href)}
      onFocus={() => onLeafFocus(idx)}
      className={cn(LEAF_BASE, leafStateClass(isDisabled, isAdd, isActive))}
    >
      {/* Root leaf gets the ‹ back-arrow affordance (navigates to master grid) */}
      {isRoot && (
        <span aria-hidden="true" className="text-muted-foreground">
          ‹
        </span>
      )}
      {showPrefix && <span aria-hidden="true">{leaf.prefixEmoji}</span>}
      {showAvatar && (
        <span
          className={cn(
            "w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0",
            leaf.avatarBgClass,
          )}
          aria-hidden="true"
        >
          {leaf.label.charAt(0).toUpperCase()}
        </span>
      )}
      {leaf.label}
      {showStar && (
        <span className="text-[10px] text-primary ml-0.5" aria-label="primario">
          ★
        </span>
      )}
    </button>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * EntitySubNavBar — sticky, full-bleed N3 entity workspace navigation bar.
 *
 * The root ({rootLabel}) is a peer leaf in the tablist (first entry) with a leading
 * ‹ arrow that navigates back to the master grid. In master mode (entity=null),
 * only the root leaf renders (active). In workspace mode (entity present), the root
 * leaf is inactive and the full leaf set renders alongside it.
 *
 * Entity identity (avatar/icon + name or placeholder) shown between the root leaf
 * and the content leaf tabs.
 */
export function EntitySubNavBar({
  rootHref,
  rootLabel,
  rootLeafId = "root",
  entity,
  leaves,
  activeLeaf,
  placeholder,
  onAddAffordance,
  entityIdentitySlot,
  className,
}: EntitySubNavBarProps) {
  const router = useRouter();
  // usePathname is consumed so the bar re-renders on soft nav between leaves.
  usePathname();
  const isMasterMode = entity === null;

  // Build the full tablist: [rootLeaf, ...contentLeaves]
  // In master mode, contentLeaves is empty (only root leaf shown, active).
  // In workspace mode, contentLeaves = leaves (content leaves + add affordance).
  const rootLeaf: EntitySubNavLeaf = {
    id: rootLeafId,
    label: rootLabel,
    href: rootHref,
    isRootLeaf: true,
  };
  const allTabs: EntitySubNavLeaf[] = isMasterMode ? [rootLeaf] : [rootLeaf, ...leaves];
  const totalTabs = allTabs.length;

  // In master mode: root leaf is active (index 0).
  // In workspace mode: active is the leaf matching activeLeaf (skip root at 0).
  const activeTabIdx = (() => {
    if (isMasterMode) return 0; // root leaf always active in master mode
    if (!activeLeaf) return 0; // root leaf active if no specific leaf
    const idx = allTabs.findIndex((l) => l.id === activeLeaf);
    return idx >= 0 ? idx : 0;
  })();

  const [focusedIdx, setFocusedIdx] = useState<number>(activeTabIdx);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Move focus to idx (circular wrap)
  const focusTab = useCallback(
    (idx: number) => {
      if (totalTabs === 0) return;
      const safeIdx = ((idx % totalTabs) + totalTabs) % totalTabs;
      setFocusedIdx(safeIdx);
      tabRefs.current[safeIdx]?.focus();
    },
    [totalTabs],
  );

  // Keyboard handler on <nav> — events bubble from child buttons
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLElement>) => {
      switch (e.key) {
        case "ArrowRight":
          e.preventDefault();
          focusTab(focusedIdx + 1);
          return;
        case "ArrowLeft":
          e.preventDefault();
          focusTab(focusedIdx - 1);
          return;
        case "Home":
          e.preventDefault();
          focusTab(0);
          return;
        case "End":
          e.preventDefault();
          focusTab(totalTabs - 1);
          return;
        default:
          break;
      }
    },
    [focusedIdx, focusTab, totalTabs],
  );

  // Stable leaf click handler — extracted to reduce cognitive complexity of render
  const handleLeafClick = useCallback(
    (idx: number, isAdd: boolean, href: string) => {
      setFocusedIdx(idx);
      if (isAdd && onAddAffordance) {
        onAddAffordance();
      } else if (href) {
        router.push(href);
      }
    },
    [onAddAffordance, router],
  );

  // Stable leaf focus handler
  const handleLeafFocus = useCallback((idx: number) => {
    setFocusedIdx(idx);
  }, []);

  return (
    <div
      className={cn(
        // Full-bleed N3 ribbon: sticky, bg-card, border-bottom, radius:0 (NOT a rounded card)
        "sticky top-0 z-20 w-full bg-card border-b border-border rounded-none",
        "flex items-center gap-0 min-h-[44px] px-4",
        className,
      )}
      data-testid="entity-sub-nav-bar"
    >
      {/* Tablist — root leaf + (workspace mode) entity identity + content leaves */}
      <div className="flex-1 overflow-x-auto scrollbar-none min-w-0">
        <nav
          role="tablist"
          aria-label={`Secciones de ${rootLabel}`}
          data-testid="entity-sub-nav-tablist"
          onKeyDown={handleKeyDown}
          className="flex items-center gap-0.5 min-w-max"
        >
          {/* Root leaf (first tab) — always rendered, with ‹ back-arrow */}
          <LeafTabButton
            key={rootLeaf.id}
            leaf={rootLeaf}
            idx={0}
            isActive={activeTabIdx === 0}
            isFocused={focusedIdx === 0}
            isDisabled={false}
            tabRef={(el) => {
              tabRefs.current[0] = el;
            }}
            onLeafClick={handleLeafClick}
            onLeafFocus={handleLeafFocus}
          />

          {/* Entity identity slot — workspace mode only. When provided, the slot
              replaces the static avatar+name block (canon §6.3: identity = selector,
              "cambiar sin volver"). The slot is NOT a tab (tablist unaffected). */}
          {!isMasterMode && entity && entityIdentitySlot && (
            <div
              className="flex items-center min-w-0 flex-shrink-0 mx-3"
              data-testid="entity-identity-slot"
            >
              {entityIdentitySlot}
            </div>
          )}

          {/* Entity identity (static) — shown only in workspace mode (entity present)
              when no entityIdentitySlot is provided (back-compat) */}
          {!isMasterMode && entity && !entityIdentitySlot && (
            <div
              className="flex items-center gap-2 min-w-0 flex-shrink-0 mx-3 max-w-[200px]"
              aria-label={`Editando: ${entity.name}`}
            >
              {entity.avatarUrl ? (
                <Avatar className="h-6 w-6 flex-shrink-0">
                  <AvatarImage src={entity.avatarUrl} alt={entity.name} />
                  <AvatarFallback className="text-xs">
                    {entity.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              ) : entity.icon ? (
                <span
                  className="w-[30px] h-[30px] rounded-lg flex items-center justify-center bg-accent text-accent-foreground text-sm flex-shrink-0"
                  aria-hidden="true"
                >
                  {entity.icon}
                </span>
              ) : (
                <span
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-primary-foreground bg-primary flex-shrink-0"
                  aria-hidden="true"
                >
                  {entity.name.charAt(0).toUpperCase()}
                </span>
              )}
              <span className="text-sm font-bold truncate">{entity.name}</span>
            </div>
          )}

          {/* Placeholder — shown only in master mode (no entity selected) */}
          {isMasterMode && placeholder && (
            <span
              className="text-sm text-muted-foreground/60 ml-3 whitespace-nowrap"
              aria-label={placeholder}
            >
              {placeholder}
            </span>
          )}

          {/* Content leaves — workspace mode only */}
          {!isMasterMode &&
            leaves.map((leaf, idx) => {
              const tabIdx = idx + 1; // offset by 1 for root leaf at index 0
              const isActive = leaf.id === activeLeaf;
              const isFocused = focusedIdx === tabIdx;

              return (
                <LeafTabButton
                  key={leaf.id}
                  leaf={leaf}
                  idx={tabIdx}
                  isActive={isActive}
                  isFocused={isFocused}
                  isDisabled={false}
                  tabRef={(el) => {
                    tabRefs.current[tabIdx] = el;
                  }}
                  onLeafClick={handleLeafClick}
                  onLeafFocus={handleLeafFocus}
                />
              );
            })}
        </nav>
      </div>
    </div>
  );
}
