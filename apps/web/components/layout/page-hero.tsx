import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  aside?: ReactNode;
  className?: string;
};

export function PageHero({
  eyebrow,
  title,
  description,
  aside,
  className,
}: PageHeroProps): React.ReactElement {
  return (
    <section className={cn("grid gap-8 lg:grid-cols-[minmax(0,1fr)_18rem]", className)}>
      <div className="space-y-5">
        <Badge variant="laguna">{eyebrow}</Badge>
        <div className="space-y-4">
          <h1 className="max-w-4xl font-display text-5xl leading-[0.92] tracking-[-0.04em] text-[var(--color-obsidiana)] md:text-6xl">
            {title}
          </h1>
          <p className="max-w-3xl text-lg leading-8 text-[var(--color-pizarra)] md:text-xl">
            {description}
          </p>
        </div>
      </div>
      {aside ? <div className="self-end">{aside}</div> : null}
    </section>
  );
}
