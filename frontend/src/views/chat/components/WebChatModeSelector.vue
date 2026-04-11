<template>
	<div class="mode-selector-wrapper">
		<div class="mode-selector glass-panel">
			<button class="mode-btn" @click="$emit('openIndustryNews')">
				<div class="icon-wrapper">
					<Newspaper size="18" class="icon" />
					<span v-if="hasNewIndustryNews" class="notice-dot"></span>
				</div>
				<span class="btn-text">行业资讯</span>
			</button>
			<button class="mode-btn" @click="$emit('openNotices')">
				<div class="icon-wrapper">
					<AlertCircle size="18" class="icon" />
					<span v-if="hasNewNotice" class="notice-dot"></span>
				</div>
				<span class="btn-text">重要通知</span>
			</button>
			<button class="mode-btn" @click="$emit('openTools')">
				<Zap size="18" class="icon" /> <span class="btn-text">智能工具</span>
			</button>
		</div>

		<div class="mode-selector glass-panel">
			<button 
				:class="['mode-btn', { active: modelValue === 'general' }]"
				@click="$emit('update:modelValue', 'general')"
			>
				<Zap size="18" class="icon" /> <span class="btn-text">全能助手</span>
			</button>
			<button 
				:class="['mode-btn', { active: modelValue === 'coach' }]"
				@click="$emit('update:modelValue', 'coach')"
			>
				<Target size="18" class="icon" /> <span class="btn-text">知识教练</span>
			</button>
			<button 
				:class="['mode-btn', { active: modelValue === 'expert' }]"
				@click="$emit('update:modelValue', 'expert')"
			>
				<FileQuestion size="18" class="icon" /> <span class="btn-text">专家指导</span>
			</button>
		</div>
	</div>
</template>

<script setup>
import { AlertCircle, Zap, Target, FileQuestion, Newspaper } from 'lucide-vue-next'

defineProps({
	modelValue: {
		type: String,
		default: 'general'
	},
	hasNewNotice: {
		type: Boolean,
		default: false
	},
	hasNewIndustryNews: {
		type: Boolean,
		default: false
	}
})

defineEmits(['update:modelValue', 'openNotices', 'openTools', 'openIndustryNews'])
</script>

<style scoped>
.mode-selector-wrapper {
	display: flex;
	flex-direction: column;
	align-items: stretch;
	gap: 10px;
	width: min(480px, 100%);
}

@media screen and (max-width: 1024px) {
	.mode-selector-wrapper {
		gap: 12px;
		width: 100%;
	}
}

.mode-selector {
	display: flex;
	background: rgba(255, 255, 255, 0.6);
	backdrop-filter: blur(10px);
	border-radius: 12px;
	padding: 4px;
	border: 1px solid rgba(0, 0, 0, 0.05);
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
	width: 100%;
}

.mode-btn {
	padding: 8px 12px;
	border-radius: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex: 1;
	gap: 8px;
	background: transparent;
	border: none;
	cursor: pointer;
	color: #64748b;
	transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.mode-btn .icon {
	opacity: 0.7;
}

.mode-btn:hover {
	background: rgba(37, 99, 235, 0.04);
	color: #2563eb;
}

.mode-btn.active {
	background: #ffffff;
	color: #2563eb;
	box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
	font-weight: 600;
}

.mode-btn.active .icon {
	color: #2563eb;
	opacity: 1;
}

.icon-wrapper {
	position: relative;
	display: flex;
	align-items: center;
}

.notice-dot {
	position: absolute;
	top: -4px;
	right: -4px;
	width: 12px;
	height: 12px;
	background: #ef4444;
	border-radius: 50%;
	border: 2px solid #ffffff;
	box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.18);
}

.btn-text {
	font-size: 13px;
	white-space: nowrap;
}

@media screen and (max-width: 768px) {
	.mode-selector {
		padding: 4px;
	}
	.mode-btn {
		padding: 8px 4px;
	}
	.btn-text {
		font-size: 12px;
	}
}
</style>
