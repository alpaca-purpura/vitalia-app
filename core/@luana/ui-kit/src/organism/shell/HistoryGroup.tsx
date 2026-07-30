// cap: platform.lift-shell-chrome-ui-kit
/**
 * HistoryGroup — conversation group molecule (Hoy / Ayer / Esta semana).
 * T-K2 port of vitalia HistoryGroup (F1-S5 T-3). Brand-agnostic: items typed as
 * ShellConversationMeta; the active-row class threads through to HistoryItem.
 *
 * Server Component — presentational. items.length === 0 → renders null
 * (groups with 0 items not rendered · SC-6).
 */

import type { ShellConversationMeta } from "./types";
import { HistoryItem } from "./HistoryItem";

export interface HistoryGroupProps {
  /** Group label: 'Hoy' | 'Ayer' | 'Esta semana'. */
  label: string;
  items: ShellConversationMeta[];
  activeId: string | null;
  onItemClick: (id: string) => void;
  /** active-row bg class (brand soft token). */
  activeClass?: string;
}

/** HistoryGroup — groups history items by time period (hidden when empty). */
export function HistoryGroup({
  label,
  items,
  activeId,
  onItemClick,
  activeClass,
}: HistoryGroupProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section aria-label={label}>
      <p className="px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <ul role="listbox" aria-label={label} className="flex flex-col gap-0.5">
        {items.map((conversation) => (
          <li key={conversation.id} role="presentation">
            <HistoryItem
              id={conversation.id}
              title={conversation.title}
              meta={conversation.meta}
              active={activeId === conversation.id}
              onClick={onItemClick}
              activeClass={activeClass}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
