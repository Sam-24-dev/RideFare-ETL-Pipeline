import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export const SheetClose = DialogPrimitive.Close;

type SheetContentProps = React.ComponentProps<typeof DialogPrimitive.Content> & {
  side?: "left" | "right";
};

export function SheetPortal({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return <DialogPrimitive.Portal>{children}</DialogPrimitive.Portal>;
}

export function SheetOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>): React.ReactElement {
  return (
    <DialogPrimitive.Overlay
      className={cn("fixed inset-0 z-50 bg-black/35 backdrop-blur-sm", className)}
      {...props}
    />
  );
}

export function SheetContent({
  children,
  className,
  side = "right",
  ...props
}: SheetContentProps): React.ReactElement {
  return (
    <SheetPortal>
      <SheetOverlay />
      <DialogPrimitive.Content
        className={cn(
          "fixed top-0 z-50 h-full w-[min(92vw,24rem)] border-[var(--color-borde)] bg-[var(--color-piedra)]/95 p-6 shadow-[0_24px_80px_rgba(17,25,39,0.28)] backdrop-blur-xl focus:outline-none",
          side === "right" ? "right-0 border-l" : "left-0 border-r",
          className,
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-full border border-[var(--color-borde)] p-2 text-[var(--color-pizarra)] transition-colors hover:border-[var(--color-cobre)] hover:text-[var(--color-cobre)]">
          <X className="h-4 w-4" />
          <span className="sr-only">Cerrar navegación</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </SheetPortal>
  );
}

export function SheetTitle(
  props: React.ComponentProps<typeof DialogPrimitive.Title>,
): React.ReactElement {
  return <DialogPrimitive.Title className="text-lg font-semibold" {...props} />;
}

export function SheetDescription(
  props: React.ComponentProps<typeof DialogPrimitive.Description>,
): React.ReactElement {
  return (
    <DialogPrimitive.Description
      className="text-sm text-[var(--color-pizarra)]"
      {...props}
    />
  );
}
