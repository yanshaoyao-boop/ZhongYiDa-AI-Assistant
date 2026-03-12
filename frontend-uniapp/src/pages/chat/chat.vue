<template>
	<view :class="['app-layout', `${currentMode}-mode`]">
		<view v-if="isSidebarOpen" class="sidebar-overlay show" @tap="isSidebarOpen = false"></view>

		<view :class="['sidebar', 'glass-panel', { show: isSidebarOpen }]">
			<view class="sidebar-header">
				<button class="new-chat-btn" @tap="startNewChatWithClose">
					<text class="new-chat-plus">+</text>
					<text>新对话</text>
				</button>
			</view>

			<scroll-view scroll-y class="session-list">
				<view
					v-for="session in sessions"
					:key="session.id"
					:class="['session-item', 'session-item-shell', { active: session.id === currentSessionId }]"
					@tap="switchSessionWithClose(session.id)"
				>
					<text class="session-title">{{ session.title || '新对话' }}</text>
					<button class="delete-btn" @tap.stop="deleteSession(session.id)">×</button>
				</view>
			</scroll-view>

			<view class="sidebar-footer">
				<button v-if="auth.isAdmin" class="sidebar-admin-btn" @tap="goToAdmin">管理后台</button>

				<view class="sidebar-user-info sidebar-account-card">
					<view class="user-avatar-sidebar">{{ userInitial }}</view>
					<view class="user-details">
						<text class="user-name-sidebar">{{ auth.userName }}</text>
						<button class="logout-link-sidebar" @tap="handleLogout">退出登录</button>
					</view>
				</view>
			</view>
		</view>

		<view class="chat-container">
			<view class="chat-nav nav-shell glass-panel">
				<view class="nav-left">
					<button class="nav-btn-hamburg" @tap="toggleSidebar">
						<text class="nav-btn-text">{{ isSidebarOpen ? '×' : '≡' }}</text>
					</button>
				</view>

				<view class="mode-selector mode-selector-pill">
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'general', 'tab-active-general': currentMode === 'general' }]"
						@tap="switchMode('general')"
					>
						<text class="tab-text">全能助手</text>
					</view>
					<view class="tab-divider"></view>
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'coach', 'tab-active-coach': currentMode === 'coach' }]"
						@tap="switchMode('coach')"
					>
						<text class="tab-text">知识教练</text>
					</view>
					<view class="tab-divider"></view>
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'expert', 'tab-active-expert': currentMode === 'expert' }]"
						@tap="switchMode('expert')"
					>
						<text class="tab-text">专家指导</text>
					</view>
				</view>
				<view class="nav-right-spacer"></view>
			</view>

			<view class="main-body-wrapper">
				<scroll-view
					scroll-y
					class="chat-main"
					:scroll-top="scrollTop"
					:scroll-into-view="scrollIntoViewTarget"
					scroll-with-animation
				>
					<view v-if="messages.length === 0" class="welcome-screen">
						<view class="welcome-stage">
						<view v-if="currentMode === 'general'" class="zen-welcome-stage">
							<view class="welcome-content welcome-panel welcome-centered">
								<view class="zen-avatar-breathe">
									<image src="/static/xiaoyi_character.png" mode="aspectFit" class="zen-avatar-img" />
								</view>
								<text class="zen-title">您好，我是小易</text>
								<text class="zen-subtitle">{{ welcomeMsg }}</text>

								<view class="suggestion-chips suggestion-chip-shell">
									<view class="zen-suggestion-grid">
										<view class="zen-card" @tap="presetMsg('我能帮你做哪些事情')">
											<view class="zen-card-content">
												<text class="zen-card-title">查看核心能力</text>
												<text class="zen-card-desc">了解我能帮您完成的物流与办公任务</text>
											</view>
										</view>
										<view class="zen-card" @tap="presetMsg('如何正确使用小易')">
											<view class="zen-card-content">
												<text class="zen-card-title">获取使用指南</text>
												<text class="zen-card-desc">掌握与小易合作的最佳提示词技巧</text>
											</view>
										</view>
									</view>
								</view>
							</view>
						</view>

						<view v-else-if="currentMode === 'expert'" class="zen-welcome-stage expert-stage welcome-centered">
							<view class="zen-expert-icon">
								<text class="expert-emoji">💡</text>
							</view>
							<text class="zen-title zen-title-expert">专家指导</text>
							<text class="zen-subtitle">请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。</text>

							<view class="zen-suggestion-grid">
								<view class="zen-card" @tap="presetMsg('我有一个关于供应链优化的复杂问题')">
									<view class="zen-card-content">
										<text class="zen-card-title">供应链优化分析</text>
										<text class="zen-card-desc">我会先帮你拆问题，再给出结构化建议。</text>
									</view>
								</view>
							</view>
						</view>

						<view v-else class="zen-welcome-stage coach-stage welcome-centered">
							<text class="zen-title zen-title-coach">知识教练</text>
							<text class="zen-subtitle">场景化陪练，帮助你把经验真正练到手。</text>

							<view class="coach-selection-shell">
								<view class="zen-level-up-container">
									<view class="zen-level-header">
										<text class="coach-step-pill">{{ currentCoachStep }}</text>
										<text class="zen-level-desc" v-if="!selectedRegion">先选择实战航线</text>
										<text class="zen-level-desc" v-else-if="!selectedPersona">再选择客户画像</text>
										<text class="zen-level-desc" v-else>最后选择训练科目</text>
									</view>

									<view v-if="currentCoachSelections.length" class="coach-selection-summary">
										<view class="zen-breadcrumbs">
											<view class="zen-breadcrumb coach-selection-chip" @tap="selectedRegion = null; selectedPersona = null">
												{{ selectedRegion }}
												<text v-if="selectedPersona" class="arrow">→</text>
											</view>
											<view v-if="selectedPersona" class="zen-breadcrumb coach-selection-chip" @tap="selectedPersona = null">
												{{ selectedPersona }}
											</view>
										</view>
									</view>

									<view v-if="!selectedRegion" class="zen-level-grid">
										<view v-for="reg in coachRegions" :key="reg.name" class="zen-level-card" @tap="selectedRegion = reg.name">
											<view class="zen-card-huge-icon">{{ reg.short }}</view>
											<view class="zen-level-info">
												<text class="zen-level-title">{{ reg.name }}</text>
												<text class="zen-level-desc-mini">{{ reg.desc }}</text>
											</view>
										</view>
									</view>

									<view v-else-if="!selectedPersona" class="zen-level-grid slide-in">
										<view v-for="persona in coachPersonas" :key="persona.name" class="zen-level-card" @tap="selectedPersona = persona.name">
											<view class="zen-card-huge-emoji">{{ persona.emoji }}</view>
											<view class="zen-level-info">
												<text class="zen-level-title">{{ persona.name }}</text>
												<text class="zen-level-desc-mini">{{ persona.desc }}</text>
											</view>
										</view>
									</view>

									<view v-else class="zen-level-grid slide-in">
										<view v-for="subject in coachSubjects" :key="subject.name" class="zen-level-card" @tap="startRandomCoachDetailed(subject.name)">
											<view class="zen-card-huge-emoji">{{ subject.emoji }}</view>
											<view class="zen-level-info">
												<text class="zen-level-title">{{ subject.name }}</text>
												<text class="zen-level-desc-mini">{{ subject.desc }}</text>
											</view>
										</view>
									</view>
								</view>
							</view>
						</view>
						</view>
					</view>

					<view class="message-list">
						<view v-for="msg in messages" :key="msg.id" class="message-wrapper" :class="msg.role">
							<view class="avatar">
								<image v-if="msg.role === 'assistant'" src="/static/xiaoyi_avatar.png" class="xiaoyi-avatar" />
								<view v-else class="user-avatar">{{ userInitial }}</view>
							</view>

							<view class="message-body message-content" :class="{ 'is-typing': msg.isTyping }">
								<image
									v-if="msg.image"
									:src="msg.image"
									mode="widthFix"
									class="chat-message-image"
									@tap="previewImage(msg.image)"
								/>
								<rich-text class="markdown-body" :nodes="renderMarkdown(msg.content)"></rich-text>
								<text v-if="msg.isTyping" class="cursor-blink"></text>
							</view>
						</view>

						<view id="chat-bottom-anchor" class="chat-bottom-anchor"></view>
						<view class="message-tail-spacer"></view>
					</view>
				</scroll-view>

				<view :class="['combat-intel-panel', 'combat-intel-shell', 'glass-panel', { show: isIntelOpen }]">
					<view class="panel-header">
						<text>实战情报中心</text>
						<text class="panel-close" @tap="isIntelOpen = false">×</text>
					</view>
					<scroll-view scroll-y class="panel-content">
						<view class="intel-section">
							<text class="intel-label">当前场景</text>
							<text class="intel-text">{{ currentScenario ? currentScenario.name : '未开始' }}</text>
						</view>
						<view class="intel-section intel-section-highlight">
							<text class="intel-label">客户画像</text>
							<text class="intel-text">{{ selectedPersona || '待选择' }}</text>
						</view>
						<view class="intel-section">
							<text class="intel-label">过关要点</text>
							<view v-if="currentScenario && formatSuccessCriteria(currentScenario.success_criteria).length">
								<text
									v-for="(item, index) in formatSuccessCriteria(currentScenario.success_criteria)"
									:key="`${currentScenario.name}-${index}`"
									class="intel-text intel-text-block"
								>
									{{ index + 1 }}. {{ item }}
								</text>
							</view>
							<text v-else class="intel-text">先进入一个教练场景，情报会自动出现在这里。</text>
						</view>
						<button class="quit-combat-btn" @tap="requestCoachEvaluation">结束对练并点评</button>
					</scroll-view>
				</view>
			</view>

			<view class="zen-footer-wrapper chat-footer">
				<view class="input-shell input-container" :class="{ 'has-image': selectedImage, 'is-focused': isInputFocused }">
				<view class="zen-floating-pill" :class="{ 'has-image': selectedImage, 'is-focused': isInputFocused }">
					<view v-if="selectedImage" class="zen-image-preview-area">
						<view class="image-preview-frame">
							<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="previewImage(selectedImage)" />
						</view>
						<view class="image-preview-meta">
							<text class="image-preview-chip">已附图</text>
						</view>
						<view class="zen-remove-image-btn" @tap="removeImage">×</view>
					</view>

					<view class="zen-input-row">
						<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="triggerImageUpload">
							<!-- color="selectedImage ? '#2563eb' : '#64748b'" -->
							<text class="upload-pic-mark">＋</text>
						</view>

						<textarea
							v-model="inputMsg"
							auto-height
							class="zen-input-box"
							:cursor-spacing="24"
							:show-confirm-bar="false"
							confirm-type="send"
							:placeholder="selectedImage ? '补充图片说明，或直接发送...' : '发送消息、粘贴或拖入图片...'"
							@confirm="sendMessage"
							@focus="isInputFocused = true"
							@blur="isInputFocused = false"
						></textarea>

						<view class="zen-send-area">
							<button v-if="!isGenerating" class="zen-send-btn" :class="{ active: inputMsg.trim() || selectedImage }" @tap="sendMessage">
								<text class="icon-send">↑</text>
							</button>
							<button v-else class="zen-send-btn stop" @tap="stopGeneration">
								<text class="icon-send">■</text>
							</button>
						</view>
					</view>
				</view>
				</view>

				<view v-if="selectedImage || isGenerating" class="composer-status-row">
					<text v-if="selectedImage" class="composer-status-chip image-ready">已附加图片，可直接发送或继续补充文字</text>
					<text v-if="isGenerating" class="composer-status-chip generating">正在生成回复，可点击停止按钮中断</text>
				</view>
			</view>
		</view>

		<view class="zen-bottom-nav">
			<view class="zen-nav-item" :class="{ active: currentTab === 'chat' }" @tap="switchTab('chat')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<text class="zen-nav-glyph">●</text>
					</view>
				</view>
				<text class="zen-nav-label">对话</text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'admin' }" @tap="switchTab('admin')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<text class="zen-nav-glyph admin">◉</text>
					</view>
				</view>
				<text class="zen-nav-label">管理</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { renderMarkdown } from '@/utils/markdown'
import { resolveApiUrl } from '@/utils/api'
import { buildImageDataUrl } from '@/utils/image-data-url'
import { validateMpImageSelection } from '@/utils/image-data-url'
import { uploadChatImage } from '@/utils/chat-image-upload'
import { captureClientEvent } from '@/utils/error-logger'
import { createMpStreamChatController } from '@/utils/mp-stream-chat'

const auth = useAuthStore()

const messages = ref([])
const inputMsg = ref('')
const isInputFocused = ref(false)
const isGenerating = ref(false)
const isSidebarOpen = ref(false)
const welcomeMsg = ref('您的全天候智能助手')
const currentMode = ref('general')
const sessions = ref([])
const currentSessionId = ref(null)
const selectedImage = ref(null)
const selectedImageUploadId = ref('')
const isImageUploading = ref(false)
const currentTab = ref('chat')
const scrollTop = ref(0)
const scrollIntoViewTarget = ref('')
const coachCases = ref([])
const currentScenario = ref(null)
const isIntelOpen = ref(false)
const selectedRegion = ref(null)
const selectedPersona = ref(null)

const POST_LOGIN_FRESH_CHAT_KEY = 'zyd_post_login_fresh_chat'
const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'

const coachRegions = [
	{ name: '美国线', short: 'US', desc: '重视海派、邮编偏远、计费重量规则。' },
	{ name: '欧洲线', short: 'EU', desc: '重视铁派、VAT 税号、清关和派送规则。' },
]

const coachPersonas = [
	{ name: '行业小白', emoji: '🙂', desc: '礼貌但不懂行，需要你用专业和耐心带着走。' },
	{ name: '江湖老手', emoji: '😏', desc: '话术老练、压价明显，更考验底盘和判断。' },
]

const coachSubjects = [
	{ name: '报价拉锯战', emoji: '💵', desc: '面对客户反复压价，如何守住利润空间。' },
	{ name: '异常纠纷处理', emoji: '🛡', desc: '处理查验、投诉、破损和延误等异常问题。' },
	{ name: '业务排雷', emoji: '🔎', desc: '识别隐藏风险、敏感货和信息不完整订单。' },
	{ name: '逼单与维护', emoji: '🤝', desc: '推进成交，同时维持客户信任与节奏。' },
]

const userInitial = computed(() => String(auth.userName || '易').trim().slice(0, 1).toUpperCase() || '易')

const currentBrandMode = computed(() => {
	const modeMeta = {
		general: { label: '全能助手' },
		coach: { label: '实战教练' },
		expert: { label: '专家指导' },
	}
	return modeMeta[currentMode.value] || modeMeta.general
})

const currentCoachSelections = computed(() => {
	return [selectedRegion.value, selectedPersona.value].filter(Boolean)
})

const currentCoachStep = computed(() => {
	if (!selectedRegion.value) return '第一步 · 选择实战航线'
	if (!selectedPersona.value) return '第二步 · 选择客户背景'
	return '第三步 · 选择练习科目'
})

const persistLastMode = (mode) => {
	try {
		uni.setStorageSync(LAST_CHAT_MODE_KEY, mode)
	} catch (error) {}
}

const getInitialChatMode = () => {
	try {
		return uni.getStorageSync(LAST_CHAT_MODE_KEY) || 'general'
	} catch (error) {
		return 'general'
	}
}

const formatSuccessCriteria = (criteria) => {
	if (Array.isArray(criteria)) return criteria
	if (typeof criteria === 'string') {
		return criteria.split('\n').map((item) => item.trim()).filter(Boolean)
	}
	return []
}

let requestTask = null
let scrollBottomTimer = null

const toggleSidebar = () => {
	isSidebarOpen.value = !isSidebarOpen.value
}

const clearSelectedImage = () => {
	selectedImage.value = null
	selectedImageUploadId.value = ''
	isImageUploading.value = false
}

const switchTab = (tab) => {
	currentTab.value = tab
	if (tab === 'admin') {
		isSidebarOpen.value = false
		uni.navigateTo({ url: '/pages/admin/admin' })
	}
}

const switchSession = (sessionId) => {
	const targetSession = sessions.value.find((session) => session.id === sessionId)
	if (!targetSession) return
	currentSessionId.value = sessionId
	messages.value = [...(targetSession.messages || [])]
	clearSelectedImage()
	scrollToBottom()
}

const switchSessionWithClose = (sessionId) => {
	switchSession(sessionId)
	isSidebarOpen.value = false
}

const saveSessions = () => {
	if (!currentSessionId.value) return

	const targetSession = sessions.value.find((session) => session.id === currentSessionId.value)
	if (!targetSession) return

	targetSession.messages = [...messages.value]
	const firstUserMessage = targetSession.messages.find((item) => item.role === 'user' && item.content)
	if (firstUserMessage) {
		const compactTitle = firstUserMessage.content.trim()
		targetSession.title = compactTitle.length > 16 ? `${compactTitle.slice(0, 16)}...` : compactTitle
	}

	try {
		uni.setStorageSync(`zyd_sessions_${currentMode.value}`, JSON.stringify(sessions.value.slice(0, 20)))
	} catch (error) {}
}

const startNewChat = ({ forceCreate = false } = {}) => {
	if (!forceCreate && currentSessionId.value) {
		const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
		if (currentSession && (!currentSession.messages || currentSession.messages.length === 0)) {
			messages.value = []
			inputMsg.value = ''
			clearSelectedImage()
			return
		}
	}

	const newSessionId = `${Date.now()}`
	sessions.value = [
		{
			id: newSessionId,
			title: '新对话',
			messages: [],
		},
		...sessions.value,
	].slice(0, 20)

	currentSessionId.value = newSessionId
	messages.value = []
	inputMsg.value = ''
	clearSelectedImage()
	saveSessions()
}

const startNewChatWithClose = () => {
	startNewChat({ forceCreate: true })
	isSidebarOpen.value = false
}

const deleteSession = (sessionId) => {
	sessions.value = sessions.value.filter((item) => item.id !== sessionId)
	if (currentSessionId.value === sessionId) {
		if (sessions.value[0]) {
			switchSession(sessions.value[0].id)
		} else {
			startNewChat({ forceCreate: true })
		}
	}
	saveSessions()
}

const scrollToBottom = () => {
	nextTick(() => {
		scrollIntoViewTarget.value = ''
		scrollTop.value += 1000
		if (scrollBottomTimer) {
			clearTimeout(scrollBottomTimer)
		}
		scrollBottomTimer = setTimeout(() => {
			scrollIntoViewTarget.value = 'chat-bottom-anchor'
			scrollTop.value += 1
			scrollBottomTimer = null
		}, 80)
	})
}

const appendAssistantPlaceholder = () => {
	const aiMsgId = `ai-${Date.now()}`
	messages.value.push({
		id: aiMsgId,
		role: 'assistant',
		content: '',
		isTyping: true,
	})
	return aiMsgId
}

const sendMessage = async () => {
	const content = inputMsg.value.trim()
	if (!content && !selectedImage.value) return
	if (isGenerating.value) return

	if (selectedImage.value && isImageUploading.value) {
		uni.showToast({ title: '图片仍在上传中', icon: 'none' })
		return
	}

	const currentImageUploadId = selectedImageUploadId.value || null
	const currentImageBase64 = selectedImage.value && selectedImage.value.startsWith('data:')
		? selectedImage.value.split(',')[1]
		: null

	messages.value.push({
		id: `user-${Date.now()}`,
		role: 'user',
		content,
		image: selectedImage.value,
	})

	inputMsg.value = ''
	clearSelectedImage()
	isGenerating.value = true
	const aiMsgId = appendAssistantPlaceholder()
	scrollToBottom()

	const streamLogContext = {
		mode: currentMode.value,
		session_id: currentSessionId.value,
		has_image: Boolean(currentImageUploadId || currentImageBase64),
	}

	requestTask = createMpStreamChatController({
		buildRequestOptions: () => ({
			url: '/api/chat/stream',
			method: 'POST',
			header: {
				Authorization: `Bearer ${auth.token}`,
				'content-type': 'application/json',
			},
			data: {
				message: content,
				mode: currentMode.value,
				image_upload_id: currentImageUploadId,
				image_base64: currentImageBase64,
				history: messages.value.slice(0, -2).map((item) => ({
					role: item.role,
					content: item.content,
				})),
			},
		}),
		chunkTimeoutMs: 20000,
		retryLimit: 1,
		onRetry: ({ attempt, error }) => {
			captureClientEvent({
				level: 'warn',
				type: 'chat-stream-retry',
				message: error?.message || 'stream retry',
				context: { ...streamLogContext, attempt },
			})
		},
	})

	try {
		await requestTask.start({
			onStatus: (statusCode) => {
				if (statusCode >= 400) {
					const aiMsg = messages.value.find((item) => item.id === aiMsgId)
					if (aiMsg && !aiMsg.content) {
						aiMsg.content = `请求失败 (${statusCode})，请检查登录状态和后端服务。`
					}
				}
			},
			onText: (text) => {
				const aiMsg = messages.value.find((item) => item.id === aiMsgId)
				if (aiMsg && text) {
					aiMsg.content += text
					scrollToBottom()
				}
			},
		})
	} catch (error) {
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) {
			if (error?.code === 'STREAM_ABORTED') {
				aiMsg.content += '\n\n[已停止生成]'
			} else if (error?.code === 'STREAM_TIMEOUT') {
				captureClientEvent({
					level: 'warn',
					type: 'chat-stream-timeout',
					message: error?.message || 'stream timed out',
					context: streamLogContext,
				})
				aiMsg.content = aiMsg.content || '响应超时，请稍后重试。'
			} else if (!aiMsg.content) {
				aiMsg.content = `请求失败：${error?.message || '网络异常'}`
			}
		}

		captureClientEvent({
			level: 'error',
			type: 'chat-stream-failure',
			message: error?.message || 'chat stream failed',
			context: { ...streamLogContext, code: error?.code || 'REQUEST_FAILED' },
		})
	} finally {
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) aiMsg.isTyping = false
		isGenerating.value = false
		requestTask = null
		saveSessions()
	}
}

const stopGeneration = () => {
	if (requestTask) {
		requestTask.abort()
	}
	isGenerating.value = false
}

const loadSessionsByMode = (mode) => {
	try {
		const raw = uni.getStorageSync(`zyd_sessions_${mode}`)
		sessions.value = raw ? JSON.parse(raw) : []
	} catch (error) {
		sessions.value = []
	}
}

const switchMode = (mode) => {
	if (currentMode.value === mode) return
	currentMode.value = mode
	persistLastMode(mode)
	isSidebarOpen.value = false
	isIntelOpen.value = false
	selectedRegion.value = null
	selectedPersona.value = null
	if (mode !== 'coach') {
		currentScenario.value = null
	}
	loadSessionsByMode(mode)
	if (sessions.value.length === 0) {
		startNewChat({ forceCreate: true })
		return
	}
	switchSession(sessions.value[0].id)
}

const matchesCoachSubject = (category, subjectName) => {
	if (!category || !subjectName) return false
	const map = {
		'报价拉锯战': ['报价', '比价', '拉锯'],
		'异常纠纷处理': ['纠纷', '异常', '投诉', '处理'],
		业务排雷: ['排雷', '风险', '敏感', '异常'],
		'逼单与维护': ['逼单', '维护', '转化', '成交'],
	}
	if (category.includes(subjectName)) return true
	return (map[subjectName] || []).some((keyword) => category.includes(keyword))
}

const buildCoachFallbackScenario = (subjectName) => ({
	name: `${selectedRegion.value} · ${selectedPersona.value} · ${subjectName}`,
	success_criteria: [
		'识别客户真实诉求与隐藏顾虑',
		'给出专业且有利润空间的回应',
		'推动下一步成交或锁定关键参数',
	],
})

const startRandomCoachDetailed = (subjectName) => {
	if (!selectedRegion.value || !selectedPersona.value) return

	const matchingCases = coachCases.value.filter((item) => {
		const category = item.category || ''
		return category.includes(selectedRegion.value)
			&& category.includes(selectedPersona.value.replace('行业', ''))
			&& matchesCoachSubject(category, subjectName)
	})

	const randomCase = matchingCases[Math.floor(Math.random() * matchingCases.length)]
	const scenario = randomCase || buildCoachFallbackScenario(subjectName)
	if (randomCase) {
		currentScenario.value = randomCase
	} else {
		currentScenario.value = scenario
	}
	isIntelOpen.value = true
	inputMsg.value = `我要挑战【${scenario.name}】场景`
	sendMessage()
}

const presetMsg = (message) => {
	inputMsg.value = message
	sendMessage()
}

const handleLogout = () => {
	auth.logout()
	uni.reLaunch({ url: '/pages/login/login' })
}

const goToAdmin = () => {
	isSidebarOpen.value = false
	currentTab.value = 'admin'
	uni.navigateTo({ url: '/pages/admin/admin' })
}

const requestCoachEvaluation = () => {
	if (isGenerating.value || messages.value.length === 0) return
	inputMsg.value = [
		'请切换到资深销售总监 / 金牌导师的视角，基于刚才全部对话输出结构化点评。',
		'要求包含：',
		'1. 战力评分（百分制）',
		'2. 报价功底与关键参数完整度',
		'3. 盈利分析与风险提醒',
		'4. 更好的成交推进话术',
		'请用 Markdown 输出。',
	].join('\n')
	sendMessage()
}

const previewImage = (url) => {
	uni.previewImage({ urls: [url] })
}

const readImageAsDataUrl = async (filePath) => {
	if (!filePath || !uni.getFileSystemManager) return ''
	return await new Promise((resolve) => {
		try {
			uni.getFileSystemManager().readFile({
				filePath,
				encoding: 'base64',
				success: ({ data }) => resolve(buildImageDataUrl(filePath, data)),
				fail: () => resolve(''),
			})
		} catch (error) {
			resolve('')
		}
	})
}

const triggerImageUpload = () => {
	uni.chooseImage({
		count: 1,
		sizeType: ['compressed'],
		success: async (res) => {
			const filePath = res.tempFilePaths?.[0]
			const selectedTempFile = res.tempFiles?.[0] || {}
			if (!filePath) return

			const imageValidationError = validateMpImageSelection(selectedTempFile)
			if (imageValidationError) {
				uni.showToast({ title: imageValidationError, icon: 'none' })
				return
			}

			selectedImage.value = filePath
			selectedImageUploadId.value = ''
			isImageUploading.value = true

			try {
				const uploadPayload = await uploadChatImage({
					filePath,
					token: auth.token,
				})
				selectedImageUploadId.value = uploadPayload.image_upload_id
			} catch (error) {
				const dataUrl = await readImageAsDataUrl(filePath)
				if (dataUrl) {
					selectedImage.value = dataUrl
				} else {
					clearSelectedImage()
				}
				captureClientEvent({
					level: 'error',
					type: 'chat-image-upload-failure',
					message: error?.message || 'image upload failed',
					context: {
						mode: currentMode.value,
						session_id: currentSessionId.value,
					},
				})
			} finally {
				isImageUploading.value = false
			}
		},
	})
}

const removeImage = () => {
	clearSelectedImage()
}

const consumePostLoginFreshChatFlag = () => {
	try {
		const shouldCreateFreshChat = uni.getStorageSync(POST_LOGIN_FRESH_CHAT_KEY) === '1'
		if (shouldCreateFreshChat) {
			uni.removeStorageSync(POST_LOGIN_FRESH_CHAT_KEY)
		}
		return shouldCreateFreshChat
	} catch (error) {
		return false
	}
}

const ensureFreshEntrySession = () => {
	const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
	if (!currentSession || (currentSession.messages && currentSession.messages.length > 0)) {
		startNewChat({ forceCreate: true })
	}
	inputMsg.value = ''
	clearSelectedImage()
	scrollTop.value = 0
}

const fetchCoachCases = async () => {
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl('/api/upload/coach-cases'),
				method: 'GET',
				header: {
					Authorization: `Bearer ${auth.token}`,
				},
				success: resolve,
				fail: reject,
			})
		})

		if (response.statusCode >= 400) {
			throw new Error(`coach cases request failed: ${response.statusCode}`)
		}

		coachCases.value = Array.isArray(response.data)
			? response.data
			: Array.isArray(response.data?.cases)
				? response.data.cases
				: []
	} catch (error) {
		coachCases.value = []
	}
}

const fetchPublicSettings = async () => {
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl('/api/settings/public'),
				method: 'GET',
				success: resolve,
				fail: reject,
			})
		})

		if (response.statusCode >= 400) return
		if (response.data?.ai_welcome_message) {
			welcomeMsg.value = response.data.ai_welcome_message
		}
	} catch (error) {}
}

onMounted(() => {
	if (!auth.isAuthenticated) {
		uni.reLaunch({ url: '/pages/login/login' })
		return
	}

	const shouldFreshChat = consumePostLoginFreshChatFlag()
	const initialMode = shouldFreshChat ? 'general' : getInitialChatMode()
	currentMode.value = ''
	switchMode(initialMode)
	fetchCoachCases()
	fetchPublicSettings()
	if (shouldFreshChat) {
		ensureFreshEntrySession()
	}
})

onUnmounted(() => {
	if (scrollBottomTimer) {
		clearTimeout(scrollBottomTimer)
		scrollBottomTimer = null
	}
})

</script>

<style scoped>
.general-mode {
	--bg-primary: #f5f7fb;
	--bg-secondary: #ffffff;
	--accent-color: #f59e0b;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(226, 232, 240, 0.92);
}

.coach-mode {
	--bg-primary: #f1fbf6;
	--bg-secondary: #ffffff;
	--accent-color: #10b981;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(211, 233, 221, 0.92);
}

.expert-mode {
	--bg-primary: #f4f8ff;
	--bg-secondary: #ffffff;
	--accent-color: #3b82f6;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(219, 234, 254, 0.96);
}

.gradient-text {
	color: var(--accent-color);
}

.coach-mode .new-chat-btn,
.coach-mode .sidebar-admin-btn,
.coach-mode .user-avatar-sidebar {
	color: var(--accent-color);
}

.coach-mode .session-item.active {
	border-color: var(--accent-color);
}

.expert-mode .new-chat-btn,
.expert-mode .sidebar-admin-btn,
.expert-mode .user-avatar-sidebar {
	color: var(--accent-color);
}

.expert-mode .session-item.active {
	border-color: var(--accent-color);
}

.app-layout {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	width: 100%;
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, var(--bg-primary) 100%);
	overflow: hidden;
}

.glass-panel {
	background: rgba(255, 255, 255, 0.94);
	backdrop-filter: blur(24rpx);
	border: 1px solid rgba(255, 255, 255, 0.7);
}

.sidebar-overlay {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.26);
	backdrop-filter: blur(6rpx);
	z-index: 1000;
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.2s ease;
}

.sidebar-overlay.show {
	opacity: 1;
	pointer-events: auto;
}

.sidebar {
	position: fixed;
	top: 0;
	left: 0;
	bottom: 0;
	width: 560rpx;
	max-width: 82vw;
	padding: calc(108rpx + env(safe-area-inset-top)) 28rpx 28rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	transform: translateX(-100%);
	transition: transform 0.24s ease;
	z-index: 1001;
	box-shadow: 24rpx 0 54rpx rgba(15, 23, 42, 0.08);
}

.sidebar.show {
	transform: translateX(0);
}

.sidebar-header {
	display: flex;
}

.new-chat-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	width: 100%;
	height: 88rpx;
	border-radius: 28rpx;
	background: #0f172a;
	color: #ffffff;
	font-size: 28rpx;
	font-weight: 700;
}

.new-chat-plus {
	font-size: 36rpx;
	line-height: 1;
}

.new-chat-btn::after,
.delete-btn::after,
.sidebar-admin-btn::after,
.logout-link-sidebar::after,
.zen-send-btn::after,
.quit-combat-btn::after {
	border: none;
}

.session-list {
	flex: 1;
	min-height: 0;
}

.session-item {
	display: flex;
	align-items: center;
	gap: 12rpx;
	padding: 20rpx 22rpx;
	margin-bottom: 12rpx;
	border-radius: 24rpx;
	border: 1px solid transparent;
}

.session-item-shell {
	background: rgba(255, 255, 255, 0.7);
}

.session-item.active {
	border-color: rgba(37, 99, 235, 0.2);
	background: rgba(37, 99, 235, 0.08);
}

.session-title {
	flex: 1;
	font-size: 24rpx;
	color: var(--text-primary);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.delete-btn {
	margin: 0;
	width: 52rpx;
	height: 52rpx;
	border-radius: 50%;
	background: rgba(239, 68, 68, 0.08);
	color: #dc2626;
	font-size: 28rpx;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 0;
}

.sidebar-footer {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.sidebar-admin-btn {
	margin: 0;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 24rpx;
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	color: #ffffff;
	font-size: 30rpx;
	line-height: 1;
	text-align: center;
	font-weight: 700;
}

.sidebar-user-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 18rpx;
}

.sidebar-account-card {
	background: rgba(255, 255, 255, 0.92);
	border-radius: 24rpx;
}

.user-avatar-sidebar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background: #0f172a;
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	font-weight: 800;
}

.user-details {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.user-name-sidebar {
	font-size: 24rpx;
	font-weight: 700;
	color: var(--text-primary);
}

.logout-link-sidebar {
	margin: 0;
	padding: 0;
	background: transparent;
	color: #ef4444;
	font-size: 22rpx;
	line-height: 1.3;
	text-align: left;
}

.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 100vh;
}

.chat-nav {
	padding: 16rpx 20rpx 12rpx;
	padding-top: calc(84rpx + env(safe-area-inset-top));
	display: flex;
	align-items: center;
	justify-content: space-between;
	position: relative;
	z-index: 20;
	gap: 12rpx;
}

.nav-shell {
	background: rgba(255, 255, 255, 0.97);
	border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.nav-left {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	width: 72rpx;
	position: relative;
	left: auto;
	top: auto;
	transform: none;
	flex-shrink: 0;
}

.nav-btn-hamburg {
	margin: 0;
	width: 72rpx;
	height: 72rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 20rpx;
	background: rgba(255, 255, 255, 0.98);
	padding: 0;
	flex-shrink: 0;
}

.nav-btn-hamburg::after {
	border: none;
}

.nav-btn-hamburg::before {
	content: '≡';
	font-size: 42rpx;
	font-weight: 700;
	line-height: 1;
	color: #475569;
}

.nav-btn-text {
	font-size: 0;
	color: transparent;
	line-height: 1;
}

.nav-right-spacer {
	display: block;
	width: 112rpx;
	min-width: 112rpx;
	flex-shrink: 0;
}

.mode-selector {
	background: rgba(255, 255, 255, 0.86);
	box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.95);
}

.mode-selector-pill {
	display: flex;
	flex: 1;
	align-items: center;
	padding: 6rpx;
	border-radius: 999rpx;
	gap: 4rpx;
	width: auto;
	min-width: 0;
	max-width: none;
	margin: 0;
}

.mode-tab {
	display: flex;
	align-items: center;
	justify-content: center;
	min-width: 0;
	flex: 1;
	padding: 14rpx 10rpx;
	border-radius: 999rpx;
	transition: all 0.2s ease;
}

.mode-btn {
	justify-content: center;
}

.mode-btn.active {
	color: var(--accent-color);
}

.tab-active-general,
.tab-active-coach,
.tab-active-expert {
	background: #ffffff;
	box-shadow: 0 8rpx 22rpx rgba(15, 23, 42, 0.08);
}

.tab-text {
	font-size: 26rpx;
	font-weight: 700;
	color: #334155;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.mode-btn.active .tab-text {
	color: var(--accent-color);
}

.tab-divider {
	display: none;
}

.main-body-wrapper {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 0;
	position: relative;
}

.chat-main {
	flex: 1;
	min-height: 0;
}

.welcome-screen {
	padding-bottom: 120rpx;
}

.welcome-stage {
	width: 100%;
}

.zen-welcome-stage {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 28rpx 24rpx 200rpx;
}

.welcome-content {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	width: 100%;
	max-width: 760rpx;
	max-width: 920rpx;
}

.welcome-centered {
	align-items: center;
	text-align: center;
}

.welcome-panel {
	width: 100%;
	max-width: 920rpx;
	padding: 40rpx 28rpx 28rpx;
	border-radius: 40rpx;
	background: rgba(255, 255, 255, 0.9);
	box-sizing: border-box;
}

.zen-title,
.zen-subtitle {
	display: block;
	width: 100%;
}

.zen-avatar-breathe {
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 28rpx;
	box-shadow: 0 20rpx 50rpx rgba(15, 23, 42, 0.08);
}

.zen-avatar-img {
	width: 112rpx;
	height: 112rpx;
	border-radius: 50%;
}

.zen-title {
	font-size: 72rpx;
	font-weight: 900;
	line-height: 1.08;
	color: var(--text-primary);
	word-break: break-word;
	margin-bottom: 14rpx;
}

.zen-title-coach {
	color: #10b981;
}

.zen-title-expert {
	color: #3b82f6;
}

.zen-subtitle {
	font-size: 34rpx;
	line-height: 1.5;
	color: var(--text-secondary);
	margin-bottom: 32rpx;
}

.suggestion-chip-shell {
	width: 100%;
	border-radius: 34rpx;
	background: rgba(248, 250, 252, 0.78);
	padding: 16rpx;
	box-sizing: border-box;
}

.suggestion-chips {
	gap: 18rpx;
}

.zen-suggestion-grid {
	display: flex;
	flex-direction: column;
	gap: 22rpx;
	width: 100%;
	max-width: 860rpx;
}

.card-row {
	display: flex;
	flex-wrap: wrap;
	gap: 18rpx;
}

.zen-card {
	padding: 30rpx 28rpx;
	border-radius: 30rpx;
	background: #ffffff;
	box-shadow: 0 10rpx 32rpx rgba(15, 23, 42, 0.05);
}

.cat-card {
	width: 100%;
	max-width: 360rpx;
	border-radius: 28rpx;
	box-shadow: 0 16rpx 38rpx rgba(25, 103, 74, 0.08);
}

.chip {
	min-height: 80rpx;
}

.zen-card-title {
	display: block;
	font-size: 34rpx;
	font-weight: 800;
	color: var(--text-primary);
	margin-bottom: 12rpx;
}

.zen-card-desc {
	display: block;
	font-size: 28rpx;
	line-height: 1.55;
	color: var(--text-secondary);
}

.zen-expert-icon {
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: #eff6ff;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 24rpx 0;
}

.expert-emoji {
	font-size: 72rpx;
}

.coach-selection-shell {
	width: 100%;
}

.zen-level-up-container {
	width: 100%;
	background: #ffffff;
	border-radius: 36rpx;
	padding: 36rpx 28rpx;
	box-sizing: border-box;
	box-shadow: 0 18rpx 40rpx rgba(15, 23, 42, 0.05);
}

.zen-level-header {
	margin-bottom: 28rpx;
	padding-bottom: 24rpx;
	border-bottom: 1px solid var(--border-light);
}

.coach-step-pill {
	display: inline-flex;
	align-items: center;
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.76);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	font-weight: 700;
	color: #365f4d;
	margin-bottom: 16rpx;
}

.zen-level-text {
	display: block;
	font-size: 22rpx;
	font-weight: 800;
	color: var(--accent-color);
	letter-spacing: 3rpx;
	margin-bottom: 10rpx;
}

.zen-level-desc {
	font-size: 40rpx;
	line-height: 1.2;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-breadcrumbs {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.coach-selection-summary {
	display: flex;
	flex-wrap: wrap;
	justify-content: center;
	gap: 12rpx;
	margin-bottom: 10rpx;
}

.zen-breadcrumb {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.94);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	color: #365f4d;
}

.coach-selection-chip {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.86);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	color: #365f4d;
}

.arrow {
	margin-left: 10rpx;
	color: #94a3b8;
}

.zen-level-grid {
	display: flex;
	flex-direction: column;
	gap: 18rpx;
}

.slide-in {
	animation: slideInRight 0.28s ease;
}

@keyframes slideInRight {
	from { opacity: 0; transform: translateX(20rpx); }
	to { opacity: 1; transform: translateX(0); }
}

.zen-level-card {
	display: flex;
	align-items: center;
	gap: 22rpx;
	padding: 26rpx 24rpx;
	border-radius: 28rpx;
	background: #f8fafc;
	border: 1px solid var(--border-light);
}

.zen-card-huge-icon,
.zen-card-huge-emoji {
	width: 82rpx;
	text-align: center;
	font-size: 54rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-level-info {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.zen-level-title {
	font-size: 30rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-level-desc-mini {
	font-size: 24rpx;
	line-height: 1.45;
	color: var(--text-secondary);
}

.message-list {
	padding: 0 24rpx 340rpx;
}

.message-tail-spacer {
	height: 80rpx;
}

.message-wrapper {
	display: flex;
	gap: 16rpx;
	margin-bottom: 28rpx;
	margin-bottom: 26rpx;
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.avatar {
	width: 72rpx;
	height: 72rpx;
	flex-shrink: 0;
}

.xiaoyi-avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
}

.user-avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
}

.xiaoyi-avatar,
.user-avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
}

.user-avatar {
	display: flex;
	align-items: center;
	justify-content: center;
	background: #0f172a;
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 700;
}

.message-body {
	flex: 1;
}

.message-content {
	max-width: 76%;
	border-radius: 22rpx;
	padding: 26rpx 30rpx;
	border-radius: 30rpx;
	font-size: 30rpx;
	line-height: 1.66;
}

.assistant .message-content {
	background: #ffffff;
	color: var(--text-primary);
	box-shadow: 0 10rpx 32rpx rgba(15, 23, 42, 0.05);
	border-radius: 30rpx 30rpx 30rpx 12rpx;
}

.user .message-content {
	margin-left: auto;
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	color: #ffffff;
	box-shadow: 0 18rpx 36rpx rgba(79, 70, 229, 0.18);
	border-radius: 30rpx 30rpx 12rpx 30rpx;
}

:deep(.markdown-body) {
	display: block;
	word-break: break-word;
}

:deep(.markdown-body p) {
	margin-bottom: 12rpx;
}

:deep(.markdown-body p:last-child) {
	margin-bottom: 0;
}

:deep(.markdown-body table) {
	width: 100%;
	border-collapse: collapse;
	margin-top: 16rpx;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
	border: 1px solid rgba(203, 213, 225, 0.9);
	padding: 8rpx;
}

.chat-message-image {
	width: 100%;
	max-width: 360rpx;
	border-radius: 22rpx;
	margin-bottom: 16rpx;
}

.cursor-blink {
	display: inline-block;
	width: 6rpx;
	height: 28rpx;
	margin-left: 6rpx;
	background: currentColor;
	animation: blink 1s step-end infinite;
}

@keyframes blink {
	50% { opacity: 0; }
}

.combat-intel-panel {
	position: absolute;
	top: 12rpx;
	right: -620rpx;
	bottom: 18rpx;
	width: 500rpx;
	border-radius: 32rpx;
	padding: 26rpx;
	transition: right 0.28s ease;
	z-index: 30;
}

.combat-intel-shell {
	background: rgba(255, 255, 255, 0.96);
	border: 1px solid rgba(211, 233, 221, 0.95);
	box-shadow: -24rpx 0 54rpx rgba(25, 103, 74, 0.1);
}

.combat-intel-panel.show {
	right: 18rpx;
}

.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 20rpx;
	font-size: 30rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.panel-close {
	font-size: 38rpx;
	color: #64748b;
	padding: 10rpx;
}

.panel-content {
	height: 100%;
}

.intel-section {
	margin-bottom: 20rpx;
	padding: 18rpx 20rpx;
	background: rgba(255, 255, 255, 0.96);
	border-radius: 22rpx;
	border: 1px solid var(--border-light);
}

.intel-section-highlight {
	background: rgba(15, 159, 114, 0.08);
}

.intel-label {
	display: block;
	font-size: 22rpx;
	color: #64748b;
	margin-bottom: 10rpx;
}

.intel-text {
	display: block;
	font-size: 26rpx;
	line-height: 1.6;
	color: var(--text-primary);
}

.intel-text-block {
	margin-bottom: 10rpx;
}

.quit-combat-btn {
	margin: 24rpx 0 0;
	height: 84rpx;
	line-height: 84rpx;
	border-radius: 24rpx;
	background: #ef4444;
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 700;
}

.zen-footer-wrapper {
	position: fixed;
	left: 0;
	right: 0;
	bottom: calc(128rpx + env(safe-area-inset-bottom));
	padding: 0 20rpx;
	z-index: 25;
}

.chat-footer {
	position: fixed;
	left: 0;
	right: 0;
	bottom: calc(128rpx + env(safe-area-inset-bottom));
	padding: 0 20rpx;
}

.zen-floating-pill {
	background: rgba(255, 255, 255, 0.98);
	backdrop-filter: blur(30rpx);
	border-radius: 36rpx;
	padding: 12rpx 16rpx;
	box-shadow: 0 14rpx 32rpx rgba(15, 23, 42, 0.08);
	border: 1px solid rgba(15, 23, 42, 0.04);
}

.input-shell {
	width: 100%;
}

.input-container.has-image {
	background: rgba(239, 246, 255, 0.96);
	border-color: rgba(37, 99, 235, 0.24);
}

.input-container.is-focused {
	transform: translateY(-4rpx);
}

.zen-image-preview-area {
	position: relative;
	width: 150rpx;
	height: 150rpx;
	margin: 8rpx 0 20rpx;
}

.image-preview-frame {
	overflow: hidden;
	border-radius: 24rpx;
}

.zen-image-preview {
	width: 150rpx;
	height: 150rpx;
	border-radius: 24rpx;
}

.image-preview-meta {
	position: absolute;
	left: 10rpx;
	bottom: 10rpx;
}

.image-preview-chip {
	padding: 8rpx 14rpx;
	border-radius: 999rpx;
	background: rgba(15, 23, 42, 0.72);
	color: #ffffff;
	font-size: 20rpx;
}

.zen-remove-image-btn {
	position: absolute;
	top: -10rpx;
	right: -10rpx;
	width: 40rpx;
	height: 40rpx;
	border-radius: 50%;
	background: #0f172a;
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
}

.zen-input-row {
	display: flex;
	align-items: center;
	gap: 10rpx;
}

.zen-upload-btn {
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(148, 163, 184, 0.12);
	flex-shrink: 0;
}

.upload-pic-btn.has-attachment {
	background: rgba(37, 99, 235, 0.12);
}

.upload-pic-mark {
	font-size: 34rpx;
	line-height: 1;
	color: #64748b;
}

.zen-input-box {
	flex: 1;
	min-height: 40rpx;
	max-height: 220rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	font-weight: 500;
}

.zen-send-area {
	display: flex;
	align-items: center;
	flex-shrink: 0;
}

.zen-send-btn {
	margin: 0;
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	background: #e2e8f0;
}

.zen-send-btn.active {
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	box-shadow: 0 24rpx 50rpx rgba(37, 99, 235, 0.14);
}

.zen-send-btn.stop {
	background: #ef4444;
}

.icon-send {
	display: block;
	font-size: 30rpx;
	font-weight: 800;
	line-height: 1;
	color: #94a3b8;
}

.zen-send-btn.active .icon-send,
.zen-send-btn.stop .icon-send {
	color: #ffffff;
}

.composer-status-row {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	margin-top: 14rpx;
	padding: 0 12rpx;
}

.composer-status-chip {
	padding: 12rpx 18rpx;
	border-radius: 999rpx;
	font-size: 22rpx;
	line-height: 1.4;
}

.composer-status-chip.image-ready {
	background: rgba(239, 246, 255, 0.96);
	color: #2563eb;
}

.composer-status-chip.generating {
	background: rgba(255, 247, 237, 0.96);
	color: #ea580c;
}

.zen-bottom-nav {
	position: fixed;
	left: 24rpx;
	right: 24rpx;
	bottom: calc(8rpx + env(safe-area-inset-bottom));
	height: 108rpx;
	padding: 0 22rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.92);
	backdrop-filter: blur(20rpx);
	display: flex;
	align-items: center;
	justify-content: space-around;
	box-shadow: 0 12rpx 40rpx rgba(15, 23, 42, 0.08);
	border: 1px solid rgba(15, 23, 42, 0.04);
	z-index: 24;
}

.zen-nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 6rpx;
	width: 160rpx;
}

.zen-nav-icon-wrapper {
	width: 58rpx;
	height: 58rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.zen-nav-glyph {
	font-size: 28rpx;
	color: #0f172a;
}

.zen-nav-glyph.admin {
	color: #91a827;
}

.zen-nav-label {
	font-size: 22rpx;
	font-weight: 700;
	color: #64748b;
}

.zen-nav-item.active .zen-nav-label {
	color: #0f172a;
}

@media screen and (min-width: 768px) {
	.app-layout {
		flex-direction: row;
	}

	.sidebar-overlay {
		display: none;
	}

	.sidebar {
		position: static;
		transform: none;
		width: 320px;
		max-width: none;
		min-height: 100vh;
		padding: 24px;
	}

	.chat-container {
		min-height: 100vh;
	}

	.chat-nav {
		padding: 24px 32px;
	}

	.nav-left {
		width: auto;
	}

	.nav-right-spacer {
		display: none;
	}

	.nav-btn-hamburg {
		display: none;
	}

	.mode-selector-pill {
		position: static;
	}

	.welcome-content,
	.welcome-panel {
		max-width: 860rpx;
	}

	.zen-suggestion-grid {
		max-width: 920rpx;
	}

	.combat-intel-panel {
		right: 18rpx;
	}

	.zen-footer-wrapper {
		position: static;
		padding: 0 32px 32px;
		margin-top: auto;
		pointer-events: auto;
	}

	.zen-bottom-nav {
		display: none;
	}
}
</style>
