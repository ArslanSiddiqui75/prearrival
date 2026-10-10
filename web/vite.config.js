import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Served by api.py at "/" from web/dist. In dev, the API and fixtures come from the FastAPI server.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/fixtures": "http://localhost:8000",
    },
  },
});
