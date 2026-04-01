import type { ReactNode } from "react";

import { HomeBackdrop } from "@/components/home/home-visuals";
import { HomeFooter } from "@/components/home/home-footer";
import { HomeNavigation } from "@/components/home/home-navigation";

type HomeShellProps = {
  children: ReactNode;
};

export function HomeShell({ children }: HomeShellProps): React.ReactElement {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--color-piedra)] text-[var(--color-obsidiana)]">
      <HomeBackdrop />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(178,115,64,0.1),transparent_28%),radial-gradient(circle_at_92%_14%,rgba(31,90,126,0.08),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.55),rgba(255,255,255,0)_42%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-[92rem] flex-col px-4 pb-10 pt-4 sm:px-6 lg:px-10">
        <HomeNavigation />
        <main className="flex-1 pt-8 md:pt-12">{children}</main>
        <HomeFooter />
      </div>
    </div>
  );
}
