import type { ReactNode } from "react";

import { SiteShell } from "@/components/layout/site-shell";

export default function PublicSiteLayout({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  return <SiteShell>{children}</SiteShell>;
}
