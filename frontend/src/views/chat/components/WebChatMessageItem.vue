<template>
	<div class="message-wrapper" :class="message.role">
		<!-- 头像部分 -->
		<div class="avatar">
			<template v-if="message.role === 'assistant'">
				<div class="avatar-container assistant">
					<img :src="aiAvatar" alt="小易" class="xiaoyi-avatar" />
				</div>
			</template>
			<template v-else>
				<div class="user-avatar">You</div>
			</template>
		</div>

		<!-- 消息体部分 -->
		<div class="message-content glass-panel" :class="{'is-typing': message.isTyping}">
			<!-- 附件图片 -->
			<div v-if="message.image" class="message-image-container">
				<img 
					:src="message.image" 
					alt="用户上传图片" 
					class="chat-message-image" 
					@click="$emit('previewImage', message.image)" 
				/>
			</div>

			<!-- 文本内容 (HTML渲染) -->
			<div class="markdown-body" v-html="renderedContent"></div>

			<!-- 打字机光标 -->
			<span v-if="message.isTyping" class="cursor-blink"></span>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
	message: {
		type: Object,
		required: true
	},
	aiAvatar: {
		type: String,
		default: ''
	}
})

const renderedContent = computed(() => renderMarkdown(props.message?.content || ''))

defineEmits(['previewImage'])
</script>

<style scoped>
.message-wrapper {
	display: flex;
	margin-bottom: 32px;
	gap: 16px;
	padding: 0 4px;
	animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
	from { opacity: 0; transform: translateY(20px); }
	to { opacity: 1; transform: translateY(0); }
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.avatar {
	flex-shrink: 0;
	margin-top: 4px;
}

.avatar-container {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	overflow: hidden;
	background: #ffffff;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(0, 0, 0, 0.03);
}

.xiaoyi-avatar {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.user-avatar {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	background: linear-gradient(135deg, #3b82f6, #2563eb);
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 700;
	font-size: 13px;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.message-content {
	max-width: 80%;
	padding: 16px 20px;
	border-radius: 16px;
	font-size: 15px;
	line-height: 1.65;
	color: #1e293b;
	position: relative;
	transition: all 0.2s;
}

.message-wrapper.assistant .message-content {
	background: rgba(255, 255, 255, 0.85);
	border-top-left-radius: 4px;
	border: 1px solid rgba(0, 0, 0, 0.04);
}

.message-wrapper.user .message-content {
	background: #2563eb;
	color: #ffffff;
	border-top-right-radius: 4px;
	box-shadow: 0 10px 30px -10px rgba(37, 99, 235, 0.3);
}

.message-image-container {
	margin-bottom: 12px;
	border-radius: 12px;
	overflow: hidden;
	border: 1px solid rgba(0, 0, 0, 0.05);
	max-width: 400px;
}

.chat-message-image {
	width: 100%;
	height: auto;
	display: block;
	cursor: zoom-in;
	transition: opacity 0.2s;
}
.chat-message-image:hover {
	opacity: 0.95;
}

.cursor-blink {
	display: inline-block;
	width: 2px;
	height: 18px;
	background: currentColor;
	margin-left: 4px;
	vertical-align: middle;
	animation: blink 1s infinite steps(2, start);
}

@keyframes blink {
	to { opacity: 0; }
}

/* 兼容 markdown-body 样式在父级定义或全局定义，这里做一些基础补充 */
.markdown-body {
	word-break: break-word;
	overflow-wrap: break-word;
}

.markdown-body :deep(.chat-table-wrap) {
	margin: 14px 0;
	overflow-x: auto;
	border: 1px solid rgba(148, 163, 184, 0.28);
	border-radius: 12px;
	background: rgba(255, 255, 255, 0.96);
	box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.message-wrapper.user .markdown-body :deep(.chat-table-wrap) {
	background: rgba(255, 255, 255, 0.16);
	border-color: rgba(255, 255, 255, 0.24);
}

.markdown-body :deep(.chat-markdown-table) {
	width: max-content;
	min-width: 100%;
	border-collapse: collapse;
	table-layout: auto;
	font-size: 14px;
	line-height: 1.55;
}

.markdown-body :deep(.chat-markdown-table th),
.markdown-body :deep(.chat-markdown-table td) {
	padding: 10px 12px;
	border: 1px solid rgba(148, 163, 184, 0.22);
	vertical-align: top;
	word-break: keep-all;
	overflow-wrap: normal;
}

.markdown-body :deep(.chat-markdown-table th) {
	background: linear-gradient(180deg, rgba(241, 245, 249, 0.96), rgba(248, 250, 252, 0.96));
	font-weight: 700;
	white-space: nowrap;
}

.message-wrapper.user .markdown-body :deep(.chat-markdown-table th),
.message-wrapper.user .markdown-body :deep(.chat-markdown-table td) {
	border-color: rgba(255, 255, 255, 0.18);
}

.message-wrapper.user .markdown-body :deep(.chat-markdown-table th) {
	background: rgba(255, 255, 255, 0.12);
}

.markdown-body :deep(.chat-markdown-table td:nth-child(-n + 6)) {
	white-space: nowrap;
}

.markdown-body :deep(.chat-markdown-table td:nth-child(7)),
.markdown-body :deep(.chat-markdown-table td:nth-child(8)) {
	min-width: 180px;
	white-space: normal;
	word-break: break-word;
	overflow-wrap: anywhere;
}
</style>
