import type { Metadata } from "next";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { EmptyState } from "@/components/layout/empty-state";
import { PageHero } from "@/components/layout/page-hero";
import { loadDashboardPayload } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Lectura pública de tarifas, volumen y clima sobre los marts exportados por RideFare.",
};

export default async function DashboardPage(): Promise<React.ReactElement> {
  const dashboard = await loadDashboardPayload();

  return (
    <div className="space-y-10">
      <PageHero
        eyebrow="Dashboard"
        title="Lectura pública de precio, volumen y contexto urbano"
        description="Esta superficie usa agregaciones estáticas exportadas desde DuckDB y dbt. La experiencia es pública, rápida y no depende de llamadas a APIs en runtime."
      />

      {dashboard.status === "ready" ? (
        <DashboardView payload={dashboard.data} />
      ) : (
        <EmptyState
          title="Todavía no hay dataset analítico para el dashboard"
          message={dashboard.message}
        />
      )}
    </div>
  );
}
