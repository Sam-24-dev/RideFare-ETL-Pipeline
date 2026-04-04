import { ImageResponse } from "next/og";

import { RideFareSocialCard } from "@/lib/social-card";
import { siteConfig } from "@/lib/site-metadata";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

export const alt = `${siteConfig.name} social preview`;

export default function OpenGraphImage(): ImageResponse {
  return new ImageResponse(
    (
      <RideFareSocialCard
        eyebrow="Data product desplegado"
        headline={siteConfig.socialTitle}
        body={`${siteConfig.socialKicker}. ${siteConfig.socialDescription}`}
      />
    ),
    {
      ...size,
    },
  );
}
