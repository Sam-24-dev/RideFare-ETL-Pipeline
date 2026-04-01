import type { Metadata } from "next";

import { CardShell } from "@/components/layout/card-shell";
import { PageHero } from "@/components/layout/page-hero";
import { SectionHeader } from "@/components/layout/section-header";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = {
  title: "Cómo funciona",
  description:
    "Cómo RideFare transforma datos brutos en lecturas públicas, marts reproducibles y escenarios exportados.",
};

const layers = [
  {
    step: "01",
    title: "Rides + weather",
    body: "Rides y clima entran como fuentes visibles. Aquí empieza el control del dato, no una caja negra.",
  },
  {
    step: "02",
    title: "Validación e interim",
    body: "Pandera y Parquet fijan contratos, tipado y una capa intermedia reproducible.",
  },
  {
    step: "03",
    title: "Marts analíticos",
    body: "DuckDB y dbt separan limpieza, enriquecimiento y vistas listas para dashboard y escenarios.",
  },
  {
    step: "04",
    title: "Escenarios ML",
    body: "Baselines, XGBoost, holdout temporal, explicabilidad y artefactos versionados.",
  },
  {
    step: "05",
    title: "Producto web",
    body: "JSON estáticos tipados sostienen la Home, el dashboard y la exploración pública.",
  },
];

const stack = [
  ["Polars + Pandera", "Contratos y limpieza de entrada."],
  ["DuckDB + dbt", "Marts reproducibles y modelado local-first."],
  ["XGBoost + SHAP", "Escenarios, benchmark y explicabilidad."],
  ["Next.js + TypeScript", "Producto público rápido sobre artefactos exportados."],
];

const limits = [
  "La muestra versionada del repo sirve para probar el flujo, no para vender métricas finales.",
  "Los escenarios son precomputados; la app no ejecuta inferencia en vivo.",
  "Las señales visibles ayudan a leer el sistema, pero no prometen causalidad.",
];

export default function HowItWorksPage(): React.ReactElement {
  return (
    <div className="space-y-12">
      <PageHero
        eyebrow="Cómo funciona"
        title="Un proceso visible, no una caja negra de notebooks"
        description="Esta página traduce el rigor técnico a una lectura pública: cómo entran los datos, cómo se modelan y cómo terminan en superficies explorables sin depender de backend en runtime."
      />

      <section className="space-y-6">
        <SectionHeader
          eyebrow="Flujo"
          title="De fuente a producto"
          description="Cada capa tiene una responsabilidad clara para que RideFare sea entendible, reproducible y mantenible."
        />
        <div className="grid gap-4 xl:grid-cols-5">
          {layers.map((layer) => (
            <CardShell key={layer.step} className="p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-cobre)]">
                {layer.step}
              </p>
              <h2 className="mt-4 font-display text-3xl tracking-[-0.03em] text-[var(--color-obsidiana)]">
                {layer.title}
              </h2>
              <p className="mt-3 text-sm leading-7 text-[var(--color-pizarra)]">{layer.body}</p>
            </CardShell>
          ))}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <CardShell className="p-6">
          <SectionHeader
            eyebrow="Stack"
            title="Tecnología elegida por responsabilidad"
            description="Cada herramienta está donde aporta claridad real, no donde suena mejor en un portfolio."
          />
          <div className="mt-6 grid gap-3">
            {stack.map(([title, body]) => (
              <div
                key={title}
                className="rounded-[1.5rem] border border-[var(--color-borde)] bg-white/75 p-4"
              >
                <p className="font-medium text-[var(--color-obsidiana)]">{title}</p>
                <p className="mt-1 text-sm text-[var(--color-pizarra)]">{body}</p>
              </div>
            ))}
          </div>
        </CardShell>

        <CardShell accent="laguna" className="p-6">
          <SectionHeader
            eyebrow="Garantías"
            title="Qué valida el producto"
            description="La interfaz pública hereda contratos y límites desde el pipeline; no es solo una capa decorativa."
          />
          <div className="mt-6 space-y-3">
            {[
              "Contratos Pandera sobre las fuentes de entrada.",
              "Tests dbt sobre columnas clave y joins temporales.",
              "Evaluación con split temporal, no aleatorio.",
              "JSON públicos validados con zod en runtime.",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.5rem] border border-[var(--color-borde)] bg-white/70 p-4 text-sm leading-7 text-[var(--color-pizarra)]"
              >
                {item}
              </div>
            ))}
          </div>
        </CardShell>
      </section>

      <section className="space-y-6">
        <SectionHeader
          eyebrow="Límites"
          title="Qué no promete RideFare"
          description="La credibilidad también depende de explicar hasta dónde llegan los datos y los escenarios visibles."
        />
        <div className="grid gap-4 lg:grid-cols-3">
          {limits.map((limit) => (
            <CardShell key={limit} className="p-6">
              <Badge variant="laguna">Límite conocido</Badge>
              <p className="mt-4 text-sm leading-7 text-[var(--color-pizarra)]">{limit}</p>
            </CardShell>
          ))}
        </div>
      </section>
    </div>
  );
}
