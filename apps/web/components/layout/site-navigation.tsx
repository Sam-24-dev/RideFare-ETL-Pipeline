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
  { href: "/dashboard", label: "Dashboard" },
  { href: "/como-funciona", label: "Cómo funciona" },
  { href: "/escenarios", label: "Escenarios" },
];

export function SiteNavigation(): React.ReactElement {
  const pathname = usePathname();

  return (
    <header className="border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_24%)]/90 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4 py-4">
        <Link
          href="/"
          aria-label="Ir al inicio de RideFare"
          title="Ir al inicio"
          className="group inline-flex min-w-0 flex-col items-start focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]"
        >
          <span className="relative font-display text-2xl tracking-[-0.05em] text-[var(--color-obsidiana)] transition-colors duration-200 group-hover:text-[var(--color-cobre-oscuro)] group-focus-visible:text-[var(--color-cobre-oscuro)] after:absolute after:-bottom-0.5 after:left-0 after:h-px after:w-full after:origin-left after:scale-x-0 after:bg-[color-mix(in_srgb,var(--color-cobre),white_6%)] after:transition-transform after:duration-200 group-hover:after:scale-x-100 group-focus-visible:after:scale-x-100">
            RideFare
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "text-[11px] font-medium uppercase tracking-[0.22em] transition-colors",
                pathname === item.href
                  ? "text-[var(--color-cobre)]"
                  : "text-[color-mix(in_srgb,var(--color-obsidiana),white_24%)] hover:text-[var(--color-obsidiana)]",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button
                aria-label="Abrir navegación principal"
                variant="secondary"
                size="compact"
                className="rounded-none border-[var(--color-borde)] bg-white/70 text-[var(--color-obsidiana)]"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="rounded-none border-l border-[var(--color-borde)] bg-[var(--color-piedra)]"
            >
              <div className="mt-10 space-y-6">
                <div className="space-y-2">
                  <SheetTitle>RideFare</SheetTitle>
                  <SheetDescription>
                    Navegación principal del producto público.
                  </SheetDescription>
                </div>
                <nav className="grid gap-2">
                  <Link
                    href="/"
                    className="border border-[var(--color-cobre)] bg-[color-mix(in_srgb,var(--color-cobre),white_84%)] px-4 py-3 text-sm uppercase tracking-[0.18em] text-[var(--color-cobre-oscuro)]"
                  >
                    Inicio
                  </Link>
                  {navigationItems.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "border px-4 py-3 text-sm uppercase tracking-[0.18em] transition-colors",
                        pathname === item.href
                          ? "border-[var(--color-cobre)] bg-[color-mix(in_srgb,var(--color-cobre),white_84%)] text-[var(--color-cobre-oscuro)]"
                          : "border-[var(--color-borde)] bg-white/75 text-[var(--color-pizarra)] hover:text-[var(--color-obsidiana)]",
                      )}
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
    </header>
  );
}
