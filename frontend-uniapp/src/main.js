import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const initializeMpRuntime = async (pinia) => {
  try {
    const [{ installGlobalErrorLogging }, { useAuthStore }, apiModule] = await Promise.all([
      import('./utils/error-logger'),
      import('./store/auth'),
      import('./utils/api'),
    ])

    apiModule.ensureApiBaseConfigured()
    installGlobalErrorLogging()
    useAuthStore(pinia).initAuth()
  } catch (error) {
    console.error('[mp-bootstrap]', error)
  }
}

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()

  app.use(pinia)

  // #ifdef MP-WEIXIN
  uni.onAppShow(() => {
    void initializeMpRuntime(pinia)
  })
  // #endif

  // #ifndef MP-WEIXIN
  void initializeMpRuntime(pinia)
  // #endif

  return {
    app,
    pinia,
  }
}
