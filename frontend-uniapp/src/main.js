import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { useAuthStore } from './store/auth'
import { installGlobalErrorLogging } from './utils/error-logger'

// 导入所有之前引入的全局图标库
import {
    Plus, Send, FileBox, Database, UploadCloud,
    Image, Menu, X, XCircle, Square,
    Users, Building, Trash2, Edit, Zap, ShieldCheck
} from 'lucide-vue-next'
import { ensureApiBaseConfigured } from './utils/api'

export function createApp() {
    const app = createSSRApp(App)
    const pinia = createPinia()

    app.use(pinia)
    ensureApiBaseConfigured()
    installGlobalErrorLogging()

    // Initialize Auth state
    const auth = useAuthStore(pinia)
    auth.initAuth()

    // Register some icons globally
    app.component('IconPlus', Plus)
    app.component('IconSend', Send)
    app.component('IconFileBox', FileBox)
    app.component('IconDatabase', Database)
    app.component('IconUpload', UploadCloud)
    app.component('IconImage', Image)
    app.component('IconMenu', Menu)
    app.component('IconX', X)
    app.component('IconXCircle', XCircle)
    app.component('IconSquare', Square)
    app.component('IconUsers', Users)
    app.component('IconBuilding', Building)
    app.component('IconTrash', Trash2)
    app.component('IconEdit', Edit)
    app.component('IconZap', Zap)
    app.component('IconShieldCheck', ShieldCheck)

    return {
        app,
        pinia
    }
}
