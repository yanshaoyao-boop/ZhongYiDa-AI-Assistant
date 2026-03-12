<template>
	<!-- #ifndef H5 -->
	<view class="mp-lab-page">
		<view class="admin-nav">
			<view class="nav-btn-circle" @tap="goBack">
				<IconChevronLeft size="20" />
			</view>
			<text class="page-title">小易实验室</text>
			<view style="width: 72rpx;"></view>
		</view>

		<view class="mp-lab-card hero-card">
			<view class="hero-copy">
				<text class="lab-title">核心参数实验面板</text>
				<text class="lab-hint">这里修改的都是原后端已经支持的系统设置，不新增字段，也不改变接口语义。</text>
			</view>
			<button class="lab-save" :disabled="saving || loading || !hasPendingChanges" @tap="saveSettings">
				{{ saving ? '正在同步...' : '保存更改' }}
			</button>
		</view>

		<view class="mp-sync-banner" :class="syncStatus">
			<text class="lab-banner-title">{{ syncStatusLabel }}</text>
			<text class="mp-sync-banner__meta">{{ lastSyncedAt ? `上次同步：${lastSyncedAt}` : '尚未有同步记录' }}</text>
			<text v-if="errorMessage" class="mp-sync-banner__meta">{{ errorMessage }}</text>
		</view>

		<view v-if="loading" class="center-state">
			<text class="lab-hint">正在读取实时配置...</text>
		</view>

		<view v-else class="lab-grid">
			<view class="mp-lab-card">
				<text class="lab-section-title">回复生成</text>

				<view class="lab-field">
					<view class="lab-field-head">
						<text>创造力（Temperature）</text>
						<text class="value-pill">{{ settings.ai_temperature }}</text>
					</view>
					<slider
						min="0"
						max="1"
						step="0.1"
						:value="Number(settings.ai_temperature)"
						@change="updateSetting('ai_temperature', $event.detail.value.toString())"
						activeColor="#2563eb"
					/>
					<text class="small-hint">数值越低越稳健，数值越高越灵活。</text>
				</view>

				<view class="lab-field">
					<view class="lab-field-head">
						<text>上下文记忆长度</text>
						<text class="value-pill">{{ settings.ai_max_history }} 条</text>
					</view>
					<slider
						min="2"
						max="30"
						step="2"
						:value="Number(settings.ai_max_history)"
						@change="updateSetting('ai_max_history', $event.detail.value.toString())"
						activeColor="#10b981"
					/>
				</view>
			</view>

			<view class="mp-lab-card">
				<text class="lab-section-title">检索与知识能力</text>

				<view class="lab-row">
					<view class="lab-row-copy">
						<text>启用私有知识库（RAG）</text>
						<text class="small-hint">沿用现有后端知识检索能力。</text>
					</view>
					<switch :checked="settings.ai_enable_rag_bool" @change="updateSetting('ai_enable_rag_bool', $event.detail.value)" color="#10b981" />
				</view>

				<view class="lab-field">
					<view class="lab-field-head">
						<text>检索深度（Top K）</text>
						<text class="value-pill">{{ settings.ai_search_top_k }}</text>
					</view>
					<slider
						min="1"
						max="10"
						step="1"
						:value="Number(settings.ai_search_top_k)"
						@change="updateSetting('ai_search_top_k', $event.detail.value.toString())"
						activeColor="#0ea5e9"
					/>
				</view>

				<view class="lab-row">
					<view class="lab-row-copy">
						<text>启用联网搜索</text>
						<text class="small-hint">只切换现有设置项，不改变后端行为。</text>
					</view>
					<switch :checked="settings.ai_enable_search_bool" @change="updateSetting('ai_enable_search_bool', $event.detail.value)" color="#2563eb" />
				</view>
			</view>

			<view class="mp-lab-card">
				<text class="lab-section-title">欢迎语</text>
				<textarea
					v-model="settings.ai_welcome_message"
					class="lab-textarea"
					auto-height
					placeholder="输入新对话时展示的欢迎语..."
					@input="handleWelcomeInput"
				/>
				<text class="small-hint">保存后即写回现有系统设置。</text>
			</view>
		</view>
	</view>
	<!-- #endif -->
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { resolveApiUrl } from '@/utils/api'
import { ensureAdminPageAccess } from '@/utils/admin-access'
// #ifdef H5
import axios from 'axios'
// #endif
import { ChevronLeft as IconChevronLeft } from 'lucide-vue-next'

const settings = reactive({
	ai_temperature: '0.3',
	ai_max_history: '10',
	ai_enable_rag_bool: true,
	ai_enable_search_bool: true,
	ai_search_top_k: '5',
	ai_welcome_message: '',
})

const loading = ref(false)
const saving = ref(false)
const syncStatus = ref('idle')
const lastSyncedAt = ref('')
const lastSnapshot = ref('')
const errorMessage = ref('')

const buildPayload = () => ({
	settings: {
		ai_temperature: settings.ai_temperature.toString(),
		ai_max_history: settings.ai_max_history.toString(),
		ai_search_top_k: settings.ai_search_top_k.toString(),
		ai_welcome_message: settings.ai_welcome_message,
		ai_enable_rag: settings.ai_enable_rag_bool ? 'true' : 'false',
		ai_enable_search: settings.ai_enable_search_bool ? 'true' : 'false',
	},
})

const buildSnapshot = () => JSON.stringify(buildPayload().settings)

const hasPendingChanges = computed(() => buildSnapshot() !== lastSnapshot.value)

const syncStatusLabel = computed(() => {
	if (syncStatus.value === 'saved') return '配置已同步'
	if (syncStatus.value === 'error') return '同步失败'
	if (syncStatus.value === 'dirty') return '存在未保存更改'
	if (loading.value) return '正在加载配置'
	return '配置正常'
})

const goBack = () => {
	const pages = getCurrentPages()
	if (pages.length > 1) {
		uni.navigateBack({ delta: 1 })
		return
	}
	uni.navigateTo({ url: '/pages/admin/admin' })
}

const formatSyncTime = (date) => {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	const hour = String(date.getHours()).padStart(2, '0')
	const minute = String(date.getMinutes()).padStart(2, '0')
	return `${year}-${month}-${day} ${hour}:${minute}`
}

const normalizeSettings = (data = {}) => {
	if (data.ai_temperature !== undefined) settings.ai_temperature = String(data.ai_temperature)
	if (data.ai_max_history !== undefined) settings.ai_max_history = String(data.ai_max_history)
	if (data.ai_search_top_k !== undefined) settings.ai_search_top_k = String(data.ai_search_top_k)
	if (data.ai_welcome_message !== undefined) settings.ai_welcome_message = String(data.ai_welcome_message || '')
	settings.ai_enable_rag_bool = data.ai_enable_rag !== 'false'
	settings.ai_enable_search_bool = data.ai_enable_search !== 'false'
}

const updateSetting = (key, value) => {
	settings[key] = value
	errorMessage.value = ''
	syncStatus.value = 'dirty'
}

const handleWelcomeInput = () => {
	syncStatus.value = 'dirty'
	errorMessage.value = ''
}

const getTokenHeaders = () => {
	try {
		const token = uni.getStorageSync('token')
		return token ? { Authorization: `Bearer ${token}` } : {}
	} catch (error) {
		return {}
	}
}

const extractErrorMessage = (error, fallback) => {
	// #ifdef H5
	return error?.response?.data?.detail || error?.message || fallback
	// #endif
	return error?.message || fallback
}

const requestSettings = async (path, options = {}) => {
	const url = resolveApiUrl(path)
	const method = options.method || 'GET'

	// #ifdef H5
	const response = await axios({
		url,
		method,
		data: options.data,
		headers: {
			...getTokenHeaders(),
			...(options.headers || {}),
		},
	})
	return response.data
	// #endif

	// #ifndef H5
	return await new Promise((resolve, reject) => {
		uni.request({
			url,
			method,
			data: options.data,
			header: {
				'content-type': 'application/json',
				...getTokenHeaders(),
				...(options.headers || {}),
			},
			timeout: 15000,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
					return
				}
				const detail = res.data && typeof res.data === 'object' ? res.data.detail : ''
				reject(new Error(detail || `request failed (${res.statusCode})`))
			},
			fail: (error) => reject(error),
		})
	})
	// #endif
}

const fetchSettings = async () => {
	loading.value = true
	errorMessage.value = ''
	try {
		const data = await requestSettings('/api/settings/')
		normalizeSettings(data)
		lastSnapshot.value = buildSnapshot()
		syncStatus.value = 'idle'
	} catch (error) {
		const message = extractErrorMessage(error, '加载配置失败')
		errorMessage.value = message
		syncStatus.value = 'error'
		uni.showToast({ title: message, icon: 'none' })
	} finally {
		loading.value = false
	}
}

const saveSettings = async () => {
	saving.value = true
	errorMessage.value = ''
	try {
		await requestSettings('/api/settings/', {
			method: 'PATCH',
			data: buildPayload(),
		})
		lastSnapshot.value = buildSnapshot()
		syncStatus.value = 'saved'
		lastSyncedAt.value = formatSyncTime(new Date())
		uni.showToast({ title: '保存成功', icon: 'success' })
	} catch (error) {
		const message = extractErrorMessage(error, '保存失败')
		errorMessage.value = message
		syncStatus.value = 'error'
		uni.showToast({ title: message, icon: 'none' })
	} finally {
		saving.value = false
	}
}

onMounted(() => {
	if (!ensureAdminPageAccess('lab')) return
	fetchSettings()
})
</script>

<style scoped>
.mp-lab-page {
	min-height: 100vh;
	padding: 24rpx;
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
	background: #f3f6fb;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	box-sizing: border-box;
}

.admin-nav {
	padding-top: calc(20rpx + env(safe-area-inset-top));
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.nav-btn-circle {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background: rgba(255, 255, 255, 0.96);
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.06);
}

.page-title {
	font-size: 38rpx;
	font-weight: 700;
	color: #0f172a;
}

.lab-grid {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.mp-lab-card,
.mp-sync-banner {
	background: rgba(255, 255, 255, 0.96);
	border-radius: 28rpx;
	padding: 24rpx;
	box-shadow: 0 14rpx 34rpx rgba(15, 23, 42, 0.06);
}

.hero-card {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20rpx;
}

.hero-copy {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.lab-title {
	display: block;
	font-size: 34rpx;
	font-weight: 700;
	color: #0f172a;
}

.lab-hint,
.mp-sync-banner__meta,
.small-hint {
	display: block;
	font-size: 24rpx;
	line-height: 1.6;
	color: #64748b;
}

.lab-save {
	margin: 0;
	padding: 0 28rpx;
	height: 76rpx;
	line-height: 76rpx;
	border-radius: 20rpx;
	background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
	color: #fff;
	font-size: 26rpx;
	font-weight: 600;
}

.lab-save[disabled] {
	opacity: 0.55;
}

.mp-sync-banner.saved {
	background: #ecfdf5;
}

.mp-sync-banner.error {
	background: #fff1f2;
}

.mp-sync-banner.dirty {
	background: #eff6ff;
}

.lab-banner-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 8rpx;
	display: block;
}

.lab-section-title {
	display: block;
	font-size: 30rpx;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 18rpx;
}

.lab-field {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-bottom: 18rpx;
}

.lab-field:last-child {
	margin-bottom: 0;
}

.lab-field-head,
.lab-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20rpx;
}

.lab-row-copy {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	flex: 1;
}

.value-pill {
	padding: 8rpx 16rpx;
	border-radius: 999rpx;
	background: #eff6ff;
	color: #2563eb;
	font-size: 22rpx;
	font-weight: 700;
}

.lab-textarea {
	min-height: 180rpx;
	padding: 20rpx;
	border-radius: 22rpx;
	background: #f8fafc;
	color: #0f172a;
	font-size: 28rpx;
	box-sizing: border-box;
}

.center-state {
	padding: 40rpx 20rpx;
	text-align: center;
}
</style>
