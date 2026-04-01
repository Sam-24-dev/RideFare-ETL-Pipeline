"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const navigationItems = [
  { href: "/", label: "Inicio" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/como-funciona", label: "Cómo funciona" },
  { href: "/escenarios", label: "Escenarios" },
];

export function SiteNavigation(): React.ReactElement {
  const pathname = usePathname();

  return (
    <header className="sticky top-4 z-40">
      <div className="rounded-full border border-[var(--color-borde)] bg-white/75 px-4 py-3 shadow-[0_16px_60px_rgba(17,25,39,0.08)] backdrop-blur-xl md:px-6">
        <div className="flex items-center justify-between gap-4">
          <Link className="flex min-w-0 items-center gap-3" href="/">
            <div className="flex h-11 w-11 items-center justify-center rounded-full border border-[var(--color-borde)] bg-[var(--color-obsidiana)] text-sm font-semibold uppercase tracking-[0.18em] text-white">
              RF
            </div>
            <div className="min-w-0">
              <p className="truncate font-display text-2xl tracking-[-0.04em] text-[var(--color-obsidiana)]">
                RideFare
              </p>
              <p className="hidden text-xs uppercase tracking-[0.22em] text-[var(--color-pizarra)] md:block">
                Data product en español
              </p>
            </div>
          </Link>

          <nav className="hidden items-center gap-2 md:flex">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                className={cn(
                  "rounded-full px-4 py-2 text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-[var(--color-obsidiana)] text-white"
                    : "text-[var(--color-pizarra)] hover:bg-[var(--color-laguna-suave)] hover:text-[var(--color-laguna)]",
                )}
                href={item.href}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button aria-label="Abrir navegación" size="compact" variant="secondary">
                  <Menu className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <div className="mt-10 space-y-6">
                  <div className="space-y-2">
                    <SheetTitle>RideFare</SheetTitle>
                    <SheetDescription>
                      Navegación principal del producto público.
                    </SheetDescription>
                  </div>
                  <nav className="grid gap-2">
                    {navigationItems.map((item) => (
                      <Link
                        key={item.href}
                        className={cn(
                          "rounded-2xl border px-4 py-3 text-base font-medium transition-colors",
                          pathname === item.href
                            ? "border-[var(--color-cobre)] bg-[color-mix(in_srgb,var(--color-cobre),white_82%)] text-[var(--color-cobre-oscuro)]"
                            : "border-[var(--color-borde)] bg-white/75 text-[var(--color-pizarra)] hover:border-[var(--color-laguna)] hover:text-[var(--color-laguna)]",
                        )}
                        href={item.href}
                      >
                        {item.label}
                      </Link>
                    ))}
                  </nav>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
