import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    proxy: {
      // 开发环境：将所有 /api 请求代理到后端，避免硬编码地址和跨域问题
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
})

