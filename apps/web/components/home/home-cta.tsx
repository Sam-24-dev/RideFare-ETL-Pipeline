import { HomeActionLink } from "./home-action-link";

export function HomeCta(): React.ReactElement {
  return (
    <section className="grid gap-8 bg-[color-mix(in_srgb,var(--color-piedra-profunda),white_24%)] px-5 py-12 lg:grid-cols-[1fr_auto] lg:items-end lg:px-8 lg:py-16">
      <div className="space-y-4">
        <h2 className="max-w-4xl font-display text-6xl leading-[0.88] tracking-[-0.06em] text-[var(--color-obsidiana)]">
          Explora la ciudad
          <br />
          desde sus <span className="text-[var(--color-cobre)]">señales</span>.
        </h2>
        <p className="max-w-2xl text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
          RideFare reúne dashboard, proceso visible y escenarios en una experiencia pública para
          leer precios, demanda y comportamiento urbano.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <HomeActionLink href="/dashboard" className="rounded-none px-5 py-3">
          Abrir dashboard
        </HomeActionLink>
        <HomeActionLink href="/escenarios" variant="secondary" className="rounded-none px-5 py-3">
          Ver escenarios
        </HomeActionLink>
      </div>
    </section>
  );
}
