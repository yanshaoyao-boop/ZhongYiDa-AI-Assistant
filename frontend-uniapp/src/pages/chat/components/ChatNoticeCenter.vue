<template>
	<view v-if="show" class="notice-center-overlay" @tap="$emit('update:show', false)">
		<view class="notice-center-sheet" @tap.stop>
			<view class="notice-center-head">
				<text class="notice-center-title">企业公告中心</text>
				<text class="notice-center-close" @tap="$emit('update:show', false)">×</text>
			</view>
			
			<view class="notice-center-tabs">
				<view class="notice-center-tab" :class="{ active: noticeTab === 'current' }" @tap="$emit('update:noticeTab', 'current')">
					<text>最新通知</text>
				</view>
				<view class="notice-center-tab" :class="{ active: noticeTab === 'history' }" @tap="$emit('update:noticeTab', 'history')">
					<text>历史公告</text>
				</view>
			</view>
			
			<scroll-view scroll-y class="notice-center-scroll">
				<view v-if="loading" class="notice-center-status">
					<view class="loading-dots">
						<text class="dot">.</text><text class="dot">.</text><text class="dot">.</text>
					</view>
					<text>从服务器获取中...</text>
				</view>
				
				<view v-else-if="notices.length === 0" class="notice-center-status empty">
					<text class="empty-icon">📂</text>
					<text>{{ noticeTab === 'current' ? '暂时没有新的重要通知' : '暂无历史公告记录' }}</text>
				</view>
				
				<view v-for="notice in notices" :key="notice.id" class="notice-center-card" @tap="$emit('previewNotice', notice)">
					<view class="notice-header">
						<text class="notice-center-date">{{ formatDate(notice.created_at) }}</text>
						<view v-if="noticeTab === 'current'" class="new-tag">NEW</view>
					</view>
					<text class="notice-center-content">{{ notice.content }}</text>
					<view class="notice-footer">
						<text class="notice-author">发布者: {{ notice.created_by_name || '管理中心' }}</text>
					</view>
				</view>
				<view class="scroll-bottom-spacer"></view>
			</scroll-view>
		</view>
	</view>
</template>

<script setup>
const props = defineProps({
	show: {
		type: Boolean,
		default: false
	},
	noticeTab: {
		type: String,
		default: 'current'
	},
	loading: {
		type: Boolean,
		default: false
	},
	notices: {
		type: Array,
		default: () => []
	}
})

defineEmits(['update:show', 'update:noticeTab', 'previewNotice'])

const formatDate = (value) => {
	if (!value) return ''
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) return String(value)
	const month = `${date.getMonth() + 1}`.padStart(2, '0')
	const day = `${date.getDate()}`.padStart(2, '0')
	const hours = `${date.getHours()}`.padStart(2, '0')
	const minutes = `${date.getMinutes()}`.padStart(2, '0')
	return `${month}-${day} ${hours}:${minutes}`
}
</script>

<style scoped>
.notice-center-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.4);
	display: flex;
	align-items: flex-end;
	justify-content: center;
	z-index: 1000;
	animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}

.notice-center-sheet {
	width: 100%;
	height: 80vh;
	background: #ffffff;
	border-radius: 24px 24px 0 0;
	display: flex;
	flex-direction: column;
	animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	overflow: hidden;
}

@keyframes slideUp {
	from { transform: translateY(100%); }
	to { transform: translateY(0); }
}

.notice-center-head {
	padding: 24px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.notice-center-title {
	font-size: 20px;
	font-weight: 700;
	color: #1e293b;
}

.notice-center-close {
	font-size: 28px;
	color: #94a3b8;
	padding: 4px;
	line-height: 1;
}

.notice-center-tabs {
	padding: 0 24px 16px;
	display: flex;
	gap: 20px;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.notice-center-tab {
	font-size: 15px;
	font-weight: 600;
	color: #94a3b8;
	padding-bottom: 8px;
	position: relative;
	transition: all 0.2s;
}

.notice-center-tab.active {
	color: #2563eb;
}

.notice-center-tab.active::after {
	content: '';
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 3px;
	background: #2563eb;
	border-radius: 2px;
}

.notice-center-scroll {
	flex: 1;
	padding: 24px;
}

.notice-center-status {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60px 0;
	color: #94a3b8;
}

.empty-icon {
	font-size: 48px;
	margin-bottom: 16px;
}

.notice-center-card {
	background: #f8fafc;
	border: 1px solid rgba(0, 0, 0, 0.03);
	border-radius: 16px;
	padding: 16px;
	margin-bottom: 16px;
	transition: all 0.2s;
}

.notice-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 8px;
}

.notice-center-date {
	font-size: 11px;
	font-weight: 700;
	color: #3b82f6;
	background: rgba(59, 130, 246, 0.1);
	padding: 2px 8px;
	border-radius: 4px;
}

.new-tag {
	font-size: 9px;
	background: #ef4444;
	color: #ffffff;
	padding: 2px 6px;
	border-radius: 4px;
	font-weight: bold;
}

.notice-center-content {
	font-size: 14px;
	color: #475569;
	line-height: 1.6;
	display: block;
	margin-bottom: 12px;
}

.notice-author {
	font-size: 11px;
	color: #94a3b8;
}

.scroll-bottom-spacer {
	height: 40px;
}

.loading-dots {
	font-size: 32px;
	display: flex;
	align-items: center;
	gap: 4px;
	margin-bottom: 8px;
}

.dot {
	animation: dotBlink 1.4s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotBlink {
	0%, 80%, 100% { opacity: 0; }
	40% { opacity: 1; }
}
</style>
