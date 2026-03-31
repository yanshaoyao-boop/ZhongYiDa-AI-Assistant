import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'

const packageJsonRaw = readFileSync(new URL('./package.json', import.meta.url), 'utf8')
const packageJson = JSON.parse(packageJsonRaw.replace(/^\uFEFF/, ''))

const appVersion = packageJson.version || '0.0.0'
const buildTimestamp = new Date().toISOString()
const versionLabel = appVersion

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  define: {
    __APP_VERSION__: JSON.stringify(versionLabel),
    __APP_BUILD_TIME__: JSON.stringify(buildTimestamp)
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '127.0.0.1',
    port: 5300,
    proxy: {
      // 开发环境：将所有 /api 请求代理到后端，避免硬编码地址和跨域问题
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
})
