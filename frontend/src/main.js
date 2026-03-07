import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'
import router from './router'
import {
  Plus, Send, FileBox, Database, UploadCloud,
  Image, Menu, X, XCircle, Square,
  Users, Building, Trash2, Edit
} from 'lucide-vue-next'

import { createPinia } from 'pinia'
import axios from 'axios'



const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize Auth state from localStorage
import { useAuthStore } from './store/auth'
const auth = useAuthStore()
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

app.mount('#app')
