<template>
	<!-- #ifdef H5 -->
	<view class="desktop-admin-shell-v2">
		<view class="desktop-admin-layout">
			<view class="desktop-admin-sidebar">
				<view class="brand-zone" @tap="navigateToHome">
					<image src="/static/logo.png" mode="aspectFit" class="desktop-logo" />
					<text class="desktop-brand-name">灏忔槗鏅鸿兘鍚庡彴</text>
				</view>

				<view class="sidebar-menu">
					<view
						v-for="entry in adminEntries"
						:key="entry.key"
						class="menu-item"
						:class="{ active: currentActiveTab === entry.key, disabled: !entry.enabled }"
						@tap="handleEntryTap(entry)"
					>
						<text class="menu-icon">{{ entry.icon }}</text>
						<text class="menu-label">{{ entry.title }}</text>
					</view>
				</view>

				<view class="sidebar-footer">
					<view class="user-pill-pc">
						<text class="user-pill-name-pc">{{ auth.userName }}</text>
                        <view class="logout-mini-pc" @tap="handleRouterLogout">退出</view>
					</view>
				</view>
			</view>

			<view class="desktop-admin-content">
				<view v-if="currentActiveTab === 'knowledge'" class="admin-panel knowledge-panel">
					<view class="panel-header">
						<view>
                            <text class="panel-title">业务知识库管理</text>
                            <text class="panel-subtitle">上传知识文档并同步到当前后端，不改动小易原有后端逻辑。</text>
						</view>
					</view>

					<view class="upload-sections">
						<view class="upload-card">
                            <text class="section-title">行政资料</text>
							<view class="drop-zone" @tap="triggerAdminSelect" @drop.prevent="handleAdminDrop" @dragover.prevent>
								<IconUpload size="32" color="#6366f1" />
                                <text>点击或拖拽上传文档</text>
								<input ref="adminInput" type="file" style="display:none" multiple @change="handleAdminSelected" />
							</view>
							<text v-if="adminMessage" class="upload-message">{{ adminMessage }}</text>
							<view class="file-list">
								<view v-for="file in uploadedAdmin" :key="file" class="file-item">
									<IconFileBox size="16" />
									<text class="filename">{{ file }}</text>
                                    <text class="delete-btn" @tap="deleteDoc(file)">删除</text>
								</view>
							</view>
						</view>

						<view class="upload-card">
                            <text class="section-title">业务资料</text>
							<view class="drop-zone" @tap="triggerBizSelect" @drop.prevent="handleBizDrop" @dragover.prevent>
								<IconUpload size="32" color="#10b981" />
                                <text>点击或拖拽上传文档</text>
								<input ref="bizInput" type="file" style="display:none" multiple @change="handleBizSelected" />
							</view>
							<text v-if="bizMessage" class="upload-message">{{ bizMessage }}</text>
							<view class="file-list">
								<view v-for="file in uploadedBiz" :key="file" class="file-item">
									<IconFileBox size="16" />
									<text class="filename">{{ file }}</text>
                                    <text class="delete-btn" @tap="deleteDoc(file)">删除</text>
								</view>
							</view>
						</view>
					</view>
				</view>

				<view v-else class="admin-panel placeholder-panel">
					<view class="info-alert">
                        <text>这个模块已迁移为独立管理页，入口仍复用原后端接口。</text>
                        <button class="go-detail-btn" @tap="navigateToCurrentTab">立即前往</button>
					</view>
				</view>
			</view>
		</view>
	</view>
	<!-- #endif -->

	<!-- #ifndef H5 -->
	<view class="mp-admin-page">
		<view class="admin-nav">
			<view class="nav-btn-circle" @tap="navigateToHome">
				<IconHome size="20" />
			</view>
			<text class="page-title">绠＄悊鍚庡彴</text>
			<view style="width: 72rpx;"></view>
		</view>

		<view class="mp-admin-hero">
			<view class="mp-admin-user-card">
				<view class="mp-admin-user-meta">
					<text class="mp-admin-user-name">{{ auth.userName }}</text>
					<text class="mp-admin-user-role">{{ auth.roleName }}</text>
				</view>
				<button class="mp-admin-logout-icon" @tap="handleRouterLogout">
					<IconLogOut size="20" color="#ef4444" />
				</button>
			</view>
		</view>

		<view class="mp-admin-entry-grid">
			<view
				v-for="entry in adminEntries"
				:key="entry.key"
				class="mp-entry-card"
				:class="{ disabled: !entry.enabled }"
				@tap="handleEntryTap(entry)"
			>
				<view class="mp-entry-icon-wrapper" :style="{ backgroundColor: entry.bgColor }">
					<text class="mp-entry-icon">{{ entry.icon }}</text>
				</view>
				<view class="mp-entry-text">
					<text class="mp-entry-title">{{ entry.title }}</text>
				</view>
				<text class="mp-entry-desc">{{ entry.desc }}</text>
			</view>
		</view>

		<view v-if="currentActiveTab === 'knowledge'" class="mp-knowledge-grid">
			<view class="mp-knowledge-subnav">
				<view
					v-for="section in knowledgeSections"
					:key="section.key"
					class="mp-knowledge-tab"
					:class="{ active: currentKnowledgeSection === section.key }"
					@tap="currentKnowledgeSection = section.key"
				>
					<text>{{ section.label }}</text>
				</view>
			</view>

			<view v-if="currentKnowledgeSection === 'admin'" class="mp-knowledge-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">行政资料</text>
					<button class="mp-knowledge-btn" :disabled="mpUploading" @tap="selectAndUploadDocument('admin')">
                        {{ mpUploading ? '上传中' : '上传文件' }}
					</button>
				</view>
				<text v-if="mpUploadMessage" class="mp-knowledge-meta">{{ mpUploadMessage }}</text>
				<text v-if="mpUploadCategory === 'admin' && mpUploadStage" class="mp-knowledge-meta subtle">
                    {{ mpUploadStage }}<text v-if="mpUploadProgress > 0"> · {{ mpUploadProgress }}%</text>
				</text>
                <view v-if="uploadedAdmin.length === 0" class="mp-knowledge-empty">暂无文件</view>
				<view v-for="file in uploadedAdmin" :key="`admin-${file}`" class="mp-knowledge-item">
					<text class="mp-knowledge-name">{{ file }}</text>
                    <text class="mp-knowledge-delete" @tap="deleteDoc(file)">删除</text>
				</view>
			</view>

			<view v-else-if="currentKnowledgeSection === 'biz'" class="mp-knowledge-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">业务资料</text>
					<button class="mp-knowledge-btn" :disabled="mpUploading" @tap="selectAndUploadDocument('biz')">
                        {{ mpUploading ? '上传中' : '上传文件' }}
					</button>
				</view>
				<text v-if="mpUploadMessage" class="mp-knowledge-meta">{{ mpUploadMessage }}</text>
				<text v-if="mpUploadCategory === 'biz' && mpUploadStage" class="mp-knowledge-meta subtle">
                    {{ mpUploadStage }}<text v-if="mpUploadProgress > 0"> · {{ mpUploadProgress }}%</text>
				</text>
                <view v-if="uploadedBiz.length === 0" class="mp-knowledge-empty">暂无文件</view>
				<view v-for="file in uploadedBiz" :key="`biz-${file}`" class="mp-knowledge-item">
					<text class="mp-knowledge-name">{{ file }}</text>
                    <text class="mp-knowledge-delete" @tap="deleteDoc(file)">删除</text>
				</view>
			</view>

			<view v-else-if="currentKnowledgeSection === 'quotes'" class="mp-knowledge-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">报价表</text>
					<button class="mp-knowledge-btn quote" :disabled="quoteUploading" @tap="selectAndUploadQuote">
                        {{ quoteUploading ? '上传中' : '更新报价' }}
					</button>
				</view>
				<text v-if="quoteMessage" class="mp-knowledge-meta">{{ quoteMessage }}</text>
				<text v-if="quoteStage" class="mp-knowledge-meta subtle">
                    {{ quoteStage }}<text v-if="quoteProgress > 0"> · {{ quoteProgress }}%</text>
				</text>
                <view v-if="uploadedQuotes.length === 0" class="mp-knowledge-empty">暂无报价表</view>
				<view v-for="file in uploadedQuotes" :key="`quote-${file}`" class="mp-knowledge-item">
					<text class="mp-knowledge-name">{{ file }}</text>
                    <text class="mp-knowledge-delete" @tap="deleteQuote(file)">删除</text>
				</view>
			</view>

			<view v-else-if="currentKnowledgeSection === 'cases'" class="mp-knowledge-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">教练案例</text>
					<button class="mp-knowledge-btn coach" :disabled="caseUploading" @tap="selectAndUploadCoachCase">
                        {{ caseUploading ? '分析中' : '上传案例' }}
					</button>
				</view>
				<text v-if="caseMessage" class="mp-knowledge-meta">{{ caseMessage }}</text>
				<text v-if="caseStage" class="mp-knowledge-meta subtle">
                    {{ caseStage }}<text v-if="caseProgress > 0"> · {{ caseProgress }}%</text>
				</text>
                <view v-if="coachCases.length === 0" class="mp-knowledge-empty">暂无案例</view>
				<view v-for="item in coachCases" :key="`case-${item.id}`" class="mp-knowledge-item stacked">
					<view class="mp-knowledge-stack">
                        <text class="mp-knowledge-name">{{ item.name || '未命名案例' }}</text>
                        <text class="mp-knowledge-caption">{{ item.category || '未分类' }}</text>
					</view>
                    <text class="mp-knowledge-delete" @tap="deleteCase(item.id)">删除</text>
				</view>
			</view>
			<view v-else-if="currentKnowledgeSection === 'quiz'" class="mp-knowledge-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">教练出题题库</text>
					<button class="mp-knowledge-btn coach" :disabled="quizUploading" @tap="selectAndUploadQuizBank">
                        {{ quizUploading ? '导入中' : '上传题库' }}
					</button>
				</view>
				<text v-if="quizMessage" class="mp-knowledge-meta">{{ quizMessage }}</text>
				<text v-if="quizStage" class="mp-knowledge-meta subtle">
                    {{ quizStage }}<text v-if="quizProgress > 0"> · {{ quizProgress }}%</text>
				</text>
                <view v-if="quizQuestions.length === 0" class="mp-knowledge-empty">暂无题目</view>
				<view v-for="item in quizQuestions" :key="`quiz-${item.id}`" class="mp-knowledge-item stacked">
					<view class="mp-knowledge-stack">
                        <text class="mp-knowledge-name">{{ item.question || '未命名题目' }}</text>
                        <text class="mp-knowledge-caption">{{ item.category || '未分类' }}</text>
					</view>
                    <text class="mp-knowledge-delete" @tap="deleteQuizQuestion(item.id)">删除</text>
				</view>
			</view>
		</view>

		<view v-else-if="currentActiveTab === 'notices'" class="mp-notice-panel">
			<view class="mp-notice-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">通知管理</text>
					<button class="mp-knowledge-btn notice" :disabled="noticeSending" @tap="sendNotice">
                        {{ noticeSending ? '发布中' : '发布通知' }}
					</button>
				</view>
				<textarea
					v-model="noticeContent"
					class="mp-notice-textarea"
					auto-height
					maxlength="-1"
                    placeholder="输入通知内容，发布后小程序通知中心会默认显示本周通知。"
				></textarea>
				<text v-if="noticeMessage" class="mp-knowledge-meta">{{ noticeMessage }}</text>
			</view>

			<view class="mp-notice-card">
				<view class="mp-knowledge-head">
                    <text class="mp-knowledge-title">历史通知</text>
					<button class="mp-notice-refresh" @tap="fetchNoticeHistory">鍒锋柊</button>
				</view>
                <view v-if="noticeHistory.length === 0" class="mp-knowledge-empty">暂无通知</view>
				<view v-for="notice in noticeHistory" :key="notice.id" class="mp-notice-history-item">
					<view class="mp-notice-history-content">
						<text class="mp-notice-history-date">{{ formatNoticeDate(notice.created_at) }}</text>
						<text class="mp-notice-history-text">{{ notice.content }}</text>
					</view>
                    <text class="mp-knowledge-delete" @tap="deleteNotice(notice.id)">删除</text>
				</view>
			</view>

		</view>

		<view class="mp-admin-footer">
			<text>漏 2026 浠叉槗杈鹃泦鍥?路 鍐呴儴绠＄悊绯荤粺</text>
		</view>
	</view>
	<!-- #endif -->
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import { resolveApiUrl } from '@/utils/api'
import { canAccessAdminSection, ensureAdminPageAccess } from '@/utils/admin-access'
import { useUploader } from '@/composables/useUploader'
import {
	FileBox as IconFileBox,
	Home as IconHome,
	LogOut as IconLogOut,
	UploadCloud as IconUpload,
} from 'lucide-vue-next'

const auth = useAuthStore()
const currentActiveTab = ref('knowledge')
const currentKnowledgeSection = ref('biz')
const knowledgeSections = [
	{ key: 'biz', label: '业务资料' },
	{ key: 'admin', label: '行政资料' },
	{ key: 'quotes', label: '报价表' },
	{ key: 'cases', label: '教练案例' },
]

knowledgeSections.push({ key: 'quiz', label: '教练出题题库' })

const adminEntries = computed(() => {
	const role = auth.user?.role || ''
	const permissions = auth.permissions

	return [
		{
			key: 'knowledge',
			title: '业务知识库',
			desc: '维护行政资料与业务知识文档',
			icon: '知',
			bgColor: '#E0F2FE',
			url: '',
			enabled: canAccessAdminSection('knowledge', role, { permissions }),
		},
		{
			key: 'notices',
			title: '通知管理',
			desc: '发布本周通知，并维护历史通知列表',
			icon: '铃',
			bgColor: '#FEE2E2',
			url: '',
			enabled: canAccessAdminSection('notices', role, { permissions }),
		},
		{
			key: 'lab',
			title: '小易实验室',
			desc: '调节核心参数，不改变后端逻辑',
			icon: '参',
			bgColor: '#EDE9FE',
			url: '/pages/admin/lab',
			enabled: canAccessAdminSection('lab', role, { permissions }),
		},
		{
			key: 'chat-logs',
			title: '会话审计',
			desc: '查看员工与小易的历史对话',
			icon: '记',
			bgColor: '#DCFCE7',
			url: '/pages/admin/chat-logs',
			enabled: canAccessAdminSection('chat-logs', role, { permissions }),
		},
		{
			key: 'staff',
			title: '账号管理',
			desc: '管理组织架构与员工账号',
			icon: '人',
			bgColor: '#FEF9C3',
			url: '/pages/admin/staff',
			enabled: canAccessAdminSection('staff', role, { permissions }),
		},
	]
})

const handleRouterLogout = () => {
	auth.logout()
}

const navigateToHome = () => {
	uni.reLaunch({ url: '/pages/chat/chat' })
}

const navigateToPage = (url) => {
	if (!url) return
	uni.navigateTo({ url })
}

const navigateToCurrentTab = () => {
	const entry = adminEntries.value.find((item) => item.key === currentActiveTab.value)
	if (entry?.url) {
		navigateToPage(entry.url)
	}
}

const syncDefaultAdminTab = () => {
	const activeEntry = adminEntries.value.find((item) => item.key === currentActiveTab.value && item.enabled)
	if (activeEntry) return

	const firstInlineEntry = adminEntries.value.find((item) => item.enabled && !item.url)
	currentActiveTab.value = firstInlineEntry?.key || ''
}

const handleEntryTap = (entry) => {
	if (!entry.enabled) {
		uni.showToast({ title: '当前账号无权访问该页面', icon: 'none' })
		return
	}

	if (entry.key === 'knowledge' || entry.key === 'notices') {
		currentActiveTab.value = entry.key
		return
	}

	navigateToPage(entry.url)
}

const BASE_URL = '/api/upload'
const uploadedAdmin = ref([])
const uploadedBiz = ref([])
const uploadedQuotes = ref([])
const coachCases = ref([])
const quizQuestions = ref([])
const mpUploading = ref(false)
const mpUploadMessage = ref('')
const mpUploadStage = ref('')
const mpUploadProgress = ref(0)
const mpUploadCategory = ref('')
const quoteUploading = ref(false)
const quoteMessage = ref('')
const quoteStage = ref('')
const quoteProgress = ref(0)
const caseUploading = ref(false)
const caseMessage = ref('')
const caseStage = ref('')
const caseProgress = ref(0)
const quizUploading = ref(false)
const quizMessage = ref('')
const quizStage = ref('')
const quizProgress = ref(0)
const noticeHistory = ref([])
const noticeContent = ref('')
const noticeSending = ref(false)
const noticeMessage = ref('')

const readToken = () => {
	try {
		return uni.getStorageSync('token')
	} catch (error) {
		return ''
	}
}

const requestUploadApi = async (path, options = {}) => {
	const url = resolveApiUrl(path)
	const method = options.method || 'GET'

	// #ifdef H5
	const response = await axios({
		url,
		method,
		params: options.params,
		data: options.data,
		headers: options.headers,
	})
	return response.data
	// #endif

	// #ifndef H5
	return await new Promise((resolve, reject) => {
		uni.request({
			url,
			method,
			data: options.params || options.data,
			header: {
				Authorization: readToken() ? `Bearer ${readToken()}` : '',
				...(options.headers || {}),
			},
			timeout: 15000,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
					return
				}
				reject(new Error(res.data?.detail || `request failed (${res.statusCode})`))
			},
			fail: reject,
		})
	})
	// #endif
}

const formatNoticeDate = (value) => {
	if (!value) return ''
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) return String(value)
	const year = date.getFullYear()
	const month = `${date.getMonth() + 1}`.padStart(2, '0')
	const day = `${date.getDate()}`.padStart(2, '0')
	const hours = `${date.getHours()}`.padStart(2, '0')
	const minutes = `${date.getMinutes()}`.padStart(2, '0')
	return `${year}-${month}-${day} ${hours}:${minutes}`
}

const fetchNoticeHistory = async () => {
	try {
		const notices = await requestUploadApi('/api/notices/history')
		noticeHistory.value = Array.isArray(notices) ? notices : []
	} catch (error) {
		console.error('Failed to fetch notices:', error)
		noticeHistory.value = []
	}
}

const sendNotice = async () => {
	const content = noticeContent.value.trim()
	if (!content || noticeSending.value) return

	noticeSending.value = true
	try {
		await requestUploadApi('/api/notices/', {
			method: 'POST',
			data: { content },
			headers: {
				'content-type': 'application/json',
			},
		})
		noticeContent.value = ''
		noticeMessage.value = '通知已发布'
		await fetchNoticeHistory()
		uni.showToast({ title: '通知已发布', icon: 'success' })
	} catch (error) {
		noticeMessage.value = error.message || '通知发布失败'
		uni.showToast({ title: noticeMessage.value, icon: 'none' })
	} finally {
		noticeSending.value = false
	}
}

const deleteNotice = async (noticeId) => {
	uni.showModal({
		 title: '删除通知',
		 content: '确定要删除这条通知吗？',
		success: async ({ confirm }) => {
			if (!confirm) return
			try {
				await requestUploadApi('/api/notices/' + encodeURIComponent(noticeId), { method: 'DELETE' })
				noticeMessage.value = '通知已删除'
				await fetchNoticeHistory()
			} catch (error) {
				uni.showToast({ title: error.message || '删除通知失败', icon: 'none' })
			}
		},
	})
}

const fetchUploadedDocs = async () => {
	try {
		const [adminFiles, bizFiles] = await Promise.all([
			requestUploadApi('/api/upload/documents', { params: { category: 'admin' } }),
			requestUploadApi('/api/upload/documents', { params: { category: 'biz' } }),
		])
		uploadedAdmin.value = adminFiles?.files || []
		uploadedBiz.value = bizFiles?.files || []
	} catch (error) {
		console.error('Failed to fetch documents:', error)
	}
}

const fetchUploadedQuotes = async () => {
	try {
		const quoteFiles = await requestUploadApi('/api/upload/quotes')
		uploadedQuotes.value = quoteFiles?.files || []
	} catch (error) {
		console.error('Failed to fetch quotes:', error)
	}
}

const fetchCoachCases = async () => {
	try {
		const caseData = await requestUploadApi('/api/upload/coach-cases')
		coachCases.value = Array.isArray(caseData) ? caseData : caseData?.cases || []
	} catch (error) {
		console.error('Failed to fetch coach cases:', error)
	}
}

const fetchQuizQuestions = async () => {
	try {
		const quizData = await requestUploadApi('/api/coach-quiz/bank')
		quizQuestions.value = Array.isArray(quizData?.questions) ? quizData.questions : []
	} catch (error) {
		console.error('Failed to fetch quiz questions:', error)
	}
}

const {
	message: adminMessage,
	inputRef: adminInput,
	onDrop: onDropAdmin,
	onSelected: onAdminSelected,
	triggerSelect: triggerAdminSelect,
	upload: uploadAdmin,
} = useUploader({
	url: `${BASE_URL}/document?category=admin&async_mode=true`,
	onSuccess: (count) => {
		fetchUploadedDocs()
        return `成功处理 ${count} 份行政资料`
	},
	onError: (count, errors) => {
		fetchUploadedDocs()
        return `处理完成，成功 ${count}，失败 ${errors.length}`
	},
})

const {
	message: bizMessage,
	inputRef: bizInput,
	onDrop: onDropBiz,
	onSelected: onBizSelected,
	triggerSelect: triggerBizSelect,
	upload: uploadBiz,
} = useUploader({
	url: `${BASE_URL}/document?category=biz&async_mode=true`,
	onSuccess: (count) => {
		fetchUploadedDocs()
        return `成功处理 ${count} 份业务资料`
	},
	onError: (count, errors) => {
		fetchUploadedDocs()
        return `处理完成，成功 ${count}，失败 ${errors.length}`
	},
})

const handleAdminSelected = async (event) => {
	onAdminSelected(event)
	await uploadAdmin()
}

const handleBizSelected = async (event) => {
	onBizSelected(event)
	await uploadBiz()
}

const handleAdminDrop = async (event) => {
	onDropAdmin(event)
	await uploadAdmin()
}

const handleBizDrop = async (event) => {
	onDropBiz(event)
	await uploadBiz()
}

const deleteDoc = async (filename) => {
	// #ifdef H5
    const confirmed = window.confirm('确定要删除 ' + filename + ' 吗？')
	if (!confirmed) return

	try {
		await requestUploadApi('/api/upload/document/' + encodeURIComponent(filename), { method: 'DELETE' })
		await fetchUploadedDocs()
	} catch (error) {
        window.alert(error.response?.data?.detail || error.message || '删除失败')
	}
	// #endif

	// #ifndef H5
	uni.showModal({
		 title: '删除文件',
		content: '确定要删除 ' + filename + ' 吗？',
		success: async ({ confirm }) => {
			if (!confirm) return
			try {
				await requestUploadApi('/api/upload/document/' + encodeURIComponent(filename), { method: 'DELETE' })
				mpUploadMessage.value = filename + ' 已删除'
				await fetchUploadedDocs()
			} catch (error) {
				uni.showToast({ title: error.message || '删除失败', icon: 'none' })
			}
		},
	})
	// #endif
}

const deleteQuote = async (filename) => {
	uni.showModal({
        title: '删除报价表',
        content: '确定要删除 ' + filename + ' 吗？',
		success: async ({ confirm }) => {
			if (!confirm) return
			try {
				await requestUploadApi('/api/upload/quote/' + encodeURIComponent(filename), { method: 'DELETE' })
                quoteMessage.value = filename + ' 已删除'
				await fetchUploadedQuotes()
			} catch (error) {
                uni.showToast({ title: error.message || '删除失败', icon: 'none' })
			}
		},
	})
}

const deleteCase = async (caseId) => {
	uni.showModal({
		title: '删除教练案例',
		content: '确定要删除这个案例吗？',
		success: async ({ confirm }) => {
			if (!confirm) return
			try {
				await requestUploadApi('/api/upload/coach-case/' + encodeURIComponent(caseId), { method: 'DELETE' })
				caseMessage.value = '案例已删除'
				await fetchCoachCases()
			} catch (error) {
				uni.showToast({ title: error.message || '删除失败', icon: 'none' })
			}
		},
	})
}

const deleteQuizQuestion = async (questionId) => {
	uni.showModal({
		 title: '删除题目',
		 content: '确定要删除这道题吗？',
		success: async ({ confirm }) => {
			if (!confirm) return
			try {
				await requestUploadApi('/api/coach-quiz/bank/' + encodeURIComponent(questionId), { method: 'DELETE' })
				quizMessage.value = '题目已删除'
				await fetchQuizQuestions()
			} catch (error) {
				uni.showToast({ title: error.message || '删除失败', icon: 'none' })
			}
		},
	})
}

const pollUploadTask = async (taskId) => {
	for (let attempt = 0; attempt < 180; attempt += 1) {
		const task = await requestUploadApi('/api/upload/tasks/' + encodeURIComponent(taskId))
		mpUploadStage.value = task.message || task.stage || '正在处理'
		if (task.status === 'success') return task
		if (task.status === 'error') throw new Error(task.error || task.message || 'upload failed')
		await new Promise((resolve) => setTimeout(resolve, 1200))
	}
	throw new Error('upload task timed out')
}

const selectAndUploadDocument = async (category) => {
	// #ifdef H5
	return
	// #endif

	// #ifndef H5
	if (mpUploading.value) return

	try {
		const chooseResult = await new Promise((resolve, reject) => {
			uni.chooseMessageFile({
				count: 1,
				type: 'file',
				success: resolve,
				fail: reject,
			})
		})

		const targetFile = chooseResult.tempFiles?.[0]
		if (!targetFile?.path) return

		mpUploading.value = true
		mpUploadCategory.value = category
		mpUploadStage.value = '正在上传'
		mpUploadProgress.value = 0
		mpUploadMessage.value = (targetFile.name || '文件') + ' 上传中'

		const uploadResult = await new Promise((resolve, reject) => {
			const uploadTask = uni.uploadFile({
				url: resolveApiUrl('/api/upload/document') + '?category=' + encodeURIComponent(category) + '&async_mode=true',
				filePath: targetFile.path,
				name: 'file',
				header: readToken() ? { Authorization: `Bearer ${readToken()}` } : {},
				success: resolve,
				fail: reject,
			})
			if (uploadTask && typeof uploadTask.onProgressUpdate === 'function') {
				uploadTask.onProgressUpdate((progressEvent) => {
					mpUploadProgress.value = Number(progressEvent.progress || 0)
					mpUploadStage.value = progressEvent.progress >= 100 ? '文件已上传，等待后端处理' : '正在上传'
				})
			}
		})

		const payload = JSON.parse(uploadResult.data || '{}')
		if (!payload.task_id) {
			throw new Error(payload.detail || payload.message || 'missing task id')
		}

		mpUploadMessage.value = (targetFile.name || '文件') + ' 正在处理'
		const task = await pollUploadTask(payload.task_id)
		mpUploadProgress.value = 100
		mpUploadStage.value = '处理完成'
		mpUploadMessage.value = task.message || ((targetFile.name || '文件') + ' 处理完成')
		await fetchUploadedDocs()
		uni.showToast({ title: '上传完成', icon: 'success' })
	} catch (error) {
		console.error('Failed to upload document in mp:', error)
		mpUploadMessage.value = error.message || '上传失败'
		mpUploadStage.value = '处理失败'
		uni.showToast({ title: mpUploadMessage.value, icon: 'none' })
	} finally {
		mpUploading.value = false
	}
	// #endif
}

const uploadSingleFile = async ({ chooseType, uploadUrl, title, successMessageRef, stageRef, progressRef, loadingRef, afterSuccess }) => {
	if (loadingRef.value) return

	try {
		const chooseResult = await new Promise((resolve, reject) => {
			uni.chooseMessageFile({
				count: 1,
				type: chooseType,
				success: resolve,
				fail: reject,
			})
		})

		const targetFile = chooseResult.tempFiles?.[0]
		if (!targetFile?.path) return

		loadingRef.value = true
		progressRef.value = 0
		stageRef.value = '正在上传'
		successMessageRef.value = (targetFile.name || title) + ' 上传中'

		const uploadResult = await new Promise((resolve, reject) => {
			const uploadTask = uni.uploadFile({
				url: resolveApiUrl(uploadUrl),
				filePath: targetFile.path,
				name: 'file',
				header: readToken() ? { Authorization: `Bearer ${readToken()}` } : {},
				success: resolve,
				fail: reject,
			})
			if (uploadTask && typeof uploadTask.onProgressUpdate === 'function') {
				uploadTask.onProgressUpdate((progressEvent) => {
					progressRef.value = Number(progressEvent.progress || 0)
					stageRef.value = progressEvent.progress >= 100 ? '文件已上传，等待服务端处理' : '正在上传'
				})
			}
		})

		const payload = JSON.parse(uploadResult.data || '{}')
		progressRef.value = 100
		stageRef.value = '处理完成'
		successMessageRef.value = payload.message || ((targetFile.name || title) + ' 处理完成')
		if (afterSuccess) {
			await afterSuccess(payload)
		}
		uni.showToast({ title: '上传完成', icon: 'success' })
	} catch (error) {
		stageRef.value = '处理失败'
		successMessageRef.value = error.message || (title + ' 上传失败')
		uni.showToast({ title: successMessageRef.value, icon: 'none' })
	} finally {
		loadingRef.value = false
	}
}

const selectAndUploadQuote = async () => {
	await uploadSingleFile({
		chooseType: 'file',
		uploadUrl: '/api/upload/quote',
		title: '报价表',
		successMessageRef: quoteMessage,
		stageRef: quoteStage,
		progressRef: quoteProgress,
		loadingRef: quoteUploading,
		afterSuccess: async () => {
			await fetchUploadedQuotes()
		},
	})
}

const selectAndUploadCoachCase = async () => {
	await uploadSingleFile({
		chooseType: 'file',
		uploadUrl: '/api/upload/coach-case',
		title: '案例文件',
		successMessageRef: caseMessage,
		stageRef: caseStage,
		progressRef: caseProgress,
		loadingRef: caseUploading,
		afterSuccess: async (payload) => {
			caseMessage.value = payload.note ? String(payload.note) : (payload.processed_count !== undefined ? ('成功生成 ' + payload.processed_count + ' 条案例') : caseMessage.value)
			await fetchCoachCases()
		},
	})
}

const selectAndUploadQuizBank = async () => {
	await uploadSingleFile({
		chooseType: 'file',
		uploadUrl: '/api/coach-quiz/bank',
		title: '题库文件',
		successMessageRef: quizMessage,
		stageRef: quizStage,
		progressRef: quizProgress,
		loadingRef: quizUploading,
		afterSuccess: async (payload) => {
			quizMessage.value = payload.imported_count !== undefined
			? ('成功导入 ' + payload.imported_count + ' 道题')
				: quizMessage.value
			await fetchQuizQuestions()
		},
	})
}

onMounted(() => {
	ensureAdminPageAccess('admin', { role: auth.user?.role || '', permissions: auth.permissions })
	syncDefaultAdminTab()
	fetchUploadedDocs()
	fetchUploadedQuotes()
	fetchCoachCases()
	fetchQuizQuestions()
	fetchNoticeHistory()
})
</script>

<style scoped>
.mp-admin-page {
	min-height: 100vh;
	padding: 0 40rpx 40rpx;
	padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	background: #f8fafc;
}

.admin-nav {
	padding: calc(20rpx + env(safe-area-inset-top)) 0 40rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.nav-btn-circle {
	width: 72rpx;
	height: 72rpx;
	background: #ffffff;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.page-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1e293b;
}

.mp-admin-user-card {
	background: #ffffff;
	border-radius: 40rpx;
	padding: 48rpx 40rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.04);
	margin-bottom: 48rpx;
	border: 1px solid rgba(0, 0, 0, 0.02);
}

.mp-admin-user-meta {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.mp-admin-user-name {
	font-size: 40rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-admin-user-role {
	font-size: 24rpx;
	color: #64748b;
}

.mp-admin-logout-icon {
	width: 88rpx;
	height: 88rpx;
	border-radius: 50%;
	background: #fef2f2;
	display: flex;
	align-items: center;
	justify-content: center;
}

.mp-admin-entry-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 32rpx;
	margin-bottom: 32rpx;
}

.mp-entry-card {
	background: #ffffff;
	border-radius: 48rpx;
	padding: 48rpx 32rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.04);
	border: 1px solid rgba(0, 0, 0, 0.02);
}

.mp-entry-card.disabled {
	opacity: 0.5;
	filter: grayscale(1);
}

.mp-entry-icon-wrapper {
	width: 96rpx;
	height: 96rpx;
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 32rpx;
}

.mp-entry-icon {
	font-size: 40rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-entry-text {
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 12rpx;
}

.mp-entry-title {
	font-size: 30rpx;
	font-weight: 600;
	color: #1e293b;
}

.mp-entry-desc {
	font-size: 24rpx;
	color: #64748b;
	line-height: 1.4;
	text-align: center;
}

.mp-admin-footer {
	margin-top: auto;
	padding: 64rpx 0;
	text-align: center;
	font-size: 22rpx;
	color: #94a3b8;
}

.mp-knowledge-grid {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.mp-knowledge-subnav {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-bottom: 8rpx;
}

.mp-knowledge-tab {
	padding: 16rpx 28rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.72);
	color: #64748b;
	font-size: 24rpx;
	font-weight: 600;
	border: 1px solid rgba(148, 163, 184, 0.18);
}

.mp-knowledge-tab.active {
	background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
	color: #1d4ed8;
	border-color: rgba(37, 99, 235, 0.16);
	box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.08);
}

.mp-knowledge-card {
	background: #ffffff;
	border-radius: 36rpx;
	padding: 28rpx;
	box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.04);
	border: 1px solid rgba(0, 0, 0, 0.02);
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.mp-notice-panel {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.mp-notice-card {
	background: #ffffff;
	border-radius: 36rpx;
	padding: 28rpx;
	box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.04);
	border: 1px solid rgba(0, 0, 0, 0.02);
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.mp-notice-textarea {
	width: 100%;
	min-height: 220rpx;
	padding: 24rpx;
	box-sizing: border-box;
	border-radius: 24rpx;
	background: #f8fafc;
	font-size: 28rpx;
	line-height: 1.6;
	color: #0f172a;
}

.mp-knowledge-btn.notice {
	background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
}

.mp-notice-refresh {
	margin: 0;
	padding: 0 22rpx;
	height: 60rpx;
	line-height: 60rpx;
	border-radius: 999rpx;
	background: rgba(15, 23, 42, 0.08);
	color: #334155;
	font-size: 22rpx;
}

.mp-notice-refresh::after {
	border: none;
}

.mp-notice-history-item {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 16rpx;
	padding: 22rpx 24rpx;
	border-radius: 24rpx;
	background: #f8fafc;
}

.mp-notice-history-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.mp-notice-history-date {
	font-size: 22rpx;
	color: #94a3b8;
}

.mp-notice-history-text {
	font-size: 26rpx;
	line-height: 1.6;
	color: #0f172a;
	white-space: pre-wrap;
	word-break: break-word;
}

.mp-knowledge-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
}

.mp-knowledge-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-knowledge-btn {
	margin: 0;
	height: 68rpx;
	line-height: 68rpx;
	padding: 0 24rpx;
	border-radius: 999rpx;
	background: #2563eb;
	color: #ffffff;
	font-size: 24rpx;
}

.mp-knowledge-btn.quote {
	background: #7c3aed;
}

.mp-knowledge-btn.coach {
	background: #059669;
}

.mp-knowledge-btn::after {
	border: none;
}

.mp-knowledge-meta,
.mp-knowledge-empty {
	font-size: 24rpx;
	color: #64748b;
}

.mp-knowledge-meta.subtle {
	color: #94a3b8;
}

.mp-knowledge-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12rpx;
	padding: 18rpx 20rpx;
	border-radius: 20rpx;
	background: #f8fafc;
}

.mp-knowledge-item.stacked {
	align-items: flex-start;
}

.mp-knowledge-name {
	flex: 1;
	font-size: 24rpx;
	color: #0f172a;
}

.mp-knowledge-stack {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.mp-knowledge-caption {
	font-size: 22rpx;
	color: #64748b;
}

.mp-knowledge-delete {
	font-size: 24rpx;
	color: #dc2626;
}

.desktop-admin-shell-v2 {
	display: none;
}

/* #ifdef H5 */
@media screen and (min-width: 769px) {
	.desktop-admin-shell-v2 {
		display: block;
	}
}

.desktop-admin-layout {
	display: flex;
	height: 100vh;
	width: 100vw;
	background: #f8fafc;
	overflow: hidden;
}

.desktop-admin-sidebar {
	width: 280px;
	height: 100%;
	background: #ffffff;
	border-right: 1px solid rgba(0, 0, 0, 0.05);
	display: flex;
	flex-direction: column;
	flex-shrink: 0;
}

.brand-zone {
	padding: 32px 24px;
	display: flex;
	align-items: center;
	gap: 12px;
	cursor: pointer;
}

.desktop-logo {
	width: 32px;
	height: 32px;
}

.desktop-brand-name {
	font-size: 18px;
	font-weight: 800;
	color: #0f172a;
}

.sidebar-menu {
	flex: 1;
	padding: 0 16px;
}

.menu-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 16px;
	margin-bottom: 8px;
	border-radius: 12px;
	cursor: pointer;
	transition: all 0.2s;
	color: #64748b;
}

.menu-item.active {
	background: #f1f5f9;
	color: #0f172a;
	font-weight: 700;
}

.menu-item.disabled {
	opacity: 0.5;
	cursor: not-allowed;
}

.desktop-admin-content {
	flex: 1;
	height: 100%;
	overflow-y: auto;
	padding: 48px;
}

.panel-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.panel-title {
	display: block;
	font-size: 28px;
	font-weight: 800;
	color: #0f172a;
}

.panel-subtitle {
	display: block;
	margin-top: 8px;
	font-size: 14px;
	color: #64748b;
}

.upload-sections {
	display: flex;
	gap: 32px;
	margin-top: 32px;
}

.upload-card {
	flex: 1;
	background: #ffffff;
	border-radius: 24px;
	padding: 32px;
	border: 1px solid rgba(0, 0, 0, 0.03);
	box-shadow: 0 4px 24px rgba(0, 0, 0, 0.02);
}

.section-title {
	display: block;
	margin-bottom: 16px;
	font-size: 18px;
	font-weight: 700;
	color: #0f172a;
}

.drop-zone {
	height: 160px;
	border: 2px dashed #e2e8f0;
	border-radius: 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	cursor: pointer;
	color: #94a3b8;
	font-size: 14px;
}

.drop-zone:hover {
	border-color: #6366f1;
	background: #f5f3ff;
}

.upload-message {
	display: block;
	margin: 16px 0 8px;
	font-size: 13px;
	color: #475569;
}

.file-list {
	margin-top: 16px;
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.file-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 12px;
	border-radius: 8px;
	background: #f8fafc;
}

.filename {
	flex: 1;
	font-size: 13px;
	color: #0f172a;
}

.delete-btn {
	font-size: 12px;
	color: #ef4444;
	cursor: pointer;
}

.placeholder-panel {
	background: #ffffff;
	border-radius: 24px;
	padding: 32px;
}

.info-alert {
	display: flex;
	flex-direction: column;
	gap: 16px;
	align-items: flex-start;
}

.go-detail-btn {
	padding: 12px 24px;
	border-radius: 999px;
	background: #0f172a;
	color: #ffffff;
	font-size: 14px;
}

.sidebar-footer {
	padding: 24px;
	border-top: 1px solid rgba(0, 0, 0, 0.03);
}

.user-pill-pc {
	background: #f1f5f9;
	padding: 12px 16px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.user-pill-name-pc {
	font-size: 13px;
	font-weight: 600;
	color: #0f172a;
}

.logout-mini-pc {
	font-size: 11px;
	color: #ef4444;
	cursor: pointer;
}
/* #endif */
</style>
