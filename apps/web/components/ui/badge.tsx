import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]",
  {
    variants: {
      variant: {
        default:
          "border-[var(--color-borde)] bg-white/75 text-[var(--color-pizarra)]",
        accent:
          "border-[color-mix(in_srgb,var(--color-cobre),black_12%)] bg-[color-mix(in_srgb,var(--color-cobre),white_82%)] text-[var(--color-cobre-oscuro)]",
        laguna:
          "border-[color-mix(in_srgb,var(--color-laguna),white_40%)] bg-[var(--color-laguna-suave)] text-[var(--color-laguna)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

type BadgeProps = React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps): React.ReactElement {
  return <div className={cn(badgeVariants({ variant, className }))} {...props} />;
}
