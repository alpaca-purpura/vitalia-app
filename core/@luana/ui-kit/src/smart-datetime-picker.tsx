"use client";

import * as React from "react";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import { toZonedTime, fromZonedTime } from "date-fns-tz";
import { cn } from "@luana/format/utils";
import { Button } from "./button";
import { Calendar } from "./calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { TimePicker } from "./TimePicker";

interface SmartDateTimePickerProps {
  value?: string; // UTC ISO String
  onChange: (value: string) => void;
  timezone: string; // "America/Lima"
  className?: string;
  placeholder?: string;
  /**
   * C2-T4 · extension surface: custom trigger element (slot).
   * Must be a focusable React element — Radix `asChild` clones it and wires open/close.
   * When omitted, the default Button with CalendarIcon renders.
   * Composición sobre fork (ADR-016 §3).
   */
  trigger?: React.ReactNode;
  /**
   * When false, hides the time section and formats the trigger date-only.
   * Default true (current behavior).
   */
  showTime?: boolean;
  /**
   * When true, days before today (in `timezone`) are disabled. Default false.
   */
  disablePast?: boolean;
}

export function SmartDateTimePicker({
  value,
  onChange,
  timezone,
  className,
  placeholder = "Seleccionar fecha",
  trigger,
  showTime = true,
  disablePast = false,
}: SmartDateTimePickerProps) {
  // Compute "Fake Local Date" for display
  // This date object's internal time corresponds to the Wall Time in the target timezone
  const date = React.useMemo(() => {
    if (!value) return undefined;
    try {
      return toZonedTime(value, timezone);
    } catch (e) {
      console.error("Invalid date or timezone", e);
      return undefined;
    }
  }, [value, timezone]);

  // Browser-local midnight of "today in `timezone`" — the floor for disablePast.
  // Only computed when needed (default behavior leaves the Calendar untouched).
  const minDay = React.useMemo(() => {
    if (!disablePast) return undefined;
    const [y, mo, d] = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
      .format(new Date())
      .split("-")
      .map(Number);
    return new Date(y, mo - 1, d);
  }, [disablePast, timezone]);

  // Time string (HH:mm) from the "Fake Local Date"
  // Default to 09:00 if creating new
  const [timeStr, setTimeStr] = React.useState(date ? format(date, "HH:mm") : "09:00");

  // Sync state when prop changes
  React.useEffect(() => {
    if (date) {
      setTimeStr(format(date, "HH:mm"));
    }
  }, [date]);

  const handleDateSelect = (newDate: Date | undefined) => {
    if (!newDate) return;
    // newDate comes from Calendar, so it's a "Fake Local" date (Browser Local)

    // Combine with current timeStr
    const [hours, minutes] = timeStr.split(":").map(Number);
    newDate.setHours(hours, minutes, 0, 0);

    // Convert "Fake Local" -> UTC
    try {
      const utcDate = fromZonedTime(newDate, timezone);
      onChange(utcDate.toISOString());
    } catch (e) {
      console.error("Error converting date", e);
    }
  };

  const handleTimeChange = (newTime: string) => {
    setTimeStr(newTime);

    // If we have a date + a complete time, update the value immediately
    if (date && newTime) {
      // Create new "Fake Local" base from the existing one
      const newDate = new Date(date);
      const [hours, minutes] = newTime.split(":").map(Number);
      newDate.setHours(hours, minutes, 0, 0);

      // Convert -> UTC
      try {
        const utcDate = fromZonedTime(newDate, timezone);
        onChange(utcDate.toISOString());
      } catch (e) {
        console.error("Error converting time", e);
      }
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        {trigger != null && React.isValidElement(trigger) ? (
          trigger
        ) : (
          <Button
            variant={"outline"}
            className={cn(
              "w-full justify-start text-left font-normal",
              !date && "text-muted-foreground",
              className,
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date ? (
              format(date, showTime ? "dd/MM/yyyy HH:mm" : "dd/MM/yyyy", { locale: es })
            ) : (
              <span>{placeholder}</span>
            )}
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-auto min-w-[280px] p-0" align="start">
        {showTime && (
          <div className="flex items-center border-b border-border bg-muted/20 p-4">
            <TimePicker value={timeStr} onChange={handleTimeChange} aria-label="Hora" />
          </div>
        )}
        <Calendar
          mode="single"
          selected={date}
          onSelect={handleDateSelect}
          disabled={minDay ? { before: minDay } : undefined}
          initialFocus
          locale={es}
          className="p-3 pointer-events-auto"
        />
      </PopoverContent>
    </Popover>
  );
}
