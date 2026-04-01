import type { ReactNode } from "react";

import { CardShell } from "@/components/layout/card-shell";
import { cn } from "@/lib/utils";

type FilterBarProps = {
  children: ReactNode;
  className?: string;
};

export function FilterBar({ children, className }: FilterBarProps): React.ReactElement {
  return (
    <CardShell className={cn("p-4 md:p-5", className)}>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{children}</div>
    </CardShell>
  );
}
