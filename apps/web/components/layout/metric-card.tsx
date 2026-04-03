import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { CardShell } from "@/components/layout/card-shell";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
  accent?: "default" | "cobre" | "laguna";
  className?: string;
};

export function MetricCard({
  label,
  value,
  hint,
  accent = "default",
  className,
}: MetricCardProps): React.ReactElement {
  return (
    <CardShell accent={accent} className={cn("p-5", className)}>
      <div className="flex items-start justify-between gap-3">
        <Badge variant={accent === "cobre" ? "accent" : accent === "laguna" ? "laguna" : "default"}>
          {label}
        </Badge>
        <ArrowUpRight className="h-4 w-4 text-[var(--color-pizarra)]" />
      </div>
      <div className="mt-8 space-y-2">
        <p className="font-display text-4xl tracking-[-0.05em] text-[var(--color-obsidiana)]">
          {value}
        </p>
        {hint ? <p className="text-sm text-[var(--color-pizarra)]">{hint}</p> : null}
      </div>
    </CardShell>
  );
}
