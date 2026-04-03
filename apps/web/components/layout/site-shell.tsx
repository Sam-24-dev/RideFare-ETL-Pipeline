import type { ReactNode } from "react";
import Link from "next/link";

import { HomeBackdrop } from "@/components/home/home-visuals";
import { SiteNavigation } from "@/components/layout/site-navigation";

type SiteShellProps = {
  children: ReactNode;
};

export function SiteShell({ children }: SiteShellProps): React.ReactElement {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--color-piedra)] text-[var(--color-obsidiana)]">
      <HomeBackdrop />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(178,115,64,0.1),transparent_28%),radial-gradient(circle_at_92%_14%,rgba(31,90,126,0.08),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.55),rgba(255,255,255,0)_42%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-[92rem] flex-col px-4 pb-10 pt-4 sm:px-6 lg:px-10">
        <SiteNavigation />
        <main className="flex-1 pt-8 md:pt-12">{children}</main>
        <footer className="mt-16 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] py-6">
          <div className="max-w-md space-y-1 text-sm text-[var(--color-pizarra)]">
            <Link
              href="/"
              aria-label="Ir al inicio de RideFare"
              title="Ir al inicio"
              className="group inline-flex flex-col items-start focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]"
            >
              <span className="relative font-display text-2xl tracking-[-0.04em] text-[var(--color-obsidiana)] transition-colors duration-200 group-hover:text-[var(--color-cobre-oscuro)] group-focus-visible:text-[var(--color-cobre-oscuro)] after:absolute after:-bottom-0.5 after:left-0 after:h-px after:w-full after:origin-left after:scale-x-0 after:bg-[color-mix(in_srgb,var(--color-cobre),white_6%)] after:transition-transform after:duration-200 group-hover:after:scale-x-100 group-focus-visible:after:scale-x-100">
                RideFare
              </span>
            </Link>
            <p>Lectura pública de tarifas urbanas.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
