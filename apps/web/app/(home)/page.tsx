import type { Metadata } from "next";

import { HomeCta } from "@/components/home/home-cta";
import { HomeHero } from "@/components/home/home-hero";
import { HomeModules } from "@/components/home/home-modules";
import { loadHomeSnapshot } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Inicio",
  description:
    "RideFare presenta inteligencia de tarifas urbanas como un producto público: datos, arquitectura y modelado en una sola experiencia editorial.",
};

export default async function HomePage(): Promise<React.ReactElement> {
  const snapshot = await loadHomeSnapshot();
  const data = snapshot.status === "ready" ? snapshot.data : null;
  const missingMessage = snapshot.status === "missing" ? snapshot.message : undefined;

  return (
    <div className="space-y-16 pb-12 md:space-y-20 md:pb-20">
      <HomeHero snapshot={data} missingMessage={missingMessage} />
      <HomeModules />
      <HomeCta />
    </div>
  );
}
