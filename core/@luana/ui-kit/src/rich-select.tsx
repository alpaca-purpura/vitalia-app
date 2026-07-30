import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./select";

export interface RichSelectOption {
  value: string;
  label: string;
  description?: string;
}

interface RichSelectProps {
  options: RichSelectOption[];
  placeholder?: string;
  value?: string;
  onValueChange: (value: string) => void;
  disabled?: boolean;
  /**
   * C2-T4 · extension surface: custom item renderer (render-prop).
   * When provided, replaces the default label+description layout inside each SelectItem.
   * Composición sobre fork (ADR-016 §3).
   */
  renderItem?: (option: RichSelectOption) => React.ReactNode;
}

export function RichSelect({
  options,
  placeholder,
  value,
  onValueChange,
  disabled,
  renderItem,
}: RichSelectProps) {
  // Ensure options have unique values and valid keys
  const validOptions = React.useMemo(() => {
    const seen = new Set<string>();
    return options.filter((opt) => {
      if (opt.value === undefined || opt.value === null) return false;
      if (seen.has(opt.value)) return false;
      seen.add(opt.value);
      return true;
    });
  }, [options]);

  return (
    <Select onValueChange={onValueChange} defaultValue={value} value={value} disabled={disabled}>
      {/* ponytail: FormControl removed — consumer wraps in FormField>FormItem>FormControl per Shadcn pattern (was crashing standalone) */}
      <SelectTrigger className="h-auto py-3 text-left">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {validOptions.map((option) => (
          <SelectItem key={option.value} value={option.value} className="py-3">
            {renderItem ? (
              renderItem(option)
            ) : (
              <div className="flex flex-col items-start gap-1 text-left">
                <span className="font-medium">{option.label}</span>
                {option.description && (
                  <span className="text-xs text-muted-foreground whitespace-normal leading-tight">
                    {option.description}
                  </span>
                )}
              </div>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
