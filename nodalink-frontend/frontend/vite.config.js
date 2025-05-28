import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false, // Disable sourcemaps for production
    minify: 'terser',
    target: 'esnext', // Modern target for better tree-shaking
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true
      }
    },
    rollupOptions: {
      external: [],
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'element-icons': ['@element-plus/icons-vue'],
          'vue-vendor': ['vue', 'vue-router', 'pinia']
        }
      }
    }
  },
  optimizeDeps: {
    include: ['element-plus', '@element-plus/icons-vue', 'vue', 'vue-router', 'pinia']
  },
  // Better compatibility with Alpine Linux containers
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false
  }
});
