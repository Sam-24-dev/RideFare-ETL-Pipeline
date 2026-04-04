export const siteConfig = {
  name: "RideFare",
  url: "https://ride-fare-etl-pipeline-web.vercel.app",
  title: "RideFare | Pricing intelligence para movilidad urbana",
  description:
    "Lectura pública de tarifas urbanas creada con data engineering, modelado temporal y una experiencia editorial en español.",
  socialTitle: "RideFare",
  socialKicker: "Pricing intelligence para movilidad urbana",
  socialDescription:
    "Producto híbrido de analytics engineering, machine learning y frontend editorial desplegado en Vercel.",
  author: {
    name: "Samir Caizapasto",
    portfolio: "https://portafolio-samir-tau.vercel.app/",
  },
  keywords: [
    "RideFare",
    "pricing intelligence",
    "urban mobility analytics",
    "DuckDB",
    "dbt",
    "XGBoost",
    "Next.js",
    "Vercel",
  ],
} as const;

export const brandPalette = {
  stone: "#F5F0E7",
  obsidian: "#18212B",
  copper: "#B97740",
  copperDark: "#8C582E",
  lagoon: "#2E6C87",
  border: "rgba(24, 33, 43, 0.14)",
} as const;
