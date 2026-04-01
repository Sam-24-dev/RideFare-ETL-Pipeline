import { HomeActionLink } from "./home-action-link";
import {
  LabPreviewGraphic,
  MethodologyPreviewGraphic,
  TerminalPreviewGraphic,
} from "./home-visuals";

export function HomeModules(): React.ReactElement {
  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-obsidiana)]">
            Ecosistema de producto
          </p>
          <h2 className="font-display text-5xl leading-[0.92] tracking-[-0.05em] text-[var(--color-obsidiana)]">
            Tres formas de entender
            <br />
            el mismo sistema.
          </h2>
        </div>
        <p className="max-w-md text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
          RideFare no se recorre en una sola vista. Puedes entrar por el análisis, por el proceso o
          por la simulación.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <article className="group grid gap-6 border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_26%)] p-4 transition-transform duration-300 hover:-translate-y-1 md:grid-cols-[1.18fr_0.82fr] md:p-5">
          <div className="min-h-[16rem] overflow-hidden border border-[rgba(255,255,255,0.08)] bg-[var(--color-obsidiana)]">
            <TerminalPreviewGraphic />
          </div>
          <div className="flex flex-col gap-5">
            <div className="space-y-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-obsidiana)]">
                Entrada principal
              </p>
              <h3 className="font-display text-4xl leading-[0.95] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                Dashboard
              </h3>
              <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                Explora rutas, clima, precios y ritmo horario en una lectura pública de la
                movilidad urbana.
              </p>
            </div>
            <div className="border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-4">
              <HomeActionLink href="/dashboard" className="rounded-none px-5 py-3">
                Abrir dashboard
              </HomeActionLink>
            </div>
          </div>
        </article>

        <article className="group border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_40%)] p-5 transition-transform duration-300 hover:-translate-y-1">
          <div className="aspect-[16/10] overflow-hidden border border-[color-mix(in_srgb,var(--color-cobre),white_64%)] bg-white/60">
            <MethodologyPreviewGraphic />
          </div>
          <div className="mt-5 space-y-4">
            <div className="space-y-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-obsidiana)]">
                Proceso visible
              </p>
              <h3 className="font-display text-4xl leading-[0.95] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                Cómo funciona
              </h3>
              <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                Descubre cómo se limpian, validan y transforman los datos antes del análisis y el
                modelo.
              </p>
            </div>
            <div className="border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-4">
              <HomeActionLink href="/como-funciona" className="rounded-none px-5 py-3">
                Ver cómo funciona
              </HomeActionLink>
            </div>
          </div>
        </article>
      </div>

      <article className="group grid gap-6 border border-[color-mix(in_srgb,var(--color-cobre),white_34%)] bg-[linear-gradient(135deg,#151311_0%,#1e1713_55%,#2b1f18_100%)] px-5 py-5 text-[#f4efe7] shadow-[0_24px_90px_rgba(20,14,10,0.2)] transition-transform duration-300 hover:-translate-y-1 lg:grid-cols-[0.82fr_1.18fr] lg:px-6">
        <div className="flex flex-col gap-5 self-start">
          <div className="space-y-3">
            <p className="text-[10px] uppercase tracking-[0.24em] text-[rgba(244,239,231,0.82)]">
              Capa avanzada
            </p>
            <h3 className="font-display text-5xl leading-[0.9] tracking-[-0.05em] text-[#f4efe7]">
              Escenarios
            </h3>
            <p className="max-w-md text-sm leading-7 text-[rgba(244,239,231,0.9)]">
              Compara el modelo, interpreta variables clave y prueba simulaciones sin salir del
              producto.
            </p>
          </div>
          <div className="border-t border-[rgba(244,239,231,0.12)] pt-4">
            <HomeActionLink href="/escenarios" className="rounded-none px-5 py-3">
              Explorar escenarios
            </HomeActionLink>
          </div>
        </div>
        <div className="min-h-[18rem] overflow-hidden border border-[rgba(244,239,231,0.1)] bg-black/12">
          <LabPreviewGraphic />
        </div>
      </article>
    </section>
  );
}
