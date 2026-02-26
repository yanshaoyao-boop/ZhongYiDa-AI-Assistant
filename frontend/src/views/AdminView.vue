<template>
  <div class="admin-container">
    <header class="admin-header glass-panel">
      <h1><span class="gradient-text">仲易达</span> 智能助手后台管理</h1>
      <p>管理业务知识库与最新报价表数据</p>
    </header>
    
    <div class="admin-content">
      <!-- Document Upload Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconFileBox class="icon-lg text-blue" />
          <h2>企业制度与文档库</h2>
        </div>
        <p class="section-desc">上传 PDF、Word。上传后系统将自动进行分块并向量化存储，供大模型检索学习。</p>
        
        <div class="drop-zone" 
             @dragover.prevent="isDraggingDoc = true" 
             @dragleave.prevent="isDraggingDoc = false" 
             @drop.prevent="onDropDoc"
             :class="{'drag-active': isDraggingDoc}"
             @click="triggerDocSelect">
          <IconUpload class="upload-icon" />
          <p v-if="!docFile">点击或拖拽制度文档到此处 (PDF / Word)</p>
          <p v-else class="file-sel">{{ docFile.name }}</p>
          <input type="file" ref="docInput" style="display:none" @change="onDocSelected" accept=".pdf,.doc,.docx,.txt" />
        </div>
        
        <button class="btn-primary" :disabled="!docFile || docUploading" @click="uploadDocument">
          <span v-if="docUploading">正在解析并存入向量库...</span>
          <span v-else>上传并学习文档</span>
        </button>
        <div v-if="docMessage" class="status-msg" :class="docStatus">{{ docMessage }}</div>
      </section>

      <!-- Quotes Upload Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconDatabase class="icon-lg text-purple" />
          <h2>结构化报价表库</h2>
        </div>
        <p class="section-desc">上传 Excel 或 CSV 格式的最新报价表。大模型将在回答报价问题时查阅此处的数据。</p>
        
        <div class="drop-zone" 
             @dragover.prevent="isDraggingQuote = true" 
             @dragleave.prevent="isDraggingQuote = false" 
             @drop.prevent="onDropQuote"
             :class="{'drag-active': isDraggingQuote}"
             @click="triggerQuoteSelect">
          <IconUpload class="upload-icon" />
          <p v-if="!quoteFile">点击或拖拽报价表到此处 (Excel / CSV)</p>
          <p v-else class="file-sel">{{ quoteFile.name }}</p>
          <input type="file" ref="quoteInput" style="display:none" @change="onQuoteSelected" accept=".xlsx,.xls,.csv" />
        </div>
        
        <button class="btn-primary quote-btn" :disabled="!quoteFile || quoteUploading" @click="uploadQuote">
          <span v-if="quoteUploading">正在更新报价数据库...</span>
          <span v-else>更新系统报价表</span>
        </button>
        <div v-if="quoteMessage" class="status-msg" :class="quoteStatus">{{ quoteMessage }}</div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { FileBox as IconFileBox, Database as IconDatabase, UploadCloud as IconUpload } from 'lucide-vue-next'

const BASE_URL = 'http://localhost:8000/api/upload'

// Docs logic
const isDraggingDoc = ref(false)
const docFile = ref(null)
const docInput = ref(null)
const docUploading = ref(false)
const docMessage = ref('')
const docStatus = ref('')

const triggerDocSelect = () => docInput.value.click()
const onDocSelected = (e) => docFile.value = e.target.files[0]
const onDropDoc = (e) => {
  isDraggingDoc.value = false
  if (e.dataTransfer.files.length > 0) {
    docFile.value = e.dataTransfer.files[0]
  }
}
const uploadDocument = async () => {
  if (!docFile.value) return
  docUploading.value = true
  docMessage.value = ''
  
  const formData = new FormData()
  formData.append('file', docFile.value)
  
  try {
    const res = await axios.post(`${BASE_URL}/document`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    docStatus.value = 'success'
    docMessage.value = res.data.message
    docFile.value = null
  } catch (err) {
    docStatus.value = 'error'
    docMessage.value = err.response?.data?.detail || err.message
  } finally {
    docUploading.value = false
  }
}

// Quote logic
const isDraggingQuote = ref(false)
const quoteFile = ref(null)
const quoteInput = ref(null)
const quoteUploading = ref(false)
const quoteMessage = ref('')
const quoteStatus = ref('')

const triggerQuoteSelect = () => quoteInput.value.click()
const onQuoteSelected = (e) => quoteFile.value = e.target.files[0]
const onDropQuote = (e) => {
  isDraggingQuote.value = false
  if (e.dataTransfer.files.length > 0) {
    quoteFile.value = e.dataTransfer.files[0]
  }
}
const uploadQuote = async () => {
  if (!quoteFile.value) return
  quoteUploading.value = true
  quoteMessage.value = ''
  
  const formData = new FormData()
  formData.append('file', quoteFile.value)
  
  try {
    const res = await axios.post(`${BASE_URL}/quote`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    quoteStatus.value = 'success'
    quoteMessage.value = res.data.message
    quoteFile.value = null
  } catch (err) {
    quoteStatus.value = 'error'
    quoteMessage.value = err.response?.data?.detail || err.message
  } finally {
    quoteUploading.value = false
  }
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 40%),
              radial-gradient(circle at bottom left, rgba(139, 92, 246, 0.1), transparent 40%);
}

.admin-header {
  padding: 24px 32px;
  text-align: left;
}
.gradient-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}
.admin-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}
.admin-header p {
  color: var(--text-secondary);
}

.admin-content {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.upload-section {
  flex: 1;
  min-width: 400px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition: transform 0.3s ease;
}
.upload-section:hover {
  transform: translateY(-4px);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon-lg {
  width: 28px;
  height: 28px;
}
.text-blue { color: #60a5fa; }
.text-purple { color: #c084fc; }

.section-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.drop-zone {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.drop-zone:hover, .drag-active {
  border-color: var(--accent-color);
  background: rgba(59, 130, 246, 0.05);
}
.upload-icon {
  width: 32px;
  height: 32px;
  color: var(--text-secondary);
}
.file-sel {
  color: var(--accent-hover);
  font-weight: 600;
}

.btn-primary {
  background: var(--primary-gradient);
  color: white;
  padding: 14px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  opacity: 0.9;
}
.btn-primary:hover:not(:disabled) {
  opacity: 1;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.btn-primary:disabled {
  background: var(--border-color);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.quote-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
}
.quote-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.status-msg {
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}
.success { background: rgba(16, 185, 129, 0.1); color: #34d399; }
.error { background: rgba(239, 68, 68, 0.1); color: #f87171; }
</style>
