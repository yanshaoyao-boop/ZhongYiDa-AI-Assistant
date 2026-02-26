import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'
import router from './router'
import { Plus, Send, FileBox, Database, UploadCloud } from 'lucide-vue-next'

const app = createApp(App)
app.use(router)

// Register some icons globally
app.component('IconPlus', Plus)
app.component('IconSend', Send)
app.component('IconFileBox', FileBox)
app.component('IconDatabase', Database)
app.component('IconUpload', UploadCloud)

app.mount('#app')
