<template>
	<view :class="['app-layout', `${currentMode}-mode`]">
		<!-- 婵炴挻鐨滈崱娆戝骄闂佸搫绉寸换鎺斿垝瀹ュ棛顩?-->
		<ChatSidebar
			:is-open="isSidebarOpen"
			:sessions="sessions"
			:current-session-id="currentSessionId"
			:user-name="auth.userName"
			:user-initial="userInitial"
			:is-admin="auth.isAdmin"
			@close="isSidebarOpen = false"
			@newchat="startNewChatWithClose"
			@switchsession="switchSessionWithClose"
			@deletesession="deleteSession"
			@opensettings="openSettings"
			@gotoadmin="goToAdmin"
			@logout="handleLogout"
		/>

		<view class="chat-container">
			<!-- 婵＄偑鍊曢悥濂稿磿鐎电硶鍋撴担鍐棈闁糕晛鎳忕粙澶嬫償閳锋稐绀侀锝堢疀閹惧磭鈧ジ鏌?-->
			<view class="chat-nav nav-shell glass-panel">
				<view class="nav-left">
					<button class="nav-btn-hamburg" @tap="toggleSidebar">
						<text class="nav-btn-text">{{ isSidebarOpen ? '×' : '☰' }}</text>
					</button>
				</view>
				<ChatModeTabs :model-value="currentMode" @change="switchMode" />
				<view class="nav-right-spacer"></view>
			</view>
			<view class="mp-debug-panel">
				<text class="mp-debug-line">m={{ messages.length }} ai={{ isGenerating ? 1 : 0 }}</text>
				<text class="mp-debug-line">stage={{ debugStage }}</text>
			</view>

			<view class="main-body-wrapper">
				<scroll-view
					scroll-y
					class="chat-main"
					:scroll-top="scrollTop"
					:scroll-into-view="scrollIntoViewTarget"
					scroll-with-animation
				>
					<!-- 濠电偛妫庨崹鑲╂崲鐎ｎ喗鍋╃€光偓閸曨剚銆?/ 闂佽桨鐒﹂悷褏鍒掑畝鍕殨婵犲﹤鍟粈?/ 缂備焦绋掑Λ鍐€傛禒瀣仼鐎光偓閸曨剚銆?-->
					<ChatWelcomeScreen
						v-if="messages.length === 0"
						:mode="currentMode"
						:user-name="auth.userName"
						:welcome-msg="welcomeMsg"
						:coach-entry-mode="coachEntryMode"
						:coach-quiz-session="coachQuizSession"
						:current-coach-quiz-question="currentCoachQuizQuestion"
						:selected-region="selectedRegion"
						:selected-persona="selectedPersona"
						:coach-regions="coachRegions"
						:coach-personas="coachPersonas"
						:coach-subjects="coachSubjects"
						@presetmsg="presetMsg"
						@switchcoachentry="val => coachEntryMode = val"
						@startquizsession="startCoachQuizSession"
						@restartquiz="restartCoachQuiz"
						@selectquizanswer="selectCoachQuizAnswer"
						@nextquizquestion="nextCoachQuizQuestion"
						@updateselectedregion="val => selectedRegion = val"
						@updateselectedpersona="val => selectedPersona = val"
						@startduel="startRandomCoachDetailed"
					/>

					<!-- 濠电偞鍨甸悧濠冨閸涙潙绀嗘俊銈呭閳?-->
					<view v-else class="message-list">
						<ChatMessageItem
							v-for="msg in messages"
							:key="msg.id"
							:message="msg"
							:user-initial="userInitial"
							:ai-avatar="XIAOYI_AVATAR_SRC"
							:markdown-nodes="renderMarkdown(msg.content)"
							:mp-blocks="renderMpMessageBlocks(msg.content)"
							@preview-image="previewImage"
						/>
						<view id="chat-bottom-anchor" class="chat-bottom-anchor"></view>
						<view class="message-tail-spacer"></view>
					</view>
				</scroll-view>

				<!-- 闂佽桨鐒﹂悷褏鍒掔仦杞跨喖鍨惧畷鍥╊攨闁诲骸婀遍崑鐐哄垂椤掑嫬绠氶柛娑卞枛琚氶梻鍌氱墑閸ㄥ搫顭?-->
				<CombatIntelPanel
					v-if="currentMode === 'coach'"
					:is-open="isIntelOpen"
					:is-collapsed="isIntelCollapsed"
					:current-scenario="currentScenario"
					:selected-persona="selectedPersona"
					:success-criteria="currentScenario ? formatSuccessCriteria(currentScenario.success_criteria) : []"
					@setopen="val => isIntelOpen = val"
					@setcollapsed="val => isIntelCollapsed = val"
					@quit="requestCoachEvaluation"
				/>
			</view>

			<!-- 底部输入区直接内联，绕开 mp-weixin 自定义组件事件不稳定问题 -->
			<view v-if="!isCoachQuizView" class="chat-composer-shell">
				<view class="mp-chat-footer">
					<view class="mp-composer-shell" :class="{ 'has-image': selectedImage, 'is-focused': isComposerFocused }">
						<view v-if="selectedImage" class="zen-image-preview-area">
							<view class="image-preview-frame">
								<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="previewImage(selectedImage)" />
							</view>
							<view class="image-preview-meta">
								<text class="image-preview-chip">已附图</text>
							</view>
							<view class="zen-remove-image-btn" @tap="removeImage">×</view>
						</view>

						<view class="mp-composer-main">
							<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="triggerImageUpload">
								<text class="upload-pic-mark">+</text>
							</view>
							<input
								:value="inputMsg"
								class="zen-input-box zen-input-box-mp mp-composer-input"
								:cursor-spacing="24"
								confirm-type="send"
								:placeholder="composerPlaceholder"
								@input="handleComposerInput"
								@confirm="handleSendConfirm"
								@focus="isComposerFocused = true"
								@blur="isComposerFocused = false"
							/>
							<view
								v-if="!isGenerating"
								class="zen-send-btn mp-send-btn"
								:class="{ active: composerCanSend }"
								@tap="handleSendTap"
							>
								<image class="icon-send-image" src="/static/send.png" mode="aspectFit" />
							</view>
							<view v-else class="zen-send-btn mp-send-btn stop" @tap="stopGeneration">
								<text class="icon-send">■</text>
							</view>
						</view>
					</view>

					<view v-if="selectedImage || isGenerating" class="composer-status-row">
						<text v-if="selectedImage" class="composer-status-chip image-ready">已附加图片，可直接发送或继续补充文字</text>
						<text v-if="isGenerating" class="composer-status-chip generating">正在生成回复，可点击停止按钮中断</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 闁圭厧鐡ㄥú鐔煎磿閹绢喗鍤曟繝濠傚暙缁€瀣倵娴ｅ啫顥嶆い?-->
		<view class="zen-bottom-nav">
			<view class="zen-nav-item" :class="{ active: currentTab === 'chat' }" @tap="switchTab('chat')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'chat' }" :src="CHAT_NAV_ICON_SRC" mode="aspectFit" />
				</view>
				<text class="zen-nav-label">鑱婂ぉ</text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'notice' }" @tap="switchTab('notice')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'notice' }" :src="NOTICE_NAV_ICON_SRC" mode="aspectFit" />
					<view v-if="hasUnreadNotices" class="zen-nav-badge"></view>
				</view>
				<text class="zen-nav-label">閫氱煡</text>
			</view>


			<view class="zen-nav-item" :class="{ active: currentTab === 'admin' }" @tap="switchTab('admin')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'admin' }" :src="ADMIN_NAV_ICON_SRC" mode="aspectFit" />
				</view>
				<text class="zen-nav-label">鍚庡彴</text>
			</view>
		</view>

		<!-- 閻庢鍠栧﹢閬嶆偘閵壯呯＜闁告洦浜濋?-->
		<ChatSettingsSheet
			:show="showSettings"
			:output-length="outputLength"
			:pwd-form="pwdForm"
			:pwd-loading="pwdLoading"
			@setshow="val => showSettings = val"
			@setoutputlength="val => outputLength = val"
			@updatepwdform="({field, value}) => pwdForm[field] = value"
			@submitpwd="submitChangePassword"
		/>

		<ChatNoticeCenter
			:show="showNoticeCenter"
			:notice-tab="noticeTab"
			:loading="noticesLoading"
			:notices="displayNotices"
			@setshow="val => showNoticeCenter = val"
			@setnoticetab="val => noticeTab = val"
			@previewnotice="previewNotice"
		/>
	</view>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { renderMarkdown } from '@/utils/markdown'
import { resolveApiUrl } from '@/utils/api'
import { buildImageDataUrl, validateMpImageSelection } from '@/utils/image-data-url'
import { uploadChatImage } from '@/utils/chat-image-upload'
import { captureClientEvent } from '@/utils/error-logger'
import { createMpStreamChatController } from '@/utils/mp-stream-chat'
import { createSseEventParser } from '@/utils/sse-parser'

import ChatSidebar from './components/ChatSidebar.vue'
import ChatModeTabs from './components/ChatModeTabs.vue'
import ChatWelcomeScreen from './components/ChatWelcomeScreen.vue'
import ChatMessageItem from './components/ChatMessageItem.vue'
import CombatIntelPanel from './components/CombatIntelPanel.vue'
import ChatSettingsSheet from './components/ChatSettingsSheet.vue'
import ChatNoticeCenter from './components/ChatNoticeCenter.vue'

const auth = useAuthStore()
const XIAOYI_AVATAR_SRC = '/static/xiaoyi_character.png'
const CHAT_NAV_ICON_SRC = '/static/nav_chat.png'
const NOTICE_NAV_ICON_SRC = '/static/nav_notice.png'
const ADMIN_NAV_ICON_SRC = '/static/nav_admin.png'
const NOTICE_SEEN_STORAGE_KEY = 'zyd_notice_last_seen_id'

const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const isSidebarOpen = ref(false)
const welcomeMsg = ref('你好，我是小易智能助手。')
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
const isIntelCollapsed = ref(false)
const selectedRegion = ref(null)
const selectedPersona = ref(null)
const coachEntryMode = ref('menu')
const coachQuizSession = ref(null)
const coachQuizLoading = ref(false)
const coachQuizError = ref('')

const showNoticeCenter = ref(false)
const noticeTab = ref('current')
const currentNotices = ref([])
const noticeHistory = ref([])
const noticesLoading = ref(false)
const hasUnreadNotices = ref(false)
const showSettings = ref(false)
const outputLength = ref('medium')
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdLoading = ref(false)

// 闁汇埄鍨遍幃鍌炲闯濞差亝鐓€鐎广儱娲ㄩ弸?
const POST_LOGIN_FRESH_CHAT_KEY = 'zyd_post_login_fresh_chat'
const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'
const coachRegions = [
	{ name: '美国线路', short: 'US', desc: '偏远区域、附加费和时效沟通。' },
	{ name: '欧洲线路', short: 'EU', desc: 'VAT、清关与签收异常处理。' },
]
const coachPersonas = [
	{ name: '强势议价型客户', emoji: 'A', desc: '关注价格，倾向压价与反复比价。' },
	{ name: '流程合规型客户', emoji: 'B', desc: '关注规则、凭证和流程闭环。' },
]
const coachSubjects = [
	{ name: '报价谈判', emoji: '1', desc: '围绕报价、时效、附加费与方案推荐。' },
	{ name: '异常处理', emoji: '2', desc: '围绕破损、延误、投诉与补偿沟通。' },
	{ name: '催单跟进', emoji: '3', desc: '围绕方案确认、异议处理和成交推进。' },
	{ name: '复盘总结', emoji: '4', desc: '围绕沟通复盘、风险识别和改进建议。' },
]

const userInitial = computed(() => String(auth.userName || '易').trim().slice(0, 1).toUpperCase() || '易')
const displayNotices = computed(() => (noticeTab.value === 'history' ? noticeHistory.value : currentNotices.value))
const isCoachQuizView = computed(() => currentMode.value === 'coach' && coachEntryMode.value === 'quiz')
const isComposerFocused = ref(false)
const composerCanSend = computed(() => Boolean(String(inputMsg.value || '').trim() || selectedImage.value))
const composerPlaceholder = computed(() => (
	currentMode.value === 'coach'
		? '和客户对练中...'
		: (selectedImage.value ? '补充图片说明，或直接发送...' : '发送消息，支持粘贴或上传图片...')
))
const debugStage = ref('idle')
const currentCoachQuizQuestion = computed(() => {
	if (!coachQuizSession.value || coachQuizSession.value.completed) return null
	return coachQuizSession.value.questions[coachQuizSession.value.currentIndex] || null
})

// 闂佸搫鍊介～澶屾兜?- 闂佺硶鏅炲▍锝夈€侀崨顖滀笉闁挎稑瀚崐?
const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value
const openSettings = () => { showSettings.value = true; isSidebarOpen.value = false; }
const closeSettings = () => {
    showSettings.value = false
    pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
    pwdLoading.value = false
}

const handleLogout = () => { auth.logout(); uni.reLaunch({ url: '/pages/login/login' }); }
const goToAdmin = () => { isSidebarOpen.value = false; currentTab.value = 'admin'; uni.navigateTo({ url: '/pages/admin/admin' }); }

const switchTab = (tab) => {
	if (tab === 'notice') { openNoticeCenter(); return; }
	currentTab.value = tab
	showNoticeCenter.value = false
	if (tab === 'admin') goToAdmin()
}

// 闂佸搫鍊介～澶屾兜?- 闁诲海鏁搁、濠囨儊閻ｅ瞼涓嶉柨娑樺閸?
const startNewChat = ({ forceCreate = false } = {}) => {
	if (currentMode.value === 'coach') resetCoachState()
	if (!forceCreate && currentSessionId.value) {
		const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
		if (currentSession && (!currentSession.messages || currentSession.messages.length === 0)) {
			messages.value = []; inputMsg.value = ''; clearSelectedImage(); return
		}
	}
	const newSessionId = `${Date.now()}`
	sessions.value = [{ id: newSessionId, title: '新对话', messages: [] }, ...sessions.value].slice(0, 20)
	currentSessionId.value = newSessionId
	messages.value = []; inputMsg.value = ''; clearSelectedImage(); saveSessions()
}

const startNewChatWithClose = () => { startNewChat({ forceCreate: true }); isSidebarOpen.value = false; }
const deleteSession = (sessionId) => {
	sessions.value = sessions.value.filter((item) => item.id !== sessionId)
	if (currentSessionId.value === sessionId) {
		if (sessions.value[0]) switchSession(sessions.value[0].id)
		else startNewChat({ forceCreate: true })
	}
	saveSessions()
}

const switchSession = (sessionId) => {
	const targetSession = sessions.value.find((session) => session.id === sessionId)
	if (!targetSession) return
	currentSessionId.value = sessionId
	messages.value = [...(targetSession.messages || [])]
	clearSelectedImage(); scrollToBottom()
}

const switchSessionWithClose = (sessionId) => { switchSession(sessionId); isSidebarOpen.value = false; }

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
	try { uni.setStorageSync(`zyd_sessions_${currentMode.value}`, JSON.stringify(sessions.value.slice(0, 20))) } catch (e) {}
}

const switchMode = (mode) => {
	if (currentMode.value === mode) return
	currentMode.value = mode
	uni.setStorageSync(LAST_CHAT_MODE_KEY, mode)
	resetCoachState(); isSidebarOpen.value = false; isIntelOpen.value = false
	selectedRegion.value = null; selectedPersona.value = null
	if (mode !== 'coach') currentScenario.value = null
	try {
		const raw = uni.getStorageSync(`zyd_sessions_${mode}`)
		sessions.value = raw ? JSON.parse(raw) : []
	} catch (e) { sessions.value = [] }
	if (sessions.value.length === 0) { startNewChat({ forceCreate: true }); return }
	switchSession(sessions.value[0].id)
}

// 闂佸搫鍊介～澶屾兜?- 闂佸憡鐟﹂崹鍧楀焵椤戞寧顦风紒妤€鑻湁濞达絽鎽滅涵鈧?
let requestTask = null
const stopGeneration = () => { if (requestTask) requestTask.abort(); isGenerating.value = false; }
const handleComposerInput = (event) => { inputMsg.value = event.detail?.value || '' }
const logMpChatDebug = (stage, payload = {}) => {
	debugStage.value = stage
	try {
		console.warn('[mp-chat-debug]', stage, JSON.stringify(payload))
	} catch (error) {
		console.warn('[mp-chat-debug]', stage, payload)
	}
}
const handleSendTap = () => {
	logMpChatDebug('tap-send', {
		inputLength: String(inputMsg.value || '').length,
		hasImage: Boolean(selectedImage.value),
		isGenerating: isGenerating.value,
		isImageUploading: isImageUploading.value,
	})
	sendMessage('tap')
}
const handleSendConfirm = () => {
	logMpChatDebug('confirm-send', {
		inputLength: String(inputMsg.value || '').length,
		hasImage: Boolean(selectedImage.value),
		isGenerating: isGenerating.value,
		isImageUploading: isImageUploading.value,
	})
	sendMessage('confirm')
}

const sendMessage = async (source = 'direct') => {
	const content = inputMsg.value.trim()
	logMpChatDebug('sendMessage-enter', {
		source,
		trimmedLength: content.length,
		hasImage: Boolean(selectedImage.value),
		isGenerating: isGenerating.value,
		isImageUploading: isImageUploading.value,
	})
	if (!content && !selectedImage.value) {
		logMpChatDebug('sendMessage-return', { reason: 'empty-message' })
		return
	}
	if (isGenerating.value) {
		logMpChatDebug('sendMessage-return', { reason: 'already-generating' })
		return
	}
	if (selectedImage.value && isImageUploading.value) {
		logMpChatDebug('sendMessage-return', { reason: 'image-uploading' })
		uni.showToast({ title: '图片上传中，请稍候', icon: 'none' }); return
	}

	const currentImageUploadId = selectedImageUploadId.value || null
	const currentImageBase64 = selectedImage.value && selectedImage.value.startsWith('data:')
		? selectedImage.value.split(',')[1] : null

	let finalContent = content
	if (outputLength.value === 'short') finalContent = `[杈撳嚭鍋忓ソ:绠€娲乚 ${content}`
	else if (outputLength.value === 'long') finalContent = `[杈撳嚭鍋忓ソ:璇︾粏] ${content}`

	messages.value.push({ id: `user-${Date.now()}`, role: 'user', content, image: selectedImage.value })
	logMpChatDebug('user-message-pushed', {
		messagesCount: messages.value.length,
		contentPreview: content.slice(0, 20),
	})
	nextTick(() => {
		logMpChatDebug('after-next-tick', {
			messagesCount: messages.value.length,
			isGenerating: isGenerating.value,
		})
	})
	inputMsg.value = ''; clearSelectedImage(); isGenerating.value = true
	
	const aiMsgId = `ai-${Date.now()}`
	messages.value.push({ id: aiMsgId, role: 'assistant', content: '', isTyping: true })
	scrollToBottom()
	const sseParser = createSseEventParser()

	requestTask = createMpStreamChatController({
		buildRequestOptions: () => ({
			url: resolveApiUrl('/api/chat/stream'),
			method: 'POST',
			header: { Authorization: `Bearer ${auth.token}`, 'content-type': 'application/json' },
			data: {
				message: finalContent,
				mode: currentMode.value,
				image_upload_id: currentImageUploadId,
				image_base64: currentImageBase64,
				history: messages.value.slice(0, -2).map((item) => ({ role: item.role, content: item.content })),
			},
		}),
	})
	logMpChatDebug('request-created', {
		url: resolveApiUrl('/api/chat/stream'),
		historyCount: messages.value.slice(0, -2).length,
	})

	try {
		await requestTask.start({
			onStatus: (statusCode) => {
				logMpChatDebug('request-status', { statusCode })
			},
			onText: (text) => {
				logMpChatDebug('request-chunk', { chunkLength: String(text || '').length })
				const aiMsg = messages.value.find((item) => item.id === aiMsgId)
				if (!aiMsg || !text) return
				const parsed = sseParser.push(text)
				for (const event of parsed.events) {
					if (event.type === 'content' && event.content) {
						aiMsg.content += event.content
					}
				}
				if (parsed.plainText) {
					aiMsg.content += parsed.plainText
				}
				scrollToBottom()
			},
		})
	} catch (error) {
		logMpChatDebug('request-error', {
			message: error?.message || 'unknown-error',
		})
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg && !aiMsg.content) aiMsg.content = `鍑洪敊浜嗭細${error?.message || '璇锋眰澶辫触'}`
	} finally {
		logMpChatDebug('sendMessage-finally', {
			isGenerating: false,
			requestTaskCleared: true,
		})
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) aiMsg.isTyping = false
		isGenerating.value = false; requestTask = null; saveSessions()
	}
}

// 闂佸搫鍊介～澶屾兜?- 闂佽桨鐒﹂悷褏鍒掑畝鍕劵闁哄嫬绻掔敮?
const startCoachQuizSession = async (count) => {
	coachQuizLoading.value = true; coachQuizError.value = ''; coachQuizSession.value = null
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl(`/api/coach-quiz/session?count=${count}`),
				method: 'GET',
				header: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
				success: resolve, fail: reject,
			})
		})
		if (response.statusCode >= 400) throw new Error('鑾峰彇棰樼洰澶辫触')
		const questions = response.data?.questions || []
		if (questions.length === 0) { coachQuizError.value = '鏆傛棤鍙敤棰樼洰'; return }
		coachQuizSession.value = {
			currentIndex: 0, correctCount: 0, completed: false,
			questions: questions.map(q => ({ ...q, selectedAnswer: '', isCorrect: false }))
		}
	} catch (e) { coachQuizError.value = '棰樼洰鍔犺浇澶辫触锛岃绋嶅悗閲嶈瘯'; } finally { coachQuizLoading.value = false }
}

const selectCoachQuizAnswer = (key) => {
	const q = currentCoachQuizQuestion.value
	if (!q || q.selectedAnswer) return
	q.selectedAnswer = key; q.isCorrect = q.answer === key
	if (q.isCorrect) coachQuizSession.value.correctCount++
}

const nextCoachQuizQuestion = () => {
	if (coachQuizSession.value.currentIndex >= coachQuizSession.value.questions.length - 1) coachQuizSession.value.completed = true
	else coachQuizSession.value.currentIndex++
}

const restartCoachQuiz = () => { coachQuizSession.value = null; coachQuizError.value = ''; coachEntryMode.value = 'quiz' }
const resetCoachState = () => {
	currentScenario.value = null; isIntelOpen.value = false; isIntelCollapsed = false
	selectedRegion.value = null; selectedPersona.value = null; coachEntryMode.value = 'menu'
	coachQuizSession.value = null
}

const startRandomCoachDetailed = (subjectName) => {
	if (!selectedRegion.value || !selectedPersona.value) return
	coachEntryMode.value = 'duel'
	const matches = coachCases.value.filter((c) => (c.category || '').includes(selectedRegion.value))
	const randomCase = matches.length ? matches[Math.floor(Math.random() * matches.length)] : null
	currentScenario.value = randomCase || {
		name: `${selectedRegion.value} 路 ${subjectName}`,
		success_criteria: ['先确认客户诉求与约束条件', '给出两套可执行方案并解释差异'],
	}
	isIntelOpen.value = true
	inputMsg.value = `我要挑战「${currentScenario.value.name}」场景`
	sendMessage()
}

const requestCoachEvaluation = () => {
	if (isGenerating.value || messages.value.length === 0) return
	inputMsg.value = '【结束对练】请基于刚才的对话，从资深销售教练视角输出结构化点评。'
	sendMessage()
}

const openNoticeCenter = async () => {
	showNoticeCenter.value = true; noticesLoading.value = true
	try {
		const [current, history] = await Promise.all([
			new Promise(res => uni.request({ url: resolveApiUrl('/api/notices/current'), header: { Authorization: `Bearer ${auth.token}` }, success: res })),
			new Promise(res => uni.request({ url: resolveApiUrl('/api/notices/history'), header: { Authorization: `Bearer ${auth.token}` }, success: res }))
		])
		currentNotices.value = current.data || []; noticeHistory.value = history.data || []
		if (currentNotices.value[0]) {
			uni.setStorageSync(NOTICE_SEEN_STORAGE_KEY, String(currentNotices.value[0].id))
			hasUnreadNotices.value = false
		}
	} finally { noticesLoading.value = false }
}

const previewNotice = (n) => uni.showModal({ title: '通知详情', content: n.content, showCancel: false })

const submitChangePassword = async () => {
	const { oldPwd, newPwd, confirmPwd } = pwdForm.value
	if (!oldPwd || !newPwd || !confirmPwd) { uni.showToast({ title: '请完整填写密码字段', icon: 'none' }); return }
	pwdLoading.value = true
	const res = await auth.changePassword(oldPwd, newPwd)
	pwdLoading.value = false
	if (res?.success) { uni.showToast({ title: '密码修改成功' }); closeSettings() }
	else uni.showToast({ title: res?.message || '密码修改失败', icon: 'none' })
}

// 闂佹悶鍎辨晶鑺ユ櫠閺嶃劍缍囬柛娑卞幖琚?
const clearSelectedImage = () => { selectedImage.value = null; selectedImageUploadId.value = ''; isImageUploading.value = false }
const removeImage = () => clearSelectedImage()
const previewImage = (url) => uni.previewImage({ urls: [url] })
const triggerImageUpload = () => {
	uni.chooseImage({
		count: 1, sizeType: ['compressed'],
		success: async (res) => {
			const filePath = res.tempFilePaths?.[0]
			if (!filePath) return
			selectedImage.value = filePath; isImageUploading.value = true
			try {
				const up = await uploadChatImage({ filePath, token: auth.token })
				selectedImageUploadId.value = up.image_upload_id
			} catch (e) {
				// 闂傚倸瀚粔鑸殿殽閸ャ劍濯撮悹鎭掑妽閺?base64
				uni.getFileSystemManager().readFile({
					filePath, encoding: 'base64',
					success: ({ data }) => { selectedImage.value = buildImageDataUrl(filePath, data) }
				})
			} finally { isImageUploading.value = false }
		}
	})
}

const scrollToBottom = () => {
	nextTick(() => {
		scrollIntoViewTarget.value = ''
		setTimeout(() => { scrollIntoViewTarget.value = 'chat-bottom-anchor' }, 50)
	})
}

const presetMsg = (m) => { inputMsg.value = m; sendMessage() }

// Utility helpers for components
const formatSuccessCriteria = (c) => Array.isArray(c) ? c : (typeof c === 'string' ? c.split('\n').filter(Boolean) : [])
const sanitizeMpInlineText = (text) => {
	return String(text || '')
		.replace(/\*\*(.*?)\*\*/g, '$1')
		.replace(/__(.*?)__/g, '$1')
		.replace(/`([^`]+)`/g, '$1')
		.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
		.replace(/<br\s*\/?>/gi, ' ')
		.replace(/<\/?[^>]+>/g, ' ')
		.replace(/\s+/g, ' ')
		.trim()
}

const normalizeInlineListMarkers = (text) => {
	let normalized = String(text || '').replace(/\r\n?/g, '\n')
	normalized = normalized.replace(
		/(^|\n)(\s*(?:\d{1,2}|[A-H])[.)])(?=\S)/g,
		'$1$2 '
	)
	normalized = normalized.replace(
		/([^\n])\s+((?:\d{1,2}|[A-H])[.)]\s+)/g,
		(match, prevChar, marker) => {
			if (/\d/.test(prevChar) && /^\d+\./.test(marker)) return match
			return `${prevChar}\n${marker}`
		}
	)
	return normalized
}

const renderMpMessageBlocks = (content) => {
	const lines = normalizeInlineListMarkers(content).split('\n')
	const blocks = []
	for (const rawLine of lines) {
		const line = rawLine.trim()
		if (!line) continue

		if (/^([-*_])\1{2,}$/.test(line)) {
			blocks.push({ type: 'divider' })
			continue
		}

		const headingMatch = line.match(/^#{1,6}\s+(.+)$/)
		if (headingMatch) {
			blocks.push({ type: 'heading', text: sanitizeMpInlineText(headingMatch[1]) })
			continue
		}

		const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/)
		if (orderedMatch) {
			blocks.push({
				type: 'ordered-item',
				text: sanitizeMpInlineText(orderedMatch[2]),
				prefix: `${orderedMatch[1]}.`,
			})
			continue
		}

		const alphaOrderedMatch = line.match(/^([A-H])[.)]\s+(.+)$/)
		if (alphaOrderedMatch) {
			blocks.push({
				type: 'ordered-item',
				text: sanitizeMpInlineText(alphaOrderedMatch[2]),
				prefix: `${alphaOrderedMatch[1]}.`,
			})
			continue
		}

		const bulletMatch = line.match(/^[-*+]\s+(.+)$/)
		if (bulletMatch) {
			blocks.push({
				type: 'bullet-item',
				text: sanitizeMpInlineText(bulletMatch[1]),
				prefix: '-',
			})
			continue
		}

		const tableRowMatch = line.match(/^\|(.+)\|$/)
		if (tableRowMatch) {
			const cells = tableRowMatch[1]
				.split('|')
				.map((cell) => sanitizeMpInlineText(cell))
				.filter(Boolean)
			if (cells.length === 0 || cells.every((cell) => /^:?-{3,}:?$/.test(cell))) {
				continue
			}
			blocks.push({
				type: 'table-row',
				text: cells.join('  |  '),
			})
			continue
		}

		const text = sanitizeMpInlineText(line)
		if (!text) continue
		blocks.push({ type: 'paragraph', text })
	}
	return blocks
}

// 闂佹眹鍨婚崰搴ㄥ箠閿熺姴宸濋柕濠忛檮閸?
onMounted(() => {
	debugStage.value = 'mounted'
	if (!auth.isAuthenticated) { uni.reLaunch({ url: '/pages/login/login' }); return }
	// 寤惰繜璇诲彇 storage锛岄伩鍏?invoke too early 閿欒
	try { outputLength.value = uni.getStorageSync('zyd_output_length') || 'medium' } catch (e) {}
	const shouldFresh = uni.getStorageSync(POST_LOGIN_FRESH_CHAT_KEY) === '1'
	if (shouldFresh) uni.removeStorageSync(POST_LOGIN_FRESH_CHAT_KEY)
	const initialMode = shouldFresh ? 'general' : (uni.getStorageSync(LAST_CHAT_MODE_KEY) || 'general')
	switchMode(initialMode)
	
	uni.request({ url: resolveApiUrl('/api/upload/coach-cases'), header: { Authorization: `Bearer ${auth.token}` }, success: r => coachCases.value = r.data || [] })
	uni.request({ url: resolveApiUrl('/api/settings/public'), success: r => welcomeMsg.value = r.data?.ai_welcome_message || welcomeMsg.value })
	uni.request({
		url: resolveApiUrl('/api/notices/current'), header: { Authorization: `Bearer ${auth.token}` },
		success: r => {
			const latestId = r.data?.[0]?.id; const seenId = uni.getStorageSync(NOTICE_SEEN_STORAGE_KEY)
			hasUnreadNotices.value = latestId && String(latestId) !== String(seenId)
		}
	})
})

watch(
	() => messages.value.length,
	(length) => {
		logMpChatDebug('watch-messages-length', { length })
	}
)
</script>

<style>
.app-layout {
	display: flex;
	flex-direction: column;
	height: 100vh;
	background: #f8fafc;
}

.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.chat-nav {
	height: 44px;
	padding: calc(var(--status-bar-height) + 4px) 16px 4px;
	display: flex;
	align-items: center;
	background: rgba(255, 255, 255, 0.9);
	backdrop-filter: blur(10px);
	z-index: 10;
}

.nav-left,
.nav-right-spacer {
	width: 40px;
	flex-shrink: 0;
}

.nav-btn-hamburg {
	width: 40px;
	height: 40px;
	padding: 0;
	margin: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	background: transparent;
	border: none;
	line-height: 1;
}

.nav-btn-hamburg::after {
	border: none;
}

.nav-btn-text {
	font-size: 22px;
	font-weight: 500;
	color: #0f172a;
	line-height: 1;
}

.mp-debug-panel {
	padding: 4px 12px;
	background: rgba(15, 23, 42, 0.78);
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.mp-debug-line {
	font-size: 10px;
	line-height: 1.4;
	color: #f8fafc;
}

.main-body-wrapper {
	flex: 1;
	position: relative;
	overflow: hidden;
}

.chat-main {
	height: 100%;
}

.message-list {
	padding-top: 20px;
}

.chat-bottom-anchor {
	height: 1px;
}

.message-tail-spacer {
	height: 40px;
}

.zen-bottom-nav {
	height: 56px;
	display: flex;
	background: #ffffff;
	border-top: 1px solid rgba(0, 0, 0, 0.05);
	padding-bottom: env(safe-area-inset-bottom);
}

.zen-nav-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	opacity: 0.5;
}

.zen-nav-item.active {
	opacity: 1;
}

.zen-nav-icon {
	position: relative;
	width: 24px;
	height: 24px;
}

.zen-nav-icon-image {
	width: 100%;
	height: 100%;
}

.zen-nav-badge {
	position: absolute;
	top: -2px;
	right: -2px;
	width: 8px;
	height: 8px;
	background: #ef4444;
	border-radius: 50%;
}

.zen-nav-label {
	font-size: 10px;
	margin-top: 2px;
}

/* 濠碘槅鍨埀顒€纾涵鈧繛鎴炴尭椤兘銆傛禒瀣殞?*/
.general-mode { --theme-color: #2563eb; }
.coach-mode { --theme-color: #059669; }
.expert-mode { --theme-color: #7c3aed; }

.chat-composer-shell {
	background: #ffffff;
	border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.mp-chat-footer {
	background: #ffffff;
	padding: 8px 16px calc(8px + env(safe-area-inset-bottom));
}

.mp-composer-shell {
	background: #f1f5f9;
	border-radius: 24px;
	padding: 4px 8px;
	transition: all 0.3s;
	border: 1px solid transparent;
}

.mp-composer-shell.is-focused {
	background: #ffffff;
	border-color: #2563eb;
	box-shadow: 0 4px 20px rgba(37, 99, 235, 0.08);
}

.mp-composer-main {
	display: flex;
	align-items: center;
}

.zen-input-box {
	flex: 1;
	min-height: 40px;
	max-height: 120px;
	padding: 8px 12px;
	font-size: 15px;
	color: #1e293b;
}

.zen-input-box-mp {
	height: 40px;
}

.zen-upload-btn {
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
	flex-shrink: 0;
}

.upload-pic-mark {
	font-size: 24px;
	font-weight: 300;
	line-height: 1;
}

.zen-send-btn {
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	transition: all 0.2s;
	opacity: 0.5;
	flex-shrink: 0;
}

.zen-send-btn.active {
	opacity: 1;
}

.icon-send-image {
	width: 24px;
	height: 24px;
}

.icon-send {
	font-size: 18px;
	line-height: 1;
}

.zen-send-btn.stop {
	opacity: 1;
	color: #ef4444;
}

.zen-image-preview-area {
	display: flex;
	align-items: center;
	padding: 8px;
	background: #ffffff;
	border-radius: 12px;
	margin-bottom: 4px;
}

.image-preview-frame {
	width: 48px;
	height: 48px;
	border-radius: 8px;
	overflow: hidden;
	margin-right: 12px;
	border: 1px solid #e2e8f0;
	flex-shrink: 0;
}

.zen-image-preview {
	width: 100%;
	height: 100%;
}

.image-preview-meta {
	display: flex;
	align-items: center;
}

.image-preview-chip {
	font-size: 12px;
	color: #64748b;
	background: #f1f5f9;
	padding: 2px 8px;
	border-radius: 4px;
}

.zen-remove-image-btn {
	margin-left: auto;
	padding: 8px;
	color: #94a3b8;
	font-size: 18px;
	line-height: 1;
}

.composer-status-row {
	padding: 6px 12px 0;
	display: flex;
	flex-wrap: wrap;
}

.composer-status-chip {
	font-size: 11px;
	padding: 2px 8px;
	border-radius: 10px;
	margin-right: 8px;
	margin-bottom: 4px;
}

.image-ready {
	background: #ecfdf5;
	color: #059669;
}

.generating {
	background: #eff6ff;
	color: #2563eb;
	animation: breathe 2s infinite ease-in-out;
}

@keyframes breathe {
	0%, 100% { opacity: 0.7; }
	50% { opacity: 1; }
}
</style>

