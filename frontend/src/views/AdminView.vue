<template>
  <div class="admin-container">
    <header class="admin-header glass-panel">
      <div class="header-main">
        <div class="admin-brand">
          <img src="/logo.png" alt="仲易达集团" class="admin-logo" />
          <span class="brand-divider">|</span>
          <span class="gradient-text">小易助手后台管理</span>
        </div>
        <div class="admin-user-nav">
          <div class="user-profile">
            <span class="user-info">
              <span class="user-name">{{ auth.userName }}</span>
              <span class="user-role">{{ auth.user?.role === 'super_admin' ? '总管' : '分公司管理员' }}</span>
            </span>
            <button @click="auth.logout(); router.push('/login')" class="logout-btn">退出登录</button>
          </div>
          <router-link to="/admin/staff" class="nav-btn">账号管理</router-link>
          <router-link to="/admin/lab" class="nav-btn">小易实验室</router-link>
          <router-link to="/admin/chat-logs" class="nav-btn">会话审计</router-link>
          <router-link to="/" class="nav-btn-outline">返回助手</router-link>
        </div>
      </div>
      <p class="header-desc">管理业务知识库与最新报价表数据</p>
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

      <!-- Notice Management Section -->
      <section class="upload-section glass-panel">
        <div class="section-header">
          <IconBell class="icon-lg text-orange" />
          <h2>通知管理</h2>
        </div>
        <p class="section-desc">发布重要通知。此处输入的内容将在前端“重要通知”模块中显示（由于本周逻辑，新发布的通知会立即显示）。</p>
        
        <textarea 
          v-model="noticeContent" 
          placeholder="请输入通知内容..." 
          class="notice-textarea"
          rows="4"
        ></textarea>
        
        <button class="btn-primary notice-btn" :disabled="!noticeContent.trim() || noticeSending" @click="sendNotice">
          <span v-if="noticeSending">发布中...</span>
          <span v-else>发布通知</span>
        </button>
        
        <div class="uploaded-list" v-if="historyNotices.length > 0">
          <h3>历史通知记录</h3>
          <ul class="notice-history-list">
            <li v-for="n in historyNotices" :key="n.id" class="notice-history-item">
              <div class="notice-item-main">
                <span class="notice-item-date">{{ formatDate(n.created_at) }}</span>
                <p class="notice-item-content">{{ n.content }}</p>
              </div>
              <button class="btn-delete" @click="deleteNotice(n.id)" title="删除通知">🗑️ 删除</button>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import axios from 'axios'
import { 
  FileBox as IconFileBox, 
  Database as IconDatabase, 
  UploadCloud as IconUpload, 
  UserCheck as IconUserCheck,
  Bell as IconBell
} from 'lucide-vue-next'
import { useUploader } from '../composables/useUploader'

const router = useRouter()
const auth = useAuthStore()

const BASE_URL = '/api/upload'

// ─── 已上传文件列表 ────────────────────────────────────────────
const uploadedAdmin = ref([])
const uploadedBiz = ref([])
const uploadedQuotes = ref([])
const coachCases = ref([])
const historyNotices = ref([])
const noticeContent = ref('')
const noticeSending = ref(false)

const fetchUploadedDocs = async () => {
  try {
    const [resA, resB] = await Promise.all([
      axios.get(`${BASE_URL}/documents?category=admin`),
      axios.get(`${BASE_URL}/documents?category=biz`)
    ])
    uploadedAdmin.value = resA.data.files || []
    uploadedBiz.value = resB.data.files || []
  } catch (err) {
    console.error('Failed to fetch documents:', err)
  }
}

const fetchUploadedQuotes = async () => {
  try {
    const res = await axios.get(`${BASE_URL}/quotes`)
    uploadedQuotes.value = res.data.files || []
  } catch (err) {
    console.error('Failed to fetch quotes:', err)
  }
}

const fetchCoachCases = async () => {
  try {
    const res = await axios.get(`${BASE_URL}/coach-cases`)
    coachCases.value = Array.isArray(res.data) ? res.data : (res.data.cases || [])
  } catch (err) {
    console.error('Failed to fetch coach cases:', err)
  }
}

const fetchHistoryNotices = async () => {
  try {
    const res = await axios.get('/api/notices/history')
    historyNotices.value = res.data
  } catch (err) {
    console.error('Failed to fetch notices:', err)
  }
}

const sendNotice = async () => {
  if (!noticeContent.value.trim()) return
  noticeSending.value = true
  try {
    await axios.post('/api/notices/', { content: noticeContent.value })
    noticeContent.value = ''
    fetchHistoryNotices()
    alert('通知发布成功！')
  } catch (err) {
    alert(`发布失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    noticeSending.value = false
  }
}

const deleteNotice = async (id) => {
  if (!confirm('确定要删除这条通知吗？')) return
  try {
    await axios.delete(`/api/notices/${id}`)
    fetchHistoryNotices()
  } catch (err) {
    alert(`删除失败: ${err.message}`)
  }
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  fetchUploadedDocs()
  fetchUploadedQuotes()
  fetchCoachCases()
  fetchHistoryNotices()
})

// ─── Admin 文档上传 ────────────────────────────────────────────
const {
  files: adminFiles, inputRef: adminInput, uploading: adminUploading,
  message: adminMessage, status: adminStatus, currentIndex: currentAdminIndex,
  isDragging: isDraggingAdmin,
  triggerSelect: triggerAdminSelect, onSelected: onAdminSelected,
  onDrop: onDropAdmin, upload: uploadAdmin
} = useUploader({
  url: `${BASE_URL}/document?category=admin`,
  onSuccess: (n) => { fetchUploadedDocs(); return `成功处理并学习了 ${n} 份行政文档。` },
  onError: (n, errs) => { fetchUploadedDocs(); return `处理完成。成功: ${n}，失败: ${errs.length}。` }
})

// ─── Biz 文档上传 ──────────────────────────────────────────────
const {
  files: bizFiles, inputRef: bizInput, uploading: bizUploading,
  message: bizMessage, status: bizStatus, currentIndex: currentBizIndex,
  isDragging: isDraggingBiz,
  triggerSelect: triggerBizSelect, onSelected: onBizSelected,
  onDrop: onDropBiz, upload: uploadBiz
} = useUploader({
  url: `${BASE_URL}/document?category=biz`,
  onSuccess: (n) => { fetchUploadedDocs(); return `成功处理并学习了 ${n} 份业务资料。` },
  onError: (n, errs) => { fetchUploadedDocs(); return `处理完成。成功: ${n}，失败: ${errs.length}。` }
})

// ─── 删除文档 ─────────────────────────────────────────────────
const deleteDoc = async (filename) => {
  if (!confirm(`确定要从系统记忆中删除【${filename}】吗？删除后不可恢复。`)) return
  try {
    await axios.delete(`${BASE_URL}/document/${encodeURIComponent(filename)}`)
    fetchUploadedDocs()
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
}

// ─── 报价表上传 ────────────────────────────────────────────────
const {
  files: quoteFiles, inputRef: quoteInput, uploading: quoteUploading,
  message: quoteMessage, status: quoteStatus, currentIndex: currentQuoteIndex,
  isDragging: isDraggingQuote,
  triggerSelect: triggerQuoteSelect, onSelected: onQuoteSelected,
  onDrop: onDropQuote, upload: uploadQuotes
} = useUploader({
  url: `${BASE_URL}/quote`,
  onSuccess: (n) => { fetchUploadedQuotes(); return `成功更新了 ${n} 份报价单。` },
  onError: (n, errs) => {
    fetchUploadedQuotes()
    return `更新完成。成功: ${n}，失败: ${errs.length}。错误: ${errs.join('; ')}`
  }
})

const deleteQuote = async (filename) => {
  if (!confirm(`确定要从系统中删除报价表【${filename}】吗？`)) return
  try {
    await axios.delete(`${BASE_URL}/quote/${encodeURIComponent(filename)}`)
    fetchUploadedQuotes()
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`)
  }
}

// ─── 教练剧本上传（特殊逻辑：需要统计生成数量） ───────────────
const {
  files: caseFiles, inputRef: caseInput, uploading: caseUploading,
  message: caseMessage, status: caseStatus, currentIndex: currentCaseIndex,
  isDragging: isDraggingCase,
  triggerSelect: triggerCaseSelect, onSelected: onCaseSelected,
  onDrop: onDropCase, upload: uploadCases
} = useUploader({
  url: `${BASE_URL}/coach-case`,
  onSuccess: (n, _errs, dataList) => {
    const total = dataList.reduce((sum, d) => sum + (d.processed_count || 0), 0)
    fetchCoachCases()
    return `成功处理 ${n} 份文件，共生成 ${total} 个实战剧本！`
  },
  onError: (n, errs, dataList) => {
    const total = (dataList || []).reduce((sum, d) => sum + (d.processed_count || 0), 0)
    fetchCoachCases()
    return `处理完成。成功: ${n} 份，失败: ${errs.length} 份。共生成 ${total} 个剧本。`
  }
})

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
.text-orange { color: #f97316; }

.notice-textarea {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: white;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  resize: vertical;
}

.notice-textarea:focus {
  border-color: var(--accent-color);
}

.notice-btn {
  background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
}

.notice-history-list {
  max-height: 300px;
  overflow-y: auto;
}

.notice-history-item {
  flex-direction: row !important;
  align-items: flex-start !important;
  gap: 12px;
}

.notice-item-main {
  flex: 1;
  text-align: left;
}

.notice-item-date {
  font-size: 11px;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 4px;
}

.notice-item-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
  margin: 0;
}

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
