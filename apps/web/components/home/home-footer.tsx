import { HomeActionLink } from "./home-action-link";

export function HomeFooter(): React.ReactElement {
  return (
    <footer className="mt-20 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] pt-6">
      <div className="flex flex-col gap-4 text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)] md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <p className="font-display text-xl tracking-[-0.04em] text-[var(--color-obsidiana)]">
            RideFare
          </p>
          <p className="max-w-xl">
            Una forma pública de entender tarifas urbanas, ver cómo se construyen y explorar
            escenarios del producto.
          </p>
        </div>
        <HomeActionLink
          href="https://github.com/Sam-24-dev/RideFare-ETL-Pipeline"
          className="rounded-none px-4 py-2"
        >
          Repositorio
        </HomeActionLink>
      </div>
    </footer>
  );
}
