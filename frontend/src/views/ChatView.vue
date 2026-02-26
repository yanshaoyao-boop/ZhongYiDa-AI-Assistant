<template>
  <div class="chat-container">
    <!-- Navbar -->
    <nav class="chat-nav glass-panel">
      <div class="brand">
        <div class="ai-orb"></div>
        <span class="gradient-text">仲易达智能助手</span>
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
        <h2>您好，我是仲易达智能员工助手</h2>
        <p>我可以帮您解答公司制度，查询最新运费与报价情况。</p>
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
              <div class="ai-avatar">AI</div>
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
          placeholder="给智能助手发送消息，按 Enter 键发送..."
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
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { Send as IconSend } from 'lucide-vue-next'

const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const chatMain = ref(null)
const inputRef = ref(null)
const currentMode = ref('general')

const renderMarkdown = (text) => {
  if (!text) return ''
  return DOMPurify.sanitize(marked(text))
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatMain.value) {
    chatMain.value.scrollTop = chatMain.value.scrollHeight
  }
}

watch(() => messages.value, scrollToBottom, { deep: true })

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
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: content
  })
  
  inputMsg.value = ''
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  isGenerating.value = true
  
  // Create assistant placeholder
  const aiMsgIdx = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    isTyping: true
  })
  
  scrollToBottom()

  try {
    const response = await fetch('http://localhost:8000/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: content,
        // Only send last 4 real messages for context to avoid token limits
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
    messages.value[aiMsgIdx].content = `**Error**: ${err.message}. 请检查后端服务是否启动以及 Doubao API KEY 是否正确配置。`
  } finally {
    messages.value[aiMsgIdx].isTyping = false
    isGenerating.value = false
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
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
  font-size: 18px;
  font-weight: 700;
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
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
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
}
.mode-btn .icon {
  font-size: 16px;
  opacity: 0.7;
}
.mode-btn:hover {
  color: var(--text-primary);
}
.mode-btn.active {
  background: var(--glass-bg);
  color: var(--text-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.mode-btn.active .icon {
  opacity: 1;
}

.ai-orb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-gradient);
  box-shadow: 0 0 12px var(--accent-color);
  animation: pulse 2s infinite ease-in-out;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
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
  padding: 32px 20%;
  scroll-behavior: smooth;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 70%;
  text-align: center;
  gap: 16px;
}
.welcome-screen h2 {
  font-size: 32px;
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
}
.suggestion-chips button:hover {
  background: rgba(255, 255, 255, 0.1);
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
.ai-avatar {
  background: var(--primary-gradient);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
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
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

/* Custom Markdown styling */
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
:deep(.markdown-body pre code) {
  display: block; padding: 12px; overflow-x: auto; 
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
  padding: 0 20% 32px;
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
