import { ImageResponse } from "next/og";

import { brandPalette } from "@/lib/site-metadata";

export const size = {
  width: 180,
  height: 180,
};

export const contentType = "image/png";

export default function AppleIcon(): ImageResponse {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
          background: brandPalette.obsidian,
          borderRadius: "46px",
          border: `6px solid rgba(185, 119, 64, 0.7)`,
          alignItems: "center",
          justifyContent: "center",
          color: brandPalette.stone,
          position: "relative",
          boxSizing: "border-box",
          fontFamily: "Georgia, serif",
          fontSize: 88,
          letterSpacing: "-0.12em",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 22,
            right: 22,
            width: 18,
            height: 18,
            borderRadius: 999,
            background: brandPalette.lagoon,
          }}
        />
        RF
      </div>
    ),
    {
      ...size,
    },
  );
}
