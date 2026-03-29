<template>
	<!-- #ifdef H5 -->
	<view class="logs-container">
		<view class="logs-header">
			<view class="header-main">
				<view class="mp-title-wrap">
					<text class="mp-title">会话审计</text>
					<text class="mp-subtitle">保持原后端查询接口不变，查看员工与小易的历史对话。</text>
				</view>
				<button class="mp-back-btn" @tap="goBackToAdmin">返回管理大厅</button>
			</view>
		</view>

		<view class="logs-layout">
			<view class="user-sidebar">
				<view class="sidebar-header">
					<text>员工列表</text>
					<text class="count-badge">{{ userStats.length }} 人</text>
				</view>
				<view class="user-list">
					<view class="user-item" :class="{ active: selectedUserId === null }" @tap="selectUser(null)">
						<text>全部记录</text>
					</view>
					<view
						v-for="stat in userStats"
						:key="stat.user_id ?? `h5-anonymous-${stat.username}`"
						class="user-item"
						:class="{ active: selectedUserId === stat.user_id }"
						@tap="selectUser(stat.user_id)"
					>
						<text class="user-name">{{ stat.username }}</text>
						<text class="user-last-active">最后活跃：{{ formatDate(stat.last_active) }}</text>
					</view>
				</view>
			</view>

			<view class="logs-main-content">
				<view class="toolbar">
					<view class="mp-search-card">
						<input
							v-model="searchQuery"
							type="text"
							placeholder="搜索员工姓名或对话关键字"
							confirm-type="search"
							@confirm="fetchLogs(0)"
							class="mp-search-input"
						/>
						<button class="mp-search-btn" :disabled="loading" @tap="fetchLogs(0)">搜索</button>
					</view>
				</view>

				<view class="mp-filter-summary">
					<text class="mp-summary-text">{{ currentFilterSummary }}</text>
					<text class="mp-summary-text">当前第 {{ currentPage + 1 }} 页</text>
				</view>

				<view class="logs-scroller">
					<view v-if="loading" class="mp-state-card">
						<text class="mp-state-title">记录加载中</text>
						<text class="mp-state-hint">正在读取会话存档。</text>
					</view>
					<view v-else-if="errorMsg" class="mp-state-card error">
						<text class="mp-state-title">获取记录失败</text>
						<text class="mp-state-hint">{{ errorMsg }}</text>
					</view>
					<view v-else-if="logs.length === 0" class="mp-state-card">
						<text class="mp-state-title">{{ emptyStateTitle }}</text>
						<text class="mp-state-hint">{{ emptyStateHint }}</text>
					</view>

					<view v-for="log in logs" :key="log.id" class="mp-log-card">
						<view class="mp-log-meta">
							<view class="user-info">
								<text class="mp-log-user">{{ log.username || 'Anonymous' }}</text>
								<text v-if="log.processing_time" class="mp-log-extra">({{ Number(log.processing_time).toFixed(2) }}s)</text>
							</view>
							<text class="mp-log-time">{{ formatDateTime(log.created_at) }}</text>
						</view>

						<view class="mp-bubble user">
							<text class="mp-bubble-label">员工</text>
							<text class="mp-bubble-text">{{ log.user_message }}</text>
						</view>

						<view class="mp-bubble assistant">
							<text class="mp-bubble-label">小易</text>
							<view class="mp-bubble-rich" v-html="formatOutput(log.ai_response)"></view>
						</view>
					</view>
				</view>

				<view class="mp-pagination-bar">
					<button class="mp-page-btn ghost" :disabled="currentPage === 0 || loading" @tap="fetchLogs(currentPage - 1)">上一页</button>
					<button class="mp-page-btn" :disabled="logs.length < limit || loading" @tap="fetchLogs(currentPage + 1)">下一页</button>
				</view>
			</view>
		</view>
	</view>
	<!-- #endif -->

	<!-- #ifndef H5 -->
	<view class="mp-logs-page">
		<view class="admin-nav">
			<view class="nav-btn-circle" @tap="goBack">
				<IconChevronLeft size="20" />
			</view>
			<text class="page-title">会话审计</text>
			<view style="width: 72rpx;"></view>
		</view>

		<view class="mp-hero">
			<view class="mp-search-card">
				<input
					v-model="searchQuery"
					type="text"
					placeholder="搜索员工姓名或对话关键字"
					confirm-type="search"
					@confirm="fetchLogs(0)"
					class="mp-search-input"
				/>
				<button class="mp-search-btn" :disabled="loading" @tap="fetchLogs(0)">搜索</button>
			</view>
		</view>

		<scroll-view scroll-x class="mp-user-strip">
			<view class="mp-user-row">
				<view class="mp-user-chip" :class="{ active: selectedUserId === null }" @tap="selectUser(null)">
					<text class="mp-user-chip-name">全部员工</text>
				</view>
				<view
					v-for="stat in userStats"
					:key="stat.user_id ?? `mp-anonymous-${stat.username}`"
					class="mp-user-chip"
					:class="{ active: selectedUserId === stat.user_id }"
					@tap="selectUser(stat.user_id)"
				>
					<text class="mp-user-chip-name">{{ stat.username }}</text>
					<text class="mp-user-chip-meta">{{ stat.message_count }} 条记录</text>
				</view>
			</view>
		</scroll-view>

		<view class="mp-filter-summary">
			<text class="mp-summary-text">{{ currentFilterSummary }}</text>
			<text class="mp-summary-text">当前第 {{ currentPage + 1 }} 页</text>
		</view>

		<scroll-view scroll-y class="mp-log-list">
			<view v-if="loading" class="mp-state-card">
				<text class="mp-state-title">记录拉取中</text>
				<text class="mp-state-hint">正在从服务器读取会话存档。</text>
			</view>
			<view v-else-if="errorMsg" class="mp-state-card error">
				<text class="mp-state-title">获取记录失败</text>
				<text class="mp-state-hint">{{ errorMsg }}</text>
			</view>
			<view v-else-if="logs.length === 0" class="mp-state-card">
				<text class="mp-state-title">{{ emptyStateTitle }}</text>
				<text class="mp-state-hint">{{ emptyStateHint }}</text>
			</view>

			<view v-for="log in logs" :key="log.id" class="mp-log-card">
				<view class="mp-log-meta">
					<view class="user-info">
						<text class="mp-log-user">{{ log.username || '匿名用户' }}</text>
						<text v-if="log.processing_time" class="mp-log-extra">({{ Number(log.processing_time).toFixed(2) }}s)</text>
					</view>
					<text class="mp-log-time">{{ formatDateTime(log.created_at) }}</text>
				</view>

				<view class="mp-bubble user">
					<text class="mp-bubble-label">员工</text>
					<text class="mp-bubble-text">{{ log.user_message }}</text>
				</view>

				<view class="mp-bubble assistant">
					<text class="mp-bubble-label">小易</text>
					<text class="mp-bubble-text">{{ log.ai_response }}</text>
				</view>
			</view>
		</scroll-view>

		<view class="mp-pagination-bar">
			<button class="mp-page-btn ghost" :disabled="currentPage === 0 || loading" @tap="fetchLogs(currentPage - 1)">上一页</button>
			<button class="mp-page-btn" :disabled="logs.length < limit || loading" @tap="fetchLogs(currentPage + 1)">下一页</button>
		</view>
	</view>
	<!-- #endif -->
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { resolveApiUrl } from '@/utils/api'
import { ensureAdminPageAccess } from '@/utils/admin-access'
import { useAuthStore } from '@/store/auth'
import { renderMarkdown } from '@/utils/markdown'
import { ChevronLeft as IconChevronLeft } from 'lucide-vue-next'

const auth = useAuthStore()
const logs = ref([])
const userStats = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedUserId = ref(null)
const currentPage = ref(0)
const errorMsg = ref('')
const limit = 20
const isMpEnv = typeof window === 'undefined'

const currentFilterSummary = computed(() => {
	const activeUser = userStats.value.find((stat) => stat.user_id === selectedUserId.value)
	const userLabel = activeUser ? activeUser.username : '全部记录'
	const keyword = searchQuery.value.trim()
	return keyword ? `${userLabel} · 关键词“${keyword}”` : userLabel
})

const canViewLogs = computed(() => auth.isSuperAdmin || auth.hasPermission('view_logs'))
const emptyStateTitle = computed(() => (canViewLogs.value ? '暂无相关记录' : '当前账号无权查看'))
const emptyStateHint = computed(() => {
	if (!canViewLogs.value) {
		return '当前账号没有会话审计权限，请联系老板或管理员分配 view_logs 权限。'
	}
	return '请尝试更换筛选条件或关键字。'
})

const goBack = () => {
	const pages = getCurrentPages()
	if (pages.length > 1) {
		uni.navigateBack({ delta: 1 })
		return
	}
	uni.navigateTo({ url: '/pages/admin/admin' })
}

const goBackToAdmin = () => {
	const pages = getCurrentPages()
	if (pages.length > 1) {
		uni.navigateBack({ delta: 1 })
		return
	}
	uni.navigateTo({ url: '/pages/admin/admin' })
}

const readToken = () => {
	try {
		return uni.getStorageSync('token')
	} catch (error) {
		return ''
	}
}

const getRequestHeaders = () => {
	const token = readToken()
	return token ? { Authorization: `Bearer ${token}` } : {}
}

const requestAdminLogs = async (path, options = {}) => {
	const url = resolveApiUrl(path)
	const method = options.method || 'GET'
	const headers = {
		...getRequestHeaders(),
		...(options.headers || {}),
	}

	// #ifdef H5
	const response = await axios({
		url,
		method,
		params: options.params,
		data: options.data,
		headers,
	})
	return response.data
	// #endif

	// #ifndef H5
	return await new Promise((resolve, reject) => {
		uni.request({
			url,
			method,
			data: options.params || options.data,
			header: headers,
			timeout: 15000,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
					return
				}
				const detail = res.data && typeof res.data === 'object' ? res.data.detail : ''
				reject(new Error(detail || `请求失败 (${res.statusCode})`))
			},
			fail: (error) => reject(error),
		})
	})
	// #endif
}

const handleRequestError = (error, fallbackMessage) => {
	console.error(fallbackMessage, error)
	errorMsg.value = error?.response?.data?.detail || error?.message || fallbackMessage
	if (isMpEnv) {
		uni.showToast({
			title: errorMsg.value,
			icon: 'none',
			duration: 2200,
		})
	}
}

const fetchUserStats = async () => {
	try {
		const data = await requestAdminLogs('/api/admin/chat-logs/users')
		userStats.value = Array.isArray(data) ? data : []
	} catch (error) {
		userStats.value = []
		handleRequestError(error, '无法加载员工列表')
	}
}

const fetchLogs = async (page = 0) => {
	loading.value = true
	errorMsg.value = ''
	try {
		const data = await requestAdminLogs('/api/admin/chat-logs', {
			params: {
				skip: page * limit,
				limit,
				user_id: selectedUserId.value === null ? undefined : selectedUserId.value,
				search: searchQuery.value.trim() || undefined,
			},
		})
		logs.value = Array.isArray(data) ? data : []
		currentPage.value = page
	} catch (error) {
		logs.value = []
		handleRequestError(error, '无法加载会话记录')
	} finally {
		loading.value = false
	}
}

const selectUser = (userId) => {
	selectedUserId.value = userId
	fetchLogs(0)
}

const parseAuditDate = (dateInput) => {
	if (!dateInput) return null
	if (dateInput instanceof Date) {
		return Number.isNaN(dateInput.getTime()) ? null : dateInput
	}
	const raw = String(dateInput).trim()
	if (!raw) return null
	const normalized = raw.replace(' ', 'T')
	const hasTimezone = /([zZ]|[+\-]\d{2}:\d{2})$/.test(normalized)
	const candidate = hasTimezone ? normalized : `${normalized}Z`
	const date = new Date(candidate)
	if (!Number.isNaN(date.getTime())) return date
	const fallback = new Date(raw)
	return Number.isNaN(fallback.getTime()) ? null : fallback
}

const formatDate = (dateStr) => {
	if (!dateStr) return '--'
	const date = parseAuditDate(dateStr)
	if (!date) return '--'
	return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const formatDateTime = (dateStr) => {
	if (!dateStr) return '--'
	const date = parseAuditDate(dateStr)
	if (!date) return '--'
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	const hours = String(date.getHours()).padStart(2, '0')
	const minutes = String(date.getMinutes()).padStart(2, '0')
	return `${year}-${month}-${day} ${hours}:${minutes}`
}

const formatOutput = (text) => {
	// #ifdef H5
	return renderMarkdown(text || '')
	// #endif
	return text || ''
}

onMounted(() => {
	if (!ensureAdminPageAccess('chat-logs')) {
		return
	}
	fetchUserStats()
	fetchLogs(0)
})
</script>

<style scoped>
.mp-logs-page,
.logs-container {
	min-height: 100vh;
	padding: 24rpx;
	background: #f3f6fb;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	box-sizing: border-box;
}

.mp-logs-page {
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
}

.admin-nav,
.header-main {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20rpx;
}

.admin-nav {
	padding-top: calc(20rpx + env(safe-area-inset-top));
}

.nav-btn-circle,
.mp-back-btn {
	height: 68rpx;
	padding: 0 26rpx;
	border-radius: 999rpx;
	border: 1px solid rgba(15, 23, 42, 0.08);
	background: rgba(255, 255, 255, 0.9);
	color: #334155;
	font-size: 24rpx;
	line-height: 68rpx;
	margin: 0;
	display: flex;
	align-items: center;
	justify-content: center;
}

.nav-btn-circle {
	width: 72rpx;
	padding: 0;
}

.nav-btn-circle::after,
.mp-back-btn::after,
.mp-search-btn::after,
.mp-page-btn::after {
	border: none;
}

.page-title,
.mp-title {
	font-size: 40rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-title-wrap {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
}

.mp-subtitle {
	font-size: 24rpx;
	color: #64748b;
}

.mp-hero,
.toolbar,
.logs-header {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.logs-layout {
	display: grid;
	grid-template-columns: 320rpx minmax(0, 1fr);
	gap: 20rpx;
	flex: 1;
	min-height: 0;
}

.user-sidebar,
.logs-main-content,
.mp-search-card,
.mp-state-card,
.mp-log-card {
	background: rgba(255, 255, 255, 0.94);
	border-radius: 28rpx;
	border: 1px solid rgba(148, 163, 184, 0.14);
	box-shadow: 0 16rpx 34rpx rgba(15, 23, 42, 0.05);
}

.user-sidebar,
.logs-main-content {
	padding: 20rpx;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	min-height: 0;
}

.sidebar-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	font-size: 24rpx;
	font-weight: 600;
	color: #0f172a;
}

.count-badge {
	font-size: 22rpx;
	color: #64748b;
}

.user-list,
.logs-scroller {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	overflow: auto;
	min-height: 0;
}

.user-item {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
	padding: 18rpx;
	border-radius: 20rpx;
	background: #f8fafc;
}

.user-item.active {
	background: linear-gradient(135deg, #0f9f6e 0%, #10b981 100%);
	color: #ffffff;
}

.user-name {
	font-size: 26rpx;
	font-weight: 600;
}

.user-last-active {
	font-size: 22rpx;
	opacity: 0.8;
}

.mp-search-card {
	padding: 20rpx;
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.mp-search-input {
	flex: 1;
	height: 76rpx;
	background: #f8fafc;
	border-radius: 20rpx;
	padding: 0 24rpx;
	font-size: 28rpx;
	color: #0f172a;
}

.mp-search-btn {
	height: 76rpx;
	line-height: 76rpx;
	padding: 0 28rpx;
	border-radius: 20rpx;
	background: linear-gradient(135deg, #0f9f6e 0%, #10b981 100%);
	color: #fff;
	font-size: 28rpx;
	font-weight: 600;
	margin: 0;
}

.mp-user-strip {
	white-space: nowrap;
}

.mp-user-row {
	display: inline-flex;
	gap: 16rpx;
	padding-right: 12rpx;
}

.mp-user-chip {
	min-width: 144rpx;
	padding: 18rpx 22rpx;
	border-radius: 24rpx;
	background: rgba(255, 255, 255, 0.8);
	border: 1px solid rgba(148, 163, 184, 0.16);
	display: flex;
	flex-direction: column;
	gap: 6rpx;
	box-sizing: border-box;
}

.mp-user-chip.active {
	background: linear-gradient(135deg, #0f9f6e 0%, #10b981 100%);
	border-color: transparent;
	box-shadow: 0 12rpx 26rpx rgba(16, 185, 129, 0.2);
}

.mp-user-chip-name {
	font-size: 28rpx;
	font-weight: 600;
	color: #0f172a;
}

.mp-user-chip-meta {
	font-size: 22rpx;
	color: #64748b;
}

.mp-user-chip.active .mp-user-chip-name,
.mp-user-chip.active .mp-user-chip-meta {
	color: #fff;
}

.mp-filter-summary {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 20rpx;
}

.mp-summary-text {
	font-size: 24rpx;
	color: #475569;
}

.mp-log-list,
.logs-main-content {
	flex: 1;
	min-height: 0;
}

.mp-state-card {
	padding: 40rpx 28rpx;
	text-align: center;
	color: #64748b;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	align-items: center;
}

.mp-state-card.error {
	color: #b91c1c;
}

.mp-state-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-state-hint {
	font-size: 25rpx;
	line-height: 1.6;
	color: inherit;
}

.mp-log-card {
	padding: 26rpx 24rpx;
	display: flex;
	flex-direction: column;
	gap: 18rpx;
}

.mp-log-meta {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 16rpx;
}

.user-info {
	display: flex;
	align-items: center;
	gap: 10rpx;
}

.mp-log-user {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f9f6e;
}

.mp-log-time,
.mp-log-extra {
	font-size: 22rpx;
	color: #64748b;
}

.mp-bubble {
	border-radius: 22rpx;
	padding: 22rpx 20rpx;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.mp-bubble.user {
	background: rgba(59, 130, 246, 0.06);
	border-left: 6rpx solid #60a5fa;
}

.mp-bubble.assistant {
	background: rgba(16, 185, 129, 0.07);
	border-left: 6rpx solid #34d399;
}

.mp-bubble-label {
	font-size: 24rpx;
	font-weight: 700;
	color: #0f172a;
}

.mp-bubble-text,
.mp-bubble-rich {
	font-size: 27rpx;
	line-height: 1.7;
	color: #334155;
	white-space: pre-wrap;
}

.mp-pagination-bar {
	display: flex;
	gap: 16rpx;
}

.mp-page-btn {
	flex: 1;
	height: 84rpx;
	line-height: 84rpx;
	border-radius: 22rpx;
	background: linear-gradient(135deg, #0f9f6e 0%, #10b981 100%);
	color: #fff;
	font-size: 28rpx;
	font-weight: 600;
	margin: 0;
}

.mp-page-btn.ghost {
	background: rgba(255, 255, 255, 0.88);
	color: #334155;
	border: 1px solid rgba(148, 163, 184, 0.2);
}

@media (max-width: 720px) {
	.logs-layout {
		grid-template-columns: 1fr;
	}
}
</style>
