<template>
	<div :class="['app-layout', currentMode + '-mode']">
		<!-- 侧边栏组件 -->
		<WebChatSidebar
			:is-open="isSidebarOpen"
			:sessions="sessions"
			:current-session-id="currentSessionId"
			:user-name="auth.userName"
			:is-admin="auth.isAdmin"
			@close="isSidebarOpen = false"
			@new-chat="startNewChatWithClose"
			@switch-session="switchSessionWithClose"
			@delete-session="deleteSession"
			@show-settings="showSettings = true"
			@logout="handleLogout"
		/>

		<div class="chat-container">
			<!-- 顶部导航栏 -->
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
						<span class="app-version" :title="versionTooltip">{{ versionBadge }}</span>
					</div>
					<!-- 移动端情报开关 -->
					<button v-if="currentMode === 'coach' && currentScenario" 
						class="intel-toggle-mobile" 
						@click="isIntelOpen = !isIntelOpen"
						:class="{ active: isIntelOpen }">
						<IconZap size="18" /> 实战情报
					</button>
				</div>

				<!-- 模式切换组件 -->
				<WebChatModeSelector
					v-model="currentMode"
					:has-new-notice="hasNewNotice"
					@open-notices="openNotices"
					@open-tools="openToolsCenter"
					@update:model-value="switchMode"
				/>
			</nav>

			<div class="main-body-wrapper">
				<!-- 聊天主区域 -->
				<main class="chat-main" ref="chatMain">
					<!-- 欢迎屏 / 教练引导 -->
					<WebWelcomeScreen
						v-if="messages.length === 0"
						:mode="currentMode"
						:welcome-msg="personalizedWelcomeMsg"
						v-model:coach-sub-mode="coachSubMode"
						v-model:selected-region="selectedRegion"
						v-model:selected-scenario="selectedScenario"
						:coach-regions="coachRegions"
						:coach-scenarios="coachScenarios"
						:quiz-step="quizStep"
						:quiz-questions="quizQuestions"
						:current-quiz-idx="currentQuizIdx"
						:selected-option="selectedOption"
						:is-quiz-submitted="isQuizSubmitted"
						:quiz-stats="quizStats"
						@preset-msg="presetMsg"
						@start-quiz="startCoachQuizFlow"
						@restart-quiz="restartQuiz"
						@start-duel="startCoachDetailedSubject"
						@fetch-questions="fetchQuizQuestions"
						@select-option="selectQuizOption"
						@next-question="nextQuizQuestion"
					/>

					<!-- 消息列表 -->
					<div v-else class="message-list">
						<WebChatMessageItem
							v-for="msg in messages"
							:key="msg.id"
							:message="msg"
							:ai-avatar="XIAOYI_AVATAR_IMG"
							@preview-image="openImageModal"
						/>
						<div ref="messagesEnd"></div>
					</div>
				</main>

				<!-- 实战情报面板 (教练模式) -->
				<div v-if="currentMode === 'coach' && currentScenario" 
					:class="['intel-overlay', { show: isIntelOpen }]" 
					@click="isIntelOpen = false"></div>
				<WebCombatIntelPanel
					v-if="currentMode === 'coach' && currentScenario"
					:show-mobile="isIntelOpen"
					:current-scenario="currentScenario"
					:success-criteria="formatSuccessCriteria(currentScenario.success_criteria)"
					@close="isIntelOpen = false"
					@quit="requestCoachEvaluation"
				/>
			</div>

			<!-- 输入区域 -->
			<WebChatMessageInput
				v-if="coachSubMode !== 'quiz'"
				v-model:input-msg="inputMsg"
				:selected-image="selectedImage"
				:is-generating="isGenerating"
				:placeholder="inputPlaceholder"
				@send="handleSendMessage"
				@stop="stopGeneration"
				@trigger-upload="triggerImageUpload"
				@remove-image="removeImage"
				@handle-paste="handlePaste"
				@handle-drop="handleDrop"
				ref="messageInputRef"
			/>
			<!-- 选图用隐藏 input -->
			<input type="file" ref="fileInput" style="display:none" @change="onImageSelected" accept="image/jpeg,image/png,image/webp" />
		</div>

		<!-- 通知遮罩层 -->
		<WebNoticeOverlay
			v-model:show="showNotices"
			v-model:notice-tab="noticeTab"
			:loading="loadingNotices"
			:notices="formatDisplayNotices"
		/>

		<!-- 设置遮罩层 -->
		<WebSettingsOverlay
			v-model:show="showSettings"
			v-model:output-length="outputLength"
			:pwd-form="pwdForm"
			:pwd-msg="pwdMsg"
			:pwd-loading="pwdLoading"
			@update:pwd-form="({field, value}) => pwdForm[field] = value"
			@submit-pwd="submitChangePassword"
			@update:output-length="setOutputLength"
		/>

		<!-- 图片放大模态框 -->
		<Teleport to="body">
			<div v-if="zoomedImage" class="image-modal-backdrop" @click="zoomedImage = null">
				<img :src="zoomedImage" class="zoomed-image" />
				<button class="modal-close-btn"><IconX size="32" /></button>
			</div>
		</Teleport>
	</div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { createSseEventParser } from '@/utils/sse-parser'
import { getLatestNoticeId, hasUnreadNotices } from '@/utils/notice-badge'
import { 
	Menu as IconMenu, X as IconX, Zap as IconZap
} from 'lucide-vue-next'

// 组件导入
import WebChatSidebar from './chat/components/WebChatSidebar.vue'
import WebChatModeSelector from './chat/components/WebChatModeSelector.vue'
import WebChatMessageItem from './chat/components/WebChatMessageItem.vue'
import WebChatMessageInput from './chat/components/WebChatMessageInput.vue'
import WebCombatIntelPanel from './chat/components/WebCombatIntelPanel.vue'
import WebNoticeOverlay from './chat/components/WebNoticeOverlay.vue'
import WebSettingsOverlay from './chat/components/WebSettingsOverlay.vue'
import WebWelcomeScreen from './chat/components/WebWelcomeScreen.vue'

// 基础常量
const auth = useAuthStore()
const router = useRouter()
const XIAOYI_AVATAR_IMG = '/xiaoyi-avatar.png'
const OUTPUT_LENGTH_KEY = 'zyd_output_length'
const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'
const NOTICE_SEEN_STORAGE_KEY = 'last_read_notice_id'
const NOTICE_CHECK_INTERVAL_MS = 60 * 1000
const APP_VERSION = __APP_VERSION__
const APP_BUILD_TIME = __APP_BUILD_TIME__

// 配置信息
const coachRegions = [
	{ name: '美国', emoji: '🇺🇸', desc: '偏远、计费重、FBA时效与附加费。' },
	{ name: '欧洲', emoji: '🇪🇺', desc: 'VAT、清关、派送签收与异常协同。' },
	{ name: '一件代发', emoji: '📦', desc: '单件履约、仓配联动、售后纠纷处理。' }
]
const coachScenarios = [
	{ name: '询价', emoji: '💵', desc: '围绕价格、时效、规则解释和成交推进。' },
	{ name: '纠纷', emoji: '🛡', desc: '围绕异常、理赔、投诉和补救方案协商。' }
]

// 响应式状态 - 基础
const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const isSidebarOpen = ref(false)
const currentMode = ref(localStorage.getItem(LAST_CHAT_MODE_KEY) || 'general')
const sessions = ref([])
const currentSessionId = ref(null)
const abortController = ref(null)

// 响应式状态 - 图片
const selectedImage = ref(null)
const selectedImageUploadId = ref('')
const isImageUploading = ref(false)
const zoomedImage = ref(null)

// 响应式状态 - 教练模式
const coachSubMode = ref('entrance')
const selectedRegion = ref(null)
const selectedScenario = ref(null)
const currentScenario = ref(null)
const isIntelOpen = ref(false)
const coachCases = ref([])

// 响应式状态 - 出题(Quiz)
const quizStep = ref('count_selection')
const quizQuestions = ref([])
const currentQuizIdx = ref(0)
const selectedOption = ref('')
const isQuizSubmitted = ref(false)
const quizStats = ref({ correct: 0, total: 0 })

// 响应式状态 - 通知与设置
const showNotices = ref(false)
const noticeTab = ref('current')
const allNotices = ref({ current: [], history: [] })
const loadingNotices = ref(false)
const hasNewNotice = ref(false)
const showSettings = ref(false)
const outputLength = ref(localStorage.getItem(OUTPUT_LENGTH_KEY) || 'medium')
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdMsg = ref(null)
const pwdLoading = ref(false)
let noticePollTimer = null

const markCurrentNoticesSeen = (currentNotices) => {
	const latestNoticeId = getLatestNoticeId(currentNotices)
	if (latestNoticeId === null) {
		return
	}
	localStorage.setItem(NOTICE_SEEN_STORAGE_KEY, String(latestNoticeId))
	hasNewNotice.value = false
}

const refreshNoticeBadgeOnVisibility = () => {
	if (typeof document === 'undefined' || document.visibilityState === 'visible') {
		refreshNoticeBadge()
	}
}

// DOM 引用
const chatMain = ref(null)
const messagesEnd = ref(null)
const fileInput = ref(null)
const messageInputRef = ref(null)

// 计算属性
const inputPlaceholder = computed(() => currentMode.value === 'coach' ? '与客户对话中...' : '发送消息、粘贴或拖入图片...')
const formatDisplayNotices = computed(() => noticeTab.value === 'history' ? allNotices.value.history : allNotices.value.current)
const versionBadge = computed(() => `v.${APP_VERSION}`)
const versionTooltip = computed(() => {
	const date = new Date(APP_BUILD_TIME)
	const buildTimeText = Number.isNaN(date.getTime())
		? APP_BUILD_TIME
		: date.toLocaleString('zh-CN', { hour12: false })
	return `当前版本 ${APP_VERSION} | 构建时间 ${buildTimeText}`
})
const personalizedWelcomeMsg = computed(() => {
	const displayName = String(auth.userName || '').trim()
	return `${displayName || '您'}您好！我是小易，有什么可以帮你的吗？`
})

// 方法 - 核心
const switchMode = (mode) => {
	if (currentMode.value === mode) return
	currentMode.value = mode
	localStorage.setItem(LAST_CHAT_MODE_KEY, mode)
	resetCoachState()
	loadSessionsByMode(mode)
	if (sessions.value.length === 0) startNewChat()
	else switchSession(sessions.value[0].id)
}

const loadSessionsByMode = (mode) => {
	const raw = localStorage.getItem(`zyd_sessions_${mode}`)
	sessions.value = raw ? JSON.parse(raw) : []
}

const startNewChat = () => {
	const newId = Date.now().toString()
	const newSession = { id: newId, title: '新对话', messages: [] }
	sessions.value = [newSession, ...sessions.value].slice(0, 50)
	currentSessionId.value = newId
	messages.value = []
	saveSessions()
}

const startNewChatWithClose = () => { startNewChat(); isSidebarOpen.value = false; }

const switchSession = (id) => {
	const s = sessions.value.find(item => item.id === id)
	if (!s) return
	currentSessionId.value = id
	messages.value = [...(s.messages || [])]
	scrollToBottom()
}

const switchSessionWithClose = (id) => { switchSession(id); isSidebarOpen.value = false; }

const deleteSession = (id) => {
	sessions.value = sessions.value.filter(s => s.id !== id)
	if (currentSessionId.value === id) {
		if (sessions.value[0]) switchSession(sessions.value[0].id)
		else startNewChat()
	}
	saveSessions()
}

const saveSessions = () => {
    if (!currentSessionId.value) return
    const s = sessions.value.find(item => item.id === currentSessionId.value)
    if (!s) return
    s.messages = [...messages.value]
    // 自动更新标题
    const firstUserMsg = s.messages.find(m => m.role === 'user' && m.content)
    if (firstUserMsg) {
        const titleText = firstUserMsg.content.trim().slice(0, 20)
        s.title = titleText + (firstUserMsg.content.length > 20 ? '...' : '')
    }
    localStorage.setItem(`zyd_sessions_${currentMode.value}`, JSON.stringify(sessions.value))
}

const getMessageById = (id) => messages.value.find((message) => message.id === id)

const handleSendMessage = async () => {
	const content = inputMsg.value.trim()
	if (!content && !selectedImage.value) return
	if (isGenerating.value) return

	const userMsgId = Date.now().toString()
	messages.value.push({ id: userMsgId, role: 'user', content, image: selectedImage.value })
	inputMsg.value = ''; selectedImage.value = null; scrollToBottom()

	isGenerating.value = true
	abortController.value = new AbortController()

	const aiMsgId = 'ai-' + Date.now()
	const aiMsg = { id: aiMsgId, role: 'assistant', content: '', isTyping: true }
	messages.value.push(aiMsg)
	scrollToBottom()

	try {
        // 构建提示偏好
        let finalContent = content
        if (outputLength.value === 'short') finalContent = `[输出偏好:极致精简] ${content}`
        else if (outputLength.value === 'long') finalContent = `[输出偏好:详尽展开] ${content}`

		const response = await fetch('/api/chat/stream', {
			method: 'POST',
			headers: { 
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${auth.token}`
			},
			body: JSON.stringify({
				message: finalContent,
				mode: currentMode.value,
				image_base64: selectedImage.value?.split(',')[1],
				image_upload_id: selectedImageUploadId.value,
				history: messages.value.slice(0, -2).map(m => ({ role: m.role, content: m.content }))
			}),
			signal: abortController.value.signal
		})
		if (!response.ok) {
			throw new Error(`HTTP ${response.status}`)
		}
		if (!response.body) {
			throw new Error('No response body')
		}

		const reader = response.body.getReader()
		const decoder = new TextDecoder()
		const sseParser = createSseEventParser()
		
		while (true) {
			const { done, value } = await reader.read()
			if (done) break
			const chunk = decoder.decode(value, { stream: true })
			const parsed = sseParser.push(chunk)
			const liveAiMsg = getMessageById(aiMsgId)
			if (!liveAiMsg) continue
			for (const event of parsed.events) {
				if (event.type === 'content' && event.content) {
					liveAiMsg.content += event.content
				}
			}
			if (parsed.plainText) {
				liveAiMsg.content += parsed.plainText
			}
			scrollToBottom()
		}
		const tail = sseParser.flush()
		if (tail.plainText) {
			const liveAiMsg = getMessageById(aiMsgId)
			if (liveAiMsg) {
				liveAiMsg.content += tail.plainText
			}
			scrollToBottom()
		}
	} catch (error) {
		if (error.name !== 'AbortError') {
			const liveAiMsg = getMessageById(aiMsgId)
			if (liveAiMsg) {
				liveAiMsg.content += `\n\n[出错了：${error.message}]`
			}
		}
	} finally {
		const liveAiMsg = getMessageById(aiMsgId)
		if (liveAiMsg) {
			liveAiMsg.isTyping = false
		}
		isGenerating.value = false; abortController.value = null
		saveSessions()
	}
}

const stopGeneration = () => { if (abortController.value) abortController.value.abort(); }

// 方法 - 教练逻辑
const startCoachQuizFlow = () => { coachSubMode.value = 'quiz'; quizStep.value = 'count_selection' }
const fetchQuizQuestions = async (count) => {
	try {
		const res = await axios.get(`/api/coach-quiz/session?count=${count}`)
		quizQuestions.value = res.data.questions.map(q => ({
			...q, options: q.options || []
		}))
		quizStep.value = 'answering'
		currentQuizIdx.value = 0
		quizStats.value = { correct: 0, total: count }
        isQuizSubmitted.value = false
        selectedOption.value = ''
	} catch (e) { alert('获取题目失败') }
}

const selectQuizOption = (key) => {
	if (isQuizSubmitted.value) return
	selectedOption.value = key; isQuizSubmitted.value = true
	if (key === quizQuestions.value[currentQuizIdx.value].answer) quizStats.value.correct++
}

const nextQuizQuestion = () => {
	if (currentQuizIdx.value === quizQuestions.value.length - 1) quizStep.value = 'result'
	else { currentQuizIdx.value++; selectedOption.value = ''; isQuizSubmitted.value = false; }
}

const restartQuiz = () => { quizStep.value = 'count_selection'; }

const getCaseRoute = (item) => {
	const text = `${item?.category || ''} ${item?.name || ''} ${item?.source || ''} ${item?.background || ''}`.toLowerCase()
	if (text.includes('一件代发') || text.includes('代发') || text.includes('dropship')) return '一件代发'
	if (text.includes('欧洲') || text.includes('欧线')) return '欧洲'
	if (text.includes('美国') || text.includes('美线')) return '美国'
	return '未知'
}

const getCaseScenario = (item) => {
	const text = `${item?.category || ''} ${item?.name || ''} ${item?.source || ''} ${item?.background || ''}`.toLowerCase()
	if (text.includes('异常纠纷处理') || text.includes('纠纷') || text.includes('投诉') || text.includes('理赔') || text.includes('索赔') || text.includes('赔偿') || text.includes('破损')) {
		return '纠纷'
	}
	if (text.includes('报价拉锯战') || text.includes('业务挖坑排雷') || text.includes('逼单客情维护') || text.includes('询价') || text.includes('报价') || text.includes('价格')) {
		return '询价'
	}
	return '询价'
}

const pickRandom = (items) => {
	if (!Array.isArray(items) || items.length === 0) return null
	return items[Math.floor(Math.random() * items.length)]
}

const startCoachDetailedSubject = (sceneName) => {
	if (!selectedRegion.value || !sceneName) return
	selectedScenario.value = sceneName

	const matchedByRouteAndScene = coachCases.value.filter(
		(item) => getCaseRoute(item) === selectedRegion.value && getCaseScenario(item) === sceneName
	)
	const matchedBySceneOnly = coachCases.value.filter(
		(item) => getCaseScenario(item) === sceneName
	)

	const randomCase = pickRandom(matchedByRouteAndScene) || pickRandom(matchedBySceneOnly)
	if (randomCase) {
		currentScenario.value = {
			...randomCase,
			persona: randomCase.persona || `${selectedRegion.value} · ${sceneName} 对练客户`,
		}
	} else {
		currentScenario.value = {
			name: `${selectedRegion.value} · ${sceneName} 通用实战`,
			persona: `${selectedRegion.value} · ${sceneName} 对练客户`,
			background: '当前案例库暂无完全匹配剧本，先进入通用对练，你可以继续上传该线路案例增强命中。',
			success_criteria: [
				'先问全关键信息，再给结论。',
				'不要硬刚，先稳住情绪再推进方案。',
				'所有关键数字、费用、时效都给到可执行口径。',
			],
		}
	}

	inputMsg.value = `我要挑战【${currentScenario.value.name}】场景`
	handleSendMessage()
	isIntelOpen.value = true
}

const requestCoachEvaluation = () => {
    inputMsg.value = '【结束对练】请现在切换为“资深销售总监/金牌导师”的人设，基于刚才的全部聊天记录输出结构化点评报告。'
    handleSendMessage()
    // 关闭情报面板，并清空当前场景状态以防逻辑干扰
    isIntelOpen.value = false
    currentScenario.value = null
}

const resetCoachState = () => {
	coachSubMode.value = 'entrance'; selectedRegion.value = null; selectedScenario.value = null
	currentScenario.value = null; quizStep.value = 'count_selection'
}

// 图片辅助
const triggerImageUpload = () => fileInput.value?.click()
const onImageSelected = (e) => {
	const file = e.target.target?.files?.[0] || e.target.files?.[0]
	if (file) handleImageFile(file)
}
const handleImageFile = (file) => {
	const reader = new FileReader()
	reader.onload = (e) => { selectedImage.value = e.target.result }
	reader.readAsDataURL(file)
}
const removeImage = () => { selectedImage.value = null; selectedImageUploadId.value = ''; }
const openImageModal = (url) => zoomedImage.value = url
const handlePaste = (e) => {
	const item = e.clipboardData.items[0]
	if (item?.type.includes('image')) handleImageFile(item.getAsFile())
}
const handleDrop = (e) => {
	const file = e.dataTransfer.files[0]
	if (file?.type.includes('image')) handleImageFile(file)
}

// 系统逻辑
const refreshNoticeBadge = async () => {
	try {
		const response = await axios.get('/api/notices/current')
		const currentNotices = Array.isArray(response.data) ? response.data : []
		allNotices.value.current = currentNotices
		const seenNoticeId = localStorage.getItem(NOTICE_SEEN_STORAGE_KEY)
		hasNewNotice.value = hasUnreadNotices(currentNotices, seenNoticeId)
	} catch (error) {
		console.error('Failed to refresh notice badge:', error)
	}
}

const openNotices = async () => {
	showNotices.value = true; loadingNotices.value = true
	try {
		const [cur, hist] = await Promise.all([
			axios.get('/api/notices/current'),
			axios.get('/api/notices/history')
		])
		allNotices.value = { current: cur.data, history: hist.data }
		markCurrentNoticesSeen(cur.data)
	} finally { loadingNotices.value = false }
}
const openToolsCenter = () => { router.push('/tools') }

const setOutputLength = (val) => {
	outputLength.value = val; localStorage.setItem(OUTPUT_LENGTH_KEY, val)
}

const logout = () => { auth.logout(); router.push('/login') }
const handleLogout = () => logout()

const submitChangePassword = async () => {
	const { oldPwd, newPwd, confirmPwd } = pwdForm.value
	if (newPwd !== confirmPwd) { pwdMsg.value = { type: 'error', text: '两次输入不一致' }; return }
	pwdLoading.value = true
	try {
		await axios.post('/api/auth/change-password', { old_password: oldPwd, new_password: newPwd })
		pwdMsg.value = { type: 'success', text: '密码修改成功' }
		pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
	} catch (err) {
		pwdMsg.value = { type: 'error', text: err.response?.data?.detail || '修改失败' }
	} finally { pwdLoading.value = false }
}

// 自动滚动辅助
const scrollToBottom = () => {
	nextTick(() => {
		if (chatMain.value) chatMain.value.scrollTop = chatMain.value.scrollHeight
	})
}
const presetMsg = (m) => { inputMsg.value = m; handleSendMessage() }
const formatSuccessCriteria = (c) => Array.isArray(c) ? c : (typeof c === 'string' ? c.split('\n').filter(Boolean) : [])

// 生命周期
onMounted(() => {
	if (!auth.isAuthenticated) { router.push('/login'); return }
	loadSessionsByMode(currentMode.value)
	if (sessions.value.length === 0) startNewChat()
	else switchSession(sessions.value[0].id)
	refreshNoticeBadge()
	noticePollTimer = window.setInterval(refreshNoticeBadge, NOTICE_CHECK_INTERVAL_MS)
	window.addEventListener('focus', refreshNoticeBadgeOnVisibility)
	document.addEventListener('visibilitychange', refreshNoticeBadgeOnVisibility)

	axios.get('/api/upload/coach-cases').then(r => coachCases.value = r.data || [])
})

onUnmounted(() => {
	if (noticePollTimer) {
		window.clearInterval(noticePollTimer)
		noticePollTimer = null
	}
	window.removeEventListener('focus', refreshNoticeBadgeOnVisibility)
	document.removeEventListener('visibilitychange', refreshNoticeBadgeOnVisibility)
})
</script>

<style>
/* 核心布局，全局应用 */
.app-layout {
	display: flex;
	height: 100vh;
	height: 100dvh;
	min-height: 100vh;
	min-height: 100dvh;
	background: #ffffff;
	overflow: hidden;
}

.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-width: 0;
}

.chat-nav {
	height: 64px;
	padding: 0 24px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: rgba(255, 255, 255, 0.82);
	backdrop-filter: blur(20px);
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
	z-index: 80;
}

.nav-left { display: flex; align-items: center; gap: 16px; }
.brand { display: flex; align-items: center; gap: 12px; }
.company-logo { height: 32px; width: auto; }
.brand-divider { color: #e2e8f0; font-size: 20px; }
.gradient-text { font-weight: 800; font-size: 18px; 
    background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.app-version {
	font-size: 12px;
	font-weight: 600;
	color: #64748b;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 999px;
	padding: 2px 8px;
	line-height: 1.4;
	white-space: nowrap;
}

.main-body-wrapper {
	flex: 1;
	display: flex;
	overflow: hidden;
	position: relative;
}

.chat-main {
	flex: 1;
	overflow-y: auto;
	padding: 24px 0;
	scroll-behavior: smooth;
}

.message-list {
	max-width: 900px;
	margin: 0 auto;
	padding: 0 40px;
}

/* 导航相关图标按钮移动端适配 */
.menu-toggle {
	display: none;
	background: transparent; border: none; cursor: pointer; color: #64748b;
}

@media screen and (max-width: 768px) {
	.menu-toggle { display: block; }
    .message-list { padding: 0 16px; }
    .chat-nav { 
        height: auto; 
        padding: 16px; 
        flex-direction: column; 
        align-items: stretch; 
        gap: 16px;
    }
    .nav-left { gap: 12px; justify-content: flex-start; }
    .company-logo { height: 26px; }
    .brand-divider { display: none; }
    .gradient-text { font-size: 16px; white-space: nowrap; }
    .app-version { font-size: 11px; padding: 2px 6px; }
    .intel-toggle-mobile { padding: 4px 8px; font-size: 13px; white-space: nowrap; }
}

/* 情报遮罩层 - 移动端专属 */
.intel-overlay {
	position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 45; opacity: 0; pointer-events: none; transition: 0.3s;
}
.intel-overlay.show { opacity: 1; pointer-events: auto; }

/* 图片弹窗 */
.image-modal-backdrop {
	position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 2000; display: flex; align-items: center; justify-content: center; cursor: zoom-out;
}
.zoomed-image { max-width: 90vw; max-height: 90vh; border-radius: 8px; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
.modal-close-btn { position: absolute; top: 24px; right: 24px; background: transparent; border: none; color: white; cursor: pointer; }

/* 模式主题变量 */
.general-mode { --theme-color: #2563eb; }
.coach-mode { --theme-color: #059669; }
.expert-mode { --theme-color: #7c3aed; }
</style>
