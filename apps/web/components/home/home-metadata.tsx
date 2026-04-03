import type { HomeSnapshot } from "@/lib/data/loaders";
import { formatCompactDate } from "@/lib/formatters";

import { HomeActionLink } from "./home-action-link";
import { MetadataMapGraphic } from "./home-visuals";

type HomeMetadataProps = {
  snapshot: HomeSnapshot | null;
  missingMessage?: string;
};

export function HomeMetadata({
  snapshot,
  missingMessage,
}: HomeMetadataProps): React.ReactElement {
  return (
    <section className="grid gap-8 border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pb-14 lg:grid-cols-[0.92fr_1.08fr] lg:items-start lg:gap-12">
      <div className="space-y-3">
        <div className="overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[var(--color-obsidiana)]">
          <div className="aspect-[1.45/1]">
            <MetadataMapGraphic />
          </div>
        </div>
        <p className="inline-block border border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-[color-mix(in_srgb,var(--color-piedra),white_28%)] px-4 py-3 text-[11px] uppercase tracking-[0.2em] text-[var(--color-obsidiana)]">
          Corte topográfico v1 · Huella visible del sistema
        </p>
      </div>

      <div className="space-y-6 lg:pt-10">
        <div className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-obsidiana)]">
            Señales públicas
          </p>
          <h2 className="font-display text-5xl leading-[0.92] tracking-[-0.05em] text-[var(--color-obsidiana)]">
            Lo que hoy deja
            <br />
            ver el producto.
          </h2>
          <p className="max-w-xl text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
            Esta lectura pública resume tres señales concretas: la ruta más visible, la ventana
            temporal exportada y el motor que alimenta los escenarios del producto.
          </p>
        </div>

        <div className="space-y-3 border-y border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] py-5">
          {snapshot ? (
            <>
              <MetadataLine title="Ruta con señal dominante" value={snapshot.dominantRoute} />
              <MetadataLine
                title="Ventana exportada"
                value={`${formatCompactDate(snapshot.timeRange.min)} → ${formatCompactDate(snapshot.timeRange.max)}`}
              />
              <MetadataLine
                title="Motor de escenarios"
                value={`${snapshot.explainabilityModel.toUpperCase()} con ${snapshot.featureCount} variables visibles`}
              />
            </>
          ) : (
            <>
              <MetadataLine
                title="Estado local"
                value={missingMessage ?? "Pendiente de exportar artefactos públicos"}
              />
              <MetadataLine
                title="Arquitectura visible"
                value="La Home se poblará cuando exista model_overview.json y dashboard_overview.json"
              />
              <MetadataLine
                title="Superficies"
                value="Dashboard, cómo funciona y escenarios seguirán accesibles sin romper el build"
              />
            </>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <HomeActionLink href="/dashboard" className="rounded-none px-5 py-3">
            Abrir dashboard
          </HomeActionLink>
          <HomeActionLink href="/escenarios" variant="secondary" className="rounded-none px-5 py-3">
            Explorar escenarios
          </HomeActionLink>
        </div>
      </div>
    </section>
  );
}

function MetadataLine({
  title,
  value,
}: {
  title: string;
  value: string;
}): React.ReactElement {
  return (
    <div className="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between md:gap-6">
      <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--color-obsidiana)]">
        {title}
      </p>
      <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_8%)] md:text-right">
        {value}
      </p>
    </div>
  );
}
