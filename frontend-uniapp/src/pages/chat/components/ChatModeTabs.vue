<template>
	<view class="mode-selector-container">
		<view class="mode-selector mode-selector-pill glass-panel">
			<view
				:class="['mode-tab', 'mode-btn', { active: modelValue === 'general', 'tab-active-general': modelValue === 'general' }]"
				@tap="emit('change', 'general')"
			>
				<text class="tab-text">全能助手</text>
			</view>
			<view class="tab-divider"></view>
			<view
				:class="['mode-tab', 'mode-btn', { active: modelValue === 'coach', 'tab-active-coach': modelValue === 'coach' }]"
				@tap="emit('change', 'coach')"
			>
				<text class="tab-text">知识教练</text>
			</view>
			<view class="tab-divider"></view>
			<view
				:class="['mode-tab', 'mode-btn', { active: modelValue === 'expert', 'tab-active-expert': modelValue === 'expert' }]"
				@tap="emit('change', 'expert')"
			>
				<text class="tab-text">专家指导</text>
			</view>
		</view>
	</view>
</template>

<script setup>
defineProps({
	modelValue: {
		type: String,
		default: 'general'
	}
})

const emit = defineEmits(['change'])
</script>

<style scoped>
.mode-selector-container {
	display: flex;
	justify-content: center;
	padding: 10px 0;
	width: 100%;
}

.mode-selector {
	display: flex;
	align-items: center;
	background: rgba(255, 255, 255, 0.6);
	backdrop-filter: blur(10px);
	border-radius: 40px;
	padding: 4px;
	border: 1px solid rgba(0, 0, 0, 0.05);
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.mode-tab {
	padding: 8px 16px;
	border-radius: 30px;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	display: flex;
	align-items: center;
	justify-content: center;
}

.tab-text {
	font-size: 13px;
	font-weight: 500;
	color: #64748b;
}

.mode-tab.active {
	background: #ffffff;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.mode-tab.active .tab-text {
	color: #1e293b;
	font-weight: 600;
}

.tab-active-general.active {
	color: #2563eb;
}

.tab-active-coach.active {
	color: #059669;
}

.tab-active-expert.active {
	color: #7c3aed;
}

.tab-divider {
	width: 1px;
	height: 12px;
	background: rgba(0, 0, 0, 0.05);
	margin: 0 4px;
}
</style>
