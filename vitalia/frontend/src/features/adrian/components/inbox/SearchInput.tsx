// cap: adrian.inbox
// story-origin: TBD
"use client";
/**
 * SearchInput.tsx — Debounced search input for the conversation list.
 *
 * Debounce: 300ms (per 03-arch-fe.md § 3).
 * Does NOT directly manage URL state — consumer (ConversationListPanel) owns
 * the nuqs state and passes value/onChange as controlled props.
 * This keeps SearchInput testable without nuqs provider.
 *
 * "use client" required for useState (debounce internal state) + useEffect.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

interface SearchInputProps {
  /** Controlled value (from URL state via nuqs) */
  value: string | null;
  /** Debounced callback (called 300ms after last keystroke) */
  onChange: (value: string | null) => void;
  className?: string;
}

/**
 * SearchInput — debounced search box for filtering conversations.
 * Shows a clear (✕) button when value is non-empty.
 * Exposes role="searchbox" for accessibility.
 */
export function SearchInput({ value, onChange, className }: SearchInputProps) {
  // Local state tracks in-progress typing (before debounce fires)
  const [localValue, setLocalValue] = useState(value ?? "");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync when controlled value changes externally (e.g., URL cleared)
  useEffect(() => {
    setLocalValue(value ?? "");
  }, [value]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const next = e.target.value;
    setLocalValue(next);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onChange(next || null);
    }, 300);
  }

  function handleClear() {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setLocalValue("");
    onChange(null);
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const hasValue = localValue.length > 0;

  return (
    <div className={cn("relative flex items-center", className)} role="search">
      {/* Search icon */}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute left-3 text-xs vt-text-muted"
      >
        🔍
      </span>

      <input
        type="search"
        role="searchbox"
        aria-label={INBOX_COPY.filters.searchPlaceholder}
        placeholder={INBOX_COPY.filters.searchPlaceholder}
        value={localValue}
        onChange={handleChange}
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        className={cn(
          "w-full rounded-md border py-2 pl-8 pr-8 text-sm",
          "vt-border vt-bg-surface vt-text-foreground",
          "placeholder:vt-text-muted",
          "focus:outline-none focus:ring-1 focus:vt-ring-primary",
          "transition-shadow",
        )}
      />

      {/* Clear button — only when value is non-empty */}
      {hasValue && (
        <button
          type="button"
          aria-label="Limpiar búsqueda"
          onClick={handleClear}
          className={cn(
            "absolute right-2 flex h-5 w-5 items-center justify-center",
            "rounded-full text-xs vt-text-muted",
            "hover:vt-text-foreground focus-visible:outline",
            "focus-visible:outline-2 focus-visible:outline-offset-2",
            "focus-visible:vt-outline-primary transition-colors",
          )}
        >
          ✕
        </button>
      )}
    </div>
  );
}
