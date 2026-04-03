import type { Metadata } from "next";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { EmptyState } from "@/components/layout/empty-state";
import { loadDashboardPayload } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Lectura pública de tarifas, trayectos y clima sobre los artefactos exportados por RideFare.",
};

export default async function DashboardPage(): Promise<React.ReactElement> {
  const dashboard = await loadDashboardPayload();

  if (dashboard.status !== "ready") {
    return (
      <EmptyState
        title="Todavía no hay dataset analítico para el dashboard"
        message={dashboard.message}
      />
    );
  }

  return <DashboardView payload={dashboard.data} />;
}
