import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type CardShellProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  accent?: "default" | "cobre" | "laguna";
};

export function CardShell({
  children,
  className,
  accent = "default",
  ...props
}: CardShellProps): React.ReactElement {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[2rem] border border-[var(--color-borde)] bg-white/72 shadow-[0_20px_70px_rgba(17,25,39,0.08)] backdrop-blur-sm",
        accent === "cobre" &&
          "border-[color-mix(in_srgb,var(--color-cobre),white_54%)] shadow-[0_24px_80px_rgba(175,103,57,0.12)]",
        accent === "laguna" &&
          "border-[color-mix(in_srgb,var(--color-laguna),white_50%)] shadow-[0_24px_80px_rgba(32,87,133,0.12)]",
        className,
      )}
      {...props}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(202,139,92,0.16),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(32,87,133,0.14),transparent_35%)]" />
      <div className="relative">{children}</div>
    </div>
  );
}
