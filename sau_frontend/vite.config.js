import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // Electron 需要使用相对路径
  base: './',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 移除自动导入，改用@use语法
      }
    }
  },
  server: {
    port: 5173,
    open: false, // Electron 模式下不自动打开浏览器
    proxy: {
      // AI 模块接口保持 /api/ai 前缀
      '/api/ai': {
        target: 'http://127.0.0.1:5409',
        changeOrigin: true
      },
      // 其他 /api 请求去掉前缀转发到后端
      '/api': {
        target: 'http://127.0.0.1:5409',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          elementPlus: ['element-plus'],
          utils: ['axios']
        }
      }
    }
  }
})
