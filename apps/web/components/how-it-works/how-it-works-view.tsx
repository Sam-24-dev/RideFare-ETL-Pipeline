import { HomeActionLink } from "@/components/home/home-action-link";
import type { HowItWorksSnapshot } from "@/lib/data/loaders";
import { cn } from "@/lib/utils";

type HowItWorksViewProps = {
  snapshot: HowItWorksSnapshot | null;
};

const lifecycleSteps = [
  {
    step: "01",
    title: "Fuentes",
    body: "Capturamos viajes y contexto climático para construir una lectura inicial del movimiento urbano.",
    tags: ["Viajes", "Clima"],
  },
  {
    step: "02",
    title: "Validación",
    body: "Limpiamos valores atípicos, revisamos consistencia entre campos y dejamos una base confiable para el análisis.",
    tags: ["Contratos", "Limpieza"],
  },
  {
    step: "03",
    title: "Vistas analíticas",
    body: "Organizamos el dato en vistas para comparar rutas, horarios y señales del dashboard.",
    tags: ["Rutas", "Horarios"],
  },
  {
    step: "04",
    title: "Modelo",
    body: "Probamos patrones de precio y demanda para abrir escenarios explicables.",
    tags: ["Predicción", "Explicabilidad"],
  },
  {
    step: "05",
    title: "Producto público",
    body: "Convertimos el proceso en superficies claras que alimentan el dashboard, esta página y la capa de escenarios.",
    tags: ["Dashboard", "Escenarios"],
  },
] as const;

export function HowItWorksView({ snapshot }: HowItWorksViewProps): React.ReactElement {
  const topSignals = snapshot?.topSignals ?? getFallbackSignals();
  const mlFactors = topSignals.map((signal) => ({
    title: signal.label,
    body: getSignalDescription(signal.label),
  }));
  const explainabilityLabel = snapshot
    ? `Escenarios construidos con una capa predictiva explicable apoyada en ${formatModelName(snapshot.explainabilityModel)}`
    : "Escenarios construidos con una capa predictiva explicable";
  const predictiveCards = [
    {
      step: "01",
      title: "Punto de partida",
      body: "Usamos una referencia base para detectar cuándo el precio realmente cambia.",
      accent:
        "border-[color-mix(in_srgb,var(--color-cobre),white_18%)] bg-[color-mix(in_srgb,var(--color-cobre),white_93%)]",
    },
    {
      step: "02",
      title: "Predicción explicable",
      body: "La capa predictiva deja visibles las señales que empujan cada lectura sin convertir el producto en una caja cerrada.",
      accent:
        "border-[color-mix(in_srgb,var(--color-laguna),white_22%)] bg-[color-mix(in_srgb,var(--color-laguna),white_91%)]",
    },
    {
      step: "03",
      title: "Escenarios comparables",
      body: "La siguiente pantalla te deja mover demanda, clima, hora y trayecto para ver cómo respondería el precio.",
      accent:
        "border-[color-mix(in_srgb,var(--color-obsidiana),white_72%)] bg-[color-mix(in_srgb,var(--color-obsidiana),white_95%)]",
    },
  ] as const;

  return (
    <div className="space-y-12 pb-6 md:space-y-16">
      <section className="relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[color-mix(in_srgb,var(--color-piedra),white_30%)] shadow-[0_24px_80px_rgba(20,36,45,0.05)]">
        <div className="absolute inset-0 opacity-85">
          <HowItWorksHeroWaves />
        </div>
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.44)_0%,rgba(255,255,255,0.14)_100%)]" />

        <div className="relative z-10 px-6 py-10 sm:px-8 md:px-10 md:py-12 lg:px-12 lg:py-14">
          <div className="max-w-4xl space-y-5">
            <h1 className="max-w-[44rem] font-display text-5xl leading-[0.9] tracking-[-0.05em] text-[var(--color-obsidiana)] sm:text-6xl lg:text-[4.5rem]">
              Cómo funciona <span className="text-[var(--color-cobre)]">RideFare</span>
            </h1>
            <p className="max-w-[40rem] text-base leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_8%)] md:text-lg">
              Desde la captura de datos urbanos hasta la lectura pública final: así convertimos
              el movimiento de la ciudad en señales claras, comparables y explorables.
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <div className="border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pb-4">
          <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
            El ciclo de vida del dato
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {lifecycleSteps.map((step, index) => (
            <article
              key={step.step}
              className={cn(
                "relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_42%)] px-5 py-6 shadow-[0_18px_48px_rgba(20,36,45,0.04)]",
                index === 2 &&
                  "bg-[color-mix(in_srgb,var(--color-piedra),white_56%)] shadow-[0_18px_56px_rgba(175,103,57,0.08)]",
                index === lifecycleSteps.length - 1 && "md:col-span-2 xl:col-span-1",
              )}
            >
              <p className="pointer-events-none absolute right-4 top-3 font-display text-6xl tracking-[-0.06em] text-[color-mix(in_srgb,var(--color-obsidiana),white_90%)]">
                {step.step}
              </p>
              <div className="relative space-y-5">
                <div className="flex flex-wrap items-center gap-2 text-[10px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                  <span>{step.tags[0]}</span>
                  <span className="text-[color-mix(in_srgb,var(--color-obsidiana),white_42%)]">·</span>
                  <span>{step.tags[1]}</span>
                </div>
                <h3 className="max-w-[12rem] font-display text-[2rem] leading-[0.98] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                  {step.title}
                </h3>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  {step.body}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:items-start">
        <div className="space-y-5 lg:pt-3">
          <div className="space-y-3">
            <h2 className="font-display text-[2.2rem] leading-[0.95] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
              Modelo y explicabilidad
            </h2>
            <p className="max-w-2xl text-sm leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)] md:text-base">
              Después de limpiar y ordenar el dato, RideFare abre una capa de predicción para
              comparar cómo cambian los precios según distancia, demanda, clima y contexto.
            </p>
            <p className="max-w-2xl text-sm leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)] md:text-base">
              Esa lectura no se presenta como una caja cerrada: dejamos visibles las señales que
              explican cada escenario.
            </p>
          </div>

          <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_24%)]">
            {explainabilityLabel}
          </p>
        </div>

        <div className="overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_48%)] p-5 shadow-[0_24px_72px_rgba(20,36,45,0.05)]">
          <div className="border border-[color-mix(in_srgb,var(--color-cobre),white_60%)] bg-white/72 p-4 sm:p-5">
            <div className="space-y-5">
              <div className="flex items-end justify-between gap-4 border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] pb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
                    Factores visibles
                  </p>
                  <h3 className="mt-2 font-display text-[1.9rem] leading-none tracking-[-0.05em] text-[var(--color-obsidiana)]">
                    Lo que entra en cada escenario
                  </h3>
                </div>
                <span className="text-[11px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_26%)]">
                  Lectura explicable
                </span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {mlFactors.map((signal, index) => (
                  <article
                    key={signal.title}
                    className={cn(
                      "space-y-3 border border-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] bg-[color-mix(in_srgb,var(--color-piedra),white_24%)] p-4",
                      index === 1 &&
                        "border-[color-mix(in_srgb,var(--color-laguna),white_34%)] bg-[color-mix(in_srgb,var(--color-laguna),white_94%)]",
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "h-7 w-1 shrink-0",
                          index === 1
                            ? "bg-[color-mix(in_srgb,var(--color-laguna),white_4%)]"
                            : "bg-[color-mix(in_srgb,var(--color-cobre),white_12%)]",
                        )}
                      />
                      <h4 className="font-display text-[1.45rem] leading-none tracking-[-0.04em] text-[var(--color-obsidiana)]">
                        {signal.title}
                      </h4>
                    </div>
                    <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                      {signal.body}
                    </p>
                  </article>
                ))}
              </div>

              <p className="border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] pt-4 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_14%)]">
                En escenarios verás cómo cambia el precio cuando estas señales se mueven juntas.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-8 overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-piedra),white_28%)_0%,color-mix(in_srgb,var(--color-piedra-profunda),white_10%)_100%)] px-5 py-10 shadow-[0_24px_80px_rgba(20,36,45,0.05)] lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] lg:px-8 lg:py-12">
        <div className="space-y-4">
          <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
            Predicción y escenarios
          </p>
          <h2 className="max-w-3xl font-display text-[2.35rem] leading-[0.94] tracking-[-0.05em] text-[var(--color-obsidiana)] sm:text-[2.7rem] md:text-[3.15rem]">
            La capa que convierte el dato limpio en decisiones comparables.
          </h2>
          <p className="max-w-2xl text-sm leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)] md:text-base">
            Aquí es donde el dato limpio se convierte en comparaciones que puedes mover y
            entender.
          </p>
          <p className="max-w-2xl text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_14%)]">
            Antes de abrir escenarios, RideFare deja claro qué toma como referencia, cómo vuelve
            explicable la predicción y qué variables podrás mover en la siguiente pantalla.
          </p>
        </div>

        <div className="relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-[color-mix(in_srgb,var(--color-obsidiana),white_96%)] p-5 shadow-[0_24px_72px_rgba(20,36,45,0.08)] sm:p-6">
          <div className="absolute inset-x-0 top-0 h-1 bg-[linear-gradient(90deg,var(--color-cobre)_0%,var(--color-laguna)_55%,color-mix(in_srgb,var(--color-obsidiana),white_20%)_100%)]" />
          <div className="grid gap-4 md:grid-cols-3">
            {predictiveCards.map((card, index) => (
              <article
                key={card.title}
                className={cn(
                  "relative overflow-hidden border p-4 sm:p-5",
                  card.accent,
                  index === 1 && "md:-translate-y-2",
                )}
              >
                <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-[color-mix(in_srgb,var(--color-obsidiana),white_28%)]">
                  {card.step}
                </p>
                <h3 className="mt-3 font-display text-[1.7rem] leading-[0.98] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                  {card.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                  {card.body}
                </p>
              </article>
            ))}
          </div>
          <p className="mt-5 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-4 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_16%)]">
            Señales visibles:{" "}
            <span className="text-[var(--color-obsidiana)]">
              {topSignals.map((signal) => signal.label).join(" · ")}
            </span>
          </p>
        </div>
      </section>

      <section className="grid gap-8 bg-[color-mix(in_srgb,var(--color-piedra-profunda),white_24%)] px-5 py-12 lg:grid-cols-[1fr_auto] lg:items-end lg:px-8 lg:py-16">
        <div className="space-y-4">
          <h2 className="max-w-4xl font-display text-5xl leading-[0.9] tracking-[-0.06em] text-[var(--color-obsidiana)] md:text-6xl">
            Lleva esta lectura a <span className="text-[var(--color-cobre)]">escenarios</span>
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
            Ahora que ves de dónde sale la predicción, explora cómo cambian los precios cuando
            se mueve la demanda, el clima y el contexto urbano.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <HomeActionLink href="/escenarios" className="rounded-none px-5 py-3">
            Ver escenarios
          </HomeActionLink>
          <HomeActionLink href="/dashboard" variant="secondary" className="rounded-none px-5 py-3">
            Abrir dashboard
          </HomeActionLink>
        </div>
      </section>
    </div>
  );
}

function formatModelName(value: string): string {
  const normalized = value.toLowerCase();

  if (normalized === "xgboost") {
    return "XGBoost";
  }

  if (normalized === "dummy_mean") {
    return "Promedio base";
  }

  if (normalized === "random_forest") {
    return "Random Forest";
  }

  return value;
}

function getFallbackSignals(): HowItWorksSnapshot["topSignals"] {
  return [
    { label: "Distancia", score: 0 },
    { label: "Demanda", score: 0 },
    { label: "Clima", score: 0 },
    { label: "Tráfico y hora", score: 0 },
  ];
}

function getSignalDescription(label: string): string {
  switch (label) {
    case "Distancia":
      return "Ayuda a comparar trayectos largos y cortos.";
    case "Demanda":
      return "Muestra cuándo el precio sube por mayor presión.";
    case "Clima":
      return "Añade contexto cuando lluvia, temperatura o nubosidad cambian la lectura.";
    case "Tráfico y hora":
      return "Sitúa cada escenario dentro del ritmo de la ciudad.";
    default:
      return "Suma contexto para abrir comparaciones públicas y entendibles.";
  }
}

function HowItWorksHeroWaves(): React.ReactElement {
  return (
    <svg
      className="h-full w-full"
      viewBox="0 0 1200 520"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d="M646 134C714 116 770 114 858 146C924 170 973 176 1044 160C1103 147 1151 136 1200 151"
        stroke="rgba(178,115,64,0.12)"
        strokeWidth="18"
        strokeLinecap="round"
      />
      <path
        d="M644 170C712 152 770 149 858 181C924 205 973 211 1044 195C1103 182 1151 171 1200 186"
        stroke="rgba(178,115,64,0.08)"
        strokeWidth="18"
        strokeLinecap="round"
      />
      <path
        d="M0 392C102 347 193 342 302 380C374 406 444 414 516 402"
        stroke="rgba(178,115,64,0.08)"
        strokeWidth="14"
        strokeLinecap="round"
      />
      <path
        d="M0 430C102 385 193 380 302 418C374 444 444 452 516 440"
        stroke="rgba(178,115,64,0.06)"
        strokeWidth="14"
        strokeLinecap="round"
      />
    </svg>
  );
}
