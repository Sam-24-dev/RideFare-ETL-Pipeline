import * as React from "react";

import { brandPalette, siteConfig } from "@/lib/site-metadata";

type RideFareSocialCardProps = {
  eyebrow: string;
  headline: string;
  body: string;
};

export function RideFareSocialCard({
  eyebrow,
  headline,
  body,
}: RideFareSocialCardProps): React.ReactElement {
  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        height: "100%",
        background: brandPalette.stone,
        color: brandPalette.obsidian,
        fontFamily: '"IBM Plex Sans", Arial, sans-serif',
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: "40px",
          border: `1px solid ${brandPalette.border}`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 12% 18%, rgba(185, 119, 64, 0.14), transparent 34%), radial-gradient(circle at 88% 26%, rgba(46, 108, 135, 0.12), transparent 28%)",
        }}
      />
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
          padding: "84px 86px",
          gap: "56px",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            display: "flex",
            width: "292px",
            height: "292px",
            borderRadius: "68px",
            background: brandPalette.obsidian,
            border: `2px solid rgba(185, 119, 64, 0.55)`,
            color: brandPalette.stone,
            position: "relative",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 22px 44px rgba(24, 33, 43, 0.12)",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "28px",
              right: "28px",
              width: "28px",
              height: "28px",
              borderRadius: "999px",
              background: brandPalette.lagoon,
            }}
          />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              fontSize: "140px",
              fontFamily: '"Cormorant Garamond", Georgia, serif',
              letterSpacing: "-0.08em",
              lineHeight: 1,
            }}
          >
            RF
          </div>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "26px",
            width: "620px",
          }}
        >
          <div
            style={{
              display: "flex",
              textTransform: "uppercase",
              letterSpacing: "0.32em",
              fontSize: "20px",
              color: brandPalette.copperDark,
              fontFamily: '"IBM Plex Sans", Arial, sans-serif',
            }}
          >
            {eyebrow}
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div
              style={{
                display: "flex",
                fontSize: "86px",
                lineHeight: 1.02,
                letterSpacing: "-0.06em",
                fontFamily: '"Cormorant Garamond", Georgia, serif',
              }}
            >
              {headline}
            </div>
            <div
              style={{
                display: "flex",
                fontSize: "34px",
                lineHeight: 1.34,
                color: "rgba(24, 33, 43, 0.78)",
                fontFamily: '"IBM Plex Sans", Arial, sans-serif',
              }}
            >
              {body}
            </div>
          </div>
          <div
            style={{
              display: "flex",
              gap: "16px",
              alignItems: "center",
              fontSize: "20px",
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: brandPalette.copper,
              fontFamily: '"IBM Plex Sans", Arial, sans-serif',
            }}
          >
            <span>{siteConfig.name}</span>
            <span style={{ color: "rgba(24, 33, 43, 0.3)" }}>•</span>
            <span>DuckDB • dbt • XGBoost • Next.js</span>
          </div>
        </div>
      </div>
    </div>
  );
}
