import type { Metadata } from "next";

import { EmptyState } from "@/components/layout/empty-state";
import { ScenariosView } from "@/components/scenarios/scenarios-view";
import { loadModelLabPayload } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Escenarios",
  description:
    "Proyecciones cartográficas de tarifas basadas en variables dinámicas y predicción explicable.",
};

export default async function ScenariosPage(): Promise<React.ReactElement> {
  const modelLab = await loadModelLabPayload();

  if (modelLab.status !== "ready") {
    return (
      <EmptyState
        title="Todavía no hay escenarios exportados"
        message={modelLab.message}
      />
    );
  }

  return <ScenariosView payload={modelLab.data} />;
}
