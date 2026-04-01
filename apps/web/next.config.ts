import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: "/metodologia",
        destination: "/como-funciona",
        permanent: true,
      },
      {
        source: "/laboratorio-modelo",
        destination: "/escenarios",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
