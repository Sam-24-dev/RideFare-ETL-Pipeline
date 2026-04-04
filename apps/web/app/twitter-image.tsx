import { ImageResponse } from "next/og";

import { RideFareSocialCard } from "@/lib/social-card";
import { siteConfig } from "@/lib/site-metadata";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

export const alt = `${siteConfig.name} Twitter preview`;

export default function TwitterImage(): ImageResponse {
  return new ImageResponse(
    (
      <RideFareSocialCard
        eyebrow="Portfolio híbrido"
        headline={siteConfig.socialTitle}
        body="Analytics engineering, machine learning y una interfaz editorial en español para pricing intelligence."
      />
    ),
    {
      ...size,
    },
  );
}
