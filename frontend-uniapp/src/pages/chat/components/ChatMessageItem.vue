<template>
	<view class="message-wrapper" :class="message.role">
		<!-- 头像 -->
		<view class="avatar">
			<image v-if="message.role === 'assistant'" :src="aiAvatar" class="xiaoyi-avatar" mode="aspectFit" />
			<view v-else class="user-avatar">{{ userInitial }}</view>
		</view>

		<!-- 消息体 -->
		<view :class="['message-body', 'message-content', { 'is-typing': message.isTyping }]">
			<!-- 图片内容 -->
			<image
				v-if="message.image"
				:src="message.image"
				mode="widthFix"
				class="chat-message-image"
				@tap="$emit('previewImage', message.image)"
			/>

			<!-- 文本内容 - 微信小程序专用渲染 -->
			<!-- #ifdef MP-WEIXIN -->
			<view class="mp-message-rich">
				<view
					v-for="(block, blockIndex) in mpBlocks"
					:key="`${message.id}-${blockIndex}`"
					class="mp-message-block"
					:class="`is-${block.type}`"
				>
					<view v-if="block.type === 'divider'" class="mp-message-divider"></view>
					<view v-else class="mp-message-line">
						<text v-if="block.prefix" class="mp-message-prefix">{{ block.prefix }}</text>
						<text class="mp-message-line-text">{{ block.text }}</text>
					</view>
				</view>
			</view>
			<!-- #endif -->

			<!-- 文本内容 - 非小程序 (H5/App) 使用 Markdown 渲染 -->
			<!-- #ifndef MP-WEIXIN -->
			<rich-text class="markdown-body" :nodes="markdownNodes"></rich-text>
			<!-- #endif -->

			<!-- 打字机光标 -->
			<text v-if="message.isTyping" class="cursor-blink"></text>
		</view>
	</view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	message: {
		type: Object,
		required: true
	},
	userInitial: {
		type: String,
		default: 'U'
	},
	aiAvatar: {
		type: String,
		default: '/static/xiaoyi_transparent.png'
	},
	// 传入解析后的内容，避免在组件内重复解析
	markdownNodes: {
		type: [Array, String],
		default: ''
	},
	mpBlocks: {
		type: Array,
		default: () => []
	}
})

defineEmits(['previewImage'])
</script>

<style scoped>
.message-wrapper {
	display: flex;
	margin-bottom: 24px;
	padding: 0 16px;
	animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
	from { opacity: 0; transform: translateY(10px); }
	to { opacity: 1; transform: translateY(0); }
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.avatar {
	width: 36px;
	height: 36px;
	flex-shrink: 0;
	border-radius: 50%;
	overflow: hidden;
	margin-top: 4px;
}

.assistant .avatar {
	margin-right: 12px;
}

.user .avatar {
	margin-left: 12px;
}

.xiaoyi-avatar {
	width: 100%;
	height: 100%;
	background: #ffffff;
}

.user-avatar {
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, #3b82f6, #2563eb);
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: bold;
	font-size: 14px;
}

.message-body {
	max-width: 75%;
	padding: 12px 16px;
	border-radius: 16px;
	position: relative;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
	font-size: 15px;
	line-height: 1.6;
}

.assistant .message-body {
	background: #ffffff;
	color: #1e293b;
	border-top-left-radius: 4px;
	border: 1px solid rgba(0, 0, 0, 0.03);
}

.user .message-body {
	background: #2563eb;
	color: #ffffff;
	border-top-right-radius: 4px;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.chat-message-image {
	max-width: 100%;
	border-radius: 8px;
	margin-bottom: 8px;
	border: 1px solid rgba(0, 0, 0, 0.05);
}

.markdown-body {
	word-break: break-word;
	overflow-wrap: break-word;
}

.markdown-body ::v-deep(.chat-table-wrap) {
	margin: 16rpx 0;
	overflow-x: auto;
	border: 1px solid rgba(148, 163, 184, 0.28);
	border-radius: 20rpx;
	background: rgba(255, 255, 255, 0.96);
}

.markdown-body ::v-deep(.chat-markdown-table) {
	width: max-content;
	min-width: 100%;
	border-collapse: collapse;
	table-layout: auto;
	font-size: 28rpx;
	line-height: 1.55;
}

.markdown-body ::v-deep(.chat-markdown-table th),
.markdown-body ::v-deep(.chat-markdown-table td) {
	padding: 14rpx 16rpx;
	border: 1px solid rgba(148, 163, 184, 0.22);
	vertical-align: top;
	word-break: keep-all;
	overflow-wrap: normal;
}

.markdown-body ::v-deep(.chat-markdown-table th) {
	background: #f8fafc;
	font-weight: 700;
	white-space: nowrap;
}

.markdown-body ::v-deep(.chat-markdown-table td:nth-child(-n + 6)) {
	white-space: nowrap;
}

.markdown-body ::v-deep(.chat-markdown-table td:nth-child(7)),
.markdown-body ::v-deep(.chat-markdown-table td:nth-child(8)) {
	min-width: 280rpx;
	white-space: normal;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.cursor-blink {
	display: inline-block;
	width: 2px;
	height: 16px;
	background: currentColor;
	margin-left: 4px;
	vertical-align: middle;
	animation: blink 1s infinite steps(2, start);
}

@keyframes blink {
  to { opacity: 0; }
}

/* 微信小程序内容块样式 */
.mp-message-rich {
	display: flex;
	flex-direction: column;
}

.mp-message-block {
	margin-bottom: 8px;
}
.mp-message-block:last-child {
	margin-bottom: 0;
}

.mp-message-divider {
	height: 1px;
	background: rgba(0, 0, 0, 0.1);
	margin: 12px 0;
}

.is-heading {
	font-weight: 700;
	font-size: 17px;
	margin: 12px 0 8px;
}

.mp-message-line {
	display: flex;
}

.mp-message-prefix {
	margin-right: 8px;
	opacity: 0.7;
	flex-shrink: 0;
}

.mp-message-line-text {
	flex: 1;
}

.is-paragraph {
	line-height: 1.6;
}
</style>
