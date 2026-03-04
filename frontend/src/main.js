import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'
import router from './router'
import { 
  Plus, Send, FileBox, Database, UploadCloud, 
  Image, Menu, X, XCircle, Square 
} from 'lucide-vue-next'

const app = createApp(App)
app.use(router)

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

app.mount('#app')
