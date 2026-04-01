import type { Metadata } from "next";

import { EmptyState } from "@/components/layout/empty-state";
import { PageHero } from "@/components/layout/page-hero";
import { ModelLabView } from "@/components/model-lab/model-lab-view";
import { loadModelLabPayload } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Escenarios",
  description:
    "Comparación, explicabilidad y simulación estática sobre los artefactos ML exportados por RideFare.",
};

export default async function ScenariosPage(): Promise<React.ReactElement> {
  const modelLab = await loadModelLabPayload();

  return (
    <div className="space-y-10">
      <PageHero
        eyebrow="Escenarios"
        title="Comparación, explicabilidad y simulación sobre un mismo run"
        description="Esta superficie consume directamente los artefactos exportados por el pipeline: benchmark, SHAP, predicciones de holdout y escenarios precomputados para lectura pública."
      />

      {modelLab.status === "ready" ? (
        <ModelLabView payload={modelLab.data} />
      ) : (
        <EmptyState
          title="Todavía no hay escenarios exportados"
          message={modelLab.message}
        />
      )}
    </div>
  );
}
