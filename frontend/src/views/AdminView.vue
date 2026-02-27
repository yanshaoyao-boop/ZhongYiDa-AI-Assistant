<template>
  <div class="admin-container">
    <header class="admin-header glass-panel">
      <div class="admin-brand">
        <img src="/logo.png" alt="仲易达集团" class="admin-logo" />
        <span class="brand-divider">|</span>
        <span class="gradient-text">智能助手后台管理</span>
      </div>
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
          <p v-if="docFiles.length === 0">点击或多选拖拽文件到此处 (PDF / Word)</p>
          <div v-else class="file-list">
            <div v-for="(file, idx) in docFiles" :key="idx" class="file-item">
              <span class="file-sel">{{ file.name }}</span>
            </div>
          </div>
          <input type="file" ref="docInput" style="display:none" @change="onDocSelected" accept=".pdf,.doc,.docx,.txt" multiple />
        </div>
        
        <button class="btn-primary" :disabled="docFiles.length === 0 || docUploading" @click="uploadDocuments">
          <span v-if="docUploading">正在批量学习中 ({{ currentFileIndex + 1 }}/{{ docFiles.length }})...</span>
          <span v-else>开始批量上传学习</span>
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
          <p v-if="quoteFiles.length === 0">点击或多选拖拽报价表到此处 (Excel / CSV)</p>
          <div v-else class="file-list">
            <div v-for="(file, idx) in quoteFiles" :key="idx" class="file-item">
              <span class="file-sel">{{ file.name }}</span>
            </div>
          </div>
          <input type="file" ref="quoteInput" style="display:none" @change="onQuoteSelected" accept=".xlsx,.xls,.csv" multiple />
        </div>
        
        <button class="btn-primary quote-btn" :disabled="quoteFiles.length === 0 || quoteUploading" @click="uploadQuotes">
          <span v-if="quoteUploading">正在更新报价库 ({{ currentQuoteIndex + 1 }}/{{ quoteFiles.length }})...</span>
          <span v-else>批量更新系统报价表</span>
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

const BASE_URL = `http://${window.location.hostname}:8000/api/upload`

// Docs logic
const isDraggingDoc = ref(false)
const docFiles = ref([])
const docInput = ref(null)
const docUploading = ref(false)
const docMessage = ref('')
const docStatus = ref('')
const currentFileIndex = ref(0)

const triggerDocSelect = () => docInput.value.click()
const onDocSelected = (e) => docFiles.value = Array.from(e.target.files)
const onDropDoc = (e) => {
  isDraggingDoc.value = false
  if (e.dataTransfer.files.length > 0) {
    docFiles.value = Array.from(e.dataTransfer.files)
  }
}
const uploadDocuments = async () => {
  if (docFiles.value.length === 0) return
  docUploading.value = true
  docMessage.value = ''
  docStatus.value = ''
  
  let successCount = 0
  let errorMessages = []

  for (let i = 0; i < docFiles.value.length; i++) {
    currentFileIndex.value = i
    const formData = new FormData()
    formData.append('file', docFiles.value[i])
    
    try {
      await axios.post(`${BASE_URL}/document`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      successCount++
    } catch (err) {
      errorMessages.push(`${docFiles.value[i].name}: ${err.response?.data?.detail || err.message}`)
    }
  }

  if (errorMessages.length === 0) {
    docStatus.value = 'success'
    docMessage.value = `成功处理并学习了 ${successCount} 份文档。`
    docFiles.value = []
  } else {
    docStatus.value = 'error'
    docMessage.value = `处理完成。成功: ${successCount}. 失败: ${errorMessages.length}. 错误信息: ${errorMessages.join('; ')}`
  }
  docUploading.value = false
}

// Quote logic
const isDraggingQuote = ref(false)
const quoteFiles = ref([])
const quoteInput = ref(null)
const quoteUploading = ref(false)
const quoteMessage = ref('')
const quoteStatus = ref('')
const currentQuoteIndex = ref(0)

const triggerQuoteSelect = () => quoteInput.value.click()
const onQuoteSelected = (e) => quoteFiles.value = Array.from(e.target.files)
const onDropQuote = (e) => {
  isDraggingQuote.value = false
  if (e.dataTransfer.files.length > 0) {
    quoteFiles.value = Array.from(e.dataTransfer.files)
  }
}
const uploadQuotes = async () => {
  if (quoteFiles.value.length === 0) return
  quoteUploading.value = true
  quoteMessage.value = ''
  quoteStatus.value = ''
  
  let successCount = 0
  for (let i = 0; i < quoteFiles.value.length; i++) {
    currentQuoteIndex.value = i
    const formData = new FormData()
    formData.append('file', quoteFiles.value[i])
    
    try {
      await axios.post(`${BASE_URL}/quote`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      successCount++
    } catch (err) {
      console.error(err)
    }
  }

  quoteStatus.value = 'success'
  quoteMessage.value = `成功更新了 ${successCount} 份报价单。`
  quoteFiles.value = []
  quoteUploading.value = false
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
.admin-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.admin-logo {
  height: 32px;
  width: auto;
}
.brand-divider {
  color: var(--border-color);
  font-weight: 300;
  font-size: 24px;
}
.gradient-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  font-size: 28px;
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
.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 120px;
  overflow-y: auto;
  width: 100%;
}
.file-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
}
.file-sel {
  color: var(--accent-hover);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
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
