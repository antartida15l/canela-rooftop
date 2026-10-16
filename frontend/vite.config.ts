import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    // Service worker: la aplicación y los modelos de IA quedan en caché tras la primera carga.
    VitePWA({
      registerType: "autoUpdate",
      manifest: false,
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg}"],
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: ({ url }) => /\/(models|ort|mediapipe)\//.test(url.pathname),
            handler: "CacheFirst",
            options: {
              cacheName: "nb-ia-v1",
              cacheableResponse: { statuses: [200] },
              expiration: { maxEntries: 30 },
            },
          },
        ],
      },
    }),
  ],
  server: { port: 5173 },
  optimizeDeps: { exclude: ["onnxruntime-web"] },
  worker: { format: "es" },
  test: { environment: "jsdom" },
});
