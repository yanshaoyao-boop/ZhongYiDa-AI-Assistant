<template>
	<view class="intel-root">
		<!-- 最小化悬浮按钮 -->
		<view v-if="isOpen && isCollapsed" class="combat-intel-minimized glass-panel" @tap="$emit('update:isCollapsed', false)">
			<text class="minimized-icon">📊</text>
			<text class="minimized-text">实战情报</text>
		</view>

		<!-- 情报面板主体 -->
		<view :class="['combat-intel-panel', 'combat-intel-shell', 'glass-panel', { show: isOpen, collapsed: isCollapsed }]">
			<view class="panel-header">
				<text class="panel-title">实战情报中心</text>
				<view class="panel-header-btns">
					<view class="panel-collapse-btn" @tap="$emit('update:isCollapsed', true)">－</view>
					<view class="panel-close" @tap="$emit('update:isOpen', false)">×</view>
				</view>
			</view>
			
			<scroll-view scroll-y class="panel-content">
				<view class="intel-section">
					<text class="intel-label">🎯 当前场景</text>
					<text class="intel-text">{{ currentScenario ? currentScenario.name : '未开始' }}</text>
				</view>
				
				<view class="intel-section intel-section-highlight">
					<text class="intel-label">👤 客户画像</text>
					<text class="intel-text">{{ selectedPersona || '待选择' }}</text>
				</view>
				
				<view class="intel-section">
					<text class="intel-label">🎖️ 过关要点</text>
					<view v-if="successCriteria && successCriteria.length">
						<text
							v-for="(item, index) in successCriteria"
							:key="index"
							class="intel-text intel-text-block"
						>
							{{ index + 1 }}. {{ item }}
						</text>
					</view>
					<text v-else class="intel-text empty-hint">先进入一个教练场景，情报会自动出现在这里。</text>
				</view>
				
				<button v-if="currentScenario" class="quit-combat-btn" @tap="$emit('quit')">结束对练并评价</button>
			</scroll-view>
		</view>
	</view>
</template>

<script setup>
defineProps({
	isOpen: {
		type: Boolean,
		default: false
	},
	isCollapsed: {
		type: Boolean,
		default: false
	},
	currentScenario: {
		type: Object,
		default: null
	},
	selectedPersona: {
		type: String,
		default: ''
	},
	successCriteria: {
		type: Array,
		default: () => []
	}
})

defineEmits(['update:isCollapsed', 'update:isOpen', 'quit'])
</script>

<style scoped>
.intel-root {
	z-index: 90;
}

.combat-intel-minimized {
	position: fixed;
	right: 16px;
	bottom: 120px;
	width: 60px;
	height: 60px;
	background: rgba(255, 255, 255, 0.9);
	border-radius: 50%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
	border: 1px solid rgba(0, 0, 0, 0.05);
	animation: bounceIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes bounceIn {
	0% { opacity: 0; transform: scale(0.5); }
	70% { opacity: 1; transform: scale(1.1); }
	100% { opacity: 1; transform: scale(1); }
}

.minimized-icon {
	font-size: 20px;
}
.minimized-text {
	font-size: 9px;
	color: #64748b;
	margin-top: 2px;
}

.combat-intel-panel {
	position: fixed;
	top: 100px;
	right: 16px;
	width: 240px;
	max-height: 60vh;
	background: rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(10px);
	border-radius: 16px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
	border: 1px solid rgba(0, 0, 0, 0.05);
	opacity: 0;
	transform: translateX(30px);
	pointer-events: none;
}

.combat-intel-panel.show {
	opacity: 1;
	transform: translateX(0);
	pointer-events: auto;
}

.combat-intel-panel.collapsed {
	opacity: 0;
	transform: translateX(30px);
	pointer-events: none;
}

.panel-header {
	padding: 12px 16px;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: rgba(255, 255, 255, 0.5);
}

.panel-title {
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

.panel-header-btns {
	display: flex;
	align-items: center;
}

.panel-collapse-btn, .panel-close {
	padding: 4px 8px;
	font-size: 18px;
	color: #94a3b8;
	line-height: 1;
}

.panel-content {
	flex: 1;
	padding: 16px;
}

.intel-section {
	margin-bottom: 16px;
}

.intel-label {
	font-size: 11px;
	color: #94a3b8;
	text-transform: uppercase;
	margin-bottom: 4px;
	display: block;
}

.intel-text {
	font-size: 14px;
	color: #1e293b;
	font-weight: 500;
}

.intel-text-block {
	display: block;
	margin-bottom: 4px;
	line-height: 1.4;
}

.intel-section-highlight {
	background: rgba(37, 99, 235, 0.05);
	padding: 8px 12px;
	border-radius: 8px;
}

.empty-hint {
	color: #94a3b8;
	font-size: 12px;
}

.quit-combat-btn {
	width: 100%;
	height: 40px;
	background: #ef4444;
	color: #ffffff;
	font-size: 13px;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-top: 12px;
	border: none;
	box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}
</style>
