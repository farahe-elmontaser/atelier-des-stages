import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Toutes les requetes vers /api sont redirigees vers le backend FastAPI (port 8000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
