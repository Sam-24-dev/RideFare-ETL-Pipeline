import type { HomeSnapshot } from "@/lib/data/loaders";

import { HomeActionLink } from "./home-action-link";
import { HomeMetrics } from "./home-metrics";
import { HeroTerrainGraphic } from "./home-visuals";

type HomeHeroProps = {
  snapshot: HomeSnapshot | null;
  missingMessage?: string;
};

export function HomeHero({ snapshot, missingMessage }: HomeHeroProps): React.ReactElement {
  return (
    <section className="border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pb-10 md:pb-12">
      <div className="relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[color-mix(in_srgb,var(--color-piedra),white_22%)] shadow-[0_30px_100px_rgba(20,36,45,0.08)]">
        <div className="absolute inset-0 opacity-95">
          <HeroTerrainGraphic />
        </div>
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(251,247,241,0.97)_0%,rgba(251,247,241,0.95)_28%,rgba(251,247,241,0.68)_58%,rgba(251,247,241,0.28)_100%)]" />

        <div className="relative z-10 px-6 py-6 sm:px-8 md:px-9 md:py-7 lg:px-12 lg:py-8 lg:pb-44">
          <div className="max-w-[58rem] space-y-5">
            <div className="space-y-4">
              <h1 className="max-w-[46rem] font-display text-5xl leading-[0.88] tracking-[-0.06em] text-[var(--color-obsidiana)] sm:text-[4.4rem] lg:text-[4.75rem]">
                El <span className="text-[var(--color-cobre)]">valor</span> de la
                <br />
                movilidad urbana
              </h1>
              <p className="max-w-[34rem] text-[1.05rem] leading-8 text-[var(--color-obsidiana)] md:text-[1.12rem]">
                Una plataforma pública para explorar cómo los viajes, el clima y el modelado ayudan
                a entender precios, demanda y comportamiento urbano.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <HomeActionLink href="/dashboard" className="rounded-none px-5 py-3">
                Ver dashboard
              </HomeActionLink>
              <HomeActionLink href="/como-funciona" variant="secondary" className="rounded-none px-5 py-3">
                Cómo funciona
              </HomeActionLink>
            </div>

            {missingMessage ? (
              <p className="max-w-[34rem] text-sm leading-6 text-[var(--color-obsidiana)]/72">
                {missingMessage}
              </p>
            ) : null}
          </div>
        </div>

        <div className="relative z-10 px-6 pb-6 sm:px-8 md:px-9 md:pb-7 lg:absolute lg:inset-x-12 lg:bottom-8 lg:px-0 lg:pb-0">
          <HomeMetrics snapshot={snapshot} variant="hero" />
        </div>
      </div>
    </section>
  );
}
