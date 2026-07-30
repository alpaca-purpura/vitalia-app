// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// VariantsRepeater — structured variants of the SAME service that change the
// price (e.g. "Composite S/ 2.500" vs "Porcelana S/ 4.500"). Controlled array
// editor: name + price (currency-prefixed) + optional note + remove, plus an
// "Agregar variante" action. Autosave is wired by the caller via onChange
// (no "Guardar" button — form-runtime-array doctrine).
"use client";

import { Button, Input } from "@luana/ui-kit";
import { cn } from "@/lib/cn";

export interface ServiceVariant {
  id: string;
  name: string;
  price: number;
  note?: string;
}

/** Minimal ISO-4217 → display-symbol map for the prefix (fallback = code). */
const CURRENCY_SYMBOL: Record<string, string> = {
  PEN: "S/",
  ARS: "AR$",
  MXN: "MX$",
  COP: "COL$",
  CLP: "CLP$",
  BRL: "R$",
  USD: "$",
};

function symbolFor(currency: string | null | undefined): string {
  if (!currency) return "$";
  return CURRENCY_SYMBOL[currency] ?? currency;
}

interface VariantsRepeaterProps {
  value: ServiceVariant[];
  onChange: (next: ServiceVariant[]) => void;
  /** Currency used for the price prefix. Fallback chain handled by caller. */
  currency: string | null | undefined;
  disabled?: boolean;
  className?: string;
}

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `v-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function VariantsRepeater({
  value,
  onChange,
  currency,
  disabled = false,
  className,
}: VariantsRepeaterProps) {
  const symbol = symbolFor(currency);

  const patch = (id: string, fields: Partial<ServiceVariant>) =>
    onChange(value.map((v) => (v.id === id ? { ...v, ...fields } : v)));

  const remove = (id: string) => onChange(value.filter((v) => v.id !== id));

  const add = () => onChange([...value, { id: newId(), name: "", price: 0, note: "" }]);

  return (
    <div className={className}>
      <div className="my-1 space-y-1.5">
        {value.map((variant) => (
          <div
            key={variant.id}
            data-testid={`variant-row-${variant.id}`}
            className="space-y-2 sm:flex sm:items-center sm:gap-2 sm:space-y-0"
          >
            <Input
              aria-label="Nombre de la variante"
              placeholder="Nombre"
              value={variant.name}
              disabled={disabled}
              onChange={(e) => patch(variant.id, { name: e.target.value })}
              className="font-medium sm:flex-1"
            />
            <div className="flex items-center gap-1">
              <span className="shrink-0 whitespace-nowrap text-sm text-muted-foreground">
                {symbol}
              </span>
              <Input
                type="number"
                inputMode="numeric"
                min={0}
                aria-label="Precio de la variante"
                placeholder="0"
                value={Number.isFinite(variant.price) ? String(variant.price) : ""}
                disabled={disabled}
                onChange={(e) => {
                  const parsed = Number(e.target.value);
                  patch(variant.id, { price: Number.isNaN(parsed) ? 0 : parsed });
                }}
                className="max-w-24"
              />
            </div>
            <Input
              aria-label="Qué cambia (opcional)"
              placeholder="qué cambia (opcional)"
              value={variant.note ?? ""}
              disabled={disabled}
              onChange={(e) => patch(variant.id, { note: e.target.value })}
              className="sm:flex-1"
            />
            <button
              type="button"
              data-testid={`variant-del-${variant.id}`}
              title="Quitar variante"
              aria-label="Quitar variante"
              disabled={disabled}
              onClick={() => remove(variant.id)}
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs text-muted-foreground transition-colors",
                "hover:bg-destructive/10 hover:text-destructive",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <Button type="button" variant="ghost" size="sm" disabled={disabled} onClick={add}>
        + Agregar variante
      </Button>
    </div>
  );
}
