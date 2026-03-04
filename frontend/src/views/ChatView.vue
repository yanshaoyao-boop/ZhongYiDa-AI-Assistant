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
        </div>

        <!-- Mode Selector -->
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
        </div>

        <div class="nav-links">
          <a href="/admin" class="nav-btn" target="_blank">管理员入口</a>
        </div>
      </nav>

      <!-- Chat Area -->
      <main class="chat-main" ref="chatMain">
        <div v-if="messages.length === 0" class="welcome-screen">
          <template v-if="currentMode === 'general'">
            <h2 class="welcome-name">您好，我是小易，您的全能助手</h2>
            <h2 class="welcome-slogan">把繁琐的流程交给我，把专注留给真正重要的事情。</h2>
            <p>今天想先解决什么？</p>
            <div class="suggestion-chips">
              <button @click="presetMsg('我能帮你做哪些事')">🤖 我能帮你做哪些事</button>
              <button @click="presetMsg('如何正确的使用小易')">📖 如何正确的使用小易</button>
            </div>
          </template>
          <template v-else>
            <h2 class="welcome-name">欢迎来到知识教练模式</h2>
            <h2 class="welcome-slogan">场景化沉浸式对练，打造金牌业务员。</h2>
            <p>请选择一个演练场景开始实战，或直接请教基础知识：</p>
            
            <!-- 5 大盲盒分类入口 -->
            <div class="category-grid">
              <div v-for="cat in mainCategories" :key="cat.name" 
                   class="category-main-card" 
                   @click="startRandomCoachInCategory(cat.name)">
                <span class="cat-emoji">{{ cat.emoji }}</span>
                <div class="cat-info">
                  <h3>{{ cat.name }}</h3>
                  <p>{{ cat.desc }}</p>
                </div>
              </div>
            </div>
            
            <div class="suggestion-chips" style="margin-top: 32px;">
              <button @click="presetMsg('能通俗地给我讲解一下什么是DDP和DDU吗？')">📖 常见物流基础名词讲解</button>
            </div>
          </template>
        </div>

        <div class="message-list">
          <div v-for="(msg, index) in messages" :key="index" 
               class="message-wrapper" :class="msg.role">
            <div class="avatar">
              <template v-if="msg.role === 'assistant'">
                <div class="avatar-container assistant">
                  <img src="/logo-icon.png" alt="AI" class="ai-avatar-icon" />
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

      <!-- Input Area -->
      <footer class="chat-footer">
        <div class="coach-action-bar" v-if="currentMode === 'coach' && messages.length > 0">
           <button class="evaluate-btn" @click="requestCoachEvaluation" :disabled="isGenerating">
              <span class="icon">📈</span> 结束对练并获取导师点评
           </button>
        </div>
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
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
const API_PORT = 8000
const API_BASE = `http://${window.location.hostname}:${API_PORT}`

const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const abortController = ref(null)

const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}
const chatMain = ref(null)
const inputRef = ref(null)
const currentMode = ref('general')
const isSidebarOpen = ref(false)

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
const selectedCategory = ref(null)
const mainCategories = [
  { name: '精明比价派', emoji: '💰', desc: '应对价格敏感、反复试探底价的客户' },
  { name: '强势大货主', emoji: '🏢', desc: '在舱位、时效与压迫式沟通中建立主权' },
  { name: '麻烦纠纷型', emoji: '💢', desc: '处理计费重、查验费、小白理解等纠纷' },
  { name: '美国线卖家', emoji: '🇺🇸', desc: '专注美森快船、海派、空派等美线实战' },
  { name: '欧洲线卖家', emoji: '🇪🇺', desc: '聚焦税号、清关、欧洲延迟等欧线博弈' }
]

const startRandomCoachInCategory = (categoryName) => {
  const matchingCases = coachCases.value.filter(c => {
    const cat = c.category || ''
    return cat.includes(categoryName) || categoryName.substring(0,3) === cat.substring(0,3)
  })
  
  if (matchingCases.length === 0) {
    alert(`库存里暂时没有【${categoryName}】类的案例，请管理员上传剧本素材。`)
    return
  }
  
  const randomCase = matchingCases[Math.floor(Math.random() * matchingCases.length)]
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

const renderMarkdown = (text) => {
  if (!text) return ''
  let cleaned = text.replace(/~~([\s\S]*?)~~/g, '$1')
  cleaned = cleaned.replace(/~+/g, '')
  return DOMPurify.sanitize(marked(cleaned))
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
  loadSessionsForMode(mode)
}

onMounted(() => {
  const oldSaved = localStorage.getItem('zyd_chat_sessions')
  if (oldSaved && !localStorage.getItem('zyd_chat_sessions_general')) {
    localStorage.setItem('zyd_chat_sessions_general', oldSaved)
  }
  loadSessionsForMode(currentMode.value)
  fetchCoachCases()
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

watch(() => messages.value, () => {
  scrollToBottom()
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.messages = messages.value
    const firstUser = messages.value.find(m => m.role === 'user')
    if (firstUser && session.title === '新对话') {
      session.title = firstUser.content.slice(0, 15) + (firstUser.content.length > 15 ? '...' : '')
    }
    debouncedSaveSessions() // 改为防抖保存
  }
}, { deep: true })

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
  
  const content = "【结束对练】请现在切换为“资深销售总监/金牌导师”的人设，根据刚才的全部聊天记录，输出一份结构化的点评报告，必须包含：\n1. 整体评分(百分制)\n2. 闪光点(我做得好的地方)\n3. 踩坑或丢分项(报错价、过度承诺或遗漏项)\n4. 话术修正建议(对比原来话术和建议话术)\n请用Markdown格式输出，并给出下一步改进建议。"
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
    role: 'user',
    content: content,
    image: selectedImage.value // Store image in history
  })
  
  inputMsg.value = ''
  const currentImage = selectedImage.value
  removeImage()
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  isGenerating.value = true
  abortController.value = new AbortController()
  
  const aiMsgIdx = messages.value.length
  messages.value.push({
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
        'Content-Type': 'application/json'
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
        messages.value[aiMsgIdx].content += chunk
        scrollToBottom()
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('Generation stopped by user')
      messages.value[aiMsgIdx].content += '\n\n*[用户已终止生成]*'
    } else {
      console.error('Chat error:', err)
      messages.value[aiMsgIdx].content = `**Error**: ${err.message}. 请检查后端服务是否启动以及 API KEY 是否正确配置。`
    }
  } finally {
    messages.value[aiMsgIdx].isTyping = false
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
  padding: 0 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.mode-selector {
  display: flex;
  padding: 4px;
  border-radius: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
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
  padding: 32px 15%;
  scroll-behavior: smooth;
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
  padding: 4px;
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

  .mode-selector {
    order: 3;
    width: 100%;
    margin-top: 12px;
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
}
</style>
