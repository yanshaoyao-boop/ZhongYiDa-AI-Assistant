<template>
	<div :class="['sidebar-overlay', { show: isOpen }]" @click="$emit('close')"></div>
	<aside :class="['sidebar', 'glass-panel', { show: isOpen }]">
		<div class="sidebar-header">
			<button class="new-chat-btn" @click="$emit('newChat')">
				<span class="icon">+</span> 新对话
			</button>
		</div>
		<div class="session-list">
			<div v-for="session in sessions" :key="session.id" 
				:class="['session-item', { active: session.id === currentSessionId }]"
				@click="$emit('switchSession', session.id)">
				<div class="session-title">{{ session.title || '新对话' }}</div>
				<button class="delete-btn" @click.stop="$emit('deleteSession', session.id)" title="删除对话">×</button>
			</div>
		</div>

		<div class="sidebar-footer">
			<button class="sidebar-settings-btn" @click="$emit('showSettings')">
				<Settings size="16" /> 设置
			</button>
			<a v-if="isAdmin" href="/admin" target="_blank" class="sidebar-admin-btn">
				<ShieldCheck size="18" /> 管理员入口
			</a>
			<div class="sidebar-user-info">
				<div class="user-avatar-sidebar">{{ userName?.[0]?.toUpperCase() || 'U' }}</div>
				<div class="user-details">
					<span class="user-name-sidebar">{{ userName }}</span>
					<button class="logout-link-sidebar" @click="$emit('logout')">退出登录</button>
				</div>
			</div>
		</div>
	</aside>
</template>

<script setup>
import { Settings, ShieldCheck } from 'lucide-vue-next'

defineProps({
	isOpen: {
		type: Boolean,
		default: false
	},
	sessions: {
		type: Array,
		default: () => []
	},
	currentSessionId: {
		type: [String, Number],
		default: ''
	},
	userName: {
		type: String,
		default: ''
	},
	isAdmin: {
		type: Boolean,
		default: false
	}
})

defineEmits(['close', 'newChat', 'switchSession', 'deleteSession', 'showSettings', 'logout'])
</script>

<style scoped>
.sidebar-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.4);
	z-index: 99;
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar-overlay.show {
	opacity: 1;
	pointer-events: auto;
}

.sidebar {
	position: fixed;
	top: 0;
	left: -320px;
	width: 320px;
	height: 100vh;
	background: #fdfdfd;
	backdrop-filter: blur(20px);
	z-index: 100;
	transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	display: flex;
	flex-direction: column;
	border-right: 1px solid rgba(0, 0, 0, 0.04);
	box-shadow: 4px 0 20px rgba(0, 0, 0, 0.02);
}
.sidebar.show {
	left: 0;
}

@media screen and (min-width: 768px) {
	.sidebar {
		position: static;
		left: 0;
	}
	.sidebar-overlay {
		display: none;
	}
}

.sidebar-header {
	padding: 24px 16px;
}

.new-chat-btn {
	width: 100%;
	height: 48px;
	background: #2563eb;
	color: #ffffff;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 15px;
	font-weight: 600;
	border: none;
	cursor: pointer;
	transition: all 0.2s;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}
.new-chat-btn .icon {
	margin-right: 8px;
	font-size: 20px;
}

.session-list {
	flex: 1;
	padding: 8px 12px;
	overflow-y: auto;
}

.session-item {
	padding: 12px 14px;
	border-radius: 12px;
	margin-bottom: 6px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	cursor: pointer;
	transition: all 0.2s;
}
.session-item:hover {
	background: rgba(37, 99, 235, 0.04);
}
.session-item.active {
	background: rgba(37, 99, 235, 0.08);
}

.session-title {
	font-size: 14px;
	color: #475569;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 180px;
}
.active .session-title {
	color: #2563eb;
	font-weight: 600;
}

.delete-btn {
	padding: 4px;
	line-height: 1;
	font-size: 18px;
	color: #94a3b8;
	background: transparent;
	border: none;
	cursor: pointer;
	opacity: 0;
}
.session-item:hover .delete-btn {
	opacity: 1;
}

.sidebar-footer {
	padding: 16px;
	border-top: 1px solid rgba(0, 0, 0, 0.05);
	background: rgba(255, 255, 255, 0.5);
}

.sidebar-settings-btn, .sidebar-admin-btn {
	width: 100%;
	height: 40px;
	background: transparent;
	color: #64748b;
	font-size: 14px;
	border: 1px solid rgba(0, 0, 0, 0.05);
	border-radius: 10px;
	margin-bottom: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	cursor: pointer;
	text-decoration: none;
}

.sidebar-user-info {
	display: flex;
	align-items: center;
	padding-top: 12px;
}

.user-avatar-sidebar {
	width: 40px;
	height: 40px;
	background: linear-gradient(135deg, #3b82f6, #2563eb);
	color: white;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 700;
	box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2);
}

.user-details {
	margin-left: 12px;
	display: flex;
	flex-direction: column;
}

.user-name-sidebar {
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

.logout-link-sidebar {
	font-size: 12px;
	color: #ef4444;
	background: transparent;
	padding: 0;
	border: none;
	cursor: pointer;
	text-align: left;
}
</style>
