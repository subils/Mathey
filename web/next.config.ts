import type { NextConfig } from "next";

// La web s'exporta com a fitxers estàtics i la serveix la placa (brick web_ui
// d'App Lab, port 7000). No hi ha servidor Node: res d'API routes, accions de
// servidor ni middleware. Totes les dades venen de /api per fetch.
const nextConfig: NextConfig = {
  output: "export",
  // /practica -> /practica/index.html, que és el que sap servir la placa
  trailingSlash: true,
  // L'optimitzador d'imatges necessita servidor
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
