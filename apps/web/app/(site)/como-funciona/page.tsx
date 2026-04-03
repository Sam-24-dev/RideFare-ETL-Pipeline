import type { Metadata } from "next";

import { HowItWorksView } from "@/components/how-it-works/how-it-works-view";
import { loadHowItWorksSnapshot } from "@/lib/data/loaders";

export const metadata: Metadata = {
  title: "Cómo funciona",
  description:
    "Cómo RideFare convierte datos urbanos en una lectura pública clara, confiable y explorable.",
};

export default async function HowItWorksPage(): Promise<React.ReactElement> {
  const snapshot = await loadHowItWorksSnapshot();

  return <HowItWorksView snapshot={snapshot.status === "ready" ? snapshot.data : null} />;
}
