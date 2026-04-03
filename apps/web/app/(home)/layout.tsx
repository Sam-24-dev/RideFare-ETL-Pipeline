import type { ReactNode } from "react";

import { HomeShell } from "@/components/home/home-shell";

export default function HomeLayout({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  return <HomeShell>{children}</HomeShell>;
}
