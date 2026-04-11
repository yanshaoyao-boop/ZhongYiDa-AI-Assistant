<template>
	<Teleport to="body">
		<div v-if="show" class="premium-modal-backdrop" @click.self="$emit('update:show', false)">
			<div class="premium-modal news-modal animate-modal">
				<div class="modal-header">
					<div class="header-top">
						<div class="header-main">
							<Newspaper class="header-icon" />
							<h3>行业资讯中心</h3>
						</div>
						<button class="close-btn-inner" @click="$emit('update:show', false)"><X /></button>
					</div>
					<div class="modal-tabs">
						<button :class="{ active: newsTab === 'current' }" @click="$emit('update:newsTab', 'current')">最新资讯</button>
						<button :class="{ active: newsTab === 'history' }" @click="$emit('update:newsTab', 'history')">历史存档</button>
					</div>
				</div>
				<div class="modal-body news-body">
					<div v-if="loading" class="modal-loading-box">
						<div class="loading-spinner"></div>
						<span>正在同步行业资讯...</span>
					</div>
					<div v-else-if="items.length === 0" class="modal-empty-box">
						<Inbox size="48" style="opacity:0.3; margin-bottom:12px;" />
						<p>暂无行业资讯内容</p>
					</div>
					<div v-else class="news-list-scroll">
						<div v-for="item in items" :key="item.id" class="news-premium-card">
							<div class="news-card-header">
								<span class="news-date">{{ formatDate(item.created_at) }}</span>
								<span v-if="newsTab === 'current'" class="news-tag-new">NEW</span>
							</div>
							<p class="news-card-text">{{ item.content }}</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup>
import { Inbox, Newspaper, X } from 'lucide-vue-next'

defineProps({
	show: {
		type: Boolean,
		default: false
	},
	newsTab: {
		type: String,
		default: 'current'
	},
	loading: {
		type: Boolean,
		default: false
	},
	items: {
		type: Array,
		default: () => []
	}
})

defineEmits(['update:show', 'update:newsTab'])

const formatDate = (value) => {
	if (!value) return ''
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) return String(value)
	return new Intl.DateTimeFormat('zh-CN', {
		timeZone: 'Asia/Shanghai',
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		hour12: false
	})
		.format(date)
		.replace(/\//g, '-')
}
</script>

<style scoped>
.premium-modal-backdrop {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.45);
	backdrop-filter: blur(8px);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.premium-modal {
	width: 100%;
	background: rgba(255, 255, 255, 0.98);
	border-radius: 24px;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.news-modal {
	max-width: 760px;
	height: 86vh;
}

.animate-modal {
	animation: slideZoomIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideZoomIn {
	from { opacity: 0; transform: scale(0.95) translateY(20px); }
	to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
	padding: 24px 28px;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.header-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.header-main {
	display: flex;
	align-items: center;
	gap: 12px;
}

.header-icon {
	color: #0284c7;
}

h3 {
	margin: 0;
	font-size: 20px;
	font-weight: 700;
	color: #0f172a;
}

.close-btn-inner {
	background: #f1f5f9;
	border: none;
	width: 32px;
	height: 32px;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
	cursor: pointer;
}

.modal-tabs {
	display: flex;
	gap: 8px;
	background: #f1f5f9;
	padding: 4px;
	border-radius: 12px;
}

.modal-tabs button {
	flex: 1;
	height: 36px;
	border: none;
	background: transparent;
	border-radius: 8px;
	font-size: 14px;
	font-weight: 600;
	color: #64748b;
	cursor: pointer;
	transition: all 0.2s;
}

.modal-tabs button.active {
	background: #ffffff;
	color: #0284c7;
	box-shadow: 0 4px 10px rgba(2, 132, 199, 0.1);
}

.modal-body {
	flex: 1;
	overflow-y: auto;
	padding: 24px 28px;
}

.modal-loading-box, .modal-empty-box {
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	color: #94a3b8;
}

.loading-spinner {
	width: 40px;
	height: 40px;
	border: 3px solid #f1f5f9;
	border-top: 3px solid #0284c7;
	border-radius: 50%;
	animation: spin 1s linear infinite;
	margin-bottom: 16px;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.news-premium-card {
	background: #f8fafc;
	border-radius: 16px;
	padding: 20px;
	margin-bottom: 16px;
	border: 1px solid rgba(0, 0, 0, 0.03);
}

.news-card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
}

.news-date {
	font-size: 12px;
	font-weight: 700;
	color: #0284c7;
	background: rgba(2, 132, 199, 0.08);
	padding: 4px 10px;
	border-radius: 6px;
}

.news-tag-new {
	font-size: 10px;
	font-weight: 800;
	background: #ef4444;
	color: #ffffff;
	padding: 2px 6px;
	border-radius: 4px;
}

.news-card-text {
	font-size: 14px;
	color: #334155;
	line-height: 1.7;
	white-space: pre-wrap;
}
</style>
