import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// Vite 配置：Tauri 前端（固定 1420 端口——tauri.conf.json devUrl 对齐；构建出 dist/）
export default defineConfig({
  plugins: [vue()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      // cargo 构建产物（src-tauri/target）在监视树内会 EBUSY 崩 vite——排除
      ignored: ["**/src-tauri/**", "**/dist/**"],
    },
  },
  build: {
    target: "chrome105",
    outDir: "dist",
  },
});
