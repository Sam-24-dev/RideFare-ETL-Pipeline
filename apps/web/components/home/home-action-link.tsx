import Link from "next/link";

import { cn } from "@/lib/utils";

type HomeActionLinkProps = {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
  className?: string;
};

export function HomeActionLink({
  href,
  children,
  variant = "primary",
  className,
}: HomeActionLinkProps): React.ReactElement {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap border text-[11px] font-medium uppercase tracking-[0.22em] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]",
        variant === "primary"
          ? "border-[var(--color-cobre-oscuro)] bg-[var(--color-cobre-oscuro)] shadow-[0_14px_42px_rgba(125,76,37,0.16)] hover:bg-[color-mix(in_srgb,var(--color-cobre-oscuro),white_10%)] hover:border-[color-mix(in_srgb,var(--color-cobre-oscuro),white_10%)]"
          : "border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-transparent text-[var(--color-obsidiana)] hover:border-[var(--color-laguna)] hover:bg-white/90",
        className,
      )}
      style={variant === "primary" ? { color: "#f4efe7" } : undefined}
    >
      {children}
    </Link>
  );
}
