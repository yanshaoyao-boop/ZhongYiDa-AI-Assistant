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
              <button @click="presetMsg('我们的出勤打卡制度是怎样的？')">公司的出勤打卡制度是怎样的？</button>
              <button @click="presetMsg('帮我查一下美西航线这周的最新报价')">查一下美西航线最新报价</button>
            </div>
          </template>
          <template v-else>
            <h2 class="welcome-name">欢迎来到知识教练模式</h2>
            <h2 class="welcome-slogan">场景化沉浸式对练，打造金牌业务员。</h2>
            <p>请选择一个演练场景开始实战，或直接请教基础知识：</p>
            
            <div class="scenario-cards">
              <div class="scenario-card" @click="startCoachScenario('抠门比价型', '你是一个手里拿了好几个极低价格的抠门客户，来找货代询价，疯狂试探底价。请直接开始第一句话，不要说多余的废话。')">
                <span class="emoji">💰</span>
                <div class="card-info">
                  <h4>抠门比价型</h4>
                  <p>疯狂压价，拿着别家的低价来刁难</p>
                </div>
              </div>
              <div class="scenario-card" @click="startCoachScenario('严苛大卖型', '你是一个每月走50条柜子的大卖，对时效、延误赔偿、账期要求极高，压迫感强。请直接开始第一句话，挑战我的专业度。')">
                <span class="emoji">🏢</span>
                <div class="card-info">
                  <h4>严苛大卖型</h4>
                  <p>货量大要求高，考验专业度与气场</p>
                </div>
              </div>
              <div class="scenario-card" @click="startCoachScenario('纯小白型', '你是一个第一次发亚马逊FBA的小白客户，什么都不懂，连DDP是什么也不知道，但又要得急。请直接开始第一句话。')">
                <span class="emoji">👶</span>
                <div class="card-info">
                  <h4>亚马逊纯小白</h4>
                  <p>第一次发货，需要极大的耐心和引导</p>
                </div>
              </div>
            </div>
            
            <div class="suggestion-chips" style="margin-top: 24px;">
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
import { ref, watch, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { Send as IconSend, Menu as IconMenu, X as IconX, Image as IconImage, XCircle as IconXCircle, Square as IconSquare } from 'lucide-vue-next'

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
  localStorage.setItem(`zyd_chat_sessions_${currentMode.value}`, JSON.stringify(sessions.value))
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
    saveSessions()
  }
}, { deep: true })

const presetMsg = (msg) => {
  inputMsg.value = msg
  sendMessage()
}

const startCoachScenario = (name, prompt) => {
  inputMsg.value = `我要挑战【${name}】场景。${prompt}`
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
    const response = await fetch(`http://${window.location.hostname}:8000/api/chat/stream`, {
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
  width: 240px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  text-align: left;
}
.scenario-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(16, 185, 129, 0.1);
  border-color: var(--accent-color);
}
.scenario-card .emoji {
  font-size: 28px;
  margin-top: 2px;
}
.scenario-card h4 {
  margin: 0 0 4px 0;
  color: var(--text-primary);
  font-size: 16px;
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
    margin: 12px 12px 0;
    padding: 12px 16px;
  }

  .brand-divider {
    display: none;
  }

  .gradient-text {
    font-size: 16px;
  }
  
  .company-logo {
    height: 24px;
  }

  .mode-selector {
    display: none; /* Hide mode selector on very small screens to save space */
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
