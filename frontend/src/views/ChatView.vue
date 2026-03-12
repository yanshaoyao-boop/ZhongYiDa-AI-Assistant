<template>
  <div :class="['app-layout', currentMode + '-mode']">
    <div :class="['sidebar-overlay', { show: isSidebarOpen }]" @click="isSidebarOpen = false"></div>
    <aside :class="['sidebar', 'glass-panel', { show: isSidebarOpen }]">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="startNewChatWithClose">
          <span class="icon">+</span> 新对话
        </button>
      </div>
      <div class="session-list">
        <div v-for="session in sessions" :key="session.id" 
             :class="['session-item', { active: session.id === currentSessionId }]"
             @click="switchSessionWithClose(session.id)">
          <div class="session-title">{{ session.title || '新对话' }}</div>
          <button class="delete-btn" @click.stop="deleteSession(session.id)" title="删除对话">×</button>
        </div>
      </div>

      <div class="sidebar-footer">
        <a v-if="auth.isAdmin" href="/admin" target="_blank" class="sidebar-admin-btn">
          <IconShieldCheck size="18" /> 管理员入口
        </a>
        <div class="sidebar-user-info">
          <div class="user-avatar-sidebar">{{ auth.userName?.[0]?.toUpperCase() }}</div>
          <div class="user-details">
            <span class="user-name-sidebar">{{ auth.userName }}</span>
            <button class="logout-link-sidebar" @click="handleLogout">退出登录</button>
          </div>
        </div>
      </div>
    </aside>

    <div class="chat-container">
      <!-- Navbar -->
      <nav class="chat-nav glass-panel">
        <div class="nav-left">
          <button class="menu-toggle" @click="isSidebarOpen = !isSidebarOpen">
            <IconMenu v-if="!isSidebarOpen" />
            <IconX v-else />
          </button>
          <div class="brand">
            <img src="/logo.png" alt="仲易达集团" class="company-logo" />
            <span class="brand-divider">|</span>
            <span class="gradient-text">小易智能助手</span>
          </div>
          <!-- Mobile Intel Toggle -->
          <button v-if="currentMode === 'coach' && currentScenario" 
                  class="intel-toggle-mobile" 
                  @click="isIntelOpen = !isIntelOpen"
                  :class="{ active: isIntelOpen }">
            <IconZap size="18" /> 实战情报
          </button>
        </div>

        <!-- Mode Selector Groups -->
        <div class="mode-selector-wrapper">
          <div class="mode-selector">
            <button class="mode-btn" @click="openNotices">
              <span class="icon">🔔</span> 重要通知
            </button>
            <button class="mode-btn">
              <span class="icon">🛠️</span> 智能工具
            </button>
          </div>

          <div class="mode-selector">
            <button 
              :class="['mode-btn', { active: currentMode === 'general' }]"
              @click="switchMode('general')"
            >
              <span class="icon">✨</span> 全能助手
            </button>
            <button 
              :class="['mode-btn', { active: currentMode === 'coach' }]"
              @click="switchMode('coach')"
            >
              <span class="icon">📚</span> 知识教练
            </button>
            <button 
              :class="['mode-btn', { active: currentMode === 'expert' }]"
              @click="switchMode('expert')"
            >
              <span class="icon">💡</span> 专家指导
            </button>
          </div>
        </div>

      </nav>

      <div class="main-body-wrapper">
        <!-- Chat Area -->
        <main class="chat-main" ref="chatMain">
          <div v-if="messages.length === 0" class="welcome-screen">
            <template v-if="currentMode === 'general'">
              <div class="welcome-brand">
                <img src="@/assets/xiaoyi_image.png" alt="小易形象" class="welcome-avatar" />
                <h2 class="welcome-name">{{ welcomeMsg }}</h2>
                <h2 class="welcome-slogan">把繁琐的流程交给我，把专注留给真正重要的事情。</h2>
              </div>
              <div class="suggestion-chips">
                <button @click="presetMsg('我能帮你做哪些事')">🤖 我能帮你做哪些事</button>
                <button @click="presetMsg('如何正确的使用小易')">📖 如何正确的使用小易</button>
              </div>
            </template>
            <template v-else-if="currentMode === 'expert'">
              <h2 class="welcome-name">欢迎来到专家指导模式</h2>
              <h2 class="welcome-slogan">请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。</h2>
            </template>
            <template v-else>
              <h2 class="welcome-name">欢迎来到知识教练模式</h2>
              <h2 class="welcome-slogan">场景化沉浸式对练，打造金牌业务员。</h2>
              <!-- 第一级：选择航线/大区 -->
              <div class="category-step-label" v-if="!selectedRegion">第一步：选择实战航线</div>
              <div class="category-grid" v-if="!selectedRegion">
                <div v-for="reg in coachRegions" :key="reg.name" 
                     class="category-main-card region-card" 
                     @click="selectedRegion = reg.name">
                  <span class="cat-emoji">{{ reg.emoji }}</span>
                  <div class="cat-info">
                    <h3>{{ reg.name }}</h3>
                    <p>{{ reg.desc }}</p>
                  </div>
                </div>
              </div>

              <!-- 第二层：选择客户身份 -->
              <div class="category-step-header" v-if="selectedRegion && !selectedPersona">
                <button class="back-link" @click="selectedRegion = null">← 返回重选航线</button>
                <div class="category-step-label">第二步：选择【{{ selectedRegion }}】客户背景</div>
              </div>
              <div class="category-grid" v-if="selectedRegion && !selectedPersona">
                <div v-for="per in coachPersonas" :key="per.name" 
                     class="category-main-card persona-card" 
                     @click="selectedPersona = per.name">
                  <span class="cat-emoji">{{ per.emoji }}</span>
                  <div class="cat-info">
                    <h3>{{ per.name }}</h3>
                    <p>{{ per.desc }}</p>
                  </div>
                </div>
              </div>

              <!-- 第三层：选择练习科目 -->
              <div class="category-step-header" v-if="selectedPersona">
                <button class="back-link" @click="selectedPersona = null">← 返回重选身份</button>
                <div class="category-step-label">第三步：选择【{{ selectedPersona }}】练习科目</div>
              </div>
              <div class="category-grid subjects" v-if="selectedPersona">
                <div v-for="sub in coachSubjects" :key="sub.name" 
                     class="category-main-card subject-card" 
                     @click="startRandomCoachDetailed(sub.name)">
                  <span class="cat-emoji">{{ sub.emoji }}</span>
                  <div class="cat-info">
                    <h3>{{ sub.name }}</h3>
                    <p>{{ sub.desc }}</p>
                  </div>
                </div>
              </div>
              
              <div class="suggestion-chips" style="margin-top: 32px;">
                <button @click="presetMsg('能通俗地给我讲解一下什么是DDP和DDU吗？')">📖 常见物流基础名词讲解</button>
              </div>
            </template>
          </div>

          <div class="message-list">
            <div v-for="msg in messages" :key="msg.id"
                class="message-wrapper" :class="msg.role">
              <div class="avatar">
                <template v-if="msg.role === 'assistant'">
                  <div class="avatar-container assistant">
                    <img src="@/assets/xiaoyi_avatar.png" alt="小易" class="xiaoyi-avatar" />
                  </div>
                </template>
                <template v-else>
                  <div class="user-avatar">You</div>
                </template>
              </div>
              <div class="message-content glass-panel" :class="{'is-typing': msg.isTyping}">
                <div v-if="msg.image" class="message-image-container">
                  <img :src="msg.image" alt="用户上传图片" class="chat-message-image" @click="openImageModal(msg.image)" />
                </div>
                <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                <span v-if="msg.isTyping" class="cursor-blink"></span>
              </div>
            </div>
          </div>
        </main>

        <!-- Combat Intel Panel (NEW) -->
        <div v-if="currentMode === 'coach' && currentScenario" :class="['intel-overlay', { show: isIntelOpen }]" @click="isIntelOpen = false"></div>
        <aside v-if="currentMode === 'coach' && currentScenario" 
               :class="['combat-intel-panel', 'glass-panel', { 'show-mobile': isIntelOpen }]">
          <div class="panel-header">
            <IconZap class="icon-zap" />
            <h3>实战情报中心</h3>
          </div>
          
          <div class="intel-section">
            <label>当前目标</label>
            <p class="mission-goal">{{ currentScenario.name }}</p>
          </div>

          <div class="intel-section">
            <label>客户情报 (Persona)</label>
            <p class="persona-brief">{{ currentScenario.persona }}</p>
          </div>

          <div class="intel-section cargo-intel" v-if="currentScenario.cargo_details">
            <label>隐藏货盘参数 (关键底牌)</label>
            <div class="cargo-grid-mini">
              <div class="cargo-item"><span>品名:</span> {{ currentScenario.cargo_details.item }}</div>
              <div class="cargo-item"><span>件数:</span> {{ currentScenario.cargo_details.qty }} CTNS</div>
              <div class="cargo-item"><span>规格:</span> {{ currentScenario.cargo_details.size_cm }} CM</div>
              <div class="cargo-item"><span>重量:</span> {{ currentScenario.cargo_details.gw_kg }} KG</div>
              <div class="cargo-item"><span>目的地:</span> {{ currentScenario.cargo_details.destination }}</div>
            </div>
            <div class="intel-warning" v-if="currentScenario.cargo_details.hidden_issue">
              ⚠️ 陷阱提醒：{{ currentScenario.cargo_details.hidden_issue }}
            </div>
          </div>

          <div class="intel-section">
            <label>必杀技 / 通关条件</label>
            <ul class="success-list">
              <li v-for="(item, idx) in formatSuccessCriteria(currentScenario.success_criteria)" :key="idx">
                {{ item }}
              </li>
            </ul>
          </div>

          <button class="quit-combat-btn" @click="requestCoachEvaluation">
             结束对练并结算
          </button>
        </aside>
      </div>

      <!-- Input Area -->
      <footer class="chat-footer">
        <div class="input-container glass-panel" 
             :class="{'has-image': selectedImage}"
             @dragover.prevent="onDragOver"
             @drop.prevent="onDrop">
          <div v-if="selectedImage" class="image-preview-area">
            <img :src="selectedImage" alt="Preview" class="image-preview" />
            <button class="remove-image-btn" @click="removeImage"><IconXCircle size="18" /></button>
          </div>
          <div class="input-box">
            <button class="upload-pic-btn" @click="triggerImageUpload" title="上传图片分析">
              <IconImage class="icon-img" />
            </button>
            <input type="file" ref="fileInput" style="display:none" @change="onImageSelected" accept="image/jpeg,image/png,image/webp" />
            <textarea 
              v-model="inputMsg" 
              @keydown.enter.prevent="sendMessage"
              @paste="handlePaste"
              placeholder="发送消息、粘贴或拖入图片..."
              rows="1"
              ref="inputRef"
              @input="autoGrow"
            ></textarea>
            <button v-if="!isGenerating" class="send-btn" :disabled="!inputMsg.trim() && !selectedImage" @click="sendMessage">
              <IconSend class="icon-send" />
            </button>
            <button v-else class="send-btn stop-btn" @click="stopGeneration" title="停止生成">
              <IconSquare class="icon-send" />
            </button>
          </div>
        </div>
        <p class="disclaimer">助手生成的内容可能不准确，请参考系统里的正式文档与报价。</p>
      </footer>
    </div>

    <!-- Notices Modal -->
    <div v-if="showNotices" class="notices-modal-overlay" @click.self="showNotices = false">
      <div class="notices-modal glass-panel">
        <div class="notices-modal-header">
          <h3>📢 重要通知</h3>
          <div class="notices-tabs">
            <button :class="{ active: noticeTab === 'current' }" @click="noticeTab = 'current'">本周通知</button>
            <button :class="{ active: noticeTab === 'history' }" @click="noticeTab = 'history'">全部历史</button>
          </div>
          <button class="close-modal-btn" @click="showNotices = false"><IconX size="20" /></button>
        </div>
        
        <div class="notices-modal-content">
          <div v-if="loadingNotices" class="notice-loading">正在加载通知...</div>
          <div v-else-if="displayNotices.length === 0" class="notice-empty">暂无通知内容</div>
          <div v-else class="notice-list-scroll">
            <div v-for="n in displayNotices" :key="n.id" class="notice-card">
              <div class="notice-date">{{ formatDate(n.created_at) }}</div>
              <div class="notice-body">{{ n.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { renderMarkdown } from '@/utils/markdown'
import { 
  Menu as IconMenu, 
  X as IconX, 
  Send as IconSend, 
  Image as IconImage, 
  Square as IconSquare, 
  XCircle as IconXCircle,
  Zap as IconZap,
  ShieldCheck as IconShieldCheck
} from 'lucide-vue-next'
// 使用相对路径，配合 vite.config.js 中的 dev proxy 转发到后端
// 生产环境由 nginx/反向代理处理 /api 路由
const API_BASE = ''

const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const abortController = ref(null)

const showNotices = ref(false)
const noticeTab = ref('current')
const allNotices = ref({ current: [], history: [] })
const loadingNotices = ref(false)

const openNotices = async () => {
  showNotices.value = true
  loadingNotices.value = true
  try {
    const [resC, resH] = await Promise.all([
      axios.get('/api/notices/current'),
      axios.get('/api/notices/history')
    ])
    allNotices.value.current = resC.data
    allNotices.value.history = resH.data
  } catch (err) {
    console.error("Failed to fetch notices:", err)
  } finally {
    loadingNotices.value = false
  }
}

const displayNotices = computed(() => {
  return noticeTab.value === 'current' ? allNotices.value.current : allNotices.value.history
})

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}
const chatMain = ref(null)
const inputRef = ref(null)
const currentMode = ref('general')
const isSidebarOpen = ref(false)
const getDynamicGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return "早安！我是小易，又是充满活力的一天，今天有什么计划需要我协助吗？"
  if (hour >= 12 && hour < 18) return "下午好！我是小易，累了可以休息一下，有琐碎的工作尽管交给我。"
  if (hour >= 18 && hour < 22) return "晚上好！我是小易，这么晚还在忙吗？注意休息，我会一直陪着您。"
  return "深夜好，我是小易。辛苦了，还在坚持工作的你真的很了不起。早点休息，我会一直陪着您。"
}

const welcomeMsg = ref(getDynamicGreeting())
const auth = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

const fetchPublicSettings = async () => {
  try {
    const res = await axios.get('/api/settings/public')
    if (res.data.ai_welcome_message) {
      welcomeMsg.value = res.data.ai_welcome_message
    } else {
      welcomeMsg.value = getDynamicGreeting()
    }
  } catch (err) {
    console.error("Failed to fetch public settings:", err)
  }
}

const selectedImage = ref(null)
const fileInput = ref(null)

const triggerImageUpload = () => {
  if (fileInput.value) fileInput.value.click()
}

const onImageSelected = (e) => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (evt) => {
      selectedImage.value = evt.target.result
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = () => {
  selectedImage.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const handlePaste = (e) => {
  const items = e.clipboardData.items
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const blob = items[i].getAsFile()
      const reader = new FileReader()
      reader.onload = (evt) => {
        selectedImage.value = evt.target.result
      }
      reader.readAsDataURL(blob)
    }
  }
}

const onDragOver = (e) => {
  // Can add visual feedback for dragging here
}

const onDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (evt) => {
      selectedImage.value = evt.target.result
    }
    reader.readAsDataURL(file)
  }
}

// Full screen image modal logic (Optional enhancement)
const showImageModal = ref(false)
const modalImageUrl = ref('')
const openImageModal = (url) => {
  modalImageUrl.value = url
  showImageModal.value = true
}
const closeImageModal = () => {
  showImageModal.value = false
}

const sessions = ref([])
const currentSessionId = ref(null)
const coachCases = ref([])
const currentScenario = ref(null) 
const selectedRegion = ref(null)
const selectedPersona = ref(null)
const isIntelOpen = ref(false)

const formatSuccessCriteria = (criteria) => {
  if (Array.isArray(criteria)) return criteria
  if (typeof criteria === 'string') return criteria.split('\n').filter(t => t.trim())
  return []
}

// L1: 大区
const coachRegions = [
  { name: '美国线', emoji: '🇺🇸', desc: '侧重美森、海派、邮编偏远、计费重规则' },
  { name: '欧洲线', emoji: '🇪🇺', desc: '侧重铁路卡航、VAT税号、清关及递延规则' }
]

// L2: 人设背景
const coachPersonas = [
  { name: '行业小白', emoji: '🐣', desc: '礼貌客气但不懂行，需要你专业引导且极易流失' },
  { name: '江湖老手', emoji: '😎', desc: '满嘴专业术语，深谙低价之道，极其挑剔计较' }
]

// L3: 练习科目
const coachSubjects = [
  { name: '报价拉锯战', emoji: '💰', desc: '模拟精明客户反复试价，考验利润把控力' },
  { name: '异常纠纷处理', emoji: '💢', desc: '处理海关查验、计费纠纷、破损扣关等危机' },
  { name: '业务挖坑排雷', emoji: '📦', desc: '看破客户隐藏的敏感货、超规格等行业深坑' },
  { name: '逼单客情维护', emoji: '🤝', desc: '针对犹豫客户进行专业度展示与最终转化' }
]

const startRandomCoachDetailed = (subjectName) => {
  if (!selectedRegion.value || !selectedPersona.value) return
  
  const region = selectedRegion.value
  const persona = selectedPersona.value
  
  const matchingCases = coachCases.value.filter(c => {
    const cat = (c.category || '').toLowerCase()
    
    // 航线匹配 (用包含)
    const rMatch = cat.includes(region.toLowerCase())
    
    // 人设匹配 (用包含，增加容错)
    const pMatch = cat.includes(persona.toLowerCase()) || 
                   (persona.includes('小白') && cat.includes('小白')) ||
                   (persona.includes('老手') && cat.includes('老手'))
    
    // 科目匹配 (多关键词匹配)
    const sMatch = cat.includes(subjectName.toLowerCase()) || 
                   (subjectName === '报价拉锯战' && (cat.includes('报价') || cat.includes('比价') || cat.includes('拉锯'))) ||
                   (subjectName === '异常纠纷处理' && (cat.includes('纠纷') || cat.includes('异常') || cat.includes('投诉') || cat.includes('处理'))) ||
                   (subjectName === '业务挖坑排雷' && (cat.includes('挖坑') || cat.includes('排雷') || cat.includes('陷阱') || cat.includes('深坑') || cat.includes('风险'))) ||
                   (subjectName === '逼单客情维护' && (cat.includes('逼单') || cat.includes('客情') || cat.includes('维护') || cat.includes('转化') || cat.includes('信任')))
    
    return rMatch && pMatch && sMatch
  })
  
  if (matchingCases.length === 0) {
    alert(`暂无【${region} · ${persona} · ${subjectName}】分类的案例。请先通过管理后台上传解析记录。`)
    return
  }
  
  const randomCase = matchingCases[Math.floor(Math.random() * matchingCases.length)]
  currentScenario.value = randomCase
  startCoachScenario(randomCase.name, randomCase.prompt)
}

const fetchCoachCases = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/upload/coach-cases`)
    // 后端现在直接返回数组
    if (Array.isArray(res.data)) {
      coachCases.value = res.data
    } else if (res.data && res.data.cases) {
      coachCases.value = res.data.cases
    } else {
      coachCases.value = []
    }
    console.log(">> Loaded coach cases count:", coachCases.value.length)
  } catch (err) {
    console.error("Failed to fetch coach cases:", err)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatMain.value) {
    chatMain.value.scrollTop = chatMain.value.scrollHeight
  }
}

const loadSessionsForMode = (mode) => {
  const saved = localStorage.getItem(`zyd_chat_sessions_${mode}`)
  if (saved) {
    try {
      sessions.value = JSON.parse(saved)
    } catch(e) {
      sessions.value = []
    }
  } else {
    sessions.value = []
  }
  
  if (sessions.value.length === 0) {
    startNewChat()
  } else {
    currentSessionId.value = sessions.value[0].id
    messages.value = sessions.value[0].messages || []
  }
}

const switchMode = (mode) => {
  if (currentMode.value === mode) return
  currentMode.value = mode
  isIntelOpen.value = false
  if (mode === 'general') {
    currentScenario.value = null
  } else {
    selectedRegion.value = null 
    selectedPersona.value = null // 重置 3 层选择
  }
  loadSessionsForMode(mode)
}

onMounted(() => {
  const oldSaved = localStorage.getItem('zyd_chat_sessions')
  if (oldSaved && !localStorage.getItem('zyd_chat_sessions_general')) {
    localStorage.setItem('zyd_chat_sessions_general', oldSaved)
  }
  loadSessionsForMode(currentMode.value)
  fetchCoachCases()
  fetchPublicSettings()
})

onUnmounted(() => {
  // 清理防抖定时器，防止组件卸载后仍写 localStorage
  if (saveTimeout) clearTimeout(saveTimeout)
  // 中断未完成的网络请求，防止内存泄漏
  if (abortController.value) abortController.value.abort()
})

const startNewChat = () => {
  const newId = Date.now().toString()
  sessions.value.unshift({
    id: newId,
    title: '新对话',
    messages: []
  })
  currentSessionId.value = newId
  messages.value = sessions.value.find(s => s.id === newId).messages
}

const startNewChatWithClose = () => {
  startNewChat()
  isSidebarOpen.value = false
}

const switchSession = (id) => {
  const session = sessions.value.find(s => s.id === id)
  if (session) {
    currentSessionId.value = id
    messages.value = session.messages || []
    setTimeout(scrollToBottom, 100)
  }
}

const switchSessionWithClose = (id) => {
  switchSession(id)
  isSidebarOpen.value = false
}

const deleteSession = (id) => {
  sessions.value = sessions.value.filter(s => s.id !== id)
  if (sessions.value.length === 0) {
    startNewChat()
  } else if (currentSessionId.value === id) {
    switchSession(sessions.value[0].id)
  } else {
    saveSessions()
  }
}

const saveSessions = () => {
  // 简单的容量保护：每个模式只保留最近 15 个有效会话，防止 LocalStorage 溢出 (Task 6)
  if (sessions.value.length > 15) {
    sessions.value = sessions.value.slice(0, 15)
  }
  
  try {
    localStorage.setItem(`zyd_chat_sessions_${currentMode.value}`, JSON.stringify(sessions.value))
  } catch (err) {
    if (err.name === 'QuotaExceededError') {
      console.warn('LocalStorage quota exceeded, trying to clear oldest session...')
      sessions.value.pop()
      saveSessions()
    }
  }
}

let saveTimeout = null
const debouncedSaveSessions = () => {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    saveSessions()
  }, 1000) // 1秒防抖，避免流式响应时频繁触发磁盘IO
}

watch(() => messages.value.length, () => {
  scrollToBottom()
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.messages = messages.value
    const firstUser = messages.value.find(m => m.role === 'user')
    if (firstUser && session.title === '新对话') {
      session.title = firstUser.content.slice(0, 15) + (firstUser.content.length > 15 ? '...' : '')
    }
    debouncedSaveSessions()
  }
})

watch(isGenerating, (newVal, oldVal) => {
  if (oldVal === true && newVal === false) {
    saveSessions()
    scrollToBottom()
  }
})

const presetMsg = (msg) => {
  inputMsg.value = msg
  sendMessage()
}

const startCoachScenario = (name, prompt) => {
  inputMsg.value = `我要挑战【${name}】场景。`
  sendMessage()
}

const requestCoachEvaluation = () => {
  if (isGenerating.value) return
  if (messages.value.length === 0) return
  
  let content = "【结束对练】请现在切换为“资深销售总监/金牌导师”的人设，根据刚才的全部聊天记录，输出一份结构化的点评报告。"
  
  if (currentScenario.value && currentScenario.value.cargo_details) {
      const d = currentScenario.value.cargo_details
      content += `\n\n【导师后台参考真实参数】：\n- 实际底价参考货物：${d.item}, ${d.qty}件, ${d.gw_kg}kg/件, 尺寸 ${d.size_cm}\n- 隐藏陷阱：${d.hidden_issue || '无'}`
  }
  
  content += "\n\n要求报告必须包含：\n1. 战力评分(百分制)\n2. 询价功底(是否问全了参数、识破了陷阱)\n3. 盈利分析(对比底价，算算报亏了没)\n4. 金牌话术修正建议\n请用丰富的Markdown格式输出。"
  
  inputMsg.value = content
  sendMessage()
}

const autoGrow = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    const newHeight = Math.min(inputRef.value.scrollHeight, 120) // max 120px
    inputRef.value.style.height = newHeight + 'px'
  }
}

const sendMessage = async () => {
  let content = inputMsg.value.trim()
  if (!content && !selectedImage.value) return
  if (isGenerating.value) return
  
  if (!content && selectedImage.value) {
    content = "这是一份发货清单图片，请帮我分析各项货物的实重、尺寸，计算出计费重，并直接为我提供合适的报价方案。"
  }
  
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: content,
    image: selectedImage.value
  })
  
  inputMsg.value = ''
  const currentImage = selectedImage.value
  removeImage()
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  isGenerating.value = true
  abortController.value = new AbortController()
  
  const aiMsgId = `ai-${Date.now()}`
  messages.value.push({
    id: aiMsgId,
    role: 'assistant',
    content: '',
    isTyping: true
  })
  
  scrollToBottom()

  try {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      signal: abortController.value.signal,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        message: content,
        mode: currentMode.value,
        image_base64: currentImage ? currentImage.split(',')[1] : null,
        history: messages.value.slice(0, Math.max(0, messages.value.length - 2)).map(m => ({
          role: m.role,
          content: m.content
        }))
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      if (chunk) {
        const aiMsg = messages.value.find(m => m.id === aiMsgId)
        if (aiMsg) aiMsg.content += chunk
        scrollToBottom()
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('Generation stopped by user')
      const aiMsg = messages.value.find(m => m.id === aiMsgId)
      if (aiMsg) aiMsg.content += '\n\n*[用户已终止生成]*'
    } else {
      console.error('Chat error:', err)
      const aiMsg = messages.value.find(m => m.id === aiMsgId)
      if (aiMsg) aiMsg.content = `**Error**: ${err.message}. 请检查后端服务是否启动以及 API KEY 是否正确配置。`
    }
  } finally {
    const aiMsg = messages.value.find(m => m.id === aiMsgId)
    if (aiMsg) aiMsg.isTyping = false
    isGenerating.value = false
  }
}

const getCategoryClass = (cat) => {
  if (!cat) return 'cat-default';
  if (cat.includes('精明比价')) return 'cat-savvy';
  if (cat.includes('强势大货主')) return 'cat-big';
  if (cat.includes('麻烦纠纷')) return 'cat-angry';
  
  // 兜底映射
  const map = {
      '精明比价手': 'cat-savvy',
      '强势大货主': 'cat-big',
      '物流白纸侠': 'cat-newbie',
      '专业老油条': 'cat-pro',
      '怒火投诉者': 'cat-angry'
  };
  return map[cat] || 'cat-default';
}

const truncate = (text, len) => {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  height: 100dvh;
  background: var(--bg-primary);
  width: 100vw;
  overflow: hidden;
  transition: background-color 0.4s ease, --primary-gradient 0.4s ease;
}

.coach-mode {
  --bg-primary: #f0fdf4;
  --bg-tertiary: #dcfce7;
  --primary-gradient: linear-gradient(135deg, #059669 0%, #10b981 100%);
  --text-gradient: linear-gradient(135deg, #064e3b 0%, #047857 100%);
  --accent-color: #059669;
  --accent-hover: #047857;
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(16, 185, 129, 0.2);
}

.expert-mode {
  --bg-primary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --primary-gradient: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  --text-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  --accent-color: #3b82f6;
  --accent-hover: #2563eb;
  --glass-bg: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(59, 130, 246, 0.2);
}

.sidebar {
  width: 280px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background: var(--bg-tertiary);
  flex-shrink: 0;
}
.sidebar-header {
  padding: 20px;
}
.new-chat-btn {
  width: 100%;
  padding: 12px;
  background: var(--primary-gradient);
  color: white;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.new-chat-btn:hover {
  opacity: 0.9;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.2);
}

.sidebar-admin-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #4f46e5;
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  justify-content: center;
  transition: all 0.2s;
}

.sidebar-admin-btn:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.sidebar-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px;
}

.user-avatar-sidebar {
  width: 36px;
  height: 36px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name-sidebar {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.logout-link-sidebar {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 12px;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.logout-link-sidebar:hover {
  text-decoration: underline;
}
.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background 0.2s;
  border: 1px solid transparent;
}
.session-item:hover {
  background: rgba(0, 0, 0, 0.05);
}
.session-item.active {
  background: rgba(37, 99, 235, 0.08);
  color: var(--accent-color);
  border-color: rgba(37, 99, 235, 0.2);
}
.session-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}
.delete-btn {
  color: var(--text-secondary);
  opacity: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
}
.session-item:hover .delete-btn {
  opacity: 1;
}
.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  margin: 16px 24px 0;
  border-radius: 12px;
  z-index: 10;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 700;
}
.company-logo {
  height: 32px;
  width: auto;
  object-fit: contain;
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
}

.mode-selector-wrapper {
  display: flex;
  gap: 24px;
  align-items: center;
}
.mode-selector {
  display: flex;
  padding: 4px;
  border-radius: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  gap: 2px;
}
.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
  background: transparent;
  border: none;
  cursor: pointer;
}
.mode-btn .icon {
  font-size: 16px;
  opacity: 0.7;
}
.mode-btn:hover {
  color: var(--text-primary);
}
.mode-btn.active {
  background: var(--bg-secondary);
  color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
}
.mode-btn.active .icon {
  opacity: 1;
}

.nav-btn {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}
.nav-btn:hover {
  color: var(--text-primary);
}

.chat-main {
  flex: 1;
  overflow-y: auto;
  padding: 32px 50px;
  scroll-behavior: smooth;
}

.main-body-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.combat-intel-panel {
  width: 320px;
  margin: 0 24px 24px 0;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  padding: 20px;
  animation: slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.05);
  z-index: 50;
}

.intel-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(2px);
  z-index: 100;
}

@keyframes slideInRight {
  from { transform: translateX(30px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.panel-header h3 {
  font-size: 18px;
  margin: 0;
  color: var(--accent-color);
  font-weight: 700;
}

.icon-zap {
  color: #f59e0b;
  fill: #f59e0b;
  width: 20px;
}

.intel-section {
  margin-bottom: 24px;
}

.intel-section label {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.mission-goal {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 16px;
}

.persona-brief {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 8px;
}

.cargo-grid-mini {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.cargo-item {
  font-size: 13px;
  color: #475569;
}

.cargo-item span {
  color: #94a3b8;
  width: 50px;
  display: inline-block;
}

.intel-warning {
  margin-top: 10px;
  font-size: 12px;
  color: #dc2626;
  background: #fef2f2;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #dc2626;
}

.success-list {
  padding-left: 20px;
  margin: 0;
}

.success-list li {
  font-size: 13px;
  color: #047857;
  margin-bottom: 6px;
}

.quit-combat-btn {
  margin-top: auto;
  width: 100%;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.quit-combat-btn:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60%;
  padding-top: 40px;
  text-align: center;
  gap: 20px;
}
.welcome-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}
.welcome-avatar {
  width: 140px;
  height: 140px;
  object-fit: contain;
  margin-bottom: 24px;
  filter: drop-shadow(0 10px 20px rgba(0,0,0,0.08));
  animation: float 6s ease-in-out infinite;
}
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}
.welcome-screen h2.welcome-name {
  font-size: 36px;
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}
.welcome-screen h2.welcome-slogan {
  font-size: 24px;
  color: var(--text-primary);
  opacity: 0.9;
  font-weight: 500;
}
.welcome-screen p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}
.suggestion-chips {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}
.suggestion-chips button {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  padding: 12px 20px;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
}
.suggestion-chips button:hover {
  background: rgba(0, 0, 0, 0.03);
  border-color: var(--accent-hover);
}

.scenario-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 800px;
  margin: 0 auto;
}
.scenario-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  padding: 16px;
  width: 280px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  text-align: left;
  overflow: hidden;
}
.scenario-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(16, 185, 129, 0.1);
  border-color: var(--accent-color);
}
.scenario-card .card-main-info {
  width: 100%;
}
.scenario-card .emoji-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.scenario-card .emoji {
  font-size: 24px;
}
.scenario-card h4 {
  margin: 0;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  flex: 1;
  word-break: break-all;
}
.card-header-row {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 6px;
}
.category-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 600;
  display: inline-block;
}
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.category-grid.subjects {
  grid-template-columns: repeat(2, 1fr);
  max-width: 800px;
}

.category-step-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.category-step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 800px;
  margin: 0 auto 16px;
}

.back-link {
  background: none;
  border: none;
  color: var(--accent-color);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
}

.back-link:hover {
  text-decoration: underline;
}

.category-main-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  padding: 24px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
}

.category-main-card:hover {
  transform: translateY(-6px) scale(1.02);
  border-color: var(--accent-color);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 20px 40px rgba(16, 185, 129, 0.15);
}

.cat-emoji {
  font-size: 48px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}

.cat-info h3 {
  margin: 0 0 4px 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
}

.cat-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.scenario-list-view {
  animation: slideIn 0.4s ease-out;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 0 16px;
}

.back-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.scenario-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
}

.coach-action-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
  animation: fadeIn 0.3s ease;
}
.evaluate-btn {
  background: var(--primary-gradient);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  transition: transform 0.2s, opacity 0.2s;
}
.evaluate-btn:hover {
  transform: translateY(-2px);
  opacity: 0.95;
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}
.evaluate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.message-wrapper {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}
.message-wrapper.user {
  flex-direction: row-reverse;
}
.avatar {
  flex-shrink: 0;
}
.avatar-container.assistant {
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  overflow: hidden;
  padding: 0;
}
.xiaoyi-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.ai-avatar-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.user-avatar {
  background: var(--bg-tertiary);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
.message-content {
  max-width: 80%;
  padding: 16px 20px;
  line-height: 1.6;
}
.message-image-container {
  margin-bottom: 12px;
}
.chat-message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  cursor: zoom-in;
  border: 1px solid var(--border-color);
  display: block;
}
.message-wrapper.user .message-content {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.2);
}

:deep(.markdown-body p) { margin-bottom: 12px; }
:deep(.markdown-body p:last-child) { margin-bottom: 0; }
:deep(.markdown-body table) { 
  width: 100%; border-collapse: collapse; margin-bottom: 16px; 
}
:deep(.markdown-body th), :deep(.markdown-body td) { 
  border: 1px solid var(--border-color); padding: 8px; 
}
:deep(.markdown-body th) { background: var(--bg-tertiary); }
:deep(.markdown-body code) { 
  background: var(--bg-secondary); padding: 2px 6px; border-radius: 4px; font-family: monospace; 
}

.cursor-blink {
  display: inline-block;
  width: 6px;
  height: 16px;
  background: var(--text-primary);
  margin-left: 4px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }

.chat-footer {
  padding: 0 15% 32px;
}
.input-container {
  display: flex;
  flex-direction: column;
  transition: border-color 0.3s;
  border-radius: 12px;
  overflow: hidden;
}
.input-container:focus-within {
  border-color: var(--accent-hover);
}
.image-preview-area {
  padding: 12px 16px 0;
  position: relative;
  display: inline-block;
  align-self: flex-start;
}
.image-preview {
  max-width: 100px;
  max-height: 100px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  object-fit: cover;
}
.remove-image-btn {
  position: absolute;
  top: 4px;
  right: 8px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.remove-image-btn:hover {
  background: var(--danger-color);
  color: white;
}
.input-box {
  display: flex;
  align-items: flex-end;
  padding: 12px 16px;
  gap: 12px;
}
.upload-pic-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  margin-bottom: 2px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.upload-pic-btn:hover {
  background: var(--bg-secondary);
  color: var(--accent-color);
}
.icon-img {
  width: 20px;
  height: 20px;
}
.input-box textarea {
  flex: 1;
  resize: none;
  font-size: 16px;
  color: var(--text-primary);
  max-height: 120px;
  padding: 4px 0;
  background: transparent;
  border: none;
  outline: none;
}
.input-box textarea::placeholder {
  color: var(--text-secondary);
}
.send-btn {
  background: var(--accent-color);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 2px;
  border: none;
  cursor: pointer;
}
.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.stop-btn {
  background: var(--danger-color, #ef4444);
}
.stop-btn:hover {
  background: #dc2626 !important;
}
.send-btn:disabled {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: not-allowed;
}
.icon-send { width: 18px; height: 18px; }

.disclaimer {
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 12px;
}

/* Responsive Design */
.menu-toggle {
  display: none;
  background: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  padding: 8px;
  margin-right: 8px;
}

.nav-left {
  display: flex;
  align-items: center;
}

@media (max-width: 1024px) {
  .chat-main {
    padding: 32px 5%;
  }
  .chat-footer {
    padding: 0 5% 32px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: 10px 0 30px rgba(0,0,0,0.1);
  }
  
  .sidebar.show {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.3);
    backdrop-filter: blur(4px);
    z-index: 999;
  }

  .sidebar-overlay.show {
    display: block;
  }

  .menu-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .chat-nav {
    margin: 8px 8px 0;
    padding: 10px 12px;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .brand-divider {
    display: none;
  }

  .gradient-text {
    font-size: 14px;
  }
  
  .company-logo {
    height: 22px;
  }

  .mode-selector-wrapper {
    order: 3;
    width: 100%;
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .mode-selector {
    width: 100%;
    justify-content: center;
    background: rgba(0, 0, 0, 0.03);
    border-radius: 10px;
    padding: 2px;
  }

  .mode-btn {
    flex: 1;
    justify-content: center;
    padding: 6px 10px;
    font-size: 13px;
    white-space: nowrap;
  }

  .chat-main {
    padding: 20px 16px;
  }

  .welcome-screen h2.welcome-name {
    font-size: 24px;
  }

  .welcome-screen h2.welcome-slogan {
    font-size: 18px;
  }

  .category-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .category-grid.subjects {
    grid-template-columns: 1fr;
  }

  .category-main-card {
    padding: 16px;
    gap: 12px;
  }

  .cat-emoji {
    font-size: 36px;
  }

  .cat-info h3 {
    font-size: 16px;
  }

  .category-step-label {
    font-size: 12px;
    margin-bottom: 12px;
  }

  .message-content {
    max-width: 90%;
    font-size: 15px;
  }

  .chat-footer {
    padding: 0 12px 20px;
  }
  
  .input-box {
    padding: 10px 14px;
  }
  
  .nav-links {
    display: none;
  }

  .notices-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(8px);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .notices-modal {
    width: 100%;
    max-width: 500px;
    max-height: 80vh;
    background: var(--bg-primary);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: modalIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes modalIn {
    from { opacity: 0; transform: scale(0.95) translateY(10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }

  .notices-modal-header {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .notices-modal-header h3 {
    margin: 0;
    font-size: 18px;
    white-space: nowrap;
  }

  .notices-tabs {
    display: flex;
    background: var(--bg-tertiary);
    padding: 4px;
    border-radius: 8px;
    gap: 4px;
  }

  .notices-tabs button {
    padding: 4px 12px;
    font-size: 12px;
    border-radius: 6px;
    color: var(--text-secondary);
    transition: all 0.2s;
  }

  .notices-tabs button.active {
    background: #ffffff;
    color: var(--accent-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }

  .close-modal-btn {
    color: var(--text-secondary);
    cursor: pointer;
  }

  .notices-modal-content {
    flex: 1;
    overflow-y: auto;
    padding: 0;
  }

  .notice-list-scroll {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .notice-card {
    background: var(--bg-tertiary);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
  }

  .notice-date {
    font-size: 11px;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }

  .notice-body {
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.5;
    white-space: pre-wrap;
  }

  .notice-loading, .notice-empty {
    padding: 40px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 14px;
  }

  .intel-toggle-mobile {
    display: flex;
    align-items: center;
    gap: 4px;
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #10b981;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 10px;
    cursor: pointer;
  }

  .intel-toggle-mobile.active {
    background: #10b981;
    color: white;
  }

  .intel-overlay.show {
    display: block;
  }

  .combat-intel-panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 85%;
    max-width: 340px;
    margin: 0;
    border-radius: 20px 0 0 20px;
    z-index: 1001;
    transform: translateX(100%);
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: -20px 0 40px rgba(0,0,0,0.15);
  }

  .combat-intel-panel.show-mobile {
    transform: translateX(0);
  }
}
</style>
