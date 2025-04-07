import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 1️⃣ Load all env vars for this mode (e.g. .env, .env.development, .env.local)
  const env = loadEnv(mode, process.cwd(), "");

  return {
    // 2️⃣ Inject them into your client code as `process.env.*`
    define: {
      "process.env": env,
    },
    plugins: [react()],
  };
});
