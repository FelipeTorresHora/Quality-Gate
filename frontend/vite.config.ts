import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }
          if (id.includes("recharts") || id.includes("d3-")) {
            return "recharts";
          }
          if (id.includes("react-router") || id.includes("@remix-run/router")) {
            return "router";
          }
          if (
            id.includes("/react-dom/") ||
            id.includes("/react/") ||
            id.includes("scheduler")
          ) {
            return "react-vendor";
          }
        }
      }
    }
  }
});
