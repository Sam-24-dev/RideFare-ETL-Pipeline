import { AlertCircle, DatabaseZap } from "lucide-react";

import { CardShell } from "@/components/layout/card-shell";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

type EmptyStateProps = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: EmptyStateProps): React.ReactElement {
  return (
    <CardShell accent="laguna" className="p-8 md:p-10">
      <div className="flex flex-col gap-6">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl border border-[var(--color-borde)] bg-white/80 p-3 text-[var(--color-laguna)]">
            <DatabaseZap className="h-6 w-6" />
          </div>
          <div className="space-y-2">
            <h2 className="font-display text-3xl tracking-[-0.03em] text-[var(--color-obsidiana)]">
              {title}
            </h2>
            <p className="max-w-3xl text-base leading-7 text-[var(--color-pizarra)]">{message}</p>
          </div>
        </div>
        <Separator />
        <div className="flex flex-col gap-4 text-sm text-[var(--color-pizarra)] md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-[var(--color-cobre)]" />
            <span>Primero ejecuta el pipeline para generar datos públicos tipados.</span>
          </div>
          <Button asChild variant="secondary">
            <a href="https://github.com/Sam-24-dev/RideFare-ETL-Pipeline#local-development">
              Ver pasos de setup
            </a>
          </Button>
        </div>
      </div>
    </CardShell>
  );
}
