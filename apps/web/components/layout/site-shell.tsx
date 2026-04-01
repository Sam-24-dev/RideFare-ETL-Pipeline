import type { ReactNode } from "react";
import Link from "next/link";

import { SiteNavigation } from "@/components/layout/site-navigation";

type SiteShellProps = {
  children: ReactNode;
};

export function SiteShell({ children }: SiteShellProps): React.ReactElement {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--color-piedra)] text-[var(--color-obsidiana)]">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(125deg,rgba(13,39,59,0.05),transparent_24%,rgba(178,115,64,0.08)_44%,transparent_64%),radial-gradient(circle_at_top_left,rgba(178,115,64,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(31,90,126,0.14),transparent_36%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:radial-gradient(circle_at_1px_1px,var(--color-obsidiana)_1px,transparent_0)] [background-size:24px_24px]" />
      <div className="relative mx-auto flex min-h-screen max-w-[92rem] flex-col px-4 pb-12 pt-4 md:px-8">
        <SiteNavigation />
        <main className="flex-1 pt-10 md:pt-14">{children}</main>
        <footer className="mt-20 border-t border-[var(--color-borde)] py-8 text-sm text-[var(--color-pizarra)]">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-medium text-[var(--color-obsidiana)]">RideFare</p>
              <p>Pricing intelligence, analytics engineering y modelado reproducible.</p>
            </div>
            <div className="flex flex-wrap gap-4">
              <Link className="transition-colors hover:text-[var(--color-cobre)]" href="/">
                Inicio
              </Link>
              <Link className="transition-colors hover:text-[var(--color-cobre)]" href="/dashboard">
                Dashboard
              </Link>
              <Link className="transition-colors hover:text-[var(--color-cobre)]" href="/como-funciona">
                Cómo funciona
              </Link>
              <Link className="transition-colors hover:text-[var(--color-cobre)]" href="/escenarios">
                Escenarios
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
