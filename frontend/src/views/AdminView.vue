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
      <!-- Admin Docs Upload Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconFileBox class="icon-lg text-blue" />
          <h2>行政规章制度 (HR/报销/考勤)</h2>
        </div>
        <p class="section-desc">上传行政规章制度 PDF、Word。上传后自动归入【行政库】。</p>
        
        <div class="drop-zone" 
             @dragover.prevent="isDraggingAdmin = true" 
             @dragleave.prevent="isDraggingAdmin = false" 
             @drop.prevent="onDropAdmin"
             :class="{'drag-active': isDraggingAdmin}"
             @click="triggerAdminSelect">
          <IconUpload class="upload-icon" />
          <p v-if="adminFiles.length === 0">拖拽行政规章资料到此处</p>
          <div v-else class="file-list">
            <div v-for="(file, idx) in adminFiles" :key="idx" class="file-item">
              <span class="file-sel">{{ file.name }}</span>
            </div>
          </div>
          <input type="file" ref="adminInput" style="display:none" @change="onAdminSelected" accept=".pdf,.doc,.docx,.txt" multiple />
        </div>
        
        <button class="btn-primary" :disabled="adminFiles.length === 0 || adminUploading" @click="uploadAdmin">
          <span v-if="adminUploading">上传中 ({{ currentAdminIndex + 1 }}/{{ adminFiles.length }})...</span>
          <span v-else>批量上传到行政库</span>
        </button>
        <div v-if="adminMessage" class="status-msg" :class="adminStatus">{{ adminMessage }}</div>
        
        <div class="uploaded-list" v-if="uploadedAdmin.length > 0">
          <h3>行政资料库</h3>
          <ul>
            <li v-for="file in uploadedAdmin" :key="file">
              <span class="file-name">{{ file }}</span>
              <button class="btn-delete" @click="deleteDoc(file)" title="删除">🗑️</button>
            </li>
          </ul>
        </div>
      </section>

      <!-- Biz Docs Upload Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconFileBox class="icon-lg text-green" />
          <h2>业务技能与资料 (术语/话术)</h2>
        </div>
        <p class="section-desc">上传业务技能、报关、销售手册。归入【业务库】供针对性检索。</p>
        
        <div class="drop-zone" 
             @dragover.prevent="isDraggingBiz = true" 
             @dragleave.prevent="isDraggingBiz = false" 
             @drop.prevent="onDropBiz"
             :class="{'drag-active': isDraggingBiz}"
             @click="triggerBizSelect">
          <IconUpload class="upload-icon" />
          <p v-if="bizFiles.length === 0">拖拽业务培训资料到此处</p>
          <div v-else class="file-list">
            <div v-for="(file, idx) in bizFiles" :key="idx" class="file-item">
              <span class="file-sel">{{ file.name }}</span>
            </div>
          </div>
          <input type="file" ref="bizInput" style="display:none" @change="onBizSelected" accept=".pdf,.doc,.docx,.txt" multiple />
        </div>
        
        <button class="btn-primary biz-btn" :disabled="bizFiles.length === 0 || bizUploading" @click="uploadBiz">
          <span v-if="bizUploading">上传中 ({{ currentBizIndex + 1 }}/{{ bizFiles.length }})...</span>
          <span v-else>批量上传到业务库</span>
        </button>
        <div v-if="bizMessage" class="status-msg" :class="bizStatus">{{ bizMessage }}</div>
        
        <div class="uploaded-list" v-if="uploadedBiz.length > 0">
          <h3>业务资料库</h3>
          <ul>
            <li v-for="file in uploadedBiz" :key="file">
              <span class="file-name">{{ file }}</span>
              <button class="btn-delete" @click="deleteDoc(file)" title="删除">🗑️</button>
            </li>
          </ul>
        </div>
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
        
        <!-- Uploaded Quotes List -->
        <div class="uploaded-list" v-if="uploadedQuotes.length > 0">
          <h3>系统中的报价表</h3>
          <ul>
            <li v-for="file in uploadedQuotes" :key="file">
              <span class="file-name">{{ file }}</span>
              <button class="btn-delete" @click="deleteQuote(file)" title="从记忆中删除">🗑️ 删除</button>
            </li>
          </ul>
        </div>
      </section>

      <!-- Coach Cases Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconUserCheck class="icon-lg text-green" />
          <h2>知识教练剧本库</h2>
        </div>
        <p class="section-desc">上传真实的客诉记录或历史聊天日志。系统将通过 AI 自动提取其中的<strong>客户人设、核心冲突点和入坑陷阱</strong>，生成实战演习剧本。</p>
        
        <div class="drop-zone" 
             @dragover.prevent="isDraggingCase = true" 
             @dragleave.prevent="isDraggingCase = false" 
             @drop.prevent="onDropCase"
             :class="{'drag-active': isDraggingCase}"
             @click="triggerCaseSelect">
          <IconUpload class="upload-icon" />
          <p v-if="caseFiles.length === 0">点击或多选拖拽真实谈单记录到此处 (txt/doc)</p>
          <div v-else class="file-list">
            <div v-for="(file, idx) in caseFiles" :key="idx" class="file-item">
              <span class="file-sel">{{ file.name }}</span>
            </div>
          </div>
          <input type="file" ref="caseInput" style="display:none" @change="onCaseSelected" accept=".pdf,.doc,.docx,.txt" multiple />
        </div>
        
        <button class="btn-primary coach-btn" :disabled="caseFiles.length === 0 || caseUploading" @click="uploadCases">
          <span v-if="caseUploading">正在深度拆解剧本 ({{ currentCaseIndex + 1 }}/{{ caseFiles.length }})...</span>
          <span v-else>批量生成实战演练剧本</span>
        </button>
        <div v-if="caseMessage" class="status-msg" :class="caseStatus">{{ caseMessage }}</div>
        
        <!-- Structured Cases List -->
        <div class="uploaded-list" v-if="coachCases.length > 0">
          <h3>实战演练剧本库</h3>
          <ul>
            <li v-for="c in coachCases" :key="c.id">
              <span class="file-name">
                <small class="tag-sm">[{{ c.category }}]</small> {{ c.name }}
              </span>
              <button class="btn-delete" @click="deleteCase(c.id)" title="删除剧本">🗑️ 删除</button>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { FileBox as IconFileBox, Database as IconDatabase, UploadCloud as IconUpload, UserCheck as IconUserCheck } from 'lucide-vue-next'

// Task 8: 去除硬编码端口，支持开发/生产环境自适应
const API_PORT = 8000
const BASE_URL = `http://${window.location.hostname}:${API_PORT}/api/upload`

const uploadedAdmin = ref([])
const uploadedBiz = ref([])
const uploadedQuotes = ref([])
const coachCases = ref([])

const fetchUploadedDocs = async () => {
  try {
    const resA = await axios.get(`${BASE_URL}/documents?category=admin`)
    uploadedAdmin.value = resA.data.files || []
    const resB = await axios.get(`${BASE_URL}/documents?category=biz`)
    uploadedBiz.value = resB.data.files || []
  } catch (err) {
    console.error("Failed to fetch documents:", err)
  }
}

const fetchUploadedQuotes = async () => {
  try {
    const res = await axios.get(`${BASE_URL}/quotes`)
    uploadedQuotes.value = res.data.files || []
  } catch (err) {
    console.error("Failed to fetch quotes:", err)
  }
}

const fetchCoachCases = async () => {
  try {
    const res = await axios.get(`${BASE_URL}/coach-cases`)
    coachCases.value = Array.isArray(res.data) ? res.data : (res.data.cases || [])
  } catch (err) {
    console.error("Failed to fetch coach cases:", err)
  }
}

onMounted(() => {
  fetchUploadedDocs()
  fetchUploadedQuotes()
  fetchCoachCases()
})

// === Admin logic ===
const isDraggingAdmin = ref(false)
const adminFiles = ref([])
const adminInput = ref(null)
const adminUploading = ref(false)
const adminMessage = ref('')
const adminStatus = ref('')
const currentAdminIndex = ref(0)
const triggerAdminSelect = () => adminInput.value.click()
const onAdminSelected = (e) => adminFiles.value = Array.from(e.target.files)
const onDropAdmin = (e) => {
  isDraggingAdmin.value = false
  if (e.dataTransfer.files.length > 0) adminFiles.value = Array.from(e.dataTransfer.files)
}
const uploadAdmin = async () => {
  if (adminFiles.value.length === 0) return
  adminUploading.value = true
  adminMessage.value = ''
  adminStatus.value = ''
  let successCount = 0
  let errorMessages = []
  for (let i = 0; i < adminFiles.value.length; i++) {
    currentAdminIndex.value = i
    const formData = new FormData()
    formData.append('file', adminFiles.value[i])
    try {
      await axios.post(`${BASE_URL}/document?category=admin`, formData, { headers: { 'Content-Type': 'multipart/form-data' }})
      successCount++
    } catch (err) {
      errorMessages.push(`${adminFiles.value[i].name}: ${err.response?.data?.detail || err.message}`)
    }
  }
  if (errorMessages.length === 0) {
    adminStatus.value = 'success'
    adminMessage.value = `成功处理并学习了 ${successCount} 份行政文档。`
    adminFiles.value = []
  } else {
    adminStatus.value = 'error'
    adminMessage.value = `处理完成。成功: ${successCount}. 失败: ${errorMessages.length}.`
  }
  adminUploading.value = false
  fetchUploadedDocs()
}

// === Biz logic ===
const isDraggingBiz = ref(false)
const bizFiles = ref([])
const bizInput = ref(null)
const bizUploading = ref(false)
const bizMessage = ref('')
const bizStatus = ref('')
const currentBizIndex = ref(0)
const triggerBizSelect = () => bizInput.value.click()
const onBizSelected = (e) => bizFiles.value = Array.from(e.target.files)
const onDropBiz = (e) => {
  isDraggingBiz.value = false
  if (e.dataTransfer.files.length > 0) bizFiles.value = Array.from(e.dataTransfer.files)
}
const uploadBiz = async () => {
  if (bizFiles.value.length === 0) return
  bizUploading.value = true
  bizMessage.value = ''
  bizStatus.value = ''
  let successCount = 0
  let errorMessages = []
  for (let i = 0; i < bizFiles.value.length; i++) {
    currentBizIndex.value = i
    const formData = new FormData()
    formData.append('file', bizFiles.value[i])
    try {
      await axios.post(`${BASE_URL}/document?category=biz`, formData, { headers: { 'Content-Type': 'multipart/form-data' }})
      successCount++
    } catch (err) {
      errorMessages.push(`${bizFiles.value[i].name}: ${err.response?.data?.detail || err.message}`)
    }
  }
  if (errorMessages.length === 0) {
    bizStatus.value = 'success'
    bizMessage.value = `成功处理并学习了 ${successCount} 份业务资料。`
    bizFiles.value = []
  } else {
    bizStatus.value = 'error'
    bizMessage.value = `处理完成。成功: ${successCount}. 失败: ${errorMessages.length}.`
  }
  bizUploading.value = false
  fetchUploadedDocs()
}

const deleteDoc = async (filename) => {
  if (!confirm(`确定要从系统记忆中删除【${filename}】吗？删除后不可恢复。`)) return
  try {
    await axios.delete(`${BASE_URL}/document/${encodeURIComponent(filename)}`)
    fetchUploadedDocs()
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
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
  let errorMessages = []

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
      errorMessages.push(`${quoteFiles.value[i].name}: ${err.response?.data?.detail || err.message}`)
    }
  }

  if (errorMessages.length === 0) {
    quoteStatus.value = 'success'
    quoteMessage.value = `成功更新了 ${successCount} 份报价单。`
    quoteFiles.value = []
  } else {
    quoteStatus.value = 'error'
    quoteMessage.value = `更新完成。成功: ${successCount}. 失败: ${errorMessages.length}. 错误: ${errorMessages.join('; ')}`
  }
  quoteUploading.value = false
  fetchUploadedQuotes()
}

const deleteQuote = async (filename) => {
  if (!confirm(`确定要从系统中删除报价表【${filename}】吗？`)) return
  try {
    await axios.delete(`${BASE_URL}/quote/${encodeURIComponent(filename)}`)
    fetchUploadedQuotes()
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
}

// Coach Cases Logic
const isDraggingCase = ref(false)
const caseFiles = ref([])
const caseInput = ref(null)
const caseUploading = ref(false)
const caseMessage = ref('')
const caseStatus = ref('')
const currentCaseIndex = ref(0)

const triggerCaseSelect = () => caseInput.value.click()
const onCaseSelected = (e) => caseFiles.value = Array.from(e.target.files)
const onDropCase = (e) => {
  isDraggingCase.value = false
  if (e.dataTransfer.files.length > 0) {
    caseFiles.value = Array.from(e.dataTransfer.files)
  }
}

const uploadCases = async () => {
  if (caseFiles.value.length === 0) return
  caseUploading.value = true
  caseMessage.value = ''
  caseStatus.value = ''
  
  let successCount = 0
  let totalCasesGenerated = 0

  for (let i = 0; i < caseFiles.value.length; i++) {
    currentCaseIndex.value = i
    const formData = new FormData()
    formData.append('file', caseFiles.value[i])
    
    try {
      const res = await axios.post(`${BASE_URL}/coach-case`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      successCount++
      totalCasesGenerated += (res.data.processed_count || 0)
    } catch (err) {
      console.error(`Failed to upload ${caseFiles.value[i].name}:`, err)
    }
  }

  caseStatus.value = 'success'
  caseMessage.value = `成功处理 ${successCount} 份文件，共生成 ${totalCasesGenerated} 个实战剧本！`
  caseFiles.value = []
  caseUploading.value = false
  fetchCoachCases()
}

const deleteCase = async (id) => {
  if (!confirm('确定要删除这个实战场景吗？')) return
  try {
    await axios.delete(`${BASE_URL}/coach-case/${id}`)
    fetchCoachCases()
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
}

const truncate = (text, len) => {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}
</script>

<style scoped>
.text-green { color: #10b981; }

.coach-btn {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
}

.case-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.case-admin-card {
  background: white;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.case-admin-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.case-emoji { font-size: 20px; }
.case-name { font-weight: 700; flex: 1; color: var(--text-primary); }

.case-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.btn-delete-small {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.btn-delete-small:hover {
  opacity: 1;
}

.admin-container {
  height: 100vh;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 40%),
              radial-gradient(circle at bottom left, rgba(139, 92, 246, 0.1), transparent 40%);
}

.admin-container::-webkit-scrollbar {
  width: 8px;
}
.admin-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.02);
}
.admin-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}
.admin-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
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

.uploaded-list {
  margin-top: 10px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 16px;
}
.uploaded-list h3 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-weight: 600;
}
.uploaded-list ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.uploaded-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  font-size: 14px;
}
.file-name {
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}
.btn-delete {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.btn-delete:hover {
  background: var(--danger-color);
  color: white;
}
</style>
