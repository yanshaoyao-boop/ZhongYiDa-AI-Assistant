<template>
	<view :class="['app-layout', `${currentMode}-mode`]">
		<!-- 娓氀嗙珶閺嶅繒绮嶆禒?-->
		<ChatSidebar
			:is-open="isSidebarOpen"
			:sessions="sessions"
			:current-session-id="currentSessionId"
			:user-name="auth.userName"
			:user-initial="userInitial"
			:is-admin="auth.isAdmin"
			@close="isSidebarOpen = false"
			@new-chat="startNewChatWithClose"
			@switch-session="switchSessionWithClose"
			@delete-session="deleteSession"
			@open-settings="openSettings"
			@go-to-admin="goToAdmin"
			@logout="handleLogout"
		/>

		<view class="chat-container">
			<!-- 妞ゅ爼鍎寸€佃壈鍩呮稉搴⒛佸蹇撳瀼閹?-->
			<view class="chat-nav nav-shell glass-panel">
				<view class="nav-left">
					<button class="nav-btn-hamburg" @tap="toggleSidebar">
						<text class="nav-btn-text">{{ isSidebarOpen ? '鑴? : '閳? }}</text>
					</button>
				</view>
				<ChatModeTabs v-model="currentMode" @update:model-value="switchMode" />
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
					<!-- 濞嗐垼绻嬮悾宀勬桨 / 閺佹瑧绮岄懣婊冨礋 / 缁涙棃顣介悾宀勬桨 -->
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
						@preset-msg="presetMsg"
						@switch-coach-entry="val => coachEntryMode = val"
						@start-quiz-session="startCoachQuizSession"
						@restart-quiz="restartCoachQuiz"
						@select-quiz-answer="selectCoachQuizAnswer"
						@next-quiz-question="nextCoachQuizQuestion"
						@update:selected-region="val => selectedRegion = val"
						@update:selected-persona="val => selectedPersona = val"
						@start-duel="startRandomCoachDetailed"
					/>

					<!-- 濞戝牊浼呴崚妤勩€?-->
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

				<!-- 閺佹瑧绮屽Ο鈥崇础鐎圭偞鍨幆鍛Г闂堛垺婢?-->
				<CombatIntelPanel
					v-if="currentMode === 'coach'"
					:is-open="isIntelOpen"
					v-model:is-collapsed="isIntelCollapsed"
					:current-scenario="currentScenario"
					:selected-persona="selectedPersona"
					:success-criteria="currentScenario ? formatSuccessCriteria(currentScenario.success_criteria) : []"
					@update:is-open="val => isIntelOpen = val"
					@quit="requestCoachEvaluation"
				/>
			</view>

			<!-- 鏉堟挸鍙嗗鍡楀隘閸?-->
			<ChatMessageInput
				v-if="!isCoachQuizView"
				v-model:input-msg="inputMsg"
				:selected-image="selectedImage"
				:is-generating="isGenerating"
				:placeholder="currentMode === 'coach' ? '娑撳骸顓归幋宄邦嚠鐠囨繀鑵?..' : '閸欐垿鈧焦绉烽幁顖樷偓浣虹煒鐠愬瓨鍨ㄩ幏鏍у弳閸ュ墽澧?..'"
				@send="sendMessage"
				@stop="stopGeneration"
				@trigger-image-upload="triggerImageUpload"
				@remove-image="removeImage"
				@preview-image="previewImage"
			/>
		</view>

		<!-- 鎼存洟鍎撮懣婊冨礋鐎佃壈顫?-->
		<view class="zen-bottom-nav">
			<view class="zen-nav-item" :class="{ active: currentTab === 'chat' }" @tap="switchTab('chat')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'chat' }" :src="CHAT_NAV_ICON_SRC" mode="aspectFit" />
				</view>
				<text class="zen-nav-label">鐎电鐦?/text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'notice' }" @tap="switchTab('notice')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'notice' }" :src="NOTICE_NAV_ICON_SRC" mode="aspectFit" />
					<view v-if="hasUnreadNotices" class="zen-nav-badge"></view>
				</view>
				<text class="zen-nav-label">闁氨鐓?/text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'tools' }" @tap="switchTab('tools')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'tools' }" :src="TOOLS_NAV_ICON_SRC" mode="aspectFit" />
				</view>
				<text class="zen-nav-label">瀹搞儱鍙?/text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'admin' }" @tap="switchTab('admin')">
				<view class="zen-nav-icon">
					<image class="zen-nav-icon-image" :class="{ active: currentTab === 'admin' }" :src="ADMIN_NAV_ICON_SRC" mode="aspectFit" />
				</view>
				<text class="zen-nav-label">缁狅紕鎮?/text>
			</view>
		</view>

		<!-- 瀵湱鐛ョ紒鍕 -->
		<ChatSettingsSheet
			v-model:show="showSettings"
			v-model:output-length="outputLength"
			:pwd-form="pwdForm"
			:pwd-loading="pwdLoading"
			@update:pwd-form="({field, value}) => pwdForm[field] = value"
			@submit-pwd="submitChangePassword"
		/>

		<ChatNoticeCenter
			v-model:show="showNoticeCenter"
			v-model:notice-tab="noticeTab"
			:loading="noticesLoading"
			:notices="displayNotices"
			@preview-notice="previewNotice"
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

// 缂佸嫪娆㈢€电厧鍙?import ChatSidebar from './components/ChatSidebar.vue'
import ChatModeTabs from './components/ChatModeTabs.vue'
import ChatWelcomeScreen from './components/ChatWelcomeScreen.vue'
import ChatMessageItem from './components/ChatMessageItem.vue'
import ChatMessageInput from './components/ChatMessageInput.vue'
import CombatIntelPanel from './components/CombatIntelPanel.vue'
import ChatSettingsSheet from './components/ChatSettingsSheet.vue'
import ChatNoticeCenter from './components/ChatNoticeCenter.vue'

const auth = useAuthStore()
const XIAOYI_AVATAR_SRC = '/static/xiaoyi_transparent.png'
const CHAT_NAV_ICON_SRC = '/static/nav_chat.png'
const NOTICE_NAV_ICON_SRC = '/static/nav_notice.png'
const TOOLS_NAV_ICON_SRC = '/static/nav_tools.png'
const ADMIN_NAV_ICON_SRC = '/static/nav_admin.png'
const NOTICE_SEEN_STORAGE_KEY = 'zyd_notice_last_seen_id'

// 閸╄櫣顢呴悩鑸碘偓?const messages = ref([])
const inputMsg = ref('')
const isGenerating = ref(false)
const isSidebarOpen = ref(false)
const welcomeMsg = ref('閹劎娈戦崗銊ャ亯閸婃瑦娅ら懗钘夊И閹?)
const currentMode = ref('general')
const sessions = ref([])
const currentSessionId = ref(null)
const selectedImage = ref(null)
const selectedImageUploadId = ref('')
const isImageUploading = ref(false)
const currentTab = ref('chat')
const scrollTop = ref(0)
const scrollIntoViewTarget = ref('')

// 閺佹瑧绮屽Ο鈥崇础閻樿埖鈧?const coachCases = ref([])
const currentScenario = ref(null)
const isIntelOpen = ref(false)
const isIntelCollapsed = ref(false)
const selectedRegion = ref(null)
const selectedPersona = ref(null)
const coachEntryMode = ref('menu')
const coachQuizSession = ref(null)
const coachQuizLoading = ref(false)
const coachQuizError = ref('')

// 闁氨鐓℃稉搴ゎ啎缂冾喚濮搁幀?const showNoticeCenter = ref(false)
const noticeTab = ref('current')
const currentNotices = ref([])
const noticeHistory = ref([])
const noticesLoading = ref(false)
const hasUnreadNotices = ref(false)
const showSettings = ref(false)
const outputLength = ref(uni.getStorageSync('zyd_output_length') || 'medium')
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdLoading = ref(false)

// 鐢悂鍣洪柊宥囩枂
const POST_LOGIN_FRESH_CHAT_KEY = 'zyd_post_login_fresh_chat'
const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'
const coachRegions = [
	{ name: '缂囧骸娴楃痪?, short: 'US', desc: '闁插秷顫嬪ù閿嬫烦閵嗕線鍋栫紓鏍т焊鏉╂嚎鈧浇顓哥拹褰掑櫢闁插繗顫夐崚娆嶁偓? },
	{ name: '濞喲勫簥缁?, short: 'EU', desc: '闁插秷顫嬮柧浣规烦閵嗕箓AT 缁嬪骸褰块妴浣圭閸忓啿鎷板ú楣冣偓浣筋潐閸掓瑣鈧? },
]
const coachPersonas = [
	{ name: '鐞涘奔绗熺亸蹇曟', emoji: '棣冩', desc: '缁€鑹扮煀娴ｅ棔绗夐幊鍌濐攽閿涘矂娓剁憰浣风稑閻劋绗撴稉姘嫲閼版劕绺剧敮锔炬絻鐠ц埇鈧? },
	{ name: '濮圭喐绠归懓浣瑰', emoji: '棣冩', desc: '鐠囨繃婀抽懓浣虹矊閵嗕礁甯囨禒閿嬫閺勬拝绱濋弴纾嬧偓鍐崣鎼存洜娲忛崪灞藉灲閺傤厹鈧? },
]
const coachSubjects = [
	{ name: '閹躲儰鐜幏澶愭暜閹?, emoji: '棣冩尲', desc: '闂堛垹顕€广垺鍩涢崣宥咁槻閸樺鐜敍灞筋洤娴ｆ洖鐣ф担蹇撳焺濞戯妇鈹栭梻娣偓? },
	{ name: '瀵倸鐖剁痪鐘垫倣婢跺嫮鎮?, emoji: '棣冩礉', desc: '婢跺嫮鎮婇弻銉╃崣閵嗕焦濮囩拠澶堚偓浣虹壃閹圭喎鎷板鎯邦嚖缁涘绱撶敮鎼佹６妫版ǜ鈧? },
	{ name: '娑撴艾濮熼幒鎺楁祫', emoji: '棣冩敺', desc: '鐠囧棗鍩嗛梾鎰妞嬪酣娅撻妴浣规櫛閹扮喕鎻ｉ崪灞间繆閹垯绗夌€瑰本鏆ｇ拋銏犲礋閵? },
	{ name: '闁厧宕熸稉搴ｆ樊閹?, emoji: '棣冾檪', desc: '閹恒劏绻橀幋鎰唉閿涘苯鎮撻弮鍓佹樊閹镐礁顓归幋铚備繆娴犺绗岄懞鍌氼殧閵? },
]

// 鐠侊紕鐣荤仦鐐粹偓?const userInitial = computed(() => String(auth.userName || '閺?).trim().slice(0, 1).toUpperCase() || '閺?)
const displayNotices = computed(() => (noticeTab.value === 'history' ? noticeHistory.value : currentNotices.value))
const isCoachQuizView = computed(() => currentMode.value === 'coach' && coachEntryMode.value === 'quiz')
const currentCoachQuizQuestion = computed(() => {
	if (!coachQuizSession.value || coachQuizSession.value.completed) return null
	return coachQuizSession.value.questions[coachQuizSession.value.currentIndex] || null
})

// 閺傝纭?- 閸╄櫣顢呯粻锛勬倞
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
	if (tab === 'tools') { uni.showToast({ title: '瀹搞儱鍙挎稉顓炵妇瀵偓閸欐垳鑵?, icon: 'none' }); return; }
	currentTab.value = tab
	showNoticeCenter.value = false
	if (tab === 'admin') goToAdmin()
}

// 閺傝纭?- 鐎电鐦界粻锛勬倞
const startNewChat = ({ forceCreate = false } = {}) => {
	if (currentMode.value === 'coach') resetCoachState()
	if (!forceCreate && currentSessionId.value) {
		const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
		if (currentSession && (!currentSession.messages || currentSession.messages.length === 0)) {
			messages.value = []; inputMsg.value = ''; clearSelectedImage(); return
		}
	}
	const newSessionId = `${Date.now()}`
	sessions.value = [{ id: newSessionId, title: '閺傛澘顕拠?, messages: [] }, ...sessions.value].slice(0, 20)
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

// 閺傝纭?- 閸欐垿鈧椒绗屽ù浣哥础
let requestTask = null
const stopGeneration = () => { if (requestTask) requestTask.abort(); isGenerating.value = false; }

const sendMessage = async () => {
	const content = inputMsg.value.trim()
	if (!content && !selectedImage.value) return
	if (isGenerating.value) return
	if (selectedImage.value && isImageUploading.value) {
		uni.showToast({ title: '閸ュ墽澧栨禒宥呮躬娑撳﹣绱舵稉?, icon: 'none' }); return
	}

	const currentImageUploadId = selectedImageUploadId.value || null
	const currentImageBase64 = selectedImage.value && selectedImage.value.startsWith('data:')
		? selectedImage.value.split(',')[1] : null

    // 閺嬪嫬缂撶敮锕€浜告總鐣屾畱閸愬懎顔?    let finalContent = content
    if (outputLength.value === 'short') finalContent = `[鏉堟挸鍤崑蹇撱偨:閺嬩浇鍤х划鍓х暆] ${content}`
    else if (outputLength.value === 'long') finalContent = `[鏉堟挸鍤崑蹇撱偨:鐠囷箑鏁栫仦鏇炵磻] ${content}`

	messages.value.push({ id: `user-${Date.now()}`, role: 'user', content, image: selectedImage.value })
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

	try {
		await requestTask.start({
			onText: (text) => {
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
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg && !aiMsg.content) aiMsg.content = `鐠囬攱鐪版径杈Е閿?{error?.message || '缂冩垹绮跺鍌氱埗'}`
	} finally {
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) aiMsg.isTyping = false
		isGenerating.value = false; requestTask = null; saveSessions()
	}
}

// 閺傝纭?- 閺佹瑧绮岄柅鏄忕帆
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
		if (response.statusCode >= 400) throw new Error('閼惧嘲褰囨０妯兼窗婢惰精瑙?)
		const questions = response.data?.questions || []
		if (questions.length === 0) { coachQuizError.value = '閺嗗倹妫ら崣顖烆暯閻?; return }
		coachQuizSession.value = {
			currentIndex: 0, correctCount: 0, completed: false,
			questions: questions.map(q => ({ ...q, selectedAnswer: '', isCorrect: false }))
		}
	} catch (e) { coachQuizError.value = '閹朵粙顣芥径杈Е閿涘矁顕柌宥堢槸' } finally { coachQuizLoading.value = false }
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
	const matches = coachCases.value.filter(c => (c.category || '').includes(selectedRegion.value) && (c.category || '').includes(selectedPersona.value.replace('鐞涘奔绗?,'')))
	const randomCase = matches[Math.floor(Math.random() * matches.length)]
	currentScenario.value = randomCase || { name: `${selectedRegion.value} 璺?${subjectName}`, success_criteria: ['鐠囧棗鍩嗙€广垺鍩涚拠澶嬬湴', '缂佹瑥鍤稉鎾茬瑹閺傝顢?] }
	isIntelOpen.value = true; inputMsg.value = `閹存垼顩﹂幐鎴炲灛閵?{currentScenario.value.name}閵嗘垵婧€閺呯棎; sendMessage()
}

const requestCoachEvaluation = () => {
	if (isGenerating.value || messages.value.length === 0) return
	inputMsg.value = '閵嗘劗绮ㄩ弶鐔奉嚠缂佸啨鈧垼顕悳鏉挎躬閸掑洦宕叉稉琛♀偓婊嗙カ濞ｉ亶鏀㈤崬顔解偓鑽ゆ磧/闁叉垹澧濈€电厧绗€閳ユ繄娈戞禍楦款啎閿涘苯鐔€娴滃骸鍨伴幍宥囨畱閸忋劑鍎撮懕濠傘亯鐠佹澘缍嶆潏鎾冲毉缂佹挻鐎崠鏍仯鐠囧嫭濮ら崨濞库偓?
	sendMessage()
}

// 閺傝纭?- 闁氨鐓℃稉搴ゎ啎缂?const openNoticeCenter = async () => {
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

const previewNotice = (n) => uni.showModal({ title: '闁氨鐓＄拠锔藉剰', content: n.content, showCancel: false })

const submitChangePassword = async () => {
	const { oldPwd, newPwd, confirmPwd } = pwdForm.value
	if (!oldPwd || !newPwd || !confirmPwd) { uni.showToast({ title: '鐠囧嘲锝為崘娆忕暚閺?, icon: 'none' }); return }
	pwdLoading.value = true
	const res = await auth.changePassword(oldPwd, newPwd)
	pwdLoading.value = false
	if (res?.success) { uni.showToast({ title: '娣囶喗鏁奸幋鎰' }); closeSettings() }
	else uni.showToast({ title: res?.message || '婢惰精瑙?, icon: 'none' })
}

// 閸ュ墽澧栨潏鍛И
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
				// 闂勫秶楠囨担璺ㄦ暏 base64
				uni.getFileSystemManager().readFile({
					filePath, encoding: 'base64',
					success: ({ data }) => { selectedImage.value = buildImageDataUrl(filePath, data) }
				})
			} finally { isImageUploading.value = false }
		}
	})
}

// 閼奉亜濮╁姘З鏉堝懎濮?const scrollToBottom = () => {
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

// 閻㈢喎鎳￠崨銊︽埂
onMounted(() => {
	if (!auth.isAuthenticated) { uni.reLaunch({ url: '/pages/login/login' }); return }
	const shouldFresh = uni.getStorageSync(POST_LOGIN_FRESH_CHAT_KEY) === '1'
	if (shouldFresh) uni.removeStorageSync(POST_LOGIN_FRESH_CHAT_KEY)
	const initialMode = shouldFresh ? 'general' : (uni.getStorageSync(LAST_CHAT_MODE_KEY) || 'general')
	switchMode(initialMode)
	
	// 閸氬骸褰撮棃娆撶帛閸旂姾娴?	uni.request({ url: resolveApiUrl('/api/upload/coach-cases'), header: { Authorization: `Bearer ${auth.token}` }, success: r => coachCases.value = r.data || [] })
	uni.request({ url: resolveApiUrl('/api/settings/public'), success: r => welcomeMsg.value = r.data?.ai_welcome_message || welcomeMsg.value })
	uni.request({
		url: resolveApiUrl('/api/notices/current'), header: { Authorization: `Bearer ${auth.token}` },
		success: r => {
			const latestId = r.data?.[0]?.id; const seenId = uni.getStorageSync(NOTICE_SEEN_STORAGE_KEY)
			hasUnreadNotices.value = latestId && String(latestId) !== String(seenId)
		}
	})
})
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

.nav-left { width: 40px; }
.nav-btn-hamburg { background: transparent; border: none; font-size: 24px; padding: 0; }
.nav-right-spacer { width: 40px; }

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

/* 濡€崇础娑撳顣介懝?*/
.general-mode { --theme-color: #2563eb; }
.coach-mode { --theme-color: #059669; }
.expert-mode { --theme-color: #7c3aed; }
</style>

