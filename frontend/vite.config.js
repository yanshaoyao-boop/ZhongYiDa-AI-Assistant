import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'
import { execSync } from 'node:child_process'

const packageJson = JSON.parse(
  readFileSync(new URL('./package.json', import.meta.url), 'utf8')
)

const appVersion = packageJson.version || '0.0.0'
const buildTimestamp = new Date().toISOString()

let gitCommit = 'unknown'
try {
  gitCommit = execSync('git rev-parse --short HEAD', {
    cwd: fileURLToPath(new URL('..', import.meta.url)),
    stdio: ['ignore', 'pipe', 'ignore']
  })
    .toString()
    .trim()
} catch (error) {
  gitCommit = 'unknown'
}

const versionLabel = `${appVersion}-${gitCommit}`

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
