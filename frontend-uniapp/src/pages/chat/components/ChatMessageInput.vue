<template>
	<view class="footer-root">
		<!-- #ifdef MP-WEIXIN -->
		<view class="mp-chat-footer">
			<view class="mp-composer-shell" :class="{ 'has-image': selectedImage, 'is-focused': isFocused }">
				<view v-if="selectedImage" class="zen-image-preview-area">
					<view class="image-preview-frame">
						<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="$emit('previewimage', selectedImage)" />
					</view>
					<view class="image-preview-meta">
						<text class="image-preview-chip">已附图</text>
					</view>
					<view class="zen-remove-image-btn" @tap="$emit('removeimage')">×</view>
				</view>

				<view class="mp-composer-main">
					<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="$emit('triggerimageupload')">
						<text class="upload-pic-mark">+</text>
					</view>
					<input
						:value="inputMsg"
						class="zen-input-box zen-input-box-mp mp-composer-input"
						:cursor-spacing="24"
						confirm-type="send"
						:placeholder="selectedImage ? '补充图片说明，或直接发送...' : placeholder"
						@input="handleInput"
						@confirm="$emit('submitmessage')"
						@focus="isFocused = true"
						@blur="isFocused = false"
					/>
					<button
						v-if="!isGenerating"
						class="zen-send-btn mp-send-btn"
						:class="{ active: canSend }"
						:disabled="!canSend"
						@tap="$emit('submitmessage')"
					>
						<image class="icon-send-image" :src="sendIcon" mode="aspectFit" />
					</button>
					<button v-else class="zen-send-btn mp-send-btn stop" @tap="$emit('stopgeneration')">
						<text class="icon-send">■</text>
					</button>
				</view>
			</view>

			<view v-if="selectedImage || isGenerating" class="composer-status-row">
				<text v-if="selectedImage" class="composer-status-chip image-ready">已附加图片，可直接发送或继续补充文字</text>
				<text v-if="isGenerating" class="composer-status-chip generating">正在生成回复，可点击停止按钮中断</text>
			</view>
		</view>
		<!-- #endif -->

		<!-- #ifndef MP-WEIXIN -->
		<view class="zen-footer-wrapper chat-footer">
			<view class="input-shell input-container" :class="{ 'has-image': selectedImage, 'is-focused': isFocused }">
				<view class="zen-floating-pill" :class="{ 'has-image': selectedImage, 'is-focused': isFocused }">
					<view v-if="selectedImage" class="zen-image-preview-area">
						<view class="image-preview-frame">
							<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="$emit('previewimage', selectedImage)" />
						</view>
						<view class="image-preview-meta">
							<text class="image-preview-chip">已附图</text>
						</view>
						<view class="zen-remove-image-btn" @tap="$emit('removeimage')">×</view>
					</view>

					<view class="zen-input-row">
						<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="$emit('triggerimageupload')">
							<text class="upload-pic-mark">+</text>
						</view>

						<textarea
							:value="inputMsg"
							auto-height
							class="zen-input-box"
							:cursor-spacing="24"
							:show-confirm-bar="false"
							confirm-type="send"
							:placeholder="selectedImage ? '补充图片说明，或直接发送...' : placeholder"
							@input="handleInput"
							@confirm="$emit('submitmessage')"
							@focus="isFocused = true"
							@blur="isFocused = false"
						></textarea>

						<view class="zen-send-area">
							<button v-if="!isGenerating" class="zen-send-btn" :class="{ active: canSend }" :disabled="!canSend" @tap="$emit('submitmessage')">
								<image class="icon-send-image" :src="sendIcon" mode="aspectFit" />
							</button>
							<button v-else class="zen-send-btn stop" @tap="$emit('stopgeneration')">
								<text class="icon-send">■</text>
							</button>
						</view>
					</view>
				</view>
			</view>

			<view v-if="selectedImage || isGenerating" class="composer-status-row">
				<text v-if="selectedImage" class="composer-status-chip image-ready">已附加图片，可直接发送或继续补充文字</text>
				<text v-if="isGenerating" class="composer-status-chip generating">正在生成回复，可点击停止按钮中断</text>
			</view>
		</view>
		<!-- #endif -->
	</view>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
	inputMsg: {
		type: String,
		default: ''
	},
	selectedImage: {
		type: String,
		default: ''
	},
	isGenerating: {
		type: Boolean,
		default: false
	},
	placeholder: {
		type: String,
		default: '发送消息，支持粘贴或上传图片...'
	},
	sendIcon: {
		type: String,
		default: '/static/send.png'
	}
})

const emit = defineEmits(['inputchange', 'submitmessage', 'stopgeneration', 'triggerimageupload', 'removeimage', 'previewimage'])
const isFocused = ref(false)
const canSend = computed(() => Boolean(props.inputMsg.trim() || props.selectedImage))

const handleInput = (event) => {
	emit('inputchange', event.detail.value)
}
</script>

<style scoped>
.footer-root {
	width: 100%;
}

.chat-footer,
.mp-chat-footer {
	background: #ffffff;
	border-top: 1px solid rgba(0, 0, 0, 0.05);
	padding: 8px 16px env(safe-area-inset-bottom);
}

.mp-composer-shell,
.zen-floating-pill {
	background: #f1f5f9;
	border-radius: 24px;
	padding: 4px 8px;
	transition: all 0.3s;
	border: 1px solid transparent;
}

.mp-composer-shell.is-focused,
.zen-floating-pill.is-focused {
	background: #ffffff;
	border-color: #2563eb;
	box-shadow: 0 4px 20px rgba(37, 99, 235, 0.08);
}

.mp-composer-main,
.zen-input-row {
	display: flex;
	align-items: center;
}

.zen-input-box {
	flex: 1;
	min-height: 40px;
	max-height: 120px;
	padding: 8px 12px;
	font-size: 15px;
	color: #1e293b;
}

.zen-upload-btn {
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
}

.upload-pic-mark {
	font-size: 24px;
	font-weight: 300;
}

.zen-send-btn {
	width: 36px;
	height: 36px;
	background: transparent;
	border: none;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	transition: all 0.2s;
	opacity: 0.5;
}

.zen-send-btn::after {
	border: none;
}

.zen-send-btn.active {
	opacity: 1;
}

.icon-send-image {
	width: 24px;
	height: 24px;
}

.zen-send-btn.stop {
	opacity: 1;
	color: #ef4444;
}

.zen-image-preview-area {
	display: flex;
	align-items: center;
	padding: 8px;
	background: #ffffff;
	border-radius: 12px;
	margin-bottom: 4px;
}

.image-preview-frame {
	width: 48px;
	height: 48px;
	border-radius: 8px;
	overflow: hidden;
	margin-right: 12px;
	border: 1px solid #e2e8f0;
}

.zen-image-preview {
	width: 100%;
	height: 100%;
}

.image-preview-chip {
	font-size: 12px;
	color: #64748b;
	background: #f1f5f9;
	padding: 2px 8px;
	border-radius: 4px;
}

.zen-remove-image-btn {
	margin-left: auto;
	padding: 8px;
	color: #94a3b8;
	font-size: 18px;
}

.composer-status-row {
	padding: 6px 12px;
	display: flex;
	flex-wrap: wrap;
}

.composer-status-chip {
	font-size: 11px;
	padding: 2px 8px;
	border-radius: 10px;
	margin-right: 8px;
	margin-bottom: 4px;
}

.image-ready {
	background: #ecfdf5;
	color: #059669;
}

.generating {
	background: #eff6ff;
	color: #2563eb;
	animation: breathe 2s infinite ease-in-out;
}

@keyframes breathe {
	0%, 100% { opacity: 0.7; }
	50% { opacity: 1; }
}
</style>
