import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

export const Select = SelectPrimitive.Root;
export const SelectValue = SelectPrimitive.Value;

export function SelectTrigger({
  className,
  children,
  screenReaderLabel,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Trigger> & {
  screenReaderLabel?: string;
}): React.ReactElement {
  const ariaLabel = props["aria-label"] ?? screenReaderLabel;
  const title = props.title ?? screenReaderLabel;

  return (
    <SelectPrimitive.Trigger
      className={cn(
        "inline-flex h-11 w-full items-center justify-between rounded-full border border-[var(--color-borde)] bg-white/70 px-4 text-sm text-[var(--color-obsidiana)] shadow-sm transition-colors hover:border-[var(--color-laguna)] focus:outline-none focus:ring-2 focus:ring-[var(--color-laguna)]",
        className,
      )}
      aria-label={ariaLabel}
      title={title}
      {...props}
    >
      {screenReaderLabel ? <span className="sr-only">{screenReaderLabel}</span> : null}
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDown className="h-4 w-4 text-[var(--color-pizarra)]" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

export function SelectContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Content>): React.ReactElement {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        className={cn(
          "z-50 overflow-hidden rounded-3xl border border-[var(--color-borde)] bg-[var(--color-piedra)] p-2 shadow-[0_18px_60px_rgba(17,25,39,0.18)]",
          className,
        )}
        {...props}
      >
        <SelectPrimitive.Viewport>{children}</SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

export function SelectItem({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Item>): React.ReactElement {
  return (
    <SelectPrimitive.Item
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-2xl py-2 pl-9 pr-3 text-sm text-[var(--color-obsidiana)] outline-none transition-colors focus:bg-[var(--color-laguna-suave)]",
        className,
      )}
      {...props}
    >
      <span className="absolute left-3 inline-flex h-4 w-4 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <Check className="h-4 w-4 text-[var(--color-laguna)]" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}
