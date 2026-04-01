import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
};

export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
  className,
}: SectionHeaderProps): React.ReactElement {
  return (
    <div className={cn("flex flex-col gap-4 md:flex-row md:items-end md:justify-between", className)}>
      <div className="space-y-2">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-cobre)]">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="font-display text-3xl tracking-[-0.03em] text-[var(--color-obsidiana)] md:text-4xl">
          {title}
        </h2>
        {description ? (
          <p className="max-w-3xl text-sm leading-7 text-[var(--color-pizarra)] md:text-base">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
