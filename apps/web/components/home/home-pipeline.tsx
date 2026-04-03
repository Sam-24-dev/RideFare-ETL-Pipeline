const pipelineSteps = [
  {
    id: "01",
    title: "Viajes + clima",
    stack: "Entrada",
    description: "Fuentes visibles listas para validación antes de cualquier lectura pública.",
  },
  {
    id: "02",
    title: "Validación",
    stack: "Pandera + Parquet",
    description: "Tipado, controles y una capa intermedia reproducible antes del análisis.",
  },
  {
    id: "03",
    title: "Marts analíticos",
    stack: "DuckDB + dbt",
    description: "Modelado de negocio para dashboard, señales públicas y escenarios.",
  },
  {
    id: "04",
    title: "Escenarios",
    stack: "XGBoost + SHAP",
    description: "Benchmark, explicabilidad y simulación exportada sin inferencia en vivo.",
  },
  {
    id: "05",
    title: "Producto web",
    stack: "Next.js + export-web",
    description: "Superficies públicas rápidas sobre artefactos estáticos y tipados.",
  },
];

export function HomePipeline(): React.ReactElement {
  return (
    <section className="grid gap-8 border-y border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] py-14 lg:grid-cols-[0.38fr_0.62fr] lg:gap-12">
      <div className="space-y-4">
        <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-obsidiana)]">
          Del dato al producto
        </p>
        <h2 className="font-display text-5xl leading-[0.92] tracking-[-0.05em] text-[var(--color-obsidiana)]">
          Un flujo visible
          <br />
          detrás de cada lectura.
        </h2>
        <p className="max-w-md text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
          RideFare convierte fuentes crudas en vistas analíticas, escenarios exportados y una
          experiencia pública consistente. Aquí se resume el recorrido sin duplicar toda la
          explicación.
        </p>
      </div>

      <div className="grid gap-px border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] lg:grid-cols-5">
        {pipelineSteps.map((step) => (
          <div
            key={step.id}
            className="flex min-h-[14rem] flex-col justify-between bg-[color-mix(in_srgb,var(--color-piedra),white_35%)] px-5 py-5"
          >
            <div className="space-y-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-obsidiana)]">
                {step.id}
              </p>
              <h3 className="font-display text-3xl leading-[0.95] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                {step.title}
              </h3>
              <p className="text-[11px] uppercase tracking-[0.2em] text-[var(--color-cobre)]">
                {step.stack}
              </p>
            </div>
            <p className="text-sm leading-6 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
              {step.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
