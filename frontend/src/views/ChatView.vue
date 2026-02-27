<template>
  <div class="app-layout">
    <aside class="sidebar glass-panel">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="startNewChat">
          <span class="icon">+</span> 新对话
        </button>
      </div>
      <div class="session-list">
        <div v-for="session in sessions" :key="session.id" 
             :class="['session-item', { active: session.id === currentSessionId }]"
             @click="switchSession(session.id)">
          <div class="session-title">{{ session.title || '新对话' }}</div>
          <button class="delete-btn" @click.stop="deleteSession(session.id)" title="删除对话">×</button>
        </div>
      </div>
    </aside>

    <div class="chat-container">
      <!-- Navbar -->
      <nav class="chat-nav glass-panel">
        <div class="brand">
          <img src="/logo.png" alt="仲易达集团" class="company-logo" />
          <span class="brand-divider">|</span>
          <span class="gradient-text">小易智能助手</span>
        </div>

        <!-- Mode Selector -->
        <div class="mode-selector">
          <button 
            :class="['mode-btn', { active: currentMode === 'general' }]"
            @click="currentMode = 'general'"
          >
            <span class="icon">✨</span> 全能助手
          </button>
          <button 
            :class="['mode-btn', { active: currentMode === 'coach' }]"
            @click="currentMode = 'coach'"
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
          <h2 class="welcome-name">您好，我是小易，您的全能助手</h2>
          <h2 class="welcome-slogan">把繁琐的流程交给我，把专注留给真正重要的事情。</h2>
          <p>今天想先解决什么？</p>
          <div class="suggestion-chips">
            <button @click="presetMsg('我们的出勤打卡制度是怎样的？')">公司的出勤打卡制度是怎样的？</button>
            <button @click="presetMsg('帮我查一下美西航线这周的最新报价')">查一下美西航线最新报价</button>
          </div>
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
              <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <span v-if="msg.isTyping" class="cursor-blink"></span>
            </div>
          </div>
        </div>
      </main>

      <!-- Input Area -->
      <footer class="chat-footer">
        <div class="input-box glass-panel">
          <textarea 
            v-model="inputMsg" 
            @keydown.enter.prevent="sendMessage"
            placeholder="给小易发送消息，按 ENTER 键发送..."
            rows="1"
            ref="inputRef"
            @input="autoGrow"
          ></textarea>
          <button class="send-btn" :disabled="!inputMsg.trim() || isGenerating" @click="sendMessage">
            <IconSend class="icon-send" />
          </button>
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
import { Send as IconSend } from 'lucide-vue-next'

const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const chatMain = ref(null)
const inputRef = ref(null)
const currentMode = ref('general')

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

onMounted(() => {
  const saved = localStorage.getItem('zyd_chat_sessions')
  if (saved) {
    try {
      sessions.value = JSON.parse(saved)
    } catch(e) {}
  }
  if (sessions.value.length === 0) {
    startNewChat()
  } else {
    currentSessionId.value = sessions.value[0].id
    messages.value = sessions.value[0].messages || []
  }
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

const switchSession = (id) => {
  const session = sessions.value.find(s => s.id === id)
  if (session) {
    currentSessionId.value = id
    messages.value = session.messages || []
    setTimeout(scrollToBottom, 100)
  }
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
  localStorage.setItem('zyd_chat_sessions', JSON.stringify(sessions.value))
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

const autoGrow = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    const newHeight = Math.min(inputRef.value.scrollHeight, 120) // max 120px
    inputRef.value.style.height = newHeight + 'px'
  }
}

const sendMessage = async () => {
  const content = inputMsg.value.trim()
  if (!content || isGenerating.value) return
  
  messages.value.push({
    role: 'user',
    content: content
  })
  
  inputMsg.value = ''
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  isGenerating.value = true
  
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
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: content,
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
    console.error('Chat error:', err)
    messages.value[aiMsgIdx].content = `**Error**: ${err.message}. 请检查后端服务是否启动以及 API KEY 是否正确配置。`
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
  background: var(--bg-primary);
  width: 100vw;
  overflow: hidden;
}
.sidebar {
  width: 260px;
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
  height: 80%;
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
.input-box {
  display: flex;
  align-items: flex-end;
  padding: 12px 16px;
  gap: 12px;
  transition: border-color 0.3s;
}
.input-box:focus-within {
  border-color: var(--accent-hover);
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
</style>
