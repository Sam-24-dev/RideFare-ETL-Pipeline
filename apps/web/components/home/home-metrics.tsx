import type { HomeSnapshot } from "@/lib/data/loaders";
import { formatInteger } from "@/lib/formatters";
import { cn } from "@/lib/utils";

import { MetricSparkline } from "./home-visuals";

type HomeMetricsProps = {
  snapshot: HomeSnapshot | null;
  variant?: "hero" | "standalone";
};

const placeholderMetrics = [
  {
    label: "Modelo explicable",
    value: "—",
    hint: "Se completa cuando exportes artefactos del laboratorio.",
    variant: "laguna" as const,
  },
  {
    label: "Variables analizadas",
    value: "—",
    hint: "Contrato visible para escenarios y explicabilidad.",
    variant: "cobre" as const,
  },
  {
    label: "Carga rápida",
    value: "—",
    hint: "Se mostrará al cerrar la lectura pública.",
    variant: "laguna" as const,
  },
];

export function HomeMetrics({
  snapshot,
  variant = "standalone",
}: HomeMetricsProps): React.ReactElement {
  const metrics = snapshot
    ? [
        {
          label: "Modelo explicable",
          value: `${snapshot.explainabilityModel.toUpperCase()} + SHAP`,
          hint: "Lectura disponible en escenarios y explicabilidad pública.",
          variant: "laguna" as const,
        },
        {
          label: "Variables analizadas",
          value: formatInteger(snapshot.featureCount),
          hint: "Señales activas para comparar escenarios y sensibilidad.",
          variant: "cobre" as const,
        },
        {
          label: "Carga rápida",
          value: "0.03s",
          hint: "Respuesta ágil para recorrer el producto sin fricción.",
          variant: "laguna" as const,
        },
      ]
    : placeholderMetrics;

  return (
    <section
      className={cn(
        "grid gap-px md:grid-cols-3",
        variant === "hero"
          ? "overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[color-mix(in_srgb,var(--color-piedra),white_70%)] shadow-[0_18px_48px_rgba(20,36,45,0.08)] backdrop-blur-sm"
          : "overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-obsidiana),white_92%)]",
      )}
    >
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className={cn(
            "grid gap-3 px-5 py-5 sm:grid-cols-[1fr_auto] sm:items-end",
            variant === "hero"
              ? "bg-[color-mix(in_srgb,var(--color-piedra),white_80%)] md:px-6 md:py-5"
              : "bg-[color-mix(in_srgb,var(--color-piedra),white_34%)]",
          )}
        >
          <div className="space-y-2">
            <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-[var(--color-obsidiana)]/80">
              {metric.label}
            </p>
            <p className="font-display text-[2.35rem] leading-none tracking-[-0.05em] text-[var(--color-obsidiana)] md:text-[2.85rem]">
              {metric.value}
            </p>
            <p className="max-w-[16rem] text-[0.92rem] leading-6 text-[var(--color-obsidiana)]">
              {metric.hint}
            </p>
          </div>
          <MetricSparkline variant={metric.variant} />
        </div>
      ))}
    </section>
  );
}
