import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--color-cobre)] px-5 py-3 text-[var(--color-piedra)] shadow-[0_12px_40px_rgba(175,103,57,0.16)] hover:bg-[color-mix(in_srgb,var(--color-cobre),white_14%)]",
        secondary:
          "border border-[var(--color-borde)] bg-white/70 px-5 py-3 text-[var(--color-obsidiana)] hover:border-[var(--color-laguna)] hover:bg-white/90",
        ghost:
          "px-3 py-2 text-[var(--color-obsidiana)] hover:bg-[var(--color-laguna-suave)] hover:text-[var(--color-laguna)]",
      },
      size: {
        default: "",
        compact: "px-3 py-2 text-xs uppercase tracking-[0.18em]",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ButtonProps): React.ReactElement {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
