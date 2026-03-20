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
        <!-- 设置按钮 -->
        <button class="sidebar-settings-btn" @click="showSettings = true">
          <IconSettings size="16" /> 设置
        </button>
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
              <div class="icon-wrapper">
                <IconAlertCircle size="18" class="icon" />
                <span v-if="hasNewNotice" class="notice-dot"></span>
              </div>
              重要通知
            </button>
            <button class="mode-btn" @click="openToolsCenter">
              <IconZap size="18" class="icon" /> 智能工具
            </button>
          </div>

          <div class="mode-selector">
            <button 
              :class="['mode-btn', { active: currentMode === 'general' }]"
              @click="switchMode('general')"
            >
              <IconZap size="18" class="icon" /> 全能助手
            </button>
            <button 
              :class="['mode-btn', { active: currentMode === 'coach' }]"
              @click="switchMode('coach')"
            >
              <IconTarget size="18" class="icon" /> 知识教练
            </button>
            <button 
              :class="['mode-btn', { active: currentMode === 'expert' }]"
              @click="switchMode('expert')"
            >
              <IconFileQuestion size="18" class="icon" /> 专家指导
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
              
              <!-- 入口选择：对练 vs 出题 -->
              <div v-if="coachSubMode === 'entrance'" class="coach-gates">
                <div class="category-main-card gate-card" @click="coachSubMode = 'practice'">
                  <div class="cat-icon-lg"><IconZap size="48" /></div>
                  <div class="cat-info">
                    <h3>教练对练</h3>
                    <p>场景化沉浸式对练，模拟真实业务沟通</p>
                  </div>
                </div>
                <div class="category-main-card gate-card" @click="startCoachQuizFlow">
                  <div class="cat-icon-lg"><IconTarget size="48" /></div>
                  <div class="cat-info">
                    <h3>教练出题</h3>
                    <p>单选题专项训练，巩固业务知识点</p>
                  </div>
                </div>
              </div>

              <!-- 教练对练流程 -->
              <template v-if="coachSubMode === 'practice'">
                <div class="category-step-header">
                  <button class="back-link" @click="coachSubMode = 'entrance'; selectedRegion = null; selectedPersona = null">← 返回主入口</button>
                  <div class="category-step-label" v-if="!selectedRegion">第一步：选择实战航线</div>
                </div>
                
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
                       @click="startCoachDetailedSubject(sub.name)">
                    <span class="cat-emoji">{{ sub.emoji }}</span>
                    <div class="cat-info">
                      <h3>{{ sub.name }}</h3>
                      <p>{{ sub.desc }}</p>
                    </div>
                  </div>
                </div>
              </template>

              <!-- 教练出题流程 -->
              <div v-if="coachSubMode === 'quiz'" class="quiz-flow">
                <!-- 步 1：选择题量 -->
                <div v-if="quizStep === 'count_selection'" class="quiz-setup">
                  <button class="back-link-quiz" @click="coachSubMode = 'entrance'">← 返回</button>
                  <h3>请选择本次训练题量</h3>
                  <div class="count-options">
                    <button class="count-btn" @click="fetchQuizQuestions(5)">5 道题</button>
                    <button class="count-btn" @click="fetchQuizQuestions(10)">10 道题</button>
                    <button class="count-btn" @click="fetchQuizQuestions(20)">20 道题</button>
                  </div>
                </div>

                <!-- 步 2：答题中 -->
                <div v-if="quizStep === 'answering'" class="quiz-card-container">
                  <div class="quiz-progress">
                    <span>题量进度: {{ currentQuizIdx + 1 }} / {{ quizQuestions.length }}</span>
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: ((currentQuizIdx + 1) / quizQuestions.length) * 100 + '%' }"></div>
                    </div>
                  </div>
                  
                  <div v-if="quizQuestions[currentQuizIdx]" class="quiz-card glass-panel">
                    <div class="quiz-question">{{ quizQuestions[currentQuizIdx].question }}</div>
                    <div class="quiz-options">
                      <button 
                        v-for="optObj in quizQuestions[currentQuizIdx].options" 
                        :key="optObj.key"
                        :class="['opt-btn', { 
                          selected: selectedOption === optObj.key,
                          correct: isQuizSubmitted && quizQuestions[currentQuizIdx].answer === optObj.key,
                          wrong: isQuizSubmitted && selectedOption === optObj.key && quizQuestions[currentQuizIdx].answer !== optObj.key
                        }]"
                        @click="selectQuizOption(optObj.key)"
                        :disabled="isQuizSubmitted"
                      >
                        <span class="opt-label">{{ optObj.key }}</span>
                        <span class="opt-text">{{ optObj.text }}</span>
                        <IconCheckCircle v-if="isQuizSubmitted && quizQuestions[currentQuizIdx].answer === optObj.key" size="18" class="status-icon" />
                        <IconXCircle v-if="isQuizSubmitted && selectedOption === optObj.key && quizQuestions[currentQuizIdx].answer !== optObj.key" size="18" class="status-icon" />
                      </button>
                    </div>

                    <div v-if="isQuizSubmitted" class="quiz-feedback-box animate-in">
                      <div :class="['feedback-header', selectedOption === quizQuestions[currentQuizIdx].answer ? 'text-correct' : 'text-wrong']">
                        <template v-if="selectedOption === quizQuestions[currentQuizIdx].answer">
                          <IconCheckCircle size="20" /> 回答正确！
                        </template>
                        <template v-else>
                          <IconXCircle size="20" /> 回答错误。正确答案是 【{{ quizQuestions[currentQuizIdx].answer }}】
                        </template>
                      </div>
                      <div class="quiz-explanation" v-if="quizQuestions[currentQuizIdx].explanation">
                        <strong>解析：</strong>{{ quizQuestions[currentQuizIdx].explanation }}
                      </div>
                      <button class="next-quiz-btn" @click="nextQuizQuestion">
                        {{ currentQuizIdx === quizQuestions.length - 1 ? '查看结果' : '下一题' }}
                        <IconChevronRight size="18" />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 步 3：总结页 -->
                <div v-if="quizStep === 'result'" class="quiz-result-card glass-panel">
                  <IconTrophy size="64" class="trophy-icon" />
                  <h2>训练完成！</h2>
                  <div class="result-stats">
                    <div class="stat-item">
                      <label>答对题数</label>
                      <span class="stat-value text-correct">{{ quizStats.correct }}</span>
                    </div>
                    <div class="stat-item">
                      <label>正确率</label>
                      <span class="stat-value">{{ Math.round((quizStats.correct / quizStats.total) * 100) }}%</span>
                    </div>
                  </div>
                  <button class="restart-quiz-btn" @click="restartQuiz">
                    <IconRotateCcw size="18" /> 重新开始
                  </button>
                </div>
              </div>

              <div v-if="coachSubMode !== 'quiz'" class="suggestion-chips" style="margin-top: 32px;">
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
      <footer v-if="coachSubMode !== 'quiz'" class="chat-footer">
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

    <!-- Notices Premium Modal -->
    <Teleport to="body">
      <div v-if="showNotices" class="premium-modal-backdrop" @click.self="showNotices = false">
        <div class="premium-modal notice-modal animate-modal">
          <div class="modal-header">
            <div class="header-top">
              <div class="header-main">
                <IconAlertCircle class="header-icon" />
                <h3>重要通知中心</h3>
              </div>
              <button class="close-btn-inner" @click="showNotices = false"><IconX /></button>
            </div>
            <div class="header-tabs">
              <button :class="{ active: noticeTab === 'current' }" @click="noticeTab = 'current'">当前通知</button>
              <button :class="{ active: noticeTab === 'history' }" @click="noticeTab = 'history'">往期回顾</button>
            </div>
          </div>
          
          <div class="modal-body custom-scrollbar">
            <div v-if="loadingNotices" class="modal-loading">
              <div class="loading-spinner"></div>
              <span>从服务器同步中...</span>
            </div>
            <div v-else-if="displayNotices.length === 0" class="modal-empty text-neutral">
              <IconMenu size="48" />
              <p>暂无相关通知内容</p>
            </div>
            <div v-else class="notice-list-premium">
              <div v-for="n in displayNotices" :key="n.id" class="notice-item-premium" @click="handleNoticeClick(n)">
                <div class="notice-meta">
                  <span class="notice-tag">NEWS</span>
                  <span class="notice-time">{{ formatDate(n.created_at) }}</span>
                </div>
                <div class="notice-author">发布人：{{ n.created_by_name || '系统发布' }}</div>
                <div class="notice-content-text">{{ n.content }}</div>
                <div class="notice-action">点击对话深入了解 <IconChevronRight size="14" /></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 设置弹窗 -->
    <Teleport to="body">
      <div v-if="showSettings" class="premium-modal-backdrop" @click.self="closeSettings">
        <div class="premium-modal settings-modal animate-modal">
          <div class="modal-header">
            <div class="header-top">
              <div class="header-main">
                <IconSettings class="header-icon" />
                <h3>用户设置</h3>
              </div>
              <button class="close-btn-inner" @click="closeSettings"><IconX /></button>
            </div>
          </div>

          <div class="modal-body custom-scrollbar">
            <!-- 输出长度 -->
            <div class="settings-section">
              <div class="settings-label">📝 小易回复长度偏好</div>
              <p class="settings-desc">控制小易每次回答内容的详尽程度</p>
              <div class="output-length-group">
                <button
                  v-for="opt in outputLengthOptions"
                  :key="opt.value"
                  :class="['length-btn', { active: outputLength === opt.value }]"
                  @click="setOutputLength(opt.value)"
                >
                  <span class="length-icon">{{ opt.icon }}</span>
                  <span class="length-label">{{ opt.label }}</span>
                  <span class="length-desc">{{ opt.desc }}</span>
                </button>
              </div>
            </div>

            <div class="settings-divider"></div>

            <!-- 修改密码 -->
            <div class="settings-section">
              <div class="settings-label">🔑 修改密码</div>
              <p class="settings-desc">修改您的登录密码（至少 6 位）</p>
              <div class="pwd-form">
                <input
                  v-model="pwdForm.oldPwd"
                  type="password"
                  placeholder="请输入当前密码"
                  class="settings-input"
                />
                <input
                  v-model="pwdForm.newPwd"
                  type="password"
                  placeholder="请输入新密码（至少 6 位）"
                  class="settings-input"
                />
                <input
                  v-model="pwdForm.confirmPwd"
                  type="password"
                  placeholder="再次确认新密码"
                  class="settings-input"
                />
                <div v-if="pwdMsg" :class="['pwd-msg', pwdMsg.type]">{{ pwdMsg.text }}</div>
                <button class="pwd-submit-btn" @click="submitChangePassword" :disabled="pwdLoading">
                  {{ pwdLoading ? '提交中...' : '确认修改' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
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
  ShieldCheck as IconShieldCheck,
  Target as IconTarget,
  FileQuestion as IconFileQuestion,
  ChevronRight as IconChevronRight,
  RotateCcw as IconRotateCcw,
  ArrowLeft as IconArrowLeft,
  CheckCircle as IconCheckCircle,
  AlertCircle as IconAlertCircle,
  Trophy as IconTrophy,
  Settings as IconSettings
} from 'lucide-vue-next'
// 使用相对路径，配合 vite.config.js 中的 dev proxy 转发到后端
// 生产环境由 nginx/反向代理处理 /api 路由
const API_BASE = ''

const auth = useAuthStore()
const router = useRouter()

// ====== 设置弹窗逻辑 ======
const showSettings = ref(false)
const closeSettings = () => { showSettings.value = false; pwdMsg.value = null; pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' } }

// 输出长度偏好
const OUTPUT_LENGTH_KEY = 'zyd_output_length'
const outputLengthOptions = [
  { value: 'short', icon: '⚡', label: '简洁', desc: '精炼核心要点，适合快速查询' },
  { value: 'medium', icon: '📋', label: '标准', desc: '均衡详细，适合日常对话' },
  { value: 'long', icon: '📄', label: '详细', desc: '完整展开，适合复杂分析' }
]
const outputLength = ref(localStorage.getItem(OUTPUT_LENGTH_KEY) || 'medium')
const setOutputLength = (val) => {
  outputLength.value = val
  localStorage.setItem(OUTPUT_LENGTH_KEY, val)
}

// 修改密码
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdMsg = ref(null)
const pwdLoading = ref(false)
const submitChangePassword = async () => {
  pwdMsg.value = null
  const { oldPwd, newPwd, confirmPwd } = pwdForm.value
  if (!oldPwd || !newPwd || !confirmPwd) {
    pwdMsg.value = { type: 'error', text: '请填写所有密码字段' }
    return
  }
  if (newPwd !== confirmPwd) {
    pwdMsg.value = { type: 'error', text: '两次输入的新密码不一致' }
    return
  }
  if (newPwd.length < 6) {
    pwdMsg.value = { type: 'error', text: '新密码不能少于 6 位' }
    return
  }
  pwdLoading.value = true
  try {
    await axios.post('/api/auth/change-password', { old_password: oldPwd, new_password: newPwd })
    pwdMsg.value = { type: 'success', text: '✅ 密码修改成功！下次登录将使用新密码。' }
    pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
  } catch (err) {
    pwdMsg.value = { type: 'error', text: err?.response?.data?.detail || '修改失败，请检查当前密码是否正确' }
  } finally {
    pwdLoading.value = false
  }
}


const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const abortController = ref(null)

const showNotices = ref(false)
const noticeTab = ref('current')
const allNotices = ref({ current: [], history: [] })
const loadingNotices = ref(false)
const hasNewNotice = ref(false)

const checkNewNotices = async () => {
  try {
    const res = await axios.get('/api/notices/current')
    const currentNotices = res.data
    if (currentNotices.length > 0) {
      const lastReadId = localStorage.getItem('last_read_notice_id')
      const latestId = currentNotices[0].id.toString()
      if (lastReadId !== latestId) {
        hasNewNotice.value = true
      }
    }
  } catch (err) {
    console.error("Failed to check new notices:", err)
  }
}

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
    if (allNotices.value.current.length > 0) {
      localStorage.setItem('last_read_notice_id', allNotices.value.current[0].id.toString())
      hasNewNotice.value = false
    }
  }
}

const displayNotices = computed(() => {
  return noticeTab.value === 'current' ? allNotices.value.current : allNotices.value.history
})

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const handleNoticeClick = (notice) => {
  showNotices.value = false
  startNewChat()
  inputMsg.value = `针对 ${notice.created_by_name || '系统发布'} 发布的这条通知内容，我想详细了解一下：\n\n"${notice.content}"`
  sendMessage()
}

const openToolsCenter = () => {
  router.push('/tools')
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
  return `${auth.userName || '您'}，您好！我是小易，您的智能助手。`
}

const welcomeMsg = ref(getDynamicGreeting())

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

const fetchPublicSettings = async () => {
  try {
    const res = await axios.get('/api/settings/public')
    if (res.data.ai_welcome_message) {
      welcomeMsg.value = res.data.ai_welcome_message.replace('{name}', auth.userName || '您')
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

// Coach Quiz State
const coachSubMode = ref('entrance') // entrance, practice, quiz
const quizStep = ref('count_selection') // count_selection, answering, result
const quizQuestions = ref([])
const currentQuizIdx = ref(0)
const quizAnswers = ref([])
const selectedQuizCount = ref(5)
const isQuizSubmitted = ref(false)
const selectedOption = ref(null)
const quizStats = ref({ correct: 0, total: 0 })

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

const startCoachDetailedSubject = (subName) => {
  coachSubMode.value = 'practice'
  startRandomCoachDetailed(subName)
}

const startCoachQuizFlow = () => {
  coachSubMode.value = 'quiz'
  quizStep.value = 'count_selection'
}

const fetchQuizQuestions = async (count) => {
  selectedQuizCount.value = count
  try {
    const res = await axios.get(`${API_BASE}/api/coach-quiz/session?count=${count}`)
    quizQuestions.value = res.data.questions || []
    currentQuizIdx.value = 0
    quizAnswers.value = []
    quizStep.value = 'answering'
    isQuizSubmitted.value = false
    selectedOption.value = null
    quizStats.value = { correct: 0, total: quizQuestions.value.length }
  } catch (err) {
    console.error("Failed to fetch quiz questions:", err)
    alert("获取题目失败，请检查网络或题库状态。")
    coachSubMode.value = 'entrance'
  }
}

const selectQuizOption = (opt) => {
  if (isQuizSubmitted.value) return
  selectedOption.value = opt
  isQuizSubmitted.value = true
  
  const current = quizQuestions.value[currentQuizIdx.value]
  const isCorrect = opt === current.answer
  if (isCorrect) quizStats.value.correct++
  
  quizAnswers.value.push({
    question: current.question,
    userAnswer: opt,
    correctAnswer: current.answer,
    isCorrect: isCorrect,
    explanation: current.explanation
  })
}

const nextQuizQuestion = () => {
  if (currentQuizIdx.value < quizQuestions.value.length - 1) {
    currentQuizIdx.value++
    isQuizSubmitted.value = false
    selectedOption.value = null
  } else {
    quizStep.value = 'result'
  }
}

const restartQuiz = () => {
  coachSubMode.value = 'entrance'
  quizStep.value = 'count_selection'
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
  } else if (mode === 'coach') {
    selectedRegion.value = null 
    selectedPersona.value = null
    coachSubMode.value = 'entrance'
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
  checkNewNotices()
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
        message: (outputLength.value === 'short' ? '[输出偏好:极致精简] ' : outputLength.value === 'long' ? '[输出偏好:详尽展开] ' : '') + content,
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

/* Icons & Badges */
.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.notice-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  background-color: #ef4444;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
  animation: notice-pulse 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
  z-index: 2;
}

@keyframes notice-pulse {
  0% { transform: scale(0.8); opacity: 0.8; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.8); opacity: 0.8; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
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

/* Coach Gates */
.coach-gates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 800px;
  margin: 40px auto;
}
.gate-card {
  flex-direction: column;
  text-align: center;
  padding: 40px 20px;
}
.cat-icon-lg {
  margin-bottom: 20px;
  background: var(--bg-tertiary);
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  color: var(--accent-color);
}

/* Quiz Flow */
.quiz-flow {
  max-width: 700px;
  margin: 20px auto;
  animation: fadeIn 0.4s ease;
}
.back-link-quiz {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  margin-bottom: 10px;
}
.count-options {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 20px;
}
.count-btn {
  padding: 12px 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}
.count-btn:hover {
  background: var(--accent-color);
  color: white;
}

.quiz-card-container {
  margin-top: 20px;
}
.quiz-progress {
  margin-bottom: 30px;
}
.progress-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  margin-top: 8px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s ease;
}

.quiz-card {
  padding: 32px;
  border-radius: 20px;
}
.quiz-question {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 24px;
  line-height: 1.5;
}
.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.opt-btn {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: white;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  gap: 12px;
}
.opt-btn:hover:not(:disabled) {
  border-color: var(--accent-color);
  background: #f0fdf4;
}
.opt-label {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: 50%;
  font-weight: 700;
}
.opt-text { flex: 1; }
.opt-btn.correct { border-color: #10b981; background: #ecfdf5; }
.opt-btn.wrong { border-color: #ef4444; background: #fef2f2; }
.opt-btn.selected { border-color: var(--accent-color); box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }

.quiz-feedback-box {
  margin-top: 24px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: 12px;
}
.feedback-header {
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.text-correct { color: #10b981; }
.text-wrong { color: #ef4444; }
.quiz-explanation {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.next-quiz-btn {
  margin-top: 20px;
  width: 100%;
  padding: 12px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
}

.quiz-result-card {
  text-align: center;
  padding: 60px 40px;
  border-radius: 30px;
}
.result-stats {
  display: flex;
  gap: 40px;
  justify-content: center;
  margin: 32px 0;
}
.stat-item {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 32px;
  font-weight: 800;
}
.restart-quiz-btn {
  padding: 12px 32px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 auto;
  cursor: pointer;
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

/* Premium Global Modal (Shared) */
.premium-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.premium-modal {
  width: 100%;
  max-width: 600px;
  max-height: 85vh;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  color: var(--accent-color);
  width: 24px;
  height: 24px;
}

.header-main h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
}

.close-btn-inner {
  background: rgba(0, 0, 0, 0.05);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.close-btn-inner:hover {
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-primary);
  transform: rotate(90deg);
}

.header-tabs {
  display: flex;
  gap: 8px;
  background: rgba(0,0,0,0.05);
  padding: 4px;
  border-radius: 12px;
  align-self: flex-start;
}

.header-tabs button {
  padding: 6px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.header-tabs button.active {
  background: white;
  color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.notice-list-premium {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notice-item-premium {
  padding: 20px;
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.2s;
}

.notice-item-premium:hover {
  transform: translateX(4px);
  border-color: var(--accent-color);
}

.notice-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.notice-tag {
  background: #fef2f2;
  color: #ef4444;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
}

.notice-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.notice-content-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.notice-author {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.notice-action {
  font-size: 13px;
  color: var(--accent-color);
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}

.modal-loading, .modal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(16, 185, 129, 0.1);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
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

/* ====== 设置按钮 (同步管理员入口风格) ====== */
/* ====== 设置按钮 (同步管理员入口风格 - 深度优化) ====== */
.sidebar-settings-btn {
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
  display: flex; /* 确保内容居中 */
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  cursor: pointer;
  border: none;
  font-family: inherit; /* 统一字体 */
}

.sidebar-settings-btn:hover {
  background: #4338ca;
  transform: translateY(-1px);
  opacity: 0.9; 
}

.sidebar-settings-btn:active {
  transform: translateY(1px);
  background: #3730a3;
}

/* ====== 设置弹窗 ====== */
.settings-modal {
  width: 460px;
  max-width: 95vw;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.settings-section {
  padding: 20px 0;
}
.settings-label {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}
.settings-desc {
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 14px;
}
.settings-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 0;
}

/* 输出长度选项 */
.output-length-group {
  display: flex;
  gap: 10px;
}
.length-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.2s ease;
}
.length-btn:hover {
  border-color: #6366f1;
  background: #f0f0ff;
}
.length-btn.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #ede9fe, #e0e7ff);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}
.length-icon { font-size: 22px; }
.length-label { font-size: 13px; font-weight: 700; color: #1e293b; }
.length-desc { font-size: 10px; color: #94a3b8; text-align: center; line-height: 1.3; }

/* 密码修改表单 */
.pwd-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.settings-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 13px;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.settings-input:focus {
  border-color: #6366f1;
  background: #fff;
}
.pwd-msg {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}
.pwd-msg.success { background: #f0fdf4; color: #16a34a; }
.pwd-msg.error { background: #fff1f2; color: #dc2626; }
.pwd-submit-btn {
  padding: 11px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
}
.pwd-submit-btn:hover:not(:disabled) { opacity: 0.88; }
.pwd-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

</style>
