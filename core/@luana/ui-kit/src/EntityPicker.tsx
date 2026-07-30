// canon: design-system-canon.md §2.4 · story-origin: core-ds-foundation
"use client";

/**
 * EntityPicker.tsx — Canon §2.4 entity selector (@luana/ui-kit · NET-NEW, no prior art).
 *
 * Lets the user CHANGE the active entity WITHOUT going back to the master grid.
 * Cimentado para escala 200+ entidades: NUNCA carga la colección entera al cliente.
 *
 * Anatomy:
 *   ┌─ trigger (Popover) ─────────────────────────────┐
 *   │  [avatar inits]  Nombre entidad actual      ▾   │
 *   └──────────────────────────────────────────────────┘
 *      ↓ (open)
 *   ┌─ popover content ───────────────────────────────┐
 *   │  🔎 [Input autofocus → debounced 200ms]          │
 *   │  ┌─ role=listbox (virtualized window) ─────────┐ │
 *   │  │ ○ option ……                                  │ │
 *   │  │ ○ option ……  (← infinite scroll sentinel)    │ │
 *   │  └──────────────────────────────────────────────┘ │
 *   │  · Mostrando N de M ·                             │
 *   └──────────────────────────────────────────────────┘
 *
 * Query-lib AGNOSTIC: receives a `searchFn` prop. The ui-kit does NOT depend on
 * react-query — the consumer wires the real API (cursor pagination contract below).
 *
 * a11y: combobox/listbox — search owns the combobox role; the list is role=listbox,
 * items are role=option; ↑↓ move the active option, Enter selects, Esc closes; the
 * search input is focused on open.
 *
 * Windowed render via @tanstack/react-virtual so the DOM only holds the visible window
 * even with hundreds of results. Infinite-scroll fetches the next cursor page when the
 * virtualizer reaches the tail.
 *
 * Slot/prop driven + brand-agnostic. Strings default to Spanish neutro LatAm.
 */

import * as React from "react";
import { ChevronDown, Search } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";

import { cn } from "@luana/format/utils";
import { useDebounce } from "@luana/hooks";

import { Avatar, AvatarFallback } from "./avatar";
import { Input } from "./input";
import { Popover, PopoverTrigger, PopoverContent } from "./popover";

// ── Types ───────────────────────────────────────────────────────────────────────

/** Minimal entity shape. Consumers may pass any extra fields via `T`. */
export interface EntityPickerItem {
  id: string;
  name: string;
  /** Optional 1-3 char initials for the avatar; derived from `name` when absent. */
  initials?: string;
}

/** Arguments handed to the consumer's `searchFn`. */
export interface EntitySearchArgs {
  /** Debounced search query (may be empty for the initial page). */
  q: string;
  /** Cursor of the page to fetch; `null`/absent → first page. */
  cursor?: string | null;
  /** Hard page size — ALWAYS passed (never "fetch everything"). */
  limit: number;
}

/** Result the consumer's `searchFn` must resolve to (cursor pagination). */
export interface EntitySearchResult<T extends EntityPickerItem = EntityPickerItem> {
  items: T[];
  /** Cursor for the NEXT page; `null`/absent → no more pages. */
  nextCursor?: string | null;
  /** Total matches (for the "Mostrando N de M" footer), when known. */
  total?: number;
}

/** The query-lib-agnostic fetcher. The consumer wires the real API here. */
export type EntitySearchFn<T extends EntityPickerItem = EntityPickerItem> = (
  args: EntitySearchArgs,
) => Promise<EntitySearchResult<T>>;

export interface EntityPickerProps<T extends EntityPickerItem = EntityPickerItem> {
  /** Currently selected entity (drives the trigger label). */
  value?: T | null;
  /** Fired when the user picks an entity from the list. */
  onChange?: (entity: T) => void;
  /** Query-lib-agnostic fetcher (cursor pagination). */
  searchFn: EntitySearchFn<T>;
  /** Page size for every fetch. Default 20. */
  limit?: number;
  /** Debounce window for the search input, in ms. Default 200. */
  debounceMs?: number;
  /** Trigger placeholder when nothing is selected. */
  placeholder?: string;
  /** Search input placeholder. */
  searchPlaceholder?: string;
  /** Empty-state label. */
  emptyLabel?: string;
  /** Disables the trigger. */
  disabled?: boolean;
  /** Optional className for the trigger. */
  className?: string;
  /** Stable test id seed. */
  testId?: string;
  /**
   * Pick-or-create: when there's a typed query and NO exact match (or zero results),
   * a final row `＋ {label(query)}` is rendered (dotted top border) that calls
   * `onCreate(query)` on click/Enter. Additive — omit it and the picker behaves as before.
   */
  createAction?: {
    /** Builds the create-row label from the current query (e.g. q => `Crear «${q}»`). */
    label: (query: string) => string;
    /** Fired with the current query when the user activates the create row. */
    onCreate: (query: string) => void;
  };
}

// ── Helpers ─────────────────────────────────────────────────────────────────────

/**
 * Derive up-to-2-char initials from a name when none are provided.
 * Null-safe by contract: a picker must NEVER crash on a value whose name is
 * missing/undefined (e.g. a stale or partial cache entry) — returns "?".
 */
function deriveInitials(name: string | null | undefined): string {
  const parts = (name ?? "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return (parts[0]![0]! + parts[parts.length - 1]![0]!).toUpperCase();
}

const ROW_HEIGHT = 44; // px — keeps the virtualizer measuring a real window under jsdom

// ── Component ─────────────────────────────────────────────────────────────────────

function EntityPickerInner<T extends EntityPickerItem>(
  {
    value,
    onChange,
    searchFn,
    limit = 20,
    debounceMs = 200,
    placeholder = "Seleccionar…",
    searchPlaceholder = "Buscar…",
    emptyLabel = "Sin resultados",
    disabled = false,
    className,
    testId,
    createAction,
  }: EntityPickerProps<T>,
  ref: React.Ref<HTMLButtonElement>,
) {
  const tid = testId ?? "entity-picker";

  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const debouncedQuery = useDebounce(query, debounceMs);

  const [items, setItems] = React.useState<T[]>([]);
  const [nextCursor, setNextCursor] = React.useState<string | null>(null);
  const [total, setTotal] = React.useState<number | undefined>(undefined);
  const [loading, setLoading] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(0);

  const listRef = React.useRef<HTMLDivElement>(null);
  const searchRef = React.useRef<HTMLInputElement>(null);
  // Guards against out-of-order responses clobbering fresher state.
  const requestSeq = React.useRef(0);

  // ── Fetch a page (first page when `reset`, else append the cursor page). ──────
  const fetchPage = React.useCallback(
    async (q: string, cursor: string | null, reset: boolean) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      try {
        const res = await searchFn({ q, cursor, limit });
        if (seq !== requestSeq.current) return; // a newer request superseded this one
        // Dedup by id al appendear páginas: la paginación por cursor puede solapar
        // filas (boundary) y el infinite-scroll puede disparar el mismo cursor 2×
        // antes de que `loading` actualice → keys React duplicadas. Dedup garantiza
        // ids únicos sin importar el solape del backend.
        setItems((prev) => {
          if (reset) return res.items;
          const seen = new Set(prev.map((p) => p.id));
          return [...prev, ...res.items.filter((it) => !seen.has(it.id))];
        });
        setNextCursor(res.nextCursor ?? null);
        setTotal(res.total);
        if (reset) setActiveIndex(0);
      } finally {
        if (seq === requestSeq.current) setLoading(false);
      }
    },
    [searchFn, limit],
  );

  // First page on open + every time the debounced query changes while open.
  React.useEffect(() => {
    if (!open) return;
    void fetchPage(debouncedQuery, null, true);
  }, [open, debouncedQuery, fetchPage]);

  // Focus the search when the popover opens; reset transient state on close.
  React.useEffect(() => {
    if (open) {
      // rAF/microtask so the portal content is mounted before we focus.
      const id = requestAnimationFrame(() => searchRef.current?.focus());
      return () => cancelAnimationFrame(id);
    }
    setQuery("");
    setItems([]);
    setNextCursor(null);
    setTotal(undefined);
    setActiveIndex(0);
    return undefined;
  }, [open]);

  // ── Virtualizer (windowed render). ────────────────────────────────────────────
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 6,
  });

  // Infinite scroll: when the last virtual row enters the window and there's a next
  // cursor, fetch the next page.
  const virtualItems = rowVirtualizer.getVirtualItems();
  React.useEffect(() => {
    const last = virtualItems[virtualItems.length - 1];
    if (!last) return;
    if (last.index >= items.length - 1 && nextCursor && !loading) {
      void fetchPage(debouncedQuery, nextCursor, false);
    }
  }, [virtualItems, items.length, nextCursor, loading, debouncedQuery, fetchPage]);

  const select = React.useCallback(
    (entity: T) => {
      onChange?.(entity);
      setOpen(false);
    },
    [onChange],
  );

  // Pick-or-create: offer the create row when there's a typed query and no EXACT
  // (case-insensitive, trimmed) name match among the loaded results.
  const trimmedQuery = query.trim();
  const hasExactMatch = React.useMemo(
    () =>
      trimmedQuery.length > 0 &&
      items.some((it) => (it.name ?? "").trim().toLowerCase() === trimmedQuery.toLowerCase()),
    [items, trimmedQuery],
  );
  const showCreate = !!createAction && trimmedQuery.length > 0 && !loading && !hasExactMatch;
  const showEmpty = !loading && items.length === 0 && !showCreate;
  // The create row occupies the virtual index === items.length (one past the last option).
  const createIndex = items.length;

  const fireCreate = React.useCallback(() => {
    if (!createAction || trimmedQuery.length === 0) return;
    createAction.onCreate(trimmedQuery);
    setOpen(false);
  }, [createAction, trimmedQuery]);

  // Keyboard nav on the search (which owns the combobox).
  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Navigable max index: last option, or the create row when it's shown.
    const maxIndex = showCreate ? createIndex : Math.max(items.length - 1, 0);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, maxIndex));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (showCreate && activeIndex === createIndex) {
        fireCreate();
        return;
      }
      const entity = items[activeIndex];
      if (entity) select(entity);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  };

  // Keep the active row scrolled into view.
  React.useEffect(() => {
    if (open && items.length > 0) rowVirtualizer.scrollToIndex(activeIndex, { align: "auto" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex, open]);

  const triggerInitials = value ? (value.initials ?? deriveInitials(value.name)) : "—";
  const triggerLabel = value?.name ?? placeholder;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          ref={ref}
          type="button"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          data-testid={`${tid}-trigger`}
          className={cn(
            "inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium text-foreground ring-offset-background transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            className,
          )}
        >
          <Avatar className="h-6 w-6">
            <AvatarFallback className="text-[10px]">{triggerInitials}</AvatarFallback>
          </Avatar>
          <span className="max-w-[14rem] truncate">{triggerLabel}</span>
          <ChevronDown className="h-4 w-4 shrink-0 opacity-60" aria-hidden="true" />
        </button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-72 p-0"
        data-testid={`${tid}-content`}
        // Keep focus inside the input; Radix would otherwise steal it back to the trigger.
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <div className="flex items-center gap-2 border-b px-3 py-2">
          <Search className="h-4 w-4 shrink-0 opacity-60" aria-hidden="true" />
          <Input
            ref={searchRef}
            type="text"
            role="combobox"
            aria-expanded={open}
            aria-controls={`${tid}-listbox`}
            aria-autocomplete="list"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={searchPlaceholder}
            data-testid={`${tid}-search`}
            className="h-8 border-0 px-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>

        {showEmpty ? (
          <div
            className="px-3 py-6 text-center text-sm text-muted-foreground"
            data-testid={`${tid}-empty`}
          >
            {emptyLabel}
          </div>
        ) : (
          <div
            ref={listRef}
            role="listbox"
            id={`${tid}-listbox`}
            aria-label="Resultados"
            data-testid={`${tid}-listbox`}
            className="max-h-64 overflow-auto"
          >
            <div
              style={{ height: rowVirtualizer.getTotalSize(), width: "100%", position: "relative" }}
            >
              {virtualItems.map((vRow) => {
                const entity = items[vRow.index];
                if (!entity) return null;
                const selected = value?.id === entity.id;
                const active = vRow.index === activeIndex;
                const inits = entity.initials ?? deriveInitials(entity.name);
                return (
                  <button
                    key={entity.id}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    data-active={active || undefined}
                    data-testid={`${tid}-option-${entity.id}`}
                    onMouseEnter={() => setActiveIndex(vRow.index)}
                    onClick={() => select(entity)}
                    className={cn(
                      "absolute left-0 top-0 flex w-full items-center gap-2 px-3 text-left text-sm transition-colors hover:bg-accent",
                      active && "bg-accent",
                      selected && "font-medium",
                    )}
                    style={{ height: ROW_HEIGHT, transform: `translateY(${vRow.start}px)` }}
                  >
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="text-[10px]">{inits}</AvatarFallback>
                    </Avatar>
                    <span className="truncate">{entity.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Pick-or-create row — final option, dotted top border, fires onCreate(query). */}
            {showCreate && createAction ? (
              <button
                type="button"
                role="option"
                aria-selected={activeIndex === createIndex}
                data-active={activeIndex === createIndex || undefined}
                data-testid={`${tid}-create`}
                onMouseEnter={() => setActiveIndex(createIndex)}
                onClick={fireCreate}
                className={cn(
                  "flex w-full items-center gap-2 border-t border-dashed border-border px-3 py-2.5 text-left text-sm text-foreground transition-colors hover:bg-accent",
                  activeIndex === createIndex && "bg-accent",
                )}
              >
                <span className="text-base leading-none text-muted-foreground" aria-hidden="true">
                  ＋
                </span>
                <span className="truncate">{createAction.label(trimmedQuery)}</span>
              </button>
            ) : null}
          </div>
        )}

        <div
          className="border-t px-3 py-2 text-center text-xs text-muted-foreground"
          data-testid={`${tid}-footer`}
        >
          {total !== undefined
            ? `Mostrando ${items.length} de ${total}`
            : `Mostrando ${items.length}`}
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Generic-friendly forwardRef wrapper. `forwardRef` erases generics, so we cast the
 * inner component back to a generic component type to preserve `T` for consumers.
 */
export const EntityPicker = React.forwardRef(EntityPickerInner) as <
  T extends EntityPickerItem = EntityPickerItem,
>(
  props: EntityPickerProps<T> & { ref?: React.Ref<HTMLButtonElement> },
) => React.ReactElement;
