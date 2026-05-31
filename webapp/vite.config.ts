import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const API = "http://127.0.0.1:11024";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 11025,
    host: "127.0.0.1",
    proxy: {
      "/api": API,
      "/mcp": API,
      "/.well-known": API,
    },
  },
});
